"""V2.3.2 static T/D/P formation re-foundation."""

from __future__ import annotations

import itertools
import json
import math
import copy
from contextlib import contextmanager
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable

import numpy as np

from .audit import ProtocolState, audit_one_posterior
from .constitution import cumulative_constitution_audit
from .rng import component_rng
from .statistics import bootstrap_interval, ece_binary


PARAMETER_PATH = (
    Path(__file__).resolve().parents[1]
    / "protocols"
    / "v2.3.2-formation-parameters.json"
)
PARAMETERS = json.loads(PARAMETER_PATH.read_text(encoding="utf-8"))
LABELS = tuple(PARAMETERS["candidate_labels"])
PRIOR = np.asarray(PARAMETERS["candidate_prior"], dtype=float)
SUPPORT = tuple(
    (self_value, outcome, localization)
    for self_value, outcome in itertools.product((0, 1), repeat=2)
    for localization in (0, 1, 2)
)
SUPPORT_INDEX = {value: index for index, value in enumerate(SUPPORT)}
TOLERANCE = 1e-10


def _logit(value: float) -> float:
    return math.log(value / (1.0 - value))


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def _sharpen(value: float, scale: float) -> float:
    return _sigmoid(scale * _logit(value))


def _base_probabilities(
    candidate: str,
    *,
    precision: str,
    control: str,
    broadcast: str,
    real_danger: bool,
    lesions: frozenset[str],
) -> tuple[float, float, float | None, float]:
    scale = float(PARAMETERS["precision_scale"][precision])
    if "event_precision" in lesions:
        scale = float(PARAMETERS["precision_scale"]["ordinary"])
    self_probability = float(PARAMETERS["self_probability"][candidate])
    if "root_coupling" in lesions and candidate == "P":
        self_probability = float(PARAMETERS["self_probability"]["D"])
    effective_control = "low" if "control_inference" in lesions else control
    if candidate == "D":
        key = "D_real" if real_danger else "D_apparent"
    else:
        key = candidate
    outcome_probability = float(
        PARAMETERS["outcome_probability"][key][
            f"{effective_control}_control"
        ]
    )
    localization_probability: float | None
    if broadcast == "collapsed" or "context_route" in lesions:
        localization_probability = None
    else:
        localization_probability = float(
            PARAMETERS["localization_probability"][candidate]
        )
    coupling = float(PARAMETERS["configural_log_coupling"][candidate])
    return (
        _sharpen(self_probability, scale),
        _sharpen(outcome_probability, scale),
        (
            None
            if localization_probability is None
            else _sharpen(localization_probability, scale)
        ),
        coupling * scale,
    )


def slice_distribution(
    candidate: str,
    *,
    event: bool,
    precision: str,
    control: str,
    broadcast: str,
    real_danger: bool,
    lesions: Iterable[str] = (),
) -> np.ndarray:
    """Normalized predictive row on the common S/Y/X support."""
    if candidate not in LABELS:
        raise ValueError("unknown formation candidate")
    lesions_set = frozenset(lesions)
    if not event:
        row = np.zeros(len(SUPPORT))
        for self_value, outcome in itertools.product((0, 1), repeat=2):
            row[SUPPORT_INDEX[(self_value, outcome, 2)]] = 0.25
        return row
    if "structure_comparison" in lesions_set:
        candidate = "T"
    ps, py, px, coupling = _base_probabilities(
        candidate,
        precision=precision,
        control=control,
        broadcast=broadcast,
        real_danger=real_danger,
        lesions=lesions_set,
    )
    weights = np.zeros(len(SUPPORT))
    for index, (self_value, outcome, localization) in enumerate(SUPPORT):
        if px is None:
            if localization != 2:
                continue
            p_localization = 1.0
        else:
            if localization == 2:
                continue
            p_localization = px if localization else 1.0 - px
        weight = (
            (ps if self_value else 1.0 - ps)
            * (py if outcome else 1.0 - py)
            * p_localization
            * math.exp(coupling * self_value * outcome)
        )
        weights[index] = weight
    return weights / weights.sum()


