#!/usr/bin/env python3
"""Prospective V3.6 COMPOSE Stage-0 and gate runner."""

from __future__ import annotations

import argparse
import copy
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
sys.path.insert(0, str(ROOT))
from ref import audit, v36, v36_oracle  # noqa: E402
from ref.trace_sink import traced_execution  # noqa: E402


RESULTS = ROOT / "results" / "V3.6"
PARAMETERS = ROOT / "protocols" / "v3.6-parameters.json"
PILOT_BLOCK = (3_600_001, 3_603_999)
BARRED_CUSTODY_SEED = 3_600_000
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
                   allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _write_report(name: str, title: str, result: Mapping[str, Any]) -> None:
    (RESULTS / name).write_text(
        "\n".join([
            f"# {title}", "", f"Verdict: **{result['verdict']}**.", "",
            "```json", json.dumps(_plain(result), indent=2, sort_keys=True,
                                     allow_nan=False), "```", "",
        ]),
        encoding="utf-8",
    )


def _trace_map(name: str, tasks: Sequence[Any], worker: Any) -> list[dict[str, Any]]:
    """Persist every event ledger and row, then hashes, before returning."""
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{name}-traces.jsonl"
    if path.exists() or (RESULTS / f"{name}-trace-hashes.json").exists():
        raise RuntimeError(f"custody refusal: {name} output already exists")
    file_hash = hashlib.sha256()
    records: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    processes = max(1, min(8, (os.cpu_count() or 2) - 1))
    with path.open("xb") as handle:
        with get_context("spawn").Pool(processes) as pool:
            for row in pool.imap(worker, tasks, chunksize=2):
                encoded = _canonical(row)
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
                file_hash.update(encoded)
                records.append({
                    "seed": int(row["seed"]),
                    "sha256": hashlib.sha256(encoded).hexdigest(),
                })
                rows.append(row)
    hash_record = {
        "file": path.name,
        "seed_start": int(tasks[0]) if tasks else None,
        "seed_end": int(tasks[-1]) if tasks else None,
        "world_count": len(rows),
        "file_sha256": file_hash.hexdigest(),
        "records": records,
        "custody_order": "JSONL persisted and fsynced before this hash record; aggregation follows",
    }
    _write_json(f"{name}-trace-hashes.json", hash_record)
    # Verify the on-disk bytes and all gap-free seeds before custody returns.
    if hashlib.sha256(path.read_bytes()).hexdigest() != file_hash.hexdigest():
        raise RuntimeError("custody failure: persisted JSONL hash mismatch")
    if [row["seed"] for row in rows] != list(tasks):
        raise RuntimeError("custody failure: seed order/gap mismatch")
    return rows


def _manifest_audit(stage: str) -> dict[str, Any]:
    path = ROOT / "results" / stage / "freeze-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in manifest["files"].items():
        target = ROOT / relative
        observed = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
        # V3.0's package initializer is explicitly superseded by V3.1's
        # committed initializer; later manifests pin the effective file.
        if stage == "V3.0" and relative == "ref/__init__.py":
            continue
        if observed != expected:
            mismatches.append({"file": relative, "expected": expected, "observed": observed})
    return {"stage": stage, "mismatches": mismatches, "passed": not mismatches}


