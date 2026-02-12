"""
    learning.jl - Dirichlet parameter learning for Active Inference

Implements online learning of generative model parameters via
Dirichlet concentration parameter updates.
"""

"""
    update_learning!(agent, model, observation, settings; learn_A, learn_B, learn_D)

Update Dirichlet concentration parameters based on observation and current beliefs.

Implements the Dirichlet update rules:
- pA[g][o, s...] += eta * delta(o, obs) * prod_f q(s_f)  for modalities in learn_A
- pB[f][s', s, a] += eta * q(s'_f, t) * q(s_f, t-1) * delta(a, action)  for factors in learn_B (t > 1)
- pD[f][s] += eta * q(s_f, t=1)  for factors in learn_D (only at t=1)

# Arguments
- `agent::AIFAgent`: Agent with beliefs and learnable parameters
- `model::AIFModel`: Model with dimensions
- `observation::Vector{Int}`: Current observation (one index per modality)
- `settings::AIFSettings`: Settings containing learning rate eta

# Keywords
- `learn_A::Vector{Int}=Int[]`: Which modalities to learn (indices into pA)
- `learn_B::Vector{Int}=Int[]`: Which factors to learn (indices into pB)
- `learn_D::Vector{Int}=Int[]`: Which factors to learn initial state prior (indices into pD)

# Returns
Nothing, modifies agent.pA, agent.pB, agent.pD in place.
"""
function update_learning!(
    agent::AIFAgent{T},
    model::AIFModel{T,Nf},
    observation::Vector{Int},
    settings::AIFSettings;
    learn_A::Vector{Int}=Int[],
    learn_B::Vector{Int}=Int[],
    learn_D::Vector{Int}=Int[]
) where {T, Nf}

    t = agent.t

    # Use specific learning rates for each matrix type
    eta_A = T(settings.eta_A)
    eta_B = T(settings.eta_B)
    eta_D = T(settings.eta_D)

    # Update pA for specified modalities
    if !isempty(learn_A)
        update_pA!(agent, model, observation, eta_A, learn_A)
    end

    # Update pB for specified factors (requires t > 1)
    if !isempty(learn_B) && t > 1
        update_pB!(agent, model, eta_B, learn_B)
    end

    # Update pD for specified factors (only at t == 1)
    if !isempty(learn_D) && t == 1
        update_pD!(agent, eta_D, learn_D)
    end

    return nothing
end

"""
    update_pA!(agent, model, observation, eta, modalities)

Update observation likelihood Dirichlet parameters pA.

For each modality g in modalities:
    pA[g][o, s_1, ..., s_Nf] += eta * delta(o, obs[g]) * prod_f q(s_f)

This accumulates evidence that observation obs[g] occurs in states
weighted by the current belief over state combinations.
"""
function update_pA!(
    agent::AIFAgent{T},
    model::AIFModel{T,Nf},
    observation::Vector{Int},
    eta::T,
    modalities::Vector{Int}
) where {T, Nf}

    t = agent.t
    qs_t = agent.qs[t]  # Current beliefs: qs_t[f] is Vector{T}

    for g in modalities
        # Validate modality index
        if g < 1 || g > model.Ng
            @warn "Skipping invalid modality index $g (model has $(model.Ng) modalities)"
            continue
        end

        obs_g = observation[g]

        # Iterate over all state combinations
        for idx in CartesianIndices(model.Ns)
            # Compute joint probability: prod_f q(s_f)[idx[f]]
            joint_prob = one(T)
            for f in 1:Nf
                joint_prob *= qs_t[f][idx[f]]
            end

            # Update pA at the observed outcome
            # pA[g] has shape (No[g], Ns[1], ..., Ns[Nf])
            agent.pA[g][obs_g, idx] += eta * joint_prob
        end
    end

    return nothing
end

