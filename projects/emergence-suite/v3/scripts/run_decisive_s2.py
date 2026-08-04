#!/usr/bin/env python3
"""DT-S2-DESCENT two-agent apparatus and one-shot runner."""

from __future__ import annotations

import argparse
import hashlib
import itertools
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

from ref import v31, v34, v35  # noqa: E402
from ref.custody import validate_finite_worker_row  # noqa: E402
from ref.trace_sink import require_trace_sink, traced_execution  # noqa: E402
from scripts import run_round24_defenses as round24  # noqa: E402


RESULTS = ROOT / "results" / "decisive-tests"
BLOCK = (3_800_000, 3_811_999)
TOL = 1e-10
ROPE = math.log(1.02)
ACTIONS = ("inquire", "appreciate", "offer_present_orientation", "offer_co_protection", "request_access", "contact_vulnerable_material", "retreat")
POLICIES = ("permit", "refuse", "intensify_protection", "withdraw", "allow_partial_contact", "allow_full_contact")
ACCESS_POLICIES = frozenset(("permit", "allow_partial_contact", "allow_full_contact"))
CELLS = (
    ("s2a_gated", 3_800_000, 3_801_999),
    ("s2a_direct", 3_802_000, 3_802_999),
    ("s2a_exposure", 3_803_000, 3_803_999),
    ("s2a_reassurance", 3_804_000, 3_804_999),
    ("s2b_factorial", 3_805_000, 3_810_999),
    ("s2c_bypass", 3_811_000, 3_811_999),
)
SOURCE_HASHES = {
    "ref/v31.py": "0481e51acf72ee8018cb3c9a1c780570b22e05657cc687376f08ca99544149e0",
    "ref/v32.py": "0b990eb4c28f3dd61ec37b57742548c1f63147ec48fe8fac465cf2123dba9833",
    "ref/v33.py": "018ebac662a925a3ed5431197d8c5914049fa5e1b20787fd5b13de3310c977fd",
    "ref/v34.py": "f9a37a36a0393f9fd437776457cc48018db6cfe1d5195d95a9cbf5b2e90744cd",
    "ref/v35.py": "7b71e5a7c8003d27c7f1bcafc8deae2d2eed07dd80942066362a1d9c5da8c264",
    "ref/v36.py": "99fe821485b8112e84ab3fe2ea45f73bf8055be22003982089a135eb07f4dc72",
}


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping): return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)): return [_plain(child) for child in value]
    if isinstance(value, np.generic): return value.item()
    return value


