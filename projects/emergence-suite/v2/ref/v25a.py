"""V2.5a exact evidence-presentation readouts.

This module is scoring-side only.  It does not alter a V2.4 candidate,
generator, likelihood, prior, transition, or posterior.  A marginal
presentation is the product of three exact candidate copies, each receiving
one observation channel while the other channels use the frozen missing
value.  The copies use the same frozen family definition and therefore form
an exact prequential derived candidate rather than an approximation.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable

import numpy as np

from .audit import ProtocolState, audit_one_posterior
from . import v24
from .rng import component_rng


ROOT = Path(__file__).resolve().parents[1]
PARAMETER_PATH = ROOT / "protocols" / "v2.5a-parameters.json"
PARAMETERS = json.loads(PARAMETER_PATH.read_text(encoding="utf-8"))
CHANNELS = ("outcome", "marker", "root")
TARGET_ROOT_KL = "root_prior_to_posterior_kl"
TOLERANCE = float(PARAMETERS["identities"]["increment_identity_tolerance"])


@dataclass(frozen=True)
class PresentationScore:
    family: str
    joint: v24.FamilyScore
    channel_scores: MappingProxyType
    marginal_per_slice_log_predictive: tuple[float, ...]
    marginal_log_evidence: float
    delta_i_per_slice: tuple[float, ...]
    delta_i: float
    increment_identity_error: float
    derived_state: ProtocolState


@dataclass(frozen=True)
class MatchingReadout:
    family: str
    generating_family: str
    seed: int
    base_length: int
    cap: int
    target_name: str
    target_kl: float
    matched_slices: int | None
    matched_kl: float | None
    ratio: float | None
    censored: bool
    absolute_kl_error: float | None
    prefix_identity: bool


def _channel_observation(
    observation: v24.Observation, channel: str
) -> v24.Observation:
    if channel not in CHANNELS:
        raise ValueError(f"unknown presentation channel {channel!r}")
    return v24.Observation(
        cue=observation.cue,
        outcome=observation.outcome if channel == "outcome" else None,
        marker=observation.marker if channel == "marker" else None,
        root=observation.root if channel == "root" else None,
    )


def channel_history(
    observations: Iterable[v24.Observation], channel: str
) -> list[v24.Observation]:
    """Return the exact frozen missing-channel marginal presentation."""
    return [_channel_observation(item, channel) for item in observations]


def association_dose_history(
    observations: Iterable[v24.Observation],
    seed: int,
    strength: float,
) -> list[v24.Observation]:
    """Attenuate Y/X alignment while preserving every channel multiset.

    The generator output and candidate likelihood are untouched.  Within
    each cue, a deterministic nested fraction retains its original marker;
    the remaining marker multiset is permuted over the remaining positions.
    Strength one is exact identity and strength zero is the complete
    marginal-preserving presentation.
    """
    value = float(strength)
    if not 0.0 <= value <= 1.0:
        raise ValueError("association dose must lie in [0,1]")
    sequence = list(observations)
    output = list(sequence)
    for cue in sorted({item.cue for item in sequence}):
        indices = [
            index
            for index, item in enumerate(sequence)
            if item.cue == cue and item.marker is not None
        ]
        if len(indices) < 2:
            continue
        order = component_rng(
            seed, f"v25a-dose-order-cue-{cue}"
        ).permutation(len(indices))
        retained = int(math.floor(value * len(indices) + 1e-12))
        retained_offsets = set(int(item) for item in order[:retained])
        moved_offsets = [
            offset for offset in range(len(indices))
            if offset not in retained_offsets
        ]
        if len(moved_offsets) > 1:
            permutation = component_rng(
                seed, f"v25a-dose-permutation-cue-{cue}"
            ).permutation(len(moved_offsets))
            if np.all(permutation == np.arange(len(moved_offsets))):
                permutation = np.roll(permutation, 1)
            source_markers = [
                sequence[indices[offset]].marker for offset in moved_offsets
            ]
            for target_position, target_offset in enumerate(moved_offsets):
                target = indices[target_offset]
                old = output[target]
                output[target] = v24.Observation(
                    cue=old.cue,
                    outcome=old.outcome,
                    marker=source_markers[int(permutation[target_position])],
                    root=old.root,
                )
    return output


def _positive_vector(value: Any) -> np.ndarray:
    leaves: list[float] = []

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for key in sorted(item):
                visit(item[key])
        elif isinstance(item, (list, tuple, np.ndarray)):
            for child in item:
                visit(child)
        elif isinstance(item, (int, float, np.integer, np.floating)):
            leaves.append(max(float(item), 1e-300))

    visit(value)
    return np.asarray(leaves or [1.0], dtype=float)


def score_presentations(
    family: str, observations: Iterable[v24.Observation]
) -> PresentationScore:
    """Score unchanged joint and exact product-of-marginals presentations."""
    sequence = list(observations)
    joint = v24.score_family(family, sequence)
    channel_scores = {
        channel: v24.score_family(
            family, channel_history(sequence, channel)
        )
        for channel in CHANNELS
    }
    marginal_per_slice = tuple(
        float(
            sum(
                channel_scores[channel].per_slice_log_predictive[index]
                for channel in CHANNELS
            )
        )
        for index in range(len(sequence))
    )
    marginal_evidence = float(sum(marginal_per_slice))
    delta = tuple(
        float(joint.per_slice_log_predictive[index] - marginal_per_slice[index])
        for index in range(len(sequence))
    )
    cumulative = float(sum(delta))
    identity_error = abs(
        cumulative - (joint.log_evidence - marginal_evidence)
    )
    derived_state = ProtocolState(
        posterior_store={f"H_R_tilde::{family}": np.asarray([1.0])},
        parameter_posterior_store={
            f"{family}::{channel}": _positive_vector(
                dict(channel_scores[channel].parameter_posterior)
            )
            for channel in CHANNELS
        },
        evidence_store={
            f"{family}::marginal": math.exp(
                max(marginal_evidence, -700.0)
            )
        },
        metadata=MappingProxyType(
            {
                "stage": "V2.5a",
                "presentation": "product_of_exact_channel_marginals",
                "analysis_only": True,
            }
        ),
    )
    audit_one_posterior(derived_state)
    return PresentationScore(
        family=family,
        joint=joint,
        channel_scores=MappingProxyType(channel_scores),
        marginal_per_slice_log_predictive=marginal_per_slice,
        marginal_log_evidence=marginal_evidence,
        delta_i_per_slice=delta,
        delta_i=cumulative,
        increment_identity_error=float(identity_error),
        derived_state=derived_state,
    )


def compare_marginal_candidates(
    observations: Iterable[v24.Observation],
) -> dict[str, Any]:
    """Finite comparison among derived candidates without updating originals."""
    sequence = list(observations)
    scores = [score_presentations(family, sequence) for family in v24.FAMILIES]
    log_evidence = np.asarray(
        [score.marginal_log_evidence for score in scores], dtype=float
    )
    posterior = v24._softmax(np.log(v24.PRIOR) + log_evidence)
    state = ProtocolState(
        posterior_store={"H_R_tilde": posterior.copy()},
        parameter_posterior_store={
            f"{score.family}::{channel}": _positive_vector(
                dict(score.channel_scores[channel].parameter_posterior)
            )
            for score in scores
            for channel in CHANNELS
        },
        evidence_store={
            score.family: math.exp(max(score.marginal_log_evidence, -700.0))
            for score in scores
        },
        metadata=MappingProxyType(
            {
                "stage": "V2.5a",
                "presentation": "marginal",
                "analysis_only": True,
            }
        ),
    )
    audit_one_posterior(state)
    return {
        "candidate_order": list(v24.FAMILIES),
        "posterior": posterior,
        "log_evidence": log_evidence,
        "scores": scores,
        "state": state,
        "one_posterior_audit": True,
    }


def root_posterior(
    observations: Iterable[v24.Observation],
    prior: Iterable[float] = (0.5, 0.5),
) -> np.ndarray:
    """Exact persistent-root posterior under the frozen root likelihood."""
    posterior = v24._normalize(np.asarray(list(prior), dtype=float))
    for observation in observations:
        if observation.root is None:
            continue
        likelihood = np.asarray(
            [
                v24._root_likelihood(state, observation.root)
                for state in range(2)
            ],
            dtype=float,
        )
        posterior = v24._normalize(posterior * likelihood)
    return posterior


def _root_posterior_at_reliability(
    observations: Iterable[v24.Observation],
    prior: Iterable[float],
    reliability: float,
) -> np.ndarray:
    """Root trajectory under the composition endpoint's declared CPT."""
    root_reliability = float(reliability)
    if not 0.5 <= root_reliability <= 1.0:
        raise ValueError("root reliability must lie in [0.5,1]")
    posterior = v24._normalize(np.asarray(list(prior), dtype=float))
    for observation in observations:
        if observation.root is None:
            continue
        likelihood = np.asarray(
            [
                (
                    root_reliability
                    if state == observation.root
                    else 1.0 - root_reliability
                )
                for state in range(2)
            ],
            dtype=float,
        )
        posterior = v24._normalize(posterior * likelihood)
    return posterior


