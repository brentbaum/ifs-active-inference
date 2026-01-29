# Plan v2: Generic Active Inference Library (Revised)

**Revision notes**: Updated based on Codex Plan Reviewer feedback addressing:
- Underspecified EFE formula
- Missing multi-factor inference equations
- Incorrect observation model type (Matrix → Tensor)
- Missing temporal belief trajectories
- Incomplete learning specification
- Vague action inference

**v2.1 additions** (for broader applicability):
- State information gain in EFE (epistemic exploration)
- B learning (transition dynamics)

---

## Goal
Create a reusable Active Inference implementation that:
1. Can be applied to any factored POMDP-like problem
2. Provides proper Expected Free Energy (EFE) calculation with explicit terms
3. Supports policy selection via EFE minimization
4. Includes Dirichlet learning for belief updating
5. Is cleanly separated from problem-specific code

---

## Architecture

### File Structure
```
src/
├── active_inference/
│   ├── core.jl           # Core types, validation, constructors
│   ├── inference.jl      # State inference (variational message passing)
│   ├── efe.jl            # Expected Free Energy calculation
│   ├── policy.jl         # Policy inference and action selection
│   ├── learning.jl       # Dirichlet parameter learning
│   └── agent.jl          # Thin agent loop orchestration
└── spider_model.jl       # Spider phobia as one application
```

---

## Core Types (`core.jl`)

### AIFSettings - Configuration
```julia
"""
Configuration for active inference agent.
"""
struct AIFSettings{T<:Real}
    gamma::T                    # Policy precision (inverse temperature)
    alpha::T                    # Action precision
    eta::T                      # Learning rate
    use_ambiguity::Bool         # Include ambiguity term in EFE
    use_utility::Bool           # Include utility/risk term in EFE
    use_states_info_gain::Bool  # Include state information gain (epistemic value)
    fpi_max_iter::Int           # Fixed-point iteration max iterations
    fpi_tol::T                  # Convergence tolerance
end

# Default constructor
function AIFSettings(;
    gamma=1.0, alpha=4.0, eta=1.0,
    use_ambiguity=true, use_utility=true, use_states_info_gain=true,
    fpi_max_iter=16, fpi_tol=1e-6
)
    AIFSettings(gamma, alpha, eta, use_ambiguity, use_utility, use_states_info_gain,
                fpi_max_iter, fpi_tol)
end
```

### PolicySet - Explicit Policy Specification
```julia
"""
Policy specification - explicit horizon and action sequences.

V[t, π, f] = action index for timestep t, policy π, factor f
"""
struct PolicySet{T<:Real}
    V::Array{Int, 3}      # (horizon, n_policies, n_factors)
    E::Vector{T}          # Policy prior P(π), length n_policies

    # Derived (for convenience)
    n_policies::Int
    horizon::Int          # T-1 planning steps
    n_factors::Int
end

function PolicySet(V::Array{Int,3}, E::Vector{T}) where T
    horizon, n_policies, n_factors = size(V)
    @assert length(E) == n_policies "E must have length n_policies"
    @assert all(E .>= 0) "E must be non-negative"
    PolicySet{T}(V, E ./ sum(E), n_policies, horizon, n_factors)
end
```

### AIFModel - Generative Model (Immutable)

**CRITICAL FIX**: A matrices are tensors, not matrices. For factored states with `Nf` factors, `A[g]` has shape `(No[g], Ns[1], Ns[2], ..., Ns[Nf])`.

