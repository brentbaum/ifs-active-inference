# V3.0 gate-5 software-repair authorization (evaluator, 2026-07-30)

Classification: pure software error in the gate-5 verification path (standing invalidate-and-repeat rule). The `recovery_rows` parity helper calls `local_log_scores` without forwarding the robustness `code_length_scale` hyperparameter (world generator and posterior scorer both correctly received 1.25; the decomposition check scored at the default 1.0), producing a spurious 1.247 parity error in the `shorter_code_penalty` cell whose scientific criteria (accuracy 0.9989, ECE 0.00065, coverage 1.0) all passed.

Authorized, narrowly: thread the hyperparameter through the parity helper; regression test pinning hyperparameter forwarding across all robustness cells; original FAIL retained; re-execute gate 5 (gate-5-repaired.json) with byte identity on all non-parity quantities; full fast suite green. Then freeze-readiness + manifest; stop before C-V30.
