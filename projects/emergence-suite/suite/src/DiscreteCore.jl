module DiscreteCore

export DirichletBanks, LikelihoodBank, StateFactor, TransitionBank

"""
    StateFactor(name, prior)

Typed seam for a discrete hidden-state factor. This mirrors the v10 core's
factored state-space convention without committing T1.1+ simulations to a
specific inference implementation yet.
"""
struct StateFactor{T<:Real}
    name::Symbol
    prior::Vector{T}
end

"""
    LikelihoodBank(counts)

Dirichlet concentration bank for one observation likelihood modality. Counts
use the v10 shape convention `(n_observations, n_state_factor_1, ...)`.
"""
struct LikelihoodBank{T<:Real, N}
    counts::Array{T, N}
end

"""
    TransitionBank(counts)

Dirichlet concentration bank for one transition factor. Counts use the v10
shape convention `(next_state, previous_state, action)`.
"""
struct TransitionBank{T<:Real}
    counts::Array{T, 3}
end

"""
    DirichletBanks(A, B)

Container seam for cross-trial structural precision. `A` holds observation
likelihood banks and `B` holds transition banks. Effective precision is not
stored here; R3 requires it to be logged separately by simulations.
"""
struct DirichletBanks{T<:Real}
    A::Vector{Array{T}}
    B::Vector{Array{T, 3}}
end

end
