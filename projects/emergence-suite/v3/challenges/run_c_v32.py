#!/usr/bin/env python3
"""One-shot sealed execution for C-V32."""

from __future__ import annotations

import ast
import hashlib
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from ref.trace_sink import serializing_trace_context  # noqa: E402
from ref.v32 import (  # noqa: E402
    TemporalStructure,
    generate_world,
    historical_prediction,
    present_context_transfer,
    score_world,
)


CHALLENGE = ROOT / "sealed-revealed" / "C-V32-split-challenge.md"
RESULTS = ROOT / "results" / "V3.2"
RUN_DIR = RESULTS / "c-v32"
MANIFEST = RESULTS / "freeze-manifest.json"
SEAL_RECORD = (
    REPOSITORY / "projects" / "ifs-paper" / "suite-v2-sealed-hashes.md"
)
EXPECTED_CHALLENGE_SHA256 = (
    "441c4a2abe24cb639fcaff1f2058b8ea501f55a1a117ec372156c1f68d8575f0"
)
RELEASED_BLOCK = (4_020_000, 4_023_999)
CELL_KEYS = (
    "cell_1_witnessed_split",
    "cell_2_single_regime",
    "cell_3_mixed_drift_recurrent",
    "cell_4_one_way_no_recurrence",
)
STAGE_CUSTODY_NOTE = "CUSTODY_NOTE_PREFLIGHT_UNSERIALIZED"


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(child) for child in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            _plain(value),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(
            _plain(value), indent=2, sort_keys=True, allow_nan=False
        )
        + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_bundle() -> dict[str, Any]:
    text = CHALLENGE.read_text(encoding="utf-8")
    section = text.index("## Cells (parse instruction binding)")
    start = text.index("{", section)
    end = text.index("\n\n## Criteria", start)
    literal = text[start:end]
    parsed = ast.literal_eval(literal)
    if not isinstance(parsed, dict):
        raise TypeError("sealed cell literal is not one dict")
    return parsed


def _verify_freeze() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in manifest["files"].items():
        path = ROOT / relative
        actual = _sha256(path)
        if actual != expected:
            mismatches.append(
                {"path": relative, "expected": expected, "actual": actual}
            )
    if mismatches:
        raise RuntimeError(f"frozen identity mismatch: {mismatches}")
    if (
        manifest["status"]
        != "FREEZE_CANDIDATE_CUSTODY_NOTE_PREFLIGHT_UNSERIALIZED"
    ):
        raise RuntimeError("unexpected V3.2 freeze disposition")
    return {
        "manifest_path": str(MANIFEST.relative_to(REPOSITORY)),
        "manifest_files_verified": len(manifest["files"]),
        "manifest_status": manifest["status"],
        "mismatches": mismatches,
    }


def _escrow_range(text: str) -> tuple[int, int]:
    start, end = text.split(":")
    return int(start), int(end)


def _validate_bundle(bundle: Mapping[str, Any]) -> list[dict[str, Any]]:
    expected_starts = (4_020_000, 4_021_000, 4_022_000, 4_023_000)
    cells = []
    for key, expected_start in zip(CELL_KEYS, expected_starts):
        definition = bundle[key]
        start, end = _escrow_range(definition["escrow"])
        if (start, end) != (expected_start, expected_start + 999):
            raise ValueError(f"unexpected escrow partition for {key}")
        if definition["n_worlds"] != 1000:
            raise ValueError(f"unexpected world count for {key}")
        structure = TemporalStructure(**definition["structure"])
        if definition["evidence_style"] not in {
            "natural",
            "witnessing",
            "single_regime",
        }:
            raise ValueError(f"unsupported evidence style for {key}")
        cells.append(
            {
                "key": key,
                "start": start,
                "end": end,
                "structure": structure,
                "evidence_style": definition["evidence_style"],
                "length": int(definition["length"]),
            }
        )
    consumed = [
        seed
        for cell in cells
        for seed in range(cell["start"], cell["end"] + 1)
    ]
    if consumed != list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)):
        raise ValueError("escrow consumption is not ascending and gap-free")
    return cells


