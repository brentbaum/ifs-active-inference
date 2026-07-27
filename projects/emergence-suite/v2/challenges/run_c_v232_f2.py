"""Run revealed C-V232-F2 against the frozen c67e853 formation stage."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from ref.v232_formation import (  # noqa: E402
    PRIOR,
    SUPPORT,
    score_history,
    slice_distribution,
)


CHALLENGE = "C-V232-F2"
FREEZE_COMMIT = "c67e853"
FIRST_SEED = 813301
WORLD_COUNT = 100
DISCRIMINATOR_WORLD_COUNT = 50
MIXED_WORLD_COUNT = 50
EMPIRICAL_P99 = 0.3345519502357523
EMPIRICAL_MULTIPLIER = 1.75
MULTIPLIED_BOUND = 0.5854659129125665
MULTIPLIED_BOUND_EXACT_DECIMAL = "0.5854659129125665"
ACUTE_EXCEEDANCE_RATE_LIMIT = 0.015
ANALYTIC_BOUND = 3.801426508560692
ENUMERATION_TOLERANCE = 1e-10
RESULT_DIR = ROOT / "results" / "challenges" / CHALLENGE
MANIFEST_REL = (
    "projects/emergence-suite/v2/results/"
    "V2.3.2-formation/freeze-manifest.json"
)
ADDENDUM_REL = (
    "projects/emergence-suite/v2/results/"
    "V2.3.2-formation/continuity-empirical-bound-addendum.json"
)
ADDENDUM_COMMIT = "97098db"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_rng(seed: int, component: str) -> np.random.Generator:
    digest = hashlib.sha256(
        f"{CHALLENGE}:{seed}:{component}".encode()
    ).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "big"))


def verify_frozen_identity() -> dict[str, Any]:
    committed_manifest_bytes = subprocess.check_output(
        ["git", "show", f"{FREEZE_COMMIT}:{MANIFEST_REL}"], cwd=REPO
    )
    committed_manifest = json.loads(committed_manifest_bytes)
    local_manifest_path = (
        ROOT / "results/V2.3.2-formation/freeze-manifest.json"
    )
    if local_manifest_path.read_bytes() != committed_manifest_bytes:
        raise RuntimeError("local formation manifest differs from c67e853")
    mismatches = []
    for relative, expected in committed_manifest["files"].items():
        path = ROOT / relative
        actual = sha256(path) if path.is_file() else None
        if actual != expected:
            mismatches.append(
                {"path": relative, "expected": expected, "actual": actual}
            )
    if mismatches:
        raise RuntimeError(f"frozen identity mismatch: {mismatches}")

    committed_addendum_bytes = subprocess.check_output(
        ["git", "show", f"{ADDENDUM_COMMIT}:{ADDENDUM_REL}"], cwd=REPO
    )
    local_addendum_path = (
        ROOT
        / "results/V2.3.2-formation/"
        "continuity-empirical-bound-addendum.json"
    )
    if local_addendum_path.read_bytes() != committed_addendum_bytes:
        raise RuntimeError(
            "local continuity addendum differs from committed 97098db"
        )
    addendum = json.loads(committed_addendum_bytes)
    frozen_p99 = addendum["results"][
        "empirical_p99_single_slice_persistent_posterior_change"
    ]
    if frozen_p99 != EMPIRICAL_P99:
        raise RuntimeError("committed empirical p99 mismatch")
    if EMPIRICAL_MULTIPLIER * frozen_p99 != MULTIPLIED_BOUND:
        raise RuntimeError("committed multiplied bound mismatch")

    frozen_analytic_bound = json.loads(
        (
            ROOT
            / "results/V2.3.2-formation/"
            "frozen-one-slice-sign-table-summary.json"
        ).read_text()
    )["analytic_per_slice_log_bf_bound"]
    if frozen_analytic_bound != ANALYTIC_BOUND:
        raise RuntimeError("frozen analytic bound mismatch")
    return {
        "commit": FREEZE_COMMIT,
        "manifest_sha256": hashlib.sha256(
            committed_manifest_bytes
        ).hexdigest(),
        "verified_file_count": len(committed_manifest["files"]),
        "mismatches": mismatches,
        "analytic_bound": frozen_analytic_bound,
        "continuity_addendum_commit": ADDENDUM_COMMIT,
        "continuity_addendum_sha256": hashlib.sha256(
            committed_addendum_bytes
        ).hexdigest(),
        "empirical_p99": frozen_p99,
    }


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
    probabilities = slice_distribution(truth, **config)
    index = int(
        stable_rng(seed, component).choice(
            len(probabilities), p=probabilities
        )
    )
    return SUPPORT[index]


def discriminator_world(
    seed: int, index: int
) -> tuple[
    str,
    str,
    list[tuple[int, int, int]],
    list[dict[str, Any]],
]:
    p_favoring = index >= DISCRIMINATOR_WORLD_COUNT // 2
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
    return (
        "P_favoring" if p_favoring else "D_favoring",
        truth,
        observations,
        [config] * 24,
    )


def mixed_world(
    seed: int, index: int
) -> tuple[
    str,
    str,
    list[tuple[int, int, int]],
    list[dict[str, Any]],
]:
    truth = ("T", "D", "P")[index % 3]
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
    return "mixed_provocation", truth, observations, configs


def score_world(
    seed: int,
    cell: str,
    truth: str,
    observations: list[tuple[int, int, int]],
    configurations: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    result = score_history(observations, configurations)
    previous_p = float(PRIOR[2])
    slice_rows = []
    for slice_index, (detail, state, config) in enumerate(
        zip(result["contributions"], result["states"], configurations)
    ):
        current_p = float(state.posterior_store["H_formation"][2])
        p_change = abs(current_p - previous_p)
        previous_p = current_p
        maximum_log_bf = max(
            abs(float(value))
            for value in detail["pairwise_log_bf"].values()
        )
        slice_rows.append(
            {
                "seed": seed,
                "cell": cell,
                "truth": truth,
                "slice_index": slice_index,
                "event": int(config["event"]),
                "precision": config["precision"],
                "control": config["control"],
                "broadcast": config["broadcast"],
                "real_danger": int(config["real_danger"]),
                "persistent_probability": current_p,
                "absolute_persistent_posterior_change": p_change,
                "maximum_absolute_pairwise_log_bf": maximum_log_bf,
                "exceeds_empirical_p99": int(p_change > EMPIRICAL_P99),
                "exceeds_multiplied_bound": int(
                    p_change > MULTIPLIED_BOUND
                ),
                "exceeds_analytic_bound": int(
                    maximum_log_bf
                    > ANALYTIC_BOUND + ENUMERATION_TOLERANCE
                ),
            }
        )
    changes = np.asarray(
        [
            row["absolute_persistent_posterior_change"]
            for row in slice_rows
        ],
        dtype=float,
    )
    acute_rows = [row for row in slice_rows if row["event"]]
    world_row = {
        "seed": seed,
        "cell": cell,
        "truth": truth,
        "slice_count": len(slice_rows),
        "acute_event_slice_count": len(acute_rows),
        "acute_empirical_p99_exceedance_count": sum(
            row["exceeds_empirical_p99"] for row in acute_rows
        ),
        "multiplied_bound_exceedance_count": sum(
            row["exceeds_multiplied_bound"] for row in slice_rows
        ),
        "analytic_bound_exceedance_count": sum(
            row["exceeds_analytic_bound"] for row in slice_rows
        ),
        "p50_persistent_change": float(np.quantile(changes, 0.50)),
        "p90_persistent_change": float(np.quantile(changes, 0.90)),
        "p99_persistent_change": float(np.quantile(changes, 0.99)),
        "maximum_persistent_change": float(np.max(changes)),
        "maximum_absolute_pairwise_log_bf": max(
            row["maximum_absolute_pairwise_log_bf"] for row in slice_rows
        ),
    }
    return world_row, slice_rows


def run_worlds() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    seeds = list(range(FIRST_SEED, FIRST_SEED + WORLD_COUNT))
    world_rows = []
    slice_rows = []
    for index, seed in enumerate(seeds[:DISCRIMINATOR_WORLD_COUNT]):
        cell, truth, observations, configs = discriminator_world(seed, index)
        world_row, world_slices = score_world(
            seed, cell, truth, observations, configs
        )
        world_rows.append(world_row)
        slice_rows.extend(world_slices)
    for index, seed in enumerate(seeds[DISCRIMINATOR_WORLD_COUNT:]):
        cell, truth, observations, configs = mixed_world(seed, index)
        world_row, world_slices = score_world(
            seed, cell, truth, observations, configs
        )
        world_rows.append(world_row)
        slice_rows.extend(world_slices)
    if len(world_rows) != WORLD_COUNT:
        raise AssertionError("challenge world count mismatch")
    if {row["seed"] for row in world_rows} != set(seeds):
        raise AssertionError("challenge seed block mismatch")
    return world_rows, slice_rows


def wilson_interval(successes: int, total: int) -> list[float]:
    probability = successes / total
    denominator = 1.0 + 1.96**2 / total
    center = (probability + 1.96**2 / (2.0 * total)) / denominator
    half = (
        1.96
        * math.sqrt(
            probability * (1.0 - probability) / total
            + 1.96**2 / (4.0 * total**2)
        )
        / denominator
    )
    return [probability, center - half, center + half]


def distribution(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "count": int(array.size),
        "p50": float(np.quantile(array, 0.50, method="linear")),
        "p90": float(np.quantile(array, 0.90, method="linear")),
        "p99": float(np.quantile(array, 0.99, method="linear")),
        "maximum": float(np.max(array)),
    }


def cluster_bootstrap_distribution_intervals(
    slice_rows: list[dict[str, Any]],
    *,
    event_only: bool,
    replicates: int = 4000,
) -> dict[str, list[float]]:
    by_seed: dict[int, list[float]] = defaultdict(list)
    for row in slice_rows:
        if not event_only or row["event"]:
            by_seed[int(row["seed"])].append(
                float(row["absolute_persistent_posterior_change"])
            )
    seeds = np.asarray(sorted(by_seed))
    rng = stable_rng(
        FIRST_SEED,
        "acute-distribution-bootstrap"
        if event_only
        else "all-distribution-bootstrap",
    )
    samples = {
        "p50": np.empty(replicates),
        "p90": np.empty(replicates),
        "p99": np.empty(replicates),
        "maximum": np.empty(replicates),
    }
    for replicate in range(replicates):
        selected = rng.choice(seeds, size=len(seeds), replace=True)
        pooled = np.concatenate([by_seed[int(seed)] for seed in selected])
        samples["p50"][replicate] = np.quantile(pooled, 0.50)
        samples["p90"][replicate] = np.quantile(pooled, 0.90)
        samples["p99"][replicate] = np.quantile(pooled, 0.99)
        samples["maximum"][replicate] = np.max(pooled)
    return {
        name: [
            float(np.quantile(values, 0.025)),
            float(np.quantile(values, 0.975)),
        ]
        for name, values in samples.items()
    }


def localize(
    rows: list[dict[str, Any]], field: str
) -> list[dict[str, Any]]:
    return [
        {
            "seed": int(row["seed"]),
            "cell": row["cell"],
            "slice_index": int(row["slice_index"]),
            "event": bool(row["event"]),
            "absolute_persistent_posterior_change": float(
                row["absolute_persistent_posterior_change"]
            ),
            "maximum_absolute_pairwise_log_bf": float(
                row["maximum_absolute_pairwise_log_bf"]
            ),
        }
        for row in rows
        if row[field]
    ]


def localize_by_seed(
    rows: list[dict[str, Any]], field: str
) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row[field]:
            grouped[int(row["seed"])].append(row)
    return [
        {
            "seed": seed,
            "cell": values[0]["cell"],
            "exceedance_count": len(values),
            "slice_indices": [
                int(value["slice_index"]) for value in values
            ],
            "maximum_absolute_persistent_posterior_change": max(
                float(value["absolute_persistent_posterior_change"])
                for value in values
            ),
            "maximum_absolute_pairwise_log_bf": max(
                float(value["maximum_absolute_pairwise_log_bf"])
                for value in values
            ),
        }
        for seed, values in sorted(grouped.items())
    ]


def summarize(
    world_rows: list[dict[str, Any]],
    slice_rows: list[dict[str, Any]],
    identity: dict[str, Any],
) -> dict[str, Any]:
    acute_rows = [row for row in slice_rows if row["event"]]
    acute_exceedances = sum(
        row["exceeds_empirical_p99"] for row in acute_rows
    )
    multiplied_exceedances = sum(
        row["exceeds_multiplied_bound"] for row in slice_rows
    )
    analytic_exceedances = sum(
        row["exceeds_analytic_bound"] for row in slice_rows
    )
    acute_fraction = acute_exceedances / len(acute_rows)
    clause_a = acute_fraction <= ACUTE_EXCEEDANCE_RATE_LIMIT
    clause_b = multiplied_exceedances == 0
    clause_c = analytic_exceedances == 0
    all_changes = [
        float(row["absolute_persistent_posterior_change"])
        for row in slice_rows
    ]
    acute_changes = [
        float(row["absolute_persistent_posterior_change"])
        for row in acute_rows
    ]
    maximum_log_bf = max(
        float(row["maximum_absolute_pairwise_log_bf"])
        for row in slice_rows
    )
    tests = {
        "clause_a_acute_empirical_p99_exceedance_rate": {
            "passed": clause_a,
            "threshold": ACUTE_EXCEEDANCE_RATE_LIMIT,
            "empirical_p99_bound": EMPIRICAL_P99,
            "acute_event_slice_count": len(acute_rows),
            "exceedance_count": acute_exceedances,
            "exceedance_rate_95_wilson_interval": wilson_interval(
                acute_exceedances, len(acute_rows)
            ),
            "localization": localize(
                acute_rows, "exceeds_empirical_p99"
            ),
            "per_seed_localization": localize_by_seed(
                acute_rows, "exceeds_empirical_p99"
            ),
        },
        "clause_b_no_slice_exceeds_multiplied_bound": {
            "passed": clause_b,
            "multiplier": EMPIRICAL_MULTIPLIER,
            "bound": MULTIPLIED_BOUND,
            "bound_exact_decimal": MULTIPLIED_BOUND_EXACT_DECIMAL,
            "all_slice_count": len(slice_rows),
            "exceedance_count": multiplied_exceedances,
            "exceedance_rate_95_wilson_interval": wilson_interval(
                multiplied_exceedances, len(slice_rows)
            ),
            "maximum_observed_change": max(all_changes),
            "localization": localize(
                slice_rows, "exceeds_multiplied_bound"
            ),
            "per_seed_localization": localize_by_seed(
                slice_rows, "exceeds_multiplied_bound"
            ),
        },
        "clause_c_frozen_analytic_bound": {
            "passed": clause_c,
            "bound": ANALYTIC_BOUND,
            "tolerance": ENUMERATION_TOLERANCE,
            "all_slice_count": len(slice_rows),
            "exceedance_count": analytic_exceedances,
            "exceedance_rate_95_wilson_interval": wilson_interval(
                analytic_exceedances, len(slice_rows)
            ),
            "maximum_observed_absolute_pairwise_log_bf": maximum_log_bf,
            "localization": localize(
                slice_rows, "exceeds_analytic_bound"
            ),
            "per_seed_localization": localize_by_seed(
                slice_rows, "exceeds_analytic_bound"
            ),
        },
    }
    return {
        "challenge": CHALLENGE,
        "verdict": (
            "PASS"
            if all(test["passed"] for test in tests.values())
            else "FAIL"
        ),
        "world_count": len(world_rows),
        "seed_block_used": [FIRST_SEED, FIRST_SEED + WORLD_COUNT - 1],
        "population": {
            "discriminator_worlds": DISCRIMINATOR_WORLD_COUNT,
            "D_favoring_worlds": sum(
                row["cell"] == "D_favoring" for row in world_rows
            ),
            "P_favoring_worlds": sum(
                row["cell"] == "P_favoring" for row in world_rows
            ),
            "mixed_provocation_worlds": MIXED_WORLD_COUNT,
            "all_slice_count": len(slice_rows),
            "acute_event_slice_count": len(acute_rows),
        },
        "freeze_identity": identity,
        "distribution": {
            "definition": (
                "Absolute q_t(P)-q_{t-1}(P) magnitude; the first slice "
                "uses the frozen prior q_0(P)=0.25. Quantiles use NumPy's "
                "linear method."
            ),
            "all_slices": distribution(all_changes),
            "acute_event_slices": distribution(acute_changes),
            "cluster_bootstrap_95_intervals": {
                "method": (
                    "4,000 deterministic nonparametric bootstrap "
                    "replicates resampling whole worlds with replacement"
                ),
                "all_slices": cluster_bootstrap_distribution_intervals(
                    slice_rows, event_only=False
                ),
                "acute_event_slices": (
                    cluster_bootstrap_distribution_intervals(
                        slice_rows, event_only=True
                    )
                ),
            },
        },
        "tests": tests,
        "failures": [
            name for name, test in tests.items() if not test["passed"]
        ],
    }


def write_outputs(
    world_rows: list[dict[str, Any]],
    slice_rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    with (RESULT_DIR / "per_seed.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(world_rows[0]))
        writer.writeheader()
        writer.writerows(world_rows)
    with (RESULT_DIR / "per_slice.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(slice_rows[0]))
        writer.writeheader()
        writer.writerows(slice_rows)
    (RESULT_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    tests = summary["tests"]
    all_distribution = summary["distribution"]["all_slices"]
    acute_distribution = summary["distribution"]["acute_event_slices"]
    clause_a = tests[
        "clause_a_acute_empirical_p99_exceedance_rate"
    ]
    clause_b = tests["clause_b_no_slice_exceeds_multiplied_bound"]
    clause_c = tests["clause_c_frozen_analytic_bound"]
    report = f"""# C-V232-F2 continuity challenge

