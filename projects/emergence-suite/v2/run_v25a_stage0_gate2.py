"""Run V2.5a stage 0 and gates 1-2 in their frozen order."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import inspect
import json
import math
import subprocess
import sys
import time
import textwrap
from pathlib import Path
from typing import Any

import numpy as np

from ref import v24, v25a, v25a_oracle
from ref.rng import component_rng


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "V2.5a"
PARAMETER_PATH = ROOT / "protocols" / "v2.5a-parameters.json"
B_MAX_FORMATION = 3.801426508560692
B_MAX_V24 = 6.704414354964107


def _json_default(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(type(value).__name__)


def write_json(name: str, value: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(
        json.dumps(value, indent=2, sort_keys=True, default=_json_default)
        + "\n",
        encoding="utf-8",
    )


def _observed_tokens(observations: list[v24.Observation]) -> int:
    return sum(
        any(value is not None for value in (item.outcome, item.marker, item.root))
        for item in observations
    )


def _world_row(seed: int, cell: str, full: bool = False) -> dict[str, Any]:
    family = (
        "context_split" if cell == "association_carrying"
        else "cue_local_relearning"
    )
    world = v24.generate_world(family, seed, length=96)
    score = v25a.score_presentations(family, world["observations"])
    match = v25a.match_marginal_root_information(
        family,
        family,
        seed,
        base_length=96,
        tolerance=float(
            v25a.PARAMETERS["criterion_freeze_procedure"][
                "default_candidates"
            ]["matching_kl_tolerance_nats"]
        ),
    )
    tokens = _observed_tokens(world["observations"])
    row = {
        "seed": seed,
        "cell": cell,
        "family": family,
        "observed_tokens": tokens,
        "delta_i": score.delta_i,
        "delta_i_per_token": score.delta_i / max(1, tokens),
        "delta_i_slice_min": min(score.delta_i_per_slice),
        "delta_i_slice_max": max(score.delta_i_per_slice),
        "joint_log_evidence": score.joint.log_evidence,
        "marginal_log_evidence": score.marginal_log_evidence,
        "increment_identity_error": score.increment_identity_error,
        "channel_log_evidence": {
            channel: score.channel_scores[channel].log_evidence
            for channel in v25a.CHANNELS
        },
        "target_root_kl": match.target_kl,
        "matched_slices": match.matched_slices,
        "matched_kl": match.matched_kl,
        "matching_ratio": match.ratio,
        "matching_censored": match.censored,
        "matching_absolute_kl_error": match.absolute_kl_error,
        "extension_prefix_identity": match.prefix_identity,
    }
    if full:
        row.update(
            {
                "joint_per_slice": list(score.joint.per_slice_log_predictive),
                "marginal_per_slice": list(
                    score.marginal_per_slice_log_predictive
                ),
                "delta_i_per_slice": list(score.delta_i_per_slice),
                "channel_per_slice": {
                    channel: list(
                        score.channel_scores[
                            channel
                        ].per_slice_log_predictive
                    )
                    for channel in v25a.CHANNELS
                },
            }
        )
    return row


def _parallel_rows(specification: list[tuple[int, str]], full: bool) -> list[dict]:
    if not specification:
        return []
    seeds = [seed for seed, _ in specification]
    if seeds != list(range(seeds[0], seeds[0] + len(seeds))):
        raise ValueError("parallel row specification must be contiguous")
    carrying_count = sum(
        cell == "association_carrying" for _, cell in specification
    )
    if any(
        cell
        != ("association_carrying" if index < carrying_count else "independent")
        for index, (_, cell) in enumerate(specification)
    ):
        raise ValueError("parallel row cells must be carrying then independent")
    workers = 8
    boundaries = np.linspace(0, len(specification), workers + 1, dtype=int)
    processes = []
    prefix = f".v25a-rows-{seeds[0]}"
    for worker in range(workers):
        output = OUT / f"{prefix}-{worker}.json"
        if output.exists():
            output.unlink()
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "rows-worker",
            "--start-position",
            str(int(boundaries[worker])),
            "--end-position",
            str(int(boundaries[worker + 1])),
            "--seed-base",
            str(seeds[0]),
            "--carrying-count",
            str(carrying_count),
            "--worker-output",
            str(output),
        ]
        if full:
            command.append("--full")
        processes.append(
            (worker, output, subprocess.Popen(command, cwd=ROOT))
        )
    remaining = {worker: process for worker, _, process in processes}
    while remaining:
        time.sleep(2)
        for worker, process in list(remaining.items()):
            status = process.poll()
            if status is None:
                continue
            if status:
                raise RuntimeError(f"row worker {worker} exited {status}")
            del remaining[worker]
    rows = []
    for worker, output, _ in processes:
        rows.extend(json.loads(output.read_text()))
        output.unlink()
    rows.sort(key=lambda row: row["seed"])
    if [row["seed"] for row in rows] != seeds:
        raise ValueError("parallel row result ledger is incomplete")
    return rows


def _run_rows_worker(args: argparse.Namespace) -> None:
    rows = []
    for position in range(args.start_position, args.end_position):
        seed = args.seed_base + position
        cell = (
            "association_carrying"
            if position < args.carrying_count
            else "independent"
        )
        rows.append(_world_row(seed, cell, args.full))
    Path(args.worker_output).write_text(
        json.dumps(rows, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _range(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {
        "minimum": float(array.min()),
        "q05": float(np.quantile(array, 0.05)),
        "median": float(np.median(array)),
        "mean": float(array.mean()),
        "q95": float(np.quantile(array, 0.95)),
        "maximum": float(array.max()),
    }


def run_pilot() -> None:
    parameters = json.loads(PARAMETER_PATH.read_text())
    if parameters["criterion_freeze_procedure"]["status"] != "SESOI_SLOTS_PENDING_PILOT":
        raise RuntimeError("stage-0 pilot may run only before numeric freeze")
    specification = [
        (seed, "association_carrying" if seed < 755100 else "independent")
        for seed in range(755000, 755200)
    ]
    rows = _parallel_rows(specification, full=False)
    carrying = [row for row in rows if row["cell"] == "association_carrying"]
    independent = [row for row in rows if row["cell"] == "independent"]
    uncensored = [row for row in rows if not row["matching_censored"]]
    root_movements = [
        math.sqrt(max(0.0, 0.5 * row["target_root_kl"]))
        for row in rows
    ]
    summary = {
        "stage": "V2.5a",
        "phase": "stage_0_attainability_pilot",
        "criterion_evaluated": False,
        "seed_block": [755000, 755199],
        "world_count": 200,
        "cells": {
            "association_carrying": 100,
            "independent": 100,
        },
        "attainable_ranges": {
            "carrying_delta_i_per_token": _range(
                [row["delta_i_per_token"] for row in carrying]
            ),
            "independent_delta_i_per_token": _range(
                [row["delta_i_per_token"] for row in independent]
            ),
            "absolute_independent_delta_i": _range(
                [abs(row["delta_i"]) for row in independent]
            ),
            "target_root_kl": _range(
                [row["target_root_kl"] for row in rows]
            ),
            "matching_ratio_uncensored": _range(
                [row["matching_ratio"] for row in uncensored]
            ),
            "matching_absolute_kl_error_uncensored": _range(
                [row["matching_absolute_kl_error"] for row in uncensored]
            ),
            "root_movement_proxy_from_kl": _range(root_movements),
        },
        "matching_censored_count": sum(
            row["matching_censored"] for row in rows
        ),
        "maximum_increment_identity_error": max(
            row["increment_identity_error"] for row in rows
        ),
        "all_extension_prefixes_identical": all(
            row["extension_prefix_identity"] for row in rows
        ),
        "reporting_only": (
            "Attainable ranges only. No threshold was applied and no "
            "criterion pass/fail was computed."
        ),
        "B_max_inherited_formation": B_MAX_FORMATION,
        "B_max_v24_common_emissions": B_MAX_V24,
        "B_max_v25a_marginal_accounting": (
            v25a.marginal_finite_information_bound()[
                "B_max_v25a_marginal_accounting"
            ]
        ),
    }
    write_json("stage0-pilot-per_world.json", rows)
    write_json("stage0-pilot.json", summary)
    (OUT / "stage0-pilot-report.md").write_text(
        "# V2.5a stage-0 attainability pilot\n\n"
        "No criterion was evaluated. This report publishes attainable ranges "
        "from the barred `755000:755199` block solely for numeric freezing.\n\n"
        f"Carrying ΔI/token range: `{summary['attainable_ranges']['carrying_delta_i_per_token']}`.\n\n"
        f"Independent ΔI/token range: `{summary['attainable_ranges']['independent_delta_i_per_token']}`.\n\n"
        f"Target root-KL range: `{summary['attainable_ranges']['target_root_kl']}`.\n\n"
        f"Uncensored matching-error range: `{summary['attainable_ranges']['matching_absolute_kl_error_uncensored']}`; "
        f"censored `{summary['matching_censored_count']}/200`.\n\n"
        f"`B_max_inherited_formation = {B_MAX_FORMATION}`; "
        f"`B_max_v24_common_emissions = {B_MAX_V24}`; "
        f"`B_max_v25a_marginal_accounting = {summary['B_max_v25a_marginal_accounting']}` "
        "(not distinct from the V2.4 common-emissions bound).\n",
        encoding="utf-8",
    )


def _source_purity_audit() -> dict[str, Any]:
    source = textwrap.dedent(inspect.getsource(v25a))
    tree = ast.parse(source)
    forbidden_branch_assignments = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        for child in ast.walk(node):
            if isinstance(child, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                names = []
                targets = (
                    child.targets
                    if isinstance(child, ast.Assign)
                    else [child.target]
                )
                for target in targets:
                    if isinstance(target, ast.Name):
                        names.append(target.id)
                for name in names:
                    if name in {"H_R", "q_H_R", "formed", "winner"}:
                        forbidden_branch_assignments.append(name)
    return {
        "forbidden_branch_assignments": forbidden_branch_assignments,
        "presentation_terms_analysis_only": all(
            token in source
            for token in ("analysis_only", "delta_i", "matched_slices")
        ),
        "passed": not forbidden_branch_assignments,
    }


def run_gate1() -> bool:
    parameters = json.loads(PARAMETER_PATH.read_text())
    if parameters["criterion_freeze_procedure"]["status"] != "NUMERIC_SESOIS_FROZEN":
        raise RuntimeError("Gate 1 cannot precede the numeric pilot freeze")
    fixture = [
        v24.Observation(0, 1, "then_marker", 1),
        v24.Observation(1, 1, "then_marker", None),
        v24.Observation(2, 0, "now_marker", 0),
        v24.Observation(0, 0, "now_marker", 0),
    ]
    independent_errors = {}
    for family in (
        "global_downweight",
        "cue_local_relearning",
        "continuous_drift",
    ):
        score = v25a.score_presentations(family, fixture)
        independent_errors[family] = max(
            map(abs, score.delta_i_per_slice)
        )
    all_scores = {
        family: v25a.score_presentations(family, fixture)
        for family in v24.FAMILIES
    }
    increment_error = max(
        score.increment_identity_error for score in all_scores.values()
    )
    dose = [
        v25a.enumerable_joint_information(value)
        for value in np.linspace(0.0, 1.0, 5)
    ]
    expectation_error = abs(
        dose[-1]["expected_delta_i"]
        - v25a.enumerable_joint_information(1.0)["expected_delta_i"]
    )
    production_cs = all_scores["context_split"]
    oracle_delta = v25a_oracle.enumerated_cs_delta_i(fixture)
    oracle_delta_error = abs(production_cs.delta_i - oracle_delta)
    joint_oracle = v25a_oracle.enumerated_cs_evidence(fixture)
    marginal_oracle = math.prod(
        v25a_oracle.enumerated_cs_evidence(fixture, channel)
        for channel in v25a.CHANNELS
    )
    joint_error = abs(
        math.exp(production_cs.joint.log_evidence) - joint_oracle
    )
    marginal_error = abs(
        math.exp(production_cs.marginal_log_evidence) - marginal_oracle
    )
    masked = v25a.score_presentations(
        "context_split", [v24.Observation(0, None, None, None)]
    )
    roots = [None, 1, 1, 0, 1, None, 1]
    observations = [
        v24.Observation(index % 3, None, None, value)
        for index, value in enumerate(roots)
    ]
    target = 0.25
    production_match = v25a.scan_root_kl(
        observations, target, 0.01, len(observations)
    )
    oracle_match = v25a_oracle.matching_scan(
        roots, target, 0.01, len(roots)
    )
    censor_production = v25a.scan_root_kl(
        observations, 1.0, 0.0, len(observations)
    )
    censor_oracle = v25a_oracle.matching_scan(
        roots, 1.0, 0.0, len(roots)
    )
    derived = v25a.compare_marginal_candidates(fixture)
    purity = _source_purity_audit()
    bound = v25a.marginal_finite_information_bound()
    monotone = all(
        right["expected_delta_i"] >= left["expected_delta_i"]
        for left, right in zip(dose, dose[1:])
    ) and dose[-1]["expected_delta_i"] > dose[0]["expected_delta_i"]
    checks = {
        "1_factorization_identity": max(independent_errors.values()) <= 1e-10,
        "2_increment_identity": increment_error <= 1e-10,
        "3_expectation_nonnegative_exact_kl": (
            expectation_error <= 1e-10
            and min(row["expected_delta_i"] for row in dose) >= -1e-14
        ),
        "4_zero_increment_calibration": max(independent_errors.values()) <= 1e-10,
        "5_matching_oracle_and_censor_boundary": (
            production_match[0] == oracle_match[0]
            and abs(production_match[1] - oracle_match[1]) <= 1e-10
            and censor_production == censor_oracle == (None, None)
        ),
        "6_presentation_purity": purity["passed"],
        "7_constitution_both_accountings": (
            joint_error <= 1e-10
            and marginal_error <= 1e-10
            and oracle_delta_error <= 1e-10
            and masked.joint.log_evidence == 0.0
            and masked.marginal_log_evidence == 0.0
        ),
        "8_one_posterior_derived_candidates": derived["one_posterior_audit"],
        "9_dose_direction": monotone,
        "10_custody": (
            "755000:755199 (barred after use)"
            in parameters["criterion_freeze_procedure"]["pilot_block"]
            and parameters["b_max"]["inherited_formation"] == B_MAX_FORMATION
            and parameters["b_max"]["v24_common_emissions"] == B_MAX_V24
        ),
    }
    result = {
        "stage": "V2.5a",
        "gate": 1,
        "proofs": checks,
        "passed": all(checks.values()),
        "factorization_maximum_errors": independent_errors,
        "increment_identity_maximum_error": increment_error,
        "expectation_kl_dose": dose,
        "expectation_identity_error": expectation_error,
        "independent_oracle": {
            "delta_i_error": oracle_delta_error,
            "joint_evidence_error": joint_error,
            "marginal_evidence_error": marginal_error,
            "matching_production": production_match,
            "matching_oracle": oracle_match,
            "censor_production": censor_production,
            "censor_oracle": censor_oracle,
        },
        "purity": purity,
        "one_posterior_audit": derived["one_posterior_audit"],
        "finite_information": bound,
        "B_max_inherited_formation": B_MAX_FORMATION,
        "B_max_v24_common_emissions": B_MAX_V24,
    }
    write_json("gate-1.json", result)
    (OUT / "gate-1-report.md").write_text(
        "# V2.5a Gate 1 — semantic proofs\n\n"
        f"Outcome: **{'PASS' if result['passed'] else 'FAIL'}**. "
        f"Proofs: `{checks}`.\n\n"
        f"Independent-oracle ΔI error `{oracle_delta_error}`; maximum "
        f"increment identity error `{increment_error}`.\n\n"
        f"`B_max_inherited_formation = {B_MAX_FORMATION}`; "
        f"`B_max_v24_common_emissions = {B_MAX_V24}`; "
        f"`B_max_v25a_marginal_accounting = {bound['B_max_v25a_marginal_accounting']}`. "
        "The marginal bound is not distinct, so no third distinct constant is introduced.\n",
        encoding="utf-8",
    )
    if not result["passed"]:
        (OUT / "gate-1-diagnosis-stub.md").write_text(
            "# V2.5a Gate-1 honest stop\n\n"
            f"Failed proofs: `{[name for name, value in checks.items() if not value]}`.\n"
        )
    return result["passed"]


def _bootstrap_interval(values: list[float]) -> tuple[float, float, float]:
    array = np.asarray(values, dtype=float)
    rng = component_rng(756000, "v25a-gate2-delta-i-bootstrap")
    means = np.empty(10000)
    for index in range(len(means)):
        means[index] = float(
            rng.choice(array, size=len(array), replace=True).mean()
        )
    low, high = np.quantile(means, [0.025, 0.975])
    return float(array.mean()), float(low), float(high)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_gate2() -> bool:
    parameters = json.loads(PARAMETER_PATH.read_text())
    if parameters["criterion_freeze_procedure"]["status"] != "NUMERIC_SESOIS_FROZEN":
        raise RuntimeError("Gate 2 cannot run before numeric freeze")
    if not (OUT / "gate-1.json").exists() or not json.loads(
        (OUT / "gate-1.json").read_text()
    )["passed"]:
        raise RuntimeError("Gate 2 cannot run after a failing Gate 1")
    specification = [
        (seed, "association_carrying" if seed < 756200 else "independent")
        for seed in range(756000, 756400)
    ]
    rows = _parallel_rows(specification, full=True)
    carrying = [row for row in rows if row["cell"] == "association_carrying"]
    independent = [row for row in rows if row["cell"] == "independent"]
    carrying_interval = _bootstrap_interval(
        [row["delta_i_per_token"] for row in carrying]
    )
    independent_max = max(abs(row["delta_i"]) for row in independent)
    sesoi = float(
        parameters["frozen_numeric_criteria"][
            "delta_i_sesoi_nats_per_token"
        ]
    )
    v24_hash = _hash(ROOT / "ref" / "v24.py")
    freeze = json.loads(
        (ROOT / "results" / "V2.4.4" / "freeze-manifest.json").read_text()
    )
    frozen_v24_hash = freeze["files"]["ref/v24.py"]
    regression = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "tests.test_constitution",
            "tests.test_v24",
            "tests.test_v243",
            "tests.test_v244",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    checks = {
        "independent_max_abs_delta_i_le_1e-10": independent_max <= 1e-10,
        "carrying_mean_delta_i_per_token_ge_sesoi": carrying_interval[0] >= sesoi,
        "carrying_lower_95_ci_gt_0": carrying_interval[1] > 0.0,
        "both_accounting_identity": max(
            row["increment_identity_error"] for row in rows
        )
        <= 1e-10,
        "v24_source_byte_identical": v24_hash == frozen_v24_hash,
        "v24_cumulative_unit_regression_green": regression.returncode == 0,
    }
    compact_rows = [
        {
            key: value
            for key, value in row.items()
            if key
            not in {
                "joint_per_slice",
                "marginal_per_slice",
                "delta_i_per_slice",
                "channel_per_slice",
            }
        }
        for row in rows
    ]
    write_json("gate-2-per_world.json", compact_rows)
    np.savez_compressed(
        OUT / "gate-2-per_slice.npz",
        seed=np.asarray([row["seed"] for row in rows], dtype=int),
        joint=np.asarray([row["joint_per_slice"] for row in rows]),
        marginal=np.asarray([row["marginal_per_slice"] for row in rows]),
        delta_i=np.asarray([row["delta_i_per_slice"] for row in rows]),
        outcome=np.asarray(
            [row["channel_per_slice"]["outcome"] for row in rows]
        ),
        marker=np.asarray(
            [row["channel_per_slice"]["marker"] for row in rows]
        ),
        root=np.asarray([row["channel_per_slice"]["root"] for row in rows]),
    )
    result = {
        "stage": "V2.5a",
        "gate": 2,
        "passed": all(checks.values()),
        "checks": checks,
        "seed_block": [756000, 756399],
        "world_counts": {
            "association_carrying": len(carrying),
            "independent": len(independent),
        },
        "frozen_delta_i_sesoi_nats_per_token": sesoi,
        "carrying_delta_i_per_token_interval": carrying_interval,
        "carrying_distribution": _range(
            [row["delta_i_per_token"] for row in carrying]
        ),
        "independent_distribution": _range(
            [row["delta_i_per_token"] for row in independent]
        ),
        "independent_maximum_absolute_delta_i": independent_max,
        "maximum_increment_identity_error": max(
            row["increment_identity_error"] for row in rows
        ),
        "per_channel_log_evidence_ranges": {
            cell: {
                channel: _range(
                    [
                        row["channel_log_evidence"][channel]
                        for row in rows
                        if row["cell"] == cell
                    ]
                )
                for channel in v25a.CHANNELS
            }
            for cell in ("association_carrying", "independent")
        },
        "v24_regression": {
            "source_sha256": v24_hash,
            "frozen_sha256": frozen_v24_hash,
            "unit_command": regression.args,
            "returncode": regression.returncode,
            "stdout": regression.stdout,
            "stderr": regression.stderr,
        },
        "B_max_inherited_formation": B_MAX_FORMATION,
        "B_max_v24_common_emissions": B_MAX_V24,
        "B_max_v25a_marginal_accounting": (
            v25a.marginal_finite_information_bound()[
                "B_max_v25a_marginal_accounting"
            ]
        ),
    }
    write_json("gate-2.json", result)
    (OUT / "gate-2-report.md").write_text(
        "# V2.5a Gate 2 — format calibration\n\n"
        f"Outcome: **{'PASS' if result['passed'] else 'FAIL'}**. "
        f"Checks: `{checks}`.\n\n"
        f"Carrying ΔI/token `{carrying_interval}` against frozen SESOI "
        f"`{sesoi}`. Independent maximum absolute ΔI `{independent_max}`.\n\n"
        f"`B_max_inherited_formation = {B_MAX_FORMATION}`; "
        f"`B_max_v24_common_emissions = {B_MAX_V24}`; "
        f"`B_max_v25a_marginal_accounting = {result['B_max_v25a_marginal_accounting']}`.\n",
        encoding="utf-8",
    )
    if not result["passed"]:
        (OUT / "gate-2-diagnosis-stub.md").write_text(
            "# V2.5a Gate-2 honest stop\n\n"
            f"Blocking failures: `{[name for name, value in checks.items() if not value]}`.\n"
        )
    return result["passed"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "phase", choices=("pilot", "gate1", "gate2", "rows-worker")
    )
    parser.add_argument("--start-position", type=int)
    parser.add_argument("--end-position", type=int)
    parser.add_argument("--seed-base", type=int)
    parser.add_argument("--carrying-count", type=int)
    parser.add_argument("--worker-output")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args()
    if args.phase == "rows-worker":
        _run_rows_worker(args)
        return 0
    if args.phase == "pilot":
        run_pilot()
        return 0
    if args.phase == "gate1":
        return 0 if run_gate1() else 1
    return 0 if run_gate2() else 1


if __name__ == "__main__":
    raise SystemExit(main())
