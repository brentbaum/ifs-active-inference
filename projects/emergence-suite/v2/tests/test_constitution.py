import inspect
import math
import unittest

from ref.constitution import (
    audit_model,
    candidate_scorer,
    cumulative_constitution_audit,
    cumulative_graded_update_audit,
    independent_candidate_sum,
    independent_homotopy_posterior,
    publish_stratified_update_distribution,
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


class RevisedGradedUpdateConstitutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = cumulative_graded_update_audit()

    def test_four_part_criterion_passes_all_standing_stages(self):
        self.assertTrue(self.report["passed"])
        self.assertEqual(
            set(self.report["stages"]),
            {"V2.0", "V2.1", "V2.2.1", "V2.3.2-formation"},
        )
        for stage in self.report["stages"].values():
            self.assertEqual(
                set(stage["sections"]),
                {
                    "A_update_identity",
                    "B_finite_information",
                    "C_evidence_strength_homotopy",
                    "D_composition",
                },
            )
            self.assertTrue(
                all(
                    section["passed"]
                    for section in stage["sections"].values()
                )
            )

    def test_update_identity_and_no_authored_winner(self):
        for stage_name in ("V2.0", "V2.2.1", "V2.3.2-formation"):
            result = self.report["stages"][stage_name]["sections"][
                "A_update_identity"
            ]
            if stage_name == "V2.3.2-formation":
                self.assertLess(
                    result["maximum_absolute_identity_error"], 1e-10
                )
            else:
                self.assertLess(
                    result["maximum_absolute_error"], 1e-10
                )
            source = result["no_authored_assignment"]
            self.assertEqual(source["forbidden_assignment_targets"], [])
            self.assertEqual(source["winner_selection_calls"], [])
            self.assertEqual(
                source["posterior_assignments_inside_if_branches"], []
            )

    def test_frozen_information_bound_and_implied_binary_bound(self):
        formation = self.report["stages"]["V2.3.2-formation"][
            "sections"
        ]["B_finite_information"]
        self.assertAlmostEqual(
            formation["published_frozen_B_max"],
            3.801426508560692,
            places=15,
        )
        self.assertAlmostEqual(
            formation["enumerated_B_max"],
            formation["published_frozen_B_max"],
            places=12,
        )
        self.assertAlmostEqual(
            formation["implied_binary_probability_change_bound"],
            math.tanh(3.801426508560692 / 4.0),
            places=15,
        )
        self.assertTrue(
            formation["every_observed_slice_within_B_max"]
        )

    def test_homotopy_exact_analytic_finite_and_path_independent(self):
        formation = self.report["stages"]["V2.3.2-formation"][
            "sections"
        ]["C_evidence_strength_homotopy"]
        self.assertLess(
            formation[
                "maximum_exact_enumeration_vs_analytic_error"
            ],
            1e-10,
        )
        self.assertLess(
            formation[
                "maximum_forward_reverse_hysteresis_error"
            ],
            1e-10,
        )
        self.assertTrue(formation["finite_derivative_everywhere"])
        self.assertTrue(formation["no_discontinuity"])
        self.assertTrue(formation["no_hysteresis"])
        self.assertEqual(
            formation["per_observation_monotonicity_failures"], 0
        )
        self.assertEqual(
            formation["frozen_sign_monotonicity_failures"], []
        )
        source = inspect.getsource(independent_homotopy_posterior)
        self.assertNotIn("_homotopy_table", source)
        self.assertNotIn("ExactEngine", source)

    def test_formation_composition_checks_are_exact(self):
        composition = self.report["stages"]["V2.3.2-formation"][
            "sections"
        ]["D_composition"]
        self.assertLess(composition["maximum_error"], 1e-10)
        self.assertEqual(
            set(composition["checks"]),
            {
                "no_event_neutrality",
                "masked_slice_neutrality",
                "matched_statistic_reorder_invariance",
                "prequential_recombination",
                "independent_summation",
            },
        )

    def test_stratified_publisher_is_descriptive_not_criterial(self):
        profile = publish_stratified_update_distribution()
        self.assertFalse(profile["criterial"])
        self.assertEqual(
            profile["classification"], "distributional_stress"
        )
        self.assertEqual(
            set(profile["strata"]),
            {
                "no-event",
                "ordinary",
                "acute",
                "high-control",
                "low-control",
                "D-favoring",
                "P-favoring",
            },
        )
        self.assertEqual(profile["strata"]["no-event"]["maximum"], 0.0)


if __name__ == "__main__":
    unittest.main()
