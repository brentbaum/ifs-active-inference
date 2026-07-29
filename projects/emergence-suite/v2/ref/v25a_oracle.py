"""Independently authored exact oracles for V2.5a.

No production V2.5a helper is imported.  The episodic oracle explicitly
enumerates every CS context path; the matching oracle performs its own root
Bayes scan.
"""

from __future__ import annotations

import itertools
import math
from typing import Iterable

import numpy as np

from . import v24


def _path_probability(path: tuple[int, ...]) -> float:
    alpha = np.asarray([[8.0, 2.0], [2.0, 8.0]], dtype=float)
    counts = np.zeros((2, 2), dtype=int)
    mass = 0.5
    for current, nxt in zip(path[:-1], path[1:]):
        mass *= float(
            (alpha[current, nxt] + counts[current, nxt])
            / (alpha[current].sum() + counts[current].sum())
        )
        counts[current, nxt] += 1
    return mass


def _emission(
    context: int, observation: v24.Observation, channel: str | None
) -> float:
    template = int(observation.cue) % 3
    probability = (
        (0.8, 0.75, 0.7)[template]
        if context == 0
        else (0.2, 0.25, 0.3)[template]
    )
    descriptor = "then" if context == 0 else "now"
    result = 1.0
    if channel in (None, "outcome") and observation.outcome is not None:
        result *= (
            probability
            if observation.outcome == 1
            else 1.0 - probability
        )
    if channel in (None, "marker") and observation.marker is not None:
        index = {
            "then_marker": 0,
            "now_marker": 1,
            "ambiguous": 2,
        }[observation.marker]
        row = {
            "then": (0.8, 0.05, 0.15),
            "now": (0.05, 0.8, 0.15),
        }[descriptor]
        result *= row[index]
    if channel in (None, "root") and observation.root is not None:
        result *= 0.5
    return result


def enumerated_cs_evidence(
    observations: Iterable[v24.Observation], channel: str | None = None
) -> float:
    sequence = list(observations)
    if channel not in (None, "outcome", "marker", "root"):
        raise ValueError("unknown oracle channel")
    total = 0.0
    for path in itertools.product((0, 1), repeat=len(sequence)):
        likelihood = math.prod(
            _emission(context, observation, channel)
            for context, observation in zip(path, sequence)
        )
        total += _path_probability(path) * likelihood
    return total


def enumerated_cs_delta_i(
    observations: Iterable[v24.Observation],
) -> float:
    sequence = list(observations)
    joint = enumerated_cs_evidence(sequence)
    marginal = math.prod(
        enumerated_cs_evidence(sequence, channel)
        for channel in ("outcome", "marker", "root")
    )
    return math.log(joint) - math.log(marginal)


def _root_likelihood(state: int, value: int) -> float:
    if state == 0:
        return 0.85 if value == 0 else 0.15
    return 0.15 if value == 0 else 0.85


def _kl_binary(q: np.ndarray) -> float:
    return float(np.sum(q * np.log(q / 0.5)))


def matching_scan(
    root_values: Iterable[int | None],
    target_kl: float,
    tolerance: float,
    cap: int,
) -> tuple[int | None, float | None]:
    values = list(root_values)
    if cap > len(values):
        raise ValueError("oracle cap exceeds supplied roots")
    posterior = np.asarray([0.5, 0.5], dtype=float)
    for index, value in enumerate(values[:cap], start=1):
        if value is not None:
            posterior *= np.asarray(
                [_root_likelihood(0, value), _root_likelihood(1, value)]
            )
            posterior /= posterior.sum()
        observed = _kl_binary(posterior)
        if observed + tolerance >= target_kl:
            return index, observed
    return None, None

