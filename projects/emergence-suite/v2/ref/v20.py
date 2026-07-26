"""V2.0 kernel protocols and gates."""

from __future__ import annotations

import math
from types import MappingProxyType

import numpy as np

from .audit import ProtocolState, audit_one_posterior
from .config import load_parameters
from .factor import Factor
from .inference import ExactEngine
from .model import FiniteModel, Variable
from .oracle import brute_force
from .rng import component_rng
from .statistics import bootstrap_interval, ece_binary
from .templates import categorical_prior, conditional_categorical, dirichlet_update


PARAMETERS = load_parameters("V2.0")


def _model(variables: list[Variable], factors: list[Factor]) -> FiniteModel:
    model = FiniteModel()
    for variable in variables:
        model.add_variable(variable)
    for factor in factors:
        model.add_factor(factor)
    return model


def semantic_models() -> dict[str, tuple[FiniteModel, dict[str, int], tuple[str, ...]]]:
    binary = lambda name, time=None: Variable(name, 2, "latent", time)
    obs = lambda name, time=None: Variable(name, 2, "observation", time)
    prior = categorical_prior("A", [0.35, 0.65])
    transition = np.array([[0.82, 0.18], [0.21, 0.79]])
    likelihood = np.array([[0.88, 0.12], [0.16, 0.84]])

    chain = _model(
        [binary("A"), binary("B"), obs("C")],
        [prior, conditional_categorical("A", "B", transition), conditional_categorical("B", "C", likelihood)],
    )
    fork = _model(
        [binary("A"), obs("B"), obs("C")],
        [prior, conditional_categorical("A", "B", transition), conditional_categorical("A", "C", likelihood)],
    )
    collider_table = np.array(
        [
            [[0.92, 0.08], [0.55, 0.45]],
            [[0.62, 0.38], [0.08, 0.92]],
        ]
    )
    collider = _model(
        [binary("A"), binary("B"), obs("C")],
        [
            categorical_prior("A", [0.35, 0.65]),
            categorical_prior("B", [0.6, 0.4]),
            Factor(("A", "B", "C"), collider_table, "conditional_categorical"),
        ],
    )
    temporal = _model(
        [binary("S0", 0), binary("S1", 1), obs("O1", 1)],
        [
            categorical_prior("S0", [0.7, 0.3]),
            conditional_categorical("S0", "S1", transition),
            conditional_categorical("S1", "O1", likelihood),
        ],
    )
    return {
        "chain": (chain, {"C": 1}, ("A", "B")),
        "fork": (fork, {"B": 1, "C": 0}, ("A",)),
        "collider": (collider, {"C": 1}, ("A", "B")),
        "temporal": (temporal, {"O1": 1}, ("S0", "S1")),
    }


def semantic_proof() -> dict[str, float]:
    engine = ExactEngine()
    errors = {}
    for name, (model, observations, query) in semantic_models().items():
        actual, actual_z = engine.infer(model, query, observations)
        expected, expected_z = brute_force(model, query, observations)
        errors[name] = max(
            float(np.max(np.abs(actual - expected))),
            abs(actual_z - expected_z),
        )
    return errors


def factor_sensitivity() -> dict[str, float]:
    model, observations, _ = semantic_models()["chain"]
    engine = ExactEngine()
    baseline, _ = engine.infer(model, ("A",), observations)
    deleted = FiniteModel(dict(model.variables), list(model.factors[:-1]))
    deleted_p, _ = engine.infer(deleted, ("A",), observations)
    mutated_factors = list(model.factors)
    mutated_factors[-1] = conditional_categorical("B", "C", [[0.55, 0.45], [0.45, 0.55]])
    mutated = FiniteModel(dict(model.variables), mutated_factors)
    mutated_p, _ = engine.infer(mutated, ("A",), observations)
    return {
        "deletion_tv": float(0.5 * np.abs(baseline - deleted_p).sum()),
        "mutation_tv": float(0.5 * np.abs(baseline - mutated_p).sum()),
    }


