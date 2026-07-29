#!/usr/bin/env python3
"""One-shot frozen V2.8 sealed challenge runner."""
from __future__ import annotations

import argparse
import ast
import concurrent.futures
import dataclasses
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ref import v232_formation, v28


RESULTS = ROOT / "results" / "V2.8"
MANIFEST = RESULTS / "freeze-manifest.json"
BOOTSTRAPS = 10_000

FILES = {
    "A": ("C-V28A-challenge.md", (2_100_000, 2_100_599)),
    "B": ("C-V28B-challenge.md", (2_110_000, 2_110_599)),
    "C": ("C-V28C-challenge.md", (2_120_000, 2_120_599)),
    "D": ("C-V28D-challenge.md", (2_130_000, 2_130_599)),
}


def plain(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return plain(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(item) for item in value]
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    return value


def dump(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(plain(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n"
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_literal(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    marker = text.index("## Bundle")
    start = text.index("{", marker)
    end_marker = "\n\nCommon custody:"
    end = text.index(end_marker, start)
    literal = text[start:end]
    if not literal.startswith("{") or not literal.endswith("}"):
        raise ValueError("bundle is not one exact bracketed literal")
    value = ast.literal_eval(literal)
    if not isinstance(value, dict):
        raise ValueError("bundle literal is not a dict")
    return value


def verify_identity() -> dict[str, Any]:
    payload = json.loads(MANIFEST.read_text())
    mismatches = []
    for relative, expected in payload["files"].items():
        path = ROOT / relative
        observed = sha256(path) if path.exists() else None
        if observed != expected:
            mismatches.append(
                {"file": relative, "expected": expected, "observed": observed}
            )
    return {
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "manifest_sha256": sha256(MANIFEST),
        "checked_files": len(payload["files"]),
        "mismatches": mismatches,
        "passed": not mismatches,
    }


def validate(code: str, bundle: dict[str, Any]) -> dict[str, Any]:
    fields = set(v28.TrajectoryProfile.__dataclass_fields__)
    protocols = tuple(bundle["arms"])
    strata = (
        tuple(bundle["stratum_pair"])
        if "stratum_pair" in bundle
        else (bundle["stratum"],)
    )
    checks = {
        "arms_public": all(item in v28.PROTOCOLS for item in protocols),
        "strata_public": all(item in v28.STRATA for item in strata),
        "released_block_public": "released_block"
        in v28.run_trajectory.__annotations__
        or "released_block"
        in __import__("inspect").signature(v28.run_trajectory).parameters,
        "required_common_fields": {
            "material_redescription",
            "material_reduction",
            "untreated_transfer",
            "protector_trust_update",
            "historical_context_error",
            "historical_index_available",
            "first_times",
        }.issubset(fields),
    }
    reason = None
    if code == "D":
        retained = json.loads(
            (RESULTS / "gate-3-per-protocol.json").read_text()
        )
        published_keys = {
            key
            for row in retained
            for key, _ in row.get("first_times", [])
        }
        checks["redescription_first_time_public"] = (
            "redescription" in published_keys
            or "redescription_first_time" in fields
        )
        if not checks["redescription_first_time_public"]:
            reason = (
                "sealed criterion requires redescription-before-reduction "
                "from first_times, but the frozen public readout publishes no "
                "redescription first time"
            )
    return {
        "checks": checks,
        "expressible": all(checks.values()),
        "prospection_failure": reason,
    }


def profile(state: v28.DevelopmentalState, seed: int, arm: str, block: tuple[int, int]) -> dict[str, Any]:
    return plain(
        v28.run_trajectory(
            state,
            seed,
            protocol=arm,
            released_block=block,
        )
    )


def single_world(task: tuple[int, str, tuple[str, ...], tuple[int, int]]) -> dict[str, Any]:
    seed, stratum, arms, block = task
    state = v28.generate_developmental_state(
        seed, stratum, released_block=block
    )
    qualified = v28.qualifies(state)
    return {
        "seed": seed,
        "stratum": stratum,
        "qualified": qualified,
        "state_sha256": state.state_sha256,
        "truth_candidate": state.truth_candidate,
        "protector_count": state.protector_count,
        "q_formation": state.q_formation.tolist(),
        "arms": (
            {arm: profile(state, seed, arm, block) for arm in arms}
            if qualified
            else {}
        ),
    }


def cross_world(task: tuple[int, tuple[str, str], tuple[str, ...], tuple[int, int]]) -> dict[str, Any]:
    seed, strata, arms, block = task
    worlds = {}
    for stratum in strata:
        state = v28.generate_developmental_state(
            seed, stratum, released_block=block
        )
        qualified = v28.qualifies(state)
        worlds[stratum] = {
            "qualified": qualified,
            "state_sha256": state.state_sha256,
            "truth_candidate": state.truth_candidate,
            "protector_count": state.protector_count,
            "q_formation": state.q_formation.tolist(),
            "arms": (
                {arm: profile(state, seed, arm, block) for arm in arms}
                if qualified
                else {}
            ),
        }
    return {"seed": seed, "worlds": worlds}


def ci(values: list[float], seed: int) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = np.empty(BOOTSTRAPS)
    for index in range(BOOTSTRAPS):
        means[index] = float(
            np.mean(array[rng.integers(0, len(array), len(array))])
        )
    return {
        "n": len(values),
        "mean": float(np.mean(array)),
        "lower_95": float(np.quantile(means, .025)),
        "upper_95": float(np.quantile(means, .975)),
    }


def rate(rows: list[dict[str, Any]], arm: str, field: str) -> float:
    return float(np.mean([bool(row["arms"][arm][field]) for row in rows]))


def mean(rows: list[dict[str, Any]], arm: str, field: str) -> float:
    return float(np.mean([float(row["arms"][arm][field]) for row in rows]))


def exact_history(rows: list[dict[str, Any]], arms: tuple[str, ...]) -> bool:
    return all(
        abs(float(row["arms"][arm]["historical_context_error"])) <= 1e-10
        for row in rows
        for arm in arms
    )


def evaluate_a(rows: list[dict[str, Any]]) -> dict[str, Any]:
    q = [row for row in rows if row["qualified"]]
    rupture = ci(
        [
            row["arms"]["bypass_protectors"]["rupture_return"]
            - row["arms"]["full"]["rupture_return"]
            for row in q
        ],
        2_100_901,
    )
    metrics = {
        "qualifying_count": len(q),
        "qualifying_rate": len(q) / len(rows),
        "full_contact_rate": rate(q, "full", "contact"),
        "full_material_redescription": rate(q, "full", "material_redescription"),
        "full_material_reduction": rate(q, "full", "material_reduction"),
        "full_untreated_transfer": mean(q, "full", "untreated_transfer"),
        "full_trust_update": mean(q, "full", "protector_trust_update"),
        "full_successful_sequence": rate(q, "full", "successful_sequence"),
        "cue_material_redescription": rate(q, "cue_exposure", "material_redescription"),
        "cue_untreated_transfer": mean(q, "cue_exposure", "untreated_transfer"),
        "cue_trust_update": mean(q, "cue_exposure", "protector_trust_update"),
        "bypass_material_reduction": rate(q, "bypass_protectors", "material_reduction"),
        "bypass_trust_update": mean(q, "bypass_protectors", "protector_trust_update"),
        "bypass_minus_full_rupture": rupture,
        "regulation_contact": rate(q, "regulation_only", "contact"),
        "regulation_material_redescription": rate(q, "regulation_only", "material_redescription"),
        "regulation_untreated_transfer": mean(q, "regulation_only", "untreated_transfer"),
        "maximum_historical_error": max(
            abs(float(row["arms"][arm]["historical_context_error"]))
            for row in q for arm in FILE_ARMS["A"]
        ),
    }
    checks = {
        "qualifying_population": len(q) > 0,
        "full_contact_min_0.80": metrics["full_contact_rate"] >= .80,
        "full_redescription_min_0.85": metrics["full_material_redescription"] >= .85,
        "full_reduction_min_0.80": metrics["full_material_reduction"] >= .80,
        "full_transfer_min_0.20": metrics["full_untreated_transfer"] >= .20,
        "full_trust_positive": metrics["full_trust_update"] > 0,
        "full_sequence_min_0.70": metrics["full_successful_sequence"] >= .70,
        "cue_redescription_max_0.10": metrics["cue_material_redescription"] <= .10,
        "cue_transfer_max_0.05": metrics["cue_untreated_transfer"] <= .05,
        "cue_trust_negative": metrics["cue_trust_update"] < 0,
        "bypass_reduction_max_0.10": metrics["bypass_material_reduction"] <= .10,
        "bypass_trust_max_0.05": metrics["bypass_trust_update"] <= .05,
        "bypass_rupture_lower_ci_gt_0.10": rupture["lower_95"] > .10,
        "regulation_contact_max_0.10": metrics["regulation_contact"] <= .10,
        "regulation_redescription_max_0.10": metrics["regulation_material_redescription"] <= .10,
        "regulation_transfer_max_0.05": metrics["regulation_untreated_transfer"] <= .05,
        "historical_error_max_1e-10": exact_history(q, FILE_ARMS["A"]),
    }
    return {"metrics": metrics, "checks": checks}


def evaluate_b(rows: list[dict[str, Any]]) -> dict[str, Any]:
    q = [row for row in rows if row["qualified"]]
    transfer = ci(
        [
            row["arms"]["full"]["untreated_transfer"]
            - row["arms"]["unreliable_partner"]["untreated_transfer"]
            for row in q
        ],
        2_110_901,
    )
    metrics = {
        "qualifying_count": len(q),
        "qualifying_rate": len(q) / len(rows),
        "full_sequence": rate(q, "full", "successful_sequence"),
        "full_reduction": rate(q, "full", "material_reduction"),
        "full_trust": mean(q, "full", "protector_trust_update"),
        "full_depth": mean(q, "full", "depth_increase"),
        "unreliable_trust": mean(q, "unreliable_partner", "protector_trust_update"),
        "unreliable_depth": mean(q, "unreliable_partner", "depth_increase"),
        "unreliable_sequence": rate(q, "unreliable_partner", "successful_sequence"),
        "full_minus_unreliable_transfer": transfer,
        "maximum_historical_error": max(
            abs(float(row["arms"][arm]["historical_context_error"]))
            for row in q for arm in FILE_ARMS["B"]
        ),
    }
    checks = {
        "qualifying_population": len(q) > 0,
        "full_sequence_min_0.70": metrics["full_sequence"] >= .70,
        "full_reduction_min_0.70": metrics["full_reduction"] >= .70,
        "full_trust_positive": metrics["full_trust"] > 0,
        "full_depth_min_0.30": metrics["full_depth"] >= .30,
        "unreliable_trust_negative": metrics["unreliable_trust"] < 0,
        "unreliable_depth_max_0": metrics["unreliable_depth"] <= 0,
        "unreliable_sequence_max_0.10": metrics["unreliable_sequence"] <= .10,
        "transfer_gap_lower_ci_gt_0.10": transfer["lower_95"] > .10,
        "historical_error_max_1e-10": exact_history(q, FILE_ARMS["B"]),
    }
    return {"metrics": metrics, "checks": checks}


def evaluate_c(rows: list[dict[str, Any]]) -> dict[str, Any]:
    danger = [
        {"seed": row["seed"], **row["worlds"]["real_danger_adaptive"]}
        for row in rows if row["worlds"]["real_danger_adaptive"]["qualified"]
    ]
    burden = [
        {"seed": row["seed"], **row["worlds"]["chronic_one"]}
        for row in rows if row["worlds"]["chronic_one"]["qualified"]
    ]
    paired = [
        row for row in rows
        if row["worlds"]["real_danger_adaptive"]["qualified"]
        and row["worlds"]["chronic_one"]["qualified"]
    ]
    d_index = v232_formation.LABELS.index("D")
    p_index = v232_formation.LABELS.index("P")
    separation = ci(
        [
            0.5 * (
                (
                    row["worlds"]["real_danger_adaptive"]["q_formation"][d_index]
                    - row["worlds"]["real_danger_adaptive"]["q_formation"][p_index]
                )
                + (
                    row["worlds"]["chronic_one"]["q_formation"][p_index]
                    - row["worlds"]["chronic_one"]["q_formation"][d_index]
                )
            )
            for row in paired
        ],
        2_120_901,
    )
    metrics = {
        "danger_qualifying_count": len(danger),
        "burden_qualifying_count": len(burden),
        "paired_qualifying_count": len(paired),
        "danger_mean_q_D": float(np.mean([row["q_formation"][d_index] for row in danger])),
        "burden_mean_q_P": float(np.mean([row["q_formation"][p_index] for row in burden])),
        "danger_mean_policy_shift": mean(danger, "full", "protector_policy_shift"),
        "paired_truth_contrast_separation": separation,
        "maximum_historical_error": max(
            abs(float(row["arms"]["full"]["historical_context_error"]))
            for row in danger + burden
        ),
    }
    checks = {
        "danger_qualifying_population": len(danger) > 0,
        "burden_qualifying_population": len(burden) > 0,
        "danger_q_D_min_0.90": metrics["danger_mean_q_D"] >= .90,
        "burden_q_P_min_0.95": metrics["burden_mean_q_P"] >= .95,
        "danger_policy_shift_min_0.15": metrics["danger_mean_policy_shift"] >= .15,
        "historical_error_max_1e-10": metrics["maximum_historical_error"] <= 1e-10,
        "historical_index_available": all(
            row["arms"]["full"]["historical_index_available"]
            for row in danger + burden
        ),
        "paired_separation_lower_ci_gt_0.80": separation["lower_95"] > .80,
    }
    return {"metrics": metrics, "checks": checks}


FILE_ARMS = {
    "A": ("full", "regulation_only", "cue_exposure", "bypass_protectors"),
    "B": ("full", "unreliable_partner"),
    "C": ("full",),
    "D": ("full", "premature_do_over"),
}


def stop_as_sealed(
    code: str,
    bundle: dict[str, Any],
    identity: dict[str, Any],
    validation: dict[str, Any],
    challenge_path: Path,
) -> None:
    prefix = f"c-v28{code.lower()}"
    per_world = RESULTS / f"{prefix}-per-world.json"
    dump(per_world, [])
    seal = {
        "status": "STOP_AS_SEALED",
        "raw_trace_sha256": sha256(per_world),
        "raw_trace_records": 0,
        "criteria_evaluated": False,
    }
    dump(RESULTS / f"{prefix}-raw-trace-seal.json", seal)
    ledger = {
        "challenge": f"C-V28{code}",
        "bundle_sha256": sha256(challenge_path),
        "release_block": list(FILES[code][1]),
        "seeds_consumed": 0,
        "ascending_gap_free": True,
        "identity": identity,
        "validation": validation,
    }
    dump(RESULTS / f"{prefix}-ledger.json", ledger)
    (RESULTS / f"{prefix}-verdict.md").write_text(
        f"# C-V28{code} immutable sealed verdict\n\n"
        "## Immutable verdict: STOP_AS_SEALED\n\n"
        f"Prospection failure: {validation['prospection_failure']}.\n\n"
        "## Verdict classes\n\n"
        "- Scientific: NOT EVALUATED.\n"
        "- Semantic: FAIL — a sealed-required quantity is absent from the frozen public API.\n"
        "- Custody: PASS — zero escrow seeds were consumed and no frozen source changed.\n"
    )


def run(code: str) -> None:
    filename, block = FILES[code]
    challenge_path = ROOT / "sealed-revealed" / filename
    bundle = parse_literal(challenge_path)
    identity = verify_identity()
    validation = validate(code, bundle)
    if not identity["passed"]:
        validation = {
            **validation,
            "expressible": False,
            "prospection_failure": "frozen manifest identity check failed",
        }
    if not validation["expressible"]:
        stop_as_sealed(
            code, bundle, identity, validation, challenge_path
        )
        print(f"C-V28{code}: STOP_AS_SEALED")
        return

    seeds = list(range(block[0], block[1] + 1))
    arms = tuple(bundle["arms"])
    if code == "C":
        strata = tuple(bundle["stratum_pair"])
        tasks = [(seed, strata, arms, block) for seed in seeds]
        worker = cross_world
    else:
        stratum = bundle["stratum"]
        tasks = [(seed, stratum, arms, block) for seed in seeds]
        worker = single_world
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        rows = list(executor.map(worker, tasks))
    if [row["seed"] for row in rows] != seeds:
        raise RuntimeError("seed order is not ascending and gap-free")

    prefix = f"c-v28{code.lower()}"
    per_world = RESULTS / f"{prefix}-per-world.json"
    dump(per_world, rows)
    seal = {
        "status": "SEALED_BEFORE_CRITERIA",
        "raw_trace_sha256": sha256(per_world),
        "raw_trace_records": len(rows),
        "first_seed": seeds[0],
        "last_seed": seeds[-1],
    }
    seal_path = RESULTS / f"{prefix}-raw-trace-seal.json"
    dump(seal_path, seal)

    # Criterion evaluation starts only after the immutable raw file and its
    # hash record exist. Re-read the sealed bytes rather than using memory.
    sealed_rows = json.loads(per_world.read_text())
    evaluation = (
        evaluate_a(sealed_rows)
        if code == "A"
        else evaluate_b(sealed_rows)
        if code == "B"
        else evaluate_c(sealed_rows)
    )
    scientific = all(evaluation["checks"].values())
    semantic = identity["passed"] and validation["expressible"]
    custody = (
        len(sealed_rows) == 600
        and [row["seed"] for row in sealed_rows] == seeds
        and sha256(per_world) == seal["raw_trace_sha256"]
    )
    verdict = "PASS" if scientific and semantic and custody else "FAIL"
    summary = {
        "challenge": f"C-V28{code}",
        "immutable_verdict": verdict,
        "scientific_passed": scientific,
        "semantic_passed": semantic,
        "custody_passed": custody,
        **evaluation,
    }
    dump(RESULTS / f"{prefix}-summary.json", summary)
    ledger = {
        "challenge": f"C-V28{code}",
        "bundle_sha256": sha256(challenge_path),
        "literal_parser": "ast.literal_eval",
        "release_block": list(block),
        "release_consumed_in_full": True,
        "seeds_consumed": 600,
        "ascending_gap_free": True,
        "same_seed_arms": True,
        "identity": identity,
        "validation": validation,
        "raw_trace_seal_sha256": sha256(seal_path),
        "raw_trace_sha256": seal["raw_trace_sha256"],
    }
    dump(RESULTS / f"{prefix}-ledger.json", ledger)
    failed = [
        name for name, passed in evaluation["checks"].items() if not passed
    ]
    lines = [
        f"# C-V28{code} immutable sealed verdict",
        "",
        f"## Immutable verdict: {verdict}",
        "",
        f"Scientific criteria: {sum(evaluation['checks'].values())}/{len(evaluation['checks'])}.",
    ]
    if failed:
        lines += ["", "Failures retained verbatim:", ""]
        lines += [f"- `{name}`" for name in failed]
    lines += [
        "",
        "## Metrics",
        "",
        "```json",
        json.dumps(plain(evaluation["metrics"]), indent=2, sort_keys=True),
        "```",
        "",
        "## Verdict classes",
        "",
        f"- Scientific: {'PASS' if scientific else 'FAIL'}.",
        f"- Semantic: {'PASS' if semantic else 'FAIL'}.",
        f"- Custody: {'PASS' if custody else 'FAIL'} — raw traces were hashed before criterion evaluation.",
        "",
    ]
    (RESULTS / f"{prefix}-verdict.md").write_text("\n".join(lines))
    print(f"C-V28{code}: {verdict}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", choices=tuple(FILES))
    args = parser.parse_args()
    run(args.bundle)


if __name__ == "__main__":
    main()
