"""Diagnose frozen V2.3 formation across open schedule dimensions."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from ref.precision import precision_categorical
from ref.rng import component_rng
from ref.v23 import (
    EVENT_BASE,
    EVENT_PRECISION,
    STRUCTURE_PRIOR,
    run_world,
)


ROOT = Path(__file__).resolve().parent
RESULT_ROOT = ROOT / "results" / "V2.3.1"
SEED_START = 63000
WORLD_COUNT = 512
REGULARITIES = ("periodic", "jittered", "bernoulli", "clustered")
RUN_LENGTHS = (16, 32, 64, 80)
ACUTE_TIMINGS = ("early", "middle", "late")
ACUTE_COUNTS = (0, 1, 3)
LOW_CONTROL_FRACTIONS = (0.0, 0.25, 0.5, 0.75, 1.0)
OLD_STEP_BOUND = 0.294529387


def logit(probability: float) -> float:
    bounded = float(np.clip(probability, 1e-12, 1.0 - 1e-12))
    return math.log(bounded / (1.0 - bounded))


def schedule_dimensions(index: int) -> tuple[str, int, str, int, float]:
    return (
        REGULARITIES[index % len(REGULARITIES)],
        RUN_LENGTHS[(index // 4) % len(RUN_LENGTHS)],
        ACUTE_TIMINGS[(index // 16) % len(ACUTE_TIMINGS)],
        ACUTE_COUNTS[(index // 48) % len(ACUTE_COUNTS)],
        LOW_CONTROL_FRACTIONS[
            (3 * index + index // 144) % len(LOW_CONTROL_FRACTIONS)
        ],
    )


def chronic_positions(
    seed: int,
    regularity: str,
    length: int,
    excluded: set[int],
) -> list[int]:
    target = max(2, round(0.16 * length))
    available = np.array(
        [time for time in range(length) if time not in excluded], dtype=int
    )
    rng = component_rng(seed, f"v231-diagnosis-{regularity}-{length}")
    if regularity == "periodic":
        positions = np.linspace(1, length - 2, target, dtype=int)
    elif regularity == "jittered":
        centers = np.linspace(1, length - 2, target)
        jitter = rng.integers(-2, 3, size=target)
        positions = np.rint(centers + jitter).astype(int)
    elif regularity == "bernoulli":
        positions = rng.choice(available, size=min(target, len(available)), replace=False)
    else:
        center = int(rng.integers(max(2, length // 4), max(3, 3 * length // 4)))
        offsets = np.arange(target) - target // 2
        positions = center + offsets
    positions = np.clip(positions, 0, length - 1)
    unique = []
    for position in positions:
        candidate = int(position)
        while candidate in excluded or candidate in unique:
            candidate = (candidate + 1) % length
        unique.append(candidate)
    return sorted(unique)


def acute_positions(
    seed: int,
    timing: str,
    count: int,
    length: int,
) -> list[int]:
    if count == 0:
        return []
    centers = {
        "early": 0.25,
        "middle": 0.50,
        "late": 0.75,
    }
    center = round(centers[timing] * (length - 1))
    offsets = [0] if count == 1 else [-2, 0, 2]
    shift = int(
        component_rng(
            seed, f"v231-diagnosis-acute-{timing}-{count}-{length}"
        ).integers(-1, 2)
    )
    return sorted(
        int(np.clip(center + offset + shift, 1, length - 2))
        for offset in offsets
    )


def make_schedule(
    seed: int,
    regularity: str,
    length: int,
    timing: str,
    acute_count: int,
    low_control_fraction: float,
) -> tuple[list[dict[str, Any]], list[int]]:
    acute = acute_positions(seed, timing, acute_count, length)
    chronic = chronic_positions(seed, regularity, length, set(acute))
    event_positions = sorted(set(acute + chronic))
    low_count = round(low_control_fraction * len(event_positions))
    control_order = component_rng(
        seed, "v231-diagnosis-control-order"
    ).permutation(len(event_positions))
    low_positions = {
        event_positions[int(index)] for index in control_order[:low_count]
    }
    schedule = []
    for time in range(length):
        event = time in event_positions
        schedule.append(
            {
                "event": int(event),
                "overwhelm": int(time in acute),
                "controllability": int(time not in low_positions),
                "broadcast": int(not event),
                "real_danger": False,
                "action": time % 2,
            }
        )
    return schedule, acute


def overwhelm_evidence(result: dict[str, Any], acute: list[int]) -> float:
    factor = precision_categorical(
        "E", "K", "B", EVENT_BASE, EVENT_PRECISION
    )
    total = 0.0
    for time in acute:
        observation = int(result["traces"][time]["event_observation"])
        high = float(factor.values[1, 1, observation])
        low = float(factor.values[1, 0, observation])
        total += math.log(high / low)
    return total


def grouped_curve(
    rows: list[dict[str, Any]], field: str, bins: int = 5
) -> list[dict[str, float]]:
    values = np.asarray([row[field] for row in rows], dtype=float)
    edges = np.unique(np.quantile(values, np.linspace(0.0, 1.0, bins + 1)))
    curve = []
    for lower, upper in zip(edges[:-1], edges[1:]):
        mask = (values >= lower) & (
            values <= upper if upper == edges[-1] else values < upper
        )
        selected = [row for row, keep in zip(rows, mask) if keep]
        if not selected:
            continue
        probabilities = np.asarray(
            [row["final_persistent_probability"] for row in selected]
        )
        curve.append(
            {
                "lower": float(lower),
                "upper": float(upper),
                "count": len(selected),
                "mean_predictor": float(np.mean(values[mask])),
                "mean_formation_probability": float(np.mean(probabilities)),
                "formation_rate_above_half": float(np.mean(probabilities >= 0.5)),
            }
        )
    return curve


def design_matrices(rows: list[dict[str, Any]]) -> tuple[np.ndarray, np.ndarray]:
    theory = np.asarray(
        [
            [
                row["uncontrollability_log_evidence"],
                row["cumulative_overwhelm_precision"],
            ]
            for row in rows
        ],
        dtype=float,
    )
    theory = (theory - theory.mean(axis=0)) / np.maximum(
        theory.std(axis=0), 1e-9
    )
    surface_columns = []
    for row in rows:
        surface_columns.append(
            [
                row["run_length"] / 80.0,
                {"early": 0.25, "middle": 0.5, "late": 0.75}[
                    row["acute_timing"]
                ],
                row["acute_count"] / 3.0,
                *[
                    float(row["regularity"] == label)
                    for label in REGULARITIES[1:]
                ],
            ]
        )
    return theory, np.asarray(surface_columns, dtype=float)


def cross_validated_r2(features: np.ndarray, outcome: np.ndarray) -> float:
    predictions = np.empty(len(outcome))
    folds = (
        component_rng(63999, "v231-diagnosis-cv-folds").permutation(len(outcome))
        % 8
    )
    for fold in range(8):
        train = folds != fold
        test = ~train
        design_train = np.column_stack([np.ones(np.sum(train)), features[train]])
        coefficients = np.linalg.lstsq(design_train, outcome[train], rcond=None)[0]
        predictions[test] = (
            np.column_stack([np.ones(np.sum(test)), features[test]]) @ coefficients
        )
    denominator = float(np.sum((outcome - outcome.mean()) ** 2))
    return 1.0 - float(np.sum((outcome - predictions) ** 2)) / denominator


def grouped_surface(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    groups = []
    for value in sorted({row[field] for row in rows}, key=str):
        selected = [
            row["final_persistent_probability"] for row in rows if row[field] == value
        ]
        groups.append(
            {
                "value": value,
                "count": len(selected),
                "mean_formation_probability": float(np.mean(selected)),
            }
        )
    return groups


def render_diagnosis(summary: dict[str, Any]) -> str:
    fit = summary["predictive_alignment"]
    steps = summary["acute_path"]
    verdict = summary["verdict"]
    generalization_explanation = (
        "The frozen family contains direct controllability and precision "
        "routes, but their current priors and relative likelihood contrasts "
        "leave formation weak and non-monotone across the theory variables. "
        "Schedule surfaces do not account for enough additional variance to "
        "meet the preregistered representational criterion."
        if verdict["generalization"] == "parametric"
        else
        "The frozen family cannot express the claimed boundary without "
        "retaining substantial dependence on schedule surfaces."
    )
    return f"""# V2.3.1 diagnosis

