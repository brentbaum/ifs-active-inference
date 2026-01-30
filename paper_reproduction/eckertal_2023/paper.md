# Paper Reference (Eckertal et al. 2023)

## Citation
Eckertal, K., et al. (2023). "Simulating Active Inference of Interpersonal Context Within and Across Mental Disorders." *Scientific Reports*.

## Links
- **Paper**: [Scientific Reports 2023]
- **Reference code**: https://github.com/Eckertal/pymdp_depression (branch: sims)
  - `gms.py`: Generative model structure
  - `library.py`: Agent profile definitions

## Abstract Summary
The paper uses active inference to model how different mental disorders affect interpersonal decision-making in a trust game paradigm. It demonstrates that:
1. Different transdiagnostic biases (uncertainty, fatalism, loss aversion, pessimism) lead to distinct behavioral patterns.
2. These biases can be formalized as differences in generative model parameters.
3. The model reproduces key features of social cognition deficits in depression, anxiety, and personality disorders.

## Key Contributions
1. Formal computational model of interpersonal inference.
2. Mapping transdiagnostic biases to generative model parameters.
3. Multiple clinical profiles (depressed, anxious, insecure, borderline).
4. Demonstration of belief dynamics in response to partner behavior changes.

## Trust Game Paradigm
- Investor (agent) decides to share or keep resources.
- Trustee (partner) can return cooperation or exploit.
- Agent must infer partner's hidden disposition (friendly/hostile/neutral).
- Different profiles have different biases affecting inference and decisions.

## Transdiagnostic Biases

| Bias | Parameter | Clinical Relevance |
|------|-----------|-------------------|
| Uncertainty | biased A | Can't distinguish friendly from hostile cues |
| Fatalism | biased B, no B learning | Actions don't change outcomes |
| Loss Aversion | biased C | Negative outcomes weigh more heavily |
| Pessimism | biased D | Prior belief others are hostile |

## Key Results Reproduced

### Figure 2A: Friendly -> Hostile
- Healthy agent starts believing context is friendly.
- After switch to hostile partner, beliefs shift dramatically.
- P(friendly) drops from ~0.9 to ~0.1.

### Figure 2B: Hostile -> Friendly
- Opposite pattern: beliefs shift from hostile to friendly.
- Demonstrates context-dependent belief updating.

### Profile Comparisons
- Depressed agents update beliefs more slowly (fatalism).
- Anxious agents have higher uncertainty in observations.
- All profiles show distinct behavioral signatures.

## Implementation Files
- Main model: `src/active_inference/trust_game.jl`
- Figure script: `scripts/paper_figure_comparison.jl`
- Tests: `test/test_trust_game.jl`
- Figures: `figures/trust_game/`
  - `paper_figure_comparison.png`
  - `trust_game_figure2A_style.png`
  - `trust_game_figure2B_style.png`

## Deviations from Paper
- We plot both qs (posterior) and pD (prior) for comparison.
- Exact B matrix values may have minor differences from pymdp.
- Some additional profiles (simplified versions) for experimentation.
- Learning rate tuning for stable dynamics.