"""
    update_pB!(agent, model, eta, factors)

Update transition Dirichlet parameters pB.

For each factor f in factors:
    pB[f][s', s, a] += eta * q(s'_f, t) * q(s_f, t-1) * delta(a, action[t-1][f])

This accumulates evidence for state transitions weighted by beliefs
at consecutive timesteps.
"""
function update_pB!(
    agent::AIFAgent{T},
    model::AIFModel{T,Nf},
    eta::T,
    factors::Vector{Int}
) where {T, Nf}

    t = agent.t

    # Get beliefs at current and previous timesteps
    qs_curr = agent.qs[t]      # Beliefs at time t
    qs_prev = agent.qs[t-1]    # Beliefs at time t-1

    # Get action taken at t-1
    action = agent.actions[t-1]

    for f in factors
        # Validate factor index
        if f < 1 || f > Nf
            @warn "Skipping invalid factor index $f (model has $Nf factors)"
            continue
        end

        # Get action for this factor (clamped to valid range)
        a_f = clamp(action[f], 1, model.Na[f])

        # Update pB[f][:, :, a_f]
        # pB[f] has shape (Ns[f], Ns[f], Na[f])
        Ns_f = model.Ns[f]

        for s_curr in 1:Ns_f  # s' (next state)
            for s_prev in 1:Ns_f  # s (previous state)
                # Weight by product of beliefs
                weight = qs_curr[f][s_curr] * qs_prev[f][s_prev]
                agent.pB[f][s_curr, s_prev, a_f] += eta * weight
            end
        end
    end

    return nothing
end

"""
    update_pD!(agent, eta, factors)

Update initial state Dirichlet parameters pD.

For each factor f in factors (only at t=1):
    pD[f][s] += eta * q(s_f, t=1)

This accumulates evidence for initial state distribution based on
inferred beliefs at the first timestep.
"""
function update_pD!(
    agent::AIFAgent{T},
    eta::T,
    factors::Vector{Int}
) where {T}

    # Only meaningful at t=1, but we check this in the caller
    qs_1 = agent.qs[1]

    for f in factors
        # Validate factor index
        Nf_actual = length(agent.pD)
        if f < 1 || f > Nf_actual
            @warn "Skipping invalid factor index $f (agent has $Nf_actual factors)"
            continue
        end

        # Update pD[f] with current beliefs
        for s in 1:length(agent.pD[f])
            agent.pD[f][s] += eta * qs_1[f][s]
        end
    end

    return nothing
end

"""
    update_pD_from_qs!(agent, eta, factors, qs)

Update initial state Dirichlet parameters pD using provided beliefs `qs`.
This mirrors pymdp's update_D behavior used in the trust game simulations.
"""
function update_pD_from_qs!(
    agent::AIFAgent{T},
    eta::T,
    factors::Vector{Int},
    qs::Vector{Vector{T}}
) where {T}
    for f in factors
        Nf_actual = length(agent.pD)
        if f < 1 || f > Nf_actual
            @warn "Skipping invalid factor index $f (agent has $Nf_actual factors)"
            continue
        end
        for s in 1:length(agent.pD[f])
            agent.pD[f][s] += eta * qs[f][s]
        end
    end
    return nothing
end

"""
    compute_learning_diagnostics(agent, model)

Compute diagnostics about learned parameters.

Returns a NamedTuple with:
- `A_entropy`: Average entropy of learned A columns
- `B_entropy`: Average entropy of learned B columns
- `D_entropy`: Entropy of learned D
- `pA_total`: Total concentration in pA
- `pB_total`: Total concentration in pB
- `pD_total`: Total concentration in pD
"""
function compute_learning_diagnostics(
    agent::AIFAgent{T},
    model::AIFModel{T,Nf}
) where {T, Nf}

    # Get normalized distributions
    A = get_A_from_pA(agent.pA)
    B = get_B_from_pB(agent.pB)
    D = get_D_from_pD(agent.pD)

    # Compute average entropy of A columns
    A_entropy = T(0)
    A_count = 0
    for g in 1:model.Ng
        for idx in CartesianIndices(model.Ns)
            col = A[g][:, idx]
            A_entropy += entropy(col)
            A_count += 1
        end
    end
    A_entropy /= max(A_count, 1)

    # Compute average entropy of B columns
    B_entropy = T(0)
    B_count = 0
    for f in 1:Nf
        for a in 1:model.Na[f]
            for s in 1:model.Ns[f]
                col = B[f][:, s, a]
                B_entropy += entropy(col)
                B_count += 1
            end
        end
    end
    B_entropy /= max(B_count, 1)

    # Compute entropy of D
    D_entropy = T(0)
    for f in 1:Nf
        D_entropy += entropy(D[f])
    end
    D_entropy /= Nf

    # Compute total concentration
    pA_total = sum(sum(pa) for pa in agent.pA)
    pB_total = sum(sum(pb) for pb in agent.pB)
    pD_total = sum(sum(pd) for pd in agent.pD)

    return (
        A_entropy = A_entropy,
        B_entropy = B_entropy,
        D_entropy = D_entropy,
        pA_total = pA_total,
        pB_total = pB_total,
        pD_total = pD_total
    )
end
