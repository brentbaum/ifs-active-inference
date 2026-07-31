#!/usr/bin/env python3
"""Prospective V3.5 PROTECT stage runner."""

from __future__ import annotations

import argparse
import ast
import hashlib
import itertools
import json
import math
import os
import sys
from dataclasses import asdict, replace
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ref import (  # noqa: E402
    audit,
    v35,
    v35_calibration,
    v35_calibration_oracle,
    v35_oracle,
    retro_calibration_audit,
    v35_topology,
    v35_topology_oracle,
)
from ref.trace_sink import serializing_trace_context, traced_execution  # noqa: E402


RESULTS = ROOT / "results" / "V3.5"
PARAMETERS = ROOT / "protocols" / "v3.5-parameters.json"
TOLERANCE = 1e-10
SMOKE_BLOCK = (3_520_000, 3_520_999)
REPAIRED_PILOT_BLOCK = (3_521_000, 3_522_999)


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
                   allow_nan=False) + "\n"
    )


def _trace_map(name: str, tasks: Sequence[Any], worker: Any):
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{name}-traces.jsonl"
    file_hash = hashlib.sha256()
    records, rows = [], []
    processes = max(1, min(8, (os.cpu_count() or 2) - 1))
    with path.open("wb") as handle:
        with get_context("spawn").Pool(processes) as pool:
            for row in pool.imap(worker, tasks, chunksize=4):
                encoded = _canonical(row)
                handle.write(encoded)
                handle.flush()
                file_hash.update(encoded)
                records.append({
                    "seed": row["seed"],
                    "sha256": hashlib.sha256(encoded).hexdigest(),
                })
                rows.append(row)
    _write_json(f"{name}-trace-hashes.json", {
        "file": path.name,
        "world_count": len(rows),
        "file_sha256": file_hash.hexdigest(),
        "records": records,
    })
    return rows


def _config(**changes):
    values = dict(
        befriend="all", partner="remaining", stakes="high",
        policy_regime="mixed", mode_count=3, topology="allied",
        support_target="all", registration="delivered",
        denied_contact="delivered", length=64,
    )
    values.update(changes)
    return v35.ProtectConfig(**values)


def _component_key(structure, sign, reliable):
    return (
        structure.active_modes, structure.mode_root_edges,
        structure.joint_policy_outcome, structure.cross_mode_outcome,
        sign, reliable,
    )


def _structure_probabilities(posterior):
    result = {}
    for probability, (structure, sign) in zip(
        posterior.probabilities, posterior.components
    ):
        key = (
            structure.active_modes, structure.mode_root_edges,
            structure.joint_policy_outcome, structure.cross_mode_outcome,
        )
        result[key] = result.get(key, 0.0) + probability
    return result


