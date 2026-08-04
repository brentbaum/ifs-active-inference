"""Zero-seed regression proofs for DT-S1-IDGEN apparatus."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import run_decisive_s1 as s1  # noqa: E402
from scripts import s1_associative_comparator as comparator  # noqa: E402


class DecisiveS1ProofTests(unittest.TestCase):
    def test_frozen_scientific_source_identity(self) -> None:
        self.assertEqual(s1._assert_sources(), s1.SOURCE_HASHES)

    def test_threshold_calibration_is_label_invariant(self) -> None:
        left = s1._threshold_distribution()
        right = s1._threshold_distribution()
        self.assertAlmostEqual(left["probability_sum"], 1.0, places=12)
        self.assertEqual(left["selected"], right["selected"])

    def test_exposure_control_is_outcome_first_rational(self) -> None:
        root = s1._expected_log_bf(0.55, 0.45)
        outcome = s1._expected_log_bf(0.84, 0.16)
        self.assertGreater(outcome, root)

    def test_support_preserving_root_lesion(self) -> None:
        proof = s1._lesion_dummy()
        self.assertTrue(proof["passed"])
        self.assertEqual(proof["semantic_class"], "SUPPORT_PRESERVING_CONDITIONING")
        self.assertAlmostEqual(proof["lesioned_untreated_prediction"], 0.5)
        self.assertLessEqual(proof["independent_q_error"], s1.TOL)

    def test_comparator_support_and_normalization(self) -> None:
        proof = comparator.support_and_normalization((1, 0, 1, 1))
        self.assertTrue(proof["full_binary_support"])
        self.assertLessEqual(proof["normalization_error"], s1.TOL)


if __name__ == "__main__":
    unittest.main()
