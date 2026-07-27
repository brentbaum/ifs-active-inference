"""V2.3.1 bounded formation and schedule-blind dynamic priors."""

from __future__ import annotations

import itertools
import math
from contextlib import contextmanager
from types import MappingProxyType
from typing import Any

import numpy as np

from . import v23
from .audit import ProtocolState, audit_one_posterior
from .config import load_parameters
from .factor import Factor
from .inference import ExactEngine
from .model import FiniteModel
from .precision import precision_categorical
from .statistics import bootstrap_interval, ece_binary
from .templates import dirichlet_update


PARAMETERS = load_parameters("V2.3.1")
INITIAL_STRUCTURE_PRIOR = np.asarray(
    PARAMETERS["initial_structure_prior"], dtype=float
)
STRUCTURE_TRANSITION = np.asarray(
    PARAMETERS["structure_transition"], dtype=float
)
CONTROL_TRANSITION = np.asarray(
    PARAMETERS["controllability_transition"], dtype=float
)
CANDIDATE_EVIDENCE_CONTRASTS = {
    name: float(value)
    for name, value in PARAMETERS["candidate_evidence_contrasts"].items()
}
ACCUMULATION_WEIGHTS = {
    name: float(value)
    for name, value in PARAMETERS["accumulation_weights"].items()
}
ACCUMULATION_OFFSET = float(PARAMETERS["accumulation_offset"])
ACCUMULATION_GAIN = float(PARAMETERS["accumulation_gain"])
ACCUMULATION_LOG_SCORE_CAP = float(
    PARAMETERS["accumulation_log_score_cap"]
)
HIGH_CONTROL_PENALTY = float(PARAMETERS["high_controllability_penalty"])
INTEGRATED_CONTROL_PENALTY = float(
    PARAMETERS["integrated_control_penalty"]
)
CONTROL_EVIDENCE_PRECISION = float(
    PARAMETERS["controllability_evidence_precision"]
)
EVENT_PRECISION = np.asarray(
    PARAMETERS["event_precision_support"], dtype=float
)
REFLEXIVE_MONITOR_RELIABILITY = float(
    PARAMETERS["reflexive_monitor_reliability"]
)
FACTOR_ROLES = {
    ("H", "G", "S"): "self",
    ("H", "G", "S", "E"): "event",
    ("H", "G", "C", "A"): "policy",
    ("H", "G", "C", "A", "W"): "transition",
    ("H", "G", "C", "A", "W", "E"): "transition",
    ("H", "G", "C", "A", "W", "Y"): "outcome",
    ("H", "G", "C", "A", "W", "Y", "E"): "outcome",
    ("H", "E", "R", "X"): "context",
}


def transition_posterior(
    posterior: np.ndarray, transition: np.ndarray
) -> np.ndarray:
    predicted = np.asarray(posterior, dtype=float) @ np.asarray(
        transition, dtype=float
    )
    return predicted / predicted.sum()


