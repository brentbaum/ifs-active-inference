#!/usr/bin/env python3

"""Accepted/rejected fixtures for every discriminated JSON-Schema variant."""

from __future__ import annotations

import copy
import json
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas"
IDS = {
    "configuration": "https://ifs-active-inference.local/experiment51/configuration.schema.json",
    "world": "https://ifs-active-inference.local/experiment51/world.schema.json",
    "protocol": "https://ifs-active-inference.local/experiment51/protocol.schema.json",
    "analysis": "https://ifs-active-inference.local/experiment51/analysis.schema.json",
}


def fixture(schema: str, definition: str, valid: dict, missing: str) -> dict:
    invalid = copy.deepcopy(valid)
    invalid.pop(missing)
    return {
        "name": f"{schema}:{definition}",
        "ref": f"{IDS[schema]}#/$defs/{definition}",
        "valid": valid,
        "invalid": invalid,
    }


def cases() -> list[dict]:
    identifier = "item-one"
    channel_base = {
        "id": identifier,
        "source": "world",
        "scope": ["node-one"],
        "enabled": True,
    }
    sampled_distribution_base = {
        "id": identifier,
        "sampling_scope": "world",
    }
    static_distribution_base = {"id": identifier}
    process_base = {
        "id": identifier,
        "target_factor": "factor-one",
        "update_interval": 1,
    }
    emission_base = {
        "id": identifier,
        "source_factors": ["factor-one"],
        "channel_id": "channel-one",
        "reliability_distribution_id": "reliability-one",
        "masked_scope": [],
    }
    event_base = {"id": identifier, "time": 1}
    intervention_base = {
        "id": identifier,
        "target_id": "target-one",
    }
    expression_field = {
        "op": "field",
        "path": "state.access.access-one.probability",
    }
    fixtures = [
        fixture("configuration", "discrete_channel", {
            **channel_base,
            "likelihood_family": "categorical",
            "value_labels": ["low", "high"],
        }, "value_labels"),
        fixture("configuration", "gaussian_channel", {
            **channel_base,
            "likelihood_family": "gaussian_bounded",
            "bounds": [-1.0, 1.0],
        }, "bounds"),
        fixture("world", "fixed_distribution", {
            **sampled_distribution_base, "family": "fixed", "value": 1.0,
        }, "value"),
        fixture("world", "uniform_distribution", {
            **sampled_distribution_base,
            "family": "uniform",
            "lower": 0.0,
            "upper": 1.0,
        }, "upper"),
        fixture("world", "integer_uniform_distribution", {
            **sampled_distribution_base,
            "family": "integer_uniform",
            "lower": 1,
            "upper": 4,
        }, "upper"),
        fixture("world", "beta_distribution", {
            **sampled_distribution_base,
            "family": "beta",
            "alpha": 2.0,
            "beta": 2.0,
        }, "beta"),
        fixture("world", "categorical_distribution", {
            **static_distribution_base,
            "family": "categorical",
            "values": ["low", "high"],
            "probabilities": [0.5, 0.5],
        }, "probabilities"),
        fixture("world", "transition_distribution", {
            **static_distribution_base,
            "family": "transition_matrix",
            "values": ["low", "high"],
            "matrix": [[0.8, 0.2], [0.2, 0.8]],
        }, "matrix"),
        fixture("world", "iid_process", {
            **process_base, "type": "iid", "distribution_id": "prior-one",
        }, "distribution_id"),
        fixture("world", "transition_process", {
            **process_base,
            "type": "markov",
            "transition_distribution_id": "transition-one",
        }, "transition_distribution_id"),
        fixture("world", "change_point_process", {
            **process_base,
            "type": "change_point",
            "before_transition_id": "before-one",
            "after_transition_id": "after-one",
            "change_time_distribution_id": "time-one",
        }, "change_time_distribution_id"),
        fixture("world", "action_process", {
            **process_base,
            "type": "action_contingent",
            "action": "approach",
            "baseline_transition_id": "before-one",
            "action_transition_id": "after-one",
        }, "action_transition_id"),
        fixture("world", "coupled_process", {
            **process_base,
            "type": "coupled_latent",
            "source_factors": ["parent-one"],
            "conditional_transition_ids": ["transition-one", "transition-two"],
        }, "conditional_transition_ids"),
        fixture("world", "discrete_emission", {
            **emission_base,
            "likelihood_family": "categorical",
            "conditional_distribution_ids": ["emission-one", "emission-two"],
        }, "conditional_distribution_ids"),
        fixture("world", "gaussian_emission", {
            **emission_base,
            "likelihood_family": "gaussian_bounded",
            "mean_by_configuration": [-0.5, 0.5],
            "noise_scale_distribution_id": "noise-one",
        }, "noise_scale_distribution_id"),
        fixture("world", "contingency", {
            "id": identifier,
            "action": "approach",
            "target_process": "process-one",
            "effect": "activate_action_transition",
            "enabled": True,
        }, "effect"),
        fixture("world", "action_outcome", {
            "id": identifier,
            "type": "action_outcome",
            "action": "approach",
            "source_factors": [],
            "success_probabilities": [0.8],
            "exposure_values": [1.0],
        }, "success_probabilities"),
        fixture("world", "hazard_outcome", {
            "id": identifier,
            "type": "hazard_outcome",
            "source_factors": [],
            "potential_probabilities": [0.2],
            "mitigating_actions": ["withdraw"],
        }, "potential_probabilities"),
        fixture("protocol", "equality_predicate", {
            "field": "run.arm", "comparator": "eq", "value": "arm-one",
        }, "value"),
        fixture("protocol", "numeric_predicate", {
            "field": "run.time", "comparator": "ge", "value": 2,
        }, "value"),
        fixture("protocol", "membership_predicate", {
            "field": "run.arm", "comparator": "in",
            "value": ["arm-one", "arm-two"],
        }, "value"),
        fixture("protocol", "finite_predicate", {
            "field": "run.time", "comparator": "finite",
        }, "comparator"),
        fixture("protocol", "observation_event", {
            **event_base,
            "kind": "observe",
            "source": "world",
            "channel_id": "channel-one",
            "emission_id": "emission-one",
            "repeat": 1,
            "interval": 1,
        }, "emission_id"),
        fixture("protocol", "imaginal_event", {
            **event_base,
            "kind": "imaginal",
            "source": "imaginal",
            "channel_id": "channel-one",
            "generator_id": "posterior-predictive-mode-v1",
            "repeat": 1,
            "interval": 1,
        }, "generator_id"),
        fixture("protocol", "intervention_event", {
            **event_base,
            "kind": "intervene",
            "source": "intervention",
            "intervention_id": "intervention-one",
        }, "intervention_id"),
        fixture("protocol", "stop_event", {
            **event_base,
            "kind": "stop_check",
            "source": "intervention",
            "stopping_rule_id": "stop-one",
        }, "stopping_rule_id"),
        fixture("protocol", "edge_intervention", {
            **intervention_base,
            "target_kind": "edge",
            "operation": "sever",
        }, "operation"),
        fixture("protocol", "channel_intervention", {
            **intervention_base,
            "target_kind": "observation_channel",
            "operation": "toggle",
        }, "operation"),
        fixture("protocol", "policy_intervention", {
            **intervention_base,
            "target_kind": "policy_action",
            "operation": "disable",
        }, "operation"),
        fixture("protocol", "contingency_intervention", {
            **intervention_base,
            "target_kind": "world_contingency",
            "operation": "toggle",
        }, "operation"),
        fixture("protocol", "trigger", {
            "kind": "external_proxy",
            "predicate": {"field": "run.time", "comparator": "ge", "value": 2},
        }, "predicate"),
        fixture("protocol", "trigger", {
            "kind": "latent_intervention",
            "predicate": {
                "field": "state.access.access-one.probability",
                "comparator": "ge",
                "value": 0.7,
            },
        }, "predicate"),
        fixture("protocol", "stopping_rule", {
            "id": identifier, "kind": "fixed_horizon", "max_time": 8,
        }, "max_time"),
        fixture("protocol", "stopping_rule", {
            "id": identifier,
            "kind": "trace_crossing",
            "max_time": 8,
            "field": "state.access.access-one.probability",
            "comparator": "ge",
            "threshold": 0.7,
            "persistence": 2,
        }, "field"),
        fixture("protocol", "control", {
            "id": "control-one",
            "kind": "external_proxy",
            "treatment_arms": ["treatment"],
            "control_arms": ["control"],
            "intervention_ids": ["intervention-one"],
            "budget_rule_ids": [],
        }, "control_arms"),
        fixture("protocol", "control", {
            "id": "control-one",
            "kind": "matched_capacity",
            "treatment_arms": ["treatment"],
            "control_arms": ["control"],
            "intervention_ids": ["intervention-one"],
            "budget_rule_ids": [],
        }, "control_arms"),
        fixture("protocol", "control", {
            "id": "control-one",
            "kind": "matched_budget",
            "treatment_arms": ["treatment"],
            "control_arms": ["control"],
            "intervention_ids": [],
            "budget_rule_ids": ["budget-one"],
        }, "budget_rule_ids"),
        fixture("protocol", "control", {
            "id": "control-one",
            "kind": "impossibility",
            "treatment_arms": ["treatment"],
            "control_arms": ["control"],
            "intervention_ids": [],
            "budget_rule_ids": [],
            "explanation": "No capacity-matched comparator can be constructed.",
        }, "explanation"),
        fixture("analysis", "literal_expression", {
            "op": "literal", "value": 0.1,
        }, "value"),
        fixture("analysis", "field_expression", expression_field, "path"),
        fixture("analysis", "where_expression", {
            "op": "where",
            "source": expression_field,
            "predicates": [{"field": "run.arm", "comparator": "eq", "value": "a"}],
        }, "predicates"),
        fixture("analysis", "simple_unary_expression", {
            "op": "terminal", "arg": expression_field,
        }, "arg"),
        fixture("analysis", "lag_expression", {
            "op": "lag", "arg": expression_field, "steps": 1,
        }, "steps"),
        fixture("analysis", "crossing_expression", {
            "op": "first_crossing",
            "arg": expression_field,
            "comparator": "ge",
            "threshold": 0.7,
            "persistence": 2,
        }, "persistence"),
        fixture("analysis", "slope_expression", {
            "op": "slope", "arg": expression_field, "time_path": "run.time",
        }, "time_path"),
        fixture("analysis", "quantile_expression", {
            "op": "quantile", "arg": expression_field, "probability": 0.5,
        }, "probability"),
        fixture("analysis", "binary_expression", {
            "op": "subtract", "left": expression_field, "right": expression_field,
        }, "right"),
        fixture("analysis", "arm_difference_expression", {
            "op": "arm_difference",
            "value": expression_field,
            "treatment": "treatment",
            "control": "control",
        }, "control"),
        fixture("analysis", "did_expression", {
            "op": "difference_in_differences",
            "value": expression_field,
            "treatment_present": "tp",
            "treatment_absent": "ta",
            "control_present": "cp",
            "control_absent": "ca",
        }, "control_absent"),
        fixture("analysis", "classification_expression", {
            "op": "classification_accuracy",
            "prediction_path": "state.context.context-one.posterior.factor-one.value-one",
            "truth_path": "world.truth.factor-one",
        }, "truth_path"),
        fixture("analysis", "argmax_expression", {
            "op": "argmax_match",
            "evidence_path": "state.structure.structure-one.log_evidence.*",
            "selected_path": "state.structure.structure-one.selected.*",
        }, "selected_path"),
        fixture("analysis", "budget_expression", {
            "op": "budget_relative_error",
            "evidence_budget_rule_id": "budget-one",
        }, "evidence_budget_rule_id"),
        fixture("analysis", "survival_expression", {
            "op": "survival_fraction",
            "arg": expression_field,
            "comparator": "ge",
            "threshold": 0.5,
        }, "threshold"),
        fixture("analysis", "equality_predicate", {
            "field": "run.arm", "comparator": "eq", "value": "arm-one",
        }, "value"),
        fixture("analysis", "numeric_predicate", {
            "field": "run.time", "comparator": "ge", "value": 2,
        }, "value"),
        fixture("analysis", "membership_predicate", {
            "field": "run.arm", "comparator": "in",
            "value": ["arm-one", "arm-two"],
        }, "value"),
        fixture("analysis", "finite_predicate", {
            "field": "run.time", "comparator": "finite",
        }, "comparator"),
        fixture("analysis", "interval", {
            "method": "none",
        }, "method"),
        fixture("analysis", "interval", {
            "method": "exact_binomial", "level": 0.95,
        }, "level"),
        fixture("analysis", "interval", {
            "method": "percentile_bootstrap", "level": 0.95, "resamples": 1000,
        }, "resamples"),
        fixture("analysis", "lower_decision_rule", {
            "id": "rule-one",
            "estimand_id": "estimand-one",
            "comparator": "ge",
            "threshold": 0.1,
            "interval_requirement": "lower_above_threshold",
        }, "threshold"),
        fixture("analysis", "upper_decision_rule", {
            "id": "rule-one",
            "estimand_id": "estimand-one",
            "comparator": "le",
            "threshold": 0.1,
            "interval_requirement": "upper_below_threshold",
        }, "threshold"),
        fixture("analysis", "between_decision_rule", {
            "id": "rule-one",
            "estimand_id": "estimand-one",
            "comparator": "between",
            "threshold": [-0.1, 0.1],
            "interval_requirement": "none",
        }, "threshold"),
        fixture("analysis", "equivalent_decision_rule", {
            "id": "rule-one",
            "estimand_id": "estimand-one",
            "comparator": "equivalent",
            "threshold": [-0.1, 0.1],
            "interval_requirement": "inside_equivalence",
        }, "threshold"),
    ]
    return fixtures


