"""Ordered V2.3.2 gate runner with the prospective ratchet."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ref.v232 import (
    anti_authoring_audit,
    formation_recovery_assay,
    recovery_assay,
    semantic_proofs,
)


ROOT = Path(__file__).resolve().parent
RESULT_ROOT = ROOT / "results" / "V2.3.2"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gate_1_pass(proofs: dict[str, Any]) -> bool:
    return bool(
        proofs["1_masked_bf"]["maximum_posterior_change"] < 1e-12
        and proofs["1_masked_bf"]["repeated_60_maximum_change"] < 1e-12
        and proofs["2_eta_zero_equivalence"][
            "posterior_maximum_difference"
        ] < 1e-12
        and abs(
            proofs["3_eta_one_non_disconfirmation"]["theta_change"]
        ) < 1e-12
        and proofs["4_engagement_disconfirms"]["theta_change"] < 0
        and proofs["5_action_no_direct_update"][
            "maximum_posterior_change"
        ] < 1e-12
        and proofs["6_relief_policy_only"]["policy_probability_change"] > 0
        and proofs["6_relief_policy_only"][
            "environment_maximum_change"
        ] < 1e-12
        and proofs["7_exact_spike_mass"]["represented_exactly"]
        and proofs["8_pure_avoidance_confound"]["correlation"] >= 0.40
        and proofs["9_probe_breaks_confound"]["absolute_reduction"] >= 0.15
        and proofs["10_enumeration_tolerance"][
            "maximum_posterior_error"
        ] < 1e-10
        and proofs["10_enumeration_tolerance"][
            "maximum_evidence_error"
        ] < 1e-10
    )


def gate_2_failures(
    formation: dict[str, Any], maintenance: dict[str, Any]
) -> list[str]:
    failures = []
    f_checks = (
        ("V2.3.2-F structure accuracy", formation["structure_accuracy"], ">=", 0.68),
        ("V2.3.2-F structure Brier", formation["structure_brier"], "<=", 0.21),
        ("V2.3.2-F structure ECE", formation["structure_ece"], "<=", 0.04),
        (
            "V2.3.2-F identifiable parameter MAE",
            formation["identifiable_parameter_mean_absolute_error"],
            "<=",
            0.10,
        ),
        (
            "V2.3.2-F controllability accuracy",
            formation["controllability_accuracy"],
            ">=",
            0.75,
        ),
        (
            "V2.3.2-F integration accuracy",
            formation["integration_accuracy"],
            ">=",
            0.75,
        ),
        (
            "V2.3.2-F real-danger accuracy",
            formation["real_danger_accuracy"],
            ">=",
            0.75,
        ),
        (
            "V2.3.2-F benign false formation",
            formation["maximum_benign_false_formation"],
            "<=",
            0.05,
        ),
    )
    identifiable = maintenance["identifiable"]
    nonidentifiable = maintenance["nonidentifiable"]
    m_checks = (
        ("V2.3.2-M H_E accuracy", identifiable["H_E_accuracy"], ">=", 0.80),
        ("V2.3.2-M H_E Brier", identifiable["H_E_brier"], "<=", 0.18),
        ("V2.3.2-M H_E ECE", identifiable["H_E_ece"], "<=", 0.08),
        (
            "V2.3.2-M theta MAE",
            identifiable["theta_mean_absolute_error"],
            "<=",
            0.10,
        ),
        (
            "V2.3.2-M eta MAE",
            identifiable["eta_mean_absolute_error"],
            "<=",
            0.10,
        ),
        (
            "V2.3.2-M theta coverage",
            identifiable["theta_coverage"],
            ">=",
            0.90,
        ),
        (
            "V2.3.2-M eta coverage",
            identifiable["eta_coverage"],
            ">=",
            0.90,
        ),
        (
            "V2.3.2-M exact-zero accuracy",
            identifiable["exact_zero_accuracy"],
            ">=",
            0.85,
        ),
        (
            "V2.3.2-M context efficacy classification accuracy",
            identifiable["context_efficacy_classification_accuracy"],
            ">=",
            0.75,
        ),
        (
            "V2.3.2-M joint non-identifiable coverage",
            nonidentifiable["joint_coverage"],
            ">=",
            0.90,
        ),
        (
            "V2.3.2-M threat-efficacy correlation",
            nonidentifiable["median_correlation"],
            ">=",
            0.40,
        ),
        (
            "V2.3.2-M theta entropy",
            nonidentifiable["minimum_theta_entropy"],
            ">=",
            0.35,
        ),
        (
            "V2.3.2-M eta entropy",
            nonidentifiable["minimum_eta_entropy"],
            ">=",
            0.35,
        ),
        (
            "V2.3.2-M H_E entropy",
            nonidentifiable["minimum_H_E_entropy"],
            ">=",
            0.25,
        ),
        (
            "V2.3.2-M false-certainty rate",
            nonidentifiable["false_certainty_rate"],
            "<=",
            0.10,
        ),
        (
            "V2.3.2-M probe correlation reduction",
            nonidentifiable["median_probe_correlation_reduction"],
            ">=",
            0.15,
        ),
    )
    for label, value, operator, threshold in (*f_checks, *m_checks):
        passed = value >= threshold if operator == ">=" else value <= threshold
        if not passed:
            failures.append(
                f"{label}: observed {value:.12f}; required {operator} {threshold:.12f}."
            )
    for name, coverage in formation[
        "identifiable_parameter_coverage"
    ].items():
        if coverage < 0.90:
            failures.append(
                f"V2.3.2-F {name} coverage: observed {coverage:.12f}; "
                "required >= 0.900000000000."
            )
    return failures


def contract_conformance() -> dict[str, Any]:
    contract = (
        ROOT / "contracts" / "v2.3.2-attribution-contract.md"
    ).read_text(encoding="utf-8")
    source = (ROOT / "ref" / "v232.py").read_text(encoding="utf-8")
    obligations = {
        "declares_D_A_P_Y_M_H_E_eta": all(
            token in contract
            for token in ("`D_t`", "`A_t`", "`P_t`", "`Y_t`", "`M_t`", "`H_E`", "`eta_x`")
        ),
        "exact_zero_spike_in_source": "ETA[0] == 0.0" in source,
        "interventional_public_api": "conditioned on do(A) and do(M)" in source,
        "environment_policy_functions_separate": (
            "def attribution_update(" in source
            and "def relief_update(" in source
        ),
        "K_is_readout_only": (
            "def posterior_readouts(" in source
            and 'posterior_store["K"]' not in source
        ),
        "independent_cartesian_oracle": "def _cartesian_update_oracle(" in source,
        "bounded_continuous_formation": (
            "FORMATION_LOG_BF_CAP" in source
            and "def formation_trajectory(" in source
        ),
    }
    anti = anti_authoring_audit()
    return {
        "obligations": obligations,
        "anti_authoring_assertions": anti,
        "passed": all(obligations.values()) and anti["passed"],
    }


def write_stop_artifacts(
    semantic: dict[str, Any],
    formation: dict[str, Any] | None,
    maintenance: dict[str, Any] | None,
    failures: list[str],
) -> None:
    conformance = contract_conformance()
    write_json(
        RESULT_ROOT / "contract-conformance-audit.json", conformance
    )
    stage_report = {
        "stage": "V2.3.2",
        "verdict": "FAIL_AT_GATE_2" if formation is not None else "FAIL_AT_GATE_1",
        "gate_status": {
            "gate_1_ten_semantic_proofs": gate_1_pass(semantic),
            "gate_2_recovery_and_nonidentifiability": (
                False if formation is not None else "not_run"
            ),
            "gate_3_formation_and_maintenance_assays": "not_run",
            "gate_4_seven_selective_lesions": "not_run",
            "gate_5_cumulative_robustness_anti_authoring": "not_run",
        },
        "failures": failures,
        "semantic_proofs": semantic,
        "formation_recovery": formation,
        "maintenance_recovery": maintenance,
        "contract_conformance": conformance,
        "sealed_challenges_accessed": False,
        "freeze_candidate_created": False,
    }
    write_json(RESULT_ROOT / "stage-report.json", stage_report)
    (RESULT_ROOT / "decisions.md").write_text(
        """# V2.3.2 decisions

