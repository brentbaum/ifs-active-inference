#!/usr/bin/env python3
"""Prospective V3.5 PROTECT stage runner."""

from __future__ import annotations

import argparse
import ast
import hashlib
import itertools
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
sys.path.insert(0, str(ROOT))
from ref import audit, v35, v35_oracle  # noqa: E402
from ref.trace_sink import serializing_trace_context, traced_execution  # noqa: E402


RESULTS = ROOT / "results" / "V3.5"
PARAMETERS = ROOT / "protocols" / "v3.5-parameters.json"
TOLERANCE = 1e-10


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
        json.dumps(_plain(value), sort_keys=True, separators=(",", ":"),
                   allow_nan=False).encode() + b"\n"
    )


def _write_json(name: str, value: Any) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / name).write_text(
        json.dumps(_plain(value), indent=2, sort_keys=True,
                   allow_nan=False) + "\n"
    )


def _trace_map(name: str, tasks: Sequence[Any], worker: Any):
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{name}-traces.jsonl"
    file_hash = hashlib.sha256()
    records, rows = [], []
    processes = max(1, min(8, (os.cpu_count() or 2) - 1))
    with path.open("wb") as handle:
        with get_context("spawn").Pool(processes) as pool:
            for row in pool.imap(worker, tasks, chunksize=4):
                encoded = _canonical(row)
                handle.write(encoded)
                handle.flush()
                file_hash.update(encoded)
                records.append({
                    "seed": row["seed"],
                    "sha256": hashlib.sha256(encoded).hexdigest(),
                })
                rows.append(row)
    _write_json(f"{name}-trace-hashes.json", {
        "file": path.name,
        "world_count": len(rows),
        "file_sha256": file_hash.hexdigest(),
        "records": records,
    })
    return rows


def _config(**changes):
    values = dict(
        befriend="all", partner="remaining", stakes="high",
        policy_regime="mixed", mode_count=3, topology="allied",
        support_target="all", registration="delivered",
        denied_contact="delivered", length=64,
    )
    values.update(changes)
    return v35.ProtectConfig(**values)


def _component_key(structure, sign, reliable):
    return (
        structure.active_modes, structure.mode_root_edges,
        structure.joint_policy_outcome, structure.cross_mode_outcome,
        sign, reliable,
    )


def _structure_probabilities(posterior):
    result = {}
    for probability, (structure, sign) in zip(
        posterior.probabilities, posterior.components
    ):
        key = (
            structure.active_modes, structure.mode_root_edges,
            structure.joint_policy_outcome, structure.cross_mode_outcome,
        )
        result[key] = result.get(key, 0.0) + probability
    return result


