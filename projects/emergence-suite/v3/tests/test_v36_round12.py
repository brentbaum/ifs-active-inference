import hashlib
import json
import unittest

from ref import v36_bridge, v36_fixture_oracle, v36_round12
from ref.trace_sink import serializing_trace_context


class V36Round12Tests(unittest.TestCase):
    def test_custody_rescoped_blocks_exclude_barred_first_seeds(self):
        self.assertEqual(v36_round12.V2_NATIVE_BLOCK, (3_700_000, 3_701_999))
        self.assertEqual(v36_round12.V3_NATIVE_BLOCK, (3_692_001, 3_693_999))
        self.assertEqual(
            v36_round12.EXTERNAL_QUALIFICATION_BLOCK,
            (3_694_001, 3_695_999),
        )

    def test_context_fixture_uses_module_prior_and_exact_marker_bridge(self):
        initial = v36_round12._dummy_context_initial("context_split")
        self.assertEqual([mass for _state, mass in initial], [0.5, 0.5])
        for descriptor in ("then", "now", "none"):
            row = v36_round12.v24.PARAMETERS["observation_interface"][
                "context_marker_cpt_nonmissing"
            ][descriptor]
            expected = row[1] / (row[0] + row[1])
            self.assertLessEqual(
                abs(
                    v36_round12._dummy_context_bridge_probability(descriptor)
                    - expected
                ),
                1e-10,
            )

    def test_all_native_fixture_dummy_joints_match_independent_oracle(self):
        for target in v36_round12.TARGETS:
            production = v36_round12.native_v2_fixture_dummy_joint(target)
            oracle = v36_fixture_oracle.v2_joint(target)
            keys = set(production) | set(oracle)
            self.assertLessEqual(
                max(abs(production.get(key, 0.0) - oracle.get(key, 0.0)) for key in keys),
                1e-10,
                target,
            )
        production_v3 = v36_round12.native_v3_fixture_dummy_factors()
        oracle_v3 = v36_fixture_oracle.v3_factors()
        for factor in ("protect", "temporal"):
            keys = set(production_v3[factor]) | set(oracle_v3[factor])
            self.assertLessEqual(
                max(
                    abs(
                        production_v3[factor].get(key, 0.0)
                        - oracle_v3[factor].get(key, 0.0)
                    )
                    for key in keys
                ),
                1e-10,
                factor,
            )

    def test_partner_dummy_is_named_remaining_bernoulli_and_normalized(self):
        channels = tuple(v36_round12.v26a.CHANNELS)
        self.assertEqual(channels.count("remaining"), 1)
        self.assertEqual(
            v36_round12.v26a.EMISSIONS.shape[1], len(channels)
        )
        production = v36_round12.native_v2_fixture_dummy_joint("partner")
        oracle = v36_fixture_oracle.v2_joint("partner")
        self.assertLessEqual(abs(sum(production.values()) - 1.0), 1e-10)
        self.assertLessEqual(abs(sum(oracle.values()) - 1.0), 1e-10)
        self.assertEqual(set(production), set(oracle))

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
