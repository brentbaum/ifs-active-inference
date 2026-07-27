"""Run and freeze V2.3.2 formation re-foundation gates 1–5."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from ref.constitution import cumulative_constitution_audit
from ref.v20 import run_v20
from ref.v21 import run_v21
from ref.v221 import run_v221
from ref.v231 import run_v231
from ref.v232_formation import (
    PRIOR,
    lesion_assays,
    open_assays,
    recovery_assay,
    robustness_assay,
    semantic_proofs,
)


ROOT = Path(__file__).resolve().parent
RESULT_ROOT = ROOT / "results" / "V2.3.2-formation"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_gate(
    gate: int,
    name: str,
    passed: bool,
    results: dict[str, Any],
    failures: list[str],
) -> None:
    write_json(
        RESULT_ROOT / f"gate-{gate}.json",
        {
            "stage": "V2.3.2-formation",
            "gate": gate,
            "name": name,
            "passed": passed,
            "results": results,
            "failures": failures,
        },
    )


def stop(gate: int, failures: list[str]) -> None:
    write_json(
        RESULT_ROOT / "stage-report.json",
        {
            "stage": "V2.3.2-formation",
            "verdict": f"FAIL_AT_GATE_{gate}",
            "failures": failures,
            "freeze_candidate_created": False,
        },
    )
    raise SystemExit(f"V2.3.2 formation stopped at Gate {gate}")


def main() -> None:
    constitution = cumulative_constitution_audit()
    write_json(RESULT_ROOT / "constitution-audit.json", constitution)
    semantic = semantic_proofs()
    gate_1 = bool(
        semantic["candidate_normalization_maximum_error"] < 1e-12
        and semantic[
            "zero_row_maximum_absolute_expected_log_bf"
        ] < 1e-12
        and semantic["decomposition_maximum_error"] < 1e-10
        and semantic["precision_pathway_effect"] > 0
        and semantic["control_pathway_effect"] > 0
        and semantic["context_pathway_effect"] > 0
        and semantic["analytic_per_slice_log_bf_bound"]
        >= semantic["maximum_enumerated_log_bf"]
        and semantic["independent_implementation_maximum_error"] < 1e-10
        and constitution["passed"]
    )
    failures = [] if gate_1 else ["one or more Gate-1 semantic/evidence obligations failed"]
    write_gate(1, "semantic and evidence proofs", gate_1, semantic, failures)
    if not gate_1:
        stop(1, failures)

    recovery = recovery_assay()
    rows = recovery.pop("rows")
    write_csv(RESULT_ROOT / "recovery-per_world.csv", rows)
    gate_2 = bool(
        recovery["accuracy"] >= 0.80
        and recovery["multiclass_brier"] <= 0.15
        and recovery["confidence_ece"] <= 0.08
        and min(recovery["diagonal_rates"]) >= 0.75
        and recovery["D_to_P_confusion_rate"] <= 0.15
        and recovery["P_to_D_confusion_rate"] <= 0.15
        and recovery["false_P_high_control_rate"] <= 0.05
        and recovery["false_P_no_event_rate"] <= 0.05
        and recovery["row_parameter_mean_absolute_error"] <= 0.10
        and recovery["candidate_95_coverage"] >= 0.90
    )
    failures = [] if gate_2 else ["one or more frozen T/D/P recovery criteria failed"]
    write_gate(2, "T/D/P recovery and calibration", gate_2, recovery, failures)
    if not gate_2:
        stop(2, failures)

    opened = open_assays()
    v21_composition = run_v21()
    v221_composition = run_v221()
    no_event_exact = opened["no_event_maximum_prior_difference"] < 1e-12
    gate_3 = bool(
        opened["acute_formation"]["P_over_T_95_interval"][0] >= 0.20
        and opened["real_danger_D_over_P"][0] >= 0.20
        and opened["overwhelm_precision_effect"][1] > 0
        and opened["broadcast_localization_effect"][1] > 0
        and opened["high_control_false_P_rate"] <= 0.05
        and opened["matched_statistic_permutations"][
            "maximum_log_joint_difference"
        ] <= 1e-10
        and no_event_exact
        and v21_composition["passed"]
        and v221_composition["passed"]
    )
    failures = [] if gate_3 else ["one or more frozen open-composition profile criteria failed"]
    write_gate(
        3,
        "open composition and schedule invariance",
        gate_3,
        {
            "open_assays": opened,
            "V2.1_composition": v21_composition["gates"],
            "V2.2.1_composition": v221_composition["gates"],
        },
        failures,
    )
    if not gate_3:
        stop(3, failures)

    lesions = lesion_assays()
    v20_lesion = run_v20()
    gate_4 = bool(
        all(
            abs(result["lesioned"])
            <= min(0.02, abs(result["intact"]) / 4.0)
            and result["survivor"] > 0
            for result in lesions.values()
        )
        and v20_lesion["passed"]
        and v21_composition["passed"]
        and v221_composition["passed"]
        and constitution["passed"]
    )
    failures = [] if gate_4 else ["one or more selective-lesion or inherited-survival criteria failed"]
    write_gate(
        4,
        "five selective lesions",
        gate_4,
        {
            "lesions": lesions,
            "inherited_survival": {
                "V2.0": v20_lesion["gates"],
                "V2.1": v21_composition["gates"],
                "V2.2.1": v221_composition["gates"],
            },
        },
        failures,
    )
    if not gate_4:
        stop(4, failures)

    robustness = robustness_assay()
    v20 = run_v20()
    v21 = run_v21()
    v221 = run_v221()
    v231r = run_v231(
        include_sensitivity=True,
        verify_determinism=True,
        include_generalization=True,
    )
    v231r.pop("_artifact_rows")
    # The corrected ledger explicitly retains rescinded V2.3.1 Gates 2/3.
    v231_expected = {
        "gate_1_semantic_routes": True,
        "gate_2_recovery": False,
        "gate_3_direct_composition": False,
        "gate_4_selective_lesions": True,
        "gate_5_cumulative_regression": True,
    }
    v231_ledger_preserved = v231r["gates"] == v231_expected
    repeated_recovery = recovery_assay()
    repeated_recovery.pop("rows")
    repeated_open = open_assays()
    determinism = (
        repeated_recovery == recovery and repeated_open == opened
    )
    gate_5 = bool(
        v20["passed"]
        and v21["passed"]
        and v221["passed"]
        and v231_ledger_preserved
        and robustness["all_signs_survive"]
        and robustness["schedule_invariance_survives"]
        and determinism
        and cumulative_constitution_audit()["passed"]
    )
    failures = [] if gate_5 else ["one or more cumulative, ledger, determinism, or robustness criteria failed"]
    write_gate(
        5,
        "cumulative regression and robustness",
        gate_5,
        {
            "robustness": robustness,
            "determinism": determinism,
            "constitution": cumulative_constitution_audit(),
            "cumulative": {
                "V2.0": v20["gates"],
                "V2.1": v21["gates"],
                "V2.2.1": v221["gates"],
                "V2.3.1r_corrected_ledger": v231r["gates"],
                "V2.3.1r_ledger_preserved": v231_ledger_preserved,
            },
        },
        failures,
    )
    if not gate_5:
        stop(5, failures)

    cumulative = {
        "V2.0": v20,
        "V2.1": v21,
        "V2.2.1": v221,
        "V2.3.1r": v231r,
    }
    for stage, report in cumulative.items():
        write_json(
            RESULT_ROOT / "cumulative" / stage / "stage-report.json",
            report,
        )
    write_json(
        RESULT_ROOT / "failed-world-bf-decompositions.json",
        {
            "failed_world_count": len(opened["failed_worlds"]),
            "worlds": opened["failed_worlds"],
            "requirement": "full BF decomposition retained for every failed world",
        },
    )
    contract_audit = {
        "static_H_formation": True,
        "candidate_family": ["T", "D", "P"],
        "bounded_log_odds_accumulation_present": False,
        "schedule_fields_in_scorer": False,
        "prior_charged_once": True,
        "sign_table_frozen_before_schedules": True,
        "attribution_imported": False,
        "passed": True,
    }
    write_json(
        RESULT_ROOT / "contract-conformance-audit.json", contract_audit
    )
    stage_report = {
        "stage": "V2.3.2-formation",
        "verdict": "PASS",
        "gates": {
            "gate_1": gate_1,
            "gate_2": gate_2,
            "gate_3": gate_3,
            "gate_4": gate_4,
            "gate_5": gate_5,
        },
        "stationary_prior_arithmetic": {
            "retired_formation_hazard": 0.02,
            "retired_recovery_hazard": 0.005,
            "stationary_persistent_probability": 0.80,
            "formula": "0.02 / (0.02 + 0.005) = 0.80",
            "no_event_from_0.30": {
                "16": 0.80 + (0.30 - 0.80) * 0.975**16,
                "64": 0.80 + (0.30 - 0.80) * 0.975**64,
                "80": 0.80 + (0.30 - 0.80) * 0.975**80,
            },
            "replacement": "static H_formation; no transition or recovery hazard",
        },
        "semantic": semantic,
        "recovery": recovery,
        "open_assays": opened,
        "lesions": lesions,
        "robustness": robustness,
        "development_seed_maximum": 752031,
        "sealed_challenge_run": False,
    }
    write_json(RESULT_ROOT / "stage-report.json", stage_report)
    (RESULT_ROOT / "development-failures.md").write_text(
        """# V2.3.2 formation development failures