def _posterior_trace(posterior: Any) -> dict[str, Any]:
    return {
        "programs": [asdict(program) for program in posterior.programs],
        "probabilities": posterior.probabilities,
        "log_evidence": posterior.log_evidence,
        "active_context_probabilities": posterior.active_context_probabilities,
        "scope_probabilities": posterior.scope_probabilities,
        "dynamics_probabilities": posterior.dynamics_probabilities,
        "parameter_means": posterior.parameter_means,
        "root_means": posterior.root_means,
        "normalization_error": abs(
            math.fsum(posterior.probabilities) - 1.0
        ),
    }


def _execute_world(cell: Mapping[str, Any], seed: int) -> dict[str, Any]:
    with serializing_trace_context(
        f"C-V32:{cell['key']}:{seed}"
    ) as sink:
        world = generate_world(
            seed,
            structure=cell["structure"],
            length=cell["length"],
            evidence_style=cell["evidence_style"],
            released_block=RELEASED_BLOCK,
        )
        posterior = score_world(world)
        score = _posterior_trace(posterior)
        score["truth_structure_probability"] = (
            posterior.structure_probability(cell["structure"])
        )
        score["outcome_context_scope_probability"] = (
            posterior.scope_probability(
                "outcome_emission", "context_specific"
            )
        )
        score["outcome_recurrence_probability"] = (
            posterior.dynamics_probability(
                "outcome_emission", "discrete_recurrent_context"
            )
        )
        score["cue_dynamics_argmax"] = max(
            posterior.dynamics_probabilities["cue_emission"],
            key=posterior.dynamics_probabilities["cue_emission"].get,
        )
        score["outcome_dynamics_argmax"] = max(
            posterior.dynamics_probabilities["outcome_emission"],
            key=posterior.dynamics_probabilities["outcome_emission"].get,
        )

        comparator = None
        if cell["key"] == CELL_KEYS[0]:
            before = historical_prediction(
                posterior, "outcome_emission", 0, 0
            )
            _ = present_context_transfer(posterior, context=1)
            after = historical_prediction(
                posterior, "outcome_emission", 0, 0
            )
            score["historical_parameter_query_error"] = abs(after - before)
            comparator_world = generate_world(
                seed,
                structure=cell["structure"],
                length=cell["length"],
                evidence_style="single_regime",
                released_block=RELEASED_BLOCK,
            )
            comparator_posterior = score_world(comparator_world)
            comparator_scope = comparator_posterior.scope_probability(
                "outcome_emission", "context_specific"
            )
            score["witnessing_gain"] = (
                score["outcome_context_scope_probability"] - comparator_scope
            )
            comparator = {
                "world": asdict(comparator_world),
                "posterior": _posterior_trace(comparator_posterior),
                "outcome_context_scope_probability": comparator_scope,
            }

        return {
            "seed": seed,
            "cell": cell["key"],
            "configuration": {
                "structure": asdict(cell["structure"]),
                "length": cell["length"],
                "evidence_style": cell["evidence_style"],
                "released_block": list(RELEASED_BLOCK),
            },
            "world": asdict(world),
            "posterior": score,
            "single_regime_comparator": comparator,
            "runtime_trace_events": tuple(sink.events),
        }


