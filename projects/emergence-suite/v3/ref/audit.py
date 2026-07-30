"""V3 scientific-state and import-boundary audits."""

from __future__ import annotations

import ast
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any


BANNED_MODULES = {
    "v232_formation",
    "v24",
    "v25a",
    "v25b",
    "v234",
    "v26b",
    "v27",
    "v28",
}
BANNED_STATE_NAMES = {
    "formed",
    "part",
    "protector",
    "exile",
    "burden",
    "unburdened",
    "permission",
    "access",
    "polarized",
    "witnessing",
}
ALLOWED_MUTABLE_STORES = {
    "latent_posterior",
    "parameter_posterior",
    "structure_posterior",
    "model_evidence",
}


def audit_state(value: Any) -> tuple[str, ...]:
    violations: list[str] = []
    if is_dataclass(value):
        for field in fields(value):
            name = field.name.lower()
            child = getattr(value, field.name)
            if name in BANNED_STATE_NAMES:
                violations.append(f"forbidden scientific field: {field.name}")
            if isinstance(child, (dict, list, set)) and name not in ALLOWED_MUTABLE_STORES:
                violations.append(f"mutable field outside posterior stores: {field.name}")
    return tuple(violations)


def audit_imports(ref_root: Path) -> tuple[str, ...]:
    violations = []
    for path in sorted(ref_root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[-1] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [(node.module or "").split(".")[-1]]
            else:
                continue
            for name in names:
                if name in BANNED_MODULES:
                    violations.append(f"{path.name}: banned import {name}")
    return tuple(violations)
