"""
    rxinfer_impl.jl - Active Inference Implementation using RxInfer.jl

This provides an active inference implementation of the spider phobia model
with proper Expected Free Energy (EFE) calculation and policy selection.

Key active inference components:
1. State inference via Bayesian filtering
2. Expected Free Energy calculation (ambiguity + utility)
3. Policy selection via softmax over negative EFE
4. Dirichlet learning for belief updating
"""

# Check if RxInfer.jl is available
const RXINFER_AVAILABLE = try
    @eval using RxInfer
    true
catch e
    @warn "RxInfer.jl not available: $e"
    false
end

# Action indices (must match model.jl action ordering)
const ACTION_APPROACH = 1
const ACTION_AVOID = 2

# Number of policies (approach, avoid)
const N_POLICIES = 2

"""
    one_hot(idx::Int, n::Int)

Convert integer index to one-hot vector representation.
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
    entropy(p::Vector{Float64})

Calculate entropy H(p) = -Σ p(x) log p(x)
"""
function entropy(p::Vector{Float64})
    H = 0.0
    for pi in p
        if pi > 1e-16
            H -= pi * log(pi)
        end
    end
    return H
end

"""
    softmax(x::Vector{Float64}; tau::Float64=1.0)

Softmax function with temperature parameter.
"""
function softmax(x::Vector{Float64}; tau::Float64=1.0)
    x_scaled = x ./ tau
    x_max = maximum(x_scaled)
    exp_x = exp.(x_scaled .- x_max)
    return exp_x ./ sum(exp_x)
end

"""
    build_rxinfer_matrices(; params::ModelParams = ModelParams())

Build matrices in the format expected for active inference.
Includes transition matrices for each action and preference vectors.
"""
function build_rxinfer_matrices(; params::ModelParams = ModelParams())
    # Get the base model
    model = build_model(params=params)

    # State dimensions
    Ns = model.Ns  # [6, 2, 2] = behavior, spider, danger
    No = model.No  # [2, 2, 3, 6] = visual, arousal, affect, behavior_obs

    # Total flattened state space size
    n_states_flat = prod(Ns)  # 6 * 2 * 2 = 24

    # Build flattened transition matrix for approach action
    B_approach = zeros(n_states_flat, n_states_flat)
    for s_flat in 1:n_states_flat
        s = unflatten_state(s_flat, Ns)
        s_next_probs = zeros(n_states_flat)
        for s_next_flat in 1:n_states_flat
            s_next = unflatten_state(s_next_flat, Ns)
            prob = 1.0
            for f in 1:length(Ns)
                a = min(ACTION_APPROACH, size(model.B[f], 3))
                prob *= model.B[f][s_next[f], s[f], a]
            end
            s_next_probs[s_next_flat] = prob
        end
        if sum(s_next_probs) > 0
            B_approach[:, s_flat] = s_next_probs ./ sum(s_next_probs)
        else
            B_approach[:, s_flat] = ones(n_states_flat) ./ n_states_flat
        end
    end

    # Build flattened transition matrix for avoid action
    B_avoid = zeros(n_states_flat, n_states_flat)
    for s_flat in 1:n_states_flat
        s = unflatten_state(s_flat, Ns)
        s_next_probs = zeros(n_states_flat)
        for s_next_flat in 1:n_states_flat
            s_next = unflatten_state(s_next_flat, Ns)
            prob = 1.0
            for f in 1:length(Ns)
                a = min(ACTION_AVOID, size(model.B[f], 3))
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

    # Collect transition matrices indexed by action
    B_actions = [B_approach, B_avoid]

    # Build flattened observation matrices
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
    d_flat = d_flat ./ maximum(d_flat) .+ 0.1

    # Preference vectors (log preferences, higher = more preferred)
    # C[g][o] = log P(o) where P encodes preferences
    C_flat = Vector{Vector{Float64}}(undef, length(No))
    for g in 1:length(No)
        # model.C contains log preferences (positive = preferred)
        C_flat[g] = model.C[g][:, 1]
    end

    # Policy prior E (uniform over approach/avoid)
    E = ones(N_POLICIES) ./ N_POLICIES

    return (
        A = A_flat,
        B = B_approach,  # Default B for backward compatibility
        B_approach = B_approach,
        B_avoid = B_avoid,
        B_actions = B_actions,
        D = D_flat,
        d = d_flat,
        C = C_flat,
        E = E,
        n_states = n_states_flat,
        No = No,
        Ns = Ns,
        T = params.T,
        params = params
    )
end

# Only define inference functions if RxInfer is available
if RXINFER_AVAILABLE

using RxInfer

