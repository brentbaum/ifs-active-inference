#!/usr/bin/env python3
"""V3.6 Gate 4: selective lesions across the five composed stages.

This runner intentionally imports no R1 fixture, bridge-adapter, external-world,
calibration, or tournament module.  Every structural lesion is scored by the
frozen constituent stage and checked against the same full posterior
conditioned on the declared restricted prior.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from dataclasses import asdict, replace
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT.parent
sys.path.insert(0, str(SUITE_ROOT))
sys.path.insert(0, str(ROOT))

from ref import v31, v32, v33, v34, v35, v36  # noqa: E402
from ref.trace_sink import require_trace_sink, traced_execution  # noqa: E402


RESULTS = ROOT / "results" / "V3.6"
GATE4_BLOCK = (3_630_000, 3_634_999)
TOLERANCE = 1e-10
LESIONS = ("grow_mode_slot", "split_context_slot", "prune_M1_G", "relate_L_PREC", "protect_joint_policy")


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(child) for child in value]
    if hasattr(value, "__dataclass_fields__"):
        return _plain(asdict(value))
    if isinstance(value, np.generic):
        return value.item()
    return value


def _canonical(value: Any) -> bytes:
    return (
        json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        + b"\n"
    )


def _write_json(name: str, value: Any) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / name).write_text(
        json.dumps(_plain(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _conditioned_error(
    full_keys: Sequence[Any],
    full_probabilities: Sequence[float],
    restricted_keys: Sequence[Any],
    restricted_probabilities: Sequence[float],
    allowed,
) -> float:
    retained = {
        key: float(probability)
        for key, probability in zip(full_keys, full_probabilities)
        if allowed(key)
    }
    mass = math.fsum(retained.values())
    if not math.isfinite(mass) or mass <= 0.0:
        return math.inf
    if set(retained) != set(restricted_keys):
        return math.inf
    return max(
        abs(float(probability) - retained[key] / mass)
        for key, probability in zip(restricted_keys, restricted_probabilities)
    )


def _posterior_distance(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        return math.inf
    return max(abs(float(a) - float(b)) for a, b in zip(left, right))


def _world_hash(world: Any) -> str:
    return hashlib.sha256(_canonical(asdict(world))).hexdigest()


def _mask_imaginal(world: v33.ReductionWorld) -> v33.ReductionWorld:
    return replace(
        world,
        slices=tuple(
            replace(
                item,
                mode=None,
                root=None,
                world=None,
                policy_proposal=None,
                action=None,
                outcome=None,
            )
            if item.episode_kind == "imaginal_post"
            else item
            for item in world.slices
        ),
    )


def _drop_imaginal(world: v33.ReductionWorld) -> v33.ReductionWorld:
    return replace(
        world,
        slices=tuple(item for item in world.slices if item.episode_kind != "imaginal_post"),
    )


@traced_execution
def _worker(task: tuple[int, str]) -> dict[str, Any]:
    seed, lesion = task
    if not GATE4_BLOCK[0] <= seed <= GATE4_BLOCK[1]:
        raise ValueError("Gate-4 seed outside authorized block")
    require_trace_sink("v36.gate4.selective_lesion", seed=seed, lesion=lesion)

    if lesion == "grow_mode_slot":
        config = v31.FormationConfig("repeated", "low", "broad", "safe", "effective", "censored", 48)
        world = v31.generate_world(seed, config, released_block=GATE4_BLOCK)
        masked_world = replace(
            world,
            slices=tuple(replace(item, mode_observed=False) for item in world.slices),
        )
        full = v31.score_world(masked_world)
        restricted = v31.score_world(world, lesions=frozenset({"mode_slot"}))
        identity_error = _conditioned_error(
            full.programs,
            full.probabilities,
            restricted.programs,
            restricted.probabilities,
            lambda program: v31.program_values(program)["active_mode"] == 0,
        )
        target_error = max(restricted.active_mode_probability, restricted.part_probability)
        mask_error = identity_error
        descriptive = {
            "full_part_probability": full.part_probability,
            "full_W_Y_probability": full.edge_probabilities["W_Y"],
            "restricted_W_Y_probability": restricted.edge_probabilities["W_Y"],
        }
        normalization_error = abs(math.fsum(restricted.probabilities) - 1.0)

    elif lesion == "split_context_slot":
        structure = v32.TemporalStructure(
            2,
            ("context_specific", "context_specific"),
            ("discrete_recurrent_context", "discrete_recurrent_context"),
        )
        world = v32.generate_world(
            seed,
            structure=structure,
            length=48,
            cue_count=3,
            evidence_style="witnessing",
            released_block=GATE4_BLOCK,
        )
        masked = frozenset({"active_contexts"})
        full = v32.score_world(world, masked_channels=masked)
        restricted = v32.score_world(
            world,
            restrictions={"active_contexts": (1,)},
            masked_channels=masked,
        )
        identity_error = _conditioned_error(
            full.programs,
            full.probabilities,
            restricted.programs,
            restricted.probabilities,
            lambda program: program.active_contexts == 1,
        )
        altered = replace(
            world,
            slices=tuple(
                replace(item, active_context_token=(item.active_context_token + 1) % 3)
                for item in world.slices
            ),
        )
        altered_masked = v32.score_world(altered, masked_channels=masked)
        mask_error = _posterior_distance(full.probabilities, altered_masked.probabilities)
        target_error = math.fsum(restricted.active_context_probabilities[1:])
        descriptive = {
            "full_context_specific": full.scope_probability("cue_emission", "context_specific"),
            "full_recurrent": full.dynamics_probability("cue_emission", "discrete_recurrent_context"),
            "restricted_recurrent": restricted.dynamics_probability("cue_emission", "discrete_recurrent_context"),
        }
        normalization_error = abs(math.fsum(restricted.probabilities) - 1.0)

    elif lesion == "prune_M1_G":
        config = v33.ReductionConfig(
            "configural", "post_revision", corrective_length=18, return_length=18
        )
        world = v33.generate_world(seed, config, released_block=GATE4_BLOCK)
        full_score = v33.score_world(world)
        restricted_score = v33.score_world(world, restrictions={"M1_G": (0,)})
        full = full_score.current
        restricted = restricted_score.current
        identity_error = _conditioned_error(
            full.programs,
            full.probabilities,
            restricted.programs,
            restricted.probabilities,
            lambda program: v31.program_values(program)["M1_G"] == 0,
        )
        masked = v33.score_world(_mask_imaginal(world)).current
        dropped = v33.score_world(_drop_imaginal(world)).current
        mask_error = _posterior_distance(masked.probabilities, dropped.probabilities)
        target_error = restricted.edge_probabilities["M1_G"]
        descriptive = {
            "full_M1_G_probability": full.edge_probabilities["M1_G"],
            "full_W_Y_probability": full.edge_probabilities["W_Y"],
            "restricted_W_Y_probability": restricted.edge_probabilities["W_Y"],
        }
        normalization_error = abs(math.fsum(restricted.probabilities) - 1.0)

    elif lesion == "relate_L_PREC":
        config = v34.RelateConfig("reliable", True, True, broadcast=True, length=48)
        world = v34.generate_world(seed, config, released_block=GATE4_BLOCK)
        full = v34.score_world(world)
        restricted = v34.score_world(world, restrictions={"L_PREC": (0,)})
        identity_error = _conditioned_error(
            full.programs,
            full.structure_probabilities,
            restricted.programs,
            restricted.structure_probabilities,
            lambda program: v34.structure_values(program)["L_PREC"] == 0,
        )
        masked = v34.score_world(world, relational_enabled=False)
        altered_world = replace(
            world,
            observations=tuple(
                replace(
                    item,
                    relational=tuple(None if value is None else 1 - value for value in item.relational),
                )
                for item in world.observations
            ),
        )
        altered_masked = v34.score_world(altered_world, relational_enabled=False)
        mask_error = _posterior_distance(masked.structure_probabilities, altered_masked.structure_probabilities)
        target_error = max(
            restricted.edge_probabilities["L_PREC"],
            max(abs(value - v34.BASE_PRECISION) for value in restricted.local_precision),
        )
        descriptive = {
            "full_L_PREC_probability": full.edge_probabilities["L_PREC"],
            "full_L_Y_probability": full.edge_probabilities["L_Y"],
            "restricted_L_Y_probability": restricted.edge_probabilities["L_Y"],
        }
        normalization_error = abs(math.fsum(restricted.structure_probabilities) - 1.0)

    elif lesion == "protect_joint_policy":
        config = v35.ProtectConfig(
            "all", "remaining", "high", "mixed", 3, "allied", "all", "delivered", "delivered", 64
        )
        world = v35.generate_world(seed, config, released_block=GATE4_BLOCK)
        full = v35.score_world(world)
        restricted = v35.score_world(world, restrictions={"JOINT_POLICY_Y": (0,)})
        identity_error = _conditioned_error(
            full.components,
            full.probabilities,
            restricted.components,
            restricted.probabilities,
            lambda component: v35.program_values(component[0])["JOINT_POLICY_Y"] == 0,
        )
        registration_masked = v35.score_world(world, registration_enabled=False)
        mask_error = _posterior_distance(full.probabilities, registration_masked.probabilities)
        target_error = restricted.edge_probabilities["JOINT_POLICY_Y"]
        descriptive = {
            "full_joint_policy_probability": full.edge_probabilities["JOINT_POLICY_Y"],
            "full_cross_mode_probability": full.edge_probabilities["CROSS_MODE_Y"],
            "restricted_cross_mode_probability": restricted.edge_probabilities["CROSS_MODE_Y"],
        }
        normalization_error = abs(math.fsum(restricted.probabilities) - 1.0)

    else:
        raise ValueError(f"unknown Gate-4 lesion {lesion}")

    return {
        "seed": seed,
        "lesion": lesion,
        "world_sha256": _world_hash(world),
        "restricted_prior_identity_error": float(identity_error),
        "masked_channel_neutrality_error": float(mask_error),
        "normalization_error": float(normalization_error),
        "finite": bool(
            math.isfinite(identity_error)
            and math.isfinite(mask_error)
            and math.isfinite(normalization_error)
            and math.isfinite(target_error)
        ),
        "declared_target_error": float(target_error),
        "unrelated_absolute_movement_descriptive": descriptive,
    }


def _trace_map(tasks: Sequence[tuple[int, str]]) -> list[dict[str, Any]]:
    RESULTS.mkdir(parents=True, exist_ok=True)
    trace_path = RESULTS / "gate-4-traces.jsonl"
    hash_path = RESULTS / "gate-4-trace-hashes.json"
    if trace_path.exists() or hash_path.exists():
        raise RuntimeError("custody refusal: Gate-4 output already exists")
    rows: list[dict[str, Any]] = []
    record_hashes: list[dict[str, Any]] = []
    file_hash = hashlib.sha256()
    processes = max(1, min(8, (os.cpu_count() or 2) - 1))
    with trace_path.open("xb") as handle:
        with get_context("spawn").Pool(processes) as pool:
            for row in pool.imap(_worker, tasks, chunksize=2):
                encoded = _canonical(row)
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
                file_hash.update(encoded)
                rows.append(row)
                record_hashes.append(
                    {"seed": row["seed"], "sha256": hashlib.sha256(encoded).hexdigest()}
                )
    ledger = {
        "file": trace_path.name,
        "file_sha256": file_hash.hexdigest(),
        "record_count": len(rows),
        "seed_block": list(GATE4_BLOCK),
        "records": record_hashes,
        "persist_before_aggregation": True,
    }
    _write_json(hash_path.name, ledger)
    if hashlib.sha256(trace_path.read_bytes()).hexdigest() != ledger["file_sha256"]:
        raise RuntimeError("Gate-4 trace hash verification failed")
    expected = list(range(GATE4_BLOCK[0], GATE4_BLOCK[1] + 1))
    if [row["seed"] for row in rows] != expected:
        raise RuntimeError("Gate-4 seed order is not ascending and gap-free")
    return rows


def run_gate4() -> dict[str, Any]:
    proof = json.loads(
        (RESULTS / "v3.6-r1-round13-native-fixture-identity-proofs.json").read_text(encoding="utf-8")
    )
    if proof.get("verdict") != "PASS":
        raise RuntimeError("all eight Round-13 pre-block proofs must pass before Gate 4")
    tasks = [
        (seed, LESIONS[(seed - GATE4_BLOCK[0]) // 1000])
        for seed in range(GATE4_BLOCK[0], GATE4_BLOCK[1] + 1)
    ]
    rows = _trace_map(tasks)
    cells: dict[str, Any] = {}
    failures: list[str] = []
    for lesion in LESIONS:
        selected = [row for row in rows if row["lesion"] == lesion]
        cell = {
            "world_count": len(selected),
            "restricted_prior_identity_error_max": max(row["restricted_prior_identity_error"] for row in selected),
            "masked_channel_neutrality_error_max": max(row["masked_channel_neutrality_error"] for row in selected),
            "normalization_error_max": max(row["normalization_error"] for row in selected),
            "declared_target_error_max": max(row["declared_target_error"] for row in selected),
            "finite_all": all(row["finite"] for row in selected),
            "unrelated_absolute_movement": {
                "classification": "DESCRIPTIVE_RENORMALIZATION_MOVEMENT",
                "note": "Absolute movement in non-target coordinates is not a selectivity criterion after conditioning the structure prior.",
            },
        }
        cell["passed"] = (
            cell["world_count"] == 1000
            and cell["restricted_prior_identity_error_max"] <= TOLERANCE
            and cell["masked_channel_neutrality_error_max"] <= TOLERANCE
            and cell["normalization_error_max"] <= TOLERANCE
            and cell["declared_target_error_max"] <= TOLERANCE
            and cell["finite_all"]
        )
        if not cell["passed"]:
            failures.append(f"{lesion}: {cell}")
        cells[lesion] = cell

    result = {
        "stage": "V3.6",
        "gate": 4,
        "seed_block": list(GATE4_BLOCK),
        "seeds_consumed": len(rows),
        "ascending_gap_free": [row["seed"] for row in rows]
        == list(range(GATE4_BLOCK[0], GATE4_BLOCK[1] + 1)),
        "proof_precondition": {
            "file": "v3.6-r1-round13-native-fixture-identity-proofs.json",
            "verdict": proof["verdict"],
        },
        "selectivity_definition": "lesioned posterior equals the full posterior conditioned on the declared restricted structure prior",
        "masking_definition": "candidate-common masked channel contribution is likelihood one and invariant to the masked token",
        "cells": cells,
        "tolerance": TOLERANCE,
        "bounds": dict(v36.finite_information_bounds()),
        "forbidden_import_audit": {
            "native_fixture_code": False,
            "bridge_adapters": False,
            "external_generator": False,
            "calibration_definitions": False,
            "tournament_statistics": False,
        },
        "custody": {
            "trace_file": "gate-4-traces.jsonl",
            "trace_hash_ledger": "gate-4-trace-hashes.json",
            "persisted_before_aggregation": True,
            "barred_blocks_touched": False,
            "escrow_touched": False,
        },
        "failures": failures,
        "verdict": "PASS" if not failures else "FAIL",
    }
    _write_json("gate-4.json", result)
    report = [
        "# V3.6 Gate 4 — composed selective lesions",
        "",
        f"Verdict: **{result['verdict']}**.",
        "",
        "The five 1,000-world cells delete one frozen production in each constituent stage. Selectivity is the exact restricted-prior identity; unrelated absolute posterior movement after renormalization is descriptive.",
        "",
        "| constituent lesion | restricted identity max | masking max | target max | pass |",
        "|---|---:|---:|---:|:---:|",
    ]
    for lesion, cell in cells.items():
        report.append(
            f"| {lesion} | {cell['restricted_prior_identity_error_max']:.3g} | "
            f"{cell['masked_channel_neutrality_error_max']:.3g} | "
            f"{cell['declared_target_error_max']:.3g} | {cell['passed']} |"
        )
    report.extend([
        "",
        "Every per-world row, including its runtime event ledger and world hash, was persisted and hashed before these aggregates were computed.",
        "",
    ])
    (RESULTS / "gate-4-report.md").write_text("\n".join(report), encoding="utf-8")
    if failures:
        _write_json(
            "gate-4-diagnosis-stub.json",
            {"stage": "V3.6", "gate": 4, "failures": failures, "next_action": "HONEST_STOP"},
        )
    return result


def main() -> None:
    result = run_gate4()
    print(json.dumps({"gate": 4, "verdict": result["verdict"]}, sort_keys=True))


if __name__ == "__main__":
    main()
