from __future__ import annotations

import copy
import math
import unittest
from pathlib import Path

import numpy as np

from ref import audit, grammar, oracle
from scripts.run_v30 import recovery_rows


class V30GrammarTests(unittest.TestCase):
    def test_01_cpts_and_transitions_normalize(self):
        for dynamics in grammar.DYNAMICS:
            matrix = grammar.transition_matrix(dynamics)
            np.testing.assert_allclose(matrix.sum(axis=1), 1.0, atol=1e-12)
        for cardinality in (2, 3, 4):
            for truth in range(cardinality):
                self.assertAlmostEqual(
                    float(grammar._categorical_row(truth, cardinality, 0.86).sum()),
                    1.0,
                    places=12,
                )

    def test_02_structure_prior_normalizes(self):
        self.assertAlmostEqual(grammar.full_program_prior_sum(), 1.0, places=12)
        self.assertEqual(grammar.structure_space_size(), 786_432)

    def test_03_absent_edge_is_independent(self):
        for parent in (0, 1):
            for child in (0, 1):
                self.assertEqual(
                    grammar.edge_conditional_probability(False, parent, child), 0.5
                )

    def test_04_dormant_slots_are_idle(self):
        structure = grammar.GrammarStructure(
            1,
            1,
            (0,) * 8,
            ("shared_global",) * 2,
            ("static",) * 2,
        )
        world = grammar.generate_world(3_000_001, structure=structure, length=1)
        self.assertEqual(grammar.dormant_slot_likelihood(world, "mode", 2), 1.0)
        self.assertEqual(grammar.dormant_slot_likelihood(world, "context", 2), 1.0)

    def test_05_independent_oracle_copies_inputs_and_matches(self):
        supports = {
            "active_modes": (0, 1),
            "edge:G_W": (0, 1),
        }
        observations = (
            ("active_modes", 1, False),
            ("edge:G_W", 0, False),
        )
        original_supports = copy.deepcopy(supports)
        original_observations = copy.deepcopy(observations)
        result, log_evidence = oracle.brute_force_posterior(
            supports, observations, 0.86
        )
        self.assertEqual(supports, original_supports)
        self.assertEqual(observations, original_observations)
        for field_index, (field, support) in enumerate(supports.items()):
            prior = grammar.field_prior(field, support)
            weights = []
            for candidate in range(len(support)):
                likelihood = (
                    0.86 if observations[field_index][1] == candidate else 0.14
                )
                weights.append(prior[candidate] * likelihood)
            expected = np.asarray(weights) / sum(weights)
            np.testing.assert_allclose(result[field], expected, atol=1e-12)
        expected_evidence = math.prod(
            sum(
                grammar.field_prior(field, support)[candidate]
                * (0.86 if observations[index][1] == candidate else 0.14)
                for candidate in range(len(support))
            )
            for index, (field, support) in enumerate(supports.items())
        )
        self.assertAlmostEqual(log_evidence, math.log(expected_evidence), places=12)

    def test_06_local_scores_recombine(self):
        world = grammar.generate_world(3_000_002, length=3)
        local = grammar.local_log_scores(world, world.structure)
        self.assertAlmostEqual(sum(local.values()), world.exact_log_probability, places=10)

    def test_07_do_action_has_no_selection_likelihood(self):
        world = grammar.generate_world(3_000_003, length=3)
        changed = grammar.GrammarWorld(
            world.seed,
            world.bounds,
            world.structure,
            world.observations,
            tuple(reversed(world.interventions)),
            world.exact_log_probability,
            world.rng_keys,
        )
        self.assertEqual(grammar.score_world(world), grammar.score_world(changed))

    def test_08_scopes_compile(self):
        expected = {
            "shared_global": ("shared_global", None),
            "cue_specific": ("cue_specific", 2),
            "context_specific": ("context_specific", 1),
            "mode_specific": ("mode_specific", 3),
        }
        for scope, result in expected.items():
            self.assertEqual(
                grammar.compile_scope(scope, cue=2, context=1, mode=3), result
            )

    def test_09_dynamics_compile(self):
        for dynamics in grammar.DYNAMICS:
            matrix = grammar.transition_matrix(dynamics)
            self.assertTrue(np.all(matrix >= 0))
            np.testing.assert_allclose(matrix.sum(axis=1), 1.0, atol=1e-12)
        one_way = grammar.transition_matrix("one_way_change")
        self.assertEqual(float(np.tril(one_way, -1).sum()), 0.0)

    def test_10_mixed_scopes_coexist(self):
        structure = grammar.GrammarStructure(
            2,
            2,
            (1, 1, 0, 1, 0, 1, 1, 0),
            ("cue_specific", "context_specific"),
            ("ordered_random_walk", "discrete_recurrent_context"),
        )
        world = grammar.generate_world(3_000_004, structure=structure, length=2)
        scored = grammar.score_world(world)
        self.assertIn("scope:cue_emission", scored.supports)
        self.assertIn("dynamics:outcome_emission", scored.supports)

    def test_11_no_analysis_label_reaches_inference(self):
        world = grammar.generate_world(3_000_005, length=1)
        labeled = grammar.GrammarWorld(
            world.seed,
            world.bounds,
            world.structure,
            world.observations,
            world.interventions,
            world.exact_log_probability,
            world.rng_keys,
            ("formed",),
        )
        with self.assertRaises(ValueError):
            grammar.score_world(labeled)
        self.assertEqual(audit.audit_imports(Path("ref")), ())

    def test_released_block_threading(self):
        with self.assertRaises(ValueError):
            grammar.generate_world(4_000_000)
        world = grammar.generate_world(
            4_000_000, released_block=(4_000_000, 4_001_999), length=1
        )
        self.assertEqual(world.seed, 4_000_000)

    def test_gate5_parity_helper_forwards_robustness_hyperparameters(self):
        cells = (
            {},
            {
                "bounds": grammar.GrammarBounds(
                    context_slots=1, mode_slots=1, cue_count=2
                )
            },
            {
                "bounds": grammar.GrammarBounds(
                    context_slots=2, mode_slots=2, cue_count=3
                )
            },
            {
                "bounds": grammar.GrammarBounds(
                    context_slots=3, mode_slots=3, cue_count=4
                )
            },
            {"missingness": 0.25},
            {
                "hyperparameters": grammar.GrammarHyperparameters(
                    diagnostic_reliability=0.86,
                    concentration=0.5,
                    code_length_scale=1.25,
                )
            },
            {
                "hyperparameters": grammar.GrammarHyperparameters(
                    diagnostic_reliability=0.86,
                    concentration=1.0,
                    code_length_scale=1.0,
                )
            },
        )
        for offset, kwargs in enumerate(cells):
            rows = recovery_rows(
                [3_015_900 + offset],
                length=3,
                **kwargs,
            )
            self.assertLessEqual(
                max(row["log_probability_parity_error"] for row in rows),
                1e-10,
            )


if __name__ == "__main__":
    unittest.main()
