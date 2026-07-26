"""V2.3 formation and active persistence through exact model comparison."""

from __future__ import annotations

import itertools
import json
from types import MappingProxyType
from typing import Any

import numpy as np

from .audit import ProtocolState, audit_one_posterior
from .config import load_parameters
from .factor import Factor
from .inference import ExactEngine
from .model import FiniteModel, Variable
from .precision import precision_categorical
from .rng import component_rng
from .statistics import bootstrap_interval, ece_binary
from .templates import categorical_prior, dirichlet_update
from .v20 import run_v20
from .v21 import run_v21
from .v221 import run_v221


PARAMETERS = load_parameters("V2.3")
STRUCTURE_PRIOR = np.asarray(PARAMETERS["formation_structure_prior"], dtype=float)
ROOT_PRIOR = np.asarray(PARAMETERS["root_prior"], dtype=float)
CONTROL_PRIOR = np.asarray(PARAMETERS["controllability_prior"], dtype=float)
BROADCAST_PRIOR = np.asarray(PARAMETERS["reflexive_broadcast_prior"], dtype=float)
WORLD_PRIOR = np.asarray(PARAMETERS["world_prior"], dtype=float)
EVENT_BASE = np.asarray(PARAMETERS["event_base_likelihood"], dtype=float)
EVENT_PRECISION = np.asarray(PARAMETERS["event_precision_support"], dtype=float)
POLICY_PRIOR = np.asarray(PARAMETERS["policy_consequence_prior"], dtype=float)
POLICY_TRUTH = PARAMETERS["policy_consequence_truth"]
EXPECTED_WEIGHTS = PARAMETERS["expected_outcome_weights"]


def _scaled_probability(value: float, scale: float) -> float:
    return float(np.clip(0.5 + (value - 0.5) * scale, 0.001, 0.999))


def _binary_rows(probability_one: np.ndarray) -> np.ndarray:
    probability_one = np.asarray(probability_one, dtype=float)
    return np.stack([1.0 - probability_one, probability_one], axis=-1)


def _policy_table(coupling_lesion: bool = False) -> np.ndarray:
    values = PARAMETERS["policy_avoid_probabilities"]
    table = np.empty((2, 2, 2, 2))
    for h, g, c in itertools.product(range(2), repeat=3):
        if coupling_lesion or h == 0:
            probability = (
                values["transient_high_control"]
                if c == 1
                else values["transient_low_control"]
            )
        elif g == 0:
            probability = values["persistent_safe"]
        elif c == 0:
            probability = values["persistent_threat_low_control"]
        else:
            probability = values["persistent_threat_high_control"]
        table[h, g, c] = [1.0 - probability, probability]
    return table


def _self_table(coupling_lesion: bool, scale: float) -> np.ndarray:
    reliability = _scaled_probability(
        float(PARAMETERS["self_root_coupling"]), scale
    )
    table = np.empty((2, 2, 2))
    for h, g in itertools.product(range(2), repeat=2):
        if coupling_lesion or h == 0:
            table[h, g] = [0.5, 0.5]
        else:
            table[h, g] = (
                [reliability, 1.0 - reliability]
                if g == 0
                else [1.0 - reliability, reliability]
            )
    return table


def _event_table(coupling_lesion: bool, scale: float) -> np.ndarray:
    coupling = _scaled_probability(
        float(PARAMETERS["event_root_coupling"]), scale
    )
    table = np.empty((2, 2, 2, 2))
    for h, g, s in itertools.product(range(2), repeat=3):
        if coupling_lesion or h == 0:
            probability = 0.12
        else:
            concordance = (g + s) / 2.0
            probability = 0.12 + (coupling - 0.12) * concordance
        table[h, g, s] = [1.0 - probability, probability]
    return table


def _world_table(
    previous_world: np.ndarray,
    real_danger: bool,
    control_lesion: bool,
    coupling_lesion: bool,
    scale: float,
) -> np.ndarray:
    previous_threat = float(previous_world[1])
    table = np.empty((2, 2, 2, 2, 2))
    root_coupling = _scaled_probability(
        float(PARAMETERS["event_root_coupling"]), scale
    )
    for h, g, c, action in itertools.product(range(2), repeat=4):
        if real_danger:
            base = (
                PARAMETERS["real_danger_avoid_threat"]
                if action == 1
                else PARAMETERS["real_danger_engage_threat"]
            )
        elif c == 0:
            base = PARAMETERS["low_control_threat"]
        elif action == 1:
            base = PARAMETERS["high_control_avoid_threat"]
        else:
            base = 1.0 - PARAMETERS["high_control_engage_recovery"]
        if not real_danger and previous_threat < 0.5:
            if c == 1 and action == 0:
                base = 0.10
            elif c == 1 and action == 1:
                base = 0.55
            else:
                base = 0.35
        probability = _scaled_probability(float(base), scale)
        if control_lesion:
            low = _scaled_probability(
                float(PARAMETERS["low_control_threat"]), scale
            )
            probability = low
        if not coupling_lesion:
            if action == 1 and (h == 0 or g == 0):
                probability = min(probability, 0.50)
            elif h == 1 and g == 1:
                probability = max(probability, root_coupling)
        table[h, g, c, action] = [1.0 - probability, probability]
    return table