@traced_execution
def _gate1_row():
    world = v35.generate_world(
        3_520_002,
        replace(_config(), length=8),
        released_block=SMOKE_BLOCK,
    )
    posterior = v35.score_world(world)
    observations = [asdict(item) for item in world.observations]
    snapshot = json.dumps(observations, sort_keys=True)
    keys, oracle_probabilities, oracle_evidence = v35_oracle.posterior(
        observations
    )
    reliable_order = [
        reliable
        for structure in v35.PROGRAMS
        for sign in ((-1, 1) if structure.cross_mode_outcome else (0,))
        for reliable in (0, 1)
    ]
    production = {
        _component_key(structure, sign, reliable): probability
        for probability, (structure, sign), reliable in zip(
            posterior.probabilities, posterior.components, reliable_order
        )
    }
    oracle_error = max(
        abs(probability - production[key])
        for key, probability in zip(keys, oracle_probabilities)
    )
    full_map = _structure_probabilities(posterior)
    restricted = v35.score_world(
        world, restrictions={"CROSS_MODE_Y": (0,)}
    )
    restricted_map = _structure_probabilities(restricted)
    retained = {key: value for key, value in full_map.items() if key[-1] == 0}
    mass = math.fsum(retained.values())
    restricted_error = max(
        abs(value - retained[key] / mass)
        for key, value in restricted_map.items()
    )
    masked = replace(
        world,
        observations=tuple(
            replace(item, registration=(None, None, None))
            for item in world.observations
        ),
    )
    masked_p = v35.score_world(masked)
    disabled_p = v35.score_world(world, registration_enabled=False)
    registration_error = max(
        abs(a - b) for a, b in zip(
            masked_p.probabilities, disabled_p.probabilities
        )
    )
    denied_masked = replace(
        world,
        observations=tuple(
            replace(
                item,
                denied_contact=None,
                contact_signals=(None, None, None),
            )
            for item in world.observations
        ),
    )
    denied_error = max(
        abs(a - b) for a, b in zip(
            v35.score_world(denied_masked).probabilities,
            v35.score_world(world, denied_enabled=False).probabilities,
        )
    )
    prior_sum = math.fsum(
        math.exp(v35.structure_log_prior(program))
        for program in v35.PROGRAMS
    )
    factor_error = 0.0
    for latent in (0, 1):
        factor_error = max(
            factor_error,
            abs(sum(v35.mode_signal_probability(o, latent) for o in (0, 1)) - 1),
            abs(sum(v35.registration_probability(o, latent) for o in (0, 1)) - 1),
        )
    for reliable in (0, 1):
        for channel in ("remaining", "pressure"):
            factor_error = max(
                factor_error,
                abs(sum(v35.partner_channel_probability(
                    o, reliable, channel
                ) for o in (0, 1)) - 1),
            )
    absent = v35.ProtectStructure(3, (0, 0, 0), 0, 0)
    edge_absence = max(
        abs(v35.outcome_probability(policy, modes, absent, 0) - 0.5)
        for policy in v35.JOINT_POLICIES
        for modes in itertools.product((0, 1), repeat=3)
    )
    source = (ROOT / "ref" / "v35.py").read_text()
    tree = ast.parse(source)
    forbidden_functions = [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name in {
            "assign_access", "set_protector", "polarization_coefficient",
            "exile_force", "policy_selection_likelihood",
        }
    ]
    label_rejected = False
    try:
        v35.score_world(replace(world, analysis_labels=("protector",)))
    except ValueError:
        label_rejected = True
    calibration = dict(v35.marginal_calibration_dummy())
    calibration_oracle = v35_oracle.marginal_calibration_dummy()
    calibration_oracle_error = max(
        abs(float(left) - float(right))
        for name in ("priors", "likelihoods", "posteriors")
        for production_row, oracle_row in zip(
            calibration[name], calibration_oracle[name]
        )
        for left, right in zip(
            (
                production_row
                if isinstance(production_row, tuple)
                else (production_row,)
            ),
            (
                oracle_row
                if isinstance(oracle_row, tuple)
                else (oracle_row,)
            ),
        )
    )
    expanded_calibration = v35_calibration.run()
    expanded_tables = v35_calibration.joint_tables()
    expanded_oracle = v35_calibration_oracle.enumerate_joint()
    expanded_oracle_error = max(
        max(abs(a - b) for a, b in zip(
            expanded_tables["likelihoods"].flat,
            (value for row in expanded_oracle["likelihoods"] for value in row),
        )),
        max(abs(a - b) for a, b in zip(
            expanded_tables["posterior_by_observation"].flat,
            (
                value
                for row in expanded_oracle["posterior_by_observation"]
                for value in row
            ),
        )),
    )
    topology_fixture = v35_topology.run()
    topology_oracle = v35_topology_oracle.run()
    topology_oracle_error = max(
        abs(
            topology_fixture["fingerprints"][truth][source][target]
            - topology_oracle["fingerprints"][truth][source][target]
        )
        for truth in ("independent", "opposed", "allied")
        for source, target in ((0, 1), (1, 0))
    )
    proofs = {
        "1_structure_prior_error": abs(prior_sum - 1.0),
        "2_factor_normalization_error": factor_error,
        "3_policy_space_size": len(v35.JOINT_POLICIES),
        "3_policy_normalization_error": abs(
            math.fsum(posterior.joint_policy_posterior) - 1.0
        ),
        "4_dormant_slots_idle": all(
            p.mode_root_edges[p.active_modes:] == (0,) * (3 - p.active_modes)
            for p in v35.PROGRAMS
        ),
        "5_edge_absence_error": edge_absence,
        "6_registration_mask_error": registration_error,
        "7_registration_outcome_direct_path": False,
        "8_denied_mask_error": denied_error,
        "9_action_selection_functions": forbidden_functions,
        "10_generator_scorer_exact_log_error": abs(
            world.exact_log_probability
            - v35.exact_complete_log_probability(world)
        ),
        "11_posterior_normalization_error": abs(
            math.fsum(posterior.probabilities) - 1.0
        ),
        "12_independent_oracle_error": oracle_error,
        "12_oracle_evidence_error": abs(
            math.exp(posterior.log_evidence) - oracle_evidence
        ),
        "12_oracle_input_copy": snapshot == json.dumps(
            observations, sort_keys=True
        ),
        "13_restricted_prior_error": restricted_error,
        "14_analysis_label_rejected": label_rejected,
        "15_readout_state_audit": audit.audit_state(posterior),
        "15_import_audit": audit.audit_imports(ROOT / "ref"),
        "17_marginal_dummy_oracle_error": calibration_oracle_error,
        "17_marginal_dummy_exact_ece": calibration["exact_ece"],
        "17_marginal_dummy_accuracy_confidence_gap": (
            calibration["exact_accuracy_confidence_gap"]
        ),
        "17_marginal_dummy_sampled_ece": calibration["sampled_ece"],
        "17_marginal_dummy_sampled_coverage_error": (
            calibration["sampled_coverage_error"]
        ),
        "17_marginal_dummy_sampling_tolerance": (
            calibration["declared_sampling_tolerance"]
        ),
        "17_expanded_marginal_calibration": expanded_calibration,
        "17_expanded_independent_oracle_error": expanded_oracle_error,
        "18_interventional_topology_fixture": topology_fixture,
        "18_topology_independent_oracle_error": topology_oracle_error,
    }
    sampling_proofs = {
        "17_marginal_dummy_sampled_ece",
        "17_marginal_dummy_sampled_coverage_error",
        "17_marginal_dummy_sampling_tolerance",
    }
    numeric = [
        abs(value) for name, value in proofs.items()
        if isinstance(value, float) and name not in sampling_proofs
    ]
    passed = (
        all(value <= TOLERANCE for value in numeric)
        and proofs["3_policy_space_size"] == 27
        and proofs["4_dormant_slots_idle"]
        and not forbidden_functions
        and proofs["12_oracle_input_copy"]
        and label_rejected
        and not proofs["15_readout_state_audit"]
        and not proofs["15_import_audit"]
        and calibration_oracle_error <= TOLERANCE
        and calibration["exact_ece"] <= TOLERANCE
        and calibration["exact_accuracy_confidence_gap"] <= TOLERANCE
        and calibration["sampled_ece"]
        <= calibration["declared_sampling_tolerance"]
        and calibration["sampled_coverage_error"]
        <= calibration["declared_sampling_tolerance"]
        and expanded_calibration["passed"]
        and expanded_oracle_error <= TOLERANCE
        and topology_fixture["passed"]
        and topology_oracle_error <= TOLERANCE
    )
    return {
        "seed": "authored_dummy",
        "passed": passed,
        "proofs": proofs,
        "structure_space_size": len(v35.PROGRAMS),
        "component_space_size": len(posterior.components),
        "bounds": dict(v35.finite_information_bounds()),
    }


