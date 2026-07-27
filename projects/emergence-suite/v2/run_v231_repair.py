"""Invalidate-and-repeat runner for the V2.3.1r instrument repair."""

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
from run_v231_freeze import gate_payload, inherited_gate_payload


ROOT = Path(__file__).resolve().parent
RESULT_ROOT = ROOT / "results" / "V2.3.1r"
DEFECTIVE_ROOT = ROOT / "results" / "V2.3.1"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_inherited(stage: str, report: dict[str, Any]) -> None:
    destination = RESULT_ROOT / "cumulative" / stage
    gate_names = list(report["gates"])
    for gate in range(1, 6):
        name = gate_names[gate - 1]
        passed = bool(report["gates"][name])
        write_json(
            destination / f"gate-{gate}.json",
            {
                "instrument": "V2.3.1r",
                "rerun_stage": stage,
                "gate": gate,
                "name": name,
                "passed": passed,
                "results": inherited_gate_payload(stage, gate, report),
                "failures": [] if passed else [f"{name} threshold not met"],
            },
        )
    write_json(destination / "stage-report.json", report)


def numeric_leaves(value: Any, prefix: str = "") -> dict[str, float]:
    leaves: dict[str, float] = {}
    if isinstance(value, bool):
        return leaves
    if isinstance(value, (int, float)):
        leaves[prefix] = float(value)
    elif isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            leaves.update(numeric_leaves(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            leaves.update(numeric_leaves(child, f"{prefix}[{index}]"))
    return leaves


def metric_diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    old_values = numeric_leaves(old)
    new_values = numeric_leaves(new)
    shared = sorted(set(old_values) & set(new_values))
    moved = [
        {
            "path": path,
            "defective": old_values[path],
            "repaired": new_values[path],
            "delta": new_values[path] - old_values[path],
        }
        for path in shared
        if abs(new_values[path] - old_values[path]) > 1e-15
    ]
    return {
        "comparison": "V2.3.1r repaired instrument minus frozen defective V2.3.1",
        "shared_numeric_leaf_count": len(shared),
        "moved_numeric_leaf_count": len(moved),
        "moved": moved,
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
                "instrument": "V2.3.1r",
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
    write_inherited("V2.0", v20)
    write_inherited("V2.1", v21)
    write_inherited("V2.2.1", v221)

    defective = json.loads(
        (DEFECTIVE_ROOT / "stage-report.json").read_text()
    )
    write_json(RESULT_ROOT / "metric-diff.json", metric_diff(defective, report))

    all_passed = bool(
        report["passed"] and v20["passed"] and v21["passed"] and v221["passed"]
    )
    output_files = sorted(
        path
        for path in RESULT_ROOT.rglob("*")
        if path.is_file() and path.name != "repair-run-manifest.json"
    )
    write_json(
        RESULT_ROOT / "repair-run-manifest.json",
        {
            "instrument": "V2.3.1r",
            "declared_stage": "V2.3.1",
            "parameters_changed": False,
            "development_seed_maximum": 63980,
            "all_gates_1_to_5_passed": all_passed,
            "stage_gates": report["gates"],
            "cumulative_gates": {
                "V2.0": v20["gates"],
                "V2.1": v21["gates"],
                "V2.2.1": v221["gates"],
            },
            "files": {
                str(path.relative_to(ROOT)): sha256(path)
                for path in output_files
            },
        },
    )
    if not all_passed:
        raise SystemExit("V2.3.1r ratchet stopped at failed gate")


if __name__ == "__main__":
    main()
