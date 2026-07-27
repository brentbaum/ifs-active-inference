"""Run sealed challenge C-V23 against the frozen V2.3 strain."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np

V2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = V2_ROOT.parents[2]
if str(V2_ROOT) not in sys.path:
    sys.path.insert(0, str(V2_ROOT))

from ref.precision import precision_categorical  # noqa: E402
from ref.templates import dirichlet_update  # noqa: E402
from ref.v23 import (  # noqa: E402
    BROADCAST_PRIOR,
    CONTROL_PRIOR,
    EVENT_BASE,
    EVENT_PRECISION,
    PARAMETERS,
    POLICY_PRIOR,
    ROOT_PRIOR,
    STRUCTURE_PRIOR,
    WORLD_PRIOR,
    infer_policy,
    infer_slice,
)


CHALLENGE = "C-V23"
STAGE = "V2.3"
FROZEN_COMMIT = "dee94c5"
RELEASED_BLOCK = (807203, 807502)
WORLD_COUNT = 60
SLICE_COUNT = 80
ACUTE_RANGE = (30, 55)
CHRONIC_RATE_BAND = (0.08, 0.16)
AVOIDANCE_ENCOUNTER_REDUCTION = 0.82
FORMATION_MARGIN = 1.0
LOW_CONTROL_FORMATION_MINIMUM = 45
HIGH_CONTROL_FORMATION_MAXIMUM = 12
STEP_INJECTION_BOUND = 0.294529387
CELLS = (
    ("low_available", 0, True),
    ("low_unavailable", 0, False),
    ("high_available", 1, True),
    ("high_unavailable", 1, False),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_frozen_identity() -> dict[str, Any]:
    manifest_rel = "projects/emergence-suite/v2/results/V2.3/freeze-manifest.json"
    manifest_bytes = subprocess.check_output(
        ["git", "show", f"{FROZEN_COMMIT}:{manifest_rel}"],
        cwd=REPO_ROOT,
    )
    manifest = json.loads(manifest_bytes)
    mismatches = []
    for relative, expected in manifest["files"].items():
        path = V2_ROOT / relative
        actual = sha256(path) if path.exists() else None
        if actual != expected:
            mismatches.append(
                {"file": relative, "expected": expected, "actual": actual}
            )
    if mismatches:
        raise RuntimeError(f"{STAGE} frozen identity failure: {mismatches}")
    frozen_bound = float(manifest["step_injection_bound"]["value"])
    if not math.isclose(
        frozen_bound, STEP_INJECTION_BOUND, rel_tol=0.0, abs_tol=5.1e-10
    ):
        raise RuntimeError(
            f"step-injection bound mismatch: {frozen_bound} vs "
            f"{STEP_INJECTION_BOUND}"
        )
    return {
        "commit": FROZEN_COMMIT,
        "manifest": manifest_rel,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "manifest_file_count": len(manifest["files"]),
        "mismatches": mismatches,
        "frozen_step_injection_value": frozen_bound,
        "challenge_step_injection_bound": STEP_INJECTION_BOUND,
    }


def released_seeds() -> list[int]:
    start, end = RELEASED_BLOCK
    seeds = list(range(start, start + WORLD_COUNT))
    if seeds[-1] > end:
        raise ValueError("requested seeds exceed the released C-V23 block")
    return seeds


def escrow_rng(seed: int, component: str) -> np.random.Generator:
    if seed < RELEASED_BLOCK[0] or seed > RELEASED_BLOCK[1]:
        raise ValueError(f"seed {seed} is outside the released C-V23 block")
    digest = hashlib.sha256(f"{CHALLENGE}:{seed}:{component}".encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "big"))


def component_uniform(seed: int, component: str) -> float:
    return float(escrow_rng(seed, component).random())


def mean_interval(values: Iterable[float]) -> tuple[float, float, float]:
    array = np.asarray(list(values), dtype=float)
    mean = float(array.mean())
    if len(array) < 2:
        return mean, mean, mean
    half_width = 1.96 * float(array.std(ddof=1)) / np.sqrt(len(array))
    return mean, mean - half_width, mean + half_width


def proportion_interval(successes: int, total: int) -> tuple[float, float, float]:
    probability = successes / total
    denominator = 1.0 + 1.96**2 / total
    center = (probability + 1.96**2 / (2 * total)) / denominator
    half = (
        1.96
        * np.sqrt(
            probability * (1.0 - probability) / total
            + 1.96**2 / (4 * total**2)
        )
        / denominator
    )
    return float(probability), float(center - half), float(center + half)


def correlation_interval(
    values_x: Iterable[float],
    values_y: Iterable[float],
) -> tuple[float, float, float]:
    x = np.asarray(list(values_x), dtype=float)
    y = np.asarray(list(values_y), dtype=float)
    if len(x) != len(y) or len(x) < 4:
        return float("nan"), float("nan"), float("nan")
    if float(x.std()) == 0.0 or float(y.std()) == 0.0:
        return 0.0, -1.0, 1.0
    correlation = float(np.corrcoef(x, y)[0, 1])
    clipped = float(np.clip(correlation, -0.999999999999, 0.999999999999))
    transformed = np.arctanh(clipped)
    half_width = 1.96 / np.sqrt(len(x) - 3)
    return (
        correlation,
        float(np.tanh(transformed - half_width)),
        float(np.tanh(transformed + half_width)),
    )


def partial_correlation_interval(
    outcome: Iterable[float],
    dose: Iterable[float],
    mediator: Iterable[float],
) -> tuple[float, float, float]:
    y = np.asarray(list(outcome), dtype=float)
    x = np.asarray(list(dose), dtype=float)
    z = np.asarray(list(mediator), dtype=float)
    design = np.column_stack([np.ones(len(z)), z])
    residual_y = y - design @ np.linalg.lstsq(design, y, rcond=None)[0]
    residual_x = x - design @ np.linalg.lstsq(design, x, rcond=None)[0]
    interval = correlation_interval(residual_y, residual_x)
    if len(y) <= 4 or not np.isfinite(interval[0]):
        return interval
    correlation = float(np.clip(interval[0], -0.999999999999, 0.999999999999))
    transformed = np.arctanh(correlation)
    half_width = 1.96 / np.sqrt(len(y) - 4)
    return (
        interval[0],
        float(np.tanh(transformed - half_width)),
        float(np.tanh(transformed + half_width)),
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("cannot write empty per-seed output")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    def native(item: Any) -> Any:
        if isinstance(item, np.generic):
            return item.item()
        if isinstance(item, np.ndarray):
            return item.tolist()
        raise TypeError(f"cannot serialize {item.__class__.__name__}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=native) + "\n",
        encoding="utf-8",
    )


def sample_binary(seed: int, component: str, probability: float) -> int:
    return int(component_uniform(seed, component) < probability)


def generated_schedule(seed: int) -> dict[str, Any]:
    rate_rng = escrow_rng(seed, "chronic-rate")
    chronic_rate = float(rate_rng.uniform(*CHRONIC_RATE_BAND))
    acute_rng = escrow_rng(seed, "acute-slice")
    acute_slice = int(acute_rng.integers(ACUTE_RANGE[0], ACUTE_RANGE[1] + 1))
    opportunities = (
        escrow_rng(seed, "chronic-opportunities").random(SLICE_COUNT)
        < chronic_rate
    )
    opportunities[acute_slice] = False
    return {
        "chronic_rate": chronic_rate,
        "acute_slice": acute_slice,
        "opportunities": opportunities,
        "scheduled_dose": float(opportunities.mean()),
    }


def initial_priors() -> dict[str, np.ndarray]:
    return {
        "H": STRUCTURE_PRIOR.copy(),
        "G": ROOT_PRIOR.copy(),
        "C": CONTROL_PRIOR.copy(),
        "R": BROADCAST_PRIOR.copy(),
        "W": WORLD_PRIOR.copy(),
    }


def transition_threat_probability(
    previous_world: int,
    action: int,
    controllability: int,
) -> float:
    if controllability == 0:
        return float(
            PARAMETERS["low_control_threat"] if previous_world else 0.35
        )
    if action == 1:
        return float(
            PARAMETERS["high_control_avoid_threat"]
            if previous_world
            else 0.55
        )
    return float(
        1.0 - PARAMETERS["high_control_engage_recovery"]
        if previous_world
        else 0.10
    )


def event_observation(
    seed: int,
    time: int,
    event: int,
    overwhelm: int,
) -> int:
    factor = precision_categorical(
        "E", "K", "B", EVENT_BASE, EVENT_PRECISION
    )
    match_probability = float(factor.values[event, overwhelm, event])
    matched = sample_binary(
        seed, f"event-match-{time}", match_probability
    )
    return event if matched else 1 - event


def exogenous_observations(
    seed: int,
    time: int,
    event: int,
    overwhelm: int,
    broadcast: int,
) -> dict[str, int]:
    event_value = event_observation(seed, time, event, overwhelm)
    monitor_match = sample_binary(
        seed,
        f"broadcast-match-{time}",
        float(PARAMETERS["broadcast_monitor_reliability"]),
    )
    monitor_value = broadcast if monitor_match else 1 - broadcast
    context_probability = (
        float(PARAMETERS["context_now_transient"])
        if event == 1 and broadcast == 1
        else 0.5
    )
    context_value = sample_binary(
        seed, f"context-now-{time}", context_probability
    )
    return {"B": event_value, "Q": monitor_value, "X": context_value}


def run_cell(
    seed: int,
    schedule: dict[str, Any],
    controllability: int,
    avoidance_available: bool,
) -> dict[str, Any]:
    priors = initial_priors()
    consequence_alpha = np.tile(POLICY_PRIOR, (2, 1))
    previous_world = 0
    acute_slice = int(schedule["acute_slice"])
    opportunities = np.asarray(schedule["opportunities"], dtype=bool)
    traces: list[dict[str, Any]] = []
    log_bayes_factors = []
    actions = []
    worlds = []
    encounter_transitions = []
    avoided_transitions = []

    for time in range(SLICE_COUNT):
        acute = time == acute_slice
        opportunity = bool(opportunities[time])
        post_event_opportunity = opportunity and time > acute_slice
        overwhelm = int(acute)
        broadcast = 0 if acute else 1

        policy_event = int(acute or opportunity)
        policy_observations = exogenous_observations(
            seed, time, policy_event, overwhelm, broadcast
        )
        if avoidance_available and time > acute_slice:
            policy = infer_policy(
                priors=priors,
                overwhelm=overwhelm,
                observations=policy_observations,
            )
            action_probability = float(policy[1])
            action = sample_binary(
                seed, f"policy-uniform-{time}", action_probability
            )
            action_intervention = False
        else:
            action_probability = 0.0
            action = 0
            action_intervention = True

        avoided_encounter = (
            post_event_opportunity
            and avoidance_available
            and action == 1
            and sample_binary(
                seed,
                f"encounter-transition-{time}",
                AVOIDANCE_ENCOUNTER_REDUCTION,
            )
            == 1
        )
        encounter = bool(acute or (opportunity and not avoided_encounter))
        actual_event = int(encounter)
        observations = exogenous_observations(
            seed, time, actual_event, overwhelm, broadcast
        )

        threat_probability = transition_threat_probability(
            previous_world, action, controllability
        )
        world = sample_binary(
            seed, f"world-transition-{time}", threat_probability
        )
        outcome_match = sample_binary(
            seed,
            f"outcome-match-{time}",
            float(PARAMETERS["outcome_observation_reliability"]),
        )
        outcome_observation = world if outcome_match else 1 - world
        observations.update({"A": action, "O": outcome_observation})

        state = infer_slice(
            priors=priors,
            consequence_alpha=consequence_alpha,
            overwhelm=overwhelm,
            real_danger=False,
            observations=observations,
            action_intervention=action_intervention,
        )
        transient_evidence = float(
            state.evidence_store["transient_conditional"]
        )
        persistent_evidence = float(
            state.evidence_store["persistent_conditional"]
        )
        log_bayes_factors.append(
            math.log(persistent_evidence) - math.log(transient_evidence)
        )

        consequence_alpha[action] = dirichlet_update(
            consequence_alpha[action],
            np.array(
                [
                    float(outcome_observation == 1),
                    float(outcome_observation == 0),
                ]
            ),
        )
        priors = {
            name: state.posterior_store[name].copy()
            for name in ("H", "G", "C", "R", "W")
        }

        actions.append(action)
        worlds.append(world)
        encounter_transitions.append(int(post_event_opportunity and encounter))
        avoided_transitions.append(int(post_event_opportunity and avoided_encounter))
        traces.append(
            {
                "time": time,
                "persistent_probability": float(
                    state.posterior_store["H"][1]
                ),
                "evidence_margin": float(sum(log_bayes_factors)),
                "action": action,
                "world": world,
                "opportunity": int(opportunity),
                "encounter": int(encounter),
                "avoided_encounter": int(avoided_encounter),
                "event_observation": observations["B"],
                "context_observation": observations["X"],
                "outcome_observation": outcome_observation,
                "action_probability": action_probability,
            }
        )
        previous_world = world

    persistent = np.asarray(
        [trace["persistent_probability"] for trace in traces], dtype=float
    )
    steps = np.diff(np.concatenate([[STRUCTURE_PRIOR[1]], persistent]))
    post_opportunities = int(
        np.sum(opportunities[np.arange(SLICE_COUNT) > acute_slice])
    )
    denominator = max(post_opportunities, 1)
    actions_array = np.asarray(actions, dtype=int)
    worlds_array = np.asarray(worlds, dtype=int)
    previous_worlds = np.concatenate([[0], worlds_array[:-1]])
    realized_avoidance = float(
        np.mean(
            (actions_array == 1)
            & (previous_worlds == 1)
            & (worlds_array == 1)
        )
    )
    return {
        "traces": traces,
        "final_persistent_probability": float(persistent[-1]),
        "evidence_margin": float(sum(log_bayes_factors)),
        "formed": bool(sum(log_bayes_factors) >= FORMATION_MARGIN),
        "acute_change": float(steps[acute_slice]),
        "acute_absolute_change": float(abs(steps[acute_slice])),
        "maximum_step": float(np.max(np.abs(steps))),
        "post_event_opportunities": post_opportunities,
        "realized_encounter_rate": float(sum(encounter_transitions) / denominator),
        "avoided_encounter_rate": float(sum(avoided_transitions) / denominator),
        "avoidance_action_rate": float(
            actions_array[acute_slice + 1 :].mean()
        ),
        "realized_avoidance_mediator": realized_avoidance,
        "realized_avoidance_encounter_mediator": float(
            sum(avoided_transitions) / denominator
        ),
    }


def render_report(summary: dict[str, Any]) -> str:
    tests = summary["tests"]
    boundary = tests["joint_formation_boundary"]
    continuity = tests["continuity"]
    persistence = tests["active_persistence"]
    mediation = tests["mediation"]
    verdict = "PASS" if summary["passed"] else "FAIL"
    failures = "\n".join(f"- `{item}`" for item in summary["failure_localization"])
    if not failures:
        failures = "- No preregistered failure was triggered."
    return f"""# C-V23 Gate 6 report

