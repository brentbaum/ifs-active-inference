"""Permanent V3.5 marginal-calibration and common-support audit."""

from __future__ import annotations

import itertools
import math
from typing import Any, Callable, Sequence

import numpy as np

from . import v35


SAMPLE_SIZE = 50_000
SAMPLING_TOLERANCE = 0.03
COVERAGE_LEVELS = (0.50, 0.80, 0.90, 0.95)


def _components():
    result = []
    priors = []
    for structure in v35.PROGRAMS:
        signs = (-1, 1) if structure.cross_mode_outcome else (0,)
        for sign in signs:
            for partner in (0, 1):
                result.append((structure, sign, partner))
                priors.append(
                    math.exp(v35.structure_log_prior(structure))
                    / len(signs)
                    / 2.0
                )
    return tuple(result), np.asarray(priors, dtype=float)


def _full_tables():
    components, priors = _components()
    observations = tuple(
        itertools.product(
            range(3), itertools.product((0, 1), repeat=5), range(3), range(2)
        )
    )
    likelihood = np.empty((len(components), len(observations)), dtype=float)
    for h, (structure, sign, partner) in enumerate(components):
        truth_active = structure.active_modes - 1
        truth_edges = tuple(v35.program_values(structure).values())
        truth_sign = 0 if sign == 0 else 1 if sign < 0 else 2
        for o, (active_obs, edge_obs, sign_obs, partner_obs) in enumerate(observations):
            value = 0.80 if active_obs == truth_active else 0.10
            for observed, truth in zip(edge_obs, truth_edges):
                value *= 0.82 if observed == truth else 0.18
            value *= 0.80 if sign_obs == truth_sign else 0.10
            value *= 0.86 if partner_obs == partner else 0.14
            likelihood[h, o] = value
    return components, priors, observations, likelihood


def joint_tables():
    components, priors, observations, likelihood = _full_tables()
    evidence = priors @ likelihood
    posterior = priors[:, None] * likelihood / evidence[None, :]
    return {
        "components": components,
        "priors": priors,
        "observations": observations,
        "likelihoods": likelihood,
        "posterior_by_observation": posterior.T,
    }


def _object_metrics(
    priors: np.ndarray,
    likelihood: np.ndarray,
    labels: Sequence[Any],
    rng: np.random.Generator,
) -> dict[str, Any]:
    unique = tuple(dict.fromkeys(labels))
    label_index = {value: index for index, value in enumerate(unique)}
    observation_probability = priors @ likelihood
    posterior_h = priors[:, None] * likelihood / observation_probability[None, :]
    posterior = np.zeros((len(unique), likelihood.shape[1]), dtype=float)
    for h, label in enumerate(labels):
        posterior[label_index[label]] += posterior_h[h]
    joint = priors[:, None] * likelihood
    joint_object = np.zeros_like(posterior)
    for h, label in enumerate(labels):
        joint_object[label_index[label]] += joint[h]
    predicted = np.argmax(posterior, axis=0)
    confidence = posterior[predicted, np.arange(posterior.shape[1])]
    exact_ece = math.fsum(
        abs(
            float(joint_object[predicted[o], o])
            - float(observation_probability[o] * confidence[o])
        )
        for o in range(posterior.shape[1])
    )
    exact_coverage = {}
    retained_sets: dict[float, list[set[int]]] = {}
    for level in COVERAGE_LEVELS:
        sets = []
        coverage = 0.0
        for o in range(posterior.shape[1]):
            retained: set[int] = set()
            cumulative = 0.0
            for index in np.argsort(-posterior[:, o]):
                retained.add(int(index))
                cumulative += float(posterior[int(index), o])
                if cumulative >= level:
                    break
            sets.append(retained)
            coverage += math.fsum(
                float(joint_object[index, o]) for index in retained
            )
        retained_sets[level] = sets
        exact_coverage[str(level)] = float(coverage)
    exact_brier = math.fsum(
        float(joint_object[truth, o])
        * float(
            np.square(posterior[:, o]).sum()
            - 2.0 * posterior[truth, o]
            + 1.0
        )
        for truth in range(len(unique))
        for o in range(posterior.shape[1])
    )
    exact_log = -math.fsum(
        float(joint_object[truth, o])
        * math.log(float(posterior[truth, o]))
        for truth in range(len(unique))
        for o in range(posterior.shape[1])
        if joint_object[truth, o] > 0
    )
    flat = joint_object.reshape(-1)
    draws = rng.choice(flat.size, size=SAMPLE_SIZE, p=flat)
    truths, observed = np.unravel_index(draws, joint_object.shape)
    sampled_correct = predicted[observed] == truths
    sampled_ece = 0.0
    rounded = np.round(confidence[observed], 12)
    for value in np.unique(rounded):
        selected = rounded == value
        sampled_ece += float(selected.mean()) * abs(
            float(confidence[observed][selected].mean())
            - float(sampled_correct[selected].mean())
        )
    sampled_coverage = {
        str(level): float(np.mean([
            int(int(truth) in retained_sets[level][int(o)])
            for truth, o in zip(truths, observed)
        ]))
        for level in COVERAGE_LEVELS
    }
    sampled_brier = float(np.mean([
        np.square(posterior[:, int(o)]).sum()
        - 2.0 * posterior[int(truth), int(o)]
        + 1.0
        for truth, o in zip(truths, observed)
    ]))
    sampled_log = float(np.mean([
        -math.log(float(posterior[int(truth), int(o)]))
        for truth, o in zip(truths, observed)
    ]))
    return {
        "class_count": len(unique),
        "exact_ece": float(exact_ece),
        "sampled_ece": float(sampled_ece),
        "exact_coverage": exact_coverage,
        "sampled_coverage": sampled_coverage,
        "coverage_error_max": max(
            abs(sampled_coverage[key] - exact_coverage[key])
            for key in exact_coverage
        ),
        "exact_brier": float(exact_brier),
        "sampled_brier": sampled_brier,
        "brier_error": abs(sampled_brier - exact_brier),
        "exact_log_score": float(exact_log),
        "sampled_log_score": sampled_log,
        "log_score_error": abs(sampled_log - exact_log),
    }


