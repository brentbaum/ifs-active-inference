import json
import math
import unittest

from ref import v36_bridge, v36_bridge_oracle
from ref.trace_sink import serializing_trace_context


class V36CommonTargetBridgeTests(unittest.TestCase):
    def test_public_dummy_fifteen_proofs(self):
        with serializing_trace_context("test-v36-r1-public-dummy") as sink:
            result = v36_bridge.bridge_proofs(v36_bridge.public_dummy())
        self.assertTrue(result["passed"], result)
        self.assertEqual(len(result["proofs"]), 15)
        self.assertLessEqual(result["forecast_semantics_error_max"], 1e-10)
        self.assertTrue(
            result["proofs"]["15_forecast_semantics_identity_all_five_targets"]
        )
        self.assertTrue(sink.events)

    def test_forecast_semantics_oracle_is_separate(self):
        dummy = v36_bridge.public_dummy()
        with serializing_trace_context("test-v36-r1-forecast-semantics"):
            for model, scored in (
                ("v2", v36_bridge.score_v2(dummy)),
                ("v3", v36_bridge.score_v3(dummy)),
            ):
                oracle = v36_bridge_oracle.direct_forecasts(dummy, model)
                for target, prediction in scored.items():
                    error = max(
                        abs(left - right)
                        for row, oracle_row in zip(
                            prediction.probabilities, oracle[target]
                        )
                        for left, right in zip(row, oracle_row)
                    )
                    self.assertLessEqual(error, 1e-10, (model, target))

    def test_independent_normalization_and_copy_hash(self):
        dummy = v36_bridge.public_dummy()
        with serializing_trace_context("test-v36-r1-oracle"):
            predictions = v36_bridge.score_v3(dummy)
        plain = {
            target: [list(row) for row in prediction.probabilities]
            for target, prediction in predictions.items()
        }
        self.assertLessEqual(
            v36_bridge_oracle.binary_normalization_error(plain), 1e-10
        )
        views = v36_bridge.adapter_documents(dummy)
        self.assertEqual(
            v36_bridge_oracle.canonical_hash(views["v2"]),
            v36_bridge_oracle.canonical_hash(views["v3"]),
        )

    def test_margin_is_log_one_point_zero_two(self):
        self.assertEqual(v36_bridge.DELTA, math.log(1.02))


if __name__ == "__main__":
    unittest.main()
