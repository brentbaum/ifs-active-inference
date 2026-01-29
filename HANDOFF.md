# Handoff: Generic Active Inference Library

## Current State: Functional but Epistemic Behavior Not Working

The Active Inference library is implemented and runs without crashes. However, the T-maze benchmark reveals that **state information gain is not driving epistemic behavior** as expected.

## Files Implemented

| File | Lines | Status | Purpose |
|------|-------|--------|---------|
| `core.jl` | ~400 | Done | Types: AIFSettings, PolicySet, AIFModel, AIFAgent |
| `inference.jl` | ~130 | Done | State inference with variational message passing |
| `efe.jl` | ~220 | Done | Expected Free Energy calculation |
| `policy.jl` | ~110 | Done | Policy inference and action selection |
| `learning.jl` | ~200 | Done | Dirichlet parameter learning (A, B, D) |
| `agent.jl` | ~150 | Done | Trial loop and environment interface |
| `spider_model.jl` | ~265 | Done | Spider phobia application |
| `tmaze.jl` | ~600 | Done | T-maze benchmark |
| `ActiveInferenceCore.jl` | ~70 | Done | Module file |

## Bug Fixed

**Infinite recursion in `PolicySet` constructor** - The convenience constructor for `Vector{<:Real}` was matching `Float64` and recursing infinitely. Fixed by restricting to `Vector{<:Integer}`.

## Current Issue: State Info Gain Not Working

### Symptom
In T-maze, the agent should check the cue first (epistemic action) before going to an arm. Instead, it goes directly to an arm 100% of the time.

### Diagnosis
EFE breakdown for T-maze policies:

```
Policy 1 (go_cue -> go_left):   ambig=0, risk=-2.0, info=1.386 => G=-3.386
Policy 2 (go_cue -> go_right):  ambig=0, risk=-2.0, info=1.386 => G=-3.386
Policy 3 (go_left -> stay):     ambig=0, risk=-4.0, info=1.386 => G=-5.386
Policy 4 (go_right -> stay):    ambig=0, risk=-4.0, info=1.386 => G=-5.386
```

**Problem**: State info gain is **identical (1.386) for all policies**, but it should be HIGHER for cue-checking policies because observing the cue resolves uncertainty about which arm has the reward.

### Root Cause Hypothesis
The `compute_state_info_gain` function computes info gain based on the **current predicted observation distribution**, but doesn't account for how different policies lead to observations that are **more or less informative about hidden states**.

In the T-maze:
- At cue location: cue observation reveals reward location (HIGH info gain)
- At arm: reward observation only confirms if you chose correctly (LOW info gain about hidden state)

The current implementation computes the same info gain because it doesn't properly simulate the **counterfactual** - what you would observe under each policy and how informative those observations would be.

### Recommended Fix
The state info gain calculation needs to be policy-aware. For each timestep in a policy:
1. Predict the state distribution: `q(s|π,τ)`
2. Predict the observation distribution: `q(o|π,τ) = Σ_s A(o|s) q(s|π,τ)`
3. For each possible observation, compute the posterior: `q(s|o,π,τ) ∝ A(o|s) q(s|π,τ)`
4. Info gain = `E_q(o)[D_KL[q(s|o,π,τ) || q(s|π,τ)]]`

The issue is likely in step 3 - the posterior computation isn't properly accounting for the **information content** of the observation at different locations.

## Quick Test Commands

```bash
# Load module and run T-maze
~/.juliaup/bin/julia --project=. -e '
include("src/active_inference/ActiveInferenceCore.jl")
using .ActiveInferenceCore
results = run_tmaze_test(n_trials=10, verbose=true)
println("Cue check rate: $(results.cue_check_rate * 100)%")
'

# Run spider model
~/.juliaup/bin/julia --project=. -e '
include("src/active_inference/ActiveInferenceCore.jl")
using .ActiveInferenceCore
include("src/model.jl")
p_safe = run_spider_aif_therapy(n_trials=20, spider_dangerous=false)
println("Final P(safe): $(p_safe[end])")
'
```

## Next Steps

1. **Debug state info gain** - The key function is `compute_state_info_gain` in `efe.jl`. It needs to properly compute the expected information gain about hidden states from observations at different locations.

2. **Reference implementation** - Compare against pymdp or SPM implementation of epistemic value / state info gain.

3. **Spider model P(safe) initialization** - Currently starts at 1.0 instead of expected 0.1. May need to use the Dirichlet priors from `model.jl` properly.

## Architecture Notes

- **Factored state space**: States are factored as `(s_1, ..., s_Nf)` with independent factors
- **A matrices are tensors**: Shape `(No[g], Ns[1], ..., Ns[Nf])` for factored states
- **Mean-field approximation**: `q(s) = ∏_f q(s_f)`
- **Policies are explicit**: `V[t, π, f]` = action for timestep t, policy π, factor f
- **EFE terms**: Ambiguity + Risk - State Info Gain (all toggleable via settings)

## Key References

- Friston et al. (2017) "Active Inference: A Process Theory"
- Da Costa et al. (2020) "Active Inference on Discrete State-Spaces"
- pymdp library: https://github.com/infer-actively/pymdp
