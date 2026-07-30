"""Independent V3.1 structural oracle.

The implementation copies inputs and independently recomputes all 128
structure scores.  It imports no production scoring helper.
"""

from __future__ import annotations

import copy
import itertools
import math
from typing import Any, Mapping, Sequence

import numpy as np


EDGE_NAMES = ("M1_G", "G_W", "G_A", "G_Y", "W_Y", "doA_Y")


def _log_beta(a: float, b: float) -> float:
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def _marginal(rows: Sequence[tuple[int, int]], alpha: float) -> float:
    return math.fsum(
        _log_beta(zero + alpha, one + alpha) - _log_beta(alpha, alpha)
        for zero, one in rows
    )


def _counts(
    slices: Sequence[Mapping[str, Any]],
    child: str,
    parents: tuple[str, ...],
) -> tuple[tuple[int, int], ...]:
    result = [[0, 0] for _ in range(1 << len(parents))]
    for item in slices:
        if child == "mode":
            if not item["mode_observed"]:
                continue
            value = item["mode"]
        elif child == "root":
            if not item["root_observed"]:
                continue
            value = item["root"]
        elif child == "world":
            value = item["world"]
        elif child == "policy_proposal":
            value = item["policy_proposal"]
        else:
            value = item["outcome_observed"]
            if value is None:
                continue
        row = 0
        for bit, parent in enumerate(parents):
            parent_value = {
                "mode": item["mode"],
                "root": item["root"],
                "world": item["world"],
                "action": int(item["action"] == 1),
            }[parent]
            row |= int(parent_value) << bit
        result[row][int(value)] += 1
    return tuple((item[0], item[1]) for item in result)


def posterior(
    slices_input: Sequence[Mapping[str, Any]],
    *,
    concentration: float = 0.5,
    code_length_scale: float = 1.0,
) -> tuple[tuple[tuple[int, ...], ...], tuple[float, ...], float]:
    slices = copy.deepcopy(tuple(dict(item) for item in slices_input))
    programs = tuple(itertools.product((0, 1), repeat=7))
    log_weights = []
    absent_weight = 2.0 ** (-code_length_scale)
    present_weight = 2.0 ** (-2.0 * code_length_scale)
    normalizer = absent_weight + present_weight
    for program in programs:
        active, *edge_bits = program
        values = dict(zip(EDGE_NAMES, edge_bits))
        total = math.fsum(
            math.log((present_weight if value else absent_weight) / normalizer)
            for value in program
        )
        modes = [
            item["mode"] for item in slices if item["mode_observed"]
        ]
        if not active and any(modes):
            total = -math.inf
        elif active:
            total += _marginal(
                ((modes.count(0), modes.count(1)),), concentration
            )
        total += _marginal(
            _counts(
                slices,
                "root",
                ("mode",) if values["M1_G"] else (),
            ),
            concentration,
        )
        total += _marginal(
            _counts(
                slices,
                "world",
                ("root",) if values["G_W"] else (),
            ),
            concentration,
        )
        total += _marginal(
            _counts(
                slices,
                "policy_proposal",
                ("root",) if values["G_A"] else (),
            ),
            concentration,
        )
        y_parents = tuple(
            parent
            for edge, parent in (
                ("G_Y", "root"),
                ("W_Y", "world"),
                ("doA_Y", "action"),
            )
            if values[edge]
        )
        total += _marginal(
            _counts(slices, "outcome", y_parents), concentration
        )
        log_weights.append(total)
    values = np.asarray(log_weights)
    maximum = float(np.max(values))
    log_evidence = maximum + math.log(float(np.exp(values - maximum).sum()))
    probabilities = tuple(float(value) for value in np.exp(values - log_evidence))
    return programs, probabilities, log_evidence


def lesion_posterior(
    slices_input: Sequence[Mapping[str, Any]],
    lesion: str,
    *,
    concentration: float = 0.5,
    code_length_scale: float = 1.0,
) -> tuple[tuple[tuple[int, ...], ...], tuple[float, ...]]:
    """Independently score a lesion as a conditioned structure prior.

    Typed-evidence transformations are copied and applied independently of the
    production scorer.  No caller-owned input is mutated.
    """
    slices = copy.deepcopy(tuple(dict(item) for item in slices_input))
    if lesion == "mode_slot":
        for item in slices:
            item["mode_observed"] = False
    elif lesion == "availability_control":
        for item in slices:
            if item["outcome_observed"] is None:
                item["outcome_observed"] = item["outcome_true"]
    elif lesion == "recursive_precision":
        for item in slices:
            observed = item["time"] % 2 == 0
            item["mode_observed"] = observed
            item["root_observed"] = observed
    elif lesion not in {
        "identity_edges",
        "action_edge",
        "fixed_G",
    }:
        raise ValueError("unknown lesion")

    programs, probabilities, _ = posterior(
        slices,
        concentration=concentration,
        code_length_scale=code_length_scale,
    )

    def allowed(program: tuple[int, ...]) -> bool:
        if lesion == "mode_slot":
            return program[0] == 0
        if lesion == "identity_edges":
            return all(program[index] == 0 for index in (1, 2, 3, 4))
        if lesion == "action_edge":
            return program[6] == 0
        return True

    retained_mass = math.fsum(
        probability
        for program, probability in zip(programs, probabilities)
        if allowed(program)
    )
    conditioned = tuple(
        probability / retained_mass if allowed(program) else 0.0
        for program, probability in zip(programs, probabilities)
    )
    return programs, conditioned