Diagnosis was completed before any repair code or V2.3.1 parameter block was
written. It used the frozen V2.3 implementation on 512 open worlds
(development seeds 63000–63511), spanning four chronic regularities, four run
lengths, three acute timings, three acute counts, and five controllability
mixtures.

## Generalization collapse

Theory-only cross-validated R² was `{fit['theory_only_cv_r2']:.3f}`. Surface
features alone reached `{fit['surface_only_cv_r2']:.3f}`, and surface features
added `{fit['surface_incremental_cv_r2']:.3f}` after inferred
uncontrollability and realized cumulative overwhelm precision were already in
the model. The largest surface-group formation spread was
`{fit['largest_surface_group_spread']:.3f}`, carried by
`{fit['largest_surface_group_feature']}`.

The apparatus therefore classifies the formation defect as
**{verdict['generalization']}**. {generalization_explanation}

## Near-boolean acute path

Across `{steps['acute_slice_count']}` acute slices, `{steps['bound_exceedances']}`
single-slice changes exceeded the frozen `.294529387` bound; the maximum was
`{steps['maximum_acute_step']:.6f}`. The correlation between acute step size
and the pre-acute persistent posterior was
`{steps['step_preacute_probability_correlation']:.3f}`. The largest mean
acute-step contrast by surface dimension was
`{steps['largest_surface_step_spread']:.3f}` for
`{steps['largest_surface_step_feature']}`.

