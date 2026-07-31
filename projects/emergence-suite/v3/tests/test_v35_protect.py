import math
import unittest
from dataclasses import asdict, replace

from ref import v35, v35_oracle
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
