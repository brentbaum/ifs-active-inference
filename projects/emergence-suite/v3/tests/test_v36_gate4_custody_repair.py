import unittest

from scripts.run_v36_gate4 import _conditioned_error


class V36Gate4CustodyRepairTests(unittest.TestCase):
    def test_retained_exact_zero_is_in_conditioned_support(self):
        full_keys = ("kept", "exact_zero", "deleted")
        full = (0.75, 0.0, 0.25)
        restricted_keys = ("kept",)
        restricted = (1.0,)
        error = _conditioned_error(
            full_keys, full, restricted_keys, restricted,
            lambda key: key != "deleted",
        )
        self.assertEqual(error, 0.0)


if __name__ == "__main__":
    unittest.main()
