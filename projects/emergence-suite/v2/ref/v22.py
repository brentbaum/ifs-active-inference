"""V2.2 identity root, association learning, and structural transfer."""

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
from .templates import categorical_prior, conditional_categorical, dirichlet_update
from .v20 import run_v20
from .v21 import BROADCAST, MONITOR, run_v21


PARAMETERS = load_parameters("V2.2")
PRECISION_PARAMETERS = load_parameters("V2.1")
ROOT_PRIOR = np.asarray(PARAMETERS["root_prior"], dtype=float)
ASSOCIATION_HIGH = float(PARAMETERS["association_high"])
ASSOCIATION_LOW = float(PARAMETERS["association_low"])
ADMISSION = np.asarray(PARAMETERS["phi_admission"], dtype=float)
OBS_RELIABILITY = float(PARAMETERS["meaning_likelihood_reliability"])
HISTORY_LENGTH = int(PARAMETERS["history_length"])
ASSOCIATION_PRIOR = np.asarray(PARAMETERS["association_prior"], dtype=float)


def _log_beta(a: float, b: float) -> float:
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def _integrated_binary_reliability(matches: int, mismatches: int) -> float:
    mismatch_prior, match_prior = ASSOCIATION_PRIOR
    return _log_beta(match_prior + matches, mismatch_prior + mismatches) - _log_beta(
        match_prior, mismatch_prior
    )


def generate_history(
    seed: int, structure: str, length: int = HISTORY_LENGTH
) -> tuple[np.ndarray, np.ndarray]:
    rng = component_rng(seed, f"v22-history-{structure}")
    if structure == "shared":
        g = (rng.random(length) >= ROOT_PRIOR[0]).astype(int)
        m = np.where(rng.random(length) < ASSOCIATION_HIGH, g, 1 - g)
    elif structure == "factorized":
        g = (rng.random(length) >= ROOT_PRIOR[0]).astype(int)
        m = rng.integers(0, 2, length)
    elif structure == "reversed":
        m = rng.integers(0, 2, length)
        g = np.where(rng.random(length) < ASSOCIATION_HIGH, m, 1 - m)
    else:
        raise ValueError(structure)
    return g, m


def structure_log_evidence(g: np.ndarray, m: np.ndarray) -> dict[str, float]:
    n = len(g)
    matches = int(np.sum(g == m))
    mismatches = n - matches
    log_g_prior = float(np.sum(np.log(ROOT_PRIOR[g])))
    integrated = _integrated_binary_reliability(matches, mismatches)
    return {
        "shared": log_g_prior + integrated,
        "factorized": log_g_prior + n * math.log(0.5),
        "reversed": n * math.log(0.5) + integrated,
    }


def structure_recovery() -> dict[str, object]:
    labels = ("shared", "factorized", "reversed")
    confusion = np.zeros((3, 3), dtype=int)
    true_probabilities: list[float] = []
    seed_start, seed_end = PARAMETERS["seed_block"]
    for offset, seed in enumerate(range(seed_start, seed_end + 1)):
        truth = labels[offset % 3]
        g, m = generate_history(seed, truth)
        log_e = structure_log_evidence(g, m)
        values = np.array([log_e[label] for label in labels])
        posterior = np.exp(values - np.max(values))
        posterior /= posterior.sum()
        estimate = int(np.argmax(posterior))
        confusion[labels.index(truth), estimate] += 1
        true_probabilities.append(float(posterior[labels.index(truth)]))
        state = ProtocolState(
            evidence_store={label: float(np.exp(values[index] - np.max(values))) for index, label in enumerate(labels)},
            metadata=MappingProxyType({"seed": seed, "truth": truth}),
        )
        audit_one_posterior(state)
    return {
        "accuracy": float(np.trace(confusion) / confusion.sum()),
        "mean_true_structure_probability": float(np.mean(true_probabilities)),
        "confusion_matrix": confusion.tolist(),
    }


