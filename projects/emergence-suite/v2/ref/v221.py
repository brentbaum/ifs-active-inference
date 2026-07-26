"""V2.2.1 exact zero-association structure repair."""

from __future__ import annotations

import math
from types import MappingProxyType

import numpy as np

from .audit import ProtocolState, audit_one_posterior
from .config import load_parameters
from .factor import Factor
from .inference import ExactEngine
from .model import FiniteModel, Variable
from .rng import component_rng
from .statistics import bootstrap_interval
from .templates import categorical_prior, conditional_categorical
from .v20 import run_v20
from .v21 import BROADCAST, MONITOR, run_v21
from .v22 import (
    ADMISSION,
    association_recovery as v22_association_recovery,
    generate_history,
    lesion_assays,
    seam_assay,
    seam_model,
    structure_log_evidence,
)


PARAMETERS = load_parameters("V2.2.1")
EXISTENCE_PRIOR = np.asarray(PARAMETERS["association_existence_prior"], dtype=float)
SLAB_PRIOR = np.asarray(PARAMETERS["association_slab_prior"], dtype=float)
ZERO_RELIABILITY = float(PARAMETERS["zero_association_reliability"])
ASSOCIATION_HIGH = float(PARAMETERS["association_high"])
ASSOCIATION_LOW = float(PARAMETERS["association_low"])
OBS_RELIABILITY = float(PARAMETERS["meaning_likelihood_reliability"])
HISTORY_LENGTH = int(PARAMETERS["history_length"])
REPAIR_HISTORY_LENGTH = int(PARAMETERS["repair_history_length"])
FLOOR_BAND = float(PARAMETERS["floor_band"])


def _log_beta(a: float, b: float) -> float:
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def _log_sequence_evidence(
    matches: int, mismatches: int, structure: int
) -> float:
    if structure == 0:
        return (matches + mismatches) * math.log(ZERO_RELIABILITY)
    mismatch_prior, match_prior = SLAB_PRIOR
    return _log_beta(
        match_prior + matches, mismatch_prior + mismatches
    ) - _log_beta(match_prior, mismatch_prior)


def learn_association(matches: int, mismatches: int) -> ProtocolState:
    """Finite comparison of exact factorization against an associated slab."""
    if matches < 0 or mismatches < 0 or matches + mismatches == 0:
        raise ValueError("association history counts must be nonnegative and nonempty")
    log_joint = np.array(
        [
            math.log(EXISTENCE_PRIOR[structure])
            + _log_sequence_evidence(matches, mismatches, structure)
            for structure in range(2)
        ]
    )
    shifted = np.exp(log_joint - np.max(log_joint))
    model_posterior = shifted / shifted.sum()
    slab_posterior = SLAB_PRIOR + np.array([mismatches, matches], dtype=float)
    state = ProtocolState(
        posterior_store={"Z_association": model_posterior},
        parameter_posterior_store={"theta_slab": slab_posterior},
        evidence_store={
            "zero_joint_evidence": float(np.exp(log_joint[0])),
            "slab_joint_evidence": float(np.exp(log_joint[1])),
        },
        metadata=MappingProxyType(
            {"stage": "V2.2.1", "matches": matches, "mismatches": mismatches}
        ),
    )
    audit_one_posterior(state)
    return state


def model_averaged_association(state: ProtocolState) -> float:
    """Pure posterior-model-averaged CPT readout; no cutoff or clamp."""
    model_posterior = state.posterior_store["Z_association"]
    slab_alpha = state.parameter_posterior_store["theta_slab"]
    slab_mean = float(slab_alpha[1] / slab_alpha.sum())
    return float(
        model_posterior[0] * ZERO_RELIABILITY
        + model_posterior[1] * slab_mean
    )


def _finite_structure_model(
    matches: int, mismatches: int
) -> tuple[FiniteModel, dict[str, int]]:
    trials = matches + mismatches
    model = FiniteModel()
    model.add_variable(Variable("Z", 2, "structure"))
    model.add_variable(Variable("K", trials + 1, "observation"))
    model.add_factor(Factor(("Z",), EXISTENCE_PRIOR, "categorical_prior"))
    null_row = np.array(
        [math.comb(trials, k) * ZERO_RELIABILITY**trials for k in range(trials + 1)]
    )
    mismatch_prior, match_prior = SLAB_PRIOR
    slab_row = np.array(
        [
            math.comb(trials, k)
            * math.exp(
                _log_beta(match_prior + k, mismatch_prior + trials - k)
                - _log_beta(match_prior, mismatch_prior)
            )
            for k in range(trials + 1)
        ]
    )
    model.add_factor(
        Factor(("Z", "K"), np.stack([null_row, slab_row]), "finite_model_evidence")
    )
    return model, {"K": matches}


