import unittest

import numpy as np

from ref import v26a, v26a_oracle


class V26aTests(unittest.TestCase):
    def test_all_emissions_and_transitions_normalize(self):
        self.assertLessEqual(
            float(np.max(np.abs(v26a.TRANSITION.sum(axis=1) - 1.0))),
            v26a.TOLERANCE,
        )
        for state in range(4):
            total = 0.0
            for mask in range(16):
                atom = tuple((mask >> axis) & 1 for axis in range(4))
                total += v26a.relational_likelihood(atom, state)
            self.assertLessEqual(abs(total - 1.0), v26a.TOLERANCE)

    def test_independent_oracle_and_input_immutability(self):
        observations = (
            v26a.PartnerObservation((1, 1, 1, 1)),
            v26a.PartnerObservation((1, 0, 1, 0)),
            v26a.PartnerObservation((0, 1, None, 0)),
            v26a.PartnerObservation((1, 1, 1, 1)),
        )
        prior = v26a.PRIOR.copy()
        transition = v26a.TRANSITION.copy()
        emissions = v26a.EMISSIONS.copy()
        before = (prior.tobytes(), transition.tobytes(), emissions.tobytes())
        filtered, smoothed, pairs, evidence = v26a.hmm_inference(observations)
        occupancy, oracle_smoothed, oracle_pairs, oracle_evidence = (
            v26a_oracle.enumerate_partner(
                [item.relational for item in observations],
                prior,
                transition,
                emissions,
            )
        )
        production_occupancy = np.sum(np.asarray(smoothed), axis=0)
        production_occupancy /= production_occupancy.sum()
        self.assertLessEqual(
            float(np.max(np.abs(production_occupancy - occupancy))),
            v26a.TOLERANCE,
        )
        self.assertLessEqual(abs(evidence - oracle_evidence), v26a.TOLERANCE)
        self.assertLessEqual(
            max(
                float(np.max(np.abs(left - right)))
                for left, right in zip(smoothed, oracle_smoothed)
            ),
            v26a.TOLERANCE,
        )
        self.assertLessEqual(
            max(
                float(np.max(np.abs(left - right)))
                for left, right in zip(pairs, oracle_pairs)
            ),
            v26a.TOLERANCE,
        )
        self.assertEqual(
            before, (prior.tobytes(), transition.tobytes(), emissions.tobytes())
        )

    def test_regulation_only_is_zero_root_evidence(self):
        world = v26a.generate_factorial_world(
            1_199_900,
            regulation_present=True,
            root_evidence_present=False,
        )
        result = v26a.score(world.observations)
        self.assertLessEqual(
            float(np.max(np.abs(result.q_root - v26a.ROOT_PRIOR))),
            v26a.TOLERANCE,
        )
        self.assertLessEqual(max(map(abs, result.root_log_bf)), v26a.TOLERANCE)

    def test_broadcast_off_preserves_local_inference(self):
        world = v26a.generate_factorial_world(
            1_199_901,
            regulation_present=True,
            root_evidence_present=True,
        )
        on = v26a.score(world.observations, broadcast=True)
        off = v26a.score(world.observations, broadcast=False)
        self.assertLessEqual(
            float(np.max(np.abs(on.q_partner - off.q_partner))),
            v26a.TOLERANCE,
        )
        self.assertLessEqual(
            max(
                float(np.max(np.abs(left - right)))
                for left, right in zip(
                    on.smoothed_partner, off.smoothed_partner
                )
            ),
            v26a.TOLERANCE,
        )

    def test_released_block_is_threaded(self):
        world = v26a.generate_recovery_world(
            1_200_002,
            released_block=(1_200_000, 1_201_499),
        )
        self.assertEqual(world.seed, 1_200_002)
        with self.assertRaises(ValueError):
            v26a.generate_recovery_world(
                2_030_000,
                released_block=(1_200_000, 1_201_499),
            )

    def test_recovery_generator_is_frozen_scorer_process(self):
        seed = 1_199_910
        world = v26a.generate_recovery_world(seed, length=12)
        rng = v26a._rng(seed, "v26a-recovery-partner-path")
        expected = [int(rng.choice(4, p=v26a.PRIOR))]
        for _ in range(1, 12):
            expected.append(
                int(rng.choice(4, p=v26a.TRANSITION[expected[-1]]))
            )
        self.assertEqual(world.truth_path, tuple(expected))
        for left, right in zip(world.truth_path, world.truth_path[1:]):
            self.assertGreater(v26a.TRANSITION[left, right], 0.0)

    def test_declared_lesions_preserve_unrelated_paths(self):
        world = v26a.generate_factorial_world(
            1_199_920,
            regulation_present=True,
            root_evidence_present=True,
        )
        baseline = v26a.score(world.observations)
        precision = v26a.score(
            world.observations, partner_precision_enabled=False
        )
        no_root = v26a.score(
            world.observations, root_evidence_enabled=False
        )
        self.assertLessEqual(
            float(np.max(np.abs(baseline.q_partner - precision.q_partner))),
            v26a.TOLERANCE,
        )
        self.assertLessEqual(
            float(np.max(np.abs(baseline.q_partner - no_root.q_partner))),
            v26a.TOLERANCE,
        )
        self.assertLessEqual(abs(no_root.root_movement), v26a.TOLERANCE)

    def test_robustness_generation_threads_released_block(self):
        world = v26a.generate_robustness_world(
            1_199_930, scenario="context_return"
        )
        self.assertEqual(len(world.observations), 32)
        with self.assertRaises(ValueError):
            v26a.generate_robustness_world(
                2_030_000,
                scenario="baseline",
                released_block=(1_207_000, 1_219_999),
            )


if __name__ == "__main__":
    unittest.main()
