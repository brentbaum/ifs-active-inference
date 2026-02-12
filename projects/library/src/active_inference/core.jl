"""
    core.jl - Core types for Active Inference

Generic Active Inference implementation supporting:
- Factored state spaces
- Multiple observation modalities
- Dirichlet learning (A, B, D)
- Expected Free Energy with ambiguity, risk, and state info gain
"""

using LinearAlgebra

#==============================================================================#
# Settings
#==============================================================================#

"""
Configuration for active inference agent.
"""
struct AIFSettings{T<:Real}
    gamma::T                    # Policy precision (inverse temperature)
    alpha::T                    # Action precision
    eta::T                      # Global learning rate (backward compat)
    eta_A::T                    # Learning rate for A matrix
    eta_B::T                    # Learning rate for B matrix
    eta_D::T                    # Learning rate for D matrix
    use_ambiguity::Bool         # Include ambiguity term in EFE
    use_utility::Bool           # Include utility/risk term in EFE
    use_states_info_gain::Bool  # Include state information gain (epistemic value)
    use_param_info_gain::Bool   # Include parameter information gain (learning value)
    use_dirichlet_expectation::Bool # Use E[ln A] from Dirichlet parameters in inference
    param_info_gain_weight::T   # Weight for parameter info gain term
    learn_A::Vector{Int}        # Modalities to include in param info gain
    learn_B::Vector{Int}        # Factors to include in param info gain
    fpi_max_iter::Int           # Fixed-point iteration max iterations
    fpi_tol::T                  # Convergence tolerance
end

"""
    AIFSettings(; kwargs...)

Create AIFSettings with sensible defaults.

# Keywords
- `gamma=1.0`: Policy precision (inverse temperature)
- `alpha=4.0`: Action precision
- `eta=1.0`: Global learning rate (used if eta_A/eta_B/eta_D not specified)
- `eta_A=nothing`: Learning rate for A matrix (defaults to eta)
- `eta_B=nothing`: Learning rate for B matrix (defaults to eta)
- `eta_D=nothing`: Learning rate for D matrix (defaults to eta)
- `use_ambiguity=true`: Include ambiguity term in EFE
- `use_utility=true`: Include utility/risk term in EFE
- `use_states_info_gain=true`: Include state information gain
- `use_param_info_gain=false`: Include parameter information gain (learning value)
- `use_dirichlet_expectation=false`: Use digamma-based expectation for A in inference
- `learn_A=Int[]`: Modalities to include in param info gain
- `learn_B=Int[]`: Factors to include in param info gain
- `fpi_max_iter=16`: Max fixed-point iterations
- `fpi_tol=1e-6`: Convergence tolerance
"""
function AIFSettings(;
    gamma::Real=1.0,
    alpha::Real=4.0,
    eta::Real=1.0,
    eta_A::Union{Nothing,Real}=nothing,
    eta_B::Union{Nothing,Real}=nothing,
    eta_D::Union{Nothing,Real}=nothing,
    use_ambiguity::Bool=true,
    use_utility::Bool=true,
    use_states_info_gain::Bool=true,
    use_param_info_gain::Bool=false,
    use_dirichlet_expectation::Bool=false,
    param_info_gain_weight::Real=1.0,
    learn_A::Vector{Int}=Int[],
    learn_B::Vector{Int}=Int[],
    fpi_max_iter::Int=16,
    fpi_tol::Real=1e-6
)
    # Use specific learning rates if provided, else fall back to eta
    lr_A = isnothing(eta_A) ? eta : eta_A
    lr_B = isnothing(eta_B) ? eta : eta_B
    lr_D = isnothing(eta_D) ? eta : eta_D

    T = promote_type(typeof(gamma), typeof(alpha), typeof(eta),
                     typeof(lr_A), typeof(lr_B), typeof(lr_D),
                     typeof(param_info_gain_weight), typeof(fpi_tol))
    AIFSettings{T}(
        T(gamma), T(alpha), T(eta), T(lr_A), T(lr_B), T(lr_D),
        use_ambiguity, use_utility, use_states_info_gain,
        use_param_info_gain, use_dirichlet_expectation, T(param_info_gain_weight),
        copy(learn_A), copy(learn_B),
        fpi_max_iter, T(fpi_tol)
    )
end

#==============================================================================#
# Policy Set
#==============================================================================#

"""
Policy specification - explicit horizon and action sequences.

V[t, π, f] = action index for timestep t, policy π, factor f
"""
struct PolicySet{T<:Real}
    V::Array{Int, 3}      # (horizon, n_policies, n_factors)
    E::Vector{T}          # Policy prior P(π), length n_policies

    # Derived dimensions
    n_policies::Int
    horizon::Int          # T-1 planning steps
    n_factors::Int
end

