"""Declared factor templates shared by all observation kinds."""

from __future__ import annotations

import numpy as np

from .factor import Factor


def categorical_prior(variable: str, probabilities: list[float] | np.ndarray) -> Factor:
    values = np.asarray(probabilities, dtype=float)
    if not np.isclose(values.sum(), 1.0):
        raise ValueError("prior must sum to one")
    return Factor((variable,), values, "categorical_prior")


def conditional_categorical(
    parent: str,
    child: str,
    rows: list[list[float]] | np.ndarray,
) -> Factor:
    values = np.asarray(rows, dtype=float)
    if values.ndim != 2 or not np.allclose(values.sum(axis=1), 1.0):
        raise ValueError("each CPT row must sum to one")
    return Factor((parent, child), values, "conditional_categorical")


def dirichlet_update(alpha: np.ndarray, counts: np.ndarray) -> np.ndarray:
    alpha = np.asarray(alpha, dtype=float)
    counts = np.asarray(counts, dtype=float)
    if alpha.shape != counts.shape or np.any(alpha <= 0) or np.any(counts < 0):
        raise ValueError("Dirichlet prior/count shapes or support invalid")
    return alpha + counts