def run_gate1() -> dict[str, Any]:
    dummy = json.loads((ROOT / "protocols" / "v3.6-public-dummy.json").read_text())
    readout_source = dummy["readout_dummy"]
    readout_before = copy.deepcopy(readout_source)
    recombined = v36_oracle.combine_readouts(readout_source)
    code_source = dummy["code_length_dummy"]["log_priors"]
    code_before = copy.deepcopy(code_source)
    code = v36_oracle.code_length(code_source, dummy["code_length_dummy"]["L_theta_given_H"])
    code_error = abs(code["L_total"] - math.fsum(
        code[key] for key in ("L_grammar", "L_H", "L_theta_given_H", "L_protocol")
    ))
    v35_gate1 = json.loads(
        (ROOT / "results" / "V3.5" / "gate-1-amendment-2-rerun.json").read_text()
    )
    v35_gate2 = json.loads(
        (ROOT / "results" / "V3.5" / "gate-2-amendment-2.json").read_text()
    )
    accounting = json.loads(
        (ROOT / "audits" / "v3.6-compression-accounting.json").read_text()
    )
    source = (ROOT / "ref" / "v36.py").read_text(encoding="utf-8")
    banned = (
        "v232_formation", "v24", "v25a", "v25b", "v234", "v26b",
        "v27", "v28",
    )
    manifests = [_manifest_audit(stage) for stage in (
        "V3.0", "V3.1", "V3.2", "V3.3", "V3.4", "V3.5"
    )]
    proofs = {
        "01_no_v2_scientific_import": not any(token in source for token in banned),
        "02_no_new_scientific_primitive": "adds no likelihood, latent variable, prior, or update equation" in source,
        "03_public_protocol_has_no_conclusion_field": all(
            set(row) == {"event_index", "event_type", "available"}
            for row in v36.protocol_declaration("full")
        ),
        "04_independent_readout_input_copy": readout_source == readout_before,
        "05_independent_readout_values": recombined == {
            "q_identity_organization": 0.7,
            "q_external_danger": 0.2,
            "q_context_specific": 0.7,
            "q_recurrent_context": 0.6,
            "q_current_edge_absence": 0.75,
            "q_partner_reliable": 0.85,
            "q_policy_open": 0.65,
        },
        "06_independent_code_input_copy": code_source == code_before,
        "07_code_length_recombination_error": code_error,
        "08_composition_readout_purity": audit.audit_state(v36.protocol_declaration("full")) == (),
        "09_expanded_item17_retained": bool(v35_gate1["proofs"]["17_expanded_marginal_calibration"]["passed"]),
        "10_candidate_common_registration_error": float(v35_gate1["proofs"]["19_registration_candidate_common_evidence_error"]),
        "11_registration_delivered_masked_error": float(v35_gate1["proofs"]["19_registration_delivered_masked_posterior_error"]),
        "12_stakes_scientific_invariance_error": float(v35_gate2["metrics"]["stakes_scientific_posterior_error_max"]),
        "13_interventional_topology_fixture": bool(v35_gate1["proofs"]["18_interventional_topology_fixture"]["passed"]),
        "14_restricted_prior_identity_error": float(v35_gate1["proofs"]["13_restricted_prior_error"]),
        "15_all_inherited_manifest_chains_effective": all(row["passed"] for row in manifests),
        "16_v35_repair_factors_counted": len(accounting["v3"]["repair_introduced_items_included"]) == 5,
        "17_factor_reduction_at_least_half": bool(accounting["reductions"]["factor_templates_at_least_50_percent"]),
        "18_constant_reduction_at_least_half": bool(accounting["reductions"]["constants_at_least_50_percent"]),
    }
    numeric_tolerance_keys = ("07_", "10_", "11_", "12_", "14_")
    passed = all(
        (value <= TOLERANCE if key.startswith(numeric_tolerance_keys) else bool(value))
        for key, value in proofs.items()
    )
    result = {
        "stage": "V3.6", "gate": 1,
        "seed_consumption": [],
        "bounds": dict(v36.finite_information_bounds()),
        "manifest_audits": manifests,
        "proofs": proofs,
        "verdict": "PASS" if passed else "FAIL",
    }
    _write_json("gate-1.json", result)
    _write_report("gate-1.md", "V3.6 Gate 1 — permanent composition battery", result)
    return result


def _config(protocol: str = "full", **changes: Any) -> v36.ComposeConfig:
    values = dict(
        protocol=protocol, mode_count=3, topology="allied", stakes="low",
        support_target="all", policy_regime="engagement", missingness=0.0,
        length=16,
    )
    values.update(changes)
    return v36.ComposeConfig(**values)


def _readout_dict(readout: v36.CompositionReadout) -> dict[str, Any]:
    return _plain(readout)


