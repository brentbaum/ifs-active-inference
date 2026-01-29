"""
    simulation.jl - Active Inference Simulation Engine

Runs the IFS spider phobia exposure therapy simulation.
Attempts to use ActiveInference.jl, falls back to native implementation.
"""

using LinearAlgebra
using Random
using Statistics

"""
    SimulationSettings

Configuration for running simulations.
"""
Base.@kwdef struct SimulationSettings
    alpha::Float64 = 16.0    # Action precision (inverse temperature)
    beta::Float64 = 1.0      # Policy precision
    gamma::Float64 = 1.0     # Precision prior
    eta::Float64 = 1.0       # Learning rate for Dirichlet parameters
    modalities_to_learn::Vector{Int} = [3]  # Which A matrices to update
    factors_to_learn::Vector{Int} = [3]     # Which d vectors to update
    exposure_mode::Bool = false  # Force approach policy during exposure
end

"""
    AgentState

Mutable state for an active inference agent during simulation.
"""
mutable struct AgentState
    # Current beliefs
    qs::Vector{Vector{Float64}}  # Posterior over hidden states per factor
    qpi::Vector{Float64}         # Posterior over policies

    # Learnable parameters (Dirichlet concentrations)
    a::Vector{Array{Float64}}    # Observation model parameters
    d::Vector{Vector{Float64}}   # Initial state parameters

    # Tracking
    action_history::Vector{Vector{Int}}
    observation_history::Vector{Vector{Int}}
    state_history::Vector{Vector{Int}}
    belief_history::Vector{Any}
end

"""
    init_agent(model; settings=SimulationSettings())

Initialize an active inference agent from a model specification.
"""
function init_agent(model; settings::SimulationSettings = SimulationSettings())
    # Initialize beliefs as uniform over states
    qs = [ones(n) ./ n for n in model.Ns]
    qpi = ones(size(model.V, 2)) ./ size(model.V, 2)

    # Copy Dirichlet parameters (will be updated during learning)
    a = deepcopy(model.a)
    d = deepcopy(model.d)

    return AgentState(
        qs, qpi,
        a, d,
        Vector{Int}[], Vector{Int}[], Vector{Int}[], []
    )
end

"""
    sample_observation(model, state::Vector{Int})

Sample an observation given the true hidden state.
"""
function sample_observation(model, state::Vector{Int})
    observations = Int[]
    for g in 1:model.Ng
        # Get likelihood for this modality given state
        A_g = model.A[g]
        # Index into A matrix with state indices
        probs = A_g[:, state...]
        probs = probs ./ sum(probs)  # Normalize

        # Sample from categorical
        obs = Categorical_sample(probs)
        push!(observations, obs)
    end
    return observations
end

"""
    Categorical_sample(p)

Sample from a categorical distribution with probabilities p.
Returns the index of the sampled outcome.
"""
function Categorical_sample(p::AbstractVector)
    cdf = cumsum(p)
    r = rand()
    for (i, c) in enumerate(cdf)
        if r <= c
            return i
        end
    end
    return length(p)
end

"""
    infer_states!(agent::AgentState, model, observation::Vector{Int}, t::Int)

Update posterior beliefs over hidden states given observation.
Uses variational message passing.
"""
function infer_states!(agent::AgentState, model, observation::Vector{Int}, t::Int)
    Nf = model.Nf

    # Simple fixed-point iteration for state inference
    for iter in 1:16
        qs_old = deepcopy(agent.qs)

        for f in 1:Nf
            # Log prior from learnable initial state distribution (agent's beliefs)
            log_prior = log.(normalize_vec(agent.d[f]) .+ 1e-16)

            # Log likelihood from observations
            log_lik = zeros(model.Ns[f])
            for g in 1:model.Ng
                A_g = normalize_columns(agent.a[g])
                # Marginalize over other factors
                for s in 1:model.Ns[f]
                    state_idx = [i == f ? s : 1 for i in 1:Nf]
                    # Average over other factor states
                    lik_sum = 0.0
                    for other_states in Iterators.product([1:model.Ns[i] for i in 1:Nf if i != f]...)
                        idx = Int[]
                        other_idx = 1
                        for i in 1:Nf
                            if i == f
                                push!(idx, s)
                            else
                                push!(idx, other_states[other_idx])
                                other_idx += 1
                            end
                        end
                        weight = prod(agent.qs[i][idx[i]] for i in 1:Nf if i != f)
                        lik_sum += weight * A_g[observation[g], idx...]
                    end
                    log_lik[s] += log(lik_sum + 1e-16)
                end
            end

            # Update posterior
            agent.qs[f] = softmax_vec(log_prior + log_lik)
        end

        # Check convergence
        if maximum(maximum(abs.(agent.qs[f] - qs_old[f])) for f in 1:Nf) < 1e-6
            break
        end
    end
