"""Run revealed C-V233-M against the qualified bank2 states."""

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

from challenges.run_c_v233_m_bank2 import verify_identity  # noqa: E402
from ref.audit import audit_one_posterior  # noqa: E402
from ref.constitution import (  # noqa: E402
    cumulative_graded_update_audit,
    publish_stratified_update_distribution,
)
from ref.rng import component_rng  # noqa: E402
from ref.v232_formation import (  # noqa: E402
    LABELS,
    SUPPORT,
    slice_distribution,
)
from ref.v233 import (  # noqa: E402
    PARAMETERS,
    canonical_state_bytes,
    canonical_state_hash,
    forbidden_path_audit,
    policy_avoidance_probability,
    run_maintenance_trajectory,
    trajectory_readout,
)


CHALLENGE = "C-V233-M"
BANK_COMMIT = "2638fa9"
PUBLIC_PLAN_COMMIT = "39236e7"
FIRST_SEED = 816001
LAST_SEED = 816900
USED_WORLD_COUNT = 120
RELEASED_BLOCK = (FIRST_SEED, LAST_SEED)
STRATA = ("moderate", "strong", "very_strong")
DOSES = (0.0, 0.25, 0.35, 0.5, 0.65, 0.75, 1.0)
DURATION = int(PARAMETERS["maintenance"]["duration"])
B_MAX = float(PARAMETERS["inherited_formation"]["B_max"])
TOLERANCE = 1e-10
BOOTSTRAP_REPLICATES = 10_000
ISOTONIC_PERMUTATIONS = 10_000
RESULT_DIR = ROOT / "results" / "challenges" / CHALLENGE
BANK_PATH = (
    ROOT
    / "results"
    / "challenges"
    / "C-V233-M-bank2"
    / "retained_states.json"
)
BANK_ADDENDUM_PATH = (
    ROOT / "results" / "V2.3.3" / "gate6-bank2-addendum.json"
)
CHALLENGE_PATH = (
    ROOT / "sealed-revealed" / "C-V233-M-challenge.md"
)
ADDENDUM_PATH = (
    ROOT / "results" / "V2.3.3" / "gate6-maintenance-addendum.json"
)
MILESTONE_PATH = (
    ROOT / "results" / "milestone-4-v2.3.3-gate6-maintenance-update.md"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_rng(component: str) -> np.random.Generator:
    digest = hashlib.sha256(f"{CHALLENGE}:{component}".encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "big"))