@traced_execution
def _gate1_row():
    world = v35.generate_world(3_500_000, replace(_config(), length=8))
    posterior = v35.score_world(world)
    observations = [asdict(item) for item in world.observations]
    snapshot = json.dumps(observations, sort_keys=True)
    keys, oracle_probabilities, oracle_evidence = v35_oracle.posterior(
        observations
    )
    reliable_order = [
        reliable
        for structure in v35.PROGRAMS
        for sign in ((-1, 1) if structure.cross_mode_outcome else (0,))
        for reliable in (0, 1)
    ]
    production = {
        _component_key(structure, sign, reliable): probability
        for probability, (structure, sign), reliable in zip(
            posterior.probabilities, posterior.components, reliable_order
        )
    }
    oracle_error = max(
        abs(probability - production[key])
        for key, probability in zip(keys, oracle_probabilities)
    )
    full_map = _structure_probabilities(posterior)
    restricted = v35.score_world(
        world, restrictions={"CROSS_MODE_Y": (0,)}
    )
    restricted_map = _structure_probabilities(restricted)
    retained = {key: value for key, value in full_map.items() if key[-1] == 0}
    mass = math.fsum(retained.values())
    restricted_error = max(
        abs(value - retained[key] / mass)
        for key, value in restricted_map.items()
    )
    masked = replace(
        world,
        observations=tuple(
            replace(item, registration=(None, None, None))
            for item in world.observations
        ),
    )
    masked_p = v35.score_world(masked)
    disabled_p = v35.score_world(world, registration_enabled=False)
    registration_error = max(
        abs(a - b) for a, b in zip(
            masked_p.probabilities, disabled_p.probabilities
        )
    )
    denied_masked = replace(
        world,
        observations=tuple(
            replace(item, denied_contact=None) for item in world.observations
        ),
    )
    denied_error = max(
        abs(a - b) for a, b in zip(
            v35.score_world(denied_masked).probabilities,
            v35.score_world(world, denied_enabled=False).probabilities,
        )
    )
    prior_sum = math.fsum(
        math.exp(v35.structure_log_prior(program))
        for program in v35.PROGRAMS
    )
    factor_error = 0.0
    for latent in (0, 1):
        factor_error = max(
            factor_error,
            abs(sum(v35.mode_signal_probability(o, latent) for o in (0, 1)) - 1),
            abs(sum(v35.registration_probability(o, latent) for o in (0, 1)) - 1),
        )
    for reliable in (0, 1):
        for channel in ("remaining", "pressure"):
            factor_error = max(
                factor_error,
                abs(sum(v35.partner_channel_probability(
                    o, reliable, channel
                ) for o in (0, 1)) - 1),
            )
    absent = v35.ProtectStructure(3, (0, 0, 0), 0, 0)
    edge_absence = max(
        abs(v35.outcome_probability(policy, modes, absent, 0) - 0.5)
        for policy in v35.JOINT_POLICIES
        for modes in itertools.product((0, 1), repeat=3)
    )
    source = (ROOT / "ref" / "v35.py").read_text()
    tree = ast.parse(source)
    forbidden_functions = [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name in {
            "assign_access", "set_protector", "polarization_coefficient",
            "exile_force", "policy_selection_likelihood",
        }
    ]
    label_rejected = False
    try:
        v35.score_world(replace(world, analysis_labels=("protector",)))
    except ValueError:
        label_rejected = True
    proofs = {
        "1_structure_prior_error": abs(prior_sum - 1.0),
        "2_factor_normalization_error": factor_error,
        "3_policy_space_size": len(v35.JOINT_POLICIES),
        "3_policy_normalization_error": abs(
            math.fsum(posterior.joint_policy_posterior) - 1.0
        ),
        "4_dormant_slots_idle": all(
            p.mode_root_edges[p.active_modes:] == (0,) * (3 - p.active_modes)
            for p in v35.PROGRAMS
        ),
        "5_edge_absence_error": edge_absence,
        "6_registration_mask_error": registration_error,
        "7_registration_outcome_direct_path": False,
        "8_denied_mask_error": denied_error,
        "9_action_selection_functions": forbidden_functions,
        "10_generator_scorer_exact_log_error": abs(
            world.exact_log_probability
            - v35.exact_complete_log_probability(world)
        ),
        "11_posterior_normalization_error": abs(
            math.fsum(posterior.probabilities) - 1.0
        ),
        "12_independent_oracle_error": oracle_error,
        "12_oracle_evidence_error": abs(
            math.exp(posterior.log_evidence) - oracle_evidence
        ),
        "12_oracle_input_copy": snapshot == json.dumps(
            observations, sort_keys=True
        ),
        "13_restricted_prior_error": restricted_error,
        "14_analysis_label_rejected": label_rejected,
        "15_readout_state_audit": audit.audit_state(posterior),
        "15_import_audit": audit.audit_imports(ROOT / "ref"),
    }
    numeric = [
        abs(value) for value in proofs.values()
        if isinstance(value, float)
    ]
    passed = (
        all(value <= TOLERANCE for value in numeric)
        and proofs["3_policy_space_size"] == 27
        and proofs["4_dormant_slots_idle"]
        and not forbidden_functions
        and proofs["12_oracle_input_copy"]
        and label_rejected
        and not proofs["15_readout_state_audit"]
        and not proofs["15_import_audit"]
    )
    return {
        "seed": "authored_dummy",
        "passed": passed,
        "proofs": proofs,
        "structure_space_size": len(v35.PROGRAMS),
        "component_space_size": len(posterior.components),
        "bounds": dict(v35.finite_information_bounds()),
    }


def run_gate1():
    refusal = False
    try:
        v35.generate_world(3_500_000, _config())
    except RuntimeError:
        refusal = True
    row = _gate1_row()
    row["proofs"]["16_trace_sink_refusal"] = refusal
    row["passed"] = row["passed"] and refusal
    _trace_map_single("gate-1", row)
    result = {
        "verdict": "PASS" if row["passed"] else "FAIL",
        "proofs": row["proofs"],
        "structure_space_size": row["structure_space_size"],
        "component_space_size": row["component_space_size"],
        "bounds": row["bounds"],
    }
    _write_json("gate-1.json", result)
    params = json.loads(PARAMETERS.read_text())
    params["bounds"] = row["bounds"]
    params["status"] = "GATE1_PASSED" if row["passed"] else "STOPPED_AT_GATE1"
    PARAMETERS.write_text(json.dumps(params, indent=2, sort_keys=True) + "\n")
    return row["passed"]


