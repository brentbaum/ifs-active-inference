import inspect
import math
import unittest

import numpy as np

from ref.v24 import (
    FAMILIES,
    Observation,
    compare_families,
    generate_world,
    independent_history_sum,
    score_family,
    semantic_proofs,
)


class ContextIndexedRedescriptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.semantic = semantic_proofs()

    def test_all_sixteen_semantic_proofs(self):
        self.assertEqual(self.semantic["proof_count"], 16)
        self.assertTrue(self.semantic["passed"])
        self.assertTrue(
            all(
                proof["passed"]
                for proof in self.semantic["proofs"].values()
            )
        )

    def test_missing_history_is_exactly_structure_neutral(self):
        observations = [
            Observation(0, None, None, None),
            Observation(1, None, None, None),
            Observation(2, None, None, None),
        ]
        result = compare_families(observations)
        self.assertLess(np.ptp(result["log_evidence"]), 1e-12)
        np.testing.assert_allclose(
            result["posterior"],
            np.full(len(FAMILIES), 1.0 / len(FAMILIES)),
            atol=1e-12,
        )

    def test_partition_identity_for_every_family(self):
        observations = [
            Observation(0, 1, "then_marker", 1),
            Observation(1, 0, "now_marker", 0),
        ]
        for family in FAMILIES:
            score = score_family(family, observations)
            self.assertLess(score.decomposition_error, 1e-10)
            self.assertAlmostEqual(
                score.log_evidence,
                score.expected_log_likelihood - score.total_complexity,
                places=10,
            )

    def test_independent_oracle_shares_no_scorer(self):
        source = inspect.getsource(independent_history_sum)
        self.assertNotIn("score_family(", source)
        self.assertNotIn("compare_families(", source)
        observations = [
            Observation(0, 1, "then_marker", 1),
            Observation(1, 0, "now_marker", 0),
        ]
        for family in FAMILIES:
            exact = math.exp(score_family(family, observations).log_evidence)
            independent = independent_history_sum(family, observations)
            self.assertAlmostEqual(exact, independent, places=10)

    def test_every_pairwise_update_is_published_log_bf(self):
        observations = [
            Observation(0, 1, "then_marker", 1),
            Observation(1, 1, "then_marker", 1),
            Observation(2, 0, "now_marker", 0),
        ]
        result = compare_families(observations)
        self.assertLess(result["maximum_update_identity_error"], 1e-10)

    def test_all_families_execute_at_supported_nonprimary_cue_counts(self):
        for cue_count in (2, 4):
            for offset, family in enumerate(FAMILIES):
                world = generate_world(
                    family,
                    799300 + 10 * cue_count + offset,
                    length=16,
                    cue_count=cue_count,
                )
                self.assertEqual(
                    {observation.cue for observation in world["observations"]},
                    set(range(cue_count)),
                )
                result = compare_families(world["observations"])
                self.assertLess(
                    result["maximum_update_identity_error"],
                    1e-10,
                )
                self.assertLess(
                    max(
                        score.decomposition_error
                        for score in result["scores"]
                    ),
                    1e-10,
                )


if __name__ == "__main__":
    unittest.main()