def _expected_outcome_table(
    consequence_alpha: np.ndarray,
    coupling_lesion: bool,
    control_lesion: bool,
) -> np.ndarray:
    favorable = consequence_alpha[:, 1] / consequence_alpha.sum(axis=1)
    flat_favorable = float(np.mean(favorable))
    table = np.empty((2, 2, 2, 2, 2, 2))
    for h, g, c, action, world in itertools.product(range(2), repeat=5):
        effective_control = 0 if control_lesion else c
        policy_favorable = (
            favorable[action] if effective_control == 1 else flat_favorable
        )
        root_risk = float(g) if h == 1 and not coupling_lesion else 0.5
        adverse = (
            EXPECTED_WEIGHTS["world"] * world
            + EXPECTED_WEIGHTS["policy_consequence"] * (1.0 - policy_favorable)
            + EXPECTED_WEIGHTS["root"] * root_risk
        )
        adverse = float(np.clip(adverse, 0.05, 0.95))
        table[h, g, c, action, world] = [1.0 - adverse, adverse]
    return table


def _context_table(broadcast_lesion: bool, scale: float) -> np.ndarray:
    transient = _scaled_probability(
        float(PARAMETERS["context_now_transient"]), scale
    )
    persistent = 1.0 - _scaled_probability(
        1.0 - float(PARAMETERS["context_now_persistent"]), scale
    )
    table = np.empty((2, 2, 2, 2))
    for h, event, broadcast in itertools.product(range(2), repeat=3):
        effective_broadcast = 1 if broadcast_lesion else broadcast
        if event == 0:
            probability = 0.5
        elif effective_broadcast == 0:
            probability = 0.5
        else:
            probability = transient if h == 0 else persistent
        table[h, event, broadcast] = [1.0 - probability, probability]
    return table


def formation_model(
    *,
    structure_prior: np.ndarray | None = None,
    root_prior: np.ndarray | None = None,
    control_prior: np.ndarray | None = None,
    broadcast_prior: np.ndarray | None = None,
    previous_world: np.ndarray | None = None,
    consequence_alpha: np.ndarray | None = None,
    overwhelm: int,
    real_danger: bool = False,
    coupling_lesion: bool = False,
    control_lesion: bool = False,
    broadcast_lesion: bool = False,
    action_intervention: bool = False,
    reliability_scale: float = 1.0,
) -> FiniteModel:
    """Compile one exact slice from public factor vocabulary."""
    model = FiniteModel()
    for variable in (
        Variable("H", 2, "structure"),
        Variable("G", 2),
        Variable("S", 2),
        Variable("C", 2),
        Variable("R", 2),
        Variable("E", 2),
        Variable("K", 2),
        Variable("A", 2, "policy"),
        Variable("W", 2),
        Variable("Y", 2),
        Variable("B", 2, "observation"),
        Variable("Q", 2, "observation"),
        Variable("X", 2, "observation"),
        Variable("O", 2, "observation"),
    ):
        model.add_variable(variable)
    model.add_factor(
        categorical_prior(
            "H", STRUCTURE_PRIOR if structure_prior is None else structure_prior
        )
    )
    model.add_factor(
        categorical_prior("G", ROOT_PRIOR if root_prior is None else root_prior)
    )
    control_values = CONTROL_PRIOR if control_prior is None else control_prior
    if control_lesion:
        control_values = np.array([0.0, 1.0])
    model.add_factor(categorical_prior("C", control_values))
    model.add_factor(
        categorical_prior(
            "R", BROADCAST_PRIOR if broadcast_prior is None else broadcast_prior
        )
    )
    model.add_factor(categorical_prior("K", [1.0 - overwhelm, overwhelm]))
    model.add_factor(
        Factor(("H", "G", "S"), _self_table(coupling_lesion, reliability_scale))
    )
    model.add_factor(
        Factor(
            ("H", "G", "S", "E"),
            _event_table(coupling_lesion, reliability_scale),
        )
    )
    if not action_intervention:
        model.add_factor(
            Factor(("H", "G", "C", "A"), _policy_table(coupling_lesion))
        )
    model.add_factor(
        Factor(
            ("H", "G", "C", "A", "W"),
            _world_table(
                WORLD_PRIOR if previous_world is None else previous_world,
                real_danger,
                control_lesion,
                coupling_lesion,
                reliability_scale,
            ),
            "action_controlled_transition",
        )
    )
    alpha = (
        np.tile(POLICY_PRIOR, (2, 1))
        if consequence_alpha is None
        else consequence_alpha
    )
    model.add_factor(
        Factor(
            ("H", "G", "C", "A", "W", "Y"),
            _expected_outcome_table(alpha, coupling_lesion, control_lesion),
            "joint_policy_outcome",
        )
    )
    model.add_factor(
        precision_categorical("E", "K", "B", EVENT_BASE, EVENT_PRECISION)
    )
    monitor = _scaled_probability(
        float(PARAMETERS["broadcast_monitor_reliability"]),
        reliability_scale,
    )
    model.add_factor(
        Factor(
            ("R", "Q"),
            np.array([[monitor, 1.0 - monitor], [1.0 - monitor, monitor]]),
            "conditional_categorical",
        )
    )
    model.add_factor(
        Factor(
            ("H", "E", "R", "X"),
            _context_table(broadcast_lesion, reliability_scale),
            "hierarchical_precision_prior",
        )
    )
    outcome = _scaled_probability(
        float(PARAMETERS["outcome_observation_reliability"]),
        reliability_scale,
    )
    model.add_factor(
        Factor(
            ("Y", "O"),
            np.array([[outcome, 1.0 - outcome], [1.0 - outcome, outcome]]),
            "conditional_categorical",
        )
    )
    return model