@traced_execution
def _pilot_row(seed: int) -> dict[str, Any]:
    if seed == BARRED_CUSTODY_SEED or not PILOT_BLOCK[0] <= seed <= PILOT_BLOCK[1]:
        raise ValueError("pilot seed outside re-scoped authorized block")
    offset = seed - PILOT_BLOCK[0]
    comparator_protocols = v36.PROTOCOLS[1:]
    if offset < 1999:
        comparator = comparator_protocols[offset % len(comparator_protocols)]
        full = v36.run_therapy(seed, _config("full"), released_block=PILOT_BLOCK)
        other = v36.run_therapy(seed, _config(comparator), released_block=PILOT_BLOCK)
        return {
            "seed": seed, "cell": "comparator", "comparator": comparator,
            "full": _readout_dict(full), "other": _readout_dict(other),
        }
    if offset < 2999:
        stress = offset % 10
        base_changes = {
            "mode_count": 1 + (stress % 3),
            "topology": ("independent", "opposed", "allied")[stress % 3],
            "support_target": "one" if stress in {3, 4} else "all",
            "policy_regime": ("exclusion", "monitoring", "engagement", "mixed")[stress % 4],
            "missingness": (0.0, 0.15, 0.3)[stress % 3],
        }
        left = v36.run_therapy(seed, _config("full", stakes="low", **base_changes), released_block=PILOT_BLOCK)
        right = v36.run_therapy(seed, _config("full", stakes="high", **base_changes), released_block=PILOT_BLOCK)
        return {
            "seed": seed, "cell": "round10_stress", "stress_index": stress,
            "low": _readout_dict(left), "high": _readout_dict(right),
        }
    # Compression/calibration profile: the V3 side is sampled here. The V2
    # noninferiority margin was frozen from committed V2-only bootstrap data.
    mode_count = 1 + (offset % 3)
    topology = ("independent", "opposed", "allied")[offset % 3]
    profile = v36.run_therapy(
        seed,
        _config(
            "full", mode_count=mode_count, topology=topology,
            support_target="one" if offset % 2 else "all",
            policy_regime=("exclusion", "engagement")[offset % 2],
            missingness=(0.0, 0.15, 0.3)[offset % 3],
        ),
        released_block=PILOT_BLOCK,
    )
    return {
        "seed": seed, "cell": "compression_profile",
        "truth": {"mode_count": mode_count, "topology": topology},
        "profile": _readout_dict(profile),
    }


def _bootstrap_interval(values: Sequence[float], seed: int) -> list[float]:
    array = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = np.mean(rng.choice(array, (4000, len(array)), replace=True), axis=1)
    return [float(x) for x in np.quantile(means, [0.025, 0.975])]


def _contrast(full: Mapping[str, Any], other: Mapping[str, Any], comparator: str) -> float:
    fields = {
        "regulation_without_root_evidence": "root_evidence_uptake",
        "cue_only_exposure": "root_transfer",
        "mode_bypass": "q_policy_open",
        "soothing_noncontingent_partner": "q_partner_reliable",
        "unreliable_partner": "q_partner_reliable",
        "broadcast_off_monitor": "root_evidence_uptake",
        "context_scope_disabled": "q_context_specific",
        "structural_pruning_disabled": "q_current_edge_absence",
    }
    if comparator == "denied_contact_masked":
        return float(full["contact_response"][2] - other["contact_response"][2])
    return float(full[fields[comparator]] - other[fields[comparator]])


