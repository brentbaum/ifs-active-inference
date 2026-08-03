"""Independent direct-factorization oracle for Round-15 reduced fixtures."""

from __future__ import annotations

import itertools
from collections import defaultdict
from typing import Any


def direct_joint(count_pair: tuple[int, int], edge_value: int, horizon: int, ladder_item: str) -> dict[tuple[Any, ...], float]:
    result: dict[tuple[Any, ...], float] = defaultdict(float)
    fixed_policies = tuple(
        (2, 2, 2) if time % 2 else (0, 0, 0)
        for time in range(horizon)
    )
    for k in count_pair:
        structural_mass = 1.0 / float(len(count_pair))
        if ladder_item == "structure_prior":
            result[(k, edge_value)] += structural_mass
            continue
        live_positions = [(time, slot) for time in range(horizon) for slot in range(k)]
        for values in itertools.product((0, 1), repeat=len(live_positions)):
            path = [[0, 0, 0] for _ in range(horizon)]
            for (time, slot), value in zip(live_positions, values):
                path[time][slot] = value
            path_tuple = tuple(tuple(row) for row in path)
            latent_mass = structural_mass / (2.0 ** len(live_positions))
            if ladder_item == "mode_paths":
                result[(k, edge_value, path_tuple)] += latent_mass
                continue
            for root_values in itertools.product((0, 1), repeat=horizon):
                root_mass = latent_mass
                for row, observed in zip(path_tuple, root_values):
                    state = int(sum(row[:k]) >= k / 2.0)
                    chance = 0.84 if state else 0.16
                    root_mass *= (chance, 1.0 - chance)[1 - observed]
                if ladder_item == "root_identity_emission":
                    result[(k, edge_value, path_tuple, root_values)] += root_mass
                    continue
                for ys in itertools.product((0, 1), repeat=horizon):
                    atom_mass = root_mass
                    for policy, row, y in zip(fixed_policies, path_tuple, ys):
                        centered = sum(policy[:k]) / k - 1.0
                        chance = 0.5 + (0.18 * centered if edge_value else 0.0)
                        atom_mass *= chance if y else 1.0 - chance
                    result[(k, edge_value, path_tuple, root_values, fixed_policies, ys)] += atom_mass
    return dict(result)
