import unittest
import math

from scripts.run_v36_gate4 import (
    _conditioned_error,
    _independent_conditioned_error,
    _positive_log_evidence,
)


class V36Gate4CustodyRepairTests(unittest.TestCase):
    def test_retained_exact_zero_is_in_conditioned_support(self):
        full_keys = ("kept", "exact_zero", "deleted")
        full = (0.75, 0.0, 0.25)
        restricted_keys = ("kept", "exact_zero")
        restricted = (1.0, 0.0)
        error = _conditioned_error(
            full_keys, full, restricted_keys, restricted,
            lambda key: key != "deleted",
        )
        self.assertEqual(error, 0.0)

    def test_full_atom_keys_prevent_reliability_collapse(self):
        full_keys = (
            ("structure", 0, 0),
            ("structure", 0, 1),
            ("deleted", 0, 0),
            ("deleted", 0, 1),
        )
        full = (0.09, 0.81, 0.01, 0.09)
        restricted_keys = full_keys[:2]
        restricted = (0.10, 0.90)
        allowed = lambda atom: atom[0] == "structure"
        self.assertLessEqual(
            _conditioned_error(
                full_keys, full, restricted_keys, restricted, allowed
            ),
            1e-15,
        )
        self.assertLessEqual(
            _independent_conditioned_error(
                full_keys, full, restricted_keys, restricted, allowed
            ),
            1e-15,
        )
        collapsed = (("structure", 0), ("structure", 0))
        with self.assertRaisesRegex(AssertionError, "not unique"):
            _independent_conditioned_error(
                collapsed, (0.09, 0.81), (("structure", 0),), (1.0,),
                lambda _atom: True,
            )

    def test_log_space_evidence_positivity_survives_linear_underflow(self):
        log_evidence = -1000.0
        self.assertEqual(math.exp(log_evidence), 0.0)
        self.assertTrue(_positive_log_evidence(log_evidence))
        self.assertFalse(_positive_log_evidence(-math.inf))
        self.assertFalse(_positive_log_evidence(None))


if __name__ == "__main__":
    unittest.main()
