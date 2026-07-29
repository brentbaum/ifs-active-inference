"""V2.7 exact multiple-protector joint-policy reference."""

from __future__ import annotations

import itertools
import json
import math
from functools import lru_cache
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Sequence

import numpy as np

from . import v221, v25b, v26b
from .audit import ProtocolState, audit_one_posterior
from .rng import component_rng


ROOT = Path(__file__).resolve().parents[1]
PARAMETERS = json.loads((ROOT / "protocols" / "v2.7-parameters.json").read_text())
TOLERANCE = float(PARAMETERS["semantic_tolerance"])
TOPOLOGIES = tuple(PARAMETERS["topologies"])
TOPOLOGY_PRIOR = np.asarray(PARAMETERS["topology_prior"], dtype=float)
MANDATE_SUPPORT = np.asarray(PARAMETERS["mandate_support"], dtype=float)
MANDATE_PRIOR = np.asarray(PARAMETERS["mandate_prior"], dtype=float)
OUTCOME_LEVEL_SUPPORT = np.asarray(
    PARAMETERS["outcome_level_support"], dtype=float
)
OUTCOME_LEVEL_PRIOR = np.asarray(
    PARAMETERS["outcome_level_prior"], dtype=float
)
REGISTRATION_PRIOR = np.asarray(PARAMETERS["registration_prior"], dtype=float)
POLICIES = v26b.POLICIES
POLICY_INDEX = v26b.POLICY_INDEX
POLICY_COORDINATE = np.asarray((-1.0, 0.0, 1.0))
IDLE_SLOT_BYTES = np.zeros(8, dtype=np.uint8).tobytes()
EPOCH_B_DEVELOPMENT_BLOCK = tuple(PARAMETERS["epoch_b_development_block"])


@dataclass(frozen=True)
class JointObservation:
    joint_policy: tuple[int, ...]
    outcome: int | None
    registration: int | None = None


@dataclass(frozen=True)
class MultiProtectorWorld:
    seed: int
    protector_count: int
    topology_index: int
    mandate_index: int
    outcome_level_index: int
    protector_worlds: tuple[v26b.ProtectorWorld, ...]
    observations: tuple[JointObservation, ...]
    scenario: str
    idle_slots: tuple[bytes, ...]
    policy_efforts: tuple[tuple[float, float, float], ...] | None = None


@dataclass(frozen=True)
class MultiProtectorScore:
    protector_scores: tuple[v26b.ProtectorScore, ...]
    q_structure: np.ndarray
    q_topology: np.ndarray
    q_mandate: np.ndarray
    q_outcome_level: np.ndarray
    q_joint_policy: np.ndarray
    joint_policies: tuple[tuple[int, ...], ...]
    expected_cost: np.ndarray
    q_alone: np.ndarray
    exiling_mass: float
    registration_support: float
    system_access: float
    descent: float
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
            EPOCH_B_DEVELOPMENT_BLOCK if released_block is None else released_block
        ),
    )


def _normalize(values: Sequence[float]) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    total = float(array.sum())
    if total <= 0.0:
        raise ValueError("cannot normalize nonpositive mass")
    return array / total


def joint_policies(protector_count: int) -> tuple[tuple[int, ...], ...]:
    if protector_count not in (1, 2, 3):
        raise ValueError("protector_count must be 1, 2, or 3")
    return tuple(itertools.product(range(3), repeat=protector_count))


def _preferences(topology_index: int, protector_count: int) -> np.ndarray:
    # Mandate direction belongs to each protector's V2.6b local policy
    # forecast, not to a slot label in the shared topology.
    return np.zeros(protector_count, dtype=float)


def shared_loss(
    joint_policy: Sequence[int],
    topology_index: int,
    mandate: float | Sequence[float],
    *,
    context: int = 1,
    cross_dependence: bool = True,
) -> float:
    """Declared loss behind the normalized shared-outcome likelihood."""
    policies = np.asarray(joint_policy, dtype=int)
    x = POLICY_COORDINATE[policies]
    n = len(x)
    mandate_values = np.broadcast_to(np.asarray(mandate, dtype=float), (n,))
    preferences = _preferences(topology_index, n)
    if int(context) == 0:
        preferences = 0.5 * preferences
    local = float(np.mean(mandate_values * (x - preferences) ** 2) / 4.0)
    cross = 0.0
    if cross_dependence and n > 1:
        strength = float(np.mean(mandate_values))
        if topology_index == TOPOLOGIES.index("opposed"):
            cross = strength * float(np.mean(x) ** 2)
        elif topology_index == TOPOLOGIES.index("coalition"):
            differences = [
                float((x[left] - x[right]) ** 2) / 4.0
                for left in range(n)
                for right in range(left + 1, n)
            ]
            cross = strength * float(np.mean(differences))
    return local + cross