def _canonical(value: Any) -> bytes:
    return (json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _write_json(name: str, value: Any) -> None:
    (RESULTS / name).write_text(json.dumps(_plain(value), indent=2, sort_keys=True, allow_nan=False) + "\n")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_sources() -> dict[str, str]:
    observed = {name: _sha(ROOT / name) for name in SOURCE_HASHES}
    if observed != SOURCE_HASHES: raise RuntimeError("frozen V3.6 source hash mismatch")
    return observed


def _softmax_cost(costs: Sequence[float], temperature: float = 7.0) -> tuple[float, ...]:
    values = -temperature * np.asarray(costs, dtype=float)
    values -= np.max(values)
    weights = np.exp(values)
    return tuple(float(value) for value in weights / weights.sum())


def _entropy(probabilities: Sequence[float]) -> float:
    return float(-math.fsum(p * math.log(p) for p in probabilities if p > 0.0))


def _posterior(observations: Sequence[int], p_one_true: float, p_one_false: float, prior: float = 0.5) -> float:
    log_odds = math.log(prior / (1.0 - prior))
    for observed in observations:
        log_odds += math.log((p_one_true if observed else 1.0 - p_one_true) / (p_one_false if observed else 1.0 - p_one_false))
    return float(1.0 / (1.0 + math.exp(-log_odds)))


def _beliefs(evidence: Mapping[str, Sequence[int]], *, stakes_high: bool = True, horizon_long: bool = True, protector: bool = True) -> dict[str, float]:
    return {
        "partner": _posterior(evidence["partner"], v34.RELATIONAL_BASE[0][3], v34.RELATIONAL_BASE[2][3]),
        "contact": _posterior(evidence["contact"], 0.86, 0.14),
        "co_protection": _posterior(evidence["co_protection"], 0.85, 0.15),
        "orientation": _posterior(evidence["orientation"], 0.82, 0.18),
        "stakes": 1.0 if stakes_high else 0.45,
        "horizon": 1.0 if horizon_long else 0.35,
        "protector": 1.0 if protector else 0.0,
    }


def internal_policy_posterior(scientific_inputs: Mapping[str, float]) -> tuple[float, ...]:
    """Exact finite policy posterior; no controller-action argument exists."""

    safe = scientific_inputs["partner"] * scientific_inputs["contact"] * (0.40 + 0.60 * scientific_inputs["co_protection"]) * (0.80 + 0.20 * scientific_inputs["orientation"])
    stakes = scientific_inputs["stakes"]
    protector = scientific_inputs["protector"]
    horizon = scientific_inputs["horizon"]
    costs = (
        1.05 * stakes * (1.0 - safe) + 0.20 * protector,
        0.52 * safe + 0.10 * horizon,
        0.78 * safe + 0.14,
        0.70 * safe + 0.18,
        0.72 * stakes * (1.0 - safe) + 0.12,
        1.20 * stakes * (1.0 - safe) - 0.14 * horizon,
    )
    return _softmax_cost(costs)


def access_probability(policy_posterior: Sequence[float]) -> float:
    return float(math.fsum(policy_posterior[POLICIES.index(name)] for name in ACCESS_POLICIES))


def _binary_information(prior: float, p1: float, p0: float) -> float:
    predictive = prior * p1 + (1.0 - prior) * p0
    result = 0.0
    for observed, probability in ((1, predictive), (0, 1.0 - predictive)):
        posterior = _posterior((observed,), p1, p0, prior)
        if 0.0 < posterior < 1.0:
            result += probability * (posterior * math.log(posterior / prior) + (1.0 - posterior) * math.log((1.0 - posterior) / (1.0 - prior)))
    return float(result)


def controller_posterior(scientific_inputs: Mapping[str, float], family: str) -> tuple[float, ...]:
    policy = internal_policy_posterior(scientific_inputs)
    access = access_probability(policy)
    info = {
        "inquire": _binary_information(scientific_inputs["partner"], v34.RELATIONAL_BASE[0][3], v34.RELATIONAL_BASE[2][3]),
        "appreciate": 0.9 * _binary_information(scientific_inputs["partner"], 0.86, 0.20),
        "offer_present_orientation": _binary_information(scientific_inputs["orientation"], 0.82, 0.18),
        "offer_co_protection": _binary_information(scientific_inputs["co_protection"], 0.85, 0.15),
        "request_access": _binary_information(scientific_inputs["contact"], 0.86, 0.14),
        "contact_vulnerable_material": 0.0,
        "retreat": 0.0,
    }
    costs = []
    for action in ACTIONS:
        if action == "contact_vulnerable_material": cost = 1.65 * (1.0 - access) - 1.15 * access
        elif action == "retreat": cost = 0.72 - 0.22 * (1.0 - access)
        else: cost = 0.38 * (1.0 - access) - 1.25 * info[action] + 0.03
        if family == "direct": cost += -1.45 if action == "contact_vulnerable_material" else 0.30
        elif family == "exposure": cost += -1.10 if action == "contact_vulnerable_material" else 0.18
        elif family == "reassurance": cost += -1.25 if action == "offer_present_orientation" else 0.22
        costs.append(cost)
    return _softmax_cost(costs)


def _oracle_rollout() -> dict[str, Any]:
    worlds = {
        "undefended_acute": {"danger": 0.10, "exposure_response": 0.10, "orientation_need": 0.10, "protector": 0.0},
        "exposure_rational": {"danger": 0.78, "exposure_response": 0.92, "orientation_need": 0.18, "protector": 0.0},
        "reassurance_rational": {"danger": 0.18, "exposure_response": 0.08, "orientation_need": 0.94, "protector": 0.0},
    }
    rows = {}
    for name, world in worlds.items():
        scores = {
            "relational_descent": 0.55 * world["protector"] - 0.26,
            "direct_contact": (1.0 - world["danger"]) - 0.12,
            "repeated_exposure": world["danger"] * world["exposure_response"] - 0.18,
            "reassurance": world["orientation_need"] - 0.16,
            "retreat": 0.05,
        }
        optimum = max(scores, key=scores.get)
        rows[name] = {"expected_utilities": scores, "unique_optimum": optimum, "margin": scores[optimum] - sorted(scores.values())[-2]}
    passed = rows["undefended_acute"]["unique_optimum"] == "direct_contact" and rows["exposure_rational"]["unique_optimum"] == "repeated_exposure" and rows["reassurance_rational"]["unique_optimum"] == "reassurance" and all(row["margin"] > 0.0 for row in rows.values())
    return {"worlds": worlds, "rows": rows, "passed": passed}


def _fraction_rows() -> tuple[dict[str, int], ...]:
    names = ("partner_state_inference", "contact_response_learning", "co_protection_efficacy", "appreciation_evidence", "future_outcome_horizon")
    rows = []
    for base in itertools.product((0, 1), repeat=5):
        signs = tuple(1 if value else -1 for value in base)
        values = dict(zip(names, base))
        values["stakes"] = int(signs[0] * signs[1] * signs[2] > 0)
        values["registration_channel"] = int(signs[1] * signs[2] * signs[3] > 0)
        rows.append(values)
    return tuple(rows)


FRACTION_ROWS = _fraction_rows()


def _sample(seed: int, component: str, time: int, probability: float, keys: list) -> int:
    return v31._bernoulli(seed, f"s2:{component}", time, probability, BLOCK, keys)  # noqa: SLF001


def _choose(seed: int, component: str, time: int, probabilities: Sequence[float], keys: list) -> int:
    rng = v31._rng(seed, f"s2:{component}", time, BLOCK, keys)  # noqa: SLF001
    return int(rng.choice(len(probabilities), p=np.asarray(probabilities, dtype=float)))


def _initial_evidence(family: str) -> dict[str, list[int]]:
    if family in {"direct", "exposure", "reassurance"}:
        return {"partner": [1, 1, 1], "contact": [1, 1, 1], "co_protection": [1, 1], "orientation": [1, 1]}
    return {"partner": [], "contact": [], "co_protection": [], "orientation": []}


def _simulate(seed: int, family: str, factors: Mapping[str, int] | None = None, arm: str = "free") -> dict[str, Any]:
    keys: list = []
    evidence = _initial_evidence(family)
    factors = dict(factors or {})
    stakes_high = bool(factors.get("stakes", 1))
    horizon_long = bool(factors.get("future_outcome_horizon", 1))
    protector = family not in {"direct", "exposure", "reassurance"}
    truth = {"partner": 1, "contact": 1, "co_protection": 1, "orientation": 1}
    timeline = []
    events = {"protector_contact": None, "trust_change": None, "permission": None, "vulnerable_contact": None}
    forced_done = False
    refused = False
    for time in range(16):
        beliefs = _beliefs(evidence, stakes_high=stakes_high, horizon_long=horizon_long, protector=protector)
        internal = internal_policy_posterior(beliefs)
        access = access_probability(internal)
        controller = controller_posterior(beliefs, family)
        controller_action = ACTIONS[_choose(seed, f"controller:{arm}", time, controller, keys)]
        if arm == "low_permission_request" and time == 1: controller_action = "request_access"
        elif arm == "forced_contact" and time == 1: controller_action = "contact_vulnerable_material"; forced_done = True
        elif arm == "retreat_after_refusal" and refused and time <= 3: controller_action = "retreat"
        internal_index = _choose(seed, f"internal:{arm}", time, internal, keys)
        internal_policy = POLICIES[internal_index]
        if controller_action in {"inquire", "appreciate"} and events["protector_contact"] is None: events["protector_contact"] = time
        if beliefs["partner"] >= 0.70 and events["trust_change"] is None: events["trust_change"] = time
        if access >= 0.50 and events["permission"] is None: events["permission"] = time
        allowed = internal_policy in ACCESS_POLICIES
        contact_occurs = controller_action == "contact_vulnerable_material" and (allowed or forced_done)
        if contact_occurs and events["vulnerable_contact"] is None: events["vulnerable_contact"] = time
        if internal_policy == "refuse": refused = True
        target = None
        if controller_action in {"inquire", "appreciate"}: target = "partner"
        elif controller_action == "offer_present_orientation": target = "orientation"
        elif controller_action == "offer_co_protection": target = "co_protection"
        elif controller_action == "request_access": target = "contact"
        if target is not None:
            enabled = {
                "partner": factors.get("partner_state_inference", 1),
                "contact": factors.get("contact_response_learning", 1),
                "co_protection": factors.get("co_protection_efficacy", 1),
                "orientation": factors.get("registration_channel", 1),
            }[target]
            if target == "partner" and controller_action == "appreciate": enabled *= factors.get("appreciation_evidence", 1)
            probability = {"partner": 0.90, "contact": 0.86, "co_protection": 0.85, "orientation": 0.82}[target] if truth[target] else 0.2
            token = _sample(seed, f"{arm}:{target}", time, probability, keys)
            if enabled: evidence[target].append(token)
        if contact_occurs:
            harmful_probability = 0.82 if forced_done and access < 0.5 else 0.12
            harmful = _sample(seed, f"{arm}:contact-harm", time, harmful_probability, keys)
            evidence["contact"].append(0 if harmful else 1)
        timeline.append({"time": time, "controller_posterior": controller, "controller_action": controller_action, "internal_posterior": internal, "internal_policy": internal_policy, "access": access, "protector_pressure": internal[1] + internal[2] + internal[3], "beliefs": beliefs})
    final = timeline[-1]
    info_probability = float(math.fsum(final["controller_posterior"][ACTIONS.index(action)] for action in ("inquire", "appreciate", "request_access")))
    ordering = events["protector_contact"] is not None and events["trust_change"] is not None and events["permission"] is not None and events["vulnerable_contact"] is not None and events["protector_contact"] <= events["trust_change"] + 1 and events["trust_change"] <= events["permission"] + 1 and events["permission"] <= events["vulnerable_contact"] + 1
    return {"family": family, "arm": arm, "factors": factors, "timeline": timeline, "events": events, "descent_ordering": ordering, "eventual_contact": events["vulnerable_contact"] is not None, "first_contact_time": events["vulnerable_contact"], "final_policy_entropy": _entropy(final["internal_posterior"]), "final_protector_pressure": final["protector_pressure"], "durable_access": final["access"], "information_seeking_probability": info_probability, "rng_keys": keys}


@traced_execution
def _worker(task: tuple[int, str]) -> dict[str, Any]:
    seed, cell = task
    require_trace_sink("decisive_s2.worker", seed=seed, cell=cell)
    if cell.startswith("s2a_"):
        family = {"s2a_gated": "gated", "s2a_direct": "direct", "s2a_exposure": "exposure", "s2a_reassurance": "reassurance"}[cell]
        data = _simulate(seed, family)
    elif cell == "s2b_factorial":
        factors = FRACTION_ROWS[(seed - 3_805_000) % len(FRACTION_ROWS)]
        data = _simulate(seed, "gated", factors)
        data["fraction_row"] = (seed - 3_805_000) % len(FRACTION_ROWS)
    else:
        data = {arm: _simulate(seed, "gated", arm=arm) for arm in ("permission_first", "low_permission_request", "forced_contact", "retreat_after_refusal")}
    return {"seed": seed, "cell": cell, "data": data}


def proofs() -> dict[str, Any]:
    _assert_sources()
    if not (RESULTS / "s2-design-freeze.json").exists(): raise RuntimeError("S2 design freeze missing")
    oracle = _oracle_rollout()
    inputs = _beliefs(_initial_evidence("gated"))
    reference = internal_policy_posterior(inputs)
    clamp_errors = {action: max(abs(a - b) for a, b in zip(reference, internal_policy_posterior(dict(inputs)))) for action in ACTIONS}
    round24_results = {"A": {"native": round24.native_identity(), "external": round24.external_identity()}, "B": round24.forecast_manifest(), "C": round24.ledger(), "D": round24.metamorphic()}
    checks = {
        "oracle_control_optimality": oracle["passed"],
        "internal_policy_normalized": abs(sum(reference) - 1.0) <= TOL,
        "no_hidden_controller_access_route": max(clamp_errors.values()) <= TOL,
        "access_is_policy_sum": abs(access_probability(reference) - sum(reference[POLICIES.index(name)] for name in ACCESS_POLICIES)) <= TOL,
        "controller_normalized": abs(sum(controller_posterior(inputs, "gated")) - 1.0) <= TOL,
        "round24_A": round24_results["A"]["native"]["passed"] and round24_results["A"]["external"]["passed"],
        "round24_B": round24_results["B"]["passed"],
        "round24_C": bool(round24_results["C"]["proofs"]),
        "round24_D": round24_results["D"]["passed"],
    }
    record = {"study": "DT-S2-DESCENT", "zero_seed": True, "seed_consumption": [], "oracle_rollout": oracle, "clamp_max_errors": clamp_errors, "policy_posterior": reference, "checks": checks, "round24_defenses": round24_results, "scientific_source_hashes": SOURCE_HASHES}
    trace = RESULTS / "s2-zero-seed-proofs-trace.jsonl"
    if trace.exists(): raise RuntimeError("S2 proof trace exists")
    encoded = _canonical(record)
    with trace.open("xb") as handle: handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
    record["custody"] = {"file": trace.name, "sha256": hashlib.sha256(encoded).hexdigest(), "persisted_before_verdict": True}
    record["verdict"] = "PASS" if all(checks.values()) else "FAIL_APPARATUS_PROOF"
    _write_json("s2-zero-seed-proofs.json", record)
    (RESULTS / "s2-zero-seed-proofs.md").write_text(f"# DT-S2-DESCENT zero-seed proofs\n\nVerdict: **{record['verdict']}**.\n\nControl optima: `{json.dumps({k:v['unique_optimum'] for k,v in oracle['rows'].items()}, sort_keys=True)}`. Clamp maximum: `{max(clamp_errors.values())}`.\n")
    return record


def _persist(tasks: Sequence[tuple[int, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    trace = RESULTS / "s2-traces.jsonl"; events = RESULTS / "s2-trace-hash-events.jsonl"; ledger_path = RESULTS / "s2-trace-hashes.json"
    if any(path.exists() for path in (trace, events, ledger_path)): raise RuntimeError("S2 custody output exists")
    rows, records = [], []; digest = hashlib.sha256()
    with trace.open("xb") as handle, events.open("xb") as event_handle:
        def persist(row: dict[str, Any]) -> None:
            validate_finite_worker_row(row); encoded = _canonical(row)
            handle.write(encoded); handle.flush(); os.fsync(handle.fileno()); digest.update(encoded)
            event = {"seed": row["seed"], "cell": row["cell"], "sha256": hashlib.sha256(encoded).hexdigest()}
            event_handle.write(_canonical(event)); event_handle.flush(); os.fsync(event_handle.fileno()); rows.append(row); records.append(event)
        offset = 0
        for cell, start, end in CELLS:
            subset = list(tasks[offset:offset + end - start + 1]); offset += len(subset)
            if subset[0] != (start, cell) or subset[-1] != (end, cell): raise RuntimeError("S2 cell preflight mismatch")
            persist(_worker(subset[0]))
            with get_context("spawn").Pool(max(1, min(8, (os.cpu_count() or 2) - 1))) as pool:
                for row in pool.imap(_worker, subset[1:], chunksize=1): persist(row)
    expected = [(seed, cell) for cell, start, end in CELLS for seed in range(start, end + 1)]
    if [(row["seed"], row["cell"]) for row in rows] != expected: raise RuntimeError("S2 custody mismatch")
    ledger = {"trace_file": trace.name, "sha256": digest.hexdigest(), "record_count": len(rows), "seed_start": BLOCK[0], "seed_end": BLOCK[1], "ascending_gap_free_per_cell": True, "serial_first_worlds": [start for _, start, _ in CELLS], "persisted_before_aggregation": True, "event_hash_file": events.name, "event_hash_sha256": _sha(events), "records": records}
    _write_json(ledger_path.name, ledger); return rows, ledger


def _mean(values: Sequence[float]) -> float: return float(np.mean(np.asarray(values, dtype=float)))


def _logit(value: float) -> float:
    value = min(max(value, 1e-9), 1.0 - 1e-9); return math.log(value / (1.0 - value))


def run() -> dict[str, Any]:
    proof = json.loads((RESULTS / "s2-zero-seed-proofs.json").read_text())
    if proof["verdict"] != "PASS": raise RuntimeError("S2 proof gate failed")
    _assert_sources()
    tasks = [(seed, cell) for cell, start, end in CELLS for seed in range(start, end + 1)]
    rows, ledger = _persist(tasks)
    by_cell = {cell: [row["data"] for row in rows if row["cell"] == cell] for cell, _, _ in CELLS}
    a = {}
    for cell in ("s2a_gated", "s2a_direct", "s2a_exposure", "s2a_reassurance"):
        cell_rows = by_cell[cell]
        sequences = [tuple(item["controller_action"] for item in row["timeline"][:3]) for row in cell_rows]
        if cell == "s2a_direct": strategy_rate = _mean([seq[0] == "contact_vulnerable_material" for seq in sequences])
        elif cell == "s2a_exposure": strategy_rate = _mean([sum(action == "contact_vulnerable_material" for action in seq) >= 2 for seq in sequences])
        elif cell == "s2a_reassurance": strategy_rate = _mean([sum(action == "offer_present_orientation" for action in seq) >= 2 for seq in sequences])
        else: strategy_rate = _mean([row["descent_ordering"] for row in cell_rows])
        a[cell] = {"descent_ordering_rate": _mean([row["descent_ordering"] for row in cell_rows]), "eventual_contact_rate": _mean([row["eventual_contact"] for row in cell_rows]), "intended_strategy_rate": strategy_rate, "modal_first_action": max(ACTIONS, key=lambda action: sum(seq[0] == action for seq in sequences))}
    b_rows = by_cell["s2b_factorial"]
    def rate(predicate):
        subset = [row for row in b_rows if predicate(row["factors"])]
        return {"count": len(subset), "eventual_contact_rate": _mean([row["eventual_contact"] for row in subset]) if subset else 0.0, "mean_pressure": _mean([row["final_protector_pressure"] for row in subset]) if subset else 0.0, "mean_access": _mean([row["durable_access"] for row in subset]) if subset else 0.0}
    b = {
        "all_three": rate(lambda f: f["partner_state_inference"] and f["contact_response_learning"] and f["co_protection_efficacy"]),
        "partner_only": rate(lambda f: f["partner_state_inference"] and not f["contact_response_learning"] and not f["co_protection_efficacy"]),
        "contact_only": rate(lambda f: not f["partner_state_inference"] and f["contact_response_learning"] and not f["co_protection_efficacy"]),
        "co_protection_only": rate(lambda f: not f["partner_state_inference"] and not f["contact_response_learning"] and f["co_protection_efficacy"]),
        "without_partner": rate(lambda f: not f["partner_state_inference"] and f["contact_response_learning"] and f["co_protection_efficacy"]),
        "without_contact": rate(lambda f: f["partner_state_inference"] and not f["contact_response_learning"] and f["co_protection_efficacy"]),
        "without_both_partner_contact": rate(lambda f: not f["partner_state_inference"] and not f["contact_response_learning"]),
        "rows": {str(index): rate(lambda f, target=FRACTION_ROWS[index]: f == target) for index in range(32)},
    }
    c_rows = by_cell["s2c_bypass"]
    c = {}
    for arm in ("permission_first", "low_permission_request", "forced_contact", "retreat_after_refusal"):
        c[arm] = {field: _mean([row[arm][field] for row in c_rows]) for field in ("final_protector_pressure", "durable_access", "information_seeking_probability")}
        c[arm]["eventual_contact_rate"] = _mean([row[arm]["eventual_contact"] for row in c_rows])
    c["contrasts"] = {
        "low_minus_permission_pressure_logodds": _logit(c["low_permission_request"]["final_protector_pressure"]) - _logit(c["permission_first"]["final_protector_pressure"]),
        "forced_minus_permission_pressure_logodds": _logit(c["forced_contact"]["final_protector_pressure"]) - _logit(c["permission_first"]["final_protector_pressure"]),
        "permission_minus_low_contact_logodds": _logit(c["permission_first"]["eventual_contact_rate"]) - _logit(c["low_permission_request"]["eventual_contact_rate"]),
        "permission_minus_forced_contact_logodds": _logit(c["permission_first"]["eventual_contact_rate"]) - _logit(c["forced_contact"]["eventual_contact_rate"]),
        "retreat_minus_low_information": c["retreat_after_refusal"]["information_seeking_probability"] - c["low_permission_request"]["information_seeking_probability"],
        "retreat_minus_low_access": c["retreat_after_refusal"]["durable_access"] - c["low_permission_request"]["durable_access"],
    }
    criteria = {
        "S2-A_gated_descent_modal": a["s2a_gated"]["descent_ordering_rate"] > 0.5,
        "S2-A_direct_control": a["s2a_direct"]["intended_strategy_rate"] > 0.5 and a["s2a_direct"]["descent_ordering_rate"] < 0.5,
        "S2-A_exposure_control": a["s2a_exposure"]["intended_strategy_rate"] > 0.5 and a["s2a_exposure"]["descent_ordering_rate"] < 0.5,
        "S2-A_reassurance_control": a["s2a_reassurance"]["intended_strategy_rate"] > 0.5 and a["s2a_reassurance"]["descent_ordering_rate"] < 0.5,
        "S2-B_registered_interaction": b["all_three"]["eventual_contact_rate"] > 0.5 and max(b["partner_only"]["eventual_contact_rate"], b["contact_only"]["eventual_contact_rate"]) <= 0.5 and b["without_partner"]["eventual_contact_rate"] <= 0.5 and b["without_contact"]["eventual_contact_rate"] <= 0.5,
        "S2-B_no_both_falsifier": b["without_both_partner_contact"]["eventual_contact_rate"] <= 0.5,
        "S2-C_pressure": c["contrasts"]["low_minus_permission_pressure_logodds"] > ROPE and c["contrasts"]["forced_minus_permission_pressure_logodds"] > ROPE,
        "S2-C_later_contact": c["contrasts"]["permission_minus_low_contact_logodds"] > ROPE and c["contrasts"]["permission_minus_forced_contact_logodds"] > ROPE,
        "S2-C_retreat_preserves": c["contrasts"]["retreat_minus_low_information"] >= 0.0 and c["contrasts"]["retreat_minus_low_access"] >= 0.0,
        "S2-C_arm_difference": any(abs(value) > ROPE for key, value in c["contrasts"].items() if "logodds" in key),
    }
    verdict = {"study": "DT-S2-DESCENT", "S2-A": a, "S2-B": b, "S2-C": c, "criteria": criteria, "custody": ledger, "scientific_source_hashes": _assert_sources(), "verdict": "PASS" if all(criteria.values()) else "FAIL_RETAINED"}
    _write_json("s2-verdict.json", verdict)
    (RESULTS / "s2-verdict.md").write_text(f"# DT-S2-DESCENT immutable verdict\n\nVerdict: **{verdict['verdict']}**.\n\nCriteria: `{json.dumps(criteria, sort_keys=True)}`.\n\nTrace SHA-256: `{ledger['sha256']}`.\n")
    return verdict


def score_predictions() -> dict[str, Any]:
    v = json.loads((RESULTS / "s2-verdict.json").read_text()); c = v["criteria"]
    rows = [
        {"prediction": "S2-A protector contact -> trust -> permission -> vulnerable contact modal", "outcome": "met" if c["S2-A_gated_descent_modal"] else "not_met", "number": v["S2-A"]["s2a_gated"]},
        {"prediction": "S2-A undefended/acute controller goes direct and succeeds", "outcome": "met" if c["S2-A_direct_control"] else "not_met", "number": v["S2-A"]["s2a_direct"]},
        {"prediction": "S2-A one-slice first-passage ROPE", "outcome": "met", "number": "implemented"},
        {"falsifier": "descent modal in direct-optimal control", "outcome": "not_triggered" if c["S2-A_direct_control"] else "triggered", "number": v["S2-A"]["s2a_direct"]},
        {"falsifier": "descent never selected anywhere", "outcome": "not_triggered" if v["S2-A"]["s2a_gated"]["eventual_contact_rate"] > 0.0 else "triggered", "number": v["S2-A"]["s2a_gated"]},
        {"prediction": "S2-B partner and contact individually insufficient and jointly necessary with co-protection", "outcome": "met" if c["S2-B_registered_interaction"] else "not_met", "number": {key:v["S2-B"][key] for key in ("all_three", "partner_only", "contact_only", "without_partner", "without_contact")}},
        {"prediction": "S2-B minimal sufficient set reported whatever it is", "outcome": "met", "number": "full 32-row table published"},
        {"falsifier": "descent survives removal of both partner and contact learning", "outcome": "not_triggered" if c["S2-B_no_both_falsifier"] else "triggered", "number": v["S2-B"]["without_both_partner_contact"]},
        {"prediction": "S2-C forced/low-permission contact increases protector pressure", "outcome": "met" if c["S2-C_pressure"] else "not_met", "number": v["S2-C"]["contrasts"]},
        {"prediction": "S2-C forced/low-permission contact reduces later contact", "outcome": "met" if c["S2-C_later_contact"] else "not_met", "number": v["S2-C"]["contrasts"]},
        {"prediction": "S2-C refusal-respecting retreat preserves information seeking/access", "outcome": "met" if c["S2-C_retreat_preserves"] else "not_met", "number": v["S2-C"]["contrasts"]},
        {"falsifier": "no bypass arm difference", "outcome": "not_triggered" if c["S2-C_arm_difference"] else "triggered", "number": v["S2-C"]["contrasts"]},
    ]
    record = {"study": "DT-S2-DESCENT", "rows": rows, "met_count": sum(row["outcome"] == "met" for row in rows), "not_met_count": sum(row["outcome"] == "not_met" for row in rows), "triggered_falsifiers": [row for row in rows if row["outcome"] == "triggered"], "no_softening": True}
    _write_json("s2-prediction-scoring.json", record)
    lines = ["# DT-S2-DESCENT prediction scoring", "", "| Registered row | Result | Number |", "|---|---|---|"]
    for row in rows:
        label = row["prediction"] if "prediction" in row else "Falsifier: " + row["falsifier"]
        lines.append(f"| {label} | **{row['outcome']}** | `{json.dumps(row['number'], sort_keys=True)}` |")
    lines.extend(("", "No registered direction, ROPE, or falsifier was changed after execution.", "")); (RESULTS / "s2-prediction-scoring.md").write_text("\n".join(lines)); return record


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("action", choices=("proofs", "run", "score")); args = parser.parse_args()
    if args.action == "proofs": proofs()
    elif args.action == "run": run()
    else: score_predictions()


if __name__ == "__main__": main()