- The frozen F and M subclaims are scored independently; neither can rescue
  the other.
- Actions and observation modes are interventions and are excluded from
  environmental evidence.
- The efficacy spike is the exact `eta=0` finite candidate. No epsilon,
  threshold, or posterior clamp is used.
- The formation inference API accepts theory variables only. Schedule
  regularity, timing, ordering, length, seed, and assay labels are absent.
- The Gate-2 stop rule is applied to the frozen seed blocks without
  temperature tuning, seed-stream substitution, or Gate-3 population
  substitution.
""",
        encoding="utf-8",
    )
    failure_lines = "\n".join(f"- {item}" for item in failures)
    (RESULT_ROOT / "development-failures.md").write_text(
        f"""# V2.3.2 development failures

## Prospective gate run

{failure_lines}

The failures are retained verbatim. Gates 3–5 were not run. The implemented
but unscored Gate-3/Gate-4 assay helpers are not evidence and are not a freeze.
""",
        encoding="utf-8",
    )
    milestone = ROOT / "results" / "milestone-3-v2.3.2-report.md"
    milestone.write_text(
        f"""# Suite v2 — V2.3.2 implementation outcome

Stage verdict: **FAIL at Gate 2; prospective ratchet stopped.**

Gate 1 passed all ten semantic obligations, including exact masked neutrality,
the exact efficacy spike, policy/environment separation, the pure-avoidance
confound, forced-engagement identification, and independent enumeration.

