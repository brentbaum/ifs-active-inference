#!/usr/bin/env python3
"""One-shot sealed C-V27 executor; no frozen scientific source changes."""

from __future__ import annotations

import ast
import concurrent.futures
import dataclasses
import hashlib
import inspect
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "V2.7"
CHALLENGE = ROOT / "sealed-revealed" / "C-V27-multiprotector-challenge.md"
MANIFEST = OUT / "freeze-manifest.json"
RELEASED_BLOCK = (2_060_000, 2_064_999)
EXPECTED_CHALLENGE_HASH = (
    "2b68bd3f39d2add80ac89ce6f54b779af1083b5e0e64dd227383391ff875593f"
)
TOLERANCE = 1e-10

sys.path.insert(0, str(ROOT))
from ref import constitution, v27  # noqa: E402
from ref.audit import audit_one_posterior  # noqa: E402


def plain(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return plain(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, bytes):
        return {"hex": value.hex()}
    return value


def canonical(value: Any) -> str:
    return json.dumps(
        plain(value),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_literal() -> dict[str, Any]:
    text = CHALLENGE.read_text(encoding="utf-8")
    start = text.index("{'parse_instruction'")
    end = text.index("\n\n## Criteria", start)
    # Binding instruction: exactly one ast.literal_eval on the bracketed text.
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
    errors = []
    expected_cells = {
        "cell_1_novel_topology": (2_060_000, 2_060_999, 1_000),
        "cell_2_mandate": (2_061_000, 2_061_799, 800),
        "cell_3_coalition": (2_061_800, 2_062_599, 800),
        "cell_4_registration_contrast": (2_062_600, 2_063_399, 800),
        "cell_5_befriending": (2_063_400, 2_064_199, 800),
        "cell_6_exiling_and_descent": (2_064_200, 2_064_999, 800),
    }
    generators = {
        "generate_recovery_world": v27.generate_recovery_world,
        "generate_control_world": v27.generate_control_world,
    }
    requested_readouts = (
        "q_topology",
        "q_mandate",
        "exiling_mass",
        "system_access",
        "descent",
        "registration_support",
        "q_joint_policy",
    )
    score_fields = {item.name for item in dataclasses.fields(v27.MultiProtectorScore)}
    for field in requested_readouts:
        if field not in score_fields:
            errors.append(f"missing score field {field}")
    for name, (start, end, count) in expected_cells.items():
        cell = bundle.get(name)
        if cell is None:
            errors.append(f"missing {name}")
            continue
        if cell["escrow"] != f"{start}:{end}" or cell["n_worlds"] != count:
            errors.append(f"{name} range/count mismatch")
        function = generators.get(cell["generator"])
        if function is None:
            errors.append(f"{name} unknown generator")
            continue
        signature = inspect.signature(function)
        if "released_block" not in signature.parameters:
            errors.append(f"{name} lacks released_block")
        configurations = (
            cell.get("kwargs_pair")
            if "kwargs_pair" in cell
            else [cell["kwargs"]]
        )
        for configuration in configurations:
            for key in configuration:
                if key not in signature.parameters:
                    errors.append(f"{name} inexpressible kwarg {key}")
    return {
        "requested_readouts": list(requested_readouts),
        "errors": errors,
        "passed": not errors,
    }


def cell_specs(bundle: dict[str, Any]) -> list[tuple[str, int, int, dict[str, Any]]]:
    result = []
    for name, cell in bundle.items():
        if not name.startswith("cell_"):
            continue
        start_text, end_text = cell["escrow"].split(":")
        result.append((name, int(start_text), int(end_text), cell))
    return result


def make_trace(task: tuple[str, int, int, dict[str, Any]]) -> dict[str, Any]:
    cell_name, seed, index, cell = task
    assignment = None
    if "kwargs_pair" in cell:
        assignment = index % 2
        kwargs = dict(cell["kwargs_pair"][assignment])
    else:
        kwargs = dict(cell["kwargs"])
    generator = getattr(v27, cell["generator"])
    world = generator(
        seed,
        released_block=RELEASED_BLOCK,
        **kwargs,
    )
    score = v27.score_world(world)
    audit_one_posterior(score.state)
    world_payload = plain(world)
    state_payload = {
        "posterior_store": plain(score.state.posterior_store),
        "parameter_posterior_store": plain(
            score.state.parameter_posterior_store
        ),
        "evidence_store": plain(score.state.evidence_store),
        "metadata": plain(dict(score.state.metadata)),
    }
    return {
        "cell": cell_name,
        "seed": seed,
        "cell_index": index,
        "pair_id": index // 2 if "kwargs_pair" in cell else None,
        "pair_assignment": assignment,
        "generator": cell["generator"],
        "kwargs": kwargs,
        "released_block": list(RELEASED_BLOCK),
        "truth": {
            "protector_count": world.protector_count,
            "topology_index": world.topology_index,
            "mandate_index": world.mandate_index,
            "outcome_level_index": world.outcome_level_index,
            "scenario": world.scenario,
        },
        "world": world_payload,
        "world_sha256": hashlib.sha256(
            canonical(world_payload).encode("utf-8")
        ).hexdigest(),
        "readouts": {
            "q_topology": plain(score.q_topology),
            "q_mandate": plain(score.q_mandate),
            "q_outcome_level": plain(score.q_outcome_level),
            "q_joint_policy": plain(score.q_joint_policy),
            "joint_policies": plain(score.joint_policies),
            "exiling_mass": score.exiling_mass,
            "system_access": score.system_access,
            "descent": score.descent,
            "registration_support": score.registration_support,
        },
        "scientific_state": state_payload,
        "scientific_state_sha256": hashlib.sha256(
            canonical(state_payload).encode("utf-8")
        ).hexdigest(),
    }


def execute_all(bundle: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    tasks = []
    for name, start, end, cell in cell_specs(bundle):
        if end - start + 1 != cell["n_worlds"]:
            raise ValueError(f"{name}: non-gap-free declared range")
        tasks.extend(
            (name, seed, seed - start, cell)
            for seed in range(start, end + 1)
        )
    seeds = [task[1] for task in tasks]
    if seeds != list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)):
        raise ValueError("escrow consumption is not ascending and gap-free")
    workers = min(int(os.environ.get("V2_WORKERS", "10")), os.cpu_count() or 1)
    try:
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
            traces = list(pool.map(make_trace, tasks, chunksize=25))
    except PermissionError:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            traces = list(pool.map(make_trace, tasks))
    by_cell: dict[str, list[dict[str, Any]]] = {
        name: [] for name, _, _, _ in cell_specs(bundle)
    }
    for trace in traces:
        by_cell[trace["cell"]].append(trace)
    return by_cell


def seal_raw_traces(
    by_cell: dict[str, list[dict[str, Any]]],
    identity: dict[str, Any],
    schema: dict[str, Any],
) -> dict[str, Any]:
    files = {}
    for cell, traces in by_cell.items():
        path = OUT / f"c-v27-{cell.replace('_', '-')}-raw.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for trace in traces:
                handle.write(canonical(trace) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        files[str(path.relative_to(ROOT))] = {
            "sha256": sha256(path),
            "records": len(traces),
            "first_seed": traces[0]["seed"],
            "last_seed": traces[-1]["seed"],
        }
    seal = {
        "challenge": "C-V27",
        "challenge_sha256": sha256(CHALLENGE),
        "freeze_identity": identity,
        "schema_validation": schema,
        "released_block": list(RELEASED_BLOCK),
        "seed_count": sum(item["records"] for item in files.values()),
        "ascending_gap_free": True,
        "criteria_evaluated_at_seal_time": False,
        "files": files,
    }
    path = OUT / "c-v27-raw-traces-seal.json"
    path.write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n")
    with path.open("r+") as handle:
        handle.flush()
        os.fsync(handle.fileno())
    return seal


def interval(values: Iterable[float]) -> dict[str, float]:
    array = np.asarray(tuple(values), dtype=float)
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
        "count": len(array),
    }


def difference_interval(
    left: Sequence[float], right: Sequence[float], *, paired: bool
) -> dict[str, float]:
    a = np.asarray(left, dtype=float)
    b = np.asarray(right, dtype=float)
    if paired:
        return interval(a - b)
    difference = float(a.mean() - b.mean())
    standard_error = math.sqrt(
        float(a.var(ddof=1)) / len(a) + float(b.var(ddof=1)) / len(b)
    )
    return {
        "mean": difference,
        "lower_95": difference - 1.96 * standard_error,
        "upper_95": difference + 1.96 * standard_error,
        "left_count": len(a),
        "right_count": len(b),
    }


def split_pair(
    traces: Sequence[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    left = [trace for trace in traces if trace["pair_assignment"] == 0]
    right = [trace for trace in traces if trace["pair_assignment"] == 1]
    if [item["pair_id"] for item in left] != [item["pair_id"] for item in right]:
        raise ValueError("paired cell pair IDs do not align")
    return left, right


def evaluate(
    bundle: dict[str, Any],
    by_cell: dict[str, list[dict[str, Any]]],
    seal: dict[str, Any],
) -> dict[str, Any]:
    c1 = by_cell["cell_1_novel_topology"]
    c2 = by_cell["cell_2_mandate"]
    c3 = by_cell["cell_3_coalition"]
    c4_on, c4_off = split_pair(by_cell["cell_4_registration_contrast"])
    c5_both, c5_none = split_pair(by_cell["cell_5_befriending"])
    c6_exile, c6_permit = split_pair(by_cell["cell_6_exiling_and_descent"])

    topology_rate = float(
        np.mean(
            [
                int(np.argmax(trace["readouts"]["q_topology"]))
                == trace["truth"]["topology_index"]
                for trace in c1
            ]
        )
    )
    topology_normalization = max(
        abs(sum(trace["readouts"]["q_topology"]) - 1.0) for trace in c1
    )
    mandate_rate = float(
        np.mean(
            [
                int(np.argmax(trace["readouts"]["q_mandate"]))
                == trace["truth"]["mandate_index"]
                for trace in c2
            ]
        )
    )
    coalition_exiling = interval(
        trace["readouts"]["exiling_mass"] for trace in c3
    )
    coalition_access_advantage = difference_interval(
        [trace["readouts"]["system_access"] for trace in c3],
        [trace["readouts"]["system_access"] for trace in c6_exile],
        paired=False,
    )
    registration_difference = difference_interval(
        [trace["readouts"]["registration_support"] for trace in c4_on],
        [trace["readouts"]["registration_support"] for trace in c4_off],
        paired=True,
    )
    registration_access_identity = max(
        abs(
            left["readouts"]["system_access"]
            - right["readouts"]["system_access"]
        )
        for left, right in zip(c4_on, c4_off)
    )
    registration_descent_identity = max(
        abs(left["readouts"]["descent"] - right["readouts"]["descent"])
        for left, right in zip(c4_on, c4_off)
    )
    befriend_access = difference_interval(
        [trace["readouts"]["system_access"] for trace in c5_both],
        [trace["readouts"]["system_access"] for trace in c5_none],
        paired=True,
    )
    befriend_exiling_both = interval(
        trace["readouts"]["exiling_mass"] for trace in c5_both
    )
    befriend_exiling_none = interval(
        trace["readouts"]["exiling_mass"] for trace in c5_none
    )
    exile_mass = interval(
        trace["readouts"]["exiling_mass"] for trace in c6_exile
    )
    exile_access = interval(
        trace["readouts"]["system_access"] for trace in c6_exile
    )
    permit_descent = interval(
        trace["readouts"]["descent"] for trace in c6_permit
    )
    permit_access = interval(
        trace["readouts"]["system_access"] for trace in c6_permit
    )
    access_difference = difference_interval(
        [trace["readouts"]["system_access"] for trace in c6_permit],
        [trace["readouts"]["system_access"] for trace in c6_exile],
        paired=True,
    )

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
                state_violations.append(
                    {"seed": trace["seed"], "fields": overlap}
                )
    constitution_result = constitution.cumulative_constitution_audit()
    consumed = [
        trace["seed"]
        for name, _, _, _ in cell_specs(bundle)
        for trace in by_cell[name]
    ]

    criteria = {
        "criterion_1_topology": {
            "topology_recovery": topology_rate,
            "normalization_max_error": topology_normalization,
            "passed": topology_rate >= 0.70 and topology_normalization <= TOLERANCE,
        },
        "criterion_2_mandate": {
            "mandate_recovery": mandate_rate,
            "passed": mandate_rate >= 0.80,
        },
        "criterion_3_coalition": {
            "exiling_mass": coalition_exiling,
            "access_minus_exiling_arm": coalition_access_advantage,
            "passed": (
                0.30 <= coalition_exiling["mean"] <= 0.65
                and coalition_access_advantage["lower_95"] > 0.10
            ),
        },
        "criterion_4_registration": {
            "support_on_minus_off": registration_difference,
            "matched_access_max_error": registration_access_identity,
            "matched_descent_max_error": registration_descent_identity,
            "passed": (
                registration_difference["mean"] >= 0.40
                and registration_access_identity <= TOLERANCE
                and registration_descent_identity <= TOLERANCE
            ),
        },
        "criterion_5_befriending": {
            "access_both_minus_none": befriend_access,
            "exiling_both": befriend_exiling_both,
            "exiling_none": befriend_exiling_none,
            "passed": (
                befriend_access["lower_95"] > 0.03
                and befriend_exiling_both["mean"] <= 0.05
                and befriend_exiling_none["mean"] <= 0.05
            ),
        },
        "criterion_6_exiling_descent": {
            "exiling_arm_mass": exile_mass,
            "exiling_arm_access": exile_access,
            "permit_arm_descent": permit_descent,
            "permit_arm_access": permit_access,
            "permit_minus_exiling_access": access_difference,
            "passed": (
                exile_mass["mean"] >= 0.90
                and exile_access["mean"] <= 0.05
                and permit_descent["mean"] >= 0.70
                and permit_access["mean"] >= 0.80
                and access_difference["lower_95"] > 0.60
            ),
        },
        "criterion_7_semantic_custody": {
            "forbidden_source": forbidden_source,
            "scientific_state_violations": state_violations,
            "constitution_passed": constitution_result["passed"],
            "one_posterior_audited_worlds": 5_000,
            "freeze_identity_passed": seal["freeze_identity"]["passed"],
            "challenge_hash_verified": (
                seal["challenge_sha256"] == EXPECTED_CHALLENGE_HASH
            ),
            "released_by": (
                "suite-v2-sealed-hashes.md C-V27 record, commit c8c1063"
            ),
            "consumed_count": len(consumed),
            "ascending_gap_free": consumed == list(
                range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)
            ),
            "passed": (
                not any(forbidden_source.values())
                and not state_violations
                and constitution_result["passed"]
                and seal["freeze_identity"]["passed"]
                and seal["challenge_sha256"] == EXPECTED_CHALLENGE_HASH
                and len(consumed) == 5_000
                and consumed
                == list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1))
            ),
        },
    }
    passed = all(item["passed"] for item in criteria.values())
    return {
        "challenge": "C-V27",
        "immutable_verdict": "PASS" if passed else "FAIL",
        "passed": passed,
        "criteria": criteria,
        "bounds": {
            "B_max_v232_formation": 3.801426508560692,
            "B_max_v24_common_emissions": 6.704414354964107,
            **v27.finite_information_bounds(),
        },
    }


