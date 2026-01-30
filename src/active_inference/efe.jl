"""
    efe.jl - Expected Free Energy calculation

We follow pymdp's convention where G is the *negative* expected free energy
to be *maximized* (policies with higher G are more likely):

G(π) = Σ_τ [expected_utility(τ) + state_info_gain(τ) + param_info_gain(τ) - ambiguity(τ)]

Where:
- expected_utility = E_{q(o|π,τ)}[log softmax(C(o,τ))] (negative log-preferences)
- state_info_gain = E_{q(o|π,τ)}[D_KL[q(s|o,π,τ) || q(s|π,τ)]] (Bayesian surprise)
- param_info_gain = expected KL between posterior and prior Dirichlet parameters
- ambiguity = E_{q(s|π,τ)}[H[P(o|s)]] (expected entropy of observations)

Note: pymdp converts C to log-probabilities via softmax before computing utility.
Since log_C is negative (log of probabilities), utilities are relative.
"""

using LinearAlgebra: dot

# Cache for softmax-transformed C matrices to avoid recomputation
const C_LOG_CACHE = Dict{UInt64, Vector{Matrix{Float64}}}()

"""
    get_log_C(C::Vector{<:Matrix})

Get log(softmax(C)) for utility computation.
Matches pymdp's calc_expected_utility which does:
  C_prob = softmax(C)
  lnC = log(C_prob)
  utility = sum(qo .* lnC)
"""
function get_log_C(C::Vector{<:Matrix{T}}) where T
    # Check cache
    key = hash(C)
    if haskey(C_LOG_CACHE, key)
        return C_LOG_CACHE[key]
    end

    log_C = Vector{Matrix{T}}(undef, length(C))
    for g in 1:length(C)
        log_C[g] = similar(C[g])
        for t in 1:size(C[g], 2)
            c_t = C[g][:, t]
            c_prob = softmax(c_t)
            log_C[g][:, t] = log.(c_prob .+ eps(T))
        end
    end

    # Cache result (limit cache size)
    if length(C_LOG_CACHE) > 100
        empty!(C_LOG_CACHE)
    end
    C_LOG_CACHE[key] = log_C

    return log_C
end

"""
    calculate_efe(agent, model, policy_idx, settings)

Calculate Expected Free Energy for a policy from current timestep onwards.

# Arguments
- `agent`: AIFAgent with current beliefs
- `model`: AIFModel
- `policy_idx`: Index of policy to evaluate
- `settings`: AIFSettings controlling which terms to include
"""
function calculate_efe(
    agent::AIFAgent{T},
    model::AIFModel{T,Nf},
    policy_idx::Int,
    settings::AIFSettings;
    sophisticated::Bool=false  # Match pymdp: no counterfactual observation branching
) where {T, Nf}

    policy = view(model.policies.V, :, policy_idx, :)  # (horizon, n_factors)

    # Get current A (possibly learned)
    A = get_A_from_pA(agent.pA)
    B = get_B_from_pB(agent.pB)

    # Get log(softmax(C)) for utility computation (pymdp formulation)
    log_C = get_log_C(model.C)

    # Calculate remaining horizon starting from current timestep
    # At t=1, we evaluate actions at τ=1,2,...,horizon
    # At t=2, we evaluate actions at τ=2,...,horizon
    start_τ = agent.t

    if sophisticated
        # Use counterfactual EFE: average over possible observation sequences
        return calculate_efe_counterfactual(agent, model, policy, A, B, log_C, settings, start_τ)
    else
        # Simple EFE without accounting for belief updates from observations
        return calculate_efe_simple(agent, model, policy, A, log_C, settings, start_τ)
    end
end

