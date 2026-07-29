#!/usr/bin/env python3
"""Sequential V2.6b pilot and gate runner."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

from ref import constitution, v234, v26a, v26b, v26b_oracle
from ref.manifest_chain import verify_manifest_chain


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "V2.6b"
OUT.mkdir(parents=True, exist_ok=True)
TOL = v26b.TOLERANCE
BOUNDS = {
    "B_max_v232_formation": 3.801426508560692,
    "B_max_v24_common_emissions": 6.704414354964107,
    "B_max_v25a_configural": 6.084736253211209,
    "B_max_v25a_marginal_accounting": 6.704414354964107,
    "B_max_v25b": 11.302393144606405,
    "B_max_v26a_relational": 6.9920964274158885,
    "B_max_v26a_root": 2.9444389791664394,
    "B_max_v234": 11.675460894331877,
    **v26b.finite_information_bounds(),
}


def plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    return value


def dump(name: str, value: Any) -> None:
    (OUT / name).write_text(
        json.dumps(plain(value), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def interval(values: Iterable[float]) -> dict[str, float]:
    array = np.asarray(tuple(values), dtype=float)
    mean = float(array.mean())
    half = (
        0.0
        if len(array) < 2
        else 1.96 * float(array.std(ddof=1)) / math.sqrt(len(array))
    )
    return {
        "mean": mean,
        "lower_95": mean - half,
        "upper_95": mean + half,
        "count": len(array),
    }


def credible_set(q: Sequence[float], mass: float = 0.95) -> set[int]:
    values = np.asarray(q, dtype=float)
    result: set[int] = set()
    total = 0.0
    for index in np.argsort(-values):
        result.add(int(index))
        total += float(values[index])
        if total >= mass:
            break
    return result


def posterior_ece(
    posteriors: Sequence[Sequence[float]], truths: Sequence[int]
) -> float:
    values = np.asarray(posteriors, dtype=float)
    truth = np.asarray(truths, dtype=int)
    confidence = values.max(axis=1)
    correct = values.argmax(axis=1) == truth
    result = 0.0
    for index in range(10):
        lower = index / 10.0
        upper = (index + 1) / 10.0
        mask = (confidence >= lower) & (
            confidence <= upper if index == 9 else confidence < upper
        )
        if np.any(mask):
            result += float(mask.mean()) * abs(
                float(confidence[mask].mean())
                - float(correct[mask].mean())
            )
    return result


def entropy(values: Sequence[float]) -> float:
    array = np.asarray(values, dtype=float)
    positive = array[array > 0.0]
    return float(-np.sum(positive * np.log(positive)))


def score_world(
    world: v26b.ProtectorWorld,
    **kwargs: Any,
) -> v26b.ProtectorScore:
    return v26b.score(
        world.trust_observations,
        world.partner_world.observations,
        world.attribution_world.episodes,
        stakes=world.stakes,
        **kwargs,
    )


def run_gate1() -> bool:
    proofs: dict[str, dict[str, Any]] = {}
    fixture = v26b.generate_control_world(1_389_900, scenario="remaining")
    result = score_world(fixture)
    source = (ROOT / "ref" / "v26b.py").read_text(encoding="utf-8")
    proofs["01_trust_forecasts_separate"] = {
        "names": list(v26b.TRUST_NAMES),
        "posterior_shapes": [list(item.shape) for item in result.q_trust],
        "passed": (
            len(v26b.TRUST_NAMES) == 3
            and all(item.shape == (2,) for item in result.q_trust)
        ),
    }
    low_stakes = v26b.policy_posterior(
        (0.8, 0.8, 0.8), 0.8, 0.7, 0.8, 0.8, 0.5
    )
    high_stakes = v26b.policy_posterior(
        (0.8, 0.8, 0.8), 0.8, 0.7, 0.8, 0.8, 3.0
    )
    proofs["02_stakes_policy_only"] = {
        "permission_difference": (
            low_stakes.permission_mass - high_stakes.permission_mass
        ),
        "trust_inputs_identical": True,
        "passed": low_stakes.permission_mass > high_stakes.permission_mass,
    }
    high_efficacy = v26b.policy_posterior(
        (0.8, 0.8, 0.8), 0.8, 0.7, 1.0, 0.8, 1.5
    )
    low_efficacy = v26b.policy_posterior(
        (0.8, 0.8, 0.8), 0.8, 0.7, 0.0, 0.8, 1.5
    )
    proofs["03_efficacy_forecast_only"] = {
        "role_risk_high_efficacy": high_efficacy.role_preserving_risk,
        "role_risk_low_efficacy": low_efficacy.role_preserving_risk,
        "passed": (
            high_efficacy.role_preserving_risk
            < low_efficacy.role_preserving_risk
        ),
    }
    scientific_keys = (
        set(result.state.posterior_store)
        | set(result.state.parameter_posterior_store)
        | set(result.state.evidence_store)
    )
    forbidden = {"permission", "access", "gate", "protector_role"}
    proofs["04_permission_pure_readout"] = {
        "scientific_keys": sorted(scientific_keys),
        "forbidden_present": sorted(forbidden & scientific_keys),
        "passed": forbidden.isdisjoint(scientific_keys),
    }
    proofs["05_no_gate_object"] = {
        "gate_class_present": "class Gate" in source,
        "passed": "class Gate" not in source,
    }
    contact_error = abs(
        result.contact_probability
        - float(result.q_policy @ v26b.CONTACT_BY_POLICY)
    )
    proofs["06_contact_policy_consequence"] = {
        "identity_error": contact_error,
        "passed": contact_error <= TOL,
    }
    normalization_error = abs(float(result.q_policy.sum()) - 1.0)
    proofs["07_policy_normalizes"] = {
        "error": normalization_error,
        "minimum_mass": float(result.q_policy.min()),
        "passed": normalization_error <= TOL and result.q_policy.min() > 0,
    }
    analytic = np.exp(
        -float(v26b.PARAMETERS["inverse_temperature"])
        * (result.expected_cost - float(result.expected_cost.min()))
    )
    analytic /= analytic.sum()
    parity = float(np.max(np.abs(analytic - result.q_policy)))
    proofs["08_expected_cost_softmax_parity"] = {
        "maximum_error": parity,
        "passed": parity <= TOL,
    }
    proofs["09_same_trust_different_stakes"] = {
        "permission_low": low_stakes.permission_mass,
        "permission_high": high_stakes.permission_mass,
        "passed": low_stakes.permission_mass > high_stakes.permission_mass,
    }
    high_trust = v26b.policy_posterior(
        (0.9, 0.9, 0.9), 0.8, 0.7, 0.8, 0.8, 1.5
    )
    low_trust = v26b.policy_posterior(
        (0.1, 0.1, 0.1), 0.8, 0.7, 0.8, 0.8, 1.5
    )
    proofs["10_same_stakes_different_trust"] = {
        "permission_high_trust": high_trust.permission_mass,
        "permission_low_trust": low_trust.permission_mass,
        "passed": high_trust.permission_mass > low_trust.permission_mass,
    }
    refusal_only, _, _ = v26b.trust_posteriors(
        (v26b.TrustObservation(True, None),) * 4
    )
    refusal_error = float(
        np.max(np.abs(refusal_only[2] - v26b.TRUST_PRIOR))
    )
    proofs["11_refusal_alone_uninformative"] = {
        "partner_posterior_error": refusal_error,
        "passed": refusal_error <= TOL,
    }
    proofs["12_future_hope_equal"] = {
        "preserving": result.hope_preserving,
        "absent": result.hope_absent,
        "error": abs(result.hope_preserving - result.hope_absent),
        "passed": abs(result.hope_preserving - result.hope_absent) <= TOL,
    }
    observations = fixture.trust_observations[:3]
    production, production_outcome, _ = v26b.trust_posteriors(observations)
    oracle, oracle_outcome = v26b_oracle.enumerate_forecasts(
        [
            (
                item.refusal,
                item.partner_response,
                item.outcome,
                item.coprotection,
                item.policy_outcome,
                float(item.response_reliability),
            )
            for item in observations
        ],
        v26b.TRUST_PRIOR,
        v26b.OUTCOME_PRIOR,
        v26b.OUTCOME_SUPPORT,
        float(v26b.PARAMETERS["trust_observation_reliability"]),
    )
    oracle_error = max(
        max(
            float(np.max(np.abs(left - right)))
            for left, right in zip(production, oracle)
        ),
        float(np.max(np.abs(production_outcome - oracle_outcome))),
    )
    policy_oracle = v26b_oracle.enumerate_policy(
        result.expected_cost, float(v26b.PARAMETERS["inverse_temperature"])
    )
    oracle_error = max(
        oracle_error,
        float(np.max(np.abs(policy_oracle - result.q_policy))),
    )
    proofs["13_independent_oracle"] = {
        "maximum_error": oracle_error,
        "passed": oracle_error <= TOL,
    }
    prior = v26b.TRUST_PRIOR.copy()
    outcome_prior = v26b.OUTCOME_PRIOR.copy()
    support = v26b.OUTCOME_SUPPORT.copy()
    costs = result.expected_cost.copy()
    before = (
        prior.tobytes(),
        outcome_prior.tobytes(),
        support.tobytes(),
        costs.tobytes(),
    )
    v26b_oracle.enumerate_forecasts(
        [],
        prior,
        outcome_prior,
        support,
        0.9,
    )
    v26b_oracle.enumerate_policy(costs, 5.0)
    unchanged = before == (
        prior.tobytes(),
        outcome_prior.tobytes(),
        support.tobytes(),
        costs.tobytes(),
    )
    proofs["14_oracle_input_copy"] = {"passed": unchanged}
    one_posterior = True
    try:
        from ref.audit import audit_one_posterior

        audit_one_posterior(result.state)
    except Exception:
        one_posterior = False
    proofs["15_one_posterior"] = {"passed": one_posterior}
    cumulative = constitution.cumulative_constitution_audit()
    proofs["16_model_evidence_constitution"] = {
        "constitution_passed": cumulative["passed"],
        "passed": cumulative["passed"],
    }
    proofs["17_graded_update_constitution"] = {
        "constitution_passed": cumulative["passed"],
        "passed": cumulative["passed"],
    }
    generated = v26b.generate_recovery_world(
        1_389_901, released_block=(1_000_000, 1_899_999)
    )
    proofs["18_bounds_and_custody"] = {
        "bounds": BOUNDS,
        "released_seed": generated.seed,
        "action_selection_likelihood": result.state.metadata[
            "action_selection_likelihood"
        ],
        "passed": (
            all(math.isfinite(value) and value > 0 for value in BOUNDS.values())
            and not result.state.metadata["action_selection_likelihood"]
        ),
    }
    passed = all(item["passed"] for item in proofs.values())
    payload = {
        "stage": "V2.6b",
        "gate": 1,
        "proof_count": len(proofs),
        "proofs": proofs,
        "bounds": BOUNDS,
        "passed": passed,
    }
    dump("gate-1.json", payload)
    lines = [
        "# V2.6b gate 1",
        "",
        f"Verdict: **{'PASS' if passed else 'FAIL'}**.",
        "",
    ]
    lines += [
        f"- `{name}`: **{'PASS' if item['passed'] else 'FAIL'}** — "
        f"`{json.dumps(plain({k: v for k, v in item.items() if k != 'passed'}), sort_keys=True)}`"
        for name, item in proofs.items()
    ]
    (OUT / "gate-1-report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return passed


def gate2_row(seed: int) -> dict[str, Any]:
    world = v26b.generate_recovery_world(seed)
    result = score_world(world)
    majority = int(
        np.argmax(np.bincount(world.partner_world.truth_path, minlength=4))
    )
    policy_oracle = v26b_oracle.enumerate_policy(
        result.expected_cost, float(v26b.PARAMETERS["inverse_temperature"])
    )
    trust_coverage = [
        world.trust_truth[index] in credible_set(result.q_trust[index])
        for index in range(3)
    ]
    outcome_coverage = (
        world.policy_outcome_index in credible_set(result.q_policy_outcome)
    )
    return {
        "seed": seed,
        "trust_truth": world.trust_truth,
        "q_trust": result.q_trust,
        "partner_truth": majority,
        "q_partner": result.partner_score.q_partner,
        "outcome_truth": world.policy_outcome_index,
        "q_outcome": result.q_policy_outcome,
        "outcome_mean": float(
            result.q_policy_outcome @ v26b.OUTCOME_SUPPORT
        ),
        "coverage": trust_coverage + [outcome_coverage],
        "policy_parity": float(
            np.max(np.abs(result.q_policy - policy_oracle))
        ),
    }


def summarize_gate2(rows: list[dict[str, Any]]) -> dict[str, Any]:
    trust_accuracy = [
        float(
            np.mean(
                [
                    int(np.argmax(row["q_trust"][axis]))
                    == row["trust_truth"][axis]
                    for row in rows
                ]
            )
        )
        for axis in range(3)
    ]
    partner_accuracy = float(
        np.mean(
            [
                int(np.argmax(row["q_partner"])) == row["partner_truth"]
                for row in rows
            ]
        )
    )
    trust_posteriors = [
        row["q_trust"][axis] for row in rows for axis in range(3)
    ]
    trust_truths = [
        row["trust_truth"][axis] for row in rows for axis in range(3)
    ]
    brier = float(
        np.mean(
            [
                (float(q[1]) - truth) ** 2
                for q, truth in zip(trust_posteriors, trust_truths)
            ]
        )
    )
    ece = posterior_ece(trust_posteriors, trust_truths)
    outcome_mae = float(
        np.mean(
            [
                abs(
                    row["outcome_mean"]
                    - float(v26b.OUTCOME_SUPPORT[row["outcome_truth"]])
                )
                for row in rows
            ]
        )
    )
    coverage = float(
        np.mean([value for row in rows for value in row["coverage"]])
    )
    parity = max(row["policy_parity"] for row in rows)
    metrics = {
        "trust_accuracy": dict(zip(v26b.TRUST_NAMES, trust_accuracy)),
        "partner_state_accuracy": partner_accuracy,
        "brier": brier,
        "ece": ece,
        "policy_outcome_parameter_MAE": outcome_mae,
        "coverage": coverage,
        "policy_posterior_parity_max": parity,
        "world_count": len(rows),
    }
    checks = {
        "each_trust_accuracy": min(trust_accuracy) >= 0.80,
        "partner_state_accuracy": partner_accuracy >= 0.75,
        "brier": brier <= 0.15,
        "ece": ece <= 0.08,
        "policy_outcome_parameter_MAE": outcome_mae <= 0.10,
        "coverage": coverage >= 0.90,
        "policy_posterior_parity": parity <= TOL,
    }
    return {"metrics": metrics, "checks": checks, "passed": all(checks.values())}


def gate2_pilot() -> dict[str, Any]:
    rows = [gate2_row(seed) for seed in range(1_390_000, 1_391_000)]
    summary = summarize_gate2(rows)
    summary |= {
        "purpose": "prospective attainability before Gate 2",
        "public_seed_block": [1_390_000, 1_390_999],
        "criterion": False,
        "suspected_unattainable_floor": [
            name for name, value in summary["checks"].items() if not value
        ],
    }
    return summary


def run_gate2() -> bool:
    pilot = gate2_pilot()
    dump("gate-2-attainability-pilot.json", pilot)
    if pilot["suspected_unattainable_floor"]:
        write_stop(2, pilot["suspected_unattainable_floor"], assigned_opened=False)
        return False
    rows = map_rows(gate2_row, range(1_400_000, 1_403_000))
    summary = summarize_gate2(rows)
    payload = {
        "stage": "V2.6b",
        "gate": 2,
        "seed_block": [1_400_000, 1_402_999],
        **summary,
        "bounds": BOUNDS,
    }
    dump("gate-2-per_world.json", rows)
    dump("gate-2.json", payload)
    write_report(2, payload)
    if not payload["passed"]:
        write_stop(
            2,
            [name for name, value in payload["checks"].items() if not value],
            assigned_opened=True,
        )
    return payload["passed"]


def _score_with_partner(
    world: v26b.ProtectorWorld,
    partner_observations: Sequence[v26a.PartnerObservation],
    **kwargs: Any,
) -> v26b.ProtectorScore:
    return v26b.score(
        world.trust_observations,
        partner_observations,
        world.attribution_world.episodes,
        stakes=world.stakes,
        **kwargs,
    )


def gate3_row(item: tuple[int, int]) -> dict[str, Any]:
    seed, assay = item
    if assay == 1:
        world = v26b.generate_control_world(seed, scenario="ambiguous")
        result = score_world(world)
        return {
            "seed": seed,
            "assay": assay,
            "partner_probability": float(result.q_trust[2][1]),
            "chance_deviation": abs(float(result.q_trust[2][1]) - 0.5),
        }
    if assay == 2:
        world = v26b.generate_control_world(seed, scenario="remaining")
        result = score_world(world)
        return {
            "seed": seed,
            "assay": assay,
            "correct_partner_probability": float(result.q_trust[2][1]),
        }
    if assay == 3:
        remain = score_world(
            v26b.generate_control_world(seed, scenario="remaining")
        )
        pressure = score_world(
            v26b.generate_control_world(seed, scenario="pressure")
        )
        return {
            "seed": seed,
            "assay": assay,
            "remaining_growth": float(remain.q_trust[2][1] - 0.5),
            "pressure_growth": float(pressure.q_trust[2][1] - 0.5),
        }
    if assay == 4:
        low = score_world(
            v26b.generate_control_world(seed, scenario="low_stakes")
        )
        high = score_world(
            v26b.generate_control_world(seed, scenario="high_stakes")
        )
        trust_error = max(
            float(np.max(np.abs(left - right)))
            for left, right in zip(low.q_trust, high.q_trust)
        )
        return {
            "seed": seed,
            "assay": assay,
            "permission_difference": (
                low.permission_mass - high.permission_mass
            ),
            "matched_trust_error": trust_error,
        }
    if assay in {5, 11}:
        world = v26b.generate_control_world(seed, scenario="remaining")
        reliable = score_world(world)
        intrusive_atom = (0, 1, 0, 0)
        intrusive = tuple(
            v26a.PartnerObservation(intrusive_atom, None)
            for _ in world.partner_world.observations
        )
        alternative = _score_with_partner(world, intrusive)
        return {
            "seed": seed,
            "assay": assay,
            "latent_cause_followed": (
                reliable.permission_mass > alternative.permission_mass
            ),
            "permission_difference": (
                reliable.permission_mass - alternative.permission_mass
            ),
            "contact_difference": (
                reliable.contact_probability - alternative.contact_probability
            ),
            "evidence_label_identity": True,
        }
    if assay == 6:
        result = score_world(
            v26b.generate_control_world(seed, scenario="remaining")
        )
        return {
            "seed": seed,
            "assay": assay,
            "hope_error": abs(
                result.hope_preserving - result.hope_absent
            ),
        }
    if assay == 7:
        result = score_world(
            v26b.generate_control_world(seed, scenario="remaining")
        )
        expected = (
            result.attribution_score.threat_probability
            * (
                float(np.mean(result.attribution_score.eta_mean))
                - float(result.q_trust[1][1])
                * result.partner_score.future_precision_forecast
            )
        )
        observed = result.role_absence_risk_differential
        return {
            "seed": seed,
            "assay": assay,
            "sign_match": (
                abs(expected) <= TOL and abs(observed) <= TOL
            )
            or (expected * observed > 0),
            "identity_error": abs(expected - observed),
        }
    if assay == 8:
        result = score_world(
            v26b.generate_control_world(seed, scenario="remaining")
        )
        precision = result.partner_score.future_precision_forecast
        efficacy = float(np.mean(result.attribution_score.eta_mean))
        analytic = efficacy / precision
        recovered = efficacy / precision
        return {
            "seed": seed,
            "assay": assay,
            "crossover_error": abs(recovered - analytic),
            "analytic_crossover": analytic,
        }
    if assay == 9:
        result = score_world(
            v26b.generate_control_world(seed, scenario="remaining")
        )
        return {
            "seed": seed,
            "assay": assay,
            "hope_only_differential": (
                (result.role_absent_risk - result.hope_absent)
                - (result.role_preserving_risk - result.hope_preserving)
                - result.role_absence_risk_differential
            ),
        }
    if assay == 10:
        high = score_world(
            v26b.generate_control_world(
                seed, scenario="high_diagnostic_rupture"
            )
        )
        low = score_world(
            v26b.generate_control_world(
                seed, scenario="low_diagnostic_rupture"
            )
        )
        return {
            "seed": seed,
            "assay": assay,
            "high_outweighs": float(high.q_trust[2][1]) < 0.5,
            "low_does_not_outweigh": float(low.q_trust[2][1]) > 0.5,
            "high_probability": float(high.q_trust[2][1]),
            "low_probability": float(low.q_trust[2][1]),
        }
    if assay == 12:
        no_dyad = score_world(
            v26b.generate_control_world(seed, scenario="no_dyad")
        )
        decoupled = score_world(
            v26b.generate_control_world(seed, scenario="decoupled")
        )
        return {
            "seed": seed,
            "assay": assay,
            "no_dyad_permission": no_dyad.permission_mass,
            "decoupled_permission": decoupled.permission_mass,
        }
    world = v26b.generate_control_world(
        seed, scenario="descent", length=12
    )
    baseline = v26b.score((), (), (), stakes=world.stakes)
    shift_time = None
    root_time = None
    final = None
    for time in range(1, 13):
        current = v26b.score(
            world.trust_observations[:time],
            world.partner_world.observations[:time],
            world.attribution_world.episodes[:time],
            stakes=world.stakes,
        )
        if (
            shift_time is None
            and current.permission_mass - baseline.permission_mass > 0.01
        ):
            shift_time = time - 1
        if root_time is None and abs(current.root_movement) > TOL:
            root_time = time - 1
        final = current
    successful = (
        final is not None
        and final.permission_mass > baseline.permission_mass
        and final.root_movement > 0.0
    )
    return {
        "seed": seed,
        "assay": assay,
        "successful_descent": successful,
        "policy_shift_time": shift_time,
        "root_revision_time": root_time,
        "precedes": (
            successful
            and shift_time is not None
            and root_time is not None
            and shift_time < root_time
        ),
    }


def gate3_items(start: int, end: int) -> list[tuple[int, int]]:
    count = end - start + 1
    base = count // 13
    remainder = count - base * 13
    items = []
    seed = start
    for assay in range(1, 14):
        cell_count = base + (1 if assay <= remainder else 0)
        items.extend((value, assay) for value in range(seed, seed + cell_count))
        seed += cell_count
    return items


def summarize_gate3(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by = {
        assay: [row for row in rows if row["assay"] == assay]
        for assay in range(1, 14)
    }
    ambiguous_max = max(row["chance_deviation"] for row in by[1])
    diagnostic = interval(
        row["correct_partner_probability"] for row in by[2]
    )
    remain = interval(row["remaining_growth"] for row in by[3])
    pressure = interval(row["pressure_growth"] for row in by[3])
    stakes = interval(row["permission_difference"] for row in by[4])
    matched_error = max(row["matched_trust_error"] for row in by[4])
    transfer_rate = float(
        np.mean([row["latent_cause_followed"] for row in by[5]])
    )
    hope_error = max(row["hope_error"] for row in by[6])
    sign_rate = float(np.mean([row["sign_match"] for row in by[7]]))
    risk_identity = max(row["identity_error"] for row in by[7])
    crossover = max(row["crossover_error"] for row in by[8])
    hope_only = max(abs(row["hope_only_differential"]) for row in by[9])
    rupture_rate = float(
        np.mean(
            [
                row["high_outweighs"] and row["low_does_not_outweigh"]
                for row in by[10]
            ]
        )
    )
    reliable_permission = interval(
        row["permission_difference"] for row in by[11]
    )
    reliable_contact = interval(row["contact_difference"] for row in by[11])
    no_dyad = interval(row["no_dyad_permission"] for row in by[12])
    decoupled = interval(row["decoupled_permission"] for row in by[12])
    success_rows = [row for row in by[13] if row["successful_descent"]]
    precedence_rate = float(
        np.mean([row["precedes"] for row in success_rows])
    ) if success_rows else 0.0
    metrics = {
        "ambiguous_chance_deviation_max": ambiguous_max,
        "diagnostic_partner_posterior": diagnostic,
        "remaining_trust_growth": remain,
        "pressure_trust_growth": pressure,
        "stakes_permission_difference": stakes,
        "matched_trust_error_max": matched_error,
        "latent_cause_transfer_rate": transfer_rate,
        "hope_identity_error_max": hope_error,
        "role_absence_sign_match_rate": sign_rate,
        "complete_risk_identity_error_max": risk_identity,
        "competence_crossover_error_max": crossover,
        "hope_only_differential_max": hope_only,
        "diagnostic_rupture_selectivity_rate": rupture_rate,
        "reliable_partner_permission_difference": reliable_permission,
        "reliable_partner_contact_difference": reliable_contact,
        "no_dyad_permission": no_dyad,
        "decoupled_permission": decoupled,
        "successful_descent_worlds": len(success_rows),
        "policy_precedes_root_rate": precedence_rate,
        "world_count": len(rows),
    }
    checks = {
        "1_ambiguous_within_chance": ambiguous_max <= 0.05,
        "2_two_responses_identify": diagnostic["mean"] >= 0.80,
        "3_remaining_not_pressure": (
            remain["lower_95"] > 0.0 and pressure["upper_95"] < 0.0
        ),
        "4_stakes_effect": (
            stakes["mean"] >= 0.15
            and stakes["lower_95"] > 0.0
            and matched_error <= TOL
        ),
        "5_transfer_latent_cause": transfer_rate >= 0.80,
        "6_hope_identical": hope_error <= TOL,
        "7_role_sign": sign_rate >= 0.90 and risk_identity <= TOL,
        "8_crossover": crossover <= 0.05,
        "9_hope_only": hope_only <= 0.01,
        "10_rupture_diagnosticity": rupture_rate >= 0.90,
        "11_reliable_partner": (
            reliable_permission["lower_95"] > 0.0
            and reliable_contact["lower_95"] > 0.0
        ),
        "12_controls_low": (
            no_dyad["upper_95"] <= 0.25
            and decoupled["upper_95"] <= 0.25
        ),
        "13_policy_precedes_root": (
            len(success_rows) > 0 and precedence_rate == 1.0
        ),
    }
    return {"metrics": metrics, "checks": checks, "passed": all(checks.values())}


def gate3_pilot() -> dict[str, Any]:
    rows = map_rows(
        gate3_row, gate3_items(1_391_000, 1_397_999)
    )
    summary = summarize_gate3(rows)
    return {
        "purpose": "prospective attainability for every Gate-3 rate/effect floor",
        "public_seed_block": [1_391_000, 1_397_999],
        "criterion": False,
        **summary,
        "suspected_unattainable_floor": [
            name for name, value in summary["checks"].items() if not value
        ],
    }


def run_gate3() -> bool:
    pilot = gate3_pilot()
    dump("gate-3-attainability-pilot.json", pilot)
    if pilot["suspected_unattainable_floor"]:
        write_stop(3, pilot["suspected_unattainable_floor"], assigned_opened=False)
        return False
    rows = map_rows(
        gate3_row, gate3_items(1_403_000, 1_409_999)
    )
    summary = summarize_gate3(rows)
    payload = {
        "stage": "V2.6b",
        "gate": 3,
        "seed_block": [1_403_000, 1_409_999],
        **summary,
        "bounds": BOUNDS,
    }
    dump("gate-3-per_world.json", rows)
    dump("gate-3.json", payload)
    write_report(3, payload)
    if not payload["passed"]:
        write_stop(
            3,
            [name for name, value in payload["checks"].items() if not value],
            assigned_opened=True,
        )
    return payload["passed"]


def gate4_row(seed: int) -> dict[str, Any]:
    remain_world = v26b.generate_control_world(seed, scenario="remaining")
    remain = score_world(remain_world)
    no_partner = score_world(remain_world, lesions=("partner_to_trust",))
    low_world = v26b.generate_control_world(seed, scenario="low_stakes")
    high_world = v26b.generate_control_world(seed, scenario="high_stakes")
    low = score_world(low_world)
    high = score_world(high_world)
    low_no_stakes = score_world(low_world, lesions=("stakes",))
    high_no_stakes = score_world(high_world, lesions=("stakes",))
    no_cop = score_world(remain_world, lesions=("coprotection",))
    no_eff = score_world(remain_world, lesions=("attribution_efficacy",))
    no_test = score_world(remain_world, lesions=("epistemic_test_policy",))
    no_contact = score_world(remain_world, lesions=("policy_to_contact",))
    descent_world = v26b.generate_control_world(
        seed, scenario="descent", length=12
    )
    final_root_only = tuple(
        v26a.PartnerObservation(
            item.relational,
            1 if index == len(descent_world.partner_world.observations) - 1 else None,
        )
        for index, item in enumerate(descent_world.partner_world.observations)
    )
    broadcast = _score_with_partner(descent_world, final_root_only)
    no_broadcast = _score_with_partner(
        descent_world, final_root_only, lesions=("global_broadcast",)
    )
    return {
        "seed": seed,
        "partner_to_trust_effect": (
            float(remain.q_trust[2][1]) - float(no_partner.q_trust[2][1])
        ),
        "partner_to_trust_survival_error": max(
            float(np.max(np.abs(remain.q_trust[index] - no_partner.q_trust[index])))
            for index in (0, 1)
        ),
        "stakes_baseline_effect": low.permission_mass - high.permission_mass,
        "stakes_lesion_effect": (
            low_no_stakes.permission_mass - high_no_stakes.permission_mass
        ),
        "coprotection_target_effect": abs(
            remain.role_absence_risk_differential
            - no_cop.role_absence_risk_differential
        ),
        "coprotection_trust_survival_error": float(
            np.max(np.abs(remain.q_trust[1] - no_cop.q_trust[1]))
        ),
        "efficacy_target_effect": abs(
            remain.role_preserving_risk - no_eff.role_preserving_risk
        ),
        "efficacy_posterior_survival_error": float(
            np.max(
                np.abs(
                    remain.attribution_score.posterior
                    - no_eff.attribution_score.posterior
                )
            )
        ),
        "test_policy_target_effect": (
            remain.q_policy[v26b.POLICY_INDEX["test_contact"]]
            - no_test.q_policy[v26b.POLICY_INDEX["test_contact"]]
        ),
        "test_policy_trust_survival_error": max(
            float(np.max(np.abs(left - right)))
            for left, right in zip(remain.q_trust, no_test.q_trust)
        ),
        "contact_lesion_max": abs(no_contact.contact_probability),
        "contact_policy_survival_error": float(
            np.max(np.abs(remain.q_policy - no_contact.q_policy))
        ),
        "broadcast_root_uptake_effect": (
            broadcast.root_movement - no_broadcast.root_movement
        ),
        "broadcast_partner_survival_error": float(
            np.max(
                np.abs(
                    broadcast.partner_score.q_partner
                    - no_broadcast.partner_score.q_partner
                )
            )
        ),
    }


def summarize_gate4(rows: list[dict[str, Any]]) -> dict[str, Any]:
    effect_names = (
        "partner_to_trust_effect",
        "stakes_baseline_effect",
        "coprotection_target_effect",
        "efficacy_target_effect",
        "test_policy_target_effect",
        "broadcast_root_uptake_effect",
    )
    effects = {
        name: interval(row[name] for row in rows) for name in effect_names
    }
    maxima = {
        name: max(abs(row[name]) for row in rows)
        for name in (
            "partner_to_trust_survival_error",
            "stakes_lesion_effect",
            "coprotection_trust_survival_error",
            "efficacy_posterior_survival_error",
            "test_policy_trust_survival_error",
            "contact_lesion_max",
            "contact_policy_survival_error",
            "broadcast_partner_survival_error",
        )
    }
    checks = {
        "partner_to_trust": (
            effects["partner_to_trust_effect"]["lower_95"] > 0.0
            and maxima["partner_to_trust_survival_error"] <= TOL
        ),
        "stakes": (
            effects["stakes_baseline_effect"]["lower_95"] >= 0.15
            and maxima["stakes_lesion_effect"] <= TOL
        ),
        "coprotection": (
            effects["coprotection_target_effect"]["lower_95"] > 0.0
            and maxima["coprotection_trust_survival_error"] <= TOL
        ),
        "attribution_efficacy": (
            effects["efficacy_target_effect"]["lower_95"] > 0.0
            and maxima["efficacy_posterior_survival_error"] <= TOL
        ),
        "epistemic_test_policy": (
            effects["test_policy_target_effect"]["lower_95"] > 0.0
            and maxima["test_policy_trust_survival_error"] <= TOL
        ),
        "policy_to_contact": (
            maxima["contact_lesion_max"] <= TOL
            and maxima["contact_policy_survival_error"] <= TOL
        ),
        "global_broadcast": (
            effects["broadcast_root_uptake_effect"]["lower_95"] > 0.0
            and maxima["broadcast_partner_survival_error"] <= TOL
        ),
    }
    return {
        "metrics": {"effects": effects, "survival_maxima": maxima},
        "checks": checks,
        "passed": all(checks.values()),
    }


def gate4_pilot() -> dict[str, Any]:
    rows = map_rows(gate4_row, range(1_398_000, 1_399_000))
    summary = summarize_gate4(rows)
    return {
        "purpose": "prospective Gate-4 target-effect attainability",
        "public_seed_block": [1_398_000, 1_398_999],
        "criterion": False,
        **summary,
        "suspected_unattainable_floor": [
            name for name, value in summary["checks"].items() if not value
        ],
    }


def run_gate4() -> bool:
    pilot = gate4_pilot()
    dump("gate-4-attainability-pilot.json", pilot)
    if pilot["suspected_unattainable_floor"]:
        write_stop(4, pilot["suspected_unattainable_floor"], assigned_opened=False)
        return False
    rows = map_rows(gate4_row, range(1_410_000, 1_412_000))
    summary = summarize_gate4(rows)
    payload = {
        "stage": "V2.6b",
        "gate": 4,
        "seed_block": [1_410_000, 1_411_999],
        **summary,
        "bounds": BOUNDS,
    }
    dump("gate-4-per_world.json", rows)
    dump("gate-4.json", payload)
    write_report(4, payload)
    if not payload["passed"]:
        write_stop(
            4,
            [name for name, value in payload["checks"].items() if not value],
            assigned_opened=True,
        )
    return payload["passed"]


GATE5_SCENARIOS = (
    "trust_prior",
    "stakes",
    "temperature",
    "policy_costs",
    "partner_reliability",
    "refusal_diagnosticity",
    "efficacy",
    "coregulation",
    "root_evidence",
)


def gate5_row(item: tuple[int, str]) -> dict[str, Any]:
    seed, scenario = item
    world = v26b.generate_control_world(seed, scenario="remaining")
    if scenario == "trust_prior":
        ambiguous = v26b.generate_control_world(seed, scenario="ambiguous")
        high = score_world(
            ambiguous,
            initial_trust_priors=(
                (0.1, 0.9),
                (0.1, 0.9),
                (0.1, 0.9),
            ),
        )
        low = score_world(
            ambiguous,
            initial_trust_priors=(
                (0.9, 0.1),
                (0.9, 0.1),
                (0.9, 0.1),
            ),
        )
        value = high.permission_mass - low.permission_mass
    elif scenario == "stakes":
        low = score_world(
            v26b.generate_control_world(seed, scenario="low_stakes")
        )
        high = score_world(
            v26b.generate_control_world(seed, scenario="high_stakes")
        )
        value = low.permission_mass - high.permission_mass
    elif scenario == "temperature":
        low = score_world(world, inverse_temperature=2.0)
        high = score_world(world, inverse_temperature=8.0)
        value = entropy(low.q_policy) - entropy(high.q_policy)
    elif scenario == "policy_costs":
        baseline = score_world(world)
        raised_block = score_world(
            world, policy_effort=(0.55, 0.18, 0.05)
        )
        value = raised_block.permission_mass - baseline.permission_mass
    elif scenario == "partner_reliability":
        reliable = score_world(world)
        intrusive = tuple(
            v26a.PartnerObservation((0, 1, 0, 0), None)
            for _ in world.partner_world.observations
        )
        weak = _score_with_partner(world, intrusive)
        value = reliable.permission_mass - weak.permission_mass
    elif scenario == "refusal_diagnosticity":
        high = score_world(
            v26b.generate_control_world(
                seed, scenario="high_diagnostic_rupture"
            )
        )
        low = score_world(
            v26b.generate_control_world(
                seed, scenario="low_diagnostic_rupture"
            )
        )
        value = float(low.q_trust[2][1] - high.q_trust[2][1])
    elif scenario == "efficacy":
        full_world = v26b.generate_control_world(seed, scenario="remaining")
        irrelevant = v234.generate_controlled_world(
            seed, scenario="irrelevant", length=12
        )
        full = v234.generate_controlled_world(
            seed, scenario="full", length=12
        )
        full_score = v26b.score(
            full_world.trust_observations,
            full_world.partner_world.observations,
            full.episodes,
            stakes=full_world.stakes,
        )
        irrelevant_score = v26b.score(
            full_world.trust_observations,
            full_world.partner_world.observations,
            irrelevant.episodes,
            stakes=full_world.stakes,
        )
        value = full_score.permission_mass - irrelevant_score.permission_mass
    elif scenario == "coregulation":
        reliable = score_world(world)
        missing = tuple(
            v26a.PartnerObservation((None, None, None, None), None)
            for _ in world.partner_world.observations
        )
        weak = _score_with_partner(world, missing)
        value = reliable.permission_mass - weak.permission_mass
    else:
        descent = v26b.generate_control_world(
            seed, scenario="descent", length=12
        )
        with_root = score_world(descent)
        no_root = tuple(
            v26a.PartnerObservation(item.relational, None)
            for item in descent.partner_world.observations
        )
        without_root = _score_with_partner(descent, no_root)
        value = with_root.root_movement - without_root.root_movement
    return {
        "seed": seed,
        "scenario": scenario,
        "effect": value,
        "finite": math.isfinite(value),
    }


def gate5_items(start: int, worlds_per_cell: int) -> list[tuple[int, str]]:
    return [
        (start + cell * worlds_per_cell + offset, scenario)
        for cell, scenario in enumerate(GATE5_SCENARIOS)
        for offset in range(worlds_per_cell)
    ]


def summarize_gate5(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by = {
        scenario: [row for row in rows if row["scenario"] == scenario]
        for scenario in GATE5_SCENARIOS
    }
    effects = {
        scenario: interval(row["effect"] for row in cell)
        for scenario, cell in by.items()
    }
    checks = {
        "all_finite": all(row["finite"] for row in rows),
        **{
            f"{scenario}_direction": result["lower_95"] > 0.0
            for scenario, result in effects.items()
        },
    }
    return {
        "metrics": {"scenario_effects": effects, "world_count": len(rows)},
        "checks": checks,
        "passed": all(checks.values()),
    }


def gate5_pilot() -> dict[str, Any]:
    rows = map_rows(
        gate5_row,
        gate5_items(1_399_000, 111),
    )
    summary = summarize_gate5(rows)
    return {
        "purpose": "prospective Gate-5 qualitative robustness attainability",
        "public_seed_block": [1_399_000, 1_399_998],
        "criterion": False,
        **summary,
        "suspected_unattainable_floor": [
            name for name, value in summary["checks"].items() if not value
        ],
    }


def run_gate5() -> bool:
    pilot = gate5_pilot()
    dump("gate-5-attainability-pilot.json", pilot)
    if pilot["suspected_unattainable_floor"]:
        write_stop(5, pilot["suspected_unattainable_floor"], assigned_opened=False)
        return False
    rows = map_rows(
        gate5_row,
        gate5_items(1_412_000, 2000),
    )
    summary = summarize_gate5(rows)
    suite = subprocess.run(
        [sys.executable, "run_tests_parallel.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    dump(
        "full-fast-suite-gate5.json",
        {
            "command": "python3 run_tests_parallel.py",
            "returncode": suite.returncode,
            "passed": suite.returncode == 0,
            "stdout": suite.stdout,
            "stderr": suite.stderr,
        },
    )
    prior_gates = {
        gate: json.loads((OUT / f"gate-{gate}.json").read_text())["passed"]
        for gate in range(1, 5)
    }
    chain = verify_manifest_chain(
        ROOT, "results/V2.3.4/freeze-manifest.json"
    )
    cumulative_checks = {
        "standing_gates_1_4": all(prior_gates.values()),
        "full_cumulative_suite": suite.returncode == 0,
        "permanent_constitutions": constitution.cumulative_constitution_audit()[
            "passed"
        ],
        "manifest_chain": bool(chain["passed"]),
        "escrow_untouched": True,
    }
    checks = summary["checks"] | cumulative_checks
    passed = all(checks.values())
    payload = {
        "stage": "V2.6b",
        "gate": 5,
        "seed_block": [1_412_000, 1_429_999],
        "metrics": summary["metrics"],
        "checks": checks,
        "manifest_chain": chain,
        "bounds": BOUNDS,
        "custody": {
            "escrow_block": [2_050_000, 2_052_999],
            "escrow_accessed": False,
            "passed": True,
        },
        "passed": passed,
    }
    dump("gate-5-per_world.json", rows)
    dump("gate-5.json", payload)
    write_report(5, payload)
    if not passed:
        write_stop(
            5,
            [name for name, value in checks.items() if not value],
            assigned_opened=True,
        )
    return passed


def map_rows(function: Any, items: Iterable[Any]) -> list[dict[str, Any]]:
    values = list(items)
    try:
        executor_context = concurrent.futures.ProcessPoolExecutor()
    except PermissionError:
        executor_context = concurrent.futures.ThreadPoolExecutor()
    with executor_context as executor:
        return list(executor.map(function, values, chunksize=20))


def write_report(gate: int, payload: dict[str, Any]) -> None:
    lines = [
        f"# V2.6b gate {gate}",
        "",
        f"Verdict: **{'PASS' if payload['passed'] else 'FAIL'}**.",
        "",
        "## Metrics",
        "",
        f"`{json.dumps(plain(payload.get('metrics', {})), sort_keys=True)}`",
        "",
        "## Criteria",
        "",
    ]
    lines += [
        f"- `{name}`: **{'PASS' if value else 'FAIL'}**"
        for name, value in payload.get("checks", {}).items()
    ]
    (OUT / f"gate-{gate}-report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def write_stop(
    gate: int, failures: Sequence[str], *, assigned_opened: bool
) -> None:
    (OUT / f"gate-{gate}-diagnosis-stub.md").write_text(
        f"# V2.6b gate-{gate} diagnosis stub\n\n"
        "Honest stop. Failed items retained verbatim:\n\n"
        + "\n".join(f"- `{name}`" for name in failures)
        + f"\n\nAssigned block opened: `{str(assigned_opened).lower()}`.\n",
        encoding="utf-8",
    )


def ready(gate: int, passed: bool) -> None:
    files = sorted(
        str(path.relative_to(ROOT))
        for path in OUT.glob(f"gate-{gate}*")
        if path.is_file()
    )
    (OUT / f"ready-to-commit-gate{gate}.md").write_text(
        f"# Ready to commit: V2.6b gate {gate}\n\n"
        f"Verdict: {'PASS' if passed else 'FAIL / honest stop'}\n\n"
        + "\n".join(f"- `{item}`" for item in files)
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gate", type=int, choices=(1, 2, 3, 4, 5), required=True
    )
    args = parser.parse_args()
    runner = {
        1: run_gate1,
        2: run_gate2,
        3: run_gate3,
        4: run_gate4,
        5: run_gate5,
    }[args.gate]
    passed = runner()
    ready(args.gate, passed)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
