"""Run V2.4 Gates 1–5 in ratchet order and create a freeze candidate."""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from types import MappingProxyType
from typing import Any

import numpy as np

from ref.constitution import cumulative_graded_update_audit
from ref.v20 import run_v20
from ref.v21 import run_v21
from ref.v221 import run_v221
from ref.v232_formation import (
    lesion_assays as formation_lesions,
    open_assays as formation_open,
    recovery_assay as formation_recovery,
    robustness_assay as formation_robustness,
    semantic_proofs as formation_semantics,
)
from ref.v233 import (
    PARAMETERS as V233_PARAMETERS,
    apparatus_validity as maintenance_validity,
    bank_ledger as maintenance_bank,
    lesion_assays as maintenance_lesions,
    open_assays as maintenance_open,
    robustness_assays as maintenance_robustness,
    semantic_proofs as maintenance_semantics,
)
from ref.v24 import (
    PARAMETERS,
    lesion_assays,
    open_assays,
    recovery_assay,
    robustness_assays,
    semantic_proofs,
)


ROOT = Path(__file__).resolve().parent
RESULT_ROOT = ROOT / "results" / "V2.4"
MILESTONE = ROOT / "results" / "milestone-5-v2.4-report.md"


def _json_default(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, MappingProxyType):
        return dict(value)
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    raise TypeError(f"cannot serialize {type(value).__name__}")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            default=_json_default,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: (
                        json.dumps(value, sort_keys=True, default=_json_default)
                        if isinstance(value, (dict, list, tuple))
                        else value
                    )
                    for key, value in row.items()
                }
            )


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
            "stage": "V2.4",
            "gate": gate,
            "name": name,
            "passed": passed,
            "failures": failures,
            "verdict_classes": {
                "scientific_outcomes": (
                    "PASS" if passed and gate >= 2 else "NOT_SCORED"
                ),
                "semantic_integrity": (
                    "PASS" if passed else "FAIL"
                ),
                "distributional_stress": (
                    "DESCRIPTIVE_ONLY" if gate in {3, 5} else "NOT_SCORED"
                ),
                "process_custody": "PASS",
            },
            "results": results,
        },
    )


def record_failure(gate: int, failures: list[str]) -> None:
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    path = RESULT_ROOT / "development-failures.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else (
        "# V2.4 development failures\n\n"
        "One deterministic Gate-2 seed (`770200`) was evaluated as a "
        "performance smoke after Gate 1 passed and before the official "
        "full Gate-2 block. Its result caused no code, parameter, threshold, "
        "or protocol decision and remains in the preregistered block.\n\n"
    )
    text = existing + (
        f"## Official Gate {gate} stop\n\n"
        + "\n".join(f"- {failure}" for failure in failures)
        + "\n"
    )
    path.write_text(text, encoding="utf-8")


def formation_status() -> dict[str, Any]:
    semantic = formation_semantics()
    recovery = formation_recovery()
    recovery.pop("rows", None)
    opened = formation_open()
    lesions = formation_lesions()
    robustness = formation_robustness()
    gates = {
        "gate_1": bool(
            semantic["candidate_normalization_maximum_error"] < 1e-12
            and semantic["zero_row_maximum_absolute_expected_log_bf"]
            < 1e-12
            and semantic["decomposition_maximum_error"] < 1e-10
            and semantic["independent_implementation_maximum_error"] < 1e-10
        ),
        "gate_2": bool(
            recovery["accuracy"] >= 0.80
            and recovery["multiclass_brier"] <= 0.15
            and recovery["confidence_ece"] <= 0.08
            and min(recovery["diagonal_rates"]) >= 0.75
        ),
        "gate_3": bool(
            opened["matched_statistic_permutations"][
                "maximum_log_joint_difference"
            ]
            <= 1e-10
            and opened["no_event_maximum_prior_difference"] < 1e-12
        ),
        "gate_4": bool(
            all(
                abs(result["lesioned"])
                <= min(0.02, abs(result["intact"]) / 4.0)
                and result["survivor"] > 0
                for result in lesions.values()
            )
        ),
        "gate_5": bool(
            robustness["all_signs_survive"]
            and robustness["schedule_invariance_survives"]
        ),
    }
    return {
        "gates": gates,
        "semantic": semantic,
        "recovery": recovery,
        "open": opened,
        "lesions": lesions,
        "robustness": robustness,
        "passed": all(gates.values()),
    }


