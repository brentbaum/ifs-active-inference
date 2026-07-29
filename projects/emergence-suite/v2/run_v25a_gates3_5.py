"""Run the committed Epoch-A V2.5a format-core gates 3-5."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np

from ref import v24, v243, v25a
from ref.rng import component_rng


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "V2.5a"
PARAMETERS = json.loads(
    (ROOT / "protocols" / "v2.5a-parameters.json").read_text()
)
B_MAX_FORMATION = 3.801426508560692
B_MAX_V24 = 6.704414354964107
B_MAX_MARGINAL = 6.704414354964107
DOSES = tuple(np.linspace(0.0, 1.0, 6))


def _native(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(type(value).__name__)


def _write_json(name: str, value: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(
        json.dumps(value, indent=2, sort_keys=True, default=_native) + "\n",
        encoding="utf-8",
    )


def _observed(observations: list[v24.Observation]) -> int:
    return sum(
        any(value is not None for value in (item.outcome, item.marker, item.root))
        for item in observations
    )


def _dose_row(position: int) -> dict[str, Any]:
    seed = 757000 + position
    level_index = position // 100
    dose = float(DOSES[level_index])
    world = v24.generate_world("context_split", seed, length=96)
    presented = v25a.association_dose_history(
        world["observations"], seed, dose
    )
    score = v25a.score_presentations("context_split", presented)
    tokens = _observed(presented)
    return {
        "position": position,
        "seed": seed,
        "level_index": level_index,
        "association_strength": dose,
        "observed_tokens": tokens,
        "delta_i": score.delta_i,
        "delta_i_per_token": score.delta_i / max(1, tokens),
        "delta_i_per_slice": list(score.delta_i_per_slice),
        "channel_log_evidence": {
            channel: score.channel_scores[channel].log_evidence
            for channel in v25a.CHANNELS
        },
        "increment_identity_error": score.increment_identity_error,
    }


def _matching_row(position: int) -> dict[str, Any]:
    seed = 758000 + position
    level_index = position // 50
    dose = float(DOSES[level_index])
    result = v25a.match_marginal_root_information(
        "context_split",
        "context_split",
        seed,
        base_length=96,
        tolerance=float(
            PARAMETERS["frozen_numeric_criteria"][
                "matching_kl_tolerance_nats"
            ]
        ),
    )
    return {
        "position": position,
        "seed": seed,
        "level_index": level_index,
        "association_strength": dose,
        "target_name": result.target_name,
        "target_kl": result.target_kl,
        "matched_slices": result.matched_slices,
        "matched_kl": result.matched_kl,
        "matching_ratio": result.ratio,
        "matching_censored": result.censored,
        "matching_absolute_kl_error": result.absolute_kl_error,
        "extension_prefix_identity": result.prefix_identity,
    }


def _bridge_row(position: int) -> dict[str, Any]:
    seed = 758500 + position
    record = v24._bank_states()[position]
    return {
        "position": position,
        **v25a.formed_bridge_format_readout(seed, record),
    }


def _misspecification_row(position: int) -> dict[str, Any]:
    seed = 759000 + position
    base_family = v24.FAMILIES[position % len(v24.FAMILIES)]
    world = v24.generate_world(
        base_family,
        seed,
        length=96,
        missingness=0.30 if position % 2 else 0.0,
    )
    observations = list(world["observations"])
    construction = "base_constructor"
    if position % 4 == 0:
        observations = v24._shuffle_marker_association(observations, seed)
        construction = "marginal_product"
    elif position % 4 == 1:
        first = v24.generate_world(
            "continuous_drift", seed, length=48
        )["observations"]
        second = v24.generate_world(
            "change_point", seed, length=48
        )["observations"]
        observations = list(first) + list(second)
        construction = "mixed_temporal"
    comparison = v24.compare_families(observations)
    selected = v24.selected_family(comparison["posterior"])
    presentation = {
        family: v25a.score_presentations(family, observations)
        for family in v24.FAMILIES
    }
    prior = np.asarray([0.5, 0.5], dtype=float)
    target = v25a.categorical_kl(
        v25a.root_posterior(observations, prior), prior
    )
    matched, matched_kl = v25a.scan_root_kl(
        observations, target, 0.01, len(observations), prior
    )
    return {
        "position": position,
        "seed": seed,
        "base_constructor": base_family,
        "construction": construction,
        "selected_family": selected or "tie",
        "family_posterior": comparison["posterior"].tolist(),
        "posterior_entropy": float(
            -np.sum(
                comparison["posterior"]
                * np.log(np.maximum(comparison["posterior"], 1e-300))
            )
        ),
        "delta_i_by_candidate": {
            family: presentation[family].delta_i
            for family in v24.FAMILIES
        },
        "increment_identity_error_maximum": max(
            presentation[family].increment_identity_error
            for family in v24.FAMILIES
        ),
        "matching_target_kl": target,
        "matched_slices_within_observed_history": matched,
        "matched_kl": matched_kl,
        "matching_censored_within_observed_history": matched is None,
        "invented_true_family_label": False,
    }


TASKS: dict[str, Callable[[int], dict[str, Any]]] = {
    "dose": _dose_row,
    "matching": _matching_row,
    "bridge": _bridge_row,
    "misspecification": _misspecification_row,
}


def _worker(task: str, start: int, end: int, output: Path) -> None:
    rows = [TASKS[task](position) for position in range(start, end)]
    output.write_text(
        json.dumps(rows, sort_keys=True, default=_native) + "\n",
        encoding="utf-8",
    )


def _parallel(task: str, count: int) -> list[dict[str, Any]]:
    workers = 8
    boundaries = np.linspace(0, count, workers + 1, dtype=int)
    jobs = []
    for worker in range(workers):
        output = OUT / f".gate3-{task}-worker-{worker}.json"
        if output.exists():
            output.unlink()
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "worker",
            "--task",
            task,
            "--start",
            str(int(boundaries[worker])),
            "--end",
            str(int(boundaries[worker + 1])),
            "--output",
            str(output),
        ]
        jobs.append((worker, output, subprocess.Popen(command, cwd=ROOT)))
    remaining = {worker: process for worker, _, process in jobs}
    while remaining:
        time.sleep(2)
        for worker, process in list(remaining.items()):
            status = process.poll()
            if status is None:
                continue
            if status:
                raise RuntimeError(f"{task} worker {worker} exited {status}")
            del remaining[worker]
    rows = []
    for _, output, _ in jobs:
        rows.extend(json.loads(output.read_text()))
        output.unlink()
    rows.sort(key=lambda row: row["position"])
    if [row["position"] for row in rows] != list(range(count)):
        raise ValueError(f"{task} worker ledger incomplete")
    return rows


def _bootstrap_mean(
    values: list[float], seed: int, component: str
) -> tuple[float, float, float]:
    array = np.asarray(values, dtype=float)
    rng = component_rng(seed, component)
    means = np.empty(10000)
    for index in range(len(means)):
        means[index] = float(
            rng.choice(array, size=len(array), replace=True).mean()
        )
    low, high = np.quantile(means, [0.025, 0.975])
    return float(array.mean()), float(low), float(high)


def _wilson(successes: int, total: int) -> tuple[float, float, float]:
    p = successes / total
    z = 1.96
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half = (
        z
        * math.sqrt(p * (1.0 - p) / total + z * z / (4 * total * total))
        / denominator
    )
    return p, center - half, center + half


def _isotonic(values: list[float]) -> list[float]:
    blocks = [[float(value), 1] for value in values]
    index = 0
    while index < len(blocks) - 1:
        if blocks[index][0] <= blocks[index + 1][0]:
            index += 1
            continue
        total = blocks[index][1] + blocks[index + 1][1]
        mean = (
            blocks[index][0] * blocks[index][1]
            + blocks[index + 1][0] * blocks[index + 1][1]
        ) / total
        blocks[index : index + 2] = [[mean, total]]
        index = max(0, index - 1)
    output = []
    for value, count in blocks:
        output.extend([value] * count)
    return output


def _dose_slope_interval(rows: list[dict[str, Any]]) -> tuple[float, float, float]:
    groups = [
        np.asarray(
            [
                row["delta_i_per_token"]
                for row in rows
                if row["level_index"] == level
            ],
            dtype=float,
        )
        for level in range(6)
    ]
    x = np.asarray(DOSES, dtype=float)

    def slope(means: np.ndarray) -> float:
        return float(np.polyfit(x, means, 1)[0])

    point = slope(np.asarray([group.mean() for group in groups]))
    rng = component_rng(757000, "v25a-gate3-dose-slope-bootstrap")
    values = np.empty(10000)
    for index in range(len(values)):
        means = np.asarray(
            [
                rng.choice(group, size=len(group), replace=True).mean()
                for group in groups
            ]
        )
        values[index] = slope(means)
    low, high = np.quantile(values, [0.025, 0.975])
    return point, float(low), float(high)


def gate3() -> bool:
    dose_rows = _parallel("dose", 600)
    _write_json("gate-3-dose-per_world.json", dose_rows)
    dose_means = [
        float(
            np.mean(
                [
                    row["delta_i_per_token"]
                    for row in dose_rows
                    if row["level_index"] == level
                ]
            )
        )
        for level in range(6)
    ]
    isotonic = _isotonic(dose_means)
    slope_interval = _dose_slope_interval(dose_rows)

    matching_rows = _parallel("matching", 300)
    _write_json("gate-3-matching-per_world.json", matching_rows)
    uncensored = [
        row for row in matching_rows if not row["matching_censored"]
    ]
    censor_interval = _wilson(
        len(matching_rows) - len(uncensored), len(matching_rows)
    )
    dose_medians = [
        float(
            np.median(
                [
                    row["matching_ratio"]
                    for row in matching_rows
                    if row["level_index"] == level
                    and not row["matching_censored"]
                ]
            )
        )
        for level in range(6)
    ]

    bridge_rows = _parallel("bridge", 120)
    _write_json("gate-3-bridge-per_world.json", bridge_rows)
    bridge_uncensored = [
        row for row in bridge_rows if not row["matching_censored"]
    ]
    bridge_interval = _bootstrap_mean(
        [row["joint_minus_marginal"] for row in bridge_uncensored],
        758500,
        "v25a-gate3-bridge-difference",
    )
    stratum_counts = {
        name: sum(row["stratum"] == name for row in bridge_rows)
        for name in ("moderate", "strong", "very_strong")
    }

    misspecification_rows = _parallel("misspecification", 240)
    _write_json(
        "gate-3-misspecification-per_world.json", misspecification_rows
    )
    match_tolerance = float(
        PARAMETERS["frozen_numeric_criteria"][
            "matching_kl_tolerance_nats"
        ]
    )
    bridge_sesoi = float(
        PARAMETERS["frozen_numeric_criteria"][
            "bridge_root_movement_sesoi"
        ]
    )
    checks = {
        "assay1_raw_means_monotone": all(
            right >= left - 1e-12
            for left, right in zip(dose_means, dose_means[1:])
        ),
        "assay1_isotonic_fit_no_adjustment": max(
            abs(left - right)
            for left, right in zip(dose_means, isotonic)
        )
        <= 1e-12,
        "assay1_slope_lower_ci_gt_0": slope_interval[1] > 0.0,
        "assay1_increment_identity": max(
            row["increment_identity_error"] for row in dose_rows
        )
        <= 1e-10,
        "assay2_matching_within_frozen_tolerance": all(
            row["matching_absolute_kl_error"] <= match_tolerance
            for row in uncensored
        ),
        "assay2_all_prefixes_identical": all(
            row["extension_prefix_identity"] for row in matching_rows
        ),
        "assay2_median_ratio_monotone": all(
            right >= left - 1e-12
            for left, right in zip(dose_medians, dose_medians[1:])
        ),
        "assay3_all_120_information_matched": len(bridge_uncensored) == 120,
        "assay3_joint_minus_marginal_mean_ge_sesoi": (
            bridge_interval[0] >= bridge_sesoi
        ),
        "assay3_joint_minus_marginal_lower_ci_gt_0": (
            bridge_interval[1] > 0.0
        ),
        "assay3_exact_per_slice_decomposition": max(
            row["decomposition_error"] for row in bridge_uncensored
        )
        <= 1e-10,
        "assay3_G_fixed_exact_zero": max(
            abs(row["G_fixed_difference"]) for row in bridge_rows
        )
        <= 1e-10,
        "assay3_zero_association_exact_zero": max(
            abs(row["zero_association_difference"]) for row in bridge_rows
        )
        <= 1e-10,
        "assay3_stratum_balance_40_40_40": stratum_counts
        == {"moderate": 40, "strong": 40, "very_strong": 40},
        "assay4_descriptive_semantics": max(
            row["increment_identity_error_maximum"]
            for row in misspecification_rows
        )
        <= 1e-10
        and not any(
            row["invented_true_family_label"] for row in misspecification_rows
        ),
    }
    failures = [name for name, value in checks.items() if not value]
    result = {
        "stage": "V2.5a",
        "gate": 3,
        "passed": not failures,
        "checks": checks,
        "blocking_failures": failures,
        "assay1_dose_response": {
            "doses": list(DOSES),
            "worlds_per_level": 100,
            "mean_delta_i_per_token": dose_means,
            "isotonic_fit": isotonic,
            "slope_interval": slope_interval,
        },
        "assay2_information_matching": {
            "world_count": 300,
            "uncensored_count": len(uncensored),
            "censoring_rate_wilson": censor_interval,
            "median_m_star_over_n_by_dose": dose_medians,
            "maximum_uncensored_absolute_kl_error": max(
                row["matching_absolute_kl_error"] for row in uncensored
            ),
        },
        "assay3_formed_p_bridge": {
            "world_count": 120,
            "uncensored_count": len(bridge_uncensored),
            "joint_minus_matched_marginal_interval": bridge_interval,
            "frozen_sesoi": bridge_sesoi,
            "stratum_counts": stratum_counts,
            "maximum_decomposition_error": max(
                row["decomposition_error"] for row in bridge_uncensored
            ),
        },
        "assay4_misspecification": {
            "world_count": 240,
            "classification": "DESCRIPTIVE_ONLY",
            "mean_posterior_entropy": float(
                np.mean(
                    [
                        row["posterior_entropy"]
                        for row in misspecification_rows
                    ]
                )
            ),
            "censored_within_observed_history": sum(
                row["matching_censored_within_observed_history"]
                for row in misspecification_rows
            ),
        },
        "B_max_inherited_formation": B_MAX_FORMATION,
        "B_max_v24_common_emissions": B_MAX_V24,
        "B_max_v25a_marginal_accounting": B_MAX_MARGINAL,
    }
    _write_json("gate-3.json", result)
    (OUT / "gate-3-report.md").write_text(
        "# V2.5a Gate 3 — format-core open assays\n\n"
        f"Outcome: **{'PASS' if not failures else 'FAIL'}**. Blocking "
        f"failures: `{failures}`.\n\n"
        f"Dose means `{dose_means}`; slope interval `{slope_interval}`.\n\n"
        f"Matching censoring `{censor_interval}`; median m*/n `{dose_medians}`.\n\n"
        f"Bridge joint-minus-matched-marginal `{bridge_interval}` against "
        f"SESOI `{bridge_sesoi}`; strata `{stratum_counts}`.\n\n"
        f"`B_max_inherited_formation = {B_MAX_FORMATION}`; "
        f"`B_max_v24_common_emissions = {B_MAX_V24}`; "
        f"`B_max_v25a_marginal_accounting = {B_MAX_MARGINAL}`.\n",
        encoding="utf-8",
    )
    if failures:
        (OUT / "gate-3-diagnosis-stub.md").write_text(
            "# V2.5a Gate-3 honest stop\n\n"
            f"Blocking failures retained verbatim: `{failures}`.\n",
            encoding="utf-8",
        )
    return not failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("gate3", "worker"))
    parser.add_argument("--task", choices=tuple(TASKS))
    parser.add_argument("--start", type=int)
    parser.add_argument("--end", type=int)
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.phase == "worker":
        _worker(args.task, args.start, args.end, Path(args.output))
        return 0
    return 0 if gate3() else 1


if __name__ == "__main__":
    raise SystemExit(main())

