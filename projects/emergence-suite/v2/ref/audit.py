"""One-posterior state container and automated architecture audit."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

import numpy as np


@dataclass(slots=True)
class ProtocolState:
    posterior_store: dict[str, np.ndarray] = field(default_factory=dict)
    parameter_posterior_store: dict[str, np.ndarray] = field(default_factory=dict)
    evidence_store: dict[str, float] = field(default_factory=dict)
    metadata: Mapping[str, str | int | float | bool] = field(
        default_factory=lambda: MappingProxyType({})
    )


def audit_one_posterior(state: ProtocolState) -> None:
    allowed = {
        "posterior_store",
        "parameter_posterior_store",
        "evidence_store",
        "metadata",
    }
    actual = set(state.__slots__)
    if actual != allowed:
        raise AssertionError(f"mutable scientific fields outside stores: {actual - allowed}")
    if not isinstance(state.metadata, MappingProxyType):
        raise AssertionError("metadata must be immutable")
    for name, value in state.posterior_store.items():
        array = np.asarray(value, dtype=float)
        if np.any(array < 0) or not np.isclose(array.sum(), 1.0, atol=1e-10):
            raise AssertionError(f"{name} is not a normalized posterior")
    for name, value in state.parameter_posterior_store.items():
        array = np.asarray(value, dtype=float)
        if np.any(array <= 0) or not np.all(np.isfinite(array)):
            raise AssertionError(f"{name} is not a valid positive parameter posterior")
    for name, value in state.evidence_store.items():
        if not np.isfinite(value) or value < 0:
            raise AssertionError(f"{name} is not finite nonnegative evidence")

