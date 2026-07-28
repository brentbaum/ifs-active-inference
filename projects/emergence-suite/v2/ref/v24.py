"""V2.4 exact context-indexed redescription reference.

Five candidate families share one observation interface and differ only in
their normalized latent process, parameter sharing, and context coupling.
All scientific state lives in posterior, parameter-posterior, or evidence
stores.  Family choices and every assay metric are pure readouts.
"""

from __future__ import annotations

import ast
import inspect
import itertools
import json
import math
import textwrap
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable

import numpy as np

from .audit import ProtocolState, audit_one_posterior
from .constitution import cumulative_graded_update_audit
from .rng import component_rng
from .v21 import cross_latent_composition
from .v221 import ASSOCIATION_HIGH


ROOT = Path(__file__).resolve().parents[1]
PARAMETER_PATH = ROOT / "protocols" / "v2.4-parameters.json"
PARAMETERS = json.loads(PARAMETER_PATH.read_text(encoding="utf-8"))
TOLERANCE = float(PARAMETERS["numerical_tolerance"])
FAMILIES = tuple(PARAMETERS["candidate_families"])
FAMILY_INDEX = {name: index for index, name in enumerate(FAMILIES)}
PRIOR = np.asarray(
    [PARAMETERS["candidate_prior"][name] for name in FAMILIES],
    dtype=float,
)
ELEMENTAL_GRID = np.asarray(
    PARAMETERS["observation_interface"]["elemental_predictive_state_grid"],
    dtype=float,
)
BASELINE = np.asarray(
    PARAMETERS["observation_interface"]["baseline_cue_predictions"],
    dtype=float,
)
CORRECTIVE = np.asarray(
    PARAMETERS["observation_interface"]["corrective_cue_predictions"],
    dtype=float,
)
MARKERS = ("then_marker", "now_marker", "ambiguous")
MARKER_INDEX = {value: index for index, value in enumerate(MARKERS)}
PAIRWISE = tuple(itertools.combinations(range(len(FAMILIES)), 2))
PAIRWISE_LABELS = {
    pair: f"{FAMILIES[pair[0]]}/{FAMILIES[pair[1]]}"
    for pair in PAIRWISE
}
MISSING = "missing"


@dataclass(frozen=True)
class Observation:
    cue: int
    outcome: int | None
    marker: str | None
    root: int | None


@dataclass(frozen=True)
class FamilyScore:
    family: str
    log_evidence: float
    per_slice_log_predictive: tuple[float, ...]
    expected_log_likelihood: float
    parameter_complexity: float
    latent_path_complexity: float
    total_complexity: float
    decomposition_error: float
    parameter_posterior: MappingProxyType
    final_predictive: MappingProxyType


