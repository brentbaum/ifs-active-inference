import unittest

import numpy as np

from ref import v26b, v26b_oracle


class V26bTests(unittest.TestCase):
    def test_oracle_copies_inputs_and_matches(self):
        observations = (
            v26b.TrustObservation(True, 1, 1, 0, 1, 0.9),
            v26b.TrustObservation(True, 1, 1, 1, 1, 0.9),
        )
        prior = v26b.TRUST_PRIOR.copy()
        outcome_prior = v26b.OUTCOME_PRIOR.copy()
        support = v26b.OUTCOME_SUPPORT.copy()
        before = (prior.tobytes(), outcome_prior.tobytes(), support.tobytes())
        production, q_outcome, _ = v26b.trust_posteriors(observations)
        oracle, oracle_outcome = v26b_oracle.enumerate_forecasts(
            [
                (
                    item.refusal,
                    item.partner_response,
                    item.outcome,
                    item.coprotection,
                    item.policy_outcome,
                    item.response_reliability,
                )
                for item in observations
            ],
            prior,
            outcome_prior,
            support,
            0.9,
        )
        self.assertLessEqual(
            max(
                float(np.max(np.abs(left - right)))
                for left, right in zip(production, oracle)
            ),
            v26b.TOLERANCE,
        )
        self.assertLessEqual(
            float(np.max(np.abs(q_outcome - oracle_outcome))),
            v26b.TOLERANCE,
        )
        self.assertEqual(
            before,
            (prior.tobytes(), outcome_prior.tobytes(), support.tobytes()),
        )

    def test_refusal_without_response_is_neutral(self):
        observations = (v26b.TrustObservation(True, None),) * 4
        q, _, _ = v26b.trust_posteriors(observations)
        self.assertLessEqual(
            float(np.max(np.abs(q[2] - v26b.TRUST_PRIOR))),
            v26b.TOLERANCE,
        )

    def test_policy_normalizes_and_contact_is_consequence(self):
        result = v26b.policy_posterior(
            (0.8, 0.8, 0.8), 0.8, 0.7, 0.8, 0.9, 1.0
        )
        self.assertLessEqual(abs(float(result.q_policy.sum()) - 1.0), v26b.TOLERANCE)
        self.assertLessEqual(
            abs(
                result.contact_probability
                - float(result.q_policy @ v26b.CONTACT_BY_POLICY)
            ),
            v26b.TOLERANCE,
        )

    def test_released_block_threading(self):
        world = v26b.generate_recovery_world(
            1_400_001, released_block=(1_400_000, 1_402_999)
        )
        self.assertEqual(world.seed, 1_400_001)
        with self.assertRaises(ValueError):
            v26b.generate_recovery_world(
                2_050_000,
                released_block=(1_400_000, 1_402_999),
            )

    def test_no_forbidden_scientific_fields(self):
        world = v26b.generate_control_world(
            1_399_990, scenario="remaining"
        )
        result = v26b.score(
            world.trust_observations,
            world.partner_world.observations,
            world.attribution_world.episodes,
            stakes=world.stakes,
        )
        keys = (
            set(result.state.posterior_store)
            | set(result.state.parameter_posterior_store)
            | set(result.state.evidence_store)
        )
        self.assertTrue(
            {"permission", "access", "gate", "protector_role"}.isdisjoint(keys)
        )


if __name__ == "__main__":
    unittest.main()