def run_gate1():
    refusal = False
    try:
        v35.generate_world(
            3_520_002,
            _config(),
            released_block=SMOKE_BLOCK,
        )
    except RuntimeError:
        refusal = True
    row = _gate1_row()
    row["proofs"]["16_trace_sink_refusal"] = refusal
    row["passed"] = row["passed"] and refusal
    _trace_map_single("gate-1-amendment-1-rerun", row)
    result = {
        "verdict": "PASS" if row["passed"] else "FAIL",
        "proofs": row["proofs"],
        "structure_space_size": row["structure_space_size"],
        "component_space_size": row["component_space_size"],
        "bounds": row["bounds"],
    }
    _write_json("gate-1-amendment-1-rerun.json", result)
    params = json.loads(PARAMETERS.read_text())
    params["bounds"] = row["bounds"]
    params["status"] = "GATE1_PASSED" if row["passed"] else "STOPPED_AT_GATE1"
    PARAMETERS.write_text(json.dumps(params, indent=2, sort_keys=True) + "\n")
    return row["passed"]


def run_amendment_preflight():
    calibration = v35_calibration.run()
    production_tables = v35_calibration.joint_tables()
    oracle_tables = v35_calibration_oracle.enumerate_joint()
    calibration_oracle_error = max(
        max(abs(a - b) for a, b in zip(
            production_tables["likelihoods"].flat,
            (
                value
                for row in oracle_tables["likelihoods"]
                for value in row
            ),
        )),
        max(abs(a - b) for a, b in zip(
            production_tables["posterior_by_observation"].flat,
            (
                value
                for row in oracle_tables["posterior_by_observation"]
                for value in row
            ),
        )),
    )
    topology = v35_topology.run()
    topology_oracle = v35_topology_oracle.run()
    topology_oracle_error = max(
        max(
            abs(
                topology["expected_log_bf"][truth][comparator]
                - topology_oracle["expected_log_bf"][truth][comparator]
            )
            for truth in ("independent", "opposed", "allied")
            for comparator in ("independent", "opposed", "allied")
        ),
        max(
            abs(
                topology["fingerprints"][truth][source][target]
                - topology_oracle["fingerprints"][truth][source][target]
            )
            for truth in ("independent", "opposed", "allied")
            for source, target in ((0, 1), (1, 0))
        ),
    )
    result = {
        "verdict": "PASS" if (
            calibration["passed"]
            and calibration_oracle_error <= TOLERANCE
            and topology["passed"]
            and topology_oracle_error <= TOLERANCE
        ) else "FAIL",
        "item_17_expanded": calibration,
        "item_17_independent_oracle_error": calibration_oracle_error,
        "interventional_topology_fixture": topology,
        "topology_independent_oracle_error": topology_oracle_error,
        "seed_consumption": "none; authored enumerable fixtures",
    }
    _write_json("stage0-amendment-1-preflight.json", result)
    return result["verdict"] == "PASS"


