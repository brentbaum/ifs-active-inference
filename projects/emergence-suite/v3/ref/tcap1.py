"""T-CAP1 focused sequential precision-filter organism.

This is a variant organism.  It imports no V3.6 scientific state and does not
modify the frozen V3.6 modules.  The two added productions are the delayed
bundle-to-allocation policy and the allocation-observability channel.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from . import v31
from .trace_sink import require_trace_sink


CHANNELS = ("threat_cue", "body_state", "partner_face", "present_context", "safety_evidence")
CONFIRMING = frozenset((0, 1, 2))
DISCONFIRMING = frozenset((3, 4))
ARMS = (
    "transparent_feedback",
    "no_feedback_candidate_common",
    "represented_feedback",
    "random_allocation",
    "sign_reversed_allocation",
    "matched_persistence",
    "full_information_replay",
    "filter_awareness_only",
)
TOL = 1e-10


@dataclass(frozen=True)
class CaptureParameters:
    coupling_strength: float
    cue_intensity: float
    allocation_persistence: float
    bundle_transition_persistence: float
    meta_observation_reliability: float

    def __post_init__(self) -> None:
        if self.coupling_strength < 0.0:
            raise ValueError("coupling_strength must be nonnegative")
        for name in ("cue_intensity", "allocation_persistence", "bundle_transition_persistence", "meta_observation_reliability"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} outside [0,1]")


@dataclass(frozen=True)
class CaptureSlice:
    time: int
    cue: float
    bundle_state: int
    allocation: int
    meta_observation: int
    observations: tuple[int | None, ...]


@dataclass(frozen=True)
class CaptureStream:
    seed: int
    arm: str
    parameters: CaptureParameters
    slices: tuple[CaptureSlice, ...]
    component_rng_keys: tuple[str, ...]


def cue_schedule(scale: float) -> tuple[float, ...]:
    levels = (0.0, 0.25, 0.5, 0.75, 1.0)
    up = tuple(scale * value for value in levels for _ in range(3))
    peak = (scale,) * 4
    down = tuple(scale * value for value in reversed(levels) for _ in range(3))
    withdrawal = (0.0,) * 8
    return up + peak + down + withdrawal


def _clip_probability(value: float) -> float:
    return min(max(float(value), 1e-9), 1.0 - 1e-9)


def _logit(value: float) -> float:
    value = _clip_probability(value)
    return math.log(value / (1.0 - value))


def _logistic(value: float) -> float:
    return float(1.0 / (1.0 + math.exp(-value)))


def allocation_probability(
    q_bundle: float,
    cue: float,
    coupling_strength: float,
    previous_allocation: int,
    persistence: float,
    *,
    rule: str = "feedback",
) -> float:
    """Production A1: delayed bundle-to-allocation policy."""

    if rule == "feedback":
        target = _logistic(coupling_strength * (2.0 * q_bundle - 1.0) + 0.5 * cue)
    elif rule == "reversed":
        target = _logistic(-coupling_strength * (2.0 * q_bundle - 1.0) + 0.5 * cue)
    elif rule == "random":
        target = 0.5
    elif rule == "candidate_common":
        target = _clip_probability(0.15 + 0.20 * cue)
    elif rule == "off":
        target = 0.0
    else:
        raise ValueError(rule)
    return _clip_probability(persistence * int(previous_allocation) + (1.0 - persistence) * target)


def allocation_observation_probability(observed: int, allocation: int, reliability: float) -> float:
    """Production A2: p(O_Phi | A_Phi,D)."""

    return reliability if int(observed) == int(allocation) else 1.0 - reliability


def delivery_probability(channel: int, allocation: int) -> float:
    if allocation == 0:
        return 0.90
    return 0.98 if channel in CONFIRMING else 0.25


def token_probability(channel: int, bundle: int, allocation: int, cue: float) -> float:
    """Probability that the delivered token favors bundle-active."""

    if allocation == 0:
        probability = 0.78 if bundle else 0.22
    elif channel in CONFIRMING:
        probability = 0.88 if bundle else 0.48
    else:
        probability = 0.55 if bundle else 0.45
    if channel in CONFIRMING:
        probability += 0.20 * cue
    return _clip_probability(probability)


def observation_atom_probability(
    channel: int,
    observed: int | None,
    bundle: int,
    allocation: int,
    cue: float,
    *,
    full_information: bool = False,
) -> float:
    delivered = 1.0 if full_information else delivery_probability(channel, allocation)
    if observed is None:
        return 1.0 - delivered
    token = token_probability(channel, bundle, 0 if full_information else allocation, cue)
    return delivered * (token if observed else 1.0 - token)


def transition_predict(q_bundle: float, persistence: float) -> float:
    return _clip_probability(persistence * q_bundle + (1.0 - persistence) * (1.0 - q_bundle))


def _channel_log_likelihood(
    observations: Sequence[int | None],
    bundle: int,
    allocation: int,
    cue: float,
    *,
    full_information: bool = False,
) -> float:
    return math.fsum(
        math.log(observation_atom_probability(index, observed, bundle, allocation, cue, full_information=full_information))
        for index, observed in enumerate(observations)
    )


def transparent_log_likelihood(observations: Sequence[int | None], bundle: int, cue: float, *, full_information: bool = False) -> float:
    return _channel_log_likelihood(observations, bundle, 0, cue, full_information=full_information)


def represented_log_likelihood(
    observations: Sequence[int | None],
    meta_observation: int,
    bundle: int,
    cue: float,
    allocation_prior: float,
    meta_reliability: float,
    *,
    full_information: bool = False,
) -> float:
    if full_information:
        return transparent_log_likelihood(observations, bundle, cue, full_information=True)
    terms = []
    for allocation in (0, 1):
        prior = allocation_prior if allocation else 1.0 - allocation_prior
        terms.append(math.log(prior) + math.log(allocation_observation_probability(meta_observation, allocation, meta_reliability)) + _channel_log_likelihood(observations, bundle, allocation, cue))
    maximum = max(terms)
    return maximum + math.log(math.fsum(math.exp(value - maximum) for value in terms))


def allocation_aware_log_likelihood(
    observations: Sequence[int | None],
    bundle: int,
    allocation: int,
    cue: float,
    *,
    full_information: bool = False,
) -> float:
    """Allocation-aware likelihood conditional on realized allocation/delivery.

    This is the round-30 oracle likelihood.  It adds no latent state and uses
    the same observation atoms as the generator while conditioning on the
    allocation that actually controlled delivery.
    """

    return _channel_log_likelihood(
        observations,
        bundle,
        allocation,
        cue,
        full_information=full_information,
    )


def posterior_update(prior: float, log_likelihood_zero: float, log_likelihood_one: float) -> float:
    return _logistic(_logit(prior) + log_likelihood_one - log_likelihood_zero)


def selection_log_bfs(
    observations: Sequence[int | None],
    meta_observation: int,
    cue: float,
    allocation_prior: float,
    meta_reliability: float,
) -> tuple[float, float]:
    naive = transparent_log_likelihood(observations, 1, cue) - transparent_log_likelihood(observations, 0, cue)
    aware = represented_log_likelihood(observations, meta_observation, 1, cue, allocation_prior, meta_reliability) - represented_log_likelihood(observations, meta_observation, 0, cue, allocation_prior, meta_reliability)
    return float(aware), float(naive)


def effective_precision(channel: int, allocation: int, cue: float, delivered: bool) -> float:
    if not delivered:
        return 0.0
    p1 = token_probability(channel, 1, allocation, cue)
    p0 = token_probability(channel, 0, allocation, cue)
    return abs(_logit(p1) - _logit(p0))


def counterfactual_disconfirming_influence(
    prior: float,
    channel: int,
    cue: float,
    allocation_prior: float,
    meta_observation: int,
    meta_reliability: float,
    architecture: str,
) -> float:
    masked = (None,) * len(CHANNELS)
    token = list(masked)
    token[channel] = 0
    if architecture == "transparent":
        masked_post = posterior_update(prior, transparent_log_likelihood(masked, 0, cue), transparent_log_likelihood(masked, 1, cue))
        token_post = posterior_update(prior, transparent_log_likelihood(token, 0, cue), transparent_log_likelihood(token, 1, cue))
    else:
        masked_post = posterior_update(prior, represented_log_likelihood(masked, meta_observation, 0, cue, allocation_prior, meta_reliability), represented_log_likelihood(masked, meta_observation, 1, cue, allocation_prior, meta_reliability))
        token_post = posterior_update(prior, represented_log_likelihood(token, meta_observation, 0, cue, allocation_prior, meta_reliability), represented_log_likelihood(token, meta_observation, 1, cue, allocation_prior, meta_reliability))
    return float(_logit(token_post) - _logit(masked_post))


def _rng(seed: int, component: str, time: int, released_block: tuple[int, int], keys: list[str]) -> np.random.Generator:
    return v31._rng(seed, f"tcap1:{component}", time, released_block, keys)  # noqa: SLF001


def _draw(seed: int, component: str, time: int, probability: float, released_block: tuple[int, int], keys: list[str]) -> int:
    return int(_rng(seed, component, time, released_block, keys).random() < probability)


def world_component_key(kind: str, channel: int | None = None) -> str:
    """Arm-invariant key for world and potential-observation randomness."""

    if kind in {"bundle-stay", "meta"} and channel is None:
        return kind
    if kind in {"delivery", "token"} and channel is not None:
        return f"{kind}:{channel}"
    raise ValueError((kind, channel))


def allocation_component_key(arm: str) -> str:
    """The sole arm-varying RNG namespace in the repaired census runner."""

    if arm not in ARMS:
        raise ValueError(arm)
    return f"allocation:{arm}"


def generate_stream(
    seed: int,
    parameters: CaptureParameters,
    arm: str,
    *,
    released_block: tuple[int, int],
    initial_q: float = 0.12,
) -> CaptureStream:
    require_trace_sink("tcap1.generate_stream", seed=seed, arm=arm)
    if arm not in ARMS:
        raise ValueError(arm)
    keys: list[str] = []
    schedule = cue_schedule(parameters.cue_intensity)
    q_controller = _clip_probability(initial_q)
    bundle = 0
    previous_allocation = 0
    slices = []
    for time, cue in enumerate(schedule):
        if time:
            stay = _draw(seed, world_component_key("bundle-stay"), time, parameters.bundle_transition_persistence, released_block, keys)
            if not stay:
                bundle = 1 - bundle
        if arm in {"no_feedback_candidate_common", "matched_persistence"}:
            rule = "candidate_common"
        elif arm == "random_allocation":
            rule = "random"
        elif arm == "sign_reversed_allocation":
            rule = "reversed"
        elif arm == "full_information_replay":
            rule = "off"
        else:
            rule = "feedback"
        allocation_prior = allocation_probability(q_controller, cue, parameters.coupling_strength, previous_allocation, parameters.allocation_persistence, rule=rule)
        allocation = _draw(seed, allocation_component_key(arm), time, allocation_prior, released_block, keys)
        meta = _draw(seed, world_component_key("meta"), time, allocation_observation_probability(1, allocation, parameters.meta_observation_reliability), released_block, keys)
        observations = []
        for channel in range(len(CHANNELS)):
            if arm == "full_information_replay":
                delivered = 1
                lambda_for_token = 0
            else:
                delivered = _draw(seed, world_component_key("delivery", channel), time, delivery_probability(channel, allocation), released_block, keys)
                lambda_for_token = allocation
            if delivered:
                observations.append(_draw(seed, world_component_key("token", channel), time, token_probability(channel, bundle, lambda_for_token, cue), released_block, keys))
            else:
                observations.append(None)
        item = CaptureSlice(time, cue, bundle, allocation, meta, tuple(observations))
        slices.append(item)
        prior = transition_predict(q_controller, parameters.bundle_transition_persistence)
        ll0 = transparent_log_likelihood(item.observations, 0, cue, full_information=arm == "full_information_replay")
        ll1 = transparent_log_likelihood(item.observations, 1, cue, full_information=arm == "full_information_replay")
        q_controller = posterior_update(prior, ll0, ll1)
        previous_allocation = allocation
    return CaptureStream(seed, arm, parameters, tuple(slices), tuple(keys))


def score_stream(stream: CaptureStream, architecture: str, *, initial_q: float = 0.12) -> dict[str, Any]:
    require_trace_sink("tcap1.score_stream", seed=stream.seed, arm=stream.arm, architecture=architecture)
    if architecture not in {"transparent", "represented", "oracle"}:
        raise ValueError(architecture)
    q = _clip_probability(initial_q)
    previous_allocation = 0
    trajectory = []
    for item in stream.slices:
        persistence = stream.parameters.bundle_transition_persistence
        if stream.arm == "matched_persistence":
            persistence = min(0.999, persistence + 0.045)
        prior = transition_predict(q, persistence)
        rule = "feedback"
        if stream.arm in {"no_feedback_candidate_common", "matched_persistence"}:
            rule = "candidate_common"
        elif stream.arm == "random_allocation":
            rule = "random"
        elif stream.arm == "sign_reversed_allocation":
            rule = "reversed"
        elif stream.arm == "full_information_replay":
            rule = "off"
        allocation_prior = allocation_probability(q, item.cue, stream.parameters.coupling_strength, previous_allocation, stream.parameters.allocation_persistence, rule=rule)
        full = stream.arm == "full_information_replay"
        if architecture == "oracle" and not full:
            ll0 = allocation_aware_log_likelihood(item.observations, 0, item.allocation, item.cue)
            ll1 = allocation_aware_log_likelihood(item.observations, 1, item.allocation, item.cue)
        elif architecture == "transparent" or full:
            ll0 = transparent_log_likelihood(item.observations, 0, item.cue, full_information=full)
            ll1 = transparent_log_likelihood(item.observations, 1, item.cue, full_information=full)
        else:
            ll0 = represented_log_likelihood(item.observations, item.meta_observation, 0, item.cue, allocation_prior, stream.parameters.meta_observation_reliability)
            ll1 = represented_log_likelihood(item.observations, item.meta_observation, 1, item.cue, allocation_prior, stream.parameters.meta_observation_reliability)
        q_next = posterior_update(prior, ll0, ll1)
        aware_bf, naive_bf = selection_log_bfs(item.observations, item.meta_observation, item.cue, allocation_prior, stream.parameters.meta_observation_reliability)
        precisions = tuple(effective_precision(index, item.allocation, item.cue, observed is not None) for index, observed in enumerate(item.observations))
        influence_architecture = "transparent" if architecture == "oracle" else architecture
        influence = counterfactual_disconfirming_influence(prior, 4, item.cue, allocation_prior, item.meta_observation, stream.parameters.meta_observation_reliability, influence_architecture)
        trajectory.append({"time": item.time, "cue": item.cue, "q_prior": prior, "q_bundle": q_next, "allocation_prior": allocation_prior, "allocation": item.allocation, "effective_precision": precisions, "disconfirming_influence": influence, "selection_aware_log_bf": aware_bf, "selection_naive_log_bf": naive_bf, "delivered_count": sum(value is not None for value in item.observations)})
        q = q_next
        previous_allocation = item.allocation
    return {"architecture": architecture, "trajectory": tuple(trajectory)}


def calibration_metastability_readout(
    stream: CaptureStream,
    *,
    initial_q: float = 0.02,
) -> dict[str, Any]:
    """Round-30 oracle-relative calibration trajectories on one realized stream."""

    transparent = score_stream(stream, "transparent", initial_q=initial_q)
    represented = score_stream(stream, "represented", initial_q=initial_q)
    oracle = score_stream(stream, "oracle", initial_q=initial_q)
    q_t = tuple(float(row["q_bundle"]) for row in transparent["trajectory"])
    q_r = tuple(float(row["q_bundle"]) for row in represented["trajectory"])
    q_o = tuple(float(row["q_bundle"]) for row in oracle["trajectory"])
    discrepancy_t = tuple(float(_logit(left) - _logit(right)) for left, right in zip(q_t, q_o))
    discrepancy_r = tuple(float(_logit(left) - _logit(right)) for left, right in zip(q_r, q_o))
    withdrawal_start = len(stream.slices) - 8
    post_t = discrepancy_t[withdrawal_start:]
    post_r = discrepancy_r[withdrawal_start:]
    congruent = 0
    disconfirming = 0
    delivered = 0
    for item in stream.slices[withdrawal_start:]:
        for channel, value in enumerate(item.observations):
            if value is None:
                continue
            delivered += 1
            if channel in CONFIRMING and value == 1:
                congruent += 1
            if channel in DISCONFIRMING and value == 0:
                disconfirming += 1
    return {
        "q_transparent": q_t,
        "q_represented": q_r,
        "q_oracle": q_o,
        "M_transparent": discrepancy_t,
        "M_represented": discrepancy_r,
        "A_M_transparent": float(math.fsum(max(value, 0.0) for value in post_t)),
        "A_M_represented": float(math.fsum(max(value, 0.0) for value in post_r)),
        "delta_A_M_transparent_minus_represented": float(
            math.fsum(max(value, 0.0) for value in post_t)
            - math.fsum(max(value, 0.0) for value in post_r)
        ),
        "peak_postwithdrawal_discrepancy_transparent": float(max(post_t)),
        "peak_postwithdrawal_discrepancy_represented": float(max(post_r)),
        "withdrawal_start": withdrawal_start,
        "cue_response_transparent": float(max(q_t[:withdrawal_start]) - q_t[0]),
        "postwithdrawal_delivered_count": delivered,
        "postwithdrawal_congruent_count": congruent,
        "postwithdrawal_disconfirming_count": disconfirming,
        "continuing_danger": bool(any(item.bundle_state == 1 for item in stream.slices[withdrawal_start:])),
        "oracle_final_probability": float(q_o[-1]),
        "oracle_truth_brier_postwithdrawal": float(
            np.mean([
                (q_o[index] - stream.slices[index].bundle_state) ** 2
                for index in range(withdrawal_start, len(stream.slices))
            ])
        ),
    }


def sustained_recovery_time(
    discrepancy: Sequence[float],
    withdrawal_start: int,
    epsilon: float,
    consecutive: int,
) -> int:
    """First post-withdrawal offset with sustained oracle agreement."""

    if epsilon <= 0.0 or consecutive < 1:
        raise ValueError("invalid recovery definition")
    post = tuple(float(value) for value in discrepancy[withdrawal_start:])
    for start in range(0, len(post) - consecutive + 1):
        if all(abs(value) <= epsilon for value in post[start:start + consecutive]):
            return start
    return -1


def stream_payload(stream: CaptureStream) -> tuple[tuple[Any, ...], ...]:
    """Canonical scientific stream payload, excluding labels and parameters."""

    return tuple(
        (item.time, item.cue, item.bundle_state, item.allocation, item.meta_observation, item.observations)
        for item in stream.slices
    )


def census3_world(
    seed: int,
    parameters: CaptureParameters,
    *,
    released_block: tuple[int, int],
) -> dict[str, Any]:
    """One Census-3 world with controls and coupling-zero counterfactual."""

    controls = simulate_all_arms(seed, parameters, released_block=released_block)
    primary = generate_stream(
        seed,
        parameters,
        "transparent_feedback",
        released_block=released_block,
        initial_q=0.02,
    )
    zero_parameters = CaptureParameters(
        0.0,
        parameters.cue_intensity,
        parameters.allocation_persistence,
        parameters.bundle_transition_persistence,
        parameters.meta_observation_reliability,
    )
    coupling_zero = generate_stream(
        seed,
        zero_parameters,
        "transparent_feedback",
        released_block=released_block,
        initial_q=0.02,
    )
    primary_readout = calibration_metastability_readout(primary, initial_q=0.02)
    zero_readout = calibration_metastability_readout(coupling_zero, initial_q=0.02)
    if tuple(item.bundle_state for item in primary.slices) != tuple(item.bundle_state for item in coupling_zero.slices):
        raise RuntimeError("coupling-zero counterfactual latent path mismatch")
    if tuple(item.cue for item in primary.slices) != tuple(item.cue for item in coupling_zero.slices):
        raise RuntimeError("coupling-zero counterfactual cue mismatch")
    if parameters.coupling_strength == 0.0:
        allocation_error = max(
            abs(
                allocation_probability(q, item.cue, 0.0, previous, parameters.allocation_persistence)
                - allocation_probability(q, item.cue, 0.0, previous, parameters.allocation_persistence)
            )
            for q, previous, item in zip(
                (0.02,) + primary_readout["q_transparent"][:-1],
                (0,) + tuple(item.allocation for item in primary.slices[:-1]),
                primary.slices,
            )
        )
        generated_error = 0.0 if stream_payload(primary) == stream_payload(coupling_zero) else 1.0
        score_error = max(
            abs(left - right)
            for left, right in zip(primary_readout["q_transparent"], zero_readout["q_transparent"])
        )
    else:
        allocation_error = None
        generated_error = None
        score_error = None
    primary_readout["A_feedback"] = float(
        primary_readout["A_M_transparent"] - zero_readout["A_M_transparent"]
    )
    return {
        "controls": controls,
        "primary": primary_readout,
        "coupling_zero": zero_readout,
        "coupling_zero_identity": {
            "applicable": parameters.coupling_strength == 0.0,
            "allocation_probability_error": allocation_error,
            "generated_stream_error": generated_error,
            "scored_posterior_error": score_error,
        },
        "primary_stream": stream_payload(primary),
        "coupling_zero_stream": stream_payload(coupling_zero),
    }


def _level_values(trajectory: Sequence[Mapping[str, float]]) -> tuple[dict[float, float], dict[float, float]]:
    up, down = {}, {}
    for level_index, level in enumerate((0.0, 0.25, 0.5, 0.75, 1.0)):
        start = level_index * 3
        up[level] = float(np.mean([trajectory[index]["q_bundle"] for index in range(start, start + 3)]))
    down_start = 19
    for index, level in enumerate((1.0, 0.75, 0.5, 0.25, 0.0)):
        start = down_start + index * 3
        down[level] = float(np.mean([trajectory[position]["q_bundle"] for position in range(start, start + 3)]))
    return up, down


def hysteresis_area(up: Mapping[float, float], down: Mapping[float, float]) -> float:
    return float(math.fsum(max(0.0, down[level] - up[level]) * 0.25 for level in (0.0, 0.25, 0.5, 0.75, 1.0)))


def dynamics_readouts(score: Mapping[str, Any]) -> dict[str, Any]:
    trajectory = score["trajectory"]
    up, down = _level_values(trajectory)
    hysteresis = hysteresis_area(up, down)
    capture_on = next((level for level in (0.0, 0.25, 0.5, 0.75, 1.0) if up[level] >= 0.70), -1.0)
    release = next((level for level in (1.0, 0.75, 0.5, 0.25, 0.0) if down[level] < 0.50), -1.0)
    withdrawal_start = len(trajectory) - 8
    recovery = next((item["time"] - withdrawal_start for item in trajectory[withdrawal_start:] if item["q_bundle"] < 0.30), -1)
    final_q = float(trajectory[-1]["q_bundle"])
    initial_q = float(trajectory[0]["q_bundle"])
    return {
        "hysteresis_area": float(hysteresis),
        "capture_on_threshold": float(capture_on),
        "release_threshold": float(release),
        "posterior_after_full_withdrawal": final_q,
        "material_elevation_after_withdrawal": final_q - initial_q,
        "recovery_time": int(recovery),
        "mean_effective_precision": tuple(float(np.mean([item["effective_precision"][index] for item in trajectory])) for index in range(len(CHANNELS))),
        "mean_disconfirming_influence": float(np.mean([item["disconfirming_influence"] for item in trajectory])),
        "mean_selection_bf_divergence": float(np.mean([item["selection_naive_log_bf"] - item["selection_aware_log_bf"] for item in trajectory])),
        "delivered_token_denominator": int(sum(item["delivered_count"] for item in trajectory)),
        "up_curve": up,
        "down_curve": down,
    }


def bistability_readout(low_score: Mapping[str, Any], high_score: Mapping[str, Any]) -> dict[str, Any]:
    """Explicit paired low/high-initial-posterior fixed-point estimand."""

    low = low_score["trajectory"]
    high = high_score["trajectory"]
    low_final = float(low[-1]["q_bundle"])
    high_final = float(high[-1]["q_bundle"])
    low_stability = abs(low_final - float(np.mean([item["q_bundle"] for item in low[-4:]])))
    high_stability = abs(high_final - float(np.mean([item["q_bundle"] for item in high[-4:]])))
    separation = abs(high_final - low_final)
    two_stable = low_stability <= 0.05 and high_stability <= 0.05 and separation >= 0.25
    return {
        "low_initial_posterior": 0.02,
        "high_initial_posterior": 0.98,
        "low_final_posterior": low_final,
        "high_final_posterior": high_final,
        "final_separation": separation,
        "low_stability_error": low_stability,
        "high_stability_error": high_stability,
        "two_stable_fixed_points": bool(two_stable),
        "fixed_point_count": 2 if two_stable else 1,
    }


def simulate_all_arms(seed: int, parameters: CaptureParameters, *, released_block: tuple[int, int]) -> dict[str, Any]:
    """Generate/control all arms; represented arms replay one common stream."""

    feedback_stream = generate_stream(seed, parameters, "transparent_feedback", released_block=released_block, initial_q=0.02)
    feedback_stream_high = generate_stream(seed, parameters, "transparent_feedback", released_block=released_block, initial_q=0.98)
    transparent = score_stream(feedback_stream, "transparent", initial_q=0.02)
    transparent_high = score_stream(feedback_stream_high, "transparent", initial_q=0.98)
    represented = score_stream(feedback_stream, "represented", initial_q=0.02)
    represented_high = score_stream(feedback_stream_high, "represented", initial_q=0.98)
    arms: dict[str, Any] = {
        "transparent_feedback": dynamics_readouts(transparent),
        "represented_feedback": dynamics_readouts(represented),
        "filter_awareness_only": dynamics_readouts(represented),
    }
    arms["transparent_feedback"]["bistability"] = bistability_readout(transparent, transparent_high)
    arms["represented_feedback"]["bistability"] = bistability_readout(represented, represented_high)
    arms["filter_awareness_only"]["bistability"] = dict(arms["represented_feedback"]["bistability"])
    stream_hash_payload = tuple((item.time, item.cue, item.bundle_state, item.allocation, item.meta_observation, item.observations) for item in feedback_stream.slices)
    arms["represented_feedback"]["common_stream_identity"] = True
    arms["filter_awareness_only"]["common_stream_identity"] = True
    common_paths = {
        "transparent_feedback": tuple(item.bundle_state for item in feedback_stream.slices),
        "represented_feedback": tuple(item.bundle_state for item in feedback_stream.slices),
        "filter_awareness_only": tuple(item.bundle_state for item in feedback_stream.slices),
    }
    for arm in ("no_feedback_candidate_common", "random_allocation", "sign_reversed_allocation", "matched_persistence", "full_information_replay"):
        stream = generate_stream(seed, parameters, arm, released_block=released_block, initial_q=0.02)
        stream_high = generate_stream(seed, parameters, arm, released_block=released_block, initial_q=0.98)
        transparent_score = score_stream(stream, "transparent", initial_q=0.02)
        transparent_score_high = score_stream(stream_high, "transparent", initial_q=0.98)
        readout = dynamics_readouts(transparent_score)
        readout["bistability"] = bistability_readout(transparent_score, transparent_score_high)
        if arm == "full_information_replay":
            represented_score = score_stream(stream, "represented", initial_q=0.02)
            error = max(abs(left["q_bundle"] - right["q_bundle"]) for left, right in zip(transparent_score["trajectory"], represented_score["trajectory"]))
            readout["transparent_represented_max_error"] = float(error)
        arms[arm] = readout
        common_paths[arm] = tuple(item.bundle_state for item in stream.slices)
    if len(set(common_paths.values())) != 1:
        raise RuntimeError("arm-common latent world path identity failed")
    return {"arms": arms, "feedback_stream": stream_hash_payload, "common_bundle_path": next(iter(common_paths.values())), "arm_common_world_identity": True, "component_rng_keys": feedback_stream.component_rng_keys}
