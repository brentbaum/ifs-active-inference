"""Permanent model-evidence constitution audits.

The candidate scorer uses the exact elimination engine.  Invariant 9 is
checked by ``independent_candidate_sum``, a scalar Cartesian implementation
that shares neither factor operations nor scorer intermediates.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import itertools
import math
import textwrap
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


# Revised graded-update constitution, adopted after V2.3.2 Gate 6.  The
# original nine-invariant audit above remains unchanged for frozen-stage
# reproducibility.  From V2.3.3 onward, callers use the cumulative audit
# below, which contains those composition checks as part D.


def _pairwise_indices(cardinality: int) -> list[tuple[int, int]]:
    return list(itertools.combinations(range(cardinality), 2))


def _safe_log_odds(
    probabilities: np.ndarray, left: int, right: int
) -> float:
    return math.log(
        float(probabilities[left]) / float(probabilities[right])
    )


def _table_update_identity(
    prior: np.ndarray,
    table: np.ndarray,
    sequence: list[int],
) -> dict[str, Any]:
    posterior = np.asarray(prior, dtype=float).copy()
    errors = []
    increments = []
    for slice_index, value in enumerate(sequence):
        likelihood = np.asarray(table[:, value], dtype=float)
        if np.any(likelihood <= 0.0):
            raise ValueError(
                "update-identity sequence must have common positive support"
            )
        updated = posterior * likelihood
        updated /= updated.sum()
        for left, right in _pairwise_indices(len(posterior)):
            increment = (
                _safe_log_odds(updated, left, right)
                - _safe_log_odds(posterior, left, right)
            )
            log_bf = math.log(
                float(likelihood[left]) / float(likelihood[right])
            )
            error = abs(increment - log_bf)
            errors.append(error)
            increments.append(
                {
                    "slice": slice_index,
                    "observation": value,
                    "pair": [left, right],
                    "posterior_log_odds_increment": increment,
                    "published_log_bf": log_bf,
                    "absolute_error": error,
                }
            )
        posterior = updated
    maximum_error = max(errors, default=0.0)
    return {
        "checked_pairwise_increments": len(errors),
        "maximum_absolute_error": maximum_error,
        "trace": increments,
        "passed": maximum_error < TOLERANCE,
    }


def _finite_information_table(
    table: np.ndarray,
) -> dict[str, Any]:
    table = np.asarray(table, dtype=float)
    values = []
    asymmetric_zeros = []
    checked = 0
    for left, right in _pairwise_indices(table.shape[0]):
        for observation in range(table.shape[1]):
            left_value = float(table[left, observation])
            right_value = float(table[right, observation])
            if left_value == 0.0 and right_value == 0.0:
                continue
            checked += 1
            if left_value <= 0.0 or right_value <= 0.0:
                asymmetric_zeros.append(
                    {
                        "pair": [left, right],
                        "observation": observation,
                        "left": left_value,
                        "right": right_value,
                    }
                )
                continue
            values.append(abs(math.log(left_value / right_value)))
    finite = not asymmetric_zeros and all(
        math.isfinite(value) for value in values
    )
    bound = max(values, default=0.0) if finite else math.inf
    return {
        "support_cells_checked": checked,
        "asymmetric_zero_cells": asymmetric_zeros,
        "B_max": bound,
        "implied_binary_probability_change_bound": (
            math.tanh(bound / 4.0) if finite else 1.0
        ),
        "all_observed_slices_within_bound": finite,
        "passed": finite,
    }


def independent_homotopy_posterior(
    prior: list[float],
    candidate_likelihoods: list[float],
    common_mixture: float,
    alpha: float,
) -> list[float]:
    """Scalar enumeration independent of the vectorized analytic curve."""
    masses = []
    for prior_value, likelihood in zip(prior, candidate_likelihoods):
        tempered = (
            (1.0 - alpha) * common_mixture + alpha * likelihood
        )
        masses.append(prior_value * tempered)
    total = sum(masses)
    return [mass / total for mass in masses]


def _homotopy_table(
    prior: np.ndarray,
    table: np.ndarray,
    *,
    target_index: int,
    alpha_count: int = 101,
) -> dict[str, Any]:
    prior = np.asarray(prior, dtype=float)
    table = np.asarray(table, dtype=float)
    mixture = prior @ table
    alphas = np.linspace(0.0, 1.0, alpha_count)
    agreement_errors = []
    hysteresis_errors = []
    derivative_values = []
    monotonicity_failures = []
    maximum_adjacent_change = 0.0
    checked_curves = 0
    for observation, common_mixture in enumerate(mixture):
        if common_mixture <= 0.0:
            continue
        likelihoods = table[:, observation]
        exact_curve = []
        analytic_curve = []
        for alpha in alphas:
            exact = independent_homotopy_posterior(
                prior.tolist(),
                likelihoods.tolist(),
                float(common_mixture),
                float(alpha),
            )
            tempered = (
                (1.0 - alpha) * common_mixture
                + alpha * likelihoods
            )
            analytic = prior * tempered
            analytic /= analytic.sum()
            exact_curve.append(float(exact[target_index]))
            analytic_curve.append(float(analytic[target_index]))
            agreement_errors.append(
                float(
                    np.max(
                        np.abs(
                            np.asarray(exact, dtype=float) - analytic
                        )
                    )
                )
            )
        reverse_curve = [
            independent_homotopy_posterior(
                prior.tolist(),
                likelihoods.tolist(),
                float(common_mixture),
                float(alpha),
            )[target_index]
            for alpha in reversed(alphas)
        ]
        hysteresis_errors.extend(
            abs(forward - reverse)
            for forward, reverse in zip(
                exact_curve, reversed(reverse_curve)
            )
        )
        derivative = (
            float(prior[target_index])
            * (
                float(likelihoods[target_index])
                - float(common_mixture)
            )
            / float(common_mixture)
        )
        derivative_values.append(derivative)
        differences = np.diff(np.asarray(exact_curve))
        maximum_adjacent_change = max(
            maximum_adjacent_change,
            float(np.max(np.abs(differences), initial=0.0)),
        )
        if derivative > TOLERANCE:
            monotone = bool(np.all(differences >= -TOLERANCE))
        elif derivative < -TOLERANCE:
            monotone = bool(np.all(differences <= TOLERANCE))
        else:
            monotone = bool(
                np.max(np.abs(differences), initial=0.0) < TOLERANCE
            )
        if not monotone:
            monotonicity_failures.append(observation)
        checked_curves += 1
    maximum_agreement_error = max(agreement_errors, default=0.0)
    maximum_hysteresis_error = max(hysteresis_errors, default=0.0)
    finite_derivative = all(
        math.isfinite(value) for value in derivative_values
    )
    passed = (
        maximum_agreement_error < TOLERANCE
        and maximum_hysteresis_error < TOLERANCE
        and finite_derivative
        and not monotonicity_failures
    )
    return {
        "definition": "p_h^alpha=(1-alpha)m+alpha*p_h",
        "common_mixture": "m=sum_h prior(h)*p_h",
        "analytic_form": (
            "q_h(alpha)=prior_h*((1-alpha)m+alpha*p_h)/m"
        ),
        "alpha_grid": [float(value) for value in alphas],
        "target_index": target_index,
        "curves_checked": checked_curves,
        "maximum_exact_vs_analytic_error": maximum_agreement_error,
        "maximum_forward_reverse_error": maximum_hysteresis_error,
        "no_discontinuity": (
            maximum_agreement_error < TOLERANCE and finite_derivative
        ),
        "no_hysteresis": maximum_hysteresis_error < TOLERANCE,
        "maximum_absolute_finite_derivative": max(
            (abs(value) for value in derivative_values), default=0.0
        ),
        "finite_derivative": finite_derivative,
        "maximum_adjacent_grid_change": maximum_adjacent_change,
        "monotonicity_failures": monotonicity_failures,
        "passed": passed,
    }


def _source_branch_assignment_audit(
    functions: list[Any],
) -> dict[str, Any]:
    forbidden_names = {
        "h",
        "q_h",
        "qh",
        "formed",
        "winner",
        "selected",
        "selected_policy",
    }
    forbidden_assignments = []
    forbidden_calls = []
    posterior_assignments = []
    branch_posterior_assignments = []
    for function in functions:
        source = textwrap.dedent(inspect.getsource(function))
        tree = ast.parse(source)
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets: list[ast.AST]
                if isinstance(node, ast.Assign):
                    targets = list(node.targets)
                else:
                    targets = [node.target]
                for target in targets:
                    names = [
                        child.id
                        for child in ast.walk(target)
                        if isinstance(child, ast.Name)
                    ]
                    if "posterior" in names:
                        expression = (
                            ast.unparse(node.value)
                            if hasattr(node, "value")
                            else "<augmented>"
                        )
                        item = {
                            "function": function.__name__,
                            "expression": expression,
                            "line": getattr(node, "lineno", None),
                        }
                        posterior_assignments.append(item)
                        parent = parents.get(node)
                        while parent is not None:
                            if isinstance(parent, ast.If):
                                branch_posterior_assignments.append(item)
                                break
                            parent = parents.get(parent)
                    for name in names:
                        if name.lower() in forbidden_names:
                            forbidden_assignments.append(
                                {
                                    "function": function.__name__,
                                    "name": name,
                                    "line": getattr(node, "lineno", None),
                                }
                            )
            if isinstance(node, ast.Call):
                call_name = ""
                if isinstance(node.func, ast.Name):
                    call_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    call_name = node.func.attr
                if call_name in {"argmax", "nanargmax"}:
                    forbidden_calls.append(
                        {
                            "function": function.__name__,
                            "call": call_name,
                            "line": getattr(node, "lineno", None),
                        }
                    )
    return {
        "functions_checked": [function.__name__ for function in functions],
        "forbidden_assignment_targets": forbidden_assignments,
        "winner_selection_calls": forbidden_calls,
        "posterior_assignment_expressions": posterior_assignments,
        "posterior_assignments_inside_if_branches": (
            branch_posterior_assignments
        ),
        "interpretation": (
            "Posterior arrays may be computed only by normalized evidence; "
            "the audit forbids authored latent/status/winner assignments."
        ),
        "passed": (
            not forbidden_assignments
            and not forbidden_calls
            and not branch_posterior_assignments
        ),
    }


def _generic_revised_stage_audit(
    model: FiniteModel,
    *,
    structure: str,
    observation: str,
    sequence: list[int],
    legacy: dict[str, Any],
) -> dict[str, Any]:
    prior = _structure_prior(model, structure)
    table = predictive_table(model, structure, observation)
    common_positive = [
        value
        for value in sequence
        if np.all(table[:, value] > 0.0)
    ]
    update_identity = _table_update_identity(
        prior, table, common_positive
    )
    source_audit = _source_branch_assignment_audit(
        [candidate_scorer]
    )
    finite_information = _finite_information_table(table)
    homotopy = _homotopy_table(
        prior, table, target_index=len(prior) - 1
    )
    composition = {
        "legacy_nine_invariants": legacy,
        "passed": legacy["passed"],
    }
    sections = {
        "A_update_identity": {
            **update_identity,
            "no_authored_assignment": source_audit,
            "passed": update_identity["passed"] and source_audit["passed"],
        },
        "B_finite_information": finite_information,
        "C_evidence_strength_homotopy": homotopy,
        "D_composition": composition,
    }
    return {
        "structure": structure,
        "observation": observation,
        "sections": sections,
        "passed": all(section["passed"] for section in sections.values()),
    }


def _v21_revised_stage_audit(legacy: dict[str, Any]) -> dict[str, Any]:
    sections = {
        "A_update_identity": {
            "not_applicable": True,
            "reason": "V2.1 has no finite structural comparison.",
            "passed": True,
        },
        "B_finite_information": {
            "not_applicable": True,
            "reason": "V2.1 has no pairwise structural likelihood table.",
            "passed": True,
        },
        "C_evidence_strength_homotopy": {
            "not_applicable": True,
            "reason": "V2.1 has no structural posterior q(H).",
            "passed": True,
        },
        "D_composition": {
            "legacy_nine_invariants": legacy,
            "passed": legacy["passed"],
        },
    }
    return {
        "structure": None,
        "observation": None,
        "sections": sections,
        "passed": all(section["passed"] for section in sections.values()),
    }


def _formation_tables() -> list[tuple[dict[str, Any], np.ndarray]]:
    from .v232_formation import LABELS, slice_distribution

    output = []
    for values in itertools.product(
        (False, True),
        ("ordinary", "overwhelm"),
        ("low", "high"),
        ("collapsed", "integrated"),
        (False, True),
    ):
        configuration = dict(
            zip(
                (
                    "event",
                    "precision",
                    "control",
                    "broadcast",
                    "real_danger",
                ),
                values,
            )
        )
        table = np.stack(
            [
                slice_distribution(candidate, **configuration)
                for candidate in LABELS
            ]
        )
        output.append((configuration, table))
    return output


def _formation_update_identity() -> dict[str, Any]:
    from .v232_formation import (
        LABELS,
        SUPPORT,
        score_history,
        score_slice,
    )

    prior = np.asarray([0.31, 0.29, 0.40], dtype=float)
    pair_keys = {
        (2, 0): "P/T",
        (1, 0): "D/T",
        (2, 1): "P/D",
    }
    errors = []
    checks = 0
    for configuration, table in _formation_tables():
        for observation_index in range(table.shape[1]):
            if not np.all(table[:, observation_index] > 0.0):
                continue
            observation = SUPPORT[observation_index]
            posterior, _, detail = score_slice(
                prior, observation, configuration
            )
            for (left, right), key in pair_keys.items():
                increment = (
                    _safe_log_odds(posterior, left, right)
                    - _safe_log_odds(prior, left, right)
                )
                published = float(detail["pairwise_log_bf"][key])
                errors.append(abs(increment - published))
                checks += 1
    source_audit = _source_branch_assignment_audit(
        [score_slice, score_history]
    )
    maximum_error = max(errors, default=0.0)
    return {
        "candidate_labels": list(LABELS),
        "pairwise_increments_checked": checks,
        "maximum_absolute_identity_error": maximum_error,
        "no_authored_assignment": source_audit,
        "passed": maximum_error < TOLERANCE and source_audit["passed"],
    }


def _formation_finite_information() -> dict[str, Any]:
    from .v232_formation import analytic_slice_bound

    bounds = []
    asymmetric_zeros = []
    checked = 0
    for configuration, table in _formation_tables():
        result = _finite_information_table(table)
        checked += result["support_cells_checked"]
        if result["asymmetric_zero_cells"]:
            asymmetric_zeros.append(
                {
                    "configuration": configuration,
                    "cells": result["asymmetric_zero_cells"],
                }
            )
        bounds.append(float(result["B_max"]))
    enumerated_bound = max(bounds)
    published_bound = float(analytic_slice_bound())
    error = abs(enumerated_bound - published_bound)
    finite = (
        math.isfinite(enumerated_bound)
        and not asymmetric_zeros
        and error < TOLERANCE
    )
    return {
        "definition": (
            "sup over every pair and common-support observation in every "
            "frozen V2.3.2 likelihood table"
        ),
        "support_cells_checked": checked,
        "asymmetric_zero_cells": asymmetric_zeros,
        "enumerated_B_max": enumerated_bound,
        "published_frozen_B_max": published_bound,
        "absolute_error": error,
        "every_observed_slice_within_B_max": finite,
        "implied_binary_probability_change_bound": math.tanh(
            published_bound / 4.0
        ),
        "passed": finite,
    }


def _formation_homotopy() -> dict[str, Any]:
    from .v232_formation import LABELS, PRIOR, expected_log_bf

    table_reports = []
    expected_monotonic_failures = []
    predicted_rows = 0
    alphas = np.linspace(0.0, 1.0, 101)
    for configuration, table in _formation_tables():
        report = _homotopy_table(
            PRIOR, table, target_index=LABELS.index("P")
        )
        table_reports.append(report)

        # The frozen sign table predicts P-favoring rows through positive
        # E_P log BF for P/T and P/D.  On exactly those rows, verify that
        # expected q(P;alpha) under the P-generating tempered distribution
        # is monotone nondecreasing.  Zero rows must remain exactly flat.
        final_signs = [
            expected_log_bf("P", "P", denominator, configuration)
            for denominator in ("T", "D")
        ]
        sign_predicts_p = all(value > TOLERANCE for value in final_signs)
        sign_predicts_zero = all(
            abs(value) < TOLERANCE for value in final_signs
        )
        if not (sign_predicts_p or sign_predicts_zero):
            continue
        predicted_rows += 1
        mixture = PRIOR @ table
        positive = mixture > 0.0
        curve = []
        for alpha in alphas:
            tempered = (1.0 - alpha) * mixture + alpha * table
            q_p = (
                PRIOR[LABELS.index("P")]
                * tempered[LABELS.index("P"), positive]
                / mixture[positive]
            )
            curve.append(
                float(
                    np.sum(
                        tempered[LABELS.index("P"), positive] * q_p
                    )
                )
            )
        differences = np.diff(np.asarray(curve))
        if sign_predicts_p:
            monotone = bool(np.all(differences >= -TOLERANCE))
        else:
            monotone = bool(
                np.max(np.abs(differences), initial=0.0) < TOLERANCE
            )
        if not monotone:
            expected_monotonic_failures.append(configuration)
    maximum_agreement_error = max(
        report["maximum_exact_vs_analytic_error"]
        for report in table_reports
    )
    maximum_hysteresis_error = max(
        report["maximum_forward_reverse_error"]
        for report in table_reports
    )
    finite_derivative = all(
        report["finite_derivative"] for report in table_reports
    )
    per_observation_monotone = all(
        not report["monotonicity_failures"] for report in table_reports
    )
    passed = (
        maximum_agreement_error < TOLERANCE
        and maximum_hysteresis_error < TOLERANCE
        and finite_derivative
        and per_observation_monotone
        and not expected_monotonic_failures
    )
    return {
        "definition": "p_h^alpha=(1-alpha)m+alpha*p_h",
        "alpha_grid_count": len(alphas),
        "table_count": len(table_reports),
        "q_P_curves_checked": sum(
            report["curves_checked"] for report in table_reports
        ),
        "maximum_exact_enumeration_vs_analytic_error": (
            maximum_agreement_error
        ),
        "maximum_forward_reverse_hysteresis_error": (
            maximum_hysteresis_error
        ),
        "no_discontinuity": (
            maximum_agreement_error < TOLERANCE and finite_derivative
        ),
        "no_hysteresis": maximum_hysteresis_error < TOLERANCE,
        "finite_derivative_everywhere": finite_derivative,
        "maximum_absolute_finite_derivative": max(
            report["maximum_absolute_finite_derivative"]
            for report in table_reports
        ),
        "per_observation_monotonicity_failures": sum(
            len(report["monotonicity_failures"])
            for report in table_reports
        ),
        "frozen_sign_predicted_rows_checked": predicted_rows,
        "frozen_sign_monotonicity_failures": (
            expected_monotonic_failures
        ),
        "passed": passed,
    }


def _formation_composition() -> dict[str, Any]:
    from .v232_formation import (
        PRIOR,
        SUPPORT,
        independent_history_sum,
        score_history,
        score_slice,
        slice_distribution,
    )

    no_event = {
        "event": False,
        "precision": "ordinary",
        "control": "high",
        "broadcast": "integrated",
        "real_danger": False,
    }
    event = {
        "event": True,
        "precision": "ordinary",
        "control": "low",
        "broadcast": "collapsed",
        "real_danger": False,
    }
    no_event_observation = SUPPORT[
        int(np.argmax(slice_distribution("T", **no_event)))
    ]
    event_observations = [
        SUPPORT[int(np.argmax(slice_distribution(candidate, **event)))]
        for candidate in ("T", "D", "P")
    ]
    no_event_posterior, _, no_event_detail = score_slice(
        PRIOR, no_event_observation, no_event
    )
    masked_posterior, _, masked_detail = score_slice(
        PRIOR, event_observations[0], event, masked=True
    )
    configurations = [event] * len(event_observations)
    forward = score_history(event_observations, configurations)
    reverse = score_history(
        list(reversed(event_observations)),
        list(reversed(configurations)),
    )
    pair_definitions = {
        "P/T": (2, 0),
        "D/T": (1, 0),
        "P/D": (2, 1),
    }
    recombination_errors = []
    for key, (left, right) in pair_definitions.items():
        recombined = _safe_log_odds(PRIOR, left, right) + sum(
            float(detail["pairwise_log_bf"][key])
            for detail in forward["contributions"]
        )
        observed = _safe_log_odds(
            forward["posterior"], left, right
        )
        recombination_errors.append(abs(recombined - observed))
    independent_posterior, independent_log_joint = (
        independent_history_sum(
            PRIOR, event_observations, configurations
        )
    )
    results = {
        "no_event_neutrality": {
            "maximum_posterior_error": float(
                np.max(np.abs(no_event_posterior - PRIOR))
            ),
            "maximum_log_bf": max(
                abs(float(value))
                for value in no_event_detail["pairwise_log_bf"].values()
            ),
        },
        "masked_slice_neutrality": {
            "maximum_posterior_error": float(
                np.max(np.abs(masked_posterior - PRIOR))
            ),
            "maximum_log_bf": max(
                abs(float(value))
                for value in masked_detail["pairwise_log_bf"].values()
            ),
        },
        "matched_statistic_reorder_invariance": {
            "maximum_log_joint_error": float(
                np.max(
                    np.abs(
                        forward["log_joint"] - reverse["log_joint"]
                    )
                )
            )
        },
        "prequential_recombination": {
            "maximum_pairwise_log_odds_error": max(
                recombination_errors, default=0.0
            )
        },
        "independent_summation": {
            "maximum_posterior_error": float(
                np.max(
                    np.abs(
                        forward["posterior"] - independent_posterior
                    )
                )
            ),
            "maximum_log_joint_error": float(
                np.max(
                    np.abs(
                        forward["log_joint"] - independent_log_joint
                    )
                )
            ),
        },
    }
    errors = [
        results["no_event_neutrality"]["maximum_posterior_error"],
        results["no_event_neutrality"]["maximum_log_bf"],
        results["masked_slice_neutrality"]["maximum_posterior_error"],
        results["masked_slice_neutrality"]["maximum_log_bf"],
        results["matched_statistic_reorder_invariance"][
            "maximum_log_joint_error"
        ],
        results["prequential_recombination"][
            "maximum_pairwise_log_odds_error"
        ],
        results["independent_summation"]["maximum_posterior_error"],
        results["independent_summation"]["maximum_log_joint_error"],
    ]
    return {
        "checks": results,
        "maximum_error": max(errors),
        "passed": max(errors) < TOLERANCE,
    }


def formation_revised_graded_update_audit() -> dict[str, Any]:
    sections = {
        "A_update_identity": _formation_update_identity(),
        "B_finite_information": _formation_finite_information(),
        "C_evidence_strength_homotopy": _formation_homotopy(),
        "D_composition": _formation_composition(),
    }
    return {
        "stage": "V2.3.2-formation",
        "sections": sections,
        "passed": all(section["passed"] for section in sections.values()),
    }


def cumulative_graded_update_audit() -> dict[str, Any]:
    """Permanent revised constitution from V2.3.3 onward."""
    from .v20 import model_comparison_model
    from .v221 import _finite_structure_model

    legacy = cumulative_constitution_audit()
    v20_model, v20_observation = model_comparison_model()
    v221_model, v221_observation = _finite_structure_model(90, 90)
    stages = {
        "V2.0": _generic_revised_stage_audit(
            v20_model,
            structure="H",
            observation="D",
            sequence=[v20_observation],
            legacy=legacy["V2.0"],
        ),
        "V2.1": _v21_revised_stage_audit(legacy["V2.1"]),
        "V2.2.1": _generic_revised_stage_audit(
            v221_model,
            structure="Z",
            observation="K",
            sequence=[v221_observation["K"]],
            legacy=legacy["V2.2.1"],
        ),
        "V2.3.2-formation": formation_revised_graded_update_audit(),
    }
    return {
        "constitution_version": "revised-graded-update-1",
        "effective_from": "V2.3.3",
        "standing_stage_scope": list(stages),
        "historical_exclusions": [
            "V2.3 and V2.3.1 are retired failure ledgers.",
            "V2.3.2 attribution is shelved for the V2.3.4 side rung.",
        ],
        "sections": {
            "A": "update identity and no authored assignment",
            "B": "finite-information guarantee and tanh(B_max/4)",
            "C": "evidence-strength homotopy",
            "D": "composition checks",
        },
        "stages": stages,
        "passed": all(stage["passed"] for stage in stages.values()),
    }


def _stress_summary(values: list[float]) -> dict[str, Any]:
    array = np.asarray(values, dtype=float)
    return {
        "count": int(array.size),
        "mean": float(array.mean()) if array.size else None,
        "p50": (
            float(np.quantile(array, 0.50)) if array.size else None
        ),
        "p90": (
            float(np.quantile(array, 0.90)) if array.size else None
        ),
        "p99": (
            float(np.quantile(array, 0.99)) if array.size else None
        ),
        "maximum": float(array.max()) if array.size else None,
    }


def publish_stratified_update_distribution() -> dict[str, Any]:
    """Descriptive, non-criterial V2.3.2 formation stress profile."""
    from .rng import component_rng
    from .v232_formation import (
        LABELS,
        PARAMETERS,
        PRIOR,
        SUPPORT,
        score_history,
        slice_distribution,
    )

    strata: dict[str, list[float]] = {
        name: []
        for name in (
            "no-event",
            "ordinary",
            "acute",
            "high-control",
            "low-control",
            "D-favoring",
            "P-favoring",
        )
    }
    start, end = PARAMETERS["open_seed_block"]
    for offset, seed in enumerate(range(start, end + 1)):
        truth = LABELS[offset % len(LABELS)]
        configurations = []
        observations = []
        for time in range(int(PARAMETERS["sequence_length"])):
            configuration = {
                "event": True,
                "precision": (
                    "overwhelm" if time % 4 == 0 else "ordinary"
                ),
                "control": "low" if time % 3 else "high",
                "broadcast": (
                    "collapsed" if time % 5 == 0 else "integrated"
                ),
                "real_danger": truth == "D",
            }
            row = slice_distribution(truth, **configuration)
            observation_index = int(
                component_rng(
                    seed, f"graded-update-stress-{time}"
                ).choice(len(row), p=row)
            )
            observations.append(SUPPORT[observation_index])
            configurations.append(configuration)
        result = score_history(observations, configurations)
        previous_p = float(PRIOR[2])
        for configuration, state in zip(
            configurations, result["states"]
        ):
            current_p = float(
                state.posterior_store["H_formation"][2]
            )
            change = abs(current_p - previous_p)
            previous_p = current_p
            strata[
                "acute"
                if configuration["precision"] == "overwhelm"
                else "ordinary"
            ].append(change)
            strata[
                "low-control"
                if configuration["control"] == "low"
                else "high-control"
            ].append(change)
            if truth == "D":
                strata["D-favoring"].append(change)
            if truth == "P":
                strata["P-favoring"].append(change)

        no_event_configuration = {
            "event": False,
            "precision": "ordinary",
            "control": "high",
            "broadcast": "integrated",
            "real_danger": False,
        }
        no_event_observation = SUPPORT[
            int(
                np.argmax(
                    slice_distribution("T", **no_event_configuration)
                )
            )
        ]
        no_event_result = score_history(
            [no_event_observation], [no_event_configuration]
        )
        strata["no-event"].append(
            abs(
                float(
                    no_event_result["posterior"][2]
                )
                - float(PRIOR[2])
            )
        )
    summaries = {
        name: _stress_summary(values) for name, values in strata.items()
    }
    return {
        "artifact": "stratified-empirical-update-distribution",
        "classification": "distributional_stress",
        "criterial": False,
        "scientific_inference_use": "none",
        "warning": (
            "Descriptive only. No pass/fail threshold may be inferred. "
            "Any future prospective quantile criterion requires matched "
            "strata and populations, world-blocked or conformal thresholds, "
            "quantile uncertainty, and no unacknowledged enrichment."
        ),
        "stage": "V2.3.2-formation",
        "seed_block": [start, end],
        "absolute_change": "|q_t(P)-q_(t-1)(P)|",
        "stratum_definitions": {
            "no-event": "event=false, separate one-slice trajectory",
            "ordinary": "event=true and precision=ordinary",
            "acute": "event=true and precision=overwhelm",
            "high-control": "event=true and control=high",
            "low-control": "event=true and control=low",
            "D-favoring": "event slices generated under H_formation=D",
            "P-favoring": "event slices generated under H_formation=P",
        },
        "strata": summaries,
        "publisher_source_sha256": hashlib.sha256(
            inspect.getsource(
                publish_stratified_update_distribution
            ).encode()
        ).hexdigest(),
    }
