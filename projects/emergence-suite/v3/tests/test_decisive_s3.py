"""Zero-seed regression proofs for DT-S3-PERMISSION."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import run_decisive_s3 as s3  # noqa: E402


class DecisiveS3Tests(unittest.TestCase):
    def test_permission_is_frozen_policy_sum(self) -> None:
        expected = s3.s2.access_probability(s3.s2.internal_policy_posterior(s3.BASE_INPUTS))
        self.assertAlmostEqual(s3.permission(s3.BASE_INPUTS), expected, places=12)

    def test_full_clamp_identity(self) -> None:
        self.assertLessEqual(abs(s3._s3a_dummy()["full_clamp_movement"]), s3.TOL)

    def test_matched_packets(self) -> None:
        packets = s3.packet_log_bfs()
        self.assertLessEqual(abs(packets["weak_accrual"] + packets["equal_total_bf_violation"]), s3.TOL)

    def test_estimand_conformance(self) -> None:
        proof = s3.estimand_conformance()
        self.assertEqual(proof["verdict"], "PASS")
        self.assertTrue(all(proof["checks"].values()))

    def test_refusal_eig_is_zero_for_uninformative_channel(self) -> None:
        self.assertAlmostEqual(s3.refusal_information_gain(0.5, 0.5), 0.0, places=12)


if __name__ == "__main__":
    unittest.main()
