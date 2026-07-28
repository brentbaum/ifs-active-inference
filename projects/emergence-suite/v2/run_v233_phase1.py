"""Generate V2.3.3 phase-1 public constitution reports only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ref.constitution import (
    cumulative_graded_update_audit,
    publish_stratified_update_distribution,
)


ROOT = Path(__file__).resolve().parent
RESULT_ROOT = ROOT / "results" / "V2.3.3"
CONTRACT = ROOT / "contracts" / "v2.3.3-maintenance-contract.md"
PLAN = ROOT / "protocols" / "v2.3.3-analysis-plan.md"
DUMMY = ROOT / "protocols" / "v2.3.3-public-dummy.json"
PARAMETERS = ROOT / "protocols" / "v2.3.3-parameters.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def verify_dummy_hashes(dummy: dict[str, Any]) -> dict[str, Any]:
    mismatches = []
    for fixture in dummy["formed_world_fixtures"]:
        canonical = json.dumps(
            fixture["serialized_state"],
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
        actual = hashlib.sha256(canonical).hexdigest()
        expected = fixture["state_sha256"]
        clone_mismatches = [
            arm
            for arm, clone_hash in fixture["clone_hashes"].items()
            if clone_hash != expected
        ]
        if actual != expected or clone_mismatches:
            mismatches.append(
                {
                    "stratum": fixture["stratum"],
                    "expected": expected,
                    "actual": actual,
                    "clone_mismatches": clone_mismatches,
                }
            )
    return {
        "fixture_count": len(dummy["formed_world_fixtures"]),
        "mismatches": mismatches,
        "passed": not mismatches,
    }


def public_conformance() -> dict[str, Any]:
    contract = CONTRACT.read_text(encoding="utf-8")
    plan = PLAN.read_text(encoding="utf-8")
    dummy = json.loads(DUMMY.read_text(encoding="utf-8"))
    parameters = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    proof_head = plan.split(
        "## Gate 1 — twelve semantic proofs", 1
    )[1].split("## Gate 2", 1)[0]
    proof_count = sum(
        proof_head.lstrip().startswith(f"{index}.")
        or f"\n{index}. " in proof_head
        for index in range(1, 13)
    )
    seed_values = []
    for key in (
        "candidate_seed_block",
    ):
        seed_values.extend(
            parameters["formed_world_bank"][key]
        )
    for key in ("development_seed_block", "robustness_seed_block"):
        seed_values.extend(parameters["maintenance"][key])
    checks = {
        "availability_only_route": (
            "policy → availability → delivered evidence → H/G"
            in contract
        ),
        "do_action_controls_M_only": (
            "`do(A_t)` changes `M_t` only" in contract
        ),
        "missing_BF_zero": (
            "incremental log BF is exactly zero" in contract
        ),
        "excluded_attribution_variables": all(
            value in contract
            for value in (
                "Efficacy",
                "prevented catastrophe",
                "relief",
                "counterfactual-attribution",
            )
        ),
        "three_bank_strata": (
            set(
                parameters["formed_world_bank"][
                    "initial_strength_strata"
                ]
            )
            == {"moderate", "strong", "very_strong"}
        ),
        "six_arms": len(parameters["maintenance"]["arms"]) == 6,
        "five_censoring_doses": (
            parameters["maintenance"]["censoring_doses"]
            == [0.0, 0.25, 0.5, 0.75, 1.0]
        ),
        "twelve_gate_1_proofs": proof_count == 12,
        "gate_2_present": "## Gate 2" in plan,
        "gate_3_present": "## Gate 3" in plan,
        "eight_gate_4_rows": (
            plan.split("## Gate 4", 1)[1].split("## Gate 5", 1)[0]
            .count("\n|")
            - 2
            == 8
        ),
        "gate_5_present": "## Gate 5" in plan,
        "two_block_gate_6": (
            "C-V233-M-bank" in plan and "C-V233-M." in plan
        ),
        "four_verdict_classes": all(
            value in plan
            for value in (
                "**Scientific outcomes:**",
                "**Semantic integrity:**",
                "**Distributional stress:**",
                "**Process-custody:**",
            )
        ),
        "all_development_seeds_below_800000": max(seed_values) < 800000,
        "dummy_is_non_scientific": (
            dummy["synthetic_schema_fixture"]
            and not dummy["scientific_result"]
            and not dummy["bank_admissible"]
        ),
    }
    dummy_hashes = verify_dummy_hashes(dummy)
    return {
        "stage": "V2.3.3-phase-1",
        "mechanism_implemented": False,
        "bank_generated": False,
        "checks": checks,
        "gate_1_proof_count": proof_count,
        "maximum_reserved_development_seed": max(seed_values),
        "dummy_hash_verification": dummy_hashes,
        "artifact_hashes": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in (CONTRACT, PLAN, DUMMY, PARAMETERS)
        },
        "passed": all(checks.values()) and dummy_hashes["passed"],
    }


def main() -> None:
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    constitution = cumulative_graded_update_audit()
    stress = publish_stratified_update_distribution()
    conformance = public_conformance()
    if not constitution["passed"]:
        raise AssertionError("revised cumulative constitution failed")
    if not conformance["passed"]:
        raise AssertionError(f"public artifact conformance failed: {conformance}")
    write_json(
        RESULT_ROOT / "revised-graded-update-constitution-audit.json",
        constitution,
    )
    write_json(
        RESULT_ROOT / "stratified-update-distribution.json",
        stress,
    )
    write_json(
        RESULT_ROOT / "phase-1-public-conformance.json",
        conformance,
    )

    formation = constitution["stages"]["V2.3.2-formation"][
        "sections"
    ]
    stage_rows = "\n".join(
        f"| {name} | {'PASS' if stage['passed'] else 'FAIL'} | "
        f"{' / '.join(section for section, value in stage['sections'].items() if value['passed'])} |"
        for name, stage in constitution["stages"].items()
    )
    stress_rows = "\n".join(
        f"| {name} | {values['count']} | {values['p50']:.12g} | "
        f"{values['p90']:.12g} | {values['p99']:.12g} | "
        f"{values['maximum']:.12g} |"
        for name, values in stress["strata"].items()
    )
    verification_path = RESULT_ROOT / "full-suite-verification.json"
    suite_note = ""
    if verification_path.is_file():
        verification = json.loads(
            verification_path.read_text(encoding="utf-8")
        )
        suite_note = f"""

