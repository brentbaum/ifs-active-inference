import unittest
from dataclasses import fields
from types import MappingProxyType

import numpy as np

from ref.audit import ProtocolState, audit_one_posterior
from ref.factor import Factor
from ref.inference import ExactEngine
from ref.model import FiniteModel, Variable
from ref.oracle import brute_force
from ref.rng import component_rng
from ref.v20 import factor_sensitivity, model_comparison, recovery, semantic_models, semantic_proof


class KernelTests(unittest.TestCase):
    def test_all_semantic_graphs_match_independent_enumeration(self):
        errors = semantic_proof()
        self.assertEqual(set(errors), {"chain", "fork", "collider", "temporal"})
        self.assertLess(max(errors.values()), 1e-10)

    def test_factor_deletion_and_mutation_are_detectable(self):
        effects = factor_sensitivity()
        self.assertGreater(min(effects.values()), 1e-3)

    def test_recovery_and_calibration(self):
        result = recovery()
        self.assertGreaterEqual(result["state_accuracy"], 0.75)
        self.assertLessEqual(result["state_brier"], 0.20)
        self.assertLessEqual(result["state_ece"], 0.12)
        self.assertLessEqual(result["parameter_mean_absolute_error"], 0.08)
        self.assertGreaterEqual(result["parameter_95_interval_coverage"], 0.85)

    def test_nested_model_comparison_matches_analytic_answer(self):
        result = model_comparison()
        self.assertLess(result["absolute_error"], 1e-10)
        self.assertGreater(result["complexity_penalty_log"], 0)

    def test_one_posterior_state_has_no_other_fields(self):
        self.assertEqual(
            {field.name for field in fields(ProtocolState)},
            {"posterior_store", "parameter_posterior_store", "evidence_store", "metadata"},
        )
        state = ProtocolState(
            posterior_store={"x": np.array([0.4, 0.6])},
            parameter_posterior_store={"theta": np.array([1.0, 2.0])},
            evidence_store={"H": 0.25},
            metadata=MappingProxyType({"seed": 1}),
        )
        audit_one_posterior(state)
        with self.assertRaises(AttributeError):
            state.node_values = {"x": 0.6}

    def test_audit_rejects_nonposterior_values(self):
        state = ProtocolState(posterior_store={"x": np.array([0.2, 0.2])})
        with self.assertRaises(AssertionError):
            audit_one_posterior(state)

    def test_component_rng_is_deterministic_and_seed_guarded(self):
        left = component_rng(77, "world").random(10)
        right = component_rng(77, "world").random(10)
        other = component_rng(77, "observation").random(10)
        np.testing.assert_array_equal(left, right)
        self.assertFalse(np.array_equal(left, other))
        with self.assertRaises(ValueError):
            component_rng(800000, "escrow")

    def test_every_declared_semantic_posterior_is_oracle_checkable(self):
        engine = ExactEngine()
        for model, observations, query in semantic_models().values():
            actual, z_actual = engine.infer(model, query, observations)
            expected, z_expected = brute_force(model, query, observations)
            np.testing.assert_allclose(actual, expected, atol=1e-10, rtol=0)
            self.assertAlmostEqual(z_actual, z_expected, places=12)

    def test_invalid_factor_and_model_declarations_fail(self):
        with self.assertRaises(ValueError):
            Factor(("x",), np.array([-1.0, 2.0]))
        model = FiniteModel()
        model.add_variable(Variable("x", 2))
        with self.assertRaises(ValueError):
            model.add_factor(Factor(("missing",), np.array([0.5, 0.5])))


if __name__ == "__main__":
    unittest.main()