def run_retro_audits():
    results = {}
    for stage in ("V3.0", "V3.1", "V3.2", "V3.3", "V3.4"):
        result = retro_calibration_audit.run(stage)
        results[stage] = result["verdict"]
        path = ROOT / "results" / stage / "amendment-1-retro-calibration-audit.json"
        path.write_text(
            json.dumps(_plain(result), indent=2, sort_keys=True, allow_nan=False)
            + "\n"
        )
    summary = {
        "verdict": "PASS" if all(value == "PASS" for value in results.values()) else "FAIL",
        "stages": results,
        "existing_stage_verdicts_rewritten": False,
        "seed_consumption": "none; authored enumerable dummies",
    }
    _write_json("suite-wide-retro-calibration-audit.json", summary)
    return summary["verdict"] == "PASS"


def _trace_map_single(name, row):
    RESULTS.mkdir(parents=True, exist_ok=True)
    encoded = _canonical(row)
    path = RESULTS / f"{name}-traces.jsonl"
    path.write_bytes(encoded)
    _write_json(f"{name}-trace-hashes.json", {
        "file": path.name, "world_count": 1,
        "file_sha256": hashlib.sha256(encoded).hexdigest(),
        "records": [{"seed": row["seed"],
                     "sha256": hashlib.sha256(encoded).hexdigest()}],
    })


