# IFS Active Inference - Spider Phobia Exposure Therapy Model

A Julia implementation of the active inference model for CBT exposure therapy, based on the MATLAB code from the Scientific Reports paper on computational models of phobia treatment.

## Overview

This package implements a Partially Observable Markov Decision Process (POMDP) active inference model that simulates:

1. **Spider phobia** with initial beliefs that spiders are dangerous
2. **Exposure therapy** where repeated safe interactions update beliefs
3. **Belief learning** through Dirichlet-categorical updates

### Model Structure

- **3 Hidden State Factors**:
  1. Behavioral state (start/stim/approach/interact/avoid/safety+cost)
  2. Spider presence (absent/present)
  3. Spider dangerousness (dangerous/safe)

- **4 Observation Modalities**:
  1. Visual (see spider or not)
  2. Arousal (low/high)
  3. Affective consequences (neutral/negative/harm)
  4. Behavioral (current action state)

- **2 Policies**: Approach vs Avoid

## Installation

### Prerequisites

Install Julia (1.6 or later):
```bash
# Using juliaup (recommended)
curl -fsSL https://install.julialang.org | sh

# Or download from https://julialang.org/downloads/
```

### Setup

```bash
cd ifs-active-inference
julia --project=.
```

In the Julia REPL:
```julia
using Pkg
Pkg.instantiate()

# Optional: Install Plots for visualization
Pkg.add("Plots")
```

## Quick Start

### Run the simulation

```bash
julia --project=. run.jl
```

Or with options:
```bash
julia --project=. run.jl --trials=200 --exposure
```

### Use as a library

```julia
using IFSActiveInference

# Build the model with custom parameters
params = ModelParams(
    CABi = 0.9,      # Cognitive-affective belief interaction
    Psafe = 0.1,     # Prior probability spider is safe
    N = 200,         # Number of trials
    T = 4            # Time steps per trial
)
model = build_model(params=params)

# Configure simulation
settings = SimulationSettings(
    alpha = 16.0,           # Action precision
    eta = 1.0,              # Learning rate
    exposure_mode = true    # Force approach policy
)

# Run exposure therapy
results = run_exposure_therapy(model; n_trials=200, settings=settings)

# View results
println("Approach: $(results.approach_count)")
println("Avoid: $(results.avoid_count)")

# Final beliefs about spider safety
p_safe = softmax_tau(results.agent.d[3]; tau=0.1)[2]
println("P(safe): $p_safe")
```

## Model Components

### Matrices

| Matrix | Description |
|--------|-------------|
| `D` | Initial state priors (categorical) |
| `d` | Dirichlet concentration parameters for D |
| `A` | Observation likelihood (state → observation) |
| `a` | Dirichlet concentration parameters for A |
| `B` | State transition matrices |
| `C` | Observation preferences (reward/cost) |
| `E` | Policy prior |
| `V` | Policy definitions (action sequences) |

### Key Functions

```julia
# Model construction
build_model(; params=ModelParams())

# Agent initialization
init_agent(model; settings=SimulationSettings())

# Run single trial
run_trial(model, agent, true_state; settings)

# Run full simulation
run_exposure_therapy(model; n_trials, settings)
```

## Theory

The model implements the **expected free energy** (EFE) formulation of active inference:

```
G(π) = Σ_t [ E_Q[H(o|s)] - E_Q[log P(o|C)] ]
     = Σ_t [ ambiguity     -  expected utility ]
```

Where:
- **Ambiguity**: Expected uncertainty about observations given states
- **Expected utility**: Alignment of expected observations with preferences

### Learning

The agent learns through **Dirichlet-categorical** updates:
- `a` parameters update the observation model (learns spider is safe)
- `d` parameters update initial state beliefs (updates P(safe))

## Testing

```bash
julia --project=. test/runtests.jl
```

## Files

```
ifs-active-inference/
├── Project.toml           # Julia dependencies
├── README.md
├── run.jl                 # Main entry point
├── spec.md                # Original specification
├── src/
│   ├── IFSActiveInference.jl  # Module definition
│   ├── model.jl           # Model construction
│   ├── simulation.jl      # Active inference engine
│   └── plotting.jl        # Visualization utilities
└── test/
    └── runtests.jl        # Unit tests
```

## References

- Original MATLAB code from the Scientific Reports paper on computational psychiatry
- [ActiveInference.jl](https://github.com/ilabcode/ActiveInference.jl) - Julia active inference library
- [pymdp](https://github.com/infer-actively/pymdp) - Python implementation
- Friston et al. "Active Inference and Learning" - Theoretical foundations

## License

MIT