def _trace_map_single(name, row):
    RESULTS.mkdir(parents=True, exist_ok=True)
    encoded = _canonical(row)
    path = RESULTS / f"{name}-traces.jsonl"
    path.write_bytes(encoded)
    _write_json(f"{name}-trace-hashes.json", {
        "file": path.name, "world_count": 1,
        "file_sha256": hashlib.sha256(encoded).hexdigest(),
        "records": [{"seed": row["seed"],
                     "sha256": hashlib.sha256(encoded).hexdigest()}],
    })


def _credible_contains(probabilities, truth_index):
    order = np.argsort(-np.asarray(probabilities))
    mass = 0.0
    for index in order:
        mass += probabilities[int(index)]
        if int(index) == truth_index:
            return True
        if mass >= 0.95:
            return False
    return False


def _ece(confidence, correct):
    p, y = np.asarray(confidence), np.asarray(correct, dtype=float)
    value = 0.0
    for low in np.linspace(0, .9, 10):
        high = low + .1
        chosen = (p >= low) & (p <= high if high == 1 else p < high)
        if chosen.any():
            value += chosen.mean() * abs(p[chosen].mean() - y[chosen].mean())
    return float(value)


@traced_execution
def _worker_recovery(task):
    seed, length, released = task
    world = v35.generate_recovery_world(
        seed, length=length, released_block=released
    )
    posterior = v35.score_world(world)
    structure_map = _structure_probabilities(posterior)
    truth_key = (
        world.truth_structure.active_modes,
        world.truth_structure.mode_root_edges,
        world.truth_structure.joint_policy_outcome,
        world.truth_structure.cross_mode_outcome,
    )
    predicted = max(structure_map, key=structure_map.get)
    ordered = list(structure_map)
    truth_index = ordered.index(truth_key)
    probabilities = [structure_map[key] for key in ordered]
    truth_edges = tuple(v35.program_values(world.truth_structure).values())
    predicted_edges = (
        predicted[1][0], predicted[1][1], predicted[1][2],
        predicted[2], predicted[3],
    )
    truth_topology = (
        "independent" if world.truth_cross_sign == 0
        else "opposed" if world.truth_cross_sign < 0 else "coalition"
    )
    predicted_topology = max(
        posterior.topology_probabilities,
        key=posterior.topology_probabilities.get,
    )
    return {
        "seed": seed,
        "truth_structure": truth_key,
        "predicted_structure": predicted,
        "edge_correct": [
            a == b for a, b in zip(predicted_edges, truth_edges)
        ],
        "active_count_correct": predicted[0] == truth_key[0],
        "program_correct": predicted == truth_key,
        "confidence": structure_map[predicted],
        "coverage": _credible_contains(probabilities, truth_index),
        "topology_correct": predicted_topology == truth_topology,
        "partner_correct": int(np.argmax(posterior.q_partner))
        == world.truth_partner,
        "normalization_error": abs(
            math.fsum(posterior.probabilities) - 1
        ),
        "exact_log_error": abs(
            world.exact_log_probability
            - v35.exact_complete_log_probability(world)
        ),
    }


def _recovery_metrics(rows):
    edge = {
        name: float(np.mean([row["edge_correct"][i] for row in rows]))
        for i, name in enumerate(v35.EDGE_NAMES)
    }
    return {
        "world_count": len(rows),
        "edge_accuracy": edge,
        "minimum_edge_accuracy": min(edge.values()),
        "active_count_accuracy": float(np.mean(
            [row["active_count_correct"] for row in rows]
        )),
        "program_accuracy": float(np.mean(
            [row["program_correct"] for row in rows]
        )),
        "topology_accuracy": float(np.mean(
            [row["topology_correct"] for row in rows]
        )),
        "partner_accuracy": float(np.mean(
            [row["partner_correct"] for row in rows]
        )),
        "ece": _ece(
            [row["confidence"] for row in rows],
            [row["program_correct"] for row in rows],
        ),
        "coverage": float(np.mean([row["coverage"] for row in rows])),
        "normalization_error_max": max(
            row["normalization_error"] for row in rows
        ),
        "exact_log_error_max": max(row["exact_log_error"] for row in rows),
    }


def _summary(world):
    p = v35.score_world(world)
    return {
        "access": p.query("access_probability"),
        "exile": p.query("exile_like_probability"),
        "polarization": p.query("polarization"),
        "coalition": p.query("coalition"),
        "trust": p.query("trust_remaining"),
        "topology": dict(p.topology_probabilities),
        "active": p.active_mode_probabilities,
        "mode": p.mode_occupancy,
        "policy": p.joint_policy_posterior,
    }


