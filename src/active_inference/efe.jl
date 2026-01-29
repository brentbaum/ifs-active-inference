"""
    efe.jl - Expected Free Energy calculation

G(π) = Σ_τ [ambiguity(τ) + risk(τ) - state_info_gain(τ)]

Where:
- ambiguity = E_{q(s|π,τ)}[H[P(o|s)]]
- risk = E_{q(o|π,τ)}[-C(o,τ)]
- state_info_gain = E_{q(o|π,τ)}[D_KL[q(s|o,π,τ) || q(s|π,τ)]]
"""

using LinearAlgebra: dot

"""
    calculate_efe(agent, model, policy_idx, settings)

Calculate Expected Free Energy for a policy.

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
    settings::AIFSettings
) where {T, Nf}

    policy = view(model.policies.V, :, policy_idx, :)  # (horizon, n_factors)

    # Forward simulate beliefs under this policy
    qs_pred = forward_simulate(agent, model, policy)

    # Get current A (possibly learned)
    A = get_A_from_pA(agent.pA)

    # Compute EFE terms
    G = zero(T)

    for τ in 1:model.policies.horizon
        t_future = agent.t + τ
        if t_future > model.T
            break
        end

        qs_τ = qs_pred[τ]  # Predicted beliefs at future timestep

        for g in 1:model.Ng
            # Compute predicted observation distribution
            qo_τ_g = compute_predicted_obs(A[g], qs_τ, model.Ns)

            if settings.use_ambiguity
                # Ambiguity: E_q(s)[H[P(o|s)]]
                ambiguity = compute_ambiguity(A[g], qs_τ, model.Ns)
                G += ambiguity
            end

            if settings.use_utility
                # Risk: E_q(o)[-C(o)]
                # C[g][:, t_future] contains log preferences
                C_τ = view(model.C[g], :, t_future)
                risk = -dot(qo_τ_g, C_τ)
                G += risk
            end

            if settings.use_states_info_gain
                # State information gain: E_q(o)[D_KL[q(s|o) || q(s)]]
                state_info_gain = compute_state_info_gain(A[g], qs_τ, qo_τ_g, model.Ns)
                G -= state_info_gain  # Subtract because info gain is "good"
            end
        end
    end

    return G
end

"""
    forward_simulate(agent, model, policy)

Forward simulate beliefs under a policy.

Returns vector of predicted beliefs: qs_pred[τ][f] for τ = 1:horizon
"""
function forward_simulate(
    agent::AIFAgent{T},
    model::AIFModel{T,Nf},
    policy::AbstractMatrix{Int}
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
        qs_current = qs_next
    end

    return qs_pred
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

Compute state information gain: E_{q(o)}[D_KL[q(s|o) || q(s)]]

This is the expected KL divergence between posterior (after observing o) and prior beliefs.
Measures how much observing o would reduce uncertainty about s.
"""
function compute_state_info_gain(
    A_g::Array{T},
    qs::Vector{Vector{T}},
    qo::Vector{T},
    Ns::NTuple{Nf, Int}
) where {T, Nf}

    No_g = length(qo)
    info_gain = zero(T)

    # For each possible observation
    for o in 1:No_g
        if qo[o] < eps(T)
            continue
        end

        # Compute posterior q(s|o) for each factor
        # Using Bayes: q(s_f|o) ∝ P(o|s_f) q(s_f)
        # where P(o|s_f) = E_{q(s_{-f})}[A_g[o, s]]
        qs_given_o = compute_posterior_given_obs(A_g, o, qs, Ns)

        # KL divergence: D_KL[q(s|o) || q(s)] = Σ_f D_KL[q(s_f|o) || q(s_f)]
        kl = zero(T)
        for f in 1:length(qs)
            for s_f in 1:Ns[f]
                p_post = qs_given_o[f][s_f]
                p_prior = qs[f][s_f]
                if p_post > eps(T)
                    kl += p_post * (log(p_post + eps(T)) - log(p_prior + eps(T)))
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