def categorical_kl(posterior: np.ndarray, prior: np.ndarray) -> float:
    q = v24._normalize(np.asarray(posterior, dtype=float))
    p = v24._normalize(np.asarray(prior, dtype=float))
    positive = q > 0.0
    return float(np.sum(q[positive] * np.log(q[positive] / p[positive])))


def scan_root_kl(
    observations: Iterable[v24.Observation],
    target_kl: float,
    tolerance: float,
    cap: int,
    prior: Iterable[float] = (0.5, 0.5),
) -> tuple[int | None, float | None]:
    """Least marginal slice whose declared root KL reaches the target."""
    sequence = list(observations)
    if cap < 1 or cap > len(sequence):
        raise ValueError("matching cap is outside the supplied sequence")
    if target_kl < 0.0 or tolerance < 0.0:
        raise ValueError("KL target and tolerance must be nonnegative")
    prior_array = v24._normalize(np.asarray(list(prior), dtype=float))
    posterior = prior_array.copy()
    for index, observation in enumerate(sequence[:cap], start=1):
        if observation.root is not None:
            likelihood = np.asarray(
                [
                    v24._root_likelihood(state, observation.root)
                    for state in range(2)
                ],
                dtype=float,
            )
            posterior = v24._normalize(posterior * likelihood)
        value = categorical_kl(posterior, prior_array)
        if value + tolerance >= target_kl:
            return index, value
    return None, None


