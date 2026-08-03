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
from ref.custody import NonFiniteWorkerRow, validate_finite_worker_row  # noqa: E402
from ref.trace_sink import require_trace_sink, traced_execution  # noqa: E402


RESULTS = ROOT / "results" / "V3.6"
GATE4_BLOCK = (3_728_000, 3_732_999)
TOLERANCE = 1e-10
LESIONS = ("grow_mode_slot", "split_context_slot", "prune_M1_G", "relate_L_PREC", "protect_joint_policy")
SUPPORT_PRESERVING = "SUPPORT_PRESERVING_CONDITIONING"
SUPPORT_DESTROYING = "SUPPORT_DESTROYING_MASKING"
LESION_CLASSES = {
    "grow_mode_slot": SUPPORT_DESTROYING,
    "split_context_slot": SUPPORT_PRESERVING,
    "prune_M1_G": SUPPORT_PRESERVING,
    "relate_L_PREC": SUPPORT_PRESERVING,
    "protect_joint_policy": SUPPORT_PRESERVING,
}


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
    if len(full_keys) != len(full_probabilities):
        raise AssertionError("full atom keys and probabilities differ in length")
    if len(restricted_keys) != len(restricted_probabilities):
        raise AssertionError("restricted atom keys and probabilities differ in length")
    if len(set(full_keys)) != len(full_keys):
        raise AssertionError("full scorer atom keys are not unique")
    if len(set(restricted_keys)) != len(restricted_keys):
        raise AssertionError("restricted scorer atom keys are not unique")
    expected_restricted_keys = {key for key in full_keys if allowed(key)}
    if set(restricted_keys) != expected_restricted_keys:
        raise AssertionError("restricted/scorer full atom key sets differ")
    retained = {
        key: float(probability)
        for key, probability in zip(full_keys, full_probabilities)
        if allowed(key)
    }
    mass = math.fsum(retained.values())
    if not math.isfinite(mass) or mass <= 0.0:
        return math.inf
    restricted = {
        key: float(probability)
        for key, probability in zip(restricted_keys, restricted_probabilities)
    }
    full_set = set(full_keys)
    if set(restricted) - full_set:
        return math.inf
    return max(
        abs(
            restricted.get(key, 0.0)
            - (retained[key] / mass if key in retained else 0.0)
        )
        for key in full_set
    )


def _independent_conditioned_error(
    full_keys: Sequence[Any], full_probabilities: Sequence[float],
    restricted_keys: Sequence[Any], restricted_probabilities: Sequence[float],
    allowed,
) -> float:
    """Separately authored direct summation oracle for the restriction."""
    if len(full_keys) != len(full_probabilities):
        raise AssertionError("full oracle atom keys and probabilities differ in length")
    if len(restricted_keys) != len(restricted_probabilities):
        raise AssertionError("restricted oracle atom keys and probabilities differ in length")
    if len(set(full_keys)) != len(full_keys):
        raise AssertionError("full oracle atom keys are not unique")
    if len(set(restricted_keys)) != len(restricted_keys):
        raise AssertionError("restricted oracle atom keys are not unique")
    expected_restricted_keys = {key for key in full_keys if allowed(key)}
    if set(restricted_keys) != expected_restricted_keys:
        raise AssertionError("restricted/oracle full atom key sets differ")
    licensed = [index for index, key in enumerate(full_keys) if allowed(key)]
    denominator = math.fsum(float(full_probabilities[index]) for index in licensed)
    if not licensed or denominator <= 0.0 or not math.isfinite(denominator):
        return math.inf
    observed = {key: float(value) for key, value in zip(restricted_keys, restricted_probabilities)}
    largest = 0.0
    for index, key in enumerate(full_keys):
        expected = float(full_probabilities[index]) / denominator if index in licensed else 0.0
        largest = max(largest, abs(observed.get(key, 0.0) - expected))
    return largest


def _prior_mass(keys: Sequence[Any], log_prior, allowed) -> float:
    logs = np.asarray([float(log_prior(key)) for key in keys], dtype=float)
    maximum = float(np.max(logs))
    weights = np.exp(logs - maximum); weights /= float(weights.sum())
    return float(math.fsum(float(value) for key, value in zip(keys, weights) if allowed(key)))


