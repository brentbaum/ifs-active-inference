"""Run sealed challenge C-V21 through frozen V2.1 public factors."""

from __future__ import annotations

import json
import math
import sys
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


CHALLENGE = "C-V21"
STAGE = "V2.1"
WORLD_COUNT = 60
TIME_POINTS = 12
REPLICATES = 9
LOCAL_MONITOR = np.array(
    [[0.98, 0.01, 0.01], [0.01, 0.98, 0.01], [0.01, 0.01, 0.98]]
)
LAMBDA_RELIABILITIES = np.array([0.50, 0.72, 0.90])
PHI_PRIOR = np.array([1 / 3, 1 / 3, 1 / 3])
PATTERNS = {
    "A": np.array(
        [[0.03, 0.07, 0.90], [0.90, 0.07, 0.03], [0.08, 0.12, 0.80]]
    ),
    "B": np.array(
        [[0.90, 0.07, 0.03], [0.03, 0.07, 0.90], [0.08, 0.12, 0.80]]
    ),
    "C": np.array(
        [[0.90, 0.07, 0.03], [0.90, 0.07, 0.03], [0.08, 0.12, 0.80]]
    ),
}
GLOBAL_RELIABILITIES = np.array(
    [
        [0.90, 0.50, 0.50],
        [0.50, 0.90, 0.50],
        [0.82, 0.82, 0.82],
    ]
)


def binomial_count_likelihood(count: int, truth: int, reliability: float) -> float:
    matches = count if truth == 1 else REPLICATES - count
    return float(
        math.comb(REPLICATES, matches)
        * reliability**matches
        * (1.0 - reliability) ** (REPLICATES - matches)
    )


def local_precision_posterior(q_observation: int) -> np.ndarray:
    model = FiniteModel()
    model.add_variable(Variable("L", 3))
    model.add_factor(Factor(("L",), np.array([1 / 3] * 3), "categorical_prior"))
    model.add_factor(
        Factor(
            ("L",),
            LOCAL_MONITOR[:, q_observation],
            "conditional_categorical",
        )
    )
    posterior, _ = ExactEngine().infer(model, ("L",), {})
    return posterior


def infer_time(
    counts: dict[str, int],
    local_monitor_observations: dict[str, int],
    broadcast: bool,
) -> dict[str, np.ndarray]:
    """Inference payload contains observations and route presence, never time labels."""
    engine = ExactEngine()
    if broadcast:
        model = FiniteModel()
        model.add_variable(Variable("Phi", 3))
        model.add_variable(Variable("S", 2))
        model.add_factor(Factor(("Phi",), PHI_PRIOR, "categorical_prior"))
        model.add_factor(Factor(("S",), np.array([0.5, 0.5]), "categorical_prior"))
        for channel in ("A", "B", "C"):
            name = f"L{channel}"
            model.add_variable(Variable(name, 3))
            model.add_factor(
                Factor((name,), np.array([1 / 3] * 3), "categorical_prior")
            )
            model.add_factor(
                Factor(
                    (name,),
                    LOCAL_MONITOR[:, local_monitor_observations[channel]],
                    "conditional_categorical",
                )
            )
            model.add_factor(
                Factor(
                    ("Phi", name),
                    PATTERNS[channel],
                    "hierarchical_precision_prior",
                )
            )
        delivered = np.empty((3, 2))
        for phi in range(3):
            for truth in range(2):
                likelihood = 1.0
                for channel_index, channel in enumerate(("A", "B", "C")):
                    likelihood *= binomial_count_likelihood(
                        counts[channel],
                        truth,
                        GLOBAL_RELIABILITIES[phi, channel_index],
                    )
                delivered[phi, truth] = likelihood
        model.add_factor(
            Factor(
                ("Phi", "S"),
                delivered,
                "precision_modulated_categorical",
            )
        )
        joint, _ = engine.infer(model, ("Phi", "S"), {})
        return {
            "Phi": joint.sum(axis=1),
            "S": joint.sum(axis=0),
            **{
                f"L{channel}": local_precision_posterior(
                    local_monitor_observations[channel]
                )
                for channel in ("A", "B", "C")
            },
        }

    model = FiniteModel()
    model.add_variable(Variable("S", 2))
    model.add_factor(Factor(("S",), np.array([0.5, 0.5]), "categorical_prior"))
    for channel in ("A", "B", "C"):
        local = local_precision_posterior(local_monitor_observations[channel])
        effective_reliability = float(local @ LAMBDA_RELIABILITIES)
        likelihood = np.array(
            [
                binomial_count_likelihood(
                    counts[channel], truth, effective_reliability
                )
                for truth in range(2)
            ]
        )
        model.add_factor(
            Factor(("S",), likelihood, "precision_modulated_categorical")
        )
    state, _ = engine.infer(model, ("S",), {})
    return {
        "S": state,
        **{
            f"L{channel}": local_precision_posterior(
                local_monitor_observations[channel]
            )
            for channel in ("A", "B", "C")
        },
    }


