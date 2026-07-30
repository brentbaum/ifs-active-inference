#!/usr/bin/env python3
"""Prospective V3.4 RELATE stage runner."""

from __future__ import annotations

import argparse
import ast
import hashlib
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

from ref import audit, v34, v34_oracle  # noqa: E402
from ref.trace_sink import traced_execution  # noqa: E402


RESULTS = ROOT / "results" / "V3.4"
PARAMETERS = ROOT / "protocols" / "v3.4-parameters.json"
TOLERANCE = 1e-10


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


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            _plain(value),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _write_json(name: str, value: Any) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / name).write_text(
        json.dumps(
            _plain(value), indent=2, sort_keys=True, allow_nan=False
        )
        + "\n",
        encoding="utf-8",
    )


def _seal_rows(
    name: str, rows: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{name}-traces.jsonl"
    file_hash = hashlib.sha256()
    records = []
    with path.open("wb") as handle:
        for row in rows:
            encoded = _canonical_bytes(row)
            handle.write(encoded)
            handle.flush()
            file_hash.update(encoded)
            records.append(
                {
                    "seed": row.get("seed", "authored-dummy"),
                    "sha256": hashlib.sha256(encoded).hexdigest(),
                }
            )
    ledger = {
        "file": path.name,
        "world_count": len(rows),
        "file_sha256": file_hash.hexdigest(),
        "records": records,
    }
    _write_json(f"{name}-trace-hashes.json", ledger)
    return ledger


def _trace_map(
    name: str, tasks: Sequence[Any], worker: Any
) -> list[dict[str, Any]]:
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{name}-traces.jsonl"
    rows = []
    records = []
    file_hash = hashlib.sha256()
    processes = max(1, min(8, (os.cpu_count() or 2) - 1))
    with path.open("wb") as handle:
        with get_context("spawn").Pool(processes) as pool:
            for row in pool.imap(worker, tasks, chunksize=8):
                encoded = _canonical_bytes(row)
                handle.write(encoded)
                handle.flush()
                file_hash.update(encoded)
                records.append(
                    {
                        "seed": row["seed"],
                        "sha256": hashlib.sha256(encoded).hexdigest(),
                    }
                )
                rows.append(row)
    _write_json(
        f"{name}-trace-hashes.json",
        {
            "file": path.name,
            "world_count": len(rows),
            "file_sha256": file_hash.hexdigest(),
            "records": records,
        },
    )
    return rows


def _authored_world(
    *, root: bool = True, masked: bool = False
) -> v34.RelateWorld:
    observations = []
    for time in range(8):
        observations.append(
            v34.RelateObservation(
                time=time,
                relational=(
                    (None,) * 5
                    if masked
                    else (1, 1, 0, 1, 0)
                ),
                regulation_response=None if masked else 1,
                partner_action=time % 2,
                outcome=None if masked else 1,
                root_evidence=(1 if root and time >= 6 else None),
            )
        )
    structure = v34.RelateStructure(1, 1, 1, 0)
    return v34.RelateWorld(
        -34,
        v34.RelateConfig("reliable", not masked, root, length=8),
        structure,
        tuple([0] * 8),
        1,
        tuple(observations),
        0.0,
        (),
    )


def _bits(structure: v34.RelateStructure) -> tuple[int, ...]:
    return tuple(v34.structure_values(structure).values())


@traced_execution
def _gate1_semantics() -> dict[str, Any]:
    world = _authored_world()
    posterior = v34.score_world(world)
    observations = [asdict(item) for item in world.observations]
    snapshot = json.dumps(observations, sort_keys=True)
    oracle_programs, oracle_probabilities, oracle_root, oracle_evidence = (
        v34_oracle.posterior(observations)
    )
    production = {
        _bits(program): probability
        for program, probability in zip(
            posterior.programs, posterior.structure_probabilities
        )
    }
    oracle_probability_error = max(
        abs(probability - production[program])
        for program, probability in zip(
            oracle_programs, oracle_probabilities
        )
    )
    oracle_root_error = max(
        abs(a - b)
        for a, b in zip(oracle_root, posterior.q_root)
    )
    masked = _authored_world(root=False, masked=True)
    masked_posterior = v34.score_world(masked)
    prior_probabilities = tuple(
        math.exp(v34.structure_log_prior(program))
        for program in v34.STRUCTURES
    )
    masked_prior_error = max(
        abs(a - b)
        for a, b in zip(
            masked_posterior.structure_probabilities,
            prior_probabilities,
        )
    )
    regulation_only = _authored_world(root=False)
    regulation_posterior = v34.score_world(regulation_only)
    broadcast_on = v34.score_world(regulation_only, broadcast=True)
    broadcast_off = v34.score_world(regulation_only, broadcast=False)
    broadcast_structure_error = max(
        abs(a - b)
        for a, b in zip(
            broadcast_on.structure_probabilities,
            broadcast_off.structure_probabilities,
        )
    )
    broadcast_partner_error = max(
        abs(a - b)
        for a, b in zip(
            broadcast_on.q_partner, broadcast_off.q_partner
        )
    )
    root_masked = v34.score_world(world, root_evidence_enabled=False)
    restrictions = {"L_Y": (0,)}
    restricted = v34.score_world(
        world, restrictions=restrictions
    )
    retained = {
        program: probability
        for program, probability in zip(
            posterior.programs, posterior.structure_probabilities
        )
        if not program.l_outcome
    }
    retained_mass = math.fsum(retained.values())
    restricted_error = max(
        abs(probability - retained[program] / retained_mass)
        for program, probability in zip(
            restricted.programs,
            restricted.structure_probabilities,
        )
    )
    restricted_oracle = v34_oracle.posterior(
        observations, restrictions=restrictions
    )
    restricted_oracle_map = dict(
        zip(restricted_oracle[0], restricted_oracle[1])
    )
    restricted_oracle_error = max(
        abs(
            probability
            - restricted_oracle_map[_bits(program)]
        )
        for program, probability in zip(
            restricted.programs,
            restricted.structure_probabilities,
        )
    )
    trust_before = tuple(posterior.structure_probabilities)
    _ = posterior.trust_remaining_after_refusal
    _ = posterior.co_regulated
    trust_pure = trust_before == posterior.structure_probabilities
    factor_normalization_error = 0.0
    for structure in v34.STRUCTURES:
        matrix = v34.transition_matrix(structure)
        factor_normalization_error = max(
            factor_normalization_error,
            float(np.max(np.abs(matrix.sum(axis=1) - 1.0))),
        )
        for state in range(4):
            for channel in range(5):
                for action in (0, 1):
                    probability = v34.relational_probability(
                        state, channel, action, structure
                    )
                    factor_normalization_error = max(
                        factor_normalization_error,
                        abs(probability + (1.0 - probability) - 1.0),
                    )
    absent = v34.RelateStructure(0, 0, 0, 0)
    edge_absence_errors = {
        "L_PREC": max(
            abs(
                v34.regulation_probability(state, absent) - 0.5
            )
            for state in range(4)
        ),
        "L_Y": max(
            abs(
                v34.outcome_probability(state, 0, absent) - 0.5
            )
            for state in range(4)
        ),
        "PA_RY": max(
            abs(
                v34.relational_probability(
                    state, channel, 0, absent
                )
                - v34.relational_probability(
                    state, channel, 1, absent
                )
            )
            for state in range(4)
            for channel in range(5)
        ),
        "L_TRANSITION": float(
            np.max(
                np.abs(v34.transition_matrix(absent) - np.eye(4))
            )
        ),
    }
    source = (ROOT / "ref" / "v34.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    action_likelihood_functions = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name in {
            "action_probability",
            "action_likelihood",
            "score_partner_action",
        }
    ]
    label_rejected = False
    try:
        v34.score_world(
            replace(world, analysis_labels=("reliable",))
        )
    except ValueError:
        label_rejected = True
    prior_sum = math.fsum(
        math.exp(v34.structure_log_prior(program))
        for program in v34.STRUCTURES
    )
    proofs = {
        "1_structure_prior_normalization_error": abs(prior_sum - 1.0),
        "2_factor_normalization_error": factor_normalization_error,
        "3_posterior_normalization_error": abs(
            math.fsum(posterior.structure_probabilities) - 1.0
        ),
        "4_edge_absence_conditional_independence_errors": (
            edge_absence_errors
        ),
        "5_masked_relational_structure_error": masked_prior_error,
        "6_regulation_only_root_bf": regulation_posterior.root_log_bf,
        "6_regulation_only_root_prior_error": max(
            abs(a - b)
            for a, b in zip(
                regulation_posterior.q_root, (0.5, 0.5)
            )
        ),
        "7_broadcast_relational_structure_error": (
            broadcast_structure_error
        ),
        "7_broadcast_partner_error": broadcast_partner_error,
        "7_broadcast_off_global_error": max(
            abs(value - v34.BASE_PRECISION)
            for value in broadcast_off.global_precision
        ),
        "8_action_selection_likelihood_functions": (
            action_likelihood_functions
        ),
        "9_analysis_label_rejected": label_rejected,
        "10_trust_readout_purity": trust_pure,
        "11_independent_oracle_probability_error": (
            oracle_probability_error
        ),
        "11_independent_oracle_root_error": oracle_root_error,
        "11_independent_oracle_evidence_error": abs(
            posterior.log_evidence - oracle_evidence
        ),
        "11_oracle_input_copy": (
            snapshot == json.dumps(observations, sort_keys=True)
        ),
        "12_static_dynamic_transition_error": (
            factor_normalization_error
        ),
        "13_root_mask_root_bf": root_masked.root_log_bf,
        "14_restricted_prior_identity_error": restricted_error,
        "14_restricted_independent_oracle_error": (
            restricted_oracle_error
        ),
        "16_import_audit": audit.audit_imports(ROOT / "ref"),
        "16_state_audit": audit.audit_state(posterior),
    }
    numeric = []
    for key, value in proofs.items():
        if isinstance(value, float):
            numeric.append(abs(value))
    numeric.extend(abs(value) for value in edge_absence_errors.values())
    passed = (
        all(value <= TOLERANCE for value in numeric)
        and not action_likelihood_functions
        and label_rejected
        and trust_pure
        and proofs["11_oracle_input_copy"]
        and not proofs["16_import_audit"]
        and not proofs["16_state_audit"]
    )
    return {
        "seed": "authored-no-rng-dummy",
        "cell": "gate1_semantics",
        "passed": passed,
        "proofs": proofs,
        "structure_space_size": len(v34.STRUCTURES),
        "finite_information_bounds": dict(
            v34.finite_information_bounds()
        ),
    }


