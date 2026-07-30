import math
import unittest
from dataclasses import asdict, replace

from ref import v34, v34_oracle
from ref.trace_sink import serializing_trace_context


class V34RelateTests(unittest.TestCase):
    def setUp(self):
        self.context = serializing_trace_context(self.id())
        self.context.__enter__()

    def tearDown(self):
        self.context.__exit__(None, None, None)

    def test_regulation_without_root_evidence_is_exactly_root_neutral(self):
        world = v34.generate_world(
            3_400_000,
            v34.RelateConfig("reliable", True, False),
        )
        posterior = v34.score_world(world)
        self.assertEqual(posterior.q_root, (0.5, 0.5))
        self.assertEqual(posterior.root_log_bf, 0.0)
        self.assertEqual(posterior.root_movement, 0.0)

    def test_independent_oracle_copies_and_matches(self):
        world = v34.generate_world(
            3_400_001,
            v34.RelateConfig("reliable", True, True),
        )
        observations = [asdict(item) for item in world.observations]
        snapshot = tuple(
            tuple(sorted(item.items())) for item in observations
        )
        production = v34.score_world(world)
        programs, probabilities, q_root, evidence = v34_oracle.posterior(
            observations
        )
        production_map = {
            tuple(v34.structure_values(program).values()): probability
            for program, probability in zip(
                production.programs,
                production.structure_probabilities,
            )
        }
        self.assertLessEqual(
            max(
                abs(probability - production_map[program])
                for program, probability in zip(programs, probabilities)
            ),
            1e-10,
        )
        self.assertLessEqual(
            max(abs(a - b) for a, b in zip(q_root, production.q_root)),
            1e-10,
        )
        self.assertLessEqual(abs(evidence - production.log_evidence), 1e-10)
        self.assertEqual(
            snapshot,
            tuple(tuple(sorted(item.items())) for item in observations),
        )

    def test_restricted_prior_identity(self):
        world = v34.generate_world(
            3_400_002,
            v34.RelateConfig("unstable", True, True),
        )
        full = v34.score_world(world)
        restricted = v34.score_world(
            world, restrictions={"L_TRANSITION": (0,)}
        )
        retained = {
            program: probability
            for program, probability in zip(
                full.programs, full.structure_probabilities
            )
            if program.transitions == 0
        }
        mass = math.fsum(retained.values())
        self.assertLessEqual(
            max(
                abs(probability - retained[program] / mass)
                for program, probability in zip(
                    restricted.programs,
                    restricted.structure_probabilities,
                )
            ),
            1e-10,
        )

    def test_analysis_labels_and_trace_guard(self):
        world = v34.generate_world(
            3_400_003,
            v34.RelateConfig("reliable", True, False),
        )
        with self.assertRaises(ValueError):
            v34.score_world(replace(world, analysis_labels=("reliable",)))
        self.context.__exit__(None, None, None)
        try:
            with self.assertRaisesRegex(
                RuntimeError, "serializing trace context"
            ):
                v34.generate_world(
                    3_400_004,
                    v34.RelateConfig("reliable", True, False),
                )
        finally:
            self.context = serializing_trace_context(
                self.id() + ":restored"
            )
            self.context.__enter__()


if __name__ == "__main__":
    unittest.main()
