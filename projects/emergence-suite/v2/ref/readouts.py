"""Pure scientific readouts from posterior/evidence stores."""

from __future__ import annotations

import numpy as np

from .audit import ProtocolState


def posterior_probability(state: ProtocolState, key: str, index: int) -> float:
    return float(state.posterior_store[key][index])


def depth(state: ProtocolState, phi_key: str = "Phi") -> float:
    """P(Phi=integrated-calibrated | observations); state 2 is contractual."""
    return posterior_probability(state, phi_key, 2)


def dominance(full: np.ndarray, leave_one_out: np.ndarray) -> float:
    """Total-variation influence of a factor on a target posterior."""
    return float(0.5 * np.abs(np.asarray(full) - np.asarray(leave_one_out)).sum())


def log_bayes_factor(state: ProtocolState, numerator: str, denominator: str) -> float:
    return float(np.log(state.evidence_store[numerator]) - np.log(state.evidence_store[denominator]))

