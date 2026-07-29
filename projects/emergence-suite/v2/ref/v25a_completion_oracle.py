"""Independent Cartesian oracles for V2.5a completion.

This module intentionally imports no production completion helper and shares
no IPF, scoring, posterior, or matching implementation with it.
"""

from __future__ import annotations

import itertools
import math
from typing import Sequence

import numpy as np


STATES = np.asarray(tuple(itertools.product((0, 1), repeat=5)), dtype=int)


def direct_marginals(table: Sequence[float]) -> np.ndarray:
    values = np.asarray(table, dtype=float)
    output = []
    for coordinate in range(5):
        total = 0.0
        for index, state in enumerate(STATES):
            if int(state[coordinate]) == 1:
                total += float(values[index])
        output.append(total)
    return np.asarray(output)


def observed_mass(table: Sequence[float], values: Sequence[int | None]) -> float:
    total = 0.0
    for probability, state in zip(table, STATES):
        compatible = True
        for observed, latent in zip(values, state):
            if observed is not None and int(observed) != int(latent):
                compatible = False
                break
        if compatible:
            total += float(probability)
    return total


def posterior_odds(
    likelihood_independent: Sequence[float],
    likelihood_coupled: Sequence[float],
    prior_odds: float,
) -> tuple[float, float]:
    left = math.prod(float(value) for value in likelihood_independent)
    right = math.prod(float(value) for value in likelihood_coupled)
    posterior = float(prior_odds) * right / left
    return posterior, math.log(right) - math.log(left)


def enumerate_mixture(
    component_priors: Sequence[float],
    component_likelihoods: Sequence[Sequence[float]],
) -> tuple[np.ndarray, float]:
    masses = []
    for prior, likelihoods in zip(component_priors, component_likelihoods):
        masses.append(float(prior) * math.prod(float(x) for x in likelihoods))
    evidence = sum(masses)
    return np.asarray(masses, dtype=float) / evidence, math.log(evidence)


def nearest_prefix(
    target: float, trajectory: Sequence[float], cap: int
) -> tuple[int, float, float]:
    best_index = 0
    best_value = float(trajectory[0])
    best_error = abs(best_value - float(target))
    for index in range(1, min(int(cap), len(trajectory))):
        value = float(trajectory[index])
        error = abs(value - float(target))
        if error < best_error:
            best_index, best_value, best_error = index, value, error
    return best_index + 1, best_value, best_error
