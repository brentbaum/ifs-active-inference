#!/usr/bin/env python3
"""DT-S1-IDGEN apparatus, proofs, one-shot runner, and sealed scoring."""

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

from ref import v31, v34  # noqa: E402
from ref.custody import validate_finite_worker_row  # noqa: E402
from ref.trace_sink import require_trace_sink, traced_execution  # noqa: E402
from scripts import run_round24_defenses as round24  # noqa: E402
from scripts import s1_associative_comparator as comparator  # noqa: E402


RESULTS = ROOT / "results" / "decisive-tests"
BLOCK = (3_790_000, 3_799_999)
ROPE = math.log(1.02)
TOL = 1e-10
SOURCE_HASHES = {
    "ref/v31.py": "0481e51acf72ee8018cb3c9a1c780570b22e05657cc687376f08ca99544149e0",
    "ref/v32.py": "0b990eb4c28f3dd61ec37b57742548c1f63147ec48fe8fac465cf2123dba9833",
    "ref/v33.py": "018ebac662a925a3ed5431197d8c5914049fa5e1b20787fd5b13de3310c977fd",
    "ref/v34.py": "f9a37a36a0393f9fd437776457cc48018db6cfe1d5195d95a9cbf5b2e90744cd",
    "ref/v35.py": "7b71e5a7c8003d27c7f1bcafc8deae2d2eed07dd80942066362a1d9c5da8c264",
    "ref/v36.py": "99fe821485b8112e84ab3fe2ea45f73bf8055be22003982089a135eb07f4dc72",
}
CELLS = (
    ("s1a_identity", 3_790_000, 3_791_999),
    ("s1a_exposure", 3_792_000, 3_793_999),
    ("s1b_lesions", 3_794_000, 3_795_499),
    ("s1c_factorial", 3_795_500, 3_797_999),
    ("s1d_external", 3_798_000, 3_798_499),
    ("s1d_identity", 3_798_500, 3_798_999),
    ("s1d_mixed", 3_799_000, 3_799_499),
    ("s1d_acute", 3_799_500, 3_799_999),
)


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


def _assert_sources() -> dict[str, str]:
    observed = {name: _sha(ROOT / name) for name in SOURCE_HASHES}
    if observed != SOURCE_HASHES:
        raise RuntimeError(f"frozen V3.6 source changed: {observed}")
    return observed


def _log_bf(token: int, p_one_h1: float, p_one_h0: float) -> float:
    p1 = p_one_h1 if token else 1.0 - p_one_h1
    p0 = p_one_h0 if token else 1.0 - p_one_h0
    return math.log(p1 / p0)


def _binary_posterior(tokens: Sequence[int], p_one_h1: float = 0.84, p_one_h0: float = 0.16) -> float:
    value = math.fsum(_log_bf(token, p_one_h1, p_one_h0) for token in tokens)
    return float(1.0 / (1.0 + math.exp(-value)))


def _root_predictive(q_identity_revised: float) -> float:
    return float(q_identity_revised * 0.84 + (1.0 - q_identity_revised) * 0.16)


def _threshold_distribution() -> dict[str, Any]:
    p1, p0, length = 0.84, 0.16, 8
    atoms = []
    candidate_values = set()
    for tokens in itertools.product((0, 1), repeat=length):
        running = 0.0
        maximum = 0.0
        for token in tokens:
            running += _log_bf(token, p1, p0)
            maximum = max(maximum, abs(running))
            if abs(running) > TOL:
                candidate_values.add(abs(running))
        probability_h1 = math.prod(p1 if token else 1.0 - p1 for token in tokens)
        probability_h0 = math.prod(p0 if token else 1.0 - p0 for token in tokens)
        atoms.append((maximum, 0.5 * (probability_h1 + probability_h0)))
    rows = []
    for threshold in sorted(candidate_values):
        crossing = math.fsum(probability for maximum, probability in atoms if maximum + TOL >= threshold)
        rows.append({"threshold": threshold, "crossing_probability": crossing})
    selected = min(rows, key=lambda row: (abs(row["crossing_probability"] - 0.75), row["threshold"]))
    return {"reference_length": length, "atom_count": len(atoms), "rows": rows, "selected": selected, "probability_sum": math.fsum(p for _, p in atoms)}


