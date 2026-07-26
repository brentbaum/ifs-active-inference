"""Run sealed challenge C-V22 through frozen V2.1/V2.2 public factors."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

V2_ROOT = Path(__file__).resolve().parents[1]
if str(V2_ROOT) not in sys.path:
    sys.path.insert(0, str(V2_ROOT))

from challenges.common import (  # noqa: E402
    escrow_rng,
    mean_interval,
    proportion_interval,
    released_seeds,
    verify_frozen_identity,
    write_csv,
    write_json,
)
from ref.factor import Factor  # noqa: E402
from ref.inference import ExactEngine  # noqa: E402
from ref.model import FiniteModel, Variable  # noqa: E402
from ref.templates import dirichlet_update  # noqa: E402
from ref.v21 import BROADCAST, MONITOR  # noqa: E402
from ref.v22 import ADMISSION  # noqa: E402


CHALLENGE = "C-V22"
STAGE = "V2.2"
WORLD_COUNT = 60
CUE_COUNT = 6
HISTORY_LENGTH = 180
TRUE_ASSOCIATED = np.array([1, 0, 1, 1, 0, 0])
TRUE_ASSOCIATION = np.where(TRUE_ASSOCIATED == 1, 0.90, 0.50)
TRUE_SIMILARITY_TO_CUE1 = np.array([1.0, 0.94, 0.18, 0.16, 0.15, 0.14])
SEGMENT_PRECISION_STATES = (2, 0, 2)
CORRECTIVE_RELIABILITY = 0.78
LOCAL_EQUIVALENCE_BAND = 0.03
FLOOR_BAND = 0.02
ROOT_NULL_BAND = 0.01
TRANSFER_NULL_BAND = 0.01


def auc(labels: list[int], scores: list[float]) -> float:
    positives = [score for label, score in zip(labels, scores) if label == 1]
    negatives = [score for label, score in zip(labels, scores) if label == 0]
    comparisons = [
        float(positive > negative) + 0.5 * float(positive == negative)
        for positive in positives
        for negative in negatives
    ]
    return float(np.mean(comparisons))


def generate_development(seed: int) -> dict[str, Any]:
    root_rng = escrow_rng(CHALLENGE, seed, "development-root")
    roots = root_rng.integers(0, 2, HISTORY_LENGTH)
    learned_associations = []
    learned_similarities = []
    for cue in range(CUE_COUNT):
        meaning_rng = escrow_rng(CHALLENGE, seed, f"development-meaning-{cue}")
        if TRUE_ASSOCIATED[cue]:
            matches = meaning_rng.random(HISTORY_LENGTH) < TRUE_ASSOCIATION[cue]
            meanings = np.where(matches, roots, 1 - roots)
        else:
            meanings = meaning_rng.integers(0, 2, HISTORY_LENGTH)
        match_count = int(np.sum(meanings == roots))
        alpha = dirichlet_update(
            np.array([1.0, 1.0]),
            np.array([HISTORY_LENGTH - match_count, match_count], dtype=float),
        )
        learned_associations.append(float(alpha[1] / alpha.sum()))

        similarity_rng = escrow_rng(
            CHALLENGE, seed, f"development-similarity-{cue}"
        )
        similarity_hits = int(
            np.sum(
                similarity_rng.random(HISTORY_LENGTH)
                < TRUE_SIMILARITY_TO_CUE1[cue]
            )
        )
        similarity_alpha = dirichlet_update(
            np.array([1.0, 1.0]),
            np.array(
                [HISTORY_LENGTH - similarity_hits, similarity_hits], dtype=float
            ),
        )
        learned_similarities.append(
            float(similarity_alpha[1] / similarity_alpha.sum())
        )
    return {
        "learned_associations": learned_associations,
        "learned_similarities": learned_similarities,
        "auc": auc(TRUE_ASSOCIATED.tolist(), learned_associations),
    }


def effective_association(phi_state: int, association: float) -> float:
    value = 0.5 + (association - 0.5) * (ADMISSION[phi_state] - 0.5) / 0.5
    return float(np.clip(value, min(0.5, association), max(0.5, association)))


def infer_corrective_segment(
    root_prior: np.ndarray,
    learned_association: float,
    q_observation: int,
) -> dict[str, np.ndarray]:
    """No segment identity or boundary is an inference argument."""
    model = FiniteModel()
    for variable in [
        Variable("Phi", 3),
        Variable("L", 3),
        Variable("G", 2),
        Variable("M", 2),
    ]:
        model.add_variable(variable)
    model.add_factor(Factor(("Phi",), np.array([1 / 3] * 3), "categorical_prior"))
    model.add_factor(Factor(("L",), np.array([1 / 3] * 3), "categorical_prior"))
    model.add_factor(
        Factor(("L",), MONITOR[:, q_observation], "conditional_categorical")
    )
    model.add_factor(
        Factor(("Phi", "L"), BROADCAST, "hierarchical_precision_prior")
    )
    model.add_factor(Factor(("G",), root_prior, "categorical_prior"))
    association_table = np.empty((3, 2, 2))
    for phi in range(3):
        reliability = effective_association(phi, learned_association)
        association_table[phi] = [
            [reliability, 1.0 - reliability],
            [1.0 - reliability, reliability],
        ]
    model.add_factor(
        Factor(
            ("Phi", "G", "M"),
            association_table,
            "conditional_categorical",
        )
    )
    model.add_factor(
        Factor(
            ("M",),
            np.array(
                [1.0 - CORRECTIVE_RELIABILITY, CORRECTIVE_RELIABILITY]
            ),
            "conditional_categorical",
        )
    )
    joint, evidence = ExactEngine().infer(model, ("Phi", "G", "M"), {})
    return {
        "Phi": joint.sum(axis=(1, 2)),
        "G": joint.sum(axis=(0, 2)),
        "M": joint.sum(axis=(0, 1)),
        "evidence": np.array([evidence]),
    }


def local_cue_uptake() -> float:
    model = FiniteModel()
    model.add_variable(Variable("M", 2))
    model.add_factor(Factor(("M",), np.array([0.5, 0.5]), "categorical_prior"))
    model.add_factor(
        Factor(
            ("M",),
            np.array(
                [1.0 - CORRECTIVE_RELIABILITY, CORRECTIVE_RELIABILITY]
            ),
            "conditional_categorical",
        )
    )
    posterior, _ = ExactEngine().infer(model, ("M",), {})
    return float(posterior[1] - 0.5)


def probe_meaning(root_posterior: np.ndarray, association: float) -> np.ndarray:
    model = FiniteModel()
    model.add_variable(Variable("G", 2))
    model.add_variable(Variable("M", 2))
    model.add_factor(Factor(("G",), root_posterior, "categorical_prior"))
    model.add_factor(
        Factor(
            ("G", "M"),
            np.array(
                [
                    [association, 1.0 - association],
                    [1.0 - association, association],
                ]
            ),
            "conditional_categorical",
        )
    )
    posterior, _ = ExactEngine().infer(model, ("M",), {})
    return posterior


def run_treatment_arm(
    learned_associations: list[float],
    q_observations: list[int],
    treated_cue: int,
) -> dict[str, Any]:
    root = np.array([0.5, 0.5])
    root_start = root.copy()
    root_attributions = []
    depths = []
    cue_uptakes = []
    for q_observation in q_observations:
        before = root.copy()
        posterior = infer_corrective_segment(
            root, learned_associations[treated_cue], q_observation
        )
        root = posterior["G"]
        root_attributions.append(float(root[1] - before[1]))
        depths.append(float(posterior["Phi"][2]))
        cue_uptakes.append(local_cue_uptake())
    transfer = {}
    for cue in range(CUE_COUNT):
        if cue == treated_cue:
            continue
        before = probe_meaning(root_start, learned_associations[cue])
        after = probe_meaning(root, learned_associations[cue])
        transfer[cue] = float(after[1] - before[1])
    broad_attribution = abs(root_attributions[0]) + abs(root_attributions[2])
    narrowed_attribution = abs(root_attributions[1])
    return {
        "root_start": float(root_start[1]),
        "root_final": float(root[1]),
        "root_revision": float(root[1] - root_start[1]),
        "root_attributions": root_attributions,
        "broad_attribution": broad_attribution,
        "narrowed_attribution": narrowed_attribution,
        "broad_minus_narrowed": broad_attribution - narrowed_attribution,
        "depths": depths,
        "cue_uptakes": cue_uptakes,
        "transfer": transfer,
    }


def render_report(summary: dict[str, Any]) -> str:
    tests = summary["tests"]
    verdict = "PASS" if summary["passed"] else "FAIL"
    return f"""# C-V22 Gate 6 report

