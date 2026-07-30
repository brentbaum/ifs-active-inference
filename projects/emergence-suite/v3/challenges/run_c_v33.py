#!/usr/bin/env python3
"""One-run sealed C-V33 executor.

`run` consumes escrow and seals raw traces. `evaluate` reads only those sealed
traces and computes the five precommitted criteria.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import sys
from dataclasses import asdict, is_dataclass, replace
from datetime import datetime, timezone
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ref import v31, v33  # noqa: E402
from ref.trace_sink import serializing_trace_context  # noqa: E402


CHALLENGE = ROOT / "sealed-revealed" / "C-V33-prune-challenge.md"
RESULTS = ROOT / "results" / "V3.3"
RUN_DIR = RESULTS / "c-v33"
PARAMETERS = ROOT / "protocols" / "v3.3-parameters.json"
MANIFEST = RESULTS / "freeze-manifest.json"
SEAL_LEDGER = ROOT.parents[1] / "ifs-paper" / "suite-v2-sealed-hashes.md"
EXPECTED_SHA256 = (
    "c6ae7f5169be554cbead523f2ffe6ac797033eb63937ccf59bb7c104e21ac3a4"
)
RELEASED_BLOCK = (4_030_000, 4_033_999)
TOLERANCE = 1e-10


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(child) for child in value]
    if is_dataclass(value):
        return _plain(asdict(value))
    if hasattr(value, "item"):
        return value.item()
    return value


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            _plain(value),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            _plain(value), indent=2, sort_keys=True, allow_nan=False
        )
        + "\n",
        encoding="utf-8",
    )


def _parse_bundle() -> dict[str, Any]:
    text = CHALLENGE.read_text(encoding="utf-8")
    literals = [
        line
        for line in text.splitlines()
        if line.startswith("{") and line.endswith("}")
    ]
    if len(literals) != 1:
        raise RuntimeError("sealed bundle does not contain one literal line")
    parsed = ast.literal_eval(literals[0])
    if not isinstance(parsed, dict):
        raise RuntimeError("sealed literal is not a dict")
    return parsed


def _verify_manifest() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in manifest["files"].items():
        path = ROOT / relative
        actual = (
            hashlib.sha256(path.read_bytes()).hexdigest()
            if path.exists()
            else None
        )
        if actual != expected:
            mismatches.append(
                {
                    "file": relative,
                    "expected": expected,
                    "actual": actual,
                }
            )
    return {
        "expected_files": len(manifest["files"]),
        "mismatches": mismatches,
        "passed": not mismatches,
        "status": manifest["status"],
    }


def validate() -> dict[str, Any]:
    bundle = _parse_bundle()
    challenge_hash = hashlib.sha256(CHALLENGE.read_bytes()).hexdigest()
    seal_text = SEAL_LEDGER.read_text(encoding="utf-8")
    parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    manifest = _verify_manifest()
    cell_items = [
        (name, value)
        for name, value in bundle.items()
        if name.startswith("cell_")
    ]
    seeds = []
    config_errors = []
    for name, cell in cell_items:
        start, end = (int(value) for value in cell["escrow"].split(":"))
        seeds.extend(range(start, end + 1))
        try:
            v33.ReductionConfig(**cell["config"])
        except (TypeError, ValueError) as error:
            config_errors.append({"cell": name, "error": str(error)})
    expected_thresholds = {
        "mode_retained": 0.9499999999999938,
        "burden_edge_mass_max": 0.8957220041345053,
        "absent_present_bf_min": 5.3387558362702816e-08,
    }
    threshold_errors = {
        key: {
            "sealed": value,
            "frozen": parameters["material_readout"][key],
        }
        for key, value in expected_thresholds.items()
        if parameters["material_readout"][key] != value
    }
    public_api = (
        "generate_world",
        "score_world",
        "append_neutral_observation",
        "burden_absent_present_bf",
        "material_reduction_readout",
        "first_material_time",
        "root_revision_event",
    )
    result = {
        "challenge_sha256": challenge_hash,
        "challenge_hash_matches": challenge_hash == EXPECTED_SHA256,
        "seal_ledger_matches": (
            EXPECTED_SHA256 in seal_text
            and "4030000:4033999" in seal_text
        ),
        "release_authorization_commit": "be21368",
        "release_block": list(RELEASED_BLOCK),
        "manifest": manifest,
        "cell_count": len(cell_items),
        "seed_count": len(seeds),
        "ascending_gap_free": seeds == list(
            range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)
        ),
        "config_errors": config_errors,
        "threshold_errors": threshold_errors,
        "public_api_missing": [
            name for name in public_api if not hasattr(v33, name)
        ],
    }
    result["passed"] = (
        result["challenge_hash_matches"]
        and result["seal_ledger_matches"]
        and manifest["passed"]
        and result["cell_count"] == 4
        and result["seed_count"] == 4000
        and result["ascending_gap_free"]
        and not config_errors
        and not threshold_errors
        and not result["public_api_missing"]
    )
    return result


def _program_values(program: Any) -> dict[str, int]:
    return {
        key: int(value)
        for key, value in v31.program_values(program).items()
    }


def _schema_hash(record: Mapping[str, Any]) -> str:
    schema = {
        key: type(value).__name__
        for key, value in sorted(record.items())
    }
    return hashlib.sha256(_canonical_bytes(schema)).hexdigest()


def _worker(task: tuple[int, str, int, Mapping[str, Any]]) -> dict[str, Any]:
    seed, cell_name, cell_index, config_values = task
    with serializing_trace_context(f"C-V33:{cell_name}:{seed}") as sink:
        config = v33.ReductionConfig(**dict(config_values))
        world = v33.generate_world(
            seed,
            config,
            released_block=RELEASED_BLOCK,
        )
        posterior = v33.score_world(world)
        parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
        threshold_values = parameters["material_readout"]
        thresholds = v33.MaterialReductionThresholds(
            mode_retained=threshold_values["mode_retained"],
            burden_edge_mass_max=threshold_values[
                "burden_edge_mass_max"
            ],
            absent_present_bf_min=threshold_values[
                "absent_present_bf_min"
            ],
            stability_observations=threshold_values[
                "stability_observations"
            ],
            neutral_tolerance=threshold_values["neutral_tolerance"],
        )
        material = dict(
            v33.material_reduction_readout(world, posterior, thresholds)
        )
        neutral = v33.append_neutral_observation(world)
        neutral_posterior = v33.score_world(neutral)
        neutral_error = max(
            abs(a - b)
            for a, b in zip(
                posterior.current.probabilities,
                neutral_posterior.current.probabilities,
            )
        )
        historical_only = replace(
            world,
            slices=tuple(
                item for item in world.slices if item.context == 0
            ),
        )
        historical_posterior = v33.score_world(historical_only)
        historical_error = abs(
            posterior.old_graph_probability
            - historical_posterior.old_graph_probability
        )
        event = v33.root_revision_event(world)
        imaginal_times = [
            item.time
            for item in world.slices
            if item.episode_kind == "imaginal_post"
        ]
        record = {
            "seed": seed,
            "seed_index": cell_index,
            "cell": cell_name,
            "challenge_sha256": EXPECTED_SHA256,
            "released_block": list(RELEASED_BLOCK),
            "config": asdict(config),
            "historical_truth_structure": _program_values(
                world.historical_structure
            ),
            "current_truth_structure": _program_values(
                world.current_truth_structure
            ),
            "observations": [asdict(item) for item in world.slices],
            "interventions": [
                {"time": item.time, "do_action": item.action}
                for item in world.slices
                if item.action is not None
            ],
            "exact_world_log_probability": world.exact_log_probability,
            "component_rng_keys": list(world.rng_keys),
            "current_structure_probabilities": list(
                posterior.current.probabilities
            ),
            "historical_structure_probabilities": list(
                posterior.historical.probabilities
            ),
            "current_log_evidence": posterior.current.log_evidence,
            "historical_log_evidence": posterior.historical.log_evidence,
            "current_edge_probabilities": dict(
                posterior.current.edge_probabilities
            ),
            "current_mode_probability": (
                posterior.current.active_mode_probability
            ),
            "old_graph_probability": posterior.old_graph_probability,
            "historical_query_error": historical_error,
            "burden_edge_mass": posterior.burden_edge_mass,
            "absent_present_bf": v33.burden_absent_present_bf(
                posterior.current
            ),
            "material_readout": material,
            "first_material_time": v33.first_material_time(
                world, thresholds
            ),
            "neutral_identity_error": neutral_error,
            "root_revision_event": event,
            "first_imaginal_post_time": (
                min(imaginal_times) if imaginal_times else None
            ),
            "schedule_identity": (
                event is not None
                and bool(imaginal_times)
                and min(imaginal_times) == event + 1
                if config.do_over == "post_revision"
                else True
            ),
            "runtime_trace_events": list(sink.events),
        }
        record["schema_sha256"] = _schema_hash(record)
        return record


def _seal_cell(
    cell_name: str,
    tasks: Sequence[tuple[int, str, int, Mapping[str, Any]]],
) -> dict[str, Any]:
    path = RUN_DIR / f"{cell_name}-traces.jsonl"
    ledger_path = RUN_DIR / f"{cell_name}-trace-hashes.json"
    file_hash = hashlib.sha256()
    records = []
    processes = max(1, min(8, (os.cpu_count() or 2) - 1))
    with path.open("xb") as handle:
        with get_context("spawn").Pool(processes) as pool:
            for row in pool.imap(_worker, tasks, chunksize=8):
                encoded = _canonical_bytes(row)
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
                file_hash.update(encoded)
                records.append(
                    {
                        "seed": row["seed"],
                        "sha256": hashlib.sha256(encoded).hexdigest(),
                    }
                )
    ledger = {
        "cell": cell_name,
        "file": path.name,
        "world_count": len(records),
        "first_seed": records[0]["seed"],
        "last_seed": records[-1]["seed"],
        "file_sha256": file_hash.hexdigest(),
        "records": records,
        "criteria_evaluated": False,
    }
    _write_json(ledger_path, ledger)
    return ledger


def run_once() -> None:
    validation = validate()
    if not validation["passed"]:
        _write_json(RESULTS / "c-v33-stop-as-sealed.json", validation)
        raise SystemExit("STOP_AS_SEALED: bundle is not expressible")
    if RUN_DIR.exists():
        raise SystemExit("C-V33 run directory already exists; rerun forbidden")
    RUN_DIR.mkdir(parents=True)
    bundle = _parse_bundle()
    started = datetime.now(timezone.utc).isoformat()
    ledgers = []
    cells = [
        (name, value)
        for name, value in bundle.items()
        if name.startswith("cell_")
    ]
    for cell_name, cell in cells:
        start, end = (int(value) for value in cell["escrow"].split(":"))
        tasks = [
            (seed, cell_name, seed - start, cell["config"])
            for seed in range(start, end + 1)
        ]
        ledgers.append(_seal_cell(cell_name, tasks))
    run_ledger = {
        "challenge": "C-V33",
        "run_count": 1,
        "started_utc": started,
        "traces_sealed_utc": datetime.now(timezone.utc).isoformat(),
        "criteria_evaluated": False,
        "validation": validation,
        "released_block": list(RELEASED_BLOCK),
        "authorization_commit": "be21368",
        "seed_consumption": {
            "count": 4000,
            "first": RELEASED_BLOCK[0],
            "last": RELEASED_BLOCK[1],
            "ascending_gap_free": True,
        },
        "cell_ledgers": [
            {
                key: value
                for key, value in ledger.items()
                if key != "records"
            }
            for ledger in ledgers
        ],
    }
    _write_json(RUN_DIR / "run-ledger-precriteria.json", run_ledger)
    print("RAW_TRACES_SEALED")


def _read_cell(cell_name: str) -> list[dict[str, Any]]:
    ledger_path = RUN_DIR / f"{cell_name}-trace-hashes.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    path = RUN_DIR / ledger["file"]
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != ledger["file_sha256"]:
        raise RuntimeError(f"{cell_name} file hash mismatch")
    lines = content.splitlines(keepends=True)
    if len(lines) != ledger["world_count"]:
        raise RuntimeError(f"{cell_name} trace count mismatch")
    for encoded, expected in zip(lines, ledger["records"]):
        if hashlib.sha256(encoded).hexdigest() != expected["sha256"]:
            raise RuntimeError(f"{cell_name} record hash mismatch")
    return [json.loads(line) for line in lines]


def _mean(values: Sequence[float]) -> float:
    return math.fsum(values) / len(values)


def evaluate() -> None:
    precriteria = json.loads(
        (RUN_DIR / "run-ledger-precriteria.json").read_text(encoding="utf-8")
    )
    if precriteria["criteria_evaluated"]:
        raise SystemExit("C-V33 criteria already evaluated")
    names = [
        name
        for name in _parse_bundle()
        if name.startswith("cell_")
    ]
    cells = {name: _read_cell(name) for name in names}
    c1, c2, c3, c4 = (cells[name] for name in names)
    c1_rate = _mean(
        [float(row["material_readout"]["material"]) for row in c1]
    )
    c2_rate = _mean(
        [float(row["material_readout"]["material"]) for row in c2]
    )
    paired_times = [
        (
            left["first_material_time"],
            right["first_material_time"],
        )
        for left, right in zip(c1, c2)
        if left["first_material_time"] is not None
        and right["first_material_time"] is not None
    ]
    paired_time_difference = _mean(
        [float(right - left) for left, right in paired_times]
    )
    summaries = {
        names[0]: {
            "material_rate": c1_rate,
            "historical_query_error_max": max(
                row["historical_query_error"] for row in c1
            ),
            "mode_retention_mean": _mean(
                [row["current_mode_probability"] for row in c1]
            ),
        },
        names[1]: {
            "material_rate": c2_rate,
            "paired_material_rate_difference": c2_rate - c1_rate,
            "paired_first_material_time_difference_mean": (
                paired_time_difference
            ),
            "paired_first_material_time_eligible": len(paired_times),
            "paired_first_material_time_censored": 1000 - len(paired_times),
            "schedule_identity_rate": _mean(
                [float(row["schedule_identity"]) for row in c2]
            ),
        },
        names[2]: {
            "durable_material_reduction_rate": _mean(
                [
                    float(row["material_readout"]["material"])
                    for row in c3
                ]
            ),
        },
        names[3]: {
            "burden_material_reduction_rate": _mean(
                [
                    float(row["material_readout"]["material"])
                    for row in c4
                ]
            ),
            "adaptive_w_y_probability_mean": _mean(
                [
                    row["current_edge_probabilities"]["W_Y"]
                    for row in c4
                ]
            ),
        },
    }
    neutral_max = max(
        row["neutral_identity_error"]
        for rows in cells.values()
        for row in rows
    )
    all_seeds = [
        row["seed"] for rows in cells.values() for row in rows
    ]
    criteria = {
        "1_correction_reduces": (
            summaries[names[0]]["material_rate"] >= 0.89
            and summaries[names[0]]["historical_query_error_max"] <= TOLERANCE
            and summaries[names[0]]["mode_retention_mean"] >= 0.95
        ),
        "2_do_over_equivalence": (
            abs(
                summaries[names[1]][
                    "paired_material_rate_difference"
                ]
            )
            <= 0.02
            and abs(
                summaries[names[1]][
                    "paired_first_material_time_difference_mean"
                ]
            )
            <= 0.5
            and summaries[names[1]]["schedule_identity_rate"] == 1.0
        ),
        "3_premature_not_durable": (
            summaries[names[2]]["durable_material_reduction_rate"] <= 0.09
        ),
        "4_adaptive_edge_survives": (
            summaries[names[3]]["burden_material_reduction_rate"] >= 0.89
            and summaries[names[3]]["adaptive_w_y_probability_mean"] >= 0.748
        ),
        "5_semantic_and_custody": (
            neutral_max <= TOLERANCE
            and all_seeds
            == list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1))
            and validate()["passed"]
        ),
    }
    verdict = "PASS" if all(criteria.values()) else "FAIL"
    result = {
        "immutable_sealed_verdict": verdict,
        "criteria": criteria,
        "cell_summaries": summaries,
        "neutral_identity_error_max": neutral_max,
        "verdict_classes": {
            "scientific": {
                key: value
                for key, value in criteria.items()
                if key.startswith(("1_", "2_", "3_", "4_"))
            },
            "semantic": {
                "neutral_observation_identity": neutral_max <= TOLERANCE,
                "maximum_error": neutral_max,
            },
            "custody": {
                "passed": criteria["5_semantic_and_custody"],
                "challenge_sha256": EXPECTED_SHA256,
                "released_block": list(RELEASED_BLOCK),
                "seeds_once_ascending_gap_free": (
                    all_seeds
                    == list(
                        range(
                            RELEASED_BLOCK[0],
                            RELEASED_BLOCK[1] + 1,
                        )
                    )
                ),
                "trace_ledgers_verified_before_evaluation": True,
            },
        },
        "standing_limitations": {
            "do_over_speedup": (
                "Gate-3/Gate-5 null retained; sealed equivalence criterion "
                f"{'passed' if criteria['2_do_over_equivalence'] else 'failed'}"
            ),
            "suggestion_direction": (
                "Gate-3/Gate-5 small-negative anomaly retained; C-V33 "
                "contains no suggestion-direction criterion"
            ),
        },
    }
    for name, summary in summaries.items():
        _write_json(RUN_DIR / f"{name}-results.json", summary)
    _write_json(RUN_DIR / "summary.json", result)
    completed = dict(precriteria)
    completed["criteria_evaluated"] = True
    completed["evaluated_utc"] = datetime.now(timezone.utc).isoformat()
    completed["immutable_sealed_verdict"] = verdict
    _write_json(RUN_DIR / "run-ledger.json", completed)
    print(verdict)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("validate", "run", "evaluate"))
    args = parser.parse_args()
    if args.step == "validate":
        result = validate()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["passed"] else 1
    if args.step == "run":
        run_once()
    else:
        evaluate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
