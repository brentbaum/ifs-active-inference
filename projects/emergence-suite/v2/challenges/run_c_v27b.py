#!/usr/bin/env python3
"""One-shot sealed C-V27-B executor with same-seed Cell-4 pairing."""

from __future__ import annotations

import ast
import concurrent.futures
import dataclasses
import hashlib
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "V2.7"
CHALLENGE = ROOT / "sealed-revealed" / "C-V27B-multiprotector-challenge.md"
MANIFEST = OUT / "freeze-manifest.json"
RELEASED_BLOCK = (2_065_000, 2_069_599)
EXPECTED_CHALLENGE_HASH = (
    "a6ba705baab940a3d830236fd17e28f6063ed003322f3281d10ca27d3aa3b60e"
)

sys.path.insert(0, str(ROOT))
from challenges import run_c_v27 as base  # noqa: E402
from ref import constitution, v27  # noqa: E402

# Reuse only the already-public challenge custody serialization helpers. These
# are challenge-side utilities, not scientific source.
base.RELEASED_BLOCK = RELEASED_BLOCK


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_literal() -> dict[str, Any]:
    text = CHALLENGE.read_text(encoding="utf-8")
    start = text.index("{'parse_instruction'")
    end = text.index("\n\n## Criteria", start)
    return ast.literal_eval(text[start:end])


def validate_frozen_identity() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in manifest["files"].items():
        path = ROOT / relative
        observed = sha256(path) if path.exists() else None
        if observed != expected:
            mismatches.append(
                {
                    "file": relative,
                    "expected": expected,
                    "observed": observed,
                }
            )
    return {
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "declared_files": len(manifest["files"]),
        "mismatches": mismatches,
        "passed": not mismatches,
    }


def validate_schema(bundle: dict[str, Any]) -> dict[str, Any]:
    expected = {
        "cell_1_novel_topology": (2_065_000, 2_065_999, 1_000),
        "cell_2_mandate": (2_066_000, 2_066_799, 800),
        "cell_3_coalition": (2_066_800, 2_067_599, 800),
        "cell_4_registration_contrast": (2_067_600, 2_067_999, 400),
        "cell_5_befriending": (2_068_000, 2_068_799, 800),
        "cell_6_exiling_and_descent": (2_068_800, 2_069_599, 800),
    }
    generators = {
        "generate_recovery_world": v27.generate_recovery_world,
        "generate_control_world": v27.generate_control_world,
    }
    fields = {field.name for field in dataclasses.fields(v27.MultiProtectorScore)}
    requested = (
        "q_topology",
        "q_mandate",
        "exiling_mass",
        "system_access",
        "descent",
        "registration_support",
        "q_joint_policy",
    )
    errors = [f"missing score field {name}" for name in requested if name not in fields]
    for name, (start, end, count) in expected.items():
        cell = bundle.get(name)
        if cell is None:
            errors.append(f"missing {name}")
            continue
        if cell["escrow"] != f"{start}:{end}" or cell["n_worlds"] != count:
            errors.append(f"{name} range/count mismatch")
        generator = generators.get(cell["generator"])
        if generator is None:
            errors.append(f"{name} unknown generator")
            continue
        signature = inspect.signature(generator)
        configurations = cell.get("kwargs_pair", [cell.get("kwargs", {})])
        for configuration in configurations:
            for key in configuration:
                if key not in signature.parameters:
                    errors.append(f"{name} inexpressible kwarg {key}")
        if "released_block" not in signature.parameters:
            errors.append(f"{name} lacks released_block")
    assignment = bundle["cell_4_registration_contrast"].get("assignment", "")
    if "SAME-SEED PAIRED" not in assignment:
        errors.append("cell 4 lacks binding same-seed assignment")
    return {
        "requested_readouts": list(requested),
        "unique_seed_count": 4_600,
        "protocol_arm_count": 5_000,
        "errors": errors,
        "passed": not errors,
    }


def cell_specs(bundle: dict[str, Any]) -> list[tuple[str, int, int, dict[str, Any]]]:
    result = []
    for name, cell in bundle.items():
        if name.startswith("cell_"):
            start, end = map(int, cell["escrow"].split(":"))
            result.append((name, start, end, cell))
    return result


