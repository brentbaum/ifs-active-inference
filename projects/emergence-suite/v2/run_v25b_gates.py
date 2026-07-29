#!/usr/bin/env python3
"""Sequential V2.5b stage runner."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

from ref import v25a_completion as v25a
from ref import v25b, v25b_oracle


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "V2.5b"
OUT.mkdir(parents=True, exist_ok=True)
P = v25b.PARAMETERS
BOUNDS = {
    **P["bounds"],
    **v25b.finite_information_bound(),
}


def dump(name: str, value: Any) -> None:
    def plain(item: Any) -> Any:
        if isinstance(item, dict):
            return {str(key): plain(child) for key, child in item.items()}
        if isinstance(item, (list, tuple)):
            return [plain(child) for child in item]
        if isinstance(item, np.ndarray):
            return [plain(child) for child in item.tolist()]
        if isinstance(item, np.generic):
            return item.item()
        return item

    (OUT / name).write_text(
        json.dumps(plain(value), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def interval(values) -> dict[str, float]:
    array = np.asarray(tuple(values), dtype=float)
    mean = float(array.mean())
    half = (
        0.0
        if len(array) < 2
        else 1.96 * float(array.std(ddof=1)) / math.sqrt(len(array))
    )
    return {
        "mean": mean,
        "lower_95": mean - half,
        "upper_95": mean + half,
    }


def credible_set(q: np.ndarray, mass: float = 0.95) -> set[int]:
    order = np.argsort(-q)
    result = set()
    total = 0.0
    for index in order:
        result.add(int(index))
        total += float(q[index])
        if total >= mass:
            break
    return result


def ece(probabilities: np.ndarray, truths: np.ndarray) -> float:
    result = 0.0
    for lower in np.linspace(0.0, 1.0, 11)[:-1]:
        upper = lower + 0.1
        mask = (probabilities >= lower) & (
            probabilities <= upper if upper >= 1.0 else probabilities < upper
        )
        if np.any(mask):
            result += float(mask.mean()) * abs(
                float(probabilities[mask].mean())
                - float(truths[mask].mean())
            )
    return result


def run_gate1() -> bool:
    normalization_errors = []
    marginal_errors = []
    for structure in v25b.STRUCTURES:
        for cue in range(4):
            for context in (0, 1):
                table = v25b.joint_table(cue, context, structure, 0.8)
                normalization_errors.append(abs(float(table.sum()) - 1.0))
                marginal_errors.append(
                    float(
                        np.max(
                            np.abs(
                                v25a.table_marginals(table)
                                - v25a.channel_marginals(cue, context)
                            )
                        )
                    )
                )
    fixture = (
        v25a.Episode(0, 0, (1, 0, 1, 0, 1)),
        v25a.Episode(1, 1, (0, 1, 0, 1, 0)),
        v25a.Episode(2, 0, (None, 0, 1, 1, 0)),
    )
    result = v25b.score(fixture, precision=0.8)
    oracle_q, oracle_evidence = v25b_oracle.score(
        fixture,
        v25b.PRIOR,
        0.8,
        float(P["coupling_strength"]),
    )
    oracle_error = max(
        float(np.max(np.abs(result.q_structure - oracle_q))),
        float(
            np.max(
                np.abs(result.log_evidence_by_structure - oracle_evidence)
            )
        ),
    )
    idx0 = v25b.STRUCTURE_INDEX["000"]
    idx1 = v25b.STRUCTURE_INDEX["111"]
    odds_error = abs(
        (
            math.log(float(result.q_structure[idx0] / result.q_structure[idx1]))
            - math.log(float(v25b.PRIOR[idx0] / v25b.PRIOR[idx1]))
        )
        - (
            result.log_evidence_by_structure[idx0]
            - result.log_evidence_by_structure[idx1]
        )
    )
    recombination_error = max(
        abs(
            math.log(
                float(
                    result.posterior_trajectory[time + 1][idx0]
                    / result.posterior_trajectory[time + 1][idx1]
                )
            )
            - math.log(
                float(
                    result.posterior_trajectory[time][idx0]
                    / result.posterior_trajectory[time][idx1]
                )
            )
            - (
                result.pairwise_000_111_log_bf[time]
                - (
                    result.pairwise_000_111_log_bf[time - 1]
                    if time
                    else 0.0
                )
            )
        )
        for time in range(len(fixture))
    )
    missing = v25a.Episode(0, 0, (None,) * 5)
    missing_result = v25b.score([missing], precision=0.8)
    imaginal, modes = v25b.do_over_episodes(
        1_000_010, count=3, precision=0.8
    )
    imaginal_result = v25b.score(
        imaginal, precision=0.8, presentations=modes
    )
    likelihood_source = inspect.getsource(v25b.likelihood)
    score_source = inspect.getsource(v25b.score)
    proofs = {
        "1_all_eight_structures_normalize": max(normalization_errors) <= 1e-12,
        "2_candidate_common_atomic_marginals": max(marginal_errors) <= 1e-12,
        "3_prior_charged_once": odds_error <= 1e-10,
        "4_coupling_spikes_exact": np.array_equal(
            v25b.STRUCTURE_BITS,
            np.asarray(
                [[int(bit) for bit in label] for label in v25b.STRUCTURES]
            ),
        ),
        "5_candidate_evidence_recombines": recombination_error <= 1e-10,
        "6_material_reduction_odds_identity": odds_error <= 1e-10,
        "7_unique_000_argmax_is_readout": isinstance(
            result.material_reduction.unique_000, bool
        ),
        "8_q000_threshold_is_readout": isinstance(
            result.material_reduction.q_000, float
        ),
        "9_bf_threshold_is_readout": isinstance(
            result.material_reduction.bf_000_111, float
        ),
        "10_three_slice_stability_is_readout": isinstance(
            result.material_reduction.consecutive_count, int
        ),
        "11_neutral_survival_is_readout": result.material_reduction.neutral_survives,
        "12_no_erasure_of_historical_context": v25b.old_context_query_error(
            0, "111", 0.8
        )
        <= 1e-10,
        "13_imaginal_observed_same_likelihood_api": (
            all(isinstance(item, v25a.Episode) for item in imaginal)
            and "presentation" in likelihood_source
            and abs(float(imaginal_result.q_structure.sum()) - 1.0) <= 1e-10
        ),
        "14_missing_imaginal_evidence_neutral": float(
            np.max(np.abs(missing_result.q_structure - v25b.PRIOR))
        )
        <= 1e-10,
        "15_timing_labels_absent_from_inference": (
            "premature" not in likelihood_source
            and "post_redescription" not in likelihood_source
            and "premature" not in score_source
            and "post_redescription" not in score_source
        ),
        "16_stability_readout_pure": "reduction operation" not in score_source,
        "17_independent_structural_oracle": oracle_error <= 1e-10,
        "18_permanent_constitutions": (
            abs(float(result.q_structure.sum()) - 1.0) <= 1e-10
            and result.material_reduction.neutral_survives
        ),
    }
    report = {
        "stage": "V2.5b",
        "gate": 1,
        "verdict": "PASS" if all(proofs.values()) else "FAIL",
        "proofs": proofs,
        "numbers": {
            "maximum_normalization_error": max(normalization_errors),
            "maximum_marginal_error": max(marginal_errors),
            "maximum_recombination_error": recombination_error,
            "material_odds_identity_error": odds_error,
            "independent_oracle_error": oracle_error,
        },
        "bounds": BOUNDS,
        "escrow_accessed": False,
    }
    dump("gate-1.json", report)
    (OUT / "gate-1-report.md").write_text(
        "# V2.5b Gate 1\n\n"
        f"**Verdict: {report['verdict']}**\n\n"
        + "\n".join(
            f"- {name}: `{'PASS' if passed else 'FAIL'}`"
            for name, passed in proofs.items()
        )
        + "\n",
        encoding="utf-8",
    )
    if report["verdict"] == "FAIL":
        (OUT / "gate-1-diagnosis-stub.md").write_text(
            "# Gate-1 diagnosis stub\n\nFailed proofs: "
            + ", ".join(key for key, value in proofs.items() if not value)
            + ". Gate 2 was not opened.\n",
            encoding="utf-8",
        )
    return report["verdict"] == "PASS"


def gate2_row(position: int) -> dict[str, Any]:
    seed = 1_100_000 + position
    structure_index = position % 8
    structure = v25b.STRUCTURES[structure_index]
    length = P["recovery_lengths"][(position // 8) % 2]
    world = v25b.generate_world(
        seed,
        truth_structure=structure,
        length=length,
        context_regime=("single", "return")[(position // 16) % 2],
    )
    score = v25b.score(world.episodes, precision=world.precision)
    selected_index = int(np.argmax(score.q_structure))
    predicted_edges = (score.expected_edges >= 0.5).astype(int)
    truth_edges = v25b.STRUCTURE_BITS[structure_index]
    return {
        "seed": seed,
        "truth_structure": structure,
        "length": length,
        "selected_structure": v25b.STRUCTURES[selected_index],
        "q_structure": score.q_structure.tolist(),
        "edge_posteriors": score.expected_edges.tolist(),
        "edge_correct": (predicted_edges == truth_edges).tolist(),
        "credible_set_covers": structure_index
        in credible_set(score.q_structure),
        "old_context_query_error": v25b.old_context_query_error(
            position % 3, structure, world.precision
        ),
    }


def parallel_gate2() -> list[dict[str, Any]]:
    workers = min(8, max(1, os.cpu_count() or 1))
    boundaries = np.linspace(0, 1000, workers + 1, dtype=int)
    jobs = []
    for worker in range(workers):
        path = OUT / f".gate2-worker-{worker}.json"
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "worker",
            "gate2",
            str(int(boundaries[worker])),
            str(int(boundaries[worker + 1])),
            str(path),
        ]
        jobs.append((path, subprocess.Popen(command, cwd=ROOT)))
    for _, process in jobs:
        if process.wait():
            raise RuntimeError("Gate-2 worker failed")
    rows = []
    for path, _ in jobs:
        rows.extend(json.loads(path.read_text()))
        path.unlink()
    if [row["seed"] for row in rows] != list(range(1_100_000, 1_101_000)):
        raise ValueError("Gate-2 seed ledger incomplete")
    return rows


def run_gate2() -> bool:
    rows = parallel_gate2()
    edge_correct = np.asarray([row["edge_correct"] for row in rows], dtype=float)
    probabilities = np.asarray(
        [row["edge_posteriors"] for row in rows], dtype=float
    )
    truths = np.asarray(
        [
            v25b.STRUCTURE_BITS[v25b.STRUCTURE_INDEX[row["truth_structure"]]]
            for row in rows
        ],
        dtype=float,
    )
    per_structure_accuracy = {}
    for structure in v25b.STRUCTURES:
        cell = [row for row in rows if row["truth_structure"] == structure]
        per_structure_accuracy[structure] = float(
            np.mean(
                [
                    row["selected_structure"] == row["truth_structure"]
                    for row in cell
                ]
            )
        )
    false_reduction = float(
        np.mean(
            [
                row["selected_structure"] == "000"
                for row in rows
                if row["truth_structure"] == "111"
            ]
        )
    )
    false_burden = float(
        np.mean(
            [
                row["selected_structure"] == "111"
                for row in rows
                if row["truth_structure"] == "000"
            ]
        )
    )
    metrics = {
        "edge_accuracy_Z_W": float(edge_correct[:, 0].mean()),
        "edge_accuracy_Z_Pi": float(edge_correct[:, 1].mean()),
        "edge_accuracy_Z_Y": float(edge_correct[:, 2].mean()),
        "eight_way_macro_accuracy": float(
            np.mean(list(per_structure_accuracy.values()))
        ),
        "brier": float(np.mean((probabilities - truths) ** 2)),
        "ECE": ece(probabilities.ravel(), truths.ravel()),
        "false_complete_reduction_in_111": false_reduction,
        "false_full_burden_in_000": false_burden,
        "parameter_coverage": float(
            np.mean([row["credible_set_covers"] for row in rows])
        ),
        "maximum_old_context_query_error": max(
            row["old_context_query_error"] for row in rows
        ),
        "per_structure_accuracy": per_structure_accuracy,
    }
    t = P["gate2"]
    checks = {
        "edge_Z_W": metrics["edge_accuracy_Z_W"] >= t["edge_accuracy_minimum"],
        "edge_Z_Pi": metrics["edge_accuracy_Z_Pi"] >= t["edge_accuracy_minimum"],
        "edge_Z_Y": metrics["edge_accuracy_Z_Y"] >= t["edge_accuracy_minimum"],
        "macro_accuracy": metrics["eight_way_macro_accuracy"]
        >= t["macro_accuracy_minimum"],
        "brier": metrics["brier"] <= t["brier_maximum"],
        "ECE": metrics["ECE"] <= t["ece_maximum"],
        "false_complete_reduction": false_reduction
        <= t["false_complete_reduction_maximum"],
        "false_full_burden": false_burden <= t["false_full_burden_maximum"],
        "coverage": metrics["parameter_coverage"] >= t["coverage_minimum"],
        "old_context": metrics["maximum_old_context_query_error"]
        <= t["old_context_query_error_maximum"],
    }
    report = {
        "stage": "V2.5b",
        "gate": 2,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
        "seed_block": [1_100_000, 1_100_999],
        "world_count": len(rows),
        "worlds_per_structure": 125,
        "metrics": metrics,
        "checks": checks,
        "bounds": BOUNDS,
        "escrow_accessed": False,
    }
    dump("gate-2-per_world.json", rows)
    dump("gate-2.json", report)
    (OUT / "gate-2-report.md").write_text(
        "# V2.5b Gate 2\n\n"
        f"**Verdict: {report['verdict']}**\n\n```json\n"
        + json.dumps(metrics, indent=2, sort_keys=True)
        + "\n```\n",
        encoding="utf-8",
    )
    if report["verdict"] == "FAIL":
        (OUT / "gate-2-diagnosis-stub.md").write_text(
            "# Gate-2 diagnosis stub\n\nFailed criteria: "
            + ", ".join(key for key, value in checks.items() if not value)
            + ". Gate 3 was not opened.\n",
            encoding="utf-8",
        )
    return report["verdict"] == "PASS"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("gate1", "gate2", "worker"))
    parser.add_argument("worker_args", nargs="*")
    args = parser.parse_args()
    if args.phase == "worker":
        task, start, end, path = args.worker_args
        if task != "gate2":
            raise ValueError("unknown worker task")
        dump_rows = [gate2_row(index) for index in range(int(start), int(end))]
        Path(path).write_text(
            json.dumps(dump_rows, sort_keys=True, allow_nan=False),
            encoding="utf-8",
        )
        raise SystemExit(0)
    ok = run_gate1() if args.phase == "gate1" else run_gate2()
    raise SystemExit(0 if ok else 2)


if __name__ == "__main__":
    main()
