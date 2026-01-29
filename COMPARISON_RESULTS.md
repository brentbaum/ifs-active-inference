# Implementation Comparison: Custom vs ActiveInference.jl

## Summary

Both implementations successfully learn from exposure therapy, but through different mechanisms.

## Custom Implementation

**Learning mechanism**: Direct Dirichlet parameter updates to `d` (initial state prior)

**Results (200 trials):**
- Safe spider: P(safe) 11.5% → 16.9% (+5.4%)
- Dangerous spider: P(safe) 9.7% → 3.0% (-6.7%)

**Characteristics:**
- Gradual belief accumulation across trials
- Directly updates belief about danger state
- More interpretable as "changing one's mind about danger"

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

## Key Differences

| Aspect | Custom | ActiveInference.jl |
|--------|--------|-------------------|
| Learning target | d (state prior) | pA (observation model) |
| Learning dynamics | Gradual accumulation | Sharp initial update, then pA refinement |
| What's learned | "Is spider dangerous?" | "What happens when I encounter danger?" |
| Approach behavior | Forced (exposure mode) | Forced (for comparison) |

## Conclusion

Both implementations capture meaningful aspects of exposure therapy learning:
- **Custom**: Models belief updating about the danger itself
- **ActiveInference.jl**: Models learning the consequences of danger

The paper's MATLAB implementation uses SPM's sophisticated variational message passing, which may combine both types of learning more naturally. Our custom implementation is closer to the paper's intended behavior for the P(safe) metric.

## Files

- `src/simulation.jl`: Custom active inference implementation
- `src/activeinference_impl.jl`: ActiveInference.jl wrapper
- `compare_implementations.jl`: Comparison script
- `comparison_safe.png`, `comparison_dangerous.png`: Result plots