def build_tasks(bundle: dict[str, Any]) -> tuple[list[tuple[Any, ...]], list[int]]:
    tasks = []
    consumed = []
    for name, start, end, cell in cell_specs(bundle):
        if end - start + 1 != cell["n_worlds"]:
            raise ValueError(f"{name}: non-gap-free range")
        for seed in range(start, end + 1):
            consumed.append(seed)
            index = seed - start
            if name == "cell_4_registration_contrast":
                # The base trace constructor selects a pair row by index mod 2.
                # Giving it 2*i and 2*i+1 yields two arms with one shared pair ID.
                tasks.append((name, seed, 2 * index, cell))
                tasks.append((name, seed, 2 * index + 1, cell))
            else:
                tasks.append((name, seed, index, cell))
    if consumed != list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)):
        raise ValueError("unique seed consumption not ascending and gap-free")
    return tasks, consumed


def execute_all(
    bundle: dict[str, Any],
) -> tuple[dict[str, list[dict[str, Any]]], list[int]]:
    tasks, consumed = build_tasks(bundle)
    workers = min(int(os.environ.get("V2_WORKERS", "10")), os.cpu_count() or 1)
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
            traces = list(pool.map(base.make_trace, tasks, chunksize=25))
    except PermissionError:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            traces = list(pool.map(base.make_trace, tasks))
    by_cell = {name: [] for name, _, _, _ in cell_specs(bundle)}
    for trace in traces:
        by_cell[trace["cell"]].append(trace)
    return by_cell, consumed


def seal_raw_traces(
    by_cell: dict[str, list[dict[str, Any]]],
    consumed: list[int],
    identity: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    files = {}
    for cell, traces in by_cell.items():
        path = OUT / f"c-v27b-{cell.replace('_', '-')}-raw.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for trace in traces:
                handle.write(base.canonical(trace) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        files[str(path.relative_to(ROOT))] = {
            "sha256": sha256(path),
            "protocol_arm_records": len(traces),
            "unique_seeds": len({trace["seed"] for trace in traces}),
            "first_seed": traces[0]["seed"],
            "last_seed": traces[-1]["seed"],
        }
    seal = {
        "challenge": "C-V27-B",
        "challenge_sha256": sha256(CHALLENGE),
        "freeze_identity": identity,
        "schema_validation": schema,
        "released_block": list(RELEASED_BLOCK),
        "unique_seed_count": len(consumed),
        "protocol_arm_count": sum(
            item["protocol_arm_records"] for item in files.values()
        ),
        "ascending_gap_free_unique_seeds": consumed
        == list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)),
        "cell_4_same_seed_two_arm_design": True,
        "criteria_evaluated_at_seal_time": False,
        "files": files,
    }
    path = OUT / "c-v27b-raw-traces-seal.json"
    path.write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n")
    with path.open("r+") as handle:
        handle.flush()
        os.fsync(handle.fileno())
    return seal


def evaluate(
    bundle: dict[str, Any],
    by_cell: dict[str, list[dict[str, Any]]],
    consumed: list[int],
    seal: dict[str, Any],
) -> dict[str, Any]:
    # Criteria 1-6 are literally unchanged. Point the public C-V27 evaluator
    # at the fresh hash/block, then replace only its custody census to reflect
    # 4,600 unique seeds and 5,000 scored protocol arms.
    base.EXPECTED_CHALLENGE_HASH = EXPECTED_CHALLENGE_HASH
    base.RELEASED_BLOCK = RELEASED_BLOCK
    verdict = base.evaluate(bundle, by_cell, seal)
    source = (ROOT / "ref" / "v27.py").read_text(encoding="utf-8")
    forbidden_source = {
        "polarization_coefficient": "polarization_coefficient" in source,
        "exile_force": "exile_force" in source,
        "gate_object": "class Gate" in source,
    }
    forbidden_state = {"polarized", "exiled", "registered", "gate", "access"}
    state_violations = []
    for traces in by_cell.values():
        for trace in traces:
            state = trace["scientific_state"]
            keys = (
                set(state["posterior_store"])
                | set(state["parameter_posterior_store"])
                | set(state["evidence_store"])
            )
            overlap = sorted(keys & forbidden_state)
            if overlap:
                state_violations.append({"seed": trace["seed"], "fields": overlap})
    constitution_result = constitution.cumulative_constitution_audit()
    semantic = {
        "forbidden_source": forbidden_source,
        "scientific_state_violations": state_violations,
        "constitution_passed": constitution_result["passed"],
        "one_posterior_audited_protocol_arms": 5_000,
        "freeze_identity_passed": seal["freeze_identity"]["passed"],
        "challenge_hash_verified": seal["challenge_sha256"]
        == EXPECTED_CHALLENGE_HASH,
        "released_by": (
            "suite-v2-sealed-hashes.md C-V27-B record, commit 1abfae2"
        ),
        "unique_seed_count": len(consumed),
        "protocol_arm_count": sum(len(traces) for traces in by_cell.values()),
        "ascending_gap_free_unique_seeds": consumed
        == list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)),
        "cell_4_same_seed_pairs": len(
            {
                trace["pair_id"]
                for trace in by_cell["cell_4_registration_contrast"]
            }
        ),
    }
    semantic["passed"] = (
        not any(forbidden_source.values())
        and not state_violations
        and constitution_result["passed"]
        and seal["freeze_identity"]["passed"]
        and seal["challenge_sha256"] == EXPECTED_CHALLENGE_HASH
        and len(consumed) == 4_600
        and sum(len(traces) for traces in by_cell.values()) == 5_000
        and semantic["ascending_gap_free_unique_seeds"]
        and semantic["cell_4_same_seed_pairs"] == 400
    )
    verdict["challenge"] = "C-V27-B"
    verdict["criteria"]["criterion_7_semantic_custody"] = semantic
    verdict["passed"] = all(
        item["passed"] for item in verdict["criteria"].values()
    )
    verdict["immutable_verdict"] = "PASS" if verdict["passed"] else "FAIL"
    return verdict