def match_marginal_root_information(
    family: str,
    generating_family: str,
    seed: int,
    *,
    base_length: int = 96,
    target_name: str = TARGET_ROOT_KL,
    tolerance: float | None = None,
    cap_multiplier: int | None = None,
) -> MatchingReadout:
    """Extend one frozen seed world and scan its exact root marginal."""
    if target_name != TARGET_ROOT_KL:
        raise ValueError("matching target was not declared as root KL")
    tol = float(
        PARAMETERS["criterion_freeze_procedure"]["default_candidates"][
            "matching_kl_tolerance_nats"
        ]
        if tolerance is None
        else tolerance
    )
    multiplier = int(
        PARAMETERS["matching"]["extension_cap_multiplier"]
        if cap_multiplier is None
        else cap_multiplier
    )
    cap = multiplier * int(base_length)
    base = v24.generate_world(
        generating_family, seed, length=base_length
    )
    extended = v24.generate_world(
        generating_family, seed, length=cap
    )
    prefix_identity = base["observations"] == extended["observations"][:base_length]
    if not prefix_identity:
        raise AssertionError("same-seed frozen generator prefix changed on extension")
    prior = np.asarray([0.5, 0.5], dtype=float)
    target_posterior = root_posterior(base["observations"], prior)
    target = categorical_kl(target_posterior, prior)
    matched, value = scan_root_kl(
        extended["observations"], target, tol, cap
    )
    return MatchingReadout(
        family=family,
        generating_family=generating_family,
        seed=int(seed),
        base_length=int(base_length),
        cap=cap,
        target_name=target_name,
        target_kl=target,
        matched_slices=matched,
        matched_kl=value,
        ratio=(None if matched is None else matched / base_length),
        censored=matched is None,
        absolute_kl_error=(
            None if value is None else abs(float(value) - target)
        ),
        prefix_identity=prefix_identity,
    )


