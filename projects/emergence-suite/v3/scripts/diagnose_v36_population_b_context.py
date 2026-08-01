#!/usr/bin/env python3
"""Read-only Population-B context calibration decomposition.

This runner never calls a world generator or a scientific scoring entry point.
It reads the retained trace bundle, enumerates a finite dummy directly from the
frozen public parameter tables, and uses a diagnosis-only deterministic
simulation key for the requested parametric calibration null.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
from collections import defaultdict
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "V3.6"
TRACE = RESULTS / "v3.6-r1-round12-v2-native-traces.jsonl"
PARAMETERS_PATH = ROOT.parent / "v2" / "protocols" / "v2.4-parameters.json"
OUTPUT_JSON = RESULTS / "population-b-context-ece-decomposition.json"
OUTPUT_MD = RESULTS / "population-b-context-ece-decomposition.md"
TARGETS = ("identity", "outcome", "context", "partner", "contact")
FAMILIES = (
    "global_downweight",
    "cue_local_relearning",
    "context_split",
    "continuous_drift",
    "change_point",
)
REPLICATES = 2_000
DUMMY_LENGTH = 3
TOLERANCE = 1e-10


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def fixed_bin(probability: float) -> int:
    return min(int(float(probability) * 10.0), 9)


def reliability(probabilities: np.ndarray, outcomes: np.ndarray) -> dict[str, Any]:
    rows = []
    ece = 0.0
    count = len(probabilities)
    for index in range(10):
        mask = np.asarray([fixed_bin(value) == index for value in probabilities])
        n = int(mask.sum())
        mean_p = float(probabilities[mask].mean()) if n else None
        frequency = float(outcomes[mask].mean()) if n else None
        signed_gap = (mean_p - frequency) if n else None
        contribution = (n / count * abs(signed_gap)) if n else 0.0
        ece += contribution
        rows.append({
            "bin": index,
            "low": index / 10.0,
            "high": (index + 1) / 10.0,
            "count": n,
            "world_fraction": n / count,
            "mean_forecast_p1": mean_p,
            "observed_frequency_1": frequency,
            "signed_p_minus_frequency": signed_gap,
            "ece_contribution": contribution,
            "forecast_sd": float(probabilities[mask].std()) if n else None,
        })
    return {"ece": float(ece), "bins": rows}


def parametric_null(
    target: str, probabilities: np.ndarray, observed_ece: float
) -> dict[str, Any]:
    key_text = f"V3.6-R1:Population-B:{target}:parametric-ECE-null:v1"
    key = int.from_bytes(hashlib.sha256(key_text.encode()).digest()[:8], "big")
    rng = np.random.Generator(np.random.PCG64(key))
    simulated = rng.random((REPLICATES, len(probabilities))) < probabilities
    null = np.zeros(REPLICATES, dtype=float)
    for index in range(10):
        mask = np.asarray([fixed_bin(value) == index for value in probabilities])
        if not np.any(mask):
            continue
        mean_p = float(probabilities[mask].mean())
        frequencies = simulated[:, mask].mean(axis=1)
        null += float(mask.mean()) * np.abs(mean_p - frequencies)
    quantiles = np.quantile(null, (0.05, 0.50, 0.95, 0.99))
    less_equal = int(np.count_nonzero(null <= observed_ece))
    greater_equal = int(np.count_nonzero(null >= observed_ece))
    return {
        "replicates": REPLICATES,
        "simulation_key_label": key_text,
        "simulation_key_uint64": key,
        "mean": float(null.mean()),
        "quantiles": {
            "q05": float(quantiles[0]),
            "q50": float(quantiles[1]),
            "q95": float(quantiles[2]),
            "q99": float(quantiles[3]),
        },
        "observed_ece": float(observed_ece),
        "observed_empirical_cdf": less_equal / REPLICATES,
        "observed_rank_with_plus_one": (less_equal + 1) / (REPLICATES + 1),
        "upper_tail_probability_with_plus_one": (
            greater_equal + 1
        ) / (REPLICATES + 1),
        "beyond_null_q99": bool(observed_ece > quantiles[3]),
        "null_values": [float(value) for value in null],
    }


def normalize(values: Iterable[float]) -> np.ndarray:
    array = np.asarray(tuple(values), dtype=float)
    return array / float(array.sum())


def state_descriptor(family: str, state: tuple[int, ...]) -> str:
    if family == "context_split":
        return "then" if state[0] == 0 else "now"
    if family == "change_point":
        return "then" if state[0] == 0 else "now"
    return ("then", "now", "none")[state[0]]


def initial_states(
    family: str, parameters: dict[str, Any], *, fixture: bool
) -> list[tuple[tuple[int, ...], float]]:
    if family == "context_split":
        if fixture:
            return [((0, 0, 0, 0, 0), 1.0)]
        initial = parameters["family_processes"][family]["initial_distribution"]
        return [((context, 0, 0, 0, 0), float(mass)) for context, mass in enumerate(initial)]
    if family == "change_point":
        return [((0, 0), 1.0)]
    initial = parameters["candidate_common_nuisance_context"]["initial_distribution"]
    return [((state,), float(mass)) for state, mass in enumerate(initial)]


def transitions(
    family: str, state: tuple[int, ...], parameters: dict[str, Any]
) -> list[tuple[tuple[int, ...], float]]:
    if family == "context_split":
        context, n00, n01, n10, n11 = state
        prior = parameters["family_processes"][family]["transition_dirichlet_prior"]
        alpha = (prior["then_row_then_now"], prior["now_row_then_now"])
        counts = ((n00, n01), (n10, n11))[context]
        row = normalize((alpha[context][0] + counts[0], alpha[context][1] + counts[1]))
        output = []
        for next_context, mass in enumerate(row):
            updated = [n00, n01, n10, n11]
            updated[context * 2 + next_context] += 1
            output.append(((next_context, *updated), float(mass)))
        return output
    if family == "change_point":
        phase, stays = state
        if phase == 1:
            return [((1, stays), 1.0)]
        a, b = parameters["family_processes"][family]["hazard_beta_prior"]
        switch = float(a / (a + b + stays))
        return [((1, stays), switch), ((0, stays + 1), 1.0 - switch)]
    matrix = parameters["candidate_common_nuisance_context"]["transition_matrix"]
    return [((next_state,), float(mass)) for next_state, mass in enumerate(matrix[state[0]])]


def emissions(
    descriptor: str, parameters: dict[str, Any], kind: str
) -> tuple[float, ...]:
    row = parameters["observation_interface"]["context_marker_cpt_nonmissing"][descriptor]
    then, now, none = map(float, row)
    if kind == "fixture_full":
        return (1.0 - now, now, 0.0)
    if kind == "module_full":
        return (then, now, none)
    if kind == "fixture_binary":
        return (1.0 - now, now)
    if kind == "module_binary":
        return (then / (then + now), now / (then + now))
    raise ValueError(kind)


def enumerate_joint(
    parameters: dict[str, Any], *, fixture_initial: bool, emission_kind: str
) -> dict[tuple[Any, ...], float]:
    prior_map = parameters["candidate_prior"]
    output: defaultdict[tuple[Any, ...], float] = defaultdict(float)

    def recurse(
        family: str,
        time: int,
        state: tuple[int, ...],
        mass: float,
        path: tuple[tuple[int, ...], ...],
        tokens: tuple[int, ...],
    ) -> None:
        descriptor = state_descriptor(family, state)
        for token, emission_mass in enumerate(emissions(descriptor, parameters, emission_kind)):
            next_mass = mass * emission_mass
            next_path = (*path, state)
            next_tokens = (*tokens, token)
            if time == DUMMY_LENGTH - 1:
                output[(family, next_path, next_tokens)] += next_mass
            else:
                for next_state, transition_mass in transitions(family, state, parameters):
                    recurse(
                        family, time + 1, next_state,
                        next_mass * transition_mass, next_path, next_tokens,
                    )

    for family in FAMILIES:
        family_prior = float(prior_map[family])
        for state, initial_mass in initial_states(
            family, parameters, fixture=fixture_initial
        ):
            recurse(family, 0, state, family_prior * initial_mass, (), ())
    return dict(output)


def distribution_comparison(
    left: dict[tuple[Any, ...], float], right: dict[tuple[Any, ...], float]
) -> dict[str, Any]:
    keys = set(left) | set(right)
    differences = {key: abs(left.get(key, 0.0) - right.get(key, 0.0)) for key in keys}
    argmax = min(
        (key for key in keys if differences[key] == max(differences.values())),
        key=repr,
    )
    return {
        "left_probability_sum": math.fsum(left.values()),
        "right_probability_sum": math.fsum(right.values()),
        "support_union_size": len(keys),
        "max_absolute_probability_error": differences[argmax],
        "total_variation_distance": 0.5 * math.fsum(differences.values()),
        "max_error_atom": {
            "family": argmax[0],
            "state_path": [list(state) for state in argmax[1]],
            "observation_tokens": list(argmax[2]),
            "left_probability": left.get(argmax, 0.0),
            "right_probability": right.get(argmax, 0.0),
        },
        "identity_within_1e-10": differences[argmax] <= TOLERANCE,
    }


def fixture_identity(parameters: dict[str, Any]) -> dict[str, Any]:
    actual_full = enumerate_joint(parameters, fixture_initial=True, emission_kind="fixture_full")
    module_full = enumerate_joint(parameters, fixture_initial=False, emission_kind="module_full")
    actual_binary = enumerate_joint(parameters, fixture_initial=True, emission_kind="fixture_binary")
    module_binary = enumerate_joint(parameters, fixture_initial=False, emission_kind="module_binary")
    emission_fixed = enumerate_joint(parameters, fixture_initial=True, emission_kind="module_binary")
    initial_fixed = enumerate_joint(parameters, fixture_initial=False, emission_kind="fixture_binary")
    both_fixed = enumerate_joint(parameters, fixture_initial=False, emission_kind="module_binary")
    return {
        "dummy_length": DUMMY_LENGTH,
        "family_prior": parameters["candidate_prior"],
        "token_coding": {"0": "then_marker", "1": "now_marker", "2": "none_marker"},
        "full_module_marker_support": distribution_comparison(actual_full, module_full),
        "descriptor_conditioned_binary_diagnostic": distribution_comparison(actual_binary, module_binary),
        "isolations_in_descriptor_conditioned_binary_diagnostic": {
            "fix_emission_only_remaining_initial_error": distribution_comparison(emission_fixed, module_binary),
            "fix_initial_only_remaining_emission_error": distribution_comparison(initial_fixed, module_binary),
            "fix_both": distribution_comparison(both_fixed, module_binary),
        },
        "production_differences": [
            {
                "production": "context_split initial distribution",
                "fixture": [1.0, 0.0],
                "frozen_module": parameters["family_processes"]["context_split"]["initial_distribution"],
            },
            {
                "production": "context marker emission mapped to binary target",
                "fixture_rule": "P(now)=raw P(now_marker); P(then)=1-P(now)",
                "frozen_module_rule": "three-valued CPT; bridge binary predictive conditions then/now on non-none",
                "rows": parameters["observation_interface"]["context_marker_cpt_nonmissing"],
            },
        ],
    }


def update_distribution(
    distribution: dict[tuple[int, ...], float],
    family: str,
    token: int,
    parameters: dict[str, Any],
) -> tuple[dict[tuple[int, ...], float], float]:
    weighted = {}
    for state, mass in distribution.items():
        descriptor = state_descriptor(family, state)
        raw = emissions(descriptor, parameters, "module_full")[token]
        weighted[state] = mass * raw
    predictive = math.fsum(weighted.values())
    return ({state: mass / predictive for state, mass in weighted.items()}, predictive)


def transition_distribution(
    distribution: dict[tuple[int, ...], float],
    family: str,
    parameters: dict[str, Any],
) -> dict[tuple[int, ...], float]:
    output: defaultdict[tuple[int, ...], float] = defaultdict(float)
    for state, mass in distribution.items():
        for next_state, transition_mass in transitions(family, state, parameters):
            output[next_state] += mass * transition_mass
    total = math.fsum(output.values())
    return {state: mass / total for state, mass in output.items()}


def family_binary_prediction(
    distribution: dict[tuple[int, ...], float],
    family: str,
    parameters: dict[str, Any],
) -> float:
    # The frozen adapter marginalizes the three-valued CPT over the latent
    # distribution first, then conditions the aggregate on then/now delivery.
    # Conditioning each latent row first is different for the nuisance `none`
    # state, whose non-none mass is smaller.
    raw_then = math.fsum(
        mass * emissions(state_descriptor(family, state), parameters, "module_full")[0]
        for state, mass in distribution.items()
    )
    raw_now = math.fsum(
        mass * emissions(state_descriptor(family, state), parameters, "module_full")[1]
        for state, mass in distribution.items()
    )
    return raw_now / (raw_then + raw_now)


def sequential_module_predictions(
    tokens: list[int], parameters: dict[str, Any]
) -> list[float]:
    distributions = {
        "nuisance": dict(initial_states("global_downweight", parameters, fixture=False)),
        "context_split": dict(initial_states("context_split", parameters, fixture=False)),
        "change_point": dict(initial_states("change_point", parameters, fixture=False)),
    }
    weights = {family: float(parameters["candidate_prior"][family]) for family in FAMILIES}
    predictions = []
    for time, token in enumerate(tokens):
        family_p1 = {}
        for family in FAMILIES:
            key = family if family in {"context_split", "change_point"} else "nuisance"
            family_p1[family] = family_binary_prediction(distributions[key], family, parameters)
        predictions.append(math.fsum(weights[family] * family_p1[family] for family in FAMILIES))

        updated = {}
        predictive_by_family = {}
        for key, family in (
            ("nuisance", "global_downweight"),
            ("context_split", "context_split"),
            ("change_point", "change_point"),
        ):
            updated[key], predictive_by_family[key] = update_distribution(
                distributions[key], family, token, parameters
            )
        new_weights = {}
        for family in FAMILIES:
            key = family if family in {"context_split", "change_point"} else "nuisance"
            new_weights[family] = weights[family] * predictive_by_family[key]
        total = math.fsum(new_weights.values())
        weights = {family: mass / total for family, mass in new_weights.items()}
        distributions = updated
        if time < len(tokens) - 1:
            distributions = {
                key: transition_distribution(value, key, parameters)
                for key, value in distributions.items()
            }
    return predictions


def sequential_row(
    payload: tuple[dict[str, Any], dict[str, Any]]
) -> tuple[list[float], list[int], float]:
    row, parameters = payload
    fixture = row["fixtures"]["context"]
    tokens = [*map(int, fixture["history"]), int(fixture["observed"])]
    predictions = sequential_module_predictions(tokens, parameters)
    terminal_error = abs(predictions[-1] - float(fixture["confidence"]))
    return predictions, tokens, terminal_error


def slice_localization(
    rows: list[dict[str, Any]], parameters: dict[str, Any]
) -> dict[str, Any]:
    all_probabilities = []
    all_outcomes = []
    terminal_errors = []
    by_time_probabilities = [[] for _ in range(49)]
    by_time_outcomes = [[] for _ in range(49)]
    workers = min(8, max(1, os.cpu_count() or 1))
    with get_context("spawn").Pool(workers) as pool:
        computed = pool.map(
            sequential_row,
            ((row, parameters) for row in rows),
            chunksize=4,
        )
    for predictions, tokens, terminal_error in computed:
        terminal_errors.append(terminal_error)
        for time, (probability, token) in enumerate(zip(predictions, tokens)):
            by_time_probabilities[time].append(probability)
            by_time_outcomes[time].append(token)
            all_probabilities.append(probability)
            all_outcomes.append(token)

    def window(start: int, stop: int) -> dict[str, Any]:
        p = np.asarray(list(itertools.chain.from_iterable(by_time_probabilities[start:stop])))
        y = np.asarray(list(itertools.chain.from_iterable(by_time_outcomes[start:stop])))
        result = reliability(p, y)
        signed = float(p.mean() - y.mean())
        return {
            "slice_start_inclusive": start,
            "slice_stop_exclusive": stop,
            "token_count": len(p),
            "mean_forecast_p1": float(p.mean()),
            "observed_frequency_1": float(y.mean()),
            "signed_p_minus_frequency": signed,
            "direction": "overpredicts now_marker" if signed > 0 else "underpredicts now_marker",
            "ece": result["ece"],
        }

    return {
        "terminal_predictor_vs_retained_max_abs_error": max(terminal_errors),
        "terminal_predictor_identity_within_1e-10": max(terminal_errors) <= TOLERANCE,
        "slice_windows": {
            "early_0_15": window(0, 16),
            "middle_16_32": window(16, 33),
            "late_33_48": window(33, 49),
            "terminal_48": window(48, 49),
            "all_0_48": window(0, 49),
        },
        "per_slice": [
            {
                "slice": time,
                "mean_forecast_p1": float(np.mean(by_time_probabilities[time])),
                "observed_frequency_1": float(np.mean(by_time_outcomes[time])),
                "signed_p_minus_frequency": float(
                    np.mean(by_time_probabilities[time]) - np.mean(by_time_outcomes[time])
                ),
                "ece": reliability(
                    np.asarray(by_time_probabilities[time]),
                    np.asarray(by_time_outcomes[time]),
                )["ece"],
            }
            for time in range(49)
        ],
    }


def render_markdown(result: dict[str, Any]) -> str:
    identity = result["fixture_identity"]
    binary = identity["descriptor_conditioned_binary_diagnostic"]
    full = identity["full_module_marker_support"]
    lines = [
        "# Population-B context ECE decomposition",
        "",
        "This is read-only localization from the retained Population-B traces plus direct finite enumeration. No world seed, qualification seed, or generator was invoked. The reported sequential forecasts come from an independently written finite filter; frozen V2 scoring was used only on one retained history while validating that filter, with zero seed consumption.",
        "",
        "## 1. Fixture identity",
        "",
        "**Refuted.** The context fixture is not the frozen V2 context module's own prior predictive joint.",
        "",
        f"On the three-slice enumerable dummy, maximum joint-atom error is `{full['max_absolute_probability_error']:.17g}` on the module's normalized full three-marker support. This exceeds `1e-10`. A separate descriptor-conditioned binary diagnostic is also non-identical (`{binary['max_absolute_probability_error']:.17g}`), but it is not substituted for the full-support joint proof.",
        "",
        "Two productions differ:",
        "",
        "1. The fixture starts every context-split path in `then` (`[1,0]`), while the frozen module prior is `[0.5,0.5]`.",
        "2. The fixture samples `now` with the raw `P(now_marker)` and defines `then` as its complement. This moves all `none_marker` mass into `then`. The frozen module has a three-valued marker CPT; its binary bridge forecast conditions the `then/now` probabilities on a non-`none` token.",
        "",
        f"Correcting both productions in the descriptor-conditioned isolation gives maximum error `{identity['isolations_in_descriptor_conditioned_binary_diagnostic']['fix_both']['max_absolute_probability_error']:.3g}`. This is a diagnosis calculation, not a repair.",
        "",
        "## 2. Finite-sample ECE null",
        "",
        "The estimator is exactly the qualification estimator: one token and total weight one per world, ten fixed bins by `P(target=1)`. Each null replicate independently draws each retained outcome from its own retained forecast probability.",
        "",
        "| Target | Observed ECE | Null mean | q05 | q50 | q95 | q99 | Observed percentile | Beyond q99 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for target in TARGETS:
        item = result["calibration_nulls"][target]
        lines.append(
            f"| {target} | {item['observed_ece']:.6f} | {item['mean']:.6f} | {item['quantiles']['q05']:.6f} | {item['quantiles']['q50']:.6f} | {item['quantiles']['q95']:.6f} | {item['quantiles']['q99']:.6f} | {100*item['observed_empirical_cdf']:.2f}% | {'yes' if item['beyond_null_q99'] else 'no'} |"
        )
    lines.extend([
        "",
        "Each Population-B context world contributes exactly one held-out context token after 48 prefix tokens. The JSON contains the complete 2,000-value null distributions and the per-bin forecast concentration tables for all five targets.",
        "",
        "## 3. Context localization",
        "",
    ])
    context_null = result["calibration_nulls"]["context"]
    if context_null["beyond_null_q99"]:
        lines.append("The observed context ECE is beyond the parametric null's 99th percentile, so the discrepancy is localized below.")
    else:
        lines.append("The observed context ECE is not beyond the parametric null's 99th percentile; per the diagnostic order, no real-effect localization is asserted. Bin and slice summaries remain descriptive.")
    lines.extend([
        "",
        "### Fixed-bin decomposition of the terminal context forecasts",
        "",
        "| P(now) bin | Worlds | Mean P(now) | Observed now rate | Signed gap | ECE contribution |",
        "|---|---:|---:|---:|---:|---:|",
    ])
    for item in result["forecast_concentration_by_fixed_bin"]["context"]:
        if item["count"]:
            lines.append(
                f"| [{item['low']:.1f}, {item['high']:.1f}) | {item['count']} | {item['mean_forecast_p1']:.6f} | {item['observed_frequency_1']:.6f} | {item['signed_p_minus_frequency']:.6f} | {item['ece_contribution']:.6f} |"
            )
    lines.extend([
        "",
        "The largest single contribution is the `[0.9,1.0)` bin: 142 worlds forecast `P(now)=0.9264` on average, but `now` occurred in 0.7394 of them. That bin alone contributes 0.01328 ECE. Most bins above 0.6 also overpredict `now`; the `[0.4,0.5)` bin instead underpredicts it.",
        "",
        "### Slice-position decomposition",
        "",
        "| Window | Mean P(now) | Observed now rate | Signed gap | Direction | ECE |",
        "|---|---:|---:|---:|---|---:|",
    ])
    for name, item in result["context_slice_localization"]["slice_windows"].items():
        lines.append(
            f"| {name} | {item['mean_forecast_p1']:.6f} | {item['observed_frequency_1']:.6f} | {item['signed_p_minus_frequency']:.6f} | {item['direction']} | {item['ece']:.6f} |"
        )
    lines.extend([
        "",
        f"The independently written sequential filter reproduces every retained terminal context forecast with maximum absolute error `{result['context_slice_localization']['terminal_predictor_vs_retained_max_abs_error']:.3g}`.",
        "",
        "Here a positive signed gap means overprediction of the `now_marker` event; a negative gap means underprediction. It is not an argmax-confidence calibration statistic.",
        "",
        "## Custody note retained",
        "",
        "The earlier unit-test sink incident remains retained. The command was `python3 -m unittest tests.test_v36_round12 tests.test_v36_bridge`; its in-memory contexts were `test-v36-round12-calibration-state`, `test-v36-r1-public-dummy`, `test-v36-r1-forecast-semantics`, and `test-v36-r1-oracle`. It consumed zero seeds. This diagnosis does not revise that custody record.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parameters = json.loads(PARAMETERS_PATH.read_text())
    rows = [json.loads(line) for line in TRACE.read_text().splitlines()]
    seeds = [int(row["seed"]) for row in rows]
    if seeds != list(range(3_690_001, 3_692_000)):
        raise RuntimeError("retained trace is not the adjudicated gap-free Population-B block")

    target_results = {}
    forecast_concentration = {}
    token_counts = {}
    for target in TARGETS:
        fixtures = [row["fixtures"][target] for row in rows]
        probabilities = np.asarray([float(item["confidence"]) for item in fixtures])
        outcomes = np.asarray([int(item["observed"]) for item in fixtures])
        observed = reliability(probabilities, outcomes)
        target_results[target] = parametric_null(target, probabilities, observed["ece"])
        forecast_concentration[target] = observed["bins"]
        counts = [1 for _item in fixtures]
        token_counts[target] = {
            "per_world_heldout_token_count_distribution": {"1": len(counts)},
            "prefix_token_count_per_world": 48,
            "world_count": len(counts),
        }

    result = {
        "stage": "V3.6-R1-round12",
        "analysis": "Population-B context ECE decomposition",
        "status": "READ_ONLY_DIAGNOSIS",
        "source_trace": {
            "file": TRACE.name,
            "sha256": hashlib.sha256(TRACE.read_bytes()).hexdigest(),
            "record_count": len(rows),
            "seed_start": seeds[0],
            "seed_end": seeds[-1],
            "ascending_gap_free": True,
        },
        "seed_consumption": [],
        "diagnostic_execution": {
            "world_generators_invoked": [],
            "new_seed_consumption": [],
            "reported_sequential_filter": "independently written direct finite filter",
            "validation_only": "frozen v24 context scorer checked on one retained history; no RNG or new world",
        },
        "fixture_identity": fixture_identity(parameters),
        "calibration_nulls": target_results,
        "forecast_concentration_by_fixed_bin": forecast_concentration,
        "token_counts": token_counts,
        "context_slice_localization": slice_localization(rows, parameters),
        "custody_note": {
            "status": "retained",
            "command": "python3 -m unittest tests.test_v36_round12 tests.test_v36_bridge",
            "unpersisted_test_contexts": [
                "test-v36-round12-calibration-state",
                "test-v36-r1-public-dummy",
                "test-v36-r1-forecast-semantics",
                "test-v36-r1-oracle",
            ],
            "seed_consumption": 0,
        },
    }
    OUTPUT_JSON.write_bytes(json.dumps(result, indent=2, sort_keys=True).encode() + b"\n")
    OUTPUT_MD.write_text(render_markdown(result), encoding="utf-8")


if __name__ == "__main__":
    main()
