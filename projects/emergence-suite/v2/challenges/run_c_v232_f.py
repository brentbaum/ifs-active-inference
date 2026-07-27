"""Run revealed C-V232-F against the frozen c67e853 formation stage."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from challenges.c_v232_f_independent import independent_log_joint  # noqa: E402
from ref.statistics import ece_binary  # noqa: E402
from ref.v232_formation import (  # noqa: E402
    LABELS,
    PRIOR,
    SUPPORT,
    SUPPORT_INDEX,
    score_history,
    slice_distribution,
)


CHALLENGE = "C-V232-F"
FREEZE_COMMIT = "c67e853"
FIRST_SEED = 813101
WORLD_COUNT = 200
RESULT_DIR = ROOT / "results" / "challenges" / CHALLENGE
MANIFEST_REL = (
    "projects/emergence-suite/v2/results/"
    "V2.3.2-formation/freeze-manifest.json"
)
ANALYTIC_BOUND = 3.801426508560692
ENUMERATION_TOLERANCE = 1e-10


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_rng(seed: int, component: str) -> np.random.Generator:
    digest = hashlib.sha256(
        f"{CHALLENGE}:{seed}:{component}".encode()
    ).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "big"))


def verify_frozen_identity() -> dict[str, Any]:
    committed_bytes = subprocess.check_output(
        ["git", "show", f"{FREEZE_COMMIT}:{MANIFEST_REL}"], cwd=REPO
    )
    committed = json.loads(committed_bytes)
    local_path = ROOT / "results/V2.3.2-formation/freeze-manifest.json"
    if local_path.read_bytes() != committed_bytes:
        raise RuntimeError("local formation manifest differs from c67e853")
    mismatches = []
    for relative, expected in committed["files"].items():
        path = ROOT / relative
        actual = sha256(path) if path.is_file() else None
        if actual != expected:
            mismatches.append(
                {"path": relative, "expected": expected, "actual": actual}
            )
    if mismatches:
        raise RuntimeError(f"frozen identity mismatch: {mismatches}")
    frozen_bound = json.loads(
        (
            ROOT
            / "results/V2.3.2-formation/"
            "frozen-one-slice-sign-table-summary.json"
        ).read_text()
    )["analytic_per_slice_log_bf_bound"]
    if frozen_bound != ANALYTIC_BOUND:
        raise RuntimeError("frozen analytic bound mismatch")
    return {
        "commit": FREEZE_COMMIT,
        "manifest_sha256": hashlib.sha256(committed_bytes).hexdigest(),
        "verified_file_count": len(committed["files"]),
        "mismatches": mismatches,
        "analytic_bound": frozen_bound,
    }


def proportion_interval(successes: int, total: int) -> tuple[float, float, float]:
    probability = successes / total
    denominator = 1.0 + 1.96**2 / total
    center = (probability + 1.96**2 / (2 * total)) / denominator
    half = (
        1.96
        * math.sqrt(
            probability * (1.0 - probability) / total
            + 1.96**2 / (4.0 * total**2)
        )
        / denominator
    )
    return probability, center - half, center + half


def mean_interval(
    values: list[float], component: str
) -> tuple[float, float, float]:
    array = np.asarray(values, dtype=float)
    means = np.empty(4000)
    rng = stable_rng(FIRST_SEED, component)
    for index in range(len(means)):
        means[index] = rng.choice(
            array, size=len(array), replace=True
        ).mean()
    low, high = np.quantile(means, [0.025, 0.975])
    return float(array.mean()), float(low), float(high)


def configuration(
    *,
    event: bool,
    precision: str = "ordinary",
    control: str = "high",
    broadcast: str = "integrated",
    real_danger: bool = False,
) -> dict[str, Any]:
    return {
        "event": event,
        "precision": precision,
        "control": control,
        "broadcast": broadcast,
        "real_danger": real_danger,
    }


def sample_observation(
    seed: int,
    component: str,
    truth: str,
    config: dict[str, Any],
) -> tuple[int, int, int]:
    row = slice_distribution(truth, **config)
    index = int(
        stable_rng(seed, component).choice(len(row), p=row)
    )
    return SUPPORT[index]


def score_world(
    seed: int,
    cell: str,
    truth: str,
    observations: list[tuple[int, int, int]],
    configurations: list[dict[str, Any]],
    *,
    triplet: int | None = None,
    variant: str = "",
) -> tuple[dict[str, Any], dict[str, Any]]:
    result = score_history(observations, configurations)
    posterior = result["posterior"]
    selected_index = int(np.argmax(posterior))
    selected = LABELS[selected_index]
    competing = [
        float(value)
        for index, value in enumerate(result["log_joint"])
        if index != selected_index
    ]
    winning_margin = float(
        result["log_joint"][selected_index] - max(competing)
    )
    step_changes = []
    slice_max_log_bfs = []
    prior = PRIOR.copy()
    for detail, state in zip(result["contributions"], result["states"]):
        current = state.posterior_store["H_formation"]
        step_changes.append(float(np.max(np.abs(current - prior))))
        prior = current
        slice_max_log_bfs.append(
            max(abs(value) for value in detail["pairwise_log_bf"].values())
        )
    formation_truth = int(truth == "P")
    p_probability = float(posterior[2])
    high_or_integrated = any(
        item["control"] == "high" or item["broadcast"] == "integrated"
        for item in configurations
        if item["event"]
    )
    row = {
        "seed": seed,
        "cell": cell,
        "triplet": "" if triplet is None else triplet,
        "variant": variant,
        "length": len(configurations),
        "event_count": sum(item["event"] for item in configurations),
        "truth": truth,
        "formation_truth": formation_truth,
        "selected": selected,
        "T_probability": float(posterior[0]),
        "D_probability": float(posterior[1]),
        "P_probability": p_probability,
        "winning_log_evidence": winning_margin,
        "formation_selected": int(selected == "P"),
        "high_or_integrated": int(high_or_integrated),
        "false_P_eligible": int(high_or_integrated and truth != "P"),
        "false_P": int(high_or_integrated and truth != "P" and selected == "P"),
        "maximum_prior_difference": float(
            max(
                np.max(
                    np.abs(state.posterior_store["H_formation"] - PRIOR)
                )
                for state in result["states"]
            )
        ),
        "maximum_slice_log_bf": max(slice_max_log_bfs, default=0.0),
        "maximum_posterior_step": max(step_changes, default=0.0),
        "brier_P": (p_probability - formation_truth) ** 2,
    }
    details = {
        "observations": observations,
        "configurations": configurations,
        "masks": [False] * len(observations),
        "log_joint": result["log_joint"],
    }
    return row, details


def no_event_world(seed: int, index: int) -> tuple[dict[str, Any], dict[str, Any]]:
    length = (40, 80, 160)[index % 3]
    config = configuration(event=False)
    observations = [
        sample_observation(seed, f"no-event-{time}", "T", config)
        for time in range(length)
    ]
    return score_world(
        seed, "no_event", "T", observations, [config] * length
    )


def matched_triplet(
    seeds: list[int], triplet: int
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    base_seed = seeds[0]
    truth = LABELS[triplet % 3]
    event_configs = []
    for index in range(18):
        event_configs.append(
            configuration(
                event=True,
                precision="overwhelm" if index < 4 else "ordinary",
                control="low" if index < 10 else "high",
                broadcast="collapsed" if index < 6 else "integrated",
                real_danger=truth == "D",
            )
        )
    event_observations = [
        sample_observation(
            base_seed, f"matched-event-{index}", truth, config
        )
        for index, config in enumerate(event_configs)
    ]
    variants = (
        ("acute_cluster", 40, list(range(11, 29))),
        ("evenly_spread", 80, np.linspace(2, 77, 18, dtype=int).tolist()),
        (
            "irregular_bursts",
            120,
            [5, 6, 7, 22, 23, 40, 41, 42, 63, 64, 79, 80, 81, 99, 100, 110, 113, 117],
        ),
    )
    output = []
    for seed, (name, length, positions) in zip(seeds, variants):
        configs = [configuration(event=False) for _ in range(length)]
        observations = [(0, 0, 2) for _ in range(length)]
        for event_index, position in enumerate(positions):
            configs[position] = event_configs[event_index]
            observations[position] = event_observations[event_index]
        output.append(
            score_world(
                seed,
                "matched_permutation",
                truth,
                observations,
                configs,
                triplet=triplet,
                variant=name,
            )
        )
    return output


def discriminator_world(
    seed: int, p_favoring: bool
) -> tuple[dict[str, Any], dict[str, Any]]:
    truth = "P" if p_favoring else "D"
    config = configuration(
        event=True,
        precision="overwhelm" if p_favoring else "ordinary",
        control="low" if p_favoring else "high",
        broadcast="collapsed" if p_favoring else "integrated",
        real_danger=not p_favoring,
    )
    observations = [
        sample_observation(seed, f"discriminator-{time}", truth, config)
        for time in range(24)
    ]
    return score_world(
        seed,
        "P_favoring" if p_favoring else "D_favoring",
        truth,
        observations,
        [config] * 24,
    )


def mixed_world(seed: int, index: int) -> tuple[dict[str, Any], dict[str, Any]]:
    truth = LABELS[index % 3]
    length = 72 + 8 * (index % 3)
    event_positions = (
        list(range(4, 10))
        + list(range(length // 3, length // 3 + 8))
        + list(range(length - 10, length - 4))
    )
    configs = [configuration(event=False) for _ in range(length)]
    observations = [(0, 0, 2) for _ in range(length)]
    for event_index, position in enumerate(event_positions):
        config = configuration(
            event=True,
            precision="overwhelm" if event_index < 3 else "ordinary",
            control="low" if event_index < len(event_positions) // 2 else "high",
            broadcast=(
                "integrated"
                if event_index % 5 in (3, 4)
                else "collapsed"
            ),
            real_danger=truth == "D",
        )
        configs[position] = config
        observations[position] = sample_observation(
            seed, f"mixed-{event_index}", truth, config
        )
    return score_world(
        seed, "mixed_provocation", truth, observations, configs
    )


def run_worlds() -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]]]:
    seeds = list(range(FIRST_SEED, FIRST_SEED + WORLD_COUNT))
    rows = []
    detail_by_seed = {}
    for index, seed in enumerate(seeds[:40]):
        row, detail = no_event_world(seed, index)
        rows.append(row)
        detail_by_seed[seed] = detail
    matched_seeds = seeds[40:100]
    for triplet in range(20):
        for row, detail in matched_triplet(
            matched_seeds[triplet * 3 : triplet * 3 + 3], triplet
        ):
            rows.append(row)
            detail_by_seed[int(row["seed"])] = detail
    discriminator_seeds = seeds[100:150]
    for index, seed in enumerate(discriminator_seeds):
        row, detail = discriminator_world(seed, index >= 25)
        rows.append(row)
        detail_by_seed[seed] = detail
    for index, seed in enumerate(seeds[150:200]):
        row, detail = mixed_world(seed, index)
        rows.append(row)
        detail_by_seed[seed] = detail
    if len(rows) != WORLD_COUNT:
        raise AssertionError("challenge world count mismatch")
    return rows, detail_by_seed


def summarize(
    rows: list[dict[str, Any]],
    detail_by_seed: dict[int, dict[str, Any]],
    identity: dict[str, Any],
) -> dict[str, Any]:
    no_event = [row for row in rows if row["cell"] == "no_event"]
    no_event_neutral = sum(
        row["maximum_prior_difference"] <= ENUMERATION_TOLERANCE
        for row in no_event
    )
    no_event_formed = sum(row["formation_selected"] for row in no_event)
    test_1_pass = no_event_neutral == 40 and no_event_formed == 0

    triplet_results = []
    for triplet in range(20):
        group = [
            row
            for row in rows
            if row["cell"] == "matched_permutation"
            and row["triplet"] == triplet
        ]
        evidences = np.asarray(
            [row["winning_log_evidence"] for row in group]
        )
        denominator = float(np.mean(np.abs(evidences)))
        relative_variation = float(
            (evidences.max() - evidences.min()) / denominator
        )
        selected_identical = len({row["selected"] for row in group}) == 1
        triplet_results.append(
            {
                "triplet": triplet,
                "relative_variation": relative_variation,
                "within_15_percent": relative_variation <= 0.15,
                "selected_identical": selected_identical,
            }
        )
    invariant_count = sum(item["within_15_percent"] for item in triplet_results)
    selection_count = sum(item["selected_identical"] for item in triplet_results)
    test_2_pass = invariant_count >= 16 and selection_count >= 18

    d_cell = [row for row in rows if row["cell"] == "D_favoring"]
    p_cell = [row for row in rows if row["cell"] == "P_favoring"]
    d_selected = sum(row["selected"] == "D" for row in d_cell)
    p_selected = sum(row["selected"] == "P" for row in p_cell)
    d_cross_p = sum(row["selected"] == "P" for row in d_cell)
    test_3_pass = (
        d_selected / len(d_cell) >= 0.70
        and p_selected / len(p_cell) >= 0.60
        and d_cross_p / len(d_cell) <= 0.15
    )

    probabilities = np.asarray([row["P_probability"] for row in rows])
    truths = np.asarray([row["formation_truth"] for row in rows])
    brier = float(np.mean((probabilities - truths) ** 2))
    ece = ece_binary(probabilities, truths)
    eligible = [row for row in rows if row["false_P_eligible"]]
    false_p = sum(row["false_P"] for row in eligible)
    false_p_rate = false_p / len(eligible)
    test_4_pass = brier <= 0.20 and ece <= 0.12 and false_p_rate <= 0.10

    all_slice_log_bfs = [
        row["maximum_slice_log_bf"] for row in rows
    ]
    analytic_exceedances = sum(
        value > ANALYTIC_BOUND + ENUMERATION_TOLERANCE
        for value in all_slice_log_bfs
    )
    posterior_steps = [row["maximum_posterior_step"] for row in rows]
    observed_p99 = float(np.quantile(posterior_steps, 0.99))
    # The frozen stage did not publish the threshold required by clause 2.
    test_5_pass = False

    audit_seeds = stable_rng(
        FIRST_SEED, "constitution-audit-seeds"
    ).choice(
        np.asarray(sorted(detail_by_seed)),
        size=10,
        replace=False,
    )
    audit_errors = []
    audit_localization = []
    for seed_value in audit_seeds:
        seed = int(seed_value)
        detail = detail_by_seed[seed]
        independent = np.asarray(
            independent_log_joint(
                detail["observations"],
                detail["configurations"],
                detail["masks"],
            )
        )
        frozen = np.asarray(detail["log_joint"])
        error = float(np.max(np.abs(independent - frozen)))
        audit_errors.append(error)
        audit_localization.append({"seed": seed, "maximum_error": error})
    test_6_pass = max(audit_errors) <= ENUMERATION_TOLERANCE

    tests = {
        "test_1_no_event_neutrality": {
            "passed": test_1_pass,
            "neutral_worlds": no_event_neutral,
            "formation_count": no_event_formed,
            "formation_rate_95_interval": proportion_interval(
                no_event_formed, len(no_event)
            ),
            "maximum_prior_difference": max(
                row["maximum_prior_difference"] for row in no_event
            ),
            "localization": [
                row["seed"]
                for row in no_event
                if row["maximum_prior_difference"] > ENUMERATION_TOLERANCE
                or row["formation_selected"]
            ],
        },
        "test_2_schedule_invariance": {
            "passed": test_2_pass,
            "within_15_percent_count": invariant_count,
            "within_15_percent_rate_95_interval": proportion_interval(
                invariant_count, 20
            ),
            "selection_identical_count": selection_count,
            "selection_identical_rate_95_interval": proportion_interval(
                selection_count, 20
            ),
            "relative_variation_95_interval": mean_interval(
                [item["relative_variation"] for item in triplet_results],
                "triplet-relative-variation",
            ),
            "localization": [
                item for item in triplet_results
                if not item["within_15_percent"]
                or not item["selected_identical"]
            ],
        },
        "test_3_D_P_separation": {
            "passed": test_3_pass,
            "D_cell_D_selection_95_interval": proportion_interval(
                d_selected, len(d_cell)
            ),
            "P_cell_P_selection_95_interval": proportion_interval(
                p_selected, len(p_cell)
            ),
            "D_cell_P_cross_selection_95_interval": proportion_interval(
                d_cross_p, len(d_cell)
            ),
            "localization": {
                "D_cell_not_D": [
                    row["seed"] for row in d_cell if row["selected"] != "D"
                ],
                "P_cell_not_P": [
                    row["seed"] for row in p_cell if row["selected"] != "P"
                ],
                "D_cell_selected_P": [
                    row["seed"] for row in d_cell if row["selected"] == "P"
                ],
            },
        },
        "test_4_calibration_profile": {
            "passed": test_4_pass,
            "Brier": brier,
            "Brier_95_interval": mean_interval(
                [row["brier_P"] for row in rows], "brier"
            ),
            "ECE": ece,
            "false_P_eligible_count": len(eligible),
            "false_P_95_interval": proportion_interval(
                false_p, len(eligible)
            ),
            "shape": {
                "selected_counts": {
                    label: sum(row["selected"] == label for row in rows)
                    for label in LABELS
                },
                "truth_counts": {
                    label: sum(row["truth"] == label for row in rows)
                    for label in LABELS
                },
            },
            "localization": [
                row["seed"] for row in eligible if row["false_P"]
            ],
        },
        "test_5_continuity": {
            "passed": test_5_pass,
            "analytic_clause_passed": analytic_exceedances == 0,
            "analytic_bound": ANALYTIC_BOUND,
            "analytic_exceedances": analytic_exceedances,
            "maximum_slice_log_bf": max(all_slice_log_bfs),
            "observed_world_maximum_step_p99": observed_p99,
            "observed_world_maximum_step_95_interval": mean_interval(
                posterior_steps, "posterior-step"
            ),
            "frozen_empirical_p99_rate_bound": None,
            "multiplier": 1.75,
            "second_clause": "INEXPRESSIBLE: c67e853 froze no empirical p99 rate bound",
            "localization": {
                "analytic_exceedance_seeds": [
                    row["seed"]
                    for row in rows
                    if row["maximum_slice_log_bf"]
                    > ANALYTIC_BOUND + ENUMERATION_TOLERANCE
                ],
                "missing_definition": [
                    "contracts/v2.3.2-formation-contract.md",
                    "protocols/v2.3.2-formation-analysis-plan.md",
                    "results/V2.3.2-formation/stage-report.json",
                    "results/V2.3.2-formation/frozen-one-slice-sign-table-summary.json",
                    "results/V2.3.2-formation/freeze-manifest.json",
                ],
            },
        },
        "test_6_constitution_spot_audit": {
            "passed": test_6_pass,
            "seed_count": 10,
            "seeds": [int(value) for value in audit_seeds],
            "maximum_recombination_error": max(audit_errors),
            "error_95_interval": mean_interval(
                audit_errors, "constitution-error"
            ),
            "localization": audit_localization,
            "independent_module": "challenges/c_v232_f_independent.py",
        },
    }
    verdict = "PASS" if all(item["passed"] for item in tests.values()) else "FAIL"
    return {
        "challenge": CHALLENGE,
        "verdict": verdict,
        "world_count": len(rows),
        "seed_block_used": [FIRST_SEED, FIRST_SEED + WORLD_COUNT - 1],
        "freeze_identity": identity,
        "tests": tests,
        "failures": [
            name for name, result in tests.items() if not result["passed"]
        ],
    }


def write_outputs(
    rows: list[dict[str, Any]], summary: dict[str, Any]
) -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    with (RESULT_DIR / "per_seed.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (RESULT_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tests = summary["tests"]
    report = f"""# C-V232-F formation challenge

