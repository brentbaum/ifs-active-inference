import unittest

from ref.trace_sink import serializing_trace_context
from ref import v37


class V37ProofTests(unittest.TestCase):
    def test_zero_seed_proof_battery(self):
        with serializing_trace_context(self.id()):
            result = v37.zero_seed_proofs()
        self.assertTrue(result["passed"])
        self.assertLessEqual(result["fixture_identity"]["maximum_atom_error"], 1e-10)

    def test_design_constants(self):
        self.assertEqual(v37.PERSISTENCE, (0.80, 0.90, 0.97))
        self.assertEqual(v37.DANGER_PRIOR, (0.5, 0.5))


if __name__ == "__main__":
    unittest.main()