def write_cell_results(
    by_cell: dict[str, list[dict[str, Any]]],
    seal: dict[str, Any],
    verdict: dict[str, Any],
) -> None:
    criteria_by_cell = {
        "cell_1_novel_topology": ["criterion_1_topology"],
        "cell_2_mandate": ["criterion_2_mandate"],
        "cell_3_coalition": ["criterion_3_coalition"],
        "cell_4_registration_contrast": ["criterion_4_registration"],
        "cell_5_befriending": ["criterion_5_befriending"],
        "cell_6_exiling_and_descent": ["criterion_6_exiling_descent"],
    }
    for cell, traces in by_cell.items():
        raw_name = f"results/V2.7/c-v27-{cell.replace('_', '-')}-raw.jsonl"
        payload = {
            "challenge": "C-V27",
            "cell": cell,
            "world_count": len(traces),
            "seed_range": [traces[0]["seed"], traces[-1]["seed"]],
            "raw_trace_file": raw_name,
            "raw_trace_sha256": seal["files"][raw_name]["sha256"],
            "criteria": {
                name: verdict["criteria"][name]
                for name in criteria_by_cell[cell]
            },
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
        (OUT / f"c-v27-{cell.replace('_', '-')}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n"
        )


def write_reports(
    verdict: dict[str, Any],
    seal: dict[str, Any],
    suite: subprocess.CompletedProcess[str],
) -> None:
    ledger = {
        "challenge": "C-V27",
        "challenge_sha256": seal["challenge_sha256"],
        "release_id": "C-V27 release record",
        "authorization_commit": "c8c1063",
        "released_block": list(RELEASED_BLOCK),
        "consumed_once": True,
        "ascending_gap_free": True,
        "seed_count": 5_000,
        "raw_traces_sealed_before_criteria": True,
        "raw_trace_seal": "results/V2.7/c-v27-raw-traces-seal.json",
        "freeze_identity": seal["freeze_identity"],
        "full_fast_suite": {
            "command": "python3 run_tests_parallel.py",
            "returncode": suite.returncode,
            "passed": suite.returncode == 0,
            "stdout": suite.stdout,
            "stderr": suite.stderr,
        },
    }
    (OUT / "c-v27-run-ledger.json").write_text(
        json.dumps(ledger, indent=2, sort_keys=True) + "\n"
    )
    lines = [
        "# C-V27 immutable sealed verdict",
        "",
        f"Immutable verdict: **{verdict['immutable_verdict']}**.",
        "",
        "The raw traces were sealed and hashed before any criterion was evaluated.",
        "",
        "## Sealed criteria",
        "",
    ]
    for name, result in verdict["criteria"].items():
        details = {key: value for key, value in result.items() if key != "passed"}
        lines.append(
            f"- `{name}`: **{'PASS' if result['passed'] else 'FAIL'}** — "
            f"`{json.dumps(plain(details), sort_keys=True)}`"
        )
    scientific = all(
        verdict["criteria"][f"criterion_{index}_{suffix}"]["passed"]
        for index, suffix in (
            (1, "topology"),
            (2, "mandate"),
            (3, "coalition"),
            (4, "registration"),
            (5, "befriending"),
            (6, "exiling_descent"),
        )
    )
    semantic = verdict["criteria"]["criterion_7_semantic_custody"]["passed"]
    lines += [
        "",
        "## Verdict classes",
        "",
        f"- Scientific: **{'PASS' if scientific else 'FAIL'}**.",
        f"- Semantic: **{'PASS' if semantic else 'FAIL'}**.",
        "- Distributional stress: reported cell-by-cell in the immutable criteria; no pooled replacement.",
        f"- Process custody: **{'PASS' if semantic and suite.returncode == 0 else 'FAIL'}**.",
        "",
        f"Full fast suite: **{'PASS' if suite.returncode == 0 else 'FAIL'}**.",
        "",
        f"Named bounds: `{json.dumps(verdict['bounds'], sort_keys=True)}`.",
    ]
    (OUT / "c-v27-verdict.md").write_text("\n".join(lines) + "\n")
    (OUT / "c-v27-summary.json").write_text(
        json.dumps(verdict, indent=2, sort_keys=True) + "\n"
    )
    if verdict["passed"]:
        (OUT / "stage-verdict.md").write_text(
            "# V2.7 stage verdict\n\n"
            "Disposition: **PASS**.\n\n"
            "V2.7 passed Gates 1–5 on the repaired instrument and passed C-V27 "
            "all seven sealed criteria. The original Gate-4 software-error "
            "FAIL remains retained beside the authorized repaired execution.\n"
        )
    ready_files = [
        "challenges/run_c_v27.py",
        "results/V2.7/c-v27-raw-traces-seal.json",
        "results/V2.7/c-v27-run-ledger.json",
        "results/V2.7/c-v27-summary.json",
        "results/V2.7/c-v27-verdict.md",
    ]
    ready_files.extend(
        f"results/V2.7/c-v27-{name.replace('_', '-')}.json"
        for name in (
            "cell_1_novel_topology",
            "cell_2_mandate",
            "cell_3_coalition",
            "cell_4_registration_contrast",
            "cell_5_befriending",
            "cell_6_exiling_and_descent",
        )
    )
    ready_files.extend(
        f"results/V2.7/c-v27-{name.replace('_', '-')}-raw.jsonl"
        for name in (
            "cell_1_novel_topology",
            "cell_2_mandate",
            "cell_3_coalition",
            "cell_4_registration_contrast",
            "cell_5_befriending",
            "cell_6_exiling_and_descent",
        )
    )
    if verdict["passed"]:
        ready_files.append("results/V2.7/stage-verdict.md")
    (OUT / "ready-to-commit-c-v27.md").write_text(
        "# C-V27 ready-to-commit list\n\n"
        + "\n".join(f"- `{item}`" for item in ready_files)
        + "\n"
    )


def stop_as_sealed(reason: str, details: Any) -> int:
    payload = {
        "challenge": "C-V27",
        "immutable_verdict": "STOP_AS_SEALED",
        "reason": reason,
        "details": plain(details),
        "seeds_consumed": 0,
        "criteria_evaluated": False,
    }
    (OUT / "c-v27-verdict.md").write_text(
        "# C-V27 immutable sealed verdict\n\n"
        "**STOP_AS_SEALED** before seed consumption or criterion evaluation.\n\n"
        f"Reason: `{reason}`.\n"
    )
    (OUT / "c-v27-stop.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    return 2


def main() -> int:
    if sha256(CHALLENGE) != EXPECTED_CHALLENGE_HASH:
        return stop_as_sealed("challenge hash mismatch", sha256(CHALLENGE))
    bundle = parse_literal()
    identity = validate_frozen_identity()
    if not identity["passed"]:
        return stop_as_sealed("frozen identity mismatch", identity)
    schema = validate_schema(bundle)
    if not schema["passed"]:
        return stop_as_sealed("prospection failure", schema)

    # Single escrow execution begins here. No criterion code is called until
    # every trace file and the raw-trace seal are durable.
    by_cell = execute_all(bundle)
    seal = seal_raw_traces(by_cell, identity, schema)
    verdict = evaluate(bundle, by_cell, seal)
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