"""
    PolicySet(V, E)

Create a PolicySet with validation.

# Arguments
- `V::Array{Int,3}`: Action sequences, shape (horizon, n_policies, n_factors)
- `E::Vector`: Policy prior (will be normalized)
"""
function PolicySet(V::Array{Int,3}, E::Vector{T}) where T<:Real
    horizon, n_policies, n_factors = size(V)
    @assert length(E) == n_policies "E must have length n_policies=$n_policies, got $(length(E))"
    @assert all(E .>= 0) "E must be non-negative"
    E_sum = sum(E)
    @assert E_sum > 0 "E must have positive sum"
    PolicySet{T}(V, E ./ E_sum, n_policies, horizon, n_factors)
end

# Convenience constructor for Integer vectors
function PolicySet(V::Array{Int,3}, E::Vector{<:Integer})
    PolicySet(V, Float64.(E))
end

#==============================================================================#
# Generative Model
#==============================================================================#

"""
Active Inference Model - immutable problem specification.

# Type conventions
- `A[g]`: Array of size (No[g], Ns[1], ..., Ns[Nf]) - observation likelihood
- `B[f]`: Array of size (Ns[f], Ns[f], Na[f]) - transitions
- `C[g]`: Matrix of size (No[g], T) - log preferences (positive = preferred)
- `D[f]`: Vector of size Ns[f] - initial state prior
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
    Ns::NTuple{Nf, Int}        # State dimensions per factor
    No::Vector{Int}            # Observation dimensions per modality
    Na::Vector{Int}            # Action dimensions per factor
    Ng::Int                    # Number of observation modalities
    T::Int                     # Trial length (timesteps)
end

"""
    AIFModel(A, B, C, D, policies; trial_length)

Create an AIFModel with validation.

# Arguments
- `A`: Vector of observation likelihood tensors
- `B`: Vector of transition tensors
- `C`: Vector of preference matrices (log preferences)
- `D`: Vector of initial state priors
- `policies`: PolicySet specifying available action sequences
- `trial_length`: Number of timesteps per trial
"""
function AIFModel(
    A::Vector{<:Array},
    B::Vector{<:Array{<:Real,3}},
    C::Vector{<:Matrix},
    D::Vector{<:Vector};
    policies::PolicySet{T},
    trial_length::Int
) where T

    Nf = length(D)
    Ng = length(A)
    Ns = Tuple(length.(D))
    No = [size(A[g], 1) for g in 1:Ng]
    Na = [size(B[f], 3) for f in 1:Nf]

    # Validate A shapes: each A[g] should be (No[g], Ns[1], ..., Ns[Nf])
    for g in 1:Ng
        expected_shape = (No[g], Ns...)
        @assert ndims(A[g]) == Nf + 1 "A[$g] must have $(Nf+1) dimensions, got $(ndims(A[g]))"
        @assert size(A[g]) == expected_shape "A[$g] shape $(size(A[g])) != expected $expected_shape"
        # Check columns sum to 1 (normalize over observations)
        A_sum = sum(A[g], dims=1)
        if !all(isapprox.(A_sum, 1.0, atol=1e-6))
            @warn "A[$g] columns don't sum to 1, normalizing"
        end
    end

    # Validate B shapes
    for f in 1:Nf
        @assert size(B[f]) == (Ns[f], Ns[f], Na[f]) "B[$f] shape $(size(B[f])) != expected $((Ns[f], Ns[f], Na[f]))"
        # Check columns sum to 1 (normalize over next states)
        for a in 1:Na[f]
            B_sum = sum(B[f][:,:,a], dims=1)
            if !all(isapprox.(B_sum, 1.0, atol=1e-6))
                @warn "B[$f][:,:,$a] columns don't sum to 1, normalizing"
            end
        end
    end

    # Validate C shapes (preferences over time)
    for g in 1:Ng
        @assert size(C[g]) == (No[g], trial_length) "C[$g] shape $(size(C[g])) != expected $((No[g], trial_length))"
    end

    # Validate D shapes
    for f in 1:Nf
        @assert length(D[f]) == Ns[f] "D[$f] length $(length(D[f])) != expected $(Ns[f])"
        D_sum = sum(D[f])
        if !isapprox(D_sum, 1.0, atol=1e-6)
            @warn "D[$f] doesn't sum to 1, normalizing"
        end
    end

    # Validate policies
    @assert policies.n_factors == Nf "Policy has $(policies.n_factors) factors but model has $Nf"
    @assert policies.horizon == trial_length - 1 "Policy horizon $(policies.horizon) != T-1=$(trial_length-1)"

    # Normalize and convert to consistent type
    A_norm = [Array{T}(a ./ sum(a, dims=1)) for a in A]
    B_norm = [Array{T,3}(b) for b in B]
    for f in 1:Nf
        for a in 1:Na[f]
            B_norm[f][:,:,a] ./= sum(B_norm[f][:,:,a], dims=1)
        end
    end
    C_typed = [Matrix{T}(c) for c in C]
    D_norm = [Vector{T}(d ./ sum(d)) for d in D]

    AIFModel{T, Nf}(A_norm, B_norm, C_typed, D_norm, policies, Ns, No, Na, Ng, trial_length)
end

# Convenience: infer trial_length from C if not provided
function AIFModel(A, B, C, D; policies, trial_length=nothing)
    tl = isnothing(trial_length) ? size(C[1], 2) : trial_length
    AIFModel(A, B, C, D; policies=policies, trial_length=tl)
end

#==============================================================================#
# Agent State
#==============================================================================#

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
    init_agent(model; pA_scale=1.0, pB_scale=1.0, pD_scale=1.0)

Initialize an agent for a model.

# Arguments
- `model`: AIFModel to create agent for
- `pA_scale`: Scale factor for initial pA Dirichlet parameters
- `pB_scale`: Scale factor for initial pB Dirichlet parameters
- `pD_scale`: Scale factor for initial pD Dirichlet parameters
"""
function init_agent(
    model::AIFModel{T, Nf};
    pA_scale::Real=1.0,
    pB_scale::Real=1.0,
    pD_scale::Real=1.0
) where {T, Nf}

    # Initialize beliefs to prior
    qs_init = [[copy(model.D[f]) for f in 1:Nf] for t in 1:model.T]
    qpi_init = copy(model.policies.E)

    # Initialize Dirichlet parameters from model
    pA = [T(pA_scale) .* copy(model.A[g]) for g in 1:model.Ng]
    pB = [T(pB_scale) .* copy(model.B[f]) for f in 1:Nf]
    pD = [T(pD_scale) .* copy(model.D[f]) for f in 1:Nf]

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
    init_agent(model, pA, pB, pD)

