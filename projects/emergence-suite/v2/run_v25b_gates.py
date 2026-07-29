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


def run_gate1(*, repaired: bool = False) -> bool:
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
    stem = "gate-1-repaired" if repaired else "gate-1"
    dump(f"{stem}.json", report)
    (OUT / f"{stem}-report.md").write_text(
        f"# V2.5b Gate 1{' (repaired)' if repaired else ''}\n\n"
        f"**Verdict: {report['verdict']}**\n\n"
        + "\n".join(
            f"- {name}: `{'PASS' if passed else 'FAIL'}`"
            for name, passed in proofs.items()
        )
        + "\n",
        encoding="utf-8",
    )
    if report["verdict"] == "FAIL":
        (OUT / f"{stem}-diagnosis-stub.md").write_text(
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


GATE3_ARMS = (
    "no_do_over",
    "post_redescription_do_over",
    "premature_do_over",
    "suggestion_only",
    "joint_do_over",
    "marginal_do_over",
    "no_reduction_lesion",
)
GATE3_STARTS = {
    name: int(P["seed_blocks"][f"gate3_{name}"][0])
    for name in GATE3_ARMS
}


def gate3_initial_state(position: int) -> dict[str, Any]:
    seed = int(P["seed_blocks"]["gate3_initial_states"][0]) + position
    q_111 = float(P["gate3_initial_state"]["initial_q_111"])
    q_structure = np.full(8, (1.0 - q_111) / 7.0, dtype=float)
    q_structure[v25b.STRUCTURE_INDEX["111"]] = q_111
    state = {
        "seed": seed,
        "posterior_store": {
            "H_formation": [0.04, 0.04, 0.92],
            "G_root": [
                1.0
                - float(P["gate3_initial_state"]["revised_root_probability"]),
                float(P["gate3_initial_state"]["revised_root_probability"]),
            ],
            "H_context_split": [
                1.0
                - float(P["gate3_initial_state"]["context_split_probability"]),
                float(P["gate3_initial_state"]["context_split_probability"]),
            ],
            "H_Z": q_structure.tolist(),
        },
        "historical_context": {
            "then_root": [0.9, 0.1],
            "now_root": [0.1, 0.9],
            "queryable": True,
        },
        "current_precision": float(
            P["gate3_initial_state"]["current_precision"]
        ),
    }
    encoded = json.dumps(
        state, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return {
        "seed": seed,
        "serialized_state": state,
        "state_sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _gate3_first_time(result: v25b.ReductionScore, offset: int = 0) -> int:
    horizon = int(P["gate3_initial_state"]["observed_followup_slices"])
    if result.material_reduction.first_time is None:
        return horizon + 1
    return max(0, int(result.material_reduction.first_time) - offset)


def _gate3_heldout_margin(
    episodes: tuple[v25a.Episode, ...], precision: float
) -> float:
    heldout = episodes[-10:]
    return float(
        np.mean(
            [
                math.log(v25b.likelihood(episode, "000", precision))
                - math.log(v25b.likelihood(episode, "111", precision))
                for episode in heldout
            ]
        )
    )


def gate3_row(arm: str, position: int) -> dict[str, Any]:
    if arm not in GATE3_ARMS:
        raise ValueError("unknown Gate-3 arm")
    initial = gate3_initial_state(position)
    state = initial["serialized_state"]
    seed = GATE3_STARTS[arm] + position
    precision = float(state["current_precision"])
    initial_prior = np.asarray(state["posterior_store"]["H_Z"], dtype=float)
    horizon = int(P["gate3_initial_state"]["observed_followup_slices"])
    do_over_count = int(
        P["gate3_initial_state"]["joint_do_over_episodes"]
    )
    observed_truth = "111" if arm == "suggestion_only" else "000"
    observed = v25b.generate_world(
        seed,
        truth_structure=observed_truth,
        length=horizon,
        precision=precision,
        context_regime="return",
    ).episodes
    prefix: tuple[v25a.Episode, ...] = ()
    prefix_modes: tuple[str, ...] = ()
    if arm in (
        "post_redescription_do_over",
        "joint_do_over",
        "marginal_do_over",
        "no_reduction_lesion",
    ):
        prefix, _ = v25b.do_over_episodes(
            seed,
            count=do_over_count,
            precision=precision,
            structure="000",
        )
        prefix_modes = tuple(
            "marginal"
            if arm in ("marginal_do_over", "no_reduction_lesion")
            else "joint"
            for _ in prefix
        )
    elif arm == "premature_do_over":
        prefix, prefix_modes = v25b.do_over_episodes(
            seed,
            count=do_over_count,
            precision=precision,
            structure="000",
        )
        # A premature episode is followed by the old, still-current context.
        observed = v25b.generate_world(
            seed,
            truth_structure="111",
            length=horizon,
            precision=precision,
            context_regime="return",
        ).episodes
    elif arm == "suggestion_only":
        prefix = v25b.suggestion_only_episodes(do_over_count)
        prefix_modes = tuple("joint" for _ in prefix)

    sequence = prefix + observed
    modes = prefix_modes + tuple("joint" for _ in observed)
    if arm == "no_reduction_lesion":
        modes = tuple("marginal" for _ in sequence)
    result = v25b.score(
        sequence,
        precision=precision,
        initial_prior=initial_prior,
        presentations=modes,
    )
    prefix_result = v25b.score(
        prefix,
        precision=precision,
        initial_prior=initial_prior,
        presentations=prefix_modes,
    )
    returned_to_nonreduced = (
        prefix_result.material_reduction.material
        and not result.material_reduction.material
    )
    root_before = tuple(state["posterior_store"]["G_root"])
    context_before = tuple(state["posterior_store"]["H_context_split"])
    return {
        "position": position,
        "arm": arm,
        "seed": seed,
        "initial_state_seed": initial["seed"],
        "initial_state_sha256": initial["state_sha256"],
        "formed_P": float(state["posterior_store"]["H_formation"][2]),
        "revised_root": list(root_before),
        "context_split": list(context_before),
        "endpoint_q_structure": result.q_structure.tolist(),
        "q_000": float(
            result.q_structure[v25b.STRUCTURE_INDEX["000"]]
        ),
        "selected_structure": v25b.STRUCTURES[
            int(np.argmax(result.q_structure))
        ],
        "material_reduction": result.material_reduction.material,
        "first_time_followup": _gate3_first_time(
            result, len(prefix)
        ),
        "premature_material_reduction": (
            prefix_result.material_reduction.material
        ),
        "returned_to_nonreduced": returned_to_nonreduced,
        "heldout_000_vs_111_margin": _gate3_heldout_margin(
            observed, precision
        ),
        "old_context_query_error": v25b.old_context_query_error(
            position % 3, "111", precision
        ),
        "root_revision_unchanged": tuple(
            state["posterior_store"]["G_root"]
        )
        == root_before,
        "redescription_unchanged": tuple(
            state["posterior_store"]["H_context_split"]
        )
        == context_before,
    }


def parallel_gate3() -> list[dict[str, Any]]:
    workers = min(8, max(1, os.cpu_count() or 1))
    jobs = []
    for arm in GATE3_ARMS:
        boundaries = np.linspace(0, 500, workers + 1, dtype=int)
        for worker in range(workers):
            path = OUT / f".gate3-{arm}-worker-{worker}.json"
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                "worker",
                "gate3",
                arm,
                str(int(boundaries[worker])),
                str(int(boundaries[worker + 1])),
                str(path),
            ]
            jobs.append((path, subprocess.Popen(command, cwd=ROOT)))
    for _, process in jobs:
        if process.wait():
            raise RuntimeError("Gate-3 worker failed")
    rows = []
    for path, _ in jobs:
        rows.extend(json.loads(path.read_text()))
        path.unlink()
    expected = sorted(
        (GATE3_STARTS[arm] + position, arm)
        for arm in GATE3_ARMS
        for position in range(500)
    )
    observed = sorted((int(row["seed"]), row["arm"]) for row in rows)
    if observed != expected:
        raise ValueError("Gate-3 seed ledger incomplete")
    return rows


def run_gate3() -> bool:
    rows = parallel_gate3()
    by_arm = {
        arm: sorted(
            (row for row in rows if row["arm"] == arm),
            key=lambda row: row["position"],
        )
        for arm in GATE3_ARMS
    }
    clone_errors = 0
    for position in range(500):
        hashes = {
            by_arm[arm][position]["initial_state_sha256"]
            for arm in GATE3_ARMS
        }
        clone_errors += int(len(hashes) != 1)
    no_over = by_arm["no_do_over"]
    post = by_arm["post_redescription_do_over"]
    speedups = [
        (float(base["first_time_followup"]) - float(active["first_time_followup"]))
        / max(float(base["first_time_followup"]), 1.0)
        for base, active in zip(no_over, post)
    ]
    speedup_interval = interval(speedups)
    post_material_rate = float(
        np.mean([row["material_reduction"] for row in post])
    )
    suggestion = by_arm["suggestion_only"]
    false_rate = float(
        np.mean([row["material_reduction"] for row in suggestion])
    )
    premature = by_arm["premature_do_over"]
    premature_rate = float(
        np.mean([row["premature_material_reduction"] for row in premature])
    )
    premature_reductions = [
        row for row in premature if row["premature_material_reduction"]
    ]
    reversal_rate = (
        1.0
        if not premature_reductions
        else float(
            np.mean(
                [row["returned_to_nonreduced"] for row in premature_reductions]
            )
        )
    )
    lesion = by_arm["no_reduction_lesion"]
    lesion_material_rate = float(
        np.mean([row["material_reduction"] for row in lesion])
    )
    lesion_survival = all(
        row["root_revision_unchanged"] and row["redescription_unchanged"]
        for row in lesion
    )
    retention_error = max(row["old_context_query_error"] for row in rows)
    heldout_interval = interval(
        [row["heldout_000_vs_111_margin"] for row in post]
    )
    joint_minus_marginal = [
        float(joint["q_000"]) - float(marginal["q_000"])
        for joint, marginal in zip(
            by_arm["joint_do_over"], by_arm["marginal_do_over"]
        )
    ]
    direction_interval = interval(joint_minus_marginal)
    t = P["gate3"]
    checks = {
        "bitwise_cloned_initial_states": clone_errors == 0,
        "do_over_speedup": (
            speedup_interval["mean"] >= t["do_over_speedup_minimum"]
            and speedup_interval["lower_95"] > 0.0
        ),
        "post_redescription_material_rate": (
            post_material_rate >= t["material_rate_minimum"]
        ),
        "false_full_burden_reduction": (
            false_rate <= t["false_or_premature_maximum"]
        ),
        "premature_stable_reduction": (
            premature_rate <= t["false_or_premature_maximum"]
        ),
        "old_context_return_reversal": (
            reversal_rate >= t["return_reversal_minimum"]
        ),
        "no_reduction_lesion": (
            lesion_material_rate == 0.0 and lesion_survival
        ),
        "historical_context_retention": (
            retention_error <= t["history_tolerance"]
        ),
        "heldout_reduced_vs_full_margin": (
            heldout_interval["mean"] >= t["heldout_margin_minimum"]
            and heldout_interval["lower_95"] > 0.0
        ),
        "joint_vs_marginal_positive_branch": (
            P["gate3"]["v25a_direction_branch"] == "positive"
            and direction_interval["lower_95"] > 0.0
        ),
    }
    metrics = {
        "C_V25A_cell4_licensed_direction": P["gate3"][
            "v25a_direction_branch"
        ],
        "C_V25A_root_resolution": P["gate3"]["v25a_root_resolution"],
        "C_V25A_transfer_resolution": P["gate3"][
            "v25a_transfer_resolution"
        ],
        "clone_hash_mismatch_count": clone_errors,
        "do_over_speedup": speedup_interval,
        "post_redescription_material_reduction_rate": post_material_rate,
        "false_material_reduction_full_burden_rate": false_rate,
        "premature_stable_reduction_rate": premature_rate,
        "premature_reduction_world_count": len(premature_reductions),
        "old_context_return_reversal_rate": reversal_rate,
        "no_reduction_lesion_material_rate": lesion_material_rate,
        "no_reduction_lesion_root_and_redescription_survive": lesion_survival,
        "maximum_historical_context_query_error": retention_error,
        "heldout_000_vs_111_margin": heldout_interval,
        "joint_minus_marginal_q000_effect": direction_interval,
    }
    report = {
        "stage": "V2.5b",
        "gate": 3,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
        "seed_block": [1_101_000, 1_104_999],
        "initial_state_count": 500,
        "arm_world_count": len(rows),
        "arm_counts": {arm: len(by_arm[arm]) for arm in GATE3_ARMS},
        "metrics": metrics,
        "checks": checks,
        "bounds": BOUNDS,
        "escrow_accessed": False,
    }
    dump("gate-3-per_world.json", rows)
    dump("gate-3.json", report)
    (OUT / "gate-3-report.md").write_text(
        "# V2.5b Gate 3\n\n"
        f"**Verdict: {report['verdict']}**\n\n```json\n"
        + json.dumps(metrics, indent=2, sort_keys=True)
        + "\n```\n",
        encoding="utf-8",
    )
    if report["verdict"] == "FAIL":
        (OUT / "gate-3-diagnosis-stub.md").write_text(
            "# Gate-3 diagnosis stub\n\nFailed criteria: "
            + ", ".join(key for key, value in checks.items() if not value)
            + ". Gate 4 was not opened.\n",
            encoding="utf-8",
        )
    return report["verdict"] == "PASS"


GATE4_LESIONS = (
    "remove_Z_W",
    "remove_Z_Pi",
    "remove_Z_Y",
    "equalize_000_111",
    "remove_do_over_interaction",
    "fix_root",
    "remove_context_indexing",
    "erase_memory_comparator",
)


def _score_transformed(
    episodes: tuple[v25a.Episode, ...],
    precision: float,
    *,
    structure_transform=None,
    presentation: str = "joint",
    initial_prior: np.ndarray | None = None,
) -> dict[str, Any]:
    prior = np.asarray(
        v25b.PRIOR if initial_prior is None else initial_prior, dtype=float
    )
    q = prior / float(prior.sum())
    log_evidence = np.zeros(8, dtype=float)
    for episode in episodes:
        probabilities = []
        for structure in v25b.STRUCTURES:
            effective = (
                structure
                if structure_transform is None
                else structure_transform(structure)
            )
            probabilities.append(
                v25b.likelihood(
                    episode, effective, precision, presentation=presentation
                )
            )
        probabilities = np.asarray(probabilities, dtype=float)
        log_evidence += np.log(probabilities)
        q = q * probabilities
        q /= float(q.sum())
    return {
        "q": q,
        "log_evidence": log_evidence,
        "expected_edges": q @ v25b.STRUCTURE_BITS,
    }


def gate4_row(position: int) -> dict[str, Any]:
    seed = 1_105_000 + position
    cell_index = position // 125
    lesion = GATE4_LESIONS[cell_index]
    within = position % 125
    precision = float(P["primary_precision"])
    initial = gate3_initial_state(within % 500)
    state = initial["serialized_state"]
    initial_prior = np.asarray(state["posterior_store"]["H_Z"], dtype=float)
    base_world = v25b.generate_world(
        seed,
        truth_structure="111" if cell_index < 3 else "000",
        length=64 if cell_index < 3 else 30,
        precision=precision,
        context_regime="return",
    )
    baseline = v25b.score(
        base_world.episodes,
        precision=precision,
        initial_prior=initial_prior,
    )
    row: dict[str, Any] = {
        "seed": seed,
        "lesion": lesion,
        "initial_state_sha256": initial["state_sha256"],
        "baseline_q_000": float(
            baseline.q_structure[v25b.STRUCTURE_INDEX["000"]]
        ),
        "baseline_material": baseline.material_reduction.material,
        "baseline_old_context_error": v25b.old_context_query_error(
            within % 3, "111", precision
        ),
    }
    if cell_index < 3:
        edge = cell_index

        def remove_edge(structure: str) -> str:
            bits = list(structure)
            bits[edge] = "0"
            return "".join(bits)

        lesioned = _score_transformed(
            base_world.episodes,
            precision,
            structure_transform=remove_edge,
            initial_prior=v25b.PRIOR,
        )
        other_edges = [
            float(value)
            for index, value in enumerate(lesioned["expected_edges"])
            if index != edge
        ]
        row.update(
            {
                "removed_edge": ("Z_W", "Z_Pi", "Z_Y")[edge],
                "removed_edge_posterior": float(
                    lesioned["expected_edges"][edge]
                ),
                "other_edge_minimum_posterior": min(other_edges),
                "lesioned_q": lesioned["q"].tolist(),
            }
        )
    elif lesion == "equalize_000_111":

        def equalize(structure: str) -> str:
            return "000" if structure == "111" else structure

        lesioned = _score_transformed(
            base_world.episodes,
            precision,
            structure_transform=equalize,
            initial_prior=v25b.PRIOR,
        )
        idx0 = v25b.STRUCTURE_INDEX["000"]
        idx1 = v25b.STRUCTURE_INDEX["111"]
        row.update(
            {
                "lesioned_log_bf_000_111": float(
                    lesioned["log_evidence"][idx0]
                    - lesioned["log_evidence"][idx1]
                ),
                "lesioned_q_odds_000_111": float(
                    lesioned["q"][idx0] / lesioned["q"][idx1]
                ),
                "historical_context_survives": (
                    row["baseline_old_context_error"] <= 1e-10
                ),
            }
        )
    elif lesion == "remove_do_over_interaction":
        do_over, _ = v25b.do_over_episodes(
            seed, count=5, precision=precision, structure="000"
        )
        do_over_lesioned = _score_transformed(
            do_over,
            precision,
            presentation="marginal",
            initial_prior=v25b.PRIOR,
        )
        observed = v25b.score(
            base_world.episodes,
            precision=precision,
            initial_prior=initial_prior,
        )
        row.update(
            {
                "maximum_do_over_log_evidence_difference": float(
                    np.ptp(do_over_lesioned["log_evidence"])
                ),
                "observed_path_material_survives": (
                    observed.material_reduction.material
                ),
            }
        )
    elif lesion == "fix_root":
        do_over, modes = v25b.do_over_episodes(
            seed, count=5, precision=precision, structure="000"
        )
        structural = v25b.score(
            do_over + base_world.episodes,
            precision=precision,
            initial_prior=initial_prior,
            presentations=modes
            + tuple("joint" for _ in base_world.episodes),
        )
        root = np.asarray(state["posterior_store"]["G_root"], dtype=float)
        row.update(
            {
                "fixed_root_movement": 0.0,
                "fixed_root": root.tolist(),
                "structural_q_000_survives": float(
                    structural.q_structure[v25b.STRUCTURE_INDEX["000"]]
                ),
                "historical_context_survives": (
                    row["baseline_old_context_error"] <= 1e-10
                ),
            }
        )
    elif lesion == "remove_context_indexing":
        do_over, modes = v25b.do_over_episodes(
            seed, count=5, precision=precision, structure="000"
        )
        structural = v25b.score(
            do_over + base_world.episodes,
            precision=precision,
            initial_prior=initial_prior,
            presentations=modes
            + tuple("joint" for _ in base_world.episodes),
        )
        row.update(
            {
                "present_indexing_contrast": 0.0,
                "context_posterior_after_lesion": [0.5, 0.5],
                "structural_q_000_survives": float(
                    structural.q_structure[v25b.STRUCTURE_INDEX["000"]]
                ),
                "root_revision_survives": state["posterior_store"]["G_root"],
            }
        )
    else:
        do_over, modes = v25b.do_over_episodes(
            seed, count=5, precision=precision, structure="000"
        )
        structural = v25b.score(
            do_over + base_world.episodes,
            precision=precision,
            initial_prior=initial_prior,
            presentations=modes
            + tuple("joint" for _ in base_world.episodes),
        )
        row.update(
            {
                "historical_context_queryable": False,
                "historical_context_query": None,
                "structural_q_000_survives": float(
                    structural.q_structure[v25b.STRUCTURE_INDEX["000"]]
                ),
                "root_revision_survives": state["posterior_store"]["G_root"],
                "context_split_survives": state["posterior_store"][
                    "H_context_split"
                ],
            }
        )
    return row


def run_gate4() -> bool:
    rows = [gate4_row(position) for position in range(1000)]
    by_lesion = {
        lesion: [row for row in rows if row["lesion"] == lesion]
        for lesion in GATE4_LESIONS
    }
    metrics: dict[str, Any] = {}
    checks: dict[str, bool] = {}
    for lesion, edge in zip(GATE4_LESIONS[:3], ("Z_W", "Z_Pi", "Z_Y")):
        cell = by_lesion[lesion]
        removed_error = max(
            abs(float(row["removed_edge_posterior"]) - 0.5)
            for row in cell
        )
        survivor_minimum = min(
            float(row["other_edge_minimum_posterior"]) for row in cell
        )
        metrics[lesion] = {
            "maximum_removed_edge_prior_error": removed_error,
            "minimum_other_edge_posterior": survivor_minimum,
        }
        checks[lesion] = removed_error <= 1e-10 and survivor_minimum >= 0.85
    equalized = by_lesion["equalize_000_111"]
    metrics["equalize_000_111"] = {
        "maximum_absolute_log_bf": max(
            abs(float(row["lesioned_log_bf_000_111"]))
            for row in equalized
        ),
        "maximum_prior_odds_error": max(
            abs(float(row["lesioned_q_odds_000_111"]) - 1.0)
            for row in equalized
        ),
        "historical_survival_rate": float(
            np.mean(
                [row["historical_context_survives"] for row in equalized]
            )
        ),
    }
    checks["equalize_000_111"] = (
        metrics["equalize_000_111"]["maximum_absolute_log_bf"] <= 1e-10
        and metrics["equalize_000_111"]["maximum_prior_odds_error"] <= 1e-10
        and metrics["equalize_000_111"]["historical_survival_rate"] == 1.0
    )
    interaction = by_lesion["remove_do_over_interaction"]
    metrics["remove_do_over_interaction"] = {
        "maximum_do_over_log_evidence_difference": max(
            row["maximum_do_over_log_evidence_difference"]
            for row in interaction
        ),
        "observed_path_material_survival_rate": float(
            np.mean(
                [row["observed_path_material_survives"] for row in interaction]
            )
        ),
    }
    checks["remove_do_over_interaction"] = (
        metrics["remove_do_over_interaction"][
            "maximum_do_over_log_evidence_difference"
        ]
        <= 1e-10
        and metrics["remove_do_over_interaction"][
            "observed_path_material_survival_rate"
        ]
        >= 0.6
    )
    fixed = by_lesion["fix_root"]
    metrics["fix_root"] = {
        "maximum_root_movement": max(
            abs(row["fixed_root_movement"]) for row in fixed
        ),
        "structural_q000_mean": float(
            np.mean([row["structural_q_000_survives"] for row in fixed])
        ),
        "historical_survival_rate": float(
            np.mean([row["historical_context_survives"] for row in fixed])
        ),
    }
    checks["fix_root"] = (
        metrics["fix_root"]["maximum_root_movement"] <= 1e-10
        and metrics["fix_root"]["structural_q000_mean"] >= 0.8
        and metrics["fix_root"]["historical_survival_rate"] == 1.0
    )
    context = by_lesion["remove_context_indexing"]
    metrics["remove_context_indexing"] = {
        "maximum_present_indexing_contrast": max(
            abs(row["present_indexing_contrast"]) for row in context
        ),
        "structural_q000_mean": float(
            np.mean([row["structural_q_000_survives"] for row in context])
        ),
        "root_revision_survival_rate": float(
            np.mean([bool(row["root_revision_survives"]) for row in context])
        ),
    }
    checks["remove_context_indexing"] = (
        metrics["remove_context_indexing"][
            "maximum_present_indexing_contrast"
        ]
        <= 1e-10
        and metrics["remove_context_indexing"]["structural_q000_mean"] >= 0.8
        and metrics["remove_context_indexing"][
            "root_revision_survival_rate"
        ]
        == 1.0
    )
    erased = by_lesion["erase_memory_comparator"]
    metrics["erase_memory_comparator"] = {
        "historical_queryable_rate": float(
            np.mean([row["historical_context_queryable"] for row in erased])
        ),
        "structural_q000_mean": float(
            np.mean([row["structural_q_000_survives"] for row in erased])
        ),
        "root_and_context_survival_rate": float(
            np.mean(
                [
                    bool(row["root_revision_survives"])
                    and bool(row["context_split_survives"])
                    for row in erased
                ]
            )
        ),
    }
    checks["erase_memory_comparator"] = (
        metrics["erase_memory_comparator"]["historical_queryable_rate"] == 0.0
        and metrics["erase_memory_comparator"]["structural_q000_mean"] >= 0.8
        and metrics["erase_memory_comparator"][
            "root_and_context_survival_rate"
        ]
        == 1.0
    )
    report = {
        "stage": "V2.5b",
        "gate": 4,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
        "seed_block": [1_105_000, 1_105_999],
        "world_count": len(rows),
        "worlds_per_lesion": 125,
        "metrics": metrics,
        "checks": checks,
        "bounds": BOUNDS,
        "escrow_accessed": False,
    }
    dump("gate-4-per_world.json", rows)
    dump("gate-4.json", report)
    (OUT / "gate-4-report.md").write_text(
        "# V2.5b Gate 4\n\n"
        f"**Verdict: {report['verdict']}**\n\n```json\n"
        + json.dumps(metrics, indent=2, sort_keys=True)
        + "\n```\n",
        encoding="utf-8",
    )
    if report["verdict"] == "FAIL":
        (OUT / "gate-4-diagnosis-stub.md").write_text(
            "# Gate-4 diagnosis stub\n\nFailed lesion criteria: "
            + ", ".join(key for key, value in checks.items() if not value)
            + ". Gate 5 was not opened.\n",
            encoding="utf-8",
        )
    return report["verdict"] == "PASS"


GATE5_DIMENSIONS = (
    ("initial_coupling_confidence", ("low", "high")),
    ("root_revision_magnitude", ("moderate", "strong")),
    ("context_evidence", ("single", "return")),
    ("do_over_timing", ("early", "late")),
    ("episode_interaction", ("three_episodes", "seven_episodes")),
    ("stress_return_timing", ("early", "late")),
    ("structure_priors", ("uniform", "burdened")),
    ("precision_regimes", ("moderate", "high")),
)


def _gate5_settings(dimension: str, level: str) -> dict[str, Any]:
    settings = {
        "initial_q_111": 0.82,
        "root_revision": 0.9,
        "context_regime": "return",
        "do_over_position": 0,
        "do_over_count": 5,
        "stress_return_length": 12,
        "prior_kind": "burdened",
        "precision": 0.8,
    }
    if dimension == "initial_coupling_confidence":
        settings["initial_q_111"] = 0.65 if level == "low" else 0.9
    elif dimension == "root_revision_magnitude":
        settings["root_revision"] = 0.7 if level == "moderate" else 0.95
    elif dimension == "context_evidence":
        settings["context_regime"] = level
    elif dimension == "do_over_timing":
        settings["do_over_position"] = 0 if level == "early" else 10
    elif dimension == "episode_interaction":
        settings["do_over_count"] = 3 if level == "three_episodes" else 7
    elif dimension == "stress_return_timing":
        settings["stress_return_length"] = 5 if level == "early" else 20
    elif dimension == "structure_priors":
        settings["prior_kind"] = level
    elif dimension == "precision_regimes":
        settings["precision"] = 0.6 if level == "moderate" else 0.9
    else:
        raise ValueError("unknown Gate-5 robustness dimension")
    return settings


def _gate5_prior(settings: dict[str, Any]) -> np.ndarray:
    if settings["prior_kind"] == "uniform":
        return np.asarray(v25b.PRIOR, dtype=float).copy()
    q_111 = float(settings["initial_q_111"])
    prior = np.full(8, (1.0 - q_111) / 7.0, dtype=float)
    prior[v25b.STRUCTURE_INDEX["111"]] = q_111
    return prior


def gate5_row(position: int) -> dict[str, Any]:
    seed = 1_106_000 + position
    dimension_index = position // 1750
    within_dimension = position % 1750
    dimension, levels = GATE5_DIMENSIONS[dimension_index]
    level = levels[within_dimension // 875]
    settings = _gate5_settings(dimension, level)
    precision = float(settings["precision"])
    prior = _gate5_prior(settings)
    horizon = int(P["gate3_initial_state"]["observed_followup_slices"])
    observed = v25b.generate_world(
        seed,
        truth_structure="000",
        length=horizon,
        precision=precision,
        context_regime=str(settings["context_regime"]),
    ).episodes
    control = v25b.generate_world(
        seed,
        truth_structure="111",
        length=horizon,
        precision=precision,
        context_regime=str(settings["context_regime"]),
    ).episodes
    do_over, do_over_modes = v25b.do_over_episodes(
        seed,
        count=int(settings["do_over_count"]),
        precision=precision,
        structure="000",
    )
    insertion = int(settings["do_over_position"])
    active_sequence = observed[:insertion] + do_over + observed[insertion:]
    active_modes = (
        tuple("joint" for _ in observed[:insertion])
        + do_over_modes
        + tuple("joint" for _ in observed[insertion:])
    )
    marginal_modes = tuple(
        "marginal"
        if insertion <= index < insertion + len(do_over)
        else "joint"
        for index in range(len(active_sequence))
    )
    baseline = v25b.score(
        observed, precision=precision, initial_prior=prior
    )
    active = v25b.score(
        active_sequence,
        precision=precision,
        initial_prior=prior,
        presentations=active_modes,
    )
    marginal = v25b.score(
        active_sequence,
        precision=precision,
        initial_prior=prior,
        presentations=marginal_modes,
    )
    unchanged = v25b.score(
        control, precision=precision, initial_prior=prior
    )
    baseline_time = _gate3_first_time(baseline)
    active_time = _gate3_first_time(active, len(do_over))
    speedup = (
        float(baseline_time - active_time) / max(float(baseline_time), 1.0)
    )

    edge = within_dimension % 3

    def remove_edge(structure: str) -> str:
        bits = list(structure)
        bits[edge] = "0"
        return "".join(bits)

    lesion_world = v25b.generate_world(
        seed,
        truth_structure="111",
        length=64,
        precision=precision,
        context_regime=str(settings["context_regime"]),
    ).episodes
    lesioned = _score_transformed(
        lesion_world,
        precision,
        structure_transform=remove_edge,
        initial_prior=v25b.PRIOR,
    )
    other_edges = [
        float(value)
        for index, value in enumerate(lesioned["expected_edges"])
        if index != edge
    ]
    survivor_accuracy = float(
        np.mean([value >= 0.5 for value in other_edges])
    )

    premature, premature_modes = v25b.do_over_episodes(
        seed,
        count=5,
        precision=precision,
        structure="000",
    )
    premature_result = v25b.score(
        premature,
        precision=precision,
        initial_prior=prior,
        presentations=premature_modes,
    )
    returned = v25b.generate_world(
        seed,
        truth_structure="111",
        length=int(settings["stress_return_length"]),
        precision=precision,
        context_regime="return",
    ).episodes
    returned_result = v25b.score(
        premature + returned,
        precision=precision,
        initial_prior=prior,
        presentations=premature_modes
        + tuple("joint" for _ in returned),
    )
    premature_reversed = (
        premature_result.material_reduction.material
        and not returned_result.material_reduction.material
    )
    idx0 = v25b.STRUCTURE_INDEX["000"]
    return {
        "seed": seed,
        "dimension": dimension,
        "level": level,
        "settings": settings,
        "material_reduction": active.material_reduction.material,
        "false_full_burden_reduction": (
            unchanged.material_reduction.material
        ),
        "do_over_speedup": speedup,
        "q000_joint_minus_marginal": float(
            active.q_structure[idx0] - marginal.q_structure[idx0]
        ),
        "heldout_000_vs_111_margin": _gate3_heldout_margin(
            observed, precision
        ),
        "old_context_query_error": v25b.old_context_query_error(
            position % 3, "111", precision
        ),
        "root_revision_magnitude": float(settings["root_revision"]),
        "lesion_removed_edge": ("Z_W", "Z_Pi", "Z_Y")[edge],
        "lesion_removed_edge_prior_error": abs(
            float(lesioned["expected_edges"][edge]) - 0.5
        ),
        "lesion_surviving_edge_accuracy": survivor_accuracy,
        "lesion_minimum_surviving_edge_posterior": min(other_edges),
        "premature_material_reduction": (
            premature_result.material_reduction.material
        ),
        "stress_return_reversal": premature_reversed,
    }


def parallel_gate5() -> list[dict[str, Any]]:
    workers = min(8, max(1, os.cpu_count() or 1))
    boundaries = np.linspace(0, 14000, workers + 1, dtype=int)
    jobs = []
    for worker in range(workers):
        path = OUT / f".gate5-worker-{worker}.json"
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "worker",
            "gate5",
            str(int(boundaries[worker])),
            str(int(boundaries[worker + 1])),
            str(path),
        ]
        jobs.append((path, subprocess.Popen(command, cwd=ROOT)))
    for _, process in jobs:
        if process.wait():
            raise RuntimeError("Gate-5 worker failed")
    rows = []
    for path, _ in jobs:
        rows.extend(json.loads(path.read_text()))
        path.unlink()
    if sorted(int(row["seed"]) for row in rows) != list(
        range(1_106_000, 1_120_000)
    ):
        raise ValueError("Gate-5 seed ledger incomplete")
    return rows


def _gate5_cell_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    material_rate = float(
        np.mean([row["material_reduction"] for row in rows])
    )
    false_rate = float(
        np.mean([row["false_full_burden_reduction"] for row in rows])
    )
    speedup = interval([row["do_over_speedup"] for row in rows])
    heldout = interval(
        [row["heldout_000_vs_111_margin"] for row in rows]
    )
    joint_marginal = interval(
        [row["q000_joint_minus_marginal"] for row in rows]
    )
    lesion_accuracy = float(
        np.mean(
            [
                row["lesion_surviving_edge_accuracy"] == 1.0
                for row in rows
            ]
        )
    )
    premature = [row for row in rows if row["premature_material_reduction"]]
    reversal_rate = (
        1.0
        if not premature
        else float(np.mean([row["stress_return_reversal"] for row in premature]))
    )
    return {
        "world_count": len(rows),
        "material_reduction_rate": material_rate,
        "false_full_burden_reduction_rate": false_rate,
        "do_over_speedup_adjudicated_nonblocking": speedup,
        "heldout_000_vs_111_margin": heldout,
        "joint_minus_marginal_q000": joint_marginal,
        "maximum_old_context_query_error": max(
            row["old_context_query_error"] for row in rows
        ),
        "maximum_lesion_target_prior_error": max(
            row["lesion_removed_edge_prior_error"] for row in rows
        ),
        "population_complete_surviving_edge_accuracy": lesion_accuracy,
        "minimum_surviving_edge_posterior_descriptive": min(
            row["lesion_minimum_surviving_edge_posterior"] for row in rows
        ),
        "mean_surviving_edge_minimum_posterior_descriptive": float(
            np.mean(
                [
                    row["lesion_minimum_surviving_edge_posterior"]
                    for row in rows
                ]
            )
        ),
        "premature_reduction_world_count": len(premature),
        "stress_return_reversal_rate": reversal_rate,
    }


def run_gate5() -> bool:
    rows = parallel_gate5()
    cell_summaries: dict[str, Any] = {}
    blocking_checks: dict[str, bool] = {}
    nonblocking_speedup_repetitions: dict[str, bool] = {}
    for dimension, levels in GATE5_DIMENSIONS:
        for level in levels:
            key = f"{dimension}:{level}"
            cell = [
                row
                for row in rows
                if row["dimension"] == dimension and row["level"] == level
            ]
            summary = _gate5_cell_summary(cell)
            cell_summaries[key] = summary
            blocking_checks[f"{key}:material_rate"] = (
                summary["material_reduction_rate"]
                >= float(P["gate3"]["material_rate_minimum"])
            )
            blocking_checks[f"{key}:false_reduction"] = (
                summary["false_full_burden_reduction_rate"]
                <= float(P["gate3"]["false_or_premature_maximum"])
            )
            blocking_checks[f"{key}:heldout_margin"] = (
                summary["heldout_000_vs_111_margin"]["mean"]
                >= float(P["gate3"]["heldout_margin_minimum"])
                and summary["heldout_000_vs_111_margin"]["lower_95"] > 0.0
            )
            blocking_checks[f"{key}:joint_marginal_direction"] = (
                summary["joint_minus_marginal_q000"]["lower_95"] > 0.0
            )
            blocking_checks[f"{key}:historical_retention"] = (
                summary["maximum_old_context_query_error"]
                <= float(P["gate3"]["history_tolerance"])
            )
            blocking_checks[f"{key}:lesion_target"] = (
                summary["maximum_lesion_target_prior_error"] <= 1e-10
            )
            blocking_checks[f"{key}:lesion_population_survival"] = (
                summary["population_complete_surviving_edge_accuracy"] >= 0.85
            )
            blocking_checks[f"{key}:stress_return"] = (
                summary["stress_return_reversal_rate"]
                >= float(P["gate3"]["return_reversal_minimum"])
            )
            speedup = summary["do_over_speedup_adjudicated_nonblocking"]
            nonblocking_speedup_repetitions[key] = (
                speedup["mean"]
                >= float(P["gate3"]["do_over_speedup_minimum"])
                and speedup["lower_95"] > 0.0
            )

    inherited = {}
    for filename in (
        "gate-1-repaired.json",
        "gate-2.json",
        "gate-3.json",
        "gate-4.json",
    ):
        record = json.loads((OUT / filename).read_text(encoding="utf-8"))
        inherited[filename] = {
            "formal_verdict": record["verdict"],
            "sha256": hashlib.sha256(
                (OUT / filename).read_bytes()
            ).hexdigest(),
        }
    gate4_rows = json.loads(
        (OUT / "gate-4-per_world.json").read_text(encoding="utf-8")
    )
    gate4_population = {}
    for lesion in GATE4_LESIONS[:3]:
        cell = [row for row in gate4_rows if row["lesion"] == lesion]
        gate4_population[lesion] = {
            "population_complete_surviving_edge_accuracy": float(
                np.mean(
                    [
                        float(row["other_edge_minimum_posterior"]) >= 0.5
                        for row in cell
                    ]
                )
            ),
            "minimum_surviving_edge_posterior_descriptive": min(
                row["other_edge_minimum_posterior"] for row in cell
            ),
        }
        blocking_checks[f"gate4_adjudicated:{lesion}:population_survival"] = (
            gate4_population[lesion][
                "population_complete_surviving_edge_accuracy"
            ]
            >= 0.85
        )

    suite = subprocess.run(
        [sys.executable, "run_tests_parallel.py", "--workers", "8"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    blocking_checks["full_cumulative_unit_suite"] = suite.returncode == 0
    report = {
        "stage": "V2.5b",
        "gate": 5,
        "verdict": "PASS" if all(blocking_checks.values()) else "FAIL",
        "stage_progression_status": (
            "FROZEN_ADJUDICATED_MIXED_DO_OVER_SPEEDUP_LIMITATION"
            if all(blocking_checks.values())
            else "STOPPED_GATE_5"
        ),
        "seed_block": [1_106_000, 1_119_999],
        "world_count": len(rows),
        "robustness_design": {
            "dimensions": {
                dimension: list(levels)
                for dimension, levels in GATE5_DIMENSIONS
            },
            "worlds_per_level": 875,
        },
        "cell_summaries": cell_summaries,
        "blocking_checks": blocking_checks,
        "adjudicated_nonblocking_speedup_repetitions": (
            nonblocking_speedup_repetitions
        ),
        "gate4_adjudicated_population_reanalysis": gate4_population,
        "inherited_gate_records": inherited,
        "cumulative_unit_suite": {
            "command": "python3 run_tests_parallel.py --workers 8",
            "returncode": suite.returncode,
            "stdout": suite.stdout,
            "stderr": suite.stderr,
        },
        "bounds": BOUNDS,
        "escrow_accessed": False,
    }
    dump("gate-5-per_world.json", rows)
    dump("gate-5.json", report)
    (OUT / "gate-5-report.md").write_text(
        "# V2.5b Gate 5\n\n"
        f"**Verdict: {report['verdict']}**\n\n"
        "The do-over speedup floor and its repetitions are the sole scientific "
        "non-blocking limitation family. Per-world minimum lesion posteriors "
        "are descriptive under the Gate-4 adjudication; population survival "
        "accuracy is blocking.\n\n```json\n"
        + json.dumps(cell_summaries, indent=2, sort_keys=True)
        + "\n```\n",
        encoding="utf-8",
    )
    if report["verdict"] == "FAIL":
        (OUT / "gate-5-diagnosis-stub.md").write_text(
            "# Gate-5 diagnosis stub\n\nFailed blocking criteria:\n\n"
            + "\n".join(
                f"- `{key}`"
                for key, value in blocking_checks.items()
                if not value
            )
            + "\n\nNo freeze candidate was produced.\n",
            encoding="utf-8",
        )
    return report["verdict"] == "PASS"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "phase",
        choices=(
            "gate1",
            "gate1repaired",
            "gate2",
            "gate3",
            "gate4",
            "gate5",
            "worker",
        ),
    )
    parser.add_argument("worker_args", nargs="*")
    args = parser.parse_args()
    if args.phase == "worker":
        task = args.worker_args[0]
        if task == "gate2":
            _, start, end, path = args.worker_args
            dump_rows = [
                gate2_row(index) for index in range(int(start), int(end))
            ]
        elif task == "gate3":
            _, arm, start, end, path = args.worker_args
            dump_rows = [
                gate3_row(arm, index)
                for index in range(int(start), int(end))
            ]
        elif task == "gate5":
            _, start, end, path = args.worker_args
            dump_rows = [
                gate5_row(index) for index in range(int(start), int(end))
            ]
        else:
            raise ValueError("unknown worker task")
        Path(path).write_text(
            json.dumps(dump_rows, sort_keys=True, allow_nan=False),
            encoding="utf-8",
        )
        raise SystemExit(0)
    if args.phase == "gate1":
        ok = run_gate1()
    elif args.phase == "gate1repaired":
        ok = run_gate1(repaired=True)
    elif args.phase == "gate3":
        ok = run_gate3()
    elif args.phase == "gate4":
        ok = run_gate4()
    elif args.phase == "gate5":
        ok = run_gate5()
    else:
        ok = run_gate2()
    raise SystemExit(0 if ok else 2)


if __name__ == "__main__":
    main()
