import ast
import inspect
import unittest

import numpy as np

from ref.v232_formation import (
    LABELS,
    PRIOR,
    SUPPORT,
    analytic_slice_bound,
    lesion_assays,
    score_history,
    score_slice,
    semantic_proofs,
    sign_table,
    slice_distribution,
)


class StaticFormationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.semantic = semantic_proofs()

    def test_normalization_zeros_decomposition_and_enumeration(self):
        self.assertLess(
            self.semantic["candidate_normalization_maximum_error"], 1e-12
        )
        self.assertEqual(
            self.semantic[
                "zero_row_maximum_absolute_expected_log_bf"
            ],
            0.0,
        )
        self.assertLess(
            self.semantic["decomposition_maximum_error"], 1e-10
        )
        self.assertLess(
            self.semantic[
                "independent_implementation_maximum_error"
            ],
            1e-10,
        )
        self.assertTrue(self.semantic["constitution"]["passed"])

    def test_pathways_and_analytic_bound(self):
        self.assertGreater(self.semantic["precision_pathway_effect"], 0)
        self.assertGreater(self.semantic["control_pathway_effect"], 0)
        self.assertGreater(self.semantic["context_pathway_effect"], 0)
        self.assertGreaterEqual(
            analytic_slice_bound(),
            self.semantic["maximum_enumerated_log_bf"],
        )

    def test_static_no_event_and_masked_histories(self):
        config = {
            "event": False,
            "precision": "ordinary",
            "control": "high",
            "broadcast": "integrated",
            "real_danger": False,
        }
        no_event = score_history([SUPPORT[2]] * 160, [config] * 160)
        self.assertTrue(np.array_equal(no_event["posterior"], PRIOR))
        posterior, evidence, detail = score_slice(
            PRIOR, None, config, masked=True
        )
        self.assertTrue(np.array_equal(posterior, PRIOR))
        self.assertEqual(evidence, 1.0)
        self.assertTrue(
            all(value == 0.0 for value in detail["pairwise_log_bf"].values())
        )

    def test_no_accumulator_transition_or_boolean_write(self):
        source = inspect.getsource(
            inspect.getmodule(slice_distribution)
        )
        self.assertNotIn("bounded_log_odds_accumulation", source)
        self.assertNotIn("structure_transition", source)
        tree = ast.parse(inspect.getsource(score_history))
        assigned = {
            target.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        self.assertNotIn("formed", assigned)

    def test_sign_table_has_all_zero_and_discriminating_rows(self):
        rows = sign_table()
        self.assertEqual(len(rows), 64)
        zeros = [
            row for row in rows if not row["event"] or row["masked"]
        ]
        self.assertEqual(len(zeros), 48)
        self.assertTrue(
            all(
                value == 0.0
                for row in zeros
                for key, value in row.items()
                if key.startswith("E_")
            )
        )
        self.assertTrue(
            any(
                row["event"]
                and not row["masked"]
                and row["real_danger"]
                and row["E_D_logBF_D_T"] > 0
                and row["E_D_logBF_P_D"] < 0
                for row in rows
            )
        )

    def test_lesions_target_only_declared_routes(self):
        lesions = lesion_assays()
        for result in lesions.values():
            self.assertLessEqual(
                abs(result["lesioned"]),
                min(0.02, abs(result["intact"]) / 4.0),
            )
            self.assertGreater(result["survivor"], 0)


if __name__ == "__main__":
    unittest.main()
