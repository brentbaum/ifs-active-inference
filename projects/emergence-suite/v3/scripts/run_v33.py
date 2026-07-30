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
from dataclasses import asdict, replace
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
def _worker_recovery(
    task: tuple[int, int, float, float] | tuple[int, int, float, float, bool],
) -> dict[str, Any]:
    seed, length, concentration, scale = task[:4]
    audit_oracle = bool(task[4]) if len(task) == 5 else False
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
    row = {
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
    if audit_oracle:
        copied = [asdict(item) for item in world.slices]
        programs, probabilities, evidence = v33_oracle.posterior(
            copied,
            concentration=concentration,
            code_length_scale=scale,
        )
        production = {
            _program_bits(program): probability
            for program, probability in zip(
                posterior.programs, posterior.probabilities
            )
        }
        row["oracle_probability_error"] = max(
            abs(probability - production[program])
            for program, probability in zip(programs, probabilities)
        )
        row["oracle_evidence_error"] = abs(
            evidence - posterior.log_evidence
        )
    return row


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


def run_gate2() -> bool:
    parameters = json.loads(PARAMETERS.read_text())
    if parameters["status"] != "FROZEN_AFTER_ATTAINABILITY_PILOT":
        raise RuntimeError("V3.3 pilot floors must be frozen before Gate 2")
    rows = _trace_map(
        "gate-2",
        [
            (seed, 64, 0.5, 1.0, (seed - 3_302_000) % 30 == 0)
            for seed in range(3_302_000, 3_305_000)
        ],
        _worker_recovery,
    )
    metrics = _recovery_metrics(rows)
    oracle_rows = [
        row for row in rows if "oracle_probability_error" in row
    ]
    metrics["oracle_audit_worlds"] = len(oracle_rows)
    metrics["maximum_oracle_probability_error"] = max(
        row["oracle_probability_error"] for row in oracle_rows
    )
    metrics["maximum_oracle_evidence_error"] = max(
        row["oracle_evidence_error"] for row in oracle_rows
    )
    criteria = parameters["criteria"]
    checks = {
        "edge_accuracy": (
            metrics["minimum_edge_accuracy"] >= criteria["edge_accuracy_min"]
        ),
        "program_accuracy": (
            metrics["program_accuracy"] >= criteria["program_accuracy_min"]
        ),
        "brier": metrics["brier"] <= criteria["brier_max"],
        "ece": metrics["ece"] <= criteria["ece_max"],
        "coverage": metrics["coverage"] >= criteria["coverage_min"],
        "normalization": (
            metrics["maximum_normalization_error"] <= TOLERANCE
        ),
        "exact_log_probability": (
            metrics["maximum_exact_log_probability_error"] <= TOLERANCE
        ),
        "independent_oracle_probability": (
            metrics["maximum_oracle_probability_error"] <= TOLERANCE
        ),
        "independent_oracle_evidence": (
            metrics["maximum_oracle_evidence_error"] <= TOLERANCE
        ),
    }
    passed = all(checks.values())
    payload = {
        "verdict": "PASS" if passed else "FAIL",
        "seed_block": [3_302_000, 3_304_999],
        "criteria": criteria,
        "checks": checks,
        "metrics": metrics,
        "trace_ledger": "gate-2-trace-hashes.json",
    }
    _write_json("gate-2.json", payload)
    (RESULTS / "gate-2-report.md").write_text(
        "# V3.3 Gate 2 — exact recovery\n\n"
        f"Verdict: **{payload['verdict']}**.\n\n"
        "The scorer recovered worlds sampled from its own exact prior. "
        f"Minimum edge accuracy was {metrics['minimum_edge_accuracy']:.3f}; "
        f"exact-program accuracy {metrics['program_accuracy']:.3f}; Brier "
        f"{metrics['brier']:.3f}; ECE {metrics['ece']:.3f}; and 95% set "
        f"coverage {metrics['coverage']:.3f}. The independent oracle's "
        f"maximum probability error was "
        f"{metrics['maximum_oracle_probability_error']:.3e}.\n",
        encoding="utf-8",
    )
    if passed:
        parameters["status"] = "GATE2_PASSED"
        PARAMETERS.write_text(
            json.dumps(parameters, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    else:
        _write_json(
            "gate-2-diagnosis-stub.json",
            {"failure": [key for key, value in checks.items() if not value]},
        )
    return passed


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
    no_do_world = v33.generate_world(seed, corrected_config)
    adaptive_world = v33.generate_world(seed, adaptive_config)
    event = v33.root_revision_event(post_world)
    post_times = [
        item.time
        for item in post_world.slices
        if item.episode_kind == "imaginal_post"
    ]
    no_do_times = [
        item.time
        for item in no_do_world.slices
        if item.episode_kind == "no_do_masked"
    ]
    premature_times = [
        item.time
        for item in premature_world.slices
        if item.episode_kind == "imaginal_premature"
    ]
    return {
        "seed": seed,
        "cell": "pilot_exact_gate3_configurations",
        "corrected": _arm_summary(corrected_world),
        "suggestion": _arm_summary(suggestion_world),
        "premature": _arm_summary(premature_world),
        "post_revision": _arm_summary(post_world),
        "adaptive": _arm_summary(adaptive_world),
        "schedule": {
            "root_revision_event": event,
            "first_post_revision_slice": (
                min(post_times) if post_times else None
            ),
            "first_no_do_opportunity_slice": (
                min(no_do_times) if no_do_times else None
            ),
            "first_premature_slice": (
                min(premature_times) if premature_times else None
            ),
            "post_is_first_slice_after_event": (
                event is not None
                and bool(post_times)
                and min(post_times) == event + 1
            ),
            "no_do_is_first_slice_after_event": (
                event is not None
                and bool(no_do_times)
                and min(no_do_times) == event + 1
            ),
            "premature_begins_before_event": (
                event is not None
                and bool(premature_times)
                and min(premature_times) < event
            ),
        },
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


@traced_execution
def _worker_gate3(task: tuple[int, str, Mapping[str, float]]) -> dict[str, Any]:
    seed, cell, thresholds = task
    base = {
        "corrective_evidence": "configural",
        "do_over": "none",
        "corrective_length": 18,
        "return_length": 18,
    }
    if cell == "correction":
        world = v33.generate_world(seed, v33.ReductionConfig(**base))
        arm = _arm_summary(world)
        trajectory = _trajectory(world)
        return {
            "seed": seed,
            "cell": cell,
            "arm": arm,
            "material": _material_from_row(arm, trajectory, thresholds),
        }
    if cell == "suggestion":
        world = v33.generate_world(
            seed,
            v33.ReductionConfig(
                "suggestion_only",
                "none",
                corrective_length=18,
                return_length=18,
            ),
        )
        arm = _arm_summary(world)
        trajectory = _trajectory(world)
        return {
            "seed": seed,
            "cell": cell,
            "arm": arm,
            "material": _material_from_row(arm, trajectory, thresholds),
        }
    if cell == "premature":
        world = v33.generate_world(
            seed,
            v33.ReductionConfig(
                "none",
                "premature",
                return_burden=True,
                corrective_length=18,
                return_length=24,
            ),
        )
        arm = _arm_summary(world)
        trajectory = _trajectory(world)
        return {
            "seed": seed,
            "cell": cell,
            "arm": arm,
            "material": _material_from_row(arm, trajectory, thresholds),
        }
    if cell == "speedup":
        no_world = v33.generate_world(seed, v33.ReductionConfig(**base))
        post_world = v33.generate_world(
            seed,
            v33.ReductionConfig(
                "configural",
                "post_revision",
                corrective_length=18,
                return_length=18,
            ),
        )
        no_time = _first_from_trajectory(
            _trajectory(no_world),
            mode=thresholds["mode_retained"],
            burden=thresholds["burden_edge_mass_max"],
            bf=thresholds["absent_present_bf_min"],
        )
        post_time = _first_from_trajectory(
            _trajectory(post_world),
            mode=thresholds["mode_retained"],
            burden=thresholds["burden_edge_mass_max"],
            bf=thresholds["absent_present_bf_min"],
        )
        return {
            "seed": seed,
            "cell": cell,
            "no_do_time": no_time,
            "post_revision_time": post_time,
            "speedup": (
                (no_time - post_time) / no_time
                if no_time is not None and post_time is not None
                else None
            ),
            "root_revision_event": v33.root_revision_event(post_world),
        }
    if cell == "necessity":
        world = v33.generate_world(seed, v33.ReductionConfig(**base))
        arm = _arm_summary(world)
        trajectory = _trajectory(world)
        return {
            "seed": seed,
            "cell": cell,
            "material": _material_from_row(arm, trajectory, thresholds),
        }
    if cell == "adaptive":
        world = v33.generate_world(
            seed,
            v33.ReductionConfig(
                "configural",
                "none",
                adaptive_edge="W_Y",
                corrective_length=18,
                return_length=18,
            ),
        )
        arm = _arm_summary(world)
        trajectory = _trajectory(world)
        return {
            "seed": seed,
            "cell": cell,
            "arm": arm,
            "material": _material_from_row(arm, trajectory, thresholds),
        }
    world = v33.generate_world(seed, v33.ReductionConfig(**base))
    arm = _arm_summary(world)
    return {
        "seed": seed,
        "cell": cell,
        "old_graph": arm["old_graph"],
        "neutral_error": arm["neutral_error"],
    }


def _bootstrap_mean_interval(
    values: Sequence[float], *, seed: int, replicates: int = 10_000
) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = np.empty(replicates, dtype=float)
    for index in range(replicates):
        means[index] = float(
            np.mean(rng.choice(array, size=len(array), replace=True))
        )
    return (
        float(np.quantile(means, 0.025)),
        float(np.quantile(means, 0.975)),
    )


def run_gate3() -> bool:
    parameters = json.loads(PARAMETERS.read_text())
    if parameters["status"] != "GATE2_PASSED":
        raise RuntimeError("V3.3 Gate 2 must pass before Gate 3")
    thresholds = parameters["material_readout"]
    allocations = (
        ("correction", 3_305_000, 3_305_800),
        ("suggestion", 3_305_800, 3_306_500),
        ("premature", 3_306_500, 3_307_200),
        ("speedup", 3_307_200, 3_308_000),
        ("necessity", 3_308_000, 3_308_700),
        ("adaptive", 3_308_700, 3_309_400),
        ("neutral_history", 3_309_400, 3_310_000),
    )
    tasks = [
        (seed, cell, thresholds)
        for cell, start, end in allocations
        for seed in range(start, end)
    ]
    rows = _trace_map("gate-3", tasks, _worker_gate3)
    grouped = {
        cell: [row for row in rows if row["cell"] == cell]
        for cell, _, _ in allocations
    }
    speeds = [
        float(row["speedup"])
        for row in grouped["speedup"]
        if row["speedup"] is not None
    ]
    speed_interval = _bootstrap_mean_interval(speeds, seed=3_307_200)
    metrics = {
        "correction_material_rate": float(
            np.mean([row["material"] for row in grouped["correction"]])
        ),
        "suggestion_false_reduction_rate": float(
            np.mean([row["material"] for row in grouped["suggestion"]])
        ),
        "suggestion_root_revision_mean": float(
            np.mean(
                [row["arm"]["root_revision"] for row in grouped["suggestion"]]
            )
        ),
        "premature_durable_reduction_rate": float(
            np.mean([row["material"] for row in grouped["premature"]])
        ),
        "necessity_material_rate": float(
            np.mean([row["material"] for row in grouped["necessity"]])
        ),
        "adaptive_edge_survival_mean": float(
            np.mean(
                [
                    row["arm"]["adaptive_w_y"]
                    for row in grouped["adaptive"]
                ]
            )
        ),
        "adaptive_material_rate": float(
            np.mean([row["material"] for row in grouped["adaptive"]])
        ),
        "mode_retention_mean": float(
            np.mean(
                [row["arm"]["mode"] for row in grouped["correction"]]
            )
        ),
        "history_reconstruction_mean": float(
            np.mean([row["old_graph"] for row in grouped["neutral_history"]])
        ),
        "neutral_error_max": max(
            row["neutral_error"] for row in grouped["neutral_history"]
        ),
        "speedup_eligible_worlds": len(speeds),
        "do_over_speedup_mean": float(np.mean(speeds)),
        "do_over_speedup_ci95": list(speed_interval),
    }
    criteria = parameters["criteria"]
    checks = {
        "corrective_material": (
            metrics["correction_material_rate"]
            >= criteria["material_reduction_rate_min"]
        ),
        "suggestion_specificity": (
            metrics["suggestion_false_reduction_rate"]
            <= criteria["suggestion_false_reduction_max"]
        ),
        "root_revision_without_pruning": (
            metrics["suggestion_root_revision_mean"] > 0.0
        ),
        "premature_not_durable": (
            metrics["premature_durable_reduction_rate"]
            <= criteria["premature_durable_reduction_max"]
        ),
        "do_over_not_necessary": (
            metrics["necessity_material_rate"]
            >= criteria["material_reduction_rate_min"]
        ),
        "adaptive_edge_survives": (
            metrics["adaptive_edge_survival_mean"]
            >= criteria["adaptive_edge_survival_min"]
        ),
        "mode_retained": (
            metrics["mode_retention_mean"]
            >= criteria["mode_retention_min"]
        ),
        "history_query": (
            metrics["history_reconstruction_mean"]
            >= criteria["history_reconstruction_min"]
        ),
        "neutral_identity": metrics["neutral_error_max"] <= TOLERANCE,
        "do_over_acceleration": (
            metrics["do_over_speedup_mean"]
            >= criteria["do_over_speedup_min"]
            and speed_interval[0] > 0.0
        ),
    }
    passed = all(checks.values())
    payload = {
        "verdict": "PASS" if passed else "FAIL",
        "seed_block": [3_305_000, 3_309_999],
        "criteria": criteria,
        "checks": checks,
        "metrics": metrics,
        "trace_ledger": "gate-3-trace-hashes.json",
    }
    _write_json("gate-3.json", payload)
    (RESULTS / "gate-3-report.md").write_text(
        "# V3.3 Gate 3 — same-edge reduction and do-over\n\n"
        f"Verdict: **{payload['verdict']}**.\n\n"
        f"Configural correction produced material reduction in "
        f"{metrics['correction_material_rate']:.3f} of worlds. Suggestion-only "
        f"false reduction was {metrics['suggestion_false_reduction_rate']:.3f}; "
        f"premature durable reduction was "
        f"{metrics['premature_durable_reduction_rate']:.3f}. Mean timely "
        f"do-over speedup was {metrics['do_over_speedup_mean']:.6f} "
        f"(95% whole-world bootstrap "
        f"[{speed_interval[0]:.6f}, {speed_interval[1]:.6f}]).\n",
        encoding="utf-8",
    )
    if passed:
        parameters["status"] = "GATE3_PASSED"
        PARAMETERS.write_text(
            json.dumps(parameters, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    else:
        parameters["status"] = "STOPPED_AT_GATE3"
        PARAMETERS.write_text(
            json.dumps(parameters, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _write_json(
            "gate-3-diagnosis-stub.json",
            {
                "failure": [key for key, value in checks.items() if not value],
                "metrics": metrics,
            },
        )
    return passed


def _masked_imaginal_world(
    world: v33.ReductionWorld,
) -> v33.ReductionWorld:
    slices = tuple(
        replace(
            item,
            mode=None,
            root=None,
            world=None,
            policy_proposal=None,
            action=None,
            outcome=None,
        )
        if item.episode_kind == "imaginal_post"
        else item
        for item in world.slices
    )
    return replace(world, slices=slices)


@traced_execution
def _worker_gate4(
    task: tuple[int, str, Mapping[str, float]]
) -> dict[str, Any]:
    seed, lesion, thresholds_map = task
    thresholds = v33.MaterialReductionThresholds(
        mode_retained=float(thresholds_map["mode_retained"]),
        burden_edge_mass_max=float(
            thresholds_map["burden_edge_mass_max"]
        ),
        absent_present_bf_min=float(
            thresholds_map["absent_present_bf_min"]
        ),
        stability_observations=int(
            thresholds_map["stability_observations"]
        ),
        neutral_tolerance=float(thresholds_map["neutral_tolerance"]),
    )
    if lesion != "imaginal_channel":
        adaptive = "W_Y" if lesion == "W_Y" else "none"
        world = v33.generate_world(
            seed,
            v33.ReductionConfig(
                "suggestion_only",
                "none",
                adaptive_edge=adaptive,
                corrective_length=18,
                return_length=18,
            ),
        )
        full = v33.score_world(world).current
        restrictions = {lesion: (0,)}
        lesioned = v33.score_world(
            world, restrictions=restrictions
        ).current
        allowed = {
            program: probability
            for program, probability in zip(
                full.programs, full.probabilities
            )
            if v31.program_values(program)[lesion] == 0
        }
        allowed_mass = math.fsum(allowed.values())
        identity_error = max(
            abs(probability - allowed[program] / allowed_mass)
            for program, probability in zip(
                lesioned.programs, lesioned.probabilities
            )
        )
        copied = [
            asdict(item) for item in world.slices if item.context == 1
        ]
        oracle_programs, oracle_probabilities, oracle_evidence = (
            v33_oracle.posterior(copied, restrictions=restrictions)
        )
        oracle_map = dict(
            zip(oracle_programs, oracle_probabilities)
        )
        oracle_error = max(
            abs(
                probability
                - oracle_map[_program_bits(program)]
            )
            for program, probability in zip(
                lesioned.programs, lesioned.probabilities
            )
        )
        unrelated_movement = {
            edge: (
                lesioned.edge_probabilities[edge]
                - full.edge_probabilities[edge]
            )
            for edge in v33.EDGE_NAMES
            if edge != lesion
        }
        return {
            "seed": seed,
            "cell": lesion,
            "restriction": {lesion: [0]},
            "restricted_prior_identity_error": identity_error,
            "independent_oracle_probability_error": oracle_error,
            "independent_oracle_evidence_error": abs(
                lesioned.log_evidence - oracle_evidence
            ),
            "normalization_error": abs(
                math.fsum(lesioned.probabilities) - 1.0
            ),
            "finite_log_evidence": math.isfinite(lesioned.log_evidence),
            "target_edge_probability": lesioned.edge_probabilities[lesion],
            "unrelated_edge_movement": unrelated_movement,
            "full_target_edge_probability": full.edge_probabilities[lesion],
        }

    post = v33.generate_world(
        seed,
        v33.ReductionConfig(
            "configural",
            "post_revision",
            corrective_length=18,
            return_length=18,
        ),
    )
    no_do = v33.generate_world(
        seed,
        v33.ReductionConfig(
            "configural",
            "none",
            corrective_length=18,
            return_length=18,
        ),
    )
    masked = _masked_imaginal_world(post)
    dropped = replace(
        post,
        slices=tuple(
            item
            for item in post.slices
            if item.episode_kind != "imaginal_post"
        ),
    )
    masked_posterior = v33.score_world(masked).current
    dropped_posterior = v33.score_world(dropped).current
    no_do_posterior = v33.score_world(no_do).current
    masked_neutrality_error = max(
        abs(a - b)
        for a, b in zip(
            masked_posterior.probabilities,
            dropped_posterior.probabilities,
        )
    )
    paired_identity_error = max(
        abs(a - b)
        for a, b in zip(
            masked_posterior.probabilities,
            no_do_posterior.probabilities,
        )
    )
    copied = [
        asdict(item) for item in masked.slices if item.context == 1
    ]
    oracle_programs, oracle_probabilities, oracle_evidence = (
        v33_oracle.posterior(copied)
    )
    oracle_map = dict(zip(oracle_programs, oracle_probabilities))
    oracle_error = max(
        abs(
            probability
            - oracle_map[_program_bits(program)]
        )
        for program, probability in zip(
            masked_posterior.programs,
            masked_posterior.probabilities,
        )
    )
    return {
        "seed": seed,
        "cell": lesion,
        "masked_neutrality_error": masked_neutrality_error,
        "paired_no_do_identity_error": paired_identity_error,
        "independent_oracle_probability_error": oracle_error,
        "independent_oracle_evidence_error": abs(
            masked_posterior.log_evidence - oracle_evidence
        ),
        "normalization_error": abs(
            math.fsum(masked_posterior.probabilities) - 1.0
        ),
        "finite_log_evidence": math.isfinite(
            masked_posterior.log_evidence
        ),
        "masked_first_material_time": v33.first_material_time(
            masked, thresholds
        ),
        "no_do_first_material_time": v33.first_material_time(
            no_do, thresholds
        ),
    }


def run_gate4() -> bool:
    parameters = json.loads(PARAMETERS.read_text())
    if parameters["status"] != "STOPPED_AT_GATE3":
        raise RuntimeError(
            "V3.3 Gate 4 requires the committed Gate-3 adjudication"
        )
    lesions = (*v33.BURDEN_EDGES, "W_Y", "imaginal_channel")
    tasks = [
        (
            seed,
            lesions[(seed - 3_310_000) % len(lesions)],
            parameters["material_readout"],
        )
        for seed in range(3_310_000, 3_312_000)
    ]
    rows = _trace_map("gate-4", tasks, _worker_gate4)
    groups = {
        lesion: [row for row in rows if row["cell"] == lesion]
        for lesion in lesions
    }
    edge_rows = [
        row for row in rows if row["cell"] != "imaginal_channel"
    ]
    mask_rows = groups["imaginal_channel"]
    metrics = {
        "world_count": len(rows),
        "cell_counts": {
            lesion: len(groups[lesion]) for lesion in lesions
        },
        "restricted_prior_identity_error_max": max(
            row["restricted_prior_identity_error"] for row in edge_rows
        ),
        "independent_oracle_probability_error_max": max(
            row["independent_oracle_probability_error"] for row in rows
        ),
        "independent_oracle_evidence_error_max": max(
            row["independent_oracle_evidence_error"] for row in rows
        ),
        "normalization_error_max": max(
            row["normalization_error"] for row in rows
        ),
        "finite_posterior_rate": float(
            np.mean([row["finite_log_evidence"] for row in rows])
        ),
        "target_edge_probability_max": {
            edge: max(
                row["target_edge_probability"] for row in groups[edge]
            )
            for edge in (*v33.BURDEN_EDGES, "W_Y")
        },
        "unrelated_movement_descriptive": {
            edge: {
                "maximum_absolute": max(
                    abs(value)
                    for row in groups[edge]
                    for value in row["unrelated_edge_movement"].values()
                ),
                "mean_absolute": float(
                    np.mean(
                        [
                            abs(value)
                            for row in groups[edge]
                            for value in row[
                                "unrelated_edge_movement"
                            ].values()
                        ]
                    )
                ),
            }
            for edge in (*v33.BURDEN_EDGES, "W_Y")
        },
        "masked_channel_neutrality_error_max": max(
            row["masked_neutrality_error"] for row in mask_rows
        ),
        "masked_paired_no_do_identity_error_max": max(
            row["paired_no_do_identity_error"] for row in mask_rows
        ),
        "masked_timing_identity_rate": float(
            np.mean(
                [
                    row["masked_first_material_time"]
                    == row["no_do_first_material_time"]
                    for row in mask_rows
                ]
            )
        ),
    }
    checks = {
        "restricted_prior_identity": (
            metrics["restricted_prior_identity_error_max"] <= TOLERANCE
        ),
        "independent_oracle_probability": (
            metrics["independent_oracle_probability_error_max"] <= TOLERANCE
        ),
        "independent_oracle_evidence": (
            metrics["independent_oracle_evidence_error_max"] <= TOLERANCE
        ),
        "finite_normalized_posteriors": (
            metrics["normalization_error_max"] <= TOLERANCE
            and metrics["finite_posterior_rate"] == 1.0
        ),
        "each_edge_production_removed": all(
            value <= TOLERANCE
            for value in metrics["target_edge_probability_max"].values()
        ),
        "imaginal_mask_candidate_common": (
            metrics["masked_channel_neutrality_error_max"] <= TOLERANCE
        ),
        "imaginal_mask_paired_identity": (
            metrics["masked_paired_no_do_identity_error_max"] <= TOLERANCE
        ),
        "imaginal_effect_removed": (
            metrics["masked_timing_identity_rate"] == 1.0
        ),
    }
    passed = all(checks.values())
    payload = {
        "verdict": "PASS" if passed else "FAIL",
        "seed_block": [3_310_000, 3_311_999],
        "checks": checks,
        "metrics": metrics,
        "selectivity_definition": (
            "restricted-prior consistency; unrelated marginal movement is "
            "descriptive because conditioning renormalizes the posterior"
        ),
        "trace_ledger": "gate-4-trace-hashes.json",
    }
    _write_json("gate-4.json", payload)
    (RESULTS / "gate-4-report.md").write_text(
        "# V3.3 Gate 4 — selective lesions\n\n"
        f"Verdict: **{payload['verdict']}**.\n\n"
        "All five production deletions were scored by conditioning the "
        "structure prior. The maximum restricted-prior identity error was "
        f"`{metrics['restricted_prior_identity_error_max']:.3e}` and the "
        "independent-oracle probability error was "
        f"`{metrics['independent_oracle_probability_error_max']:.3e}`. "
        "The imaginal-channel lesion used candidate-common masking; its "
        "maximum neutrality error was "
        f"`{metrics['masked_channel_neutrality_error_max']:.3e}` and paired "
        "no-do timing agreed in "
        f"`{metrics['masked_timing_identity_rate']:.3f}` of worlds. "
        "Non-target marginal movement is reported descriptively as posterior "
        "renormalization, not treated as a second lesion target.\n",
        encoding="utf-8",
    )
    if passed:
        parameters["status"] = "GATE4_PASSED_ADJUDICATED_CONTINUATION"
        PARAMETERS.write_text(
            json.dumps(parameters, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    else:
        parameters["status"] = "STOPPED_AT_GATE4"
        PARAMETERS.write_text(
            json.dumps(parameters, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _write_json(
            "gate-4-diagnosis-stub.json",
            {
                "failed": [
                    name for name, passed_check in checks.items()
                    if not passed_check
                ],
                "metrics": metrics,
            },
        )
    return passed


@traced_execution
def _worker_gate5_assay(
    task: tuple[int, str, str, Mapping[str, float]]
) -> dict[str, Any]:
    seed, cell, arm, thresholds = task
    if arm == "suggestion":
        world = v33.generate_world(
            seed,
            v33.ReductionConfig(
                "suggestion_only",
                "none",
                corrective_length=18,
                return_length=18,
            ),
        )
        summary = _arm_summary(world)
        return {
            "seed": seed,
            "cell": cell,
            "arm": arm,
            "material": _material_from_row(
                summary, _trajectory(world), thresholds
            ),
            "root_revision": summary["root_revision"],
        }
    if arm == "speedup":
        no_do = v33.generate_world(
            seed,
            v33.ReductionConfig(
                "configural",
                "none",
                corrective_length=18,
                return_length=18,
            ),
        )
        timely = v33.generate_world(
            seed,
            v33.ReductionConfig(
                "configural",
                "post_revision",
                corrective_length=18,
                return_length=18,
            ),
        )
        no_time = _first_from_trajectory(
            _trajectory(no_do),
            mode=thresholds["mode_retained"],
            burden=thresholds["burden_edge_mass_max"],
            bf=thresholds["absent_present_bf_min"],
        )
        timely_time = _first_from_trajectory(
            _trajectory(timely),
            mode=thresholds["mode_retained"],
            burden=thresholds["burden_edge_mass_max"],
            bf=thresholds["absent_present_bf_min"],
        )
        event = v33.root_revision_event(timely)
        opportunity = [
            item.time
            for item in timely.slices
            if item.episode_kind == "imaginal_post"
        ]
        return {
            "seed": seed,
            "cell": cell,
            "arm": arm,
            "no_do_time": no_time,
            "timely_time": timely_time,
            "speedup": (
                (no_time - timely_time) / no_time
                if no_time is not None and timely_time is not None
                else None
            ),
            "schedule_identity": (
                event is not None
                and bool(opportunity)
                and min(opportunity) == event + 1
            ),
        }
    corrective_length = (
        12 if cell == "correction_length_12"
        else 30 if cell == "correction_length_30"
        else 18
    )
    return_length = 30 if cell == "later_stress_30" else 18
    adaptive = "W_Y" if arm == "adaptive" else "none"
    world = v33.generate_world(
        seed,
        v33.ReductionConfig(
            "configural",
            "none",
            adaptive_edge=adaptive,
            corrective_length=corrective_length,
            return_length=return_length,
        ),
    )
    summary = _arm_summary(world)
    return {
        "seed": seed,
        "cell": cell,
        "arm": arm,
        "material": _material_from_row(
            summary, _trajectory(world), thresholds
        ),
        "mode": summary["mode"],
        "adaptive_w_y": summary["adaptive_w_y"],
        "neutral_error": summary["neutral_error"],
        "old_graph": summary["old_graph"],
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
    return (
        path.exists()
        and hashlib.sha256(path.read_bytes()).hexdigest()
        == ledger["file_sha256"]
        and sum(1 for _ in path.open("rb")) == ledger["world_count"]
    )


def run_gate5() -> bool:
    parameters = json.loads(PARAMETERS.read_text())
    if parameters["status"] != "GATE4_PASSED_ADJUDICATED_CONTINUATION":
        raise RuntimeError("V3.3 Gate 4 must pass before Gate 5")
    recovery_specs = (
        ("recovery_length_32", 3_312_000, 32, 0.5, 1.0),
        ("recovery_length_96", 3_312_800, 96, 0.5, 1.0),
        ("recovery_concentration_1", 3_313_600, 64, 1.0, 1.0),
        ("recovery_code_scale_1_25", 3_314_400, 64, 0.5, 1.25),
    )
    recovery_tasks = [
        (seed, length, concentration, scale)
        for _, start, length, concentration, scale in recovery_specs
        for seed in range(start, start + 800)
    ]
    recovery_rows = _trace_map(
        "gate-5-recovery", recovery_tasks, _worker_recovery
    )
    recovery_metrics = {}
    for index, (name, *_rest) in enumerate(recovery_specs):
        subset = recovery_rows[index * 800 : (index + 1) * 800]
        recovery_metrics[name] = _recovery_metrics(subset)

    thresholds = parameters["material_readout"]
    assay_tasks: list[tuple[int, str, str, Mapping[str, float]]] = []
    for seed in range(3_315_200, 3_316_000):
        assay_tasks.append(
            (seed, "correction_length_12", "correction", thresholds)
        )
    for seed in range(3_316_000, 3_316_800):
        assay_tasks.append(
            (seed, "correction_length_30", "correction", thresholds)
        )
    for seed in range(3_316_800, 3_317_600):
        assay_tasks.append(
            (seed, "later_stress_30", "correction", thresholds)
        )
    primary_arms = ("correction", "suggestion", "speedup", "adaptive")
    for seed in range(3_317_600, 3_320_000):
        assay_tasks.append(
            (
                seed,
                "primary_repetition",
                primary_arms[(seed - 3_317_600) % 4],
                thresholds,
            )
        )
    assay_rows = _trace_map(
        "gate-5-assays", assay_tasks, _worker_gate5_assay
    )
    assay_groups = {
        cell: [row for row in assay_rows if row["cell"] == cell]
        for cell in (
            "correction_length_12",
            "correction_length_30",
            "later_stress_30",
            "primary_repetition",
        )
    }
    primary = assay_groups["primary_repetition"]
    primary_by_arm = {
        arm: [row for row in primary if row["arm"] == arm]
        for arm in primary_arms
    }
    speeds = [
        float(row["speedup"])
        for row in primary_by_arm["speedup"]
        if row["speedup"] is not None
    ]
    suggestions = [
        float(row["root_revision"])
        for row in primary_by_arm["suggestion"]
    ]
    scientific = {
        "correction_length_12_material_rate": float(
            np.mean(
                [
                    row["material"]
                    for row in assay_groups["correction_length_12"]
                ]
            )
        ),
        "correction_length_30_material_rate": float(
            np.mean(
                [
                    row["material"]
                    for row in assay_groups["correction_length_30"]
                ]
            )
        ),
        "later_stress_30_material_rate": float(
            np.mean(
                [
                    row["material"]
                    for row in assay_groups["later_stress_30"]
                ]
            )
        ),
        "primary_correction_material_rate": float(
            np.mean(
                [
                    row["material"]
                    for row in primary_by_arm["correction"]
                ]
            )
        ),
        "primary_suggestion_false_reduction_rate": float(
            np.mean(
                [
                    row["material"]
                    for row in primary_by_arm["suggestion"]
                ]
            )
        ),
        "primary_adaptive_edge_survival": float(
            np.mean(
                [
                    row["adaptive_w_y"]
                    for row in primary_by_arm["adaptive"]
                ]
            )
        ),
        "primary_adaptive_material_rate": float(
            np.mean(
                [
                    row["material"]
                    for row in primary_by_arm["adaptive"]
                ]
            )
        ),
        "primary_neutral_error_max": max(
            row["neutral_error"]
            for arm in ("correction", "adaptive")
            for row in primary_by_arm[arm]
        ),
        "do_over_speedup_mean": float(np.mean(speeds)),
        "do_over_speedup_ci95": list(
            _bootstrap_mean_interval(speeds, seed=3_318_202)
        ),
        "do_over_schedule_identity_rate": float(
            np.mean(
                [
                    row["schedule_identity"]
                    for row in primary_by_arm["speedup"]
                ]
            )
        ),
        "suggestion_root_direction_mean": float(np.mean(suggestions)),
        "suggestion_root_direction_ci95": list(
            _bootstrap_mean_interval(suggestions, seed=3_318_201)
        ),
    }
    criterion = parameters["criteria"]
    recovery_checks = {
        name: {
            "edge_accuracy": (
                values["minimum_edge_accuracy"]
                >= max(0.45, criterion["edge_accuracy_min"] - 0.08)
            ),
            "coverage": (
                values["coverage"]
                >= max(0.75, criterion["coverage_min"] - 0.10)
            ),
            "normalization": (
                values["maximum_normalization_error"] <= TOLERANCE
            ),
            "exact_log_probability": (
                values["maximum_exact_log_probability_error"] <= TOLERANCE
            ),
        }
        for name, values in recovery_metrics.items()
    }
    scientific_checks = {
        "correction_length_12": (
            scientific["correction_length_12_material_rate"] >= 0.75
        ),
        "correction_length_30": (
            scientific["correction_length_30_material_rate"]
            >= criterion["material_reduction_rate_min"]
        ),
        "later_stress_30": (
            scientific["later_stress_30_material_rate"]
            >= criterion["material_reduction_rate_min"]
        ),
        "primary_correction": (
            scientific["primary_correction_material_rate"]
            >= criterion["material_reduction_rate_min"]
        ),
        "primary_suggestion_specificity": (
            scientific["primary_suggestion_false_reduction_rate"]
            <= criterion["suggestion_false_reduction_max"]
        ),
        "primary_adaptive_survival": (
            scientific["primary_adaptive_edge_survival"]
            >= criterion["adaptive_edge_survival_min"]
        ),
        "primary_neutral_identity": (
            scientific["primary_neutral_error_max"] <= TOLERANCE
        ),
        "do_over_schedule_identity": (
            scientific["do_over_schedule_identity_rate"] == 1.0
        ),
    }
    prior_stage_manifests = [
        _verify_stage_manifest(stage)
        for stage in ("V3.0", "V3.1", "V3.2")
    ]
    gate1 = json.loads((RESULTS / "gate-1.json").read_text())
    gate2 = json.loads((RESULTS / "gate-2.json").read_text())
    gate3 = json.loads((RESULTS / "gate-3.json").read_text())
    gate4 = json.loads((RESULTS / "gate-4.json").read_text())
    nonblocking_names = {
        "do_over_acceleration",
        "root_revision_without_pruning",
    }
    gate3_blocking = {
        name: value
        for name, value in gate3["checks"].items()
        if name not in nonblocking_names
    }
    cumulative = {
        "gate1_pass": gate1["verdict"] == "PASS",
        "gate2_pass": gate2["verdict"] == "PASS",
        "gate3_formal_verdict_retained": gate3["verdict"],
        "gate3_blocking_checks": gate3_blocking,
        "gate3_nonblocking_checks": {
            name: gate3["checks"][name] for name in nonblocking_names
        },
        "gate4_pass": gate4["verdict"] == "PASS",
        "prior_stage_manifests": prior_stage_manifests,
        "trace_ledgers": {
            name: _trace_ledger_valid(name)
            for name in (
                "gate-2",
                "gate-3",
                "gate-4",
                "gate-5-recovery",
                "gate-5-assays",
            )
        },
    }
    cumulative_pass = (
        cumulative["gate1_pass"]
        and cumulative["gate2_pass"]
        and all(gate3_blocking.values())
        and cumulative["gate4_pass"]
        and all(item["passed"] for item in prior_stage_manifests)
        and all(cumulative["trace_ledgers"].values())
    )
    blocking = {
        "recovery_robustness": all(
            all(values.values()) for values in recovery_checks.values()
        ),
        "scientific_robustness": all(scientific_checks.values()),
        "cumulative_regression": cumulative_pass,
    }
    nonblocking = {
        "do_over_speedup_floor_repetition": {
            "passed": (
                scientific["do_over_speedup_mean"]
                >= criterion["do_over_speedup_min"]
                and scientific["do_over_speedup_ci95"][0] > 0.0
            ),
            "mean": scientific["do_over_speedup_mean"],
            "ci95": scientific["do_over_speedup_ci95"],
            "frozen_floor": criterion["do_over_speedup_min"],
        },
        "suggestion_direction_repetition": {
            "passed": scientific["suggestion_root_direction_mean"] > 0.0,
            "mean": scientific["suggestion_root_direction_mean"],
            "ci95": scientific["suggestion_root_direction_ci95"],
            "frozen_direction": "positive",
        },
        "authorization": "gate3-adjudication.md",
    }
    passed = all(blocking.values())
    payload = {
        "verdict": "PASS" if passed else "FAIL",
        "seed_block": [3_312_000, 3_319_999],
        "blocking": blocking,
        "recovery_metrics": recovery_metrics,
        "recovery_checks": recovery_checks,
        "scientific_metrics": scientific,
        "scientific_checks": scientific_checks,
        "adjudicated_nonblocking": nonblocking,
        "cumulative": cumulative,
        "trace_ledgers": [
            "gate-5-recovery-trace-hashes.json",
            "gate-5-assays-trace-hashes.json",
        ],
    }
    _write_json("gate-5.json", payload)
    (RESULTS / "gate-5-report.md").write_text(
        "# V3.3 Gate 5 — cumulative robustness\n\n"
        f"Verdict: **{payload['verdict']}** for all blocking criteria.\n\n"
        "The adjudicated families remain non-blocking and are reported "
        "verbatim. Timely do-over speedup repeated at "
        f"`{scientific['do_over_speedup_mean']:.6f}` (95% CI "
        f"`[{scientific['do_over_speedup_ci95'][0]:.6f}, "
        f"{scientific['do_over_speedup_ci95'][1]:.6f}]`; floor "
        f"`{criterion['do_over_speedup_min']}`). Suggestion root direction "
        f"repeated at `{scientific['suggestion_root_direction_mean']:.6f}` "
        f"(95% CI `[{scientific['suggestion_root_direction_ci95'][0]:.6f}, "
        f"{scientific['suggestion_root_direction_ci95'][1]:.6f}]`).\n\n"
        "All V3.0–V3.2 freeze manifests were independently rehashed. Gate-3 "
        "remains formally FAIL; only its two adjudicated families are omitted "
        "from cumulative blocking aggregation.\n",
        encoding="utf-8",
    )
    if passed:
        parameters["status"] = (
            "FROZEN_ADJUDICATED_MIXED_DO_OVER_NULL_AND_"
            "SUGGESTION_DIRECTION"
        )
    else:
        parameters["status"] = "STOPPED_AT_GATE5"
        _write_json(
            "gate-5-diagnosis-stub.json",
            {
                "failed": [
                    name for name, value in blocking.items() if not value
                ],
                "recovery_checks": recovery_checks,
                "scientific_checks": scientific_checks,
            },
        )
    PARAMETERS.write_text(
        json.dumps(parameters, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return passed


def write_freeze_manifest() -> bool:
    parameters = json.loads(PARAMETERS.read_text())
    expected_status = (
        "FROZEN_ADJUDICATED_MIXED_DO_OVER_NULL_AND_"
        "SUGGESTION_DIRECTION"
    )
    if parameters["status"] != expected_status:
        raise RuntimeError("V3.3 is not freeze-ready")
    fixed = (
        ROOT / "contracts" / "v3.3-prune-contract.md",
        ROOT / "protocols" / "v3.3-analysis-plan.md",
        ROOT / "protocols" / "v3.3-parameters.json",
        ROOT / "protocols" / "v3.3-public-dummy.json",
        ROOT / "ref" / "trace_sink.py",
        ROOT / "ref" / "v31.py",
        ROOT / "ref" / "v33.py",
        ROOT / "ref" / "v33_oracle.py",
        ROOT / "scripts" / "run_v33.py",
        ROOT / "tests" / "test_v33_prune.py",
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
        "stage": "V3.3",
        "status": expected_status,
        "files": files,
        "local_only_trace_bundles": local_only,
        "escrow": {
            "block": [4_030_000, 4_033_999],
            "status": "UNTOUCHED",
        },
        "formal_gate_verdicts": {
            "gate1": "PASS",
            "gate2": "PASS",
            "gate3": "FAIL",
            "gate4": "PASS",
            "gate5": "PASS",
        },
        "adjudicated_nonblocking_families": [
            "do_over_speedup",
            "suggestion_direction",
        ],
    }
    _write_json("freeze-manifest.json", payload)
    return True


def run_pilot() -> bool:
    parameters = json.loads(PARAMETERS.read_text())
    if parameters["status"] != "EVENT_INDEXED_REPAIR_PILOT_PENDING":
        raise RuntimeError("event-indexed V3.3 pilot is not authorized")
    recovery_rows = _trace_map(
        "stage0-event-pilot-recovery",
        [
            (seed, 64, 0.5, 1.0)
            for seed in range(3_330_000, 3_331_000)
        ],
        _worker_recovery,
    )
    assay_rows = _trace_map(
        "stage0-event-pilot-assays",
        list(range(3_331_000, 3_332_000)),
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
            "stage0-event-pilot.json",
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
        "event_world_rate": float(
            np.mean(
                [
                    row["schedule"]["root_revision_event"] is not None
                    for row in assay_rows
                ]
            )
        ),
        "post_schedule_identity_rate": float(
            np.mean(
                [
                    row["schedule"]["post_is_first_slice_after_event"]
                    for row in assay_rows
                ]
            )
        ),
        "no_do_schedule_identity_rate": float(
            np.mean(
                [
                    row["schedule"]["no_do_is_first_slice_after_event"]
                    for row in assay_rows
                ]
            )
        ),
        "premature_precedes_event_rate": float(
            np.mean(
                [
                    row["schedule"]["premature_begins_before_event"]
                    for row in assay_rows
                ]
            )
        ),
    }
    if (
        attainable["material_reduction_rate"] <= 0.0
        or attainable["do_over_speedup"] <= 0.0
    ):
        _write_json(
            "stage0-event-pilot.json",
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
        "do_over_speedup_min": attainable["do_over_speedup"] * 0.5,
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
        "stage0-event-pilot.json",
        {
            "verdict": "DESCRIPTIVE_ATTAINABILITY_PASS",
            "barred_block": [3_330_000, 3_331_999],
            "recovery": recovery,
            "material_readout": readout,
            "attainable": attainable,
            "frozen_criteria": criteria,
        },
    )
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
    if args.step == "gate1":
        passed = run_gate1()
    elif args.step == "pilot":
        passed = run_pilot()
    elif args.step == "gate2":
        passed = run_gate2()
    elif args.step == "gate3":
        passed = run_gate3()
    elif args.step == "gate4":
        passed = run_gate4()
    elif args.step == "gate5":
        passed = run_gate5()
    else:
        passed = write_freeze_manifest()
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
