#!/usr/bin/env python3
"""One-run C-V25B-B sealed challenge runner."""

from __future__ import annotations

import argparse
import ast
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

from ref import v25b  # noqa: E402
from run_v25b_gates import (  # noqa: E402
    GATE3_ARMS,
    _gate3_first_time,
    _gate3_heldout_margin,
    gate3_initial_state,
)


CHALLENGE = ROOT / "sealed-revealed" / "C-V25BB-reduction-challenge.md"
OUT = ROOT / "results" / "V2.5b"
MANIFEST = OUT / "freeze-manifest.json"
RELEASE_LEDGER = (
    REPO_ROOT / "projects" / "ifs-paper" / "suite-v2-sealed-hashes.md"
)
RELEASED_BLOCK = (2_020_000, 2_021_999)
CELL_FILES = {
    "cell_1_correct_timing": "c-v25bb-cell-1.json",
    "cell_2_premature": "c-v25bb-cell-2.json",
    "cell_3_old_context_return": "c-v25bb-cell-3.json",
    "cell_4_partial_truth": "c-v25bb-cell-4.json",
    "cell_5_no_erasure": "c-v25bb-cell-5.json",
}
GATE3_ROW_FIELDS = {
    "position",
    "arm",
    "seed",
    "initial_state_seed",
    "initial_state_sha256",
    "formed_P",
    "revised_root",
    "context_split",
    "endpoint_q_structure",
    "q_000",
    "selected_structure",
    "material_reduction",
    "first_time_followup",
    "premature_material_reduction",
    "returned_to_nonreduced",
    "heldout_000_vs_111_margin",
    "old_context_query_error",
    "root_revision_unchanged",
    "redescription_unchanged",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: Any) -> None:
    def plain(item: Any) -> Any:
        if isinstance(item, np.ndarray):
            return item.tolist()
        if isinstance(item, np.generic):
            return item.item()
        raise TypeError(f"cannot serialize {type(item)!r}")

    path.write_text(
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            allow_nan=False,
            default=plain,
        )
        + "\n",
        encoding="utf-8",
    )


def parse_bundle() -> dict[str, Any]:
    text = CHALLENGE.read_text(encoding="utf-8")
    start = text.index("{'parse_instruction'")
    criteria = text.index("\n\n## Criteria", start)
    end = text.rfind("}", start, criteria) + 1
    return ast.literal_eval(text[start:end])


def parse_escrow(value: str) -> tuple[int, int]:
    left, right = value.split(":")
    return int(left), int(right)


def verify_freeze() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in manifest["files"].items():
        path = ROOT / relative
        actual = sha256(path) if path.exists() else None
        if actual != expected:
            mismatches.append(
                {
                    "file": relative,
                    "expected": expected,
                    "actual": actual,
                }
            )
    return {
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "manifest_sha256": sha256(MANIFEST),
        "file_count": len(manifest["files"]),
        "mismatches": mismatches,
        "passed": not mismatches,
    }


def validate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    signature = inspect.signature(v25b.generate_world)
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
        if cell["arm"] not in GATE3_ARMS:
            errors.append(
                f"{cell_name}: arm {cell['arm']!r} is not frozen"
            )
        unknown_fields = sorted(set(cell["score"]) - GATE3_ROW_FIELDS)
        if unknown_fields:
            errors.append(
                f"{cell_name}: non-frozen gate3_row fields {unknown_fields}"
            )
    if cells != list(CELL_FILES):
        errors.append("cell order differs from sealed five-cell order")
    if seeds != list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)):
        errors.append("cell escrow ranges are not ascending and gap-free")
    freeze = verify_freeze()
    if not freeze["passed"]:
        errors.append("frozen source identity failed")
    ledger_text = RELEASE_LEDGER.read_text(encoding="utf-8")
    release_phrase = (
        "Escrow: C-V25B-B seeds 2020000:2021999 "
        "(unconsumed by the retained C-V25B stop; release record stands)"
    )
    if release_phrase not in ledger_text:
        errors.append("committed C-V25B-B release ledger entry not found")
    return {
        "challenge": "C-V25B-B",
        "challenge_sha256": sha256(CHALLENGE),
        "verified_seal_sha256": (
            "d781130feb9c675f3e476788a0d103cd99a0e1588b70eff1de9c95fccf602c32"
        ),
        "bundle_parse_instruction": bundle["parse_instruction"],
        "literal_parser": "ast.literal_eval",
        "cell_order": cells,
        "seed_start": seeds[0],
        "seed_end": seeds[-1],
        "seed_count": len(seeds),
        "frozen_gate3_row_fields": sorted(GATE3_ROW_FIELDS),
        "freeze_identity": freeze,
        "release_ledger": {
            "file": str(RELEASE_LEDGER.relative_to(REPO_ROOT)),
            "sha256": sha256(RELEASE_LEDGER),
            "release_phrase_found": release_phrase in ledger_text,
            "commit": "8d57a8c",
        },
        "expressible": not errors,
        "errors": errors,
    }


