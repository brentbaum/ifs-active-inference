"""Independently authored exact oracles for the two V3.7 additions."""

from __future__ import annotations

import itertools
import math
from typing import Sequence


PERSISTENCE = (0.80, 0.90, 0.97)


def _partner_emission(observed: int, state: int) -> float:
    probability_one = 0.86 if state else 0.14
    return probability_one if observed else 1.0 - probability_one


def _contact_emission(observed: int, state: int, policy: int, response: int) -> float:
    probability_one = 0.14
    if response and policy == 0:
        probability_one = 0.50 if state else 0.86
    return probability_one if observed else 1.0 - probability_one


def enumerate_partner_atoms(
    partner: Sequence[int], contact: Sequence[int], policy: Sequence[int]
) -> dict[tuple[int, int, int], float]:
    """Direct path summation; shares no forward helper with production."""
    if not (len(partner) == len(contact) == len(policy)):
        raise ValueError("oracle sequences differ in length")
    result = {(r, state, response): 0.0 for r in range(3) for state in (0, 1) for response in (0, 1)}
    length = len(partner)
    for r_index, rho in enumerate(PERSISTENCE):
        for response in (0, 1):
            for path in itertools.product((0, 1), repeat=length + 1):
                mass = (1.0 / 3.0) * 0.5 * 0.5
                for time in range(length):
                    if time:
                        mass *= rho if path[time] == path[time - 1] else 1.0 - rho
                    mass *= _partner_emission(int(partner[time]), path[time])
                    mass *= _contact_emission(
                        int(contact[time]), path[time], int(policy[time]), response
                    )
                if length:
                    mass *= rho if path[-1] == path[-2] else 1.0 - rho
                result[(r_index, path[-1], response)] += mass
    normalizer = math.fsum(result.values())
    return {key: value / normalizer for key, value in result.items()}


def direct_partner_contact_forecasts(
    partner: Sequence[int], contact: Sequence[int], policy: Sequence[int],
    future_policies: Sequence[int],
) -> tuple[tuple[tuple[float, float], ...], tuple[tuple[float, float], ...]]:
    if not (len(partner) == len(contact) == len(policy)):
        raise ValueError("oracle sequences differ in length")

    # Independently authored forward summation.  It deliberately does not
    # call enumerate_partner_atoms: that complete-path implementation is the
    # separate oracle for small fixtures, while this exact elimination path
    # remains tractable for the public 48-slice forecast schedule.
    state = {
        (r_index, latent, response): 1.0 / 12.0
        for r_index in range(3)
        for latent in (0, 1)
        for response in (0, 1)
    }
    for partner_observation, contact_observation, action in zip(
        partner, contact, policy, strict=True
    ):
        updated = {
            (r_index, latent, response): mass
            * _partner_emission(int(partner_observation), latent)
            * _contact_emission(int(contact_observation), latent, int(action), response)
            for (r_index, latent, response), mass in state.items()
        }
        normalizer = math.fsum(updated.values())
        if not math.isfinite(normalizer) or normalizer <= 0.0:
            raise ValueError("non-finite or zero partner/contact normalizer")
        updated = {key: mass / normalizer for key, mass in updated.items()}

        moved = {key: 0.0 for key in updated}
        for (r_index, latent, response), mass in updated.items():
            rho = PERSISTENCE[r_index]
            moved[(r_index, latent, response)] += mass * rho
            moved[(r_index, 1 - latent, response)] += mass * (1.0 - rho)
        state = moved
    partner_rows, contact_rows = [], []
    for future_policy in future_policies:
        p_partner = math.fsum(
            mass * (0.86 if latent else 0.14)
            for (_rho, latent, _response), mass in state.items()
        )
        p_contact = math.fsum(
            mass * _contact_emission(1, latent, int(future_policy), response)
            for (_rho, latent, response), mass in state.items()
        )
        partner_rows.append((1.0 - p_partner, p_partner))
        contact_rows.append((1.0 - p_contact, p_contact))
        moved = {key: 0.0 for key in state}
        for (r_index, latent, response), mass in state.items():
            rho = PERSISTENCE[r_index]
            moved[(r_index, latent, response)] += mass * rho
            moved[(r_index, 1 - latent, response)] += mass * (1.0 - rho)
        state = moved
    return tuple(partner_rows), tuple(contact_rows)


def enumerate_danger_forecasts(
    identity_base: float, outcome_base: float
) -> tuple[tuple[float, float], tuple[float, float], float]:
    """Direct two-atom marginal with its joint normalizer."""
    identity_one = math.fsum((0.5 * identity_base, 0.5 * 0.14))
    outcome_one = math.fsum((0.5 * outcome_base, 0.5 * 0.86))
    joint_sum = math.fsum(
        0.5 * (identity_base if i else 1.0 - identity_base)
        * (outcome_base if y else 1.0 - outcome_base)
        + 0.5 * (0.14 if i else 0.86) * (0.86 if y else 0.14)
        for i, y in itertools.product((0, 1), repeat=2)
    )
    return (1.0 - identity_one, identity_one), (1.0 - outcome_one, outcome_one), joint_sum