def write_cell_results(
    by_cell: dict[str, list[dict[str, Any]]],
    seal: dict[str, Any],
    verdict: dict[str, Any],
) -> None:
    criteria_by_cell = {
        "cell_1_novel_topology": "criterion_1_topology",
        "cell_2_mandate": "criterion_2_mandate",
        "cell_3_coalition": "criterion_3_coalition",
        "cell_4_registration_contrast": "criterion_4_registration",
        "cell_5_befriending": "criterion_5_befriending",
        "cell_6_exiling_and_descent": "criterion_6_exiling_descent",
    }
    for cell, traces in by_cell.items():
        raw_name = f"results/V2.7/c-v27b-{cell.replace('_', '-')}-raw.jsonl"
        payload = {
            "challenge": "C-V27-B",
            "cell": cell,
            "protocol_arm_count": len(traces),
            "unique_seed_count": len({trace["seed"] for trace in traces}),
            "seed_range": [traces[0]["seed"], traces[-1]["seed"]],
            "same_seed_paired": cell == "cell_4_registration_contrast",
            "raw_trace_file": raw_name,
            "raw_trace_sha256": seal["files"][raw_name]["sha256"],
            "criterion": verdict["criteria"][criteria_by_cell[cell]],
            "per_world_readouts": [
                {
                    "seed": trace["seed"],
                    "pair_id": trace["pair_id"],
                    "pair_assignment": trace["pair_assignment"],
                    "truth": trace["truth"],
                    "readouts": trace["readouts"],
                    "world_sha256": trace["world_sha256"],
                    "scientific_state_sha256": trace[
                        "scientific_state_sha256"
                    ],
                }
                for trace in traces
            ],
        }
        (OUT / f"c-v27b-{cell.replace('_', '-')}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n"
        )