Verdict: **{verdict}**

The runner checked all {summary['frozen_identity']['manifest_file_count']} frozen
V2.3 files against commit `{summary['frozen_identity']['commit']}` with zero
mismatches. It used seeds `{summary['seed_block_used'][0]}` through
`{summary['seed_block_used'][1]}` in all four cells, with 60 worlds per cell
and component streams paired within seed.

## Preregistered tests

1. **Joint formation boundary — {'PASS' if boundary['passed'] else 'FAIL'}.**
   Persistent evidence reached the `>= 1 nat` margin in
   `{boundary['low_control_formed_worlds']}/60` low-control worlds and
   `{boundary['high_control_formed_worlds']}/60` high-control worlds. The
   respective 95% Wilson intervals were
   `{boundary['low_control_formed_95_interval'][1]:.3f}`–
   `{boundary['low_control_formed_95_interval'][2]:.3f}` and
   `{boundary['high_control_formed_95_interval'][1]:.3f}`–
   `{boundary['high_control_formed_95_interval'][2]:.3f}`. This comparison
   uses the avoidance-unavailable replay cells, so controllability is the
   only cell difference.
2. **Continuity — {'PASS' if continuity['passed'] else 'FAIL'}.** Mean
   acute-slice posterior change was
   `{continuity['acute_change_95_interval'][0]:.6f}` (95% interval
   `{continuity['acute_change_95_interval'][1]:.6f}` to
   `{continuity['acute_change_95_interval'][2]:.6f}`). The largest acute
   single-slice change was `{continuity['maximum_acute_step']:.9f}`, against
   the frozen bound `{continuity['step_injection_bound']:.9f}`; there were
   `{continuity['acute_bound_exceedances']}` exceedances.