def association_recovery() -> dict[str, object]:
    errors = []
    coverage = []
    seed_start, seed_end = PARAMETERS["seed_block"]
    for seed in range(seed_start, seed_end + 1):
        g, m = generate_history(seed, "shared")
        matches = int(np.sum(g == m))
        alpha = dirichlet_update(
            ASSOCIATION_PRIOR, np.array([len(g) - matches, matches])
        )
        mean = float(alpha[1] / alpha.sum())
        errors.append(abs(mean - ASSOCIATION_HIGH))
        rng = component_rng(seed, "v22-association-interval")
        samples = rng.beta(alpha[1], alpha[0], 5000)
        low, high = np.quantile(samples, [0.025, 0.975])
        coverage.append(float(low <= ASSOCIATION_HIGH <= high))
        state = ProtocolState(
            parameter_posterior_store={"cue_root_reliability": alpha},
            metadata=MappingProxyType({"seed": seed}),
        )
        audit_one_posterior(state)
    return {
        "mean_absolute_error": float(np.mean(errors)),
        "coverage_95": float(np.mean(coverage)),
        "error_95_interval": bootstrap_interval(errors, 703, "v22-association-error"),
    }


def seam_model(
    broadcast: bool,
    association: float = ASSOCIATION_HIGH,
    cut_root: bool = False,
    fixed_root: np.ndarray | None = None,
) -> FiniteModel:
    model = FiniteModel()
    for variable in [
        Variable("Phi", 3),
        Variable("L0", 3),
        Variable("Q0", 3, "observation"),
        Variable("G", 2),
        Variable("M0", 2),
        Variable("M1", 2),
        Variable("O0", 2, "observation"),
    ]:
        model.add_variable(variable)
    model.add_factor(categorical_prior("Phi", PRECISION_PARAMETERS["phi_prior"]))
    model.add_factor(categorical_prior("L0", [1 / 3] * 3))
    model.add_factor(Factor(("L0", "Q0"), MONITOR, "conditional_categorical"))
    if broadcast:
        model.add_factor(Factor(("Phi", "L0"), BROADCAST, "hierarchical_precision_prior"))
    model.add_factor(categorical_prior("G", fixed_root if fixed_root is not None else ROOT_PRIOR))
    if cut_root:
        model.add_factor(categorical_prior("M0", [0.5, 0.5]))
    else:
        table = np.empty((3, 2, 2))
        for phi, admission in enumerate(ADMISSION):
            effective = 0.5 + (association - 0.5) * (admission - 0.5) / 0.5
            effective = float(np.clip(effective, 0.5, association))
            table[phi] = [[effective, 1 - effective], [1 - effective, effective]]
        model.add_factor(Factor(("Phi", "G", "M0"), table, "conditional_categorical"))
    model.add_factor(
        conditional_categorical(
            "G",
            "M1",
            [[association, 1 - association], [1 - association, association]],
        )
    )
    model.add_factor(
        conditional_categorical(
            "M0",
            "O0",
            [[OBS_RELIABILITY, 1 - OBS_RELIABILITY], [1 - OBS_RELIABILITY, OBS_RELIABILITY]],
        )
    )
    return model


def seam_assay() -> dict[str, object]:
    engine = ExactEngine()
    definitions = {
        "broad": (True, 2),
        "broadcast_off": (False, 2),
        "narrowed": (True, 0),
    }
    output = {}
    for name, (broadcast, monitor) in definitions.items():
        model = seam_model(broadcast)
        base_m0, _ = engine.infer(model, ("M0",), {"Q0": monitor})
        base_g, _ = engine.infer(model, ("G",), {"Q0": monitor})
        base_m1, _ = engine.infer(model, ("M1",), {"Q0": monitor})
        base_phi, _ = engine.infer(model, ("Phi",), {"Q0": monitor})
        post_m0, _ = engine.infer(model, ("M0",), {"Q0": monitor, "O0": 1})
        post_g, _ = engine.infer(model, ("G",), {"Q0": monitor, "O0": 1})
        post_m1, _ = engine.infer(model, ("M1",), {"Q0": monitor, "O0": 1})
        post_phi, z = engine.infer(model, ("Phi",), {"Q0": monitor, "O0": 1})
        state = ProtocolState(
            posterior_store={"Phi": post_phi, "G": post_g, "M0": post_m0, "M1": post_m1},
            evidence_store={"model": z},
            metadata=MappingProxyType({"regime": name}),
        )
        audit_one_posterior(state)
        output[name] = {
            "local_fluency": float(post_m0[1]),
            "cue_uptake": float(post_m0[1] - base_m0[1]),
            "depth": float(post_phi[2]),
            "root_uptake": float(post_g[1] - base_g[1]),
            "transfer": float(post_m1[1] - base_m1[1]),
            "base_root": base_g.tolist(),
            "base_phi": base_phi.tolist(),
        }
    broad_base = np.asarray(output["broad"]["base_root"])
    mediated_cut = seam_model(True, cut_root=True, fixed_root=broad_base)
    cut_before, _ = engine.infer(mediated_cut, ("M1",), {"Q0": 2})
    cut_after, _ = engine.infer(mediated_cut, ("M1",), {"Q0": 2, "O0": 1})
    output["mediation"] = {
        "transfer_with_g_fixed_and_cue_root_cut": float(cut_after[1] - cut_before[1]),
        "broad_indirect_effect": output["broad"]["transfer"],
    }
    return output


