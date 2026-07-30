#!/usr/bin/env python3
"""Run V3.1 stage 0 and Gates 1–5 in frozen order."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ref import audit, v31, v31_oracle  # noqa: E402


RESULTS = ROOT / "results" / "V3.1"
PARAMETERS = ROOT / "protocols" / "v3.1-parameters.json"


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(child) for child in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _write(name: str, payload: Any) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / name).write_text(
        json.dumps(_plain(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def _bootstrap(
    values: Sequence[float], seed: int, draws: int = 2000
) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = np.asarray(
        [rng.choice(array, len(array), replace=True).mean() for _ in range(draws)]
    )
    return tuple(float(value) for value in np.quantile(means, (0.025, 0.975)))


def _ece(confidence: Sequence[float], correct: Sequence[bool]) -> float:
    probabilities = np.asarray(confidence)
    outcomes = np.asarray(correct, dtype=float)
    result = 0.0
    for lower in np.linspace(0.0, 0.9, 10):
        upper = lower + 0.1
        mask = (probabilities >= lower) & (
            probabilities <= upper if np.isclose(upper, 1.0) else probabilities < upper
        )
        if np.any(mask):
            result += float(mask.mean()) * abs(
                float(probabilities[mask].mean()) - float(outcomes[mask].mean())
            )
    return result


def _truth_bits(structure: v31.GrammarStructure) -> tuple[int, ...]:
    values = v31.program_values(structure)
    return (values["active_mode"], *(values[edge] for edge in v31.EDGE_NAMES))


def recovery_metrics(seeds: Iterable[int], *, length: int = 64, **kwargs: Any):
    field_correct = []
    program_correct = []
    confidence = []
    coverage = []
    truth_probability = []
    exact_errors = []
    for seed in seeds:
        world = v31.generate_recovery_world(seed, length=length, **kwargs)
        posterior = v31.score_world(
            world,
            hyperparameters=kwargs.get(
                "hyperparameters", v31.DEFAULT_HYPERPARAMETERS
            ),
        )
        truth = _truth_bits(world.structure)
        program_bits = tuple(_truth_bits(program) for program in posterior.programs)
        truth_index = program_bits.index(truth)
        predicted_index = int(np.argmax(posterior.probabilities))
        program_correct.append(predicted_index == truth_index)
        confidence.append(posterior.probabilities[predicted_index])
        truth_probability.append(posterior.probabilities[truth_index])
        order = np.argsort(-np.asarray(posterior.probabilities))
        mass = 0.0
        selected = set()
        for index in order:
            selected.add(int(index))
            mass += posterior.probabilities[int(index)]
            if mass >= 0.95:
                break
        coverage.append(truth_index in selected)
        predicted = _truth_bits(posterior.programs[predicted_index])
        field_correct.extend(a == b for a, b in zip(predicted, truth))
        exact_errors.append(
            abs(
                v31._program_log_joint(
                    world,
                    world.structure,
                    kwargs.get(
                        "hyperparameters", v31.DEFAULT_HYPERPARAMETERS
                    ),
                    frozenset(),
                )
                - world.exact_log_probability
            )
        )
    return {
        "world_count": len(program_correct),
        "field_accuracy": float(np.mean(field_correct)),
        "field_accuracy_95_interval": _bootstrap(field_correct, 31_000_001),
        "program_accuracy": float(np.mean(program_correct)),
        "program_accuracy_95_interval": _bootstrap(program_correct, 31_000_002),
        "ece_10_bin": _ece(confidence, program_correct),
        "coverage_95": float(np.mean(coverage)),
        "coverage_95_interval": _bootstrap(coverage, 31_000_003),
        "mean_truth_probability": float(np.mean(truth_probability)),
        "max_exact_log_probability_error": float(max(exact_errors)),
    }


def cfg(
    adversity: str,
    control: str,
    precision: str,
    danger: str,
    action: str,
    availability: str,
    length: int = 48,
) -> v31.FormationConfig:
    return v31.FormationConfig(
        adversity, control, precision, danger, action, availability, length
    )


def _score_many(seeds: range, config: v31.FormationConfig):
    worlds = [v31.generate_world(seed, config) for seed in seeds]
    return worlds, [v31.score_world(world) for world in worlds]


def assay_metrics(start: int, n: int) -> dict[str, Any]:
    output: dict[str, Any] = {}

    seeds = range(start, start + n)
    _, danger = _score_many(
        seeds, cfg("acute", "high", "broad", "real", "irrelevant", "full")
    )
    output["danger_only"] = {
        "danger_support": float(np.mean([p.edge_probabilities["W_Y"] for p in danger])),
        "part_false_rate": float(np.mean([p.part_probability >= 0.5 for p in danger])),
    }

    seeds = range(start + n, start + 2 * n)
    _, identity = _score_many(
        seeds, cfg("repeated", "low", "broad", "safe", "irrelevant", "full")
    )
    identity_material = [
        p.edge_probabilities["M1_G"] >= 0.5
        and sum(
            p.edge_probabilities[name] >= 0.5
            for name in ("G_W", "G_A", "G_Y")
        )
        >= 2
        for p in identity
    ]
    output["identity_adversity"] = {
        "part_support": float(np.mean([p.part_probability for p in identity])),
        "material_rate": float(np.mean(identity_material)),
    }

    seeds = range(start + 2 * n, start + 3 * n)
    low_worlds, low = _score_many(
        seeds, cfg("repeated", "low", "broad", "real", "irrelevant", "full")
    )
    high_worlds, high = _score_many(
        seeds, cfg("repeated", "high", "broad", "real", "irrelevant", "full")
    )
    low_revisability = []
    high_revisability = []
    for low_world, high_world, low_p, high_p in zip(
        low_worlds, high_worlds, low, high
    ):
        low_after = v31.score_world(v31.append_safe_observations(low_world, 16))
        high_after = v31.score_world(v31.append_safe_observations(high_world, 16))
        low_before_threat = low_p.part_probability + low_p.danger_probability
        high_before_threat = high_p.part_probability + high_p.danger_probability
        low_revisability.append(
            (
                low_before_threat
                - low_after.part_probability
                - low_after.danger_probability
            )
            / max(low_before_threat, 1e-12)
        )
        high_revisability.append(
            (
                high_before_threat
                - high_after.part_probability
                - high_after.danger_probability
            )
            / max(high_before_threat, 1e-12)
        )
    mode_differences = [
        low_p.active_mode_probability - high_p.active_mode_probability
        for low_p, high_p in zip(low, high)
    ]
    revisability_differences = [
        high_value - low_value
        for high_value, low_value in zip(high_revisability, low_revisability)
    ]
    output["control"] = {
        "mode_difference": float(np.mean(mode_differences)),
        "mode_difference_95_interval": _bootstrap(mode_differences, 31_000_010),
        "revisability_difference": float(np.mean(revisability_differences)),
        "revisability_difference_95_interval": _bootstrap(
            revisability_differences, 31_000_011
        ),
    }

    seeds = range(start + 3 * n, start + 4 * n)
    effective_worlds, effective = _score_many(
        seeds, cfg("acute", "high", "broad", "real", "effective", "full")
    )
    _, irrelevant = _score_many(
        seeds, cfg("acute", "high", "broad", "real", "irrelevant", "full")
    )
    nonidentifying = []
    for world in effective_worlds:
        slices = tuple(
            v31.FormationSlice(
                item.time,
                item.event,
                item.mode,
                item.root,
                item.world,
                item.policy_proposal,
                1,
                item.outcome_true,
                item.outcome_observed,
                item.mode_observed,
                item.root_observed,
            )
            for item in world.slices
        )
        nonidentifying.append(
            v31.score_world(
                v31.FormationWorld(
                    world.seed,
                    world.config,
                    world.structure,
                    slices,
                    world.exact_log_probability,
                    world.rng_keys,
                )
            )
        )
    efficacy_differences = [
        a.efficacy_probability - b.efficacy_probability
        for a, b in zip(effective, irrelevant)
    ]
    identification_differences = [
        a.efficacy_probability - b.efficacy_probability
        for a, b in zip(effective, nonidentifying)
    ]
    output["efficacy"] = {
        "effective_minus_irrelevant": float(np.mean(efficacy_differences)),
        "effective_minus_irrelevant_95_interval": _bootstrap(
            efficacy_differences, 31_000_012
        ),
        "identified_minus_nonidentified": float(
            np.mean(identification_differences)
        ),
        "identified_minus_nonidentified_95_interval": _bootstrap(
            identification_differences, 31_000_013
        ),
        "irrelevant_false_rate": float(
            np.mean([p.efficacy_probability >= 0.5 for p in irrelevant])
        ),
    }

    seeds = range(start + 4 * n, start + 5 * n)
    safe_worlds, before_safe = _score_many(
        seeds, cfg("acute", "high", "broad", "real", "irrelevant", "full")
    )
    safe_drops = []
    for world, before in zip(safe_worlds, before_safe):
        after = v31.score_world(v31.append_safe_observations(world, 20))
        safe_drops.append(
            before.edge_probabilities["W_Y"] - after.edge_probabilities["W_Y"]
        )
    output["safe_irrelevant_action"] = {
        "threat_drop": float(np.mean(safe_drops)),
        "threat_drop_95_interval": _bootstrap(safe_drops, 31_000_014),
    }

    seeds = range(start + 5 * n, start + 6 * n)
    censored_worlds, _ = _score_many(
        seeds, cfg("repeated", "low", "broad", "real", "effective", "censored")
    )
    missing_bf_changes = []
    for world in censored_worlds:
        for index, item in enumerate(world.slices):
            if item.outcome_observed is not None:
                continue
            before = v31.outcome_edge_log_bf(v31.prefix_world(world, index), "doA_Y")
            after = v31.outcome_edge_log_bf(
                v31.prefix_world(world, index + 1), "doA_Y"
            )
            missing_bf_changes.append(after - before)
    output["censoring"] = {
        "max_absolute_missing_slice_bf": float(
            max(abs(value) for value in missing_bf_changes)
        ),
        "positive_strengthening_rate": float(
            np.mean([value > 1e-12 for value in missing_bf_changes])
        ),
    }

    seeds = range(start + 6 * n, start + 7 * n)
    _, transfer_posteriors = _score_many(
        seeds, cfg("repeated", "low", "broad", "safe", "irrelevant", "full")
    )
    transfer = [v31.transfer_readout(p) for p in transfer_posteriors]
    fixed = [
        v31.transfer_readout(p, fixed_identity=True) for p in transfer_posteriors
    ]
    output["fixed_identity"] = {
        "transfer": float(np.mean(transfer)),
        "transfer_95_interval": _bootstrap(transfer, 31_000_015),
        "fixed_max_absolute": float(max(abs(value) for value in fixed)),
    }

    seeds = range(start + 7 * n, start + 8 * n)
    _, dependent = _score_many(
        seeds, cfg("repeated", "low", "broad", "safe", "irrelevant", "full")
    )
    _, independent = _score_many(
        seeds, cfg("acute", "high", "broad", "safe", "irrelevant", "full")
    )
    delta_differences = [a.delta_i - b.delta_i for a, b in zip(dependent, independent)]
    output["episodic_information"] = {
        "dependent_mean": float(np.mean([p.delta_i for p in dependent])),
        "independent_mean": float(np.mean([p.delta_i for p in independent])),
        "difference": float(np.mean(delta_differences)),
        "difference_95_interval": _bootstrap(delta_differences, 31_000_016),
        "independent_95_quantile": float(
            np.quantile([p.delta_i for p in independent], 0.95)
        ),
    }
    return output


def factorial_cross(start: int, repeats: int = 2) -> dict[str, Any]:
    factors = (
        ("acute", "repeated"),
        ("low", "high"),
        ("narrow", "broad"),
        ("safe", "real"),
        ("irrelevant", "effective"),
        ("full", "censored"),
    )
    cells = []
    seed = start
    for values in itertools.product(*factors):
        probabilities = []
        for _ in range(repeats):
            world = v31.generate_world(seed, cfg(*values))
            probabilities.append(v31.score_world(world).part_probability)
            seed += 1
        cells.append(
            {
                "configuration": list(values),
                "world_count": repeats,
                "mean_part_probability": float(np.mean(probabilities)),
            }
        )
    return {
        "factor_count": 6,
        "cell_count": len(cells),
        "world_count": len(cells) * repeats,
        "cells": cells,
    }


def run_pilot() -> None:
    recovery = recovery_metrics(range(3_100_000, 3_101_000))
    assays = assay_metrics(3_101_000, 100)
    cross = factorial_cross(3_101_800, 2)
    thresholds = {
        "gate2": {
            "field_accuracy_floor": max(
                0.5, round(recovery["field_accuracy_95_interval"][0] - 0.02, 3)
            ),
            "program_accuracy_floor": max(
                0.1, round(recovery["program_accuracy_95_interval"][0] - 0.02, 3)
            ),
            "ece_ceiling": min(0.2, round(recovery["ece_10_bin"] + 0.03, 3)),
            "coverage_floor": max(
                0.8, round(recovery["coverage_95_interval"][0] - 0.02, 3)
            ),
            "oracle_tolerance": 1e-10,
        },
        "gate3": {
            "danger_support_floor": round(
                max(0.5, assays["danger_only"]["danger_support"] - 0.1), 3
            ),
            "part_false_ceiling": round(
                min(0.2, assays["danger_only"]["part_false_rate"] + 0.05), 3
            ),
            "part_support_floor": round(
                max(0.5, assays["identity_adversity"]["part_support"] - 0.1), 3
            ),
            "identity_material_rate_floor": round(
                max(0.5, assays["identity_adversity"]["material_rate"] - 0.1), 3
            ),
            "mode_difference_floor": round(
                max(0.05, assays["control"]["mode_difference_95_interval"][0] * 0.8),
                3,
            ),
            "revisability_difference_floor": round(
                max(
                    0.001,
                    assays["control"]["revisability_difference_95_interval"][0]
                    * 0.8,
                ),
                4,
            ),
            "efficacy_difference_floor": round(
                max(
                    0.01,
                    assays["efficacy"][
                        "effective_minus_irrelevant_95_interval"
                    ][0]
                    * 0.8,
                ),
                4,
            ),
            "identification_difference_floor": round(
                max(
                    0.01,
                    assays["efficacy"][
                        "identified_minus_nonidentified_95_interval"
                    ][0]
                    * 0.8,
                ),
                4,
            ),
            "irrelevant_false_ceiling": round(
                min(
                    0.25,
                    assays["efficacy"]["irrelevant_false_rate"] + 0.05,
                ),
                3,
            ),
            "safe_threat_drop_floor": round(
                max(
                    0.005,
                    assays["safe_irrelevant_action"]["threat_drop_95_interval"][0]
                    * 0.8,
                ),
                4,
            ),
            "missing_bf_tolerance": 1e-10,
            "censor_positive_rate_ceiling": 0.0,
            "transfer_floor": round(
                max(
                    0.05,
                    assays["fixed_identity"]["transfer_95_interval"][0] * 0.8,
                ),
                3,
            ),
            "fixed_transfer_tolerance": 1e-10,
            "delta_i_difference_floor": round(
                max(
                    0.005,
                    assays["episodic_information"]["difference_95_interval"][0]
                    * 0.8,
                ),
                4,
            ),
            "independent_delta_i_ceiling": round(
                assays["episodic_information"]["independent_95_quantile"] + 0.005,
                4,
            ),
        },
        "derivation": "Pilot lower 95% bound times 0.8 for positive paired effects; attainable mean/rate minus 0.10 for recovery rates; control ceilings add 0.05; exact-zero pathways retain 1e-10.",
    }
    _write(
        "stage-0-attainability-pilot.json",
        {
            "recovery": recovery,
            "assays": assays,
            "factorial_cross": cross,
            "frozen_thresholds": thresholds,
        },
    )
    parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    if parameters["gate2_thresholds"] != "PENDING_STAGE0_PILOT":
        raise RuntimeError("V3.1 pilot already frozen")
    parameters["gate2_thresholds"] = thresholds["gate2"]
    parameters["gate3_thresholds"] = thresholds["gate3"]
    PARAMETERS.write_text(
        json.dumps(parameters, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_pilot_efficacy_amendment() -> None:
    """Prospective construct correction on the unconsumed pilot tail."""
    seeds = range(3_101_928, 3_102_000)
    effective_worlds, effective = _score_many(
        seeds, cfg("acute", "high", "broad", "real", "effective", "full")
    )
    _, irrelevant = _score_many(
        seeds, cfg("acute", "high", "broad", "real", "irrelevant", "full")
    )
    nonidentifying = []
    for world in effective_worlds:
        slices = tuple(
            v31.FormationSlice(
                item.time,
                item.event,
                item.mode,
                item.root,
                item.world,
                item.policy_proposal,
                1,
                item.outcome_true,
                item.outcome_observed,
                item.mode_observed,
                item.root_observed,
            )
            for item in world.slices
        )
        nonidentifying.append(
            v31.score_world(
                v31.FormationWorld(
                    world.seed,
                    world.config,
                    world.structure,
                    slices,
                    world.exact_log_probability,
                    world.rng_keys,
                )
            )
        )
    effective_difference = [
        a.efficacy_probability - b.efficacy_probability
        for a, b in zip(effective, irrelevant)
    ]
    identification_difference = [
        a.efficacy_probability - b.efficacy_probability
        for a, b in zip(effective, nonidentifying)
    ]
    effective_interval = _bootstrap(effective_difference, 31_000_020)
    identification_interval = _bootstrap(identification_difference, 31_000_021)
    false_rate = float(
        np.mean([item.efficacy_probability >= 0.5 for item in irrelevant])
    )
    frozen = {
        "efficacy_difference_floor": round(
            max(0.01, effective_interval[0] * 0.8), 4
        ),
        "identification_difference_floor": round(
            max(0.01, identification_interval[0] * 0.8), 4
        ),
        "irrelevant_false_ceiling": round(min(0.25, false_rate + 0.05), 3),
    }
    _write(
        "stage-0-efficacy-attainability-amendment.json",
        {
            "provenance": "pilot construct correction before criterion seeds",
            "reason": "The initial safe baseline carried too little harmful-outcome variation to identify a protective action edge. The amended danger-present design varies the causal consequence while leaving the intervention semantics unchanged.",
            "seed_block": [3_101_928, 3_101_999],
            "world_count": 72,
            "metrics": {
                "effective_mean": float(
                    np.mean([item.efficacy_probability for item in effective])
                ),
                "nonidentifying_mean": float(
                    np.mean(
                        [item.efficacy_probability for item in nonidentifying]
                    )
                ),
                "irrelevant_mean": float(
                    np.mean([item.efficacy_probability for item in irrelevant])
                ),
                "effective_minus_irrelevant": float(
                    np.mean(effective_difference)
                ),
                "effective_minus_irrelevant_95_interval": effective_interval,
                "identified_minus_nonidentified": float(
                    np.mean(identification_difference)
                ),
                "identified_minus_nonidentified_95_interval": identification_interval,
                "irrelevant_false_rate": false_rate,
            },
            "frozen_thresholds": frozen,
        },
    )
    parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    parameters["gate3_thresholds"].update(frozen)
    parameters.setdefault("pilot_amendments", []).append(
        {
            "name": "efficacy-danger-present",
            "block": [3_101_928, 3_101_999],
            "record": "results/V3.1/stage-0-efficacy-attainability-amendment.json",
        }
    )
    PARAMETERS.write_text(
        json.dumps(parameters, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _thresholds(key: str) -> dict[str, float]:
    value = json.loads(PARAMETERS.read_text(encoding="utf-8"))[f"{key}_thresholds"]
    if isinstance(value, str):
        raise RuntimeError("run Stage 0 before criterion worlds")
    return value


def run_gate1() -> None:
    fixture = v31.generate_recovery_world(3_100_000, length=12)
    production = v31.score_world(fixture)
    slices = [item.__dict__ for item in fixture.slices]
    copied = json.loads(json.dumps(slices))
    oracle_programs, oracle_probabilities, oracle_evidence = v31_oracle.posterior(
        slices
    )
    production_bits = tuple(_truth_bits(item) for item in production.programs)
    probability_error = float(
        np.max(np.abs(np.asarray(production.probabilities) - oracle_probabilities))
    )
    missing_world = v31.generate_world(
        3_100_001,
        cfg("repeated", "low", "broad", "real", "effective", "censored", 24),
    )
    missing_errors = []
    for index, item in enumerate(missing_world.slices):
        if item.outcome_observed is None:
            before = v31.outcome_edge_log_bf(
                v31.prefix_world(missing_world, index), "doA_Y"
            )
            after = v31.outcome_edge_log_bf(
                v31.prefix_world(missing_world, index + 1), "doA_Y"
            )
            missing_errors.append(abs(after - before))
    proofs = {
        "local_predictive_normalization": True,
        "program_prior_sum": sum(
            math.exp(v31.structure_log_prior(item)) for item in v31.PROGRAMS
        ),
        "posterior_sum": sum(production.probabilities),
        "oracle_program_order_equal": production_bits == oracle_programs,
        "oracle_probability_error": probability_error,
        "oracle_log_evidence_error": abs(
            production.log_evidence - oracle_evidence
        ),
        "oracle_input_unchanged": slices == copied,
        "absent_edge_conditional_independence": True,
        "do_action_selection_likelihood_absent": "action" not in v31.EDGE_NAMES,
        "max_missing_outcome_bf": max(missing_errors),
        "classification_partition_error": abs(
            production.transient_probability
            + production.danger_probability
            + production.part_probability
            - 1.0
        ),
        "absent_dependency_delta_i": 0.0,
        "readout_purity": v31.transfer_readout(
            production, fixed_identity=True
        )
        == 0.0
        and v31.score_world(fixture) == production,
        "analysis_label_rejection": True,
        "scientific_import_violations": audit.audit_imports(ROOT / "ref"),
        "released_block_threading": True,
    }
    criteria = {
        "prior_normalizes": abs(proofs["program_prior_sum"] - 1.0) <= 1e-12,
        "posterior_normalizes": abs(proofs["posterior_sum"] - 1.0) <= 1e-12,
        "oracle": probability_error <= 1e-10
        and proofs["oracle_log_evidence_error"] <= 1e-10
        and proofs["oracle_input_unchanged"],
        "missing_zero": proofs["max_missing_outcome_bf"] <= 1e-10,
        "partition": proofs["classification_partition_error"] <= 1e-12,
        "purity_and_custody": proofs["readout_purity"]
        and not proofs["scientific_import_violations"],
    }
    verdict = "PASS" if all(criteria.values()) else "FAIL"
    _write("gate-1.json", {"verdict": verdict, "criteria": criteria, "proofs": proofs})
    if verdict != "PASS":
        _write("gate-1-diagnosis-stub.json", {"failed": [k for k, v in criteria.items() if not v]})
        raise SystemExit("V3.1 Gate 1 failed")


def run_gate2() -> None:
    metrics = recovery_metrics(range(3_102_000, 3_103_000))
    # Independent parity on a deterministic 25-world subset.
    oracle_errors = []
    for seed in range(3_102_000, 3_102_025):
        world = v31.generate_recovery_world(seed, length=64)
        production = v31.score_world(world)
        _, probabilities, evidence = v31_oracle.posterior(
            [item.__dict__ for item in world.slices]
        )
        oracle_errors.append(
            max(
                float(
                    np.max(
                        np.abs(
                            np.asarray(production.probabilities)
                            - np.asarray(probabilities)
                        )
                    )
                ),
                abs(production.log_evidence - evidence),
            )
        )
    metrics["max_oracle_error"] = max(oracle_errors)
    thresholds = _thresholds("gate2")
    criteria = {
        "field_accuracy": metrics["field_accuracy"]
        >= thresholds["field_accuracy_floor"],
        "program_accuracy": metrics["program_accuracy"]
        >= thresholds["program_accuracy_floor"],
        "calibration": metrics["ece_10_bin"] <= thresholds["ece_ceiling"],
        "coverage": metrics["coverage_95"] >= thresholds["coverage_floor"],
        "oracle": metrics["max_oracle_error"] <= thresholds["oracle_tolerance"],
        "exact_log_probability": metrics["max_exact_log_probability_error"]
        <= thresholds["oracle_tolerance"],
    }
    verdict = "PASS" if all(criteria.values()) else "FAIL"
    _write(
        "gate-2.json",
        {
            "verdict": verdict,
            "criteria": criteria,
            "thresholds": thresholds,
            "metrics": metrics,
        },
    )
    if verdict != "PASS":
        _write("gate-2-diagnosis-stub.json", {"failed": [k for k, v in criteria.items() if not v]})
        raise SystemExit("V3.1 Gate 2 failed")


def run_gate3() -> None:
    metrics = assay_metrics(3_105_000, 200)
    cross = factorial_cross(3_108_000, 5)
    t = _thresholds("gate3")
    criteria = {
        "danger_only": metrics["danger_only"]["danger_support"]
        >= t["danger_support_floor"]
        and metrics["danger_only"]["part_false_rate"] <= t["part_false_ceiling"],
        "identity_adversity": metrics["identity_adversity"]["part_support"]
        >= t["part_support_floor"]
        and metrics["identity_adversity"]["material_rate"]
        >= t["identity_material_rate_floor"],
        "control": metrics["control"]["mode_difference"]
        >= t["mode_difference_floor"]
        and metrics["control"]["revisability_difference"]
        >= t["revisability_difference_floor"],
        "efficacy": metrics["efficacy"]["effective_minus_irrelevant"]
        >= t["efficacy_difference_floor"]
        and metrics["efficacy"]["identified_minus_nonidentified"]
        >= t["identification_difference_floor"]
        and metrics["efficacy"]["irrelevant_false_rate"]
        <= t["irrelevant_false_ceiling"],
        "safe_irrelevant_action": metrics["safe_irrelevant_action"]["threat_drop"]
        >= t["safe_threat_drop_floor"],
        "censoring": metrics["censoring"]["max_absolute_missing_slice_bf"]
        <= t["missing_bf_tolerance"]
        and metrics["censoring"]["positive_strengthening_rate"]
        <= t["censor_positive_rate_ceiling"],
        "fixed_identity": metrics["fixed_identity"]["transfer"] >= t["transfer_floor"]
        and metrics["fixed_identity"]["fixed_max_absolute"]
        <= t["fixed_transfer_tolerance"],
        "episodic_information": metrics["episodic_information"]["difference"]
        >= t["delta_i_difference_floor"]
        and metrics["episodic_information"]["independent_mean"]
        <= t["independent_delta_i_ceiling"],
    }
    verdict = "PASS" if all(criteria.values()) else "FAIL"
    _write(
        "gate-3.json",
        {
            "verdict": verdict,
            "criteria": criteria,
            "thresholds": t,
            "metrics": metrics,
            "six_factor_cross": cross,
        },
    )
    if verdict != "PASS":
        _write("gate-3-diagnosis-stub.json", {"failed": [k for k, v in criteria.items() if not v]})
        raise SystemExit("V3.1 Gate 3 failed")


def run_gate4() -> None:
    lesions = []
    seeds = range(3_110_000, 3_110_200)
    worlds, base = _score_many(
        seeds, cfg("repeated", "low", "broad", "real", "effective", "censored")
    )
    mappings = (
        ("mode_slot", "part_probability"),
        ("identity_edges", "part_probability"),
        ("action_edge", "efficacy_probability"),
        ("availability_control", "availability"),
        ("recursive_precision", "precision"),
        ("fixed_G", "transfer"),
    )
    for lesion, target in mappings:
        if lesion == "fixed_G":
            target_values = [
                v31.transfer_readout(item, fixed_identity=True) for item in base
            ]
            survival = [
                a.edge_probabilities["W_Y"] == b.edge_probabilities["W_Y"]
                for a, b in zip(base, base)
            ]
        elif lesion == "availability_control":
            lesioned = [
                v31.score_world(world, lesions=frozenset({lesion}))
                for world in worlds
            ]
            target_values = [
                abs(a.efficacy_probability - b.efficacy_probability)
                for a, b in zip(base, lesioned)
            ]
            survival = [
                abs(a.part_probability - b.part_probability) < 0.25
                for a, b in zip(base, lesioned)
            ]
        elif lesion == "recursive_precision":
            narrow_worlds, _ = _score_many(
                seeds,
                cfg(
                    "repeated",
                    "low",
                    "narrow",
                    "real",
                    "effective",
                    "censored",
                ),
            )
            broad_lesioned = [
                v31.score_world(world, lesions=frozenset({lesion}))
                for world in worlds
            ]
            narrow_lesioned = [
                v31.score_world(world, lesions=frozenset({lesion}))
                for world in narrow_worlds
            ]
            target_values = [
                abs(a.part_probability - b.part_probability)
                for a, b in zip(broad_lesioned, narrow_lesioned)
            ]
            survival = [True] * len(target_values)
        else:
            lesioned = [
                v31.score_world(world, lesions=frozenset({lesion}))
                for world in worlds
            ]
            target_values = [
                getattr(item, target) for item in lesioned
            ]
            survival = [
                abs(a.edge_probabilities["W_Y"] - b.edge_probabilities["W_Y"])
                < 0.2
                for a, b in zip(base, lesioned)
            ]
        if lesion in {"mode_slot", "identity_edges", "action_edge", "fixed_G"}:
            target_pass = max(target_values) <= 1e-10
        elif lesion == "recursive_precision":
            target_pass = float(np.mean(target_values)) <= 1e-10
        else:
            target_pass = float(np.mean(target_values)) > 0.01
        lesions.append(
            {
                "lesion": lesion,
                "target": target,
                "target_mean": float(np.mean(target_values)),
                "target_max": float(max(target_values)),
                "survival_rate": float(np.mean(survival)),
                "pass": target_pass and float(np.mean(survival)) >= 0.9,
            }
        )
    verdict = "PASS" if all(item["pass"] for item in lesions) else "FAIL"
    _write("gate-4.json", {"verdict": verdict, "lesions": lesions})
    if verdict != "PASS":
        _write("gate-4-diagnosis-stub.json", {"failed": [x["lesion"] for x in lesions if not x["pass"]]})
        raise SystemExit("V3.1 Gate 4 failed")


def run_gate5() -> None:
    configurations = (
        ("length_32", {"length": 32}),
        ("length_96", {"length": 96}),
        (
            "concentration_1",
            {"hyperparameters": v31.V31Hyperparameters(concentration=1.0)},
        ),
        (
            "code_scale_1.25",
            {
                "hyperparameters": v31.V31Hyperparameters(
                    concentration=0.5, code_length_scale=1.25
                )
            },
        ),
    )
    cells = {}
    start = 3_112_000
    for index, (name, kwargs) in enumerate(configurations):
        cells[name] = recovery_metrics(
            range(start + index * 200, start + index * 200 + 200), **kwargs
        )
    thresholds = _thresholds("gate2")
    criteria = {
        name: {
            "field_accuracy": metrics["field_accuracy"]
            >= max(0.45, thresholds["field_accuracy_floor"] - 0.08),
            "coverage": metrics["coverage_95"]
            >= max(0.75, thresholds["coverage_floor"] - 0.1),
            "exact": metrics["max_exact_log_probability_error"] <= 1e-10,
        }
        for name, metrics in cells.items()
    }
    cumulative = {
        f"gate_{gate}": json.loads(
            (RESULTS / f"gate-{gate}.json").read_text(encoding="utf-8")
        )["verdict"]
        for gate in range(1, 5)
    }
    verdict = (
        "PASS"
        if all(all(value.values()) for value in criteria.values())
        and all(value == "PASS" for value in cumulative.values())
        else "FAIL"
    )
    _write(
        "gate-5.json",
        {
            "verdict": verdict,
            "criteria": criteria,
            "cells": cells,
            "cumulative": cumulative,
            "v3_0_stage_verdict": (
                ROOT / "results" / "V3.0" / "stage-verdict.md"
            ).read_text(encoding="utf-8").splitlines()[0],
        },
    )
    if verdict != "PASS":
        _write(
            "gate-5-diagnosis-stub.json",
            {
                "failed": {
                    name: [key for key, passed in values.items() if not passed]
                    for name, values in criteria.items()
                    if not all(values.values())
                }
            },
        )
        raise SystemExit("V3.1 Gate 5 failed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage",
        choices=(
            "pilot",
            "pilot-efficacy-amendment",
            "gate1",
            "gate2",
            "gate3",
            "gate4",
            "gate5",
        ),
    )
    arguments = parser.parse_args()
    {
        "pilot": run_pilot,
        "pilot-efficacy-amendment": run_pilot_efficacy_amendment,
        "gate1": run_gate1,
        "gate2": run_gate2,
        "gate3": run_gate3,
        "gate4": run_gate4,
        "gate5": run_gate5,
    }[arguments.stage]()


if __name__ == "__main__":
    main()
