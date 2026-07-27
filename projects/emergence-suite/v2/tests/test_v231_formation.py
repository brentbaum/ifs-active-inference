import ast
import inspect
import unittest

from ref.audit import audit_one_posterior
from ref.v231 import (
    analytic_step_bound,
    generalization_assay,
    infer_slice,
    lesion_assays,
    original_open_assays,
    recovery_assay,
    semantic_proofs,
)


class BoundedFormationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.semantic = semantic_proofs()
        cls.recovery = recovery_assay()
        cls.opened = original_open_assays()

    def test_exact_comparison_and_analytic_step_bound(self):
        self.assertLess(
            self.semantic["finite_comparison"]["maximum_error"], 1e-10
        )
        self.assertLess(
            analytic_step_bound()["adjacent_slice_change_bound"],
            0.294529387,
        )

    def test_no_formation_write_rule(self):
        tree = ast.parse(inspect.getsource(infer_slice))
        assigned_names = {
            target.id
            for node in ast.walk(tree)
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            for target in (
                node.targets
                if isinstance(node, ast.Assign)
                else [node.target]
            )
            if isinstance(target, ast.Name)
        }
        self.assertNotIn("formed", assigned_names)

    def test_recovery(self):
        self.assertGreaterEqual(self.recovery["structure_accuracy"], 0.85)
        self.assertGreaterEqual(
            self.recovery["mean_true_structure_probability"], 0.75
        )
        self.assertLessEqual(self.recovery["structure_brier"], 0.20)
        self.assertLessEqual(self.recovery["structure_ece"], 0.10)
        self.assertGreaterEqual(
            self.recovery["controllability_accuracy"], 0.75
        )
        self.assertGreaterEqual(self.recovery["broadcast_accuracy"], 0.75)

    def test_original_open_gates_and_continuity(self):
        self.assertGreaterEqual(
            self.opened["acute_formation"][
                "final_persistent_95_interval"
            ][0],
            0.70,
        )
        self.assertGreaterEqual(
            self.opened["gradual_accumulation"][
                "final_persistent_95_interval"
            ][0],
            0.70,
        )
        self.assertGreaterEqual(
            self.opened["gradual_accumulation"][
                "acute_minus_gradual_maximum_step"
            ],
            0.05,
        )
        self.assertLessEqual(
            self.opened["step_injection"]["maximum"], 0.294529387
        )
        for effect in self.opened["closed_loop_vs_exact_replay"].values():
            self.assertGreater(effect[1], 0.0)

    def test_selective_lesions_and_audit(self):
        lesions = lesion_assays()
        self.assertLessEqual(
            abs(
                lesions["controllability_inference"][
                    "lesioned_contrast"
                ]
            ),
            0.03,
        )
        self.assertLessEqual(
            lesions["formation_coupling"]["lesioned_distance_from_prior"],
            0.08,
        )
        self.assertLessEqual(
            abs(
                lesions["reflexive_broadcast_context"][
                    "lesioned_contrast"
                ]
            ),
            0.03,
        )
        audit_one_posterior(
            self.opened["worlds"]["acute"][0]["states"][-1]
        )

    def test_varied_schedule_generalization_smoke(self):
        varied = generalization_assay(
            diagnosis_world_count=128, paired_world_count=16
        )
        self.assertLessEqual(varied["surface_incremental_cv_r2"], 0.05)
        self.assertGreaterEqual(
            varied["low_minus_high_control_95_interval"][0], 0.20
        )
        self.assertEqual(varied["step_injection"]["exceedances"], 0)


if __name__ == "__main__":
    unittest.main()
