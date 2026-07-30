"""Independently authored brute-force oracle for reduced V3.0 fixtures.

This module intentionally shares no scoring helper with ``ref.grammar``.
Inputs are copied before any calculation.
"""

from __future__ import annotations

import copy
import itertools
import math
from typing import Any, Mapping

import numpy as np


def _cost(name: str, value: Any) -> float:
    if name == "active_modes":
        return 1.0 + float(value)
    if name == "active_contexts":
        return float(value)
    if name.startswith("edge:"):
        return 1.0 + float(value)
    if name.startswith("scope:"):
        return 1.0 if value == "shared_global" else 3.0
    if name.startswith("dynamics:"):
        return 1.0 if value == "static" else 3.0
    raise KeyError(name)


def _prior(name: str, support: tuple[Any, ...]) -> np.ndarray:
    raw = np.asarray([2.0 ** (-_cost(name, value)) for value in support])
    return raw / raw.sum()


def brute_force_posterior(
    supports_input: Mapping[str, tuple[Any, ...]],
    observations_input: tuple[tuple[str, int, bool], ...],
    reliability: float,
) -> tuple[dict[str, tuple[float, ...]], float]:
    supports = copy.deepcopy(dict(supports_input))
    observations = copy.deepcopy(tuple(observations_input))
    fields = tuple(supports)
    joint_weights: list[float] = []
    assignments: list[tuple[Any, ...]] = []
    for assignment in itertools.product(*(supports[field] for field in fields)):
        probability = 1.0
        mapping = dict(zip(fields, assignment))
        for field in fields:
            support = tuple(supports[field])
            truth = support.index(mapping[field])
            probability *= float(_prior(field, support)[truth])
            for obs_field, value, missing in observations:
                if obs_field != field or missing:
                    continue
                if len(support) == 1:
                    probability *= 1.0
                elif value == truth:
                    probability *= reliability
                else:
                    probability *= (1.0 - reliability) / (len(support) - 1)
        assignments.append(assignment)
        joint_weights.append(probability)
    evidence = math.fsum(joint_weights)
    marginals: dict[str, tuple[float, ...]] = {}
    for field_index, field in enumerate(fields):
        values = []
        for candidate in supports[field]:
            mass = math.fsum(
                weight
                for assignment, weight in zip(assignments, joint_weights)
                if assignment[field_index] == candidate
            )
            values.append(mass / evidence)
        marginals[field] = tuple(values)
    return marginals, math.log(evidence)
