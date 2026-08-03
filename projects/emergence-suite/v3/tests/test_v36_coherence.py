import unittest

from ref.v36_coherence import prove_generator_coherence


class GeneratorCoherenceTests(unittest.TestCase):
    def test_external_and_native_generator_supports_are_coherent(self):
        result = prove_generator_coherence()
        self.assertEqual(result["verdict"], "PASS")
        self.assertTrue(result["population_a_native_generator"]["passed"])
        self.assertEqual(len(result["external_strata"]), 4)
        self.assertTrue(all(row["passed"] for row in result["external_strata"]))


if __name__ == "__main__":
    unittest.main()