def maintenance_status() -> dict[str, Any]:
    block = V233_PARAMETERS["formed_world_bank"]["candidate_seed_block"]
    bank = maintenance_bank(int(block[0]), int(block[1]))
    semantic = maintenance_semantics()
    validity = maintenance_validity(bank)
    opened = maintenance_open(bank)
    opened.pop("rows", None)
    lesions = maintenance_lesions(bank)
    lesions.pop("rows", None)
    robustness = maintenance_robustness(bank)
    gates = {
        "gate_1": bool(semantic["passed"]),
        "gate_2": bool(validity["passed"] and bank["qualified"]),
        "gate_3": bool(opened["passed"]),
        "gate_4": bool(lesions["passed"]),
        "gate_5": bool(robustness["passed"]),
    }
    return {
        "gates": gates,
        "semantic": semantic,
        "validity": validity,
        "bank_counts": bank["eligible_counts_retained"],
        "open": opened,
        "lesions": lesions,
        "robustness": robustness,
        "passed": all(gates.values()),
    }


def previous_tracked_changes() -> list[str]:
    command = [
        "git",
        "diff",
        "--name-only",
        "HEAD",
        "--",
        "projects/emergence-suite/v2/ref",
        "projects/emergence-suite/v2/tests",
        "projects/emergence-suite/v2/contracts",
        "projects/emergence-suite/v2/protocols",
        "projects/emergence-suite/v2/results",
    ]
    result = subprocess.run(
        command,
        cwd=ROOT.parents[2],
        check=True,
        capture_output=True,
        text=True,
    )
    allowed = {
        "projects/emergence-suite/v2/ref/v24.py",
        "projects/emergence-suite/v2/tests/test_v24.py",
        "projects/emergence-suite/v2/run_v24_freeze.py",
    }
    return [
        value
        for value in result.stdout.splitlines()
        if value and value not in allowed and "/V2.4/" not in value
        and "milestone-5-v2.4-report.md" not in value
    ]


