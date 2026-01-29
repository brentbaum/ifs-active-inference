# Handoff: Generic Active Inference Library

## Current State: Functional but Epistemic Behavior Not Working

The Active Inference library is implemented and runs without crashes. However, the T-maze benchmark reveals that **state information gain is not driving epistemic behavior** as expected.

## Project Overview

This project implements:
1. **Generic Active Inference Library** (`src/active_inference/`) - Reusable AIF framework
2. **Spider Phobia Model** - Exposure therapy simulation (original goal)
3. **T-Maze Benchmark** - Classic epistemic behavior test (verification)
4. **Multiple implementations** - Custom, ActiveInference.jl, and RxInfer.jl wrappers

## Files Implemented

### Core Active Inference Library (`src/active_inference/`)

| File | Lines | Status | Purpose |
|------|-------|--------|---------|
| `core.jl` | ~400 | Done | Types: AIFSettings, PolicySet, AIFModel, AIFAgent |
| `inference.jl` | ~130 | Done | State inference with variational message passing |
| `efe.jl` | ~220 | **Bug** | Expected Free Energy calculation - state info gain broken |
| `policy.jl` | ~110 | Done | Policy inference and action selection |
| `learning.jl` | ~200 | Done | Dirichlet parameter learning (A, B, D) |
| `agent.jl` | ~150 | Done | Trial loop and environment interface |
| `spider_model.jl` | ~265 | Done | Spider phobia application |
| `tmaze.jl` | ~600 | Done | T-maze benchmark |
| `ActiveInferenceCore.jl` | ~70 | Done | Module file |

### Other Implementations (`src/`)

| File | Purpose |
|------|---------|
| `simulation.jl` | Original custom AIF implementation |
| `activeinference_impl.jl` | ActiveInference.jl wrapper |
| `rxinfer_impl.jl` | RxInfer.jl implementation |
| `model.jl` | Spider phobia model construction |
| `plotting.jl` | Visualization utilities |

## Bug Fixed

**Infinite recursion in `PolicySet` constructor** - The convenience constructor for `Vector{<:Real}` was matching `Float64` and recursing infinitely. Fixed by restricting to `Vector{<:Integer}`.

---

## CRITICAL ISSUE: State Information Gain Not Working

### Symptom
In T-maze, the agent should check the cue first (epistemic action) before going to an arm. Instead, **it goes directly to an arm 100% of the time**.

### Diagnosis
EFE breakdown for T-maze policies (from debugging):

```
Policy 1 (go_cue -> go_left):   ambig=0, risk=-2.0, info=1.386 => G=-3.386
Policy 2 (go_cue -> go_right):  ambig=0, risk=-2.0, info=1.386 => G=-3.386
Policy 3 (go_left -> stay):     ambig=0, risk=-4.0, info=1.386 => G=-5.386
Policy 4 (go_right -> stay):    ambig=0, risk=-4.0, info=1.386 => G=-5.386
```