"""
    calculate_expected_free_energy(qs::Vector{Float64}, A, C, B_action, T::Int)

Calculate Expected Free Energy (EFE) for a single action/policy.

G = Σ_τ [ ambiguity + risk ]
  = Σ_τ [ E_Q[H[P(o|s)]] - E_Q[log P(o|C)] ]

Where:
- Ambiguity: Expected entropy of observations given predicted states
- Risk: Expected negative log preference (negative utility)

Arguments:
- qs: Current state belief
- A: Observation likelihood matrices (one per modality)
- C: Log preference vectors (one per modality)
- B_action: Transition matrix for this action
- T: Planning horizon
"""
function calculate_expected_free_energy(
    qs::Vector{Float64},
    A::Vector{Matrix{Float64}},
    C::Vector{Vector{Float64}},
    B_action::Matrix{Float64},
    T::Int
)
    G = 0.0
    qs_future = copy(qs)

    for tau in 1:(T-1)
        # Predict next state under this action
        qs_next = B_action * qs_future
        qs_next = qs_next ./ (sum(qs_next) + 1e-16)

        # For each observation modality
        for g in 1:length(A)
            A_g = A[g]
            C_g = C[g]

            # Expected observation distribution: Q(o) = Σ_s Q(s) P(o|s)
            qo = A_g * qs_next
            qo = qo ./ (sum(qo) + 1e-16)

            # Ambiguity: E_Q[H[P(o|s)]] = Σ_s Q(s) H[P(o|s)]
            # This is the expected entropy of observations given state uncertainty
            ambiguity = 0.0
            for s in 1:length(qs_next)
                if qs_next[s] > 1e-16
                    # Entropy of P(o|s) for this state
                    po_given_s = A_g[:, s]
                    H_o_given_s = entropy(po_given_s)
                    ambiguity += qs_next[s] * H_o_given_s
                end
            end

            # Risk: -E_Q[log P(o|C)] = -Σ_o Q(o) log P(o|C)
            # C contains log preferences, so risk = -Σ_o Q(o) C(o)
            # Negative because we want to minimize EFE and maximize utility
            risk = 0.0
            for o in 1:length(qo)
                if qo[o] > 1e-16
                    risk -= qo[o] * C_g[o]  # Negative of expected log preference
                end
            end

            G += ambiguity + risk
        end

        qs_future = qs_next
    end

    return G
end

"""
    infer_policies(qs::Vector{Float64}, matrices; gamma::Float64=1.0)

Compute posterior over policies using Expected Free Energy.

Q(π) ∝ P(π) exp(-γ G(π))

Returns:
- qpi: Posterior probability over policies [P(approach), P(avoid)]
- G: Expected free energy for each policy
"""
function infer_policies(qs::Vector{Float64}, matrices; gamma::Float64=1.0)
    G = zeros(N_POLICIES)

    # Calculate EFE for each policy
    for pi in 1:N_POLICIES
        B_action = matrices.B_actions[pi]
        G[pi] = calculate_expected_free_energy(qs, matrices.A, matrices.C, B_action, matrices.T)
    end

    # Policy posterior with prior E
    log_E = log.(matrices.E .+ 1e-16)
    qpi = softmax(-gamma .* G .+ log_E)

    return qpi, G
end

"""
    sample_action(qpi::Vector{Float64})

Sample an action from the policy posterior.
Returns ACTION_APPROACH (1) or ACTION_AVOID (2).
"""
function sample_action(qpi::Vector{Float64})
    r = rand()
    if r < qpi[1]
        return ACTION_APPROACH
    else
        return ACTION_AVOID
    end
end

"""
    run_rxinfer_state_inference(; observation, params=ModelParams())

Run single-timestep state inference using Bayesian update.
"""
function run_rxinfer_state_inference(; observation::Vector{Int}, params::ModelParams = ModelParams())
    matrices = build_rxinfer_matrices(params=params)

    # Validate observation indices
    for g in 1:length(matrices.No)
        if observation[g] < 1 || observation[g] > matrices.No[g]
            error("Observation[$g] = $(observation[g]) out of range [1, $(matrices.No[g])]")
        end
    end

    # Prior over state from D
    prior = copy(matrices.D)

    # Likelihood for each modality
    lik = ones(matrices.n_states)
    for g in 1:length(matrices.No)
        A_g = matrices.A[g]
        obs_idx = observation[g]
        lik .*= A_g[obs_idx, :]
    end

    # Posterior via Bayes
    posterior = prior .* lik
    posterior ./= sum(posterior) + 1e-16

    return (
        qs = posterior,
        D = matrices.D,
        matrices = matrices
    )
end