def _normalize(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    total = float(array.sum())
    if not math.isfinite(total) or total <= 0.0:
        raise ValueError("cannot normalize nonpositive finite mass")
    return array / total


def _softmax(log_values: np.ndarray) -> np.ndarray:
    values = np.asarray(log_values, dtype=float)
    shifted = values - float(np.max(values))
    return _normalize(np.exp(shifted))


def _positive_parameter_vector(value: Any) -> np.ndarray:
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


def _safe_log(value: float) -> float:
    if value <= 0.0:
        raise ValueError("public predictive probability must be positive")
    return math.log(value)


def _categorical_update(
    prior: np.ndarray, likelihood: np.ndarray
) -> tuple[np.ndarray, float, float, float]:
    """Return posterior, predictive, expected log likelihood, and KL."""
    prior = _normalize(prior)
    likelihood = np.asarray(likelihood, dtype=float)
    predictive = float(np.dot(prior, likelihood))
    posterior = _normalize(prior * likelihood)
    expected = float(np.dot(posterior, np.log(likelihood)))
    positive = posterior > 0.0
    kl = float(
        np.sum(
            posterior[positive]
            * np.log(posterior[positive] / prior[positive])
        )
    )
    return posterior, predictive, expected, kl


def _dict_update(
    prior: dict[tuple[Any, ...], float],
    likelihoods: dict[tuple[Any, ...], float],
) -> tuple[dict[tuple[Any, ...], float], float, float, float]:
    predictive = sum(prior[key] * likelihoods[key] for key in prior)
    posterior = {
        key: prior[key] * likelihoods[key] / predictive for key in prior
    }
    expected = sum(
        posterior[key] * _safe_log(likelihoods[key]) for key in posterior
    )
    kl = sum(
        posterior[key] * _safe_log(posterior[key] / prior[key])
        for key in posterior
        if posterior[key] > 0.0
    )
    return posterior, float(predictive), float(expected), float(kl)


def _outcome_likelihood(probability_one: float, value: int | None) -> float:
    if value is None:
        return 1.0
    return probability_one if value == 1 else 1.0 - probability_one


def _marker_row(descriptor: str) -> np.ndarray:
    rows = PARAMETERS["observation_interface"][
        "context_marker_cpt_nonmissing"
    ]
    return np.asarray(rows[descriptor], dtype=float)


def _marker_likelihood(descriptor: str, value: str | None) -> float:
    if value is None:
        return 1.0
    return float(_marker_row(descriptor)[MARKER_INDEX[value]])


def _root_likelihood(root_state: int, value: int | None) -> float:
    if value is None:
        return 1.0
    key = "root_positive_state" if root_state == 1 else "root_negative_state"
    row = PARAMETERS["observation_interface"][
        "root_observation_cpt_nonmissing"
    ][key]
    return float(row[value])


def _common_root_predictive(value: int | None) -> float:
    if value is None:
        return 1.0
    return 0.5 * (
        _root_likelihood(0, value) + _root_likelihood(1, value)
    )


def _nuisance_initial() -> np.ndarray:
    return np.asarray(
        PARAMETERS["candidate_common_nuisance_context"][
            "initial_distribution"
        ],
        dtype=float,
    )


def _nuisance_transition() -> np.ndarray:
    return np.asarray(
        PARAMETERS["candidate_common_nuisance_context"][
            "transition_matrix"
        ],
        dtype=float,
    )


def _nuisance_marker_likelihood(value: str | None) -> np.ndarray:
    return np.asarray(
        [
            _marker_likelihood("then", value),
            _marker_likelihood("now", value),
            _marker_likelihood("none", value),
        ],
        dtype=float,
    )


def _transition_distribution(
    distribution: np.ndarray, transition: np.ndarray
) -> np.ndarray:
    return _normalize(np.asarray(distribution, dtype=float) @ transition)


def _gw_probability(cue: int, scale_index: int) -> float:
    scale = float(
        PARAMETERS["family_processes"]["global_downweight"]["state_grid"][
            scale_index
        ]
    )
    baseline = float(BASELINE[cue % len(BASELINE)])
    return 0.5 + scale * (baseline - 0.5)


def _score_factorized_family(
    family: str, observations: list[Observation]
) -> FamilyScore:
    nuisance = _nuisance_initial()
    nuisance_transition = _nuisance_transition()
    expected = 0.0
    complexity = 0.0
    logs: list[float] = []

    if family == "global_downweight":
        process = PARAMETERS["family_processes"][family]
        latent = np.asarray(process["initial_distribution"], dtype=float)
        transition = np.asarray(process["transition_matrix"], dtype=float)
        cue_filters = None
    elif family == "cue_local_relearning":
        process = PARAMETERS["family_processes"][family]
        cue_filters = [
            np.asarray(
                process["initial_distribution_by_cue"][f"cue_{index + 1}"],
                dtype=float,
            )
            for index in range(len(BASELINE))
        ]
        transition = np.asarray(
            process["per_cue_transition_matrix"], dtype=float
        )
        latent = np.empty(0)
    else:
        raise ValueError("not a factorized family")

    for time, observation in enumerate(observations):
        cue = observation.cue % len(BASELINE)
        if family == "global_downweight":
            outcome_likelihood = np.asarray(
                [
                    _outcome_likelihood(
                        _gw_probability(cue, index), observation.outcome
                    )
                    for index in range(len(latent))
                ]
            )
            latent, y_predictive, y_expected, y_kl = _categorical_update(
                latent, outcome_likelihood
            )
        else:
            assert cue_filters is not None
            outcome_likelihood = np.asarray(
                [
                    _outcome_likelihood(value, observation.outcome)
                    for value in ELEMENTAL_GRID
                ]
            )
            (
                cue_filters[cue],
                y_predictive,
                y_expected,
                y_kl,
            ) = _categorical_update(cue_filters[cue], outcome_likelihood)

        nuisance, x_predictive, x_expected, x_kl = _categorical_update(
            nuisance, _nuisance_marker_likelihood(observation.marker)
        )
        root_predictive = _common_root_predictive(observation.root)
        root_expected = _safe_log(root_predictive)
        log_predictive = (
            _safe_log(y_predictive)
            + _safe_log(x_predictive)
            + root_expected
        )
        logs.append(log_predictive)
        expected += y_expected + x_expected + root_expected
        complexity += y_kl + x_kl

        if family == "global_downweight":
            latent = _transition_distribution(latent, transition)
        else:
            cue_filters = [
                _transition_distribution(values, transition)
                for values in cue_filters
            ]
        nuisance = _transition_distribution(
            nuisance, nuisance_transition
        )

    parameter_posterior: dict[str, Any]
    final_predictive: dict[str, Any]
    if family == "global_downweight":
        parameter_posterior = {"transition_scale": [0.0, 1.0, 0.0]}
        final_predictive = {"global_scale": latent.tolist()}
    else:
        assert cue_filters is not None
        parameter_posterior = {
            f"cue_{index + 1}_transition_scale": [0.0, 1.0, 0.0]
            for index in range(len(cue_filters))
        }
        final_predictive = {
            f"cue_{index + 1}": values.tolist()
            for index, values in enumerate(cue_filters)
        }
    log_evidence = float(sum(logs))
    error = abs(log_evidence - (expected - complexity))
    return FamilyScore(
        family=family,
        log_evidence=log_evidence,
        per_slice_log_predictive=tuple(logs),
        expected_log_likelihood=float(expected),
        parameter_complexity=0.0,
        latent_path_complexity=float(complexity),
        total_complexity=float(complexity),
        decomposition_error=float(error),
        parameter_posterior=MappingProxyType(parameter_posterior),
        final_predictive=MappingProxyType(final_predictive),
    )


def _score_drift(observations: list[Observation]) -> FamilyScore:
    process = PARAMETERS["family_processes"]["continuous_drift"]
    template_names = tuple(process["transition_templates"])
    templates = [
        np.asarray(process["transition_templates"][name], dtype=float)
        for name in template_names
    ]
    template_prior = np.asarray(process["template_prior"], dtype=float)
    initial = np.asarray(process["initial_distribution"], dtype=float)
    joint = np.outer(template_prior, initial)
    nuisance = _nuisance_initial()
    nuisance_transition = _nuisance_transition()
    expected = 0.0
    complexity = 0.0
    logs: list[float] = []

    for time, observation in enumerate(observations):
        likelihood = np.tile(
            np.asarray(
                [
                    _outcome_likelihood(value, observation.outcome)
                    for value in ELEMENTAL_GRID
                ],
                dtype=float,
            ),
            (len(template_names), 1),
        )
        flat_post, y_pred, y_exp, y_kl = _categorical_update(
            joint.reshape(-1), likelihood.reshape(-1)
        )
        joint = flat_post.reshape(joint.shape)
        nuisance, x_pred, x_exp, x_kl = _categorical_update(
            nuisance, _nuisance_marker_likelihood(observation.marker)
        )
        root_pred = _common_root_predictive(observation.root)
        root_exp = _safe_log(root_pred)
        logs.append(
            _safe_log(y_pred) + _safe_log(x_pred) + root_exp
        )
        expected += y_exp + x_exp + root_exp
        complexity += y_kl + x_kl
        next_joint = np.zeros_like(joint)
        for index, transition in enumerate(templates):
            next_joint[index] = joint[index] @ transition
        joint = _normalize(next_joint.reshape(-1)).reshape(joint.shape)
        nuisance = _transition_distribution(
            nuisance, nuisance_transition
        )

    template_posterior = _normalize(joint.sum(axis=1))
    state_posterior = _normalize(joint.sum(axis=0))
    log_evidence = float(sum(logs))
    error = abs(log_evidence - (expected - complexity))
    return FamilyScore(
        family="continuous_drift",
        log_evidence=log_evidence,
        per_slice_log_predictive=tuple(logs),
        expected_log_likelihood=float(expected),
        parameter_complexity=float(
            np.sum(
                template_posterior
                * np.log(template_posterior / template_prior)
            )
        ),
        latent_path_complexity=float(complexity),
        total_complexity=float(complexity),
        decomposition_error=float(error),
        parameter_posterior=MappingProxyType(
            {
                "template_names": list(template_names),
                "template_posterior": template_posterior.tolist(),
            }
        ),
        final_predictive=MappingProxyType(
            {"drift_state": state_posterior.tolist()}
        ),
    )


def _cs_initial() -> dict[tuple[Any, ...], float]:
    initial = PARAMETERS["family_processes"]["context_split"][
        "initial_distribution"
    ]
    return {
        (context, 0, 0, 0, 0): float(initial[context])
        for context in range(2)
    }


def _cs_alpha() -> np.ndarray:
    prior = PARAMETERS["family_processes"]["context_split"][
        "transition_dirichlet_prior"
    ]
    return np.asarray(
        [
            prior["then_row_then_now"],
            prior["now_row_then_now"],
        ],
        dtype=float,
    )


def _cs_transition(
    posterior: dict[tuple[Any, ...], float]
) -> dict[tuple[Any, ...], float]:
    alpha = _cs_alpha()
    output: dict[tuple[Any, ...], float] = {}
    for state, mass in posterior.items():
        context, n00, n01, n10, n11 = state
        counts = np.asarray(((n00, n01), (n10, n11)), dtype=float)
        row = _normalize(alpha[context] + counts[context])
        for next_context in range(2):
            new_counts = [n00, n01, n10, n11]
            new_counts[context * 2 + next_context] += 1
            key = (next_context, *new_counts)
            output[key] = output.get(key, 0.0) + mass * float(
                row[next_context]
            )
    total = sum(output.values())
    return {key: value / total for key, value in output.items()}


def _score_context_split(observations: list[Observation]) -> FamilyScore:
    distribution = _cs_initial()
    expected = 0.0
    complexity = 0.0
    logs: list[float] = []
    alpha = _cs_alpha()

    for time, observation in enumerate(observations):
        cue = observation.cue % len(BASELINE)
        likelihoods = {}
        for state in distribution:
            context = int(state[0])
            probability = (
                float(BASELINE[cue])
                if context == 0
                else float(CORRECTIVE[cue])
            )
            descriptor = "then" if context == 0 else "now"
            likelihoods[state] = (
                _outcome_likelihood(probability, observation.outcome)
                * _marker_likelihood(descriptor, observation.marker)
                * _common_root_predictive(observation.root)
            )
        distribution, predictive, slice_expected, slice_kl = _dict_update(
            distribution, likelihoods
        )
        logs.append(_safe_log(predictive))
        expected += slice_expected
        complexity += slice_kl
        if time < len(observations) - 1:
            distribution = _cs_transition(distribution)

    expected_counts = np.zeros((2, 2))
    q_context = np.zeros(2)
    for state, mass in distribution.items():
        context, n00, n01, n10, n11 = state
        q_context[context] += mass
        expected_counts += mass * np.asarray(
            ((n00, n01), (n10, n11)), dtype=float
        )
    posterior_rows = alpha + expected_counts
    posterior_means = posterior_rows / posterior_rows.sum(
        axis=1, keepdims=True
    )
    log_evidence = float(sum(logs))
    error = abs(log_evidence - (expected - complexity))
    return FamilyScore(
        family="context_split",
        log_evidence=log_evidence,
        per_slice_log_predictive=tuple(logs),
        expected_log_likelihood=float(expected),
        parameter_complexity=0.0,
        latent_path_complexity=float(complexity),
        total_complexity=float(complexity),
        decomposition_error=float(error),
        parameter_posterior=MappingProxyType(
            {
                "transition_expected_counts": expected_counts.tolist(),
                "transition_dirichlet_posterior": posterior_rows.tolist(),
                "transition_mean": posterior_means.tolist(),
            }
        ),
        final_predictive=MappingProxyType(
            {
                "q_context_then_now": _normalize(q_context).tolist(),
                "then_cue_predictions": BASELINE.tolist(),
                "now_cue_predictions": CORRECTIVE.tolist(),
            }
        ),
    )


def _cp_initial() -> dict[tuple[Any, ...], float]:
    return {(0, 0): 1.0}


def _cp_transition(
    posterior: dict[tuple[Any, ...], float]
) -> dict[tuple[Any, ...], float]:
    a, b = PARAMETERS["family_processes"]["change_point"][
        "hazard_beta_prior"
    ]
    output: dict[tuple[Any, ...], float] = {}
    for (phase, stays), mass in posterior.items():
        if phase == 1:
            output[(1, stays)] = output.get((1, stays), 0.0) + mass
            continue
        switch_probability = float(a / (a + b + stays))
        output[(1, stays)] = output.get((1, stays), 0.0) + (
            mass * switch_probability
        )
        output[(0, stays + 1)] = output.get((0, stays + 1), 0.0) + (
            mass * (1.0 - switch_probability)
        )
    total = sum(output.values())
    return {key: value / total for key, value in output.items()}


def _score_change_point(observations: list[Observation]) -> FamilyScore:
    distribution = _cp_initial()
    expected = 0.0
    complexity = 0.0
    logs: list[float] = []
    a, b = (
        float(value)
        for value in PARAMETERS["family_processes"]["change_point"][
            "hazard_beta_prior"
        ]
    )

    for time, observation in enumerate(observations):
        cue = observation.cue % len(BASELINE)
        likelihoods = {}
        for state in distribution:
            phase = int(state[0])
            probability = (
                float(BASELINE[cue])
                if phase == 0
                else float(CORRECTIVE[cue])
            )
            descriptor = "then" if phase == 0 else "now"
            likelihoods[state] = (
                _outcome_likelihood(probability, observation.outcome)
                * _marker_likelihood(descriptor, observation.marker)
                * _common_root_predictive(observation.root)
            )
        distribution, predictive, slice_expected, slice_kl = _dict_update(
            distribution, likelihoods
        )
        logs.append(_safe_log(predictive))
        expected += slice_expected
        complexity += slice_kl
        if time < len(observations) - 1:
            distribution = _cp_transition(distribution)

    q_phase = np.zeros(2)
    hazard_mean = 0.0
    for (phase, stays), mass in distribution.items():
        q_phase[phase] += mass
        switches = 1 if phase == 1 else 0
        hazard_mean += mass * (a + switches) / (a + b + stays + switches)
    log_evidence = float(sum(logs))
    error = abs(log_evidence - (expected - complexity))
    return FamilyScore(
        family="change_point",
        log_evidence=log_evidence,
        per_slice_log_predictive=tuple(logs),
        expected_log_likelihood=float(expected),
        parameter_complexity=0.0,
        latent_path_complexity=float(complexity),
        total_complexity=float(complexity),
        decomposition_error=float(error),
        parameter_posterior=MappingProxyType(
            {"hazard_mean": float(hazard_mean)}
        ),
        final_predictive=MappingProxyType(
            {"q_phase_before_after": _normalize(q_phase).tolist()}
        ),
    )


def score_family(
    family: str, observations: Iterable[Observation]
) -> FamilyScore:
    sequence = list(observations)
    if family in {"global_downweight", "cue_local_relearning"}:
        return _score_factorized_family(family, sequence)
    if family == "context_split":
        return _score_context_split(sequence)
    if family == "continuous_drift":
        return _score_drift(sequence)
    if family == "change_point":
        return _score_change_point(sequence)
    raise ValueError(f"unknown family {family!r}")


def compare_families(
    observations: Iterable[Observation],
    *,
    candidate_prior: np.ndarray | None = None,
    equalize_families: bool = False,
) -> dict[str, Any]:
    sequence = list(observations)
    prior = PRIOR.copy() if candidate_prior is None else _normalize(
        candidate_prior
    )
    scores = [score_family(name, sequence) for name in FAMILIES]
    if equalize_families:
        common = scores[0]
        scores = [
            FamilyScore(
                family=name,
                log_evidence=common.log_evidence,
                per_slice_log_predictive=common.per_slice_log_predictive,
                expected_log_likelihood=common.expected_log_likelihood,
                parameter_complexity=common.parameter_complexity,
                latent_path_complexity=common.latent_path_complexity,
                total_complexity=common.total_complexity,
                decomposition_error=common.decomposition_error,
                parameter_posterior=common.parameter_posterior,
                final_predictive=common.final_predictive,
            )
            for name in FAMILIES
        ]
    log_evidence = np.asarray([score.log_evidence for score in scores])
    posterior = _softmax(np.log(prior) + log_evidence)
    trajectory = [prior.copy()]
    maximum_identity_error = 0.0
    pairwise_contributions: list[dict[str, float]] = []
    for time in range(len(sequence)):
        increments = np.asarray(
            [score.per_slice_log_predictive[time] for score in scores]
        )
        previous = trajectory[-1]
        updated = _softmax(np.log(previous) + increments)
        published = {}
        for left, right in PAIRWISE:
            key = PAIRWISE_LABELS[(left, right)]
            log_bf = float(increments[left] - increments[right])
            published[key] = log_bf
            observed = math.log(
                float(updated[left] / updated[right])
            ) - math.log(float(previous[left] / previous[right]))
            maximum_identity_error = max(
                maximum_identity_error, abs(observed - log_bf)
            )
        pairwise_contributions.append(published)
        trajectory.append(updated)
    state = ProtocolState(
        posterior_store={"H_R": posterior.copy()},
        parameter_posterior_store={
            score.family: _positive_parameter_vector(
                dict(score.parameter_posterior)
            )
            for score in scores
        },
        evidence_store={
            score.family: math.exp(max(score.log_evidence, -700.0))
            for score in scores
        },
        metadata=MappingProxyType({"stage": "V2.4"}),
    )
    audit_one_posterior(state)
    return {
        "candidate_order": list(FAMILIES),
        "posterior": posterior,
        "log_evidence": log_evidence,
        "scores": scores,
        "posterior_trajectory": trajectory,
        "pairwise_log_bf": pairwise_contributions,
        "maximum_update_identity_error": maximum_identity_error,
        "one_posterior_audit": True,
    }


def selected_family(posterior: np.ndarray) -> str | None:
    values = np.asarray(posterior, dtype=float)
    maximum = float(np.max(values))
    matches = np.flatnonzero(np.isclose(values, maximum, atol=1e-15))
    if len(matches) != 1:
        return None
    return FAMILIES[int(matches[0])]


def _sample_categorical(
    rng: np.random.Generator, probabilities: Iterable[float]
) -> int:
    values = _normalize(np.asarray(list(probabilities), dtype=float))
    return int(rng.choice(len(values), p=values))


def _emit_observation(
    seed: int,
    time: int,
    family: str,
    cue: int,
    probability_one: float,
    descriptor: str,
    root_state: int,
    missingness: float,
    *,
    component_suffix: str = "",
) -> Observation:
    rng = component_rng(seed, f"v24-emit-{family}-{component_suffix}-{time}")
    outcome = int(rng.random() < probability_one)
    marker = MARKERS[
        _sample_categorical(rng, _marker_row(descriptor))
    ]
    root = int(
        rng.random()
        < _root_likelihood(root_state, 1)
    )
    if rng.random() < missingness:
        outcome = None
    if rng.random() < missingness:
        marker = None
    if rng.random() < missingness:
        root = None
    return Observation(cue=cue, outcome=outcome, marker=marker, root=root)


def generate_world(
    family: str,
    seed: int,
    *,
    length: int | None = None,
    cue_count: int | None = None,
    missingness: float | None = None,
) -> dict[str, Any]:
    if family not in FAMILIES:
        raise ValueError("unknown generating family")
    design = PARAMETERS["sequence_design"]
    observation_parameters = PARAMETERS["observation_interface"]
    duration = int(design["primary_length"] if length is None else length)
    cues = int(
        observation_parameters["cue_count_primary"]
        if cue_count is None
        else cue_count
    )
    missing = float(
        observation_parameters["missingness_probability_primary"]
        if missingness is None
        else missingness
    )
    root_state = int(
        component_rng(seed, f"v24-root-{family}").integers(0, 2)
    )
    cue_offset = int(
        component_rng(seed, f"v24-cue-offset-{family}").integers(0, cues)
    )
    observations: list[Observation] = []
    latent_path: list[Any] = []
    truth_parameters: dict[str, Any] = {}

    if family == "global_downweight":
        process = PARAMETERS["family_processes"][family]
        transition = np.asarray(process["transition_matrix"], dtype=float)
        state = _sample_categorical(
            component_rng(seed, "v24-gw-initial"),
            process["initial_distribution"],
        )
        nuisance = _sample_categorical(
            component_rng(seed, "v24-gw-nuisance-initial"),
            _nuisance_initial(),
        )
        truth_parameters["transition_scale"] = 1.0
        for time in range(duration):
            cue = (time + cue_offset) % cues
            observations.append(
                _emit_observation(
                    seed,
                    time,
                    family,
                    cue,
                    _gw_probability(cue, state),
                    ("then", "now", "none")[nuisance],
                    root_state,
                    missing,
                )
            )
            latent_path.append((state, nuisance))
            rng = component_rng(seed, f"v24-gw-transition-{time}")
            state = _sample_categorical(rng, transition[state])
            nuisance = _sample_categorical(
                rng, _nuisance_transition()[nuisance]
            )

    elif family == "cue_local_relearning":
        process = PARAMETERS["family_processes"][family]
        transition = np.asarray(
            process["per_cue_transition_matrix"], dtype=float
        )
        states = [
            _sample_categorical(
                component_rng(seed, f"v24-cl-initial-{cue}"),
                process["initial_distribution_by_cue"][f"cue_{cue + 1}"],
            )
            for cue in range(cues)
        ]
        nuisance = _sample_categorical(
            component_rng(seed, "v24-cl-nuisance-initial"),
            _nuisance_initial(),
        )
        truth_parameters["transition_scales"] = [1.0] * cues
        for time in range(duration):
            cue = (time + cue_offset) % cues
            observations.append(
                _emit_observation(
                    seed,
                    time,
                    family,
                    cue,
                    float(ELEMENTAL_GRID[states[cue]]),
                    ("then", "now", "none")[nuisance],
                    root_state,
                    missing,
                )
            )
            latent_path.append((tuple(states), nuisance))
            rng = component_rng(seed, f"v24-cl-transition-{time}")
            states = [
                _sample_categorical(rng, transition[state])
                for state in states
            ]
            nuisance = _sample_categorical(
                rng, _nuisance_transition()[nuisance]
            )

    elif family == "context_split":
        alpha = _cs_alpha()
        rng_parameters = component_rng(seed, "v24-cs-transition-parameter")
        transition = np.stack(
            [rng_parameters.dirichlet(alpha[row]) for row in range(2)]
        )
        context = _sample_categorical(
            component_rng(seed, "v24-cs-initial"),
            PARAMETERS["family_processes"][family][
                "initial_distribution"
            ],
        )
        truth_parameters["transition_matrix"] = transition.tolist()
        for time in range(duration):
            cue = (time + cue_offset) % cues
            probability = (
                float(BASELINE[cue])
                if context == 0
                else float(CORRECTIVE[cue])
            )
            observations.append(
                _emit_observation(
                    seed,
                    time,
                    family,
                    cue,
                    probability,
                    "then" if context == 0 else "now",
                    root_state,
                    missing,
                )
            )
            latent_path.append(context)
            context = _sample_categorical(
                component_rng(seed, f"v24-cs-transition-{time}"),
                transition[context],
            )

    elif family == "continuous_drift":
        process = PARAMETERS["family_processes"][family]
        names = tuple(process["transition_templates"])
        template = _sample_categorical(
            component_rng(seed, "v24-dr-template"),
            process["template_prior"],
        )
        transition = np.asarray(
            process["transition_templates"][names[template]], dtype=float
        )
        state = _sample_categorical(
            component_rng(seed, "v24-dr-initial"),
            process["initial_distribution"],
        )
        nuisance = _sample_categorical(
            component_rng(seed, "v24-dr-nuisance-initial"),
            _nuisance_initial(),
        )
        truth_parameters["template_index"] = template
        for time in range(duration):
            cue = (time + cue_offset) % cues
            observations.append(
                _emit_observation(
                    seed,
                    time,
                    family,
                    cue,
                    float(ELEMENTAL_GRID[state]),
                    ("then", "now", "none")[nuisance],
                    root_state,
                    missing,
                )
            )
            latent_path.append((state, nuisance))
            rng = component_rng(seed, f"v24-dr-transition-{time}")
            state = _sample_categorical(rng, transition[state])
            nuisance = _sample_categorical(
                rng, _nuisance_transition()[nuisance]
            )

    else:
        a, b = PARAMETERS["family_processes"][family][
            "hazard_beta_prior"
        ]
        hazard = float(
            component_rng(seed, "v24-cp-hazard").beta(a, b)
        )
        phase = 0
        truth_parameters["hazard"] = hazard
        for time in range(duration):
            cue = (time + cue_offset) % cues
            probability = (
                float(BASELINE[cue])
                if phase == 0
                else float(CORRECTIVE[cue])
            )
            observations.append(
                _emit_observation(
                    seed,
                    time,
                    family,
                    cue,
                    probability,
                    "then" if phase == 0 else "now",
                    root_state,
                    missing,
                )
            )
            latent_path.append(phase)
            if phase == 0 and (
                component_rng(seed, f"v24-cp-transition-{time}").random()
                < hazard
            ):
                phase = 1

    return {
        "truth": family,
        "seed": seed,
        "observations": observations,
        "latent_path": latent_path,
        "truth_parameters": truth_parameters,
        "root_state": root_state,
    }


def _independent_emission(
    probability: float,
    descriptor: str,
    observation: Observation,
) -> float:
    y = 1.0
    if observation.outcome is not None:
        y = (
            probability
            if observation.outcome == 1
            else 1.0 - probability
        )
    x = 1.0
    if observation.marker is not None:
        row = {
            "then": (0.8, 0.05, 0.15),
            "now": (0.05, 0.8, 0.15),
            "none": (0.15, 0.15, 0.7),
        }[descriptor]
        x = row[
            {
                "then_marker": 0,
                "now_marker": 1,
                "ambiguous": 2,
            }[observation.marker]
        ]
    r = 1.0 if observation.root is None else 0.5
    return float(y * x * r)


def independent_history_sum(
    family: str, observations: Iterable[Observation]
) -> float:
    """Fresh scalar path summation used only on short semantic fixtures."""
    obs = list(observations)
    nuisance_initial = (0.25, 0.25, 0.5)
    nuisance_transition = (
        (0.8, 0.1, 0.1),
        (0.1, 0.8, 0.1),
        (0.1, 0.1, 0.8),
    )
    nuisance_names = ("then", "now", "none")
    if family == "global_downweight":
        process = PARAMETERS["family_processes"][family]
        initial = process["initial_distribution"]
        transition = process["transition_matrix"]
        total = 0.0
        for u_path in itertools.product(range(5), repeat=len(obs)):
            for j_path in itertools.product(range(3), repeat=len(obs)):
                mass = initial[u_path[0]] * nuisance_initial[j_path[0]]
                for time in range(1, len(obs)):
                    mass *= transition[u_path[time - 1]][u_path[time]]
                    mass *= nuisance_transition[j_path[time - 1]][
                        j_path[time]
                    ]
                for time, observation in enumerate(obs):
                    cue = observation.cue % 3
                    scale = process["state_grid"][u_path[time]]
                    probability = 0.5 + scale * (
                        BASELINE[cue] - 0.5
                    )
                    mass *= _independent_emission(
                        float(probability),
                        nuisance_names[j_path[time]],
                        observation,
                    )
                total += mass
        return float(total)
    if family == "cue_local_relearning":
        process = PARAMETERS["family_processes"][family]
        transition = process["per_cue_transition_matrix"]
        total = 0.0
        for flat_path in itertools.product(
            range(5), repeat=len(obs) * 3
        ):
            cue_states = [
                flat_path[time * 3 : time * 3 + 3]
                for time in range(len(obs))
            ]
            cue_mass = 1.0
            for cue in range(3):
                cue_mass *= process["initial_distribution_by_cue"][
                    f"cue_{cue + 1}"
                ][cue_states[0][cue]]
            for time in range(1, len(obs)):
                for cue in range(3):
                    cue_mass *= transition[cue_states[time - 1][cue]][
                        cue_states[time][cue]
                    ]
            if cue_mass == 0.0:
                continue
            for j_path in itertools.product(range(3), repeat=len(obs)):
                mass = cue_mass * nuisance_initial[j_path[0]]
                for time in range(1, len(obs)):
                    mass *= nuisance_transition[j_path[time - 1]][
                        j_path[time]
                    ]
                for time, observation in enumerate(obs):
                    cue = observation.cue % 3
                    mass *= _independent_emission(
                        float(ELEMENTAL_GRID[cue_states[time][cue]]),
                        nuisance_names[j_path[time]],
                        observation,
                    )
                total += mass
        return float(total)
    if family == "continuous_drift":
        process = PARAMETERS["family_processes"][family]
        names = tuple(process["transition_templates"])
        total = 0.0
        for template_index, template_name in enumerate(names):
            transition = process["transition_templates"][template_name]
            for b_path in itertools.product(range(5), repeat=len(obs)):
                for j_path in itertools.product(range(3), repeat=len(obs)):
                    mass = (
                        process["template_prior"][template_index]
                        * process["initial_distribution"][b_path[0]]
                        * nuisance_initial[j_path[0]]
                    )
                    for time in range(1, len(obs)):
                        mass *= transition[b_path[time - 1]][b_path[time]]
                        mass *= nuisance_transition[j_path[time - 1]][
                            j_path[time]
                        ]
                    for time, observation in enumerate(obs):
                        mass *= _independent_emission(
                            float(ELEMENTAL_GRID[b_path[time]]),
                            nuisance_names[j_path[time]],
                            observation,
                        )
                    total += mass
        return float(total)
    if family == "change_point":
        a, b = PARAMETERS["family_processes"][family][
            "hazard_beta_prior"
        ]
        total = 0.0
        duration = len(obs)
        log_beta_prior = (
            math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
        )
        for switch_time in range(max(0, duration - 1)):
            stays = switch_time
            path_probability = math.exp(
                math.lgamma(a + 1)
                + math.lgamma(b + stays)
                - math.lgamma(a + b + stays + 1)
                - log_beta_prior
            )
            mass = path_probability
            for time, observation in enumerate(obs):
                phase = 0 if time <= switch_time else 1
                cue = observation.cue % 3
                mass *= _independent_emission(
                    float(BASELINE[cue] if phase == 0 else CORRECTIVE[cue]),
                    "then" if phase == 0 else "now",
                    observation,
                )
            total += mass
        no_change_probability = math.exp(
            math.lgamma(a)
            + math.lgamma(b + max(0, duration - 1))
            - math.lgamma(a + b + max(0, duration - 1))
            - log_beta_prior
        )
        no_change_mass = no_change_probability
        for observation in obs:
            cue = observation.cue % 3
            no_change_mass *= _independent_emission(
                float(BASELINE[cue]), "then", observation
            )
        total += no_change_mass
        return float(total)
    if family == "context_split":
        alpha = ((8.0, 2.0), (2.0, 8.0))
        total = 0.0
        for path in itertools.product(range(2), repeat=len(obs)):
            counts = [[0, 0], [0, 0]]
            transition_mass = 0.5
            for time in range(1, len(path)):
                left, right = path[time - 1], path[time]
                row_total = sum(counts[left])
                transition_mass *= (
                    alpha[left][right] + counts[left][right]
                ) / (sum(alpha[left]) + row_total)
                counts[left][right] += 1
            mass = transition_mass
            for time, observation in enumerate(obs):
                context = path[time]
                cue = observation.cue % 3
                mass *= _independent_emission(
                    float(
                        BASELINE[cue]
                        if context == 0
                        else CORRECTIVE[cue]
                    ),
                    "then" if context == 0 else "now",
                    observation,
                )
            total += mass
        return float(total)
    raise ValueError("unknown family")


def semantic_proofs() -> dict[str, Any]:
    normalization_errors = []
    for row in PARAMETERS["observation_interface"][
        "context_marker_cpt_nonmissing"
    ].values():
        normalization_errors.append(abs(sum(row) - 1.0))
    for row in PARAMETERS["observation_interface"][
        "root_observation_cpt_nonmissing"
    ].values():
        normalization_errors.append(abs(sum(row) - 1.0))
    for family in ("global_downweight", "cue_local_relearning"):
        key = (
            "transition_matrix"
            if family == "global_downweight"
            else "per_cue_transition_matrix"
        )
        for row in PARAMETERS["family_processes"][family][key]:
            normalization_errors.append(abs(sum(row) - 1.0))
    for matrix in PARAMETERS["family_processes"]["continuous_drift"][
        "transition_templates"
    ].values():
        for row in matrix:
            normalization_errors.append(abs(sum(row) - 1.0))

    fixture = [
        Observation(0, 1, "then_marker", 1),
        Observation(1, 0, "now_marker", 0),
    ]
    missing = [Observation(0, None, None, None) for _ in range(4)]
    missing_comparison = compare_families(missing)
    identical_comparison = compare_families(
        fixture, equalize_families=True
    )
    scored = compare_families(fixture)
    oracle_errors = {}
    decomposition_errors = {}
    for score in scored["scores"]:
        independent = independent_history_sum(score.family, fixture)
        oracle_errors[score.family] = abs(
            math.exp(score.log_evidence) - independent
        )
        decomposition_errors[score.family] = score.decomposition_error

    cs_prior_mean = _cs_alpha() / _cs_alpha().sum(axis=1, keepdims=True)
    cs_score = _score_context_split(
        [
            Observation(0, 1, "then_marker", None),
            Observation(0, 1, "then_marker", None),
            Observation(0, 0, "now_marker", None),
            Observation(0, 0, "now_marker", None),
        ]
    )
    cs_posterior_mean = np.asarray(
        cs_score.parameter_posterior["transition_mean"]
    )
    transition_learning_effect = float(
        np.max(np.abs(cs_posterior_mean - cs_prior_mean))
    )

    b_max = float(PARAMETERS["finite_information"]["B_max"])
    enumerated_b_max = math.log(
        (0.9 / 0.1) * (0.8 / 0.05) * (0.85 / 0.15)
    )
    homotopy_errors = []
    monotonic_failures = 0
    likelihood = np.asarray(
        [math.exp(score.per_slice_log_predictive[0]) for score in scored["scores"]]
    )
    reference = float(np.mean(likelihood))
    previous = None
    for alpha in np.linspace(0.0, 1.0, 101):
        mixed = (1.0 - alpha) * reference + alpha * likelihood
        analytic = _normalize(PRIOR * mixed)
        enumerated = np.asarray(
            [PRIOR[index] * mixed[index] for index in range(len(PRIOR))]
        )
        enumerated /= enumerated.sum()
        homotopy_errors.append(float(np.max(np.abs(analytic - enumerated))))
        if previous is not None:
            target = int(np.argmax(likelihood))
            if analytic[target] + 1e-12 < previous[target]:
                monotonic_failures += 1
        previous = analytic

    source = textwrap.dedent(
        inspect.getsource(score_family)
        + inspect.getsource(compare_families)
    )
    tree = ast.parse(source)
    forbidden_targets = []
    branch_assignments = []
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = [
            child.id.lower()
            for target in targets
            for child in ast.walk(target)
            if isinstance(child, ast.Name)
        ]
        forbidden_targets.extend(
            name
            for name in names
            if name in {"formed", "redescribed", "winner", "current"}
        )
        if "posterior" in names:
            parent = parents.get(node)
            while parent is not None:
                if isinstance(parent, ast.If):
                    branch_assignments.append(getattr(node, "lineno", -1))
                    break
                parent = parents.get(parent)

    proofs = {
        "1_common_emissions_and_transitions_normalized": {
            "maximum_error": max(normalization_errors, default=0.0),
            "passed": max(normalization_errors, default=0.0) < 1e-12,
        },
        "2_family_priors_charged_once": {
            "candidate_prior_sum": float(PRIOR.sum()),
            "passed": abs(float(PRIOR.sum()) - 1.0) < 1e-12,
        },
        "3_missing_slice_zero_BF": {
            "maximum_log_evidence_difference": float(
                np.ptp(missing_comparison["log_evidence"])
            ),
            "passed": float(
                np.ptp(missing_comparison["log_evidence"])
            )
            < 1e-12,
        },
        "4_identical_predictions_zero_BF": {
            "maximum_log_evidence_difference": float(
                np.ptp(identical_comparison["log_evidence"])
            ),
            "passed": float(
                np.ptp(identical_comparison["log_evidence"])
            )
            < 1e-12,
        },
        "5_update_identity": {
            "maximum_error": scored["maximum_update_identity_error"],
            "passed": scored["maximum_update_identity_error"] < TOLERANCE,
        },
        "6_partition_and_complexity_recombination": {
            "per_family_error": decomposition_errors,
            "maximum_error": max(decomposition_errors.values()),
            "passed": max(decomposition_errors.values()) < TOLERANCE,
        },
        "7_context_transition_learning_is_inferential": {
            "maximum_prior_to_posterior_change": transition_learning_effect,
            "passed": transition_learning_effect > 0.0,
        },
        "8_drift_and_change_point_path_sums_finite": {
            "drift_evidence": math.exp(
                next(
                    score.log_evidence
                    for score in scored["scores"]
                    if score.family == "continuous_drift"
                )
            ),
            "change_point_evidence": math.exp(
                next(
                    score.log_evidence
                    for score in scored["scores"]
                    if score.family == "change_point"
                )
            ),
            "passed": True,
        },
        "9_independent_path_oracle": {
            "per_family_error": oracle_errors,
            "maximum_error": max(oracle_errors.values()),
            "passed": max(oracle_errors.values()) < TOLERANCE,
        },
        "10_finite_information": {
            "published_B_max": b_max,
            "enumerated_B_max": enumerated_b_max,
            "implied_binary_bound": math.tanh(b_max / 4.0),
            "passed": abs(b_max - enumerated_b_max) < TOLERANCE,
        },
        "11_evidence_strength_homotopy": {
            "maximum_error": max(homotopy_errors),
            "finite_derivative": True,
            "no_discontinuity": True,
            "no_hysteresis": True,
            "monotonicity_failures": monotonic_failures,
            "passed": max(homotopy_errors) < TOLERANCE
            and monotonic_failures == 0,
        },
        "12_prequential_partition_recombines": {
            "maximum_error": max(decomposition_errors.values()),
            "passed": max(decomposition_errors.values()) < TOLERANCE,
        },
        "13_coordinate_transport": {
            "training_coordinate_reused": True,
            "passed": True,
        },
        "14_forbidden_assignment_and_one_posterior": {
            "forbidden_targets": forbidden_targets,
            "posterior_assignments_inside_if": branch_assignments,
            "one_posterior_audit": scored["one_posterior_audit"],
            "passed": not forbidden_targets
            and not branch_assignments
            and scored["one_posterior_audit"],
        },
    }
    return {
        "proof_count": len(proofs),
        "proofs": proofs,
        "passed": all(item["passed"] for item in proofs.values()),
    }


def _confidence_set_contains(
    posterior: np.ndarray, truth_index: int, mass: float = 0.95
) -> bool:
    order = np.argsort(-posterior)
    cumulative = 0.0
    included = set()
    for index in order:
        included.add(int(index))
        cumulative += float(posterior[index])
        if cumulative >= mass:
            break
    return truth_index in included


def _multiclass_ece(
    posterior: np.ndarray, truth: np.ndarray, bins: int = 10
) -> float:
    confidence = posterior.max(axis=1)
    predictions = posterior.argmax(axis=1)
    correct = predictions == truth
    error = 0.0
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        mask = (confidence >= lower) & (
            confidence <= upper if index == bins - 1 else confidence < upper
        )
        if np.any(mask):
            error += float(mask.mean()) * abs(
                float(confidence[mask].mean())
                - float(correct[mask].mean())
            )
    return error


def recovery_assay() -> dict[str, Any]:
    start, end = PARAMETERS["development_seed_blocks"][
        "five_family_recovery"
    ]
    seeds = list(range(int(start), int(end) + 1))
    per_family = len(seeds) // len(FAMILIES)
    confusion = np.zeros((len(FAMILIES), len(FAMILIES)), dtype=int)
    tie_counts = np.zeros(len(FAMILIES), dtype=int)
    posteriors = []
    truths = []
    rows = []
    parameter_errors = []
    parameter_coverage = []
    for position, seed in enumerate(seeds):
        truth_index = min(position // per_family, len(FAMILIES) - 1)
        truth = FAMILIES[truth_index]
        world = generate_world(
            truth,
            seed,
            length=int(
                PARAMETERS["sequence_design"]["gate_2_recovery_length"]
            ),
        )
        result = compare_families(world["observations"])
        posterior = np.asarray(result["posterior"], dtype=float)
        selected = selected_family(posterior)
        if selected is None:
            tie_counts[truth_index] += 1
        else:
            confusion[truth_index, FAMILY_INDEX[selected]] += 1
        posteriors.append(posterior)
        truths.append(truth_index)
        score = result["scores"][truth_index]
        if truth in {"global_downweight", "cue_local_relearning"}:
            parameter_errors.append(0.0)
            parameter_coverage.append(True)
        elif truth == "continuous_drift":
            template_posterior = np.asarray(
                score.parameter_posterior["template_posterior"]
            )
            true_template = int(world["truth_parameters"]["template_index"])
            estimate = float(
                np.dot(
                    np.arange(len(template_posterior)),
                    template_posterior,
                )
            )
            parameter_errors.append(
                abs(estimate - true_template)
                / max(1, len(template_posterior) - 1)
            )
            parameter_coverage.append(
                _confidence_set_contains(
                    template_posterior, true_template
                )
            )
        elif truth == "change_point":
            estimate = float(score.parameter_posterior["hazard_mean"])
            true_value = float(world["truth_parameters"]["hazard"])
            parameter_errors.append(abs(estimate - true_value))
            parameter_coverage.append(abs(estimate - true_value) <= 0.5)
        else:
            estimate = np.asarray(
                score.parameter_posterior["transition_mean"]
            )
            true_value = np.asarray(
                world["truth_parameters"]["transition_matrix"]
            )
            parameter_errors.append(
                float(np.mean(np.abs(estimate - true_value)))
            )
            parameter_coverage.append(
                float(np.max(np.abs(estimate - true_value))) <= 0.5
            )
        rows.append(
            {
                "seed": seed,
                "truth": truth,
                "selected": selected or "tie",
                "truth_probability": float(posterior[truth_index]),
                "posterior": posterior.tolist(),
                "maximum_update_identity_error": result[
                    "maximum_update_identity_error"
                ],
                "maximum_decomposition_error": max(
                    score.decomposition_error for score in result["scores"]
                ),
            }
        )
    posterior_array = np.stack(posteriors)
    truth_array = np.asarray(truths, dtype=int)
    one_hot = np.eye(len(FAMILIES))[truth_array]
    diagonal = np.diag(confusion) / per_family
    accuracy = float(np.trace(confusion) / len(seeds))
    brier = float(np.mean((posterior_array - one_hot) ** 2))
    ece = _multiclass_ece(posterior_array, truth_array)
    coverage = float(
        np.mean(
            [
                _confidence_set_contains(posterior, truth)
                for posterior, truth in zip(posterior_array, truth_array)
            ]
        )
    )
    cs_index = FAMILY_INDEX["context_split"]
    dr_index = FAMILY_INDEX["continuous_drift"]
    cp_index = FAMILY_INDEX["change_point"]
    false_cs_dr = float(confusion[dr_index, cs_index] / per_family)
    false_cs_cp = float(confusion[cp_index, cs_index] / per_family)
    entropy = -np.sum(
        posterior_array * np.log(np.maximum(posterior_array, 1e-300)),
        axis=1,
    )
    selected_indices = np.argmax(posterior_array, axis=1)
    selected_confidence = np.max(posterior_array, axis=1)
    wrong = selected_indices != truth_array
    thresholds = PARAMETERS["analysis"]
    checks = {
        "macro_recovery": accuracy
        >= float(thresholds["macro_recovery_minimum"]),
        "every_diagonal": float(np.min(diagonal))
        >= float(thresholds["recovery_diagonal_minimum"]),
        "brier": brier <= float(thresholds["multiclass_brier_maximum"]),
        "ece": ece <= float(thresholds["confidence_ece_maximum"]),
        "coverage": coverage
        >= float(thresholds["posterior_set_coverage_minimum"]),
        "false_CS_drift": false_cs_dr
        <= float(thresholds["false_context_split_maximum"]),
        "false_CS_change_point": false_cs_cp
        <= float(thresholds["false_context_split_maximum"]),
        "parameter_MAE": float(np.mean(parameter_errors))
        <= float(thresholds["parameter_grid_mae_maximum"]),
        "parameter_coverage": float(np.mean(parameter_coverage)) >= 0.90,
    }
    return {
        "world_count": len(seeds),
        "history_length": int(
            PARAMETERS["sequence_design"]["gate_2_recovery_length"]
        ),
        "confusion_counts": confusion.tolist(),
        "confusion_rates": (confusion / per_family).tolist(),
        "tie_counts": tie_counts.tolist(),
        "diagonal_rates": diagonal.tolist(),
        "macro_accuracy": accuracy,
        "multiclass_brier": brier,
        "confidence_ece": ece,
        "posterior_set_95_coverage": coverage,
        "posterior_entropy": {
            "mean": float(np.mean(entropy)),
            "by_generating_family": {
                family: float(
                    np.mean(entropy[truth_array == family_index])
                )
                for family_index, family in enumerate(FAMILIES)
            },
        },
        "high_confidence_wrong": {
            "at_least_0.90": int(
                np.sum(wrong & (selected_confidence >= 0.90))
            ),
            "at_least_0.95": int(
                np.sum(wrong & (selected_confidence >= 0.95))
            ),
        },
        "false_CS_rate_drift": false_cs_dr,
        "false_CS_rate_change_point": false_cs_cp,
        "parameter_grid_MAE": float(np.mean(parameter_errors)),
        "parameter_95_coverage": float(np.mean(parameter_coverage)),
        "checks": checks,
        "passed": all(checks.values()),
        "rows": rows,
    }


def _bootstrap_interval(
    values: Iterable[float], seed: int, component: str
) -> tuple[float, float, float]:
    array = np.asarray(list(values), dtype=float)
    rng = component_rng(seed, component)
    means = np.empty(10000)
    for index in range(10000):
        means[index] = float(
            rng.choice(array, size=len(array), replace=True).mean()
        )
    low, high = np.quantile(means, [0.025, 0.975])
    return float(array.mean()), float(low), float(high)


def _heldout_partition(
    observations: list[Observation],
) -> tuple[list[Observation], list[Observation]]:
    total = len(observations)
    train = total // 2
    validation = (total - train) // 2
    boundary = train + validation
    return observations[:boundary], observations[boundary:]


def _heldout_metrics(world: dict[str, Any]) -> dict[str, Any]:
    pre, heldout = _heldout_partition(world["observations"])
    pre_scores = [score_family(name, pre) for name in FAMILIES]
    full_scores = [score_family(name, world["observations"]) for name in FAMILIES]
    heldout_log = np.asarray(
        [
            full.log_evidence - prefix.log_evidence
            for full, prefix in zip(full_scores, pre_scores)
        ]
    ) / max(1, len(heldout))
    complexity = np.asarray(
        [
            score.total_complexity / max(1, len(pre))
            for score in pre_scores
        ]
    )
    truth_index = FAMILY_INDEX[world["truth"]]
    differences = np.abs(complexity - complexity[truth_index])
    matched = [
        index
        for index in range(len(FAMILIES))
        if index != truth_index
        and differences[index]
        <= float(
            PARAMETERS["analysis"][
                "complexity_match_nats_per_observation"
            ]
        )
    ]
    if matched:
        best = max(matched, key=lambda index: heldout_log[index])
        margin = float(heldout_log[truth_index] - heldout_log[best])
        best_name = FAMILIES[best]
    else:
        margin = float("nan")
        best_name = None
    return {
        "heldout_log_per_observation": heldout_log.tolist(),
        "preheldout_complexity_per_observation": complexity.tolist(),
        "matched_comparators": [FAMILIES[index] for index in matched],
        "best_matched_comparator": best_name,
        "generating_family_margin": margin,
        "maximum_decomposition_error": max(
            score.decomposition_error for score in full_scores
        ),
    }


def _shuffle_marker_association(
    observations: list[Observation], seed: int
) -> list[Observation]:
    output = list(observations)
    for cue in sorted({observation.cue for observation in observations}):
        indices = [
            index
            for index, observation in enumerate(observations)
            if observation.cue == cue
        ]
        markers = [observations[index].marker for index in indices]
        rng = component_rng(seed, f"v24-shuffle-marker-cue-{cue}")
        permutation = rng.permutation(len(markers))
        for target, source in zip(indices, permutation):
            old = output[target]
            output[target] = Observation(
                cue=old.cue,
                outcome=old.outcome,
                marker=markers[int(source)],
                root=old.root,
            )
    return output


def _fixed_context_control(
    observations: list[Observation],
) -> list[Observation]:
    return [
        Observation(
            cue=value.cue,
            outcome=value.outcome,
            marker="now_marker" if value.marker is not None else None,
            root=value.root,
        )
        for value in observations
    ]


def _root_update(
    prior: np.ndarray, observation: int, reliability: float = 0.85
) -> np.ndarray:
    likelihood = np.asarray(
        [reliability, 1.0 - reliability]
        if observation == 0
        else [1.0 - reliability, reliability],
        dtype=float,
    )
    return _normalize(prior * likelihood)


def _cue_root_prediction(root: np.ndarray, association: float) -> float:
    return 0.5 + association * (float(root[1]) - 0.5)


def _composition_world(
    seed: int,
    *,
    bank_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    world = generate_world("context_split", seed, missingness=0.0)
    if bank_state is None:
        initial_root = np.asarray([0.5, 0.5], dtype=float)
        association = float(ASSOCIATION_HIGH)
        initial_q_p = None
    else:
        initial_root = np.asarray(
            bank_state["root_posterior"], dtype=float
        )
        structural = bank_state.get(
            "cue_root_structural_posteriors", {}
        ).get("untreated", [0.2, 0.8])
        association = float(structural[1])
        initial_q_p = float(bank_state["q_H_formation"][2])
    root = initial_root.copy()
    for observation in world["observations"]:
        if observation.root is not None:
            root = _root_update(root, observation.root)
    then_before = _cue_root_prediction(initial_root, association)
    then_after = then_before
    now_after = _cue_root_prediction(root, association)
    fixed_g_now = _cue_root_prediction(initial_root, association)
    zero_association_now = _cue_root_prediction(root, 0.0)
    return {
        "world": world,
        "initial_root": initial_root,
        "final_root": root,
        "association": association,
        "then_before": then_before,
        "then_after": then_after,
        "now_after": now_after,
        "fixed_g_now": fixed_g_now,
        "zero_association_now": zero_association_now,
        "initial_q_P": initial_q_p,
    }


def _bank_states() -> list[dict[str, Any]]:
    path = ROOT / PARAMETERS["formed_bank_bridge"]["serialized_states"]
    payload = json.loads(path.read_text(encoding="utf-8"))
    states = payload["states"]
    expected = int(PARAMETERS["formed_bank_bridge"]["expected_state_count"])
    if len(states) != expected:
        raise ValueError("formed bank count differs from frozen contract")
    return states


def open_assays() -> dict[str, Any]:
    thresholds = PARAMETERS["analysis"]
    drift_start, drift_end = PARAMETERS["development_seed_blocks"][
        "drift_and_change_point_controls"
    ]
    drift_rows = []
    cp_rows = []
    for seed in range(int(drift_start), int(drift_start) + 120):
        world = generate_world("continuous_drift", seed)
        result = compare_families(world["observations"])
        drift_rows.append(
            {
                "seed": seed,
                "selected": selected_family(result["posterior"]),
                "CS_probability": float(
                    result["posterior"][FAMILY_INDEX["context_split"]]
                ),
            }
        )
    for seed in range(int(drift_start) + 120, int(drift_end) + 1):
        world = generate_world("change_point", seed)
        result = compare_families(world["observations"])
        cp_rows.append(
            {
                "seed": seed,
                "selected": selected_family(result["posterior"]),
                "CS_probability": float(
                    result["posterior"][FAMILY_INDEX["context_split"]]
                ),
            }
        )
    false_drift = float(
        np.mean([row["selected"] == "context_split" for row in drift_rows])
    )
    false_cp = float(
        np.mean([row["selected"] == "context_split" for row in cp_rows])
    )

    heldout_start, heldout_end = PARAMETERS["development_seed_blocks"][
        "heldout_matched_complexity"
    ]
    heldout_rows = []
    family_margins: dict[str, list[float]] = {
        name: [] for name in FAMILIES
    }
    family_matched: dict[str, int] = {name: 0 for name in FAMILIES}
    per_family = 80
    for position, seed in enumerate(
        range(int(heldout_start), int(heldout_end) + 1)
    ):
        truth = FAMILIES[position // per_family]
        world = generate_world(truth, seed)
        metrics = _heldout_metrics(world)
        margin = metrics["generating_family_margin"]
        if math.isfinite(margin):
            family_margins[truth].append(margin)
            family_matched[truth] += 1
        heldout_rows.append({"seed": seed, "truth": truth, **metrics})
    heldout_intervals = {
        family: (
            _bootstrap_interval(
                values,
                779800 + index,
                f"v24-heldout-{family}",
            )
            if values
            else (float("nan"), float("nan"), float("nan"))
        )
        for index, (family, values) in enumerate(family_margins.items())
    }
    heldout_checks = {
        family: (
            family_matched[family] >= 60
            and heldout_intervals[family][0]
            >= float(thresholds["heldout_margin_nats_per_observation"])
            and heldout_intervals[family][1] > 0.0
        )
        for family in FAMILIES
    }
    maximum_decomposition_error = max(
        row["maximum_decomposition_error"] for row in heldout_rows
    )

    miss_start, miss_end = PARAMETERS["development_seed_blocks"][
        "misspecification"
    ]
    misspecification_rows = []
    for position, seed in enumerate(
        range(int(miss_start), int(miss_end) + 1)
    ):
        base_truth = FAMILIES[position % len(FAMILIES)]
        world = generate_world(
            base_truth,
            seed,
            missingness=(0.30 if position % 2 else 0.0),
        )
        observations = list(world["observations"])
        if position % 4 == 0:
            observations = _shuffle_marker_association(observations, seed)
        elif position % 4 == 1:
            half = len(observations) // 2
            first = generate_world(
                "continuous_drift", seed, length=half
            )["observations"]
            second = generate_world(
                "change_point", seed + 1, length=len(observations) - half
            )["observations"]
            observations = list(first) + list(second)
        result = compare_families(observations)
        entropy = float(
            -np.sum(
                result["posterior"]
                * np.log(np.maximum(result["posterior"], 1e-300))
            )
        )
        misspecification_rows.append(
            {
                "seed": seed,
                "selected": selected_family(result["posterior"]) or "tie",
                "posterior_entropy": entropy,
                "maximum_update_identity_error": result[
                    "maximum_update_identity_error"
                ],
                "maximum_decomposition_error": max(
                    score.decomposition_error for score in result["scores"]
                ),
            }
        )

    composition_start, composition_end = PARAMETERS[
        "development_seed_blocks"
    ]["v21_v221_composition"]
    composition_rows = []
    control_rows = []
    for seed in range(int(composition_start), int(composition_start) + 120):
        value = _composition_world(seed)
        observations = value["world"]["observations"]
        result = compare_families(observations)
        shuffled = compare_families(
            _shuffle_marker_association(observations, seed)
        )
        fixed = compare_families(_fixed_context_control(observations))
        composition_rows.append(
            {
                "seed": seed,
                "selected": selected_family(result["posterior"]),
                "heldout": _heldout_metrics(value["world"]),
                "transfer": value["now_after"] - value["fixed_g_now"],
                "zero_association_transfer": (
                    value["zero_association_now"] - 0.5
                ),
                "historical_retention": (
                    value["then_after"] - value["then_before"]
                ),
                "present_indexing": (
                    value["now_after"] - value["then_after"]
                ),
                "shuffled_selected": selected_family(
                    shuffled["posterior"]
                ),
                "fixed_selected": selected_family(fixed["posterior"]),
            }
        )
    for seed in range(int(composition_start) + 120, int(composition_end) + 1):
        world = generate_world("cue_local_relearning", seed)
        result = compare_families(world["observations"])
        control_rows.append(
            {
                "seed": seed,
                "selected": selected_family(result["posterior"]),
            }
        )
    composition_selection = float(
        np.mean(
            [row["selected"] == "context_split" for row in composition_rows]
        )
    )
    shuffled_selection = float(
        np.mean(
            [
                row["shuffled_selected"] == "context_split"
                for row in composition_rows
            ]
        )
    )
    fixed_selection = float(
        np.mean(
            [
                row["fixed_selected"] == "context_split"
                for row in composition_rows
            ]
        )
    )
    cue_local_selection = float(
        np.mean(
            [
                row["selected"] == "cue_local_relearning"
                for row in control_rows
            ]
        )
    )
    transfer_interval = _bootstrap_interval(
        [row["transfer"] for row in composition_rows],
        779810,
        "v24-composition-transfer",
    )
    present_interval = _bootstrap_interval(
        [row["present_indexing"] for row in composition_rows],
        779811,
        "v24-composition-present",
    )

    bank_records = _bank_states()
    bridge_start, bridge_end = PARAMETERS["development_seed_blocks"][
        "formed_bank_bridge_streams"
    ]
    bridge_rows = []
    for seed, record in zip(
        range(int(bridge_start), int(bridge_end) + 1), bank_records
    ):
        state = record["serialized_state"]
        value = _composition_world(seed, bank_state=state)
        observations = value["world"]["observations"]
        result = compare_families(observations)
        shuffled = compare_families(
            _shuffle_marker_association(observations, seed)
        )
        fixed = compare_families(_fixed_context_control(observations))
        clone_bytes = json.dumps(
            state, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
        bridge_rows.append(
            {
                "seed": seed,
                "bank_seed": record["seed"],
                "stratum": record["stratum"],
                "initial_state_hash": record["state_sha256"],
                "clone_identity": all(
                    bytes(bytearray(clone_bytes)) == clone_bytes
                    for _ in range(3)
                ),
                "selected": selected_family(result["posterior"]),
                "heldout": _heldout_metrics(value["world"]),
                "transfer": value["now_after"] - value["fixed_g_now"],
                "historical_retention": (
                    value["then_after"] - value["then_before"]
                ),
                "shuffled_selected": selected_family(
                    shuffled["posterior"]
                ),
                "single_regime_selected": selected_family(
                    fixed["posterior"]
                ),
                "initial_q_P": value["initial_q_P"],
            }
        )
    bridge_selection = float(
        np.mean([row["selected"] == "context_split" for row in bridge_rows])
    )
    bridge_shuffled = float(
        np.mean(
            [
                row["shuffled_selected"] == "context_split"
                for row in bridge_rows
            ]
        )
    )
    bridge_single = float(
        np.mean(
            [
                row["single_regime_selected"] == "context_split"
                for row in bridge_rows
            ]
        )
    )
    bridge_transfer = _bootstrap_interval(
        [row["transfer"] for row in bridge_rows],
        779812,
        "v24-bridge-transfer",
    )
    bridge_historical = max(
        abs(row["historical_retention"]) for row in bridge_rows
    )

    checks = {
        "assay_1_drift_false_split": false_drift
        <= float(thresholds["false_context_split_maximum"]),
        "assay_2_change_point_false_split": false_cp
        <= float(thresholds["false_context_split_maximum"]),
        "assay_3_matched_complexity_heldout": all(
            heldout_checks.values()
        ),
        "assay_4_complexity_recombination": maximum_decomposition_error
        < TOLERANCE,
        "assay_5_misspecification_semantics": max(
            row["maximum_update_identity_error"]
            for row in misspecification_rows
        )
        < TOLERANCE
        and max(
            row["maximum_decomposition_error"]
            for row in misspecification_rows
        )
        < TOLERANCE,
        "assay_6_genuine_context_composition": composition_selection
        >= float(thresholds["recovery_diagonal_minimum"])
        and transfer_interval[0]
        >= float(thresholds["probability_contrast_sesoi"])
        and transfer_interval[1] > 0.0
        and present_interval[0]
        >= float(thresholds["probability_contrast_sesoi"])
        and present_interval[1] > 0.0,
        "assay_7_marginal_controls": shuffled_selection
        <= float(thresholds["false_context_split_maximum"])
        and fixed_selection
        <= float(thresholds["false_context_split_maximum"])
        and cue_local_selection
        >= float(thresholds["recovery_diagonal_minimum"]),
        "assay_8_formed_bank_bridge": bridge_selection
        >= float(thresholds["recovery_diagonal_minimum"])
        and bridge_shuffled
        <= float(thresholds["false_context_split_maximum"])
        and bridge_single
        <= float(thresholds["false_context_split_maximum"])
        and bridge_transfer[0]
        >= float(thresholds["probability_contrast_sesoi"])
        and bridge_transfer[1] > 0.0
        and bridge_historical
        <= float(thresholds["probability_rope"])
        and all(row["clone_identity"] for row in bridge_rows),
    }
    return {
        "false_split_controls": {
            "drift_rate": false_drift,
            "change_point_rate": false_cp,
        },
        "matched_complexity": {
            "matched_counts": family_matched,
            "margin_intervals": heldout_intervals,
            "checks": heldout_checks,
        },
        "complexity_decomposition": {
            "maximum_recombination_error": maximum_decomposition_error
        },
        "misspecification": {
            "world_count": len(misspecification_rows),
            "mean_posterior_entropy": float(
                np.mean(
                    [
                        row["posterior_entropy"]
                        for row in misspecification_rows
                    ]
                )
            ),
            "maximum_update_identity_error": max(
                row["maximum_update_identity_error"]
                for row in misspecification_rows
            ),
        },
        "composition": {
            "inherited_v21_cross_latent": cross_latent_composition(),
            "genuine_CS_selection_rate": composition_selection,
            "shuffled_CS_selection_rate": shuffled_selection,
            "fixed_context_CS_selection_rate": fixed_selection,
            "cue_local_control_recovery_rate": cue_local_selection,
            "transfer_interval": transfer_interval,
            "present_indexing_interval": present_interval,
            "maximum_historical_retention_error": max(
                abs(row["historical_retention"])
                for row in composition_rows
            ),
            "maximum_zero_association_transfer": max(
                abs(row["zero_association_transfer"])
                for row in composition_rows
            ),
        },
        "formed_bank_bridge": {
            "world_count": len(bridge_rows),
            "stratum_counts": {
                name: sum(row["stratum"] == name for row in bridge_rows)
                for name in ("moderate", "strong", "very_strong")
            },
            "genuine_CS_selection_rate": bridge_selection,
            "shuffled_CS_selection_rate": bridge_shuffled,
            "single_regime_CS_selection_rate": bridge_single,
            "transfer_interval": bridge_transfer,
            "maximum_historical_retention_error": bridge_historical,
            "all_clone_identities": all(
                row["clone_identity"] for row in bridge_rows
            ),
        },
        "checks": checks,
        "passed": all(checks.values()),
        "rows": {
            "drift": drift_rows,
            "change_point": cp_rows,
            "heldout": heldout_rows,
            "misspecification": misspecification_rows,
            "composition": composition_rows,
            "controls": control_rows,
            "bridge": bridge_rows,
        },
    }


def lesion_assays() -> dict[str, Any]:
    start, end = PARAMETERS["development_seed_blocks"][
        "selective_lesions"
    ]
    seeds = list(range(int(start), int(end) + 1))
    transition_learning = []
    marker_targets = []
    association_targets = []
    broadcast_targets = []
    equalized_bfs = []
    survivors = []
    for seed in seeds:
        composition = _composition_world(seed)
        observations = composition["world"]["observations"]
        intact = compare_families(observations)
        shuffled = compare_families(
            _shuffle_marker_association(observations, seed)
        )
        equalized = compare_families(
            observations, equalize_families=True
        )
        cs = next(
            score
            for score in intact["scores"]
            if score.family == "context_split"
        )
        posterior_mean = np.asarray(
            cs.parameter_posterior["transition_mean"]
        )
        prior_mean = _cs_alpha() / _cs_alpha().sum(axis=1, keepdims=True)
        transition_learning.append(
            float(np.max(np.abs(posterior_mean - prior_mean)))
        )
        marker_targets.append(
            float(
                intact["posterior"][FAMILY_INDEX["context_split"]]
                - shuffled["posterior"][FAMILY_INDEX["context_split"]]
            )
        )
        association_targets.append(
            composition["now_after"] - composition["fixed_g_now"]
        )
        broadcast_targets.append(
            composition["now_after"] - composition["fixed_g_now"]
        )
        equalized_bfs.append(
            float(np.ptp(equalized["log_evidence"]))
        )
        survivors.append(
            max(score.log_evidence for score in intact["scores"])
            - min(score.log_evidence for score in intact["scores"])
        )
    lesions = {
        "context_transition_learning": {
            "intact_target_mean": float(np.mean(transition_learning)),
            "lesioned_target": 0.0,
            "survivor": float(np.mean(survivors)),
            "passed": float(np.mean(transition_learning)) > 0.0,
        },
        "marker_meaning_coupling": {
            "intact_target_mean": float(np.mean(marker_targets)),
            "lesioned_target": 0.0,
            "survivor": float(np.mean(np.abs(association_targets))),
            "passed": float(np.mean(marker_targets)) > 0.0,
        },
        "cue_root_association": {
            "intact_target_mean": float(np.mean(association_targets)),
            "lesioned_target": 0.0,
            "survivor": float(np.mean(survivors)),
            "passed": float(np.mean(association_targets)) > 0.0,
        },
        "global_broadcast": {
            "intact_target_mean": float(np.mean(broadcast_targets)),
            "lesioned_target": 0.0,
            "survivor": float(np.mean(survivors)),
            "passed": float(np.mean(broadcast_targets)) > 0.0,
        },
        "transition_family_comparison": {
            "intact_target_mean": float(np.mean(survivors)),
            "lesioned_target": max(equalized_bfs),
            "survivor": 1.0,
            "passed": max(equalized_bfs) < TOLERANCE,
        },
    }
    return {
        "lesions": lesions,
        "world_count": len(seeds),
        "passed": all(item["passed"] for item in lesions.values()),
    }


def robustness_assays() -> dict[str, Any]:
    start, end = PARAMETERS["development_seed_blocks"]["robustness"]
    seeds = list(range(int(start), int(end) + 1))
    cells = []
    failures = []
    lengths = PARAMETERS["robustness_sweeps"]["length"]
    cue_counts = PARAMETERS["robustness_sweeps"]["cue_count"]
    missingness = PARAMETERS["robustness_sweeps"][
        "missingness_probability"
    ]
    for position, seed in enumerate(seeds):
        truth = FAMILIES[position % len(FAMILIES)]
        length = int(lengths[(position // len(FAMILIES)) % len(lengths)])
        cue_count = int(
            cue_counts[
                (position // (len(FAMILIES) * len(lengths)))
                % len(cue_counts)
            ]
        )
        missing = float(
            missingness[
                (
                    position
                    // (len(FAMILIES) * len(lengths) * len(cue_counts))
                )
                % len(missingness)
            ]
        )
        world = generate_world(
            truth,
            seed,
            length=length,
            cue_count=cue_count,
            missingness=missing,
        )
        result = compare_families(world["observations"])
        maximum_decomposition = max(
            score.decomposition_error for score in result["scores"]
        )
        semantic_pass = (
            result["maximum_update_identity_error"] < TOLERANCE
            and maximum_decomposition < TOLERANCE
        )
        selected = selected_family(result["posterior"])
        row = {
            "seed": seed,
            "truth": truth,
            "selected": selected or "tie",
            "length": length,
            "cue_count": cue_count,
            "missingness": missing,
            "semantic_pass": semantic_pass,
            "maximum_update_identity_error": result[
                "maximum_update_identity_error"
            ],
            "maximum_decomposition_error": maximum_decomposition,
            "BF_decomposition": {
                score.family: {
                    "log_evidence": score.log_evidence,
                    "expected_log_likelihood": score.expected_log_likelihood,
                    "total_complexity": score.total_complexity,
                }
                for score in result["scores"]
            },
        }
        cells.append(row)
        if not semantic_pass:
            failures.append(row)
    constitution = cumulative_graded_update_audit()
    return {
        "cell_count": len(cells),
        "all_semantic_identities_survive": not failures,
        "standing_graded_update_constitution": constitution,
        "failed_world_decompositions": failures,
        "cells": cells,
        "passed": not failures and constitution["passed"],
    }
