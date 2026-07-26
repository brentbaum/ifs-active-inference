"""V2.1 recursive precision protocols compiled to generic factors."""

from __future__ import annotations

from types import MappingProxyType

import numpy as np

from .audit import ProtocolState, audit_one_posterior
from .config import load_parameters
from .factor import Factor
from .inference import ExactEngine
from .model import FiniteModel, Variable
from .oracle import brute_force
from .precision import gaussian_log_likelihood, observation_likelihood, precision_categorical
from .readouts import depth, dominance
from .rng import component_rng
from .statistics import bootstrap_interval
from .templates import (
    categorical_prior,
    conditional_categorical,
    dirichlet_update,
)
from .v20 import run_v20


PARAMETERS = load_parameters("V2.1")
SUPPORT = np.asarray(PARAMETERS["precision_support"], dtype=float)
BASE = np.asarray(PARAMETERS["base_likelihood"], dtype=float)
BROADCAST = np.asarray(PARAMETERS["broadcast_cpt"], dtype=float)
_MONITOR_RELIABILITY = float(PARAMETERS["monitor_reliability"])
_MONITOR_OFF = (1.0 - _MONITOR_RELIABILITY) / 2.0
MONITOR = np.array(
    [
        [_MONITOR_RELIABILITY, _MONITOR_OFF, _MONITOR_OFF],
        [_MONITOR_OFF, _MONITOR_RELIABILITY, _MONITOR_OFF],
        [_MONITOR_OFF, _MONITOR_OFF, _MONITOR_RELIABILITY],
    ]
)


def precision_model(broadcast: bool = True) -> FiniteModel:
    model = FiniteModel()
    for variable in [
        Variable("Phi", 3),
        Variable("L0", 3),
        Variable("L1", 3),
        Variable("Q0", 3, "observation"),
        Variable("Y", 2),
        Variable("OY", 2, "observation"),
    ]:
        model.add_variable(variable)
    model.add_factor(categorical_prior("Phi", PARAMETERS["phi_prior"]))
    model.add_factor(categorical_prior("L0", [1 / 3] * 3))
    model.add_factor(Factor(("L0", "Q0"), MONITOR, "conditional_categorical"))
    if broadcast:
        model.add_factor(Factor(("Phi", "L0"), BROADCAST, "hierarchical_precision_prior"))
    model.add_factor(Factor(("Phi", "L1"), BROADCAST, "hierarchical_precision_return"))
    model.add_factor(categorical_prior("Y", [0.5, 0.5]))
    model.add_factor(precision_categorical("Y", "L1", "OY", BASE, SUPPORT))
    return model


def semantic_precision_proof() -> dict[str, object]:
    low = BASE**SUPPORT[0]
    low /= low.sum(axis=1, keepdims=True)
    high = BASE**SUPPORT[-1]
    high /= high.sum(axis=1, keepdims=True)
    factor = precision_categorical("X", "L", "O", BASE, SUPPORT)
    gaussian_factor = observation_likelihood(
        "bounded_gaussian",
        latent="X",
        precision="L",
        observation="O",
        means=[-0.5, 0.5],
        precision_support=SUPPORT,
        observation_support=np.linspace(-1.0, 1.0, 9),
    )
    numeric_low = factor.values[0, 0, 0]
    numeric_high = factor.values[0, -1, 0]
    gaussian_variances = np.exp(-SUPPORT)
    gaussian_logs = [gaussian_log_likelihood(0.2, 0.0, value) for value in SUPPORT]
    return {
        "analytic_low_correct": float(low[0, 0]),
        "analytic_high_correct": float(high[0, 0]),
        "numeric_low_correct": float(numeric_low),
        "numeric_high_correct": float(numeric_high),
        "sharpening_effect": float(numeric_high - numeric_low),
        "analytic_numeric_max_error": float(
            max(abs(numeric_low - low[0, 0]), abs(numeric_high - high[0, 0]))
        ),
        "gaussian_variances": gaussian_variances.tolist(),
        "gaussian_log_likelihoods_at_point": gaussian_logs,
        "bounded_gaussian_factor_shape": list(gaussian_factor.values.shape),
        "bounded_gaussian_rows_normalized": bool(
            np.allclose(gaussian_factor.values.sum(axis=2), 1.0)
        ),
        "gaussian_variance_monotone": bool(np.all(np.diff(gaussian_variances) < 0)),
    }


