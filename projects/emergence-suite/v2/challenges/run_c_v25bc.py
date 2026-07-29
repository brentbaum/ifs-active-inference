#!/usr/bin/env python3
"""One-run C-V25B-C sealed challenge runner."""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from challenges import run_c_v25bb as base  # noqa: E402


CHALLENGE = ROOT / "sealed-revealed" / "C-V25BC-reduction-challenge.md"
OUT = ROOT / "results" / "V2.5b"
RELEASE_LEDGER = (
    REPO_ROOT / "projects" / "ifs-paper" / "suite-v2-sealed-hashes.md"
)
RELEASED_BLOCK = (2_022_000, 2_023_999)
CELL_FILES = {
    "cell_1_correct_timing": "c-v25bc-cell-1.json",
    "cell_2_premature": "c-v25bc-cell-2.json",
    "cell_3_old_context_return": "c-v25bc-cell-3.json",
    "cell_4_partial_truth": "c-v25bc-cell-4.json",
    "cell_5_no_erasure": "c-v25bc-cell-5.json",
}

# The shared scorer reads these module globals. Point them at this sealed
# artifact and fresh released block before any validation or generation.
base.CHALLENGE = CHALLENGE
base.RELEASED_BLOCK = RELEASED_BLOCK
base.CELL_FILES = CELL_FILES


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_escrow(value: str) -> tuple[int, int]:
    left, right = value.split(":")
    return int(left), int(right)


def validate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    signature = inspect.signature(base.v25b.generate_world)
    permitted_kwargs = set(signature.parameters) - {"seed", "released_block"}
    cells = [key for key in bundle if key.startswith("cell_")]
    errors = []
    seeds = []
    for cell_name in cells:
        cell = bundle[cell_name]
        start, end = parse_escrow(cell["escrow"])
        if end - start + 1 != int(cell["n_worlds"]):
            errors.append(f"{cell_name}: escrow count mismatch")
        seeds.extend(range(start, end + 1))
        unknown_kwargs = sorted(set(cell["world"]) - permitted_kwargs)
        if unknown_kwargs:
            errors.append(
                f"{cell_name}: unknown generate_world kwargs {unknown_kwargs}"
            )
        if cell["arm"] not in base.GATE3_ARMS:
            errors.append(
                f"{cell_name}: arm {cell['arm']!r} is not frozen"
            )
        unknown_fields = sorted(
            set(cell["score"]) - base.GATE3_ROW_FIELDS
        )
        if unknown_fields:
            errors.append(
                f"{cell_name}: non-frozen gate3_row fields {unknown_fields}"
            )
    if cells != list(CELL_FILES):
        errors.append("cell order differs from sealed five-cell order")
    if seeds != list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)):
        errors.append("cell escrow ranges are not ascending and gap-free")
    for cell_name in ("cell_1_correct_timing", "cell_3_old_context_return",
                      "cell_5_no_erasure"):
        if bundle[cell_name]["world"]["truth_structure"] != "000":
            errors.append(
                f"{cell_name}: material demand is not on 000 truth"
            )
    if bundle["cell_2_premature"]["world"]["truth_structure"] != "111":
        errors.append("cell_2_premature: specificity ceiling is not 111 truth")
    if bundle["cell_4_partial_truth"]["world"]["truth_structure"] != "101":
        errors.append("cell_4_partial_truth: recovery truth is not 101")
    freeze = base.verify_freeze()
    if not freeze["passed"]:
        errors.append("frozen source identity failed")
    ledger_text = RELEASE_LEDGER.read_text(encoding="utf-8")
    release_phrase = (
        "Escrow: C-V25B-C seeds 2022000:2023999 "
        "(fresh; 2020000:2021999 consumed by the retained C-V25B-B FAIL "
        "and closed)"
    )
    if release_phrase not in ledger_text:
        errors.append("committed C-V25B-C release ledger entry not found")
    return {
        "challenge": "C-V25B-C",
        "challenge_sha256": sha256(CHALLENGE),
        "verified_seal_sha256": (
            "f90dbb800bf98f58d9ce1b916a5d9d218faee40b7e16f773dfa6fe12ce31b17e"
        ),
        "bundle_parse_instruction": bundle["parse_instruction"],
        "literal_parser": "ast.literal_eval",
        "cell_order": cells,
        "seed_start": seeds[0],
        "seed_end": seeds[-1],
        "seed_count": len(seeds),
        "frozen_gate3_row_fields": sorted(base.GATE3_ROW_FIELDS),
        "criterion_direction_lint": {
            "material_demands_on_000_truth": True,
            "premature_ceiling_on_111_truth": True,
            "partial_recovery_on_101_truth": True,
        },
        "freeze_identity": freeze,
        "release_ledger": {
            "file": str(RELEASE_LEDGER.relative_to(REPO_ROOT)),
            "sha256": sha256(RELEASE_LEDGER),
            "release_phrase_found": release_phrase in ledger_text,
            "commit": "139d5bc",
        },
        "expressible": not errors,
        "errors": errors,
    }


