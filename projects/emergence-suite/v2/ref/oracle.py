"""Independent Cartesian-product checker.

This deliberately does not call factor multiplication, conditioning,
marginalization, or the elimination engine.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from itertools import product

import numpy as np

from .model import FiniteModel


def brute_force_slow(
    model: FiniteModel,
    query: Iterable[str],
    observations: Mapping[str, int] | None = None,
) -> tuple[np.ndarray, float]:
    """Retained Cartesian-product reference implementation."""
    model.validate()
    evidence_map = dict(observations or {})
    query_names = tuple(query)
    if set(query_names) & set(evidence_map):
        raise ValueError("query variables cannot also be observed")
    names = tuple(model.variables)
    cards = {name: model.variables[name].cardinality for name in names}
    output = np.zeros(tuple(cards[name] for name in query_names) or (), dtype=float)
    total = 0.0
    for states in product(*(range(cards[name]) for name in names)):
        assignment = dict(zip(names, states))
        if any(assignment[name] != value for name, value in evidence_map.items()):
            continue
        mass = 1.0
        for factor in model.factors:
            index = tuple(assignment[name] for name in factor.variables)
            mass *= float(factor.values[index])
        total += mass
        index = tuple(assignment[name] for name in query_names)
        output[index] += mass
    if total <= 0:
        raise ValueError("conditioning event has zero model evidence")
    return output / total, total


def brute_force(
    model: FiniteModel,
    query: Iterable[str],
    observations: Mapping[str, int] | None = None,
    *,
    slow: bool = False,
) -> tuple[np.ndarray, float]:
    """Broadcast-joint audit with the slow Cartesian path selectable."""
    if slow:
        return brute_force_slow(model, query, observations)
    model.validate()
    evidence_map = dict(observations or {})
    query_names = tuple(query)
    if set(query_names) & set(evidence_map):
        raise ValueError("query variables cannot also be observed")

    names = tuple(model.variables)
    cardinalities = [
        model.variables[name].cardinality for name in names
    ]
    axes = {name: index for index, name in enumerate(names)}
    joint = np.ones(cardinalities, dtype=float)
    for factor in model.factors:
        factor_axes = [axes[name] for name in factor.variables]
        order = np.argsort(factor_axes)
        values = np.transpose(factor.values, order)
        shape = [1] * len(names)
        for axis in sorted(factor_axes):
            shape[axis] = cardinalities[axis]
        joint = joint * values.reshape(shape)

    index = [slice(None)] * len(names)
    for name, value in evidence_map.items():
        index[axes[name]] = int(value)
    conditioned = joint[tuple(index)]
    retained_names = [
        name for name in names if name not in evidence_map
    ]
    total = float(conditioned.sum())
    if total <= 0:
        raise ValueError("conditioning event has zero model evidence")
    sum_axes = tuple(
        axis
        for axis, name in enumerate(retained_names)
        if name not in query_names
    )
    output = (
        conditioned.sum(axis=sum_axes)
        if sum_axes
        else conditioned
    )
    retained_query = [
        name for name in retained_names if name in query_names
    ]
    if tuple(retained_query) != query_names and query_names:
        output = np.transpose(
            output,
            tuple(retained_query.index(name) for name in query_names),
        )
    return np.asarray(output, dtype=float) / total, total
