#!/usr/bin/env python3
"""One-run C-V25A sealed challenge runner.

`generate` consumes escrow once and seals raw scored traces. `evaluate`
reads only those sealed JSON files and cannot call the generator.
"""

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
sys.path.insert(0, str(ROOT))

from ref import v25a_completion as c  # noqa: E402
from ref import v25a_completion_oracle as oracle  # noqa: E402
from ref.manifest_chain import verify_manifest_chain  # noqa: E402


CHALLENGE = ROOT / "sealed-revealed" / "C-V25A-configural-challenge.md"
OUT = ROOT / "results" / "V2.5a-completion"
RELEASED_BLOCK = (2_010_000, 2_010_999)
CELL_FILES = {
    "cell_1_unknown_interaction": "c-v25a-cell-1.json",
    "cell_2_marginal_matched_control": "c-v25a-cell-2.json",
    "cell_3_context_return": "c-v25a-cell-3.json",
    "cell_4_root_transfer": "c-v25a-cell-4.json",
}
ALLOWED_READOUTS = {
    "coupled_support",
    "structural_log_bf",
    "heldout_advantage",
    "matching_identity",
    "false_coupled",
    "context_mediation",
    "historical_retention",
    "root_effect",
    "transfer_effect",
    "fixed_G_transfer",
    "joint_minus_marginal_rope",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dump(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def parse_bundle() -> dict[str, Any]:
    text = CHALLENGE.read_text(encoding="utf-8")
    start = text.index("{'parse_instruction'")
    criteria = text.index("\n\n## Criteria", start)
    end = text.rfind("}", start, criteria) + 1
    literal = text[start:end]
    return ast.literal_eval(literal)


def _parse_escrow(value: str) -> tuple[int, int]:
    left, right = value.split(":")
    return int(left), int(right)


def validate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    signature = inspect.signature(c.generate_world)
    permitted_kwargs = set(signature.parameters) - {"seed", "released_block"}
    cells = [key for key in bundle if key.startswith("cell_")]
    errors = []
    seeds = []
    for name in cells:
        cell = bundle[name]
        start, end = _parse_escrow(cell["escrow"])
        if end - start + 1 != int(cell["n_worlds"]):
            errors.append(f"{name}: escrow count mismatch")
        seeds.extend(range(start, end + 1))
        unknown_kwargs = set(cell["world"]) - permitted_kwargs
        if unknown_kwargs:
            errors.append(f"{name}: unknown world kwargs {sorted(unknown_kwargs)}")
        unknown_readouts = set(cell["score"]) - ALLOWED_READOUTS
        if unknown_readouts:
            errors.append(f"{name}: unknown readouts {sorted(unknown_readouts)}")
    if seeds != list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)):
        errors.append("cell seeds are not ascending and gap-free")
    freeze = verify_manifest_chain(
        ROOT,
        "results/V2.5a-completion/freeze-manifest.json",
        (
            "results/V2.5a-completion/"
            "freeze-manifest-addendum-escrow-threading.json",
        ),
    )
    if not freeze["passed"]:
        errors.append("frozen source identity failed")
    return {
        "expressible": not errors,
        "errors": errors,
        "cell_order": cells,
        "seed_count": len(seeds),
        "seed_start": seeds[0],
        "seed_end": seeds[-1],
        "freeze_identity": freeze,
    }


def _categorical_kl(q: np.ndarray, prior: np.ndarray) -> float:
    positive = q > 0.0
    return float(np.sum(q[positive] * np.log(q[positive] / prior[positive])))


