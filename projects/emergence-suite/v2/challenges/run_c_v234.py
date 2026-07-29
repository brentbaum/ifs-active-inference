#!/usr/bin/env python3
"""One-run C-V234 sealed counterfactual-attribution challenge runner."""

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
from typing import Any, Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from ref import constitution, v234  # noqa: E402
from ref.audit import audit_one_posterior  # noqa: E402
from run_v234_gates import known_config_prior  # noqa: E402


CHALLENGE = ROOT / "sealed-revealed" / "C-V234-attribution-challenge.md"
SEAL_LEDGER = REPO_ROOT / "projects" / "ifs-paper" / "suite-v2-sealed-hashes.md"
OUT = ROOT / "results" / "V2.3.4"
CHALLENGE_ID = "C-V234"
FILE_STEM = "c-v234"
RELEASED_BLOCK = (2_040_000, 2_041_999)
VERIFIED_SEAL = "1d9329bafd15fdc5e2c987bb4fa9105146d8740f05fefdd675f1fab61764cdd7"
RELEASE_PHRASE = (
    "Escrow: C-V234 seeds 2040000:2041999, released by this record "
    "via the frozen released_block parameter."
)
CELL2_NO_FALSE_FLOOR = 0.90
CELL3_EXISTENCE_FLOOR = 0.60
STAGE_PASS_TEXT = (
    "V2.3.4 entered Gate 6 with the clean `FROZEN_ALL_GATES_PASS` "
    "base: Gates 1–5 passed without an adjudicated limitation. "
    "C-V234 then passed all seven sealed criteria. The single stage "
    "disposition therefore licenses the counterfactual-attribution "
    "claim: the construction distinguishes low danger from danger "
    "successfully prevented by action, while action remains an "
    "intervention and relief remains policy-only."
)
CELL_FILES = {
    "cell_1_effective_action": "c-v234-cell-1.json",
    "cell_2_sham_action": "c-v234-cell-2.json",
    "cell_3_partial": "c-v234-cell-3.json",
    "cell_4_context_switch": "c-v234-cell-4.json",
    "cell_5_forced_probe": "c-v234-cell-5.json",
    "cell_6_relief_only": "c-v234-cell-6.json",
}
TOL = v234.TOLERANCE


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
    literals = [
        line for line in lines if line.startswith("{") and line.endswith("}")
    ]
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
    errors: list[str] = []
    cells = [key for key in bundle if key.startswith("cell_")]
    seeds: list[int] = []
    generators = {
        "generate_controlled_world": v234.generate_controlled_world,
        "generate_world": v234.generate_world,
    }
    for cell_name in cells:
        cell = bundle[cell_name]
        start, end = parse_escrow(cell["escrow"])
        if end - start + 1 != int(cell["n_worlds"]):
            errors.append(f"{cell_name}: escrow count mismatch")
        seeds.extend(range(start, end + 1))
        generator = generators.get(cell["generator"])
        if generator is None:
            errors.append(f"{cell_name}: generator is not public")
            continue
        permitted = set(inspect.signature(generator).parameters) - {
            "seed",
            "released_block",
        }
        unknown = sorted(set(cell["kwargs"]) - permitted)
        if unknown:
            errors.append(f"{cell_name}: unknown kwargs {unknown}")
    if cells != list(CELL_FILES):
        errors.append("cell order differs from sealed order")
    if seeds != list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)):
        errors.append("escrow ranges are not ascending and gap-free")
    freeze = verify_freeze()
    if not freeze["passed"]:
        errors.append("frozen V2.3.4 identity failed")
    challenge_hash = sha256(CHALLENGE)
    if challenge_hash != VERIFIED_SEAL:
        errors.append("challenge hash differs from verified seal")
    ledger_text = SEAL_LEDGER.read_text(encoding="utf-8")
    release_phrase = RELEASE_PHRASE
    if release_phrase not in ledger_text:
        errors.append(f"{CHALLENGE_ID} release ledger phrase absent")
    return {
        "challenge": CHALLENGE_ID,
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


def entropy(probabilities: Iterable[float]) -> float:
    values = np.asarray(tuple(probabilities), dtype=float)
    positive = values[values > 0.0]
    return float(-np.sum(positive * np.log(positive)))


def episode_record(item: v234.Episode) -> dict[str, Any]:
    return {
        "action": item.action,
        "context": item.context,
        "outcome": item.outcome,
        "near_miss": item.near_miss,
        "efficacy_observation": item.efficacy_observation,
        "relief": item.relief,
    }


def score_record(result: v234.AttributionScore) -> dict[str, Any]:
    audit_one_posterior(result.state)
    return {
        "posterior": result.posterior,
        "posterior_entropy": entropy(result.posterior),
        "threat_probability": result.threat_probability,
        "efficacy_causal_probability": result.efficacy_causal_probability,
        "eta_mean": result.eta_mean,
        "theta_eta_correlation": result.theta_eta_correlation,
        "prevented_probability_K": result.prevented_probability_K,
        "policy_probability": result.policy_probability,
        "formation_probability": result.formation_probability,
        "log_evidence": result.log_evidence,
        "one_posterior_audit": True,
    }


def recombined_k(
    episodes: tuple[v234.Episode, ...],
    result: v234.AttributionScore,
) -> list[float]:
    values = []
    for prior, episode in zip(result.trajectory[:-1], episodes):
        likelihood, conditional_k = v234.slice_likelihood(episode)
        evidence = float(prior @ likelihood)
        values.append(float((prior * likelihood) @ conditional_k / evidence))
    return values


def action_free_reference(
    episodes: tuple[v234.Episode, ...],
) -> tuple[v234.AttributionScore, v234.AttributionScore]:
    prior = known_config_prior(0, 0)
    sham = v234.score(episodes, initial_prior=prior)
    action_free = tuple(
        v234.Episode(
            v234.ACTIONS["engage"],
            item.context,
            item.outcome,
            item.near_miss,
            item.efficacy_observation,
            item.relief,
        )
        for item in episodes
    )
    return sham, v234.score(action_free, initial_prior=prior)


def world_record(
    cell_name: str,
    seed: int,
    generator_name: str,
    kwargs: dict[str, Any],
    world: v234.AttributionWorld,
    result: v234.AttributionScore,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "cell": cell_name,
        "seed": seed,
        "generator": generator_name,
        "generator_kwargs": kwargs,
        "released_block": list(RELEASED_BLOCK),
        "truth": {
            "theta_index": world.theta_index,
            "theta": float(v234.THETA[world.theta_index]),
            "eta_indices": world.eta_indices,
            "eta": [float(v234.ETA[index]) for index in world.eta_indices],
            "identifiable": world.identifiable,
        },
        "episodes": [episode_record(item) for item in world.episodes],
        "score": score_record(result),
    }
    if cell_name == "cell_1_effective_action":
        reference_world = v234.generate_controlled_world(
            seed,
            scenario="low_danger",
            length=int(kwargs["length"]),
            released_block=RELEASED_BLOCK,
        )
        reference = v234.score(reference_world.episodes)
        record["low_danger_reference"] = score_record(reference)
        record["prevented_probability_K_recombined"] = recombined_k(
            world.episodes, result
        )
    elif cell_name == "cell_2_sham_action":
        sham, action_free = action_free_reference(world.episodes)
        record["known_irrelevant_sham_score"] = score_record(sham)
        record["known_irrelevant_action_free_score"] = score_record(action_free)
    elif cell_name == "cell_4_context_switch":
        switch = next(
            (
                index
                for index in range(1, len(world.episodes))
                if world.episodes[index].context
                != world.episodes[index - 1].context
            ),
            None,
        )
        if switch is None:
            raise RuntimeError("context-switch world has no switch")
        pre = v234.score(world.episodes[:switch])
        pre_snapshot = tuple(pre.eta_mean)
        through_post = v234.score(world.episodes[: 2 * switch])
        record["context_query"] = {
            "switch_index": switch,
            "pre_switch_eta_context_0": pre_snapshot[0],
            "post_switch_eta_context_1": through_post.eta_mean[1],
            "pre_switch_eta_requery": pre.eta_mean[0],
            "pre_switch_posterior_sha256": hashlib.sha256(
                np.asarray(pre.posterior, dtype=np.float64).tobytes()
            ).hexdigest(),
        }
    elif cell_name == "cell_5_forced_probe":
        reference_world = v234.generate_world(
            seed,
            identifiable=False,
            length=int(kwargs["length"]),
            theta_index=int(kwargs["theta_index"]),
            eta_indices=tuple(kwargs["eta_indices"]),
            probe_frequency=float(kwargs["probe_frequency"]),
            released_block=RELEASED_BLOCK,
        )
        reference = v234.score(reference_world.episodes)
        record["no_probe_reference"] = score_record(reference)
    elif cell_name == "cell_6_relief_only":
        record["prior_reference"] = {
            "posterior": v234.JOINT_PRIOR,
            "threat_probability": float(v234.JOINT_PRIOR @ v234.STATE_THETA),
            "efficacy_causal_probability": float(
                v234.JOINT_PRIOR @ v234.STATE_CAUSAL
            ),
            "eta_mean": [
                float(v234.JOINT_PRIOR @ v234.STATE_ETA0),
                float(v234.JOINT_PRIOR @ v234.STATE_ETA1),
            ],
        }
    return record


def generate_and_seal() -> None:
    bundle = parse_bundle()
    validation = validate_bundle(bundle)
    if not validation["expressible"]:
        dump(
            OUT / f"{FILE_STEM}-stop-as-sealed.json",
            {
                "immutable_verdict": "STOP_AS_SEALED",
                "validation": validation,
                "seeds_consumed": 0,
            },
        )
        raise SystemExit(2)
    seal_path = OUT / f"{FILE_STEM}-raw-trace-seal.json"
    if seal_path.exists():
        raise RuntimeError("raw trace seal exists; one-run budget is spent")
    hashes: dict[str, str] = {}
    counts: dict[str, int] = {}
    consumed: list[int] = []
    for cell_name in validation["cell_order"]:
        cell = bundle[cell_name]
        start, end = parse_escrow(cell["escrow"])
        rows = []
        for seed in range(start, end + 1):
            kwargs = dict(cell["kwargs"])
            generator = getattr(v234, cell["generator"])
            world = generator(
                seed,
                released_block=RELEASED_BLOCK,
                **kwargs,
            )
            result = v234.score(world.episodes)
            rows.append(
                world_record(
                    cell_name,
                    seed,
                    cell["generator"],
                    kwargs,
                    world,
                    result,
                )
            )
            consumed.append(seed)
        path = OUT / CELL_FILES[cell_name]
        dump(path, rows)
        hashes[CELL_FILES[cell_name]] = sha256(path)
        counts[cell_name] = len(rows)
    gap_free = consumed == list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1))
    seal = {
        "challenge": CHALLENGE_ID,
        "phase": "raw_traces_sealed_before_criteria",
        "validation": validation,
        "cell_hashes": hashes,
        "record_counts": counts,
        "consumed_seed_start": consumed[0],
        "consumed_seed_end": consumed[-1],
        "consumed_seed_count": len(consumed),
        "ascending_gap_free": gap_free,
        "criteria_evaluated": False,
    }
    dump(seal_path, seal)
    dump(
        OUT / f"{FILE_STEM}-run-ledger.json",
        {
            "challenge": CHALLENGE_ID,
            "release": {
                "block": list(RELEASED_BLOCK),
                "source": str(SEAL_LEDGER.relative_to(REPO_ROOT)),
                "authorization": "revealed sealed challenge and user release",
            },
            "literal_parser": "ast.literal_eval",
            "one_run": True,
            "seeds_consumed_once": len(consumed),
            "ascending_gap_free": gap_free,
            "raw_trace_seal": str(seal_path.relative_to(ROOT)),
            "raw_trace_seal_sha256": sha256(seal_path),
            "criteria_evaluated_at_ledger_write": False,
        },
    )


