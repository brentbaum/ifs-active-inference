#!/usr/bin/env python3
"""One-shot sealed execution for C-V31."""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from ref.v31 import FormationConfig, generate_world, score_world  # noqa: E402


CHALLENGE = ROOT / "sealed-revealed" / "C-V31-grow-challenge.md"
RESULTS = ROOT / "results" / "V3.1"
RUN_DIR = RESULTS / "c-v31"
MANIFEST = RESULTS / "freeze-manifest.json"
SEAL_RECORD = (
    REPOSITORY / "projects" / "ifs-paper" / "suite-v2-sealed-hashes.md"
)
EXPECTED_CHALLENGE_SHA256 = (
    "1e78a9c3443ddb10dfc8e7b56d75321f0487db49eb79443caecfb9e0011cf740"
)
RELEASED_BLOCK = (4_010_000, 4_013_999)
CELL_KEYS = (
    "cell_1_chronic_real_effective_censored",
    "cell_2_acute_real_effective_full",
    "cell_3_chronic_safe_sham_masked",
    "cell_4_none_real_sham_full",
)


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
    inherited = manifest["inherited_manifest"]
    inherited_actual = _sha256(ROOT / inherited["path"])
    if inherited_actual != inherited["sha256"]:
        mismatches.append(
            {
                "path": inherited["path"],
                "expected": inherited["sha256"],
                "actual": inherited_actual,
            }
        )
    if mismatches:
        raise RuntimeError(f"frozen identity mismatch: {mismatches}")
    return {
        "manifest_path": str(MANIFEST.relative_to(REPOSITORY)),
        "manifest_file_count": manifest["file_count"],
        "manifest_files_verified": len(manifest["files"]),
        "inherited_manifest_verified": True,
        "mismatches": mismatches,
    }


def _escrow_range(text: str) -> tuple[int, int]:
    start, end = text.split(":")
    return int(start), int(end)


