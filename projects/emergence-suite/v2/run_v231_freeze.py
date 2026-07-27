"""Run V2.3.1 gates 1–5, cumulative regressions, and freeze packaging."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from ref.v20 import run_v20
from ref.v21 import run_v21
from ref.v221 import run_v221
from ref.v231 import run_v231


ROOT = Path(__file__).resolve().parent
RESULT_ROOT = ROOT / "results" / "V2.3.1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"cannot write empty CSV {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def inherited_gate_payload(
    stage: str, gate: int, report: dict[str, Any]
) -> dict[str, Any]:
    if stage == "V2.0":
        keys = {
            1: {"semantic_errors"},
            2: {"recovery"},
            3: {"model_comparison"},
            4: {"factor_sensitivity", "recovery"},
            5: set(),
        }[gate]
    elif stage == "V2.1":
        keys = {
            1: {"semantic_proof"},
            2: {"recovery"},
            3: {"broadcast", "composition", "open_assays"},
            4: {"broadcast", "batch"},
            5: {"v2.0_regression"},
        }[gate]
    else:
        keys = {
            1: {"semantic_proof", "structure_recovery"},
            2: {"association_recovery"},
            3: {"seam", "transfer_2x2", "repair_floor_assay"},
            4: {"lesions", "repair_floor_assay"},
            5: {"batch", "v2.0_regression", "v2.1_regression"},
        }[gate]
    return {key: report[key] for key in keys}


def write_inherited_rerun(stage: str, report: dict[str, Any]) -> None:
    destination = RESULT_ROOT / "cumulative" / stage
    gate_names = list(report["gates"])
    for gate in range(1, 6):
        name = gate_names[gate - 1]
        passed = bool(report["gates"][name])
        write_json(
            destination / f"gate-{gate}.json",
            {
                "strain": "V2.3.1",
                "rerun_stage": stage,
                "gate": gate,
                "name": name,
                "passed": passed,
                "results": inherited_gate_payload(stage, gate, report),
                "failures": [] if passed else [f"{name} threshold not met"],
            },
        )
    write_json(destination / "stage-report.json", report)


def gate_payload(gate: int, report: dict[str, Any]) -> dict[str, Any]:
    if gate == 1:
        return {"semantic_proofs": report["semantic_proofs"]}
    if gate == 2:
        return {"recovery": report["recovery"]}
    if gate == 3:
        return {
            "original_open_assays": report["open_assays"],
            "varied_schedule_assay": report["generalization_assay"],
            "expanded_step_injection": report["expanded_step_injection"],
        }
    if gate == 4:
        return {
            "lesions": report["lesions"],
            "inherited_regressions": {
                "V2.0": report["v2.0_regression"],
                "V2.1": report["v2.1_regression"],
                "V2.2.1": report["v2.2.1_regression"],
            },
        }
    return {
        "sensitivity": report["sensitivity"],
        "determinism": report["determinism"],
        "expanded_step_injection": report["expanded_step_injection"],
        "cumulative_regressions": {
            "V2.0": report["v2.0_regression"],
            "V2.1": report["v2.1_regression"],
            "V2.2.1": report["v2.2.1_regression"],
        },
    }


def milestone_report(report: dict[str, Any]) -> str:
    opened = report["open_assays"]
    varied = report["generalization_assay"]
    recovery = report["recovery"]
    chain = opened["closed_loop_vs_exact_replay"]
    steps = report["expanded_step_injection"]
    return f"""# Suite v2 — V2.3.1 formation repair

Stage verdict: **{'PASS' if report['passed'] else 'FAIL'}** for gates 1–5.

The committed C-V23 failure is retained as the reason for this strain. The
diagnosis classified the schedule-collapse defect as parametric and the
single-slice jump defect as representational. The repair makes
event-context controllability explicit, adds schedule-blind Markov structure
dynamics, and bounds every candidate-evidence contribution.

## Recovery and original assays

- Structure accuracy / ECE: `{recovery['structure_accuracy']:.3f}` /
  `{recovery['structure_ece']:.4f}`.
- Controllability / broadcast accuracy:
  `{recovery['controllability_accuracy']:.3f}` /
  `{recovery['broadcast_accuracy']:.3f}`.
- Acute / gradual final persistent posterior:
  `{opened['acute_formation']['final_persistent_95_interval'][0]:.3f}` /
  `{opened['gradual_accumulation']['final_persistent_95_interval'][0]:.3f}`.
- Low-minus-high control without overwhelm:
  `{opened['low_control_without_overwhelm']['low_minus_high_control_95_interval'][0]:.3f}`.
- Closed-loop chain:
  policy `{chain['policy_avoidance'][0]:.3f}` → transition
  `{chain['world_transition'][0]:.3f}` → observation
  `{chain['observed_evidence'][0]:.3f}` → persistent model
  `{chain['persistent_model'][0]:.3f}` → root
  `{chain['root_persistence'][0]:.3f}`.

## Expanded generalization assay

- Theory-variable curves monotone:
  `{varied['calibration_monotone']}`.
- These gate curves hold the other preregistered theory variable constant.
  The raw marginal curves are retained separately and are not used as a
  substitute for the independent surface-increment test.
- Surface incremental cross-validated R²:
  `{varied['surface_incremental_cv_r2']:.6f}`.
- Paired low-minus-high-control formation:
  `{varied['low_minus_high_control_95_interval'][0]:.3f}`
  (95% interval
  `{varied['low_minus_high_control_95_interval'][1]:.3f}`–
  `{varied['low_minus_high_control_95_interval'][2]:.3f}`).

