"""Run sealed challenge C-V20 without importing the frozen oracle."""

from __future__ import annotations

import json
import math
import sys
from itertools import product
from pathlib import Path
from typing import Any

import numpy as np

V2_ROOT = Path(__file__).resolve().parents[1]
if str(V2_ROOT) not in sys.path:
    sys.path.insert(0, str(V2_ROOT))

from challenges.common import (  # noqa: E402
    escrow_rng,
    mean_interval,
    proportion_interval,
    released_seeds,
    verify_frozen_identity,
    write_csv,
    write_json,
)
from ref.factor import Factor  # noqa: E402
from ref.inference import ExactEngine  # noqa: E402
from ref.model import FiniteModel, Variable  # noqa: E402


CHALLENGE = "C-V20"
STAGE = "V2.0"
WORLD_COUNT = 50
TIME_SLICES = 5
PERTURBATIONS = (0.20, 0.50, 0.80)
X_PRIOR = np.array([0.45, 0.35, 0.20])
Y_PRIOR = np.array([0.60, 0.40])
X_TRANSITIONS = np.array(
    [
        [
            [0.82, 0.14, 0.04],
            [0.12, 0.76, 0.12],
            [0.04, 0.14, 0.82],
        ],
        [
            [0.15, 0.75, 0.10],
            [0.10, 0.15, 0.75],
            [0.75, 0.10, 0.15],
        ],
    ]
)
Y_TRANSITION = np.array([[0.82, 0.18], [0.22, 0.78]])
COLLIDER = np.empty((3, 2, 4))
for _x in range(3):
    for _y in range(2):
        COLLIDER[_x, _y] = 0.04
        COLLIDER[_x, _y, (_x + 2 * _y) % 4] = 0.88
X_ONLY = COLLIDER.mean(axis=1)


def runner_local_oracle(
    episode: dict[str, Any],
    query_time: int,
    observation_end: int,
    structure: str,
    collider_table: np.ndarray = COLLIDER,
) -> tuple[np.ndarray, float]:
    """Fresh direct trajectory summation; no frozen-oracle imports or helpers."""
    posterior = np.zeros((3, 2), dtype=float)
    evidence = 0.0
    actions = episode["actions"]
    for x_path in product(range(3), repeat=TIME_SLICES):
        x_mass = float(X_PRIOR[x_path[0]])
        for time in range(1, TIME_SLICES):
            x_mass *= float(
                X_TRANSITIONS[actions[time - 1], x_path[time - 1], x_path[time]]
            )
        for y_path in product(range(2), repeat=TIME_SLICES):
            mass = x_mass * float(Y_PRIOR[y_path[0]])
            for time in range(1, TIME_SLICES):
                mass *= float(Y_TRANSITION[y_path[time - 1], y_path[time]])
            for time in range(observation_end + 1):
                if structure == "H1":
                    mass *= float(
                        collider_table[
                            x_path[time], y_path[time], episode["o1"][time]
                        ]
                    )
                else:
                    mass *= float(X_ONLY[x_path[time], episode["o1"][time]])
                reliability = episode["reliability"]
                mass *= (
                    reliability
                    if episode["o2"][time] == y_path[time]
                    else 1.0 - reliability
                )
            evidence += mass
            posterior[x_path[query_time], y_path[query_time]] += mass
    if evidence <= 0:
        raise RuntimeError("runner-local oracle found zero evidence")
    return posterior / evidence, evidence


def build_model(
    episode: dict[str, Any],
    structure: str,
    observation_end: int = TIME_SLICES - 1,
    collider_table: np.ndarray = COLLIDER,
) -> FiniteModel:
    model = FiniteModel()
    for time in range(TIME_SLICES):
        model.add_variable(Variable(f"X{time}", 3, "latent", time))
        model.add_variable(Variable(f"Y{time}", 2, "latent", time))
    model.add_factor(Factor(("X0",), X_PRIOR, "categorical_prior"))
    model.add_factor(Factor(("Y0",), Y_PRIOR, "categorical_prior"))
    for time in range(1, TIME_SLICES):
        action = episode["actions"][time - 1]
        model.add_factor(
            Factor(
                (f"X{time - 1}", f"X{time}"),
                X_TRANSITIONS[action],
                "action_controlled_transition",
            )
        )
        model.add_factor(
            Factor(
                (f"Y{time - 1}", f"Y{time}"),
                Y_TRANSITION,
                "conditional_categorical",
            )
        )
    for time in range(observation_end + 1):
        if structure == "H1":
            model.add_factor(
                Factor(
                    (f"X{time}", f"Y{time}"),
                    collider_table[:, :, episode["o1"][time]],
                    "conditional_categorical",
                )
            )
        else:
            model.add_factor(
                Factor(
                    (f"X{time}",),
                    X_ONLY[:, episode["o1"][time]],
                    "conditional_categorical",
                )
            )
        reliability = episode["reliability"]
        o2 = episode["o2"][time]
        model.add_factor(
            Factor(
                (f"Y{time}",),
                np.array(
                    [
                        reliability if o2 == 0 else 1.0 - reliability,
                        reliability if o2 == 1 else 1.0 - reliability,
                    ]
                ),
                "conjugate_categorical_likelihood",
            )
        )
    return model