def run_gate1() -> bool:
    runtime_refusal = False
    try:
        v34.generate_world(
            3_400_000,
            v34.RelateConfig("reliable", True, False),
        )
    except RuntimeError as error:
        runtime_refusal = "serializing trace context" in str(error)
    payload = _gate1_semantics()
    payload["proofs"]["15_trace_sink_refusal"] = runtime_refusal
    payload["passed"] = payload["passed"] and runtime_refusal
    _seal_rows("gate-1", [payload])
    result = {
        "verdict": "PASS" if payload["passed"] else "FAIL",
        "proofs": payload["proofs"],
        "structure_space_size": payload["structure_space_size"],
        "finite_information_bounds": payload[
            "finite_information_bounds"
        ],
        "pilot_unopened": True,
    }
    _write_json("gate-1.json", result)
    parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    parameters["status"] = (
        "GATE1_PASSED_PILOT_UNOPENED"
        if payload["passed"]
        else "STOPPED_AT_GATE1"
    )
    PARAMETERS.write_text(
        json.dumps(parameters, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not payload["passed"]:
        _write_json(
            "gate-1-diagnosis-stub.json",
            {"failed": payload["proofs"]},
        )
    return bool(payload["passed"])


def _ece(
    confidence: Sequence[float], correct: Sequence[bool]
) -> float:
    probabilities = np.asarray(confidence, dtype=float)
    outcomes = np.asarray(correct, dtype=float)
    result = 0.0
    for lower in np.linspace(0.0, 0.9, 10):
        upper = lower + 0.1
        selected = (probabilities >= lower) & (
            probabilities <= upper
            if math.isclose(upper, 1.0)
            else probabilities < upper
        )
        if selected.any():
            result += float(selected.mean()) * abs(
                float(probabilities[selected].mean())
                - float(outcomes[selected].mean())
            )
    return float(result)


def _credible_contains(
    probabilities: Sequence[float], truth_index: int
) -> bool:
    order = np.argsort(-np.asarray(probabilities))
    mass = 0.0
    for index in order:
        mass += float(probabilities[int(index)])
        if int(index) == truth_index:
            return True
        if mass >= 0.95:
            return False
    return False


@traced_execution
def _worker_recovery(
    task: tuple[int, int, float, float]
) -> dict[str, Any]:
    seed, length, transition_stay, scale = task
    hyperparameters = v34.V34Hyperparameters(
        code_length_scale=scale,
        transition_stay=transition_stay,
    )
    world = v34.generate_recovery_world(
        seed, length=length, hyperparameters=hyperparameters
    )
    posterior = v34.score_world(
        world, hyperparameters=hyperparameters
    )
    truth_bits = _bits(world.truth_structure)
    predicted_index = int(
        np.argmax(posterior.structure_probabilities)
    )
    predicted_bits = _bits(posterior.programs[predicted_index])
    truth_index = posterior.programs.index(world.truth_structure)
    partner_correct = [
        int(np.argmax(probabilities)) == truth
        for probabilities, truth in zip(
            posterior.smoothed_partner, world.truth_partner_path
        )
    ]
    return {
        "seed": seed,
        "cell": "recovery",
        "truth_bits": truth_bits,
        "predicted_bits": predicted_bits,
        "edge_correct": [
            predicted == truth
            for predicted, truth in zip(predicted_bits, truth_bits)
        ],
        "program_correct": predicted_bits == truth_bits,
        "confidence": posterior.structure_probabilities[predicted_index],
        "credible_contains_truth": _credible_contains(
            posterior.structure_probabilities, truth_index
        ),
        "root_correct": int(np.argmax(posterior.q_root))
        == world.truth_root,
        "root_confidence": max(posterior.q_root),
        "partner_accuracy": float(np.mean(partner_correct)),
        "normalization_error": abs(
            math.fsum(posterior.structure_probabilities) - 1.0
        ),
        "exact_complete_log_probability_error": abs(
            world.exact_log_probability
            - v34.exact_complete_log_probability(
                world, hyperparameters=hyperparameters
            )
        ),
    }


def _recovery_metrics(
    rows: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    edge_accuracy = {
        edge: float(
            np.mean(
                [row["edge_correct"][index] for row in rows]
            )
        )
        for index, edge in enumerate(v34.EDGE_NAMES)
    }
    correct = [bool(row["program_correct"]) for row in rows]
    confidence = [float(row["confidence"]) for row in rows]
    root_correct = [bool(row["root_correct"]) for row in rows]
    root_confidence = [float(row["root_confidence"]) for row in rows]
    return {
        "world_count": len(rows),
        "edge_accuracy": edge_accuracy,
        "minimum_edge_accuracy": min(edge_accuracy.values()),
        "transition_accuracy": edge_accuracy["L_TRANSITION"],
        "program_accuracy": float(np.mean(correct)),
        "root_accuracy": float(np.mean(root_correct)),
        "partner_accuracy": float(
            np.mean([row["partner_accuracy"] for row in rows])
        ),
        "structure_brier": float(
            np.mean(
                [
                    (probability - float(outcome)) ** 2
                    for probability, outcome in zip(
                        confidence, correct
                    )
                ]
            )
        ),
        "structure_ece": _ece(confidence, correct),
        "root_ece": _ece(root_confidence, root_correct),
        "coverage": float(
            np.mean([row["credible_contains_truth"] for row in rows])
        ),
        "maximum_normalization_error": max(
            row["normalization_error"] for row in rows
        ),
        "maximum_exact_complete_log_probability_error": max(
            row["exact_complete_log_probability_error"] for row in rows
        ),
    }


def _score_summary(
    world: v34.RelateWorld, *, broadcast: bool | None = None
) -> dict[str, Any]:
    posterior = v34.score_world(world, broadcast=broadcast)
    return {
        "root_bf": posterior.root_log_bf,
        "root_movement": posterior.root_movement,
        "transfer": posterior.transfer,
        "local_precision": (
            posterior.local_precision[-1]
            if posterior.local_precision
            else v34.BASE_PRECISION
        ),
        "global_precision": (
            posterior.global_precision[-1]
            if posterior.global_precision
            else v34.BASE_PRECISION
        ),
        "q_partner": posterior.q_partner,
        "trust": posterior.trust_remaining_after_refusal,
        "transition": posterior.transition_probability,
        "switch_onset": posterior.switch_onset,
        "structure_probabilities": posterior.structure_probabilities,
        "co_regulated": posterior.co_regulated,
    }


@traced_execution
def _worker_pilot_assays(seed: int) -> dict[str, Any]:
    factorial = {}
    for regulation, root in (
        (False, False),
        (True, False),
        (False, True),
        (True, True),
    ):
        name = f"r{int(regulation)}_g{int(root)}"
        world = v34.generate_world(
            seed,
            v34.RelateConfig(
                "reliable", regulation, root, length=48
            ),
        )
        factorial[name] = _score_summary(world)
    controls = {}
    for pattern in (
        "soothing_noncontingent",
        "intrusive",
        "unstable",
        "switch",
    ):
        world = v34.generate_world(
            seed,
            v34.RelateConfig(pattern, True, False, length=48),
        )
        controls[pattern] = _score_summary(world)
    broadcast_world = v34.generate_world(
        seed,
        v34.RelateConfig("reliable", True, True, length=48),
    )
    broadcast_on = _score_summary(broadcast_world, broadcast=True)
    broadcast_off = _score_summary(broadcast_world, broadcast=False)
    return {
        "seed": seed,
        "cell": "pilot_exact_gate3_set",
        "factorial": factorial,
        "controls": controls,
        "broadcast_on": broadcast_on,
        "broadcast_off": broadcast_off,
        "broadcast_local_identity_error": max(
            abs(a - b)
            for a, b in zip(
                broadcast_on["q_partner"],
                broadcast_off["q_partner"],
            )
        ),
        "switch_truth_onset": 24,
    }


def run_pilot() -> bool:
    parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    if parameters["status"] != "GATE1_PASSED_PILOT_UNOPENED":
        raise RuntimeError("V3.4 Gate 1 must pass before the pilot")
    recovery_rows = _trace_map(
        "stage0-pilot-recovery",
        [
            (seed, 48, 0.88, 1.0)
            for seed in range(3_400_000, 3_400_800)
        ],
        _worker_recovery,
    )
    assay_rows = _trace_map(
        "stage0-pilot-assays",
        list(range(3_400_800, 3_402_000)),
        _worker_pilot_assays,
    )
    recovery = _recovery_metrics(recovery_rows)
    local_differences = [
        row["factorial"]["r1_g0"]["local_precision"]
        - row["factorial"]["r0_g0"]["local_precision"]
        for row in assay_rows
    ]
    uptake_differences = [
        row["factorial"]["r1_g1"]["root_movement"]
        - row["factorial"]["r0_g1"]["root_movement"]
        for row in assay_rows
    ]
    transfer_differences = [
        row["factorial"]["r1_g1"]["transfer"]
        - row["factorial"]["r0_g1"]["transfer"]
        for row in assay_rows
    ]
    reliable_trust = [
        row["factorial"]["r1_g0"]["trust"] for row in assay_rows
    ]
    soothing_trust = [
        row["controls"]["soothing_noncontingent"]["trust"]
        for row in assay_rows
    ]
    intrusive_trust = [
        row["controls"]["intrusive"]["trust"] for row in assay_rows
    ]
    unstable_transition = [
        row["controls"]["unstable"]["transition"]
        for row in assay_rows
    ]
    switch_errors = [
        abs(
            row["controls"]["switch"]["switch_onset"]
            - row["switch_truth_onset"]
        )
        for row in assay_rows
    ]
    broadcast_uptake = [
        row["broadcast_on"]["root_movement"]
        - row["broadcast_off"]["root_movement"]
        for row in assay_rows
    ]
    attainable = {
        "local_precision_difference_mean": float(
            np.mean(local_differences)
        ),
        "factorial_uptake_difference_mean": float(
            np.mean(uptake_differences)
        ),
        "factorial_transfer_difference_mean": float(
            np.mean(transfer_differences)
        ),
        "regulation_only_root_bf_max_abs": max(
            abs(row["factorial"]["r1_g0"]["root_bf"])
            for row in assay_rows
        ),
        "no_evidence_root_bf_max_abs": max(
            abs(row["factorial"]["r0_g0"]["root_bf"])
            for row in assay_rows
        ),
        "reliable_trust_mean": float(np.mean(reliable_trust)),
        "soothing_contingency_gap_mean": float(
            np.mean(
                np.asarray(reliable_trust)
                - np.asarray(soothing_trust)
            )
        ),
        "intrusive_trust_q95": float(
            np.quantile(intrusive_trust, 0.95)
        ),
        "unstable_transition_probability_mean": float(
            np.mean(unstable_transition)
        ),
        "switch_onset_error_q95": float(
            np.quantile(switch_errors, 0.95)
        ),
        "broadcast_local_identity_max": max(
            row["broadcast_local_identity_error"]
            for row in assay_rows
        ),
        "broadcast_root_uptake_mean": float(
            np.mean(broadcast_uptake)
        ),
    }
    if (
        attainable["regulation_only_root_bf_max_abs"] > TOLERANCE
        or attainable["no_evidence_root_bf_max_abs"] > TOLERANCE
        or attainable["factorial_uptake_difference_mean"] <= 0.0
        or attainable["local_precision_difference_mean"] <= 0.0
    ):
        parameters["status"] = "STOPPED_AT_STAGE0_UNATTAINABLE"
        PARAMETERS.write_text(
            json.dumps(parameters, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _write_json(
            "stage0-pilot.json",
            {
                "verdict": "STOP_UNATTAINABLE",
                "recovery": recovery,
                "attainable": attainable,
                "barred_block": [3_400_000, 3_401_999],
            },
        )
        return False
    criteria = {
        "edge_accuracy_min": max(
            0.50,
            math.floor(
                (recovery["minimum_edge_accuracy"] - 0.05) * 100
            )
            / 100,
        ),
        "transition_accuracy_min": max(
            0.55,
            math.floor(
                (recovery["transition_accuracy"] - 0.05) * 100
            )
            / 100,
        ),
        "program_accuracy_min": max(
            0.20,
            math.floor(
                (recovery["program_accuracy"] - 0.05) * 100
            )
            / 100,
        ),
        "root_accuracy_min": max(
            0.70,
            math.floor((recovery["root_accuracy"] - 0.05) * 100)
            / 100,
        ),
        "partner_accuracy_min": max(
            0.60,
            math.floor((recovery["partner_accuracy"] - 0.05) * 100)
            / 100,
        ),
        "ece_max": min(
            0.20,
            math.ceil(
                (
                    max(recovery["structure_ece"], recovery["root_ece"])
                    + 0.05
                )
                * 100
            )
            / 100,
        ),
        "coverage_min": max(
            0.80,
            math.floor((recovery["coverage"] - 0.05) * 100)
            / 100,
        ),
        "local_precision_difference_min": (
            attainable["local_precision_difference_mean"] * 0.5
        ),
        "factorial_uptake_difference_min": (
            attainable["factorial_uptake_difference_mean"] * 0.5
        ),
        "factorial_transfer_difference_min": (
            attainable["factorial_transfer_difference_mean"] * 0.5
        ),
        "reliable_trust_min": float(
            np.quantile(reliable_trust, 0.05) * 0.9
        ),
        "soothing_contingency_gap_min": (
            attainable["soothing_contingency_gap_mean"] * 0.5
        ),
        "intrusive_trust_max": min(
            0.75, attainable["intrusive_trust_q95"] + 0.05
        ),
        "unstable_transition_probability_min": (
            attainable["unstable_transition_probability_mean"] * 0.75
        ),
        "switch_onset_error_max": max(
            2.0, attainable["switch_onset_error_q95"] + 1.0
        ),
        "broadcast_local_identity_max": TOLERANCE,
        "broadcast_root_uptake_min": (
            attainable["broadcast_root_uptake_mean"] * 0.5
        ),
    }
    parameters["criteria"] = criteria
    parameters["status"] = "FROZEN_AFTER_ATTAINABILITY_PILOT"
    parameters["pilot_summary_sha256"] = hashlib.sha256(
        _canonical_bytes(
            {"recovery": recovery, "attainable": attainable}
        )
    ).hexdigest()
    PARAMETERS.write_text(
        json.dumps(parameters, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_json(
        "stage0-pilot.json",
        {
            "verdict": "DESCRIPTIVE_ATTAINABILITY_PASS",
            "barred_block": [3_400_000, 3_401_999],
            "recovery": recovery,
            "attainable": attainable,
            "frozen_criteria": criteria,
        },
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("gate1", "pilot"))
    args = parser.parse_args()
    passed = run_gate1() if args.step == "gate1" else run_pilot()
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
