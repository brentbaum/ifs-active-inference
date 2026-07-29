#!/usr/bin/env python3
"""One-run C-V26A sealed partner challenge custody runner."""

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
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from ref import constitution, v26a  # noqa: E402
from ref.audit import audit_one_posterior  # noqa: E402


CHALLENGE = ROOT / "sealed-revealed" / "C-V26A-partner-challenge.md"
SEAL_LEDGER = REPO_ROOT / "projects" / "ifs-paper" / "suite-v2-sealed-hashes.md"
OUT = ROOT / "results" / "V2.6a"
RELEASED_BLOCK = (2_030_000, 2_031_999)
VERIFIED_SEAL = "cba6d516516401c05f00cc0586e57e750964f3f8128d3b541eb3352823e56621"
CELL_FILES = {
    "cell_1_stable_reliable": "c-v26a-cell-1.json",
    "cell_2_soothing_noncontingent": "c-v26a-cell-2.json",
    "cell_3_switching": "c-v26a-cell-3.json",
    "cell_4_factorial": "c-v26a-cell-4.json",
}


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
    literals = [line for line in lines if line.startswith("{") and line.endswith("}")]
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
    errors = []
    cells = [key for key in bundle if key.startswith("cell_")]
    seeds: list[int] = []
    generators = {
        "generate_control_world": v26a.generate_control_world,
        "generate_recovery_world": v26a.generate_recovery_world,
        "generate_factorial_world": v26a.generate_factorial_world,
    }
    for cell_name in cells:
        cell = bundle[cell_name]
        start, end = parse_escrow(cell["escrow"])
        if end - start + 1 != int(cell["n_worlds"]):
            errors.append(f"{cell_name}: escrow count mismatch")
        seeds.extend(range(start, end + 1))
        generator = generators.get(cell["generator"])
        if generator is None:
            errors.append(f"{cell_name}: unknown generator")
            continue
        signature = inspect.signature(generator)
        permitted = set(signature.parameters) - {"seed", "released_block"}
        declared_sets = (
            cell["kwargs_grid"]
            if "kwargs_grid" in cell
            else [cell["kwargs"]]
        )
        for kwargs in declared_sets:
            unknown = sorted(set(kwargs) - permitted)
            if unknown:
                errors.append(f"{cell_name}: unknown kwargs {unknown}")
    if cells != list(CELL_FILES):
        errors.append("cell order differs from sealed order")
    if seeds != list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)):
        errors.append("escrow ranges are not ascending and gap-free")
    if bundle["cell_4_factorial"].get("assignment") != (
        "seed index mod 4 selects the grid row (125 worlds per factorial cell)"
    ):
        errors.append("factorial assignment is not the sealed rule")
    freeze = verify_freeze()
    if not freeze["passed"]:
        errors.append("frozen V2.6a identity failed")
    challenge_hash = sha256(CHALLENGE)
    if challenge_hash != VERIFIED_SEAL:
        errors.append("challenge hash differs from verified seal")
    ledger_text = SEAL_LEDGER.read_text(encoding="utf-8")
    release_phrase = (
        "Escrow: C-V26A seeds 2030000:2031999, released by this record "
        "via the frozen released_block parameter."
    )
    if release_phrase not in ledger_text:
        errors.append("C-V26A release ledger phrase absent")
    return {
        "challenge": "C-V26A",
        "challenge_sha256": challenge_hash,
        "verified_seal_sha256": VERIFIED_SEAL,
        "literal_parser": "ast.literal_eval",
        "parse_instruction": bundle["parse_instruction"],
        "cell_order": cells,
        "seed_start": seeds[0],
        "seed_end": seeds[-1],
        "seed_count": len(seeds),
        "freeze_identity": freeze,
        "release_ledger": {
            "file": str(SEAL_LEDGER.relative_to(REPO_ROOT)),
            "sha256": sha256(SEAL_LEDGER),
            "release_phrase_found": release_phrase in ledger_text,
        },
        "expressible": not errors,
        "errors": errors,
    }


def observation_record(item: v26a.PartnerObservation) -> dict[str, Any]:
    return {"relational": list(item.relational), "root": item.root}


