import copy
import json
import math
import unittest
from pathlib import Path

from ref import audit, v36, v36_oracle


ROOT = Path(__file__).resolve().parents[1]


class V36CompositionTests(unittest.TestCase):
    def test_public_dummy_recombination_and_input_copy(self):
        dummy = json.loads(
            (ROOT / "protocols" / "v3.6-public-dummy.json").read_text()
        )
        source = dummy["readout_dummy"]
        before = copy.deepcopy(source)
        result = v36_oracle.combine_readouts(source)
        self.assertEqual(source, before)
        self.assertAlmostEqual(result["q_identity_organization"], 0.7)
        self.assertAlmostEqual(result["q_context_specific"], 0.7)
        self.assertAlmostEqual(result["q_current_edge_absence"], 0.75)

    def test_code_length_identity_and_input_copy(self):
        dummy = json.loads(
            (ROOT / "protocols" / "v3.6-public-dummy.json").read_text()
        )["code_length_dummy"]
        priors = dummy["log_priors"]
        before = copy.deepcopy(priors)
        result = v36_oracle.code_length(priors, dummy["L_theta_given_H"])
        self.assertEqual(priors, before)
        self.assertLessEqual(
            abs(
                result["L_total"]
                - math.fsum(
                    result[key]
                    for key in (
                        "L_grammar", "L_H", "L_theta_given_H", "L_protocol"
                    )
                )
            ),
            v36.TOLERANCE,
        )

    def test_protocol_declaration_has_no_authored_conclusion(self):
        declaration = v36.protocol_declaration("full")
        self.assertEqual(tuple(row["event_index"] for row in declaration), tuple(range(10)))
        self.assertTrue(all(set(row) == {"event_index", "event_type", "available"} for row in declaration))

    def test_readout_schema_passes_one_posterior_audit(self):
        fields = {field.name for field in v36.CompositionReadout.__dataclass_fields__.values()}
        forbidden = {"formed", "winner", "part", "protector", "burden", "polarized", "exiled", "registered"}
        self.assertFalse(fields & forbidden)
        self.assertEqual(audit.audit_state(v36.protocol_declaration("full")), ())

    def test_compression_registry_counts_repairs(self):
        registry = json.loads(
            (ROOT / "audits" / "v3.6-compression-accounting.json").read_text()
        )
        repairs = set(registry["v3"]["repair_introduced_items_included"])
        self.assertIn("mode-specific support", repairs)
        self.assertIn("mode-specific contact outcome", repairs)
        self.assertIn("candidate-common registration", repairs)
        self.assertIn("stakes-weighted policy utility", repairs)
        self.assertTrue(registry["reductions"]["factor_templates_at_least_50_percent"])
        self.assertTrue(registry["reductions"]["constants_at_least_50_percent"])


if __name__ == "__main__":
    unittest.main()
