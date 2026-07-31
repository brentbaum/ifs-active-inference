"""V3.5 PROTECT: exact multi-mode policy organization.

Clinical classifications are readouts over one posterior on generic mode,
edge, parameter-sign, partner, and joint-policy variables.  They are never
scientific state and never enter scoring.
"""

from __future__ import annotations

import hashlib
import itertools
import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

from .audit import audit_state
from .trace_sink import require_trace_sink


STAGE_VERSION = "V3.5"
DEVELOPMENT_BLOCK = (3_500_000, 3_519_999)
MODE_SLOTS = 3
POLICY_VALUES = (0, 1, 2)
JOINT_POLICIES = tuple(itertools.product(POLICY_VALUES, repeat=MODE_SLOTS))
EDGE_NAMES = (
    "M1_G",
    "M2_G",
    "M3_G",
    "JOINT_POLICY_Y",
    "CROSS_MODE_Y",
)
TOLERANCE = 1e-10
MARGINAL_CALIBRATION_TOLERANCE = 0.03


@dataclass(frozen=True)
class ProtectStructure:
    active_modes: int
    mode_root_edges: tuple[int, int, int]
    joint_policy_outcome: int
    cross_mode_outcome: int

    def __post_init__(self) -> None:
        if self.active_modes not in (1, 2, 3):
            raise ValueError("active_modes must be in {1,2,3}")
        if len(self.mode_root_edges) != MODE_SLOTS:
            raise ValueError("three mode-root spikes are required")
        values = (
            *self.mode_root_edges,
            self.joint_policy_outcome,
            self.cross_mode_outcome,
        )
        if any(value not in (0, 1) for value in values):
            raise ValueError("all structural productions are exact spikes")
        if any(self.mode_root_edges[self.active_modes :]):
            raise ValueError("dormant mode edges must be absent")


@dataclass(frozen=True)
class ProtectConfig:
    befriend: str
    partner: str
    stakes: str
    policy_regime: str
    mode_count: int
    topology: str
    support_target: str
    registration: str
    denied_contact: str
    length: int = 64

    def __post_init__(self) -> None:
        supports = {
            "befriend": {"none", "one", "all"},
            "partner": {"remaining", "pressure"},
            "stakes": {"low", "high"},
            "policy_regime": {"exclusion", "monitoring", "engagement", "mixed"},
            "topology": {"independent", "opposed", "allied"},
            "support_target": {"none", "one", "all"},
            "registration": {"delivered", "masked"},
            "denied_contact": {"delivered", "masked"},
        }
        for name, support in supports.items():
            if getattr(self, name) not in support:
                raise ValueError(f"invalid {name}")
        if self.mode_count not in (1, 2, 3):
            raise ValueError("mode_count must be in {1,2,3}")
        if self.length < 8:
            raise ValueError("length must be at least eight")


@dataclass(frozen=True)
class ProtectObservation:
    time: int
    mode_signals: tuple[int | None, int | None, int | None]
    root_signal: int | None
    policy: tuple[int, int, int]
    outcome: int | None
    partner_remaining: int | None
    partner_pressure: int | None
    support_signals: tuple[int | None, int | None, int | None]
    registration: tuple[int | None, int | None, int | None]
    denied_contact: int | None
    stakes: float
    support_targets: tuple[int, int, int] = (0, 0, 0)
    contact_signals: tuple[
        int | None, int | None, int | None
    ] = (None, None, None)


@dataclass(frozen=True)
class ProtectWorld:
    seed: int
    config: ProtectConfig | None
    truth_structure: ProtectStructure
    truth_cross_sign: int
    truth_partner: int
    truth_modes: tuple[tuple[int, int, int], ...]
    observations: tuple[ProtectObservation, ...]
    exact_log_probability: float
    rng_keys: tuple[tuple[str, int, str, int | str], ...]
    analysis_labels: tuple[str, ...] = ()
    truth_support_response: tuple[int, int, int] = (0, 0, 0)
    truth_contact_response: tuple[int, int, int] = (0, 0, 0)


@dataclass(frozen=True)
class ProtectPosterior:
    components: tuple[tuple[ProtectStructure, int], ...]
    probabilities: tuple[float, ...]
    log_evidence: float
    edge_probabilities: Mapping[str, float]
    active_mode_probabilities: tuple[float, float, float]
    mode_occupancy: tuple[float, float, float]
    topology_probabilities: Mapping[str, float]
    q_partner: tuple[float, float]
    joint_policy_posterior: tuple[float, ...]
    support_response_posterior: tuple[float, float, float]
    contact_response_posterior: tuple[float, float, float]
    interventional_influence: tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    readouts: Mapping[str, float]
    latent_posterior: Mapping[str, tuple[float, ...]]
    parameter_posterior: Mapping[str, tuple[float, ...]]
    structure_posterior: Mapping[str, tuple[float, ...]]
    model_evidence: Mapping[str, float]

    def query(self, name: str) -> float:
        return float(self.readouts[name])


def program_values(structure: ProtectStructure) -> Mapping[str, int]:
    return MappingProxyType(
        {
            "M1_G": structure.mode_root_edges[0],
            "M2_G": structure.mode_root_edges[1],
            "M3_G": structure.mode_root_edges[2],
            "JOINT_POLICY_Y": structure.joint_policy_outcome,
            "CROSS_MODE_Y": structure.cross_mode_outcome,
        }
    )