Verdict: **{summary['verdict']}**.

The frozen identity check passed for
`{summary['freeze_identity']['verified_file_count']}` files at
`{summary['freeze_identity']['commit']}`. The first 200 released seeds
`813101:813300` were used.

## Test outcomes

1. No-event neutrality: **{'PASS' if tests['test_1_no_event_neutrality']['passed'] else 'FAIL'}**.
   Neutral worlds `{tests['test_1_no_event_neutrality']['neutral_worlds']}/40`;
   formation `{tests['test_1_no_event_neutrality']['formation_count']}/40`;
   maximum prior difference
   `{tests['test_1_no_event_neutrality']['maximum_prior_difference']:.3g}`.
2. Schedule invariance: **{'PASS' if tests['test_2_schedule_invariance']['passed'] else 'FAIL'}**.
   Relative-evidence criterion
   `{tests['test_2_schedule_invariance']['within_15_percent_count']}/20`;
   identical selection
   `{tests['test_2_schedule_invariance']['selection_identical_count']}/20`.
   Winning evidence is the frozen comparative margin over the runner-up, so
   candidate-common no-event support cancels as required by the constitution.
3. D/P separation: **{'PASS' if tests['test_3_D_P_separation']['passed'] else 'FAIL'}**.
   D-cell D selection
   `{tests['test_3_D_P_separation']['D_cell_D_selection_95_interval'][0]:.3f}`;
   P-cell P selection
   `{tests['test_3_D_P_separation']['P_cell_P_selection_95_interval'][0]:.3f}`;
   D-cell P cross-selection
   `{tests['test_3_D_P_separation']['D_cell_P_cross_selection_95_interval'][0]:.3f}`.
