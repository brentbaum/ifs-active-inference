"""
    inference.jl - State inference for Active Inference

Variational message passing for factored state spaces.
"""

"""
    infer_states!(agent, model, observation, settings)

Update state beliefs given observation using variational message passing.

Performs mean-field fixed-point iteration:
1. For each factor f: ln q(s_f) ∝ ln prior_f + Σ_g marginal_likelihood(o_g, s_f)
2. Repeat until convergence or max_iter

Where marginal_likelihood integrates over beliefs of other factors.
"""
function infer_states!(
    agent::AIFAgent{T},
    model::AIFModel{T,Nf},
    observation::Vector{Int},
    settings::AIFSettings
) where {T, Nf}

    t = agent.t

    # Store observation
    push!(agent.observations, observation)

    # Get current A (possibly learned)
    A = get_A_from_pA(agent.pA)
    lnA = nothing
    if settings.use_dirichlet_expectation
        lnA = Vector{Array{T}}(undef, model.Ng)
        floor = exp(-4)
        for g in 1:model.Ng
            pA_safe = agent.pA[g] .+ floor
            lnA[g] = digamma.(pA_safe) .- digamma.(sum(pA_safe, dims=1))
        end
    end

    # Get current B (possibly learned)
    B = get_B_from_pB(agent.pB)

    # Initialize beliefs
    if t == 1
        # At t=1, initialize from prior D
        for f in 1:Nf
            agent.qs[t][f] .= agent.pD[f] ./ sum(agent.pD[f])
        end
    else
        # At t>1, initialize from B-propagated beliefs
        for f in 1:Nf
            prev_action = agent.actions[t-1][f]
            prev_action = clamp(prev_action, 1, model.Na[f])
            B_f_a = B[f][:, :, prev_action]
            agent.qs[t][f] .= B_f_a * agent.qs[t-1][f]
        end
    end

    # Fixed-point iteration
    for iter in 1:settings.fpi_max_iter
        qs_old = [copy(agent.qs[t][f]) for f in 1:Nf]

        for f in 1:Nf
            # Start with log prior contribution
            if t == 1
                ln_qs = log.(agent.pD[f] ./ sum(agent.pD[f]) .+ eps(T))
            else
                # Prior from t-1 propagated through B
                prev_action = agent.actions[t-1][f]
                prev_action = clamp(prev_action, 1, model.Na[f])
                B_f_a = B[f][:, :, prev_action]
                predicted = B_f_a * agent.qs[t-1][f]
                ln_qs = log.(predicted .+ eps(T))
            end

            # Add log likelihood from each modality
            for g in 1:model.Ng
                ln_A_marginal = settings.use_dirichlet_expectation ?
                    compute_ln_A_marginal_from_lnA(
                        lnA[g], observation[g], agent.qs[t], f, model.Ns
                    ) :
                    compute_ln_A_marginal(
                        A[g], observation[g], agent.qs[t], f, model.Ns
                    )
                ln_qs .+= ln_A_marginal
            end

            # Normalize to get posterior
            agent.qs[t][f] .= softmax(ln_qs)
        end

        # Check convergence
        max_diff = maximum(
            maximum(abs.(agent.qs[t][f] .- qs_old[f])) for f in 1:Nf
        )
        if max_diff < settings.fpi_tol
            break
        end
    end

    return agent.qs[t]
end

"""
    compute_ln_A_marginal_from_lnA(lnA_g, o, qs, f, Ns)

Compute E_{q(s_{-f})}[ln A_g(o_g | s)] for factor f using a precomputed lnA.
"""
function compute_ln_A_marginal_from_lnA(
    lnA_g::Array{T},
    o::Int,
    qs::Vector{Vector{T}},
    f::Int,
    Ns::NTuple{Nf, Int}
) where {T, Nf}

    result = zeros(T, Ns[f])

    for idx in CartesianIndices(Ns)
        s_f = idx[f]
        prob_other = one(T)
        for ff in 1:Nf
            if ff != f
                prob_other *= qs[ff][idx[ff]]
            end
        end

        result[s_f] += lnA_g[o, idx] * prob_other
    end

    return result
end

"""
    compute_ln_A_marginal(A_g, o, qs, f, Ns)

Compute E_{q(s_{-f})}[ln A_g(o_g | s)] for factor f.

Marginalizes the log-likelihood over all factors except f,
weighted by current beliefs q(s_{-f}).

# Arguments
- `A_g`: Observation likelihood tensor for modality g, shape (No_g, Ns[1], ..., Ns[Nf])
- `o`: Observed value for modality g
- `qs`: Current beliefs, qs[f] is belief over factor f
- `f`: Factor to compute marginal for
- `Ns`: Tuple of state dimensions
"""
function compute_ln_A_marginal(
    A_g::Array{T},
    o::Int,
    qs::Vector{Vector{T}},
    f::Int,
    Ns::NTuple{Nf, Int}
) where {T, Nf}

    result = zeros(T, Ns[f])

    # Iterate over all state combinations
    for idx in CartesianIndices(Ns)
        s_f = idx[f]

        # Compute joint probability of other factors: ∏_{f' ≠ f} q(s_{f'})
        prob_other = one(T)
        for ff in 1:Nf
            if ff != f
                prob_other *= qs[ff][idx[ff]]
            end
        end

        # Add weighted log likelihood
        # A_g[o, s_1, ..., s_Nf] gives P(o | s)
        likelihood = A_g[o, idx]
        result[s_f] += log(likelihood + eps(T)) * prob_other
    end

    return result
end

"""
    compute_joint_state_prob(qs, Ns)

Compute joint probability over all state combinations.

Returns array of shape Ns where result[idx] = ∏_f q(s_f)[idx[f]]
"""
function compute_joint_state_prob(
    qs::Vector{Vector{T}},
    Ns::NTuple{Nf, Int}
) where {T, Nf}

    result = zeros(T, Ns)
    for idx in CartesianIndices(Ns)
        prob = one(T)
        for f in 1:Nf
            prob *= qs[f][idx[f]]
        end
        result[idx] = prob
    end
    return result
end