def _seal_cell(cell: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, list[Any]]]:
    trace_path = RUN_DIR / f"{cell['key']}-traces.jsonl"
    record_hashes = []
    file_hasher = hashlib.sha256()
    extracted: dict[str, list[Any]] = {
        "seed": [],
        "truth_structure_probability": [],
        "outcome_context_scope_probability": [],
        "outcome_recurrence_probability": [],
        "cue_dynamics_argmax": [],
        "outcome_dynamics_argmax": [],
        "normalization_error": [],
        "historical_parameter_query_error": [],
        "witnessing_gain": [],
    }
    with trace_path.open("wb") as handle:
        for seed in range(cell["start"], cell["end"] + 1):
            record = _execute_world(cell, seed)
            encoded = _canonical_bytes(record)
            handle.write(encoded)
            handle.flush()
            file_hasher.update(encoded)
            record_hashes.append(
                {
                    "seed": seed,
                    "sha256": hashlib.sha256(encoded).hexdigest(),
                }
            )
            extracted["seed"].append(seed)
            for key in extracted:
                if key == "seed":
                    continue
                if key in record["posterior"]:
                    extracted[key].append(record["posterior"][key])
    ledger = {
        "cell": cell["key"],
        "seed_block": [cell["start"], cell["end"]],
        "world_count": len(record_hashes),
        "trace_file": trace_path.name,
        "trace_file_sha256": file_hasher.hexdigest(),
        "record_hashes": record_hashes,
        "serialized_at_execution_before_criteria": True,
    }
    ledger_path = RUN_DIR / f"{cell['key']}-trace-hashes.json"
    _write_json(ledger_path, ledger)
    ledger["ledger_file"] = ledger_path.name
    ledger["ledger_sha256"] = _sha256(ledger_path)
    return ledger, extracted


def _bootstrap_interval(values: Sequence[float]) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    rng = np.random.default_rng(32_000_001)
    draws = np.empty(10_000)
    for index in range(len(draws)):
        draws[index] = rng.choice(
            array, len(array), replace=True
        ).mean()
    return tuple(
        float(value) for value in np.quantile(draws, (0.025, 0.975))
    )


