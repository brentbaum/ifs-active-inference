import math
import unittest

import numpy as np

from ref import v24, v25a, v25a_oracle


class EvidencePresentationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = [
            v24.Observation(0, 1, "then_marker", 1),
            v24.Observation(1, 1, "then_marker", None),
            v24.Observation(2, 0, "now_marker", 0),
            v24.Observation(0, 0, "now_marker", 0),
        ]

    def test_factorized_families_are_exact_zero(self):
        for family in (
            "global_downweight",
            "cue_local_relearning",
            "continuous_drift",
        ):
            score = v25a.score_presentations(family, self.fixture)
            self.assertLessEqual(max(map(abs, score.delta_i_per_slice)), 1e-10)
            self.assertLessEqual(score.increment_identity_error, 1e-10)

    def test_cs_delta_matches_independent_enumeration(self):
        score = v25a.score_presentations("context_split", self.fixture)
        oracle = v25a_oracle.enumerated_cs_delta_i(self.fixture)
        self.assertAlmostEqual(score.delta_i, oracle, places=10)
        self.assertLessEqual(score.increment_identity_error, 1e-10)

    def test_missing_slice_is_neutral_under_both_presentations(self):
        fixture = [v24.Observation(0, None, None, None)]
        score = v25a.score_presentations("context_split", fixture)
        self.assertEqual(score.joint.log_evidence, 0.0)
        self.assertEqual(score.marginal_log_evidence, 0.0)
        self.assertEqual(score.delta_i, 0.0)

    def test_derived_candidate_one_posterior_audit(self):
        result = v25a.compare_marginal_candidates(self.fixture)
        self.assertTrue(result["one_posterior_audit"])
        self.assertAlmostEqual(float(np.sum(result["posterior"])), 1.0)

    def test_matching_scan_matches_independent_oracle(self):
        roots = [None, 1, 1, 0, 1, None, 1]
        observations = [
            v24.Observation(index % 3, None, None, value)
            for index, value in enumerate(roots)
        ]
        target = 0.25
        production = v25a.scan_root_kl(observations, target, 0.01, len(roots))
        oracle = v25a_oracle.matching_scan(roots, target, 0.01, len(roots))
        self.assertEqual(production[0], oracle[0])
        self.assertAlmostEqual(production[1], oracle[1], places=14)
        censored = v25a.scan_root_kl(observations, 1.0, 0.0, len(roots))
        self.assertEqual(censored, (None, None))

    def test_information_dose_is_monotone(self):
        values = [
            v25a.enumerable_joint_information(value)["expected_delta_i"]
            for value in np.linspace(0.0, 1.0, 5)
        ]
        self.assertAlmostEqual(values[0], 0.0, places=14)
        self.assertTrue(all(right >= left for left, right in zip(values, values[1:])))
        self.assertGreater(values[-1], values[0])

    def test_marginal_bound_is_not_distinct(self):
        result = v25a.marginal_finite_information_bound()
        self.assertFalse(result["distinct"])
        self.assertAlmostEqual(
            result["B_max_v25a_marginal_accounting"],
            6.704414354964107,
            places=14,
        )


if __name__ == "__main__":
    unittest.main()