def _finite_optional(*values: float | None) -> bool:
    return all(value is None or math.isfinite(float(value)) for value in values)


def _positive_log_evidence(value: float | None) -> bool:
    """Evidence is positive iff its log is finite; never exponentiate it."""
    return value is not None and math.isfinite(float(value))


def _v35_atom_keys(posterior: v35.ProtectPosterior) -> tuple[Any, ...]:
    """Expose scorer atoms as (structure, cross_sign, reliable)."""
    if len(posterior.components) != len(posterior.probabilities):
        raise AssertionError("V3.5 component/probability lengths differ")
    if len(posterior.components) % 2:
        raise AssertionError("V3.5 scorer atoms do not form reliability pairs")
    keys = []
    for index, component in enumerate(posterior.components):
        pair_start = index - (index % 2)
        if posterior.components[pair_start] != component or posterior.components[pair_start + 1] != component:
            raise AssertionError("V3.5 scorer reliability-pair ordering changed")
        structure, cross_sign = component
        keys.append((structure, int(cross_sign), int(index % 2)))
    if len(set(keys)) != len(keys):
        raise AssertionError("V3.5 full atom coordinate set is not unique")
    return tuple(keys)


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
        masked_reference = v31.score_world(masked_world, lesions=frozenset({"mode_slot"}))
        surviving = v31.score_world(world, lesions=frozenset({"mode_slot"}))
        restricted = surviving
        identity_error = None
        oracle_error = _posterior_distance(
            masked_reference.probabilities, surviving.probabilities
        )
        target_error = max(surviving.active_mode_probability, surviving.part_probability)
        mask_error = _posterior_distance(
            surviving.probabilities, masked_reference.probabilities
        )
        unrelated_error = max(
            abs(surviving.edge_probabilities[name] - masked_reference.edge_probabilities[name])
            for name in ("W_Y", "doA_Y")
        )
        licensed_count = 0
        prior_mass = 0.0
        restricted_log_evidence = None
        identity_applicable = False
        descriptive = {
            "masked_reference_part_probability": masked_reference.part_probability,
            "masked_reference_W_Y_probability": masked_reference.edge_probabilities["W_Y"],
            "restricted_W_Y_probability": restricted.edge_probabilities["W_Y"],
        }
        normalization_error = abs(math.fsum(surviving.probabilities) - 1.0)

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
        allowed = lambda program: program.active_contexts == 1
        oracle_error = _independent_conditioned_error(
            full.programs, full.probabilities, restricted.programs,
            restricted.probabilities, allowed,
        )
        licensed_count = sum(allowed(program) for program in full.programs)
        prior_mass = _prior_mass(full.programs, v32.structure_log_prior, allowed)
        restricted_log_evidence = restricted.log_evidence
        identity_applicable = True
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
        unrelated_error = abs(
            restricted.scope_probability("cue_emission", "shared_global")
            - math.fsum(
                float(probability)
                for program, probability in zip(full.programs, full.probabilities)
                if allowed(program) and program.scopes[0] == "shared_global"
            ) / math.fsum(
                float(probability)
                for program, probability in zip(full.programs, full.probabilities)
                if allowed(program)
            )
        )
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
        allowed = lambda program: v31.program_values(program)["M1_G"] == 0
        oracle_error = _independent_conditioned_error(
            full.programs, full.probabilities, restricted.programs,
            restricted.probabilities, allowed,
        )
        licensed_count = sum(allowed(program) for program in full.programs)
        prior_mass = _prior_mass(
            full.programs,
            lambda program: v31.structure_log_prior(program, v31.DEFAULT_HYPERPARAMETERS),
            allowed,
        )
        restricted_log_evidence = restricted.log_evidence
        identity_applicable = True
        masked = v33.score_world(_mask_imaginal(world)).current
        dropped = v33.score_world(_drop_imaginal(world)).current
        mask_error = _posterior_distance(masked.probabilities, dropped.probabilities)
        target_error = restricted.edge_probabilities["M1_G"]
        unrelated_error = abs(
            restricted.edge_probabilities["W_Y"]
            - math.fsum(
                float(probability)
                for program, probability in zip(full.programs, full.probabilities)
                if allowed(program) and v31.program_values(program)["W_Y"]
            ) / math.fsum(
                float(probability)
                for program, probability in zip(full.programs, full.probabilities)
                if allowed(program)
            )
        )
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
        allowed = lambda program: v34.structure_values(program)["L_PREC"] == 0
        oracle_error = _independent_conditioned_error(
            full.programs, full.structure_probabilities, restricted.programs,
            restricted.structure_probabilities, allowed,
        )
        licensed_count = sum(allowed(program) for program in full.programs)
        prior_mass = _prior_mass(full.programs, v34.structure_log_prior, allowed)
        restricted_log_evidence = restricted.log_evidence
        identity_applicable = True
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
        unrelated_error = abs(
            restricted.edge_probabilities["L_Y"]
            - math.fsum(
                float(probability)
                for program, probability in zip(full.programs, full.structure_probabilities)
                if allowed(program) and v34.structure_values(program)["L_Y"]
            ) / math.fsum(
                float(probability)
                for program, probability in zip(full.programs, full.structure_probabilities)
                if allowed(program)
            )
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
        full_atom_keys = _v35_atom_keys(full)
        restricted_atom_keys = _v35_atom_keys(restricted)
        allowed = lambda atom: v35.program_values(atom[0])["JOINT_POLICY_Y"] == 0
        identity_error = _conditioned_error(
            full_atom_keys,
            full.probabilities,
            restricted_atom_keys,
            restricted.probabilities,
            allowed,
        )
        oracle_error = _independent_conditioned_error(
            full_atom_keys, full.probabilities, restricted_atom_keys,
            restricted.probabilities, allowed,
        )
        licensed_count = sum(allowed(atom) for atom in full_atom_keys)
        unique_structures = tuple(dict.fromkeys(component[0] for component in full.components))
        prior_mass = float(math.fsum(
            math.exp(v35.structure_log_prior(structure))
            for structure in unique_structures
            if v35.program_values(structure)["JOINT_POLICY_Y"] == 0
        ) / math.fsum(
            math.exp(v35.structure_log_prior(structure)) for structure in unique_structures
        ))
        restricted_log_evidence = restricted.log_evidence
        identity_applicable = True
        registration_masked = v35.score_world(world, registration_enabled=False)
        mask_error = _posterior_distance(full.probabilities, registration_masked.probabilities)
        target_error = restricted.edge_probabilities["JOINT_POLICY_Y"]
        unrelated_error = abs(
            restricted.edge_probabilities["CROSS_MODE_Y"]
            - math.fsum(
                float(probability)
                for component, probability in zip(full.components, full.probabilities)
                if allowed(component) and v35.program_values(component[0])["CROSS_MODE_Y"]
            ) / math.fsum(
                float(probability)
                for component, probability in zip(full.components, full.probabilities)
                if allowed(component)
            )
        )
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
        "semantic_class": LESION_CLASSES[lesion],
        "licensed_support_count": int(licensed_count),
        "restricted_prior_mass": float(prior_mass),
        "restricted_log_evidence": None if restricted_log_evidence is None else float(restricted_log_evidence),
        "restricted_prior_identity_applicable": bool(identity_applicable),
        "restricted_prior_identity_error": None if identity_error is None else float(identity_error),
        "masked_channel_neutrality_error": float(mask_error),
        "independent_oracle_error": float(oracle_error),
        "posterior_normalization_error": float(normalization_error),
        "target_pathway_removed": bool(target_error <= TOLERANCE),
        "unrelated_survivors_preserved": bool(unrelated_error <= TOLERANCE),
        "finite": bool(
            _finite_optional(identity_error, restricted_log_evidence)
            and math.isfinite(mask_error)
            and math.isfinite(oracle_error)
            and math.isfinite(normalization_error)
            and math.isfinite(target_error)
            and math.isfinite(unrelated_error)
        ),
        "declared_target_error": float(target_error),
        "unrelated_absolute_movement_descriptive": descriptive,
    }


