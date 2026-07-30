#!/usr/bin/env python3
"""One-run C-V30 sealed grammar-kernel challenge runner."""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


V3_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = V3_ROOT.parents[2]
RESULTS = V3_ROOT / "results" / "V3.0"
RUN_RESULTS = RESULTS / "c-v30"
CHALLENGE = V3_ROOT / "sealed-revealed" / "C-V30-grammar-challenge.md"
MANIFEST = RESULTS / "freeze-manifest.json"
RELEASED_BLOCK = (4_000_000, 4_001_999)
RUN_MARKER = RUN_RESULTS / ".escrow-run-started"

sys.path.insert(0, str(V3_ROOT))

from ref import grammar  # noqa: E402


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): plain(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(child) for child in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(plain(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def parse_bundle() -> dict[str, Any]:
    text = CHALLENGE.read_text(encoding="utf-8")
    heading = "## Cells (parse instruction binding)"
    start_section = text.index(heading) + len(heading)
    start = text.index("{", start_section)
    end = text.index("\n\n## Criteria", start)
    literal = text[start:end]
    parsed = ast.literal_eval(literal)
    if not isinstance(parsed, dict):
        raise ValueError("sealed bracketed literal is not a dict")
    return parsed


def verify_manifest() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    errors = []
    for relative, expected in manifest["files"].items():
        path = V3_ROOT / relative
        actual = sha256_file(path)
        if actual != expected:
            errors.append(
                {"path": relative, "expected": expected, "actual": actual}
            )
    return {
        "manifest_path": str(MANIFEST.relative_to(V3_ROOT)),
        "declared_count": manifest["file_count"],
        "verified_count": len(manifest["files"]) - len(errors),
        "errors": errors,
        "pass": not errors and manifest["file_count"] == len(manifest["files"]),
    }


def cells(bundle: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    return [
        (name, value)
        for name, value in bundle.items()
        if name.startswith("cell_")
    ]


def validate_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    errors = []
    expected_start = RELEASED_BLOCK[0]
    generate_parameters = inspect.signature(grammar.generate_world).parameters
    for name, cell in cells(bundle):
        start, end = (int(value) for value in str(cell["escrow"]).split(":"))
        if start != expected_start:
            errors.append(f"{name}: escrow is not ascending gap-free")
        expected_start = end + 1
        if end - start + 1 != int(cell["n_worlds"]):
            errors.append(f"{name}: escrow size differs from n_worlds")
        structure_data = cell["structure"]
        try:
            structure = grammar.GrammarStructure(**structure_data)
        except Exception as error:
            errors.append(f"{name}: structure does not compile: {error}")
            continue
        if tuple(structure.edges) != tuple(structure_data["edges"]):
            errors.append(f"{name}: edge order changed")
        if any(scope not in grammar.SCOPES for scope in structure.scopes):
            errors.append(f"{name}: unsupported scope")
        if any(dynamics not in grammar.DYNAMICS for dynamics in structure.dynamics):
            errors.append(f"{name}: unsupported dynamics")
        for key in cell["world_kwargs"]:
            if key not in generate_parameters:
                errors.append(f"{name}: unsupported world keyword {key}")
    if expected_start - 1 != RELEASED_BLOCK[1]:
        errors.append("cell escrows do not exhaust the released block")
    return {
        "cell_count": len(cells(bundle)),
        "seed_count": sum(int(cell["n_worlds"]) for _, cell in cells(bundle)),
        "errors": errors,
        "pass": not errors,
    }


def field_supports(bounds: grammar.GrammarBounds) -> dict[str, tuple[Any, ...]]:
    supports: dict[str, tuple[Any, ...]] = {
        "active_modes": tuple(range(bounds.mode_slots + 1)),
        "active_contexts": tuple(range(1, bounds.context_slots + 1)),
    }
    supports.update({f"edge:{edge}": (0, 1) for edge in grammar.EDGES})
    supports.update(
        {f"scope:{block}": tuple(grammar.SCOPES) for block in grammar.BLOCKS}
    )
    supports.update(
        {
            f"dynamics:{block}": tuple(grammar.DYNAMICS)
            for block in grammar.BLOCKS
        }
    )
    return supports


def structure_values(structure: grammar.GrammarStructure) -> dict[str, Any]:
    values: dict[str, Any] = {
        "active_modes": structure.active_modes,
        "active_contexts": structure.active_contexts,
    }
    values.update(
        {f"edge:{edge}": value for edge, value in zip(grammar.EDGES, structure.edges)}
    )
    values.update(
        {
            f"scope:{block}": value
            for block, value in zip(grammar.BLOCKS, structure.scopes)
        }
    )
    values.update(
        {
            f"dynamics:{block}": value
            for block, value in zip(grammar.BLOCKS, structure.dynamics)
        }
    )
    return values


def oracle_code_length(field: str, value: Any) -> float:
    if field == "active_modes":
        return 1.0 + float(value)
    if field == "active_contexts":
        return float(value)
    if field.startswith("edge:"):
        return 1.0 + float(value)
    if field.startswith("scope:"):
        return 1.0 if value == "shared_global" else 3.0
    if field.startswith("dynamics:"):
        return 1.0 if value == "static" else 3.0
    raise KeyError(field)


def oracle_prior_probability(
    field: str, support: Sequence[Any], truth: Any
) -> float:
    weights = [2.0 ** (-oracle_code_length(field, value)) for value in support]
    return weights[support.index(truth)] / math.fsum(weights)


def independent_world_log_probability(world: grammar.GrammarWorld) -> float:
    """Fresh summation path sharing no scoring helper with ref/grammar.py."""
    supports = field_supports(world.bounds)
    truths = structure_values(world.structure)
    total = 0.0
    for field, support in supports.items():
        truth_index = support.index(truths[field])
        total += math.log(oracle_prior_probability(field, support, truths[field]))
        for observation in world.observations:
            if observation.field != field or observation.missing:
                continue
            if len(support) == 1:
                probability = 1.0
            elif observation.value == truth_index:
                probability = 0.86
            else:
                probability = 0.14 / (len(support) - 1)
            total += math.log(probability)
    return total


def trace_record(
    cell_name: str,
    world: grammar.GrammarWorld,
    posterior: grammar.StructurePosterior,
) -> dict[str, Any]:
    oracle_log_probability = independent_world_log_probability(world)
    local_log_probability = math.fsum(
        grammar.local_log_scores(world, world.structure).values()
    )
    dormant_checks = []
    for slot_kind, active, bound in (
        ("mode", world.structure.active_modes, world.bounds.mode_slots),
        ("context", world.structure.active_contexts, world.bounds.context_slots),
    ):
        for index in range(active + 1, bound + 1):
            dormant_checks.append(
                {
                    "slot_kind": slot_kind,
                    "slot_index": index,
                    "likelihood": grammar.dormant_slot_likelihood(
                        world, slot_kind, index
                    ),
                }
            )
    absent_edge_checks = []
    for edge, present in zip(grammar.EDGES, world.structure.edges):
        if present:
            continue
        probabilities = [
            grammar.edge_conditional_probability(False, parent, child)
            for parent in (0, 1)
            for child in (0, 1)
        ]
        absent_edge_checks.append(
            {
                "edge": edge,
                "probabilities": probabilities,
                "max_parent_difference": max(probabilities) - min(probabilities),
            }
        )
    return {
        "cell": cell_name,
        "seed": world.seed,
        "bounds": plain(world.bounds.__dict__),
        "structure": plain(world.structure.__dict__),
        "observations": [plain(observation.__dict__) for observation in world.observations],
        "interventions": list(world.interventions),
        "rng_keys": [list(key) for key in world.rng_keys],
        "world_exact_log_probability": world.exact_log_probability,
        "oracle_log_probability": oracle_log_probability,
        "local_log_probability": local_log_probability,
        "structure_posterior": {
            "supports": plain(posterior.supports),
            "field_probabilities": plain(posterior.field_probabilities),
            "log_evidence": posterior.log_evidence,
            "world_log_probability": posterior.world_log_probability,
        },
        "dormant_checks": dormant_checks,
        "absent_edge_checks": absent_edge_checks,
    }


def ece_10_bin(confidence: np.ndarray, correct: np.ndarray) -> float:
    error = 0.0
    for lower in np.linspace(0.0, 0.9, 10):
        upper = lower + 0.1
        mask = (confidence >= lower) & (
            confidence <= upper if np.isclose(upper, 1.0) else confidence < upper
        )
        if np.any(mask):
            error += float(mask.mean()) * abs(
                float(confidence[mask].mean()) - float(correct[mask].mean())
            )
    return error


def run_once() -> None:
    RUN_RESULTS.mkdir(parents=True, exist_ok=True)
    if RUN_MARKER.exists():
        raise RuntimeError("C-V30 one-run marker already exists")

    bundle = parse_bundle()
    manifest_audit = verify_manifest()
    expressibility = validate_bundle(bundle)
    preflight = {
        "challenge_sha256": sha256_file(CHALLENGE),
        "manifest_identity": manifest_audit,
        "expressibility": expressibility,
    }
    write_json(RUN_RESULTS / "preflight.json", preflight)
    if not manifest_audit["pass"] or not expressibility["pass"]:
        raise RuntimeError("STOP AS SEALED: identity or expressibility failure")

    RUN_MARKER.write_text(
        datetime.now(timezone.utc).isoformat() + "\n", encoding="utf-8"
    )
    phase_events = [
        {
            "phase": "escrow_run_started",
            "at": RUN_MARKER.read_text(encoding="utf-8").strip(),
        }
    ]
    raw_paths = []
    consumed_seeds = []
    for cell_name, cell in cells(bundle):
        start, end = (int(value) for value in str(cell["escrow"]).split(":"))
        structure = grammar.GrammarStructure(**cell["structure"])
        raw_path = RUN_RESULTS / f"{cell_name}-raw.jsonl"
        with raw_path.open("x", encoding="utf-8") as stream:
            for seed in range(start, end + 1):
                world = grammar.generate_world(
                    seed,
                    structure=structure,
                    released_block=RELEASED_BLOCK,
                    **cell["world_kwargs"],
                )
                posterior = grammar.score_world(world)
                stream.write(
                    canonical_json(trace_record(cell_name, world, posterior)) + "\n"
                )
                consumed_seeds.append(seed)
        raw_paths.append(raw_path)

    trace_hashes = {
        path.name: {"sha256": sha256_file(path), "bytes": path.stat().st_size}
        for path in raw_paths
    }
    trace_seal = {
        "sealed_before_criteria": True,
        "sealed_at": datetime.now(timezone.utc).isoformat(),
        "record_count": len(consumed_seeds),
        "files": trace_hashes,
    }
    write_json(RUN_RESULTS / "raw-traces-sha256.json", trace_seal)
    phase_events.append(
        {"phase": "raw_traces_hashed", "at": trace_seal["sealed_at"]}
    )

    # Criteria evaluation begins only after the immutable raw-trace hash file exists.
    all_cell_results = {}
    all_records = []
    for raw_path in raw_paths:
        records = [
            json.loads(line)
            for line in raw_path.read_text(encoding="utf-8").splitlines()
        ]
        all_records.extend(records)
        correct = []
        confidence = []
        for record in records:
            truths = structure_values(
                grammar.GrammarStructure(**record["structure"])
            )
            posterior = record["structure_posterior"]
            for field, truth in truths.items():
                support = posterior["supports"][field]
                probabilities = posterior["field_probabilities"][field]
                predicted_index = int(np.argmax(probabilities))
                correct.append(support[predicted_index] == truth)
                confidence.append(probabilities[predicted_index])
        result = {
            "cell": records[0]["cell"],
            "world_count": len(records),
            "first_seed": records[0]["seed"],
            "last_seed": records[-1]["seed"],
            "structure_field_accuracy": float(np.mean(correct)),
            "ece_10_bin": ece_10_bin(
                np.asarray(confidence), np.asarray(correct, dtype=float)
            ),
            "max_oracle_log_probability_error": max(
                abs(
                    record["world_exact_log_probability"]
                    - record["oracle_log_probability"]
                )
                for record in records
            ),
            "max_local_recombination_error": max(
                abs(
                    record["world_exact_log_probability"]
                    - record["local_log_probability"]
                )
                for record in records
            ),
            "max_dormant_likelihood_error": max(
                (
                    abs(check["likelihood"] - 1.0)
                    for record in records
                    for check in record["dormant_checks"]
                ),
                default=0.0,
            ),
            "max_absent_edge_independence_error": max(
                (
                    check["max_parent_difference"]
                    for record in records
                    for check in record["absent_edge_checks"]
                ),
                default=0.0,
            ),
        }
        all_cell_results[result["cell"]] = result
        write_json(RUN_RESULTS / f"{result['cell']}-results.json", result)

    exact_sequence = consumed_seeds == list(
        range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)
    )
    criterion_1 = all(
        result["world_count"] == 500 for result in all_cell_results.values()
    ) and len(all_records) == 2_000
    criterion_2 = all(
        result["max_oracle_log_probability_error"] <= 1e-10
        and result["max_local_recombination_error"] <= 1e-10
        for result in all_cell_results.values()
    )
    criterion_3 = all(
        result["structure_field_accuracy"] >= 0.979
        and result["ece_10_bin"] <= 0.03
        for result in all_cell_results.values()
    )
    criterion_4 = all(
        result["max_dormant_likelihood_error"] <= 1e-10
        and result["max_absent_edge_independence_error"] <= 1e-10
        for result in all_cell_results.values()
    )
    criterion_5 = (
        exact_sequence
        and len(set(consumed_seeds)) == 2_000
        and trace_seal["sealed_before_criteria"]
        and manifest_audit["pass"]
        and expressibility["pass"]
    )
    criteria = {
        "criterion_1_compile_sample_score": criterion_1,
        "criterion_2_exact_probability": criterion_2,
        "criterion_3_structure_recovery": criterion_3,
        "criterion_4_semantics": criterion_4,
        "criterion_5_custody": criterion_5,
    }
    verdict = "PASS" if all(criteria.values()) else "FAIL"
    phase_events.append(
        {
            "phase": "criteria_evaluated",
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
    ledger = {
        "challenge": "C-V30",
        "release_authority": {
            "released_block": list(RELEASED_BLOCK),
            "purpose": "C-V30 sealed challenge",
            "authorization": "evaluator release accompanying revealed seal fdc8b516",
        },
        "challenge_sha256": preflight["challenge_sha256"],
        "freeze_manifest": manifest_audit,
        "seed_count": len(consumed_seeds),
        "unique_seed_count": len(set(consumed_seeds)),
        "first_seed": consumed_seeds[0],
        "last_seed": consumed_seeds[-1],
        "ascending_gap_free": exact_sequence,
        "raw_trace_seal": trace_seal,
        "phase_events": phase_events,
    }
    write_json(RUN_RESULTS / "run-ledger.json", ledger)
    write_json(
        RUN_RESULTS / "criteria.json",
        {
            "immutable_verdict": verdict,
            "criteria": criteria,
            "cells": all_cell_results,
        },
    )

    report_lines = [
        f"# C-V30 immutable sealed verdict: {verdict}",
        "",
        "The verdict above is the sealed-written result. Pass requires all five criteria.",
        "",
        "## Criteria",
        "",
    ]
    for index, (name, passed) in enumerate(criteria.items(), start=1):
        report_lines.append(
            f"{index}. **{'PASS' if passed else 'FAIL'}** — `{name}`."
        )
    report_lines.extend(
        [
            "",
            "## Verdict classes",
            "",
            f"- Scientific-apparatus: {'PASS' if all((criterion_1, criterion_2, criterion_3)) else 'FAIL'}.",
            f"- Semantic: {'PASS' if criterion_4 else 'FAIL'}.",
            f"- Custody: {'PASS' if criterion_5 else 'FAIL'}.",
            "",
            "## Cell results",
            "",
        ]
    )
    for name, result in all_cell_results.items():
        report_lines.append(
            f"- `{name}`: accuracy {result['structure_field_accuracy']:.6f}; "
            f"ECE {result['ece_10_bin']:.6f}; oracle error "
            f"{result['max_oracle_log_probability_error']:.3e}; local error "
            f"{result['max_local_recombination_error']:.3e}."
        )
    report_lines.extend(
        [
            "",
            "Raw traces were hashed before criterion aggregation. All 2,000 escrow seeds",
            "were consumed once, ascending and gap-free. Frozen source identity was",
            f"{manifest_audit['verified_count']}/{manifest_audit['declared_count']}.",
            "",
        ]
    )
    (RESULTS / "c-v30-verdict.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )

    if verdict == "PASS":
        (RESULTS / "stage-verdict.md").write_text(
            "# V3.0 stage verdict: PASS\n\n"
            "V3.0 passed public Gates 1–5, including the authorized Gate-5 "
            "verification repair with the original FAIL retained, and passed "
            "the one-run sealed C-V30 apparatus challenge across all five "
            "criteria. The exact grammar kernel is closed and V3.1 is "
            "unblocked.\n",
            encoding="utf-8",
        )


def preflight_only() -> None:
    bundle = parse_bundle()
    result = {
        "challenge_sha256": sha256_file(CHALLENGE),
        "manifest_identity": verify_manifest(),
        "expressibility": validate_bundle(bundle),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["manifest_identity"]["pass"] or not result["expressibility"]["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {"preflight", "run"}:
        raise SystemExit("usage: run_c_v30.py {preflight|run}")
    if sys.argv[1] == "preflight":
        preflight_only()
    else:
        run_once()
