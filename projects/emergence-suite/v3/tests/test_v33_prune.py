import math
import unittest
from dataclasses import asdict, replace

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

    def test_event_indexed_do_over_schedule(self):
        timely = v33.generate_world(
            3_330_000,
            v33.ReductionConfig(
                "configural",
                "post_revision",
                corrective_length=18,
                return_length=18,
            ),
        )
        no_do = v33.generate_world(
            3_330_000,
            v33.ReductionConfig(
                "configural",
                "none",
                corrective_length=18,
                return_length=18,
            ),
        )
        event = v33.root_revision_event(timely)
        timely_start = min(
            item.time
            for item in timely.slices
            if item.episode_kind == "imaginal_post"
        )
        no_do_start = min(
            item.time
            for item in no_do.slices
            if item.episode_kind == "no_do_masked"
        )
        self.assertEqual(timely_start, event + 1)
        self.assertEqual(no_do_start, event + 1)
        premature = v33.generate_world(
            3_330_001,
            v33.ReductionConfig(
                "none",
                "premature",
                return_burden=True,
                corrective_length=18,
                return_length=24,
            ),
        )
        self.assertLess(
            max(
                item.time
                for item in premature.slices
                if item.episode_kind == "imaginal_premature"
            ),
            min(
                item.time
                for item in premature.slices
                if item.episode_kind == "ordinary"
            ),
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

    def test_restricted_prior_and_candidate_common_masking(self):
        world = v33.generate_world(
            3_310_000,
            v33.ReductionConfig("suggestion_only", "none"),
        )
        full = v33.score_world(world).current
        restricted = v33.score_world(
            world, restrictions={"G_W": (0,)}
        ).current
        allowed = {
            program: probability
            for program, probability in zip(
                full.programs, full.probabilities
            )
            if v31.program_values(program)["G_W"] == 0
        }
        mass = math.fsum(allowed.values())
        self.assertLessEqual(
            max(
                abs(probability - allowed[program] / mass)
                for program, probability in zip(
                    restricted.programs, restricted.probabilities
                )
            ),
            1e-10,
        )
        timely = v33.generate_world(
            3_310_001,
            v33.ReductionConfig("configural", "post_revision"),
        )
        masked = replace(
            timely,
            slices=tuple(
                replace(
                    item,
                    mode=None,
                    root=None,
                    world=None,
                    policy_proposal=None,
                    action=None,
                    outcome=None,
                )
                if item.episode_kind == "imaginal_post"
                else item
                for item in timely.slices
            ),
        )
        dropped = replace(
            timely,
            slices=tuple(
                item
                for item in timely.slices
                if item.episode_kind != "imaginal_post"
            ),
        )
        masked_posterior = v33.score_world(masked).current
        dropped_posterior = v33.score_world(dropped).current
        self.assertLessEqual(
            max(
                abs(a - b)
                for a, b in zip(
                    masked_posterior.probabilities,
                    dropped_posterior.probabilities,
                )
            ),
            1e-10,
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