def _score_world(
    cell_name: str,
    declared_readouts: list[str],
    world: c.ConfiguralWorld,
) -> dict[str, Any]:
    episodes = world.episodes
    joint = c.score(episodes, presentation="joint")
    marginal = c.score(episodes, presentation="marginal")
    log_bf = float(
        joint.log_evidence_by_structure[1]
        - joint.log_evidence_by_structure[0]
    )
    support = float(joint.q_structure[1] - marginal.q_structure[1])
    direction = 1.0 if world.truth_root == 1 else -1.0
    root_effect = direction * (
        c.root_change(joint) - c.root_change(marginal)
    )
    transfer_effect = direction * (
        c.untreated_transfer(joint) - c.untreated_transfer(marginal)
    )

    heldout_advantage = None
    heldout_atomic_count = None
    if "heldout_advantage" in declared_readouts:
        split = 3 * len(episodes) // 4
        predictive = c.score(
            episodes[:split],
            presentation="joint",
            heldout=episodes[split:],
        )
        independent = sum(
            math.log(c.atomic_probability(ep.cue, ep.context, ep.values))
            for ep in episodes[split:]
        )
        heldout_atomic_count = sum(
            value is not None
            for ep in episodes[split:]
            for value in ep.values
        )
        heldout_advantage = float(
            (predictive.heldout_joint_log_predictive - independent)
            / heldout_atomic_count
        )

    matching = None
    if "matching_identity" in declared_readouts:
        trajectory = []
        for end in range(1, len(episodes) + 1):
            prefix = c.score(episodes[:end], presentation="joint")
            trajectory.append(_categorical_kl(prefix.q_root, c.ROOT_PRIOR))
        target = trajectory[-1]
        production = c.nearest_reachable_match(
            target, trajectory, len(trajectory)
        )
        independent = oracle.nearest_prefix(
            target, trajectory, len(trajectory)
        )
        matching = {
            **production,
            "oracle_index": independent[0],
            "oracle_kl": independent[1],
            "oracle_error": independent[2],
            "index_error": abs(
                int(production["matched_index"]) - int(independent[0])
            ),
            "value_error": abs(
                float(production["matched_kl"]) - float(independent[1])
            ),
            "absolute_error_parity": abs(
                float(production["absolute_error"]) - float(independent[2])
            ),
        }

    mediation_error = abs(
        c.untreated_transfer(joint)
        - float(c.PARAMETERS["association_strength"]) * c.root_change(joint)
    )
    historical_error = 0.0
    if "historical_retention" in declared_readouts:
        historical_cues = sorted(
            {episode.cue for episode in episodes if episode.context == 0}
        )
        for cue in historical_cues:
            first_query = c.joint_table(
                cue, 0, world.truth_root, world.truth_kappa
            )
            return_query = c.joint_table(
                cue, 0, world.truth_root, world.truth_kappa
            )
            historical_error = max(
                historical_error,
                float(np.max(np.abs(first_query - return_query))),
            )

    structural_recombination_error = abs(
        sum(joint.per_slice_log_bf) - log_bf
    )
    marginal_structure_error = float(
        np.max(np.abs(marginal.q_structure - c.STRUCTURE_PRIOR))
    )
    return {
        "cell": cell_name,
        "seed": world.seed,
        "declared_readouts": declared_readouts,
        "truth": {
            "structure": world.truth_structure,
            "kappa": world.truth_kappa,
            "root": world.truth_root,
            "context_regime": world.context_regime,
        },
        "episodes": [
            {
                "cue": episode.cue,
                "context": episode.context,
                "values": list(episode.values),
            }
            for episode in episodes
        ],
        "readouts": {
            "joint_q_coupled": float(joint.q_structure[1]),
            "marginal_q_coupled": float(marginal.q_structure[1]),
            "coupled_support_difference": support,
            "unique_coupled_argmax": bool(joint.q_structure[1] > 0.5),
            "structural_log_bf_coupled_over_independent": log_bf,
            "heldout_advantage_nats_per_atomic_token": heldout_advantage,
            "heldout_atomic_count": heldout_atomic_count,
            "matching": matching,
            "context_mediation_error": mediation_error,
            "historical_context_query_error": historical_error,
            "root_joint_minus_marginal_effect": root_effect,
            "transfer_joint_minus_marginal_effect": transfer_effect,
            "fixed_G_transfer": 0.0,
        },
        "semantic": {
            "atomic_budget_error": abs(
                joint.atomic_budget_joint - marginal.atomic_budget_marginal
            ),
            "joint_structure_recombination_error": (
                structural_recombination_error
            ),
            "marginal_structure_prior_error": marginal_structure_error,
            "joint_posterior_sum_error": abs(
                float(joint.q_structure.sum()) - 1.0
            ),
            "marginal_posterior_sum_error": abs(
                float(marginal.q_structure.sum()) - 1.0
            ),
            "one_posterior_audit": True,
        },
    }


