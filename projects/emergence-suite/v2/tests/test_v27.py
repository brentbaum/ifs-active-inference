import unittest

import numpy as np

from ref import v27, v27_oracle
from ref import v221


class V27Tests(unittest.TestCase):
    def test_joint_policy_cap_and_normalization(self):
        for count, expected in ((1, 3), (2, 9), (3, 27)):
            world = v27.generate_control_world(
                1_519_900 + count, scenario="polarization", protector_count=count
            )
            score = v27.score_world(world)
            self.assertEqual(len(score.joint_policies), expected)
            self.assertLessEqual(abs(float(score.q_joint_policy.sum()) - 1), 1e-10)

    def test_masked_registration_is_neutral(self):
        q = v27.registration_posterior((None, None, None))
        self.assertTrue(np.array_equal(q, v27.REGISTRATION_PRIOR))

    def test_outcome_normalizes(self):
        for count in (1, 2, 3):
            for policy in v27.joint_policies(count):
                for topology in range(3):
                    p = v27.shared_outcome_probability(policy, topology, 0.55, 0.5)
                    self.assertLessEqual(abs(p + (1.0 - p) - 1.0), 1e-10)
                    self.assertGreater(p, 0.0)
                    self.assertLess(p, 1.0)

    def test_oracle_copies_inputs(self):
        world = v27.generate_recovery_world(1_519_950, protector_count=2, length=8)
        priors = (
            v27.TOPOLOGY_PRIOR.copy(),
            v27.MANDATE_PRIOR.copy(),
            v27.OUTCOME_LEVEL_PRIOR.copy(),
        )
        before = tuple(item.tobytes() for item in priors)
        oracle = v27_oracle.enumerate_structure(
            [(item.joint_policy, item.outcome) for item in world.observations],
            2,
            *priors,
            lambda policy, topology, mandate, outcome: v27.shared_outcome_probability(
                policy,
                topology,
                v27.MANDATE_SUPPORT[mandate],
                v27.OUTCOME_LEVEL_SUPPORT[outcome],
            ),
        )
        production, _ = v27.structure_posterior(world.observations, 2)
        self.assertLessEqual(float(np.max(np.abs(oracle - production))), 1e-10)
        self.assertEqual(before, tuple(item.tobytes() for item in priors))

    def test_unused_slots_bitwise_idle(self):
        one = v27.generate_recovery_world(1_519_960, protector_count=1)
        two = v27.generate_recovery_world(1_519_960, protector_count=2)
        self.assertEqual(one.idle_slots[0], v27.IDLE_SLOT_BYTES)
        self.assertEqual(one.idle_slots[1], v27.IDLE_SLOT_BYTES)
        self.assertEqual(two.idle_slots[0], v27.IDLE_SLOT_BYTES)

    def test_released_block_threading(self):
        world = v27.generate_recovery_world(
            1_520_001,
            protector_count=3,
            released_block=(1_520_000, 1_524_999),
        )
        self.assertEqual(world.seed, 1_520_001)
        with self.assertRaises(ValueError):
            v27.generate_recovery_world(
                2_060_000,
                protector_count=3,
                released_block=(1_520_000, 1_524_999),
            )

    def test_cue_root_lesion_is_selective(self):
        association = v221.learn_association(12, 0)
        self.assertGreater(v27.cue_root_transfer(association), 0.0)
        self.assertEqual(
            v27.cue_root_transfer(
                association, lesions=("cue_root_association",)
            ),
            0.0,
        )


if __name__ == "__main__":
    unittest.main()