"""
    calculate_efe_simple(agent, model, policy, A, log_C, settings, start_τ)

Simple EFE calculation without sophisticated inference.
Beliefs are only propagated through transitions, not updated by observations.
Starts from policy timestep `start_τ` to handle mid-trial policy evaluation.

Uses pymdp formulation where utility = E[log(softmax(C))].
"""
function calculate_efe_simple(
    agent::AIFAgent{T},
    model::AIFModel{T,Nf},
    policy::AbstractMatrix{Int},
    A::Vector{<:Array},
    log_C::Vector{<:Matrix},
    settings::AIFSettings,
    start_τ::Int
) where {T, Nf}

    horizon = size(policy, 1)

    # Forward simulate from current beliefs for remaining timesteps
    qs_pred = forward_simulate_from(agent, model, policy, start_τ)

    G = zero(T)

    # Evaluate EFE from start_τ to horizon
    for idx in 1:(horizon - start_τ + 1)
        τ = start_τ + idx - 1
        t_future = agent.t + idx  # Time in trial

        if t_future > model.T
            break
        end

        qs_τ = qs_pred[idx]
        qs_prev = idx == 1 ? agent.qs[agent.t] : qs_pred[idx - 1]

        for g in 1:model.Ng
            qo_τ_g = compute_predicted_obs(A[g], qs_τ, model.Ns)

            if settings.use_ambiguity
                G += compute_ambiguity(A[g], qs_τ, model.Ns)
            end

            if settings.use_utility
                # pymdp formulation: utility = E[log(softmax(C))]
                log_C_τ = view(log_C[g], :, t_future)
                G += dot(qo_τ_g, log_C_τ)
            end

            if settings.use_states_info_gain
                G += compute_state_info_gain(A[g], qs_τ, qo_τ_g, model.Ns)
            end
        end

        if settings.use_param_info_gain
            weight = settings.param_info_gain_weight
            G += weight * compute_param_info_gain_A(agent, model, qs_τ, A, settings)
            G += weight * compute_param_info_gain_B(agent, model, qs_prev, qs_τ, policy, τ, settings)
        end
    end

    return G
end

"""
    calculate_efe_counterfactual(agent, model, policy, A, B, log_C, settings, start_τ)

Counterfactual EFE: For each timestep, branch over possible observations,
update beliefs accordingly, and average the EFE over branches.

This properly accounts for how observations at τ reduce uncertainty at τ+1.
Starts from policy timestep `start_τ` to handle mid-trial policy evaluation.

Uses pymdp formulation where utility = E[log(softmax(C))].
"""
function calculate_efe_counterfactual(
    agent::AIFAgent{T},
    model::AIFModel{T,Nf},
    policy::AbstractMatrix{Int},
    A::Vector{<:Array},
    B::Vector{<:Array},
    log_C::Vector{<:Matrix},
    settings::AIFSettings,
    start_τ::Int
) where {T, Nf}

    horizon = size(policy, 1)

    # Recursive computation: for each branch of observations, compute EFE
    # Start with current beliefs
    qs_current = [copy(agent.qs[agent.t][f]) for f in 1:Nf]

    return efe_counterfactual_recursive(
        qs_current, start_τ, horizon, policy, A, B, log_C, model, settings, agent.t, start_τ,
        agent.pA, agent.pB
    )
end

