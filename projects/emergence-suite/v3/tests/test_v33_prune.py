import math
import unittest
from dataclasses import asdict

from ref import v31, v33, v33_oracle
from ref.trace_sink import serializing_trace_context


class V33PruneTests(unittest.TestCase):
    def setUp(self):
        self.context = serializing_trace_context(self.id())
        self.context.__enter__()

    def tearDown(self):
        self.context.__exit__(None, None, None)

    def test_same_programs_and_edge_identities_as_grow(self):
        self.assertEqual(v33.PROGRAMS, v31.PROGRAMS)
        self.assertEqual(v33.EDGE_NAMES, v31.EDGE_NAMES)

    def test_neutral_observation_is_exactly_structure_neutral(self):
        world = v33.generate_world(
            3_300_000,
            v33.ReductionConfig("configural", "none"),
        )
        before = v33.score_world(world)
        after = v33.score_world(v33.append_neutral_observation(world))
        self.assertLessEqual(
            max(
                abs(a - b)
                for a, b in zip(
                    before.current.probabilities,
                    after.current.probabilities,
                )
            ),
            1e-10,
        )

    def test_episode_label_is_not_evidence(self):
        world = v33.generate_world(
            3_300_001,
            v33.ReductionConfig("configural", "post_revision"),
        )
        relabeled = v33.relabel_episode(
            world, "imaginal_post", "ordinary"
        )
        before = v33.score_world(world)
        after = v33.score_world(relabeled)
        self.assertLessEqual(
            max(
                abs(a - b)
                for a, b in zip(
                    before.current.probabilities,
                    after.current.probabilities,
                )
            ),
            1e-10,
        )

    def test_independent_oracle_copies_and_matches(self):
        world = v33.generate_world(
            3_300_002,
            v33.ReductionConfig("configural", "none"),
        )
        slices = [
            asdict(item) for item in world.slices if item.context == 1
        ]
        snapshot = tuple(tuple(sorted(item.items())) for item in slices)
        production = v33.score_world(world).current
        programs, probabilities, evidence = v33_oracle.posterior(slices)
        production_by_bits = {
            (
                v31.program_values(program)["active_mode"],
                *(
                    v31.program_values(program)[edge]
                    for edge in v31.EDGE_NAMES
                ),
            ): probability
            for program, probability in zip(
                production.programs, production.probabilities
            )
        }
        self.assertLessEqual(
            max(
                abs(probability - production_by_bits[program])
                for program, probability in zip(programs, probabilities)
            ),
            1e-10,
        )
        self.assertLessEqual(abs(evidence - production.log_evidence), 1e-10)
        self.assertEqual(
            snapshot, tuple(tuple(sorted(item.items())) for item in slices)
        )

    def test_runtime_guard_refuses_untraced_generation(self):
        self.context.__exit__(None, None, None)
        try:
            with self.assertRaisesRegex(
                RuntimeError, "serializing trace context"
            ):
                v33.generate_world(
                    3_300_003,
                    v33.ReductionConfig("configural", "none"),
                )
        finally:
            self.context = serializing_trace_context(self.id() + ":restored")
            self.context.__enter__()


if __name__ == "__main__":
    unittest.main()