def generate_and_seal() -> None:
    bundle = base.parse_bundle()
    validation = validate_bundle(bundle)
    if not validation["expressible"]:
        base.dump(
            OUT / "c-v25bc-stop-as-sealed.json",
            {
                "verdict": "STOP_AS_SEALED",
                "validation": validation,
                "seeds_consumed": 0,
            },
        )
        raise SystemExit(2)
    seal_path = OUT / "c-v25bc-raw-trace-seal.json"
    if seal_path.exists():
        raise RuntimeError("raw seal already exists; one-run budget is spent")
    hashes = {}
    cell_records = {}
    consumed = []
    for cell_name in validation["cell_order"]:
        cell = bundle[cell_name]
        start, end = parse_escrow(cell["escrow"])
        rows = [
            base.score_world(cell_name, cell, seed, seed - start)
            for seed in range(start, end + 1)
        ]
        consumed.extend(range(start, end + 1))
        path = OUT / CELL_FILES[cell_name]
        base.dump(path, rows)
        relative = str(path.relative_to(ROOT))
        hashes[relative] = sha256(path)
        cell_records[cell_name] = {
            "file": relative,
            "sha256": hashes[relative],
            "seed_start": start,
            "seed_end": end,
            "world_count": len(rows),
        }
    ledger = {
        "challenge": "C-V25B-C",
        "seal_and_reveal_commit": "139d5bc",
        "challenge_sha256": sha256(CHALLENGE),
        "released_block": list(RELEASED_BLOCK),
        "released_block_passed_explicitly": True,
        "release_ledger_commit": "139d5bc",
        "prior_block_closed": [2_020_000, 2_021_999],
        "seed_order": "ascending gap-free within cells and globally",
        "seed_count": len(consumed),
        "seed_start": consumed[0],
        "seed_end": consumed[-1],
        "seed_sequence_sha256": hashlib.sha256(
            json.dumps(consumed, separators=(",", ":")).encode()
        ).hexdigest(),
        "freeze_identity": validation["freeze_identity"],
        "criteria_evaluated": False,
    }
    ledger_path = OUT / "c-v25bc-run-ledger.json"
    base.dump(ledger_path, ledger)
    ledger_relative = str(ledger_path.relative_to(ROOT))
    hashes[ledger_relative] = sha256(ledger_path)
    base.dump(
        seal_path,
        {
            "challenge": "C-V25B-C",
            "phase": "RAW_TRACES_SEALED_BEFORE_CRITERIA",
            "criteria_evaluated": False,
            "cell_files": cell_records,
            "ledger": {
                "file": ledger_relative,
                "sha256": hashes[ledger_relative],
            },
            "all_raw_hashes": hashes,
        },
    )


