import unittest
from unittest.mock import patch

import numpy as np

from ref import oracle, v23, v24, v244


class PerformanceAmendmentOneTests(unittest.TestCase):
    def test_fast_and_slow_oracle_audit_verdicts_match(self):
        model = v23.formation_model(overwhelm=1)
        fast_posterior, fast_evidence = oracle.brute_force(
            model, ("H",), {"B": 1}
        )
        slow_posterior, slow_evidence = oracle.brute_force(
            model, ("H",), {"B": 1}, slow=True
        )
        self.assertEqual(
            np.allclose(
                fast_posterior,
                slow_posterior,
                atol=1e-10,
                rtol=0,
            ),
            True,
        )
        self.assertEqual(
            np.isclose(
                fast_evidence,
                slow_evidence,
                atol=1e-10,
                rtol=0,
            ),
            True,
        )

    def test_crt_cached_and_cold_graphs_are_bit_identical(self):
        for seed in (790700, 790701):
            world = v24.generate_world(
                "context_split", seed, length=96
            )
            pre, _ = v24._heldout_partition(world["observations"])
            v244._cached_graph.cache_clear()
            cold = v244.crt_readout(pre, seed)
            warm = v244.crt_readout(pre, seed)
            self.assertEqual(cold["T0"], warm["T0"])
            self.assertEqual(cold["p_CRT"], warm["p_CRT"])
            self.assertEqual(cold["Q95"], warm["Q95"])
            self.assertEqual(cold["E_null"], warm["E_null"])
            self.assertEqual(cold["selective"], warm["selective"])
            self.assertTrue(np.array_equal(cold["null"], warm["null"]))

    def test_graph_cache_reuses_parameter_keyed_lattice(self):
        v244._cached_graph.cache_clear()
        key = v244._graph_parameter_key("context_split")
        first = v244._cached_graph("context_split", 72, key)
        second = v244._cached_graph("context_split", 72, key)
        self.assertIs(first, second)
        info = v244._cached_graph.cache_info()
        self.assertEqual(info.misses, 1)
        self.assertEqual(info.hits, 1)

    def test_scalar_cs_transition_preserves_compare_families_bits(self):
        observations = v24.generate_world(
            "context_split", 790700, length=96
        )["observations"]
        fast = v24.compare_families(observations)
        with patch.object(
            v24,
            "_cs_transition",
            v24._cs_transition_numpy_reference,
        ):
            reference = v24.compare_families(observations)
        self.assertTrue(
            np.array_equal(fast["posterior"], reference["posterior"])
        )
        self.assertTrue(
            np.array_equal(
                fast["log_evidence"], reference["log_evidence"]
            )
        )
        self.assertEqual(
            fast["maximum_update_identity_error"],
            reference["maximum_update_identity_error"],
        )
        for fast_score, reference_score in zip(
            fast["scores"], reference["scores"]
        ):
            self.assertEqual(
                fast_score.log_evidence,
                reference_score.log_evidence,
            )
            self.assertEqual(
                fast_score.per_slice_log_predictive,
                reference_score.per_slice_log_predictive,
            )
            self.assertEqual(
                fast_score.total_complexity,
                reference_score.total_complexity,
            )


if __name__ == "__main__":
    unittest.main()