def _active_count_predictive(mask_registration: bool):
    observations = tuple(
        itertools.product((0, 1), repeat=2 if mask_registration else 4)
    )
    likelihood = np.empty((3, len(observations)), dtype=float)
    for active in (1, 2, 3):
        for o, values in enumerate(observations):
            cursor = 0
            value = 1.0
            for slot in (1, 2):
                signal = values[cursor]
                cursor += 1
                if slot < active:
                    if mask_registration:
                        value *= 0.5
                    else:
                        registration = values[cursor]
                        cursor += 1
                        value *= math.fsum(
                            0.5
                            * v35.mode_signal_probability(signal, mode)
                            * v35.registration_probability(registration, mode)
                            for mode in (0, 1)
                        )
                else:
                    value *= v35.mode_signal_probability(signal, 0)
                    if not mask_registration:
                        registration = values[cursor]
                        cursor += 1
                        value *= v35.registration_probability(registration, 0)
            likelihood[active - 1, o] = value
    priors = np.asarray([0.5, 0.3, 0.2], dtype=float)
    return priors, likelihood


def run() -> dict[str, Any]:
    components, priors, _observations, likelihood = _full_tables()
    normalization_error = float(np.max(np.abs(likelihood.sum(axis=1) - 1.0)))
    rng = np.random.default_rng(35_000_017)
    objects: dict[str, Any] = {
        "full_structure": _object_metrics(
            priors,
            likelihood,
            [component[0] for component in components],
            rng,
        ),
        "active_mode_count": _object_metrics(
            priors,
            likelihood,
            [component[0].active_modes for component in components],
            rng,
        ),
        "cross_mode_sign": _object_metrics(
            priors, likelihood, [component[1] for component in components], rng
        ),
        "partner_state": _object_metrics(
            priors, likelihood, [component[2] for component in components], rng
        ),
    }
    for edge in v35.EDGE_NAMES:
        objects[f"edge:{edge}"] = _object_metrics(
            priors,
            likelihood,
            [v35.program_values(component[0])[edge] for component in components],
            rng,
        )
    stratification = {}
    for name, masked in (("fully_observed", False), ("registration_masked", True)):
        active_priors, active_likelihood = _active_count_predictive(masked)
        stratification[name] = {
            "support_normalization_error": float(
                np.max(np.abs(active_likelihood.sum(axis=1) - 1.0))
            ),
            "metrics": _object_metrics(
                active_priors,
                active_likelihood,
                (1, 2, 3),
                rng,
            ),
            "truth_strata": {
                str(active): {
                    "prior_mass": float(active_priors[active - 1]),
                    "support_size": int(active_likelihood.shape[1]),
                }
                for active in (1, 2, 3)
            },
        }
    stress_observation = ((1, 1), (1, 1), (1, 1))
    stress_likelihoods = {}
    for active in (1, 2, 3):
        value = 1.0
        for index, (signal, registration) in enumerate(stress_observation):
            if index < active:
                value *= math.fsum(
                    0.5
                    * v35.mode_signal_probability(signal, mode)
                    * v35.registration_probability(registration, mode)
                    for mode in (0, 1)
                )
            else:
                value *= v35.mode_signal_probability(signal, 0)
                value *= v35.registration_probability(registration, 0)
            value *= v35.support_probability(1, 0, 0)
        stress_likelihoods[str(active)] = float(value)
    sampling_errors = [
        metric[key]
        for metric in objects.values()
        for key in ("sampled_ece", "coverage_error_max", "brier_error", "log_score_error")
    ]
    return {
        "sample_size": SAMPLE_SIZE,
        "sampling_tolerance": SAMPLING_TOLERANCE,
        "common_support": {
            "support_size": int(likelihood.shape[1]),
            "candidate_count": int(likelihood.shape[0]),
            "normalization_error_max": normalization_error,
        },
        "objects": objects,
        "stratification": stratification,
        "candidate_support_stress": {
            "truth_active_modes": 3,
            "higher_slot_channels_nonmissing": True,
            "candidate_likelihoods": stress_likelihoods,
            "all_candidates_finite_positive": all(
                value > 0 and math.isfinite(value)
                for value in stress_likelihoods.values()
            ),
        },
        "max_sampling_error": float(max(sampling_errors)),
        "passed": (
            normalization_error <= v35.TOLERANCE
            and all(
                cell["support_normalization_error"] <= v35.TOLERANCE
                for cell in stratification.values()
            )
            and all(
                metric["exact_ece"] <= v35.TOLERANCE
                for metric in objects.values()
            )
            and max(sampling_errors) <= SAMPLING_TOLERANCE
            and all(value > 0 for value in stress_likelihoods.values())
        ),
    }
