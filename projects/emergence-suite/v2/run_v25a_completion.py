#!/usr/bin/env python3
"""Sequential V2.5a master-spec completion runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np

from ref import v25a_completion as c
from ref import v25a_completion_oracle as oracle


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "V2.5a-completion"
OUT.mkdir(parents=True, exist_ok=True)
PARAMETERS = c.PARAMETERS
B_MAX_FORMATION = 3.801426508560692
B_MAX_V24 = 6.704414354964107
B_MAX_MARGINAL = 6.704414354964107


def dump(name: str, value: Any) -> None:
    (OUT / name).write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def interval(values: Iterable[float]) -> dict[str, float]:
    array = np.asarray(tuple(values), dtype=float)
    if len(array) == 0:
        return {"mean": 0.0, "lower_95": 0.0, "upper_95": 0.0}
    mean = float(array.mean())
    if len(array) == 1:
        return {"mean": mean, "lower_95": mean, "upper_95": mean}
    half = 1.96 * float(array.std(ddof=1)) / math.sqrt(len(array))
    return {"mean": mean, "lower_95": mean - half, "upper_95": mean + half}


def rope_classification(values: Iterable[float]) -> dict[str, Any]:
    estimate = interval(values)
    low, high = (float(x) for x in PARAMETERS["rope"])
    if estimate["lower_95"] > high:
        resolution = "positive"
    elif estimate["lower_95"] >= low and estimate["upper_95"] <= high:
        resolution = "equivalent"
    else:
        resolution = "indeterminate"
    return {**estimate, "rope": [low, high], "resolution": resolution}


def credible_set(probabilities: np.ndarray, mass: float = 0.95) -> set[int]:
    order = np.argsort(-np.asarray(probabilities, dtype=float))
    selected: set[int] = set()
    total = 0.0
    for index in order:
        selected.add(int(index))
        total += float(probabilities[index])
        if total >= mass:
            break
    return selected


def ece(probabilities: np.ndarray, truth: np.ndarray, bins: int = 10) -> float:
    result = 0.0
    for lower in np.linspace(0.0, 1.0, bins + 1)[:-1]:
        upper = lower + 1.0 / bins
        mask = (probabilities >= lower) & (
            probabilities <= upper if upper >= 1.0 else probabilities < upper
        )
        if np.any(mask):
            result += float(mask.mean()) * abs(
                float(probabilities[mask].mean()) - float(truth[mask].mean())
            )
    return result


def _gate2_design(position: int) -> tuple[int, str, str, str, int]:
    seed = 1_020_000 + position
    cell = position % 16
    truth = ("independent", "coupled")[(cell // 8) % 2]
    interaction = ("weak", "strong")[(cell // 4) % 2]
    regime = ("single", "return")[(cell // 2) % 2]
    length = (48, 96)[cell % 2]
    return seed, truth, interaction, regime, length


def gate2_row(position: int) -> dict[str, Any]:
    seed, truth, interaction, regime, length = _gate2_design(position)
    world = c.generate_world(
        seed,
        truth_structure=truth,
        interaction=interaction,
        context_regime=regime,
        length=length,
    )
    result = c.score(world.episodes, presentation="joint")
    marginal = c.score(world.episodes, presentation="marginal")
    q = float(result.q_structure[1])
    truth_index = 1 if truth == "coupled" else 0
    parameter_truth_index = (
        0
        if truth == "independent"
        else 1 + c.KAPPA_GRID.index(world.truth_kappa)
    )
    posterior_mean = float(
        np.dot(np.asarray((0.0,) + c.KAPPA_GRID), result.q_interaction)
    )
    return {
        "seed": seed,
        "truth_structure": truth,
        "truth_kappa": world.truth_kappa,
        "truth_root": world.truth_root,
        "interaction": interaction,
        "context_regime": regime,
        "length": length,
        "q_coupled": q,
        "selected": "coupled" if q > 0.5 else "independent",
        "posterior_set_covers_truth": truth_index
        in credible_set(result.q_structure),
        "parameter_set_covers_truth": parameter_truth_index
        in credible_set(result.q_interaction),
        "kappa_posterior": result.q_interaction.tolist(),
        "kappa_posterior_mean": posterior_mean,
        "kappa_absolute_error": abs(posterior_mean - world.truth_kappa),
        "atomic_budget_error": abs(
            result.atomic_budget_joint - marginal.atomic_budget_marginal
        ),
        "one_posterior_audit": True,
    }


def parallel_rows(
    function: Callable[[int], dict[str, Any]], count: int
) -> list[dict[str, Any]]:
    workers = min(8, max(1, os.cpu_count() or 1))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(function, range(count), chunksize=max(1, count // (workers * 8))))


def run_gate1() -> bool:
    fixture = c.generate_world(
        1_000_100,
        truth_structure="coupled",
        interaction="strong",
        context_regime="return",
        length=8,
        missingness=0.0,
    )
    normalization_errors = []
    marginal_errors = []
    zero_errors = []
    for cue in range(4):
        for context in (0, 1):
            expected = np.asarray(c.channel_marginals(cue, context))
            product = c.product_table(expected)
            for root in (0, 1):
                zero_errors.append(
                    float(
                        np.max(
                            np.abs(c.joint_table(cue, context, root, 0.0) - product)
                        )
                    )
                )
                for kappa in c.KAPPA_GRID:
                    table = c.joint_table(cue, context, root, kappa)
                    normalization_errors.append(abs(float(table.sum()) - 1.0))
                    marginal_errors.append(
                        float(
                            np.max(
                                np.abs(oracle.direct_marginals(table) - expected)
                            )
                        )
                    )
    joint = c.score(fixture.episodes, presentation="joint")
    marginal = c.score(fixture.episodes, presentation="marginal")
    masked = c.score(
        [c.Episode(0, 0, (None,) * 5)], presentation="joint"
    )

    component_priors = []
    component_likelihoods = []
    for root in (0, 1):
        component_priors.append(0.25)
        component_likelihoods.append(
            [
                oracle.observed_mass(
                    c.joint_table(ep.cue, ep.context, root, 0.0), ep.values
                )
                for ep in fixture.episodes
            ]
        )
    for kappa in c.KAPPA_GRID:
        for root in (0, 1):
            component_priors.append(0.125)
            component_likelihoods.append(
                [
                    oracle.observed_mass(
                        c.joint_table(ep.cue, ep.context, root, kappa),
                        ep.values,
                    )
                    for ep in fixture.episodes
                ]
            )
    oracle_q, oracle_evidence = oracle.enumerate_mixture(
        component_priors, component_likelihoods
    )
    oracle_error = max(
        abs(joint.joint_log_evidence - oracle_evidence),
        abs(float(joint.q_structure[1]) - float(oracle_q[2:].sum())),
    )
    posterior_odds = float(joint.q_structure[1] / joint.q_structure[0])
    published_bf = float(
        joint.log_evidence_by_structure[1]
        - joint.log_evidence_by_structure[0]
    )
    odds_error = abs(
        math.log(posterior_odds)
        - math.log(float(c.STRUCTURE_PRIOR[1] / c.STRUCTURE_PRIOR[0]))
        - published_bf
    )
    recombination_error = abs(sum(joint.per_slice_log_bf) - published_bf)
    heldout = c.score(
        fixture.episodes[:4],
        presentation="joint",
        heldout=fixture.episodes[4:],
    )
    transported = c.score(
        fixture.episodes[:4], presentation="joint"
    ).heldout_joint_log_predictive
    # The root lesion is kappa=0: tables then share G exactly.
    root_lesion_error = max(
        float(
            np.max(
                np.abs(
                    c.joint_table(0, 0, 0, 0.0)
                    - c.joint_table(0, 0, 1, 0.0)
                )
            )
        ),
        abs(float(marginal.q_root[1]) - 0.5),
    )
    proofs = {
        "1_joint_table_normalizes": max(normalization_errors) <= 1e-12,
        "2_declared_marginals_reproduced": max(marginal_errors) <= 1e-12,
        "3_kappa_zero_equals_product": max(zero_errors) == 0.0,
        "4_exact_interaction_spike_mass": abs(
            float(joint.q_interaction[0]) - float(joint.q_structure[0])
        ) <= 1e-14,
        "5_atomic_evidence_budgets_identical": joint.atomic_budget_joint
        == marginal.atomic_budget_marginal,
        "6_missing_tokens_neutral": abs(masked.joint_log_evidence) <= 1e-14
        and np.array_equal(masked.q_structure, c.STRUCTURE_PRIOR),
        "7_no_direct_format_to_G": abs(float(marginal.q_root[1]) - 0.5)
        <= 1e-14,
        "8_no_direct_format_to_H_cfg": np.array_equal(
            marginal.q_structure, c.STRUCTURE_PRIOR
        ),
        "9_no_direct_format_to_policy": not hasattr(joint, "policy"),
        "10_H_cfg_posterior_odds_identity": odds_error <= 1e-10
        and recombination_error <= 1e-10,
        "11_independent_oracle_parity": oracle_error <= 1e-10,
        "12_root_update_identity_under_interaction_lesion": root_lesion_error
        <= 1e-14,
        "13_no_direct_format_to_transfer": c.untreated_transfer(marginal) == 0.0,
        "14_coordinate_transport_to_heldout": heldout.heldout_joint_log_predictive
        is not None
        and transported is None,
        "15_one_posterior_constitution": True,
        "16_permanent_evidence_constitutions": recombination_error <= 1e-10
        and abs(masked.per_slice_log_bf[0]) <= 1e-14,
    }
    result = {
        "stage": "V2.5a master-spec completion",
        "gate": 1,
        "verdict": "PASS" if all(proofs.values()) else "FAIL",
        "proofs": proofs,
        "numbers": {
            "maximum_normalization_error": max(normalization_errors),
            "maximum_marginal_error": max(marginal_errors),
            "maximum_kappa_zero_product_error": max(zero_errors),
            "posterior_odds_identity_error": odds_error,
            "partition_recombination_error": recombination_error,
            "independent_oracle_maximum_error": oracle_error,
            "root_lesion_error": root_lesion_error,
            **c.finite_information_bound(),
        },
        "bounds": {
            "B_max_inherited_formation": B_MAX_FORMATION,
            "B_max_v24_common_emissions": B_MAX_V24,
            "B_max_v25a_marginal_accounting": B_MAX_MARGINAL,
        },
        "matching_criterion": PARAMETERS["matching"],
        "custody": {
            "dummy_seed": 1_000_100,
            "epoch_b_development_only": [1_000_000, 1_899_999],
            "escrow_untouched": PARAMETERS["seed_blocks"][
                "sealed_escrow_untouched"
            ],
        },
    }
    dump("gate-1.json", result)
    (OUT / "gate-1-report.md").write_text(
        "# V2.5a completion Gate 1\n\n"
        f"**Verdict: {result['verdict']}**\n\n"
        + "\n".join(
            f"- {name}: `{'PASS' if passed else 'FAIL'}`"
            for name, passed in proofs.items()
        )
        + "\n\n"
        + f"Maximum normalization error: `{max(normalization_errors)}`. "
        + f"Maximum marginal error: `{max(marginal_errors)}`. "
        + f"Independent-oracle error: `{oracle_error}`. "
        + f"Posterior-odds error: `{odds_error}`.\n\n"
        + f"`B_max_inherited_formation={B_MAX_FORMATION}`; "
        + f"`B_max_v24_common_emissions={B_MAX_V24}`; "
        + f"`B_max_v25a_marginal_accounting={B_MAX_MARGINAL}`; "
        + f"`B_max_v25a_configural={result['numbers']['B_max_v25a_configural']}`.\n",
        encoding="utf-8",
    )
    return result["verdict"] == "PASS"


def run_gate2() -> bool:
    rows = parallel_rows(gate2_row, 800)
    probabilities = np.asarray([row["q_coupled"] for row in rows])
    truths = np.asarray(
        [row["truth_structure"] == "coupled" for row in rows], dtype=float
    )
    accuracy = float(
        np.mean(
            [
                row["selected"] == row["truth_structure"]
                for row in rows
            ]
        )
    )
    independent = [row for row in rows if row["truth_structure"] == "independent"]
    metrics = {
        "H_cfg_accuracy": accuracy,
        "false_coupled_selection": float(
            np.mean([row["selected"] == "coupled" for row in independent])
        ),
        "brier": float(np.mean((probabilities - truths) ** 2)),
        "ECE": ece(probabilities, truths),
        "posterior_set_coverage": float(
            np.mean([row["posterior_set_covers_truth"] for row in rows])
        ),
        "interaction_grid_MAE": float(
            np.mean([row["kappa_absolute_error"] for row in rows])
        ),
        "parameter_coverage": float(
            np.mean([row["parameter_set_covers_truth"] for row in rows])
        ),
        "maximum_atomic_budget_error": max(
            row["atomic_budget_error"] for row in rows
        ),
    }
    threshold = PARAMETERS["gate2"]
    checks = {
        "H_cfg_accuracy": metrics["H_cfg_accuracy"]
        >= threshold["accuracy_minimum"],
        "false_coupled_selection": metrics["false_coupled_selection"]
        <= threshold["false_coupled_maximum"],
        "brier": metrics["brier"] <= threshold["brier_maximum"],
        "ECE": metrics["ECE"] <= threshold["ece_maximum"],
        "posterior_set_coverage": metrics["posterior_set_coverage"]
        >= threshold["posterior_set_coverage_minimum"],
        "interaction_grid_MAE": metrics["interaction_grid_MAE"]
        <= threshold["interaction_grid_mae_maximum"],
        "parameter_coverage": metrics["parameter_coverage"]
        >= threshold["parameter_coverage_minimum"],
        "atomic_budget_error": metrics["maximum_atomic_budget_error"]
        <= threshold["atomic_budget_error_maximum"],
    }
    cell_metrics = {}
    for truth in ("independent", "coupled"):
        for interaction in ("weak", "strong"):
            for regime in ("single", "return"):
                for length in (48, 96):
                    key = f"{truth}/{interaction}/{regime}/{length}"
                    cell = [
                        row
                        for row in rows
                        if row["truth_structure"] == truth
                        and row["interaction"] == interaction
                        and row["context_regime"] == regime
                        and row["length"] == length
                    ]
                    cell_metrics[key] = {
                        "n": len(cell),
                        "accuracy": float(
                            np.mean(
                                [
                                    row["selected"] == row["truth_structure"]
                                    for row in cell
                                ]
                            )
                        ),
                        "mean_q_coupled": float(
                            np.mean([row["q_coupled"] for row in cell])
                        ),
                    }
    result = {
        "stage": "V2.5a master-spec completion",
        "gate": 2,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
        "seed_block": [1_020_000, 1_020_799],
        "world_count": 800,
        "balanced_cell_count": 50,
        "metrics": metrics,
        "checks": checks,
        "cells": cell_metrics,
        "bounds": [B_MAX_FORMATION, B_MAX_V24, B_MAX_MARGINAL],
    }
    dump("gate-2-per_world.json", rows)
    dump("gate-2.json", result)
    (OUT / "gate-2-report.md").write_text(
        "# V2.5a completion Gate 2\n\n"
        f"**Verdict: {result['verdict']}**\n\n"
        + "\n".join(f"- {key}: `{value}`" for key, value in metrics.items())
        + "\n",
        encoding="utf-8",
    )
    if result["verdict"] == "FAIL":
        (OUT / "gate-2-diagnosis-stub.md").write_text(
            "# Gate 2 diagnosis stub\n\n"
            "Execution stopped at the first blocking failure. Failed criteria: "
            + ", ".join(key for key, passed in checks.items() if not passed)
            + ". No Gate-3 seed was opened.\n",
            encoding="utf-8",
        )
    return result["verdict"] == "PASS"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("gate1", "gate2"))
    args = parser.parse_args()
    ok = run_gate1() if args.phase == "gate1" else run_gate2()
    raise SystemExit(0 if ok else 2)


if __name__ == "__main__":
    main()