def transfer_2x2() -> dict[str, object]:
    engine = ExactEngine()
    cells = {}
    for association_index, (association_name, association) in enumerate([
            ("low_association", ASSOCIATION_LOW),
            ("high_association", ASSOCIATION_HIGH),
        ]):
        # Association histories are paired across similarity arms; recognition
        # histories vary independently on a component-specific stream.
        association_rng = component_rng(3300 + association_index, "v22-2x2-association")
        g = (association_rng.random(HISTORY_LENGTH) >= ROOT_PRIOR[0]).astype(int)
        m = np.where(
            association_rng.random(HISTORY_LENGTH) < association, g, 1 - g
        )
        matches = int(np.sum(g == m))
        association_alpha = dirichlet_update(
            ASSOCIATION_PRIOR,
            np.array([HISTORY_LENGTH - matches, matches], dtype=float),
        )
        learned_association = float(association_alpha[1] / association_alpha.sum())
        for similarity_index, (similarity_name, similarity) in enumerate([
            ("low_similarity", 0.62),
            ("high_similarity", 0.94),
        ]):
            recognition_rng = component_rng(
                3400 + 10 * association_index + similarity_index,
                "v22-2x2-recognition",
            )
            recognition_correct = int(
                np.sum(recognition_rng.random(HISTORY_LENGTH) < similarity)
            )
            similarity_alpha = dirichlet_update(
                np.array([1.0, 1.0]),
                np.array(
                    [HISTORY_LENGTH - recognition_correct, recognition_correct],
                    dtype=float,
                ),
            )
            learned_similarity = float(similarity_alpha[1] / similarity_alpha.sum())
            model = seam_model(True, association=learned_association)
            before, _ = engine.infer(model, ("M1",), {"Q0": 2})
            after, _ = engine.infer(model, ("M1",), {"Q0": 2, "O0": 1})
            cells[f"{similarity_name}__{association_name}"] = {
                "transfer": float(after[1] - before[1]),
                "learned_cue_recognition": learned_similarity,
                "learned_root_association": learned_association,
            }
    low_assoc = np.mean(
        [value["transfer"] for key, value in cells.items() if "low_association" in key]
    )
    high_assoc = np.mean(
        [value["transfer"] for key, value in cells.items() if "high_association" in key]
    )
    low_similarity = np.mean(
        [value["transfer"] for key, value in cells.items() if "low_similarity" in key]
    )
    high_similarity = np.mean(
        [value["transfer"] for key, value in cells.items() if "high_similarity" in key]
    )
    return {
        "cells": cells,
        "association_main_effect": float(high_assoc - low_assoc),
        "similarity_main_effect": float(high_similarity - low_similarity),
    }


