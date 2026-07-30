import math
import unittest

from ref.v32 import (
    DEFAULT_HYPERPARAMETERS,
    DYNAMICS,
    SCOPES,
    TemporalStructure,
    full_prior_sum,
    generate_world,
    redescription_readouts,
    score_world,
    structure_space_size,
)
from ref.v32_oracle import brute_force_structure_posterior


class V32SplitTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
