import math
import unittest

import numpy as np

from ref import v24, v25a, v25a_oracle


class EvidencePresentationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = [
            v24.Observation(0, 1, "then_marker", 1),
            v24.Observation(1, 1, "then_marker", None),
            v24.Observation(2, 0, "now_marker", 0),
            v24.Observation(0, 0, "now_marker", 0),
        ]

    def test_factorized_families_are_exact_zero(self):
        for family in (
            "global_downweight",
            "cue_local_relearning",
            "continuous_drift",
        ):
            score = v25a.score_presentations(family, self.fixture)
            self.assertLessEqual(max(map(abs, score.delta_i_per_slice)), 1e-10)
            self.assertLessEqual(score.increment_identity_error, 1e-10)

    def test_cs_delta_matches_independent_enumeration(self):
        score = v25a.score_presentations("context_split", self.fixture)
        oracle = v25a_oracle.enumerated_cs_delta_i(self.fixture)
        self.assertAlmostEqual(score.delta_i, oracle, places=10)
        self.assertLessEqual(score.increment_identity_error, 1e-10)

    def test_missing_slice_is_neutral_under_both_presentations(self):
        fixture = [v24.Observation(0, None, None, None)]
        score = v25a.score_presentations("context_split", fixture)
        self.assertEqual(score.joint.log_evidence, 0.0)
        self.assertEqual(score.marginal_log_evidence, 0.0)
        self.assertEqual(score.delta_i, 0.0)

    def test_derived_candidate_one_posterior_audit(self):
        result = v25a.compare_marginal_candidates(self.fixture)
        self.assertTrue(result["one_posterior_audit"])
        self.assertAlmostEqual(float(np.sum(result["posterior"])), 1.0)

    def test_matching_scan_matches_independent_oracle(self):
        roots = [None, 1, 1, 0, 1, None, 1]
        observations = [
            v24.Observation(index % 3, None, None, value)
            for index, value in enumerate(roots)
        ]
        target = 0.25
        production = v25a.scan_root_kl(observations, target, 0.01, len(roots))
        oracle = v25a_oracle.matching_scan(roots, target, 0.01, len(roots))
        self.assertEqual(production[0], oracle[0])
        self.assertAlmostEqual(production[1], oracle[1], places=14)
        censored = v25a.scan_root_kl(observations, 1.0, 0.0, len(roots))
        self.assertEqual(censored, (None, None))

    def test_information_dose_is_monotone(self):
        values = [
            v25a.enumerable_joint_information(value)["expected_delta_i"]
            for value in np.linspace(0.0, 1.0, 5)
        ]
        self.assertAlmostEqual(values[0], 0.0, places=14)
        self.assertTrue(all(right >= left for left, right in zip(values, values[1:])))
        self.assertGreater(values[-1], values[0])

    def test_dose_operator_preserves_channel_multisets(self):
        world = v24.generate_world("context_split", 755000, length=32)
        original = world["observations"]
        for strength in (0.0, 0.4, 1.0):
            transformed = v25a.association_dose_history(
                original, 755000, strength
            )
            self.assertEqual(
                sorted(item.outcome for item in original if item.outcome is not None),
                sorted(item.outcome for item in transformed if item.outcome is not None),
            )
            self.assertEqual(
                sorted(item.marker for item in original if item.marker is not None),
                sorted(item.marker for item in transformed if item.marker is not None),
            )
            self.assertEqual(
                [item.root for item in original],
                [item.root for item in transformed],
            )
        self.assertEqual(
            v25a.association_dose_history(original, 755000, 1.0),
            original,
        )

    def test_formed_bridge_format_decomposes(self):
        record = v24._bank_states()[0]
        result = v25a.formed_bridge_format_readout(755000, record)
        self.assertFalse(result["matching_censored"])
        self.assertLessEqual(result["matching_absolute_kl_error"], 0.01)
        self.assertLessEqual(result["decomposition_error"], 1e-10)
        self.assertEqual(result["G_fixed_difference"], 0.0)
        self.assertEqual(result["zero_association_difference"], 0.0)

    def test_bridge_trajectory_uses_contract_endpoint_reliability(self):
        record = v24._bank_states()[0]
        state = record["serialized_state"]
        joint = v24._composition_world(755000, bank_state=state)
        result = v25a.formed_bridge_format_readout(755000, record)
        reliability = float(joint["association_reliability"])
        initial = np.asarray(joint["initial_root"], dtype=float)
        posterior = initial.copy()
        for observation in joint["world"]["observations"]:
            if observation.root is None:
                continue
            likelihood = np.asarray(
                [
                    reliability
                    if root_state == observation.root
                    else 1.0 - reliability
                    for root_state in range(2)
                ],
                dtype=float,
            )
            posterior = posterior * likelihood
            posterior = posterior / posterior.sum()
        direction = float(joint["new_direction"])
        initial_prediction = v24._cue_root_prediction(
            initial, float(joint["association"])
        )
        endpoint = direction * (
            v24._cue_root_prediction(
                posterior, float(joint["association"])
            )
            - initial_prediction
        )
        self.assertAlmostEqual(
            endpoint, result["joint_root_movement"], places=14
        )
        self.assertAlmostEqual(
            sum(result["per_slice_difference_increments"]),
            result["joint_minus_marginal"],
            places=14,
        )

    def test_marginal_bound_is_not_distinct(self):
        result = v25a.marginal_finite_information_bound()
        self.assertFalse(result["distinct"])
        self.assertAlmostEqual(
            result["B_max_v25a_marginal_accounting"],
            6.704414354964107,
            places=14,
        )


if __name__ == "__main__":
    unittest.main()