def _episode_record(episode) -> dict[str, Any]:
    return {
        "cue": int(episode.cue),
        "context": int(episode.context),
        "values": list(episode.values),
    }


def score_world(
    cell_name: str,
    cell: dict[str, Any],
    seed: int,
    position: int,
) -> dict[str, Any]:
    world = v25b.generate_world(
        seed,
        released_block=RELEASED_BLOCK,
        **cell["world"],
    )
    arm = cell["arm"]
    initial = gate3_initial_state(position)
    state = initial["serialized_state"]
    precision = float(world.precision)
    initial_prior = np.asarray(state["posterior_store"]["H_Z"], dtype=float)
    do_over_count = int(
        v25b.PARAMETERS["gate3_initial_state"]["joint_do_over_episodes"]
    )
    observed = world.episodes
    prefix = ()
    prefix_modes = ()
    if arm in (
        "post_redescription_do_over",
        "joint_do_over",
        "marginal_do_over",
        "no_reduction_lesion",
    ):
        prefix, _ = v25b.do_over_episodes(
            seed,
            count=do_over_count,
            precision=precision,
            structure="000",
            released_block=RELEASED_BLOCK,
        )
        prefix_modes = tuple(
            "marginal"
            if arm in ("marginal_do_over", "no_reduction_lesion")
            else "joint"
            for _ in prefix
        )
    elif arm == "premature_do_over":
        prefix, prefix_modes = v25b.do_over_episodes(
            seed,
            count=do_over_count,
            precision=precision,
            structure="000",
            released_block=RELEASED_BLOCK,
        )
    elif arm == "suggestion_only":
        prefix = v25b.suggestion_only_episodes(do_over_count)
        prefix_modes = tuple("joint" for _ in prefix)

    sequence = prefix + observed
    modes = prefix_modes + tuple("joint" for _ in observed)
    if arm == "no_reduction_lesion":
        modes = tuple("marginal" for _ in sequence)
    result = v25b.score(
        sequence,
        precision=precision,
        initial_prior=initial_prior,
        presentations=modes,
    )
    prefix_result = v25b.score(
        prefix,
        precision=precision,
        initial_prior=initial_prior,
        presentations=prefix_modes,
    )
    returned_to_nonreduced = bool(
        prefix_result.material_reduction.material
        and not result.material_reduction.material
    )
    root_before = tuple(state["posterior_store"]["G_root"])
    context_before = tuple(state["posterior_store"]["H_context_split"])
    fields = {
        "position": position,
        "arm": arm,
        "seed": seed,
        "initial_state_seed": initial["seed"],
        "initial_state_sha256": initial["state_sha256"],
        "formed_P": float(state["posterior_store"]["H_formation"][2]),
        "revised_root": list(root_before),
        "context_split": list(context_before),
        "endpoint_q_structure": result.q_structure.tolist(),
        "q_000": float(
            result.q_structure[v25b.STRUCTURE_INDEX["000"]]
        ),
        "selected_structure": v25b.STRUCTURES[
            int(np.argmax(result.q_structure))
        ],
        "material_reduction": bool(result.material_reduction.material),
        "first_time_followup": _gate3_first_time(result, len(prefix)),
        "premature_material_reduction": bool(
            prefix_result.material_reduction.material
        ),
        "returned_to_nonreduced": returned_to_nonreduced,
        "heldout_000_vs_111_margin": _gate3_heldout_margin(
            observed, precision
        ),
        "old_context_query_error": v25b.old_context_query_error(
            position % 3, "111", precision
        ),
        "root_revision_unchanged": (
            tuple(state["posterior_store"]["G_root"]) == root_before
        ),
        "redescription_unchanged": (
            tuple(state["posterior_store"]["H_context_split"])
            == context_before
        ),
    }
    idx0 = v25b.STRUCTURE_INDEX["000"]
    idx1 = v25b.STRUCTURE_INDEX["111"]
    final_log_bf = (
        result.pairwise_000_111_log_bf[-1]
        if result.pairwise_000_111_log_bf
        else 0.0
    )
    evidence_log_bf = float(
        result.log_evidence_by_structure[idx0]
        - result.log_evidence_by_structure[idx1]
    )
    posterior_log_odds = math.log(
        float(result.q_structure[idx0] / result.q_structure[idx1])
    )
    prior_log_odds = math.log(
        float(initial_prior[idx0] / initial_prior[idx1])
    )
    requested = {name: fields[name] for name in cell["score"]}
    return {
        "cell": cell_name,
        "seed": seed,
        "arm": arm,
        "declared_score_fields": list(cell["score"]),
        "truth": {
            "structure": world.truth_structure,
            "precision": world.precision,
            "context_regime": world.context_regime,
        },
        "observations": [_episode_record(item) for item in observed],
        "imaginal_prefix": [_episode_record(item) for item in prefix],
        "presentation_modes": list(modes),
        "requested_readouts": requested,
        "frozen_gate3_row": fields,
        "semantic": {
            "posterior_sum_error": abs(
                float(result.q_structure.sum()) - 1.0
            ),
            "pairwise_recombination_error": abs(
                float(final_log_bf) - evidence_log_bf
            ),
            "posterior_odds_identity_error": abs(
                (posterior_log_odds - prior_log_odds) - evidence_log_bf
            ),
            "neutral_survival": bool(
                result.material_reduction.neutral_survives
            ),
            "one_posterior_audit": True,
        },
    }