def shared_outcome_probability(
    joint_policy: Sequence[int],
    topology_index: int,
    mandate: float | Sequence[float],
    outcome_level: float,
    *,
    context: int = 1,
    cross_dependence: bool = True,
) -> float:
    loss = shared_loss(
        joint_policy,
        topology_index,
        mandate,
        context=context,
        cross_dependence=cross_dependence,
    )
    logit = 4.0 * (float(outcome_level) - 0.5) - 3.0 * (loss - 0.25)
    return float(1.0 / (1.0 + math.exp(-logit)))


def structure_posterior(
    observations: Iterable[JointObservation],
    protector_count: int,
) -> tuple[np.ndarray, float]:
    sequence = tuple(observations)
    prior = (
        TOPOLOGY_PRIOR[:, None, None]
        * MANDATE_PRIOR[None, :, None]
        * OUTCOME_LEVEL_PRIOR[None, None, :]
    )
    if protector_count == 1:
        prior = prior.copy()
        prior[1:, :, :] = 0.0
        prior /= prior.sum()
    log_weights = np.full_like(prior, -np.inf)
    positive = prior > 0.0
    log_weights[positive] = np.log(prior[positive])
    policies = joint_policies(protector_count)
    policy_index = {policy: index for index, policy in enumerate(policies)}
    table = _candidate_probability_table(protector_count)
    for item in sequence:
        if item.outcome is None:
            continue
        probability = table[policy_index[item.joint_policy]]
        log_weights += np.log(probability if item.outcome else 1.0 - probability)
    maximum = float(np.max(log_weights))
    shifted = np.exp(log_weights - maximum)
    total = float(shifted.sum())
    return shifted / total, maximum + math.log(total)


@lru_cache(maxsize=3)
def _candidate_probability_table(protector_count: int) -> np.ndarray:
    table = np.empty((3**protector_count, 3, 3, 3), dtype=float)
    for policy_index, policy in enumerate(joint_policies(protector_count)):
        for topology, mandate, level in itertools.product(range(3), repeat=3):
            table[policy_index, topology, mandate, level] = (
                shared_outcome_probability(
                    policy,
                    topology,
                    MANDATE_SUPPORT[mandate],
                    OUTCOME_LEVEL_SUPPORT[level],
                )
            )
    table.setflags(write=False)
    return table


def registration_posterior(
    observations: Iterable[int | None],
    *,
    reliability: float | None = None,
    prior: Sequence[float] | None = None,
) -> np.ndarray:
    q = _normalize(
        REGISTRATION_PRIOR.copy()
        if prior is None
        else np.array(prior, dtype=float, copy=True)
    )
    rel = float(
        PARAMETERS["registration_reliability"]
        if reliability is None
        else reliability
    )
    for observed in observations:
        if observed is None:
            likelihood = np.ones(2)
        else:
            likelihood = np.asarray(
                [rel if observed == state else 1.0 - rel for state in (0, 1)]
            )
        q = q * likelihood / float(q @ likelihood)
    return q


