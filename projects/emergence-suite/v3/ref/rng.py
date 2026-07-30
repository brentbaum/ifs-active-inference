"""Epoch-C component RNG and custody checks."""

from __future__ import annotations

import hashlib

import numpy as np


STAGE_VERSION = "V3.0"
DEVELOPMENT_BLOCK = (3_000_000, 3_015_999)


def component_rng(
    seed: int,
    component: str,
    *,
    time_or_event: int | str = 0,
    released_block: tuple[int, int] | None = None,
) -> np.random.Generator:
    """Return a deterministic RNG whose key contains all custody coordinates."""
    block = DEVELOPMENT_BLOCK if released_block is None else released_block
    start, end = map(int, block)
    if start < 0 or end < start or not start <= int(seed) <= end:
        raise ValueError("seed is outside the authorized V3 block")
    key = f"{STAGE_VERSION}:{int(seed)}:{component}:{time_or_event}"
    entropy = int.from_bytes(hashlib.sha256(key.encode()).digest()[:16], "big")
    return np.random.default_rng(entropy)


def component_key(
    seed: int, component: str, time_or_event: int | str
) -> tuple[str, int, str, int | str]:
    return STAGE_VERSION, int(seed), str(component), time_or_event