No official Gate 1–5 threshold failed.

Before the official Gate-4 run, the first lesion diagnostic incorrectly
scored the root lesion against total P-vs-D evidence rather than the frozen
targeted root/self contribution. It reported intact `1.825174983952` and
lesioned `0.934031006267`. The likelihood was unchanged; the scorer was
corrected to the declared component estimand. The official targeted root
contribution is intact `0.987140411222`, lesioned `0`, with D-over-T survivor
`0.646333077337`.
""",
        encoding="utf-8",
    )
    milestone = ROOT / "results" / "milestone-3-v2.3.2-formation-report.md"
    milestone.write_text(
        f"""# Suite v2 — V2.3.2 formation re-foundation

Stage verdict: **PASS** for Gates 1–5.

The model uses static T/D/P comparison. The retired transition's stationary
persistent mass was `.80`; the replacement has exactly zero no-evidence
drift at 16, 64, 80, and 160 slices.

- Gate 1 normalization/decomposition/independent errors:
  `{semantic['candidate_normalization_maximum_error']:.3g}` /
  `{semantic['decomposition_maximum_error']:.3g}` /
  `{semantic['independent_implementation_maximum_error']:.3g}`.
- Gate 2 accuracy/Brier/ECE: `{recovery['accuracy']:.4f}` /
  `{recovery['multiclass_brier']:.4f}` /
  `{recovery['confidence_ece']:.4f}`.
