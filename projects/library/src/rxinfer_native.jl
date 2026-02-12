"""
    rxinfer_native.jl - Native RxInfer Factor Graph Models for Active Inference

This module provides native RxInfer models using DiscreteTransition nodes
for proper variational message passing. The factor graph structure enables:

1. State inference via belief propagation (Bayesian filtering)
2. Dirichlet learning for belief updating over trials
3. Multi-modality observation handling

Key models:
- `spider_perception_model`: Single timestep perception (state inference from obs)
- `spider_temporal_model`: Multi-timestep HMM for temporal inference
- `spider_prior_learning_model`: Learns initial state beliefs over trials

Note: Expected Free Energy (EFE) calculation and policy selection remain
external since they require planning over hypothetical futures, which isn't
directly supported by standard variational message passing.
"""

# Only load if RxInfer is available
if RXINFER_AVAILABLE

using RxInfer

# ============================================================================
# Model Definitions
# ============================================================================

"""
    spider_perception_model(obs, A, prior_state)

Single-timestep perception model for state inference.

Given observations from multiple modalities (visual, arousal, affect, behavior),
infer the hidden state (combined behavior x spider x danger).

Arguments:
- obs: Vector of observation vectors, one per modality
- A: Vector of observation likelihood matrices, one per modality
- prior_state: Prior belief over states (from D or previous inference)
"""
RxInfer.@model function spider_perception_model(obs, A, prior_state)
    # Hidden state with prior
    s ~ Categorical(prior_state)

    # Multi-modality observations
    for g in 1:length(A)
        obs[g] ~ DiscreteTransition(s, A[g])
    end
end

"""
    spider_temporal_model(obs, A, B, prior_state)

Multi-timestep HMM for temporal state inference.

Performs Bayesian filtering/smoothing over a sequence of observations,
given a fixed transition matrix B (action already selected).

Arguments:
- obs: Vector of observations for each timestep, each containing multi-modal obs
- A: Observation likelihood matrices (Vector of matrices, one per modality)
- B: Transition matrix for the selected action
- prior_state: Initial state prior
"""
RxInfer.@model function spider_temporal_model(y_flat, A_combined, B, prior_state)
    # For now, using a simplified single-modality combined observation
    # y_flat is a vector of one-hot observations for each timestep
    s_prev = prior_state
    for t in 1:length(y_flat)
        s[t] ~ DiscreteTransition(s_prev, B)
        y_flat[t] ~ DiscreteTransition(s[t], A_combined)
        s_prev = s[t]
    end
end

"""
    spider_prior_learning_model(s_observations, d_prior)

Learn the initial state prior D from observed state sequences.

Used for Dirichlet-Categorical conjugate learning of the initial state
distribution. Updates after each trial based on the inferred initial state.

Arguments:
- s_observations: Vector of one-hot state observations (initial states from each trial)
- d_prior: Dirichlet prior concentrations
"""
RxInfer.@model function spider_prior_learning_model(s_observations, d_prior)
    D ~ Dirichlet(d_prior)
    for t in 1:length(s_observations)
        s_observations[t] ~ Categorical(D)
    end
end

# ============================================================================
# Inference Functions
# ============================================================================

"""
    infer_state_rxinfer(observations, A, prior_state)

Infer hidden state from multi-modal observations using RxInfer message passing.

Returns:
- qs: Posterior belief over states (probability vector)
- result: Full RxInfer inference result
"""
function infer_state_rxinfer(observations::Vector{Vector{Float64}},
                              A::Vector{Matrix{Float64}},
                              prior_state::Vector{Float64})
    # Run inference
    result = RxInfer.infer(
        model = spider_perception_model(A=A, prior_state=prior_state),
        data = (obs = observations,)
    )

    # Extract state posterior as probability vector
    s_posterior = result.posteriors[:s]
    qs = probvec(s_posterior)

    return qs, result
end

"""
    infer_temporal_state_rxinfer(observations, A_combined, B, prior_state)

Run temporal state inference over a sequence of observations.

Arguments:
- observations: Vector of observation vectors (one per timestep)
- A_combined: Combined observation likelihood matrix
- B: Transition matrix for selected action
- prior_state: Initial state prior

Returns:
- qs_sequence: Vector of state posteriors (one per timestep)
- result: Full RxInfer inference result
"""
function infer_temporal_state_rxinfer(observations::Vector{Vector{Float64}},
                                       A_combined::Matrix{Float64},
                                       B::Matrix{Float64},
                                       prior_state::Vector{Float64})
    result = RxInfer.infer(
        model = spider_temporal_model(A_combined=A_combined, B=B, prior_state=prior_state),
        data = (y_flat = observations,)
    )

    # Extract state posteriors for each timestep
    s_posteriors = result.posteriors[:s]
    qs_sequence = [probvec(s_t) for s_t in s_posteriors]

    return qs_sequence, result