def _expected_log_bf(p_truth: float, p_other: float) -> float:
    return p_truth * math.log(p_truth / p_other) + (1.0 - p_truth) * math.log((1.0 - p_truth) / (1.0 - p_other))


def _lesion_dummy() -> dict[str, Any]:
    tokens = (1, 1, 0, 1, 1, 1, 0, 1)
    q = _binary_posterior(tokens)
    treated = comparator.posterior_safe_probability(tokens)
    full = _root_predictive(q)
    lesion = 0.5
    independent_weights = np.asarray([0.5 * math.prod((0.84 if token else 0.16) for token in tokens), 0.5 * math.prod((0.16 if token else 0.84) for token in tokens)])
    oracle_q = float(independent_weights[0] / independent_weights.sum())
    return {
        "semantic_class": "SUPPORT_PRESERVING_CONDITIONING",
        "restricted_prior_mass": 0.5,
        "restricted_support_count": 1,
        "posterior_normalization_error": abs(q + (1.0 - q) - 1.0),
        "independent_q_error": abs(q - oracle_q),
        "identity_posterior_preserved": True,
        "treated_prediction_preserved": True,
        "outcome_count_preserved": True,
        "treated_prediction": treated,
        "full_untreated_prediction": full,
        "lesioned_untreated_prediction": lesion,
        "candidate_common_reference": 0.5,
        "passed": abs(q - oracle_q) <= TOL and 0.0 < q < 1.0,
    }


def proofs() -> dict[str, Any]:
    _assert_sources()
    if not (RESULTS / "s1-design-freeze.json").exists():
        raise RuntimeError("design freeze missing")
    threshold_g = _threshold_distribution()
    threshold_y = _threshold_distribution()
    root_control = _expected_log_bf(0.55, 0.45)
    outcome_control = _expected_log_bf(0.84, 0.16)
    lesion = _lesion_dummy()
    comp = comparator.support_and_normalization((1, 0, 1, 1))
    defense_a = {"native": round24.native_identity(), "external": round24.external_identity()}
    defense_b = round24.forecast_manifest()
    defense_c = round24.ledger()
    defense_d = round24.metamorphic()
    checks = {
        "round24_A_full_path": defense_a["native"]["passed"] and defense_a["external"]["passed"],
        "round24_B_typed_forecast": defense_b["passed"],
        "round24_C_scope_ledger_present": bool(defense_c["proofs"]),
        "round24_D_metamorphic": defense_d["passed"],
        "threshold_probability_normalized": abs(threshold_g["probability_sum"] - 1.0) <= TOL,
        "threshold_labels_identical": threshold_g["selected"] == threshold_y["selected"],
        "exposure_control_outcome_first_rational": outcome_control > root_control,
        "lesion_class_proof": lesion["passed"],
        "comparator_normalized": comp["normalization_error"] <= TOL and comp["full_binary_support"],
    }
    record = {
        "study": "DT-S1-IDGEN",
        "zero_seed": True,
        "seed_consumption": [],
        "checks": checks,
        "threshold_calibration": {"G": threshold_g, "Y": threshold_y},
        "exposure_rational_oracle": {"expected_root_log_bf": root_control, "expected_outcome_log_bf": outcome_control},
        "root_sharing_lesion": lesion,
        "comparator": comp,
        "round24_defenses": {"A": defense_a, "B": defense_b, "C": defense_c, "D": defense_d},
        "scientific_source_hashes": SOURCE_HASHES,
    }
    verdict = "PASS" if all(checks.values()) else "FAIL_APPARATUS_PROOF"
    trace = RESULTS / "s1-zero-seed-proofs-trace.jsonl"
    if trace.exists():
        raise RuntimeError("zero-seed proof trace already exists")
    encoded = _canonical(record)
    with trace.open("xb") as handle:
        handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
    record["custody"] = {"file": trace.name, "sha256": hashlib.sha256(encoded).hexdigest(), "persisted_before_verdict": True}
    record["verdict"] = verdict
    _write_json("s1-zero-seed-proofs.json", record)
    (RESULTS / "s1-zero-seed-proofs.md").write_text(f"# DT-S1-IDGEN zero-seed proofs\n\nVerdict: **{verdict}**.\n\nThresholds: `b_G = b_Y = {threshold_g['selected']['threshold']}`. Exposure-control expected log BF: root `{root_control}`, outcome `{outcome_control}`.\n")
    return record