"""
Recursively compute counterfactual EFE by branching over observations.

Parameters:
- τ: Current policy timestep being evaluated
- start_τ: Initial policy timestep (used to compute trial time offset)

Uses pymdp formulation where utility = E[log(softmax(C))].
"""
function efe_counterfactual_recursive(
    qs::Vector{Vector{T}},
    τ::Int,
    horizon::Int,
    policy::AbstractMatrix{Int},
    A::Vector{<:Array},
    B::Vector{<:Array},
    log_C::Vector{<:Matrix},
    model::AIFModel{T,Nf},
    settings::AIFSettings,
    current_t::Int,
    start_τ::Int,
    pA::Vector{<:Array},
    pB::Vector{<:Array}
) where {T, Nf}

    if τ > horizon
        return zero(T)
    end

    # Compute trial time: each step from start_τ advances time by 1
    steps_taken = τ - start_τ + 1
    t_future = current_t + steps_taken
    if t_future > model.T
        return zero(T)
    end

    # Apply transition to get beliefs at this timestep
    qs_τ = Vector{Vector{T}}(undef, Nf)
    for f in 1:Nf
        action = clamp(policy[τ, f], 1, model.Na[f])
        qs_τ[f] = B[f][:, :, action] * qs[f]
    end

    # Compute EFE terms for this timestep
    G_τ = zero(T)

    for g in 1:model.Ng
        qo_g = compute_predicted_obs(A[g], qs_τ, model.Ns)

        if settings.use_ambiguity
            G_τ += compute_ambiguity(A[g], qs_τ, model.Ns)
        end

        if settings.use_utility
            # pymdp formulation: utility = E[log(softmax(C))]
            log_C_τ = view(log_C[g], :, t_future)
            G_τ += dot(qo_g, log_C_τ)
        end

        if settings.use_states_info_gain
            G_τ += compute_state_info_gain(A[g], qs_τ, qo_g, model.Ns)
        end
    end

    if settings.use_param_info_gain
        weight = settings.param_info_gain_weight
        G_τ += weight * compute_param_info_gain_A_from_pA(pA, model, qs_τ, A, settings)
        G_τ += weight * compute_param_info_gain_B_from_pB(pB, model, qs, qs_τ, policy, τ, settings)
    end

    # For subsequent timesteps, branch over observations and average
    if τ < horizon
        # Compute joint observation distribution (simplified: just use first informative modality)
        # Full version would branch over all modality combinations

        # Find the modality with highest entropy (most informative to branch on)
        best_g = 1
        best_entropy = -Inf
        for g in 1:model.Ng
            qo_g = compute_predicted_obs(A[g], qs_τ, model.Ns)
            H = -sum(p * log(p + eps(T)) for p in qo_g if p > eps(T))
            if H > best_entropy
                best_entropy = H
                best_g = g
            end
        end

        # Branch over observations for this modality
        qo_branch = compute_predicted_obs(A[best_g], qs_τ, model.Ns)
        G_future = zero(T)

        for o in 1:length(qo_branch)
            if qo_branch[o] < eps(T)
                continue
            end

            # Compute posterior beliefs given this observation
            qs_given_o = compute_posterior_given_obs(A[best_g], o, qs_τ, model.Ns)

            # Recursively compute EFE for remaining timesteps
            G_branch = efe_counterfactual_recursive(
                qs_given_o, τ + 1, horizon, policy, A, B, log_C, model, settings, current_t, start_τ,
                pA, pB
            )

            G_future += qo_branch[o] * G_branch
        end

        G_τ += G_future
    end

    return G_τ
end

"""
    forward_simulate_from(agent, model, policy, start_τ)

Forward simulate beliefs under a policy starting from policy timestep start_τ.

Returns vector of predicted beliefs: qs_pred[idx][f] for idx = 1:(horizon-start_τ+1)
where qs_pred[1] corresponds to beliefs after applying action at start_τ.
"""
function forward_simulate_from(
    agent::AIFAgent{T},
    model::AIFModel{T,Nf},
    policy::AbstractMatrix{Int},
    start_τ::Int
) where {T, Nf}

    horizon = size(policy, 1)
    n_steps = horizon - start_τ + 1

    if n_steps <= 0
        return Vector{Vector{Vector{T}}}()
    end

    # Get current B (possibly learned)
    B = get_B_from_pB(agent.pB)

    # Start from current beliefs
    qs_current = [copy(agent.qs[agent.t][f]) for f in 1:Nf]

    qs_pred = Vector{Vector{Vector{T}}}(undef, n_steps)

    for idx in 1:n_steps
        τ = start_τ + idx - 1
        qs_next = Vector{Vector{T}}(undef, Nf)

        for f in 1:Nf
            action = policy[τ, f]
            action = clamp(action, 1, model.Na[f])
            B_f_a = B[f][:, :, action]
            qs_next[f] = B_f_a * qs_current[f]
        end

        qs_pred[idx] = qs_next
        qs_current = qs_next
    end

    return qs_pred
end

"""
    forward_simulate(agent, model, policy; sophisticated=false)

Forward simulate beliefs under a policy.

If sophisticated=false (default): Simple transition-only propagation.
If sophisticated=true: Accounts for expected belief updates from observations.

Returns vector of predicted beliefs: qs_pred[τ][f] for τ = 1:horizon
"""
function forward_simulate(
    agent::AIFAgent{T},
    model::AIFModel{T,Nf},
    policy::AbstractMatrix{Int};
    A::Union{Nothing, Vector{<:Array}}=nothing,
    sophisticated::Bool=false
) where {T, Nf}

    horizon = size(policy, 1)

    # Get current B (possibly learned)
    B = get_B_from_pB(agent.pB)

    # Start from current beliefs
    qs_current = [copy(agent.qs[agent.t][f]) for f in 1:Nf]

    qs_pred = Vector{Vector{Vector{T}}}(undef, horizon)

    for τ in 1:horizon
        qs_next = Vector{Vector{T}}(undef, Nf)

        for f in 1:Nf
            action = policy[τ, f]
            # Clamp action to valid range
            action = clamp(action, 1, model.Na[f])

            # Apply transition: q(s'|π) = B * q(s|π)
            B_f_a = B[f][:, :, action]
            qs_next[f] = B_f_a * qs_current[f]
        end

        qs_pred[τ] = qs_next

        # If sophisticated, update beliefs by averaging over expected observations
        if sophisticated && !isnothing(A)
            qs_next = compute_expected_posterior(A, qs_next, model.Ns)
        end

        qs_current = qs_next
    end

    return qs_pred