def joint_policy_posterior(
    protector_scores: Sequence[v26b.ProtectorScore],
    q_structure: np.ndarray,
    *,
    mandate_override: Sequence[float] | None = None,
    policy_cost_adjustments: Sequence[Sequence[float]] | None = None,
    cross_dependence: bool = True,
    compare_joint_policies: bool = True,
) -> tuple[tuple[tuple[int, ...], ...], np.ndarray, np.ndarray]:
    scores = tuple(protector_scores)
    policies = joint_policies(len(scores))
    adjustments = (
        np.zeros((len(scores), 3), dtype=float)
        if policy_cost_adjustments is None
        else np.asarray(policy_cost_adjustments, dtype=float)
    )
    if adjustments.shape != (len(scores), 3):
        raise ValueError("policy_cost_adjustments must have shape (protectors, 3)")
    expected_cost = np.empty(len(policies), dtype=float)
    for policy_index, policy in enumerate(policies):
        local = sum(
            float(scores[index].expected_cost[value] + adjustments[index, value])
            for index, value in enumerate(policy)
        )
        structural = 0.0
        for topology in range(len(TOPOLOGIES)):
            for mandate_index, mandate_value in enumerate(MANDATE_SUPPORT):
                mandates: float | Sequence[float] = (
                    mandate_value
                    if mandate_override is None
                    else tuple(mandate_override)
                )
                probability = float(q_structure[topology, mandate_index, :].sum())
                structural += probability * shared_loss(
                    policy,
                    topology,
                    mandates,
                    cross_dependence=cross_dependence,
                )
        expected_cost[policy_index] = (
            local + float(PARAMETERS["shared_outcome_weight"]) * structural
        )
    if compare_joint_policies:
        beta = float(PARAMETERS["joint_policy_inverse_temperature"])
        weights = np.exp(-beta * (expected_cost - float(expected_cost.min())))
        q_policy = weights / float(weights.sum())
    else:
        q_policy = np.full(len(policies), 1.0 / len(policies))
    return policies, q_policy, expected_cost


def score(
    protector_scores: Sequence[v26b.ProtectorScore],
    observations: Iterable[JointObservation],
    protector_count: int,
    *,
    lesions: Sequence[str] = (),
    mandate_override: Sequence[float] | None = None,
    policy_cost_adjustments: Sequence[Sequence[float]] | None = None,
    registration_reliability: float | None = None,
) -> MultiProtectorScore:
    scores = tuple(protector_scores)
    if len(scores) != protector_count:
        raise ValueError("protector score count mismatch")
    lesion_set = set(lesions)
    sequence = tuple(observations)
    q_structure, log_evidence = structure_posterior(sequence, protector_count)
    if "cross_outcome_dependence" in lesion_set:
        q_structure = q_structure.copy()
        q_structure[1:, :, :] = 0.0
        q_structure /= q_structure.sum()
    policies, q_policy, costs = joint_policy_posterior(
        scores,
        q_structure,
        mandate_override=mandate_override,
        policy_cost_adjustments=policy_cost_adjustments,
        cross_dependence=("cross_outcome_dependence" not in lesion_set),
        compare_joint_policies=("joint_policy_comparison" not in lesion_set),
    )
    registrations = [
        None if "registration" in lesion_set else item.registration
        for item in sequence
    ]
    q_alone = registration_posterior(
        registrations, reliability=registration_reliability
    )
    all_block = tuple([POLICY_INDEX["block"]] * protector_count)
    exiling_mass = float(q_policy[policies.index(all_block)])
    contact = np.asarray(
        [
            np.mean([v26b.CONTACT_BY_POLICY[value] for value in policy])
            for policy in policies
        ]
    )
    system_access = float(q_policy @ contact)
    descent = float(
        system_access
        * np.mean([item.partner_score.future_precision_forecast for item in scores])
    )
    q_topology = q_structure.sum(axis=(1, 2))
    q_mandate = q_structure.sum(axis=(0, 2))
    q_outcome = q_structure.sum(axis=(0, 1))
    state = ProtocolState(
        posterior_store={
            "multi_protector_structure": q_structure.copy(),
            "joint_policy": q_policy.copy(),
            "alone_with_this": q_alone.copy(),
            **{
                f"protector_{index}_trust": item.q_trust[2].copy()
                for index, item in enumerate(scores)
            },
        },
        parameter_posterior_store={
            "shared_outcome_level": q_outcome.copy(),
            "mandate_strength": q_mandate.copy(),
        },
        evidence_store={
            "shared_outcomes": math.exp(max(log_evidence, -700.0)),
        },
        metadata=MappingProxyType(
            {
                "stage": "V2.7",
                "protector_count": protector_count,
                "action_selection_likelihood": False,
                "lesions": tuple(sorted(lesion_set)),
                "named_states_are_readouts": True,
            }
        ),
    )
    audit_one_posterior(state)
    return MultiProtectorScore(
        protector_scores=scores,
        q_structure=q_structure,
        q_topology=q_topology,
        q_mandate=q_mandate,
        q_outcome_level=q_outcome,
        q_joint_policy=q_policy,
        joint_policies=policies,
        expected_cost=costs,
        q_alone=q_alone,
        exiling_mass=exiling_mass,
        registration_support=float(q_alone[1] - REGISTRATION_PRIOR[1]),
        system_access=system_access,
        descent=descent,
        state=state,
    )


