"""Shared custody, reporting, and released-seed utilities for Gate 6."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Iterable

import numpy as np


V2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = V2_ROOT.parents[2]
FROZEN_COMMIT = "60ba6e0"
RELEASED_BLOCKS = {
    "C-V20": (800347, 800646),
    "C-V21": (801392, 801691),
    "C-V22": (802051, 802350),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_frozen_identity(stage: str) -> dict[str, Any]:
    manifest_rel = f"projects/emergence-suite/v2/results/{stage}/freeze-manifest.json"
    manifest_bytes = subprocess.check_output(
        ["git", "show", f"{FROZEN_COMMIT}:{manifest_rel}"],
        cwd=REPO_ROOT,
    )
    manifest = json.loads(manifest_bytes)
    mismatches = []
    for relative, expected in manifest["files"].items():
        path = V2_ROOT / relative
        actual = _sha256(path) if path.exists() else None
        if actual != expected:
            mismatches.append(
                {"file": relative, "expected": expected, "actual": actual}
            )
    if mismatches:
        raise RuntimeError(f"{stage} frozen identity failure: {mismatches}")
    return {
        "commit": FROZEN_COMMIT,
        "manifest_file_count": len(manifest["files"]),
        "mismatches": mismatches,
    }


def released_seeds(challenge: str, count: int) -> list[int]:
    start, end = RELEASED_BLOCKS[challenge]
    seeds = list(range(start, start + count))
    if not seeds or seeds[-1] > end:
        raise ValueError(f"{challenge} requested seeds outside released block")
    return seeds


def escrow_rng(challenge: str, seed: int, component: str) -> np.random.Generator:
    start, end = RELEASED_BLOCKS[challenge]
    if seed < start or seed > end:
        raise ValueError(f"seed {seed} is outside {challenge}'s released block")
    digest = hashlib.sha256(f"{challenge}:{seed}:{component}".encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "big"))


def mean_interval(values: Iterable[float]) -> tuple[float, float, float]:
    array = np.asarray(list(values), dtype=float)
    mean = float(array.mean())
    if len(array) < 2:
        return mean, mean, mean
    half_width = 1.96 * float(array.std(ddof=1)) / np.sqrt(len(array))
    return mean, mean - half_width, mean + half_width


def proportion_interval(successes: int, total: int) -> tuple[float, float, float]:
    probability = successes / total
    denominator = 1.0 + 1.96**2 / total
    center = (probability + 1.96**2 / (2 * total)) / denominator
    half = (
        1.96
        * np.sqrt(
            probability * (1 - probability) / total
            + 1.96**2 / (4 * total**2)
        )
        / denominator
    )
    return float(probability), float(center - half), float(center + half)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("cannot write empty per-seed output")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    def native_scalar(item: Any) -> Any:
        if isinstance(item, np.generic):
            return item.item()
        if isinstance(item, np.ndarray):
            return item.tolist()
        raise TypeError(f"Object of type {item.__class__.__name__} is not JSON serializable")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=native_scalar) + "\n",
        encoding="utf-8",
    )
