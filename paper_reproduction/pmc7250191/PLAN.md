# PMC7250191 Paper Reproduction Plan

Paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC7250191/

## Status
- [x] Extract task specification into a local markdown (`task_spec.md`).
- [x] Map paper model to current library primitives and list capability gaps.
 - [x] Design the generative model (A/B/C/D, outcome modalities, policies, phases).
- [ ] Implement learning vs. reporting phases and reproduction scripts.
- [ ] Implement concept expansion (unused slots) and validate learning curves.
- [ ] Implement Bayesian model reduction (BMR) for D (and optionally A).
- [ ] Reproduce figures/metrics and add tests/plots.
- [ ] Document parameters, assumptions, and deviations.

## Notes
- No neural process simulation required.
- BMR appears to be the primary library‑level gap.
- Supplementary code retrieved: `paper_reproduction/pmc7250191/data/Concepts_model.m` (parameters extracted into `task_spec.md`).