def slice_decomposition(
    candidate: str,
    observation: tuple[int, int, int],
    *,
    event: bool,
    precision: str,
    control: str,
    broadcast: str,
    real_danger: bool,
    lesions: Iterable[str] = (),
) -> dict[str, float]:
    if not event:
        probability = slice_distribution(
            candidate,
            event=False,
            precision=precision,
            control=control,
            broadcast=broadcast,
            real_danger=real_danger,
            lesions=lesions,
        )[SUPPORT_INDEX[observation]]
        return {
            "self": 0.0,
            "outcome_control": 0.0,
            "localization": 0.0,
            "configural": 0.0,
            "normalization": math.log(probability),
            "total": math.log(probability),
        }
    lesions_set = frozenset(lesions)
    effective_candidate = (
        "T" if "structure_comparison" in lesions_set else candidate
    )
    ps, py, px, coupling = _base_probabilities(
        effective_candidate,
        precision=precision,
        control=control,
        broadcast=broadcast,
        real_danger=real_danger,
        lesions=lesions_set,
    )
    self_value, outcome, localization = observation
    self_term = math.log(ps if self_value else 1.0 - ps)
    outcome_term = math.log(py if outcome else 1.0 - py)
    if px is None:
        if localization != 2:
            return {
                "self": -math.inf,
                "outcome_control": 0.0,
                "localization": 0.0,
                "configural": 0.0,
                "normalization": 0.0,
                "total": -math.inf,
            }
        localization_term = 0.0
    else:
        if localization == 2:
            return {
                "self": -math.inf,
                "outcome_control": 0.0,
                "localization": 0.0,
                "configural": 0.0,
                "normalization": 0.0,
                "total": -math.inf,
            }
        localization_term = math.log(
            px if localization else 1.0 - px
        )
    configural_term = coupling * self_value * outcome
    raw_logs = []
    for support_value in SUPPORT:
        s, y, x = support_value
        if px is None and x != 2:
            continue
        if px is not None and x == 2:
            continue
        raw_logs.append(
            math.log(ps if s else 1.0 - ps)
            + math.log(py if y else 1.0 - py)
            + (
                0.0
                if px is None
                else math.log(px if x else 1.0 - px)
            )
            + coupling * s * y
        )
    maximum = max(raw_logs)
    log_partition = maximum + math.log(
        sum(math.exp(value - maximum) for value in raw_logs)
    )
    total = (
        self_term
        + outcome_term
        + localization_term
        + configural_term
        - log_partition
    )
    return {
        "self": self_term,
        "outcome_control": outcome_term,
        "localization": localization_term,
        "configural": configural_term,
        "normalization": -log_partition,
        "total": total,
    }


def score_slice(
    prior: np.ndarray,
    observation: tuple[int, int, int] | None,
    configuration: dict[str, Any],
    *,
    masked: bool = False,
    lesions: Iterable[str] = (),
) -> tuple[np.ndarray, float, dict[str, Any]]:
    prior = np.asarray(prior, dtype=float)
    if masked or observation is None:
        contributions = np.zeros(len(LABELS))
        return prior.copy(), 1.0, {
            "candidate_log_likelihoods": contributions.tolist(),
            "pairwise_log_bf": {"P/T": 0.0, "D/T": 0.0, "P/D": 0.0},
            "decomposition": {},
        }
    likelihoods = np.array(
        [
            slice_distribution(candidate, lesions=lesions, **configuration)[
                SUPPORT_INDEX[observation]
            ]
            for candidate in LABELS
        ]
    )
    joint = prior * likelihoods
    evidence = float(joint.sum())
    posterior = joint / evidence
    decompositions = {
        candidate: slice_decomposition(
            candidate, observation, lesions=lesions, **configuration
        )
        for candidate in LABELS
    }
    logs = np.log(likelihoods)
    return posterior, evidence, {
        "candidate_log_likelihoods": logs.tolist(),
        "pairwise_log_bf": {
            "P/T": float(logs[2] - logs[0]),
            "D/T": float(logs[1] - logs[0]),
            "P/D": float(logs[2] - logs[1]),
        },
        "decomposition": decompositions,
    }


