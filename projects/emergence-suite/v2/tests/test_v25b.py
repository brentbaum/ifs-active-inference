import unittest

import numpy as np

from ref import v25a_completion as v25a
from ref import v25b, v25b_oracle


class V25bTests(unittest.TestCase):
    def test_all_tables_normalize_and_preserve_marginals(self):
        for structure in v25b.STRUCTURES:
            table = v25b.joint_table(1, 1, structure, 0.8)
            self.assertAlmostEqual(float(table.sum()), 1.0, places=13)
            observed = v25a.table_marginals(table)
            expected = v25a.channel_marginals(1, 1)
            self.assertLessEqual(
                float(np.max(np.abs(observed - expected))), 1e-12
            )

    def test_independent_oracle(self):
        fixture = (
            v25a.Episode(0, 0, (1, 0, 1, 0, 1)),
            v25a.Episode(1, 1, (0, 1, 0, 1, 0)),
            v25a.Episode(2, 0, (None, 0, 1, 1, 0)),
        )
        production = v25b.score(fixture, precision=0.8)
        posterior, evidence = v25b_oracle.score(
            fixture,
            v25b.PRIOR,
            0.8,
            float(v25b.PARAMETERS["coupling_strength"]),
        )
        self.assertLessEqual(
            float(np.max(np.abs(production.q_structure - posterior))), 1e-10
        )
        self.assertLessEqual(
            float(
                np.max(
                    np.abs(production.log_evidence_by_structure - evidence)
                )
            ),
            1e-10,
        )

    def test_independent_oracle_leaves_inputs_bitwise_unchanged(self):
        fixture = (
            v25a.Episode(0, 0, (1, 0, 1, 0, 1)),
            v25a.Episode(1, 1, (0, 1, 0, 1, 0)),
        )
        prior = np.asarray(
            [0.04, 0.08, 0.12, 0.16, 0.16, 0.12, 0.08, 0.24],
            dtype=float,
        )
        prior_before = prior.copy()
        fixture_before = tuple(fixture)
        v25b_oracle.score(
            fixture,
            prior,
            0.8,
            float(v25b.PARAMETERS["coupling_strength"]),
        )
        self.assertTrue(np.array_equal(prior, prior_before))
        self.assertEqual(fixture, fixture_before)

    def test_missing_episode_is_candidate_common(self):
        missing = v25a.Episode(0, 0, (None,) * 5)
        result = v25b.score([missing], precision=0.8)
        self.assertLessEqual(
            float(np.max(np.abs(result.q_structure - v25b.PRIOR))), 1e-10
        )

    def test_imaginal_path_uses_episode_likelihood(self):
        episodes, modes = v25b.do_over_episodes(
            1_000_010, count=2, precision=0.8
        )
        self.assertTrue(all(isinstance(item, v25a.Episode) for item in episodes))
        result = v25b.score(
            episodes, precision=0.8, presentations=modes
        )
        self.assertAlmostEqual(float(result.q_structure.sum()), 1.0)


if __name__ == "__main__":
    unittest.main()
