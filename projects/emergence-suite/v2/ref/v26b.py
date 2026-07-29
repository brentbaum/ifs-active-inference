"""V2.6b exact one-protector trust, policy, and future-risk reference."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Sequence

import numpy as np

from . import v234, v26a
from .audit import ProtocolState, audit_one_posterior
from .rng import component_rng


ROOT = Path(__file__).resolve().parents[1]
PARAMETERS = json.loads(
    (ROOT / "protocols" / "v2.6b-parameters.json").read_text()
)
TOLERANCE = float(PARAMETERS["semantic_tolerance"])
TRUST_NAMES = ("T_outcome", "T_coprotection", "T_partner")
TRUST_PRIOR = np.asarray(PARAMETERS["trust_prior"], dtype=float)
OUTCOME_SUPPORT = np.asarray(
    PARAMETERS["policy_outcome_support"], dtype=float
)
OUTCOME_PRIOR = np.asarray(PARAMETERS["policy_outcome_prior"], dtype=float)
POLICIES = tuple(PARAMETERS["policies"])
POLICY_INDEX = {name: index for index, name in enumerate(POLICIES)}
CONTACT_BY_POLICY = np.asarray(
    PARAMETERS["contact_probability_by_policy"], dtype=float
)
POLICY_EFFORT = np.asarray(PARAMETERS["policy_effort"], dtype=float)
EPOCH_B_DEVELOPMENT_BLOCK = tuple(
    PARAMETERS["epoch_b_development_block"]
)


@dataclass(frozen=True)
class TrustObservation:
    refusal: bool
    partner_response: int | None = None
    outcome: int | None = None
    coprotection: int | None = None
    policy_outcome: int | None = None
    response_reliability: float | None = None


@dataclass(frozen=True)
class ProtectorWorld:
    seed: int
    trust_truth: tuple[int, int, int]
    policy_outcome_index: int
    partner_world: v26a.PartnerWorld
    attribution_world: v234.AttributionWorld
    trust_observations: tuple[TrustObservation, ...]
    stakes: float
    scenario: str


@dataclass(frozen=True)
class PolicyReadout:
    q_policy: np.ndarray
    expected_cost: np.ndarray
    vulnerable_risk: float
    unsupported_risk: float
    role_preserving_risk: float
    role_absent_risk: float
    role_absence_risk_differential: float
    hope_preserving: float
    hope_absent: float
    permission_mass: float
    contact_probability: float


@dataclass(frozen=True)
class ProtectorScore:
    q_trust: tuple[np.ndarray, np.ndarray, np.ndarray]
    q_policy_outcome: np.ndarray
    q_policy: np.ndarray
    expected_cost: np.ndarray
    permission_mass: float
    contact_probability: float
    vulnerable_risk: float
    unsupported_risk: float
    role_preserving_risk: float
    role_absent_risk: float
    role_absence_risk_differential: float
    hope_preserving: float
    hope_absent: float
    partner_score: v26a.PartnerScore
    attribution_score: v234.AttributionScore
    root_movement: float
    transfer: float
    state: ProtocolState


def _rng(
    seed: int,
    component: str,
    released_block: tuple[int, int] | None = None,
) -> np.random.Generator:
    return component_rng(
        seed,
        component,
        released_block=(
            EPOCH_B_DEVELOPMENT_BLOCK
            if released_block is None
            else released_block
        ),
    )


def _normalize(values: Sequence[float]) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    total = float(result.sum())
    if total <= 0.0:
        raise ValueError("cannot normalize nonpositive mass")
    return result / total


def _binary_likelihood(
    observed: int | None,
    state: int,
    reliability: float,
) -> float:
    if observed is None:
        return 1.0
    return (
        float(reliability)
        if int(observed) == int(state)
        else 1.0 - float(reliability)
    )


def trust_posteriors(
    observations: Iterable[TrustObservation],
    *,
    initial_priors: Sequence[Sequence[float]] | None = None,
    partner_to_trust: bool = True,
) -> tuple[tuple[np.ndarray, np.ndarray, np.ndarray], np.ndarray, float]:
    """Exact independent forecast and policy-outcome parameter posteriors."""
    sequence = tuple(observations)
    if initial_priors is None:
        q = [TRUST_PRIOR.copy() for _ in TRUST_NAMES]
    else:
        q = [
            _normalize(np.array(item, dtype=float, copy=True))
            for item in initial_priors
        ]
    q_outcome = OUTCOME_PRIOR.copy()
    log_evidence = 0.0
    default_reliability = float(
        PARAMETERS["trust_observation_reliability"]
    )
    for item in sequence:
        observed = (
            item.outcome,
            item.coprotection,
            (
                item.partner_response
                if item.refusal and partner_to_trust
                else None
            ),
        )
        reliabilities = (
            default_reliability,
            default_reliability,
            (
                default_reliability
                if item.response_reliability is None
                else float(item.response_reliability)
            ),
        )
        for axis in range(3):
            likelihood = np.asarray(
                [
                    _binary_likelihood(
                        observed[axis], state, reliabilities[axis]
                    )
                    for state in (0, 1)
                ],
                dtype=float,
            )
            evidence = float(q[axis] @ likelihood)
            q[axis] = q[axis] * likelihood / evidence
            log_evidence += math.log(evidence)
        if item.policy_outcome is not None:
            likelihood = np.asarray(
                [
                    probability
                    if int(item.policy_outcome) == 1
                    else 1.0 - probability
                    for probability in OUTCOME_SUPPORT
                ],
                dtype=float,
            )
            evidence = float(q_outcome @ likelihood)
            q_outcome = q_outcome * likelihood / evidence
            log_evidence += math.log(evidence)
    return (q[0], q[1], q[2]), q_outcome, log_evidence


def policy_posterior(
    trust_means: Sequence[float],
    policy_outcome_mean: float,
    danger_probability: float,
    efficacy_probability: float,
    future_precision: float,
    stakes: float,
    *,
    stakes_enabled: bool = True,
    coprotection_enabled: bool = True,
    efficacy_enabled: bool = True,
    epistemic_test_enabled: bool = True,
    policy_to_contact_enabled: bool = True,
    inverse_temperature: float | None = None,
    policy_effort: Sequence[float] | None = None,
) -> PolicyReadout:
    """Exact expected-cost policy posterior and pure readouts."""
    outcome_trust, coprotection_trust, partner_trust = map(
        float, trust_means
    )
    if not coprotection_enabled:
        coprotection_trust = float(TRUST_PRIOR[1])
    if not efficacy_enabled:
        efficacy_probability = float(
            v234.JOINT_PRIOR
            @ ((v234.STATE_ETA0 + v234.STATE_ETA1) / 2.0)
        )
    applied_stakes = float(stakes) if stakes_enabled else 0.0
    precision = float(np.clip(future_precision, 0.0, 1.0))
    tolerable_success = outcome_trust * float(policy_outcome_mean)
    vulnerable_risk = 1.0 - tolerable_success
    supported = coprotection_trust * partner_trust * precision
    unsupported_risk = float(
        PARAMETERS["unsupported_risk_weight"]
    ) * (1.0 - supported)
    role_preserving_risk = float(danger_probability) * (
        1.0 - float(efficacy_probability)
    )
    role_absent_risk = float(danger_probability) * (
        1.0 - coprotection_trust * precision
    )
    future_risk = 0.5 * (role_preserving_risk + role_absent_risk)
    complete_risk = vulnerable_risk + unsupported_risk + future_risk
    epistemic = (
        float(PARAMETERS["epistemic_value_test"])
        if epistemic_test_enabled
        else 0.0
    )
    efforts = (
        POLICY_EFFORT.copy()
        if policy_effort is None
        else np.asarray(policy_effort, dtype=float).copy()
    )
    if efforts.shape != (3,):
        raise ValueError("policy_effort must have three entries")
    costs = efforts + applied_stakes * CONTACT_BY_POLICY * complete_risk
    costs = costs.copy()
    costs[POLICY_INDEX["test_contact"]] -= epistemic
    beta = float(
        PARAMETERS["inverse_temperature"]
        if inverse_temperature is None
        else inverse_temperature
    )
    weights = np.exp(-beta * (costs - float(costs.min())))
    q_policy = weights / float(weights.sum())
    permission_mass = float(
        q_policy[POLICY_INDEX["test_contact"]]
        + q_policy[POLICY_INDEX["permit_contact"]]
    )
    contact_rates = (
        CONTACT_BY_POLICY
        if policy_to_contact_enabled
        else np.zeros_like(CONTACT_BY_POLICY)
    )
    contact_probability = float(q_policy @ contact_rates)
    hope = float(PARAMETERS["hope_value"])
    return PolicyReadout(
        q_policy=q_policy,
        expected_cost=costs,
        vulnerable_risk=vulnerable_risk,
        unsupported_risk=unsupported_risk,
        role_preserving_risk=role_preserving_risk,
        role_absent_risk=role_absent_risk,
        role_absence_risk_differential=(
            role_absent_risk - role_preserving_risk
        ),
        hope_preserving=hope,
        hope_absent=hope,
        permission_mass=permission_mass,
        contact_probability=contact_probability,
    )


def score(
    trust_observations: Iterable[TrustObservation],
    partner_observations: Iterable[v26a.PartnerObservation],
    attribution_episodes: Iterable[v234.Episode],
    *,
    stakes: float | None = None,
    lesions: Sequence[str] = (),
    inverse_temperature: float | None = None,
    initial_trust_priors: Sequence[Sequence[float]] | None = None,
    policy_effort: Sequence[float] | None = None,
) -> ProtectorScore:
    sequence = tuple(trust_observations)
    partner_sequence = tuple(partner_observations)
    attribution_sequence = tuple(attribution_episodes)
    lesion_set = set(lesions)
    q_trust, q_outcome, trust_log_evidence = trust_posteriors(
        sequence,
        initial_priors=initial_trust_priors,
        partner_to_trust=("partner_to_trust" not in lesion_set),
    )
    partner_score = v26a.score(
        partner_sequence,
        broadcast=("global_broadcast" not in lesion_set),
    )
    attribution_score = v234.score(attribution_sequence)
    trust_means = [float(item[1]) for item in q_trust]
    policy = policy_posterior(
        trust_means,
        float(q_outcome @ OUTCOME_SUPPORT),
        attribution_score.threat_probability,
        float(np.mean(attribution_score.eta_mean)),
        partner_score.future_precision_forecast,
        float(
            PARAMETERS["default_stakes"]
            if stakes is None
            else stakes
        ),
        stakes_enabled=("stakes" not in lesion_set),
        coprotection_enabled=("coprotection" not in lesion_set),
        efficacy_enabled=("attribution_efficacy" not in lesion_set),
        epistemic_test_enabled=(
            "epistemic_test_policy" not in lesion_set
        ),
        policy_to_contact_enabled=(
            "policy_to_contact" not in lesion_set
        ),
        inverse_temperature=inverse_temperature,
        policy_effort=policy_effort,
    )
    evidence_value = math.exp(max(trust_log_evidence, -700.0))
    state = ProtocolState(
        posterior_store={
            TRUST_NAMES[index]: q_trust[index].copy()
            for index in range(3)
        }
        | {
            "protector_policy": policy.q_policy.copy(),
            "partner_L": partner_score.q_partner.copy(),
            "G": partner_score.q_root.copy(),
            "attribution_theta_eta": attribution_score.posterior.copy(),
        },
        parameter_posterior_store={
            "policy_outcome": q_outcome.copy(),
        },
        evidence_store={
            "protector_forecasts": max(
                evidence_value, np.finfo(float).tiny
            ),
        },
        metadata=MappingProxyType(
            {
                "stage": "V2.6b",
                "action_selection_likelihood": False,
                "lesions": tuple(sorted(lesion_set)),
                "readouts_are_scientific_inputs": False,
            }
        ),
    )
    audit_one_posterior(state)
    return ProtectorScore(
        q_trust=q_trust,
        q_policy_outcome=q_outcome,
        q_policy=policy.q_policy,
        expected_cost=policy.expected_cost,
        permission_mass=policy.permission_mass,
        contact_probability=policy.contact_probability,
        vulnerable_risk=policy.vulnerable_risk,
        unsupported_risk=policy.unsupported_risk,
        role_preserving_risk=policy.role_preserving_risk,
        role_absent_risk=policy.role_absent_risk,
        role_absence_risk_differential=(
            policy.role_absence_risk_differential
        ),
        hope_preserving=policy.hope_preserving,
        hope_absent=policy.hope_absent,
        partner_score=partner_score,
        attribution_score=attribution_score,
        root_movement=partner_score.root_movement,
        transfer=partner_score.transfer,
        state=state,
    )


def _sample_truth(
    seed: int,
    released_block: tuple[int, int] | None,
) -> tuple[tuple[int, int, int], int]:
    rng = _rng(seed, "v26b-truth", released_block)
    trust = tuple(
        int(rng.choice(2, p=TRUST_PRIOR)) for _ in range(3)
    )
    outcome_index = int(rng.choice(len(OUTCOME_PRIOR), p=OUTCOME_PRIOR))
    return trust, outcome_index


def _sample_trust_observations(
    seed: int,
    truth: tuple[int, int, int],
    outcome_index: int,
    length: int,
    released_block: tuple[int, int] | None,
) -> tuple[TrustObservation, ...]:
    reliability = float(PARAMETERS["trust_observation_reliability"])
    observations = []
    for time in range(length):
        rng = _rng(seed, f"v26b-trust-{time}", released_block)
        values = [
            int(
                truth[index]
                if rng.random() < reliability
                else 1 - truth[index]
            )
            for index in range(3)
        ]
        policy_outcome = int(
            rng.random() < OUTCOME_SUPPORT[outcome_index]
        )
        observations.append(
            TrustObservation(
                refusal=True,
                partner_response=values[2],
                outcome=values[0],
                coprotection=values[1],
                policy_outcome=policy_outcome,
                response_reliability=reliability,
            )
        )
    return tuple(observations)


def generate_recovery_world(
    seed: int,
    *,
    length: int | None = None,
    released_block: tuple[int, int] | None = None,
) -> ProtectorWorld:
    count = int(
        PARAMETERS["gate2_length"] if length is None else length
    )
    trust_truth, outcome_index = _sample_truth(seed, released_block)
    partner_world = v26a.generate_recovery_world(
        seed,
        length=count,
        released_block=released_block,
    )
    attribution_world = v234.generate_world(
        seed,
        identifiable=True,
        length=count,
        released_block=released_block,
    )
    observations = _sample_trust_observations(
        seed,
        trust_truth,
        outcome_index,
        count,
        released_block,
    )
    return ProtectorWorld(
        seed=seed,
        trust_truth=trust_truth,
        policy_outcome_index=outcome_index,
        partner_world=partner_world,
        attribution_world=attribution_world,
        trust_observations=observations,
        stakes=float(PARAMETERS["default_stakes"]),
        scenario="recovery",
    )


def _controlled_partner_observations(
    state: int,
    length: int,
    *,
    root_start: int | None = None,
) -> tuple[v26a.PartnerObservation, ...]:
    atom = tuple(
        int(probability >= 0.5) for probability in v26a.EMISSIONS[state]
    )
    return tuple(
        v26a.PartnerObservation(
            atom,
            1 if root_start is not None and time >= root_start else None,
        )
        for time in range(length)
    )


def _controlled_attribution(
    seed: int,
    length: int,
    released_block: tuple[int, int] | None,
    *,
    scenario: str = "partial",
) -> v234.AttributionWorld:
    return v234.generate_controlled_world(
        seed,
        scenario=scenario,
        length=length,
        released_block=released_block,
    )


def generate_control_world(
    seed: int,
    *,
    scenario: str,
    length: int = 12,
    released_block: tuple[int, int] | None = None,
) -> ProtectorWorld:
    reliability = float(PARAMETERS["trust_observation_reliability"])
    truth = (1, 1, 1)
    outcome_index = 2
    stakes = float(PARAMETERS["default_stakes"])
    response: int | None = 1
    response_reliability = reliability
    observed_count = length
    partner_state = v26a.STATE_INDEX["reliable_contingent"]
    root_start: int | None = None
    if scenario == "ambiguous":
        response = None
        observed_count = 2
    elif scenario == "remaining":
        response = 1
        observed_count = 2
    elif scenario == "pressure":
        response = 0
        truth = (1, 1, 0)
        observed_count = 2
        partner_state = v26a.STATE_INDEX["intrusive"]
    elif scenario == "high_stakes":
        stakes = 3.0
    elif scenario == "low_stakes":
        stakes = 0.5
    elif scenario == "high_diagnostic_rupture":
        response_reliability = 0.999
        observed_count = 4
    elif scenario == "low_diagnostic_rupture":
        response_reliability = 0.70
        observed_count = 4
    elif scenario == "no_dyad":
        response = None
        truth = (0, 0, 0)
        outcome_index = 0
        partner_state = v26a.STATE_INDEX["unstable"]
    elif scenario == "decoupled":
        stakes = 3.0
        partner_state = v26a.STATE_INDEX["unstable"]
    elif scenario == "descent":
        root_start = max(2, length // 2)
    observations = []
    if scenario in {"high_diagnostic_rupture", "low_diagnostic_rupture"}:
        for time in range(3):
            observations.append(
                TrustObservation(
                    True, 1, 1, 1, 1, 0.75
                )
            )
        observations.append(
            TrustObservation(
                True, 0, 1, 1, 1, response_reliability
            )
        )
    else:
        for _ in range(observed_count):
            observations.append(
                TrustObservation(
                    refusal=True,
                    partner_response=response,
                    outcome=(
                        None if scenario in {"ambiguous", "no_dyad"} else truth[0]
                    ),
                    coprotection=(
                        None if scenario in {"ambiguous", "no_dyad"} else truth[1]
                    ),
                    policy_outcome=(
                        None if scenario in {"ambiguous", "no_dyad"} else 1
                    ),
                    response_reliability=response_reliability,
                )
            )
    partner_observations = _controlled_partner_observations(
        partner_state,
        max(len(observations), length),
        root_start=root_start,
    )
    if scenario in {"no_dyad", "decoupled"}:
        partner_observations = tuple(
            v26a.PartnerObservation((None, None, None, None), None)
            for _ in range(max(len(observations), length))
        )
    partner_world = v26a.PartnerWorld(
        seed=seed,
        truth_family=v26a.PARTNER_STATES[partner_state],
        truth_path=tuple(
            [partner_state] * len(partner_observations)
        ),
        observations=partner_observations,
        switching=False,
    )
    attribution_world = _controlled_attribution(
        seed,
        max(len(observations), length),
        released_block,
        scenario="partial",
    )
    return ProtectorWorld(
        seed=seed,
        trust_truth=truth,
        policy_outcome_index=outcome_index,
        partner_world=partner_world,
        attribution_world=attribution_world,
        trust_observations=tuple(observations),
        stakes=stakes,
        scenario=scenario,
    )


def finite_information_bounds() -> dict[str, float]:
    reliability = float(PARAMETERS["trust_observation_reliability"])
    trust_bound = math.log(reliability / (1.0 - reliability))
    minimum = float(
        min(
            OUTCOME_SUPPORT.min(),
            1.0 - OUTCOME_SUPPORT.max(),
        )
    )
    maximum = float(
        max(
            OUTCOME_SUPPORT.max(),
            1.0 - OUTCOME_SUPPORT.min(),
        )
    )
    outcome_bound = math.log(maximum / minimum)
    return {
        "B_max_v26b_trust": trust_bound,
        "B_max_v26b_policy_outcome": outcome_bound,
        "implied_binary_change_bound_v26b": math.tanh(trust_bound / 4.0),
    }
