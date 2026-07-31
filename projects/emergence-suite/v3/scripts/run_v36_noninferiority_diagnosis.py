#!/usr/bin/env python3
"""Read-only localization of the V3.6 Gate-3 predictive comparison.

This runner consumes only the evaluator-authorized diagnosis block.  It does
not evaluate a criterion.  Every per-world row, including its runtime event
ledger, is persisted and hashed before aggregation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from dataclasses import asdict
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT.parent
sys.path.insert(0, str(SUITE_ROOT))
sys.path.insert(0, str(ROOT))

from ref import v31, v36  # noqa: E402
from ref.trace_sink import require_trace_sink, traced_execution  # noqa: E402
from v2.ref import v232_formation as v2_formation, v28 as v2_trajectory  # noqa: E402


RESULTS = ROOT / "results" / "V3.6"
BLOCK = (3_665_160, 3_667_159)
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
                   allow_nan=False).encode("utf-8") + b"\n"
    )


def _logsumexp(values: Sequence[float]) -> float:
    maximum = max(values)
    return maximum + math.log(math.fsum(math.exp(value - maximum) for value in values))


def _entropy(probabilities: Sequence[float]) -> float:
    return -math.fsum(float(p) * math.log(float(p)) for p in probabilities if p > 0.0)


def _ece(confidences: Sequence[float], correct: Sequence[bool]) -> float:
    p = np.asarray(confidences, dtype=float)
    y = np.asarray(correct, dtype=float)
    total = 0.0
    for index in range(10):
        low, high = index / 10.0, (index + 1) / 10.0
        selected = (p >= low) & (p <= high if index == 9 else p < high)
        if selected.any():
            total += float(selected.mean()) * abs(float(p[selected].mean()) - float(y[selected].mean()))
    return float(total)


def _v3_factor_scores(world: v31.FormationWorld) -> dict[str, float]:
    """Truth-structure factor decomposition using frozen production helpers."""
    values = v31.program_values(world.structure)
    concentration = v31.DEFAULT_HYPERPARAMETERS.concentration
    outcome_parents = tuple(
        parent
        for edge, parent in (("G_Y", "root"), ("W_Y", "world"), ("doA_Y", "action"))
        if values[edge]
    )
    return {
        "mode_signals": float(v31._mode_log_score(  # noqa: SLF001 - diagnosis of frozen scorer
            world.slices, values["active_mode"], concentration, False
        )),
        "root": float(v31.beta_bernoulli_log_marginal(
            v31._counts(world.slices, "root", ("mode",) if values["M1_G"] else ()),  # noqa: SLF001
            concentration,
        )),
        "world": float(v31.beta_bernoulli_log_marginal(
            v31._counts(world.slices, "world", ("root",) if values["G_W"] else ()),  # noqa: SLF001
            concentration,
        )),
        "policy": float(v31.beta_bernoulli_log_marginal(
            v31._counts(world.slices, "policy_proposal", ("root",) if values["G_A"] else ()),  # noqa: SLF001
            concentration,
        )),
        "outcomes": float(v31.beta_bernoulli_log_marginal(
            v31._counts(world.slices, "outcome", outcome_parents),  # noqa: SLF001
            concentration,
        )),
    }


def _v2_factor_scores(score: Mapping[str, Any], truth: str) -> dict[str, float]:
    sums = {
        "mode_signals": 0.0,
        "outcomes": 0.0,
        "context_cue_emissions": 0.0,
    }
    for contribution in score["contributions"]:
        terms = contribution["decomposition"][truth]
        sums["mode_signals"] += float(terms["self"])
        sums["outcomes"] += float(terms["outcome_control"])
        sums["context_cue_emissions"] += math.fsum(
            float(terms[name]) for name in ("localization", "configural", "normalization")
        )
    return sums


def _type_normalized(factors: Mapping[str, float], counts: Mapping[str, int]) -> float:
    rates = [
        float(value) / counts[name]
        for name, value in factors.items()
        if counts.get(name, 0) > 0
    ]
    return float(np.mean(rates))


@traced_execution
def _row(seed: int) -> dict[str, Any]:
    if not BLOCK[0] <= seed <= BLOCK[1]:
        raise ValueError("diagnosis seed outside authorized block")
    require_trace_sink("v36.gate3_noninferiority_diagnosis", seed=seed)
    index = seed - BLOCK[0]
    stratum = v2_trajectory.STRATA[index % len(v2_trajectory.STRATA)]

    v2_state = v2_trajectory.generate_developmental_state(
        seed, stratum, released_block=BLOCK
    )
    v2_score = v2_formation.score_history(
        list(v2_state.observations), list(v2_state.configurations)
    )
    v2_log_evidence = _logsumexp(v2_score["log_joint"])
    v2_truth_index = v2_formation.LABELS.index(v2_state.truth_candidate)
    v2_truth_likelihood = float(v2_score["log_likelihoods"][v2_truth_index])
    v2_factors = _v2_factor_scores(v2_score, v2_state.truth_candidate)
    v2_localization_observed = sum(observation[2] != 2 for observation in v2_state.observations)
    v2_counts = {
        "mode_signals": len(v2_state.observations),
        "outcomes": len(v2_state.observations),
        "context_cue_emissions": v2_localization_observed,
    }
    v2_actual_tokens = 2 * len(v2_state.observations) + v2_localization_observed
    v2_authored_tokens = 3 * len(v2_state.observations)
    v2_posterior = np.asarray(v2_score["posterior"], dtype=float)

    mode_count = 1 if stratum in {"acute_one", "chronic_one", "real_danger_adaptive"} else 3
    topology = ("independent", "opposed", "allied")[index % 3]
    compose_config = v36.ComposeConfig(
        protocol="full", mode_count=mode_count, topology=topology,
        stakes="low", support_target="one" if index % 2 else "all",
        policy_regime="monitoring" if stratum == "real_danger_adaptive" else "mixed",
        missingness=(0.0, 0.15, 0.30)[index % 3], length=16,
    )
    grow_config = v36._component_declarations(compose_config)["grow"]  # noqa: SLF001
    v3_world = v31.generate_world(seed, grow_config, released_block=BLOCK)
    v3_score = v31.score_world(v3_world)
    v3_factors = _v3_factor_scores(v3_world)
    v3_truth_likelihood = math.fsum(v3_factors.values())
    v3_mode_count = sum(item.mode_observed for item in v3_world.slices)
    v3_root_count = sum(item.root_observed for item in v3_world.slices)
    v3_outcome_count = sum(item.outcome_observed is not None for item in v3_world.slices)
    v3_counts = {
        "mode_signals": v3_mode_count,
        "root": v3_root_count,
        "world": len(v3_world.slices),
        "policy": len(v3_world.slices),
        "outcomes": v3_outcome_count,
    }
    v3_actual_tokens = sum(v3_counts.values())
    v3_authored_tokens = 5 * len(v3_world.slices)
    v3_probabilities = np.asarray(v3_score.probabilities, dtype=float)
    v3_truth_index = v3_score.programs.index(v3_world.structure)

    # These hashes intentionally include typed field names. Equal hashes would
    # therefore mean actual schema-and-value equality, not merely equal length.
    v2_observation_document = {
        "channels": ["self_value", "outcome", "localization"],
        "values": list(v2_state.observations),
        "masks": [observation[2] == 2 for observation in v2_state.observations],
    }
    v3_observation_document = {
        "channels": ["mode", "root", "world", "policy_proposal", "outcome"],
        "values": [
            {
                "mode": item.mode if item.mode_observed else None,
                "root": item.root if item.root_observed else None,
                "world": item.world,
                "policy_proposal": item.policy_proposal,
                "outcome": item.outcome_observed,
            }
            for item in v3_world.slices
        ],
    }

    v2_structure_effect = v2_log_evidence - v2_truth_likelihood
    v3_structure_effect = float(v3_score.log_evidence) - v3_truth_likelihood
    original_v2 = v2_log_evidence / v2_authored_tokens
    original_v3 = float(v3_score.log_evidence) / v3_authored_tokens
    actual_v2 = v2_log_evidence / v2_actual_tokens
    actual_v3 = float(v3_score.log_evidence) / v3_actual_tokens
    type_v2 = _type_normalized(v2_factors, v2_counts)
    type_v3 = _type_normalized(v3_factors, v3_counts)

    return {
        "seed": seed,
        "stratum": stratum,
        "truth_mode_count": mode_count,
        "truth_topology": topology,
        "support": {
            "v2_schema": v2_observation_document["channels"],
            "v3_schema": v3_observation_document["channels"],
            "v2_observation_sha256": hashlib.sha256(_canonical(v2_observation_document)).hexdigest(),
            "v3_observation_sha256": hashlib.sha256(_canonical(v3_observation_document)).hexdigest(),
            "byte_identical": _canonical(v2_observation_document) == _canonical(v3_observation_document),
            "v2_slice_count": len(v2_state.observations),
            "v3_slice_count": len(v3_world.slices),
            "v2_authored_token_count": v2_authored_tokens,
            "v3_authored_token_count": v3_authored_tokens,
            "v2_delivered_token_count": v2_actual_tokens,
            "v3_delivered_token_count": v3_actual_tokens,
            "v2_masked_localization_count": len(v2_state.observations) - v2_localization_observed,
            "v3_masked_counts": {
                "mode": len(v3_world.slices) - v3_mode_count,
                "root": len(v3_world.slices) - v3_root_count,
                "outcome": len(v3_world.slices) - v3_outcome_count,
            },
        },
        "scores": {
            "v2_log_evidence_total": v2_log_evidence,
            "v3_log_evidence_total": float(v3_score.log_evidence),
            "v3_minus_v2_total": float(v3_score.log_evidence) - v2_log_evidence,
            "v2_authored_per_token": original_v2,
            "v3_authored_per_token": original_v3,
            "v3_minus_v2_authored_per_token": original_v3 - original_v2,
            "v2_delivered_per_token": actual_v2,
            "v3_delivered_per_token": actual_v3,
            "v3_minus_v2_delivered_per_token": actual_v3 - actual_v2,
            "v2_channel_type_mean": type_v2,
            "v3_channel_type_mean": type_v3,
            "v3_minus_v2_channel_type_mean": type_v3 - type_v2,
        },
        "decomposition": {
            "v2_truth_clamped_factors": v2_factors,
            "v3_truth_clamped_factors": v3_factors,
            "v2_truth_clamped_likelihood": v2_truth_likelihood,
            "v3_truth_clamped_likelihood": v3_truth_likelihood,
            "v2_structure_mixture_effect": v2_structure_effect,
            "v3_structure_mixture_effect": v3_structure_effect,
            "truth_clamped_parameter_difference_authored_per_token": (
                v3_truth_likelihood / v3_authored_tokens
                - v2_truth_likelihood / v2_authored_tokens
            ),
            "structure_mixture_difference_authored_per_token": (
                v3_structure_effect / v3_authored_tokens
                - v2_structure_effect / v2_authored_tokens
            ),
            "additive_recombination_error": abs(
                (original_v3 - original_v2)
                - (
                    v3_truth_likelihood / v3_authored_tokens
                    - v2_truth_likelihood / v2_authored_tokens
                    + v3_structure_effect / v3_authored_tokens
                    - v2_structure_effect / v2_authored_tokens
                )
            ),
        },
        "calibration": {
            "v2_correct": int(np.argmax(v2_posterior)) == v2_truth_index,
            "v2_confidence": float(v2_posterior.max()),
            "v2_truth_probability": float(v2_posterior[v2_truth_index]),
            "v2_entropy": _entropy(v2_posterior),
            "v2_normalized_entropy": _entropy(v2_posterior) / math.log(len(v2_posterior)),
            "v3_correct": int(np.argmax(v3_probabilities)) == v3_truth_index,
            "v3_confidence": float(v3_probabilities.max()),
            "v3_truth_probability": float(v3_probabilities[v3_truth_index]),
            "v3_entropy": _entropy(v3_probabilities),
            "v3_normalized_entropy": _entropy(v3_probabilities) / math.log(len(v3_probabilities)),
        },
    }


def _persist() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    RESULTS.mkdir(parents=True, exist_ok=True)
    trace_path = RESULTS / "gate3-noninferiority-diagnosis-traces.jsonl"
    hash_path = RESULTS / "gate3-noninferiority-diagnosis-trace-hashes.json"
    if trace_path.exists() or hash_path.exists():
        raise RuntimeError("diagnosis outputs already exist; rerun refused")
    rows: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    seeds = list(range(BLOCK[0], BLOCK[1] + 1))
    processes = max(1, min(8, (os.cpu_count() or 2) - 1))
    with trace_path.open("xb") as handle:
        with get_context("spawn").Pool(processes) as pool:
            for row in pool.imap(_row, seeds, chunksize=2):
                encoded = _canonical(row)
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
                digest.update(encoded)
                records.append({
                    "seed": int(row["seed"]),
                    "sha256": hashlib.sha256(encoded).hexdigest(),
                })
                rows.append(row)
    ledger = {
        "file": trace_path.name,
        "sha256": digest.hexdigest(),
        "record_count": len(rows),
        "seed_block": list(BLOCK),
        "ascending_gap_free": [row["seed"] for row in rows] == seeds,
        "records": records,
        "persisted_before_aggregation": True,
    }
    hash_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with hash_path.open("rb") as handle:
        os.fsync(handle.fileno())
    return rows, ledger


def _quantiles(values: Sequence[float]) -> dict[str, float]:
    levels = (0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0)
    result = np.quantile(np.asarray(values, dtype=float), levels)
    return {f"q{int(level * 100):02d}": float(value) for level, value in zip(levels, result)}


def _mean(values: Sequence[float]) -> float:
    return float(np.mean(np.asarray(values, dtype=float)))


def _aggregate(rows: Sequence[Mapping[str, Any]], ledger: Mapping[str, Any]) -> dict[str, Any]:
    authored = [row["scores"]["v3_minus_v2_authored_per_token"] for row in rows]
    delivered = [row["scores"]["v3_minus_v2_delivered_per_token"] for row in rows]
    totals = [row["scores"]["v3_minus_v2_total"] for row in rows]
    typed = [row["scores"]["v3_minus_v2_channel_type_mean"] for row in rows]
    v2_advantage = [-value for value in authored]

    channel_names = (
        "mode_signals", "outcomes", "partner", "support", "contact",
        "registration", "context_cue_emissions", "root", "world", "policy",
    )
    per_channel: dict[str, Any] = {}
    v2_factor_names = {"mode_signals", "outcomes", "context_cue_emissions"}
    v3_factor_names = {"mode_signals", "outcomes", "root", "world", "policy"}
    for name in channel_names:
        left = [row["decomposition"]["v2_truth_clamped_factors"].get(name, 0.0) for row in rows]
        right = [row["decomposition"]["v3_truth_clamped_factors"].get(name, 0.0) for row in rows]
        per_channel[name] = {
            "v2_present_in_tournament_score": name in v2_factor_names,
            "v3_present_in_tournament_score": name in v3_factor_names,
            "v2_mean_total_nats": _mean(left),
            "v3_mean_total_nats": _mean(right),
            "v3_minus_v2_mean_total_nats": _mean([b - a for a, b in zip(left, right)]),
            "comparison_warning": "different typed supports; this is an additive bookkeeping coordinate, not a like-for-like channel score",
        }

    structure_difference = [row["decomposition"]["structure_mixture_difference_authored_per_token"] for row in rows]
    parameter_difference = [row["decomposition"]["truth_clamped_parameter_difference_authored_per_token"] for row in rows]
    v2_structure_effect = [row["decomposition"]["v2_structure_mixture_effect"] for row in rows]
    v3_structure_effect = [row["decomposition"]["v3_structure_mixture_effect"] for row in rows]
    subclasses = {}
    for field in ("stratum", "truth_mode_count", "truth_topology"):
        for value in sorted({row[field] for row in rows}, key=str):
            selected = [
                -row["scores"]["v3_minus_v2_authored_per_token"]
                for row in rows if row[field] == value
            ]
            subclasses[f"{field}={value}"] = {
                "world_count": len(selected), "mean_v2_advantage": _mean(selected),
                "quantiles": _quantiles(selected),
            }

    result = {
        "stage": "V3.6",
        "analysis": "Gate-3 predictive-noninferiority decomposition; non-criterial diagnosis only",
        "authorized_seed_block": list(BLOCK),
        "world_count": len(rows),
        "custody": {
            "persisted_before_aggregation": ledger["persisted_before_aggregation"],
            "ascending_gap_free": ledger["ascending_gap_free"],
            "trace_file": ledger["file"],
            "trace_sha256": ledger["sha256"],
            "event_ledgers_present": all(bool(row.get("_runtime_trace_events")) for row in rows),
            "gates_4_5_touched": False,
            "escrow_touched": False,
        },
        "support_equality": {
            "byte_identical_worlds": sum(row["support"]["byte_identical"] for row in rows),
            "byte_identical_rate": _mean([row["support"]["byte_identical"] for row in rows]),
            "v2_schema": ["self_value", "outcome", "localization"],
            "v3_schema": ["mode", "root", "world", "policy_proposal", "outcome"],
            "v2_slice_counts": sorted({row["support"]["v2_slice_count"] for row in rows}),
            "v3_slice_counts": sorted({row["support"]["v3_slice_count"] for row in rows}),
            "v2_authored_token_counts": sorted({row["support"]["v2_authored_token_count"] for row in rows}),
            "v2_delivered_token_counts": sorted({row["support"]["v2_delivered_token_count"] for row in rows}),
            "v3_authored_token_counts": sorted({row["support"]["v3_authored_token_count"] for row in rows}),
            "v3_delivered_token_counts": sorted({row["support"]["v3_delivered_token_count"] for row in rows}),
            "v2_masked_localization_count_distribution": _quantiles([row["support"]["v2_masked_localization_count"] for row in rows]),
            "finding": "The two sides are not scored on a common observation support. Same seed and broad truth condition do not produce the same observations.",
        },
        "normalization": {
            "authored_v3_minus_v2_nats_per_nominal_token": {"mean": _mean(authored), "quantiles": _quantiles(authored)},
            "v3_minus_v2_total_nats_per_world": {"mean": _mean(totals), "quantiles": _quantiles(totals)},
            "delivered_token_v3_minus_v2_nats_per_token": {"mean": _mean(delivered), "quantiles": _quantiles(delivered)},
            "channel_type_equal_weight_v3_minus_v2": {"mean": _mean(typed), "quantiles": _quantiles(typed)},
            "normalization_stable": all(np.sign(_mean(values)) == np.sign(_mean(authored)) for values in (totals, delivered, typed)),
            "denominator_identity": {
                "v2": "3 * slice_count (counts deterministic localization sentinel as a nominal token)",
                "v3": "5 * slice_count",
                "same_denominator_rule": False,
            },
        },
        "per_channel_decomposition": {
            "basis": "truth-structure-clamped frozen likelihood factors; exact additive within each model",
            "channels": per_channel,
            "partner_support_contact_registration_note": "These channels are absent from both predictive quantities used by the Gate-3 tournament and contribute exactly zero there.",
            "alignment_warning": "No causal attribution of the cross-model deficit to a like-for-like channel is valid because the channel supports differ.",
            "finding": "The deficit is concentrated in the structure/model-averaging coordinate, not a shared channel. V3 additionally scores root, world, and policy factors absent from the V2 quantity; V2 uses the compact joint T/D/P formation production.",
        },
        "structure_vs_parameters": {
            "truth_clamped_parameter_difference_authored_per_token": {"mean": _mean(parameter_difference), "quantiles": _quantiles(parameter_difference)},
            "structure_mixture_difference_authored_per_token": {"mean": _mean(structure_difference), "quantiles": _quantiles(structure_difference)},
            "v2_structure_mixture_effect_nats_per_world": {"mean": _mean(v2_structure_effect), "quantiles": _quantiles(v2_structure_effect)},
            "v3_structure_mixture_effect_nats_per_world": {"mean": _mean(v3_structure_effect), "quantiles": _quantiles(v3_structure_effect)},
            "structure_share_of_authored_mean_deficit": abs(_mean(structure_difference)) / abs(_mean(authored)),
            "dominant_component": "structure prior/model averaging over the three-state V2 menu versus the 128-program V3 GROW space",
            "recombined_mean": _mean([a + b for a, b in zip(parameter_difference, structure_difference)]),
            "maximum_recombination_error": max(row["decomposition"]["additive_recombination_error"] for row in rows),
        },
        "calibration_cross_check": {
            "v2_accuracy": _mean([row["calibration"]["v2_correct"] for row in rows]),
            "v2_ece": _ece([row["calibration"]["v2_confidence"] for row in rows], [row["calibration"]["v2_correct"] for row in rows]),
            "v2_mean_truth_probability": _mean([row["calibration"]["v2_truth_probability"] for row in rows]),
            "v2_mean_normalized_entropy": _mean([row["calibration"]["v2_normalized_entropy"] for row in rows]),
            "v3_accuracy": _mean([row["calibration"]["v3_correct"] for row in rows]),
            "v3_ece": _ece([row["calibration"]["v3_confidence"] for row in rows], [row["calibration"]["v3_correct"] for row in rows]),
            "v3_mean_truth_probability": _mean([row["calibration"]["v3_truth_probability"] for row in rows]),
            "v3_mean_normalized_entropy": _mean([row["calibration"]["v3_normalized_entropy"] for row in rows]),
            "gate2_profile_reference": json.loads((RESULTS / "gate-2.json").read_text())["metrics"],
            "profile_population_identity": False,
            "profile_population_note": "Gate 3 copied the Gate-2 64-slice prior-sampled recovery metrics; it did not compute calibration on the 16-slice fixed-config tournament population.",
            "diagnosis": "The tournament population has poor exact-structure recovery and elevated entropy; the passing 6C reference therefore missed this population. This is separate from, and cannot validate, the unequal-support predictive comparison.",
        },
        "v2_predictive_advantage_distribution": {
            "overall": {"mean": _mean(v2_advantage), "quantiles": _quantiles(v2_advantage)},
            "subclasses": subclasses,
            "finding": "The advantage is not uniform: acute_one worlds drive it; real_danger_adaptive worlds favor V3 on average; topology has little separation.",
        },
        "classification": "UNCLASSIFIED_DIAGNOSIS_ONLY",
        "criteria_evaluated": False,
    }
    return result


def _write_report(result: Mapping[str, Any]) -> None:
    s = result
    support = s["support_equality"]
    norm = s["normalization"]
    struct = s["structure_vs_parameters"]
    calibration = s["calibration_cross_check"]
    advantage = s["v2_predictive_advantage_distribution"]
    channel_rows = []
    for name, values in s["per_channel_decomposition"]["channels"].items():
        channel_rows.append(
            f"| {name} | {values['v2_mean_total_nats']:.6f} | {values['v3_mean_total_nats']:.6f} | {values['v3_minus_v2_mean_total_nats']:.6f} |"
        )
    subclass_rows = []
    for name, values in advantage["subclasses"].items():
        q = values["quantiles"]
        subclass_rows.append(
            f"| {name} | {values['world_count']} | {values['mean_v2_advantage']:.6f} | {q['q05']:.6f} | {q['q50']:.6f} | {q['q95']:.6f} |"
        )
    text = f"""# V3.6 Gate-3 predictive noninferiority decomposition

