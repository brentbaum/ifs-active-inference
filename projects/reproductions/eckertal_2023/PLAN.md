# Eckertal 2023 Paper Reproduction Plan

Paper: Eckertal et al. (2023) "Simulating Active Inference of Interpersonal Context Within and Across Mental Disorders"
*Scientific Reports*, 2023

Reference implementation: https://github.com/Eckertal/pymdp_depression (branch: sims)

## Status
- [x] Extract task specification into local markdown (`task_spec.md`).
- [x] Map paper model to current library primitives and list capability gaps.
- [x] Design the generative model (A/B/C/D matrices, outcome modalities, policies).
- [x] Implement trust game environment and simulation.
- [x] Implement paper-matching clinical profiles (healthy, depressed, anxious, etc.).
- [x] Implement paper-specific B transition matrices (depressed, insecure, defeated, static).
- [x] Implement multi-phase simulations with context switching.
- [x] Reproduce Figure 2A and 2B belief dynamics.
- [x] Add tests validating expected behavior.
- [x] Document parameters, assumptions, and deviations.

## Notes
- Model simulates trust game (investor/trustee) paradigm.
- Different agent profiles represent transdiagnostic biases in mental disorders.
- Key mechanisms: observation uncertainty, loss aversion, pessimism, fatalism.
- Implementation complete in `src/active_inference/trust_game.jl`.
- Figure comparison script: `scripts/paper_figure_comparison.jl`.
- Tests in `test/test_trust_game.jl`.
- Figures in `figures/trust_game/`.
