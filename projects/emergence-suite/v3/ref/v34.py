"""V3.4 RELATE: exact partner inference and recursively earned precision.

The scientific posterior ranges over four generic productions:

* L -> local relational precision,
* L -> Y,
* partner action -> relational observations / Y,
* dynamic versus static partner state.

Partner-state names occur only in world construction metadata.  Inference sees
finite state indices, typed observations, interventions, and generic edges.
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


STAGE_VERSION = "V3.4"
DEVELOPMENT_BLOCK = (3_400_000, 3_419_999)
PARTNER_CARDINALITY = 4
RELATIONAL_CHANNELS = (
    "soothing",
    "contingency",
    "pressure",
    "remaining",
    "instability",
)
EDGE_NAMES = ("L_PREC", "L_Y", "PA_RY", "L_TRANSITION")
PROGRAMS = tuple(itertools.product((0, 1), repeat=len(EDGE_NAMES)))
PARTNER_PRIOR = (0.25, 0.25, 0.25, 0.25)
RELATIONAL_BASE = (
    (0.90, 0.90, 0.10, 0.90, 0.10),
    (0.90, 0.20, 0.20, 0.30, 0.40),
    (0.30, 0.30, 0.90, 0.20, 0.60),
    (0.60, 0.50, 0.40, 0.50, 0.90),
)
ACTION_SIGNS = (1.0, 1.0, -1.0, 1.0, -1.0)
STATE_PRECISION = (0.90, 0.65, 0.20, 0.35)
STATE_OUTCOME = (0.85, 0.55, 0.25, 0.40)
BASE_PRECISION = 0.45
ACTION_EFFECT = 0.12
ROOT_GAIN = 0.42
TRANSITION_STAY = 0.88
TOLERANCE = 1e-10


@dataclass(frozen=True)
class RelateStructure:
    l_precision: int
    l_outcome: int
    partner_action: int
    transitions: int

    def __post_init__(self) -> None:
        if any(
            value not in (0, 1)
            for value in (
                self.l_precision,
                self.l_outcome,
                self.partner_action,
                self.transitions,
            )
        ):
            raise ValueError("relational productions are exact binary spikes")


@dataclass(frozen=True)
class RelateConfig:
    partner_pattern: str
    regulation_present: bool
    root_evidence_present: bool
    broadcast: bool = True
    length: int = 48

    def __post_init__(self) -> None:
        if self.partner_pattern not in {
            "reliable",
            "soothing_noncontingent",
            "intrusive",
            "unstable",
            "switch",
        }:
            raise ValueError("invalid partner-pattern constructor")
        if self.length < 2:
            raise ValueError("length must be at least two")


@dataclass(frozen=True)
class RelateObservation:
    time: int
    relational: tuple[int | None, ...]
    regulation_response: int | None
    partner_action: int
    outcome: int | None
    root_evidence: int | None

    def __post_init__(self) -> None:
        if len(self.relational) != len(RELATIONAL_CHANNELS):
            raise ValueError("five typed relational channels are required")


@dataclass(frozen=True)
class RelateWorld:
    seed: int
    config: RelateConfig | None
    truth_structure: RelateStructure
    truth_partner_path: tuple[int, ...]
    truth_root: int
    observations: tuple[RelateObservation, ...]
    exact_log_probability: float
    rng_keys: tuple[tuple[str, int, str, int | str], ...]
    analysis_labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class RelatePosterior:
    programs: tuple[RelateStructure, ...]
    structure_probabilities: tuple[float, ...]
    log_evidence: float
    edge_probabilities: Mapping[str, float]
    q_root: tuple[float, float]
    q_partner: tuple[float, ...]
    smoothed_partner: tuple[tuple[float, ...], ...]
    local_precision: tuple[float, ...]
    global_precision: tuple[float, ...]
    root_log_bf: float
    root_movement: float
    transfer: float
    trust_remaining_after_refusal: float
    transition_probability: float
    switch_onset: int | None
    co_regulated: bool
    latent_posterior: Mapping[str, tuple[float, ...]]
    parameter_posterior: Mapping[str, tuple[float, ...]]
    structure_posterior: Mapping[str, tuple[float, ...]]
    model_evidence: Mapping[str, float]

    def structure_probability(self, structure: RelateStructure) -> float:
        return self.structure_probabilities[self.programs.index(structure)]


@dataclass(frozen=True)
class V34Hyperparameters:
    code_length_scale: float = 1.0
    transition_stay: float = TRANSITION_STAY

    def __post_init__(self) -> None:
        if self.code_length_scale <= 0:
            raise ValueError("code-length scale must be positive")
        if not 0.25 < self.transition_stay < 1.0:
            raise ValueError("transition stay must be in (0.25, 1)")


DEFAULT_HYPERPARAMETERS = V34Hyperparameters()


def make_structure(bits: Sequence[int]) -> RelateStructure:
    return RelateStructure(*(int(value) for value in bits))


STRUCTURES = tuple(make_structure(bits) for bits in PROGRAMS)


def structure_values(structure: RelateStructure) -> Mapping[str, int]:
    return MappingProxyType(
        {
            "L_PREC": structure.l_precision,
            "L_Y": structure.l_outcome,
            "PA_RY": structure.partner_action,
            "L_TRANSITION": structure.transitions,
        }
    )


def _binary_prior(value: int, scale: float) -> float:
    absent = 2.0 ** (-scale)
    present = 2.0 ** (-2.0 * scale)
    return (present if value else absent) / (absent + present)


def structure_log_prior(
    structure: RelateStructure,
    hyperparameters: V34Hyperparameters = DEFAULT_HYPERPARAMETERS,
    restrictions: Mapping[str, tuple[int, ...]] | None = None,
) -> float:
    limits = {} if restrictions is None else dict(restrictions)
    total = 0.0
    for name, value in structure_values(structure).items():
        support = tuple(limits.get(name, (0, 1)))
        if value not in support:
            return -math.inf
        probabilities = np.asarray(
            [
                _binary_prior(candidate, hyperparameters.code_length_scale)
                for candidate in support
            ],
            dtype=float,
        )
        probabilities /= probabilities.sum()
        total += math.log(float(probabilities[support.index(value)]))
    return total


def _rng(
    seed: int,
    component: str,
    event: int | str,
    released_block: tuple[int, int] | None,
    keys: list[tuple[str, int, str, int | str]],
) -> np.random.Generator:
    block = DEVELOPMENT_BLOCK if released_block is None else released_block
    if not block[0] <= int(seed) <= block[1]:
        raise ValueError("seed is outside the authorized V3.4 block")
    key = (STAGE_VERSION, int(seed), str(component), event)
    keys.append(key)
    digest = hashlib.sha256(repr(key).encode("utf-8")).digest()
    return np.random.default_rng(int.from_bytes(digest[:16], "big"))


def _clip_probability(value: float) -> float:
    return float(np.clip(value, 0.02, 0.98))


def transition_matrix(
    structure: RelateStructure,
    hyperparameters: V34Hyperparameters = DEFAULT_HYPERPARAMETERS,
) -> np.ndarray:
    if not structure.transitions:
        return np.eye(PARTNER_CARDINALITY, dtype=float)
    stay = hyperparameters.transition_stay
    matrix = np.full(
        (PARTNER_CARDINALITY, PARTNER_CARDINALITY),
        (1.0 - stay) / (PARTNER_CARDINALITY - 1),
        dtype=float,
    )
    np.fill_diagonal(matrix, stay)
    return matrix


def relational_probability(
    state: int,
    channel: int,
    action: int,
    structure: RelateStructure,
) -> float:
    probability = RELATIONAL_BASE[state][channel]
    if structure.partner_action:
        probability += (
            ACTION_EFFECT
            * (1.0 if action else -1.0)
            * ACTION_SIGNS[channel]
        )
    return _clip_probability(probability)


def regulation_probability(
    state: int, structure: RelateStructure
) -> float:
    return STATE_PRECISION[state] if structure.l_precision else 0.5


def outcome_probability(
    state: int, action: int, structure: RelateStructure
) -> float:
    probability = STATE_OUTCOME[state] if structure.l_outcome else 0.5
    if structure.partner_action:
        probability += ACTION_EFFECT * (1.0 if action else -1.0)
    return _clip_probability(probability)


def local_precision_value(
    state: int, structure: RelateStructure
) -> float:
    return STATE_PRECISION[state] if structure.l_precision else BASE_PRECISION


def root_probability(
    observed: int,
    root_state: int,
    state: int,
    structure: RelateStructure,
    *,
    broadcast: bool,
) -> float:
    local = local_precision_value(state, structure)
    precision = local if broadcast else BASE_PRECISION
    correct = 0.5 + ROOT_GAIN * precision
    return correct if int(observed) == int(root_state) else 1.0 - correct


def observation_likelihood(
    observation: RelateObservation,
    state: int,
    root_state: int,
    structure: RelateStructure,
    *,
    broadcast: bool,
    root_evidence_enabled: bool = True,
    relational_enabled: bool = True,
) -> float:
    result = 1.0
    if relational_enabled:
        for channel, observed in enumerate(observation.relational):
            if observed is not None:
                probability = relational_probability(
                    state,
                    channel,
                    observation.partner_action,
                    structure,
                )
                result *= probability if observed else 1.0 - probability
        if observation.regulation_response is not None:
            probability = regulation_probability(state, structure)
            result *= (
                probability
                if observation.regulation_response
                else 1.0 - probability
            )
        if observation.outcome is not None:
            probability = outcome_probability(
                state, observation.partner_action, structure
            )
            result *= probability if observation.outcome else 1.0 - probability
    if root_evidence_enabled and observation.root_evidence is not None:
        result *= root_probability(
            observation.root_evidence,
            root_state,
            state,
            structure,
            broadcast=broadcast,
        )
    return float(result)


def _forward_backward(
    observations: Sequence[RelateObservation],
    structure: RelateStructure,
    root_state: int,
    *,
    hyperparameters: V34Hyperparameters,
    broadcast: bool,
    root_evidence_enabled: bool,
    relational_enabled: bool,
) -> tuple[float, tuple[np.ndarray, ...], tuple[np.ndarray, ...]]:
    matrix = transition_matrix(structure, hyperparameters)
    likelihoods = tuple(
        np.asarray(
            [
                observation_likelihood(
                    observation,
                    state,
                    root_state,
                    structure,
                    broadcast=broadcast,
                    root_evidence_enabled=root_evidence_enabled,
                    relational_enabled=relational_enabled,
                )
                for state in range(PARTNER_CARDINALITY)
            ],
            dtype=float,
        )
        for observation in observations
    )
    if not likelihoods:
        return 0.0, (), ()
    filtered = []
    scales = []
    predicted = np.asarray(PARTNER_PRIOR, dtype=float)
    log_evidence = 0.0
    for time, likelihood in enumerate(likelihoods):
        if time:
            predicted = filtered[-1] @ matrix
        unnormalized = predicted * likelihood
        scale = float(unnormalized.sum())
        if scale <= 0:
            raise ValueError("zero relational evidence")
        filtered.append(unnormalized / scale)
        scales.append(scale)
        log_evidence += math.log(scale)
    backward = [np.ones(PARTNER_CARDINALITY) for _ in likelihoods]
    for time in range(len(likelihoods) - 2, -1, -1):
        backward[time] = (
            matrix @ (likelihoods[time + 1] * backward[time + 1])
        ) / scales[time + 1]
    smoothed = tuple(
        (filtered[time] * backward[time])
        / float((filtered[time] * backward[time]).sum())
        for time in range(len(likelihoods))
    )
    pairwise = []
    for time in range(len(likelihoods) - 1):
        joint = (
            filtered[time][:, None]
            * matrix
            * (
                likelihoods[time + 1] * backward[time + 1]
            )[None, :]
        )
        pairwise.append(joint / float(joint.sum()))
    return float(log_evidence), smoothed, tuple(pairwise)


def score_world(
    world: RelateWorld,
    *,
    hyperparameters: V34Hyperparameters = DEFAULT_HYPERPARAMETERS,
    restrictions: Mapping[str, tuple[int, ...]] | None = None,
    broadcast: bool | None = None,
    root_evidence_enabled: bool = True,
    relational_enabled: bool = True,
) -> RelatePosterior:
    require_trace_sink("v34.score_world", seed=int(world.seed))
    if world.analysis_labels:
        raise ValueError("analysis labels may not reach V3.4 inference")
    use_broadcast = (
        bool(world.config.broadcast)
        if broadcast is None and world.config is not None
        else True if broadcast is None else bool(broadcast)
    )
    programs = tuple(
        structure
        for structure in STRUCTURES
        if math.isfinite(
            structure_log_prior(
                structure, hyperparameters, restrictions
            )
        )
    )
    log_weights = []
    components = []
    for structure in programs:
        for root_state in (0, 1):
            log_likelihood, smoothed, pairwise = _forward_backward(
                world.observations,
                structure,
                root_state,
                hyperparameters=hyperparameters,
                broadcast=use_broadcast,
                root_evidence_enabled=root_evidence_enabled,
                relational_enabled=relational_enabled,
            )
            log_weights.append(
                structure_log_prior(
                    structure, hyperparameters, restrictions
                )
                + math.log(0.5)
                + log_likelihood
            )
            components.append(
                (structure, root_state, smoothed, pairwise)
            )
    values = np.asarray(log_weights, dtype=float)
    maximum = float(np.max(values))
    log_evidence = maximum + math.log(
        float(np.exp(values - maximum).sum())
    )
    joint = np.exp(values - log_evidence)
    structure_probabilities = tuple(
        float(
            math.fsum(
                joint[index]
                for index, component in enumerate(components)
                if component[0] == structure
            )
        )
        for structure in programs
    )
    root_observed = (
        root_evidence_enabled
        and any(
            item.root_evidence is not None for item in world.observations
        )
    )
    if root_observed:
        q_root_one = float(
            math.fsum(
                joint[index]
                for index, component in enumerate(components)
                if component[1] == 1
            )
        )
        q_root = (1.0 - q_root_one, q_root_one)
        root_log_bf = math.log(q_root[1] / q_root[0])
    else:
        q_root = (0.5, 0.5)
        root_log_bf = 0.0
    count = len(world.observations)
    smoothed_model_average = []
    local_precision = []
    global_precision = []
    for time in range(count):
        q_time = np.zeros(PARTNER_CARDINALITY)
        local = 0.0
        for index, component in enumerate(components):
            structure, _root, smoothed, _pairwise = component
            if not smoothed:
                continue
            q_time += float(joint[index]) * smoothed[time]
            local += float(joint[index]) * float(
                smoothed[time]
                @ np.asarray(
                    [
                        local_precision_value(state, structure)
                        for state in range(PARTNER_CARDINALITY)
                    ]
                )
            )
        smoothed_model_average.append(
            tuple(float(value) for value in q_time)
        )
        local_precision.append(local)
        global_precision.append(local if use_broadcast else BASE_PRECISION)
    occupancy = (
        tuple(
            float(value)
            for value in np.mean(
                np.asarray(smoothed_model_average), axis=0
            )
        )
        if smoothed_model_average
        else PARTNER_PRIOR
    )
    edge_probabilities = MappingProxyType(
        {
            name: float(
                math.fsum(
                    probability
                    for structure, probability in zip(
                        programs, structure_probabilities
                    )
                    if structure_values(structure)[name]
                )
            )
            for name in EDGE_NAMES
        }
    )
    transition_probability = edge_probabilities["L_TRANSITION"]
    switch_probabilities = []
    for time in range(max(count - 1, 0)):
        probability = 0.0
        for index, component in enumerate(components):
            pairwise = component[3]
            if pairwise:
                probability += float(joint[index]) * (
                    1.0 - float(np.trace(pairwise[time]))
                )
        switch_probabilities.append(probability)
    switch_onset = (
        int(np.argmax(switch_probabilities)) + 1
        if switch_probabilities
        else None
    )
    trust = 0.0
    if count:
        final_time = count - 1
        for index, component in enumerate(components):
            structure, _root, smoothed, _pairwise = component
            for state in range(PARTNER_CARDINALITY):
                trust += (
                    float(joint[index])
                    * float(smoothed[final_time][state])
                    * relational_probability(
                        state, 3, 0, structure
                    )
                )
    movement = q_root[1] - 0.5
    posterior = RelatePosterior(
        programs=programs,
        structure_probabilities=structure_probabilities,
        log_evidence=float(log_evidence),
        edge_probabilities=edge_probabilities,
        q_root=q_root,
        q_partner=occupancy,
        smoothed_partner=tuple(smoothed_model_average),
        local_precision=tuple(local_precision),
        global_precision=tuple(global_precision),
        root_log_bf=float(root_log_bf),
        root_movement=float(movement),
        transfer=float(0.7 * movement),
        trust_remaining_after_refusal=float(trust),
        transition_probability=float(transition_probability),
        switch_onset=switch_onset,
        co_regulated=bool(
            occupancy[0] >= 0.6
            and global_precision
            and global_precision[-1] > BASE_PRECISION
        ),
        latent_posterior=MappingProxyType(
            {"L": occupancy, "G": q_root}
        ),
        parameter_posterior=MappingProxyType({}),
        structure_posterior=MappingProxyType(
            {"programs": structure_probabilities}
        ),
        model_evidence=MappingProxyType(
            {"relational_structure": float(log_evidence)}
        ),
    )
    violations = audit_state(posterior)
    if violations:
        raise AssertionError("; ".join(violations))
    return posterior


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


def _sample_observation(
    seed: int,
    time: int,
    state: int,
    root_state: int,
    structure: RelateStructure,
    *,
    regulation_present: bool,
    root_evidence_present: bool,
    broadcast: bool,
    released_block: tuple[int, int] | None,
    keys: list[tuple[str, int, str, int | str]],
) -> RelateObservation:
    action = time % 2
    relational = []
    for channel in range(len(RELATIONAL_CHANNELS)):
        value = _bernoulli(
            seed,
            f"relational:{channel}",
            time,
            relational_probability(state, channel, action, structure),
            released_block,
            keys,
        )
        relational.append(value if regulation_present else None)
    regulation = _bernoulli(
        seed,
        "regulation-response",
        time,
        regulation_probability(state, structure),
        released_block,
        keys,
    )
    outcome = _bernoulli(
        seed,
        "partner-outcome",
        time,
        outcome_probability(state, action, structure),
        released_block,
        keys,
    )
    root = None
    if root_evidence_present:
        # ``_bernoulli`` returns the observed bit, so its parameter must be
        # p(O_G=1), not p(O_G=G).  Keeping this expressed through the public
        # likelihood pins recovery generation to the scorer for either G.
        root = _bernoulli(
            seed,
            "root-evidence",
            time,
            root_probability(
                1,
                root_state,
                state,
                structure,
                broadcast=broadcast,
            ),
            released_block,
            keys,
        )
    return RelateObservation(
        time=time,
        relational=tuple(relational),
        regulation_response=regulation if regulation_present else None,
        partner_action=action,
        outcome=outcome if regulation_present else None,
        root_evidence=root,
    )


def _complete_log_probability(
    structure: RelateStructure,
    root_state: int,
    path: Sequence[int],
    observations: Sequence[RelateObservation],
    *,
    hyperparameters: V34Hyperparameters,
    broadcast: bool,
) -> float:
    total = structure_log_prior(structure, hyperparameters) + math.log(0.5)
    total += math.log(PARTNER_PRIOR[path[0]])
    matrix = transition_matrix(structure, hyperparameters)
    for time, state in enumerate(path):
        if time:
            total += math.log(matrix[path[time - 1], state])
        total += math.log(
            observation_likelihood(
                observations[time],
                state,
                root_state,
                structure,
                broadcast=broadcast,
            )
        )
    return float(total)


def _pattern_path(
    seed: int,
    config: RelateConfig,
    structure: RelateStructure,
    released_block: tuple[int, int] | None,
    keys: list[tuple[str, int, str, int | str]],
) -> tuple[int, ...]:
    if config.partner_pattern == "reliable":
        return tuple([0] * config.length)
    if config.partner_pattern == "soothing_noncontingent":
        return tuple([1] * config.length)
    if config.partner_pattern == "intrusive":
        return tuple([2] * config.length)
    if config.partner_pattern == "switch":
        onset = config.length // 2
        return tuple([0] * onset + [2] * (config.length - onset))
    matrix = transition_matrix(
        replace_structure(structure, transitions=1)
    )
    path = [
        int(
            _rng(
                seed, "partner-path-initial", 0, released_block, keys
            ).choice(PARTNER_CARDINALITY, p=PARTNER_PRIOR)
        )
    ]
    for time in range(1, config.length):
        path.append(
            int(
                _rng(
                    seed,
                    "partner-path-transition",
                    time,
                    released_block,
                    keys,
                ).choice(PARTNER_CARDINALITY, p=matrix[path[-1]])
            )
        )
    return tuple(path)


def replace_structure(
    structure: RelateStructure, **changes: int
) -> RelateStructure:
    values = dict(structure_values(structure))
    values.update(changes)
    return RelateStructure(
        values["L_PREC"],
        values["L_Y"],
        values["PA_RY"],
        values["L_TRANSITION"],
    )


def generate_world(
    seed: int,
    config: RelateConfig,
    *,
    structure: RelateStructure | None = None,
    released_block: tuple[int, int] | None = None,
    hyperparameters: V34Hyperparameters = DEFAULT_HYPERPARAMETERS,
) -> RelateWorld:
    require_trace_sink("v34.generate_world", seed=int(seed))
    keys: list[tuple[str, int, str, int | str]] = []
    truth = structure or RelateStructure(
        1,
        1,
        1,
        int(config.partner_pattern in {"unstable", "switch"}),
    )
    path = _pattern_path(seed, config, truth, released_block, keys)
    root_state = 1
    observations = tuple(
        _sample_observation(
            seed,
            time,
            state,
            root_state,
            truth,
            regulation_present=config.regulation_present,
            root_evidence_present=(
                config.root_evidence_present
                and time >= config.length - 4
            ),
            broadcast=config.broadcast,
            released_block=released_block,
            keys=keys,
        )
        for time, state in enumerate(path)
    )
    exact = _complete_log_probability(
        truth,
        root_state,
        path,
        observations,
        hyperparameters=hyperparameters,
        broadcast=config.broadcast,
    )
    return RelateWorld(
        int(seed),
        config,
        truth,
        path,
        root_state,
        observations,
        exact,
        tuple(keys),
    )


def generate_recovery_world(
    seed: int,
    *,
    length: int = 48,
    released_block: tuple[int, int] | None = None,
    hyperparameters: V34Hyperparameters = DEFAULT_HYPERPARAMETERS,
) -> RelateWorld:
    require_trace_sink("v34.generate_recovery_world", seed=int(seed))
    keys: list[tuple[str, int, str, int | str]] = []
    bits = []
    for index, name in enumerate(EDGE_NAMES):
        probability = _binary_prior(1, hyperparameters.code_length_scale)
        bits.append(
            _bernoulli(
                seed,
                f"recovery-structure:{name}",
                index,
                probability,
                released_block,
                keys,
            )
        )
    structure = make_structure(bits)
    root_state = _bernoulli(
        seed, "recovery-root", 0, 0.5, released_block, keys
    )
    matrix = transition_matrix(structure, hyperparameters)
    initial = _rng(
        seed, "recovery-path-initial", 0, released_block, keys
    )
    path = [int(initial.choice(PARTNER_CARDINALITY, p=PARTNER_PRIOR))]
    for time in range(1, length):
        path.append(
            int(
                _rng(
                    seed,
                    "recovery-path-transition",
                    time,
                    released_block,
                    keys,
                ).choice(PARTNER_CARDINALITY, p=matrix[path[-1]])
            )
        )
    observations = tuple(
        _sample_observation(
            seed,
            time,
            state,
            root_state,
            structure,
            regulation_present=True,
            root_evidence_present=time >= length - 4,
            broadcast=True,
            released_block=released_block,
            keys=keys,
        )
        for time, state in enumerate(path)
    )
    exact = _complete_log_probability(
        structure,
        root_state,
        path,
        observations,
        hyperparameters=hyperparameters,
        broadcast=True,
    )
    return RelateWorld(
        int(seed),
        None,
        structure,
        tuple(path),
        root_state,
        observations,
        exact,
        tuple(keys),
    )


def exact_complete_log_probability(
    world: RelateWorld,
    *,
    hyperparameters: V34Hyperparameters = DEFAULT_HYPERPARAMETERS,
) -> float:
    require_trace_sink(
        "v34.exact_complete_log_probability", seed=int(world.seed)
    )
    broadcast = bool(world.config.broadcast) if world.config else True
    return _complete_log_probability(
        world.truth_structure,
        world.truth_root,
        world.truth_partner_path,
        world.observations,
        hyperparameters=hyperparameters,
        broadcast=broadcast,
    )


def finite_information_bounds() -> Mapping[str, float]:
    relational = 0.0
    for observed in (0, 1):
        for channel in range(len(RELATIONAL_CHANNELS)):
            for action in (0, 1):
                values = []
                for structure in STRUCTURES:
                    for state in range(PARTNER_CARDINALITY):
                        probability = relational_probability(
                            state, channel, action, structure
                        )
                        values.append(
                            probability if observed else 1.0 - probability
                        )
                relational = max(
                    relational,
                    math.log(max(values) / min(values)),
                )
    root = 0.0
    for observed in (0, 1):
        values = [
            root_probability(
                observed,
                root_state,
                state,
                structure,
                broadcast=True,
            )
            for structure in STRUCTURES
            for state in range(PARTNER_CARDINALITY)
            for root_state in (0, 1)
        ]
        root = max(root, math.log(max(values) / min(values)))
    return MappingProxyType(
        {
            "B_max_v34_relational": float(relational),
            "B_max_v34_root": float(root),
            "implied_relational_binary_change_bound": math.tanh(
                relational / 4.0
            ),
            "implied_root_binary_change_bound": math.tanh(root / 4.0),
        }
    )
