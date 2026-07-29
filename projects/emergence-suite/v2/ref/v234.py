"""V2.3.4 exact counterfactual action-attribution reference."""

from __future__ import annotations

import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Sequence

import numpy as np

from .audit import ProtocolState, audit_one_posterior
from .rng import component_rng


ROOT = Path(__file__).resolve().parents[1]
PARAMETERS = json.loads(
    (ROOT / "protocols" / "v2.3.4-parameters.json").read_text()
)
THETA = np.asarray(PARAMETERS["theta_support"], dtype=float)
ETA = np.asarray(PARAMETERS["eta_support"], dtype=float)
THETA_PRIOR = np.asarray(PARAMETERS["theta_prior"], dtype=float)
TOLERANCE = float(PARAMETERS["semantic_tolerance"])
EPOCH_B_DEVELOPMENT_BLOCK = tuple(PARAMETERS["epoch_b_development_block"])
ACTIONS = {"engage": 0, "protect": 1}

CONFIGS = tuple(itertools.product(range(len(ETA)), repeat=2))
CONFIG_INDEX = {item: index for index, item in enumerate(CONFIGS)}
_base = np.asarray(PARAMETERS["eta_slab_base_weights"], dtype=float)
_config_base = np.asarray([_base[left] * _base[right] for left, right in CONFIGS])
_config_base[CONFIG_INDEX[(0, 0)]] = 0.0
CONFIG_PRIOR = _config_base / _config_base.sum()
CONFIG_PRIOR *= 1.0 - float(PARAMETERS["irrelevant_spike_prior"])
CONFIG_PRIOR[CONFIG_INDEX[(0, 0)]] = float(
    PARAMETERS["irrelevant_spike_prior"]
)
JOINT_PRIOR = (THETA_PRIOR[:, None] * CONFIG_PRIOR[None, :]).reshape(-1)
STATE_THETA = np.repeat(THETA, len(CONFIGS))
STATE_ETA0 = np.tile(np.asarray([ETA[item[0]] for item in CONFIGS]), len(THETA))
STATE_ETA1 = np.tile(np.asarray([ETA[item[1]] for item in CONFIGS]), len(THETA))
STATE_CAUSAL = ((STATE_ETA0 > 0) | (STATE_ETA1 > 0)).astype(int)


@dataclass(frozen=True)
class Episode:
    action: int
    context: int
    outcome: int | None
    near_miss: int | None = None
    efficacy_observation: int | None = None
    relief: int | None = None


@dataclass(frozen=True)
class AttributionWorld:
    seed: int
    theta_index: int
    eta_indices: tuple[int, int]
    episodes: tuple[Episode, ...]
    identifiable: bool


@dataclass(frozen=True)
class AttributionScore:
    posterior: np.ndarray
    trajectory: tuple[np.ndarray, ...]
    threat_probability: float
    efficacy_causal_probability: float
    eta_mean: tuple[float, float]
    theta_eta_correlation: tuple[float, float]
    prevented_probability_K: tuple[float, ...]
    policy_probability: float
    formation_probability: float
    log_evidence: float
    state: ProtocolState


def _rng(
    seed: int,
    component: str,
    released_block: tuple[int, int] | None = None,
) -> np.random.Generator:
    return component_rng(
        seed,
        component,
        released_block=(
            EPOCH_B_DEVELOPMENT_BLOCK
            if released_block is None
            else released_block
        ),
    )