def recovery(seed_start: int | None = None, seed_end: int | None = None) -> dict[str, object]:
    if seed_start is None or seed_end is None:
        seed_start, seed_end = PARAMETERS["seed_block"]
    reliability = float(PARAMETERS["observation_reliability"])
    trials = int(PARAMETERS["recovery_trials"])
    engine = ExactEngine()
    probabilities: list[float] = []
    outcomes: list[int] = []
    correct: list[float] = []
    parameter_errors: list[float] = []
    coverages: list[float] = []
    paired_draw_mismatches = 0
    audit_failures: list[str] = []

    model = _model(
        [Variable("S", 2), Variable("O", 2, "observation")],
        [
            categorical_prior("S", PARAMETERS["state_prior"]),
            conditional_categorical("S", "O", [[reliability, 1 - reliability], [1 - reliability, reliability]]),
        ],
    )
    for seed in range(seed_start, seed_end + 1):
        world = component_rng(seed, "world")
        paired_world = component_rng(seed, "world")
        if not np.array_equal(world.integers(0, 2, 16), paired_world.integers(0, 2, 16)):
            paired_draw_mismatches += 1
        world = component_rng(seed, "recovery-world")
        states = world.integers(0, 2, trials)
        matches = world.random(trials) < reliability
        observations = np.where(matches, states, 1 - states)
        counts = np.array([np.sum(~matches), np.sum(matches)], dtype=float)
        alpha = dirichlet_update(np.asarray(PARAMETERS["dirichlet_prior"], dtype=float), counts)
        mean = float(alpha[1] / alpha.sum())
        parameter_errors.append(abs(mean - reliability))
        interval_rng = component_rng(seed, "beta-interval")
        samples = interval_rng.beta(alpha[1], alpha[0], size=5000)
        low, high = np.quantile(samples, [0.025, 0.975])
        coverages.append(float(low <= reliability <= high))
        state = ProtocolState(metadata=MappingProxyType({"seed": seed, "stage": "V2.0"}))
        state.parameter_posterior_store["observation_reliability"] = alpha
        for truth, observed in zip(states, observations):
            posterior, z = engine.infer(model, ("S",), {"O": int(observed)})
            state.posterior_store["S"] = posterior
            state.evidence_store["trace"] = z
            try:
                audit_one_posterior(state)
            except AssertionError as exc:
                audit_failures.append(str(exc))
            probabilities.append(float(posterior[1]))
            outcomes.append(int(truth == 1))
            correct.append(float(np.argmax(posterior) == truth))
    p = np.asarray(probabilities)
    y = np.asarray(outcomes)
    return {
        "seed_count": seed_end - seed_start + 1,
        "state_accuracy": float(np.mean(correct)),
        "state_brier": float(np.mean((p - y) ** 2)),
        "state_ece": ece_binary(p, y),
        "parameter_mean_absolute_error": float(np.mean(parameter_errors)),
        "parameter_95_interval_coverage": float(np.mean(coverages)),
        "parameter_error_95_interval": bootstrap_interval(parameter_errors, 701, "v20-parameter-error"),
        "paired_draw_mismatches": paired_draw_mismatches,
        "audit_failures": audit_failures,
    }


def model_comparison() -> dict[str, float]:
    successes, trials = 8, 10
    evidence_fixed = 0.5**trials
    evidence_flexible = math.exp(
        math.lgamma(successes + 1)
        + math.lgamma(trials - successes + 1)
        - math.lgamma(trials + 2)
    )
    engine_model = _model(
        [Variable("H", 2, "structure"), Variable("D", trials + 1, "observation")],
        [
            categorical_prior("H", [0.5, 0.5]),
            Factor(
                ("H", "D"),
                np.array(
                    [
                        [math.comb(trials, k) * 0.5**trials for k in range(trials + 1)],
                        [
                            math.comb(trials, k)
                            * math.exp(math.lgamma(k + 1) + math.lgamma(trials - k + 1) - math.lgamma(trials + 2))
                            for k in range(trials + 1)
                        ],
                    ]
                ),
                "finite_model_evidence",
            ),
        ],
    )
    posterior, total_evidence = ExactEngine().infer(engine_model, ("H",), {"D": successes})
    engine_log_bf = float(np.log(posterior[1]) - np.log(posterior[0]))
    analytic_log_bf = float(np.log(evidence_flexible) - np.log(evidence_fixed))
    maximum_likelihood_flexible = (successes / trials) ** successes * (
        (trials - successes) / trials
    ) ** (trials - successes)
    return {
        "analytic_log_bayes_factor": analytic_log_bf,
        "engine_log_bayes_factor": engine_log_bf,
        "absolute_error": abs(engine_log_bf - analytic_log_bf),
        "flexible_integrated_evidence": evidence_flexible,
        "flexible_maximum_likelihood": maximum_likelihood_flexible,
        "complexity_penalty_log": float(np.log(maximum_likelihood_flexible) - np.log(evidence_flexible)),
        "total_mixture_evidence": total_evidence,
    }


def run_v20() -> dict[str, object]:
    semantic = semantic_proof()
    sensitivity = factor_sensitivity()
    recovered = recovery()
    comparison = model_comparison()
    checks = {
        "gate_1_semantic": max(semantic.values()) < 1e-10,
        "gate_2_recovery": (
            recovered["state_accuracy"] >= 0.75
            and recovered["state_brier"] <= 0.20
            and recovered["state_ece"] <= 0.12
            and recovered["parameter_mean_absolute_error"] <= 0.08
            and recovered["parameter_95_interval_coverage"] >= 0.85
        ),
        "gate_3_comparison": comparison["absolute_error"] < 1e-10
        and comparison["complexity_penalty_log"] > 0,
        "gate_4_batch_mutation": recovered["seed_count"] == 64
        and recovered["paired_draw_mismatches"] == 0
        and min(sensitivity.values()) > 1e-3,
        "gate_5_one_posterior": not recovered["audit_failures"],
    }
    return {
        "stage": "V2.0",
        "semantic_errors": semantic,
        "factor_sensitivity": sensitivity,
        "recovery": recovered,
        "model_comparison": comparison,
        "gates": checks,
        "passed": all(checks.values()),
    }