4. Calibration profile: **{'PASS' if tests['test_4_calibration_profile']['passed'] else 'FAIL'}**.
   Brier `{tests['test_4_calibration_profile']['Brier']:.6f}`;
   ECE `{tests['test_4_calibration_profile']['ECE']:.6f}`;
   false-P `{tests['test_4_calibration_profile']['false_P_95_interval'][0]:.3f}`.
5. Continuity: **FAIL (inexpressible frozen threshold)**.
   The analytic clause passed with
   `{tests['test_5_continuity']['analytic_exceedances']}` exceedances and
   maximum slice log BF
   `{tests['test_5_continuity']['maximum_slice_log_bf']:.6f}` against
   `{ANALYTIC_BOUND:.6f}`. The c67e853 freeze contains no empirical p99 rate
   bound to multiply by 1.75; no post-seal value was invented.
6. Independent constitution audit:
   **{'PASS' if tests['test_6_constitution_spot_audit']['passed'] else 'FAIL'}**.
   Maximum error
   `{tests['test_6_constitution_spot_audit']['maximum_recombination_error']:.3g}`
   across ten seed-drawn worlds.

## Failure localization

The sole failing test is Test 5's second clause. The missing frozen definition
was checked in the contract, analysis plan, stage report, sign-table summary,
and manifest. This is a prospective contract omission, not a numerical
continuity exceedance. Per-test seed localization and all intervals are in
`summary.json`; all 200 world outcomes are retained in `per_seed.csv`.
"""
    (RESULT_DIR / "report.md").write_text(report, encoding="utf-8")


def main() -> None:
    identity = verify_frozen_identity()
    rows, details = run_worlds()
    summary = summarize(rows, details, identity)
    write_outputs(rows, summary)


if __name__ == "__main__":
    main()