```julia
"""
Active Inference Model - immutable problem specification.

Type conventions:
- A[g]: Array{T, Nf+1} of size (No[g], Ns[1], ..., Ns[Nf]) - observation likelihood
- B[f]: Array{T,3} of size (Ns[f], Ns[f], Na[f]) - transitions
- C[g]: Matrix{T} of size (No[g], T) - log preferences (positive = preferred)
- D[f]: Vector{T} of size Ns[f] - initial state prior
"""
struct AIFModel{T<:Real, Nf}
    # Core matrices
    A::Vector{Array{T}}        # P(o|s) - observation likelihoods per modality
    B::Vector{Array{T,3}}      # P(s'|s,a) - transitions per factor
    C::Vector{Matrix{T}}       # Log preferences per modality (No[g] × T)
    D::Vector{Vector{T}}       # Initial state prior per factor

    # Policies
    policies::PolicySet{T}

    # Dimensions (validated at construction)
    Ns::NTuple{Nf, Int}        # State dimensions per factor (tuple for type stability)
    No::Vector{Int}            # Observation dimensions per modality
    Na::Vector{Int}            # Action dimensions per factor
    Ng::Int                    # Number of observation modalities
    T::Int                     # Trial length (timesteps)
end

# Constructor with validation
function AIFModel(A, B, C, D, policies::PolicySet{T}; trial_length::Int) where T
    Nf = length(D)
    Ng = length(A)
    Ns = Tuple(length.(D))
    No = [size(A[g], 1) for g in 1:Ng]
    Na = [size(B[f], 3) for f in 1:Nf]

    # Validate A shapes: each A[g] should be (No[g], Ns[1], ..., Ns[Nf])
    expected_A_shape = (No[g], Ns...)
    for g in 1:Ng
        @assert ndims(A[g]) == Nf + 1 "A[$g] must have Nf+1=$(Nf+1) dimensions"
        @assert size(A[g]) == (No[g], Ns...) "A[$g] shape $(size(A[g])) != expected $((No[g], Ns...))"
        @assert all(sum(A[g], dims=1) .≈ 1) "A[$g] columns must sum to 1"
    end

    # Validate B shapes
    for f in 1:Nf
        @assert size(B[f]) == (Ns[f], Ns[f], Na[f]) "B[$f] shape mismatch"
        for a in 1:Na[f]
            @assert all(sum(B[f][:,:,a], dims=1) .≈ 1) "B[$f][:,:,$a] columns must sum to 1"
        end
    end

    # Validate C shapes (preferences over time)
    for g in 1:Ng
        @assert size(C[g]) == (No[g], trial_length) "C[$g] must be (No[$g], T)"
    end

    # Validate D shapes
    for f in 1:Nf
        @assert length(D[f]) == Ns[f] "D[$f] length mismatch"
        @assert sum(D[f]) ≈ 1 "D[$f] must sum to 1"
    end

    # Validate policies
    @assert policies.n_factors == Nf "Policy factors must match model"
    @assert policies.horizon == trial_length - 1 "Policy horizon must be T-1"

    AIFModel{T, Nf}(A, B, C, D, policies, Ns, No, Na, Ng, trial_length)
end
```

### AIFAgent - Mutable State

**CRITICAL FIX**: Include temporal belief trajectories and proper observation history.

```julia
"""
Agent state - mutable beliefs and learnable parameters.

qs[t][f] = belief over states for factor f at timestep t
"""
mutable struct AIFAgent{T<:Real}
    # Current timestep
    t::Int

    # Temporal beliefs: qs[t][f] is Vector{T} of length Ns[f]
    qs::Vector{Vector{Vector{T}}}      # [timestep][factor] -> belief vector

    # Policy posterior
    qpi::Vector{T}                      # Posterior over policies

    # Observation history for current trial
    observations::Vector{Vector{Int}}   # [timestep] -> observation per modality
    actions::Vector{Vector{Int}}        # [timestep] -> action per factor

    # Learnable Dirichlet concentration parameters
    pA::Vector{Array{T}}               # Same shape as A (for learning A)
    pB::Vector{Array{T,3}}             # Same shape as B (for learning B)
    pD::Vector{Vector{T}}              # Same shape as D (for learning D)
end

"""
Initialize agent for a model.
"""
function init_agent(model::AIFModel{T, Nf};
                    pA_scale::T=1.0, pB_scale::T=1.0, pD_scale::T=1.0) where {T, Nf}
    # Initialize beliefs to prior
    qs_init = [[copy(model.D[f]) for f in 1:Nf] for t in 1:model.T]
    qpi_init = copy(model.policies.E)

    # Initialize Dirichlet parameters from model
    pA = [pA_scale .* copy(model.A[g]) for g in 1:model.Ng]
    pB = [pB_scale .* copy(model.B[f]) for f in 1:Nf]
    pD = [pD_scale .* copy(model.D[f]) for f in 1:Nf]

    AIFAgent{T}(
        1,                              # t
        qs_init,                        # qs
        qpi_init,                       # qpi
        Vector{Int}[],                  # observations
        Vector{Int}[],                  # actions
        pA, pB, pD
    )
end

"""
Reset agent for new trial (preserves learned parameters).
"""
function reset_trial!(agent::AIFAgent, model::AIFModel)
    agent.t = 1
    for t in 1:model.T
        for f in 1:length(model.D)
            # Reset to current learned prior
            agent.qs[t][f] .= agent.pD[f] ./ sum(agent.pD[f])
        end
    end
    agent.qpi .= model.policies.E
    empty!(agent.observations)
    empty!(agent.actions)
end
```