def generate_episode(seed: int, policy: int, structure: str) -> dict[str, Any]:
    truth_rng = escrow_rng(CHALLENGE, seed, "o2-truth")
    reliability = float(truth_rng.uniform(0.78, 0.90))
    latent_rng = escrow_rng(CHALLENGE, seed, "latent")
    x = [int(latent_rng.choice(3, p=X_PRIOR))]
    y = [int(latent_rng.choice(2, p=Y_PRIOR))]
    actions = [policy] * (TIME_SLICES - 1)
    for time in range(1, TIME_SLICES):
        x.append(
            int(
                latent_rng.choice(
                    3, p=X_TRANSITIONS[actions[time - 1], x[-1]]
                )
            )
        )
        y.append(int(latent_rng.choice(2, p=Y_TRANSITION[y[-1]])))
    o1_rng = escrow_rng(CHALLENGE, seed, "o1")
    o2_rng = escrow_rng(CHALLENGE, seed, "o2")
    o1 = []
    o2 = []
    for time in range(TIME_SLICES):
        likelihood = (
            COLLIDER[x[time], y[time]]
            if structure == "H1"
            else X_ONLY[x[time]]
        )
        o1.append(int(o1_rng.choice(4, p=likelihood)))
        o2.append(
            int(y[time] if o2_rng.random() < reliability else 1 - y[time])
        )
    return {
        "seed": seed,
        "policy": policy,
        "structure": structure,
        "reliability": reliability,
        "actions": actions,
        "x": x,
        "y": y,
        "o1": o1,
        "o2": o2,
    }


def log_evidence(
    episode: dict[str, Any],
    structure: str,
    collider_table: np.ndarray = COLLIDER,
) -> float:
    model = build_model(episode, structure, collider_table=collider_table)
    _, evidence = ExactEngine().infer(model, (), {})
    return float(np.log(evidence))


def render_report(summary: dict[str, Any]) -> str:
    verdict = "PASS" if summary["passed"] else "FAIL"
    return f"""# C-V20 Gate 6 report

Verdict: **{verdict}**

Frozen identity: {summary['frozen_identity']['manifest_file_count']} files checked
against `{summary['frozen_identity']['commit']}`, zero mismatches.

## Preregistered tests

- Exactness: {'PASS' if summary['tests']['exactness']['passed'] else 'FAIL'};
  maximum filtered/smoothed error
  `{summary['tests']['exactness']['maximum_absolute_error']:.3g}`.
- Learning: {'PASS' if summary['tests']['learning']['passed'] else 'FAIL'};
  posterior mean `{summary['tests']['learning']['posterior_mean']:.3f}` versus
  block truth `{summary['tests']['learning']['block_truth']:.3f}`.
- Structure comparison:
  {'PASS' if summary['tests']['comparison']['passed'] else 'FAIL'};
  H1 cumulative wins `{summary['tests']['comparison']['h1_wins_at_least_1_nat']}/50`,
  H2 cumulative wins `{summary['tests']['comparison']['h2_wins_at_least_1_nat']}/50`.
- Collider mutation:
  {'PASS' if summary['tests']['mutation']['passed'] else 'FAIL'};
  margins `{summary['tests']['mutation']['cumulative_margins']}` for perturbations
  `{list(PERTURBATIONS)}`.

## Failure interpretation

{summary['failure_interpretation']}

No frozen engine, stage, contract, tolerance, or manifest file was modified.
"""


