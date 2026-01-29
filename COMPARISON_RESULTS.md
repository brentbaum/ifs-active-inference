# Implementation Comparison: Custom vs ActiveInference.jl vs RxInfer.jl

## Summary

All three implementations successfully demonstrate exposure therapy learning dynamics, but through different mechanisms and with varying learning rates.

## Custom Implementation

**Learning mechanism**: Direct Dirichlet parameter updates to `d` (initial state prior)

**Results (200 trials):**
- Safe spider: P(safe) 11.5% → 16.9% (+5.4%)
- Dangerous spider: P(safe) 9.7% → 3.0% (-6.7%)

**Characteristics:**
- Gradual belief accumulation across trials
- Directly updates belief about danger state
- More interpretable as "changing one's mind about danger"
- Conservative learning rate

## ActiveInference.jl Implementation

**Learning mechanism**: Dirichlet parameter updates to `pA` (observation likelihood)

**Results (200 trials):**
- pD-based P(safe): Jumps from 10% → 55% at trial 1, then plateaus
- pA learning shows clear safe/dangerous distinction:
  - Safe spider: Behavior 4 → 99.4% neutral affect
  - Dangerous spider: Behavior 4 → 93.1% negative affect

**Characteristics:**
- One-shot belief update for initial state (pD)
- Continuous learning of observation likelihoods (pA)
- Learns "what outcomes to expect" rather than "what the danger state is"
- More aligned with perceptual learning literature

## RxInfer.jl Implementation

**Learning mechanism**: Manual Bayesian inference with Dirichlet updates on flattened state space

**Results (200 trials):**
- Safe spider: P(safe) 50.5% → 69.8% (+19.3%)
- Dangerous spider: P(safe) 49.5% → 30.2% (-19.3%)

**Characteristics:**
- Uses flattened 24-state representation (behavior × spider × danger)
- Forward filtering with Bayesian updates
- Uses average belief across timesteps for learning signal
- Symmetric learning rates demonstrate appropriate sensitivity to ground truth
- Correctly differentiates safe vs dangerous conditions
- Uses manual inference (RxInfer's @model macro has scoping issues in modules)

## Key Differences

| Aspect | Custom | ActiveInference.jl | RxInfer.jl |
|--------|--------|-------------------|------------|
| Learning target | d (state prior) | pA (observation model) | d (flattened state) |
| Learning dynamics | Gradual (+5%) | Sharp initial, then pA | Moderate (+19%) |
| What's learned | "Is spider dangerous?" | "What happens when I encounter danger?" | "What is the true state?" |
| State representation | Factored (3 factors) | Factored (3 factors) | Flattened (24 states) |
| Inference method | Custom variational | ActiveInference.jl VMP | Manual Bayesian filtering |

## Interpretation

1. **Custom Implementation**: Models belief updating about the danger itself, matching the paper's intended P(safe) metric. Conservative learning suitable for therapeutic contexts.

2. **ActiveInference.jl**: Models learning the consequences of danger through observation model updates. The P(safe) metric doesn't capture this type of learning well.

3. **RxInfer.jl**: Shows moderate belief updating with symmetric learning. Uses average filtered belief across timesteps to accumulate evidence, providing a balanced approach between the conservative custom implementation and aggressive pure Bayesian updates.

## Conclusion

All implementations capture meaningful aspects of exposure therapy learning:
- **Custom**: Conservative belief updating about danger (closest to paper's intended behavior)
- **ActiveInference.jl**: Perceptual learning about outcomes
- **RxInfer.jl**: Moderate Bayesian belief revision with symmetric learning

The choice of implementation depends on the modeling goal:
- For replicating the paper's P(safe) dynamics: Custom implementation
- For sophisticated observation model learning: ActiveInference.jl
- For balanced belief updating with full inference: RxInfer.jl

## Files

- `src/simulation.jl`: Custom active inference implementation
- `src/activeinference_impl.jl`: ActiveInference.jl wrapper
- `src/rxinfer_impl.jl`: RxInfer.jl implementation
- `test/test_rxinfer.jl`: RxInfer-specific unit tests (169 tests)
- `compare_implementations.jl`: Three-way comparison script
- `comparison_safe.png`, `comparison_dangerous.png`: Result plots