---

## State Inference (`inference.jl`)

**CRITICAL FIX**: Provide exact variational update equations for multi-factor inference.

### Mathematical Specification

For factored states with mean-field approximation:
```
q(s) = ∏_f q(s_f)
```

The variational update for factor f (fixing other factors):
```
ln q(s_f) ∝ ln D_f(s_f) + ∑_g E_{q(s_{-f})}[ln A_g(o_g | s)]
```

Where `E_{q(s_{-f})}[ln A_g(o_g | s)]` marginalizes over other factors.

### Implementation
```julia
"""
Update state beliefs given observation using variational message passing.

Performs mean-field fixed-point iteration:
1. For each factor f:
   ln q(s_f) ∝ ln D_f + Σ_g marginal_likelihood(o_g, s_f)
2. Repeat until convergence or max_iter

Where marginal_likelihood integrates over beliefs of other factors.
"""
function infer_states!(agent::AIFAgent{T}, model::AIFModel{T,Nf},
                       observation::Vector{Int}, settings::AIFSettings) where {T, Nf}
    t = agent.t

    # Store observation
    push!(agent.observations, observation)

    # Get current A (possibly learned)
    A = [agent.pA[g] ./ sum(agent.pA[g], dims=1) for g in 1:model.Ng]

    # Initialize from prior (D at t=1, or B-propagated at t>1)
    if t == 1
        for f in 1:Nf
            agent.qs[t][f] .= agent.pD[f] ./ sum(agent.pD[f])
        end
    end

    # Fixed-point iteration
    for iter in 1:settings.fpi_max_iter
        qs_old = [copy(agent.qs[t][f]) for f in 1:Nf]

        for f in 1:Nf
            # Compute log likelihood contribution from all modalities
            ln_qs = log.(agent.qs[t][f] .+ 1e-16)

            # Add prior contribution
            if t == 1
                ln_qs .+= log.(agent.pD[f] ./ sum(agent.pD[f]) .+ 1e-16)
            else
                # Use posterior from t-1 propagated through B
                prev_action = agent.actions[t-1][f]
                B_f = model.B[f][:, :, prev_action]
                predicted = B_f * agent.qs[t-1][f]
                ln_qs .+= log.(predicted .+ 1e-16)
            end

            # Add likelihood from each modality
            for g in 1:model.Ng
                ln_A_marginal = compute_ln_A_marginal(A[g], observation[g],
                                                      agent.qs[t], f, model.Ns)
                ln_qs .+= ln_A_marginal
            end

            # Normalize
            agent.qs[t][f] .= softmax(ln_qs)
        end

        # Check convergence
        max_diff = maximum(maximum(abs.(agent.qs[t][f] .- qs_old[f])) for f in 1:Nf)
        if max_diff < settings.fpi_tol
            break
        end
    end
end

"""
Compute E_{q(s_{-f})}[ln A_g(o_g | s)] for factor f.

Marginalizes A over all factors except f, weighted by q(s_{-f}).
"""
function compute_ln_A_marginal(A_g::Array{T}, o::Int,
                                qs::Vector{Vector{T}}, f::Int,
                                Ns::NTuple{Nf, Int}) where {T, Nf}
    # A_g has shape (No_g, Ns[1], ..., Ns[Nf])
    # We want E_{-f}[ln A_g[o, s_1, ..., s_Nf]]

    # Extract the slice for observation o
    # A_g_o has shape (Ns[1], ..., Ns[Nf])
    A_g_o = selectdim(A_g, 1, o)

    # Marginalize over all factors except f
    result = zeros(T, Ns[f])

    # Use tensor contraction: sum over all dims except f
    for s_f in 1:Ns[f]
        # Build indices: s_f fixed, others summed
        prob_sum = zero(T)

        # Iterate over all combinations of other factors
        for idx in CartesianIndices(Ns)
            if idx[f] != s_f
                continue
            end
            # Compute joint probability of other factors
            prob_other = one(T)
            for ff in 1:Nf
                if ff != f
                    prob_other *= qs[ff][idx[ff]]
                end
            end
            prob_sum += log(A_g_o[idx] + 1e-16) * prob_other
        end
        result[s_f] = prob_sum
    end

    return result
end

"""
Numerically stable softmax.
"""
function softmax(x::Vector{T}) where T
    x_shifted = x .- maximum(x)
    exp_x = exp.(x_shifted)
    return exp_x ./ sum(exp_x)
end
```