end

"""
    learn_prior_rxinfer(s_observations, d_prior; iterations=10)

Learn initial state prior D from observed initial states using Dirichlet-Categorical
conjugate inference.

Arguments:
- s_observations: Vector of one-hot initial state observations
- d_prior: Current Dirichlet prior concentrations

Returns:
- d_posterior: Updated Dirichlet concentrations
- D_mean: Expected value of the Dirichlet (normalized state prior)
"""
function learn_prior_rxinfer(s_observations::Vector{Vector{Float64}},
                              d_prior::Vector{Float64};
                              iterations::Int=10)
    result = RxInfer.infer(
        model = spider_prior_learning_model(d_prior=d_prior),
        data = (s_observations = s_observations,),
        iterations = iterations
    )

    # Extract Dirichlet posterior
    D_posterior = last(result.posteriors[:D])

    # Get the Dirichlet alpha parameters (concentrations)
    d_posterior = D_posterior.alpha

    # Expected value (normalized prior)
    D_mean = d_posterior ./ sum(d_posterior)

    return d_posterior, D_mean
end

# ============================================================================
# Observation Likelihood Learning (External Dirichlet Updates)
# ============================================================================

#=
DESIGN DECISION: External vs In-Graph Learning for Observation Matrix A

We use EXTERNAL (closed-form) Dirichlet updates for learning A rather than
in-graph learning with DirichletCollection. Here's why:

TRADEOFF ANALYSIS:

External A (what we use):
  ✓ Simple to implement and debug - inspect counts/α directly
  ✓ Faster - no extra nodes in factor graph
  ✓ Matches existing pattern (external EFE, trial-by-trial updates)
  ✓ Easier unit tests - verify closed-form updates with known counts
  ✗ A is fixed during each inference pass (no posterior coupling)
  ✗ Splits logic across model code and loop code

In-graph A (DirichletCollection):
  ✓ Mathematically "pure" end-to-end probabilistic program
  ✓ Uncertainty about A can propagate to other variables
  ✓ Cleaner path to joint inference with other latent structure
  ✗ Stack overflow with DiscreteTransition in RxInfer 4.6 (the immediate issue)
  ✗ More complex graph, harder to debug when learning stalls
  ✗ Performance hit from additional nodes and messages

WHEN IN-GRAPH WOULD BE WORTH IT:
  - Need posterior uncertainty over A to influence other latents within
    a single inference pass
  - Hierarchical priors on A
  - Joint inference coupling between A and other model parameters
  - Moving toward full variational learning in RxInfer

For our exposure therapy simulation with sequential trials and external EFE,
the closed-form Dirichlet update is mathematically identical and much simpler.
=#

"""
    learn_likelihood_external(a_prior, observations, states)

Learn observation likelihood matrix A using closed-form Dirichlet updates.

This performs the same Bayesian update as in-graph DirichletCollection learning,
but computed externally for simplicity and stability. The Dirichlet-Categorical
conjugacy gives us: α_posterior = α_prior + counts

Arguments:
- a_prior: Matrix of Dirichlet prior concentrations (n_obs × n_states)
- observations: Vector of one-hot observation vectors
- states: Vector of one-hot state vectors (known or inferred)

Returns:
- a_posterior: Updated Dirichlet concentration matrix
- A_mean: Expected value of A (normalized likelihood matrix, columns sum to 1)

Example:
```julia
# 2 observations, 3 states, uniform prior
a_prior = ones(2, 3)
obs = [[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]]  # observations over time
states = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]]  # known states

a_post, A = learn_likelihood_external(a_prior, obs, states)
# A[:,1] learned from obs when in state 1, etc.
```
"""
function learn_likelihood_external(
    a_prior::Matrix{Float64},
    observations::Vector{Vector{Float64}},
    states::Vector{Vector{Float64}}
)
    # Accumulate counts: outer product of observation × state at each timestep
    # counts[o, s] = how often we saw observation o when in state s
    counts = zeros(size(a_prior))
    for t in eachindex(observations)
        # Outer product: obs (column) × state (row transposed) = obs × state matrix
        counts .+= observations[t] * states[t]'
    end

    # Dirichlet posterior: α_post = α_prior + counts
    a_posterior = a_prior .+ counts

    # Expected value of Dirichlet (mean of the posterior)
    # Normalize columns so each state's observation distribution sums to 1
    A_mean = a_posterior ./ sum(a_posterior, dims=1)

    return a_posterior, A_mean
