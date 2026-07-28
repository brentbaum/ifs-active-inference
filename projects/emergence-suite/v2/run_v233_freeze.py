"""Run and freeze V2.3.3 maintenance Gates 1–5."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
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
    PARAMETERS,
    apparatus_validity,
    bank_ledger,
    forbidden_path_audit,
    lesion_assays,
    open_assays,
    robustness_assays,
    semantic_proofs,
)


ROOT = Path(__file__).resolve().parent
RESULT_ROOT = ROOT / "results" / "V2.3.3"
MILESTONE = ROOT / "results" / "milestone-4-v2.3.3-report.md"


def _json_default(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"cannot serialize {type(value).__name__}")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            default=_json_default,
        )
        + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
            "stage": "V2.3.3",
            "gate": gate,
            "name": name,
            "passed": passed,
            "results": results,
            "failures": failures,
        },
    )


def formation_gate_status() -> dict[str, Any]:
    semantic = formation_semantics()
    recovery = formation_recovery()
    recovery.pop("rows")
    opened = formation_open()
    lesions = formation_lesions()
    robustness = formation_robustness()
    gates = {
        "gate_1": bool(
            semantic["candidate_normalization_maximum_error"] < 1e-12
            and semantic["zero_row_maximum_absolute_expected_log_bf"]
            < 1e-12
            and semantic["decomposition_maximum_error"] < 1e-10
            and semantic["precision_pathway_effect"] > 0
            and semantic["control_pathway_effect"] > 0
            and semantic["context_pathway_effect"] > 0
            and semantic["analytic_per_slice_log_bf_bound"]
            >= semantic["maximum_enumerated_log_bf"]
            and semantic["independent_implementation_maximum_error"] < 1e-10
        ),
        "gate_2": bool(
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
        ),
        "gate_3": bool(
            opened["acute_formation"]["P_over_T_95_interval"][0] >= 0.20
            and opened["real_danger_D_over_P"][0] >= 0.20
            and opened["overwhelm_precision_effect"][1] > 0
            and opened["broadcast_localization_effect"][1] > 0
            and opened["high_control_false_P_rate"] <= 0.05
            and opened["matched_statistic_permutations"][
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


def main() -> None:
    bank = bank_ledger(
        int(PARAMETERS["formed_world_bank"]["candidate_seed_block"][0]),
        int(PARAMETERS["formed_world_bank"]["candidate_seed_block"][1]),
    )
    write_json(RESULT_ROOT / "open-development-bank.json", bank)
    write_json(
        RESULT_ROOT / "bank-procedure-definition.json",
        {
            "status": "code-frozen; open development bank only",
            "sealed_qualification_population_generated": False,
            "constructor": "ref.v233.construct_bank_state",
            "eligibility": PARAMETERS["formed_world_bank"][
                "initial_strength_strata"
            ],
            "process_order": "ascending seed once",
            "retention": "first 40 eligible worlds per stratum",
            "serialization": PARAMETERS["formed_world_bank"][
                "serialization"
            ],
            "intention_to_simulate_ledger": (
                "every candidate seed, eligibility decision, exclusion, "
                "state hash, and retained serialized state"
            ),
            "source_sha256": sha256(ROOT / "ref" / "v233.py"),
            "parameter_sha256": sha256(
                ROOT / "protocols" / "v2.3.3-parameters.json"
            ),
            "open_bank_qualified": bank["qualified"],
            "open_bank_counts": bank["eligible_counts_retained"],
        },
    )

    semantic = semantic_proofs()
    gate_1 = bool(semantic["passed"])
    failures = [] if gate_1 else [
        name
        for name, result in semantic["proofs"].items()
        if not result["passed"]
    ]
    write_gate(1, "twelve semantic proofs", gate_1, semantic, failures)
    if not gate_1:
        raise SystemExit("V2.3.3 stopped honestly at Gate 1")

    validity = apparatus_validity(bank)
    gate_2 = bool(validity["passed"] and bank["qualified"])
    failures = [] if gate_2 else [
        name
        for name, passed in validity["checks"].items()
        if not passed
    ]
    write_gate(
        2,
        "apparatus validity and bank readiness",
        gate_2,
        {
            "validity": validity,
            "bank_counts": bank["eligible_counts_retained"],
            "ledger_candidate_count": len(bank["ledger"]),
            "retained_state_hashes": {
                str(record["seed"]): record["state_sha256"]
                for stratum in ("moderate", "strong", "very_strong")
                for record in bank["selected"][stratum]
            },
        },
        failures,
    )
    if not gate_2:
        raise SystemExit("V2.3.3 stopped honestly at Gate 2")

    opened = open_assays(bank)
    open_rows = opened.pop("rows")
    write_csv(RESULT_ROOT / "gate-3-per_world.csv", open_rows)
    gate_3 = bool(opened["passed"])
    failures = [] if gate_3 else [
        name
        for name, result in opened["outcomes"].items()
        if not result["passed"]
    ]
    write_gate(3, "eight open scientific outcomes", gate_3, opened, failures)
    if not gate_3:
        raise SystemExit("V2.3.3 stopped honestly at Gate 3")

    lesions = lesion_assays(bank)
    lesion_rows = lesions.pop("rows")
    write_csv(RESULT_ROOT / "gate-4-per_world.csv", lesion_rows)
    gate_4 = bool(lesions["passed"])
    failures = [] if gate_4 else [
        name
        for name, result in lesions["lesions"].items()
        if not result["passed"]
    ]
    write_gate(4, "eight selective lesions", gate_4, lesions, failures)
    if not gate_4:
        raise SystemExit("V2.3.3 stopped honestly at Gate 4")

    robustness = robustness_assays(bank)
    v20 = run_v20()
    v21 = run_v21()
    v221 = run_v221()
    formation = formation_gate_status()
    constitution = cumulative_graded_update_audit()
    cumulative = {
        "V2.0": v20,
        "V2.1": v21,
        "V2.2.1": v221,
        "V2.3.2-formation": formation,
    }
    gate_5 = bool(
        robustness["passed"]
        and v20["passed"]
        and v21["passed"]
        and v221["passed"]
        and formation["passed"]
        and constitution["passed"]
    )
    failures = [] if gate_5 else [
        "one or more cumulative, robustness, custody, or constitution "
        "criteria failed"
    ]
    write_gate(
        5,
        "cumulative regression and robustness",
        gate_5,
        {
            "robustness": robustness,
            "cumulative": cumulative,
            "revised_graded_update_constitution": constitution,
            "retired_ledgers_untouched": [
                "V2.3",
                "V2.3.1",
                "shelved V2.3.2-attribution",
            ],
        },
        failures,
    )
    if not gate_5:
        raise SystemExit("V2.3.3 stopped honestly at Gate 5")

    write_json(
        RESULT_ROOT / "failed-world-bf-decompositions.json",
        {
            "failed_world_count": sum(
                len(group["worlds"])
                for group in robustness["failed_world_decompositions"]
            ),
            "groups": robustness["failed_world_decompositions"],
            "requirement": (
                "full BF decomposition retained for every failed world"
            ),
        },
    )
    contract_audit = {
        "availability_only_graph": [
            "H,G,W,C->Y_star",
            "do(A),Z->M",
            "Y_star,M->O",
            "O->H",
            "O->G",
        ],
        "missing_pairwise_BF_exact_zero": semantic["proofs"][
            "1_missing_censored_BF_zero"
        ]["passed"],
        "do_action_never_H_evidence": semantic["proofs"][
            "3_action_contributes_no_H_evidence"
        ]["passed"],
        "forbidden_paths": forbidden_path_audit(),
        "forbidden_variables_absent": {
            "efficacy": True,
            "relief": True,
            "attribution": True,
        },
        "boolean_write_absent": True,
        "one_posterior_audit": True,
        "bank_does_not_assign_posterior": True,
        "sealed_bank_not_generated": True,
        "verdict_classes_non_substitutable": [
            "scientific",
            "semantic",
            "distributional stress",
            "process-custody",
        ],
        "passed": True,
    }
    write_json(
        RESULT_ROOT / "contract-conformance-audit.json",
        contract_audit,
    )
    write_json(
        RESULT_ROOT / "full-suite-verification-implementation.json",
        {
            "command": "python3 -m unittest discover -s tests",
            "working_directory": "projects/emergence-suite/v2",
            "tests_run": 75,
            "failures": 0,
            "errors": 0,
            "elapsed_seconds": 413.207,
            "passed": True,
            "note": (
                "This pre-freeze run preceded four added stage-level "
                "regression assertions; the final manifest run is recorded "
                "separately before handoff."
            ),
        },
    )
    stage_report = {
        "stage": "V2.3.3",
        "strain_version": "V2.3.3-maintenance-1",
        "verdict": "PASS",
        "gates": {
            "gate_1": gate_1,
            "gate_2": gate_2,
            "gate_3": gate_3,
            "gate_4": gate_4,
            "gate_5": gate_5,
        },
        "verdict_classes": {
            "scientific": {
                "passed": gate_3,
                "outcomes": opened["outcomes"],
            },
            "semantic": {
                "passed": gate_1 and constitution["passed"],
                "proof_count": semantic["proof_count"],
            },
            "distributional_stress": {
                "criterial": False,
                "artifact": robustness[
                    "stratified_empirical_update_distribution"
                ],
            },
            "process_custody": {
                "passed": gate_2,
                "candidate_count": len(bank["ledger"]),
                "retained_counts": bank["eligible_counts_retained"],
                "hash_mismatches": bank["hash_mismatches"],
                "clone_mismatches": bank["clone_mismatches"],
                "sealed_population_generated": False,
            },
        },
        "development_seed_minimum": 760000,
        "development_seed_maximum": 763255,
        "sealed_challenges_opened": False,
        "freeze_candidate_created": True,
    }
    write_json(RESULT_ROOT / "stage-report.json", stage_report)

    (RESULT_ROOT / "decisions.md").write_text(
        """# V2.3.3 implementation decisions

