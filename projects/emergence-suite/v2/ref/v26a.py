"""V2.6a exact latent-partner process and co-regulation reference."""

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
PARAMETERS = json.loads((ROOT / "protocols" / "v2.6a-parameters.json").read_text())
PARTNER_STATES = tuple(PARAMETERS["partner_states"])
STATE_INDEX = {name: index for index, name in enumerate(PARTNER_STATES)}
PRIOR = np.asarray(PARAMETERS["partner_prior"], dtype=float)
EMISSIONS = np.asarray(
    [PARAMETERS["emission_success_probabilities"][name] for name in PARTNER_STATES],
    dtype=float,
)
LOCAL_PRECISION = np.asarray(PARAMETERS["relational_precision_by_state"], dtype=float)
ROOT_PRIOR = np.asarray(PARAMETERS["root_prior"], dtype=float)
EPOCH_B_DEVELOPMENT_BLOCK = tuple(PARAMETERS["epoch_b_development_block"])
TOLERANCE = float(PARAMETERS["semantic_tolerance"])
CHANNELS = ("regulation", "remaining", "respect", "trust")


def _transition_matrix() -> np.ndarray:
    stay = float(PARAMETERS["transition_stay_probability"])
    matrix = np.full((4, 4), (1.0 - stay) / 3.0, dtype=float)
    np.fill_diagonal(matrix, stay)
    matrix.setflags(write=False)
    return matrix


TRANSITION = _transition_matrix()


@dataclass(frozen=True)
class PartnerObservation:
    relational: tuple[int | None, int | None, int | None, int | None]
    root: int | None = None


@dataclass(frozen=True)
class PartnerWorld:
    seed: int
    truth_family: str
    truth_path: tuple[int, ...]
    observations: tuple[PartnerObservation, ...]
    switching: bool


@dataclass(frozen=True)
class PartnerScore:
    q_partner: np.ndarray
    q_root: np.ndarray
    filtered_partner: tuple[np.ndarray, ...]
    smoothed_partner: tuple[np.ndarray, ...]
    pairwise_transitions: tuple[np.ndarray, ...]
    local_precision: tuple[float, ...]
    global_precision: tuple[float, ...]
    root_log_bf: tuple[float, ...]
    root_movement: float
    transfer: float
    co_regulated: bool
    local_arousal: float
    switch_rate: float
    switch_onset: int | None
    future_precision_forecast: float
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
            EPOCH_B_DEVELOPMENT_BLOCK if released_block is None else released_block
        ),
    )


def _normalize(values: np.ndarray) -> np.ndarray:
    total = float(np.sum(values))
    if total <= 0.0:
        raise ValueError("cannot normalize nonpositive mass")
    return np.asarray(values, dtype=float) / total


def relational_likelihood(
    relational: Sequence[int | None],
    state_index: int,
) -> float:
    """Normalized observed-data likelihood for one partner state."""
    result = 1.0
    for observed, probability in zip(relational, EMISSIONS[state_index]):
        if observed is not None:
            result *= probability if int(observed) == 1 else 1.0 - probability
    return float(result)


def emission_vector(observation: PartnerObservation) -> np.ndarray:
    return np.asarray(
        [relational_likelihood(observation.relational, index) for index in range(4)],
        dtype=float,
    )


