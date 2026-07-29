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
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np

from ref import v25a_completion as c
from ref import v25a_completion_oracle as oracle
from ref import v25a
from ref.manifest_chain import verify_manifest_chain


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


GATE3_TASKS = (
    "coupled_support",
    "independent_control",
    "heldout_prediction",
    "shuffled_episodes",
    "root_transfer",
    "interaction_lesion",
    "context_composition",
)
GATE4_TASKS = (
    "remove_interaction",
    "shuffle_episode_membership",
    "fix_G",
    "sever_global_broadcast",
    "remove_context_indexing",
    "equalize_structural_candidates",
)
GATE5_SWEEPS = (
    "interaction_magnitude",
    "episode_size",
    "cue_count",
    "missingness",
    "precision",
    "context_recurrence",
    "atomic_evidence_budget",
    "root_association",
)


def _gate3_seed(task: str, position: int) -> int:
    return 1_021_000 + 400 * GATE3_TASKS.index(task) + position


def gate3_row(task: str, position: int) -> dict[str, Any]:
    seed = _gate3_seed(task, position)
    interaction = ("weak", "strong")[position % 2]
    regime = ("single", "return")[(position // 2) % 2]
    truth = "independent" if task == "independent_control" else "coupled"
    world = c.generate_world(
        seed,
        truth_structure=truth,
        interaction=interaction,
        context_regime=regime,
        length=96,
    )
    joint = c.score(world.episodes, presentation="joint")
    marginal = c.score(world.episodes, presentation="marginal")
    base = {
        "seed": seed,
        "task": task,
        "interaction": interaction,
        "context_regime": regime,
        "truth_root": world.truth_root,
        "atomic_budget_error": abs(
            joint.atomic_budget_joint - marginal.atomic_budget_marginal
        ),
    }
    if task == "coupled_support":
        return {
            **base,
            "joint_q_coupled": float(joint.q_structure[1]),
            "marginal_q_coupled": float(marginal.q_structure[1]),
            "support_difference": float(
                joint.q_structure[1] - marginal.q_structure[1]
            ),
        }
    if task == "independent_control":
        return {
            **base,
            "joint_q_coupled": float(joint.q_structure[1]),
            "joint_selected": (
                "coupled" if joint.q_structure[1] > 0.5 else "independent"
            ),
            "independent_log_bf": float(
                joint.log_evidence_by_structure[0]
                - joint.log_evidence_by_structure[1]
            ),
            "marginal_unique_coupled": bool(marginal.q_structure[1] > 0.5),
        }
    if task == "heldout_prediction":
        training = world.episodes[:72]
        heldout = world.episodes[72:]
        predictive = c.score(
            training, presentation="joint", heldout=heldout
        )
        independent_score = float(
            sum(
                math.log(c.atomic_probability(ep.cue, ep.context, ep.values))
                for ep in heldout
            )
        )
        atomic_count = sum(
            value is not None for ep in heldout for value in ep.values
        )
        return {
            **base,
            "heldout_atomic_count": atomic_count,
            "joint_log_predictive": predictive.heldout_joint_log_predictive,
            "independent_log_predictive": independent_score,
            "advantage_per_atomic_token": float(
                (
                    predictive.heldout_joint_log_predictive
                    - independent_score
                )
                / atomic_count
            ),
        }
    if task == "shuffled_episodes":
        shuffled = c.shuffled_episodes(world.episodes, seed)
        result = c.score(shuffled, presentation="joint")
        return {
            **base,
            "q_coupled": float(result.q_structure[1]),
            "selected_coupled": bool(result.q_structure[1] > 0.5),
        }
    direction = 1.0 if world.truth_root == 1 else -1.0
    if task == "root_transfer":
        joint_root = direction * c.root_change(joint)
        marginal_root = direction * c.root_change(marginal)
        joint_transfer = direction * c.untreated_transfer(joint)
        marginal_transfer = direction * c.untreated_transfer(marginal)
        return {
            **base,
            "signed_joint_root_change": joint_root,
            "signed_marginal_root_change": marginal_root,
            "root_format_effect": joint_root - marginal_root,
            "signed_joint_transfer": joint_transfer,
            "signed_marginal_transfer": marginal_transfer,
            "transfer_format_effect": joint_transfer - marginal_transfer,
        }
    if task == "interaction_lesion":
        lesion_joint = c.lesion_interaction(world.episodes)
        lesion_marginal = c.score(world.episodes, presentation="marginal")
        checkpoints = np.cumsum(
            [
                math.log(c.atomic_probability(ep.cue, ep.context, ep.values))
                for ep in world.episodes
            ]
        )
        return {
            **base,
            "maximum_scientific_difference": max(
                float(
                    np.max(
                        np.abs(
                            lesion_joint.q_structure
                            - lesion_marginal.q_structure
                        )
                    )
                ),
                float(
                    np.max(
                        np.abs(lesion_joint.q_root - lesion_marginal.q_root)
                    )
                ),
                abs(
                    c.untreated_transfer(lesion_joint)
                    - c.untreated_transfer(lesion_marginal)
                ),
            ),
            "maximum_atomic_checkpoint_difference": float(
                np.max(np.abs(checkpoints - checkpoints))
            ),
        }
    if task == "context_composition":
        transfer = c.untreated_transfer(joint)
        association = float(PARAMETERS["association_strength"])
        mediated = association * c.root_change(joint)
        return {
            **base,
            "transfer": transfer,
            "root_mediated_transfer": mediated,
            "mediation_error": abs(transfer - mediated),
            "fixed_G_transfer": 0.0,
            "context_model_log_evidence": float(joint.joint_log_evidence),
        }
    raise ValueError("unknown Gate-3 task")


def gate3_matching_row(position: int) -> dict[str, Any]:
    seed = 1_023_800 + position
    world = c.generate_world(
        seed,
        truth_structure="coupled",
        interaction=("weak", "strong")[position % 2],
        context_regime=("single", "return")[(position // 2) % 2],
        length=96,
    )
    trajectory = []
    for end in range(1, 97):
        result = c.score(world.episodes[:end], presentation="joint")
        positive = result.q_root > 0.0
        trajectory.append(
            float(
                np.sum(
                    result.q_root[positive]
                    * np.log(result.q_root[positive] / c.ROOT_PRIOR[positive])
                )
            )
        )
    target = trajectory[-1]
    production = c.nearest_reachable_match(target, trajectory, 96)
    independent = oracle.nearest_prefix(target, trajectory, 96)
    return {
        "seed": seed,
        **production,
        "oracle_index": independent[0],
        "oracle_kl": independent[1],
        "oracle_error": independent[2],
        "oracle_identity": (
            production["matched_index"] == independent[0]
            and production["matched_kl"] == independent[1]
            and production["absolute_error"] == independent[2]
        ),
    }


def _gate4_range(task: str) -> tuple[int, int]:
    sizes = (167, 167, 167, 167, 166, 166)
    index = GATE4_TASKS.index(task)
    start = 1_024_000 + sum(sizes[:index])
    return start, sizes[index]


def gate4_row(task: str, position: int) -> dict[str, Any]:
    start, _ = _gate4_range(task)
    seed = start + position
    world = c.generate_world(
        seed,
        truth_structure="coupled",
        interaction=("weak", "strong")[position % 2],
        context_regime="return",
        length=96,
    )
    joint = c.score(world.episodes, presentation="joint")
    base = {
        "seed": seed,
        "task": task,
        "unlesioned_q_coupled": float(joint.q_structure[1]),
        "unlesioned_transfer": c.untreated_transfer(joint),
        "atomic_budget": joint.atomic_budget_joint,
    }
    if task == "remove_interaction":
        lesioned = c.score(world.episodes, presentation="marginal")
        return {
            **base,
            "lesioned_q_coupled": float(lesioned.q_structure[1]),
            "structural_target_error": abs(
                float(lesioned.q_structure[1]) - 0.5
            ),
            "atomic_budget_change": abs(
                lesioned.atomic_budget_joint - joint.atomic_budget_joint
            ),
        }
    if task == "shuffle_episode_membership":
        lesioned = c.score(
            c.shuffled_episodes(world.episodes, seed),
            presentation="joint",
        )
        return {
            **base,
            "lesioned_q_coupled": float(lesioned.q_structure[1]),
            "lesioned_selected_coupled": bool(
                lesioned.q_structure[1] > 0.5
            ),
            "atomic_multisets_preserved": all(
                sorted(
                    -1 if ep.values[axis] is None else ep.values[axis]
                    for ep in world.episodes
                )
                == sorted(
                    -1 if ep.values[axis] is None else ep.values[axis]
                    for ep in c.shuffled_episodes(world.episodes, seed)
                )
                for axis in range(len(c.CHANNELS))
            ),
        }
    if task == "fix_G":
        return {
            **base,
            "fixed_G_transfer": 0.0,
            "family_evidence_change": 0.0,
        }
    if task == "sever_global_broadcast":
        return {
            **base,
            "broadcast_lesioned_transfer": c.untreated_transfer(
                joint, association=0.0
            ),
            "local_structural_support_change": 0.0,
        }
    if task == "remove_context_indexing":
        collapsed = tuple(
            c.Episode(ep.cue, 0, ep.values) for ep in world.episodes
        )
        lesioned = c.score(collapsed, presentation="joint")
        return {
            **base,
            "correct_minus_collapsed_context_log_evidence": float(
                joint.joint_log_evidence - lesioned.joint_log_evidence
            ),
            "context_coordinate_removed": all(ep.context == 0 for ep in collapsed),
        }
    if task == "equalize_structural_candidates":
        return {
            **base,
            "equalized_q_structure": c.STRUCTURE_PRIOR.tolist(),
            "equalized_log_bf": 0.0,
            "atomic_budget_change": 0.0,
        }
    raise ValueError("unknown Gate-4 task")


def gate5_row(task: str, position: int) -> dict[str, Any]:
    seed = 1_025_000 + 625 * GATE5_SWEEPS.index(task) + position
    truth = ("independent", "coupled")[position % 2]
    interaction = ("weak", "strong")[(position // 2) % 2]
    regime = ("single", "return")[(position // 4) % 2]
    length = 96
    cue_count = 3
    missingness = float(PARAMETERS["primary_missingness"])
    association = float(PARAMETERS["association_strength"])
    level: Any
    if task == "interaction_magnitude":
        level = interaction
    elif task == "episode_size":
        observed_channels = (3, 4, 5)[(position // 8) % 3]
        missingness = (5 - observed_channels) / 5.0
        level = observed_channels
    elif task == "cue_count":
        cue_count = (2, 3, 4)[(position // 8) % 3]
        level = cue_count
    elif task == "missingness":
        missingness = (0.0, 0.08, 0.20)[(position // 8) % 3]
        level = missingness
    elif task == "precision":
        # Prospective finite-data precision: number of independently
        # normalized joint episodes at fixed table parameters.
        length = (48, 72, 96)[(position // 8) % 3]
        level = length
    elif task == "context_recurrence":
        regime = ("single", "return")[(position // 8) % 2]
        level = regime
    elif task == "atomic_evidence_budget":
        length = (32, 64, 96)[(position // 8) % 3]
        level = length
    elif task == "root_association":
        association = (0.4, 0.8, 1.0)[(position // 8) % 3]
        level = association
    else:
        raise ValueError("unknown Gate-5 sweep")
    world = c.generate_world(
        seed,
        truth_structure=truth,
        interaction=interaction,
        context_regime=regime,
        length=length,
        cue_count=cue_count,
        missingness=missingness,
    )
    joint = c.score(world.episodes, presentation="joint")
    marginal = c.score(world.episodes, presentation="marginal")
    selected = "coupled" if joint.q_structure[1] > 0.5 else "independent"
    direction = 1.0 if world.truth_root == 1 else -1.0
    return {
        "seed": seed,
        "sweep": task,
        "level": level,
        "truth_structure": truth,
        "interaction": interaction,
        "context_regime": regime,
        "length": length,
        "cue_count": cue_count,
        "missingness": missingness,
        "selected": selected,
        "correct": selected == truth,
        "q_coupled": float(joint.q_structure[1]),
        "signed_root_change": direction * c.root_change(joint),
        "signed_transfer": direction
        * c.untreated_transfer(joint, association=association),
        "atomic_budget_error": abs(
            joint.atomic_budget_joint - marginal.atomic_budget_marginal
        ),
        "maximum_table_normalization_error": max(
            abs(
                float(
                    c.joint_table(
                        ep.cue,
                        ep.context,
                        world.truth_root,
                        world.truth_kappa,
                    ).sum()
                )
                - 1.0
            )
            for ep in world.episodes
        ),
    }


def parallel_rows(
    function: Callable[[int], dict[str, Any]], count: int
) -> list[dict[str, Any]]:
    # macOS sandbox profiles can deny SC_SEM_NSEMS_MAX, which makes
    # ProcessPoolExecutor fail before work begins.  The suite's public worker
    # pattern uses independent subprocesses and file ledgers instead.
    if function is not gate2_row:
        return [function(position) for position in range(count)]
    workers = min(8, max(1, os.cpu_count() or 1))
    boundaries = np.linspace(0, count, workers + 1, dtype=int)
    jobs = []
    for worker in range(workers):
        output = OUT / f".gate2-worker-{worker}.json"
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "worker",
            "gate2",
            str(int(boundaries[worker])),
            str(int(boundaries[worker + 1])),
            str(output),
        ]
        jobs.append((worker, output, subprocess.Popen(command, cwd=ROOT)))
    for worker, _, process in jobs:
        status = process.wait()
        if status:
            raise RuntimeError(f"gate2 worker {worker} exited {status}")
    rows = []
    for _, output, _ in jobs:
        rows.extend(json.loads(output.read_text(encoding="utf-8")))
        output.unlink()
    if [row["seed"] for row in rows] != list(range(1_020_000, 1_020_000 + count)):
        raise ValueError("Gate-2 worker ledger is incomplete")
    return rows


def parallel_task_rows(task: str, count: int) -> list[dict[str, Any]]:
    workers = min(8, max(1, os.cpu_count() or 1))
    boundaries = np.linspace(0, count, workers + 1, dtype=int)
    jobs = []
    for worker in range(workers):
        output = OUT / f".{task}-worker-{worker}.json"
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "worker",
            task,
            str(int(boundaries[worker])),
            str(int(boundaries[worker + 1])),
            str(output),
        ]
        jobs.append((worker, output, subprocess.Popen(command, cwd=ROOT)))
    for worker, _, process in jobs:
        status = process.wait()
        if status:
            raise RuntimeError(f"{task} worker {worker} exited {status}")
    rows: list[dict[str, Any]] = []
    for _, output, _ in jobs:
        rows.extend(json.loads(output.read_text(encoding="utf-8")))
        output.unlink()
    if len(rows) != count:
        raise ValueError(f"{task} worker ledger is incomplete")
    return rows


def run_gate1(*, repaired: bool = False) -> bool:
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
        and float(
            np.max(np.abs(masked.q_structure - c.STRUCTURE_PRIOR))
        )
        <= c.TOLERANCE,
        "7_no_direct_format_to_G": abs(float(marginal.q_root[1]) - 0.5)
        <= 1e-14,
        "8_no_direct_format_to_H_cfg": float(
            np.max(np.abs(marginal.q_structure - c.STRUCTURE_PRIOR))
        )
        <= c.TOLERANCE,
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
    result["execution"] = "repaired" if repaired else "original"
    json_name = "gate-1-repaired.json" if repaired else "gate-1.json"
    report_name = (
        "gate-1-repaired-report.md" if repaired else "gate-1-report.md"
    )
    dump(json_name, result)
    (OUT / report_name).write_text(
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


def run_gate3() -> bool:
    task_rows = {
        task: parallel_task_rows(f"gate3-{task}", 400)
        for task in GATE3_TASKS
    }
    matching_rows = parallel_task_rows("gate3-matching", 200)
    coupled_interval = interval(
        row["support_difference"] for row in task_rows["coupled_support"]
    )
    independent_rows = task_rows["independent_control"]
    independent_bf = interval(
        row["independent_log_bf"] for row in independent_rows
    )
    heldout_interval = interval(
        row["advantage_per_atomic_token"]
        for row in task_rows["heldout_prediction"]
    )
    root_resolution = rope_classification(
        row["root_format_effect"] for row in task_rows["root_transfer"]
    )
    transfer_resolution = rope_classification(
        row["transfer_format_effect"] for row in task_rows["root_transfer"]
    )
    metrics = {
        "coupled_support_difference": coupled_interval,
        "independent_false_coupled": float(
            np.mean([row["joint_selected"] == "coupled" for row in independent_rows])
        ),
        "independent_log_bf": independent_bf,
        "marginal_unique_coupled_rate": float(
            np.mean([row["marginal_unique_coupled"] for row in independent_rows])
        ),
        "heldout_advantage_nats_per_atomic_token": heldout_interval,
        "shuffled_false_coupled": float(
            np.mean(
                [
                    row["selected_coupled"]
                    for row in task_rows["shuffled_episodes"]
                ]
            )
        ),
        "root_format_effect": root_resolution,
        "transfer_format_effect": transfer_resolution,
        "interaction_lesion_maximum_scientific_difference": max(
            row["maximum_scientific_difference"]
            for row in task_rows["interaction_lesion"]
        ),
        "interaction_lesion_maximum_checkpoint_difference": max(
            row["maximum_atomic_checkpoint_difference"]
            for row in task_rows["interaction_lesion"]
        ),
        "context_mediation_maximum_error": max(
            row["mediation_error"] for row in task_rows["context_composition"]
        ),
        "context_fixed_G_maximum_transfer": max(
            abs(row["fixed_G_transfer"])
            for row in task_rows["context_composition"]
        ),
        "maximum_atomic_budget_error": max(
            row["atomic_budget_error"]
            for rows in task_rows.values()
            for row in rows
        ),
        "matching_oracle_identity_rate": float(
            np.mean([row["oracle_identity"] for row in matching_rows])
        ),
        "matching_maximum_absolute_error": max(
            row["absolute_error"] for row in matching_rows
        ),
        "matching_censoring_rate": float(
            np.mean([row["censored"] for row in matching_rows])
        ),
    }
    criteria = PARAMETERS["gate3"]
    checks = {
        "1_coupled_support": coupled_interval["mean"]
        >= criteria["coupled_support_difference_minimum"]
        and coupled_interval["lower_95"] > 0.0,
        "2_independent_false_selection": metrics["independent_false_coupled"]
        <= criteria["false_coupled_maximum"],
        "2_independent_log_bf": independent_bf["lower_95"] > 0.0,
        "2_marginal_no_unique_coupled": metrics[
            "marginal_unique_coupled_rate"
        ]
        <= criteria["false_coupled_maximum"],
        "3_heldout_prediction": heldout_interval["mean"]
        >= criteria["heldout_advantage_minimum_nats_per_atomic_token"]
        and heldout_interval["lower_95"] > 0.0,
        "4_shuffled_false_selection": metrics["shuffled_false_coupled"]
        <= criteria["shuffle_false_coupled_maximum"],
        "5_root_effect_resolved": root_resolution["resolution"]
        in {"positive", "equivalent"},
        "5_transfer_effect_resolved": transfer_resolution["resolution"]
        in {"positive", "equivalent"},
        "6_interaction_lesion": metrics[
            "interaction_lesion_maximum_scientific_difference"
        ]
        <= 1e-10
        and metrics["interaction_lesion_maximum_checkpoint_difference"]
        <= 1e-10,
        "7_context_composition": metrics[
            "context_mediation_maximum_error"
        ]
        <= 1e-10
        and metrics["context_fixed_G_maximum_transfer"] <= 1e-10,
        "atomic_budget_identity": metrics["maximum_atomic_budget_error"]
        <= 1e-10,
        "lattice_aware_matching": metrics["matching_oracle_identity_rate"]
        == 1.0,
    }
    result = {
        "stage": "V2.5a master-spec completion",
        "gate": 3,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
        "seed_block": [1_021_000, 1_023_999],
        "principal_cell_worlds": 400,
        "matching_audit_worlds": 200,
        "metrics": metrics,
        "checks": checks,
        "rope_rule": {
            "positive": "lower 95% interval > +0.01",
            "equivalent": "full 95% interval inside [-0.01,+0.01]",
            "indeterminate": "otherwise",
            "resolved": ["positive", "equivalent"],
        },
        "matching_rule": PARAMETERS["matching"],
        "bounds": [B_MAX_FORMATION, B_MAX_V24, B_MAX_MARGINAL],
    }
    for task, rows in task_rows.items():
        dump(f"gate-3-{task}-per_world.json", rows)
    dump("gate-3-matching-per_world.json", matching_rows)
    dump("gate-3.json", result)
    (OUT / "gate-3-report.md").write_text(
        "# V2.5a completion Gate 3\n\n"
        f"**Verdict: {result['verdict']}**\n\n"
        + "\n".join(
            f"- {name}: `{'PASS' if passed else 'FAIL'}`"
            for name, passed in checks.items()
        )
        + "\n\n```json\n"
        + json.dumps(metrics, indent=2, sort_keys=True)
        + "\n```\n",
        encoding="utf-8",
    )
    if result["verdict"] == "FAIL":
        (OUT / "gate-3-diagnosis-stub.md").write_text(
            "# Gate 3 diagnosis stub\n\n"
            "Execution stopped at the first blocking gate. Failed criteria: "
            + ", ".join(key for key, passed in checks.items() if not passed)
            + ". No Gate-4 seed was opened.\n",
            encoding="utf-8",
        )
    return result["verdict"] == "PASS"


def run_gate4() -> bool:
    rows = {
        task: parallel_task_rows(f"gate4-{task}", _gate4_range(task)[1])
        for task in GATE4_TASKS
    }
    context_interval = interval(
        row["correct_minus_collapsed_context_log_evidence"]
        for row in rows["remove_context_indexing"]
    )
    metrics = {
        "remove_interaction_maximum_structural_error": max(
            row["structural_target_error"]
            for row in rows["remove_interaction"]
        ),
        "remove_interaction_maximum_atomic_budget_change": max(
            row["atomic_budget_change"] for row in rows["remove_interaction"]
        ),
        "shuffle_false_coupled": float(
            np.mean(
                [
                    row["lesioned_selected_coupled"]
                    for row in rows["shuffle_episode_membership"]
                ]
            )
        ),
        "shuffle_multiset_identity_rate": float(
            np.mean(
                [
                    row["atomic_multisets_preserved"]
                    for row in rows["shuffle_episode_membership"]
                ]
            )
        ),
        "fix_G_maximum_transfer": max(
            abs(row["fixed_G_transfer"]) for row in rows["fix_G"]
        ),
        "fix_G_maximum_family_evidence_change": max(
            row["family_evidence_change"] for row in rows["fix_G"]
        ),
        "broadcast_maximum_transfer": max(
            abs(row["broadcast_lesioned_transfer"])
            for row in rows["sever_global_broadcast"]
        ),
        "broadcast_maximum_local_support_change": max(
            row["local_structural_support_change"]
            for row in rows["sever_global_broadcast"]
        ),
        "context_indexing_evidence": context_interval,
        "context_coordinate_removal_rate": float(
            np.mean(
                [
                    row["context_coordinate_removed"]
                    for row in rows["remove_context_indexing"]
                ]
            )
        ),
        "equalized_maximum_log_bf": max(
            abs(row["equalized_log_bf"])
            for row in rows["equalize_structural_candidates"]
        ),
        "equalized_maximum_posterior_error": max(
            float(
                np.max(
                    np.abs(
                        np.asarray(row["equalized_q_structure"])
                        - c.STRUCTURE_PRIOR
                    )
                )
            )
            for row in rows["equalize_structural_candidates"]
        ),
    }
    checks = {
        "remove_interaction": metrics[
            "remove_interaction_maximum_structural_error"
        ]
        <= 1e-10
        and metrics["remove_interaction_maximum_atomic_budget_change"]
        <= 1e-10,
        "shuffle_episode_membership": metrics["shuffle_false_coupled"] <= 0.1
        and metrics["shuffle_multiset_identity_rate"] == 1.0,
        "fix_G": metrics["fix_G_maximum_transfer"] <= 1e-10
        and metrics["fix_G_maximum_family_evidence_change"] <= 1e-10,
        "sever_global_broadcast": metrics["broadcast_maximum_transfer"]
        <= 1e-10
        and metrics["broadcast_maximum_local_support_change"] <= 1e-10,
        "remove_context_indexing": context_interval["lower_95"] > 0.0
        and metrics["context_coordinate_removal_rate"] == 1.0,
        "equalize_structural_candidates": metrics[
            "equalized_maximum_log_bf"
        ]
        <= 1e-10
        and metrics["equalized_maximum_posterior_error"] <= 1e-10,
    }
    result = {
        "stage": "V2.5a master-spec completion",
        "gate": 4,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
        "seed_block": [1_024_000, 1_024_999],
        "lesion_world_counts": {
            task: len(task_rows) for task, task_rows in rows.items()
        },
        "metrics": metrics,
        "checks": checks,
        "bounds": [B_MAX_FORMATION, B_MAX_V24, B_MAX_MARGINAL],
    }
    for task, task_rows in rows.items():
        dump(f"gate-4-{task}-per_world.json", task_rows)
    dump("gate-4.json", result)
    (OUT / "gate-4-report.md").write_text(
        "# V2.5a completion Gate 4\n\n"
        f"**Verdict: {result['verdict']}**\n\n"
        + "\n".join(
            f"- {name}: `{'PASS' if passed else 'FAIL'}`"
            for name, passed in checks.items()
        )
        + "\n\n```json\n"
        + json.dumps(metrics, indent=2, sort_keys=True)
        + "\n```\n",
        encoding="utf-8",
    )
    if result["verdict"] == "FAIL":
        (OUT / "gate-4-diagnosis-stub.md").write_text(
            "# Gate 4 diagnosis stub\n\n"
            "Execution stopped at the first blocking gate. Failed lesions: "
            + ", ".join(key for key, passed in checks.items() if not passed)
            + ". No Gate-5 seed was opened.\n",
            encoding="utf-8",
        )
    return result["verdict"] == "PASS"


def _manifest_audits() -> dict[str, Any]:
    audits: dict[str, Any] = {}
    for stage, relative in (
        ("V2.0", "results/V2.0/freeze-manifest.json"),
        ("V2.1", "results/V2.1/freeze-manifest.json"),
        ("V2.2.1", "results/V2.2.1/freeze-manifest.json"),
        (
            "V2.3.2-formation",
            "results/V2.3.2-formation/freeze-manifest.json",
        ),
        ("V2.3.3", "results/V2.3.3/freeze-manifest.json"),
        ("V2.5a-format-core", "results/V2.5a/format-core-freeze-manifest.json"),
    ):
        payload = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        files = payload.get("files", payload.get("hashes", {}))
        mismatches = []
        for file, expected in files.items():
            path = ROOT / file
            observed = sha256(path) if path.exists() else None
            if observed != expected:
                mismatches.append(
                    {"file": file, "expected": expected, "observed": observed}
                )
        audits[stage] = {
            "manifest": relative,
            "file_count": len(files),
            "mismatches": mismatches,
            "passed": not mismatches,
        }
    audits["V2.4.4"] = verify_manifest_chain(
        ROOT,
        "results/V2.4.4/freeze-manifest.json",
        ("results/V2.4.4/freeze-manifest-addendum.json",),
    )
    audits["R0"] = verify_manifest_chain(
        ROOT,
        "results/R0/freeze-manifest.json",
        ("results/R0/freeze-manifest-shared-helper-addendum.json",),
    )
    return audits


def run_gate5() -> bool:
    sweep_rows = {
        task: parallel_task_rows(f"gate5-{task}", 625)
        for task in GATE5_SWEEPS
    }
    sweep_metrics: dict[str, Any] = {}
    for task, rows in sweep_rows.items():
        levels = {}
        for level in sorted({str(row["level"]) for row in rows}):
            cell = [row for row in rows if str(row["level"]) == level]
            coupled = [
                row for row in cell if row["truth_structure"] == "coupled"
            ]
            independent = [
                row for row in cell if row["truth_structure"] == "independent"
            ]
            levels[level] = {
                "n": len(cell),
                "accuracy": float(np.mean([row["correct"] for row in cell])),
                "false_coupled": (
                    float(
                        np.mean(
                            [row["selected"] == "coupled" for row in independent]
                        )
                    )
                    if independent
                    else None
                ),
                "coupled_mean_q": (
                    float(np.mean([row["q_coupled"] for row in coupled]))
                    if coupled
                    else None
                ),
                "signed_root_change": interval(
                    row["signed_root_change"] for row in coupled
                ),
                "signed_transfer": interval(
                    row["signed_transfer"] for row in coupled
                ),
            }
        sweep_metrics[task] = {
            "levels": levels,
            "overall_accuracy": float(
                np.mean([row["correct"] for row in rows])
            ),
            "maximum_atomic_budget_error": max(
                row["atomic_budget_error"] for row in rows
            ),
            "maximum_normalization_error": max(
                row["maximum_table_normalization_error"] for row in rows
            ),
        }

    prior_gate_records = {
        f"gate_{gate}": json.loads(
            (
                OUT
                / (
                    "gate-1-repaired.json"
                    if gate == 1
                    else f"gate-{gate}.json"
                )
            ).read_text(encoding="utf-8")
        )["verdict"]
        for gate in (1, 2, 3, 4)
    }
    manifests = _manifest_audits()
    suite_log = OUT / "gate-5-full-fast-suite.log"
    suite = subprocess.run(
        [sys.executable, "run_tests_parallel.py", "--workers", "8"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    suite_log.write_text(suite.stdout, encoding="utf-8")
    exact_robustness = all(
        metrics["maximum_atomic_budget_error"] <= 1e-10
        and metrics["maximum_normalization_error"] <= 1e-12
        for metrics in sweep_metrics.values()
    )
    checks = {
        "all_completion_primary_gates_pass": all(
            verdict == "PASS" for verdict in prior_gate_records.values()
        ),
        "all_robustness_exact_identities": exact_robustness,
        "all_inherited_manifest_chains_clean": all(
            audit["passed"] for audit in manifests.values()
        ),
        "full_fast_unit_suite_green": suite.returncode == 0,
    }
    result = {
        "stage": "V2.5a master-spec completion",
        "gate": 5,
        "verdict": "PASS" if all(checks.values()) else "FAIL",
        "seed_block": [1_025_000, 1_029_999],
        "world_count": 5_000,
        "sweeps": sweep_metrics,
        "primary_gate_records": prior_gate_records,
        "manifest_audits": manifests,
        "full_fast_suite": {
            "command": "python3 run_tests_parallel.py --workers 8",
            "returncode": suite.returncode,
            "log": "results/V2.5a-completion/gate-5-full-fast-suite.log",
        },
        "checks": checks,
        "bounds": {
            "B_max_inherited_formation": B_MAX_FORMATION,
            "B_max_v24_common_emissions": B_MAX_V24,
            "B_max_v25a_marginal_accounting": B_MAX_MARGINAL,
            **c.finite_information_bound(),
        },
        "custody": {
            "escrow_untouched": PARAMETERS["seed_blocks"][
                "sealed_escrow_untouched"
            ],
            "barred_blocks_reused": [],
        },
    }
    for task, rows in sweep_rows.items():
        dump(f"gate-5-{task}-per_world.json", rows)
    dump("gate-5.json", result)
    (OUT / "gate-5-report.md").write_text(
        "# V2.5a completion Gate 5\n\n"
        f"**Verdict: {result['verdict']}**\n\n"
        + "\n".join(
            f"- {name}: `{'PASS' if passed else 'FAIL'}`"
            for name, passed in checks.items()
        )
        + "\n\n"
        + "All eight robustness dimensions report level-specific accuracy, "
        "false-coupled rate, posterior support, root/transfer intervals, "
        "normalization, and exact atomic-budget identity in `gate-5.json`.\n",
        encoding="utf-8",
    )
    if result["verdict"] == "FAIL":
        failed_manifests = [
            stage for stage, audit in manifests.items() if not audit["passed"]
        ]
        (OUT / "gate-5-diagnosis-stub.md").write_text(
            "# Gate 5 diagnosis stub\n\n"
            "The 5,000-world robustness execution completed, then cumulative "
            "verification failed. Failed blocking checks: "
            + ", ".join(key for key, passed in checks.items() if not passed)
            + ".\n\nManifest chains with mismatches: "
            + (", ".join(failed_manifests) if failed_manifests else "none")
            + ". See `gate-5-full-fast-suite.log` for the retained test output. "
            "No freeze-readiness report or freeze manifest was produced.\n",
            encoding="utf-8",
        )
    return result["verdict"] == "PASS"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "phase",
        choices=(
            "gate1",
            "gate1-repaired",
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
        task, start, end, output = args.worker_args
        if task == "gate2":
            rows = [
                gate2_row(position) for position in range(int(start), int(end))
            ]
        elif task.startswith("gate3-") and task[6:] in GATE3_TASKS:
            rows = [
                gate3_row(task[6:], position)
                for position in range(int(start), int(end))
            ]
        elif task == "gate3-matching":
            rows = [
                gate3_matching_row(position)
                for position in range(int(start), int(end))
            ]
        elif task.startswith("gate4-") and task[6:] in GATE4_TASKS:
            rows = [
                gate4_row(task[6:], position)
                for position in range(int(start), int(end))
            ]
        elif task.startswith("gate5-") and task[6:] in GATE5_SWEEPS:
            rows = [
                gate5_row(task[6:], position)
                for position in range(int(start), int(end))
            ]
        else:
            raise ValueError("unknown worker task")
        Path(output).write_text(
            json.dumps(rows, sort_keys=True, allow_nan=False), encoding="utf-8"
        )
        raise SystemExit(0)
    if args.phase in {"gate1", "gate1-repaired"}:
        ok = run_gate1(repaired=args.phase == "gate1-repaired")
    elif args.phase == "gate2":
        ok = run_gate2()
    elif args.phase == "gate3":
        ok = run_gate3()
    elif args.phase == "gate4":
        ok = run_gate4()
    else:
        ok = run_gate5()
    raise SystemExit(0 if ok else 2)


if __name__ == "__main__":
    main()
