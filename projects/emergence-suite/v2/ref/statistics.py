"""Small deterministic reporting utilities."""

from __future__ import annotations

import numpy as np

from .rng import component_rng


def bootstrap_interval(
    values: list[float] | np.ndarray,
    seed: int,
    component: str,
    draws: int = 2000,
) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    rng = component_rng(seed, component)
    means = np.empty(draws)
    for index in range(draws):
        means[index] = rng.choice(array, size=len(array), replace=True).mean()
    low, high = np.quantile(means, [0.025, 0.975])
    return float(low), float(high)


def ece_binary(probabilities: np.ndarray, outcomes: np.ndarray, bins: int = 10) -> float:
    probabilities = np.asarray(probabilities, dtype=float)
    outcomes = np.asarray(outcomes, dtype=float)
    total = len(probabilities)
    error = 0.0
    for lower in np.linspace(0.0, 0.9, bins):
        upper = lower + 0.1
        mask = (probabilities >= lower) & (
            probabilities <= upper if np.isclose(upper, 1.0) else probabilities < upper
        )
        if np.any(mask):
            error += mask.mean() * abs(probabilities[mask].mean() - outcomes[mask].mean())
    return float(error)

