"""Zero-seed T-CAP1 semantic regression tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ref import tcap1  # noqa: E402
from scripts import run_tcap1  # noqa: E402


class TCap1Tests(unittest.TestCase):
    def test_semantic_proofs(self) -> None:
        proof = run_tcap1.semantic_proofs()
        self.assertTrue(all(proof["checks"].values()))

    def test_allocation_is_one_cycle_delayed(self) -> None:
        q = 0.3
        before = tcap1.allocation_probability(q, .5, 4.0, 0, .6)
        self.assertEqual(before, tcap1.allocation_probability(q, .5, 4.0, 0, .6))
        self.assertNotEqual(before, tcap1.allocation_probability(.8, .5, 4.0, 0, .6))

    def test_allocation_observation_normalizes(self) -> None:
        for allocation in (0, 1):
            self.assertAlmostEqual(sum(tcap1.allocation_observation_probability(value, allocation, .8) for value in (0, 1)), 1.0, places=12)

    def test_channel_atoms_normalize_on_common_support(self) -> None:
        for channel in range(5):
            for bundle in (0, 1):
                for allocation in (0, 1):
                    total = sum(tcap1.observation_atom_probability(channel, observed, bundle, allocation, .4) for observed in (None, 0, 1))
                    self.assertAlmostEqual(total, 1.0, places=12)

    def test_round27_estimand_conformance(self) -> None:
        proof = run_tcap1.estimand_conformance()
        self.assertTrue(all(proof["checks"].values()))

    def test_full_information_replay_likelihood_identity(self) -> None:
        observations = (1, 0, 1, 0, 1)
        for bundle in (0, 1):
            transparent = tcap1.transparent_log_likelihood(observations, bundle, .3, full_information=True)
            represented = tcap1.represented_log_likelihood(observations, 1, bundle, .3, .7, .8, full_information=True)
            self.assertAlmostEqual(transparent, represented, places=12)

    def test_arm_common_world_proof(self) -> None:
        proof = run_tcap1.arm_common_world_proof()
        self.assertEqual(proof["verdict"], "PASS")
        self.assertTrue(all(proof["checks"].values()))
        self.assertTrue(proof["checks"]["cue_schedules_arm_invariant"])
        self.assertTrue(proof["checks"]["potential_outcome_uniform_keys_arm_invariant"])
        self.assertTrue(proof["checks"]["exogenous_uniform_keys_arm_invariant"])
        self.assertTrue(proof["checks"]["inference_architectures_replay_exact_realized_stream"])

    def test_only_allocation_rng_key_varies_by_arm(self) -> None:
        reference = {
            "bundle": tcap1.world_component_key("bundle-stay"),
            "meta": tcap1.world_component_key("meta"),
            "delivery": tuple(tcap1.world_component_key("delivery", index) for index in range(5)),
            "token": tuple(tcap1.world_component_key("token", index) for index in range(5)),
        }
        for arm in tcap1.ARMS:
            self.assertEqual(reference["bundle"], tcap1.world_component_key("bundle-stay"))
            self.assertTrue(tcap1.allocation_component_key(arm).endswith(arm))

    def test_bistability_is_paired_initial_condition_readout(self) -> None:
        def score(values):
            return {"trajectory": tuple({"q_bundle": value} for value in values)}
        result = tcap1.bistability_readout(score((.02, .02, .02, .02)), score((.98, .98, .98, .98)))
        self.assertTrue(result["two_stable_fixed_points"])
        self.assertEqual(result["fixed_point_count"], 2)

    def test_allocation_aware_oracle_conditions_on_realized_allocation(self) -> None:
        observations = (1, None, 0, 1, None)
        for bundle in (0, 1):
            direct = tcap1._channel_log_likelihood(observations, bundle, 1, .4)  # noqa: SLF001
            oracle = tcap1.allocation_aware_log_likelihood(observations, bundle, 1, .4)
            self.assertEqual(direct, oracle)

    def test_coupling_zero_probability_identity_is_exact(self) -> None:
        for q in (.02, .3, .8):
            for cue in (0.0, .5, 1.0):
                left = tcap1.allocation_probability(q, cue, 0.0, 1, .6)
                right = tcap1.allocation_probability(q, cue, 0.0, 1, .6)
                self.assertEqual(left, right)


if __name__ == "__main__":
    unittest.main()
