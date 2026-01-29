# Handoff: IFS Active Inference Implementation

## Project Overview

This is a Julia implementation of Active Inference for exposure therapy modeling, specifically simulating spider phobia treatment. The project includes:

1. **Spider Phobia Model** - POMDP-based exposure therapy simulation
2. **Generic Active Inference Library** - Reusable Active Inference implementation
3. **T-maze Benchmark** - Standard epistemic behavior test
4. **Multiple Backend Support** - Custom, ActiveInference.jl, and RxInfer.jl implementations

---

## Installation

### Installing Julia

**Recommended: Using juliaup**
```bash
# Linux/macOS
curl -fsSL https://install.julialang.org | sh

# Or using wget
wget -qO- https://install.julialang.org | sh

# Windows (PowerShell)
winget install julia -s msstore
```

**Alternative: Direct download**
```bash
# Download from official website
# https://julialang.org/downloads/

# Linux x64 (example for v1.10.7)
wget https://julialang-s3.julialang.org/bin/linux/x64/1.10/julia-1.10.7-linux-x86_64.tar.gz
tar -xzf julia-1.10.7-linux-x86_64.tar.gz
sudo ln -sf $(pwd)/julia-1.10.7/bin/julia /usr/local/bin/julia
```

**Via Python (alternative)**
```bash
pip install juliacall
# Julia will be installed automatically on first use
```

**Network-restricted environments**: If external downloads are blocked, Julia must be pre-installed or provided as a pre-built binary.

### Project Setup

```bash
cd ifs-active-inference
julia --project=. -e 'using Pkg; Pkg.instantiate()'
```

This installs dependencies from `Project.toml`:
- `ActiveInference.jl` - Julia Active Inference library
- `RxInfer.jl` - Reactive message passing for probabilistic programming
- `Plots.jl` - Visualization

---

## Quick Start

### Run Spider Therapy Simulation
```bash
julia --project=. run.jl --trials=200 --exposure
```

### Run T-maze Benchmark
```bash
julia --project=. -e '
include("src/active_inference/ActiveInferenceCore.jl")
using .ActiveInferenceCore
results = run_tmaze_test(n_trials=10, verbose=true)
println("Cue check rate: $(results.cue_check_rate * 100)%")
'
```

### Run Implementation Comparison
```bash
julia --project=. compare_implementations.jl
```

---

## Current State

### What Works

| Component | Status | Notes |
|-----------|--------|-------|
| Spider model construction | Working | 3 state factors, 4 observation modalities |
| Custom Active Inference | Working | Gradual learning (+5% P(safe)) |
| ActiveInference.jl wrapper | Working | pA learning, sharp initial update |
| RxInfer.jl implementation | Working | Symmetric learning (+/-19%) |
| T-maze environment | Working | Environment runs correctly |
| Plotting utilities | Working | Generates comparison plots |

### Known Issue: State Information Gain in T-maze

**Symptom**: Agent goes directly to arms instead of checking cue first (0% cue-check rate).

**Root cause**: State information gain is identical (1.386) for all policies. The calculation doesn't properly distinguish between:
- Cue location: observation resolves which arm has reward (HIGH info gain)
- Arm locations: observation only confirms if choice was correct (LOW info gain)

**EFE breakdown**:
```
Policy 1 (go_cue -> go_left):   ambig=0, risk=-2.0, info=1.386 => G=-3.386
Policy 2 (go_cue -> go_right):  ambig=0, risk=-2.0, info=1.386 => G=-3.386
Policy 3 (go_left -> stay):     ambig=0, risk=-4.0, info=1.386 => G=-5.386
Policy 4 (go_right -> stay):    ambig=0, risk=-4.0, info=1.386 => G=-5.386
```

**Location in code**: `src/active_inference/efe.jl:197-234` (`compute_state_info_gain` function)