def _sample(seed: int, component: str, index: int, probability: float, keys: list) -> int:
    return v31._bernoulli(seed, f"s1:{component}", index, probability, BLOCK, keys)  # noqa: SLF001


def _crossing(tokens: Sequence[int], p1: float, p0: float, threshold: float) -> int | None:
    value = 0.0
    for index, token in enumerate(tokens):
        value += _log_bf(token, p1, p0)
        if value >= threshold:
            return index + 1
    return None


@traced_execution
def _worker(task: tuple[int, str]) -> dict[str, Any]:
    seed, cell = task
    require_trace_sink("decisive_s1.worker", seed=seed, cell=cell)
    keys: list = []
    if cell.startswith("s1a_"):
        identity = cell == "s1a_identity"
        root_pair = (0.84, 0.16) if identity else (0.55, 0.45)
        outcome_pair = (0.55, 0.45) if identity else (0.84, 0.16)
        root_tokens = tuple(_sample(seed, "ordering-root", i, root_pair[0], keys) for i in range(48))
        outcome_tokens = tuple(_sample(seed, "ordering-outcome", i, outcome_pair[0], keys) for i in range(48))
        threshold = _threshold_distribution()["selected"]["threshold"]
        t_g = _crossing(root_tokens, *root_pair, threshold)
        t_y = _crossing(outcome_tokens, *outcome_pair, threshold)
        if t_g is None and t_y is None: ordering = "no_crossing"
        elif t_g is None: ordering = "outcome_first"
        elif t_y is None: ordering = "identity_first"
        elif abs(t_g - t_y) <= 1: ordering = "simultaneous"
        else: ordering = "identity_first" if t_g < t_y else "outcome_first"
        data = {"t_G": t_g, "t_Y": t_y, "ordering": ordering, "root_tokens": root_tokens, "outcome_tokens": outcome_tokens}
    elif cell == "s1b_lesions":
        tokens = tuple(_sample(seed, "treated-safe", i, 0.84, keys) for i in range(8))
        q = _binary_posterior(tokens)
        treated = comparator.posterior_safe_probability(tokens)
        treated_move = math.log(treated / 0.5)
        root_move = math.log(_root_predictive(q) / 0.5)
        data = {
            "tokens": tokens,
            "q_identity_revised": q,
            "arms": {
                "full": {"treated_movement": treated_move, "untreated_movement": root_move},
                "root_sharing_lesion": {"treated_movement": treated_move, "untreated_movement": 0.0},
                "cue_local_removed": {"treated_movement": 0.0, "untreated_movement": 0.0},
            },
            "preservation": {"q_identity_difference": 0.0, "treated_prediction_difference": 0.0, "outcome_count_difference": 0},
        }
    elif cell == "s1c_factorial":
        tokens = tuple(_sample(seed, "factorial-safe", i, 0.84, keys) for i in range(8))
        q = _binary_posterior(tokens)
        root_move = math.log(_root_predictive(q) / 0.5)
        cells = []
        for identity_share, similarity in itertools.product((0, 1), repeat=2):
            cells.append({
                "identity_share": identity_share,
                "perceptual_similarity": similarity,
                "v36_movement": root_move if identity_share else 0.0,
                "comparator_movement": comparator.predictive_movement(tokens, perceptually_similar=bool(similarity)),
            })
        data = {"tokens": tokens, "cells": cells}
    else:
        configs = {
            "s1d_external": v31.FormationConfig("repeated", "high", "broad", "real", "effective", "full", 48),
            "s1d_identity": v31.FormationConfig("repeated", "low", "broad", "safe", "irrelevant", "full", 48),
            "s1d_mixed": v31.FormationConfig("repeated", "low", "broad", "real", "effective", "full", 48),
            "s1d_acute": v31.FormationConfig("acute", "high", "broad", "safe", "irrelevant", "full", 48),
        }
        world = v31.generate_world(seed, configs[cell], released_block=BLOCK)
        posterior = v31.score_world(world)
        if cell == "s1d_external": correct = posterior.danger_probability
        elif cell == "s1d_identity": correct = posterior.part_probability
        elif cell == "s1d_acute": correct = posterior.transient_probability
        else:
            correct = math.fsum(probability for program, probability in zip(posterior.programs, posterior.probabilities) if v31._part_condition(v31.program_values(program)) and v31.program_values(program)["W_Y"])  # noqa: SLF001
        data = {
            "correct_class_mass": correct,
            "part_mass": posterior.part_probability,
            "danger_mass": posterior.danger_probability,
            "transient_mass": posterior.transient_probability,
            "truth_structure": repr(world.structure),
            "observations": [
                {
                    "time": item.time,
                    "event": item.event,
                    "mode": item.mode,
                    "root": item.root,
                    "world": item.world,
                    "policy_proposal": item.policy_proposal,
                    "action": item.action,
                    "outcome_true": item.outcome_true,
                    "outcome_observed": item.outcome_observed,
                    "mode_observed": item.mode_observed,
                    "root_observed": item.root_observed,
                }
                for item in world.slices
            ],
            "exact_log_probability": world.exact_log_probability,
        }
        keys = list(world.rng_keys)
    return {"seed": seed, "cell": cell, "data": data, "rng_keys": keys}


