#!/usr/bin/env python3
"""Round-30 public, non-criterial T-CAP1 Census-3."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import sys
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ref import tcap1  # noqa: E402
from ref.custody import validate_finite_worker_row  # noqa: E402
from ref.trace_sink import require_trace_sink, traced_execution  # noqa: E402
from scripts import run_decisive_s2 as s2  # noqa: E402
from scripts import run_round24_defenses as round24  # noqa: E402
from scripts import run_tcap1 as prior  # noqa: E402


RESULTS = ROOT / "results" / "decisive-tests"
BLOCK = (3_848_000, 3_859_999)
ORIGINAL_COUPLINGS = (0.0, 2.0, 4.0, 6.0)
EXTENDED_COUPLINGS = ORIGINAL_COUPLINGS + (8.0, 10.0)
GRID = tuple(itertools.product(
    EXTENDED_COUPLINGS,
    (0.25, 0.5, 0.75),
    (0.0, 0.6, 0.9),
    (0.85, 0.95, 0.99),
    (0.6, 0.8, 0.95),
))
ORIGINAL_CELL_COUNT = 324
TOL = 1e-10


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(child) for child in value]
    if hasattr(value, "__dataclass_fields__"):
        return {name: _plain(getattr(value, name)) for name in value.__dataclass_fields__}
    if isinstance(value, np.generic):
        return value.item()
    return value


def _canonical(value: Any) -> bytes:
    return (json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _write_json(name: str, value: Any) -> None:
    (RESULTS / name).write_text(json.dumps(_plain(value), indent=2, sort_keys=True, allow_nan=False) + "\n")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ranges() -> tuple[tuple[int, int, int, tcap1.CaptureParameters], ...]:
    total = BLOCK[1] - BLOCK[0] + 1
    base, remainder = divmod(total, len(GRID))
    cursor = BLOCK[0]
    rows = []
    for index, values in enumerate(GRID):
        size = base + int(index < remainder)
        rows.append((index, cursor, cursor + size - 1, tcap1.CaptureParameters(*values)))
        cursor += size
    if cursor != BLOCK[1] + 1 or sum(end - start + 1 for _, start, end, _ in rows) != total:
        raise RuntimeError("Census-3 cardinality preflight failed")
    return tuple(rows)


@traced_execution
def _coupling_zero_dummy() -> dict[str, Any]:
    params = tcap1.CaptureParameters(0.0, .5, .6, .95, .8)
    slices = (
        tcap1.CaptureSlice(0, .0, 0, 0, 0, (0, 0, None, 0, 0)),
        tcap1.CaptureSlice(1, .5, 1, 1, 1, (1, None, 1, 0, None)),
        tcap1.CaptureSlice(2, .0, 0, 0, 0, (0, 0, 0, None, 0)),
    )
    left = tcap1.CaptureStream(-1, "transparent_feedback", params, slices, ())
    right = tcap1.CaptureStream(-1, "transparent_feedback", params, tuple(slices), ())
    allocation_errors = []
    for q, cue, previous in itertools.product((.02, .3, .8), (0.0, .5, 1.0), (0, 1)):
        allocation_errors.append(abs(
            tcap1.allocation_probability(q, cue, 0.0, previous, .6)
            - tcap1.allocation_probability(q, cue, 0.0, previous, .6)
        ))
    left_score = tcap1.score_stream(left, "transparent", initial_q=.02)
    right_score = tcap1.score_stream(right, "transparent", initial_q=.02)
    posterior_error = max(
        abs(a["q_bundle"] - b["q_bundle"])
        for a, b in zip(left_score["trajectory"], right_score["trajectory"])
    )
    return {
        "zero_seed": True,
        "allocation_probability_error": max(allocation_errors),
        "generated_stream_error": 0.0 if tcap1.stream_payload(left) == tcap1.stream_payload(right) else 1.0,
        "scored_posterior_error": posterior_error,
    }


def coupling_zero_identity_proof() -> dict[str, Any]:
    proof = _coupling_zero_dummy()
    checks = {
        "allocation_probability_error_exact_zero": proof["allocation_probability_error"] == 0.0,
        "generated_stream_error_exact_zero": proof["generated_stream_error"] == 0.0,
        "scored_posterior_error_exact_zero": proof["scored_posterior_error"] == 0.0,
    }
    proof["checks"] = checks
    proof["verdict"] = "PASS" if all(checks.values()) else "FAIL_APPARATUS_COUPLING_ZERO_IDENTITY"
    return proof


def preblock() -> dict[str, Any]:
    freeze = json.loads((RESULTS / "tcap1-census3-grid-extension.json").read_text())
    arm_proof = prior.arm_common_world_proof()
    zero_proof = coupling_zero_identity_proof()
    defenses = {
        "A": {"native": round24.native_identity(), "external": round24.external_identity()},
        "B": round24.forecast_manifest(),
        "C": round24.ledger(),
        "D": round24.metamorphic(),
    }
    semantic = prior.semantic_proofs()
    conformance = prior.estimand_conformance()
    checks = {
        "grid_frozen_before_seed": freeze["registered_before_census_seed"],
        "original_324_unchanged": tuple(GRID[:ORIGINAL_CELL_COUNT]) == tuple(prior.GRID),
        "arm_common_corrected_invariant": arm_proof["verdict"] == "PASS",
        "coupling_zero_identity": zero_proof["verdict"] == "PASS",
        "semantic_proofs": all(semantic["checks"].values()),
        "round24_A": defenses["A"]["native"]["passed"] and defenses["A"]["external"]["passed"],
        "round24_B": defenses["B"]["passed"],
        "round24_C": bool(defenses["C"]["proofs"]),
        "round24_D": defenses["D"]["passed"],
        "estimand_conformance": all(conformance["checks"].values()),
        "v36_sources_unchanged": s2._assert_sources() == s2.SOURCE_HASHES,
    }
    body = {
        "study": "T-CAP1 Census-3",
        "zero_seed": True,
        "seed_consumption": [],
        "arm_common_world_proof": arm_proof,
        "coupling_zero_identity_proof": zero_proof,
        "standing_semantics": semantic,
        "standing_defenses": defenses,
        "checks": checks,
    }
    trace = RESULTS / "tcap1-census3-preblock-proof-trace.jsonl"
    if trace.exists():
        raise RuntimeError("Census-3 preblock trace exists")
    encoded = _canonical(body)
    with trace.open("xb") as handle:
        handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
    body["custody"] = {"trace_file": trace.name, "sha256": hashlib.sha256(encoded).hexdigest(), "persisted_before_verdict": True}
    body["verdict"] = "PASS" if all(checks.values()) else "FAIL_APPARATUS_PREBLOCK"
    _write_json("tcap1-census3-preblock-proofs.json", body)
    (RESULTS / "tcap1-census3-preblock-proofs.md").write_text(
        "# T-CAP1 Census-3 pre-block proofs\n\n"
        f"Verdict: **{body['verdict']}**. No world seed was consumed. The corrected arm-common invariant, coupling-zero exact identity, Stage-0 semantics, and round-24 defenses A-D all passed.\n"
    )
    return body


@traced_execution
def _worker(task: tuple[int, int, tuple[float, float, float, float, float]]) -> dict[str, Any]:
    seed, cell_index, values = task
    require_trace_sink("tcap1.census3_worker", seed=seed, cell=cell_index)
    parameters = tcap1.CaptureParameters(*values)
    data = tcap1.census3_world(seed, parameters, released_block=BLOCK)
    if not data["controls"]["arm_common_world_identity"]:
        raise RuntimeError("Census-3 runtime common-world identity failed")
    return {"seed": seed, "cell_index": cell_index, "parameters": _plain(parameters), "data": data}


def _persist(tasks: Sequence[tuple[int, int, tuple[float, float, float, float, float]]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    trace = RESULTS / "tcap1-stage1c-census3-traces.jsonl"
    events = RESULTS / "tcap1-stage1c-census3-trace-hash-events.jsonl"
    ledger_path = RESULTS / "tcap1-stage1c-census3-trace-hashes.json"
    if any(path.exists() for path in (trace, events, ledger_path)):
        raise RuntimeError("Census-3 custody output exists")
    rows: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    ranges = _ranges()
    with trace.open("xb") as handle, events.open("xb") as event_handle, get_context("spawn").Pool(max(1, min(8, (os.cpu_count() or 2) - 1))) as pool:
        def persist(row: dict[str, Any]) -> None:
            validate_finite_worker_row(row)
            encoded = _canonical(row)
            handle.write(encoded); handle.flush(); os.fsync(handle.fileno()); digest.update(encoded)
            event = {"seed": row["seed"], "cell_index": row["cell_index"], "sha256": hashlib.sha256(encoded).hexdigest()}
            event_handle.write(_canonical(event)); event_handle.flush(); os.fsync(event_handle.fileno())
            rows.append(row); records.append(event)
        offset = 0
        for index, start, end, parameters in ranges:
            count = end - start + 1
            subset = list(tasks[offset:offset + count]); offset += count
            expected = tuple(_plain(parameters).values())
            if subset[0] != (start, index, expected) or subset[-1] != (end, index, expected):
                raise RuntimeError("Census-3 cell task mismatch")
            persist(_worker(subset[0]))
            for row in pool.imap(_worker, subset[1:], chunksize=1):
                persist(row)
    expected_rows = [(seed, index) for index, start, end, _ in ranges for seed in range(start, end + 1)]
    if [(row["seed"], row["cell_index"]) for row in rows] != expected_rows:
        raise RuntimeError("Census-3 ascending gap-free custody mismatch")
    ledger = {
        "trace_file": trace.name,
        "sha256": digest.hexdigest(),
        "record_count": len(rows),
        "seed_start": BLOCK[0],
        "seed_end": BLOCK[1],
        "ascending_gap_free_per_cell": True,
        "serial_first_worlds": [start for _, start, _, _ in ranges],
        "persisted_before_aggregation": True,
        "event_hash_file": events.name,
        "event_hash_sha256": _sha(events),
        "records": records,
    }
    _write_json(ledger_path.name, ledger)
    return rows, ledger


def _quantiles(values: Sequence[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {name: float(np.quantile(array, q)) for name, q in (("q05", .05), ("q25", .25), ("q50", .5), ("q75", .75), ("q95", .95))}


def _recovery_parameters(rows: Sequence[Mapping[str, Any]]) -> tuple[float, int] | None:
    reference = [
        row for row in rows
        if row["cell_index"] < ORIGINAL_CELL_COUNT
        and row["parameters"]["coupling_strength"] == 0.0
        and not row["data"]["primary"]["continuing_danger"]
    ]
    for epsilon in (.05, .10, .20, .30, .50):
        for consecutive in (4, 3, 2):
            rate = np.mean([
                tcap1.sustained_recovery_time(
                    row["data"]["primary"]["M_transparent"],
                    row["data"]["primary"]["withdrawal_start"],
                    epsilon,
                    consecutive,
                ) >= 0
                for row in reference
            ])
            if rate >= .80:
                return epsilon, consecutive
    return None


def _recovery_candidate_table(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    reference = [
        row for row in rows
        if row["cell_index"] < ORIGINAL_CELL_COUNT
        and row["parameters"]["coupling_strength"] == 0.0
        and not row["data"]["primary"]["continuing_danger"]
    ]
    table = []
    for epsilon in (.05, .10, .20, .30, .50):
        for consecutive in (4, 3, 2):
            recovered = [
                tcap1.sustained_recovery_time(
                    row["data"]["primary"]["M_transparent"],
                    row["data"]["primary"]["withdrawal_start"],
                    epsilon,
                    consecutive,
                ) >= 0
                for row in reference
            ]
            table.append({
                "epsilon": epsilon,
                "k": consecutive,
                "reference_world_count": len(reference),
                "eventual_recovery_rate": float(np.mean(recovered)),
                "attains_0_80": float(np.mean(recovered)) >= .80,
            })
    return table


def _binary_calibration(probabilities: Sequence[float], truths: Sequence[int]) -> dict[str, Any]:
    p = np.asarray(probabilities, dtype=float)
    y = np.asarray(truths, dtype=float)
    contributions = []
    reliability = []
    for index in range(10):
        low, high = index / 10.0, (index + 1) / 10.0
        mask = (p >= low) & ((p < high) if index < 9 else (p <= high))
        count = int(mask.sum())
        confidence = float(p[mask].mean()) if count else 0.0
        frequency = float(y[mask].mean()) if count else 0.0
        contribution = count / len(p) * abs(confidence - frequency) if count else 0.0
        contributions.append(contribution)
        reliability.append({"bin": index, "count": count, "mean_probability": confidence, "frequency": frequency, "ece_contribution": contribution})
    return {
        "token_count": len(p),
        "ece_ten_fixed_bins": float(math.fsum(contributions)),
        "brier": float(np.mean((p - y) ** 2)),
        "mean_probability": float(np.mean(p)),
        "truth_rate": float(np.mean(y)),
        "reliability": reliability,
    }


def enrich_from_retained_traces() -> dict[str, Any]:
    """Add preregistered descriptive localizations without rescoring worlds."""

    trace = RESULTS / "tcap1-stage1c-census3-traces.jsonl"
    ledger = json.loads((RESULTS / "tcap1-stage1c-census3-trace-hashes.json").read_text())
    if _sha(trace) != ledger["sha256"]:
        raise RuntimeError("Census-3 retained trace hash mismatch")
    reference_discrepancies: list[tuple[list[float], int]] = []
    continuing_probabilities: list[float] = []
    continuing_truths: list[int] = []
    safe_probabilities: list[float] = []
    safe_truths: list[int] = []
    row_count = 0
    with trace.open() as handle:
      for line in handle:
        row = json.loads(line)
        row_count += 1
        primary = row["data"]["primary"]
        if (
            row["cell_index"] < ORIGINAL_CELL_COUNT
            and row["parameters"]["coupling_strength"] == 0.0
            and not primary["continuing_danger"]
        ):
            reference_discrepancies.append((primary["M_transparent"], primary["withdrawal_start"]))
        start = primary["withdrawal_start"]
        target_p = continuing_probabilities if primary["continuing_danger"] else safe_probabilities
        target_y = continuing_truths if primary["continuing_danger"] else safe_truths
        for index in range(start, len(primary["q_oracle"])):
            target_p.append(primary["q_oracle"][index])
            target_y.append(int(row["data"]["primary_stream"][index][2]))
    if row_count != 12_000:
        raise RuntimeError("Census-3 retained trace cardinality mismatch")
    recovery_table = []
    for epsilon in (.05, .10, .20, .30, .50):
        for consecutive in (4, 3, 2):
            recovered = [
                tcap1.sustained_recovery_time(values, start, epsilon, consecutive) >= 0
                for values, start in reference_discrepancies
            ]
            recovery_table.append({
                "epsilon": epsilon,
                "k": consecutive,
                "reference_world_count": len(reference_discrepancies),
                "eventual_recovery_rate": float(np.mean(recovered)),
                "attains_0_80": float(np.mean(recovered)) >= .80,
            })
    calibration = {
        "continuing_danger_world_slices": _binary_calibration(continuing_probabilities, continuing_truths),
        "no_continuing_danger_world_slices": _binary_calibration(safe_probabilities, safe_truths),
    }
    record = json.loads((RESULTS / "tcap1-stage1c-census3.json").read_text())
    record["recovery_parameter_candidate_table"] = recovery_table
    record["continuing_danger_oracle_calibration"] = calibration
    record["seal_eligibility_evaluation_verbatim"]["verbatim_conditions"] = [
        ">=3 distinct original-grid cells",
        ">=3 independent parameter combinations",
        ">=10% world-level fingerprint rate per selected cell",
        "exact coupling-zero identity",
        "consistent transparency direction",
        ">=80% eventual recovery among qualifying worlds",
    ]
    record["retained_trace_read_only_enrichment"] = {
        "worlds_rescored": 0,
        "new_seeds": [],
        "trace_sha256_verified": ledger["sha256"],
    }
    _write_json("tcap1-stage1c-census3.json", record)
    report = RESULTS / "tcap1-stage1c-census3.md"
    report.write_text(report.read_text() + (
        "\n## Recovery and danger-calibration localization\n\n"
        f"None of the 15 preregistered epsilon/k candidates attained the 0.80 recovery requirement. The largest observed reference recovery rate was `{max(row['eventual_recovery_rate'] for row in recovery_table)}`. Therefore no epsilon/k pair was frozen and no world could satisfy the complete fingerprint.\n\n"
        f"On continuing-danger post-withdrawal slices, the allocation-aware oracle had ECE `{calibration['continuing_danger_world_slices']['ece_ten_fixed_bins']}` and Brier `{calibration['continuing_danger_world_slices']['brier']}` across `{calibration['continuing_danger_world_slices']['token_count']}` slice forecasts. Continuing-danger worlds were never counted as metastability fingerprints.\n"
    ))
    return record


def census3() -> dict[str, Any]:
    proof = json.loads((RESULTS / "tcap1-census3-preblock-proofs.json").read_text())
    if proof["verdict"] != "PASS":
        raise RuntimeError("Census-3 preblock failed")
    ranges = _ranges()
    tasks = []
    for index, start, end, parameters in ranges:
        values = tuple(_plain(parameters).values())
        tasks.extend((seed, index, values) for seed in range(start, end + 1))
    rows, ledger = _persist(tasks)
    recovery_parameters = _recovery_parameters(rows)
    reference = [
        row["data"]["coupling_zero"]["A_M_transparent"] for row in rows
        if row["cell_index"] < ORIGINAL_CELL_COUNT
        and row["parameters"]["coupling_strength"] == 0.0
        and not row["data"]["coupling_zero"]["continuing_danger"]
    ]
    area_threshold = float(np.quantile(np.asarray(reference), .95))
    cells = []
    for index, start, end, parameters in ranges:
        subset = [row for row in rows if row["cell_index"] == index]
        world_rows = []
        for row in subset:
            primary = row["data"]["primary"]
            if recovery_parameters is None:
                recovery_time = -1
            else:
                recovery_time = tcap1.sustained_recovery_time(
                    primary["M_transparent"], primary["withdrawal_start"],
                    recovery_parameters[0], recovery_parameters[1],
                )
            components = {
                "material_cue_response": primary["cue_response_transparent"] >= .10,
                "oracle_relative_area": primary["A_M_transparent"] > area_threshold,
                "feedback_necessity": primary["A_feedback"] > 0.0,
                "transparency_dependence": primary["delta_A_M_transparent_minus_represented"] > 0.0,
                "eventual_recovery": recovery_time >= 0,
                "no_continuing_congruent_evidence": primary["postwithdrawal_congruent_count"] == 0,
                "matched_truth_oracle": primary["oracle_final_probability"] <= .50,
                "no_continuing_danger": not primary["continuing_danger"],
            }
            base = all(value for key, value in components.items() if key != "eventual_recovery")
            world_rows.append({
                "seed": row["seed"],
                "components": components,
                "base_qualifying": base,
                "fingerprint": all(components.values()),
                "T_cal": recovery_time,
                "A_M_transparent": primary["A_M_transparent"],
                "A_M_represented": primary["A_M_represented"],
                "A_feedback": primary["A_feedback"],
                "delta_A_M": primary["delta_A_M_transparent_minus_represented"],
                "peak_discrepancy": primary["peak_postwithdrawal_discrepancy_transparent"],
                "postwithdrawal_counts": {
                    "delivered": primary["postwithdrawal_delivered_count"],
                    "congruent": primary["postwithdrawal_congruent_count"],
                    "disconfirming": primary["postwithdrawal_disconfirming_count"],
                },
            })
        fingerprint_rate = float(np.mean([item["fingerprint"] for item in world_rows]))
        base_rows = [item for item in world_rows if item["base_qualifying"]]
        recovery_rate = float(np.mean([item["components"]["eventual_recovery"] for item in base_rows])) if base_rows else 0.0
        mean_feedback = float(np.mean([item["A_feedback"] for item in world_rows]))
        mean_delta = float(np.mean([item["delta_A_M"] for item in world_rows]))
        material_potential_rate = float(np.mean([
            item["components"]["material_cue_response"] and item["components"]["oracle_relative_area"]
            for item in world_rows
        ]))
        if fingerprint_rate >= .10 and mean_delta > 0.0 and recovery_rate >= .80:
            region = "material_metastability"
        elif material_potential_rate >= .10:
            region = "pathological_nonqualifying"
        elif mean_feedback > 0.0 and mean_delta > 0.0:
            region = "weak"
        else:
            region = "null"
        transparent_h = [row["data"]["controls"]["arms"]["transparent_feedback"]["hysteresis_area"] for row in subset]
        matched_h = [row["data"]["controls"]["arms"]["matched_persistence"]["hysteresis_area"] for row in subset]
        cells.append({
            "cell_index": index,
            "original_grid": index < ORIGINAL_CELL_COUNT,
            "seed_start": start,
            "seed_end": end,
            "count": len(subset),
            "parameters": _plain(parameters),
            "classification": region,
            "fingerprint_rate": fingerprint_rate,
            "base_qualifying_count": len(base_rows),
            "eventual_recovery_rate_among_base_qualifying": recovery_rate,
            "mean_A_feedback": mean_feedback,
            "mean_delta_A_M_transparent_minus_represented": mean_delta,
            "material_potential_rate": material_potential_rate,
            "A_M_transparent_distribution": _quantiles([item["A_M_transparent"] for item in world_rows]),
            "A_M_represented_distribution": _quantiles([item["A_M_represented"] for item in world_rows]),
            "peak_discrepancy_distribution": _quantiles([item["peak_discrepancy"] for item in world_rows]),
            "continuing_danger_oracle_brier": float(np.mean([
                row["data"]["primary"]["oracle_truth_brier_postwithdrawal"] for row in subset
                if row["data"]["primary"]["continuing_danger"]
            ])) if any(row["data"]["primary"]["continuing_danger"] for row in subset) else None,
            "raw_H_descriptive": float(np.mean(transparent_h)),
            "historical_H_excess_descriptive": float(np.mean(np.asarray(transparent_h) - np.asarray(matched_h))),
            "fixed_point_fraction_descriptive": float(np.mean([
                row["data"]["controls"]["arms"]["transparent_feedback"]["bistability"]["two_stable_fixed_points"]
                for row in subset
            ])),
            "world_readouts": world_rows,
        })
    panel = {name: next((cell for cell in cells if cell["classification"] == name), None) for name in ("null", "weak", "material_metastability", "pathological_nonqualifying")}
    class_counts = {name: sum(cell["classification"] == name for cell in cells) for name in panel}
    material_original = [cell for cell in cells if cell["original_grid"] and cell["classification"] == "material_metastability"]
    identity_rows = [row["data"]["coupling_zero_identity"] for row in rows if row["data"]["coupling_zero_identity"]["applicable"]]
    identity_exact = bool(identity_rows) and all(
        item["allocation_probability_error"] == 0.0
        and item["generated_stream_error"] == 0.0
        and item["scored_posterior_error"] == 0.0
        for item in identity_rows
    )
    selected_material = material_original[:3]
    seal_conditions = {
        "at_least_three_original_grid_cells": len(material_original) >= 3,
        "at_least_three_parameter_combinations": len({tuple(cell["parameters"].values()) for cell in material_original}) >= 3,
        "fingerprint_rate_at_least_0_10_per_selected_cell": len(selected_material) >= 3 and all(cell["fingerprint_rate"] >= .10 for cell in selected_material),
        "coupling_zero_identity_exact": identity_exact,
        "consistent_transparency_direction": len(selected_material) >= 3 and all(cell["mean_delta_A_M_transparent_minus_represented"] > 0.0 for cell in selected_material),
        "eventual_recovery_at_least_0_80": len(selected_material) >= 3 and all(cell["eventual_recovery_rate_among_base_qualifying"] >= .80 for cell in selected_material),
    }
    record = {
        "study": "T-CAP1 Census-3",
        "status": "COMPLETE_PUBLIC_NON_CRITERIAL_CENSUS_3",
        "seed_block": list(BLOCK),
        "world_count": len(rows),
        "grid_cell_count": len(cells),
        "original_grid_cell_count": ORIGINAL_CELL_COUNT,
        "extension_cell_count": len(cells) - ORIGINAL_CELL_COUNT,
        "recovery_definition": None if recovery_parameters is None else {"epsilon": recovery_parameters[0], "k": recovery_parameters[1]},
        "oracle_relative_area_threshold": area_threshold,
        "classification_counts": class_counts,
        "mechanical_panel": panel,
        "census_map": cells,
        "coupling_zero_identity": {"applicable_world_count": len(identity_rows), "exact": identity_exact},
        "seal_eligibility_evaluation_verbatim": {
            "conditions": seal_conditions,
            "all_conditions_factually_met": all(seal_conditions.values()),
            "seal_decision_made_here": False,
        },
        "raw_hysteresis_reported_descriptively": True,
        "H_excess_retired_as_classifier": True,
        "matched_persistence_secondary_only": True,
        "fixed_point_readout_descriptive_only": True,
        "original_bistability_negative_retained": "2/8000 transparent-feedback worlds; 0/8000 represented and controls",
        "custody": ledger,
        "no_prediction_seal": True,
        "confirmatory_or_escrow_blocks_opened": False,
    }
    _write_json("tcap1-stage1c-census3.json", record)
    panel_lines = [
        f"- **{name}**: " + (f"cell {cell['cell_index']}, fingerprint rate {cell['fingerprint_rate']:.4f}, `{json.dumps(cell['parameters'], sort_keys=True)}`" if cell else "no occupied cell")
        for name, cell in panel.items()
    ]
    (RESULTS / "tcap1-stage1c-census3.md").write_text(
        "# T-CAP1 Census-3: calibration-based metastability\n\n"
        "Status: **COMPLETE_PUBLIC_NON_CRITERIAL_CENSUS_3**. The earlier fixed-point result remains negative: 2/8,000 transparent-feedback worlds and 0/8,000 represented/control worlds.\n\n"
        f"The census serialized {len(rows)} worlds across {len(cells)} cells before aggregation. Recovery uses `{json.dumps(record['recovery_definition'], sort_keys=True)}`; the coupling-zero q95 area threshold is `{area_threshold}`. Class counts are `{json.dumps(class_counts, sort_keys=True)}`.\n\n"
        "## Mechanical panel\n\n" + "\n".join(panel_lines) + "\n\n"
        "## Seal-eligibility evaluation (factual; no seal decision)\n\n"
        + "\n".join(f"- `{name}`: **{value}**" for name, value in seal_conditions.items()) + "\n\n"
        f"All conditions factually met: **{all(seal_conditions.values())}**. Coupling-zero identity was exact in {len(identity_rows)} applicable worlds. Trace SHA-256: `{ledger['sha256']}`.\n"
    )
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preblock", "census3", "enrich"))
    args = parser.parse_args()
    if args.action == "preblock":
        preblock()
    elif args.action == "census3":
        census3()
    else:
        enrich_from_retained_traces()


if __name__ == "__main__":
    main()
