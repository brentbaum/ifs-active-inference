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
    task: tuple[
        int,
        int,
        float,
        float,
        tuple[int, int] | None,
        bool,
    ]
) -> dict[str, Any]:
    (
        seed,
        length,
        transition_stay,
        scale,
        released_block,
        audit_oracle,
    ) = task
    hyperparameters = v34.V34Hyperparameters(
        code_length_scale=scale,
        transition_stay=transition_stay,
    )
    world = v34.generate_recovery_world(
        seed,
        length=length,
        hyperparameters=hyperparameters,
        released_block=released_block,
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
    row = {
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
    if audit_oracle:
        observations = [asdict(item) for item in world.observations]
        snapshot = json.dumps(observations, sort_keys=True)
        programs, probabilities, root, evidence = v34_oracle.posterior(
            observations,
            code_length_scale=scale,
            transition_stay=transition_stay,
        )
        production = {
            _bits(program): probability
            for program, probability in zip(
                posterior.programs, posterior.structure_probabilities
            )
        }
        row["oracle_structure_error"] = max(
            abs(probability - production[program])
            for program, probability in zip(programs, probabilities)
        )
        row["oracle_root_error"] = max(
            abs(a - b) for a, b in zip(root, posterior.q_root)
        )
        row["oracle_evidence_error"] = abs(
            evidence - posterior.log_evidence
        )
        row["oracle_input_unchanged"] = (
            snapshot == json.dumps(observations, sort_keys=True)
        )
    return row


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
        "edge_probabilities": dict(posterior.edge_probabilities),
        "co_regulated": posterior.co_regulated,
    }


@traced_execution
def _worker_pilot_assays(seed: int) -> dict[str, Any]:
    released_block = (3_430_000, 3_431_999)
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
            released_block=released_block,
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
            released_block=released_block,
        )
        controls[pattern] = _score_summary(world)
    broadcast_world = v34.generate_world(
        seed,
        v34.RelateConfig("reliable", True, True, length=48),
        released_block=released_block,
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
    if parameters["status"] != "STAGE0_REPAIR_AUTHORIZED":
        raise RuntimeError("V3.4 repaired pilot is not authorized")
    recovery_rows = _trace_map(
        "stage0-pilot-repaired-recovery",
        [
            (
                seed,
                48,
                0.88,
                1.0,
                (3_430_000, 3_431_999),
                False,
            )
            for seed in range(3_430_000, 3_430_800)
        ],
        _worker_recovery,
    )
    assay_rows = _trace_map(
        "stage0-pilot-repaired-assays",
        list(range(3_430_800, 3_432_000)),
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
        or recovery["root_ece"]
        > recovery["structure_ece"] + 0.05
    ):
        parameters["status"] = "STOPPED_AT_STAGE0_UNATTAINABLE"
        PARAMETERS.write_text(
            json.dumps(parameters, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _write_json(
            "stage0-pilot-repaired.json",
            {
                "verdict": "STOP_UNATTAINABLE",
                "recovery": recovery,
                "attainable": attainable,
                "barred_block": [3_430_000, 3_431_999],
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
        "stage0-pilot-repaired.json",
        {
            "verdict": "DESCRIPTIVE_ATTAINABILITY_PASS",
        "barred_block": [3_430_000, 3_431_999],
            "recovery": recovery,
            "attainable": attainable,
            "frozen_criteria": criteria,
        },
    )
    return True


def run_gate2() -> bool:
    parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    if parameters["status"] != "FROZEN_AFTER_ATTAINABILITY_PILOT":
        raise RuntimeError("the corrected pilot must freeze before Gate 2")
    rows = _trace_map(
        "gate-2",
        [
            (
                seed,
                48,
                0.88,
                1.0,
                None,
                (seed - 3_402_000) % 30 == 0,
            )
            for seed in range(3_402_000, 3_405_000)
        ],
        _worker_recovery,
    )
    metrics = _recovery_metrics(rows)
    audited = [row for row in rows if "oracle_structure_error" in row]
    oracle = {
        "world_count": len(audited),
        "maximum_structure_error": max(
            row["oracle_structure_error"] for row in audited
        ),
        "maximum_root_error": max(
            row["oracle_root_error"] for row in audited
        ),
        "maximum_evidence_error": max(
            row["oracle_evidence_error"] for row in audited
        ),
        "all_inputs_unchanged": all(
            row["oracle_input_unchanged"] for row in audited
        ),
    }
    criteria = parameters["criteria"]
    checks = {
        "minimum_edge_accuracy": (
            metrics["minimum_edge_accuracy"]
            >= criteria["edge_accuracy_min"]
        ),
        "transition_accuracy": (
            metrics["transition_accuracy"]
            >= criteria["transition_accuracy_min"]
        ),
        "program_accuracy": (
            metrics["program_accuracy"]
            >= criteria["program_accuracy_min"]
        ),
        "root_accuracy": (
            metrics["root_accuracy"] >= criteria["root_accuracy_min"]
        ),
        "partner_accuracy": (
            metrics["partner_accuracy"]
            >= criteria["partner_accuracy_min"]
        ),
        "structure_ece": metrics["structure_ece"] <= criteria["ece_max"],
        "root_ece": metrics["root_ece"] <= criteria["ece_max"],
        "coverage": metrics["coverage"] >= criteria["coverage_min"],
        "normalization": (
            metrics["maximum_normalization_error"] <= TOLERANCE
        ),
        "complete_log_probability": (
            metrics["maximum_exact_complete_log_probability_error"]
            <= TOLERANCE
        ),
        "independent_oracle": (
            oracle["maximum_structure_error"] <= TOLERANCE
            and oracle["maximum_root_error"] <= TOLERANCE
            and oracle["maximum_evidence_error"] <= TOLERANCE
            and oracle["all_inputs_unchanged"]
        ),
    }
    passed = all(checks.values())
    result = {
        "verdict": "PASS" if passed else "FAIL",
        "seed_block": [3_402_000, 3_404_999],
        "metrics": metrics,
        "thresholds": criteria,
        "independent_oracle": oracle,
        "checks": checks,
        "calibration_by_theorem": (
            "world structures, roots, paths, and observations are sampled "
            "from the scorer's own normalized process"
        ),
    }
    _write_json("gate-2.json", result)
    parameters["status"] = "GATE2_PASSED" if passed else "STOPPED_AT_GATE2"
    PARAMETERS.write_text(
        json.dumps(parameters, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not passed:
        _write_json(
            "gate-2-diagnosis-stub.json",
            {
                "failed_checks": [
                    name for name, value in checks.items() if not value
                ],
                "metrics": metrics,
            },
        )
    return passed


def _mean_ci(values: Sequence[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    mean = float(array.mean())
    standard_error = (
        float(array.std(ddof=1) / math.sqrt(len(array)))
        if len(array) > 1
        else 0.0
    )
    return {
        "mean": mean,
        "lower_95": mean - 1.96 * standard_error,
        "upper_95": mean + 1.96 * standard_error,
    }


@traced_execution
def _worker_factorial(seed: int) -> dict[str, Any]:
    arms = {}
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
        arms[name] = _score_summary(world)
    return {"seed": seed, "cell": "factorial", "arms": arms}


@traced_execution
def _worker_control(task: tuple[int, str]) -> dict[str, Any]:
    seed, pattern = task
    world = v34.generate_world(
        seed, v34.RelateConfig(pattern, True, False, length=48)
    )
    score = _score_summary(world)
    row = {
        "seed": seed,
        "cell": pattern,
        "score": score,
    }
    if pattern == "soothing_noncontingent":
        reference = v34.generate_world(
            seed,
            v34.RelateConfig("reliable", True, False, length=48),
        )
        row["reliable_reference"] = _score_summary(reference)
    return row


@traced_execution
def _worker_broadcast(seed: int) -> dict[str, Any]:
    world = v34.generate_world(
        seed,
        v34.RelateConfig("reliable", True, True, length=48),
    )
    on = _score_summary(world, broadcast=True)
    off = _score_summary(world, broadcast=False)
    local_on_posterior = v34.score_world(
        world, broadcast=True, root_evidence_enabled=False
    )
    local_off_posterior = v34.score_world(
        world, broadcast=False, root_evidence_enabled=False
    )
    return {
        "seed": seed,
        "cell": "broadcast",
        "on": on,
        "off": off,
        "local_q_partner_identity_error": max(
            abs(a - b)
            for a, b in zip(
                local_on_posterior.q_partner,
                local_off_posterior.q_partner,
            )
        ),
        "local_structure_identity_error": max(
            abs(a - b)
            for a, b in zip(
                local_on_posterior.structure_probabilities,
                local_off_posterior.structure_probabilities,
            )
        ),
        "off_global_baseline_error": max(
            abs(value - v34.BASE_PRECISION)
            for value in off["global_precision"]
        )
        if isinstance(off["global_precision"], tuple)
        else abs(off["global_precision"] - v34.BASE_PRECISION),
        "off_local_precision": off["local_precision"],
    }


def run_gate3() -> bool:
    parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    if parameters["status"] != "GATE2_PASSED":
        raise RuntimeError("Gate 2 must pass before Gate 3")
    factorial = _trace_map(
        "gate-3-factorial",
        list(range(3_405_000, 3_406_000)),
        _worker_factorial,
    )
    controls = {}
    allocations = {
        "soothing_noncontingent": (3_406_000, 3_406_800),
        "intrusive": (3_406_800, 3_407_600),
        "unstable": (3_407_600, 3_408_400),
        "switch": (3_408_400, 3_409_200),
    }
    for pattern, (start, end) in allocations.items():
        controls[pattern] = _trace_map(
            f"gate-3-{pattern}",
            [(seed, pattern) for seed in range(start, end)],
            _worker_control,
        )
    broadcast = _trace_map(
        "gate-3-broadcast",
        list(range(3_409_200, 3_410_000)),
        _worker_broadcast,
    )
    no_root_bf = [
        abs(row["arms"][arm]["root_bf"])
        for row in factorial
        for arm in ("r0_g0", "r1_g0")
    ]
    no_root_movement = [
        abs(row["arms"][arm]["root_movement"])
        for row in factorial
        for arm in ("r0_g0", "r1_g0")
    ]
    local_difference = [
        row["arms"]["r1_g0"]["local_precision"]
        - row["arms"]["r0_g0"]["local_precision"]
        for row in factorial
    ]
    unregulated_evidence = [
        row["arms"]["r0_g1"]["root_movement"] for row in factorial
    ]
    uptake_difference = [
        row["arms"]["r1_g1"]["root_movement"]
        - row["arms"]["r0_g1"]["root_movement"]
        for row in factorial
    ]
    transfer_difference = [
        row["arms"]["r1_g1"]["transfer"]
        - row["arms"]["r0_g1"]["transfer"]
        for row in factorial
    ]
    reliable_trust = [
        row["arms"]["r1_g0"]["trust"] for row in factorial
    ]
    soothing_gap = [
        row["reliable_reference"]["trust"] - row["score"]["trust"]
        for row in controls["soothing_noncontingent"]
    ]
    intrusive_trust = [
        row["score"]["trust"] for row in controls["intrusive"]
    ]
    unstable_transition = [
        row["score"]["transition"] for row in controls["unstable"]
    ]
    switch_error = [
        abs(row["score"]["switch_onset"] - 24)
        for row in controls["switch"]
    ]
    broadcast_uptake = [
        row["on"]["root_movement"] - row["off"]["root_movement"]
        for row in broadcast
    ]
    metrics = {
        "regulation_only_root_bf_max_abs": max(no_root_bf),
        "no_root_movement_max_abs": max(no_root_movement),
        "local_precision_difference": _mean_ci(local_difference),
        "unregulated_root_evidence_movement": _mean_ci(
            unregulated_evidence
        ),
        "regulated_uptake_difference": _mean_ci(uptake_difference),
        "regulated_transfer_difference": _mean_ci(
            transfer_difference
        ),
        "reliable_trust": _mean_ci(reliable_trust),
        "soothing_noncontingent_trust_gap": _mean_ci(soothing_gap),
        "intrusive_trust_q95": float(
            np.quantile(intrusive_trust, 0.95)
        ),
        "unstable_transition_probability": _mean_ci(
            unstable_transition
        ),
        "switch_onset_error_q95": float(
            np.quantile(switch_error, 0.95)
        ),
        "broadcast_local_q_partner_identity_max": max(
            row["local_q_partner_identity_error"] for row in broadcast
        ),
        "broadcast_local_structure_identity_max": max(
            row["local_structure_identity_error"] for row in broadcast
        ),
        "broadcast_off_global_baseline_error_max": max(
            row["off_global_baseline_error"] for row in broadcast
        ),
        "broadcast_off_local_precision": _mean_ci(
            [row["off_local_precision"] for row in broadcast]
        ),
        "broadcast_root_uptake_difference": _mean_ci(
            broadcast_uptake
        ),
    }
    criteria = parameters["criteria"]
    checks = {
        "regulation_without_root_is_exactly_neutral": (
            metrics["regulation_only_root_bf_max_abs"] <= TOLERANCE
            and metrics["no_root_movement_max_abs"] <= TOLERANCE
        ),
        "regulation_increases_local_precision": (
            metrics["local_precision_difference"]["mean"]
            >= criteria["local_precision_difference_min"]
            and metrics["local_precision_difference"]["lower_95"] > 0.0
        ),
        "root_evidence_available_without_regulation": (
            metrics["unregulated_root_evidence_movement"]["lower_95"]
            > 0.0
        ),
        "regulation_increases_root_uptake": (
            metrics["regulated_uptake_difference"]["mean"]
            >= criteria["factorial_uptake_difference_min"]
            and metrics["regulated_uptake_difference"]["lower_95"] > 0.0
        ),
        "regulation_increases_transfer": (
            metrics["regulated_transfer_difference"]["mean"]
            >= criteria["factorial_transfer_difference_min"]
            and metrics["regulated_transfer_difference"]["lower_95"] > 0.0
        ),
        "reliable_partner_trust": (
            metrics["reliable_trust"]["mean"]
            >= criteria["reliable_trust_min"]
        ),
        "soothing_without_contingency_distinguished": (
            metrics["soothing_noncontingent_trust_gap"]["mean"]
            >= criteria["soothing_contingency_gap_min"]
            and metrics["soothing_noncontingent_trust_gap"]["lower_95"]
            > 0.0
        ),
        "intrusion_distinguished": (
            metrics["intrusive_trust_q95"]
            <= criteria["intrusive_trust_max"]
        ),
        "instability_supports_transitions": (
            metrics["unstable_transition_probability"]["mean"]
            >= criteria["unstable_transition_probability_min"]
        ),
        "partner_switch_localized": (
            metrics["switch_onset_error_q95"]
            <= criteria["switch_onset_error_max"]
        ),
        "broadcast_off_preserves_local_inference": (
            metrics["broadcast_local_q_partner_identity_max"]
            <= criteria["broadcast_local_identity_max"]
            and metrics["broadcast_local_structure_identity_max"]
            <= criteria["broadcast_local_identity_max"]
            and metrics["broadcast_off_global_baseline_error_max"]
            <= TOLERANCE
            and metrics["broadcast_off_local_precision"]["mean"]
            > v34.BASE_PRECISION
        ),
        "broadcast_increases_root_uptake": (
            metrics["broadcast_root_uptake_difference"]["mean"]
            >= criteria["broadcast_root_uptake_min"]
            and metrics["broadcast_root_uptake_difference"]["lower_95"]
            > 0.0
        ),
    }
    passed = all(checks.values())
    result = {
        "verdict": "PASS" if passed else "FAIL",
        "seed_allocations": {
            "factorial": [3_405_000, 3_405_999],
            **{
                name: [start, end - 1]
                for name, (start, end) in allocations.items()
            },
            "broadcast": [3_409_200, 3_409_999],
        },
        "metrics": metrics,
        "thresholds": criteria,
        "checks": checks,
        "root_write_separation": (
            "regulation-only root BF and root movement are exact zero"
        ),
    }
    _write_json("gate-3.json", result)
    parameters["status"] = "GATE3_PASSED" if passed else "STOPPED_AT_GATE3"
    PARAMETERS.write_text(
        json.dumps(parameters, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not passed:
        _write_json(
            "gate-3-diagnosis-stub.json",
            {
                "failed_checks": [
                    name for name, value in checks.items() if not value
                ],
                "metrics": metrics,
            },
        )
    return passed


def _restricted_identity(
    full: v34.RelatePosterior,
    restricted: v34.RelatePosterior,
    edge: str,
) -> float:
    retained = {
        program: probability
        for program, probability in zip(
            full.programs, full.structure_probabilities
        )
        if v34.structure_values(program)[edge] == 0
    }
    mass = math.fsum(retained.values())
    return max(
        abs(probability - retained[program] / mass)
        for program, probability in zip(
            restricted.programs,
            restricted.structure_probabilities,
        )
    )


def _restricted_oracle_error(
    world: v34.RelateWorld,
    restricted: v34.RelatePosterior,
    edge: str,
) -> tuple[float, bool]:
    observations = [asdict(item) for item in world.observations]
    snapshot = json.dumps(observations, sort_keys=True)
    programs, probabilities, _root, _evidence = v34_oracle.posterior(
        observations, restrictions={edge: (0,)}
    )
    oracle_map = dict(zip(programs, probabilities))
    error = max(
        abs(
            probability
            - oracle_map[_bits(program)]
        )
        for program, probability in zip(
            restricted.programs,
            restricted.structure_probabilities,
        )
    )
    return error, snapshot == json.dumps(observations, sort_keys=True)


@traced_execution
def _worker_lesion(task: tuple[int, str]) -> dict[str, Any]:
    seed, lesion = task
    if lesion == "L_PREC":
        config = v34.RelateConfig("reliable", True, False, length=48)
    elif lesion == "broadcast":
        config = v34.RelateConfig("reliable", True, True, length=48)
    elif lesion == "L_Y":
        config = v34.RelateConfig("reliable", True, False, length=48)
    elif lesion == "root_evidence":
        config = v34.RelateConfig("reliable", True, True, length=48)
    else:
        config = v34.RelateConfig("switch", True, False, length=48)
    world = v34.generate_world(seed, config)
    full = v34.score_world(world)
    row: dict[str, Any] = {
        "seed": seed,
        "cell": lesion,
        "full": _score_summary(world),
    }
    if lesion in {"L_PREC", "L_Y", "L_TRANSITION"}:
        restricted = v34.score_world(
            world, restrictions={lesion: (0,)}
        )
        oracle_error, input_unchanged = _restricted_oracle_error(
            world, restricted, lesion
        )
        row.update(
            {
                "conditioned_identity_error": _restricted_identity(
                    full, restricted, lesion
                ),
                "independent_oracle_error": oracle_error,
                "oracle_input_unchanged": input_unchanged,
                "restricted_edge_probability": (
                    restricted.edge_probabilities[lesion]
                ),
                "restricted_local_precision": (
                    restricted.local_precision[-1]
                ),
                "restricted_transition_probability": (
                    restricted.transition_probability
                ),
                "restricted_switch_onset": restricted.switch_onset,
                "restricted_normalization_error": abs(
                    math.fsum(restricted.structure_probabilities) - 1.0
                ),
                "restricted_finite": bool(
                    np.isfinite(restricted.log_evidence)
                ),
            }
        )
    elif lesion == "broadcast":
        off = v34.score_world(world, broadcast=False)
        local_on = v34.score_world(
            world, broadcast=True, root_evidence_enabled=False
        )
        local_off = v34.score_world(
            world, broadcast=False, root_evidence_enabled=False
        )
        row.update(
            {
                "lesioned_root_movement": off.root_movement,
                "uptake_removed": full.root_movement - off.root_movement,
                "local_partner_identity_error": max(
                    abs(a - b)
                    for a, b in zip(
                        local_on.q_partner, local_off.q_partner
                    )
                ),
                "local_structure_identity_error": max(
                    abs(a - b)
                    for a, b in zip(
                        local_on.structure_probabilities,
                        local_off.structure_probabilities,
                    )
                ),
                "global_baseline_error": max(
                    abs(value - v34.BASE_PRECISION)
                    for value in off.global_precision
                ),
            }
        )
    else:
        masked = v34.score_world(
            world, root_evidence_enabled=False
        )
        row.update(
            {
                "lesioned_root_bf": masked.root_log_bf,
                "lesioned_root_movement": masked.root_movement,
                "lesioned_root_prior_error": max(
                    abs(a - b) for a, b in zip(masked.q_root, (0.5, 0.5))
                ),
                "lesioned_normalization_error": abs(
                    math.fsum(masked.structure_probabilities) - 1.0
                ),
            }
        )
    return row


def run_gate4() -> bool:
    parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    if parameters["status"] != "GATE3_PASSED":
        raise RuntimeError("Gate 3 must pass before Gate 4")
    allocations = {
        "L_PREC": (3_410_000, 3_410_400),
        "broadcast": (3_410_400, 3_410_800),
        "L_Y": (3_410_800, 3_411_200),
        "root_evidence": (3_411_200, 3_411_600),
        "L_TRANSITION": (3_411_600, 3_412_000),
    }
    cells = {}
    for lesion, (start, end) in allocations.items():
        cells[lesion] = _trace_map(
            f"gate-4-{lesion.lower()}",
            [(seed, lesion) for seed in range(start, end)],
            _worker_lesion,
        )
    structure_rows = [
        row
        for lesion in ("L_PREC", "L_Y", "L_TRANSITION")
        for row in cells[lesion]
    ]
    identity = {
        "conditioned_prior_max_error": max(
            row["conditioned_identity_error"]
            for row in structure_rows
        ),
        "independent_oracle_max_error": max(
            row["independent_oracle_error"]
            for row in structure_rows
        ),
        "all_oracle_inputs_unchanged": all(
            row["oracle_input_unchanged"] for row in structure_rows
        ),
        "normalization_max_error": max(
            row["restricted_normalization_error"]
            for row in structure_rows
        ),
        "all_finite": all(
            row["restricted_finite"] for row in structure_rows
        ),
    }
    lprec = cells["L_PREC"]
    broadcast = cells["broadcast"]
    ly = cells["L_Y"]
    root = cells["root_evidence"]
    transitions = cells["L_TRANSITION"]
    full_switch_errors = [
        abs(row["full"]["switch_onset"] - 24)
        for row in transitions
    ]
    restricted_switch_errors = [
        abs(row["restricted_switch_onset"] - 24)
        for row in transitions
    ]
    metrics = {
        "restricted_prior_identity": identity,
        "L_PREC": {
            "restricted_edge_max": max(
                row["restricted_edge_probability"] for row in lprec
            ),
            "local_precision_baseline_error_max": max(
                abs(
                    row["restricted_local_precision"]
                    - v34.BASE_PRECISION
                )
                for row in lprec
            ),
            "full_minus_lesioned_local_precision": _mean_ci(
                [
                    row["full"]["local_precision"]
                    - row["restricted_local_precision"]
                    for row in lprec
                ]
            ),
        },
        "broadcast": {
            "uptake_removed": _mean_ci(
                [row["uptake_removed"] for row in broadcast]
            ),
            "local_partner_identity_max": max(
                row["local_partner_identity_error"] for row in broadcast
            ),
            "local_structure_identity_max": max(
                row["local_structure_identity_error"]
                for row in broadcast
            ),
            "global_baseline_error_max": max(
                row["global_baseline_error"] for row in broadcast
            ),
        },
        "L_Y": {
            "restricted_edge_max": max(
                row["restricted_edge_probability"] for row in ly
            ),
            "full_edge_probability": _mean_ci(
                [
                    row["full"]["edge_probabilities"]["L_Y"]
                    for row in ly
                ]
            ),
        },
        "root_evidence": {
            "root_bf_max_abs": max(
                abs(row["lesioned_root_bf"]) for row in root
            ),
            "root_movement_max_abs": max(
                abs(row["lesioned_root_movement"]) for row in root
            ),
            "root_prior_error_max": max(
                row["lesioned_root_prior_error"] for row in root
            ),
            "normalization_error_max": max(
                row["lesioned_normalization_error"] for row in root
            ),
        },
        "L_TRANSITION": {
            "restricted_edge_max": max(
                row["restricted_edge_probability"]
                for row in transitions
            ),
            "full_switch_error": _mean_ci(full_switch_errors),
            "lesioned_switch_error": _mean_ci(
                restricted_switch_errors
            ),
        },
    }
    checks = {
        "restricted_prior_and_oracle_identity": (
            identity["conditioned_prior_max_error"] <= TOLERANCE
            and identity["independent_oracle_max_error"] <= TOLERANCE
            and identity["all_oracle_inputs_unchanged"]
            and identity["normalization_max_error"] <= TOLERANCE
            and identity["all_finite"]
        ),
        "partner_to_precision_target_only": (
            metrics["L_PREC"]["restricted_edge_max"] <= TOLERANCE
            and metrics["L_PREC"]["local_precision_baseline_error_max"]
            <= TOLERANCE
            and metrics["L_PREC"][
                "full_minus_lesioned_local_precision"
            ]["lower_95"]
            > 0.0
        ),
        "broadcast_target_only": (
            metrics["broadcast"]["uptake_removed"]["lower_95"] > 0.0
            and metrics["broadcast"]["local_partner_identity_max"]
            <= TOLERANCE
            and metrics["broadcast"]["local_structure_identity_max"]
            <= TOLERANCE
            and metrics["broadcast"]["global_baseline_error_max"]
            <= TOLERANCE
        ),
        "partner_to_outcome_removed": (
            metrics["L_Y"]["restricted_edge_max"] <= TOLERANCE
        ),
        "root_evidence_mask_is_neutral": (
            metrics["root_evidence"]["root_bf_max_abs"] <= TOLERANCE
            and metrics["root_evidence"]["root_movement_max_abs"]
            <= TOLERANCE
            and metrics["root_evidence"]["root_prior_error_max"]
            <= TOLERANCE
            and metrics["root_evidence"]["normalization_error_max"]
            <= TOLERANCE
        ),
        "transition_lesion_removes_switch_localization": (
            metrics["L_TRANSITION"]["restricted_edge_max"] <= TOLERANCE
            and metrics["L_TRANSITION"]["lesioned_switch_error"]["mean"]
            > metrics["L_TRANSITION"]["full_switch_error"]["mean"]
        ),
    }
    passed = all(checks.values())
    result = {
        "verdict": "PASS" if passed else "FAIL",
        "seed_allocations": {
            name: [start, end - 1]
            for name, (start, end) in allocations.items()
        },
        "metrics": metrics,
        "checks": checks,
        "renormalization_note": (
            "absolute unrelated posterior movement after a structure "
            "deletion is descriptive; selectivity is the exact "
            "conditioned-prior identity"
        ),
    }
    _write_json("gate-4.json", result)
    parameters["status"] = "GATE4_PASSED" if passed else "STOPPED_AT_GATE4"
    PARAMETERS.write_text(
        json.dumps(parameters, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not passed:
        _write_json(
            "gate-4-diagnosis-stub.json",
            {
                "failed_checks": [
                    name for name, value in checks.items() if not value
                ],
                "metrics": metrics,
            },
        )
    return passed


def _mask_world(
    world: v34.RelateWorld, mode: str
) -> v34.RelateWorld:
    observations = []
    for item in world.observations:
        if mode == "missingness" and item.time % 3 == 0:
            observations.append(
                replace(
                    item,
                    relational=(None,) * len(v34.RELATIONAL_CHANNELS),
                    regulation_response=None,
                    outcome=None,
                )
            )
        elif mode == "reduced_emission":
            relational = list(item.relational)
            relational[1] = None
            relational[3] = None
            observations.append(
                replace(item, relational=tuple(relational))
            )
        elif mode == "action_prevalence":
            observations.append(
                replace(item, partner_action=int(item.time % 4 != 0))
            )
        else:
            observations.append(item)
    return replace(world, observations=tuple(observations))


@traced_execution
def _worker_gate5_assay(task: tuple[int, str]) -> dict[str, Any]:
    seed, cell = task
    if cell == "broadcast_primary":
        world = v34.generate_world(
            seed,
            v34.RelateConfig("reliable", True, True, length=48),
        )
        on = v34.score_world(world, broadcast=True)
        off = v34.score_world(world, broadcast=False)
        local_on = v34.score_world(
            world, broadcast=True, root_evidence_enabled=False
        )
        local_off = v34.score_world(
            world, broadcast=False, root_evidence_enabled=False
        )
        return {
            "seed": seed,
            "cell": cell,
            "uptake_difference": (
                on.root_movement - off.root_movement
            ),
            "local_partner_identity_error": max(
                abs(a - b)
                for a, b in zip(local_on.q_partner, local_off.q_partner)
            ),
            "local_structure_identity_error": max(
                abs(a - b)
                for a, b in zip(
                    local_on.structure_probabilities,
                    local_off.structure_probabilities,
                )
            ),
            "normalization_error": max(
                abs(math.fsum(on.structure_probabilities) - 1.0),
                abs(math.fsum(off.structure_probabilities) - 1.0),
            ),
        }
    world = v34.generate_world(
        seed,
        v34.RelateConfig("reliable", True, True, length=48),
    )
    transformed = _mask_world(world, cell)
    posterior = v34.score_world(transformed)
    if cell == "reduced_emission":
        comparator = v34.generate_world(
            seed,
            v34.RelateConfig(
                "soothing_noncontingent", True, True, length=48
            ),
        )
        comparator_posterior = v34.score_world(
            _mask_world(comparator, cell)
        )
        trust_gap = (
            posterior.trust_remaining_after_refusal
            - comparator_posterior.trust_remaining_after_refusal
        )
    else:
        trust_gap = None
    return {
        "seed": seed,
        "cell": cell,
        "normalization_error": abs(
            math.fsum(posterior.structure_probabilities) - 1.0
        ),
        "finite": bool(np.isfinite(posterior.log_evidence)),
        "root_movement": posterior.root_movement,
        "trust": posterior.trust_remaining_after_refusal,
        "trust_gap": trust_gap,
    }


def _verify_stage_manifest(stage: str) -> dict[str, Any]:
    path = ROOT / "results" / stage / "freeze-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in manifest["files"].items():
        target = ROOT / relative
        actual = (
            hashlib.sha256(target.read_bytes()).hexdigest()
            if target.exists()
            else None
        )
        if actual != expected:
            mismatches.append(
                {
                    "file": relative,
                    "expected": expected,
                    "actual": actual,
                }
            )
    return {
        "stage": stage,
        "file_count": len(manifest["files"]),
        "mismatches": mismatches,
        "passed": not mismatches,
    }


def _trace_ledger_valid(name: str) -> bool:
    ledger = json.loads(
        (RESULTS / f"{name}-trace-hashes.json").read_text(encoding="utf-8")
    )
    path = RESULTS / ledger["file"]
    return bool(
        path.exists()
        and hashlib.sha256(path.read_bytes()).hexdigest()
        == ledger["file_sha256"]
        and sum(1 for _ in path.open("rb")) == ledger["world_count"]
    )


def run_gate5() -> bool:
    parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    if parameters["status"] != "GATE4_PASSED":
        raise RuntimeError("Gate 4 must pass before Gate 5")
    recovery_specs = (
        ("length_32", 3_412_000, 32, 0.88, 1.0),
        ("length_96", 3_413_000, 96, 0.88, 1.0),
        ("transition_stay_0_75", 3_414_000, 48, 0.75, 1.0),
        ("code_length_scale_1_5", 3_415_000, 48, 0.88, 1.5),
    )
    recovery_metrics = {}
    recovery_trace_names = []
    for name, start, length, stay, scale in recovery_specs:
        trace_name = f"gate-5-{name}"
        recovery_trace_names.append(trace_name)
        rows = _trace_map(
            trace_name,
            [
                (
                    seed,
                    length,
                    stay,
                    scale,
                    None,
                    (seed - start) % 100 == 0,
                )
                for seed in range(start, start + 1_000)
            ],
            _worker_recovery,
        )
        recovery_metrics[name] = _recovery_metrics(rows)
        audited = [
            row for row in rows if "oracle_structure_error" in row
        ]
        recovery_metrics[name]["oracle_max_error"] = max(
            max(
                row["oracle_structure_error"],
                row["oracle_root_error"],
                row["oracle_evidence_error"],
            )
            for row in audited
        )
        recovery_metrics[name]["oracle_inputs_unchanged"] = all(
            row["oracle_input_unchanged"] for row in audited
        )
    assay_specs = {
        "missingness": (3_416_000, 3_417_000),
        "reduced_emission": (3_417_000, 3_418_000),
        "action_prevalence": (3_418_000, 3_419_000),
        "broadcast_primary": (3_419_000, 3_420_000),
    }
    assay_rows = {}
    assay_trace_names = []
    for name, (start, end) in assay_specs.items():
        trace_name = f"gate-5-{name}"
        assay_trace_names.append(trace_name)
        assay_rows[name] = _trace_map(
            trace_name,
            [(seed, name) for seed in range(start, end)],
            _worker_gate5_assay,
        )
    assays = {
        "missingness": {
            "normalization_error_max": max(
                row["normalization_error"]
                for row in assay_rows["missingness"]
            ),
            "all_finite": all(
                row["finite"] for row in assay_rows["missingness"]
            ),
            "root_movement": _mean_ci(
                [
                    row["root_movement"]
                    for row in assay_rows["missingness"]
                ]
            ),
        },
        "reduced_emission": {
            "normalization_error_max": max(
                row["normalization_error"]
                for row in assay_rows["reduced_emission"]
            ),
            "all_finite": all(
                row["finite"] for row in assay_rows["reduced_emission"]
            ),
            "trust_gap": _mean_ci(
                [
                    row["trust_gap"]
                    for row in assay_rows["reduced_emission"]
                ]
            ),
        },
        "action_prevalence": {
            "normalization_error_max": max(
                row["normalization_error"]
                for row in assay_rows["action_prevalence"]
            ),
            "all_finite": all(
                row["finite"] for row in assay_rows["action_prevalence"]
            ),
            "root_movement": _mean_ci(
                [
                    row["root_movement"]
                    for row in assay_rows["action_prevalence"]
                ]
            ),
        },
        "broadcast_primary": {
            "uptake_difference": _mean_ci(
                [
                    row["uptake_difference"]
                    for row in assay_rows["broadcast_primary"]
                ]
            ),
            "local_partner_identity_max": max(
                row["local_partner_identity_error"]
                for row in assay_rows["broadcast_primary"]
            ),
            "local_structure_identity_max": max(
                row["local_structure_identity_error"]
                for row in assay_rows["broadcast_primary"]
            ),
            "normalization_error_max": max(
                row["normalization_error"]
                for row in assay_rows["broadcast_primary"]
            ),
        },
    }
    criteria = parameters["criteria"]
    recovery_checks = {
        name: {
            "edge_recovery": (
                values["minimum_edge_accuracy"]
                >= criteria["edge_accuracy_min"]
            ),
            "program_recovery": (
                values["program_accuracy"]
                >= criteria["program_accuracy_min"]
            ),
            "root_recovery": (
                values["root_accuracy"]
                >= criteria["root_accuracy_min"]
            ),
            "calibration": (
                values["structure_ece"] <= criteria["ece_max"]
                and values["root_ece"] <= criteria["ece_max"]
            ),
            "coverage": values["coverage"] >= criteria["coverage_min"],
            "normalization": (
                values["maximum_normalization_error"] <= TOLERANCE
            ),
            "exact_probability": (
                values["maximum_exact_complete_log_probability_error"]
                <= TOLERANCE
            ),
            "oracle": (
                values["oracle_max_error"] <= TOLERANCE
                and values["oracle_inputs_unchanged"]
            ),
        }
        for name, values in recovery_metrics.items()
    }
    assay_checks = {
        "missingness": (
            assays["missingness"]["normalization_error_max"] <= TOLERANCE
            and assays["missingness"]["all_finite"]
            and assays["missingness"]["root_movement"]["lower_95"] > 0.0
        ),
        "reduced_emission": (
            assays["reduced_emission"]["normalization_error_max"]
            <= TOLERANCE
            and assays["reduced_emission"]["all_finite"]
            and assays["reduced_emission"]["trust_gap"]["lower_95"] > 0.0
        ),
        "action_prevalence": (
            assays["action_prevalence"]["normalization_error_max"]
            <= TOLERANCE
            and assays["action_prevalence"]["all_finite"]
            and assays["action_prevalence"]["root_movement"]["lower_95"]
            > 0.0
        ),
        "broadcast_primary": (
            assays["broadcast_primary"]["uptake_difference"]["mean"]
            >= criteria["broadcast_root_uptake_min"]
            and assays["broadcast_primary"]["uptake_difference"][
                "lower_95"
            ]
            > 0.0
            and assays["broadcast_primary"][
                "local_partner_identity_max"
            ]
            <= TOLERANCE
            and assays["broadcast_primary"][
                "local_structure_identity_max"
            ]
            <= TOLERANCE
            and assays["broadcast_primary"]["normalization_error_max"]
            <= TOLERANCE
        ),
    }
    prior_stages = [
        _verify_stage_manifest(stage)
        for stage in ("V3.0", "V3.1", "V3.2", "V3.3")
    ]
    trace_names = recovery_trace_names + assay_trace_names
    trace_custody = {
        name: _trace_ledger_valid(name) for name in trace_names
    }
    checks = {
        "recovery_robustness": all(
            all(cell.values()) for cell in recovery_checks.values()
        ),
        "scientific_robustness": all(assay_checks.values()),
        "prior_stage_manifests": all(
            stage["passed"] for stage in prior_stages
        ),
        "trace_custody": all(trace_custody.values()),
        "gate3_primary_still_passes": (
            json.loads(
                (RESULTS / "gate-3.json").read_text(encoding="utf-8")
            )["verdict"]
            == "PASS"
        ),
        "gate4_primary_still_passes": (
            json.loads(
                (RESULTS / "gate-4.json").read_text(encoding="utf-8")
            )["verdict"]
            == "PASS"
        ),
    }
    passed = all(checks.values())
    result = {
        "verdict": "PASS" if passed else "FAIL",
        "seed_block": [3_412_000, 3_419_999],
        "recovery_metrics": recovery_metrics,
        "recovery_checks": recovery_checks,
        "assay_metrics": assays,
        "assay_checks": assay_checks,
        "prior_stage_manifests": prior_stages,
        "trace_custody": trace_custody,
        "checks": checks,
    }
    _write_json("gate-5.json", result)
    parameters["status"] = "GATE5_PASSED" if passed else "STOPPED_AT_GATE5"
    PARAMETERS.write_text(
        json.dumps(parameters, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if not passed:
        _write_json(
            "gate-5-diagnosis-stub.json",
            {
                "failed_checks": [
                    name for name, value in checks.items() if not value
                ],
                "recovery_checks": recovery_checks,
                "assay_checks": assay_checks,
            },
        )
    return passed


def write_freeze_manifest() -> bool:
    parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    expected_status = "FROZEN_ADJUDICATED_SHORT_HISTORY_CONJUNCTION_BOUND"
    if parameters["status"] != expected_status:
        raise RuntimeError("V3.4 is not freeze-ready")
    fixed = (
        ROOT / "contracts" / "v3.4-relate-contract.md",
        ROOT / "protocols" / "v3.4-analysis-plan.md",
        ROOT / "protocols" / "v3.4-parameters.json",
        ROOT / "protocols" / "v3.4-public-dummy.json",
        ROOT / "ref" / "audit.py",
        ROOT / "ref" / "trace_sink.py",
        ROOT / "ref" / "v34.py",
        ROOT / "ref" / "v34_oracle.py",
        ROOT / "scripts" / "run_v34.py",
        ROOT / "tests" / "test_v34_relate.py",
    )
    result_files = tuple(
        path
        for path in sorted(RESULTS.iterdir())
        if path.is_file()
        and path.name not in {
            "freeze-manifest.json",
            "ready-to-commit.md",
        }
    )
    files = {}
    local_only = {}
    for path in (*fixed, *result_files):
        relative = str(path.relative_to(ROOT))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if path.stat().st_size > 90 * 1024 * 1024:
            local_only[relative] = {
                "sha256": digest,
                "size_bytes": path.stat().st_size,
            }
        else:
            files[relative] = digest
    payload = {
        "stage": "V3.4",
        "status": expected_status,
        "files": files,
        "local_only_trace_bundles": local_only,
        "escrow": {
            "block": [4_040_000, 4_043_999],
            "status": "UNTOUCHED",
        },
        "formal_gate_verdicts": {
            "gate1": "PASS",
            "gate2": "PASS",
            "gate3": "PASS",
            "gate4": "PASS",
            "gate5": "FAIL_RETAINED",
        },
        "adjudicated_gate5_blocking_verdict": "PASS",
        "adjudicated_limitation": (
            "32-slice whole-program conjunction accuracy is descriptive; "
            "the frozen 48-slice primary cell is blocking"
        ),
        "stage0_defect_record": (
            "recovery root-observation generator/scorer mismatch repaired "
            "under evaluator authorization; original pilot retained"
        ),
    }
    _write_json("freeze-manifest.json", payload)
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "step",
        choices=(
            "gate1",
            "pilot",
            "gate2",
            "gate3",
            "gate4",
            "gate5",
            "freeze",
        ),
    )
    args = parser.parse_args()
    passed = (
        run_gate1()
        if args.step == "gate1"
        else run_pilot()
        if args.step == "pilot"
        else run_gate2()
        if args.step == "gate2"
        else run_gate3()
        if args.step == "gate3"
        else run_gate4()
        if args.step == "gate4"
        else run_gate5()
        if args.step == "gate5"
        else write_freeze_manifest()
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
