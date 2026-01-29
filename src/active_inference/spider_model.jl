"""
    spider_model.jl - Spider Phobia Model for Active Inference

Application of the generic Active Inference framework to model spider phobia
exposure therapy, based on the CBT simulation from the Scientific Reports paper.
"""

# Include the model.jl from parent directory for model construction functions
include("../model.jl")

# =============================================================================
# Spider Environment
# =============================================================================

"""
    SpiderEnvironment <: AIFEnvironment

Environment for the spider phobia exposure therapy simulation.

The environment tracks:
- Whether the spider is actually dangerous
- Current state across three factors: [behavior, spider_present, danger]
- Generates observations from the A matrices
- Applies state transitions via B matrices
"""
mutable struct SpiderEnvironment <: AIFEnvironment
    spider_dangerous::Bool
    current_state::Vector{Int}  # [behavior, spider_present, danger]
    A::Vector{Array{Float64}}   # For sampling observations
    B::Vector{Array{Float64,3}} # For transitions

    # Initial state for reset
    initial_state::Vector{Int}
end

"""
    SpiderEnvironment(spider_dangerous::Bool, A, B)

Create a spider environment.

# Arguments
- `spider_dangerous`: Whether the spider is actually dangerous
- `A`: Observation likelihood matrices (for generating observations)
- `B`: State transition matrices

# Initial State
- Factor 1 (behavior): 1 (start)
- Factor 2 (spider_present): 2 (spider is present)
- Factor 3 (danger): 1 if dangerous, 2 if safe
"""
function SpiderEnvironment(spider_dangerous::Bool, A::Vector{<:Array}, B::Vector{<:Array{<:Real,3}})
    # Initial state: start behavior, spider present, danger based on spider_dangerous
    initial_state = [1, 2, spider_dangerous ? 1 : 2]
    current_state = copy(initial_state)

    # Convert to consistent types
    A_typed = [Array{Float64}(a) for a in A]
    B_typed = [Array{Float64,3}(b) for b in B]

    SpiderEnvironment(spider_dangerous, current_state, A_typed, B_typed, initial_state)
end

"""
    reset!(env::SpiderEnvironment)

Reset the environment to its initial state.
"""
function reset!(env::SpiderEnvironment)
    env.current_state .= env.initial_state
    return env
end

"""
    get_state(env::SpiderEnvironment) -> Vector{Int}

Get the current true state of the environment.
Returns a copy of the state vector [behavior, spider_present, danger].
"""
function get_state(env::SpiderEnvironment)::Vector{Int}
    return copy(env.current_state)
end

"""
    observe(env::SpiderEnvironment) -> Vector{Int}

Sample an observation from each modality based on current state.
Uses the A matrices to generate probabilistic observations.
"""
function observe(env::SpiderEnvironment)::Vector{Int}
    Ng = length(env.A)
    obs = Vector{Int}(undef, Ng)

    s1, s2, s3 = env.current_state

    for g in 1:Ng
        # Get observation probabilities for current state
        # A[g] has shape (No[g], Ns[1], Ns[2], Ns[3])
        probs = env.A[g][:, s1, s2, s3]

        # Normalize (should already be normalized, but ensure numerical stability)
        probs_sum = sum(probs)
        if probs_sum > 0
            probs = probs ./ probs_sum
        else
            # Uniform if all zero (shouldn't happen with proper A)
            probs = fill(1.0 / length(probs), length(probs))
        end

        # Sample observation
        obs[g] = sample_categorical(probs)
    end

    return obs
end

"""
    step!(env::SpiderEnvironment, action::Vector{Int})

Apply an action to transition the environment state.
Only factor 1 (behavior) is controllable; factors 2 and 3 are fixed.

# Arguments
- `action`: Vector of action indices, one per factor
"""
function step!(env::SpiderEnvironment, action::Vector{Int})
    Nf = length(env.B)

    for f in 1:Nf
        s_current = env.current_state[f]

        # Get action for this factor (use 1 if factor has only 1 action)
        Na_f = size(env.B[f], 3)
        a_f = Na_f > 1 ? action[f] : 1

        # Get transition probabilities
        # B[f] has shape (Ns[f], Ns[f], Na[f])
        probs = env.B[f][:, s_current, a_f]

        # Normalize
        probs_sum = sum(probs)
        if probs_sum > 0
            probs = probs ./ probs_sum
        else
            # Stay in current state if no valid transitions
            probs = zeros(length(probs))
            probs[s_current] = 1.0
        end

        # Sample next state
        env.current_state[f] = sample_categorical(probs)
    end

    return env