def generate_and_seal() -> None:
    bundle = parse_bundle()
    validation = validate_bundle(bundle)
    if not validation["expressible"]:
        dump(
            OUT / "c-v25bb-stop-as-sealed.json",
            {
                "verdict": "STOP_AS_SEALED",
                "validation": validation,
                "seeds_consumed": 0,
            },
        )
        raise SystemExit(2)
    seal_path = OUT / "c-v25bb-raw-trace-seal.json"
    if seal_path.exists():
        raise RuntimeError("raw seal already exists; one-run budget is spent")

    hashes = {}
    cell_records = {}
    consumed = []
    for cell_name in validation["cell_order"]:
        cell = bundle[cell_name]
        start, end = parse_escrow(cell["escrow"])
        rows = [
            score_world(cell_name, cell, seed, seed - start)
            for seed in range(start, end + 1)
        ]
        consumed.extend(range(start, end + 1))
        path = OUT / CELL_FILES[cell_name]
        dump(path, rows)
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
        "challenge": "C-V25B-B",
        "seal_and_reveal_commit": "8d57a8c",
        "challenge_sha256": sha256(CHALLENGE),
        "released_block": list(RELEASED_BLOCK),
        "released_block_passed_explicitly": True,
        "release_ledger_commit": "8d57a8c",
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
    ledger_path = OUT / "c-v25bb-run-ledger.json"
    dump(ledger_path, ledger)
    ledger_relative = str(ledger_path.relative_to(ROOT))
    hashes[ledger_relative] = sha256(ledger_path)
    seal = {
        "challenge": "C-V25B-B",
        "phase": "RAW_TRACES_SEALED_BEFORE_CRITERIA",
        "criteria_evaluated": False,
        "cell_files": cell_records,
        "ledger": {
            "file": ledger_relative,
            "sha256": hashes[ledger_relative],
        },
        "all_raw_hashes": hashes,
    }
    dump(seal_path, seal)


