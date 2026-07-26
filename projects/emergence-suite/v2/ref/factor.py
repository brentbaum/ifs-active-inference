"""Generic nonnegative factor tables; no domain-specific edge vocabulary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

import numpy as np


@dataclass(frozen=True, slots=True)
class Factor:
    variables: tuple[str, ...]
    values: np.ndarray
    template: str = "conditional_categorical"

    def __post_init__(self) -> None:
        array = np.asarray(self.values, dtype=float)
        if array.ndim != len(self.variables):
            raise ValueError("one factor axis is required per variable")
        if len(set(self.variables)) != len(self.variables):
            raise ValueError("factor scope contains duplicate variables")
        if np.any(array < 0) or not np.all(np.isfinite(array)):
            raise ValueError("factor entries must be finite and nonnegative")
        object.__setattr__(self, "values", array.copy())

    def condition(self, observations: Mapping[str, int]) -> "Factor":
        values = self.values
        scope = list(self.variables)
        for name in tuple(self.variables):
            if name in observations:
                axis = scope.index(name)
                index = int(observations[name])
                if index < 0 or index >= values.shape[axis]:
                    raise ValueError(f"observation {name}={index} outside support")
                values = np.take(values, index, axis=axis)
                scope.pop(axis)
        return Factor(tuple(scope), np.asarray(values), self.template)

    def marginalize(self, variable: str) -> "Factor":
        if variable not in self.variables:
            return self
        axis = self.variables.index(variable)
        scope = self.variables[:axis] + self.variables[axis + 1 :]
        return Factor(scope, self.values.sum(axis=axis), self.template)

    def reorder(self, order: Iterable[str]) -> "Factor":
        target = tuple(order)
        if set(target) != set(self.variables):
            raise ValueError("reorder must preserve scope")
        axes = tuple(self.variables.index(name) for name in target)
        return Factor(target, np.transpose(self.values, axes), self.template)

    def multiply(self, other: "Factor") -> "Factor":
        union = self.variables + tuple(v for v in other.variables if v not in self.variables)
        left_shape = [1] * len(union)
        right_shape = [1] * len(union)
        for axis, name in enumerate(self.variables):
            left_shape[union.index(name)] = self.values.shape[axis]
        for axis, name in enumerate(other.variables):
            right_shape[union.index(name)] = other.values.shape[axis]
        left = self.values.reshape(left_shape)
        right_order = tuple(v for v in union if v in other.variables)
        right = other.reorder(right_order).values if right_order != other.variables else other.values
        for axis, name in enumerate(right_order):
            right_shape[union.index(name)] = right.shape[axis]
        return Factor(union, left * right.reshape(right_shape), "product")