def hmm_inference(
    observations: Sequence[PartnerObservation],
    *,
    initial_prior: Sequence[float] | None = None,
    transition: np.ndarray | None = None,
) -> tuple[
    tuple[np.ndarray, ...],
    tuple[np.ndarray, ...],
    tuple[np.ndarray, ...],
    float,
]:
    """Exact scaled forward/backward inference for the single partner latent."""
    sequence = tuple(observations)
    prior = _normalize(PRIOR.copy() if initial_prior is None else np.asarray(initial_prior, dtype=float).copy())
    matrix = np.asarray(TRANSITION if transition is None else transition, dtype=float).copy()
    if matrix.shape != (4, 4):
        raise ValueError("transition must be 4x4")
    if float(np.max(np.abs(matrix.sum(axis=1) - 1.0))) > TOLERANCE:
        raise ValueError("transition rows must normalize")
    emissions = tuple(emission_vector(item) for item in sequence)
    filtered: list[np.ndarray] = []
    scales: list[float] = []
    predicted = prior
    log_evidence = 0.0
    for time, likelihoods in enumerate(emissions):
        if time:
            predicted = filtered[-1] @ matrix
        unnormalized = predicted * likelihoods
        scale = float(unnormalized.sum())
        if scale <= 0.0:
            raise ValueError("zero evidence")
        filtered.append(unnormalized / scale)
        scales.append(scale)
        log_evidence += math.log(scale)
    if not sequence:
        return (), (), (), 0.0
    backward = [np.ones(4, dtype=float) for _ in sequence]
    for time in range(len(sequence) - 2, -1, -1):
        backward[time] = (
            matrix @ (emissions[time + 1] * backward[time + 1])
        ) / scales[time + 1]
    smoothed = tuple(
        _normalize(filtered[time] * backward[time]) for time in range(len(sequence))
    )
    pairwise: list[np.ndarray] = []
    for time in range(len(sequence) - 1):
        joint = (
            filtered[time][:, None]
            * matrix
            * (emissions[time + 1] * backward[time + 1])[None, :]
        )
        pairwise.append(joint / float(joint.sum()))
    return tuple(filtered), smoothed, tuple(pairwise), log_evidence


def independent_channel_inference(
    observations: Sequence[PartnerObservation],
    *,
    transition: np.ndarray,
) -> tuple[
    tuple[np.ndarray, ...],
    tuple[np.ndarray, ...],
    tuple[np.ndarray, ...],
    float,
]:
    """Lesion path: infer each channel separately, without a shared latent."""
    channel_results = []
    for axis in range(4):
        isolated = tuple(
            PartnerObservation(
                tuple(
                    value if index == axis else None
                    for index, value in enumerate(item.relational)
                ),
                None,
            )
            for item in observations
        )
        channel_results.append(
            hmm_inference(isolated, transition=transition)
        )
    filtered = tuple(
        _normalize(
            np.mean(
                [result[0][time] for result in channel_results], axis=0
            )
        )
        for time in range(len(observations))
    )
    smoothed = tuple(
        _normalize(
            np.mean(
                [result[1][time] for result in channel_results], axis=0
            )
        )
        for time in range(len(observations))
    )
    pairwise = tuple(
        np.mean(
            [result[2][time] for result in channel_results], axis=0
        )
        for time in range(max(len(observations) - 1, 0))
    )
    log_evidence = float(sum(result[3] for result in channel_results))
    return filtered, smoothed, pairwise, log_evidence


def root_probability(observed: int, root_state: int, precision: float) -> float:
    correct = 0.5 + float(PARAMETERS["root_likelihood_gain"]) * float(precision)
    return correct if int(observed) == int(root_state) else 1.0 - correct


