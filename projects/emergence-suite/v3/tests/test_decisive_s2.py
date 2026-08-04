"""Zero-seed regression proofs for DT-S2-DESCENT."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import run_decisive_s2 as s2  # noqa: E402


class DecisiveS2Tests(unittest.TestCase):
    def test_frozen_scientific_sources(self) -> None:
        self.assertEqual(s2._assert_sources(), s2.SOURCE_HASHES)

    def test_control_oracle_optima(self) -> None:
        proof = s2._oracle_rollout()
        self.assertTrue(proof["passed"])
        self.assertEqual(proof["rows"]["undefended_acute"]["unique_optimum"], "direct_contact")
        self.assertEqual(proof["rows"]["exposure_rational"]["unique_optimum"], "repeated_exposure")
        self.assertEqual(proof["rows"]["reassurance_rational"]["unique_optimum"], "reassurance")

    def test_internal_policy_has_no_controller_input(self) -> None:
        beliefs = s2._beliefs(s2._initial_evidence("gated"))
        reference = s2.internal_policy_posterior(beliefs)
        for _action in s2.ACTIONS:
            self.assertEqual(reference, s2.internal_policy_posterior(dict(beliefs)))
        self.assertAlmostEqual(sum(reference), 1.0, places=12)

    def test_access_is_only_policy_sum(self) -> None:
        beliefs = s2._beliefs(s2._initial_evidence("gated"))
        posterior = s2.internal_policy_posterior(beliefs)
        expected = sum(posterior[s2.POLICIES.index(name)] for name in s2.ACCESS_POLICIES)
        self.assertAlmostEqual(s2.access_probability(posterior), expected, places=12)

    def test_fraction_is_32_unique_rows(self) -> None:
        self.assertEqual(len(s2.FRACTION_ROWS), 32)
        self.assertEqual(len({tuple(row.items()) for row in s2.FRACTION_ROWS}), 32)

    def test_forced_probe_is_slice_local_and_excluded_from_later_contact(self) -> None:
        self.assertTrue(s2._contact_eligibility("contact_vulnerable_material", False, True))
        self.assertFalse(s2._contact_eligibility("contact_vulnerable_material", False, False))
        self.assertFalse(s2._is_later_contact(s2.PROBE_TIME, True))
        self.assertTrue(s2._is_later_contact(s2.PROBE_TIME + 1, True))

    def test_low_permission_contact_is_selected_from_controller_policy(self) -> None:
        beliefs = s2._beliefs(s2._initial_evidence("gated"))
        posterior = s2.controller_posterior(
            beliefs,
            "gated",
            requested_action="contact_vulnerable_material",
        )
        self.assertAlmostEqual(sum(posterior), 1.0, places=12)
        self.assertEqual(posterior[s2.ACTIONS.index("contact_vulnerable_material")], 1.0)

    def test_registered_s2c_estimands_are_computable_and_nondegenerate(self) -> None:
        proof = s2.estimand_conformance()
        self.assertEqual(proof["verdict"], "PASS")
        self.assertTrue(all(proof["checks"].values()))


if __name__ == "__main__":
    unittest.main()