def formed_bridge_format_readout(
    seed: int,
    bank_record: dict[str, Any],
    *,
    tolerance: float | None = None,
    cap_multiplier: int | None = None,
) -> dict[str, Any]:
    """Joint versus information-matched marginal formed-state root uptake."""
    state = bank_record["serialized_state"]
    joint = v24._composition_world(seed, bank_state=state)
    base_observations = list(joint["world"]["observations"])
    base_length = len(base_observations)
    multiplier = int(
        PARAMETERS["matching"]["extension_cap_multiplier"]
        if cap_multiplier is None
        else cap_multiplier
    )
    tol = float(
        PARAMETERS["frozen_numeric_criteria"][
            "matching_kl_tolerance_nats"
        ]
        if tolerance is None
        else tolerance
    )
    cap = multiplier * base_length
    extended_world = v24.generate_world(
        "context_split", seed, length=cap, missingness=0.0
    )
    initial_prediction = v24._cue_root_prediction(
        joint["initial_root"], joint["association"]
    )
    extended_observations, direction, _ = v24._witnessing_root_tokens(
        seed, extended_world, initial_prediction
    )
    if extended_observations[:base_length] != base_observations:
        raise AssertionError("formed bridge extension changed frozen prefix")

    initial_root = np.asarray(joint["initial_root"], dtype=float)
    target_kl = categorical_kl(
        np.asarray(joint["final_root"], dtype=float), initial_root
    )
    matched, matched_kl = scan_root_kl(
        extended_observations,
        target_kl,
        tol,
        cap,
        prior=initial_root,
    )
    joint_movement = float(joint["signed_transfer"])
    joint_trajectory = [0.0]
    for index in range(1, base_length + 1):
        posterior = _root_posterior_at_reliability(
            base_observations[:index],
            initial_root,
            reliability=float(joint["association_reliability"]),
        )
        prediction = v24._cue_root_prediction(
            posterior, joint["association"]
        )
        joint_trajectory.append(
            direction * (prediction - initial_prediction)
        )

    marginal_trajectory = [0.0]
    marginal_movement: float | None = None
    marginal_root: np.ndarray | None = None
    if matched is not None:
        for index in range(1, matched + 1):
            prefix = extended_observations[:index]
            global_root = root_posterior(prefix, initial_root)
            marker_score = v24.score_family(
                "context_split", channel_history(prefix, "marker")
            )
            q_context = np.asarray(
                marker_score.final_predictive["q_context_then_now"],
                dtype=float,
            )
            present_root = v24._normalize(
                q_context[1] * global_root
                + q_context[0] * initial_root
            )
            prediction = v24._cue_root_prediction(
                present_root, joint["association"]
            )
            marginal_trajectory.append(
                direction * (prediction - initial_prediction)
            )
            marginal_root = present_root
        marginal_movement = marginal_trajectory[-1]

    horizon = max(base_length, matched or 0)
    difference_trajectory = []
    for index in range(horizon + 1):
        joint_value = joint_trajectory[min(index, base_length)]
        marginal_value = (
            marginal_trajectory[min(index, matched)]
            if matched is not None
            else 0.0
        )
        difference_trajectory.append(joint_value - marginal_value)
    increments = [
        difference_trajectory[index] - difference_trajectory[index - 1]
        for index in range(1, len(difference_trajectory))
    ]
    difference = (
        None
        if marginal_movement is None
        else joint_movement - marginal_movement
    )
    decomposition_error = (
        None
        if difference is None
        else abs(sum(increments) - difference)
    )
    return {
        "seed": seed,
        "bank_seed": bank_record["seed"],
        "stratum": bank_record["stratum"],
        "initial_state_hash": bank_record["state_sha256"],
        "base_length": base_length,
        "cap": cap,
        "target_name": TARGET_ROOT_KL,
        "target_kl": target_kl,
        "matched_slices": matched,
        "matched_kl": matched_kl,
        "matching_absolute_kl_error": (
            None if matched_kl is None else abs(matched_kl - target_kl)
        ),
        "matching_censored": matched is None,
        "joint_root_movement": joint_movement,
        "marginal_root_movement": marginal_movement,
        "joint_minus_marginal": difference,
        "per_slice_difference_increments": increments,
        "decomposition_error": decomposition_error,
        "G_fixed_difference": 0.0,
        "zero_association_difference": 0.0,
        "joint_local_delta_i": score_presentations(
            "context_split", base_observations
        ).delta_i,
        "marginal_present_root": (
            None if marginal_root is None else marginal_root.tolist()
        ),
    }


def enumerable_joint_information(
    association_strength: float,
) -> dict[str, float]:
    """Exact one-slice CS dummy KL for the frozen Y/X channel tables."""
    strength = float(association_strength)
    if not 0.0 <= strength <= 1.0:
        raise ValueError("association strength must lie in [0,1]")
    joint = np.zeros((2, len(v24.MARKERS)), dtype=float)
    marker_mean = 0.5 * (
        v24._marker_row("then") + v24._marker_row("now")
    )
    for context in (0, 1):
        outcome_p = float(
            v24.BASELINE[0] if context == 0 else v24.CORRECTIVE[0]
        )
        marker_context = v24._marker_row(
            "then" if context == 0 else "now"
        )
        marker = (
            strength * marker_context + (1.0 - strength) * marker_mean
        )
        outcome = np.asarray([1.0 - outcome_p, outcome_p], dtype=float)
        joint += 0.5 * np.outer(outcome, marker)
    outcome_marginal = joint.sum(axis=1)
    marker_marginal = joint.sum(axis=0)
    product = np.outer(outcome_marginal, marker_marginal)
    positive = joint > 0.0
    kl = float(np.sum(joint[positive] * np.log(joint[positive] / product[positive])))
    return {
        "association_strength": strength,
        "expected_delta_i": kl,
        "joint_sum_error": abs(float(joint.sum()) - 1.0),
        "minimum_probability": float(joint.min()),
    }


def marginal_finite_information_bound() -> dict[str, Any]:
    """Derive the table-supremum bound for product-marginal accounting."""
    outcome_ratio = 0.9 / 0.1
    marker_ratio = 0.8 / 0.05
    root_ratio = 0.85 / 0.15
    value = math.log(outcome_ratio * marker_ratio * root_ratio)
    return {
        "B_max_v25a_marginal_accounting": value,
        "B_max_v24_common_emissions": float(
            v24.PARAMETERS["finite_information"]["B_max"]
        ),
        "distinct": not math.isclose(
            value,
            float(v24.PARAMETERS["finite_information"]["B_max"]),
            rel_tol=0.0,
            abs_tol=1e-15,
        ),
        "implied_binary_probability_change_bound": math.tanh(value / 4.0),
    }
