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
- `exposure_mode::Bool=true`: Force approach policy (simulates therapist-guided exposure)
- `use_paper_priors::Bool=true`: Use Dirichlet priors from paper (d, a) instead of categorical (D, A)
- `pA_init::Union{Nothing, Vector{<:Array}}=nothing`: Custom initial pA Dirichlet parameters
- `pD_init::Union{Nothing, Vector{<:Vector}}=nothing`: Custom initial pD Dirichlet parameters

# Returns
A vector of length `n_trials` containing p_safe = pD[3][2] / sum(pD[3]) after each trial.
This tracks the agent's belief that the spider is safe over the course of therapy.

# Paper Reference
The model is based on the CBT simulation from the Scientific Reports paper.
With use_paper_priors=true:
- Initial P(safe) ≈ 10% (from d[3] = [45, 5] giving P(safe) = 5/50 = 0.1)
- Safe spider: P(safe) should increase through exposure
- Dangerous spider: P(safe) should decrease

# Exposure Mode
With exposure_mode=true, the agent always approaches the spider (policy 1),
simulating therapist-guided exposure therapy. This is necessary because:
- The agent starts with strong belief (90%) that spider is dangerous
- Avoiding provides no differential evidence (dangerous and safe give same observations)
- Only approaching/interacting provides evidence (harm vs neutral observations)
Without exposure mode, the agent avoids and never learns.
"""
function run_spider_aif_therapy(;
    n_trials::Int=200,
    spider_dangerous::Bool=false,
    params::ModelParams=ModelParams(),
    settings::AIFSettings=AIFSettings(),
    exposure_mode::Bool=true,
    use_paper_priors::Bool=true,
    pA_init::Union{Nothing, Vector{<:Array}}=nothing,
    pD_init::Union{Nothing, Vector{<:Vector}}=nothing
)
    # Build the raw model to get both categorical (A,D) and Dirichlet (a,d) priors
    raw_model = build_model(params=params)

    # Create PolicySet from the model's V and E
    policies = PolicySet(raw_model.V, raw_model.E)

    # Create AIFModel
    model = AIFModel(
        raw_model.A,
        raw_model.B,
        raw_model.C,
        raw_model.D;
        policies=policies,
        trial_length=params.T
    )

    # Determine initial Dirichlet parameters
    if !isnothing(pA_init) && !isnothing(pD_init)
        # Use custom initial Dirichlet parameters
        pA = pA_init
        pD = pD_init
    elseif use_paper_priors
        # Use Dirichlet priors from paper (a, d)
        pA = raw_model.a
        pD = raw_model.d
    else
        # Use categorical priors scaled (original behavior)
        pA = [copy(model.A[g]) for g in 1:model.Ng]
        pD = [copy(model.D[f]) for f in 1:length(model.D)]
    end

    # pB from model B
    pB = [copy(model.B[f]) for f in 1:length(model.B)]

    # Initialize agent with proper Dirichlet priors
    agent = init_agent(model, pA, pB, pD)

    # Create environment
    env = SpiderEnvironment(spider_dangerous, model.A, model.B)

    # Results storage: track p_safe after each trial
    results = Vector{Float64}(undef, n_trials)

    # Learning configuration: learn D[3] (danger beliefs)
    # NOTE: A matrix learning disabled - see run_exposure_trial! docstring
    learn_D = [3]  # Learn danger beliefs

    # Run trials
    for trial in 1:n_trials
        if exposure_mode
            # Run trial with forced approach policy
            run_exposure_trial!(agent, model, env, settings;
                               learn_D=learn_D)
        else
            # Run trial with EFE-based policy selection
            run_trial!(agent, model, env, settings;
                      learn_A=learn_A, learn_B=Int[], learn_D=learn_D)
        end

        # Record p_safe = P(safe) = pD[3][2] / sum(pD[3])
        p_safe = agent.pD[3][2] / sum(agent.pD[3])
        results[trial] = p_safe
    end

    return results
end

"""
    run_exposure_trial!(agent, model, env, settings; learn_D)

Run a single exposure therapy trial with forced approach policy.

Unlike run_trial!, this forces approach actions (policy 1) instead of
using EFE-based policy selection. This simulates therapist-guided exposure
where the patient is encouraged to approach despite their fear.

The agent still:
- Performs state inference (updates beliefs based on observations)
- Learns D parameters (updates danger beliefs based on observations)

But it does NOT:
- Use EFE to select actions (always approaches)
- Learn A parameters (observation model stays fixed)

NOTE: A matrix learning is disabled because updating pA for all state
combinations (weighted by belief) causes the observation model to degrade.
When the agent sees neutral outcomes and believes the spider is probably safe,
it still updates pA[dangerous, neutral], which increases P(neutral|dangerous)
and slows down learning. By keeping A fixed, we get proper belief updating
that matches the paper's expected results (~90% P(safe) for safe spider).

IMPORTANT: For static hidden states (like danger in factor 3), we update
pD based on FINAL beliefs (after all evidence), not initial beliefs.
This is because the danger state doesn't change during the trial, and
we want to learn from all the evidence collected.
"""
function run_exposure_trial!(
    agent,
    model,
    env::AIFEnvironment,
    settings;
    learn_D::Vector{Int}=Int[]
)
    # Reset agent and environment
    reset_trial!(agent, model)
    reset!(env)

    Nf = length(model.D)

    # Forced approach action: action 1 for factor 1, identity for others
    approach_action = ones(Int, Nf)

    # Main trial loop
    for t in 1:model.T
        # Set current timestep
        agent.t = t

        # Get observation from environment
        obs = observe(env)

        # State inference - this is where beliefs update based on evidence!
        infer_states!(agent, model, obs, settings)

        # NOTE: A matrix learning disabled - see docstring for explanation

        # Action: always approach (except at final timestep)
        if t < model.T
            # Store action for learning (even though it's forced)
            push!(agent.actions, copy(approach_action))

            # Execute approach action in environment
            step!(env, approach_action)
        end
    end

    # Update pD based on FINAL beliefs (at end of trial)
    # This is crucial for static hidden states like "danger" that don't change
    # but need to be inferred from evidence collected during the trial
    if !isempty(learn_D)
        update_pD_final!(agent, settings.eta, learn_D)
    end

    return nothing
end

"""
    update_pD_final!(agent, eta, factors)

Update pD based on FINAL beliefs (at end of trial) rather than initial beliefs.

For static hidden states that don't change during a trial (like "danger"),
we want to update the prior based on all evidence collected during the trial,
not just the initial observation.
"""
function update_pD_final!(
    agent,
    eta::Real,
    factors::Vector{Int}
)
    T = length(agent.qs)  # Total timesteps
    qs_final = agent.qs[T]  # Final beliefs

    for f in factors
        Nf_actual = length(agent.pD)
        if f < 1 || f > Nf_actual
            @warn "Skipping invalid factor index $f (agent has $Nf_actual factors)"
            continue
        end

        # Update pD[f] with FINAL beliefs (not initial)
        for s in 1:length(agent.pD[f])
            agent.pD[f][s] += eta * qs_final[f][s]
        end
    end

    return nothing
end