def enumerate_programs() -> tuple[ProtectStructure, ...]:
    result = []
    for active in (1, 2, 3):
        for roots in itertools.product((0, 1), repeat=active):
            padded = tuple(roots) + (0,) * (MODE_SLOTS - active)
            for joint, cross in itertools.product((0, 1), repeat=2):
                result.append(
                    ProtectStructure(active, padded, joint, cross)
                )
    return tuple(result)


PROGRAMS = enumerate_programs()


def _code_length(structure: ProtectStructure) -> float:
    return (
        1.0
        + float(structure.active_modes)
        + math.fsum(program_values(structure).values())
    )


_PRIOR_NORMALIZER = math.fsum(2.0 ** (-_code_length(p)) for p in PROGRAMS)


def structure_log_prior(
    structure: ProtectStructure,
    restrictions: Mapping[str, tuple[int, ...]] | None = None,
    *,
    code_length_scale: float = 1.0,
) -> float:
    if code_length_scale <= 0:
        raise ValueError("code-length scale must be positive")
    limits = {} if restrictions is None else dict(restrictions)
    if structure.active_modes not in limits.get(
        "active_modes", (1, 2, 3)
    ):
        return -math.inf
    for name, value in program_values(structure).items():
        if value not in limits.get(name, (0, 1)):
            return -math.inf
    retained = [
        program
        for program in PROGRAMS
        if program.active_modes
        in limits.get("active_modes", (1, 2, 3))
        and all(
            value in limits.get(name, (0, 1))
            for name, value in program_values(program).items()
        )
    ]
    normalizer = math.fsum(
        2.0 ** (-code_length_scale * _code_length(program))
        for program in retained
    )
    return (
        -code_length_scale * _code_length(structure) * math.log(2.0)
        - math.log(normalizer)
    )


def _clip(value: float) -> float:
    return float(np.clip(value, 0.03, 0.97))


def mode_signal_probability(observed: int, latent: int) -> float:
    return 0.86 if int(observed) == int(latent) else 0.14


def registration_probability(observed: int, latent: int) -> float:
    """Candidate-common registration production.

    ``latent`` remains in the public signature for channel-interface
    compatibility, but registration is the plan-declared epistemic null.  All
    candidates therefore use the frozen M_k=0 prior predictive: P(1)=0.20.
    """
    del latent
    return 0.20 if int(observed) else 0.80


def root_signal_probability(
    observed: int,
    modes: Sequence[int],
    structure: ProtectStructure,
) -> float:
    parents = [
        modes[index]
        for index in range(structure.active_modes)
        if structure.mode_root_edges[index]
    ]
    if not parents:
        return 0.5
    root = int(math.fsum(parents) >= len(parents) / 2.0)
    return 0.84 if int(observed) == root else 0.16


def outcome_probability(
    policy: Sequence[int],
    modes: Sequence[int],
    structure: ProtectStructure,
    cross_sign: int,
) -> float:
    probability = 0.5
    active = structure.active_modes
    if structure.joint_policy_outcome:
        centered = math.fsum(policy[:active]) / active - 1.0
        probability += 0.18 * centered
    if structure.cross_mode_outcome:
        active_pairs = [
            (left, right)
            for left in range(active)
            for right in range(left + 1, active)
            if modes[left] and modes[right]
        ]
        if active_pairs:
            if cross_sign < 0:
                conflict = math.fsum(
                    abs(policy[left] - policy[right]) / 2.0
                    for left, right in active_pairs
                ) / len(active_pairs)
                probability += 0.30 * conflict
            else:
                coalition = math.fsum(
                    int(policy[left] == 2 and policy[right] == 2)
                    for left, right in active_pairs
                ) / len(active_pairs)
                probability += 0.30 * coalition
    return _clip(probability)


def partner_channel_probability(
    observed: int, reliable: int, channel: str
) -> float:
    probability = 0.86 if channel == "remaining" else 0.14
    if not reliable:
        probability = 1.0 - probability
    return probability if observed else 1.0 - probability


def support_probability(
    observed: int, reliable: int, targeted: int
) -> float:
    probability = 0.82 if reliable and targeted else 0.25
    return probability if observed else 1.0 - probability


def denied_contact_probability(
    observed: int, vulnerable: int, policy: int
) -> float:
    probability = 0.86 if vulnerable and policy == 0 else 0.14
    return probability if observed else 1.0 - probability


def contact_probability(
    observed: int,
    reliable: int,
    policy: int,
    response: int,
) -> float:
    probability = 0.14
    if response and policy == 0:
        probability = 0.50 if reliable else 0.86
    return probability if observed else 1.0 - probability


def _mode_prior(modes: Sequence[int], active: int) -> float:
    if any(modes[active:]):
        return 0.0
    return 0.5 ** active