def broadcast_assay() -> dict[str, object]:
    engine = ExactEngine()
    on = precision_model(True)
    off = precision_model(False)
    posterior_on, z_on = engine.infer(on, ("Phi",), {"Q0": 2, "OY": 1})
    posterior_off, z_off = engine.infer(off, ("Phi",), {"Q0": 2, "OY": 1})
    posterior_off_low, _ = engine.infer(off, ("Phi",), {"Q0": 0, "OY": 1})
    local_on, _ = engine.infer(on, ("L0",), {"Q0": 2})
    local_off, _ = engine.infer(off, ("L0",), {"Q0": 2})
    oracle, oracle_z = brute_force(on, ("Phi",), {"Q0": 2, "OY": 1})
    state_on = ProtocolState(
        posterior_store={"Phi": posterior_on},
        evidence_store={"model": z_on},
        metadata=MappingProxyType({"broadcast": True}),
    )
    state_off = ProtocolState(
        posterior_store={"Phi": posterior_off},
        evidence_store={"model": z_off},
        metadata=MappingProxyType({"broadcast": False}),
    )
    audit_one_posterior(state_on)
    audit_one_posterior(state_off)
    return {
        "depth_on": depth(state_on),
        "depth_off": depth(state_off),
        "depth_effect": depth(state_on) - depth(state_off),
        "off_monitor_depth_effect": float(posterior_off[2] - posterior_off_low[2]),
        "local_on": local_on.tolist(),
        "local_off": local_off.tolist(),
        "local_max_difference": float(np.max(np.abs(local_on - local_off))),
        "engine_oracle_error": float(max(np.max(np.abs(posterior_on - oracle)), abs(z_on - oracle_z))),
    }


def cross_latent_composition() -> dict[str, float]:
    engine = ExactEngine()
    model = precision_model(True)
    broad, _ = engine.infer(model, ("Y",), {"Q0": 2, "OY": 1})
    narrow, _ = engine.infer(model, ("Y",), {"Q0": 0, "OY": 1})
    log_odds_broad = float(np.log(broad[1] / broad[0]))
    log_odds_narrow = float(np.log(narrow[1] / narrow[0]))
    return {
        "posterior_y_broad": float(broad[1]),
        "posterior_y_narrow": float(narrow[1]),
        "delivered_log_odds_effect": abs(log_odds_broad - log_odds_narrow),
    }


def open_assays() -> dict[str, object]:
    engine = ExactEngine()
    model = precision_model(True)
    regimes = {}
    for label, monitor, observation in [
        ("r0", 2, 1),
        ("r1", 2, 0),
        ("r2", 0, 1),
        ("r3", 0, 0),
    ]:
        phi, _ = engine.infer(model, ("Phi",), {"Q0": monitor, "OY": observation})
        y, _ = engine.infer(model, ("Y",), {"Q0": monitor, "OY": observation})
        y_without_monitor, _ = engine.infer(model, ("Y",), {"OY": observation})
        state = ProtocolState(
            posterior_store={"Phi": phi, "Y": y},
            metadata=MappingProxyType({"assay": label}),
        )
        audit_one_posterior(state)
        regimes[label] = {
            "depth": depth(state),
            "dominance": dominance(y, y_without_monitor),
            "target_posterior": float(y[1]),
        }
    reliable_l, _ = engine.infer(model, ("L0",), {"Q0": 2})
    unreliable_l, _ = engine.infer(model, ("L0",), {"Q0": 0})
    conflict_calibrated, _ = engine.infer(model, ("Y",), {"Q0": 1, "OY": 1})
    conflict_confident, _ = engine.infer(model, ("Y",), {"Q0": 2, "OY": 0})
    comparator = precision_model(False)
    independent_y, _ = engine.infer(comparator, ("Y",), {"Q0": 2, "OY": 1})
    return {
        "reliable_local_high_probability": float(reliable_l[2]),
        "unreliable_local_low_probability": float(unreliable_l[0]),
        "conflict_less_confident_calibrated_target": float(conflict_calibrated[1]),
        "conflict_confident_miscalibrated_target": float(conflict_confident[1]),
        "four_unlabeled_regimes": regimes,
        "independent_local_comparator_target": float(independent_y[1]),
    }