def _validate_bundle(bundle: Mapping[str, Any]) -> list[dict[str, Any]]:
    expected_starts = (4_010_000, 4_011_000, 4_012_000, 4_013_000)
    cells = []
    for key, expected_start in zip(CELL_KEYS, expected_starts):
        definition = bundle[key]
        start, end = _escrow_range(definition["escrow"])
        if (start, end) != (expected_start, expected_start + 999):
            raise ValueError(f"unexpected escrow partition for {key}")
        if definition["n_worlds"] != 1000:
            raise ValueError(f"unexpected world count for {key}")
        config = FormationConfig(**definition["config"])
        cells.append(
            {
                "key": key,
                "start": start,
                "end": end,
                "config": config,
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


def _trace_score(posterior: Any) -> dict[str, Any]:
    return {
        "probabilities": posterior.probabilities,
        "log_evidence": posterior.log_evidence,
        "edge_probabilities": dict(posterior.edge_probabilities),
        "active_mode_probability": posterior.active_mode_probability,
        "transient_probability": posterior.transient_probability,
        "danger_probability": posterior.danger_probability,
        "part_probability": posterior.part_probability,
        "efficacy_probability": posterior.efficacy_probability,
        "delta_i": posterior.delta_i,
        "burden_mass": posterior.burden_mass,
        "normalization_error": abs(
            float(np.sum(np.asarray(posterior.probabilities))) - 1.0
        ),
    }


def _seal_cell(
    cell: Mapping[str, Any], records: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    trace_path = RUN_DIR / f"{cell['key']}-traces.jsonl"
    hashes = []
    file_hasher = hashlib.sha256()
    with trace_path.open("wb") as handle:
        for record in records:
            encoded = _canonical_bytes(record)
            handle.write(encoded)
            file_hasher.update(encoded)
            hashes.append(
                {
                    "seed": record["seed"],
                    "sha256": hashlib.sha256(encoded).hexdigest(),
                }
            )
    ledger = {
        "cell": cell["key"],
        "seed_block": [cell["start"], cell["end"]],
        "world_count": len(records),
        "trace_file": trace_path.name,
        "trace_file_sha256": file_hasher.hexdigest(),
        "record_hashes": hashes,
    }
    ledger_path = RUN_DIR / f"{cell['key']}-trace-hashes.json"
    _write_json(ledger_path, ledger)
    ledger["ledger_file"] = ledger_path.name
    ledger["ledger_sha256"] = _sha256(ledger_path)
    return ledger


def _difference_interval(
    high: Sequence[float], low: Sequence[float]
) -> tuple[float, float]:
    high_values = np.asarray(high, dtype=float)
    low_values = np.asarray(low, dtype=float)
    rng = np.random.default_rng(31_000_005)
    draws = np.empty(2000)
    for index in range(len(draws)):
        draws[index] = (
            rng.choice(high_values, len(high_values), replace=True).mean()
            - rng.choice(low_values, len(low_values), replace=True).mean()
        )
    return tuple(
        float(value) for value in np.quantile(draws, (0.025, 0.975))
    )


def main() -> None:
    if RUN_DIR.exists() or (RESULTS / "c-v31-verdict.md").exists():
        raise SystemExit("C-V31 one-run output already exists")
    if _sha256(CHALLENGE) != EXPECTED_CHALLENGE_SHA256:
        raise SystemExit("C-V31 plaintext does not match the committed seal")
    seal_text = SEAL_RECORD.read_text(encoding="utf-8")
    if EXPECTED_CHALLENGE_SHA256 not in seal_text:
        raise SystemExit("C-V31 seal record is absent")
    if "C-V31 seeds 4010000:4013999, released by this record" not in seal_text:
        raise SystemExit("C-V31 escrow release record is absent")

    freeze_identity = _verify_freeze()
    bundle = _parse_bundle()
    cells = _validate_bundle(bundle)
    RUN_DIR.mkdir(parents=True)

    cell_records: dict[str, list[dict[str, Any]]] = {}
    trace_ledgers = []
    for cell in cells:
        records = []
        for seed in range(cell["start"], cell["end"] + 1):
            world = generate_world(
                seed,
                cell["config"],
                released_block=RELEASED_BLOCK,
            )
            posterior = score_world(world)
            records.append(
                {
                    "seed": seed,
                    "cell": cell["key"],
                    "config": asdict(cell["config"]),
                    "world": asdict(world),
                    "score": _trace_score(posterior),
                }
            )
        cell_records[cell["key"]] = records
        trace_ledgers.append(_seal_cell(cell, records))

    trace_schema = {
        "top_level": ["seed", "cell", "config", "world", "score"],
        "score": sorted(cell_records[CELL_KEYS[0]][0]["score"]),
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

    run_ledger = {
        "challenge": "C-V31",
        "challenge_sha256": EXPECTED_CHALLENGE_SHA256,
        "release_authority": (
            "projects/ifs-paper/suite-v2-sealed-hashes.md "
            "C-V31 record at commit f9a9a49"
        ),
        "released_block": list(RELEASED_BLOCK),
        "consumption": "ascending_gap_free_once",
        "consumed_seed_count": 4000,
        "first_seed": 4_010_000,
        "last_seed": 4_013_999,
        "frozen_identity": freeze_identity,
        "raw_trace_seal": raw_trace_seal_path.name,
        "raw_trace_seal_sha256": raw_trace_seal_hash,
        "criteria_evaluated_after_trace_seal": True,
    }
    _write_json(RUN_DIR / "run-ledger.json", run_ledger)

    values = {
        key: {
            readout: [
                float(record["score"][readout])
                for record in cell_records[key]
            ]
            for readout in (
                "part_probability",
                "danger_probability",
                "efficacy_probability",
                "delta_i",
                "normalization_error",
            )
        }
        for key in CELL_KEYS
    }
    summaries = {
        key: {
            f"mean_{readout}": float(np.mean(readout_values))
            for readout, readout_values in cell_values.items()
        }
        for key, cell_values in values.items()
    }
    c1, c2, c3, c4 = CELL_KEYS
    high_part = values[c1]["part_probability"] + values[c3]["part_probability"]
    low_part = values[c2]["part_probability"] + values[c4]["part_probability"]
    part_difference = float(np.mean(high_part) - np.mean(low_part))
    part_difference_interval = _difference_interval(high_part, low_part)

    criteria = {
        "criterion_1": (
            summaries[c1]["mean_part_probability"] >= 0.95
            and summaries[c1]["mean_delta_i"] >= 0.15
        ),
        "criterion_2": (
            summaries[c2]["mean_danger_probability"] >= 0.60
            and summaries[c2]["mean_part_probability"] <= 0.05
            and summaries[c2]["mean_efficacy_probability"] >= 0.45
        ),
        "criterion_3": (
            summaries[c3]["mean_part_probability"] >= 0.95
            and summaries[c3]["mean_danger_probability"] <= 0.05
            and summaries[c3]["mean_delta_i"] >= 0.15
        ),
        "criterion_4": (
            summaries[c4]["mean_danger_probability"] >= 0.80
            and summaries[c4]["mean_part_probability"] <= 0.05
            and summaries[c4]["mean_efficacy_probability"] <= 0.35
        ),
        "criterion_5": part_difference_interval[0] > 0.80,
        "criterion_6": (
            max(
                value
                for cell in CELL_KEYS
                for value in values[cell]["normalization_error"]
            )
            <= 1e-10
            and sum(len(cell_records[key]) for key in CELL_KEYS) == 4000
            and [
                record["seed"]
                for key in CELL_KEYS
                for record in cell_records[key]
            ]
            == list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1))
        ),
    }
    verdict = "PASS" if all(criteria.values()) else "FAIL"
    summary = {
        "immutable_verdict": verdict,
        "criteria": criteria,
        "cell_summaries": summaries,
        "classification_separation": {
            "difference": part_difference,
            "whole_world_bootstrap_95_interval": part_difference_interval,
            "bootstrap_replicates": 2000,
        },
        "maximum_normalization_error": max(
            value
            for key in CELL_KEYS
            for value in values[key]["normalization_error"]
        ),
        "raw_trace_seal_sha256": raw_trace_seal_hash,
        "verdict_classes": {
            "scientific": all(criteria[f"criterion_{i}"] for i in range(1, 6)),
            "semantic": criteria["criterion_6"],
            "custody": criteria["criterion_6"],
        },
    }
    _write_json(RUN_DIR / "summary.json", summary)

    lines = [
        f"# C-V31 immutable sealed verdict: {verdict}",
        "",
        "The verdict above is the single sealed verdict and is retained as "
        "written.",
        "",
        "## Six sealed criteria",
        "",
    ]
    lines.extend(
        f"{index}. **{'PASS' if criteria[f'criterion_{index}'] else 'FAIL'}**"
        for index in range(1, 7)
    )
    lines.extend(
        [
            "",
            "## Cell results",
            "",
            "| cell | part | danger | efficacy | Delta_I |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    lines.extend(
        "| {cell} | {part:.6f} | {danger:.6f} | {efficacy:.6f} | {delta:.6f} |".format(
            cell=key,
            part=summaries[key]["mean_part_probability"],
            danger=summaries[key]["mean_danger_probability"],
            efficacy=summaries[key]["mean_efficacy_probability"],
            delta=summaries[key]["mean_delta_i"],
        )
        for key in CELL_KEYS
    )
    lines.extend(
        [
            "",
            "Classification separation (cells 1+3 minus 2+4): "
            f"`{part_difference:.6f}`, whole-world bootstrap 95% interval "
            f"`[{part_difference_interval[0]:.6f}, "
            f"{part_difference_interval[1]:.6f}]`.",
            "",
            "Maximum posterior-normalization error: "
            f"`{summary['maximum_normalization_error']:.3g}`.",
            "",
            "## Verdict classes",
            "",
            f"- Scientific: **{'PASS' if summary['verdict_classes']['scientific'] else 'FAIL'}**.",
            f"- Semantic: **{'PASS' if summary['verdict_classes']['semantic'] else 'FAIL'}**.",
            f"- Custody: **{'PASS' if summary['verdict_classes']['custody'] else 'FAIL'}**.",
            "",
            "All 4,000 seeds were consumed once, ascending and gap-free. "
            "Per-world traces and hashes were written before criteria. Raw "
            f"trace seal SHA-256: `{raw_trace_seal_hash}`.",
            "",
        ]
    )
    (RESULTS / "c-v31-verdict.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )

    if verdict == "PASS":
        (RESULTS / "stage-verdict.md").write_text(
            "# V3.1 stage verdict: PASS_WITH_ADJUDICATED_REVISABILITY_LIMITATION\n\n"
            "Gates 1–2 passed. Gate 3 retains its formal revisability-floor "
            "FAIL under the evaluator-authorized mixed-verdict continuation; "
            "all other Gate-3 criteria passed. Gate 4 passed under the "
            "restricted-prior lesion identity after preserving both earlier "
            "verdicts. Gate 5 passed. C-V31 passed all six sealed criteria, "
            "including scientific, semantic, and custody classes.\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
