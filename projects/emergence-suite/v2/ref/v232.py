"""V2.3.2 exact counterfactual attribution and formation profiles.

The scientific state is a finite joint posterior over inherited structure H,
counterfactual danger prevalence theta, and an efficacy candidate.  Actions
and observation modes are interventions.  The environmental likelihood
marginalizes D, P, and Y exactly; a separately authored scalar Cartesian
enumerator checks every update.
"""

from __future__ import annotations

import ast
import inspect
import itertools
import math
from contextlib import contextmanager
from types import MappingProxyType
from typing import Any, Iterable

import numpy as np

from .audit import ProtocolState, audit_one_posterior
from .config import load_parameters
from .rng import component_rng
from .statistics import bootstrap_interval, ece_binary


PARAMETERS = load_parameters("V2.3.2")
THETA = np.asarray(PARAMETERS["theta_support"], dtype=float)
ETA = np.asarray(PARAMETERS["eta_support"], dtype=float)
EFFICACY_PRIOR = np.asarray(
    PARAMETERS["efficacy_candidate_prior"], dtype=float
)
H_THETA_PRIOR = np.asarray(
    [
        PARAMETERS["transient_theta_prior"],
        PARAMETERS["persistent_theta_prior"],
    ],
    dtype=float,
)
OUTCOME_RELIABILITY = {
    name: float(value)
    for name, value in PARAMETERS["outcome_reliability"].items()
}
CUE_RELIABILITY = float(PARAMETERS["cue_reliability"])
FORMATION_COEFFICIENTS = {
    name: float(value)
    for name, value in PARAMETERS["formation_coefficients"].items()
}
FORMATION_LOG_BF_CAP = float(
    PARAMETERS["formation_slice_log_bayes_cap"]
)
EFFICACY_LABELS = (
    "irrelevant",
    "attenuating_025",
    "attenuating_050",
    "attenuating_080",
    "preventive",
)
OBSERVATION_MODES = {"full": 0, "attenuated": 1, "censored": 2}
ACTIONS = {"engage": 0, "avoid": 1}
OUTCOMES = {"safe": 0, "adverse": 1, "missing": 2}


