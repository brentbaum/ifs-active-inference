"""
    ActiveInferenceCore

Generic Active Inference implementation supporting:
- Factored state spaces with multiple observation modalities
- Expected Free Energy with ambiguity, risk, and state information gain
- Dirichlet learning for A (observations), B (transitions), and D (initial states)
- Classic benchmarks (T-maze, spider phobia)
"""
module ActiveInferenceCore

using LinearAlgebra

# Core types and utilities
include("core.jl")

# State inference
include("inference.jl")

# Expected Free Energy
include("efe.jl")

# Policy inference
include("policy.jl")

# Learning
include("learning.jl")

# Agent loop
include("agent.jl")

# Applications
include("spider_model.jl")
include("tmaze.jl")

# Export core types
export AIFSettings, PolicySet, AIFModel, AIFAgent
export init_agent, reset_trial!

# Export inference
export infer_states!

# Export EFE
export calculate_efe, forward_simulate

# Export policy
export infer_policies!, sample_action

# Export learning
export update_learning!

# Export agent
export AIFEnvironment, run_trial!

# Export utilities
export softmax, entropy, kl_divergence, sample_categorical
export get_A_from_pA, get_B_from_pB, get_D_from_pD

# Export spider model
export SpiderEnvironment, build_spider_aif_model, run_spider_aif_therapy

# Export T-maze
export TMazeEnvironment, build_tmaze_model, run_tmaze_test

end # module
