# Sealed stage challenge C-V2.0 — kernel exactness on a novel graph

**Sealed by evaluator before V2.0 development. Runs on the frozen V2.0 kernel with ZERO new kernel code — only the public graph/protocol vocabulary. Inexpressibility or any needed code change is a prospection failure.**

## Configuration
A 5-slice temporal model, all discrete, declared entirely in the kernel's public vocabulary:
- Two latent chains X (ternary) and Y (binary) with separate transition CPTs; X's transition is action-controlled (two actions).
- A collider: observation O1ₜ depends jointly on (Xₜ, Yₜ) (categorical CPT, 4 outcomes).
- A second observation O2ₜ depends on Yₜ only, with a learnable reliability parameter under a conjugate prior.
- Structure comparison: H1 = as above; H2 = O1 depends on Xₜ only (Y-edge severed). Same parameter count discipline as the kernel's finite comparison requires.

## Tests (seeds from escrow block C-V20; 50 generated episodes)
1. **Exactness:** filtered and smoothed posteriors over (Xₜ, Yₜ) match brute-force enumeration (independently coded in the challenge runner via direct summation over all 3⁵·2⁵ trajectories) within 1e-10, for every t, on 10 episodes under each action policy.
2. **Learning:** the O2 reliability parameter's posterior mean converges within 0.05 of truth by episode 50 (truth varies per seed).
3. **Comparison:** generating from H1, log-evidence favors H1 in ≥ 45/50 episodes by ≥ 1 nat cumulative; generating from H2, mirrored.
4. **Mutation:** perturbing the collider CPT toward independence must lower H1's evidence margin monotonically across three preregistered perturbation sizes.

Pass = all four. Any kernel modification, special-case branch, or numerical tolerance change to pass = failure, reported as such.
