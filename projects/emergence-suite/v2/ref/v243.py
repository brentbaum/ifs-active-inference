"""V2.4.3 pure structural-existence and BMA readouts."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import numpy as np

from . import v24


@dataclass(frozen=True)
class PathClassReadout:
    prior: tuple[float, float]
    posterior: tuple[float, float]
    conditional_evidence: tuple[float, float]
    log_bf: float
    bf: float
    full_evidence: float
    recombination_error: float


def _emission(context: int, observation: v24.Observation) -> float:
    cue = observation.cue % len(v24.BASELINE)
    probability = v24.BASELINE[cue] if context == 0 else v24.CORRECTIVE[cue]
    descriptor = "then" if context == 0 else "now"
    return (
        v24._outcome_likelihood(float(probability), observation.outcome)
        * v24._marker_likelihood(descriptor, observation.marker)
        * v24._common_root_predictive(observation.root)
    )


def _path_masses(observations: list[v24.Observation], use_likelihood: bool):
    alpha = v24._cs_alpha()
    states = {
        (0, 0, 0, 0, 0, 1): 0.5,
        (1, 0, 0, 0, 0, 2): 0.5,
    }
    for time, observation in enumerate(observations):
        weighted = {
            state: mass * (_emission(state[0], observation) if use_likelihood else 1.0)
            for state, mass in states.items()
        }
        if time == len(observations) - 1:
            states = weighted
            break
        output = {}
        for state, mass in weighted.items():
            context, n00, n01, n10, n11, mask = state
            counts = ((n00, n01), (n10, n11))
            denominator = float(alpha[context].sum() + sum(counts[context]))
            for nxt in (0, 1):
                new = [n00, n01, n10, n11]
                probability = (alpha[context, nxt] + counts[context][nxt]) / denominator
                new[2 * context + nxt] += 1
                key = (nxt, *new, mask | (1 << nxt))
                output[key] = output.get(key, 0.0) + mass * float(probability)
        states = output
    one = sum(mass for state, mass in states.items() if state[-1] in (1, 2))
    two = sum(mass for state, mass in states.items() if state[-1] == 3)
    return np.asarray([one, two], dtype=float)


def path_class_readout(observations: Iterable[v24.Observation]) -> PathClassReadout:
    sequence = list(observations)
    alpha = v24._cs_alpha()
    constant_prior = []
    constant_joint = []
    for context in (0, 1):
        mass = 0.5
        for transition_index in range(max(0, len(sequence) - 1)):
            mass *= float(
                (alpha[context, context] + transition_index)
                / (alpha[context].sum() + transition_index)
            )
        constant_prior.append(mass)
        constant_joint.append(
            mass * math.prod(_emission(context, item) for item in sequence)
        )
    prior_mass = np.asarray(
        [sum(constant_prior), 1.0 - sum(constant_prior)], dtype=float
    )
    one_joint = sum(constant_joint)
    full = math.exp(v24.score_family("context_split", sequence).log_evidence)
    joint = np.asarray([one_joint, full - one_joint], dtype=float)
    prior = prior_mass / prior_mass.sum()
    posterior = joint / full
    conditional = joint / prior
    log_bf = math.log(posterior[1] / posterior[0]) - math.log(prior[1] / prior[0])
    recombined = float(np.dot(prior, conditional))
    return PathClassReadout(
        prior=tuple(prior),
        posterior=tuple(posterior),
        conditional_evidence=tuple(conditional),
        log_bf=log_bf,
        bf=math.exp(log_bf),
        full_evidence=full,
        recombination_error=abs(full - recombined),
    )


def material_redescription(observations: Iterable[v24.Observation]) -> dict:
    sequence = list(observations)
    comparison = v24.compare_families(sequence)
    readout = path_class_readout(sequence)
    posterior = np.asarray(comparison["posterior"])
    cs = v24.FAMILY_INDEX["context_split"]
    unique = bool(np.sum(posterior == posterior.max()) == 1 and posterior[cs] == posterior.max())
    material = bool(unique and readout.posterior[1] >= 0.80 and readout.bf >= 4.0)
    return {
        "material_redescription": material,
        "raw_cs_argmax": unique,
        "pi0": readout.prior[0], "pi1": readout.prior[1],
        "q0": readout.posterior[0], "q1": readout.posterior[1],
        "bf": readout.bf, "log_bf": readout.log_bf,
        "recombination_error": readout.recombination_error,
    }


def bma_heldout(observations: Iterable[v24.Observation]) -> dict:
    sequence = list(observations)
    pre, heldout = v24._heldout_partition(sequence)
    pre_result = v24.compare_families(pre)
    weights = np.asarray(pre_result["posterior"])
    pre_scores = [v24.score_family(name, pre) for name in v24.FAMILIES]
    full_scores = [v24.score_family(name, sequence) for name in v24.FAMILIES]
    logs = np.asarray([f.log_evidence - p.log_evidence for p, f in zip(pre_scores, full_scores)])
    terms = np.log(weights) + logs
    maximum = float(terms.max())
    bma = maximum + math.log(float(np.exp(terms - maximum).sum()))
    observed = sum(any(value is not None for value in (o.outcome, o.marker, o.root)) for o in heldout)
    return {
        "pre_weights": weights.tolist(),
        "family_log_scores": logs.tolist(),
        "bma_log_score": bma,
        "observed_tokens": observed,
        "material_pre": material_redescription(pre),
    }