Initialize an agent with custom Dirichlet priors.
"""
function init_agent(
    model::AIFModel{T, Nf},
    pA::Vector{<:Array},
    pB::Vector{<:Array{<:Real,3}},
    pD::Vector{<:Vector}
) where {T, Nf}

    # Initialize beliefs to normalized pD
    qs_init = [[pD[f] ./ sum(pD[f]) for f in 1:Nf] for t in 1:model.T]
    qpi_init = copy(model.policies.E)

    AIFAgent{T}(
        1,
        qs_init,
        qpi_init,
        Vector{Int}[],
        Vector{Int}[],
        [Array{T}(pa) for pa in pA],
        [Array{T,3}(pb) for pb in pB],
        [Vector{T}(pd) for pd in pD]
    )
end

"""
    reset_trial!(agent, model)

Reset agent for a new trial (preserves learned parameters).
"""
function reset_trial!(agent::AIFAgent{T}, model::AIFModel{T,Nf}) where {T, Nf}
    agent.t = 1

    # Reset beliefs to current learned prior
    for t in 1:model.T
        for f in 1:Nf
            agent.qs[t][f] .= agent.pD[f] ./ sum(agent.pD[f])
        end
    end

    # Reset policy posterior to prior
    agent.qpi .= model.policies.E

    # Clear history
    empty!(agent.observations)
    empty!(agent.actions)

    return agent
end

#==============================================================================#
# Utility Functions
#==============================================================================#

"""
Numerically stable softmax.
"""
function softmax(x::AbstractVector{T}) where T<:Real
    x_shifted = x .- maximum(x)
    exp_x = exp.(x_shifted)
    return exp_x ./ sum(exp_x)
end

"""
Entropy of a probability distribution.
"""
function entropy(p::AbstractVector{T}) where T<:Real
    -sum(pi * log(pi + eps(T)) for pi in p if pi > 0)
end

"""
KL divergence D_KL[p || q].
"""
function kl_divergence(p::AbstractVector{T}, q::AbstractVector{T}) where T<:Real
    sum(pi * (log(pi + eps(T)) - log(qi + eps(T))) for (pi, qi) in zip(p, q) if pi > 0)
end

"""
Sample from categorical distribution.
"""
function sample_categorical(probs::AbstractVector{T}) where T<:Real
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

"""
Get normalized A from Dirichlet parameters.
"""
function get_A_from_pA(pA::Vector{<:Array{T}}) where T
    [pA_g ./ sum(pA_g, dims=1) for pA_g in pA]
end

"""
Get normalized B from Dirichlet parameters.
"""
function get_B_from_pB(pB::Vector{<:Array{T,3}}) where T
    result = similar.(pB)
    for (f, pB_f) in enumerate(pB)
        for a in 1:size(pB_f, 3)
            result[f][:,:,a] = pB_f[:,:,a] ./ sum(pB_f[:,:,a], dims=1)
        end
    end
    return result
end

"""
Get normalized D from Dirichlet parameters.
"""
function get_D_from_pD(pD::Vector{<:Vector{T}}) where T
    [pD_f ./ sum(pD_f) for pD_f in pD]
end
