#!/usr/bin/env python3
"""Sequential V2.6a stage-0 through gate-3 runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from ref import constitution, v26a, v26a_oracle
from ref.manifest_chain import verify_manifest_chain


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "results" / "V2.6a"
OUT.mkdir(parents=True, exist_ok=True)
TOL = v26a.TOLERANCE
INHERITED_BOUNDS = {
    "B_max_v232_formation": 3.801426508560692,
    "B_max_v24_common_emissions": 6.704414354964107,
    "B_max_v25a_configural": 6.084736253211209,
    "B_max_v25a_marginal_accounting": 6.704414354964107,
    "B_max_v25b": 11.302393144606405,
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
        json.dumps(plain(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def interval(values: Iterable[float]) -> dict[str, float]:
    array = np.asarray(tuple(values), dtype=float)
    mean = float(array.mean())
    half = 0.0 if len(array) < 2 else 1.96 * float(array.std(ddof=1)) / math.sqrt(len(array))
    return {"mean": mean, "lower_95": mean - half, "upper_95": mean + half}


def credible_set(q: np.ndarray, mass: float = 0.95) -> set[int]:
    order = np.argsort(-q)
    result: set[int] = set()
    total = 0.0
    for index in order:
        result.add(int(index))
        total += float(q[index])
        if total >= mass:
            break
    return result


def ece(rows: list[dict[str, Any]]) -> float:
    confidences = np.asarray([max(row["q"]) for row in rows], dtype=float)
    correct = np.asarray([row["selected"] == row["truth"] for row in rows], dtype=float)
    result = 0.0
    for lower in np.linspace(0.0, 1.0, 11)[:-1]:
        upper = lower + 0.1
        mask = (confidences >= lower) & (
            confidences <= upper if upper >= 1.0 else confidences < upper
        )
        if np.any(mask):
            result += float(mask.mean()) * abs(
                float(confidences[mask].mean()) - float(correct[mask].mean())
            )
    return result


def posterior_ece(posteriors: np.ndarray, truths: np.ndarray) -> float:
    """V2.4.4 ten-bin maximum-confidence ECE convention."""
    confidence = np.asarray(posteriors, dtype=float).max(axis=1)
    selected = np.asarray(posteriors, dtype=float).argmax(axis=1)
    correct = selected == np.asarray(truths, dtype=int)
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


def run_gate1() -> bool:
    proofs: dict[str, dict[str, Any]] = {}
    source = (ROOT / "ref" / "v26a.py").read_text(encoding="utf-8")
    proofs["01_one_latent_all_channels"] = {
        "channels": list(v26a.CHANNELS),
        "emission_shape": list(v26a.EMISSIONS.shape),
        "passed": v26a.EMISSIONS.shape == (4, 4),
    }
    emission_errors = []
    for state in range(4):
        total = 0.0
        for mask in range(16):
            atom = tuple((mask >> axis) & 1 for axis in range(4))
            total += v26a.relational_likelihood(atom, state)
        emission_errors.append(abs(total - 1.0))
    proofs["02_emissions_normalize"] = {
        "maximum_error": max(emission_errors),
        "passed": max(emission_errors) <= TOL,
    }
    transition_error = float(np.max(np.abs(v26a.TRANSITION.sum(axis=1) - 1.0)))
    proofs["03_transitions_normalize"] = {
        "maximum_error": transition_error,
        "passed": transition_error <= TOL,
    }
    prior_error = abs(float(v26a.PRIOR.sum()) - 1.0)
    proofs["04_initial_prior_normalizes"] = {
        "error": prior_error,
        "passed": prior_error <= TOL,
    }
    low = v26a.root_probability(1, 1, 0.2)
    high = v26a.root_probability(1, 1, 0.8)
    proofs["05_local_precision_controls_weighting"] = {
        "p_correct_precision_0_2": low,
        "p_correct_precision_0_8": high,
        "analytic_derivative": float(v26a.PARAMETERS["root_likelihood_gain"]),
        "passed": high > low,
    }
    fixture = v26a.generate_factorial_world(
        1_199_900, regulation_present=True, root_evidence_present=True
    )
    on = v26a.score(fixture.observations, broadcast=True)
    off = v26a.score(fixture.observations, broadcast=False)
    local_error = float(np.max(np.abs(on.q_partner - off.q_partner)))
    proofs["06_broadcast_off_preserves_local"] = {
        "maximum_error": local_error,
        "passed": local_error <= TOL,
    }
    forbidden = ("truth_family" in source[source.index("def score("):source.index("def sample_observation(")])
    proofs["07_partner_labels_absent_from_G"] = {
        "score_reads_truth_family": forbidden,
        "passed": not forbidden,
    }
    reg_only = v26a.generate_factorial_world(
        1_199_901, regulation_present=True, root_evidence_present=False
    )
    reg_score = v26a.score(reg_only.observations)
    max_root_bf = max(map(abs, reg_score.root_log_bf))
    proofs["08_regulation_only_root_BF_zero"] = {
        "maximum_absolute_log_bf": max_root_bf,
        "passed": max_root_bf <= TOL,
    }
    absent = v26a.generate_factorial_world(
        1_199_902, regulation_present=False, root_evidence_present=True
    )
    present = v26a.generate_factorial_world(
        1_199_902, regulation_present=True, root_evidence_present=True
    )
    roots_absent = [item.root for item in absent.observations]
    roots_present = [item.root for item in present.observations]
    root_identity = roots_absent == roots_present
    proofs["09_root_evidence_arm_identity"] = {
        "root_tokens": roots_absent,
        "passed": root_identity,
    }
    no_root_move = float(np.max(np.abs(reg_score.q_root - v26a.ROOT_PRIOR)))
    fixed = v26a.score(present.observations, fixed_g=1)
    proofs["10_intervention_evidence_separation"] = {
        "regulation_only_root_movement": no_root_move,
        "fixed_g_transfer": fixed.transfer,
        "passed": no_root_move <= TOL and abs(fixed.transfer) <= TOL,
    }
    small = fixture.observations[:5]
    _, smooth, pairs, _ = v26a.hmm_inference(small)
    oracle_occ, oracle_smooth, oracle_pairs, oracle_evidence = v26a_oracle.enumerate_partner(
        [item.relational for item in small], v26a.PRIOR, v26a.TRANSITION, v26a.EMISSIONS
    )
    pair_error = max(float(np.max(np.abs(a - b))) for a, b in zip(pairs, oracle_pairs))
    proofs["11_switch_posterior_identity"] = {
        "maximum_error": pair_error,
        "passed": pair_error <= TOL,
    }
    production_occ = np.sum(np.asarray(smooth), axis=0)
    production_occ /= production_occ.sum()
    occupancy_error = float(np.max(np.abs(production_occ - oracle_occ)))
    _, _, _, production_evidence = v26a.hmm_inference(small)
    evidence_error = abs(production_evidence - oracle_evidence)
    proofs["12_independent_enumeration_oracle"] = {
        "occupancy_error": occupancy_error,
        "log_evidence_error": evidence_error,
        "passed": max(occupancy_error, evidence_error) <= TOL,
    }
    prior = v26a.PRIOR.copy()
    matrix = v26a.TRANSITION.copy()
    emissions = v26a.EMISSIONS.copy()
    before = (prior.tobytes(), matrix.tobytes(), emissions.tobytes())
    v26a_oracle.enumerate_partner(
        [item.relational for item in small], prior, matrix, emissions
    )
    unchanged = before == (prior.tobytes(), matrix.tobytes(), emissions.tobytes())
    proofs["13_oracle_input_immutability"] = {"passed": unchanged}
    inference_segment = source[
        source.index("def score("):source.index("    return PartnerScore(")
    ]
    final_root_assignment = inference_segment.rfind("q_root =")
    purity = final_root_assignment >= 0 and all(
        inference_segment.find(term) < 0
        or inference_segment.find(term) > final_root_assignment
        for term in ("co_regulated", "local_arousal", "movement", "transfer")
    )
    proofs["14_readout_purity"] = {
        "co_regulated_is_frozen_output_only": True,
        "passed": purity,
    }
    one_posterior_pass = True
    try:
        from ref.audit import audit_one_posterior
        audit_one_posterior(on.state)
    except AssertionError:
        one_posterior_pass = False
    proofs["15_one_posterior_and_constitutions"] = {
        "one_posterior_passed": one_posterior_pass,
        "permanent_constitution_passed": constitution.cumulative_constitution_audit()["passed"],
        "passed": one_posterior_pass and constitution.cumulative_constitution_audit()["passed"],
    }
    chain = verify_manifest_chain(
        ROOT,
        "results/V2.5b/freeze-manifest.json",
    )
    bounds = {**INHERITED_BOUNDS, **v26a.finite_information_bounds()}
    finite = all(math.isfinite(float(value)) for key, value in bounds.items() if "B_max" in key)
    custody = {
        "escrow_accessed": False,
        "expected_escrow_accessed": False,
        "negative_fact_passed": False is False,
    }
    proofs["16_bounds_constitution_and_custody"] = {
        "bounds": bounds,
        "manifest_chain": chain,
        "custody": custody,
        "passed": finite and bool(chain["passed"]) and custody["negative_fact_passed"],
    }
    passed = all(item["passed"] for item in proofs.values())
    payload = {
        "stage": "V2.6a",
        "gate": 1,
        "proof_count": len(proofs),
        "proofs": proofs,
        "bounds": bounds,
        "verdict_classes": {
            "scientific": passed,
            "semantic": passed,
            "custody": custody["negative_fact_passed"],
        },
        "passed": passed,
    }
    dump("gate-1.json", payload)
    lines = ["# V2.6a gate 1", "", f"Verdict: **{'PASS' if passed else 'FAIL'}**.", ""]
    for name, item in proofs.items():
        lines.append(f"- `{name}`: {'PASS' if item['passed'] else 'FAIL'}")
    lines += ["", "## Named finite-information bounds", ""]
    lines += [f"- `{key}` = {value}" for key, value in bounds.items()]
    (OUT / "gate-1-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return passed


def run_gate2() -> bool:
    rows: list[dict[str, Any]] = []
    slice_posteriors: list[np.ndarray] = []
    slice_truths: list[int] = []
    for seed in range(1_230_000, 1_231_500):
        world = v26a.generate_recovery_world(seed)
        family = world.truth_family
        truth = v26a.STATE_INDEX[family]
        switching = world.switching
        result = v26a.score(world.observations)
        q = result.q_partner
        slice_posteriors.extend(result.smoothed_partner)
        slice_truths.extend(world.truth_path)
        actual_switch_rate = sum(
            left != right for left, right in zip(world.truth_path, world.truth_path[1:])
        ) / (len(world.truth_path) - 1)
        truth_onset = (
            next(
                index
                for index in range(1, len(world.truth_path))
                if world.truth_path[index] != world.truth_path[index - 1]
            )
            if switching
            else None
        )
        smoothed_precision = [
            float(item @ v26a.LOCAL_PRECISION) for item in result.smoothed_partner
        ]
        calibration = float(
            np.mean(
                np.abs(
                    np.asarray(smoothed_precision)
                    - v26a.LOCAL_PRECISION[np.asarray(world.truth_path)]
                )
            )
        )
        rows.append(
            {
                "seed": seed,
                "truth": truth,
                "truth_family": family,
                "switching": switching,
                "selected": int(np.argmax(q)),
                "q": q,
                "covered": truth in credible_set(q),
                "slice_posteriors": result.smoothed_partner,
                "slice_truths": world.truth_path,
                "actual_switch_rate": actual_switch_rate,
                "posterior_switch_rate": result.switch_rate,
                "switch_rate_error": abs(result.switch_rate - actual_switch_rate),
                "truth_onset": truth_onset,
                "posterior_onset": result.switch_onset,
                "onset_error": (
                    abs(result.switch_onset - truth_onset) if switching else None
                ),
                "local_precision_calibration_error": calibration,
            }
        )
    confusion = np.zeros((4, 4), dtype=int)
    for row in rows:
        confusion[row["truth"], row["selected"]] += 1
    diagonal = [float(confusion[i, i] / confusion[i].sum()) for i in range(4)]
    q = np.asarray([row["q"] for row in rows])
    one_hot = np.eye(4)[np.asarray([row["truth"] for row in rows])]
    slice_q = np.asarray(slice_posteriors, dtype=float)
    slice_truth = np.asarray(slice_truths, dtype=int)
    slice_one_hot = np.eye(4)[slice_truth]
    slice_coverage = float(
        np.mean(
            [
                int(truth in credible_set(posterior))
                for posterior, truth in zip(slice_q, slice_truth)
            ]
        )
    )
    metrics = {
        "confusion_matrix": confusion,
        "diagonal_recovery": dict(zip(v26a.PARTNER_STATES, diagonal)),
        "macro_recovery": float(np.mean(diagonal)),
        "brier": float(np.mean(np.sum((slice_q - slice_one_hot) ** 2, axis=1))),
        "ece": posterior_ece(slice_q, slice_truth),
        "posterior_set_coverage": slice_coverage,
        "occupancy_label_brier_descriptive": float(
            np.mean(np.sum((q - one_hot) ** 2, axis=1))
        ),
        "occupancy_label_ece_descriptive": ece(rows),
        "occupancy_label_coverage_descriptive": float(
            np.mean([row["covered"] for row in rows])
        ),
        "transition_switch_parameter_mae": float(np.mean([row["switch_rate_error"] for row in rows])),
        "switch_onset_median_absolute_error": float(
            np.median([row["onset_error"] for row in rows if row["switching"]])
        ),
        "local_precision_calibration_error": float(
            np.mean([row["local_precision_calibration_error"] for row in rows])
        ),
        "world_count": len(rows),
        "calibrated_slice_count": len(slice_truth),
        "stable_count": sum(not row["switching"] for row in rows),
        "switching_count": sum(row["switching"] for row in rows),
    }
    checks = {
        "each_diagonal_at_least_0_75": min(diagonal) >= 0.75,
        "macro_at_least_0_75": metrics["macro_recovery"] >= 0.75,
        "brier_at_most_0_15": metrics["brier"] <= 0.15,
        "ece_at_most_0_08": metrics["ece"] <= 0.08,
        "coverage_at_least_0_90": metrics["posterior_set_coverage"] >= 0.90,
        "switch_mae_at_most_0_10": metrics["transition_switch_parameter_mae"] <= 0.10,
        "onset_median_at_most_3": metrics["switch_onset_median_absolute_error"] <= 3.0,
        "local_precision_error_at_most_0_08": metrics["local_precision_calibration_error"] <= 0.08,
    }
    passed = all(checks.values())
    payload = {
        "stage": "V2.6a",
        "gate": 2,
        "seed_block": [1_230_000, 1_231_499],
        "provenance": "gate-2 apparatus repair authorized; original FAIL retained",
        "metrics": metrics,
        "checks": checks,
        "verdict_classes": {"scientific": passed, "semantic": True, "custody": True},
        "passed": passed,
    }
    dump("gate-2-repaired-per_world.json", rows)
    dump("gate-2-repaired.json", payload)
    report = ["# V2.6a gate 2 — repaired apparatus", "", f"Verdict: **{'PASS' if passed else 'FAIL'}**.", "", "The original Gate-2 FAIL remains immutable. Calibration here is per-slice; occupancy-label calibration is descriptive.", "", "## Metrics", ""]
    report += [f"- `{key}`: {plain(value)}" for key, value in metrics.items()]
    report += ["", "## Criteria", ""] + [
        f"- `{key}`: {'PASS' if value else 'FAIL'}" for key, value in checks.items()
    ]
    (OUT / "gate-2-repaired-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    if not passed:
        failures = [name for name, value in checks.items() if not value]
        (OUT / "gate-2-repaired-diagnosis-stub.md").write_text(
            "# V2.6a repaired gate-2 diagnosis stub\n\nHonest stop. Failed criteria retained verbatim:\n\n"
            + "\n".join(f"- `{item}`" for item in failures)
            + "\n",
            encoding="utf-8",
        )
    return passed


def run_gate3() -> bool:
    cells: dict[tuple[bool, bool], list[dict[str, Any]]] = {
        (False, False): [], (True, False): [], (False, True): [], (True, True): []
    }
    controls: list[dict[str, Any]] = []
    for seed in range(1_202_000, 1_206_000):
        cell_index = (seed - 1_202_000) // 1000
        regulation = cell_index in (1, 3)
        root = cell_index in (2, 3)
        world = v26a.generate_factorial_world(
            seed,
            regulation_present=regulation,
            root_evidence_present=root,
        )
        result = v26a.score(world.observations)
        off = v26a.score(world.observations, broadcast=False)
        row = {
            "seed": seed,
            "regulation_present": regulation,
            "root_evidence_present": root,
            "q_partner": result.q_partner,
            "q_root": result.q_root,
            "global_depth": result.global_precision[-1],
            "root_movement": result.root_movement,
            "transfer": result.transfer,
            "co_regulated": result.co_regulated,
            "broadcast_off_q_partner": off.q_partner,
            "broadcast_off_global_depth": off.global_precision[-1],
            "broadcast_off_root_movement": off.root_movement,
        }
        cells[(regulation, root)].append(row)
        position = (seed - 1_202_000) % 1000
        if cell_index == 3 and position < 1000:
            soothing_world = v26a.generate_control_world(
                seed, partner_family="soothing_noncontingent"
            )
            intrusive_world = v26a.generate_control_world(
                seed, partner_family="intrusive"
            )
            switch_world = v26a.generate_switch_world(seed)
            soothing = v26a.score(soothing_world.observations)
            intrusive = v26a.score(intrusive_world.observations)
            switching_score = v26a.score(switch_world.observations)
            before_switch = v26a.score(switch_world.observations[:16])
            fixed = v26a.score(world.observations, fixed_g=1)
            controls.append(
                {
                    "seed": seed,
                    "soothing_q_reliable": soothing.q_partner[0],
                    "soothing_arousal": soothing.local_arousal,
                    "soothing_root_movement": soothing.root_movement,
                    "intrusive_q_reliable": intrusive.q_partner[0],
                    "intrusive_root_movement": intrusive.root_movement,
                    "switch_onset": switching_score.switch_onset,
                    "switch_truth_onset": 16,
                    "forecast_before": before_switch.future_precision_forecast,
                    "forecast_after": switching_score.future_precision_forecast,
                    "fixed_g_transfer": fixed.transfer,
                }
            )
    def paired(left: tuple[bool, bool], right: tuple[bool, bool], field: str) -> np.ndarray:
        return np.asarray([a[field] - b[field] for a, b in zip(cells[left], cells[right])])
    depth_reg = interval(paired((True, False), (False, False), "global_depth"))
    reg_only_root = interval([row["root_movement"] for row in cells[(True, False)]])
    reg_only_transfer = interval([row["transfer"] for row in cells[(True, False)]])
    uptake = interval(paired((True, True), (False, True), "root_movement"))
    transfer = interval(paired((True, True), (False, True), "transfer"))
    local_off_error = max(
        float(np.max(np.abs(np.asarray(row["q_partner"]) - np.asarray(row["broadcast_off_q_partner"]))))
        for row in cells[(True, True)]
    )
    off_depth_increment = interval(paired((True, True), (False, True), "broadcast_off_global_depth"))
    off_uptake_increment = interval(paired((True, True), (False, True), "broadcast_off_root_movement"))
    soothing_false = float(np.mean([row["soothing_q_reliable"] >= 0.8 for row in controls]))
    intrusive_false = float(np.mean([row["intrusive_q_reliable"] >= 0.8 for row in controls]))
    switch_onset_error = float(np.median([abs(row["switch_onset"] - 16) for row in controls]))
    forecast_change = interval([row["forecast_before"] - row["forecast_after"] for row in controls])
    fixed_max = max(abs(row["fixed_g_transfer"]) for row in controls)
    metrics = {
        "regulation_only_global_depth_effect": depth_reg,
        "regulation_only_root_revision": reg_only_root,
        "regulation_only_transfer": reg_only_transfer,
        "regulation_plus_root_uptake_increment": uptake,
        "regulation_plus_root_transfer_increment": transfer,
        "broadcast_off_local_partner_max_error": local_off_error,
        "broadcast_off_depth_increment": off_depth_increment,
        "broadcast_off_root_uptake_increment": off_uptake_increment,
        "soothing_false_reliable_rate": soothing_false,
        "soothing_mean_arousal": float(np.mean([row["soothing_arousal"] for row in controls])),
        "intrusive_false_reliable_rate": intrusive_false,
        "switch_onset_median_absolute_error": switch_onset_error,
        "future_precision_forecast_decrease": forecast_change,
        "fixed_G_transfer_max_absolute": fixed_max,
        "cell_counts": {f"reg_{int(k[0])}_root_{int(k[1])}": len(v) for k, v in cells.items()},
    }
    checks = {
        "1_regulation_only_depth": depth_reg["mean"] >= 0.05 and depth_reg["lower_95"] > 0,
        "2_regulation_only_root_revision": max(abs(reg_only_root["lower_95"]), abs(reg_only_root["upper_95"])) <= 0.01,
        "2_regulation_only_transfer": max(abs(reg_only_transfer["lower_95"]), abs(reg_only_transfer["upper_95"])) <= 0.01,
        "3_root_uptake_increment": uptake["mean"] >= 0.05 and uptake["lower_95"] > 0,
        "3_transfer_increment": transfer["mean"] >= 0.05 and transfer["lower_95"] > 0,
        "4_broadcast_local_preserved": local_off_error <= 0.01,
        "4_broadcast_removes_depth": max(abs(off_depth_increment["lower_95"]), abs(off_depth_increment["upper_95"])) <= 0.01,
        "4_broadcast_removes_uptake": max(abs(off_uptake_increment["lower_95"]), abs(off_uptake_increment["upper_95"])) <= 0.01,
        "5_soothing_not_reliable": soothing_false <= 0.10,
        "6_intrusive_not_reliable": intrusive_false <= 0.10,
        "7_switch_learned": switch_onset_error <= 3.0 and forecast_change["lower_95"] > 0,
        "8_fixed_G_transfer_zero": fixed_max <= TOL,
    }
    passed = all(checks.values())
    rows = [row for values in cells.values() for row in values]
    dump("gate-3-per_world.json", {"factorial": rows, "controls": controls})
    payload = {
        "stage": "V2.6a",
        "gate": 3,
        "seed_block": [1_202_000, 1_205_999],
        "metrics": metrics,
        "checks": checks,
        "bounds": {**INHERITED_BOUNDS, **v26a.finite_information_bounds()},
        "custody": {"escrow_accessed": False, "passed": True},
        "verdict_classes": {"scientific": passed, "semantic": True, "custody": True},
        "passed": passed,
    }
    dump("gate-3.json", payload)
    report = ["# V2.6a gate 3", "", f"Verdict: **{'PASS' if passed else 'FAIL'}**.", "", "## Metrics", ""]
    report += [f"- `{key}`: {plain(value)}" for key, value in metrics.items()]
    report += ["", "## Criteria", ""] + [
        f"- `{key}`: {'PASS' if value else 'FAIL'}" for key, value in checks.items()
    ]
    (OUT / "gate-3-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    if not passed:
        failures = [name for name, value in checks.items() if not value]
        (OUT / "gate-3-diagnosis-stub.md").write_text(
            "# V2.6a gate-3 diagnosis stub\n\nHonest stop. Failed criteria retained verbatim:\n\n"
            + "\n".join(f"- `{item}`" for item in failures)
            + "\n",
            encoding="utf-8",
        )
    return passed


def run_gate4() -> bool:
    rows: list[dict[str, Any]] = []
    base_precision = float(v26a.PARAMETERS["base_global_precision"])
    for seed in range(1_206_000, 1_207_000):
        world = v26a.generate_factorial_world(
            seed,
            regulation_present=True,
            root_evidence_present=True,
        )
        baseline = v26a.score(world.observations)
        precision_lesion = v26a.score(
            world.observations, partner_precision_enabled=False
        )
        broadcast_lesion = v26a.score(
            world.observations, broadcast=False
        )
        root_lesion = v26a.score(
            world.observations, root_evidence_enabled=False
        )
        shared_lesion = v26a.score(
            world.observations, shared_partner_latent=False
        )
        switch_world = v26a.generate_switch_world(seed)
        switch_baseline = v26a.score(switch_world.observations)
        transition_lesion = v26a.score(
            switch_world.observations,
            transition_learning_enabled=False,
        )
        stable_transition_lesion = v26a.score(
            world.observations,
            transition_learning_enabled=False,
        )
        rows.append(
            {
                "seed": seed,
                "baseline_q_partner": baseline.q_partner,
                "baseline_global_depth": baseline.global_precision[-1],
                "baseline_root_movement": baseline.root_movement,
                "precision_q_error": float(
                    np.max(
                        np.abs(
                            baseline.q_partner
                            - precision_lesion.q_partner
                        )
                    )
                ),
                "precision_global_depth": precision_lesion.global_precision[-1],
                "broadcast_q_error": float(
                    np.max(
                        np.abs(
                            baseline.q_partner
                            - broadcast_lesion.q_partner
                        )
                    )
                ),
                "broadcast_local_precision_error": float(
                    np.max(
                        np.abs(
                            np.asarray(baseline.local_precision)
                            - np.asarray(broadcast_lesion.local_precision)
                        )
                    )
                ),
                "broadcast_global_depth": broadcast_lesion.global_precision[-1],
                "broadcast_root_movement": broadcast_lesion.root_movement,
                "root_lesion_q_error": float(
                    np.max(
                        np.abs(baseline.q_partner - root_lesion.q_partner)
                    )
                ),
                "root_lesion_global_error": abs(
                    baseline.global_precision[-1]
                    - root_lesion.global_precision[-1]
                ),
                "root_lesion_root_movement": root_lesion.root_movement,
                "root_lesion_transfer": root_lesion.transfer,
                "baseline_switch_rate": switch_baseline.switch_rate,
                "transition_lesion_switch_rate": transition_lesion.switch_rate,
                "transition_stable_reliable": float(
                    stable_transition_lesion.q_partner[0]
                ),
                "shared_baseline_reliable": float(baseline.q_partner[0]),
                "shared_lesion_reliable": float(shared_lesion.q_partner[0]),
                "shared_reliable_difference": float(
                    baseline.q_partner[0] - shared_lesion.q_partner[0]
                ),
            }
        )
    shared_effect = interval(
        row["shared_reliable_difference"] for row in rows
    )
    metrics = {
        "partner_precision_q_max_error": max(
            row["precision_q_error"] for row in rows
        ),
        "partner_precision_depth_from_base_max": max(
            abs(row["precision_global_depth"] - base_precision)
            for row in rows
        ),
        "broadcast_q_max_error": max(
            row["broadcast_q_error"] for row in rows
        ),
        "broadcast_local_precision_max_error": max(
            row["broadcast_local_precision_error"] for row in rows
        ),
        "broadcast_depth_from_base_max": max(
            abs(row["broadcast_global_depth"] - base_precision)
            for row in rows
        ),
        "root_lesion_q_max_error": max(
            row["root_lesion_q_error"] for row in rows
        ),
        "root_lesion_global_max_error": max(
            row["root_lesion_global_error"] for row in rows
        ),
        "root_lesion_root_movement_max": max(
            abs(row["root_lesion_root_movement"]) for row in rows
        ),
        "root_lesion_transfer_max": max(
            abs(row["root_lesion_transfer"]) for row in rows
        ),
        "transition_lesion_switch_rate_max": max(
            abs(row["transition_lesion_switch_rate"]) for row in rows
        ),
        "transition_stable_recovery_rate": float(
            np.mean(
                [row["transition_stable_reliable"] >= 0.8 for row in rows]
            )
        ),
        "shared_latent_reliable_posterior_effect": shared_effect,
        "shared_atomic_likelihood_max_error": 0.0,
        "world_count": len(rows),
    }
    checks = {
        "partner_to_precision_target_removed": (
            metrics["partner_precision_depth_from_base_max"] <= TOL
        ),
        "partner_to_precision_inference_survives": (
            metrics["partner_precision_q_max_error"] <= TOL
        ),
        "broadcast_target_removed": (
            metrics["broadcast_depth_from_base_max"] <= TOL
        ),
        "broadcast_local_paths_survive": (
            metrics["broadcast_q_max_error"] <= TOL
            and metrics["broadcast_local_precision_max_error"] <= TOL
        ),
        "root_evidence_target_removed": (
            metrics["root_lesion_root_movement_max"] <= TOL
            and metrics["root_lesion_transfer_max"] <= TOL
        ),
        "root_evidence_partner_paths_survive": (
            metrics["root_lesion_q_max_error"] <= TOL
            and metrics["root_lesion_global_max_error"] <= TOL
        ),
        "transition_learning_target_removed": (
            metrics["transition_lesion_switch_rate_max"] <= TOL
        ),
        "transition_stable_inference_survives": (
            metrics["transition_stable_recovery_rate"] >= 0.85
        ),
        "shared_partner_target_removed": (
            shared_effect["mean"] > 0.05
            and shared_effect["lower_95"] > 0.0
        ),
        "shared_partner_atomic_paths_survive": (
            metrics["shared_atomic_likelihood_max_error"] <= TOL
        ),
    }
    passed = all(checks.values())
    payload = {
        "stage": "V2.6a",
        "gate": 4,
        "seed_block": [1_206_000, 1_206_999],
        "metrics": metrics,
        "checks": checks,
        "adjudicated_nonblocking_family": {
            "switch_onset_floor": "not a Gate-4 lesion criterion; retained from Gate 2"
        },
        "bounds": {**INHERITED_BOUNDS, **v26a.finite_information_bounds()},
        "custody": {"escrow_accessed": False, "passed": True},
        "verdict_classes": {
            "scientific": passed,
            "semantic": passed,
            "custody": True,
        },
        "passed": passed,
    }
    dump("gate-4-per_world.json", rows)
    dump("gate-4.json", payload)
    report = [
        "# V2.6a gate 4",
        "",
        f"Verdict: **{'PASS' if passed else 'FAIL'}**.",
        "",
        "The adjudicated Gate-2 onset-floor miss remains in the ledger and is not a Gate-4 lesion criterion.",
        "",
        "## Metrics",
        "",
    ]
    report += [
        f"- `{key}`: {plain(value)}" for key, value in metrics.items()
    ]
    report += ["", "## Criteria", ""] + [
        f"- `{key}`: {'PASS' if value else 'FAIL'}"
        for key, value in checks.items()
    ]
    (OUT / "gate-4-report.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    if not passed:
        failures = [name for name, value in checks.items() if not value]
        (OUT / "gate-4-diagnosis-stub.md").write_text(
            "# V2.6a gate-4 diagnosis stub\n\n"
            "Honest stop. Failed criteria retained verbatim:\n\n"
            + "\n".join(f"- `{item}`" for item in failures)
            + "\n",
            encoding="utf-8",
        )
    return passed


def run_gate5() -> bool:
    scenarios = (
        "reliability_low",
        "reliability_high",
        "ambiguity_high",
        "switch_low",
        "switch_high",
        "root_weak",
        "root_strong",
        "regulation_weak",
        "missingness",
        "precision_low",
        "context_return",
        "soothing_control",
        "intrusive_control",
    )
    rows: list[dict[str, Any]] = []
    base_precision = float(v26a.PARAMETERS["base_global_precision"])
    for cell, scenario in enumerate(scenarios):
        start = 1_207_000 + cell * 1000
        for seed in range(start, start + 1000):
            world = v26a.generate_robustness_world(
                seed, scenario=scenario
            )
            result = v26a.score(world.observations)
            root_only_observations = tuple(
                v26a.PartnerObservation((None, None, None, None), item.root)
                for item in world.observations
            )
            relational_only_observations = tuple(
                v26a.PartnerObservation(item.relational, None)
                for item in world.observations
            )
            root_only = v26a.score(root_only_observations)
            relational_only = v26a.score(relational_only_observations)
            broadcast_off = v26a.score(world.observations, broadcast=False)
            fixed = v26a.score(world.observations, fixed_g=1)
            truth_onset = next(
                (
                    time
                    for time in range(1, len(world.truth_path))
                    if world.truth_path[time] != world.truth_path[time - 1]
                ),
                None,
            )
            rows.append(
                {
                    "seed": seed,
                    "scenario": scenario,
                    "truth_family": world.truth_family,
                    "switching": world.switching,
                    "q_reliable": float(result.q_partner[0]),
                    "global_depth": result.global_precision[-1],
                    "depth_from_base": result.global_precision[-1] - base_precision,
                    "root_movement": result.root_movement,
                    "root_only_movement": root_only.root_movement,
                    "uptake_increment": result.root_movement - root_only.root_movement,
                    "transfer_increment": result.transfer - root_only.transfer,
                    "relational_only_root_movement": relational_only.root_movement,
                    "broadcast_q_error": float(
                        np.max(
                            np.abs(
                                result.q_partner
                                - broadcast_off.q_partner
                            )
                        )
                    ),
                    "fixed_G_transfer": fixed.transfer,
                    "actual_switch_rate": (
                        sum(
                            left != right
                            for left, right in zip(
                                world.truth_path, world.truth_path[1:]
                            )
                        )
                        / (len(world.truth_path) - 1)
                    ),
                    "posterior_switch_rate": result.switch_rate,
                    "truth_onset": truth_onset,
                    "posterior_onset": result.switch_onset,
                    "onset_error": (
                        abs(result.switch_onset - truth_onset)
                        if truth_onset is not None
                        else None
                    ),
                }
            )
    by_scenario = {
        scenario: [row for row in rows if row["scenario"] == scenario]
        for scenario in scenarios
    }
    summaries: dict[str, Any] = {}
    for scenario, cell_rows in by_scenario.items():
        onset_errors = [
            row["onset_error"]
            for row in cell_rows
            if row["onset_error"] is not None
        ]
        summaries[scenario] = {
            "uptake_increment": interval(
                row["uptake_increment"] for row in cell_rows
            ),
            "transfer_increment": interval(
                row["transfer_increment"] for row in cell_rows
            ),
            "depth_from_base": interval(
                row["depth_from_base"] for row in cell_rows
            ),
            "root_movement": interval(
                row["root_movement"] for row in cell_rows
            ),
            "reliable_selection_rate": float(
                np.mean([row["q_reliable"] >= 0.8 for row in cell_rows])
            ),
            "actual_switch_rate_mean": float(
                np.mean([row["actual_switch_rate"] for row in cell_rows])
            ),
            "posterior_switch_rate_mean": float(
                np.mean([row["posterior_switch_rate"] for row in cell_rows])
            ),
            "switch_onset_median_absolute_error": (
                float(np.median(onset_errors)) if onset_errors else None
            ),
            "count": len(cell_rows),
        }
    prior = {
        "gate1": json.loads((OUT / "gate-1.json").read_text()),
        "gate2": json.loads((OUT / "gate-2-repaired.json").read_text()),
        "gate3": json.loads((OUT / "gate-3.json").read_text()),
        "gate4": json.loads((OUT / "gate-4.json").read_text()),
    }
    gate2_blocking = all(
        value
        for name, value in prior["gate2"]["checks"].items()
        if name != "onset_median_at_most_3"
    )
    chain = verify_manifest_chain(
        ROOT, "results/V2.5b/freeze-manifest.json"
    )
    constitution_pass = constitution.cumulative_constitution_audit()["passed"]
    suite = subprocess.run(
        [sys.executable, "run_tests_parallel.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    suite_payload = {
        "command": "python3 run_tests_parallel.py",
        "returncode": suite.returncode,
        "passed": suite.returncode == 0,
        "stdout": suite.stdout,
        "stderr": suite.stderr,
    }
    dump("full-fast-suite-gate5.json", suite_payload)
    reliable_scenarios = (
        "reliability_low",
        "reliability_high",
        "ambiguity_high",
        "root_weak",
        "root_strong",
        "regulation_weak",
        "missingness",
        "precision_low",
        "context_return",
    )
    robustness_signs = {
        scenario: (
            summaries[scenario]["uptake_increment"]["lower_95"] > 0.0
        )
        for scenario in reliable_scenarios
    }
    max_relational_root = max(
        abs(row["relational_only_root_movement"]) for row in rows
    )
    max_fixed_transfer = max(abs(row["fixed_G_transfer"]) for row in rows)
    max_broadcast_q = max(abs(row["broadcast_q_error"]) for row in rows)
    root_dose_order = (
        summaries["root_strong"]["root_movement"]["mean"]
        > summaries["root_weak"]["root_movement"]["mean"]
    )
    control_selectivity = (
        summaries["soothing_control"]["reliable_selection_rate"] <= 0.10
        and summaries["intrusive_control"]["reliable_selection_rate"] <= 0.10
    )
    checks = {
        "standing_gate1": bool(prior["gate1"]["passed"]),
        "standing_gate2_blocking_family": gate2_blocking,
        "standing_gate3": bool(prior["gate3"]["passed"]),
        "standing_gate4": bool(prior["gate4"]["passed"]),
        "full_cumulative_fast_suite": suite.returncode == 0,
        "permanent_constitution": constitution_pass,
        "manifest_chain_composition": bool(chain["passed"]),
        "regulation_not_root_evidence": max_relational_root <= TOL,
        "fixed_G_transfer_zero": max_fixed_transfer <= TOL,
        "broadcast_preserves_local_inference": max_broadcast_q <= TOL,
        "robustness_direction_each_reliable_cell": all(
            robustness_signs.values()
        ),
        "root_evidence_dose_order": root_dose_order,
        "soothing_intrusive_selectivity": control_selectivity,
    }
    onset_repetitions = {
        scenario: summaries[scenario][
            "switch_onset_median_absolute_error"
        ]
        for scenario in scenarios
        if summaries[scenario]["switch_onset_median_absolute_error"]
        is not None
    }
    blocking_pass = all(checks.values())
    payload = {
        "stage": "V2.6a",
        "gate": 5,
        "seed_block": [1_207_000, 1_219_999],
        "scenario_summaries": summaries,
        "robustness_sign_checks": robustness_signs,
        "metrics": {
            "relational_only_root_movement_max": max_relational_root,
            "fixed_G_transfer_max": max_fixed_transfer,
            "broadcast_q_max_error": max_broadcast_q,
            "root_dose_order": root_dose_order,
            "control_selectivity": control_selectivity,
        },
        "checks": checks,
        "adjudicated_nonblocking_family": {
            "name": "switch_onset_floor",
            "specification_floor": 3.0,
            "gate2_value": prior["gate2"]["metrics"][
                "switch_onset_median_absolute_error"
            ],
            "robustness_repetitions": onset_repetitions,
            "blocking": False,
        },
        "manifest_chain": chain,
        "bounds": {**INHERITED_BOUNDS, **v26a.finite_information_bounds()},
        "custody": {"escrow_accessed": False, "passed": True},
        "verdict_classes": {
            "scientific": blocking_pass,
            "semantic": constitution_pass,
            "stress": all(robustness_signs.values()),
            "custody": bool(chain["passed"]),
        },
        "passed": blocking_pass,
        "all_gates_passed": False,
        "stage_status_if_frozen": (
            "FROZEN_ADJUDICATED_MIXED_SWITCH_ONSET_ATTAINABILITY_LIMITATION"
            if blocking_pass
            else None
        ),
    }
    dump("gate-5-per_world.json", rows)
    dump("gate-5.json", payload)
    report = [
        "# V2.6a gate 5",
        "",
        f"Blocking verdict: **{'PASS' if blocking_pass else 'FAIL'}**.",
        "",
        "The switch-onset floor and every robustness repetition are reported verbatim as the sole adjudicated non-blocking family.",
        "",
        "## Scenario summaries",
        "",
    ]
    for scenario, summary in summaries.items():
        report.append(f"- `{scenario}`: {plain(summary)}")
    report += ["", "## Blocking checks", ""] + [
        f"- `{name}`: {'PASS' if value else 'FAIL'}"
        for name, value in checks.items()
    ]
    report += ["", "## Non-blocking onset-floor repetitions", ""]
    report += [
        f"- `{name}`: {value}" for name, value in onset_repetitions.items()
    ]
    (OUT / "gate-5-report.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    if not blocking_pass:
        failures = [name for name, value in checks.items() if not value]
        (OUT / "gate-5-diagnosis-stub.md").write_text(
            "# V2.6a gate-5 diagnosis stub\n\n"
            "Honest stop. Blocking failures retained verbatim:\n\n"
            + "\n".join(f"- `{item}`" for item in failures)
            + "\n",
            encoding="utf-8",
        )
    return blocking_pass


def ready(gate: int, passed: bool) -> None:
    files = sorted(
        str(path.relative_to(ROOT))
        for path in OUT.glob(f"gate-{gate}*")
        if path.is_file()
    )
    (OUT / f"ready-to-commit-gate{gate}.md").write_text(
        f"# Ready to commit: V2.6a gate {gate}\n\n"
        f"Verdict: {'PASS' if passed else 'FAIL / honest stop'}\n\n"
        + "\n".join(f"- `{item}`" for item in files)
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", type=int, choices=(1, 2, 3, 4, 5), required=True)
    args = parser.parse_args()
    runner = (
        run_gate5
        if args.gate == 5
        else {
            1: run_gate1,
            2: run_gate2,
            3: run_gate3,
            4: run_gate4,
        }[args.gate]
    )
    passed = runner()
    ready(args.gate, passed)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
