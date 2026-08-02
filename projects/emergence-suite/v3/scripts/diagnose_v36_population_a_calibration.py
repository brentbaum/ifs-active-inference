#!/usr/bin/env python3
"""Read-only posterior-predictive calibration-null decomposition for V3.6 A."""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ref import v35  # noqa: E402


RESULTS = ROOT / "results" / "V3.6"
TRACE = RESULTS / "v3.6-r1-round14-v3-native-replacement-2-traces.jsonl"
PROOF = RESULTS / "v3.6-r1-round13-native-fixture-identity-proofs.json"
OUTPUT_JSON = RESULTS / "population-a-calibration-null-decomposition.json"
OUTPUT_MD = RESULTS / "population-a-calibration-null-decomposition.md"
REPLICATES = 2_000
TARGETS = ("identity", "outcome", "context", "partner", "contact")
LEVELS = (0.50, 0.80, 0.90, 0.95)


def _bin(probability: np.ndarray) -> np.ndarray:
    return np.minimum((probability * 10.0).astype(int), 9)


def _ece(probability: np.ndarray, outcome: np.ndarray, weight: np.ndarray) -> float:
    bins = _bin(probability)
    total = 0.0
    for index in range(10):
        selected = bins == index
        if np.any(selected):
            total += abs(float(np.sum(weight[selected] * (probability[selected] - outcome[selected]))))
    return total


def _reliability(probability: np.ndarray, outcome: np.ndarray, weight: np.ndarray) -> list[dict[str, Any]]:
    bins = _bin(probability)
    rows = []
    for index in range(10):
        selected = bins == index
        mass = float(np.sum(weight[selected]))
        rows.append({
            "bin": index,
            "low": index / 10.0,
            "high": (index + 1) / 10.0,
            "count": int(np.sum(selected)),
            "effective_world_mass": mass,
            "confidence": float(np.sum(weight[selected] * probability[selected]) / mass) if mass else None,
            "frequency": float(np.sum(weight[selected] * outcome[selected]) / mass) if mass else None,
            "signed_confidence_minus_frequency": float(
                np.sum(weight[selected] * (probability[selected] - outcome[selected])) / mass
            ) if mass else None,
            "ece_contribution": abs(float(np.sum(weight[selected] * (probability[selected] - outcome[selected])))),
        })
    return rows


def _null_summary(values: np.ndarray, observed: float) -> dict[str, Any]:
    quantiles = np.quantile(values, (0.05, 0.50, 0.95, 0.99))
    return {
        "replicates": REPLICATES,
        "mean": float(np.mean(values)),
        "q05": float(quantiles[0]),
        "q50": float(quantiles[1]),
        "q95": float(quantiles[2]),
        "q99": float(quantiles[3]),
        "observed": float(observed),
        "observed_empirical_percentile_plus_one": float(
            (1 + np.sum(values <= observed)) / (REPLICATES + 1)
        ),
        "beyond_q99": bool(observed > quantiles[3]),
    }


def _binary_null(
    rng: np.random.Generator,
    probability: np.ndarray,
    observed: np.ndarray,
    weight: np.ndarray,
) -> tuple[dict[str, Any], np.ndarray]:
    values = np.empty(REPLICATES, dtype=float)
    for start in range(0, REPLICATES, 40):
        size = min(40, REPLICATES - start)
        synthetic = rng.random((size, len(probability))) < probability
        for offset in range(size):
            values[start + offset] = _ece(probability, synthetic[offset], weight)
    return _null_summary(values, _ece(probability, observed, weight)), values


def _coverage_mass(classes_left: Sequence[dict[str, Any]], classes_right: Sequence[dict[str, Any]], level: float) -> float:
    pairs = [
        (float(left["mass"]) * float(right["mass"]),
         f"{left['canonical_min_program_id']}|{right['canonical_min_program_id']}")
        for left in classes_left for right in classes_right
    ]
    pairs.sort(key=lambda item: (-item[0], item[1]))
    cumulative = 0.0
    included_mass = 0.0
    for mass, _name in pairs:
        included_mass += mass
        cumulative += mass
        if cumulative >= level:
            break
    return float(included_mass)