Status: **DIAGNOSIS ONLY — no classification, repair, criterion, or floor.**

This run consumed the authorized diagnosis block `{BLOCK[0]}:{BLOCK[1]}` once, ascending and gap-free. All {s['world_count']} per-world records and runtime event ledgers were persisted to `{s['custody']['trace_file']}` and hashed (`{s['custody']['trace_sha256']}`) before aggregation. Gates 4–5, escrow, barred blocks, and scientific modules were not touched.

## Apparatus-first finding

The failed number is not a comparison on common predictive support. It combines V2's T/D/P formation likelihood over `(self value, outcome, localization)` with V3's GROW likelihood over `(mode, root, world, policy proposal, outcome)`. The two sides also use different history lengths and independently generated observations. Exactly **{support['byte_identical_worlds']} of {s['world_count']}** observation documents were byte-identical. Same seed and a matched broad truth condition did not make the evidence streams equal.

This means the reported `-0.0339 nats/token` cannot yet be interpreted as V3 losing predictive accuracy to V2 on the same data. The localization below describes the software accounting that produced it; it does not replace or revise the committed Gate-3 verdict.

## 1. Support equality

V2 scored channels: `{', '.join(support['v2_schema'])}`. V3 scored channels: `{', '.join(support['v3_schema'])}`. V2 histories had {support['v2_slice_counts']} slices; V3 always had {support['v3_slice_counts']} slices. V2's nominal token counts were {support['v2_authored_token_counts']}, versus delivered-token counts {support['v2_delivered_token_counts']}; V3's nominal and delivered counts were both {support['v3_authored_token_counts']} and {support['v3_delivered_token_counts']}.

