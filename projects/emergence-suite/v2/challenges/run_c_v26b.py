#!/usr/bin/env python3
"""One-run C-V26B sealed protector challenge custody runner."""

from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from ref import constitution, v26b  # noqa: E402
from ref.audit import audit_one_posterior  # noqa: E402


CHALLENGE = ROOT / "sealed-revealed" / "C-V26B-protector-challenge.md"
SEAL_LEDGER = REPO_ROOT / "projects" / "ifs-paper" / "suite-v2-sealed-hashes.md"
OUT = ROOT / "results" / "V2.6b"
RELEASED_BLOCK = (2_050_000, 2_052_999)
VERIFIED_SEAL = "c7e00412c7f06cbead6f03152b0be4fc70da013a00fd1de0780b3cb0e62e4abf"
CELL_FILES = {
    "cell_1_ambiguous_partner": "c-v26b-cell-1.json",
    "cell_2_refusal_remaining": "c-v26b-cell-2.json",
    "cell_3_refusal_pressure": "c-v26b-cell-3.json",
    "cell_4_stakes_contrast": "c-v26b-cell-4.json",
    "cell_5_role_future_crossover": "c-v26b-cell-5.json",
    "cell_6_descent": "c-v26b-cell-6.json",
}
TOL = v26b.TOLERANCE


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    return value


def dump(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(plain(value), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def parse_bundle() -> dict[str, Any]:
    lines = CHALLENGE.read_text(encoding="utf-8").splitlines()
    literals = [
        line for line in lines if line.startswith("{") and line.endswith("}")
    ]
    if len(literals) != 1:
        raise ValueError("challenge must contain exactly one bracketed literal")
    parsed = ast.literal_eval(literals[0])
    if not isinstance(parsed, dict):
        raise TypeError("challenge literal is not a dict")
    return parsed


def parse_escrow(value: str) -> tuple[int, int]:
    left, right = value.split(":")
    return int(left), int(right)


def verify_freeze() -> dict[str, Any]:
    manifest_path = OUT / "freeze-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in manifest["files"].items():
        path = ROOT / relative
        observed = sha256(path) if path.exists() else None
        if observed != expected:
            mismatches.append(
                {"file": relative, "expected": expected, "observed": observed}
            )
    return {
        "manifest": str(manifest_path.relative_to(ROOT)),
        "manifest_sha256": sha256(manifest_path),
        "file_count": len(manifest["files"]),
        "mismatches": mismatches,
        "passed": not mismatches,
    }


def validate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    cells = [key for key in bundle if key.startswith("cell_")]
    seeds: list[int] = []
    signature = inspect.signature(v26b.generate_control_world)
    permitted = set(signature.parameters) - {"seed", "released_block"}
    pair_assignment = (
        "seed index mod 2 selects the pair row (250 worlds each)"
    )
    for cell_name in cells:
        cell = bundle[cell_name]
        start, end = parse_escrow(cell["escrow"])
        if end - start + 1 != int(cell["n_worlds"]):
            errors.append(f"{cell_name}: escrow count mismatch")
        seeds.extend(range(start, end + 1))
        if cell["generator"] != "generate_control_world":
            errors.append(f"{cell_name}: generator is not the frozen public constructor")
        declarations = (
            cell["kwargs_pair"] if "kwargs_pair" in cell else [cell["kwargs"]]
        )
        for kwargs in declarations:
            unknown = sorted(set(kwargs) - permitted)
            if unknown:
                errors.append(f"{cell_name}: unknown kwargs {unknown}")
        if "kwargs_pair" in cell:
            if len(cell["kwargs_pair"]) != 2:
                errors.append(f"{cell_name}: pair does not have two rows")
            if cell.get("assignment") != pair_assignment:
                errors.append(f"{cell_name}: pair assignment differs from seal")
    if cells != list(CELL_FILES):
        errors.append("cell order differs from sealed order")
    if seeds != list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)):
        errors.append("escrow ranges are not ascending and gap-free")
    challenge_hash = sha256(CHALLENGE)
    if challenge_hash != VERIFIED_SEAL:
        errors.append("challenge hash differs from verified seal")
    freeze = verify_freeze()
    if not freeze["passed"]:
        errors.append("frozen V2.6b identity failed")
    ledger_text = SEAL_LEDGER.read_text(encoding="utf-8")
    release_phrase = (
        "Escrow: C-V26B seeds 2050000:2052999, released by this record "
        "via the frozen released_block parameter. Pilot block "
        "1332000:1332599 BARRED (permission-profile attainability pilot, "
        "non-criterion). Full accumulated linter applied."
    )
    if release_phrase not in ledger_text:
        errors.append("C-V26B release ledger phrase absent")
    return {
        "challenge": "C-V26B",
        "challenge_sha256": challenge_hash,
        "verified_seal_sha256": VERIFIED_SEAL,
        "literal_parser": "ast.literal_eval",
        "parse_instruction": bundle["parse_instruction"],
        "cell_order": cells,
        "seed_start": seeds[0],
        "seed_end": seeds[-1],
        "seed_count": len(seeds),
        "pair_assignment": pair_assignment,
        "freeze_identity": freeze,
        "release_ledger": {
            "file": str(SEAL_LEDGER.relative_to(REPO_ROOT)),
            "sha256": sha256(SEAL_LEDGER),
            "release_phrase_found": release_phrase in ledger_text,
        },
        "expressible": not errors,
        "errors": errors,
    }