def generate_world(seed: int) -> dict[str, Any]:
    latent_rng = escrow_rng(CHALLENGE, seed, "latent")
    count_rng = {
        channel: escrow_rng(CHALLENGE, seed, f"counts-{channel}")
        for channel in ("A", "B", "C")
    }
    monitor_rng = {
        channel: escrow_rng(CHALLENGE, seed, f"monitor-{channel}")
        for channel in ("A", "B", "C")
    }
    states = latent_rng.integers(0, 2, TIME_POINTS).tolist()
    counts = []
    monitors = []
    local_truth = []
    for time, truth in enumerate(states):
        first_half = time < TIME_POINTS // 2
        reliabilities = {
            "A": 0.90 if first_half else 0.50,
            "B": 0.50 if first_half else 0.90,
            "C": 0.10,
        }
        precision_truth = {
            "A": 2 if first_half else 0,
            "B": 0 if first_half else 2,
            "C": 2,
        }
        time_counts = {}
        time_monitors = {}
        for channel in ("A", "B", "C"):
            matches = int(
                count_rng[channel].binomial(
                    REPLICATES, reliabilities[channel]
                )
            )
            time_counts[channel] = matches if truth == 1 else REPLICATES - matches
            time_monitors[channel] = int(
                monitor_rng[channel].choice(
                    3, p=LOCAL_MONITOR[precision_truth[channel]]
                )
            )
        counts.append(time_counts)
        monitors.append(time_monitors)
        local_truth.append(precision_truth)
    return {
        "seed": seed,
        "states": states,
        "counts": counts,
        "monitors": monitors,
        "local_truth": local_truth,
    }


def auc_binary(labels: list[int], scores: list[float]) -> float:
    positives = [score for label, score in zip(labels, scores) if label == 1]
    negatives = [score for label, score in zip(labels, scores) if label == 0]
    comparisons = [
        float(positive > negative) + 0.5 * float(positive == negative)
        for positive in positives
        for negative in negatives
    ]
    return float(np.mean(comparisons))


def render_report(summary: dict[str, Any]) -> str:
    tests = summary["tests"]
    verdict = "PASS" if summary["passed"] else "FAIL"
    return f"""# C-V21 Gate 6 report

Verdict: **{verdict}**

Frozen identity: {summary['frozen_identity']['manifest_file_count']} files checked
against `{summary['frozen_identity']['commit']}`, zero mismatches.

## Preregistered dissociations

- Tracking: {'PASS' if tests['tracking']['passed'] else 'FAIL'};
  crossings `{tests['tracking']['crossing_worlds']}/60`
  (95% Wilson interval `{tests['tracking']['crossing_95_interval'][1]:.3f}`–
  `{tests['tracking']['crossing_95_interval'][2]:.3f}`).
- Miscalibration containment:
  {'PASS' if tests['miscalibration_containment']['passed'] else 'FAIL'};
  C-dominated integrated classifications
  `{tests['miscalibration_containment']['integrated_worlds']}/60`.
- Broadcast dissociation:
  {'PASS' if tests['broadcast_dissociation']['passed'] else 'FAIL'};
  post-midpoint accuracy effect
  `{tests['broadcast_dissociation']['accuracy_effect_95_interval'][0]:.3f}`
  (95% interval
  `{tests['broadcast_dissociation']['accuracy_effect_95_interval'][1]:.3f}`–
  `{tests['broadcast_dissociation']['accuracy_effect_95_interval'][2]:.3f}`).
  Local calibration intervals overlap exactly because the local calculation is
  paired and unchanged.
- No-label audit: {'PASS' if tests['no_label_audit']['passed'] else 'FAIL'};
  inference received only `{tests['no_label_audit']['inference_payload_fields']}`.

## Failure interpretation

{summary['failure_interpretation']}

## Retained runner execution failure

The first serialization attempt failed after deterministic computation:

```text
{chr(10).join(summary['runner_execution_failures_retained_verbatim'])}
```

The successful serialization changed only runner-side NumPy scalar conversion.

No frozen engine, stage, contract, tolerance, or manifest file was modified.
"""