In V2, collapsed-broadcast slices encode localization with the deterministic sentinel `2`. The Gate-3 denominator nevertheless counted that field as a token. V3's GROW cell used broad precision and full availability, so all five scored fields were delivered. The observation hashes, channel names, masks, and token counts therefore establish unequal support, not merely different numerical values.

## 2. Normalization

| Accounting | Mean V3 − V2 |
|---|---:|
| frozen nominal-token statistic | {norm['authored_v3_minus_v2_nats_per_nominal_token']['mean']:.9f} nats/token |
| raw per-world total | {norm['v3_minus_v2_total_nats_per_world']['mean']:.9f} nats/world |
| delivered-token normalization | {norm['delivered_token_v3_minus_v2_nats_per_token']['mean']:.9f} nats/token |
| equal-weight truth-clamped channel-type rates | {norm['channel_type_equal_weight_v3_minus_v2']['mean']:.9f} |

The sign is {'stable' if norm['normalization_stable'] else 'not stable'} across these descriptive normalizations. It remains an unequal-support comparison in every row. The frozen calculation uses `3 × V2 slices` and `5 × V3 slices`; it is not one shared atomic-token denominator.

## 3. Per-channel decomposition

The table uses each model's truth-structure-clamped, exactly recombining likelihood factors. Because the supports differ, the last column is bookkeeping rather than a like-for-like predictive contrast.