def _slice_likelihood(
    observation: ProtectObservation,
    modes: Sequence[int],
    structure: ProtectStructure,
    cross_sign: int,
    reliable: int,
    *,
    registration_enabled: bool = True,
    denied_enabled: bool = True,
) -> float:
    result = 1.0
    for index in range(MODE_SLOTS):
        active = index < structure.active_modes
        signal = observation.mode_signals[index]
        if signal is not None:
            result *= (
                mode_signal_probability(signal, modes[index])
                if active else mode_signal_probability(signal, 0)
            )
        registered = observation.registration[index]
        if registration_enabled and registered is not None:
            result *= registration_probability(registered, 0)
    if observation.root_signal is not None:
        result *= root_signal_probability(
            observation.root_signal, modes, structure
        )
    if observation.outcome is not None:
        probability = outcome_probability(
            observation.policy, modes, structure, cross_sign
        )
        result *= probability if observation.outcome else 1.0 - probability
    if observation.partner_remaining is not None:
        result *= partner_channel_probability(
            observation.partner_remaining, reliable, "remaining"
        )
    if observation.partner_pressure is not None:
        result *= partner_channel_probability(
            observation.partner_pressure, reliable, "pressure"
        )
    if denied_enabled and observation.denied_contact is not None:
        vulnerable_index = max(structure.active_modes - 1, 0)
        result *= denied_contact_probability(
            observation.denied_contact,
            modes[vulnerable_index],
            observation.policy[vulnerable_index],
        )
    return float(result)


def _binary_parameter_evidence(
    observations: Sequence[ProtectObservation],
    structure: ProtectStructure,
    reliable: int,
    channel: str,
    enabled: bool = True,
) -> tuple[float, tuple[float, float, float]]:
    if not enabled:
        return 0.0, tuple(
            0.5 if index < structure.active_modes else 0.0
            for index in range(MODE_SLOTS)
        )
    log_evidence = 0.0
    posteriors = []
    for index in range(MODE_SLOTS):
        if index >= structure.active_modes:
            dormant_log = 0.0
            for observation in observations:
                observed = (
                    observation.support_signals[index]
                    if channel == "support"
                    else observation.contact_signals[index]
                )
                if observed is None:
                    continue
                probability = (
                    support_probability(observed, 0, 0)
                    if channel == "support"
                    else contact_probability(observed, 0, 1, 0)
                )
                dormant_log += math.log(probability)
            log_evidence += dormant_log
            posteriors.append(0.0)
            continue
        theta_logs = []
        for theta in (0, 1):
            value = -math.log(2.0)
            for observation in observations:
                observed = (
                    observation.support_signals[index]
                    if channel == "support"
                    else observation.contact_signals[index]
                )
                if observed is None:
                    continue
                if channel == "support":
                    targeted = observation.support_targets[index]
                    probability = support_probability(
                        observed,
                        reliable,
                        int(theta and targeted),
                    )
                else:
                    probability = contact_probability(
                        observed,
                        reliable,
                        observation.policy[index],
                        theta,
                    )
                value += math.log(probability)
            theta_logs.append(value)
        maximum = max(theta_logs)
        evidence = maximum + math.log(
            math.fsum(math.exp(value - maximum) for value in theta_logs)
        )
        log_evidence += evidence
        posteriors.append(math.exp(theta_logs[1] - evidence))
    return float(log_evidence), tuple(float(value) for value in posteriors)


def _component_evidence(
    observations: Sequence[ProtectObservation],
    structure: ProtectStructure,
    sign: int,
    reliable: int,
    *,
    registration_enabled: bool,
    denied_enabled: bool,
) -> tuple[
    float,
    tuple[tuple[float, ...], ...],
    tuple[float, float, float],
    tuple[float, float, float],
]:
    log_evidence = 0.0
    mode_posteriors = []
    for observation in observations:
        configurations = tuple(itertools.product((0, 1), repeat=MODE_SLOTS))
        weights = np.asarray(
            [
                _mode_prior(modes, structure.active_modes)
                * _slice_likelihood(
                    observation,
                    modes,
                    structure,
                    sign,
                    reliable,
                    registration_enabled=registration_enabled,
                    denied_enabled=denied_enabled,
                )
                for modes in configurations
            ],
            dtype=float,
        )
        evidence = float(weights.sum())
        if evidence <= 0:
            raise ValueError("zero multi-mode evidence")
        weights /= evidence
        log_evidence += math.log(evidence)
        mode_posteriors.append(
            tuple(
                float(
                    math.fsum(
                        probability * modes[index]
                        for probability, modes in zip(
                            weights, configurations
                        )
                    )
                )
                for index in range(MODE_SLOTS)
            )
        )
    support_log, support_posterior = _binary_parameter_evidence(
        observations, structure, reliable, "support"
    )
    contact_log, contact_posterior = _binary_parameter_evidence(
        observations,
        structure,
        reliable,
        "contact",
        enabled=denied_enabled,
    )
    return (
        float(log_evidence + support_log + contact_log),
        tuple(mode_posteriors),
        support_posterior,
        contact_posterior,
    )


def _softmax(values: Sequence[float]) -> tuple[float, ...]:
    array = np.asarray(values, dtype=float)
    maximum = float(array.max())
    weights = np.exp(array - maximum)
    weights /= weights.sum()
    return tuple(float(value) for value in weights)