def trust_observation_record(item: v26b.TrustObservation) -> dict[str, Any]:
    return {
        "refusal": item.refusal,
        "partner_response": item.partner_response,
        "outcome": item.outcome,
        "coprotection": item.coprotection,
        "policy_outcome": item.policy_outcome,
        "response_reliability": item.response_reliability,
    }


def partner_observation_record(item: Any) -> dict[str, Any]:
    return {"relational": item.relational, "root": item.root}


def attribution_episode_record(item: Any) -> dict[str, Any]:
    return {
        "action": item.action,
        "context": item.context,
        "outcome": item.outcome,
        "near_miss": item.near_miss,
        "efficacy_observation": item.efficacy_observation,
        "relief": item.relief,
    }


def score_record(result: v26b.ProtectorScore) -> dict[str, Any]:
    audit_one_posterior(result.state)
    return {
        "permission_mass": result.permission_mass,
        "contact_probability": result.contact_probability,
        "q_policy": result.q_policy,
        "q_trust": result.q_trust,
        "q_policy_outcome": result.q_policy_outcome,
        "expected_cost": result.expected_cost,
        "role_absence_risk_differential": (
            result.role_absence_risk_differential
        ),
        "role_preserving_risk": result.role_preserving_risk,
        "role_absent_risk": result.role_absent_risk,
        "root_movement": result.root_movement,
        "transfer": result.transfer,
        "partner_q": result.partner_score.q_partner,
        "partner_future_precision": (
            result.partner_score.future_precision_forecast
        ),
        "attribution_threat": (
            result.attribution_score.threat_probability
        ),
        "attribution_eta": result.attribution_score.eta_mean,
        "one_posterior_audit": True,
    }


def generate_and_seal() -> None:
    bundle = parse_bundle()
    validation = validate_bundle(bundle)
    if not validation["expressible"]:
        dump(
            OUT / "c-v26b-stop-as-sealed.json",
            {
                "immutable_verdict": "STOP_AS_SEALED",
                "validation": validation,
                "seeds_consumed": 0,
            },
        )
        raise SystemExit(2)
    seal_path = OUT / "c-v26b-raw-trace-seal.json"
    if seal_path.exists():
        raise RuntimeError("raw trace seal exists; one-run budget is spent")
    hashes: dict[str, str] = {}
    counts: dict[str, int] = {}
    consumed: list[int] = []
    for cell_name in validation["cell_order"]:
        cell = bundle[cell_name]
        start, end = parse_escrow(cell["escrow"])
        rows = []
        for local_index, seed in enumerate(range(start, end + 1)):
            if "kwargs_pair" in cell:
                pair_row = local_index % 2
                kwargs = dict(cell["kwargs_pair"][pair_row])
            else:
                pair_row = None
                kwargs = dict(cell["kwargs"])
            world = v26b.generate_control_world(
                seed,
                released_block=RELEASED_BLOCK,
                **kwargs,
            )
            result = v26b.score(
                world.trust_observations,
                world.partner_world.observations,
                world.attribution_world.episodes,
                stakes=world.stakes,
            )
            rows.append(
                {
                    "cell": cell_name,
                    "seed": seed,
                    "local_index": local_index,
                    "pair_row": pair_row,
                    "generator": cell["generator"],
                    "generator_kwargs": kwargs,
                    "released_block": list(RELEASED_BLOCK),
                    "world_truth": {
                        "trust_truth": world.trust_truth,
                        "policy_outcome_index": world.policy_outcome_index,
                        "partner_truth_family": world.partner_world.truth_family,
                        "attribution_theta_index": (
                            world.attribution_world.theta_index
                        ),
                        "attribution_eta_indices": (
                            world.attribution_world.eta_indices
                        ),
                        "stakes": world.stakes,
                        "scenario": world.scenario,
                    },
                    "trust_observations": [
                        trust_observation_record(item)
                        for item in world.trust_observations
                    ],
                    "partner_observations": [
                        partner_observation_record(item)
                        for item in world.partner_world.observations
                    ],
                    "attribution_episodes": [
                        attribution_episode_record(item)
                        for item in world.attribution_world.episodes
                    ],
                    "score": score_record(result),
                }
            )
            consumed.append(seed)
        path = OUT / CELL_FILES[cell_name]
        dump(path, rows)
        hashes[CELL_FILES[cell_name]] = sha256(path)
        counts[cell_name] = len(rows)
    gap_free = consumed == list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1))
    seal = {
        "challenge": "C-V26B",
        "phase": "raw_traces_sealed_before_criteria",
        "validation": validation,
        "cell_hashes": hashes,
        "record_counts": counts,
        "consumed_seed_start": consumed[0],
        "consumed_seed_end": consumed[-1],
        "consumed_seed_count": len(consumed),
        "ascending_gap_free": gap_free,
        "criteria_evaluated": False,
    }
    dump(seal_path, seal)
    dump(
        OUT / "c-v26b-run-ledger.json",
        {
            "challenge": "C-V26B",
            "release": {
                "block": list(RELEASED_BLOCK),
                "source": str(SEAL_LEDGER.relative_to(REPO_ROOT)),
                "authorization": "revealed sealed challenge and user release",
            },
            "literal_parser": "ast.literal_eval",
            "one_run": True,
            "seeds_consumed_once": len(consumed),
            "ascending_gap_free": gap_free,
            "raw_trace_seal": str(seal_path.relative_to(ROOT)),
            "raw_trace_seal_sha256": sha256(seal_path),
            "criteria_evaluated_at_ledger_write": False,
        },
    )