def semantic_proof() -> dict[str, object]:
    cases = {"zero": (90, 90), "associated": (162, 18)}
    errors = {}
    posteriors = {}
    for name, (matches, mismatches) in cases.items():
        analytic = learn_association(matches, mismatches)
        model, observations = _finite_structure_model(matches, mismatches)
        exact, _ = ExactEngine().infer(model, ("Z",), observations)
        errors[name] = float(
            np.max(
                np.abs(exact - analytic.posterior_store["Z_association"])
            )
        )
        posteriors[name] = analytic.posterior_store["Z_association"].tolist()
    return {
        "analytic_exact_errors": errors,
        "maximum_error": max(errors.values()),
        "posteriors_zero_associated": posteriors,
    }


def structure_recovery() -> dict[str, object]:
    labels = ("shared", "factorized", "reversed")
    seed_start, seed_end = PARAMETERS["seed_block"]
    confusion = np.zeros((3, 3), dtype=int)
    true_probabilities = []
    for offset, seed in enumerate(range(seed_start, seed_end + 1)):
        truth = labels[offset % 3]
        g, m = generate_history(seed, truth, HISTORY_LENGTH)
        log_evidence = structure_log_evidence(g, m)
        values = np.array([log_evidence[label] for label in labels])
        posterior = np.exp(values - values.max())
        posterior /= posterior.sum()
        confusion[labels.index(truth), int(np.argmax(posterior))] += 1
        true_probabilities.append(float(posterior[labels.index(truth)]))
    return {
        "accuracy": float(np.trace(confusion) / confusion.sum()),
        "mean_true_structure_probability": float(np.mean(true_probabilities)),
        "confusion_matrix": confusion.tolist(),
    }


def association_recovery() -> dict[str, object]:
    seed_start, seed_end = PARAMETERS["seed_block"]
    existence_correct = []
    true_probabilities = []
    slab_errors = []
    slab_coverages = []
    for seed in range(seed_start, seed_end + 1):
        for truth_name, reliability, truth_structure in (
            ("zero", ZERO_RELIABILITY, 0),
            ("associated", ASSOCIATION_HIGH, 1),
        ):
            rng = component_rng(seed, f"v221-recovery-{truth_name}")
            matches = int(rng.binomial(HISTORY_LENGTH, reliability))
            state = learn_association(matches, HISTORY_LENGTH - matches)
            posterior = state.posterior_store["Z_association"]
            existence_correct.append(float(np.argmax(posterior) == truth_structure))
            true_probabilities.append(float(posterior[truth_structure]))
            if truth_structure == 1:
                slab = state.parameter_posterior_store["theta_slab"]
                mean = float(slab[1] / slab.sum())
                slab_errors.append(abs(mean - ASSOCIATION_HIGH))
                interval_rng = component_rng(seed, "v221-slab-interval")
                samples = interval_rng.beta(slab[1], slab[0], 5000)
                lower, upper = np.quantile(samples, [0.025, 0.975])
                slab_coverages.append(
                    float(lower <= ASSOCIATION_HIGH <= upper)
                )
    return {
        "existence_accuracy": float(np.mean(existence_correct)),
        "mean_true_existence_probability": float(np.mean(true_probabilities)),
        "slab_parameter_mean_absolute_error": float(np.mean(slab_errors)),
        "slab_parameter_95_interval_coverage": float(np.mean(slab_coverages)),
        "legacy_associated_recovery": v22_association_recovery(),
    }


def _correction_segment(
    root_prior: np.ndarray, association: float, q_observation: int
) -> dict[str, np.ndarray]:
    model = FiniteModel()
    for variable in [
        Variable("Phi", 3),
        Variable("L", 3),
        Variable("G", 2),
        Variable("M", 2),
    ]:
        model.add_variable(variable)
    model.add_factor(categorical_prior("Phi", [1 / 3] * 3))
    model.add_factor(categorical_prior("L", [1 / 3] * 3))
    model.add_factor(
        Factor(("L",), MONITOR[:, q_observation], "conditional_categorical")
    )
    model.add_factor(
        Factor(("Phi", "L"), BROADCAST, "hierarchical_precision_prior")
    )
    model.add_factor(categorical_prior("G", root_prior))
    table = np.empty((3, 2, 2))
    for phi in range(3):
        effective = (
            0.5
            + (association - 0.5)
            * (ADMISSION[phi] - 0.5)
            / 0.5
        )
        table[phi] = [
            [effective, 1.0 - effective],
            [1.0 - effective, effective],
        ]
    model.add_factor(
        Factor(("Phi", "G", "M"), table, "conditional_categorical")
    )
    model.add_factor(
        Factor(
            ("M",),
            np.array([1.0 - OBS_RELIABILITY, OBS_RELIABILITY]),
            "conditional_categorical",
        )
    )
    joint, _ = ExactEngine().infer(model, ("Phi", "G", "M"), {})
    return {
        "Phi": joint.sum(axis=(1, 2)),
        "G": joint.sum(axis=(0, 2)),
        "M": joint.sum(axis=(0, 1)),
    }