def precision_recovery() -> dict[str, float]:
    engine = ExactEngine()
    model = precision_model(False)
    confusion = np.zeros((3, 3), dtype=int)
    for true_state in range(3):
        for observed in range(3):
            count = int(round(MONITOR[true_state, observed] * 100))
            posterior, _ = engine.infer(model, ("L0",), {"Q0": observed})
            confusion[true_state, int(np.argmax(posterior))] += count
    parameter_errors = []
    parameter_coverages = []
    seed_start, seed_end = PARAMETERS["seed_block"]
    for seed in range(seed_start, seed_end + 1):
        rng = component_rng(seed, "v21-monitor-parameter")
        correct = int(np.sum(rng.random(180) < _MONITOR_RELIABILITY))
        alpha = dirichlet_update(
            np.array([1.0, 1.0]), np.array([180 - correct, correct], dtype=float)
        )
        mean = float(alpha[1] / alpha.sum())
        parameter_errors.append(abs(mean - _MONITOR_RELIABILITY))
        interval_rng = component_rng(seed, "v21-monitor-interval")
        samples = interval_rng.beta(alpha[1], alpha[0], 5000)
        low, high = np.quantile(samples, [0.025, 0.975])
        parameter_coverages.append(float(low <= _MONITOR_RELIABILITY <= high))
        state = ProtocolState(
            parameter_posterior_store={"monitor_reliability": alpha},
            metadata=MappingProxyType({"seed": seed}),
        )
        audit_one_posterior(state)
    return {
        "accuracy": float(np.trace(confusion) / confusion.sum()),
        "confusion_matrix": confusion.tolist(),
        "parameter_mean_absolute_error": float(np.mean(parameter_errors)),
        "parameter_95_interval_coverage": float(np.mean(parameter_coverages)),
    }


def batch_evaluation() -> dict[str, object]:
    engine = ExactEngine()
    on = precision_model(True)
    off = precision_model(False)
    effects = []
    paired_mismatches = 0
    maximum_oracle_error = 0.0
    seed_start, seed_end = PARAMETERS["seed_block"]
    for seed in range(seed_start, seed_end + 1):
        rng_on = component_rng(seed, "v21-world")
        rng_off = component_rng(seed, "v21-world")
        q_on = int(rng_on.choice(3, p=MONITOR[2]))
        q_off = int(rng_off.choice(3, p=MONITOR[2]))
        oy_on = int(rng_on.random() < 0.8)
        oy_off = int(rng_off.random() < 0.8)
        paired_mismatches += int((q_on, oy_on) != (q_off, oy_off))
        posterior_on, z_on = engine.infer(on, ("Phi",), {"Q0": q_on, "OY": oy_on})
        posterior_off, _ = engine.infer(off, ("Phi",), {"Q0": q_off, "OY": oy_off})
        oracle, oracle_z = brute_force(on, ("Phi",), {"Q0": q_on, "OY": oy_on})
        maximum_oracle_error = max(
            maximum_oracle_error,
            float(np.max(np.abs(posterior_on - oracle))),
            abs(z_on - oracle_z),
        )
        effects.append(float(posterior_on[2] - posterior_off[2]))
    return {
        "seed_count": len(effects),
        "mean_depth_effect": float(np.mean(effects)),
        "depth_effect_95_interval": bootstrap_interval(effects, 702, "v21-depth"),
        "paired_draw_mismatches": paired_mismatches,
        "maximum_oracle_error": maximum_oracle_error,
    }


def run_v21() -> dict[str, object]:
    semantic = semantic_precision_proof()
    broadcast = broadcast_assay()
    composition = cross_latent_composition()
    assays = open_assays()
    recovery = precision_recovery()
    batch = batch_evaluation()
    prior = run_v20()
    gates = {
        "gate_1_semantic": semantic["sharpening_effect"] >= 0.15
        and semantic["analytic_numeric_max_error"] < 1e-12
        and semantic["gaussian_variance_monotone"],
        "gate_2_recovery": recovery["accuracy"] >= 0.70
        and recovery["parameter_mean_absolute_error"] <= 0.08
        and recovery["parameter_95_interval_coverage"] >= 0.85,
        "gate_3_composition": broadcast["depth_effect"] >= 0.20
        and composition["delivered_log_odds_effect"] >= 0.20,
        "gate_4_selective_lesion": broadcast["depth_off"] < 0.40
        and abs(broadcast["off_monitor_depth_effect"]) < 0.05
        and broadcast["local_max_difference"] < 1e-10
        and batch["seed_count"] == 64
        and batch["paired_draw_mismatches"] == 0
        and batch["maximum_oracle_error"] < 1e-10
        and prior["passed"],
        "gate_5_cumulative_regression": prior["passed"],
    }
    return {
        "stage": "V2.1",
        "semantic_proof": semantic,
        "recovery": recovery,
        "broadcast": broadcast,
        "composition": composition,
        "open_assays": assays,
        "batch": batch,
        "v2.0_regression": prior["gates"],
        "gates": gates,
        "passed": all(gates.values()),
    }
