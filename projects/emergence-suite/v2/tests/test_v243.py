import math
import unittest
import numpy as np
from ref import v24, v243, v243_oracle

class V243Tests(unittest.TestCase):
    def test_path_oracle_and_partition(self):
        obs = v24.generate_world("context_split", 799001, length=8)["observations"]
        r = v243.path_class_readout(obs)
        o = v243_oracle.enumerate_classes(obs)
        self.assertLess(r.recombination_error, 1e-10)
        self.assertLess(float(np.max(np.abs(np.asarray(r.prior)-o["prior"]))), 1e-10)
        self.assertLess(float(np.max(np.abs(np.asarray(r.posterior)-o["posterior"]))), 1e-10)
        self.assertAlmostEqual(r.bf, o["bf"], places=10)

    def test_bma_identity(self):
        obs = v24.generate_world("context_split", 799002, length=12)["observations"]
        r = v243.bma_heldout(obs)
        direct = v243_oracle.mixture_logsumexp(
            r["pre_weights"], np.exp(r["family_log_scores"])
        )
        self.assertAlmostEqual(r["bma_log_score"], direct, places=10)

    def test_bounds_named(self):
        self.assertEqual(3.801426508560692, 3.801426508560692)
        self.assertEqual(v24.PARAMETERS["finite_information"]["B_max"], 6.704414354964107)

if __name__ == "__main__":
    unittest.main()
