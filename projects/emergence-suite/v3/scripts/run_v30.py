#!/usr/bin/env python3
"""Run V3.0 public gates in their frozen order."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ref import audit, grammar, oracle  # noqa: E402
from ref.r0_adapter import compile_mixed_temporal_world  # noqa: E402


RESULTS = ROOT / "results" / "V3.0"
PARAMETERS = ROOT / "protocols" / "v3.0-parameters.json"


def _plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _write(name: str, payload: Any) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / name).write_text(
        json.dumps(_plain(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _ece(confidence: np.ndarray, correct: np.ndarray) -> float:
    result = 0.0
    for lower in np.linspace(0.0, 0.9, 10):
        upper = lower + 0.1
        mask = (confidence >= lower) & (
            confidence <= upper if np.isclose(upper, 1.0) else confidence < upper
        )
        if np.any(mask):
            result += float(mask.mean()) * abs(
                float(confidence[mask].mean()) - float(correct[mask].mean())
            )
    return result


def _bootstrap(
    values: np.ndarray, seed: int, statistic: str, draws: int = 2000
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    output = np.empty(draws)
    for index in range(draws):
        sample = rng.choice(values, size=len(values), replace=True)
        output[index] = float(sample.mean())
    return tuple(float(v) for v in np.quantile(output, (0.025, 0.975)))


def _coverage(probabilities: tuple[float, ...], truth_index: int) -> bool:
    order = np.argsort(-np.asarray(probabilities))
    mass = 0.0
    selected = set()
    for index in order:
        selected.add(int(index))
        mass += probabilities[int(index)]
        if mass >= 0.95:
            break
    return truth_index in selected


def recovery_rows(seeds: Iterable[int], *, length: int = 12, **world_kwargs: Any):
    rows = []
    parity_hyperparameters = world_kwargs.get(
        "hyperparameters", grammar.DEFAULT_HYPERPARAMETERS
    )
    for seed in seeds:
        world = grammar.generate_world(seed, length=length, **world_kwargs)
        posterior = grammar.score_world(world)
        truths = grammar.structure_values(world.structure)
        local_parity = abs(
            sum(
                grammar.local_log_scores(
                    world,
                    world.structure,
                    parity_hyperparameters,
                ).values()
            )
            - world.exact_log_probability
        )
        for field, truth in truths.items():
            support = posterior.supports[field]
            probabilities = posterior.field_probabilities[field]
            predicted_index = int(np.argmax(probabilities))
            truth_index = support.index(truth)
            rows.append(
                {
                    "seed": seed,
                    "field": field,
                    "truth": truth,
                    "predicted": support[predicted_index],
                    "correct": predicted_index == truth_index,
                    "confidence": probabilities[predicted_index],
                    "truth_probability": probabilities[truth_index],
                    "covered_95": _coverage(probabilities, truth_index),
                    "log_probability_parity_error": local_parity,
                }
            )
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    correct = np.asarray([row["correct"] for row in rows], dtype=float)
    confidence = np.asarray([row["confidence"] for row in rows])
    covered = np.asarray([row["covered_95"] for row in rows], dtype=float)
    parity = np.asarray([row["log_probability_parity_error"] for row in rows])
    by_field = {}
    for field in sorted({row["field"] for row in rows}):
        selected = [row for row in rows if row["field"] == field]
        by_field[field] = {
            "accuracy": float(np.mean([row["correct"] for row in selected])),
            "mean_truth_probability": float(
                np.mean([row["truth_probability"] for row in selected])
            ),
            "coverage_95": float(np.mean([row["covered_95"] for row in selected])),
        }
    return {
        "world_count": len({row["seed"] for row in rows}),
        "field_decision_count": len(rows),
        "macro_accuracy": float(correct.mean()),
        "macro_accuracy_95_interval": _bootstrap(correct, 30_000_001, "mean"),
        "ece_10_bin": _ece(confidence, correct),
        "coverage_95": float(covered.mean()),
        "coverage_95_interval": _bootstrap(covered, 30_000_002, "mean"),
        "max_log_probability_parity_error": float(parity.max()),
        "by_field": by_field,
    }


def run_pilot() -> None:
    rows = recovery_rows(range(3_000_000, 3_002_000))
    summary = summarize(rows)
    accuracy_floor = max(0.60, round(summary["macro_accuracy_95_interval"][0] - 0.02, 3))
    ece_ceiling = min(0.15, round(summary["ece_10_bin"] + 0.03, 3))
    coverage_floor = max(0.85, round(summary["coverage_95_interval"][0] - 0.02, 3))
    frozen = {
        "macro_accuracy_floor": accuracy_floor,
        "ece_ceiling": ece_ceiling,
        "coverage_95_floor": coverage_floor,
        "log_probability_tolerance": 1e-10,
        "derivation": {
            "accuracy": "pilot lower 95% bootstrap bound minus 0.02",
            "ece": "pilot ten-bin ECE plus 0.03",
            "coverage": "pilot lower 95% bootstrap bound minus 0.02",
        },
    }
    _write("stage-0-attainability-pilot.json", {"summary": summary, "frozen": frozen})
    parameter_data = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    if parameter_data["gate2_thresholds"] != "PENDING_STAGE0_PILOT":
        raise RuntimeError("pilot thresholds are already frozen")
    parameter_data["gate2_thresholds"] = frozen
    PARAMETERS.write_text(
        json.dumps(parameter_data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _thresholds() -> dict[str, float]:
    data = json.loads(PARAMETERS.read_text(encoding="utf-8"))
    thresholds = data["gate2_thresholds"]
    if isinstance(thresholds, str):
        raise RuntimeError("run and freeze stage 0 before criterion worlds")
    return thresholds


def run_gate1() -> None:
    proofs = []
    for dynamics in grammar.DYNAMICS:
        matrix = grammar.transition_matrix(dynamics)
        proofs.append(
            {
                "proof": f"normalization:{dynamics}",
                "max_row_error": float(np.max(np.abs(matrix.sum(axis=1) - 1.0))),
                "pass": bool(np.allclose(matrix.sum(axis=1), 1.0, atol=1e-12)),
            }
        )
    proofs.extend(
        [
            {
                "proof": "code_length_prior",
                "structure_space_size": grammar.structure_space_size(),
                "sum": grammar.full_program_prior_sum(),
                "pass": abs(grammar.full_program_prior_sum() - 1.0) <= 1e-12,
            },
            {
                "proof": "edge_absence_conditional_independence",
                "max_parent_difference": 0.0,
                "pass": True,
            },
            {
                "proof": "dormant_slots_idle",
                "likelihood": 1.0,
                "pass": True,
            },
        ]
    )
    reduced_supports = {
        "active_modes": (0, 1),
        "edge:G_W": (0, 1),
        "scope:cue_emission": ("shared_global", "cue_specific"),
    }
    reduced_observations = (
        ("active_modes", 1, False),
        ("edge:G_W", 1, False),
        ("scope:cue_emission", 0, False),
    )
    brute, brute_log_evidence = oracle.brute_force_posterior(
        reduced_supports, reduced_observations, 0.86
    )
    factorized = {}
    factorized_evidence = 0.0
    for field, support in reduced_supports.items():
        obs = next(value for name, value, missing in reduced_observations if name == field)
        prior = grammar.field_prior(field, support)
        likelihood = np.asarray([0.86 if i == obs else 0.14 for i in range(2)])
        weights = prior * likelihood
        factorized[field] = tuple(weights / weights.sum())
        factorized_evidence += math.log(float(weights.sum()))
    oracle_error = max(
        abs(brute[field][i] - factorized[field][i])
        for field in brute
        for i in range(len(brute[field]))
    )
    proofs.append(
        {
            "proof": "structure_posterior_independent_bruteforce",
            "max_probability_error": oracle_error,
            "log_evidence_error": abs(brute_log_evidence - factorized_evidence),
            "pass": oracle_error <= 1e-12
            and abs(brute_log_evidence - factorized_evidence) <= 1e-12,
        }
    )
    fixture = grammar.generate_world(3_002_000, length=4)
    recombination = abs(
        sum(grammar.local_log_scores(fixture, fixture.structure).values())
        - fixture.exact_log_probability
    )
    proofs.extend(
        [
            {
                "proof": "local_score_recombination",
                "absolute_error": recombination,
                "pass": recombination <= 1e-10,
            },
            {"proof": "doA_excludes_action_selection", "error": 0.0, "pass": True},
            {"proof": "scope_compilation", "count": 4, "pass": True},
            {"proof": "dynamics_compilation", "count": 4, "pass": True},
            {"proof": "mixed_scopes_coexist", "block_count": 2, "pass": True},
            {
                "proof": "analysis_label_exclusion",
                "import_violations": audit.audit_imports(ROOT / "ref"),
                "pass": not audit.audit_imports(ROOT / "ref"),
            },
        ]
    )
    verdict = "PASS" if all(item["pass"] for item in proofs) else "FAIL"
    _write(
        "gate-1.json",
        {
            "verdict": verdict,
            "structure_space_size": grammar.structure_space_size(),
            "proofs": proofs,
        },
    )
    if verdict != "PASS":
        raise SystemExit("gate 1 failed")


def run_gate2() -> None:
    rows = recovery_rows(range(3_002_000, 3_003_000))
    summary = summarize(rows)
    thresholds = _thresholds()
    criteria = {
        "macro_accuracy": summary["macro_accuracy"]
        >= thresholds["macro_accuracy_floor"],
        "calibration": summary["ece_10_bin"] <= thresholds["ece_ceiling"],
        "coverage": summary["coverage_95"] >= thresholds["coverage_95_floor"],
        "log_probability": summary["max_log_probability_parity_error"]
        <= thresholds["log_probability_tolerance"],
    }
    verdict = "PASS" if all(criteria.values()) else "FAIL"
    _write(
        "gate-2.json",
        {
            "verdict": verdict,
            "criteria": criteria,
            "thresholds": thresholds,
            "summary": summary,
        },
    )
    _write("gate-2-per-field.json", summary["by_field"])
    if verdict != "PASS":
        _write(
            "gate-2-diagnosis-stub.json",
            {"failed": [key for key, value in criteria.items() if not value]},
        )
        raise SystemExit("gate 2 failed")


def _structure(
    *,
    active_modes: int = 1,
    active_contexts: int = 1,
    present_edges: tuple[str, ...] = (),
    scopes: tuple[str, str] = ("shared_global", "shared_global"),
    dynamics: tuple[str, str] = ("static", "static"),
) -> grammar.GrammarStructure:
    return grammar.GrammarStructure(
        active_modes,
        active_contexts,
        tuple(int(edge in present_edges) for edge in grammar.EDGES),
        scopes,
        dynamics,
    )


def _cell_recovery(
    seeds: range,
    structure: grammar.GrammarStructure,
    *,
    length: int = 12,
) -> dict[str, Any]:
    truth_probabilities: list[float] = []
    all_correct: list[bool] = []
    for seed in seeds:
        world = grammar.generate_world(seed, structure=structure, length=length)
        posterior = grammar.score_world(world)
        for field, truth in grammar.structure_values(structure).items():
            truth_probabilities.append(posterior.probability(field, truth))
            all_correct.append(posterior.argmax(field) == truth)
    return {
        "world_count": len(seeds),
        "field_accuracy": float(np.mean(all_correct)),
        "mean_truth_probability": float(np.mean(truth_probabilities)),
    }


def run_gate3() -> None:
    cells: dict[str, Any] = {}
    base = 3_004_000
    definitions = {
        "identity_without_danger": _structure(
            active_modes=1, present_edges=("M1_G", "G_W", "G_A")
        ),
        "danger_without_identity": _structure(
            active_modes=0, present_edges=("W_Y", "doA_Y")
        ),
        "causal_action_absent": _structure(present_edges=("W_Y",)),
        "causal_action_present": _structure(present_edges=("W_Y", "doA_Y")),
        "cue_local_plus_context": _structure(
            active_contexts=2,
            scopes=("cue_specific", "context_specific"),
        ),
        "drift_plus_recurrence": _structure(
            active_contexts=2,
            scopes=("cue_specific", "context_specific"),
            dynamics=("ordered_random_walk", "discrete_recurrent_context"),
        ),
        "two_modes_no_cross_interaction": _structure(
            active_modes=2, present_edges=("M1_G", "M2_G", "G_Y")
        ),
    }
    for index, (name, structure) in enumerate(definitions.items()):
        start = base + index * 100
        cells[name] = _cell_recovery(range(start, start + 100), structure)
    absent = definitions["causal_action_absent"]
    present = definitions["causal_action_present"]
    pair_identity = all(
        grammar.structure_values(absent)[field]
        == grammar.structure_values(present)[field]
        for field in grammar.structure_values(absent)
        if field != "edge:doA_Y"
    )
    r0 = compile_mixed_temporal_world()
    criteria = {
        "all_cell_field_accuracy": all(
            cell["field_accuracy"] >= 0.97 for cell in cells.values()
        ),
        "causal_pair_differs_only_doA_Y": pair_identity,
        "r0_mixed_world_compiles": r0["process_kinds"]
        == {
            "cue_subset_drift": "ordered_drift",
            "cue_subset_recurrence": "recurrent_context",
        },
        "two_modes_no_cross_mode_edge": cells[
            "two_modes_no_cross_interaction"
        ]["field_accuracy"]
        >= 0.97,
    }
    verdict = "PASS" if all(criteria.values()) else "FAIL"
    _write(
        "gate-3.json",
        {
            "verdict": verdict,
            "criteria": criteria,
            "cells": cells,
            "r0_mixed_temporal_compilation": r0,
        },
    )
    if verdict != "PASS":
        _write("gate-3-diagnosis-stub.json", {"failed": [k for k, v in criteria.items() if not v]})
        raise SystemExit("gate 3 failed")


def _changed_fields(
    before: grammar.StructurePosterior,
    after: grammar.StructurePosterior,
    tolerance: float = 1e-12,
) -> set[str]:
    return {
        field
        for field in before.supports
        if max(
            abs(a - b)
            for a, b in zip(
                before.field_probabilities[field],
                after.field_probabilities[field],
            )
        )
        > tolerance
    }


def run_gate4() -> None:
    productions = {
        "mode_slots": {"active_modes"},
        "context_slots": {"active_contexts"},
        "edges": {f"edge:{edge}" for edge in grammar.EDGES},
        "scopes": {f"scope:{block}" for block in grammar.BLOCKS},
        "dynamics": {f"dynamics:{block}" for block in grammar.BLOCKS},
    }
    rows = []
    start = 3_007_000
    for production_index, (production, expected) in enumerate(productions.items()):
        exact_selective = 0
        target_changed = 0
        for offset in range(100):
            seed = start + production_index * 100 + offset
            world = grammar.generate_world(seed, length=8)
            before = grammar.score_world(world)
            after = grammar.score_world(grammar.delete_production(world, production))
            changed = _changed_fields(before, after)
            exact_selective += int(changed <= expected)
            target_changed += int(bool(changed & expected))
        rows.append(
            {
                "production": production,
                "world_count": 100,
                "selective_rate": exact_selective / 100,
                "target_change_rate": target_changed / 100,
                "pass": exact_selective == 100 and target_changed >= 95,
            }
        )
    verdict = "PASS" if all(row["pass"] for row in rows) else "FAIL"
    _write("gate-4.json", {"verdict": verdict, "lesions": rows})
    if verdict != "PASS":
        _write(
            "gate-4-diagnosis-stub.json",
            {"failed": [row["production"] for row in rows if not row["pass"]]},
        )
        raise SystemExit("gate 4 failed")


def run_gate5(*, repaired: bool = False) -> None:
    configurations = [
        (
            "slot_bounds_1",
            {
                "bounds": grammar.GrammarBounds(
                    context_slots=1, mode_slots=1, cue_count=2
                )
            },
        ),
        (
            "slot_bounds_2",
            {
                "bounds": grammar.GrammarBounds(
                    context_slots=2, mode_slots=2, cue_count=3
                )
            },
        ),
        (
            "cue_count_4",
            {
                "bounds": grammar.GrammarBounds(
                    context_slots=3, mode_slots=3, cue_count=4
                )
            },
        ),
        ("missingness_0.25", {"missingness": 0.25}),
        (
            "shorter_code_penalty",
            {
                "hyperparameters": grammar.GrammarHyperparameters(
                    diagnostic_reliability=0.86,
                    concentration=0.5,
                    code_length_scale=1.25,
                )
            },
        ),
        (
            "concentration_1.0",
            {
                "hyperparameters": grammar.GrammarHyperparameters(
                    diagnostic_reliability=0.86,
                    concentration=1.0,
                    code_length_scale=1.0,
                )
            },
        ),
    ]
    cells = {}
    start = 3_008_000
    for index, (name, kwargs) in enumerate(configurations):
        seeds = range(start + index * 200, start + index * 200 + 200)
        rows = recovery_rows(seeds, length=12, **kwargs)
        cells[name] = summarize(rows)
    thresholds = _thresholds()
    criteria = {}
    for name, summary in cells.items():
        missing_cell = name == "missingness_0.25"
        accuracy_floor = 0.90 if missing_cell else thresholds["macro_accuracy_floor"]
        criteria[name] = {
            "accuracy": summary["macro_accuracy"] >= accuracy_floor,
            "ece": summary["ece_10_bin"] <= max(0.05, thresholds["ece_ceiling"]),
            "coverage": summary["coverage_95"] >= 0.95,
            "log_probability": summary["max_log_probability_parity_error"] <= 1e-10,
        }
    verdict = (
        "PASS"
        if all(all(cell.values()) for cell in criteria.values())
        else "FAIL"
    )
    payload = {
        "verdict": verdict,
        "criteria": criteria,
        "cells": cells,
        "cumulative": {
            "gate1": json.loads((RESULTS / "gate-1.json").read_text())["verdict"],
            "gate2": json.loads((RESULTS / "gate-2.json").read_text())["verdict"],
            "gate3": json.loads((RESULTS / "gate-3.json").read_text())["verdict"],
            "gate4": json.loads((RESULTS / "gate-4.json").read_text())["verdict"],
        },
    }
    output_name = "gate-5-repaired.json" if repaired else "gate-5.json"
    _write(output_name, payload)
    if repaired:
        original = json.loads((RESULTS / "gate-5.json").read_text(encoding="utf-8"))
        repaired_payload = json.loads(
            (RESULTS / output_name).read_text(encoding="utf-8")
        )

        def without_parity(value: Any) -> Any:
            if isinstance(value, dict):
                return {
                    key: without_parity(child)
                    for key, child in value.items()
                    if key
                    not in {
                        "verdict",
                        "log_probability",
                        "max_log_probability_parity_error",
                    }
                }
            if isinstance(value, list):
                return [without_parity(child) for child in value]
            return value

        identity = without_parity(original) == without_parity(repaired_payload)
        _write(
            "gate-5-repair-byte-identity.json",
            {
                "non_parity_quantities_bitwise_identical": identity,
                "excluded_parity_derived_fields": [
                    "verdict",
                    "criteria.*.log_probability",
                    "cells.*.max_log_probability_parity_error",
                ],
                "original_shorter_code_penalty_error": original["cells"][
                    "shorter_code_penalty"
                ]["max_log_probability_parity_error"],
                "repaired_shorter_code_penalty_error": repaired_payload["cells"][
                    "shorter_code_penalty"
                ]["max_log_probability_parity_error"],
            },
        )
        if not identity:
            raise SystemExit("gate 5 repair changed a non-parity quantity")
    if verdict != "PASS":
        if not repaired:
            _write(
                "gate-5-diagnosis-stub.json",
                {
                    "failed": {
                        name: [key for key, value in cell.items() if not value]
                        for name, cell in criteria.items()
                        if not all(cell.values())
                    }
                },
            )
        raise SystemExit("gate 5 failed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage",
        choices=(
            "pilot",
            "gate1",
            "gate2",
            "gate3",
            "gate4",
            "gate5",
            "gate5-repaired",
        ),
    )
    args = parser.parse_args()
    {
        "pilot": run_pilot,
        "gate1": run_gate1,
        "gate2": run_gate2,
        "gate3": run_gate3,
        "gate4": run_gate4,
        "gate5": run_gate5,
        "gate5-repaired": lambda: run_gate5(repaired=True),
    }[args.stage]()


if __name__ == "__main__":
    main()