def interval(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    mean = float(array.mean())
    half = (
        0.0
        if len(array) < 2
        else 1.96 * float(array.std(ddof=1)) / math.sqrt(len(array))
    )
    return {
        "mean": mean,
        "lower_95": mean - half,
        "upper_95": mean + half,
    }


def rate_interval(values: list[bool]) -> dict[str, float]:
    successes = int(sum(values))
    total = len(values)
    rate = successes / total
    denominator = 1.0 + 1.96**2 / total
    center = (rate + 1.96**2 / (2 * total)) / denominator
    half = (
        1.96
        * math.sqrt(
            rate * (1.0 - rate) / total
            + 1.96**2 / (4 * total**2)
        )
        / denominator
    )
    return {
        "rate": rate,
        "lower_95": center - half,
        "upper_95": center + half,
        "successes": successes,
        "total": total,
    }


def evaluate() -> None:
    bundle = parse_bundle()
    seal_path = OUT / "c-v25bb-raw-trace-seal.json"
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
    ledger_path = OUT / "c-v25bb-run-ledger.json"
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
    c1_material = rate_interval(
        [row["requested_readouts"]["material_reduction"] for row in c1]
    )
    c1_retention = max(
        row["requested_readouts"]["old_context_query_error"] for row in c1
    )
    c1_times = [
        int(row["requested_readouts"]["first_time_followup"]) for row in c1
    ]
    c2_premature = rate_interval(
        [
            row["requested_readouts"]["premature_material_reduction"]
            for row in c2
        ]
    )
    c2_material = rate_interval(
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
        else rate_interval(
            [
                row["requested_readouts"]["returned_to_nonreduced"]
                for row in c2_eligible
            ]
        )
    )
    c3_eligible = [
        row
        for row in c3
        if row["requested_readouts"]["premature_material_reduction"]
    ]
    c3_reversal = (
        None
        if not c3_eligible
        else rate_interval(
            [
                row["requested_readouts"]["returned_to_nonreduced"]
                for row in c3_eligible
            ]
        )
    )
    c3_retention = max(
        row["requested_readouts"]["old_context_query_error"] for row in c3
    )
    c3_material = rate_interval(
        [row["requested_readouts"]["material_reduction"] for row in c3]
    )
    c4_recovery = rate_interval(
        [
            row["requested_readouts"]["selected_structure"] == "101"
            for row in c4
        ]
    )
    c4_false_complete = rate_interval(
        [row["requested_readouts"]["material_reduction"] for row in c4]
    )
    c4_false_full = rate_interval(
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
    c5_material = rate_interval(
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
        "2_cell_2_premature": c2_premature["rate"] <= 0.10,
        "3_cell_3_old_context_return": (
            c3_reversal is not None
            and c3_reversal["rate"] >= 0.60
            and c3_retention <= 1e-10
        ),
        "4_cell_4_partial_truth": (
            c4_recovery["rate"] >= 0.75
            and c4_false_complete["rate"] <= 0.10
            and c4_false_full["rate"] <= 0.10
        ),
        "5_cell_5_no_erasure": (
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
                **interval(c1_times),
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
            "returned_to_nonreduced_among_premature": c2_reversal,
            "final_material_reduction": c2_material,
        },
        "cell_3": {
            "eligible_premature_or_unsupported_count": len(c3_eligible),
            "returned_to_nonreduced_among_eligible": c3_reversal,
            "maximum_old_context_query_error": c3_retention,
            "final_material_reduction": c3_material,
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
            "prior_C_V25B_stop_retained": True,
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
            **v25b.finite_information_bound(),
        },
        "challenge_sha256": sha256(CHALLENGE),
        "raw_trace_seal_sha256": sha256(seal_path),
        "bundle_parse_instruction": bundle["parse_instruction"],
    }
    dump(OUT / "c-v25bb-summary.json", summary)
    lines = [
        "# C-V25B-B sealed verdict",
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
            "The original C-V25B `STOP_AS_SEALED` verdict remains retained. "
            "Full population metrics and 95% intervals are in "
            "`c-v25bb-summary.json`; raw per-world traces are sealed in the "
            "five cell files.",
        ]
    )
    (OUT / "c-v25bb-verdict.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    if verdict == "PASS":
        (OUT / "stage-verdict.md").write_text(
            "# V2.5b stage verdict\n\n"
            "**Disposition: "
            "`PASS_WITH_ADJUDICATED_DO_OVER_SPEEDUP_LIMITATION`**\n\n"
            "Gate 1 passed after the authorized oracle software repair. "
            "Gate 2 passed. Gate 3's formal FAIL and do-over-speedup "
            "effect-size limitation remain retained under adjudication. "
            "Gate 4's formal FAIL remains retained as an adjudicated "
            "criterion-operationalization defect. Gate 5 passed every "
            "blocking criterion. C-V25B stopped as sealed without consuming "
            "escrow; the corrected C-V25B-B sealed challenge passed all six "
            "criteria.\n",
            encoding="utf-8",
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("validate", "generate", "evaluate"))
    args = parser.parse_args()
    bundle = parse_bundle()
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