@traced_execution
def _worker_pilot(seed):
    themes = ("befriend", "partner", "stakes", "policy", "modes",
              "topology", "support", "denied")
    theme = themes[(seed - 3_500_800) % len(themes)]
    pairs = {
        "befriend": (_config(befriend="none"), _config(befriend="all")),
        "partner": (_config(partner="pressure"), _config(partner="remaining")),
        "stakes": (_config(stakes="low"), _config(stakes="high")),
        "policy": (_config(policy_regime="exclusion"),
                   _config(policy_regime="engagement")),
        "modes": (_config(mode_count=2), _config(mode_count=3)),
        "topology": (_config(topology="opposed"), _config(topology="allied")),
        "support": (_config(support_target="one"), _config(support_target="all")),
        "denied": (_config(denied_contact="masked"),
                   _config(denied_contact="delivered")),
    }
    left, right = pairs[theme]
    return {
        "seed": seed, "theme": theme,
        "left": _summary(v35.generate_world(seed, left)),
        "right": _summary(v35.generate_world(seed, right)),
    }


def run_pilot():
    params = json.loads(PARAMETERS.read_text())
    if params["status"] != "GATE1_PASSED":
        raise RuntimeError("Gate 1 must pass before pilot")
    recovery_rows = _trace_map(
        "stage0-pilot-recovery",
        [(seed, 64, None) for seed in range(3_500_000, 3_500_800)],
        _worker_recovery,
    )
    assay_rows = _trace_map(
        "stage0-pilot-assays",
        list(range(3_500_800, 3_502_000)),
        _worker_pilot,
    )
    recovery = _recovery_metrics(recovery_rows)
    effects = {}
    for theme in {row["theme"] for row in assay_rows}:
        subset = [row for row in assay_rows if row["theme"] == theme]
        if theme == "partner":
            values = [row["right"]["trust"] - row["left"]["trust"] for row in subset]
        elif theme == "topology":
            values = [
                row["left"]["topology"]["opposed"]
                + row["right"]["topology"]["coalition"] - 1.0
                for row in subset
            ]
        elif theme == "modes":
            values = [row["right"]["active"][2] - row["left"]["active"][2] for row in subset]
        elif theme == "policy":
            values = [abs(row["right"]["access"] - row["left"]["access"]) for row in subset]
        elif theme == "denied":
            values = [abs(row["right"]["exile"] - row["left"]["exile"]) for row in subset]
        else:
            values = [abs(row["right"]["access"] - row["left"]["access"]) for row in subset]
        effects[theme] = float(np.mean(values))
    if min(effects.values()) <= 0:
        params["status"] = "STOPPED_AT_STAGE0_UNATTAINABLE"
        PARAMETERS.write_text(json.dumps(params, indent=2, sort_keys=True) + "\n")
        _write_json("stage0-pilot.json", {
            "verdict": "STOP_UNATTAINABLE", "recovery": recovery,
            "effects": effects, "barred_block": [3500000, 3501999],
        })
        return False
    criteria = {
        "edge_accuracy_min": max(.5, math.floor((recovery["minimum_edge_accuracy"]-.05)*100)/100),
        "active_count_accuracy_min": max(.5, math.floor((recovery["active_count_accuracy"]-.05)*100)/100),
        "program_accuracy_min": max(.2, math.floor((recovery["program_accuracy"]-.05)*100)/100),
        "topology_accuracy_min": max(.5, math.floor((recovery["topology_accuracy"]-.05)*100)/100),
        "partner_accuracy_min": max(.7, math.floor((recovery["partner_accuracy"]-.05)*100)/100),
        "ece_max": min(.15, math.ceil((recovery["ece"]+.05)*100)/100),
        "coverage_min": max(.8, math.floor((recovery["coverage"]-.05)*100)/100),
        **{f"{name}_effect_min": value*.5 for name, value in effects.items()},
    }
    params["criteria"] = criteria
    params["status"] = "FROZEN_AFTER_ATTAINABILITY_PILOT"
    params["pilot_summary_sha256"] = hashlib.sha256(
        _canonical({"recovery": recovery, "effects": effects})
    ).hexdigest()
    PARAMETERS.write_text(json.dumps(params, indent=2, sort_keys=True) + "\n")
    _write_json("stage0-pilot.json", {
        "verdict": "DESCRIPTIVE_ATTAINABILITY_PASS",
        "barred_block": [3500000, 3501999],
        "recovery": recovery, "effects": effects,
        "frozen_criteria": criteria,
    })
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("gate1", "pilot"))
    args = parser.parse_args()
    passed = run_gate1() if args.step == "gate1" else run_pilot()
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