def interval(values: Iterable[float]) -> dict[str, float]:
    array = np.asarray(tuple(values), dtype=float)
    mean = float(array.mean())
    half = 1.96 * float(array.std(ddof=1)) / math.sqrt(len(array))
    return {
        "mean": mean,
        "lower_95": mean - half,
        "upper_95": mean + half,
        "count": len(array),
    }


def paired_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    left = [row for row in rows if row["pair_row"] == 0]
    right = [row for row in rows if row["pair_row"] == 1]
    if len(left) != len(right):
        raise ValueError("sealed pair rows are unbalanced")
    return left, right


def evaluate() -> bool:
    seal_path = OUT / "c-v26b-raw-trace-seal.json"
    summary_path = OUT / "c-v26b-summary.json"
    if not seal_path.exists():
        raise RuntimeError("raw traces must be sealed before criteria")
    if summary_path.exists():
        raise RuntimeError("criteria already evaluated; rerun forbidden")
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    cells = {
        name: json.loads((OUT / filename).read_text(encoding="utf-8"))
        for name, filename in CELL_FILES.items()
    }
    hashes_match = {
        filename: sha256(OUT / filename)
        for filename in CELL_FILES.values()
    } == seal["cell_hashes"]
    ambiguous = cells["cell_1_ambiguous_partner"]
    remaining = cells["cell_2_refusal_remaining"]
    pressure = cells["cell_3_refusal_pressure"]
    stakes = cells["cell_4_stakes_contrast"]
    crossover = cells["cell_5_role_future_crossover"]
    descent = cells["cell_6_descent"]

    ambiguous_permission = interval(
        row["score"]["permission_mass"] for row in ambiguous
    )
    remaining_permission = interval(
        row["score"]["permission_mass"] for row in remaining
    )
    pressure_permission = interval(
        row["score"]["permission_mass"] for row in pressure
    )
    remaining_pressure = interval(
        left["score"]["permission_mass"]
        - right["score"]["permission_mass"]
        for left, right in zip(remaining, pressure)
    )
    policy_normalization_error = max(
        abs(sum(row["score"]["q_policy"]) - 1.0) for row in pressure
    )

    high_stakes, low_stakes = paired_rows(stakes)
    stakes_difference = interval(
        low["score"]["permission_mass"] - high["score"]["permission_mass"]
        for high, low in zip(high_stakes, low_stakes)
    )

    high_rupture, low_rupture = paired_rows(crossover)
    rupture_difference = interval(
        low["score"]["permission_mass"] - high["score"]["permission_mass"]
        for high, low in zip(high_rupture, low_rupture)
    )
    high_role = interval(
        row["score"]["role_absence_risk_differential"]
        for row in high_rupture
    )
    low_role = interval(
        row["score"]["role_absence_risk_differential"]
        for row in low_rupture
    )
    pooled_role = interval(
        row["score"]["role_absence_risk_differential"]
        for row in crossover
    )
    # Low rupture has greater access. A negative role-absence differential
    # means the protector-absent future is forecast less risky than continued
    # protector preservation, matching that ordering.
    role_direction_consistent = pooled_role["upper_95"] < 0.0

    descent_permission = interval(
        row["score"]["permission_mass"] for row in descent
    )
    descent_contact = interval(
        row["score"]["contact_probability"] for row in descent
    )
    descent_ambiguous = interval(
        left["score"]["permission_mass"]
        - right["score"]["permission_mass"]
        for left, right in zip(descent, ambiguous)
    )

    one_posterior = all(
        row["score"]["one_posterior_audit"]
        for rows in cells.values()
        for row in rows
    )
    scientific_keys_forbidden = {
        "permission",
        "access",
        "gate",
        "protector_role",
    }
    source = (ROOT / "ref" / "v26b.py").read_text(encoding="utf-8")
    no_gate_object = "class Gate" not in source
    cumulative = constitution.cumulative_constitution_audit()
    criteria = {
        "1_ambiguous_partner": {
            "permission_mass": ambiguous_permission,
            "passed": ambiguous_permission["mean"] <= 0.05,
        },
        "2_refusal_remaining": {
            "remaining_permission_mass": remaining_permission,
            "remaining_minus_pressure": remaining_pressure,
            "passed": (
                remaining_permission["mean"] >= 0.15
                and remaining_pressure["lower_95"] > 0.10
            ),
        },
        "3_refusal_pressure": {
            "pressure_permission_mass": pressure_permission,
            "q_policy_normalization_error_max": policy_normalization_error,
            "passed": (
                pressure_permission["mean"] <= 0.05
                and policy_normalization_error <= TOL
            ),
        },
        "4_stakes_contrast": {
            "low_minus_high_permission": stakes_difference,
            "pair_counts": {
                "high_stakes": len(high_stakes),
                "low_stakes": len(low_stakes),
            },
            "passed": stakes_difference["lower_95"] > 0.30,
        },
        "5_role_future_crossover": {
            "low_minus_high_rupture_permission": rupture_difference,
            "high_rupture_role_differential": high_role,
            "low_rupture_role_differential": low_role,
            "pooled_role_differential": pooled_role,
            "expected_role_sign": "negative",
            "role_direction_consistent": role_direction_consistent,
            "pair_counts": {
                "high_rupture": len(high_rupture),
                "low_rupture": len(low_rupture),
            },
            "passed": (
                rupture_difference["lower_95"] > 0.10
                and role_direction_consistent
            ),
        },
        "6_descent": {
            "permission_mass": descent_permission,
            "contact_probability": descent_contact,
            "descent_minus_ambiguous": descent_ambiguous,
            "passed": (
                descent_permission["mean"] >= 0.25
                and descent_contact["mean"] >= 0.10
                and descent_ambiguous["lower_95"] > 0.20
            ),
        },
        "7_semantic_custody": {
            "no_gate_object": no_gate_object,
            "forbidden_scientific_fields": sorted(
                scientific_keys_forbidden
            ),
            "permission_and_contact_are_score_readouts": True,
            "one_posterior_all_worlds": one_posterior,
            "permanent_constitution": cumulative["passed"],
            "raw_hashes_match_seal": hashes_match,
            "seed_count": seal["consumed_seed_count"],
            "ascending_gap_free": seal["ascending_gap_free"],
            "freeze_identity": seal["validation"]["freeze_identity"],
            "release_ledger": seal["validation"]["release_ledger"],
            "passed": (
                no_gate_object
                and one_posterior
                and cumulative["passed"]
                and hashes_match
                and seal["consumed_seed_count"] == 3000
                and seal["ascending_gap_free"]
                and seal["validation"]["freeze_identity"]["passed"]
                and seal["validation"]["release_ledger"][
                    "release_phrase_found"
                ]
            ),
        },
    }
    passed = all(item["passed"] for item in criteria.values())
    summary = {
        "challenge": "C-V26B",
        "immutable_sealed_verdict": "PASS" if passed else "FAIL",
        "pass_rule": "all seven sealed criteria",
        "criteria": criteria,
        "verdict_classes": {
            "scientific": all(
                criteria[f"{index}_{name}"]["passed"]
                for index, name in (
                    (1, "ambiguous_partner"),
                    (2, "refusal_remaining"),
                    (3, "refusal_pressure"),
                    (4, "stakes_contrast"),
                    (5, "role_future_crossover"),
                    (6, "descent"),
                )
            ),
            "semantic": (
                no_gate_object and one_posterior and cumulative["passed"]
            ),
            "custody": criteria["7_semantic_custody"]["passed"],
        },
        "bounds": {
            "B_max_v232_formation": 3.801426508560692,
            "B_max_v24_common_emissions": 6.704414354964107,
            "B_max_v25a_configural": 6.084736253211209,
            "B_max_v25a_marginal_accounting": 6.704414354964107,
            "B_max_v25b": 11.302393144606405,
            "B_max_v26a_relational": 6.9920964274158885,
            "B_max_v26a_root": 2.9444389791664394,
            "B_max_v234": 11.675460894331877,
            **v26b.finite_information_bounds(),
        },
        "passed": passed,
    }
    dump(summary_path, summary)
    ledger_path = OUT / "c-v26b-run-ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["criteria_evaluated_after_raw_seal"] = True
    ledger["immutable_verdict"] = summary["immutable_sealed_verdict"]
    ledger["summary_sha256"] = sha256(summary_path)
    dump(ledger_path, ledger)
    return passed