3. **Active persistence — {'PASS' if persistence['passed'] else 'FAIL'}.**
   Among `{persistence['formed_pair_count']}` low-control formed paired
   worlds, unavailable-minus-available realized disconfirming-context
   encounter rate was
   `{persistence['encounter_reduction_95_interval'][0]:.6f}` (95% interval
   `{persistence['encounter_reduction_95_interval'][1]:.6f}` to
   `{persistence['encounter_reduction_95_interval'][2]:.6f}`). The
   available-minus-replay end evidence margin was
   `{persistence['persistence_margin_effect_95_interval'][0]:.6f}` (95%
   interval `{persistence['persistence_margin_effect_95_interval'][1]:.6f}`
   to `{persistence['persistence_margin_effect_95_interval'][2]:.6f}`).
4. **Mediation — {'PASS' if mediation['passed'] else 'FAIL'}.** Across
   `{mediation['observation_count']}` formed-world arm observations, the
   correlation between end persistence and realized avoidance was
   `{mediation['avoidance_correlation_95_interval'][0]:.3f}` (95% interval
   `{mediation['avoidance_correlation_95_interval'][1]:.3f}` to
   `{mediation['avoidance_correlation_95_interval'][2]:.3f}`). The partial
   correlation with scheduled dose after conditioning on realized avoidance
   was `{mediation['dose_partial_correlation_95_interval'][0]:.3f}` (95%
   interval `{mediation['dose_partial_correlation_95_interval'][1]:.3f}` to
   `{mediation['dose_partial_correlation_95_interval'][2]:.3f}`).

