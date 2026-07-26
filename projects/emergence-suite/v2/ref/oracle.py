"""Independent Cartesian-product checker.

This deliberately does not call factor multiplication, conditioning,
marginalization, or the elimination engine.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from itertools import product

import numpy as np

from .model import FiniteModel


def brute_force(
    model: FiniteModel,
    query: Iterable[str],
    observations: Mapping[str, int] | None = None,
) -> tuple[np.ndarray, float]:
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