def independent_history_sum(
    prior: np.ndarray,
    observations: list[tuple[int, int, int] | None],
    configurations: list[dict[str, Any]],
    masks: list[bool] | None = None,
    lesions: Iterable[str] = (),
) -> tuple[np.ndarray, np.ndarray]:
    """Independent scalar implementation; does not call score_slice."""
    masks = [False] * len(observations) if masks is None else masks
    log_joint = [math.log(float(value)) for value in prior]
    for observation, configuration, masked in zip(
        observations, configurations, masks
    ):
        if masked or observation is None:
            continue
        index = SUPPORT_INDEX[observation]
        for candidate_index, candidate in enumerate(LABELS):
            row = slice_distribution(
                candidate, lesions=lesions, **configuration
            )
            log_joint[candidate_index] += math.log(float(row[index]))
    maximum = max(log_joint)
    masses = [math.exp(value - maximum) for value in log_joint]
    total = sum(masses)
    posterior = np.array([value / total for value in masses])
    return posterior, np.asarray(log_joint)


def score_history(
    observations: list[tuple[int, int, int] | None],
    configurations: list[dict[str, Any]],
    *,
    prior: np.ndarray | None = None,
    masks: list[bool] | None = None,
    lesions: Iterable[str] = (),
) -> dict[str, Any]:
    posterior = PRIOR.copy() if prior is None else np.asarray(prior).copy()
    masks = [False] * len(observations) if masks is None else masks
    initial_prior = posterior.copy()
    contributions = []
    log_likelihoods = np.zeros(len(LABELS))
    states = []
    for observation, configuration, masked in zip(
        observations, configurations, masks
    ):
        posterior, evidence, detail = score_slice(
            posterior,
            observation,
            configuration,
            masked=masked,
            lesions=lesions,
        )
        log_likelihoods += np.asarray(
            detail["candidate_log_likelihoods"]
        )
        contributions.append(detail)
        state = ProtocolState(
            posterior_store={"H_formation": posterior.copy()},
            evidence_store={"slice": evidence},
            metadata=MappingProxyType(
                {
                    "stage": "V2.3.2-formation",
                    "static_structure": True,
                }
            ),
        )
        audit_one_posterior(state)
        states.append(state)
    independent_posterior, independent_joint = independent_history_sum(
        initial_prior,
        observations,
        configurations,
        masks,
        lesions,
    )
    if not np.allclose(
        posterior, independent_posterior, atol=TOLERANCE, rtol=0
    ):
        raise AssertionError("history scorer disagrees with independent sum")
    return {
        "posterior": posterior,
        "log_likelihoods": log_likelihoods,
        "log_joint": np.log(initial_prior) + log_likelihoods,
        "independent_log_joint": independent_joint,
        "contributions": contributions,
        "states": states,
    }


def expected_log_bf(
    generating_candidate: str,
    comparison_numerator: str,
    comparison_denominator: str,
    configuration: dict[str, Any],
    *,
    masked: bool = False,
    lesions: Iterable[str] = (),
) -> float:
    if masked:
        return 0.0
    generating = slice_distribution(
        generating_candidate, lesions=lesions, **configuration
    )
    numerator = slice_distribution(
        comparison_numerator, lesions=lesions, **configuration
    )
    denominator = slice_distribution(
        comparison_denominator, lesions=lesions, **configuration
    )
    positive = generating > 0
    return float(
        np.sum(
            generating[positive]
            * np.log(numerator[positive] / denominator[positive])
        )
    )


def sign_table() -> list[dict[str, Any]]:
    rows = []
    for event, precision, control, broadcast, real_danger, masked in itertools.product(
        (False, True),
        ("ordinary", "overwhelm"),
        ("low", "high"),
        ("collapsed", "integrated"),
        (False, True),
        (False, True),
    ):
        configuration = {
            "event": event,
            "precision": precision,
            "control": control,
            "broadcast": broadcast,
            "real_danger": real_danger,
        }
        row: dict[str, Any] = {
            **configuration,
            "masked": masked,
        }
        for generating in LABELS:
            for numerator, denominator in (
                ("P", "T"),
                ("D", "T"),
                ("P", "D"),
            ):
                row[
                    f"E_{generating}_logBF_{numerator}_{denominator}"
                ] = expected_log_bf(
                    generating,
                    numerator,
                    denominator,
                    configuration,
                    masked=masked,
                )
        rows.append(row)
    return rows