def _policy_scores(
    probabilities: Sequence[float],
    components: Sequence[tuple[ProtectStructure, int]],
    mode_occupancy: Sequence[float],
    q_reliable: float,
    support_response: Sequence[float],
    contact_response: Sequence[float],
    stakes: float,
) -> tuple[float, ...]:
    if stakes <= 0:
        raise ValueError("stakes must be positive")
    scores = []
    for policy in JOINT_POLICIES:
        safe = math.fsum(
            float(probability)
            * outcome_probability(
                policy, mode_occupancy, structure, sign
            )
            for probability, (structure, sign) in zip(
                probabilities, components
            )
        )
        vulnerable_cost = math.fsum(
            float(probability)
            * mode_occupancy[structure.active_modes - 1]
            * int(policy[structure.active_modes - 1] == 2)
            * (
                1.0
                - (
                    0.5
                    + 0.18
                    * (policy[structure.active_modes - 1] - 1.0)
                    if structure.joint_policy_outcome
                    else 0.5
                )
            )
            for probability, (structure, _sign) in zip(
                probabilities, components
            )
        )
        support_benefit = math.fsum(
            q_reliable
            * support_response[index]
            * mode_occupancy[index]
            * int(policy[index] == 2)
            for index in range(MODE_SLOTS)
        )
        denied_cost = math.fsum(
            contact_response[index]
            * mode_occupancy[index]
            * int(policy[index] == 0)
            for index in range(MODE_SLOTS)
        )
        effort = math.fsum(abs(value - 1) for value in policy)
        scores.append(
            2.0 * safe
            - 4.0 * stakes * vulnerable_cost
            + 1.2 * support_benefit
            - 1.2 * denied_cost
            - 0.05 * effort
        )
    return tuple(float(value) for value in scores)


def _policy_distribution(
    scores: Sequence[float],
    fixed: Mapping[int, int] | None = None,
) -> tuple[float, ...]:
    fixed_values = {} if fixed is None else dict(fixed)
    retained = [
        index
        for index, policy in enumerate(JOINT_POLICIES)
        if all(policy[slot] == value for slot, value in fixed_values.items())
    ]
    selected = _softmax([scores[index] for index in retained])
    result = [0.0] * len(JOINT_POLICIES)
    for probability, index in zip(selected, retained):
        result[index] = probability
    return tuple(result)


def interventional_policy_influence(
    scores: Sequence[float],
) -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]:
    result = []
    for source in range(MODE_SLOTS):
        low = _policy_distribution(scores, {source: 0})
        high = _policy_distribution(scores, {source: 2})
        row = []
        for target in range(MODE_SLOTS):
            if target == source:
                row.append(0.0)
                continue
            high_mean = math.fsum(
                probability * policy[target]
                for probability, policy in zip(high, JOINT_POLICIES)
            )
            low_mean = math.fsum(
                probability * policy[target]
                for probability, policy in zip(low, JOINT_POLICIES)
            )
            row.append(float(high_mean - low_mean))
        result.append(tuple(row))
    return tuple(result)


