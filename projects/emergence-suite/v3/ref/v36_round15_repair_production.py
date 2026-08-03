"""Production-semantics exact reduced grammar for Round-15 repair proofs."""

from __future__ import annotations

import itertools
from collections import defaultdict
from typing import Any


ABSENT = -1


def exact_joint(active_counts: tuple[int, int], length: int, step: str) -> dict[tuple[Any, ...], float]:
    result: dict[tuple[Any, ...], float] = defaultdict(float)
    schedule = tuple((2, 2, 2) if time % 2 else (0, 0, 0) for time in range(length))
    steps = (
        "structure_prior", "mode_paths", "root_identity_emission",
        "do_policy_outcome_emission", "partner_emission",
        "contact_emission", "temporal_context", "masking",
    )
    stage = steps.index(step)
    for active in active_counts:
        for edge in (0, 1):
            structural_mass = 1.0 / (2.0 * len(active_counts))
            if stage == 0:
                result[(active, edge, (), ABSENT, ABSENT, ABSENT, ABSENT, ABSENT)] += structural_mass
                continue
            for bits in itertools.product((0, 1), repeat=active * length):
                modes = []
                offset = 0
                for _time in range(length):
                    modes.append(tuple(bits[offset:offset + active]) + (0,) * (3 - active))
                    offset += active
                path = tuple(modes)
                path_mass = structural_mass * (0.5 ** (active * length))
                root_values = (ABSENT,) if stage < 2 else (0, 1)
                outcome_values = (ABSENT,) if stage < 3 else (0, 1)
                partner_values = (ABSENT,) if stage < 4 else (0, 1)
                contact_values = (ABSENT,) if stage < 5 else (0, 1)
                context_values: tuple[int, ...]
                if stage < 6:
                    context_values = (ABSENT,)
                elif stage == 7:
                    context_values = (ABSENT,)
                else:
                    context_values = (0, 1)
                for root, outcome, partner, contact, context in itertools.product(
                    root_values, outcome_values, partner_values,
                    contact_values, context_values,
                ):
                    mass = path_mass
                    if root != ABSENT:
                        truth = int(sum(path[-1][:active]) >= active / 2.0)
                        chance = 0.84 if truth else 0.16
                        mass *= chance if root else 1.0 - chance
                    if outcome != ABSENT:
                        centered = sum(schedule[-1][:active]) / active - 1.0
                        chance = 0.5 + (0.18 * centered if edge else 0.0)
                        mass *= chance if outcome else 1.0 - chance
                    if partner != ABSENT:
                        mass *= 0.5
                    if contact != ABSENT:
                        joint = 0.0
                        for reliable in (0, 1):
                            p_partner = 0.86 if reliable else 0.14
                            p_partner = p_partner if partner else 1.0 - p_partner
                            for response in (0, 1):
                                p_contact = 0.14
                                if response and schedule[-1][0] == 0:
                                    p_contact = 0.50 if reliable else 0.86
                                p_contact = p_contact if contact else 1.0 - p_contact
                                joint += 0.25 * p_partner * p_contact
                        mass *= joint / 0.5
                    if context != ABSENT:
                        context_truth = (length - 1) % 2
                        chance = 0.80 if context_truth else 0.20
                        mass *= chance if context else 1.0 - chance
                    result[(active, edge, path, root, outcome, partner, contact, context)] += mass
    return dict(result)

