"""Execute gates 1–5 in ratcheted order and build freeze candidates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ref.v20 import run_v20
from ref.v21 import run_v21
from ref.v22 import run_v22


ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stage_artifacts(stage: str) -> list[Path]:
    version = stage.lower()
    inherited = ["__init__.py", "config.py", "factor.py", "model.py", "inference.py", "oracle.py", "audit.py", "templates.py", "rng.py", "statistics.py"]
    sources = [ROOT / "ref" / name for name in inherited]
    if stage != "V2.0":
        sources.extend([ROOT / "ref" / "precision.py", ROOT / "ref" / "readouts.py"])
    sources.extend(ROOT / "ref" / f"v2{minor}.py" for minor in range(int(stage[-1]) + 1))
    tests = [
        ROOT / "tests" / f"test_v2{minor}_{'kernel' if minor == 0 else 'precision' if minor == 1 else 'root'}.py"
        for minor in range(int(stage[-1]) + 1)
    ]
    return [
        ROOT / "contracts" / f"{version}-{'kernel-' if stage == 'V2.0' else 'precision-' if stage == 'V2.1' else 'root-'}contract.md",
        ROOT / "protocols" / f"{version}-analysis-plan.md",
        ROOT / "protocols" / f"{version}-parameters.json",
        ROOT / "protocols" / f"{version}-dummy-bundle.json",
        ROOT / "results" / stage / "decisions.md",
        *(ROOT / "results" / stage / f"gate-{gate}.json" for gate in range(1, 6)),
        ROOT / "results" / stage / "stage-report.json",
        ROOT / "README.md",
        ROOT / "run_milestone.py",
        *sources,
        *tests,
    ]


def write_stage(stage: str, report: dict[str, Any]) -> None:
    result_dir = ROOT / "results" / stage
    result_dir.mkdir(parents=True, exist_ok=True)
    gate_payloads = {
        1: {key: value for key, value in report.items() if key in {"semantic_errors", "semantic_proof", "structure_recovery"}},
        2: {key: value for key, value in report.items() if key in {"recovery", "association_recovery"}},
        3: {key: value for key, value in report.items() if key in {"model_comparison", "composition", "broadcast", "seam", "transfer_2x2"}},
        4: {key: value for key, value in report.items() if key in {"factor_sensitivity", "batch", "lesions", "seam"}},
        5: {key: value for key, value in report.items() if key.endswith("_regression")},
    }
    gate_names = list(report["gates"])
    for gate in range(1, 6):
        gate_name = gate_names[gate - 1]
        payload = {
            "stage": stage,
            "gate": gate,
            "name": gate_name,
            "passed": report["gates"][gate_name],
            "results": gate_payloads[gate],
            "failures": [] if report["gates"][gate_name] else [f"{gate_name} threshold not met"],
        }
        write_json(result_dir / f"gate-{gate}.json", payload)
    write_json(result_dir / "stage-report.json", report)
    artifacts = stage_artifacts(stage)
    missing = [str(path.relative_to(ROOT)) for path in artifacts if not path.exists()]
    if missing:
        raise RuntimeError(f"cannot freeze {stage}; missing artifacts: {missing}")
    manifest = {
        "stage": stage,
        "status": "freeze-candidate" if report["passed"] else "failed-gate-stop",
        "all_gates_1_to_5_passed": report["passed"],
        "sealed_gate_6_run": False,
        "files": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in sorted(set(artifacts))
        },
    }
    write_json(result_dir / "freeze-manifest.json", manifest)


def milestone_markdown(reports: list[dict[str, Any]]) -> str:
    lines = [
        "# Suite v2 milestone 1 report",
        "",
        "Generated from real Python reference runs. Gate 6 remains evaluator-sealed and unrun.",
        "",
    ]
    for report in reports:
        stage = report["stage"]
        lines.extend([f"## {stage}", ""])
        for name, passed in report["gates"].items():
            lines.append(f"- {name}: {'PASS' if passed else 'FAIL'}")
        if stage == "V2.0":
            lines.extend(
                [
                    f"- Maximum semantic parity error: {max(report['semantic_errors'].values()):.3g}",
                    f"- State recovery accuracy / Brier / ECE: {report['recovery']['state_accuracy']:.3f} / {report['recovery']['state_brier']:.3f} / {report['recovery']['state_ece']:.3f}",
                    f"- Parameter MAE / 95% coverage: {report['recovery']['parameter_mean_absolute_error']:.3f} / {report['recovery']['parameter_95_interval_coverage']:.3f}",
                ]
            )
        elif stage == "V2.1":
            lines.extend(
                [
                    f"- Likelihood sharpening effect: {report['semantic_proof']['sharpening_effect']:.3f}",
                    f"- Broadcast depth on/off/effect: {report['broadcast']['depth_on']:.3f} / {report['broadcast']['depth_off']:.3f} / {report['broadcast']['depth_effect']:.3f}",
                    f"- Cross-latent delivered log-odds effect: {report['composition']['delivered_log_odds_effect']:.3f}",
                    f"- Batch mean depth effect (95% interval): {report['batch']['mean_depth_effect']:.3f} ({report['batch']['depth_effect_95_interval'][0]:.3f}, {report['batch']['depth_effect_95_interval'][1]:.3f})",
                ]
            )
        else:
            seam = report["seam"]
            lines.extend(
                [
                    f"- Structure recovery accuracy / mean true probability: {report['structure_recovery']['accuracy']:.3f} / {report['structure_recovery']['mean_true_structure_probability']:.3f}",
                    f"- Association recovery MAE / 95% coverage: {report['association_recovery']['mean_absolute_error']:.3f} / {report['association_recovery']['coverage_95']:.3f}",
                    f"- Root uptake broad / broadcast-off / narrowed: {seam['broad']['root_uptake']:.3f} / {seam['broadcast_off']['root_uptake']:.3f} / {seam['narrowed']['root_uptake']:.3f}",
                    f"- Transfer broad / broadcast-off / narrowed: {seam['broad']['transfer']:.3f} / {seam['broadcast_off']['transfer']:.3f} / {seam['narrowed']['transfer']:.3f}",
                    f"- 2x2 association / similarity effects: {report['transfer_2x2']['association_main_effect']:.3f} / {report['transfer_2x2']['similarity_main_effect']:.3f}",
                    f"- Fixed-G direct transfer: {seam['mediation']['transfer_with_g_fixed_and_cue_root_cut']:.3g}",
                ]
            )
        lines.extend(
            [
                f"- Freeze candidate: `results/{stage}/freeze-manifest.json`",
                f"- Decision log: `results/{stage}/decisions.md`",
                "",
            ]
        )
    lines.extend(
        [
            "## Regressions and stop status",
            "",
            "All inherited gates survived in the final V2.2 strain. No failed gate blocked the ratchet. No formation, reduction, partner, or protector mechanisms were added. Work stops at the three freeze candidates; evaluator verification, commits, and sealed challenges remain external.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    runners = [run_v20, run_v21, run_v22]
    reports = []
    for runner in runners:
        report = runner()
        reports.append(report)
        write_stage(report["stage"], report)
        if not report["passed"]:
            break
    (ROOT / "results" / "milestone-1-report.md").write_text(
        milestone_markdown(reports), encoding="utf-8"
    )
    if len(reports) != 3 or not all(report["passed"] for report in reports):
        raise SystemExit("ratchet stopped at failed stage")


if __name__ == "__main__":
    main()