The matched replay shares every seed-generated context opportunity and
component uniform. Availability changes only whether a realized policy filters
a post-event encounter; the unavailable arm exposes the paired opportunity.
The mediation readout uses realized actions and threat-maintaining world
transitions only. Neither formation status nor any threshold enters inference.

## Failure localization

{failures}

No frozen engine, stage, contract, parameter, result, tolerance, or manifest
file was modified.
"""


def render_milestone_update(summary: dict[str, Any]) -> str:
    verdict = "PASS" if summary["passed"] else "FAIL"
    boundary = summary["tests"]["joint_formation_boundary"]
    persistence = summary["tests"]["active_persistence"]
    return f"""# Suite v2 milestone 2 — V2.3 Gate 6 update

C-V23 verdict: **{verdict}**.

The evaluator-revealed challenge ran on the identity-verified V2.3 freeze at
commit `dee94c5`, using released seeds 807203–807262 in four paired 60-world
cells. Persistent comparison won in
`{boundary['low_control_formed_worlds']}/60` low-control and
`{boundary['high_control_formed_worlds']}/60` high-control replay worlds.
Among the `{persistence['formed_pair_count']}` low-control formed pairs, the
available-minus-replay end evidence-margin effect was
`{persistence['persistence_margin_effect_95_interval'][0]:.6f}`
(`{persistence['persistence_margin_effect_95_interval'][1]:.6f}`–
`{persistence['persistence_margin_effect_95_interval'][2]:.6f}`).
Full effects, intervals, continuity audit, mediation result, and any failure
localization are retained in `results/challenges/C-V23/`.

