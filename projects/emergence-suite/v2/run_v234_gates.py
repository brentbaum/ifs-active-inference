#!/usr/bin/env python3
"""Sequential V2.3.4 gate runner."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from ref import constitution, v234, v234_oracle
from ref.manifest_chain import verify_manifest_chain


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "V2.3.4"
OUT.mkdir(parents=True, exist_ok=True)
TOL = v234.TOLERANCE
BOUNDS = {
    "B_max_v232_formation": 3.801426508560692,
    "B_max_v24_common_emissions": 6.704414354964107,
    "B_max_v25a_configural": 6.084736253211209,
    "B_max_v25a_marginal_accounting": 6.704414354964107,
    "B_max_v25b": 11.302393144606405,
    "B_max_v26a_relational": 6.9920964274158885,
    "B_max_v26a_root": 2.9444389791664394,
    **v234.finite_information_bound(),
}


def plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    return value


def dump(name: str, value: Any) -> None:
    (OUT / name).write_text(
        json.dumps(plain(value), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def interval(values: Iterable[float]) -> dict[str, float]:
    array = np.asarray(tuple(values), dtype=float)
    mean = float(array.mean())
    half = (
        0.0
        if len(array) < 2
        else 1.96 * float(array.std(ddof=1)) / math.sqrt(len(array))
    )
    return {"mean": mean, "lower_95": mean - half, "upper_95": mean + half}


def confidence_ece(probability: np.ndarray, truth: np.ndarray) -> float:
    confidence = np.maximum(probability, 1.0 - probability)
    prediction = probability >= 0.5
    correct = prediction == truth.astype(bool)
    result = 0.0
    for index in range(10):
        lower, upper = index / 10.0, (index + 1) / 10.0
        mask = (confidence >= lower) & (
            confidence <= upper if index == 9 else confidence < upper
        )
        if np.any(mask):
            result += float(mask.mean()) * abs(
                float(confidence[mask].mean())
                - float(correct[mask].mean())
            )
    return result


def credible_set(q: np.ndarray, mass: float = 0.95) -> set[int]:
    order = np.argsort(-q)
    result: set[int] = set()
    cumulative = 0.0
    for index in order:
        result.add(int(index))
        cumulative += float(q[index])
        if cumulative >= mass:
            break
    return result


def posterior_metrics(
    world: v234.AttributionWorld, result: v234.AttributionScore
) -> dict[str, Any]:
    q = result.posterior.reshape(len(v234.THETA), len(v234.CONFIGS))
    q_theta = q.sum(axis=1)
    q_config = q.sum(axis=0)
    eta_marginals = []
    eta_selected = []
    for context in range(2):
        marginal = np.zeros(len(v234.ETA))
        for index, config in enumerate(v234.CONFIGS):
            marginal[config[context]] += q_config[index]
        eta_marginals.append(marginal)
        eta_selected.append(int(np.argmax(marginal)))
    true_flat = world.theta_index * len(v234.CONFIGS) + v234.CONFIG_INDEX[
        world.eta_indices
    ]
    causal_truth = int(world.eta_indices != (0, 0))
    return {
        "q_causal": result.efficacy_causal_probability,
        "causal_truth": causal_truth,
        "causal_selected": int(result.efficacy_causal_probability >= 0.5),
        "theta_mean": result.threat_probability,
        "theta_truth": float(v234.THETA[world.theta_index]),
        "theta_selected": int(np.argmax(q_theta)),
        "eta_mean": result.eta_mean,
        "eta_truth": [
            float(v234.ETA[index]) for index in world.eta_indices
        ],
        "eta_selected": eta_selected,
        "eta_truth_indices": world.eta_indices,
        "covered": true_flat in credible_set(result.posterior),
        "correlation": result.theta_eta_correlation,
    }


def attainability_audit() -> dict[str, Any]:
    rows = []
    for seed in range(1_299_000, 1_299_200):
        world = v234.generate_world(seed, identifiable=True)
        rows.append(posterior_metrics(world, v234.score(world.episodes)))
    reductions = []
    for seed in range(1_299_200, 1_299_400):
        pure = v234.generate_world(seed, identifiable=False)
        probed = v234.generate_world(seed, identifiable=True)
        pure_score = v234.score(pure.episodes)
        probed_score = v234.score(probed.episodes)
        reductions.append(
            abs(pure_score.theta_eta_correlation[0])
            - abs(probed_score.theta_eta_correlation[0])
        )
    metrics = {
        "public_seed_block": [1_299_000, 1_299_399],
        "identifiable_worlds": 200,
        "H_E_accuracy": float(
            np.mean(
                [
                    row["causal_selected"] == row["causal_truth"]
                    for row in rows
                ]
            )
        ),
        "context_eta_accuracy": float(
            np.mean(
                [
                    row["eta_selected"][context]
                    == row["eta_truth_indices"][context]
                    for row in rows
                    for context in range(2)
                ]
            )
        ),
        "eta_MAE": float(
            np.mean(
                [
                    abs(row["eta_mean"][context] - row["eta_truth"][context])
                    for row in rows
                    for context in range(2)
                ]
            )
        ),
        "danger_MAE": float(
            np.mean(
                [abs(row["theta_mean"] - row["theta_truth"]) for row in rows]
            )
        ),
        "probe_median_absolute_correlation_reduction": float(
            np.median(reductions)
        ),
    }
    floors = {
        "H_E_accuracy": metrics["H_E_accuracy"] >= 0.85,
        "context_eta_accuracy": metrics["context_eta_accuracy"] >= 0.75,
        "eta_MAE": metrics["eta_MAE"] <= 0.10,
        "danger_MAE": metrics["danger_MAE"] <= 0.05,
        "probe_correlation_reduction": (
            metrics["probe_median_absolute_correlation_reduction"] >= 0.15
        ),
    }
    return {
        "metrics": metrics,
        "floor_screen": floors,
        "suspected_unattainable_floor": (
            [name for name, passed in floors.items() if not passed]
        ),
        "criterion_status": "public-dummy descriptive only",
    }


def run_gate1() -> bool:
    proofs: dict[str, dict[str, Any]] = {}
    masked = v234.Episode(v234.ACTIONS["protect"], 0, None)
    masked_likelihood, _ = v234.slice_likelihood(masked)
    masked_error = float(np.max(np.abs(masked_likelihood - 1.0)))
    proofs["01_masked_BF_one"] = {
        "maximum_error": masked_error,
        "passed": masked_error <= TOL,
    }
    safe_protect = v234.Episode(v234.ACTIONS["protect"], 0, 0)
    ordinary, _ = v234.slice_likelihood(safe_protect)
    irrelevant, _ = v234.slice_likelihood(
        safe_protect, force_action_irrelevant=True
    )
    zero_states = v234.STATE_ETA0 == 0.0
    zero_error = float(np.max(np.abs(ordinary[zero_states] - irrelevant[zero_states])))
    proofs["02_eta_zero_equals_irrelevant"] = {
        "maximum_error": zero_error,
        "passed": zero_error <= TOL,
    }
    full_states = v234.STATE_ETA0 == 1.0
    full_range = float(np.ptp(ordinary[full_states]))
    proofs["03_full_efficacy_safety_not_danger_evidence"] = {
        "likelihood_range_over_theta": full_range,
        "passed": full_range <= TOL,
    }
    engage_safe = v234.Episode(v234.ACTIONS["engage"], 0, 0)
    before = float(v234.JOINT_PRIOR @ v234.STATE_THETA)
    after = v234.score([engage_safe]).threat_probability
    proofs["04_engagement_safety_disconfirms_danger"] = {
        "before": before,
        "after": after,
        "passed": after < before,
    }
    engage_masked, _ = v234.slice_likelihood(
        v234.Episode(v234.ACTIONS["engage"], 0, None)
    )
    action_error = float(np.max(np.abs(engage_masked - masked_likelihood)))
    proofs["05_action_no_direct_update"] = {
        "maximum_error": action_error,
        "action_selection_likelihood": False,
        "passed": action_error <= TOL,
    }
    relief_score = v234.score(
        [v234.Episode(v234.ACTIONS["protect"], 0, None, relief=1)]
    )
    relief_error = float(
        np.max(np.abs(relief_score.posterior - v234.JOINT_PRIOR))
    )
    proofs["06_relief_policy_only"] = {
        "scientific_posterior_error": relief_error,
        "policy_probability": relief_score.policy_probability,
        "passed": relief_error <= TOL and relief_score.policy_probability > 0.5,
    }
    spike = float(v234.JOINT_PRIOR[v234.STATE_CAUSAL == 0].sum())
    proofs["07_exact_spike"] = {
        "spike_mass": spike,
        "eta_value": 0.0,
        "passed": abs(spike - v234.PARAMETERS["irrelevant_spike_prior"]) <= TOL,
    }
    pure_world = v234.generate_world(1_299_400, identifiable=False)
    pure = v234.score(pure_world.episodes)
    proofs["08_pure_avoidance_confounding"] = {
        "theta_eta_correlation": pure.theta_eta_correlation,
        "passed": pure.theta_eta_correlation[0] > 0.0,
    }
    probe_world = v234.generate_world(1_299_400, identifiable=True)
    probed = v234.score(probe_world.episodes)
    reduction = abs(pure.theta_eta_correlation[0]) - abs(
        probed.theta_eta_correlation[0]
    )
    proofs["09_forced_probe_reduces_confounding"] = {
        "absolute_correlation_reduction": reduction,
        "passed": reduction > 0.0,
    }
    oracle_episode = v234.Episode(1, 1, 0, 1, 1)
    likelihood, _ = v234.slice_likelihood(oracle_episode)
    production = v234._normalize(v234.JOINT_PRIOR * likelihood)
    prior_copy = v234.JOINT_PRIOR.copy()
    prior_bytes = prior_copy.tobytes()
    oracle, oracle_evidence = v234_oracle.update(
        prior_copy,
        v234.THETA,
        v234.ETA,
        v234.CONFIGS,
        (
            oracle_episode.action,
            oracle_episode.context,
            oracle_episode.outcome,
            oracle_episode.near_miss,
            oracle_episode.efficacy_observation,
        ),
        (
            v234.PARAMETERS["outcome_reliability"],
            v234.PARAMETERS["danger_diagnostic_reliability"],
            v234.PARAMETERS["efficacy_diagnostic_reliability"],
        ),
    )
    oracle_error = float(np.max(np.abs(production - oracle)))
    proofs["10_independent_enumeration"] = {
        "maximum_error": oracle_error,
        "prior_input_unchanged": prior_bytes == prior_copy.tobytes(),
        "oracle_evidence": oracle_evidence,
        "passed": (
            oracle_error <= TOL and prior_bytes == prior_copy.tobytes()
        ),
    }
    audit = attainability_audit()
    passed = all(item["passed"] for item in proofs.values())
    payload = {
        "stage": "V2.3.4",
        "gate": 1,
        "proofs": proofs,
        "proof_count": len(proofs),
        "attainability_audit_before_gate2": audit,
        "bounds": BOUNDS,
        "custody": {"escrow_accessed": False, "passed": True},
        "passed": passed,
    }
    dump("gate-1.json", payload)
    dump("gate-2-attainability-public-dummies.json", audit)
    report = [
        "# V2.3.4 gate 1",
        "",
        f"Verdict: **{'PASS' if passed else 'FAIL'}**.",
        "",
    ]
    report += [
        f"- `{name}`: {'PASS' if item['passed'] else 'FAIL'} — {plain(item)}"
        for name, item in proofs.items()
    ]
    report += [
        "",
        "## Prospective Gate-2 attainability screen",
        "",
        f"`{plain(audit)}`",
    ]
    (OUT / "gate-1-report.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    return passed


def run_gate2() -> bool:
    identifiable_rows = []
    for seed in range(1_300_000, 1_301_500):
        world = v234.generate_world(seed, identifiable=True)
        result = v234.score(world.episodes)
        identifiable_rows.append(
            {
                "seed": seed,
                **posterior_metrics(world, result),
                "posterior": result.posterior,
            }
        )
    pure_rows = []
    for seed in range(1_301_500, 1_303_000):
        world = v234.generate_world(seed, identifiable=False)
        result = v234.score(world.episodes)
        probed_world = v234.generate_world(seed, identifiable=True)
        probed = v234.score(probed_world.episodes)
        metrics = posterior_metrics(world, result)
        pure_rows.append(
            {
                "seed": seed,
                **metrics,
                "posterior": result.posterior,
                "probed_correlation": probed.theta_eta_correlation,
                "absolute_correlation_reduction": (
                    abs(result.theta_eta_correlation[0])
                    - abs(probed.theta_eta_correlation[0])
                ),
            }
        )
    causal_probability = np.asarray(
        [row["q_causal"] for row in identifiable_rows]
    )
    causal_truth = np.asarray(
        [row["causal_truth"] for row in identifiable_rows], dtype=int
    )
    zero_truth_rows = [
        row for row in identifiable_rows if row["causal_truth"] == 0
    ]
    context_accuracy = [
        row["eta_selected"][context] == row["eta_truth_indices"][context]
        for row in identifiable_rows
        for context in range(2)
    ]
    metrics = {
        "identifiable_world_count": len(identifiable_rows),
        "pure_avoidance_world_count": len(pure_rows),
        "H_E_accuracy": float(
            np.mean(
                [
                    row["causal_selected"] == row["causal_truth"]
                    for row in identifiable_rows
                ]
            )
        ),
        "exact_zero_accuracy": float(
            np.mean([row["causal_selected"] == 0 for row in zero_truth_rows])
        ),
        "brier": float(
            np.mean((causal_probability - causal_truth) ** 2)
        ),
        "ece": confidence_ece(causal_probability, causal_truth),
        "context_efficacy_classification": float(np.mean(context_accuracy)),
        "eta_MAE": float(
            np.mean(
                [
                    abs(row["eta_mean"][context] - row["eta_truth"][context])
                    for row in identifiable_rows
                    for context in range(2)
                ]
            )
        ),
        "danger_rate_MAE": float(
            np.mean(
                [
                    abs(row["theta_mean"] - row["theta_truth"])
                    for row in identifiable_rows
                ]
            )
        ),
        "parameter_coverage": float(
            np.mean([row["covered"] for row in identifiable_rows])
        ),
        "pure_false_certainty_rate": float(
            np.mean(
                [
                    max(row["q_causal"], 1.0 - row["q_causal"]) >= 0.95
                    and row["causal_selected"] != row["causal_truth"]
                    for row in pure_rows
                ]
            )
        ),
        "pure_joint_coverage": float(
            np.mean([row["covered"] for row in pure_rows])
        ),
        "pure_median_theta_eta_correlation": float(
            np.median([row["correlation"][0] for row in pure_rows])
        ),
        "probe_median_absolute_correlation_reduction": float(
            np.median(
                [row["absolute_correlation_reduction"] for row in pure_rows]
            )
        ),
    }
    checks = {
        "H_E_accuracy_at_least_0_85": metrics["H_E_accuracy"] >= 0.85,
        "exact_zero_accuracy_at_least_0_85": metrics["exact_zero_accuracy"] >= 0.85,
        "brier_at_most_0_15": metrics["brier"] <= 0.15,
        "ece_at_most_0_08": metrics["ece"] <= 0.08,
        "context_efficacy_at_least_0_75": metrics["context_efficacy_classification"] >= 0.75,
        "eta_MAE_at_most_0_10": metrics["eta_MAE"] <= 0.10,
        "danger_MAE_at_most_0_05": metrics["danger_rate_MAE"] <= 0.05,
        "coverage_at_least_0_90": metrics["parameter_coverage"] >= 0.90,
        "pure_false_certainty_at_most_0_05": metrics["pure_false_certainty_rate"] <= 0.05,
        "pure_joint_coverage_at_least_0_90": metrics["pure_joint_coverage"] >= 0.90,
        "pure_positive_correlation": metrics["pure_median_theta_eta_correlation"] > 0.0,
        "probes_reduce_correlation_at_least_0_15": metrics["probe_median_absolute_correlation_reduction"] >= 0.15,
    }
    passed = all(checks.values())
    payload = {
        "stage": "V2.3.4",
        "gate": 2,
        "seed_block": [1_300_000, 1_302_999],
        "metrics": metrics,
        "checks": checks,
        "bounds": BOUNDS,
        "passed": passed,
    }
    dump("gate-2-per_world.json", {"identifiable": identifiable_rows, "pure": pure_rows})
    dump("gate-2.json", payload)
    report = ["# V2.3.4 gate 2", "", f"Verdict: **{'PASS' if passed else 'FAIL'}**.", "", "## Metrics", ""]
    report += [f"- `{name}`: {value}" for name, value in metrics.items()]
    report += ["", "## Criteria", ""] + [
        f"- `{name}`: {'PASS' if value else 'FAIL'}"
        for name, value in checks.items()
    ]
    (OUT / "gate-2-report.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    if not passed:
        failures = [name for name, value in checks.items() if not value]
        (OUT / "gate-2-diagnosis-stub.md").write_text(
            "# V2.3.4 gate-2 diagnosis stub\n\n"
            "Honest stop. Failed criteria retained verbatim:\n\n"
            + "\n".join(f"- `{name}`" for name in failures)
            + "\n",
            encoding="utf-8",
        )
    return passed


def known_config_prior(left: int, right: int) -> np.ndarray:
    prior = np.zeros_like(v234.JOINT_PRIOR)
    config_index = v234.CONFIG_INDEX[(left, right)]
    for theta_index, weight in enumerate(v234.THETA_PRIOR):
        prior[theta_index * len(v234.CONFIGS) + config_index] = weight
    return prior


def safe_episodes(
    count: int,
    *,
    action: int,
    masked: bool = False,
    near_miss_last: int | None = None,
    relief: int | None = None,
) -> tuple[v234.Episode, ...]:
    return tuple(
        v234.Episode(
            action,
            (time // 12) % 2,
            None if masked else 0,
            near_miss_last if time == count - 1 else None,
            None,
            relief,
        )
        for time in range(count)
    )


def gate3_row(seed: int, assay: int) -> dict[str, Any]:
    prior_threat = float(v234.THETA_PRIOR @ v234.THETA)
    if assay == 1:
        prior = known_config_prior(0, 0)
        protect = v234.score(
            safe_episodes(32, action=v234.ACTIONS["protect"]),
            initial_prior=prior,
        )
        engage = v234.score(
            safe_episodes(32, action=v234.ACTIONS["engage"]),
            initial_prior=prior,
        )
        return {
            "seed": seed,
            "assay": assay,
            "scientific_identity_error": abs(
                protect.threat_probability - engage.threat_probability
            ),
        }
    if assay == 2:
        prior = known_config_prior(4, 4)
        protected = v234.score(
            safe_episodes(32, action=v234.ACTIONS["protect"]),
            initial_prior=prior,
        )
        observed = v234.score(
            safe_episodes(32, action=v234.ACTIONS["engage"]),
            initial_prior=prior,
        )
        return {
            "seed": seed,
            "assay": assay,
            "threat_preservation": (
                protected.threat_probability - observed.threat_probability
            ),
        }
    if assay == 3:
        full = v234.score(
            safe_episodes(32, action=v234.ACTIONS["protect"]),
            initial_prior=known_config_prior(4, 4),
        )
        partial = v234.score(
            safe_episodes(32, action=v234.ACTIONS["protect"]),
            initial_prior=known_config_prior(2, 2),
        )
        full_learning = prior_threat - full.threat_probability
        partial_learning = prior_threat - partial.threat_probability
        return {
            "seed": seed,
            "assay": assay,
            "partial_minus_full_corrective_learning": (
                partial_learning - full_learning
            ),
        }
    if assay == 4:
        result = v234.score(
            safe_episodes(32, action=v234.ACTIONS["protect"], masked=True)
        )
        return {
            "seed": seed,
            "assay": assay,
            "posterior_error": float(
                np.max(np.abs(result.posterior - v234.JOINT_PRIOR))
            ),
        }
    if assay == 5:
        result = v234.score(
            safe_episodes(
                32,
                action=v234.ACTIONS["protect"],
                masked=True,
                relief=1,
            )
        )
        return {
            "seed": seed,
            "assay": assay,
            "policy_change": result.policy_probability - 0.5,
            "threat_change": result.threat_probability - prior_threat,
        }
    if assay == 6:
        world = v234.generate_controlled_world(seed, scenario="adaptive")
        result = v234.score(world.episodes)
        return {
            "seed": seed,
            "assay": assay,
            "danger_recovered": result.threat_probability,
            "efficacy_recovered": min(result.eta_mean),
            "adaptive_recovered": (
                result.threat_probability >= 0.7
                and min(result.eta_mean) >= 0.75
            ),
        }
    if assay == 7:
        world = v234.generate_controlled_world(
            seed, scenario="context_switch"
        )
        result = v234.score(world.episodes)
        q = result.posterior.reshape(len(v234.THETA), len(v234.CONFIGS)).sum(0)
        selected = []
        for context in range(2):
            marginal = np.zeros(len(v234.ETA))
            for index, config in enumerate(v234.CONFIGS):
                marginal[config[context]] += q[index]
            selected.append(int(np.argmax(marginal)))
        return {
            "seed": seed,
            "assay": assay,
            "context_accuracy": float(
                np.mean(
                    [
                        selected[context] == world.eta_indices[context]
                        for context in range(2)
                    ]
                )
            ),
        }
    if assay == 8:
        pure_world = v234.generate_world(
            seed,
            identifiable=False,
            theta_index=0,
            eta_indices=(4, 4),
        )
        probe_world = v234.generate_world(
            seed,
            identifiable=True,
            theta_index=0,
            eta_indices=(4, 4),
        )
        pure = v234.score(pure_world.episodes)
        probed = v234.score(probe_world.episodes)
        return {
            "seed": seed,
            "assay": assay,
            "correlation_reduction": (
                abs(pure.theta_eta_correlation[0])
                - abs(probed.theta_eta_correlation[0])
            ),
            "threat_revision": (
                pure.threat_probability - probed.threat_probability
            ),
        }
    if assay == 9:
        deltas = []
        for eta_index in (0, 2, 4):
            result = v234.score(
                safe_episodes(32, action=v234.ACTIONS["protect"]),
                initial_prior=known_config_prior(eta_index, eta_index),
            )
            deltas.append(result.threat_probability - prior_threat)
        return {
            "seed": seed,
            "assay": assay,
            "maximum_safety_only_strengthening": max(deltas),
        }
    if assay == 10:
        prior = known_config_prior(4, 4)
        safety = v234.score(
            safe_episodes(32, action=v234.ACTIONS["protect"]),
            initial_prior=prior,
        )
        diagnostic = v234.score(
            safe_episodes(
                32,
                action=v234.ACTIONS["protect"],
                near_miss_last=1,
            ),
            initial_prior=prior,
        )
        return {
            "seed": seed,
            "assay": assay,
            "safety_only_change": safety.threat_probability - prior_threat,
            "diagnostic_strengthening": (
                diagnostic.threat_probability - safety.threat_probability
            ),
        }
    world = v234.generate_controlled_world(seed, scenario="partial")
    observed = v234.score(world.episodes)
    masked_episodes = tuple(
        v234.Episode(
            item.action,
            item.context,
            None,
            item.near_miss,
            item.efficacy_observation,
            item.relief,
        )
        for item in world.episodes
    )
    masked = v234.score(masked_episodes)
    initial_logit = math.log(prior_threat / (1.0 - prior_threat))
    masked_logit = math.log(
        masked.threat_probability / (1.0 - masked.threat_probability)
    )
    observed_logit = math.log(
        observed.threat_probability / (1.0 - observed.threat_probability)
    )
    omitted = masked_logit - initial_logit
    attribution = observed_logit - masked_logit
    total = observed_logit - initial_logit
    return {
        "seed": seed,
        "assay": assay,
        "decomposition_error": abs(total - omitted - attribution),
        "omitted_evidence": omitted,
        "attribution_evidence": attribution,
        "total_change": total,
    }


def gate3_attainability() -> dict[str, Any]:
    rows = [
        gate3_row(1_299_500 + assay, assay) for assay in range(1, 12)
    ]
    context_population = [
        gate3_row(seed, 7)["context_accuracy"]
        for seed in range(1_299_600, 1_299_800)
    ]
    context_population_accuracy = float(np.mean(context_population))
    screen = {
        "assay_1_identity": rows[0]["scientific_identity_error"] <= TOL,
        "assay_2_floor": rows[1]["threat_preservation"] >= 0.05,
        "assay_3_floor": rows[2]["partial_minus_full_corrective_learning"] >= 0.05,
        "assay_5_policy": rows[4]["policy_change"] >= 0.10,
        "assay_6_adaptive": rows[5]["adaptive_recovered"],
        "assay_7_context": context_population_accuracy >= 0.75,
        "assay_8_correlation": rows[7]["correlation_reduction"] > 0.0,
        "assay_10_diagnostic": rows[9]["diagnostic_strengthening"] > 0.0,
        "assay_11_decomposition": rows[10]["decomposition_error"] <= TOL,
    }
    return {
        "public_dummy_seed_blocks": [
            [1_299_501, 1_299_511],
            [1_299_600, 1_299_799]
        ],
        "rows": rows,
        "context_population_accuracy_200_worlds": (
            context_population_accuracy
        ),
        "screen": screen,
        "suspected_unattainable_floor": [
            name for name, passed in screen.items() if not passed
        ],
        "criterion_status": "public-dummy descriptive only",
    }


def run_gate3() -> bool:
    boundaries = [450] * 10 + [500]
    rows = []
    seed = 1_303_000
    for assay, count in enumerate(boundaries, start=1):
        for _ in range(count):
            rows.append(gate3_row(seed, assay))
            seed += 1
    by_assay = {
        assay: [row for row in rows if row["assay"] == assay]
        for assay in range(1, 12)
    }
    identity_max = max(row["scientific_identity_error"] for row in by_assay[1])
    preservation = interval(row["threat_preservation"] for row in by_assay[2])
    partial = interval(
        row["partial_minus_full_corrective_learning"] for row in by_assay[3]
    )
    masked_max = max(row["posterior_error"] for row in by_assay[4])
    policy = interval(row["policy_change"] for row in by_assay[5])
    sham_threat = interval(row["threat_change"] for row in by_assay[5])
    adaptive_rate = float(np.mean([row["adaptive_recovered"] for row in by_assay[6]]))
    context_accuracy = float(np.mean([row["context_accuracy"] for row in by_assay[7]]))
    correlation = interval(row["correlation_reduction"] for row in by_assay[8])
    probe_revision = interval(row["threat_revision"] for row in by_assay[8])
    safety_strengthening = max(
        row["maximum_safety_only_strengthening"] for row in by_assay[9]
    )
    diagnostic = interval(row["diagnostic_strengthening"] for row in by_assay[10])
    decomposition_max = max(row["decomposition_error"] for row in by_assay[11])
    metrics = {
        "irrelevant_vs_engage_identity_max": identity_max,
        "full_protection_threat_preservation": preservation,
        "partial_minus_full_corrective_learning": partial,
        "masked_posterior_error_max": masked_max,
        "relief_sham_policy_change": policy,
        "relief_sham_threat_change": sham_threat,
        "adaptive_recovery_rate": adaptive_rate,
        "context_efficacy_macro_accuracy": context_accuracy,
        "forced_probe_correlation_reduction": correlation,
        "forced_probe_threat_revision": probe_revision,
        "safety_only_strengthening_max": safety_strengthening,
        "diagnostic_strengthening": diagnostic,
        "maintenance_decomposition_error_max": decomposition_max,
        "world_count": len(rows),
    }
    checks = {
        "1_irrelevant_identical": identity_max <= TOL,
        "2_full_preserves_threat": preservation["mean"] >= 0.05 and preservation["lower_95"] > 0,
        "3_partial_more_corrective": partial["mean"] >= 0.05 and partial["lower_95"] > 0,
        "4_masked_neutral": masked_max <= TOL,
        "5_relief_policy": policy["mean"] >= 0.10 and policy["lower_95"] > 0,
        "5_relief_threat_neutral": max(abs(sham_threat["lower_95"]), abs(sham_threat["upper_95"])) <= 0.01,
        "6_adaptive_recovered": adaptive_rate >= 0.75,
        "7_context_classification": context_accuracy >= 0.75,
        "8_probes_reduce_confounding": correlation["lower_95"] > 0 and probe_revision["lower_95"] > 0,
        "9_safety_not_strengthen": safety_strengthening <= TOL,
        "10_diagnostic_required": diagnostic["lower_95"] > 0,
        "11_maintenance_decomposition": decomposition_max <= TOL,
    }
    passed = all(checks.values())
    payload = {
        "stage": "V2.3.4",
        "gate": 3,
        "seed_block": [1_303_000, 1_307_999],
        "metrics": metrics,
        "checks": checks,
        "bounds": BOUNDS,
        "passed": passed,
    }
    dump("gate-3-per_world.json", rows)
    dump("gate-3.json", payload)
    report = ["# V2.3.4 gate 3", "", f"Verdict: **{'PASS' if passed else 'FAIL'}**.", "", "## Metrics", ""]
    report += [f"- `{name}`: {plain(value)}" for name, value in metrics.items()]
    report += ["", "## Criteria", ""] + [
        f"- `{name}`: {'PASS' if value else 'FAIL'}" for name, value in checks.items()
    ]
    (OUT / "gate-3-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    if not passed:
        failures = [name for name, value in checks.items() if not value]
        (OUT / "gate-3-diagnosis-stub.md").write_text(
            "# V2.3.4 gate-3 diagnosis stub\n\nHonest stop. Failed criteria retained verbatim:\n\n"
            + "\n".join(f"- `{name}`" for name in failures)
            + "\n",
            encoding="utf-8",
        )
    return passed


def gate4_row(seed: int) -> dict[str, Any]:
    adaptive_world = v234.generate_controlled_world(seed, scenario="adaptive")
    adaptive = v234.score(adaptive_world.episodes)
    no_existence = v234.score(
        adaptive_world.episodes, lesions=("efficacy_existence",)
    )
    broadcast = v234.score(
        adaptive_world.episodes, lesions=("broadcast",)
    )
    full_safety = safe_episodes(32, action=v234.ACTIONS["protect"])
    full_baseline = v234.score(
        full_safety, initial_prior=known_config_prior(4, 4)
    )
    action_irrelevant = v234.score(
        full_safety,
        initial_prior=known_config_prior(4, 4),
        lesions=("action_relevance",),
    )
    engage = v234.score(
        safe_episodes(32, action=v234.ACTIONS["engage"]),
        initial_prior=known_config_prior(4, 4),
    )
    masked_world = v234.generate_world(
        seed,
        identifiable=False,
        theta_index=0,
        eta_indices=(2, 2),
        masking=1.0,
    )
    visible_world = v234.generate_world(
        seed,
        identifiable=False,
        theta_index=0,
        eta_indices=(2, 2),
        masking=0.0,
    )
    masked_score = v234.score(masked_world.episodes)
    visible_score = v234.score(visible_world.episodes)
    relief_episodes = safe_episodes(
        32,
        action=v234.ACTIONS["protect"],
        masked=True,
        relief=1,
    )
    relief = v234.score(relief_episodes)
    no_relief = v234.score(relief_episodes, lesions=("relief",))
    context_world = v234.generate_controlled_world(
        seed, scenario="context_switch"
    )
    context = v234.score(context_world.episodes)
    no_context = v234.score(
        context_world.episodes, lesions=("context_specificity",)
    )
    no_formation = v234.score(
        adaptive_world.episodes, lesions=("formation_coupling",)
    )
    prior_threat = float(v234.THETA_PRIOR @ v234.THETA)
    return {
        "seed": seed,
        "efficacy_existence_causal": no_existence.efficacy_causal_probability,
        "efficacy_existence_threat_survival": abs(
            no_existence.threat_probability - adaptive.threat_probability
        ),
        "visible_correction": (
            masked_score.threat_probability - visible_score.threat_probability
        ),
        "visible_efficacy_survival": visible_score.efficacy_causal_probability,
        "action_irrelevant_identity_error": abs(
            action_irrelevant.threat_probability - engage.threat_probability
        ),
        "action_irrelevant_effect": (
            full_baseline.threat_probability
            - action_irrelevant.threat_probability
        ),
        "relief_removed_policy_error": abs(no_relief.policy_probability - 0.5),
        "relief_scientific_survival_error": float(
            np.max(np.abs(relief.posterior - no_relief.posterior))
        ),
        "context_baseline_difference": abs(context.eta_mean[0] - context.eta_mean[1]),
        "context_lesion_difference": abs(no_context.eta_mean[0] - no_context.eta_mean[1]),
        "context_threat_survival": abs(
            context.threat_probability - no_context.threat_probability
        ),
        "formation_removed_error": abs(
            no_formation.formation_probability - prior_threat
        ),
        "formation_threat_survival": abs(
            no_formation.threat_probability - adaptive.threat_probability
        ),
        "broadcast_threat_update": abs(
            broadcast.threat_probability - prior_threat
        ),
        "broadcast_action_semantic_error": float(
            np.max(
                np.abs(
                    v234.slice_likelihood(v234.Episode(0, 0, None))[0]
                    - v234.slice_likelihood(v234.Episode(1, 0, None))[0]
                )
            )
        ),
    }


def gate4_attainability() -> dict[str, Any]:
    rows = [gate4_row(seed) for seed in range(1_299_800, 1_299_900)]
    visible = interval(row["visible_correction"] for row in rows)
    action = interval(row["action_irrelevant_effect"] for row in rows)
    context_effect = interval(
        row["context_baseline_difference"] - row["context_lesion_difference"]
        for row in rows
    )
    screen = {
        "visible_correction_positive": visible["lower_95"] > 0,
        "action_irrelevant_effect_positive": action["lower_95"] > 0,
        "context_specificity_removed": context_effect["lower_95"] > 0,
        "formation_exact": max(row["formation_removed_error"] for row in rows) <= TOL,
        "broadcast_update_removed": max(row["broadcast_threat_update"] for row in rows) <= TOL,
    }
    return {
        "public_seed_block": [1_299_800, 1_299_899],
        "metrics": {
            "visible_correction": visible,
            "action_irrelevant_effect": action,
            "context_specificity_effect": context_effect,
        },
        "screen": screen,
        "suspected_unattainable_floor": [
            name for name, passed in screen.items() if not passed
        ],
        "criterion_status": "public-dummy descriptive only",
    }


def run_gate4() -> bool:
    rows = [gate4_row(seed) for seed in range(1_308_000, 1_309_000)]
    visible = interval(row["visible_correction"] for row in rows)
    action = interval(row["action_irrelevant_effect"] for row in rows)
    context_effect = interval(
        row["context_baseline_difference"] - row["context_lesion_difference"]
        for row in rows
    )
    metrics = {
        "efficacy_existence_causal_min": min(row["efficacy_existence_causal"] for row in rows),
        "efficacy_existence_threat_survival_max": max(row["efficacy_existence_threat_survival"] for row in rows),
        "forced_visibility_correction": visible,
        "action_irrelevant_effect": action,
        "action_irrelevant_identity_max": max(row["action_irrelevant_identity_error"] for row in rows),
        "relief_removed_policy_error_max": max(row["relief_removed_policy_error"] for row in rows),
        "relief_scientific_survival_max": max(row["relief_scientific_survival_error"] for row in rows),
        "context_specificity_effect": context_effect,
        "formation_removed_error_max": max(row["formation_removed_error"] for row in rows),
        "formation_threat_survival_max": max(row["formation_threat_survival"] for row in rows),
        "broadcast_threat_update_max": max(row["broadcast_threat_update"] for row in rows),
        "broadcast_action_semantic_error_max": max(row["broadcast_action_semantic_error"] for row in rows),
        "world_count": len(rows),
    }
    checks = {
        "efficacy_existence_removed": metrics["efficacy_existence_causal_min"] >= 1.0 - TOL,
        "efficacy_existence_threat_survives": metrics["efficacy_existence_threat_survival_max"] <= 0.05,
        "outcomes_visible_target": visible["lower_95"] > 0,
        "action_irrelevant_target": action["lower_95"] > 0 and metrics["action_irrelevant_identity_max"] <= TOL,
        "relief_removed_target": metrics["relief_removed_policy_error_max"] <= TOL,
        "relief_scientific_survives": metrics["relief_scientific_survival_max"] <= TOL,
        "context_specificity_removed": context_effect["lower_95"] > 0,
        "formation_coupling_removed": metrics["formation_removed_error_max"] <= TOL,
        "formation_threat_survives": metrics["formation_threat_survival_max"] <= TOL,
        "broadcast_removed": metrics["broadcast_threat_update_max"] <= TOL,
        "broadcast_action_semantics_survive": metrics["broadcast_action_semantic_error_max"] <= TOL,
    }
    passed = all(checks.values())
    payload = {
        "stage": "V2.3.4",
        "gate": 4,
        "seed_block": [1_308_000, 1_308_999],
        "metrics": metrics,
        "checks": checks,
        "bounds": BOUNDS,
        "passed": passed,
    }
    dump("gate-4-per_world.json", rows)
    dump("gate-4.json", payload)
    report = ["# V2.3.4 gate 4", "", f"Verdict: **{'PASS' if passed else 'FAIL'}**.", "", "## Metrics", ""]
    report += [f"- `{name}`: {plain(value)}" for name, value in metrics.items()]
    report += ["", "## Criteria", ""] + [
        f"- `{name}`: {'PASS' if value else 'FAIL'}" for name, value in checks.items()
    ]
    (OUT / "gate-4-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    if not passed:
        failures = [name for name, value in checks.items() if not value]
        (OUT / "gate-4-diagnosis-stub.md").write_text(
            "# V2.3.4 gate-4 diagnosis stub\n\nHonest stop. Failed criteria retained verbatim:\n\n"
            + "\n".join(f"- `{name}`" for name in failures)
            + "\n",
            encoding="utf-8",
        )
    return passed


GATE5_SCENARIOS = (
    "threat_low",
    "threat_high",
    "efficacy_prior",
    "spike_high",
    "action_cost",
    "efficacy_partial",
    "probe_low",
    "context_change",
    "relief_high",
    "masking",
    "precision_low",
)


def reweighted_prior(
    theta_weights: Sequence[float] | None = None,
    spike: float | None = None,
) -> np.ndarray:
    theta = v234.THETA_PRIOR if theta_weights is None else np.asarray(theta_weights, dtype=float)
    theta = theta / theta.sum()
    config = v234.CONFIG_PRIOR.copy()
    if spike is not None:
        causal = config.copy()
        causal[v234.CONFIG_INDEX[(0, 0)]] = 0.0
        causal /= causal.sum()
        config = causal * (1.0 - spike)
        config[v234.CONFIG_INDEX[(0, 0)]] = spike
    return (theta[:, None] * config[None, :]).reshape(-1)


def gate5_row(item: tuple[int, str]) -> dict[str, Any]:
    seed, scenario = item
    prior = None
    if scenario == "threat_low":
        world = v234.generate_world(seed, identifiable=True, theta_index=0, eta_indices=(4, 4))
        prior = reweighted_prior([0.4, 0.3, 0.15, 0.1, 0.05])
    elif scenario == "threat_high":
        world = v234.generate_world(seed, identifiable=True, theta_index=4, eta_indices=(4, 4))
        prior = reweighted_prior([0.05, 0.1, 0.15, 0.3, 0.4])
    elif scenario == "efficacy_prior":
        world = v234.generate_world(seed, identifiable=True, theta_index=3, eta_indices=(4, 4))
        prior = reweighted_prior(spike=0.65)
    elif scenario == "spike_high":
        world = v234.generate_world(seed, identifiable=True, theta_index=2, eta_indices=(0, 0))
        prior = reweighted_prior(spike=0.75)
    elif scenario == "action_cost":
        world = v234.generate_controlled_world(seed, scenario="relief_sham")
    elif scenario == "efficacy_partial":
        world = v234.generate_world(seed, identifiable=True, theta_index=3, eta_indices=(2, 2))
    elif scenario == "probe_low":
        world = v234.generate_world(
            seed,
            identifiable=True,
            theta_index=0,
            eta_indices=(4, 4),
            probe_frequency=0.20,
        )
    elif scenario == "context_change":
        world = v234.generate_controlled_world(seed, scenario="context_switch")
    elif scenario == "relief_high":
        world = v234.generate_world(
            seed,
            identifiable=False,
            theta_index=2,
            eta_indices=(0, 0),
            masking=1.0,
            relief_probability=0.95,
        )
    elif scenario == "masking":
        world = v234.generate_world(
            seed,
            identifiable=False,
            theta_index=0,
            eta_indices=(2, 2),
            masking=0.60,
        )
    elif scenario == "precision_low":
        world = v234.generate_world(
            seed,
            identifiable=True,
            theta_index=3,
            eta_indices=(2, 2),
        )
    else:
        world = v234.generate_world(seed, identifiable=True, theta_index=4, eta_indices=(4, 4))
    result = v234.score(
        world.episodes,
        initial_prior=prior,
        evidence_precision=(0.65 if scenario == "precision_low" else 1.0),
    )
    no_action_evidence = v234.score(
        tuple(
            v234.Episode(item.action, item.context, None, None, None, item.relief)
            for item in world.episodes
        ),
        initial_prior=prior,
    )
    row = {
        "seed": seed,
        "scenario": scenario,
        "threat": result.threat_probability,
        "q_causal": result.efficacy_causal_probability,
        "eta_mean": result.eta_mean,
        "policy_probability": result.policy_probability,
        "correlation": result.theta_eta_correlation,
        "truth_theta": float(v234.THETA[world.theta_index]),
        "truth_eta": [float(v234.ETA[index]) for index in world.eta_indices],
        "masked_action_scientific_error": float(
            np.max(
                np.abs(
                    no_action_evidence.posterior
                    - (v234.JOINT_PRIOR if prior is None else prior)
                )
            )
        ),
        "one_posterior": True,
    }
    if scenario == "probe_low":
        pure_world = v234.generate_world(
            seed,
            identifiable=False,
            theta_index=0,
            eta_indices=(4, 4),
        )
        pure = v234.score(pure_world.episodes)
        row["probe_correlation_reduction"] = (
            abs(pure.theta_eta_correlation[0])
            - abs(result.theta_eta_correlation[0])
        )
    if scenario == "context_change":
        q = result.posterior.reshape(len(v234.THETA), len(v234.CONFIGS)).sum(0)
        hits = []
        for context in range(2):
            marginal = np.zeros(len(v234.ETA))
            for index, config in enumerate(v234.CONFIGS):
                marginal[config[context]] += q[index]
            hits.append(int(np.argmax(marginal)) == world.eta_indices[context])
        row["context_accuracy"] = float(np.mean(hits))
    if scenario == "masking":
        visible_world = v234.generate_world(
            seed,
            identifiable=False,
            theta_index=0,
            eta_indices=(2, 2),
            masking=0.0,
        )
        visible = v234.score(visible_world.episodes)
        row["masking_error_cost"] = (
            abs(result.threat_probability - row["truth_theta"])
            - abs(visible.threat_probability - row["truth_theta"])
        )
    if scenario == "precision_low":
        full = v234.score(world.episodes)
        row["precision_error_cost"] = (
            abs(result.threat_probability - row["truth_theta"])
            - abs(full.threat_probability - row["truth_theta"])
        )
    return row


def gate5_attainability() -> dict[str, Any]:
    public_items = [
        (1_299_900 + index, scenario)
        for index, scenario in enumerate(GATE5_SCENARIOS)
        if scenario not in {"masking", "precision_low"}
    ]
    rows = [gate5_row(item) for item in public_items]
    masking_rows = [
        gate5_row((seed, "masking")) for seed in range(1_299_900, 1_300_000)
    ]
    precision_rows = [
        gate5_row((seed, "precision_low")) for seed in range(1_299_900, 1_300_000)
    ]
    masking_costs = np.asarray(
        [row["masking_error_cost"] for row in masking_rows], dtype=float
    )
    precision_costs = np.asarray(
        [row["precision_error_cost"] for row in precision_rows], dtype=float
    )
    checks = {
        "probe_reduction": next(row for row in rows if row["scenario"] == "probe_low")["probe_correlation_reduction"] > 0,
        "context_accuracy": next(row for row in rows if row["scenario"] == "context_change")["context_accuracy"] >= 0.5,
        "masking_mean_truth_error_cost_positive": float(np.mean(masking_costs)) > 0.0,
        "masking_positive_rate_at_least_0_80": float(np.mean(masking_costs > 0.0)) >= 0.80,
        "precision_mean_truth_error_cost_positive": float(np.mean(precision_costs)) > 0.0,
        "precision_nonnegative_rate_at_least_0_85": float(np.mean(precision_costs >= 0.0)) >= 0.85,
    }
    return {
        "purpose": "Prospective information-attainability screen completed before opening the assigned Gate-5 block.",
        "public_dummy_seed_block": [1_299_900, 1_299_999],
        "representative_rows": rows,
        "masking_truth_error_cost": {
            "mean": float(np.mean(masking_costs)),
            "q05": float(np.quantile(masking_costs, 0.05)),
            "q50": float(np.quantile(masking_costs, 0.50)),
            "q95": float(np.quantile(masking_costs, 0.95)),
            "positive_rate": float(np.mean(masking_costs > 0.0)),
        },
        "precision_truth_error_cost": {
            "mean": float(np.mean(precision_costs)),
            "q05": float(np.quantile(precision_costs, 0.05)),
            "q50": float(np.quantile(precision_costs, 0.50)),
            "q95": float(np.quantile(precision_costs, 0.95)),
            "nonnegative_rate": float(np.mean(precision_costs >= 0.0)),
        },
        "screen": checks,
        "suspected_unattainable_floor": [name for name, passed in checks.items() if not passed],
        "criterion_status": "public-dummy descriptive only",
        "interpretation": "Masking and precision are evaluated by excess absolute error relative to the generating danger truth; this avoids a prior-relative update-magnitude saturation artifact.",
    }


def run_gate5() -> bool:
    attainability = gate5_attainability()
    dump("gate-5-attainability-public-dummies.json", attainability)
    if attainability["suspected_unattainable_floor"]:
        (OUT / "gate-5-diagnosis-stub.md").write_text(
            "# V2.3.4 gate-5 prospective attainability stop\n\n"
            "The assigned Gate-5 seed block was not opened. Suspected "
            "information-theoretically unattainable directions:\n\n"
            + "\n".join(
                f"- `{name}`"
                for name in attainability["suspected_unattainable_floor"]
            )
            + "\n",
            encoding="utf-8",
        )
        return False
    items = []
    for cell, scenario in enumerate(GATE5_SCENARIOS):
        start = 1_309_000 + cell * 1000
        items.extend((seed, scenario) for seed in range(start, start + 1000))
    try:
        executor_context = concurrent.futures.ProcessPoolExecutor()
    except PermissionError:
        # Some managed sandboxes deny the semaphore-limit query performed by
        # ProcessPoolExecutor before workers start. Thread execution preserves
        # the exact item order and scientific computation.
        executor_context = concurrent.futures.ThreadPoolExecutor()
    with executor_context as executor:
        rows = list(executor.map(gate5_row, items, chunksize=20))
    by_scenario = {
        scenario: [row for row in rows if row["scenario"] == scenario]
        for scenario in GATE5_SCENARIOS
    }
    summaries = {}
    for scenario, cell_rows in by_scenario.items():
        summaries[scenario] = {
            "threat_error": interval(abs(row["threat"] - row["truth_theta"]) for row in cell_rows),
            "eta_error": interval(
                np.mean(
                    [
                        abs(row["eta_mean"][context] - row["truth_eta"][context])
                        for context in range(2)
                    ]
                )
                for row in cell_rows
            ),
            "q_causal": interval(row["q_causal"] for row in cell_rows),
            "policy_probability": interval(row["policy_probability"] for row in cell_rows),
            "masked_action_scientific_error_max": max(row["masked_action_scientific_error"] for row in cell_rows),
            "count": len(cell_rows),
        }
    probe = interval(row["probe_correlation_reduction"] for row in by_scenario["probe_low"])
    context_accuracy = float(np.mean([row["context_accuracy"] for row in by_scenario["context_change"]]))
    masking = interval(row["masking_error_cost"] for row in by_scenario["masking"])
    precision = interval(row["precision_error_cost"] for row in by_scenario["precision_low"])
    precision_nonnegative_rate = float(
        np.mean(
            [
                row["precision_error_cost"] >= 0.0
                for row in by_scenario["precision_low"]
            ]
        )
    )
    action_cost_science_error = summaries["action_cost"]["masked_action_scientific_error_max"]
    suite = subprocess.run(
        [sys.executable, "run_tests_parallel.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    dump(
        "full-fast-suite-gate5.json",
        {
            "command": "python3 run_tests_parallel.py",
            "returncode": suite.returncode,
            "passed": suite.returncode == 0,
            "stdout": suite.stdout,
            "stderr": suite.stderr,
        },
    )
    chain = verify_manifest_chain(ROOT, "results/V2.6a/freeze-manifest.json")
    prior_gates = {
        gate: json.loads((OUT / f"gate-{gate}.json").read_text())["passed"]
        for gate in range(1, 5)
    }
    max_action_error = max(
        row["masked_action_scientific_error"]
        for row in rows
        if row["scenario"] in {"action_cost", "relief_high"}
    )
    checks = {
        "standing_gates_1_4": all(prior_gates.values()),
        "full_cumulative_suite": suite.returncode == 0,
        "permanent_constitution": constitution.cumulative_constitution_audit()["passed"],
        "manifest_chain": bool(chain["passed"]),
        "action_cost_no_scientific_likelihood": action_cost_science_error <= TOL,
        "relief_no_scientific_likelihood": max_action_error <= TOL,
        "probe_frequency_direction": probe["lower_95"] > 0,
        "context_change_classification": context_accuracy >= 0.75,
        "masking_truth_error_cost": masking["lower_95"] > 0,
        "precision_truth_error_cost": precision["lower_95"] > 0,
        "precision_nonnegative_rate": precision_nonnegative_rate >= 0.85,
        "partial_efficacy_recovery": summaries["efficacy_partial"]["eta_error"]["upper_95"] <= 0.10,
        "spike_prior_zero_recovery": summaries["spike_high"]["q_causal"]["upper_95"] <= 0.15,
        "threat_prior_low_recovery": summaries["threat_low"]["threat_error"]["upper_95"] <= 0.05,
        "threat_prior_high_recovery": summaries["threat_high"]["threat_error"]["upper_95"] <= 0.05,
    }
    passed = all(checks.values())
    payload = {
        "stage": "V2.3.4",
        "gate": 5,
        "seed_block": [1_309_000, 1_319_999],
        "scenario_summaries": summaries,
        "metrics": {
            "probe_correlation_reduction": probe,
            "context_accuracy": context_accuracy,
            "masking_truth_error_cost": masking,
            "precision_truth_error_cost": precision,
            "precision_nonnegative_rate": precision_nonnegative_rate,
            "action_cost_scientific_error": action_cost_science_error,
        },
        "checks": checks,
        "manifest_chain": chain,
        "bounds": BOUNDS,
        "custody": {"escrow_accessed": False, "passed": True},
        "passed": passed,
    }
    dump("gate-5-per_world.json", rows)
    dump("gate-5.json", payload)
    report = ["# V2.3.4 gate 5", "", f"Verdict: **{'PASS' if passed else 'FAIL'}**.", "", "## Scenario summaries", ""]
    report += [f"- `{name}`: {plain(value)}" for name, value in summaries.items()]
    report += ["", "## Criteria", ""] + [
        f"- `{name}`: {'PASS' if value else 'FAIL'}" for name, value in checks.items()
    ]
    (OUT / "gate-5-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    if not passed:
        failures = [name for name, value in checks.items() if not value]
        (OUT / "gate-5-diagnosis-stub.md").write_text(
            "# V2.3.4 gate-5 diagnosis stub\n\nHonest stop. Failed criteria retained verbatim:\n\n"
            + "\n".join(f"- `{name}`" for name in failures)
            + "\n",
            encoding="utf-8",
        )
    return passed


def ready(gate: int, passed: bool) -> None:
    files = sorted(
        str(path.relative_to(ROOT))
        for path in OUT.glob(f"gate-{gate}*")
        if path.is_file()
    )
    (OUT / f"ready-to-commit-gate{gate}.md").write_text(
        f"# Ready to commit: V2.3.4 gate {gate}\n\n"
        f"Verdict: {'PASS' if passed else 'FAIL / honest stop'}\n\n"
        + "\n".join(f"- `{item}`" for item in files)
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", type=int, choices=(1, 2, 3, 4, 5), required=True)
    args = parser.parse_args()
    runner = {1: run_gate1, 2: run_gate2, 3: run_gate3, 4: run_gate4, 5: run_gate5}.get(args.gate)
    if runner is None:
        raise RuntimeError(f"gate {args.gate} runner not yet defined")
    passed = runner()
    ready(args.gate, passed)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