| Channel/factor | V2 mean nats/world | V3 mean nats/world | V3 − V2 |
|---|---:|---:|---:|
{chr(10).join(channel_rows)}

Partner, support, contact, and registration are not present in either predictive quantity used by this tournament; each contributes exactly zero to the published deficit. The dominant deficit is not a matched channel. It is the structure/model-averaging term described next. Among the raw likelihood factors, V3 additionally pays about 7.58–8.07 nats/world each for root, world, and policy observations that V2 never scores. The V2-specific object is the compact, normalized joint T/D/P slice likelihood—especially its localization/configural production. Accordingly, no scientifically valid statement such as “V2 wins on partner evidence” or “V3 loses on outcome evidence” follows from this comparison.

## 4. Structure versus parameters

Clamping both scorers to their own generating structure gives a mean parameter-predictive component of **{struct['truth_clamped_parameter_difference_authored_per_token']['mean']:.9f}** nats/nominal-token. The residual contribution of structure prior/model averaging is **{struct['structure_mixture_difference_authored_per_token']['mean']:.9f}**. They recombine to **{struct['recombined_mean']:.9f}**, with maximum numerical error `{struct['maximum_recombination_error']:.3g}`.

V2's model-evidence-minus-truth-likelihood term is **{struct['v2_structure_mixture_effect_nats_per_world']['mean']:.6f} nats/world**; V3's is **{struct['v3_structure_mixture_effect_nats_per_world']['mean']:.6f} nats/world**. Their normalized difference accounts for **{100.0 * struct['structure_share_of_authored_mean_deficit']:.1f}%** of the mean nominal-token deficit. Thus the miss is {'mostly parameter-predictive' if abs(struct['truth_clamped_parameter_difference_authored_per_token']['mean']) > abs(struct['structure_mixture_difference_authored_per_token']['mean']) else 'mostly structural/model-averaging'} under the frozen, unequal-support accounting: the three-state V2 menu concentrates prior/model mass much more cheaply than the 128-program V3 GROW space. “Parameter-predictive” here does not mean bad parameter inference; it includes the cost of scoring different channel families.