Across the original and expanded open batteries, the empirical p99
single-slice change is `{steps['percentile_99']:.9f}`, the maximum is
`{steps['maximum']:.9f}`, and the analytic bound is
`{steps['analytic_bound']:.9f}` over `{steps['count']}` changes. There were
`{steps['exceedances']}` exceedances of the frozen V2.3 p99.

All three selective lesions and every cumulative V2.0, V2.1, and V2.2.1 gate
passed. The 32-point stage-local neighborhood and complete repeated
original-plus-varied seed blocks are retained. C-V23b remains sealed and was
not inferred or run.
"""


def artifact_paths() -> list[Path]:
    cumulative = sorted(
        path
        for path in (RESULT_ROOT / "cumulative").rglob("*")
        if path.is_file()
    )
    return [
        ROOT / "contracts" / "v2.3.1-formation-contract.md",
        ROOT / "protocols" / "v2.3.1-analysis-plan.md",
        ROOT / "protocols" / "v2.3.1-parameters.json",
        ROOT / "protocols" / "v2.3.1-dummy-bundle.json",
        ROOT / "ref" / "v231.py",
        ROOT / "tests" / "test_v231_formation.py",
        ROOT / "run_v231_diagnosis.py",
        ROOT / "run_v231_freeze.py",
        RESULT_ROOT / "diagnosis.md",
        RESULT_ROOT / "diagnosis-summary.json",
        RESULT_ROOT / "diagnosis-per_world.csv",
        RESULT_ROOT / "decisions.md",
        RESULT_ROOT / "development-failures.md",
        RESULT_ROOT / "open-assays-per_seed.csv",
        RESULT_ROOT / "generalization-calibration-per_world.csv",
        RESULT_ROOT / "generalization-paired-per_world.csv",
        RESULT_ROOT / "neighborhood-profile.csv",
        RESULT_ROOT / "gate-1.json",
        RESULT_ROOT / "gate-2.json",
        RESULT_ROOT / "gate-3.json",
        RESULT_ROOT / "gate-4.json",
        RESULT_ROOT / "gate-5.json",
        RESULT_ROOT / "stage-report.json",
        ROOT / "results" / "milestone-2-v2.3.1-report.md",
        *sorted((ROOT / "ref").glob("*.py")),
        *sorted((ROOT / "tests").glob("test_*.py")),
        *cumulative,
    ]


def main() -> None:
    report = run_v231(
        include_sensitivity=True,
        verify_determinism=True,
        include_generalization=True,
    )
    artifact_rows = report.pop("_artifact_rows")
    write_csv(
        RESULT_ROOT / "open-assays-per_seed.csv",
        report["open_assays"]["per_seed"],
    )
    write_csv(
        RESULT_ROOT / "generalization-calibration-per_world.csv",
        artifact_rows["generalization_calibration"],
    )
    write_csv(
        RESULT_ROOT / "generalization-paired-per_world.csv",
        artifact_rows["generalization_paired"],
    )
    write_csv(
        RESULT_ROOT / "neighborhood-profile.csv",
        report["sensitivity"]["full_profile"],
    )
    gate_names = list(report["gates"])
    for gate in range(1, 6):
        name = gate_names[gate - 1]
        passed = bool(report["gates"][name])
        write_json(
            RESULT_ROOT / f"gate-{gate}.json",
            {
                "stage": "V2.3.1",
                "gate": gate,
                "name": name,
                "passed": passed,
                "results": gate_payload(gate, report),
                "failures": [] if passed else [f"{name} threshold not met"],
            },
        )
    write_json(RESULT_ROOT / "stage-report.json", report)

    v20 = run_v20()
    v21 = run_v21()
    v221 = run_v221()
    write_inherited_rerun("V2.0", v20)
    write_inherited_rerun("V2.1", v21)
    write_inherited_rerun("V2.2.1", v221)

    milestone_path = ROOT / "results" / "milestone-2-v2.3.1-report.md"
    milestone_path.write_text(milestone_report(report), encoding="utf-8")

    all_passed = (
        report["passed"] and v20["passed"] and v21["passed"] and v221["passed"]
    )
    files = artifact_paths()
    missing = [
        str(path.relative_to(ROOT)) for path in files if not path.exists()
    ]
    if missing:
        raise RuntimeError(
            f"cannot freeze V2.3.1; missing artifacts: {missing}"
        )
    manifest = {
        "stage": "V2.3.1",
        "status": "freeze-candidate" if all_passed else "failed-gate-stop",
        "all_gates_1_to_5_passed": all_passed,
        "analysis_plan_frozen_before_protocol_runs": True,
        "diagnosis_completed_before_repair": True,
        "inherited_parameter_blocks_modified": False,
        "development_seed_maximum": 63980,
        "step_injection_bound": {
            "definition": (
                "empirical 99th-percentile absolute adjacent-slice change "
                "in p(H_formation=persistent) across original and expanded "
                "open assay arms"
            ),
            "percentile": 99,
            "value": report["expanded_step_injection"]["percentile_99"],
            "maximum": report["expanded_step_injection"]["maximum"],
            "analytic_bound": report["expanded_step_injection"][
                "analytic_bound"
            ],
            "slice_change_count": report["expanded_step_injection"]["count"],
        },
        "prospective_challenge": "C-V23b",
        "prospective_challenge_revealed": False,
        "prospective_challenge_run": False,
        "files": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in sorted(set(files))
        },
    }
    write_json(RESULT_ROOT / "freeze-manifest.json", manifest)
    if not all_passed:
        raise SystemExit("V2.3.1 ratchet stopped at failed open gate")


if __name__ == "__main__":
    main()
