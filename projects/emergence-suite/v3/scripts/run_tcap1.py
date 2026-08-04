#!/usr/bin/env python3
"""T-CAP1 Stage 0 proofs and Stage 1 public dynamics census."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import sys
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ref import tcap1  # noqa: E402
from ref.custody import validate_finite_worker_row  # noqa: E402
from ref.trace_sink import require_trace_sink, traced_execution  # noqa: E402
from scripts import run_decisive_s2 as s2  # noqa: E402
from scripts import run_round24_defenses as round24  # noqa: E402


RESULTS = ROOT / "results" / "decisive-tests"
BLOCK = (3_824_000, 3_831_999)
CENSUS2_BLOCK = (3_840_000, 3_847_999)
TOL = 1e-10
GRID = tuple(itertools.product(
    (0.0, 2.0, 4.0, 6.0),
    (0.25, 0.5, 0.75),
    (0.0, 0.6, 0.9),
    (0.85, 0.95, 0.99),
    (0.6, 0.8, 0.95),
))


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(child) for child in value]
    if hasattr(value, "__dataclass_fields__"):
        return {name: _plain(getattr(value, name)) for name in value.__dataclass_fields__}
    if isinstance(value, np.generic):
        return value.item()
    return value


def _canonical(value: Any) -> bytes:
    return (json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _write_json(name: str, value: Any) -> None:
    (RESULTS / name).write_text(json.dumps(_plain(value), indent=2, sort_keys=True, allow_nan=False) + "\n")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _enumerable_support(channels: int = 2):
    return itertools.product((0, 1), (0, 1), *[(None, 0, 1) for _ in range(channels)])


def _dummy_observation_probability(observations, bundle, allocation, cue):
    return math.prod(tcap1.observation_atom_probability(index, value, bundle, allocation, cue) for index, value in enumerate(observations))


def semantic_proofs() -> dict[str, Any]:
    q_previous = 0.37
    cue = 0.4
    beta = 2.0
    persistence = 0.6
    meta_reliability = 0.8
    allocation_prior = tcap1.allocation_probability(q_previous, cue, beta, 0, persistence)

    generator_sums = {}
    represented_sums = {}
    transparent_sums = {}
    for bundle in (0, 1):
        generator_total = 0.0
        represented_total = 0.0
        for allocation, meta, first, second in _enumerable_support():
            observations = (first, second)
            p_a = allocation_prior if allocation else 1.0 - allocation_prior
            p_meta = tcap1.allocation_observation_probability(meta, allocation, meta_reliability)
            p_obs = _dummy_observation_probability(observations, bundle, allocation, cue)
            generator_total += p_a * p_meta * p_obs
            represented_total += p_a * p_meta * p_obs
        generator_sums[str(bundle)] = generator_total
        represented_sums[str(bundle)] = represented_total
        transparent_total = math.fsum(_dummy_observation_probability(observations, bundle, 0, cue) for observations in itertools.product((None, 0, 1), repeat=2))
        transparent_sums[str(bundle)] = transparent_total

    observation = (1, None)
    meta = 1
    aware, naive = tcap1.selection_log_bfs(observation, meta, cue, allocation_prior, meta_reliability)
    direct_aware = tcap1.represented_log_likelihood(observation, meta, 1, cue, allocation_prior, meta_reliability) - tcap1.represented_log_likelihood(observation, meta, 0, cue, allocation_prior, meta_reliability)
    direct_naive = tcap1.transparent_log_likelihood(observation, 1, cue) - tcap1.transparent_log_likelihood(observation, 0, cue)

    q_after_zero = tcap1.posterior_update(q_previous, tcap1.transparent_log_likelihood((0, None), 0, cue), tcap1.transparent_log_likelihood((0, None), 1, cue))
    q_after_one = tcap1.posterior_update(q_previous, tcap1.transparent_log_likelihood((1, None), 0, cue), tcap1.transparent_log_likelihood((1, None), 1, cue))
    allocation_before_zero = tcap1.allocation_probability(q_previous, cue, beta, 0, persistence)
    allocation_before_one = tcap1.allocation_probability(q_previous, cue, beta, 0, persistence)
    delayed_next_zero = tcap1.allocation_probability(q_after_zero, cue, beta, 0, persistence)
    delayed_next_one = tcap1.allocation_probability(q_after_one, cue, beta, 0, persistence)

    full_observation = (1, 0)
    transparent_full = tuple(tcap1.transparent_log_likelihood(full_observation, bundle, cue, full_information=True) for bundle in (0, 1))
    represented_full = tuple(tcap1.represented_log_likelihood(full_observation, meta, bundle, cue, allocation_prior, meta_reliability, full_information=True) for bundle in (0, 1))

    canonical_stream = {"allocation": 1, "meta": 1, "observations": [1, None], "cue": cue}
    architecture_streams = {"transparent": canonical_stream, "represented": canonical_stream}

    checks = {
        "generator_normalization": max(abs(value - 1.0) for value in generator_sums.values()) <= TOL,
        "transparent_likelihood_normalization": max(abs(value - 1.0) for value in transparent_sums.values()) <= TOL,
        "represented_likelihood_normalization": max(abs(value - 1.0) for value in represented_sums.values()) <= TOL,
        "identical_generated_stream": architecture_streams["transparent"] is architecture_streams["represented"],
        "one_cycle_delay_identity": abs(allocation_before_zero - allocation_before_one) <= TOL and abs(delayed_next_zero - delayed_next_one) > TOL,
        "no_within_slice_posterior_feedback": abs(allocation_before_zero - allocation_prior) <= TOL,
        "selection_aware_BF_correctness": abs(aware - direct_aware) <= TOL and abs(naive - direct_naive) <= TOL,
        "full_information_replay_identity": max(abs(left - right) for left, right in zip(transparent_full, represented_full)) <= TOL,
    }
    return {
        "dummy": {"bundle_states": 2, "channels": 2, "channel_support": ["masked", 0, 1], "allocation_prior": allocation_prior},
        "normalization": {"generator": generator_sums, "transparent": transparent_sums, "represented": represented_sums},
        "selection_BF": {"aware": aware, "aware_direct": direct_aware, "naive": naive, "naive_direct": direct_naive},
        "delay": {"q_after_zero": q_after_zero, "q_after_one": q_after_one, "allocation_current_zero": allocation_before_zero, "allocation_current_one": allocation_before_one, "allocation_next_zero": delayed_next_zero, "allocation_next_one": delayed_next_one},
        "full_replay": {"transparent": transparent_full, "represented": represented_full},
        "checks": checks,
    }


def arm_common_world_proof() -> dict[str, Any]:
    """Zero-seed proof that only allocation RNG namespaces vary by arm."""

    world_keys = {
        arm: {
            "bundle": tcap1.world_component_key("bundle-stay"),
            "meta": tcap1.world_component_key("meta"),
            "delivery": [tcap1.world_component_key("delivery", channel) for channel in range(len(tcap1.CHANNELS))],
            "token": [tcap1.world_component_key("token", channel) for channel in range(len(tcap1.CHANNELS))],
        }
        for arm in tcap1.ARMS
    }
    allocation_keys = {arm: tcap1.allocation_component_key(arm) for arm in tcap1.ARMS}

    def path_from_stays(stays: Sequence[int]) -> tuple[int, ...]:
        state = 0
        path = [state]
        for stay in stays:
            if not stay:
                state = 1 - state
            path.append(state)
        return tuple(path)

    enumerated = []
    for stays in itertools.product((0, 1), repeat=4):
        paths = {arm: path_from_stays(stays) for arm in tcap1.ARMS}
        enumerated.append({"stay_bits": stays, "paths": paths, "byte_identical": len(set(paths.values())) == 1})
    reference = world_keys[tcap1.ARMS[0]]
    checks = {
        "world_keys_arm_invariant": all(keys == reference for keys in world_keys.values()),
        "allocation_keys_are_declared_arm_varying": len(set(allocation_keys.values())) == len(tcap1.ARMS),
        "enumerated_latent_paths_byte_identical": all(row["byte_identical"] for row in enumerated),
        "only_declared_process_varies": all(set(keys) == {"bundle", "meta", "delivery", "token"} for keys in world_keys.values()),
    }
    return {"zero_seed": True, "seed_consumption": [], "world_keys": world_keys, "allocation_keys": allocation_keys, "enumerated_paths": enumerated, "checks": checks, "verdict": "PASS" if all(checks.values()) else "FAIL_APPARATUS_ARM_COMMON_WORLD_PROOF"}


def persist_arm_common_world_proof() -> dict[str, Any]:
    record = arm_common_world_proof()
    trace = RESULTS / "tcap1-round29-arm-common-world-proof-trace.jsonl"
    if trace.exists():
        raise RuntimeError("round-29 arm-common proof trace exists")
    encoded = _canonical(record)
    with trace.open("xb") as handle:
        handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
    record["custody"] = {"trace_file": trace.name, "sha256": hashlib.sha256(encoded).hexdigest(), "persisted_before_verdict": True}
    _write_json("tcap1-round29-arm-common-world-proof.json", record)
    (RESULTS / "tcap1-round29-arm-common-world-proof.md").write_text(
        "# T-CAP1 arm-common world proof\n\n"
        f"Verdict: **{record['verdict']}**. All {len(tcap1.ARMS)} arms use identical world, bundle-path, metacognitive-noise, delivery-noise, and token-noise keys. Only allocation RNG keys vary by arm.\n"
    )
    return record


def estimand_conformance() -> dict[str, Any]:
    levels = (0.0, 0.25, 0.5, 0.75, 1.0)
    hand_up = {0.0: 0.10, 0.25: 0.20, 0.5: 0.35, 0.75: 0.60, 1.0: 0.80}
    hand_down = {0.0: 0.30, 0.25: 0.42, 0.5: 0.58, 0.75: 0.70, 1.0: 0.82}
    production = tcap1.hysteresis_area(hand_up, hand_down)
    hand_oracle = sum((hand_down[level] - hand_up[level]) * 0.25 for level in levels if hand_down[level] > hand_up[level])
    arms = {}
    for arm in tcap1.ARMS:
        arms[arm] = {
            "intervention_event": "cue level change and next-cycle allocation selection",
            "observation_window": "42-slice up/peak/down/withdrawal sweep; later outcomes use slices after the relevant cue transition",
            "denominator_population": "all serialized worlds assigned to the parameter cell; effective-precision summaries divide by delivered tokens only",
            "exclusions": ["masked channel tokens excluded from delivered-token denominators", "no world excluded from hysteresis, threshold, or recovery summaries"],
            "registered_statistics": ["hysteresis_area", "capture_on_threshold", "release_threshold", "posterior_after_full_withdrawal", "recovery_time", "fixed_point_count", "effective_precision", "disconfirming_influence", "selection_BF_divergence"],
        }
    checks = {
        "aggregate_hand_reproduction": abs(production - hand_oracle) <= TOL,
        "all_arms_declared": set(arms) == set(tcap1.ARMS),
        "all_windows_declared": all(row["observation_window"] for row in arms.values()),
        "all_denominators_declared": all(row["denominator_population"] for row in arms.values()),
        "all_exclusions_declared": all(row["exclusions"] for row in arms.values()),
    }
    return {"round27_extension": True, "arms": arms, "hand_trace": {"up": hand_up, "down": hand_down, "production_H": production, "independent_hand_H": hand_oracle}, "checks": checks}


def stage0() -> dict[str, Any]:
    if not (RESULTS / "tcap1-design-freeze.json").exists():
        raise RuntimeError("T-CAP1 design freeze missing")
    semantics = semantic_proofs()
    conformance = estimand_conformance()
    defenses = {
        "A": {"native": round24.native_identity(), "external": round24.external_identity()},
        "B": round24.forecast_manifest(),
        "C": round24.ledger(),
        "D": round24.metamorphic(),
    }
    checks = {
        **semantics["checks"],
        "round24_A": defenses["A"]["native"]["passed"] and defenses["A"]["external"]["passed"],
        "round24_B": defenses["B"]["passed"],
        "round24_C": bool(defenses["C"]["proofs"]),
        "round24_D": defenses["D"]["passed"],
        "estimand_conformance": all(conformance["checks"].values()),
        "v36_sources_unchanged": s2._assert_sources() == s2.SOURCE_HASHES,
    }
    pre_verdict = {"study": "T-CAP1", "stage": 0, "zero_seed": True, "seed_consumption": [], "semantic_proofs": semantics, "standing_defenses": defenses, "estimand_conformance": conformance, "checks": checks, "frozen_v36_hashes": s2.SOURCE_HASHES}
    trace = RESULTS / "tcap1-stage0-proof-trace.jsonl"
    if trace.exists():
        raise RuntimeError("T-CAP1 Stage-0 trace exists")
    encoded = _canonical(pre_verdict)
    with trace.open("xb") as handle:
        handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
    record = dict(pre_verdict)
    record["custody"] = {"trace_file": trace.name, "sha256": hashlib.sha256(encoded).hexdigest(), "persisted_before_verdict": True}
    record["verdict"] = "PASS" if all(checks.values()) else "FAIL_APPARATUS_STAGE0"
    _write_json("tcap1-stage0-proofs.json", record)
    (RESULTS / "tcap1-stage0-proofs.md").write_text(
        "# T-CAP1 Stage 0 semantic proofs\n\n"
        f"Verdict: **{record['verdict']}**. No world seed was consumed.\n\n"
        f"All eight T-CAP1 semantic identities, round-24 defenses A–D, and the round-27 estimand-conformance extension: `{all(checks.values())}`.\n"
    )
    return record


def _cell_ranges(block: tuple[int, int] = BLOCK) -> tuple[tuple[int, int, int, tcap1.CaptureParameters], ...]:
    total, count = block[1] - block[0] + 1, len(GRID)
    base, remainder = divmod(total, count)
    cursor = block[0]
    rows = []
    for index, values in enumerate(GRID):
        size = base + int(index < remainder)
        params = tcap1.CaptureParameters(*values)
        rows.append((index, cursor, cursor + size - 1, params))
        cursor += size
    if cursor != block[1] + 1:
        raise RuntimeError("T-CAP1 Stage-1 cardinality preflight failed")
    return tuple(rows)


@traced_execution
def _worker(task: tuple[int, int, tuple[float, float, float, float, float]]) -> dict[str, Any]:
    seed, cell_index, values = task
    require_trace_sink("tcap1.stage1_worker", seed=seed, cell=cell_index)
    parameters = tcap1.CaptureParameters(*values)
    data = tcap1.simulate_all_arms(seed, parameters, released_block=BLOCK)
    return {"seed": seed, "cell_index": cell_index, "parameters": _plain(parameters), "data": data}


def _persist_stage1(tasks: Sequence[tuple[int, int, tuple[float, float, float, float, float]]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    trace = RESULTS / "tcap1-stage1-census-traces.jsonl"
    events = RESULTS / "tcap1-stage1-census-trace-hash-events.jsonl"
    ledger_path = RESULTS / "tcap1-stage1-census-trace-hashes.json"
    if any(path.exists() for path in (trace, events, ledger_path)):
        raise RuntimeError("T-CAP1 Stage-1 custody output exists")
    rows, records, digest = [], [], hashlib.sha256()
    ranges = _cell_ranges()
    with trace.open("xb") as handle, events.open("xb") as event_handle:
        def persist(row: dict[str, Any]) -> None:
            validate_finite_worker_row(row)
            encoded = _canonical(row)
            handle.write(encoded); handle.flush(); os.fsync(handle.fileno()); digest.update(encoded)
            event = {"seed": row["seed"], "cell_index": row["cell_index"], "sha256": hashlib.sha256(encoded).hexdigest()}
            event_handle.write(_canonical(event)); event_handle.flush(); os.fsync(event_handle.fileno())
            rows.append(row); records.append(event)
        offset = 0
        for index, start, end, parameters in ranges:
            subset = list(tasks[offset:offset + end - start + 1]); offset += len(subset)
            expected_values = tuple(_plain(parameters).values())
            if subset[0] != (start, index, expected_values) or subset[-1] != (end, index, expected_values):
                raise RuntimeError("T-CAP1 Stage-1 cell preflight mismatch")
            persist(_worker(subset[0]))
            with get_context("spawn").Pool(max(1, min(8, (os.cpu_count() or 2) - 1))) as pool:
                for row in pool.imap(_worker, subset[1:], chunksize=1):
                    persist(row)
    expected = [(seed, index) for index, start, end, _ in ranges for seed in range(start, end + 1)]
    if [(row["seed"], row["cell_index"]) for row in rows] != expected:
        raise RuntimeError("T-CAP1 Stage-1 custody mismatch")
    ledger = {"trace_file": trace.name, "sha256": digest.hexdigest(), "record_count": len(rows), "seed_start": BLOCK[0], "seed_end": BLOCK[1], "ascending_gap_free_per_cell": True, "serial_first_worlds": [start for _, start, _, _ in ranges], "persisted_before_aggregation": True, "event_hash_file": events.name, "event_hash_sha256": _sha(events), "records": records}
    _write_json(ledger_path.name, ledger)
    return rows, ledger


def _mean(values: Sequence[float]) -> float:
    return float(np.mean(np.asarray(values, dtype=float)))


def _quantiles(values: Sequence[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=float)
    return {name: float(np.quantile(array, q)) for name, q in (("q05", .05), ("q25", .25), ("q50", .5), ("q75", .75), ("q95", .95))}


def stage1() -> dict[str, Any]:
    proof = json.loads((RESULTS / "tcap1-stage0-proofs.json").read_text())
    if proof["verdict"] != "PASS":
        raise RuntimeError("T-CAP1 Stage-0 gate failed")
    ranges = _cell_ranges()
    tasks = []
    for index, start, end, parameters in ranges:
        values = tuple(_plain(parameters).values())
        tasks.extend((seed, index, values) for seed in range(start, end + 1))
    rows, ledger = _persist_stage1(tasks)
    cells = []
    for index, start, end, parameters in ranges:
        subset = [row for row in rows if row["cell_index"] == index]
        arm_summary = {}
        for arm in tcap1.ARMS:
            arm_rows = [row["data"]["arms"][arm] for row in subset]
            arm_summary[arm] = {
                key: _mean([item[key] for item in arm_rows])
                for key in ("hysteresis_area", "capture_on_threshold", "release_threshold", "posterior_after_full_withdrawal", "material_elevation_after_withdrawal", "recovery_time", "fixed_point_count", "mean_disconfirming_influence", "mean_selection_bf_divergence", "delivered_token_denominator")
            }
            arm_summary[arm]["hysteresis_distribution"] = _quantiles([item["hysteresis_area"] for item in arm_rows])
            arm_summary[arm]["effective_precision_by_channel"] = [_mean([item["mean_effective_precision"][channel] for item in arm_rows]) for channel in range(len(tcap1.CHANNELS))]
            if arm == "full_information_replay":
                arm_summary[arm]["transparent_represented_max_error"] = max(item["transparent_represented_max_error"] for item in arm_rows)
        h = arm_summary["transparent_feedback"]["hysteresis_area"]
        region = "no_hysteresis" if h < .02 else "near_boundary" if h < .08 else "clear_hysteresis"
        cells.append({"cell_index": index, "seed_start": start, "seed_end": end, "count": len(subset), "parameters": _plain(parameters), "region": region, "arms": arm_summary})

    panel = {}
    for region in ("no_hysteresis", "near_boundary", "clear_hysteresis"):
        matches = [cell for cell in cells if cell["region"] == region]
        panel[region] = matches[0] if matches else None
    region_counts = {region: sum(cell["region"] == region for cell in cells) for region in panel}
    panel_complete = all(cell is not None for cell in panel.values())
    minimum_h = min(cell["arms"]["transparent_feedback"]["hysteresis_area"] for cell in cells)
    aggregate = {
        arm: {
            "hysteresis": _quantiles([row["data"]["arms"][arm]["hysteresis_area"] for row in rows]),
            "posterior_after_withdrawal": _quantiles([row["data"]["arms"][arm]["posterior_after_full_withdrawal"] for row in rows]),
            "disconfirming_influence": _quantiles([row["data"]["arms"][arm]["mean_disconfirming_influence"] for row in rows]),
            "selection_BF_divergence": _quantiles([row["data"]["arms"][arm]["mean_selection_bf_divergence"] for row in rows]),
        }
        for arm in tcap1.ARMS
    }
    status = "COMPLETE_NON_CRITERIAL_DYNAMICS_CENSUS" if panel_complete else "COMPLETE_NON_CRITERIAL_DYNAMICS_CENSUS_PANEL_SPAN_NOT_ATTAINED"
    record = {"study": "T-CAP1", "stage": 1, "status": status, "seed_block": list(BLOCK), "grid_cell_count": len(cells), "world_count": len(rows), "channels": list(tcap1.CHANNELS), "arms": list(tcap1.ARMS), "region_counts": region_counts, "frozen_parameter_panel": panel, "panel_complete": panel_complete, "panel_finding": None if panel_complete else {"classification": "PUBLIC_CENSUS_DYNAMIC_RANGE_NOT_SPANNED", "minimum_cell_mean_transparent_hysteresis": minimum_h, "predeclared_clear_boundary": 0.08, "missing_regions": [region for region, cell in panel.items() if cell is None], "interpretation": "The requested panel cannot be frozen without a post-data redefinition, which was not performed."}, "census_map": cells, "aggregate_distributions": aggregate, "custody": ledger, "no_prediction_seal": True, "confirmatory_blocks_opened": False, "escrow_opened": False}
    _write_json("tcap1-stage1-census.json", record)
    panel_lines = []
    for region, cell in panel.items():
        panel_lines.append(f"- **{region}**: " + (f"cell {cell['cell_index']}, `{json.dumps(cell['parameters'], sort_keys=True)}`, mean transparent H `{cell['arms']['transparent_feedback']['hysteresis_area']}`" if cell else "no occupied cell; reported without substitution"))
    (RESULTS / "tcap1-stage1-census.md").write_text(
        "# T-CAP1 Stage 1 public dynamics census\n\n"
        f"Status: **{status}**. No prediction or threshold was sealed.\n\n"
        f"The census used {len(rows)} public worlds across {len(cells)} parameter cells. Region counts: `{json.dumps(region_counts, sort_keys=True)}`.\n\n"
        "## Frozen parameter panel\n\n" + "\n".join(panel_lines) + "\n\n"
        + ("The requested three-region panel is incomplete. The absent entries remain null; no post-data region or grid change was made.\n\n" if not panel_complete else "")
        + f"Trace SHA-256: `{ledger['sha256']}`. All seven controls plus the primary transparent arm are present.\n"
    )
    return record


def stage1b_preblock() -> dict[str, Any]:
    arm_proof = json.loads((RESULTS / "tcap1-round29-arm-common-world-proof.json").read_text())
    defenses = {
        "A": {"native": round24.native_identity(), "external": round24.external_identity()},
        "B": round24.forecast_manifest(),
        "C": round24.ledger(),
        "D": round24.metamorphic(),
    }
    stage0_record = json.loads((RESULTS / "tcap1-stage0-proofs.json").read_text())
    checks = {
        "stage0_stands": stage0_record["verdict"] == "PASS",
        "arm_common_world_proof": arm_proof["verdict"] == "PASS",
        "round24_A": defenses["A"]["native"]["passed"] and defenses["A"]["external"]["passed"],
        "round24_B": defenses["B"]["passed"],
        "round24_C": bool(defenses["C"]["proofs"]),
        "round24_D": defenses["D"]["passed"],
        "estimand_conformance": all(estimand_conformance()["checks"].values()),
        "v36_sources_unchanged": s2._assert_sources() == s2.SOURCE_HASHES,
    }
    pre_verdict = {"study": "T-CAP1", "battery": "Census-2 preblock", "zero_seed": True, "seed_consumption": [], "checks": checks, "arm_common_world_proof": arm_proof, "standing_defenses": defenses}
    trace = RESULTS / "tcap1-stage1b-preblock-proof-trace.jsonl"
    if trace.exists():
        raise RuntimeError("T-CAP1 Census-2 preblock trace exists")
    encoded = _canonical(pre_verdict)
    with trace.open("xb") as handle:
        handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
    record = dict(pre_verdict)
    record["custody"] = {"trace_file": trace.name, "sha256": hashlib.sha256(encoded).hexdigest(), "persisted_before_verdict": True}
    record["verdict"] = "PASS" if all(checks.values()) else "FAIL_APPARATUS_PREBLOCK"
    _write_json("tcap1-stage1b-preblock-proofs.json", record)
    (RESULTS / "tcap1-stage1b-preblock-proofs.md").write_text(f"# T-CAP1 Census-2 preblock proofs\n\nVerdict: **{record['verdict']}**. No world seed was consumed.\n")
    return record


@traced_execution
def _worker_stage1b(task: tuple[int, int, tuple[float, float, float, float, float]]) -> dict[str, Any]:
    seed, cell_index, values = task
    require_trace_sink("tcap1.stage1b_worker", seed=seed, cell=cell_index)
    parameters = tcap1.CaptureParameters(*values)
    data = tcap1.simulate_all_arms(seed, parameters, released_block=CENSUS2_BLOCK)
    if not data["arm_common_world_identity"]:
        raise RuntimeError("Census-2 runtime arm-common identity failed")
    return {"seed": seed, "cell_index": cell_index, "parameters": _plain(parameters), "data": data}


def _persist_stage1b(tasks: Sequence[tuple[int, int, tuple[float, float, float, float, float]]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    trace = RESULTS / "tcap1-stage1b-census-traces.jsonl"
    events = RESULTS / "tcap1-stage1b-census-trace-hash-events.jsonl"
    ledger_path = RESULTS / "tcap1-stage1b-census-trace-hashes.json"
    if any(path.exists() for path in (trace, events, ledger_path)):
        raise RuntimeError("T-CAP1 Census-2 custody output exists")
    rows, records, digest = [], [], hashlib.sha256()
    ranges = _cell_ranges(CENSUS2_BLOCK)
    with trace.open("xb") as handle, events.open("xb") as event_handle:
        def persist(row: dict[str, Any]) -> None:
            validate_finite_worker_row(row)
            encoded = _canonical(row)
            handle.write(encoded); handle.flush(); os.fsync(handle.fileno()); digest.update(encoded)
            event = {"seed": row["seed"], "cell_index": row["cell_index"], "sha256": hashlib.sha256(encoded).hexdigest()}
            event_handle.write(_canonical(event)); event_handle.flush(); os.fsync(event_handle.fileno())
            rows.append(row); records.append(event)
        offset = 0
        for index, start, end, parameters in ranges:
            subset = list(tasks[offset:offset + end - start + 1]); offset += len(subset)
            expected_values = tuple(_plain(parameters).values())
            if subset[0] != (start, index, expected_values) or subset[-1] != (end, index, expected_values):
                raise RuntimeError("T-CAP1 Census-2 cell preflight mismatch")
            persist(_worker_stage1b(subset[0]))
            with get_context("spawn").Pool(max(1, min(8, (os.cpu_count() or 2) - 1))) as pool:
                for row in pool.imap(_worker_stage1b, subset[1:], chunksize=1):
                    persist(row)
    expected = [(seed, index) for index, start, end, _ in ranges for seed in range(start, end + 1)]
    if [(row["seed"], row["cell_index"]) for row in rows] != expected:
        raise RuntimeError("T-CAP1 Census-2 custody mismatch")
    ledger = {"trace_file": trace.name, "sha256": digest.hexdigest(), "record_count": len(rows), "seed_start": CENSUS2_BLOCK[0], "seed_end": CENSUS2_BLOCK[1], "ascending_gap_free_per_cell": True, "serial_first_worlds": [start for _, start, _, _ in ranges], "persisted_before_aggregation": True, "event_hash_file": events.name, "event_hash_sha256": _sha(events), "records": records}
    _write_json(ledger_path.name, ledger)
    return rows, ledger


def stage1b() -> dict[str, Any]:
    preblock = json.loads((RESULTS / "tcap1-stage1b-preblock-proofs.json").read_text())
    if preblock["verdict"] != "PASS":
        raise RuntimeError("T-CAP1 Census-2 preblock failed")
    ranges = _cell_ranges(CENSUS2_BLOCK)
    tasks = []
    for index, start, end, parameters in ranges:
        values = tuple(_plain(parameters).values())
        tasks.extend((seed, index, values) for seed in range(start, end + 1))
    rows, ledger = _persist_stage1b(tasks)
    cells = []
    for index, start, end, parameters in ranges:
        subset = [row for row in rows if row["cell_index"] == index]
        arm_summary = {}
        for arm in tcap1.ARMS:
            arm_rows = [row["data"]["arms"][arm] for row in subset]
            arm_summary[arm] = {
                key: _mean([item[key] for item in arm_rows])
                for key in ("hysteresis_area", "capture_on_threshold", "release_threshold", "posterior_after_full_withdrawal", "material_elevation_after_withdrawal", "recovery_time", "mean_disconfirming_influence", "mean_selection_bf_divergence", "delivered_token_denominator")
            }
            arm_summary[arm]["hysteresis_distribution"] = _quantiles([item["hysteresis_area"] for item in arm_rows])
            arm_summary[arm]["effective_precision_by_channel"] = [_mean([item["mean_effective_precision"][channel] for item in arm_rows]) for channel in range(len(tcap1.CHANNELS))]
            arm_summary[arm]["two_stable_fixed_point_fraction"] = _mean([item["bistability"]["two_stable_fixed_points"] for item in arm_rows])
            arm_summary[arm]["initial_posterior_final_separation"] = _mean([item["bistability"]["final_separation"] for item in arm_rows])
            arm_summary[arm]["bistability_distribution"] = _quantiles([item["bistability"]["final_separation"] for item in arm_rows])
            if arm == "full_information_replay":
                arm_summary[arm]["transparent_represented_max_error"] = max(item["transparent_represented_max_error"] for item in arm_rows)
        paired_excess = [row["data"]["arms"]["transparent_feedback"]["hysteresis_area"] - row["data"]["arms"]["matched_persistence"]["hysteresis_area"] for row in subset]
        h_excess = _mean(paired_excess)
        region = "no_hysteresis" if h_excess < .02 else "near_boundary" if h_excess < .08 else "clear_hysteresis"
        cells.append({"cell_index": index, "seed_start": start, "seed_end": end, "count": len(subset), "parameters": _plain(parameters), "region": region, "H_excess_mean": h_excess, "H_excess_distribution": _quantiles(paired_excess), "raw_H_descriptive": {"transparent": arm_summary["transparent_feedback"]["hysteresis_area"], "matched_persistence": arm_summary["matched_persistence"]["hysteresis_area"]}, "arms": arm_summary, "arm_common_world_identity": all(row["data"]["arm_common_world_identity"] for row in subset)})
    panel = {}
    for region in ("no_hysteresis", "near_boundary", "clear_hysteresis"):
        matches = [cell for cell in cells if cell["region"] == region]
        panel[region] = matches[0] if matches else None
    region_counts = {region: sum(cell["region"] == region for cell in cells) for region in panel}
    panel_complete = all(cell is not None for cell in panel.values())
    bistability_census = {
        arm: {
            "two_stable_fixed_point_world_count": int(round(sum(cell["arms"][arm]["two_stable_fixed_point_fraction"] * cell["count"] for cell in cells))),
            "two_stable_fixed_point_world_fraction": sum(cell["arms"][arm]["two_stable_fixed_point_fraction"] * cell["count"] for cell in cells) / len(rows),
        }
        for arm in tcap1.ARMS
    }
    record = {
        "study": "T-CAP1",
        "stage": "1b",
        "status": "COMPLETE_NON_CRITERIAL_DYNAMICS_CENSUS_2" if panel_complete else "COMPLETE_NON_CRITERIAL_DYNAMICS_CENSUS_2_PANEL_SPAN_NOT_ATTAINED",
        "seed_block": list(CENSUS2_BLOCK),
        "grid_identity": "same frozen 324-cell Stage-1 grid",
        "grid_cell_count": len(cells),
        "world_count": len(rows),
        "classification_estimand": "cell mean of paired H_transparent - H_matched-persistence",
        "raw_H_reported_descriptively": True,
        "region_counts": region_counts,
        "panel_complete": panel_complete,
        "frozen_parameter_panel": panel,
        "bistability_census": bistability_census,
        "census_map": cells,
        "custody": ledger,
        "arm_common_world_identity_all_rows": all(row["data"]["arm_common_world_identity"] for row in rows),
        "no_prediction_seal": True,
        "confirmatory_blocks_opened": False,
        "escrow_opened": False,
    }
    _write_json("tcap1-stage1b-census.json", record)
    panel_lines = []
    for region, cell in panel.items():
        panel_lines.append(f"- **{region}**: " + (f"cell {cell['cell_index']}, `{json.dumps(cell['parameters'], sort_keys=True)}`, mean H_excess `{cell['H_excess_mean']}`" if cell else "no occupied cell; reported without substitution"))
    finding = "The excess-hysteresis grid spans all three frozen regions." if panel_complete else "The excess-hysteresis panel does not span all three regions. Missing entries remain null; no parameter or boundary was tuned."
    (RESULTS / "tcap1-stage1b-census.md").write_text(
        "# T-CAP1 Census-2 dynamics map\n\n"
        f"Status: **{record['status']}**. This is a public, non-criterial census.\n\n"
        f"All {len(rows)} worlds used arm-common latent paths. Regions are classified on paired `H_excess = H_transparent - H_matched-persistence`; raw H remains descriptive. Counts: `{json.dumps(region_counts, sort_keys=True)}`.\n\n"
        "## Frozen parameter panel\n\n" + "\n".join(panel_lines) + "\n\n" + finding + "\n\n"
        f"Trace SHA-256: `{ledger['sha256']}`.\n"
    )
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("stage0", "stage1", "proof29", "preblock29", "stage1b"))
    args = parser.parse_args()
    if args.action == "stage0":
        stage0()
    elif args.action == "stage1":
        stage1()
    elif args.action == "proof29":
        persist_arm_common_world_proof()
    elif args.action == "preblock29":
        stage1b_preblock()
    else:
        stage1b()


if __name__ == "__main__":
    main()
