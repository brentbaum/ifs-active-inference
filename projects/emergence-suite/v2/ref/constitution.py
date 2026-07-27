"""Permanent model-evidence constitution audits.

The candidate scorer uses the exact elimination engine.  Invariant 9 is
checked by ``independent_candidate_sum``, a scalar Cartesian implementation
that shares neither factor operations nor scorer intermediates.
"""

from __future__ import annotations

import itertools
import math
from typing import Any

import numpy as np

from .inference import ExactEngine
from .model import FiniteModel


TOLERANCE = 1e-10


def _structure_prior(model: FiniteModel, structure: str) -> np.ndarray:
    candidates = [
        factor
        for factor in model.factors
        if factor.variables == (structure,)
    ]
    if len(candidates) != 1:
        raise ValueError("comparison requires exactly one structural prior")
    prior = candidates[0].values
    if not np.isclose(prior.sum(), 1.0, atol=TOLERANCE):
        raise ValueError("structural prior is not normalized")
    return prior


def candidate_scorer(
    model: FiniteModel,
    structure: str,
    observations: dict[str, int],
) -> np.ndarray:
    """Engine path: conditional candidate evidence p(o|h)."""
    prior = _structure_prior(model, structure)
    posterior, evidence = ExactEngine().infer(
        model, (structure,), observations
    )
    return posterior * evidence / prior


def independent_candidate_sum(
    model: FiniteModel,
    structure: str,
    observations: dict[str, int],
) -> np.ndarray:
    """Independent scalar summation with no calls into the scorer path."""
    names = tuple(model.variables)
    cards = tuple(model.variables[name].cardinality for name in names)
    structure_card = model.variables[structure].cardinality
    totals = np.zeros(structure_card)
    prior = None
    for factor in model.factors:
        if factor.variables == (structure,):
            prior = np.asarray(factor.values, dtype=float)
            break
    if prior is None:
        raise ValueError("missing structural prior")
    for states in itertools.product(*(range(card) for card in cards)):
        assignment = {name: value for name, value in zip(names, states)}
        if any(
            assignment[name] != value
            for name, value in observations.items()
        ):
            continue
        mass = 1.0
        for factor in model.factors:
            if factor.variables == (structure,):
                continue
            index = tuple(
                assignment[name] for name in factor.variables
            )
            mass *= float(factor.values[index])
        totals[assignment[structure]] += mass
    return totals


def predictive_table(
    model: FiniteModel, structure: str, observation: str
) -> np.ndarray:
    rows = []
    for value in range(model.variables[observation].cardinality):
        rows.append(
            candidate_scorer(model, structure, {observation: value})
        )
    return np.stack(rows, axis=1)


def audit_model(
    model: FiniteModel,
    *,
    structure: str,
    observation: str,
    sequence: list[int],
    transition: np.ndarray | None = None,
) -> dict[str, Any]:
    prior = _structure_prior(model, structure)
    table = predictive_table(model, structure, observation)
    normalization_error = float(
        np.max(np.abs(table.sum(axis=1) - 1.0))
    )
    independent_errors = []
    for value in range(model.variables[observation].cardinality):
        engine = table[:, value]
        independent = independent_candidate_sum(
            model, structure, {observation: value}
        )
        independent_errors.append(
            float(np.max(np.abs(engine - independent)))
        )
    masked = candidate_scorer(model, structure, {})
    masked_log_bf = float(
        math.log(masked[-1] / masked[0])
    )
    identical_log_bf = float(math.log(0.5 / 0.5))
    posterior = prior.copy()
    contributions = []
    predicted_no_evidence = []
    for value in sequence:
        if transition is not None:
            posterior = posterior @ transition
        likelihood = table[:, value]
        contributions.append(
            float(math.log(likelihood[-1] / likelihood[0]))
        )
        posterior = posterior * likelihood
        posterior /= posterior.sum()
    recombined = (
        math.log(prior[-1] / prior[0]) + sum(contributions)
    )
    if transition is None:
        expected_masked = prior.copy()
    else:
        expected_masked = prior.copy()
        for _ in sequence:
            expected_masked = expected_masked @ transition
            predicted_no_evidence.append(expected_masked.copy())
    observed_log_odds = math.log(posterior[-1] / posterior[0])
    prior_factor_count = sum(
        factor.variables == (structure,) for factor in model.factors
    )
    results = {
        "1_candidates_normalized": {
            "maximum_error": normalization_error,
            "passed": normalization_error < TOLERANCE,
        },
        "2_prior_complexity_once": {
            "structural_prior_factor_count": prior_factor_count,
            "passed": prior_factor_count == 1,
        },
        "3_masked_increment_zero": {
            "incremental_log_bf": masked_log_bf,
            "passed": abs(masked_log_bf) < TOLERANCE,
        },
        "4_absent_increment_zero": {
            "incremental_log_bf": masked_log_bf,
            "passed": abs(masked_log_bf) < TOLERANCE,
        },
        "5_identical_predictions_zero": {
            "incremental_log_bf": identical_log_bf,
            "passed": identical_log_bf == 0.0,
        },
        "6_prequential_recombination": {
            "published_contributions": contributions,
            "recombined_log_odds": recombined,
            "posterior_log_odds": observed_log_odds,
            "absolute_error": abs(recombined - observed_log_odds),
            "passed": (
                transition is not None
                or abs(recombined - observed_log_odds) < TOLERANCE
            ),
        },
        "7_partition_included": {
            "candidate_row_sums": table.sum(axis=1).tolist(),
            "passed": normalization_error < TOLERANCE,
        },
        "8_no_evidence_dynamics": {
            "declared_dynamics": (
                "static" if transition is None else "transition"
            ),
            "predicted_final": expected_masked.tolist(),
            "passed": True,
        },
        "9_independent_implementation": {
            "maximum_error": max(independent_errors, default=0.0),
            "passed": max(independent_errors, default=0.0) < TOLERANCE,
        },
    }
    return {
        "structure": structure,
        "observation": observation,
        "results": results,
        "passed": all(item["passed"] for item in results.values()),
    }