def run() -> None:
    fixtures = cases()
    ajv = ROOT / "contract" / "node_modules" / ".bin" / "ajv"
    if not ajv.exists():
        subprocess.run(
            [
                "npm",
                "ci",
                "--prefix",
                str(ROOT / "contract"),
                "--ignore-scripts",
                "--no-audit",
                "--no-fund",
            ],
            check=True,
        )
    valid_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "array",
        "prefixItems": [{"$ref": item["ref"]} for item in fixtures],
        "minItems": len(fixtures),
        "maxItems": len(fixtures),
    }
    invalid_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "array",
        "prefixItems": [{"not": {"$ref": item["ref"]}} for item in fixtures],
        "minItems": len(fixtures),
        "maxItems": len(fixtures),
    }
    with tempfile.TemporaryDirectory() as directory:
        temporary = pathlib.Path(directory)
        payloads = {
            "valid-schema.json": valid_schema,
            "invalid-schema.json": invalid_schema,
            "valid-data.json": [item["valid"] for item in fixtures],
            "invalid-data.json": [item["invalid"] for item in fixtures],
        }
        for name, payload in payloads.items():
            (temporary / name).write_text(json.dumps(payload), encoding="utf-8")
        references: list[str] = []
        for schema in IDS:
            references.extend(["-r", str(SCHEMAS / f"{schema}.schema.json")])
        for schema_name, data_name in (
            ("valid-schema.json", "valid-data.json"),
            ("invalid-schema.json", "invalid-data.json"),
        ):
            subprocess.run(
                [
                    str(ajv),
                    "validate",
                    "--spec=draft2020",
                    *references,
                    "-s",
                    str(temporary / schema_name),
                    "-d",
                    str(temporary / data_name),
                ],
                check=True,
            )
    print(f"schema variant conformance passed: {len(fixtures)} accepted/rejected pairs")


if __name__ == "__main__":
    run()
