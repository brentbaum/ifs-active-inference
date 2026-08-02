"""Independent finite oracle for V3.6 native-prior fixture identity.

This module deliberately imports no production fixture or bridge helper.  It
expands the frozen module priors, transitions, and observation tables directly.
"""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

from . import v32, v35
from v2.ref import v232_formation, v234, v24, v26b


LENGTH = 2
TOTAL_SLICES = 64
V2_ROOT = Path(__file__).resolve().parents[2] / "v2"
PARTNER_PARAMETERS = json.loads(
    (V2_ROOT / "protocols" / "v2.6a-parameters.json").read_text()
)
PARTNER_CHANNELS = ("regulation", "remaining", "respect", "trust")


def _bernoulli(probability: float, value: int) -> float:
    return float(probability if value else 1.0 - probability)


def _context_initial(family: str) -> tuple[tuple[tuple[int, ...], float], ...]:
    if family == "context_split":
        prior = v24.PARAMETERS["family_processes"][family]["initial_distribution"]
        return tuple(((index, 0, 0, 0, 0), float(mass)) for index, mass in enumerate(prior))
    if family == "change_point":
        return (((0, 0), 1.0),)
    prior = v24.PARAMETERS["candidate_common_nuisance_context"]["initial_distribution"]
    return tuple(((index,), float(mass)) for index, mass in enumerate(prior))


def _descriptor(family: str, state: tuple[int, ...]) -> str:
    if family in {"context_split", "change_point"}:
        return "then" if state[0] == 0 else "now"
    return ("then", "now", "none")[state[0]]


def _context_row(descriptor: str) -> tuple[float, float]:
    row = v24.PARAMETERS["observation_interface"][
        "context_marker_cpt_nonmissing"
    ][descriptor]
    then, now = float(row[0]), float(row[1])
    total = then + now
    return then / total, now / total


def _context_next(
    family: str, state: tuple[int, ...]
) -> tuple[tuple[tuple[int, ...], float], ...]:
    if family == "context_split":
        context, n00, n01, n10, n11 = state
        table = v24.PARAMETERS["family_processes"][family][
            "transition_dirichlet_prior"
        ]
        alpha = (
            table["then_row_then_now"], table["now_row_then_now"]
        )[context]
        counts = ((n00, n01), (n10, n11))[context]
        values = (alpha[0] + counts[0], alpha[1] + counts[1])
        total = float(sum(values))
        result = []
        for next_context in (0, 1):
            updated = [n00, n01, n10, n11]
            updated[context * 2 + next_context] += 1
            result.append(((next_context, *updated), values[next_context] / total))
        return tuple(result)
    if family == "change_point":
        phase, stays = state
        if phase == 1:
            return (((1, stays), 1.0),)
        a, b = v24.PARAMETERS["family_processes"][family]["hazard_beta_prior"]
        probability = float(a / (a + b + stays))
        return (((1, stays), probability), ((0, stays + 1), 1.0 - probability))
    matrix = v24.PARAMETERS["candidate_common_nuisance_context"]["transition_matrix"]
    return tuple(((index,), float(mass)) for index, mass in enumerate(matrix[state[0]]))