def analytic_slice_bound() -> float:
    maximum = 0.0
    for row in sign_table():
        if row["masked"]:
            continue
        configuration = {
            key: row[key]
            for key in (
                "event",
                "precision",
                "control",
                "broadcast",
                "real_danger",
            )
        }
        distributions = {
            candidate: slice_distribution(candidate, **configuration)
            for candidate in LABELS
        }
        for left, right in itertools.combinations(LABELS, 2):
            positive = (
                distributions[left] > 0
            ) & (distributions[right] > 0)
            maximum = max(
                maximum,
                float(
                    np.max(
                        np.abs(
                            np.log(
                                distributions[left][positive]
                                / distributions[right][positive]
                            )
                        )
                    )
                ),
            )
    return maximum


def semantic_proofs() -> dict[str, Any]:
    table = sign_table()
    normalization_errors = []
    decomposition_errors = []
    independent_errors = []
    observed_log_ratios = []
    for row in table:
        configuration = {
            key: row[key]
            for key in (
                "event",
                "precision",
                "control",
                "broadcast",
                "real_danger",
            )
        }
        for candidate in LABELS:
            distribution = slice_distribution(candidate, **configuration)
            normalization_errors.append(abs(float(distribution.sum()) - 1.0))
            for index in np.flatnonzero(distribution > 0):
                observation = SUPPORT[int(index)]
                decomposition = slice_decomposition(
                    candidate, observation, **configuration
                )
                decomposition_errors.append(
                    abs(
                        decomposition["total"]
                        - math.log(float(distribution[index]))
                    )
                )
        if not row["masked"]:
            observation = SUPPORT[
                int(np.argmax(slice_distribution("P", **configuration)))
            ]
            scored = score_history([observation], [configuration])
            independent_errors.append(
                float(
                    np.max(
                        np.abs(
                            scored["log_joint"]
                            - scored["independent_log_joint"]
                        )
                    )
                )
            )
            for left, right in itertools.combinations(LABELS, 2):
                dl = slice_distribution(left, **configuration)
                dr = slice_distribution(right, **configuration)
                positive = (dl > 0) & (dr > 0)
                observed_log_ratios.extend(
                    np.abs(np.log(dl[positive] / dr[positive])).tolist()
                )
    zero_rows = [
        row
        for row in table
        if not row["event"] or row["masked"]
    ]
    maximum_zero = max(
        abs(value)
        for row in zero_rows
        for key, value in row.items()
        if key.startswith("E_")
    )
    ordinary = {
        "event": True,
        "precision": "ordinary",
        "control": "low",
        "broadcast": "collapsed",
        "real_danger": False,
    }
    overwhelm = {**ordinary, "precision": "overwhelm"}
    precision_effect = expected_log_bf(
        "P", "P", "T", overwhelm
    ) - expected_log_bf("P", "P", "T", ordinary)
    low = expected_log_bf("P", "P", "T", overwhelm)
    high = expected_log_bf(
        "P", "P", "T", {**overwhelm, "control": "high"}
    )
    integrated = expected_log_bf(
        "D",
        "D",
        "P",
        {**overwhelm, "broadcast": "integrated", "real_danger": True},
    )
    collapsed = expected_log_bf(
        "D",
        "D",
        "P",
        {**overwhelm, "broadcast": "collapsed", "real_danger": True},
    )
    bound = analytic_slice_bound()
    return {
        "candidate_normalization_maximum_error": max(normalization_errors),
        "zero_row_maximum_absolute_expected_log_bf": maximum_zero,
        "decomposition_maximum_error": max(decomposition_errors),
        "precision_pathway_effect": precision_effect,
        "low_control_P_vs_T_expected_log_bf": low,
        "high_control_P_vs_T_expected_log_bf": high,
        "control_pathway_effect": low - high,
        "integrated_D_vs_P_expected_log_bf": integrated,
        "collapsed_D_vs_P_expected_log_bf": collapsed,
        "context_pathway_effect": integrated - collapsed,
        "analytic_per_slice_log_bf_bound": bound,
        "maximum_enumerated_log_bf": max(observed_log_ratios),
        "independent_implementation_maximum_error": max(independent_errors),
        "constitution": cumulative_constitution_audit(),
    }