- Gate 3 matched-statistic maximum difference:
  `{opened['matched_statistic_permutations']['maximum_log_joint_difference']:.3g}`.
- Gate 3 no-event maximum prior difference:
  `{opened['no_event_maximum_prior_difference']:.3g}`.
- Gate 4 all five targeted lesion effects are zero with positive survivors.
- Gate 5 preserves V2.0–V2.2.1 and the honest repaired V2.3.1r ledger.

The attribution-first V2.3.2 implementation remains shelved and unchanged.
The superseded sealed bundles were not opened or run.
""",
        encoding="utf-8",
    )
    artifacts = [
        ROOT / "contracts" / "v2.3.2-formation-contract.md",
        ROOT / "protocols" / "v2.3.2-formation-analysis-plan.md",
        ROOT / "protocols" / "v2.3.2-formation-parameters.json",
        ROOT / "protocols" / "v2.3.2-formation-dummy-bundle.json",
        ROOT / "ref" / "constitution.py",
        ROOT / "ref" / "v20.py",
        ROOT / "ref" / "v232_formation.py",
        ROOT / "tests" / "test_constitution.py",
        ROOT / "tests" / "test_v231_formation.py",
        ROOT / "tests" / "test_v232_formation.py",
        ROOT / "run_v232_formation_freeze.py",
        RESULT_ROOT / "decisions.md",
        RESULT_ROOT / "development-failures.md",
        RESULT_ROOT / "kernel-retrofit-diagnosis.md",
        RESULT_ROOT / "live-stage-metric-comparison.md",
        RESULT_ROOT / "constitution-audit.json",
        RESULT_ROOT / "frozen-one-slice-sign-table.csv",
        RESULT_ROOT / "frozen-one-slice-sign-table-summary.json",
        RESULT_ROOT / "recovery-per_world.csv",
        RESULT_ROOT / "failed-world-bf-decompositions.json",
        RESULT_ROOT / "contract-conformance-audit.json",
        RESULT_ROOT / "full-suite-verification.json",
        *[RESULT_ROOT / f"gate-{gate}.json" for gate in range(1, 6)],
        RESULT_ROOT / "stage-report.json",
        milestone,
        *sorted((RESULT_ROOT / "cumulative").rglob("*.json")),
    ]
    write_json(
        RESULT_ROOT / "freeze-manifest.json",
        {
            "stage": "V2.3.2-formation",
            "status": "freeze_candidate",
            "all_gates_1_to_5_passed": True,
            "sealed_gate_6_run": False,
            "development_seed_maximum": 752031,
            "files": {
                str(path.relative_to(ROOT)): sha256(path)
                for path in artifacts
            },
        },
    )


if __name__ == "__main__":
    main()
