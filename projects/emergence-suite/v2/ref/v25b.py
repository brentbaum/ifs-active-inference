"""V2.5b exact structural-reduction lattice and do-over evidence path."""

from __future__ import annotations

import functools
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
from . import v25a_completion as v25a


ROOT = Path(__file__).resolve().parents[1]
PARAMETERS = json.loads(
    (ROOT / "protocols" / "v2.5b-parameters.json").read_text()
)
STRUCTURES = tuple(PARAMETERS["structure_order"])
STRUCTURE_BITS = np.asarray(
    [[int(bit) for bit in label] for label in STRUCTURES], dtype=int
)
STRUCTURE_INDEX = {label: index for index, label in enumerate(STRUCTURES)}
PRIOR = np.asarray(PARAMETERS["structure_prior"], dtype=float)
ATOMS = v25a.ATOM_ARRAY
CHANNELS = v25a.CHANNELS
EDGE_CHANNELS = (1, 2, 3)  # W, Pi, Y; identity is C at index 4.
EPOCH_B_DEVELOPMENT_BLOCK = (1_000_000, 1_899_999)
TOLERANCE = float(PARAMETERS["semantic_tolerance"])


@dataclass(frozen=True)
class ReductionWorld:
    seed: int
    truth_structure: str
    precision: float
    context_regime: str
    episodes: tuple[v25a.Episode, ...]


@dataclass(frozen=True)
class MaterialReduction:
    material: bool
    first_time: int | None
    unique_000: bool
    q_000: float
    bf_000_111: float
    consecutive_count: int
    neutral_survives: bool


@dataclass(frozen=True)
class ReductionScore:
    q_structure: np.ndarray
    log_evidence_by_structure: np.ndarray
    posterior_trajectory: tuple[np.ndarray, ...]
    pairwise_000_111_log_bf: tuple[float, ...]
    material_reduction: MaterialReduction
    expected_edges: np.ndarray
    state: ProtocolState