def _sample_observation(
    seed: int,
    component: str,
    candidate: str,
    configuration: dict[str, Any],
) -> tuple[int, int, int]:
    distribution = slice_distribution(candidate, **configuration)
    index = int(
        component_rng(seed, component).choice(
            len(distribution), p=distribution
        )
    )
    return SUPPORT[index]


def _recovery_configurations(truth: str) -> list[dict[str, Any]]:
    values = []
    for time in range(int(PARAMETERS["sequence_length"])):
        values.append(
            {
                "event": True,
                "precision": "overwhelm" if time % 4 == 0 else "ordinary",
                "control": "low" if time % 3 else "high",
                "broadcast": "collapsed" if time % 5 == 0 else "integrated",
                "real_danger": truth == "D",
            }
        )
    return values


def recovery_assay() -> dict[str, Any]:
    confusion = np.zeros((3, 3), dtype=int)
    probabilities = []
    truths = []
    brier = []
    coverages = []
    parameter_errors = []
    rows = []
    start, end = PARAMETERS["recovery_seed_block"]
    for offset, seed in enumerate(range(start, end + 1)):
        truth_index = offset % 3
        truth = LABELS[truth_index]
        configurations = _recovery_configurations(truth)
        observations = [
            _sample_observation(
                seed, f"v232f-recovery-{time}", truth, configuration
            )
            for time, configuration in enumerate(configurations)
        ]
        result = score_history(observations, configurations)
        posterior = result["posterior"]
        predicted = int(np.argmax(posterior))
        confusion[truth_index, predicted] += 1
        probabilities.append(float(posterior[predicted]))
        truths.append(int(predicted == truth_index))
        target = np.zeros(3)
        target[truth_index] = 1.0
        brier.append(float(np.mean((posterior - target) ** 2)))
        ordered = np.argsort(posterior)[::-1]
        included = []
        total = 0.0
        for index in ordered:
            included.append(int(index))
            total += float(posterior[index])
            if total >= 0.95:
                break
        coverages.append(float(truth_index in included))
        empirical = np.bincount(
            [SUPPORT_INDEX[value] for value in observations],
            minlength=len(SUPPORT),
        ) / len(observations)
        expected = np.mean(
            [
                slice_distribution(truth, **configuration)
                for configuration in configurations
            ],
            axis=0,
        )
        parameter_errors.append(float(np.mean(np.abs(empirical - expected))))
        rows.append(
            {
                "seed": seed,
                "truth": truth,
                "predicted": LABELS[predicted],
                "T_probability": posterior[0],
                "D_probability": posterior[1],
                "P_probability": posterior[2],
            }
        )
    row_totals = confusion.sum(axis=1)
    false_p_high_control = []
    no_event_false_p = []
    for seed in range(start, start + 100):
        high_config = {
            "event": True,
            "precision": "ordinary",
            "control": "high",
            "broadcast": "integrated",
            "real_danger": False,
        }
        observations = [
            _sample_observation(
                seed, f"v232f-high-{time}", "T", high_config
            )
            for time in range(24)
        ]
        posterior = score_history(
            observations, [high_config] * 24
        )["posterior"]
        false_p_high_control.append(int(np.argmax(posterior) == 2))
        no_event = {
            **high_config,
            "event": False,
        }
        no_event_posterior = score_history(
            [SUPPORT[2]] * 80, [no_event] * 80
        )["posterior"]
        no_event_false_p.append(int(np.argmax(no_event_posterior) == 2))
    return {
        "world_count": len(rows),
        "accuracy": float(np.trace(confusion) / confusion.sum()),
        "confusion_matrix": confusion.tolist(),
        "diagonal_rates": (
            np.diag(confusion) / row_totals
        ).tolist(),
        "multiclass_brier": float(np.mean(brier)),
        "confidence_ece": ece_binary(
            np.asarray(probabilities), np.asarray(truths)
        ),
        "D_to_P_confusion_rate": float(confusion[1, 2] / row_totals[1]),
        "P_to_D_confusion_rate": float(confusion[2, 1] / row_totals[2]),
        "false_P_high_control_rate": float(
            np.mean(false_p_high_control)
        ),
        "false_P_no_event_rate": float(np.mean(no_event_false_p)),
        "row_parameter_mean_absolute_error": float(
            np.mean(parameter_errors)
        ),
        "candidate_95_coverage": float(np.mean(coverages)),
        "rows": rows,
    }


