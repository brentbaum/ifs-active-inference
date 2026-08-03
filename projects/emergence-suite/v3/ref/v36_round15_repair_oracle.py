"""Independent direct-factorization oracle for repaired Round-15 fixtures."""

from __future__ import annotations

from collections import defaultdict
from itertools import product
from typing import Any


MISSING = -1


def enumerate_joint(k_support: tuple[int, int], horizon: int, factor_name: str) -> dict[tuple[Any, ...], float]:
    output: dict[tuple[Any, ...], float] = defaultdict(float)
    order = {
        "structure_prior": 0, "mode_paths": 1,
        "root_identity_emission": 2, "do_policy_outcome_emission": 3,
        "partner_emission": 4, "contact_emission": 5,
        "temporal_context": 6, "masking": 7,
    }
    level = order[factor_name]
    common_do = [((0, 0, 0), (2, 2, 2))[time % 2] for time in range(horizon)]
    for k in k_support:
        for z in (0, 1):
            base = 1.0 / float(2 * len(k_support))
            if level == 0:
                output[(k, z, (), MISSING, MISSING, MISSING, MISSING, MISSING)] += base
                continue
            positions = [(time, slot) for time in range(horizon) for slot in range(k)]
            for assignment in product((0, 1), repeat=len(positions)):
                matrix = [[0, 0, 0] for _ in range(horizon)]
                for position, bit in zip(positions, assignment):
                    matrix[position[0]][position[1]] = bit
                path = tuple(tuple(row) for row in matrix)
                latent_weight = base / (2 ** len(positions))
                roots = (MISSING,) if level < 2 else (0, 1)
                outcomes = (MISSING,) if level < 3 else (0, 1)
                partners = (MISSING,) if level < 4 else (0, 1)
                contacts = (MISSING,) if level < 5 else (0, 1)
                contexts = (MISSING,) if level < 6 or level == 7 else (0, 1)
                for r, y, p, d, c in product(roots, outcomes, partners, contacts, contexts):
                    weight = latent_weight
                    if r != MISSING:
                        state = int(sum(path[-1][0:k]) * 2 >= k)
                        probability = (0.84 if state else 0.16)
                        weight *= probability if r == 1 else 1 - probability
                    if y != MISSING:
                        average = sum(common_do[-1][0:k]) / float(k)
                        probability = 0.5 + (0.18 * (average - 1.0) if z else 0.0)
                        weight *= probability if y == 1 else 1 - probability
                    if p != MISSING and d == MISSING:
                        weight *= 0.5
                    elif p != MISSING and d != MISSING:
                        pair_probability = 0.0
                        for latent_partner in (0, 1):
                            partner_one = (0.14, 0.86)[latent_partner]
                            partner_factor = partner_one if p else 1 - partner_one
                            for theta in (0, 1):
                                contact_one = 0.14
                                if theta == 1 and common_do[-1][0] == 0:
                                    contact_one = (0.86, 0.50)[latent_partner]
                                contact_factor = contact_one if d else 1 - contact_one
                                pair_probability += 0.25 * partner_factor * contact_factor
                        weight *= pair_probability
                    if c != MISSING:
                        hidden_context = (horizon - 1) % 2
                        probability = (0.20, 0.80)[hidden_context]
                        weight *= probability if c else 1 - probability
                    output[(k, z, path, r, y, p, d, c)] += weight
    return dict(output)

