"""Independent arithmetic oracle for the V3.6-R1 bridge.

This module imports no production bridge helper.  It checks copied documents,
binary normalization, delivered-token scoring, and credible-set coverage from
plain serialized values.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping, Sequence


def canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def binary_normalization_error(
    predictions: Mapping[str, Sequence[Sequence[float]]],
) -> float:
    largest = 0.0
    for rows in predictions.values():
        for row in rows:
            if len(row) != 2 or min(row) < 0.0:
                return math.inf
            largest = max(largest, abs(math.fsum(row) - 1.0))
    return largest


def delivered_mean_log_score(
    probabilities: Sequence[Sequence[float]],
    observed: Sequence[int | None],
    delivered: Sequence[bool],
) -> float:
    values = []
    for row, value, available in zip(probabilities, observed, delivered):
        if not available or value is None:
            continue
        values.append(math.log(float(row[int(value)])))
    if not values:
        raise ValueError("oracle received no delivered observations")
    return math.fsum(values) / len(values)


def credible_set_contains(
    class_probabilities: Mapping[str, float],
    truth: str,
    mass: float,
) -> bool:
    cumulative = 0.0
    for key, probability in sorted(
        class_probabilities.items(), key=lambda item: (-item[1], item[0])
    ):
        cumulative += probability
        if key == truth:
            return True
        if cumulative >= mass:
            return False
    return False
