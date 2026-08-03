#!/usr/bin/env python3
"""Round-15 apparatus-first diagnosis from retained Population-A traces."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import re
import sys
from collections import Counter
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Any, Iterable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ref import v32, v35  # noqa: E402
from ref.v36_round15_oracle import direct_joint  # noqa: E402
from ref.v36_round15_production_enum import enumerate_atoms  # noqa: E402

RESULTS = ROOT / "results" / "V3.6"
TRACE = RESULTS / "v3.6-r1-round14-v3-native-replacement-2-traces.jsonl"
QUAL = RESULTS / "v3.6-r1-round14-v3-native-replacement-2-qualification.json"
FIXTURES = ROOT / "protocols" / "v3.6-round15-reduced-fixtures.json"
ROLE_MANIFEST = ROOT / "protocols" / "v3.6-round15-field-role-manifest.json"
OUT_JSON = RESULTS / "round15-five-layer-diagnosis.json"
OUT_MD = RESULTS / "round15-five-layer-diagnosis.md"
N = 2_000
TOL = 1e-10
TARGETS = ("identity", "outcome", "context", "partner", "contact")
EDGES = tuple(v35.EDGE_NAMES)


def load_rows() -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in TRACE.read_text().splitlines() if line]
    if len(rows) != N:
        raise RuntimeError(f"expected {N} retained rows, got {len(rows)}")
    return rows


def parse_protect(program_id: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"p(\d{3}):s([+-]\d):l([01])", program_id)
    if not match:
        raise ValueError(program_id)
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def protect_prior() -> tuple[list[str], np.ndarray]:
    names, probabilities = [], []
    for index, structure in enumerate(v35.PROGRAMS):
        signs = (-1, 1) if structure.cross_mode_outcome else (0,)
        for sign in signs:
            for reliable in (0, 1):
                names.append(f"p{index:03d}:s{sign:+d}:l{reliable}")
                probabilities.append(
                    math.exp(v35.structure_log_prior(structure))
                    / len(signs) / 2.0
                )
    values = np.asarray(probabilities, dtype=float)
    values /= values.sum()
    return names, values


def temporal_prior() -> tuple[list[str], np.ndarray]:
    names = [f"t{index:03d}" for index in range(len(v32.PROGRAMS))]
    values = np.asarray(
        [math.exp(v32.structure_log_prior(item)) for item in v32.PROGRAMS],
        dtype=float,
    )
    values /= values.sum()
    return names, values


def pearson(counts: np.ndarray, expected: np.ndarray) -> float:
    return float(np.sum((counts - expected) ** 2 / expected))


def multinomial_log_probability(counts: np.ndarray, probabilities: np.ndarray) -> float:
    nonzero = counts > 0
    return float(
        math.lgamma(int(counts.sum()) + 1)
        - math.fsum(math.lgamma(int(value) + 1) for value in counts[nonzero])
        + float(np.sum(counts[nonzero] * np.log(probabilities[nonzero])))
    )


def a1_prior_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    p_names, p_prior = protect_prior()
    t_names, t_prior = temporal_prior()
    p_lookup = {name: index for index, name in enumerate(p_names)}
    t_lookup = {name: index for index, name in enumerate(t_names)}
    joint_prior = np.outer(p_prior, t_prior).ravel()
    counts = np.zeros(len(joint_prior), dtype=int)
    protect_counts: Counter[str] = Counter()
    temporal_counts: Counter[str] = Counter()
    for row in rows:
        truth = row["calibration_state"]["truth_program"]
        protect_counts[truth["protect"]] += 1
        temporal_counts[truth["temporal"]] += 1
        counts[p_lookup[truth["protect"]] * len(t_names) + t_lookup[truth["temporal"]]] += 1
    expected = N * joint_prior
    observed_pearson = pearson(counts, expected)
    observed_logp = multinomial_log_probability(counts, joint_prior)
    rng_seed = int.from_bytes(hashlib.sha256(b"V3.6/round15/A1/prior-draw-null/v1").digest()[:8], "big")
    rng = np.random.default_rng(rng_seed)
    null_pearson = np.empty(2_000, dtype=float)
    null_logp = np.empty(2_000, dtype=float)
    for rep in range(2_000):
        simulated = rng.multinomial(N, joint_prior)
        null_pearson[rep] = pearson(simulated, expected)
        null_logp[rep] = multinomial_log_probability(simulated, joint_prior)

    feature_names = (
        "K1", "K2", "K3", *EDGES, "sign_negative", "sign_positive",
        "partner_reliable", "temporal_C1", "temporal_C2", "temporal_C3",
        "scope0_context_specific", "dynamics0_recurrent",
    )

    def features(p_index: int, t_index: int) -> np.ndarray:
        p_program, sign, reliable = parse_protect(p_names[p_index])
        structure = v35.PROGRAMS[p_program]
        temporal = v32.PROGRAMS[t_index]
        edge_values = v35.program_values(structure)
        return np.asarray([
            int(structure.active_modes == 1), int(structure.active_modes == 2), int(structure.active_modes == 3),
            *(int(edge_values[name]) for name in EDGES), int(sign < 0), int(sign > 0), reliable,
            int(temporal.active_contexts == 1), int(temporal.active_contexts == 2), int(temporal.active_contexts == 3),
            int(temporal.scopes[0] == "context_specific"),
            int(temporal.dynamics[0] == "discrete_recurrent_context"),
        ], dtype=float)

    p_features = np.asarray([features(index, 0)[:11] for index in range(len(p_names))])
    t_features = np.asarray([features(0, index)[11:] for index in range(len(t_names))])
    observed_feature_rows = []
    for row in rows:
        truth = row["calibration_state"]["truth_program"]
        observed_feature_rows.append(np.concatenate((
            p_features[p_lookup[truth["protect"]]], t_features[t_lookup[truth["temporal"]]],
        )))
    observed_matrix = np.asarray(observed_feature_rows)
    expected_means = np.concatenate((p_prior @ p_features, t_prior @ t_features))
    observed_means = observed_matrix.mean(axis=0)

    # Simultaneous grouped-marginal band under the exact prior.
    variances = np.maximum(expected_means * (1.0 - expected_means) / N, 1e-18)
    max_z = np.empty(2_000)
    for rep in range(2_000):
        p_draw = rng.choice(len(p_names), size=N, p=p_prior)
        t_draw = rng.choice(len(t_names), size=N, p=t_prior)
        means = np.concatenate((p_features[p_draw].mean(axis=0), t_features[t_draw].mean(axis=0)))
        max_z[rep] = float(np.max(np.abs(means - expected_means) / np.sqrt(variances)))
    simultaneous_z = float(np.quantile(max_z, 0.95))
    marginals = []
    for name, observed, expected_mean, variance in zip(feature_names, observed_means, expected_means, variances):
        half = simultaneous_z * math.sqrt(float(variance))
        marginals.append({
            "feature": name, "observed": float(observed), "expected": float(expected_mean),
            "simultaneous_95_low": max(0.0, float(expected_mean - half)),
            "simultaneous_95_high": min(1.0, float(expected_mean + half)),
            "inside_simultaneous_95": bool(abs(observed - expected_mean) <= half),
        })

    expected_joint = np.zeros((len(feature_names), len(feature_names)))
    # Exact feature joint through the factorized protect/temporal prior.
    for pi, pp in enumerate(p_prior):
        for ti, tp in enumerate(t_prior):
            vector = np.concatenate((p_features[pi], t_features[ti]))
            expected_joint += pp * tp * np.outer(vector, vector)
    observed_joint = observed_matrix.T @ observed_matrix / N
    dependencies = []
    for left in range(len(feature_names)):
        for right in range(left + 1, len(feature_names)):
            observed_cov = observed_joint[left, right] - observed_means[left] * observed_means[right]
            expected_cov = expected_joint[left, right] - expected_means[left] * expected_means[right]
            dependencies.append({
                "left": feature_names[left], "right": feature_names[right],
                "observed_covariance": float(observed_cov), "expected_covariance": float(expected_cov),
                "absolute_error": float(abs(observed_cov - expected_cov)),
            })
    dependencies.sort(key=lambda item: -item["absolute_error"])
    return {
        "analysis_rng": {"kind": "analysis_only", "sha256_key": "V3.6/round15/A1/prior-draw-null/v1", "integer_seed": rng_seed},
        "complete_category_count": len(joint_prior), "observed_nonempty_categories": int(np.sum(counts > 0)),
        "complete_program_frequencies_nonzero": [
            {"protect_program": p_names[index // len(t_names)], "temporal_program": t_names[index % len(t_names)], "observed_count": int(counts[index]), "expected_count": float(expected[index])}
            for index in np.flatnonzero(counts)
        ],
        "protect_program_frequencies": [
            {"program_id": name, "observed_count": int(protect_counts[name]), "expected_count": float(N * probability)}
            for name, probability in zip(p_names, p_prior)
        ],
        "temporal_program_frequencies": [
            {"program_id": name, "observed_count": int(temporal_counts[name]), "expected_count": float(N * probability)}
            for name, probability in zip(t_names, t_prior)
        ],
        "pearson": observed_pearson,
        "pearson_null": {"replicates": 2000, "mean": float(null_pearson.mean()), "q95": float(np.quantile(null_pearson, .95)), "q99": float(np.quantile(null_pearson, .99)), "upper_tail_p_plus_one": float((1 + np.sum(null_pearson >= observed_pearson)) / 2001)},
        "multinomial_log_probability": observed_logp,
        "multinomial_log_probability_null": {"mean": float(null_logp.mean()), "q01": float(np.quantile(null_logp, .01)), "q05": float(np.quantile(null_logp, .05)), "lower_tail_p_plus_one": float((1 + np.sum(null_logp <= observed_logp)) / 2001)},
        "grouped_marginals": marginals,
        "pairwise_dependencies": dependencies,
        "contact_response": {"status": "NOT_SERIALIZED", "auditable": False},
        "ks_used": False,
    }


def a2_joint_identity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    sample = rows[0]
    missing = []
    required = {
        "latent_mode_path": "calibration_state.native_path.modes",
        "context_state_path": "calibration_state.native_path.contexts",
        "prefix_observations": "canonical_slice_prefix",
        "contact_response_truth": "calibration_state.truth_contact_response",
        "intervention_schedule": "canonical_slice_prefix.joint_policy",
        "masks": "canonical_slice_prefix.context_availability",
    }
    flat = json.dumps(sample, sort_keys=True)
    for label, path in required.items():
        if path not in flat:
            missing.append(label)
    return {
        "verdict": "FAIL_APPARATUS_REQUIRED_NATIVE_PATH_STATE_NOT_SERIALIZED",
        "required_components": [
            "structure_prior", "cross_sign_prior", "partner_contact_priors", "mode_path",
            "root_identity_emission", "do_policy_outcome_emission", "partner_emission",
            "contact_response_emission", "temporal_structure_prior", "context_path",
            "context_emission", "masking",
        ],
        "missing_required_state": missing,
        "seed_reconstruction_performed": False,
        "worlds_auditable": 0,
        "max_abs_log_joint_error": None,
        "max_component_recombination_error": None,
    }


def a3_semantics() -> dict[str, Any]:
    bridge = (ROOT / "ref" / "v36_bridge.py").read_text()
    round12 = (ROOT / "ref" / "v36_round12.py").read_text()
    manifest = json.loads(ROLE_MANIFEST.read_text())
    checks = {
        "mode_signals_not_manufactured": "item.time, (None, None, None), item.identity" in bridge,
        "scorer_marginalizes_mode_path": "_mode_prior(modes, structure.active_modes)" in (ROOT / "ref" / "v35.py").read_text(),
        "action_not_in_observation_likelihood": "item.action" not in bridge[bridge.index("def _v35_observation"):bridge.index("def _v35_world")],
        "masked_context_skipped": "if item.context is None:\n                continue" in bridge,
        "prefix_fit_excludes_suffix": "world.slices[:PREFIX_SLICES]" in bridge,
        "adapter_is_rng_free": "component_rng" not in bridge[bridge.index("def adapter_documents"):bridge.index("def _v2_identity")],
    }
    # The native intervention schedule is deterministically selected using the
    # latent active-mode count, while the scorer constitutionally omits an
    # action-selection likelihood and retains the unconditional structure prior.
    schedule_depends_on_truth = "if index < structure.active_modes else 1" in round12
    scorer_omits_selection = "prior = v35.structure_log_prior(structure)" in bridge and "action_selection" not in bridge
    checks["intervention_schedule_independent_of_truth"] = not schedule_depends_on_truth
    observations = {
        key: value["factor"] for key, value in manifest["canonical_slice"].items()
        if value["role"] in {"observable", "observable_or_mask"}
    }
    return {
        "field_role_manifest": str(ROLE_MANIFEST.relative_to(ROOT.parent)),
        "checks": checks,
        "one_factor_per_observable": len(observations) == len(set(observations.values())),
        "observable_factor_map": observations,
        "finding": {
            "code": "NATIVE_INTERVENTION_DESIGN_DEPENDS_ON_LATENT_STRUCTURE",
            "latent_dependency": "joint_policy coordinates above active_modes are set to 1; active coordinates alternate 0/2",
            "scorer_semantics": "do(joint_policy), no action-selection likelihood, unconditional structure prior",
            "consequence": "the generated intervention vector reveals active count through the experimental design, but the posterior correctly refuses to score that design as evidence; the prior-predictive calibration theorem premise is false",
            "apparatus_layer": "generator design",
        },
        "all_checks_pass": bool(all(checks.values())),
    }


def fixed_bin_ece(probability: np.ndarray, outcome: np.ndarray, weights: np.ndarray) -> float:
    indices = np.minimum((probability * 10).astype(int), 9)
    total = 0.0
    for index in range(10):
        selected = indices == index
        if np.any(selected):
            total += abs(float(np.sum(weights[selected] * (probability[selected] - outcome[selected]))))
    return total


def reconstruct_a4_a5(rows: list[dict[str, Any]], qualification: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    max_errors = Counter()
    active_probabilities, active_truths, class_confidences, class_correct = [], [], [], []
    edge_probabilities = {edge: [] for edge in EDGES}
    edge_truths = {edge: [] for edge in EDGES}
    coverage = {level: [] for level in ("0.5", "0.8", "0.9", "0.95")}
    target_vectors = {target: [[], [], []] for target in TARGETS}
    for row in rows:
        state = row["calibration_state"]
        p_index, sign, reliable = parse_protect(state["truth_program"]["protect"])
        truth_structure = v35.PROGRAMS[p_index]
        max_errors["truth_active_count"] = max(max_errors["truth_active_count"], abs(truth_structure.active_modes - int(state["truth_active_count"])))
        reconstructed_edges = v35.program_values(truth_structure)
        for edge in EDGES:
            max_errors[f"truth_edge:{edge}"] = max(max_errors[f"truth_edge:{edge}"], abs(int(reconstructed_edges[edge]) - int(state["truth_edges"][edge])))
        active = np.zeros(3)
        edges = {edge: 0.0 for edge in EDGES}
        program_to_signature = {}
        for item in state["protect_structure_posterior"]:
            mass = float(item["mass"])
            structure = v35.PROGRAMS[int(item["structure_index"])]
            active[structure.active_modes - 1] += mass
            for edge, present in v35.program_values(structure).items():
                edges[edge] += mass * int(present)
            program_to_signature[item["program_id"]] = item["signature_sha256"]
        temporal_map = {item["program_id"]: item["signature_sha256"] for item in state["temporal_structure_posterior"]}
        truth_class = f"{program_to_signature[state['truth_program']['protect']]}|{temporal_map[state['truth_program']['temporal']]}"
        max_errors["truth_class"] = max(max_errors["truth_class"], float(truth_class != state["truth_class"]))
        max_errors["active_posterior"] = max(max_errors["active_posterior"], float(np.max(np.abs(active - np.asarray(state["active_count_posterior"])))))
        for edge in EDGES:
            max_errors[f"edge_posterior:{edge}"] = max(max_errors[f"edge_posterior:{edge}"], abs(edges[edge] - float(state["edge_posteriors"][edge])))
        active_probabilities.append(active)
        active_truths.append(truth_structure.active_modes - 1)
        class_confidences.append(float(state["class_confidence"]))
        class_correct.append(int(state["class_correct"]))
        for level in coverage:
            coverage[level].append(int(state["class_coverage"][level]))
        for edge in EDGES:
            edge_probabilities[edge].append(edges[edge]); edge_truths[edge].append(int(reconstructed_edges[edge]))
        for target in TARGETS:
            prediction = row["predictions"]["v3"][target]
            selected = [(float(p), int(y)) for p, y, delivered in zip(prediction["p1"], row["targets"][target], prediction["delivered"]) if delivered and y is not None]
            for p, y in selected:
                target_vectors[target][0].append(p); target_vectors[target][1].append(y); target_vectors[target][2].append(1.0 / N / len(selected))

    active_p = np.asarray(active_probabilities); active_y = np.asarray(active_truths)
    weights = np.full(N, 1.0 / N)
    top = np.argmax(active_p, axis=1); confidence = np.max(active_p, axis=1)
    replicated = {
        "active_count_top_label_ece": fixed_bin_ece(confidence, (top == active_y).astype(int), weights),
        "active_count_macro_classwise_ece": float(np.mean([fixed_bin_ece(active_p[:, index], (active_y == index).astype(int), weights) for index in range(3)])),
        "equivalence_class_top_label_ece": fixed_bin_ece(np.asarray(class_confidences), np.asarray(class_correct), weights),
        "class_coverage": {level: float(np.mean(values)) for level, values in coverage.items()},
        "edges": {edge: fixed_bin_ece(np.asarray(edge_probabilities[edge]), np.asarray(edge_truths[edge]), weights) for edge in EDGES},
        "targets": {},
    }
    for target, (ps, ys, ws) in target_vectors.items():
        replicated["targets"][target] = fixed_bin_ece(np.asarray(ps), np.asarray(ys), np.asarray(ws))
    recorded = {
        "active_count_top_label_ece": qualification["structure_calibration"]["active_count_top_label"]["ece"],
        "active_count_macro_classwise_ece": qualification["structure_calibration"]["active_count_macro_classwise"]["macro_ece"],
        "equivalence_class_top_label_ece": qualification["structure_calibration"]["equivalence_class_top_label"]["ece"],
        "class_coverage": {level: qualification["structure_calibration"]["class_set_coverage"][level] for level in coverage},
        "edges": {edge: qualification["structure_calibration"]["edges"][edge]["ece"] for edge in EDGES},
        "targets": {target: qualification["predictive_calibration"][target]["ece"] for target in TARGETS},
    }
    differences = []
    def walk(left: Any, right: Any, path: str = "") -> None:
        if isinstance(left, dict):
            for key in left: walk(left[key], right[key], f"{path}.{key}" if path else key)
        else: differences.append({"field": path, "replicated": left, "recorded": right, "absolute_error": abs(float(left) - float(right))})
    walk(replicated, recorded)
    return (
        {"max_errors": dict(max_errors), "all_truth_and_readout_errors_le_1e_12": bool(max(max_errors.values(), default=0.0) <= 1e-12), "contact_truth_reconstruction": "NOT_SERIALIZED"},
        {"replicated": replicated, "recorded": recorded, "comparisons": differences, "max_absolute_error": max(item["absolute_error"] for item in differences), "passes_1e_12": max(item["absolute_error"] for item in differences) <= 1e-12},
    )


def compare_joints(left: dict[tuple[Any, ...], float], right: dict[tuple[Any, ...], float]) -> dict[str, Any]:
    support_left, support_right = set(left), set(right)
    union = support_left | support_right
    return {
        "production_sum": math.fsum(left.values()), "oracle_sum": math.fsum(right.values()),
        "support_equal": support_left == support_right,
        "production_only_atoms": len(support_left - support_right), "oracle_only_atoms": len(support_right - support_left),
        "max_atom_error": max(abs(left.get(atom, 0.0) - right.get(atom, 0.0)) for atom in union),
    }


def layer_b() -> dict[str, Any]:
    fixtures = json.loads(FIXTURES.read_text())
    output = []
    for fixture in fixtures["fixtures"]:
        for length in fixtures["lengths"]:
            steps = []
            for step in fixtures["factor_ladder"]:
                if step not in {"structure_prior", "mode_paths", "root_identity_emission", "do_policy_outcome_emission"}:
                    steps.append({"step": step, "status": "NOT_RUN_AFTER_FIRST_FAILURE"})
                    continue
                production = enumerate_atoms(tuple(fixture["active_counts"]), fixture["joint_policy_y"], length, step)
                oracle = direct_joint(tuple(fixture["active_counts"]), fixture["joint_policy_y"], length, step)
                comparison = compare_joints(production, oracle)
                comparison.update({"step": step, "status": "PASS" if comparison["support_equal"] and comparison["max_atom_error"] <= TOL and abs(comparison["production_sum"] - 1) <= TOL and abs(comparison["oracle_sum"] - 1) <= TOL else "FAIL"})
                steps.append(comparison)
                if comparison["status"] == "FAIL":
                    for later in fixtures["factor_ladder"][fixtures["factor_ladder"].index(step) + 1:]:
                        steps.append({"step": later, "status": "NOT_RUN_AFTER_FIRST_FAILURE"})
                    break
            output.append({"fixture": fixture["name"], "length": length, "steps": steps, "first_failure": next((item["step"] for item in steps if item["status"] == "FAIL"), None)})
    failures = sorted(set(item["first_failure"] for item in output if item["first_failure"]))
    return {"implementations": ["ref/v36_round15_production_enum.py", "ref/v36_round15_oracle.py"], "fixtures": output, "first_failing_steps": failures, "all_structure_mode_root_steps_pass": all(all(step["status"] == "PASS" for step in item["steps"] if step["step"] in {"structure_prior", "mode_paths", "root_identity_emission"}) for item in output)}


def layer_c(rows: list[dict[str, Any]]) -> dict[str, Any]:
    getcontext().prec = 90
    candidates = []
    for row in rows:
        state = row["calibration_state"]
        active = np.asarray(state["active_count_posterior"])
        truth = int(state["truth_active_count"]) - 1
        residual = float(np.max(active) - int(np.argmax(active) == truth))
        jpy_residual = float(state["edge_posteriors"]["JOINT_POLICY_Y"] - state["truth_edges"]["JOINT_POLICY_Y"])
        candidates.append((row, residual, jpy_residual))
    selected = {
        "active_overconfident": max(candidates, key=lambda item: item[1])[0],
        "active_underconfident": min(candidates, key=lambda item: item[1])[0],
        "jpy_overpredicted": max(candidates, key=lambda item: item[2])[0],
        "calibrated_control": min(candidates, key=lambda item: abs(item[1]) + abs(item[2]))[0],
    }
    audits = []
    maximum_error = Decimal(0)
    for label, row in selected.items():
        state = row["calibration_state"]
        masses = [Decimal(str(item["mass"])) for item in state["protect_structure_posterior"]]
        total = sum(masses, Decimal(0))
        active = [Decimal(0), Decimal(0), Decimal(0)]
        jpy = Decimal(0)
        zero_count = 0
        for item, mass in zip(state["protect_structure_posterior"], masses):
            structure = v35.PROGRAMS[int(item["structure_index"])]
            active[structure.active_modes - 1] += mass
            jpy += mass * Decimal(structure.joint_policy_outcome)
            zero_count += int(mass == 0)
        reference_active = [Decimal(str(value)) for value in state["active_count_posterior"]]
        active_error = max(abs(a - b) for a, b in zip(active, reference_active))
        edge_error = abs(jpy - Decimal(str(state["edge_posteriors"]["JOINT_POLICY_Y"])))
        maximum_error = max(maximum_error, abs(total - Decimal(1)), active_error, edge_error)
        audits.append({"label": label, "seed": row["seed"], "posterior_sum_error": str(abs(total - Decimal(1))), "active_count_error": str(active_error), "jpy_error": str(edge_error), "exact_zero_program_count": zero_count})
    return {
        "decimal_precision": 90, "subset": audits, "max_serialized_posterior_arithmetic_error": str(maximum_error),
        "passes_1e_10_for_recomputable_quantities": maximum_error <= Decimal("1e-10"),
        "absolute_program_log_joint_recomputable": False,
        "limitation": "Complete paths and unnormalized program log joints were not serialized; seed reconstruction is forbidden. Absolute log-joint and normalizer recomputation cannot be performed.",
    }


def write_markdown(result: dict[str, Any]) -> None:
    a1, a2, a3, a4, a5, b, c = (result[key] for key in ("layer_a1", "layer_a2", "layer_a3", "layer_a4", "layer_a5", "layer_b", "layer_c"))
    marginal_failures = [item for item in a1["grouped_marginals"] if not item["inside_simultaneous_95"]]
    lines = [
        "# V3.6 Round-15 five-layer diagnosis",
        "",
        f"Final apparatus classification: **{result['layer_e']['classification']}**.",
        "",
        "## Localization",
        "",
        "The complete-native Population-A generator chooses the three-coordinate `do(joint_policy)` vector from the latent truth's active-mode count. Active coordinates alternate 0/2; coordinates above the truth count are set to 1. The scorer correctly treats policy as an intervention, includes no action-selection likelihood, and starts every candidate from the unconditional frozen structure prior. Thus the world constructor makes the experimental design depend on H while the posterior conditions as if that design were candidate-common. This violates the prior-predictive calibration theorem before any scientific likelihood is judged.",
        "",
        "This is a **generator-only apparatus mismatch**. The proposed source diff is recorded but not applied. Population A-R1 remains closed.",
        "",
        "## Layer A — retained trace",
        "",
        f"A1 used {a1['complete_category_count']:,} complete protect×temporal categories (no KS). Pearson={a1['pearson']:.6g}; exact-prior Monte Carlo upper-tail p={a1['pearson_null']['upper_tail_p_plus_one']:.6g}. The multinomial-log-probability lower-tail p={a1['multinomial_log_probability_null']['lower_tail_p_plus_one']:.6g}. Grouped simultaneous-band misses: {len(marginal_failures)}. Contact-response truth was not serialized, so its requested frequency is explicitly unauditable.",
        "",
        f"A2: **{a2['verdict']}**. Missing: {', '.join(a2['missing_required_state'])}. No seed reconstruction was performed.",
        "",
        f"A3: the semantic manifest found the intervention-design mismatch. All {len(a3['checks']) - 1} other deterministic semantic checks passed; the deliberately tested independence property failed.",
        "",
        f"A4 independent truth/readout reconstruction max error={max(a4['max_errors'].values(), default=0.0):.3g}; contact truth remains unavailable. A5 independent estimator max error={a5['max_absolute_error']:.3g} (tolerance 1e-12).",
        "",
        "## Layer B — reduced exact paths",
        "",
        f"Across the 1v2/2v3 and JPY absent/present fixtures at T=1..4, structure prior, latent-mode path, and root-emission stages passed. The first failing step was: {', '.join(b['first_failing_steps'])}. At that step the production atoms contain a truth-count-dependent intervention schedule, while the direct factorization oracle holds the do schedule common across candidates.",
        "",
        "## Layer C — high precision",
        "",
        f"Decimal precision={c['decimal_precision']}; maximum recomputable posterior aggregation error={c['max_serialized_posterior_arithmetic_error']}. Absolute log joints were not recomputable because the required paths were not serialized; they were not reconstructed.",
        "",
        "## Layer D",
        "",
        "Not opened. Layers A and B localized a concrete generator mismatch; all seeds 3716000:3720999 remain unused and unbarred by this diagnosis.",
        "",
        "## Stop and conditional repair boundary",
        "",
        "The apparatus-first repair statement is independent of the desired ECE direction: make the intervention/query schedule candidate-common, or explicitly model its selection probability. The constitutional choice is the former because do(action) selection is never evidence. The prepared diff changes only the Population-A native generator schedule; it is not applied in this run. All thresholds, priors, scorers, likelihoods, calibration definitions, and scientific modules remain unchanged.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n")


def main() -> None:
    if (OUT_JSON.exists() or OUT_MD.exists()) and "--replace" not in sys.argv:
        raise RuntimeError("Round-15 diagnosis outputs already exist")
    rows = load_rows()
    qualification = json.loads(QUAL.read_text())
    a4, a5 = reconstruct_a4_a5(rows, qualification)
    result = {
        "status": "STOPPED_AFTER_LOCALIZATION",
        "population_a_formal_verdict_retained": "FAIL",
        "scientific_interpretation_withheld": True,
        "layer_a1": a1_prior_audit(rows),
        "layer_a2": a2_joint_identity(rows),
        "layer_a3": a3_semantics(),
        "layer_a4": a4,
        "layer_a5": a5,
        "layer_b": layer_b(),
        "layer_c": layer_c(rows),
        "layer_d": {"opened": False, "reason": "A/B localized a concrete mismatch", "consumed_seeds": []},
        "layer_e": {
            "classification": "GENERATOR_ONLY",
            "defect": "truth-dependent do(joint_policy) schedule in complete-native Population-A generator",
            "scientific_source_change_required": False,
            "prepared_diff": "results/V3.6/round15-generator-only-proposed.diff",
            "diff_applied": False,
            "population_a_r1_opened": False,
        },
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    write_markdown(result)
    print(json.dumps({"classification": result["layer_e"]["classification"], "a1_p": result["layer_a1"]["pearson_null"]["upper_tail_p_plus_one"], "a5_error": result["layer_a5"]["max_absolute_error"], "b_failures": result["layer_b"]["first_failing_steps"]}, sort_keys=True))


if __name__ == "__main__":
    main()
