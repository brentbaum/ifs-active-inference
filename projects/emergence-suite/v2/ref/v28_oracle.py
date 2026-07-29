"""Independent reduced-fixture oracle for composition-only V2.8."""

from __future__ import annotations

import itertools
from typing import Sequence

import numpy as np


def enumerate_policy(costs_input: Sequence[Sequence[float]], beta: float) -> np.ndarray:
    costs = np.array(costs_input, dtype=float, copy=True)
    policies = tuple(itertools.product(range(3), repeat=costs.shape[0]))
    totals = np.asarray(
        [sum(costs[index, value] for index, value in enumerate(policy)) for policy in policies]
    )
    weights = np.exp(-beta * (totals - totals.min()))
    return weights / weights.sum()


def clone_bytes(value: bytes, count: int) -> tuple[bytes, ...]:
    return tuple(bytes(bytearray(value)) for _ in range(count))


def ordering(depth: int | None, policy: int | None, contact: int | None, root: int | None, reduction: int | None) -> bool:
    values = (depth, policy, contact, root, reduction)
    return bool(
        all(value is not None for value in values)
        and depth < contact
        and policy < contact
        and root < reduction
    )