def score(
    observations: Iterable[PartnerObservation],
    *,
    broadcast: bool = True,
    fixed_g: int | None = None,
    partner_precision_enabled: bool = True,
    root_evidence_enabled: bool = True,
    transition_learning_enabled: bool = True,
    shared_partner_latent: bool = True,
) -> PartnerScore:
    sequence = tuple(observations)
    inference_transition = (
        TRANSITION if transition_learning_enabled else np.eye(4, dtype=float)
    )
    if shared_partner_latent:
        filtered, smoothed, pairwise, log_evidence = hmm_inference(
            sequence, transition=inference_transition
        )
    else:
        filtered, smoothed, pairwise, log_evidence = (
            independent_channel_inference(
                sequence, transition=inference_transition
            )
        )
    prior_local = float(PRIOR @ LOCAL_PRECISION)
    local = tuple(
        float(q @ LOCAL_PRECISION) if partner_precision_enabled else prior_local
        for q in filtered
    )
    base = float(PARAMETERS["base_global_precision"])
    gain = float(PARAMETERS["broadcast_strength"])
    global_precision = tuple(
        float(np.clip(base + gain * (value - prior_local), 0.0, 1.0))
        if broadcast
        else base
        for value in local
    )
    q_root = ROOT_PRIOR.copy()
    root_bfs: list[float] = []
    for observation, precision in zip(sequence, global_precision):
        if observation.root is None or not root_evidence_enabled:
            root_bfs.append(0.0)
            continue
        likelihoods = np.asarray(
            [
                root_probability(observation.root, root_state, precision)
                for root_state in (0, 1)
            ]
        )
        root_bfs.append(float(math.log(likelihoods[1] / likelihoods[0])))
        q_root = _normalize(q_root * likelihoods)
    if fixed_g is not None:
        q_root = np.asarray([1.0, 0.0] if int(fixed_g) == 0 else [0.0, 1.0])
    occupancy = _normalize(np.sum(np.asarray(smoothed), axis=0)) if smoothed else PRIOR.copy()
    expected_switches = float(
        sum(1.0 - float(np.trace(item)) for item in pairwise)
    )
    switch_rate = expected_switches / max(len(sequence) - 1, 1)
    if pairwise:
        switch_probabilities = np.asarray(
            [1.0 - float(np.trace(item)) for item in pairwise]
        )
        onset = int(np.argmax(switch_probabilities)) + 1
    else:
        onset = None
    forecast = float(
        (
            filtered[-1] @ inference_transition @ LOCAL_PRECISION
            if filtered
            else prior_local
        )
    )
    movement = float(q_root[1] - ROOT_PRIOR[1])
    transfer = 0.0 if fixed_g is not None else float(PARAMETERS["transfer_strength"]) * movement
    evidence_weights = np.exp(
        np.asarray([log_evidence] * 4, dtype=float)
        - max(float(log_evidence), 0.0)
    )
    state = ProtocolState(
        posterior_store={"L": occupancy.copy(), "G": q_root.copy()},
        parameter_posterior_store={
            "switch_beta": np.asarray(
                [1.0 + expected_switches, 1.0 + max(len(sequence) - 1 - expected_switches, 0.0)]
            ),
            "local_precision": np.asarray([1e-12 + (local[-1] if local else prior_local)]),
        },
        evidence_store={
            name: float(max(value, np.finfo(float).tiny))
            for name, value in zip(PARTNER_STATES, evidence_weights)
        },
        metadata=MappingProxyType(
            {
                "stage": "V2.6a",
                "broadcast": bool(broadcast),
                "fixed_g": fixed_g is not None,
                "partner_precision_enabled": bool(partner_precision_enabled),
                "root_evidence_enabled": bool(root_evidence_enabled),
                "transition_learning_enabled": bool(transition_learning_enabled),
                "shared_partner_latent": bool(shared_partner_latent),
            }
        ),
    )
    audit_one_posterior(state)
    q_reliable = float(occupancy[STATE_INDEX["reliable_contingent"]])
    return PartnerScore(
        q_partner=occupancy,
        q_root=q_root,
        filtered_partner=filtered,
        smoothed_partner=smoothed,
        pairwise_transitions=pairwise,
        local_precision=local,
        global_precision=global_precision,
        root_log_bf=tuple(root_bfs),
        root_movement=movement,
        transfer=transfer,
        co_regulated=(
            q_reliable >= float(PARAMETERS["reliable_readout_minimum"])
            and bool(global_precision)
            and global_precision[-1] > base
        ),
        local_arousal=float(occupancy[1] + occupancy[2]),
        switch_rate=switch_rate,
        switch_onset=onset,
        future_precision_forecast=forecast,
        log_evidence=log_evidence,
        state=state,
    )


