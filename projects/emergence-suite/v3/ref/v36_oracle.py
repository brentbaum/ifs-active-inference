"""Independent composition and code-length oracle for V3.6 public dummies."""

from __future__ import annotations

import copy
import math
from typing import Any, Mapping


PROTOCOL_COUNT = 11
GRAMMAR_BITS = 58.0


def combine_readouts(parts_input: Mapping[str, Mapping[str, Any]]) -> dict[str, float]:
    """Copy inputs and independently reproduce the published composition map."""
    parts = copy.deepcopy(dict(parts_input))
    split = parts["split"]
    return {
        "q_identity_organization": float(parts["grow"]["part_probability"]),
        "q_external_danger": float(parts["grow"]["danger_probability"]),
        "q_context_specific": 0.5 * (
            float(split["cue_context_specific"])
            + float(split["outcome_context_specific"])
        ),
        "q_recurrent_context": 0.5 * (
            float(split["cue_recurrent"])
            + float(split["outcome_recurrent"])
        ),
        "q_current_edge_absence": 1.0 - float(parts["prune"]["burden_mass"]),
        "q_partner_reliable": float(parts["relate"]["q_reliable"]),
        "q_policy_open": float(parts["protect"]["q_open"]),
    }


def code_length(
    log_priors_input: Mapping[str, float],
    parameter_bits: float,
) -> dict[str, float]:
    priors = copy.deepcopy(dict(log_priors_input))
    L_H = -math.fsum(float(value) for value in priors.values()) / math.log(2.0)
    L_protocol = math.log2(PROTOCOL_COUNT)
    return {
        "L_grammar": GRAMMAR_BITS,
        "L_H": L_H,
        "L_theta_given_H": float(parameter_bits),
        "L_protocol": L_protocol,
        "L_total": GRAMMAR_BITS + L_H + float(parameter_bits) + L_protocol,
    }