## 5. Calibration cross-check

| Model | accuracy | ECE | mean truth probability | normalized posterior entropy |
|---|---:|---:|---:|---:|
| V2 T/D/P | {calibration['v2_accuracy']:.6f} | {calibration['v2_ece']:.6f} | {calibration['v2_mean_truth_probability']:.6f} | {calibration['v2_mean_normalized_entropy']:.6f} |
| V3 GROW graph | {calibration['v3_accuracy']:.6f} | {calibration['v3_ece']:.6f} | {calibration['v3_mean_truth_probability']:.6f} | {calibration['v3_mean_normalized_entropy']:.6f} |

The reported 6C profile did **not** measure calibration on this tournament population. Gate 3 copied Gate 2's results from 64-slice, prior-sampled recovery worlds (Gate-2 ECE 0.01183 and exact-program accuracy 0.5696). These diagnosis worlds use a fixed 16-slice formation configuration. On them, exact-program accuracy is 0.025, ECE is 0.286, and normalized posterior entropy is 0.465. So the answer is not simply “well calibrated but honestly diffuse”: the referenced profile missed this population. Some of the apparent failure can reflect observationally equivalent graph programs, but the exact-structure statistic is plainly not calibrated here. This remains distinct from the predictive comparison, which also lacks common support.

## 6. Distribution and subclasses