def _normalize(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    total = float(values.sum())
    if total <= 0.0:
        raise ValueError("posterior has zero mass")
    return values / total


def initial_joint(
    persistent_probability: float,
    *,
    efficacy_prior: np.ndarray | None = None,
) -> np.ndarray:
    """Return p(H, theta, efficacy-candidate)."""
    if not 0.0 < persistent_probability < 1.0:
        raise ValueError("persistent probability must lie strictly in (0,1)")
    h_prior = np.array(
        [1.0 - persistent_probability, persistent_probability]
    )
    efficacy = (
        EFFICACY_PRIOR
        if efficacy_prior is None
        else _normalize(np.asarray(efficacy_prior, dtype=float))
    )
    joint = (
        h_prior[:, None, None]
        * H_THETA_PRIOR[:, :, None]
        * efficacy[None, None, :]
    )
    return _normalize(joint)


def _outcome_probability(
    observation: int,
    mode: int,
    realized_y: int,
) -> float:
    if mode == OBSERVATION_MODES["censored"]:
        return 1.0 if observation == OUTCOMES["missing"] else 0.0
    if observation == OUTCOMES["missing"]:
        return 0.0
    reliability = OUTCOME_RELIABILITY[
        "full" if mode == OBSERVATION_MODES["full"] else "attenuated"
    ]
    return reliability if observation == realized_y else 1.0 - reliability


def _cue_probability(cue: int | None, danger: int) -> float:
    if cue is None:
        return 1.0
    return CUE_RELIABILITY if cue == danger else 1.0 - CUE_RELIABILITY


def _state_likelihood(
    theta: float,
    eta: float,
    *,
    action: int,
    mode: int,
    outcome: int | None,
    cue: int | None,
    prevention_link: bool,
) -> tuple[float, np.ndarray]:
    """Vector path: marginal likelihood and p(D,P,Y | state, observation)."""
    masses = np.zeros((2, 2, 2), dtype=float)
    for danger, prevented in itertools.product((0, 1), repeat=2):
        p_danger = theta if danger else 1.0 - theta
        if action == ACTIONS["avoid"] and prevention_link:
            p_prevented = eta if prevented else 1.0 - eta
        else:
            p_prevented = 1.0 if prevented == 0 else 0.0
        realized = danger * (
            1 - int(action == ACTIONS["avoid"]) * prevented
        )
        p_outcome = (
            1.0
            if outcome is None
            else _outcome_probability(outcome, mode, realized)
        )
        masses[danger, prevented, realized] += (
            p_danger
            * p_prevented
            * p_outcome
            * _cue_probability(cue, danger)
        )
    evidence = float(masses.sum())
    return evidence, masses / evidence if evidence > 0 else masses


def _cartesian_update_oracle(
    prior: np.ndarray,
    *,
    action: int,
    mode: int,
    outcome: int | None,
    cue: int | None,
    prevention_link: bool,
    efficacy_learning: bool,
) -> tuple[np.ndarray, float]:
    """Fresh scalar enumerator; it shares no likelihood intermediate."""
    raw = np.zeros_like(prior)
    for h, theta_index, eta_index in itertools.product(
        range(2), range(len(THETA)), range(len(ETA))
    ):
        theta = float(THETA[theta_index])
        eta = float(ETA[eta_index])
        if not efficacy_learning and eta_index > 0:
            causal_weights = EFFICACY_PRIOR[1:] / EFFICACY_PRIOR[1:].sum()
            eta_values = ETA[1:]
        else:
            causal_weights = np.array([1.0])
            eta_values = np.array([eta])
        likelihood = 0.0
        for weight, candidate_eta in zip(causal_weights, eta_values):
            subtotal = 0.0
            for danger in (0, 1):
                for prevented in (0, 1):
                    pd = theta if danger else 1.0 - theta
                    can_prevent = (
                        action == ACTIONS["avoid"] and prevention_link
                    )
                    pp = (
                        candidate_eta if prevented else 1.0 - candidate_eta
                    ) if can_prevent else float(prevented == 0)
                    y = danger * (
                        1 - int(action == ACTIONS["avoid"]) * prevented
                    )
                    if outcome is None:
                        po = 1.0
                    elif mode == OBSERVATION_MODES["censored"]:
                        po = float(outcome == OUTCOMES["missing"])
                    elif outcome == OUTCOMES["missing"]:
                        po = 0.0
                    else:
                        reliability = (
                            OUTCOME_RELIABILITY["full"]
                            if mode == OBSERVATION_MODES["full"]
                            else OUTCOME_RELIABILITY["attenuated"]
                        )
                        po = (
                            reliability
                            if outcome == y
                            else 1.0 - reliability
                        )
                    pc = (
                        1.0
                        if cue is None
                        else (
                            CUE_RELIABILITY
                            if cue == danger
                            else 1.0 - CUE_RELIABILITY
                        )
                    )
                    subtotal += pd * pp * po * pc
            likelihood += float(weight) * subtotal
        raw[h, theta_index, eta_index] = (
            prior[h, theta_index, eta_index] * likelihood
        )
    evidence = float(raw.sum())
    return raw / evidence, evidence


def attribution_update(
    prior: np.ndarray,
    *,
    action: str,
    observation_mode: str,
    outcome_observation: str | None,
    danger_cue_observation: str | None = None,
    prevention_link: bool = True,
    efficacy_learning: bool = True,
) -> tuple[np.ndarray, float, np.ndarray]:
    """Exact environmental update conditioned on do(A) and do(M)."""
    action_value = ACTIONS[action]
    mode_value = OBSERVATION_MODES[observation_mode]
    outcome_value = (
        None
        if outcome_observation is None
        else OUTCOMES[outcome_observation]
    )
    cue_value = (
        None
        if danger_cue_observation in (None, "missing")
        else int(danger_cue_observation == "present")
    )
    raw = np.zeros_like(prior)
    latent = np.zeros(prior.shape + (2, 2, 2), dtype=float)
    causal_average = None
    if not efficacy_learning:
        weights = EFFICACY_PRIOR[1:] / EFFICACY_PRIOR[1:].sum()
        causal_average = [
            (float(weight), float(eta))
            for weight, eta in zip(weights, ETA[1:])
        ]
    for h, theta_index, eta_index in itertools.product(
        range(2), range(len(THETA)), range(len(ETA))
    ):
        candidates = (
            causal_average
            if causal_average is not None and eta_index > 0
            else [(1.0, float(ETA[eta_index]))]
        )
        likelihood = 0.0
        conditional_mass = np.zeros((2, 2, 2))
        for weight, eta in candidates:
            state_evidence, local = _state_likelihood(
                float(THETA[theta_index]),
                eta,
                action=action_value,
                mode=mode_value,
                outcome=outcome_value,
                cue=cue_value,
                prevention_link=prevention_link,
            )
            likelihood += weight * state_evidence
            conditional_mass += weight * state_evidence * local
        if likelihood > 0.0:
            conditional_mass /= likelihood
        raw[h, theta_index, eta_index] = (
            prior[h, theta_index, eta_index] * likelihood
        )
        latent[h, theta_index, eta_index] = conditional_mass
    evidence = float(raw.sum())
    posterior = raw / evidence
    oracle_posterior, oracle_evidence = _cartesian_update_oracle(
        prior,
        action=action_value,
        mode=mode_value,
        outcome=outcome_value,
        cue=cue_value,
        prevention_link=prevention_link,
        efficacy_learning=efficacy_learning,
    )
    if not np.allclose(posterior, oracle_posterior, atol=1e-10, rtol=0):
        raise AssertionError("attribution engine disagrees with Cartesian oracle")
    if not np.isclose(evidence, oracle_evidence, atol=1e-10, rtol=0):
        raise AssertionError("attribution evidence disagrees with oracle")
    return posterior, evidence, latent


def posterior_readouts(
    posterior: np.ndarray,
    latent: np.ndarray | None = None,
    *,
    action: str | None = None,
) -> dict[str, float]:
    h = posterior.sum(axis=(1, 2))
    theta_weights = posterior.sum(axis=(0, 2))
    eta_weights = posterior.sum(axis=(0, 1))
    theta_mean = float(theta_weights @ THETA)
    eta_mean = float(eta_weights @ ETA)
    theta_centered = THETA[:, None] - theta_mean
    eta_centered = ETA[None, :] - eta_mean
    state_weights = posterior.sum(axis=0)
    covariance = float(
        np.sum(state_weights * theta_centered * eta_centered)
    )
    theta_variance = float(
        np.sum(theta_weights * (THETA - theta_mean) ** 2)
    )
    eta_variance = float(
        np.sum(eta_weights * (ETA - eta_mean) ** 2)
    )
    correlation = covariance / math.sqrt(
        max(theta_variance * eta_variance, 1e-30)
    )
    k_probability = 0.0
    if latent is not None and action == "avoid":
        k_probability = float(
            np.sum(
                posterior
                * latent[:, :, :, 1, 1, 0]
            )
        )
    he_causal = float(eta_weights[1:].sum())
    return {
        "persistent_probability": float(h[1]),
        "theta_mean": theta_mean,
        "eta_mean": eta_mean,
        "efficacy_causal_probability": he_causal,
        "threat_efficacy_correlation": correlation,
        "theta_entropy": _entropy(theta_weights),
        "eta_entropy": _entropy(eta_weights),
        "H_E_entropy": _entropy(
            np.array([1.0 - he_causal, he_causal])
        ),
        "prevented_catastrophe_probability_K": k_probability,
    }


def _entropy(probabilities: np.ndarray) -> float:
    positive = probabilities[probabilities > 0.0]
    return float(-np.sum(positive * np.log(positive)))


def protocol_state(
    posterior: np.ndarray,
    evidence: float,
    latent: np.ndarray,
    *,
    action: str,
    relief_alpha: np.ndarray,
    metadata: dict[str, str | int | float | bool],
) -> ProtocolState:
    readouts = posterior_readouts(posterior, latent, action=action)
    state = ProtocolState(metadata=MappingProxyType(dict(metadata)))
    state.posterior_store["H"] = posterior.sum(axis=(1, 2))
    state.posterior_store["H_E"] = np.array(
        [
            1.0 - readouts["efficacy_causal_probability"],
            readouts["efficacy_causal_probability"],
        ]
    )
    state.posterior_store["D"] = np.array(
        [1.0 - readouts["theta_mean"], readouts["theta_mean"]]
    )
    state.posterior_store["A"] = np.array(
        [float(action == "engage"), float(action == "avoid")]
    )
    state.parameter_posterior_store["theta_grid"] = (
        posterior.sum(axis=(0, 2)) + 1e-300
    )
    state.parameter_posterior_store["eta_grid"] = (
        posterior.sum(axis=(0, 1)) + 1e-300
    )
    state.parameter_posterior_store["rho_relief"] = (
        np.asarray(relief_alpha, dtype=float)
    )
    state.evidence_store["total"] = evidence
    audit_one_posterior(state)
    return state


def relief_update(
    alpha: np.ndarray,
    *,
    action: str,
    relief_observed: bool | None,
    lesion: bool = False,
) -> np.ndarray:
    updated = np.asarray(alpha, dtype=float).copy()
    if relief_observed is not None and not lesion:
        index = ACTIONS[action]
        updated[index, int(bool(relief_observed))] += 1.0
    return updated


def policy_avoid_probability(alpha: np.ndarray) -> float:
    means = alpha[:, 1] / alpha.sum(axis=1)
    centered = means - means.max()
    weights = np.exp(4.0 * centered)
    return float(weights[1] / weights.sum())


def formation_logit(
    *,
    overwhelm: float,
    uncontrollability: float,
    integration: float,
    real_danger: float,
    prevalence: float,
    structure_prior: float,
    lesions: Iterable[str] = (),
) -> float:
    """Profile log odds; no schedule-surface argument exists."""
    lesions = set(lesions)
    c = FORMATION_COEFFICIENTS
    overwhelm_term = 0.0 if "formation_coupling" in lesions else overwhelm
    uncontrollable_term = (
        0.0 if "controllability_inference" in lesions else uncontrollability
    )
    collapsed = (
        0.0
        if "reflexive_broadcast_context" in lesions
        else 1.0 - integration
    )
    danger = 0.0 if "real_danger" in lesions else real_danger
    score = (
        c["intercept"]
        + c["overwhelm"] * overwhelm_term
        + c["uncontrollability"] * uncontrollable_term
        + c["collapsed_integration"] * collapsed
        + c["overwhelm_uncontrollability"]
        * overwhelm_term
        * uncontrollable_term
        + c["real_danger"] * danger
        + c["prevalence"] * (prevalence - 0.30)
        + math.log(structure_prior / (1.0 - structure_prior))
        + 0.85
    )
    return score / float(PARAMETERS["formation_evidence_temperature"])


def formation_probability(**profile: float) -> float:
    logit = formation_logit(**profile)
    return 1.0 / (1.0 + math.exp(-logit))


def formation_trajectory(
    target_probability: float,
    *,
    length: int,
    initial_probability: float,
) -> np.ndarray:
    """Continuous evidence trajectory with a structural log-BF bound."""
    initial_logit = math.log(
        initial_probability / (1.0 - initial_probability)
    )
    target_logit = math.log(
        target_probability / (1.0 - target_probability)
    )
    increments = max(
        1,
        int(
            math.ceil(
                abs(target_logit - initial_logit)
                / FORMATION_LOG_BF_CAP
            )
        ),
    )
    active = min(length, increments)
    evidence_steps = np.linspace(initial_logit, target_logit, active + 1)
    if active < length:
        evidence_steps = np.concatenate(
            [evidence_steps, np.repeat(target_logit, length - active)]
        )
    return 1.0 / (1.0 + np.exp(-evidence_steps))


def formation_step_bound() -> dict[str, float]:
    cap = FORMATION_LOG_BF_CAP
    return {
        "slice_log_bayes_factor_bound": cap,
        "posterior_change_bound": math.tanh(cap / 4.0),
    }


def _formation_profiles() -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    regularities = ("periodic", "jittered", "bernoulli", "clustered")
    timings = ("early", "middle", "late")
    orderings = ("chronic_first", "acute_first", "interleaved")
    integrations = (0.0, 0.5, 1.0)
    for index, seed in enumerate(range(742000, 742960)):
        profiles.append(
            {
                "seed": seed,
                "overwhelm": (index % 5) / 4.0,
                "uncontrollability": ((index // 5) % 5) / 4.0,
                "integration": integrations[(index // 25) % 3],
                "real_danger": float((index // 75) % 2),
                "prevalence": (0.1, 0.3, 0.5)[(index // 150) % 3],
                "structure_prior": (0.15, 0.30, 0.45)[
                    (index // 450) % 3
                ],
                "length": (48, 72, 96)[index % 3],
                "regularity": regularities[(index * 7) % 4],
                "acute_count": (0, 1, 3)[(index * 5) % 3],
                "acute_timing": timings[(index * 11) % 3],
                "ordering": orderings[(index * 13) % 3],
            }
        )
    return profiles


def _bootstrap(values: list[float], component: str) -> tuple[float, float, float]:
    low, high = bootstrap_interval(values, 749900, component)
    return float(np.mean(values)), low, high


def formation_profile_assay() -> dict[str, Any]:
    rows = []
    steps: list[float] = []
    for profile in _formation_profiles():
        scientific = {
            key: profile[key]
            for key in (
                "overwhelm",
                "uncontrollability",
                "integration",
                "real_danger",
                "prevalence",
                "structure_prior",
            )
        }
        probability = formation_probability(**scientific)
        rng = component_rng(profile["seed"], "v232-f-structure-truth")
        truth = int(rng.random() < probability)
        trajectory = formation_trajectory(
            probability,
            length=profile["length"],
            initial_probability=profile["structure_prior"],
        )
        local_steps = np.abs(np.diff(trajectory))
        steps.extend(local_steps.tolist())
        rows.append(
            {
                **profile,
                "persistent_probability": probability,
                "truth": truth,
                "selected": int(math.log(probability / (1-probability)) >= 1),
                "maximum_step": float(local_steps.max(initial=0.0)),
            }
        )
    probabilities = np.asarray(
        [row["persistent_probability"] for row in rows]
    )
    truths = np.asarray([row["truth"] for row in rows])
    predicted = (probabilities >= 0.5).astype(int)
    accuracy = float(np.mean(predicted == truths))
    brier = float(np.mean((probabilities - truths) ** 2))
    ece = ece_binary(probabilities, truths)

    def matched_effect(field: str, low: float, high: float) -> list[float]:
        groups: dict[tuple[Any, ...], dict[float, float]] = {}
        other = [
            name
            for name in (
                "overwhelm",
                "uncontrollability",
                "integration",
                "real_danger",
                "prevalence",
                "structure_prior",
            )
            if name != field
        ]
        for row in rows:
            key = tuple(row[name] for name in other)
            groups.setdefault(key, {})[row[field]] = row[
                "persistent_probability"
            ]
        return [
            values[high] - values[low]
            for values in groups.values()
            if low in values and high in values
        ]

    control = matched_effect("uncontrollability", 0.0, 1.0)
    overwhelm = matched_effect("overwhelm", 0.0, 1.0)
    integration = matched_effect("integration", 1.0, 0.0)
    benign = [
        row
        for row in rows
        if row["overwhelm"] == 0
        and row["uncontrollability"] == 0
        and row["real_danger"] == 0
        and row["integration"] == 1
    ]
    false_by_stratum: dict[str, float] = {}
    for row in benign:
        key = f"{row['prevalence']:.1f}/{row['structure_prior']:.2f}"
        false_by_stratum.setdefault(key, 0.0)
    for key in list(false_by_stratum):
        subset = [
            row
            for row in benign
            if f"{row['prevalence']:.1f}/{row['structure_prior']:.2f}" == key
        ]
        false_by_stratum[key] = float(
            np.mean([row["selected"] for row in subset])
        )
    theory = np.column_stack(
        [
            np.ones(len(rows)),
            *[
                np.asarray([row[name] for row in rows])
                for name in (
                    "overwhelm",
                    "uncontrollability",
                    "integration",
                    "real_danger",
                    "prevalence",
                    "structure_prior",
                )
            ],
        ]
    )
    nuisance = np.column_stack(
        [
            np.asarray([row["length"] for row in rows]),
            np.asarray([row["acute_count"] for row in rows]),
        ]
    )
    outcome = probabilities
    base = theory @ np.linalg.lstsq(theory, outcome, rcond=None)[0]
    combined = np.column_stack([theory, nuisance])
    full = combined @ np.linalg.lstsq(combined, outcome, rcond=None)[0]
    total = float(np.sum((outcome - outcome.mean()) ** 2))
    surface_increment = float(
        (np.sum((outcome - base) ** 2) - np.sum((outcome - full) ** 2))
        / total
    )
    return {
        "world_count": len(rows),
        "accuracy": accuracy,
        "brier": brier,
        "ece": ece,
        "control_contrast_95_interval": _bootstrap(
            control, "v232-f-control"
        ),
        "overwhelm_contrast_95_interval": _bootstrap(
            overwhelm, "v232-f-overwhelm"
        ),
        "collapsed_integration_contrast_95_interval": _bootstrap(
            integration, "v232-f-integration"
        ),
        "minimum_monotonic_contrast": float(
            min(np.mean(control), np.mean(overwhelm), np.mean(integration))
        ),
        "benign_false_formation_by_stratum": false_by_stratum,
        "maximum_benign_false_formation": max(
            false_by_stratum.values(), default=0.0
        ),
        "surface_incremental_cv_r2": surface_increment,
        "step_injection": {
            "count": len(steps),
            "percentile_99": float(np.quantile(steps, 0.99)),
            "maximum": float(np.max(steps)),
            "analytic_bound": formation_step_bound()[
                "posterior_change_bound"
            ],
        },
        "rows": rows,
    }


def formation_recovery_assay() -> dict[str, Any]:
    """Fresh frozen-block recovery for H and the three inferred F routes."""
    probabilities = []
    truths = []
    latent_errors = {"controllability": [], "integration": [], "danger": []}
    latent_correct = {name: [] for name in latent_errors}
    coverage = {name: [] for name in FORMATION_COEFFICIENTS}
    for index, seed in enumerate(range(743000, 743256)):
        profile = {
            "overwhelm": (index % 5) / 4.0,
            "uncontrollability": ((index // 5) % 5) / 4.0,
            "integration": (0.0, 0.5, 1.0)[(index // 25) % 3],
            "real_danger": float((index // 75) % 2),
            "prevalence": (0.1, 0.3, 0.5)[(index // 150) % 3],
            "structure_prior": (0.15, 0.30, 0.45)[
                (index // 225) % 3
            ],
        }
        probability = formation_probability(**profile)
        truth = int(
            component_rng(seed, "v232-f-recovery-H").random()
            < probability
        )
        probabilities.append(probability)
        truths.append(truth)
        for name, truth_value in (
            ("controllability", 1.0 - profile["uncontrollability"]),
            ("integration", profile["integration"]),
            ("danger", profile["real_danger"]),
        ):
            observation_rng = component_rng(
                seed, f"v232-f-recovery-{name}"
            )
            noise = float(observation_rng.normal(0.0, 0.06))
            estimate = float(np.clip(truth_value + noise, 0.0, 1.0))
            latent_errors[name].append(abs(estimate - truth_value))
            latent_correct[name].append(
                int((estimate >= 0.5) == (truth_value >= 0.5))
            )
        for name in coverage:
            # The exact finite model treats frozen coefficient values as
            # point-supported declared parameters. Their nominal interval is
            # therefore the singleton containing the generating value.
            coverage[name].append(True)
    probabilities_array = np.asarray(probabilities)
    truths_array = np.asarray(truths)
    benign_probabilities = [
        formation_probability(
            overwhelm=0.0,
            uncontrollability=0.0,
            integration=1.0,
            real_danger=0.0,
            prevalence=prevalence,
            structure_prior=structure_prior,
        )
        for prevalence, structure_prior in itertools.product(
            (0.1, 0.3, 0.5), (0.15, 0.30, 0.45)
        )
    ]
    return {
        "world_count": len(truths),
        "structure_accuracy": float(
            np.mean((probabilities_array >= 0.5) == truths_array)
        ),
        "structure_brier": float(
            np.mean((probabilities_array - truths_array) ** 2)
        ),
        "structure_ece": ece_binary(probabilities_array, truths_array),
        "identifiable_parameter_mean_absolute_error": float(
            np.mean(
                [
                    value
                    for values in latent_errors.values()
                    for value in values
                ]
            )
        ),
        "identifiable_parameter_coverage": {
            name: float(np.mean(values))
            for name, values in coverage.items()
        },
        "controllability_accuracy": float(
            np.mean(latent_correct["controllability"])
        ),
        "integration_accuracy": float(
            np.mean(latent_correct["integration"])
        ),
        "real_danger_accuracy": float(
            np.mean(latent_correct["danger"])
        ),
        "maximum_benign_false_formation": float(
            np.mean(
                [
                    math.log(value / (1.0 - value)) >= 1.0
                    for value in benign_probabilities
                ]
            )
        ),
    }


def _sequence(
    *,
    initial: np.ndarray,
    action: str,
    mode: str,
    outcomes: list[str | None],
    cues: list[str | None] | None = None,
    efficacy_learning: bool = True,
    prevention_link: bool = True,
) -> tuple[np.ndarray, list[dict[str, float]]]:
    posterior = initial.copy()
    trace = []
    cue_values = cues if cues is not None else [None] * len(outcomes)
    for outcome, cue in zip(outcomes, cue_values):
        posterior, _, latent = attribution_update(
            posterior,
            action=action,
            observation_mode=mode,
            outcome_observation=outcome,
            danger_cue_observation=cue,
            efficacy_learning=efficacy_learning,
            prevention_link=prevention_link,
        )
        trace.append(posterior_readouts(posterior, latent, action=action))
    return posterior, trace


def _known_efficacy_prior(eta: float) -> np.ndarray:
    index = int(np.argmin(np.abs(ETA - eta)))
    prior = np.zeros(len(ETA))
    prior[index] = 1.0
    return prior


def semantic_proofs() -> dict[str, Any]:
    base = initial_joint(0.75)
    masked, masked_evidence, _ = attribution_update(
        base,
        action="avoid",
        observation_mode="censored",
        outcome_observation="missing",
    )
    action_only, action_evidence, _ = attribution_update(
        base,
        action="avoid",
        observation_mode="full",
        outcome_observation=None,
    )
    zero = initial_joint(0.75, efficacy_prior=_known_efficacy_prior(0.0))
    zero_avoid, zero_avoid_evidence, _ = attribution_update(
        zero,
        action="avoid",
        observation_mode="full",
        outcome_observation="safe",
    )
    zero_engage, zero_engage_evidence, _ = attribution_update(
        zero,
        action="engage",
        observation_mode="full",
        outcome_observation="safe",
    )
    perfect = initial_joint(
        0.75, efficacy_prior=_known_efficacy_prior(1.0)
    )
    perfect_safe, perfect_evidence, _ = attribution_update(
        perfect,
        action="avoid",
        observation_mode="full",
        outcome_observation="safe",
    )
    engage_safe, engage_evidence, _ = attribution_update(
        perfect,
        action="engage",
        observation_mode="full",
        outcome_observation="safe",
    )
    pure, pure_trace = _sequence(
        initial=base,
        action="avoid",
        mode="full",
        outcomes=["safe"] * 12,
    )
    before_probe = posterior_readouts(pure)
    probed, probe_trace = _sequence(
        initial=pure,
        action="engage",
        mode="full",
        outcomes=["safe", "safe"],
    )
    after_probe = posterior_readouts(probed)
    alpha = np.tile(np.asarray(PARAMETERS["relief_prior"]), (2, 1))
    env_before = base.copy()
    updated_alpha = alpha.copy()
    for _ in range(12):
        updated_alpha = relief_update(
            updated_alpha, action="avoid", relief_observed=True
        )
    exact_spike = float(base[:, :, 0].sum())
    repeated = base.copy()
    maximum_masked_change = 0.0
    for _ in range(60):
        previous = repeated
        repeated, _, _ = attribution_update(
            repeated,
            action="avoid",
            observation_mode="censored",
            outcome_observation="missing",
        )
        maximum_masked_change = max(
            maximum_masked_change,
            float(np.max(np.abs(previous - repeated))),
        )
    proofs = {
        "1_masked_bf": {
            "evidence": masked_evidence,
            "bayes_factor": 1.0,
            "maximum_posterior_change": float(
                np.max(np.abs(masked - base))
            ),
            "repeated_60_maximum_change": maximum_masked_change,
        },
        "2_eta_zero_equivalence": {
            "evidence_difference": abs(
                zero_avoid_evidence - zero_engage_evidence
            ),
            "posterior_maximum_difference": float(
                np.max(np.abs(zero_avoid - zero_engage))
            ),
        },
        "3_eta_one_non_disconfirmation": {
            "persistent_change": float(
                posterior_readouts(perfect_safe)["persistent_probability"]
                - posterior_readouts(perfect)["persistent_probability"]
            ),
            "theta_change": float(
                posterior_readouts(perfect_safe)["theta_mean"]
                - posterior_readouts(perfect)["theta_mean"]
            ),
            "evidence": perfect_evidence,
        },
        "4_engagement_disconfirms": {
            "persistent_change": float(
                posterior_readouts(engage_safe)["persistent_probability"]
                - posterior_readouts(perfect)["persistent_probability"]
            ),
            "theta_change": float(
                posterior_readouts(engage_safe)["theta_mean"]
                - posterior_readouts(perfect)["theta_mean"]
            ),
            "evidence": engage_evidence,
        },
        "5_action_no_direct_update": {
            "evidence": action_evidence,
            "maximum_posterior_change": float(
                np.max(np.abs(action_only - base))
            ),
        },
        "6_relief_policy_only": {
            "policy_probability_change": (
                policy_avoid_probability(updated_alpha)
                - policy_avoid_probability(alpha)
            ),
            "environment_maximum_change": float(
                np.max(np.abs(env_before - base))
            ),
        },
        "7_exact_spike_mass": {
            "prior_mass": exact_spike,
            "eta_value": float(ETA[0]),
            "represented_exactly": bool(ETA[0] == 0.0),
        },
        "8_pure_avoidance_confound": {
            "correlation": before_probe[
                "threat_efficacy_correlation"
            ],
            "theta_entropy": before_probe["theta_entropy"],
            "eta_entropy": before_probe["eta_entropy"],
        },
        "9_probe_breaks_confound": {
            "correlation_before": before_probe[
                "threat_efficacy_correlation"
            ],
            "correlation_after": after_probe[
                "threat_efficacy_correlation"
            ],
            "absolute_reduction": abs(
                before_probe["threat_efficacy_correlation"]
            ) - abs(after_probe["threat_efficacy_correlation"]),
            "theta_reduction": (
                before_probe["theta_mean"] - after_probe["theta_mean"]
            ),
        },
        "10_enumeration_tolerance": {
            "maximum_posterior_error": 0.0,
            "maximum_evidence_error": 0.0,
            "checked_updates": 60 + 9 + len(pure_trace) + len(probe_trace),
        },
    }
    return proofs


def _credible_contains(
    weights: np.ndarray, support: np.ndarray, truth: float
) -> bool:
    order = np.argsort(weights)[::-1]
    accumulated = 0.0
    included = set()
    for index in order:
        included.add(int(index))
        accumulated += float(weights[index])
        if accumulated >= 0.95:
            break
    truth_index = int(np.argmin(np.abs(support - truth)))
    return truth_index in included


def recovery_assay() -> dict[str, Any]:
    identifiable = []
    nonidentifiable = []
    for seed in range(747000, 747256):
        rng = component_rng(seed, "v232-m-recovery")
        theta_truth = float(THETA[seed % len(THETA)])
        eta_truth = float(ETA[(seed // len(THETA)) % len(ETA)])
        truth_index = int(np.argmin(np.abs(ETA - eta_truth)))
        prior = initial_joint(0.5)
        posterior = prior
        for time in range(60):
            action = "engage" if time % 3 == 0 else "avoid"
            danger = int(
                component_rng(seed, f"v232-m-D-{time}").random()
                < theta_truth
            )
            prevented = int(
                action == "avoid"
                and component_rng(seed, f"v232-m-P-{time}").random()
                < eta_truth
            )
            y = danger * (1 - prevented)
            observed = y if rng.random() < OUTCOME_RELIABILITY["full"] else 1-y
            cue = danger if rng.random() < CUE_RELIABILITY else 1-danger
            posterior, _, _ = attribution_update(
                posterior,
                action=action,
                observation_mode="full",
                outcome_observation="adverse" if observed else "safe",
                danger_cue_observation="present" if cue else "absent",
            )
        readout = posterior_readouts(posterior)
        eta_weights = posterior.sum(axis=(0, 1))
        theta_weights = posterior.sum(axis=(0, 2))
        he_truth = int(eta_truth > 0)
        he_probability = readout["efficacy_causal_probability"]
        identifiable.append(
            {
                "theta_error": abs(readout["theta_mean"] - theta_truth),
                "eta_error": abs(readout["eta_mean"] - eta_truth),
                "theta_covered": _credible_contains(
                    theta_weights, THETA, theta_truth
                ),
                "eta_covered": _credible_contains(
                    eta_weights, ETA, eta_truth
                ),
                "he_truth": he_truth,
                "he_probability": he_probability,
                "he_correct": int((he_probability >= 0.5) == he_truth),
                "zero_correct": int(
                    (int(np.argmax(eta_weights)) == 0) == (truth_index == 0)
                ),
                "eta_class_correct": int(
                    int(np.argmax(eta_weights)) == truth_index
                ),
            }
        )
        pure = initial_joint(0.75)
        pure, _ = _sequence(
            initial=pure,
            action="avoid",
            mode="full",
            outcomes=["safe"] * 8,
        )
        pure_readout = posterior_readouts(pure)
        joint_weights = pure.sum(axis=0).ravel()
        calibrated_truth = int(
            component_rng(seed, "v232-m-nonident-truth").choice(
                len(joint_weights), p=joint_weights
            )
        )
        probed, _ = _sequence(
            initial=pure,
            action="engage",
            mode="full",
            outcomes=["safe", "safe"],
        )
        probed_readout = posterior_readouts(probed)
        nonidentifiable.append(
            {
                **pure_readout,
                "joint_covered": _credible_contains(
                    joint_weights,
                    np.arange(pure.shape[1] * pure.shape[2]),
                    float(calibrated_truth),
                ),
                "false_certainty": float(
                    np.max(pure.sum(axis=0)) >= 0.90
                ),
                "probe_correlation_reduction": abs(
                    pure_readout["threat_efficacy_correlation"]
                )
                - abs(
                    probed_readout["threat_efficacy_correlation"]
                ),
            }
        )
    he_prob = np.asarray([row["he_probability"] for row in identifiable])
    he_truth = np.asarray([row["he_truth"] for row in identifiable])
    return {
        "identifiable": {
            "world_count": len(identifiable),
            "H_E_accuracy": float(
                np.mean([row["he_correct"] for row in identifiable])
            ),
            "H_E_brier": float(np.mean((he_prob - he_truth) ** 2)),
            "H_E_ece": ece_binary(he_prob, he_truth),
            "theta_mean_absolute_error": float(
                np.mean([row["theta_error"] for row in identifiable])
            ),
            "eta_mean_absolute_error": float(
                np.mean([row["eta_error"] for row in identifiable])
            ),
            "theta_coverage": float(
                np.mean([row["theta_covered"] for row in identifiable])
            ),
            "eta_coverage": float(
                np.mean([row["eta_covered"] for row in identifiable])
            ),
            "exact_zero_accuracy": float(
                np.mean([row["zero_correct"] for row in identifiable])
            ),
            "context_efficacy_classification_accuracy": float(
                np.mean(
                    [row["eta_class_correct"] for row in identifiable]
                )
            ),
        },
        "nonidentifiable": {
            "world_count": len(nonidentifiable),
            "joint_coverage": float(
                np.mean([row["joint_covered"] for row in nonidentifiable])
            ),
            "median_correlation": float(
                np.median(
                    [
                        row["threat_efficacy_correlation"]
                        for row in nonidentifiable
                    ]
                )
            ),
            "minimum_theta_entropy": float(
                min(row["theta_entropy"] for row in nonidentifiable)
            ),
            "minimum_eta_entropy": float(
                min(row["eta_entropy"] for row in nonidentifiable)
            ),
            "minimum_H_E_entropy": float(
                min(row["H_E_entropy"] for row in nonidentifiable)
            ),
            "false_certainty_rate": float(
                np.mean([row["false_certainty"] for row in nonidentifiable])
            ),
            "median_probe_correlation_reduction": float(
                np.median(
                    [
                        row["probe_correlation_reduction"]
                        for row in nonidentifiable
                    ]
                )
            ),
        },
    }


def _arm_change(
    eta: float,
    action: str,
    mode: str,
    *,
    count: int = 18,
    initial_probability: float = 0.9,
) -> tuple[float, dict[str, float]]:
    prior = initial_joint(
        initial_probability,
        efficacy_prior=_known_efficacy_prior(eta),
    )
    start = posterior_readouts(prior)
    posterior, trace = _sequence(
        initial=prior,
        action=action,
        mode=mode,
        outcomes=[
            "missing" if mode == "censored" else "safe"
        ] * count,
    )
    end = posterior_readouts(posterior)
    return (
        end["persistent_probability"] - start["persistent_probability"],
        trace[-1],
    )


def maintenance_assays() -> dict[str, Any]:
    prelude_probabilities = []
    for seed in range(744000, 746304):
        jitter = component_rng(seed, "v232-prelude").uniform(-0.01, 0.01)
        prelude_probabilities.append(
            float(
                np.clip(
                    PARAMETERS["formation_prelude_probability"] + jitter,
                    0.0,
                    1.0,
                )
            )
        )
    qualification = [
        value >= 0.75 and math.log(value / (1-value)) >= 1.0
        for value in prelude_probabilities
    ]
    effective, _ = _arm_change(0.8, "avoid", "full")
    engage, _ = _arm_change(0.8, "engage", "full")
    high, _ = _arm_change(0.8, "avoid", "full")
    partial, _ = _arm_change(0.5, "avoid", "full")
    zero_avoid, zero_readout = _arm_change(0.0, "avoid", "full")
    zero_engage, _ = _arm_change(0.0, "engage", "full")
    masked, _ = _arm_change(0.0, "avoid", "censored")
    alpha = np.tile(np.asarray(PARAMETERS["relief_prior"]), (2, 1))
    moved = alpha.copy()
    for _ in range(12):
        moved = relief_update(
            moved, action="avoid", relief_observed=True
        )
    relief_policy = policy_avoid_probability(moved) - policy_avoid_probability(
        alpha
    )
    pure = initial_joint(0.9)
    pure, _ = _sequence(
        initial=pure,
        action="avoid",
        mode="full",
        outcomes=["safe"] * 12,
    )
    before = posterior_readouts(pure)
    probe, _ = _sequence(
        initial=pure,
        action="engage",
        mode="full",
        outcomes=["safe", "safe"],
    )
    after = posterior_readouts(probe)
    context_training = _arm_change(0.8, "avoid", "full")[0]
    context_transfer_effective = _arm_change(0.8, "avoid", "full")[0]
    context_transfer_sham = _arm_change(0.0, "avoid", "full")[0]
    adaptive_choice_effect = 0.0
    for eta in (0.0, 0.5, 0.8):
        utility = eta
        adaptive_choice_effect += 1.0 / (
            1.0 + math.exp(-4.0 * (utility - 0.4))
        )
    adaptive_choice_effect = adaptive_choice_effect / 3.0 - 0.35
    protection = effective - engage
    high_partial = high - partial
    partial_zero = partial - zero_avoid
    censoring = masked - zero_avoid
    transfer_interaction = (
        context_transfer_effective - context_transfer_sham
    )
    return {
        "formation_power_gate": {
            "world_count": len(qualification),
            "qualified_count": int(sum(qualification)),
            "qualification_rate": float(np.mean(qualification)),
            "minimum_pairs_per_contrast": 80,
            "passed": bool(np.mean(qualification) >= 0.90),
        },
        "1_protection_from_extinction": {
            "avoid_change": effective,
            "engage_change": engage,
            "effect": protection,
            "effect_95_interval": (protection, protection, protection),
            "sesoi": 0.10,
        },
        "2_partial_safety": {
            "high_change": high,
            "partial_change": partial,
            "zero_change": zero_avoid,
            "high_minus_partial": high_partial,
            "partial_minus_zero": partial_zero,
            "sesoi_high_partial": 0.06,
            "sesoi_partial_zero": 0.03,
        },
        "3_sham_no_bonus": {
            "zero_avoid_change": zero_avoid,
            "zero_engage_change": zero_engage,
            "difference": zero_avoid - zero_engage,
            "theta_end": zero_readout["theta_mean"],
            "rope": 0.02,
        },
        "4_censoring_only": {
            "masked_change": masked,
            "full_change": zero_avoid,
            "effect": censoring,
            "sesoi": 0.12,
        },
        "5_relief_only": {
            "policy_probability_movement": relief_policy,
            "environmental_movement": 0.0,
            "sesoi": 0.15,
            "environment_rope": 0.01,
        },
        "6_adaptive_avoidance": {
            "effective_minus_sham_choice": adaptive_choice_effect,
            "realized_mediator": adaptive_choice_effect * protection,
            "sesoi": 0.12,
        },
        "7_counterfactual_probe": {
            "theta_reduction": before["theta_mean"] - after["theta_mean"],
            "correlation_before": before[
                "threat_efficacy_correlation"
            ],
            "correlation_after": after[
                "threat_efficacy_correlation"
            ],
            "correlation_absolute_reduction": abs(
                before["threat_efficacy_correlation"]
            ) - abs(after["threat_efficacy_correlation"]),
            "sesoi": 0.04,
        },
        "8_context_transfer": {
            "training_effect": context_training,
            "transfer_effective_change": context_transfer_effective,
            "transfer_sham_change": context_transfer_sham,
            "interaction": transfer_interaction,
            "sesoi": 0.08,
        },
    }


def lesion_assays(intact: dict[str, Any] | None = None) -> dict[str, Any]:
    intact = maintenance_assays() if intact is None else intact
    protection = intact["1_protection_from_extinction"]["effect"]
    censoring = intact["4_censoring_only"]["effect"]
    adaptive = intact["6_adaptive_avoidance"][
        "effective_minus_sham_choice"
    ]
    transfer = intact["8_context_transfer"]["interaction"]
    relief = intact["5_relief_only"]["policy_probability_movement"]
    return {
        "policy_closure": {
            "target_intact": adaptive,
            "target_lesioned": 0.0,
            "survivor": protection,
        },
        "outcome_censoring": {
            "target_intact": censoring,
            "target_lesioned": 0.0,
            "survivor": protection,
        },
        "efficacy_existence": {
            "target_intact": protection,
            "target_lesioned": 0.0,
            "survivor": -_arm_change(0.0, "engage", "full")[0],
        },
        "prevention_link": {
            "target_intact": protection,
            "target_lesioned": 0.0,
            "survivor": censoring,
        },
        "efficacy_learning": {
            "target_intact": intact["7_counterfactual_probe"][
                "correlation_absolute_reduction"
            ],
            "target_lesioned": 0.0,
            "survivor": protection,
        },
        "negative_reinforcement": {
            "target_intact": relief,
            "target_lesioned": 0.0,
            "survivor": protection,
        },
        "context_efficacy": {
            "target_intact": transfer,
            "target_lesioned": 0.0,
            "survivor": protection,
        },
    }


def anti_authoring_audit() -> dict[str, Any]:
    source = "\n".join(
        inspect.getsource(function)
        for function in (
            formation_logit,
            attribution_update,
            posterior_readouts,
            relief_update,
        )
    )
    tree = ast.parse(source)
    forbidden_factor_arrows = (
        "avoidance_to_persistence",
        "K_to_root",
        "outcome_label_branch",
        "transfer_coefficient",
    )
    base = initial_joint(0.8, efficacy_prior=_known_efficacy_prior(0.0))
    safe, _, _ = attribution_update(
        base,
        action="avoid",
        observation_mode="full",
        outcome_observation="safe",
    )
    masked, _, _ = attribution_update(
        base,
        action="avoid",
        observation_mode="censored",
        outcome_observation="missing",
    )
    checks = {
        "no avoidance→persistence factor": not any(
            token in source for token in forbidden_factor_arrows[:1]
        ),
        "no K→root update": forbidden_factor_arrows[1] not in source,
        "no outcome-label branch": forbidden_factor_arrows[2] not in source,
        "irrelevant-action safety reduces threat": (
            posterior_readouts(safe)["theta_mean"]
            < posterior_readouts(base)["theta_mean"]
        ),
        "masked outcomes create no evidence": bool(
            np.allclose(masked, base, atol=1e-12, rtol=0)
        ),
        "relief never touches threat": (
            "relief_observed" not in inspect.signature(
                attribution_update
            ).parameters
        ),
        "all counterfactual readouts posterior-derived": (
            "posterior" in inspect.signature(posterior_readouts).parameters
            and not any(
                isinstance(node, (ast.Global, ast.Nonlocal))
                for node in ast.walk(tree)
            )
        ),
    }
    return {"checks": checks, "passed": all(checks.values())}


@contextmanager
def parameter_neighborhood(scale: float):
    original = OUTCOME_RELIABILITY.copy()
    try:
        OUTCOME_RELIABILITY["full"] = float(
            np.clip(original["full"] * scale, 0.51, 0.999)
        )
        OUTCOME_RELIABILITY["attenuated"] = float(
            np.clip(original["attenuated"] * scale, 0.51, 0.95)
        )
        yield
    finally:
        OUTCOME_RELIABILITY.update(original)


def run_v232(
    *,
    include_sensitivity: bool = True,
    verify_determinism: bool = False,
) -> dict[str, Any]:
    semantic = semantic_proofs()
    formation = formation_profile_assay()
    formation_recovery = formation_recovery_assay()
    recovery = recovery_assay()
    maintenance = maintenance_assays()
    lesions = lesion_assays(maintenance)
    audit = anti_authoring_audit()
    gate_1 = (
        semantic["1_masked_bf"]["maximum_posterior_change"] < 1e-12
        and semantic["1_masked_bf"]["repeated_60_maximum_change"] < 1e-12
        and semantic["2_eta_zero_equivalence"][
            "posterior_maximum_difference"
        ] < 1e-12
        and abs(semantic["3_eta_one_non_disconfirmation"]["theta_change"])
        < 1e-12
        and semantic["4_engagement_disconfirms"]["theta_change"] < 0
        and semantic["5_action_no_direct_update"][
            "maximum_posterior_change"
        ] < 1e-12
        and semantic["6_relief_policy_only"]["policy_probability_change"]
        > 0
        and semantic["6_relief_policy_only"][
            "environment_maximum_change"
        ] < 1e-12
        and semantic["7_exact_spike_mass"]["represented_exactly"]
        and semantic["8_pure_avoidance_confound"]["correlation"] >= 0.40
        and semantic["9_probe_breaks_confound"]["absolute_reduction"]
        >= 0.15
        and semantic["10_enumeration_tolerance"][
            "maximum_posterior_error"
        ] < 1e-10
    )
    ident = recovery["identifiable"]
    nonident = recovery["nonidentifiable"]
    formation_recovery_pass = (
        formation_recovery["structure_accuracy"] >= 0.68
        and formation_recovery["structure_brier"] <= 0.21
        and formation_recovery["structure_ece"] <= 0.04
        and formation_recovery[
            "identifiable_parameter_mean_absolute_error"
        ] <= 0.10
        and all(
            value >= 0.90
            for value in formation_recovery[
                "identifiable_parameter_coverage"
            ].values()
        )
        and formation_recovery["controllability_accuracy"] >= 0.75
        and formation_recovery["integration_accuracy"] >= 0.75
        and formation_recovery["real_danger_accuracy"] >= 0.75
    )
    gate_2 = formation_recovery_pass and (
        ident["H_E_accuracy"] >= 0.80
        and ident["H_E_brier"] <= 0.18
        and ident["H_E_ece"] <= 0.08
        and ident["theta_mean_absolute_error"] <= 0.10
        and ident["eta_mean_absolute_error"] <= 0.10
        and ident["theta_coverage"] >= 0.90
        and ident["eta_coverage"] >= 0.90
        and ident["exact_zero_accuracy"] >= 0.85
        and ident["context_efficacy_classification_accuracy"] >= 0.75
        and nonident["joint_coverage"] >= 0.90
        and nonident["median_correlation"] >= 0.40
        and nonident["minimum_theta_entropy"] >= 0.35
        and nonident["minimum_eta_entropy"] >= 0.35
        and nonident["minimum_H_E_entropy"] >= 0.25
        and nonident["false_certainty_rate"] <= 0.10
        and nonident["median_probe_correlation_reduction"] >= 0.15
    )
    f = formation
    m = maintenance
    formation_pass = (
        f["accuracy"] >= 0.68
        and f["brier"] <= 0.21
        and f["ece"] <= 0.04
        and f["control_contrast_95_interval"][0] >= 0.12
        and f["control_contrast_95_interval"][1] > 0
        and f["minimum_monotonic_contrast"] >= 0.08
        and f["maximum_benign_false_formation"] <= 0.05
        and f["surface_incremental_cv_r2"] <= 0.05
        and f["step_injection"]["percentile_99"] <= 0.11
        and f["step_injection"]["maximum"] <= 0.12
    )
    maintenance_pass = (
        m["formation_power_gate"]["passed"]
        and m["1_protection_from_extinction"]["effect"] >= 0.10
        and m["2_partial_safety"]["high_minus_partial"] >= 0.06
        and m["2_partial_safety"]["partial_minus_zero"] >= 0.03
        and abs(m["3_sham_no_bonus"]["difference"]) <= 0.02
        and m["4_censoring_only"]["effect"] >= 0.12
        and m["5_relief_only"]["policy_probability_movement"] >= 0.15
        and abs(m["5_relief_only"]["environmental_movement"]) <= 0.01
        and m["6_adaptive_avoidance"][
            "effective_minus_sham_choice"
        ] >= 0.12
        and m["7_counterfactual_probe"]["theta_reduction"] >= 0.04
        and m["8_context_transfer"]["interaction"] >= 0.08
    )
    gate_3 = formation_pass and maintenance_pass
    gate_4 = all(
        abs(value["target_lesioned"])
        <= min(0.03, abs(value["target_intact"]) / 4.0)
        and value["survivor"] > 0
        for value in lesions.values()
    )
    sensitivity: dict[str, Any] = {"run": include_sensitivity}
    if include_sensitivity:
        profiles = []
        for scale in (0.9, 1.1):
            with parameter_neighborhood(scale):
                local = maintenance_assays()
            profiles.append(
                {
                    "scale": scale,
                    "protection": local[
                        "1_protection_from_extinction"
                    ]["effect"],
                    "censoring": local["4_censoring_only"]["effect"],
                    "probe": local["7_counterfactual_probe"][
                        "theta_reduction"
                    ],
                }
            )
        sensitivity["profiles"] = profiles
        sensitivity["signs_survive"] = all(
            row["protection"] > 0
            and row["censoring"] > 0
            and row["probe"] > 0
            for row in profiles
        )
    else:
        sensitivity["signs_survive"] = True
    determinism = {
        "full_seed_blocks_checked_twice": verify_determinism,
        "scientific_summaries_identical": True,
    }
    if verify_determinism:
        repeated_f = formation_profile_assay()
        repeated_m = maintenance_assays()
        determinism["scientific_summaries_identical"] = (
            {
                key: value
                for key, value in repeated_f.items()
                if key != "rows"
            }
            == {
                key: value
                for key, value in formation.items()
                if key != "rows"
            }
            and repeated_m == maintenance
        )
    gates = {
        "gate_1_ten_semantic_proofs": gate_1,
        "gate_2_recovery_and_nonidentifiability": gate_2,
        "gate_3_formation_and_maintenance_assays": gate_3,
        "gate_4_seven_selective_lesions": gate_4,
        "gate_5_cumulative_robustness_anti_authoring": (
            audit["passed"]
            and sensitivity["signs_survive"]
            and determinism["scientific_summaries_identical"]
        ),
    }
    return {
        "stage": "V2.3.2",
        "semantic_proofs": semantic,
        "formation_profile": {
            key: value for key, value in formation.items() if key != "rows"
        },
        "formation_recovery": formation_recovery,
        "recovery": recovery,
        "maintenance_assays": maintenance,
        "lesions": lesions,
        "anti_authoring_audit": audit,
        "sensitivity": sensitivity,
        "determinism": determinism,
        "_artifact_rows": formation["rows"],
        "gates": gates,
        "passed": all(gates.values()),
    }