def _normalize(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    total = float(array.sum())
    if total <= 0.0:
        raise ValueError("zero posterior mass")
    return array / total


def _reliability(name: str, precision: float) -> float:
    declared = float(PARAMETERS[name])
    return 0.5 + float(precision) * (declared - 0.5)


def _binary_probability(observed: int | None, truth: int, reliability: float) -> float:
    if observed is None:
        return 1.0
    return reliability if int(observed) == int(truth) else 1.0 - reliability


def slice_likelihood(
    episode: Episode,
    *,
    force_action_irrelevant: bool = False,
    remove_context_specificity: bool = False,
    broadcast_precision: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Return exact candidate likelihood and conditional K probability."""
    likelihood = np.zeros(len(JOINT_PRIOR), dtype=float)
    k_numerator = np.zeros(len(JOINT_PRIOR), dtype=float)
    outcome_rel = _reliability("outcome_reliability", broadcast_precision)
    danger_rel = _reliability(
        "danger_diagnostic_reliability", broadcast_precision
    )
    efficacy_rel = _reliability(
        "efficacy_diagnostic_reliability", broadcast_precision
    )
    for state in range(len(JOINT_PRIOR)):
        theta = float(STATE_THETA[state])
        eta = (
            float(STATE_ETA0[state])
            if remove_context_specificity or episode.context == 0
            else float(STATE_ETA1[state])
        )
        if force_action_irrelevant:
            eta = 0.0
        total = 0.0
        k_mass = 0.0
        for danger, prevented in itertools.product((0, 1), repeat=2):
            pd = theta if danger else 1.0 - theta
            can_prevent = episode.action == ACTIONS["protect"]
            pp = (
                eta if prevented else 1.0 - eta
            ) if can_prevent else float(prevented == 0)
            realized = danger * (1 - int(can_prevent) * prevented)
            probability = (
                pd
                * pp
                * _binary_probability(
                    episode.outcome, realized, outcome_rel
                )
                * _binary_probability(
                    episode.near_miss, danger, danger_rel
                )
                * _binary_probability(
                    episode.efficacy_observation,
                    prevented,
                    efficacy_rel,
                )
            )
            total += probability
            if (
                danger == 1
                and can_prevent
                and prevented == 1
                and realized == 0
            ):
                k_mass += probability
        likelihood[state] = total
        k_numerator[state] = k_mass
    conditional_k = np.divide(
        k_numerator,
        likelihood,
        out=np.zeros_like(k_numerator),
        where=likelihood > 0,
    )
    return likelihood, conditional_k


def _correlation(q: np.ndarray, context: int) -> float:
    eta = STATE_ETA0 if context == 0 else STATE_ETA1
    theta_mean = float(q @ STATE_THETA)
    eta_mean = float(q @ eta)
    covariance = float(q @ ((STATE_THETA - theta_mean) * (eta - eta_mean)))
    theta_sd = math.sqrt(float(q @ (STATE_THETA - theta_mean) ** 2))
    eta_sd = math.sqrt(float(q @ (eta - eta_mean) ** 2))
    return 0.0 if theta_sd * eta_sd <= 1e-15 else covariance / (theta_sd * eta_sd)


def score(
    episodes: Iterable[Episode],
    *,
    initial_prior: Sequence[float] | None = None,
    lesions: Sequence[str] = (),
    evidence_precision: float = 1.0,
) -> AttributionScore:
    sequence = tuple(episodes)
    lesion_set = set(lesions)
    q = _normalize(
        JOINT_PRIOR.copy()
        if initial_prior is None
        else np.asarray(initial_prior, dtype=float).copy()
    )
    if "efficacy_existence" in lesion_set:
        q[STATE_CAUSAL == 0] = 0.0
        q = _normalize(q)
    trajectory = [q.copy()]
    k_values: list[float] = []
    log_evidence = 0.0
    policy = np.asarray(PARAMETERS["policy_prior"], dtype=float).copy()
    for episode in sequence:
        likelihood, conditional_k = slice_likelihood(
            episode,
            force_action_irrelevant=("action_relevance" in lesion_set),
            remove_context_specificity=(
                "context_specificity" in lesion_set
            ),
            broadcast_precision=(
                0.0 if "broadcast" in lesion_set else float(evidence_precision)
            ),
        )
        evidence = float(q @ likelihood)
        k_values.append(float((q * likelihood) @ conditional_k / evidence))
        q = q * likelihood / evidence
        trajectory.append(q.copy())
        log_evidence += math.log(evidence)
        if episode.relief is not None and "relief" not in lesion_set:
            policy[int(episode.relief)] += 1.0
    threat = float(q @ STATE_THETA)
    causal = float(q @ STATE_CAUSAL)
    eta_means = (float(q @ STATE_ETA0), float(q @ STATE_ETA1))
    formation = (
        float(THETA_PRIOR @ THETA)
        if "formation_coupling" in lesion_set
        else threat
    )
    state = ProtocolState(
        posterior_store={"theta_eta": q.copy()},
        parameter_posterior_store={"policy_relief_beta": policy.copy()},
        evidence_store={
            "attribution_model": math.exp(max(log_evidence, -700.0))
        },
        metadata=MappingProxyType(
            {
                "stage": "V2.3.4",
                "action_selection_likelihood": False,
                "lesion_count": len(lesion_set),
                "evidence_precision": float(evidence_precision),
            }
        ),
    )
    audit_one_posterior(state)
    return AttributionScore(
        posterior=q,
        trajectory=tuple(trajectory),
        threat_probability=threat,
        efficacy_causal_probability=causal,
        eta_mean=eta_means,
        theta_eta_correlation=(_correlation(q, 0), _correlation(q, 1)),
        prevented_probability_K=tuple(k_values),
        policy_probability=float(policy[1] / policy.sum()),
        formation_probability=formation,
        log_evidence=log_evidence,
        state=state,
    )


def _sample_truth(
    seed: int,
    released_block: tuple[int, int] | None,
) -> tuple[int, tuple[int, int]]:
    rng = _rng(seed, "v234-truth", released_block)
    flat = int(rng.choice(len(JOINT_PRIOR), p=JOINT_PRIOR))
    theta_index = flat // len(CONFIGS)
    config = CONFIGS[flat % len(CONFIGS)]
    return theta_index, config


def generate_world(
    seed: int,
    *,
    identifiable: bool,
    length: int | None = None,
    theta_index: int | None = None,
    eta_indices: tuple[int, int] | None = None,
    masking: float = 0.0,
    probe_frequency: float | None = None,
    relief_probability: float = 0.5,
    released_block: tuple[int, int] | None = None,
) -> AttributionWorld:
    """Sample parameters and episodes from the exact frozen scorer process."""
    sampled_theta, sampled_eta = _sample_truth(seed, released_block)
    truth_theta = sampled_theta if theta_index is None else int(theta_index)
    truth_eta = sampled_eta if eta_indices is None else tuple(map(int, eta_indices))
    count = int(PARAMETERS["gate2_length"] if length is None else length)
    frequency = float(
        PARAMETERS["gate2_probe_frequency"]
        if probe_frequency is None
        else probe_frequency
    )
    probe_period = max(1, int(round(1.0 / frequency)))
    episodes = []
    for time in range(count):
        context = (time // 12) % 2
        engage = identifiable and time % probe_period == 0
        action = ACTIONS["engage"] if engage else ACTIONS["protect"]
        rng = _rng(seed, f"v234-slice-{time}", released_block)
        danger = int(rng.random() < THETA[truth_theta])
        eta = ETA[truth_eta[context]]
        prevented = int(
            action == ACTIONS["protect"] and rng.random() < eta
        )
        realized = danger * (1 - prevented)
        outcome = int(
            realized
            if rng.random() < float(PARAMETERS["outcome_reliability"])
            else 1 - realized
        )
        if rng.random() < masking:
            outcome = None
        near_miss = None
        efficacy_observation = None
        if identifiable:
            near_miss = int(
                danger
                if rng.random()
                < float(PARAMETERS["danger_diagnostic_reliability"])
                else 1 - danger
            )
            if action == ACTIONS["protect"] and time % 4 == 1:
                efficacy_observation = int(
                    prevented
                    if rng.random()
                    < float(PARAMETERS["efficacy_diagnostic_reliability"])
                    else 1 - prevented
                )
        relief = int(rng.random() < relief_probability)
        episodes.append(
            Episode(
                action,
                context,
                outcome,
                near_miss,
                efficacy_observation,
                relief,
            )
        )
    return AttributionWorld(
        seed,
        truth_theta,
        truth_eta,
        tuple(episodes),
        identifiable,
    )


def generate_controlled_world(
    seed: int,
    *,
    scenario: str,
    length: int = 32,
    released_block: tuple[int, int] | None = None,
) -> AttributionWorld:
    """Public controlled constructor for semantic, assay, and lesion cells."""
    scenario_truth = {
        "irrelevant": (2, (0, 0)),
        "full": (3, (4, 4)),
        "partial": (3, (2, 2)),
        "danger_full": (4, (4, 4)),
        "context_switch": (3, (4, 0)),
        "low_danger": (0, (0, 0)),
        "adaptive": (4, (4, 4)),
    }
    theta_index, eta_indices = scenario_truth.get(
        scenario, scenario_truth["full"]
    )
    identifiable = scenario in {"context_switch", "low_danger", "adaptive"}
    masking = 1.0 if scenario == "masked" else 0.0
    world = generate_world(
        seed,
        identifiable=identifiable,
        length=length,
        theta_index=theta_index,
        eta_indices=eta_indices,
        masking=masking,
        released_block=released_block,
    )
    if scenario == "relief_sham":
        episodes = tuple(
            Episode(ACTIONS["protect"], time % 2, None, None, None, 1)
            for time in range(length)
        )
        return AttributionWorld(seed, 2, (0, 0), episodes, False)
    if scenario == "near_miss":
        episodes = list(world.episodes)
        episodes[-1] = Episode(
            ACTIONS["protect"], 0, 0, 1, 1, episodes[-1].relief
        )
        return AttributionWorld(
            seed, theta_index, eta_indices, tuple(episodes), True
        )
    return world


def finite_information_bound() -> dict[str, float]:
    minimum = min(
        1.0 - float(PARAMETERS["outcome_reliability"]),
        1.0 - float(PARAMETERS["danger_diagnostic_reliability"]),
        1.0 - float(PARAMETERS["efficacy_diagnostic_reliability"]),
    )
    maximum = max(
        float(PARAMETERS["outcome_reliability"]),
        float(PARAMETERS["danger_diagnostic_reliability"]),
        float(PARAMETERS["efficacy_diagnostic_reliability"]),
    )
    bound = 3.0 * math.log(maximum / minimum)
    return {
        "B_max_v234": bound,
        "implied_binary_change_bound": math.tanh(bound / 4.0),
    }
