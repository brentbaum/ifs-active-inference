import math
import unittest
from pathlib import Path

from ref.trace_sink import (
    audit_runner_trace_contexts,
    serializing_trace_context,
)
from ref.v32 import (
    DEFAULT_HYPERPARAMETERS,
    DYNAMICS,
    SCOPES,
    TemporalStructure,
    full_prior_sum,
    generate_world,
    redescription_readouts,
    score_world,
    single_regime_scope_neutrality_error,
    structure_space_size,
)
from ref.v32_oracle import (
    brute_force_structure_posterior,
    single_regime_scope_neutrality_error as brute_force_scope_neutrality,
)


class V32SplitTests(unittest.TestCase):
    def setUp(self):
        self.trace_context = serializing_trace_context(self.id())
        self.trace_context.__enter__()

    def tearDown(self):
        self.trace_context.__exit__(None, None, None)

    def test_bounded_structure_space_and_prior(self):
        self.assertEqual(structure_space_size(), 432)
        self.assertAlmostEqual(full_prior_sum(), 1.0, places=14)

    def test_generator_and_independent_oracle_agree(self):
        truth = TemporalStructure(
            2,
            ("context_specific", "cue_specific"),
            ("discrete_recurrent_context", "ordered_random_walk"),
        )
        world = generate_world(3_200_000, structure=truth, length=10)
        production = score_world(world)
        oracle = brute_force_structure_posterior(world, DEFAULT_HYPERPARAMETERS)
        by_program = dict(zip(oracle.programs, oracle.probabilities))
        self.assertLessEqual(
            max(
                abs(probability - by_program[program])
                for program, probability in zip(
                    production.programs, production.probabilities
                )
            ),
            1e-10,
        )
        self.assertLessEqual(abs(production.log_evidence - oracle.log_evidence), 1e-10)

    def test_restricted_prior_identity(self):
        world = generate_world(3_200_001, length=12)
        restrictions = {
            "scope:cue_emission": ("shared_global", "cue_specific")
        }
        direct = score_world(world, restrictions=restrictions)
        full = score_world(world)
        allowed = [
            (program, probability)
            for program, probability in zip(full.programs, full.probabilities)
            if program.scopes[0] in restrictions["scope:cue_emission"]
        ]
        normalizer = math.fsum(probability for _, probability in allowed)
        conditioned = {
            program: probability / normalizer for program, probability in allowed
        }
        self.assertLessEqual(
            max(
                abs(probability - conditioned[program])
                for program, probability in zip(
                    direct.programs, direct.probabilities
                )
            ),
            1e-10,
        )

    def test_readouts_do_not_mutate_posterior(self):
        world = generate_world(3_200_002, length=12)
        posterior = score_world(world)
        before = posterior.probabilities
        redescription_readouts(posterior)
        self.assertEqual(before, posterior.probabilities)

    def test_all_scope_and_dynamics_productions_execute(self):
        seed = 3_200_010
        for index, scope in enumerate(SCOPES):
            for dynamics in DYNAMICS:
                structure = TemporalStructure(
                    2, (scope, "shared_global"), (dynamics, "static")
                )
                posterior = score_world(
                    generate_world(seed + index, structure=structure, length=8)
                )
                self.assertTrue(math.isfinite(posterior.log_evidence))

    def test_single_regime_scope_neutrality_and_dormancy(self):
        structure = TemporalStructure(
            2,
            ("context_specific", "context_specific"),
            ("discrete_recurrent_context", "discrete_recurrent_context"),
        )
        world = generate_world(
            3_230_000,
            structure=structure,
            length=24,
            evidence_style="single_regime",
        )
        production_error = single_regime_scope_neutrality_error(world)
        oracle_error = brute_force_scope_neutrality(
            world, DEFAULT_HYPERPARAMETERS
        )
        self.assertLessEqual(production_error, 1e-10)
        self.assertLessEqual(oracle_error, 1e-10)
        posterior = score_world(world)
        self.assertEqual(
            posterior.parameter_mean("cue_emission", context=1, cue=0), 0.5
        )


class V32TraceGuardTests(unittest.TestCase):
    def test_public_generation_refuses_without_trace_sink(self):
        with self.assertRaisesRegex(RuntimeError, "serializing trace context"):
            generate_world(3_230_010, length=8)

    def test_runner_repository_has_no_unguarded_public_calls(self):
        scripts = Path(__file__).resolve().parents[1] / "scripts"
        self.assertEqual(audit_runner_trace_contexts(scripts), ())


if __name__ == "__main__":
    unittest.main()
