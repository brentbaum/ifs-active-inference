"""
    rxinfer_impl.jl - Implementation using RxInfer.jl package

This provides an alternative implementation of the spider phobia model
using the RxInfer.jl package for reactive message passing inference.

RxInfer.jl handles the factor graph construction and variational inference
automatically through its @model macro.
"""

# Check if RxInfer.jl is available
const RXINFER_AVAILABLE = try
    @eval using RxInfer
    true
catch e
    @warn "RxInfer.jl not available: $e"
    false
end

"""
    one_hot(idx::Int, n::Int)

Convert integer index to one-hot vector representation.
RxInfer requires one-hot vectors for categorical observations.
"""
function one_hot(idx::Int, n::Int)
    v = zeros(n)
    v[idx] = 1.0
    return v
end

"""
    flatten_state(state::Vector{Int}, dims::Vector{Int})

Convert multi-factor state to single flattened index.
For the spider model: [behavior, spider, danger] -> single index
"""
function flatten_state(state::Vector{Int}, dims::Vector{Int})
    idx = 1
    multiplier = 1
    for i in length(dims):-1:1
        idx += (state[i] - 1) * multiplier
        multiplier *= dims[i]
    end
    return idx
end

"""
    unflatten_state(idx::Int, dims::Vector{Int})

Convert single flattened index back to multi-factor state.
"""
function unflatten_state(idx::Int, dims::Vector{Int})
    state = zeros(Int, length(dims))
    remaining = idx - 1
    for i in length(dims):-1:1
        state[i] = (remaining % dims[i]) + 1
        remaining = remaining ÷ dims[i]
    end
    return state
end

"""
    build_rxinfer_matrices(; params::ModelParams = ModelParams())

Build matrices in the format expected by RxInfer.jl.
RxInfer uses 2D matrices for transition/observation models.

For multi-factor states, we flatten the state space.
"""
function build_rxinfer_matrices(; params::ModelParams = ModelParams())
    # Get the base model
    model = build_model(params=params)

    # State dimensions
    Ns = model.Ns  # [6, 2, 2] = behavior, spider, danger
    No = model.No  # [2, 2, 3, 6] = visual, arousal, affect, behavior_obs

    # Total flattened state space size
    n_states_flat = prod(Ns)  # 6 * 2 * 2 = 24

    # Build flattened transition matrix for action 1 (approach)
    B_approach = zeros(n_states_flat, n_states_flat)
    for s_flat in 1:n_states_flat
        s = unflatten_state(s_flat, Ns)
        # Apply transition for each factor
        s_next_probs = zeros(n_states_flat)
        for s_next_flat in 1:n_states_flat
            s_next = unflatten_state(s_next_flat, Ns)
            prob = 1.0
            for f in 1:length(Ns)
                a = min(1, size(model.B[f], 3))  # Approach action
                prob *= model.B[f][s_next[f], s[f], a]
            end
            s_next_probs[s_next_flat] = prob
        end
        # Normalize
        if sum(s_next_probs) > 0
            B_approach[:, s_flat] = s_next_probs ./ sum(s_next_probs)
        else
            B_approach[:, s_flat] = ones(n_states_flat) ./ n_states_flat
        end
    end

    # Build flattened transition matrix for action 2 (avoid)
    B_avoid = zeros(n_states_flat, n_states_flat)
    for s_flat in 1:n_states_flat
        s = unflatten_state(s_flat, Ns)
        s_next_probs = zeros(n_states_flat)
        for s_next_flat in 1:n_states_flat
            s_next = unflatten_state(s_next_flat, Ns)
            prob = 1.0
            for f in 1:length(Ns)
                a = min(2, size(model.B[f], 3))  # Avoid action
                prob *= model.B[f][s_next[f], s[f], a]
            end
            s_next_probs[s_next_flat] = prob
        end
        if sum(s_next_probs) > 0
            B_avoid[:, s_flat] = s_next_probs ./ sum(s_next_probs)
        else
            B_avoid[:, s_flat] = ones(n_states_flat) ./ n_states_flat
        end
    end

    # Build flattened observation matrices
    # A[g] maps from flattened state to observation probabilities
    A_flat = Vector{Matrix{Float64}}(undef, length(No))
    for g in 1:length(No)
        A_flat[g] = zeros(No[g], n_states_flat)
        for s_flat in 1:n_states_flat
            s = unflatten_state(s_flat, Ns)
            A_flat[g][:, s_flat] = model.A[g][:, s...]
        end
        # Ensure columns sum to 1
        for col in 1:n_states_flat
            col_sum = sum(A_flat[g][:, col])
            if col_sum > 0
                A_flat[g][:, col] ./= col_sum
            else
                A_flat[g][:, col] .= 1.0 / No[g]
            end
        end
    end

    # Flattened initial state distribution
    D_flat = zeros(n_states_flat)
    for s_flat in 1:n_states_flat
        s = unflatten_state(s_flat, Ns)
        D_flat[s_flat] = prod(model.D[f][s[f]] for f in 1:length(Ns))
    end
    D_flat ./= sum(D_flat)

    # Flattened Dirichlet prior for D
    d_flat = zeros(n_states_flat)
    for s_flat in 1:n_states_flat
        s = unflatten_state(s_flat, Ns)
        d_flat[s_flat] = prod(model.d[f][s[f]] for f in 1:length(Ns))
    end
    # Scale down to reasonable concentration
    d_flat = d_flat ./ maximum(d_flat) .+ 0.1

    # Preference vector (negative log of preferred outcomes)
    # Higher values = less preferred
    C_flat = Vector{Vector{Float64}}(undef, length(No))
    for g in 1:length(No)
        # Use first column of C (time 1)
        C_flat[g] = -model.C[g][:, 1]  # Negative because RxInfer uses costs, not preferences
    end

    return (
        A = A_flat,
        B = B_approach,  # Default B for tests expecting :B key
        B_approach = B_approach,
        B_avoid = B_avoid,
        D = D_flat,
        d = d_flat,
        C = C_flat,
        n_states = n_states_flat,
        No = No,
        Ns = Ns,
        T = params.T,
        params = params
    )