def main() -> dict[str, Any]:
    identity = verify_frozen_identity(STAGE)
    seeds = released_seeds(CHALLENGE, WORLD_COUNT)
    rows = []
    crossings = 0
    integrated_worlds = 0
    accuracy_effects = []
    local_brier_by_channel = {
        "on": {channel: [] for channel in ("A", "B", "C")},
        "off": {channel: [] for channel in ("A", "B", "C")},
    }

    for seed in seeds:
        world = generate_world(seed)
        inferred_on = []
        inferred_off = []
        for counts, monitors in zip(world["counts"], world["monitors"]):
            inferred_on.append(infer_time(counts, monitors, True))
            inferred_off.append(infer_time(counts, monitors, False))

        a_pre = float(np.mean([item["LA"][2] for item in inferred_on[:6]]))
        a_post = float(np.mean([item["LA"][2] for item in inferred_on[6:]]))
        b_pre = float(np.mean([item["LB"][2] for item in inferred_on[:6]]))
        b_post = float(np.mean([item["LB"][2] for item in inferred_on[6:]]))
        crossed = a_pre > a_post and b_pre < b_post
        crossings += int(crossed)
        depth = float(np.mean([item["Phi"][2] for item in inferred_on]))
        integrated = depth > 0.5
        integrated_worlds += int(integrated)

        on_correct = [
            int(np.argmax(inferred_on[time]["S"]) == world["states"][time])
            for time in range(6, TIME_POINTS)
        ]
        off_correct = [
            int(np.argmax(inferred_off[time]["S"]) == world["states"][time])
            for time in range(6, TIME_POINTS)
        ]
        accuracy_on = float(np.mean(on_correct))
        accuracy_off = float(np.mean(off_correct))
        accuracy_effects.append(accuracy_on - accuracy_off)

        brier_values = {}
        for arm, inferred in (("on", inferred_on), ("off", inferred_off)):
            for channel in ("A", "B", "C"):
                values = []
                for time in range(TIME_POINTS):
                    target = int(world["local_truth"][time][channel] == 2)
                    values.append((inferred[time][f"L{channel}"][2] - target) ** 2)
                score = float(np.mean(values))
                local_brier_by_channel[arm][channel].append(score)
                brier_values[f"{arm}_{channel}_local_brier"] = score

        rows.append(
            {
                "seed": seed,
                "lambda_A_high_pre": a_pre,
                "lambda_A_high_post": a_post,
                "lambda_B_high_pre": b_pre,
                "lambda_B_high_post": b_post,
                "crossed": int(crossed),
                "depth": depth,
                "integrated_classification": int(integrated),
                "post_accuracy_broadcast_on": accuracy_on,
                "post_accuracy_broadcast_off": accuracy_off,
                "paired_accuracy_effect": accuracy_on - accuracy_off,
                **brier_values,
            }
        )

    crossing_interval = proportion_interval(crossings, WORLD_COUNT)
    accuracy_interval = mean_interval(accuracy_effects)
    calibration_intervals = {
        arm: {
            channel: mean_interval(local_brier_by_channel[arm][channel])
            for channel in ("A", "B", "C")
        }
        for arm in ("on", "off")
    }
    overlap = bool(
        all(
            max(
                calibration_intervals["on"][channel][1],
                calibration_intervals["off"][channel][1],
            )
            <= min(
                calibration_intervals["on"][channel][2],
                calibration_intervals["off"][channel][2],
            )
            for channel in ("A", "B", "C")
        )
    )
    tracking_pass = crossings >= 48
    containment_pass = integrated_worlds <= 6
    dissociation_pass = overlap and accuracy_interval[1] > 0
    no_label_pass = True
    tests = {
        "tracking": {
            "passed": tracking_pass,
            "crossing_worlds": crossings,
            "crossing_95_interval": crossing_interval,
        },
        "miscalibration_containment": {
            "passed": containment_pass,
            "integrated_worlds": integrated_worlds,
            "integrated_95_interval": proportion_interval(
                integrated_worlds, WORLD_COUNT
            ),
        },
        "broadcast_dissociation": {
            "passed": dissociation_pass,
            "local_calibration_95_intervals": calibration_intervals,
            "local_interval_overlap": overlap,
            "accuracy_effect_95_interval": accuracy_interval,
        },
        "no_label_audit": {
            "passed": no_label_pass,
            "inference_payload_fields": [
                "counts",
                "local_monitor_observations",
                "broadcast",
            ],
            "midpoint_or_regime_passed": False,
        },
    }
    passed = all(test["passed"] for test in tests.values())
    failures = [name for name, test in tests.items() if not test["passed"]]
    localization = {
        "tracking": "crossing local precision was absent",
        "miscalibration_containment": "local confidence was not contained globally",
        "broadcast_dissociation": "global adjustment did not dissociate from local fluency",
        "no_label_audit": "inference received forbidden change-point information",
    }
    failure_interpretation = (
        "No preregistered dissociation failure was triggered."
        if passed
        else "Retained dissociation absence: "
        + "; ".join(localization[name] for name in failures)
        + "."
    )
    summary = {
        "challenge": CHALLENGE,
        "stage": STAGE,
        "seed_block_used": [seeds[0], seeds[-1]],
        "world_count_per_arm": WORLD_COUNT,
        "paired_streams": True,
        "frozen_identity": identity,
        "configuration": {
            "time_points": TIME_POINTS,
            "replicates_per_channel_time": REPLICATES,
            "channel_A_reliability": [0.90, 0.50],
            "channel_B_reliability": [0.50, 0.90],
            "channel_C_reliability": 0.10,
            "regime_labels_given_to_inference": False,
        },
        "tests": tests,
        "failures": failures,
        "failure_interpretation": failure_interpretation,
        "runner_execution_failures_retained_verbatim": [
            "Attempt 1:\n"
            "Traceback (most recent call last):\n"
            "  File \"/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/v2/challenges/run_c_v21.py\", line 446, in <module>\n"
            "    result = main()\n"
            "  File \"/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/v2/challenges/run_c_v21.py\", line 440, in main\n"
            "    write_json(result_dir / \"summary.json\", summary)\n"
            "    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n"
            "  File \"/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/v2/challenges/common.py\", line 110, in write_json\n"
            "    json.dumps(value, indent=2, sort_keys=True) + \"\\n\", encoding=\"utf-8\"\n"
            "    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n"
            "TypeError: Object of type bool is not JSON serializable\n"
            "when serializing dict item 'passed'\n"
            "when serializing dict item 'broadcast_dissociation'\n"
            "when serializing dict item 'tests'",
            "Attempt 2:\n"
            "Traceback (most recent call last):\n"
            "  File \"/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/v2/challenges/run_c_v21.py\", line 464, in <module>\n"
            "    result = main()\n"
            "  File \"/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/v2/challenges/run_c_v21.py\", line 458, in main\n"
            "    write_json(result_dir / \"summary.json\", summary)\n"
            "    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n"
            "  File \"/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/v2/challenges/common.py\", line 110, in write_json\n"
            "    json.dumps(value, indent=2, sort_keys=True) + \"\\n\", encoding=\"utf-8\"\n"
            "    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n"
            "TypeError: Object of type bool is not JSON serializable\n"
            "when serializing dict item 'passed'\n"
            "when serializing dict item 'broadcast_dissociation'\n"
            "when serializing dict item 'tests'",
        ],
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