---

## Expected Free Energy (`efe.jl`)

**CRITICAL FIX**: Provide exact EFE formula with explicit derivation.

### Mathematical Specification

Expected Free Energy for policy π at future timestep τ:

```
G(π, τ) = E_Q(o,s|π)[ln Q(s|π) - ln P(o,s|π)]
        = E_Q(s|π)[H[P(o|s)]]  +  E_Q(o|π)[-ln P(o)]  -  E_Q[D_KL[Q(s|o,π) || Q(s|π)]]
        = Ambiguity            +  Risk                 -  State Info Gain
```

Where:
- **Ambiguity** = `E_{q(s|π)}[H[P(o|s)]]` = expected entropy of observations given beliefs
- **Risk** = `E_{q(o|π)}[-C(o)]` = negative expected log preference (C is log preference)
- **State Info Gain** = `E_{q(o|π)}[D_KL[q(s|o,π) || q(s|π)]]` = expected information gain about states (epistemic value)

Note: State info gain is subtracted because it's a "good" term (reduces EFE when info gain is high).

Total EFE for policy:
```
G(π) = Σ_{τ=t+1}^{T} G(π, τ)
```

### Implementation
```julia
"""
Calculate Expected Free Energy for a policy.

G(π) = Σ_τ [ambiguity(τ) + risk(τ) - state_info_gain(τ)]

Where for each future timestep τ:
- ambiguity = E_{q(s|π,τ)}[H[P(o|s)]]
- risk = E_{q(o|π,τ)}[-C(o,τ)]
- state_info_gain = E_{q(o|π,τ)}[D_KL[q(s|o,π,τ) || q(s|π,τ)]]
"""
function calculate_efe(agent::AIFAgent{T}, model::AIFModel{T,Nf},
                       policy_idx::Int, settings::AIFSettings) where {T, Nf}
    policy = model.policies.V[:, policy_idx, :]  # (horizon, n_factors)

    # Forward simulate beliefs under this policy
    qs_pred = forward_simulate(agent, model, policy)

    # Compute EFE terms
    G = zero(T)

    # Get current A (possibly learned)
    A = [agent.pA[g] ./ sum(agent.pA[g], dims=1) for g in 1:model.Ng]

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
                C_τ = model.C[g][:, t_future]
                risk = -dot(qo_τ_g, C_τ)
                G += risk
            end

            if settings.use_states_info_gain
                # State information gain: E_q(o)[D_KL[q(s|o) || q(s)]]
                # This rewards policies that lead to informative observations
                state_info_gain = compute_state_info_gain(A[g], qs_τ, qo_τ_g, model.Ns)
                G -= state_info_gain  # Subtract because info gain is "good"
            end
        end
    end

    return G
end

"""
Forward simulate beliefs under a policy.

Returns vector of predicted beliefs: qs_pred[τ][f] for τ = 1:horizon
"""
function forward_simulate(agent::AIFAgent{T}, model::AIFModel{T,Nf},
                          policy::Matrix{Int}) where {T, Nf}
    horizon = size(policy, 1)

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
            B_f_a = model.B[f][:, :, action]
            qs_next[f] = B_f_a * qs_current[f]
        end

        qs_pred[τ] = qs_next
        qs_current = qs_next
    end

    return qs_pred
end

"""
Compute predicted observation distribution: q(o_g | π, τ) = Σ_s A_g(o|s) q(s|π,τ)
"""
function compute_predicted_obs(A_g::Array{T}, qs::Vector{Vector{T}},
                                Ns::NTuple{Nf, Int}) where {T, Nf}
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
Compute ambiguity: E_{q(s)}[H[P(o|s)]] for modality g.

This is the expected entropy of observations given state beliefs.
"""
function compute_ambiguity(A_g::Array{T}, qs::Vector{Vector{T}},
                           Ns::NTuple{Nf, Int}) where {T, Nf}
    ambiguity = zero(T)

    for idx in CartesianIndices(Ns)
        # Joint probability of this state
        prob_s = prod(qs[f][idx[f]] for f in 1:Nf)

        # Entropy of P(o|s) for this state
        p_o_given_s = A_g[:, idx]
        H = -sum(p * log(p + 1e-16) for p in p_o_given_s if p > 0)

        ambiguity += prob_s * H
    end

    return ambiguity
end

"""
Compute state information gain: E_{q(o)}[D_KL[q(s|o) || q(s)]]

This is the expected KL divergence between posterior (after observing o) and prior beliefs.
Measures how much observing o would reduce uncertainty about s.

Uses the identity: I(s;o) = H[q(s)] - E_q(o)[H[q(s|o)]]
                         = H[q(s)] - H[q(s|o)] averaged over q(o)
"""
function compute_state_info_gain(A_g::Array{T}, qs::Vector{Vector{T}},
                                  qo::Vector{T}, Ns::NTuple{Nf, Int}) where {T, Nf}
    No_g = length(qo)
    info_gain = zero(T)

    # For each possible observation
    for o in 1:No_g
        if qo[o] < 1e-16
            continue
        end

        # Compute posterior q(s|o) ∝ P(o|s) q(s) for each factor
        # This is a simplification assuming factorized posterior
        qs_given_o = Vector{Vector{T}}(undef, length(qs))

        for f in 1:length(qs)
            # Marginalize A over other factors to get likelihood for factor f
            likelihood_f = zeros(T, Ns[f])
            for s_f in 1:Ns[f]
                for idx in CartesianIndices(Ns)
                    if idx[f] != s_f
                        continue
                    end
                    prob_other = prod(qs[ff][idx[ff]] for ff in 1:length(qs) if ff != f)
                    likelihood_f[s_f] += A_g[o, idx] * prob_other
                end
            end

            # Posterior: q(s_f|o) ∝ P(o|s_f) q(s_f)
            posterior_f = likelihood_f .* qs[f]
            posterior_f ./= sum(posterior_f) + 1e-16
            qs_given_o[f] = posterior_f
        end

        # KL divergence: D_KL[q(s|o) || q(s)] = Σ_f D_KL[q(s_f|o) || q(s_f)]
        kl = zero(T)
        for f in 1:length(qs)
            for s_f in 1:Ns[f]
                if qs_given_o[f][s_f] > 1e-16
                    kl += qs_given_o[f][s_f] * (log(qs_given_o[f][s_f] + 1e-16) -
                                                 log(qs[f][s_f] + 1e-16))
                end
            end
        end

        info_gain += qo[o] * kl
    end

    return info_gain
end
```

