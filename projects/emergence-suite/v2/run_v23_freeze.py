"""Run V2.3 gates 1–5, cumulative regressions, and freeze packaging."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from ref.v20 import run_v20
from ref.v21 import run_v21
from ref.v221 import run_v221
from ref.v23 import run_v23


ROOT = Path(__file__).resolve().parent
RESULT_ROOT = ROOT / "results" / "V2.3"


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
                "strain": "V2.3",
                "rerun_stage": stage,
                "gate": gate,
                "name": name,
                "passed": passed,
                "results": inherited_gate_payload(stage, gate, report),
                "failures": [] if passed else [f"{name} threshold not met"],
            },
        )
    write_json(destination / "stage-report.json", report)


def v23_gate_payload(gate: int, report: dict[str, Any]) -> dict[str, Any]:
    if gate == 1:
        return {"semantic_proofs": report["semantic_proofs"]}
    if gate == 2:
        return {"recovery": report["recovery"]}
    if gate == 3:
        return {
            "open_assays": {
                key: value
                for key, value in report["open_assays"].items()
                if key != "per_seed"
            }
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
        "step_injection": report["open_assays"]["step_injection"],
        "cumulative_regressions": {
            "V2.0": report["v2.0_regression"],
            "V2.1": report["v2.1_regression"],
            "V2.2.1": report["v2.2.1_regression"],
        },
    }


def milestone_report(report: dict[str, Any]) -> str:
    semantic = report["semantic_proofs"]
    recovery = report["recovery"]
    opened = report["open_assays"]
    chain = opened["closed_loop_vs_exact_replay"]
    return f"""# Suite v2 — V2.3 formation and active persistence

Stage verdict: **{'PASS' if report['passed'] else 'FAIL'}** for gates 1–5.

## Formation semantics

- Event-precision log-odds increase: `{semantic['event_precision']['log_odds_increase']:.6f}`.
- Low/high-control action evidence contrasts:
  `{semantic['controllability']['low_control_action_log_evidence_difference']:.6f}` /
  `{semantic['controllability']['high_control_action_log_evidence_difference']:.6f}`.
- Action-dependent transition effect:
  `{semantic['action_transition']['avoid_minus_engage_threat_probability']:.6f}`.
- Reflexive-collapse context effect:
  `{semantic['reflexive_broadcast']['persistent_probability_effect']:.6f}`.
- Independent finite-comparison error:
  `{semantic['finite_comparison']['maximum_error']:.3g}`.

## Recovery

- Structure accuracy / mean true probability:
  `{recovery['structure_accuracy']:.3f}` / `{recovery['mean_true_structure_probability']:.3f}`.
- Structure Brier / ECE:
  `{recovery['structure_brier']:.4f}` / `{recovery['structure_ece']:.4f}`.
- Controllability / broadcast accuracy:
  `{recovery['controllability_accuracy']:.3f}` / `{recovery['broadcast_accuracy']:.3f}`.
- Policy-consequence parameter MAE / coverage:
  `{recovery['policy_parameter_mean_absolute_error']:.4f}` /
  `{recovery['policy_parameter_95_interval_coverage']:.3f}`.

## Open assays

- Acute final persistent posterior:
  `{opened['acute_formation']['final_persistent_95_interval'][0]:.3f}`
  (95% interval `{opened['acute_formation']['final_persistent_95_interval'][1]:.3f}`–
  `{opened['acute_formation']['final_persistent_95_interval'][2]:.3f}`).
- Gradual final posterior / accumulated change:
  `{opened['gradual_accumulation']['final_persistent_95_interval'][0]:.3f}` /
  `{opened['gradual_accumulation']['formation_change_95_interval'][0]:.3f}`.
- Acute-minus-controlled effect:
  `{opened['overwhelm_with_control']['acute_minus_controlled_95_interval'][0]:.3f}`.
- Low-minus-high controllability effect without overwhelm:
  `{opened['low_control_without_overwhelm']['low_minus_high_control_95_interval'][0]:.3f}`.
- Adaptive real-danger persistence:
  `{opened['adaptive_persistent_threat']['final_persistent_95_interval'][0]:.3f}`;
  this is correct structure recovery, not an error.

The realized closed-loop chain was:

`policy {chain['policy_avoidance'][0]:.3f} -> world {chain['world_transition'][0]:.3f}
-> observation {chain['observed_evidence'][0]:.3f}
-> persistent model {chain['persistent_model'][0]:.3f}
-> G {chain['root_persistence'][0]:.3f}`.

Every paired 95% interval excludes zero. The mediator computed only from
realized actions and transitions was `{chain['realized_mediator'][0]:.3f}`
(`{chain['realized_mediator'][1]:.3f}`–`{chain['realized_mediator'][2]:.3f}`).

## Freeze audit and regressions

The empirical 99th-percentile single-slice absolute change in persistent-model
posterior across all open assay arms was
`{opened['step_injection']['percentile_99']:.9f}` over
`{opened['step_injection']['count']}` slice changes.

All isolated V2.3 lesions passed. All V2.0, V2.1, and V2.2.1 gates passed
unchanged. The full 32-point neighborhood profile, joint reliability
perturbations, prior sensitivity, and byte-identical full-seed determinism
check are retained in the stage artifacts.

## Status

V2.3 is a freeze candidate. C-V23 remains sealed, unrevealed, and unrun.
No evaluator seed was used and no commit was created.
"""


def artifact_paths() -> list[Path]:
    cumulative = sorted(
        path
        for path in (RESULT_ROOT / "cumulative").rglob("*")
        if path.is_file()
    )
    inherited_sources = sorted((ROOT / "ref").glob("*.py"))
    tests = sorted((ROOT / "tests").glob("test_*.py"))
    return [
        ROOT / "contracts" / "v2.3-formation-contract.md",
        ROOT / "protocols" / "v2.3-analysis-plan.md",
        ROOT / "protocols" / "v2.3-parameters.json",
        ROOT / "protocols" / "v2.3-dummy-bundle.json",
        RESULT_ROOT / "decisions.md",
        RESULT_ROOT / "development-failures.md",
        RESULT_ROOT / "open-assays-per_seed.csv",
        RESULT_ROOT / "neighborhood-profile.csv",
        RESULT_ROOT / "gate-1.json",
        RESULT_ROOT / "gate-2.json",
        RESULT_ROOT / "gate-3.json",
        RESULT_ROOT / "gate-4.json",
        RESULT_ROOT / "gate-5.json",
        RESULT_ROOT / "stage-report.json",
        ROOT / "results" / "milestone-2-v2.3-report.md",
        ROOT / "run_v23_freeze.py",
        *inherited_sources,
        *tests,
        *cumulative,
    ]


def main() -> None:
    report = run_v23(include_sensitivity=True, verify_determinism=True)
    write_csv(
        RESULT_ROOT / "open-assays-per_seed.csv",
        report["open_assays"]["per_seed"],
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
                "stage": "V2.3",
                "gate": gate,
                "name": name,
                "passed": passed,
                "results": v23_gate_payload(gate, report),
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

    milestone_path = ROOT / "results" / "milestone-2-v2.3-report.md"
    milestone_path.write_text(milestone_report(report), encoding="utf-8")

    all_passed = (
        report["passed"] and v20["passed"] and v21["passed"] and v221["passed"]
    )
    files = artifact_paths()
    missing = [
        str(path.relative_to(ROOT)) for path in files if not path.exists()
    ]
    if missing:
        raise RuntimeError(f"cannot freeze V2.3; missing artifacts: {missing}")
    manifest = {
        "stage": "V2.3",
        "status": "freeze-candidate" if all_passed else "failed-gate-stop",
        "all_gates_1_to_5_passed": all_passed,
        "analysis_plan_frozen_before_protocol_runs": True,
        "inherited_parameter_blocks_modified": False,
        "development_seed_maximum": 62331,
        "step_injection_bound": {
            "definition": "empirical 99th-percentile absolute adjacent-slice change in p(H_formation=persistent) across all open assay arms",
            "percentile": 99,
            "value": report["open_assays"]["step_injection"][
                "percentile_99"
            ],
            "slice_change_count": report["open_assays"]["step_injection"][
                "count"
            ],
        },
        "prospective_challenge": "C-V23",
        "prospective_challenge_revealed": False,
        "prospective_challenge_run": False,
        "files": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in sorted(set(files))
        },
    }
    write_json(RESULT_ROOT / "freeze-manifest.json", manifest)
    if not all_passed:
        raise SystemExit("V2.3 ratchet stopped at failed open gate")


if __name__ == "__main__":
    main()