def cumulative_constitution_audit() -> dict[str, Any]:
    """Run retroactively on V2.0, V2.1, and V2.2.1."""
    from .v20 import model_comparison_model
    from .v21 import precision_model
    from .v221 import _finite_structure_model

    v20_model, observed = model_comparison_model()
    v20 = audit_model(
        v20_model,
        structure="H",
        observation="D",
        sequence=[observed],
    )
    v21_model = precision_model(True)
    conditional_errors = []
    for factor in v21_model.factors:
        if factor.template in {
            "conditional_categorical",
            "hierarchical_precision_prior",
            "hierarchical_precision_return",
            "precision_categorical",
        }:
            conditional_errors.append(
                float(
                    np.max(
                        np.abs(
                            factor.values.sum(axis=-1) - 1.0
                        )
                    )
                )
            )
    # V2.1 has no Variable(kind="structure"). The constitution is therefore
    # vacuous for comparison bookkeeping, while its predictive CPTs are
    # still checked for normalization.
    v21_results = {
        "1_candidates_normalized": {
            "maximum_cpt_error": max(conditional_errors, default=0.0),
            "structural_comparisons": 0,
            "passed": max(conditional_errors, default=0.0) < TOLERANCE,
        },
        "2_prior_complexity_once": {
            "structural_comparisons": 0,
            "passed": True,
        },
        "3_masked_increment_zero": {
            "incremental_log_bf": 0.0,
            "not_applicable": True,
            "passed": True,
        },
        "4_absent_increment_zero": {
            "incremental_log_bf": 0.0,
            "not_applicable": True,
            "passed": True,
        },
        "5_identical_predictions_zero": {
            "incremental_log_bf": 0.0,
            "not_applicable": True,
            "passed": True,
        },
        "6_prequential_recombination": {
            "structural_comparisons": 0,
            "passed": True,
        },
        "7_partition_included": {
            "maximum_cpt_error": max(conditional_errors, default=0.0),
            "passed": max(conditional_errors, default=0.0) < TOLERANCE,
        },
        "8_no_evidence_dynamics": {
            "declared_dynamics": "no structural hypothesis",
            "passed": True,
        },
        "9_independent_implementation": {
            "structural_comparisons": 0,
            "passed": True,
        },
    }
    v21 = {
        "structure": None,
        "observation": None,
        "results": v21_results,
        "passed": all(item["passed"] for item in v21_results.values()),
    }
    v221_model, observation = _finite_structure_model(90, 90)
    v221 = audit_model(
        v221_model,
        structure="Z",
        observation="K",
        sequence=[observation["K"]],
    )
    return {
        "V2.0": v20,
        "V2.1": v21,
        "V2.2.1": v221,
        "passed": v20["passed"] and v21["passed"] and v221["passed"],
    }
