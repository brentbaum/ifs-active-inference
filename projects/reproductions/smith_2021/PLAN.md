# Smith 2021 Paper Reproduction Plan

Paper: Smith et al. (2021) "Simulating the computational mechanisms of cognitive and behavioral psychotherapeutic interventions: Insights from active inference"
https://www.nature.com/articles/s41598-021-89047-0

Reference implementation: https://github.com/rssmith33/Simulating_Cognitive_Behavioral_Therapy

## Status
- [x] Extract task specification into local markdown (`task_spec.md`).
- [x] Map paper model to current library primitives and list capability gaps.
- [x] Design the generative model (A/B/C/D matrices, outcome modalities, policies).
- [x] Implement spider phobia environment and exposure therapy simulation.
- [x] Implement therapist-guided exposure mode (forced approach policy).
- [x] Reproduce learning curves (P(safe) evolution over trials).
- [x] Add tests validating expected behavior.
- [x] Document parameters, assumptions, and deviations.

## Notes
- Model simulates CBT exposure therapy for spider phobia.
- Key mechanism: agent learns that spider is safe through repeated exposure.
- Exposure mode forces approach actions, simulating therapist guidance.
- Learning is on D matrix (prior beliefs about danger state).
- Implementation complete in `src/active_inference/spider_model.jl`.
- Tests in `test/test_concepts_model.jl` (spider model tests included).
