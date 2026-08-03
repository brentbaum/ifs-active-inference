#!/usr/bin/env python3
"""V3.6 Gate 5 cumulative regression and robustness battery."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import math
import os
from multiprocessing import get_context
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ref import v36  # noqa: E402
from ref.custody import NonFiniteWorkerRow, validate_finite_worker_row  # noqa: E402
from ref.trace_sink import traced_execution  # noqa: E402


RESULTS = ROOT / "results" / "V3.6"
BLOCK = (3_635_000, 3_659_999)
TOLERANCE = 1e-10
PARAMETERS = ROOT / "protocols" / "v3.6-parameters.json"
EFFECT_COMPARATORS = (
    "broadcast_off_monitor",
    "context_scope_disabled",
    "cue_only_exposure",
    "denied_contact_masked",
    "mode_bypass",
    "regulation_without_root_evidence",
    "soothing_noncontingent_partner",
    "structural_pruning_disabled",
    "unreliable_partner",
)


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
                   allow_nan=False).encode("utf-8") + b"\n"
    )


def _write_json(name: str, value: Any) -> None:
    path = RESULTS / name
    encoded = (
        json.dumps(_plain(value), indent=2, sort_keys=True, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    with path.open("xb") as handle:
        handle.write(encoded); handle.flush(); os.fsync(handle.fileno())


def _config(protocol: str = "full", **changes: Any) -> v36.ComposeConfig:
    values = {
        "protocol": protocol, "mode_count": 3, "topology": "allied",
        "stakes": "low", "support_target": "all",
        "policy_regime": "engagement", "missingness": 0.0, "length": 16,
    }
    values.update(changes)
    return v36.ComposeConfig(**values)


def _readout(value: v36.CompositionReadout) -> dict[str, Any]:
    return _plain(asdict(value))


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


@traced_execution
def _worker(task: tuple[int, str, Any]) -> dict[str, Any]:
    seed, cell, argument = task
    if not BLOCK[0] <= seed <= BLOCK[1]:
        raise ValueError("Gate-5 seed outside authorized block")
    if cell == "effect":
        comparator = str(argument)
        full = _readout(v36.run_therapy(seed, _config(), released_block=BLOCK))
        other = _readout(v36.run_therapy(
            seed, _config(comparator), released_block=BLOCK
        ))
        return {
            "seed": seed, "cell": cell, "comparator": comparator,
            "effect": _contrast(full, other, comparator),
            "full": full, "other": other,
        }
    if cell == "stakes":
        low = _readout(v36.run_therapy(
            seed, _config(stakes="low"), released_block=BLOCK
        ))
        high = _readout(v36.run_therapy(
            seed, _config(stakes="high"), released_block=BLOCK
        ))
        return {"seed": seed, "cell": cell, "low": low, "high": high}
    if cell == "information":
        length = int(argument)
        value = _readout(v36.run_therapy(
            seed, _config(length=length), released_block=BLOCK
        ))
        return {"seed": seed, "cell": cell, "length": length, "value": value}
    if cell == "robustness":
        index = int(argument)
        changes = {
            "mode_count": 1 + index % 3,
            "topology": ("independent", "opposed", "allied")[index % 3],
            "stakes": ("low", "high")[index % 2],
            "support_target": ("one", "all")[index % 2],
            "policy_regime": ("exclusion", "monitoring", "engagement", "mixed")[index % 4],
            "missingness": (0.0, 0.15, 0.30)[index % 3],
            "length": (16, 32, 48, 64)[index % 4],
        }
        value = _readout(v36.run_therapy(
            seed, _config(**changes), released_block=BLOCK
        ))
        return {
            "seed": seed, "cell": cell, "configuration": changes,
            "value": value,
        }
    raise ValueError(f"unknown Gate-5 cell {cell}")


def _tasks() -> tuple[list[tuple[int, str, Any]], list[int]]:
    tasks: list[tuple[int, str, Any]] = []
    groups: list[int] = []
    seed = BLOCK[0]
    for comparator in EFFECT_COMPARATORS:
        tasks.extend((value, "effect", comparator) for value in range(seed, seed + 2000))
        groups.append(2000); seed += 2000
    tasks.extend((value, "stakes", None) for value in range(seed, seed + 2000))
    groups.append(2000); seed += 2000
    for length in (32, 48, 64):
        tasks.extend((value, "information", length) for value in range(seed, seed + 1000))
        groups.append(1000); seed += 1000
    tasks.extend((value, "robustness", value - seed) for value in range(seed, seed + 2000))
    groups.append(2000); seed += 2000
    if seed != BLOCK[1] + 1 or len(tasks) != 25_000:
        raise AssertionError("Gate-5 task partition does not cover its block")
    return tasks, groups


def _persist(tasks: Sequence[tuple[int, str, Any]], groups: Sequence[int]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    trace = RESULTS / "v3.6-r1-gate5-traces.jsonl"
    hashes = RESULTS / "v3.6-r1-gate5-trace-hashes.json"
    events = RESULTS / "v3.6-r1-gate5-trace-hash-events.jsonl"
    if trace.exists() or hashes.exists() or events.exists():
        raise RuntimeError("custody refusal: Gate-5 outputs already exist")
    rows: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    processes = max(1, min(8, (os.cpu_count() or 2) - 1))

    def persist(trace_handle, event_handle, row):
        try:
            validate_finite_worker_row(row)
        except NonFiniteWorkerRow as error:
            provenance = {
                "record_type": "NONFINITE_WORKER_ROW_REJECTION",
                "seed": int(row.get("seed", -1)), "cell": row.get("cell"),
                "offending_paths": list(error.paths),
            }
            encoded = _canonical(provenance)
            trace_handle.write(encoded); trace_handle.flush(); os.fsync(trace_handle.fileno())
            raise RuntimeError(str(error)) from error
        encoded = _canonical(row)
        trace_handle.write(encoded); trace_handle.flush(); os.fsync(trace_handle.fileno())
        digest.update(encoded)
        record = {"seed": int(row["seed"]), "sha256": hashlib.sha256(encoded).hexdigest()}
        event_handle.write(_canonical(record)); event_handle.flush(); os.fsync(event_handle.fileno())
        records.append(record); rows.append(row)

    position = 0
    serial_first = []
    with trace.open("xb") as trace_handle, events.open("xb") as event_handle:
        for size in groups:
            group = tasks[position:position + size]
            serial_first.append(int(group[0][0]))
            persist(trace_handle, event_handle, _worker(group[0]))
            with get_context("spawn").Pool(processes) as pool:
                for row in pool.imap(_worker, group[1:], chunksize=2):
                    persist(trace_handle, event_handle, row)
            position += size
    expected = list(range(BLOCK[0], BLOCK[1] + 1))
    if [int(row["seed"]) for row in rows] != expected:
        raise RuntimeError("Gate-5 seed order/gap mismatch")
    ledger = {
        "file": trace.name, "sha256": digest.hexdigest(),
        "record_count": len(rows), "seed_block": list(BLOCK),
        "ascending_gap_free": True, "persisted_before_aggregation": True,
        "incremental_hash_events_file": events.name,
        "incremental_hash_events_sha256": hashlib.sha256(events.read_bytes()).hexdigest(),
        "serial_cell_first_seeds": serial_first,
        "records": records,
    }
    _write_json(hashes.name, ledger)
    if hashlib.sha256(trace.read_bytes()).hexdigest() != digest.hexdigest():
        raise RuntimeError("Gate-5 persisted trace hash mismatch")
    return rows, ledger


def _bootstrap(values: Sequence[float], seed: int) -> list[float]:
    array = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(100):
        indices = rng.integers(0, len(array), size=(100, len(array)))
        means.extend(np.mean(array[indices], axis=1))
    return [float(value) for value in np.quantile(means, (0.025, 0.975))]


SCIENTIFIC_FIELDS = (
    "q_identity_organization", "q_external_danger", "q_action_efficacy",
    "episodic_information", "q_context_specific", "q_recurrent_context",
    "historical_retention", "q_current_edge_absence", "root_revision",
    "q_partner_reliable", "local_precision", "global_precision",
    "root_evidence_uptake", "root_transfer", "q_joint_policy_edge",
    "support_response", "contact_response", "stage_log_evidence",
)


def _distance(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    errors = []
    for field in SCIENTIFIC_FIELDS:
        a, b = left[field], right[field]
        if isinstance(a, list):
            aa, bb = np.asarray(a, dtype=object).ravel(), np.asarray(b, dtype=object).ravel()
            errors.extend(
                abs(float(x) - float(y)) for x, y in zip(aa, bb)
                if isinstance(x, (int, float)) and isinstance(y, (int, float))
            )
        else:
            errors.append(abs(float(a) - float(b)))
    return max(errors, default=0.0)


def _effective_manifest_audit() -> list[dict[str, Any]]:
    current_seed_map = hashlib.sha256(
        (ROOT / "protocols" / "epoch-c-seed-map.json").read_bytes()
    ).hexdigest()
    results = []
    for stage in ("V3.0", "V3.1", "V3.2", "V3.3", "V3.4", "V3.5"):
        path = ROOT / "results" / stage / "freeze-manifest.json"
        manifest = json.loads(path.read_text())
        mismatches = []
        superseded = []
        for relative, expected in manifest["files"].items():
            target = ROOT / relative
            observed = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
            if stage == "V3.0" and relative == "ref/__init__.py":
                superseded.append({"file": relative, "reason": "later stage initializer"})
                continue
            if observed != expected:
                if relative == "protocols/epoch-c-seed-map.json" and stage in {"V3.0", "V3.1"}:
                    superseded.append({
                        "file": relative, "base_hash": expected,
                        "effective_hash": current_seed_map,
                        "reason": "append-only Epoch-C custody succession pinned by later manifests",
                    })
                else:
                    mismatches.append({"file": relative, "expected": expected, "observed": observed})
        results.append({
            "stage": stage, "manifest": str(path.relative_to(ROOT)),
            "mismatches": mismatches, "authorized_supersessions": superseded,
            "passed": not mismatches,
        })
    return results


def run() -> dict[str, Any]:
    tasks, groups = _tasks()
    rows, ledger = _persist(tasks, groups)
    parameters = json.loads(PARAMETERS.read_text())
    floors = parameters["criteria"]["effect_minima"]
    failures = []
    effects = {}
    for index, comparator in enumerate(EFFECT_COMPARATORS):
        values = [float(row["effect"]) for row in rows if row["cell"] == "effect" and row["comparator"] == comparator]
        interval = _bootstrap(values, 3_635_000 + index)
        mean = float(np.mean(values))
        passed = mean >= floors[comparator] and interval[0] > 0.0
        effects[comparator] = {
            "world_count": len(values), "mean": mean, "interval_95": interval,
            "floor": floors[comparator], "passed": passed,
        }
        if not passed:
            failures.append(f"primary effect {comparator} failed")

    stakes_rows = [row for row in rows if row["cell"] == "stakes"]
    identity = [_distance(row["low"], row["high"]) for row in stakes_rows]
    policy = [float(row["low"]["q_policy_open"] - row["high"]["q_policy_open"]) for row in stakes_rows]
    policy_interval = _bootstrap(policy, 3_653_000)
    stakes = {
        "world_count": len(stakes_rows),
        "scientific_identity_error_max": max(identity),
        "identity_tolerance": parameters["criteria"]["stakes_scientific_identity_tolerance"],
        "policy_effect_mean": float(np.mean(policy)),
        "policy_effect_interval_95": policy_interval,
        "policy_floor": parameters["criteria"]["stakes_policy_effect_min"],
    }
    stakes["passed"] = bool(
        stakes["scientific_identity_error_max"] <= stakes["identity_tolerance"]
        and stakes["policy_effect_mean"] >= stakes["policy_floor"]
        and policy_interval[0] > 0.0
    )
    if not stakes["passed"]:
        failures.append("primary stakes identity/policy effect failed")

    curve_fields = (
        "q_identity_organization", "q_context_specific",
        "q_current_edge_absence", "q_partner_reliable", "q_policy_open",
        "L_total",
    )
    information_curve = {}
    primary_full = [row["full"] for row in rows if row["cell"] == "effect"]
    information_curve["16"] = {
        field: float(np.mean([row[field] for row in primary_full]))
        for field in curve_fields
    }
    information_curve["16"]["world_count"] = len(primary_full)
    for length in (32, 48, 64):
        selected = [row["value"] for row in rows if row["cell"] == "information" and row["length"] == length]
        information_curve[str(length)] = {
            **{field: float(np.mean([row[field] for row in selected])) for field in curve_fields},
            "world_count": len(selected),
        }

    robust_rows = [row for row in rows if row["cell"] == "robustness"]
    robustness = {
        "classification": "DESCRIPTIVE_SWEEP_NO_PRIMARY_FLOOR_TRANSPLANT",
        "world_count": len(robust_rows),
        "all_finite": all(math.isfinite(float(row["value"]["L_total"])) for row in robust_rows),
        "mode_counts": sorted(set(row["configuration"]["mode_count"] for row in robust_rows)),
        "lengths": sorted(set(row["configuration"]["length"] for row in robust_rows)),
        "missingness": sorted(set(row["configuration"]["missingness"] for row in robust_rows)),
        "L_total_range": [
            min(float(row["value"]["L_total"]) for row in robust_rows),
            max(float(row["value"]["L_total"]) for row in robust_rows),
        ],
    }
    if not robustness["all_finite"]:
        failures.append("robustness sweep produced nonfinite output")

    manifests = _effective_manifest_audit()
    if not all(row["passed"] for row in manifests):
        failures.append("inherited freeze manifest verification failed")
    gate2 = json.loads((RESULTS / "gate-2.json").read_text())
    gate3 = json.loads((RESULTS / "gate-3.json").read_text())
    gate4 = json.loads((RESULTS / "v3.6-r1-gate4-verdict.json").read_text())
    pop_a = json.loads((RESULTS / "v3.6-r1-round15-v3-native-a-r1-qualification.json").read_text())
    pop_b = json.loads((RESULTS / "v3.6-r1-round12-v2-native-replacement-qualification.json").read_text())
    pop_c = json.loads((RESULTS / "v3.6-r1-round16-population-c-qualification.json").read_text())
    tournament = json.loads((RESULTS / "v3.6-r1-tournament-verdict.json").read_text())
    fixture = json.loads((RESULTS / "v3.6-r1-round13-native-fixture-identity-proofs.json").read_text())
    support = json.loads((RESULTS / "shared-target-support-audit.json").read_text())
    accounting = json.loads((ROOT / "audits" / "v3.6-compression-accounting.json").read_text())
    if gate2["verdict"] != "PASS": failures.append("Gate 2 cumulative regression failed")
    if gate4["verdict"] != "PASS": failures.append("Gate 4 retained scientific FAIL")
    if pop_a["verdict"] != "PASS" or pop_b["verdict"] != "PASS" or pop_c["verdict"] != "PASS":
        failures.append("native/external qualification regression failed")
    if fixture["verdict"] != "PASS" or not support["passed"]:
        failures.append("bridge fixture/support regression failed")

    result = {
        "stage": "V3.6", "gate": 5, "seed_block": list(BLOCK),
        "world_count": len(rows), "primary_effects": effects, "stakes": stakes,
        "information_curves": information_curve, "robustness": robustness,
        "cumulative_regression": {
            "gate2": gate2["verdict"],
            "gate3_original": gate3["verdict"],
            "gate4": gate4["verdict"],
            "tournament_immutable_verdict": tournament["immutable_verdict"],
            "tournament_scientific_status": tournament["scientific_status"],
            "tournament_failure_is_retained_not_recomputed": True,
            "population_a": pop_a["verdict"], "population_b": pop_b["verdict"],
            "population_c": pop_c["verdict"],
            "target_predictive_calibration": {
                "population_a": pop_a["predictive_calibration"],
                "population_c_descriptive": pop_c["external_calibration_descriptive_nonblocking"],
            },
            "equivalence_class_profile": pop_a["structure_calibration"],
            "common_support_equality": support["passed"],
            "fixture_proofs": fixture["verdict"],
            "prior_model_averaging_decomposition": {
                "gate2_expanded_item17": gate2["expanded_item17"]["passed"],
                "L_total_identity": "L_grammar + L_H + L_theta_given_H + L_protocol",
                "factor_template_reduction": accounting["reductions"]["factor_templates_fraction"],
                "constant_reduction": accounting["reductions"]["frozen_scientific_constants_fraction"],
            },
            "inherited_manifests": manifests,
        },
        "retained_findings": {
            "premature_do_over": parameters["retained_descriptive_findings"]["premature_do_over_endpoint_path_independence"],
            "gate3_tournament": tournament["scientific_status"],
            "gate4_failures": gate4["failures"],
        },
        "bounds": dict(v36.finite_information_bounds()),
        "custody": ledger, "failures": failures,
        "immutable_verdict": "PASS" if not failures else "FAIL",
        "verdict": "PASS" if not failures else "FAIL",
    }
    _write_json("v3.6-r1-gate5-verdict.json", result)
    report = [
        "# V3.6-R1 Gate 5 verdict", "",
        f"Immutable verdict: **{result['immutable_verdict']}**.", "",
        "Primary-length floors were applied only to their own cells. The",
        "32/48/64 information curves and joint robustness panel are descriptive.",
        "The tournament and Gate-4 verdicts are retained verbatim.", "",
        "```json", json.dumps(_plain(result), indent=2, sort_keys=True, allow_nan=False),
        "```", "",
    ]
    (RESULTS / "v3.6-r1-gate5-verdict.md").write_text("\n".join(report), encoding="utf-8")
    return result


if __name__ == "__main__":
    result = run()
    print(json.dumps({"gate": 5, "verdict": result["verdict"]}, sort_keys=True))
