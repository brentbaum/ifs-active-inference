"""Independently authored Cartesian structural oracle for V2.5b."""

from __future__ import annotations

import itertools
import math
from typing import Iterable, Sequence

import numpy as np

from . import v25a_completion as v25a


ATOMS = np.asarray(tuple(itertools.product((0, 1), repeat=5)), dtype=int)
STRUCTURES = tuple("".join(map(str, bits)) for bits in itertools.product((0, 1), repeat=3))
EDGE_CHANNELS = (1, 2, 3)


def _product(marginals: Sequence[float]) -> np.ndarray:
    result = np.ones(32, dtype=float)
    for axis, probability in enumerate(marginals):
        for index, state in enumerate(ATOMS):
            result[index] *= (
                probability if state[axis] else 1.0 - probability
            )
    return result / result.sum()


def build_table(
    cue: int,
    context: int,
    structure: str,
    precision: float,
    coupling_strength: float,
) -> np.ndarray:
    marginals = v25a.channel_marginals(cue, context)
    output = _product(marginals)
    if structure != "000" and precision != 0.0:
        weight = np.zeros(32, dtype=float)
        for edge, channel in zip((int(x) for x in structure), EDGE_CHANNELS):
            if edge:
                for index, state in enumerate(ATOMS):
                    weight[index] += (2 * state[4] - 1) * (
                        2 * state[channel] - 1
                    )
        output *= np.exp(coupling_strength * precision * weight)
        output /= output.sum()
        for _ in range(10000):
            for axis, target in enumerate(marginals):
                one = ATOMS[:, axis] == 1
                output[one] *= target / output[one].sum()
                output[~one] *= (1.0 - target) / output[~one].sum()
                output /= output.sum()
            if max(
                abs(output[ATOMS[:, axis] == 1].sum() - target)
                for axis, target in enumerate(marginals)
            ) <= 1e-14:
                break
    return output / output.sum()


def observed_mass(
    table: Sequence[float], values: Sequence[int | None]
) -> float:
    total = 0.0
    for state, probability in zip(ATOMS, table):
        if all(
            observed is None or int(observed) == int(latent)
            for observed, latent in zip(values, state)
        ):
            total += float(probability)
    return total


def score(
    episodes: Iterable[v25a.Episode],
    prior: Sequence[float],
    precision: float,
    coupling_strength: float,
) -> tuple[np.ndarray, np.ndarray]:
    masses = np.asarray(prior, dtype=float)
    log_evidence = np.zeros(8, dtype=float)
    for episode in episodes:
        likelihoods = []
        for structure in STRUCTURES:
            table = build_table(
                episode.cue,
                episode.context,
                structure,
                precision,
                coupling_strength,
            )
            likelihoods.append(observed_mass(table, episode.values))
        likelihoods = np.asarray(likelihoods)
        masses *= likelihoods
        masses /= masses.sum()
        log_evidence += np.log(likelihoods)
    return masses, log_evidence
