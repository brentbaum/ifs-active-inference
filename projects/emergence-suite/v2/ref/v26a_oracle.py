"""Independently authored path-enumeration oracle for V2.6a."""

from __future__ import annotations

import itertools
import math
from typing import Sequence

import numpy as np


def enumerate_partner(
    relational_observations: Sequence[Sequence[int | None]],
    prior_input: Sequence[float],
    transition_input: np.ndarray,
    emission_input: np.ndarray,
) -> tuple[np.ndarray, tuple[np.ndarray, ...], tuple[np.ndarray, ...], float]:
    """Enumerate all paths without importing or sharing production helpers."""
    observations = tuple(tuple(item) for item in relational_observations)
    prior = np.array(prior_input, dtype=float, copy=True)
    transition = np.array(transition_input, dtype=float, copy=True)
    emissions = np.array(emission_input, dtype=float, copy=True)
    path_count = len(observations)
    weights: list[float] = []
    paths = list(itertools.product(range(4), repeat=path_count))
    for path in paths:
        probability = float(prior[path[0]]) if path_count else 1.0
        for time, state in enumerate(path):
            if time:
                probability *= float(transition[path[time - 1], state])
            for observed, success in zip(observations[time], emissions[state]):
                if observed is not None:
                    probability *= float(success if int(observed) else 1.0 - success)
        weights.append(probability)
    evidence = float(sum(weights))
    if path_count == 0:
        return prior / prior.sum(), (), (), 0.0
    normalized = np.asarray(weights, dtype=float) / evidence
    marginals = []
    for time in range(path_count):
        q = np.zeros(4, dtype=float)
        for probability, path in zip(normalized, paths):
            q[path[time]] += probability
        marginals.append(q)
    pairs = []
    for time in range(path_count - 1):
        q = np.zeros((4, 4), dtype=float)
        for probability, path in zip(normalized, paths):
            q[path[time], path[time + 1]] += probability
        pairs.append(q)
    occupancy = np.sum(np.asarray(marginals), axis=0)
    occupancy /= occupancy.sum()
    return occupancy, tuple(marginals), tuple(pairs), math.log(evidence)
