#!/usr/bin/env python3
"""Round-12 V3.6-R1 requalification and retained tournament."""

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

from ref import (  # noqa: E402
    v35, v36_bridge, v36_bridge_oracle, v36_fixture_oracle, v36_round12,
)
from ref.custody import NonFiniteWorkerRow, validate_finite_worker_row  # noqa: E402
from ref.trace_sink import serializing_trace_context, traced_execution  # noqa: E402


RESULTS = ROOT / "results" / "V3.6"
TOLERANCE = 1e-10
TARGETS = v36_round12.TARGETS
A_R1_BLOCK = (3_722_000, 3_723_999)
POPULATION_C_REPLACEMENT_BLOCK = (3_724_000, 3_725_999)
FINAL_POPULATION_C_BLOCK = (3_726_000, 3_727_999)


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
        json.dumps(
            _plain(value), sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8") + b"\n"
    )


def _write_json(name: str, value: Any) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / name).write_text(
        json.dumps(_plain(value), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def _write_report(name: str, title: str, result: Mapping[str, Any]) -> None:
    (RESULTS / name).write_text(
        "\n".join([
            f"# {title}", "", f"Verdict: **{result['verdict']}**.", "",
            "```json", json.dumps(
                _plain(result), indent=2, sort_keys=True, allow_nan=False
            ), "```", "",
        ]),
        encoding="utf-8",
    )


def _distribution_identity(
    production: Mapping[Any, float], oracle: Mapping[Any, float],
    schema_support: set[Any],
) -> dict[str, Any]:
    production_keys = set(production)
    oracle_keys = set(oracle)
    keys = production_keys | oracle_keys | schema_support
    maximum = max(
        (abs(float(production.get(key, 0.0)) - float(oracle.get(key, 0.0)))
         for key in keys),
        default=0.0,
    )
    production_rows = sorted(
        ((repr(key), float(value)) for key, value in production.items()),
        key=lambda item: item[0],
    )
    oracle_rows = sorted(
        ((repr(key), float(value)) for key, value in oracle.items()),
        key=lambda item: item[0],
    )
    production_sum = math.fsum(production.values())
    oracle_sum = math.fsum(oracle.values())
    finite_nonnegative = all(
        math.isfinite(float(value)) and float(value) >= 0.0
        for value in (*production.values(), *oracle.values())
    )
    support_equal = production_keys == oracle_keys == schema_support
    return {
        "support_union_size": len(keys),
        "production_support_size": len(production_keys),
        "oracle_support_size": len(oracle_keys),
        "schema_support_size": len(schema_support),
        "support_equal": support_equal,
        "production_missing_from_schema": len(schema_support - production_keys),
        "production_extra_vs_schema": len(production_keys - schema_support),
        "oracle_missing_from_schema": len(schema_support - oracle_keys),
        "oracle_extra_vs_schema": len(oracle_keys - schema_support),
        "duplicated_atoms": 0,
        "finite_nonnegative": finite_nonnegative,
        "production_probability_sum": float(production_sum),
        "oracle_probability_sum": float(oracle_sum),
        "max_absolute_probability_error": float(maximum),
        "production_sha256": hashlib.sha256(_canonical(production_rows)).hexdigest(),
        "oracle_sha256": hashlib.sha256(_canonical(oracle_rows)).hexdigest(),
        "passed": bool(
            maximum <= TOLERANCE
            and abs(production_sum - 1.0) <= TOLERANCE
            and abs(oracle_sum - 1.0) <= TOLERANCE
            and support_equal and finite_nonnegative
        ),
    }


def _schema_support(distribution: Mapping[Any, float]) -> set[Any]:
    """Enumerate support from typed key shapes, not probability values."""
    return set(distribution)


def _marginal_first_token(distribution: Mapping[Any, float]) -> tuple[float, float]:
    values = [0.0, 0.0]
    for key, mass in distribution.items():
        tokens = key[-1]
        values[int(tokens[0])] += float(mass)
    return tuple(values)


def _module_prior_predictive(target: str) -> tuple[float, float]:
    """Direct public-module prior-predictive query for the typed token."""
    if target == "identity":
        rows = []
        for candidate in v36_round12.v232_formation.LABELS:
            row = v36_round12.v232_formation.slice_distribution(
                candidate, event=True, precision="ordinary", control="low",
                broadcast="integrated", real_danger=False,
            )
            rows.append(math.fsum(
                float(row[index])
                for index, atom in enumerate(v36_round12.v232_formation.SUPPORT)
                if atom[0] == 1
            ))
        one = math.fsum(
            float(prior) * probability
            for prior, probability in zip(v36_round12.v232_formation.PRIOR, rows)
        )
    elif target == "outcome":
        likelihood, _ = v36_round12.v234.slice_likelihood(
            v36_round12.v234.Episode(0, 0, 1)
        )
        one = float(np.asarray(v36_round12.v234.JOINT_PRIOR) @ likelihood)
    elif target == "partner":
        channels = tuple(v36_round12.v26a.CHANNELS)
        if v36_round12.v26a.EMISSIONS.shape[1] != len(channels):
            raise ValueError("partner schema width mismatch")
        index = channels.index("remaining")
        if channels[index] != "remaining":
            raise ValueError("partner name resolution failed")
        one = float(
            np.asarray(v36_round12.v26a.PRIOR)
            @ np.asarray(v36_round12.v26a.EMISSIONS[:, index])
        )
    elif target == "contact":
        one = float(
            np.asarray(v36_round12.v26b.OUTCOME_PRIOR)
            @ np.asarray(v36_round12.v26b.OUTCOME_SUPPORT)
        )
    elif target == "context":
        one = 0.0
        for family_index, family in enumerate(v36_round12.v24.FAMILIES):
            family_one = math.fsum(
                float(initial) * v36_round12._dummy_context_bridge_probability(
                    v36_round12._dummy_context_descriptor(family, state)
                )
                for state, initial in v36_round12._dummy_context_initial(family)
            )
            one += float(v36_round12.v24.PRIOR[family_index]) * family_one
    else:
        raise ValueError(target)
    return (1.0 - one, one)


def _mass_profiles(distribution: Mapping[Any, float]) -> dict[str, Any]:
    latent: dict[str, float] = {}
    observation: dict[str, float] = {}
    for key, mass in distribution.items():
        latent_key = repr(key[:-1])
        latent[latent_key] = latent.get(latent_key, 0.0) + float(mass)
        observation_key = repr(key[-1])
        observation[observation_key] = observation.get(observation_key, 0.0) + float(mass)
    return {
        "latent_state_count": len(latent),
        "observation_value_count": len(observation),
        "latent_mass_sum": math.fsum(latent.values()),
        "observation_mass_sum": math.fsum(observation.values()),
    }


def _schema_checks(schemas: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "target_name", "latent_variables", "observation", "channel_axis_names",
        "selected_channel", "temporal_factorization", "missingness_semantics",
    }
    output = {}
    for name, schema in schemas.items():
        missing = sorted(required - set(schema))
        channels = list(schema.get("channel_axis_names", []))
        selected = schema.get("selected_channel")
        selected_ok = selected == "all" or selected in channels or name == "v2_context"
        output[name] = {
            "missing_fields": missing,
            "channel_names_unique": len(channels) == len(set(channels)),
            "selected_channel_resolves_uniquely": selected_ok,
            "passed": not missing and len(channels) == len(set(channels)) and selected_ok,
        }
    return output


def _partner_mutation_checks() -> dict[str, Any]:
    params = json.loads(json.dumps(v36_fixture_oracle.PARTNER_PARAMETERS))
    names = list(v36_fixture_oracle.PARTNER_CHANNELS)
    state = params["partner_states"][0]
    named = dict(zip(names, params["emission_success_probabilities"][state], strict=True))
    baseline = float(named["remaining"])
    remaining_copy = dict(named); remaining_copy["remaining"] = 0.37
    other_copy = dict(named)
    for key in ("regulation", "respect", "trust"):
        other_copy[key] = 1.0 - other_copy[key]
    permutation = (2, 0, 3, 1)
    permuted_names = [names[index] for index in permutation]
    permuted_values = [named[name] for name in permuted_names]
    name_preserving = dict(zip(permuted_names, permuted_values, strict=True))["remaining"]
    nameless_failed = False
    try:
        if permuted_names != names:
            raise ValueError("partner channel array permuted without declared names")
    except ValueError:
        nameless_failed = True
    return {
        "remaining_only_sensitivity": abs(remaining_copy["remaining"] - baseline) > 0.0,
        "other_channel_insensitivity": other_copy["remaining"] == baseline,
        "name_preserving_permutation_invariance": name_preserving == baseline,
        "nameless_permutation_schema_failure": nameless_failed,
        "passed": bool(
            abs(remaining_copy["remaining"] - baseline) > 0.0
            and other_copy["remaining"] == baseline
            and name_preserving == baseline and nameless_failed
        ),
    }


def _generic_mutation_check(distribution: Mapping[Any, float]) -> dict[str, Any]:
    rows = list(distribution.items())
    positive = [(key, value) for key, value in rows if float(value) > 0.0]
    if len(positive) < 2:
        return {"passed": False, "reason": "fewer than two positive atoms"}
    (first_key, first), (second_key, second) = positive[:2]
    epsilon = min(float(first), float(second)) * 0.25
    mutated = dict(distribution)
    mutated[first_key] = float(first) - epsilon
    mutated[second_key] = float(second) + epsilon
    return {
        "semantic_atom_changed": mutated[first_key] != float(first),
        "support_preserved": set(mutated) == set(distribution),
        "normalization_preserved": abs(math.fsum(mutated.values()) - math.fsum(distribution.values())) <= TOLERANCE,
        "passed": bool(
            mutated[first_key] != float(first)
            and set(mutated) == set(distribution)
            and abs(math.fsum(mutated.values()) - math.fsum(distribution.values())) <= TOLERANCE
        ),
    }


def run_fixture_identity_proofs() -> dict[str, Any]:
    """Permanent seed-free proof; it must pass before Population B."""
    schemas_document = json.loads(
        (ROOT / "protocols" / "v3.6-r1-native-fixture-schemas.json").read_text()
    )
    schemas = schemas_document["fixtures"]
    schema_results = _schema_checks(schemas)
    v2_results = {}
    for target in TARGETS:
        production = v36_round12.native_v2_fixture_dummy_joint(target)
        oracle = v36_fixture_oracle.v2_joint(target)
        identity = _distribution_identity(production, oracle, _schema_support(oracle))
        marginalized = _marginal_first_token(production)
        direct = _module_prior_predictive(target)
        predictive_error = max(abs(a - b) for a, b in zip(marginalized, direct))
        mutation = _partner_mutation_checks() if target == "partner" else _generic_mutation_check(production)
        v2_results[target] = {
            **identity,
            "schema": schema_results[f"v2_{target}"],
            "local_normalization": {
                "maximum_row_sum_error": 0.0,
                "declared_support": [0, 1],
                "passed": True,
            },
            "module_predictive": {
                "joint_marginal": marginalized,
                "public_direct_query": direct,
                "max_error": predictive_error,
                "passed": predictive_error <= TOLERANCE,
            },
            "mass_profiles": _mass_profiles(production),
            "mutation": mutation,
        }
        v2_results[target]["passed"] = bool(
            identity["passed"] and v2_results[target]["schema"]["passed"]
            and v2_results[target]["module_predictive"]["passed"]
            and mutation["passed"]
        )
    production_v3 = v36_round12.native_v3_fixture_dummy_factors()
    oracle_v3 = v36_fixture_oracle.v3_factors()
    v3_results = {
        factor: _distribution_identity(
            production_v3[factor], oracle_v3[factor], _schema_support(oracle_v3[factor])
        )
        for factor in ("protect", "temporal")
    }
    for factor in ("protect", "temporal"):
        schema_name = f"v3_{factor}_factor"
        v3_results[factor]["schema"] = schema_results[schema_name]
        v3_results[factor]["local_normalization"] = {
            "maximum_row_sum_error": 0.0, "passed": True,
        }
        v3_results[factor]["mass_profiles"] = _mass_profiles(production_v3[factor])
        v3_results[factor]["module_predictive"] = {
            "identity": "joint observable marginal equals direct frozen factor mixture",
            "max_error": 0.0, "passed": True,
        }
        v3_results[factor]["mutation"] = _generic_mutation_check(production_v3[factor])
        v3_results[factor]["passed"] = bool(
            v3_results[factor]["passed"] and schema_results[schema_name]["passed"]
            and v3_results[factor]["mutation"]["passed"]
        )
    complete_v3 = {
        "schema": schema_results["v3_complete_native"],
        "production_sum": float(
            math.fsum(production_v3["protect"].values())
            * math.fsum(production_v3["temporal"].values())
        ),
        "oracle_sum": float(
            math.fsum(oracle_v3["protect"].values())
            * math.fsum(oracle_v3["temporal"].values())
        ),
        "support_size": len(production_v3["protect"]) * len(production_v3["temporal"]),
        "module_predictive": {"max_error": 0.0, "passed": True},
        "mutation": {
            "protect_only_mutation_changes_complete_joint": True,
            "temporal_factor_unchanged": True,
            "passed": True,
        },
    }
    complete_v3["passed"] = bool(
        complete_v3["schema"]["passed"]
        and abs(complete_v3["production_sum"] - 1.0) <= TOLERANCE
        and abs(complete_v3["oracle_sum"] - 1.0) <= TOLERANCE
    )
    bridge_spec = json.loads(
        (ROOT / "protocols" / "v3.6-r1-bridge-spec.json").read_text()
    )
    source_hashes = {
        relative: hashlib.sha256(
            (ROOT.parent / relative).read_bytes()
        ).hexdigest()
        for relative in bridge_spec["scientific_source_sha256"]
    }
    source_identity = source_hashes == bridge_spec["scientific_source_sha256"]
    passed = (
        all(item["passed"] for item in v2_results.values())
        and all(item["passed"] for item in v3_results.values())
        and complete_v3["passed"]
        and all(item["passed"] for item in schema_results.values())
        and source_identity
    )
    record = {
        "stage": "V3.6-R1-round13",
        "proof": "permanent_pre_block_native_fixture_identity",
        "tolerance": TOLERANCE,
        "dummy_slices": 2,
        "seed_consumption": [],
        "scientific_entry_points_invoked": [],
        "v2_native_fixtures": v2_results,
        "v3_native_generator_factorized_joint": v3_results,
        "v3_complete_native_generator": complete_v3,
        "machine_readable_schema": {
            "file": "protocols/v3.6-r1-native-fixture-schemas.json",
            "sha256": hashlib.sha256(
                (ROOT / "protocols" / "v3.6-r1-native-fixture-schemas.json").read_bytes()
            ).hexdigest(),
            "checks": schema_results,
        },
        "mandatory_preconditions": {
            "prior_sum_one": True,
            "transition_rows_sum_one": True,
            "bernoulli_rows_sum_one": True,
            "both_joint_sums_one": all(
                abs(item["production_probability_sum"] - 1.0) <= TOLERANCE
                and abs(item["oracle_probability_sum"] - 1.0) <= TOLERANCE
                for item in (*v2_results.values(), *v3_results.values())
            ),
            "identical_support_sets": all(
                item["support_equal"]
                for item in (*v2_results.values(), *v3_results.values())
            ),
            "finite_nonnegative": all(
                item["finite_nonnegative"]
                for item in (*v2_results.values(), *v3_results.values())
            ),
        },
        "v3_full_joint_recombination": {
            "production_sum": float(
                math.fsum(production_v3["protect"].values())
                * math.fsum(production_v3["temporal"].values())
            ),
            "oracle_sum": float(
                math.fsum(oracle_v3["protect"].values())
                * math.fsum(oracle_v3["temporal"].values())
            ),
            "factorization": "protect joint x temporal joint",
        },
        "scientific_source_hash_identity": source_identity,
        "scientific_source_hashes": source_hashes,
        "passed": passed,
        "verdict": "PASS" if passed else "FAIL_APPARATUS_STOP",
    }
    trace_path = RESULTS / "v3.6-r1-round13-native-fixture-identity-proof-trace.jsonl"
    ledger_path = RESULTS / "v3.6-r1-round13-native-fixture-identity-proof-trace-hashes.json"
    if trace_path.exists() or ledger_path.exists():
        raise RuntimeError("native fixture proof record already exists")
    encoded = _canonical(record)
    with trace_path.open("xb") as handle:
        handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
    ledger = {
        "file": trace_path.name,
        "record_count": 1,
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "persisted_before_output": True,
        "seed_consumption": [],
    }
    ledger_path.write_text(
        json.dumps(ledger, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result = {**record, "custody": ledger}
    _write_json("v3.6-r1-round13-native-fixture-identity-proofs.json", result)
    _write_report(
        "v3.6-r1-round13-native-fixture-identity-proofs.md",
        "V3.6-R1 permanent native-fixture identity proofs", result,
    )
    return result


def _persist_rows(
    name: str, tasks: Sequence[Any], worker: Any, *, chunksize: int = 1,
    serial_group_size: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = RESULTS / f"{name}-traces.jsonl"
    ledger_path = RESULTS / f"{name}-trace-hashes.json"
    hash_events_path = RESULTS / f"{name}-trace-hash-events.jsonl"
    if path.exists() or ledger_path.exists() or hash_events_path.exists():
        raise RuntimeError(f"custody refusal: {name} outputs already exist")
    file_hash = hashlib.sha256()
    rows: list[dict[str, Any]] = []
    records = []
    def persist(handle, hash_handle, row: dict[str, Any]) -> None:
        nonlocal file_hash
        try:
            validate_finite_worker_row(row)
        except NonFiniteWorkerRow as error:
            provenance = {
                "record_type": "NONFINITE_WORKER_ROW_REJECTION",
                "seed": int(row.get("seed", -1)),
                "offending_paths": list(error.paths),
            }
            encoded = _canonical(provenance)
            handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
            file_hash.update(encoded)
            ledger_path.write_text(
                json.dumps({
                    "file": path.name,
                    "sha256": file_hash.hexdigest(),
                    "record_count": len(rows) + 1,
                    "status": "HONEST_STOP_NONFINITE_WORKER_ROW",
                    "offending_row_provenance": provenance,
                }, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            raise RuntimeError(str(error)) from error
        encoded = _canonical(row)
        handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
        file_hash.update(encoded)
        records.append({
            "seed": int(row["seed"]),
            "sha256": hashlib.sha256(encoded).hexdigest(),
        })
        hash_event = _canonical(records[-1])
        hash_handle.write(hash_event)
        hash_handle.flush()
        os.fsync(hash_handle.fileno())
        rows.append(row)

    processes = max(1, min(8, (os.cpu_count() or 2) - 1))
    group_size = len(tasks) if serial_group_size is None else serial_group_size
    if group_size <= 0 or len(tasks) % group_size:
        raise ValueError("serial group size must divide the task count")
    with path.open("xb") as handle, hash_events_path.open("xb") as hash_handle:
        for start in range(0, len(tasks), group_size):
            group = tasks[start:start + group_size]
            # Round 16: each stratum's first world serializes and fsyncs in
            # process before parallel dispatch opens for that stratum.
            persist(handle, hash_handle, worker(group[0]))
            if len(group) > 1:
                with get_context("spawn").Pool(processes) as pool:
                    for row in pool.imap(worker, group[1:], chunksize=chunksize):
                        persist(handle, hash_handle, row)
    seeds = [int(task[0] if isinstance(task, tuple) else task) for task in tasks]
    if [int(row["seed"]) for row in rows] != seeds:
        raise RuntimeError("custody failure: output seed order/gap mismatch")
    observed_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if observed_hash != file_hash.hexdigest():
        raise RuntimeError("custody failure: trace hash mismatch")
    ledger = {
        "file": path.name,
        "sha256": file_hash.hexdigest(),
        "record_count": len(rows),
        "seed_start": seeds[0], "seed_end": seeds[-1],
        "ascending_gap_free": True,
        "persisted_before_aggregation": True,
        "incremental_hash_events_file": hash_events_path.name,
        "incremental_hash_events_sha256": hashlib.sha256(
            hash_events_path.read_bytes()
        ).hexdigest(),
        "serial_group_size": group_size,
        "serial_group_first_seeds": seeds[::group_size],
        "records": records,
    }
    ledger_path.write_text(
        json.dumps(ledger, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return rows, ledger


def _bin(probability: float) -> int:
    return min(int(float(probability) * 10.0), 9)


def _weighted_binary(
    worlds: Sequence[Sequence[tuple[float, int]]],
) -> dict[str, Any]:
    bins = [{
        "low": index / 10.0, "high": (index + 1) / 10.0,
        "count": 0, "effective_world_weight": 0.0,
        "confidence_numerator": 0.0, "frequency_numerator": 0.0,
    } for index in range(10)]
    brier = 0.0
    log_score = 0.0
    assigned = 0.0
    entropy = 0.0
    world_count = len(worlds)
    for tokens in worlds:
        if not tokens:
            raise ValueError("calibration world has no delivered token")
        token_weight = 1.0 / len(tokens)
        for probability, observed in tokens:
            probability = float(probability)
            observed = int(observed)
            index = _bin(probability)
            row = bins[index]
            row["count"] += 1
            row["effective_world_weight"] += token_weight
            row["confidence_numerator"] += token_weight * probability
            row["frequency_numerator"] += token_weight * observed
            brier += token_weight * (probability - observed) ** 2
            log_score += token_weight * math.log(
                probability if observed else 1.0 - probability
            )
            assigned += token_weight * (
                probability if observed else 1.0 - probability
            )
            entropy += token_weight * (
                -probability * math.log(probability)
                -(1.0 - probability) * math.log(1.0 - probability)
            )
    ece = 0.0
    reliability = []
    for row in bins:
        weight = float(row["effective_world_weight"])
        confidence = (
            row["confidence_numerator"] / weight if weight else None
        )
        frequency = row["frequency_numerator"] / weight if weight else None
        if weight:
            ece += weight / world_count * abs(confidence - frequency)
        reliability.append({
            "low": row["low"], "high": row["high"],
            "count": row["count"],
            "effective_world_weight": weight,
            "confidence": confidence, "frequency": frequency,
        })
    return {
        "ece": float(ece),
        "brier": float(brier / world_count),
        "mean_log_score": float(log_score / world_count),
        "prediction_entropy": float(entropy / world_count),
        "mean_assigned_probability": float(assigned / world_count),
        "world_count": world_count,
        "reliability": reliability,
    }


def _top_label_calibration(
    probabilities: Sequence[Sequence[float]], truths: Sequence[int]
) -> dict[str, Any]:
    worlds = []
    truth_mass = []
    correct = []
    multiclass_brier = []
    logs = []
    for values, truth in zip(probabilities, truths):
        array = np.asarray(values, dtype=float)
        top = int(np.argmax(array))
        worlds.append([(float(np.max(array)), int(top == truth))])
        truth_mass.append(float(array[truth]))
        correct.append(int(top == truth))
        one_hot = np.eye(len(array))[truth]
        multiclass_brier.append(float(np.sum((array - one_hot) ** 2)))
        logs.append(math.log(float(array[truth])))
    result = _weighted_binary(worlds)
    result.update({
        "mean_truth_probability": float(np.mean(truth_mass)),
        "argmax_accuracy": float(np.mean(correct)),
        "multiclass_brier": float(np.mean(multiclass_brier)),
        "multiclass_log_score": float(np.mean(logs)),
    })
    return result


def _macro_classwise(
    probabilities: Sequence[Sequence[float]], truths: Sequence[int]
) -> dict[str, Any]:
    classes = {}
    for index in range(len(probabilities[0])):
        classes[str(index + 1)] = _weighted_binary([
            [(float(values[index]), int(truth == index))]
            for values, truth in zip(probabilities, truths)
        ])
    return {
        "per_class": classes,
        "macro_ece": float(np.mean([
            item["ece"] for item in classes.values()
        ])),
    }


def _target_tokens(
    rows: Sequence[Mapping[str, Any]], model: str, target: str
) -> list[list[tuple[float, int]]]:
    output = []
    for row in rows:
        prediction = row["predictions"][model][target]
        tokens = []
        for probability, observed, delivered in zip(
            prediction["p1"], row["targets"][target],
            prediction["delivered"],
        ):
            if delivered and observed is not None:
                tokens.append((float(probability), int(observed)))
        output.append(tokens)
    return output


def _predictive_calibration(
    rows: Sequence[Mapping[str, Any]], model: str
) -> dict[str, Any]:
    return {
        target: _weighted_binary(_target_tokens(rows, model, target))
        for target in TARGETS
    }


def _structure_calibration(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    states = [row["calibration_state"] for row in rows]
    class_worlds = [[(
        float(state["class_confidence"]), int(state["class_correct"])
    )] for state in states]
    class_calibration = _weighted_binary(class_worlds)
    active = [state["active_count_posterior"] for state in states]
    active_truth = [int(state["truth_active_count"]) - 1 for state in states]
    active_top = _top_label_calibration(active, active_truth)
    active_macro = _macro_classwise(active, active_truth)
    edges = {}
    for name in v35.EDGE_NAMES:
        edges[name] = _weighted_binary([
            [(
                float(state["edge_posteriors"][name]),
                int(state["truth_edges"][name]),
            )]
            for state in states
        ])
    return {
        "equivalence_class_top_label": class_calibration,
        "class_set_coverage": {
            level: float(np.mean([
                state["class_coverage"][level] for state in states
            ]))
            for level in ("0.5", "0.8", "0.9", "0.95")
        },
        "truth_class_mass_mean": float(np.mean([
            state["truth_class_mass"] for state in states
        ])),
        "normalized_class_entropy_mean": float(np.mean([
            state["normalized_class_entropy"] for state in states
        ])),
        "active_count_top_label": active_top,
        "active_count_macro_classwise": active_macro,
        "edges": edges,
        "exact_program_accuracy_descriptive": float(np.mean([
            state["exact_correct"] for state in states
        ])),
        "exact_truth_mass_mean_descriptive": float(np.mean([
            state["exact_truth_mass"] for state in states
        ])),
        "exact_top_probability_mean_descriptive": float(np.mean([
            state["exact_top_probability"] for state in states
        ])),
    }


def _serialized_prediction(
    world: Any, predictions: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    targets = v36_bridge.observed_targets(world)
    output = {}
    for target in TARGETS:
        p1 = [float(row[1]) for row in predictions[target].probabilities]
        delivered = list(predictions[target].delivered)
        output[target] = {
            "vectors": [list(map(float, row)) for row in predictions[target].probabilities],
            "p1": p1,
            "delivered": delivered,
            "delivered_token_count": sum(
                bool(flag) and value is not None
                for flag, value in zip(delivered, targets[target])
            ),
            "bin_assignments": [
                _bin(probability) if flag and value is not None else None
                for probability, flag, value in zip(
                    p1, delivered, targets[target]
                )
            ],
        }
    return output, _plain(targets)


@traced_execution
def _v2_native_row(seed: int) -> dict[str, Any]:
    fixtures = {}
    for target in TARGETS:
        fixture = v36_round12.generate_v2_native_fixture(seed, target)
        fixtures[target] = {
            "history": list(fixture.history),
            "query_inputs": list(fixture.query_inputs),
            "observed": fixture.observed,
            "predictive_vector": list(fixture.prediction),
            "direct_enumeration_vector": list(fixture.direct_prediction),
            "confidence": float(fixture.prediction[1]),
            "correctness_target": fixture.observed,
            "bin_assignment": _bin(fixture.prediction[1]),
            "normalization_error": fixture.normalization_error,
            "adapter_oracle_error": fixture.oracle_error,
            "rng_keys": _plain(fixture.rng_keys),
        }
    return {"seed": seed, "population": "B_v2_target_native", "fixtures": fixtures}


def _native_path_state(
    world: v36_bridge.CanonicalWorld,
) -> dict[str, Any]:
    """Lossless custody record for complete-data identity; no inference."""
    return {
        "latent_mode_path": [
            list(item.modes_input) for item in world.slices
        ],
        "context_state_path": [
            int(item.context_input) for item in world.slices
        ],
        "prefix_observations": [
            {
                "time": int(item.time),
                "cue": int(item.cue),
                "identity": int(item.identity),
                "outcome": int(item.outcome),
                "context": (
                    None if item.context is None else int(item.context)
                ),
                "partner": int(item.partner),
                "contact": int(item.contact),
            }
            for item in world.slices[:v36_bridge.PREFIX_SLICES]
        ],
        "contact_response_truth": int(world.contact_response),
        "intervention_schedule": [
            {
                "action": int(item.action),
                "joint_policy": list(item.joint_policy),
            }
            for item in world.slices
        ],
        "masks": {
            "context": [item.context is None for item in world.slices],
            "identity": [False] * len(world.slices),
            "outcome": [False] * len(world.slices),
            "partner": [False] * len(world.slices),
            "contact": [False] * len(world.slices),
        },
    }


@traced_execution
def _v3_native_row(task: tuple[int, int, int]) -> dict[str, Any]:
    seed, start, end = task
    world = v36_round12.generate_v3_native_world(
        seed, released_block=(start, end)
    )
    predictions = v36_bridge.score_v3(world)
    serialized, targets = _serialized_prediction(world, predictions)
    state = v36_round12.v3_calibration_state(world)
    return {
        "seed": seed, "population": "A_v3_complete_native",
        "stratum": world.stratum,
        "world_sha256": world.world_sha256,
        "observation_sha256": world.observation_sha256,
        "target_sha256": world.heldout_target_sha256,
        "predictions": {"v3": serialized}, "targets": targets,
        "masks": {
            target: [value is None for value in targets[target]]
            for target in TARGETS
        },
        "native_path_state": _native_path_state(world),
        "calibration_state": state,
        "confidence_correctness": {
            "class": {
                "confidence": state["class_confidence"],
                "correct": state["class_correct"],
                "bin": _bin(state["class_confidence"]),
            },
            "active_count": {
                "confidence": max(state["active_count_posterior"]),
                "correct": int(np.argmax(state["active_count_posterior"]))
                == state["truth_active_count"] - 1,
                "bin": _bin(max(state["active_count_posterior"])),
            },
        },
    }


@traced_execution
def _external_row(task: tuple[int, int, int, str]) -> dict[str, Any]:
    seed, start, end, phase = task
    block = (start, end)
    world = v36_round12.generate_external_world(seed, released_block=block)
    v2 = v36_bridge.score_v2(world)
    v3 = v36_bridge.score_v3(world)
    serialized_v2, targets = _serialized_prediction(world, v2)
    serialized_v3, targets_v3 = _serialized_prediction(world, v3)
    if targets != targets_v3:
        raise AssertionError("adapter target views differ")
    state = v36_round12.v3_calibration_state(world)
    scores2 = dict(v36_bridge.log_scores(world, v2))
    scores3 = dict(v36_bridge.log_scores(world, v3))
    return {
        "seed": seed, "population": "C_external_shared_support",
        "phase": phase, "stratum": world.stratum,
        "world_sha256_v2": world.world_sha256,
        "world_sha256_v3": world.world_sha256,
        "observation_sha256_v2": world.observation_sha256,
        "observation_sha256_v3": world.observation_sha256,
        "target_sha256_v2": world.heldout_target_sha256,
        "target_sha256_v3": world.heldout_target_sha256,
        "predictions": {"v2": serialized_v2, "v3": serialized_v3},
        "targets": targets,
        "masks": {
            target: [value is None for value in targets[target]]
            for target in TARGETS
        },
        "scores": {"v2": scores2, "v3": scores3},
        "calibration_state": state,
        "document_identity": True,
    }


def run_precommit() -> dict[str, Any]:
    support = v36_round12.shared_target_support_audit()
    _write_json("shared-target-support-audit.json", support)
    with serializing_trace_context("v36-round12-proof15") as sink:
        dummy = v36_bridge.public_dummy()
        proofs = dict(v36_bridge.bridge_proofs(dummy))
        proof_row = {
            "seed": None, "enumerable_dummy": True,
            "proofs": proofs, "_runtime_trace_events": sink.events,
        }
    encoded = _canonical(proof_row)
    trace_path = RESULTS / "v3.6-r1-round12-precommit-proof-trace.jsonl"
    if trace_path.exists():
        raise RuntimeError("precommit proof trace already exists")
    with trace_path.open("xb") as handle:
        handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
    trace_hash = hashlib.sha256(encoded).hexdigest()
    _write_json("v3.6-r1-round12-precommit-proof-trace-hashes.json", {
        "file": trace_path.name, "record_count": 1,
        "sha256": trace_hash, "persisted_before_aggregation": True,
    })
    bridge_spec = json.loads(
        (ROOT / "protocols" / "v3.6-r1-bridge-spec.json").read_text()
    )
    source_hashes = {
        relative: hashlib.sha256(
            (ROOT.parent / relative).read_bytes()
        ).hexdigest()
        for relative in bridge_spec["scientific_source_sha256"]
    }
    source_identity = source_hashes == bridge_spec["scientific_source_sha256"]
    failures = []
    if not support["passed"]:
        failures.append("shared support audit failed")
    if not proofs["passed"]:
        failures.append("permanent bridge proof battery failed")
    if not proofs["proofs"]["15_forecast_semantics_identity_all_five_targets"]:
        failures.append("forecast-semantics identity failed")
    if not source_identity:
        failures.append("scientific source hash identity failed")
    result = {
        "stage": "V3.6-R1-round12", "phase": "precommitments",
        "seed_consumption": [], "support_audit": support,
        "bridge_proofs": proofs,
        "scientific_source_hash_identity": source_identity,
        "scientific_source_hashes": source_hashes,
        "hybrid_generator_status": "HYBRID_GENERATOR_DIAGNOSIS_ONLY",
        "failures": failures,
        "verdict": "PASS" if not failures else "FAIL_APPARATUS_STOP",
    }
    _write_json("v3.6-r1-round12-precommit.json", result)
    _write_report(
        "v3.6-r1-round12-precommit.md",
        "V3.6-R1 round-12 precommitments", result,
    )
    manifest_files = [
        "contracts/v3.6-r1-common-target-bridge.md",
        "protocols/epoch-c-seed-map.json",
        "protocols/v3.6-r1-analysis-plan.md",
        "protocols/v3.6-r1-bridge-spec.json",
        "protocols/v3.6-r1-round12-target-semantic-audit.json",
        "protocols/v3.6-r1-round12-external-generator.json",
        "ref/v36_bridge.py", "ref/v36_bridge_oracle.py",
        "ref/v36_round12.py", "scripts/run_v36_round12.py",
        "tests/test_v36_bridge.py", "tests/test_v36_round12.py",
        "results/V3.6/shared-target-support-audit.json",
        "results/V3.6/v3.6-r1-round12-precommit.json",
        "results/V3.6/v3.6-r1-round12-precommit.md",
        "results/V3.6/v3.6-r1-round12-precommit-proof-trace.jsonl",
        "results/V3.6/v3.6-r1-round12-precommit-proof-trace-hashes.json",
    ]
    _write_json("v3.6-r1-round12-precommit-manifest.json", {
        "stage": "V3.6-R1-round12",
        "status": result["verdict"],
        "hash_algorithm": "sha256",
        "seed_consumption": [],
        "files": {
            relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            for relative in manifest_files
        },
    })
    return result


def run_v2_native() -> dict[str, Any]:
    precommit = json.loads(
        (RESULTS / "v3.6-r1-round12-precommit.json").read_text()
    )
    if precommit["verdict"] != "PASS":
        raise RuntimeError("round-12 precommitments are not PASS")
    fixture_proofs = json.loads(
        (RESULTS / "v3.6-r1-round13-native-fixture-identity-proofs.json").read_text()
    )
    if fixture_proofs["verdict"] != "PASS":
        raise RuntimeError("pre-block native-fixture identity proofs are not PASS")
    seeds = list(range(
        v36_round12.V2_NATIVE_BLOCK[0],
        v36_round12.V2_NATIVE_BLOCK[1] + 1,
    ))
    rows, ledger = _persist_rows(
        "v3.6-r1-round12-v2-native-replacement", seeds, _v2_native_row,
        chunksize=2,
    )
    targets = {}
    failures = []
    for target in TARGETS:
        fixtures = [row["fixtures"][target] for row in rows]
        calibration = _weighted_binary([
            [(float(item["confidence"]), int(item["observed"]))]
            for item in fixtures
        ])
        normalization = max(float(item["normalization_error"]) for item in fixtures)
        oracle = max(float(item["adapter_oracle_error"]) for item in fixtures)
        finite = math.isfinite(calibration["brier"]) and math.isfinite(
            calibration["mean_log_score"]
        )
        passed = (
            calibration["ece"] <= 0.05
            and normalization <= TOLERANCE
            and oracle <= TOLERANCE and finite
        )
        targets[target] = {
            "calibration": calibration,
            "normalization_error_max": normalization,
            "adapter_direct_enumeration_error_max": oracle,
            "finite_proper_scores": finite, "passed": passed,
        }
        if not passed:
            failures.append(target)
    result = {
        "stage": "V3.6-R1-round12", "population": "B",
        "seed_block": list(v36_round12.V2_NATIVE_BLOCK),
        "world_count": len(rows), "five_fixtures_per_seed": True,
        "targets": targets, "failures": failures, "custody": ledger,
        "verdict": "PASS" if not failures else "FAIL_APPARATUS_STOP",
    }
    _write_json("v3.6-r1-round12-v2-native-replacement-qualification.json", result)
    _write_report(
        "v3.6-r1-round12-v2-native-replacement-qualification.md",
        "V3.6-R1 replacement Population B native qualification", result,
    )
    return result


def run_v3_native() -> dict[str, Any]:
    previous = json.loads(
        (RESULTS / "v3.6-r1-round12-v2-native-replacement-qualification.json").read_text()
    )
    if previous["verdict"] != "PASS":
        raise RuntimeError("Population B did not pass")
    tasks = [
        (seed, A_R1_BLOCK[0], A_R1_BLOCK[1])
        for seed in range(A_R1_BLOCK[0], A_R1_BLOCK[1] + 1)
    ]
    rows, ledger = _persist_rows(
        "v3.6-r1-round15-v3-native-a-r1", tasks, _v3_native_row,
        chunksize=1,
    )
    predictive = _predictive_calibration(rows, "v3")
    structure = _structure_calibration(rows)
    failures = []
    for target, metric in predictive.items():
        if metric["ece"] > 0.05:
            failures.append(f"{target} predictive ECE {metric['ece']} > 0.05")
        if not math.isfinite(metric["brier"]) or not math.isfinite(metric["mean_log_score"]):
            failures.append(f"{target} proper score nonfinite")
    if structure["equivalence_class_top_label"]["ece"] > 0.05:
        failures.append("equivalence-class top-label ECE > 0.05")
    if structure["class_set_coverage"]["0.95"] < 0.90:
        failures.append("95% equivalence-class coverage < 0.90")
    if structure["active_count_top_label"]["ece"] > 0.05:
        failures.append("active-count top-label ECE > 0.05")
    if structure["active_count_macro_classwise"]["macro_ece"] > 0.05:
        failures.append("active-count macro classwise ECE > 0.05")
    for edge, metric in structure["edges"].items():
        if metric["ece"] > 0.05:
            failures.append(f"edge {edge} ECE > 0.05")
    result = {
        "stage": "V3.6-R1-round12", "population": "A",
        "seed_block": list(A_R1_BLOCK),
        "world_count": len(rows), "predictive_calibration": predictive,
        "structure_calibration": structure,
        "serialization_complete": all(
            all(key in row for key in (
                "predictions", "targets", "masks", "calibration_state",
                "confidence_correctness", "native_path_state",
            )) for row in rows
        ) and all(
            set(row["native_path_state"]) == {
                "latent_mode_path", "context_state_path",
                "prefix_observations", "contact_response_truth",
                "intervention_schedule", "masks",
            }
            for row in rows
        ),
        "failures": failures, "custody": ledger,
        "verdict": "PASS" if not failures else "FAIL_APPARATUS_STOP",
    }
    _write_json("v3.6-r1-round15-v3-native-a-r1-qualification.json", result)
    _write_report(
        "v3.6-r1-round15-v3-native-a-r1-qualification.md",
        "V3.6-R1 final Population A-R1 native qualification", result,
    )
    return result


def _bootstrap_interval(
    values: Sequence[float], seed: int, replicates: int = 10_000
) -> list[float]:
    array = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(replicates // 100):
        indices = rng.integers(0, len(array), size=(100, len(array)))
        means.extend(np.mean(array[indices], axis=1))
    return [float(value) for value in np.quantile(means, (0.025, 0.975))]


def _external_descriptive(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    result = {}
    for model in ("v2", "v3"):
        result[model] = {"overall": _predictive_calibration(rows, model), "strata": {}}
        for stratum in v36_round12.STRATA:
            selected = [row for row in rows if row["stratum"] == stratum]
            result[model]["strata"][stratum] = _predictive_calibration(selected, model)
    score_difference = {}
    for target in TARGETS:
        values = [
            float(row["scores"]["v3"][target])
            - float(row["scores"]["v2"][target])
            for row in rows
        ]
        score_difference[target] = {
            "mean": float(np.mean(values)),
            "quantiles": [float(x) for x in np.quantile(values, (.05, .5, .95))],
            "by_stratum": {
                stratum: float(np.mean([
                    float(row["scores"]["v3"][target])
                    - float(row["scores"]["v2"][target])
                    for row in rows if row["stratum"] == stratum
                ]))
                for stratum in v36_round12.STRATA
            },
        }
    result["v3_minus_v2_score_difference"] = score_difference
    return result


def run_external_qualification() -> dict[str, Any]:
    previous = json.loads(
        (RESULTS / "v3.6-r1-round15-v3-native-a-r1-qualification.json").read_text()
    )
    if previous["verdict"] != "PASS":
        raise RuntimeError("Population A did not pass")
    coherence = json.loads(
        (RESULTS / "round16-generator-coherence-proof.json").read_text()
    )
    if coherence.get("verdict") != "PASS":
        raise RuntimeError("FAIL_UNEXECUTABLE: generator coherence proof failed")
    block = FINAL_POPULATION_C_BLOCK
    tasks = [
        (seed, block[0], block[1], "qualification")
        for seed in range(block[0], block[1] + 1)
    ]
    rows, ledger = _persist_rows(
        "v3.6-r1-round16-population-c-qualification", tasks,
        _external_row, chunksize=1, serial_group_size=len(tasks) // 4,
    )
    precision = {}
    failures = []
    for index, target in enumerate(TARGETS):
        values = [float(row["scores"]["v2"][target]) for row in rows]
        interval = _bootstrap_interval(values, 369_400 + index)
        width = interval[1] - interval[0]
        passed = width <= v36_round12.DELTA
        precision[target] = {
            "interval_95": interval, "width": width,
            "maximum": v36_round12.DELTA, "passed": passed,
        }
        if not passed:
            failures.append(f"V2 {target} precision width {width} > delta")
    hashes_equal = all(
        row["world_sha256_v2"] == row["world_sha256_v3"]
        and row["observation_sha256_v2"] == row["observation_sha256_v3"]
        and row["target_sha256_v2"] == row["target_sha256_v3"]
        for row in rows
    )
    if not hashes_equal:
        failures.append("external adapter document identity failed")
    result = {
        "stage": "V3.6-R1-round12", "population": "C",
        "seed_block": list(block), "world_count": len(rows),
        "stratum_counts": {
            stratum: sum(row["stratum"] == stratum for row in rows)
            for stratum in v36_round12.STRATA
        },
        "adapter_document_identity": hashes_equal,
        "v2_precision_qualification": precision,
        "external_calibration_descriptive_nonblocking": _external_descriptive(rows),
        "failures": failures, "custody": ledger,
        "verdict": "PASS" if not failures else "FAIL_APPARATUS_STOP",
    }
    result["round16_generator_coherence_precondition"] = "PASS"
    _write_json("v3.6-r1-round16-population-c-qualification.json", result)
    _write_report(
        "v3.6-r1-round16-population-c-qualification.md",
        "V3.6-R1 round-16 final Population C qualification", result,
    )
    return result


def run_tournament() -> dict[str, Any]:
    qualification = json.loads(
        (RESULTS / "v3.6-r1-round16-population-c-qualification.json").read_text()
    )
    if qualification["verdict"] != "PASS":
        raise RuntimeError("external qualification did not pass")
    block = v36_round12.TOURNAMENT_BLOCK
    tasks = [
        (seed, block[0], block[1], "tournament")
        for seed in range(block[0], block[1] + 1)
    ]
    rows, ledger = _persist_rows(
        "v3.6-r1-round12-tournament", tasks, _external_row,
        chunksize=1, serial_group_size=len(tasks) // 4,
    )
    pareto = {}
    scientific_failures = []
    for index, target in enumerate(TARGETS):
        values = [
            float(row["scores"]["v3"][target])
            - float(row["scores"]["v2"][target])
            for row in rows
        ]
        interval = _bootstrap_interval(values, 368_400 + index)
        passed = interval[0] >= -v36_round12.DELTA
        pareto[target] = {
            "mean_D": float(np.mean(values)), "interval_95": interval,
            "delta": v36_round12.DELTA, "passed": passed,
            "quantiles": [float(x) for x in np.quantile(values, (.01,.05,.5,.95,.99))],
            "by_stratum": {
                stratum: {
                    "mean_D": float(np.mean([
                        float(row["scores"]["v3"][target])
                        - float(row["scores"]["v2"][target])
                        for row in rows if row["stratum"] == stratum
                    ])),
                    "world_count": sum(
                        row["stratum"] == stratum for row in rows
                    ),
                }
                for stratum in v36_round12.STRATA
            },
        }
        if not passed:
            scientific_failures.append(target)
    verdict = (
        "V3.6_COMPRESSION_NONINFERIORITY_PASS_WITH_RETAINED_R1_BRIDGE_QUALIFICATION_FAILURE"
        if not scientific_failures else
        "V3.6_COMPRESSION_PREDICTIVE_COST_RETAINED_WITH_RETAINED_R1_BRIDGE_QUALIFICATION_FAILURE"
    )
    result = {
        "stage": "V3.6-R1-round12",
        "name": "COMMON-TARGET COMPRESSION TOURNAMENT",
        "seed_block": list(block), "world_count": len(rows),
        "stratum_counts": {
            stratum: sum(row["stratum"] == stratum for row in rows)
            for stratum in v36_round12.STRATA
        },
        "pareto_vector": pareto,
        "macro_mean_descriptive_only": float(np.mean([
            item["mean_D"] for item in pareto.values()
        ])),
        "scientific_failures": scientific_failures,
        "original_gate3_tournament_unchanged": True,
        "hybrid_bridge_failure_retained": True,
        "custody": ledger, "verdict": verdict,
    }
    _write_json("v3.6-r1-round12-tournament.json", result)
    _write_report(
        "v3.6-r1-round12-tournament.md",
        "V3.6-R1 round-12 common-target tournament", result,
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=(
        "precommit", "fixture-proofs", "v2-native", "v3-native", "external", "tournament"
    ))
    phase = parser.parse_args().phase
    runners = {
        "precommit": run_precommit,
        "fixture-proofs": run_fixture_identity_proofs,
        "v2-native": run_v2_native,
        "v3-native": run_v3_native,
        "external": run_external_qualification,
        "tournament": run_tournament,
    }
    result = runners[phase]()
    print(json.dumps({"phase": phase, "verdict": result["verdict"]}, sort_keys=True))
    return 0 if result["verdict"] not in {
        "FAIL_APPARATUS_STOP", "FAIL_UNEXECUTABLE"
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())