end

"""
    calculate_EFE(model, agent::AgentState, policy_idx::Int, settings::SimulationSettings)

Calculate expected free energy for a given policy.
EFE = ambiguity - expected utility
"""
function calculate_EFE(model, agent::AgentState, policy_idx::Int, settings::SimulationSettings)
    T = model.T
    Nf = model.Nf
    V = model.V

    G = 0.0  # Expected free energy

    # Forward simulate beliefs under this policy
    qs_future = deepcopy(agent.qs)

    for t in 1:(T-1)
        # Get action for this policy at this time
        actions = [V[t, policy_idx, f] for f in 1:Nf]

        # Predict next state under this action
        qs_next = Vector{Vector{Float64}}(undef, Nf)
        for f in 1:Nf
            B_f = model.B[f]
            if size(B_f, 3) >= actions[f]
                qs_next[f] = B_f[:, :, actions[f]] * qs_future[f]
            else
                qs_next[f] = B_f[:, :, 1] * qs_future[f]
            end
            qs_next[f] = normalize_vec(qs_next[f])
        end

        # Calculate expected observations
        for g in 1:model.Ng
            A_g = normalize_columns(agent.a[g])
            C_g = model.C[g]

            # Expected observation probabilities
            qo = zeros(model.No[g])
            for s_combo in Iterators.product([1:n for n in model.Ns]...)
                weight = prod(qs_next[f][s_combo[f]] for f in 1:Nf)
                qo .+= weight .* A_g[:, s_combo...]
            end
            qo = normalize_vec(qo)

            # Expected utility (negative of preferences)
            utility = -dot(qo, C_g[:, min(t+1, T)])

            # Ambiguity (entropy of expected observations)
            H = -sum(p > 0 ? p * log(p) : 0 for p in qo)

            G += utility + 0.5 * H
        end

        qs_future = qs_next
    end

    return G
end

"""
    infer_policies!(agent::AgentState, model, settings::SimulationSettings)

Compute posterior over policies based on expected free energy.
"""
function infer_policies!(agent::AgentState, model, settings::SimulationSettings)
    Np = size(model.V, 2)
    G = zeros(Np)

    for pi in 1:Np
        G[pi] = calculate_EFE(model, agent, pi, settings)
    end

    # Policy posterior with prior E
    log_E = log.(model.E .+ 1e-16)
    agent.qpi = softmax_vec(-settings.gamma * G + log_E)
end

"""
    sample_action!(agent::AgentState, model, t::Int, settings::SimulationSettings)

Sample an action based on policy posterior.
"""
function sample_action!(agent::AgentState, model, t::Int, settings::SimulationSettings)
    Nf = model.Nf
    V = model.V

    # Marginalize over policies to get action probabilities per factor
    actions = Int[]
    for f in 1:Nf
        # Get unique actions for this factor at this time
        possible_actions = unique(V[t, :, f])
        action_probs = zeros(length(possible_actions))

        for (ai, a) in enumerate(possible_actions)
            for pi in 1:length(agent.qpi)
                if V[t, pi, f] == a
                    action_probs[ai] += agent.qpi[pi]
                end
            end
        end

        action_probs = normalize_vec(action_probs)

        # Sample action with temperature
        if settings.alpha > 0
            action_probs = softmax_vec(log.(action_probs .+ 1e-16) * settings.alpha)
        end

        action_idx = Categorical_sample(action_probs)
        push!(actions, possible_actions[action_idx])
    end

    return actions
end

"""
    update_transition!(state::Vector{Int}, actions::Vector{Int}, model)

Apply transitions to get next state.
"""
function update_transition!(state::Vector{Int}, actions::Vector{Int}, model)
    new_state = similar(state)
    for f in 1:model.Nf
        B_f = model.B[f]
        a = min(actions[f], size(B_f, 3))
        trans_probs = B_f[:, state[f], a]
        trans_probs = normalize_vec(trans_probs)
        new_state[f] = Categorical_sample(trans_probs)
    end
    return new_state
end

"""
    update_learning!(agent::AgentState, model, observation::Vector{Int}, settings::SimulationSettings)

Update Dirichlet parameters based on observations (categorical learning).
"""
function update_learning!(agent::AgentState, model, observation::Vector{Int}, settings::SimulationSettings)
    eta = settings.eta

    # Update a (observation model) for learnable modalities
    for g in settings.modalities_to_learn
        if g <= model.Ng
            # Get expected state
            for s_combo in Iterators.product([1:n for n in model.Ns]...)
                weight = prod(agent.qs[f][s_combo[f]] for f in 1:model.Nf)
                if weight > 0.01  # Only update for likely states
                    # Increment concentration for observed outcome
                    agent.a[g][observation[g], s_combo...] += eta * weight
                end
            end
        end
    end

    # Update d (initial state prior) for learnable factors
    for f in settings.factors_to_learn
        if f <= model.Nf
            agent.d[f] .+= eta .* agent.qs[f]
        end
    end