def main() -> dict[str, Any]:
    identity = verify_frozen_identity(STAGE)
    seeds = released_seeds(CHALLENGE, WORLD_COUNT)
    h1_episodes = []
    h2_episodes = []
    for index, seed in enumerate(seeds):
        policy = 0 if index < 10 else 1 if index < 20 else index % 2
        h1_episodes.append(generate_episode(seed, policy, "H1"))
        h2_episodes.append(generate_episode(seed, policy, "H2"))

    maximum_exactness_error = 0.0
    exact_checks = 0
    engine = ExactEngine()
    for episode in h1_episodes[:20]:
        for time in range(TIME_SLICES):
            for observation_end in (time, TIME_SLICES - 1):
                model = build_model(episode, "H1", observation_end)
                actual, actual_z = engine.infer(
                    model, (f"X{time}", f"Y{time}"), {}
                )
                expected, expected_z = runner_local_oracle(
                    episode, time, observation_end, "H1"
                )
                maximum_exactness_error = max(
                    maximum_exactness_error,
                    float(np.max(np.abs(actual - expected))),
                    abs(actual_z - expected_z),
                )
                exact_checks += 1

    alpha_mismatch = 1.0
    alpha_match = 1.0
    truth_values = []
    cumulative_h1 = 0.0
    cumulative_h2 = 0.0
    h1_wins = 0
    h2_wins = 0
    rows = []
    h1_episode_effects = []
    h2_episode_effects = []
    for index, (seed, h1_episode, h2_episode) in enumerate(
        zip(seeds, h1_episodes, h2_episodes)
    ):
        matches = sum(
            int(observed == truth)
            for observed, truth in zip(h1_episode["o2"], h1_episode["y"])
        )
        alpha_match += matches
        alpha_mismatch += TIME_SLICES - matches
        truth_values.extend([h1_episode["reliability"]] * TIME_SLICES)

        h1_margin = log_evidence(h1_episode, "H1") - log_evidence(
            h1_episode, "H2"
        )
        h2_margin = log_evidence(h2_episode, "H2") - log_evidence(
            h2_episode, "H1"
        )
        cumulative_h1 += h1_margin
        cumulative_h2 += h2_margin
        h1_wins += int(cumulative_h1 >= 1.0)
        h2_wins += int(cumulative_h2 >= 1.0)
        h1_episode_effects.append(h1_margin)
        h2_episode_effects.append(h2_margin)
        rows.append(
            {
                "seed": seed,
                "policy": h1_episode["policy"],
                "o2_truth_reliability": h1_episode["reliability"],
                "o2_matches": matches,
                "o2_trials": TIME_SLICES,
                "o2_posterior_mean": alpha_match / (alpha_match + alpha_mismatch),
                "h1_episode_log_bf": h1_margin,
                "h1_cumulative_log_bf": cumulative_h1,
                "h2_episode_log_bf": h2_margin,
                "h2_cumulative_log_bf": cumulative_h2,
                "paired_latent_mismatch": int(
                    h1_episode["x"] != h2_episode["x"]
                    or h1_episode["y"] != h2_episode["y"]
                ),
            }
        )

    mutation_margins = []
    for amount in PERTURBATIONS:
        table = (1.0 - amount) * COLLIDER + amount * X_ONLY[:, None, :]
        margin = sum(
            log_evidence(episode, "H1", table) - log_evidence(episode, "H2")
            for episode in h1_episodes
        )
        mutation_margins.append(float(margin))

    posterior_mean = alpha_match / (alpha_match + alpha_mismatch)
    block_truth = float(np.mean(truth_values))
    exact_pass = maximum_exactness_error < 1e-10 and exact_checks == 200
    learning_pass = abs(posterior_mean - block_truth) <= 0.05
    comparison_pass = h1_wins >= 45 and h2_wins >= 45
    mutation_pass = bool(np.all(np.diff(mutation_margins) < 0))
    tests = {
        "exactness": {
            "passed": exact_pass,
            "maximum_absolute_error": maximum_exactness_error,
            "checks": exact_checks,
            "episodes_per_policy": 10,
        },
        "learning": {
            "passed": learning_pass,
            "posterior_mean": posterior_mean,
            "block_truth": block_truth,
            "absolute_error": abs(posterior_mean - block_truth),
        },
        "comparison": {
            "passed": comparison_pass,
            "h1_wins_at_least_1_nat": h1_wins,
            "h2_wins_at_least_1_nat": h2_wins,
            "h1_episode_effect_95_interval": mean_interval(h1_episode_effects),
            "h2_episode_effect_95_interval": mean_interval(h2_episode_effects),
            "h1_win_95_interval": proportion_interval(h1_wins, WORLD_COUNT),
            "h2_win_95_interval": proportion_interval(h2_wins, WORLD_COUNT),
        },
        "mutation": {
            "passed": mutation_pass,
            "perturbations": list(PERTURBATIONS),
            "cumulative_margins": mutation_margins,
        },
    }
    passed = all(test["passed"] for test in tests.values())
    failures = [name for name, test in tests.items() if not test["passed"]]
    failure_interpretation = (
        "No preregistered failure interpretation was triggered."
        if passed
        else "Retained failure(s): "
        + ", ".join(failures)
        + ". This localizes the kernel finding to the named dissociation(s)."
    )
    summary = {
        "challenge": CHALLENGE,
        "stage": STAGE,
        "seed_block_used": [seeds[0], seeds[-1]],
        "world_count": WORLD_COUNT,
        "frozen_identity": identity,
        "configuration": {
            "time_slices": TIME_SLICES,
            "x_cardinality": 3,
            "y_cardinality": 2,
            "actions": 2,
            "collider_outcomes": 4,
            "perturbations": list(PERTURBATIONS),
        },
        "tests": tests,
        "failures": failures,
        "failure_interpretation": failure_interpretation,
        "passed": passed,
    }
    result_dir = V2_ROOT / "results" / "challenges" / CHALLENGE
    write_csv(result_dir / "per_seed.csv", rows)
    write_json(result_dir / "summary.json", summary)
    (result_dir / "report.md").write_text(render_report(summary), encoding="utf-8")
    return summary


if __name__ == "__main__":
    result = main()
    print(json.dumps({"challenge": CHALLENGE, "passed": result["passed"]}))
    if not result["passed"]:
        raise SystemExit(1)

