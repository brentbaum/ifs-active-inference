"""
    IFSActiveInference.jl - Internal Family Systems meets Active Inference

A Julia implementation of the CBT spider phobia exposure therapy model
using active inference. Based on the MATLAB code from the Scientific Reports paper.

This package provides:
- Model construction (D, A, B, C, E, V matrices)
- Active inference simulation with belief updating
- Dirichlet learning for exposure therapy
- Visualization of belief evolution

Example usage:
```julia
using IFSActiveInference

# Build the model
model = build_model()

# Run exposure therapy simulation
results = run_exposure_therapy(model; n_trials=200)

# Generate visualizations
generate_report(results)
```
"""
module IFSActiveInference

using LinearAlgebra
using Random
using Statistics
using Plots

# Model construction
include("model.jl")

# Simulation engine
include("simulation.jl")

# Visualization
include("plotting.jl")

# ActiveInference.jl-based implementation (optional)
include("activeinference_impl.jl")

# RxInfer.jl-based implementation (optional)
include("rxinfer_impl.jl")

# Export public API
export ModelParams,
       build_model,
       create_initial_state_priors,
       create_observation_model,
       create_transition_model,
       create_policies,
       create_preferences,
       create_policy_prior,
       softmax_tau,
       normalize_columns

export SimulationSettings,
       AgentState,
       init_agent,
       run_trial,
       run_exposure_therapy

export plot_belief_evolution,
       plot_affective_learning,
       plot_behavioral_summary,
       generate_report

# ActiveInference.jl implementation exports (when available)
export ACTIVEINFERENCE_AVAILABLE,
       build_aif_matrices,
       run_aif_exposure_therapy

# RxInfer.jl implementation exports (when available)
export RXINFER_AVAILABLE,
       build_rxinfer_matrices,
       one_hot,
       flatten_state,
       unflatten_state

end # module
