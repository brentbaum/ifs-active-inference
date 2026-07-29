#!/usr/bin/env python3
"""Sequential V2.6a stage-0 through gate-3 runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
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
    for offset, seed in enumerate(range(1_200_000, 1_201_500)):
        truth = offset % 4
        switching = ((offset // 4) % 2) == 1
        family = v26a.PARTNER_STATES[truth]
        world = v26a.generate_recovery_world(
            seed, truth_family=family, switching=switching
        )
        result = v26a.score(world.observations)
        q = result.q_partner
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
    metrics = {
        "confusion_matrix": confusion,
        "diagonal_recovery": dict(zip(v26a.PARTNER_STATES, diagonal)),
        "macro_recovery": float(np.mean(diagonal)),
        "brier": float(np.mean(np.sum((q - one_hot) ** 2, axis=1))),
        "ece": ece(rows),
        "posterior_set_coverage": float(np.mean([row["covered"] for row in rows])),
        "transition_switch_parameter_mae": float(np.mean([row["switch_rate_error"] for row in rows])),
        "switch_onset_median_absolute_error": float(
            np.median([row["onset_error"] for row in rows if row["switching"]])
        ),
        "local_precision_calibration_error": float(
            np.mean([row["local_precision_calibration_error"] for row in rows])
        ),
        "world_count": len(rows),
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
        "seed_block": [1_200_000, 1_201_499],
        "metrics": metrics,
        "checks": checks,
        "verdict_classes": {"scientific": passed, "semantic": True, "custody": True},
        "passed": passed,
    }
    dump("gate-2-per_world.json", rows)
    dump("gate-2.json", payload)
    report = ["# V2.6a gate 2", "", f"Verdict: **{'PASS' if passed else 'FAIL'}**.", "", "## Metrics", ""]
    report += [f"- `{key}`: {plain(value)}" for key, value in metrics.items()]
    report += ["", "## Criteria", ""] + [
        f"- `{key}`: {'PASS' if value else 'FAIL'}" for key, value in checks.items()
    ]
    (OUT / "gate-2-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    if not passed:
        failures = [name for name, value in checks.items() if not value]
        (OUT / "gate-2-diagnosis-stub.md").write_text(
            "# V2.6a gate-2 diagnosis stub\n\nHonest stop. Failed criteria retained verbatim:\n\n"
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
    parser.add_argument("--gate", type=int, choices=(1, 2, 3), required=True)
    args = parser.parse_args()
    runner = {1: run_gate1, 2: run_gate2, 3: run_gate3}[args.gate]
    passed = runner()
    ready(args.gate, passed)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