**Problem**: State info gain is **identical (1.386) for all policies**, but it should be:
- **HIGHER** for cue-checking policies (observing cue resolves uncertainty about reward location)
- **LOWER** for direct-arm policies (reward observation doesn't reduce uncertainty, just confirms/denies success)

### Root Cause Analysis

The bug is in `src/active_inference/efe.jl:197-233` in `compute_state_info_gain()`.

**The function computes information gain correctly for a given state distribution, but the problem is that all policies produce the same predicted observation entropy because:**

1. The function receives `qo` (predicted observation distribution) which is already marginalized
2. At timestep 1, all policies start from the same initial belief (uniform over reward location)
3. The predicted observation distribution `qo` doesn't differ enough between policies because the forward simulation (`forward_simulate`) only propagates beliefs through B matrices, not through the observation model

**The fundamental issue**: The current implementation computes `E[D_KL[q(s|o) || q(s)]]` but uses the **prior** `q(s)` for all policies rather than the **policy-specific predicted** `q(s|π)`. This means all policies have identical information gain.

### Where the Bug Is (Code Location)

**File**: `src/active_inference/efe.jl`

**Function**: `compute_state_info_gain()` (lines 197-233)

**The Issue in Detail**:
```julia
# Line 216: This computes posterior given obs correctly...
qs_given_o = compute_posterior_given_obs(A_g, o, qs, Ns)

# But the KL divergence (lines 218-230) compares against qs which
# is the same for all policies at the same predicted location
# because the A matrix gives identical observation distributions
# when the underlying state is the same.
```

**The Real Problem**: At timestep τ=1 in the T-maze:
- Policy 1 & 2: Agent goes to CUE location → state is (LOC_CUE, ?)
- Policy 3 & 4: Agent goes to ARM location → state is (LOC_ARM, ?)

But the cue observation modality (A[2]) has **different informativeness** depending on location:
- At LOC_CUE: Observation REVEALS reward location (high info gain)
- At LOC_ARM: Observation is always NULL (zero info gain for cue modality)

The current code **doesn't capture this** because `compute_predicted_obs` produces identical observation distributions when the predicted location distributions are similar.

### Debugging Commands

```bash
# Run T-maze with verbose EFE debugging
~/.juliaup/bin/julia --project=. -e '
include("src/active_inference/ActiveInferenceCore.jl")
using .ActiveInferenceCore

model = build_tmaze_model()
agent = init_agent(model)
settings = AIFSettings(gamma=16.0, alpha=16.0, use_states_info_gain=true)

# Debug: Print EFE breakdown for each policy
for pi in 1:4
    G = calculate_efe(agent, model, pi, settings)
    println("Policy $pi: G = $G")
end
'
```

### Recommended Fix Strategy

**Option 1: Fix the information gain per modality per location**

The state info gain should be computed **per observation modality** and should account for whether that modality is informative at the predicted location.

For the cue modality (A[2]):
- At cue location: observation entropy is high, posterior entropy is low → HIGH info gain
- Elsewhere: observation entropy is zero (deterministic NULL) → ZERO info gain

**Option 2: Reference pymdp implementation**

Look at how pymdp computes `calc_states_info_gain()`:
- https://github.com/infer-actively/pymdp/blob/master/pymdp/maths.py

The key insight from pymdp is that they compute info gain using:
```python
# H[Q(s)] - E_Q(o)[H[Q(s|o)]]
# = prior entropy - expected posterior entropy
```

Rather than computing KL divergences, they use the **entropy reduction** formulation.

### Expected Correct Behavior

With proper state info gain:
- Cue-checking policies (1, 2) should have **higher** state info gain (~1.0 for cue modality)
- Direct-arm policies (3, 4) should have **lower** state info gain (~0.0 for cue modality)
- This should make cue-checking policies preferred (lower EFE because `-info_gain` term)

---

## Quick Test Commands

```bash
# Load module and run T-maze
~/.juliaup/bin/julia --project=. -e '
include("src/active_inference/ActiveInferenceCore.jl")
using .ActiveInferenceCore
results = run_tmaze_test(n_trials=10, verbose=true)
println("Cue check rate: $(results.cue_check_rate * 100)%")
'

# Run T-maze comparison (with/without info gain)
~/.juliaup/bin/julia --project=. -e '
include("src/active_inference/ActiveInferenceCore.jl")
using .ActiveInferenceCore
run_tmaze_comparison(n_trials=20)
'

# Run spider model
~/.juliaup/bin/julia --project=. -e '
include("src/active_inference/ActiveInferenceCore.jl")
using .ActiveInferenceCore
include("src/model.jl")
results = run_spider_aif_therapy(n_trials=20, spider_dangerous=false)
println("Final P(safe): $(results[end].p_safe)")
'

# Compare all three implementations (custom, ActiveInference.jl, RxInfer.jl)
~/.juliaup/bin/julia --project=. compare_implementations.jl
```

---

## Next Steps (Priority Order)

### 1. Fix State Information Gain (Critical)
**File**: `src/active_inference/efe.jl`
**Function**: `compute_state_info_gain()`

Options:
- A) Implement entropy-based formulation: `H[q(s)] - E_q(o)[H[q(s|o)]]`
- B) Fix the KL-based formulation to use policy-specific predicted states
- C) Port the pymdp implementation directly

