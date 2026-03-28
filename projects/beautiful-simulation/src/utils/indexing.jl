"""
Generic indexing helpers adapted from the reusable patterns in
`projects/library/src/rxinfer_impl.jl`.
"""

function one_hot(idx::Int, n::Int)
    v = zeros(Float64, n)
    v[idx] = 1.0
    return v
end

function flatten_state(state::Vector{Int}, dims::Vector{Int})
    idx = 1
    multiplier = 1
    for i in length(dims):-1:1
        idx += (state[i] - 1) * multiplier
        multiplier *= dims[i]
    end
    return idx
end

function unflatten_state(idx::Int, dims::Vector{Int})
    state = zeros(Int, length(dims))
    remaining = idx - 1
    for i in length(dims):-1:1
        state[i] = (remaining % dims[i]) + 1
        remaining = remaining ÷ dims[i]
    end
    return state
end

joint_index_s_phi(s::Int, phi::Int; n_s::Int = 4, n_phi::Int = 4) =
    flatten_state([s, phi], [n_s, n_phi])

function inverse_joint_index_s_phi(idx::Int; n_s::Int = 4, n_phi::Int = 4)
    s, phi = unflatten_state(idx, [n_s, n_phi])
    return s, phi
end

joint_index_s_phi_phi(
    s::Int,
    phi_v::Int,
    phi_a::Int;
    n_s::Int = 4,
    n_phi::Int = 4
) = flatten_state([s, phi_v, phi_a], [n_s, n_phi, n_phi])

function inverse_joint_index_s_phi_phi(
    idx::Int;
    n_s::Int = 4,
    n_phi::Int = 4
)
    s, phi_v, phi_a = unflatten_state(idx, [n_s, n_phi, n_phi])
    return s, phi_v, phi_a
end

function marginalize_joint(q_joint::AbstractVector{<:Real}, dims::Vector{Int}, axis::Int)
    marginal = zeros(Float64, dims[axis])
    for idx in eachindex(q_joint)
        state = unflatten_state(idx, dims)
        marginal[state[axis]] += q_joint[idx]
    end
    return marginal
end

function marginalize_joint_rows(joint_rows::Matrix{Float64}, dims::Vector{Int}, axis::Int)
    marginals = zeros(Float64, size(joint_rows, 1), dims[axis])
    for t in axes(joint_rows, 1)
        marginals[t, :] = marginalize_joint(view(joint_rows, t, :), dims, axis)
    end
    return marginals
end
