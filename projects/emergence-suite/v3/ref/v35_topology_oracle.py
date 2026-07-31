"""Independent formulas for the V3.5 topology fixture."""

from __future__ import annotations

import itertools
import math


NAMES = ("independent", "opposed", "allied")
POLICIES = tuple(itertools.product(range(3), repeat=2))


def _p(name, policy):
    left, right = policy
    if name == "independent":
        return 0.5
    if name == "opposed":
        return 0.5 + 0.30 * abs(left - right) / 2.0
    return 0.5 + 0.30 * int(left == right == 2)


def _softmax(values):
    maximum = max(values)
    weights = [math.exp(value - maximum) for value in values]
    total = sum(weights)
    return [value / total for value in weights]


def _influence(name):
    scores = {
        policy: (
            2.0 * _p(name, policy)
            - 4.0 * int(policy[1] == 2) * 0.5
            - 0.05 * sum(abs(value - 1) for value in policy)
        )
        for policy in POLICIES
    }
    result = [[0.0, 0.0], [0.0, 0.0]]
    for source, target in ((0, 1), (1, 0)):
        means = []
        for fixed in (0, 2):
            retained = [policy for policy in POLICIES if policy[source] == fixed]
            probabilities = _softmax([scores[policy] for policy in retained])
            means.append(sum(p * policy[target] for p, policy in zip(probabilities, retained)))
        result[source][target] = means[1] - means[0]
    return tuple(tuple(row) for row in result)


def run():
    table = {}
    for truth in NAMES:
        table[truth] = {}
        for comparator in NAMES:
            value = 0.0
            for policy in POLICIES:
                p = _p(truth, policy)
                q = _p(comparator, policy)
                value += p * math.log(p / q) + (1 - p) * math.log((1 - p) / (1 - q))
            table[truth][comparator] = 100.0 * value
    return {
        "expected_log_bf": table,
        "fingerprints": {name: _influence(name) for name in NAMES},
    }
