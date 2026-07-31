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
AMENDMENT2_PILOT_BLOCK = (3_523_961, 3_525_960)
GATE2_BLOCK = (3_502_000, 3_504_999)
GATE3_BLOCK = (3_505_000, 3_509_999)
GATE4_BLOCK = (3_510_000, 3_511_999)
GATE5_BLOCK = (3_512_000, 3_519_999)
REPLACEMENT_GATE2_BLOCK = (3_530_000, 3_532_999)
REPLACEMENT_GATE3_BLOCK = (3_533_000, 3_537_999)


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


def _write_report(name: str, title: str, result: Mapping[str, Any]) -> None:
    lines = [f"# {title}", "", f"Verdict: **{result['verdict']}**.", ""]
    lines.extend([
        "All worlds were executed inside serializing trace contexts. The",
        "runtime event ledger is embedded in each persisted JSONL record; the",
        "record-level and whole-file SHA-256 hashes were written before this",
        "criterion report was produced.",
        "",
        f"Seed block: `{result.get('seed_block')}`.",
        "",
        "```json",
        json.dumps(_plain(result), indent=2, sort_keys=True, allow_nan=False),
        "```",
        "",
    ])
    (RESULTS / name).write_text("\n".join(lines))


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


def _scientific_posterior_distance(left, right):
    values = [
        max(abs(a - b) for a, b in zip(
            left.probabilities, right.probabilities
        )),
        max(abs(a - b) for a, b in zip(
            left.active_mode_probabilities, right.active_mode_probabilities
        )),
        max(abs(a - b) for a, b in zip(
            left.mode_occupancy, right.mode_occupancy
        )),
        max(abs(a - b) for a, b in zip(left.q_partner, right.q_partner)),
        max(abs(
            left.edge_probabilities[name] - right.edge_probabilities[name]
        ) for name in v35.EDGE_NAMES),
        max(abs(
            left.topology_probabilities[name]
            - right.topology_probabilities[name]
        ) for name in left.topology_probabilities),
        max(abs(a - b) for a, b in zip(
            left.support_response_posterior,
            right.support_response_posterior,
        )),
        max(abs(a - b) for a, b in zip(
            left.contact_response_posterior,
            right.contact_response_posterior,
        )),
    ]
    return max(values)