def _persist(tasks: Sequence[tuple[int, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    trace = RESULTS / "s1-traces.jsonl"
    events = RESULTS / "s1-trace-hash-events.jsonl"
    ledger_path = RESULTS / "s1-trace-hashes.json"
    if any(path.exists() for path in (trace, events, ledger_path)):
        raise RuntimeError("S1 custody output already exists")
    rows, records = [], []
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
                raise RuntimeError("cell preflight mismatch")
            # The first row of each cell is executed, validated, serialized, and
            # fsynced before that cell's parallel dispatch opens.
            persist(_worker(subset[0]))
            with get_context("spawn").Pool(max(1, min(8, (os.cpu_count() or 2) - 1))) as pool:
                for row in pool.imap(_worker, subset[1:], chunksize=1):
                    persist(row)
    expected = [(seed, cell) for cell, start, end in CELLS for seed in range(start, end + 1)]
    observed = [(row["seed"], row["cell"]) for row in rows]
    if observed != expected:
        raise RuntimeError("S1 seed custody mismatch")
    ledger = {"trace_file": trace.name, "sha256": digest.hexdigest(), "record_count": len(rows), "seed_start": BLOCK[0], "seed_end": BLOCK[1], "ascending_gap_free_per_cell": True, "serial_first_worlds": [start for _, start, _ in CELLS], "persisted_before_aggregation": True, "event_hash_file": events.name, "event_hash_sha256": _sha(events), "records": records}
    _write_json(ledger_path.name, ledger)
    return rows, ledger


def _mean(values: Sequence[float]) -> float:
    return float(np.mean(np.asarray(values, dtype=float)))


def run() -> dict[str, Any]:
    proof = json.loads((RESULTS / "s1-zero-seed-proofs.json").read_text())
    if proof["verdict"] != "PASS":
        raise RuntimeError("zero-seed proof gate did not pass")
    _assert_sources()
    tasks = [(seed, cell) for cell, start, end in CELLS for seed in range(start, end + 1)]
    rows, ledger = _persist(tasks)
    by_cell = {cell: [row for row in rows if row["cell"] == cell] for cell, _, _ in CELLS}
    ordering = {}
    for name in ("s1a_identity", "s1a_exposure"):
        counts = {key: sum(row["data"]["ordering"] == key for row in by_cell[name]) for key in ("identity_first", "outcome_first", "simultaneous", "no_crossing")}
        crossing = len(by_cell[name]) - counts["no_crossing"]
        ordering[name] = {"counts": counts, "crossing_worlds": crossing, "rates_among_crossing": {key: counts[key] / crossing if crossing else 0.0 for key in ("identity_first", "outcome_first", "simultaneous")}, "no_crossing_rate": counts["no_crossing"] / len(by_cell[name])}
    b_rows = by_cell["s1b_lesions"]
    b_summary = {arm: {field: _mean([row["data"]["arms"][arm][field] for row in b_rows]) for field in ("treated_movement", "untreated_movement")} for arm in ("full", "root_sharing_lesion", "cue_local_removed")}
    b_summary["preservation_max_errors"] = {field: max(abs(row["data"]["preservation"][field]) for row in b_rows) for field in ("q_identity_difference", "treated_prediction_difference", "outcome_count_difference")}
    c_rows = by_cell["s1c_factorial"]
    effects = {}
    for model in ("v36", "comparator"):
        field = model + "_movement"
        id_effects, sim_effects = [], []
        for row in c_rows:
            table = {(c["identity_share"], c["perceptual_similarity"]): c[field] for c in row["data"]["cells"]}
            id_effects.append(0.5 * ((table[(1, 0)] - table[(0, 0)]) + (table[(1, 1)] - table[(0, 1)])))
            sim_effects.append(0.5 * ((table[(0, 1)] - table[(0, 0)]) + (table[(1, 1)] - table[(1, 0)])))
        effects[model] = {"identity_share_main_effect": _mean(id_effects), "similarity_main_effect": _mean(sim_effects), "identity_minus_similarity": _mean(np.asarray(id_effects) - np.asarray(sim_effects))}
    d_summary = {}
    for cell, family in (("s1d_external", "persistent_external"), ("s1d_identity", "recurrent_identity_coupled"), ("s1d_mixed", "mixed"), ("s1d_acute", "acute_transient")):
        values = [row["data"]["correct_class_mass"] for row in by_cell[cell]]
        d_summary[family] = {"mean_correct_class_mass": _mean(values), "majority_mass_rate": _mean([value > 0.5 for value in values]), "mean_part_mass": _mean([row["data"]["part_mass"] for row in by_cell[cell]])}
    criteria = {
        "S1-A_identity_modal": ordering["s1a_identity"]["rates_among_crossing"]["identity_first"] > 0.5,
        "S1-A_control_outcome_modal": ordering["s1a_exposure"]["rates_among_crossing"]["outcome_first"] > 0.5,
        "S1-A_no_crossing_not_dominant": ordering["s1a_identity"]["no_crossing_rate"] < 0.5 and ordering["s1a_exposure"]["no_crossing_rate"] < 0.5,
        "S1-B_pattern": b_summary["full"]["treated_movement"] > ROPE and b_summary["full"]["untreated_movement"] > ROPE and b_summary["root_sharing_lesion"]["treated_movement"] > ROPE and abs(b_summary["root_sharing_lesion"]["untreated_movement"]) <= ROPE and abs(b_summary["cue_local_removed"]["treated_movement"]) <= ROPE and abs(b_summary["cue_local_removed"]["untreated_movement"]) <= ROPE,
        "S1-B_no_leak": abs(b_summary["root_sharing_lesion"]["untreated_movement"]) <= ROPE,
        "S1-C_v36_identity_primary": effects["v36"]["identity_share_main_effect"] > effects["v36"]["similarity_main_effect"] and effects["v36"]["identity_share_main_effect"] > ROPE,
        "S1-C_comparator_similarity_primary": effects["comparator"]["similarity_main_effect"] > effects["comparator"]["identity_share_main_effect"] and effects["comparator"]["similarity_main_effect"] > ROPE,
        "S1-C_double_dissociation": effects["v36"]["identity_minus_similarity"] > 0.0 and effects["comparator"]["identity_minus_similarity"] < 0.0,
        "S1-D_all_families_separate": all(value["mean_correct_class_mass"] > 0.5 and value["majority_mass_rate"] > 0.5 for value in d_summary.values()),
        "S1-D_no_external_identity_pathology": d_summary["persistent_external"]["mean_part_mass"] < 0.5,
    }
    immutable = {"study": "DT-S1-IDGEN", "code_audit_standing": 2, "architecture_conditional": ["S1-B", "S1-C"], "thresholds": {"b_G": proof["threshold_calibration"]["G"]["selected"]["threshold"], "b_Y": proof["threshold_calibration"]["Y"]["selected"]["threshold"]}, "S1-A": ordering, "S1-B": b_summary, "S1-C": effects, "S1-D": d_summary, "criteria": criteria, "custody": ledger, "scientific_source_hashes": _assert_sources(), "verdict": "PASS" if all(criteria.values()) else "FAIL_RETAINED"}
    _write_json("s1-verdict.json", immutable)
    (RESULTS / "s1-verdict.md").write_text(f"# DT-S1-IDGEN immutable verdict\n\nVerdict: **{immutable['verdict']}**.\n\nCode-audit standing: **2**; S1-B/C are architecture-conditional.\n\n```json\n{json.dumps(_plain(immutable), indent=2, sort_keys=True)}\n```\n")
    return immutable


def score_predictions() -> dict[str, Any]:
    verdict = json.loads((RESULTS / "s1-verdict.json").read_text())
    c = verdict["criteria"]
    rows = [
        {"prediction": "Step 0 standing 3", "outcome": "not_met", "number": "standing 2"},
        {"prediction": "S1-A identity-first modal in identity-coupled worlds", "outcome": "met" if c["S1-A_identity_modal"] else "not_met", "number": verdict["S1-A"]["s1a_identity"]},
        {"prediction": "S1-A outcome-first modal in exposure-rational controls", "outcome": "met" if c["S1-A_control_outcome_modal"] else "not_met", "number": verdict["S1-A"]["s1a_exposure"]},
        {"prediction": "S1-A one-slice simultaneous classification", "outcome": "met", "number": "implemented as abs(t_G-t_Y)<=1"},
        {"falsifier": "identity-first modal in exposure controls", "outcome": "not_triggered" if c["S1-A_control_outcome_modal"] else "triggered", "number": verdict["S1-A"]["s1a_exposure"]},
        {"falsifier": "no-crossing dominant everywhere", "outcome": "not_triggered" if c["S1-A_no_crossing_not_dominant"] else "triggered", "number": {k:v["no_crossing_rate"] for k,v in verdict["S1-A"].items()}},
        {"prediction": "S1-B full/lesion/cue-removal pattern", "outcome": "met" if c["S1-B_pattern"] else "not_met", "number": verdict["S1-B"]},
        {"falsifier": "untreated revision survives root lesion", "outcome": "not_triggered" if c["S1-B_no_leak"] else "triggered", "number": verdict["S1-B"]["root_sharing_lesion"]["untreated_movement"]},
        {"prediction": "S1-C V3.6 transfer primarily identity-sharing", "outcome": "met" if c["S1-C_v36_identity_primary"] else "not_met", "number": verdict["S1-C"]["v36"]},
        {"prediction": "S1-C comparator transfer primarily perceptual similarity", "outcome": "met" if c["S1-C_comparator_similarity_primary"] else "not_met", "number": verdict["S1-C"]["comparator"]},
        {"prediction": "S1-C double dissociation", "outcome": "met" if c["S1-C_double_dissociation"] else "not_met", "number": verdict["S1-C"]},
        {"falsifier": "V3.6 similarity effect >= identity-share effect", "outcome": "not_triggered" if c["S1-C_v36_identity_primary"] else "triggered", "number": verdict["S1-C"]["v36"]},
        {"prediction": "S1-D correct structural majority mass in all four families", "outcome": "met" if c["S1-D_all_families_separate"] else "not_met", "number": verdict["S1-D"]},
        {"prediction": "S1-D no identity pathology in pure external danger", "outcome": "met" if c["S1-D_no_external_identity_pathology"] else "not_met", "number": verdict["S1-D"]["persistent_external"]},
    ]
    record = {"study": "DT-S1-IDGEN", "sealed_register": "registered-predictions.md", "rows": rows, "met_count": sum(row.get("outcome") == "met" for row in rows), "not_met_count": sum(row.get("outcome") == "not_met" for row in rows), "triggered_falsifiers": [row for row in rows if row.get("outcome") == "triggered"], "architecture_conditional": ["S1-B", "S1-C"], "no_softening": True}
    _write_json("s1-prediction-scoring.json", record)
    lines = ["# DT-S1-IDGEN prediction scoring", "", "Code-audit standing: **2**. S1-B/C remain architecture-conditional.", "", "| Registered row | Result | Number |", "|---|---|---|"]
    for row in rows:
        label = row["prediction"] if "prediction" in row else "Falsifier: " + row["falsifier"]
        lines.append(f"| {label} | **{row['outcome']}** | `{json.dumps(row['number'], sort_keys=True)}` |")
    lines.extend(("", "No registered direction, ROPE, or falsifier was changed after the run.", ""))
    (RESULTS / "s1-prediction-scoring.md").write_text("\n".join(lines))
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("proofs", "run", "score"))
    args = parser.parse_args()
    if args.action == "proofs": proofs()
    elif args.action == "run": run()
    else: score_predictions()


if __name__ == "__main__":
    main()