**Required fix**: Make state info gain policy-aware:
1. Predict state distribution: `q(s|pi,tau)`
2. Predict observation distribution: `q(o|pi,tau) = Sum_s A(o|s) q(s|pi,tau)`
3. For each observation, compute posterior: `q(s|o,pi,tau) ~ A(o|s) q(s|pi,tau)`
4. Info gain = `E_q(o)[D_KL[q(s|o,pi,tau) || q(s|pi,tau)]]`

The issue is that the posterior isn't accounting for the **location-dependent informativeness** of observations.

---

## Project Structure

```
ifs-active-inference/
|-- Project.toml              # Julia dependencies
|-- Manifest.toml             # Locked dependency versions
|-- run.jl                    # Main entry point
|-- compare_implementations.jl # Three-way comparison script
|
|-- src/
|   |-- IFSActiveInference.jl # Main module
|   |-- model.jl              # Spider model construction
|   |-- simulation.jl         # Custom Active Inference engine
|   |-- activeinference_impl.jl # ActiveInference.jl wrapper
|   |-- rxinfer_impl.jl       # RxInfer.jl implementation
|   |-- plotting.jl           # Visualization utilities
|   |
|   |-- active_inference/     # Generic Active Inference library
|       |-- ActiveInferenceCore.jl # Module file (~70 lines)
|       |-- core.jl           # Types: AIFSettings, PolicySet, AIFModel, AIFAgent (~400 lines)
|       |-- inference.jl      # State inference with VMP (~130 lines)
|       |-- efe.jl            # Expected Free Energy calculation (~220 lines)
|       |-- policy.jl         # Policy inference and action selection (~110 lines)
|       |-- learning.jl       # Dirichlet parameter learning (~200 lines)
|       |-- agent.jl          # Trial loop and environment interface (~150 lines)
|       |-- tmaze.jl          # T-maze benchmark (~600 lines)
|       |-- spider_model.jl   # Spider phobia using generic library (~265 lines)
|
|-- test/
|   |-- runtests.jl           # Main test runner
|   |-- test_rxinfer.jl       # RxInfer-specific tests (169 tests)
|
|-- results/                  # Output from simulations
|-- results_safe/             # Safe spider condition results
|-- results_dangerous/        # Dangerous spider condition results
```

---

## Implementation Comparison Results

| Aspect | Custom | ActiveInference.jl | RxInfer.jl |
|--------|--------|-------------------|------------|
| Learning target | d (state prior) | pA (observation model) | d (flattened state) |
| Safe spider learning | +5.4% | pA-based | +19.3% |
| Dangerous spider learning | -6.7% | pA-based | -19.3% |
| State representation | Factored (3) | Factored (3) | Flattened (24) |
| Interpretation | "Is spider dangerous?" | "What outcomes to expect?" | "What is true state?" |

---

## Key Functions

### Model Construction
```julia
build_model(; params=ModelParams())  # Spider model
create_tmaze_model(; ...)            # T-maze model
```

### Agent/Simulation
```julia
init_agent(model; settings)          # Initialize agent
run_trial(model, agent, true_state)  # Single trial
run_exposure_therapy(model; n_trials)# Full simulation
run_tmaze_test(n_trials; verbose)    # T-maze benchmark
```

### EFE Calculation
```julia
calculate_efe(agent, model, policy_idx, settings)
compute_state_info_gain(A_g, qs, qo, Ns)  # <- Issue is here
compute_ambiguity(A_g, qs, Ns)
```

---

## Next Steps

1. **Fix state info gain** - Make `compute_state_info_gain` in `efe.jl` location/policy-aware
2. **Reference comparison** - Compare against pymdp or SPM implementation
3. **Spider model P(safe) init** - Currently starts at 1.0 instead of 0.1
4. **Documentation** - Add docstrings to all public functions

---

## References

- Friston et al. (2017) "Active Inference: A Process Theory"
- Da Costa et al. (2020) "Active Inference on Discrete State-Spaces"
- [pymdp](https://github.com/infer-actively/pymdp) - Python implementation
- [ActiveInference.jl](https://github.com/ilabcode/ActiveInference.jl) - Julia library
- Original MATLAB code from Scientific Reports paper on computational psychiatry