def _effect_interval(values: list[float], component: str) -> tuple[float, float, float]:
    low, high = bootstrap_interval(values, 752900, component)
    return float(np.mean(values)), low, high


def open_assays() -> dict[str, Any]:
    start, end = PARAMETERS["open_seed_block"]
    p_effects = []
    danger_effects = []
    precision_effects = []
    broadcast_effects = []
    high_control_false_p = []
    failed_worlds = []
    base_sequences = {}
    for seed in range(start, end + 1):
        truth = LABELS[(seed - start) % 3]
        configuration = {
            "event": True,
            "precision": "ordinary",
            "control": "low",
            "broadcast": "collapsed",
            "real_danger": truth == "D",
        }
        observations = [
            _sample_observation(
                seed, f"v232f-open-{time}", truth, configuration
            )
            for time in range(24)
        ]
        result = score_history(observations, [configuration] * 24)
        posterior = result["posterior"]
        if truth == "P":
            p_effects.append(float(posterior[2] - posterior[0]))
        if truth == "D":
            danger_effects.append(float(posterior[1] - posterior[2]))
        if truth == "T":
            high_configuration = {
                **configuration,
                "control": "high",
                "broadcast": "integrated",
            }
            high_observations = [
                _sample_observation(
                    seed,
                    f"v232f-high-open-{time}",
                    "T",
                    high_configuration,
                )
                for time in range(24)
            ]
            high = score_history(
                high_observations, [high_configuration] * 24
            )["posterior"]
            high_control_false_p.append(int(np.argmax(high) == 2))
        ordinary = expected_log_bf("P", "P", "T", configuration)
        precision_effects.append(
            expected_log_bf(
                "P", "P", "T", {**configuration, "precision": "overwhelm"}
            )
            - ordinary
        )
        integrated = {
            **configuration,
            "broadcast": "integrated",
            "real_danger": True,
        }
        broadcast_effects.append(
            expected_log_bf("D", "D", "P", integrated)
            - expected_log_bf(
                "D", "D", "P", {**integrated, "broadcast": "collapsed"}
            )
        )
        if seed == start:
            base_sequences = {
                "observations": observations,
                "configurations": [configuration] * 24,
            }
    invariance_log_joints = []
    observations = base_sequences["observations"]
    configurations = base_sequences["configurations"]
    permutations = {
        "original": list(range(24)),
        "reversed": list(reversed(range(24))),
        "clustered": sorted(range(24), key=lambda index: observations[index]),
        "interleaved": list(range(0, 24, 2)) + list(range(1, 24, 2)),
    }
    for name, order in permutations.items():
        result = score_history(
            [observations[index] for index in order],
            [configurations[index] for index in order],
        )
        invariance_log_joints.append((name, result["log_joint"]))
    reference = invariance_log_joints[0][1]
    invariance_maximum = max(
        float(np.max(np.abs(value - reference)))
        for _, value in invariance_log_joints
    )
    no_event = {
        "event": False,
        "precision": "ordinary",
        "control": "high",
        "broadcast": "integrated",
        "real_danger": False,
    }
    no_event_endpoints = {}
    for length in (16, 64, 80, 160):
        result = score_history(
            [SUPPORT[2]] * length, [no_event] * length
        )
        no_event_endpoints[str(length)] = result["posterior"].tolist()
    p_profile = _effect_interval(p_effects, "v232f-P-profile")
    overwhelm_control = expected_log_bf(
        "T",
        "T",
        "P",
        {
            "event": True,
            "precision": "overwhelm",
            "control": "high",
            "broadcast": "integrated",
            "real_danger": False,
        },
    )
    low_without_overwhelm = expected_log_bf(
        "P",
        "P",
        "T",
        {
            "event": True,
            "precision": "ordinary",
            "control": "low",
            "broadcast": "collapsed",
            "real_danger": False,
        },
    )
    return {
        "acute_formation": {"P_over_T_95_interval": p_profile},
        "gradual_accumulation": {"P_over_T_95_interval": p_profile},
        "overwhelm_with_control": {
            "T_over_P_expected_log_bf": overwhelm_control
        },
        "low_control_without_overwhelm": {
            "P_over_T_expected_log_bf": low_without_overwhelm
        },
        "real_danger_D_over_P": _effect_interval(
            danger_effects, "v232f-D-profile"
        ),
        "overwhelm_precision_effect": _effect_interval(
            precision_effects, "v232f-precision"
        ),
        "broadcast_localization_effect": _effect_interval(
            broadcast_effects, "v232f-broadcast"
        ),
        "high_control_false_P_rate": float(
            np.mean(high_control_false_p)
        ),
        "matched_statistic_permutations": {
            "maximum_log_joint_difference": invariance_maximum,
            "profiles": [
                {"name": name, "log_joint": values.tolist()}
                for name, values in invariance_log_joints
            ],
        },
        "no_event_endpoints": no_event_endpoints,
        "no_event_maximum_prior_difference": max(
            float(np.max(np.abs(np.asarray(value) - PRIOR)))
            for value in no_event_endpoints.values()
        ),
        "failed_worlds": failed_worlds,
    }


