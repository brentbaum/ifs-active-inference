#!/usr/bin/env python3
"""One-shot custody runner for the revealed C-V35B challenge."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import sys
from dataclasses import asdict, replace
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Mapping

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "V3.5"
CHALLENGE = ROOT / "sealed-revealed" / "C-V35B-protect-challenge.md"
FREEZE_MANIFEST = RESULTS / "freeze-manifest.json"
PARAMETERS = ROOT / "protocols" / "v3.5-parameters.json"
LEDGER = ROOT.parents[1] / "ifs-paper" / "suite-v2-sealed-hashes.md"
TRACE_PATH = RESULTS / "cv35b-challenge-traces.jsonl"
HASH_PATH = RESULTS / "cv35b-challenge-trace-hashes.json"
RAW_SEAL_PATH = RESULTS / "cv35b-challenge-raw-seal.json"
VERDICT_PATH = RESULTS / "cv35b-challenge-verdict.json"
REPORT_PATH = RESULTS / "cv35b-challenge-report.md"
ESCROW = (4_055_000, 4_059_999)
EXPECTED_CHALLENGE_SHA256 = (
    "b57339b9b1e8200ab94cf489870fbf3ae2a11a1041ce1b7762e1d65810403127"
)
TOLERANCE = 1e-10
ROPE = 0.01

sys.path.insert(0, str(ROOT))
from ref import v35, v35_oracle  # noqa: E402
from ref.trace_sink import traced_execution  # noqa: E402


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(child) for child in value]
    if hasattr(value, "__dataclass_fields__"):
        return _plain(asdict(value))
    if isinstance(value, np.generic):
        return value.item()
    return value


def _canonical(value: Any) -> bytes:
    return (
        json.dumps(
            _plain(value), sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: Any, *, sort_keys: bool = True) -> None:
    path.write_text(
        json.dumps(
            _plain(value), indent=2, sort_keys=sort_keys, allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _parse_bundle() -> dict[str, Any]:
    text = CHALLENGE.read_text(encoding="utf-8")
    start = text.index("{'parse_instruction'")
    end = text.index("\n\n## Criteria", start)
    literal = text[start:end]
    bundle = ast.literal_eval(literal)
    if not isinstance(bundle, dict) or len(bundle) != 14:
        raise RuntimeError("sealed bracketed literal did not parse as 13 cells")
    bundle["_literal_sha256"] = hashlib.sha256(
        literal.encode("utf-8")
    ).hexdigest()
    return bundle


def _verify_pre_execution(bundle: Mapping[str, Any]) -> dict[str, Any]:
    forbidden_existing = [
        path for path in (
            TRACE_PATH, HASH_PATH, RAW_SEAL_PATH, VERDICT_PATH, REPORT_PATH,
        )
        if path.exists()
    ]
    if forbidden_existing:
        raise RuntimeError(
            "C-V35B single-run artifacts already exist: "
            + ", ".join(str(path) for path in forbidden_existing)
        )
    challenge_hash = _sha256(CHALLENGE)
    if challenge_hash != EXPECTED_CHALLENGE_SHA256:
        raise RuntimeError("revealed challenge hash does not match its seal")
    ledger_text = LEDGER.read_text(encoding="utf-8")
    release_phrase = "Escrow 4055000:4059999 is RELEASED"
    if release_phrase not in ledger_text:
        raise RuntimeError("escrow release record is absent")
    manifest = json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in manifest["files"].items():
        target = ROOT / relative
        actual = _sha256(target) if target.exists() else None
        if actual != expected:
            mismatches.append({
                "file": relative, "expected": expected, "actual": actual,
            })
    if mismatches:
        raise RuntimeError(f"frozen identity mismatch: {mismatches}")
    seeds = []
    cells = []
    for name, cell in bundle.items():
        if not name.startswith("cell_"):
            continue
        start_text, end_text = cell["escrow"].split(":")
        start, end = int(start_text), int(end_text)
        expected_n = cell.get("n_pairs", cell.get("n_worlds"))
        if end - start + 1 != expected_n:
            raise RuntimeError(f"{name} count does not match its subblock")
        cells.append({"name": name, "start": start, "end": end})
        seeds.extend(range(start, end + 1))
    if seeds != list(range(ESCROW[0], ESCROW[1] + 1)):
        raise RuntimeError("sealed cell blocks are not ascending and gap-free")
    return {
        "challenge_sha256": challenge_hash,
        "literal_sha256": bundle["_literal_sha256"],
        "ledger_sha256": _sha256(LEDGER),
        "freeze_manifest_sha256": _sha256(FREEZE_MANIFEST),
        "freeze_files_verified": len(manifest["files"]),
        "freeze_mismatches": mismatches,
        "cells": cells,
        "released_block": list(ESCROW),
    }


def _config(changes: Mapping[str, Any]) -> v35.ProtectConfig:
    values = {
        "befriend": "all",
        "partner": "remaining",
        "stakes": "high",
        "policy_regime": "mixed",
        "mode_count": 3,
        "topology": "allied",
        "support_target": "all",
        "registration": "delivered",
        "denied_contact": "delivered",
        "length": 64,
    }
    values.update(changes)
    return v35.ProtectConfig(**values)


def _summary(posterior: Any) -> dict[str, Any]:
    return {
        "access": posterior.readouts["access_probability"],
        "trust": posterior.readouts["trust_remaining"],
        "support_response": posterior.support_response_posterior,
        "contact_response": posterior.contact_response_posterior,
        "topology": dict(posterior.topology_probabilities),
        "interventional_influence": posterior.interventional_influence,
        "joint_policy_y": posterior.edge_probabilities["JOINT_POLICY_Y"],
        "edge_probabilities": dict(posterior.edge_probabilities),
        "joint_policy_posterior": posterior.joint_policy_posterior,
        "structure_probabilities": posterior.probabilities,
        "normalization_error": abs(math.fsum(posterior.probabilities) - 1.0),
    }


def _structure_probabilities(posterior: Any) -> dict[tuple[Any, ...], float]:
    result: dict[tuple[Any, ...], float] = {}
    for probability, (structure, _sign) in zip(
        posterior.probabilities, posterior.components
    ):
        key = (
            structure.active_modes,
            structure.mode_root_edges,
            structure.joint_policy_outcome,
            structure.cross_mode_outcome,
        )
        result[key] = result.get(key, 0.0) + probability
    return result


def _credible_contains(probabilities: list[float], truth_index: int) -> bool:
    order = np.argsort(-np.asarray(probabilities))
    mass = 0.0
    for index in order:
        mass += probabilities[int(index)]
        if int(index) == truth_index:
            return True
        if mass >= 0.95:
            return False
    return False


def _oracle_error(world: Any) -> float:
    """Independent full-structure audit on a four-slice exact prefix."""
    audit_world = replace(world, observations=world.observations[:4])
    production = v35.score_world(audit_world)
    observations = [asdict(item) for item in audit_world.observations]
    keys, oracle_probabilities, _evidence = v35_oracle.posterior(observations)
    reliable_order = [
        reliable
        for structure in v35.PROGRAMS
        for _sign in ((-1, 1) if structure.cross_mode_outcome else (0,))
        for reliable in (0, 1)
    ]
    production_map = {
        (
            structure.active_modes,
            structure.mode_root_edges,
            structure.joint_policy_outcome,
            structure.cross_mode_outcome,
            sign,
            reliable,
        ): probability
        for probability, (structure, sign), reliable in zip(
            production.probabilities,
            production.components,
            reliable_order,
        )
    }
    return max(
        abs(production_map[key] - probability)
        for key, probability in zip(keys, oracle_probabilities)
    )


def _recovery_row(seed: int) -> dict[str, Any]:
    world = v35.generate_recovery_world(
        seed, length=64, released_block=ESCROW
    )
    posterior = v35.score_world(world)
    structure_map = _structure_probabilities(posterior)
    truth_key = (
        world.truth_structure.active_modes,
        world.truth_structure.mode_root_edges,
        world.truth_structure.joint_policy_outcome,
        world.truth_structure.cross_mode_outcome,
    )
    predicted = max(structure_map, key=structure_map.get)
    ordered = list(structure_map)
    truth_index = ordered.index(truth_key)
    probabilities = [structure_map[key] for key in ordered]
    truth_edges = tuple(v35.program_values(world.truth_structure).values())
    predicted_edges = (
        predicted[1][0], predicted[1][1], predicted[1][2],
        predicted[2], predicted[3],
    )
    truth_topology = (
        "independent" if world.truth_cross_sign == 0
        else "opposed" if world.truth_cross_sign < 0 else "coalition"
    )
    predicted_topology = max(
        posterior.topology_probabilities,
        key=posterior.topology_probabilities.get,
    )
    audited = seed < 4_059_620
    return {
        "truth_structure": truth_key,
        "predicted_structure": predicted,
        "edge_correct": [a == b for a, b in zip(predicted_edges, truth_edges)],
        "active_count_correct": predicted[0] == truth_key[0],
        "program_correct": predicted == truth_key,
        "confidence": structure_map[predicted],
        "coverage": _credible_contains(probabilities, truth_index),
        "topology_correct": predicted_topology == truth_topology,
        "partner_correct": int(np.argmax(posterior.q_partner))
        == world.truth_partner,
        "normalization_error": abs(math.fsum(posterior.probabilities) - 1.0),
        "oracle_audited": audited,
        "oracle_prefix_slices": 4 if audited else 0,
        "independent_oracle_error": _oracle_error(world) if audited else None,
    }


@traced_execution
def _worker(task: tuple[int, str, dict[str, Any]]) -> dict[str, Any]:
    seed, cell_name, cell = task
    row: dict[str, Any] = {"seed": seed, "cell": cell_name}
    if cell.get("recovery"):
        row["recovery"] = _recovery_row(seed)
        return row
    if cell_name == "cell_11_mode_dormancy":
        world = v35.generate_world(
            seed, _config(cell["config"]), released_block=ESCROW
        )
        posterior = v35.score_world(
            world, restrictions={"active_modes": (2,)}
        )
        row["posterior"] = _summary(posterior)
        row["dormant_effect"] = max(
            abs(posterior.interventional_influence[2][index])
            + abs(posterior.interventional_influence[index][2])
            for index in (0, 1)
        )
        return row
    if cell_name.startswith("cell_6_policy_") or cell_name.startswith(
        "cell_7_policy_"
    ) or cell_name.startswith("cell_8_policy_"):
        world = v35.generate_world(
            seed, _config(cell["config"]), released_block=ESCROW
        )
        masked = replace(
            world,
            observations=tuple(
                replace(observation, outcome=None)
                for observation in world.observations
            ),
        )
        row["masked"] = _summary(v35.score_world(masked))
        row["observed"] = _summary(v35.score_world(world))
        return row
    left_world = v35.generate_world(
        seed, _config(cell["left"]), released_block=ESCROW
    )
    right_world = v35.generate_world(
        seed, _config(cell["right"]), released_block=ESCROW
    )
    row["left"] = _summary(v35.score_world(left_world))
    row["right"] = _summary(v35.score_world(right_world))
    return row


def _make_tasks(bundle: Mapping[str, Any]) -> list[tuple[int, str, dict[str, Any]]]:
    tasks = []
    for name, cell in bundle.items():
        if not name.startswith("cell_"):
            continue
        start_text, end_text = cell["escrow"].split(":")
        tasks.extend(
            (seed, name, cell)
            for seed in range(int(start_text), int(end_text) + 1)
        )
    if [task[0] for task in tasks] != list(range(ESCROW[0], ESCROW[1] + 1)):
        raise RuntimeError("task construction violated ascending gap-free custody")
    return tasks


def _execute_and_seal(
    tasks: list[tuple[int, str, dict[str, Any]]], preflight: Mapping[str, Any]
) -> list[dict[str, Any]]:
    records = []
    rows = []
    file_hash = hashlib.sha256()
    processes = max(1, min(8, (os.cpu_count() or 2) - 1))
    with TRACE_PATH.open("xb") as handle:
        with get_context("spawn").Pool(processes) as pool:
            for row in pool.imap(_worker, tasks, chunksize=2):
                encoded = _canonical(row)
                handle.write(encoded)
                handle.flush()
                file_hash.update(encoded)
                records.append({
                    "seed": row["seed"],
                    "cell": row["cell"],
                    "sha256": hashlib.sha256(encoded).hexdigest(),
                })
                rows.append(row)
    hash_record = {
        "file": TRACE_PATH.name,
        "world_or_pair_records": len(rows),
        "file_sha256": file_hash.hexdigest(),
        "records": records,
    }
    _write_json(HASH_PATH, hash_record)
    raw_seal = {
        "status": "RAW_TRACES_AND_PER_WORLD_STATISTICS_SEALED_BEFORE_CRITERIA",
        "preflight": preflight,
        "trace_file": TRACE_PATH.name,
        "trace_file_sha256": file_hash.hexdigest(),
        "trace_hash_record": HASH_PATH.name,
        "trace_hash_record_sha256": _sha256(HASH_PATH),
        "record_count": len(rows),
        "seed_first": rows[0]["seed"],
        "seed_last": rows[-1]["seed"],
        "ascending_gap_free_once": [row["seed"] for row in rows]
        == list(range(ESCROW[0], ESCROW[1] + 1)),
        "criteria_evaluated_at_write_time": False,
    }
    _write_json(RAW_SEAL_PATH, raw_seal)
    return rows


def _interval(values: list[float], index: int) -> dict[str, Any]:
    array = np.asarray(values, dtype=float)
    rng = np.random.default_rng(35_500 + index)
    bootstrap = np.mean(
        array[rng.integers(0, len(array), size=(5_000, len(array)))], axis=1
    )
    return {
        "mean": float(array.mean()),
        "ci95": [
            float(np.quantile(bootstrap, 0.025)),
            float(np.quantile(bootstrap, 0.975)),
        ],
        "n": len(values),
        "bootstrap_replicates": 5_000,
    }


def _ece(confidence: list[float], correct: list[bool]) -> float:
    p = np.asarray(confidence)
    y = np.asarray(correct, dtype=float)
    value = 0.0
    for low in np.linspace(0, 0.9, 10):
        high = low + 0.1
        chosen = (p >= low) & (p <= high if high == 1 else p < high)
        if chosen.any():
            value += chosen.mean() * abs(p[chosen].mean() - y[chosen].mean())
    return float(value)


def _cell(rows: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    return [row for row in rows if row["cell"] == name]


def _effect(
    values: list[float], floor: float, index: int
) -> dict[str, Any]:
    metric = _interval(values, index)
    metric["floor"] = floor
    metric["mean_meets_floor"] = metric["mean"] >= floor
    metric["ci_carries_positive_sign"] = metric["ci95"][0] > 0.0
    metric["passed"] = (
        metric["mean_meets_floor"] and metric["ci_carries_positive_sign"]
    )
    return metric


def _evaluate(rows: list[dict[str, Any]], raw_seal: Mapping[str, Any]) -> dict[str, Any]:
    c1 = _cell(rows, "cell_1_befriend")
    c2 = _cell(rows, "cell_2_partner")
    c3 = _cell(rows, "cell_3_stakes")
    c4 = _cell(rows, "cell_4_support")
    c5 = _cell(rows, "cell_5_denied")
    c6 = _cell(rows, "cell_6_policy_exclusion")
    c7 = _cell(rows, "cell_7_policy_monitoring")
    c8 = _cell(rows, "cell_8_policy_engagement")
    c9 = _cell(rows, "cell_9_topology_opposed")
    c10 = _cell(rows, "cell_10_topology_allied")
    c11 = _cell(rows, "cell_11_mode_dormancy")
    c12 = _cell(rows, "cell_12_registration")
    c13 = _cell(rows, "cell_13_recovery")

    criteria: list[dict[str, Any]] = []
    criterion1_metrics = {
        "cell1_access": _effect(
            [r["right"]["access"] - r["left"]["access"] for r in c1],
            0.030808420228944897, 1,
        ),
        "cell1_support_response_3": _effect(
            [r["right"]["support_response"][2] - r["left"]["support_response"][2] for r in c1],
            0.25002964669658534, 2,
        ),
        "cell4_support_response_3": _effect(
            [r["right"]["support_response"][2] - r["left"]["support_response"][2] for r in c4],
            0.2500000001761959, 3,
        ),
        "cell4_access": _effect(
            [r["right"]["access"] - r["left"]["access"] for r in c4],
            0.031786343743120116, 4,
        ),
    }
    criteria.append({
        "criterion": 1,
        "name": "befriending_and_targeted_support",
        "passed": all(m["passed"] for m in criterion1_metrics.values()),
        "metrics": criterion1_metrics,
    })

    stakes_errors = [
        max(abs(a - b) for a, b in zip(
            r["right"]["structure_probabilities"],
            r["left"]["structure_probabilities"],
        ))
        for r in c3
    ]
    criterion2_metrics = {
        "cell2_trust_remaining": _effect(
            [r["right"]["trust"] - r["left"]["trust"] for r in c2],
            0.4999999999999974, 5,
        ),
        "cell2_access": _effect(
            [r["right"]["access"] - r["left"]["access"] for r in c2],
            0.0575741252904589, 6,
        ),
        "cell3_access_low_minus_high": _effect(
            [r["right"]["access"] - r["left"]["access"] for r in c3],
            0.05456176795537784, 7,
        ),
        "cell3_scientific_posterior_identity_error_max": {
            "value": max(stakes_errors),
            "tolerance": TOLERANCE,
            "passed": max(stakes_errors) <= TOLERANCE,
        },
    }
    criteria.append({
        "criterion": 2,
        "name": "partner_and_stakes",
        "passed": all(m["passed"] for m in criterion2_metrics.values()),
        "metrics": criterion2_metrics,
    })

    criterion3_metrics = {}
    for index, (name, cell, floor) in enumerate((
        ("cell6_exclusion", c6, 0.22369120540497045),
        ("cell7_monitoring", c7, 0.028590899494582652),
        ("cell8_engagement", c8, 0.2818778047497165),
    ), start=8):
        criterion3_metrics[name] = _effect(
            [r["observed"]["joint_policy_y"] - r["masked"]["joint_policy_y"] for r in cell],
            floor, index,
        )
    criteria.append({
        "criterion": 3,
        "name": "outcome_bearing_policy_histories",
        "passed": all(m["passed"] for m in criterion3_metrics.values()),
        "metrics": criterion3_metrics,
    })

    criterion4_metrics = {
        "cell5_contact_response_3": _effect(
            [r["right"]["contact_response"][2] - r["left"]["contact_response"][2] for r in c5],
            0.23462657827078734, 11,
        ),
        "cell5_access": _effect(
            [r["right"]["access"] - r["left"]["access"] for r in c5],
            0.011022406848183891, 12,
        ),
    }
    criteria.append({
        "criterion": 4,
        "name": "denied_contact",
        "passed": all(m["passed"] for m in criterion4_metrics.values()),
        "metrics": criterion4_metrics,
    })

    dormant_values = [r["dormant_effect"] for r in c11]
    criterion5_metrics = {
        "cell9_opposed_recovery": _effect(
            [r["right"]["topology"]["opposed"] - r["left"]["topology"]["opposed"] for r in c9],
            0.19077996532688585, 13,
        ),
        "cell9_opposed_D_0_1_negated_raw": _effect(
            [-r["right"]["interventional_influence"][0][1] for r in c9],
            0.021813188533686426, 14,
        ),
        "cell9_opposed_D_1_0_negated_raw": _effect(
            [-r["right"]["interventional_influence"][1][0] for r in c9],
            0.02162728537716363, 15,
        ),
        "cell10_allied_recovery": _effect(
            [r["right"]["topology"]["coalition"] - r["left"]["topology"]["coalition"] for r in c10],
            0.04582309257999451, 16,
        ),
        "cell10_allied_D_0_1": _effect(
            [r["right"]["interventional_influence"][0][1] for r in c10],
            0.004841000047368376, 17,
        ),
        "cell10_allied_D_1_0": _effect(
            [r["right"]["interventional_influence"][1][0] for r in c10],
            0.004820009680542292, 18,
        ),
        "cell11_dormant_effect_max": {
            "value": max(dormant_values),
            "tolerance": TOLERANCE,
            "all_worlds_pass": all(value <= TOLERANCE for value in dormant_values),
            "passed": all(value <= TOLERANCE for value in dormant_values),
        },
    }
    criteria.append({
        "criterion": 5,
        "name": "interventional_topology_and_exact_dormancy",
        "passed": all(m["passed"] for m in criterion5_metrics.values()),
        "metrics": criterion5_metrics,
    })

    registration_errors = [
        max(abs(a - b) for a, b in zip(
            r["right"]["structure_probabilities"],
            r["left"]["structure_probabilities"],
        ))
        for r in c12
    ]
    registration_policy = _interval(
        [r["right"]["access"] - r["left"]["access"] for r in c12], 19
    )
    registration_policy.update({
        "rope": [-ROPE, ROPE],
        "passed": registration_policy["ci95"][0] >= -ROPE
        and registration_policy["ci95"][1] <= ROPE,
    })
    criterion6_metrics = {
        "cell12_scientific_posterior_identity_error_max": {
            "value": max(registration_errors),
            "tolerance": TOLERANCE,
            "all_pairs_pass": all(value <= TOLERANCE for value in registration_errors),
            "passed": all(value <= TOLERANCE for value in registration_errors),
        },
        "cell12_policy_difference_equivalence": registration_policy,
    }
    criteria.append({
        "criterion": 6,
        "name": "registration_candidate_common_null",
        "passed": all(m["passed"] for m in criterion6_metrics.values()),
        "metrics": criterion6_metrics,
    })

    recovery = [r["recovery"] for r in c13]
    edge_accuracy = {
        name: float(np.mean([row["edge_correct"][index] for row in recovery]))
        for index, name in enumerate(v35.EDGE_NAMES)
    }
    audited_oracle_errors = [
        row["independent_oracle_error"] for row in recovery
        if row["oracle_audited"]
    ]
    recovery_metrics = {
        "active_count_accuracy": float(np.mean([r["active_count_correct"] for r in recovery])),
        "coverage": float(np.mean([r["coverage"] for r in recovery])),
        "ece": _ece([r["confidence"] for r in recovery], [r["program_correct"] for r in recovery]),
        "exact_program_accuracy": float(np.mean([r["program_correct"] for r in recovery])),
        "topology_accuracy": float(np.mean([r["topology_correct"] for r in recovery])),
        "edge_accuracy": edge_accuracy,
        "minimum_edge_accuracy": min(edge_accuracy.values()),
        "partner_accuracy": float(np.mean([r["partner_correct"] for r in recovery])),
        "normalization_error_max": max(r["normalization_error"] for r in recovery),
        "independent_oracle_error_max": max(audited_oracle_errors),
        "independent_oracle_audited_worlds": len(audited_oracle_errors),
        "independent_oracle_prefix_slices": 4,
    }
    recovery_checks = {
        "active_count_accuracy": recovery_metrics["active_count_accuracy"] >= 0.9,
        "coverage": recovery_metrics["coverage"] >= 0.8718750000000001,
        "ece": recovery_metrics["ece"] <= 0.06279020976257683,
        "exact_program_accuracy": recovery_metrics["exact_program_accuracy"] >= 0.49612500000000004,
        "topology_accuracy": recovery_metrics["topology_accuracy"] >= 0.61425,
        "minimum_edge_accuracy": recovery_metrics["minimum_edge_accuracy"] >= 0.6165,
        "partner_accuracy": recovery_metrics["partner_accuracy"] >= 0.9,
        "normalization_error_max": recovery_metrics["normalization_error_max"] <= TOLERANCE,
        "independent_oracle_error_max": recovery_metrics["independent_oracle_error_max"] <= TOLERANCE,
    }
    custody_checks = {
        "all_5000_seeds_once": len(rows) == 5_000 and len({r["seed"] for r in rows}) == 5_000,
        "ascending_gap_free": [r["seed"] for r in rows] == list(range(ESCROW[0], ESCROW[1] + 1)),
        "runtime_event_ledgers_persisted": all(r.get("_runtime_trace_events") for r in rows),
        "raw_sealed_before_criteria": raw_seal["criteria_evaluated_at_write_time"] is False,
        "trace_hash_matches": _sha256(TRACE_PATH) == raw_seal["trace_file_sha256"],
        "escrow_release_record_verified": True,
    }
    criteria.append({
        "criterion": 7,
        "name": "recovery_semantics_and_custody",
        "passed": all(recovery_checks.values()) and all(custody_checks.values()),
        "metrics": recovery_metrics,
        "recovery_checks": recovery_checks,
        "custody_checks": custody_checks,
    })
    return {
        "criteria": criteria,
        "overall": "PASS" if all(item["passed"] for item in criteria) else "FAIL",
    }


def _write_report(verdict: Mapping[str, Any]) -> None:
    immutable = verdict["immutable_verdict"]
    lines = [
        "# C-V35B sealed challenge report",
        "",
        "## Immutable sealed verdict",
        "",
        f"Overall: **{immutable['overall']}**.",
        "",
    ]
    for item in immutable["criteria"]:
        lines.append(
            f"- Criterion {item['criterion']} — {item['name']}: "
            f"**{'PASS' if item['passed'] else 'FAIL'}**."
        )
    lines.extend([
        "",
        "The verdict above was written only after the per-seed trace and",
        "statistics JSONL had been closed, hashed record-by-record, and sealed",
        "in `cv35b-challenge-raw-seal.json`. It is retained as written.",
        "",
        "## Verdict classes",
        "",
        f"- Scientific: **{verdict['verdict_classes']['scientific']}**.",
        f"- Semantic: **{verdict['verdict_classes']['semantic']}**.",
        f"- Custody: **{verdict['verdict_classes']['custody']}**.",
        "",
        "## Complete sealed statistics",
        "",
        "```json",
        json.dumps(_plain(immutable), indent=2, sort_keys=True, allow_nan=False),
        "```",
        "",
    ])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    bundle = _parse_bundle()
    preflight = _verify_pre_execution(bundle)
    tasks = _make_tasks(bundle)
    rows = _execute_and_seal(tasks, preflight)
    raw_seal = json.loads(RAW_SEAL_PATH.read_text(encoding="utf-8"))
    evaluated = _evaluate(rows, raw_seal)
    criterion_map = {item["criterion"]: item["passed"] for item in evaluated["criteria"]}
    verdict = {
        "immutable_verdict": {
            "overall": evaluated["overall"],
            "criteria": evaluated["criteria"],
        },
        "verdict_classes": {
            "scientific": "PASS" if all(criterion_map[i] for i in range(1, 7)) else "FAIL",
            "semantic": "PASS" if criterion_map[7] else "FAIL",
            "custody": "PASS" if criterion_map[7] else "FAIL",
        },
        "challenge": "C-V35B",
        "challenge_sha256": preflight["challenge_sha256"],
        "released_block": list(ESCROW),
        "raw_seal_file": RAW_SEAL_PATH.name,
        "raw_seal_sha256": _sha256(RAW_SEAL_PATH),
        "single_run": True,
        "reruns": 0,
        "threshold_adjustments": 0,
        "software_error": None,
    }
    _write_json(VERDICT_PATH, verdict, sort_keys=False)
    _write_report(verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