---

## Policy Selection (`policy.jl`)

**CRITICAL FIX**: Include numerical stability and explicit action marginalization.

```julia
"""
Compute posterior over policies: Q(π) ∝ P(π) exp(-γ G(π))
"""
function infer_policies!(agent::AIFAgent{T}, model::AIFModel{T,Nf},
                         settings::AIFSettings) where {T, Nf}
    n_policies = model.policies.n_policies

    # Compute EFE for each policy
    G = [calculate_efe(agent, model, pi, settings) for pi in 1:n_policies]

    # Log posterior: ln Q(π) = ln P(π) - γ G(π) + const
    ln_qpi = log.(model.policies.E .+ 1e-16) .- settings.gamma .* G

    # Normalize with numerical stability
    agent.qpi .= softmax(ln_qpi)
end

"""
Sample action from policy posterior for current timestep.

Marginalizes over policies to get action distribution per factor:
P(a_f | t) = Σ_π Q(π) δ(a_f, V[t, π, f])

Then samples with action precision α.
"""
function sample_action(agent::AIFAgent{T}, model::AIFModel{T,Nf};
                       alpha::T=4.0) where {T, Nf}
    t = agent.t
    τ = t  # Policy timestep index (1-based)

    if τ > model.policies.horizon
        # No more actions to take
        return ones(Int, Nf)
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
        ln_action_probs = alpha .* log.(action_probs .+ 1e-16)
        action_dist = softmax(ln_action_probs)

        # Sample from categorical
        actions[f] = sample_categorical(action_dist)
    end

    # Store action
    push!(agent.actions, actions)

    return actions
end

"""
Sample from categorical distribution.
"""
function sample_categorical(probs::Vector{T}) where T
    r = rand()
    cumprob = zero(T)
    for i in 1:length(probs)
        cumprob += probs[i]
        if r <= cumprob
            return i
        end
    end
    return length(probs)
end
```

---

## Learning (`learning.jl`)

**CRITICAL FIX**: Proper Dirichlet update with sufficient statistics.
**v2.1**: Added B learning for transition dynamics.

