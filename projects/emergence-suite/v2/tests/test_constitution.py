import inspect
import unittest

from ref.constitution import (
    audit_model,
    candidate_scorer,
    cumulative_constitution_audit,
    independent_candidate_sum,
)
from ref.v20 import model_comparison_model


class ModelEvidenceConstitutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = cumulative_constitution_audit()

    def test_all_nine_invariants_at_all_standing_stages(self):
        self.assertTrue(self.report["passed"])
        for stage in ("V2.0", "V2.1", "V2.2.1"):
            results = self.report[stage]["results"]
            self.assertEqual(len(results), 9)
            self.assertTrue(all(item["passed"] for item in results.values()))

    def test_masked_absent_and_identical_predictions_are_zero(self):
        for stage in ("V2.0", "V2.1", "V2.2.1"):
            results = self.report[stage]["results"]
            self.assertAlmostEqual(
                results["3_masked_increment_zero"][
                    "incremental_log_bf"
                ],
                0.0,
                places=12,
            )
            self.assertAlmostEqual(
                results["4_absent_increment_zero"][
                    "incremental_log_bf"
                ],
                0.0,
                places=12,
            )
            self.assertAlmostEqual(
                results["5_identical_predictions_zero"][
                    "incremental_log_bf"
                ],
                0.0,
                places=12,
            )

    def test_independent_path_shares_no_scorer_code(self):
        scorer_source = inspect.getsource(candidate_scorer)
        independent_source = inspect.getsource(independent_candidate_sum)
        self.assertNotIn("candidate_scorer", independent_source)
        self.assertNotIn("ExactEngine", independent_source)
        self.assertNotEqual(scorer_source, independent_source)

    def test_static_no_evidence_sequence_preserves_prior(self):
        model, observed = model_comparison_model()
        report = audit_model(
            model,
            structure="H",
            observation="D",
            sequence=[observed],
        )
        self.assertEqual(
            report["results"]["8_no_evidence_dynamics"][
                "declared_dynamics"
            ],
            "static",
        )
        self.assertEqual(
            report["results"]["8_no_evidence_dynamics"][
                "predicted_final"
            ],
            [0.5, 0.5],
        )


if __name__ == "__main__":
    unittest.main()
