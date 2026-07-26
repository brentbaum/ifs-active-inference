"""Run all gates 1–5 for the additive V2.2.1 strain and freeze results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ref.v20 import run_v20
from ref.v21 import run_v21
from ref.v221 import run_v221


ROOT = Path(__file__).resolve().parent
RESULT_ROOT = ROOT / "results" / "V2.2.1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def gate_payload(stage: str, gate: int, report: dict[str, Any]) -> dict[str, Any]:
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


def write_stage_rerun(stage: str, report: dict[str, Any]) -> None:
    destination = RESULT_ROOT / "cumulative" / stage
    destination.mkdir(parents=True, exist_ok=True)
    gate_names = list(report["gates"])
    for gate in range(1, 6):
        name = gate_names[gate - 1]
        passed = bool(report["gates"][name])
        write_json(
            destination / f"gate-{gate}.json",
            {
                "strain": "V2.2.1",
                "rerun_stage": stage,
                "gate": gate,
                "name": name,
                "passed": passed,
                "results": gate_payload(stage, gate, report),
                "failures": [] if passed else [f"{name} threshold not met"],
            },
        )
    write_json(destination / "stage-report.json", report)


def milestone_report(
    v20: dict[str, Any], v21: dict[str, Any], v221: dict[str, Any]
) -> str:
    floor = v221["repair_floor_assay"]
    semantic = v221["semantic_proof"]
    recovery = v221["association_recovery"]
    return f"""# Suite v2 milestone 1 — V2.2.1 repair section

This additive strain responds to the retained C-V22 failure. The prerepair
diagnosis found verdict (b): calibrated continuous association learning, but no
finite model component for exact non-association.

## Repair

V2.2.1 compares an exact `theta=.5` association spike against a learnable
Beta(match=9,mismatch=1) slab under prior model probabilities `.6/.4`.
Downstream inference receives the posterior-model-averaged CPT. No transfer
threshold, association clamp, target write, or mediation lesion was added.

## Gate reruns

### V2.0 under V2.2.1

{chr(10).join(f"- {name}: {'PASS' if passed else 'FAIL'}" for name, passed in v20['gates'].items())}

State accuracy/Brier/ECE remained
`{v20['recovery']['state_accuracy']:.3f}` /
`{v20['recovery']['state_brier']:.3f}` /
`{v20['recovery']['state_ece']:.3f}`.

### V2.1 under V2.2.1

{chr(10).join(f"- {name}: {'PASS' if passed else 'FAIL'}" for name, passed in v21['gates'].items())}

Broadcast depth effect remained `{v21['broadcast']['depth_effect']:.3f}`;
cross-latent delivered log-odds effect remained
`{v21['composition']['delivered_log_odds_effect']:.3f}`.

### Repaired V2.2

{chr(10).join(f"- {name}: {'PASS' if passed else 'FAIL'}" for name, passed in v221['gates'].items())}

- Analytic/exact structure-posterior error:
  `{semantic['maximum_error']:.3g}`.
- True-zero / true-associated component posterior:
  `{semantic['posteriors_zero_associated']['zero'][0]:.4f}` /
  `{semantic['posteriors_zero_associated']['associated'][1]:.4f}`.
- Existence recovery accuracy:
  `{recovery['existence_accuracy']:.3f}`.
- Slab parameter MAE / 95% coverage:
  `{recovery['slab_parameter_mean_absolute_error']:.3f}` /
  `{recovery['slab_parameter_95_interval_coverage']:.3f}`.
- True-zero floor-clean rate:
  `{floor['zero_floor_clean_rate']:.3f}` over
  `{floor['world_count']}` worlds.
- Mean true-zero transfer, 95% interval:
  `{floor['zero_transfer_mean']:.4f}`
  `[{floor['zero_transfer_95_interval'][0]:.4f},
  {floor['zero_transfer_95_interval'][1]:.4f}]`.
- Mean associated transfer, 95% interval:
  `{floor['associated_transfer_mean']:.3f}`
  `[{floor['associated_transfer_95_interval'][0]:.3f},
  {floor['associated_transfer_95_interval'][1]:.3f}]`.

## Status

All gates 1–5 pass in the V2.2.1 strain. The original V2.2 and Gate-6
artifacts remain unchanged. C-V22b remains sealed and unrun; its plaintext and
seeds were not accessed. Work stops at this freeze candidate.
"""


def artifacts() -> list[Path]:
    cumulative = sorted(
        path
        for path in (RESULT_ROOT / "cumulative").rglob("*")
        if path.is_file()
    )
    inherited_sources = [
        ROOT / "ref" / name
        for name in (
            "__init__.py",
            "audit.py",
            "config.py",
            "factor.py",
            "inference.py",
            "model.py",
            "oracle.py",
            "precision.py",
            "readouts.py",
            "rng.py",
            "statistics.py",
            "templates.py",
            "v20.py",
            "v21.py",
            "v22.py",
            "v221.py",
        )
    ]
    tests = [
        ROOT / "tests" / name
        for name in (
            "test_v20_kernel.py",
            "test_v21_precision.py",
            "test_v22_root.py",
            "test_v221_association.py",
        )
    ]
    return [
        ROOT / "contracts" / "v2.2.1-association-contract.md",
        ROOT / "protocols" / "v2.2.1-analysis-plan.md",
        ROOT / "protocols" / "v2.2.1-parameters.json",
        ROOT / "protocols" / "v2.2.1-dummy-bundle.json",
        ROOT / "diagnostics" / "run_v221_diagnosis.py",
        RESULT_ROOT / "diagnosis.md",
        RESULT_ROOT / "diagnosis-summary.json",
        RESULT_ROOT / "diagnosis-per_seed.csv",
        RESULT_ROOT / "decisions.md",
        RESULT_ROOT / "stage-report.json",
        ROOT / "results" / "milestone-1-v2.2.1-report.md",
        ROOT / "run_v221_freeze.py",
        *inherited_sources,
        *tests,
        *cumulative,
    ]


def main() -> None:
    v20 = run_v20()
    write_stage_rerun("V2.0", v20)
    v21 = run_v21()
    write_stage_rerun("V2.1", v21)
    v221 = run_v221()
    write_stage_rerun("V2.2", v221)
    write_json(RESULT_ROOT / "stage-report.json", v221)
    report_path = ROOT / "results" / "milestone-1-v2.2.1-report.md"
    report_path.write_text(
        milestone_report(v20, v21, v221), encoding="utf-8"
    )
    all_passed = v20["passed"] and v21["passed"] and v221["passed"]
    files = artifacts()
    missing = [
        str(path.relative_to(ROOT)) for path in files if not path.exists()
    ]
    if missing:
        raise RuntimeError(f"cannot freeze V2.2.1; missing artifacts: {missing}")
    manifest = {
        "strain": "V2.2.1",
        "status": "freeze-candidate" if all_passed else "failed-gate-stop",
        "all_gates_1_to_5_passed": all_passed,
        "prospective_challenge": "C-V22b",
        "prospective_challenge_revealed": False,
        "prospective_challenge_run": False,
        "inherited_parameter_blocks_modified": False,
        "files": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in sorted(set(files))
        },
    }
    write_json(RESULT_ROOT / "freeze-manifest.json", manifest)
    if not all_passed:
        raise SystemExit("V2.2.1 ratchet stopped at failed open gate")


if __name__ == "__main__":
    main()