def write_json(path: Path, value: Any) -> None:
    def native(item: Any) -> Any:
        if isinstance(item, np.generic):
            return item.item()
        if isinstance(item, np.ndarray):
            return item.tolist()
        raise TypeError(f"cannot serialize {type(item).__name__}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=native) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def wilson(successes: int, total: int) -> list[float]:
    probability = successes / total
    z = 1.96
    denominator = 1.0 + z * z / total
    center = (probability + z * z / (2.0 * total)) / denominator
    half = (
        z
        * math.sqrt(
            probability * (1.0 - probability) / total
            + z * z / (4.0 * total * total)
        )
        / denominator
    )
    return [probability, center - half, center + half]


def verify_bank_custody() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    identity = verify_identity()
    bank_bytes = subprocess.check_output(
        [
            "git",
            "show",
            (
                f"{BANK_COMMIT}:projects/emergence-suite/v2/"
                "results/challenges/C-V233-M-bank2/retained_states.json"
            ),
        ],
        cwd=REPO,
    )
    if BANK_PATH.read_bytes() != bank_bytes:
        raise RuntimeError("local qualified bank differs from 2638fa9")
    addendum_bytes = subprocess.check_output(
        [
            "git",
            "show",
            (
                f"{BANK_COMMIT}:projects/emergence-suite/v2/"
                "results/V2.3.3/gate6-bank2-addendum.json"
            ),
        ],
        cwd=REPO,
    )
    if BANK_ADDENDUM_PATH.read_bytes() != addendum_bytes:
        raise RuntimeError("local bank2 addendum differs from 2638fa9")
    addendum = json.loads(addendum_bytes)
    expected_bank_hash = addendum["result_hashes"][
        "results/challenges/C-V233-M-bank2/retained_states.json"
    ]
    if sha256(BANK_PATH) != expected_bank_hash:
        raise RuntimeError("qualified bank hash mismatch")
    bank = json.loads(bank_bytes)
    states = bank["states"]
    counts = {
        stratum: sum(state["stratum"] == stratum for state in states)
        for stratum in STRATA
    }
    if len(states) != 120 or any(counts[name] != 40 for name in STRATA):
        raise RuntimeError(f"qualified bank is not 40/40/40: {counts}")
    state_hash_failures = []
    for record in states:
        digest = canonical_state_hash(record["serialized_state"])
        if digest != record["state_sha256"]:
            state_hash_failures.append(record["seed"])
    if state_hash_failures:
        raise RuntimeError(
            f"qualified bank state hash failures: {state_hash_failures}"
        )
    return {
        "frozen_plus_repair_identity": identity,
        "qualified_bank_commit": BANK_COMMIT,
        "qualified_bank_sha256": expected_bank_hash,
        "qualified_bank_counts": counts,
        "qualified_bank_state_hash_failures": state_hash_failures,
        "passed": True,
    }, states


def cell_assignment(local_index: int) -> dict[str, Any]:
    return {
        "safe_reliability": (
            "high" if local_index % 2 == 0 else "degraded"
        ),
        "action_cost": (
            "default" if (local_index // 2) % 2 == 0 else "elevated"
        ),
        "schedule": (
            "front_loaded"
            if (local_index // 4) % 2 == 0
            else "distributed"
        ),
        "labels_permuted": local_index % 4 < 2,
        "base_censoring": (
            0.35 if (local_index // 10) % 2 == 0 else 0.65
        ),
        "context_shift": local_index % 4 == 0,
    }


def corrective_stream(
    seed: int,
    cell: dict[str, Any],
) -> tuple[list[tuple[int, int, int]], list[dict[str, Any]]]:
    reliability = 0.85 if cell["safe_reliability"] == "high" else 0.68
    outcomes = []
    configurations = []
    for time in range(DURATION):
        shifted = bool(cell["context_shift"] and time >= DURATION // 2)
        configuration = {
            "event": True,
            "precision": "ordinary",
            "control": "high",
            "broadcast": "collapsed" if shifted else "integrated",
            "real_danger": False,
        }
        row = slice_distribution("T", **configuration)
        safe_indices = [
            index
            for index, observation in enumerate(SUPPORT)
            if observation[0] == 0
            and observation[1] == 0
            and row[index] > 0
        ]
        adverse_indices = [
            index
            for index, observation in enumerate(SUPPORT)
            if observation[0] == 0
            and observation[1] == 1
            and row[index] > 0
        ]
        category_rng = component_rng(
            seed,
            f"v233-m-sealed-reliability-{time}",
            released_block=RELEASED_BLOCK,
        )
        safe = float(category_rng.random()) < reliability
        support_indices = safe_indices if safe else adverse_indices
        weights = np.asarray([row[index] for index in support_indices])
        weights /= weights.sum()
        observation_rng = component_rng(
            seed,
            f"v233-m-sealed-outcome-{time}",
            released_block=RELEASED_BLOCK,
        )
        selected = int(
            observation_rng.choice(len(support_indices), p=weights)
        )
        outcomes.append(SUPPORT[support_indices[selected]])
        configurations.append(configuration)
    return outcomes, configurations


def policy_actions(
    seed: int,
    state: dict[str, Any],
    cell: dict[str, Any],
) -> list[str]:
    cost = (
        float(PARAMETERS["maintenance"]["policy"]["action_cost"])
        if cell["action_cost"] == "default"
        else 2.0
        * float(PARAMETERS["maintenance"]["policy"]["action_cost"])
    )
    probability = policy_avoidance_probability(
        float(state["q_H_formation"][2]), action_cost=cost
    )
    actions = []
    for time in range(DURATION):
        rng = component_rng(
            seed,
            f"v233-m-sealed-policy-{time}",
            released_block=RELEASED_BLOCK,
        )
        actions.append(
            "avoid" if float(rng.random()) < probability else "engage"
        )
    return actions


def closed_loop_availability(
    seed: int,
    actions: list[str],
    censoring: float,
    schedule: str,
) -> list[bool]:
    avoid_positions = [
        index for index, action in enumerate(actions) if action == "avoid"
    ]
    censored_count = int(round(censoring * len(avoid_positions)))
    if schedule == "front_loaded":
        censored = set(avoid_positions[:censored_count])
    else:
        ranked = sorted(
            avoid_positions,
            key=lambda time: float(
                component_rng(
                    seed,
                    f"v233-m-sealed-closed-schedule-{time}",
                    released_block=RELEASED_BLOCK,
                ).random()
            ),
        )
        censored = set(ranked[:censored_count])
    return [time not in censored for time in range(DURATION)]


def dose_availability(
    seed: int,
    dose: float,
    schedule: str,
) -> list[bool]:
    count = int(round(dose * DURATION))
    if schedule == "front_loaded":
        censored = set(range(count))
    else:
        ranked = sorted(
            range(DURATION),
            key=lambda time: float(
                component_rng(
                    seed,
                    f"v233-m-sealed-dose-rank-{time}",
                    released_block=RELEASED_BLOCK,
                ).random()
            ),
        )
        censored = set(ranked[:count])
    return [time not in censored for time in range(DURATION)]


def clone_state(state: dict[str, Any]) -> dict[str, Any]:
    return json.loads(canonical_state_bytes(state))


def run_trajectory(
    state: dict[str, Any],
    outcomes: list[tuple[int, int, int]],
    configurations: list[dict[str, Any]],
    actions: list[str],
    availability: list[bool],
    *,
    lesions: tuple[str, ...] = (),
):
    return run_maintenance_trajectory(
        clone_state(state),
        outcomes,
        configurations,
        actions,
        availability,
        lesions=lesions,
    )


def scientific_error(left, right) -> float:
    errors = []
    for left_state, right_state in zip(left.states, right.states):
        for key in ("H_formation", "G"):
            errors.append(
                float(
                    np.max(
                        np.abs(
                            left_state.posterior_store[key]
                            - right_state.posterior_store[key]
                        )
                    )
                )
            )
        errors.append(
            abs(
                float(left_state.evidence_store["slice"])
                - float(right_state.evidence_store["slice"])
            )
        )
    errors.extend(
        [
            float(np.max(np.abs(left.final_h - right.final_h))),
            float(np.max(np.abs(left.final_g - right.final_g))),
            float(
                np.max(
                    np.abs(
                        left.final_untreated_cue
                        - right.final_untreated_cue
                    )
                )
            ),
        ]
    )
    return max(errors, default=0.0)


def mechanistic_errors(trajectory) -> tuple[float, float]:
    readout = trajectory_readout(trajectory)
    bf_pt = sum(
        float(detail["pairwise_log_bf"]["P/T"])
        for detail in trajectory.contributions
    )
    bf_pd = sum(
        float(detail["pairwise_log_bf"]["P/D"])
        for detail in trajectory.contributions
    )
    return (
        abs(readout["delta_L_PT"] - bf_pt),
        abs(readout["delta_L_PD"] - bf_pd),
    )


def update_identity_error(trajectory) -> float:
    maximum = 0.0
    previous = trajectory.initial_h
    for state, detail in zip(trajectory.states, trajectory.contributions):
        current = state.posterior_store["H_formation"]
        for key, (left, right) in {
            "P/T": (2, 0),
            "P/D": (2, 1),
            "D/T": (1, 0),
        }.items():
            increment = math.log(
                float(current[left]) / float(current[right])
            ) - math.log(float(previous[left]) / float(previous[right]))
            maximum = max(
                maximum,
                abs(increment - float(detail["pairwise_log_bf"][key])),
            )
        audit_one_posterior(state)
        previous = current
    return maximum


def danger_stream(
    seed: int, truth: str, kind: str
) -> tuple[list[tuple[int, int, int]], list[dict[str, Any]]]:
    if kind == "external":
        configuration = {
            "event": True,
            "precision": "ordinary",
            "control": "high",
            "broadcast": "integrated",
            "real_danger": True,
        }
    elif kind == "identity":
        configuration = {
            "event": True,
            "precision": "overwhelm",
            "control": "low",
            "broadcast": "collapsed",
            "real_danger": False,
        }
    else:
        configuration = {
            "event": True,
            "precision": "ordinary",
            "control": "high",
            "broadcast": "integrated",
            "real_danger": False,
        }
    row = slice_distribution(truth, **configuration)
    observations = []
    for time in range(DURATION):
        rng = component_rng(
            seed,
            f"v233-m-sealed-danger-{kind}-{time}",
            released_block=RELEASED_BLOCK,
        )
        observations.append(
            SUPPORT[int(rng.choice(len(row), p=row))]
        )
    return observations, [configuration.copy() for _ in range(DURATION)]


def stratified_interval(
    rows: list[dict[str, Any]], field: str, component: str
) -> list[float]:
    grouped = {
        stratum: np.asarray(
            [float(row[field]) for row in rows if row["stratum"] == stratum]
        )
        for stratum in STRATA
    }
    rng = stable_rng(component)
    means = np.empty(BOOTSTRAP_REPLICATES)
    for draw in range(BOOTSTRAP_REPLICATES):
        pieces = [
            rng.choice(values, size=len(values), replace=True)
            for values in grouped.values()
        ]
        means[draw] = np.concatenate(pieces).mean()
    low, high = np.quantile(means, [0.025, 0.975])
    return [
        float(np.mean([float(row[field]) for row in rows])),
        float(low),
        float(high),
    ]


def within_stratum_interval(
    rows: list[dict[str, Any]],
    field: str,
    stratum: str,
) -> list[float]:
    values = np.asarray(
        [float(row[field]) for row in rows if row["stratum"] == stratum]
    )
    rng = stable_rng(f"{field}-{stratum}")
    means = np.empty(BOOTSTRAP_REPLICATES)
    for draw in range(BOOTSTRAP_REPLICATES):
        means[draw] = rng.choice(
            values, size=len(values), replace=True
        ).mean()
    low, high = np.quantile(means, [0.025, 0.975])
    return [float(values.mean()), float(low), float(high)]


def pava(values: np.ndarray) -> np.ndarray:
    blocks = [
        {"start": index, "end": index + 1, "mean": float(value), "weight": 1}
        for index, value in enumerate(values)
    ]
    index = 0
    while index < len(blocks) - 1:
        if blocks[index]["mean"] <= blocks[index + 1]["mean"]:
            index += 1
            continue
        left = blocks[index]
        right = blocks[index + 1]
        weight = left["weight"] + right["weight"]
        merged = {
            "start": left["start"],
            "end": right["end"],
            "mean": (
                left["mean"] * left["weight"]
                + right["mean"] * right["weight"]
            )
            / weight,
            "weight": weight,
        }
        blocks[index : index + 2] = [merged]
        index = max(0, index - 1)
    fitted = np.empty(len(values))
    for block in blocks:
        fitted[block["start"] : block["end"]] = block["mean"]
    return fitted


def isotonic_test(matrix: np.ndarray, component: str) -> dict[str, Any]:
    means = matrix.mean(axis=0)
    fitted = pava(means)
    grand = float(matrix.mean())
    observed = float(
        np.sum((matrix - grand) ** 2)
        - np.sum((matrix - fitted[None, :]) ** 2)
    )
    rng = stable_rng(component)
    exceedances = 0
    for _ in range(ISOTONIC_PERMUTATIONS):
        permuted = np.vstack(
            [row[rng.permutation(len(row))] for row in matrix]
        )
        permuted_means = permuted.mean(axis=0)
        permuted_fit = pava(permuted_means)
        permuted_grand = float(permuted.mean())
        statistic = float(
            np.sum((permuted - permuted_grand) ** 2)
            - np.sum((permuted - permuted_fit[None, :]) ** 2)
        )
        exceedances += statistic >= observed - 1e-15
    return {
        "dose_means": means.tolist(),
        "isotonic_fitted_means": fitted.tolist(),
        "statistic": observed,
        "permutations": ISOTONIC_PERMUTATIONS,
        "p_value": (exceedances + 1) / (ISOTONIC_PERMUTATIONS + 1),
        "fitted_nondecreasing": bool(
            np.all(np.diff(fitted) >= -TOLERANCE)
        ),
    }


def natural_weighted(
    rows: list[dict[str, Any]], fields: tuple[str, ...]
) -> dict[str, Any]:
    bank2 = json.loads(
        (
            ROOT
            / "results"
            / "challenges"
            / "C-V233-M-bank2"
            / "summary.json"
        ).read_text()
    )
    eligibility = bank2["criteria"][
        "1_scientific_sampling_adequacy"
    ]["eligibility"]
    total = sum(eligibility[name]["eligible_count"] for name in STRATA)
    weights = {
        name: eligibility[name]["eligible_count"] / total
        for name in STRATA
    }
    per_stratum = {
        name: {
            field: float(
                np.mean(
                    [
                        float(row[field])
                        for row in rows
                        if row["stratum"] == name
                    ]
                )
            )
            for field in fields
        }
        for name in STRATA
    }
    return {
        "classification": "descriptive_only",
        "conditioning_population": (
            "bank2 candidates within the formed nonsaturated bands"
        ),
        "weights": weights,
        "per_stratum_means": per_stratum,
        "weighted_means": {
            field: sum(
                weights[name] * per_stratum[name][field]
                for name in STRATA
            )
            for field in fields
        },
        "equal_stratum_primary_means": {
            field: float(np.mean([float(row[field]) for row in rows]))
            for field in fields
        },
        "criterial": False,
    }


def main() -> None:
    custody, bank_states = verify_bank_custody()
    ordered_bank = [
        record
        for stratum in STRATA
        for record in bank_states
        if record["stratum"] == stratum
    ]
    maintenance_seeds = list(
        range(FIRST_SEED, FIRST_SEED + USED_WORLD_COUNT)
    )
    rows = []
    dose_rows = []
    decomposition_rows = []
    failure_localization = []
    all_trajectories = []
    clone_failures = []

    for world_index, (seed, bank_record) in enumerate(
        zip(maintenance_seeds, ordered_bank)
    ):
        stratum = bank_record["stratum"]
        local_index = world_index % 40
        cell = cell_assignment(local_index)
        state = bank_record["serialized_state"]
        serialized = canonical_state_bytes(state)
        clone_count = 6 + len(DOSES) + 8
        clones = [bytes(bytearray(serialized)) for _ in range(clone_count)]
        clone_ok = (
            hashlib.sha256(serialized).hexdigest()
            == bank_record["state_sha256"]
            and all(clone == serialized for clone in clones)
        )
        if not clone_ok:
            clone_failures.append(seed)

        outcomes, configurations = corrective_stream(seed, cell)
        actions = policy_actions(seed, state, cell)
        base_availability = closed_loop_availability(
            seed,
            actions,
            float(cell["base_censoring"]),
            str(cell["schedule"]),
        )
        arm_a = run_trajectory(
            state,
            outcomes,
            configurations,
            ["engage"] * DURATION,
            [True] * DURATION,
        )
        arm_b = run_trajectory(
            state,
            outcomes,
            configurations,
            actions,
            base_availability,
        )
        arm_c = run_trajectory(
            state,
            outcomes,
            configurations,
            actions.copy(),
            base_availability.copy(),
        )
        arm_d = run_trajectory(
            state,
            outcomes,
            configurations,
            ["avoid"] * DURATION,
            [True] * DURATION,
        )
        arm_e = run_trajectory(
            state,
            outcomes,
            configurations,
            ["sham"] * DURATION,
            [True] * DURATION,
        )
        permuted = {
            "engage": "sham",
            "avoid": "engage",
            "sham": "avoid",
        }
        label_actions = (
            [permuted[action] for action in actions]
            if cell["labels_permuted"]
            else actions.copy()
        )
        label_trajectory = run_trajectory(
            state,
            outcomes,
            configurations,
            label_actions,
            base_availability.copy(),
        )
        fixed_a = run_trajectory(
            state,
            outcomes,
            configurations,
            ["engage"] * DURATION,
            [True] * DURATION,
            lesions=("root_coupling",),
        )
        fixed_b = run_trajectory(
            state,
            outcomes,
            configurations,
            actions,
            base_availability,
            lesions=("root_coupling",),
        )
        all_trajectories.extend(
            [
                arm_a,
                arm_b,
                arm_c,
                arm_d,
                arm_e,
                label_trajectory,
                fixed_a,
                fixed_b,
            ]
        )
        readout_a = trajectory_readout(arm_a)
        readout_b = trajectory_readout(arm_b)
        readout_c = trajectory_readout(arm_c)
        readout_fixed_a = trajectory_readout(fixed_a)
        readout_fixed_b = trajectory_readout(fixed_b)
        m_pt = readout_b["delta_L_PT"] - readout_a["delta_L_PT"]
        m_pd = readout_b["delta_L_PD"] - readout_a["delta_L_PD"]
        hidden_indices = [
            index
            for index, available in enumerate(base_availability)
            if not available
        ]
        withheld_pt = -sum(
            float(arm_a.contributions[index]["pairwise_log_bf"]["P/T"])
            for index in hidden_indices
        )
        withheld_pd = -sum(
            float(arm_a.contributions[index]["pairwise_log_bf"]["P/D"])
            for index in hidden_indices
        )
        censored_count = len(hidden_indices)

        dose_m_pt = []
        dose_m_pd = []
        dose_trajectories = {}
        for dose in DOSES:
            availability = dose_availability(
                seed, dose, str(cell["schedule"])
            )
            trajectory = run_trajectory(
                state,
                outcomes,
                configurations,
                actions,
                availability,
            )
            all_trajectories.append(trajectory)
            readout = trajectory_readout(trajectory)
            m_dose_pt = (
                readout["delta_L_PT"] - readout_a["delta_L_PT"]
            )
            m_dose_pd = (
                readout["delta_L_PD"] - readout_a["delta_L_PD"]
            )
            dose_m_pt.append(m_dose_pt)
            dose_m_pd.append(m_dose_pd)
            identity_pt, identity_pd = mechanistic_errors(trajectory)
            delivered_pairs = [
                (outcome, configuration)
                for outcome, configuration, available in zip(
                    outcomes, configurations, availability
                )
                if available
            ]
            compressed = run_trajectory(
                state,
                [pair[0] for pair in delivered_pairs],
                [pair[1] for pair in delivered_pairs],
                ["engage"] * len(delivered_pairs),
                [True] * len(delivered_pairs),
            )
            schedule_error = max(
                float(np.max(np.abs(trajectory.final_h - compressed.final_h))),
                float(np.max(np.abs(trajectory.final_g - compressed.final_g))),
            )
            dose_trajectories[str(dose)] = trajectory
            dose_rows.append(
                {
                    "seed": seed,
                    "bank_seed": bank_record["seed"],
                    "stratum": stratum,
                    "dose": dose,
                    "schedule": cell["schedule"],
                    "M_PT": m_dose_pt,
                    "M_PD": m_dose_pd,
                    "delivered_count": readout["delivered_count"],
                    "censored_count": readout["censored_count"],
                    "mechanistic_error_PT": identity_pt,
                    "mechanistic_error_PD": identity_pd,
                    "matched_evidence_schedule_error": schedule_error,
                }
            )

        external_outcomes, external_configs = danger_stream(
            seed, "D", "external"
        )
        identity_outcomes, identity_configs = danger_stream(
            seed, "P", "identity"
        )
        generic_outcomes, generic_configs = danger_stream(
            seed, "T", "generic"
        )
        external = run_trajectory(
            state,
            external_outcomes,
            external_configs,
            ["engage"] * DURATION,
            [True] * DURATION,
        )
        identity_danger = run_trajectory(
            state,
            identity_outcomes,
            identity_configs,
            ["engage"] * DURATION,
            [True] * DURATION,
        )
        generic = run_trajectory(
            state,
            generic_outcomes,
            generic_configs,
            ["engage"] * DURATION,
            [True] * DURATION,
        )
        all_trajectories.extend([external, identity_danger, generic])
        generic_readout = trajectory_readout(generic)

        yoke_error = scientific_error(arm_b, arm_c)
        no_action_error = max(
            scientific_error(arm_a, arm_d),
            scientific_error(arm_a, arm_e),
        )
        label_error = scientific_error(arm_b, label_trajectory)
        root_difference = (
            abs(readout_a["root_revision"])
            - abs(readout_b["root_revision"])
        )
        transfer_difference = (
            abs(readout_a["untreated_cue_transfer"])
            - abs(readout_b["untreated_cue_transfer"])
        )
        fixed_m_pt = (
            readout_fixed_b["delta_L_PT"]
            - readout_fixed_a["delta_L_PT"]
        )
        fixed_m_pd = (
            readout_fixed_b["delta_L_PD"]
            - readout_fixed_a["delta_L_PD"]
        )
        fixed_transfer_difference = (
            abs(readout_fixed_a["untreated_cue_transfer"])
            - abs(readout_fixed_b["untreated_cue_transfer"])
        )
        direct_residual_pt = (
            readout_b["delta_L_PT"] - readout_c["delta_L_PT"]
        )
        direct_residual_pd = (
            readout_b["delta_L_PD"] - readout_c["delta_L_PD"]
        )
        max_slice_bf = max(
            abs(float(value))
            for trajectory in (
                arm_a,
                arm_b,
                external,
                identity_danger,
                generic,
            )
            for detail in trajectory.contributions
            for value in detail["pairwise_log_bf"].values()
        )
        update_error = max(
            update_identity_error(trajectory)
            for trajectory in (
                arm_a,
                arm_b,
                arm_c,
                arm_d,
                arm_e,
                external,
                identity_danger,
                generic,
                *dose_trajectories.values(),
            )
        )
        complete = trajectory_readout(dose_trajectories["1.0"])
        row = {
            "seed": seed,
            "seed_position": world_index + 1,
            "bank_seed": bank_record["seed"],
            "bank_state_sha256": bank_record["state_sha256"],
            "stratum": stratum,
            "q0_P": float(state["q_H_formation"][2]),
            **cell,
            "A_delta_L_PT": readout_a["delta_L_PT"],
            "A_delta_L_PD": readout_a["delta_L_PD"],
            "B_delta_L_PT": readout_b["delta_L_PT"],
            "B_delta_L_PD": readout_b["delta_L_PD"],
            "M_PT": m_pt,
            "M_PD": m_pd,
            "B_delivered": readout_b["delivered_count"],
            "B_censored": readout_b["censored_count"],
            "B_avoidance": readout_b["realized_avoidance"],
            "M_PT_per_withheld": (
                m_pt / censored_count if censored_count else 0.0
            ),
            "M_PD_per_withheld": (
                m_pd / censored_count if censored_count else 0.0
            ),
            "complete_delta_L_PT": complete["delta_L_PT"],
            "complete_delta_L_PD": complete["delta_L_PD"],
            "yoke_max_error": yoke_error,
            "no_action_max_error": no_action_error,
            "label_permutation_max_error": label_error,
            "dose_M_PT": dose_m_pt,
            "dose_M_PD": dose_m_pd,
            "external_selected": LABELS[int(np.argmax(external.final_h))],
            "identity_selected": LABELS[
                int(np.argmax(identity_danger.final_h))
            ],
            "generic_selected": LABELS[int(np.argmax(generic.final_h))],
            "generic_delta_L_PT": generic_readout["delta_L_PT"],
            "generic_delta_L_PD": generic_readout["delta_L_PD"],
            "root_revision_difference": root_difference,
            "transfer_difference": transfer_difference,
            "fixed_transfer_difference": fixed_transfer_difference,
            "fixed_M_PT": fixed_m_pt,
            "fixed_M_PD": fixed_m_pd,
            "withheld_BF_identity_PT": withheld_pt,
            "withheld_BF_identity_PD": withheld_pd,
            "availability_identity_error_PT": abs(m_pt - withheld_pt),
            "availability_identity_error_PD": abs(m_pd - withheld_pd),
            "direct_action_residual_PT": direct_residual_pt,
            "direct_action_residual_PD": direct_residual_pd,
            "policy_generated_censoring": int(
                all(actions[index] == "avoid" for index in hidden_indices)
            ),
            "maximum_slice_log_BF": max_slice_bf,
            "maximum_update_identity_error": update_error,
            "clone_ok": int(clone_ok),
            "released_seed_authorization": (
                f"{FIRST_SEED}:{LAST_SEED}"
            ),
        }
        rows.append(row)
        decomposition_rows.append(
            {
                "seed": seed,
                "bank_seed": bank_record["seed"],
                "stratum": stratum,
                "q0_P": row["q0_P"],
                "avoidance_count": row["B_avoidance"],
                "censored_count": censored_count,
                "total_M_PT": m_pt,
                "total_M_PD": m_pd,
                "withheld_BF_identity_PT": withheld_pt,
                "withheld_BF_identity_PD": withheld_pd,
                "availability_identity_error_PT": abs(
                    m_pt - withheld_pt
                ),
                "availability_identity_error_PD": abs(
                    m_pd - withheld_pd
                ),
                "closed_minus_yoked_direct_residual_PT": (
                    direct_residual_pt
                ),
                "closed_minus_yoked_direct_residual_PD": (
                    direct_residual_pd
                ),
                "policy_generated_censoring": row[
                    "policy_generated_censoring"
                ],
                "interpretation": (
                    "Availability identity and endogenous policy feedback "
                    "are complementary causal results, not additive "
                    "coefficient terms."
                ),
            }
        )
        exact_failures = {
            "complete_censoring": max(
                abs(row["complete_delta_L_PT"]),
                abs(row["complete_delta_L_PD"]),
            )
            > TOLERANCE,
            "yoke": yoke_error > TOLERANCE,
            "no_action": no_action_error > TOLERANCE,
            "label": label_error > TOLERANCE,
            "availability_identity": max(
                row["availability_identity_error_PT"],
                row["availability_identity_error_PD"],
            )
            > TOLERANCE,
            "update_identity": update_error > TOLERANCE,
            "finite_bound": max_slice_bf > B_MAX + TOLERANCE,
        }
        if any(exact_failures.values()):
            failure_localization.append(
                {
                    "seed": seed,
                    "bank_seed": bank_record["seed"],
                    "failed_exact_checks": [
                        key for key, failed in exact_failures.items() if failed
                    ],
                    "A_contributions": list(arm_a.contributions),
                    "B_contributions": list(arm_b.contributions),
                }
            )

    intervals = {
        field: stratified_interval(rows, field, f"ci-{field}")
        for field in (
            "A_delta_L_PT",
            "A_delta_L_PD",
            "M_PT",
            "M_PD",
            "root_revision_difference",
            "transfer_difference",
            "fixed_M_PT",
            "fixed_M_PD",
            "M_PT_per_withheld",
            "M_PD_per_withheld",
        )
    }
    stratum_maintenance = {
        stratum: {
            pair: within_stratum_interval(rows, pair, stratum)
            for pair in ("M_PT", "M_PD")
        }
        for stratum in STRATA
    }
    dose_matrix_pt = np.asarray(
        [[float(value) for value in row["dose_M_PT"]] for row in rows]
    )
    dose_matrix_pd = np.asarray(
        [[float(value) for value in row["dose_M_PD"]] for row in rows]
    )
    isotonic_pt = isotonic_test(dose_matrix_pt, "isotonic-pt")
    isotonic_pd = isotonic_test(dose_matrix_pd, "isotonic-pd")
    maximum_dose_identity = max(
        max(
            float(row["mechanistic_error_PT"]),
            float(row["mechanistic_error_PD"]),
        )
        for row in dose_rows
    )
    maximum_schedule_error = max(
        float(row["matched_evidence_schedule_error"])
        for row in dose_rows
    )
    external_d_count = sum(
        row["external_selected"] == "D" for row in rows
    )
    identity_p_count = sum(
        row["identity_selected"] == "P" for row in rows
    )
    generic_p_count = sum(
        row["generic_selected"] == "P" for row in rows
    )
    external_d_rate = wilson(external_d_count, len(rows))
    identity_p_rate = wilson(identity_p_count, len(rows))
    generic_p_rate = wilson(generic_p_count, len(rows))
    fixed_transfer_max = max(
        abs(float(row["fixed_transfer_difference"])) for row in rows
    )
    constitution = cumulative_graded_update_audit()
    forbidden = forbidden_path_audit()
    challenge_constitution = {
        "maximum_update_identity_error": max(
            float(row["maximum_update_identity_error"]) for row in rows
        ),
        "maximum_slice_log_BF": max(
            float(row["maximum_slice_log_BF"]) for row in rows
        ),
        "frozen_B_max": B_MAX,
        "masked_and_delivered_composition_maximum_error": (
            maximum_dose_identity
        ),
        "matched_evidence_schedule_maximum_error": (
            maximum_schedule_error
        ),
        "one_posterior_audited_trajectory_count": len(all_trajectories),
        "cumulative_constitution": constitution,
        "forbidden_path_audit": forbidden,
    }
    challenge_constitution["passed"] = (
        challenge_constitution["maximum_update_identity_error"]
        <= TOLERANCE
        and challenge_constitution["maximum_slice_log_BF"]
        <= B_MAX + TOLERANCE
        and maximum_dose_identity <= TOLERANCE
        and maximum_schedule_error <= TOLERANCE
        and constitution["passed"]
        and forbidden["passed"]
    )

    criteria = {
        "1_safe_full_observation_erodes_P": {
            "class": "scientific",
            "A_delta_L_PT_95_interval": intervals["A_delta_L_PT"],
            "A_delta_L_PD_95_interval": intervals["A_delta_L_PD"],
            "passed": (
                intervals["A_delta_L_PT"][2] < 0
                and intervals["A_delta_L_PD"][2] < 0
            ),
        },
        "2_censoring_protects": {
            "class": "scientific",
            "M_PT_95_interval": intervals["M_PT"],
            "M_PD_95_interval": intervals["M_PD"],
            "per_stratum": stratum_maintenance,
            "passed": (
                intervals["M_PT"][1] > 0
                and intervals["M_PD"][1] > 0
                and all(
                    stratum_maintenance[stratum][pair][1] > 0
                    for stratum in STRATA
                    for pair in ("M_PT", "M_PD")
                )
            ),
        },
        "3_complete_censoring_neutral": {
            "class": "scientific_semantic",
            "maximum_absolute_delta_log_odds": max(
                max(
                    abs(float(row["complete_delta_L_PT"])),
                    abs(float(row["complete_delta_L_PD"])),
                )
                for row in rows
            ),
            "passed": all(
                max(
                    abs(float(row["complete_delta_L_PT"])),
                    abs(float(row["complete_delta_L_PD"])),
                )
                <= TOLERANCE
                for row in rows
            ),
        },
        "4_closed_loop_yoked_identity": {
            "class": "semantic",
            "maximum_error": max(
                float(row["yoke_max_error"]) for row in rows
            ),
            "passed": all(
                float(row["yoke_max_error"]) <= TOLERANCE for row in rows
            ),
        },
        "5_no_action_bonus": {
            "class": "semantic",
            "maximum_A_D_E_error": max(
                float(row["no_action_max_error"]) for row in rows
            ),
            "maximum_label_permutation_error": max(
                float(row["label_permutation_max_error"]) for row in rows
            ),
            "passed": all(
                float(row["no_action_max_error"]) <= TOLERANCE
                and float(row["label_permutation_max_error"]) <= TOLERANCE
                for row in rows
            ),
        },
        "6_dose_response": {
            "class": "scientific",
            "doses": list(DOSES),
            "M_PT_isotonic": isotonic_pt,
            "M_PD_isotonic": isotonic_pd,
            "maximum_mechanistic_identity_error": maximum_dose_identity,
            "maximum_matched_evidence_schedule_error": (
                maximum_schedule_error
            ),
            "passed": (
                isotonic_pt["p_value"] <= 0.05
                and isotonic_pd["p_value"] <= 0.05
                and isotonic_pt["fitted_nondecreasing"]
                and isotonic_pd["fitted_nondecreasing"]
                and maximum_dose_identity <= TOLERANCE
                and maximum_schedule_error <= TOLERANCE
            ),
        },
        "7_D_P_danger_control": {
            "class": "scientific",
            "external_D_selection_rate_95_wilson": external_d_rate,
            "identity_P_selection_rate_95_wilson": identity_p_rate,
            "generic_P_selection_rate_95_wilson": generic_p_rate,
            "generic_null_band_maximum": 0.15,
            "passed": (
                external_d_rate[0] >= 0.80
                and generic_p_rate[0] <= 0.15
            ),
        },
        "8_root_transfer_follows_delivered_evidence": {
            "class": "scientific",
            "root_revision_difference_95_interval": intervals[
                "root_revision_difference"
            ],
            "transfer_difference_95_interval": intervals[
                "transfer_difference"
            ],
            "fixed_G_maximum_transfer_difference": fixed_transfer_max,
            "fixed_G_M_PT_95_interval": intervals["fixed_M_PT"],
            "fixed_G_M_PD_95_interval": intervals["fixed_M_PD"],
            "passed": (
                intervals["root_revision_difference"][1] > 0
                and intervals["transfer_difference"][1] > 0
                and fixed_transfer_max <= TOLERANCE
                and intervals["fixed_M_PT"][1] > 0
                and intervals["fixed_M_PD"][1] > 0
            ),
        },
        "9_constitution_identity_custody": {
            "class": "semantic_custody",
            "challenge_constitution": challenge_constitution,
            "frozen_and_bank_identity": custody,
            "seed_block_used": [
                maintenance_seeds[0],
                maintenance_seeds[-1],
            ],
            "released_seed_block": [FIRST_SEED, LAST_SEED],
            "ITS_ledger_world_count": len(rows),
            "clone_failure_seeds": clone_failures,
            "exact_failure_count": len(failure_localization),
            "passed": (
                challenge_constitution["passed"]
                and custody["passed"]
                and not clone_failures
                and not failure_localization
                and all(
                    FIRST_SEED <= int(row["seed"]) <= LAST_SEED
                    for row in rows
                )
                and len(rows) == USED_WORLD_COUNT
            ),
        },
    }
    verdict = (
        "PASS"
        if all(bool(criterion["passed"]) for criterion in criteria.values())
        else "FAIL"
    )
    failed_criteria = [
        name for name, criterion in criteria.items() if not criterion["passed"]
    ]

    per_withheld = {
        "M_PT_per_withheld_95_interval": intervals[
            "M_PT_per_withheld"
        ],
        "M_PD_per_withheld_95_interval": intervals[
            "M_PD_per_withheld"
        ],
        "total_delivered": sum(int(row["B_delivered"]) for row in rows),
        "total_censored": sum(int(row["B_censored"]) for row in rows),
    }
    decomposition = {
        "classification": "descriptive_causal_decomposition",
        "availability_identity_maximum_error_PT": max(
            float(row["availability_identity_error_PT"]) for row in rows
        ),
        "availability_identity_maximum_error_PD": max(
            float(row["availability_identity_error_PD"]) for row in rows
        ),
        "closed_yoked_direct_action_maximum_residual_PT": max(
            abs(float(row["direct_action_residual_PT"])) for row in rows
        ),
        "closed_yoked_direct_action_maximum_residual_PD": max(
            abs(float(row["direct_action_residual_PD"])) for row in rows
        ),
        "policy_generated_censoring_world_count": sum(
            int(row["policy_generated_censoring"]) for row in rows
        ),
        "table": "decomposition.csv",
        "note": (
            "The availability identity and endogenous policy feedback are "
            "two complementary causal results, not additive authored "
            "coefficients."
        ),
    }
    natural = natural_weighted(
        rows,
        (
            "A_delta_L_PT",
            "A_delta_L_PD",
            "M_PT",
            "M_PD",
            "root_revision_difference",
            "transfer_difference",
        ),
    )
    negative_control = {
        "status": "NOT_COMPUTABLE_FROM_REQUESTED_TRACES",
        "reason": (
            "The qualified input contains only the 120 formed bank states. "
            "No unformed serialized state or maintenance trace was "
            "requested; no extra constructor or maintenance run was added."
        ),
        "criterial": False,
    }
    cell_stress = {}
    for dimension in (
        "safe_reliability",
        "action_cost",
        "schedule",
        "labels_permuted",
        "base_censoring",
        "context_shift",
    ):
        values = sorted({str(row[dimension]) for row in rows})
        cell_stress[dimension] = {
            value: {
                "count": sum(str(row[dimension]) == value for row in rows),
                "mean_M_PT": float(
                    np.mean(
                        [
                            float(row["M_PT"])
                            for row in rows
                            if str(row[dimension]) == value
                        ]
                    )
                ),
                "mean_M_PD": float(
                    np.mean(
                        [
                            float(row["M_PD"])
                            for row in rows
                            if str(row[dimension]) == value
                        ]
                    )
                ),
            }
            for value in values
        }
    stress = {
        "classification": "distributional_stress_noncriterial",
        "private_cell_summaries": cell_stress,
        "graded_update_distribution": (
            publish_stratified_update_distribution()
        ),
    }
    summary = {
        "challenge": CHALLENGE,
        "verdict": verdict,
        "failed_criteria": failed_criteria,
        "sealed_cell_instantiation": {
            "mapping_frozen_before_execution": True,
            "safe_reliability": {
                "high": 0.85,
                "degraded_but_informative": 0.68,
                "source": "frozen default and public 0.8 robustness multiplier",
            },
            "action_cost": {
                "default": 0.1,
                "elevated": 0.2,
                "source": "frozen default and public 2.0 robustness multiplier",
            },
            "base_closed_loop_censoring": [0.35, 0.65],
            "dose_grid": list(DOSES),
            "schedule": ["front_loaded", "distributed"],
            "label_permutation_fraction": 0.5,
            "context_shift_fraction": 0.25,
            "context_shift": "integrated to collapsed broadcast at mid-run",
            "world_assignment": (
                "qualified bank ordered moderate/strong/very_strong; "
                "first 40 states per stratum paired to released seeds "
                "816001:816120"
            ),
        },
        "criteria": criteria,
        "verdict_classes": {
            "scientific": (
                "PASS"
                if all(
                    criteria[name]["passed"]
                    for name in (
                        "1_safe_full_observation_erodes_P",
                        "2_censoring_protects",
                        "3_complete_censoring_neutral",
                        "6_dose_response",
                        "7_D_P_danger_control",
                        "8_root_transfer_follows_delivered_evidence",
                    )
                )
                else "FAIL"
            ),
            "semantic": (
                "PASS"
                if all(
                    criteria[name]["passed"]
                    for name in (
                        "3_complete_censoring_neutral",
                        "4_closed_loop_yoked_identity",
                        "5_no_action_bonus",
                        "9_constitution_identity_custody",
                    )
                )
                else "FAIL"
            ),
            "distributional_stress": "DESCRIPTIVE_ONLY",
            "process_custody": (
                "PASS"
                if criteria["9_constitution_identity_custody"]["passed"]
                else "FAIL"
            ),
        },
        "world_count": len(rows),
        "stratum_counts": {
            stratum: sum(row["stratum"] == stratum for row in rows)
            for stratum in STRATA
        },
        "effect_intervals": intervals,
        "round2_descriptive_additions": {
            "per_withheld_observation": per_withheld,
            "causal_decomposition": decomposition,
            "natural_constructor_weighting": natural,
            "unformed_negative_control": negative_control,
        },
        "stress": stress,
        "failure_interpretation": (
            None
            if verdict == "PASS"
            else (
                "Criterion-2 failure with intact 1/3/4 is a genuine C1b "
                "negative; criterion-4/5 failure is action-route "
                "architecture failure; criterion-6 mechanistic failure "
                "is an undeclared evidence path; criterion-7 failure "
                "revives D/P conflation."
            )
        ),
        "maintenance_seed_block_used": [
            maintenance_seeds[0],
            maintenance_seeds[-1],
        ],
        "unused_released_seed_block": [
            maintenance_seeds[-1] + 1,
            LAST_SEED,
        ],
        "challenge_spec_sha256": sha256(CHALLENGE_PATH),
    }
    seed_ledger = [
        {
            "seed": seed,
            "position": position,
            "used": int(seed in set(maintenance_seeds)),
            "reason": (
                "paired_base_world"
                if seed in set(maintenance_seeds)
                else "not_used_after_first_eligible_120_world_population"
            ),
            "released_block_authorization": f"{FIRST_SEED}:{LAST_SEED}",
        }
        for position, seed in enumerate(
            range(FIRST_SEED, LAST_SEED + 1), start=1
        )
    ]
    write_csv(RESULT_DIR / "per_world.csv", rows)
    write_csv(RESULT_DIR / "per_dose.csv", dose_rows)
    write_csv(RESULT_DIR / "decomposition.csv", decomposition_rows)
    write_csv(RESULT_DIR / "seed_ledger.csv", seed_ledger)
    write_json(RESULT_DIR / "failed-worlds.json", {
        "failed_world_count": len(failure_localization),
        "worlds": failure_localization,
    })
    write_json(RESULT_DIR / "stress.json", stress)
    write_json(RESULT_DIR / "summary.json", summary)

    criteria_lines = "\n".join(
        f"{index}. **{'PASS' if criterion['passed'] else 'FAIL'}** — "
        f"`{name}`"
        for index, (name, criterion) in enumerate(criteria.items(), start=1)
    )
    report = f"""# {CHALLENGE}

Preregistered verdict: **{verdict}**.

The runner verified the frozen `3e9bad2` identity plus the authorized repair,
and the committed 120-state bank2 bank at 40/40/40. It used maintenance seeds
`{maintenance_seeds[0]}:{maintenance_seeds[-1]}` from the released block.

## Nine sealed criteria

{criteria_lines}

Safe full observation ΔL^PT / ΔL^PD were
`{intervals['A_delta_L_PT']}` / `{intervals['A_delta_L_PD']}`.
Maintenance M^PT / M^PD were `{intervals['M_PT']}` /
`{intervals['M_PD']}`. External danger selected D at
`{external_d_rate[0]:.4f}` (95% Wilson
`[{external_d_rate[1]:.4f}, {external_d_rate[2]:.4f}]`); generic adversity
selected P at `{generic_p_rate[0]:.4f}`.

Dose isotonic p-values were `{isotonic_pt['p_value']:.6g}` (P/T) and
`{isotonic_pd['p_value']:.6g}` (P/D). Maximum mechanistic identity error was
`{maximum_dose_identity:.3g}` and matched-evidence schedule error was
`{maximum_schedule_error:.3g}`.

## Verdict classes

- Scientific: **{summary['verdict_classes']['scientific']}**
- Semantic: **{summary['verdict_classes']['semantic']}**
- Distributional stress: **DESCRIPTIVE ONLY**
- Process custody: **{summary['verdict_classes']['process_custody']}**

## Round-2 descriptive additions

Per-withheld-observation M^PT / M^PD were
`{intervals['M_PT_per_withheld']}` /
`{intervals['M_PD_per_withheld']}`. The within-world availability identity,
endogenous-policy mediator, and zero direct-action residual are published in
`decomposition.csv`. Natural-constructor weighting is descriptive and does
not replace the equal-stratum primary estimand. The unformed-state negative
control was not computable because the requested traces contain only formed
bank states; no extra run was introduced.

All failures and BF decompositions are retained in `failed-worlds.json`.
"""
    (RESULT_DIR / "report.md").write_text(report, encoding="utf-8")
    result_files = [
        RESULT_DIR / "per_world.csv",
        RESULT_DIR / "per_dose.csv",
        RESULT_DIR / "decomposition.csv",
        RESULT_DIR / "seed_ledger.csv",
        RESULT_DIR / "failed-worlds.json",
        RESULT_DIR / "stress.json",
        RESULT_DIR / "summary.json",
        RESULT_DIR / "report.md",
    ]
    addendum = {
        "stage": "V2.3.3",
        "challenge": CHALLENGE,
        "verdict": verdict,
        "criterion_verdicts": {
            name: "PASS" if criterion["passed"] else "FAIL"
            for name, criterion in criteria.items()
        },
        "verdict_classes": summary["verdict_classes"],
        "qualified_bank_commit": BANK_COMMIT,
        "maintenance_seed_block_released": [FIRST_SEED, LAST_SEED],
        "maintenance_seed_block_used": [
            maintenance_seeds[0],
            maintenance_seeds[-1],
        ],
        "identity": custody,
        "challenge_spec_sha256": sha256(CHALLENGE_PATH),
        "challenge_runner_sha256": sha256(Path(__file__)),
        "result_hashes": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in result_files
        },
        "engine_code_changed": False,
    }
    write_json(ADDENDUM_PATH, addendum)
    MILESTONE_PATH.write_text(
        f"""# V2.3.3 Gate 6 maintenance update

`{CHALLENGE}` preregistered verdict: **{verdict}**. All nine sealed criteria
were run on the qualified 40/40/40 bank2 states using the first 120 released
maintenance seeds. Scientific, semantic, and custody classes were
`{summary['verdict_classes']['scientific']}`,
`{summary['verdict_classes']['semantic']}`, and
`{summary['verdict_classes']['process_custody']}` respectively;
distributional stress remained descriptive only. Maintenance M^PT and M^PD
were `{intervals['M_PT']}` and `{intervals['M_PD']}`. Round-2
per-withheld-observation, causal-decomposition, and natural-weighting
readouts are published without changing frozen criteria.
""",
        encoding="utf-8",
    )
    addendum["result_hashes"][
        str(MILESTONE_PATH.relative_to(ROOT))
    ] = sha256(MILESTONE_PATH)
    write_json(ADDENDUM_PATH, addendum)


if __name__ == "__main__":
    main()