```julia
"""
Update Dirichlet concentration parameters based on observation.

Dirichlet update rules:
- pA[g][o, s...] += η * δ(o, obs) * ∏_f q(s_f)
- pB[f][s', s, a] += η * q(s'_f, t) * q(s_f, t-1) * δ(a, action)
- pD[f][s] += η * q(s_f, t=1)
"""
function update_learning!(agent::AIFAgent{T}, model::AIFModel{T,Nf},
                          observation::Vector{Int}, settings::AIFSettings;
                          learn_A::Vector{Int}=Int[],
                          learn_B::Vector{Int}=Int[],
                          learn_D::Vector{Int}=Int[]) where {T, Nf}
    t = agent.t
    η = settings.eta

    # Update pA for specified modalities
    for g in learn_A
        for idx in CartesianIndices(model.Ns)
            # Joint probability of this state
            prob_s = prod(agent.qs[t][f][idx[f]] for f in 1:Nf)

            # Update: pA[o_observed, s] += η * q(s)
            o = observation[g]
            agent.pA[g][o, idx] += η * prob_s
        end
    end

    # Update pB for specified factors (requires t > 1 and action taken)
    if t > 1 && length(agent.actions) >= t - 1
        for f in learn_B
            action = agent.actions[t-1][f]
            action = clamp(action, 1, model.Na[f])

            # Update: pB[s', s, a] += η * q(s'_f, t) * q(s_f, t-1)
            for s_prev in 1:model.Ns[f]
                for s_curr in 1:model.Ns[f]
                    agent.pB[f][s_curr, s_prev, action] +=
                        η * agent.qs[t][f][s_curr] * agent.qs[t-1][f][s_prev]
                end
            end
        end
    end

    # Update pD for specified factors (only at t=1)
    if t == 1
        for f in learn_D
            agent.pD[f] .+= η .* agent.qs[1][f]
        end
    end
end

"""
Get normalized A from Dirichlet parameters.
"""
function get_A_from_pA(pA::Vector{Array{T}}) where T
    [pA_g ./ sum(pA_g, dims=1) for pA_g in pA]
end

"""
Get normalized B from Dirichlet parameters.
"""
function get_B_from_pB(pB::Vector{Array{T,3}}) where T
    [pB_f ./ sum(pB_f, dims=1) for pB_f in pB]
end

"""
Get normalized D from Dirichlet parameters.
"""
function get_D_from_pD(pD::Vector{Vector{T}}) where T
    [pD_f ./ sum(pD_f) for pD_f in pD]
end
```

---

## Agent Loop (`agent.jl`)

```julia
"""
Run single trial: observe → infer → plan → act → learn.

Returns trial history for analysis.
"""
function run_trial!(agent::AIFAgent{T}, model::AIFModel{T,Nf}, env,
                    settings::AIFSettings;
                    learn_A::Vector{Int}=Int[],
                    learn_B::Vector{Int}=Int[],
                    learn_D::Vector{Int}=Int[]) where {T, Nf}

    reset_trial!(agent, model)

    history = (
        observations = Vector{Vector{Int}}(),
        actions = Vector{Vector{Int}}(),
        beliefs = Vector{Vector{Vector{T}}}(),
        qpi = Vector{Vector{T}}(),
        states = Vector{Vector{Int}}()
    )

    for t in 1:model.T
        agent.t = t

        # Get observation from environment
        obs = observe(env)
        push!(history.observations, obs)
        push!(history.states, get_state(env))

        # State inference
        infer_states!(agent, model, obs, settings)
        push!(history.beliefs, [copy(agent.qs[t][f]) for f in 1:Nf])

        # Learning (update Dirichlet parameters)
        update_learning!(agent, model, obs, settings;
                         learn_A=learn_A, learn_B=learn_B, learn_D=learn_D)

        if t < model.T
            # Policy inference
            infer_policies!(agent, model, settings)
            push!(history.qpi, copy(agent.qpi))

            # Action selection and execution
            action = sample_action(agent, model; alpha=settings.alpha)
            push!(history.actions, action)

            step!(env, action)
        end
    end

    return history
end

"""
Environment interface (to be implemented by specific environments).
"""
abstract type AIFEnvironment end

function observe(env::AIFEnvironment)::Vector{Int}
    error("observe() not implemented for $(typeof(env))")
end

function step!(env::AIFEnvironment, action::Vector{Int})
    error("step!() not implemented for $(typeof(env))")
end

function get_state(env::AIFEnvironment)::Vector{Int}
    error("get_state() not implemented for $(typeof(env))")
end

function reset!(env::AIFEnvironment)
    error("reset!() not implemented for $(typeof(env))")
end
```

---

## Spider Model Application (`spider_model.jl`)