def predicted_priors(priors: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    predicted = {name: value.copy() for name, value in priors.items()}
    predicted["H"] = transition_posterior(
        priors["H"], STRUCTURE_TRANSITION
    )
    predicted["C"] = transition_posterior(
        priors["C"], CONTROL_TRANSITION
    )
    return predicted


def _robust_factor(factor: Factor, contrast: float) -> Factor:
    if "H" not in factor.variables or len(factor.variables) == 1:
        return factor
    axis = factor.variables.index("H")
    transient = np.take(factor.values, 0, axis=axis)
    persistent = np.take(factor.values, 1, axis=axis)
    midpoint = 0.5 * (transient + persistent)
    robust_transient = (1.0 - contrast) * midpoint + contrast * transient
    robust_persistent = (1.0 - contrast) * midpoint + contrast * persistent
    values = np.stack([robust_transient, robust_persistent], axis=axis)
    return Factor(factor.variables, values, "bounded_candidate_evidence")


def _robustify(
    model: FiniteModel, contrasts: dict[str, float]
) -> FiniteModel:
    model.factors = [
        _robust_factor(
            factor,
            contrasts.get(FACTOR_ROLES.get(factor.variables, ""), 0.0),
        )
        for factor in model.factors
    ]
    return model


def _replace_reflexive_monitor(model: FiniteModel) -> FiniteModel:
    table = np.array(
        [
            [
                REFLEXIVE_MONITOR_RELIABILITY,
                1.0 - REFLEXIVE_MONITOR_RELIABILITY,
            ],
            [
                1.0 - REFLEXIVE_MONITOR_RELIABILITY,
                REFLEXIVE_MONITOR_RELIABILITY,
            ],
        ]
    )
    model.factors = [
        (
            Factor(("R", "Q"), table, factor.template)
            if factor.variables == ("R", "Q")
            else factor
        )
        for factor in model.factors
    ]
    return model


def _replace_event_precision(model: FiniteModel) -> FiniteModel:
    replacement = precision_categorical(
        "E", "K", "B", v23.EVENT_BASE, EVENT_PRECISION
    )
    model.factors = [
        replacement if factor.variables == ("E", "K", "B") else factor
        for factor in model.factors
    ]
    return model


def _event_gate_controllability(model: FiniteModel) -> FiniteModel:
    """Make C identify controllability in event contexts, not safe slices."""
    gated = []
    for factor in model.factors:
        if factor.variables == ("H", "G", "C", "A", "W"):
            midpoint = factor.values.mean(axis=2, keepdims=True)
            event_values = midpoint + CONTROL_EVIDENCE_PRECISION * (
                factor.values - midpoint
            )
            event_values = np.clip(event_values, 0.01, 0.99)
            event_values /= event_values.sum(axis=-1, keepdims=True)
            neutral = event_values.mean(axis=2, keepdims=True)
            neutral = np.repeat(neutral, 2, axis=2)
            gated.append(
                Factor(
                    ("H", "G", "C", "A", "W", "E"),
                    np.stack([neutral, event_values], axis=-1),
                    "event_gated_action_controlled_transition",
                )
            )
        elif factor.variables == ("H", "G", "C", "A", "W", "Y"):
            neutral = factor.values.mean(axis=2, keepdims=True)
            neutral = np.repeat(neutral, 2, axis=2)
            gated.append(
                Factor(
                    ("H", "G", "C", "A", "W", "Y", "E"),
                    np.stack([neutral, factor.values], axis=-1),
                    "event_gated_joint_policy_outcome",
                )
            )
        else:
            gated.append(factor)
    model.factors = gated
    return model


def _control_contrast_probability(
    previous_world: int,
    action: int,
    controllability: int,
    real_danger: bool,
) -> float:
    rows = np.asarray(
        [
            v23._transition_threat_probability(
                previous_world, action, candidate, real_danger
            )
            for candidate in (0, 1)
        ]
    )
    midpoint = float(rows.mean())
    transformed = midpoint + CONTROL_EVIDENCE_PRECISION * (
        rows[controllability] - midpoint
    )
    return float(np.clip(transformed, 0.01, 0.99))


def _accumulation_factor(
    gain: float | None = None,
    *,
    broadcast_lesion: bool = False,
) -> Factor:
    if gain is None:
        gain = ACCUMULATION_GAIN
    values = np.empty((2, 2, 2, 2, 2, 2))
    for h, event, precision, control, broadcast, adverse in itertools.product(
        range(2), repeat=6
    ):
        effective_broadcast = 1 if broadcast_lesion else broadcast
        score = gain * event * (
            ACCUMULATION_WEIGHTS["overwhelm_uncontrollability"]
            * precision
            * (1 - control)
            + ACCUMULATION_WEIGHTS["overwhelm_collapsed_broadcast"]
            * precision
            * (1 - effective_broadcast)
            + ACCUMULATION_WEIGHTS["uncontrollability"] * (1 - control)
            + ACCUMULATION_WEIGHTS["collapsed_broadcast"]
            * (1 - effective_broadcast)
            + ACCUMULATION_WEIGHTS["adverse_outcome"] * adverse
            + ACCUMULATION_WEIGHTS["overwhelm_precision"] * precision
            - HIGH_CONTROL_PENALTY * control
            - INTEGRATED_CONTROL_PENALTY
            * control
            * effective_broadcast
            - ACCUMULATION_OFFSET
        )
        score = float(
            np.clip(
                score,
                -ACCUMULATION_LOG_SCORE_CAP,
                ACCUMULATION_LOG_SCORE_CAP,
            )
        )
        values[h, event, precision, control, broadcast, adverse] = math.exp(
            (2 * h - 1) * score / 2.0
        )
    return Factor(
        ("H", "E", "K", "C", "R", "Y"),
        values,
        "bounded_log_odds_accumulation",
    )


def formation_model(
    *,
    structure_prior: np.ndarray,
    root_prior: np.ndarray,
    control_prior: np.ndarray,
    broadcast_prior: np.ndarray,
    previous_world: np.ndarray,
    consequence_alpha: np.ndarray,
    overwhelm: int,
    real_danger: bool = False,
    coupling_lesion: bool = False,
    control_lesion: bool = False,
    broadcast_lesion: bool = False,
    action_intervention: bool = False,
    reliability_scale: float = 1.0,
    candidate_evidence_contrasts: dict[str, float] | None = None,
) -> FiniteModel:
    contrasts = (
        CANDIDATE_EVIDENCE_CONTRASTS
        if candidate_evidence_contrasts is None
        else {
            name: float(value)
            for name, value in candidate_evidence_contrasts.items()
        }
    )
    if any(not 0.0 <= value < 1.0 for value in contrasts.values()):
        raise ValueError("candidate evidence contrasts must be in [0,1)")
    if coupling_lesion:
        contrasts = {name: 0.0 for name in CANDIDATE_EVIDENCE_CONTRASTS}
    model = v23.formation_model(
        structure_prior=structure_prior,
        root_prior=root_prior,
        control_prior=control_prior,
        broadcast_prior=broadcast_prior,
        previous_world=previous_world,
        consequence_alpha=consequence_alpha,
        overwhelm=overwhelm,
        real_danger=real_danger,
        coupling_lesion=False,
        control_lesion=control_lesion,
        broadcast_lesion=broadcast_lesion,
        action_intervention=action_intervention,
        reliability_scale=reliability_scale,
    )
    model = _replace_reflexive_monitor(model)
    model = _replace_event_precision(model)
    model = _event_gate_controllability(model)
    model = _robustify(model, contrasts)
    if not coupling_lesion:
        model.add_factor(
            _accumulation_factor(broadcast_lesion=broadcast_lesion)
        )
    return model


def policy_model(
    *,
    priors: dict[str, np.ndarray],
    overwhelm: int,
    coupling_lesion: bool = False,
    control_lesion: bool = False,
    broadcast_lesion: bool = False,
    reliability_scale: float = 1.0,
    candidate_evidence_contrasts: dict[str, float] | None = None,
) -> FiniteModel:
    contrasts = (
        CANDIDATE_EVIDENCE_CONTRASTS
        if candidate_evidence_contrasts is None
        else {
            name: float(value)
            for name, value in candidate_evidence_contrasts.items()
        }
    )
    if coupling_lesion:
        contrasts = {name: 0.0 for name in CANDIDATE_EVIDENCE_CONTRASTS}
    model = v23.policy_model(
        structure_prior=priors["H"],
        root_prior=priors["G"],
        control_prior=priors["C"],
        broadcast_prior=priors["R"],
        overwhelm=overwhelm,
        coupling_lesion=False,
        control_lesion=control_lesion,
        broadcast_lesion=broadcast_lesion,
        reliability_scale=reliability_scale,
    )
    model = _replace_reflexive_monitor(model)
    model = _replace_event_precision(model)
    return _robustify(model, contrasts)


def infer_policy(
    *,
    priors: dict[str, np.ndarray],
    overwhelm: int,
    observations: dict[str, int],
    coupling_lesion: bool = False,
    control_lesion: bool = False,
    broadcast_lesion: bool = False,
    reliability_scale: float = 1.0,
) -> np.ndarray:
    predicted = predicted_priors(priors)
    model = policy_model(
        priors=predicted,
        overwhelm=overwhelm,
        coupling_lesion=coupling_lesion,
        control_lesion=control_lesion,
        broadcast_lesion=broadcast_lesion,
        reliability_scale=reliability_scale,
    )
    posterior, _ = ExactEngine().infer(
        model, ("A",), {**observations, "K": overwhelm}
    )
    return posterior


def _marginal(
    joint: np.ndarray, query: tuple[str, ...], name: str
) -> np.ndarray:
    axis = query.index(name)
    axes = tuple(index for index in range(joint.ndim) if index != axis)
    return joint.sum(axis=axes)


def infer_slice(
    *,
    priors: dict[str, np.ndarray],
    consequence_alpha: np.ndarray,
    overwhelm: int,
    real_danger: bool,
    observations: dict[str, int],
    coupling_lesion: bool = False,
    control_lesion: bool = False,
    broadcast_lesion: bool = False,
    action_intervention: bool = False,
    reliability_scale: float = 1.0,
) -> ProtocolState:
    predicted = predicted_priors(priors)
    model = formation_model(
        structure_prior=predicted["H"],
        root_prior=predicted["G"],
        control_prior=predicted["C"],
        broadcast_prior=predicted["R"],
        previous_world=predicted["W"],
        consequence_alpha=consequence_alpha,
        overwhelm=overwhelm,
        real_danger=real_danger,
        coupling_lesion=coupling_lesion,
        control_lesion=control_lesion,
        broadcast_lesion=broadcast_lesion,
        action_intervention=action_intervention,
        reliability_scale=reliability_scale,
    )
    latent_query = tuple(
        name
        for name in ("H", "G", "S", "C", "R", "E", "A", "W", "Y")
        if name not in observations
    )
    inference_observations = {**observations, "K": overwhelm}
    joint, evidence = ExactEngine().infer(
        model, latent_query, inference_observations
    )
    state = ProtocolState(
        metadata=MappingProxyType(
            {
                "stage": "V2.3.1",
                "overwhelm": overwhelm,
                "real_danger": real_danger,
                "coupling_lesion": coupling_lesion,
                "control_lesion": control_lesion,
                "broadcast_lesion": broadcast_lesion,
                "action_intervention": action_intervention,
                "predicted_persistent_probability": float(predicted["H"][1]),
            }
        )
    )
    for name in ("H", "G", "S", "C", "R", "E", "A", "W", "Y"):
        if name in observations:
            posterior = np.zeros(2)
            posterior[observations[name]] = 1.0
        else:
            posterior = _marginal(joint, latent_query, name)
        state.posterior_store[name] = posterior
    state.parameter_posterior_store["theta_consequence_engage"] = (
        consequence_alpha[0].copy()
    )
    state.parameter_posterior_store["theta_consequence_avoid"] = (
        consequence_alpha[1].copy()
    )
    state.evidence_store["total"] = evidence
    for index, label in enumerate(("transient", "persistent")):
        prior = predicted["H"][index]
        state.evidence_store[f"{label}_conditional"] = float(
            state.posterior_store["H"][index] * evidence / prior
        )
    audit_one_posterior(state)
    return state


def analytic_step_bound(
    contrasts: dict[str, float] | None = None,
) -> dict[str, Any]:
    values = (
        CANDIDATE_EVIDENCE_CONTRASTS
        if contrasts is None
        else contrasts
    )
    factor_log_bounds = {
        name: math.log((1.0 + contrast) / (1.0 - contrast))
        for name, contrast in values.items()
    }
    accumulation_scores = [
        ACCUMULATION_GAIN
        * (
            event * (
                ACCUMULATION_WEIGHTS["overwhelm_uncontrollability"]
                * precision
                * (1 - control)
                + ACCUMULATION_WEIGHTS["overwhelm_collapsed_broadcast"]
                * precision
                * (1 - broadcast)
                + ACCUMULATION_WEIGHTS["uncontrollability"] * (1 - control)
                + ACCUMULATION_WEIGHTS["collapsed_broadcast"]
                * (1 - broadcast)
                + ACCUMULATION_WEIGHTS["adverse_outcome"]
                * adverse
                + ACCUMULATION_WEIGHTS["overwhelm_precision"] * precision
                - HIGH_CONTROL_PENALTY * control
                - INTEGRATED_CONTROL_PENALTY * control * broadcast
                - ACCUMULATION_OFFSET
            )
        )
        for event, precision, control, broadcast, adverse in itertools.product(
            range(2), repeat=5
        )
    ]
    accumulation_log_bound = min(
        max(abs(value) for value in accumulation_scores),
        ACCUMULATION_LOG_SCORE_CAP,
    )
    log_bayes_bound = float(
        sum(factor_log_bounds.values()) + accumulation_log_bound
    )
    evidence_update_bound = math.tanh(log_bayes_bound / 4.0)
    transition_change_bound = max(
        float(STRUCTURE_TRANSITION[0, 1]),
        float(STRUCTURE_TRANSITION[1, 0]),
    )
    return {
        "pointwise_factor_log_ratio_bounds": factor_log_bounds,
        "candidate_factor_count_bound": len(factor_log_bounds),
        "accumulation_log_ratio_bound": accumulation_log_bound,
        "slice_log_bayes_factor_bound": log_bayes_bound,
        "evidence_update_bound": evidence_update_bound,
        "transition_change_bound": transition_change_bound,
        "adjacent_slice_change_bound": (
            evidence_update_bound + transition_change_bound
        ),
    }


def _manual_structure_posterior(
    model: FiniteModel, observations: dict[str, int]
) -> np.ndarray:
    latent_names = [
        name for name in model.variables if name not in observations and name != "H"
    ]
    masses = np.zeros(2)
    for h in range(2):
        for values in itertools.product((0, 1), repeat=len(latent_names)):
            assignment = dict(zip(latent_names, values))
            assignment.update(observations)
            assignment["H"] = h
            mass = 1.0
            for factor in model.factors:
                mass *= factor.values[
                    tuple(assignment[name] for name in factor.variables)
                ]
            masses[h] += mass
    return masses / masses.sum()


def semantic_proofs() -> dict[str, Any]:
    inherited = v23.semantic_proofs()
    priors = {
        "H": v23.STRUCTURE_PRIOR.copy(),
        "G": v23.ROOT_PRIOR.copy(),
        "C": v23.CONTROL_PRIOR.copy(),
        "R": v23.BROADCAST_PRIOR.copy(),
        "W": v23.WORLD_PRIOR.copy(),
    }
    predicted = predicted_priors(priors)
    model = formation_model(
        structure_prior=predicted["H"],
        root_prior=predicted["G"],
        control_prior=predicted["C"],
        broadcast_prior=predicted["R"],
        previous_world=predicted["W"],
        consequence_alpha=np.tile(v23.POLICY_PRIOR, (2, 1)),
        overwhelm=1,
    )
    observations = {"B": 1, "Q": 0, "X": 1, "A": 1, "O": 1, "K": 1}
    engine, _ = ExactEngine().infer(model, ("H",), observations)
    manual = _manual_structure_posterior(model, observations)
    gated_transition = next(
        factor
        for factor in model.factors
        if factor.variables == ("H", "G", "C", "A", "W", "E")
    )
    safe_control_difference = float(
        np.max(
            np.abs(
                gated_transition.values[:, :, 0, :, :, 0]
                - gated_transition.values[:, :, 1, :, :, 0]
            )
        )
    )
    event_control_difference = float(
        np.max(
            np.abs(
                gated_transition.values[:, :, 0, :, :, 1]
                - gated_transition.values[:, :, 1, :, :, 1]
            )
        )
    )
    h_factors = [
        factor
        for factor in model.factors
        if "H" in factor.variables and len(factor.variables) > 1
    ]
    maximum_observed_log_ratio = 0.0
    for factor in h_factors:
        axis = factor.variables.index("H")
        first = np.take(factor.values, 0, axis=axis)
        second = np.take(factor.values, 1, axis=axis)
        maximum_observed_log_ratio = max(
            maximum_observed_log_ratio,
            float(np.max(np.abs(np.log(second / first)))),
        )
    return {
        "inherited_routes": inherited,
        "dynamic_structure": {
            "transient_to_persistent": float(STRUCTURE_TRANSITION[0, 1]),
            "persistent_to_transient": float(STRUCTURE_TRANSITION[1, 0]),
            "zero_prior_prediction": transition_posterior(
                np.array([1.0, 0.0]), STRUCTURE_TRANSITION
            ).tolist(),
            "one_prior_prediction": transition_posterior(
                np.array([0.0, 1.0]), STRUCTURE_TRANSITION
            ).tolist(),
        },
        "bounded_candidate_evidence": {
            **analytic_step_bound(),
            "observed_candidate_factor_count": len(h_factors),
            "maximum_observed_factor_log_ratio": maximum_observed_log_ratio,
        },
        "event_context_controllability": {
            "safe_slice_control_row_maximum_difference": (
                safe_control_difference
            ),
            "event_slice_control_row_maximum_difference": (
                event_control_difference
            ),
        },
        "finite_comparison": {
            "engine_posterior": engine.tolist(),
            "manual_posterior": manual.tolist(),
            "maximum_error": float(np.max(np.abs(engine - manual))),
        },
    }


def _initial_priors(
    structure_prior: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    return {
        "H": (
            INITIAL_STRUCTURE_PRIOR
            if structure_prior is None
            else structure_prior
        ).copy(),
        "G": v23.ROOT_PRIOR.copy(),
        "C": v23.CONTROL_PRIOR.copy(),
        "R": v23.BROADCAST_PRIOR.copy(),
        "W": v23.WORLD_PRIOR.copy(),
    }


def run_world(
    seed: int,
    schedule: list[dict[str, Any]],
    *,
    action_mode: str,
    stream_family: str,
    structure_prior: np.ndarray | None = None,
    coupling_lesion: bool = False,
    control_lesion: bool = False,
    broadcast_lesion: bool = False,
    reliability_scale: float = 1.0,
) -> dict[str, Any]:
    priors = _initial_priors(structure_prior)
    consequence_alpha = np.tile(v23.POLICY_PRIOR, (2, 1))
    previous_world_truth = 0
    traces = []
    states = []
    for time, slice_config in enumerate(schedule):
        event = int(slice_config["event"])
        overwhelm = int(slice_config["overwhelm"])
        controllability = int(slice_config["controllability"])
        broadcast = int(slice_config["broadcast"])
        real_danger = bool(slice_config["real_danger"])
        event_factor = precision_categorical(
            "E", "K", "B", v23.EVENT_BASE, EVENT_PRECISION
        )
        event_probability = float(
            event_factor.values[event, overwhelm, event]
        )
        event_match = v23._sample_binary(
            seed, f"{stream_family}-event-match-{time}", event_probability
        )
        event_observation = event if event_match else 1 - event
        monitor = REFLEXIVE_MONITOR_RELIABILITY
        monitor_match = v23._sample_binary(
            seed, f"{stream_family}-broadcast-match-{time}", monitor
        )
        monitor_observation = broadcast if monitor_match else 1 - broadcast
        context_probability = (
            float(v23.PARAMETERS["context_now_transient"])
            if event == 1 and broadcast == 1
            else 0.5
        )
        context_observation = v23._sample_binary(
            seed,
            f"{stream_family}-context-now-{time}",
            context_probability,
        )
        exogenous = {
            "B": event_observation,
            "Q": monitor_observation,
            "X": context_observation,
        }
        if action_mode == "closed_loop":
            policy = infer_policy(
                priors=priors,
                overwhelm=overwhelm,
                observations=exogenous,
                coupling_lesion=coupling_lesion,
                control_lesion=control_lesion,
                broadcast_lesion=broadcast_lesion,
                reliability_scale=reliability_scale,
            )
            action_probability = float(policy[1])
            action = v23._sample_binary(
                seed,
                f"{stream_family}-policy-uniform-{time}",
                action_probability,
            )
        elif action_mode == "engage_replay":
            action_probability = 0.0
            action = 0
        elif action_mode == "declared":
            action = int(slice_config.get("action", 0))
            action_probability = float(action)
        else:
            raise ValueError(f"unsupported action mode {action_mode}")

        threat_probability = v23._transition_threat_probability(
            previous_world_truth, action, controllability, real_danger
        )
        if event:
            threat_probability = _control_contrast_probability(
                previous_world_truth,
                action,
                controllability,
                real_danger,
            )
        world = v23._sample_binary(
            seed,
            f"{stream_family}-world-uniform-{time}",
            threat_probability,
        )
        outcome_match = v23._sample_binary(
            seed,
            f"{stream_family}-outcome-match-{time}",
            float(v23.PARAMETERS["outcome_observation_reliability"]),
        )
        outcome_observation = world if outcome_match else 1 - world
        observations = {
            **exogenous,
            "A": action,
            "O": outcome_observation,
        }
        state = infer_slice(
            priors=priors,
            consequence_alpha=consequence_alpha,
            overwhelm=overwhelm,
            real_danger=real_danger,
            observations=observations,
            coupling_lesion=coupling_lesion,
            control_lesion=control_lesion,
            broadcast_lesion=broadcast_lesion,
            action_intervention=action_mode != "closed_loop",
            reliability_scale=reliability_scale,
        )
        consequence_alpha[action] = dirichlet_update(
            consequence_alpha[action],
            np.array(
                [
                    float(outcome_observation == 1),
                    float(outcome_observation == 0),
                ]
            ),
        )
        state.parameter_posterior_store["theta_consequence_engage"] = (
            consequence_alpha[0].copy()
        )
        state.parameter_posterior_store["theta_consequence_avoid"] = (
            consequence_alpha[1].copy()
        )
        audit_one_posterior(state)
        predicted_h = float(
            state.metadata["predicted_persistent_probability"]
        )
        transient_evidence = state.evidence_store["transient_conditional"]
        persistent_evidence = state.evidence_store["persistent_conditional"]
        traces.append(
            {
                "time": time,
                "persistent_probability": float(
                    state.posterior_store["H"][1]
                ),
                "predicted_persistent_probability": predicted_h,
                "slice_log_bayes_factor": float(
                    math.log(persistent_evidence / transient_evidence)
                ),
                "root_threat_probability": float(
                    state.posterior_store["G"][1]
                ),
                "high_controllability_probability": float(
                    state.posterior_store["C"][1]
                ),
                "integrated_broadcast_probability": float(
                    state.posterior_store["R"][1]
                ),
                "event_probability": float(state.posterior_store["E"][1]),
                "policy_avoid_probability": action_probability,
                "action": action,
                "previous_world": previous_world_truth,
                "world": world,
                "adverse_observation": outcome_observation,
                "event_observation": event_observation,
                "context_observation": context_observation,
                "monitor_observation": monitor_observation,
                "model_evidence": state.evidence_store["total"],
            }
        )
        states.append(state)
        priors = {
            name: state.posterior_store[name].copy()
            for name in ("H", "G", "C", "R", "W")
        }
        previous_world_truth = world

    persistent = np.asarray(
        [trace["persistent_probability"] for trace in traces]
    )
    actions = np.asarray([trace["action"] for trace in traces])
    worlds = np.asarray([trace["world"] for trace in traces])
    outcomes = np.asarray(
        [trace["adverse_observation"] for trace in traces]
    )
    avoid_mask = actions == 1
    engage_mask = actions == 0
    threat_after_avoid = (
        float(worlds[avoid_mask].mean()) if np.any(avoid_mask) else 0.0
    )
    threat_after_engage = (
        float(worlds[engage_mask].mean()) if np.any(engage_mask) else 0.0
    )
    mediator = float(
        avoid_mask.mean() * (threat_after_avoid - threat_after_engage)
    )
    initial = float(
        INITIAL_STRUCTURE_PRIOR[1]
        if structure_prior is None
        else structure_prior[1]
    )
    steps = np.diff(np.concatenate([[initial], persistent]))
    return {
        "seed": seed,
        "traces": traces,
        "states": states,
        "final_persistent_probability": float(persistent[-1]),
        "final_root_probability": traces[-1]["root_threat_probability"],
        "final_controllability_probability": traces[-1][
            "high_controllability_probability"
        ],
        "final_broadcast_probability": traces[-1][
            "integrated_broadcast_probability"
        ],
        "avoidance_rate": float(actions.mean()),
        "adverse_transition_rate": float(worlds.mean()),
        "adverse_outcome_rate": float(outcomes.mean()),
        "realized_avoidance_mediator": mediator,
        "formation_change": float(persistent[-1] - initial),
        "maximum_step": float(np.max(np.abs(steps))),
        "step_injections": np.abs(steps).tolist(),
    }


@contextmanager
def _repaired_evaluation_context():
    """Route frozen V2.3 assay definitions through the repaired public API."""
    original_run_world = v23.run_world
    original_infer_slice = v23.infer_slice
    original_infer_policy = v23.infer_policy
    try:
        v23.run_world = run_world
        v23.infer_slice = infer_slice
        v23.infer_policy = infer_policy
        yield
    finally:
        v23.run_world = original_run_world
        v23.infer_slice = original_infer_slice
        v23.infer_policy = original_infer_policy


def original_open_assays(
    *,
    seed_start: int | None = None,
    seed_end: int | None = None,
    structure_prior: np.ndarray | None = None,
    reliability_scale: float = 1.0,
) -> dict[str, Any]:
    if seed_start is None or seed_end is None:
        seed_start, seed_end = PARAMETERS["seed_block"]
    with _repaired_evaluation_context():
        return v23.open_assays(
            seed_start=seed_start,
            seed_end=seed_end,
            structure_prior=structure_prior,
            reliability_scale=reliability_scale,
        )


def _dynamic_recovery_attempt() -> dict[str, Any]:
    original_block = v23.PARAMETERS["recovery_seed_block"]
    v23.PARAMETERS["recovery_seed_block"] = PARAMETERS["recovery_seed_block"]
    try:
        with _repaired_evaluation_context():
            base = v23.recovery_assay()
    finally:
        v23.PARAMETERS["recovery_seed_block"] = original_block
    probabilities = []
    truths = []
    confusion = np.zeros((2, 2), dtype=int)
    start, end = PARAMETERS["recovery_seed_block"]
    for offset, seed in enumerate(range(start, end + 1)):
        inference_priors = _initial_priors()
        generation_priors = _initial_priors()
        initial_truth = offset % 2
        generation_priors["H"] = np.eye(2)[initial_truth]
        consequence_alpha = np.tile(v23.POLICY_PRIOR, (2, 1))
        for time in range(24):
            overwhelm = time % 2
            predicted = predicted_priors(generation_priors)
            model = formation_model(
                structure_prior=predicted["H"],
                root_prior=predicted["G"],
                control_prior=predicted["C"],
                broadcast_prior=predicted["R"],
                previous_world=predicted["W"],
                consequence_alpha=consequence_alpha,
                overwhelm=overwhelm,
            )
            query = (
                "H",
                "G",
                "C",
                "R",
                "W",
                "B",
                "Q",
                "X",
                "A",
                "O",
            )
            generated, _ = ExactEngine().infer(
                model, query, {"K": overwhelm}
            )
            rng = v23.component_rng(
                seed, f"v231-dynamic-recovery-{initial_truth}-{time}"
            )
            flat_index = int(
                rng.choice(generated.size, p=generated.reshape(-1))
            )
            sampled = np.unravel_index(flat_index, generated.shape)
            assignment = {
                name: int(value) for name, value in zip(query, sampled)
            }
            state = infer_slice(
                priors=inference_priors,
                consequence_alpha=consequence_alpha,
                overwhelm=overwhelm,
                real_danger=False,
                observations={
                    name: assignment[name]
                    for name in ("B", "Q", "X", "A", "O")
                },
            )
            truth = assignment["H"]
            probability = float(state.posterior_store["H"][1])
            prediction = int(probability >= 0.5)
            probabilities.append(probability)
            truths.append(truth)
            confusion[truth, prediction] += 1
            action = assignment["A"]
            outcome = assignment["O"]
            consequence_alpha[action] = dirichlet_update(
                consequence_alpha[action],
                np.array(
                    [float(outcome == 1), float(outcome == 0)]
                ),
            )
            inference_priors = {
                name: state.posterior_store[name].copy()
                for name in ("H", "G", "C", "R", "W")
            }
            generation_priors = {
                name: np.eye(2)[assignment[name]]
                for name in ("H", "G", "C", "R", "W")
            }
    probability_array = np.asarray(probabilities)
    truth_array = np.asarray(truths)
    true_probabilities = np.where(
        truth_array == 1, probability_array, 1.0 - probability_array
    )
    base.update(
        {
            "structure_confusion_matrix": confusion.tolist(),
            "structure_accuracy": float(
                np.mean((probability_array >= 0.5) == truth_array)
            ),
            "mean_true_structure_probability": float(
                np.mean(true_probabilities)
            ),
            "structure_brier": float(
                np.mean((probability_array - truth_array) ** 2)
            ),
            "structure_ece": ece_binary(probability_array, truth_array),
            "structure_recovery_world_count": end - start + 1,
            "structure_recovery_slice_count_per_world": 24,
            "structure_recovery_generator": (
                "exact dynamic joint-state sampling"
            ),
        }
    )
    return base


def recovery_assay() -> dict[str, Any]:
    original_block = v23.PARAMETERS["recovery_seed_block"]
    v23.PARAMETERS["recovery_seed_block"] = PARAMETERS["recovery_seed_block"]
    try:
        with _repaired_evaluation_context():
            base = v23.recovery_assay()
    finally:
        v23.PARAMETERS["recovery_seed_block"] = original_block

    controlled = {
        "event": 1,
        "overwhelm": 1,
        "controllability": 1,
        "broadcast": 1,
        "real_danger": False,
    }
    persistent = {
        "event": 1,
        "overwhelm": 1,
        "controllability": 0,
        "broadcast": 0,
        "real_danger": False,
    }
    probabilities = []
    truths = []
    confusion = np.zeros((2, 2), dtype=int)
    start, end = PARAMETERS["recovery_seed_block"]
    for offset, seed in enumerate(range(start, end + 1)):
        truth = offset % 2
        schedule = [
            (controlled if truth == 0 else persistent).copy()
            for _ in range(24)
        ]
        result = run_world(
            seed,
            schedule,
            action_mode="closed_loop",
            stream_family=f"v231-regime-recovery-{truth}",
        )
        probability = result["final_persistent_probability"]
        prediction = int(probability >= 0.5)
        probabilities.append(probability)
        truths.append(truth)
        confusion[truth, prediction] += 1
    probability_array = np.asarray(probabilities)
    truth_array = np.asarray(truths)
    true_probabilities = np.where(
        truth_array == 1, probability_array, 1.0 - probability_array
    )
    base.update(
        {
            "structure_confusion_matrix": confusion.tolist(),
            "structure_accuracy": float(
                np.mean((probability_array >= 0.5) == truth_array)
            ),
            "mean_true_structure_probability": float(
                np.mean(true_probabilities)
            ),
            "structure_brier": float(
                np.mean((probability_array - truth_array) ** 2)
            ),
            "structure_ece": ece_binary(probability_array, truth_array),
            "structure_recovery_slice_count": 24,
            "structure_recovery_generator": (
                "paired controlled-integrated versus "
                "low-control-collapsed regimes"
            ),
        }
    )
    return base


def lesion_assays() -> dict[str, Any]:
    with _repaired_evaluation_context():
        return v23.lesion_assays()


@contextmanager
def _stage_parameter_context(scale: float):
    global ACCUMULATION_WEIGHTS
    global CONTROL_EVIDENCE_PRECISION
    global EVENT_PRECISION
    global REFLEXIVE_MONITOR_RELIABILITY
    global STRUCTURE_TRANSITION
    global CONTROL_TRANSITION

    originals = {
        "weights": ACCUMULATION_WEIGHTS,
        "control_precision": CONTROL_EVIDENCE_PRECISION,
        "event_precision": EVENT_PRECISION,
        "monitor": REFLEXIVE_MONITOR_RELIABILITY,
        "structure_transition": STRUCTURE_TRANSITION,
        "control_transition": CONTROL_TRANSITION,
    }
    shift = 0.5 * (scale - 1.0)
    ACCUMULATION_WEIGHTS = dict(ACCUMULATION_WEIGHTS)
    ACCUMULATION_WEIGHTS["uncontrollability"] += shift
    ACCUMULATION_WEIGHTS["overwhelm_collapsed_broadcast"] -= shift
    CONTROL_EVIDENCE_PRECISION *= scale
    EVENT_PRECISION = EVENT_PRECISION * scale
    REFLEXIVE_MONITOR_RELIABILITY = float(
        np.clip(
            1.0 - (1.0 - REFLEXIVE_MONITOR_RELIABILITY) / scale,
            0.5,
            0.999,
        )
    )
    STRUCTURE_TRANSITION = STRUCTURE_TRANSITION.copy()
    STRUCTURE_TRANSITION[0, 1] *= scale
    STRUCTURE_TRANSITION[0, 0] = 1.0 - STRUCTURE_TRANSITION[0, 1]
    CONTROL_TRANSITION = CONTROL_TRANSITION.copy()
    CONTROL_TRANSITION[0, 1] *= scale
    CONTROL_TRANSITION[1, 0] *= scale
    CONTROL_TRANSITION[0, 0] = 1.0 - CONTROL_TRANSITION[0, 1]
    CONTROL_TRANSITION[1, 1] = 1.0 - CONTROL_TRANSITION[1, 0]
    try:
        yield
    finally:
        ACCUMULATION_WEIGHTS = originals["weights"]
        CONTROL_EVIDENCE_PRECISION = originals["control_precision"]
        EVENT_PRECISION = originals["event_precision"]
        REFLEXIVE_MONITOR_RELIABILITY = originals["monitor"]
        STRUCTURE_TRANSITION = originals["structure_transition"]
        CONTROL_TRANSITION = originals["control_transition"]


def sensitivity_profile() -> dict[str, Any]:
    start, end = PARAMETERS["sensitivity_seed_block"]
    profiles = []
    for offset, seed in enumerate(range(start, end + 1)):
        rng = v23.component_rng(seed, "v231-neighborhood")
        scale = float(rng.uniform(0.9, 1.1))
        persistent_prior = float(rng.uniform(0.10, 0.35))
        with _stage_parameter_context(scale):
            result = original_open_assays(
                seed_start=seed,
                seed_end=seed,
                structure_prior=np.array(
                    [1.0 - persistent_prior, persistent_prior]
                ),
                reliability_scale=scale,
            )
            local_bound = analytic_step_bound()[
                "adjacent_slice_change_bound"
            ]
        chain = result["closed_loop_vs_exact_replay"]
        profiles.append(
            {
                "index": offset,
                "seed": seed,
                "joint_stage_scale": scale,
                "persistent_prior": persistent_prior,
                "analytic_step_bound": local_bound,
                "adaptive_persistence": result[
                    "adaptive_persistent_threat"
                ]["final_persistent_95_interval"][0],
                "policy_effect": chain["policy_avoidance"][0],
                "transition_effect": chain["world_transition"][0],
                "observation_effect": chain["observed_evidence"][0],
                "structure_effect": chain["persistent_model"][0],
                "root_effect": chain["root_persistence"][0],
                "mediator_effect": chain["realized_mediator"][0],
            }
        )
    effect_keys = (
        "adaptive_persistence",
        "policy_effect",
        "transition_effect",
        "observation_effect",
        "structure_effect",
        "root_effect",
        "mediator_effect",
    )
    signs_survive = all(
        float(np.mean([profile[key] for profile in profiles])) > 0
        for key in effect_keys
    ) and all(
        profile["analytic_step_bound"] < 0.294529387
        for profile in profiles
    )
    joint = {}
    for label, scale in (("minus_10_percent", 0.9), ("plus_10_percent", 1.1)):
        with _stage_parameter_context(scale):
            result = original_open_assays(
                seed_start=PARAMETERS["seed_block"][0],
                seed_end=PARAMETERS["seed_block"][0] + 15,
                reliability_scale=scale,
            )
        chain = result["closed_loop_vs_exact_replay"]
        joint[label] = {
            "adaptive_persistence": result[
                "adaptive_persistent_threat"
            ]["final_persistent_95_interval"][0],
            "chain_effects": {key: value[0] for key, value in chain.items()},
        }
    prior_sensitivity = {}
    for persistent_prior in (0.10, 0.30, 0.35):
        result = original_open_assays(
            seed_start=PARAMETERS["seed_block"][0],
            seed_end=PARAMETERS["seed_block"][0] + 15,
            structure_prior=np.array(
                [1.0 - persistent_prior, persistent_prior]
            ),
        )
        prior_sensitivity[str(persistent_prior)] = {
            "adaptive_persistence": result[
                "adaptive_persistent_threat"
            ]["final_persistent_95_interval"][0],
            "closed_loop_structure_effect": result[
                "closed_loop_vs_exact_replay"
            ]["persistent_model"][0],
        }
    return {
        "neighborhood_count": len(profiles),
        "neighborhood_signs_survive": signs_survive,
        "full_profile": profiles,
        "joint_reliability_perturbations": joint,
        "structure_prior_sensitivity": prior_sensitivity,
    }


def _effect_interval(
    values: list[float], seed: int, component: str
) -> tuple[float, float, float]:
    low, high = bootstrap_interval(values, seed, component)
    return float(np.mean(values)), low, high


def _overwhelm_evidence(
    result: dict[str, Any], acute: list[int]
) -> float:
    factor = precision_categorical(
        "E", "K", "B", v23.EVENT_BASE, EVENT_PRECISION
    )
    total = 0.0
    for time in acute:
        observation = int(result["traces"][time]["event_observation"])
        high = float(factor.values[1, 1, observation])
        ordinary = float(factor.values[1, 0, observation])
        total += math.log(high / ordinary)
    return total


def _conditional_calibration_curve(
    rows: list[dict[str, Any]],
    field: str,
    other_field: str,
    marginal: list[dict[str, float]],
) -> list[dict[str, float]]:
    predictor = np.asarray([row[field] for row in rows], dtype=float)
    other = np.asarray([row[other_field] for row in rows], dtype=float)
    outcome = np.asarray(
        [row["final_persistent_probability"] for row in rows], dtype=float
    )
    design = np.column_stack([np.ones(len(rows)), predictor, other])
    coefficients = np.linalg.lstsq(design, outcome, rcond=None)[0]
    other_mean = float(other.mean())
    adjusted = []
    for group in marginal:
        mean_predictor = group["mean_predictor"]
        adjusted.append(
            {
                **group,
                "marginal_mean_formation_probability": group[
                    "mean_formation_probability"
                ],
                "mean_formation_probability": float(
                    coefficients
                    @ np.array([1.0, mean_predictor, other_mean])
                ),
                "held_constant": other_field,
                "held_constant_value": other_mean,
            }
        )
    return adjusted


def generalization_assay(
    *,
    diagnosis_world_count: int = 512,
    paired_world_count: int = 64,
) -> dict[str, Any]:
    from run_v231_diagnosis import (
        OLD_STEP_BOUND,
        cross_validated_r2,
        design_matrices,
        grouped_curve,
        make_schedule,
        schedule_dimensions,
    )

    calibration_rows = []
    all_steps = []
    for index, seed in enumerate(range(63000, 63000 + diagnosis_world_count)):
        regularity, length, timing, acute_count, low_fraction = (
            schedule_dimensions(index)
        )
        schedule, acute = make_schedule(
            seed,
            regularity,
            length,
            timing,
            acute_count,
            low_fraction,
        )
        result = run_world(
            seed,
            schedule,
            action_mode="declared",
            stream_family="v231-generalization",
        )
        probability_high_control = result[
            "final_controllability_probability"
        ]
        bounded = float(
            np.clip(probability_high_control, 1e-12, 1.0 - 1e-12)
        )
        uncontrollability = -math.log(bounded / (1.0 - bounded))
        calibration_rows.append(
            {
                "seed": seed,
                "regularity": regularity,
                "run_length": length,
                "acute_timing": timing,
                "acute_count": acute_count,
                "low_control_fraction": low_fraction,
                "uncontrollability_log_evidence": uncontrollability,
                "cumulative_overwhelm_precision": _overwhelm_evidence(
                    result, acute
                ),
                "final_persistent_probability": result[
                    "final_persistent_probability"
                ],
                "maximum_step": result["maximum_step"],
            }
        )
        all_steps.extend(result["step_injections"])

    theory, surface = design_matrices(calibration_rows)
    outcome = np.asarray(
        [
            row["final_persistent_probability"]
            for row in calibration_rows
        ]
    )
    theory_r2 = cross_validated_r2(theory, outcome)
    combined_r2 = cross_validated_r2(
        np.column_stack([theory, surface]), outcome
    )
    marginal_curves = {
        field: grouped_curve(calibration_rows, field)
        for field in (
            "uncontrollability_log_evidence",
            "cumulative_overwhelm_precision",
        )
    }
    curves = {
        "uncontrollability_log_evidence": _conditional_calibration_curve(
            calibration_rows,
            "uncontrollability_log_evidence",
            "cumulative_overwhelm_precision",
            marginal_curves["uncontrollability_log_evidence"],
        ),
        "cumulative_overwhelm_precision": _conditional_calibration_curve(
            calibration_rows,
            "cumulative_overwhelm_precision",
            "uncontrollability_log_evidence",
            marginal_curves["cumulative_overwhelm_precision"],
        ),
    }
    monotone = {
        field: all(
            right["mean_formation_probability"]
            >= left["mean_formation_probability"] - 1e-12
            for left, right in zip(curve, curve[1:])
        )
        for field, curve in curves.items()
    }

    paired_differences = []
    paired_rows = []
    for index, seed in enumerate(
        range(
            PARAMETERS["seed_block"][0],
            PARAMETERS["seed_block"][0] + paired_world_count,
        )
    ):
        regularity, length, timing, acute_count, _ = schedule_dimensions(index)
        if acute_count == 0:
            acute_count = 1
        low_schedule, _ = make_schedule(
            seed, regularity, length, timing, acute_count, 1.0
        )
        high_schedule, _ = make_schedule(
            seed, regularity, length, timing, acute_count, 0.0
        )
        low = run_world(
            seed,
            low_schedule,
            action_mode="declared",
            stream_family="v231-generalization-pair",
        )
        high = run_world(
            seed,
            high_schedule,
            action_mode="declared",
            stream_family="v231-generalization-pair",
        )
        difference = (
            low["final_persistent_probability"]
            - high["final_persistent_probability"]
        )
        paired_differences.append(difference)
        all_steps.extend(low["step_injections"])
        all_steps.extend(high["step_injections"])
        paired_rows.append(
            {
                "seed": seed,
                "regularity": regularity,
                "run_length": length,
                "acute_timing": timing,
                "acute_count": acute_count,
                "low_final": low["final_persistent_probability"],
                "high_final": high["final_persistent_probability"],
                "low_minus_high": difference,
                "low_maximum_step": low["maximum_step"],
                "high_maximum_step": high["maximum_step"],
            }
        )

    boundary = _effect_interval(
        paired_differences, 63980, "v231-generalization-boundary"
    )
    return {
        "calibration_world_count": len(calibration_rows),
        "paired_world_count": len(paired_rows),
        "calibration_curves": curves,
        "marginal_calibration_curves": marginal_curves,
        "calibration_monotone": monotone,
        "theory_only_cv_r2": theory_r2,
        "combined_cv_r2": combined_r2,
        "surface_incremental_cv_r2": combined_r2 - theory_r2,
        "low_minus_high_control_95_interval": boundary,
        "step_injection": {
            "count": len(all_steps),
            "percentile_99": float(np.quantile(all_steps, 0.99)),
            "maximum": float(np.max(all_steps)),
            "old_bound": OLD_STEP_BOUND,
            "exceedances": int(np.sum(np.asarray(all_steps) > OLD_STEP_BOUND)),
        },
        "raw_step_injections": all_steps,
        "calibration_per_world": calibration_rows,
        "paired_per_world": paired_rows,
    }


def _original_gate_3_pass(open_results: dict[str, Any]) -> bool:
    chain = open_results["closed_loop_vs_exact_replay"]
    return (
        open_results["acute_formation"]["final_persistent_95_interval"][0]
        >= 0.70
        and open_results["gradual_accumulation"][
            "final_persistent_95_interval"
        ][0]
        >= 0.70
        and open_results["gradual_accumulation"][
            "formation_change_95_interval"
        ][0]
        >= 0.35
        and open_results["gradual_accumulation"][
            "acute_minus_gradual_maximum_step"
        ]
        >= 0.05
        and open_results["overwhelm_with_control"][
            "acute_minus_controlled_95_interval"
        ][0]
        >= 0.15
        and open_results["low_control_without_overwhelm"][
            "low_minus_high_control_95_interval"
        ][0]
        >= 0.15
        and open_results["adaptive_persistent_threat"][
            "final_persistent_95_interval"
        ][0]
        >= 0.75
        and all(value[1] > 0 for value in chain.values())
    )


def run_v231(
    *,
    include_sensitivity: bool = True,
    verify_determinism: bool = False,
    include_generalization: bool = True,
) -> dict[str, Any]:
    from .v20 import run_v20
    from .v21 import run_v21
    from .v221 import run_v221

    semantic = semantic_proofs()
    recovery = recovery_assay()
    opened = original_open_assays()
    public_opened = {
        key: value for key, value in opened.items() if key != "worlds"
    }
    generalization = (
        generalization_assay()
        if include_generalization
        else generalization_assay(
            diagnosis_world_count=64, paired_world_count=16
        )
    )
    public_generalization = {
        key: value
        for key, value in generalization.items()
        if not key.endswith("per_world") and key != "raw_step_injections"
    }
    expanded_steps = [
        step
        for worlds in opened["worlds"].values()
        for world in worlds
        for step in world["step_injections"]
    ] + generalization["raw_step_injections"]
    expanded_step_injection = {
        "count": len(expanded_steps),
        "percentile_99": float(np.quantile(expanded_steps, 0.99)),
        "maximum": float(np.max(expanded_steps)),
        "analytic_bound": analytic_step_bound()[
            "adjacent_slice_change_bound"
        ],
        "old_bound": 0.294529387,
        "exceedances": int(
            np.sum(np.asarray(expanded_steps) > 0.294529387)
        ),
    }
    lesions = lesion_assays()
    sensitivity = sensitivity_profile() if include_sensitivity else {}
    v20 = run_v20()
    v21 = run_v21()
    v221 = run_v221()

    determinism = {
        "full_seed_block_checked_twice": verify_determinism,
        "scientific_summaries_identical": True,
    }
    if verify_determinism:
        repeated = original_open_assays()
        repeated_generalization = generalization_assay()
        first = {
            key: value for key, value in opened.items() if key != "worlds"
        }
        second = {
            key: value for key, value in repeated.items() if key != "worlds"
        }
        repeated_generalization_public = {
            key: value
            for key, value in repeated_generalization.items()
            if not key.endswith("per_world")
            and key != "raw_step_injections"
        }
        determinism["scientific_summaries_identical"] = (
            first == second
            and repeated_generalization_public == public_generalization
        )

    inherited = semantic["inherited_routes"]
    bound = semantic["bounded_candidate_evidence"]
    semantic_pass = (
        inherited["event_precision"]["log_odds_increase"] >= 1.0
        and inherited["event_precision"]["analytic_factor_error"] < 1e-12
        and inherited["controllability"][
            "low_control_action_log_evidence_difference"
        ]
        < 1e-12
        and inherited["controllability"][
            "high_control_action_log_evidence_difference"
        ]
        >= 0.50
        and inherited["action_transition"][
            "avoid_minus_engage_threat_probability"
        ]
        >= 0.50
        and inherited["reflexive_broadcast"][
            "persistent_probability_effect"
        ]
        >= 0.10
        and semantic["finite_comparison"]["maximum_error"] < 1e-10
        and semantic["event_context_controllability"][
            "safe_slice_control_row_maximum_difference"
        ]
        < 1e-12
        and semantic["event_context_controllability"][
            "event_slice_control_row_maximum_difference"
        ]
        > 0.10
        and bound["adjacent_slice_change_bound"] < 0.294529387
        and bound["maximum_observed_factor_log_ratio"]
        <= max(bound["pointwise_factor_log_ratio_bounds"].values())
        + bound["accumulation_log_ratio_bound"]
        + 1e-12
    )
    recovery_pass = (
        recovery["structure_accuracy"] >= 0.85
        and recovery["mean_true_structure_probability"] >= 0.75
        and recovery["structure_brier"] <= 0.20
        and recovery["structure_ece"] <= 0.10
        and recovery["controllability_accuracy"] >= 0.75
        and recovery["broadcast_accuracy"] >= 0.75
        and recovery["policy_parameter_mean_absolute_error"] <= 0.08
        and recovery["policy_parameter_95_interval_coverage"] >= 0.85
    )
    generalization_pass = (
        all(public_generalization["calibration_monotone"].values())
        and public_generalization["surface_incremental_cv_r2"] <= 0.05
        and public_generalization["low_minus_high_control_95_interval"][0]
        >= 0.20
        and public_generalization["low_minus_high_control_95_interval"][1]
        > 0.0
        and public_generalization["step_injection"]["exceedances"] == 0
        and public_generalization["step_injection"]["maximum"]
        <= 0.294529387
    )
    lesion_pass = (
        abs(lesions["controllability_inference"]["lesioned_contrast"])
        <= 0.03
        and lesions["formation_coupling"][
            "lesioned_distance_from_prior"
        ]
        <= 0.08
        and abs(
            lesions["reflexive_broadcast_context"]["lesioned_contrast"]
        )
        <= 0.03
        and v20["passed"]
        and v21["passed"]
        and v221["passed"]
    )
    sensitivity_pass = (
        not include_sensitivity
        or (
            sensitivity["neighborhood_count"] == 32
            and sensitivity["neighborhood_signs_survive"]
            and all(
                item["adaptive_persistence"] > 0
                and all(
                    effect > 0
                    for effect in item["chain_effects"].values()
                )
                for item in sensitivity[
                    "joint_reliability_perturbations"
                ].values()
            )
            and all(
                item["adaptive_persistence"] > 0
                and item["closed_loop_structure_effect"] > 0
                for item in sensitivity[
                    "structure_prior_sensitivity"
                ].values()
            )
        )
    )
    gates = {
        "gate_1_semantic_routes": semantic_pass,
        "gate_2_recovery": recovery_pass,
        "gate_3_direct_composition": (
            _original_gate_3_pass(opened) and generalization_pass
        ),
        "gate_4_selective_lesions": lesion_pass,
        "gate_5_cumulative_regression": (
            v20["passed"]
            and v21["passed"]
            and v221["passed"]
            and sensitivity_pass
            and determinism["scientific_summaries_identical"]
        ),
    }
    return {
        "stage": "V2.3.1",
        "semantic_proofs": semantic,
        "recovery": recovery,
        "open_assays": public_opened,
        "generalization_assay": public_generalization,
        "expanded_step_injection": expanded_step_injection,
        "lesions": lesions,
        "sensitivity": sensitivity,
        "determinism": determinism,
        "v2.0_regression": v20["gates"],
        "v2.1_regression": v21["gates"],
        "v2.2.1_regression": v221["gates"],
        "_artifact_rows": {
            "generalization_calibration": generalization[
                "calibration_per_world"
            ],
            "generalization_paired": generalization["paired_per_world"],
        },
        "gates": gates,
        "passed": all(gates.values()),
    }
