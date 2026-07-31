"""Independently authored brute-force oracle for reduced V3.5 fixtures."""

from __future__ import annotations

import copy
import itertools
import math
from typing import Any, Mapping, Sequence


def _programs():
    for active in (1, 2, 3):
        for roots in itertools.product((0, 1), repeat=active):
            padded = tuple(roots) + (0,) * (3 - active)
            for joint, cross in itertools.product((0, 1), repeat=2):
                yield active, padded, joint, cross


PROGRAMS = tuple(_programs())


def _length(program):
    active, roots, joint, cross = program
    return 1.0 + active + sum(roots) + joint + cross


NORMALIZER = math.fsum(2.0 ** (-_length(p)) for p in PROGRAMS)


def _prior(program):
    return 2.0 ** (-_length(program)) / NORMALIZER


def _clip(value):
    return min(0.97, max(0.03, value))


def _outcome(policy, modes, program, sign):
    active, _roots, joint, cross = program
    probability = 0.5
    if joint:
        probability += 0.18 * (sum(policy[:active]) / active - 1.0)
    if cross:
        pairs = [
            (i, j)
            for i in range(active)
            for j in range(i + 1, active)
            if modes[i] and modes[j]
        ]
        if pairs and sign < 0:
            probability -= 0.30 * sum(
                abs(policy[i] - policy[j]) / 2.0 for i, j in pairs
            ) / len(pairs)
        elif pairs:
            probability += 0.30 * sum(
                policy[i] == policy[j] == 2 for i, j in pairs
            ) / len(pairs)
    return _clip(probability)


def _slice(item, modes, program, sign, reliable):
    active, roots, _joint, _cross = program
    value = 1.0
    for index in range(active):
        signal = item["mode_signals"][index]
        if signal is not None:
            value *= 0.86 if int(signal) == modes[index] else 0.14
        registration = item["registration"][index]
        if registration is not None:
            value *= 0.80 if int(registration) == modes[index] else 0.20
        support = item["support_signals"][index]
        if support is not None:
            p = 0.82 if reliable else 0.25
            value *= p if support else 1.0 - p
    root_signal = item["root_signal"]
    if root_signal is not None:
        parents = [modes[i] for i in range(active) if roots[i]]
        if not parents:
            p = 0.5
        else:
            root = int(sum(parents) >= len(parents) / 2.0)
            p = 0.84 if int(root_signal) == root else 0.16
        value *= p
    p_outcome = _outcome(item["policy"], modes, program, sign)
    value *= p_outcome if item["outcome"] else 1.0 - p_outcome
    if item["partner_remaining"] is not None:
        p = 0.86 if reliable else 0.14
        value *= p if item["partner_remaining"] else 1.0 - p
    if item["partner_pressure"] is not None:
        p = 0.14 if reliable else 0.86
        value *= p if item["partner_pressure"] else 1.0 - p
    if item["denied_contact"] is not None:
        vulnerable = active - 1
        p = 0.86 if modes[vulnerable] and item["policy"][vulnerable] == 0 else 0.14
        value *= p if item["denied_contact"] else 1.0 - p
    return value


def posterior(
    observations_input: Sequence[Mapping[str, Any]],
) -> tuple[tuple[tuple[Any, ...], ...], tuple[float, ...], float]:
    observations = copy.deepcopy(tuple(dict(item) for item in observations_input))
    keys = []
    weights = []
    for program in PROGRAMS:
        signs = (-1, 1) if program[3] else (0,)
        for sign in signs:
            for reliable in (0, 1):
                likelihood = 1.0
                for item in observations:
                    evidence = 0.0
                    for modes in itertools.product((0, 1), repeat=3):
                        if any(modes[program[0] :]):
                            continue
                        evidence += 0.5 ** program[0] * _slice(
                            item, modes, program, sign, reliable
                        )
                    likelihood *= evidence
                keys.append((*program, sign, reliable))
                weights.append(
                    _prior(program) / len(signs) / 2.0 * likelihood
                )
    evidence = math.fsum(weights)
    return tuple(keys), tuple(value / evidence for value in weights), evidence