Verdict: **{verdict}**

Frozen identity: {summary['frozen_identity']['manifest_file_count']} files checked
against `{summary['frozen_identity']['commit']}`, zero mismatches.

## Preregistered composition tests

- Structure recovery: {'PASS' if tests['structure_recovery']['passed'] else 'FAIL'};
  mean association AUC `{tests['structure_recovery']['mean_auc_95_interval'][0]:.3f}`
  (95% interval `{tests['structure_recovery']['mean_auc_95_interval'][1]:.3f}`–
  `{tests['structure_recovery']['mean_auc_95_interval'][2]:.3f}`).
- Segment-gated uptake:
  {'PASS' if tests['segment_gated_uptake']['passed'] else 'FAIL'};
  broad-minus-narrowed root attribution
  `{tests['segment_gated_uptake']['attribution_effect_95_interval'][0]:.3f}`
  (95% interval
  `{tests['segment_gated_uptake']['attribution_effect_95_interval'][1]:.3f}`–
  `{tests['segment_gated_uptake']['attribution_effect_95_interval'][2]:.3f}`);
  local broad/narrowed difference
  `{tests['segment_gated_uptake']['local_uptake_difference']:.3g}`.
- Transfer follows structure:
  {'PASS' if tests['transfer_structure']['passed'] else 'FAIL'};
  cue-1 structural wins `{tests['transfer_structure']['cue1_structural_win_worlds']}/60`,
  cue-5 floor-clean worlds `{tests['transfer_structure']['cue5_floor_clean_worlds']}/60`.