def _probe(root: np.ndarray, association: float) -> np.ndarray:
    model = FiniteModel()
    model.add_variable(Variable("G", 2))
    model.add_variable(Variable("M", 2))
    model.add_factor(categorical_prior("G", root))
    model.add_factor(
        conditional_categorical(
            "G",
            "M",
            [
                [association, 1.0 - association],
                [1.0 - association, association],
            ],
        )
    )
    posterior, _ = ExactEngine().infer(model, ("M",), {})
    return posterior


def _treatment_transfer(treated_association: float) -> float:
    root_start = np.array([0.5, 0.5])
    root = root_start.copy()
    for q_observation in (2, 0, 2):
        root = _correction_segment(root, treated_association, q_observation)["G"]
    before = _probe(root_start, ASSOCIATION_HIGH)
    after = _probe(root, ASSOCIATION_HIGH)
    return float(after[1] - before[1])


def repair_floor_assay() -> dict[str, object]:
    seed_start, seed_end = PARAMETERS["repair_seed_block"]
    zero_transfers = []
    associated_transfers = []
    null_probabilities = []
    associated_probabilities = []
    for seed in range(seed_start, seed_end + 1):
        zero_rng = component_rng(seed, "v221-floor-zero")
        zero_matches = int(
            zero_rng.binomial(REPAIR_HISTORY_LENGTH, ZERO_RELIABILITY)
        )
        zero_state = learn_association(
            zero_matches, REPAIR_HISTORY_LENGTH - zero_matches
        )
        zero_association = model_averaged_association(zero_state)
        zero_transfers.append(abs(_treatment_transfer(zero_association)))
        null_probabilities.append(
            float(zero_state.posterior_store["Z_association"][0])
        )

        associated_rng = component_rng(seed, "v221-floor-associated")
        associated_matches = int(
            associated_rng.binomial(
                REPAIR_HISTORY_LENGTH, ASSOCIATION_HIGH
            )
        )
        associated_state = learn_association(
            associated_matches,
            REPAIR_HISTORY_LENGTH - associated_matches,
        )
        associated_association = model_averaged_association(associated_state)
        associated_transfers.append(
            abs(_treatment_transfer(associated_association))
        )
        associated_probabilities.append(
            float(associated_state.posterior_store["Z_association"][1])
        )
    floor_clean = [value <= FLOOR_BAND for value in zero_transfers]
    return {
        "world_count": len(zero_transfers),
        "zero_floor_clean_rate": float(np.mean(floor_clean)),
        "zero_transfer_mean": float(np.mean(zero_transfers)),
        "zero_transfer_95_interval": bootstrap_interval(
            zero_transfers, 705, "v221-zero-transfer"
        ),
        "zero_component_probability_mean": float(
            np.mean(null_probabilities)
        ),
        "associated_transfer_mean": float(np.mean(associated_transfers)),
        "associated_transfer_95_interval": bootstrap_interval(
            associated_transfers, 706, "v221-associated-transfer"
        ),
        "associated_component_probability_mean": float(
            np.mean(associated_probabilities)
        ),
    }


def repaired_transfer_2x2() -> dict[str, object]:
    seed_start, _ = PARAMETERS["seed_block"]
    cells = {}
    for association_name, reliability, offset in (
        ("low_association", ASSOCIATION_LOW, 0),
        ("high_association", ASSOCIATION_HIGH, 1),
    ):
        rng = component_rng(seed_start + offset, "v221-2x2-association")
        matches = int(rng.binomial(HISTORY_LENGTH, reliability))
        state = learn_association(matches, HISTORY_LENGTH - matches)
        learned = model_averaged_association(state)
        model = seam_model(True, association=learned)
        before, _ = ExactEngine().infer(model, ("M1",), {"Q0": 2})
        after, _ = ExactEngine().infer(
            model, ("M1",), {"Q0": 2, "O0": 1}
        )
        transfer = float(after[1] - before[1])
        for similarity_name, similarity in (
            ("low_similarity", 0.62),
            ("high_similarity", 0.94),
        ):
            cells[f"{similarity_name}__{association_name}"] = {
                "transfer": transfer,
                "cue_recognition_probability": similarity,
                "learned_association": learned,
                "association_existence_posterior": state.posterior_store[
                    "Z_association"
                ].tolist(),
            }
    low = np.mean(
        [
            value["transfer"]
            for key, value in cells.items()
            if "low_association" in key
        ]
    )
    high = np.mean(
        [
            value["transfer"]
            for key, value in cells.items()
            if "high_association" in key
        ]
    )
    low_similarity = np.mean(
        [
            value["transfer"]
            for key, value in cells.items()
            if "low_similarity" in key
        ]
    )
    high_similarity = np.mean(
        [
            value["transfer"]
            for key, value in cells.items()
            if "high_similarity" in key
        ]
    )
    return {
        "cells": cells,
        "association_main_effect": float(high - low),
        "similarity_main_effect": float(high_similarity - low_similarity),
    }


