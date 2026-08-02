"""Generic persisted-trace custody guards.

This module is apparatus only.  It does not define or transform any scientific
quantity; it rejects a worker record containing a non-finite numeric value
before that record can reach strict JSON serialization.
"""

from __future__ import annotations

import math
from dataclasses import asdict, is_dataclass
from typing import Any, Mapping, Sequence

import numpy as np


class NonFiniteWorkerRow(ValueError):
    """Raised before serialization with stable row provenance."""

    def __init__(self, paths: Sequence[str]):
        self.paths = tuple(paths)
        super().__init__("non-finite worker-row values at " + ", ".join(self.paths))


def _nonfinite_paths(value: Any, path: str, output: list[str]) -> None:
    if is_dataclass(value):
        _nonfinite_paths(asdict(value), path, output)
        return
    if isinstance(value, Mapping):
        for key, child in value.items():
            _nonfinite_paths(child, f"{path}.{key}", output)
        return
    if isinstance(value, (tuple, list)):
        for index, child in enumerate(value):
            _nonfinite_paths(child, f"{path}[{index}]", output)
        return
    if isinstance(value, np.ndarray):
        for index, child in np.ndenumerate(value):
            suffix = "".join(f"[{item}]" for item in index)
            _nonfinite_paths(child, f"{path}{suffix}", output)
        return
    if isinstance(value, (float, np.floating)) and not math.isfinite(float(value)):
        output.append(path)


def validate_finite_worker_row(row: Mapping[str, Any]) -> None:
    """Require every floating value in ``row`` to be finite."""
    paths: list[str] = []
    _nonfinite_paths(row, "$", paths)
    if paths:
        raise NonFiniteWorkerRow(paths)
