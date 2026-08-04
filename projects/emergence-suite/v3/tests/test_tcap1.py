"""Zero-seed T-CAP1 semantic regression tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ref import tcap1  # noqa: E402
from scripts import run_tcap1  # noqa: E402


class TCap1Tests(unittest.TestCase):
    def test_semantic_proofs(self) -> None:
        proof = run_tcap1.semantic_proofs()
        self.assertTrue(all(proof["checks"].values()))

    def test_allocation_is_one_cycle_delayed(self) -> None:
        q = 0.3
        before = tcap1.allocation_probability(q, .5, 4.0, 0, .6)
        self.assertEqual(before, tcap1.allocation_probability(q, .5, 4.0, 0, .6))
        self.assertNotEqual(before, tcap1.allocation_probability(.8, .5, 4.0, 0, .6))

    def test_allocation_observation_normalizes(self) -> None:
        for allocation in (0, 1):
            self.assertAlmostEqual(sum(tcap1.allocation_observation_probability(value, allocation, .8) for value in (0, 1)), 1.0, places=12)

    def test_channel_atoms_normalize_on_common_support(self) -> None:
        for channel in range(5):
            for bundle in (0, 1):
                for allocation in (0, 1):
                    total = sum(tcap1.observation_atom_probability(channel, observed, bundle, allocation, .4) for observed in (None, 0, 1))
                    self.assertAlmostEqual(total, 1.0, places=12)

    def test_round27_estimand_conformance(self) -> None:
        proof = run_tcap1.estimand_conformance()
        self.assertTrue(all(proof["checks"].values()))

    def test_full_information_replay_likelihood_identity(self) -> None:
        observations = (1, 0, 1, 0, 1)
        for bundle in (0, 1):
            transparent = tcap1.transparent_log_likelihood(observations, bundle, .3, full_information=True)
            represented = tcap1.represented_log_likelihood(observations, 1, bundle, .3, .7, .8, full_information=True)
            self.assertAlmostEqual(transparent, represented, places=12)


if __name__ == "__main__":
    unittest.main()
