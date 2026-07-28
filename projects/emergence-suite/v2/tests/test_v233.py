import hashlib
import json
import unittest
from pathlib import Path

import numpy as np

from ref.v232_formation import PRIOR
from ref.v233 import (
    DOSES,
    canonical_state_bytes,
    canonical_state_hash,
    classify_initial_strength,
    clone_state_bytes,
    corrective_stream,
    bank_ledger,
    lesion_assays,
    forbidden_path_audit,
    maintenance_slice,
    open_assays,
    robustness_assays,
    run_maintenance_trajectory,
    semantic_proofs,
    trajectory_readout,
)


class AvailabilityMaintenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.semantic = semantic_proofs()
        dummy = json.loads(
            Path("protocols/v2.3.3-public-dummy.json").read_text()
        )
        cls.dummy = dummy["formed_world_fixtures"][0]["serialized_state"]
        cls.bank = bank_ledger(760000, 761799)

    def test_all_twelve_semantic_proofs(self):
        self.assertEqual(self.semantic["proof_count"], 12)
        self.assertTrue(self.semantic["passed"])
        self.assertTrue(
            all(
                proof["passed"]
                for proof in self.semantic["proofs"].values()
            )
        )

    def test_missing_is_exactly_neutral_under_every_action_and_dose(self):
        outcomes, configurations = corrective_stream(762000, 1)
        for action in ("engage", "avoid", "sham"):
            for _dose in DOSES:
                posterior, evidence, detail = maintenance_slice(
                    PRIOR,
                    outcomes[0],
                    configurations[0],
                    do_action=action,
                    available=False,
                )
                self.assertTrue(np.array_equal(posterior, PRIOR))
                self.assertEqual(evidence, 1.0)
                self.assertTrue(
                    all(
                        value == 0.0
                        for value in detail["pairwise_log_bf"].values()
                    )
                )

    def test_complete_censoring_preserves_log_odds(self):
        outcomes, configurations = corrective_stream(762001, 12)
        result = run_maintenance_trajectory(
            self.dummy,
            outcomes,
            configurations,
            ["avoid"] * 12,
            [False] * 12,
        )
        readout = trajectory_readout(result)
        self.assertLessEqual(abs(readout["delta_L_PT"]), 1e-10)
        self.assertLessEqual(abs(readout["delta_L_PD"]), 1e-10)

    def test_canonical_hash_and_clones_are_bitwise(self):
        serialized = canonical_state_bytes(self.dummy)
        digest = canonical_state_hash(self.dummy)
        self.assertEqual(digest, hashlib.sha256(serialized).hexdigest())
        self.assertTrue(
            all(
                clone == serialized
                for clone in clone_state_bytes(serialized, 11)
            )
        )

    def test_strata_have_disjoint_frozen_boundaries(self):
        self.assertEqual(classify_initial_strength(0.60), "moderate")
        self.assertEqual(classify_initial_strength(0.75), "strong")
        self.assertEqual(classify_initial_strength(0.90), "very_strong")
        self.assertEqual(classify_initial_strength(0.98), "very_strong")
        self.assertIsNone(classify_initial_strength(0.59))
        self.assertIsNone(classify_initial_strength(0.99))

    def test_forbidden_paths_absent(self):
        result = forbidden_path_audit()
        self.assertTrue(result["passed"])
        self.assertTrue(all(result["checks"].values()))

    def test_gate_2_bank_qualification(self):
        self.assertTrue(self.bank["qualified"])
        self.assertEqual(
            self.bank["eligible_counts_retained"],
            {"moderate": 40, "strong": 40, "very_strong": 40},
        )
        self.assertFalse(self.bank["hash_mismatches"])
        self.assertFalse(self.bank["clone_mismatches"])

    def test_gate_3_open_assays(self):
        result = open_assays(self.bank)
        self.assertEqual(result["world_count"], 120)
        self.assertTrue(result["passed"])

    def test_gate_4_lesions(self):
        result = lesion_assays(self.bank)
        self.assertEqual(len(result["lesions"]), 8)
        self.assertTrue(result["passed"])

    def test_gate_5_robustness(self):
        result = robustness_assays(self.bank)
        self.assertEqual(len(result["cells"]), 32)
        self.assertTrue(result["passed"])


if __name__ == "__main__":
    unittest.main()
