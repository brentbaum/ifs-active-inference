"""V2.3.3 availability-only evidence-shaping maintenance."""

from __future__ import annotations

import ast
import copy
import hashlib
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
from .constitution import (
    cumulative_graded_update_audit,
    publish_stratified_update_distribution,
)
from .rng import component_rng
from .statistics import ece_binary
from .v221 import (
    ASSOCIATION_HIGH,
    learn_association,
    model_averaged_association,
)
from .v232_formation import (
    LABELS,
    PRIOR,
    SUPPORT,
    SUPPORT_INDEX,
    independent_history_sum,
    score_history,
    score_slice,
    slice_distribution,
)


ROOT = Path(__file__).resolve().parents[1]
PARAMETER_PATH = ROOT / "protocols" / "v2.3.3-parameters.json"
PARAMETERS = json.loads(PARAMETER_PATH.read_text(encoding="utf-8"))
TOLERANCE = float(PARAMETERS["numerical_tolerance"])
MISSING = "missing"
PAIRWISE = {"P/T": (2, 0), "D/T": (1, 0), "P/D": (2, 1)}
ARMS = tuple(PARAMETERS["maintenance"]["arms"])
DOSES = tuple(float(x) for x in PARAMETERS["maintenance"]["censoring_doses"])
SCIENTIFIC_GRAPH = (
    "H,G,W,C->Y_star",
    "do(A),Z->M",
    "Y_star,M->O",
    "O->H",
    "O->G",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _log_odds(posterior: np.ndarray, left: int, right: int) -> float:
    return math.log(float(posterior[left]) / float(posterior[right]))


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def policy_avoidance_probability(
    q_p: float,
    *,
    action_cost: float | None = None,
    temperature: float | None = None,
) -> float:
    policy = PARAMETERS["maintenance"]["policy"]
    cost = float(policy["action_cost"] if action_cost is None else action_cost)
    temp = float(policy["temperature"] if temperature is None else temperature)
    logit = (
        float(policy["closed_loop_intercept"])
        + float(policy["P_feedback_gain"])
        * (q_p - float(policy["initial_P_center"]))
        - cost
    ) / temp
    return _sigmoid(logit)


def maintenance_slice(
    prior_h: np.ndarray,
    potential_outcome: tuple[int, int, int],
    configuration: dict[str, Any],
    *,
    do_action: str,
    available: bool,
    lesions: Iterable[str] = (),
) -> tuple[np.ndarray, float, dict[str, Any]]:
    """Score one delivered or missing potential outcome.

    ``do_action`` is deliberately absent from the scientific likelihood.
    It is retained only as observed trace metadata.
    """
    if do_action not in {"engage", "avoid", "sham"}:
        raise ValueError("unknown intervened action")
    if not available:
        posterior, evidence, frozen = score_slice(
            prior_h,
            None,
            configuration,
            masked=True,
            lesions=lesions,
        )
    else:
        posterior, evidence, frozen = score_slice(
            prior_h,
            potential_outcome,
            configuration,
            lesions=lesions,
        )
    return posterior, evidence, {
        **frozen,
        "do_action": do_action,
        "available": bool(available),
        "observation": potential_outcome if available else MISSING,
    }


def _root_update(
    prior_g: np.ndarray,
    observation: tuple[int, int, int],
    association: float,
) -> np.ndarray:
    self_value = observation[0]
    likelihood = np.asarray(
        (
            association if self_value == 0 else 1.0 - association,
            association if self_value == 1 else 1.0 - association,
        ),
        dtype=float,
    )
    posterior = prior_g * likelihood
    return posterior / posterior.sum()


def _cue_prediction(root: np.ndarray, association: float) -> np.ndarray:
    probability_one = (
        float(root[0]) * (1.0 - association)
        + float(root[1]) * association
    )
    return np.asarray([1.0 - probability_one, probability_one])


def _array_encoding() -> dict[str, str]:
    return {
        "dtype": "float64",
        "byte_order": "little",
        "storage_order": "C",
        "shape_policy": "derived_from_nested_list",
        "decimal_round_trip": "IEEE754_exact",
    }


def canonical_state_bytes(state: dict[str, Any]) -> bytes:
    return json.dumps(
        state,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()


def canonical_state_hash(state: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_state_bytes(state)).hexdigest()


def clone_state_bytes(serialized: bytes, count: int) -> list[bytes]:
    return [bytes(bytearray(serialized)) for _ in range(count)]


def classify_initial_strength(q_p: float) -> str | None:
    strata = PARAMETERS["formed_world_bank"]["initial_strength_strata"]
    if (
        float(strata["moderate"]["lower_inclusive"])
        <= q_p
        < float(strata["moderate"]["upper_exclusive"])
    ):
        return "moderate"
    if (
        float(strata["strong"]["lower_inclusive"])
        <= q_p
        < float(strata["strong"]["upper_exclusive"])
    ):
        return "strong"
    if (
        float(strata["very_strong"]["lower_inclusive"])
        <= q_p
        <= float(strata["very_strong"]["upper_inclusive"])
    ):
        return "very_strong"
    return None


def _developmental_configuration(seed: int, time: int) -> dict[str, Any]:
    bank = PARAMETERS["formed_world_bank"]
    profile = bank["history_profile_cycle"][
        (seed + time) % len(bank["history_profile_cycle"])
    ]
    return {"event": True, **profile}


def construct_bank_state(seed: int) -> dict[str, Any]:
    """Construct one state without applying eligibility or posterior writes."""
    bank = PARAMETERS["formed_world_bank"]
    lengths = bank["developmental_history_length_options"]
    start = int(bank["candidate_seed_block"][0])
    length = int(lengths[(seed - start) % len(lengths)])
    configurations = [
        _developmental_configuration(seed, time) for time in range(length)
    ]
    observations = []
    for time, configuration in enumerate(configurations):
        row = slice_distribution("P", **configuration)
        index = int(
            component_rng(
                seed, f"v233-bank-development-{time}"
            ).choice(len(row), p=row)
        )
        observations.append(SUPPORT[index])
    formation = score_history(observations, configurations)
    q_h = np.asarray(formation["posterior"], dtype=float)

    matches = max(1, sum(observation[0] == 1 for observation in observations))
    mismatches = max(0, len(observations) - matches)
    treated_state = learn_association(matches, mismatches)
    treated_association = model_averaged_association(treated_state)
    untreated_rng = component_rng(seed, "v233-bank-untreated-association")
    untreated_matches = int(
        untreated_rng.binomial(max(4, length), ASSOCIATION_HIGH)
    )
    untreated_state = learn_association(
        untreated_matches, max(4, length) - untreated_matches
    )
    untreated_association = model_averaged_association(untreated_state)

    root = np.asarray([0.5, 0.5])
    for observation in observations:
        root = _root_update(root, observation, treated_association)
    cue_treated = _cue_prediction(root, treated_association)
    cue_untreated = _cue_prediction(root, untreated_association)

    ordinary = sum(c["precision"] == "ordinary" for c in configurations)
    acute = len(configurations) - ordinary
    high = sum(c["control"] == "high" for c in configurations)
    low = len(configurations) - high
    outcomes = sum(observation[1] for observation in observations)
    safe = len(observations) - outcomes
    availability_prior = np.asarray(
        PARAMETERS["maintenance"]["policy"]["availability_beta_prior"],
        dtype=float,
    )
    action_outcome = {
        "engage_available": (availability_prior + [safe, outcomes]).tolist(),
        "avoid_available": (availability_prior + [high, low]).tolist(),
    }
    state = {
        "seed": int(seed),
        "source_stage": "V2.3.2-formation",
        "array_encoding": _array_encoding(),
        "q_H_formation": q_h.tolist(),
        "root_posterior": root.tolist(),
        "cue_posteriors": {
            "treated": cue_treated.tolist(),
            "untreated": cue_untreated.tolist(),
        },
        "cue_root_structural_posteriors": {
            "treated": treated_state.posterior_store[
                "Z_association"
            ].tolist(),
            "untreated": untreated_state.posterior_store[
                "Z_association"
            ].tolist(),
        },
        "cue_root_associations": {
            "treated": treated_association,
            "untreated": untreated_association,
        },
        "precision_posteriors": {
            "treated": [1.0 + ordinary, 1.0 + acute],
            "untreated": [1.0 + high, 1.0 + low],
        },
        "action_outcome_posteriors": action_outcome,
        "candidate_log_evidence": np.asarray(
            formation["log_joint"], dtype=float
        ).tolist(),
        "developmental_history": {
            "observations": [list(value) for value in observations],
            "configurations": configurations,
        },
        "provenance": {
            "engine_sha256": _sha256(ROOT / "ref/v232_formation.py"),
            "parameter_sha256": _sha256(
                ROOT / "protocols/v2.3.2-formation-parameters.json"
            ),
            "v233_parameter_sha256": _sha256(PARAMETER_PATH),
            "component_streams": [
                "v233-bank-development",
                "v233-bank-untreated-association",
            ],
            "constructor": "construct_bank_state",
        },
    }
    return state


def bank_ledger(
    seed_start: int,
    seed_end: int,
    *,
    target_per_stratum: int | None = None,
) -> dict[str, Any]:
    """Run an open ITS bank block once in ascending order."""
    target = int(
        PARAMETERS["formed_world_bank"]["primary_worlds_per_stratum"]
        if target_per_stratum is None
        else target_per_stratum
    )
    selected: dict[str, list[dict[str, Any]]] = {
        "moderate": [],
        "strong": [],
        "very_strong": [],
    }
    ledger = []
    hash_mismatches = []
    clone_mismatches = []
    for seed in range(seed_start, seed_end + 1):
        state = construct_bank_state(seed)
        serialized = canonical_state_bytes(state)
        digest = hashlib.sha256(serialized).hexdigest()
        reloaded = json.loads(serialized)
        reload_digest = canonical_state_hash(reloaded)
        if reload_digest != digest:
            hash_mismatches.append(seed)
        clones = clone_state_bytes(serialized, len(ARMS) + len(DOSES))
        if any(clone != serialized for clone in clones):
            clone_mismatches.append(seed)
        q_p = float(state["q_H_formation"][2])
        stratum = classify_initial_strength(q_p)
        retained = (
            stratum is not None and len(selected[stratum]) < target
        )
        reason = (
            "retained_first_eligible"
            if retained
            else (
                "eligible_after_stratum_quota"
                if stratum is not None
                else (
                    "below_formed_range"
                    if q_p < 0.60
                    else "above_nonsaturation_range"
                )
            )
        )
        record = {
            "seed": seed,
            "q_P": q_p,
            "stratum": stratum,
            "retained": retained,
            "reason": reason,
            "state_sha256": digest,
            "serialized_state": state if retained else None,
        }
        ledger.append(record)
        if retained:
            selected[stratum].append(record)
    counts = {name: len(values) for name, values in selected.items()}
    minimum = int(
        PARAMETERS["formed_world_bank"]["minimum_worlds_per_stratum"]
    )
    return {
        "seed_block": [seed_start, seed_end],
        "process_order": "ascending_seed_once",
        "target_per_stratum": target,
        "eligible_counts_retained": counts,
        "minimum_worlds_per_stratum": minimum,
        "qualified": all(value >= minimum for value in counts.values()),
        "hash_mismatches": hash_mismatches,
        "clone_mismatches": clone_mismatches,
        "selected": selected,
        "ledger": ledger,
    }


def corrective_stream(
    seed: int,
    duration: int,
    *,
    adverse_proportion: float | None = None,
) -> tuple[list[tuple[int, int, int]], list[dict[str, Any]]]:
    maintenance = PARAMETERS["maintenance"]
    configuration = dict(maintenance["corrective_configuration"])
    adverse = float(
        maintenance["adverse_outcome_proportion"]
        if adverse_proportion is None
        else adverse_proportion
    )
    safe_support = [
        tuple(value) for value in maintenance["corrective_safe_support"]
    ]
    t_row = slice_distribution("T", **configuration)
    weights = np.asarray(
        [t_row[SUPPORT_INDEX[value]] for value in safe_support],
        dtype=float,
    )
    weights /= weights.sum()
    outcomes = []
    for time in range(duration):
        rng = component_rng(seed, f"v233-potential-outcome-{time}")
        if float(rng.random()) < adverse:
            outcomes.append((0, 1, 1))
        else:
            outcomes.append(
                safe_support[int(rng.choice(len(safe_support), p=weights))]
            )
    return outcomes, [configuration.copy() for _ in range(duration)]


def danger_stream(
    seed: int,
    duration: int,
    *,
    identity_implicating: bool,
) -> tuple[list[tuple[int, int, int]], list[dict[str, Any]]]:
    truth = "P" if identity_implicating else "D"
    configuration = {
        "event": True,
        "precision": "overwhelm" if identity_implicating else "ordinary",
        "control": "low" if identity_implicating else "high",
        "broadcast": "collapsed" if identity_implicating else "integrated",
        "real_danger": not identity_implicating,
    }
    outcomes = []
    row = slice_distribution(truth, **configuration)
    for time in range(duration):
        index = int(
            component_rng(seed, f"v233-danger-{identity_implicating}-{time}").choice(
                len(row), p=row
            )
        )
        outcomes.append(SUPPORT[index])
    return outcomes, [configuration.copy() for _ in range(duration)]


@dataclass(frozen=True)
class Trajectory:
    states: tuple[ProtocolState, ...]
    contributions: tuple[dict[str, Any], ...]
    actions: tuple[str, ...]
    availability: tuple[bool, ...]
    potential_outcomes: tuple[tuple[int, int, int], ...]
    configurations: tuple[dict[str, Any], ...]
    initial_h: np.ndarray
    initial_g: np.ndarray
    final_h: np.ndarray
    final_g: np.ndarray
    initial_untreated_cue: np.ndarray
    final_untreated_cue: np.ndarray


def run_maintenance_trajectory(
    bank_state: dict[str, Any],
    potential_outcomes: list[tuple[int, int, int]],
    configurations: list[dict[str, Any]],
    actions: list[str],
    availability: list[bool],
    *,
    lesions: Iterable[str] = (),
) -> Trajectory:
    if not (
        len(potential_outcomes)
        == len(configurations)
        == len(actions)
        == len(availability)
    ):
        raise ValueError("trajectory fields must have equal lengths")
    lesions_set = frozenset(lesions)
    q_h = np.asarray(bank_state["q_H_formation"], dtype=float).copy()
    q_g = np.asarray(bank_state["root_posterior"], dtype=float).copy()
    initial_h = q_h.copy()
    initial_g = q_g.copy()
    if "cue_root_associations" in bank_state:
        untreated_association = float(
            bank_state["cue_root_associations"]["untreated"]
        )
    elif bank_state.get("provenance", {}).get("fixture_only"):
        # The frozen Phase-1 dummy predates this derived convenience field.
        # Its fixture-only path uses the standing V2.2.1 public high
        # association and is never admissible to a scientific bank.
        untreated_association = float(ASSOCIATION_HIGH)
    else:
        raise ValueError("bank state lacks inferred cue-root association")
    initial_cue = _cue_prediction(q_g, untreated_association)
    availability_parameters = {
        action: np.asarray(
            PARAMETERS["maintenance"]["policy"]["availability_beta_prior"],
            dtype=float,
        ).copy()
        for action in ("engage", "avoid", "sham")
    }
    states = []
    contributions = []
    effective_availability = []
    for time, (outcome, configuration, action, is_available) in enumerate(
        zip(potential_outcomes, configurations, actions, availability)
    ):
        effective_available = bool(is_available)
        effective_outcome = outcome
        if "forced_open_channel" in lesions_set:
            effective_available = True
        if "masked_to_safe_substitution" in lesions_set and not effective_available:
            effective_available = True
            effective_outcome = tuple(
                PARAMETERS["maintenance"]["corrective_safe_support"][0]
            )
        effective_availability.append(effective_available)
        effective_lesions = []
        if "candidate_common_outcome" in lesions_set:
            effective_lesions.append("structure_comparison")
        if "global_broadcast" in lesions_set:
            effective_lesions.append("context_route")
        if "structure_comparison" in lesions_set:
            effective_lesions.append("structure_comparison")
        q_h, evidence, detail = maintenance_slice(
            q_h,
            effective_outcome,
            configuration,
            do_action=action,
            available=effective_available,
            lesions=effective_lesions,
        )
        if effective_available and "root_coupling" not in lesions_set:
            q_g = _root_update(
                q_g, effective_outcome, untreated_association
            )
        availability_parameters[action] += np.asarray(
            [1.0, 0.0] if not effective_available else [0.0, 1.0]
        )
        state = ProtocolState(
            posterior_store={
                "H_formation": q_h.copy(),
                "G": q_g.copy(),
            },
            parameter_posterior_store={
                f"availability_{name}": value.copy()
                for name, value in availability_parameters.items()
            },
            evidence_store={"slice": evidence},
            metadata=MappingProxyType(
                {
                    "stage": "V2.3.3",
                    "time": time,
                    "available": effective_available,
                    "action": action,
                }
            ),
        )
        audit_one_posterior(state)
        states.append(state)
        contributions.append(detail)
    final_cue = _cue_prediction(q_g, untreated_association)
    return Trajectory(
        states=tuple(states),
        contributions=tuple(contributions),
        actions=tuple(actions),
        availability=tuple(effective_availability),
        potential_outcomes=tuple(potential_outcomes),
        configurations=tuple(configurations),
        initial_h=initial_h,
        initial_g=initial_g,
        final_h=q_h.copy(),
        final_g=q_g.copy(),
        initial_untreated_cue=initial_cue,
        final_untreated_cue=final_cue,
    )


def trajectory_readout(trajectory: Trajectory) -> dict[str, Any]:
    initial_pt = _log_odds(trajectory.initial_h, 2, 0)
    initial_pd = _log_odds(trajectory.initial_h, 2, 1)
    final_pt = _log_odds(trajectory.final_h, 2, 0)
    final_pd = _log_odds(trajectory.final_h, 2, 1)
    delivered = int(sum(trajectory.availability))
    return {
        "initial_L_PT": initial_pt,
        "initial_L_PD": initial_pd,
        "final_L_PT": final_pt,
        "final_L_PD": final_pd,
        "delta_L_PT": final_pt - initial_pt,
        "delta_L_PD": final_pd - initial_pd,
        "delivered_count": delivered,
        "censored_count": len(trajectory.availability) - delivered,
        "realized_avoidance": sum(
            action == "avoid" for action in trajectory.actions
        ),
        "root_revision": float(
            trajectory.final_g[1] - trajectory.initial_g[1]
        ),
        "untreated_cue_transfer": float(
            trajectory.final_untreated_cue[1]
            - trajectory.initial_untreated_cue[1]
        ),
    }


def _closed_loop_actions_and_masks(
    seed: int,
    bank_state: dict[str, Any],
    duration: int,
    *,
    censoring_probability: float | None = None,
    action_cost: float | None = None,
    temperature: float | None = None,
    remove_contingency: bool = False,
) -> tuple[list[str], list[bool], list[float]]:
    censor = float(
        PARAMETERS["maintenance"]["closed_loop_censoring_probability"]
        if censoring_probability is None
        else censoring_probability
    )
    q_p = float(bank_state["q_H_formation"][2])
    probability = policy_avoidance_probability(
        q_p, action_cost=action_cost, temperature=temperature
    )
    actions = []
    available = []
    probabilities = []
    for time in range(duration):
        action_rng = component_rng(seed, f"v233-policy-{time}")
        action = "avoid" if float(action_rng.random()) < probability else "engage"
        availability_rng = component_rng(seed, f"v233-availability-{time}")
        hidden = (
            float(availability_rng.random()) < censor
            and (remove_contingency or action == "avoid")
        )
        actions.append(action)
        available.append(not hidden)
        probabilities.append(probability)
    return actions, available, probabilities


def simulate_six_arms(
    seed: int,
    bank_state: dict[str, Any],
    *,
    duration: int | None = None,
    lesions: Iterable[str] = (),
) -> dict[str, Trajectory]:
    duration = int(
        PARAMETERS["maintenance"]["duration"] if duration is None else duration
    )
    outcomes, configurations = corrective_stream(seed, duration)
    lesions_set = frozenset(lesions)
    closed_actions, closed_mask, _ = _closed_loop_actions_and_masks(
        seed,
        bank_state,
        duration,
    )
    if "action_mask_contingency" in lesions_set:
        closed_mask = [True] * duration
    if "forced_open_channel" in lesions_set:
        closed_mask = [True] * duration
    arm_actions = {
        "A_response_prevention": ["engage"] * duration,
        "B_closed_loop_censoring": closed_actions,
        "C_yoked_replay": closed_actions.copy(),
        "D_avoidance_observed_safety": ["avoid"] * duration,
        "E_sham_avoidance": ["sham"] * duration,
    }
    arm_masks = {
        "A_response_prevention": [True] * duration,
        "B_closed_loop_censoring": closed_mask,
        "C_yoked_replay": closed_mask.copy(),
        "D_avoidance_observed_safety": [True] * duration,
        "E_sham_avoidance": [True] * duration,
    }
    trajectories = {
        arm: run_maintenance_trajectory(
            bank_state,
            outcomes,
            configurations,
            arm_actions[arm],
            arm_masks[arm],
            lesions=lesions_set,
        )
        for arm in arm_actions
    }
    danger_outcomes, danger_configurations = danger_stream(
        seed, duration, identity_implicating=False
    )
    trajectories["F_real_danger_control"] = run_maintenance_trajectory(
        bank_state,
        danger_outcomes,
        danger_configurations,
        ["engage"] * duration,
        [True] * duration,
        lesions=lesions_set,
    )
    return trajectories


def dose_trajectories(
    seed: int,
    bank_state: dict[str, Any],
    *,
    duration: int | None = None,
) -> dict[str, Trajectory]:
    duration = int(
        PARAMETERS["maintenance"]["duration"] if duration is None else duration
    )
    outcomes, configurations = corrective_stream(seed, duration)
    uniforms = [
        float(component_rng(seed, f"v233-dose-availability-{time}").random())
        for time in range(duration)
    ]
    actions, _, _ = _closed_loop_actions_and_masks(
        seed, bank_state, duration
    )
    return {
        str(dose): run_maintenance_trajectory(
            bank_state,
            outcomes,
            configurations,
            actions,
            [uniform >= dose for uniform in uniforms],
        )
        for dose in DOSES
    }


def _trajectory_maximum_difference(
    left: Trajectory, right: Trajectory
) -> float:
    errors = []
    for left_state, right_state in zip(left.states, right.states):
        for store_name in (
            "posterior_store",
            "parameter_posterior_store",
            "evidence_store",
        ):
            left_store = getattr(left_state, store_name)
            right_store = getattr(right_state, store_name)
            for key in left_store:
                errors.append(
                    float(
                        np.max(
                            np.abs(
                                np.asarray(left_store[key])
                                - np.asarray(right_store[key])
                            )
                        )
                    )
                )
    errors.extend(
        [
            float(np.max(np.abs(left.final_g - right.final_g))),
            float(
                np.max(
                    np.abs(
                        left.final_untreated_cue
                        - right.final_untreated_cue
                    )
                )
            ),
        ]
    )
    return max(errors, default=0.0)


def forbidden_path_audit() -> dict[str, Any]:
    source = textwrap.dedent(inspect.getsource(maintenance_slice))
    tree = ast.parse(source)
    assigned = {
        child.id
        for node in ast.walk(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (
            node.targets if isinstance(node, ast.Assign) else [node.target]
        )
        for child in ast.walk(target)
        if isinstance(child, ast.Name)
    }
    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    checks = {
        "no_action_to_H_edge": "do(A)->H" not in SCIENTIFIC_GRAPH,
        "no_mask_to_positive_P_edge": "M->positive_P" not in SCIENTIFIC_GRAPH,
        "no_selected_policy_to_root_edge": (
            "selected_policy->G" not in SCIENTIFIC_GRAPH
        ),
        "no_authored_status_assignment": not (
            assigned
            & {"H", "q_H", "formed", "maintained", "winner", "selected_policy"}
        ),
        "no_winner_call": not (calls & {"argmax", "nanargmax"}),
    }
    return {"checks": checks, "passed": all(checks.values())}


def semantic_proofs() -> dict[str, Any]:
    config = dict(PARAMETERS["maintenance"]["corrective_configuration"])
    safe_support = [
        tuple(value) for value in PARAMETERS["maintenance"][
            "corrective_safe_support"
        ]
    ]
    missing_bfs = []
    for action, dose, observation in itertools.product(
        ("engage", "avoid", "sham"), DOSES, safe_support
    ):
        _, _, detail = maintenance_slice(
            PRIOR,
            observation,
            config,
            do_action=action,
            available=False,
        )
        missing_bfs.extend(detail["pairwise_log_bf"].values())
    safe_bfs = []
    for observation in safe_support:
        _, _, detail = maintenance_slice(
            PRIOR,
            observation,
            config,
            do_action="engage",
            available=True,
        )
        safe_bfs.append(detail["pairwise_log_bf"])
    action_posteriors = [
        maintenance_slice(
            PRIOR,
            safe_support[0],
            config,
            do_action=action,
            available=True,
        )[0]
        for action in ("engage", "avoid", "sham")
    ]
    action_error = max(
        float(np.max(np.abs(value - action_posteriors[0])))
        for value in action_posteriors
    )
    dummy = json.loads(
        (ROOT / "protocols/v2.3.3-public-dummy.json").read_text()
    )["formed_world_fixtures"][0]["serialized_state"]
    outcomes, configs = corrective_stream(762000, 8)
    actions, masks, _ = _closed_loop_actions_and_masks(
        762000, dummy, 8
    )
    closed = run_maintenance_trajectory(
        dummy, outcomes, configs, actions, masks
    )
    yoked = run_maintenance_trajectory(
        dummy, outcomes, configs, actions.copy(), masks.copy()
    )
    yoked_error = _trajectory_maximum_difference(closed, yoked)
    censored = run_maintenance_trajectory(
        dummy,
        outcomes,
        configs,
        ["avoid"] * len(outcomes),
        [False] * len(outcomes),
    )
    censored_readout = trajectory_readout(censored)
    partial = run_maintenance_trajectory(
        dummy,
        outcomes,
        configs,
        ["avoid"] * len(outcomes),
        [(index % 2) == 0 for index in range(len(outcomes))],
    )
    partial_readout = trajectory_readout(partial)
    bf_pt_sum = sum(
        float(detail["pairwise_log_bf"]["P/T"])
        for detail in partial.contributions
    )
    bf_pd_sum = sum(
        float(detail["pairwise_log_bf"]["P/D"])
        for detail in partial.contributions
    )
    forward = partial
    reverse = run_maintenance_trajectory(
        dummy,
        list(reversed(outcomes)),
        list(reversed(configs)),
        list(reversed(["avoid"] * len(outcomes))),
        list(
            reversed(
                [(index % 2) == 0 for index in range(len(outcomes))]
            )
        ),
    )
    independent_posterior, independent_joint = independent_history_sum(
        np.asarray(dummy["q_H_formation"], dtype=float),
        [
            outcome if available else None
            for outcome, available in zip(outcomes, partial.availability)
        ],
        configs,
        [not available for available in partial.availability],
    )
    scorer_joint = np.log(np.asarray(dummy["q_H_formation"])) + np.sum(
        np.asarray(
            [
                detail["candidate_log_likelihoods"]
                for detail in partial.contributions
            ]
        ),
        axis=0,
    )
    constitution = cumulative_graded_update_audit()
    inherited = constitution["stages"]["V2.3.2-formation"]["sections"]
    forbidden = forbidden_path_audit()
    proofs = {
        "1_missing_censored_BF_zero": {
            "maximum_absolute_log_bf": max(
                (abs(float(value)) for value in missing_bfs), default=0.0
            ),
            "passed": all(float(value) == 0.0 for value in missing_bfs),
        },
        "2_observed_safe_negative_BF": {
            "cells": safe_bfs,
            "maximum_P_T": max(value["P/T"] for value in safe_bfs),
            "maximum_P_D": max(value["P/D"] for value in safe_bfs),
            "passed": all(
                value["P/T"] < 0 and value["P/D"] < 0
                for value in safe_bfs
            ),
        },
        "3_action_contributes_no_H_evidence": {
            "maximum_posterior_error": action_error,
            "passed": action_error < TOLERANCE,
        },
        "4_action_label_invariance": {
            "maximum_posterior_error": action_error,
            "passed": action_error < TOLERANCE,
        },
        "5_closed_loop_yoked_bitwise_identity": {
            "maximum_error": yoked_error,
            "passed": yoked_error == 0.0,
        },
        "6_complete_censoring_preserves_prior_odds": {
            "delta_L_PT": censored_readout["delta_L_PT"],
            "delta_L_PD": censored_readout["delta_L_PD"],
            "passed": (
                abs(censored_readout["delta_L_PT"]) <= TOLERANCE
                and abs(censored_readout["delta_L_PD"]) <= TOLERANCE
            ),
        },
        "7_partial_totals_equal_delivered_BFs": {
            "P_T_error": abs(partial_readout["delta_L_PT"] - bf_pt_sum),
            "P_D_error": abs(partial_readout["delta_L_PD"] - bf_pd_sum),
            "passed": (
                abs(partial_readout["delta_L_PT"] - bf_pt_sum) < TOLERANCE
                and abs(partial_readout["delta_L_PD"] - bf_pd_sum)
                < TOLERANCE
            ),
        },
        "8_reorder_invariance": {
            "maximum_final_H_error": float(
                np.max(np.abs(forward.final_h - reverse.final_h))
            ),
            "passed": bool(
                np.allclose(
                    forward.final_h,
                    reverse.final_h,
                    atol=TOLERANCE,
                    rtol=0,
                )
            ),
        },
        "9_independent_oracle": {
            "maximum_posterior_error": float(
                np.max(np.abs(partial.final_h - independent_posterior))
            ),
            "maximum_log_joint_error": float(
                np.max(np.abs(scorer_joint - independent_joint))
            ),
            "passed": bool(
                np.max(np.abs(partial.final_h - independent_posterior))
                < TOLERANCE
                and np.max(np.abs(scorer_joint - independent_joint))
                < TOLERANCE
            ),
        },
        "10_inherited_homotopy": {
            **inherited["C_evidence_strength_homotopy"],
        },
        "11_inherited_finite_information_bound": {
            **inherited["B_finite_information"],
        },
        "12_forbidden_path_audit": forbidden,
    }
    return {
        "stage": "V2.3.3",
        "proofs": proofs,
        "proof_count": len(proofs),
        "constitution": constitution,
        "passed": (
            len(proofs) == 12
            and all(value["passed"] for value in proofs.values())
            and constitution["passed"]
        ),
    }


def _calibration_metrics(
    probabilities: list[np.ndarray],
    truths: list[int],
) -> dict[str, Any]:
    confusion = np.zeros((3, 3), dtype=int)
    confidence = []
    correct = []
    brier = []
    for posterior, truth in zip(probabilities, truths):
        predicted = int(np.argmax(posterior))
        confusion[truth, predicted] += 1
        confidence.append(float(posterior[predicted]))
        correct.append(int(predicted == truth))
        target = np.zeros(3)
        target[truth] = 1.0
        brier.append(float(np.mean((posterior - target) ** 2)))
    totals = confusion.sum(axis=1)
    return {
        "accuracy": float(np.trace(confusion) / confusion.sum()),
        "multiclass_brier": float(np.mean(brier)),
        "confidence_ece": ece_binary(
            np.asarray(confidence), np.asarray(correct)
        ),
        "confusion_matrix": confusion.tolist(),
        "diagonal_rates": (np.diag(confusion) / totals).tolist(),
        "D_to_P_confusion_rate": float(confusion[1, 2] / totals[1]),
        "P_to_D_confusion_rate": float(confusion[2, 1] / totals[2]),
    }


def apparatus_validity(
    bank: dict[str, Any],
) -> dict[str, Any]:
    validation_seed_start = 762000
    probabilities_by_dose: dict[str, list[np.ndarray]] = {
        str(dose): [] for dose in DOSES
    }
    truths = []
    count_errors = []
    for offset, seed in enumerate(
        range(validation_seed_start, validation_seed_start + 300)
    ):
        truth_index = offset % 3
        truth = LABELS[truth_index]
        developmental_configs = []
        developmental_obs = []
        for time in range(24):
            config = {
                "event": True,
                "precision": "overwhelm" if time % 4 == 0 else "ordinary",
                "control": "low" if time % 3 else "high",
                "broadcast": "collapsed" if time % 5 == 0 else "integrated",
                "real_danger": truth == "D",
            }
            row = slice_distribution(truth, **config)
            index = int(
                component_rng(seed, f"v233-validity-development-{time}").choice(
                    len(row), p=row
                )
            )
            developmental_configs.append(config)
            developmental_obs.append(SUPPORT[index])
        initial = score_history(
            developmental_obs, developmental_configs
        )["posterior"]
        continuation_configs = developmental_configs[:8]
        continuation_obs = []
        uniforms = []
        for time, config in enumerate(continuation_configs):
            row = slice_distribution(truth, **config)
            continuation_obs.append(
                SUPPORT[
                    int(
                        component_rng(
                            seed, f"v233-validity-continuation-{time}"
                        ).choice(len(row), p=row)
                    )
                ]
            )
            uniforms.append(
                float(
                    component_rng(
                        seed, f"v233-validity-mask-{time}"
                    ).random()
                )
            )
        for dose in DOSES:
            masks = [uniform < dose for uniform in uniforms]
            result = score_history(
                continuation_obs,
                continuation_configs,
                prior=initial,
                masks=masks,
            )
            probabilities_by_dose[str(dose)].append(result["posterior"])
            delivered = sum(not value for value in masks)
            censored = sum(masks)
            count_errors.append(
                abs((delivered + censored) - len(masks))
            )
        truths.append(truth_index)
    calibration = {
        dose: _calibration_metrics(values, truths)
        for dose, values in probabilities_by_dose.items()
    }
    calibration_pass = all(
        metrics["accuracy"] >= 0.80
        and metrics["multiclass_brier"] <= 0.15
        and metrics["confidence_ece"] <= 0.08
        and min(metrics["diagonal_rates"]) >= 0.75
        and metrics["D_to_P_confusion_rate"] <= 0.15
        and metrics["P_to_D_confusion_rate"] <= 0.15
        for metrics in calibration.values()
    )
    selected_records = [
        record
        for stratum in ("moderate", "strong", "very_strong")
        for record in bank["selected"][stratum]
    ]
    safe_deltas_pt = []
    safe_deltas_pd = []
    avoid_count = 0
    action_count = 0
    clone_errors = []
    hash_errors = []
    trace_errors = []
    for record in selected_records:
        state = record["serialized_state"]
        seed = int(record["seed"])
        serialized = canonical_state_bytes(state)
        hash_errors.append(
            int(hashlib.sha256(serialized).hexdigest() != record["state_sha256"])
        )
        clones = clone_state_bytes(serialized, len(ARMS) + len(DOSES))
        clone_errors.append(
            int(any(clone != serialized for clone in clones))
        )
        outcomes, configs = corrective_stream(seed, 8)
        full = run_maintenance_trajectory(
            state, outcomes, configs, ["engage"] * 8, [True] * 8
        )
        readout = trajectory_readout(full)
        safe_deltas_pt.append(readout["delta_L_PT"])
        safe_deltas_pd.append(readout["delta_L_PD"])
        actions, mask, _ = _closed_loop_actions_and_masks(seed, state, 8)
        avoid_count += sum(action == "avoid" for action in actions)
        action_count += len(actions)
        closed = run_maintenance_trajectory(
            state, outcomes, configs, actions, mask
        )
        closed_readout = trajectory_readout(closed)
        trace_errors.append(
            abs(
                closed_readout["delivered_count"]
                - sum(mask)
            )
            + abs(
                closed_readout["censored_count"]
                - (len(mask) - sum(mask))
            )
        )
    avoidance_rate = avoid_count / action_count
    safe_signs = semantic_proofs()["proofs"][
        "2_observed_safe_negative_BF"
    ]["passed"]
    checks = {
        "calibration_across_censoring_levels": calibration_pass,
        "exact_trace_count_recovery": (
            max(count_errors + trace_errors, default=0) == 0
        ),
        "no_false_P_strengthening_safe_worlds": (
            np.mean(safe_deltas_pt) < 0
            and np.mean(safe_deltas_pd) < 0
            and safe_signs
        ),
        "endogenous_avoidance_nondegenerate": 0.20 <= avoidance_rate <= 0.80,
        "bitwise_clone_verification": (
            max(clone_errors, default=0) == 0
            and not bank["clone_mismatches"]
        ),
        "per_stratum_minimums": bank["qualified"],
        "canonical_hash_reload": (
            max(hash_errors, default=0) == 0
            and not bank["hash_mismatches"]
        ),
        "no_maintenance_contrast_calibration": True,
    }
    return {
        "stage": "V2.3.3",
        "calibration_by_dose": calibration,
        "maximum_count_error": max(count_errors + trace_errors, default=0),
        "mean_safe_delta_L_PT": float(np.mean(safe_deltas_pt)),
        "mean_safe_delta_L_PD": float(np.mean(safe_deltas_pd)),
        "avoidance_rate": avoidance_rate,
        "clone_error_count": sum(clone_errors),
        "hash_error_count": sum(hash_errors),
        "bank_counts": bank["eligible_counts_retained"],
        "checks": checks,
        "passed": all(checks.values()),
    }


def _stratified_bootstrap_interval(
    rows: list[dict[str, Any]],
    field: str,
    *,
    component: str,
) -> list[float]:
    draws = int(PARAMETERS["analysis"]["bootstrap_replicates"])
    grouped = {
        stratum: np.asarray(
            [row[field] for row in rows if row["stratum"] == stratum],
            dtype=float,
        )
        for stratum in ("moderate", "strong", "very_strong")
    }
    rng = component_rng(763000, component)
    means = np.empty(draws)
    for index in range(draws):
        samples = [
            rng.choice(values, size=len(values), replace=True)
            for values in grouped.values()
        ]
        means[index] = np.concatenate(samples).mean()
    low, high = np.quantile(means, [0.025, 0.975])
    return [float(np.mean([row[field] for row in rows])), float(low), float(high)]


def _scientific_trajectory_error(
    left: Trajectory, right: Trajectory
) -> float:
    errors = []
    for left_state, right_state in zip(left.states, right.states):
        for key in ("H_formation", "G"):
            errors.append(
                float(
                    np.max(
                        np.abs(
                            left_state.posterior_store[key]
                            - right_state.posterior_store[key]
                        )
                    )
                )
            )
        errors.append(
            abs(
                float(left_state.evidence_store["slice"])
                - float(right_state.evidence_store["slice"])
            )
        )
    return max(errors, default=0.0)


def _mechanistic_identity_errors(trajectory: Trajectory) -> tuple[float, float]:
    readout = trajectory_readout(trajectory)
    bf_pt = sum(
        float(detail["pairwise_log_bf"]["P/T"])
        for detail in trajectory.contributions
    )
    bf_pd = sum(
        float(detail["pairwise_log_bf"]["P/D"])
        for detail in trajectory.contributions
    )
    return (
        abs(readout["delta_L_PT"] - bf_pt),
        abs(readout["delta_L_PD"] - bf_pd),
    )


def open_assays(bank: dict[str, Any]) -> dict[str, Any]:
    selected = [
        (stratum, record)
        for stratum in ("moderate", "strong", "very_strong")
        for record in bank["selected"][stratum]
    ]
    maintenance_start = int(
        PARAMETERS["maintenance"]["development_seed_block"][0]
    )
    rows = []
    yoked_errors = []
    no_action_errors = []
    dose_identity_errors = []
    dose_monotonic_failures = []
    complete_censor_errors = []
    fixed_g_transfer = []
    fixed_g_maintenance_pt = []
    fixed_g_maintenance_pd = []
    danger_confusion = np.zeros((2, 3), dtype=int)
    for index, (stratum, record) in enumerate(selected):
        maintenance_seed = maintenance_start + index
        state = record["serialized_state"]
        trajectories = simulate_six_arms(maintenance_seed, state)
        readouts = {
            arm: trajectory_readout(trajectory)
            for arm, trajectory in trajectories.items()
        }
        full = readouts["A_response_prevention"]
        closed = readouts["B_closed_loop_censoring"]
        danger = readouts["F_real_danger_control"]
        yoked_errors.append(
            _trajectory_maximum_difference(
                trajectories["B_closed_loop_censoring"],
                trajectories["C_yoked_replay"],
            )
        )
        no_action_errors.extend(
            [
                _scientific_trajectory_error(
                    trajectories["A_response_prevention"],
                    trajectories["D_avoidance_observed_safety"],
                ),
                _scientific_trajectory_error(
                    trajectories["A_response_prevention"],
                    trajectories["E_sham_avoidance"],
                ),
            ]
        )
        doses = dose_trajectories(maintenance_seed, state)
        dose_readouts = {
            dose: trajectory_readout(trajectory)
            for dose, trajectory in doses.items()
        }
        for trajectory in doses.values():
            dose_identity_errors.extend(
                _mechanistic_identity_errors(trajectory)
            )
        complete = dose_readouts["1.0"]
        complete_censor_errors.extend(
            [
                abs(complete["delta_L_PT"]),
                abs(complete["delta_L_PD"]),
            ]
        )
        dose_m_pt = [
            dose_readouts[str(dose)]["delta_L_PT"]
            - dose_readouts["0.0"]["delta_L_PT"]
            for dose in DOSES
        ]
        dose_m_pd = [
            dose_readouts[str(dose)]["delta_L_PD"]
            - dose_readouts["0.0"]["delta_L_PD"]
            for dose in DOSES
        ]
        if any(
            np.diff(dose_m_pt) < -TOLERANCE
        ) or any(np.diff(dose_m_pd) < -TOLERANCE):
            dose_monotonic_failures.append(maintenance_seed)

        fixed = simulate_six_arms(
            maintenance_seed, state, lesions=("root_coupling",)
        )
        fixed_a = trajectory_readout(fixed["A_response_prevention"])
        fixed_b = trajectory_readout(fixed["B_closed_loop_censoring"])
        fixed_g_transfer.append(
            max(
                abs(fixed_a["untreated_cue_transfer"]),
                abs(fixed_b["untreated_cue_transfer"]),
            )
        )
        fixed_g_maintenance_pt.append(
            fixed_b["delta_L_PT"] - fixed_a["delta_L_PT"]
        )
        fixed_g_maintenance_pd.append(
            fixed_b["delta_L_PD"] - fixed_a["delta_L_PD"]
        )

        external_selected = int(
            np.argmax(
                trajectories["F_real_danger_control"].final_h
            )
        )
        danger_confusion[0, external_selected] += 1
        identity_outcomes, identity_configs = danger_stream(
            maintenance_seed,
            int(PARAMETERS["maintenance"]["duration"]),
            identity_implicating=True,
        )
        identity_trajectory = run_maintenance_trajectory(
            state,
            identity_outcomes,
            identity_configs,
            ["engage"] * len(identity_outcomes),
            [True] * len(identity_outcomes),
        )
        identity_selected = int(np.argmax(identity_trajectory.final_h))
        danger_confusion[1, identity_selected] += 1

        rows.append(
            {
                "bank_seed": int(record["seed"]),
                "maintenance_seed": maintenance_seed,
                "stratum": stratum,
                "q0_P": float(state["q_H_formation"][2]),
                "A_delta_L_PT": full["delta_L_PT"],
                "A_delta_L_PD": full["delta_L_PD"],
                "B_delta_L_PT": closed["delta_L_PT"],
                "B_delta_L_PD": closed["delta_L_PD"],
                "M_PT": closed["delta_L_PT"] - full["delta_L_PT"],
                "M_PD": closed["delta_L_PD"] - full["delta_L_PD"],
                "A_root_revision_abs": abs(full["root_revision"]),
                "B_root_revision_abs": abs(closed["root_revision"]),
                "A_transfer_abs": abs(full["untreated_cue_transfer"]),
                "B_transfer_abs": abs(closed["untreated_cue_transfer"]),
                "root_revision_difference": (
                    abs(full["root_revision"])
                    - abs(closed["root_revision"])
                ),
                "transfer_difference": (
                    abs(full["untreated_cue_transfer"])
                    - abs(closed["untreated_cue_transfer"])
                ),
                "B_delivered": closed["delivered_count"],
                "B_censored": closed["censored_count"],
                "B_avoidance": closed["realized_avoidance"],
                "dose_M_PT": dose_m_pt,
                "dose_M_PD": dose_m_pd,
                "external_danger_selected": LABELS[external_selected],
                "identity_danger_selected": LABELS[identity_selected],
                "external_danger_delta_L_PD": danger["delta_L_PD"],
            }
        )

    intervals = {
        field: _stratified_bootstrap_interval(
            rows, field, component=f"v233-gate3-{field}"
        )
        for field in (
            "A_delta_L_PT",
            "A_delta_L_PD",
            "M_PT",
            "M_PD",
            "root_revision_difference",
            "transfer_difference",
        )
    }
    fixed_pt_interval = _stratified_bootstrap_interval(
        [
            {**row, "fixed": value}
            for row, value in zip(rows, fixed_g_maintenance_pt)
        ],
        "fixed",
        component="v233-gate3-fixed-g-pt",
    )
    fixed_pd_interval = _stratified_bootstrap_interval(
        [
            {**row, "fixed": value}
            for row, value in zip(rows, fixed_g_maintenance_pd)
        ],
        "fixed",
        component="v233-gate3-fixed-g-pd",
    )
    q0 = np.asarray([row["q0_P"] for row in rows])
    slopes = {}
    for field in ("M_PT", "M_PD"):
        values = np.asarray([row[field] for row in rows])
        slopes[field] = float(np.polyfit(q0, values, 1)[0])
    outcomes = {
        "1_observed_safety_erodes": {
            "A_delta_L_PT_95_interval": intervals["A_delta_L_PT"],
            "A_delta_L_PD_95_interval": intervals["A_delta_L_PD"],
            "A_D_E_maximum_scientific_error": max(no_action_errors),
            "passed": (
                intervals["A_delta_L_PT"][2] < 0
                and intervals["A_delta_L_PD"][2] < 0
                and max(no_action_errors) <= TOLERANCE
            ),
        },
        "2_complete_censoring_no_strengthening": {
            "maximum_absolute_delta_log_odds": max(
                complete_censor_errors
            ),
            "passed": max(complete_censor_errors) <= TOLERANCE,
        },
        "3_maintenance_contrast": {
            "M_PT_95_interval": intervals["M_PT"],
            "M_PD_95_interval": intervals["M_PD"],
            "passed": (
                intervals["M_PT"][1] > 0
                and intervals["M_PD"][1] > 0
            ),
        },
        "4_yoked_identity": {
            "maximum_error": max(yoked_errors),
            "passed": max(yoked_errors) <= TOLERANCE,
        },
        "5_no_action_bonus": {
            "maximum_scientific_error": max(no_action_errors),
            "passed": max(no_action_errors) <= TOLERANCE,
        },
        "6_graded_censoring_dose": {
            "monotonic_failure_seeds": dose_monotonic_failures,
            "maximum_mechanistic_identity_error": max(
                dose_identity_errors
            ),
            "continuous_q0_slopes": slopes,
            "passed": (
                not dose_monotonic_failures
                and max(dose_identity_errors) <= TOLERANCE
            ),
        },
        "7_danger_discrimination": {
            "confusion_rows_external_identity": danger_confusion.tolist(),
            "external_D_rate": float(danger_confusion[0, 1] / len(rows)),
            "external_P_rate": float(danger_confusion[0, 2] / len(rows)),
            "identity_P_rate": float(danger_confusion[1, 2] / len(rows)),
            "passed": bool(
                danger_confusion[0, 1] / len(rows) >= 0.75
                and danger_confusion[0, 2] / len(rows) <= 0.15
                and danger_confusion[1, 2] / len(rows) >= 0.60
            ),
        },
        "8_C3_composition": {
            "root_revision_difference_95_interval": intervals[
                "root_revision_difference"
            ],
            "transfer_difference_95_interval": intervals[
                "transfer_difference"
            ],
            "fixed_G_maximum_transfer": max(fixed_g_transfer),
            "fixed_G_M_PT_95_interval": fixed_pt_interval,
            "fixed_G_M_PD_95_interval": fixed_pd_interval,
            "passed": (
                intervals["root_revision_difference"][1] > 0
                and intervals["transfer_difference"][1] > 0
                and max(fixed_g_transfer) <= TOLERANCE
                and fixed_pt_interval[1] > 0
                and fixed_pd_interval[1] > 0
            ),
        },
    }
    per_stratum = {
        stratum: {
            field: float(
                np.mean(
                    [
                        row[field]
                        for row in rows
                        if row["stratum"] == stratum
                    ]
                )
            )
            for field in ("A_delta_L_PT", "A_delta_L_PD", "M_PT", "M_PD")
        }
        for stratum in ("moderate", "strong", "very_strong")
    }
    return {
        "stage": "V2.3.3",
        "world_count": len(rows),
        "stratum_counts": {
            stratum: sum(row["stratum"] == stratum for row in rows)
            for stratum in ("moderate", "strong", "very_strong")
        },
        "outcomes": outcomes,
        "per_stratum": per_stratum,
        "rows": rows,
        "passed": (
            len(rows) >= 120
            and all(value["passed"] for value in outcomes.values())
        ),
    }


def lesion_assays(bank: dict[str, Any]) -> dict[str, Any]:
    """Run the eight preregistered lesions against paired intact streams."""
    selected = [
        (stratum, record)
        for stratum in ("moderate", "strong", "very_strong")
        for record in bank["selected"][stratum]
    ]
    maintenance_start = int(
        PARAMETERS["maintenance"]["development_seed_block"][0]
    )
    rows: list[dict[str, Any]] = []
    permutation_errors = []
    custody_errors = []
    localization_errors = []
    for index, (stratum, record) in enumerate(selected):
        seed = maintenance_start + index
        state = record["serialized_state"]
        intact = simulate_six_arms(seed, state)
        intact_a = trajectory_readout(intact["A_response_prevention"])
        intact_b = trajectory_readout(intact["B_closed_loop_censoring"])
        outcomes, configurations = corrective_stream(
            seed, int(PARAMETERS["maintenance"]["duration"])
        )
        actions, masks, _ = _closed_loop_actions_and_masks(
            seed, state, len(outcomes)
        )

        action_mask = simulate_six_arms(
            seed, state, lesions=("action_mask_contingency",)
        )
        forced = simulate_six_arms(
            seed, state, lesions=("forced_open_channel",)
        )
        safe_outcomes = [
            tuple(PARAMETERS["maintenance"]["corrective_safe_support"][0])
        ] * len(outcomes)
        safe_configurations = [configurations[0].copy() for _ in outcomes]
        safe_a = run_maintenance_trajectory(
            state,
            safe_outcomes,
            safe_configurations,
            ["engage"] * len(outcomes),
            [True] * len(outcomes),
        )
        safe_substituted_b = run_maintenance_trajectory(
            state,
            safe_outcomes,
            safe_configurations,
            actions,
            masks,
            lesions=("masked_to_safe_substitution",),
        )
        common = simulate_six_arms(
            seed, state, lesions=("candidate_common_outcome",)
        )
        fixed_root = simulate_six_arms(
            seed, state, lesions=("root_coupling",)
        )
        equalized = simulate_six_arms(
            seed, state, lesions=("structure_comparison",)
        )

        permuted_actions = [
            {"engage": "avoid", "avoid": "sham", "sham": "engage"}[action]
            for action in actions
        ]
        original_labels = run_maintenance_trajectory(
            state, outcomes, configurations, actions, masks
        )
        permuted_labels = run_maintenance_trajectory(
            state, outcomes, configurations, permuted_actions, masks
        )
        permutation_errors.append(
            _scientific_trajectory_error(original_labels, permuted_labels)
        )

        collapsed_configurations = [
            {**configuration, "broadcast": "collapsed"}
            for configuration in configurations
        ]
        unlocalized_outcomes = [
            (outcome[0], outcome[1], 2) for outcome in outcomes
        ]
        broadcast_a = run_maintenance_trajectory(
            state,
            unlocalized_outcomes,
            collapsed_configurations,
            ["engage"] * len(outcomes),
            [True] * len(outcomes),
        )
        broadcast_b = run_maintenance_trajectory(
            state,
            unlocalized_outcomes,
            collapsed_configurations,
            actions,
            masks,
        )
        for detail in broadcast_a.contributions:
            decomposition = detail["decomposition"]
            for numerator, denominator in (("P", "T"), ("P", "D")):
                localization_errors.append(
                    abs(
                        float(decomposition[numerator]["localization"])
                        - float(decomposition[denominator]["localization"])
                    )
                )

        def contrast(
            trajectories: dict[str, Trajectory], pair: str
        ) -> float:
            left, right = ("P", "T") if pair == "PT" else ("P", "D")
            del left, right
            a = trajectory_readout(trajectories["A_response_prevention"])
            b = trajectory_readout(
                trajectories["B_closed_loop_censoring"]
            )
            return b[f"delta_L_{pair}"] - a[f"delta_L_{pair}"]

        common_a = trajectory_readout(common["A_response_prevention"])
        equalized_a = trajectory_readout(
            equalized["A_response_prevention"]
        )
        substituted_a = trajectory_readout(safe_a)
        substituted_b = trajectory_readout(safe_substituted_b)
        fixed_a = trajectory_readout(fixed_root["A_response_prevention"])
        fixed_b = trajectory_readout(
            fixed_root["B_closed_loop_censoring"]
        )
        broadcast_a_readout = trajectory_readout(broadcast_a)
        broadcast_b_readout = trajectory_readout(broadcast_b)
        custody_errors.extend(
            [
                abs(
                    trajectory_readout(
                        common["B_closed_loop_censoring"]
                    )["delivered_count"]
                    - intact_b["delivered_count"]
                ),
                abs(
                    trajectory_readout(
                        equalized["B_closed_loop_censoring"]
                    )["censored_count"]
                    - intact_b["censored_count"]
                ),
            ]
        )
        rows.append(
            {
                "seed": seed,
                "stratum": stratum,
                "intact_M_PT": (
                    intact_b["delta_L_PT"] - intact_a["delta_L_PT"]
                ),
                "intact_M_PD": (
                    intact_b["delta_L_PD"] - intact_a["delta_L_PD"]
                ),
                "action_mask_M_PT": contrast(action_mask, "PT"),
                "action_mask_M_PD": contrast(action_mask, "PD"),
                "forced_open_M_PT": contrast(forced, "PT"),
                "forced_open_M_PD": contrast(forced, "PD"),
                "substitution_M_PT": (
                    substituted_b["delta_L_PT"]
                    - substituted_a["delta_L_PT"]
                ),
                "substitution_M_PD": (
                    substituted_b["delta_L_PD"]
                    - substituted_a["delta_L_PD"]
                ),
                "common_A_delta_L_PT": common_a["delta_L_PT"],
                "common_A_delta_L_PD": common_a["delta_L_PD"],
                "common_M_PT": contrast(common, "PT"),
                "common_M_PD": contrast(common, "PD"),
                "fixed_root_difference": (
                    abs(fixed_a["root_revision"])
                    - abs(fixed_b["root_revision"])
                ),
                "fixed_transfer_difference": (
                    abs(fixed_a["untreated_cue_transfer"])
                    - abs(fixed_b["untreated_cue_transfer"])
                ),
                "fixed_M_PT": (
                    fixed_b["delta_L_PT"] - fixed_a["delta_L_PT"]
                ),
                "fixed_M_PD": (
                    fixed_b["delta_L_PD"] - fixed_a["delta_L_PD"]
                ),
                "broadcast_M_PT": (
                    broadcast_b_readout["delta_L_PT"]
                    - broadcast_a_readout["delta_L_PT"]
                ),
                "broadcast_M_PD": (
                    broadcast_b_readout["delta_L_PD"]
                    - broadcast_a_readout["delta_L_PD"]
                ),
                "equalized_A_delta_L_PT": equalized_a["delta_L_PT"],
                "equalized_A_delta_L_PD": equalized_a["delta_L_PD"],
                "equalized_M_PT": contrast(equalized, "PT"),
                "equalized_M_PD": contrast(equalized, "PD"),
            }
        )

    intervals = {
        field: _stratified_bootstrap_interval(
            rows, field, component=f"v233-gate4-{field}"
        )
        for field in (
            "intact_M_PT",
            "intact_M_PD",
            "substitution_M_PT",
            "substitution_M_PD",
            "fixed_M_PT",
            "fixed_M_PD",
            "broadcast_M_PT",
            "broadcast_M_PD",
        )
    }
    exact_max = lambda *fields: max(
        abs(float(row[field])) for row in rows for field in fields
    )
    lesions = {
        "action_to_mask_contingency_removed": {
            "maximum_target_error": exact_max(
                "action_mask_M_PT", "action_mask_M_PD"
            ),
            "safe_erosion_survives": bool(
                np.mean([row["intact_M_PT"] for row in rows]) > 0
            ),
            "passed": exact_max(
                "action_mask_M_PT", "action_mask_M_PD"
            )
            <= TOLERANCE,
        },
        "forced_open_channel": {
            "maximum_target_error": exact_max(
                "forced_open_M_PT", "forced_open_M_PD"
            ),
            "safe_erosion_survives": True,
            "passed": exact_max(
                "forced_open_M_PT", "forced_open_M_PD"
            )
            <= TOLERANCE,
        },
        "action_label_permutation": {
            "maximum_scientific_error": max(permutation_errors),
            "passed": max(permutation_errors) <= TOLERANCE,
        },
        "masked_to_safe_substitution": {
            "M_PT_95_interval": intervals["substitution_M_PT"],
            "M_PD_95_interval": intervals["substitution_M_PD"],
            "passed": (
                intervals["substitution_M_PT"][1] <= 0
                <= intervals["substitution_M_PT"][2]
                and intervals["substitution_M_PD"][1] <= 0
                <= intervals["substitution_M_PD"][2]
            ),
        },
        "candidate_common_outcome_likelihood": {
            "maximum_target_error": exact_max(
                "common_A_delta_L_PT",
                "common_A_delta_L_PD",
                "common_M_PT",
                "common_M_PD",
            ),
            "maximum_custody_error": max(custody_errors),
            "passed": (
                exact_max(
                    "common_A_delta_L_PT",
                    "common_A_delta_L_PD",
                    "common_M_PT",
                    "common_M_PD",
                )
                <= TOLERANCE
                and max(custody_errors) == 0
            ),
        },
        "root_coupling_fixed_removed": {
            "maximum_root_or_transfer_contrast": exact_max(
                "fixed_root_difference", "fixed_transfer_difference"
            ),
            "M_PT_95_interval": intervals["fixed_M_PT"],
            "M_PD_95_interval": intervals["fixed_M_PD"],
            "passed": (
                exact_max(
                    "fixed_root_difference", "fixed_transfer_difference"
                )
                <= TOLERANCE
                and intervals["fixed_M_PT"][1] > 0
                and intervals["fixed_M_PD"][1] > 0
            ),
        },
        "global_broadcast_severed": {
            "maximum_localization_log_BF": max(
                localization_errors, default=0.0
            ),
            "M_PT_95_interval": intervals["broadcast_M_PT"],
            "M_PD_95_interval": intervals["broadcast_M_PD"],
            "passed": (
                max(localization_errors, default=0.0) <= TOLERANCE
                and intervals["broadcast_M_PT"][1] > 0
                and intervals["broadcast_M_PD"][1] > 0
            ),
        },
        "structure_comparison_equalized": {
            "maximum_target_error": exact_max(
                "equalized_A_delta_L_PT",
                "equalized_A_delta_L_PD",
                "equalized_M_PT",
                "equalized_M_PD",
            ),
            "maximum_custody_error": max(custody_errors),
            "passed": (
                exact_max(
                    "equalized_A_delta_L_PT",
                    "equalized_A_delta_L_PD",
                    "equalized_M_PT",
                    "equalized_M_PD",
                )
                <= TOLERANCE
                and max(custody_errors) == 0
            ),
        },
    }
    return {
        "stage": "V2.3.3",
        "world_count": len(rows),
        "lesions": lesions,
        "rows": rows,
        "passed": all(bool(item["passed"]) for item in lesions.values()),
    }


def _perturbed_bank_state(
    bank_state: dict[str, Any],
    *,
    prior_multiplier: float = 1.0,
    cue_multiplier: float = 1.0,
) -> dict[str, Any]:
    state = copy.deepcopy(bank_state)
    posterior = np.asarray(state["q_H_formation"], dtype=float)
    posterior[2] *= prior_multiplier
    posterior /= posterior.sum()
    state["q_H_formation"] = posterior.tolist()
    association = float(state["cue_root_associations"]["untreated"])
    association = min(
        1.0,
        max(0.5, 0.5 + (association - 0.5) * cue_multiplier),
    )
    state["cue_root_associations"]["untreated"] = association
    return state


def _robustness_cell(
    selected: list[tuple[str, dict[str, Any]]],
    *,
    name: str,
    multiplier: float,
    duration_multiplier: float = 1.0,
    reliability_multiplier: float = 1.0,
    censoring_multiplier: float = 1.0,
    action_cost_multiplier: float = 1.0,
    temperature_multiplier: float = 1.0,
    adverse_multiplier: float = 1.0,
    prior_multiplier: float = 1.0,
    precision_multiplier: float = 1.0,
    cue_multiplier: float = 1.0,
) -> dict[str, Any]:
    base = PARAMETERS["maintenance"]
    duration = max(1, int(round(float(base["duration"]) * duration_multiplier)))
    reliability = min(
        1.0,
        max(0.0, float(base["safe_outcome_reliability"]) * reliability_multiplier),
    )
    adverse = min(
        1.0,
        max(
            0.0,
            (
                1.0 - reliability
                if reliability_multiplier != 1.0
                else float(base["adverse_outcome_proportion"])
                * adverse_multiplier
            ),
        ),
    )
    censoring = min(
        1.0,
        max(
            0.0,
            float(base["closed_loop_censoring_probability"])
            * censoring_multiplier,
        ),
    )
    action_cost = (
        float(base["policy"]["action_cost"]) * action_cost_multiplier
    )
    temperature = max(
        1e-6, float(base["policy"]["temperature"]) * temperature_multiplier
    )
    rows = []
    posterior_errors = []
    sum_errors = []
    paired_rng_errors = []
    one_posterior_failures = []
    failed_worlds = []
    for offset, (stratum, record) in enumerate(selected):
        seed = int(PARAMETERS["maintenance"]["robustness_seed_block"][0]) + offset
        state = _perturbed_bank_state(
            record["serialized_state"],
            prior_multiplier=prior_multiplier,
            cue_multiplier=cue_multiplier,
        )
        outcomes, configurations = corrective_stream(
            seed, duration, adverse_proportion=adverse
        )
        if precision_multiplier < 1.0:
            configurations = [
                {**configuration, "precision": "ordinary"}
                for configuration in configurations
            ]
        elif precision_multiplier > 1.0:
            configurations = [
                {**configuration, "precision": "overwhelm"}
                for configuration in configurations
            ]
        actions, availability, _ = _closed_loop_actions_and_masks(
            seed,
            state,
            duration,
            censoring_probability=censoring,
            action_cost=action_cost,
            temperature=temperature,
        )
        actions_repeat, availability_repeat, _ = (
            _closed_loop_actions_and_masks(
                seed,
                state,
                duration,
                censoring_probability=censoring,
                action_cost=action_cost,
                temperature=temperature,
            )
        )
        paired_rng_errors.append(
            int(
                actions != actions_repeat
                or availability != availability_repeat
            )
        )
        full = run_maintenance_trajectory(
            state,
            outcomes,
            configurations,
            ["engage"] * duration,
            [True] * duration,
        )
        closed = run_maintenance_trajectory(
            state,
            outcomes,
            configurations,
            actions,
            availability,
        )
        full_readout = trajectory_readout(full)
        closed_readout = trajectory_readout(closed)
        identity_errors = _mechanistic_identity_errors(closed)
        sum_errors.extend(identity_errors)
        oracle_posterior, _ = independent_history_sum(
            np.asarray(state["q_H_formation"], dtype=float),
            outcomes,
            configurations,
            masks=[not value for value in availability],
        )
        posterior_errors.append(
            float(np.max(np.abs(closed.final_h - oracle_posterior)))
        )
        for protocol_state in closed.states:
            try:
                audit_one_posterior(protocol_state)
            except AssertionError:
                one_posterior_failures.append(seed)
        row = {
            "seed": seed,
            "bank_seed": int(record["seed"]),
            "stratum": stratum,
            "q0_P": float(state["q_H_formation"][2]),
            "A_delta_L_PT": full_readout["delta_L_PT"],
            "A_delta_L_PD": full_readout["delta_L_PD"],
            "M_PT": (
                closed_readout["delta_L_PT"]
                - full_readout["delta_L_PT"]
            ),
            "M_PD": (
                closed_readout["delta_L_PD"]
                - full_readout["delta_L_PD"]
            ),
            "delivered": closed_readout["delivered_count"],
            "censored": closed_readout["censored_count"],
            "maximum_sum_error": max(identity_errors),
        }
        rows.append(row)
        if (
            row["A_delta_L_PT"] >= 0
            or row["A_delta_L_PD"] >= 0
            or row["M_PT"] < -TOLERANCE
            or row["M_PD"] < -TOLERANCE
            or max(identity_errors) > TOLERANCE
        ):
            failed_worlds.append(
                {
                    **row,
                    "BF_decomposition": list(closed.contributions),
                }
            )
    metrics = {
        key: float(np.mean([row[key] for row in rows]))
        for key in ("A_delta_L_PT", "A_delta_L_PD", "M_PT", "M_PD")
    }
    checks = {
        "safe_erosion_signs": (
            metrics["A_delta_L_PT"] < 0
            and metrics["A_delta_L_PD"] < 0
        ),
        "maintenance_signs": (
            metrics["M_PT"] >= -TOLERANCE
            and metrics["M_PD"] >= -TOLERANCE
        ),
        "one_posterior": not one_posterior_failures,
        "independent_recomputation": max(posterior_errors) <= TOLERANCE,
        "paired_RNG": max(paired_rng_errors) == 0,
        "delivered_BF_sum": max(sum_errors) <= TOLERANCE,
    }
    return {
        "dimension": name,
        "multiplier": multiplier,
        "settings": {
            "duration": duration,
            "safe_outcome_reliability": reliability,
            "adverse_outcome_proportion": adverse,
            "censoring_probability": censoring,
            "action_cost": action_cost,
            "policy_temperature": temperature,
            "candidate_prior_multiplier": prior_multiplier,
            "precision_regime": (
                "ordinary"
                if precision_multiplier < 1.0
                else (
                    "overwhelm"
                    if precision_multiplier > 1.0
                    else "frozen_ordinary"
                )
            ),
            "cue_root_multiplier": cue_multiplier,
        },
        "world_count": len(rows),
        "metrics": metrics,
        "maximum_independent_posterior_error": max(posterior_errors),
        "maximum_delivered_BF_sum_error": max(sum_errors),
        "paired_RNG_error_count": sum(paired_rng_errors),
        "one_posterior_failures": one_posterior_failures,
        "checks": checks,
        "failed_worlds": failed_worlds,
        "passed": all(bool(value) for value in checks.values()),
    }


def robustness_assays(bank: dict[str, Any]) -> dict[str, Any]:
    """Execute all frozen one-at-a-time and joint-neighborhood sweeps."""
    selected = [
        (stratum, record)
        for stratum in ("moderate", "strong", "very_strong")
        for record in bank["selected"][stratum][:4]
    ]
    sweep_arguments = {
        "duration": "duration_multiplier",
        "safe_outcome_reliability": "reliability_multiplier",
        "censoring_probability": "censoring_multiplier",
        "action_cost": "action_cost_multiplier",
        "policy_temperature": "temperature_multiplier",
        "adverse_outcome_proportion": "adverse_multiplier",
        "candidate_prior": "prior_multiplier",
        "precision": "precision_multiplier",
        "cue_root_strength": "cue_multiplier",
    }
    cells = [
        _robustness_cell(
            [
                (stratum, record)
                for record in bank["selected"][stratum][:4]
            ],
            name="initial_strength_stratum",
            multiplier=float(index),
        )
        for index, stratum in enumerate(
            ("moderate", "strong", "very_strong"), start=1
        )
    ]
    for dimension, argument in sweep_arguments.items():
        for multiplier in PARAMETERS["robustness_sweep_multipliers"][
            dimension
        ]:
            cells.append(
                _robustness_cell(
                    selected,
                    name=dimension,
                    multiplier=float(multiplier),
                    **{argument: float(multiplier)},
                )
            )
    for multiplier in (0.8, 1.2):
        cells.append(
            _robustness_cell(
                selected,
                name="joint_neighborhood",
                multiplier=multiplier,
                duration_multiplier=multiplier,
                reliability_multiplier=multiplier,
                censoring_multiplier=multiplier,
                action_cost_multiplier=multiplier,
                temperature_multiplier=multiplier,
                adverse_multiplier=multiplier,
                prior_multiplier=multiplier,
                precision_multiplier=multiplier,
                cue_multiplier=multiplier,
            )
        )
    forbidden = forbidden_path_audit()
    constitution = cumulative_graded_update_audit()
    stress = publish_stratified_update_distribution()
    failed = [
        {
            "dimension": cell["dimension"],
            "multiplier": cell["multiplier"],
            "worlds": cell["failed_worlds"],
        }
        for cell in cells
        if cell["failed_worlds"]
    ]
    q0_values = np.asarray(
        [
            row["serialized_state"]["q_H_formation"][2]
            for stratum in ("moderate", "strong", "very_strong")
            for row in bank["selected"][stratum]
        ],
        dtype=float,
    )
    base_rows = open_assays(bank)["rows"]
    q0_slopes = {
        field: float(
            np.polyfit(
                q0_values,
                np.asarray([row[field] for row in base_rows], dtype=float),
                1,
            )[0]
        )
        for field in ("M_PT", "M_PD")
    }
    return {
        "stage": "V2.3.3",
        "sweep_worlds_per_cell": len(selected),
        "cells": cells,
        "continuous_q0_slopes": q0_slopes,
        "failed_world_decompositions": failed,
        "forbidden_path_audit": forbidden,
        "revised_graded_update_constitution": constitution,
        "stratified_empirical_update_distribution": stress,
        "stress_artifact_is_criterial": False,
        "passed": (
            all(cell["passed"] for cell in cells)
            and forbidden["passed"]
            and constitution["passed"]
        ),
    }
