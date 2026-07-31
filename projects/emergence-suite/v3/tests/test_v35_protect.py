import math
import unittest
from dataclasses import asdict, replace

from ref import (
    v35,
    v35_calibration,
    v35_calibration_oracle,
    v35_oracle,
    v35_topology,
    v35_topology_oracle,
)
from ref.trace_sink import serializing_trace_context


class V35ProtectTests(unittest.TestCase):
    def setUp(self):
        self.context = serializing_trace_context(self.id())
        self.context.__enter__()

    def tearDown(self):
        self.context.__exit__(None, None, None)

    def config(self):
        return v35.ProtectConfig(
            "all", "remaining", "high", "mixed", 3, "allied",
            "all", "delivered", "delivered", 16,
        )

    def test_joint_policy_space_and_posterior_normalize(self):
        world = v35.generate_world(3_500_000, self.config())
        posterior = v35.score_world(world)
        self.assertEqual(len(v35.JOINT_POLICIES), 27)
        self.assertLessEqual(
            abs(math.fsum(posterior.probabilities) - 1.0), 1e-10
        )
        self.assertLessEqual(
            abs(math.fsum(posterior.joint_policy_posterior) - 1.0),
            1e-10,
        )

    def test_generator_scorer_channels_normalize(self):
        structure = v35.ProtectStructure(3, (1, 1, 1), 1, 1)
        for latent in (0, 1):
            self.assertAlmostEqual(
                v35.mode_signal_probability(0, latent)
                + v35.mode_signal_probability(1, latent),
                1.0,
            )
            self.assertAlmostEqual(
                v35.registration_probability(0, latent)
                + v35.registration_probability(1, latent),
                1.0,
            )
        for modes in ((0, 0, 0), (1, 0, 1), (1, 1, 1)):
            for policy in v35.JOINT_POLICIES:
                for sign in (-1, 1):
                    p = v35.outcome_probability(
                        policy, modes, structure, sign
                    )
                    self.assertAlmostEqual(p + (1.0 - p), 1.0)

    def test_registration_mask_is_candidate_common(self):
        world = v35.generate_world(3_500_001, self.config())
        masked = replace(
            world,
            observations=tuple(
                replace(item, registration=(None, None, None))
                for item in world.observations
            ),
        )
        direct = v35.score_world(masked)
        disabled = v35.score_world(world, registration_enabled=False)
        self.assertLessEqual(
            max(abs(a - b) for a, b in zip(
                direct.probabilities, disabled.probabilities
            )),
            1e-10,
        )

    def test_registration_evidence_is_identical_across_candidates(self):
        observation = v35.ProtectObservation(
            0,
            (None, None, None),
            None,
            (1, 1, 1),
            None,
            None,
            None,
            (None, None, None),
            (1, 0, 1),
            None,
            1.0,
        )
        masked = replace(observation, registration=(None, None, None))
        contributions = []
        for structure in v35.PROGRAMS:
            for modes in __import__("itertools").product((0, 1), repeat=3):
                if any(modes[structure.active_modes:]):
                    continue
                observed = v35._slice_likelihood(
                    observation, modes, structure, 0, 0
                )
                baseline = v35._slice_likelihood(
                    masked, modes, structure, 0, 0
                )
                contributions.append(observed / baseline)
        self.assertEqual(max(contributions) - min(contributions), 0.0)
        self.assertLessEqual(
            abs(contributions[0] - 0.20 * 0.80 * 0.20), 1e-10
        )

    def test_registration_delivered_and_masked_posteriors_are_identical(self):
        world = v35.generate_world(3_500_005, self.config())
        delivered = v35.score_world(world)
        masked_world = replace(
            world,
            observations=tuple(
                replace(item, registration=(None, None, None))
                for item in world.observations
            ),
        )
        masked = v35.score_world(masked_world)
        comparisons = (
            max(abs(a - b) for a, b in zip(
                delivered.probabilities, masked.probabilities
            )),
            max(abs(a - b) for a, b in zip(
                delivered.active_mode_probabilities,
                masked.active_mode_probabilities,
            )),
            max(abs(a - b) for a, b in zip(
                delivered.mode_occupancy, masked.mode_occupancy
            )),
            max(abs(a - b) for a, b in zip(
                delivered.joint_policy_posterior,
                masked.joint_policy_posterior,
            )),
        )
        self.assertLessEqual(max(comparisons), 1e-10)

    def test_dormant_candidate_scores_higher_slot_channels(self):
        structure = v35.ProtectStructure(1, (0, 0, 0), 0, 0)
        observation = v35.ProtectObservation(
            0,
            (None, 1, None),
            None,
            (1, 1, 1),
            0,
            None,
            None,
            (None, None, None),
            (None, 1, None),
            None,
            1.0,
        )
        masked = replace(
            observation,
            mode_signals=(None, None, None),
            registration=(None, None, None),
        )
        modes = (0, 0, 0)
        observed_likelihood = v35._slice_likelihood(
            observation, modes, structure, 0, 0
        )
        masked_likelihood = v35._slice_likelihood(
            masked, modes, structure, 0, 0
        )
        self.assertLess(observed_likelihood, masked_likelihood)
        self.assertLessEqual(
            abs(
                observed_likelihood / masked_likelihood
                - v35.mode_signal_probability(1, 0)
                * v35.registration_probability(1, 0)
            ),
            1e-10,
        )

    def test_marginal_calibration_dummy_identity(self):
        production = v35.marginal_calibration_dummy()
        oracle = v35_oracle.marginal_calibration_dummy()
        for name in ("priors", "likelihoods", "posteriors"):
            production_values = tuple(
                value
                for row in production[name]
                for value in (row if isinstance(row, tuple) else (row,))
            )
            oracle_values = tuple(
                value
                for row in oracle[name]
                for value in (row if isinstance(row, tuple) else (row,))
            )
            self.assertEqual(len(production_values), len(oracle_values))
            self.assertLessEqual(
                max(abs(a - b) for a, b in zip(
                    production_values, oracle_values
                )),
                1e-10,
            )
        self.assertLessEqual(production["exact_ece"], 1e-10)
        self.assertLessEqual(
            production["exact_accuracy_confidence_gap"], 1e-10
        )
        self.assertLessEqual(
            production["sampled_ece"],
            production["declared_sampling_tolerance"],
        )
        self.assertLessEqual(
            production["sampled_coverage_error"],
            production["declared_sampling_tolerance"],
        )

    def test_expanded_marginal_calibration_and_support(self):
        result = v35_calibration.run()
        production = v35_calibration.joint_tables()
        oracle = v35_calibration_oracle.enumerate_joint()
        self.assertTrue(result["passed"])
        self.assertLessEqual(
            result["common_support"]["normalization_error_max"], 1e-10
        )
        self.assertTrue(
            result["candidate_support_stress"][
                "all_candidates_finite_positive"
            ]
        )
        self.assertLessEqual(
            max(abs(a - b) for a, b in zip(
                production["likelihoods"].flat,
                (
                    value
                    for row in oracle["likelihoods"]
                    for value in row
                ),
            )),
            1e-10,
        )
        self.assertLessEqual(
            max(abs(a - b) for a, b in zip(
                production["posterior_by_observation"].flat,
                (
                    value
                    for row in oracle["posterior_by_observation"]
                    for value in row
                ),
            )),
            1e-10,
        )

    def test_interventional_topology_fixture(self):
        production = v35_topology.run()
        oracle = v35_topology_oracle.run()
        self.assertTrue(production["passed"])
        for truth in ("independent", "opposed", "allied"):
            for comparator in ("independent", "opposed", "allied"):
                self.assertLessEqual(
                    abs(
                        production["expected_log_bf"][truth][comparator]
                        - oracle["expected_log_bf"][truth][comparator]
                    ),
                    1e-10,
                )
            for source, target in ((0, 1), (1, 0)):
                self.assertLessEqual(
                    abs(
                        production["fingerprints"][truth][source][target]
                        - oracle["fingerprints"][truth][source][target]
                    ),
                    1e-10,
                )

    def test_mixed_schedule_balances_two_mode_joint_policies(self):
        keys = []
        policies = {
            v35._policy_for(
                3_520_003,
                time,
                "mixed",
                2,
                (3_520_000, 3_520_999),
                keys,
            )[:2]
            for time in range(9)
        }
        self.assertEqual(
            policies,
            set(__import__("itertools").product(range(3), repeat=2)),
        )

    def test_independent_oracle_copies_and_matches(self):
        world = v35.generate_world(3_500_002, replace(self.config(), length=8))
        observations = [asdict(item) for item in world.observations]
        snapshot = repr(observations)
        production = v35.score_world(world)
        keys, probabilities, evidence = v35_oracle.posterior(observations)
        production_map = {}
        for probability, (structure, sign), reliable in zip(
            production.probabilities,
            production.components,
            [
                r
                for structure in v35.PROGRAMS
                for sign in ((-1, 1) if structure.cross_mode_outcome else (0,))
                for r in (0, 1)
            ],
        ):
            key = (
                structure.active_modes,
                structure.mode_root_edges,
                structure.joint_policy_outcome,
                structure.cross_mode_outcome,
                sign,
                reliable,
            )
            production_map[key] = probability
        self.assertLessEqual(
            max(abs(p - production_map[k]) for k, p in zip(keys, probabilities)),
            1e-10,
        )
        self.assertLessEqual(
            abs(math.exp(production.log_evidence) - evidence), 1e-10
        )
        self.assertEqual(snapshot, repr(observations))

    def test_trace_guard_and_label_rejection(self):
        world = v35.generate_world(3_500_003, self.config())
        with self.assertRaises(ValueError):
            v35.score_world(replace(world, analysis_labels=("protector",)))
        self.context.__exit__(None, None, None)
        try:
            with self.assertRaisesRegex(RuntimeError, "trace context"):
                v35.generate_world(3_500_004, self.config())
        finally:
            self.context = serializing_trace_context(self.id() + ":restore")
            self.context.__enter__()


if __name__ == "__main__":
    unittest.main()
