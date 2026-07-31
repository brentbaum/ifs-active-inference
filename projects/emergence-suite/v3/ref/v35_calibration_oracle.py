"""Independent enumeration oracle for the V3.5 calibration dummy."""

from __future__ import annotations

import itertools
import math


def _programs():
    for active in (1, 2, 3):
        for roots in itertools.product((0, 1), repeat=active):
            padded = tuple(roots) + (0,) * (3 - active)
            for joint, cross in itertools.product((0, 1), repeat=2):
                yield active, padded, joint, cross


def _length(program):
    active, roots, joint, cross = program
    return 1.0 + active + sum(roots) + joint + cross


def enumerate_joint():
    programs = tuple(_programs())
    program_weights = [2.0 ** (-_length(program)) for program in programs]
    normalizer = sum(program_weights)
    components = []
    priors = []
    for program, raw in zip(programs, program_weights):
        signs = (-1, 1) if program[3] else (0,)
        for sign in signs:
            for partner in (0, 1):
                components.append((program, sign, partner))
                priors.append(raw / normalizer / len(signs) / 2.0)
    observations = tuple(
        itertools.product(
            range(3), itertools.product((0, 1), repeat=5), range(3), range(2)
        )
    )
    likelihoods = []
    for program, sign, partner in components:
        active, roots, joint, cross = program
        edges = (*roots, joint, cross)
        sign_truth = 0 if sign == 0 else 1 if sign < 0 else 2
        row = []
        for active_obs, edge_obs, sign_obs, partner_obs in observations:
            value = 0.80 if active_obs == active - 1 else 0.10
            for observed, truth in zip(edge_obs, edges):
                value *= 0.82 if observed == truth else 0.18
            value *= 0.80 if sign_obs == sign_truth else 0.10
            value *= 0.86 if partner_obs == partner else 0.14
            row.append(value)
        likelihoods.append(tuple(row))
    posterior = []
    for o in range(len(observations)):
        weights = [
            prior * likelihoods[h][o]
            for h, prior in enumerate(priors)
        ]
        evidence = sum(weights)
        posterior.append(tuple(value / evidence for value in weights))
    return {
        "components": tuple(components),
        "priors": tuple(priors),
        "likelihoods": tuple(likelihoods),
        "posterior_by_observation": tuple(posterior),
        "normalization_error_max": max(
            abs(sum(row) - 1.0) for row in likelihoods
        ),
    }