Verdict: **{summary['verdict']}**.

The frozen identity check passed for
`{summary['freeze_identity']['verified_file_count']}` files at
`{summary['freeze_identity']['commit']}`. The committed continuity addendum
at `97098db` also matched byte-for-byte. All 100 released seeds,
`813301:813400`, were used: 50 D/P-discriminator worlds and 50
mixed-provocation worlds.

## Full distribution

Single-slice change is
`abs(q_t(P) - q_(t-1)(P))`, using the frozen prior `q_0(P)=0.25` at each
world's first slice.

| Population | n | p50 | p90 | p99 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| All slices | {all_distribution['count']} | {all_distribution['p50']:.12g} | {all_distribution['p90']:.12g} | {all_distribution['p99']:.12g} | {all_distribution['maximum']:.12g} |
| Acute-event slices | {acute_distribution['count']} | {acute_distribution['p50']:.12g} | {acute_distribution['p90']:.12g} | {acute_distribution['p99']:.12g} | {acute_distribution['maximum']:.12g} |

The corresponding world-cluster-bootstrap 95% intervals are retained in
`summary.json`, and every observed slice is retained in `per_slice.csv`.

## Three clauses

1. Acute-event exceedance rate: **{'PASS' if clause_a['passed'] else 'FAIL'}**.
   `{clause_a['exceedance_count']}/{clause_a['acute_event_slice_count']}`
   acute slices exceeded `{EMPIRICAL_P99}`, a rate of
   `{clause_a['exceedance_rate_95_wilson_interval'][0]:.6f}`
   (95% Wilson interval
   `[{clause_a['exceedance_rate_95_wilson_interval'][1]:.6f},`
   ` {clause_a['exceedance_rate_95_wilson_interval'][2]:.6f}]`) against the
   `0.015` limit.
