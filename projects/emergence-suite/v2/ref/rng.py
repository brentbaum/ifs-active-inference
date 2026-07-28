"""Deterministic component-specific random streams."""

from __future__ import annotations

import hashlib

import numpy as np


MAX_DEVELOPMENT_SEED = 799_999


def component_rng(
    seed: int,
    component: str,
    *,
    released_block: tuple[int, int] | None = None,
) -> np.random.Generator:
    if released_block is None:
        if seed < 0 or seed > MAX_DEVELOPMENT_SEED:
            raise ValueError("development seeds must be in [0, 799999]")
    else:
        start, end = released_block
        if start < 0 or end < start or not start <= seed <= end:
            raise ValueError("seed is outside the evaluator-released block")
    digest = hashlib.sha256(f"suite-v2:{seed}:{component}".encode()).digest()
    entropy = int.from_bytes(digest[:8], "big")
    return np.random.default_rng(entropy)