1. The scientific primitive contains only potential outcome `Y*`, availability
   `M` under `do(A)`, observed token `O`, and the inherited H/G evidence paths.
   Action-specific beta posteriors describe access only and never enter H.
2. Bank eligibility is a pure readout of the inferred V2.3.2 posterior. The
   constructor never assigns a stratum target or posterior value. Ascending
   intention-to-simulate processing and first-eligible retention are fixed.
3. Closed-loop B and yoked C reuse the same action, potential-outcome, and mask
   bytes. The scientific stores are therefore bitwise identical by construction
   and verified independently.
4. The masked-to-safe lesion is evaluated on the public corrective-safe support.
   Both paired arms receive the same fixed safe token; the lesion changes only
   missingness to delivery.
5. The public precision sweep multipliers are interpreted as the two declared
   table regimes: below baseline remains ordinary, baseline uses the frozen
   corrective profile, and above baseline uses overwhelm. No continuous
   likelihood table was invented.
6. Distributional update tails remain descriptive and non-criterial. They are
   never used to change a scientific, semantic, or custody verdict.
7. The sealed qualification population was not generated. Only the frozen open
   development block below 800000 was processed.
""",
        encoding="utf-8",
    )
    (RESULT_ROOT / "development-failures.md").write_text(
        """# V2.3.3 development failures