end

# Only define models and inference functions if RxInfer is available
if RXINFER_AVAILABLE

# Import RxInfer types at module level
using RxInfer

"""
RxInfer model for spider phobia state inference.
Single timestep inference given observation.
"""
RxInfer.@model function spider_state_inference_model(y_visual, y_arousal, y_affect, y_behavior,
                                              A_visual, A_arousal, A_affect, A_behavior,
                                              d_prior)
    # Prior over flattened state
    D ~ Dirichlet(d_prior)
    s ~ Categorical(D)

    # Observations from each modality
    y_visual ~ Transition(s, A_visual)
    y_arousal ~ Transition(s, A_arousal)
    y_affect ~ Transition(s, A_affect)
    y_behavior ~ Transition(s, A_behavior)
end

"""
RxInfer model for spider phobia with transitions and learning.
Multi-timestep model with Dirichlet learning on D.
"""
RxInfer.@model function spider_learning_model(y_visual, y_arousal, y_affect, y_behavior,
                                       A_visual, A_arousal, A_affect, A_behavior,
                                       B, d_prior, T)
    # Learnable initial state prior
    D ~ Dirichlet(d_prior)

    # State sequence
    s = randomvar(T)
    s[1] ~ Categorical(D)
    for t in 2:T
        s[t] ~ Transition(s[t-1], B)
    end

    # Observations at each timestep
    for t in 1:T
        y_visual[t] ~ Transition(s[t], A_visual)
        y_arousal[t] ~ Transition(s[t], A_arousal)
        y_affect[t] ~ Transition(s[t], A_affect)
        y_behavior[t] ~ Transition(s[t], A_behavior)
    end
end

"""
    run_rxinfer_state_inference(; observation, params=ModelParams())

Run single-timestep state inference using RxInfer.
"""
function run_rxinfer_state_inference(; observation::Vector{Int}, params::ModelParams = ModelParams())
    matrices = build_rxinfer_matrices(params=params)

    # Convert observations to one-hot
    y_visual = one_hot(observation[1], matrices.No[1])
    y_arousal = one_hot(observation[2], matrices.No[2])
    y_affect = one_hot(observation[3], matrices.No[3])
    y_behavior = one_hot(observation[4], matrices.No[4])

    result = infer(
        model = spider_state_inference_model(
            A_visual = matrices.A[1],
            A_arousal = matrices.A[2],
            A_affect = matrices.A[3],
            A_behavior = matrices.A[4],
            d_prior = matrices.d
        ),
        data = (
            y_visual = y_visual,
            y_arousal = y_arousal,
            y_affect = y_affect,
            y_behavior = y_behavior
        ),
        iterations = 10
    )

    # Extract posterior
    D_posterior = last(result.posteriors[:D])
    s_posterior = last(result.posteriors[:s])

    return (
        qs = probvec(s_posterior),
        D = D_posterior,
        matrices = matrices
    )
end