end

"""
    compute_expected_posterior(A, qs, Ns)

Compute expected posterior beliefs after averaging over all possible observations.

For each modality g, for each possible observation o:
1. Compute q(o|s) = A[g][o,s] weighted by q(s)
2. Compute posterior q(s|o) using Bayes rule
3. Weight by p(o) and average

This gives the "expected updated beliefs" - accounting for the fact that
observations will reduce uncertainty.
"""
function compute_expected_posterior(
    A::Vector{<:Array{T}},
    qs::Vector{Vector{T}},
    Ns::NTuple{Nf, Int}
) where {T, Nf}

    # Start with current beliefs
    qs_updated = [copy(q) for q in qs]

    # Update beliefs based on expected observation from each modality
    for (g, A_g) in enumerate(A)
        # Compute predicted observation distribution
        qo_g = compute_predicted_obs(A_g, qs_updated, Ns)

        # Compute expected posterior for each factor
        for f in 1:Nf
            expected_post_f = zeros(T, Ns[f])

            No_g = size(A_g, 1)
            for o in 1:No_g
                if qo_g[o] < eps(T)
                    continue
                end

                # Compute posterior q(s_f|o)
                qs_given_o = compute_posterior_given_obs(A_g, o, qs_updated, Ns)

                # Weight by probability of this observation
                expected_post_f .+= qo_g[o] .* qs_given_o[f]
            end

            # Normalize
            expected_post_f ./= sum(expected_post_f) + eps(T)
            qs_updated[f] = expected_post_f
        end
    end

    return qs_updated
end

"""
    compute_predicted_obs(A_g, qs, Ns)

Compute predicted observation distribution: q(o_g | π, τ) = Σ_s A_g(o|s) q(s|π,τ)
"""
function compute_predicted_obs(
    A_g::Array{T},
    qs::Vector{Vector{T}},
    Ns::NTuple{Nf, Int}
) where {T, Nf}

    No_g = size(A_g, 1)
    qo = zeros(T, No_g)

    # Marginalize over all state combinations
    for idx in CartesianIndices(Ns)
        # Joint probability of this state combination
        prob_s = prod(qs[f][idx[f]] for f in 1:Nf)

        # Add contribution to each observation
        for o in 1:No_g
            qo[o] += A_g[o, idx] * prob_s
        end
    end

    return qo
end

"""
    compute_ambiguity(A_g, qs, Ns)

Compute ambiguity: E_{q(s)}[H[P(o|s)]] for modality g.

This is the expected entropy of observations given state beliefs.
"""
function compute_ambiguity(
    A_g::Array{T},
    qs::Vector{Vector{T}},
    Ns::NTuple{Nf, Int}
) where {T, Nf}

    ambiguity = zero(T)

    for idx in CartesianIndices(Ns)
        # Joint probability of this state
        prob_s = prod(qs[f][idx[f]] for f in 1:Nf)

        if prob_s < eps(T)
            continue
        end

        # Entropy of P(o|s) for this state
        p_o_given_s = view(A_g, :, idx)
        H = zero(T)
        for p in p_o_given_s
            if p > eps(T)
                H -= p * log(p)
            end
        end

        ambiguity += prob_s * H
    end

    return ambiguity
end

"""
    compute_state_info_gain(A_g, qs, qo, Ns)

Compute expected information gain about hidden states.

This returns E_{q(o|π)}[ KL(q(s|o,π) || q(s|π)) ], i.e. expected reduction in state uncertainty.
"""
function compute_state_info_gain(
    A_g::Array{T},
    qs::Vector{Vector{T}},
    qo::Vector{T},
    Ns::NTuple{Nf, Int}
) where {T, Nf}

    info_gain = zero(T)
    No = size(A_g, 1)

    for o in 1:No
        if qo[o] < eps(T)
            continue
        end
        qs_given_o = compute_posterior_given_obs(A_g, o, qs, Ns)
        kl = zero(T)
        for f in 1:Nf
            for s in 1:Ns[f]
                p = qs_given_o[f][s]
                if p > eps(T)
                    kl += p * log(p / (qs[f][s] + eps(T)))
                end
            end
        end
        info_gain += qo[o] * kl
    end

    return info_gain
