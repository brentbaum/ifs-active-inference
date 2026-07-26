"""Typed finite generative-model declarations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np

from .factor import Factor


@dataclass(frozen=True, slots=True)
class Variable:
    name: str
    cardinality: int
    kind: str = "latent"
    time: int | None = None

    def __post_init__(self) -> None:
        if not self.name or self.cardinality < 2:
            raise ValueError("variables require a name and cardinality >= 2")
        if self.kind not in {"latent", "observation", "policy", "parameter", "structure"}:
            raise ValueError(f"unsupported variable kind: {self.kind}")


@dataclass(slots=True)
class FiniteModel:
    variables: dict[str, Variable] = field(default_factory=dict)
    factors: list[Factor] = field(default_factory=list)

    def add_variable(self, variable: Variable) -> None:
        if variable.name in self.variables:
            raise ValueError(f"duplicate variable {variable.name}")
        self.variables[variable.name] = variable

    def add_factor(self, factor: Factor) -> None:
        if not factor.variables:
            raise ValueError("factor scope cannot be empty")
        for axis, name in enumerate(factor.variables):
            if name not in self.variables:
                raise ValueError(f"factor references undeclared variable {name}")
            expected = self.variables[name].cardinality
            if factor.values.shape[axis] != expected:
                raise ValueError(f"{name} axis has size {factor.values.shape[axis]}, expected {expected}")
        self.factors.append(factor)

    def conditioned(self, observations: Mapping[str, int]) -> "FiniteModel":
        clone = FiniteModel(dict(self.variables), [])
        for factor in self.factors:
            clone.factors.append(factor.condition(observations))
        return clone

    def validate(self) -> None:
        if not self.variables or not self.factors:
            raise ValueError("model must declare variables and factors")
        for factor in self.factors:
            if np.any(factor.values < 0) or not np.all(np.isfinite(factor.values)):
                raise ValueError("factor entries must be finite and nonnegative")

