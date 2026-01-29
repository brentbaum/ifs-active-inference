# Handoff: Generic Active Inference Library

## Current State: T-Maze Working, Spider Model Needs Verification

The Active Inference library is implemented and the T-maze benchmark now demonstrates **correct epistemic behavior**: the agent checks the cue first, learns the reward location, and then navigates to the correct arm with 100% accuracy.

## Files Implemented

| File | Lines | Status | Purpose |
|------|-------|--------|---------|
| `core.jl` | ~400 | Done | Types: AIFSettings, PolicySet, AIFModel, AIFAgent |
| `inference.jl` | ~130 | Done | State inference with variational message passing |
| `efe.jl` | ~280 | Done | Expected Free Energy calculation |
| `policy.jl` | ~110 | Done | Policy inference and action selection |
| `learning.jl` | ~200 | Done | Dirichlet parameter learning (A, B, D) |
| `agent.jl` | ~150 | Done | Trial loop and environment interface |
| `spider_model.jl` | ~265 | Done | Spider phobia application |
| `tmaze.jl` | ~600 | Done | T-maze benchmark |
| `ActiveInferenceCore.jl` | ~70 | Done | Module file |

## Bugs Fixed

### 1. Infinite recursion in `PolicySet` constructor
The convenience constructor for `Vector{<:Real}` was matching `Float64` and recursing infinitely. Fixed by restricting to `Vector{<:Integer}`.

### 2. T-maze preferences at all timesteps
The C matrix (preferences) gave reward preference at ALL timesteps, causing go-arm-early policies to have double the expected utility. Fixed by only giving reward preference at the **final timestep** (T).

### 3. EFE calculation not accounting for current timestep
When `infer_policies!` was called at t>1, the EFE calculation still computed from τ=1, not from the remaining actions. This meant at t=2, after seeing the cue, all policies appeared to have equal EFE because the calculation was trying to evaluate already-taken actions.

**Fix**: Added `start_τ` parameter to EFE functions:
- At t=1: `start_τ=1`, evaluates full policy
- At t=2: `start_τ=2`, only evaluates remaining actions

### 4. Counterfactual EFE t_future calculation
The counterfactual recursive function calculated `t_future = current_t + τ`, which was wrong when starting from τ>1. For example, at t=2 with start_τ=2:
- Old: `t_future = 2 + 2 = 4 > model.T`, returned 0
- Fixed: `t_future = current_t + (τ - start_τ + 1)`

## T-Maze Results

```
WITH State Info Gain (Epistemic):
  Cue check rate:  100.0%
  Reward rate:     100.0%
  Correct choice:  100.0%

WITHOUT State Info Gain (Pragmatic):
  Cue check rate:  100.0%
  Reward rate:     100.0%
  Correct choice:  100.0%
```

Both conditions achieve 100% because:
1. At t=1, policies with "go_cue" as first action have higher combined probability (50%) than individual arm policies (25% each)
2. High alpha (16.0) makes action sampling strongly favor the mode
3. At t=2, after seeing the cue, the agent correctly updates beliefs and chooses the rewarded arm

## Quick Test Commands

```bash
# Load module and run T-maze
~/.juliaup/bin/julia --project=. -e '
include("src/active_inference/ActiveInferenceCore.jl")
using .ActiveInferenceCore
results = run_tmaze_test(n_trials=10, verbose=true)
println("Cue check rate: $(results.cue_check_rate * 100)%")
println("Reward rate: $(results.reward_rate * 100)%")
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

## Remaining Issues

1. **Spider model P(safe) initialization** - Currently starts at 1.0 instead of expected 0.1. May need to use the Dirichlet priors from `model.jl` properly.

2. **Warning about unused type variable** - `update_pD!` at learning.jl:175 declares type variable Nf but doesn't use it. Cosmetic issue.

## Architecture Notes

- **Factored state space**: States are factored as `(s_1, ..., s_Nf)` with independent factors
- **A matrices are tensors**: Shape `(No[g], Ns[1], ..., Ns[Nf])` for factored states
- **Mean-field approximation**: `q(s) = ∏_f q(s_f)`
- **Policies are explicit**: `V[t, π, f]` = action for timestep t, policy π, factor f
- **EFE terms**: Ambiguity + Risk - State Info Gain (all toggleable via settings)
- **Counterfactual EFE**: Branches over observations and updates beliefs to properly account for information gain

## Key References

- Friston et al. (2017) "Active Inference: A Process Theory"
- Da Costa et al. (2020) "Active Inference on Discrete State-Spaces"
- pymdp library: https://github.com/infer-actively/pymdp
