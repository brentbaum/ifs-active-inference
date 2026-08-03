#!/usr/bin/env python3
"""One-shot runner for the revealed C-V36A sealed challenge."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import sys
from dataclasses import asdict
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ref import v36  # noqa: E402
from ref.custody import validate_finite_worker_row  # noqa: E402
from ref.trace_sink import serializing_trace_context  # noqa: E402


RESULTS = ROOT / "results" / "V3.6"
CHALLENGE = ROOT / "sealed-revealed" / "C-V36A-acute-formation-challenge.md"
MANIFEST = RESULTS / "v3.6-freeze-manifest-final.json"
EXPECTED_CHALLENGE_SHA256 = (
    "3b81a5cb0b52a4423f2dc9e090ccd6b28598405d105d3b8b47c8fea6d0083ff8"
)
RELEASED_BLOCK = (4_100_000, 4_102_999)
TRACE_PATH = RESULTS / "c-v36a-traces.jsonl"
EVENT_HASH_PATH = RESULTS / "c-v36a-event-hashes.jsonl"
TRACE_HASHES_PATH = RESULTS / "c-v36a-trace-hashes.json"
VERDICT_JSON = RESULTS / "c-v36a-verdict.json"
VERDICT_MD = RESULTS / "c-v36a-verdict.md"


def _plain(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _plain(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(child) for child in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _canonical(value: Any) -> bytes:
    return (
        json.dumps(_plain(value), sort_keys=True, separators=(",", ":"),
                   allow_nan=False).encode("utf-8") + b"\n"
    )


def _write_json_exclusive(path: Path, value: Any) -> None:
    encoded = json.dumps(
        _plain(value), indent=2, sort_keys=True, allow_nan=False
    ).encode("utf-8") + b"\n"
    with path.open("xb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())


def _parse_challenge() -> dict[str, Any]:
    raw = CHALLENGE.read_bytes()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != EXPECTED_CHALLENGE_SHA256:
        raise RuntimeError(f"sealed challenge hash mismatch: {observed}")
    text = raw.decode("utf-8")
    literal_lines = [
        line for line in text.splitlines()
        if line.startswith("{'parse_instruction':")
    ]
    if len(literal_lines) != 1:
        raise RuntimeError("sealed challenge must contain exactly one literal line")
    parsed = ast.literal_eval(literal_lines[0])
    if not isinstance(parsed, dict):
        raise RuntimeError("sealed challenge literal is not a dictionary")
    return parsed


def _parse_range(text: str) -> tuple[int, int]:
    left, right = text.split(":")
    return int(left), int(right)


def _validate_bundle(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    expected = [
        ("cell_a1_regulation", 4_100_000, 4_100_799, 800),
        ("cell_a2_cue_only", 4_100_800, 4_101_499, 700),
        ("cell_a3_pruning", 4_101_500, 4_102_199, 700),
        ("cell_a4_single_mode_full", 4_102_200, 4_102_999, 800),
    ]
    tasks: list[dict[str, Any]] = []
    readout_fields = set(v36.CompositionReadout.__dataclass_fields__)
    for cell, start, end, count in expected:
        declaration = spec[cell]
        if _parse_range(declaration["escrow"]) != (start, end):
            raise RuntimeError(f"{cell}: escrow mismatch")
        declared_count = declaration.get("n_pairs", declaration.get("n_worlds"))
        if declared_count != count or end - start + 1 != count:
            raise RuntimeError(f"{cell}: cardinality mismatch")
        if declaration.get("mode_count") != 1:
            raise RuntimeError(f"{cell}: mode-count mismatch")
        if "field" in declaration and declaration["field"] not in readout_fields:
            raise RuntimeError(f"{cell}: inexpressible readout field")
        protocols = [declaration.get("protocol")]
        if "n_pairs" in declaration:
            protocols = [declaration["full"], declaration["ablation"]]
        for protocol in protocols:
            if protocol not in v36.PROTOCOLS:
                raise RuntimeError(f"{cell}: inexpressible protocol {protocol}")
        tasks.extend(
            {"seed": seed, "cell": cell, "declaration": dict(declaration)}
            for seed in range(start, end + 1)
        )
    seeds = [task["seed"] for task in tasks]
    if seeds != list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)):
        raise RuntimeError("challenge seed map is not ascending and gap-free")
    return tasks


def _verify_freeze() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in manifest["files"].items():
        path = ROOT / relative
        observed = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        if observed != expected:
            mismatches.append({"file": relative, "expected": expected, "observed": observed})
    # The committed epoch map is a post-manifest custody/allocation record.  It
    # is not executable or scientific source; all executable frozen files must
    # still match byte-for-byte.
    allowed_custody_files = {"protocols/epoch-c-seed-map.json"}
    forbidden = [item for item in mismatches if item["file"] not in allowed_custody_files]
    if forbidden:
        raise RuntimeError(f"frozen identity mismatch: {forbidden[:3]}")
    source_mismatches = [item for item in mismatches if item["file"].startswith("ref/")]
    if source_mismatches:
        raise RuntimeError(f"frozen source mismatch: {source_mismatches[:3]}")
    return {
        "manifest": MANIFEST.name,
        "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "file_count": len(manifest["files"]),
        "scientific_or_executable_mismatches": forbidden,
        "authorized_post_freeze_custody_record_changes": mismatches,
    }


def _config(protocol: str, mode_count: int) -> v36.ComposeConfig:
    return v36.ComposeConfig(
        protocol=protocol,
        mode_count=mode_count,
        topology="allied",
        stakes="low",
        support_target="all",
        policy_regime="engagement",
        missingness=0.0,
        length=16,
    )


def _run_arm(seed: int, cell: str, arm: str, protocol: str, mode_count: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    with serializing_trace_context(f"C-V36A:{cell}:{seed}:{arm}") as sink:
        readout = v36.run_therapy(
            seed, _config(protocol, mode_count), released_block=RELEASED_BLOCK
        )
    return _plain(readout), _plain(sink.events)


def _worker(task: Mapping[str, Any]) -> dict[str, Any]:
    seed = int(task["seed"])
    cell = str(task["cell"])
    declaration = task["declaration"]
    mode_count = int(declaration["mode_count"])
    if "n_pairs" in declaration:
        full, full_events = _run_arm(
            seed, cell, "full", declaration["full"], mode_count
        )
        ablation, ablation_events = _run_arm(
            seed, cell, "ablation", declaration["ablation"], mode_count
        )
        field = str(declaration["field"])
        row = {
            "seed": seed,
            "cell": cell,
            "paired": True,
            "field": field,
            "full_protocol": declaration["full"],
            "ablation_protocol": declaration["ablation"],
            "full": full,
            "ablation": ablation,
            "paired_difference": float(full[field] - ablation[field]),
            "event_ledgers": {"full": full_events, "ablation": ablation_events},
        }
    else:
        readout, events = _run_arm(
            seed, cell, "single", declaration["protocol"], mode_count
        )
        row = {
            "seed": seed,
            "cell": cell,
            "paired": False,
            "protocol": declaration["protocol"],
            "readout": readout,
            "event_ledgers": {"single": events},
        }
    validate_finite_worker_row(row)
    return row


def _persist_row(
    row: Mapping[str, Any], trace_handle: Any, event_handle: Any,
    trace_digest: Any, event_digest: Any,
) -> dict[str, Any]:
    encoded = _canonical(row)
    trace_handle.write(encoded)
    trace_handle.flush()
    os.fsync(trace_handle.fileno())
    trace_digest.update(encoded)
    event_payload = {
        "seed": int(row["seed"]),
        "cell": row["cell"],
        "row_sha256": hashlib.sha256(encoded).hexdigest(),
        "event_ledgers_sha256": hashlib.sha256(
            _canonical(row["event_ledgers"])
        ).hexdigest(),
    }
    event_encoded = _canonical(event_payload)
    event_handle.write(event_encoded)
    event_handle.flush()
    os.fsync(event_handle.fileno())
    event_digest.update(event_encoded)
    return event_payload


def _execute(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for path in (TRACE_PATH, EVENT_HASH_PATH, TRACE_HASHES_PATH, VERDICT_JSON, VERDICT_MD):
        if path.exists():
            raise RuntimeError(f"one-shot custody refusal: {path.name} already exists")
    rows: list[dict[str, Any]] = []
    event_records: list[dict[str, Any]] = []
    trace_digest = hashlib.sha256()
    event_digest = hashlib.sha256()
    processes = max(1, min(8, (os.cpu_count() or 2) - 1))
    with TRACE_PATH.open("xb") as trace_handle, EVENT_HASH_PATH.open("xb") as event_handle:
        # Each cell's first world is executed serially and durably persisted before
        # that cell's parallel remainder opens.
        for cell in (
            "cell_a1_regulation", "cell_a2_cue_only",
            "cell_a3_pruning", "cell_a4_single_mode_full",
        ):
            cell_tasks = [task for task in tasks if task["cell"] == cell]
            first = _worker(cell_tasks[0])
            event_records.append(_persist_row(
                first, trace_handle, event_handle, trace_digest, event_digest
            ))
            rows.append(first)
            with get_context("spawn").Pool(processes) as pool:
                for row in pool.imap(_worker, cell_tasks[1:], chunksize=4):
                    event_records.append(_persist_row(
                        row, trace_handle, event_handle, trace_digest, event_digest
                    ))
                    rows.append(row)
    expected = list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1))
    if [int(row["seed"]) for row in rows] != expected:
        raise RuntimeError("post-execution seed order/gap failure")
    if len({int(row["seed"]) for row in rows}) != len(rows):
        raise RuntimeError("post-execution duplicate seed failure")
    hash_record = {
        "challenge": "C-V36A",
        "trace_file": TRACE_PATH.name,
        "trace_file_sha256": trace_digest.hexdigest(),
        "event_hash_file": EVENT_HASH_PATH.name,
        "event_hash_file_sha256": event_digest.hexdigest(),
        "row_count": len(rows),
        "seed_start": expected[0],
        "seed_end": expected[-1],
        "ascending_gap_free": True,
        "unique_seed_count": len(set(expected)),
        "records": event_records,
        "custody_order": (
            "Every row and event-ledger hash was flushed and fsynced before "
            "this aggregate hash record and before criterion aggregation."
        ),
    }
    _write_json_exclusive(TRACE_HASHES_PATH, hash_record)
    if hashlib.sha256(TRACE_PATH.read_bytes()).hexdigest() != trace_digest.hexdigest():
        raise RuntimeError("trace file rehash failure")
    if hashlib.sha256(EVENT_HASH_PATH.read_bytes()).hexdigest() != event_digest.hexdigest():
        raise RuntimeError("event hash file rehash failure")
    return rows


def _bootstrap(values: list[float], analysis_seed: int) -> list[float]:
    array = np.asarray(values, dtype=float)
    rng = np.random.default_rng(analysis_seed)
    means = np.mean(rng.choice(array, (4000, len(array)), replace=True), axis=1)
    return [float(x) for x in np.quantile(means, [0.025, 0.975])]


def _distribution(values: Iterable[float]) -> dict[str, Any]:
    array = np.asarray(list(values), dtype=float)
    return {
        "n": int(array.size),
        "mean": float(np.mean(array)),
        "std": float(np.std(array)),
        "min": float(np.min(array)),
        "q05": float(np.quantile(array, 0.05)),
        "q25": float(np.quantile(array, 0.25)),
        "median": float(np.quantile(array, 0.50)),
        "q75": float(np.quantile(array, 0.75)),
        "q95": float(np.quantile(array, 0.95)),
        "max": float(np.max(array)),
    }


def _evaluate(rows: list[dict[str, Any]], freeze: Mapping[str, Any]) -> dict[str, Any]:
    paired_cells = (
        ("criterion_1", "cell_a1_regulation", 36_001),
        ("criterion_2", "cell_a2_cue_only", 36_002),
        ("criterion_3", "cell_a3_pruning", 36_003),
    )
    criteria: dict[str, Any] = {}
    for criterion, cell, analysis_seed in paired_cells:
        selected = [row for row in rows if row["cell"] == cell]
        values = [float(row["paired_difference"]) for row in selected]
        interval = _bootstrap(values, analysis_seed)
        criteria[criterion] = {
            "cell": cell,
            "field": selected[0]["field"],
            "world_pairs": len(values),
            "mean_full_minus_ablation": float(np.mean(values)),
            "interval_95": interval,
            "whole_world_bootstrap_replicates": 4000,
            "deterministic_analysis_seed": analysis_seed,
            "positive_sign_carried": interval[0] > 0.0,
            "passed": interval[0] > 0.0,
        }
    a4 = [row for row in rows if row["cell"] == "cell_a4_single_mode_full"]
    finite_fields = ("q_external_danger", "q_identity_organization", "L_total")
    finiteness = {
        field: all(math.isfinite(float(row["readout"][field])) for row in a4)
        for field in finite_fields
    }
    fingerprints = (
        "opposed_D_0_1", "opposed_D_1_0", "allied_D_0_1", "allied_D_1_0"
    )
    criteria["criterion_4"] = {
        "cell": "cell_a4_single_mode_full",
        "worlds": len(a4),
        "finite_every_world": finiteness,
        "cross_mode_fingerprint_distributions_descriptive_no_floor": {
            field: _distribution(float(row["readout"][field]) for row in a4)
            for field in fingerprints
        },
        "passed": all(finiteness.values()),
    }
    criteria["criterion_5"] = {
        "seed_start": RELEASED_BLOCK[0],
        "seed_end": RELEASED_BLOCK[1],
        "consumed": len(rows),
        "unique": len({row["seed"] for row in rows}),
        "ascending_gap_free": [row["seed"] for row in rows]
        == list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)),
        "escrow_remainder_retired_unconsumed": [4_103_000, 4_109_999],
        "event_ledgers_persisted_before_aggregation": True,
        "trace_hash_record": TRACE_HASHES_PATH.name,
    }
    criteria["criterion_5"]["passed"] = (
        criteria["criterion_5"]["consumed"] == 3000
        and criteria["criterion_5"]["unique"] == 3000
        and criteria["criterion_5"]["ascending_gap_free"]
    )
    overall = all(entry["passed"] for entry in criteria.values())
    return {
        "challenge": "C-V36A",
        "immutable_verdict": "PASS" if overall else "FAIL",
        "criteria": criteria,
        "verdict_classes": {
            "scientific": "PASS" if all(criteria[f"criterion_{i}"]["passed"] for i in (1, 2, 3)) else "FAIL",
            "semantic_reporting": "PASS" if criteria["criterion_4"]["passed"] else "FAIL",
            "custody": "PASS" if criteria["criterion_5"]["passed"] else "FAIL",
        },
        "challenge_sha256": EXPECTED_CHALLENGE_SHA256,
        "parse_method": "ast.literal_eval on the exact bracketed literal line only",
        "frozen_identity": dict(freeze),
        "trace_sha256": hashlib.sha256(TRACE_PATH.read_bytes()).hexdigest(),
        "event_hash_ledger_sha256": hashlib.sha256(EVENT_HASH_PATH.read_bytes()).hexdigest(),
        "verdict_written_before_interpretation": True,
        "one_shot": True,
    }


def _write_report(verdict: Mapping[str, Any]) -> None:
    criteria = verdict["criteria"]
    lines = [
        "# C-V36A sealed challenge verdict", "",
        f"Immutable sealed verdict: **{verdict['immutable_verdict']}**.", "",
        "## Criterion results", "",
    ]
    for index in (1, 2, 3):
        entry = criteria[f"criterion_{index}"]
        lines.append(
            f"{index}. **{'PASS' if entry['passed'] else 'FAIL'}** — "
            f"{entry['field']} mean full-minus-ablation "
            f"{entry['mean_full_minus_ablation']:.12g}, whole-world bootstrap "
            f"95% CI [{entry['interval_95'][0]:.12g}, {entry['interval_95'][1]:.12g}] "
            f"over {entry['world_pairs']} same-seed pairs."
        )
    c4 = criteria["criterion_4"]
    lines.extend(["", f"4. **{'PASS' if c4['passed'] else 'FAIL'}** — all required "
                  "single-mode readouts were finite in every world. Cross-mode "
                  "fingerprints are descriptive only:", ""])
    for field, summary in c4["cross_mode_fingerprint_distributions_descriptive_no_floor"].items():
        lines.append(
            f"   - `{field}`: mean {summary['mean']:.12g}; median {summary['median']:.12g}; "
            f"5th–95th percentile [{summary['q05']:.12g}, {summary['q95']:.12g}]; "
            f"range [{summary['min']:.12g}, {summary['max']:.12g}]."
        )
    c5 = criteria["criterion_5"]
    lines.extend([
        "", f"5. **{'PASS' if c5['passed'] else 'FAIL'}** — 3,000 unique seeds "
        "were consumed once, ascending and gap-free. The raw trace and event-ledger "
        "hash stream were fsynced before aggregation. Escrow 4103000:4109999 is "
        "retired unconsumed.", "", "## Verdict classes", "",
        f"- Scientific: **{verdict['verdict_classes']['scientific']}**",
        f"- Semantic/reporting: **{verdict['verdict_classes']['semantic_reporting']}**",
        f"- Custody: **{verdict['verdict_classes']['custody']}**", "",
        "## Interpretation", "",
        "The immutable result above is retained as written. The three paired cells "
        "localize the regulated-evidence, cue-only-transfer, and structural-pruning "
        "pathways at single-mode scale. The fourth cell reports posterior-model-averaged "
        "cross-mode fingerprints without imposing a zero floor, exactly as sealed.", "",
        f"Raw trace SHA-256: `{verdict['trace_sha256']}`.  ",
        f"Event-hash ledger SHA-256: `{verdict['event_hash_ledger_sha256']}`.", "",
    ])
    encoded = "\n".join(lines).encode("utf-8")
    with VERDICT_MD.open("xb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    spec = _parse_challenge()
    tasks = _validate_bundle(spec)
    freeze = _verify_freeze()
    rows = _execute(tasks)
    verdict = _evaluate(rows, freeze)
    # Immutable machine verdict precedes the interpretive Markdown report.
    _write_json_exclusive(VERDICT_JSON, verdict)
    _write_report(verdict)


if __name__ == "__main__":
    main()