def _normalize(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    return array / float(array.sum())


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


def _coupling_statistic(structure: str) -> np.ndarray:
    bits = STRUCTURE_BITS[STRUCTURE_INDEX[structure]]
    identity = 2 * ATOMS[:, 4] - 1
    result = np.zeros(len(ATOMS), dtype=float)
    for exists, channel in zip(bits, EDGE_CHANNELS):
        if exists:
            result += identity * (2 * ATOMS[:, channel] - 1)
    return result


@functools.lru_cache(maxsize=None)
def joint_table(
    cue: int,
    context: int,
    structure: str,
    precision: float,
) -> np.ndarray:
    """Exact normalized candidate table preserving V2.5a atomic marginals."""
    if structure not in STRUCTURE_INDEX:
        raise ValueError("unknown burden-coupling structure")
    marginals = v25a.channel_marginals(cue, context)
    base = v25a.product_table(marginals)
    if structure == "000" or float(precision) == 0.0:
        output = base
    else:
        strength = float(PARAMETERS["coupling_strength"]) * float(precision)
        output = base * np.exp(strength * _coupling_statistic(structure))
        output /= output.sum()
        tolerance = float(PARAMETERS["ipf_tolerance"])
        for _ in range(int(PARAMETERS["ipf_max_iterations"])):
            for axis, target in enumerate(marginals):
                mask = ATOMS[:, axis] == 1
                output[mask] *= target / float(output[mask].sum())
                output[~mask] *= (1.0 - target) / float(output[~mask].sum())
                output /= output.sum()
            error = max(
                abs(float(output[ATOMS[:, axis] == 1].sum()) - target)
                for axis, target in enumerate(marginals)
            )
            if error <= tolerance:
                break
        else:
            raise RuntimeError("V2.5b IPF did not converge")
    output = np.asarray(output / output.sum(), dtype=float)
    output.setflags(write=False)
    return output


def likelihood(
    episode: v25a.Episode,
    structure: str,
    precision: float,
    *,
    presentation: str = "joint",
) -> float:
    """One likelihood API for observed and imaginal V2.5a episodes."""
    if presentation == "joint":
        return v25a._episode_probability(
            joint_table(
                episode.cue, episode.context, structure, float(precision)
            ),
            episode.values,
        )
    if presentation == "marginal":
        return v25a.atomic_probability(
            episode.cue, episode.context, episode.values
        )
    raise ValueError("presentation must be joint or marginal")


def _condition(q: np.ndarray, log_bf: float, consecutive: int) -> tuple[bool, int]:
    index_000 = STRUCTURE_INDEX["000"]
    index_111 = STRUCTURE_INDEX["111"]
    unique = int(np.argmax(q)) == index_000 and int(np.sum(q == q.max())) == 1
    bf = math.exp(min(log_bf, 700.0))
    current = (
        unique
        and float(q[index_000])
        >= float(PARAMETERS["material_reduction"]["q_000_minimum"])
        and bf >= float(
            PARAMETERS["material_reduction"]["bf_000_111_minimum"]
        )
    )
    return current, consecutive + 1 if current else 0


def score(
    episodes: Iterable[v25a.Episode],
    *,
    precision: float,
    initial_prior: Sequence[float] | None = None,
    presentations: Sequence[str] | None = None,
) -> ReductionScore:
    sequence = tuple(episodes)
    modes = (
        tuple("joint" for _ in sequence)
        if presentations is None
        else tuple(presentations)
    )
    if len(modes) != len(sequence):
        raise ValueError("presentation count differs from episode count")
    prior = _normalize(PRIOR if initial_prior is None else np.asarray(initial_prior))
    q = prior.copy()
    trajectory = [q.copy()]
    log_evidence = np.zeros(len(STRUCTURES), dtype=float)
    log_bfs = []
    first_time = None
    consecutive = 0
    for time, (episode, mode) in enumerate(zip(sequence, modes), start=1):
        probabilities = np.asarray(
            [
                likelihood(
                    episode, structure, precision, presentation=mode
                )
                for structure in STRUCTURES
            ],
            dtype=float,
        )
        log_evidence += np.log(probabilities)
        q = _normalize(q * probabilities)
        trajectory.append(q.copy())
        log_bf = float(
            log_evidence[STRUCTURE_INDEX["000"]]
            - log_evidence[STRUCTURE_INDEX["111"]]
        )
        log_bfs.append(log_bf)
        current, consecutive = _condition(q, log_bf, consecutive)
        if (
            first_time is None
            and current
            and consecutive
            >= int(
                PARAMETERS["material_reduction"][
                    "consecutive_scored_observations"
                ]
            )
        ):
            first_time = time
    final_log_bf = (
        log_bfs[-1]
        if log_bfs
        else 0.0
    )
    current, final_consecutive = _condition(
        q, final_log_bf, max(consecutive - 1, 0)
    )
    neutral = v25a.Episode(0, 0, (None,) * len(CHANNELS))
    neutral_probabilities = np.asarray(
        [likelihood(neutral, structure, precision) for structure in STRUCTURES]
    )
    neutral_q = _normalize(q * neutral_probabilities)
    neutral_survives = float(np.max(np.abs(neutral_q - q))) <= TOLERANCE
    index_000 = STRUCTURE_INDEX["000"]
    unique = (
        int(np.argmax(q)) == index_000
        and int(np.sum(q == q.max())) == 1
    )
    material = (
        first_time is not None
        and current
        and final_consecutive >= 3
        and neutral_survives
    )
    expected_edges = q @ STRUCTURE_BITS
    state = ProtocolState(
        posterior_store={"H_Z": q.copy()},
        parameter_posterior_store={
            "Z_W_Z_Pi_Z_Y": np.asarray(expected_edges, dtype=float)
        },
        evidence_store={
            structure: math.exp(max(float(value), -700.0))
            for structure, value in zip(STRUCTURES, log_evidence)
        },
        metadata=MappingProxyType({"stage": "V2.5b"}),
    )
    audit_one_posterior(state)
    return ReductionScore(
        q_structure=q,
        log_evidence_by_structure=log_evidence,
        posterior_trajectory=tuple(trajectory),
        pairwise_000_111_log_bf=tuple(log_bfs),
        material_reduction=MaterialReduction(
            material=material,
            first_time=first_time,
            unique_000=unique,
            q_000=float(q[index_000]),
            bf_000_111=math.exp(min(final_log_bf, 700.0)),
            consecutive_count=final_consecutive,
            neutral_survives=neutral_survives,
        ),
        expected_edges=np.asarray(expected_edges),
        state=state,
    )


def sample_episode(
    seed: int,
    event: int,
    *,
    cue: int,
    context: int,
    structure: str,
    precision: float,
    missingness: float,
    namespace: str,
    released_block: tuple[int, int] | None = None,
) -> v25a.Episode:
    rng = _rng(seed, f"v25b-{namespace}-{event}", released_block)
    table = joint_table(cue, context, structure, precision)
    atom = ATOMS[int(rng.choice(len(ATOMS), p=table))]
    values: list[int | None] = [int(value) for value in atom]
    for axis in range(len(values)):
        if rng.random() < missingness:
            values[axis] = None
    return v25a.Episode(cue, context, tuple(values))


def generate_world(
    seed: int,
    *,
    truth_structure: str,
    length: int,
    precision: float | None = None,
    context_regime: str = "return",
    cue_count: int = 3,
    missingness: float | None = None,
    released_block: tuple[int, int] | None = None,
) -> ReductionWorld:
    effective_precision = float(
        PARAMETERS["primary_precision"] if precision is None else precision
    )
    missing = float(
        PARAMETERS["primary_missingness"]
        if missingness is None
        else missingness
    )
    contexts = v25a.context_path(length, context_regime)
    offset = int(
        _rng(seed, "v25b-cue-offset", released_block).integers(0, cue_count)
    )
    episodes = tuple(
        sample_episode(
            seed,
            time,
            cue=(time + offset) % cue_count,
            context=context,
            structure=truth_structure,
            precision=effective_precision,
            missingness=missing,
            namespace="observed",
            released_block=released_block,
        )
        for time, context in enumerate(contexts)
    )
    return ReductionWorld(
        seed=seed,
        truth_structure=truth_structure,
        precision=effective_precision,
        context_regime=context_regime,
        episodes=episodes,
    )


def do_over_episodes(
    seed: int,
    *,
    count: int,
    precision: float,
    structure: str = "000",
    presentation: str = "joint",
    released_block: tuple[int, int] | None = None,
) -> tuple[tuple[v25a.Episode, ...], tuple[str, ...]]:
    """Sample imaginal episodes; no reduction or outcome write exists."""
    episodes = tuple(
        sample_episode(
            seed,
            event,
            cue=event % 3,
            context=1,
            structure=structure,
            precision=precision,
            missingness=0.0,
            namespace="imaginal-do-over",
            released_block=released_block,
        )
        for event in range(count)
    )
    return episodes, tuple(presentation for _ in episodes)


def suggestion_only_episodes(count: int) -> tuple[v25a.Episode, ...]:
    """Positive Y-only observations; exact marginals make them common."""
    return tuple(
        v25a.Episode(event % 3, 1, (None, None, None, 1, None))
        for event in range(count)
    )


def old_context_query_error(
    cue: int, structure: str, precision: float
) -> float:
    before = joint_table(cue, 0, structure, precision)
    returned = joint_table(cue, 0, structure, precision)
    return float(np.max(np.abs(before - returned)))


def finite_information_bound() -> dict[str, float]:
    minimum = 1.0
    maximum = 0.0
    for cue in range(4):
        for context in (0, 1):
            for structure in STRUCTURES:
                table = joint_table(
                    cue,
                    context,
                    structure,
                    float(PARAMETERS["primary_precision"]),
                )
                minimum = min(minimum, float(table.min()))
                maximum = max(maximum, float(table.max()))
    value = math.log(maximum / minimum)
    return {
        "B_max_v25b": value,
        "implied_binary_probability_change_bound": math.tanh(value / 4.0),
    }