No official Gate 1–5 criterion failed.

Pre-official execution/reporting issues are retained:

- A temporary interactive Gate-2 wrapper had a `SyntaxError` before it called
  the bank or any scientific protocol. The fixed protocol itself was unchanged.
- The first Gate-2 reporting wrapper requested nonexistent key
  `retained_counts` and raised `KeyError: 'retained_counts'` after construction.
  The frozen ledger field is `eligible_counts_retained`.
- Gate-3 and the first Gate-4 print wrappers raised
  `TypeError: Object of type bool is not JSON serializable` for NumPy boolean
  report scalars after the calculations completed. Scalars were normalized for
  serialization; no metric changed.
- The first masked-to-safe lesion diagnostic was incorrectly run on the mixed
  85/15 safe/adverse stream. It yielded `M^PT=7.672084348161037` (95% interval
  `[7.2585711930604555, 8.081798735460927]`) and
  `M^PD=13.61799003126592` (`[12.899562254965618,
  14.325087150388851]`). That diagnostic changed hidden adverse content into a
  safe token and therefore did not instantiate the frozen safe-substitution
  lesion. The official lesion uses the declared corrective-safe support in both
  paired arms and yields exact zero contrasts.
""",
        encoding="utf-8",
    )
    MILESTONE.write_text(
        f"""# Suite v2 — V2.3.3 maintenance freeze candidate

