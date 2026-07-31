import copy
import json
import math
import unittest
from pathlib import Path
from types import SimpleNamespace

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

    def test_do_over_schedule_is_event_indexed_not_fixed_slice(self):
        def world(boundary):
            slices = [
                SimpleNamespace(time=time, episode_kind="imaginal_premature", context=1, mode=1, root=None)
                for time in range(boundary - 3, boundary)
            ]
            slices.append(
                SimpleNamespace(time=boundary, episode_kind="corrective", context=1, mode=1, root=0)
            )
            return SimpleNamespace(
                config=SimpleNamespace(do_over="premature"),
                slices=tuple(slices),
            )

        early = v36.do_over_schedule_audit(world(7))
        late = v36.do_over_schedule_audit(world(19))
        self.assertTrue(early["event_indexed"])
        self.assertTrue(late["event_indexed"])
        self.assertEqual(early["root_revision_event"], 7)
        self.assertEqual(late["root_revision_event"], 19)
        self.assertLess(max(early["premature_times"]), 7)
        self.assertLess(max(late["premature_times"]), 19)

    def test_pruning_disabled_keeps_corrective_event_stream(self):
        declarations = v36._component_declarations(
            v36.ComposeConfig(protocol="structural_pruning_disabled")
        )
        self.assertEqual(declarations["reduction"].corrective_evidence, "configural")
        self.assertEqual(declarations["reduction"].do_over, "post_revision")

    def test_premature_finding_is_descriptive_and_has_no_floor(self):
        parameters = json.loads(
            (ROOT / "protocols" / "v3.6-parameters.json").read_text()
        )
        self.assertNotIn(
            "premature_do_over", parameters["criteria"]["effect_minima"]
        )
        finding = parameters["retained_descriptive_findings"][
            "premature_do_over_endpoint_path_independence"
        ]
        self.assertIsNone(finding["floor"])
        self.assertFalse(finding["gate_criterion"])
        self.assertTrue(finding["required_in_every_downstream_profile"])


if __name__ == "__main__":
    unittest.main()
