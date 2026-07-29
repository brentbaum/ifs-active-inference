import unittest

import numpy as np

from ref import v25a_completion as completion
from ref import v25a_completion_oracle as oracle


class V25aCompletionTests(unittest.TestCase):
    def test_tables_normalize_and_preserve_marginals(self):
        for cue in range(4):
            for context in (0, 1):
                expected = completion.channel_marginals(cue, context)
                for root in (0, 1):
                    for kappa in (0.0,) + completion.KAPPA_GRID:
                        table = completion.joint_table(
                            cue, context, root, kappa
                        )
                        self.assertAlmostEqual(float(table.sum()), 1.0, places=13)
                        observed = oracle.direct_marginals(table)
                        self.assertLessEqual(
                            float(np.max(np.abs(observed - expected))), 1e-12
                        )

    def test_zero_slab_is_product(self):
        table = completion.joint_table(2, 1, 0, 0.0)
        product = completion.product_table(
            completion.channel_marginals(2, 1)
        )
        self.assertTrue(np.array_equal(table, product))

    def test_masked_episode_is_neutral(self):
        episode = completion.Episode(0, 0, (None,) * 5)
        result = completion.score([episode], presentation="joint")
        self.assertAlmostEqual(result.joint_log_evidence, 0.0, places=14)
        self.assertAlmostEqual(result.q_structure[0], 0.5, places=14)

    def test_atomic_budget_is_identical(self):
        world = completion.generate_world(
            1000000,
            truth_structure="coupled",
            interaction="strong",
            context_regime="return",
            length=32,
        )
        joint = completion.score(world.episodes, presentation="joint")
        marginal = completion.score(world.episodes, presentation="marginal")
        self.assertEqual(joint.atomic_budget_joint, marginal.atomic_budget_marginal)
        self.assertLessEqual(
            float(np.max(np.abs(marginal.q_structure - [0.5, 0.5]))), 1e-12
        )

    def test_independent_oracle_matches_component_mixture(self):
        world = completion.generate_world(
            1000001,
            truth_structure="coupled",
            interaction="weak",
            context_regime="single",
            length=4,
            missingness=0.0,
        )
        production = completion.score(world.episodes, presentation="joint")
        priors = []
        likelihoods = []
        for root in (0, 1):
            priors.append(0.25)
            likelihoods.append(
                [
                    oracle.observed_mass(
                        completion.joint_table(ep.cue, ep.context, root, 0.0),
                        ep.values,
                    )
                    for ep in world.episodes
                ]
            )
        for kappa in completion.KAPPA_GRID:
            for root in (0, 1):
                priors.append(0.125)
                likelihoods.append(
                    [
                        oracle.observed_mass(
                            completion.joint_table(
                                ep.cue, ep.context, root, kappa
                            ),
                            ep.values,
                        )
                        for ep in world.episodes
                    ]
                )
        posterior, evidence = oracle.enumerate_mixture(priors, likelihoods)
        self.assertAlmostEqual(production.joint_log_evidence, evidence, places=12)
        self.assertAlmostEqual(
            production.q_structure[1], float(posterior[2:].sum()), places=12
        )

    def test_matching_oracle(self):
        trajectory = [0.03, 0.12, 0.19, 0.31]
        production = completion.nearest_reachable_match(0.2, trajectory, 4)
        independent = oracle.nearest_prefix(0.2, trajectory, 4)
        self.assertEqual(production["matched_index"], independent[0])
        self.assertEqual(production["matched_kl"], independent[1])
        self.assertEqual(production["absolute_error"], independent[2])


if __name__ == "__main__":
    unittest.main()