def sample_observation(
    seed: int,
    time: int,
    *,
    state_index: int,
    root: int | None = None,
    missingness: float = 0.0,
    namespace: str,
    released_block: tuple[int, int] | None = None,
    success_probabilities: Sequence[float] | None = None,
) -> PartnerObservation:
    rng = _rng(seed, f"v26a-{namespace}-{time}", released_block)
    probabilities = (
        EMISSIONS[state_index]
        if success_probabilities is None
        else np.asarray(success_probabilities, dtype=float)
    )
    values: list[int | None] = [
        int(rng.random() < probability) for probability in probabilities
    ]
    for axis in range(4):
        if rng.random() < missingness:
            values[axis] = None
    return PartnerObservation(tuple(values), root)


def generate_robustness_world(
    seed: int,
    *,
    scenario: str,
    length: int | None = None,
    released_block: tuple[int, int] | None = None,
) -> PartnerWorld:
    """Declared Gate-5 misspecification and composition sweep constructor."""
    count = int(PARAMETERS["gate3_length"] if length is None else length)
    reliable = STATE_INDEX["reliable_contingent"]
    family_state = {
        "soothing_control": STATE_INDEX["soothing_noncontingent"],
        "intrusive_control": STATE_INDEX["intrusive"],
    }.get(scenario, reliable)
    path = [family_state] * count
    if scenario in {"switch_low", "switch_high"}:
        stay = 0.98 if scenario == "switch_low" else 0.75
        transition = np.full((4, 4), (1.0 - stay) / 3.0)
        np.fill_diagonal(transition, stay)
        rng = _rng(seed, f"v26a-robustness-{scenario}-path", released_block)
        path = [int(rng.choice(4, p=PRIOR))]
        for _ in range(1, count):
            path.append(int(rng.choice(4, p=transition[path[-1]])))
    elif scenario == "context_return":
        first = count // 3
        second = (2 * count) // 3
        path = (
            [reliable] * first
            + [STATE_INDEX["intrusive"]] * (second - first)
            + [reliable] * (count - second)
        )
    observations: list[PartnerObservation] = []
    for time, state in enumerate(path):
        probabilities = EMISSIONS[state].copy()
        if scenario == "reliability_high" and state == reliable:
            probabilities = np.asarray([0.95, 0.95, 0.95, 0.95])
        elif scenario == "reliability_low" and state == reliable:
            probabilities = np.asarray([0.75, 0.75, 0.75, 0.75])
        elif scenario == "ambiguity_high":
            probabilities = 0.5 + 0.45 * (probabilities - 0.5)
        elif scenario == "precision_low":
            probabilities = 0.5 + 0.65 * (probabilities - 0.5)
        root_count = {
            "root_weak": 1,
            "root_strong": 4,
        }.get(scenario, 1)
        root = 1 if time >= count - root_count else None
        missingness = 0.35 if scenario == "missingness" else 0.0
        observation = sample_observation(
            seed,
            time,
            state_index=state,
            root=root,
            missingness=missingness,
            namespace=f"robustness-{scenario}",
            released_block=released_block,
            success_probabilities=probabilities,
        )
        if scenario == "regulation_weak":
            observation = PartnerObservation(
                (
                    observation.relational[0],
                    observation.relational[1],
                    None,
                    None,
                ),
                observation.root,
            )
        observations.append(observation)
    counts = np.bincount(path, minlength=4)
    majority = int(np.flatnonzero(counts == counts.max())[0])
    return PartnerWorld(
        seed=seed,
        truth_family=PARTNER_STATES[majority],
        truth_path=tuple(path),
        observations=tuple(observations),
        switching=any(left != right for left, right in zip(path, path[1:])),
    )


