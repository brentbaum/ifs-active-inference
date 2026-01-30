# Paper Reference (Smith et al. 2021)

## Citation
Smith, R., et al. (2021). "Simulating the computational mechanisms of cognitive and behavioral psychotherapeutic interventions: Insights from active inference." *Scientific Reports*, 11, 8145.

## Links
- **Paper**: https://www.nature.com/articles/s41598-021-89047-0
- **Reference code**: https://github.com/rssmith33/Simulating_Cognitive_Behavioral_Therapy
- **DOI**: 10.1038/s41598-021-89047-0

## Abstract Summary
The paper uses active inference to simulate how cognitive behavioral therapy (CBT) interventions work computationally. It models:
1. **Exposure therapy**: Reducing fear through repeated safe exposure.
2. **Cognitive restructuring**: Updating beliefs about danger.
3. **Behavioral activation**: Encouraging approach behaviors.

## Key Contributions
1. Formal computational model of CBT mechanisms.
2. Demonstrates why exposure therapy requires guided approach (not just presence).
3. Shows how prior beliefs about danger affect learning.
4. Provides quantitative predictions for therapy outcomes.

## Model Overview
- Agent has hidden states: behavior, spider presence, danger.
- Agent infers danger state from observations (harm/neutral outcomes).
- Strong prior belief that spider is dangerous (~90%).
- Through exposure, agent updates beliefs based on evidence.

## Key Results Reproduced
- Initial P(safe) ~ 10% (matching paper's d[3] = [45, 5]).
- After 200 exposure trials with safe spider: P(safe) ~ 81-90%.
- Learning requires approach (avoidance provides no evidence).

## Implementation Files
- Main model: `src/active_inference/spider_model.jl`
- Tests: `test/test_concepts_model.jl` (includes spider model tests)
- Figures: `figures/spider_*.png`

## Deviations from Paper
- A matrix learning disabled (improves convergence, see learnings.md).
- Exact hyperparameters may differ slightly from reference code.
- Single spider type (vs. paper's multiple phobia types).