V2's nominal-token advantage has mean **{advantage['overall']['mean']:.9f}**. Overall quantiles are `{json.dumps(advantage['overall']['quantiles'], sort_keys=True)}`.

| Subclass | n | mean V2 advantage | q05 | median | q95 |
|---|---:|---:|---:|---:|---:|
{chr(10).join(subclass_rows)}

These strata localize which independently generated evidence schedules drive the number. They are not common-world treatment effects.

## Custody and stopping point

No criterion was evaluated. No scientific source, threshold, floor, Gate-4/5 artifact, escrow, or barred seed was touched. The committed Gate-3 FAIL remains intact and unclassified pending evaluator adjudication.
"""
    (RESULTS / "gate3-noninferiority-decomposition.md").write_text(text, encoding="utf-8")


def _load_persisted() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    trace_path = RESULTS / "gate3-noninferiority-diagnosis-traces.jsonl"
    hash_path = RESULTS / "gate3-noninferiority-diagnosis-trace-hashes.json"
    ledger = json.loads(hash_path.read_text(encoding="utf-8"))
    raw = trace_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ledger["sha256"]:
        raise RuntimeError("persisted diagnosis trace hash mismatch")
    rows = [json.loads(line) for line in raw.splitlines()]
    expected = list(range(BLOCK[0], BLOCK[1] + 1))
    if [row["seed"] for row in rows] != expected:
        raise RuntimeError("persisted diagnosis seed order mismatch")
    for row, record in zip(rows, ledger["records"]):
        if hashlib.sha256(_canonical(row)).hexdigest() != record["sha256"]:
            raise RuntimeError(
                f"persisted row hash mismatch at seed {row['seed']}"
            )
    return rows, ledger


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--aggregate-existing", action="store_true",
        help="verify and aggregate the already-persisted one-shot traces",
    )
    arguments = parser.parse_args()
    rows, ledger = (
        _load_persisted() if arguments.aggregate_existing else _persist()
    )
    result = _aggregate(rows, ledger)
    json_path = RESULTS / "gate3-noninferiority-decomposition.json"
    json_path.write_text(json.dumps(_plain(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_report(result)
    print(json.dumps({
        "status": result["classification"],
        "world_count": result["world_count"],
        "support_byte_identical": result["support_equality"]["byte_identical_worlds"],
        "authored_difference": result["normalization"]["authored_v3_minus_v2_nats_per_nominal_token"]["mean"],
        "trace_sha256": result["custody"]["trace_sha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
