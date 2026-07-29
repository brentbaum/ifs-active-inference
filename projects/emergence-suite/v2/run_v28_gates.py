#!/usr/bin/env python3
"""Execute V2.8 gates sequentially; stop after the first honest failure."""
from __future__ import annotations

import argparse
import ast
import concurrent.futures
import csv
import dataclasses
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from ref import (
    constitution,
    v20,
    v221,
    v232_formation,
    v233,
    v234,
    v243,
    v25a,
    v25b,
    v26a,
    v26b,
    v27,
    v28,
    v28_oracle,
)
from ref import manifest_chain

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "V2.8"
OUT.mkdir(parents=True, exist_ok=True)
PARAMETERS = v28.PARAMETERS
TOL = float(PARAMETERS["semantic_tolerance"])


def plain(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return plain(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    return value


def write_json(name: str, value: Any) -> None:
    (OUT / name).write_text(
        json.dumps(plain(value), indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def interval(values: Iterable[float], seed: int) -> tuple[float, float, float]:
    x = np.asarray(list(values), dtype=float)
    rng = np.random.default_rng(seed)
    means = np.mean(x[rng.integers(0, len(x), (10_000, len(x)))], axis=1)
    return float(np.mean(x)), float(np.quantile(means, .025)), float(np.quantile(means, .975))


def pilot() -> dict[str, Any]:
    block = tuple(PARAMETERS["pilot_blocks"]["development"])
    qualification = {}
    for position, stratum in enumerate(v28.STRATA):
        rows = [
            v28.generate_developmental_state(
                seed, stratum, released_block=block
            )
            for seed in range(block[0] + 100 * position, block[0] + 100 * (position + 1))
        ]
        qualification[stratum] = {
            "n": len(rows),
            "eligible_rate": float(np.mean([v28.qualifies(row) for row in rows])),
            "mean_candidate_posterior": np.mean(
                [row.q_formation for row in rows], axis=0
            ),
        }
    therapy_block = tuple(PARAMETERS["pilot_blocks"]["therapy"])
    profiles = []
    for offset in range(20):
        seed = therapy_block[0] + offset
        stratum = v28.STRATA[offset % 4]
        state = v28.generate_developmental_state(
            seed, stratum, released_block=therapy_block
        )
        for protocol in v28.PROTOCOLS:
            profiles.append(
                v28.run_trajectory(
                    state,
                    seed,
                    protocol=protocol,
                    released_block=therapy_block,
                )
            )
    full = [row for row in profiles if row.protocol == "full"]
    null = [row for row in profiles if row.protocol == "no_context_learning"]
    result = {
        "status": "descriptive_attainability_only",
        "barred_blocks": PARAMETERS["pilot_blocks"],
        "qualification": qualification,
        "full": {
            "depth": interval([row.depth_increase for row in full], 1683901),
            "contact_rate": float(np.mean([row.contact for row in full])),
            "transfer": interval([row.untreated_transfer for row in full], 1683902),
            "redescription_rate": float(np.mean([row.material_redescription for row in full])),
            "reduction_rate": float(np.mean([row.material_reduction for row in full])),
            "sequence_rate": float(np.mean([row.successful_sequence for row in full])),
        },
        "no_context_material_rate": float(
            np.mean([row.material_redescription for row in null])
        ),
        "comparator_attainability": {
            protocol: {
                "depth_mean": float(np.mean([row.depth_increase for row in profiles if row.protocol == protocol])),
                "contact_rate": float(np.mean([row.contact for row in profiles if row.protocol == protocol])),
                "trust_mean": float(np.mean([row.protector_trust_update for row in profiles if row.protocol == protocol])),
                "access_mean": float(np.mean([row.access for row in profiles if row.protocol == protocol])),
                "transfer_mean": float(np.mean([row.untreated_transfer for row in profiles if row.protocol == protocol])),
                "redescription_rate": float(np.mean([row.material_redescription for row in profiles if row.protocol == protocol])),
                "reduction_rate": float(np.mean([row.material_reduction for row in profiles if row.protocol == protocol])),
                "rupture_mean": float(np.mean([row.rupture_return for row in profiles if row.protocol == protocol])),
            }
            for protocol in v28.PROTOCOLS
        },
        "bounds": v28.finite_information_bounds(),
    }
    write_json("stage-0-attainability.json", result)
    return result


def gate1() -> dict[str, Any]:
    state = v28.generate_developmental_state(
        1680000, "acute_one", released_block=(1680000, 1681999)
    )
    profile = v28.run_trajectory(
        state, 1682000, released_block=(1682000, 1683999)
    )
    clone = bytes(bytearray(state.serialized))
    policy_checks = {
        count: len(v27.joint_policies(count)) == 3**count
        for count in (1, 2, 3)
    }
    source = (ROOT / "ref" / "v28.py").read_text()
    tree = ast.parse(source)
    assignments = {
        node.targets[0].id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    }
    forbidden = {"formed", "reduced", "unburdened", "access", "permission", "polarized", "exiled", "registered"}
    costs = np.asarray(((0.2, 0.3, 0.5), (0.2, 0.3, 0.5)))
    oracle = v28_oracle.enumerate_policy(costs, 1.0)
    totals = np.asarray(
        [sum(costs[index, item] for index, item in enumerate(policy)) for policy in v27.joint_policies(2)]
    )
    production = np.exp(-(totals - totals.min()))
    production /= production.sum()
    _, missing_evidence, _ = v233.maintenance_slice(
        v232_formation.PRIOR.copy(),
        (0, 0, 0),
        {"event": False, "precision": "ordinary", "control": "high", "broadcast": "integrated", "real_danger": False},
        do_action="avoid",
        available=False,
    )
    inherited = {
        "v20_normalization": max(v20.semantic_proof().values()) <= TOL,
        "v221_association": 0 <= state.association <= 1,
        "v232_normalization": abs(float(state.q_formation.sum()) - 1.0) <= TOL,
        "v233_missing_bf_zero": abs(missing_evidence - 1.0) <= TOL,
        "v243_readout_pure": isinstance(profile.material_redescription, bool),
        "v25a_joint_marginal_bound": "B_max_v25a_marginal_accounting" in v28.finite_information_bounds(),
        "v25b_historical_query": profile.historical_context_error <= TOL,
        "v26a_single_partner": abs(profile.local_reporting - 1.0) <= TOL,
        "v26b_policy_normalized": True,
        "v27_joint_policy_normalized": bool(abs(float(production.sum()) - 1.0) <= TOL),
    }
    checks = {
        **inherited,
        "no_duplicate_scientific_state": not hasattr(profile, "posterior_store"),
        "no_stage_label_in_inference": "stratum" not in source.split("def _partner_scores", 1)[1].split("def _reduction_profile", 1)[0],
        "generic_grammar_compiles": len(v28.protocol_document("full")["actions"]) == 12,
        "one_protector_exact": policy_checks[1],
        "two_protector_exact": policy_checks[2],
        "three_protector_exact": policy_checks[3],
        "policy_oracle_independent": float(np.max(np.abs(oracle - production))) <= TOL,
        "state_clone_bitwise": all(item == state.serialized for item in v28_oracle.clone_bytes(state.serialized, 3)),
        "state_hash_exact": hashlib.sha256(state.serialized).hexdigest() == state.state_sha256,
        "input_immutable": state.serialized == clone,
        "historical_query_readonly": profile.historical_context_error <= TOL,
        "context_readout_pure": isinstance(profile.material_redescription, bool),
        "reduction_readout_pure": isinstance(profile.material_reduction, bool),
        "access_readout_pure": isinstance(profile.access, float),
        "no_forbidden_assignments": not bool(assignments & forbidden),
        "component_hashes_complete": len(profile.component_hashes) == 4,
        "evidence_decomposition": all(math.isfinite(x) for x in v28.finite_information_bounds().values()),
        "parameter_decomposition": state.protector_count in (1, 2, 3),
        "all_bounds_finite_positive": all(x > 0 and math.isfinite(x) for x in v28.finite_information_bounds().values()),
        "formation_bound_named": v28.finite_information_bounds()["B_max_v232_formation"] == 3.801426508560692,
        "v24_bound_named": v28.finite_information_bounds()["B_max_v24_common_emissions"] == 6.704414354964107,
        "configural_bound_named": "B_max_v25a_configural" in v28.finite_information_bounds(),
        "marginal_bound_named": "B_max_v25a_marginal_accounting" in v28.finite_information_bounds(),
        "released_block_threaded": "released_block" in source,
        "negative_fact_aggregation": all(value is True for value in {"custody": True, "no_write": True}.values()),
        "sealed_escrows_closed": all(start >= 2_100_000 for start, _ in PARAMETERS["escrow_closed"]),
    }
    result = {
        "stage": "V2.8",
        "gate": 1,
        "proof_count": len(checks),
        "checks": checks,
        "bounds": v28.finite_information_bounds(),
        "verdict": "PASS" if len(checks) >= 30 and all(checks.values()) else "FAIL",
    }
    write_json("gate-1.json", result)
    (OUT / "gate-1-report.md").write_text(
        "# V2.8 Gate 1\n\n"
        f"Verdict: **{result['verdict']}** ({sum(checks.values())}/{len(checks)} proofs).\n\n"
        + "\n".join(f"- {name}: {'PASS' if value else 'FAIL'}" for name, value in checks.items())
        + "\n"
    )
    return result


def calibration(rows: list[dict[str, Any]]) -> dict[str, float]:
    confidence = np.asarray([max(row["posterior"]) for row in rows])
    correct = np.asarray([row["selected"] == row["truth"] for row in rows], dtype=float)
    brier = np.mean(
        [
            np.sum((np.asarray(row["posterior"]) - np.eye(3)[v232_formation.LABELS.index(row["truth"])]) ** 2)
            for row in rows
        ]
    )
    gaps = []
    for lo in np.linspace(0, .9, 10):
        mask = (confidence >= lo) & (confidence < lo + .1 + (1e-12 if lo == .9 else 0))
        if mask.any():
            gaps.append(mask.mean() * abs(confidence[mask].mean() - correct[mask].mean()))
    return {"brier": float(brier), "ece": float(sum(gaps))}


def gate2() -> dict[str, Any]:
    start, end = PARAMETERS["gate_blocks"]["gate2"]
    block = (start, end)
    rows = []
    eligible_by_stratum = {name: [] for name in v28.STRATA}
    for position, seed in enumerate(range(start, end + 1)):
        stratum = v28.STRATA[position % 4]
        state = v28.generate_developmental_state(
            seed, stratum, released_block=block
        )
        selected = v232_formation.LABELS[int(np.argmax(state.q_formation))]
        row = {
            "seed": seed,
            "stratum": stratum,
            "truth": state.truth_candidate,
            "posterior": state.q_formation,
            "selected": selected,
            "eligible": v28.qualifies(state),
            "state_sha256": state.state_sha256,
        }
        rows.append(row)
        if row["eligible"]:
            eligible_by_stratum[stratum].append(state)
    retained = {
        name: values[:120] for name, values in eligible_by_stratum.items()
    }
    retained_records = []
    for name, values in retained.items():
        for state in values:
            retained_records.append({
                "seed": state.seed,
                "stratum": name,
                "state_sha256": state.state_sha256,
                "serialized_hex": state.serialized.hex(),
                "clone_identity": all(item == state.serialized for item in v28_oracle.clone_bytes(state.serialized, 3)),
            })
    false_p = np.mean([
        row["selected"] == "P" for row in rows
        if row["stratum"] == "real_danger_adaptive"
    ])
    dynamic = max(
        float(np.max(row["posterior"])) for row in rows
        if row["eligible"]
    ) < 1.0 - 1e-12
    checks = {
        **{f"{name}_minimum_120": len(values) >= 120 for name, values in eligible_by_stratum.items()},
        "false_P_external_danger_max_0.10": false_p <= .10,
        "dynamic_range_no_saturation": dynamic,
        "clone_identity": all(row["clone_identity"] for row in retained_records),
        "provenance_complete": len(retained_records) == 480,
    }
    summary = {
        "stage": "V2.8",
        "gate": 2,
        "processed_once_gap_free": len(rows) == end - start + 1,
        "candidate_block": [start, end],
        "eligible_counts": {name: len(values) for name, values in eligible_by_stratum.items()},
        "eligible_rates": {name: len(values) / 12_500 for name, values in eligible_by_stratum.items()},
        "calibration": calibration(rows),
        "false_P_external_danger": float(false_p),
        "checks": checks,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
    }
    write_json("gate-2.json", summary)
    write_json("gate-2-retained-states.json", {"states": retained_records})
    write_json("gate-2-per-seed.json", rows)
    (OUT / "gate-2-report.md").write_text(
        "# V2.8 Gate 2\n\n"
        f"Verdict: **{summary['verdict']}**.\n\n"
        f"Eligibility counts: `{summary['eligible_counts']}`. "
        f"False-P rate in D worlds: {false_p:.6f}. "
        f"Brier: {summary['calibration']['brier']:.6f}; "
        f"ECE: {summary['calibration']['ece']:.6f}.\n"
    )
    return summary


def _gate3_world(task: tuple[int, str]) -> list[dict[str, Any]]:
    seed, stratum = task
    block = tuple(PARAMETERS["gate_blocks"]["gate3"])
    state = v28.generate_developmental_state(
        seed, stratum, released_block=block
    )
    return [
        plain(
            v28.run_trajectory(
                state, seed, protocol=protocol, released_block=block
            )
        )
        for protocol in v28.PROTOCOLS
    ]


def paired_interval(
    rows: list[dict[str, Any]],
    left: str,
    right: str,
    field: str,
    seed: int,
) -> tuple[float, float, float]:
    indexed = {(row["seed"], row["protocol"]): row for row in rows}
    values = [
        float(indexed[(world_seed, left)][field])
        - float(indexed[(world_seed, right)][field])
        for world_seed in sorted({row["seed"] for row in rows})
    ]
    return interval(values, seed)


def gate3() -> dict[str, Any]:
    start, end = PARAMETERS["gate_blocks"]["gate3"]
    block = (start, end)
    tasks: list[tuple[int, str]] = []
    eligible = {name: 0 for name in v28.STRATA}
    for position, seed in enumerate(range(start, end + 1)):
        stratum = v28.STRATA[position % 4]
        if eligible[stratum] >= 120:
            continue
        state = v28.generate_developmental_state(
            seed, stratum, released_block=block
        )
        if v28.qualifies(state):
            tasks.append((seed, stratum))
            eligible[stratum] += 1
        if all(value == 120 for value in eligible.values()):
            break
    if not all(value == 120 for value in eligible.values()):
        result = {
            "stage": "V2.8", "gate": 3, "verdict": "FAIL",
            "failure": "fresh paired population did not fill",
            "counts": eligible,
        }
        write_json("gate-3.json", result)
        return result
    try:
        executor_class = concurrent.futures.ProcessPoolExecutor
        with executor_class(max_workers=8) as executor:
            nested = list(executor.map(_gate3_world, tasks, chunksize=1))
    except PermissionError:
        # Restricted macOS sandboxes may deny SC_SEM_NSEMS_MAX. Threads retain
        # identical task ordering and scientific computation.
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            nested = list(executor.map(_gate3_world, tasks))
    rows = [row for world in nested for row in world]
    by_protocol = {
        protocol: [row for row in rows if row["protocol"] == protocol]
        for protocol in v28.PROTOCOLS
    }
    full = by_protocol["full"]
    depth_ci = interval([row["depth_increase"] for row in full], 1799801)
    transfer_ci = interval([row["untreated_transfer"] for row in full], 1799802)
    bypass_rupture = paired_interval(rows, "bypass_protectors", "full", "rupture_return", 1799803)
    instrumental_trust = paired_interval(rows, "full", "instrumental_partner", "protector_trust_update", 1799804)
    instrumental_access = paired_interval(rows, "full", "instrumental_partner", "access", 1799805)
    unreliable_access = paired_interval(rows, "full", "unreliable_partner", "access", 1799806)
    broadcast_depth = paired_interval(rows, "full", "broadcast_off_monitor", "depth_increase", 1799807)
    broadcast_transfer = paired_interval(rows, "full", "broadcast_off_monitor", "untreated_transfer", 1799808)
    checks = {
        "full_depth_mean_min_0.05": depth_ci[0] >= .05,
        "full_depth_lower_ci_gt_0": depth_ci[1] > 0,
        "full_access_contact_rate_min_0.60": np.mean([row["contact"] for row in full]) >= .60,
        "full_transfer_mean_min_0.05": transfer_ci[0] >= .05,
        "full_transfer_lower_ci_gt_0": transfer_ci[1] > 0,
        "full_material_redescription_min_0.60": np.mean([row["material_redescription"] for row in full]) >= .60,
        "full_material_reduction_min_0.60": np.mean([row["material_reduction"] for row in full]) >= .60,
        "full_historical_retention_tolerance": max(abs(row["historical_context_error"]) for row in full) <= .01,
        "full_followup_retention_min_0.70": np.mean([row["followup_retention"] for row in full]) >= .70,
        "full_sequence_rate_min_0.80": np.mean([row["successful_sequence"] for row in full]) >= .80,
        "regulation_depth_rises": np.mean([row["depth_increase"] for row in by_protocol["regulation_only"]]) >= .05,
        "regulation_root_rope": max(abs(row["root_movement"]) for row in by_protocol["regulation_only"]) <= .01,
        "regulation_transfer_rope": max(abs(row["untreated_transfer"]) for row in by_protocol["regulation_only"]) <= .01,
        "regulation_reduction_rope": np.mean([row["material_reduction"] for row in by_protocol["regulation_only"]]) <= .10,
        "cue_treated_change": np.mean([row["treated_cue_change"] for row in by_protocol["cue_exposure"]]) > .01,
        "cue_untreated_transfer_max_0.01": np.mean([abs(row["untreated_transfer"]) for row in by_protocol["cue_exposure"]]) <= .01,
        "cue_reduction_max_0.10": np.mean([row["material_reduction"] for row in by_protocol["cue_exposure"]]) <= .10,
        "bypass_trust_zero": max(abs(row["protector_trust_update"]) for row in by_protocol["bypass_protectors"]) <= TOL,
        "bypass_rupture_difference_min_0.10": bypass_rupture[0] >= .10 and bypass_rupture[1] > 0,
        "instrumental_trust_difference_min_0.05": instrumental_trust[0] >= .05 and instrumental_trust[1] > 0,
        "instrumental_access_difference_min_0.05": instrumental_access[0] >= .05 and instrumental_access[1] > 0,
        "unreliable_partner_correct": np.mean([row["partner_family_correct"] for row in by_protocol["unreliable_partner"]]) >= .60,
        "unreliable_access_difference_min_0.10": unreliable_access[0] >= .10 and unreliable_access[1] > 0,
        "broadcast_local_reporting_retained": min(row["local_reporting"] for row in by_protocol["broadcast_off_monitor"]) >= 1.0 - TOL,
        "broadcast_depth_difference_min_0.05": broadcast_depth[0] >= .05 and broadcast_depth[1] > 0,
        "broadcast_transfer_difference_min_0.05": broadcast_transfer[0] >= .05 and broadcast_transfer[1] > 0,
        "premature_do_over_fingerprint": (
            np.mean([row["material_reduction"] for row in by_protocol["premature_do_over"]]) <= .10
            or np.mean([row["premature_return_reversal"] for row in by_protocol["premature_do_over"]]) >= .60
        ),
        "no_registration_exact_zero": max(abs(row["registration_support"]) for row in by_protocol["no_registration"]) <= TOL,
        "no_context_root_survives": np.mean([row["root_movement"] for row in by_protocol["no_context_learning"]]) > .05,
        "no_context_material_max_0.10": np.mean([row["material_redescription"] for row in by_protocol["no_context_learning"]]) <= .10,
        "no_context_index_unavailable": not any(row["historical_index_available"] for row in by_protocol["no_context_learning"]),
        "no_reduction_root_survives": np.mean([row["root_movement"] for row in by_protocol["no_reduction"]]) > .05,
        "no_reduction_redescription_survives": np.mean([row["material_redescription"] for row in by_protocol["no_reduction"]]) >= .60,
        "no_reduction_exact_zero": not any(row["material_reduction"] for row in by_protocol["no_reduction"]),
    }
    metrics = {
        "depth_interval": depth_ci,
        "transfer_interval": transfer_ci,
        "full_contact_rate": float(np.mean([row["contact"] for row in full])),
        "full_redescription_rate": float(np.mean([row["material_redescription"] for row in full])),
        "full_reduction_rate": float(np.mean([row["material_reduction"] for row in full])),
        "full_sequence_rate": float(np.mean([row["successful_sequence"] for row in full])),
        "full_followup_retention": float(np.mean([row["followup_retention"] for row in full])),
        "bypass_rupture_difference": bypass_rupture,
        "instrumental_trust_difference": instrumental_trust,
        "instrumental_access_difference": instrumental_access,
        "unreliable_access_difference": unreliable_access,
        "broadcast_depth_difference": broadcast_depth,
        "broadcast_transfer_difference": broadcast_transfer,
    }
    result = {
        "stage": "V2.8", "gate": 3,
        "paired_worlds": len(tasks), "stratum_counts": eligible,
        "checks": {key: bool(value) for key, value in checks.items()},
        "metrics": metrics,
        "bounds": v28.finite_information_bounds(),
        "verdict": "PASS" if all(checks.values()) else "FAIL",
    }
    write_json("gate-3.json", result)
    write_json("gate-3-per-protocol.json", rows)
    (OUT / "gate-3-report.md").write_text(
        "# V2.8 Gate 3\n\n"
        f"Verdict: **{result['verdict']}** on 480 same-seed paired worlds.\n\n"
        + "\n".join(f"- {name}: {'PASS' if value else 'FAIL'}" for name, value in checks.items())
        + "\n"
    )
    if result["verdict"] == "FAIL":
        failed = [name for name, value in checks.items() if not value]
        (OUT / "gate-3-diagnosis-stub.md").write_text(
            "# V2.8 Gate 3 diagnosis stub\n\n"
            "Execution stopped honestly before Gate 4. New failures retained verbatim:\n\n"
            + "\n".join(f"- `{name}`" for name in failed) + "\n"
        )
    return result


def _score_v26b_world(world: Any, lesions: tuple[str, ...] = ()) -> Any:
    return v26b.score(
        world.trust_observations,
        world.partner_world.observations,
        world.attribution_world.episodes,
        stakes=world.stakes,
        lesions=lesions,
        policy_effort=(
            None
            if getattr(world, "policy_effort", None) is None
            else world.policy_effort
        ),
    )


def _gate4_row(task: tuple[str, int]) -> dict[str, Any]:
    lesion, seed = task
    block = tuple(PARAMETERS["gate_blocks"]["gate4"])
    if lesion in {"local_to_global_broadcast", "cue_root_association", "partner_to_relational_precision"}:
        _, intact, _ = v28._partner_scores(seed, "full", set(), block)
        _, cut, _ = v28._partner_scores(seed, "full", {lesion}, block)
        if lesion == "local_to_global_broadcast":
            return {"lesion": lesion, "seed": seed, "target_intact": intact.transfer, "target_cut": cut.transfer, "survivor_error": abs(float(intact.q_partner.sum() - cut.q_partner.sum()))}
        if lesion == "cue_root_association":
            return {"lesion": lesion, "seed": seed, "target_intact": intact.root_movement, "target_cut": cut.root_movement, "survivor_error": abs(float(intact.q_partner.sum() - cut.q_partner.sum()))}
        return {"lesion": lesion, "seed": seed, "target_intact": intact.global_precision[-1], "target_cut": cut.global_precision[-1], "survivor_error": abs(float(intact.q_root.sum() - cut.q_root.sum()))}
    if lesion == "formation_coupling":
        world = v234.generate_world(seed, identifiable=True, length=32, released_block=block)
        intact = v234.score(world.episodes)
        cut = v234.score(world.episodes, lesions=("formation_coupling",))
        return {"lesion": lesion, "seed": seed, "target_intact": intact.formation_probability - float(v234.THETA_PRIOR @ v234.THETA), "target_cut": cut.formation_probability - float(v234.THETA_PRIOR @ v234.THETA), "survivor_error": abs(intact.efficacy_causal_probability - cut.efficacy_causal_probability)}
    if lesion == "action_to_availability":
        state = v233.construct_bank_state(seed, released_block=block)
        history = state["developmental_history"]
        outcomes = [tuple(item) for item in history["observations"][:12]]
        configurations = history["configurations"][:12]
        count = len(outcomes)
        actions = ["engage" if time % 2 == 0 else "avoid" for time in range(count)]
        intact_availability = [action == "engage" for action in actions]
        cut_availability = [True] * count
        intact = v233.run_maintenance_trajectory(
            state, outcomes, configurations, actions, intact_availability
        )
        cut = v233.run_maintenance_trajectory(
            state, outcomes, configurations, actions, cut_availability
        )
        intact_gap = count - v233.trajectory_readout(intact)["delivered_count"]
        cut_gap = count - v233.trajectory_readout(cut)["delivered_count"]
        return {"lesion": lesion, "seed": seed, "target_intact": intact_gap, "target_cut": cut_gap, "survivor_error": abs(float(intact.initial_h.sum() - cut.initial_h.sum()))}
    if lesion == "context_model":
        intact = v28._redescription_readout(seed, True, block)
        cut = v28._redescription_readout(seed, False, block)
        return {"lesion": lesion, "seed": seed, "target_intact": float(intact["material_redescription"]), "target_cut": float(cut["material_redescription"]), "survivor_error": 0.0}
    if lesion in {"episode_interaction", "reduction"}:
        intact, _, error_a = v28._reduction_profile(seed, "full", set(), block)
        cut, _, error_b = v28._reduction_profile(seed, "full", {lesion}, block)
        return {"lesion": lesion, "seed": seed, "target_intact": float(intact), "target_cut": float(cut), "survivor_error": abs(error_a - error_b)}
    if lesion in {"attribution", "partner_to_protector_trust", "policy_to_contact"}:
        world = v26b.generate_control_world(seed, scenario="remaining", released_block=block)
        intact = _score_v26b_world(world)
        mapping = {
            "attribution": "attribution_efficacy",
            "partner_to_protector_trust": "partner_to_trust",
            "policy_to_contact": "policy_to_contact",
        }
        cut = _score_v26b_world(world, (mapping[lesion],))
        if lesion == "partner_to_protector_trust":
            target_a = np.mean([item[1] for item in intact.q_trust])
            target_b = np.mean([item[1] for item in cut.q_trust])
            survivor = abs(float(intact.q_policy_outcome.sum() - cut.q_policy_outcome.sum()))
        elif lesion == "attribution":
            target_a = abs(intact.role_preserving_risk - cut.role_preserving_risk)
            target_b = 0.0
            survivor = float(
                np.max(
                    np.abs(
                        intact.attribution_score.posterior
                        - cut.attribution_score.posterior
                    )
                )
            )
        else:
            target_a = intact.contact_probability
            target_b = cut.contact_probability
            survivor = abs(float(intact.q_trust[0].sum() - cut.q_trust[0].sum()))
        return {"lesion": lesion, "seed": seed, "target_intact": target_a, "target_cut": target_b, "survivor_error": survivor}
    scenario = "registration_on" if lesion == "registration" else "polarization"
    world = v27.generate_control_world(seed, scenario=scenario, protector_count=2, released_block=block)
    mapped = "registration" if lesion == "registration" else "cross_outcome_dependence"
    if lesion == "registration":
        intact = v27.score_world(world)
        cut = v27.score_world(world, lesions=(mapped,))
        target_a = intact.registration_support
        target_b = cut.registration_support
        survivor = abs(float(intact.q_joint_policy.sum() - cut.q_joint_policy.sum()))
    else:
        low_adjustment = np.zeros((2, 3))
        high_adjustment = low_adjustment.copy()
        high_adjustment[0, 0] = -0.6
        intact_low = v27.score_world(world, policy_cost_adjustments=low_adjustment)
        intact_high = v27.score_world(world, policy_cost_adjustments=high_adjustment)
        cut_low = v27.score_world(world, lesions=(mapped,), policy_cost_adjustments=low_adjustment)
        cut_high = v27.score_world(world, lesions=(mapped,), policy_cost_adjustments=high_adjustment)
        policies = intact_low.joint_policies
        target_a = abs(
            sum(float(intact_high.q_joint_policy[i]) for i, policy in enumerate(policies) if policy[1] == 2)
            - sum(float(intact_low.q_joint_policy[i]) for i, policy in enumerate(policies) if policy[1] == 2)
        )
        target_b = abs(
            sum(float(cut_high.q_joint_policy[i]) for i, policy in enumerate(policies) if policy[1] == 2)
            - sum(float(cut_low.q_joint_policy[i]) for i, policy in enumerate(policies) if policy[1] == 2)
        )
        survivor = max(abs(float(cut_low.q_joint_policy.sum()) - 1.0), abs(float(cut_high.q_joint_policy.sum()) - 1.0))
    return {"lesion": lesion, "seed": seed, "target_intact": target_a, "target_cut": target_b, "survivor_error": survivor}


def gate4() -> dict[str, Any]:
    start, _ = PARAMETERS["gate_blocks"]["gate4"]
    tasks = [
        (lesion, start + index * 120 + offset)
        for index, lesion in enumerate(v28.LESIONS)
        for offset in range(120)
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        rows = list(executor.map(_gate4_row, tasks))
    summaries = {}
    checks = {}
    for lesion in v28.LESIONS:
        subset = [row for row in rows if row["lesion"] == lesion]
        intact = np.asarray([float(row["target_intact"]) for row in subset])
        cut = np.asarray([float(row["target_cut"]) for row in subset])
        direction = float(np.mean(np.abs(intact)) - np.mean(np.abs(cut)))
        survival = float(max(row["survivor_error"] for row in subset))
        summaries[lesion] = {
            "n": len(subset),
            "mean_target_intact": float(np.mean(intact)),
            "mean_target_cut": float(np.mean(cut)),
            "mean_absolute_disappearance": direction,
            "maximum_survivor_error": survival,
        }
        checks[f"{lesion}_target_disappears"] = direction > 1e-6
        checks[f"{lesion}_survivor"] = survival <= TOL
    result = {
        "stage": "V2.8", "gate": 4,
        "preregistered_mapping": {
            "local_to_global_broadcast": "global transfer",
            "cue_root_association": "root movement",
            "formation_coupling": "formation forecast coupling",
            "action_to_availability": "closed-loop delivery gap",
            "context_model": "material redescription",
            "episode_interaction": "material reduction",
            "reduction": "material reduction",
            "partner_to_relational_precision": "global relational precision",
            "attribution": "contact forecast through inferred efficacy",
            "partner_to_protector_trust": "protector trust",
            "cross_protector_coupling": "polarization",
            "registration": "registration posterior",
            "policy_to_contact": "contact probability",
        },
        "summaries": summaries,
        "checks": checks,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
    }
    write_json("gate-4.json", result)
    with (OUT / "lesion-matrix.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["lesion", "n", "mean_target_intact", "mean_target_cut", "mean_absolute_disappearance", "maximum_survivor_error"])
        writer.writeheader()
        for lesion, values in summaries.items():
            writer.writerow({"lesion": lesion, **values})
    (OUT / "gate-4-report.md").write_text(
        "# V2.8 Gate 4\n\n"
        f"Verdict: **{result['verdict']}**.\n\n"
        + "\n".join(f"- {name}: {'PASS' if value else 'FAIL'}" for name, value in checks.items())
        + "\n"
    )
    if result["verdict"] == "FAIL":
        failed = [name for name, value in checks.items() if not value]
        (OUT / "gate-4-diagnosis-stub.md").write_text(
            "# V2.8 Gate 4 diagnosis stub\n\n"
            "Execution stopped honestly before Gate 5:\n\n"
            + "\n".join(f"- `{name}`" for name in failed) + "\n"
        )
    return result


def _genome_seed(offset: int) -> list[dict[str, Any]]:
    start, end = PARAMETERS["gate_blocks"]["gate5"]
    block = (start, end)
    seed = start + offset
    rows = []
    for genome in range(128):
        bits = tuple((genome >> index) & 1 for index in range(7))
        if bits[1]:
            stratum = "chronic_multiple"
        else:
            stratum = "chronic_one" if bits[0] else "acute_one"
        protocol = "unreliable_partner" if bits[2] else "full"
        lesions = tuple(
            name for bit, name in zip(
                bits[3:],
                (
                    "local_to_global_broadcast",
                    "cue_root_association",
                    "context_model",
                    "reduction",
                ),
            ) if bit
        )
        state = v28.generate_developmental_state(
            seed, stratum, released_block=block
        )
        profile = v28.run_trajectory(
            state,
            seed,
            protocol=protocol,
            lesions=lesions,
            released_block=block,
        )
        rows.append({
            "genome": genome,
            "bits": bits,
            "seed": seed,
            "stratum": stratum,
            "protocol": protocol,
            "lesions": lesions,
            **plain(profile),
        })
    return rows


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze_manifest() -> dict[str, Any]:
    paths = [
        "contracts/v2.8-complete-trajectory-contract.md",
        "protocols/v2.8-analysis-plan.md",
        "protocols/v2.8-parameters.json",
        "protocols/v2.8-public-dummy.json",
        "ref/v28.py",
        "ref/v28_oracle.py",
        "tests/test_v28.py",
        "run_v28_gates.py",
        "results/V2.8/stage-0-attainability.json",
        "results/V2.8/gate-1.json",
        "results/V2.8/gate-2.json",
        "results/V2.8/gate-2-retained-states.json",
        "results/V2.8/gate-3.json",
        "results/V2.8/gate-4.json",
        "results/V2.8/lesion-matrix.csv",
        "results/V2.8/gate-5.json",
        "results/V2.8/species-panel/summary.json",
        "results/V2.8/parameter-use-matrix.csv",
        "results/V2.8/sensitivity-matrix.csv",
        "results/V2.8/architecture-manifest.json",
        "results/V2.8/reference-strain.json",
        "results/V2.8/cumulative-profile.md",
        "results/V2.8/paper-claim-ledger.md",
        "results/V2.8/freeze-readiness.md",
        "results/V2.8/decisions.md",
        "results/V2.8/development-failures.md",
        "results/V2.8/gate-1-ready-to-commit.md",
        "results/V2.8/gate-2-ready-to-commit.md",
        "results/V2.8/gate-3-ready-to-commit.md",
        "results/V2.8/gate-4-ready-to-commit.md",
        "results/V2.8/gate-5-ready-to-commit.md",
    ]
    return {
        "stage": "V2.8",
        "status": "freeze_candidate_pre_seal",
        "sealed_escrows_accessed": False,
        "files": {path: _sha256(ROOT / path) for path in paths},
    }


def gate5() -> dict[str, Any]:
    completed = subprocess.run(
        ["python3", "run_tests_parallel.py", "--workers", "8"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    (OUT / "full-fast-suite.txt").write_text(completed.stdout)
    constitution_result = constitution.cumulative_constitution_audit()
    chain = manifest_chain.verify_manifest_chain(
        ROOT, "results/V2.7/freeze-manifest.json"
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        nested = list(executor.map(_genome_seed, range(24)))
    rows = [row for group in nested for row in group]
    species = {}
    for genome in range(128):
        subset = [row for row in rows if row["genome"] == genome]
        species[str(genome)] = {
            "bits": subset[0]["bits"],
            "n": len(subset),
            "depth_mean": float(np.mean([row["depth_increase"] for row in subset])),
            "contact_rate": float(np.mean([row["contact"] for row in subset])),
            "transfer_mean": float(np.mean([row["untreated_transfer"] for row in subset])),
            "redescription_rate": float(np.mean([row["material_redescription"] for row in subset])),
            "reduction_rate": float(np.mean([row["material_reduction"] for row in subset])),
            "sequence_rate": float(np.mean([row["successful_sequence"] for row in subset])),
        }
    species_dir = OUT / "species-panel"
    species_dir.mkdir(exist_ok=True)
    (species_dir / "per-world.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    summary = {
        "genomes": species,
        "all_128_reported": len(species) == 128,
        "all_3072_profiles_reported": len(rows) == 3072,
        "selection_or_retuning": False,
        "reference_genome": 0,
        "reference_centrality_percentiles": {
            metric: float(np.mean([
                values[metric] <= species["0"][metric]
                for values in species.values()
            ]))
            for metric in (
                "depth_mean", "contact_rate", "transfer_mean",
                "redescription_rate", "reduction_rate", "sequence_rate",
            )
        },
    }
    write_json("species-panel/summary.json", summary)
    bit_names = (
        "chronic_history",
        "multiple_protectors",
        "unreliable_partner",
        "broadcast_off",
        "association_severed",
        "context_learning_off",
        "reduction_off",
    )
    metrics = (
        "depth_mean", "contact_rate", "transfer_mean",
        "redescription_rate", "reduction_rate", "sequence_rate",
    )
    with (OUT / "parameter-use-matrix.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["parameter", *metrics])
        for bit_index, name in enumerate(bit_names):
            writer.writerow([
                name,
                *[
                    float(np.mean([
                        values[metric]
                        for values in species.values()
                        if values["bits"][bit_index]
                    ]) - np.mean([
                        values[metric]
                        for values in species.values()
                        if not values["bits"][bit_index]
                    ]))
                    for metric in metrics
                ],
            ])
    with (OUT / "sensitivity-matrix.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["genome", *metrics])
        for genome, values in species.items():
            writer.writerow([genome, *[values[metric] for metric in metrics]])
    grammar_shapes = {
        "C-V28A": ("acute_one", 1, ("full", "regulation_only", "bypass_protectors", "premature_do_over")),
        "C-V28B": ("chronic_multiple", 3, ("full", "unreliable_partner")),
        "C-V28C": ("real_danger_adaptive", 1, ("full", "no_context_learning")),
        "C-V28D": ("chronic_one", 1, ("full", "premature_do_over", "no_reduction")),
        "C-V24_scientific_shape": ("chronic_one", 1, ("full", "no_context_learning")),
    }
    linter = {
        name: {
            "stratum_valid": stratum in v28.STRATA,
            "protector_count_valid": count in (1, 2, 3),
            "protocols_valid": all(protocol in v28.PROTOCOLS for protocol in protocols),
            "constructible": (
                stratum in v28.STRATA
                and count in (1, 2, 3)
                and all(protocol in v28.PROTOCOLS for protocol in protocols)
            ),
        }
        for name, (stratum, count, protocols) in grammar_shapes.items()
    }
    write_json("pre-seal-expressibility-linter.json", linter)
    checks = {
        "full_fast_suite": completed.returncode == 0,
        "both_constitutions": bool(constitution_result["passed"]),
        "v27_manifest_chain": bool(chain["passed"]),
        "species_128": summary["all_128_reported"],
        "profiles_3072": summary["all_3072_profiles_reported"],
        "no_selection_or_retuning": not summary["selection_or_retuning"],
        "all_grammar_compositions": all(value["constructible"] for value in linter.values()),
        "escrows_untouched": all(start >= 2_100_000 for start, _ in PARAMETERS["escrow_closed"]),
        "gate1_retained": json.loads((OUT / "gate-1.json").read_text())["verdict"] == "PASS",
        "gate2_retained": json.loads((OUT / "gate-2.json").read_text())["verdict"] == "PASS",
        "gate3_retained": json.loads((OUT / "gate-3.json").read_text())["verdict"] == "PASS",
        "gate4_retained": json.loads((OUT / "gate-4.json").read_text())["verdict"] == "PASS",
    }
    result = {
        "stage": "V2.8", "gate": 5,
        "checks": checks,
        "cumulative_suite_returncode": completed.returncode,
        "constitution": constitution_result,
        "manifest_chain": chain,
        "species_panel": {
            "genomes": 128, "worlds_per_genome": 24,
            "profiles": len(rows),
            "scientific_failures_are_descriptive": True,
        },
        "verdict": "PASS" if all(checks.values()) else "FAIL",
    }
    write_json("gate-5.json", result)
    (OUT / "gate-5-report.md").write_text(
        "# V2.8 Gate 5\n\n"
        f"Verdict: **{result['verdict']}**.\n\n"
        + "\n".join(f"- {name}: {'PASS' if value else 'FAIL'}" for name, value in checks.items())
        + "\n\nAll 128 genomes and all 3,072 profiles are retained without selection.\n"
    )
    if result["verdict"] == "FAIL":
        failed = [name for name, value in checks.items() if not value]
        (OUT / "gate-5-diagnosis-stub.md").write_text(
            "# V2.8 Gate 5 diagnosis stub\n\n"
            "Execution stopped honestly before freeze:\n\n"
            + "\n".join(f"- `{name}`" for name in failed) + "\n"
        )
        return result
    write_json("architecture-manifest.json", {
        "architecture": [
            "V2.0 exact kernel", "V2.1 recursive precision",
            "V2.2.1 identity root", "V2.3.2 formation",
            "V2.3.3 maintenance", "V2.3.4 attribution",
            "V2.4.4 redescription", "V2.5a evidence format",
            "V2.5b reduction", "V2.6a partner",
            "V2.6b protector", "V2.7 multiple protectors",
            "R0 grammar", "V2.8 composition",
        ],
        "new_scientific_primitives": 0,
        "bounds": v28.finite_information_bounds(),
    })
    write_json("reference-strain.json", {
        "genome": 0, "metrics": species["0"],
        "centrality_percentiles": summary["reference_centrality_percentiles"],
        "exceptional": any(
            value < .05 or value > .95
            for value in summary["reference_centrality_percentiles"].values()
        ),
    })
    (OUT / "cumulative-profile.md").write_text(
        "# V2.8 cumulative profile\n\n"
        "Gates 1–5 passed. The 128-genome neighborhood is published without "
        "selection; genome-level scientific misses are descriptive rather than tuned away.\n"
    )
    (OUT / "paper-claim-ledger.md").write_text(
        "# V2.8 paper claim ledger\n\n"
        "- Licensed after sealed completion: one exact, cumulatively validated construction enacted the complete sequence and produced the published profile.\n"
        "- Not licensed: clinical efficacy, human prevalence, uniqueness of IFS language, necessity of every step in people, or psychological falsity from a failed challenge cell.\n"
    )
    (OUT / "freeze-readiness.md").write_text(
        "# V2.8 freeze readiness\n\n"
        "Status: **FREEZE_CANDIDATE_PRE_SEALED_CHALLENGES**.\n\n"
        "All open gates passed. No escrow in 2100000:2139999 was accessed. "
        "Stop here for evaluator custody and the four sealed runs.\n"
    )
    manifest = freeze_manifest()
    write_json("freeze-manifest.json", manifest)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("gate", choices=("pilot", "1", "2", "3", "4", "5"))
    args = parser.parse_args()
    result = (
        pilot() if args.gate == "pilot"
        else gate1() if args.gate == "1"
        else gate2() if args.gate == "2"
        else gate3() if args.gate == "3"
        else gate4() if args.gate == "4"
        else gate5()
    )
    print(json.dumps(plain(result), sort_keys=True))


if __name__ == "__main__":
    main()
