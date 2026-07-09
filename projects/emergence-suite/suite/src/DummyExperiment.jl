module DummyExperiment

using Random
using LinearAlgebra
using Statistics

export run_dummy_seed

const EPS = 1e-12

normalize_cols(A) = A ./ max.(sum(A; dims = 1), EPS)

function normalize_B(B::Array{Float64, 3})
    out = copy(B)
    for a in axes(B, 3)
        out[:, :, a] .= B[:, :, a] ./ max.(sum(B[:, :, a]; dims = 1), EPS)
    end
    return out
end

function onehot(i::Int, n::Int)
    v = zeros(Float64, n)
    v[i] = 1.0
    return v
end

function init_A(n1::Int, n2::Int)
    A1 = zeros(Float64, 2, n1, n2)
    A2 = zeros(Float64, 2, n1, n2)
    for s1 in 1:n1, s2 in 1:n2
        A1[:, s1, s2] .= s1 == 1 ? (0.9, 0.1) : (0.1, 0.9)
        A2[:, s1, s2] .= s2 == 1 ? (0.9, 0.1) : (0.1, 0.9)
    end
    return [A1, A2]
end

function init_B(n::Int)
    B = zeros(Float64, n, n, 2)
    for s in 1:n
        B[1, s, 1] = 0.85
        B[min(2, n), s, 1] += 0.15
        B[n, s, 2] = 0.85
        B[max(1, n - 1), s, 2] += 0.15
    end
    return normalize_B(B)
end

mutable struct DummyState
    pA::Vector{Array{Float64}}
    pB::Vector{Array{Float64, 3}}
    qs::Vector{Vector{Float64}}
    true_A::Vector{Array{Float64}}
    true_B::Vector{Array{Float64, 3}}
    state::Vector{Int}
    policies::Vector{Vector{Int}}
    growth_happened::Bool
end

function sample_categorical(rng::AbstractRNG, p)
    u = rand(rng)
    c = 0.0
    for i in eachindex(p)
        c += p[i]
        u <= c && return i
    end
    return length(p)
end

function joint_from_marginals(qs)
    J = ones(Float64, length.(qs)...)
    for idx in CartesianIndices(J)
        p = 1.0
        for f in eachindex(qs)
            p *= qs[f][idx[f]]
        end
        J[idx] = p
    end
    return J
end

function marginals_from_joint(J)
    qs = Vector{Vector{Float64}}(undef, ndims(J))
    for f in 1:ndims(J)
        dims_to_sum = Tuple(i for i in 1:ndims(J) if i != f)
        q = vec(sum(J; dims = dims_to_sum))
        qs[f] = q ./ max(sum(q), EPS)
    end
    return qs
end

function likelihood(A, obs::Vector{Int}, ns::Vector{Int})
    L = ones(Float64, ns...)
    for g in eachindex(A)
        L .*= selectdim(A[g], 1, obs[g])
    end
    return L
end

function model_from_counts(st::DummyState)
    A = [normalize_cols(a) for a in st.pA]
    B = [normalize_B(b) for b in st.pB]
    return A, B
end

function infer_states(st::DummyState, obs::Vector{Int}, A, B, action::Union{Nothing, Vector{Int}})
    prior = action === nothing ? [copy(q) for q in st.qs] : [B[f][:, :, action[f]] * st.qs[f] for f in eachindex(st.qs)]
    J = joint_from_marginals(prior) .* likelihood(A, obs, length.(prior))
    J ./= max(sum(J), EPS)
    return marginals_from_joint(J), J
end

function predicted_obs(A_g, qs)
    qo = zeros(Float64, size(A_g, 1))
    for idx in CartesianIndices(size(A_g)[2:end])
        p = 1.0
        for f in eachindex(qs)
            p *= qs[f][idx[f]]
        end
        qo .+= A_g[:, idx] .* p
    end
    return qo ./ max(sum(qo), EPS)
end

function ambiguity(A_g, qs)
    h = 0.0
    for idx in CartesianIndices(size(A_g)[2:end])
        p = 1.0
        for f in eachindex(qs)
            p *= qs[f][idx[f]]
        end
        col = A_g[:, idx]
        h -= p * sum(col .* log.(col .+ EPS))
    end
    return h
end

function score_policies(st::DummyState, A, B)
    C = (log.([0.25, 0.75]), log.([0.25, 0.75]))
    scores = Float64[]
    for policy in st.policies
        qnext = [B[f][:, :, policy[f]] * st.qs[f] for f in eachindex(st.qs)]
        g = 0.0
        for m in eachindex(A)
            qo = predicted_obs(A[m], qnext)
            g += dot(qo, C[m]) - ambiguity(A[m], qnext)
        end
        push!(scores, g)
    end
    return scores
end