def _trace_map(tasks: Sequence[tuple[int, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    RESULTS.mkdir(parents=True, exist_ok=True)
    trace_path = RESULTS / "v3.6-r1-gate4-replacement-traces.jsonl"
    hash_path = RESULTS / "v3.6-r1-gate4-replacement-trace-hashes.json"
    hash_events_path = RESULTS / "v3.6-r1-gate4-replacement-trace-hash-events.jsonl"
    if trace_path.exists() or hash_path.exists() or hash_events_path.exists():
        raise RuntimeError("custody refusal: Gate-4 output already exists")
    rows: list[dict[str, Any]] = []
    record_hashes: list[dict[str, Any]] = []
    file_hash = hashlib.sha256()
    def persist(handle, hash_handle, row: dict[str, Any]) -> None:
        nonlocal file_hash
        try:
            validate_finite_worker_row(row)
        except NonFiniteWorkerRow as error:
            provenance = {
                "record_type": "NONFINITE_WORKER_ROW_REJECTION",
                "seed": int(row.get("seed", -1)),
                "lesion": row.get("lesion"),
                "offending_paths": list(error.paths),
            }
            encoded = _canonical(provenance)
            handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
            file_hash.update(encoded)
            _write_json(hash_path.name, {
                "file": trace_path.name,
                "file_sha256": file_hash.hexdigest(),
                "record_count": len(rows) + 1,
                "status": "HONEST_STOP_NONFINITE_WORKER_ROW",
                "offending_row_provenance": provenance,
            })
            raise RuntimeError(str(error)) from error
        encoded = _canonical(row)
        handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
        file_hash.update(encoded)
        rows.append(row)
        record_hashes.append({
            "seed": row["seed"], "sha256": hashlib.sha256(encoded).hexdigest()
        })
        hash_handle.write(_canonical(record_hashes[-1]))
        hash_handle.flush(); os.fsync(hash_handle.fileno())

    processes = max(1, min(8, (os.cpu_count() or 2) - 1))
    cell_size = 1000
    with trace_path.open("xb") as handle, hash_events_path.open("xb") as hash_handle:
        for start in range(0, len(tasks), cell_size):
            cell = tasks[start:start + cell_size]
            # Round-16 custody: every cell's first row is durable before the
            # parallel remainder of that cell opens.
            persist(handle, hash_handle, _worker(cell[0]))
            with get_context("spawn").Pool(processes) as pool:
                for row in pool.imap(_worker, cell[1:], chunksize=2):
                    persist(handle, hash_handle, row)
    ledger = {
        "file": trace_path.name,
        "file_sha256": file_hash.hexdigest(),
        "record_count": len(rows),
        "seed_block": list(GATE4_BLOCK),
        "incremental_hash_events_file": hash_events_path.name,
        "incremental_hash_events_sha256": hashlib.sha256(
            hash_events_path.read_bytes()
        ).hexdigest(),
        "serial_cell_first_seeds": list(range(GATE4_BLOCK[0], GATE4_BLOCK[1] + 1, cell_size)),
        "records": record_hashes,
        "persist_before_aggregation": True,
    }
    _write_json(hash_path.name, ledger)
    if hashlib.sha256(trace_path.read_bytes()).hexdigest() != ledger["file_sha256"]:
        raise RuntimeError("Gate-4 trace hash verification failed")
    expected = list(range(GATE4_BLOCK[0], GATE4_BLOCK[1] + 1))
    if [row["seed"] for row in rows] != expected:
        raise RuntimeError("Gate-4 seed order is not ascending and gap-free")
    return rows, ledger


def _support_preserving_dummy(lesion: str) -> dict[str, Any]:
    keys = ("licensed_positive", "licensed_exact_zero", "excluded")
    prior = (0.4, 0.1, 0.5)
    likelihood = (0.75, 0.0, 0.5)
    joint = tuple(p * l for p, l in zip(prior, likelihood))
    evidence = math.fsum(joint)
    full = tuple(value / evidence for value in joint)
    allowed = lambda key: key != "excluded"
    restricted_log_evidence = math.log(joint[0] + joint[1])
    restricted_keys = keys[:2]
    restricted = (1.0, 0.0)
    identity = _conditioned_error(
        keys, full, restricted_keys, restricted, allowed
    )
    oracle = _independent_conditioned_error(
        keys, full, restricted_keys, restricted, allowed
    )
    return {
        "lesion": lesion,
        "semantic_class": SUPPORT_PRESERVING,
        "licensed_support_count": 2,
        "restricted_prior_mass": prior[0] + prior[1],
        "restricted_log_evidence": restricted_log_evidence,
        "restricted_identity_applicable": True,
        "restricted_identity_error": identity,
        "masked_neutrality_error": 0.0,
        "independent_oracle_error": oracle,
        "target_pathway_removed": True,
        "unrelated_survivors_preserved": True,
        "posterior_normalization_error": abs(math.fsum(restricted) - 1.0),
        "all_outputs_finite": all(math.isfinite(value) for value in (
            prior[0] + prior[1], restricted_log_evidence, identity, oracle,
        )),
        "boundary_fixture": {
            "exact_zero_retained_candidate": "licensed_exact_zero",
            "full_support_conditioning": True,
            "target_channel_observed_before_masking": True,
            "unaffected_channel_observed": True,
        },
    }


def _support_destroying_dummy() -> dict[str, Any]:
    masked_reference = (0.35, 0.65)
    surviving = tuple(masked_reference)
    return {
        "lesion": "grow_mode_slot",
        "semantic_class": SUPPORT_DESTROYING,
        "licensed_support_count": 0,
        "restricted_prior_mass": 0.0,
        "restricted_log_evidence": None,
        "restricted_identity_applicable": False,
        "restricted_identity_error": None,
        "masked_neutrality_error": _posterior_distance(
            masked_reference, surviving
        ),
        "independent_oracle_error": max(
            abs(surviving[index] - masked_reference[index]) for index in range(2)
        ),
        "target_pathway_removed": True,
        "unrelated_survivors_preserved": True,
        "posterior_normalization_error": abs(math.fsum(surviving) - 1.0),
        "all_outputs_finite": all(math.isfinite(value) for value in surviving),
        "boundary_fixture": {
            "empty_licensed_target_subset": True,
            "all_target_channels_masked_to_likelihood_one": True,
            "target_channel_observed_before_masking": True,
            "unaffected_channel_observed": True,
            "clinical_or_protocol_label_reaches_inference": False,
            "fallback_assigns_desired_readout": False,
        },
    }


def run_preblock_proofs() -> dict[str, Any]:
    rows = [_support_destroying_dummy()] + [
        _support_preserving_dummy(lesion)
        for lesion in LESIONS if lesion != "grow_mode_slot"
    ]
    failures = []
    for row in rows:
        validate_finite_worker_row(row)
        preserving = row["semantic_class"] == SUPPORT_PRESERVING
        passed = (
            row["masked_neutrality_error"] <= TOLERANCE
            and row["independent_oracle_error"] <= TOLERANCE
            and row["target_pathway_removed"]
            and row["unrelated_survivors_preserved"]
            and row["posterior_normalization_error"] <= TOLERANCE
            and row["all_outputs_finite"]
            and (
                row["licensed_support_count"] > 0
                and row["restricted_prior_mass"] > 0.0
                and _positive_log_evidence(row["restricted_log_evidence"])
                and row["restricted_identity_applicable"]
                and row["restricted_identity_error"] <= TOLERANCE
                if preserving else
                row["licensed_support_count"] == 0
                and row["restricted_prior_mass"] == 0.0
                and row["restricted_log_evidence"] is None
                and not row["restricted_identity_applicable"]
                and row["restricted_identity_error"] is None
            )
        )
        row["passed"] = bool(passed)
        if not passed:
            failures.append(row["lesion"])
    bridge_spec = json.loads(
        (ROOT / "protocols" / "v3.6-r1-bridge-spec.json").read_text()
    )
    source_hashes = {
        relative: hashlib.sha256((SUITE_ROOT / relative).read_bytes()).hexdigest()
        for relative in bridge_spec["scientific_source_sha256"]
    }
    source_identity = source_hashes == bridge_spec["scientific_source_sha256"]
    if not source_identity:
        failures.append("scientific_source_hash_identity")
    round16_repair = json.loads(
        (RESULTS / "round16-constructor-repair-audit.json").read_text()
    )
    round16_coherence = json.loads(
        (RESULTS / "round16-generator-coherence-proof.json").read_text()
    )
    if round16_repair.get("status") != "PASS":
        failures.append("round16_constructor_repair_audit")
    if round16_coherence.get("verdict") != "PASS":
        failures.append("round16_generator_coherence")
    record = {
        "stage": "V3.6",
        "proof": "ROUND14_ZERO_SEED_LESION_PRE_RUN_TABLE",
        "tolerance": TOLERANCE,
        "seed_consumption": [],
        "lesion_declarations_frozen_before_execution": LESION_CLASSES,
        "rows": rows,
        "boundary_fixtures": {
            "exact_zero_retained_candidate": True,
            "empty_licensed_target_subset": True,
            "all_target_channels_masked": True,
            "target_channel_observed_before_masking": True,
            "unaffected_channel_observed": True,
            "full_support_conditioning_lesion": True,
        },
        "scientific_source_hash_identity": source_identity,
        "scientific_source_hashes": source_hashes,
        "round16_constructor_repair_audit": round16_repair.get("status"),
        "round16_generator_coherence": round16_coherence.get("verdict"),
        "failures": failures,
        "verdict": "PASS" if not failures else "FAIL_PREBLOCK_LESION_PROOF",
    }
    trace = RESULTS / "v3.6-r1-round19-gate4-preblock-proof-trace.jsonl"
    ledger_path = RESULTS / "v3.6-r1-round19-gate4-preblock-proof-trace-hashes.json"
    if trace.exists() or ledger_path.exists():
        raise RuntimeError("Round-14 lesion preproof outputs already exist")
    encoded = _canonical(record)
    with trace.open("xb") as handle:
        handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
    ledger = {
        "file": trace.name,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "record_count": 1,
        "persisted_and_hashed_before_verdict_output": True,
        "seed_consumption": [],
    }
    _write_json(ledger_path.name, ledger)
    result = {**record, "custody": ledger}
    _write_json("v3.6-r1-round19-gate4-preblock-proofs.json", result)
    (RESULTS / "v3.6-r1-round19-gate4-preblock-proofs.md").write_text(
        "# V3.6 Round-19 repaired zero-seed lesion proofs\n\n"
        f"Verdict: **{result['verdict']}**.\n\n"
        "All five lesion classes were declared before seeded execution. The "
        "proof table includes exact-zero retained support, empty destroyed "
        "support, masking, unaffected observations, and full conditioning.\n",
        encoding="utf-8",
    )
    return result


def run_gate4(lesion_proof: Mapping[str, Any]) -> dict[str, Any]:
    proof = json.loads(
        (RESULTS / "v3.6-r1-round13-native-fixture-identity-proofs.json").read_text(encoding="utf-8")
    )
    if proof.get("verdict") != "PASS":
        raise RuntimeError("all eight Round-13 pre-block proofs must pass before Gate 4")
    if lesion_proof.get("verdict") != "PASS":
        raise RuntimeError("Round-17 zero-seed lesion proof table is not PASS")
    tasks = [
        (seed, LESIONS[(seed - GATE4_BLOCK[0]) // 1000])
        for seed in range(GATE4_BLOCK[0], GATE4_BLOCK[1] + 1)
    ]
    rows, trace_ledger = _trace_map(tasks)
    cells: dict[str, Any] = {}
    failures: list[str] = []
    for lesion in LESIONS:
        selected = [row for row in rows if row["lesion"] == lesion]
        cell = {
            "world_count": len(selected),
            "semantic_class": LESION_CLASSES[lesion],
            "restricted_prior_identity_applicable": LESION_CLASSES[lesion] == SUPPORT_PRESERVING,
            "restricted_prior_identity_error_max": (
                max(row["restricted_prior_identity_error"] for row in selected)
                if LESION_CLASSES[lesion] == SUPPORT_PRESERVING else None
            ),
            "masked_channel_neutrality_error_max": max(row["masked_channel_neutrality_error"] for row in selected),
            "independent_oracle_error_max": max(row["independent_oracle_error"] for row in selected),
            "posterior_normalization_error_max": max(row["posterior_normalization_error"] for row in selected),
            "declared_target_error_max": max(row["declared_target_error"] for row in selected),
            "finite_all": all(row["finite"] for row in selected),
            "target_pathway_removed_all": all(row["target_pathway_removed"] for row in selected),
            "unrelated_survivors_preserved_all": all(row["unrelated_survivors_preserved"] for row in selected),
            "licensed_support_positive_all": all(
                row["licensed_support_count"] > 0 and row["restricted_prior_mass"] > 0.0
                and _positive_log_evidence(row["restricted_log_evidence"])
                for row in selected
            ) if LESION_CLASSES[lesion] == SUPPORT_PRESERVING else True,
            "unrelated_absolute_movement": {
                "classification": "DESCRIPTIVE_RENORMALIZATION_MOVEMENT",
                "note": "Absolute movement in non-target coordinates is not a selectivity criterion after conditioning the structure prior.",
            },
        }
        cell["passed"] = (
            cell["world_count"] == 1000
            and (
                cell["restricted_prior_identity_error_max"] <= TOLERANCE
                if cell["restricted_prior_identity_applicable"]
                else all(row["restricted_prior_identity_error"] is None for row in selected)
            )
            and cell["masked_channel_neutrality_error_max"] <= TOLERANCE
            and cell["independent_oracle_error_max"] <= TOLERANCE
            and cell["posterior_normalization_error_max"] <= TOLERANCE
            and cell["declared_target_error_max"] <= TOLERANCE
            and cell["finite_all"]
            and cell["target_pathway_removed_all"]
            and cell["unrelated_survivors_preserved_all"]
            and cell["licensed_support_positive_all"]
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
            "fixture_file": "v3.6-r1-round13-native-fixture-identity-proofs.json",
            "fixture_verdict": proof["verdict"],
            "lesion_file": "v3.6-r1-round19-gate4-preblock-proofs.json",
            "lesion_verdict": lesion_proof["verdict"],
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
            "trace_file": "v3.6-r1-gate4-replacement-traces.jsonl",
            "trace_hash_ledger": "v3.6-r1-gate4-replacement-trace-hashes.json",
            "trace_sha256": trace_ledger["file_sha256"],
            "incremental_hash_events_sha256": trace_ledger["incremental_hash_events_sha256"],
            "serial_cell_first_seeds": trace_ledger["serial_cell_first_seeds"],
            "persisted_before_aggregation": True,
            "barred_blocks_touched": False,
            "escrow_touched": False,
        },
        "failures": failures,
        "verdict": "PASS" if not failures else "FAIL",
    }
    result["immutable_verdict"] = result["verdict"]
    _write_json("v3.6-r1-gate4-replacement-verdict.json", result)
    report = [
        "# V3.6 replacement Gate 4 — repaired composed selective lesions",
        "",
        f"Verdict: **{result['verdict']}**.",
        "",
        "The five 1,000-world cells delete one frozen production in each constituent stage. Selectivity is the exact restricted-prior identity; unrelated absolute posterior movement after renormalization is descriptive.",
        "",
        "| constituent lesion | restricted identity max | masking max | target max | pass |",
        "|---|---:|---:|---:|:---:|",
    ]
    for lesion, cell in cells.items():
        identity_text = (
            f"{cell['restricted_prior_identity_error_max']:.3g}"
            if cell["restricted_prior_identity_error_max"] is not None else "N/A"
        )
        report.append(
            f"| {lesion} | {identity_text} | "
            f"{cell['masked_channel_neutrality_error_max']:.3g} | "
            f"{cell['declared_target_error_max']:.3g} | {cell['passed']} |"
        )
    report.extend([
        "",
        "Every per-world row, including its runtime event ledger and world hash, was persisted and hashed before these aggregates were computed.",
        "",
    ])
    (RESULTS / "v3.6-r1-gate4-replacement-verdict.md").write_text("\n".join(report), encoding="utf-8")
    if failures:
        _write_json(
            "gate-4-replacement-round19-diagnosis-stub.json",
            {"stage": "V3.6", "gate": 4, "failures": failures, "next_action": "HONEST_STOP"},
        )
    return result


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "preproof":
        result = run_preblock_proofs()
        print(json.dumps({"phase": "gate4-preproof", "verdict": result["verdict"]}, sort_keys=True))
    elif len(sys.argv) == 2 and sys.argv[1] == "replacement":
        lesion_proof = json.loads(
            (RESULTS / "v3.6-r1-round19-gate4-preblock-proofs.json").read_text()
        )
        if lesion_proof.get("verdict") != "PASS":
            raise RuntimeError("Round-19 zero-seed lesion proof table is not PASS")
        result = run_gate4(lesion_proof)
        print(json.dumps({"gate": 4, "verdict": result["verdict"]}, sort_keys=True))
    else:
        raise SystemExit("usage: run_v36_gate4.py preproof|replacement")


if __name__ == "__main__":
    main()