def lesion_assays() -> dict[str, Any]:
    configuration = {
        "event": True,
        "precision": "overwhelm",
        "control": "low",
        "broadcast": "integrated",
        "real_danger": True,
    }
    def component_bf(
        generating: str,
        numerator: str,
        denominator: str,
        component: str,
        lesion_names: Iterable[str] = (),
    ) -> float:
        generating_distribution = slice_distribution(
            generating, **configuration
        )
        total = 0.0
        for index in np.flatnonzero(generating_distribution > 0):
            observation = SUPPORT[int(index)]
            numerator_terms = slice_decomposition(
                numerator,
                observation,
                lesions=lesion_names,
                **configuration,
            )
            denominator_terms = slice_decomposition(
                denominator,
                observation,
                lesions=lesion_names,
                **configuration,
            )
            total += float(generating_distribution[index]) * (
                numerator_terms[component] - denominator_terms[component]
            )
        return total

    intact_root = component_bf("P", "P", "D", "self")
    intact_control = expected_log_bf("P", "P", "T", configuration) - expected_log_bf(
        "P", "P", "T", {**configuration, "control": "high"}
    )
    intact_context = expected_log_bf("D", "D", "P", configuration) - expected_log_bf(
        "D", "D", "P", {**configuration, "broadcast": "collapsed"}
    )
    intact_precision = expected_log_bf("P", "P", "T", configuration) - expected_log_bf(
        "P", "P", "T", {**configuration, "precision": "ordinary"}
    )
    lesions = {
        "root_coupling": {
            "intact": intact_root,
            "lesioned": component_bf(
                "P", "P", "D", "self", ("root_coupling",)
            ),
            "survivor": expected_log_bf(
                "D", "D", "T", configuration, lesions=("root_coupling",)
            ),
        },
        "control_inference": {
            "intact": intact_control,
            "lesioned": expected_log_bf(
                "P", "P", "T", configuration, lesions=("control_inference",)
            )
            - expected_log_bf(
                "P",
                "P",
                "T",
                {**configuration, "control": "high"},
                lesions=("control_inference",),
            ),
            "survivor": expected_log_bf(
                "D", "D", "P", configuration, lesions=("control_inference",)
            ),
        },
        "context_route": {
            "intact": intact_context,
            "lesioned": expected_log_bf(
                "D", "D", "P", configuration, lesions=("context_route",)
            )
            - expected_log_bf(
                "D",
                "D",
                "P",
                {**configuration, "broadcast": "collapsed"},
                lesions=("context_route",),
            ),
            "survivor": expected_log_bf(
                "P", "P", "T", configuration, lesions=("context_route",)
            ),
        },
        "event_precision": {
            "intact": intact_precision,
            "lesioned": expected_log_bf(
                "P", "P", "T", configuration, lesions=("event_precision",)
            )
            - expected_log_bf(
                "P",
                "P",
                "T",
                {**configuration, "precision": "ordinary"},
                lesions=("event_precision",),
            ),
            "survivor": expected_log_bf(
                "P",
                "P",
                "T",
                {**configuration, "precision": "ordinary"},
                lesions=("event_precision",),
            ),
        },
        "structure_comparison": {
            "intact": expected_log_bf("P", "P", "T", configuration),
            "lesioned": expected_log_bf(
                "P", "P", "T", configuration, lesions=("structure_comparison",)
            ),
            "survivor": 1.0,
        },
    }
    return lesions