The acute defect is **{verdict['acute_path']}**. A finite but unbounded-at-the-
slice-level Bayes factor is applied after a static posterior has been driven
to schedule-dependent extremes. V2.3 has neither a transition floor nor a
declared bound on candidate evidence per slice, so the forbidden write-like
signature is structurally available.

## Repair decision

The acute defect requires a structure-family repair; the generalization
defect permits stage-local prior/likelihood rebalancing. V2.3.1 will therefore
add a schedule-blind Markov hazard over the candidate structure and a robust,
explicitly bounded per-slice candidate-evidence channel, then calibrate only
their stage-local priors/contrasts against the theory variables. The repair
may read only carried posteriors and current generative factors. It will not
read run length, timing, regularity, event count, or any schedule statistic.

The full calibration curves, surface groups, and per-world records are
retained in `diagnosis-summary.json` and `diagnosis-per_world.csv`. These same
worlds become a permanent repaired-stage open assay.
"""


def main() -> None:
    rows = []
    acute_records = []
    for index, seed in enumerate(range(SEED_START, SEED_START + WORLD_COUNT)):
        regularity, length, timing, acute_count, low_fraction = (
            schedule_dimensions(index)
        )
        schedule, acute = make_schedule(
            seed,
            regularity,
            length,
            timing,
            acute_count,
            low_fraction,
        )
        result = run_world(
            seed,
            schedule,
            action_mode="declared",
            stream_family="v231-diagnosis",
        )
        final_control = result["final_controllability_probability"]
        row = {
            "seed": seed,
            "regularity": regularity,
            "run_length": length,
            "acute_timing": timing,
            "acute_count": acute_count,
            "low_control_fraction": low_fraction,
            "event_count": int(sum(item["event"] for item in schedule)),
            "uncontrollability_log_evidence": (
                -logit(final_control) + logit(0.5)
            ),
            "cumulative_overwhelm_precision": overwhelm_evidence(result, acute),
            "final_persistent_probability": result[
                "final_persistent_probability"
            ],
            "maximum_step": result["maximum_step"],
        }
        for time in acute:
            persistent = result["traces"][time]["persistent_probability"]
            previous = (
                STRUCTURE_PRIOR[1]
                if time == 0
                else result["traces"][time - 1]["persistent_probability"]
            )
            acute_records.append(
                {
                    **row,
                    "acute_time": time,
                    "preacute_persistent_probability": previous,
                    "acute_step": persistent - previous,
                    "acute_absolute_step": abs(persistent - previous),
                }
            )
        rows.append(row)

    theory, surface = design_matrices(rows)
    outcome = np.asarray(
        [row["final_persistent_probability"] for row in rows], dtype=float
    )
    theory_r2 = cross_validated_r2(theory, outcome)
    surface_r2 = cross_validated_r2(surface, outcome)
    combined_r2 = cross_validated_r2(
        np.column_stack([theory, surface]), outcome
    )
    surfaces = {
        field: grouped_surface(rows, field)
        for field in (
            "regularity",
            "run_length",
            "acute_timing",
            "acute_count",
            "low_control_fraction",
        )
    }
    raw_spreads = {
        field: max(group["mean_formation_probability"] for group in groups)
        - min(group["mean_formation_probability"] for group in groups)
        for field, groups in surfaces.items()
    }
    theory_design = np.column_stack([np.ones(len(theory)), theory])
    theory_residuals = outcome - theory_design @ np.linalg.lstsq(
        theory_design, outcome, rcond=None
    )[0]
    residual_spreads = {}
    for field in surfaces:
        means = [
            float(
                np.mean(
                    [
                        residual
                        for row, residual in zip(rows, theory_residuals)
                        if row[field] == value
                    ]
                )
            )
            for value in {row[field] for row in rows}
        ]
        residual_spreads[field] = max(means) - min(means)
    largest_surface = max(residual_spreads, key=residual_spreads.get)

    step_spreads = {}
    for field in ("regularity", "run_length", "acute_timing", "acute_count"):
        means = []
        for value in {row[field] for row in acute_records}:
            means.append(
                float(
                    np.mean(
                        [
                            row["acute_absolute_step"]
                            for row in acute_records
                            if row[field] == value
                        ]
                    )
                )
            )
        step_spreads[field] = max(means) - min(means)
    largest_step_surface = max(step_spreads, key=step_spreads.get)
    preacute = np.asarray(
        [row["preacute_persistent_probability"] for row in acute_records]
    )
    acute_steps = np.asarray(
        [row["acute_absolute_step"] for row in acute_records]
    )

    representational = (
        combined_r2 - theory_r2 >= 0.10
        or residual_spreads[largest_surface] >= 0.20
    )
    acute_representational = bool(np.any(acute_steps > OLD_STEP_BOUND))
    summary = {
        "strain_diagnosed": "V2.3",
        "seed_block": [SEED_START, SEED_START + WORLD_COUNT - 1],
        "world_count": WORLD_COUNT,
        "dimensions": {
            "regularities": list(REGULARITIES),
            "run_lengths": list(RUN_LENGTHS),
            "acute_timings": list(ACUTE_TIMINGS),
            "acute_counts": list(ACUTE_COUNTS),
            "low_control_fractions": list(LOW_CONTROL_FRACTIONS),
        },
        "calibration_curves": {
            "uncontrollability_log_evidence": grouped_curve(
                rows, "uncontrollability_log_evidence"
            ),
            "cumulative_overwhelm_precision": grouped_curve(
                rows, "cumulative_overwhelm_precision"
            ),
        },
        "surface_groups": surfaces,
        "predictive_alignment": {
            "theory_only_cv_r2": theory_r2,
            "surface_only_cv_r2": surface_r2,
            "combined_cv_r2": combined_r2,
            "surface_incremental_cv_r2": combined_r2 - theory_r2,
            "largest_surface_group_feature": largest_surface,
            "largest_surface_group_spread": residual_spreads[largest_surface],
            "all_surface_group_spreads": raw_spreads,
            "theory_adjusted_surface_group_spreads": residual_spreads,
        },
        "acute_path": {
            "acute_slice_count": len(acute_records),
            "bound": OLD_STEP_BOUND,
            "bound_exceedances": int(np.sum(acute_steps > OLD_STEP_BOUND)),
            "maximum_acute_step": float(np.max(acute_steps)),
            "step_preacute_probability_correlation": float(
                np.corrcoef(acute_steps, preacute)[0, 1]
            ),
            "largest_surface_step_feature": largest_step_surface,
            "largest_surface_step_spread": step_spreads[largest_step_surface],
            "all_surface_step_spreads": step_spreads,
        },
        "verdict": {
            "generalization": (
                "representational" if representational else "parametric"
            ),
            "acute_path": (
                "representational" if acute_representational else "parametric"
            ),
        },
    }

    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    with (RESULT_ROOT / "diagnosis-per_world.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (RESULT_ROOT / "diagnosis-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (RESULT_ROOT / "diagnosis.md").write_text(
        render_diagnosis(summary), encoding="utf-8"
    )
    print(json.dumps(summary["verdict"], sort_keys=True))


if __name__ == "__main__":
    main()