The frozen V2.3 milestone report and freeze manifest remain unchanged; this
file and the Gate 6 addendum are additive.
"""


def main() -> dict[str, Any]:
    identity = verify_frozen_identity()
    seeds = released_seeds()
    rows: list[dict[str, Any]] = []
    worlds: dict[int, dict[str, dict[str, Any]]] = {}

    for seed in seeds:
        schedule = generated_schedule(seed)
        cells = {}
        for name, controllability, available in CELLS:
            cells[name] = run_cell(
                seed,
                schedule,
                controllability=controllability,
                avoidance_available=available,
            )
        worlds[seed] = cells

        row: dict[str, Any] = {
            "seed": seed,
            "acute_slice": schedule["acute_slice"],
            "chronic_rate": schedule["chronic_rate"],
            "scheduled_dose": schedule["scheduled_dose"],
            "scheduled_opportunities": int(
                np.sum(schedule["opportunities"])
            ),
        }
        for name, _, _ in CELLS:
            result = cells[name]
            for field in (
                "final_persistent_probability",
                "evidence_margin",
                "formed",
                "acute_change",
                "acute_absolute_change",
                "maximum_step",
                "post_event_opportunities",
                "realized_encounter_rate",
                "avoided_encounter_rate",
                "avoidance_action_rate",
                "realized_avoidance_mediator",
                "realized_avoidance_encounter_mediator",
            ):
                value = result[field]
                row[f"{name}_{field}"] = int(value) if isinstance(value, bool) else value
        rows.append(row)

    low_formed = sum(
        worlds[seed]["low_unavailable"]["formed"] for seed in seeds
    )
    high_formed = sum(
        worlds[seed]["high_unavailable"]["formed"] for seed in seeds
    )
    low_interval = proportion_interval(low_formed, WORLD_COUNT)
    high_interval = proportion_interval(high_formed, WORLD_COUNT)
    boundary_pass = (
        low_formed >= LOW_CONTROL_FORMATION_MINIMUM
        and high_formed <= HIGH_CONTROL_FORMATION_MAXIMUM
    )

    acute_changes = [
        worlds[seed][name]["acute_change"]
        for seed in seeds
        for name, _, _ in CELLS
    ]
    acute_absolute = [
        worlds[seed][name]["acute_absolute_change"]
        for seed in seeds
        for name, _, _ in CELLS
    ]
    acute_interval = mean_interval(acute_changes)
    bound_exceedances = sum(
        value > STEP_INJECTION_BOUND for value in acute_absolute
    )
    continuity_pass = acute_interval[1] > 0.0 and bound_exceedances == 0

    formed_seeds = [
        seed for seed in seeds if worlds[seed]["low_unavailable"]["formed"]
    ]
    encounter_effects = [
        worlds[seed]["low_unavailable"]["realized_encounter_rate"]
        - worlds[seed]["low_available"]["realized_encounter_rate"]
        for seed in formed_seeds
    ]
    persistence_effects = [
        worlds[seed]["low_available"]["evidence_margin"]
        - worlds[seed]["low_unavailable"]["evidence_margin"]
        for seed in formed_seeds
    ]
    encounter_interval = mean_interval(encounter_effects)
    persistence_interval = mean_interval(persistence_effects)
    active_persistence_pass = (
        len(formed_seeds) > 0
        and encounter_interval[1] > 0.0
        and persistence_interval[1] > 0.0
    )

    mediation_outcomes = []
    mediation_values = []
    mediation_doses = []
    for seed in formed_seeds:
        schedule = generated_schedule(seed)
        for name in ("low_available", "low_unavailable"):
            mediation_outcomes.append(
                worlds[seed][name]["final_persistent_probability"]
            )
            mediation_values.append(
                worlds[seed][name]["realized_avoidance_mediator"]
            )
            mediation_doses.append(schedule["scheduled_dose"])
    avoidance_interval = correlation_interval(
        mediation_outcomes, mediation_values
    )
    dose_partial_interval = partial_correlation_interval(
        mediation_outcomes, mediation_doses, mediation_values
    )
    mediation_pass = (
        len(mediation_outcomes) >= 8
        and avoidance_interval[1] > 0.0
        and dose_partial_interval[1] <= 0.0 <= dose_partial_interval[2]
    )

    tests = {
        "joint_formation_boundary": {
            "passed": boundary_pass,
            "evidence_margin_threshold_nats": FORMATION_MARGIN,
            "low_control_formed_worlds": low_formed,
            "low_control_formed_95_interval": low_interval,
            "low_control_minimum": LOW_CONTROL_FORMATION_MINIMUM,
            "high_control_formed_worlds": high_formed,
            "high_control_formed_95_interval": high_interval,
            "high_control_maximum": HIGH_CONTROL_FORMATION_MAXIMUM,
            "primary_cells": [
                "low_unavailable",
                "high_unavailable",
            ],
        },
        "continuity": {
            "passed": continuity_pass,
            "acute_change_95_interval": acute_interval,
            "maximum_acute_step": max(acute_absolute),
            "acute_bound_exceedances": bound_exceedances,
            "trajectory_count": len(acute_changes),
            "step_injection_bound": STEP_INJECTION_BOUND,
            "frozen_unrounded_value": identity[
                "frozen_step_injection_value"
            ],
        },
        "active_persistence": {
            "passed": active_persistence_pass,
            "formed_pair_count": len(formed_seeds),
            "formation_selection_cell": "low_unavailable",
            "encounter_reduction_95_interval": encounter_interval,
            "persistence_margin_effect_95_interval": persistence_interval,
        },
        "mediation": {
            "passed": mediation_pass,
            "observation_count": len(mediation_outcomes),
            "avoidance_correlation_95_interval": avoidance_interval,
            "dose_partial_correlation_95_interval": dose_partial_interval,
            "mediator_definition": (
                "mean of realized A=avoid and W(previous)=threat and "
                "W(next)=threat indicators; actions and transitions only"
            ),
        },
    }
    passed = all(test["passed"] for test in tests.values())
    localization = []
    if not boundary_pass:
        localization.append(
            "Test 1: the sealed joint formation boundary was not met "
            "(persistent evidence margin >= 1 nat in >=45/60 low-control "
            "and <=12/60 high-control worlds)."
        )
    if not continuity_pass:
        localization.append(
            "Test 2: the acute-event persistent posterior did not rise with "
            "a 95% interval bounded above zero and no individual acute "
            "single-slice change above 0.294529387."
        )
    if not active_persistence_pass:
        localization.append(
            "Test 3: among low-control formed worlds, avoidance availability "
            "did not both reduce realized disconfirming-context encounters "
            "and increase the end persistent evidence margin with both paired "
            "95% intervals bounded away from zero."
        )
    if not mediation_pass:
        localization.append(
            "Test 4: end persistence did not correlate positively with "
            "realized avoidance, or scheduled dose retained a non-null "
            "partial correlation after conditioning on realized avoidance."
        )

    summary = {
        "challenge": CHALLENGE,
        "stage": STAGE,
        "seed_block_released": list(RELEASED_BLOCK),
        "seed_block_used": [seeds[0], seeds[-1]],
        "world_count_per_cell": WORLD_COUNT,
        "slice_count": SLICE_COUNT,
        "paired_streams": True,
        "frozen_identity": identity,
        "configuration": {
            "cells": [
                {
                    "name": name,
                    "controllability": controllability,
                    "avoidance_available": available,
                }
                for name, controllability, available in CELLS
            ],
            "acute_slice_range_inclusive": list(ACUTE_RANGE),
            "chronic_rate_band": list(CHRONIC_RATE_BAND),
            "avoidance_encounter_reduction": AVOIDANCE_ENCOUNTER_REDUCTION,
            "matched_replay": (
                "same seed-generated context opportunities and component "
                "uniforms; unavailable arm removes only the policy filter"
            ),
            "formation_predicate_consulted_by_inference": False,
            "step_injection_bound": STEP_INJECTION_BOUND,
        },
        "tests": tests,
        "failure_localization": localization,
        "passed": passed,
    }

    result_dir = V2_ROOT / "results" / "challenges" / CHALLENGE
    write_csv(result_dir / "per_seed.csv", rows)
    write_json(result_dir / "summary.json", summary)
    report_path = result_dir / "report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary), encoding="utf-8")

    milestone_path = V2_ROOT / "results" / "milestone-2-v2.3-gate6-update.md"
    milestone_path.write_text(render_milestone_update(summary), encoding="utf-8")

    sealed_path = V2_ROOT / "sealed-revealed" / "C-V23-formation-challenge.md"
    addendum = {
        "strain": STAGE,
        "base_freeze_commit": FROZEN_COMMIT,
        "base_freeze_manifest": identity["manifest"],
        "base_freeze_manifest_sha256": identity["manifest_sha256"],
        "base_manifest_file_count_verified": identity["manifest_file_count"],
        "base_manifest_mismatches": identity["mismatches"],
        "overlay": {
            "prospective_challenge": CHALLENGE,
            "prospective_challenge_revealed": True,
            "prospective_challenge_run": True,
            "sealed_gate_6_run": True,
            "verdict": "PASS" if passed else "FAIL",
        },
        "challenge_spec_sha256": sha256(sealed_path),
        "challenge_runner_sha256": sha256(Path(__file__)),
        "result_hashes": {
            "results/challenges/C-V23/per_seed.csv": sha256(
                result_dir / "per_seed.csv"
            ),
            "results/challenges/C-V23/summary.json": sha256(
                result_dir / "summary.json"
            ),
            "results/challenges/C-V23/report.md": sha256(report_path),
            "results/milestone-2-v2.3-gate6-update.md": sha256(
                milestone_path
            ),
        },
    }
    write_json(V2_ROOT / "results" / "V2.3" / "gate6-addendum.json", addendum)
    return summary


if __name__ == "__main__":
    result = main()
    print(json.dumps({"challenge": CHALLENGE, "passed": result["passed"]}))
    if not result["passed"]:
        raise SystemExit(1)