Gate 2 failed on the frozen open blocks:

{failure_lines}

All other Gate-2 criteria passed. Gates 3–5, cumulative regression, and the
sealed challenges were not run. No V2.3.2 freeze candidate is claimed.
""",
        encoding="utf-8",
    )
    manifest_inputs = [
        ROOT / "contracts" / "v2.3.2-attribution-contract.md",
        ROOT / "protocols" / "v2.3.2-F-analysis-plan.md",
        ROOT / "protocols" / "v2.3.2-M-analysis-plan.md",
        ROOT / "protocols" / "v2.3.2-F-dummy-bundle.json",
        ROOT / "protocols" / "v2.3.2-M-dummy-bundle.json",
        ROOT / "protocols" / "v2.3.2-parameters.json",
        ROOT / "ref" / "v232.py",
        ROOT / "tests" / "test_v232_attribution.py",
        ROOT / "run_v232_freeze.py",
        RESULT_ROOT / "gate-1.json",
        RESULT_ROOT / "gate-2.json",
        RESULT_ROOT / "contract-conformance-audit.json",
        RESULT_ROOT / "stage-report.json",
        RESULT_ROOT / "decisions.md",
        RESULT_ROOT / "development-failures.md",
        milestone,
    ]
    existing = [path for path in manifest_inputs if path.exists()]
    write_json(
        RESULT_ROOT / "failed-ratchet-manifest.json",
        {
            "stage": "V2.3.2",
            "status": "failed_gate_2_no_freeze",
            "development_seed_maximum": 747255,
            "gates_3_to_5_run": False,
            "sealed_challenges_accessed": False,
            "files": {
                str(path.relative_to(ROOT)): sha256(path)
                for path in existing
            },
        },
    )


def main() -> None:
    semantic = semantic_proofs()
    semantic_passed = gate_1_pass(semantic)
    write_json(
        RESULT_ROOT / "gate-1.json",
        {
            "stage": "V2.3.2",
            "gate": 1,
            "name": "ten semantic proofs",
            "passed": semantic_passed,
            "results": semantic,
            "failures": [] if semantic_passed else ["Gate 1 semantic obligations failed."],
        },
    )
    if not semantic_passed:
        write_stop_artifacts(
            semantic,
            None,
            None,
            ["Gate 1 semantic obligations failed."],
        )
        raise SystemExit("V2.3.2 ratchet stopped at Gate 1")

    formation = formation_recovery_assay()
    maintenance = recovery_assay()
    failures = gate_2_failures(formation, maintenance)
    write_json(
        RESULT_ROOT / "gate-2.json",
        {
            "stage": "V2.3.2",
            "gate": 2,
            "name": "identifiable recovery and calibrated non-identifiability",
            "passed": not failures,
            "results": {
                "formation": formation,
                "maintenance": maintenance,
            },
            "failures": failures,
        },
    )
    if failures:
        write_stop_artifacts(
            semantic, formation, maintenance, failures
        )
        raise SystemExit("V2.3.2 ratchet stopped at Gate 2")

    raise SystemExit(
        "Gate 2 unexpectedly passed; Gates 3–5 runner intentionally not "
        "entered in this failed prospective implementation."
    )


if __name__ == "__main__":
    main()