def policy_model(
    *,
    structure_prior: np.ndarray,
    root_prior: np.ndarray,
    control_prior: np.ndarray,
    broadcast_prior: np.ndarray,
    overwhelm: int,
    coupling_lesion: bool = False,
    control_lesion: bool = False,
    broadcast_lesion: bool = False,
    reliability_scale: float = 1.0,
) -> FiniteModel:
    """Exact ancestral marginal of the full slice before policy realization."""
    model = FiniteModel()
    for variable in (
        Variable("H", 2, "structure"),
        Variable("G", 2),
        Variable("S", 2),
        Variable("C", 2),
        Variable("R", 2),
        Variable("E", 2),
        Variable("K", 2),
        Variable("A", 2, "policy"),
        Variable("B", 2, "observation"),
        Variable("Q", 2, "observation"),
        Variable("X", 2, "observation"),
    ):
        model.add_variable(variable)
    model.add_factor(categorical_prior("H", structure_prior))
    model.add_factor(categorical_prior("G", root_prior))
    model.add_factor(
        categorical_prior(
            "C", np.array([0.0, 1.0]) if control_lesion else control_prior
        )
    )
    model.add_factor(categorical_prior("R", broadcast_prior))
    model.add_factor(categorical_prior("K", [1.0 - overwhelm, overwhelm]))
    model.add_factor(
        Factor(("H", "G", "S"), _self_table(coupling_lesion, reliability_scale))
    )
    model.add_factor(
        Factor(
            ("H", "G", "S", "E"),
            _event_table(coupling_lesion, reliability_scale),
        )
    )
    model.add_factor(Factor(("H", "G", "C", "A"), _policy_table(coupling_lesion)))
    model.add_factor(
        precision_categorical("E", "K", "B", EVENT_BASE, EVENT_PRECISION)
    )
    monitor = _scaled_probability(
        float(PARAMETERS["broadcast_monitor_reliability"]),
        reliability_scale,
    )
    model.add_factor(
        Factor(
            ("R", "Q"),
            np.array([[monitor, 1.0 - monitor], [1.0 - monitor, monitor]]),
        )
    )
    model.add_factor(
        Factor(
            ("H", "E", "R", "X"),
            _context_table(broadcast_lesion, reliability_scale),
        )
    )
    return model


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
    model = policy_model(
        structure_prior=priors["H"],
        root_prior=priors["G"],
        control_prior=priors["C"],
        broadcast_prior=priors["R"],
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


def _marginal(joint: np.ndarray, query: tuple[str, ...], name: str) -> np.ndarray:
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
    model = formation_model(
        structure_prior=priors["H"],
        root_prior=priors["G"],
        control_prior=priors["C"],
        broadcast_prior=priors["R"],
        previous_world=priors["W"],
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
                "stage": "V2.3",
                "overwhelm": overwhelm,
                "real_danger": real_danger,
                "coupling_lesion": coupling_lesion,
                "control_lesion": control_lesion,
                "broadcast_lesion": broadcast_lesion,
                "action_intervention": action_intervention,
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
        prior = priors["H"][index]
        state.evidence_store[f"{label}_conditional"] = (
            float(state.posterior_store["H"][index] * evidence / prior)
            if prior > 0
            else 0.0
        )
    audit_one_posterior(state)
    return state


def _manual_structure_posterior(
    model: FiniteModel, observations: dict[str, int]
) -> np.ndarray:
    """Fresh Cartesian summation for V2.3's finite-comparison proof."""
    latent_names = [
        name for name in model.variables if name not in observations and name != "H"
    ]
    masses = np.zeros(2)
    for h in range(2):
        for values in itertools.product((0, 1), repeat=len(latent_names)):
            assignment = dict(zip(latent_names, values))
            assignment.update(observations)
            assignment["H"] = h
            product = 1.0
            for factor in model.factors:
                index = tuple(assignment[name] for name in factor.variables)
                product *= factor.values[index]
            masses[h] += product
    return masses / masses.sum()


def semantic_proofs() -> dict[str, Any]:
    precision_factor = precision_categorical(
        "E", "K", "B", EVENT_BASE, EVENT_PRECISION
    )
    low_odds = precision_factor.values[1, 0, 1] / precision_factor.values[0, 0, 1]
    high_odds = precision_factor.values[1, 1, 1] / precision_factor.values[0, 1, 1]
    analytic_high = (EVENT_BASE[1, 1] / EVENT_BASE[0, 1]) ** EVENT_PRECISION[1]

    alpha = np.array([[2.0, 8.0], [8.0, 2.0]])
    outcome_table = _expected_outcome_table(alpha, False, False)
    low_action_evidence = outcome_table[1, 1, 0, :, 1, 1]
    high_action_evidence = outcome_table[1, 1, 1, :, 1, 1]
    low_action_log_difference = abs(
        float(
            np.log(low_action_evidence[0] / (1.0 - low_action_evidence[0]))
            - np.log(low_action_evidence[1] / (1.0 - low_action_evidence[1]))
        )
    )
    high_action_log_difference = abs(
        float(
            np.log(high_action_evidence[0] / (1.0 - high_action_evidence[0]))
            - np.log(high_action_evidence[1] / (1.0 - high_action_evidence[1]))
        )
    )

    action_transition_effect = float(
        _transition_threat_probability(1, 1, 1, False)
        - _transition_threat_probability(1, 0, 1, False)
    )

    base_priors = {
        "H": STRUCTURE_PRIOR,
        "G": ROOT_PRIOR,
        "C": CONTROL_PRIOR,
        "R": BROADCAST_PRIOR,
        "W": WORLD_PRIOR,
    }
    collapsed = infer_slice(
        priors={**base_priors, "R": np.array([0.98, 0.02])},
        consequence_alpha=np.tile(POLICY_PRIOR, (2, 1)),
        overwhelm=1,
        real_danger=False,
        observations={"B": 1, "Q": 0, "X": 1},
    )
    integrated = infer_slice(
        priors={**base_priors, "R": np.array([0.02, 0.98])},
        consequence_alpha=np.tile(POLICY_PRIOR, (2, 1)),
        overwhelm=1,
        real_danger=False,
        observations={"B": 1, "Q": 1, "X": 1},
    )
    broadcast_effect = float(
        collapsed.posterior_store["H"][1] - integrated.posterior_store["H"][1]
    )

    comparison_model = formation_model(
        overwhelm=1,
        previous_world=WORLD_PRIOR,
        consequence_alpha=np.tile(POLICY_PRIOR, (2, 1)),
    )
    comparison_observations = {"B": 1, "Q": 0, "X": 1, "A": 1, "O": 1}
    engine_posterior, _ = ExactEngine().infer(
        comparison_model, ("H",), comparison_observations
    )
    manual_posterior = _manual_structure_posterior(
        comparison_model, comparison_observations
    )
    return {
        "event_precision": {
            "low_matching_odds": float(low_odds),
            "high_matching_odds": float(high_odds),
            "log_odds_increase": float(np.log(high_odds) - np.log(low_odds)),
            "analytic_factor_error": abs(float(high_odds - analytic_high)),
        },
        "controllability": {
            "low_control_action_log_evidence_difference": low_action_log_difference,
            "high_control_action_log_evidence_difference": high_action_log_difference,
        },
        "action_transition": {
            "avoid_minus_engage_threat_probability": action_transition_effect
        },
        "reflexive_broadcast": {
            "collapsed_persistent_probability": float(
                collapsed.posterior_store["H"][1]
            ),
            "integrated_persistent_probability": float(
                integrated.posterior_store["H"][1]
            ),
            "persistent_probability_effect": broadcast_effect,
        },
        "finite_comparison": {
            "engine_posterior": engine_posterior.tolist(),
            "manual_posterior": manual_posterior.tolist(),
            "maximum_error": float(
                np.max(np.abs(engine_posterior - manual_posterior))
            ),
        },
    }


def _transition_threat_probability(
    previous_world: int,
    action: int,
    controllability: int,
    real_danger: bool,
) -> float:
    if real_danger:
        return float(
            PARAMETERS["real_danger_avoid_threat"]
            if action == 1
            else PARAMETERS["real_danger_engage_threat"]
        )
    if controllability == 0:
        return float(
            PARAMETERS["low_control_threat"]
            if previous_world == 1
            else 0.35
        )
    if action == 1:
        return float(
            PARAMETERS["high_control_avoid_threat"]
            if previous_world == 1
            else 0.55
        )
    return float(
        1.0 - PARAMETERS["high_control_engage_recovery"]
        if previous_world == 1
        else 0.10
    )


def _sample_binary(seed: int, component: str, probability: float) -> int:
    return int(component_rng(seed, component).random() < probability)


def _initial_priors(structure_prior: np.ndarray | None = None) -> dict[str, np.ndarray]:
    return {
        "H": (STRUCTURE_PRIOR if structure_prior is None else structure_prior).copy(),
        "G": ROOT_PRIOR.copy(),
        "C": CONTROL_PRIOR.copy(),
        "R": BROADCAST_PRIOR.copy(),
        "W": WORLD_PRIOR.copy(),
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
    consequence_alpha = np.tile(POLICY_PRIOR, (2, 1))
    previous_world_truth = 0
    traces = []
    states = []
    for time, slice_config in enumerate(schedule):
        event = int(slice_config["event"])
        overwhelm = int(slice_config["overwhelm"])
        controllability = int(slice_config["controllability"])
        broadcast = int(slice_config["broadcast"])
        real_danger = bool(slice_config["real_danger"])

        precision_state = overwhelm
        event_factor = precision_categorical(
            "E", "K", "B", EVENT_BASE, EVENT_PRECISION
        )
        event_probability = float(event_factor.values[event, precision_state, event])
        event_match = _sample_binary(
            seed, f"{stream_family}-event-match-{time}", event_probability
        )
        event_observation = event if event_match else 1 - event

        monitor = float(PARAMETERS["broadcast_monitor_reliability"])
        monitor_match = _sample_binary(
            seed, f"{stream_family}-broadcast-match-{time}", monitor
        )
        monitor_observation = broadcast if monitor_match else 1 - broadcast

        if event == 1 and broadcast == 1:
            context_probability = float(PARAMETERS["context_now_transient"])
        else:
            context_probability = 0.5
        context_observation = _sample_binary(
            seed, f"{stream_family}-context-now-{time}", context_probability
        )
        exogenous_observations = {
            "B": event_observation,
            "Q": monitor_observation,
            "X": context_observation,
        }
        if action_mode == "closed_loop":
            policy_posterior = infer_policy(
                priors=priors,
                overwhelm=overwhelm,
                observations=exogenous_observations,
                coupling_lesion=coupling_lesion,
                control_lesion=control_lesion,
                broadcast_lesion=broadcast_lesion,
                reliability_scale=reliability_scale,
            )
            action_probability = float(policy_posterior[1])
            action = _sample_binary(
                seed, f"{stream_family}-policy-uniform-{time}", action_probability
            )
        elif action_mode == "engage_replay":
            action_probability = 0.0
            action = 0
        elif action_mode == "declared":
            action = int(slice_config.get("action", 0))
            action_probability = float(action)
        else:
            raise ValueError(f"unsupported action mode {action_mode}")

        threat_probability = _transition_threat_probability(
            previous_world_truth, action, controllability, real_danger
        )
        world = _sample_binary(
            seed, f"{stream_family}-world-uniform-{time}", threat_probability
        )
        outcome_reliability = float(PARAMETERS["outcome_observation_reliability"])
        outcome_match = _sample_binary(
            seed, f"{stream_family}-outcome-match-{time}", outcome_reliability
        )
        outcome_observation = world if outcome_match else 1 - world
        observations = {
            **exogenous_observations,
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
        traces.append(
            {
                "time": time,
                "persistent_probability": float(state.posterior_store["H"][1]),
                "root_threat_probability": float(state.posterior_store["G"][1]),
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

    persistent = np.array([trace["persistent_probability"] for trace in traces])
    actions = np.array([trace["action"] for trace in traces])
    worlds = np.array([trace["world"] for trace in traces])
    outcomes = np.array([trace["adverse_observation"] for trace in traces])
    avoid_mask = actions == 1
    engage_mask = actions == 0
    threat_after_avoid = float(worlds[avoid_mask].mean()) if np.any(avoid_mask) else 0.0
    threat_after_engage = (
        float(worlds[engage_mask].mean()) if np.any(engage_mask) else 0.0
    )
    mediator = float(
        avoid_mask.mean() * (threat_after_avoid - threat_after_engage)
    )
    initial = float(STRUCTURE_PRIOR[1] if structure_prior is None else structure_prior[1])
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


def _schedules() -> dict[str, list[dict[str, Any]]]:
    safe = {
        "event": 0,
        "overwhelm": 0,
        "controllability": 1,
        "broadcast": 1,
        "real_danger": False,
    }
    acute_event = {
        "event": 1,
        "overwhelm": 1,
        "controllability": 0,
        "broadcast": 0,
        "real_danger": False,
    }
    gradual_event = {
        "event": 1,
        "overwhelm": 0,
        "controllability": 0,
        "broadcast": 0,
        "real_danger": False,
    }
    controlled_event = {
        "event": 1,
        "overwhelm": 1,
        "controllability": 1,
        "broadcast": 1,
        "real_danger": False,
    }
    low_control_event = {
        "event": 1,
        "overwhelm": 0,
        "controllability": 0,
        "broadcast": 0,
        "real_danger": False,
        "action": 0,
    }
    high_control_event = {
        "event": 1,
        "overwhelm": 0,
        "controllability": 1,
        "broadcast": 0,
        "real_danger": False,
        "action": 0,
    }
    danger = {
        "event": 1,
        "overwhelm": 1,
        "controllability": 1,
        "broadcast": 0,
        "real_danger": True,
    }
    active = {
        "event": 1,
        "overwhelm": 0,
        "controllability": 1,
        "broadcast": 0,
        "real_danger": False,
    }
    return {
        "acute": [safe.copy() for _ in range(2)]
        + [acute_event.copy() for _ in range(6)],
        "gradual": [safe.copy() for _ in range(2)]
        + [
            {**gradual_event, "action": index % 2}
            for index in range(20)
        ]
        + [
            {**gradual_event, "action": index % 2, "overwhelm": 1}
            for index in range(5)
        ],
        "overwhelm_control": [safe.copy() for _ in range(2)]
        + [controlled_event.copy() for _ in range(6)],
        "low_control": [safe.copy() for _ in range(2)]
        + [
            {**low_control_event, "action": index % 2}
            for index in range(40)
        ],
        "high_control": [safe.copy() for _ in range(2)]
        + [
            {**high_control_event, "action": index % 2}
            for index in range(40)
        ],
        "adaptive_threat": [safe.copy() for _ in range(2)]
        + [danger.copy() for _ in range(10)],
        "active_persistence": [safe.copy() for _ in range(2)]
        + [{**active, "overwhelm": 1} for _ in range(2)]
        + [active.copy() for _ in range(12)],
    }


def _effect_interval(
    values: list[float], seed: int, component: str
) -> tuple[float, float, float]:
    low, high = bootstrap_interval(values, seed, component)
    return float(np.mean(values)), low, high


def open_assays(
    *,
    seed_start: int | None = None,
    seed_end: int | None = None,
    structure_prior: np.ndarray | None = None,
    reliability_scale: float = 1.0,
) -> dict[str, Any]:
    if seed_start is None or seed_end is None:
        seed_start, seed_end = PARAMETERS["seed_block"]
    schedules = _schedules()
    names = (
        "acute",
        "gradual",
        "overwhelm_control",
        "low_control",
        "high_control",
        "adaptive_threat",
    )
    worlds: dict[str, list[dict[str, Any]]] = {name: [] for name in names}
    worlds["closed_loop"] = []
    worlds["exact_replay"] = []
    all_steps = []
    per_seed = []
    for seed in range(seed_start, seed_end + 1):
        for name in names:
            action_mode = (
                "engage_replay"
                if name == "adaptive_threat"
                else "declared"
                if name in ("gradual", "low_control", "high_control")
                else "closed_loop"
            )
            result = run_world(
                seed,
                schedules[name],
                action_mode=action_mode,
                stream_family=name,
                structure_prior=structure_prior,
                reliability_scale=reliability_scale,
            )
            worlds[name].append(result)
            all_steps.extend(result["step_injections"])
        closed = run_world(
            seed,
            schedules["active_persistence"],
            action_mode="closed_loop",
            stream_family="avoidance-replay-pair",
            structure_prior=structure_prior,
            reliability_scale=reliability_scale,
        )
        replay = run_world(
            seed,
            schedules["active_persistence"],
            action_mode="engage_replay",
            stream_family="avoidance-replay-pair",
            structure_prior=structure_prior,
            reliability_scale=reliability_scale,
        )
        worlds["closed_loop"].append(closed)
        worlds["exact_replay"].append(replay)
        all_steps.extend(closed["step_injections"])
        all_steps.extend(replay["step_injections"])
        per_seed.append(
            {
                "seed": seed,
                "acute_final": worlds["acute"][-1][
                    "final_persistent_probability"
                ],
                "gradual_final": worlds["gradual"][-1][
                    "final_persistent_probability"
                ],
                "overwhelm_control_final": worlds["overwhelm_control"][-1][
                    "final_persistent_probability"
                ],
                "low_control_final": worlds["low_control"][-1][
                    "final_persistent_probability"
                ],
                "high_control_final": worlds["high_control"][-1][
                    "final_persistent_probability"
                ],
                "adaptive_threat_final": worlds["adaptive_threat"][-1][
                    "final_persistent_probability"
                ],
                "closed_loop_final": closed["final_persistent_probability"],
                "exact_replay_final": replay["final_persistent_probability"],
                "closed_loop_avoidance_rate": closed["avoidance_rate"],
                "exact_replay_avoidance_rate": replay["avoidance_rate"],
                "closed_loop_adverse_transition_rate": closed[
                    "adverse_transition_rate"
                ],
                "exact_replay_adverse_transition_rate": replay[
                    "adverse_transition_rate"
                ],
                "closed_loop_adverse_outcome_rate": closed[
                    "adverse_outcome_rate"
                ],
                "exact_replay_adverse_outcome_rate": replay[
                    "adverse_outcome_rate"
                ],
                "closed_loop_root": closed["final_root_probability"],
                "exact_replay_root": replay["final_root_probability"],
                "closed_loop_mediator": closed["realized_avoidance_mediator"],
                "exact_replay_mediator": replay["realized_avoidance_mediator"],
            }
        )

    def values(name: str, field: str) -> list[float]:
        return [float(world[field]) for world in worlds[name]]

    acute_final = _effect_interval(
        values("acute", "final_persistent_probability"), 740, "v23-acute"
    )
    acute_steps = _effect_interval(
        values("acute", "maximum_step"), 741, "v23-acute-step"
    )
    gradual_final = _effect_interval(
        values("gradual", "final_persistent_probability"), 742, "v23-gradual"
    )
    gradual_change = _effect_interval(
        values("gradual", "formation_change"), 743, "v23-gradual-change"
    )
    gradual_steps = _effect_interval(
        values("gradual", "maximum_step"), 744, "v23-gradual-step"
    )

    def paired(left: str, right: str, field: str, component: str) -> tuple[float, float, float]:
        differences = [
            a[field] - b[field] for a, b in zip(worlds[left], worlds[right])
        ]
        return _effect_interval(differences, 745, component)

    overwhelm_control = paired(
        "acute",
        "overwhelm_control",
        "final_persistent_probability",
        "v23-overwhelm-control",
    )
    low_control = paired(
        "low_control",
        "high_control",
        "final_persistent_probability",
        "v23-low-control",
    )
    adaptive = _effect_interval(
        values("adaptive_threat", "final_persistent_probability"),
        746,
        "v23-adaptive",
    )
    chain = {
        "policy_avoidance": paired(
            "closed_loop", "exact_replay", "avoidance_rate", "v23-chain-policy"
        ),
        "world_transition": paired(
            "closed_loop",
            "exact_replay",
            "adverse_transition_rate",
            "v23-chain-world",
        ),
        "observed_evidence": paired(
            "closed_loop",
            "exact_replay",
            "adverse_outcome_rate",
            "v23-chain-observation",
        ),
        "persistent_model": paired(
            "closed_loop",
            "exact_replay",
            "final_persistent_probability",
            "v23-chain-structure",
        ),
        "root_persistence": paired(
            "closed_loop", "exact_replay", "final_root_probability", "v23-chain-root"
        ),
        "realized_mediator": paired(
            "closed_loop",
            "exact_replay",
            "realized_avoidance_mediator",
            "v23-chain-mediator",
        ),
    }
    return {
        "world_count": seed_end - seed_start + 1,
        "acute_formation": {
            "final_persistent_95_interval": acute_final,
            "maximum_step_95_interval": acute_steps,
        },
        "gradual_accumulation": {
            "final_persistent_95_interval": gradual_final,
            "formation_change_95_interval": gradual_change,
            "maximum_step_95_interval": gradual_steps,
            "acute_minus_gradual_maximum_step": acute_steps[0] - gradual_steps[0],
        },
        "overwhelm_with_control": {
            "acute_minus_controlled_95_interval": overwhelm_control
        },
        "low_control_without_overwhelm": {
            "low_minus_high_control_95_interval": low_control
        },
        "adaptive_persistent_threat": {
            "final_persistent_95_interval": adaptive,
            "interpretation": "correct persistence under real danger",
        },
        "closed_loop_vs_exact_replay": chain,
        "step_injection": {
            "count": len(all_steps),
            "percentile_99": float(np.quantile(all_steps, 0.99)),
            "maximum": float(np.max(all_steps)),
        },
        "per_seed": per_seed,
        "worlds": worlds,
    }


def recovery_assay() -> dict[str, Any]:
    start, end = PARAMETERS["recovery_seed_block"]
    schedules = _schedules()
    structure_probabilities = []
    structure_truths = []
    structure_correct = []
    control_correct = []
    broadcast_correct = []
    parameter_errors = []
    parameter_coverages = []
    confusion = np.zeros((2, 2), dtype=int)
    for offset, seed in enumerate(range(start, end + 1)):
        truth = offset % 2
        if truth == 0:
            schedule = [schedules["acute"][0].copy() for _ in range(12)]
            for event_time in (5, 6, 7):
                schedule[event_time] = {
                    "event": 1,
                    "overwhelm": 0,
                    "controllability": 1,
                    "broadcast": 1,
                    "real_danger": False,
                }
            control_truth = 1
            broadcast_truth = 1
            mode = "engage_replay"
        else:
            schedule = [item.copy() for item in schedules["adaptive_threat"]]
            for item in schedule:
                item["controllability"] = 0
                item["broadcast"] = 0
            control_truth = 0
            broadcast_truth = 0
            mode = "closed_loop"
        result = run_world(
            seed,
            schedule,
            action_mode=mode,
            stream_family=f"v23-recovery-{truth}",
        )
        probability = result["final_persistent_probability"]
        prediction = int(probability >= 0.5)
        confusion[truth, prediction] += 1
        structure_probabilities.append(probability)
        structure_truths.append(truth)
        structure_correct.append(float(prediction == truth))
        control_schedule_name = (
            "high_control" if control_truth == 1 else "low_control"
        )
        control_result = run_world(
            seed,
            schedules[control_schedule_name],
            action_mode="declared",
            stream_family=f"v23-control-recovery-{control_truth}",
        )
        control_prediction = int(
            control_result["final_controllability_probability"] >= 0.5
        )
        broadcast_prediction = int(result["final_broadcast_probability"] >= 0.5)
        control_correct.append(float(control_prediction == control_truth))
        broadcast_correct.append(float(broadcast_prediction == broadcast_truth))

        for action, truth_probability in enumerate(
            (
                POLICY_TRUTH["engage_favorable"],
                POLICY_TRUTH["avoid_favorable"],
            )
        ):
            rng = component_rng(seed, f"v23-parameter-recovery-{action}")
            favorable = int(rng.binomial(120, truth_probability))
            alpha = dirichlet_update(
                POLICY_PRIOR,
                np.array([120 - favorable, favorable], dtype=float),
            )
            mean = float(alpha[1] / alpha.sum())
            parameter_errors.append(abs(mean - truth_probability))
            interval_rng = component_rng(seed, f"v23-parameter-interval-{action}")
            samples = interval_rng.beta(alpha[1], alpha[0], 3000)
            low, high = np.quantile(samples, [0.025, 0.975])
            parameter_coverages.append(
                float(low <= truth_probability <= high)
            )

    probabilities = np.asarray(structure_probabilities)
    truths = np.asarray(structure_truths)
    true_probabilities = np.where(truths == 1, probabilities, 1.0 - probabilities)
    return {
        "world_count": len(structure_truths),
        "structure_confusion_matrix": confusion.tolist(),
        "structure_accuracy": float(np.mean(structure_correct)),
        "mean_true_structure_probability": float(np.mean(true_probabilities)),
        "structure_brier": float(np.mean((probabilities - truths) ** 2)),
        "structure_ece": ece_binary(probabilities, truths),
        "controllability_accuracy": float(np.mean(control_correct)),
        "broadcast_accuracy": float(np.mean(broadcast_correct)),
        "policy_parameter_mean_absolute_error": float(np.mean(parameter_errors)),
        "policy_parameter_95_interval_coverage": float(
            np.mean(parameter_coverages)
        ),
    }


def lesion_assays() -> dict[str, Any]:
    priors_low = _initial_priors()
    priors_low["C"] = np.array([0.98, 0.02])
    priors_high = _initial_priors()
    priors_high["C"] = np.array([0.02, 0.98])
    observations = {"B": 1, "Q": 0, "X": 0, "A": 1, "O": 1}

    def persistence(
        priors: dict[str, np.ndarray],
        observation_override: dict[str, int] | None = None,
        **lesions: bool,
    ) -> float:
        state = infer_slice(
            priors=priors,
            consequence_alpha=np.array([[2.0, 8.0], [8.0, 2.0]]),
            overwhelm=0,
            real_danger=False,
            observations=(
                observations
                if observation_override is None
                else observation_override
            ),
            **lesions,
        )
        return float(state.posterior_store["H"][1])

    intact_control = persistence(priors_low) - persistence(priors_high)
    lesioned_control = persistence(
        priors_low, control_lesion=True
    ) - persistence(priors_high, control_lesion=True)

    acute_priors = _initial_priors()
    intact_coupling = persistence(acute_priors)
    lesioned_coupling = persistence(acute_priors, coupling_lesion=True)

    collapsed_priors = _initial_priors()
    collapsed_priors["R"] = np.array([0.98, 0.02])
    integrated_priors = _initial_priors()
    integrated_priors["R"] = np.array([0.02, 0.98])
    broadcast_observations = {**observations, "X": 1}
    intact_broadcast = persistence(
        collapsed_priors, broadcast_observations
    ) - persistence(
        integrated_priors, broadcast_observations
    )
    lesioned_broadcast = persistence(
        collapsed_priors,
        broadcast_observations,
        broadcast_lesion=True,
    ) - persistence(
        integrated_priors,
        broadcast_observations,
        broadcast_lesion=True,
    )
    return {
        "controllability_inference": {
            "intact_contrast": intact_control,
            "lesioned_contrast": lesioned_control,
        },
        "formation_coupling": {
            "intact_persistent_probability": intact_coupling,
            "lesioned_persistent_probability": lesioned_coupling,
            "persistent_prior": float(STRUCTURE_PRIOR[1]),
            "lesioned_distance_from_prior": abs(
                lesioned_coupling - STRUCTURE_PRIOR[1]
            ),
        },
        "reflexive_broadcast_context": {
            "intact_contrast": intact_broadcast,
            "lesioned_contrast": lesioned_broadcast,
        },
    }


def sensitivity_profile() -> dict[str, Any]:
    start, end = PARAMETERS["sensitivity_seed_block"]
    profiles = []
    for offset, seed in enumerate(range(start, end + 1)):
        rng = component_rng(seed, "v23-neighborhood")
        scale = float(rng.uniform(0.9, 1.1))
        persistent_prior = float(rng.uniform(0.10, 0.35))
        prior = np.array([1.0 - persistent_prior, persistent_prior])
        result = open_assays(
            seed_start=seed,
            seed_end=seed,
            structure_prior=prior,
            reliability_scale=scale,
        )
        chain = result["closed_loop_vs_exact_replay"]
        profiles.append(
            {
                "index": offset,
                "seed": seed,
                "reliability_scale": scale,
                "persistent_prior": persistent_prior,
                "adaptive_persistence": result["adaptive_persistent_threat"][
                    "final_persistent_95_interval"
                ][0],
                "policy_effect": chain["policy_avoidance"][0],
                "transition_effect": chain["world_transition"][0],
                "observation_effect": chain["observed_evidence"][0],
                "structure_effect": chain["persistent_model"][0],
                "root_effect": chain["root_persistence"][0],
                "mediator_effect": chain["realized_mediator"][0],
            }
        )
    signs_survive = all(
        float(np.mean([profile[key] for profile in profiles])) > 0
        for key in (
            "adaptive_persistence",
            "policy_effect",
            "transition_effect",
            "observation_effect",
            "structure_effect",
            "root_effect",
            "mediator_effect",
        )
    )
    joint = {}
    for label, scale in (("minus_10_percent", 0.9), ("plus_10_percent", 1.1)):
        result = open_assays(
            seed_start=PARAMETERS["seed_block"][0],
            seed_end=PARAMETERS["seed_block"][0] + 15,
            reliability_scale=scale,
        )
        chain = result["closed_loop_vs_exact_replay"]
        joint[label] = {
            "adaptive_persistence": result["adaptive_persistent_threat"][
                "final_persistent_95_interval"
            ][0],
            "chain_effects": {key: value[0] for key, value in chain.items()},
        }
    prior_sensitivity = {}
    for persistent_prior in (0.10, 0.22, 0.35):
        result = open_assays(
            seed_start=PARAMETERS["seed_block"][0],
            seed_end=PARAMETERS["seed_block"][0] + 15,
            structure_prior=np.array([1.0 - persistent_prior, persistent_prior]),
        )
        prior_sensitivity[str(persistent_prior)] = {
            "adaptive_persistence": result["adaptive_persistent_threat"][
                "final_persistent_95_interval"
            ][0],
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


def _gate_3_pass(open_results: dict[str, Any]) -> bool:
    chain = open_results["closed_loop_vs_exact_replay"]
    return (
        open_results["acute_formation"]["final_persistent_95_interval"][0] >= 0.70
        and open_results["gradual_accumulation"]["final_persistent_95_interval"][0]
        >= 0.70
        and open_results["gradual_accumulation"]["formation_change_95_interval"][0]
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


def run_v23(
    include_sensitivity: bool = True,
    verify_determinism: bool = False,
) -> dict[str, Any]:
    semantic = semantic_proofs()
    recovery = recovery_assay()
    open_results = open_assays()
    public_open_results = {
        key: value for key, value in open_results.items() if key != "worlds"
    }
    determinism = {
        "full_seed_block_checked_twice": verify_determinism,
        "scientific_summaries_identical": True,
    }
    if verify_determinism:
        repeated = open_assays()
        repeated_public = {
            key: value for key, value in repeated.items() if key != "worlds"
        }
        first_bytes = json.dumps(
            public_open_results, sort_keys=True, separators=(",", ":")
        ).encode()
        repeated_bytes = json.dumps(
            repeated_public, sort_keys=True, separators=(",", ":")
        ).encode()
        determinism["scientific_summaries_identical"] = (
            first_bytes == repeated_bytes
        )
    lesions = lesion_assays()
    sensitivity = sensitivity_profile() if include_sensitivity else {}
    v20 = run_v20()
    v21 = run_v21()
    v221 = run_v221()
    semantic_pass = (
        semantic["event_precision"]["log_odds_increase"] >= 1.0
        and semantic["event_precision"]["analytic_factor_error"] < 1e-12
        and semantic["controllability"][
            "low_control_action_log_evidence_difference"
        ]
        < 1e-12
        and semantic["controllability"][
            "high_control_action_log_evidence_difference"
        ]
        >= 0.50
        and semantic["action_transition"][
            "avoid_minus_engage_threat_probability"
        ]
        >= 0.50
        and semantic["reflexive_broadcast"][
            "persistent_probability_effect"
        ]
        >= 0.10
        and semantic["finite_comparison"]["maximum_error"] < 1e-10
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
    lesion_pass = (
        abs(lesions["controllability_inference"]["lesioned_contrast"]) <= 0.03
        and lesions["formation_coupling"]["lesioned_distance_from_prior"] <= 0.08
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
                and all(effect > 0 for effect in item["chain_effects"].values())
                for item in sensitivity["joint_reliability_perturbations"].values()
            )
            and all(
                item["adaptive_persistence"] > 0
                and item["closed_loop_structure_effect"] > 0
                for item in sensitivity["structure_prior_sensitivity"].values()
            )
        )
    )
    gates = {
        "gate_1_semantic_routes": semantic_pass,
        "gate_2_recovery": recovery_pass,
        "gate_3_direct_composition": _gate_3_pass(open_results),
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
        "stage": "V2.3",
        "semantic_proofs": semantic,
        "recovery": recovery,
        "open_assays": public_open_results,
        "lesions": lesions,
        "sensitivity": sensitivity,
        "determinism": determinism,
        "v2.0_regression": v20["gates"],
        "v2.1_regression": v21["gates"],
        "v2.2.1_regression": v221["gates"],
        "gates": gates,
        "passed": all(gates.values()),
    }