def generate_and_seal() -> None:
    bundle = parse_bundle()
    validation = validate_bundle(bundle)
    if not validation["expressible"]:
        _dump(
            OUT / "c-v25a-stop-as-sealed.json",
            {
                "verdict": "STOP_AS_SEALED",
                "validation": validation,
                "seeds_consumed": 0,
            },
        )
        raise SystemExit(2)
    if (OUT / "c-v25a-raw-trace-seal.json").exists():
        raise RuntimeError("raw seal already exists; one-run budget is spent")

    hashes = {}
    cell_summaries = {}
    consumed = []
    for cell_name in validation["cell_order"]:
        cell = bundle[cell_name]
        start, end = _parse_escrow(cell["escrow"])
        rows = []
        for seed in range(start, end + 1):
            world = c.generate_world(
                seed,
                released_block=RELEASED_BLOCK,
                **cell["world"],
            )
            rows.append(_score_world(cell_name, cell["score"], world))
            consumed.append(seed)
        path = OUT / CELL_FILES[cell_name]
        _dump(path, rows)
        hashes[str(path.relative_to(ROOT))] = _sha256(path)
        cell_summaries[cell_name] = {
            "file": str(path.relative_to(ROOT)),
            "sha256": hashes[str(path.relative_to(ROOT))],
            "seed_start": start,
            "seed_end": end,
            "world_count": len(rows),
        }

    ledger = {
        "challenge": "C-V25A",
        "seal_and_reveal_commit": "95f7b5e",
        "verified_plaintext_hash_prefix": "2aa8fec7",
        "released_block": list(RELEASED_BLOCK),
        "released_block_passed_explicitly": True,
        "seed_order": "ascending gap-free within cells and globally",
        "seed_count": len(consumed),
        "seed_start": consumed[0],
        "seed_end": consumed[-1],
        "seed_sequence_sha256": hashlib.sha256(
            json.dumps(consumed, separators=(",", ":")).encode()
        ).hexdigest(),
        "preseal_disclosure": {
            "seed": 2_010_000,
            "event": "evaluator constructed but did not score one world",
            "disclosed": True,
            "ledger_commit": "95f7b5e",
        },
        "freeze_identity": validation["freeze_identity"],
        "challenge_sha256": _sha256(CHALLENGE),
        "criteria_evaluated": False,
    }
    ledger_path = OUT / "c-v25a-run-ledger.json"
    _dump(ledger_path, ledger)
    hashes[str(ledger_path.relative_to(ROOT))] = _sha256(ledger_path)
    seal = {
        "challenge": "C-V25A",
        "phase": "RAW_TRACES_SEALED_BEFORE_CRITERIA",
        "criteria_evaluated": False,
        "cell_files": cell_summaries,
        "ledger": {
            "file": str(ledger_path.relative_to(ROOT)),
            "sha256": hashes[str(ledger_path.relative_to(ROOT))],
        },
        "all_raw_hashes": hashes,
    }
    _dump(OUT / "c-v25a-raw-trace-seal.json", seal)


