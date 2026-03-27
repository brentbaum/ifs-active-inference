# Note for Edmundo — Simulation Results (2026-03-27)

## Summary

We now have three simulation versions. V3 is the one that matters most.

## V2: Proves Moves 1 and 2

- 3 hidden factors, 5 observation channels, gated witnessed self-state
- Cascade diagonal (self-state → threat → outcome → policy) under relational depth
- H1 vs H2: cascade present only when self-state is upstream
- Self-energy sweep shows threshold at E_t ≈ 0.60-0.65

**BUT:** Adversarial Test 4 showed v2 does NOT prove Move 3. Replacing Channel 5's self-state content with threat content produced similar dynamics. The model can't distinguish where evidence enters the causal chain. The gating does the work, not the content.

## V3: Proves Move 3 (generalization)

Designed through 2-round adversarial collaboration with GPT 5.4.

- 2 hidden factors: shared self-state + stimulus-specific threat
- Cross-trial Dirichlet learning. No explicit gate.
- Train on DOG (20 trials), probe on CAT (5 trials, learning frozen)
- H1: self-state + threat learn. H2: only threat learns.

**Results:**
- H1-highE: P(contact cat) ≈ 1.0 — TRANSFER (self revised)
- H2-highE: P(contact cat) ≈ 0.0 — NO TRANSFER (only dog threat revised)
- H1-lowE: P(contact cat) ≈ 0.0 — NO TRANSFER (self too rigid)
- D_threat_cat unchanged — transfer is through shared d_self, not leakage
- η_self=0 kills transfer — self learning is necessary

This is the paper's Move 3 claim made computational: identity-level revision transfers; threat-level revision stays local.

## Discussion points

1. **EFE vs bespoke scoring:** V2 now uses EFE for policy selection. More principled but harder to explain. V3 uses simpler policy (belief-based). Which should the paper use? The EFE decomposition gives us epistemic/pragmatic trajectories but adds complexity.

2. **Which simulations go in the paper?** My suggestion: V3 main figure (generalization) as the headline. V2 cascade heatmap and E_t sweep as mechanism support. V2 polarization as extension.

3. **The adversarial results should be disclosed.** V2 Test 4 failure + V3 fix shows intellectual honesty and sharpens the claim. A reviewer will trust this more than if we only showed the clean results.

4. **The v3 design is minimal (2 factors, 3 channels).** It could be a standalone short paper or the simulation section of the main paper. What's the right scope?

## Files

- `projects/ifs-paper/simulation-v3-spec.md` — full spec
- `projects/library/src/active_inference/ifs_model_v3.jl` — model
- `projects/ifs-paper/figures/v3/` — 4 figures
- `projects/ifs-paper/figures/v2/adversarial/RESULTS.md` — v2 adversarial tests
