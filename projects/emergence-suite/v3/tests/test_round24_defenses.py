"""Permanent regression coverage for the external round-24 defenses."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import run_round24_defenses as defenses  # noqa: E402


class Round24DefenseTests(unittest.TestCase):
    def test_full_path_generator_scorer_identity(self) -> None:
        native = defenses.native_identity()
        external = defenses.external_identity()
        self.assertTrue(native["support_equal"])
        self.assertTrue(external["support_equal"])
        self.assertLessEqual(native["maximum_error"], defenses.TOL)
        self.assertLessEqual(external["maximum_error"], defenses.TOL)

    def test_typed_forecast_semantics(self) -> None:
        manifest = defenses.forecast_manifest()
        self.assertTrue(manifest["passed"])
        self.assertEqual(
            set(manifest["targets"]),
            {"identity", "outcome", "context", "partner", "contact"},
        )
        self.assertTrue(
            all(
                target["target_type"] == "observable"
                for target in manifest["targets"].values()
            )
        )

    def test_proof_scope_ledger_is_complete_per_entry(self) -> None:
        ledger = defenses.ledger()
        required = {
            "proof",
            "premise",
            "files_functions",
            "scope",
            "dependent_batteries",
            "invalidated_by",
        }
        self.assertTrue(ledger["proofs"])
        for entry in ledger["proofs"]:
            self.assertEqual(set(entry), required)

    def test_metamorphic_invariance(self) -> None:
        result = defenses.metamorphic()
        self.assertTrue(result["passed"])
        for name, value in result.items():
            if name.endswith("error"):
                self.assertLessEqual(value, defenses.TOL)


if __name__ == "__main__":
    unittest.main()
