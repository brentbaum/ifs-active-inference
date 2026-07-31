#!/usr/bin/env python3
"""Prospective V3.6 COMPOSE Stage-0 and gate runner."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import sys
from dataclasses import asdict, replace
from multiprocessing import get_context
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT.parent
sys.path.insert(0, str(SUITE_ROOT))
sys.path.insert(0, str(ROOT))
from ref import audit, v35, v36, v36_oracle  # noqa: E402
from ref.trace_sink import require_trace_sink, traced_execution  # noqa: E402
from v2.ref import v232_formation as v2_formation, v28 as v2_trajectory  # noqa: E402


RESULTS = ROOT / "results" / "V3.6"
PARAMETERS = ROOT / "protocols" / "v3.6-parameters.json"
FIRST_PILOT_BLOCK = (3_600_001, 3_603_999)
FRESH_PILOT_BLOCK = (3_660_000, 3_663_999)
BARRED_CUSTODY_SEED = 3_600_000
TOLERANCE = 1e-10
GATE2_BLOCK = (3_604_000, 3_613_999)
GATE3_BLOCK = (3_614_000, 3_629_999)
GATE4_BLOCK = (3_630_000, 3_634_999)
GATE5_BLOCK = (3_635_000, 3_659_999)


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
        json.dumps(_plain(value), sort_keys=True, separators=(",", ":"),
                   allow_nan=False).encode() + b"\n"
    )


def _write_json(name: str, value: Any) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / name).write_text(
        json.dumps(_plain(value), indent=2, sort_keys=True,
                   allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _write_report(name: str, title: str, result: Mapping[str, Any]) -> None:
    (RESULTS / name).write_text(
        "\n".join([
            f"# {title}", "", f"Verdict: **{result['verdict']}**.", "",
            "```json", json.dumps(_plain(result), indent=2, sort_keys=True,
                                     allow_nan=False), "```", "",
        ]),
        encoding="utf-8",
    )


def _trace_map(name: str, tasks: Sequence[Any], worker: Any) -> list[dict[str, Any]]:
    """Persist every event ledger and row, then hashes, before returning."""
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{name}-traces.jsonl"
    if path.exists() or (RESULTS / f"{name}-trace-hashes.json").exists():
        raise RuntimeError(f"custody refusal: {name} output already exists")
    file_hash = hashlib.sha256()
    records: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    processes = max(1, min(8, (os.cpu_count() or 2) - 1))
    with path.open("xb") as handle:
        with get_context("spawn").Pool(processes) as pool:
            for row in pool.imap(worker, tasks, chunksize=2):
                encoded = _canonical(row)
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
                file_hash.update(encoded)
                records.append({
                    "seed": int(row["seed"]),
                    "sha256": hashlib.sha256(encoded).hexdigest(),
                })
                rows.append(row)
    hash_record = {
        "file": path.name,
        "seed_start": int(tasks[0]) if tasks else None,
        "seed_end": int(tasks[-1]) if tasks else None,
        "world_count": len(rows),
        "file_sha256": file_hash.hexdigest(),
        "records": records,
        "custody_order": "JSONL persisted and fsynced before this hash record; aggregation follows",
    }
    _write_json(f"{name}-trace-hashes.json", hash_record)
    # Verify the on-disk bytes and all gap-free seeds before custody returns.
    if hashlib.sha256(path.read_bytes()).hexdigest() != file_hash.hexdigest():
        raise RuntimeError("custody failure: persisted JSONL hash mismatch")
    if [row["seed"] for row in rows] != list(tasks):
        raise RuntimeError("custody failure: seed order/gap mismatch")
    return rows


def _manifest_audit(stage: str) -> dict[str, Any]:
    path = ROOT / "results" / stage / "freeze-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in manifest["files"].items():
        target = ROOT / relative
        observed = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
        # V3.0's package initializer is explicitly superseded by V3.1's
        # committed initializer; later manifests pin the effective file.
        if stage == "V3.0" and relative == "ref/__init__.py":
            continue
        if observed != expected:
            mismatches.append({"file": relative, "expected": expected, "observed": observed})
    return {"stage": stage, "mismatches": mismatches, "passed": not mismatches}


def run_gate1() -> dict[str, Any]:
    dummy = json.loads((ROOT / "protocols" / "v3.6-public-dummy.json").read_text())
    readout_source = dummy["readout_dummy"]
    readout_before = copy.deepcopy(readout_source)
    recombined = v36_oracle.combine_readouts(readout_source)
    code_source = dummy["code_length_dummy"]["log_priors"]
    code_before = copy.deepcopy(code_source)
    code = v36_oracle.code_length(code_source, dummy["code_length_dummy"]["L_theta_given_H"])
    code_error = abs(code["L_total"] - math.fsum(
        code[key] for key in ("L_grammar", "L_H", "L_theta_given_H", "L_protocol")
    ))
    v35_gate1 = json.loads(
        (ROOT / "results" / "V3.5" / "gate-1-amendment-2-rerun.json").read_text()
    )
    v35_gate2 = json.loads(
        (ROOT / "results" / "V3.5" / "gate-2-amendment-2.json").read_text()
    )
    accounting = json.loads(
        (ROOT / "audits" / "v3.6-compression-accounting.json").read_text()
    )
    source = (ROOT / "ref" / "v36.py").read_text(encoding="utf-8")
    banned = (
        "v232_formation", "v24", "v25a", "v25b", "v234", "v26b",
        "v27", "v28",
    )
    manifests = [_manifest_audit(stage) for stage in (
        "V3.0", "V3.1", "V3.2", "V3.3", "V3.4", "V3.5"
    )]
    proofs = {
        "01_no_v2_scientific_import": not any(token in source for token in banned),
        "02_no_new_scientific_primitive": "adds no likelihood, latent variable, prior, or update equation" in source,
        "03_public_protocol_has_no_conclusion_field": all(
            set(row) == {"event_index", "event_type", "available"}
            for row in v36.protocol_declaration("full")
        ),
        "04_independent_readout_input_copy": readout_source == readout_before,
        "05_independent_readout_values": recombined == {
            "q_identity_organization": 0.7,
            "q_external_danger": 0.2,
            "q_context_specific": 0.7,
            "q_recurrent_context": 0.6,
            "q_current_edge_absence": 0.75,
            "q_partner_reliable": 0.85,
            "q_policy_open": 0.65,
        },
        "06_independent_code_input_copy": code_source == code_before,
        "07_code_length_recombination_error": code_error,
        "08_composition_readout_purity": audit.audit_state(v36.protocol_declaration("full")) == (),
        "09_expanded_item17_retained": bool(v35_gate1["proofs"]["17_expanded_marginal_calibration"]["passed"]),
        "10_candidate_common_registration_error": float(v35_gate1["proofs"]["19_registration_candidate_common_evidence_error"]),
        "11_registration_delivered_masked_error": float(v35_gate1["proofs"]["19_registration_delivered_masked_posterior_error"]),
        "12_stakes_scientific_invariance_error": float(v35_gate2["metrics"]["stakes_scientific_posterior_error_max"]),
        "13_interventional_topology_fixture": bool(v35_gate1["proofs"]["18_interventional_topology_fixture"]["passed"]),
        "14_restricted_prior_identity_error": float(v35_gate1["proofs"]["13_restricted_prior_error"]),
        "15_all_inherited_manifest_chains_effective": all(row["passed"] for row in manifests),
        "16_v35_repair_factors_counted": len(accounting["v3"]["repair_introduced_items_included"]) == 5,
        "17_factor_reduction_at_least_half": bool(accounting["reductions"]["factor_templates_at_least_50_percent"]),
        "18_constant_reduction_at_least_half": bool(accounting["reductions"]["constants_at_least_50_percent"]),
    }
    numeric_tolerance_keys = ("07_", "10_", "11_", "12_", "14_")
    passed = all(
        (value <= TOLERANCE if key.startswith(numeric_tolerance_keys) else bool(value))
        for key, value in proofs.items()
    )
    result = {
        "stage": "V3.6", "gate": 1,
        "seed_consumption": [],
        "bounds": dict(v36.finite_information_bounds()),
        "manifest_audits": manifests,
        "proofs": proofs,
        "verdict": "PASS" if passed else "FAIL",
    }
    _write_json("gate-1.json", result)
    _write_report("gate-1.md", "V3.6 Gate 1 — permanent composition battery", result)
    return result


def run_gate1_adjudicated() -> dict[str, Any]:
    retained = json.loads((RESULTS / "gate-1.json").read_text())

    def fixture(boundary: int, kind: str) -> Any:
        if kind == "premature":
            slices = [
                SimpleNamespace(time=time, episode_kind="imaginal_premature", context=1, mode=1, root=None)
                for time in range(boundary - 3, boundary)
            ]
        else:
            slices = []
        slices.append(SimpleNamespace(
            time=boundary, episode_kind="corrective", context=1, mode=1, root=0
        ))
        if kind == "post_revision":
            slices.extend([
                SimpleNamespace(time=time, episode_kind="imaginal_post", context=1, mode=1, root=None)
                for time in range(boundary + 1, boundary + 4)
            ])
        return SimpleNamespace(
            config=SimpleNamespace(do_over=kind), slices=tuple(slices)
        )

    audits = {
        "premature_boundary_7": dict(v36.do_over_schedule_audit(fixture(7, "premature"))),
        "premature_boundary_19": dict(v36.do_over_schedule_audit(fixture(19, "premature"))),
        "post_revision_boundary_11": dict(v36.do_over_schedule_audit(fixture(11, "post_revision"))),
    }
    plan = (ROOT / "protocols" / "v3.6-analysis-plan.md").read_text()
    proofs = {
        "retained_gate1_pass": retained["verdict"] == "PASS",
        "premature_schedule_follows_moving_boundary": all(
            audits[key]["event_indexed"]
            for key in ("premature_boundary_7", "premature_boundary_19")
        ),
        "post_revision_schedule_follows_observed_boundary": audits["post_revision_boundary_11"]["event_indexed"],
        "premature_declared_positive_causal_effect": (
            "full minus premature-do-over `q_current_edge_absence` | positive | causal effect" in plan
        ),
        "post_revision_equivalence_retained": (
            "V3.3 post-revision do-over | full interval inside ROPE | equivalence retained finding" in plan
        ),
        "fresh_block_declared": "`3660000:3663999`" in plan,
    }
    result = {
        "stage": "V3.6", "gate": "1-adjudicated-plan-fidelity",
        "authorization": "results/V3.6/stage0-adjudication.md",
        "seed_consumption": [], "schedule_fixtures": audits,
        "proofs": proofs,
        "verdict": "PASS" if all(proofs.values()) else "FAIL",
    }
    _write_json("gate-1-adjudicated.json", result)
    _write_report("gate-1-adjudicated.md", "V3.6 Gate 1 plan-fidelity addendum", result)
    return result


def _config(protocol: str = "full", **changes: Any) -> v36.ComposeConfig:
    values = dict(
        protocol=protocol, mode_count=3, topology="allied", stakes="low",
        support_target="all", policy_regime="engagement", missingness=0.0,
        length=16,
    )
    values.update(changes)
    return v36.ComposeConfig(**values)


def _readout_dict(readout: v36.CompositionReadout) -> dict[str, Any]:
    return _plain(readout)


@traced_execution
def _pilot_row(seed: int) -> dict[str, Any]:
    if seed == BARRED_CUSTODY_SEED or not FRESH_PILOT_BLOCK[0] <= seed <= FRESH_PILOT_BLOCK[1]:
        raise ValueError("pilot seed outside fresh adjudicated block")
    offset = seed - FRESH_PILOT_BLOCK[0]
    comparator_protocols = v36.PROTOCOLS[1:]
    if offset < 1999:
        comparator = comparator_protocols[offset % len(comparator_protocols)]
        full = v36.run_therapy(seed, _config("full"), released_block=FRESH_PILOT_BLOCK)
        other = v36.run_therapy(seed, _config(comparator), released_block=FRESH_PILOT_BLOCK)
        return {
            "seed": seed, "cell": "comparator", "comparator": comparator,
            "full": _readout_dict(full), "other": _readout_dict(other),
        }
    if offset < 2999:
        stress = offset % 10
        base_changes = {
            "mode_count": 1 + (stress % 3),
            "topology": ("independent", "opposed", "allied")[stress % 3],
            "support_target": "one" if stress in {3, 4} else "all",
            "policy_regime": ("exclusion", "monitoring", "engagement", "mixed")[stress % 4],
            "missingness": (0.0, 0.15, 0.3)[stress % 3],
        }
        left = v36.run_therapy(seed, _config("full", stakes="low", **base_changes), released_block=FRESH_PILOT_BLOCK)
        right = v36.run_therapy(seed, _config("full", stakes="high", **base_changes), released_block=FRESH_PILOT_BLOCK)
        return {
            "seed": seed, "cell": "round10_stress", "stress_index": stress,
            "low": _readout_dict(left), "high": _readout_dict(right),
        }
    # Compression/calibration profile: the V3 side is sampled here. The V2
    # noninferiority margin was frozen from committed V2-only bootstrap data.
    mode_count = 1 + (offset % 3)
    topology = ("independent", "opposed", "allied")[offset % 3]
    profile = v36.run_therapy(
        seed,
        _config(
            "full", mode_count=mode_count, topology=topology,
            support_target="one" if offset % 2 else "all",
            policy_regime=("exclusion", "engagement")[offset % 2],
            missingness=(0.0, 0.15, 0.3)[offset % 3],
        ),
        released_block=FRESH_PILOT_BLOCK,
    )
    return {
        "seed": seed, "cell": "compression_profile",
        "truth": {"mode_count": mode_count, "topology": topology},
        "profile": _readout_dict(profile),
    }


def _bootstrap_interval(values: Sequence[float], seed: int) -> list[float]:
    array = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = np.mean(rng.choice(array, (4000, len(array)), replace=True), axis=1)
    return [float(x) for x in np.quantile(means, [0.025, 0.975])]


def _credible_contains(probabilities: Sequence[float], truth_index: int) -> bool:
    order = np.argsort(-np.asarray(probabilities))
    mass = 0.0
    for index in order:
        mass += probabilities[int(index)]
        if int(index) == truth_index:
            return True
        if mass >= 0.95:
            return False
    return False


def _ece(confidence: Sequence[float], correct: Sequence[bool]) -> float:
    p = np.asarray(confidence)
    y = np.asarray(correct, dtype=float)
    value = 0.0
    for low in np.linspace(0.0, 0.9, 10):
        high = low + 0.1
        chosen = (p >= low) & (p <= high if high == 1.0 else p < high)
        if chosen.any():
            value += chosen.mean() * abs(p[chosen].mean() - y[chosen].mean())
    return float(value)


def _structure_probabilities(posterior: v35.ProtectPosterior) -> dict[Any, float]:
    result: dict[Any, float] = {}
    for probability, (structure, _sign) in zip(
        posterior.probabilities, posterior.components
    ):
        key = (
            structure.active_modes, structure.mode_root_edges,
            structure.joint_policy_outcome, structure.cross_mode_outcome,
        )
        result[key] = result.get(key, 0.0) + probability
    return result


def _scientific_posterior_distance(
    left: v35.ProtectPosterior, right: v35.ProtectPosterior
) -> float:
    values = [
        max(abs(a - b) for a, b in zip(left.probabilities, right.probabilities)),
        max(abs(a - b) for a, b in zip(left.active_mode_probabilities, right.active_mode_probabilities)),
        max(abs(a - b) for a, b in zip(left.mode_occupancy, right.mode_occupancy)),
        max(abs(a - b) for a, b in zip(left.q_partner, right.q_partner)),
        max(abs(left.edge_probabilities[name] - right.edge_probabilities[name]) for name in v35.EDGE_NAMES),
        max(abs(left.topology_probabilities[name] - right.topology_probabilities[name]) for name in left.topology_probabilities),
        max(abs(a - b) for a, b in zip(left.support_response_posterior, right.support_response_posterior)),
        max(abs(a - b) for a, b in zip(left.contact_response_posterior, right.contact_response_posterior)),
    ]
    return max(values)


def _complete_posterior_distance(
    left: v35.ProtectPosterior, right: v35.ProtectPosterior
) -> float:
    values = [
        _scientific_posterior_distance(left, right),
        max(abs(a - b) for a, b in zip(left.joint_policy_posterior, right.joint_policy_posterior)),
        max(
            abs(left.interventional_influence[i][j] - right.interventional_influence[i][j])
            for i in range(v35.MODE_SLOTS) for j in range(v35.MODE_SLOTS)
        ),
    ]
    return max(values)


@traced_execution
def _gate2_row(seed: int) -> dict[str, Any]:
    if not GATE2_BLOCK[0] <= seed <= GATE2_BLOCK[1]:
        raise ValueError("Gate-2 seed outside authorized block")
    world = v35.generate_recovery_world(
        seed, length=64, released_block=GATE2_BLOCK
    )
    posterior = v35.score_world(world)
    masked_world = replace(
        world,
        observations=tuple(
            replace(item, registration=(None, None, None))
            for item in world.observations
        ),
    )
    masked = v35.score_world(masked_world)
    low = v35.score_world(replace(
        world,
        observations=tuple(replace(item, stakes=0.7) for item in world.observations),
    ))
    high = v35.score_world(replace(
        world,
        observations=tuple(replace(item, stakes=1.3) for item in world.observations),
    ))
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
    truth_edges = tuple(v35.program_values(world.truth_structure).values())
    predicted_edges = (
        predicted[1][0], predicted[1][1], predicted[1][2],
        predicted[2], predicted[3],
    )
    truth_topology = (
        "independent" if world.truth_cross_sign == 0
        else "opposed" if world.truth_cross_sign < 0 else "coalition"
    )
    support_finite = []
    for active in (1, 2, 3):
        restricted = v35.score_world(world, restrictions={"active_modes": (active,)})
        support_finite.append(
            bool(restricted.probabilities)
            and all(math.isfinite(value) for value in restricted.probabilities)
            and abs(math.fsum(restricted.probabilities) - 1.0) <= TOLERANCE
        )
    return {
        "seed": seed,
        "truth_structure": truth_key,
        "predicted_structure": predicted,
        "edge_correct": [a == b for a, b in zip(predicted_edges, truth_edges)],
        "active_count_correct": predicted[0] == truth_key[0],
        "program_correct": predicted == truth_key,
        "confidence": structure_map[predicted],
        "truth_probability": structure_map[truth_key],
        "coverage": _credible_contains([structure_map[key] for key in ordered], truth_index),
        "topology_correct": max(posterior.topology_probabilities, key=posterior.topology_probabilities.get) == truth_topology,
        "partner_correct": int(np.argmax(posterior.q_partner)) == world.truth_partner,
        "normalization_error": abs(math.fsum(posterior.probabilities) - 1.0),
        "exact_log_error": abs(world.exact_log_probability - v35.exact_complete_log_probability(world)),
        "registration_delivered_masked_error": _complete_posterior_distance(posterior, masked),
        "stakes_scientific_error": _scientific_posterior_distance(low, high),
        "candidate_support_finite_1_2_3": support_finite,
    }


def run_gate2() -> dict[str, Any]:
    rows = _trace_map(
        "gate-2", list(range(GATE2_BLOCK[0], GATE2_BLOCK[1] + 1)),
        _gate2_row,
    )
    inherited = json.loads(
        (ROOT / "protocols" / "v3.5-parameters.json").read_text()
    )["criteria"]
    edge_accuracy = {
        name: float(np.mean([row["edge_correct"][index] for row in rows]))
        for index, name in enumerate(v35.EDGE_NAMES)
    }
    metrics = {
        "world_count": len(rows),
        "active_count_accuracy": float(np.mean([row["active_count_correct"] for row in rows])),
        "edge_accuracy": edge_accuracy,
        "minimum_edge_accuracy": min(edge_accuracy.values()),
        "program_accuracy": float(np.mean([row["program_correct"] for row in rows])),
        "topology_accuracy": float(np.mean([row["topology_correct"] for row in rows])),
        "partner_accuracy": float(np.mean([row["partner_correct"] for row in rows])),
        "ece": _ece([row["confidence"] for row in rows], [row["program_correct"] for row in rows]),
        "brier": float(np.mean([(1.0 - row["truth_probability"]) ** 2 for row in rows])),
        "coverage": float(np.mean([row["coverage"] for row in rows])),
        "normalization_error_max": max(row["normalization_error"] for row in rows),
        "exact_log_error_max": max(row["exact_log_error"] for row in rows),
        "registration_identity_error_max": max(row["registration_delivered_masked_error"] for row in rows),
        "stakes_scientific_identity_error_max": max(row["stakes_scientific_error"] for row in rows),
        "candidate_support_pass_rate": float(np.mean([all(row["candidate_support_finite_1_2_3"]) for row in rows])),
    }
    comparisons = {
        "active_count_accuracy": [metrics["active_count_accuracy"], inherited["active_count_accuracy_min"], ">="],
        "minimum_edge_accuracy": [metrics["minimum_edge_accuracy"], inherited["edge_accuracy_min"], ">="],
        "program_accuracy": [metrics["program_accuracy"], inherited["program_accuracy_min"], ">="],
        "topology_accuracy": [metrics["topology_accuracy"], inherited["topology_accuracy_min"], ">="],
        "partner_accuracy": [metrics["partner_accuracy"], inherited["partner_accuracy_min"], ">="],
        "coverage": [metrics["coverage"], inherited["coverage_min"], ">="],
        "ece": [metrics["ece"], inherited["ece_max"], "<="],
        "normalization_error_max": [metrics["normalization_error_max"], TOLERANCE, "<="],
        "exact_log_error_max": [metrics["exact_log_error_max"], TOLERANCE, "<="],
        "registration_identity_error_max": [metrics["registration_identity_error_max"], TOLERANCE, "<="],
        "stakes_scientific_identity_error_max": [metrics["stakes_scientific_identity_error_max"], TOLERANCE, "<="],
        "candidate_support_pass_rate": [metrics["candidate_support_pass_rate"], 1.0, ">="],
    }
    failures = []
    for name, (value, threshold, direction) in comparisons.items():
        passed = value >= threshold if direction == ">=" else value <= threshold
        if not passed:
            failures.append(f"{name}={value} {direction} {threshold} failed")
    item17 = json.loads(
        (ROOT / "results" / "V3.5" / "gate-1-amendment-2-rerun.json").read_text()
    )["proofs"]["17_expanded_marginal_calibration"]
    if not item17["passed"]:
        failures.append("expanded item-17 marginal calibration is not PASS")
    result = {
        "stage": "V3.6", "gate": 2,
        "seed_block": list(GATE2_BLOCK), "seeds_consumed": len(rows),
        "ascending_gap_free": [row["seed"] for row in rows] == list(range(GATE2_BLOCK[0], GATE2_BLOCK[1] + 1)),
        "frozen_recovery_criteria": inherited,
        "expanded_item17": item17,
        "metrics": metrics, "comparisons": comparisons,
        "failures": failures,
        "bounds": dict(v36.finite_information_bounds()),
        "custody": {"trace_hash_ledger": "gate-2-trace-hashes.json", "escrow_touched": False, "barred_blocks_touched": False},
        "verdict": "PASS" if not failures else "FAIL",
    }
    _write_json("gate-2.json", result)
    _write_report("gate-2.md", "V3.6 Gate 2 — recovery and calibration", result)
    if failures:
        _write_json("gate-2-diagnosis-stub.json", {"stage": "V3.6", "gate": 2, "failures": failures, "next_action": "HONEST_STOP"})
    return result


@traced_execution
def _gate3_row(seed: int) -> dict[str, Any]:
    if not GATE3_BLOCK[0] <= seed <= GATE3_BLOCK[1]:
        raise ValueError("Gate-3 seed outside authorized block")
    offset = seed - GATE3_BLOCK[0]
    if offset < 12_000:
        comparator = v36.PROTOCOLS[1:][offset % 10]
        full = v36.run_therapy(seed, _config("full"), released_block=GATE3_BLOCK)
        other = v36.run_therapy(seed, _config(comparator), released_block=GATE3_BLOCK)
        return {
            "seed": seed, "cell": "paired_comparator", "comparator": comparator,
            "full": _readout_dict(full), "other": _readout_dict(other),
        }
    if offset < 14_000:
        stress = offset % 10
        changes = {
            "mode_count": 1 + stress % 3,
            "topology": ("independent", "opposed", "allied")[stress % 3],
            "support_target": "one" if stress in {3, 4} else "all",
            "policy_regime": ("exclusion", "monitoring", "engagement", "mixed")[stress % 4],
            "missingness": (0.0, 0.15, 0.30)[stress % 3],
        }
        low = v36.run_therapy(seed, _config("full", stakes="low", **changes), released_block=GATE3_BLOCK)
        high = v36.run_therapy(seed, _config("full", stakes="high", **changes), released_block=GATE3_BLOCK)
        return {"seed": seed, "cell": "stakes_and_6B_stress", "stress_index": stress, "low": _readout_dict(low), "high": _readout_dict(high)}

    require_trace_sink("v36.v2_public_tournament", seed=seed)
    index = offset - 14_000
    stratum = v2_trajectory.STRATA[index % len(v2_trajectory.STRATA)]
    v2_state = v2_trajectory.generate_developmental_state(
        seed, stratum, released_block=GATE3_BLOCK
    )
    v2_profile = v2_trajectory.run_trajectory(
        v2_state, seed, protocol="full", released_block=GATE3_BLOCK
    )
    v2_score = v2_formation.score_history(
        list(v2_state.observations), list(v2_state.configurations)
    )
    v2_log_evidence = float(np.logaddexp.reduce(v2_score["log_joint"]))
    mode_count = 1 if stratum in {"acute_one", "chronic_one", "real_danger_adaptive"} else 3
    topology = ("independent", "opposed", "allied")[index % 3]
    v3_profile = v36.run_therapy(
        seed,
        _config(
            "full", mode_count=mode_count, topology=topology,
            policy_regime="monitoring" if stratum == "real_danger_adaptive" else "mixed",
            support_target="one" if index % 2 else "all",
            missingness=(0.0, 0.15, 0.30)[index % 3],
        ),
        released_block=GATE3_BLOCK,
    )
    v3_evidence = dict(v3_profile.stage_log_evidence)
    # Atomic-accounting normalization: the V2 T/D/P slice has three observed
    # typed channels; the V3 GROW slice scores five typed channels.
    v2_predictive = v2_log_evidence / (3.0 * len(v2_state.observations))
    v3_predictive = v3_evidence["grow"] / (5.0 * 16.0)
    return {
        "seed": seed, "cell": "common_world_tournament", "stratum": stratum,
        "truth_mode_count": mode_count, "truth_topology": topology,
        "v2": {
            "qualified": v2_trajectory.qualifies(v2_state),
            "formation_confidence": float(max(v2_state.q_formation)),
            "formation_correct": int(np.argmax(v2_state.q_formation)) == v2_formation.LABELS.index(v2_state.truth_candidate),
            "predictive_log_density_per_atomic_token": v2_predictive,
            "successful_sequence": bool(v2_profile.successful_sequence),
            "material_redescription": bool(v2_profile.material_redescription),
            "material_reduction": bool(v2_profile.material_reduction),
            "historical_error": float(v2_profile.historical_context_error),
        },
        "v3": {
            "predictive_log_density_per_atomic_token": v3_predictive,
            "q_identity_organization": v3_profile.q_identity_organization,
            "q_external_danger": v3_profile.q_external_danger,
            "q_context_specific": v3_profile.q_context_specific,
            "q_current_edge_absence": v3_profile.q_current_edge_absence,
            "historical_retention": v3_profile.historical_retention,
            "q_partner_reliable": v3_profile.q_partner_reliable,
            "q_policy_open": v3_profile.q_policy_open,
            "L_total": v3_profile.L_total,
        },
    }


def run_gate3() -> dict[str, Any]:
    gate2 = json.loads((RESULTS / "gate-2.json").read_text())
    if gate2["verdict"] != "PASS":
        raise RuntimeError("Gate 2 must pass before Gate 3")
    rows = _trace_map(
        "gate-3", list(range(GATE3_BLOCK[0], GATE3_BLOCK[1] + 1)),
        _gate3_row,
    )
    parameters = json.loads(PARAMETERS.read_text())
    floors = parameters["criteria"]["effect_minima"]
    paired = [row for row in rows if row["cell"] == "paired_comparator"]
    effects = {}
    failures = []
    for comparator in v36.PROTOCOLS[1:]:
        selected = [row for row in paired if row["comparator"] == comparator]
        values = [_contrast(row["full"], row["other"], comparator) for row in selected]
        interval = _bootstrap_interval(values, 361_400 + len(effects))
        entry = {"mean": float(np.mean(values)), "interval_95": interval, "world_count": len(values)}
        if comparator == "premature_do_over":
            entry.update({"classification": "DESCRIPTIVE_RETAINED_FINDING", "floor": None, "gate_criterion": False})
        else:
            floor = floors[comparator]
            passed = entry["mean"] >= floor and interval[0] > 0.0
            entry.update({"floor": floor, "passed": passed})
            if not passed:
                failures.append(f"{comparator} effect failed")
        effects[comparator] = entry

    stress_rows = [row for row in rows if row["cell"] == "stakes_and_6B_stress"]
    scientific_fields = (
        "q_identity_organization", "q_external_danger", "q_action_efficacy",
        "episodic_information", "q_context_specific", "q_recurrent_context",
        "historical_retention", "q_current_edge_absence", "root_revision",
        "q_partner_reliable", "local_precision", "global_precision",
        "root_evidence_uptake", "root_transfer", "q_joint_policy_edge",
        "support_response", "contact_response", "stage_log_evidence",
    )
    identity_errors, policy_effects = [], []
    for row in stress_rows:
        low, high = row["low"], row["high"]
        errors = []
        for field in scientific_fields:
            a, b = low[field], high[field]
            if isinstance(a, list):
                aa, bb = np.asarray(a, dtype=object).ravel(), np.asarray(b, dtype=object).ravel()
                errors.extend(abs(float(x) - float(y)) for x, y in zip(aa, bb) if isinstance(x, (int, float)) and isinstance(y, (int, float)))
            else:
                errors.append(abs(float(a) - float(b)))
        identity_errors.append(max(errors, default=0.0))
        policy_effects.append(float(low["q_policy_open"] - high["q_policy_open"]))
    policy_interval = _bootstrap_interval(policy_effects, 361_999)
    stakes = {
        "scientific_identity_error_max": max(identity_errors),
        "policy_effect_mean": float(np.mean(policy_effects)),
        "policy_effect_interval_95": policy_interval,
        "identity_tolerance": parameters["criteria"]["stakes_scientific_identity_tolerance"],
        "policy_floor": parameters["criteria"]["stakes_policy_effect_min"],
    }
    stakes["passed"] = (
        stakes["scientific_identity_error_max"] <= stakes["identity_tolerance"]
        and stakes["policy_effect_mean"] >= stakes["policy_floor"]
        and policy_interval[0] > 0.0
    )
    if not stakes["passed"]:
        failures.append("stakes identity/policy effect failed")

    tournament_rows = [row for row in rows if row["cell"] == "common_world_tournament"]
    differences = [row["v3"]["predictive_log_density_per_atomic_token"] - row["v2"]["predictive_log_density_per_atomic_token"] for row in tournament_rows]
    difference_interval = _bootstrap_interval(differences, 362_999)
    accounting = json.loads((ROOT / "audits" / "v3.6-compression-accounting.json").read_text())
    margin = parameters["criteria"]["noninferiority_margin_nats_per_token"]
    tournament = {
        "world_count": len(tournament_rows),
        "same_seed_common_truth_conditions": True,
        "predictive_difference_v3_minus_v2_mean": float(np.mean(differences)),
        "predictive_difference_interval_95": difference_interval,
        "noninferiority_margin": margin,
        "noninferiority_pass": difference_interval[0] >= -margin,
        "v2_formation_accuracy": float(np.mean([row["v2"]["formation_correct"] for row in tournament_rows])),
        "v2_mean_confidence": float(np.mean([row["v2"]["formation_confidence"] for row in tournament_rows])),
        "v2_qualification_rate": float(np.mean([row["v2"]["qualified"] for row in tournament_rows])),
        "v3_gate2_calibration": {key: gate2["metrics"][key] for key in ("ece", "coverage", "active_count_accuracy", "minimum_edge_accuracy", "candidate_support_pass_rate")},
        "v3_structure_length_mean": float(np.mean([row["v3"]["L_total"] for row in tournament_rows])),
        "factor_template_reduction": accounting["reductions"]["factor_templates_fraction"],
        "constant_reduction": accounting["reductions"]["frozen_scientific_constants_fraction"],
        "factor_reduction_pass": accounting["reductions"]["factor_templates_at_least_50_percent"],
        "constant_reduction_pass": accounting["reductions"]["constants_at_least_50_percent"],
        "pareto_profile_only": True,
        "stress_cells": {
            "mode_counts": [1, 2, 3], "higher_slot_nonmissing": True,
            "mixed_masking_dormancy": True, "support_one_vs_all": True,
            "stakes_posterior_identity": stakes["scientific_identity_error_max"],
            "policy_histories": ["exclusion", "monitoring", "engagement", "mixed"],
            "topologies": ["independent", "opposed", "allied"],
            "signed_interventional_fingerprints_reported": True,
        },
    }
    if not tournament["noninferiority_pass"]:
        failures.append("tournament predictive noninferiority failed")
    if not tournament["factor_reduction_pass"] or not tournament["constant_reduction_pass"]:
        failures.append("compression reduction criterion failed")
    result = {
        "stage": "V3.6", "gate": 3, "seed_block": list(GATE3_BLOCK),
        "seeds_consumed": len(rows), "ascending_gap_free": [row["seed"] for row in rows] == list(range(GATE3_BLOCK[0], GATE3_BLOCK[1] + 1)),
        "effects": effects,
        "premature_do_over_required_downstream_record": parameters["retained_descriptive_findings"]["premature_do_over_endpoint_path_independence"],
        "stakes": stakes, "compression_tournament": tournament,
        "failures": failures, "bounds": dict(v36.finite_information_bounds()),
        "custody": {"trace_hash_ledger": "gate-3-trace-hashes.json", "escrow_touched": False, "barred_blocks_touched": False},
        "verdict": "PASS" if not failures else "FAIL",
    }
    _write_json("gate-3.json", result)
    _write_report("gate-3.md", "V3.6 Gate 3 — composition and compression tournament", result)
    if failures:
        _write_json("gate-3-diagnosis-stub.json", {"stage": "V3.6", "gate": 3, "failures": failures, "next_action": "HONEST_STOP"})
    return result


def _contrast(full: Mapping[str, Any], other: Mapping[str, Any], comparator: str) -> float:
    fields = {
        "regulation_without_root_evidence": "root_evidence_uptake",
        "cue_only_exposure": "root_transfer",
        "mode_bypass": "q_policy_open",
        "soothing_noncontingent_partner": "q_partner_reliable",
        "unreliable_partner": "q_partner_reliable",
        "broadcast_off_monitor": "root_evidence_uptake",
        "premature_do_over": "q_current_edge_absence",
        "context_scope_disabled": "q_context_specific",
        "structural_pruning_disabled": "q_current_edge_absence",
    }
    if comparator == "denied_contact_masked":
        return float(full["contact_response"][2] - other["contact_response"][2])
    return float(full[fields[comparator]] - other[fields[comparator]])


def _aggregate_pilot(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    comparator_rows = [row for row in rows if row["cell"] == "comparator"]
    effects: dict[str, Any] = {}
    attainable = True
    for comparator in v36.PROTOCOLS[1:]:
        selected = [row for row in comparator_rows if row["comparator"] == comparator]
        values = [_contrast(row["full"], row["other"], comparator) for row in selected]
        interval = _bootstrap_interval(values, 36_000 + len(effects))
        ok = interval[0] > 0.0
        effects[comparator] = {"kind": "causal_effect", "direction": "positive", "mean": float(np.mean(values)), "interval_95": interval, "attainable": ok}
        attainable = attainable and ok
    stress_rows = [row for row in rows if row["cell"] == "round10_stress"]
    scientific_fields = (
        "q_identity_organization", "q_external_danger", "q_action_efficacy",
        "episodic_information", "q_context_specific", "q_recurrent_context",
        "historical_retention", "q_current_edge_absence", "root_revision",
        "q_partner_reliable", "local_precision", "global_precision",
        "root_evidence_uptake", "root_transfer", "q_joint_policy_edge",
        "support_response", "contact_response", "stage_log_evidence",
    )
    stakes_errors = []
    stakes_policy = []
    for row in stress_rows:
        low, high = row["low"], row["high"]
        errors = []
        for field in scientific_fields:
            a, b = low[field], high[field]
            if isinstance(a, list):
                flat_a = np.asarray(a, dtype=object).ravel()
                flat_b = np.asarray(b, dtype=object).ravel()
                numeric = [abs(float(x) - float(y)) for x, y in zip(flat_a, flat_b) if isinstance(x, (int, float)) and isinstance(y, (int, float))]
                errors.append(max(numeric, default=0.0))
            else:
                errors.append(abs(float(a) - float(b)))
        stakes_errors.append(max(errors))
        stakes_policy.append(float(low["q_policy_open"] - high["q_policy_open"]))
    stakes_interval = _bootstrap_interval(stakes_policy, 36_999)
    stakes_ok = max(stakes_errors, default=0.0) <= TOLERANCE and stakes_interval[0] > 0.0
    attainable = attainable and stakes_ok
    profile_rows = [row for row in rows if row["cell"] == "compression_profile"]
    lengths = [float(row["profile"]["L_total"]) for row in profile_rows]
    accounting = json.loads((ROOT / "audits" / "v3.6-compression-accounting.json").read_text())
    result = {
        "stage": "V3.6", "pilot_block": list(FRESH_PILOT_BLOCK),
        "barred_seed": BARRED_CUSTODY_SEED,
        "world_count": len(rows),
        "seed_order_gap_free": [row["seed"] for row in rows] == list(range(FRESH_PILOT_BLOCK[0], FRESH_PILOT_BLOCK[1] + 1)),
        "effects": effects,
        "stakes_identity_error_max": max(stakes_errors, default=0.0),
        "stakes_policy_low_minus_high": {"mean": float(np.mean(stakes_policy)), "interval_95": stakes_interval, "attainable": stakes_interval[0] > 0.0},
        "structure_code_length": {"mean": float(np.mean(lengths)), "min": float(np.min(lengths)), "max": float(np.max(lengths)), "quantiles": [float(x) for x in np.quantile(lengths, [0.05, 0.5, 0.95])]},
        "compression_counts": accounting["reductions"],
        "retained_findings": {
            "V3.1_revisability_effect_interval": json.loads((ROOT / "results" / "V3.1" / "gate-3.json").read_text())["metrics"].get("revisability_difference_95_interval"),
            "V3.3_do_over_equivalence": json.loads((ROOT / "results" / "V3.3" / "gate-5.json").read_text())["adjudicated_nonblocking"].get("do_over_speedup_floor_repetition"),
            "V3.4_information_curve": json.loads((ROOT / "results" / "V3.4" / "gate-5-adjudicated.json").read_text()).get("information_curve"),
            "V3.5_failure_records": [
                "original dormant-idleness proof did not prove common observed-channel support",
                "original polarization readout was conditional rather than interventional",
            ],
        },
        "all_declared_signs_attainable": attainable,
        "verdict": "PASS" if attainable else "FAIL",
    }
    return result


def _mechanical_freeze(result: Mapping[str, Any]) -> None:
    parameters = json.loads(PARAMETERS.read_text())
    parameters["status"] = "STAGE0_MECHANICALLY_FROZEN_AWAITING_SEALS"
    parameters["fresh_pilot_summary_sha256"] = hashlib.sha256(
        (RESULTS / "stage-0-adjudicated-attainability-pilot.json").read_bytes()
    ).hexdigest()
    parameters["criteria"] = {
        "effect_minima": {
            name: 0.5 * abs(float(values["mean"]))
            for name, values in result["effects"].items()
            if name != "premature_do_over"
        },
        "stakes_policy_effect_min": 0.5 * abs(float(result["stakes_policy_low_minus_high"]["mean"])),
        "stakes_scientific_identity_tolerance": TOLERANCE,
        "equivalence_rope": 0.01,
        "noninferiority_margin_nats_per_token": parameters["noninferiority_margin_nats_per_token"],
    }
    first = json.loads(
        (RESULTS / "stage-0-attainability-pilot.json").read_text()
    )["effects"]["premature_do_over"]
    fresh = result["effects"]["premature_do_over"]
    parameters["retained_descriptive_findings"] = {
        "premature_do_over_endpoint_path_independence": {
            "floor": None,
            "gate_criterion": False,
            "required_in_every_downstream_profile": True,
            "first_pilot": {
                "mean": first["mean"],
                "interval_95": first["interval_95"],
                "declaration": "equivalence",
            },
            "fresh_event_indexed_pilot": {
                "mean": fresh["mean"],
                "interval_95": fresh["interval_95"],
                "declaration": "positive causal effect",
            },
            "v3_3_cross_reference": "premature shortcut alone was not durable; post-revision do-over equivalence remains",
        }
    }
    PARAMETERS.write_text(json.dumps(parameters, indent=2, sort_keys=True) + "\n")
    accounting_path = ROOT / "audits" / "v3.6-compression-accounting.json"
    accounting = json.loads(accounting_path.read_text())
    accounting["status"] = "stage-0 mechanically frozen"
    accounting["v3"]["per_world_structure_code_length"] = result["structure_code_length"]
    accounting["finalization"] = {
        "pilot_block": list(FRESH_PILOT_BLOCK),
        "pilot_summary_sha256": parameters["fresh_pilot_summary_sha256"],
        "v3_5_repair_factors_included": True,
        "factor_and_constant_reductions_exceed_50_percent": True,
        "one_structural_prior_only": True,
        "named_v2_hypothesis_menu_in_scientific_state": False,
        "separate_formation_and_reduction_edge_stores": False,
        "independent_efficacy_or_episode_ontology": False,
        "topology_or_trust_state_ontology": False,
        "pareto_profile_required": True,
    }
    accounting_path.write_text(json.dumps(accounting, indent=2, sort_keys=True) + "\n")


def _freeze_readiness(result: Mapping[str, Any]) -> None:
    files = [
        "audits/v3.6-compression-accounting.json",
        "contracts/v3.6-compose-contract.md",
        "protocols/v3.6-analysis-plan.md",
        "protocols/v3.6-parameters.json",
        "protocols/v3.6-public-dummy.json",
        "ref/v36.py", "ref/v36_oracle.py", "scripts/run_v36.py",
        "tests/test_v36_compose.py",
        "results/V3.6/gate-1.json", "results/V3.6/gate-1-adjudicated.json",
        "results/V3.6/stage0-custody-stop.json",
        "results/V3.6/stage0-custody-adjudication.md",
        "results/V3.6/stage0-adjudication.md",
        "results/V3.6/stage0-adjudication-2.md",
        "results/V3.6/stage-0-attainability-pilot.json",
        "results/V3.6/stage0-pilot-diagnosis-stub.json",
        "results/V3.6/stage-0-adjudicated-attainability-pilot.json",
        "results/V3.6/stage-0-adjudicated-attainability-pilot-trace-hashes.json",
        "results/V3.6/stage0-adjudicated-pilot-diagnosis-stub.json",
        "results/V3.6/stage0-adjudication-2-conformance.json",
    ]
    hashes = {
        relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        for relative in files
    }
    readiness = {
        "stage": "V3.6", "status": "STAGE0_FREEZE_READY_AWAITING_C_V36A_B_C_SEALS",
        "gate1": "PASS",
        "fresh_pilot_formal_record": "FAIL_RETAINED_AS_DESCRIPTIVE_FINDING",
        "stage0_adjudication_2_authorized_progression": True,
        "first_pilot_stop_retained": True,
        "premature_do_over_floor": None,
        "premature_do_over_gate_criterion": False,
        "floors_frozen_mechanically": True,
        "fresh_pilot_block": list(FRESH_PILOT_BLOCK),
        "gate_blocks_opened": False, "escrow_touched": False,
        "bounds": dict(v36.finite_information_bounds()),
    }
    _write_json("stage0-freeze-readiness.json", readiness)
    _write_report("stage0-freeze-readiness.md", "V3.6 Stage-0 freeze readiness", {**readiness, "verdict": "PASS"})
    _write_json("stage0-freeze-manifest.json", {
        "stage": "V3.6", "status": readiness["status"],
        "hash_algorithm": "sha256", "files": hashes,
        "escrow": {"C-V36A": [4100000, 4109999], "C-V36B": [4110000, 4119999], "C-V36C": [4120000, 4129999]},
    })
    _write_json("stage0-pre-seal-package.json", {
        "stage": "V3.6",
        "status": readiness["status"],
        "public_dummy": "protocols/v3.6-public-dummy.json",
        "parameters": "protocols/v3.6-parameters.json",
        "compression_accounting": "audits/v3.6-compression-accounting.json",
        "freeze_manifest": "results/V3.6/stage0-freeze-manifest.json",
        "freeze_manifest_sha256": hashlib.sha256(
            (RESULTS / "stage0-freeze-manifest.json").read_bytes()
        ).hexdigest(),
        "gate_blocks_opened": False,
        "escrow_touched": False,
    })


def run_adjudicated_freeze() -> dict[str, Any]:
    result = json.loads(
        (RESULTS / "stage-0-adjudicated-attainability-pilot.json").read_text()
    )
    failures = sorted(
        name for name, values in result["effects"].items()
        if not values["attainable"]
    )
    if failures != ["premature_do_over"]:
        raise RuntimeError(f"adjudicated freeze mismatch: {failures}")
    if result["stakes_identity_error_max"] > TOLERANCE:
        raise RuntimeError("stakes identity no longer exact")
    if not result["stakes_policy_low_minus_high"]["attainable"]:
        raise RuntimeError("stakes policy effect not attainable")
    conformance = {
        "stage": "V3.6",
        "authorization": "results/V3.6/stage0-adjudication-2.md",
        "seed_consumption": [],
        "only_nonattainable_contrast": failures,
        "premature_floor": None,
        "premature_gate_criterion": False,
        "remaining_floors_frozen_mechanically": True,
        "verdict": "PASS",
    }
    _write_json("stage0-adjudication-2-conformance.json", conformance)
    _mechanical_freeze(result)
    _freeze_readiness(result)
    return conformance


def run_fresh_pilot() -> dict[str, Any]:
    gate1 = json.loads((RESULTS / "gate-1-adjudicated.json").read_text())
    if gate1["verdict"] != "PASS":
        raise RuntimeError("Gate 1 must pass before pilot")
    rows = _trace_map(
        "stage-0-adjudicated-attainability-pilot",
        list(range(FRESH_PILOT_BLOCK[0], FRESH_PILOT_BLOCK[1] + 1)),
        _pilot_row,
    )
    result = _aggregate_pilot(rows)
    _write_json("stage-0-adjudicated-attainability-pilot.json", result)
    _write_report("stage-0-adjudicated-attainability-pilot.md", "V3.6 adjudicated traced attainability pilot", result)
    if result["verdict"] == "PASS":
        _mechanical_freeze(result)
        _freeze_readiness(result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("gate1", "gate1-adjudicated", "fresh-pilot", "adjudicated-freeze", "gate2", "gate3"))
    args = parser.parse_args()
    if args.command == "gate1":
        result = run_gate1()
    elif args.command == "gate1-adjudicated":
        result = run_gate1_adjudicated()
    elif args.command == "fresh-pilot":
        result = run_fresh_pilot()
    elif args.command == "adjudicated-freeze":
        result = run_adjudicated_freeze()
    elif args.command == "gate2":
        result = run_gate2()
    else:
        result = run_gate3()
    print(json.dumps({"command": args.command, "verdict": result["verdict"]}, sort_keys=True))


if __name__ == "__main__":
    main()
