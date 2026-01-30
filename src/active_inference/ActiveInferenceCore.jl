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
using Plots
using SpecialFunctions

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
include("trust_game.jl")
include("concepts_model.jl")

# Visualization
include("visualization.jl")

# Export core types
export AIFSettings, PolicySet, AIFModel, AIFAgent
export init_agent, reset_trial!

# Export inference
export infer_states!

# Export EFE
export calculate_efe, forward_simulate
export compute_predicted_obs, compute_ambiguity, compute_state_info_gain

# Export policy
export infer_policies!, sample_action

# Export learning
export update_learning!

# Export agent
export AIFEnvironment, run_trial!
export observe, step!, get_state, reset!

# Export utilities
export softmax, entropy, kl_divergence, sample_categorical
export get_A_from_pA, get_B_from_pB, get_D_from_pD

# Export spider model
export SpiderEnvironment, build_spider_aif_model, run_spider_aif_therapy

# Export T-maze
export TMazeEnvironment, build_tmaze_model, run_tmaze_test

# Export Trust Game
export AgentProfile, TrustGameEnvironment, TrustGameResults
export healthy_profile, depressed_profile, anxious_profile, insecure_profile, all_profiles
export healthy_profile_paper, depressed_profile_paper, depressed2_profile_paper
export social_phobia_profile_paper, social_phobia2_profile_paper, borderline_profile_paper
export all_paper_profiles
export build_trust_game_model, build_trust_game_A, build_trust_game_B, build_trust_game_C, build_trust_game_D
export build_trust_game_policies
export run_trust_game_simulation, run_trust_game_comparison
export PaperStyleResults, run_trust_game_phases
export plot_trust_game_sharing, plot_trust_game_beliefs, plot_trust_game_summary
export plot_trust_game_paper_style, plot_trust_game_comparison_paper_style

# Export Concepts Model (PMC7250191)
export ConceptsEnvironment, CONCEPT_ANIMALS, CONCEPT_REPORTS, CONCEPT_FEEDBACK
export DISTANCE_REPORTS
export build_concepts_model, build_concepts_A, build_concepts_B, build_concepts_C, build_concepts_D
export build_concepts_policies, init_concepts_agent, concepts_settings
export copy_agent_to_model, run_concepts_learning!, evaluate_reporting
export bmr_reduce_D, apply_bmr_D!
export build_distance_model, build_distance_A, build_distance_B, build_distance_D
export build_distance_policies, evaluate_distance_reporting

# Export visualization
export plot_spider_therapy, plot_spider_comparison
export plot_belief_evolution, plot_belief_heatmap
export plot_tmaze_trial, plot_tmaze_policy_probs
export plot_tmaze_summary, plot_tmaze_comparison_summary
export plot_learning_curve

end # module
