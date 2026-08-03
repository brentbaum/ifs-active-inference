"""Production-semantics reduced enumerator for the Round-15 diagnosis.

This module intentionally shares no implementation helper with the oracle.
Only the JSON fixture declarations are common.
"""

from __future__ import annotations

import itertools
from collections import defaultdict
from typing import Any


def enumerate_atoms(active_counts: tuple[int, int], joint_policy_y: int, length: int, step: str) -> dict[tuple[Any, ...], float]:
    prior = 1.0 / len(active_counts)
    atoms: dict[tuple[Any, ...], float] = defaultdict(float)
    for active in active_counts:
        if step == "structure_prior":
            atoms[(active, joint_policy_y)] += prior
            continue
        active_bits = active * length
        for drawn in itertools.product((0, 1), repeat=active_bits):
            modes = []
            cursor = 0
            for _time in range(length):
                row = list(drawn[cursor:cursor + active]) + [0] * (3 - active)
                cursor += active
                modes.append(tuple(row))
            path_mass = prior * (0.5 ** active_bits)
            if step == "mode_paths":
                atoms[(active, joint_policy_y, tuple(modes))] += path_mass
                continue
            for roots in itertools.product((0, 1), repeat=length):
                mass = path_mass
                for mode, root in zip(modes, roots):
                    rooted = mode[:active]
                    truth = int(bool(rooted) and sum(rooted) >= len(rooted) / 2.0)
                    probability = 0.84 if truth else 0.16
                    mass *= probability if root else 1.0 - probability
                if step == "root_identity_emission":
                    atoms[(active, joint_policy_y, tuple(modes), roots)] += mass
                    continue
                # The actual native generator chooses an intervention vector
                # as a function of the latent active count.
                policies = tuple(
                    tuple((2 if time % 2 else 0) if index < active else 1 for index in range(3))
                    for time in range(length)
                )
                for outcomes in itertools.product((0, 1), repeat=length):
                    outcome_mass = mass
                    for policy, mode, outcome in zip(policies, modes, outcomes):
                        centered = sum(policy[:active]) / active - 1.0
                        p1 = 0.5 + (0.18 * centered if joint_policy_y else 0.0)
                        outcome_mass *= p1 if outcome else 1.0 - p1
                    atoms[(active, joint_policy_y, tuple(modes), roots, policies, outcomes)] += outcome_mass
    return dict(atoms)
