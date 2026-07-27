"""Run the revealed C-V23b formation challenge against frozen V2.3.1.

This file is challenge-layer code only.  It declares worlds in the public
contract vocabulary and calls the frozen inference API.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from ref.precision import precision_categorical  # noqa: E402
from ref.templates import dirichlet_update  # noqa: E402
from ref.v23 import (  # noqa: E402
    BROADCAST_PRIOR,
    CONTROL_PRIOR,
    EVENT_BASE,
    POLICY_PRIOR,
    ROOT_PRIOR,
    WORLD_PRIOR,
    PARAMETERS as V23_PARAMETERS,
)
from ref.v231 import (  # noqa: E402
    EVENT_PRECISION,
    INITIAL_STRUCTURE_PRIOR,
    PARAMETERS,
    REFLEXIVE_MONITOR_RELIABILITY,
    infer_policy,
    infer_slice,
)


CHALLENGE = "C-V23b"
FREEZE_COMMIT = "7d5650c"
FIRST_SEED = 809301
LAST_RELEASED_SEED = 809900
BASE_WORLD_COUNT = 120
TRAJECTORY_COUNT = 240
WORLDS_PER_CELL = 8
P99_BOUND_REPORTED = 0.097067
MAX_MULTIPLIER = 1.75
EXCEEDANCE_RATE_LIMIT = 0.015
FORMATION_MARGIN = 1.0
AVOIDANCE_REDUCTION = 0.82
CONTROL_LEVELS = (0.0, 0.25, 0.50, 0.75, 1.0)
LOW_CONTROL_FRACTIONS = (1.0, 0.75, 0.50, 0.25, 0.0)
PROFILE_NAMES = ("none", "steady-low", "bursty-moderate")
RESULT_DIR = ROOT / "results" / "challenges" / CHALLENGE
MANIFEST_PATH = ROOT / "results" / "V2.3.1" / "freeze-manifest.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(data: object) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def git_bytes(commit: str, relative_path: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{commit}:{relative_path}"], cwd=REPO
    )


def verify_freeze_identity() -> dict[str, object]:
    relative_manifest = str(MANIFEST_PATH.relative_to(REPO))
    committed_bytes = git_bytes(FREEZE_COMMIT, relative_manifest)
    committed = json.loads(committed_bytes)
    local = json.loads(MANIFEST_PATH.read_text())
    if local != committed:
        raise RuntimeError("local V2.3.1 manifest differs from the frozen commit")

    mismatches: list[dict[str, str]] = []
    file_entries = committed["files"]
    entries = (
        file_entries.items()
        if isinstance(file_entries, dict)
        else ((item["path"], item["sha256"]) for item in file_entries)
    )
    for relative_path, expected in entries:
        path = ROOT / relative_path
        actual = sha256_bytes(path.read_bytes()) if path.is_file() else "<missing>"
        if actual != expected:
            mismatches.append(
                {"path": relative_path, "expected": expected, "actual": actual}
            )
    if mismatches:
        raise RuntimeError(f"frozen file identity failure: {mismatches}")

    bound_record = committed["step_injection_bound"]
    frozen_p99 = float(
        bound_record.get("p99_single_slice_change", bound_record.get("value"))
    )
    if round(frozen_p99, 6) != P99_BOUND_REPORTED:
        raise RuntimeError(
            f"frozen p99 mismatch: manifest={frozen_p99}, challenge={P99_BOUND_REPORTED}"
        )
    return {
        "commit": FREEZE_COMMIT,
        "manifest_path": relative_manifest,
        "manifest_sha256": sha256_bytes(committed_bytes),
        "verified_file_count": len(committed["files"]),
        "frozen_p99_exact": frozen_p99,
        "frozen_p99_reported": P99_BOUND_REPORTED,
        "status": "PASS",
    }


def stable_rng(seed: int, component: str) -> np.random.Generator:
    digest = hashlib.sha256(f"{CHALLENGE}|{seed}|{component}".encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "big"))


def bernoulli(seed: int, component: str, probability: float) -> int:
    return int(stable_rng(seed, component).random() < probability)


def categorical_observation(
    seed: int, component: str, state: int, match_probability: float
) -> int:
    return state if bernoulli(seed, component, match_probability) else 1 - state


@dataclass(frozen=True)
class Schedule:
    seed: int
    length: int
    acute_count: int
    control_level: int
    action_dependence: float
    low_control_fraction: float
    chronic_profile: str
    acute_mask: np.ndarray
    chronic_mask: np.ndarray
    controllability_mask: np.ndarray
    acute_widths: tuple[int, ...]

    @property
    def event_mask(self) -> np.ndarray:
        return self.acute_mask | self.chronic_mask

    @property
    def scheduled_dose(self) -> float:
        return float(np.mean(self.event_mask))


def _place_interval(mask: np.ndarray, center: int, width: int) -> None:
    start = center - (width - 1) // 2
    start = max(0, min(start, len(mask) - width))
    mask[start : start + width] = True


def make_schedule(seed: int, acute_count: int, control_level: int) -> Schedule:
    rng = stable_rng(seed, "schedule")
    length = int(rng.choice((60, 90, 120)))
    chronic_profile = str(rng.choice(PROFILE_NAMES))
    acute_mask = np.zeros(length, dtype=bool)
    chronic_mask = np.zeros(length, dtype=bool)
    widths: list[int] = []

    if acute_count:
        middle = np.arange(math.ceil(0.20 * length), math.floor(0.80 * length))
        if acute_count == 1:
            centers = [int(rng.choice(middle))]
        else:
            split = len(middle) // 2
            centers = [
                int(rng.choice(middle[:split])),
                int(rng.choice(middle[split:])),
            ]
        for index, center in enumerate(centers):
            width = int(rng.choice((1, 2, 3)))
            widths.append(width)
            _place_interval(acute_mask, center, width)

    available = np.flatnonzero(~acute_mask)
    if chronic_profile == "steady-low":
        target = max(1, int(round(0.08 * length)))
        proposed = np.linspace(2, length - 3, target, dtype=int)
        for position in proposed:
            if not acute_mask[position]:
                chronic_mask[position] = True
        shortfall = target - int(chronic_mask.sum())
        if shortfall:
            candidates = available[~chronic_mask[available]]
            chosen = rng.choice(candidates, size=shortfall, replace=False)
            chronic_mask[chosen] = True
    elif chronic_profile == "bursty-moderate":
        target = max(2, int(round(0.18 * length)))
        allocations = (target // 2, target - target // 2)
        centers = (
            int(rng.integers(max(3, length // 8), max(4, length // 2))),
            int(rng.integers(length // 2, min(length - 3, 7 * length // 8))),
        )
        for center, allocation in zip(centers, allocations):
            radius = allocation + 2
            candidates = [
                p
                for p in range(max(0, center - radius), min(length, center + radius + 1))
                if not acute_mask[p] and not chronic_mask[p]
            ]
            candidates.sort(key=lambda p: (abs(p - center), p))
            chronic_mask[candidates[:allocation]] = True
        shortfall = target - int(chronic_mask.sum())
        if shortfall:
            candidates = available[~chronic_mask[available]]
            chosen = rng.choice(candidates, size=shortfall, replace=False)
            chronic_mask[chosen] = True

    event_positions = np.flatnonzero(acute_mask | chronic_mask)
    low_fraction = LOW_CONTROL_FRACTIONS[control_level - 1]
    low_count = round(low_fraction * len(event_positions))
    control_order = stable_rng(seed, "controllability-order").permutation(
        len(event_positions)
    )
    low_positions = {
        int(event_positions[int(index)]) for index in control_order[:low_count]
    }
    controllability_mask = np.ones(length, dtype=bool)
    for position in low_positions:
        controllability_mask[position] = False

    return Schedule(
        seed=seed,
        length=length,
        acute_count=acute_count,
        control_level=control_level,
        action_dependence=CONTROL_LEVELS[control_level - 1],
        low_control_fraction=low_fraction,
        chronic_profile=chronic_profile,
        acute_mask=acute_mask,
        chronic_mask=chronic_mask,
        controllability_mask=controllability_mask,
        acute_widths=tuple(widths),
    )


def transition_probability(
    previous_world: int,
    action: int,
    controllability: int,
    event_context: bool,
) -> float:
    if previous_world:
        low = float(V23_PARAMETERS["low_control_threat"])
        high = float(
            V23_PARAMETERS["high_control_avoid_threat"]
            if action
            else 1.0 - V23_PARAMETERS["high_control_engage_recovery"]
        )
    else:
        low = 0.35
        high = 0.55 if action else 0.10

    if event_context:
        precision = float(PARAMETERS["controllability_evidence_precision"])
        midpoint = 0.5 * (low + high)
        low = float(np.clip(midpoint + precision * (low - midpoint), 0.01, 0.99))
        high = float(np.clip(midpoint + precision * (high - midpoint), 0.01, 0.99))
    return high if controllability else low


def initial_priors() -> dict[str, np.ndarray]:
    return {
        "H": np.asarray(INITIAL_STRUCTURE_PRIOR, dtype=float).copy(),
        "G": np.asarray(ROOT_PRIOR, dtype=float).copy(),
        "C": np.asarray(CONTROL_PRIOR, dtype=float).copy(),
        "R": np.asarray(BROADCAST_PRIOR, dtype=float).copy(),
        "W": np.asarray(WORLD_PRIOR, dtype=float).copy(),
    }


def event_observations(
    seed: int,
    time: int,
    event: int,
    overwhelm: int,
    broadcast: int,
    prefix: str,
) -> dict[str, int]:
    factor = precision_categorical("E", "K", "B", EVENT_BASE, EVENT_PRECISION)
    event_match = float(factor.values[event, overwhelm, event])
    context_match = (
        float(V23_PARAMETERS["context_now_transient"])
        if event and broadcast
        else 0.5
    )
    return {
        "B": categorical_observation(
            seed, f"{prefix}:event:{time}", event, event_match
        ),
        "X": categorical_observation(
            seed, f"{prefix}:context:{time}", event, context_match
        ),
        "Q": categorical_observation(
            seed,
            f"{prefix}:monitor:{time}",
            broadcast,
            float(REFLEXIVE_MONITOR_RELIABILITY),
        ),
    }


def run_arm(schedule: Schedule, avoidance_available: bool) -> dict[str, object]:
    priors = initial_priors()
    policy_counts = np.tile(np.asarray(POLICY_PRIOR, dtype=float), (2, 1))
    previous_world = 0
    first_event = int(np.flatnonzero(schedule.event_mask)[0]) if schedule.event_mask.any() else schedule.length
    traces: list[dict[str, object]] = []

    for time in range(schedule.length):
        planned_acute = bool(schedule.acute_mask[time])
        planned_chronic = bool(schedule.chronic_mask[time])
        planned_event = int(planned_acute or planned_chronic)
        planned_overwhelm = int(planned_acute)
        planned_broadcast = 0 if planned_acute else 1

        may_act = avoidance_available and time > first_event
        if may_act:
            policy_obs = event_observations(
                schedule.seed,
                time,
                planned_event,
                planned_overwhelm,
                planned_broadcast,
                "shared",
            )
            policy_posterior = infer_policy(
                priors=priors,
                overwhelm=planned_overwhelm,
                observations=policy_obs,
            )
            action = bernoulli(
                schedule.seed,
                f"shared:policy_action:{time}",
                float(policy_posterior[1]),
            )
        else:
            action = 0
            policy_posterior = np.array([1.0, 0.0])

        avoided_encounter = bool(
            planned_chronic
            and may_act
            and action
            and bernoulli(
                schedule.seed, f"shared:avoidance_filter:{time}", AVOIDANCE_REDUCTION
            )
        )
        actual_event = int(planned_event and not avoided_encounter)
        actual_overwhelm = int(planned_acute)
        actual_broadcast = 0 if planned_acute else 1

        probability_threat = transition_probability(
            previous_world,
            action,
            int(schedule.controllability_mask[time]),
            bool(actual_event),
        )
        world = bernoulli(
            schedule.seed, f"shared:world_transition:{time}", probability_threat
        )
        outcome_match = float(V23_PARAMETERS["outcome_observation_reliability"])
        outcome = categorical_observation(
            schedule.seed,
            f"shared:outcome:{time}",
            world,
            outcome_match,
        )
        observations = event_observations(
            schedule.seed,
            time,
            actual_event,
            actual_overwhelm,
            actual_broadcast,
            "shared",
        )
        observations.update({"A": action, "O": outcome})

        state = infer_slice(
            priors=priors,
            consequence_alpha=policy_counts,
            overwhelm=actual_overwhelm,
            real_danger=False,
            observations=observations,
            action_intervention=not may_act,
        )
        priors = {
            name: np.asarray(state.posterior_store[name], dtype=float).copy()
            for name in ("H", "G", "C", "R", "W")
        }
        policy_counts[action] = dirichlet_update(
            policy_counts[action],
            np.array(
                [
                    float(outcome == 1),
                    float(outcome == 0),
                ]
            ),
        )
        conditional = np.asarray(
            [
                state.evidence_store["transient_conditional"],
                state.evidence_store["persistent_conditional"],
            ],
            dtype=float,
        )
        log_bayes_factor = float(
            math.log(max(conditional[1], 1e-300))
            - math.log(max(conditional[0], 1e-300))
        )
        traces.append(
            {
                "time": time,
                "planned_event": planned_event,
                "actual_event": actual_event,
                "acute": int(planned_acute),
                "overwhelm": actual_overwhelm,
                "broadcast": actual_broadcast,
                "action": action,
                "avoided_encounter": int(avoided_encounter),
                "previous_world": previous_world,
                "world": world,
                "H": float(state.posterior_store["H"][1]),
                "C": float(state.posterior_store["C"][1]),
                "log_bayes_factor": log_bayes_factor,
            }
        )
        previous_world = world

    h = np.asarray([float(t["H"]) for t in traces])
    changes = np.abs(np.diff(np.r_[float(INITIAL_STRUCTURE_PRIOR[1]), h]))
    actions = np.asarray([int(t["action"]) for t in traces])
    previous = np.asarray([int(t["previous_world"]) for t in traces])
    worlds = np.asarray([int(t["world"]) for t in traces])
    mediator = float(np.mean((actions == 1) & (previous == 1) & (worlds == 1)))
    margin = float(sum(float(t["log_bayes_factor"]) for t in traces))
    return {
        "formation_margin": margin,
        "formed": int(margin >= FORMATION_MARGIN),
        "final_persistent_probability": float(h[-1]),
        "max_step_change": float(changes.max(initial=0.0)),
        "step_changes": changes,
        "acute_mask": schedule.acute_mask.copy(),
        "realized_avoidance_mediator": mediator,
        "avoidance_rate": float(actions.mean()),
        "realized_event_fraction": float(
            np.mean([int(t["actual_event"]) for t in traces])
        ),
        "traces": traces,
    }


def normal_interval(values: np.ndarray) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if values.size < 2:
        return (float("nan"), float("nan"))
    mean = float(values.mean())
    se = float(values.std(ddof=1) / math.sqrt(values.size))
    return mean - 1.96 * se, mean + 1.96 * se


def wilson_interval(successes: int, total: int) -> tuple[float, float]:
    if total == 0:
        return (float("nan"), float("nan"))
    z = 1.96
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = (
        z
        * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))
        / denominator
    )
    return center - radius, center + radius


def correlation_interval(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 4 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan"), float("nan"), float("nan")
    r = float(np.corrcoef(x, y)[0, 1])
    clipped = float(np.clip(r, -0.999999, 0.999999))
    fisher = math.atanh(clipped)
    radius = 1.96 / math.sqrt(len(x) - 3)
    return r, math.tanh(fisher - radius), math.tanh(fisher + radius)


def partial_correlation_interval(
    outcome: np.ndarray, predictor: np.ndarray, control: np.ndarray
) -> tuple[float, float, float]:
    design = np.column_stack([np.ones(len(control)), control])
    outcome_residual = outcome - design @ np.linalg.lstsq(
        design, outcome, rcond=None
    )[0]
    predictor_residual = predictor - design @ np.linalg.lstsq(
        design, predictor, rcond=None
    )[0]
    return correlation_interval(outcome_residual, predictor_residual)


def isotonic_decreasing(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    blocks: list[list[float]] = []
    for index, (value, weight) in enumerate(zip(values, weights)):
        blocks.append([float(index), float(index), float(-value), float(weight)])
        while len(blocks) >= 2 and blocks[-2][2] > blocks[-1][2]:
            right = blocks.pop()
            left = blocks.pop()
            total_weight = left[3] + right[3]
            blocks.append(
                [
                    left[0],
                    right[1],
                    (left[2] * left[3] + right[2] * right[3]) / total_weight,
                    total_weight,
                ]
            )
    fitted = np.empty(len(values), dtype=float)
    for start, end, value, _weight in blocks:
        fitted[int(start) : int(end) + 1] = -value
    return fitted


def isotonic_statistic(pair_values: np.ndarray) -> tuple[float, np.ndarray]:
    means = pair_values.reshape(5, WORLDS_PER_CELL).mean(axis=1)
    weights = np.full(5, WORLDS_PER_CELL, dtype=float)
    fitted = isotonic_decreasing(means, weights)
    pooled = float(pair_values.mean())
    statistic = float(np.sum(weights * (fitted - pooled) ** 2))
    return statistic, fitted


def isotonic_permutation_test(pair_values: np.ndarray) -> dict[str, object]:
    observed, fitted = isotonic_statistic(pair_values)
    rng = stable_rng(FIRST_SEED, "isotonic-permutation-analysis")
    exceedances = 0
    repetitions = 9999
    for _ in range(repetitions):
        shuffled = rng.permutation(pair_values)
        statistic, _ = isotonic_statistic(shuffled)
        exceedances += int(statistic >= observed - 1e-15)
    p_value = (exceedances + 1) / (repetitions + 1)
    return {
        "statistic": observed,
        "permutations": repetitions,
        "p_value": p_value,
        "fitted_rates": fitted.tolist(),
    }


def rate_summary(values: list[int]) -> dict[str, object]:
    successes = int(sum(values))
    total = len(values)
    low, high = wilson_interval(successes, total)
    return {
        "successes": successes,
        "n": total,
        "rate": successes / total if total else None,
        "ci95": [low, high],
    }


def json_safe(value: object) -> object:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, np.ndarray):
        return [json_safe(v) for v in value.tolist()]
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    return value


def main() -> int:
    identity = verify_freeze_identity()
    frozen_p99 = float(identity["frozen_p99_exact"])
    seeds = list(range(FIRST_SEED, FIRST_SEED + BASE_WORLD_COUNT))
    if seeds[-1] > LAST_RELEASED_SEED:
        raise RuntimeError("challenge attempted to use a seed outside the released block")

    records: list[dict[str, object]] = []
    full: list[dict[str, object]] = []
    for offset, seed in enumerate(seeds):
        combination = offset // WORLDS_PER_CELL
        acute_count = combination // 5
        control_level = combination % 5 + 1
        schedule = make_schedule(seed, acute_count, control_level)
        available = run_arm(schedule, True)
        replay = run_arm(schedule, False)
        full.append(
            {
                "seed": seed,
                "schedule": schedule,
                "available": available,
                "replay": replay,
            }
        )
        record: dict[str, object] = {
            "seed": seed,
            "length": schedule.length,
            "acute_count": acute_count,
            "acute_widths": "|".join(str(v) for v in schedule.acute_widths),
            "control_level": control_level,
            "action_dependence": schedule.action_dependence,
            "low_control_fraction": schedule.low_control_fraction,
            "chronic_profile": schedule.chronic_profile,
            "scheduled_dose": schedule.scheduled_dose,
        }
        for name, arm in (("available", available), ("replay", replay)):
            for field in (
                "formation_margin",
                "formed",
                "final_persistent_probability",
                "max_step_change",
                "realized_avoidance_mediator",
                "avoidance_rate",
                "realized_event_fraction",
            ):
                record[f"{name}_{field}"] = arm[field]
        records.append(record)

    # Test 1: the isotonic shape test uses paired-arm averages, while the
    # preregistered anchor rates count all 16 trajectories per control level.
    one_acute = [item for item in full if item["schedule"].acute_count == 1]
    pair_values = np.asarray(
        [
            0.5 * (item["available"]["formed"] + item["replay"]["formed"])
            for item in sorted(
                one_acute,
                key=lambda item: (
                    item["schedule"].control_level,
                    item["seed"],
                ),
            )
        ],
        dtype=float,
    )
    trend = isotonic_permutation_test(pair_values)
    raw_curve: list[dict[str, object]] = []
    for level in range(1, 6):
        values: list[int] = []
        for item in one_acute:
            if item["schedule"].control_level == level:
                values.extend(
                    [item["available"]["formed"], item["replay"]["formed"]]
                )
        summary = rate_summary(values)
        summary["control_level"] = level
        summary["action_dependence"] = CONTROL_LEVELS[level - 1]
        raw_curve.append(summary)
    fitted = np.asarray(trend["fitted_rates"], dtype=float)
    shape_pass = bool(
        trend["p_value"] <= 0.05
        and fitted[0] > fitted[-1]
        and np.all(np.diff(fitted) <= 1e-12)
    )
    level_one_pass = bool(raw_curve[0]["rate"] >= 0.60)
    level_five_pass = bool(raw_curve[4]["rate"] <= 0.15)
    chronic_values: list[int] = []
    for item in full:
        schedule = item["schedule"]
        if (
            schedule.acute_count == 0
            and schedule.control_level == 1
            and schedule.chronic_profile == "bursty-moderate"
        ):
            chronic_values.extend(
                [item["available"]["formed"], item["replay"]["formed"]]
            )
    chronic_anchor = rate_summary(chronic_values)
    chronic_pass = bool(
        chronic_anchor["n"] and chronic_anchor["rate"] >= 0.25
    )
    test_one_pass = shape_pass and level_one_pass and level_five_pass and chronic_pass
    test_one = {
        "name": "formation dose-response",
        "pass": test_one_pass,
        "shape": {
            "pass": shape_pass,
            "raw_curve": raw_curve,
            "isotonic": trend,
            "criterion": "permutation p <= 0.05, non-increasing fit, strict endpoint decline",
        },
        "calibration": {
            "pass": level_one_pass and level_five_pass and chronic_pass,
            "one_acute_level_1_at_least_0_60": level_one_pass,
            "one_acute_level_5_at_most_0_15": level_five_pass,
            "chronic_only_bursty_no_control_at_least_0_25": chronic_pass,
            "chronic_only_bursty_no_control": chronic_anchor,
        },
    }

    # Test 2: empty schedules must remain at floor at every level.
    floor_levels: list[dict[str, object]] = []
    floor_pass = True
    for level in range(1, 6):
        values = []
        for item in full:
            schedule = item["schedule"]
            if (
                schedule.acute_count == 0
                and schedule.control_level == level
                and schedule.chronic_profile == "none"
            ):
                values.extend(
                    [item["available"]["formed"], item["replay"]["formed"]]
                )
        result = rate_summary(values)
        result["control_level"] = level
        level_pass = bool(result["n"] and result["rate"] <= 0.05)
        result["pass"] = level_pass
        floor_pass = floor_pass and level_pass
        floor_levels.append(result)
    test_two = {
        "name": "no-event floor",
        "pass": floor_pass,
        "criterion": "formation rate <= 0.05 at every controllability level",
        "levels": floor_levels,
    }

    # Test 3: exceedance denominator is every acute-event slice in all 240
    # trajectories.  The hard maximum is checked over every slice.
    acute_changes: list[float] = []
    all_changes: list[float] = []
    for item in full:
        for arm_name in ("available", "replay"):
            arm = item[arm_name]
            changes = np.asarray(arm["step_changes"], dtype=float)
            all_changes.extend(changes.tolist())
            acute_changes.extend(changes[np.asarray(arm["acute_mask"], dtype=bool)].tolist())
    acute_array = np.asarray(acute_changes, dtype=float)
    all_array = np.asarray(all_changes, dtype=float)
    exceedances = int(np.sum(acute_array > frozen_p99))
    exceedance_rate = (
        exceedances / len(acute_array) if len(acute_array) else float("nan")
    )
    hard_limit = MAX_MULTIPLIER * frozen_p99
    max_change = float(all_array.max(initial=0.0))
    test_three = {
        "name": "continuity",
        "pass": bool(
            exceedance_rate <= EXCEEDANCE_RATE_LIMIT and max_change <= hard_limit
        ),
        "frozen_p99_bound": frozen_p99,
        "challenge_multiplier": MAX_MULTIPLIER,
        "hard_maximum": hard_limit,
        "acute_slice_count": len(acute_array),
        "acute_exceedance_count": exceedances,
        "acute_exceedance_rate": exceedance_rate,
        "acute_exceedance_rate_limit": EXCEEDANCE_RATE_LIMIT,
        "maximum_all_slice_change": max_change,
        "maximum_acute_slice_change": float(acute_array.max(initial=0.0)),
    }

    # Test 4: selection is made using replay formation, before examining the
    # available-arm outcome.  The mediator contains realized action and world
    # transitions only, exactly as in C-V23.
    selected = [
        item
        for item in full
        if item["schedule"].control_level <= 2 and item["replay"]["formed"]
    ]
    paired_effects = np.asarray(
        [
            item["available"]["formation_margin"]
            - item["replay"]["formation_margin"]
            for item in selected
        ],
        dtype=float,
    )
    advantage_ci = normal_interval(paired_effects)
    end_values: list[float] = []
    mediators: list[float] = []
    doses: list[float] = []
    for item in selected:
        for arm_name in ("available", "replay"):
            arm = item[arm_name]
            end_values.append(float(arm["final_persistent_probability"]))
            mediators.append(float(arm["realized_avoidance_mediator"]))
            doses.append(float(item["schedule"].scheduled_dose))
    mediator_corr = correlation_interval(
        np.asarray(end_values), np.asarray(mediators)
    )
    dose_partial = partial_correlation_interval(
        np.asarray(end_values), np.asarray(doses), np.asarray(mediators)
    )
    enough_worlds = len(selected) >= 40
    advantage_effect_pass = bool(
        len(paired_effects) >= 2 and advantage_ci[0] > 0
    )
    advantage_pass = enough_worlds and advantage_effect_pass
    mediation_pass = bool(
        math.isfinite(mediator_corr[1])
        and mediator_corr[1] > 0
        and math.isfinite(dose_partial[1])
        and dose_partial[1] <= 0 <= dose_partial[2]
    )
    test_four = {
        "name": "persistence advantage and realized mediation",
        "pass": advantage_pass and mediation_pass,
        "formed_low_control_pair_count": len(selected),
        "expected_minimum_pair_count": 40,
        "paired_persistence_advantage": {
            "readout": "available-minus-replay end persistent evidence margin",
            "mean": float(paired_effects.mean()) if len(paired_effects) else None,
            "ci95": list(advantage_ci),
            "pass": advantage_effect_pass,
        },
        "realized_avoidance_correlation": {
            "r": mediator_corr[0],
            "ci95": [mediator_corr[1], mediator_corr[2]],
            "pass": bool(math.isfinite(mediator_corr[1]) and mediator_corr[1] > 0),
        },
        "scheduled_dose_partial_correlation": {
            "r": dose_partial[0],
            "ci95": [dose_partial[1], dose_partial[2]],
            "pass": bool(
                math.isfinite(dose_partial[1])
                and dose_partial[1] <= 0 <= dose_partial[2]
            ),
        },
        "mediator_definition": "mean(A_t=avoid and W_(t-1)=threat and W_t=threat)",
    }

    tests = [test_one, test_two, test_three, test_four]
    failures: list[str] = []
    if not shape_pass:
        failures.append(
            "Test 1 shape failure: formation probability did not show the preregistered monotone isotonic decline across the five controllability levels."
        )
    if not level_one_pass:
        failures.append(
            "Test 1 calibration failure: the level-1 no-control formation rate in one-acute worlds was below 0.60."
        )
    if not level_five_pass:
        failures.append(
            "Test 1 calibration failure: the level-5 strongly action-dependent formation rate in one-acute worlds exceeded 0.15."
        )
    if not chronic_pass:
        failures.append(
            "Test 1 calibration failure: the chronic-only bursty no-control formation rate was below 0.25."
        )
    if not test_two["pass"]:
        failures.append(
            "Test 2 failure: at least one controllability level exceeded the 0.05 formation floor in zero-acute, no-chronic worlds."
        )
    if not test_three["pass"]:
        failures.append(
            "Test 3 failure: the acute-slice p99 exceedance rate exceeded 1.5% or a single-slice posterior change exceeded 1.75 times the frozen V2.3.1 p99 bound."
        )
    if not enough_worlds:
        failures.append(
            "Test 4 localization failure: fewer than 40 matched low-control pairs formed in the replay arm."
        )
    if not advantage_effect_pass:
        failures.append(
            "Test 4 failure: the paired 95% interval for the avoidance-available persistence advantage did not exclude zero."
        )
    if not mediation_pass:
        failures.append(
            "Test 4 failure: end-state persistence did not track realized avoidance with a positive 95% interval while scheduled dose vanished after conditioning on that mediator."
        )

    verdict = "PASS" if all(bool(test["pass"]) for test in tests) else "FAIL"
    summary = {
        "challenge": CHALLENGE,
        "verdict": verdict,
        "identity": identity,
        "protocol": {
            "released_seed_block": [FIRST_SEED, LAST_RELEASED_SEED],
            "used_seed_block": [seeds[0], seeds[-1]],
            "base_worlds": BASE_WORLD_COUNT,
            "trajectories": TRAJECTORY_COUNT,
            "paired_arms": ["avoidance_available", "matched_replay"],
            "lengths": [60, 90, 120],
            "acute_counts": [0, 1, 2],
            "control_action_dependence": list(CONTROL_LEVELS),
            "event_slice_low_control_fractions": list(LOW_CONTROL_FRACTIONS),
            "chronic_profiles": list(PROFILE_NAMES),
            "acute_intensity_band_slices": [1, 2, 3],
            "avoidance_filter_probability": AVOIDANCE_REDUCTION,
        },
        "tests": tests,
        "failures_verbatim": failures,
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    with (RESULT_DIR / "per_seed.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    (RESULT_DIR / "summary.json").write_text(canonical_json(json_safe(summary)))
    write_report(summary)
    write_milestone_update(summary)
    write_addendum(summary)
    print(canonical_json(json_safe({"challenge": CHALLENGE, "verdict": verdict, "failures": failures})))
    return 0 if verdict == "PASS" else 1


def fmt(value: object, digits: int = 4) -> str:
    if value is None:
        return "NA"
    return f"{float(value):.{digits}f}"


def write_report(summary: dict[str, object]) -> None:
    one, two, three, four = summary["tests"]
    curve = one["shape"]["raw_curve"]
    fitted = one["shape"]["isotonic"]["fitted_rates"]
    failures = summary["failures_verbatim"]
    failure_text = "\n".join(f"- {failure}" for failure in failures) or "- None."
    lines = [
        "# C-V23b formation challenge report",
        "",
        f"Verdict: **{summary['verdict']}**.",
        "",
        "The runner verified every file in the V2.3.1 freeze manifest against commit "
        f"`{FREEZE_COMMIT}` before inference. It used seeds `{FIRST_SEED}:{FIRST_SEED + BASE_WORLD_COUNT - 1}`: "
        f"120 paired base worlds and {TRAJECTORY_COUNT} arm trajectories. No frozen engine, stage, contract, parameter, or result file was changed.",
        "",
        "## Test 1 — formation dose-response",
        "",
        "| Control level | Action dependence | Formed / n | Rate | 95% Wilson interval | Isotonic fit |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for index, item in enumerate(curve):
        lines.append(
            f"| {item['control_level']} | {fmt(item['action_dependence'], 2)} | "
            f"{item['successes']} / {item['n']} | {fmt(item['rate'])} | "
            f"[{fmt(item['ci95'][0])}, {fmt(item['ci95'][1])}] | {fmt(fitted[index])} |"
        )
    chronic = one["calibration"]["chronic_only_bursty_no_control"]
    lines.extend(
        [
            "",
            f"Shape verdict: **{'PASS' if one['shape']['pass'] else 'FAIL'}** "
            f"(isotonic permutation p = {fmt(one['shape']['isotonic']['p_value'])}).",
            "",
            f"Calibration verdict: **{'PASS' if one['calibration']['pass'] else 'FAIL'}**. "
            f"The chronic-only bursty/no-control anchor was {chronic['successes']}/{chronic['n']} "
            f"= {fmt(chronic['rate'])}, 95% Wilson interval "
            f"[{fmt(chronic['ci95'][0])}, {fmt(chronic['ci95'][1])}].",
            "",
            "The shape and calibration conclusions above are intentionally separate: a monotone curve does not rescue a missed absolute anchor.",
            "",
            "## Test 2 — no-event floor",
            "",
            "| Control level | Formed / n | Rate | 95% Wilson interval | Verdict |",
            "|---:|---:|---:|---:|---:|",
        ]
    )
    for item in two["levels"]:
        lines.append(
            f"| {item['control_level']} | {item['successes']} / {item['n']} | "
            f"{fmt(item['rate'])} | [{fmt(item['ci95'][0])}, {fmt(item['ci95'][1])}] | "
            f"{'PASS' if item['pass'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            f"Test 2 verdict: **{'PASS' if two['pass'] else 'FAIL'}**.",
            "",
            "## Test 3 — continuity",
            "",
            f"The exact frozen p99 bound was `{three['frozen_p99_bound']:.12f}` "
            f"(reported freeze value `{P99_BOUND_REPORTED}`); the challenge hard maximum was "
            f"`1.75 × p99 = {three['hard_maximum']:.12f}`. "
            f"{three['acute_exceedance_count']}/{three['acute_slice_count']} acute slices exceeded p99 "
            f"({fmt(three['acute_exceedance_rate'], 6)}; limit {EXCEEDANCE_RATE_LIMIT:.3f}). "
            f"The maximum change over all slices was {three['maximum_all_slice_change']:.12f}.",
            "",
            f"Test 3 verdict: **{'PASS' if three['pass'] else 'FAIL'}**.",
            "",
            "## Test 4 — persistence and mediation",
            "",
            f"The replay arm selected {four['formed_low_control_pair_count']} formed low-control matched pairs "
            f"(required at least {four['expected_minimum_pair_count']}). The available-minus-replay end persistent-evidence-margin "
            f"effect was {fmt(four['paired_persistence_advantage']['mean'], 6)}, 95% paired interval "
            f"[{fmt(four['paired_persistence_advantage']['ci95'][0], 6)}, "
            f"{fmt(four['paired_persistence_advantage']['ci95'][1], 6)}].",
            "",
            f"End persistence versus the realized action/transition-only mediator: r = "
            f"{fmt(four['realized_avoidance_correlation']['r'], 4)}, 95% interval "
            f"[{fmt(four['realized_avoidance_correlation']['ci95'][0], 4)}, "
            f"{fmt(four['realized_avoidance_correlation']['ci95'][1], 4)}]. "
            f"Scheduled dose after conditioning on the mediator: partial r = "
            f"{fmt(four['scheduled_dose_partial_correlation']['r'], 4)}, 95% interval "
            f"[{fmt(four['scheduled_dose_partial_correlation']['ci95'][0], 4)}, "
            f"{fmt(four['scheduled_dose_partial_correlation']['ci95'][1], 4)}].",
            "",
            f"Test 4 verdict: **{'PASS' if four['pass'] else 'FAIL'}**.",
            "",
            "## Retained failures",
            "",
            failure_text,
            "",
            "## Configuration localization",
            "",
            "The five-level gradient was compiled exactly as in V2.3.1's public open-generalization assay: a seed-paired fraction of event positions was assigned the public binary low-controllability state (fractions 1.00, 0.75, 0.50, 0.25, 0.00), and the remaining event positions were assigned high controllability. No continuous latent or interpolated transition table was added. Acute intensity was represented as a seed-drawn 1–3-slice event episode; acute centers were drawn in the middle 60% of each schedule. Steady-low and bursty-moderate chronic profiles were generated without reading run length or schedule shape inside the frozen model. Avoidance could remove chronic encounter evidence with the previously declared 0.82 probability, while acute events were not avoidable. The matched replay arm shared all exogenous random streams and engaged instead of avoiding.",
            "",
        ]
    )
    (RESULT_DIR / "report.md").write_text("\n".join(lines))


def write_addendum(summary: dict[str, object]) -> None:
    addendum_path = ROOT / "results" / "V2.3.1" / "gate6-addendum.json"
    result_files = [
        RESULT_DIR / "per_seed.csv",
        RESULT_DIR / "summary.json",
        RESULT_DIR / "report.md",
        ROOT / "results" / "milestone-2-v2.3.1-gate6-update.md",
    ]
    challenge_spec = (
        ROOT / "sealed-revealed" / "C-V23b-formation-challenge.md"
    )
    addendum = {
        "base_freeze_commit": FREEZE_COMMIT,
        "base_freeze_manifest": summary["identity"]["manifest_path"],
        "base_freeze_manifest_sha256": summary["identity"]["manifest_sha256"],
        "base_manifest_file_count_verified": summary["identity"][
            "verified_file_count"
        ],
        "base_manifest_mismatches": [],
        "challenge_runner_sha256": sha256_bytes(
            (ROOT / "challenges" / "run_c_v23b.py").read_bytes()
        ),
        "challenge_spec_sha256": sha256_bytes(challenge_spec.read_bytes()),
        "overlay": {
            "prospective_challenge": CHALLENGE,
            "prospective_challenge_revealed": True,
            "prospective_challenge_run": True,
            "sealed_gate_6_run": True,
            "verdict": summary["verdict"],
        },
        "result_hashes": {
            str(path.relative_to(ROOT)): sha256_bytes(path.read_bytes())
            for path in result_files
        },
        "strain": "V2.3.1",
    }
    addendum_path.write_text(canonical_json(json_safe(addendum)))


def write_milestone_update(summary: dict[str, object]) -> None:
    path = ROOT / "results" / "milestone-2-v2.3.1-gate6-update.md"
    failures = summary["failures_verbatim"]
    failure_text = "\n".join(f"- {failure}" for failure in failures) or "- None."
    text = f"""# Milestone update — V2.3.1 Gate 6

C-V23b verdict: **{summary['verdict']}**.

The challenge ran 120 paired base worlds (240 trajectories) using released seeds
`{FIRST_SEED}:{FIRST_SEED + BASE_WORLD_COUNT - 1}`. Before the run, the runner
verified all {summary['identity']['verified_file_count']} files named by the
V2.3.1 freeze manifest against commit `{FREEZE_COMMIT}`. The frozen p99
single-slice bound was `{summary['identity']['frozen_p99_exact']:.12f}`.

Test verdicts:

"""
    for test in summary["tests"]:
        text += f"- {test['name']}: **{'PASS' if test['pass'] else 'FAIL'}**\n"
    text += f"""

Retained failures:

{failure_text}

Full per-seed results, effect intervals, shape/calibration localization, and
continuity accounting are in `results/challenges/C-V23b/`.
"""
    path.write_text(text)


if __name__ == "__main__":
    raise SystemExit(main())