def _score_protector_world(
    world: v26b.ProtectorWorld,
    *,
    lesions: Sequence[str] = (),
    policy_effort: Sequence[float] | None = None,
) -> v26b.ProtectorScore:
    return v26b.score(
        world.trust_observations,
        world.partner_world.observations,
        world.attribution_world.episodes,
        stakes=world.stakes,
        lesions=lesions,
        policy_effort=policy_effort,
    )


def score_world(
    world: MultiProtectorWorld,
    *,
    lesions: Sequence[str] = (),
    mandate_override: Sequence[float] | None = None,
    policy_cost_adjustments: Sequence[Sequence[float]] | None = None,
    registration_reliability: float | None = None,
) -> MultiProtectorScore:
    common_protector_lesions = tuple(
        lesion
        for lesion in lesions
        if lesion in {"partner_to_trust", "global_broadcast", "attribution_efficacy"}
    )
    scores = tuple(
        _score_protector_world(
            item,
            lesions=(
                common_protector_lesions
                + (
                    ("partner_to_trust",)
                    if "partner_to_one" in set(lesions) and index == 0
                    else ()
                )
            ),
            policy_effort=(
                None if world.policy_efforts is None else world.policy_efforts[index]
            ),
        )
        for index, item in enumerate(world.protector_worlds)
    )
    return score(
        scores,
        world.observations,
        world.protector_count,
        lesions=lesions,
        mandate_override=mandate_override,
        policy_cost_adjustments=policy_cost_adjustments,
        registration_reliability=registration_reliability,
    )


def cue_root_transfer(
    association_state: ProtocolState,
    *,
    lesions: Sequence[str] = (),
) -> float:
    """Compose the frozen V2.2.1 association posterior as a pure forecast."""
    if "cue_root_association" in set(lesions):
        return 0.0
    return float(v221.model_averaged_association(association_state))


def score_world_with_reduction(
    world: MultiProtectorWorld,
    reduction_score: v25b.ReductionScore,
    *,
    lesions: Sequence[str] = (),
) -> MultiProtectorScore:
    """Compose the frozen reduction posterior into future mandate forecasts."""
    baseline, _ = structure_posterior(world.observations, world.protector_count)
    mean_mandate = float(baseline.sum(axis=(0, 2)) @ MANDATE_SUPPORT)
    q_reduced = float(
        reduction_score.q_structure[v25b.STRUCTURE_INDEX["000"]]
    )
    effective = mean_mandate * (1.0 - 0.75 * q_reduced)
    if "reduction" in set(lesions):
        effective = mean_mandate
    return score_world(
        world,
        lesions=lesions,
        mandate_override=tuple(effective for _ in range(world.protector_count)),
    )


def generate_recovery_world(
    seed: int,
    *,
    protector_count: int,
    length: int | None = None,
    released_block: tuple[int, int] | None = None,
) -> MultiProtectorWorld:
    count = int(PARAMETERS["recovery_length"] if length is None else length)
    topology_rng = _rng(seed, "v27-structure", released_block)
    topology_index = (
        0
        if protector_count == 1
        else int(topology_rng.choice(3, p=TOPOLOGY_PRIOR))
    )
    mandate_index = int(topology_rng.choice(3, p=MANDATE_PRIOR))
    outcome_index = int(topology_rng.choice(3, p=OUTCOME_LEVEL_PRIOR))
    scenarios = ("remaining", "low_stakes", "high_stakes")
    protectors = tuple(
        v26b.generate_control_world(
            seed,
            scenario=scenarios[index],
            length=12,
            released_block=released_block,
        )
        for index in range(protector_count)
    )
    policies = joint_policies(protector_count)
    observations = []
    for time in range(count):
        policy = policies[time % len(policies)]
        probability = shared_outcome_probability(
            policy,
            topology_index,
            MANDATE_SUPPORT[mandate_index],
            OUTCOME_LEVEL_SUPPORT[outcome_index],
        )
        outcome_rng = _rng(seed, f"v27-outcome-{time}", released_block)
        observations.append(
            JointObservation(
                joint_policy=policy,
                outcome=int(outcome_rng.random() < probability),
                registration=None,
            )
        )
    return MultiProtectorWorld(
        seed=seed,
        protector_count=protector_count,
        topology_index=topology_index,
        mandate_index=mandate_index,
        outcome_level_index=outcome_index,
        protector_worlds=protectors,
        observations=tuple(observations),
        scenario="recovery",
        idle_slots=tuple(
            IDLE_SLOT_BYTES for _ in range(3 - protector_count)
        ),
        policy_efforts=None,
    )