### 2. Verify with T-Maze Benchmark
After fixing, run:
```bash
~/.juliaup/bin/julia --project=. -e '
include("src/active_inference/ActiveInferenceCore.jl")
using .ActiveInferenceCore
results = run_tmaze_comparison(n_trials=100)
# Expected: cue_check_rate > 80% WITH info gain
#           cue_check_rate ~ 50% WITHOUT info gain
'
```

### 3. Fix Spider Model P(safe) Initialization
Currently starts at 1.0 instead of expected 0.1. The Dirichlet priors from `model.jl` may need to be passed correctly to `init_agent()`.

### 4. Documentation and Tests
- Add unit tests for EFE components
- Document the fix for future reference

---

## Architecture Notes

### State Space
- **Factored state space**: States are factored as `(s_1, ..., s_Nf)` with independent factors
- **Mean-field approximation**: `q(s) = ∏_f q(s_f)`

### Generative Model
- **A matrices are tensors**: Shape `(No[g], Ns[1], ..., Ns[Nf])` for factored states
- **B matrices are 3D**: Shape `(Ns[f], Ns[f], Na[f])` per factor
- **C matrices are preferences**: Shape `(No[g], T)` as log preferences
- **D vectors are initial priors**: Shape `(Ns[f],)` per factor

### Policies
- **Policies are explicit**: `V[t, π, f]` = action for timestep t, policy π, factor f
- **Policy posterior**: `Q(π) ∝ P(π) exp(-γ G(π))`

### EFE Terms
```
G(π) = Σ_τ [Ambiguity + Risk - State_Info_Gain]

Ambiguity = E_q(s)[H[P(o|s)]]           # Expected obs entropy given beliefs
Risk = E_q(o)[-C(o)]                     # Negative expected preference
State_Info_Gain = E_q(o)[D_KL[q(s|o) || q(s)]]  # Expected belief update
```

All terms are toggleable via `AIFSettings` flags.

---

## Implementation Comparison Summary

From `COMPARISON_RESULTS.md`:

| Aspect | Custom | ActiveInference.jl | RxInfer.jl |
|--------|--------|-------------------|------------|
| Learning target | d (state prior) | pA (observation model) | d (flattened state) |
| Learning dynamics | Gradual (+5%) | Sharp initial, then pA | Moderate (+19%) |
| What's learned | "Is spider dangerous?" | "What happens when I encounter danger?" | "What is the true state?" |

---

## Key References

- Friston et al. (2017) "Active Inference: A Process Theory"
- Da Costa et al. (2020) "Active Inference on Discrete State-Spaces"
- pymdp library: https://github.com/infer-actively/pymdp
- pymdp state info gain: https://github.com/infer-actively/pymdp/blob/master/pymdp/maths.py

---

## File Tree

```
ifs-active-inference/
├── src/
│   ├── active_inference/          # Generic AIF library
│   │   ├── ActiveInferenceCore.jl # Module file
│   │   ├── core.jl                # Types and validation
│   │   ├── inference.jl           # State inference (VMP)
│   │   ├── efe.jl                 # EFE calculation (BUG HERE)
│   │   ├── policy.jl              # Policy inference
│   │   ├── learning.jl            # Dirichlet learning
│   │   ├── agent.jl               # Trial loop
│   │   ├── spider_model.jl        # Spider phobia env
│   │   └── tmaze.jl               # T-maze benchmark
│   ├── IFSActiveInference.jl      # Main module
│   ├── model.jl                   # Spider model construction
│   ├── simulation.jl              # Original custom impl
│   ├── activeinference_impl.jl    # ActiveInference.jl wrapper
│   ├── rxinfer_impl.jl            # RxInfer.jl impl
│   └── plotting.jl                # Visualization
├── test/
│   └── runtests.jl
├── HANDOFF.md                     # This file
├── PLAN_v2.md                     # Implementation plan
├── COMPARISON_RESULTS.md          # Three-way comparison
├── README.md                      # User documentation
└── spec.md                        # Original specification
```