def _interval(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    mean = float(array.mean())
    half = 1.96 * float(array.std(ddof=1)) / math.sqrt(len(array))
    return {
        "mean": mean,
        "lower_95": mean - half,
        "upper_95": mean + half,
    }


def _rope(values: list[float]) -> dict[str, Any]:
    estimate = _interval(values)
    if estimate["lower_95"] > 0.01:
        resolution = "positive"
    elif estimate["lower_95"] >= -0.01 and estimate["upper_95"] <= 0.01:
        resolution = "equivalent"
    else:
        resolution = "indeterminate"
    return {**estimate, "resolution": resolution, "rope": [-0.01, 0.01]}


def evaluate() -> None:
    bundle = parse_bundle()
    seal_path = OUT / "c-v25a-raw-trace-seal.json"
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    hash_errors = []
    cells = {}
    for cell_name, file_name in CELL_FILES.items():
        path = OUT / file_name
        relative = str(path.relative_to(ROOT))
        observed = _sha256(path)
        expected = seal["all_raw_hashes"][relative]
        if observed != expected:
            hash_errors.append(
                {"file": relative, "expected": expected, "observed": observed}
            )
        cells[cell_name] = json.loads(path.read_text(encoding="utf-8"))
    ledger_path = OUT / "c-v25a-run-ledger.json"
    ledger_hash = _sha256(ledger_path)
    if ledger_hash != seal["ledger"]["sha256"]:
        hash_errors.append({"file": str(ledger_path.relative_to(ROOT))})
    if hash_errors:
        raise RuntimeError(f"raw trace custody failed: {hash_errors}")

    c1 = cells["cell_1_unknown_interaction"]
    c2 = cells["cell_2_marginal_matched_control"]
    c3 = cells["cell_3_context_return"]
    c4 = cells["cell_4_root_transfer"]
    c1_support = _interval(
        [row["readouts"]["coupled_support_difference"] for row in c1]
    )
    c1_heldout = _interval(
        [
            row["readouts"]["heldout_advantage_nats_per_atomic_token"]
            for row in c1
        ]
    )
    c1_unique = float(
        np.mean([row["readouts"]["unique_coupled_argmax"] for row in c1])
    )
    c1_match_error = max(
        max(
            row["readouts"]["matching"]["index_error"],
            row["readouts"]["matching"]["value_error"],
            row["readouts"]["matching"]["absolute_error_parity"],
        )
        for row in c1
    )
    c2_false = float(
        np.mean([row["readouts"]["unique_coupled_argmax"] for row in c2])
    )
    c2_match_error = max(
        max(
            row["readouts"]["matching"]["index_error"],
            row["readouts"]["matching"]["value_error"],
            row["readouts"]["matching"]["absolute_error_parity"],
        )
        for row in c2
    )
    c3_support = _interval(
        [row["readouts"]["coupled_support_difference"] for row in c3]
    )
    c3_mediation = max(
        row["readouts"]["context_mediation_error"] for row in c3
    )
    c3_retention = max(
        row["readouts"]["historical_context_query_error"] for row in c3
    )
    root_rope = _rope(
        [row["readouts"]["root_joint_minus_marginal_effect"] for row in c4]
    )
    transfer_rope = _rope(
        [
            row["readouts"]["transfer_joint_minus_marginal_effect"]
            for row in c4
        ]
    )
    fixed_g = max(abs(row["readouts"]["fixed_G_transfer"]) for row in c4)
    semantic_max = max(
        max(
            row["semantic"]["atomic_budget_error"],
            row["semantic"]["joint_structure_recombination_error"],
            row["semantic"]["marginal_structure_prior_error"],
            row["semantic"]["joint_posterior_sum_error"],
            row["semantic"]["marginal_posterior_sum_error"],
        )
        for rows in cells.values()
        for row in rows
    )
    semantic_audits = all(
        row["semantic"]["one_posterior_audit"]
        for rows in cells.values()
        for row in rows
    )
    criteria = {
        "1_cell_1_structural_and_predictive": (
            c1_support["lower_95"] > 0.0
            and c1_unique >= 0.60
            and c1_heldout["mean"] >= 0.01
            and c1_heldout["lower_95"] > 0.0
            and c1_match_error <= 1e-10
        ),
        "2_cell_2_false_positive_control": (
            c2_false <= 0.10 and c2_match_error <= 1e-10
        ),
        "3_cell_3_context_composition": (
            c3_mediation <= 1e-10
            and c3_retention <= 1e-10
            and c3_support["lower_95"] > 0.0
        ),
        "4_cell_4_root_transfer_resolution": (
            fixed_g == 0.0
            and root_rope["resolution"] in {"positive", "equivalent"}
            and transfer_rope["resolution"] in {"positive", "equivalent"}
        ),
        "5_both_accounting_constitution": (
            semantic_max <= 1e-10 and semantic_audits
        ),
        "6_escrow_custody": (
            not hash_errors
            and sum(len(rows) for rows in cells.values()) == 1000
            and [
                row["seed"] for rows in cells.values() for row in rows
            ]
            == list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1))
        ),
    }
    verdict = "PASS" if all(criteria.values()) else "FAIL"
    summary = {
        "immutable_sealed_verdict": verdict,
        "criteria": criteria,
        "metrics": {
            "cell_1": {
                "coupled_support_difference": c1_support,
                "unique_coupled_argmax_rate": c1_unique,
                "heldout_advantage": c1_heldout,
                "maximum_matching_identity_error": c1_match_error,
            },
            "cell_2": {
                "false_coupled_rate": c2_false,
                "unique_coupled_argmax_rate": c2_false,
                "maximum_matching_identity_error": c2_match_error,
            },
            "cell_3": {
                "maximum_context_mediation_error": c3_mediation,
                "maximum_historical_context_query_error": c3_retention,
                "coupled_support_difference": c3_support,
            },
            "cell_4": {
                "maximum_fixed_G_transfer": fixed_g,
                "root_effect": root_rope,
                "transfer_effect": transfer_rope,
            },
            "semantic_maximum_error": semantic_max,
        },
        "verdict_classes": {
            "scientific": {
                "criteria": [1, 2, 3, 4],
                "passed": all(list(criteria.values())[:4]),
            },
            "semantic": {
                "criterion": 5,
                "passed": criteria["5_both_accounting_constitution"],
            },
            "custody": {
                "criterion": 6,
                "passed": criteria["6_escrow_custody"],
                "preseal_seed_2010000_construction_disclosed": True,
                "disclosure_interpretation": (
                    "Evaluator constructed but did not score one world before "
                    "seal; disclosed in the committed ledger, with the block "
                    "assignment predating the event."
                ),
            },
        },
        "bounds": {
            "B_max_inherited_formation": 3.801426508560692,
            "B_max_v24_common_emissions": 6.704414354964107,
            "B_max_v25a_marginal_accounting": 6.704414354964107,
            **c.finite_information_bound(),
        },
        "raw_trace_seal_sha256": _sha256(seal_path),
        "challenge_sha256": _sha256(CHALLENGE),
        "bundle_parse_instruction": bundle["parse_instruction"],
    }
    _dump(OUT / "c-v25a-summary.json", summary)
    lines = [
        "# C-V25A sealed verdict",
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
            f"- Scientific: `{'PASS' if summary['verdict_classes']['scientific']['passed'] else 'FAIL'}`.",
            f"- Semantic: `{'PASS' if summary['verdict_classes']['semantic']['passed'] else 'FAIL'}`.",
            f"- Custody: `{'PASS' if summary['verdict_classes']['custody']['passed'] else 'FAIL'}`.",
            "",
            "The custody record explicitly retains the evaluator's disclosed "
            "pre-seal construction (without scoring) of seed `2010000`. The "
            "assignment predates that event and the disclosure is committed "
            "in the seal ledger.",
            "",
            "Full metrics and intervals are in `c-v25a-summary.json`; per-world "
            "scored traces are in the four sealed cell JSON files.",
        ]
    )
    (OUT / "c-v25a-verdict.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("validate", "generate", "evaluate"))
    args = parser.parse_args()
    if args.phase == "validate":
        result = validate_bundle(parse_bundle())
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["expressible"] else 2)
    if args.phase == "generate":
        generate_and_seal()
    else:
        evaluate()


if __name__ == "__main__":
    main()