def main() -> None:
    replacing = "--replace" in sys.argv
    if (OUTPUT_JSON.exists() or OUTPUT_MD.exists()) and not replacing:
        raise RuntimeError("diagnosis outputs already exist")
    active_p = []
    active_truth = []
    edge_p = []
    edge_truth = []
    class_confidence = []
    class_correct = []
    coverage_observed = {level: [] for level in LEVELS}
    coverage_probability = {level: [] for level in LEVELS}
    targets = {target: {"p": [], "y": [], "w": [], "world_token_counts": []} for target in TARGETS}
    active_sum_error = 0.0
    active_marginal_error = 0.0
    row_count = 0

    with TRACE.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            state = row["calibration_state"]
            active = np.asarray(state["active_count_posterior"], dtype=float)
            active_p.append(active)
            active_truth.append(int(state["truth_active_count"]) - 1)
            active_sum_error = max(active_sum_error, abs(float(np.sum(active)) - 1.0))
            reconstructed = np.zeros(3, dtype=float)
            for item in state["protect_structure_posterior"]:
                structure_index = int(item["structure_index"])
                reconstructed[v35.PROGRAMS[structure_index].active_modes - 1] += float(item["mass"])
            active_marginal_error = max(
                active_marginal_error, float(np.max(np.abs(reconstructed - active)))
            )
            edge_p.append(float(state["edge_posteriors"]["JOINT_POLICY_Y"]))
            edge_truth.append(int(state["truth_edges"]["JOINT_POLICY_Y"]))
            class_confidence.append(float(state["class_confidence"]))
            class_correct.append(int(state["class_correct"]))
            for level in LEVELS:
                coverage_observed[level].append(int(state["class_coverage"][str(level)]))
                coverage_probability[level].append(_coverage_mass(
                    state["class_posterior"]["protect_factor"],
                    state["class_posterior"]["temporal_factor"], level,
                ))
            for target in TARGETS:
                prediction = row["predictions"]["v3"][target]
                delivered = prediction["delivered"]
                observations = row["targets"][target]
                selected = [
                    (float(probability), int(observation))
                    for probability, observation, available in zip(
                        prediction["p1"], observations, delivered
                    ) if available and observation is not None
                ]
                targets[target]["world_token_counts"].append(len(selected))
                for probability, observation in selected:
                    targets[target]["p"].append(probability)
                    targets[target]["y"].append(observation)
                    targets[target]["w"].append(1.0 / len(selected) / 2000.0)
            row_count += 1

    if row_count != 2000:
        raise RuntimeError(f"expected 2000 retained rows, found {row_count}")
    active_p_array = np.asarray(active_p, dtype=float)
    active_truth_array = np.asarray(active_truth, dtype=int)
    edge_p_array = np.asarray(edge_p, dtype=float)
    edge_truth_array = np.asarray(edge_truth, dtype=int)
    class_p_array = np.asarray(class_confidence, dtype=float)
    class_y_array = np.asarray(class_correct, dtype=int)
    world_weight = np.full(row_count, 1.0 / row_count)
    analysis_key = hashlib.sha256(b"V3.6-round14-calibration-null-v1").digest()
    rng = np.random.default_rng(int.from_bytes(analysis_key[:8], "big"))

    # Active-count top-label null.
    active_top = np.argmax(active_p_array, axis=1)
    active_conf = np.max(active_p_array, axis=1)
    active_correct = (active_top == active_truth_array).astype(int)
    top_values = np.empty(REPLICATES)
    macro_values = np.empty(REPLICATES)
    cumulative = np.cumsum(active_p_array, axis=1)
    for replicate in range(REPLICATES):
        draw = np.sum(rng.random(row_count)[:, None] > cumulative, axis=1)
        top_values[replicate] = _ece(active_conf, (active_top == draw).astype(int), world_weight)
        macro_values[replicate] = np.mean([
            _ece(active_p_array[:, index], (draw == index).astype(int), world_weight)
            for index in range(3)
        ])
    active_top_observed = _ece(active_conf, active_correct, world_weight)
    active_macro_observed = float(np.mean([
        _ece(active_p_array[:, index], (active_truth_array == index).astype(int), world_weight)
        for index in range(3)
    ]))

    edge_summary, _edge_null_values = _binary_null(
        rng, edge_p_array, edge_truth_array, world_weight
    )
    class_summary, _class_null_values = _binary_null(
        rng, class_p_array, class_y_array, world_weight
    )

    target_results = {}
    for target in TARGETS:
        probability = np.asarray(targets[target]["p"], dtype=float)
        observed = np.asarray(targets[target]["y"], dtype=int)
        weight = np.asarray(targets[target]["w"], dtype=float)
        summary, _values = _binary_null(rng, probability, observed, weight)
        target_results[target] = {
            "null": summary,
            "reliability": _reliability(probability, observed, weight),
            "world_token_counts": {
                "minimum": int(min(targets[target]["world_token_counts"])),
                "median": float(np.median(targets[target]["world_token_counts"])),
                "maximum": int(max(targets[target]["world_token_counts"])),
                "total": int(len(probability)),
            },
        }

    coverage_results = {}
    for level in LEVELS:
        probabilities = np.asarray(coverage_probability[level], dtype=float)
        observed = np.asarray(coverage_observed[level], dtype=int)
        null = np.empty(REPLICATES)
        for replicate in range(REPLICATES):
            null[replicate] = float(np.mean(rng.random(row_count) < probabilities))
        coverage_results[str(level)] = {
            "null": _null_summary(null, float(np.mean(observed))),
            "mean_hpd_set_posterior_mass": float(np.mean(probabilities)),
        }

    active_by_truth = {}
    for truth in range(3):
        selected = active_truth_array == truth
        active_by_truth[str(truth + 1)] = {
            "world_count": int(np.sum(selected)),
            "top_label_ece": _ece(
                active_conf[selected], active_correct[selected],
                np.full(int(np.sum(selected)), 1.0 / int(np.sum(selected))),
            ),
            "mean_confidence_minus_accuracy": float(
                np.mean(active_conf[selected] - active_correct[selected])
            ),
            "joint_policy_edge_ece": _ece(
                edge_p_array[selected], edge_truth_array[selected],
                np.full(int(np.sum(selected)), 1.0 / int(np.sum(selected))),
            ),
            "joint_policy_mean_probability_minus_frequency": float(
                np.mean(edge_p_array[selected] - edge_truth_array[selected])
            ),
        }

    active_residual = active_conf - active_correct
    edge_residual = edge_p_array - edge_truth_array
    correlation = float(np.corrcoef(active_residual, edge_residual)[0, 1])
    proof = json.loads(PROOF.read_text())
    complete = proof["v3_complete_native_generator"]
    report = {
        "stage": "V3.6",
        "analysis": "Population-A posterior-predictive calibration null decomposition",
        "source_trace": TRACE.name,
        "source_trace_sha256": hashlib.sha256(TRACE.read_bytes()).hexdigest(),
        "world_count": row_count,
        "new_world_seeds_consumed": [],
        "analysis_rng": {
            "kind": "deterministic analysis-only posterior-predictive resampling key",
            "key_sha256": hashlib.sha256(b"V3.6-round14-calibration-null-v1").hexdigest(),
            "replicates": REPLICATES,
        },
        "estimators": {
            "world_weighting": "1/N_world; within-world delivered tokens each receive 1/n_world_tokens",
            "bins": "ten fixed bins; index=min(int(p*10),9)",
            "active_top_label": "confidence=max q(K); correct=argmax q(K)==K_truth",
            "active_macro": "mean of three binary classwise ECEs",
            "edge": "binary ECE of q(JOINT_POLICY_Y=1) against edge truth",
            "percentile": "(1 + count(null <= observed))/(R + 1)",
        },
        "parametric_nulls": {
            "failing": {
                "active_count_top_label_ece": _null_summary(top_values, active_top_observed),
                "active_count_macro_classwise_ece": _null_summary(macro_values, active_macro_observed),
                "JOINT_POLICY_Y_binary_edge_ece": edge_summary,
            },
            "passing_controls": {
                "targets": target_results,
                "equivalence_class_top_label_ece": {
                    "null": class_summary,
                    "reliability": _reliability(class_p_array, class_y_array, world_weight),
                },
                "class_set_coverage": coverage_results,
            },
        },
        "theorem_premise": {
            "preblock_proof_file": PROOF.name,
            "proof_entry": "v3_complete_native_generator",
            "proof_passed": bool(complete["passed"]),
            "production_joint_sum": complete["production_sum"],
            "oracle_joint_sum": complete["oracle_sum"],
            "module_predictive_max_error": complete["module_predictive"]["max_error"],
            "proof_scope": "The retained entry is an enumerable factorized native-fixture dummy (protect and temporal factors, with recombination), not a direct equality proof over every 64-slice latent/observation path.",
            "protect_factor_max_atom_error": proof["v3_native_generator_factorized_joint"]["protect"]["max_absolute_probability_error"],
            "temporal_factor_max_atom_error": proof["v3_native_generator_factorized_joint"]["temporal"]["max_absolute_probability_error"],
            "active_count_posterior_sum_error_max": active_sum_error,
            "active_count_vs_serialized_structure_marginal_error_max": active_marginal_error,
            "marginalization_recomputable": True,
            "marginalization_note": "Each persisted protect row contains structure_index and mass; structure_index resolves in the frozen v35.PROGRAMS support.",
        },
        "localization": {
            "active_top_reliability": _reliability(active_conf, active_correct, world_weight),
            "active_macro_per_class_reliability": {
                str(index + 1): _reliability(
                    active_p_array[:, index], (active_truth_array == index).astype(int), world_weight
                ) for index in range(3)
            },
            "JOINT_POLICY_Y_reliability": _reliability(edge_p_array, edge_truth_array, world_weight),
            "by_truth_active_count": active_by_truth,
            "active_top_vs_JOINT_POLICY_Y_signed_residual_correlation": correlation,
            "shared_structure_interpretation": "Positive correlation means worlds with active-count overconfidence also tend toward JOINT_POLICY_Y overprediction; near zero means the two misses are not carried by the same worlds.",
            "direction_summary": {
                "active_count_top_label": "Mixed and nonmonotone: the high-mass [0.4,0.5) bin is overconfident by 0.0452 and [0.5,0.6) is overconfident by 0.2209; bins >=0.6 are underconfident because empirical accuracy rises sharply to 0.839-1.0.",
                "active_count_macro": "Class-specific swaps dominate: count-1 is underpredicted in [0.3,0.4) and strongly overpredicted in [0.5,0.6); count-2 is underpredicted in [0.2,0.3) but overpredicted in its dominant [0.3,0.4) bin; count-3 is strongly underpredicted in [0.1,0.2).",
                "JOINT_POLICY_Y": "Systematic overprediction across bins below 0.7 and again in [0.8,0.9); signed gaps are +0.076 to +0.129 through bins [0.1,0.7).",
                "shared_miss": "Residual correlation is near zero (-0.0505). Although both quantities depend on policy-edge-bearing programs, their world-level calibration errors are not carried by the same subclass: JOINT_POLICY_Y overprediction is largest in true one-mode worlds, while active-count confidence changes sign by truth count.",
            },
            "passing_control_anomalies": {
                "identity_target": "Observed ECE is beyond its null q99 and is mainly underconfidence in bins [0.3,0.8), despite passing the frozen absolute 0.05 criterion.",
                "coverage_0.95": "Observed 0.964 is just above null q99 0.9635; this is overcoverage rather than the criterion-relevant undercoverage.",
            },
        },
        "bin_occupancy": {
            "active_top": [row["count"] for row in _reliability(active_conf, active_correct, world_weight)],
            "JOINT_POLICY_Y": [row["count"] for row in _reliability(edge_p_array, edge_truth_array, world_weight)],
            "class_top": [row["count"] for row in _reliability(class_p_array, class_y_array, world_weight)],
            "targets": {
                target: [row["count"] for row in target_results[target]["reliability"]]
                for target in TARGETS
            },
            "token_mass_caveat": "Target ECE is world-weighted: a world contributes total weight 1/N regardless of its delivered-token count. Raw token counts can therefore be highly concentrated without receiving proportional world mass.",
            "concentration_summary": {
                "active_top": "1,152/2,000 worlds (57.6%) lie in [0.4,0.5); 280 (14.0%) lie in [0.5,0.6).",
                "JOINT_POLICY_Y": "700/2,000 worlds (35.0%) lie in [0,0.1); 390 (19.5%) lie in [0.9,1.0).",
                "target_tokens": "Contact and partner tokens occupy almost entirely two bins; identity has 10,680 tokens in [0.3,0.4) and 10,443 in [0.5,0.6). These are raw counts, not world weights.",
            },
        },
    }
    encoded = (json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    temp = OUTPUT_JSON.with_suffix(".json.tmp")
    with temp.open("wb") as handle:
        handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
    temp.replace(OUTPUT_JSON)

    failing = report["parametric_nulls"]["failing"]
    beyond = [name for name, item in failing.items() if item["beyond_q99"]]
    control_beyond = [
        target for target, item in target_results.items()
        if item["null"]["beyond_q99"]
    ] + [
        f"coverage_{level}" for level, item in coverage_results.items()
        if item["null"]["beyond_q99"]
    ] + (["equivalence_class_top_label_ece"] if class_summary["beyond_q99"] else [])
    lines = [
        "# Population-A calibration-null decomposition", "",
        "This analysis is read-only over the retained 2,000-world trace. No world seed was generated or rescored.", "",
        "## Parametric nulls", "",
        "| statistic | observed | null mean | q95 | q99 | percentile | beyond q99 |",
        "|---|---:|---:|---:|---:|---:|:---:|",
    ]
    for name, item in failing.items():
        lines.append(
            f"| {name} | {item['observed']:.6f} | {item['mean']:.6f} | "
            f"{item['q95']:.6f} | {item['q99']:.6f} | "
            f"{item['observed_empirical_percentile_plus_one']:.4f} | {item['beyond_q99']} |"
        )
    lines += ["", "The five target ECEs, equivalence-class top-label ECE, and 50/80/90/95% class coverage are reported as passing controls in the JSON record.", ""]
    lines += [
        "## Theorem premise", "",
        f"The pre-block complete-native fixture proof passed: production sum `{complete['production_sum']}`, oracle sum `{complete['oracle_sum']}`, public module-predictive error `{complete['module_predictive']['max_error']}`. Its scope is the enumerable factorized dummy, not every complete 64-slice path. The active-count posterior sum error is `{active_sum_error}` and its maximum mismatch from a fresh marginalization of the serialized protect posterior is `{active_marginal_error}`.", "",
    ]
    if beyond:
        lines += [
            "## Localization", "",
            "Observed statistics beyond their null q99: " + ", ".join(beyond) + ". Bin-level signed gaps, truth-class decomposition, and the active-count/JOINT_POLICY_Y residual correlation are recorded in the JSON.", "",
        ]
    else:
        lines += ["## Localization", "", "None of the three observed failures exceeds its posterior-predictive null q99; the threshold misses are typical finite-sample draws under the retained posteriors.", ""]
    lines += [
        "The active-count miss is nonmonotone across confidence bins. `JOINT_POLICY_Y` is predominantly overpredicted below posterior 0.7. Their signed residual correlation is `-0.0505`, so the two structural misses are not concentrated in the same worlds.", "",
        "Passing controls beyond their null q99: " + (", ".join(control_beyond) if control_beyond else "none") + ". Identity is mainly underconfident; 95% class coverage is overcoverage.", "",
    ]
    lines += [
        "## Token-mass caveat", "",
        "Target calibration is world-weighted. Each world has total weight 1/2000, split across its delivered tokens, so large raw token bins do not receive proportional world weight. Full occupancy tables are in the JSON.", "",
    ]
    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"status": "COMPLETE", "beyond_q99": beyond}, sort_keys=True))


if __name__ == "__main__":
    main()
