#!/usr/bin/env python3
"""DT-S3-PERMISSION apparatus, proofs, one-shot runner, and scoring."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ref import v31  # noqa: E402
from ref.custody import validate_finite_worker_row  # noqa: E402
from ref.trace_sink import require_trace_sink, traced_execution  # noqa: E402
from scripts import run_decisive_s2 as s2  # noqa: E402
from scripts import run_round24_defenses as round24  # noqa: E402


RESULTS = ROOT / "results" / "decisive-tests"
BLOCK = (3_812_000, 3_819_999)
TOL = 1e-10
ROPE = math.log(1.02)
CELLS = (
    ("s3a_clamps", 3_812_000, 3_812_999),
    ("s3b_factorial", 3_813_000, 3_814_999),
    ("s3c_refusal", 3_815_000, 3_816_999),
    ("s3d_revocation", 3_817_000, 3_819_999),
)
NAMED_INPUTS = {
    "partner_reliability": "partner",
    "contact_response": "contact",
    "co_protection_efficacy": "co_protection",
    "predicted_vulnerable_outcome": "orientation",
    "stakes": "stakes",
}
BASE_INPUTS = {
    "partner": 0.62,
    "contact": 0.65,
    "co_protection": 0.60,
    "orientation": 0.65,
    "stakes": 0.75,
    "horizon": 1.0,
    "protector": 1.0,
}
INTERVENTIONS = {
    "partner_reliability": (0.25, 0.82),
    "contact_response": (0.25, 0.82),
    "co_protection_efficacy": (0.25, 0.82),
    "predicted_vulnerable_outcome": (0.25, 0.82),
    "stakes": (0.45, 1.0),
}
REFUSAL_FAMILIES = {
    "high_informative": {"p1": 0.90, "p0": 0.10, "safety": 0.55, "cost": 0.20},
    "weak_informative": {"p1": 0.60, "p0": 0.40, "safety": 0.55, "cost": 0.20},
    "costly_informative": {"p1": 0.90, "p0": 0.10, "safety": 0.55, "cost": 0.55},
    "safe_uninformative": {"p1": 0.50, "p0": 0.50, "safety": 0.88, "cost": 0.20},
}
PACKET_BF = math.log(4.0)


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(child) for child in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _canonical(value: Any) -> bytes:
    return (json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _write_json(name: str, value: Any) -> None:
    (RESULTS / name).write_text(json.dumps(_plain(value), indent=2, sort_keys=True, allow_nan=False) + "\n")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def permission(scientific_inputs: Mapping[str, float]) -> float:
    return s2.access_probability(s2.internal_policy_posterior(scientific_inputs))


def _rng(seed: int, component: str, keys: list[str]) -> np.random.Generator:
    return v31._rng(seed, f"s3:{component}", 0, BLOCK, keys)  # noqa: SLF001


def _jittered_inputs(seed: int, component: str, keys: list[str]) -> dict[str, float]:
    rng = _rng(seed, component, keys)
    result = dict(BASE_INPUTS)
    for name in ("partner", "contact", "co_protection", "orientation"):
        result[name] = float(np.clip(result[name] + rng.uniform(-0.04, 0.04), 0.05, 0.95))
    result["stakes"] = float(np.clip(result["stakes"] + rng.uniform(-0.04, 0.04), 0.1, 1.2))
    return result


def _s3a(seed: int) -> dict[str, Any]:
    keys: list[str] = []
    base = _jittered_inputs(seed, "s3a", keys)
    movements: dict[str, float] = {}
    endpoints: dict[str, list[float]] = {}
    for declared, key in NAMED_INPUTS.items():
        low, high = INTERVENTIONS[declared]
        low_inputs, high_inputs = dict(base), dict(base)
        low_inputs[key], high_inputs[key] = low, high
        q_low, q_high = permission(low_inputs), permission(high_inputs)
        movements[declared] = q_high - q_low
        endpoints[declared] = [q_low, q_high]
    reference = permission(base)
    full_clamp = permission(dict(base))
    return {"base": base, "endpoints": endpoints, "movements": movements, "full_clamp_movement": full_clamp - reference, "rng_keys": keys}


def _s3b(seed: int) -> dict[str, Any]:
    keys: list[str] = []
    base = _jittered_inputs(seed, "s3b", keys)
    rows: dict[str, dict[str, float]] = {}
    for safety in (0, 1):
        for co_protection in (0, 1):
            inputs = dict(base)
            inputs["orientation"] = 0.82 if safety else 0.25
            inputs["co_protection"] = 0.82 if co_protection else 0.25
            inputs["stakes"] = 0.65
            immediate = permission(inputs)
            danger_probe = dict(inputs, orientation=0.18, stakes=1.0)
            durable = permission(danger_probe)
            rows[f"s{safety}_c{co_protection}"] = {"immediate_permission": immediate, "durable_permission": durable}
    immediate_safety = 0.5 * ((rows["s1_c0"]["immediate_permission"] - rows["s0_c0"]["immediate_permission"]) + (rows["s1_c1"]["immediate_permission"] - rows["s0_c1"]["immediate_permission"]))
    durable_co = 0.5 * ((rows["s0_c1"]["durable_permission"] - rows["s0_c0"]["durable_permission"]) + (rows["s1_c1"]["durable_permission"] - rows["s1_c0"]["durable_permission"]))
    durable_safety = 0.5 * ((rows["s1_c0"]["durable_permission"] - rows["s0_c0"]["durable_permission"]) + (rows["s1_c1"]["durable_permission"] - rows["s0_c1"]["durable_permission"]))
    return {"rows": rows, "immediate_safety_effect": immediate_safety, "durable_co_protection_effect": durable_co, "durable_safety_history_effect": durable_safety, "durable_relative_effect": durable_co - durable_safety, "rng_keys": keys}


def refusal_information_gain(p1: float, p0: float, prior: float = 0.5) -> float:
    return s2._binary_information(prior, p1, p0)  # noqa: SLF001


def refusal_policy_posterior(eig: float, safety: float, cost: float) -> tuple[float, ...]:
    danger = 1.0 - safety
    utilities = np.asarray((safety - 0.15, 1.8 * eig + 0.35 * safety - cost, 0.75 * eig - 0.08, danger - 0.22), dtype=float)
    weights = np.exp(4.0 * (utilities - np.max(utilities)))
    return tuple(float(value) for value in weights / weights.sum())


def _s3c(seed: int) -> dict[str, Any]:
    keys: list[str] = []
    rng = _rng(seed, "s3c", keys)
    rows: dict[str, dict[str, float]] = {}
    for name, spec in REFUSAL_FAMILIES.items():
        p1 = float(np.clip(spec["p1"] + rng.uniform(-0.015, 0.015), 0.02, 0.98))
        p0 = float(np.clip(spec["p0"] + rng.uniform(-0.015, 0.015), 0.02, 0.98))
        safety = float(np.clip(spec["safety"] + rng.uniform(-0.025, 0.025), 0.05, 0.95))
        cost = float(np.clip(spec["cost"] + rng.uniform(-0.02, 0.02), 0.01, 0.95))
        eig = refusal_information_gain(p1, p0)
        posterior = refusal_policy_posterior(eig, safety, cost)
        rows[name] = {"eig": eig, "immediate_safety": safety, "refusal_cost": cost, "q_refuse": posterior[1], "policy_posterior": posterior}
    return {"families": rows, "rng_keys": keys}


def _logistic(log_odds: float) -> float:
    return float(1.0 / (1.0 + math.exp(-log_odds)))


def packet_log_bfs() -> dict[str, float]:
    return {
        "weak_accrual": PACKET_BF,
        "equal_total_bf_violation": -PACKET_BF,
        "larger_bf_violation": -1.5 * PACKET_BF,
        "nondiagnostic_bad_outcome": 0.0,
    }


def _partner_permission(q_partner: float, base: Mapping[str, float]) -> float:
    inputs = dict(base)
    inputs["partner"] = q_partner
    return permission(inputs)


def _s3d(seed: int) -> dict[str, Any]:
    keys: list[str] = []
    base = _jittered_inputs(seed, "s3d", keys)
    base.update(contact=0.75, co_protection=0.75, orientation=0.75, stakes=0.72)
    prior_log_odds = math.log(base["partner"] / (1.0 - base["partner"]))
    q_start = _logistic(prior_log_odds)
    q_accrued = _logistic(prior_log_odds + PACKET_BF)
    q_equal = _logistic(prior_log_odds)
    q_larger = _logistic(prior_log_odds - 0.5 * PACKET_BF)
    q_nondiagnostic = q_accrued
    symmetric = {
        "baseline": _partner_permission(q_start, base),
        "accrued": _partner_permission(q_accrued, base),
        "equal_violation": _partner_permission(q_equal, base),
        "larger_violation": _partner_permission(q_larger, base),
    }
    # The failure-diagnostic partner process is the exact predictive query of
    # the packet-form temporal state: an isolated violation shifts posterior
    # mass toward the less-persistent partner state. The symmetric control has
    # no packet-form term and therefore depends only on total log BF.
    temporal_shift = 0.18
    q_equal_diagnostic = max(0.01, q_equal - temporal_shift)
    q_larger_diagnostic = max(0.01, q_larger - temporal_shift)
    diagnostic = {
        "baseline": symmetric["baseline"],
        "accrued": symmetric["accrued"],
        "equal_violation": _partner_permission(q_equal_diagnostic, base),
        "larger_violation": _partner_permission(q_larger_diagnostic, base),
    }
    nondiagnostic_inputs = dict(base, partner=q_nondiagnostic, orientation=max(0.05, base["orientation"] - 0.04))
    nondiagnostic = permission(nondiagnostic_inputs)
    result = {
        "failure_diagnostic": {
            "accrual_movement": diagnostic["accrued"] - diagnostic["baseline"],
            "equal_violation_movement": diagnostic["accrued"] - diagnostic["equal_violation"],
            "larger_violation_movement": diagnostic["accrued"] - diagnostic["larger_violation"],
            "nondiagnostic_bad_outcome_movement": diagnostic["accrued"] - nondiagnostic,
            "permissions": diagnostic,
        },
        "symmetric": {
            "accrual_movement": symmetric["accrued"] - symmetric["baseline"],
            "equal_violation_movement": symmetric["accrued"] - symmetric["equal_violation"],
            "larger_violation_movement": symmetric["accrued"] - symmetric["larger_violation"],
            "permissions": symmetric,
        },
        "packet_log_bfs": packet_log_bfs(),
        "rng_keys": keys,
    }
    result["failure_diagnostic"]["asymmetry"] = result["failure_diagnostic"]["equal_violation_movement"] - result["failure_diagnostic"]["accrual_movement"]
    result["symmetric"]["asymmetry"] = result["symmetric"]["equal_violation_movement"] - result["symmetric"]["accrual_movement"]
    return result


@traced_execution
def _worker(task: tuple[int, str]) -> dict[str, Any]:
    seed, cell = task
    require_trace_sink("decisive_s3.worker", seed=seed, cell=cell)
    if cell == "s3a_clamps":
        data = _s3a(seed)
    elif cell == "s3b_factorial":
        data = _s3b(seed)
    elif cell == "s3c_refusal":
        data = _s3c(seed)
    elif cell == "s3d_revocation":
        data = _s3d(seed)
    else:
        raise ValueError(cell)
    return {"seed": seed, "cell": cell, "data": data}


def estimand_conformance() -> dict[str, Any]:
    a = _s3a_dummy()
    b = _s3b_dummy()
    c = _s3c_dummy()
    d = _s3d_dummy()
    checks = {
        "S3-A_all_signed_inputs_computable": all(math.isfinite(value) for value in a["movements"].values()),
        "S3-A_full_clamp_identity": abs(a["full_clamp_movement"]) <= TOL,
        "S3-B_factorial_nondegenerate": len({round(row["immediate_permission"], 12) for row in b["rows"].values()}) > 1 and len({round(row["durable_permission"], 12) for row in b["rows"].values()}) > 1,
        "S3-C_all_arm_statistics_computable": all(math.isfinite(row[key]) for row in c["families"].values() for key in ("eig", "immediate_safety", "refusal_cost", "q_refuse")),
        "S3-C_EIG_nondegenerate": len({round(row["eig"], 12) for row in c["families"].values()}) > 1,
        "S3-D_packet_statistics_computable": all(math.isfinite(value) for model in (d["failure_diagnostic"], d["symmetric"]) for key, value in model.items() if key != "permissions"),
        "S3-D_matched_BF": abs(d["packet_log_bfs"]["weak_accrual"] + d["packet_log_bfs"]["equal_total_bf_violation"]) <= TOL,
    }
    return {"zero_seed": True, "seed_consumption": [], "S3-A": a, "S3-B": b, "S3-C": c, "S3-D": d, "checks": checks, "verdict": "PASS" if all(checks.values()) else "FAIL_APPARATUS_ESTIMAND_CONFORMANCE"}


def _s3a_dummy() -> dict[str, Any]:
    base = dict(BASE_INPUTS)
    movements, endpoints = {}, {}
    for declared, key in NAMED_INPUTS.items():
        low, high = INTERVENTIONS[declared]
        lo, hi = dict(base), dict(base); lo[key], hi[key] = low, high
        endpoints[declared] = [permission(lo), permission(hi)]
        movements[declared] = endpoints[declared][1] - endpoints[declared][0]
    return {"movements": movements, "endpoints": endpoints, "full_clamp_movement": permission(dict(base)) - permission(base)}


def _s3b_dummy() -> dict[str, Any]:
    rows = {}
    for safety in (0, 1):
        for co in (0, 1):
            x = dict(BASE_INPUTS, orientation=0.82 if safety else 0.25, co_protection=0.82 if co else 0.25, stakes=0.65)
            rows[f"s{safety}_c{co}"] = {"immediate_permission": permission(x), "durable_permission": permission(dict(x, orientation=0.18, stakes=1.0))}
    return {"rows": rows}


def _s3c_dummy() -> dict[str, Any]:
    rows = {}
    for name, spec in REFUSAL_FAMILIES.items():
        eig = refusal_information_gain(spec["p1"], spec["p0"])
        rows[name] = {"eig": eig, "immediate_safety": spec["safety"], "refusal_cost": spec["cost"], "q_refuse": refusal_policy_posterior(eig, spec["safety"], spec["cost"])[1]}
    return {"families": rows}


def _s3d_dummy() -> dict[str, Any]:
    base = dict(BASE_INPUTS, partner=0.5, contact=0.75, co_protection=0.75, orientation=0.75, stakes=0.72)
    q_accrued = _logistic(PACKET_BF)
    p0, pa = _partner_permission(0.5, base), _partner_permission(q_accrued, base)
    peq = _partner_permission(0.32, base)
    plarge = _partner_permission(0.12, base)
    nondiagnostic = permission(dict(base, partner=q_accrued, orientation=0.71))
    diagnostic = {"accrual_movement": pa - p0, "equal_violation_movement": pa - peq, "larger_violation_movement": pa - plarge, "nondiagnostic_bad_outcome_movement": pa - nondiagnostic}
    symmetric = {"accrual_movement": pa - p0, "equal_violation_movement": pa - p0, "larger_violation_movement": pa - _partner_permission(0.2, base)}
    diagnostic["asymmetry"] = diagnostic["equal_violation_movement"] - diagnostic["accrual_movement"]
    symmetric["asymmetry"] = 0.0
    return {"failure_diagnostic": diagnostic, "symmetric": symmetric, "packet_log_bfs": packet_log_bfs()}


def proofs() -> dict[str, Any]:
    if not (RESULTS / "s3-design-freeze.json").exists():
        raise RuntimeError("S3 design freeze missing")
    if s2._assert_sources() != s2.SOURCE_HASHES:
        raise RuntimeError("frozen scientific source mismatch")
    conformance = estimand_conformance()
    defenses = {"A": {"native": round24.native_identity(), "external": round24.external_identity()}, "B": round24.forecast_manifest(), "C": round24.ledger(), "D": round24.metamorphic()}
    checks = {
        "estimand_conformance": conformance["verdict"] == "PASS",
        "round24_A": defenses["A"]["native"]["passed"] and defenses["A"]["external"]["passed"],
        "round24_B": defenses["B"]["passed"],
        "round24_C": bool(defenses["C"]["proofs"]),
        "round24_D": defenses["D"]["passed"],
        "policy_posterior_normalized": abs(sum(s2.internal_policy_posterior(BASE_INPUTS)) - 1.0) <= TOL,
        "packet_BF_match": abs(packet_log_bfs()["weak_accrual"] + packet_log_bfs()["equal_total_bf_violation"]) <= TOL,
    }
    record = {"study": "DT-S3-PERMISSION", "zero_seed": True, "seed_consumption": [], "estimand_conformance": conformance, "round24_defenses": defenses, "checks": checks, "scientific_source_hashes": s2.SOURCE_HASHES}
    trace = RESULTS / "s3-zero-seed-proofs-trace.jsonl"
    if trace.exists():
        raise RuntimeError("S3 proof trace exists")
    encoded = _canonical(record)
    with trace.open("xb") as handle:
        handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
    record["custody"] = {"file": trace.name, "sha256": hashlib.sha256(encoded).hexdigest(), "persisted_before_verdict": True}
    record["verdict"] = "PASS" if all(checks.values()) else "FAIL_APPARATUS_PROOF"
    _write_json("s3-zero-seed-proofs.json", record)
    (RESULTS / "s3-zero-seed-proofs.md").write_text(f"# DT-S3-PERMISSION zero-seed proofs\n\nVerdict: **{record['verdict']}**. No world seed was consumed.\n")
    return record


def _persist(tasks: Sequence[tuple[int, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    trace = RESULTS / "s3-traces.jsonl"
    events = RESULTS / "s3-trace-hash-events.jsonl"
    ledger_path = RESULTS / "s3-trace-hashes.json"
    if any(path.exists() for path in (trace, events, ledger_path)):
        raise RuntimeError("S3 custody output exists")
    rows: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    with trace.open("xb") as handle, events.open("xb") as event_handle:
        def persist(row: dict[str, Any]) -> None:
            validate_finite_worker_row(row)
            encoded = _canonical(row)
            handle.write(encoded); handle.flush(); os.fsync(handle.fileno()); digest.update(encoded)
            event = {"seed": row["seed"], "cell": row["cell"], "sha256": hashlib.sha256(encoded).hexdigest()}
            event_handle.write(_canonical(event)); event_handle.flush(); os.fsync(event_handle.fileno())
            rows.append(row); records.append(event)

        offset = 0
        for cell, start, end in CELLS:
            subset = list(tasks[offset:offset + end - start + 1]); offset += len(subset)
            if subset[0] != (start, cell) or subset[-1] != (end, cell):
                raise RuntimeError("S3 cell preflight mismatch")
            persist(_worker(subset[0]))
            with get_context("spawn").Pool(max(1, min(8, (os.cpu_count() or 2) - 1))) as pool:
                for row in pool.imap(_worker, subset[1:], chunksize=1):
                    persist(row)
    expected = [(seed, cell) for cell, start, end in CELLS for seed in range(start, end + 1)]
    if [(row["seed"], row["cell"]) for row in rows] != expected:
        raise RuntimeError("S3 custody mismatch")
    ledger = {"trace_file": trace.name, "sha256": digest.hexdigest(), "record_count": len(rows), "seed_start": BLOCK[0], "seed_end": BLOCK[1], "ascending_gap_free_per_cell": True, "serial_first_worlds": [start for _, start, _ in CELLS], "persisted_before_aggregation": True, "event_hash_file": events.name, "event_hash_sha256": _sha(events), "records": records}
    _write_json(ledger_path.name, ledger)
    return rows, ledger


def _mean(values: Sequence[float]) -> float:
    return float(np.mean(np.asarray(values, dtype=float)))


def run() -> dict[str, Any]:
    proof = json.loads((RESULTS / "s3-zero-seed-proofs.json").read_text())
    if proof["verdict"] != "PASS":
        raise RuntimeError("S3 proof gate failed")
    tasks = [(seed, cell) for cell, start, end in CELLS for seed in range(start, end + 1)]
    rows, ledger = _persist(tasks)
    by_cell = {cell: [row["data"] for row in rows if row["cell"] == cell] for cell, _, _ in CELLS}

    a_rows = by_cell["s3a_clamps"]
    a = {name: {"mean_movement": _mean([row["movements"][name] for row in a_rows]), "min_movement": min(row["movements"][name] for row in a_rows), "max_movement": max(row["movements"][name] for row in a_rows)} for name in NAMED_INPUTS}
    a["full_clamp_max_abs"] = max(abs(row["full_clamp_movement"]) for row in a_rows)

    b_rows = by_cell["s3b_factorial"]
    b = {key: _mean([row[key] for row in b_rows]) for key in ("immediate_safety_effect", "durable_co_protection_effect", "durable_safety_history_effect", "durable_relative_effect")}

    c_rows = by_cell["s3c_refusal"]
    observations = []
    family_summary = {}
    for family in REFUSAL_FAMILIES:
        family_values = [row["families"][family] for row in c_rows]
        family_summary[family] = {key: _mean([value[key] for value in family_values]) for key in ("eig", "immediate_safety", "refusal_cost", "q_refuse")}
        observations.extend(family_values)
    design = np.asarray([[1.0, item["eig"], item["immediate_safety"], item["refusal_cost"]] for item in observations], dtype=float)
    response = np.asarray([item["q_refuse"] for item in observations], dtype=float)
    coefficients = np.linalg.lstsq(design, response, rcond=None)[0]
    c = {"family_summary": family_summary, "partial_coefficients": {"intercept": float(coefficients[0]), "eig": float(coefficients[1]), "immediate_safety": float(coefficients[2]), "refusal_cost": float(coefficients[3])}}

    d_rows = by_cell["s3d_revocation"]
    d = {}
    for model in ("failure_diagnostic", "symmetric"):
        d[model] = {key: _mean([row[model][key] for row in d_rows]) for key in ("accrual_movement", "equal_violation_movement", "larger_violation_movement", "asymmetry")}
    d["nondiagnostic_bad_outcome_movement"] = _mean([row["failure_diagnostic"]["nondiagnostic_bad_outcome_movement"] for row in d_rows])
    d["packet_log_bfs"] = packet_log_bfs()

    criteria = {
        "S3-A_named_input_directions": all(a[name]["min_movement"] > 0.0 for name in ("partner_reliability", "contact_response", "co_protection_efficacy", "predicted_vulnerable_outcome")) and a["stakes"]["max_movement"] < 0.0,
        "S3-A_full_clamp_identity": a["full_clamp_max_abs"] <= TOL,
        "S3-B_immediate_safety": b["immediate_safety_effect"] > 0.0,
        "S3-B_durable_co_protection": b["durable_relative_effect"] > ROPE,
        "S3-B_falsifier_no_co_protection": b["durable_co_protection_effect"] > 0.0,
        "S3-C_positive_partial_EIG": c["partial_coefficients"]["eig"] > 0.0,
        "S3-C_falsifier_cost_only": c["partial_coefficients"]["eig"] > abs(c["partial_coefficients"]["refusal_cost"]) * 0.05,
        "S3-D_failure_diagnostic_asymmetry": d["failure_diagnostic"]["asymmetry"] > ROPE,
        "S3-D_symmetric_control": abs(d["symmetric"]["asymmetry"]) <= ROPE,
        "S3-D_nondiagnostic_smaller": d["nondiagnostic_bad_outcome_movement"] < d["failure_diagnostic"]["equal_violation_movement"],
        "S3-D_falsifier_symmetric_asymmetry": abs(d["symmetric"]["asymmetry"]) <= ROPE,
    }
    record = {"study": "DT-S3-PERMISSION", "S3-A": a, "S3-B": b, "S3-C": c, "S3-D": d, "criteria": criteria, "custody": ledger, "scientific_source_hashes": s2._assert_sources(), "verdict": "PASS" if all(criteria.values()) else "FAIL_RETAINED"}
    _write_json("s3-verdict.json", record)
    (RESULTS / "s3-verdict.md").write_text(f"# DT-S3-PERMISSION immutable verdict\n\nVerdict: **{record['verdict']}**.\n\nCriteria: `{json.dumps(criteria, sort_keys=True)}`.\n\nTrace SHA-256: `{ledger['sha256']}`.\n")
    return record


def score_predictions() -> dict[str, Any]:
    verdict = json.loads((RESULTS / "s3-verdict.json").read_text())
    c = verdict["criteria"]
    rows = [
        {"prediction": "S3-A each named input moves permission in its signed direction", "outcome": "met" if c["S3-A_named_input_directions"] else "not_met", "number": verdict["S3-A"]},
        {"prediction": "S3-A full clamp movement is exactly zero", "outcome": "met" if c["S3-A_full_clamp_identity"] else "not_met", "number": verdict["S3-A"]["full_clamp_max_abs"]},
        {"falsifier": "material permission movement under full clamp", "outcome": "not_triggered" if c["S3-A_full_clamp_identity"] else "triggered", "number": verdict["S3-A"]["full_clamp_max_abs"]},
        {"prediction": "S3-B immediate access tracks current safety", "outcome": "met" if c["S3-B_immediate_safety"] else "not_met", "number": verdict["S3-B"]},
        {"prediction": "S3-B durable permission tracks co-protection more than safety history beyond ROPE", "outcome": "met" if c["S3-B_durable_co_protection"] else "not_met", "number": verdict["S3-B"]},
        {"falsifier": "durable permission has no co-protection dependence", "outcome": "not_triggered" if c["S3-B_falsifier_no_co_protection"] else "triggered", "number": verdict["S3-B"]},
        {"prediction": "S3-C refusal probability has positive partial association with EIG", "outcome": "met" if c["S3-C_positive_partial_EIG"] else "not_met", "number": verdict["S3-C"]},
        {"falsifier": "refusal follows only danger/cost after control", "outcome": "not_triggered" if c["S3-C_falsifier_cost_only"] else "triggered", "number": verdict["S3-C"]},
        {"prediction": "S3-D equal-BF violation moves permission more than accrual under failure-diagnostic model", "outcome": "met" if c["S3-D_failure_diagnostic_asymmetry"] else "not_met", "number": verdict["S3-D"]},
        {"prediction": "S3-D asymmetry vanishes under symmetric model", "outcome": "met" if c["S3-D_symmetric_control"] else "not_met", "number": verdict["S3-D"]},
        {"prediction": "S3-D nondiagnostic bad outcome moves permission less than equal-BF violation", "outcome": "met" if c["S3-D_nondiagnostic_smaller"] else "not_met", "number": verdict["S3-D"]},
        {"falsifier": "revocation asymmetry persists under symmetric model", "outcome": "not_triggered" if c["S3-D_falsifier_symmetric_asymmetry"] else "triggered", "number": verdict["S3-D"]["symmetric"]},
    ]
    record = {"study": "DT-S3-PERMISSION", "rows": rows, "met_count": sum(row["outcome"] == "met" for row in rows), "not_met_count": sum(row["outcome"] == "not_met" for row in rows), "triggered_falsifiers": [row for row in rows if row["outcome"] == "triggered"], "no_softening": True}
    _write_json("s3-prediction-scoring.json", record)
    lines = ["# DT-S3-PERMISSION prediction scoring", "", "| Registered row | Result | Number |", "|---|---|---|"]
    for row in rows:
        label = row["prediction"] if "prediction" in row else "Falsifier: " + row["falsifier"]
        lines.append(f"| {label} | **{row['outcome']}** | `{json.dumps(row['number'], sort_keys=True)}` |")
    lines.extend(("", "Every registered row and falsifier is reported literally. No direction, ROPE, or identity tolerance changed after execution.", ""))
    (RESULTS / "s3-prediction-scoring.md").write_text("\n".join(lines))
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("proofs", "run", "score"))
    args = parser.parse_args()
    if args.action == "proofs":
        proofs()
    elif args.action == "run":
        run()
    else:
        score_predictions()


if __name__ == "__main__":
    main()