def repaired_batch_transfer() -> dict[str, object]:
    seed_start, seed_end = PARAMETERS["seed_block"]
    effects = []
    for seed in range(seed_start, seed_end + 1):
        rng = component_rng(seed, "v221-batch-associated")
        matches = int(rng.binomial(HISTORY_LENGTH, ASSOCIATION_HIGH))
        state = learn_association(matches, HISTORY_LENGTH - matches)
        association = model_averaged_association(state)
        model = seam_model(True, association)
        before, _ = ExactEngine().infer(model, ("M1",), {"Q0": 2})
        after, _ = ExactEngine().infer(
            model, ("M1",), {"Q0": 2, "O0": 1}
        )
        effects.append(float(after[1] - before[1]))
    return {
        "seed_count": len(effects),
        "mean_transfer": float(np.mean(effects)),
        "transfer_95_interval": bootstrap_interval(
            effects, 707, "v221-batch-transfer"
        ),
    }


def run_v221() -> dict[str, object]:
    semantic = semantic_proof()
    structures = structure_recovery()
    associations = association_recovery()
    seam = seam_assay()
    factorial = repaired_transfer_2x2()
    floor = repair_floor_assay()
    lesions = lesion_assays()
    batch = repaired_batch_transfer()
    v20 = run_v20()
    v21 = run_v21()

    zero_posterior = semantic["posteriors_zero_associated"]["zero"][0]
    associated_posterior = semantic["posteriors_zero_associated"]["associated"][1]
    gates = {
        "gate_1_structure_semantics": (
            semantic["maximum_error"] < 1e-10
            and zero_posterior >= 0.90
            and associated_posterior >= 0.90
            and structures["accuracy"] >= 0.80
            and structures["mean_true_structure_probability"] >= 0.70
        ),
        "gate_2_recovery": (
            associations["existence_accuracy"] >= 0.90
            and associations["slab_parameter_mean_absolute_error"] <= 0.10
            and associations["slab_parameter_95_interval_coverage"] >= 0.85
        ),
        "gate_3_precision_root_transfer": (
            min(
                seam[name]["cue_uptake"]
                for name in ("broad", "broadcast_off", "narrowed")
            )
            >= 0.20
            and seam["broad"]["root_uptake"]
            - seam["broadcast_off"]["root_uptake"]
            >= 0.08
            and seam["broadcast_off"]["root_uptake"]
            - seam["narrowed"]["root_uptake"]
            >= 0.03
            and seam["broad"]["transfer"] - seam["narrowed"]["transfer"]
            >= 0.08
            and factorial["association_main_effect"] > 0.10
            and abs(factorial["similarity_main_effect"]) < 0.03
            and floor["zero_floor_clean_rate"] >= 0.95
            and floor["associated_transfer_mean"] >= 0.15
        ),
        "gate_4_selective_lesions": (
            lesions["cut_transfer"] < 0.01
            and lesions["cut_treated_cue_uptake"] >= 0.20
            and abs(
                seam["mediation"][
                    "transfer_with_g_fixed_and_cue_root_cut"
                ]
            )
            < 1e-10
            and seam["broadcast_off"]["local_fluency"] >= 0.80
            and floor["zero_transfer_mean"] < 0.01
        ),
        "gate_5_cumulative_regression": (
            v20["passed"]
            and v21["passed"]
            and batch["seed_count"] == 64
            and batch["mean_transfer"] >= 0.15
        ),
    }
    return {
        "stage": "V2.2.1",
        "semantic_proof": semantic,
        "structure_recovery": structures,
        "association_recovery": associations,
        "seam": seam,
        "transfer_2x2": factorial,
        "repair_floor_assay": floor,
        "lesions": lesions,
        "batch": batch,
        "v2.0_regression": v20["gates"],
        "v2.1_regression": v21["gates"],
        "gates": gates,
        "passed": all(gates.values()),
    }

