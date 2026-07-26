import unittest

import numpy as np

from ref.inference import ExactEngine
from ref.oracle import brute_force
from ref.v20 import run_v20
from ref.v21 import (
    batch_evaluation,
    broadcast_assay,
    cross_latent_composition,
    open_assays,
    precision_model,
    precision_recovery,
    run_v21,
    semantic_precision_proof,
)


class PrecisionTests(unittest.TestCase):
    def test_precision_changes_likelihood_entering_inference(self):
        result = semantic_precision_proof()
        self.assertGreaterEqual(result["sharpening_effect"], 0.15)
        self.assertLess(result["analytic_numeric_max_error"], 1e-12)
        self.assertTrue(result["gaussian_variance_monotone"])

    def test_broadcast_changes_depth_not_local_calculation(self):
        result = broadcast_assay()
        self.assertGreaterEqual(result["depth_effect"], 0.20)
        self.assertLess(result["local_max_difference"], 1e-10)
        self.assertLess(result["engine_oracle_error"], 1e-10)

    def test_global_inference_changes_evidence_for_another_latent(self):
        result = cross_latent_composition()
        self.assertGreaterEqual(result["delivered_log_odds_effect"], 0.20)

    def test_precision_recovery(self):
        result = precision_recovery()
        self.assertGreaterEqual(result["accuracy"], 0.70)
        self.assertLessEqual(result["parameter_mean_absolute_error"], 0.08)
        self.assertGreaterEqual(result["parameter_95_interval_coverage"], 0.85)

    def test_open_assays_have_unlabeled_four_regimes_and_comparator(self):
        assays = open_assays()
        self.assertEqual(set(assays["four_unlabeled_regimes"]), {"r0", "r1", "r2", "r3"})
        self.assertIn("independent_local_comparator_target", assays)
        for values in assays["four_unlabeled_regimes"].values():
            self.assertIn("dominance", values)
            self.assertIn("depth", values)

    def test_full_seed_block_is_paired_and_oracle_checked(self):
        batch = batch_evaluation()
        self.assertEqual(batch["seed_count"], 64)
        self.assertEqual(batch["paired_draw_mismatches"], 0)
        self.assertLess(batch["maximum_oracle_error"], 1e-10)

    def test_extended_model_posterior_matches_oracle(self):
        model = precision_model(True)
        actual, z_actual = ExactEngine().infer(model, ("Phi", "Y"), {"Q0": 2, "OY": 1})
        expected, z_expected = brute_force(model, ("Phi", "Y"), {"Q0": 2, "OY": 1})
        np.testing.assert_allclose(actual, expected, atol=1e-10, rtol=0)
        self.assertAlmostEqual(z_actual, z_expected, places=12)

    def test_cumulative_v20_regression(self):
        self.assertTrue(run_v20()["passed"])
        self.assertTrue(run_v21()["passed"])


if __name__ == "__main__":
    unittest.main()