```julia
"""
Spider phobia environment implementing AIFEnvironment interface.
"""
mutable struct SpiderEnvironment <: AIFEnvironment
    spider_dangerous::Bool
    current_state::Vector{Int}  # [behavior, spider_present, danger]
    A::Vector{Array{Float64}}   # For sampling observations
end

function SpiderEnvironment(spider_dangerous::Bool, A::Vector{Array{Float64}})
    # Initial state: start position, spider present, danger determined by spider_dangerous
    initial_state = [1, 2, spider_dangerous ? 1 : 2]
    SpiderEnvironment(spider_dangerous, initial_state, A)
end

function reset!(env::SpiderEnvironment)
    env.current_state = [1, 2, env.spider_dangerous ? 1 : 2]
end

function get_state(env::SpiderEnvironment)
    return copy(env.current_state)
end

function observe(env::SpiderEnvironment)
    # Sample observation from each modality given true state
    obs = Int[]
    for g in 1:length(env.A)
        probs = env.A[g][:, env.current_state...]
        probs = probs ./ (sum(probs) + 1e-16)
        push!(obs, sample_categorical(probs))
    end
    return obs
end

function step!(env::SpiderEnvironment, action::Vector{Int})
    # Apply transitions (simplified - use B matrices in full impl)
    # Factor 1 (behavior) changes based on action
    # Factors 2, 3 are static
    env.current_state[1] = transition_behavior(env.current_state[1], action[1])
end

"""
Build spider phobia AIFModel using existing model construction.
"""
function build_spider_aif_model(params::ModelParams)
    # Use existing model.jl construction
    model_tuple = build_model(params=params)

    # Create PolicySet
    policies = PolicySet(
        model_tuple.V,
        Float64.(model_tuple.E ./ sum(model_tuple.E))
    )

    # Convert C to log preferences (already in right format)

    # Normalize A, B, D
    A = [a ./ sum(a, dims=1) for a in model_tuple.A]
    B = model_tuple.B
    C = model_tuple.C
    D = [d ./ sum(d) for d in model_tuple.D]

    return AIFModel(A, B, C, D, policies; trial_length=params.T)
end

"""
Run spider phobia exposure therapy using generic AIF framework.
"""
function run_spider_aif_therapy(;
    n_trials::Int=200,
    spider_dangerous::Bool=false,
    params::ModelParams=ModelParams(),
    settings::AIFSettings=AIFSettings(),
    exposure_mode::Bool=true
)
    model = build_spider_aif_model(params)
    agent = init_agent(model)
    env = SpiderEnvironment(spider_dangerous, model.A)

    results = []

    for trial in 1:n_trials
        reset!(env)
        history = run_trial!(agent, model, env, settings;
                            learn_A=[3],   # Learn affective consequences
                            learn_D=[3])   # Learn about danger

        # Extract metrics
        p_safe = agent.pD[3][2] / sum(agent.pD[3])
        push!(results, (
            trial=trial,
            p_safe=p_safe,
            pD=copy(agent.pD),
            pA=copy(agent.pA[3])
        ))

        if trial % 50 == 0
            @info "Trial $trial: P(safe) = $(round(p_safe, digits=3))"
        end
    end

    return results
end
```

---

## Testing Plan

### Unit Tests (`test/test_active_inference.jl`)

