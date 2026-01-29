"""
    policy.jl - Policy inference and action selection

Computes posterior over policies via EFE minimization and samples actions.
"""

"""
    infer_policies!(agent, model, settings)

Compute posterior over policies: Q(π) ∝ P(π) exp(-γ G(π))
"""
function infer_policies!(
    agent::AIFAgent{T},
    model::AIFModel{T,Nf},
    settings::AIFSettings
) where {T, Nf}

    n_policies = model.policies.n_policies

    # Compute EFE for each policy
    G = Vector{T}(undef, n_policies)
    for pi in 1:n_policies
        G[pi] = calculate_efe(agent, model, pi, settings)
    end

    # Log posterior: ln Q(π) = ln P(π) - γ G(π) + const
    ln_qpi = log.(model.policies.E .+ eps(T)) .- settings.gamma .* G

    # Normalize with numerical stability
    agent.qpi .= softmax(ln_qpi)

    return agent.qpi
end

"""
    sample_action(agent, model; alpha=4.0)

Sample action from policy posterior for current timestep.

Marginalizes over policies to get action distribution per factor:
P(a_f | t) = Σ_π Q(π) δ(a_f, V[t, π, f])

Then samples with action precision α.

# Arguments
- `agent`: AIFAgent with policy posterior qpi
- `model`: AIFModel
- `alpha`: Action precision (higher = more deterministic)
"""
function sample_action(
    agent::AIFAgent{T},
    model::AIFModel{T,Nf};
    alpha::Real=4.0
) where {T, Nf}

    t = agent.t
    τ = t  # Policy timestep index (1-based)

    if τ > model.policies.horizon
        # No more actions to take, return default
        actions = ones(Int, Nf)
        push!(agent.actions, actions)
        return actions
    end

    actions = Vector{Int}(undef, Nf)

    for f in 1:Nf
        # Compute action distribution for this factor
        action_probs = zeros(T, model.Na[f])

        for pi in 1:model.policies.n_policies
            action = model.policies.V[τ, pi, f]
            action = clamp(action, 1, model.Na[f])
            action_probs[action] += agent.qpi[pi]
        end

        # Apply action precision and sample
        ln_action_probs = T(alpha) .* log.(action_probs .+ eps(T))
        action_dist = softmax(ln_action_probs)

        # Sample from categorical
        actions[f] = sample_categorical(action_dist)
    end

    # Store action
    push!(agent.actions, actions)

    return actions
end

"""
    get_action_distribution(agent, model, t)

Get the action distribution for each factor at timestep t.

Returns vector of vectors: result[f][a] = P(a_f = a)
"""
function get_action_distribution(
    agent::AIFAgent{T},
    model::AIFModel{T,Nf},
    t::Int
) where {T, Nf}

    if t > model.policies.horizon
        # Return uniform over first action
        return [[one(T)] for f in 1:Nf]
    end

    result = Vector{Vector{T}}(undef, Nf)

    for f in 1:Nf
        action_probs = zeros(T, model.Na[f])

        for pi in 1:model.policies.n_policies
            action = model.policies.V[t, pi, f]
            action = clamp(action, 1, model.Na[f])
            action_probs[action] += agent.qpi[pi]
        end

        result[f] = action_probs
    end

    return result
end

"""
    get_expected_efe(agent, model, settings)

Compute expected EFE under current policy distribution.

E_Q(π)[G(π)] = Σ_π Q(π) G(π)
"""
function get_expected_efe(
    agent::AIFAgent{T},
    model::AIFModel{T,Nf},
    settings::AIFSettings
) where {T, Nf}

    expected_G = zero(T)
    for pi in 1:model.policies.n_policies
        G_pi = calculate_efe(agent, model, pi, settings)
        expected_G += agent.qpi[pi] * G_pi
    end
    return expected_G
end
