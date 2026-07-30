#!/usr/bin/env python3
"""One-run sealed C-V34 executor.

The ``run`` phase consumes escrow and seals raw traces.  The ``evaluate``
phase reads only those sealed traces and computes the five sealed criteria.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from ref import v34  # noqa: E402
from ref.trace_sink import serializing_trace_context  # noqa: E402


CHALLENGE = ROOT / "sealed-revealed" / "C-V34-relate-challenge.md"
RESULTS = ROOT / "results" / "V3.4"
RUN_DIR = RESULTS / "c-v34"
MANIFEST = RESULTS / "freeze-manifest.json"
SEAL_LEDGER = (
    REPOSITORY / "projects" / "ifs-paper" / "suite-v2-sealed-hashes.md"
)
EXPECTED_SHA256 = (
    "6b09fd32e32e7b79e1ef5e99a136bf90f32695b10369eb04f902f4275f3a4c16"
)
RELEASED_BLOCK = (4_040_000, 4_043_999)
TOLERANCE = 1e-10
CELL_NAMES = (
    "cell_1_reliable_regulated",
    "cell_2_no_root_evidence",
    "cell_3_unregulated",
    "cell_4_switch",
)


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
    section = text.index("## Cells (parse instruction binding)")
    start = text.index("{", section)
    end = text.index("\n\n## Criteria", start)
    literal = text[start:end]
    parsed = ast.literal_eval(literal)
    if not isinstance(parsed, dict):
        raise TypeError("sealed cell literal is not one dict")
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
    manifest = _verify_manifest()
    seeds = []
    config_errors = []
    cell_schemas = []
    for name in CELL_NAMES:
        cell = bundle[name]
        start, end = (int(value) for value in cell["escrow"].split(":"))
        seeds.extend(range(start, end + 1))
        try:
            config = v34.RelateConfig(**cell["config"])
        except (TypeError, ValueError) as error:
            config_errors.append({"cell": name, "error": str(error)})
        else:
            cell_schemas.append(
                {
                    "cell": name,
                    "start": start,
                    "end": end,
                    "n_worlds": cell["n_worlds"],
                    "config": asdict(config),
                }
            )
    public_fields = (
        "root_movement",
        "global_precision",
        "q_partner",
        "smoothed_partner",
        "root_log_bf",
        "structure_probabilities",
        "switch_onset",
    )
    result = {
        "challenge_sha256": challenge_hash,
        "challenge_hash_matches": challenge_hash == EXPECTED_SHA256,
        "seal_ledger_matches": (
            EXPECTED_SHA256 in seal_text
            and "4040000:4043999" in seal_text
        ),
        "release_block": list(RELEASED_BLOCK),
        "release_authority": (
            "suite-v2-sealed-hashes.md C-V34 release record"
        ),
        "manifest": manifest,
        "cell_count": len(cell_schemas),
        "seed_count": len(seeds),
        "ascending_gap_free": seeds
        == list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)),
        "config_errors": config_errors,
        "public_api_missing": [
            name
            for name in ("generate_world", "score_world")
            if not hasattr(v34, name)
        ],
        "public_readout_fields": list(public_fields),
        "cell_schemas": cell_schemas,
    }
    result["passed"] = (
        result["challenge_hash_matches"]
        and result["seal_ledger_matches"]
        and manifest["passed"]
        and manifest["status"]
        == "FROZEN_ADJUDICATED_SHORT_HISTORY_CONJUNCTION_BOUND"
        and result["cell_count"] == 4
        and result["seed_count"] == 4000
        and result["ascending_gap_free"]
        and not result["config_errors"]
        and not result["public_api_missing"]
    )
    return result


def _schema_hash(record: Mapping[str, Any]) -> str:
    schema = {
        key: type(value).__name__
        for key, value in sorted(record.items())
    }
    return hashlib.sha256(_canonical_bytes(schema)).hexdigest()


def _worker(
    task: tuple[int, int, str, Mapping[str, Any]]
) -> dict[str, Any]:
    seed, seed_index, cell_name, config_values = task
    with serializing_trace_context(
        f"C-V34:{cell_name}:{seed}"
    ) as sink:
        config = v34.RelateConfig(**dict(config_values))
        world = v34.generate_world(
            seed,
            config,
            released_block=RELEASED_BLOCK,
        )
        posterior = v34.score_world(world)
        truth_counts = {
            state: world.truth_partner_path.count(state)
            for state in range(v34.PARTNER_CARDINALITY)
        }
        majority_truth = max(truth_counts, key=truth_counts.get)
        partner_argmax = max(
            range(v34.PARTNER_CARDINALITY),
            key=lambda state: posterior.q_partner[state],
        )
        onset = config.length // 2
        pre_switch_before = tuple(
            tuple(values)
            for values in posterior.smoothed_partner[:onset]
        )
        _ = tuple(posterior.smoothed_partner[onset:])
        pre_switch_after = tuple(
            tuple(values)
            for values in posterior.smoothed_partner[:onset]
        )
        pre_switch_query_error = (
            max(
                abs(a - b)
                for before, after in zip(
                    pre_switch_before, pre_switch_after
                )
                for a, b in zip(before, after)
            )
            if pre_switch_before
            else 0.0
        )
        post_switch_correct = [
            int(max(range(4), key=lambda state: probabilities[state]))
            == truth
            for probabilities, truth in zip(
                posterior.smoothed_partner[onset:],
                world.truth_partner_path[onset:],
            )
        ]
        record = {
            "seed": seed,
            "seed_index": seed_index,
            "cell": cell_name,
            "challenge_sha256": EXPECTED_SHA256,
            "released_block": list(RELEASED_BLOCK),
            "config": asdict(config),
            "truth_structure": asdict(world.truth_structure),
            "truth_partner_path": list(world.truth_partner_path),
            "truth_root": world.truth_root,
            "observations": [
                asdict(item) for item in world.observations
            ],
            "exact_world_log_probability": world.exact_log_probability,
            "component_rng_keys": list(world.rng_keys),
            "structure_probabilities": list(
                posterior.structure_probabilities
            ),
            "structure_normalization_error": abs(
                math.fsum(posterior.structure_probabilities) - 1.0
            ),
            "log_evidence": posterior.log_evidence,
            "edge_probabilities": dict(posterior.edge_probabilities),
            "q_root": list(posterior.q_root),
            "q_partner": list(posterior.q_partner),
            "smoothed_partner": [
                list(values) for values in posterior.smoothed_partner
            ],
            "local_precision": list(posterior.local_precision),
            "global_precision": list(posterior.global_precision),
            "root_log_bf": posterior.root_log_bf,
            "root_movement": posterior.root_movement,
            "transfer": posterior.transfer,
            "trust_remaining_after_refusal": (
                posterior.trust_remaining_after_refusal
            ),
            "transition_probability": posterior.transition_probability,
            "switch_onset": posterior.switch_onset,
            "co_regulated": posterior.co_regulated,
            "majority_truth_partner_state": majority_truth,
            "partner_argmax_state": partner_argmax,
            "partner_argmax_correct": partner_argmax == majority_truth,
            "post_switch_correct": post_switch_correct,
            "pre_switch_query_error": pre_switch_query_error,
            "runtime_trace_events": list(sink.events),
        }
        record["schema_sha256"] = _schema_hash(record)
        return record


def _seal_cell(
    cell_name: str,
    tasks: Sequence[tuple[int, int, str, Mapping[str, Any]]],
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
        _write_json(RESULTS / "c-v34-stop-as-sealed.json", validation)
        raise SystemExit("STOP_AS_SEALED: bundle is not expressible")
    if RUN_DIR.exists():
        raise SystemExit("C-V34 run directory already exists; rerun forbidden")
    RUN_DIR.mkdir(parents=True)
    bundle = _parse_bundle()
    started = datetime.now(timezone.utc).isoformat()
    ledgers = []
    for cell_name in CELL_NAMES:
        cell = bundle[cell_name]
        start, end = (int(value) for value in cell["escrow"].split(":"))
        tasks = [
            (seed, seed - start, cell_name, cell["config"])
            for seed in range(start, end + 1)
        ]
        ledgers.append(_seal_cell(cell_name, tasks))
    run_ledger = {
        "challenge": "C-V34",
        "run_count": 1,
        "started_utc": started,
        "traces_sealed_utc": datetime.now(timezone.utc).isoformat(),
        "criteria_evaluated": False,
        "validation": validation,
        "released_block": list(RELEASED_BLOCK),
        "release_authority": (
            "suite-v2-sealed-hashes.md C-V34 release record"
        ),
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
    ledger = json.loads(
        (RUN_DIR / f"{cell_name}-trace-hashes.json").read_text(
            encoding="utf-8"
        )
    )
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


def _mean_ci(values: Sequence[float]) -> dict[str, float]:
    mean = _mean(values)
    if len(values) < 2:
        standard_error = 0.0
    else:
        variance = math.fsum(
            (value - mean) ** 2 for value in values
        ) / (len(values) - 1)
        standard_error = math.sqrt(variance / len(values))
    return {
        "mean": mean,
        "lower_95": mean - 1.96 * standard_error,
        "upper_95": mean + 1.96 * standard_error,
    }


def evaluate() -> None:
    precriteria = json.loads(
        (RUN_DIR / "run-ledger-precriteria.json").read_text(
            encoding="utf-8"
        )
    )
    if precriteria["criteria_evaluated"]:
        raise SystemExit("C-V34 criteria already evaluated")
    cells = {name: _read_cell(name) for name in CELL_NAMES}
    c1, c2, c3, c4 = (cells[name] for name in CELL_NAMES)
    if not all(
        left["seed_index"] == right["seed_index"] == third["seed_index"]
        for left, right, third in zip(c1, c2, c3)
    ):
        raise RuntimeError("paired cell indices do not align")
    c1_movement = [row["root_movement"] for row in c1]
    c2_movement = [row["root_movement"] for row in c2]
    c3_movement = [row["root_movement"] for row in c3]
    c1_minus_c2 = [
        left - right for left, right in zip(c1_movement, c2_movement)
    ]
    c1_minus_c3 = [
        left - right for left, right in zip(c1_movement, c3_movement)
    ]
    summaries = {
        CELL_NAMES[0]: {
            "root_movement": _mean_ci(c1_movement),
            "global_precision_mean": _mean(
                [
                    value
                    for row in c1
                    for value in row["global_precision"]
                ]
            ),
            "partner_argmax_accuracy": _mean(
                [float(row["partner_argmax_correct"]) for row in c1]
            ),
        },
        CELL_NAMES[1]: {
            "root_movement_max_abs": max(
                abs(value) for value in c2_movement
            ),
            "root_log_bf_max_abs": max(
                abs(row["root_log_bf"]) for row in c2
            ),
            "paired_cell1_minus_cell2_movement": _mean_ci(
                c1_minus_c2
            ),
        },
        CELL_NAMES[2]: {
            "global_precision_mean": _mean(
                [
                    value
                    for row in c3
                    for value in row["global_precision"]
                ]
            ),
            "paired_cell1_minus_cell3_movement": _mean_ci(
                c1_minus_c3
            ),
        },
        CELL_NAMES[3]: {
            "post_switch_partner_recovery": _mean(
                [
                    float(correct)
                    for row in c4
                    for correct in row["post_switch_correct"]
                ]
            ),
            "switch_onset_error": {
                "mean": _mean(
                    [
                        abs(row["switch_onset"] - 32)
                        for row in c4
                    ]
                ),
                "q95": sorted(
                    abs(row["switch_onset"] - 32) for row in c4
                )[949],
                "maximum": max(
                    abs(row["switch_onset"] - 32) for row in c4
                ),
            },
            "pre_switch_query_error_max": max(
                row["pre_switch_query_error"] for row in c4
            ),
        },
    }
    normalization_max = max(
        row["structure_normalization_error"]
        for rows in cells.values()
        for row in rows
    )
    all_seeds = [
        row["seed"] for name in CELL_NAMES for row in cells[name]
    ]
    criteria = {
        "1_reliable_regulated": (
            summaries[CELL_NAMES[0]]["root_movement"]["mean"] >= 0.30
            and summaries[CELL_NAMES[0]]["global_precision_mean"] >= 0.80
            and summaries[CELL_NAMES[0]]["partner_argmax_accuracy"]
            >= 0.90
        ),
        "2_no_root_writing_and_uptake": (
            summaries[CELL_NAMES[1]]["root_movement_max_abs"]
            <= TOLERANCE
            and summaries[CELL_NAMES[1]][
                "paired_cell1_minus_cell2_movement"
            ]["lower_95"]
            > 0.25
        ),
        "3_regulation_increases_uptake": (
            summaries[CELL_NAMES[2]]["global_precision_mean"] <= 0.55
            and summaries[CELL_NAMES[2]][
                "paired_cell1_minus_cell3_movement"
            ]["lower_95"]
            > 0.02
        ),
        "4_switch_tracking_and_retention": (
            summaries[CELL_NAMES[3]]["post_switch_partner_recovery"]
            >= 0.75
            and summaries[CELL_NAMES[3]]["pre_switch_query_error_max"]
            <= TOLERANCE
        ),
        "5_semantic_and_custody": (
            summaries[CELL_NAMES[1]]["root_log_bf_max_abs"]
            <= TOLERANCE
            and normalization_max <= TOLERANCE
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
        "normalization_error_max": normalization_max,
        "verdict_classes": {
            "scientific": {
                key: value
                for key, value in criteria.items()
                if key.startswith(("1_", "2_", "3_", "4_"))
            },
            "semantic": {
                "regulation_only_root_log_bf_exact_zero": (
                    summaries[CELL_NAMES[1]]["root_log_bf_max_abs"]
                    <= TOLERANCE
                ),
                "maximum_regulation_only_root_log_bf": (
                    summaries[CELL_NAMES[1]]["root_log_bf_max_abs"]
                ),
                "posterior_normalization": (
                    normalization_max <= TOLERANCE
                ),
                "maximum_normalization_error": normalization_max,
            },
            "custody": {
                "passed": criteria["5_semantic_and_custody"],
                "challenge_sha256": EXPECTED_SHA256,
                "released_block": list(RELEASED_BLOCK),
                "seeds_once_ascending_gap_free": all_seeds
                == list(
                    range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)
                ),
                "paired_indices_aligned": True,
                "trace_ledgers_verified_before_evaluation": True,
            },
        },
        "descriptive": {
            "switch_onset_error": summaries[CELL_NAMES[3]][
                "switch_onset_error"
            ]
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