def main() -> None:
    if RUN_DIR.exists() or (RESULTS / "c-v32-verdict.md").exists():
        raise SystemExit("C-V32 one-run output already exists")
    if _sha256(CHALLENGE) != EXPECTED_CHALLENGE_SHA256:
        raise SystemExit("C-V32 plaintext does not match the committed seal")
    seal_text = SEAL_RECORD.read_text(encoding="utf-8")
    if EXPECTED_CHALLENGE_SHA256 not in seal_text:
        raise SystemExit("C-V32 seal record is absent")
    release_text = (
        "Escrow: C-V32 seeds 4020000:4023999, released by this record."
    )
    if release_text not in seal_text:
        raise SystemExit("C-V32 escrow release record is absent")

    freeze_identity = _verify_freeze()
    bundle = _parse_bundle()
    cells = _validate_bundle(bundle)
    RUN_DIR.mkdir(parents=True)

    trace_ledgers = []
    values: dict[str, dict[str, list[Any]]] = {}
    for cell in cells:
        ledger, extracted = _seal_cell(cell)
        trace_ledgers.append(ledger)
        values[cell["key"]] = extracted

    trace_schema = {
        "top_level": [
            "seed",
            "cell",
            "configuration",
            "world",
            "posterior",
            "single_regime_comparator",
            "runtime_trace_events",
        ],
        "posterior_readouts": sorted(
            key
            for key in values[CELL_KEYS[0]]
            if key != "seed"
        ),
    }
    schema_hash = hashlib.sha256(
        json.dumps(trace_schema, sort_keys=True).encode("utf-8")
    ).hexdigest()
    raw_trace_seal = {
        "challenge_sha256": EXPECTED_CHALLENGE_SHA256,
        "schema_sha256": schema_hash,
        "world_count": 4000,
        "cells": trace_ledgers,
        "sealed_before_criteria": True,
    }
    raw_trace_seal_path = RUN_DIR / "raw-traces-seal.json"
    _write_json(raw_trace_seal_path, raw_trace_seal)
    raw_trace_seal_hash = _sha256(raw_trace_seal_path)

    consumed_seeds = [
        seed for key in CELL_KEYS for seed in values[key]["seed"]
    ]
    run_ledger = {
        "challenge": "C-V32",
        "challenge_sha256": EXPECTED_CHALLENGE_SHA256,
        "release_authority": (
            "projects/ifs-paper/suite-v2-sealed-hashes.md C-V32 record "
            "committed at 36e9861"
        ),
        "released_block": list(RELEASED_BLOCK),
        "consumption": "ascending_gap_free_once",
        "consumed_seed_count": len(consumed_seeds),
        "first_seed": consumed_seeds[0],
        "last_seed": consumed_seeds[-1],
        "frozen_identity": freeze_identity,
        "raw_trace_seal": raw_trace_seal_path.name,
        "raw_trace_seal_sha256": raw_trace_seal_hash,
        "criteria_evaluated_after_trace_seal": True,
        "stage_custody_note_carried": STAGE_CUSTODY_NOTE,
    }
    _write_json(RUN_DIR / "run-ledger.json", run_ledger)

    # Criteria evaluation begins only after all raw traces and their seal exist.
    summaries = {
        key: {
            "mean_truth_structure_probability": float(
                np.mean(cell["truth_structure_probability"])
            ),
            "mean_outcome_context_scope_probability": float(
                np.mean(cell["outcome_context_scope_probability"])
            ),
            "mean_outcome_recurrence_probability": float(
                np.mean(cell["outcome_recurrence_probability"])
            ),
            "cue_dynamics_accuracy": float(
                np.mean(
                    np.asarray(cell["cue_dynamics_argmax"])
                    == (
                        "ordered_random_walk"
                        if key == CELL_KEYS[2]
                        else ""
                    )
                )
            ),
            "outcome_dynamics_accuracy": float(
                np.mean(
                    np.asarray(cell["outcome_dynamics_argmax"])
                    == (
                        "discrete_recurrent_context"
                        if key == CELL_KEYS[2]
                        else ""
                    )
                )
            ),
            "maximum_normalization_error": max(
                cell["normalization_error"]
            ),
        }
        for key, cell in values.items()
    }
    c1, c2, c3, c4 = CELL_KEYS
    witnessing_values = [
        float(value) for value in values[c1]["witnessing_gain"]
    ]
    witnessing_mean = float(np.mean(witnessing_values))
    witnessing_interval = _bootstrap_interval(witnessing_values)
    historical_max = max(
        values[c1]["historical_parameter_query_error"]
    )
    maximum_normalization_error = max(
        summary["maximum_normalization_error"]
        for summary in summaries.values()
    )
    custody_ok = (
        consumed_seeds
        == list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1))
        and all(ledger["world_count"] == 1000 for ledger in trace_ledgers)
        and raw_trace_seal["sealed_before_criteria"]
        and maximum_normalization_error <= 1e-10
    )
    criteria = {
        "criterion_1_witnessed_split": (
            summaries[c1]["mean_truth_structure_probability"] >= 0.90
            and summaries[c1][
                "mean_outcome_context_scope_probability"
            ]
            >= 0.95
            and historical_max <= 1e-10
        ),
        "criterion_2_single_regime_scope_neutrality": (
            summaries[c2][
                "mean_outcome_context_scope_probability"
            ]
            <= 0.30
            and summaries[c2]["mean_truth_structure_probability"] >= 0.50
        ),
        "criterion_3_mixed_temporal_structure": (
            summaries[c3]["mean_truth_structure_probability"] >= 0.85
            and summaries[c3]["cue_dynamics_accuracy"] >= 0.85
            and summaries[c3]["outcome_dynamics_accuracy"] >= 0.85
        ),
        "criterion_4_one_way_not_recurrent": (
            summaries[c4]["mean_outcome_recurrence_probability"] <= 0.29
        ),
        "criterion_5_semantic_and_custody": custody_ok,
    }
    verdict = "PASS" if all(criteria.values()) else "FAIL"
    verdict_classes = {
        "scientific": all(
            criteria[key]
            for key in (
                "criterion_1_witnessed_split",
                "criterion_2_single_regime_scope_neutrality",
                "criterion_3_mixed_temporal_structure",
                "criterion_4_one_way_not_recurrent",
            )
        ),
        "semantic": (
            maximum_normalization_error <= 1e-10
        ),
        "custody": custody_ok,
    }
    summary = {
        "immutable_verdict": verdict,
        "criteria": criteria,
        "cell_summaries": summaries,
        "witnessing_gain": {
            "mean": witnessing_mean,
            "whole_world_bootstrap_95_interval": witnessing_interval,
            "bootstrap_replicates": 10_000,
            "comparator": (
                "same-seed, same-structure single_regime presentation; "
                "frozen Gate-3 construct"
            ),
        },
        "historical_parameter_query_max_error": historical_max,
        "maximum_normalization_error": maximum_normalization_error,
        "raw_trace_seal_sha256": raw_trace_seal_hash,
        "verdict_classes": verdict_classes,
        "stage_custody_note": STAGE_CUSTODY_NOTE,
    }
    _write_json(RUN_DIR / "summary.json", summary)
    for key in CELL_KEYS:
        _write_json(
            RUN_DIR / f"{key}-results.json",
            {
                "cell": key,
                "summary": summaries[key],
                "trace_ledger": next(
                    ledger for ledger in trace_ledgers if ledger["cell"] == key
                ),
            },
        )

    lines = [
        f"# C-V32 immutable sealed verdict: {verdict}",
        "",
        "The verdict above is the single sealed verdict and is retained as "
        "written.",
        "",
        f"Permanent stage custody clause: `{STAGE_CUSTODY_NOTE}`. The "
        "repair-pilot preflight violation remains in the stage record; this "
        "challenge does not clear or reclassify it.",
        "",
        "## Five sealed criteria",
        "",
    ]
    for index, key in enumerate(criteria, start=1):
        lines.append(
            f"{index}. **{'PASS' if criteria[key] else 'FAIL'}** — `{key}`."
        )
    lines.extend(
        [
            "",
            "## Cell results",
            "",
            "| cell | true structure | context scope | recurrence | cue dynamics accuracy | outcome dynamics accuracy |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for key in CELL_KEYS:
        item = summaries[key]
        lines.append(
            "| {cell} | {truth:.6f} | {scope:.6f} | {recurrence:.6f} | "
            "{cue:.6f} | {outcome:.6f} |".format(
                cell=key,
                truth=item["mean_truth_structure_probability"],
                scope=item["mean_outcome_context_scope_probability"],
                recurrence=item["mean_outcome_recurrence_probability"],
                cue=item["cue_dynamics_accuracy"],
                outcome=item["outcome_dynamics_accuracy"],
            )
        )
    lines.extend(
        [
            "",
            "Cell-1 witnessing gain versus its frozen same-seed "
            f"single-regime comparator: `{witnessing_mean:.6f}`, whole-world "
            "bootstrap 95% interval "
            f"`[{witnessing_interval[0]:.6f}, "
            f"{witnessing_interval[1]:.6f}]`.",
            "",
            "Maximum historical-parameter query error: "
            f"`{historical_max:.3g}`. Maximum posterior-normalization error: "
            f"`{maximum_normalization_error:.3g}`.",
            "",
            "## Verdict classes",
            "",
            f"- Scientific: **{'PASS' if verdict_classes['scientific'] else 'FAIL'}**.",
            f"- Semantic: **{'PASS' if verdict_classes['semantic'] else 'FAIL'}**.",
            f"- Custody for this sealed execution: **{'PASS' if verdict_classes['custody'] else 'FAIL'}**.",
            f"- Stage custody history: `{STAGE_CUSTODY_NOTE}` retained.",
            "",
            "All 4,000 escrow seeds were consumed once, ascending and "
            "gap-free. Per-world traces and hashes were written before any "
            "criterion was evaluated. Raw trace seal SHA-256: "
            f"`{raw_trace_seal_hash}`.",
            "",
        ]
    )
    (RESULTS / "c-v32-verdict.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    if verdict == "PASS":
        (RESULTS / "stage-verdict.md").write_text(
            "# V3.2 stage verdict: PASS_WITH_CUSTODY_NOTE_PREFLIGHT_UNSERIALIZED\n\n"
            "The initial Stage-0 design defect—single-regime observations "
            "spuriously identifying context scope—remains retained. Its "
            "adjudicated repair established exact pre-witness scope neutrality. "
            "The repair-pilot preflight custody violation also remains retained "
            "under `CUSTODY_NOTE_PREFLIGHT_UNSERIALIZED`, after bit-exact "
            "reproduction and runtime trace-sink hardening. Gates 1–5 passed. "
            "C-V32 passed all five sealed criteria and its scientific, semantic, "
            "and sealed-execution custody classes.\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