def write_reports(
    verdict: dict[str, Any],
    seal: dict[str, Any],
    suite: subprocess.CompletedProcess[str],
) -> None:
    ledger = {
        "challenge": "C-V27-B",
        "challenge_sha256": seal["challenge_sha256"],
        "release_id": "C-V27-B release record",
        "authorization_commit": "1abfae2",
        "released_block": list(RELEASED_BLOCK),
        "unique_seeds_consumed_once": True,
        "unique_seed_count": 4_600,
        "protocol_arm_count": 5_000,
        "cell_4_same_seed_pair_count": 400,
        "ascending_gap_free": True,
        "raw_traces_sealed_before_criteria": True,
        "raw_trace_seal": "results/V2.7/c-v27b-raw-traces-seal.json",
        "freeze_identity": seal["freeze_identity"],
        "full_fast_suite": {
            "command": "python3 run_tests_parallel.py",
            "returncode": suite.returncode,
            "passed": suite.returncode == 0,
            "stdout": suite.stdout,
            "stderr": suite.stderr,
        },
    }
    (OUT / "c-v27b-run-ledger.json").write_text(
        json.dumps(ledger, indent=2, sort_keys=True) + "\n"
    )
    lines = [
        "# C-V27-B immutable sealed verdict",
        "",
        f"Immutable verdict: **{verdict['immutable_verdict']}**.",
        "",
        "Raw traces were sealed and hashed before criterion evaluation.",
        "",
        "## Sealed criteria",
        "",
    ]
    for name, result in verdict["criteria"].items():
        details = {key: value for key, value in result.items() if key != "passed"}
        lines.append(
            f"- `{name}`: **{'PASS' if result['passed'] else 'FAIL'}** — "
            f"`{json.dumps(base.plain(details), sort_keys=True)}`"
        )
    scientific = all(
        verdict["criteria"][name]["passed"]
        for name in (
            "criterion_1_topology",
            "criterion_2_mandate",
            "criterion_3_coalition",
            "criterion_4_registration",
            "criterion_5_befriending",
            "criterion_6_exiling_descent",
        )
    )
    semantic = verdict["criteria"]["criterion_7_semantic_custody"]["passed"]
    lines += [
        "",
        "## Verdict classes",
        "",
        f"- Scientific: **{'PASS' if scientific else 'FAIL'}**.",
        f"- Semantic: **{'PASS' if semantic else 'FAIL'}**.",
        "- Distributional stress: reported per cell without pooling.",
        f"- Process custody: **{'PASS' if semantic and suite.returncode == 0 else 'FAIL'}**.",
        "",
        f"Full fast suite: **{'PASS' if suite.returncode == 0 else 'FAIL'}**.",
        "",
        f"Named bounds: `{json.dumps(verdict['bounds'], sort_keys=True)}`.",
    ]
    (OUT / "c-v27b-verdict.md").write_text("\n".join(lines) + "\n")
    (OUT / "c-v27b-summary.json").write_text(
        json.dumps(verdict, indent=2, sort_keys=True) + "\n"
    )
    if verdict["passed"]:
        (OUT / "stage-verdict.md").write_text(
            "# V2.7 stage verdict\n\n"
            "Disposition: **PASS_AFTER_PAIRING_CORRECTED_SEALED_CHALLENGE**.\n\n"
            "The open stage passed Gates 1–5 on the repaired instrument. C-V27 "
            "is retained as FAIL because its registration identity compared "
            "different seeds. C-V27-B corrected only that pairing on fresh "
            "escrow and passed all seven sealed criteria. This is the single "
            "V2.7 stage disposition; both seal outcomes remain immutable.\n"
        )
    names = (
        "cell_1_novel_topology",
        "cell_2_mandate",
        "cell_3_coalition",
        "cell_4_registration_contrast",
        "cell_5_befriending",
        "cell_6_exiling_and_descent",
    )
    files = [
        "challenges/run_c_v27b.py",
        "results/V2.7/c-v27b-raw-traces-seal.json",
        "results/V2.7/c-v27b-run-ledger.json",
        "results/V2.7/c-v27b-summary.json",
        "results/V2.7/c-v27b-verdict.md",
    ]
    files += [
        f"results/V2.7/c-v27b-{name.replace('_', '-')}.json"
        for name in names
    ]
    files += [
        f"results/V2.7/c-v27b-{name.replace('_', '-')}-raw.jsonl"
        for name in names
    ]
    if verdict["passed"]:
        files.append("results/V2.7/stage-verdict.md")
    files.append("results/V2.7/ready-to-commit-c-v27b.md")
    (OUT / "ready-to-commit-c-v27b.md").write_text(
        "# C-V27-B ready-to-commit list\n\n"
        + "\n".join(f"- `{item}`" for item in files)
        + "\n"
    )


def stop_as_sealed(reason: str, details: Any) -> int:
    payload = {
        "challenge": "C-V27-B",
        "immutable_verdict": "STOP_AS_SEALED",
        "reason": reason,
        "details": base.plain(details),
        "unique_seeds_consumed": 0,
        "criteria_evaluated": False,
    }
    (OUT / "c-v27b-verdict.md").write_text(
        "# C-V27-B immutable sealed verdict\n\n"
        "**STOP_AS_SEALED** before seed consumption or criterion evaluation.\n\n"
        f"Reason: `{reason}`.\n"
    )
    (OUT / "c-v27b-stop.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    return 2


def main() -> int:
    observed_hash = sha256(CHALLENGE)
    if observed_hash != EXPECTED_CHALLENGE_HASH:
        return stop_as_sealed("challenge hash mismatch", observed_hash)
    bundle = parse_literal()
    identity = validate_frozen_identity()
    if not identity["passed"]:
        return stop_as_sealed("frozen identity mismatch", identity)
    schema = validate_schema(bundle)
    if not schema["passed"]:
        return stop_as_sealed("prospection failure", schema)

    by_cell, consumed = execute_all(bundle)
    seal = seal_raw_traces(by_cell, consumed, identity, schema)
    verdict = evaluate(bundle, by_cell, consumed, seal)
    write_cell_results(by_cell, seal, verdict)
    suite = subprocess.run(
        [sys.executable, "run_tests_parallel.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    write_reports(verdict, seal, suite)
    print(verdict["immutable_verdict"])
    return 0 if verdict["passed"] and suite.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
