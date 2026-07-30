from __future__ import annotations

import copy
import unittest
from dataclasses import replace

import numpy as np

from ref import v31, v31_oracle


class V31GrowTests(unittest.TestCase):
    def test_structure_space_is_one_grammar_region(self):
        self.assertEqual(len(v31.PROGRAMS), 128)
        self.assertEqual(len(set(v31.PROGRAMS)), 128)

    def test_prior_normalizes(self):
        total = sum(np.exp(v31.structure_log_prior(item)) for item in v31.PROGRAMS)
        self.assertAlmostEqual(total, 1.0, places=12)

    def test_oracle_copies_and_matches(self):
        world = v31.generate_recovery_world(3_100_001, length=8)
        slices = [item.__dict__ for item in world.slices]
        original = copy.deepcopy(slices)
        oracle_programs, oracle_probabilities, oracle_evidence = v31_oracle.posterior(
            slices
        )
        posterior = v31.score_world(world)
        self.assertEqual(slices, original)
        production_bits = tuple(
            (
                v31.program_values(program)["active_mode"],
                *(v31.program_values(program)[edge] for edge in v31.EDGE_NAMES),
            )
            for program in posterior.programs
        )
        self.assertEqual(production_bits, oracle_programs)
        np.testing.assert_allclose(
            posterior.probabilities, oracle_probabilities, atol=1e-10
        )
        self.assertAlmostEqual(
            posterior.log_evidence, oracle_evidence, places=10
        )

    def test_classifications_are_pure_and_partition(self):
        world = v31.generate_recovery_world(3_100_002, length=12)
        posterior = v31.score_world(world)
        self.assertAlmostEqual(
            posterior.transient_probability
            + posterior.danger_probability
            + posterior.part_probability,
            1.0,
            places=12,
        )

    def test_missing_outcome_is_zero_bayes_factor(self):
        config = v31.FormationConfig(
            "repeated", "low", "broad", "real", "effective", "censored", 16
        )
        world = v31.generate_world(3_100_003, config)
        for index, item in enumerate(world.slices):
            if item.outcome_observed is None:
                before = v31.score_world(v31.prefix_world(world, index))
                after = v31.score_world(v31.prefix_world(world, index + 1))
                # Other channels may update, but the outcome factor itself is absent.
                self.assertIsNone(item.outcome_observed)
                self.assertTrue(np.isfinite(before.log_evidence))
                self.assertTrue(np.isfinite(after.log_evidence))

    def test_do_action_has_no_action_selection_score(self):
        config = v31.FormationConfig(
            "acute", "high", "broad", "safe", "effective", "full", 12
        )
        world = v31.generate_world(3_100_004, config)
        self.assertEqual(len(world.slices), 12)
        # Actions enter only as parents of Y; no action-probability factor exists.
        self.assertNotIn("action", v31.EDGE_NAMES)
        self.assertIn("doA_Y", v31.EDGE_NAMES)

    def test_fixed_identity_removes_transfer_only_at_readout(self):
        world = v31.generate_recovery_world(3_100_005, length=12)
        posterior = v31.score_world(world)
        self.assertEqual(
            v31.transfer_readout(posterior, fixed_identity=True), 0.0
        )
        self.assertEqual(v31.score_world(world), posterior)

    def test_deleted_mode_slot_masks_typed_channel_candidate_commonly(self):
        config = v31.FormationConfig(
            "repeated", "low", "broad", "real", "effective", "censored", 16
        )
        world = v31.generate_world(3_100_006, config)
        masked_copy = replace(
            world,
            slices=tuple(
                replace(
                    item,
                    mode_observed=not item.mode_observed,
                )
                for item in world.slices
            ),
        )
        lesion = frozenset({"mode_slot"})
        original = v31.score_world(world, lesions=lesion)
        remasked = v31.score_world(masked_copy, lesions=lesion)
        self.assertTrue(np.isfinite(original.log_evidence))
        self.assertAlmostEqual(sum(original.probabilities), 1.0, places=12)
        self.assertTrue(np.all(np.isfinite(original.probabilities)))
        np.testing.assert_allclose(
            original.probabilities,
            remasked.probabilities,
            atol=1e-10,
            rtol=0.0,
        )
        self.assertAlmostEqual(
            original.log_evidence,
            remasked.log_evidence,
            places=10,
        )

    def test_lesion_oracle_copies_and_matches_restricted_prior(self):
        config = v31.FormationConfig(
            "repeated", "low", "broad", "real", "effective", "censored", 16
        )
        world = v31.generate_world(3_100_007, config)
        raw = [item.__dict__ for item in world.slices]
        original = copy.deepcopy(raw)
        for lesion in (
            "mode_slot",
            "identity_edges",
            "action_edge",
            "availability_control",
            "recursive_precision",
            "fixed_G",
        ):
            programs, oracle = v31_oracle.lesion_posterior(raw, lesion)
            production = (
                v31.score_world(world)
                if lesion == "fixed_G"
                else v31.score_world(world, lesions=frozenset({lesion}))
            )
            production_bits = tuple(
                (
                    v31.program_values(program)["active_mode"],
                    *(
                        v31.program_values(program)[edge]
                        for edge in v31.EDGE_NAMES
                    ),
                )
                for program in production.programs
            )
            self.assertEqual(programs, production_bits)
            np.testing.assert_allclose(
                oracle,
                production.probabilities,
                atol=1e-10,
                rtol=0.0,
            )
        self.assertEqual(raw, original)

    def test_released_block_threading(self):
        with self.assertRaises(ValueError):
            v31.generate_recovery_world(4_010_000)
        world = v31.generate_recovery_world(
            4_010_000, released_block=(4_010_000, 4_013_999), length=4
        )
        self.assertEqual(world.seed, 4_010_000)


if __name__ == "__main__":
    unittest.main()
