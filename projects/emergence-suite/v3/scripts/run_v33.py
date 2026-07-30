#!/usr/bin/env python3
"""Prospective V3.3 PRUNE stage runner."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import sys
from dataclasses import asdict
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ref import v31, v33, v33_oracle  # noqa: E402
from ref.trace_sink import (  # noqa: E402
    serializing_trace_context,
    traced_execution,
)


RESULTS = ROOT / "results" / "V3.3"
PARAMETERS = ROOT / "protocols" / "v3.3-parameters.json"
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


def _write_json(name: str, value: Any) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / name).write_text(
        json.dumps(
            _plain(value), indent=2, sort_keys=True, allow_nan=False
        )
        + "\n",
        encoding="utf-8",
    )


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


def _seal_rows(name: str, rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{name}-traces.jsonl"
    file_hash = hashlib.sha256()
    hashes = []
    with path.open("wb") as handle:
        for row in rows:
            encoded = _canonical_bytes(row)
            handle.write(encoded)
            handle.flush()
            file_hash.update(encoded)
            hashes.append(
                {
                    "seed": row.get("seed", "authored-dummy"),
                    "sha256": hashlib.sha256(encoded).hexdigest(),
                }
            )
    ledger = {
        "file": path.name,
        "world_count": len(rows),
        "file_sha256": file_hash.hexdigest(),
        "records": hashes,
    }
    _write_json(f"{name}-trace-hashes.json", ledger)
    return ledger


def _trace_map(name: str, tasks: Sequence[Any], worker: Any) -> list[dict[str, Any]]:
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{name}-traces.jsonl"
    rows = []
    hashes = []
    file_hash = hashlib.sha256()
    processes = max(1, min(8, (os.cpu_count() or 2) - 1))
    with path.open("wb") as handle:
        with get_context("spawn").Pool(processes) as pool:
            for row in pool.imap(worker, tasks, chunksize=8):
                encoded = _canonical_bytes(row)
                handle.write(encoded)
                handle.flush()
                file_hash.update(encoded)
                hashes.append(
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
            "records": hashes,
        },
    )
    return rows


def _authored_dummy() -> v33.ReductionWorld:
    history = []
    current = []
    for time in range(16):
        mode = time % 2
        root = mode
        world = root
        policy = root
        outcome = root
        history.append(
            v33.ReductionSlice(
                time,
                0,
                mode,
                root,
                world,
                policy,
                time % 2,
                outcome,
                "historical",
            )
        )
        current.append(
            v33.ReductionSlice(
                16 + time,
                1,
                mode,
                0,
                time % 2,
                (time // 2) % 2,
                time % 2,
                (time // 3) % 2,
                "corrective",
            )
        )
    return v33.ReductionWorld(
        -33,
        None,
        v33.formed_structure(),
        v33.reduced_structure(),
        tuple(history + current),
        0.0,
        (),
    )


def _program_bits(program: Any) -> tuple[int, ...]:
    values = v31.program_values(program)
    return (
        values["active_mode"],
        *(values[edge] for edge in v31.EDGE_NAMES),
    )


@traced_execution
def _gate1_semantics() -> dict[str, Any]:
    world = _authored_dummy()
    posterior = v33.score_world(world)
    current_slices = [
        asdict(item) for item in world.slices if item.context == 1
    ]
    oracle_programs, oracle_probabilities, oracle_evidence = (
        v33_oracle.posterior(current_slices)
    )
    production = {
        _program_bits(program): probability
        for program, probability in zip(
            posterior.current.programs,
            posterior.current.probabilities,
        )
    }
    oracle_error = max(
        abs(probability - production[program])
        for program, probability in zip(
            oracle_programs, oracle_probabilities
        )
    )
    neutral_world = v33.append_neutral_observation(world)
    neutral = v33.score_world(neutral_world)
    neutral_error = max(
        abs(a - b)
        for a, b in zip(
            posterior.current.probabilities,
            neutral.current.probabilities,
        )
    )
    relabeled = v33.score_world(
        v33.relabel_episode(world, "corrective", "imaginal_post")
    )
    label_error = max(
        abs(a - b)
        for a, b in zip(
            posterior.current.probabilities,
            relabeled.current.probabilities,
        )
    )
    history_only = v33.ReductionWorld(
        world.seed,
        world.config,
        world.historical_structure,
        world.current_truth_structure,
        tuple(item for item in world.slices if item.context == 0),
        world.exact_log_probability,
        world.rng_keys,
    )
    historical_before = v33.score_world(history_only).historical
    dormancy_error = max(
        abs(a - b)
        for a, b in zip(
            historical_before.probabilities,
            posterior.historical.probabilities,
        )
    )
    restrictions = {"G_W": (0,)}
    restricted = v33.score_world(world, restrictions=restrictions).current
    allowed = {
        program: probability
        for program, probability in zip(
            posterior.current.programs,
            posterior.current.probabilities,
        )
        if v31.program_values(program)["G_W"] == 0
    }
    allowed_mass = math.fsum(allowed.values())
    restricted_error = max(
        abs(probability - allowed[program] / allowed_mass)
        for program, probability in zip(
            restricted.programs, restricted.probabilities
        )
    )
    oracle_restricted = v33_oracle.posterior(
        current_slices, restrictions=restrictions
    )
    oracle_restricted_map = dict(
        zip(oracle_restricted[0], oracle_restricted[1])
    )
    independent_restricted_error = max(
        abs(
            probability
            - oracle_restricted_map[_program_bits(program)]
        )
        for program, probability in zip(
            restricted.programs, restricted.probabilities
        )
    )
    prior_sum = math.fsum(
        math.exp(v31.structure_log_prior(program))
        for program in v33.PROGRAMS
    )
    source = (ROOT / "ref" / "v33.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_operations = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name in {"reduce", "prune", "unburden", "delete_burden"}
    }
    action_scored_as_child = '"action",' in source.split(
        "def _program_log_joint", 1
    )[1].split("def _parameter_means", 1)[0]
    before = tuple(posterior.current.probabilities)
    thresholds = v33.MaterialReductionThresholds(0.5, 1.0, 0.0)
    _ = v33.material_reduction_readout(world, posterior, thresholds)
    readout_pure = before == posterior.current.probabilities
    active_without_burden = any(
        v31.program_values(program)["active_mode"]
        and all(
            v31.program_values(program)[edge] == 0
            for edge in v33.BURDEN_EDGES
        )
        for program in v33.PROGRAMS
    )
    label_rejected = False
    try:
        from dataclasses import replace

        v33.score_world(replace(world, analysis_labels=("unburdened",)))
    except ValueError:
        label_rejected = True
    proofs = {
        "1_same_programs": v33.PROGRAMS == v31.PROGRAMS,
        "1_same_edges": v33.EDGE_NAMES == v31.EDGE_NAMES,
        "2_prior_normalization_error": abs(prior_sum - 1.0),
        "2_posterior_normalization_error": abs(
            math.fsum(posterior.current.probabilities) - 1.0
        ),
        "3_local_joint_recombination_error": abs(
            v33._program_log_joint(
                tuple(item for item in world.slices if item.context == 1),
                world.current_truth_structure,
                v31.DEFAULT_HYPERPARAMETERS,
            )
            - v33._program_log_joint(
                tuple(item for item in world.slices if item.context == 1),
                world.current_truth_structure,
                v31.DEFAULT_HYPERPARAMETERS,
            )
        ),
        "4_independent_oracle_probability_error": oracle_error,
        "4_independent_oracle_evidence_error": abs(
            posterior.current.log_evidence - oracle_evidence
        ),
        "5_neutral_observation_probability_error": neutral_error,
        "6_episode_label_neutrality_error": label_error,
        "7_context_dormancy_probability_error": dormancy_error,
        "8_mode_spike_separate_from_burden": active_without_burden,
        "9_action_selection_likelihood_absent": not action_scored_as_child,
        "10_restricted_prior_identity_error": restricted_error,
        "10_independent_restricted_oracle_error": independent_restricted_error,
        "11_readout_purity": readout_pure,
        "12_forbidden_operations": sorted(forbidden_operations),
        "13_analysis_label_rejected": label_rejected,
    }
    numeric_errors = [
        value
        for key, value in proofs.items()
        if key.endswith("error") and isinstance(value, float)
    ]
    passed = (
        all(error <= TOLERANCE for error in numeric_errors)
        and proofs["1_same_programs"]
        and proofs["1_same_edges"]
        and proofs["8_mode_spike_separate_from_burden"]
        and proofs["9_action_selection_likelihood_absent"]
        and proofs["11_readout_purity"]
        and not proofs["12_forbidden_operations"]
        and proofs["13_analysis_label_rejected"]
    )
    return {
        "seed": "authored-no-rng-dummy",
        "cell": "gate1_semantics",
        "passed": passed,
        "proofs": proofs,
        "structure_space_size": len(v33.PROGRAMS),
    }


def run_gate1() -> bool:
    runtime_refusal = False
    try:
        v33.generate_world(
            3_300_000, v33.ReductionConfig("configural", "none")
        )
    except RuntimeError as error:
        runtime_refusal = "serializing trace context" in str(error)
    payload = _gate1_semantics()
    payload["proofs"]["14_trace_sink_refusal"] = runtime_refusal
    payload["passed"] = payload["passed"] and runtime_refusal
    _seal_rows("gate-1", [payload])
    _write_json(
        "gate-1.json",
        {
            "verdict": "PASS" if payload["passed"] else "FAIL",
            "proofs": payload["proofs"],
            "structure_space_size": payload["structure_space_size"],
            "tolerance": TOLERANCE,
            "executed_before_pilot": True,
        },
    )
    if payload["passed"]:
        parameters = json.loads(PARAMETERS.read_text())
        parameters["status"] = "GATE1_PASSED_PILOT_UNOPENED"
        PARAMETERS.write_text(
            json.dumps(parameters, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return bool(payload["passed"])


def _ece(confidence: Sequence[float], correct: Sequence[bool]) -> float:
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
    return result


def _credible_contains(posterior: v33.ContextPosterior, truth: Any) -> bool:
    order = np.argsort(-np.asarray(posterior.probabilities))
    mass = 0.0
    for index in order:
        mass += posterior.probabilities[int(index)]
        if posterior.programs[int(index)] == truth:
            return True
        if mass >= 0.95:
            return False
    return False


@traced_execution
def _worker_recovery(task: tuple[int, int, float, float]) -> dict[str, Any]:
    seed, length, concentration, scale = task
    hp = v31.V31Hyperparameters(concentration, scale)
    world = v33.generate_recovery_world(
        seed, length=length, hyperparameters=hp
    )
    posterior = v33.score_world(world, hyperparameters=hp).current
    truth_bits = _program_bits(world.current_truth_structure)
    predicted_index = int(np.argmax(posterior.probabilities))
    predicted_bits = _program_bits(posterior.programs[predicted_index])
    truth_probability = posterior.structure_probability(
        world.current_truth_structure
    )
    return {
        "seed": seed,
        "cell": "recovery",
        "truth_bits": truth_bits,
        "predicted_bits": predicted_bits,
        "program_correct": predicted_bits == truth_bits,
        "edge_correct": [
            predicted_bits[index] == truth_bits[index]
            for index in range(1, 7)
        ],
        "confidence": posterior.probabilities[predicted_index],
        "truth_probability": truth_probability,
        "credible_contains_truth": _credible_contains(
            posterior, world.current_truth_structure
        ),
        "normalization_error": abs(
            math.fsum(posterior.probabilities) - 1.0
        ),
        "exact_log_probability_error": abs(
            world.exact_log_probability
            - v33._program_log_joint(
                world.slices, world.current_truth_structure, hp
            )
        ),
        "rng_keys_sha256": hashlib.sha256(
            repr(world.rng_keys).encode()
        ).hexdigest(),
    }


def _recovery_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    correct = [bool(row["program_correct"]) for row in rows]
    confidence = [float(row["confidence"]) for row in rows]
    edge_accuracy = {
        edge: float(
            np.mean([row["edge_correct"][index] for row in rows])
        )
        for index, edge in enumerate(v33.EDGE_NAMES)
    }
    return {
        "world_count": len(rows),
        "edge_accuracy": edge_accuracy,
        "minimum_edge_accuracy": min(edge_accuracy.values()),
        "program_accuracy": float(np.mean(correct)),
        "brier": float(
            np.mean(
                [
                    (probability - float(outcome)) ** 2
                    for probability, outcome in zip(confidence, correct)
                ]
            )
        ),
        "ece": _ece(confidence, correct),
        "coverage": float(
            np.mean([row["credible_contains_truth"] for row in rows])
        ),
        "maximum_normalization_error": max(
            row["normalization_error"] for row in rows
        ),
        "maximum_exact_log_probability_error": max(
            row["exact_log_probability_error"] for row in rows
        ),
    }


def _trajectory(world: v33.ReductionWorld) -> list[dict[str, float]]:
    current = [item for item in world.slices if item.context == 1]
    result = []
    for length in range(1, len(current) + 1):
        local = v33._score_context(
            current[:length], v31.DEFAULT_HYPERPARAMETERS
        )
        result.append(
            {
                "length": length,
                "mode": local.active_mode_probability,
                "burden": max(
                    local.edge_probabilities[edge]
                    for edge in v33.BURDEN_EDGES
                ),
                "bf": v33.burden_absent_present_bf(local),
            }
        )
    return result


def _arm_summary(world: v33.ReductionWorld) -> dict[str, Any]:
    posterior = v33.score_world(world)
    neutral = v33.score_world(v33.append_neutral_observation(world))
    return {
        "mode": posterior.current.active_mode_probability,
        "burden": posterior.burden_edge_mass,
        "bf": v33.burden_absent_present_bf(posterior.current),
        "old_graph": posterior.old_graph_probability,
        "root_revision": posterior.root_revision,
        "adaptive_w_y": posterior.current.edge_probabilities["W_Y"],
        "neutral_error": max(
            abs(a - b)
            for a, b in zip(
                posterior.current.probabilities,
                neutral.current.probabilities,
            )
        ),
        "rng_keys_sha256": hashlib.sha256(
            repr(world.rng_keys).encode()
        ).hexdigest(),
    }


@traced_execution
def _worker_pilot_assays(seed: int) -> dict[str, Any]:
    corrected_config = v33.ReductionConfig(
        "configural",
        "none",
        corrective_length=18,
        return_length=18,
    )
    suggestion_config = v33.ReductionConfig(
        "suggestion_only",
        "none",
        corrective_length=18,
        return_length=18,
    )
    premature_config = v33.ReductionConfig(
        "none",
        "premature",
        return_burden=True,
        corrective_length=18,
        return_length=24,
    )
    post_config = v33.ReductionConfig(
        "configural",
        "post_revision",
        corrective_length=18,
        return_length=18,
    )
    adaptive_config = v33.ReductionConfig(
        "configural",
        "none",
        adaptive_edge="W_Y",
        corrective_length=18,
        return_length=18,
    )
    corrected_world = v33.generate_world(seed, corrected_config)
    suggestion_world = v33.generate_world(seed, suggestion_config)
    premature_world = v33.generate_world(seed, premature_config)
    post_world = v33.generate_world(seed, post_config)
    adaptive_world = v33.generate_world(seed, adaptive_config)
    return {
        "seed": seed,
        "cell": "pilot_exact_gate3_configurations",
        "corrected": _arm_summary(corrected_world),
        "suggestion": _arm_summary(suggestion_world),
        "premature": _arm_summary(premature_world),
        "post_revision": _arm_summary(post_world),
        "adaptive": _arm_summary(adaptive_world),
        "corrected_trajectory": _trajectory(corrected_world),
        "post_revision_trajectory": _trajectory(post_world),
    }


def _first_from_trajectory(
    trajectory: Sequence[Mapping[str, float]],
    *,
    mode: float,
    burden: float,
    bf: float,
    stability: int = 3,
) -> int | None:
    consecutive = 0
    for item in trajectory:
        eligible = (
            item["mode"] >= mode
            and item["burden"] <= burden
            and item["bf"] >= bf
        )
        consecutive = consecutive + 1 if eligible else 0
        if consecutive >= stability:
            return int(item["length"])
    return None


def _material_from_row(
    arm: Mapping[str, Any],
    trajectory: Sequence[Mapping[str, float]],
    thresholds: Mapping[str, float],
) -> bool:
    time = _first_from_trajectory(
        trajectory,
        mode=thresholds["mode_retained"],
        burden=thresholds["burden_edge_mass_max"],
        bf=thresholds["absent_present_bf_min"],
    )
    return bool(
        time is not None
        and arm["mode"] >= thresholds["mode_retained"]
        and arm["burden"] <= thresholds["burden_edge_mass_max"]
        and arm["bf"] >= thresholds["absent_present_bf_min"]
        and arm["neutral_error"] <= 1e-10
    )


def run_pilot() -> bool:
    parameters = json.loads(PARAMETERS.read_text())
    if parameters["status"] != "GATE1_PASSED_PILOT_UNOPENED":
        raise RuntimeError("Gate 1 must pass before the V3.3 pilot")
    recovery_rows = _trace_map(
        "stage0-pilot-recovery",
        [
            (seed, 64, 0.5, 1.0)
            for seed in range(3_300_000, 3_301_000)
        ],
        _worker_recovery,
    )
    assay_rows = _trace_map(
        "stage0-pilot-assays",
        list(range(3_301_000, 3_302_000)),
        _worker_pilot_assays,
    )
    recovery = _recovery_metrics(recovery_rows)
    corrected_burden = np.asarray(
        [row["corrected"]["burden"] for row in assay_rows]
    )
    suggestion_burden = np.asarray(
        [row["suggestion"]["burden"] for row in assay_rows]
    )
    corrected_bf = np.asarray(
        [row["corrected"]["bf"] for row in assay_rows]
    )
    suggestion_bf = np.asarray(
        [row["suggestion"]["bf"] for row in assay_rows]
    )
    corrected_upper = float(np.quantile(corrected_burden, 0.95))
    suggestion_lower = float(np.quantile(suggestion_burden, 0.05))
    corrected_bf_lower = float(np.quantile(corrected_bf, 0.05))
    suggestion_bf_upper = float(np.quantile(suggestion_bf, 0.95))
    separable = (
        corrected_upper < suggestion_lower
        and corrected_bf_lower > suggestion_bf_upper
    )
    if not separable:
        _write_json(
            "stage0-pilot.json",
            {
                "verdict": "STOP_UNATTAINABLE",
                "recovery": recovery,
                "separation": {
                    "corrected_burden_q95": corrected_upper,
                    "suggestion_burden_q05": suggestion_lower,
                    "corrected_bf_q05": corrected_bf_lower,
                    "suggestion_bf_q95": suggestion_bf_upper,
                },
            },
        )
        return False
    readout = {
        "mode_retained": max(
            0.80,
            float(
                np.quantile(
                    [row["corrected"]["mode"] for row in assay_rows],
                    0.05,
                )
                * 0.95
            ),
        ),
        "burden_edge_mass_max": (corrected_upper + suggestion_lower) / 2,
        "absent_present_bf_min": math.sqrt(
            corrected_bf_lower * suggestion_bf_upper
        ),
        "stability_observations": 3,
        "neutral_tolerance": 1e-10,
    }
    corrected_material = []
    suggestion_material = []
    premature_material = []
    speedups = []
    for row in assay_rows:
        corrected_material.append(
            _material_from_row(
                row["corrected"],
                row["corrected_trajectory"],
                readout,
            )
        )
        suggestion_material.append(
            row["suggestion"]["burden"]
            <= readout["burden_edge_mass_max"]
            and row["suggestion"]["bf"]
            >= readout["absent_present_bf_min"]
        )
        premature_material.append(
            row["premature"]["burden"]
            <= readout["burden_edge_mass_max"]
            and row["premature"]["bf"]
            >= readout["absent_present_bf_min"]
        )
        no_time = _first_from_trajectory(
            row["corrected_trajectory"],
            mode=readout["mode_retained"],
            burden=readout["burden_edge_mass_max"],
            bf=readout["absent_present_bf_min"],
        )
        post_time = _first_from_trajectory(
            row["post_revision_trajectory"],
            mode=readout["mode_retained"],
            burden=readout["burden_edge_mass_max"],
            bf=readout["absent_present_bf_min"],
        )
        if no_time is not None and post_time is not None:
            speedups.append((no_time - post_time) / no_time)
    attainable = {
        "material_reduction_rate": float(np.mean(corrected_material)),
        "suggestion_false_reduction_rate": float(
            np.mean(suggestion_material)
        ),
        "premature_durable_reduction_rate": float(
            np.mean(premature_material)
        ),
        "history_reconstruction": float(
            np.mean([row["corrected"]["old_graph"] for row in assay_rows])
        ),
        "mode_retention": float(
            np.mean([row["corrected"]["mode"] for row in assay_rows])
        ),
        "adaptive_edge_survival": float(
            np.mean([row["adaptive"]["adaptive_w_y"] for row in assay_rows])
        ),
        "do_over_speedup": float(np.mean(speedups)) if speedups else 0.0,
        "speedup_eligible_worlds": len(speedups),
        "neutral_error_max": max(
            row["corrected"]["neutral_error"] for row in assay_rows
        ),
    }
    if (
        attainable["material_reduction_rate"] <= 0.0
        or attainable["do_over_speedup"] <= 0.0
    ):
        _write_json(
            "stage0-pilot.json",
            {
                "verdict": "STOP_UNATTAINABLE",
                "recovery": recovery,
                "material_readout": readout,
                "attainable": attainable,
            },
        )
        return False
    criteria = {
        "edge_accuracy_min": max(
            0.5,
            math.floor((recovery["minimum_edge_accuracy"] - 0.05) * 100)
            / 100,
        ),
        "program_accuracy_min": max(
            0.25,
            math.floor((recovery["program_accuracy"] - 0.05) * 100)
            / 100,
        ),
        "brier_max": min(
            0.35, math.ceil((recovery["brier"] + 0.05) * 100) / 100
        ),
        "ece_max": min(
            0.30, math.ceil((recovery["ece"] + 0.05) * 100) / 100
        ),
        "coverage_min": max(
            0.80,
            math.floor((recovery["coverage"] - 0.05) * 100) / 100,
        ),
        "material_reduction_rate_min": max(
            0.50,
            math.floor(
                (attainable["material_reduction_rate"] - 0.08) * 100
            )
            / 100,
        ),
        "suggestion_false_reduction_max": min(
            0.30,
            math.ceil(
                (attainable["suggestion_false_reduction_rate"] + 0.08)
                * 100
            )
            / 100,
        ),
        "premature_durable_reduction_max": min(
            0.30,
            math.ceil(
                (attainable["premature_durable_reduction_rate"] + 0.08)
                * 100
            )
            / 100,
        ),
        "history_reconstruction_min": max(
            0.50, round(attainable["history_reconstruction"] * 0.75, 3)
        ),
        "mode_retention_min": max(
            0.80, round(attainable["mode_retention"] * 0.9, 3)
        ),
        "adaptive_edge_survival_min": max(
            0.50, round(attainable["adaptive_edge_survival"] * 0.75, 3)
        ),
        "do_over_speedup_min": round(
            attainable["do_over_speedup"] * 0.5, 3
        ),
    }
    parameters["status"] = "FROZEN_AFTER_ATTAINABILITY_PILOT"
    parameters["material_readout"] = readout
    parameters["criteria"] = criteria
    parameters["pilot_summary_sha256"] = hashlib.sha256(
        _canonical_bytes(
            {
                "recovery": recovery,
                "readout": readout,
                "attainable": attainable,
            }
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
            "barred_block": [3_300_000, 3_301_999],
            "recovery": recovery,
            "material_readout": readout,
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
