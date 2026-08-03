#!/usr/bin/env python3
"""One-shot runner for the revealed C-V36C sealed challenge."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import re
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
    _bootstrap, _canonical, _distribution, _plain, _verify_freeze,
    _write_json_exclusive,
)


RESULTS = ROOT / "results" / "V3.6"
CHALLENGE = ROOT / "sealed-revealed" / "C-V36C-mixed-temporal-challenge.md"
EXPECTED_SHA256 = "c958ea843c46a05eecc95642f56e5d038a7ebcaf84249d81d7b655153462f851"
RELEASED_BLOCK = (4_120_000, 4_122_999)
TRACE_PATH = RESULTS / "c-v36c-traces.jsonl"
EVENT_HASH_PATH = RESULTS / "c-v36c-event-hashes.jsonl"
TRACE_HASHES_PATH = RESULTS / "c-v36c-trace-hashes.json"
VERDICT_JSON = RESULTS / "c-v36c-verdict.json"
VERDICT_MD = RESULTS / "c-v36c-verdict.md"

SCIENTIFIC_FIELDS = (
    "q_identity_organization", "q_external_danger", "q_action_efficacy",
    "episodic_information", "q_context_specific", "q_recurrent_context",
    "historical_retention", "q_current_edge_absence", "root_revision",
    "q_partner_reliable", "local_precision", "global_precision",
    "root_evidence_uptake", "root_transfer", "q_joint_policy_edge",
    "support_response", "contact_response", "stage_log_evidence",
)


def _parse() -> dict[str, Any]:
    raw = CHALLENGE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
        raise RuntimeError("sealed challenge hash mismatch")
    lines = [line for line in raw.decode().splitlines() if line.startswith("{'parse_instruction':")]
    if len(lines) != 1:
        raise RuntimeError("sealed challenge must contain exactly one literal line")
    value = ast.literal_eval(lines[0])
    if not isinstance(value, dict):
        raise RuntimeError("sealed literal is not a dictionary")
    return value


def _parse_range(value: str) -> tuple[int, int]:
    left, right = value.split(":")
    return int(left), int(right)


def _field_value(readout: Mapping[str, Any], field: str) -> float:
    match = re.fullmatch(r"([A-Za-z0-9_]+)(?:\[([0-9]+)\])?", field)
    if match is None or match.group(1) not in readout:
        raise RuntimeError(f"inexpressible field {field}")
    value = readout[match.group(1)]
    if match.group(2) is not None:
        value = value[int(match.group(2))]
    return float(value)


def _validate(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    cells = (
        ("cell_c1_context", 4_120_000, 4_120_799, 800),
        ("cell_c2_broadcast", 4_120_800, 4_121_499, 700),
        ("cell_c3_denied", 4_121_500, 4_122_199, 700),
        ("cell_c4_stakes", 4_122_200, 4_122_999, 800),
    )
    fields = set(v36.CompositionReadout.__dataclass_fields__)
    tasks: list[dict[str, Any]] = []
    for name, start, end, count in cells:
        declaration = dict(spec[name])
        if _parse_range(declaration["escrow"]) != (start, end):
            raise RuntimeError(f"{name}: escrow mismatch")
        if declaration["n_pairs"] != count or end - start + 1 != count:
            raise RuntimeError(f"{name}: cardinality mismatch")
        if "stakes_pair" not in declaration:
            base_field = declaration["field"].split("[")[0]
            if base_field not in fields:
                raise RuntimeError(f"{name}: inexpressible field")
            if declaration["full"] not in v36.PROTOCOLS or declaration["ablation"] not in v36.PROTOCOLS:
                raise RuntimeError(f"{name}: inexpressible protocol")
        tasks.extend(
            {"seed": seed, "cell": name, "declaration": declaration}
            for seed in range(start, end + 1)
        )
    if [task["seed"] for task in tasks] != list(range(4_120_000, 4_123_000)):
        raise RuntimeError("seed map is not ascending and gap-free")
    return tasks


def _config(protocol: str, stakes: str = "low") -> v36.ComposeConfig:
    return v36.ComposeConfig(
        protocol=protocol, mode_count=3, topology="allied", stakes=stakes,
        support_target="all", policy_regime="engagement", missingness=0.0,
        length=16,
    )


def _arm(seed: int, cell: str, arm: str, protocol: str, stakes: str = "low"):
    with serializing_trace_context(f"C-V36C:{cell}:{seed}:{arm}") as sink:
        readout = v36.run_therapy(
            seed, _config(protocol, stakes), released_block=RELEASED_BLOCK
        )
    return _plain(readout), _plain(sink.events)


def _numeric_differences(left: Any, right: Any) -> list[float]:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return [abs(float(left) - float(right))]
    if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
        output: list[float] = []
        for a, b in zip(left, right):
            output.extend(_numeric_differences(a, b))
        return output
    if isinstance(left, str) and isinstance(right, str):
        if left != right:
            raise RuntimeError("scientific sequence labels differ")
        return []
    raise RuntimeError("scientific identity fields have incompatible shapes")


def _worker(task: Mapping[str, Any]) -> dict[str, Any]:
    seed, cell = int(task["seed"]), str(task["cell"])
    declaration = task["declaration"]
    if declaration.get("stakes_pair"):
        high, high_events = _arm(seed, cell, "high", "full", "high")
        low, low_events = _arm(seed, cell, "low", "full", "low")
        errors: list[float] = []
        for field in SCIENTIFIC_FIELDS:
            errors.extend(_numeric_differences(low[field], high[field]))
        row = {
            "seed": seed, "cell": cell, "paired": True, "stakes_pair": True,
            "left_high": high, "right_low": low,
            "q_policy_open_low_minus_high": float(low["q_policy_open"] - high["q_policy_open"]),
            "scientific_identity_error": max(errors, default=0.0),
            "event_ledgers": {"high": high_events, "low": low_events},
        }
    else:
        ablation, ablation_events = _arm(
            seed, cell, "ablation", declaration["ablation"]
        )
        full, full_events = _arm(seed, cell, "full", declaration["full"])
        field = declaration["field"]
        row = {
            "seed": seed, "cell": cell, "paired": True, "field": field,
            "ablation_protocol": declaration["ablation"], "full_protocol": declaration["full"],
            "ablation": ablation, "full": full,
            "paired_difference": _field_value(full, field) - _field_value(ablation, field),
            "event_ledgers": {"ablation": ablation_events, "full": full_events},
        }
    validate_finite_worker_row(row)
    return row


def _persist(row, trace_handle, event_handle, trace_digest, event_digest):
    encoded = _canonical(row)
    trace_handle.write(encoded); trace_handle.flush(); os.fsync(trace_handle.fileno())
    trace_digest.update(encoded)
    record = {
        "seed": row["seed"], "cell": row["cell"],
        "row_sha256": hashlib.sha256(encoded).hexdigest(),
        "event_ledgers_sha256": hashlib.sha256(_canonical(row["event_ledgers"])).hexdigest(),
    }
    event_encoded = _canonical(record)
    event_handle.write(event_encoded); event_handle.flush(); os.fsync(event_handle.fileno())
    event_digest.update(event_encoded)
    return record


def _execute(tasks):
    for path in (TRACE_PATH, EVENT_HASH_PATH, TRACE_HASHES_PATH, VERDICT_JSON, VERDICT_MD):
        if path.exists():
            raise RuntimeError(f"one-shot custody refusal: {path.name} exists")
    rows, records = [], []
    trace_digest, event_digest = hashlib.sha256(), hashlib.sha256()
    processes = max(1, min(8, (os.cpu_count() or 2) - 1))
    cell_order = ("cell_c1_context", "cell_c2_broadcast", "cell_c3_denied", "cell_c4_stakes")
    with TRACE_PATH.open("xb") as trace_handle, EVENT_HASH_PATH.open("xb") as event_handle:
        for cell in cell_order:
            cell_tasks = [task for task in tasks if task["cell"] == cell]
            first = _worker(cell_tasks[0])
            records.append(_persist(first, trace_handle, event_handle, trace_digest, event_digest)); rows.append(first)
            with get_context("spawn").Pool(processes) as pool:
                for row in pool.imap(_worker, cell_tasks[1:], chunksize=4):
                    records.append(_persist(row, trace_handle, event_handle, trace_digest, event_digest)); rows.append(row)
    expected = list(range(4_120_000, 4_123_000))
    if [row["seed"] for row in rows] != expected or len({row["seed"] for row in rows}) != 3000:
        raise RuntimeError("post-execution seed custody failure")
    hashes = {
        "challenge": "C-V36C", "trace_file": TRACE_PATH.name,
        "trace_file_sha256": trace_digest.hexdigest(),
        "event_hash_file": EVENT_HASH_PATH.name,
        "event_hash_file_sha256": event_digest.hexdigest(),
        "row_count": len(rows), "seed_start": expected[0], "seed_end": expected[-1],
        "ascending_gap_free": True, "records": records,
        "custody_order": "Rows and event hashes were flushed and fsynced before aggregation.",
    }
    _write_json_exclusive(TRACE_HASHES_PATH, hashes)
    if hashlib.sha256(TRACE_PATH.read_bytes()).hexdigest() != trace_digest.hexdigest():
        raise RuntimeError("trace rehash failure")
    if hashlib.sha256(EVENT_HASH_PATH.read_bytes()).hexdigest() != event_digest.hexdigest():
        raise RuntimeError("event-hash rehash failure")
    return rows


def _paired(rows, cell, floor, analysis_seed):
    chosen = [row for row in rows if row["cell"] == cell]
    values = [float(row["paired_difference"]) for row in chosen]
    interval = _bootstrap(values, analysis_seed); mean = float(np.mean(values))
    return {
        "cell": cell, "field": chosen[0]["field"], "world_pairs": len(values),
        "mean_full_minus_ablation": mean, "interval_95": interval,
        "frozen_floor": floor, "floor_met": mean >= floor,
        "positive_sign_carried": interval[0] > 0.0,
        "whole_world_bootstrap_replicates": 4000,
        "deterministic_analysis_seed": analysis_seed,
        "passed": mean >= floor and interval[0] > 0.0,
    }


def _population_distributions(rows):
    output = {}
    for cell in ("cell_c1_context", "cell_c2_broadcast", "cell_c3_denied", "cell_c4_stakes"):
        selected = [row for row in rows if row["cell"] == cell]
        arms = ("left_high", "right_low") if cell == "cell_c4_stakes" else ("ablation", "full")
        output[cell] = {
            arm: {
                field: _distribution(row[arm][field] for row in selected)
                for field in ("q_external_danger", "q_identity_organization")
            }
            for arm in arms
        }
    return output


def _evaluate(rows, freeze):
    criteria = {
        "criterion_1": _paired(rows, "cell_c1_context", 0.4840615966920863, 36_201),
        "criterion_2": _paired(rows, "cell_c2_broadcast", 0.2285343371910469, 36_202),
        "criterion_3": _paired(rows, "cell_c3_denied", 0.06642048890922031, 36_203),
    }
    stakes = [row for row in rows if row["cell"] == "cell_c4_stakes"]
    effects = [float(row["q_policy_open_low_minus_high"]) for row in stakes]
    interval = _bootstrap(effects, 36_204); mean = float(np.mean(effects))
    identity_max = max(float(row["scientific_identity_error"]) for row in stakes)
    criteria["criterion_4"] = {
        "cell": "cell_c4_stakes", "world_pairs": len(stakes),
        "scientific_identity_error_max": identity_max,
        "scientific_identity_tolerance": 1e-10,
        "scientific_identity_every_pair": identity_max <= 1e-10,
        "q_policy_open_low_minus_high_mean": mean, "interval_95": interval,
        "frozen_floor": 0.0522537705013991,
        "floor_met": mean >= 0.0522537705013991,
        "positive_sign_carried": interval[0] > 0.0,
        "passed": identity_max <= 1e-10 and mean >= 0.0522537705013991 and interval[0] > 0.0,
    }
    premature = {
        "first_pilot": {"mean": 0.015139500753264512, "interval_95": [-0.018567536075274952, 0.04911686181384986], "original_declaration": "equivalence"},
        "fresh_event_indexed_pilot": {"mean": -0.007591287369016907, "interval_95": [-0.03688060730166053, 0.021721859932301718], "original_declaration": "positive causal effect"},
        "classification": "DESCRIPTIVE_RETAINED_FINDING", "floor": None, "gate_criterion": False,
    }
    custody_pass = (
        len(rows) == 3000 and len({row["seed"] for row in rows}) == 3000
        and [row["seed"] for row in rows] == list(range(4_120_000, 4_123_000))
    )
    criteria["criterion_5"] = {
        "population_distributions_descriptive_no_floor": _population_distributions(rows),
        "premature_do_over_retained_finding": premature,
        "consumed": len(rows), "unique": len({row["seed"] for row in rows}),
        "ascending_gap_free": custody_pass,
        "event_ledgers_persisted_before_aggregation": True,
        "escrow_remainder_retired_unconsumed": [4_123_000, 4_129_999],
        "trace_hash_record": TRACE_HASHES_PATH.name, "passed": custody_pass,
    }
    overall = all(item["passed"] for item in criteria.values())
    return {
        "challenge": "C-V36C", "immutable_verdict": "PASS" if overall else "FAIL",
        "criteria": criteria,
        "verdict_classes": {
            "scientific": "PASS" if all(criteria[f"criterion_{i}"]["passed"] for i in (1, 2, 3, 4)) else "FAIL",
            "reporting_custody": "PASS" if criteria["criterion_5"]["passed"] else "FAIL",
        },
        "challenge_sha256": EXPECTED_SHA256,
        "parse_method": "ast.literal_eval on the exact bracketed literal line only",
        "frozen_identity": freeze,
        "trace_sha256": hashlib.sha256(TRACE_PATH.read_bytes()).hexdigest(),
        "event_hash_ledger_sha256": hashlib.sha256(EVENT_HASH_PATH.read_bytes()).hexdigest(),
        "verdict_written_before_interpretation": True, "one_shot": True,
    }


def _report(verdict):
    c = verdict["criteria"]
    lines = ["# C-V36C sealed challenge verdict", "", f"Immutable sealed verdict: **{verdict['immutable_verdict']}**.", "", "## Criterion results", ""]
    for index in (1, 2, 3):
        item = c[f"criterion_{index}"]
        lines.append(f"{index}. **{'PASS' if item['passed'] else 'FAIL'}** — `{item['field']}` mean full-minus-ablation {item['mean_full_minus_ablation']:.12g}; 95% CI [{item['interval_95'][0]:.12g}, {item['interval_95'][1]:.12g}]; frozen floor {item['frozen_floor']:.12g}; {item['world_pairs']} pairs.")
    item = c["criterion_4"]
    lines.append(f"4. **{'PASS' if item['passed'] else 'FAIL'}** — scientific-posterior identity error max {item['scientific_identity_error_max']:.12g} (tolerance 1e-10); low-minus-high `q_policy_open` mean {item['q_policy_open_low_minus_high_mean']:.12g}, 95% CI [{item['interval_95'][0]:.12g}, {item['interval_95'][1]:.12g}], frozen floor {item['frozen_floor']:.12g}.")
    lines.extend(["", f"5. **{'PASS' if c['criterion_5']['passed'] else 'FAIL'}** — all population distributions are published in the machine verdict; 3,000 seeds were consumed once, ascending and gap-free; escrow 4123000:4129999 is retired unconsumed.", "", "Premature-do-over retained finding (descriptive; no criterion):", "", "- First pilot: mean 0.015139500753264512; 95% CI [-0.018567536075274952, 0.04911686181384986].", "- Fresh event-indexed pilot: mean -0.007591287369016907; 95% CI [-0.03688060730166053, 0.021721859932301718].", "", "## Verdict classes", "", f"- Scientific: **{verdict['verdict_classes']['scientific']}**", f"- Reporting/custody: **{verdict['verdict_classes']['reporting_custody']}**", "", "## Interpretation", "", "The immutable result above is retained as written. The cells test context scoping, witnessing, contact-outcome learning, and the exact separation between stakes-invariant beliefs and stakes-sensitive policy.", "", f"Raw trace SHA-256: `{verdict['trace_sha256']}`.  ", f"Event-hash ledger SHA-256: `{verdict['event_hash_ledger_sha256']}`.", ""])
    with VERDICT_MD.open("xb") as handle:
        handle.write("\n".join(lines).encode()); handle.flush(); os.fsync(handle.fileno())


def main():
    tasks = _validate(_parse()); freeze = _verify_freeze(); rows = _execute(tasks)
    verdict = _evaluate(rows, freeze)
    _write_json_exclusive(VERDICT_JSON, verdict)
    _report(verdict)


if __name__ == "__main__":
    main()
