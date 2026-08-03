#!/usr/bin/env python3
"""One-shot runner for the revealed C-V36B sealed challenge."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import sys
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Mapping

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ref import v36  # noqa: E402
from ref.custody import validate_finite_worker_row  # noqa: E402
from ref.trace_sink import serializing_trace_context  # noqa: E402
from scripts.run_cv36a import (  # noqa: E402
    _bootstrap,
    _canonical,
    _plain,
    _verify_freeze,
    _write_json_exclusive,
)


RESULTS = ROOT / "results" / "V3.6"
CHALLENGE = ROOT / "sealed-revealed" / "C-V36B-chronic-protection-challenge.md"
EXPECTED_SHA256 = "e74aec8d1c18805e49aaab2aeafc828df6f3247129995c5477c950becfa9592b"
RELEASED_BLOCK = (4_110_000, 4_112_999)
TRACE_PATH = RESULTS / "c-v36b-traces.jsonl"
EVENT_HASH_PATH = RESULTS / "c-v36b-event-hashes.jsonl"
TRACE_HASHES_PATH = RESULTS / "c-v36b-trace-hashes.json"
VERDICT_JSON = RESULTS / "c-v36b-verdict.json"
VERDICT_MD = RESULTS / "c-v36b-verdict.md"


def _parse() -> dict[str, Any]:
    raw = CHALLENGE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
        raise RuntimeError("sealed challenge hash mismatch")
    lines = [
        line for line in raw.decode("utf-8").splitlines()
        if line.startswith("{'parse_instruction':")
    ]
    if len(lines) != 1:
        raise RuntimeError("sealed challenge must contain exactly one literal line")
    value = ast.literal_eval(lines[0])
    if not isinstance(value, dict):
        raise RuntimeError("sealed literal is not a dictionary")
    return value


def _range(value: str) -> tuple[int, int]:
    parts = value.split(":")
    if len(parts) != 2:
        raise RuntimeError("invalid escrow range")
    return int(parts[0]), int(parts[1])


def _validate(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    cells = (
        ("cell_b1_unreliable", 4_110_000, 4_110_699, 700),
        ("cell_b2_noncontingent", 4_110_700, 4_111_399, 700),
        ("cell_b3_mode_bypass", 4_111_400, 4_111_999, 600),
        ("cell_b4_opposed", 4_112_000, 4_112_499, 500),
        ("cell_b5_allied", 4_112_500, 4_112_999, 500),
    )
    tasks: list[dict[str, Any]] = []
    readout_fields = set(v36.CompositionReadout.__dataclass_fields__)
    for name, start, end, count in cells:
        declaration = dict(spec[name])
        if _range(declaration["escrow"]) != (start, end):
            raise RuntimeError(f"{name}: escrow mismatch")
        observed_count = declaration.get("n_pairs", declaration.get("n_worlds"))
        if observed_count != count or end - start + 1 != count:
            raise RuntimeError(f"{name}: cardinality mismatch")
        if declaration.get("field") and declaration["field"] not in readout_fields:
            raise RuntimeError(f"{name}: inexpressible readout")
        protocols = (
            [declaration["full"], declaration["ablation"]]
            if "n_pairs" in declaration else [declaration["protocol"]]
        )
        if any(protocol not in v36.PROTOCOLS for protocol in protocols):
            raise RuntimeError(f"{name}: inexpressible protocol")
        if declaration["topology"] not in {"independent", "opposed", "allied"}:
            raise RuntimeError(f"{name}: inexpressible topology")
        tasks.extend(
            {"seed": seed, "cell": name, "declaration": declaration}
            for seed in range(start, end + 1)
        )
    if [task["seed"] for task in tasks] != list(range(4_110_000, 4_113_000)):
        raise RuntimeError("seed map is not ascending and gap-free")
    return tasks


def _config(protocol: str, topology: str) -> v36.ComposeConfig:
    return v36.ComposeConfig(
        protocol=protocol,
        mode_count=3,
        topology=topology,
        stakes="low",
        support_target="all",
        policy_regime="engagement",
        missingness=0.0,
        length=16,
    )


def _arm(seed: int, cell: str, arm: str, protocol: str, topology: str):
    with serializing_trace_context(f"C-V36B:{cell}:{seed}:{arm}") as sink:
        readout = v36.run_therapy(
            seed, _config(protocol, topology), released_block=RELEASED_BLOCK
        )
    return _plain(readout), _plain(sink.events)


def _worker(task: Mapping[str, Any]) -> dict[str, Any]:
    seed = int(task["seed"])
    cell = str(task["cell"])
    declaration = task["declaration"]
    topology = declaration["topology"]
    if "n_pairs" in declaration:
        full, full_events = _arm(seed, cell, "full", declaration["full"], topology)
        ablation, ablation_events = _arm(
            seed, cell, "ablation", declaration["ablation"], topology
        )
        field = declaration["field"]
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
        readout, events = _arm(seed, cell, "single", declaration["protocol"], topology)
        row = {
            "seed": seed,
            "cell": cell,
            "paired": False,
            "topology": topology,
            "readout": readout,
            "event_ledgers": {"single": events},
        }
    validate_finite_worker_row(row)
    return row


def _persist(row, trace_handle, event_handle, trace_digest, event_digest):
    encoded = _canonical(row)
    trace_handle.write(encoded)
    trace_handle.flush()
    os.fsync(trace_handle.fileno())
    trace_digest.update(encoded)
    event_record = {
        "seed": row["seed"],
        "cell": row["cell"],
        "row_sha256": hashlib.sha256(encoded).hexdigest(),
        "event_ledgers_sha256": hashlib.sha256(
            _canonical(row["event_ledgers"])
        ).hexdigest(),
    }
    event_encoded = _canonical(event_record)
    event_handle.write(event_encoded)
    event_handle.flush()
    os.fsync(event_handle.fileno())
    event_digest.update(event_encoded)
    return event_record


def _execute(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for path in (TRACE_PATH, EVENT_HASH_PATH, TRACE_HASHES_PATH, VERDICT_JSON, VERDICT_MD):
        if path.exists():
            raise RuntimeError(f"one-shot custody refusal: {path.name} exists")
    rows, records = [], []
    trace_digest, event_digest = hashlib.sha256(), hashlib.sha256()
    processes = max(1, min(8, (os.cpu_count() or 2) - 1))
    cell_order = (
        "cell_b1_unreliable", "cell_b2_noncontingent", "cell_b3_mode_bypass",
        "cell_b4_opposed", "cell_b5_allied",
    )
    with TRACE_PATH.open("xb") as trace_handle, EVENT_HASH_PATH.open("xb") as event_handle:
        for cell in cell_order:
            cell_tasks = [task for task in tasks if task["cell"] == cell]
            first = _worker(cell_tasks[0])
            records.append(_persist(
                first, trace_handle, event_handle, trace_digest, event_digest
            ))
            rows.append(first)
            with get_context("spawn").Pool(processes) as pool:
                for row in pool.imap(_worker, cell_tasks[1:], chunksize=4):
                    records.append(_persist(
                        row, trace_handle, event_handle, trace_digest, event_digest
                    ))
                    rows.append(row)
    expected = list(range(4_110_000, 4_113_000))
    if [row["seed"] for row in rows] != expected or len(set(expected)) != len(rows):
        raise RuntimeError("post-execution seed custody failure")
    hash_record = {
        "challenge": "C-V36B",
        "trace_file": TRACE_PATH.name,
        "trace_file_sha256": trace_digest.hexdigest(),
        "event_hash_file": EVENT_HASH_PATH.name,
        "event_hash_file_sha256": event_digest.hexdigest(),
        "row_count": len(rows),
        "seed_start": expected[0],
        "seed_end": expected[-1],
        "ascending_gap_free": True,
        "records": records,
        "custody_order": "Rows and event hashes were flushed and fsynced before aggregation.",
    }
    _write_json_exclusive(TRACE_HASHES_PATH, hash_record)
    if hashlib.sha256(TRACE_PATH.read_bytes()).hexdigest() != trace_digest.hexdigest():
        raise RuntimeError("trace rehash failure")
    if hashlib.sha256(EVENT_HASH_PATH.read_bytes()).hexdigest() != event_digest.hexdigest():
        raise RuntimeError("event-hash rehash failure")
    return rows


def _paired_criterion(rows, cell, floor, analysis_seed):
    selected = [row for row in rows if row["cell"] == cell]
    values = [float(row["paired_difference"]) for row in selected]
    interval = _bootstrap(values, analysis_seed)
    mean = float(np.mean(values))
    return {
        "cell": cell,
        "field": selected[0]["field"],
        "world_pairs": len(values),
        "frozen_floor": floor,
        "mean_full_minus_ablation": mean,
        "interval_95": interval,
        "whole_world_bootstrap_replicates": 4000,
        "deterministic_analysis_seed": analysis_seed,
        "floor_met": mean >= floor,
        "positive_sign_carried": interval[0] > 0.0,
        "passed": mean >= floor and interval[0] > 0.0,
    }


def _evaluate(rows, freeze):
    criteria = {
        "criterion_1": _paired_criterion(
            rows, "cell_b1_unreliable", 0.37054935530184596, 36_101
        ),
        "criterion_2": _paired_criterion(
            rows, "cell_b2_noncontingent", 0.4970780975763216, 36_102
        ),
        "criterion_3": _paired_criterion(
            rows, "cell_b3_mode_bypass", 0.034129478327372516, 36_103
        ),
    }
    sign_cells = {
        "opposed_D_0_1": ("cell_b4_opposed", 36_104),
        "opposed_D_1_0": ("cell_b4_opposed", 36_105),
        "allied_D_0_1": ("cell_b5_allied", 36_106),
        "allied_D_1_0": ("cell_b5_allied", 36_107),
    }
    signs = {}
    for field, (cell, analysis_seed) in sign_cells.items():
        values = [
            float(row["readout"][field]) for row in rows if row["cell"] == cell
        ]
        interval = _bootstrap(values, analysis_seed)
        signs[field] = {
            "cell": cell,
            "worlds": len(values),
            "mean": float(np.mean(values)),
            "interval_95": interval,
            "expected_frozen_readout_sign": "positive",
            "interval_excludes_zero_in_expected_direction": interval[0] > 0.0,
            "passed": interval[0] > 0.0,
        }
    criteria["criterion_4"] = {
        "opposed_and_allied_reported_separately": True,
        "fingerprints": signs,
        "passed": all(value["passed"] for value in signs.values()),
    }
    criteria["criterion_5"] = {
        "consumed": len(rows),
        "unique": len({row["seed"] for row in rows}),
        "ascending_gap_free": [row["seed"] for row in rows]
        == list(range(4_110_000, 4_113_000)),
        "event_ledgers_persisted_before_aggregation": True,
        "escrow_remainder_retired_unconsumed": [4_113_000, 4_119_999],
        "trace_hash_record": TRACE_HASHES_PATH.name,
    }
    criteria["criterion_5"]["passed"] = (
        criteria["criterion_5"]["consumed"] == 3000
        and criteria["criterion_5"]["unique"] == 3000
        and criteria["criterion_5"]["ascending_gap_free"]
    )
    overall = all(value["passed"] for value in criteria.values())
    return {
        "challenge": "C-V36B",
        "immutable_verdict": "PASS" if overall else "FAIL",
        "criteria": criteria,
        "verdict_classes": {
            "scientific": "PASS" if all(criteria[f"criterion_{i}"]["passed"] for i in (1, 2, 3, 4)) else "FAIL",
            "custody": "PASS" if criteria["criterion_5"]["passed"] else "FAIL",
        },
        "challenge_sha256": EXPECTED_SHA256,
        "parse_method": "ast.literal_eval on the exact bracketed literal line only",
        "frozen_identity": freeze,
        "trace_sha256": hashlib.sha256(TRACE_PATH.read_bytes()).hexdigest(),
        "event_hash_ledger_sha256": hashlib.sha256(EVENT_HASH_PATH.read_bytes()).hexdigest(),
        "verdict_written_before_interpretation": True,
        "one_shot": True,
    }


def _report(verdict):
    criteria = verdict["criteria"]
    lines = [
        "# C-V36B sealed challenge verdict", "",
        f"Immutable sealed verdict: **{verdict['immutable_verdict']}**.", "",
        "## Criterion results", "",
    ]
    for index in (1, 2, 3):
        item = criteria[f"criterion_{index}"]
        lines.append(
            f"{index}. **{'PASS' if item['passed'] else 'FAIL'}** — "
            f"`{item['field']}` mean full-minus-ablation {item['mean_full_minus_ablation']:.12g}; "
            f"95% CI [{item['interval_95'][0]:.12g}, {item['interval_95'][1]:.12g}]; "
            f"frozen floor {item['frozen_floor']:.12g}; {item['world_pairs']} pairs."
        )
    lines.extend(["", f"4. **{'PASS' if criteria['criterion_4']['passed'] else 'FAIL'}** — "
                  "opposed and allied fingerprints were evaluated separately:", ""])
    for field, item in criteria["criterion_4"]["fingerprints"].items():
        lines.append(
            f"   - `{field}`: mean {item['mean']:.12g}; 95% CI "
            f"[{item['interval_95'][0]:.12g}, {item['interval_95'][1]:.12g}]."
        )
    lines.extend([
        "", f"5. **{'PASS' if criteria['criterion_5']['passed'] else 'FAIL'}** — "
        "3,000 unique seeds were consumed once, ascending and gap-free; raw rows and "
        "event-ledger hashes were fsynced before aggregation. Escrow "
        "4113000:4119999 is retired unconsumed.", "", "## Verdict classes", "",
        f"- Scientific: **{verdict['verdict_classes']['scientific']}**",
        f"- Custody: **{verdict['verdict_classes']['custody']}**", "",
        "## Interpretation", "",
        "The immutable result above is retained as written. The cells separately test "
        "partner reliability, noncontingent soothing, protection-respecting policy access, "
        "and the opposed/allied interventional topology fingerprints.", "",
        f"Raw trace SHA-256: `{verdict['trace_sha256']}`.  ",
        f"Event-hash ledger SHA-256: `{verdict['event_hash_ledger_sha256']}`.", "",
    ])
    encoded = "\n".join(lines).encode("utf-8")
    with VERDICT_MD.open("xb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())


def main() -> None:
    spec = _parse()
    tasks = _validate(spec)
    freeze = _verify_freeze()
    rows = _execute(tasks)
    verdict = _evaluate(rows, freeze)
    _write_json_exclusive(VERDICT_JSON, verdict)
    _report(verdict)


if __name__ == "__main__":
    main()
