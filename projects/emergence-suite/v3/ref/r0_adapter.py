"""Narrow adapter to the standing generic R0 compiler."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Mapping


_WORLD_IR = (
    Path(__file__).resolve().parents[2] / "v2" / "ref" / "world_ir.py"
)


def _module():
    name = "_suite_v3_r0_world_ir"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _WORLD_IR)
    if spec is None or spec.loader is None:
        raise RuntimeError("R0 compiler could not be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def compile_mixed_temporal_world() -> Mapping[str, Any]:
    """Compile drift on one cue subset and recurrence on another."""
    world_spec = {
        "stage_version": "V2.G0",
        "name": "v3.0-mixed-temporal-public-cell",
        "processes": [
            {
                "name": "cue_subset_drift",
                "kind": "ordered_drift",
                "scope": ["cue:0", "cue:1"],
                "length": 6,
                "states": [0, 1, 2],
                "initial": [0.7, 0.2, 0.1],
                "transition": {
                    "0": [0.75, 0.25, 0.0],
                    "1": [0.15, 0.7, 0.15],
                    "2": [0.0, 0.25, 0.75],
                },
            },
            {
                "name": "cue_subset_recurrence",
                "kind": "recurrent_context",
                "scope": ["cue:2"],
                "length": 6,
                "states": ["then", "now"],
                "initial": [0.7, 0.3],
                "transition": {"then": [0.7, 0.3], "now": [0.35, 0.65]},
            },
        ],
    }
    compiled = _module().compile_world(world_spec)
    return {
        "world_spec_hash": compiled.world_spec_hash,
        "process_kinds": {item.name: item.kind for item in compiled.processes},
        "process_scopes": {
            item.name: list(item.scope) for item in compiled.processes
        },
    }
