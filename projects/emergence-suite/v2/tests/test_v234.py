import unittest

import numpy as np

from ref import v234, v234_oracle


class V234Tests(unittest.TestCase):
    def test_prior_and_exact_spike(self):
        self.assertLessEqual(abs(float(v234.JOINT_PRIOR.sum()) - 1.0), v234.TOLERANCE)
        spike = float(v234.JOINT_PRIOR[v234.STATE_CAUSAL == 0].sum())
        self.assertLessEqual(
            abs(spike - v234.PARAMETERS["irrelevant_spike_prior"]),
            v234.TOLERANCE,
        )

    def test_masked_relief_slice_is_scientifically_neutral(self):
        episode = v234.Episode(v234.ACTIONS["protect"], 0, None, None, None, 1)
        likelihood, _ = v234.slice_likelihood(episode)
        self.assertLessEqual(
            float(np.max(np.abs(likelihood - 1.0))), v234.TOLERANCE
        )
        result = v234.score([episode])
        self.assertLessEqual(
            float(np.max(np.abs(result.posterior - v234.JOINT_PRIOR))),
            v234.TOLERANCE,
        )
        self.assertGreater(result.policy_probability, 0.5)

    def test_independent_oracle_and_input_copy(self):
        episode = v234.Episode(1, 1, 0, 1, 1, 0)
        likelihood, _ = v234.slice_likelihood(episode)
        expected = v234.JOINT_PRIOR * likelihood
        expected /= expected.sum()
        prior = v234.JOINT_PRIOR.copy()
        before = prior.tobytes()
        observed, _ = v234_oracle.update(
            prior,
            v234.THETA,
            v234.ETA,
            v234.CONFIGS,
            (
                episode.action,
                episode.context,
                episode.outcome,
                episode.near_miss,
                episode.efficacy_observation,
            ),
            (
                v234.PARAMETERS["outcome_reliability"],
                v234.PARAMETERS["danger_diagnostic_reliability"],
                v234.PARAMETERS["efficacy_diagnostic_reliability"],
            ),
        )
        self.assertLessEqual(
            float(np.max(np.abs(expected - observed))), v234.TOLERANCE
        )
        self.assertEqual(before, prior.tobytes())

    def test_generation_threads_released_block(self):
        world = v234.generate_world(1_299_900, identifiable=True, length=4)
        self.assertEqual(len(world.episodes), 4)
        with self.assertRaises(ValueError):
            v234.generate_world(
                2_040_000,
                identifiable=True,
                length=4,
                released_block=(1_300_000, 1_319_999),
            )

    def test_action_is_not_likelihood_observation(self):
        engage = v234.Episode(v234.ACTIONS["engage"], 0, None)
        protect = v234.Episode(v234.ACTIONS["protect"], 0, None)
        left, _ = v234.slice_likelihood(engage)
        right, _ = v234.slice_likelihood(protect)
        self.assertLessEqual(float(np.max(np.abs(left - right))), v234.TOLERANCE)


if __name__ == "__main__":
    unittest.main()
