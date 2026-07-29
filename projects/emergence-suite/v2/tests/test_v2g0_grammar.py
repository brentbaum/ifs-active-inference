import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ref import protocol_ir, v2g0_fixtures as fixtures, world_ir


SEED = 1_000_000


class V2G0GrammarSemanticProofs(unittest.TestCase):
    def sample(self, process, seed=SEED):
        compiled = world_ir.compile_world(fixtures.world(process))
        trace = world_ir.sample_world(compiled, seed)
        return compiled, trace

    def test_01_every_process_primitive_normalizes_and_scores(self):
        primitives = [
            fixtures.static(),
            fixtures.iid(),
            fixtures.markov(),
            fixtures.ordered_drift(),
            fixtures.change_point(),
            fixtures.recurrent_context(),
            fixtures.action_contingent(),
            fixtures.masked_observation(),
            fixtures.joint_episode(),
            fixtures.partner_process(),
            fixtures.joint_policy_outcome(),
        ]
        for index, process in enumerate(primitives):
            with self.subTest(kind=process["kind"]):
                compiled, trace = self.sample(process, SEED + index)
                production = world_ir.log_prob_world(compiled, trace)
                oracle = world_ir.independent_world_log_prob(
                    fixtures.world(process), trace
                )
                self.assertAlmostEqual(production, oracle, places=12)

    def test_02_exact_onset_window_mass(self):
        process = fixtures.change_point()
        self.assertAlmostEqual(world_ir.public_normalizer(process), 0.6, places=14)
        _, trace = self.sample(process)
        self.assertIn(trace.truth_trace["change"]["onset"], range(2, 8))

    def test_03_exact_recurrence_conditioned_normalizer(self):
        process = fixtures.recurrent_context()
        normalizer = world_ir.public_normalizer(process)
        self.assertGreater(normalizer, 0.0)
        self.assertLess(normalizer, 1.0)
        _, trace = self.sample(process)
        path = trace.truth_trace["context"]
        first_change = next(i for i in range(1, len(path)) if path[i] != path[i - 1])
        self.assertIn(path[0], path[first_change + 1 :])

    def test_04_subset_scoping_is_published(self):
        _, trace = self.sample(fixtures.ordered_drift())
        self.assertEqual(trace.process_scopes["drift"], ("cue:1", "cue:2"))
        self.assertNotIn("cue:0", trace.process_scopes["drift"])

    def test_05_disjoint_product_composition(self):
        spec = fixtures.world(fixtures.iid(), fixtures.recurrent_context())
        compiled = world_ir.compile_world(spec)
        trace = world_ir.sample_world(compiled, SEED)
        self.assertEqual(set(trace.truth_trace), {"iid", "context"})

    def test_06_shared_latent_composition(self):
        _, trace = self.sample(fixtures.shared_latent())
        value = trace.truth_trace["shared-context"]
        self.assertEqual(value["targets"]["cue:left"], value["latent"])
        self.assertEqual(value["targets"]["cue:right"], value["latent"])

    def test_07_mixture_has_explicit_finite_variable(self):
        _, trace = self.sample(fixtures.mixture())
        self.assertIn(
            trace.mixture_components["mixed-process"],
            {"stable-component", "drift-component"},
        )

    def test_08_mixed_drift_plus_recurrent_context(self):
        spec, protocol = fixtures.composition_cells()[
            "mixed_subset_drift_plus_recurrent_split"
        ]
        trace = protocol_ir.run_bridge({}, spec, protocol, SEED)
        self.assertEqual(set(trace.truth_trace), {"drift", "context"})

    def test_09_action_is_an_intervention_not_world_evidence(self):
        process = fixtures.action_contingent()
        spec = fixtures.world(process)
        protocol = fixtures.protocol(
            {"name": "availability", "source_process": "availability"},
            actions=tuple(process["actions"]),
        )
        trace = protocol_ir.run_bridge({}, spec, protocol, SEED)
        self.assertEqual(trace.interventions, tuple(process["actions"]))
        self.assertNotIn("action_probability", trace.inference_input)

    def test_10_missingness_is_candidate_common_and_neutral(self):
        data = fixtures.iid()
        mask = fixtures.masked_observation()
        spec = fixtures.world(data, mask)
        protocol = fixtures.protocol(
            {
                "name": "masked",
                "source_process": "iid",
                "masked_by": "mask",
            }
        )
        trace = protocol_ir.run_bridge({}, spec, protocol, SEED)
        observed = trace.observation_trace[0]["values"]
        truth = trace.truth_trace["iid"]
        availability = trace.truth_trace["mask"]
        self.assertEqual(
            observed,
            [value if present else None for value, present in zip(truth, availability)],
        )
        self.assertTrue(mask["candidate_common"])

    def test_11_generic_bridge_accepts_multiple_families(self):
        protocol = fixtures.protocol({"name": "x", "source_process": "x"})
        for process in (fixtures.iid("x"), fixtures.ordered_drift("x")):
            trace = protocol_ir.run_bridge(
                {"banked": [0.2, 0.8]}, fixtures.world(process), protocol, SEED
            )
            self.assertEqual(trace.initial_state["banked"], [0.2, 0.8])

    def test_12_independent_log_probability_parity(self):
        compiled, trace = self.sample(fixtures.partner_process())
        self.assertLessEqual(
            abs(
                world_ir.log_prob_world(compiled, trace)
                - world_ir.independent_world_log_prob(compiled.spec, trace)
            ),
            1e-10,
        )

    def test_13_no_protocol_label_available_to_inference(self):
        spec = fixtures.world(fixtures.iid())
        protocol = fixtures.protocol(
            {"name": "outcome", "source_process": "iid"},
            name="secret-protocol-label",
        )
        trace = protocol_ir.run_bridge({}, spec, protocol, SEED)
        payload = repr(dict(trace.inference_input))
        self.assertNotIn("secret-protocol-label", payload)
        self.assertNotIn("protocol_spec_hash", payload)

    def test_14_rng_keys_have_all_four_required_parts(self):
        _, trace = self.sample(fixtures.partner_process())
        self.assertTrue(trace.component_rng_keys)
        for key in trace.component_rng_keys:
            self.assertEqual(len(key), 4)
            self.assertEqual(key[0], "V2.G0")
            self.assertEqual(key[1], SEED)
            self.assertIsInstance(key[2], str)
            self.assertIsNotNone(key[3])

    def test_15_sealed_escrow_is_inaccessible(self):
        compiled = world_ir.compile_world(fixtures.world(fixtures.static()))
        with self.assertRaisesRegex(ValueError, "escrow"):
            world_ir.sample_world(compiled, 2_000_000)

    def test_16_diagnosis_seeds_are_inaccessible_to_public_sampler(self):
        compiled = world_ir.compile_world(fixtures.world(fixtures.static()))
        with self.assertRaisesRegex(ValueError, "diagnosis"):
            world_ir.sample_world(compiled, 1_010_000)

    def test_17_schema_dry_run_is_deterministic_and_score_free(self):
        spec = fixtures.world(fixtures.iid())
        protocol = fixtures.protocol({"name": "x", "source_process": "iid"})
        first = protocol_ir.dry_run_schema(spec, protocol, SEED)
        second = protocol_ir.dry_run_schema(spec, protocol, SEED)
        self.assertEqual(first.deterministic_hash, second.deterministic_hash)
        self.assertFalse(first.scientific_scores_inspected)

    def test_18_overlapping_product_scopes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "overlap"):
            world_ir.compile_world(
                fixtures.world(
                    fixtures.iid("one", ("same",)),
                    fixtures.iid("two", ("same",)),
                )
            )

    def test_19_unnormalized_transition_is_rejected(self):
        process = fixtures.markov()
        process["transition"]["a"] = [0.8, 0.3]
        with self.assertRaisesRegex(ValueError, "sum to one"):
            world_ir.compile_world(fixtures.world(process))

    def test_20_bounded_continuous_iid_has_exact_density(self):
        process = {
            "name": "continuous",
            "kind": "iid",
            "scope": ["latent:continuous"],
            "length": 3,
            "distribution": "uniform",
            "bounds": [-2.0, 2.0],
        }
        compiled, trace = self.sample(process)
        self.assertAlmostEqual(
            world_ir.log_prob_world(compiled, trace), -3.0 * math.log(4.0)
        )

    def test_21_minimum_visit_restriction_is_exact(self):
        process = fixtures.recurrent_context()
        process["restriction"] = {"minimum_visits": {"old": 4, "new": 2}}
        _, trace = self.sample(process)
        path = trace.truth_trace["context"]
        self.assertGreaterEqual(path.count("old"), 4)
        self.assertGreaterEqual(path.count("new"), 2)

    def test_22_conditioned_sampling_uses_no_seed_rejection(self):
        _, trace = self.sample(fixtures.recurrent_context())
        path_keys = [
            key for key in trace.component_rng_keys if key[3] == "conditioned_path"
        ]
        self.assertEqual(len(path_keys), 1)

    def test_23_trace_contains_every_custody_field(self):
        _, trace = self.sample(fixtures.iid())
        for name in (
            "world_spec_hash",
            "protocol_spec_hash",
            "process_scopes",
            "truth_trace",
            "observation_trace",
            "interventions",
            "component_rng_keys",
            "exact_world_log_probability",
            "output_schema_hash",
        ):
            self.assertTrue(hasattr(trace, name))

    def test_24_joint_policy_vector_conditions_outcome(self):
        _, trace = self.sample(fixtures.joint_policy_outcome())
        value = trace.truth_trace["joint-outcome"]
        self.assertEqual(value["policies"], fixtures.joint_policy_outcome()["policies"])
        self.assertEqual(len(value["outcomes"]), 3)

    def test_25_gate_runner_custody_regressions(self):
        import run_v2g0_gates

        checks = {
            "every_cell_executes": True,
            "zero_new_code_required": True,
        }
        self.assertEqual(run_v2g0_gates._verdict(checks), "PASS")
        self.assertNotIn("new_code_required", checks)
        manifest = run_v2g0_gates._verify_v244_manifest()
        self.assertEqual(manifest["base_manifest_file_count"], 86)
        self.assertEqual(manifest["effective_manifest_file_count"], 87)
        self.assertEqual(manifest["mismatches"], [])
        self.assertEqual(
            set(manifest["custody_files"]),
            {"base", "addenda"},
        )
        self.assertIn(
            "results/V2.4.4/freeze-readiness.md",
            manifest["overlaid_entries"],
        )

    def test_26_file_based_seed_release_and_development_identity(self):
        compiled = world_ir.compile_world(fixtures.world(fixtures.static()))
        development_before = world_ir.sample_world(compiled, SEED)
        with tempfile.TemporaryDirectory() as directory:
            release_path = Path(directory) / "released-blocks.json"
            release_path.write_text(
                json.dumps(
                    {
                        "stage": "V2.G0",
                        "version": 1,
                        "released_blocks": [
                            {
                                "start": 3_000_000,
                                "end": 3_000_499,
                                "purpose": "sealed",
                                "release_id": "SYNTHETIC-TEST-BLOCK",
                                "authorization_commit": "test-fixture",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with (
                patch.object(world_ir, "RELEASED_BLOCKS_PATH", release_path),
                patch.object(world_ir, "SEALED_ESCROW", (3_000_000, 3_000_499)),
            ):
                sealed = world_ir.sample_world(compiled, 3_000_000)
                self.assertEqual(sealed.component_rng_keys[0][1], 3_000_000)
                with self.assertRaisesRegex(ValueError, "diagnosis"):
                    world_ir.sample_world(compiled, 1_010_000)
                development_with_release = world_ir.sample_world(compiled, SEED)
        self.assertEqual(development_before, development_with_release)

        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing-release-record.json"
            with patch.object(world_ir, "RELEASED_BLOCKS_PATH", missing):
                development_without_record = world_ir.sample_world(compiled, SEED)
        self.assertEqual(development_before, development_without_record)


if __name__ == "__main__":
    unittest.main()