end

"""
    run_trial(model, agent::AgentState, true_state::Vector{Int};
              settings=SimulationSettings())

Run a single trial of the active inference simulation.
Returns: (observations, actions, states, beliefs)
"""
function run_trial(model, agent::AgentState, true_state::Vector{Int};
                   settings::SimulationSettings = SimulationSettings())
    T = model.T
    observations = Vector{Int}[]
    actions = Vector{Int}[]
    states = [copy(true_state)]
    beliefs = [deepcopy(agent.qs)]

    current_state = copy(true_state)

    for t in 1:T
        # Generate observation
        obs = sample_observation(model, current_state)
        push!(observations, obs)

        # State inference
        infer_states!(agent, model, obs, t)
        push!(beliefs, deepcopy(agent.qs))

        # Learning update (MOVED: now happens between state and policy inference)
        # This matches ActiveInference.jl's order: infer_states -> update_parameters -> infer_policies
        update_learning!(agent, model, obs, settings)

        if t < T
            # Policy inference (now uses updated parameters)
            infer_policies!(agent, model, settings)

            # Action selection
            action = sample_action!(agent, model, t, settings)
            push!(actions, action)

            # State transition
            current_state = update_transition!(current_state, action, model)
            push!(states, copy(current_state))
        end
    end

    # Record history
    push!(agent.observation_history, observations[end])
    if !isempty(actions)
        push!(agent.action_history, actions[end])
    end
    push!(agent.state_history, states[end])
    push!(agent.belief_history, beliefs[end])

    return (observations=observations, actions=actions, states=states, beliefs=beliefs)
end

"""
    run_exposure_therapy(model; n_trials=200, settings=SimulationSettings(), spider_dangerous=false)

Run the full exposure therapy simulation.
Returns: Results containing belief evolution and behavioral outcomes.

If spider_dangerous=true, the spider actually causes harm (tests learning that spider IS dangerous).
If spider_dangerous=false (default), the spider is safe (tests learning that spider is NOT dangerous).
"""
function run_exposure_therapy(model; n_trials::Int = 200, settings::SimulationSettings = SimulationSettings(), spider_dangerous::Bool = false)
    agent = init_agent(model; settings=settings)

    # Track belief evolution
    d_evolution = Vector{Vector{Float64}}[]
    a_evolution = []
    approach_count = 0
    avoid_count = 0

    # Set up exposure mode: force approach policy
    exposure_settings = if settings.exposure_mode
        SimulationSettings(
            alpha = settings.alpha,
            beta = settings.beta,
            gamma = settings.gamma,
            eta = settings.eta,
            modalities_to_learn = settings.modalities_to_learn,
            factors_to_learn = settings.factors_to_learn,
            exposure_mode = true
        )
    else
        settings
    end

    for trial in 1:n_trials
        # Initial state: start position, spider present
        # Factor 3: 1=dangerous, 2=safe
        danger_state = spider_dangerous ? 1 : 2
        true_state = [1, 2, danger_state]  # start, spider present, danger status

        # If exposure mode, override policy prior to force approach
        if exposure_settings.exposure_mode
            model_copy = merge(model, (E = [1.0, 0.0],))  # Force approach
            result = run_trial(model_copy, agent, true_state; settings=exposure_settings)
        else
            result = run_trial(model, agent, true_state; settings=settings)
        end

        # Track which policy was chosen
        if !isempty(result.actions) && result.actions[1][1] == 1
            approach_count += 1
        else
            avoid_count += 1
        end

        # Store belief evolution
        push!(d_evolution, deepcopy([normalize_vec(d) for d in agent.d]))
        push!(a_evolution, deepcopy(agent.a[3]))

        if trial % 50 == 0
            @info "Trial $trial/$n_trials: Approach=$approach_count, Avoid=$avoid_count"
        end
    end

    return (
        agent = agent,
        d_evolution = d_evolution,
        a_evolution = a_evolution,
        approach_count = approach_count,
        avoid_count = avoid_count,
        n_trials = n_trials
    )
end

# Helper functions
function normalize_vec(x::AbstractVector)
    s = sum(x)
    return s > 0 ? x ./ s : ones(length(x)) ./ length(x)
end

function softmax_vec(x::AbstractVector; tau::Real = 1.0)
    x_shifted = x .- maximum(x)
    ex = exp.(x_shifted ./ tau)
    return ex ./ sum(ex)
end

function merge(nt1::NamedTuple, nt2::NamedTuple)
    return (; nt1..., nt2...)
end