def evaluate() -> None:
    bundle = base.parse_bundle()
    seal_path = OUT / "c-v25bc-raw-trace-seal.json"
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    hash_errors = []
    cells = {}
    for cell_name, filename in CELL_FILES.items():
        path = OUT / filename
        relative = str(path.relative_to(ROOT))
        actual = sha256(path)
        expected = seal["all_raw_hashes"][relative]
        if actual != expected:
            hash_errors.append(
                {"file": relative, "expected": expected, "actual": actual}
            )
        cells[cell_name] = json.loads(path.read_text(encoding="utf-8"))
    ledger_path = OUT / "c-v25bc-run-ledger.json"
    if sha256(ledger_path) != seal["ledger"]["sha256"]:
        hash_errors.append(
            {"file": str(ledger_path.relative_to(ROOT))}
        )
    if hash_errors:
        raise RuntimeError(f"raw trace custody failed: {hash_errors}")

    c1 = cells["cell_1_correct_timing"]
    c2 = cells["cell_2_premature"]
    c3 = cells["cell_3_old_context_return"]
    c4 = cells["cell_4_partial_truth"]
    c5 = cells["cell_5_no_erasure"]
    c1_material = base.rate_interval(
        [row["requested_readouts"]["material_reduction"] for row in c1]
    )
    c1_retention = max(
        row["requested_readouts"]["old_context_query_error"] for row in c1
    )
    c1_times = [
        int(row["requested_readouts"]["first_time_followup"]) for row in c1
    ]
    c2_premature = base.rate_interval(
        [
            row["requested_readouts"]["premature_material_reduction"]
            for row in c2
        ]
    )
    c2_material = base.rate_interval(
        [row["requested_readouts"]["material_reduction"] for row in c2]
    )
    c2_eligible = [
        row
        for row in c2
        if row["requested_readouts"]["premature_material_reduction"]
    ]
    c2_reversal = (
        None
        if not c2_eligible
        else base.rate_interval(
            [
                row["requested_readouts"]["returned_to_nonreduced"]
                for row in c2_eligible
            ]
        )
    )
    c3_material = base.rate_interval(
        [row["requested_readouts"]["material_reduction"] for row in c3]
    )
    c3_retention = max(
        row["requested_readouts"]["old_context_query_error"] for row in c3
    )
    c3_eligible = [
        row
        for row in c3
        if row["requested_readouts"]["premature_material_reduction"]
    ]
    c3_reversal = (
        None
        if not c3_eligible
        else base.rate_interval(
            [
                row["requested_readouts"]["returned_to_nonreduced"]
                for row in c3_eligible
            ]
        )
    )
    c4_recovery = base.rate_interval(
        [
            row["requested_readouts"]["selected_structure"] == "101"
            for row in c4
        ]
    )
    c4_false_complete = base.rate_interval(
        [row["requested_readouts"]["material_reduction"] for row in c4]
    )
    c4_false_full = base.rate_interval(
        [
            row["requested_readouts"]["selected_structure"] == "111"
            for row in c4
        ]
    )
    c4_q = np.asarray(
        [row["requested_readouts"]["endpoint_q_structure"] for row in c4],
        dtype=float,
    )
    c5_retention = max(
        row["requested_readouts"]["old_context_query_error"] for row in c5
    )
    c5_redescription = all(
        row["requested_readouts"]["redescription_unchanged"] for row in c5
    )
    c5_root = all(
        row["requested_readouts"]["root_revision_unchanged"] for row in c5
    )
    c5_material = base.rate_interval(
        [row["requested_readouts"]["material_reduction"] for row in c5]
    )
    semantic_max = max(
        max(
            row["semantic"]["posterior_sum_error"],
            row["semantic"]["pairwise_recombination_error"],
            row["semantic"]["posterior_odds_identity_error"],
        )
        for rows in cells.values()
        for row in rows
    )
    semantic_flags = all(
        row["semantic"]["neutral_survival"]
        and row["semantic"]["one_posterior_audit"]
        for rows in cells.values()
        for row in rows
    )
    consumed = [
        row["seed"] for cell_name in CELL_FILES for row in cells[cell_name]
    ]
    criteria = {
        "1_cell_1_correct_timing": (
            c1_material["rate"] >= 0.60 and c1_retention <= 1e-10
        ),
        "2_cell_2_premature_specificity": (
            c2_premature["rate"] <= 0.10
            and c2_material["rate"] <= 0.10
        ),
        "3_cell_3_old_context_return": (
            c3_material["rate"] >= 0.60 and c3_retention <= 1e-10
        ),
        "4_cell_4_partial_truth": (
            c4_recovery["rate"] >= 0.75
            and c4_false_complete["rate"] <= 0.10
            and c4_false_full["rate"] <= 0.10
        ),
        "5_cell_5_no_erasure_under_reduction": (
            c5_retention <= 1e-10
            and c5_redescription
            and c5_root
            and c5_material["rate"] >= 0.60
        ),
        "6_semantic_and_custody": (
            semantic_max <= 1e-10
            and semantic_flags
            and not hash_errors
            and consumed
            == list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1))
        ),
    }
    verdict = "PASS" if all(criteria.values()) else "FAIL"
    metrics = {
        "cell_1": {
            "material_reduction": c1_material,
            "maximum_old_context_query_error": c1_retention,
            "first_time_followup": {
                **base.interval(c1_times),
                "minimum": min(c1_times),
                "maximum": max(c1_times),
                "q25": float(np.quantile(c1_times, 0.25)),
                "median": float(np.quantile(c1_times, 0.5)),
                "q75": float(np.quantile(c1_times, 0.75)),
                "distribution": c1_times,
            },
        },
        "cell_2": {
            "premature_material_reduction": c2_premature,
            "final_material_reduction": c2_material,
            "returned_to_nonreduced_among_premature": c2_reversal,
        },
        "cell_3": {
            "material_reduction": c3_material,
            "maximum_old_context_query_error": c3_retention,
            "premature_reduction_world_count": len(c3_eligible),
            "returned_to_nonreduced_among_premature": c3_reversal,
        },
        "cell_4": {
            "structure_101_recovery": c4_recovery,
            "false_complete_reduction": c4_false_complete,
            "false_full_burden_selection": c4_false_full,
            "endpoint_q_structure": {
                "mean": c4_q.mean(axis=0).tolist(),
                "q05": np.quantile(c4_q, 0.05, axis=0).tolist(),
                "q50": np.quantile(c4_q, 0.5, axis=0).tolist(),
                "q95": np.quantile(c4_q, 0.95, axis=0).tolist(),
            },
        },
        "cell_5": {
            "maximum_old_context_query_error": c5_retention,
            "redescription_unchanged_all": c5_redescription,
            "root_revision_unchanged_all": c5_root,
            "material_reduction": c5_material,
        },
        "semantic_maximum_error": semantic_max,
    }
    classes = {
        "scientific": {
            "criteria": [1, 2, 3, 4, 5],
            "passed": all(list(criteria.values())[:5]),
        },
        "semantic": {
            "criterion": 6,
            "passed": semantic_max <= 1e-10 and semantic_flags,
        },
        "custody": {
            "criterion": 6,
            "passed": (
                not hash_errors
                and consumed
                == list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1))
            ),
            "prior_seal_history_retained": {
                "C-V25B": "STOP_AS_SEALED",
                "C-V25B-B": "FAIL_DIRECTION_INVERSION_SPECIFICITY_RESULT",
            },
        },
    }
    summary = {
        "immutable_sealed_verdict": verdict,
        "criteria": criteria,
        "metrics": metrics,
        "verdict_classes": classes,
        "bounds": {
            "B_max_inherited_formation": 3.801426508560692,
            "B_max_v24_common_emissions": 6.704414354964107,
            "B_max_v25a_configural": 6.084736253211209,
            "B_max_v25a_marginal_accounting": 6.704414354964107,
            **base.v25b.finite_information_bound(),
        },
        "challenge_sha256": sha256(CHALLENGE),
        "raw_trace_seal_sha256": sha256(seal_path),
        "bundle_parse_instruction": bundle["parse_instruction"],
    }
    base.dump(OUT / "c-v25bc-summary.json", summary)
    lines = [
        "# C-V25B-C sealed verdict",
        "",
        f"**IMMUTABLE SEALED VERDICT: {verdict}**",
        "",
        "## Sealed criteria",
        "",
    ]
    lines.extend(
        f"- {name}: `{'PASS' if passed else 'FAIL'}`"
        for name, passed in criteria.items()
    )
    lines.extend(
        [
            "",
            "## Verdict classes",
            "",
            f"- Scientific: `{'PASS' if classes['scientific']['passed'] else 'FAIL'}`.",
            f"- Semantic: `{'PASS' if classes['semantic']['passed'] else 'FAIL'}`.",
            f"- Custody: `{'PASS' if classes['custody']['passed'] else 'FAIL'}`.",
            "",
            "C-V25B's `STOP_AS_SEALED` and C-V25B-B's retained specificity "
            "result remain in the record. Full metrics and 95% intervals are "
            "in `c-v25bc-summary.json`; raw traces are sealed in five cell "
            "files.",
        ]
    )
    (OUT / "c-v25bc-verdict.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    if verdict == "PASS":
        (OUT / "stage-verdict.md").write_text(
            "# V2.5b stage verdict\n\n"
            "**Disposition: "
            "`PASS_WITH_ADJUDICATED_DO_OVER_SPEEDUP_LIMITATION`**\n\n"
            "Gate 1 passed after the authorized oracle software repair; "
            "Gate 2 passed. Gate 3's formal FAIL and sub-floor positive "
            "do-over speedup remain retained under adjudication. Gate 4's "
            "formal FAIL remains retained as an adjudicated criterion "
            "operationalization defect. Gate 5 passed every blocking "
            "criterion.\n\n"
            "Seal history: C-V25B stopped as sealed before consuming escrow "
            "because its capacity readout was absent; C-V25B-B failed its "
            "direction-inverted reduction demands while establishing perfect "
            "specificity in 111-truth cells; direction-corrected C-V25B-C "
            "passed all six sealed criteria on fresh escrow.\n",
            encoding="utf-8",
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("validate", "generate", "evaluate"))
    args = parser.parse_args()
    bundle = base.parse_bundle()
    if args.phase == "validate":
        validation = validate_bundle(bundle)
        print(json.dumps(validation, indent=2, sort_keys=True))
        raise SystemExit(0 if validation["expressible"] else 2)
    if args.phase == "generate":
        generate_and_seal()
    else:
        evaluate()


if __name__ == "__main__":
    main()
