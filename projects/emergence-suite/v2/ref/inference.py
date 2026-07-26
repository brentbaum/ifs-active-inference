"""Exact variable elimination engine."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from functools import reduce

import numpy as np

from .factor import Factor
from .model import FiniteModel


class ExactEngine:
    """Sum-product elimination with deterministic min-fill-style ordering."""

    @staticmethod
    def _product(factors: list[Factor]) -> Factor:
        if not factors:
            return Factor((), np.asarray(1.0), "identity")
        return reduce(lambda a, b: a.multiply(b), factors)

    def unnormalized(
        self,
        model: FiniteModel,
        query: Iterable[str],
        observations: Mapping[str, int] | None = None,
    ) -> Factor:
        model.validate()
        evidence = dict(observations or {})
        query_scope = tuple(query)
        if set(query_scope) & set(evidence):
            raise ValueError("query variables cannot also be observed")
        factors = [factor.condition(evidence) for factor in model.factors]
        hidden = set(model.variables) - set(query_scope) - set(evidence)
        while hidden:
            variable = min(
                hidden,
                key=lambda name: (
                    sum(np.prod(f.values.shape) for f in factors if name in f.variables),
                    name,
                ),
            )
            touching = [f for f in factors if variable in f.variables]
            factors = [f for f in factors if variable not in f.variables]
            if touching:
                factors.append(self._product(touching).marginalize(variable))
            hidden.remove(variable)
        result = self._product(factors)
        for variable in tuple(result.variables):
            if variable not in query_scope:
                result = result.marginalize(variable)
        if result.variables != query_scope and query_scope:
            result = result.reorder(query_scope)
        return result

    def infer(
        self,
        model: FiniteModel,
        query: Iterable[str],
        observations: Mapping[str, int] | None = None,
    ) -> tuple[np.ndarray, float]:
        factor = self.unnormalized(model, query, observations)
        evidence = float(np.sum(factor.values))
        if evidence <= 0:
            raise ValueError("conditioning event has zero model evidence")
        posterior = factor.values / evidence
        # Every reported engine posterior is checked through the separately
        # authored Cartesian-product path. No factor-algebra intermediate is
        # shared with that path.
        from .oracle import brute_force

        oracle_posterior, oracle_evidence = brute_force(model, query, observations)
        if not np.allclose(posterior, oracle_posterior, atol=1e-10, rtol=0) or not np.isclose(
            evidence, oracle_evidence, atol=1e-10, rtol=0
        ):
            raise AssertionError("variable elimination disagrees with brute-force oracle")
        return posterior, evidence

    def evidence(self, model: FiniteModel, observations: Mapping[str, int]) -> float:
        return self.infer(model, (), observations)[1]
