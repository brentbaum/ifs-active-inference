import ast
import inspect
import unittest

from ref.audit import audit_one_posterior
from ref.v20 import run_v20
from ref.v21 import run_v21
from ref.v221 import run_v221
from ref.v23 import (
    infer_slice,
    lesion_assays,
    open_assays,
    recovery_assay,
    semantic_proofs,
)


class FormationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.semantic = semantic_proofs()
        cls.recovery = recovery_assay()
        cls.open = open_assays()

    def test_three_routes_are_likelihood_or_posterior_effects(self):
        self.assertGreaterEqual(
            self.semantic["event_precision"]["log_odds_increase"], 1.0
        )
        self.assertLess(
            self.semantic["event_precision"]["analytic_factor_error"], 1e-12
        )
        self.assertLess(
            self.semantic["controllability"][
                "low_control_action_log_evidence_difference"
            ],
            1e-12,
        )
        self.assertGreaterEqual(
            self.semantic["controllability"][
                "high_control_action_log_evidence_difference"
            ],
            0.50,
        )
        self.assertGreaterEqual(
            self.semantic["reflexive_broadcast"][
                "persistent_probability_effect"
            ],
            0.10,
        )

    def test_finite_comparison_and_action_transition(self):
        self.assertLess(
            self.semantic["finite_comparison"]["maximum_error"], 1e-10
        )
        self.assertGreaterEqual(
            self.semantic["action_transition"][
                "avoid_minus_engage_threat_probability"
            ],
            0.50,
        )
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
        self.assertNotIn("persistent", assigned_names)

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
        self.assertLessEqual(
            self.recovery["policy_parameter_mean_absolute_error"], 0.08
        )
        self.assertGreaterEqual(
            self.recovery["policy_parameter_95_interval_coverage"], 0.85
        )

    def test_open_assays_and_realized_chain(self):
        self.assertEqual(self.open["world_count"], 64)
        self.assertGreaterEqual(
            self.open["acute_formation"]["final_persistent_95_interval"][0],
            0.70,
        )
        self.assertGreaterEqual(
            self.open["gradual_accumulation"][
                "final_persistent_95_interval"
            ][0],
            0.70,
        )
        self.assertGreaterEqual(
            self.open["gradual_accumulation"][
                "formation_change_95_interval"
            ][0],
            0.35,
        )
        self.assertGreaterEqual(
            self.open["gradual_accumulation"][
                "acute_minus_gradual_maximum_step"
            ],
            0.05,
        )
        self.assertGreaterEqual(
            self.open["overwhelm_with_control"][
                "acute_minus_controlled_95_interval"
            ][0],
            0.15,
        )
        self.assertGreaterEqual(
            self.open["low_control_without_overwhelm"][
                "low_minus_high_control_95_interval"
            ][0],
            0.15,
        )
        self.assertGreaterEqual(
            self.open["adaptive_persistent_threat"][
                "final_persistent_95_interval"
            ][0],
            0.75,
        )
        chain = self.open["closed_loop_vs_exact_replay"]
        for effect in chain.values():
            self.assertGreater(effect[1], 0.0)
        self.assertGreater(self.open["step_injection"]["count"], 0)

    def test_selective_lesions(self):
        lesions = lesion_assays()
        self.assertLessEqual(
            abs(
                lesions["controllability_inference"]["lesioned_contrast"]
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

    def test_one_posterior_and_cumulative_gates(self):
        sample_state = self.open["worlds"]["acute"][0]["states"][-1]
        audit_one_posterior(sample_state)
        self.assertTrue(run_v20()["passed"])
        self.assertTrue(run_v21()["passed"])
        self.assertTrue(run_v221()["passed"])


if __name__ == "__main__":
    unittest.main()