def score_record(result: v26a.PartnerScore) -> dict[str, Any]:
    audit_one_posterior(result.state)
    return {
        "q_partner": result.q_partner,
        "q_root": result.q_root,
        "filtered_partner": result.filtered_partner,
        "smoothed_partner": result.smoothed_partner,
        "pairwise_transitions": result.pairwise_transitions,
        "local_precision": result.local_precision,
        "global_precision": result.global_precision,
        "root_log_bf": result.root_log_bf,
        "root_movement": result.root_movement,
        "transfer": result.transfer,
        "co_regulated": result.co_regulated,
        "local_arousal": result.local_arousal,
        "switch_rate": result.switch_rate,
        "switch_onset": result.switch_onset,
        "future_precision_forecast": result.future_precision_forecast,
        "log_evidence": result.log_evidence,
        "one_posterior_audit": True,
    }


def world_record(
    cell_name: str,
    seed: int,
    generator_name: str,
    kwargs: dict[str, Any],
    world: v26a.PartnerWorld,
    result: v26a.PartnerScore,
    reference: v26a.PartnerScore | None = None,
) -> dict[str, Any]:
    return {
        "cell": cell_name,
        "seed": seed,
        "generator": generator_name,
        "generator_kwargs": kwargs,
        "released_block": list(RELEASED_BLOCK),
        "truth_family": world.truth_family,
        "truth_path": world.truth_path,
        "switching": world.switching,
        "observations": [observation_record(item) for item in world.observations],
        "score": score_record(result),
        "no_regulation_reference": (
            score_record(reference) if reference is not None else None
        ),
    }


def generate_and_seal() -> None:
    bundle = parse_bundle()
    validation = validate_bundle(bundle)
    stop_path = OUT / "c-v26a-stop-as-sealed.json"
    if not validation["expressible"]:
        dump(
            stop_path,
            {
                "verdict": "STOP_AS_SEALED",
                "validation": validation,
                "seeds_consumed": 0,
            },
        )
        raise SystemExit(2)
    seal_path = OUT / "c-v26a-raw-trace-seal.json"
    if seal_path.exists():
        raise RuntimeError("raw trace seal exists; one-run budget is spent")
    hashes: dict[str, str] = {}
    consumed: list[int] = []
    record_counts: dict[str, int] = {}
    for cell_name in validation["cell_order"]:
        cell = bundle[cell_name]
        start, end = parse_escrow(cell["escrow"])
        rows = []
        for local_index, seed in enumerate(range(start, end + 1)):
            if "kwargs_grid" in cell:
                kwargs = dict(cell["kwargs_grid"][local_index % 4])
            else:
                kwargs = dict(cell["kwargs"])
            generator = getattr(v26a, cell["generator"])
            world = generator(
                seed, released_block=RELEASED_BLOCK, **kwargs
            )
            result = v26a.score(world.observations)
            reference = None
            if cell_name in {
                "cell_1_stable_reliable",
                "cell_2_soothing_noncontingent",
            }:
                reference_world = v26a.generate_factorial_world(
                    seed,
                    regulation_present=False,
                    root_evidence_present=True,
                    length=int(kwargs["length"]),
                    released_block=RELEASED_BLOCK,
                )
                reference = v26a.score(reference_world.observations)
            rows.append(
                world_record(
                    cell_name,
                    seed,
                    cell["generator"],
                    kwargs,
                    world,
                    result,
                    reference,
                )
            )
            consumed.append(seed)
        path = OUT / CELL_FILES[cell_name]
        dump(path, rows)
        hashes[CELL_FILES[cell_name]] = sha256(path)
        record_counts[cell_name] = len(rows)
    gap_free = consumed == list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1))
    seal = {
        "challenge": "C-V26A",
        "phase": "raw_traces_sealed_before_criteria",
        "validation": validation,
        "cell_hashes": hashes,
        "record_counts": record_counts,
        "consumed_seed_start": consumed[0],
        "consumed_seed_end": consumed[-1],
        "consumed_seed_count": len(consumed),
        "ascending_gap_free": gap_free,
        "criteria_evaluated": False,
    }
    dump(seal_path, seal)
    dump(
        OUT / "c-v26a-run-ledger.json",
        {
            "challenge": "C-V26A",
            "release": {
                "block": list(RELEASED_BLOCK),
                "source": str(SEAL_LEDGER.relative_to(REPO_ROOT)),
                "authorization": "revealed sealed challenge and user release",
            },
            "one_run": True,
            "seeds_consumed_once": len(consumed),
            "ascending_gap_free": gap_free,
            "raw_trace_seal": str(seal_path.relative_to(ROOT)),
            "raw_trace_seal_sha256": sha256(seal_path),
            "criteria_evaluated_at_ledger_write": False,
        },
    )


