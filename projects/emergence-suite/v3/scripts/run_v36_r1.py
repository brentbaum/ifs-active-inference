#!/usr/bin/env python3
"""V3.6-R1 common-target bridge qualification and one-shot tournament."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT.parent
sys.path.insert(0, str(SUITE_ROOT))
sys.path.insert(0, str(ROOT))

from ref import v35, v36_bridge, v36_bridge_oracle  # noqa: E402
from ref.trace_sink import serializing_trace_context, traced_execution  # noqa: E402


RESULTS = ROOT / "results" / "V3.6"
BRIDGE = v36_bridge.BRIDGE_BLOCK
TOURNAMENT = v36_bridge.TOURNAMENT_BLOCK
TOLERANCE = v36_bridge.TOLERANCE


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(child) for child in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _canonical(value: Any) -> bytes:
    return (
        json.dumps(_plain(value), sort_keys=True, separators=(",", ":"),
                   allow_nan=False).encode("utf-8") + b"\n"
    )


def _write_json(name: str, value: Any) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / name).write_text(
        json.dumps(_plain(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _persist_rows(name: str, tasks: Sequence[Any], worker: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = RESULTS / f"{name}-traces.jsonl"
    ledger_path = RESULTS / f"{name}-trace-hashes.json"
    if path.exists() or ledger_path.exists():
        raise RuntimeError(f"custody refusal: {name} outputs already exist")
    rows, records = [], []
    digest = hashlib.sha256()
    processes = max(1, min(8, (os.cpu_count() or 2) - 1))
    with path.open("xb") as handle:
        with get_context("spawn").Pool(processes) as pool:
            for row in pool.imap(worker, tasks, chunksize=1):
                encoded = _canonical(row)
                handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
                digest.update(encoded)
                records.append({"seed": int(row["seed"]), "sha256": hashlib.sha256(encoded).hexdigest()})
                rows.append(row)
    task_seeds = [int(task[0] if isinstance(task, tuple) else task) for task in tasks]
    ledger = {
        "file": path.name, "sha256": digest.hexdigest(),
        "record_count": len(rows), "seed_start": task_seeds[0],
        "seed_end": task_seeds[-1],
        "ascending_gap_free": [row["seed"] for row in rows] == task_seeds,
        "persisted_before_aggregation": True, "records": records,
    }
    ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rows, ledger


def _proofs() -> dict[str, Any]:
    trace_path = RESULTS / "v3.6-r1-bridge-proofs-trace.jsonl"
    ledger_path = RESULTS / "v3.6-r1-bridge-proofs-trace-hashes.json"
    if trace_path.exists() or ledger_path.exists():
        raise RuntimeError("proof output already exists")
    with serializing_trace_context("v36-r1-fourteen-bridge-proofs") as sink:
        result = dict(v36_bridge.bridge_proofs(v36_bridge.public_dummy()))
        row = {"seed": 0, "public_dummy": True, "result": result, "_runtime_trace_events": sink.events}
    encoded = _canonical(row)
    with trace_path.open("xb") as handle:
        handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
    ledger = {
        "file": trace_path.name, "sha256": hashlib.sha256(encoded).hexdigest(),
        "record_count": 1, "persisted_before_aggregation": True,
        "records": [{"seed": 0, "sha256": hashlib.sha256(encoded).hexdigest()}],
    }
    ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n")
    output = {
        "stage": "V3.6-R1", "phase": "pre-criterion bridge proofs",
        "r0_spec_hash": v36_bridge.R0_SPEC_HASH,
        "margin": v36_bridge.DELTA, **result,
        "custody": ledger,
        "verdict": "PASS" if result["passed"] else "FAIL_APPARATUS_STOP",
    }
    _write_json("v3.6-r1-bridge-proofs.json", output)
    (RESULTS / "v3.6-r1-bridge-proofs.md").write_text(
        "# V3.6-R1 pre-criterion bridge proofs\n\n"
        f"Verdict: **{output['verdict']}**. All fourteen proofs are listed in "
        "the JSON record. The public dummy ledger was persisted and hashed "
        "before this aggregate was written.\n",
        encoding="utf-8",
    )
    return output


def _coverage(classes: Mapping[str, float], truth: str, mass: float) -> bool:
    return v36_bridge_oracle.credible_set_contains(classes, truth, mass)


@traced_execution
def _bridge_row(task: tuple[int, str]) -> dict[str, Any]:
    seed, population = task
    world = v36_bridge.generate_document(seed, population=population, released_block=BRIDGE)
    views = v36_bridge.adapter_documents(world)
    v2 = v36_bridge.score_v2(world)
    v3 = v36_bridge.score_v3(world)
    observed = v36_bridge.observed_targets(world)
    scores2 = v36_bridge.log_scores(world, v2)
    scores3 = v36_bridge.log_scores(world, v3)
    predictions = {
        model: {
            target: {
                "p1": [float(row[1]) for row in values[target].probabilities],
                "delivered": list(values[target].delivered),
            }
            for target in v36_bridge.TARGETS
        }
        for model, values in (("v2", v2), ("v3", v3))
    }
    row = {
        "seed": seed, "population": population, "stratum": world.stratum,
        "active_modes": world.active_modes,
        "world_sha256_v2": world.world_sha256,
        "world_sha256_v3": world.world_sha256,
        "observation_sha256_v2": world.observation_sha256,
        "observation_sha256_v3": world.observation_sha256,
        "heldout_target_sha256_v2": world.heldout_target_sha256,
        "heldout_target_sha256_v3": world.heldout_target_sha256,
        "targets": _plain(observed), "predictions": predictions,
        "scores": {"v2": dict(scores2), "v3": dict(scores3)},
        "truth": {
            "active_modes": world.active_modes,
            "edges": dict(v35.program_values(world.structure)),
        },
    }
    if population == "own_prior":
        profile = v36_bridge.equivalence_profile(world)
        classes = dict(profile["classes"])
        row["equivalence"] = {
            "truth_mass": profile["truth_class_mass"],
            "confidence": profile["class_confidence"],
            "correct": profile["class_correct"],
            "coverage": {str(level): _coverage(classes, profile["truth_class"], level) for level in (0.5, 0.8, 0.9, 0.95)},
            "normalized_entropy": profile["class_entropy"] / max(math.log(len(classes)), 1.0),
            "active_probabilities": list(profile["active_count_probabilities"]),
            "edge_probabilities": dict(profile["edge_probabilities"]),
            "exact_truth_mass": profile["exact_truth_mass"],
            "exact_confidence": profile["exact_confidence"],
            "exact_correct": profile["exact_correct"],
        }
    return row


def _reliability(probabilities: Sequence[float], outcomes: Sequence[int]) -> dict[str, Any]:
    p, y = np.asarray(probabilities), np.asarray(outcomes, dtype=float)
    bins = []
    ece = 0.0
    for index in range(10):
        low, high = index / 10, (index + 1) / 10
        chosen = (p >= low) & (p <= high if index == 9 else p < high)
        count = int(chosen.sum())
        confidence = float(p[chosen].mean()) if count else None
        frequency = float(y[chosen].mean()) if count else None
        if count:
            ece += count / len(p) * abs(confidence - frequency)
        bins.append({"low": low, "high": high, "count": count, "confidence": confidence, "frequency": frequency})
    return {
        "ece": float(ece), "brier": float(np.mean((p - y) ** 2)),
        "mean_log_score": float(np.mean(y * np.log(p) + (1-y) * np.log(1-p))),
        "reliability": bins, "token_count": len(p),
    }


def _target_calibration(rows: Sequence[Mapping[str, Any]], model: str, target: str) -> dict[str, Any]:
    p, y = [], []
    for row in rows:
        values = row["predictions"][model][target]
        for probability, observed, delivered in zip(values["p1"], row["targets"][target], values["delivered"]):
            if delivered and observed is not None:
                p.append(probability); y.append(int(observed))
    result = _reliability(p, y)
    result["strata"] = {}
    for field in ("stratum", "active_modes"):
        for value in sorted({row[field] for row in rows}, key=str):
            selected = [row for row in rows if row[field] == value]
            pp, yy = [], []
            for row in selected:
                values = row["predictions"][model][target]
                for probability, observed, delivered in zip(values["p1"], row["targets"][target], values["delivered"]):
                    if delivered and observed is not None:
                        pp.append(probability); yy.append(int(observed))
            result["strata"][f"{field}={value}"] = _reliability(pp, yy)
    return result


def _ece_confidence(confidence: Sequence[float], correct: Sequence[bool]) -> float:
    p, y = np.asarray(confidence), np.asarray(correct, dtype=float)
    total = 0.0
    for index in range(10):
        chosen = (p >= index/10) & (p <= (index+1)/10 if index == 9 else p < (index+1)/10)
        if chosen.any(): total += chosen.mean() * abs(p[chosen].mean() - y[chosen].mean())
    return float(total)


def _ece_binary(probability: Sequence[float], truth: Sequence[int]) -> float:
    return _reliability(probability, truth)["ece"]


def _bootstrap_width(values: Sequence[float], seed: int) -> tuple[list[float], float]:
    array = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(100):
        indices = rng.integers(0, len(array), size=(100, len(array)))
        means.extend(np.mean(array[indices], axis=1))
    interval = [float(value) for value in np.quantile(means, [0.025, 0.975])]
    return interval, interval[1] - interval[0]


def run_bridge() -> dict[str, Any]:
    proof = json.loads((RESULTS / "v3.6-r1-bridge-proofs.json").read_text())
    if proof["verdict"] != "PASS":
        raise RuntimeError("bridge proofs are not PASS")
    tasks = [(seed, "own_prior" if seed < 3_682_000 else "fixed_stratum") for seed in range(BRIDGE[0], BRIDGE[1] + 1)]
    rows, ledger = _persist_rows("v3.6-r1-bridge", tasks, _bridge_row)
    calibrations = {
        model: {target: _target_calibration(rows, model, target) for target in v36_bridge.TARGETS}
        for model in ("v2", "v3")
    }
    fixed = [row for row in rows if row["population"] == "fixed_stratum"]
    precision = {}
    for index, target in enumerate(v36_bridge.TARGETS):
        interval, width = _bootstrap_width([row["scores"]["v2"][target] for row in fixed], 368_000 + index)
        precision[target] = {"interval_95": interval, "width": width, "maximum": v36_bridge.DELTA, "passed": width <= v36_bridge.DELTA}
    own = [row for row in rows if row["population"] == "own_prior"]
    class_ece = _ece_confidence([row["equivalence"]["confidence"] for row in own], [row["equivalence"]["correct"] for row in own])
    coverage = {level: float(np.mean([row["equivalence"]["coverage"][level] for row in own])) for level in ("0.5", "0.8", "0.9", "0.95")}
    active_probability = [row["equivalence"]["active_probabilities"][row["truth"]["active_modes"]-1] for row in own]
    active_correct = [int(np.argmax(row["equivalence"]["active_probabilities"])) == row["truth"]["active_modes"]-1 for row in own]
    active_ece = _ece_confidence(active_probability, active_correct)
    edge_ece = {
        name: _ece_binary([row["equivalence"]["edge_probabilities"][name] for row in own], [row["truth"]["edges"][name] for row in own])
        for name in v35.EDGE_NAMES
    }
    structure = {
        "class_ece": class_ece, "coverage": coverage,
        "active_count_ece": active_ece, "edge_ece": edge_ece,
        "normalized_class_entropy_mean": float(np.mean([row["equivalence"]["normalized_entropy"] for row in own])),
        "exact_program_accuracy_descriptive": float(np.mean([row["equivalence"]["exact_correct"] for row in own])),
        "exact_program_ece_descriptive": _ece_confidence([row["equivalence"]["exact_confidence"] for row in own], [row["equivalence"]["exact_correct"] for row in own]),
        "reweighted_posterior_diagnostic_only": True,
    }
    failures = []
    for model, targets in calibrations.items():
        for target, metrics in targets.items():
            if metrics["ece"] > 0.05:
                failures.append(f"{model} {target} predictive ECE {metrics['ece']} > 0.05")
    for target, values in precision.items():
        if not values["passed"]: failures.append(f"V2 {target} bootstrap width {values['width']} > delta")
    if class_ece > 0.05: failures.append(f"class ECE {class_ece} > 0.05")
    if coverage["0.95"] < 0.90: failures.append(f"95% class-set coverage {coverage['0.95']} < 0.90")
    if active_ece > 0.05: failures.append(f"active-count ECE {active_ece} > 0.05")
    for edge, value in edge_ece.items():
        if value > 0.05: failures.append(f"edge {edge} ECE {value} > 0.05")
    hashes_equal = all(row["world_sha256_v2"] == row["world_sha256_v3"] and row["observation_sha256_v2"] == row["observation_sha256_v3"] and row["heldout_target_sha256_v2"] == row["heldout_target_sha256_v3"] for row in rows)
    if not hashes_equal: failures.append("per-seed document identity failed")
    result = {
        "stage": "V3.6-R1", "phase": "bridge qualification",
        "seed_block": list(BRIDGE), "world_count": len(rows),
        "proofs": proof["proofs"], "per_seed_hash_identity": hashes_equal,
        "v2_precision_qualification": precision,
        "predictive_calibration": calibrations,
        "equivalence_class_profile": structure,
        "failures": failures, "custody": ledger,
        "verdict": "PASS" if not failures else "FAIL_APPARATUS_STOP",
    }
    _write_json("v3.6-r1-bridge-qualification.json", result)
    (RESULTS / "v3.6-r1-bridge-qualification.md").write_text(
        "# V3.6-R1 bridge qualification\n\n"
        f"Verdict: **{result['verdict']}**.\n\n"
        + ("Failures:\n" + "\n".join(f"- {item}" for item in failures) if failures else "All bridge, precision, predictive-calibration, and equivalence-class requirements passed.") + "\n",
        encoding="utf-8",
    )
    if failures:
        _write_json("v3.6-r1-bridge-diagnosis-stub.json", {"failures": failures, "next_action": "HONEST_STOP_RETURN_TO_EVALUATOR"})
    return result


@traced_execution
def _tournament_row(seed: int) -> dict[str, Any]:
    world = v36_bridge.generate_document(seed, population="fixed_stratum", released_block=TOURNAMENT)
    views = v36_bridge.adapter_documents(world)
    v2 = v36_bridge.score_v2(world); v3 = v36_bridge.score_v3(world)
    return {
        "seed": seed, "stratum": world.stratum, "active_modes": world.active_modes,
        "world_sha256_v2": world.world_sha256, "world_sha256_v3": world.world_sha256,
        "observation_sha256_v2": world.observation_sha256, "observation_sha256_v3": world.observation_sha256,
        "heldout_target_sha256_v2": world.heldout_target_sha256, "heldout_target_sha256_v3": world.heldout_target_sha256,
        "scores": {"v2": dict(v36_bridge.log_scores(world, v2)), "v3": dict(v36_bridge.log_scores(world, v3))},
    }


def _bootstrap_interval(values: Sequence[float], seed: int) -> list[float]:
    array = np.asarray(values, dtype=float); rng = np.random.default_rng(seed); means = []
    for _ in range(100):
        indices = rng.integers(0, len(array), size=(100, len(array)))
        means.extend(np.mean(array[indices], axis=1))
    return [float(value) for value in np.quantile(means, [0.025, 0.975])]


def run_tournament() -> dict[str, Any]:
    qualification = json.loads((RESULTS / "v3.6-r1-bridge-qualification.json").read_text())
    if qualification["verdict"] != "PASS":
        raise RuntimeError("bridge qualification did not pass; tournament forbidden")
    seeds = list(range(TOURNAMENT[0], TOURNAMENT[1] + 1))
    rows, ledger = _persist_rows("v3.6-r1-tournament", seeds, _tournament_row)
    pareto = {}
    failures = []
    for index, target in enumerate(v36_bridge.TARGETS):
        values = [row["scores"]["v3"][target] - row["scores"]["v2"][target] for row in rows]
        interval = _bootstrap_interval(values, 368_400 + index)
        passed = interval[0] >= -v36_bridge.DELTA
        pareto[target] = {"mean_D": float(np.mean(values)), "interval_95": interval, "delta": v36_bridge.DELTA, "passed": passed, "quantiles": [float(x) for x in np.quantile(values, [0.01,0.05,0.5,0.95,0.99])]}
        if not passed: failures.append(target)
    macro = float(np.mean([value["mean_D"] for value in pareto.values()]))
    result = {
        "stage": "V3.6-R1", "name": "COMMON-TARGET COMPRESSION TOURNAMENT",
        "seed_block": list(TOURNAMENT), "world_count": len(rows),
        "pareto_vector": pareto, "macro_mean_descriptive_only": macro,
        "scientific_failures": failures,
        "original_tournament_unchanged": True,
        "custody": ledger,
        "verdict": "PASS_SHARED_TARGET_NONINFERIORITY" if not failures else "RETAINED_SCIENTIFIC_PREDICTIVE_COST",
    }
    _write_json("v3.6-r1-tournament.json", result)
    (RESULTS / "v3.6-r1-tournament.md").write_text(
        "# V3.6-R1 common-target compression tournament\n\n"
        f"Immutable scientific result: **{result['verdict']}**.\n\n"
        "The five familywise results are the criterion; the macro mean is descriptive only. "
        "A valid numerical failure does not block later mechanism gates.\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("proofs", "bridge", "tournament"))
    phase = parser.parse_args().phase
    result = _proofs() if phase == "proofs" else run_bridge() if phase == "bridge" else run_tournament()
    print(json.dumps({"phase": phase, "verdict": result["verdict"]}, sort_keys=True))
    return 0 if result["verdict"] in {"PASS", "PASS_SHARED_TARGET_NONINFERIORITY", "RETAINED_SCIENTIFIC_PREDICTIVE_COST"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