"""
    run_rxinfer_exposure_therapy(; n_trials=200, spider_dangerous=false, params=ModelParams(),
                                   low_concentration=false, exposure_mode=false, gamma=1.0)

Run exposure therapy simulation using proper Active Inference.

Key active inference components:
1. State inference via Bayesian filtering
2. Expected Free Energy (EFE) calculation with ambiguity + utility terms
3. Policy selection via softmax over negative EFE
4. Dirichlet learning for belief updating

Arguments:
- n_trials: Number of exposure trials
- spider_dangerous: Whether the spider is actually dangerous
- params: Model parameters
- low_concentration: Use weak priors for faster learning
- exposure_mode: If true, force approach actions (bypass EFE-based selection)
- gamma: Policy precision (inverse temperature for action selection)
"""
function run_rxinfer_exposure_therapy(;
    n_trials::Int = 200,
    spider_dangerous::Bool = false,
    params::ModelParams = ModelParams(),
    low_concentration::Bool = false,
    exposure_mode::Bool = false,
    gamma::Float64 = 1.0
)
    matrices = build_rxinfer_matrices(params=params)

    # Initial d prior (Dirichlet concentration parameters)
    d_prior = if low_concentration
        ones(matrices.n_states) .+ 0.1
    else
        copy(matrices.d)
    end

    # Track evolution
    d_evolution = Vector{Float64}[]
    approach_count = 0
    avoid_count = 0
    efe_history = Vector{Float64}[]  # Track EFE values

    # Ground truth danger state
    danger_idx = spider_dangerous ? 1 : 2

    mode_str = exposure_mode ? "exposure mode (forced approach)" : "active inference (EFE-based)"
    @info "RxInfer Active Inference agent initialized" n_states=matrices.n_states mode=mode_str gamma=gamma

    for trial in 1:n_trials
        # Track observations and states for this trial
        observations = Vector{Int}[]
        true_states = Int[]
        actions = Int[]

        # Initial state: start position, spider present, danger status
        true_state_multi = [1, 2, danger_idx]
        true_state = flatten_state(true_state_multi, matrices.Ns)
        push!(true_states, true_state)

        # Current belief state (from learned prior)
        qs = d_prior ./ sum(d_prior)

        for t in 1:params.T
            # Generate observation for each modality
            obs = Int[]
            for g in 1:length(matrices.No)
                probs = matrices.A[g][:, true_state]
                probs = probs ./ (sum(probs) + 1e-16)
                # Sample from categorical
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
            push!(observations, obs)

            # State inference: update belief given observation
            lik = ones(matrices.n_states)
            for g in 1:length(matrices.No)
                lik .*= matrices.A[g][obs[g], :]
            end
            qs = qs .* lik
            qs = qs ./ (sum(qs) + 1e-16)

            # Action selection (only at timesteps before T)
            if t < params.T
                if exposure_mode
                    # Exposure therapy: force approach
                    action = ACTION_APPROACH
                else
                    # Active inference: select action via EFE
                    qpi, G = infer_policies(qs, matrices; gamma=gamma)
                    action = sample_action(qpi)

                    # Store EFE for first timestep of first trial for debugging
                    if trial == 1 && t == 1
                        push!(efe_history, G...)
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

                # Predict next state belief
                qs = B_action * qs
                qs = qs ./ (sum(qs) + 1e-16)
            end
        end

        # Learning: update d_prior based on trial experience
        # Use average belief across all timesteps as learning signal
        # Recompute filtered beliefs for learning
        prior = d_prior ./ sum(d_prior)
        filtered_beliefs = Vector{Vector{Float64}}()

        for t in 1:params.T
            # Prediction
            if t == 1
                predicted = prior
            else
                action = actions[t-1]
                B_action = matrices.B_actions[action]
                predicted = B_action * filtered_beliefs[t-1]
            end
            predicted = predicted ./ (sum(predicted) + 1e-16)

            # Update with observation
            lik = ones(matrices.n_states)
            for g in 1:length(matrices.No)
                lik .*= matrices.A[g][observations[t][g], :]
            end
            posterior = predicted .* lik
            posterior = posterior ./ (sum(posterior) + 1e-16)
            push!(filtered_beliefs, posterior)
        end

        # Update d_prior using average belief
        avg_belief = sum(filtered_beliefs) ./ length(filtered_beliefs)
        eta = 0.5  # Learning rate
        d_prior = d_prior .+ eta .* avg_belief

        # Store current d_prior
        push!(d_evolution, copy(d_prior))

        if trial % 50 == 0
            @info "RxInfer Trial $trial/$n_trials" approach=approach_count avoid=avoid_count
        end
    end

    return (
        d_evolution = d_evolution,
        approach_count = approach_count,
        avoid_count = avoid_count,
        n_trials = n_trials,
        matrices = matrices,
        efe_history = efe_history
    )
end

end  # if RXINFER_AVAILABLE

# Export functions
export RXINFER_AVAILABLE,
       build_rxinfer_matrices,
       one_hot,
       flatten_state,
       unflatten_state,
       entropy,
       softmax

if RXINFER_AVAILABLE
    export run_rxinfer_state_inference,
           run_rxinfer_exposure_therapy,
           calculate_expected_free_energy,
           infer_policies,
           sample_action
end
