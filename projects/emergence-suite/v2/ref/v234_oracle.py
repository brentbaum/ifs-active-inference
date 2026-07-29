"""Independent scalar Cartesian oracle for V2.3.4."""

from __future__ import annotations

import itertools
from typing import Sequence

import numpy as np


def update(
    prior_input: Sequence[float],
    theta_input: Sequence[float],
    eta_input: Sequence[float],
    configs_input: Sequence[tuple[int, int]],
    episode: tuple[int, int, int | None, int | None, int | None],
    reliabilities: tuple[float, float, float],
) -> tuple[np.ndarray, float]:
    prior = np.array(prior_input, dtype=float, copy=True)
    theta_values = np.array(theta_input, dtype=float, copy=True)
    eta_values = np.array(eta_input, dtype=float, copy=True)
    configs = tuple(tuple(item) for item in configs_input)
    action, context, outcome, near_miss, efficacy_observation = episode
    raw = np.zeros_like(prior)
    state = 0
    for theta in theta_values:
        for config in configs:
            eta = float(eta_values[config[context]])
            likelihood = 0.0
            for danger, prevented in itertools.product((0, 1), repeat=2):
                pd = theta if danger else 1.0 - theta
                pp = (
                    eta if prevented else 1.0 - eta
                ) if action == 1 else float(prevented == 0)
                realized = int(danger * (1 - int(action == 1) * prevented))
                po = 1.0 if outcome is None else (
                    reliabilities[0]
                    if outcome == realized
                    else 1.0 - reliabilities[0]
                )
                pn = 1.0 if near_miss is None else (
                    reliabilities[1]
                    if near_miss == danger
                    else 1.0 - reliabilities[1]
                )
                pe = 1.0 if efficacy_observation is None else (
                    reliabilities[2]
                    if efficacy_observation == prevented
                    else 1.0 - reliabilities[2]
                )
                likelihood += pd * pp * po * pn * pe
            raw[state] = prior[state] * likelihood
            state += 1
    evidence = float(raw.sum())
    return raw / evidence, evidence