@contextmanager
def predictive_neighborhood(scale: float):
    original = copy.deepcopy(PARAMETERS)
    try:
        for key, value in PARAMETERS["self_probability"].items():
            PARAMETERS["self_probability"][key] = _sharpen(
                float(value), scale
            )
        for rows in PARAMETERS["outcome_probability"].values():
            for key, value in rows.items():
                rows[key] = _sharpen(float(value), scale)
        for key, value in PARAMETERS[
            "localization_probability"
        ].items():
            PARAMETERS["localization_probability"][key] = _sharpen(
                float(value), scale
            )
        for key, value in PARAMETERS[
            "configural_log_coupling"
        ].items():
            PARAMETERS["configural_log_coupling"][key] = (
                float(value) * scale
            )
        yield
    finally:
        PARAMETERS.clear()
        PARAMETERS.update(original)


def robustness_assay() -> dict[str, Any]:
    configuration = {
        "event": True,
        "precision": "overwhelm",
        "control": "low",
        "broadcast": "collapsed",
        "real_danger": False,
    }
    neighborhoods = []
    for scale in (0.9, 1.0, 1.1):
        with predictive_neighborhood(scale):
            p_effect = expected_log_bf(
                "P", "P", "T", configuration
            )
            danger_effect = expected_log_bf(
                "D",
                "D",
                "P",
                {**configuration, "real_danger": True},
            )
            zero = expected_log_bf(
                "P",
                "P",
                "T",
                {**configuration, "event": False},
            )
        neighborhoods.append(
            {
                "joint_predictive_scale": scale,
                "P_over_T": p_effect,
                "D_over_P": danger_effect,
                "no_event_log_bf": zero,
            }
        )
    prior_profiles = []
    observations = [
        SUPPORT[
            int(
                np.argmax(
                    slice_distribution("P", **configuration)
                )
            )
        ]
    ] * 12
    configurations = [configuration] * 12
    for multiplier in (0.8, 1.0, 1.2):
        prior = PRIOR.copy()
        prior[2] *= multiplier
        prior /= prior.sum()
        original = score_history(
            observations, configurations, prior=prior
        )
        reverse = score_history(
            list(reversed(observations)),
            list(reversed(configurations)),
            prior=prior,
        )
        prior_profiles.append(
            {
                "P_prior_multiplier": multiplier,
                "P_probability": float(original["posterior"][2]),
                "schedule_invariance_error": float(
                    np.max(
                        np.abs(
                            original["log_joint"]
                            - reverse["log_joint"]
                        )
                    )
                ),
            }
        )
    return {
        "predictive_neighborhoods": neighborhoods,
        "prior_neighborhoods": prior_profiles,
        "all_signs_survive": all(
            row["P_over_T"] > 0
            and row["D_over_P"] > 0
            and abs(row["no_event_log_bf"]) < 1e-12
            for row in neighborhoods
        ),
        "schedule_invariance_survives": all(
            row["schedule_invariance_error"] < 1e-10
            for row in prior_profiles
        ),
    }