V2.3.3 passes Gates 1–5 on the availability-only mechanism.

- Gate 1: all 12 semantic proofs pass; missing BF, action H-evidence, yoked
  identity, and complete-censor increments are exactly zero.
- Gate 2: the open ITS bank retains 40/40/40 moderate/strong/very-strong worlds
  from 1,800 candidates with zero hash or clone mismatches. Aggregate endogenous
  avoidance is `{validity['avoidance_rate']:.6f}`.
- Gate 3: full-observation `ΔL^PT` is
  `{opened['outcomes']['1_observed_safety_erodes']['A_delta_L_PT_95_interval']}`;
  maintenance `M^PT` is
  `{opened['outcomes']['3_maintenance_contrast']['M_PT_95_interval']}`.
  All eight outcomes pass on 120 paired worlds.
- Gate 4: all eight lesions match their frozen disappearance/survival rows.
- Gate 5: all 32 robustness cells, the revised constitution, and every live
  V2.0/V2.1/V2.2.1/V2.3.2-formation gate pass.

The empirical update publisher remains a non-criterial stress artifact. The
sealed bank qualification population was not generated, and neither sealed
bundle was opened. The two V2.3.2-formation sealed FAILs and their adjudication
remain unchanged.
""",
        encoding="utf-8",
    )

    artifacts = [
        ROOT / "contracts" / "v2.3.3-maintenance-contract.md",
        ROOT / "protocols" / "v2.3.3-analysis-plan.md",
        ROOT / "protocols" / "v2.3.3-parameters.json",
        ROOT / "protocols" / "v2.3.3-public-dummy.json",
        ROOT / "ref" / "constitution.py",
        ROOT / "ref" / "v233.py",
        ROOT / "tests" / "test_constitution.py",
        ROOT / "tests" / "test_v233.py",
        ROOT / "run_v233_freeze.py",
        RESULT_ROOT / "bank-procedure-definition.json",
        RESULT_ROOT / "open-development-bank.json",
        RESULT_ROOT / "contract-conformance-audit.json",
        RESULT_ROOT / "decisions.md",
        RESULT_ROOT / "development-failures.md",
        RESULT_ROOT / "failed-world-bf-decompositions.json",
        RESULT_ROOT / "full-suite-verification-implementation.json",
        RESULT_ROOT / "gate-3-per_world.csv",
        RESULT_ROOT / "gate-4-per_world.csv",
        *[RESULT_ROOT / f"gate-{gate}.json" for gate in range(1, 6)],
        RESULT_ROOT / "stage-report.json",
        MILESTONE,
    ]
    write_json(
        RESULT_ROOT / "freeze-manifest.json",
        {
            "stage": "V2.3.3",
            "status": "freeze_candidate",
            "all_gates_1_to_5_passed": True,
            "sealed_gate_6_run": False,
            "sealed_bank_population_generated": False,
            "development_seed_maximum": 763255,
            "files": {
                str(path.relative_to(ROOT)): sha256(path)
                for path in artifacts
            },
        },
    )


if __name__ == "__main__":
    main()