```julia
@testset "Active Inference Core" begin
    @testset "Softmax numerical stability" begin
        # Test with large values
        x = [1000.0, 1001.0, 1002.0]
        p = softmax(x)
        @test sum(p) ≈ 1.0
        @test all(p .>= 0)
        @test p[3] > p[2] > p[1]
    end

    @testset "PolicySet validation" begin
        V = ones(Int, 3, 4, 2)  # 3 timesteps, 4 policies, 2 factors
        E = [0.25, 0.25, 0.25, 0.25]
        ps = PolicySet(V, E)
        @test ps.horizon == 3
        @test ps.n_policies == 4
        @test sum(ps.E) ≈ 1.0
    end

    @testset "AIFModel validation" begin
        # Small test model: 2 factors, 1 modality
        Ns = (3, 2)  # 3 states factor 1, 2 states factor 2
        No = [4]     # 4 observations
        Na = [2, 1]  # 2 actions factor 1, 1 action factor 2
        T = 3

        A = [rand(No[1], Ns...)]
        A[1] ./= sum(A[1], dims=1)

        B = [
            rand(Ns[1], Ns[1], Na[1]),
            reshape([1.0 0; 0 1], 2, 2, 1)
        ]
        for f in 1:2
            for a in 1:Na[f]
                B[f][:,:,a] ./= sum(B[f][:,:,a], dims=1)
            end
        end

        C = [zeros(No[1], T)]
        D = [ones(Ns[1])/Ns[1], ones(Ns[2])/Ns[2]]

        V = ones(Int, T-1, 2, 2)
        E = [0.5, 0.5]
        policies = PolicySet(V, E)

        model = AIFModel(A, B, C, D, policies; trial_length=T)
        @test model.Nf == 2
        @test model.Ng == 1
    end

    @testset "EFE calculation" begin
        # Create minimal model and verify EFE is finite
        # Compare against hand-calculated values for simple case
    end

    @testset "State inference convergence" begin
        # Verify fixed-point iteration converges
        # Check that beliefs update correctly given observation
    end
end

@testset "Spider Model Integration" begin
    @testset "Safe spider learning" begin
        # Run short simulation with safe spider
        # Verify P(safe) increases over trials
        results = run_spider_aif_therapy(
            n_trials=50,
            spider_dangerous=false,
            settings=AIFSettings(gamma=1.0, alpha=4.0, eta=1.0)
        )

        p_safe_start = results[1].p_safe
        p_safe_end = results[end].p_safe
        @test p_safe_end > p_safe_start  # Should learn spider is safe
    end

    @testset "Dangerous spider learning" begin
        # Run simulation with dangerous spider
        # Verify P(safe) stays low or decreases
        results = run_spider_aif_therapy(
            n_trials=50,
            spider_dangerous=true,
            settings=AIFSettings(gamma=1.0, alpha=4.0, eta=1.0)
        )

        p_safe_end = results[end].p_safe
        @test p_safe_end < 0.3  # Should maintain belief spider is dangerous
    end
end
```

---

## Implementation Order

### Phase 1: Core Framework
1. **core.jl** - Types with validation (AIFSettings, PolicySet, AIFModel, AIFAgent)
2. **inference.jl** - State inference with fixed-point iteration and marginal computation
3. **efe.jl** - EFE calculation with forward simulation

### Phase 2: Policy & Agent
4. **policy.jl** - Policy inference and action sampling
5. **learning.jl** - Dirichlet updates
6. **agent.jl** - Trial loop and environment interface

### Phase 3: Spider Application
7. **spider_model.jl** - Environment and model builder
8. Integration with existing visualization

### Phase 4: Testing & Validation
9. Unit tests for each module
10. Integration test comparing to ActiveInference.jl results

---

## Verification Criteria

1. **Correctness**: EFE-driven action selection produces approach when safe, avoid when dangerous
2. **Learning**: P(safe) increases for safe spider, maintains low for dangerous
3. **Convergence**: State inference converges within max_iter
4. **Numerical stability**: No NaN/Inf with edge cases
5. **Compatibility**: Results comparable to existing ActiveInference.jl implementation

---

## Classic Active Inference Benchmarks

For end-to-end verification, implement these classic benchmarks (simple → complex):

### 1. Two-Armed Bandit (Simplest)
**Reference**: Friston et al. (2015) "Active inference and epistemic value"

- 2 states (arm 1 better, arm 2 better)
- 2 actions (pull arm 1, pull arm 2)
- 2 observations (reward, no reward)
- **Expected behavior**: Agent explores initially (epistemic), then exploits (pragmatic)
- **Key test**: State info gain drives early exploration

### 2. T-Maze (Classic)
**Reference**: Friston et al. (2016) "Active inference and learning"

- States: location × reward_location (e.g., 4 × 2 = 8)
- Actions: move left, move right, move forward
- Observations: visual cue (at start), reward (at ends)
- **Expected behavior**: Agent goes to cue location first, then to rewarded arm
- **Key test**: Epistemic action (check cue) before pragmatic (get reward)

### 3. Contextual Bandit
- States: context × arm_values
- Context changes between trials
- **Expected behavior**: Learn context-dependent arm values
- **Key test**: B learning updates transition beliefs

### 4. Spider Phobia (Our Primary)
- Multi-factor state space
- Affective learning (pA)
- Prior belief learning (pD)
- **Expected behavior**: Matches paper results for exposure therapy

### Implementation Order for Benchmarks
1. **T-Maze first** - Classic, well-documented expected results, tests epistemic value
2. **Spider phobia** - Our main application
3. **Two-armed bandit** - Simpler but good for parameter sweeps
4. **Contextual bandit** - Tests B learning specifically
