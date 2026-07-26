import ast
import inspect
import unittest

import numpy as np

import ref.v22 as v22
from ref.inference import ExactEngine
from ref.oracle import brute_force
from ref.v20 import run_v20
from ref.v21 import run_v21


class RootTransferTests(unittest.TestCase):
    def test_structure_recovery(self):
        result = v22.structure_recovery()
        self.assertGreaterEqual(result["accuracy"], 0.80)
        self.assertGreaterEqual(result["mean_true_structure_probability"], 0.70)

    def test_association_parameter_recovery(self):
        result = v22.association_recovery()
        self.assertLessEqual(result["mean_absolute_error"], 0.10)
        self.assertGreaterEqual(result["coverage_95"], 0.85)

    def test_three_way_precision_seam_and_mediation(self):
        result = v22.seam_assay()
        for name in ("broad", "broadcast_off", "narrowed"):
            self.assertGreaterEqual(result[name]["cue_uptake"], 0.20)
        self.assertGreaterEqual(
            result["broad"]["root_uptake"] - result["broadcast_off"]["root_uptake"], 0.08
        )
        self.assertGreaterEqual(
            result["broadcast_off"]["root_uptake"] - result["narrowed"]["root_uptake"], 0.03
        )
        self.assertGreaterEqual(
            result["broad"]["transfer"] - result["narrowed"]["transfer"], 0.08
        )
        self.assertAlmostEqual(
            result["mediation"]["transfer_with_g_fixed_and_cue_root_cut"], 0.0, places=12
        )

    def test_broadcast_off_first_face(self):
        result = v22.seam_assay()
        local = result["broadcast_off"]
        broad = result["broad"]
        self.assertGreaterEqual(local["local_fluency"], 0.80)
        self.assertLess(local["depth"], broad["depth"])
        self.assertLess(local["root_uptake"], broad["root_uptake"])
        self.assertLess(local["transfer"], broad["transfer"])

    def test_transfer_follows_association_not_similarity(self):
        result = v22.transfer_2x2()
        self.assertGreater(result["association_main_effect"], 0.10)
        self.assertLess(abs(result["similarity_main_effect"]), 0.03)

    def test_association_lesion_removes_transfer_not_local_uptake(self):
        result = v22.lesion_assays()
        self.assertLess(result["cut_transfer"], 0.01)
        self.assertGreaterEqual(result["cut_treated_cue_uptake"], 0.20)

    def test_root_model_matches_independent_oracle(self):
        model = v22.seam_model(True)
        observations = {"Q0": 2, "O0": 1}
        actual, z_actual = ExactEngine().infer(model, ("Phi", "G", "M1"), observations)
        expected, z_expected = brute_force(model, ("Phi", "G", "M1"), observations)
        np.testing.assert_allclose(actual, expected, atol=1e-10, rtol=0)
        self.assertAlmostEqual(z_actual, z_expected, places=12)

    def test_no_transfer_parameter_in_model_factory(self):
        tree = ast.parse(inspect.getsource(v22.seam_model))
        argument_names = [arg.arg for arg in tree.body[0].args.args]
        self.assertNotIn("transfer", argument_names)
        self.assertNotIn("transfer_coefficient", argument_names)

    def test_full_seed_block_and_cumulative_regression(self):
        batch = v22.batch_transfer()
        self.assertEqual(batch["seed_count"], 64)
        self.assertLess(batch["maximum_oracle_error"], 1e-10)
        self.assertTrue(run_v20()["passed"])
        self.assertTrue(run_v21()["passed"])
        self.assertTrue(v22.run_v22()["passed"])


if __name__ == "__main__":
    unittest.main()

