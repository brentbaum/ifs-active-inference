import unittest

import numpy as np

from ref import v28, v28_oracle


class V28Tests(unittest.TestCase):
    def test_development_starts_from_neutral_priors_and_serializes(self):
        state = v28.generate_developmental_state(
            1_689_900, "chronic_one"
        )
        self.assertEqual(state.protector_count, 1)
        self.assertEqual(len(state.state_sha256), 64)
        self.assertEqual(
            v28_oracle.clone_bytes(state.serialized, 2),
            (state.serialized, state.serialized),
        )

    def test_protocol_has_twelve_generic_do_actions(self):
        document = v28.protocol_document("full")
        self.assertEqual(len(document["actions"]), 12)
        self.assertTrue(all(set(item) == {"do"} for item in document["actions"]))

    def test_same_seed_pairing_is_bitwise(self):
        state = v28.generate_developmental_state(
            1_689_901, "chronic_multiple"
        )
        left = v28.run_trajectory(state, 1_689_902)
        right = v28.run_trajectory(state, 1_689_902)
        self.assertEqual(left, right)

    def test_oracle_copies_inputs(self):
        costs = np.asarray([[0.1, 0.2, 0.3], [0.3, 0.2, 0.1]])
        before = costs.tobytes()
        q = v28_oracle.enumerate_policy(costs, 4.0)
        self.assertEqual(before, costs.tobytes())
        self.assertLessEqual(abs(float(q.sum()) - 1.0), 1e-10)

    def test_no_scientific_state_layer(self):
        self.assertFalse(hasattr(v28.TrajectoryProfile, "state"))
        self.assertFalse(hasattr(v28.DevelopmentalState, "posterior_store"))


if __name__ == "__main__":
    unittest.main()
