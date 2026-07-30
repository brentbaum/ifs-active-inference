"""Independently authored exact oracle for V3.3 PRUNE."""

from __future__ import annotations

import copy
import itertools
import math
from typing import Any, Mapping, Sequence


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
        values = {
            "mode": item["mode"],
            "root": item["root"],
            "world": item["world"],
            "policy": item["policy_proposal"],
            "action": item["action"],
            "outcome": item["outcome"],
        }
        child_value = values[child]
        if child_value is None or any(values[parent] is None for parent in parents):
            continue
        row = 0
        for bit, parent in enumerate(parents):
            row |= int(values[parent]) << bit
        result[row][int(child_value)] += 1
    return tuple((item[0], item[1]) for item in result)


def posterior(
    slices_input: Sequence[Mapping[str, Any]],
    *,
    concentration: float = 0.5,
    code_length_scale: float = 1.0,
    restrictions: Mapping[str, tuple[int, ...]] | None = None,
) -> tuple[tuple[tuple[int, ...], ...], tuple[float, ...], float]:
    """Copy inputs and enumerate all allowed seven-bit graph programs."""

    slices = copy.deepcopy(tuple(dict(item) for item in slices_input))
    limits = {} if restrictions is None else {
        str(key): tuple(value) for key, value in dict(restrictions).items()
    }
    programs = tuple(
        program
        for program in itertools.product((0, 1), repeat=7)
        if all(
            (
                program[0]
                if name == "active_mode"
                else program[1 + EDGE_NAMES.index(name)]
            )
            in allowed
            for name, allowed in limits.items()
        )
    )
    absent = 2.0 ** (-code_length_scale)
    present = 2.0 ** (-2.0 * code_length_scale)
    prior_total = absent + present
    log_weights = []
    for program in programs:
        active, *edge_bits = program
        edges = dict(zip(EDGE_NAMES, edge_bits))
        score = math.fsum(
            math.log((present if value else absent) / prior_total)
            for value in program
        )
        modes = [item["mode"] for item in slices if item["mode"] is not None]
        if not active and any(modes):
            score = -math.inf
        elif active:
            score += _marginal(
                ((modes.count(0), modes.count(1)),), concentration
            )
        score += _marginal(
            _counts(
                slices,
                "root",
                ("mode",) if edges["M1_G"] else (),
            ),
            concentration,
        )
        score += _marginal(
            _counts(
                slices,
                "world",
                ("root",) if edges["G_W"] else (),
            ),
            concentration,
        )
        score += _marginal(
            _counts(
                slices,
                "policy",
                ("root",) if edges["G_A"] else (),
            ),
            concentration,
        )
        parents = tuple(
            parent
            for edge, parent in (
                ("G_Y", "root"),
                ("W_Y", "world"),
                ("doA_Y", "action"),
            )
            if edges[edge]
        )
        score += _marginal(
            _counts(slices, "outcome", parents), concentration
        )
        log_weights.append(score)
    maximum = max(log_weights)
    evidence = maximum + math.log(
        math.fsum(math.exp(value - maximum) for value in log_weights)
    )
    probabilities = tuple(
        math.exp(value - evidence) for value in log_weights
    )
    return programs, probabilities, evidence

