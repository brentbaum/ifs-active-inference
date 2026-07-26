import ast
import inspect
import unittest

from ref.v20 import run_v20
from ref.v21 import run_v21
from ref.v221 import (
    association_recovery,
    learn_association,
    model_averaged_association,
    repair_floor_assay,
    run_v221,
    semantic_proof,
)


class AssociationRepairTests(unittest.TestCase):
    def test_exact_zero_and_slab_finite_comparison(self):
        result = semantic_proof()
        self.assertLess(result["maximum_error"], 1e-10)
        self.assertGreaterEqual(
            result["posteriors_zero_associated"]["zero"][0], 0.90
        )
        self.assertGreaterEqual(
            result["posteriors_zero_associated"]["associated"][1], 0.90
        )

    def test_model_average_is_not_a_threshold_or_clamp(self):
        state = learn_association(95, 85)
        value = model_averaged_association(state)
        zero_weight, slab_weight = state.posterior_store["Z_association"]
        slab = state.parameter_posterior_store["theta_slab"]
        expected = zero_weight * 0.5 + slab_weight * slab[1] / slab.sum()
        self.assertAlmostEqual(value, expected, places=14)
        tree = ast.parse(inspect.getsource(model_averaged_association))
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        self.assertNotIn("threshold", names)
        self.assertNotIn("transfer", names)

    def test_existence_and_slab_recovery(self):
        result = association_recovery()
        self.assertGreaterEqual(result["existence_accuracy"], 0.90)
        self.assertLessEqual(
            result["slab_parameter_mean_absolute_error"], 0.10
        )
        self.assertGreaterEqual(
            result["slab_parameter_95_interval_coverage"], 0.85
        )

    def test_repaired_open_floor_and_associated_transfer(self):
        result = repair_floor_assay()
        self.assertEqual(result["world_count"], 256)
        self.assertGreaterEqual(result["zero_floor_clean_rate"], 0.95)
        self.assertLess(result["zero_transfer_mean"], 0.01)
        self.assertGreaterEqual(result["associated_transfer_mean"], 0.15)

    def test_all_cumulative_strains_pass(self):
        self.assertTrue(run_v20()["passed"])
        self.assertTrue(run_v21()["passed"])
        self.assertTrue(run_v221()["passed"])


if __name__ == "__main__":
    unittest.main()

