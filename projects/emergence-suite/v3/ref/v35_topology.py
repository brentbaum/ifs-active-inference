"""Enumerable interventional topology fixture for V3.5."""

from __future__ import annotations

import math

from . import v35


TOPOLOGIES = ("independent", "opposed", "allied")
POLICIES = tuple((left, right, 1) for left in range(3) for right in range(3))
REPETITIONS = 100


def _model(name: str):
    if name == "independent":
        return v35.ProtectStructure(2, (0, 0, 0), 0, 0), 0
    return (
        v35.ProtectStructure(2, (0, 0, 0), 0, 1),
        -1 if name == "opposed" else 1,
    )


def _probabilities(name: str):
    structure, sign = _model(name)
    return tuple(
        v35.outcome_probability(policy, (1, 1, 0), structure, sign)
        for policy in POLICIES
    )


def _expected_log_bf(truth: str, comparator: str) -> float:
    truth_p = _probabilities(truth)
    comparator_p = _probabilities(comparator)
    return float(
        REPETITIONS
        * math.fsum(
            p * math.log(p / q)
            + (1.0 - p) * math.log((1.0 - p) / (1.0 - q))
            for p, q in zip(truth_p, comparator_p)
        )
    )


def _posterior(truth: str):
    expected_scores = []
    truth_p = _probabilities(truth)
    for candidate in TOPOLOGIES:
        candidate_p = _probabilities(candidate)
        expected_scores.append(
            REPETITIONS
            * math.fsum(
                p * math.log(q) + (1.0 - p) * math.log(1.0 - q)
                for p, q in zip(truth_p, candidate_p)
            )
        )
    maximum = max(expected_scores)
    weights = [math.exp(value - maximum) for value in expected_scores]
    total = math.fsum(weights)
    return tuple(value / total for value in weights)


def _influence(name: str):
    structure, sign = _model(name)
    components = ((structure, sign),)
    scores = v35._policy_scores(
        (1.0,), components, (1.0, 1.0, 0.0), 0.5,
        (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 1.0,
    )
    return v35.interventional_policy_influence(scores)


def run():
    table = {
        truth: {
            comparator: _expected_log_bf(truth, comparator)
            for comparator in TOPOLOGIES
        }
        for truth in TOPOLOGIES
    }
    recovery = {
        truth: {
            name: probability
            for name, probability in zip(TOPOLOGIES, _posterior(truth))
        }
        for truth in TOPOLOGIES
    }
    fingerprints = {name: _influence(name) for name in TOPOLOGIES}
    independent_error = max(
        abs(fingerprints["independent"][i][j])
        for i in (0, 1) for j in (0, 1) if i != j
    )
    opposed_values = (
        fingerprints["opposed"][0][1], fingerprints["opposed"][1][0]
    )
    allied_values = (
        fingerprints["allied"][0][1], fingerprints["allied"][1][0]
    )
    lesion_error = max(
        abs(fingerprints["independent"][i][j])
        for i in range(3) for j in range(3)
    )
    single = v35.ProtectStructure(1, (1, 0, 0), 1, 0)
    single_scores = v35._policy_scores(
        (1.0,), ((single, 0),), (0.8, 0.0, 0.0), 0.7,
        (0.6, 0.0, 0.0), (0.4, 0.0, 0.0), 1.0,
    )
    single_identity = max(
        abs(a - b)
        for a, b in zip(
            v35._policy_distribution(single_scores),
            v35._policy_distribution(single_scores),
        )
    )
    passed = (
        all(max(values, key=values.get) == truth for truth, values in recovery.items())
        and all(
            value > 0
            for truth, row in table.items()
            for comparator, value in row.items()
            if truth != comparator
        )
        and independent_error <= v35.TOLERANCE
        and all(value < 0 for value in opposed_values)
        and all(value > 0 for value in allied_values)
        and lesion_error <= v35.TOLERANCE
        and single_identity <= v35.TOLERANCE
    )
    return {
        "balanced_interventional_policy_count": len(POLICIES),
        "repetitions_per_policy": REPETITIONS,
        "expected_log_bf": table,
        "recovery": recovery,
        "fingerprints": fingerprints,
        "independent_error": independent_error,
        "opposed_reciprocal": opposed_values,
        "allied_reciprocal": allied_values,
        "cross_edge_lesion_error": lesion_error,
        "single_mode_learning_identity_error": single_identity,
        "passed": passed,
    }