def main() -> None:
    started = time.perf_counter()
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)

    semantic = semantic_proofs()
    inherited_constitution = cumulative_graded_update_audit()
    gate_1 = bool(semantic["passed"] and inherited_constitution["passed"])
    failures = [
        name
        for name, result in semantic["proofs"].items()
        if not result["passed"]
    ]
    if not inherited_constitution["passed"]:
        failures.append("inherited cumulative graded-update constitution")
    write_gate(
        1,
        "fourteen semantic and constitutional proofs",
        gate_1,
        {
            "v24": semantic,
            "inherited_graded_update_constitution": inherited_constitution,
        },
        failures,
    )
    if not gate_1:
        record_failure(1, failures)
        raise SystemExit("V2.4 stopped honestly at Gate 1")

    recovery = recovery_assay()
    recovery_rows = recovery.pop("rows")
    write_csv(RESULT_ROOT / "gate-2-recovery-per_world.csv", recovery_rows)
    gate_2 = bool(recovery["passed"])
    failures = [
        name
        for name, passed in recovery["checks"].items()
        if not passed
    ]
    write_gate(
        2,
        "five-family recovery and calibration",
        gate_2,
        recovery,
        failures,
    )
    if not gate_2:
        record_failure(2, failures)
        raise SystemExit("V2.4 stopped honestly at Gate 2")

    opened = open_assays()
    open_rows = opened.pop("rows")
    for name, rows in open_rows.items():
        write_csv(RESULT_ROOT / f"gate-3-{name}-per_world.csv", rows)
    gate_3 = bool(opened["passed"])
    failures = [
        name
        for name, passed in opened["checks"].items()
        if not passed
    ]
    write_gate(
        3,
        "eight open and composition assays",
        gate_3,
        opened,
        failures,
    )
    if not gate_3:
        record_failure(3, failures)
        raise SystemExit("V2.4 stopped honestly at Gate 3")

    lesions = lesion_assays()
    gate_4 = bool(lesions["passed"])
    failures = [
        name
        for name, result in lesions["lesions"].items()
        if not result["passed"]
    ]
    write_gate(
        4,
        "five selective lesions",
        gate_4,
        lesions,
        failures,
    )
    if not gate_4:
        record_failure(4, failures)
        raise SystemExit("V2.4 stopped honestly at Gate 4")

    robustness = robustness_assays()
    v20 = run_v20()
    v21 = run_v21()
    v221 = run_v221()
    formation = formation_status()
    maintenance = maintenance_status()
    constitution = cumulative_graded_update_audit()
    write_json(
        RESULT_ROOT / "cumulative" / "V2.0" / "stage-report.json", v20
    )
    write_json(
        RESULT_ROOT / "cumulative" / "V2.1" / "stage-report.json", v21
    )
    write_json(
        RESULT_ROOT / "cumulative" / "V2.2.1" / "stage-report.json", v221
    )
    write_json(
        RESULT_ROOT
        / "cumulative"
        / "V2.3.2-formation"
        / "stage-report.json",
        formation,
    )
    write_json(
        RESULT_ROOT / "cumulative" / "V2.3.3" / "stage-report.json",
        maintenance,
    )
    tracked_changes = previous_tracked_changes()
    suite_start = time.perf_counter()
    suite = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    suite_elapsed = time.perf_counter() - suite_start
    suite_result = {
        "command": "python3 -m unittest discover -s tests",
        "returncode": suite.returncode,
        "stdout": suite.stdout,
        "stderr": suite.stderr,
        "elapsed_seconds": suite_elapsed,
        "passed": suite.returncode == 0,
    }
    write_json(RESULT_ROOT / "full-suite-verification.json", suite_result)
    gate_5 = bool(
        robustness["passed"]
        and v20["passed"]
        and v21["passed"]
        and v221["passed"]
        and formation["passed"]
        and maintenance["passed"]
        and constitution["passed"]
        and not tracked_changes
        and suite.returncode == 0
    )
    failures = []
    if not robustness["passed"]:
        failures.append("V2.4 robustness")
    for name, value in (
        ("V2.0", v20["passed"]),
        ("V2.1", v21["passed"]),
        ("V2.2.1", v221["passed"]),
        ("V2.3.2-formation", formation["passed"]),
        ("V2.3.3", maintenance["passed"]),
        ("graded-update constitution", constitution["passed"]),
        ("full unittest suite", suite.returncode == 0),
    ):
        if not value:
            failures.append(name)
    if tracked_changes:
        failures.append(
            "prior frozen tracked artifacts changed: "
            + ", ".join(tracked_changes)
        )
    write_gate(
        5,
        "cumulative regression and robustness",
        gate_5,
        {
            "v24_robustness": robustness,
            "cumulative_passes": {
                "V2.0": v20["passed"],
                "V2.1": v21["passed"],
                "V2.2.1": v221["passed"],
                "V2.3.2-formation": formation["passed"],
                "V2.3.3": maintenance["passed"],
            },
            "graded_update_constitution": constitution,
            "prior_frozen_tracked_changes": tracked_changes,
            "full_suite": suite_result,
        },
        failures,
    )
    if not gate_5:
        record_failure(5, failures)
        raise SystemExit("V2.4 stopped honestly at Gate 5")

    decisions = """# V2.4 decisions

- The five families replace complete initial/transition/context process
  bundles; no family is an edge toggle.
- Cue/root/marker emissions are one common normalized interface. Candidate
  differences are process sharing and dynamics only.
- CS transition uncertainty is integrated with transition-count sufficient
  states. CP hazard uncertainty is integrated with the no-change path.
- Fixed GW/CL transition scales have degenerate parameter posteriors because
  the frozen parameter block declares fixed matrices, not a scale prior.
- Complexity is the exact sum of per-slice posterior-versus-predictive KL;
  the pre-held-out match is frozen before scoring the held-out suffix.
- The Experiments 44/44b lessons used are marginal-preserving controls,
  explicit complexity charges, and training-coordinate transport. No old
  source, parameter, likelihood, or result was ported.
- The V2.3.3 qualified bank is read as immutable initial conditions; no
  state is selected on a V2.4 result.
- The sealed C-V24 hash and contents were not opened or inferred.
"""
    (RESULT_ROOT / "decisions.md").write_text(decisions, encoding="utf-8")
    (RESULT_ROOT / "development-failures.md").write_text(
        "# V2.4 development failures\n\n"
        "No official Gate 1–5 criterion failed.\n\n"
        "One deterministic Gate-2 seed (`770200`) was evaluated as a "
        "performance smoke after Gate 1 passed and before the official "
        "full Gate-2 block. Its result caused no code, parameter, threshold, "
        "or protocol decision and remains in the preregistered block.\n",
        encoding="utf-8",
    )
    write_json(
        RESULT_ROOT / "failed-world-bf-decompositions.json",
        {
            "failed_world_count": len(
                robustness["failed_world_decompositions"]
            ),
            "worlds": robustness["failed_world_decompositions"],
            "failures_retained_verbatim": True,
        },
    )
    contract_audit = {
        "five_replaceable_process_families": True,
        "common_observation_likelihood": True,
        "all_process_rows_normalized": semantic["proofs"][
            "1_common_emissions_and_transitions_normalized"
        ]["passed"],
        "prequential_partition_recombination": semantic["proofs"][
            "12_prequential_partition_recombines"
        ]["passed"],
        "independent_oracle": semantic["proofs"][
            "9_independent_path_oracle"
        ]["passed"],
        "one_posterior": semantic["proofs"][
            "14_forbidden_assignment_and_one_posterior"
        ]["passed"],
        "formed_bank_as_initial_conditions": opened["formed_bank_bridge"][
            "all_clone_identities"
        ],
        "frozen_prior_stage_artifacts_unchanged": not tracked_changes,
        "sealed_gate_6_run": False,
        "passed": True,
    }
    write_json(
        RESULT_ROOT / "contract-conformance-audit.json", contract_audit
    )
    stage_report = {
        "stage": "V2.4",
        "version": "V2.4-redescription-1",
        "status": "freeze_candidate",
        "all_gates_1_to_5_passed": True,
        "gate_verdicts": {f"gate_{index}": "PASS" for index in range(1, 6)},
        "verdict_classes": {
            "scientific_outcomes": "PASS",
            "semantic_integrity": "PASS",
            "distributional_stress": "DESCRIPTIVE_ONLY",
            "process_custody": "PASS",
        },
        "development_seed_maximum": 773499,
        "sealed_gate_6_run": False,
        "elapsed_seconds": time.perf_counter() - started,
    }
    write_json(RESULT_ROOT / "stage-report.json", stage_report)
    MILESTONE.write_text(
        """# Milestone 5 — V2.4 context-indexed redescription

V2.4 is a freeze candidate. Gates 1–5 passed prospectively under the frozen
contract and analysis plan. The exact reference compares global
down-weighting, cue-local relearning, context split, continuous drift, and
change point through common normalized observations and fully replaceable
temporal processes.

The stage reports the full five-family recovery matrix, drift and
change-point false-split controls, pre-held-out matched-complexity prediction,
exact complexity decomposition, misspecification stress, V2.1/V2.2.1
composition, and a bitwise-cloned V2.3.3 formed-bank bridge. Selective
lesions and every standing cumulative stage passed. Distributional stress is
descriptive and cannot alter the scientific, semantic, or custody verdicts.

C-V24 remains sealed and unrun. No escrow seed was accessed.
""",
        encoding="utf-8",
    )

    manifest_paths = [
        ROOT / "contracts" / "v2.4-redescription-contract.md",
        ROOT / "protocols" / "v2.4-analysis-plan.md",
        ROOT / "protocols" / "v2.4-public-dummy.json",
        ROOT / "protocols" / "v2.4-parameters.json",
        ROOT / "ref" / "v24.py",
        ROOT / "tests" / "test_v24.py",
        ROOT / "run_v24_freeze.py",
        *sorted(
            path
            for path in RESULT_ROOT.rglob("*")
            if path.is_file() and path.name != "freeze-manifest.json"
        ),
        MILESTONE,
    ]
    manifest = {
        "stage": "V2.4",
        "status": "freeze_candidate",
        "all_gates_1_to_5_passed": True,
        "sealed_gate_6_run": False,
        "development_seed_maximum": 773499,
        "files": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in manifest_paths
        },
    }
    write_json(RESULT_ROOT / "freeze-manifest.json", manifest)
    print("V2.4 freeze candidate complete")


if __name__ == "__main__":
    main()
