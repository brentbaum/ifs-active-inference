"""Independently authored brute-force oracle for V3.4.

This module copies every input and shares no scoring helper with ``ref.v34``.
"""

from __future__ import annotations

import copy
import itertools
import math
from typing import Any, Mapping, Sequence

import numpy as np


EDGE_NAMES = ("L_PREC", "L_Y", "PA_RY", "L_TRANSITION")
PROGRAMS = tuple(itertools.product((0, 1), repeat=4))
RELATIONAL_BASE = (
    (0.90, 0.90, 0.10, 0.90, 0.10),
    (0.90, 0.20, 0.20, 0.30, 0.40),
    (0.30, 0.30, 0.90, 0.20, 0.60),
    (0.60, 0.50, 0.40, 0.50, 0.90),
)
ACTION_SIGNS = (1.0, 1.0, -1.0, 1.0, -1.0)
STATE_PRECISION = (0.90, 0.65, 0.20, 0.35)
STATE_OUTCOME = (0.85, 0.55, 0.25, 0.40)
ACTION_EFFECT = 0.12
BASE_PRECISION = 0.45
ROOT_GAIN = 0.42


def _binary_prior(value: int, scale: float) -> float:
    absent = 2.0 ** (-scale)
    present = 2.0 ** (-2.0 * scale)
    return (present if value else absent) / (absent + present)


def _prior(
    program: tuple[int, ...],
    scale: float,
    restrictions: Mapping[str, tuple[int, ...]],
) -> float:
    result = 1.0
    for index, name in enumerate(EDGE_NAMES):
        support = tuple(restrictions.get(name, (0, 1)))
        if program[index] not in support:
            return 0.0
        probabilities = [_binary_prior(value, scale) for value in support]
        result *= probabilities[support.index(program[index])] / sum(
            probabilities
        )
    return result


def _transition(program: tuple[int, ...], stay: float) -> np.ndarray:
    if not program[3]:
        return np.eye(4)
    matrix = np.full((4, 4), (1.0 - stay) / 3.0)
    np.fill_diagonal(matrix, stay)
    return matrix


def _clip(value: float) -> float:
    return float(np.clip(value, 0.02, 0.98))


def _relational(
    state: int,
    channel: int,
    action: int,
    program: tuple[int, ...],
) -> float:
    value = RELATIONAL_BASE[state][channel]
    if program[2]:
        value += (
            ACTION_EFFECT
            * (1.0 if action else -1.0)
            * ACTION_SIGNS[channel]
        )
    return _clip(value)


def _regulation(state: int, program: tuple[int, ...]) -> float:
    return STATE_PRECISION[state] if program[0] else 0.5


def _outcome(
    state: int, action: int, program: tuple[int, ...]
) -> float:
    value = STATE_OUTCOME[state] if program[1] else 0.5
    if program[2]:
        value += ACTION_EFFECT * (1.0 if action else -1.0)
    return _clip(value)


def _root(
    observed: int,
    root_state: int,
    state: int,
    program: tuple[int, ...],
    broadcast: bool,
) -> float:
    local = STATE_PRECISION[state] if program[0] else BASE_PRECISION
    precision = local if broadcast else BASE_PRECISION
    correct = 0.5 + ROOT_GAIN * precision
    return correct if observed == root_state else 1.0 - correct


def _emission(
    item: Mapping[str, Any],
    state: int,
    root_state: int,
    program: tuple[int, ...],
    *,
    broadcast: bool,
    root_evidence_enabled: bool,
    relational_enabled: bool,
) -> float:
    result = 1.0
    action = int(item["partner_action"])
    if relational_enabled:
        for channel, observed in enumerate(item["relational"]):
            if observed is not None:
                probability = _relational(
                    state, channel, action, program
                )
                result *= probability if observed else 1.0 - probability
        regulation = item["regulation_response"]
        if regulation is not None:
            probability = _regulation(state, program)
            result *= probability if regulation else 1.0 - probability
        outcome = item["outcome"]
        if outcome is not None:
            probability = _outcome(state, action, program)
            result *= probability if outcome else 1.0 - probability
    root = item["root_evidence"]
    if root_evidence_enabled and root is not None:
        result *= _root(
            int(root), root_state, state, program, broadcast
        )
    return float(result)


def _hmm_evidence(
    observations: Sequence[Mapping[str, Any]],
    program: tuple[int, ...],
    root_state: int,
    *,
    transition_stay: float,
    broadcast: bool,
    root_evidence_enabled: bool,
    relational_enabled: bool,
) -> float:
    state_mass = np.full(4, 0.25)
    matrix = _transition(program, transition_stay)
    for time, item in enumerate(observations):
        if time:
            state_mass = state_mass @ matrix
        likelihood = np.asarray(
            [
                _emission(
                    item,
                    state,
                    root_state,
                    program,
                    broadcast=broadcast,
                    root_evidence_enabled=root_evidence_enabled,
                    relational_enabled=relational_enabled,
                )
                for state in range(4)
            ]
        )
        state_mass = state_mass * likelihood
    return float(state_mass.sum())


def posterior(
    observations_input: Sequence[Mapping[str, Any]],
    *,
    code_length_scale: float = 1.0,
    transition_stay: float = 0.88,
    restrictions: Mapping[str, tuple[int, ...]] | None = None,
    broadcast: bool = True,
    root_evidence_enabled: bool = True,
    relational_enabled: bool = True,
) -> tuple[
    tuple[tuple[int, ...], ...],
    tuple[float, ...],
    tuple[float, float],
    float,
]:
    observations = copy.deepcopy(
        tuple(dict(item) for item in observations_input)
    )
    limits = (
        {}
        if restrictions is None
        else {
            str(name): tuple(values)
            for name, values in dict(restrictions).items()
        }
    )
    retained = tuple(
        program
        for program in PROGRAMS
        if _prior(program, code_length_scale, limits) > 0.0
    )
    joint_weights = []
    joint_keys = []
    for program in retained:
        for root_state in (0, 1):
            weight = (
                _prior(program, code_length_scale, limits)
                * 0.5
                * _hmm_evidence(
                    observations,
                    program,
                    root_state,
                    transition_stay=transition_stay,
                    broadcast=broadcast,
                    root_evidence_enabled=root_evidence_enabled,
                    relational_enabled=relational_enabled,
                )
            )
            joint_weights.append(weight)
            joint_keys.append((program, root_state))
    evidence = math.fsum(joint_weights)
    normalized = [
        value / evidence for value in joint_weights
    ]
    structure_probabilities = tuple(
        math.fsum(
            probability
            for key, probability in zip(joint_keys, normalized)
            if key[0] == program
        )
        for program in retained
    )
    if root_evidence_enabled and any(
        item["root_evidence"] is not None for item in observations
    ):
        root_one = math.fsum(
            probability
            for key, probability in zip(joint_keys, normalized)
            if key[1] == 1
        )
        q_root = (1.0 - root_one, root_one)
    else:
        q_root = (0.5, 0.5)
    return retained, structure_probabilities, q_root, math.log(evidence)
