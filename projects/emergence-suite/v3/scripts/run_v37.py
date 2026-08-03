#!/usr/bin/env python3
"""V3.7 proof, qualification, tournament, and prediction-scoring runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import pickle
import sys
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT.parent
sys.path.insert(0, str(SUITE_ROOT))
sys.path.insert(0, str(ROOT))

from ref import v35, v36_bridge, v36_round12, v37  # noqa: E402
from ref.custody import NonFiniteWorkerRow, validate_finite_worker_row  # noqa: E402
from ref.trace_sink import serializing_trace_context, traced_execution  # noqa: E402


RESULTS = ROOT / "results" / "V3.7"
TARGETS = v36_bridge.TARGETS
STRATA = v36_round12.STRATA
DELTA = math.log(1.02)
TOLERANCE = 1e-10
A37_R1_BLOCK = (3_746_000, 3_747_999)


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(child) for child in value]
    if hasattr(value, "__dataclass_fields__"):
        return {field: _plain(getattr(value, field)) for field in value.__dataclass_fields__}
    if isinstance(value, np.generic):
        return value.item()
    return value


def _canonical(value: Any) -> bytes:
    return (
        json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _write_json(name: str, value: Any) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / name
    path.write_text(
        json.dumps(_plain(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _write_report(name: str, title: str, value: Mapping[str, Any]) -> None:
    (RESULTS / name).write_text(
        "\n".join((
            f"# {title}", "", f"Verdict: **{value['verdict']}**.", "",
            "```json", json.dumps(_plain(value), indent=2, sort_keys=True, allow_nan=False),
            "```", "",
        )),
        encoding="utf-8",
    )


def _bin(probability: float) -> int:
    return min(int(float(probability) * 10.0), 9)


def _weighted_binary(worlds: Sequence[Sequence[tuple[float, int]]]) -> dict[str, Any]:
    bins = [{
        "low": index / 10.0, "high": (index + 1) / 10.0, "count": 0,
        "effective_world_weight": 0.0, "confidence_numerator": 0.0,
        "frequency_numerator": 0.0,
    } for index in range(10)]
    brier = log_score = assigned = entropy = 0.0
    for tokens in worlds:
        if not tokens:
            raise ValueError("calibration world has no delivered token")
        weight = 1.0 / len(tokens)
        for probability, observed in tokens:
            probability = float(probability); observed = int(observed)
            row = bins[_bin(probability)]
            row["count"] += 1; row["effective_world_weight"] += weight
            row["confidence_numerator"] += weight * probability
            row["frequency_numerator"] += weight * observed
            brier += weight * (probability - observed) ** 2
            log_score += weight * math.log(probability if observed else 1.0 - probability)
            assigned += weight * (probability if observed else 1.0 - probability)
            entropy += weight * (-probability * math.log(probability) - (1-probability) * math.log(1-probability))
    ece = 0.0; reliability = []
    for row in bins:
        weight = float(row["effective_world_weight"])
        confidence = row["confidence_numerator"] / weight if weight else None
        frequency = row["frequency_numerator"] / weight if weight else None
        if weight:
            ece += weight / len(worlds) * abs(confidence - frequency)
        reliability.append({
            "low": row["low"], "high": row["high"], "count": row["count"],
            "effective_world_weight": weight, "confidence": confidence,
            "frequency": frequency,
        })
    return {
        "ece": float(ece), "brier": float(brier / len(worlds)),
        "mean_log_score": float(log_score / len(worlds)),
        "prediction_entropy": float(entropy / len(worlds)),
        "mean_assigned_probability": float(assigned / len(worlds)),
        "world_count": len(worlds), "reliability": reliability,
    }


def _top_label(probabilities: Sequence[Sequence[float]], truths: Sequence[int]) -> dict[str, Any]:
    worlds = []; truth_mass = []; correct = []; brier = []; logs = []
    for values, truth in zip(probabilities, truths, strict=True):
        array = np.asarray(values, dtype=float); top = int(np.argmax(array))
        worlds.append([(float(np.max(array)), int(top == truth))])
        truth_mass.append(float(array[truth])); correct.append(int(top == truth))
        brier.append(float(np.sum((array - np.eye(len(array))[truth]) ** 2)))
        logs.append(math.log(float(array[truth])))
    result = _weighted_binary(worlds)
    result.update({
        "mean_truth_probability": float(np.mean(truth_mass)),
        "argmax_accuracy": float(np.mean(correct)),
        "multiclass_brier": float(np.mean(brier)),
        "multiclass_log_score": float(np.mean(logs)),
    })
    return result


def _macro_classwise(probabilities: Sequence[Sequence[float]], truths: Sequence[int]) -> dict[str, Any]:
    classes = {
        str(index + 1): _weighted_binary([[(float(values[index]), int(truth == index))]
                                          for values, truth in zip(probabilities, truths, strict=True)])
        for index in range(len(probabilities[0]))
    }
    return {"per_class": classes, "macro_ece": float(np.mean([row["ece"] for row in classes.values()]))}


def _serialized_prediction(document: Any, predictions: Mapping[str, Any]):
    targets = v36_bridge.observed_targets(document)
    output = {}
    for target in TARGETS:
        vectors = [list(map(float, row)) for row in predictions[target].probabilities]
        p1 = [row[1] for row in vectors]; delivered = list(predictions[target].delivered)
        output[target] = {
            "vectors": vectors, "p1": p1, "delivered": delivered,
            "delivered_token_count": sum(flag and value is not None for flag, value in zip(delivered, targets[target], strict=True)),
            "bin_assignments": [_bin(probability) if flag and value is not None else None
                                for probability, flag, value in zip(p1, delivered, targets[target], strict=True)],
        }
    return output, _plain(targets)


def _predictive_calibration(rows: Sequence[Mapping[str, Any]], model: str) -> dict[str, Any]:
    result = {}
    for target in TARGETS:
        worlds = []
        for row in rows:
            prediction = row["predictions"][model][target]
            worlds.append([(float(p), int(y)) for p, y, delivered in zip(
                prediction["p1"], row["targets"][target], prediction["delivered"], strict=True
            ) if delivered and y is not None])
        result[target] = _weighted_binary(worlds)
    return result


def _structure_calibration(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    states = [row["calibration_state"] for row in rows]
    class_top = _weighted_binary([[(float(state["class_confidence"]), int(state["class_correct"]))] for state in states])
    active = [state["active_count_posterior"] for state in states]
    truths = [int(state["truth_active_count"]) - 1 for state in states]
    edges = {
        name: _weighted_binary([[(float(state["edge_posteriors"][name]), int(state["truth_edges"][name]))] for state in states])
        for name in v35.EDGE_NAMES
    }
    return {
        "equivalence_class_top_label": class_top,
        "class_set_coverage": {level: float(np.mean([state["class_coverage"][level] for state in states])) for level in ("0.5", "0.8", "0.9", "0.95")},
        "active_count_top_label": _top_label(active, truths),
        "active_count_macro_classwise": _macro_classwise(active, truths),
        "edges": edges,
        "truth_class_mass_mean": float(np.mean([state["truth_class_mass"] for state in states])),
        "normalized_class_entropy_mean": float(np.mean([state["normalized_class_entropy"] for state in states])),
        "exact_program_accuracy_descriptive": float(np.mean([state["exact_correct"] for state in states])),
    }


def _bootstrap(values: Sequence[float], seed: int) -> list[float]:
    array = np.asarray(values, dtype=float); rng = np.random.default_rng(seed); means = []
    for _ in range(100):
        indices = rng.integers(0, len(array), size=(100, len(array)))
        means.extend(np.mean(array[indices], axis=1))
    return [float(value) for value in np.quantile(means, (0.025, 0.975))]


def _persist_rows(name: str, tasks: Sequence[Any], worker: Any, group_size: int):
    path = RESULTS / f"{name}-traces.jsonl"; ledger_path = RESULTS / f"{name}-trace-hashes.json"
    event_path = RESULTS / f"{name}-trace-hash-events.jsonl"
    if any(item.exists() for item in (path, ledger_path, event_path)):
        raise RuntimeError(f"custody refusal: {name} output exists")
    if len(tasks) % group_size:
        raise ValueError("stratum group size does not divide task count")
    rows = []; records = []; digest = hashlib.sha256()
    def persist(handle, event_handle, row):
        try:
            validate_finite_worker_row(row)
        except NonFiniteWorkerRow as error:
            provenance = {"record_type": "NONFINITE_WORKER_ROW_REJECTION", "seed": row.get("seed"), "paths": list(error.paths)}
            encoded = _canonical(provenance); handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
            raise RuntimeError(str(error)) from error
        encoded = _canonical(row); handle.write(encoded); handle.flush(); os.fsync(handle.fileno()); digest.update(encoded)
        record = {"seed": int(row["seed"]), "sha256": hashlib.sha256(encoded).hexdigest()}
        event_handle.write(_canonical(record)); event_handle.flush(); os.fsync(event_handle.fileno())
        rows.append(row); records.append(record)
    processes = max(1, min(8, (os.cpu_count() or 2) - 1))
    with path.open("xb") as handle, event_path.open("xb") as event_handle:
        for start in range(0, len(tasks), group_size):
            group = tasks[start:start + group_size]
            persist(handle, event_handle, worker(group[0]))
            if len(group) > 1:
                with get_context("spawn").Pool(processes) as pool:
                    for row in pool.imap(worker, group[1:], chunksize=1):
                        persist(handle, event_handle, row)
    seeds = [int(task[0] if isinstance(task, tuple) else task) for task in tasks]
    if [int(row["seed"]) for row in rows] != seeds or seeds != list(range(seeds[0], seeds[-1] + 1)):
        raise RuntimeError("custody failure: seeds not ascending and gap-free")
    ledger = {
        "file": path.name, "sha256": digest.hexdigest(), "record_count": len(rows),
        "seed_start": seeds[0], "seed_end": seeds[-1], "ascending_gap_free": True,
        "persisted_before_aggregation": True, "incremental_hash_events_file": event_path.name,
        "incremental_hash_events_sha256": hashlib.sha256(event_path.read_bytes()).hexdigest(),
        "per_stratum_serial_first_seeds": seeds[::group_size], "records": records,
    }
    ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rows, ledger


@traced_execution
def _native_row(task: tuple[int, int, int]) -> dict[str, Any]:
    seed, start, end = task; world = v37.generate_v3_native_world(seed, released_block=(start, end))
    return _native_row_from_world(world, seed=seed)


def _native_row_from_world(world: v37.V37World, *, seed: int) -> dict[str, Any]:
    predictions = v37.score_v37(world); serialized, targets = _serialized_prediction(world.document, predictions)
    state = v37.calibration_state(world)
    return {
        "seed": seed, "population": "A37_complete_native", "stratum": world.document.stratum,
        "world_sha256": world.document.world_sha256, "observation_sha256": world.document.observation_sha256,
        "target_sha256": world.document.heldout_target_sha256,
        # Round 21: immutable scientific views become plain containers only
        # at the worker-row serialization boundary.  Values are unchanged.
        "predictions": {"v37": serialized}, "targets": targets,
        "calibration_state": _plain(state),
        "native_path_state": {
            "latent_mode_path": [list(item.modes_input) for item in world.document.slices],
            "context_state_path": [item.context_input for item in world.document.slices],
            "partner_state_path": list(world.partner_state_path), "danger_state_path": list(world.danger_state_path),
            "persistence_index": world.persistence_index, "contact_response_truth": world.contact_parameter,
            "prefix_observations": [_plain(item) for item in world.document.slices[:v36_bridge.PREFIX_SLICES]],
            "intervention_schedule": [{"action": item.action, "joint_policy": list(item.joint_policy)} for item in world.document.slices],
            "masks": {target: [value is None for value in targets[target]] for target in TARGETS},
        },
    }


@traced_execution
def _external_row(task: tuple[int, int, int, str]) -> dict[str, Any]:
    seed, start, end, phase = task; world = v37.generate_external_world(seed, released_block=(start, end)); document = world.document
    return _external_row_from_document(document, phase=phase)


def _external_row_from_document(document: v36_bridge.CanonicalWorld, *, phase: str) -> dict[str, Any]:
    seed = int(document.seed)
    prediction2 = v36_bridge.score_v2(document); prediction37 = v37.score_v37(document)
    serialized2, targets2 = _serialized_prediction(document, prediction2)
    serialized37, targets37 = _serialized_prediction(document, prediction37)
    if targets2 != targets37:
        raise AssertionError("adapter target views differ")
    scores2 = dict(v36_bridge.log_scores(document, prediction2)); scores37 = dict(v36_bridge.log_scores(document, prediction37))
    return {
        "seed": seed, "population": "external_shared_support", "phase": phase, "stratum": document.stratum,
        "world_sha256_v2": document.world_sha256, "world_sha256_v37": document.world_sha256,
        "observation_sha256_v2": document.observation_sha256, "observation_sha256_v37": document.observation_sha256,
        "target_sha256_v2": document.heldout_target_sha256, "target_sha256_v37": document.heldout_target_sha256,
        "predictions": {"v2": serialized2, "v37": serialized37}, "targets": targets2,
        "scores": {"v2": scores2, "v37": scores37}, "document_identity": True,
    }


def _roundtrip(value: Any) -> dict[str, Any]:
    encoded = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
    decoded = pickle.loads(encoded)
    return {
        "pickle_byte_count": len(encoded),
        "deep_equal": decoded == value,
        "original_type": type(value).__name__,
        "decoded_type": type(decoded).__name__,
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _run_roundtrip_proof(label: str, kinds: Sequence[str]) -> dict[str, Any]:
    """Persist the exact parallel worker-row types before a block opens."""
    path = RESULTS / f"v3.7-{label}-serialization-roundtrip-proof.jsonl"
    hash_path = RESULTS / f"v3.7-{label}-serialization-roundtrip-proof-hash.json"
    if path.exists() or hash_path.exists():
        raise RuntimeError(f"round-trip proof output already exists for {label}")
    with serializing_trace_context(f"v37-{label}-serialization-roundtrip") as sink:
        document = v36_bridge.public_dummy()
        records = {}
        if "native" in kinds:
            dummy_world = v37.V37World(
                document=document,
                persistence_index=0,
                partner_state_path=(0,) * len(document.slices),
                danger_state_path=(0,) * len(document.slices),
                contact_parameter=int(document.contact_response),
            )
            records["native"] = _roundtrip(
                _native_row_from_world(dummy_world, seed=int(document.seed))
            )
        if "external" in kinds:
            records["external"] = _roundtrip(
                _external_row_from_document(document, phase="zero_seed_roundtrip")
            )
        events = list(sink.events)
    result = {
        "label": label, "zero_seed": True, "worker_row_types": records,
        "nested_deep_equality_required": True, "runtime_trace_events": events,
        "verdict": "PASS" if records and all(row["deep_equal"] for row in records.values()) else "FAIL_APPARATUS_STOP",
    }
    encoded = _canonical(result)
    with path.open("xb") as handle:
        handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
    hash_record = {
        "file": path.name, "sha256": hashlib.sha256(encoded).hexdigest(),
        "persisted_before_block": True, "record_count": 1,
    }
    _write_json(hash_path.name, hash_record)
    if result["verdict"] != "PASS":
        raise RuntimeError(f"serialization round-trip proof failed for {label}")
    return {**result, "custody": hash_record}


def run_proofs() -> dict[str, Any]:
    with serializing_trace_context("v37-zero-seed-proof-battery") as sink:
        proofs = _plain(v37.zero_seed_proofs()); events = list(sink.events)
    frozen_manifest = json.loads((ROOT / "results/V3.6/v3.6-freeze-manifest-final.json").read_text())
    checked = {}; changed = []
    for relative, expected in frozen_manifest.get("files", {}).items():
        if relative.startswith("ref/v3") and (ROOT / relative).exists():
            observed = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            checked[relative] = {"expected": expected, "observed": observed, "equal": observed == expected}
            if observed != expected: changed.append(relative)
    record = {
        "stage": "V3.7", "proofs": proofs, "runtime_trace_events": events,
        "frozen_v36_scientific_hash_check": checked, "changed_frozen_files": changed,
        "verdict": "PASS" if proofs["passed"] and not changed else "FAIL_APPARATUS_STOP",
    }
    encoded = _canonical(record); trace = RESULTS / "v3.7-zero-seed-proof-record.jsonl"
    with trace.open("xb") as handle: handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
    hashes = {"file": trace.name, "sha256": hashlib.sha256(encoded).hexdigest(), "record_count": 1, "persisted_before_verdict": True}
    _write_json("v3.7-zero-seed-proof-hashes.json", hashes)
    record["custody"] = hashes; _write_json("v3.7-zero-seed-proofs.json", record); _write_report("v3.7-zero-seed-proofs.md", "V3.7 zero-seed proof battery", record)
    return record


def run_population_a() -> dict[str, Any]:
    if json.loads((RESULTS / "v3.7-zero-seed-proofs.json").read_text())["verdict"] != "PASS":
        raise RuntimeError("zero-seed proofs did not pass")
    roundtrip = _run_roundtrip_proof("population-a37-r1-preblock", ("native",))
    start, end = A37_R1_BLOCK; tasks = [(seed, start, end) for seed in range(start, end + 1)]
    rows, ledger = _persist_rows("v3.7-population-a37-r1", tasks, _native_row, 500)
    predictive = _predictive_calibration(rows, "v37"); structure = _structure_calibration(rows); failures = []
    for target, metrics in predictive.items():
        if metrics["ece"] > .05: failures.append(f"{target} ECE {metrics['ece']} > 0.05")
        if not math.isfinite(metrics["brier"]) or not math.isfinite(metrics["mean_log_score"]): failures.append(f"{target} proper score non-finite")
    if structure["equivalence_class_top_label"]["ece"] > .05: failures.append("class top-label ECE > 0.05")
    if structure["class_set_coverage"]["0.95"] < .90: failures.append("class 95% coverage < 0.90")
    if structure["active_count_top_label"]["ece"] > .05: failures.append("active-count top-label ECE > 0.05")
    if structure["active_count_macro_classwise"]["macro_ece"] > .05: failures.append("active-count macro ECE > 0.05")
    for edge, metrics in structure["edges"].items():
        if metrics["ece"] > .05: failures.append(f"edge {edge} ECE > 0.05")
    max_norm = max(float(row["calibration_state"]["normalization_error"]) for row in rows)
    if max_norm > TOLERANCE: failures.append("posterior normalization error > 1e-10")
    result = {"stage": "V3.7", "population": "A37", "seed_block": [start,end], "world_count": len(rows),
              "stratum_counts": {s: sum(row["stratum"] == s for row in rows) for s in STRATA},
              "predictive_calibration": predictive, "structure_calibration": structure,
              "maximum_normalization_error": max_norm, "serialization_roundtrip_proof": roundtrip,
              "failures": failures, "custody": ledger,
              "verdict": "PASS" if not failures else "FAIL"}
    _write_json("v3.7-population-a37-r1.json", result); _write_report("v3.7-population-a37-r1.md", "V3.7 Population A37-R1 qualification", result)
    return result


def _external_descriptive(rows):
    output = {}
    for model in ("v2", "v37"):
        output[model] = {"overall": _predictive_calibration(rows, model), "strata": {}}
        for stratum in STRATA:
            output[model]["strata"][stratum] = _predictive_calibration([row for row in rows if row["stratum"] == stratum], model)
    return output


def run_population_c() -> dict[str, Any]:
    if json.loads((RESULTS / "v3.7-population-a37-r1.json").read_text())["verdict"] != "PASS": raise RuntimeError("Population A37-R1 did not pass")
    roundtrip = _run_roundtrip_proof("population-c37-preblock", ("external",))
    start,end=v37.C_BLOCK; tasks=[(seed,start,end,"C37") for seed in range(start,end+1)]
    rows,ledger=_persist_rows("v3.7-population-c37",tasks,_external_row,500)
    identity=all(row["document_identity"] and row["world_sha256_v2"]==row["world_sha256_v37"] and row["observation_sha256_v2"]==row["observation_sha256_v37"] and row["target_sha256_v2"]==row["target_sha256_v37"] for row in rows)
    result={"stage":"V3.7","population":"C37","seed_block":[start,end],"world_count":len(rows),
            "adapter_document_identity":identity,"descriptive_calibration":_external_descriptive(rows),
            "serialization_roundtrip_proof":roundtrip,"custody":ledger,
            "verdict":"PASS" if identity else "FAIL_APPARATUS_STOP"}
    _write_json("v3.7-population-c37.json",result);_write_report("v3.7-population-c37.md","V3.7 Population C37",result);return result


def run_tournament() -> dict[str, Any]:
    if json.loads((RESULTS / "v3.7-population-c37.json").read_text())["verdict"] != "PASS": raise RuntimeError("Population C37 did not pass")
    roundtrip = _run_roundtrip_proof("tournament-t37-preblock", ("external",))
    coherence = _plain(v37.generator_coherence_proof())
    encoded = _canonical(coherence); proof_path=RESULTS/"v3.7-tournament-coherence-proof.jsonl"
    with proof_path.open("xb") as handle: handle.write(encoded);handle.flush();os.fsync(handle.fileno())
    _write_json("v3.7-tournament-coherence-proof-hash.json",{"file":proof_path.name,"sha256":hashlib.sha256(encoded).hexdigest(),"persisted_before_block":True})
    if not coherence["passed"]: raise RuntimeError("tournament coherence proof failed")
    start,end=v37.TOURNAMENT_BLOCK; tasks=[(seed,start,end,"T37") for seed in range(start,end+1)]
    rows,ledger=_persist_rows("v3.7-tournament",tasks,_external_row,1500)
    identity=all(row["document_identity"] for row in rows); pareto={}; failures=[]
    for index,target in enumerate(TARGETS):
        values=[float(row["scores"]["v37"][target])-float(row["scores"]["v2"][target]) for row in rows]
        interval=_bootstrap(values,374000+index);passed=interval[0]>=-DELTA
        pareto[target]={"mean_D":float(np.mean(values)),"interval_95":interval,"delta":DELTA,"passed":passed,
                        "quantiles":[float(x) for x in np.quantile(values,(.01,.05,.5,.95,.99))],
                        "by_stratum":{s:{"mean_D":float(np.mean([float(row["scores"]["v37"][target])-float(row["scores"]["v2"][target]) for row in rows if row["stratum"]==s])),"world_count":sum(row["stratum"]==s for row in rows)} for s in STRATA}}
        if not passed: failures.append(target)
    result={"stage":"V3.7","name":"T37 COMMON-TARGET TOURNAMENT","seed_block":[start,end],"world_count":len(rows),
            "adapter_document_identity":identity,"criterion":{"definition":"lower95[S_V3.7-S_V2] >= -log(1.02) per family","delta":DELTA,"weighted_aggregate_used":False},
            "pareto_vector":pareto,"descriptive_calibration":_external_descriptive(rows),"failed_families":failures,
            "serialization_roundtrip_proof":roundtrip,"custody":ledger,
            "verdict":"PASS" if identity and not failures else ("FAIL_SCIENTIFIC_RETAINED" if identity else "FAIL_APPARATUS_STOP")}
    _write_json("v3.7-tournament-verdict.json",result);_write_report("v3.7-tournament-verdict.md","V3.7 T37 tournament",result);return result


def run_prediction_scoring() -> dict[str, Any]:
    tournament=json.loads((RESULTS/"v3.7-tournament-verdict.json").read_text()); baseline=json.loads((ROOT/"results/V3.6/v3.6-r1-tournament-verdict.json").read_text())
    current=tournament["pareto_vector"]; old=baseline["pareto_vector"]
    rows=[]
    ranges={"partner":(-.02,.05),"contact":(-.05,.02),"identity":(-.06,0.0),"outcome":(-.01,.01)}
    for number,target in enumerate(("partner","contact","identity","outcome"),1):
        value=current[target]["mean_D"]; lo,hi=ranges[target]
        rows.append({"row":number,"prediction":f"{target} mean in [{lo}, {hi}] and family PASS","outcome":value,"family_verdict":current[target]["passed"],"met":lo<=value<=hi and current[target]["passed"]})
    context=value=current["context"]["mean_D"]
    rows.append({"row":5,"prediction":"context within +/-0.03 of +0.269 and PASS","outcome":context,"distance":abs(context-.269),"family_verdict":current["context"]["passed"],"met":abs(context-.269)<=.03 and current["context"]["passed"]})
    strata={target:{s:current[target]["by_stratum"][s]["mean_D"] for s in STRATA} for target in TARGETS}
    spread=max(strata["partner"].values())-min(strata["partner"].values());contact_spread=max(strata["contact"].values())-min(strata["contact"].values())
    commitments=[{"row":1,"prediction":"partner and contact stratum spread < 0.05","partner_spread":spread,"contact_spread":contact_spread,"met":spread<.05 and contact_spread<.05}]
    identity_fractions={s:(strata["identity"][s]-old["identity"]["by_stratum"][s]["mean_D"])/abs(old["identity"]["by_stratum"][s]["mean_D"]) for s in ("acute_one","real_danger_adaptive")}
    commitments.append({"row":2,"prediction":"identity deficit shrinks >=70% in acute_one and real_danger_adaptive; chronic_one remains near its registered baseline","shrinkage_fractions":identity_fractions,"chronic_one_old":old["identity"]["by_stratum"]["chronic_one"]["mean_D"],"chronic_one_new":strata["identity"]["chronic_one"],"met":all(v>=.70 for v in identity_fractions.values()) and abs(strata["identity"]["chronic_one"]-old["identity"]["by_stratum"]["chronic_one"]["mean_D"])<=.03})
    old_acute=old["outcome"]["by_stratum"]["acute_one"]["mean_D"]; shrink=(strata["outcome"]["acute_one"]-old_acute)/abs(old_acute)
    other=[s for s in STRATA if s!="acute_one"]
    commitments.append({"row":3,"prediction":"acute outcome deficit shrinks >=60%; all other strata within +/-0.02","acute_shrinkage_fraction":shrink,"other_values":{s:strata["outcome"][s] for s in other},"met":shrink>=.60 and all(abs(strata["outcome"][s])<=.02 for s in other)})
    commitments.append({"row":4,"prediction":"context recurrent strata >=0.30 and acute_one within +/-0.05 of +0.03","values":strata["context"],"met":all(strata["context"][s]>=.30 for s in ("chronic_one","chronic_multiple")) and abs(strata["context"]["acute_one"]-.03)<=.05})
    partner_improvement=current["partner"]["mean_D"]-old["partner"]["mean_D"]
    falsifiers=[
        {"row":1,"falsifier":"partner improvement less than half the registered V3.6 deficit","improvement":partner_improvement,"half_deficit":abs(old["partner"]["mean_D"])/2,"met":partner_improvement < abs(old["partner"]["mean_D"])/2},
        {"row":2,"falsifier":"context gain drops by more than 0.05","change":current["context"]["mean_D"]-old["context"]["mean_D"],"met":current["context"]["mean_D"] < old["context"]["mean_D"]-.05},
        {"row":3,"falsifier":"identity shows no improvement in real_danger_adaptive","old":old["identity"]["by_stratum"]["real_danger_adaptive"]["mean_D"],"new":strata["identity"]["real_danger_adaptive"],"met":strata["identity"]["real_danger_adaptive"]<=old["identity"]["by_stratum"]["real_danger_adaptive"]["mean_D"]},
    ]
    result={"stage":"V3.7","registered_prediction_sha256":hashlib.sha256((RESULTS/"registered-prediction.md").read_bytes()).hexdigest(),"tournament_verdict_immutable_before_scoring":True,"numbered_prediction_rows":rows,"per_stratum_commitments":commitments,"falsifiers":{"met_means_falsifier_triggered":True,"rows":falsifiers},"verdict":"PREDICTION_SCORED"}
    _write_json("prediction-scoring.json",result);_write_report("prediction-scoring.md","V3.7 registered-prediction scoring",result);return result


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("action",choices=("proofs","a","c","tournament","score","all"));args=parser.parse_args()
    if args.action in ("proofs","all"): run_proofs()
    if args.action in ("a","all"): run_population_a()
    if args.action in ("c","all"): run_population_c()
    if args.action in ("tournament","all"): run_tournament()
    if args.action in ("score","all"): run_prediction_scoring()


if __name__ == "__main__":
    main()