def _credible_contains(probabilities, truth_index):
    order = np.argsort(-np.asarray(probabilities))
    mass = 0.0
    for index in order:
        mass += probabilities[int(index)]
        if int(index) == truth_index:
            return True
        if mass >= 0.95:
            return False
    return False


def _ece(confidence, correct):
    p, y = np.asarray(confidence), np.asarray(correct, dtype=float)
    value = 0.0
    for low in np.linspace(0, .9, 10):
        high = low + .1
        chosen = (p >= low) & (p <= high if high == 1 else p < high)
        if chosen.any():
            value += chosen.mean() * abs(p[chosen].mean() - y[chosen].mean())
    return float(value)


@traced_execution
def _worker_recovery(task):
    seed, length, released = task
    world = v35.generate_recovery_world(
        seed, length=length, released_block=released
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
    return {
        "seed": seed,
        "truth_structure": truth_key,
        "predicted_structure": predicted,
        "edge_correct": [
            a == b for a, b in zip(predicted_edges, truth_edges)
        ],
        "active_count_correct": predicted[0] == truth_key[0],
        "program_correct": predicted == truth_key,
        "confidence": structure_map[predicted],
        "coverage": _credible_contains(probabilities, truth_index),
        "topology_correct": predicted_topology == truth_topology,
        "partner_correct": int(np.argmax(posterior.q_partner))
        == world.truth_partner,
        "normalization_error": abs(
            math.fsum(posterior.probabilities) - 1
        ),
        "exact_log_error": abs(
            world.exact_log_probability
            - v35.exact_complete_log_probability(world)
        ),
    }


def _recovery_metrics(rows):
    edge = {
        name: float(np.mean([row["edge_correct"][i] for row in rows]))
        for i, name in enumerate(v35.EDGE_NAMES)
    }
    return {
        "world_count": len(rows),
        "edge_accuracy": edge,
        "minimum_edge_accuracy": min(edge.values()),
        "active_count_accuracy": float(np.mean(
            [row["active_count_correct"] for row in rows]
        )),
        "program_accuracy": float(np.mean(
            [row["program_correct"] for row in rows]
        )),
        "topology_accuracy": float(np.mean(
            [row["topology_correct"] for row in rows]
        )),
        "partner_accuracy": float(np.mean(
            [row["partner_correct"] for row in rows]
        )),
        "ece": _ece(
            [row["confidence"] for row in rows],
            [row["program_correct"] for row in rows],
        ),
        "coverage": float(np.mean([row["coverage"] for row in rows])),
        "normalization_error_max": max(
            row["normalization_error"] for row in rows
        ),
        "exact_log_error_max": max(row["exact_log_error"] for row in rows),
    }


def _paired_interval(values, *, index):
    array = np.asarray(values, dtype=float)
    rng = np.random.default_rng(35_500 + index)
    boot = np.mean(
        array[rng.integers(0, len(array), size=(5_000, len(array)))],
        axis=1,
    )
    return {
        "mean": float(array.mean()),
        "ci95": [
            float(np.quantile(boot, 0.025)),
            float(np.quantile(boot, 0.975)),
        ],
        "n": int(len(array)),
    }


def _pilot_estimands(rows):
    result = {}
    for index, theme in enumerate(PILOT_THEMES):
        subset = [row for row in rows if row["theme"] == theme]
        values = {}
        if theme == "befriend":
            values = {
                "access": [r["right"]["access"] - r["left"]["access"] for r in subset],
                "support_response_3": [
                    r["right"]["support_response"][2]
                    - r["left"]["support_response"][2]
                    for r in subset
                ],
            }
        elif theme == "partner":
            values = {
                "q_remaining": [r["right"]["trust"] - r["left"]["trust"] for r in subset],
                "access": [r["right"]["access"] - r["left"]["access"] for r in subset],
            }
        elif theme == "stakes":
            values = {
                "access_low_minus_high": [
                    r["right"]["access"] - r["left"]["access"] for r in subset
                ],
                "scientific_posterior_identity_error": [
                    max(abs(a - b) for a, b in zip(
                        r["right"]["structure_probabilities"],
                        r["left"]["structure_probabilities"],
                    ))
                    for r in subset
                ],
            }
        elif theme.startswith("policy_"):
            values = {
                "joint_policy_edge_uptake": [
                    r["right"]["edges"]["JOINT_POLICY_Y"]
                    - r["left"]["edges"]["JOINT_POLICY_Y"]
                    for r in subset
                ]
            }
        elif theme == "mode_recovery":
            values = {
                "third_mode_exposure": [
                    r["right"]["active"][2] - r["left"]["active"][2]
                    for r in subset
                ]
            }
        elif theme == "mode_dormancy":
            values = {"dormant_influence_error": [r["dormant_effect"] for r in subset]}
        elif theme == "topology_opposed":
            values = {
                "opposed_recovery": [
                    r["right"]["topology"]["opposed"]
                    - r["left"]["topology"]["opposed"]
                    for r in subset
                ],
                "opposed_D_0_1": [-r["right"]["influence"][0][1] for r in subset],
                "opposed_D_1_0": [-r["right"]["influence"][1][0] for r in subset],
            }
        elif theme == "topology_allied":
            values = {
                "allied_recovery": [
                    r["right"]["topology"]["coalition"]
                    - r["left"]["topology"]["coalition"]
                    for r in subset
                ],
                "allied_D_0_1": [r["right"]["influence"][0][1] for r in subset],
                "allied_D_1_0": [r["right"]["influence"][1][0] for r in subset],
            }
        elif theme == "support":
            values = {
                "support_response_3": [
                    r["right"]["support_response"][2]
                    - r["left"]["support_response"][2]
                    for r in subset
                ],
                "access": [r["right"]["access"] - r["left"]["access"] for r in subset],
            }
        elif theme == "denied":
            values = {
                "contact_response_3": [
                    r["right"]["contact_response"][2]
                    - r["left"]["contact_response"][2]
                    for r in subset
                ],
                "access": [r["right"]["access"] - r["left"]["access"] for r in subset],
            }
        result[theme] = {
            name: _paired_interval(value, index=index * 10 + offset)
            for offset, (name, value) in enumerate(values.items())
        }
    return result


def _attainable(estimands):
    identity_names = {
        "scientific_posterior_identity_error",
        "dormant_influence_error",
    }
    failures = []
    for theme, values in estimands.items():
        for name, metric in values.items():
            if name in identity_names:
                if max(abs(value) for value in metric["ci95"]) > TOLERANCE:
                    failures.append(f"{theme}:{name}:identity")
            elif metric["ci95"][0] <= 0:
                failures.append(f"{theme}:{name}:sign")
    return failures


def _tasks(start, end, released):
    return [
        (seed, PILOT_THEMES[(seed - start) % len(PILOT_THEMES)], released)
        for seed in range(start, end + 1)
    ]


def run_smoke():
    recovery = _trace_map(
        "stage0-amendment-1-smoke-recovery",
        [(seed, 32, SMOKE_BLOCK) for seed in range(3_520_003, 3_520_303)],
        _worker_recovery,
    )
    assays = _trace_map(
        "stage0-amendment-1-smoke-assays",
        _tasks(3_520_303, 3_520_999, SMOKE_BLOCK),
        _worker_pilot,
    )
    result = {
        "verdict": "PASS" if not _attainable(_pilot_estimands(assays)) else "FAIL",
        "block": [3_520_000, 3_520_999],
        "prior_consumption": {
            "3520000": "pre-amendment repaired Gate-1 trace",
            "3520001": "retained masking-runner Gate-1 FAIL",
            "3520002": "Gate-1 Amendment-1 PASS",
        },
        "recovery": _recovery_metrics(recovery),
        "estimands": _pilot_estimands(assays),
        "failures": _attainable(_pilot_estimands(assays)),
    }
    _write_json("stage0-amendment-1-smoke.json", result)
    params = json.loads(PARAMETERS.read_text())
    params["status"] = (
        "AMENDMENT_1_SMOKE_PASSED"
        if result["verdict"] == "PASS"
        else "STOPPED_AT_AMENDMENT_1_SMOKE"
    )
    PARAMETERS.write_text(json.dumps(params, indent=2, sort_keys=True) + "\n")
    return result["verdict"] == "PASS"
    return {
        "world_count": len(rows),
        "edge_accuracy": edge,
        "minimum_edge_accuracy": min(edge.values()),
        "active_count_accuracy": float(np.mean(
            [row["active_count_correct"] for row in rows]
        )),
        "program_accuracy": float(np.mean(
            [row["program_correct"] for row in rows]
        )),
        "topology_accuracy": float(np.mean(
            [row["topology_correct"] for row in rows]
        )),
        "partner_accuracy": float(np.mean(
            [row["partner_correct"] for row in rows]
        )),
        "ece": _ece(
            [row["confidence"] for row in rows],
            [row["program_correct"] for row in rows],
        ),
        "coverage": float(np.mean([row["coverage"] for row in rows])),
        "normalization_error_max": max(
            row["normalization_error"] for row in rows
        ),
        "exact_log_error_max": max(row["exact_log_error"] for row in rows),
    }


def _summary(world):
    p = v35.score_world(world)
    return {
        "access": p.query("access_probability"),
        "exile": p.query("exile_like_probability"),
        "polarization": p.query("polarization"),
        "coalition": p.query("coalition"),
        "trust": p.query("trust_remaining"),
        "topology": dict(p.topology_probabilities),
        "active": p.active_mode_probabilities,
        "mode": p.mode_occupancy,
        "policy": p.joint_policy_posterior,
        "support_response": p.support_response_posterior,
        "contact_response": p.contact_response_posterior,
        "influence": p.interventional_influence,
        "edges": dict(p.edge_probabilities),
        "structure_probabilities": p.probabilities,
    }


PILOT_THEMES = (
    "befriend",
    "partner",
    "stakes",
    "policy_exclusion",
    "policy_monitoring",
    "policy_engagement",
    "mode_recovery",
    "mode_dormancy",
    "topology_opposed",
    "topology_allied",
    "support",
    "denied",
)


@traced_execution
def _worker_pilot(task):
    seed, theme, released = task
    pairs = {
        "befriend": (_config(befriend="none"), _config(befriend="all")),
        "partner": (
            _config(partner="pressure"),
            _config(partner="remaining"),
        ),
        "stakes": (_config(stakes="high"), _config(stakes="low")),
        "mode_recovery": (
            _config(mode_count=2),
            _config(mode_count=3),
        ),
        "topology_opposed": (
            _config(topology="independent"),
            _config(topology="opposed"),
        ),
        "topology_allied": (
            _config(topology="independent"),
            _config(topology="allied"),
        ),
        "support": (
            _config(support_target="one"),
            _config(support_target="all"),
        ),
        "denied": (
            _config(denied_contact="masked"),
            _config(denied_contact="delivered"),
        ),
    }
    if theme.startswith("policy_"):
        regime = theme.removeprefix("policy_")
        world = v35.generate_world(
            seed, _config(policy_regime=regime), released_block=released
        )
        masked = replace(
            world,
            observations=tuple(
                replace(observation, outcome=None)
                for observation in world.observations
            ),
        )
        return {
            "seed": seed,
            "theme": theme,
            "left": _summary(masked),
            "right": _summary(world),
        }
    if theme == "mode_dormancy":
        world = v35.generate_world(
            seed, _config(mode_count=2), released_block=released
        )
        posterior = v35.score_world(
            world, restrictions={"active_modes": (2,)}
        )
        dormant_effect = max(
            abs(posterior.interventional_influence[2][index])
            + abs(posterior.interventional_influence[index][2])
            for index in (0, 1)
        )
        return {
            "seed": seed,
            "theme": theme,
            "dormant_effect": dormant_effect,
            "left": _summary(world),
            "right": _summary(world),
        }
    left_config, right_config = pairs[theme]
    left_world = v35.generate_world(
        seed, left_config, released_block=released
    )
    right_world = v35.generate_world(
        seed, right_config, released_block=released
    )
    return {
        "seed": seed,
        "theme": theme,
        "left": _summary(left_world),
        "right": _summary(right_world),
    }


def run_pilot():
    params = json.loads(PARAMETERS.read_text())
    if params["status"] not in {
        "AMENDMENT_1_SMOKE_PASSED",
        "AMENDMENT_1_SMOKE_FAIL_RETAINED_PLAN_FIDELITY_CORRECTED",
    }:
        raise RuntimeError("Amendment-1 smoke must precede the pilot")
    recovery_rows = _trace_map(
        "stage0-amendment-1-pilot-recovery",
        [
            (seed, 64, REPAIRED_PILOT_BLOCK)
            for seed in range(3_521_000, 3_521_800)
        ],
        _worker_recovery,
    )
    assay_rows = _trace_map(
        "stage0-amendment-1-pilot-assays",
        _tasks(3_521_800, 3_522_999, REPAIRED_PILOT_BLOCK),
        _worker_pilot,
    )
    recovery = _recovery_metrics(recovery_rows)
    estimands = _pilot_estimands(assay_rows)
    failures = _attainable(estimands)
    if failures:
        params["status"] = "STOPPED_AT_STAGE0_AMENDMENT_1_PILOT"
        PARAMETERS.write_text(json.dumps(params, indent=2, sort_keys=True) + "\n")
        _write_json("stage0-amendment-1-pilot.json", {
            "verdict": "STOP_UNATTAINABLE",
            "recovery": recovery,
            "estimands": estimands,
            "failures": failures,
            "barred_block": list(REPAIRED_PILOT_BLOCK),
        })
        return False
    nonzero = {
        f"{theme}:{name}": metric["mean"]
        for theme, values in estimands.items()
        for name, metric in values.items()
        if name not in {
            "scientific_posterior_identity_error",
            "dormant_influence_error",
        }
    }
    criteria = {
        "edge_accuracy_min": 0.9 * recovery["minimum_edge_accuracy"],
        "active_count_accuracy_min": 0.9 * recovery["active_count_accuracy"],
        "program_accuracy_min": 0.9 * recovery["program_accuracy"],
        "topology_accuracy_min": 0.9 * recovery["topology_accuracy"],
        "partner_accuracy_min": 0.9 * recovery["partner_accuracy"],
        "coverage_min": 0.9 * recovery["coverage"],
        "ece_max": recovery["ece"] + 0.03,
        "effect_minima": {
            name: 0.5 * value for name, value in nonzero.items()
        },
        "exact_identity_tolerance": TOLERANCE,
        "equivalence_rope": 0.01,
    }
    params["criteria"] = criteria
    params["status"] = "FROZEN_AFTER_ATTAINABILITY_PILOT"
    params["pilot_summary_sha256"] = hashlib.sha256(
        _canonical({"recovery": recovery, "estimands": estimands})
    ).hexdigest()
    PARAMETERS.write_text(json.dumps(params, indent=2, sort_keys=True) + "\n")
    _write_json("stage0-amendment-1-pilot.json", {
        "verdict": "DESCRIPTIVE_ATTAINABILITY_PASS",
        "barred_block": list(REPAIRED_PILOT_BLOCK),
        "recovery": recovery,
        "estimands": estimands,
        "frozen_criteria": criteria,
    })
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "step", choices=("gate1", "preflight", "retro", "smoke", "pilot")
    )
    args = parser.parse_args()
    if args.step == "gate1":
        passed = run_gate1()
    elif args.step == "preflight":
        passed = run_amendment_preflight()
    elif args.step == "retro":
        passed = run_retro_audits()
    elif args.step == "smoke":
        passed = run_smoke()
    else:
        passed = run_pilot()
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