def score_world(
    world: ProtectWorld,
    *,
    restrictions: Mapping[str, tuple[int, ...]] | None = None,
    registration_enabled: bool = True,
    denied_enabled: bool = True,
    code_length_scale: float = 1.0,
) -> ProtectPosterior:
    require_trace_sink("v35.score_world", seed=int(world.seed))
    if world.analysis_labels:
        raise ValueError("analysis labels may not reach V3.5 inference")
    components: list[tuple[ProtectStructure, int]] = []
    log_weights = []
    mode_terms = []
    partner_terms = []
    support_terms = []
    contact_terms = []
    for structure in PROGRAMS:
        prior = structure_log_prior(
            structure,
            restrictions,
            code_length_scale=code_length_scale,
        )
        if not math.isfinite(prior):
            continue
        signs = (-1, 1) if structure.cross_mode_outcome else (0,)
        for sign in signs:
            for reliable in (0, 1):
                likelihood, modes, support_q, contact_q = _component_evidence(
                    world.observations,
                    structure,
                    sign,
                    reliable,
                    registration_enabled=registration_enabled,
                    denied_enabled=denied_enabled,
                )
                components.append((structure, sign))
                log_weights.append(
                    prior
                    - math.log(len(signs))
                    - math.log(2.0)
                    + likelihood
                )
                mode_terms.append(modes)
                partner_terms.append(reliable)
                support_terms.append(support_q)
                contact_terms.append(contact_q)
    values = np.asarray(log_weights, dtype=float)
    maximum = float(values.max())
    log_evidence = maximum + math.log(float(np.exp(values - maximum).sum()))
    probabilities = np.exp(values - log_evidence)
    edge_probabilities = MappingProxyType(
        {
            name: float(
                math.fsum(
                    probability
                    for probability, (structure, _sign) in zip(
                        probabilities, components
                    )
                    if program_values(structure)[name]
                )
            )
            for name in EDGE_NAMES
        }
    )
    active_probabilities = tuple(
        float(
            math.fsum(
                probability
                for probability, (structure, _sign) in zip(
                    probabilities, components
                )
                if structure.active_modes >= index + 1
            )
        )
        for index in range(MODE_SLOTS)
    )
    occupancy = []
    for mode in range(MODE_SLOTS):
        occupancy.append(
            float(
                math.fsum(
                    probability
                    * math.fsum(row[mode] for row in modes)
                    / max(len(modes), 1)
                    for probability, modes in zip(
                        probabilities, mode_terms
                    )
                )
            )
        )
    q_reliable = float(
        math.fsum(
            probability
            for probability, reliable in zip(
                probabilities, partner_terms
            )
            if reliable
        )
    )
    support_response = tuple(
        float(
            math.fsum(
                probability * term[index]
                for probability, term in zip(probabilities, support_terms)
            )
        )
        for index in range(MODE_SLOTS)
    )
    contact_response = tuple(
        float(
            math.fsum(
                probability * term[index]
                for probability, term in zip(probabilities, contact_terms)
            )
        )
        for index in range(MODE_SLOTS)
    )
    topology = MappingProxyType(
        {
            "independent": float(
                math.fsum(
                    probability
                    for probability, (_structure, sign) in zip(
                        probabilities, components
                    )
                    if sign == 0
                )
            ),
            "opposed": float(
                math.fsum(
                    probability
                    for probability, (_structure, sign) in zip(
                        probabilities, components
                    )
                    if sign < 0
                )
            ),
            "coalition": float(
                math.fsum(
                    probability
                    for probability, (_structure, sign) in zip(
                        probabilities, components
                    )
                    if sign > 0
                )
            ),
        }
    )
    final_modes = tuple(float(value) for value in occupancy)
    stakes = (
        world.observations[-1].stakes if world.observations else 1.0
    )
    policy_scores = _policy_scores(
        probabilities,
        components,
        final_modes,
        q_reliable,
        support_response,
        contact_response,
        stakes,
    )
    joint_policy = _policy_distribution(policy_scores)
    influence = interventional_policy_influence(policy_scores)
    access_probability = float(
        math.fsum(
            component_probability
            * policy_probability
            * int(policy[structure.active_modes - 1] == 2)
            for component_probability, (structure, _sign) in zip(
                probabilities, components
            )
            for policy_probability, policy in zip(
                joint_policy, JOINT_POLICIES
            )
        )
    )
    exile_probability = float(
        math.fsum(
            component_probability
            * policy_probability
            * int(policy[structure.active_modes - 1] == 0)
            for component_probability, (structure, _sign) in zip(
                probabilities, components
            )
            for policy_probability, policy in zip(
                joint_policy, JOINT_POLICIES
            )
        )
    )
    protector_probability = float(
        math.fsum(
            component_probability
            * policy_probability
            * int(
                policy[0] in (0, 1)
                and policy[structure.active_modes - 1] != 0
            )
            for component_probability, (structure, _sign) in zip(
                probabilities, components
            )
            for policy_probability, policy in zip(
                joint_policy, JOINT_POLICIES
            )
        )
    )
    polarization = float(
        max(
            abs(influence[left][right])
            for left in range(MODE_SLOTS)
            for right in range(MODE_SLOTS)
            if left != right
        )
    )
    coalition = topology["coalition"] * float(
        math.fsum(
            probability
            for probability, policy in zip(joint_policy, JOINT_POLICIES)
            if policy[0] == 2 and policy[1] == 2
        )
    )
    readouts = MappingProxyType(
        {
            "protector_like_probability": protector_probability,
            "exile_like_probability": exile_probability,
            "access_probability": access_probability,
            "polarization": float(polarization),
            "coalition": float(coalition),
            "trust_remaining": q_reliable,
            "registration_information": float(
                math.fsum(
                    int(
                        value is not None
                    )
                    for item in world.observations
                    for value in item.registration
                )
            ),
        }
    )
    posterior = ProtectPosterior(
        components=tuple(components),
        probabilities=tuple(float(value) for value in probabilities),
        log_evidence=float(log_evidence),
        edge_probabilities=edge_probabilities,
        active_mode_probabilities=active_probabilities,
        mode_occupancy=tuple(occupancy),
        topology_probabilities=topology,
        q_partner=(1.0 - q_reliable, q_reliable),
        joint_policy_posterior=joint_policy,
        support_response_posterior=support_response,
        contact_response_posterior=contact_response,
        interventional_influence=influence,
        readouts=readouts,
        latent_posterior=MappingProxyType(
            {"M": tuple(occupancy), "L": (1.0 - q_reliable, q_reliable)}
        ),
        parameter_posterior=MappingProxyType(
            {
                "cross_sign": (
                    topology["opposed"],
                    topology["coalition"],
                ),
                "support_response": support_response,
                "contact_response": contact_response,
            }
        ),
        structure_posterior=MappingProxyType(
            {"programs": tuple(float(value) for value in probabilities)}
        ),
        model_evidence=MappingProxyType(
            {"protect": float(log_evidence)}
        ),
    )
    violations = audit_state(posterior)
    if violations:
        raise AssertionError("; ".join(violations))
    return posterior


def _rng(
    seed: int,
    component: str,
    event: int | str,
    released_block: tuple[int, int] | None,
    keys: list[tuple[str, int, str, int | str]],
) -> np.random.Generator:
    block = DEVELOPMENT_BLOCK if released_block is None else released_block
    if not block[0] <= int(seed) <= block[1]:
        raise ValueError("seed is outside the authorized V3.5 block")
    key = (STAGE_VERSION, int(seed), str(component), event)
    keys.append(key)
    digest = hashlib.sha256(repr(key).encode("utf-8")).digest()
    return np.random.default_rng(int.from_bytes(digest[:16], "big"))


def _bernoulli(
    seed: int,
    component: str,
    event: int,
    probability: float,
    released_block: tuple[int, int] | None,
    keys: list[tuple[str, int, str, int | str]],
) -> int:
    return int(
        _rng(seed, component, event, released_block, keys).random()
        < probability
    )


