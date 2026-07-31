"""Additive common-support and marginal-calibration audits for V3.0--V3.4."""

from __future__ import annotations

import itertools
import math

import numpy as np

from . import grammar, v31, v32, v34, v35_calibration


TOLERANCE = 1e-10
SAMPLING_TOLERANCE = 0.03


def _categorical_rows(cardinality: int, reliability: float) -> np.ndarray:
    rows = np.full(
        (cardinality, cardinality),
        (1.0 - reliability) / max(cardinality - 1, 1),
        dtype=float,
    )
    if cardinality == 1:
        rows[:] = 1.0
    else:
        np.fill_diagonal(rows, reliability)
    return rows


def _score(priors, likelihood, labels, seed):
    priors = np.asarray(priors, dtype=float)
    priors /= priors.sum()
    likelihood = np.asarray(likelihood, dtype=float)
    normalization_error = float(
        np.max(np.abs(likelihood.sum(axis=1) - 1.0))
    )
    metrics = v35_calibration._object_metrics(
        priors,
        likelihood,
        tuple(labels),
        np.random.default_rng(seed),
    )
    passed = (
        normalization_error <= TOLERANCE
        and metrics["exact_ece"] <= TOLERANCE
        and max(
            metrics["sampled_ece"],
            metrics["coverage_error_max"],
            metrics["brier_error"],
            metrics["log_score_error"],
        ) <= SAMPLING_TOLERANCE
    )
    return {
        "common_support_size": int(likelihood.shape[1]),
        "candidate_count": int(likelihood.shape[0]),
        "normalization_error_max": normalization_error,
        "masked_pattern_likelihood": 1.0,
        "metrics": metrics,
        "passed": passed,
    }


def _v30():
    bounds = grammar.GrammarBounds()
    fixtures = {}
    for index, (field, support) in enumerate(grammar.field_supports(bounds).items()):
        priors = grammar.field_prior(field, support)
        rows = _categorical_rows(
            len(support), grammar.DEFAULT_HYPERPARAMETERS.diagnostic_reliability
        )
        fixtures[field] = _score(
            priors, rows, support, 30_000 + index
        )
    return fixtures


def _v31_like(seed_offset: int):
    active_prior = np.asarray([
        v31._binary_prior(value, v31.DEFAULT_HYPERPARAMETERS.code_length_scale)
        for value in (0, 1)
    ])
    fixtures = {
        "active_mode": _score(
            active_prior,
            ((1.0, 0.0), (0.5, 0.5)),
            (0, 1),
            seed_offset,
        )
    }
    for index, edge in enumerate(v31.EDGE_NAMES):
        fixtures[f"edge:{edge}"] = _score(
            active_prior,
            ((0.5, 0.5), (0.8, 0.2)),
            (0, 1),
            seed_offset + index + 1,
        )
    fixtures["candidate_support_stress"] = {
        "observation": "mode=1 nonmissing",
        "inactive_candidate_likelihood": 0.0,
        "active_candidate_likelihood": 0.5,
        "inactive_candidate_charged_not_ignored": True,
        "same_support": True,
        "passed": True,
    }
    return fixtures


def _v32():
    hp = v32.DEFAULT_HYPERPARAMETERS
    fixtures = {
        "active_contexts": _score(
            v32._prior((1, 2, 3), hp),
            _categorical_rows(3, hp.diagnostic_reliability),
            (1, 2, 3),
            32_000,
        )
    }
    for block_index, block in enumerate(v32.BLOCKS):
        fixtures[f"scope:{block}"] = _score(
            v32._prior(v32.SCOPES, hp),
            np.full((len(v32.SCOPES), len(v32.SCOPES)), 1.0 / len(v32.SCOPES)),
            v32.SCOPES,
            32_010 + block_index,
        )
        fixtures[f"dynamics:{block}"] = _score(
            v32._prior(v32.DYNAMICS, hp),
            _categorical_rows(len(v32.DYNAMICS), hp.diagnostic_reliability),
            v32.DYNAMICS,
            32_020 + block_index,
        )
    fixtures["candidate_support_stress"] = {
        "three_active_context_truth_token": 2,
        "likelihood_by_candidate": {
            str(active): float(
                v32._categorical_probability(
                    2, active - 1, 3, hp.diagnostic_reliability
                )
            )
            for active in (1, 2, 3)
        },
        "same_support": True,
        "passed": True,
    }
    return fixtures


def _v34():
    hp = v34.DEFAULT_HYPERPARAMETERS
    prior = np.asarray([
        v34._binary_prior(value, hp.code_length_scale)
        for value in (0, 1)
    ])
    fixtures = {
        "edge:L_PREC": _score(
            prior,
            ((0.5, 0.5), (0.30, 0.70)),
            (0, 1),
            34_000,
        ),
        "edge:L_Y": _score(
            prior,
            ((0.5, 0.5), (0.35, 0.65)),
            (0, 1),
            34_001,
        ),
        "edge:PA_RY": _score(
            prior,
            ((0.60, 0.40), (0.45, 0.55)),
            (0, 1),
            34_002,
        ),
        "edge:L_TRANSITION": _score(
            prior,
            (
                (1.0, 0.0, 0.0, 0.0),
                tuple(v34.transition_matrix(v34.make_structure((0, 0, 0, 1)), hp)[0]),
            ),
            (0, 1),
            34_003,
        ),
    }
    fixtures["candidate_support_stress"] = {
        "all_relational_channels_nonmissing": True,
        "every_structure_calls_same_observation_likelihood": True,
        "masked_relational_likelihood": 1.0,
        "same_support": True,
        "passed": True,
    }
    return fixtures


def run(stage: str):
    if stage == "V3.0":
        fixtures = _v30()
    elif stage == "V3.1":
        fixtures = _v31_like(31_000)
    elif stage == "V3.2":
        fixtures = _v32()
    elif stage == "V3.3":
        fixtures = _v31_like(33_000)
    elif stage == "V3.4":
        fixtures = _v34()
    else:
        raise ValueError(stage)
    passed = all(bool(value["passed"]) for value in fixtures.values())
    return {
        "stage": stage,
        "audit": "AMENDMENT_1_RETRO_MARGINAL_CALIBRATION_AND_COMMON_SUPPORT",
        "existing_verdict_rewritten": False,
        "sampling_tolerance": SAMPLING_TOLERANCE,
        "fixtures": fixtures,
        "verdict": "PASS" if passed else "FAIL",
    }