end

"""
    learn_likelihood_multi_modality(a_priors, observations, states)

Learn observation likelihood matrices for multiple modalities.

Arguments:
- a_priors: Vector of prior matrices, one per modality
- observations: Vector of observation tuples (one tuple per timestep,
               each tuple contains one-hot obs for each modality)
- states: Vector of one-hot state vectors

Returns:
- a_posteriors: Vector of updated Dirichlet concentration matrices
- A_means: Vector of expected likelihood matrices
"""
function learn_likelihood_multi_modality(
    a_priors::Vector{Matrix{Float64}},
    observations::Vector{Vector{Vector{Float64}}},
    states::Vector{Vector{Float64}}
)
    n_modalities = length(a_priors)
    a_posteriors = Vector{Matrix{Float64}}(undef, n_modalities)
    A_means = Vector{Matrix{Float64}}(undef, n_modalities)

    for g in 1:n_modalities
        # Extract observations for this modality across all timesteps
        obs_g = [observations[t][g] for t in eachindex(observations)]
        a_posteriors[g], A_means[g] = learn_likelihood_external(a_priors[g], obs_g, states)
    end

    return a_posteriors, A_means
end

# ============================================================================
# Hybrid Active Inference Loop
# ============================================================================

"""
    run_rxinfer_native_therapy(; n_trials=200, spider_dangerous=true,
                                params=ModelParams(), exposure_mode=false, gamma=1.0)

Run active inference therapy simulation using native RxInfer for state inference.

This is a hybrid approach:
- State inference: RxInfer message passing
- EFE calculation: External (pymdp-style calculation)
- Policy selection: Softmax over negative EFE
- Learning: RxInfer Dirichlet-Categorical conjugate updates

Arguments:
- n_trials: Number of therapy trials
- spider_dangerous: Ground truth spider danger status
- params: Model parameters
- exposure_mode: If true, force approach actions (exposure therapy)
- gamma: Precision of policy selection (higher = more deterministic)

Returns:
- Named tuple with evolution of beliefs, actions, and approach/avoid counts
"""
function run_rxinfer_native_therapy(;
    n_trials::Int = 200,
    spider_dangerous::Bool = true,
    params::ModelParams = ModelParams(),
    exposure_mode::Bool = false,
    gamma::Float64 = 1.0
)
    # Build matrices
    matrices = build_rxinfer_matrices(params=params)
    n_states = matrices.n_states

    # === SEPARATE GENERATIVE MODEL FROM RECOGNITION MODEL ===
    # A_world: The "true" observation model used to generate observations
    #          This is FIXED and represents how the world actually works
    # A_agent: The agent's BELIEFS about the observation model
    #          This is LEARNED through experience
    #
    # Without this separation, A learning creates a feedback loop where
    # observations generated by the current A reinforce those same beliefs.
    A_world = deepcopy(matrices.A)  # Fixed - never modified during simulation

    # Initialize D prior (uniform)
    d_prior = ones(n_states)
    D_mean = d_prior ./ sum(d_prior)

    # Initialize A priors for learnable modalities
    # We learn modality 3 (affect) to match the original paper model
    a_priors = [copy(A_g) .+ 1.0 for A_g in matrices.A]  # Add 1 for proper Dirichlet
    modalities_to_learn = [3]  # Only learn affect modality (matches paper)

    # A_agent: Current agent beliefs about observation likelihoods
    # Derived from a_priors, updated during learning
    A_agent = [a_priors[g] ./ sum(a_priors[g], dims=1) for g in 1:length(matrices.A)]

    # Track evolution
    d_evolution = Vector{Float64}[]
    a_evolution = Matrix{Float64}[]  # Track A[3] evolution
    approach_count = 0
    avoid_count = 0
    efe_history = Vector{Float64}[]

    # Initial state observations for learning (accumulated over trials)
    initial_state_obs = Vector{Float64}[]

    # Accumulated observations for A learning (across trials)
    trial_observations = Vector{Vector{Vector{Float64}}}()  # Per-trial observations
    trial_state_beliefs = Vector{Vector{Vector{Float64}}}()  # Per-trial state beliefs

    # Ground truth danger state
    danger_idx = spider_dangerous ? 1 : 2

    mode_str = exposure_mode ? "exposure mode (forced approach)" : "active inference (EFE-based)"
    @info "RxInfer Native Active Inference agent initialized" n_states mode=mode_str gamma

    for trial in 1:n_trials
        # Initial true state: [behavior=1 (safe distance), spider=present, danger_idx]
        true_state_factors = [1, 1, danger_idx]
        true_state = flatten_state(true_state_factors, matrices.Ns)

        # Initialize beliefs using learned D
        qs = copy(D_mean)

        # Track states and actions
        true_states = Int[true_state]
        actions = Int[]

        # Track observations and beliefs for A learning this trial
        trial_obs = Vector{Vector{Float64}}[]
        trial_qs = Vector{Float64}[]

        # Run trial through timesteps
        for t in 1:params.T
            # Generate observation based on true state using FIXED world model
            obs = Vector{Float64}[]
            for g in 1:length(A_world)
                obs_probs = A_world[g][:, true_state]  # Use A_world, not A_agent!
                # Sample observation
                r = rand()
                cumprob = 0.0
                obs_idx = 1
                for i in 1:length(obs_probs)
                    cumprob += obs_probs[i]
                    if r <= cumprob
                        obs_idx = i
                        break
                    end
                end
                push!(obs, one_hot(obs_idx, matrices.No[g]))
            end

            # State inference using RxInfer with LEARNED agent beliefs
            qs, _ = infer_state_rxinfer(obs, A_agent, qs)

            # Store for A learning
            push!(trial_obs, obs)
            push!(trial_qs, copy(qs))

            # Action selection (only at timesteps before T)
            if t < params.T
                if exposure_mode
                    action = ACTION_APPROACH
                else
                    # Active inference: select action via EFE using LEARNED agent beliefs
                    matrices_agent = (A=A_agent, B_actions=matrices.B_actions, C=matrices.C, E=matrices.E, T=matrices.T)
                    qpi, G = infer_policies(qs, matrices_agent; gamma=gamma)
                    action = sample_action(qpi)

                    # Store EFE for first timestep of first trial for debugging
                    if trial == 1 && t == 1
                        push!(efe_history, G)
                    end
                end
                push!(actions, action)

                # Track approach/avoid
                if t == 1
                    if action == ACTION_APPROACH
                        approach_count += 1
                    else
                        avoid_count += 1
                    end
                end

                # Environment transition based on action
                B_action = matrices.B_actions[action]
                trans_probs = B_action[:, true_state]
                trans_probs = trans_probs ./ (sum(trans_probs) + 1e-16)
                r = rand()
                cumprob = 0.0
                next_state = 1
                for i in 1:length(trans_probs)
                    cumprob += trans_probs[i]
                    if r <= cumprob
                        next_state = i
                        break
                    end
                end
                true_state = next_state
                push!(true_states, true_state)

                # Update belief using transition model
                qs = B_action * qs
                qs = qs ./ (sum(qs) + 1e-16)
            end
        end

        # Learning: record initial state observation for D learning
        # Use the posterior belief at trial end as a soft observation
        push!(initial_state_obs, one_hot(true_states[1], n_states))

        # Periodically update D prior using accumulated observations
        if trial % 10 == 0 && length(initial_state_obs) >= 5
            # Use last N observations for learning
            recent_obs = initial_state_obs[max(1, end-19):end]
            d_prior, D_mean = learn_prior_rxinfer(recent_obs, d_prior)
        end

        # Store D evolution (extract danger-related beliefs)
        push!(d_evolution, copy(D_mean))

        # A learning: update observation likelihoods for learnable modalities
        # Use external Dirichlet update (see design notes in this file)
        # IMPORTANT: Update A_agent (learnable beliefs), NOT A_world (fixed generative model)
        eta_a = 0.5  # Learning rate for A
        for g in modalities_to_learn
            for t in eachindex(trial_obs)
                # Use SOFT state beliefs for learning (not argmax)
                # This is more Bayesian and avoids winner-take-all dynamics
                soft_state = trial_qs[t]  # Full probability distribution
                # Accumulate counts via outer product
                a_priors[g] .+= eta_a .* (trial_obs[t][g] * soft_state')
            end
            # Update A_agent (agent's learned beliefs), NOT A_world!
            A_agent[g] .= a_priors[g] ./ sum(a_priors[g], dims=1)
        end

        # Store A_agent[3] evolution (the learned beliefs, not the world)
        push!(a_evolution, copy(A_agent[3]))
    end

    # Compute final danger belief across all D states
    danger_belief = sum(D_mean[i] for i in 1:n_states
                        if unflatten_state(i, matrices.Ns)[3] == 1)  # danger=1

    return (
        d_evolution = d_evolution,
        a_evolution = a_evolution,
        approach_count = approach_count,
        avoid_count = avoid_count,
        efe_history = efe_history,
        final_danger_belief = danger_belief,
        final_D = D_mean,
        final_A = A_agent,  # Return learned agent beliefs, not fixed world model
        A_world = A_world   # Also expose the fixed world model for comparison
    )
end

end # if RXINFER_AVAILABLE