def _policy_for(
    seed: int,
    time: int,
    regime: str,
    active: int,
    released_block: tuple[int, int] | None,
    keys: list[tuple[str, int, str, int | str]],
) -> tuple[int, int, int]:
    center = {"exclusion": 0, "monitoring": 1, "engagement": 2}.get(
        regime, time % 3
    )
    result = []
    for mode in range(MODE_SLOTS):
        if mode >= active:
            result.append(1)
        elif regime == "mixed":
            result.append((time // (3 ** mode)) % 3)
        else:
            jitter = int(
                _rng(
                    seed,
                    f"policy-jitter:{mode}",
                    time,
                    released_block,
                    keys,
                ).random()
                < 0.12
            )
            result.append((center + jitter) % 3 if jitter else center)
    return tuple(result)


def _sample_world(
    seed: int,
    structure: ProtectStructure,
    sign: int,
    *,
    config: ProtectConfig | None,
    length: int,
    reliable: int,
    support_response: tuple[int, int, int],
    contact_response: tuple[int, int, int],
    released_block: tuple[int, int] | None,
    keys: list[tuple[str, int, str, int | str]],
) -> ProtectWorld:
    modes_path = []
    observations = []
    for time in range(length):
        modes = tuple(
            _bernoulli(
                seed,
                f"mode:{index}",
                time,
                0.5,
                released_block,
                keys,
            )
            if index < structure.active_modes
            else 0
            for index in range(MODE_SLOTS)
        )
        modes_path.append(modes)
        regime = config.policy_regime if config is not None else "mixed"
        policy = _policy_for(
            seed,
            time,
            regime,
            structure.active_modes,
            released_block,
            keys,
        )
        if config is None:
            target_count = structure.active_modes
            registration_delivered = True
            denied_delivered = True
            stakes = 1.0
        else:
            support_count = {
                "none": 0,
                "one": 1,
                "all": structure.active_modes,
            }[config.support_target]
            befriend_count = {
                "none": 0,
                "one": 1,
                "all": structure.active_modes,
            }[config.befriend]
            target_count = min(support_count, befriend_count)
            registration_delivered = config.registration == "delivered"
            denied_delivered = config.denied_contact == "delivered"
            stakes = 0.7 if config.stakes == "low" else 1.3
        mode_signals = tuple(
            _bernoulli(
                seed,
                f"mode-signal:{index}",
                time,
                (
                    mode_signal_probability(1, modes[index])
                    if index < structure.active_modes
                    else mode_signal_probability(1, 0)
                ),
                released_block,
                keys,
            )
            for index in range(MODE_SLOTS)
        )
        roots = [
            modes[index]
            for index in range(structure.active_modes)
            if structure.mode_root_edges[index]
        ]
        truth_root = int(
            bool(roots) and math.fsum(roots) >= len(roots) / 2.0
        )
        root_one = root_signal_probability(
            1, modes, structure
        )
        root_signal = _bernoulli(
            seed,
            "root-signal",
            time,
            root_one,
            released_block,
            keys,
        )
        outcome = _bernoulli(
            seed,
            "outcome",
            time,
            outcome_probability(policy, modes, structure, sign),
            released_block,
            keys,
        )
        remaining = _bernoulli(
            seed,
            "partner-remaining",
            time,
            0.86 if reliable else 0.14,
            released_block,
            keys,
        )
        pressure = _bernoulli(
            seed,
            "partner-pressure",
            time,
            0.14 if reliable else 0.86,
            released_block,
            keys,
        )
        support_targets = tuple(
            int(index < target_count) for index in range(MODE_SLOTS)
        )
        support = tuple(
            _bernoulli(
                seed,
                f"support:{index}",
                time,
                (
                    0.82
                    if reliable
                    and index < target_count
                    and support_response[index]
                    else 0.25
                )
                if index < structure.active_modes
                else support_probability(1, 0, 0),
                released_block,
                keys,
            )
            for index in range(MODE_SLOTS)
        )
        registration = tuple(
            _bernoulli(
                seed,
                f"registration:{index}",
                time,
                (
                    registration_probability(1, modes[index])
                    if index < structure.active_modes
                    else registration_probability(1, 0)
                ),
                released_block,
                keys,
            )
            if registration_delivered
            else None
            for index in range(MODE_SLOTS)
        )
        denied = None
        contact_signals = tuple(
            _bernoulli(
                seed,
                f"contact:{index}",
                time,
                (
                    0.50
                    if reliable
                    and contact_response[index]
                    and policy[index] == 0
                    else 0.86
                    if (not reliable)
                    and contact_response[index]
                    and policy[index] == 0
                    else 0.14
                )
                if index < structure.active_modes
                else 0.14,
                released_block,
                keys,
            )
            if denied_delivered
            else None
            for index in range(MODE_SLOTS)
        )
        observations.append(
            ProtectObservation(
                time,
                mode_signals,
                root_signal,
                policy,
                outcome,
                remaining,
                pressure,
                support,
                registration,
                denied,
                stakes,
                support_targets,
                contact_signals,
            )
        )
    total = structure_log_prior(structure)
    total += -math.log(2.0) if structure.cross_mode_outcome else 0.0
    total += -math.log(2.0)
    total += -structure.active_modes * math.log(2.0)
    total += -structure.active_modes * math.log(2.0)
    for modes, observation in zip(modes_path, observations):
        total += math.log(_mode_prior(modes, structure.active_modes))
        total += math.log(
            _slice_likelihood(
                observation,
                modes,
                structure,
                sign,
                reliable,
            )
        )
    for index in range(MODE_SLOTS):
        for observation in observations:
            support_value = observation.support_signals[index]
            if support_value is not None:
                probability = (
                    support_probability(
                        support_value,
                        reliable,
                        int(
                            support_response[index]
                            and observation.support_targets[index]
                        ),
                    )
                    if index < structure.active_modes
                    else support_probability(support_value, 0, 0)
                )
                total += math.log(probability)
            contact_value = observation.contact_signals[index]
            if contact_value is not None:
                probability = (
                    contact_probability(
                        contact_value,
                        reliable,
                        observation.policy[index],
                        contact_response[index],
                    )
                    if index < structure.active_modes
                    else contact_probability(contact_value, 0, 1, 0)
                )
                total += math.log(probability)
    return ProtectWorld(
        int(seed),
        config,
        structure,
        sign,
        reliable,
        tuple(modes_path),
        tuple(observations),
        float(total),
        tuple(keys),
        (),
        support_response,
        contact_response,
    )


def generate_world(
    seed: int,
    config: ProtectConfig,
    *,
    released_block: tuple[int, int] | None = None,
) -> ProtectWorld:
    require_trace_sink("v35.generate_world", seed=int(seed))
    keys: list[tuple[str, int, str, int | str]] = []
    structure = ProtectStructure(
        config.mode_count,
        tuple(
            int(index < config.mode_count)
            for index in range(MODE_SLOTS)
        ),
        1,
        int(config.topology != "independent"),
    )
    sign = (
        -1
        if config.topology == "opposed"
        else 1
        if config.topology == "allied"
        else 0
    )
    reliable = int(config.partner == "remaining")
    support_response = tuple(
        int(index < structure.active_modes) for index in range(MODE_SLOTS)
    )
    contact_response = support_response
    return _sample_world(
        seed,
        structure,
        sign,
        config=config,
        length=config.length,
        reliable=reliable,
        support_response=support_response,
        contact_response=contact_response,
        released_block=released_block,
        keys=keys,
    )


def generate_recovery_world(
    seed: int,
    *,
    length: int = 64,
    released_block: tuple[int, int] | None = None,
) -> ProtectWorld:
    require_trace_sink("v35.generate_recovery_world", seed=int(seed))
    keys: list[tuple[str, int, str, int | str]] = []
    probabilities = np.asarray(
        [math.exp(structure_log_prior(program)) for program in PROGRAMS]
    )
    structure = PROGRAMS[
        int(
            _rng(
                seed, "structure", 0, released_block, keys
            ).choice(len(PROGRAMS), p=probabilities)
        )
    ]
    sign = (
        int(
            _rng(seed, "cross-sign", 0, released_block, keys).choice(
                (-1, 1)
            )
        )
        if structure.cross_mode_outcome
        else 0
    )
    reliable = _bernoulli(
        seed, "partner-state", 0, 0.5, released_block, keys
    )
    support_response = tuple(
        _bernoulli(
            seed,
            f"support-response:{index}",
            0,
            0.5,
            released_block,
            keys,
        )
        if index < structure.active_modes
        else 0
        for index in range(MODE_SLOTS)
    )
    contact_response = tuple(
        _bernoulli(
            seed,
            f"contact-response:{index}",
            0,
            0.5,
            released_block,
            keys,
        )
        if index < structure.active_modes
        else 0
        for index in range(MODE_SLOTS)
    )
    return _sample_world(
        seed,
        structure,
        sign,
        config=None,
        length=length,
        reliable=reliable,
        support_response=support_response,
        contact_response=contact_response,
        released_block=released_block,
        keys=keys,
    )


def exact_complete_log_probability(world: ProtectWorld) -> float:
    total = structure_log_prior(world.truth_structure)
    total += (
        -math.log(2.0)
        if world.truth_structure.cross_mode_outcome
        else 0.0
    )
    total += -math.log(2.0)
    total += -world.truth_structure.active_modes * math.log(2.0)
    total += -world.truth_structure.active_modes * math.log(2.0)
    for modes, observation in zip(
        world.truth_modes, world.observations
    ):
        total += math.log(
            _mode_prior(modes, world.truth_structure.active_modes)
        )
        total += math.log(
            _slice_likelihood(
                observation,
                modes,
                world.truth_structure,
                world.truth_cross_sign,
                world.truth_partner,
            )
        )
    for index in range(MODE_SLOTS):
        for observation in world.observations:
            support_value = observation.support_signals[index]
            if support_value is not None:
                probability = (
                    support_probability(
                        support_value,
                        world.truth_partner,
                        int(
                            world.truth_support_response[index]
                            and observation.support_targets[index]
                        ),
                    )
                    if index < world.truth_structure.active_modes
                    else support_probability(support_value, 0, 0)
                )
                total += math.log(probability)
            contact_value = observation.contact_signals[index]
            if contact_value is not None:
                probability = (
                    contact_probability(
                        contact_value,
                        world.truth_partner,
                        observation.policy[index],
                        world.truth_contact_response[index],
                    )
                    if index < world.truth_structure.active_modes
                    else contact_probability(contact_value, 0, 1, 0)
                )
                total += math.log(probability)
    return float(total)


def marginal_calibration_dummy(
    sample_size: int = 20_000,
) -> Mapping[str, Any]:
    """Enumerable two-program calibration check on shared channel support."""
    if sample_size <= 0:
        raise ValueError("sample size must be positive")
    programs = (
        ProtectStructure(1, (0, 0, 0), 0, 0),
        ProtectStructure(2, (0, 0, 0), 0, 0),
    )
    raw_priors = np.asarray(
        [math.exp(structure_log_prior(program)) for program in programs],
        dtype=float,
    )
    priors = raw_priors / raw_priors.sum()
    outcomes = tuple(itertools.product((0, 1), repeat=2))
    likelihoods = np.zeros((len(programs), len(outcomes)), dtype=float)
    for h_index, program in enumerate(programs):
        for o_index, (signal, registration) in enumerate(outcomes):
            observation = ProtectObservation(
                0,
                (None, signal, None),
                None,
                (1, 1, 1),
                0,
                None,
                None,
                (None, None, None),
                (None, registration, None),
                None,
                1.0,
            )
            likelihoods[h_index, o_index] = math.fsum(
                _mode_prior(modes, program.active_modes)
                * _slice_likelihood(
                    observation, modes, program, 0, 0
                )
                for modes in itertools.product(
                    (0, 1), repeat=MODE_SLOTS
                )
            )
    observation_probabilities = priors @ likelihoods
    observation_probabilities /= observation_probabilities.sum()
    posteriors = (
        priors[:, None] * likelihoods
        / (priors @ likelihoods)[None, :]
    )
    joint = priors[:, None] * likelihoods
    joint /= joint.sum()
    exact_ece = 0.0
    exact_accuracy = 0.0
    exact_confidence = 0.0
    exact_coverage = 0.0
    for o_index in range(len(outcomes)):
        predicted = int(np.argmax(posteriors[:, o_index]))
        confidence = float(posteriors[predicted, o_index])
        mass = float(joint[:, o_index].sum())
        correct_mass = float(joint[predicted, o_index])
        exact_accuracy += correct_mass
        exact_confidence += mass * confidence
        exact_ece += abs(correct_mass - mass * confidence)
        order = np.argsort(-posteriors[:, o_index])
        retained: set[int] = set()
        cumulative = 0.0
        for index in order:
            retained.add(int(index))
            cumulative += float(posteriors[int(index), o_index])
            if cumulative >= 0.95:
                break
        exact_coverage += math.fsum(
            float(joint[index, o_index]) for index in retained
        )
    generator = np.random.default_rng(35_000_001)
    flat_joint = joint.reshape(-1)
    draws = generator.choice(
        flat_joint.size, size=sample_size, p=flat_joint
    )
    sampled_confidence = []
    sampled_correct = []
    sampled_covered = []
    for draw in draws:
        truth, o_index = np.unravel_index(int(draw), joint.shape)
        predicted = int(np.argmax(posteriors[:, o_index]))
        sampled_confidence.append(float(posteriors[predicted, o_index]))
        sampled_correct.append(int(predicted == truth))
        order = np.argsort(-posteriors[:, o_index])
        retained = set()
        cumulative = 0.0
        for index in order:
            retained.add(int(index))
            cumulative += float(posteriors[int(index), o_index])
            if cumulative >= 0.95:
                break
        sampled_covered.append(int(truth in retained))
    sampled_ece = 0.0
    confidence_array = np.asarray(sampled_confidence)
    correct_array = np.asarray(sampled_correct, dtype=float)
    for confidence in sorted(set(sampled_confidence)):
        selected = np.isclose(
            confidence_array, confidence, atol=1e-14, rtol=0.0
        )
        sampled_ece += float(selected.mean()) * abs(
            float(confidence_array[selected].mean())
            - float(correct_array[selected].mean())
        )
    return MappingProxyType(
        {
            "priors": tuple(float(value) for value in priors),
            "likelihoods": tuple(
                tuple(float(value) for value in row)
                for row in likelihoods
            ),
            "posteriors": tuple(
                tuple(float(value) for value in row)
                for row in posteriors
            ),
            "exact_ece": float(exact_ece),
            "exact_accuracy_confidence_gap": float(
                abs(exact_accuracy - exact_confidence)
            ),
            "exact_coverage": float(exact_coverage),
            "sampled_ece": float(sampled_ece),
            "sampled_coverage": float(np.mean(sampled_covered)),
            "sampled_coverage_error": float(
                abs(np.mean(sampled_covered) - exact_coverage)
            ),
            "declared_sampling_tolerance": (
                MARGINAL_CALIBRATION_TOLERANCE
            ),
        }
    )


def finite_information_bounds() -> Mapping[str, float]:
    probabilities = (
        0.14,
        0.20,
        0.25,
        0.03,
        0.97,
        0.86,
    )
    bound = max(abs(math.log(p / (1.0 - p))) for p in probabilities)
    return MappingProxyType(
        {
            "B_max_v35_atomic": float(bound),
            "implied_binary_change_bound": float(math.tanh(bound / 4.0)),
        }
    )