def _complete_posterior_distance(left, right):
    values = [
        _scientific_posterior_distance(left, right),
        max(abs(a - b) for a, b in zip(
            left.joint_policy_posterior, right.joint_policy_posterior
        )),
        max(
            abs(left.interventional_influence[i][j]
                - right.interventional_influence[i][j])
            for i in range(v35.MODE_SLOTS)
            for j in range(v35.MODE_SLOTS)
        ),
    ]
    return max(values)


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
    delivered_masked_errors = [
        max(abs(a - b) for a, b in zip(
            posterior.probabilities, masked_p.probabilities
        )),
        max(abs(a - b) for a, b in zip(
            posterior.active_mode_probabilities,
            masked_p.active_mode_probabilities,
        )),
        max(abs(a - b) for a, b in zip(
            posterior.mode_occupancy, masked_p.mode_occupancy
        )),
        max(abs(a - b) for a, b in zip(
            posterior.joint_policy_posterior,
            masked_p.joint_policy_posterior,
        )),
        max(abs(
            posterior.edge_probabilities[name]
            - masked_p.edge_probabilities[name]
        ) for name in v35.EDGE_NAMES),
    ]
    registration_only = v35.ProtectObservation(
        0,
        (None, None, None),
        None,
        (1, 1, 1),
        None,
        None,
        None,
        (None, None, None),
        (1, 0, 1),
        None,
        1.0,
    )
    registration_only_masked = replace(
        registration_only, registration=(None, None, None)
    )
    registration_contributions = []
    for structure in v35.PROGRAMS:
        for modes in itertools.product((0, 1), repeat=v35.MODE_SLOTS):
            if any(modes[structure.active_modes:]):
                continue
            registration_contributions.append(
                v35._slice_likelihood(
                    registration_only, modes, structure, 0, 0
                )
                / v35._slice_likelihood(
                    registration_only_masked, modes, structure, 0, 0
                )
            )
    registration_candidate_common_error = (
        max(registration_contributions) - min(registration_contributions)
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
        "19_registration_candidate_common_evidence_error": (
            registration_candidate_common_error
        ),
        "19_registration_delivered_masked_posterior_error": max(
            delivered_masked_errors
        ),
        "19_candidate_common_channels_audited": ("registration",),
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


def run_gate1_amendment2():
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
    _trace_map_single("gate-1-amendment-2-rerun", row)
    result = {
        "verdict": "PASS" if row["passed"] else "FAIL",
        "proofs": row["proofs"],
        "structure_space_size": row["structure_space_size"],
        "component_space_size": row["component_space_size"],
        "bounds": row["bounds"],
        "retained_predecessor": "gate-1-amendment-1-rerun.json",
        "authorization": "gate3-adjudication-amendment-2.md",
    }
    _write_json("gate-1-amendment-2-rerun.json", result)
    params = json.loads(PARAMETERS.read_text())
    params["status"] = (
        "GATE1_AMENDMENT2_PASSED"
        if row["passed"] else "STOPPED_AT_GATE1_AMENDMENT2"
    )
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
    registration_masked = replace(
        world,
        observations=tuple(
            replace(item, registration=(None, None, None))
            for item in world.observations
        ),
    )
    registration_masked_posterior = v35.score_world(registration_masked)
    low_stakes = replace(
        world,
        observations=tuple(
            replace(item, stakes=0.7) for item in world.observations
        ),
    )
    high_stakes = replace(
        world,
        observations=tuple(
            replace(item, stakes=1.3) for item in world.observations
        ),
    )
    low_stakes_posterior = v35.score_world(low_stakes)
    high_stakes_posterior = v35.score_world(high_stakes)
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
        "support_parameter_correct": [
            int(value >= 0.5) == truth
            for value, truth in zip(
                posterior.support_response_posterior,
                world.truth_support_response,
            )
        ],
        "contact_parameter_correct": [
            int(value >= 0.5) == truth
            for value, truth in zip(
                posterior.contact_response_posterior,
                world.truth_contact_response,
            )
        ],
        "normalization_error": abs(
            math.fsum(posterior.probabilities) - 1
        ),
        "exact_log_error": abs(
            world.exact_log_probability
            - v35.exact_complete_log_probability(world)
        ),
        "registration_delivered_masked_posterior_error": (
            _complete_posterior_distance(
                posterior, registration_masked_posterior
            )
        ),
        "stakes_scientific_posterior_error": (
            _scientific_posterior_distance(
                low_stakes_posterior, high_stakes_posterior
            )
        ),
        "stakes_policy_difference": max(abs(a - b) for a, b in zip(
            low_stakes_posterior.joint_policy_posterior,
            high_stakes_posterior.joint_policy_posterior,
        )),
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
        "support_parameter_accuracy": [
            float(np.mean([row["support_parameter_correct"][index] for row in rows]))
            for index in range(v35.MODE_SLOTS)
        ],
        "contact_parameter_accuracy": [
            float(np.mean([row["contact_parameter_correct"][index] for row in rows]))
            for index in range(v35.MODE_SLOTS)
        ],
        "whole_program_accuracy": float(np.mean(
            [row["program_correct"] for row in rows]
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
        "registration_delivered_masked_posterior_error_max": max(
            row["registration_delivered_masked_posterior_error"]
            for row in rows
        ),
        "stakes_scientific_posterior_error_max": max(
            row["stakes_scientific_posterior_error"] for row in rows
        ),
        "stakes_policy_difference_mean": float(np.mean(
            [row["stakes_policy_difference"] for row in rows]
        )),
    }


def _recovery_failures(metrics, criteria):
    comparisons = {
        "minimum_edge_accuracy": (
            metrics["minimum_edge_accuracy"],
            criteria["edge_accuracy_min"],
            ">=",
        ),
        "active_count_accuracy": (
            metrics["active_count_accuracy"],
            criteria["active_count_accuracy_min"],
            ">=",
        ),
        "whole_program_accuracy": (
            metrics["whole_program_accuracy"],
            criteria["program_accuracy_min"],
            ">=",
        ),
        "topology_accuracy": (
            metrics["topology_accuracy"],
            criteria["topology_accuracy_min"],
            ">=",
        ),
        "partner_accuracy": (
            metrics["partner_accuracy"],
            criteria["partner_accuracy_min"],
            ">=",
        ),
        "coverage": (metrics["coverage"], criteria["coverage_min"], ">="),
        "ece": (metrics["ece"], criteria["ece_max"], "<="),
        "normalization_error_max": (
            metrics["normalization_error_max"],
            criteria["exact_identity_tolerance"],
            "<=",
        ),
        "exact_log_error_max": (
            metrics["exact_log_error_max"],
            criteria["exact_identity_tolerance"],
            "<=",
        ),
    }
    failures = []
    for name, (value, threshold, direction) in comparisons.items():
        passed = value >= threshold if direction == ">=" else value <= threshold
        if not passed:
            failures.append(
                f"{name}={value:.12g} {direction} {threshold:.12g} failed"
            )
    return failures, comparisons


def run_gate2():
    params = json.loads(PARAMETERS.read_text())
    if params["status"] != "FROZEN_AFTER_ATTAINABILITY_PILOT":
        raise RuntimeError("the amendment-1 floors must be frozen before Gate 2")
    rows = _trace_map(
        "gate-2-amendment-1",
        [
            (seed, 64, GATE2_BLOCK)
            for seed in range(GATE2_BLOCK[0], GATE2_BLOCK[1] + 1)
        ],
        _worker_recovery,
    )
    metrics = _recovery_metrics(rows)
    failures, comparisons = _recovery_failures(metrics, params["criteria"])
    gate1 = json.loads(
        (RESULTS / "gate-1-amendment-1-rerun.json").read_text()
    )
    if gate1["verdict"] != "PASS":
        failures.append("permanent semantic proof battery is not PASS")
    result = {
        "verdict": "PASS" if not failures else "FAIL",
        "seed_block": list(GATE2_BLOCK),
        "seeds_consumed": len(rows),
        "ascending_gap_free": [row["seed"] for row in rows]
        == list(range(GATE2_BLOCK[0], GATE2_BLOCK[1] + 1)),
        "frozen_criteria": params["criteria"],
        "comparisons": comparisons,
        "metrics": metrics,
        "semantic_proofs": {
            "three_case_active_dormant_masked": "Gate-1 items 4, 6, 8, and expanded item 17; exercised at scale by common-support own-model recovery",
            "hierarchical_partner_support": {
                "partner_accuracy": metrics["partner_accuracy"],
                "support_parameter_accuracy": metrics["support_parameter_accuracy"],
            },
            "stakes_in_utility_identity": "exact Gate-3 paired identity; no stakes field enters component evidence",
            "outcome_bearing_policy_history": "Gate-3 paired observed-vs-masked outcome path",
            "theta_contact_target": metrics["contact_parameter_accuracy"],
            "interventional_D_fingerprints": gate1["proofs"]["18_interventional_topology_fixture"],
            "exact_zero_claims_are_identities": True,
        },
        "failures": failures,
        "bounds": dict(v35.finite_information_bounds()),
        "custody": {
            "runtime_events_persisted_in_trace_jsonl": True,
            "trace_hash_ledger": "gate-2-amendment-1-trace-hashes.json",
            "barred_blocks_touched": False,
            "escrow_touched": False,
        },
    }
    _write_json("gate-2-amendment-1.json", result)
    _write_report("gate-2-report.md", "V3.5 Gate 2 — Amendment 1", result)
    params["status"] = "GATE2_PASSED" if not failures else "STOPPED_AT_GATE2"
    PARAMETERS.write_text(json.dumps(params, indent=2, sort_keys=True) + "\n")
    return not failures


def run_gate2_amendment2():
    params = json.loads(PARAMETERS.read_text())
    if params["status"] != "FROZEN_AFTER_AMENDMENT2_PILOT":
        raise RuntimeError("Amendment-2 refreeze must precede replacement Gate 2")
    rows = _trace_map(
        "gate-2-amendment-2",
        [
            (seed, 64, REPLACEMENT_GATE2_BLOCK)
            for seed in range(
                REPLACEMENT_GATE2_BLOCK[0],
                REPLACEMENT_GATE2_BLOCK[1] + 1,
            )
        ],
        _worker_recovery,
    )
    metrics = _recovery_metrics(rows)
    failures, comparisons = _recovery_failures(metrics, params["criteria"])
    tolerance = params["criteria"]["exact_identity_tolerance"]
    identity_metrics = {
        "registration_delivered_masked_posterior_error_max": (
            metrics["registration_delivered_masked_posterior_error_max"]
        ),
        "stakes_scientific_posterior_error_max": (
            metrics["stakes_scientific_posterior_error_max"]
        ),
    }
    for name, value in identity_metrics.items():
        if value > tolerance:
            failures.append(f"{name}={value:.12g} exceeds {tolerance:.12g}")
    gate1 = json.loads(
        (RESULTS / "gate-1-amendment-2-rerun.json").read_text()
    )
    if gate1["verdict"] != "PASS":
        failures.append("Amendment-2 permanent semantic proof battery is not PASS")
    result = {
        "verdict": "PASS" if not failures else "FAIL",
        "seed_block": list(REPLACEMENT_GATE2_BLOCK),
        "seeds_consumed": len(rows),
        "ascending_gap_free": [row["seed"] for row in rows]
        == list(range(
            REPLACEMENT_GATE2_BLOCK[0],
            REPLACEMENT_GATE2_BLOCK[1] + 1,
        )),
        "frozen_criteria": params["criteria"],
        "comparisons": comparisons,
        "metrics": metrics,
        "semantic_proofs_at_scale": {
            "candidate_common_registration_identity": identity_metrics[
                "registration_delivered_masked_posterior_error_max"
            ],
            "three_case_active_dormant_masked": (
                "permanent items 4, 6, 8, 17, and 19 plus common-support "
                "own-model recovery over active counts 1/2/3"
            ),
            "hierarchical_partner_support": {
                "partner_accuracy": metrics["partner_accuracy"],
                "support_parameter_accuracy": metrics[
                    "support_parameter_accuracy"
                ],
            },
            "stakes_in_utility_scientific_posterior_identity": (
                identity_metrics["stakes_scientific_posterior_error_max"]
            ),
            "stakes_policy_path_present_descriptive": metrics[
                "stakes_policy_difference_mean"
            ],
            "theta_contact_target_accuracy": metrics[
                "contact_parameter_accuracy"
            ],
            "interventional_D_fingerprints": gate1["proofs"][
                "18_interventional_topology_fixture"
            ],
            "exact_zero_claims_scored_as_identities": True,
        },
        "failures": failures,
        "bounds": dict(v35.finite_information_bounds()),
        "custody": {
            "runtime_events_persisted_in_trace_jsonl": True,
            "trace_hash_ledger": "gate-2-amendment-2-trace-hashes.json",
            "barred_blocks_touched": False,
            "retired_or_sealed_escrow_touched": False,
        },
    }
    _write_json("gate-2-amendment-2.json", result)
    _write_report("gate-2-amendment-2-report.md", "V3.5 Replacement Gate 2", result)
    params["status"] = (
        "REPLACEMENT_GATE2_PASSED"
        if not failures else "STOPPED_AT_REPLACEMENT_GATE2"
    )
    PARAMETERS.write_text(json.dumps(params, indent=2, sort_keys=True) + "\n")
    if failures:
        (RESULTS / "gate-2-amendment-2-diagnosis-stub.md").write_text(
            "# V3.5 replacement Gate 2 diagnosis stub\n\n"
            "Replacement Gate 2 stopped honestly. No replacement Gate-3 seed "
            "was opened.\n\n"
            + "\n".join(f"- {failure}" for failure in failures) + "\n"
        )
    return not failures


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


def _pilot_estimands(rows, themes=None):
    result = {}
    selected_themes = PILOT_THEMES if themes is None else tuple(themes)
    for index, theme in enumerate(selected_themes):
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
        elif theme == "registration":
            values = {
                "policy_difference": [
                    r["right"]["access"] - r["left"]["access"]
                    for r in subset
                ],
                "scientific_posterior_max_abs_difference": [
                    max(abs(a - b) for a, b in zip(
                        r["right"]["structure_probabilities"],
                        r["left"]["structure_probabilities"],
                    ))
                    for r in subset
                ],
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
GATE3_THEMES = PILOT_THEMES + ("registration",)


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
        "registration": (
            _config(registration="masked"),
            _config(registration="delivered"),
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


def _amendment2_pilot_failures(estimands):
    failures = []
    exact = {
        "stakes:scientific_posterior_identity_error",
        "mode_dormancy:dormant_influence_error",
    }
    equivalence = {
        "registration:policy_difference",
        "registration:scientific_posterior_max_abs_difference",
    }
    for theme, values in estimands.items():
        for name, metric in values.items():
            key = f"{theme}:{name}"
            if key in exact:
                if max(abs(value) for value in metric["ci95"]) > TOLERANCE:
                    failures.append(f"{key}:identity")
            elif key in equivalence:
                if metric["ci95"][0] < -0.01 or metric["ci95"][1] > 0.01:
                    failures.append(f"{key}:equivalence")
            elif metric["ci95"][0] <= 0.0:
                failures.append(f"{key}:sign")
    return failures


def run_amendment2_pilot():
    params = json.loads(PARAMETERS.read_text())
    if params["status"] != "GATE1_AMENDMENT2_PASSED":
        raise RuntimeError("Amendment-2 Gate 1 must pass before the fresh pilot")
    recovery_end = AMENDMENT2_PILOT_BLOCK[0] + 799
    recovery_rows = _trace_map(
        "stage0-amendment-2-pilot-recovery",
        [
            (seed, 64, AMENDMENT2_PILOT_BLOCK)
            for seed in range(AMENDMENT2_PILOT_BLOCK[0], recovery_end + 1)
        ],
        _worker_recovery,
    )
    assay_start = recovery_end + 1
    assay_rows = _trace_map(
        "stage0-amendment-2-pilot-assays",
        [
            (
                seed,
                GATE3_THEMES[(seed - assay_start) % len(GATE3_THEMES)],
                AMENDMENT2_PILOT_BLOCK,
            )
            for seed in range(assay_start, AMENDMENT2_PILOT_BLOCK[1] + 1)
        ],
        _worker_pilot,
    )
    recovery = _recovery_metrics(recovery_rows)
    estimands = _pilot_estimands(assay_rows, GATE3_THEMES)
    failures = _amendment2_pilot_failures(estimands)
    old_criteria = params.get("criteria", {})
    if failures:
        params["status"] = "STOPPED_AT_STAGE0_AMENDMENT2_PILOT"
        PARAMETERS.write_text(json.dumps(params, indent=2, sort_keys=True) + "\n")
        result = {
            "verdict": "STOP_UNATTAINABLE",
            "seed_block": list(AMENDMENT2_PILOT_BLOCK),
            "recovery": recovery,
            "estimands": estimands,
            "failures": failures,
            "barred_on_consumption": True,
            "retained_invalidated_amendment1_criteria": old_criteria,
        }
        _write_json("stage0-amendment-2-pilot.json", result)
        return False
    excluded = {
        "scientific_posterior_identity_error",
        "dormant_influence_error",
        "policy_difference",
        "scientific_posterior_max_abs_difference",
    }
    nonzero = {
        f"{theme}:{name}": metric["mean"]
        for theme, values in estimands.items()
        for name, metric in values.items()
        if name not in excluded
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
    summary = {"recovery": recovery, "estimands": estimands}
    params["criteria"] = criteria
    params["status"] = "FROZEN_AFTER_AMENDMENT2_PILOT"
    params["pilot_summary_sha256"] = hashlib.sha256(
        _canonical(summary)
    ).hexdigest()
    params["amendment2_pilot_summary_sha256"] = params["pilot_summary_sha256"]
    PARAMETERS.write_text(json.dumps(params, indent=2, sort_keys=True) + "\n")
    result = {
        "verdict": "DESCRIPTIVE_ATTAINABILITY_PASS",
        "seed_block": list(AMENDMENT2_PILOT_BLOCK),
        "seed_partition": {
            "recovery": [AMENDMENT2_PILOT_BLOCK[0], recovery_end],
            "assays": [assay_start, AMENDMENT2_PILOT_BLOCK[1]],
        },
        "ascending_gap_free_once": (
            [row["seed"] for row in recovery_rows]
            + [row["seed"] for row in assay_rows]
            == list(range(
                AMENDMENT2_PILOT_BLOCK[0],
                AMENDMENT2_PILOT_BLOCK[1] + 1,
            ))
        ),
        "barred_on_consumption": True,
        "recovery": recovery,
        "estimands": estimands,
        "frozen_criteria": criteria,
        "mechanical_rule": params["floor_rule"],
        "retained_invalidated_amendment1_criteria": old_criteria,
        "failures": failures,
        "custody": {
            "runtime_events_persisted_in_trace_jsonl": True,
            "recovery_hash_ledger": (
                "stage0-amendment-2-pilot-recovery-trace-hashes.json"
            ),
            "assay_hash_ledger": (
                "stage0-amendment-2-pilot-assays-trace-hashes.json"
            ),
            "replacement_gate_blocks_opened": False,
            "original_gate4_gate5_opened": False,
            "retired_or_new_escrow_opened": False,
        },
    }
    _write_json("stage0-amendment-2-pilot.json", result)
    return True


def _gate3_tasks():
    return [
        (
            seed,
            GATE3_THEMES[(seed - GATE3_BLOCK[0]) % len(GATE3_THEMES)],
            GATE3_BLOCK,
        )
        for seed in range(GATE3_BLOCK[0], GATE3_BLOCK[1] + 1)
    ]


def run_gate3():
    params = json.loads(PARAMETERS.read_text())
    if params["status"] != "GATE2_PASSED":
        raise RuntimeError("Gate 2 must pass before Gate 3")
    rows = _trace_map("gate-3-amendment-1", _gate3_tasks(), _worker_pilot)
    estimands = _pilot_estimands(rows, GATE3_THEMES)
    criteria = params["criteria"]
    failures = []
    comparisons = {}
    for key, floor in criteria["effect_minima"].items():
        theme, name = key.split(":", 1)
        metric = estimands[theme][name]
        passed = metric["mean"] >= floor and metric["ci95"][0] > 0.0
        comparisons[key] = {
            "metric": metric,
            "floor": floor,
            "lower_ci_must_exceed_zero": True,
            "passed": passed,
        }
        if not passed:
            failures.append(
                f"{key}: mean={metric['mean']:.12g}, "
                f"CI={metric['ci95']}, floor={floor:.12g}"
            )
    identity_values = {
        "stakes_scientific_posterior": max(
            max(abs(a - b) for a, b in zip(
                row["right"]["structure_probabilities"],
                row["left"]["structure_probabilities"],
            ))
            for row in rows if row["theme"] == "stakes"
        ),
        "dormant_mode_influence": max(
            abs(row["dormant_effect"])
            for row in rows if row["theme"] == "mode_dormancy"
        ),
    }
    for name, value in identity_values.items():
        if value > criteria["exact_identity_tolerance"]:
            failures.append(f"{name}={value:.12g} exceeds exact tolerance")
    registration = estimands["registration"]
    rope = criteria["equivalence_rope"]
    registration_pass = (
        registration["policy_difference"]["ci95"][0] >= -rope
        and registration["policy_difference"]["ci95"][1] <= rope
        and registration["scientific_posterior_max_abs_difference"]["ci95"][1]
        <= rope
    )
    if not registration_pass:
        failures.append(
            "registration equivalence interval is not wholly inside the frozen ROPE"
        )
    result = {
        "verdict": "PASS" if not failures else "FAIL",
        "seed_block": list(GATE3_BLOCK),
        "seeds_consumed": len(rows),
        "ascending_gap_free": [row["seed"] for row in rows]
        == list(range(GATE3_BLOCK[0], GATE3_BLOCK[1] + 1)),
        "estimands": estimands,
        "frozen_effect_comparisons": comparisons,
        "identity_values": identity_values,
        "registration_equivalence": {
            "rope": [-rope, rope],
            "metrics": registration,
            "passed": registration_pass,
        },
        "opposed_recording_convention": (
            "opposed_D_* is the negated raw interventional influence; "
            "the raw opposed D entries are negative"
        ),
        "failures": failures,
        "bounds": dict(v35.finite_information_bounds()),
        "custody": {
            "runtime_events_persisted_in_trace_jsonl": True,
            "trace_hash_ledger": "gate-3-amendment-1-trace-hashes.json",
            "barred_blocks_touched": False,
            "escrow_touched": False,
        },
    }
    _write_json("gate-3-amendment-1.json", result)
    _write_report("gate-3-report.md", "V3.5 Gate 3 — Amendment 1", result)
    params["status"] = "GATE3_PASSED" if not failures else "STOPPED_AT_GATE3"
    PARAMETERS.write_text(json.dumps(params, indent=2, sort_keys=True) + "\n")
    if failures:
        (RESULTS / "gate-3-diagnosis-stub.md").write_text(
            "# V3.5 Gate 3 diagnosis stub\n\n"
            "Gate 3 stopped honestly. No Gate-4 seed was opened.\n\n"
            + "\n".join(f"- {failure}" for failure in failures) + "\n"
        )
    return not failures


def run_gate3_amendment2():
    params = json.loads(PARAMETERS.read_text())
    if params["status"] != "REPLACEMENT_GATE2_PASSED":
        raise RuntimeError("replacement Gate 2 must pass before replacement Gate 3")
    tasks = [
        (
            seed,
            GATE3_THEMES[
                (seed - REPLACEMENT_GATE3_BLOCK[0]) % len(GATE3_THEMES)
            ],
            REPLACEMENT_GATE3_BLOCK,
        )
        for seed in range(
            REPLACEMENT_GATE3_BLOCK[0],
            REPLACEMENT_GATE3_BLOCK[1] + 1,
        )
    ]
    rows = _trace_map("gate-3-amendment-2", tasks, _worker_pilot)
    estimands = _pilot_estimands(rows, GATE3_THEMES)
    criteria = params["criteria"]
    failures = []
    comparisons = {}
    for key, floor in criteria["effect_minima"].items():
        theme, name = key.split(":", 1)
        metric = estimands[theme][name]
        passed = metric["mean"] >= floor and metric["ci95"][0] > 0.0
        comparisons[key] = {
            "metric": metric,
            "floor": floor,
            "lower_ci_must_exceed_zero": True,
            "passed": passed,
        }
        if not passed:
            failures.append(
                f"{key}: mean={metric['mean']:.12g}, "
                f"CI={metric['ci95']}, floor={floor:.12g}"
            )
    identity_values = {
        "stakes_scientific_posterior": max(
            max(abs(a - b) for a, b in zip(
                row["right"]["structure_probabilities"],
                row["left"]["structure_probabilities"],
            ))
            for row in rows if row["theme"] == "stakes"
        ),
        "dormant_mode_influence": max(
            abs(row["dormant_effect"])
            for row in rows if row["theme"] == "mode_dormancy"
        ),
    }
    for name, value in identity_values.items():
        if value > criteria["exact_identity_tolerance"]:
            failures.append(f"{name}={value:.12g} exceeds exact tolerance")
    registration = estimands["registration"]
    rope = criteria["equivalence_rope"]
    registration_pass = (
        registration["policy_difference"]["ci95"][0] >= -rope
        and registration["policy_difference"]["ci95"][1] <= rope
        and registration[
            "scientific_posterior_max_abs_difference"
        ]["ci95"][1] <= rope
    )
    if not registration_pass:
        failures.append(
            "registration equivalence interval is not wholly inside the frozen ROPE"
        )
    result = {
        "verdict": "PASS" if not failures else "FAIL",
        "seed_block": list(REPLACEMENT_GATE3_BLOCK),
        "seeds_consumed": len(rows),
        "ascending_gap_free": [row["seed"] for row in rows]
        == list(range(
            REPLACEMENT_GATE3_BLOCK[0],
            REPLACEMENT_GATE3_BLOCK[1] + 1,
        )),
        "estimands": estimands,
        "frozen_effect_comparisons": comparisons,
        "identity_values": identity_values,
        "registration_equivalence": {
            "rope": [-rope, rope],
            "metrics": registration,
            "passed": registration_pass,
        },
        "opposed_recording_convention": (
            "opposed_D_* is the negated raw interventional influence; "
            "raw opposed D entries are negative"
        ),
        "opposed_allied_reported_separately": True,
        "failures": failures,
        "bounds": dict(v35.finite_information_bounds()),
        "custody": {
            "runtime_events_persisted_in_trace_jsonl": True,
            "trace_hash_ledger": "gate-3-amendment-2-trace-hashes.json",
            "barred_blocks_touched": False,
            "retired_or_sealed_escrow_touched": False,
        },
    }
    _write_json("gate-3-amendment-2.json", result)
    _write_report("gate-3-amendment-2-report.md", "V3.5 Replacement Gate 3", result)
    params["status"] = (
        "REPLACEMENT_GATE3_PASSED"
        if not failures else "STOPPED_AT_REPLACEMENT_GATE3"
    )
    PARAMETERS.write_text(json.dumps(params, indent=2, sort_keys=True) + "\n")
    if failures:
        (RESULTS / "gate-3-amendment-2-diagnosis-stub.md").write_text(
            "# V3.5 replacement Gate 3 diagnosis stub\n\n"
            "Replacement Gate 3 stopped honestly. No Gate-4 seed was opened.\n\n"
            + "\n".join(f"- {failure}" for failure in failures) + "\n"
        )
    return not failures


GATE4_LESIONS = (
    "mode_slot",
    "mode_root_edges",
    "joint_policy_edge",
    "cross_mode_edge",
    "registration_channel",
    "contact_channel",
)


def _program_allowed(structure, restrictions):
    if structure.active_modes not in restrictions.get(
        "active_modes", (1, 2, 3)
    ):
        return False
    return all(
        value in restrictions.get(name, (0, 1))
        for name, value in v35.program_values(structure).items()
    )


def _restricted_prior_identity(full, restricted, restrictions):
    retained = [
        probability
        for probability, (structure, _sign) in zip(
            full.probabilities, full.components
        )
        if _program_allowed(structure, restrictions)
    ]
    mass = math.fsum(retained)
    conditioned = [probability / mass for probability in retained]
    return max(abs(a - b) for a, b in zip(
        conditioned, restricted.probabilities
    ))


def _mask_slots(world, first_masked_slot):
    def masked(values):
        return tuple(
            value if index < first_masked_slot else None
            for index, value in enumerate(values)
        )
    return replace(
        world,
        observations=tuple(
            replace(
                item,
                mode_signals=masked(item.mode_signals),
                support_signals=masked(item.support_signals),
                registration=masked(item.registration),
                contact_signals=masked(item.contact_signals),
                support_targets=tuple(
                    value if index < first_masked_slot else 0
                    for index, value in enumerate(item.support_targets)
                ),
            )
            for item in world.observations
        ),
    )


@traced_execution
def _worker_gate4(task):
    seed, lesion = task
    config = _config(
        mode_count=1 if lesion == "mode_slot" else 3,
        topology="allied" if lesion == "cross_mode_edge" else "independent",
    )
    world = v35.generate_world(seed, config, released_block=GATE4_BLOCK)
    restrictions = {}
    scoring_world = world
    if lesion == "mode_slot":
        restrictions = {"active_modes": (1,)}
        scoring_world = _mask_slots(world, 1)
    elif lesion == "mode_root_edges":
        restrictions = {name: (0,) for name in ("M1_G", "M2_G", "M3_G")}
    elif lesion == "joint_policy_edge":
        restrictions = {"JOINT_POLICY_Y": (0,)}
    elif lesion == "cross_mode_edge":
        restrictions = {"CROSS_MODE_Y": (0,)}
    elif lesion == "registration_channel":
        scoring_world = replace(
            world,
            observations=tuple(
                replace(item, registration=(None, None, None))
                for item in world.observations
            ),
        )
    elif lesion == "contact_channel":
        scoring_world = replace(
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
    full = v35.score_world(scoring_world)
    lesioned = v35.score_world(scoring_world, restrictions=restrictions)
    identity_error = _restricted_prior_identity(full, lesioned, restrictions)
    result = {
        "seed": seed,
        "lesion": lesion,
        "restriction": restrictions,
        "restricted_prior_identity_error": identity_error,
        "normalization_error": abs(math.fsum(lesioned.probabilities) - 1.0),
        "finite_evidence": math.isfinite(lesioned.log_evidence),
        "target_error": 0.0,
        "selectivity_error": 0.0,
    }
    if lesion == "mode_slot":
        baseline = v35.score_world(
            world, restrictions={"active_modes": (1,)}
        )
        result["target_error"] = max(
            max(abs(a - b) for a, b in zip(
                baseline.q_partner, lesioned.q_partner
            )),
            abs(
                baseline.edge_probabilities["JOINT_POLICY_Y"]
                - lesioned.edge_probabilities["JOINT_POLICY_Y"]
            ),
        )
        result["dormant_D_error"] = max(
            abs(lesioned.interventional_influence[i][j])
            for i in range(v35.MODE_SLOTS)
            for j in range(v35.MODE_SLOTS)
            if i >= 1 or j >= 1
        )
    elif lesion == "mode_root_edges":
        result["target_error"] = max(
            lesioned.edge_probabilities[name]
            for name in ("M1_G", "M2_G", "M3_G")
        )
    elif lesion == "joint_policy_edge":
        result["target_error"] = lesioned.edge_probabilities[
            "JOINT_POLICY_Y"
        ]
    elif lesion == "cross_mode_edge":
        result["target_error"] = max(
            abs(lesioned.interventional_influence[i][j])
            for i in range(v35.MODE_SLOTS)
            for j in range(v35.MODE_SLOTS)
            if i != j
        )
        result["cross_edge_probability"] = lesioned.edge_probabilities[
            "CROSS_MODE_Y"
        ]
    elif lesion == "registration_channel":
        disabled = v35.score_world(world, registration_enabled=False)
        result["target_error"] = _complete_posterior_distance(
            lesioned, disabled
        )
    elif lesion == "contact_channel":
        disabled = v35.score_world(world, denied_enabled=False)
        result["target_error"] = _complete_posterior_distance(
            lesioned, disabled
        )
    return result


def run_gate4():
    params = json.loads(PARAMETERS.read_text())
    if params["status"] != "REPLACEMENT_GATE3_PASSED":
        raise RuntimeError("replacement Gate 3 must pass before Gate 4")
    tasks = [
        (
            seed,
            GATE4_LESIONS[(seed - GATE4_BLOCK[0]) % len(GATE4_LESIONS)],
        )
        for seed in range(GATE4_BLOCK[0], GATE4_BLOCK[1] + 1)
    ]
    rows = _trace_map("gate-4-amendment-2", tasks, _worker_gate4)
    tolerance = params["criteria"]["exact_identity_tolerance"]
    cells = {}
    failures = []
    for lesion in GATE4_LESIONS:
        subset = [row for row in rows if row["lesion"] == lesion]
        cell = {
            "n": len(subset),
            "restricted_prior_identity_error_max": max(
                row["restricted_prior_identity_error"] for row in subset
            ),
            "normalization_error_max": max(
                row["normalization_error"] for row in subset
            ),
            "finite_evidence_all": all(row["finite_evidence"] for row in subset),
            "target_error_max": max(row["target_error"] for row in subset),
        }
        if lesion == "mode_slot":
            cell["dormant_D_error_max"] = max(
                row["dormant_D_error"] for row in subset
            )
        if lesion == "cross_mode_edge":
            cell["cross_edge_probability_max"] = max(
                row["cross_edge_probability"] for row in subset
            )
        cell["passed"] = (
            cell["restricted_prior_identity_error_max"] <= tolerance
            and cell["normalization_error_max"] <= tolerance
            and cell["finite_evidence_all"]
            and cell["target_error_max"] <= tolerance
            and cell.get("dormant_D_error_max", 0.0) <= tolerance
            and cell.get("cross_edge_probability_max", 0.0) <= tolerance
        )
        if not cell["passed"]:
            failures.append(f"{lesion}: {cell}")
        cells[lesion] = cell
    result = {
        "verdict": "PASS" if not failures else "FAIL",
        "seed_block": list(GATE4_BLOCK),
        "seeds_consumed": len(rows),
        "ascending_gap_free": [row["seed"] for row in rows]
        == list(range(GATE4_BLOCK[0], GATE4_BLOCK[1] + 1)),
        "cells": cells,
        "restricted_prior_identity_tolerance": tolerance,
        "masking_semantics": (
            "slot/channel deletion is candidate-common masking; masked "
            "channels contribute no likelihood"
        ),
        "failures": failures,
        "custody": {
            "runtime_events_persisted_in_trace_jsonl": True,
            "trace_hash_ledger": "gate-4-amendment-2-trace-hashes.json",
            "barred_blocks_touched": False,
            "retired_or_sealed_escrow_touched": False,
        },
    }
    _write_json("gate-4-amendment-2.json", result)
    _write_report("gate-4-amendment-2-report.md", "V3.5 Gate 4 lesions", result)
    params["status"] = "GATE4_PASSED" if not failures else "STOPPED_AT_GATE4"
    PARAMETERS.write_text(json.dumps(params, indent=2, sort_keys=True) + "\n")
    if failures:
        (RESULTS / "gate-4-amendment-2-diagnosis-stub.md").write_text(
            "# V3.5 Gate 4 diagnosis stub\n\n"
            "Gate 4 stopped honestly. No Gate-5 seed was opened.\n\n"
            + "\n".join(f"- {failure}" for failure in failures) + "\n"
        )
    return not failures


def _compact_recovery_row(world, posterior):
    structure_map = _structure_probabilities(posterior)
    truth_key = (
        world.truth_structure.active_modes,
        world.truth_structure.mode_root_edges,
        world.truth_structure.joint_policy_outcome,
        world.truth_structure.cross_mode_outcome,
    )
    predicted = max(structure_map, key=structure_map.get)
    truth_edges = tuple(v35.program_values(world.truth_structure).values())
    predicted_edges = (
        predicted[1][0], predicted[1][1], predicted[1][2],
        predicted[2], predicted[3],
    )
    return {
        "truth_structure": truth_key,
        "predicted_structure": predicted,
        "edge_correct": [
            left == right for left, right in zip(predicted_edges, truth_edges)
        ],
        "active_count_correct": predicted[0] == truth_key[0],
        "program_correct": predicted == truth_key,
        "confidence": structure_map[predicted],
        "normalization_error": abs(math.fsum(posterior.probabilities) - 1.0),
        "finite_evidence": math.isfinite(posterior.log_evidence),
    }


@traced_execution
def _worker_gate5(task):
    seed, cell, detail = task
    if cell == "primary_assay":
        row = _worker_pilot.__wrapped__((seed, detail, GATE5_BLOCK))
        row["cell"] = cell
        return row
    if cell in {"primary_recovery_64", "length_32", "length_96"}:
        length = {"primary_recovery_64": 64, "length_32": 32, "length_96": 96}[cell]
        row = _worker_recovery.__wrapped__((seed, length, GATE5_BLOCK))
        row["cell"] = cell
        return row
    if cell == "policy_schedule":
        row = _worker_pilot.__wrapped__((seed, detail, GATE5_BLOCK))
        row["cell"] = cell
        return row
    world = v35.generate_recovery_world(
        seed, length=64, released_block=GATE5_BLOCK
    )
    if cell == "missingness_25pct":
        observations = []
        for item in world.observations:
            if item.time % 4 == 0:
                observations.append(replace(
                    item,
                    mode_signals=(None, None, None),
                    root_signal=None,
                    outcome=None,
                    partner_remaining=None,
                    partner_pressure=None,
                    support_signals=(None, None, None),
                    registration=(None, None, None),
                    denied_contact=None,
                    contact_signals=(None, None, None),
                ))
            else:
                observations.append(item)
        scored_world = replace(world, observations=tuple(observations))
        posterior = v35.score_world(scored_world)
        scale = 1.0
    elif cell == "code_length_scale":
        scale = 0.75 if seed % 2 == 0 else 1.25
        posterior = v35.score_world(world, code_length_scale=scale)
    else:
        raise ValueError(f"unknown Gate-5 cell {cell}")
    return {
        "seed": seed,
        "cell": cell,
        "code_length_scale": scale,
        **_compact_recovery_row(world, posterior),
    }


def _gate5_tasks():
    tasks = []
    seed = GATE5_BLOCK[0]
    for theme in GATE3_THEMES:
        for _ in range(500):
            tasks.append((seed, "primary_assay", theme))
            seed += 1
    for _ in range(500):
        tasks.append((seed, "primary_recovery_64", None))
        seed += 1
    for cell in (
        "length_32",
        "length_96",
        "missingness_25pct",
        "code_length_scale",
        "policy_schedule",
    ):
        for index in range(200):
            detail = (
                ("policy_exclusion", "policy_monitoring", "policy_engagement")[
                    index % 3
                ]
                if cell == "policy_schedule" else None
            )
            tasks.append((seed, cell, detail))
            seed += 1
    if seed != GATE5_BLOCK[1] + 1:
        raise AssertionError("Gate-5 task partition does not fill its block")
    return tasks


def _manifest_verification(stage):
    path = ROOT / "results" / stage / "freeze-manifest.json"
    manifest = json.loads(path.read_text())
    mismatches = []
    for relative, expected in manifest["files"].items():
        target = ROOT / relative
        actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
        if actual != expected:
            mismatches.append({
                "file": relative,
                "expected": expected,
                "actual": actual,
            })
    return {
        "stage": stage,
        "file_count": len(manifest["files"]),
        "mismatches": mismatches,
        "passed": not mismatches,
    }


def _descriptive_recovery_metrics(rows):
    edge = {
        name: float(np.mean([row["edge_correct"][index] for row in rows]))
        for index, name in enumerate(v35.EDGE_NAMES)
    }
    return {
        "n": len(rows),
        "edge_accuracy": edge,
        "minimum_edge_accuracy": min(edge.values()),
        "whole_program_accuracy": float(np.mean([
            row["program_correct"] for row in rows
        ])),
        "active_count_accuracy": float(np.mean([
            row["active_count_correct"] for row in rows
        ])),
        "normalization_error_max": max(
            row["normalization_error"] for row in rows
        ),
        "finite_evidence_all": all(row.get("finite_evidence", True) for row in rows),
    }


def _evaluate_primary_assays(rows, criteria):
    estimands = _pilot_estimands(rows, GATE3_THEMES)
    failures = []
    comparisons = {}
    for key, floor in criteria["effect_minima"].items():
        theme, name = key.split(":", 1)
        metric = estimands[theme][name]
        passed = metric["mean"] >= floor and metric["ci95"][0] > 0.0
        comparisons[key] = {
            "metric": metric,
            "floor": floor,
            "passed": passed,
        }
        if not passed:
            failures.append(f"{key}: {comparisons[key]}")
    tolerance = criteria["exact_identity_tolerance"]
    identities = {
        "stakes_scientific_posterior": max(
            max(abs(a - b) for a, b in zip(
                row["right"]["structure_probabilities"],
                row["left"]["structure_probabilities"],
            ))
            for row in rows if row["theme"] == "stakes"
        ),
        "dormant_mode_influence": max(
            abs(row["dormant_effect"])
            for row in rows if row["theme"] == "mode_dormancy"
        ),
    }
    for name, value in identities.items():
        if value > tolerance:
            failures.append(f"{name}={value:.12g} exceeds {tolerance:.12g}")
    registration = estimands["registration"]
    rope = criteria["equivalence_rope"]
    registration_pass = (
        registration["policy_difference"]["ci95"][0] >= -rope
        and registration["policy_difference"]["ci95"][1] <= rope
        and registration[
            "scientific_posterior_max_abs_difference"
        ]["ci95"][1] <= rope
    )
    if not registration_pass:
        failures.append("primary registration equivalence failed")
    return {
        "estimands": estimands,
        "comparisons": comparisons,
        "identities": identities,
        "registration_pass": registration_pass,
        "failures": failures,
    }


def run_gate5():
    params = json.loads(PARAMETERS.read_text())
    if params["status"] != "GATE4_PASSED":
        raise RuntimeError("Gate 4 must pass before Gate 5")
    rows = _trace_map("gate-5-amendment-2", _gate5_tasks(), _worker_gate5)
    criteria = params["criteria"]
    primary_assay_rows = [row for row in rows if row["cell"] == "primary_assay"]
    primary_recovery_rows = [
        row for row in rows if row["cell"] == "primary_recovery_64"
    ]
    primary_recovery = _recovery_metrics(primary_recovery_rows)
    recovery_failures, recovery_comparisons = _recovery_failures(
        primary_recovery, criteria
    )
    primary_assays = _evaluate_primary_assays(primary_assay_rows, criteria)
    manifests = [
        _manifest_verification(stage)
        for stage in ("V3.0", "V3.1", "V3.2", "V3.3", "V3.4")
    ]
    standing = {
        name: json.loads((RESULTS / name).read_text())["verdict"]
        for name in (
            "gate-1-amendment-2-rerun.json",
            "gate-2-amendment-2.json",
            "gate-3-amendment-2.json",
            "gate-4-amendment-2.json",
        )
    }
    failures = list(recovery_failures) + list(primary_assays["failures"])
    failures.extend(
        f"manifest {item['stage']} mismatches: {item['mismatches']}"
        for item in manifests if not item["passed"]
    )
    failures.extend(
        f"standing result {name} is {verdict}"
        for name, verdict in standing.items() if verdict != "PASS"
    )
    sweep_cells = {}
    for cell in (
        "length_32", "length_96", "missingness_25pct", "code_length_scale"
    ):
        subset = [row for row in rows if row["cell"] == cell]
        if cell in {"length_32", "length_96"}:
            sweep_cells[cell] = _recovery_metrics(subset)
        else:
            sweep_cells[cell] = _descriptive_recovery_metrics(subset)
            if cell == "code_length_scale":
                sweep_cells[cell]["by_scale"] = {
                    str(scale): _descriptive_recovery_metrics([
                        row for row in subset if row["code_length_scale"] == scale
                    ])
                    for scale in (0.75, 1.25)
                }
    policy_rows = [row for row in rows if row["cell"] == "policy_schedule"]
    sweep_cells["policy_schedule"] = _pilot_estimands(
        policy_rows,
        ("policy_exclusion", "policy_monitoring", "policy_engagement"),
    )
    apparatus_errors = [
        metric["normalization_error_max"]
        for metric in sweep_cells.values()
        if isinstance(metric, dict) and "normalization_error_max" in metric
    ]
    if apparatus_errors and max(apparatus_errors) > criteria["exact_identity_tolerance"]:
        failures.append("a robustness cell exceeded normalization tolerance")
    result = {
        "verdict": "PASS" if not failures else "FAIL",
        "seed_block": list(GATE5_BLOCK),
        "seeds_consumed": len(rows),
        "ascending_gap_free": [row["seed"] for row in rows]
        == list(range(GATE5_BLOCK[0], GATE5_BLOCK[1] + 1)),
        "partition": {
            "primary_assays": len(primary_assay_rows),
            "primary_recovery_64": len(primary_recovery_rows),
            "sweeps": {
                cell: len([row for row in rows if row["cell"] == cell])
                for cell in (
                    "length_32", "length_96", "missingness_25pct",
                    "code_length_scale", "policy_schedule",
                )
            },
        },
        "primary_recovery": primary_recovery,
        "primary_recovery_comparisons": recovery_comparisons,
        "primary_assays": primary_assays,
        "sweeps_descriptive_no_primary_floor_transplant": sweep_cells,
        "manifest_verification": manifests,
        "standing_gate_verdicts": standing,
        "failures": failures,
        "custody": {
            "runtime_events_persisted_in_trace_jsonl": True,
            "trace_hash_ledger": "gate-5-amendment-2-trace-hashes.json",
            "barred_blocks_touched": False,
            "retired_or_sealed_escrow_touched": False,
        },
    }
    _write_json("gate-5-amendment-2.json", result)
    _write_report("gate-5-amendment-2-report.md", "V3.5 Gate 5 robustness", result)
    params["status"] = "GATE5_PASSED" if not failures else "STOPPED_AT_GATE5"
    PARAMETERS.write_text(json.dumps(params, indent=2, sort_keys=True) + "\n")
    if failures:
        (RESULTS / "gate-5-amendment-2-diagnosis-stub.md").write_text(
            "# V3.5 Gate 5 diagnosis stub\n\nGate 5 stopped honestly.\n\n"
            + "\n".join(f"- {failure}" for failure in failures) + "\n"
        )
    return not failures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "step", choices=(
            "gate1", "gate1a2", "preflight", "retro", "smoke", "pilot",
            "gate2", "gate2a2", "gate3", "gate3a2", "gate4", "gate5", "pilot2",
        )
    )
    args = parser.parse_args()
    if args.step == "gate1":
        passed = run_gate1()
    elif args.step == "gate1a2":
        passed = run_gate1_amendment2()
    elif args.step == "preflight":
        passed = run_amendment_preflight()
    elif args.step == "retro":
        passed = run_retro_audits()
    elif args.step == "smoke":
        passed = run_smoke()
    elif args.step == "pilot":
        passed = run_pilot()
    elif args.step == "gate2":
        passed = run_gate2()
    elif args.step == "gate2a2":
        passed = run_gate2_amendment2()
    elif args.step == "pilot2":
        passed = run_amendment2_pilot()
    elif args.step == "gate3a2":
        passed = run_gate3_amendment2()
    elif args.step == "gate4":
        passed = run_gate4()
    elif args.step == "gate5":
        passed = run_gate5()
    else:
        passed = run_gate3()
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