2. Multiplied empirical bound: **{'PASS' if clause_b['passed'] else 'FAIL'}**.
   `{clause_b['exceedance_count']}` slices exceeded
   `1.75 × {EMPIRICAL_P99} = {MULTIPLIED_BOUND_EXACT_DECIMAL}`; the maximum was
   `{clause_b['maximum_observed_change']:.12g}`. The exceedance-rate 95%
   Wilson interval is
   `[{clause_b['exceedance_rate_95_wilson_interval'][1]:.6f},`
   ` {clause_b['exceedance_rate_95_wilson_interval'][2]:.6f}]`.
3. Frozen analytic bound: **{'PASS' if clause_c['passed'] else 'FAIL'}**.
   `{clause_c['exceedance_count']}` slices exceeded
   `{ANALYTIC_BOUND}`; the maximum absolute pairwise slice log BF was
   `{clause_c['maximum_observed_absolute_pairwise_log_bf']:.12g}`. The
   exceedance-rate 95% Wilson interval is
   `[{clause_c['exceedance_rate_95_wilson_interval'][1]:.6f},`
   ` {clause_c['exceedance_rate_95_wilson_interval'][2]:.6f}]`.

## Localization

Per-seed and per-slice localization for every empirical-p99 exceedance and
every clause-(b) or clause-(c) violation is recorded verbatim in
`summary.json`; `per_seed.csv` gives world-level counts and maxima.
"""
    (RESULT_DIR / "report.md").write_text(report, encoding="utf-8")


def main() -> None:
    identity = verify_frozen_identity()
    world_rows, slice_rows = run_worlds()
    summary = summarize(world_rows, slice_rows, identity)
    write_outputs(world_rows, slice_rows, summary)


if __name__ == "__main__":
    main()