"""
    run_rxinfer_exposure_therapy(; n_trials=200, spider_dangerous=false, params=ModelParams(), low_concentration=false)

Run exposure therapy simulation using RxInfer.jl package.
"""
function run_rxinfer_exposure_therapy(;
    n_trials::Int = 200,
    spider_dangerous::Bool = false,
    params::ModelParams = ModelParams(),
    low_concentration::Bool = false
)
    matrices = build_rxinfer_matrices(params=params)

    # Initial d prior
    d_prior = if low_concentration
        ones(matrices.n_states) .+ 0.1
    else
        copy(matrices.d)
    end

    # Track evolution (vector of d_prior per trial)
    d_evolution = Vector{Float64}[]
    approach_count = 0
    avoid_count = 0

    # Ground truth danger state
    danger_idx = spider_dangerous ? 1 : 2

    @info "RxInfer agent initialized with $(matrices.n_states) flattened states"

    for trial in 1:n_trials
        # Generate observations for a full trial (T timesteps)
        observations = Vector{Vector{Float64}}[]
        true_states = Int[]

        # Initial state: start position, spider present, danger status
        true_state_multi = [1, 2, danger_idx]
        true_state = flatten_state(true_state_multi, matrices.Ns)
        push!(true_states, true_state)

        for t in 1:params.T
            # Generate observation
            obs = Int[]
            for g in 1:length(matrices.No)
                probs = matrices.A[g][:, true_state]
                probs = probs ./ (sum(probs) + 1e-16)
                # Sample
                r = rand()
                cumprob = 0.0
                sampled = 1
                for i in 1:length(probs)
                    cumprob += probs[i]
                    if r <= cumprob
                        sampled = i
                        break
                    end
                end
                push!(obs, sampled)
            end

            # Convert to one-hot vectors
            obs_onehot = [one_hot(obs[g], matrices.No[g]) for g in 1:length(matrices.No)]
            push!(observations, vcat(obs_onehot...))

            # Exposure mode: force approach action
            action = 1  # Approach
            if t == 1
                approach_count += 1
            end

            # Transition (using approach matrix)
            if t < params.T
                trans_probs = matrices.B_approach[:, true_state]
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
            end
        end

        # Run inference for this trial
        try
            # Prepare observations
            y_visual = [one_hot(Int(observations[t][1] > 0.5 ? 1 : 2), matrices.No[1]) for t in 1:params.T]
            y_arousal = [one_hot(Int(observations[t][matrices.No[1]+1] > 0.5 ? 1 : 2), matrices.No[2]) for t in 1:params.T]
            y_affect_start = matrices.No[1] + matrices.No[2] + 1
            y_affect = [begin
                affect_obs = observations[t][y_affect_start:y_affect_start+matrices.No[3]-1]
                idx = argmax(affect_obs)
                one_hot(idx, matrices.No[3])
            end for t in 1:params.T]
            y_behavior = [begin
                beh_start = y_affect_start + matrices.No[3]
                beh_obs = observations[t][beh_start:end]
                idx = argmax(beh_obs)
                one_hot(idx, matrices.No[4])
            end for t in 1:params.T]

            result = infer(
                model = spider_learning_model(
                    A_visual = matrices.A[1],
                    A_arousal = matrices.A[2],
                    A_affect = matrices.A[3],
                    A_behavior = matrices.A[4],
                    B = matrices.B_approach,
                    d_prior = d_prior,
                    T = params.T
                ),
                data = (
                    y_visual = y_visual,
                    y_arousal = y_arousal,
                    y_affect = y_affect,
                    y_behavior = y_behavior
                ),
                iterations = 10
            )

            # Update d_prior from posterior
            D_posterior = last(result.posteriors[:D])
            d_prior = mean(D_posterior) .* sum(d_prior) .+ 0.1
            d_prior = d_prior ./ sum(d_prior) .* sum(matrices.d)

        catch e
            @debug "Inference error at trial $trial: $e"
        end

        # Store current d_prior (single vector per trial)
        push!(d_evolution, copy(d_prior))

        if trial % 50 == 0
            @info "RxInfer Trial $trial/$n_trials: Approach=$approach_count"
        end
    end

    return (
        d_evolution = d_evolution,
        approach_count = approach_count,
        avoid_count = avoid_count,
        n_trials = n_trials,
        matrices = matrices
    )
end

end  # if RXINFER_AVAILABLE

# Export functions
export RXINFER_AVAILABLE,
       build_rxinfer_matrices,
       one_hot,
       flatten_state,
       unflatten_state
if RXINFER_AVAILABLE
    export run_rxinfer_state_inference,
           run_rxinfer_exposure_therapy
end