end

"""
    compute_posterior_given_obs(A_g, o, qs, Ns)

Compute factorized posterior q(s|o) given observation o.

Returns vector of posteriors: result[f] is q(s_f|o)
"""
function compute_posterior_given_obs(
    A_g::Array{T},
    o::Int,
    qs::Vector{Vector{T}},
    Ns::NTuple{Nf, Int}
) where {T, Nf}

    qs_given_o = Vector{Vector{T}}(undef, Nf)

    for f in 1:Nf
        # Compute marginal likelihood P(o|s_f) by averaging over other factors
        likelihood_f = zeros(T, Ns[f])

        for s_f in 1:Ns[f]
            for idx in CartesianIndices(Ns)
                if idx[f] != s_f
                    continue
                end
                # Probability of other factors
                prob_other = prod(qs[ff][idx[ff]] for ff in 1:Nf if ff != f)
                likelihood_f[s_f] += A_g[o, idx] * prob_other
            end
        end

        # Posterior: q(s_f|o) ∝ P(o|s_f) q(s_f)
        posterior_f = likelihood_f .* qs[f]
        posterior_sum = sum(posterior_f)
        if posterior_sum > eps(T)
            posterior_f ./= posterior_sum
        else
            # Fallback to prior if likelihood is zero everywhere
            posterior_f = copy(qs[f])
        end
        qs_given_o[f] = posterior_f
    end

    return qs_given_o
end

# ==============================================================================
# Parameter Information Gain (pymdp-style wnorm)
# ==============================================================================

# Match pymdp's spm_wnorm approximation:
# wA = 1/sum(A) - 1/A (with epsilon)
function wnorm(A::Array{T}) where {T}
    A_eps = A .+ eps(T)
    norm = one(T) ./ sum(A_eps, dims=1)
    avg = one(T) ./ A_eps
    return norm .- avg
end

function compute_param_info_gain_A(
    agent::AIFAgent{T},
    model::AIFModel{T,Nf},
    qs::Vector{Vector{T}},
    A::Vector{<:Array},
    settings::AIFSettings
) where {T, Nf}
    return compute_param_info_gain_A_from_pA(agent.pA, model, qs, A, settings)
end

function compute_param_info_gain_A_from_pA(
    pA::Vector{<:Array},
    model::AIFModel{T,Nf},
    qs::Vector{Vector{T}},
    A::Vector{<:Array},
    settings::AIFSettings
) where {T, Nf}
    ig = zero(T)
    if isempty(settings.learn_A)
        return ig
    end

    for g in settings.learn_A
        if g < 1 || g > model.Ng
            continue
        end

        wA = wnorm(pA[g])
        qo = compute_predicted_obs(A[g], qs, model.Ns)
        wA_qs = compute_predicted_obs(wA, qs, model.Ns)
        ig -= dot(qo, wA_qs)
    end

    return ig
end

function compute_param_info_gain_B(
    agent::AIFAgent{T},
    model::AIFModel{T,Nf},
    qs_prev::Vector{Vector{T}},
    qs_curr::Vector{Vector{T}},
    policy::AbstractMatrix{Int},
    τ::Int,
    settings::AIFSettings
) where {T, Nf}
    return compute_param_info_gain_B_from_pB(agent.pB, model, qs_prev, qs_curr, policy, τ, settings)
end

function compute_param_info_gain_B_from_pB(
    pB::Vector{<:Array},
    model::AIFModel{T,Nf},
    qs_prev::Vector{Vector{T}},
    qs_curr::Vector{Vector{T}},
    policy::AbstractMatrix{Int},
    τ::Int,
    settings::AIFSettings
) where {T, Nf}
    ig = zero(T)
    if isempty(settings.learn_B)
        return ig
    end

    for f in settings.learn_B
        if f < 1 || f > Nf
            continue
        end
        a_f = clamp(policy[τ, f], 1, model.Na[f])
        wB = wnorm(pB[f][:, :, a_f])
        ig -= dot(qs_curr[f], wB * qs_prev[f])
    end

    return ig
end