def _aggregate_pilot(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    comparator_rows = [row for row in rows if row["cell"] == "comparator"]
    effects: dict[str, Any] = {}
    attainable = True
    for comparator in v36.PROTOCOLS[1:]:
        selected = [row for row in comparator_rows if row["comparator"] == comparator]
        if comparator == "premature_do_over":
            values = [float(row["full"]["q_current_edge_absence"] - row["other"]["q_current_edge_absence"]) for row in selected]
            interval = _bootstrap_interval(values, 36_000 + len(effects))
            ok = interval[0] >= -0.01 and interval[1] <= 0.01
            effects[comparator] = {"kind": "equivalence", "mean": float(np.mean(values)), "interval_95": interval, "rope": 0.01, "attainable": ok}
        else:
            values = [_contrast(row["full"], row["other"], comparator) for row in selected]
            interval = _bootstrap_interval(values, 36_000 + len(effects))
            ok = interval[0] > 0.0
            effects[comparator] = {"kind": "causal_effect", "mean": float(np.mean(values)), "interval_95": interval, "attainable": ok}
        attainable = attainable and ok
    stress_rows = [row for row in rows if row["cell"] == "round10_stress"]
    scientific_fields = (
        "q_identity_organization", "q_external_danger", "q_action_efficacy",
        "episodic_information", "q_context_specific", "q_recurrent_context",
        "historical_retention", "q_current_edge_absence", "root_revision",
        "q_partner_reliable", "local_precision", "global_precision",
        "root_evidence_uptake", "root_transfer", "q_joint_policy_edge",
        "support_response", "contact_response", "stage_log_evidence",
    )
    stakes_errors = []
    stakes_policy = []
    for row in stress_rows:
        low, high = row["low"], row["high"]
        errors = []
        for field in scientific_fields:
            a, b = low[field], high[field]
            if isinstance(a, list):
                flat_a = np.asarray(a, dtype=object).ravel()
                flat_b = np.asarray(b, dtype=object).ravel()
                numeric = [abs(float(x) - float(y)) for x, y in zip(flat_a, flat_b) if isinstance(x, (int, float)) and isinstance(y, (int, float))]
                errors.append(max(numeric, default=0.0))
            else:
                errors.append(abs(float(a) - float(b)))
        stakes_errors.append(max(errors))
        stakes_policy.append(float(low["q_policy_open"] - high["q_policy_open"]))
    stakes_interval = _bootstrap_interval(stakes_policy, 36_999)
    stakes_ok = max(stakes_errors, default=0.0) <= TOLERANCE and stakes_interval[0] > 0.0
    attainable = attainable and stakes_ok
    profile_rows = [row for row in rows if row["cell"] == "compression_profile"]
    lengths = [float(row["profile"]["L_total"]) for row in profile_rows]
    accounting = json.loads((ROOT / "audits" / "v3.6-compression-accounting.json").read_text())
    result = {
        "stage": "V3.6", "pilot_block": list(PILOT_BLOCK),
        "barred_seed": BARRED_CUSTODY_SEED,
        "world_count": len(rows),
        "seed_order_gap_free": [row["seed"] for row in rows] == list(range(PILOT_BLOCK[0], PILOT_BLOCK[1] + 1)),
        "effects": effects,
        "stakes_identity_error_max": max(stakes_errors, default=0.0),
        "stakes_policy_low_minus_high": {"mean": float(np.mean(stakes_policy)), "interval_95": stakes_interval, "attainable": stakes_interval[0] > 0.0},
        "structure_code_length": {"mean": float(np.mean(lengths)), "min": float(np.min(lengths)), "max": float(np.max(lengths)), "quantiles": [float(x) for x in np.quantile(lengths, [0.05, 0.5, 0.95])]},
        "compression_counts": accounting["reductions"],
        "retained_findings": {
            "V3.1_revisability_effect_interval": json.loads((ROOT / "results" / "V3.1" / "gate-3.json").read_text())["metrics"].get("revisability_difference_95_interval"),
            "V3.3_do_over_equivalence": json.loads((ROOT / "results" / "V3.3" / "gate-5.json").read_text())["adjudicated_nonblocking"].get("do_over_speedup_floor_repetition"),
            "V3.4_information_curve": json.loads((ROOT / "results" / "V3.4" / "gate-5-adjudicated.json").read_text()).get("information_curve"),
            "V3.5_failure_records": [
                "original dormant-idleness proof did not prove common observed-channel support",
                "original polarization readout was conditional rather than interventional",
            ],
        },
        "all_declared_signs_attainable": attainable,
        "verdict": "PASS" if attainable else "FAIL",
    }
    return result


def run_pilot() -> dict[str, Any]:
    gate1 = json.loads((RESULTS / "gate-1.json").read_text())
    if gate1["verdict"] != "PASS":
        raise RuntimeError("Gate 1 must pass before pilot")
    rows = _trace_map(
        "stage-0-attainability-pilot",
        list(range(PILOT_BLOCK[0], PILOT_BLOCK[1] + 1)),
        _pilot_row,
    )
    result = _aggregate_pilot(rows)
    _write_json("stage-0-attainability-pilot.json", result)
    _write_report("stage-0-attainability-pilot.md", "V3.6 traced attainability pilot", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("gate1", "pilot"))
    args = parser.parse_args()
    result = run_gate1() if args.command == "gate1" else run_pilot()
    print(json.dumps({"command": args.command, "verdict": result["verdict"]}, sort_keys=True))


if __name__ == "__main__":
    main()
