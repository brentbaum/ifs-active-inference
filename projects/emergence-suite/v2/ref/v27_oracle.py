"""Independent finite summation oracle for V2.7."""

from __future__ import annotations

import itertools
import math
from typing import Callable, Sequence

import numpy as np


def outcome_probability(
    policy_input: Sequence[int],
    topology: int,
    mandate: float,
    outcome_level: float,
    *,
    context: int = 1,
) -> float:
    """Fresh scalar transcription of the declared table, without ref helpers."""
    coordinate = (-1.0, 0.0, 1.0)
    x = [coordinate[int(value)] for value in policy_input]
    n = len(x)
    preferences = [0.0] * n
    if context == 0:
        preferences = [0.5 * value for value in preferences]
    local = sum(
        mandate * (value - target) ** 2
        for value, target in zip(x, preferences)
    ) / (4.0 * n)
    cross = 0.0
    if n > 1 and topology == 1:
        cross = mandate * (sum(x) / n) ** 2
    elif n > 1 and topology == 2:
        pairs = [
            (x[left] - x[right]) ** 2 / 4.0
            for left in range(n)
            for right in range(left + 1, n)
        ]
        cross = mandate * sum(pairs) / len(pairs)
    logit = 4.0 * (outcome_level - 0.5) - 3.0 * (local + cross - 0.25)
    return 1.0 / (1.0 + math.exp(-logit))


def joint_loss(
    policy_input: Sequence[int],
    topology: int,
    mandate_input: float | Sequence[float],
) -> float:
    coordinate = (-1.0, 0.0, 1.0)
    x = [coordinate[int(value)] for value in policy_input]
    n = len(x)
    mandates = (
        [float(mandate_input)] * n
        if np.asarray(mandate_input).ndim == 0
        else [float(value) for value in mandate_input]
    )
    preferences = [0.0] * n
    local = sum(
        mandate * (value - target) ** 2
        for mandate, value, target in zip(mandates, x, preferences)
    ) / (4.0 * n)
    if n == 1 or topology == 0:
        return local
    strength = sum(mandates) / n
    if topology == 1:
        return local + strength * (sum(x) / n) ** 2
    pairs = [
        (x[left] - x[right]) ** 2 / 4.0
        for left in range(n)
        for right in range(left + 1, n)
    ]
    return local + strength * sum(pairs) / len(pairs)


def enumerate_structure(
    observations: Sequence[tuple[tuple[int, ...], int | None]],
    protector_count: int,
    topology_prior_input: Sequence[float],
    mandate_prior_input: Sequence[float],
    outcome_prior_input: Sequence[float],
    probability_fn: Callable[[tuple[int, ...], int, int, int], float],
) -> np.ndarray:
    topology_prior = np.array(topology_prior_input, dtype=float, copy=True)
    mandate_prior = np.array(mandate_prior_input, dtype=float, copy=True)
    outcome_prior = np.array(outcome_prior_input, dtype=float, copy=True)
    masses = np.empty((3, 3, 3), dtype=float)
    for topology, mandate, outcome in itertools.product(range(3), repeat=3):
        prior = (
            topology_prior[topology]
            * mandate_prior[mandate]
            * outcome_prior[outcome]
        )
        if protector_count == 1 and topology != 0:
            prior = 0.0
        likelihood = 1.0
        for policy, observed in observations:
            if observed is not None:
                probability = float(
                    probability_fn(policy, topology, mandate, outcome)
                )
                likelihood *= probability if observed else 1.0 - probability
        masses[topology, mandate, outcome] = prior * likelihood
    return masses / float(masses.sum())


def enumerate_joint_policy(
    protector_costs_input: Sequence[Sequence[float]],
    structural_cost_fn: Callable[[tuple[int, ...]], float],
    inverse_temperature: float,
) -> tuple[tuple[tuple[int, ...], ...], np.ndarray]:
    costs = np.array(protector_costs_input, dtype=float, copy=True)
    policies = tuple(itertools.product(range(3), repeat=costs.shape[0]))
    joint_costs = []
    for policy in policies:
        local = sum(float(costs[index, value]) for index, value in enumerate(policy))
        joint_costs.append(local + float(structural_cost_fn(policy)))
    minimum = min(joint_costs)
    weights = np.asarray(
        [math.exp(-inverse_temperature * (value - minimum)) for value in joint_costs]
    )
    return policies, weights / float(weights.sum())


def registration(
    observations: Sequence[int | None],
    prior_input: Sequence[float],
    reliability: float,
) -> np.ndarray:
    q = np.array(prior_input, dtype=float, copy=True)
    q /= q.sum()
    for observed in observations:
        likelihood = np.ones(2)
        if observed is not None:
            likelihood = np.asarray(
                [
                    reliability if observed == state else 1.0 - reliability
                    for state in (0, 1)
                ]
            )
        q *= likelihood
        q /= q.sum()
    return q
