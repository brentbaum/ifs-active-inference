import hashlib
import json
import unittest

from ref import v36_bridge, v36_round12
from ref.trace_sink import serializing_trace_context


class V36Round12Tests(unittest.TestCase):
    def test_shared_target_support_audit(self):
        result = v36_round12.shared_target_support_audit()
        self.assertTrue(result["passed"])
        self.assertFalse(result["selection_uses_model_score_difference"])
        for target in v36_round12.TARGETS:
            self.assertEqual(result["targets"][target]["intersection"], [0, 1])
            self.assertEqual(
                result["targets"][target]["external_public_grid"],
                [0.2, 0.5, 0.8],
            )

    def test_public_dummy_complete_calibration_serialization(self):
        dummy = v36_bridge.public_dummy()
        with serializing_trace_context("test-v36-round12-calibration-state"):
            state = v36_round12.v3_calibration_state(dummy)
        self.assertEqual(
            state["joint_structure_posterior_representation"],
            "outer_product_of_complete_factor_posteriors",
        )
        self.assertLessEqual(
            state["class_posterior"]["normalization_error"], 1e-10
        )
        self.assertEqual(len(state["active_count_posterior"]), 3)
        self.assertEqual(set(state["edge_posteriors"]), set(state["truth_edges"]))
        self.assertEqual(
            set(state["class_coverage"]), {"0.5", "0.8", "0.9", "0.95"}
        )

    def test_scientific_source_hashes_remain_frozen(self):
        root = v36_round12.__file__
        del root
        spec_path = (
            v36_round12.v36_bridge.SUITE_ROOT
            / "v3" / "protocols" / "v3.6-r1-bridge-spec.json"
        )
        spec = json.loads(spec_path.read_text())
        observed = {
            relative: hashlib.sha256(
                (v36_round12.v36_bridge.SUITE_ROOT / relative).read_bytes()
            ).hexdigest()
            for relative in spec["scientific_source_sha256"]
        }
        self.assertEqual(observed, spec["scientific_source_sha256"])


if __name__ == "__main__":
    unittest.main()