def v2_joint(target: str) -> Mapping[tuple[Any, ...], float]:
    result: dict[tuple[Any, ...], float] = {}
    if target == "identity":
        for latent, candidate in enumerate(v232_formation.LABELS):
            cpt = v232_formation.slice_distribution(
                candidate, event=True, precision="ordinary", control="low",
                broadcast="integrated", real_danger=False,
            )
            probability = sum(
                float(cpt[index]) for index, atom in enumerate(
                    v232_formation.SUPPORT
                ) if atom[0] == 1
            )
            for observations in itertools.product((0, 1), repeat=LENGTH):
                result[(latent, observations)] = float(
                    v232_formation.PRIOR[latent]
                ) * math.prod(_bernoulli(probability, value) for value in observations)
    elif target == "outcome":
        for latent, prior in enumerate(v234.JOINT_PRIOR):
            for observations in itertools.product((0, 1), repeat=LENGTH):
                probability = float(prior)
                for time, value in enumerate(observations):
                    cpt, _ = v234.slice_likelihood(
                        v234.Episode(time % 2, (time // 12) % 2, 1)
                    )
                    probability *= _bernoulli(float(cpt[latent]), value)
                result[(latent, observations)] = probability
    elif target == "partner":
        states = tuple(PARTNER_PARAMETERS["partner_states"])
        prior = tuple(float(value) for value in PARTNER_PARAMETERS["partner_prior"])
        stay = float(PARTNER_PARAMETERS["transition_stay_probability"])
        transition = tuple(
            tuple(stay if row == column else (1.0 - stay) / (len(states) - 1)
                  for column in range(len(states)))
            for row in range(len(states))
        )
        named_emissions = {
            state: {
                channel: float(value)
                for channel, value in zip(
                    PARTNER_CHANNELS,
                    PARTNER_PARAMETERS["emission_success_probabilities"][state],
                    strict=True,
                )
            }
            for state in states
        }
        for first in range(len(states)):
            for second in range(len(states)):
                path = prior[first] * transition[first][second]
                for observations in itertools.product((0, 1), repeat=LENGTH):
                    result[((first, second), observations)] = path * (
                        _bernoulli(named_emissions[states[first]]["remaining"], observations[0])
                        * _bernoulli(named_emissions[states[second]]["remaining"], observations[1])
                    )
    elif target == "contact":
        for latent, prior in enumerate(v26b.OUTCOME_PRIOR):
            probability = float(v26b.OUTCOME_SUPPORT[latent])
            for observations in itertools.product((0, 1), repeat=LENGTH):
                result[(latent, observations)] = float(prior) * math.prod(
                    _bernoulli(probability, value) for value in observations
                )
    elif target == "context":
        def visit(
            family: str, time: int, state: tuple[int, ...], probability: float,
            path: tuple[tuple[int, ...], ...], observations: tuple[int, ...],
        ) -> None:
            row = _context_row(_descriptor(family, state))
            for value in (0, 1):
                mass = probability * row[value]
                next_path, next_obs = (*path, state), (*observations, value)
                if time == LENGTH - 1:
                    result[(family, next_path, next_obs)] = mass
                else:
                    for next_state, transition in _context_next(family, state):
                        visit(
                            family, time + 1, next_state, mass * transition,
                            next_path, next_obs,
                        )
        for family_index, family in enumerate(v24.FAMILIES):
            for state, initial in _context_initial(family):
                visit(
                    family, 0, state,
                    float(v24.PRIOR[family_index]) * initial, (), (),
                )
    else:
        raise ValueError(target)
    return MappingProxyType(result)


def v3_factors() -> Mapping[str, Mapping[tuple[Any, ...], float]]:
    protect: dict[tuple[Any, ...], float] = {}
    log_priors = np.asarray(
        [v35.structure_log_prior(item) for item in v35.PROGRAMS], dtype=float
    )
    log_priors -= float(np.max(log_priors))
    structure_prior = np.exp(log_priors)
    structure_prior /= float(structure_prior.sum())
    time, action = 1, 1
    for structure_index, structure in enumerate(v35.PROGRAMS):
        signs = (-1, 1) if structure.cross_mode_outcome else (0,)
        for sign, reliable, contact in itertools.product(signs, (0, 1), (0, 1)):
            base = float(structure_prior[structure_index]) / len(signs) / 4.0
            for active in itertools.product((0, 1), repeat=structure.active_modes):
                modes = tuple(active) + (0,) * (3 - structure.active_modes)
                policy = tuple(
                    2 if index < structure.active_modes else 1
                    for index in range(3)
                )
                cpts = (
                    v35.root_signal_probability(1, modes, structure),
                    v35.outcome_probability(policy, modes, structure, sign),
                    v35.partner_channel_probability(1, reliable, "remaining"),
                    v35.contact_probability(1, reliable, policy[0], contact),
                )
                for observations in itertools.product((0, 1), repeat=4):
                    protect[(structure_index, sign, reliable, contact, modes, observations)] = (
                        base * 0.5 ** structure.active_modes * math.prod(
                            _bernoulli(cpt, value)
                            for cpt, value in zip(cpts, observations)
                        )
                    )

    temporal: dict[tuple[Any, ...], float] = {}
    log_temporal = np.asarray(
        [v32.structure_log_prior(item) for item in v32.PROGRAMS], dtype=float
    )
    log_temporal -= float(np.max(log_temporal))
    temporal_prior = np.exp(log_temporal)
    temporal_prior /= float(temporal_prior.sum())
    for index, program in enumerate(v32.PROGRAMS):
        context = int(v32.context_path(program, TOTAL_SLICES, "natural")[time])
        probability = v32.emission_probability(
            program.scopes[0], program.dynamics[0], cue=time % 3,
            context=context, time=time, length=TOTAL_SLICES,
        )
        for value in (0, 1):
            temporal[(index, context, value)] = float(
                temporal_prior[index]
            ) * _bernoulli(probability, value)
    return MappingProxyType({
        "protect": MappingProxyType(protect),
        "temporal": MappingProxyType(temporal),
    })
