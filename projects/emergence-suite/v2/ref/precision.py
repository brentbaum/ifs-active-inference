"""V2.1 precision-modulated observation factors behind one interface."""

from __future__ import annotations

import numpy as np

from .factor import Factor


def precision_categorical(
    latent: str,
    precision: str,
    observation: str,
    base_rows: list[list[float]] | np.ndarray,
    precision_support: list[float] | np.ndarray,
) -> Factor:
    base = np.asarray(base_rows, dtype=float)
    support = np.asarray(precision_support, dtype=float)
    if base.ndim != 2 or np.any(base <= 0) or not np.allclose(base.sum(axis=1), 1.0):
        raise ValueError("base likelihood rows must be positive and normalized")
    table = np.empty((base.shape[0], len(support), base.shape[1]))
    for state, exponent in enumerate(support):
        powered = base**exponent
        table[:, state, :] = powered / powered.sum(axis=1, keepdims=True)
    return Factor((latent, precision, observation), table, "precision_modulated_categorical")


def precision_bounded_gaussian(
    latent: str,
    precision: str,
    observation: str,
    means: list[float] | np.ndarray,
    precision_support: list[float] | np.ndarray,
    observation_support: list[float] | np.ndarray,
) -> Factor:
    means_array = np.asarray(means, dtype=float)
    precision_array = np.asarray(precision_support, dtype=float)
    observations = np.asarray(observation_support, dtype=float)
    table = np.empty((len(means_array), len(precision_array), len(observations)))
    for latent_state, mean in enumerate(means_array):
        for precision_state, lambda_value in enumerate(precision_array):
            variance = np.exp(-lambda_value)
            density = np.exp(-0.5 * (observations - mean) ** 2 / variance) / np.sqrt(
                2.0 * np.pi * variance
            )
            table[latent_state, precision_state] = density / density.sum()
    return Factor(
        (latent, precision, observation),
        table,
        "precision_modulated_bounded_gaussian",
    )


def observation_likelihood(kind: str, **kwargs: object) -> Factor:
    """Single public likelihood interface for every observation kind."""
    if kind == "categorical":
        return precision_categorical(**kwargs)
    if kind == "bounded_gaussian":
        return precision_bounded_gaussian(**kwargs)
    raise ValueError(f"unsupported observation kind: {kind}")


def gaussian_log_likelihood(
    observation: float,
    mean: float,
    lambda_value: float,
) -> float:
    variance = np.exp(-lambda_value)
    return float(
        -0.5
        * (
            np.log(2.0 * np.pi * variance)
            + (observation - mean) ** 2 / variance
        )
    )

