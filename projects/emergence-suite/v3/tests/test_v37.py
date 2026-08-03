import unittest

from ref.trace_sink import serializing_trace_context
from ref import v36_bridge, v37
from scripts import run_v37


class V37ProofTests(unittest.TestCase):
    def test_zero_seed_proof_battery(self):
        with serializing_trace_context(self.id()):
            result = v37.zero_seed_proofs()
        self.assertTrue(result["passed"])
        self.assertLessEqual(result["fixture_identity"]["maximum_atom_error"], 1e-10)

    def test_design_constants(self):
        self.assertEqual(v37.PERSISTENCE, (0.80, 0.90, 0.97))
        self.assertEqual(v37.DANGER_PRIOR, (0.5, 0.5))

    def test_candidate_common_schedule_all_truth_structures(self):
        result = v37.candidate_common_schedule_proof()
        self.assertTrue(result["passed"])
        self.assertEqual(result["schedule_signature_count"], 1)
        self.assertEqual(result["maximum_schedule_difference"], 0)
        self.assertLessEqual(result["complete_data_maximum_atom_error"], 1e-10)
        self.assertLessEqual(
            result["complete_data_maximum_normalization_error"], 1e-10
        )

    def test_exact_worker_rows_pickle_roundtrip_with_nested_types(self):
        with serializing_trace_context(self.id()):
            document = v36_bridge.public_dummy()
            world = v37.V37World(
                document=document,
                persistence_index=0,
                partner_state_path=(0,) * len(document.slices),
                danger_state_path=(0,) * len(document.slices),
                contact_parameter=int(document.contact_response),
            )
            native = run_v37._native_row_from_world(world, seed=document.seed)
            external = run_v37._external_row_from_document(
                document, phase="unit_test_zero_seed"
            )
        self.assertTrue(run_v37._roundtrip(native)["deep_equal"])
        self.assertTrue(run_v37._roundtrip(external)["deep_equal"])


if __name__ == "__main__":
    unittest.main()