def generate_control_world(
    seed: int,
    *,
    scenario: str,
    protector_count: int = 2,
    released_block: tuple[int, int] | None = None,
) -> MultiProtectorWorld:
    scenario_map = {
        "polarization": (1, 2, 1, ("low_stakes", "low_stakes", "remaining")),
        "exiling": (0, 0, 0, ("high_stakes", "high_stakes", "high_stakes")),
        "test": (0, 1, 1, ("ambiguous", "ambiguous", "ambiguous")),
        "permit": (2, 0, 2, ("low_stakes", "low_stakes", "low_stakes")),
        "registration_on": (1, 1, 1, ("remaining", "remaining", "remaining")),
        "registration_off": (1, 1, 1, ("remaining", "remaining", "remaining")),
        "befriend_none": (1, 1, 1, ("pressure", "pressure", "pressure")),
        "befriend_one": (1, 1, 1, ("remaining", "pressure", "pressure")),
        "befriend_both": (1, 1, 1, ("remaining", "remaining", "pressure")),
        "coalition": (2, 2, 1, ("remaining", "remaining", "remaining")),
    }
    if scenario not in scenario_map:
        raise ValueError(f"unknown V2.7 control scenario: {scenario}")
    topology, mandate, level, protector_scenarios = scenario_map[scenario]
    protectors = tuple(
        v26b.generate_control_world(
            seed,
            scenario=protector_scenarios[index],
            length=12,
            released_block=released_block,
        )
        for index in range(protector_count)
    )
    registration = (
        1 if scenario == "registration_on" else None
    )
    observations = tuple(
        JointObservation(
            policy,
            int(
                shared_outcome_probability(
                    policy,
                    topology,
                    MANDATE_SUPPORT[mandate],
                    OUTCOME_LEVEL_SUPPORT[level],
                )
                >= 0.5
            ),
            registration,
        )
        for policy in joint_policies(protector_count)
        for _ in range(3)
    )
    effort_map = {
        "exiling": (0.0, 2.0, 3.0),
        "test": (2.0, 0.0, 3.0),
        "permit": (3.0, 2.0, 0.0),
    }
    efforts = (
        None
        if scenario not in effort_map
        else tuple(effort_map[scenario] for _ in range(protector_count))
    )
    return MultiProtectorWorld(
        seed=seed,
        protector_count=protector_count,
        topology_index=topology,
        mandate_index=mandate,
        outcome_level_index=level,
        protector_worlds=protectors,
        observations=observations,
        scenario=scenario,
        idle_slots=tuple(IDLE_SLOT_BYTES for _ in range(3 - protector_count)),
        policy_efforts=efforts,
    )


def finite_information_bounds() -> dict[str, float]:
    probabilities = [
        shared_outcome_probability(policy, topology, mandate, level)
        for topology in range(3)
        for mandate in MANDATE_SUPPORT
        for level in OUTCOME_LEVEL_SUPPORT
        for protector_count in (1, 2, 3)
        for policy in joint_policies(protector_count)
    ]
    minimum = min(min(probabilities), 1.0 - max(probabilities))
    maximum = max(max(probabilities), 1.0 - min(probabilities))
    outcome_bound = math.log(maximum / minimum)
    reliability = float(PARAMETERS["registration_reliability"])
    return {
        "B_max_v27_shared_outcome": outcome_bound,
        "B_max_v27_registration": math.log(reliability / (1.0 - reliability)),
    }
