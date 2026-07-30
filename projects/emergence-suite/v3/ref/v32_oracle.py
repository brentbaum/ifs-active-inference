"""Independently authored brute-force oracle for V3.2.

This module deliberately duplicates the finite grammar summation.  It imports
only the immutable public data types and copies every numerical input before
scoring; it shares no scorer, prior, emission, or normalization helper with
``ref.v32``.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Any, Mapping

from .v32 import TemporalHyperparameters, TemporalStructure, TemporalWorld


_SCOPES = ("shared_global", "cue_specific", "context_specific")
_DYNAMICS = (
    "static",
    "discrete_recurrent_context",
    "ordered_random_walk",
    "one_way_change",
)
_BLOCKS = ("cue_emission", "outcome_emission")


@dataclass(frozen=True)
class OraclePosterior:
    programs: tuple[TemporalStructure, ...]
    probabilities: tuple[float, ...]
    log_evidence: float


def _cost(value: Any) -> float:
    if isinstance(value, int):
        return float(value)
    return 1.0 if value in {"shared_global", "static"} else 3.0


def _normalized_weights(values: tuple[Any, ...], scale: float) -> tuple[float, ...]:
    raw = tuple(2.0 ** (-scale * _cost(value)) for value in values)
    total = math.fsum(raw)
    return tuple(value / total for value in raw)


def _categorical(observed: int, truth: int, size: int, reliability: float) -> float:
    return reliability if observed == truth else (1.0 - reliability) / (size - 1)


def _scope(scope: str, cue: int, context: int) -> float:
    if scope == "shared_global":
        return 0.5
    if scope == "cue_specific":
        return 0.22 if cue % 2 == 0 else 0.78
    return (0.18, 0.82, 0.5)[context]


def _dynamics(kind: str, time: int, length: int, context: int) -> float:
    if kind == "static":
        return 0.5
    if kind == "discrete_recurrent_context":
        return (0.2, 0.8, 0.5)[context]
    if kind == "ordered_random_walk":
        return 0.18 + 0.64 * time / max(1, length - 1)
    return 0.18 if time < length // 2 else 0.82


def _emission(
    scope: str,
    dynamics: str,
    cue: int,
    context: int,
    time: int,
    length: int,
    floor: float,
) -> float:
    value = 0.5 + (_scope(scope, cue, context) - 0.5) + (
        _dynamics(dynamics, time, length, context) - 0.5
    )
    return min(1.0 - floor, max(floor, value))


def _logsumexp(values: tuple[float, ...]) -> float:
    peak = max(values)
    return peak + math.log(math.fsum(math.exp(value - peak) for value in values))


def brute_force_structure_posterior(
    world: TemporalWorld,
    hyperparameters: TemporalHyperparameters,
    *,
    restrictions: Mapping[str, tuple[Any, ...]] | None = None,
    masked_channels: frozenset[str] = frozenset(),
) -> OraclePosterior:
    """Enumerate every allowed joint program using copied inputs."""

    copied = tuple(
        (
            int(item.time),
            int(item.cue),
            int(item.context),
            str(item.block),
            int(item.value),
            int(item.root_value),
            int(item.active_context_token),
            int(item.scope_token),
            int(item.dynamics_token),
            bool(item.missing),
        )
        for item in tuple(world.slices)
    )
    scale = float(hyperparameters.code_length_scale)
    reliability = float(hyperparameters.diagnostic_reliability)
    floor = float(hyperparameters.emission_floor)
    length = int(world.length)
    limits = {} if restrictions is None else {
        str(key): tuple(value) for key, value in dict(restrictions).items()
    }
    active_support = limits.get("active_contexts", (1, 2, 3))
    scope_support = {
        block: limits.get(f"scope:{block}", _SCOPES) for block in _BLOCKS
    }
    dynamics_support = {
        block: limits.get(f"dynamics:{block}", _DYNAMICS) for block in _BLOCKS
    }
    active_prior = _normalized_weights((1, 2, 3), scale)
    scope_prior = _normalized_weights(_SCOPES, scale)
    dynamics_prior = _normalized_weights(_DYNAMICS, scale)
    programs = tuple(
        TemporalStructure(active, scopes, dynamics)
        for active in active_support
        for scopes in itertools.product(
            scope_support[_BLOCKS[0]], scope_support[_BLOCKS[1]]
        )
        for dynamics in itertools.product(
            dynamics_support[_BLOCKS[0]], dynamics_support[_BLOCKS[1]]
        )
    )
    log_weights = []
    for program in programs:
        score = math.log(active_prior[program.active_contexts - 1])
        score += math.fsum(
            math.log(scope_prior[_SCOPES.index(scope)])
            for scope in program.scopes
        )
        score += math.fsum(
            math.log(dynamics_prior[_DYNAMICS.index(kind)])
            for kind in program.dynamics
        )
        for (
            time,
            cue,
            context,
            block,
            observed,
            root,
            active_token,
            scope_token,
            dynamics_token,
            missing,
        ) in copied:
            if missing:
                continue
            index = _BLOCKS.index(block)
            scope = program.scopes[index]
            dynamics = program.dynamics[index]
            probability = _emission(
                scope, dynamics, cue, context, time, length, floor
            )
            score += math.log(probability if observed else 1.0 - probability)
            root_probability = _scope(scope, cue, context) if scope == "context_specific" else 0.5
            score += math.log(root_probability if root else 1.0 - root_probability)
            if "active_contexts" not in masked_channels:
                score += math.log(
                    _categorical(
                        active_token,
                        program.active_contexts - 1,
                        3,
                        reliability,
                    )
                )
            if f"scope:{block}" not in masked_channels:
                score += math.log(
                    (
                        _categorical(
                            scope_token,
                            _SCOPES.index(scope),
                            3,
                            reliability,
                        )
                        if time == 0 and cue == 0
                        else 1.0 / 3.0
                    )
                )
            if f"dynamics:{block}" not in masked_channels:
                score += math.log(
                    (
                        _categorical(
                            dynamics_token,
                            _DYNAMICS.index(dynamics),
                            4,
                            reliability,
                        )
                        if time == 0 and cue == 0
                        else 1.0 / 4.0
                    )
                )
        log_weights.append(score)
    normalizer = _logsumexp(tuple(log_weights))
    probabilities = tuple(math.exp(value - normalizer) for value in log_weights)
    return OraclePosterior(programs, probabilities, normalizer)
