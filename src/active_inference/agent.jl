"""
    Agent trial loop for Active Inference

This module implements the environment interface and main trial loop
for running Active Inference agents.
"""

# =============================================================================
# Abstract Environment Interface
# =============================================================================

"""
    AIFEnvironment

Abstract type for Active Inference environments.
Concrete implementations must define the interface functions below.
"""
abstract type AIFEnvironment end

"""
    observe(env::AIFEnvironment) -> Vector{Int}

Get the current observation from the environment.
Returns a vector of observation indices, one per modality.
"""
function observe(env::AIFEnvironment)::Vector{Int}
    error("observe not implemented for $(typeof(env))")
end

"""
    step!(env::AIFEnvironment, action::Vector{Int})

Execute an action in the environment.
`action` is a vector of action indices, one per factor.
"""
function step!(env::AIFEnvironment, action::Vector{Int})
    error("step! not implemented for $(typeof(env))")
end

"""
    get_state(env::AIFEnvironment) -> Vector{Int}

Get the true hidden state of the environment.
Returns a vector of state indices, one per factor.
"""
function get_state(env::AIFEnvironment)::Vector{Int}
    error("get_state not implemented for $(typeof(env))")
end

"""
    reset!(env::AIFEnvironment)

Reset the environment to its initial state.
"""
function reset!(env::AIFEnvironment)
    error("reset! not implemented for $(typeof(env))")
end

# =============================================================================
# Trial Loop
# =============================================================================

"""
    run_trial!(agent, model, env, settings; learn_A=Int[], learn_B=Int[], learn_D=Int[], deterministic_actions=false)

Run a single trial of Active Inference.

# Arguments
- `agent`: The Active Inference agent
- `model`: The generative model
- `env`: The environment (subtype of AIFEnvironment)
- `settings`: Inference settings

# Keyword Arguments
- `learn_A::Vector{Int}`: Indices of A matrices to learn (default: empty)
- `learn_B::Vector{Int}`: Indices of B matrices to learn (default: empty)
- `learn_D::Vector{Int}`: Indices of D vectors to learn (default: empty)
- `deterministic_actions::Bool`: If true, pick MAP actions instead of sampling

# Returns
A NamedTuple containing the trial history:
- `observations`: Vector of observations at each timestep
- `actions`: Vector of actions taken (length T-1)
- `beliefs`: Vector of posterior beliefs at each timestep
- `qpi`: Vector of policy posteriors at each timestep
- `states`: Vector of true environment states at each timestep
"""
function run_trial!(
    agent,
    model,
    env::AIFEnvironment,
    settings;
    learn_A::Vector{Int}=Int[],
    learn_B::Vector{Int}=Int[],
    learn_D::Vector{Int}=Int[],
    deterministic_actions::Bool=false
)
    # Reset agent and environment
    reset_trial!(agent, model)
    reset!(env)

    # Initialize history storage
    observations = Vector{Vector{Int}}(undef, model.T)
    actions = Vector{Vector{Int}}(undef, model.T - 1)
    beliefs = Vector{Any}(undef, model.T)
    qpi = Vector{Any}(undef, model.T)
    states = Vector{Vector{Int}}(undef, model.T)

    # Main trial loop
    for t in 1:model.T
        # Set current timestep
        agent.t = t

        # Get observation from environment
        obs = observe(env)
        observations[t] = obs

        # Record true state
        states[t] = get_state(env)

        # State inference
        infer_states!(agent, model, obs, settings)

        # Store beliefs
        beliefs[t] = deepcopy(agent.qs)

        # Learning updates
        update_learning!(agent, model, obs, settings;
                        learn_A=learn_A, learn_B=learn_B, learn_D=learn_D)

        # Policy inference and action selection (except at final timestep)
        if t < model.T
            infer_policies!(agent, model, settings)
            qpi[t] = deepcopy(agent.qpi)

            action = sample_action(agent, model; alpha=settings.alpha, deterministic=deterministic_actions)
            actions[t] = action

            # Execute action in environment
            step!(env, action)
        else
            # No policy inference at final timestep
            qpi[t] = nothing
        end
    end

    return (
        observations = observations,
        actions = actions,
        beliefs = beliefs,
        qpi = qpi,
        states = states
    )
end
