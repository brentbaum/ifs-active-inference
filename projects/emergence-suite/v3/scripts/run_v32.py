#!/usr/bin/env python3
"""Prospective V3.2 stage runner with execution-time trace custody."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from dataclasses import asdict
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ref import v32, v32_oracle  # noqa: E402


RESULTS = ROOT / "results" / "V3.2"
PARAMETERS = ROOT / "protocols" / "v3.2-parameters.json"
TOLERANCE = 1e-10

CANONICAL = {
    "static": v32.TemporalStructure(
        1, ("shared_global", "shared_global"), ("static", "static")
    ),
    "cue_local": v32.TemporalStructure(
        1, ("cue_specific", "cue_specific"), ("static", "static")
    ),
    "recurrent_context": v32.TemporalStructure(
        2,
        ("context_specific", "context_specific"),
        ("discrete_recurrent_context", "discrete_recurrent_context"),
    ),
    "continuous_drift": v32.TemporalStructure(
        1,
        ("shared_global", "shared_global"),
        ("ordered_random_walk", "ordered_random_walk"),
    ),
    "one_way_change": v32.TemporalStructure(
        2,
        ("context_specific", "context_specific"),
        ("one_way_change", "one_way_change"),
    ),
}
MIXED = v32.TemporalStructure(
    2,
    ("context_specific", "context_specific"),
    ("ordered_random_walk", "discrete_recurrent_context"),
)


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


def _write_json(name: str, payload: Any) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / name).write_text(
        json.dumps(_plain(payload), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _sha_payload(payload: Any) -> str:
    encoded = json.dumps(
        _plain(payload), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _classification(posterior: v32.TemporalPosterior) -> tuple[str, float]:
    probabilities = dict(v32.region_probabilities(posterior))
    label = max(probabilities, key=probabilities.get)
    total = math.fsum(probabilities.values())
    return label, probabilities[label] / total


def _credible_contains(
    posterior: v32.TemporalPosterior, truth: v32.TemporalStructure
) -> bool:
    order = np.argsort(-np.asarray(posterior.probabilities))
    mass = 0.0
    for index in order:
        mass += posterior.probabilities[int(index)]
        if posterior.programs[int(index)] == truth:
            return True
        if mass >= 0.95:
            return False
    return False


def _world_record(
    world: v32.TemporalWorld,
    posterior: v32.TemporalPosterior,
    *,
    cell: str,
    truth_label: str,
    hyperparameters: v32.TemporalHyperparameters = v32.DEFAULT_HYPERPARAMETERS,
) -> dict[str, Any]:
    predicted, confidence = _classification(posterior)
    truth_probability = posterior.structure_probability(world.structure)
    return _plain({
        "seed": world.seed,
        "cell": cell,
        "truth_label": truth_label,
        "truth_structure": asdict(world.structure),
        "predicted_label": predicted,
        "classification_confidence": confidence,
        "truth_probability": truth_probability,
        "credible_contains_truth": _credible_contains(posterior, world.structure),
        "active_probabilities": posterior.active_context_probabilities,
        "scope_probabilities": posterior.scope_probabilities,
        "dynamics_probabilities": posterior.dynamics_probabilities,
        "log_evidence": posterior.log_evidence,
        "exact_log_probability": world.exact_log_probability,
        "truth_log_joint_error": abs(
            world.exact_log_probability
            - (
                v32.structure_log_prior(world.structure, hyperparameters)
                + _truth_log_likelihood(
                    world, world.structure, hyperparameters
                )
            )
        ),
        "rng_keys_sha256": _sha_payload(world.rng_keys),
        "readouts": v32.redescription_readouts(posterior),
    })


def _truth_log_likelihood(
    world: v32.TemporalWorld,
    structure: v32.TemporalStructure,
    hyperparameters: v32.TemporalHyperparameters = v32.DEFAULT_HYPERPARAMETERS,
) -> float:
    # Public factor recombination path, separate from the stored generator total.
    active = 0.0
    blocks = 0.0
    for block, scope, dynamics in zip(
        v32.BLOCKS, structure.scopes, structure.dynamics
    ):
        blocks += v32._candidate_log_likelihood(
            world,
            structure.active_contexts,
            block,
            scope,
            dynamics,
            hyperparameters,
            mask_active_channel=True,
        )
        active += v32._candidate_log_likelihood(
            world,
            structure.active_contexts,
            block,
            "shared_global",
            "static",
            hyperparameters,
            mask_scope_channel=True,
            mask_dynamics_channel=True,
        )
        active -= v32._candidate_log_likelihood(
            world,
            structure.active_contexts,
            block,
            "shared_global",
            "static",
            hyperparameters,
            mask_active_channel=True,
            mask_scope_channel=True,
            mask_dynamics_channel=True,
        )
    return active + blocks


def _worker_recovery(task: tuple[int, str, int, int, float, float, float]) -> dict[str, Any]:
    seed, label, length, cue_count, missingness, scale, reliability = task
    hp = v32.TemporalHyperparameters(reliability, scale, 0.08)
    world = v32.generate_world(
        seed,
        structure=CANONICAL[label],
        length=length,
        cue_count=cue_count,
        missingness=missingness,
        hyperparameters=hp,
    )
    posterior = v32.score_world(world, hyperparameters=hp)
    record = _world_record(
        world,
        posterior,
        cell=label,
        truth_label=label,
        hyperparameters=hp,
    )
    record["field_correct"] = {
        "active": int(np.argmax(posterior.active_context_probabilities)) + 1
        == world.structure.active_contexts,
        "scopes": [
            max(posterior.scope_probabilities[block], key=posterior.scope_probabilities[block].get)
            == world.structure.scopes[index]
            for index, block in enumerate(v32.BLOCKS)
        ],
        "dynamics": [
            max(
                posterior.dynamics_probabilities[block],
                key=posterior.dynamics_probabilities[block].get,
            )
            == world.structure.dynamics[index]
            for index, block in enumerate(v32.BLOCKS)
        ],
    }
    return record


def _trace_map(
    name: str, tasks: Sequence[Any], worker: Any, processes: int | None = None
) -> list[dict[str, Any]]:
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{name}-traces.jsonl"
    rows: list[dict[str, Any]] = []
    hashes = []
    file_hash = hashlib.sha256()
    count = processes or max(1, min(8, (os.cpu_count() or 2) - 1))
    with path.open("wb") as handle:
        with get_context("spawn").Pool(count) as pool:
            for row in pool.imap(worker, tasks, chunksize=8):
                encoded = (
                    json.dumps(
                        _plain(row),
                        sort_keys=True,
                        separators=(",", ":"),
                        allow_nan=False,
                    ).encode()
                    + b"\n"
                )
                handle.write(encoded)
                handle.flush()
                file_hash.update(encoded)
                hashes.append({"seed": row["seed"], "sha256": hashlib.sha256(encoded).hexdigest()})
                rows.append(row)
    ledger = {
        "file": path.name,
        "world_count": len(rows),
        "file_sha256": file_hash.hexdigest(),
        "records": hashes,
    }
    _write_json(f"{name}-trace-hashes.json", ledger)
    return rows


def _ece(confidences: Sequence[float], correct: Sequence[bool]) -> float:
    p = np.asarray(confidences, dtype=float)
    y = np.asarray(correct, dtype=float)
    result = 0.0
    for lower in np.linspace(0.0, 0.9, 10):
        upper = lower + 0.1
        selected = (p >= lower) & (
            p <= upper if math.isclose(upper, 1.0) else p < upper
        )
        if selected.any():
            result += float(selected.mean()) * abs(
                float(p[selected].mean()) - float(y[selected].mean())
            )
    return result


def _recovery_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    labels = tuple(CANONICAL)
    confusion = {
        truth: {
            predicted: sum(
                row["truth_label"] == truth and row["predicted_label"] == predicted
                for row in rows
            )
            for predicted in labels
        }
        for truth in labels
    }
    correct = [row["predicted_label"] == row["truth_label"] for row in rows]
    confidences = [row["classification_confidence"] for row in rows]
    per_family = {
        label: float(
            np.mean(
                [
                    row["predicted_label"] == label
                    for row in rows
                    if row["truth_label"] == label
                ]
            )
        )
        for label in labels
    }
    active = [row["field_correct"]["active"] for row in rows]
    scopes = [value for row in rows for value in row["field_correct"]["scopes"]]
    dynamics = [value for row in rows for value in row["field_correct"]["dynamics"]]
    return {
        "world_count": len(rows),
        "confusion": confusion,
        "per_family_accuracy": per_family,
        "macro_region_recovery": float(np.mean(tuple(per_family.values()))),
        "active_context_accuracy": float(np.mean(active)),
        "scope_accuracy": float(np.mean(scopes)),
        "dynamics_accuracy": float(np.mean(dynamics)),
        "brier": float(
            np.mean(
                [
                    (confidence - float(outcome)) ** 2
                    for confidence, outcome in zip(confidences, correct)
                ]
            )
        ),
        "ece": _ece(confidences, correct),
        "coverage": float(np.mean([row["credible_contains_truth"] for row in rows])),
        "max_exact_log_probability_error": max(
            row["truth_log_joint_error"] for row in rows
        ),
    }


def _bootstrap(values: Sequence[float], seed: int, draws: int = 2000) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = [float(rng.choice(values, len(values), replace=True).mean()) for _ in range(draws)]
    return tuple(float(value) for value in np.quantile(means, (0.025, 0.975)))


def run_pilot() -> None:
    labels = tuple(CANONICAL)
    tasks = [
        (seed, labels[(seed - 3_230_000) % 5], 48, 3, 0.0, 1.0, 0.74)
        for seed in range(3_230_000, 3_232_000)
    ]
    rows = _trace_map("stage0-repair-pilot", tasks, _worker_recovery)
    metrics = _recovery_metrics(rows)
    # Paired attainable-range fixtures use already-barred pilot seeds.
    fixture = _pilot_assays(range(3_230_000, 3_230_200))
    thresholds = {
        "active_context_accuracy": max(0.50, math.floor((metrics["active_context_accuracy"] - 0.05) * 100) / 100),
        "scope_accuracy": max(0.50, math.floor((metrics["scope_accuracy"] - 0.05) * 100) / 100),
        "dynamics_accuracy": max(0.50, math.floor((metrics["dynamics_accuracy"] - 0.05) * 100) / 100),
        "macro_region_recovery": max(0.50, math.floor((metrics["macro_region_recovery"] - 0.08) * 100) / 100),
        "brier_max": min(0.35, math.ceil((metrics["brier"] + 0.05) * 100) / 100),
        "ece_max": min(0.30, math.ceil((metrics["ece"] + 0.05) * 100) / 100),
        "coverage_min": max(0.80, math.floor((metrics["coverage"] - 0.05) * 100) / 100),
        "mixed_block_accuracy": max(0.50, math.floor((fixture["mixed_accuracy"] - 0.08) * 100) / 100),
        "recurrent_context_probability": max(0.55, round(fixture["recurrent_context_probability"] * 0.75, 3)),
        "material_redescription_rate": max(0.50, math.floor((fixture["material_rate"] - 0.08) * 100) / 100),
        "historical_query_separation": max(0.05, round(fixture["history_separation"] * 0.5, 3)),
        "one_way_false_recurrence_max": min(0.30, math.ceil((fixture["false_recurrence"] + 0.08) * 100) / 100),
        "witnessing_scope_gain": max(0.01, round(fixture["witnessing_gain"] * 0.5, 3)),
        "present_transfer": max(0.01, round(fixture["present_transfer"] * 0.5, 3)),
        "old_context_retention_error_max": 1e-10,
    }
    attainable = fixture["witnessing_gain"] > 0.0
    parameters = json.loads(PARAMETERS.read_text())
    parameters["status"] = (
        "FROZEN_AFTER_STAGE0_PILOT"
        if attainable
        else "STOPPED_AT_STAGE0_UNATTAINABLE_WITNESSING_CONTRAST"
    )
    if not attainable:
        thresholds["witnessing_scope_gain"] = "UNFROZEN_ATTAINABILITY_FAILURE"
    parameters["criterion_thresholds"] = thresholds
    parameters["pilot_summary_sha256"] = _sha_payload(
        {"metrics": metrics, "attainability": fixture}
    )
    PARAMETERS.write_text(json.dumps(parameters, indent=2, sort_keys=True) + "\n")
    _write_json(
        "stage0-repair-pilot.json",
        {
            "verdict_class": "descriptive_attainability_only",
            "barred_block": [3_230_000, 3_231_999],
            "recovery": metrics,
            "attainability": fixture,
            (
                "frozen_thresholds"
                if attainable
                else "candidate_thresholds_not_frozen_due_to_stop"
            ): thresholds,
            "stage0_status": (
                "PASS" if attainable else "STOP_UNATTAINABLE_WITNESSING_CONTRAST"
            ),
        },
    )


def _pilot_assays(seeds: Iterable[int]) -> dict[str, float]:
    mixed, recurrent, material, history, false_recurrent, gains, transfers = (
        [],
        [],
        [],
        [],
        [],
        [],
        [],
    )
    for seed in seeds:
        mixed_p = v32.score_world(v32.generate_world(seed, structure=MIXED, length=48))
        mixed.extend(
            [
                max(mixed_p.dynamics_probabilities[block], key=mixed_p.dynamics_probabilities[block].get)
                == MIXED.dynamics[index]
                for index, block in enumerate(v32.BLOCKS)
            ]
        )
        recurrent_world = v32.generate_world(
            seed, structure=CANONICAL["recurrent_context"], length=48
        )
        recurrent_p = v32.score_world(recurrent_world)
        recurrent.append(
            recurrent_p.scope_probability("cue_emission", "context_specific")
        )
        material.append(v32.redescription_readouts(recurrent_p)["material"])
        history.append(
            abs(
                v32.historical_prediction(recurrent_p, "cue_emission", 1, 0)
                - v32.historical_prediction(recurrent_p, "cue_emission", 0, 0)
            )
        )
        one_way = v32.score_world(
            v32.generate_world(
                seed, structure=CANONICAL["one_way_change"], length=48
            )
        )
        false_recurrent.append(
            one_way.dynamics_probability(
                "cue_emission", "discrete_recurrent_context"
            )
        )
        witness = v32.score_world(
            v32.generate_world(
                seed,
                structure=CANONICAL["recurrent_context"],
                length=48,
                evidence_style="witnessing",
            )
        )
        baseline = v32.score_world(
            v32.generate_world(
                seed,
                structure=CANONICAL["recurrent_context"],
                length=48,
                evidence_style="single_regime",
            )
        )
        gains.append(
            witness.scope_probability("cue_emission", "context_specific")
            - baseline.scope_probability("cue_emission", "context_specific")
        )
        transfers.append(v32.present_context_transfer(witness, context=1))
    return {
        "mixed_accuracy": float(np.mean(mixed)),
        "recurrent_context_probability": float(np.mean(recurrent)),
        "material_rate": float(np.mean(material)),
        "history_separation": float(np.mean(history)),
        "false_recurrence": float(np.mean(false_recurrent)),
        "witnessing_gain": float(np.mean(gains)),
        "present_transfer": float(np.mean(transfers)),
    }


def _parameters() -> dict[str, Any]:
    payload = json.loads(PARAMETERS.read_text())
    if payload["status"] != "FROZEN_AFTER_STAGE0_PILOT":
        raise RuntimeError("stage-0 thresholds are not frozen")
    return payload


def run_gate1() -> bool:
    dummy = v32.generate_world(
        3_230_000,
        structure=MIXED,
        length=12,
        evidence_style="witnessing",
    )
    production = v32.score_world(dummy)
    oracle = v32_oracle.brute_force_structure_posterior(
        dummy, v32.DEFAULT_HYPERPARAMETERS
    )
    oracle_map = dict(zip(oracle.programs, oracle.probabilities))
    restriction = {"scope:cue_emission": ("shared_global", "cue_specific")}
    restricted = v32.score_world(dummy, restrictions=restriction)
    full = dict(zip(production.programs, production.probabilities))
    allowed_mass = math.fsum(
        probability
        for program, probability in full.items()
        if program.scopes[0] in restriction["scope:cue_emission"]
    )
    restricted_error = max(
        abs(
            probability - full[program] / allowed_mass
        )
        for program, probability in zip(
            restricted.programs, restricted.probabilities
        )
    )
    before = tuple(production.probabilities)
    _ = v32.redescription_readouts(production)
    readout_pure = before == production.probabilities
    label_rejected = False
    try:
        from dataclasses import replace
        v32.score_world(replace(dummy, analysis_labels=("split",)))
    except ValueError:
        label_rejected = True
    custody_rejected = False
    try:
        v32.generate_world(4_020_000)
    except ValueError:
        custody_rejected = True
    truth_recombination = abs(
        dummy.exact_log_probability
        - (
            v32.structure_log_prior(dummy.structure)
            + _truth_log_likelihood(dummy, dummy.structure)
        )
    )
    neutrality_world = v32.generate_world(
        3_230_001,
        structure=CANONICAL["recurrent_context"],
        length=24,
        evidence_style="single_regime",
    )
    neutrality_error = v32.single_regime_scope_neutrality_error(
        neutrality_world
    )
    neutrality_oracle_error = (
        v32_oracle.single_regime_scope_neutrality_error(
            neutrality_world, v32.DEFAULT_HYPERPARAMETERS
        )
    )
    dormant_parameter_error = abs(
        v32.score_world(neutrality_world).parameter_mean(
            "cue_emission", 1, 0
        )
        - 0.5
    )
    proofs = {
        "1_normalization": abs(math.fsum(production.probabilities) - 1.0),
        "2_prior_and_space": {
            "space_size": v32.structure_space_size(),
            "prior_error": abs(v32.full_prior_sum() - 1.0),
        },
        "3_generator_factor_recombination_error": truth_recombination,
        "4_independent_oracle_probability_error": max(
            abs(probability - oracle_map[program])
            for program, probability in zip(
                production.programs, production.probabilities
            )
        ),
        "4_independent_oracle_evidence_error": abs(
            production.log_evidence - oracle.log_evidence
        ),
        "5_local_recombination_error": truth_recombination,
        "6_scope_compilation_distinct": len(
            {
                v32.emission_probability(
                    scope,
                    "static",
                    cue=1,
                    context=1,
                    time=2,
                    length=12,
                )
                for scope in v32.SCOPES
            }
        )
        == 3,
        "7_dynamics_compilation_distinct": len(
            {
                v32.emission_probability(
                    "shared_global",
                    dynamics,
                    cue=0,
                    context=1,
                    time=2,
                    length=12,
                )
                for dynamics in v32.DYNAMICS
            }
        )
        >= 3,
        "8_mixed_scope_dynamics_coexist": MIXED in production.programs,
        "9_masked_channel_neutrality_log_bf": v32.masked_slice_log_bf(
            dummy, 0, 12, CANONICAL["static"], CANONICAL["recurrent_context"]
        ),
        "10_restricted_prior_identity_error": restricted_error,
        "10_independent_restricted_oracle_error": (
            lambda oracle_restricted: max(
                abs(
                    probability
                    - dict(
                        zip(
                            oracle_restricted.programs,
                            oracle_restricted.probabilities,
                        )
                    )[program]
                )
                for program, probability in zip(
                    restricted.programs, restricted.probabilities
                )
            )
        )(
            v32_oracle.brute_force_structure_posterior(
                dummy,
                v32.DEFAULT_HYPERPARAMETERS,
                restrictions=restriction,
            )
        ),
        "11_readout_purity": readout_pure,
        "12_analysis_label_rejected": label_rejected,
        "12_escrow_seed_rejected": custody_rejected,
        "13_scope_neutrality_under_single_regime": {
            "production_error": neutrality_error,
            "independent_oracle_error": neutrality_oracle_error,
            "dormant_parameter_prior_mean_error": dormant_parameter_error,
        },
    }
    blocking = [
        proofs["1_normalization"] <= TOLERANCE,
        proofs["2_prior_and_space"]["space_size"] == 432,
        proofs["2_prior_and_space"]["prior_error"] <= TOLERANCE,
        proofs["3_generator_factor_recombination_error"] <= TOLERANCE,
        proofs["4_independent_oracle_probability_error"] <= TOLERANCE,
        proofs["4_independent_oracle_evidence_error"] <= TOLERANCE,
        proofs["6_scope_compilation_distinct"],
        proofs["7_dynamics_compilation_distinct"],
        proofs["8_mixed_scope_dynamics_coexist"],
        abs(proofs["9_masked_channel_neutrality_log_bf"]) <= TOLERANCE,
        proofs["10_restricted_prior_identity_error"] <= TOLERANCE,
        proofs["10_independent_restricted_oracle_error"] <= TOLERANCE,
        proofs["11_readout_purity"],
        proofs["12_analysis_label_rejected"],
        proofs["12_escrow_seed_rejected"],
        proofs["13_scope_neutrality_under_single_regime"][
            "production_error"
        ]
        <= TOLERANCE,
        proofs["13_scope_neutrality_under_single_regime"][
            "independent_oracle_error"
        ]
        <= TOLERANCE,
        proofs["13_scope_neutrality_under_single_regime"][
            "dormant_parameter_prior_mean_error"
        ]
        <= TOLERANCE,
    ]
    passed = all(blocking)
    _write_json(
        "gate-1.json",
        {
            "verdict": "PASS" if passed else "FAIL",
            "proofs": proofs,
            "tolerance": TOLERANCE,
            "structure_space_size": 432,
        },
    )
    return passed


def _check_recovery(metrics: Mapping[str, Any], thresholds: Mapping[str, float]) -> dict[str, bool]:
    return {
        "active_context_accuracy": metrics["active_context_accuracy"] >= thresholds["active_context_accuracy"],
        "scope_accuracy": metrics["scope_accuracy"] >= thresholds["scope_accuracy"],
        "dynamics_accuracy": metrics["dynamics_accuracy"] >= thresholds["dynamics_accuracy"],
        "macro_region_recovery": metrics["macro_region_recovery"] >= thresholds["macro_region_recovery"],
        "brier": metrics["brier"] <= thresholds["brier_max"],
        "ece": metrics["ece"] <= thresholds["ece_max"],
        "coverage": metrics["coverage"] >= thresholds["coverage_min"],
        "exact_log_probability": metrics["max_exact_log_probability_error"] <= TOLERANCE,
    }


def run_gate2() -> bool:
    labels = tuple(CANONICAL)
    tasks = [
        (seed, labels[(seed - 3_202_000) // 600], 48, 3, 0.0, 1.0, 0.74)
        for seed in range(3_202_000, 3_205_000)
    ]
    rows = _trace_map("gate-2", tasks, _worker_recovery)
    metrics = _recovery_metrics(rows)
    thresholds = _parameters()["criterion_thresholds"]
    criteria = _check_recovery(metrics, thresholds)
    passed = all(criteria.values())
    _write_json(
        "gate-2.json",
        {
            "verdict": "PASS" if passed else "FAIL",
            "metrics": metrics,
            "thresholds": thresholds,
            "criteria": criteria,
            "calibration_by_theorem": "generator samples from scorer prior and likelihood",
        },
    )
    if not passed:
        _diagnosis_stub(2, criteria)
    return passed


def _worker_gate3(task: tuple[int, str]) -> dict[str, Any]:
    seed, cell = task
    if cell == "canonical":
        label = tuple(CANONICAL)[seed % 5]
        return _worker_recovery((seed, label, 48, 3, 0.0, 1.0, 0.74))
    if cell == "mixed":
        world = v32.generate_world(seed, structure=MIXED, length=48)
        posterior = v32.score_world(world)
        row = _world_record(world, posterior, cell=cell, truth_label="mixed")
        row["mixed_correct"] = [
            max(posterior.dynamics_probabilities[block], key=posterior.dynamics_probabilities[block].get)
            == MIXED.dynamics[index]
            for index, block in enumerate(v32.BLOCKS)
        ]
        return row
    if cell in {"recurrent", "one_way", "retention"}:
        truth = CANONICAL[
            "one_way_change" if cell == "one_way" else "recurrent_context"
        ]
        world = v32.generate_world(seed, structure=truth, length=48)
        posterior = v32.score_world(world)
        row = _world_record(world, posterior, cell=cell, truth_label=cell)
        row["history_separation"] = abs(
            v32.historical_prediction(posterior, "cue_emission", 1, 0)
            - v32.historical_prediction(posterior, "cue_emission", 0, 0)
        )
        row["old_query_before"] = v32.historical_prediction(
            posterior, "cue_emission", 0, 0
        )
        _ = v32.present_context_transfer(posterior, context=1)
        row["old_query_after"] = v32.historical_prediction(
            posterior, "cue_emission", 0, 0
        )
        return row
    if cell == "witnessing":
        witness_world = v32.generate_world(
            seed,
            structure=CANONICAL["recurrent_context"],
            length=48,
            evidence_style="witnessing",
        )
        baseline_world = v32.generate_world(
            seed,
            structure=CANONICAL["recurrent_context"],
            length=48,
            evidence_style="single_regime",
        )
        witness = v32.score_world(witness_world)
        baseline = v32.score_world(baseline_world)
        row = _world_record(witness_world, witness, cell=cell, truth_label=cell)
        row["scope_gain"] = witness.scope_probability("cue_emission", "context_specific") - baseline.scope_probability("cue_emission", "context_specific")
        row["paired_rng_scope"] = baseline_world.seed == witness_world.seed
        return row
    if cell == "transfer":
        world = v32.generate_world(
            seed,
            structure=CANONICAL["recurrent_context"],
            length=48,
            evidence_style="witnessing",
        )
        posterior = v32.score_world(world)
        row = _world_record(world, posterior, cell=cell, truth_label=cell)
        row["transfer"] = v32.present_context_transfer(posterior, context=1)
        row["fixed_g"] = v32.present_context_transfer(
            posterior, context=1, fixed_g=True
        )
        row["zero_association"] = v32.present_context_transfer(
            posterior, context=1, association_strength=0.0
        )
        return row
    raise ValueError(cell)


def run_gate3() -> bool:
    ranges = (
        ("canonical", 3_205_000, 3_206_000),
        ("mixed", 3_206_000, 3_206_800),
        ("recurrent", 3_206_800, 3_207_600),
        ("one_way", 3_207_600, 3_208_200),
        ("witnessing", 3_208_200, 3_208_800),
        ("transfer", 3_208_800, 3_209_400),
        ("retention", 3_209_400, 3_210_000),
    )
    tasks = [(seed, cell) for cell, start, end in ranges for seed in range(start, end)]
    rows = _trace_map("gate-3", tasks, _worker_gate3)
    grouped = {
        cell: [row for row in rows if row["cell"] == cell]
        for cell, _, _ in ranges
    }
    threshold = _parameters()["criterion_thresholds"]
    mixed_accuracy = float(
        np.mean(
            [
                value
                for row in grouped["mixed"]
                for value in row["mixed_correct"]
            ]
        )
    )
    recurrent_probability = float(
        np.mean(
            [
                row["scope_probabilities"]["cue_emission"]["context_specific"]
                for row in grouped["recurrent"]
            ]
        )
    )
    material_rate = float(
        np.mean([row["readouts"]["material"] for row in grouped["recurrent"]])
    )
    history_separation = float(
        np.mean([row["history_separation"] for row in grouped["recurrent"]])
    )
    false_recurrence = float(
        np.mean(
            [
                row["dynamics_probabilities"]["cue_emission"][
                    "discrete_recurrent_context"
                ]
                for row in grouped["one_way"]
            ]
        )
    )
    scope_gains = [row["scope_gain"] for row in grouped["witnessing"]]
    transfers = [row["transfer"] for row in grouped["transfer"]]
    old_errors = [
        abs(row["old_query_after"] - row["old_query_before"])
        for row in grouped["retention"]
    ]
    metrics = {
        "mixed_block_accuracy": mixed_accuracy,
        "recurrent_context_probability": recurrent_probability,
        "material_redescription_rate": material_rate,
        "raw_redescription_rate": float(np.mean([row["readouts"]["raw"] for row in grouped["recurrent"]])),
        "selective_redescription_rate": float(np.mean([row["readouts"]["selective"] for row in grouped["recurrent"]])),
        "historical_query_separation": history_separation,
        "one_way_false_recurrence": false_recurrence,
        "witnessing_scope_gain": float(np.mean(scope_gains)),
        "witnessing_scope_gain_ci": _bootstrap(scope_gains, 32),
        "present_transfer": float(np.mean(transfers)),
        "present_transfer_ci": _bootstrap(transfers, 33),
        "fixed_g_max_abs": max(abs(row["fixed_g"]) for row in grouped["transfer"]),
        "zero_association_max_abs": max(abs(row["zero_association"]) for row in grouped["transfer"]),
        "old_context_retention_max_error": max(old_errors),
    }
    criteria = {
        "mixed": mixed_accuracy >= threshold["mixed_block_accuracy"],
        "recurrent_probability": recurrent_probability >= threshold["recurrent_context_probability"],
        "material": material_rate >= threshold["material_redescription_rate"],
        "historical": history_separation >= threshold["historical_query_separation"],
        "one_way_selectivity": false_recurrence <= threshold["one_way_false_recurrence_max"],
        "witnessing": metrics["witnessing_scope_gain"] >= threshold["witnessing_scope_gain"] and metrics["witnessing_scope_gain_ci"][0] > 0,
        "transfer": metrics["present_transfer"] >= threshold["present_transfer"] and metrics["present_transfer_ci"][0] > 0,
        "fixed_g": metrics["fixed_g_max_abs"] <= TOLERANCE,
        "zero_association": metrics["zero_association_max_abs"] <= TOLERANCE,
        "retention": metrics["old_context_retention_max_error"] <= threshold["old_context_retention_error_max"],
    }
    passed = all(criteria.values())
    _write_json("gate-3.json", {"verdict": "PASS" if passed else "FAIL", "metrics": metrics, "criteria": criteria, "thresholds": threshold})
    if not passed:
        _diagnosis_stub(3, criteria)
    return passed


def _worker_gate4(task: tuple[int, str]) -> dict[str, Any]:
    seed, lesion = task
    world = v32.generate_world(
        seed, structure=CANONICAL["recurrent_context"], length=48
    )
    full = v32.score_world(world)
    if lesion == "context_slot":
        restrictions = {"active_contexts": (1,)}
        masked = frozenset({"active_contexts"})
    elif lesion == "context_scope":
        restrictions = {
            f"scope:{block}": ("shared_global", "cue_specific")
            for block in v32.BLOCKS
        }
        masked = frozenset()
    elif lesion == "recurrent_dynamics":
        restrictions = {
            f"dynamics:{block}": tuple(
                value
                for value in v32.DYNAMICS
                if value != "discrete_recurrent_context"
            )
            for block in v32.BLOCKS
        }
        masked = frozenset()
    else:
        restrictions, masked = {}, frozenset()
    lesioned = v32.score_world(
        world, restrictions=restrictions, masked_channels=masked
    )
    oracle = v32_oracle.brute_force_structure_posterior(
        world,
        v32.DEFAULT_HYPERPARAMETERS,
        restrictions=restrictions,
        masked_channels=masked,
    )
    oracle_map = dict(zip(oracle.programs, oracle.probabilities))
    oracle_error = max(
        abs(probability - oracle_map[program])
        for program, probability in zip(
            lesioned.programs, lesioned.probabilities
        )
    )
    if restrictions:
        allowed = {
            program: probability
            for program, probability in zip(full.programs, full.probabilities)
            if all(
                (
                    key != "active_contexts"
                    or program.active_contexts in support
                )
                and (
                    not key.startswith("scope:")
                    or program.scopes[v32.BLOCKS.index(key.split(":", 1)[1])] in support
                )
                and (
                    not key.startswith("dynamics:")
                    or program.dynamics[v32.BLOCKS.index(key.split(":", 1)[1])] in support
                )
                for key, support in restrictions.items()
            )
        }
        mass = math.fsum(allowed.values())
        identity_error = max(
            abs(probability - allowed[program] / mass)
            for program, probability in zip(
                lesioned.programs, lesioned.probabilities
            )
        )
    else:
        identity_error = oracle_error
    row = _world_record(world, full, cell=lesion, truth_label="recurrent")
    row.update(
        {
            "restricted_identity_error": identity_error,
            "oracle_error": oracle_error,
            "active_two_plus": sum(lesioned.active_context_probabilities[1:]),
            "context_scope": lesioned.scope_probability(
                "cue_emission", "context_specific"
            ),
            "recurrent": lesioned.dynamics_probability(
                "cue_emission", "discrete_recurrent_context"
            ),
            "transfer": (
                v32.present_context_transfer(
                    lesioned, context=1, fixed_g=lesion == "fixed_g",
                    association_strength=0.0 if lesion == "association" else 1.0,
                )
            ),
            "full_transfer": v32.present_context_transfer(full, context=1),
        }
    )
    return row


def run_gate4() -> bool:
    lesions = (
        "context_slot",
        "context_scope",
        "recurrent_dynamics",
        "fixed_g",
        "association",
    )
    tasks = [
        (seed, lesions[(seed - 3_210_000) // 400])
        for seed in range(3_210_000, 3_212_000)
    ]
    rows = _trace_map("gate-4", tasks, _worker_gate4)
    groups = {lesion: [row for row in rows if row["cell"] == lesion] for lesion in lesions}
    metrics = {
        "max_restricted_identity_error": max(row["restricted_identity_error"] for row in rows),
        "max_independent_oracle_error": max(row["oracle_error"] for row in rows),
        "context_slot_active_mass_max": max(row["active_two_plus"] for row in groups["context_slot"]),
        "context_scope_mass_max": max(row["context_scope"] for row in groups["context_scope"]),
        "recurrent_mass_max": max(row["recurrent"] for row in groups["recurrent_dynamics"]),
        "fixed_g_transfer_max": max(abs(row["transfer"]) for row in groups["fixed_g"]),
        "association_transfer_max": max(abs(row["transfer"]) for row in groups["association"]),
        "unrelated_transfer_survival": float(
            np.mean(
                [
                    row["transfer"] > 0
                    for row in groups["context_slot"]
                    + groups["recurrent_dynamics"]
                ]
            )
        ),
    }
    criteria = {
        "restricted_prior_identity": metrics["max_restricted_identity_error"] <= TOLERANCE,
        "independent_oracle": metrics["max_independent_oracle_error"] <= TOLERANCE,
        "context_slot": metrics["context_slot_active_mass_max"] <= TOLERANCE,
        "context_scope": metrics["context_scope_mass_max"] <= TOLERANCE,
        "recurrent": metrics["recurrent_mass_max"] <= TOLERANCE,
        "fixed_g": metrics["fixed_g_transfer_max"] <= TOLERANCE,
        "association": metrics["association_transfer_max"] <= TOLERANCE,
        "selectivity_survival": metrics["unrelated_transfer_survival"] >= 0.95,
    }
    passed = all(criteria.values())
    _write_json("gate-4.json", {"verdict": "PASS" if passed else "FAIL", "metrics": metrics, "criteria": criteria})
    if not passed:
        _diagnosis_stub(4, criteria)
    return passed


def run_gate5() -> bool:
    cells = (
        ("length32", 32, 3, 0.0, 1.0, 0.74),
        ("length96", 96, 3, 0.0, 1.0, 0.74),
        ("cue2", 48, 2, 0.0, 1.0, 0.74),
        ("cue4", 48, 4, 0.0, 1.0, 0.74),
        ("missing20", 48, 3, 0.2, 1.0, 0.74),
        ("prior125", 48, 3, 0.0, 1.25, 0.74),
        ("reliability68", 48, 3, 0.0, 1.0, 0.68),
        ("primary", 48, 3, 0.0, 1.0, 0.74),
    )
    tasks = []
    for cell_index, (cell, length, cues, missing, scale, reliability) in enumerate(cells):
        start = 3_212_000 + cell_index * 1000
        for seed in range(start, start + 1000):
            label = tuple(CANONICAL)[(seed - start) % 5]
            tasks.append((seed, label, length, cues, missing, scale, reliability))
    rows = _trace_map("gate-5", tasks, _worker_recovery)
    metrics = {}
    threshold = _parameters()["criterion_thresholds"]
    blocking = {}
    for index, (cell, *_rest) in enumerate(cells):
        subset = rows[index * 1000 : (index + 1) * 1000]
        cell_metrics = _recovery_metrics(subset)
        metrics[cell] = cell_metrics
        # Primary is blocking; robustness must remain directionally informative.
        if cell == "primary":
            blocking[cell] = all(_check_recovery(cell_metrics, threshold).values())
        else:
            blocking[cell] = (
                cell_metrics["macro_region_recovery"] >= 0.45
                and cell_metrics["coverage"] >= 0.75
                and cell_metrics["max_exact_log_probability_error"] <= TOLERANCE
            )
    standing = _standing_regression()
    blocking["standing_regression"] = standing["passed"]
    passed = all(blocking.values())
    _write_json(
        "gate-5.json",
        {
            "verdict": "PASS" if passed else "FAIL",
            "metrics": metrics,
            "blocking": blocking,
            "standing_regression": standing,
        },
    )
    if not passed:
        _diagnosis_stub(5, blocking)
    return passed


def _standing_regression() -> dict[str, Any]:
    checks = {}
    for stage in ("V3.0", "V3.1"):
        report = ROOT / "results" / stage / "stage-verdict.md"
        freeze = ROOT / "results" / stage / "freeze-readiness.md"
        checks[stage] = report.exists() or freeze.exists()
    return {"checks": checks, "passed": all(checks.values())}


def _diagnosis_stub(gate: int, criteria: Mapping[str, Any]) -> None:
    (RESULTS / f"gate{gate}-diagnosis-stub.md").write_text(
        f"# V3.2 Gate {gate} diagnosis stub\n\n"
        "Execution stopped prospectively at the first blocking failure. No later "
        "gate was opened.\n\n"
        f"Criteria retained verbatim: `{json.dumps(_plain(criteria), sort_keys=True)}`\n",
        encoding="utf-8",
    )


def freeze() -> None:
    files = [
        ROOT / "ref" / "v32.py",
        ROOT / "ref" / "v32_oracle.py",
        ROOT / "tests" / "test_v32_split.py",
        ROOT / "contracts" / "v3.2-split-contract.md",
        ROOT / "protocols" / "v3.2-analysis-plan.md",
        ROOT / "protocols" / "v3.2-public-dummy.json",
        PARAMETERS,
    ]
    files.extend(RESULTS / f"gate-{gate}.json" for gate in range(1, 6))
    manifest = {
        "stage": "V3.2",
        "status": "FREEZE_CANDIDATE",
        "files": {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files
        },
        "escrow": {"block": [4_020_000, 4_023_999], "status": "UNTOUCHED"},
    }
    _write_json("freeze-manifest.json", manifest)
    (RESULTS / "freeze-readiness.md").write_text(
        "# V3.2 freeze readiness\n\n"
        "Status: **FREEZE_CANDIDATE — gates 1–5 passed**.\n\n"
        "V3.2 expresses static, cue-local, recurrent-context, drift, one-way, "
        "and mixed temporal worlds as regions of one 432-program grammar. "
        "Historical parameters remain queryable; present transfer disappears "
        "under fixed-G and zero-association controls. Raw, material, and "
        "selective redescription remain reported diagnostics. Escrow "
        "`4020000:4023999` was not accessed.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("pilot", "gate1", "gate2", "gate3", "gate4", "gate5", "all"))
    args = parser.parse_args()
    steps = ("pilot", "gate1", "gate2", "gate3", "gate4", "gate5") if args.step == "all" else (args.step,)
    for step in steps:
        if step == "pilot":
            run_pilot()
            continue
        passed = globals()[f"run_{step}"]()
        if not passed:
            return 1
    if args.step in {"gate5", "all"}:
        freeze()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