def lesion_assays() -> dict[str, float]:
    engine = ExactEngine()
    full = seam_model(True, ASSOCIATION_HIGH)
    cut = seam_model(True, 0.5)
    full_before, _ = engine.infer(full, ("M1",), {"Q0": 2})
    full_after, _ = engine.infer(full, ("M1",), {"Q0": 2, "O0": 1})
    cut_before, _ = engine.infer(cut, ("M1",), {"Q0": 2})
    cut_after, _ = engine.infer(cut, ("M1",), {"Q0": 2, "O0": 1})
    cut_m0_before, _ = engine.infer(cut, ("M0",), {"Q0": 2})
    cut_m0_after, _ = engine.infer(cut, ("M0",), {"Q0": 2, "O0": 1})
    return {
        "full_transfer": float(full_after[1] - full_before[1]),
        "cut_transfer": float(cut_after[1] - cut_before[1]),
        "cut_treated_cue_uptake": float(cut_m0_after[1] - cut_m0_before[1]),
    }


def batch_transfer() -> dict[str, object]:
    engine = ExactEngine()
    effects = []
    maximum_oracle_error = 0.0
    from .oracle import brute_force

    seed_start, seed_end = PARAMETERS["seed_block"]
    for seed in range(seed_start, seed_end + 1):
        g, m = generate_history(seed, "shared")
        matches = int(np.sum(g == m))
        association = float((matches + 1) / (len(g) + 2))
        model = seam_model(True, association)
        before, _ = engine.infer(model, ("M1",), {"Q0": 2})
        after, z = engine.infer(model, ("M1",), {"Q0": 2, "O0": 1})
        oracle, oracle_z = brute_force(model, ("M1",), {"Q0": 2, "O0": 1})
        maximum_oracle_error = max(
            maximum_oracle_error,
            float(np.max(np.abs(after - oracle))),
            abs(z - oracle_z),
        )
        effects.append(float(after[1] - before[1]))
    return {
        "seed_count": len(effects),
        "mean_transfer": float(np.mean(effects)),
        "transfer_95_interval": bootstrap_interval(effects, 704, "v22-transfer"),
        "maximum_oracle_error": maximum_oracle_error,
    }


def run_v22() -> dict[str, object]:
    structures = structure_recovery()
    associations = association_recovery()
    seam = seam_assay()
    factorial = transfer_2x2()
    lesions = lesion_assays()
    batch = batch_transfer()
    v20 = run_v20()
    v21 = run_v21()
    gates = {
        "gate_1_structure_recovery": structures["accuracy"] >= 0.80
        and structures["mean_true_structure_probability"] >= 0.70,
        "gate_2_parameter_recovery": associations["mean_absolute_error"] <= 0.10
        and associations["coverage_95"] >= 0.85,
        "gate_3_precision_root_transfer": (
            min(seam[name]["cue_uptake"] for name in ("broad", "broadcast_off", "narrowed"))
            >= 0.20
            and seam["broad"]["root_uptake"] - seam["broadcast_off"]["root_uptake"] >= 0.08
            and seam["broadcast_off"]["root_uptake"] - seam["narrowed"]["root_uptake"] >= 0.03
            and seam["broad"]["transfer"] - seam["narrowed"]["transfer"] >= 0.08
            and abs(seam["mediation"]["transfer_with_g_fixed_and_cue_root_cut"]) < 1e-10
            and factorial["association_main_effect"] > 0.10
            and abs(factorial["similarity_main_effect"]) < 0.03
        ),
        "gate_4_selective_lesions": lesions["cut_transfer"] < 0.01
        and lesions["cut_treated_cue_uptake"] >= 0.20
        and seam["broadcast_off"]["local_fluency"] >= 0.80
        and seam["broadcast_off"]["depth"] < seam["broad"]["depth"]
        and seam["broadcast_off"]["root_uptake"] < seam["broad"]["root_uptake"]
        and seam["broadcast_off"]["transfer"] < seam["broad"]["transfer"]
        and batch["seed_count"] == 64
        and batch["maximum_oracle_error"] < 1e-10,
        "gate_5_cumulative_regression": v20["passed"] and v21["passed"],
    }
    return {
        "stage": "V2.2",
        "structure_recovery": structures,
        "association_recovery": associations,
        "seam": seam,
        "transfer_2x2": factorial,
        "lesions": lesions,
        "batch": batch,
        "v2.0_regression": v20["gates"],
        "v2.1_regression": v21["gates"],
        "gates": gates,
        "passed": all(gates.values()),
    }
