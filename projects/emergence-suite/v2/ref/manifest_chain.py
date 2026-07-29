"""Public verification of a base freeze manifest plus committed addenda."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifest_chain(
    repository_root: Path,
    base_manifest: str,
    addenda: Iterable[str] = (),
) -> dict[str, object]:
    """Overlay ordered manifest addenda and verify the effective file chain.

    Paths in the manifest are resolved relative to ``repository_root``.
    Addenda are explicit custody inputs and are applied in the supplied order.
    """
    root = Path(repository_root).resolve()
    base_relative = str(base_manifest)
    base_path = root / base_relative
    base_payload = json.loads(base_path.read_text(encoding="utf-8"))
    effective_files = dict(base_payload["files"])
    custody_addenda = []
    overlaid_entries = []

    for relative in addenda:
        addendum_relative = str(relative)
        addendum_path = root / addendum_relative
        payload = json.loads(addendum_path.read_text(encoding="utf-8"))
        declared_base = payload.get("addendum_to")
        if declared_base not in {
            base_relative,
            Path(base_relative).name,
        }:
            raise ValueError(
                f"{addendum_relative} does not declare addendum_to "
                f"{base_relative}"
            )
        entries = dict(payload["files"])
        effective_files.update(entries)
        overlaid_entries.extend(entries)
        custody_addenda.append(
            {
                "file": addendum_relative,
                "sha256": _sha256(addendum_path),
            }
        )

    mismatches = []
    for relative, expected in effective_files.items():
        path = root / relative
        observed = _sha256(path) if path.exists() else None
        if observed != expected:
            mismatches.append(
                {
                    "file": relative,
                    "expected": expected,
                    "observed": observed,
                }
            )

    return {
        "custody_files": {
            "base": {
                "file": base_relative,
                "sha256": _sha256(base_path),
            },
            "addenda": custody_addenda,
        },
        "base_manifest_file_count": len(base_payload["files"]),
        "effective_manifest_file_count": len(effective_files),
        "overlaid_entries": sorted(set(overlaid_entries)),
        "mismatches": mismatches,
        "passed": not mismatches,
    }