def interval(values: Iterable[float]) -> dict[str, float]:
    array = np.asarray(tuple(values), dtype=float)
    mean = float(array.mean())
    half = 1.96 * float(array.std(ddof=1)) / math.sqrt(len(array))
    return {
        "mean": mean,
        "lower_95": mean - half,
        "upper_95": mean + half,
        "count": len(array),
    }


def independent_difference_interval(
    left: Iterable[float],
    right: Iterable[float],
) -> dict[str, float]:
    left_array = np.asarray(tuple(left), dtype=float)
    right_array = np.asarray(tuple(right), dtype=float)
    difference = float(left_array.mean() - right_array.mean())
    standard_error = math.sqrt(
        float(left_array.var(ddof=1)) / len(left_array)
        + float(right_array.var(ddof=1)) / len(right_array)
    )
    half = 1.96 * standard_error
    return {
        "mean_difference": difference,
        "lower_95": difference - half,
        "upper_95": difference + half,
        "left_count": len(left_array),
        "right_count": len(right_array),
    }


def evaluate() -> bool:
    seal_path = OUT / f"{FILE_STEM}-raw-trace-seal.json"
    summary_path = OUT / f"{FILE_STEM}-summary.json"
    if not seal_path.exists():
        raise RuntimeError("raw traces must be sealed before criteria")
    if summary_path.exists():
        raise RuntimeError("criteria already evaluated; rerun forbidden")
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    cells = {
        name: json.loads((OUT / filename).read_text(encoding="utf-8"))
        for name, filename in CELL_FILES.items()
    }
    observed_hashes = {
        filename: sha256(OUT / filename) for filename in CELL_FILES.values()
    }
    hashes_match = observed_hashes == seal["cell_hashes"]

    cell1 = cells["cell_1_effective_action"]
    cell2 = cells["cell_2_sham_action"]
    cell3 = cells["cell_3_partial"]
    cell4 = cells["cell_4_context_switch"]
    cell5 = cells["cell_5_forced_probe"]
    cell6 = cells["cell_6_relief_only"]

    cell1_existence = float(
        np.mean(
            [
                row["score"]["efficacy_causal_probability"] > 0.5
                and abs(
                    row["score"]["efficacy_causal_probability"] - 0.5
                )
                > TOL
                for row in cell1
            ]
        )
    )
    danger_separation = interval(
        row["score"]["threat_probability"]
        - row["low_danger_reference"]["threat_probability"]
        for row in cell1
    )
    k_error = max(
        abs(left - right)
        for row in cell1
        for left, right in zip(
            row["score"]["prevented_probability_K"],
            row["prevented_probability_K_recombined"],
        )
    )

    cell2_no_false = float(
        np.mean(
            [
                row["score"]["efficacy_causal_probability"] <= 0.5
                for row in cell2
            ]
        )
    )
    sham_action_identity = max(
        abs(
            row["known_irrelevant_sham_score"]["threat_probability"]
            - row["known_irrelevant_action_free_score"]["threat_probability"]
        )
        for row in cell2
    )

    eta1 = [
        float(np.mean(row["score"]["eta_mean"])) for row in cell1
    ]
    eta2 = [
        float(np.mean(row["score"]["eta_mean"])) for row in cell2
    ]
    eta3 = [
        float(np.mean(row["score"]["eta_mean"])) for row in cell3
    ]
    full_above_partial = independent_difference_interval(eta1, eta3)
    partial_above_sham = independent_difference_interval(eta3, eta2)
    cell3_existence = float(
        np.mean(
            [
                row["score"]["efficacy_causal_probability"] > 0.5
                for row in cell3
            ]
        )
    )

    context_drop = interval(
        row["context_query"]["pre_switch_eta_context_0"]
        - row["context_query"]["post_switch_eta_context_1"]
        for row in cell4
    )
    pre_switch_query_error = max(
        abs(
            row["context_query"]["pre_switch_eta_context_0"]
            - row["context_query"]["pre_switch_eta_requery"]
        )
        for row in cell4
    )

    entropy_reduction = interval(
        row["no_probe_reference"]["posterior_entropy"]
        - row["score"]["posterior_entropy"]
        for row in cell5
    )

    relief_posterior_error = max(
        max(
            abs(left - right)
            for left, right in zip(
                row["score"]["posterior"],
                row["prior_reference"]["posterior"],
            )
        )
        for row in cell6
    )
    relief_danger_error = max(
        abs(
            row["score"]["threat_probability"]
            - row["prior_reference"]["threat_probability"]
        )
        for row in cell6
    )
    relief_causal_error = max(
        abs(
            row["score"]["efficacy_causal_probability"]
            - row["prior_reference"]["efficacy_causal_probability"]
        )
        for row in cell6
    )
    relief_eta_error = max(
        abs(left - right)
        for row in cell6
        for left, right in zip(
            row["score"]["eta_mean"],
            row["prior_reference"]["eta_mean"],
        )
    )

    one_posterior = all(
        row["score"]["one_posterior_audit"]
        for rows in cells.values()
        for row in rows
    )
    constitution_result = constitution.cumulative_constitution_audit()
    criteria = {
        "1_effective_action": {
            "efficacy_existence_unique_rate": cell1_existence,
            "danger_vs_low_danger": danger_separation,
            "prevented_outcome_recombination_error_max": k_error,
            "passed": (
                cell1_existence >= 0.75
                and danger_separation["lower_95"] > 0.0
                and k_error <= TOL
            ),
        },
        "2_sham_action": {
            "no_false_attribution_rate": cell2_no_false,
            "known_irrelevant_action_free_identity_error_max": (
                sham_action_identity
            ),
            "passed": (
                cell2_no_false >= CELL2_NO_FALSE_FLOOR
                and sham_action_identity <= TOL
            ),
        },
        "3_partial_efficacy": {
            "cell_1_eta_mean": interval(eta1),
            "cell_3_eta_mean": interval(eta3),
            "cell_2_eta_mean": interval(eta2),
            "full_above_partial": full_above_partial,
            "partial_above_sham": partial_above_sham,
            "efficacy_existence_recovery_rate": cell3_existence,
            "passed": (
                full_above_partial["lower_95"] > 0.0
                and partial_above_sham["lower_95"] > 0.0
                and cell3_existence >= CELL3_EXISTENCE_FLOOR
            ),
        },
        "4_context_switch": {
            "pre_minus_post_context_efficacy": context_drop,
            "pre_switch_attribution_query_error_max": pre_switch_query_error,
            "passed": (
                context_drop["lower_95"] > 0.0
                and pre_switch_query_error <= TOL
            ),
        },
        "5_forced_probe": {
            "joint_theta_eta_entropy_reduction": entropy_reduction,
            "passed": entropy_reduction["lower_95"] > 0.0,
        },
        "6_relief_only": {
            "scientific_posterior_movement_max": relief_posterior_error,
            "danger_movement_max": relief_danger_error,
            "efficacy_existence_movement_max": relief_causal_error,
            "efficacy_magnitude_movement_max": relief_eta_error,
            "passed": max(
                relief_posterior_error,
                relief_danger_error,
                relief_causal_error,
                relief_eta_error,
            )
            <= TOL,
        },
        "7_semantic_custody": {
            "one_posterior_all_worlds": one_posterior,
            "permanent_constitution": constitution_result["passed"],
            "raw_hashes_match_seal": hashes_match,
            "seed_count": seal["consumed_seed_count"],
            "ascending_gap_free": seal["ascending_gap_free"],
            "freeze_identity": seal["validation"]["freeze_identity"],
            "release_ledger": seal["validation"]["release_ledger"],
            "passed": (
                one_posterior
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
    passed = all(result["passed"] for result in criteria.values())
    summary = {
        "challenge": CHALLENGE_ID,
        "immutable_sealed_verdict": "PASS" if passed else "FAIL",
        "pass_rule": "all seven sealed criteria",
        "criteria": criteria,
        "verdict_classes": {
            "scientific": all(
                criteria[f"{index}_{name}"]["passed"]
                for index, name in (
                    (1, "effective_action"),
                    (2, "sham_action"),
                    (3, "partial_efficacy"),
                    (4, "context_switch"),
                    (5, "forced_probe"),
                    (6, "relief_only"),
                )
            ),
            "semantic": (
                one_posterior and constitution_result["passed"]
            ),
            "custody": criteria["7_semantic_custody"]["passed"],
        },
        "bounds": {
            "B_max_v232_formation": 3.801426508560692,
            "B_max_v24_common_emissions": 6.704414354964107,
            "B_max_v25a_configural": 6.084736253211209,
            "B_max_v25a_marginal_accounting": 6.704414354964107,
            "B_max_v25b": 11.302393144606405,
            "B_max_v26a_relational": 6.9920964274158885,
            "B_max_v26a_root": 2.9444389791664394,
            **v234.finite_information_bound(),
        },
        "passed": passed,
    }
    dump(summary_path, summary)
    ledger_path = OUT / f"{FILE_STEM}-run-ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["criteria_evaluated_after_raw_seal"] = True
    ledger["immutable_verdict"] = summary["immutable_sealed_verdict"]
    ledger["summary_sha256"] = sha256(summary_path)
    dump(ledger_path, ledger)
    return passed


def write_verdict(passed: bool) -> None:
    summary = json.loads((OUT / f"{FILE_STEM}-summary.json").read_text())
    lines = [
        f"# {CHALLENGE_ID} sealed verdict",
        "",
        f"Immutable sealed verdict: **{summary['immutable_sealed_verdict']}**.",
        "",
        "Pass requires all seven sealed criteria. No threshold, direction, "
        "reference construction, or scientific field was changed.",
        "",
        "## Criteria",
        "",
    ]
    for name, result in summary["criteria"].items():
        metrics = {key: value for key, value in result.items() if key != "passed"}
        lines.append(
            f"- `{name}`: **{'PASS' if result['passed'] else 'FAIL'}** — "
            f"`{json.dumps(metrics, sort_keys=True)}`"
        )
    lines += [
        "",
        "## Verdict classes",
        "",
        f"- Scientific: **{'PASS' if summary['verdict_classes']['scientific'] else 'FAIL'}**",
        f"- Semantic: **{'PASS' if summary['verdict_classes']['semantic'] else 'FAIL'}**",
        f"- Custody: **{'PASS' if summary['verdict_classes']['custody'] else 'FAIL'}**",
        "",
        "The base stage entered Gate 6 with a clean all-gates-1–5 freeze.",
        "Escrow was consumed once, ascending and gap-free, after evaluator release.",
    ]
    (OUT / f"{FILE_STEM}-verdict.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    if passed:
        (OUT / "stage-verdict.md").write_text(
            "# V2.3.4 stage verdict\n\n"
            "Final disposition: **PASS**.\n\n"
            f"{STAGE_PASS_TEXT}\n",
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
        OUT / f"{FILE_STEM}-full-fast-suite.json",
        {
            "command": "python3 run_tests_parallel.py",
            "returncode": suite.returncode,
            "passed": suite.returncode == 0,
            "stdout": suite.stdout,
            "stderr": suite.stderr,
        },
    )
    files = [
        f"results/V2.3.4/{filename}" for filename in CELL_FILES.values()
    ] + [
        f"results/V2.3.4/{FILE_STEM}-raw-trace-seal.json",
        f"results/V2.3.4/{FILE_STEM}-run-ledger.json",
        f"results/V2.3.4/{FILE_STEM}-summary.json",
        f"results/V2.3.4/{FILE_STEM}-verdict.md",
        f"results/V2.3.4/{FILE_STEM}-full-fast-suite.json",
        f"challenges/run_{FILE_STEM.replace('-', '_')}.py",
    ]
    if (OUT / "stage-verdict.md").exists():
        files.append("results/V2.3.4/stage-verdict.md")
    if FILE_STEM != "c-v234":
        files.append("challenges/run_c_v234.py")
    (OUT / f"ready-to-commit-{FILE_STEM}.md").write_text(
        f"# Ready to commit: {CHALLENGE_ID}\n\n"
        + "\n".join(f"- `{item}`" for item in files)
        + "\n",
        encoding="utf-8",
    )
    if suite.returncode:
        raise SystemExit(suite.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase", choices=("validate", "generate", "evaluate"), required=True
    )
    args = parser.parse_args()
    bundle = parse_bundle()
    if args.phase == "validate":
        validation = validate_bundle(bundle)
        print(json.dumps(plain(validation), indent=2, sort_keys=True))
        return 0 if validation["expressible"] else 2
    if args.phase == "generate":
        generate_and_seal()
        return 0
    passed = evaluate()
    write_verdict(passed)
    run_suite_and_ready()
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