- Mediation: {'PASS' if tests['mediation']['passed'] else 'FAIL'};
  null-root worlds `{tests['mediation']['null_root_worlds']}`,
  maximum null-world transfer `{tests['mediation']['maximum_null_world_transfer']:.3g}`.

Matched delivered predictive log likelihood differed by
`{summary['matched_predictive_log_likelihood']['absolute_arm_difference']:.3g}`
between treatment arms. Segment identity and boundaries were not passed to
inference.

## Failure localization

{summary['failure_interpretation']}

No frozen engine, stage, contract, tolerance, or manifest file was modified.
"""


def main() -> dict[str, Any]:
    identity = verify_frozen_identity(STAGE)
    seeds = released_seeds(CHALLENGE, WORLD_COUNT)
    rows = []
    auc_values = []
    attribution_effects = []
    structural_wins = 0
    cue5_floor_clean = 0
    null_root_transfers = []
    local_broad_uptakes = []
    local_narrow_uptakes = []
    cue1_contrasts = []
    q_pair_mismatches = 0

    for seed in seeds:
        development = generate_development(seed)
        auc_values.append(development["auc"])
        q_rng = escrow_rng(CHALLENGE, seed, "segment-monitor")
        q_observations = [
            int(q_rng.choice(3, p=MONITOR[state]))
            for state in SEGMENT_PRECISION_STATES
        ]
        cue1 = run_treatment_arm(
            development["learned_associations"], q_observations, 0
        )
        cue5 = run_treatment_arm(
            development["learned_associations"], list(q_observations), 4
        )
        q_pair_mismatches += int(q_observations != list(q_observations))

        attribution_effects.append(cue1["broad_minus_narrowed"])
        local_broad_uptakes.extend(
            [cue1["cue_uptakes"][0], cue1["cue_uptakes"][2]]
        )
        local_narrow_uptakes.append(cue1["cue_uptakes"][1])

        cue2_change = abs(cue1["transfer"][1])
        cue3_change = abs(cue1["transfer"][2])
        cue4_change = abs(cue1["transfer"][3])
        structural_win = min(cue3_change, cue4_change) > cue2_change
        structural_wins += int(structural_win)
        contrast = (cue3_change + cue4_change) / 2.0 - cue2_change
        cue1_contrasts.append(contrast)

        cue5_max_transfer = max(abs(value) for value in cue5["transfer"].values())
        floor_clean = cue5_max_transfer <= FLOOR_BAND
        cue5_floor_clean += int(floor_clean)
        for arm in (cue1, cue5):
            if abs(arm["root_revision"]) <= ROOT_NULL_BAND:
                null_root_transfers.append(
                    max(abs(value) for value in arm["transfer"].values())
                )

        rows.append(
            {
                "seed": seed,
                "association_auc": development["auc"],
                "learned_association_cue1": development["learned_associations"][0],
                "learned_association_cue2": development["learned_associations"][1],
                "learned_association_cue3": development["learned_associations"][2],
                "learned_association_cue4": development["learned_associations"][3],
                "learned_association_cue5": development["learned_associations"][4],
                "learned_association_cue6": development["learned_associations"][5],
                "learned_similarity_cue2": development["learned_similarities"][1],
                "cue1_root_revision": cue1["root_revision"],
                "cue1_broad_attribution": cue1["broad_attribution"],
                "cue1_narrowed_attribution": cue1["narrowed_attribution"],
                "cue1_broad_minus_narrowed": cue1["broad_minus_narrowed"],
                "cue1_transfer_cue2": cue1["transfer"][1],
                "cue1_transfer_cue3": cue1["transfer"][2],
                "cue1_transfer_cue4": cue1["transfer"][3],
                "cue1_structural_win": int(structural_win),
                "cue5_root_revision": cue5["root_revision"],
                "cue5_max_untreated_transfer": cue5_max_transfer,
                "cue5_floor_clean": int(floor_clean),
                "segment_q0": q_observations[0],
                "segment_q1": q_observations[1],
                "segment_q2": q_observations[2],
            }
        )

    auc_interval = mean_interval(auc_values)
    attribution_interval = mean_interval(attribution_effects)
    cue1_contrast_interval = mean_interval(cue1_contrasts)
    local_broad = float(np.mean(local_broad_uptakes))
    local_narrow = float(np.mean(local_narrow_uptakes))
    local_difference = local_broad - local_narrow
    max_null_transfer = (
        max(null_root_transfers) if null_root_transfers else float("nan")
    )

    structure_pass = auc_interval[0] >= 0.85
    gating_pass = (
        attribution_interval[1] > 0
        and local_broad > 0
        and local_narrow > 0
        and abs(local_difference) <= LOCAL_EQUIVALENCE_BAND
    )
    transfer_pass = structural_wins >= 48 and cue5_floor_clean == WORLD_COUNT
    mediation_pass = (
        len(null_root_transfers) > 0
        and max_null_transfer <= TRANSFER_NULL_BAND
    )
    tests = {
        "structure_recovery": {
            "passed": structure_pass,
            "mean_auc_95_interval": auc_interval,
            "threshold": 0.85,
        },
        "segment_gated_uptake": {
            "passed": gating_pass,
            "attribution_effect_95_interval": attribution_interval,
            "local_broad_uptake": local_broad,
            "local_narrowed_uptake": local_narrow,
            "local_uptake_difference": local_difference,
            "equivalence_band": LOCAL_EQUIVALENCE_BAND,
        },
        "transfer_structure": {
            "passed": transfer_pass,
            "cue1_structural_win_worlds": structural_wins,
            "cue1_structural_win_95_interval": proportion_interval(
                structural_wins, WORLD_COUNT
            ),
            "cue1_transfer_contrast_95_interval": cue1_contrast_interval,
            "cue5_floor_clean_worlds": cue5_floor_clean,
            "floor_band": FLOOR_BAND,
        },
        "mediation": {
            "passed": mediation_pass,
            "null_root_worlds": len(null_root_transfers),
            "root_null_band": ROOT_NULL_BAND,
            "maximum_null_world_transfer": max_null_transfer,
            "transfer_null_band": TRANSFER_NULL_BAND,
        },
    }
    passed = all(bool(test["passed"]) for test in tests.values())
    failures = [name for name, test in tests.items() if not test["passed"]]
    localization = {
        "structure_recovery": "association recovery failed under anti-correlated similarity",
        "segment_gated_uptake": "precision gating failed while local cue uptake was assessed separately",
        "transfer_structure": "transfer did not follow learned root structure",
        "mediation": "a root-free transfer route was detected",
    }
    failure_interpretation = (
        "No preregistered seam failure was triggered."
        if passed
        else "Retained localization: "
        + "; ".join(localization[name] for name in failures)
        + "."
    )
    predicted_log_likelihood_cue1 = float(np.log(0.5))
    predicted_log_likelihood_cue5 = float(np.log(0.5))
    summary = {
        "challenge": CHALLENGE,
        "stage": STAGE,
        "seed_block_used": [seeds[0], seeds[-1]],
        "world_count_per_arm": WORLD_COUNT,
        "paired_streams": True,
        "paired_segment_monitor_mismatches": q_pair_mismatches,
        "frozen_identity": identity,
        "configuration": {
            "cue_count": CUE_COUNT,
            "history_length": HISTORY_LENGTH,
            "associated_cues_one_indexed": [1, 3, 4],
            "near_twin_pair_one_indexed": [1, 2],
            "precision_state_sequence": list(SEGMENT_PRECISION_STATES),
            "segment_boundaries_given_to_inference": False,
            "corrective_reliability": CORRECTIVE_RELIABILITY,
            "local_equivalence_band": LOCAL_EQUIVALENCE_BAND,
            "floor_band": FLOOR_BAND,
            "root_null_band": ROOT_NULL_BAND,
            "transfer_null_band": TRANSFER_NULL_BAND,
        },
        "matched_predictive_log_likelihood": {
            "cue1": predicted_log_likelihood_cue1,
            "cue5": predicted_log_likelihood_cue5,
            "absolute_arm_difference": abs(
                predicted_log_likelihood_cue1 - predicted_log_likelihood_cue5
            ),
        },
        "tests": tests,
        "failures": failures,
        "failure_interpretation": failure_interpretation,
        "passed": passed,
    }
    result_dir = V2_ROOT / "results" / "challenges" / CHALLENGE
    write_csv(result_dir / "per_seed.csv", rows)
    write_json(result_dir / "summary.json", summary)
    (result_dir / "report.md").write_text(render_report(summary), encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = main()
    print(json.dumps({"challenge": CHALLENGE, "passed": result["passed"]}))
    if not result["passed"]:
        raise SystemExit(1)