The final cumulative command
`{verification['command']}` passed all
`{verification['tests_run']}` tests in one run, including all
`{verification['constitution_tests_run']}` constitution tests. No V2.3.3
mechanism or formed-world bank was executed.
"""
    report = f"""# V2.3.3 phase 1 — revised constitution and public artifacts

No V2.3.3 maintenance mechanism was implemented and no formed-world bank was
generated. This phase freezes only the permanent constitutional audit and the
public contract, analysis plan, parameters, and dummy fixture.

## Revised cumulative constitution

Overall: **PASS**.

| Standing stage | Verdict | Passing sections |
| --- | --- | --- |
{stage_rows}

For V2.3.2 formation, update-identity maximum error was
`{formation['A_update_identity']['maximum_absolute_identity_error']:.12g}`
across
`{formation['A_update_identity']['pairwise_increments_checked']}` pairwise
increments. The exact table supremum is
`B_max={formation['B_finite_information']['enumerated_B_max']:.15g}` and the
implied binary probability-change bound is
`{formation['B_finite_information']['implied_binary_probability_change_bound']:.15g}`.
The homotopy checked
`{formation['C_evidence_strength_homotopy']['q_P_curves_checked']}` exact
`q(P;alpha)` curves on 101 alpha values; maximum analytic-enumeration error
was
`{formation['C_evidence_strength_homotopy']['maximum_exact_enumeration_vs_analytic_error']:.3g}`,
forward/reverse hysteresis error was
`{formation['C_evidence_strength_homotopy']['maximum_forward_reverse_hysteresis_error']:.3g}`,
and both monotonicity-failure counts were zero. Composition maximum error was
`{formation['D_composition']['maximum_error']:.3g}`.

## Descriptive update stress profile

Classification: **distributional stress; non-criterial**. No threshold or
scientific verdict is derived from these values.

| Stratum | n | p50 | p90 | p99 | maximum |
| --- | ---: | ---: | ---: | ---: | ---: |
{stress_rows}

## Public-artifact conformance

All `{len(conformance['checks'])}` public conformance checks passed, including
the twelve Gate-1 obligations, eight Gate-4 lesion rows, four verdict classes,
two-block Gate-6 custody, six arms, five censoring doses, and development
seeds below 800000. All three synthetic dummy states and every arm clone hash
recomputed exactly. The dummy is non-scientific and bank-inadmissible.
{suite_note}
"""
    (RESULT_ROOT / "phase-1-report.md").write_text(
        report, encoding="utf-8"
    )


if __name__ == "__main__":
    main()