function env_step!(rng::AbstractRNG, st::DummyState, action::Vector{Int})
    for f in eachindex(st.state)
        st.state[f] = sample_categorical(rng, st.true_B[f][:, st.state[f], action[f]])
    end
    return nothing
end

function env_observe(rng::AbstractRNG, st::DummyState)
    return [sample_categorical(rng, vec(st.true_A[g][:, st.state...])) for g in eachindex(st.true_A)]
end

function update_A!(st::DummyState, obs::Vector{Int}, joint)
    for g in eachindex(st.pA)
        view(st.pA[g], obs[g], ntuple(_ -> Colon(), ndims(joint))...) .+= joint
    end
    return nothing
end

function update_B!(st::DummyState, prev_qs, action::Vector{Int})
    for f in eachindex(st.pB)
        st.pB[f][:, :, action[f]] .+= st.qs[f] * prev_qs[f]'
    end
    return nothing
end

function true_A_concentration(st::DummyState)
    vals = Float64[]
    for g in eachindex(st.pA)
        for idx in CartesianIndices(size(st.pA[g])[2:end])
            truth = argmax(st.true_A[g][:, idx])
            push!(vals, st.pA[g][truth, idx] / sum(st.pA[g][:, idx]))
        end
    end
    return mean(vals)
end

function entropy_A(st::DummyState)
    vals = Float64[]
    for g in eachindex(st.pA), idx in CartesianIndices(size(st.pA[g])[2:end])
        p = st.pA[g][:, idx] ./ sum(st.pA[g][:, idx])
        push!(vals, -sum(p .* log.(p .+ EPS)))
    end
    return mean(vals)
end

function grow_factor1!(st::DummyState)
    old_n1, n2 = length(st.qs[1]), length(st.qs[2])
    new_n1 = old_n1 + 1
    old_pA = st.pA
    old_true_A = st.true_A
    st.pA = [fill(1.0, 2, new_n1, n2), fill(1.0, 2, new_n1, n2)]
    st.true_A = init_A(new_n1, n2)
    for g in 1:2
        st.pA[g][:, 1:old_n1, :] .= old_pA[g]
        st.true_A[g][:, 1:old_n1, :] .= old_true_A[g]
    end
    old_pB = st.pB[1]
    old_true_B = st.true_B[1]
    st.pB[1] = fill(1.0, new_n1, new_n1, 2)
    st.true_B[1] = init_B(new_n1)
    st.pB[1][1:old_n1, 1:old_n1, :] .= old_pB
    st.true_B[1][1:old_n1, 1:old_n1, :] .= old_true_B
    st.qs[1] = vcat(0.85 .* st.qs[1], 0.15)
    st.qs[1] ./= sum(st.qs[1])
    st.state[1] = new_n1
    st.growth_happened = true
    return nothing
end

function run_dummy_seed(seed::Int; trials::Int = 120, growth_trial::Int = 60)
    rng = MersenneTwister(seed)
    st = DummyState(
        [fill(1.0, 2, 2, 2), fill(1.0, 2, 2, 2)],
        [fill(1.0, 2, 2, 2), fill(1.0, 2, 2, 2)],
        [fill(0.5, 2), fill(0.5, 2)],
        init_A(2, 2),
        [init_B(2), init_B(2)],
        [1, 1],
        [[1, 1], [1, 2], [2, 1], [2, 2]],
        false
    )

    previous_action = nothing
    initial_concentration = true_A_concentration(st)
    checkpoints = NamedTuple[]

    for t in 1:trials
        if t == growth_trial
            grow_factor1!(st)
            previous_action = nothing
        end
        obs = env_observe(rng, st)
        A, B = model_from_counts(st)
        prev_qs = [copy(q) for q in st.qs]
        st.qs, joint = infer_states(st, obs, A, B, previous_action)
        update_A!(st, obs, joint)
        previous_action !== nothing && update_B!(st, prev_qs, previous_action)

        A, B = model_from_counts(st)
        scores = score_policies(st, A, B)
        policy_idx = argmax(scores)
        action = copy(st.policies[policy_idx])
        env_step!(rng, st, action)
        previous_action = action

        if t in (1, growth_trial, trials)
            push!(checkpoints, (
                seed = seed,
                trial = t,
                true_A_concentration = true_A_concentration(st),
                A_entropy = entropy_A(st),
                best_policy = policy_idx
            ))
        end
    end

    final_concentration = true_A_concentration(st)
    final_entropy = entropy_A(st)
    return (
        seed = seed,
        initial_true_A_concentration = initial_concentration,
        final_true_A_concentration = final_concentration,
        concentration_gain = final_concentration - initial_concentration,
        final_A_entropy = final_entropy,
        growth_happened = st.growth_happened,
        final_factor1_states = length(st.qs[1]),
        final_factor2_states = length(st.qs[2]),
        checkpoints = checkpoints
    )
end

end