end

# =============================================================================
# Model Construction
# =============================================================================

"""
    build_spider_aif_model(params::ModelParams) -> AIFModel

Build an AIFModel from the spider phobia model specification.

# Arguments
- `params`: ModelParams containing simulation parameters

# Returns
An AIFModel ready for use with the Active Inference framework.
"""
function build_spider_aif_model(params::ModelParams)
    # Build the raw model using functions from model.jl
    raw_model = build_model(params=params)

    # Create PolicySet from the model's V and E
    policies = PolicySet(raw_model.V, raw_model.E)

    # Create and return the AIFModel
    return AIFModel(
        raw_model.A,
        raw_model.B,
        raw_model.C,
        raw_model.D;
        policies=policies,
        trial_length=params.T
    )
end

# =============================================================================
# Therapy Simulation
# =============================================================================

"""
    run_spider_aif_therapy(; kwargs...) -> Vector{Float64}

Run a spider phobia exposure therapy simulation.

# Keyword Arguments
- `n_trials::Int=200`: Number of therapy trials
- `spider_dangerous::Bool=false`: Whether the spider is actually dangerous
- `params::ModelParams=ModelParams()`: Model parameters
- `settings::AIFSettings=AIFSettings()`: Inference settings
- `pA_init::Union{Nothing, Vector{<:Array}}=nothing`: Initial pA Dirichlet parameters
- `pD_init::Union{Nothing, Vector{<:Vector}}=nothing`: Initial pD Dirichlet parameters

# Returns
A vector of length `n_trials` containing p_safe = pD[3][2] / sum(pD[3]) after each trial.
This tracks the agent's belief that the spider is safe over the course of therapy.
"""
function run_spider_aif_therapy(;
    n_trials::Int=200,
    spider_dangerous::Bool=false,
    params::ModelParams=ModelParams(),
    settings::AIFSettings=AIFSettings(),
    pA_init::Union{Nothing, Vector{<:Array}}=nothing,
    pD_init::Union{Nothing, Vector{<:Vector}}=nothing
)
    # Build the model
    model = build_spider_aif_model(params)

    # Initialize agent
    if !isnothing(pA_init) && !isnothing(pD_init)
        # Use custom initial Dirichlet parameters
        # Need pB as well - use model B scaled
        pB_init = [copy(model.B[f]) for f in 1:length(model.B)]
        agent = init_agent(model, pA_init, pB_init, pD_init)
    elseif !isnothing(pA_init)
        # Custom pA, default pD from model
        pB_init = [copy(model.B[f]) for f in 1:length(model.B)]
        pD_default = [copy(model.D[f]) for f in 1:length(model.D)]
        agent = init_agent(model, pA_init, pB_init, pD_default)
    elseif !isnothing(pD_init)
        # Custom pD, default pA from model
        pA_default = [copy(model.A[g]) for g in 1:model.Ng]
        pB_init = [copy(model.B[f]) for f in 1:length(model.B)]
        agent = init_agent(model, pA_default, pB_init, pD_init)
    else
        # Use default initialization
        agent = init_agent(model)
    end

    # Create environment
    env = SpiderEnvironment(spider_dangerous, model.A, model.B)

    # Results storage: track p_safe after each trial
    results = Vector{Float64}(undef, n_trials)

    # Learning configuration: learn A[3] (affective) and D[3] (danger beliefs)
    learn_A = [3]  # Learn affective consequences
    learn_D = [3]  # Learn danger beliefs

    # Run trials
    for trial in 1:n_trials
        # Run a single trial with learning
        run_trial!(agent, model, env, settings;
                  learn_A=learn_A, learn_B=Int[], learn_D=learn_D)

        # Record p_safe = P(safe) = pD[3][2] / sum(pD[3])
        p_safe = agent.pD[3][2] / sum(agent.pD[3])
        results[trial] = p_safe
    end

    return results
end