def generate_recovery_world(
    seed: int,
    *,
    length: int | None = None,
    released_block: tuple[int, int] | None = None,
) -> PartnerWorld:
    """Draw a recovery world from the exact frozen scorer process."""
    count = int(PARAMETERS["gate2_length"] if length is None else length)
    path_rng = _rng(seed, "v26a-recovery-partner-path", released_block)
    path = [int(path_rng.choice(4, p=PRIOR))]
    for _ in range(1, count):
        path.append(int(path_rng.choice(4, p=TRANSITION[path[-1]])))
    counts = np.bincount(path, minlength=4)
    majority = int(np.flatnonzero(counts == counts.max())[0])
    truth_family = PARTNER_STATES[majority]
    switching = any(left != right for left, right in zip(path, path[1:]))
    observations = tuple(
        sample_observation(
            seed,
            time,
            state_index=state,
            namespace="recovery",
            released_block=released_block,
        )
        for time, state in enumerate(path)
    )
    return PartnerWorld(seed, truth_family, tuple(path), observations, switching)


def generate_factorial_world(
    seed: int,
    *,
    regulation_present: bool,
    root_evidence_present: bool,
    length: int | None = None,
    released_block: tuple[int, int] | None = None,
) -> PartnerWorld:
    count = int(PARAMETERS["gate3_length"] if length is None else length)
    reliable = STATE_INDEX["reliable_contingent"]
    observations = []
    for time in range(count):
        root = 1 if root_evidence_present and time == count - 1 else None
        if regulation_present:
            observations.append(
                sample_observation(
                    seed,
                    time,
                    state_index=reliable,
                    root=root,
                    namespace="factorial-reliable",
                    released_block=released_block,
                )
            )
        else:
            observations.append(PartnerObservation((None, None, None, None), root))
    return PartnerWorld(
        seed, "reliable_contingent", tuple([reliable] * count), tuple(observations), False
    )


def generate_control_world(
    seed: int,
    *,
    partner_family: str,
    length: int | None = None,
    root_evidence_present: bool = True,
    released_block: tuple[int, int] | None = None,
) -> PartnerWorld:
    count = int(PARAMETERS["gate3_length"] if length is None else length)
    state = STATE_INDEX[partner_family]
    observations = tuple(
        sample_observation(
            seed,
            time,
            state_index=state,
            root=(1 if root_evidence_present and time == count - 1 else None),
            namespace=f"control-{partner_family}",
            released_block=released_block,
        )
        for time in range(count)
    )
    return PartnerWorld(seed, partner_family, tuple([state] * count), observations, False)


def generate_switch_world(
    seed: int,
    *,
    length: int | None = None,
    released_block: tuple[int, int] | None = None,
) -> PartnerWorld:
    count = int(PARAMETERS["gate3_length"] if length is None else length)
    first = STATE_INDEX["reliable_contingent"]
    second = STATE_INDEX["intrusive"]
    onset = count // 2
    path = tuple([first] * onset + [second] * (count - onset))
    observations = tuple(
        sample_observation(
            seed,
            time,
            state_index=state,
            namespace="switch-control",
            released_block=released_block,
        )
        for time, state in enumerate(path)
    )
    return PartnerWorld(seed, "reliable_contingent", path, observations, True)


def finite_information_bounds() -> dict[str, float]:
    relational_atoms = tuple(itertools.product((0, 1), repeat=4))
    relational = 0.0
    for atom in relational_atoms:
        probabilities = np.asarray(
            [relational_likelihood(atom, state) for state in range(4)]
        )
        relational = max(
            relational,
            float(np.max(np.log(probabilities[:, None] / probabilities[None, :]))),
        )
    root = 0.0
    for precision in (0.0, 1.0):
        for observed in (0, 1):
            probabilities = np.asarray(
                [root_probability(observed, state, precision) for state in (0, 1)]
            )
            root = max(root, abs(float(math.log(probabilities[1] / probabilities[0]))))
    return {
        "B_max_v26a_relational": relational,
        "B_max_v26a_root": root,
        "implied_relational_binary_change_bound": math.tanh(relational / 4.0),
        "implied_root_binary_change_bound": math.tanh(root / 4.0),
    }