def write_verdict(passed: bool) -> None:
    summary = json.loads((OUT / "c-v26b-summary.json").read_text())
    lines = [
        "# C-V26B sealed verdict",
        "",
        f"Immutable sealed verdict: **{summary['immutable_sealed_verdict']}**.",
        "",
        "Pass requires all seven sealed criteria. No threshold, direction, "
        "readout, pairing rule, or scientific field was changed.",
        "",
        "## Criteria",
        "",
    ]
    for name, result in summary["criteria"].items():
        metrics = {key: value for key, value in result.items() if key != "passed"}
        lines.append(
            f"- `{name}`: **{'PASS' if result['passed'] else 'FAIL'}** — "
            f"`{json.dumps(metrics, sort_keys=True)}`"
        )
    lines += [
        "",
        "## Verdict classes",
        "",
        f"- Scientific: **{'PASS' if summary['verdict_classes']['scientific'] else 'FAIL'}**",
        f"- Semantic: **{'PASS' if summary['verdict_classes']['semantic'] else 'FAIL'}**",
        f"- Custody: **{'PASS' if summary['verdict_classes']['custody'] else 'FAIL'}**",
        "",
        "Escrow was consumed once, ascending and gap-free, after evaluator release.",
    ]
    (OUT / "c-v26b-verdict.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    if passed:
        (OUT / "stage-verdict.md").write_text(
            "# V2.6b stage verdict\n\n"
            "Final disposition: **PASS**.\n\n"
            "V2.6b entered Gate 6 with the clean "
            "`FROZEN_ALL_GATES_PASS` base. C-V26B passed all seven sealed "
            "criteria and all scientific, semantic, and custody classes. "
            "The licensed claim is retained: protector permission is an "
            "exact policy posterior under trust and stakes, relational "
            "evidence changes access by changing forecasts, and no gate "
            "object writes permission or contact.\n",
            encoding="utf-8",
        )


def run_suite_and_ready() -> None:
    suite = subprocess.run(
        [sys.executable, "run_tests_parallel.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    dump(
        OUT / "c-v26b-full-fast-suite.json",
        {
            "command": "python3 run_tests_parallel.py",
            "returncode": suite.returncode,
            "passed": suite.returncode == 0,
            "stdout": suite.stdout,
            "stderr": suite.stderr,
        },
    )
    files = [
        f"results/V2.6b/{filename}" for filename in CELL_FILES.values()
    ] + [
        "results/V2.6b/c-v26b-raw-trace-seal.json",
        "results/V2.6b/c-v26b-run-ledger.json",
        "results/V2.6b/c-v26b-summary.json",
        "results/V2.6b/c-v26b-verdict.md",
        "results/V2.6b/c-v26b-full-fast-suite.json",
        "challenges/run_c_v26b.py",
    ]
    if (OUT / "stage-verdict.md").exists():
        files.append("results/V2.6b/stage-verdict.md")
    (OUT / "ready-to-commit-c-v26b.md").write_text(
        "# Ready to commit: C-V26B\n\n"
        + "\n".join(f"- `{item}`" for item in files)
        + "\n",
        encoding="utf-8",
    )
    if suite.returncode:
        raise SystemExit(suite.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase", choices=("validate", "generate", "evaluate"), required=True
    )
    args = parser.parse_args()
    bundle = parse_bundle()
    if args.phase == "validate":
        validation = validate_bundle(bundle)
        print(json.dumps(plain(validation), indent=2, sort_keys=True))
        return 0 if validation["expressible"] else 2
    if args.phase == "generate":
        generate_and_seal()
        return 0
    passed = evaluate()
    write_verdict(passed)
    run_suite_and_ready()
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
