import ast
import inspect
import json
import unittest
from pathlib import Path

from ref.audit import audit_one_posterior
from ref.v231 import (
    analytic_step_bound,
    infer_slice,
    lesion_assays,
    original_open_assays,
    semantic_proofs,
)


class BoundedFormationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.semantic = semantic_proofs()
        cls.opened = original_open_assays()
        cls.retired_ledger = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "results"
                / "V2.3.1r"
                / "stage-report.json"
            ).read_text(encoding="utf-8")
        )

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

    def test_retired_recovery_ledger_remains_rescinded(self):
        recovery = self.retired_ledger["recovery"]
        self.assertAlmostEqual(
            recovery["structure_ece"],
            0.10579451215553712,
            places=14,
        )
        self.assertGreater(recovery["structure_ece"], 0.10)
        self.assertFalse(
            self.retired_ledger["gates"]["gate_2_recovery"]
        )

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

    def test_retired_generalization_ledger_remains_rescinded(self):
        varied = self.retired_ledger["generalization_assay"]
        self.assertAlmostEqual(
            varied["surface_incremental_cv_r2"],
            0.6173327730910273,
            places=14,
        )
        self.assertGreater(varied["surface_incremental_cv_r2"], 0.05)
        self.assertAlmostEqual(
            varied["low_minus_high_control_95_interval"][0],
            0.07275975652956246,
            places=14,
        )
        self.assertFalse(
            self.retired_ledger["gates"][
                "gate_3_direct_composition"
            ]
        )


if __name__ == "__main__":
    unittest.main()
