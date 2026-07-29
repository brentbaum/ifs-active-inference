"""Independently authored exact oracle for V2.6b."""

from __future__ import annotations

from typing import Sequence

import numpy as np


def enumerate_forecasts(
    observations: Sequence[
        tuple[
            bool,
            int | None,
            int | None,
            int | None,
            int | None,
            float,
        ]
    ],
    trust_prior_input: Sequence[float],
    outcome_prior_input: Sequence[float],
    outcome_support_input: Sequence[float],
    default_reliability: float,
) -> tuple[tuple[np.ndarray, np.ndarray, np.ndarray], np.ndarray]:
    """Cartesian two-state updates; all inputs are copied."""
    trust_prior = np.array(trust_prior_input, dtype=float, copy=True)
    outcome_prior = np.array(outcome_prior_input, dtype=float, copy=True)
    support = np.array(outcome_support_input, dtype=float, copy=True)
    posteriors = [trust_prior / trust_prior.sum() for _ in range(3)]
    q_outcome = outcome_prior / outcome_prior.sum()
    for refusal, partner, outcome, coprotection, policy_outcome, response_rel in observations:
        values = (
            outcome,
            coprotection,
            partner if refusal else None,
        )
        reliabilities = (
            default_reliability,
            default_reliability,
            response_rel,
        )
        for axis, (observed, reliability) in enumerate(
            zip(values, reliabilities)
        ):
            likelihood = np.ones(2, dtype=float)
            if observed is not None:
                likelihood = np.asarray(
                    [
                        reliability
                        if int(observed) == state
                        else 1.0 - reliability
                        for state in (0, 1)
                    ]
                )
            posteriors[axis] *= likelihood
            posteriors[axis] /= posteriors[axis].sum()
        if policy_outcome is not None:
            likelihood = np.asarray(
                [
                    value if int(policy_outcome) else 1.0 - value
                    for value in support
                ]
            )
            q_outcome *= likelihood
            q_outcome /= q_outcome.sum()
    return (
        posteriors[0],
        posteriors[1],
        posteriors[2],
    ), q_outcome


def enumerate_policy(
    expected_cost_input: Sequence[float],
    inverse_temperature: float,
) -> np.ndarray:
    """Independent finite-policy normalization from copied costs."""
    costs = np.array(expected_cost_input, dtype=float, copy=True)
    weights = np.exp(
        -float(inverse_temperature) * (costs - float(costs.min()))
    )
    return weights / weights.sum()