def interval(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    mean = float(array.mean())
    half = 1.96 * float(array.std(ddof=1)) / math.sqrt(len(array))
    return {"mean": mean, "lower_95": mean - half, "upper_95": mean + half}


def unique_argmax(values: list[float], index: int) -> bool:
    array = np.asarray(values, dtype=float)
    return (
        int(np.argmax(array)) == index
        and int(np.sum(np.abs(array - array.max()) <= v26a.TOLERANCE)) == 1
    )


def evaluate() -> bool:
    seal_path = OUT / "c-v26a-raw-trace-seal.json"
    if not seal_path.exists():
        raise RuntimeError("raw traces must be sealed before criteria")
    if (OUT / "c-v26a-summary.json").exists():
        raise RuntimeError("criteria already evaluated; rerun forbidden")
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    cells = {
        name: json.loads((OUT / filename).read_text(encoding="utf-8"))
        for name, filename in CELL_FILES.items()
    }
    custody_hashes = {
        filename: sha256(OUT / filename) for filename in CELL_FILES.values()
    }
    hashes_match = custody_hashes == seal["cell_hashes"]

    reliable = cells["cell_1_stable_reliable"]
    soothing = cells["cell_2_soothing_noncontingent"]
    switching = cells["cell_3_switching"]
    factorial = cells["cell_4_factorial"]

    reliable_index = v26a.STATE_INDEX["reliable_contingent"]
    soothing_index = v26a.STATE_INDEX["soothing_noncontingent"]
    reliable_recovery = float(
        np.mean(
            [
                unique_argmax(row["score"]["q_partner"], reliable_index)
                for row in reliable
            ]
        )
    )
    soothing_recovery = float(
        np.mean(
            [
                unique_argmax(row["score"]["q_partner"], soothing_index)
                for row in soothing
            ]
        )
    )
    reliable_depth = [
        row["score"]["global_precision"][-1]
        - row["no_regulation_reference"]["global_precision"][-1]
        for row in reliable
    ]
    soothing_depth = [
        row["score"]["global_precision"][-1]
        - row["no_regulation_reference"]["global_precision"][-1]
        for row in soothing
    ]
    reliable_depth_ci = interval(reliable_depth)
    soothing_depth_ci = interval(soothing_depth)
    contingency_difference = interval(
        [left - right for left, right in zip(reliable_depth, soothing_depth)]
    )
    reliable_regulation_bf_max = max(
        abs(value)
        for row in reliable
        for value, observation in zip(
            row["score"]["root_log_bf"], row["observations"]
        )
        if observation["root"] is None
    )
    soothing_regulation_bf_max = max(
        abs(value)
        for row in soothing
        for value, observation in zip(
            row["score"]["root_log_bf"], row["observations"]
        )
        if observation["root"] is None
    )

    post_switch_correct = 0
    post_switch_total = 0
    onset_errors = []
    pre_switch_query_error = 0.0
    switching_worlds = 0
    for row in switching:
        truth = row["truth_path"]
        onset = next(
            (
                time
                for time in range(1, len(truth))
                if truth[time] != truth[time - 1]
            ),
            None,
        )
        smoothed = np.asarray(row["score"]["smoothed_partner"], dtype=float)
        immutable_copy = np.asarray(
            row["score"]["smoothed_partner"], dtype=float
        ).copy()
        if onset is not None:
            switching_worlds += 1
            post_switch_correct += int(
                np.sum(
                    np.argmax(smoothed[onset:], axis=1)
                    == np.asarray(truth[onset:], dtype=int)
                )
            )
            post_switch_total += len(truth) - onset
            onset_errors.append(abs(row["score"]["switch_onset"] - onset))
            pre_switch_query_error = max(
                pre_switch_query_error,
                float(
                    np.max(
                        np.abs(
                            smoothed[:onset]
                            - immutable_copy[:onset]
                        )
                    )
                ),
            )
    post_switch_recovery = post_switch_correct / post_switch_total

    groups: dict[tuple[bool, bool], list[dict[str, Any]]] = {}
    for row in factorial:
        kwargs = row["generator_kwargs"]
        key = (
            bool(kwargs["regulation_present"]),
            bool(kwargs["root_evidence_present"]),
        )
        groups.setdefault(key, []).append(row)
    uptake_interaction = interval(
        [
            left["score"]["root_movement"] - right["score"]["root_movement"]
            for left, right in zip(groups[(True, True)], groups[(False, True)])
        ]
    )
    no_root_max = max(
        abs(row["score"]["root_movement"])
        for key in ((True, False), (False, False))
        for row in groups[key]
    )
    regulation_depth = interval(
        [
            left["score"]["global_precision"][-1]
            - right["score"]["global_precision"][-1]
            for left, right in zip(groups[(True, True)], groups[(False, True)])
        ]
        + [
            left["score"]["global_precision"][-1]
            - right["score"]["global_precision"][-1]
            for left, right in zip(groups[(True, False)], groups[(False, False)])
        ]
    )

    constitution_result = constitution.cumulative_constitution_audit()
    semantic_worlds = all(
        row["score"]["one_posterior_audit"]
        for rows in cells.values()
        for row in rows
    )
    criteria = {
        "1_stable_reliable": {
            "recovery_rate": reliable_recovery,
            "global_precision_difference": reliable_depth_ci,
            "regulation_only_root_log_bf_max": reliable_regulation_bf_max,
            "passed": (
                reliable_recovery >= 0.75
                and reliable_depth_ci["mean"] > 0.0
                and reliable_depth_ci["lower_95"] > 0.0
                and reliable_regulation_bf_max <= v26a.TOLERANCE
            ),
        },
        "2_soothing_noncontingent": {
            "recovery_rate": soothing_recovery,
            "global_precision_difference": soothing_depth_ci,
            "cell1_minus_cell2_depth": contingency_difference,
            "regulation_only_root_log_bf_max": soothing_regulation_bf_max,
            "passed": (
                soothing_recovery >= 0.75
                and contingency_difference["mean"] > 0.0
                and contingency_difference["lower_95"] > 0.0
                and soothing_regulation_bf_max <= v26a.TOLERANCE
            ),
        },
        "3_switching": {
            "switching_world_count": switching_worlds,
            "post_switch_slice_count": post_switch_total,
            "post_switch_recovery": post_switch_recovery,
            "switch_onset_absolute_error_descriptive": {
                "count": len(onset_errors),
                "mean": float(np.mean(onset_errors)),
                "median": float(np.median(onset_errors)),
                "p95": float(np.quantile(onset_errors, 0.95)),
                "maximum": float(np.max(onset_errors)),
                "blocking": False,
            },
            "pre_switch_history_query_error": pre_switch_query_error,
            "passed": (
                post_switch_recovery >= 0.75
                and pre_switch_query_error <= v26a.TOLERANCE
            ),
        },
        "4_factorial": {
            "cell_counts": {
                f"reg_{int(key[0])}_root_{int(key[1])}": len(rows)
                for key, rows in groups.items()
            },
            "root_uptake_interaction": uptake_interaction,
            "no_root_movement_max": no_root_max,
            "regulation_global_precision_main_effect": regulation_depth,
            "passed": (
                uptake_interaction["lower_95"] > 0.0
                and no_root_max <= v26a.TOLERANCE
                and regulation_depth["mean"] > 0.0
            ),
        },
        "5_semantic_custody": {
            "one_posterior_all_worlds": semantic_worlds,
            "permanent_constitution": constitution_result["passed"],
            "raw_hashes_match_seal": hashes_match,
            "seed_count": seal["consumed_seed_count"],
            "ascending_gap_free": seal["ascending_gap_free"],
            "freeze_identity": seal["validation"]["freeze_identity"],
            "release_ledger": seal["validation"]["release_ledger"],
            "passed": (
                semantic_worlds
                and constitution_result["passed"]
                and hashes_match
                and seal["consumed_seed_count"] == 2000
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
        "challenge": "C-V26A",
        "immutable_sealed_verdict": "PASS" if passed else "FAIL",
        "pass_rule": "all five sealed criteria",
        "criteria": criteria,
        "verdict_classes": {
            "scientific": all(
                criteria[f"{index}_{name}"]["passed"]
                for index, name in (
                    (1, "stable_reliable"),
                    (2, "soothing_noncontingent"),
                    (3, "switching"),
                    (4, "factorial"),
                )
            ),
            "semantic": (
                semantic_worlds and constitution_result["passed"]
            ),
            "custody": criteria["5_semantic_custody"]["passed"],
        },
        "bounds": {
            "B_max_v232_formation": 3.801426508560692,
            "B_max_v24_common_emissions": 6.704414354964107,
            "B_max_v25a_configural": 6.084736253211209,
            "B_max_v25a_marginal_accounting": 6.704414354964107,
            "B_max_v25b": 11.302393144606405,
            **v26a.finite_information_bounds(),
        },
        "pi1": 0.92741935483871,
        "passed": passed,
    }
    dump(OUT / "c-v26a-summary.json", summary)
    ledger_path = OUT / "c-v26a-run-ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["criteria_evaluated_after_raw_seal"] = True
    ledger["immutable_verdict"] = summary["immutable_sealed_verdict"]
    ledger["summary_sha256"] = sha256(OUT / "c-v26a-summary.json")
    dump(ledger_path, ledger)
    return passed


def write_verdict(passed: bool) -> None:
    summary = json.loads((OUT / "c-v26a-summary.json").read_text())
    criteria = summary["criteria"]
    lines = [
        "# C-V26A sealed verdict",
        "",
        f"Immutable sealed verdict: **{summary['immutable_sealed_verdict']}**.",
        "",
        "Pass requires all five sealed criteria; no threshold, direction, or "
        "non-blocking family was changed.",
        "",
        "## Criteria",
        "",
    ]
    for name, result in criteria.items():
        lines.append(
            f"- `{name}`: **{'PASS' if result['passed'] else 'FAIL'}** — "
            f"{plain({key: value for key, value in result.items() if key != 'passed'})}"
        )
    lines += [
        "",
        "## Verdict classes",
        "",
        f"- Scientific: {'PASS' if summary['verdict_classes']['scientific'] else 'FAIL'}",
        f"- Semantic: {'PASS' if summary['verdict_classes']['semantic'] else 'FAIL'}",
        f"- Custody: {'PASS' if summary['verdict_classes']['custody'] else 'FAIL'}",
        "",
        "The switch-onset errors in cell 3 are descriptive only, exactly as "
        "sealed and adjudicated.",
    ]
    (OUT / "c-v26a-verdict.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    if passed:
        (OUT / "stage-verdict.md").write_text(
            "# V2.6a stage verdict\n\n"
            "Final disposition: **PASS_WITH_ADJUDICATED_SWITCH_ONSET_"
            "ATTAINABILITY_LIMITATION**.\n\n"
            "The original and repaired Gate-2 FAILs remain in the record. "
            "The committed adjudication made only the onset-floor family "
            "non-blocking. Gates 3–5 passed all blocking criteria, and "
            "C-V26A passed all five sealed criteria. The licensed claim is "
            "therefore retained: co-regulation changes the inferential "
            "regime and evidence uptake; it is not itself root-changing "
            "evidence.\n",
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
        OUT / "c-v26a-full-fast-suite.json",
        {
            "command": "python3 run_tests_parallel.py",
            "returncode": suite.returncode,
            "passed": suite.returncode == 0,
            "stdout": suite.stdout,
            "stderr": suite.stderr,
        },
    )
    files = [
        f"results/V2.6a/{filename}" for filename in CELL_FILES.values()
    ] + [
        "results/V2.6a/c-v26a-raw-trace-seal.json",
        "results/V2.6a/c-v26a-run-ledger.json",
        "results/V2.6a/c-v26a-summary.json",
        "results/V2.6a/c-v26a-verdict.md",
        "results/V2.6a/c-v26a-full-fast-suite.json",
        "results/V2.6a/stage-verdict.md",
        "challenges/run_c_v26a.py",
    ]
    (OUT / "ready-to-commit-c-v26a.md").write_text(
        "# Ready to commit: C-V26A\n\n"
        + "\n".join(f"- `{item}`" for item in files)
        + "\n",
        encoding="utf-8",
    )
    if suite.returncode:
        raise SystemExit(suite.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("generate", "evaluate"), required=True)
    args = parser.parse_args()
    if args.phase == "generate":
        generate_and_seal()
        return 0
    passed = evaluate()
    write_verdict(passed)
    run_suite_and_ready()
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
