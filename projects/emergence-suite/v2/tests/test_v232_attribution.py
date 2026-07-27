import ast
import inspect
import unittest

import numpy as np

from ref.audit import audit_one_posterior
from ref.v232 import (
    anti_authoring_audit,
    attribution_update,
    formation_step_bound,
    initial_joint,
    policy_avoid_probability,
    posterior_readouts,
    protocol_state,
    relief_update,
    semantic_proofs,
)


class AttributionSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proofs = semantic_proofs()

    def test_masking_action_and_exact_efficacy_semantics(self):
        self.assertLess(
            self.proofs["1_masked_bf"]["maximum_posterior_change"],
            1e-12,
        )
        self.assertLess(
            self.proofs["1_masked_bf"]["repeated_60_maximum_change"],
            1e-12,
        )
        self.assertLess(
            self.proofs["2_eta_zero_equivalence"][
                "posterior_maximum_difference"
            ],
            1e-12,
        )
        self.assertLess(
            abs(
                self.proofs["3_eta_one_non_disconfirmation"][
                    "theta_change"
                ]
            ),
            1e-12,
        )
        self.assertLess(
            self.proofs["5_action_no_direct_update"][
                "maximum_posterior_change"
            ],
            1e-12,
        )

    def test_environment_policy_separation_and_probe(self):
        self.assertLess(
            self.proofs["4_engagement_disconfirms"]["theta_change"], 0
        )
        self.assertGreater(
            self.proofs["6_relief_policy_only"][
                "policy_probability_change"
            ],
            0,
        )
        self.assertEqual(
            self.proofs["6_relief_policy_only"][
                "environment_maximum_change"
            ],
            0,
        )
        self.assertGreaterEqual(
            self.proofs["8_pure_avoidance_confound"]["correlation"], 0.40
        )
        self.assertGreaterEqual(
            self.proofs["9_probe_breaks_confound"]["absolute_reduction"],
            0.15,
        )

    def test_exact_spike_enumeration_and_continuity(self):
        self.assertTrue(
            self.proofs["7_exact_spike_mass"]["represented_exactly"]
        )
        self.assertLess(
            self.proofs["10_enumeration_tolerance"][
                "maximum_posterior_error"
            ],
            1e-10,
        )
        self.assertLess(
            formation_step_bound()["posterior_change_bound"], 0.12
        )

    def test_k_is_a_readout_and_state_obeys_one_posterior_rule(self):
        prior = initial_joint(0.8)
        posterior, evidence, latent = attribution_update(
            prior,
            action="avoid",
            observation_mode="full",
            outcome_observation="safe",
        )
        readouts = posterior_readouts(
            posterior, latent, action="avoid"
        )
        self.assertGreaterEqual(
            readouts["prevented_catastrophe_probability_K"], 0
        )
        state = protocol_state(
            posterior,
            evidence,
            latent,
            action="avoid",
            relief_alpha=np.tile(np.array([2.0, 2.0]), (2, 1)),
            metadata={"stage": "V2.3.2"},
        )
        self.assertNotIn("K", state.posterior_store)
        audit_one_posterior(state)

    def test_no_boolean_write_and_anti_authoring_assertions(self):
        tree = ast.parse(inspect.getsource(attribution_update))
        assigned = {
            target.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        }
        self.assertNotIn("formed", assigned)
        self.assertTrue(anti_authoring_audit()["passed"])

    def test_relief_update_has_no_environment_argument(self):
        alpha = np.tile(np.array([2.0, 2.0]), (2, 1))
        moved = relief_update(
            alpha, action="avoid", relief_observed=True
        )
        self.assertGreater(
            policy_avoid_probability(moved),
            policy_avoid_probability(alpha),
        )


if __name__ == "__main__":
    unittest.main()
