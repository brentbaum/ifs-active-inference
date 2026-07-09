#!/usr/bin/env julia

using LinearAlgebra
using Random
using Statistics
using Printf

const EPS = 1e-12

mutable struct SpikeState
    pA::Vector{Array{Float64}}
    pB::Vector{Array{Float64, 3}}
    qs::Vector{Vector{Float64}}
    true_A::Vector{Array{Float64}}
    true_B::Vector{Array{Float64, 3}}
    state::Vector{Int}
    policies::Vector{Vector{Int}}
    growth_happened::Bool
end

normalize_cols(A) = A ./ max.(sum(A; dims = 1), EPS)

function normalize_B(B::Array{Float64, 3})
    out = copy(B)
    for a in axes(B, 3)
        out[:, :, a] .= B[:, :, a] ./ max.(sum(B[:, :, a]; dims = 1), EPS)
    end
    out
end

function softmax(x)
    z = x .- maximum(x)
    ex = exp.(z)
    ex ./ sum(ex)
end

function onehot(i, n)
    v = zeros(Float64, n)
    v[i] = 1.0
    v
end

function init_A(n1::Int, n2::Int)
    A1 = zeros(Float64, 2, n1, n2)
    A2 = zeros(Float64, 2, n1, n2)
    for s1 in 1:n1, s2 in 1:n2
        A1[:, s1, s2] .= s1 == 1 ? [0.9, 0.1] : [0.1, 0.9]
        A2[:, s1, s2] .= s2 == 1 ? [0.9, 0.1] : [0.1, 0.9]
    end
    [A1, A2]
end

function init_B(n::Int)
    B = zeros(Float64, n, n, 2)
    for s in 1:n
        B[1, s, 1] = 0.85
        B[min(2, n), s, 1] += 0.15
        B[n, s, 2] = 0.85
        B[max(1, n - 1), s, 2] += 0.15
    end
    normalize_B(B)
end

function model_from_counts(st::SpikeState)
    A = [normalize_cols(a) for a in st.pA]
    B = [normalize_B(b) for b in st.pB]
    return A, B
end

function likelihood(A, obs::Vector{Int}, ns::Vector{Int})
    L = ones(Float64, ns...)
    for g in eachindex(A)
        L .*= selectdim(A[g], 1, obs[g])
    end
    L
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
    J
end

function marginals_from_joint(J)
    qs = Vector{Vector{Float64}}(undef, ndims(J))
    for f in 1:ndims(J)
        dims_to_sum = Tuple(i for i in 1:ndims(J) if i != f)
        q = vec(sum(J; dims = dims_to_sum))
        qs[f] = q ./ max(sum(q), EPS)
    end
    qs
end

function infer_states(st::SpikeState, obs::Vector{Int}, A, B, action::Union{Nothing, Vector{Int}})
    prior = if action === nothing
        [copy(q) for q in st.qs]
    else
        [B[f][:, :, action[f]] * st.qs[f] for f in eachindex(st.qs)]
    end
    J = joint_from_marginals(prior) .* likelihood(A, obs, length.(prior))
    J ./= max(sum(J), EPS)
    marginals_from_joint(J), J
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
    qo ./ max(sum(qo), EPS)
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
    h
end

function score_policies(st::SpikeState, A, B)
    C = [log.([0.25, 0.75]), log.([0.25, 0.75])]
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
    scores
end

function sample_categorical(rng, p)
    u = rand(rng)
    c = 0.0
    for i in eachindex(p)
        c += p[i]
        if u <= c
            return i
        end
    end
    return length(p)
end

function env_step!(rng, st::SpikeState, action::Vector{Int})
    for f in eachindex(st.state)
        st.state[f] = sample_categorical(rng, st.true_B[f][:, st.state[f], action[f]])
    end
end

function env_observe(rng, st::SpikeState)
    [sample_categorical(rng, vec(st.true_A[g][:, st.state...])) for g in eachindex(st.true_A)]
end

function update_A!(st::SpikeState, obs::Vector{Int}, joint)
    for g in eachindex(st.pA)
        view(st.pA[g], obs[g], ntuple(i -> Colon(), ndims(joint))...) .+= joint
    end
end

function update_B!(st::SpikeState, prev_qs, action::Vector{Int})
    for f in eachindex(st.pB)
        st.pB[f][:, :, action[f]] .+= st.qs[f] * prev_qs[f]'
    end
end

function true_A_concentration(st::SpikeState)
    vals = Float64[]
    for g in eachindex(st.pA)
        for idx in CartesianIndices(size(st.pA[g])[2:end])
            truth = argmax(st.true_A[g][:, idx])
            push!(vals, st.pA[g][truth, idx] / sum(st.pA[g][:, idx]))
        end
    end
    mean(vals)
end

function entropy_A(st::SpikeState)
    vals = Float64[]
    for g in eachindex(st.pA), idx in CartesianIndices(size(st.pA[g])[2:end])
        p = st.pA[g][:, idx] ./ sum(st.pA[g][:, idx])
        push!(vals, -sum(p .* log.(p .+ EPS)))
    end
    mean(vals)
end

function loggamma_lanczos(z::Float64)
    coeffs = [
        676.5203681218851,
        -1259.1392167224028,
        771.32342877765313,
        -176.61502916214059,
        12.507343278686905,
        -0.13857109526572012,
        9.9843695780195716e-6,
        1.5056327351493116e-7
    ]
    if z < 0.5
        return log(pi) - log(sin(pi * z)) - loggamma_lanczos(1.0 - z)
    end
    z -= 1.0
    x = 0.99999999999980993
    for (i, c) in enumerate(coeffs)
        x += c / (z + i)
    end
    t = z + length(coeffs) - 0.5
    return 0.5 * log(2pi) + (z + 0.5) * log(t) - t + log(x)
end

function logbeta(alpha)
    sum(loggamma_lanczos, Float64.(alpha)) - loggamma_lanczos(sum(alpha))
end

function dirichlet_log_evidence(counts, prior)
    total = 0.0
    for idx in CartesianIndices(size(counts)[2:end])
        c = counts[:, idx]
        p = prior[:, idx]
        total += logbeta(c .+ p) - logbeta(p)
    end
    total
end

# Tying reduction: reduced model shares one likelihood column between states 1 and 2.
# Correct comparison is pooled marginal evidence, per column-pair and rest-index:
#   delta = logB(a + n1 + n2) - logB(a + n1) - logB(a + n2) + logB(a)
# delta > 0 favors the tied (simpler) model. NOT the count-averaging comparison
# (that returns 0 for symmetric data and lacks the Occam term).
function bmr_delta_f(counts)
    size(counts, 2) < 2 && return 0.0
    a = ones(size(counts, 1))
    total = 0.0
    for rest in CartesianIndices(size(counts)[3:end])
        n1 = counts[:, 1, Tuple(rest)...] .- 1.0
        n2 = counts[:, 2, Tuple(rest)...] .- 1.0
        total += logbeta(a .+ n1 .+ n2) - logbeta(a .+ n1) - logbeta(a .+ n2) + logbeta(a)
    end
    total
end

# Canonical Friston-2017 prior-swap BMR over Dirichlet counts (the T1.3 form;
# matches derivations/d2_toy_demo.py): posterior counts `post`, full prior b_f,
# reduced prior b_r. delta > 0 favors the reduced model.
function bmr_delta_f_prior_swap(post, b_f, b_r)
    total = 0.0
    for idx in CartesianIndices(size(post)[2:end])
        p, f, r = post[:, idx], b_f[:, idx], b_r[:, idx]
        total += logbeta(f) - logbeta(r) + logbeta(p .+ r .- f) - logbeta(p)
    end
    total
end

function grow_factor1!(st::SpikeState)
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
end

function run_spike(; seed = 7, trials = 200)
    rng = MersenneTwister(seed)
    st = SpikeState(
        [fill(1.0, 2, 2, 2), fill(1.0, 2, 2, 2)],
        [fill(1.0, 2, 2, 2), fill(1.0, 2, 2, 2)],
        [fill(0.5, 2), fill(0.5, 2)],
        init_A(2, 2),
        [init_B(2), init_B(2)],
        [1, 1],
        [[1, 1], [1, 2], [2, 1], [2, 2]],
        false
    )

    started = time()
    prev_action = nothing
    initial_conc = true_A_concentration(st)
    checkpoints = Dict{Int, Tuple{Float64, Float64}}()

    for t in 1:trials
        if t == 100
            grow_factor1!(st)
            prev_action = nothing
            @printf("growth trial=%d ns=(%d,%d) pA1_shape=%s pB1_shape=%s\n",
                    t, length(st.qs[1]), length(st.qs[2]), string(size(st.pA[1])), string(size(st.pB[1])))
        end

        obs = env_observe(rng, st)
        A, B = model_from_counts(st)
        prev_qs = [copy(q) for q in st.qs]
        st.qs, joint = infer_states(st, obs, A, B, prev_action)
        update_A!(st, obs, joint)
        if prev_action !== nothing
            update_B!(st, prev_qs, prev_action)
        end

        A, B = model_from_counts(st)
        scores = score_policies(st, A, B)
        policy_idx = argmax(scores)
        action = copy(st.policies[policy_idx])
        env_step!(rng, st, action)
        prev_action = action

        if t in (1, 50, 99, 100, 150, 200)
            checkpoints[t] = (true_A_concentration(st), entropy_A(st))
            @printf("trial=%03d true_A_concentration=%.4f A_entropy=%.4f best_policy=%d efe_scores=%s\n",
                    t, checkpoints[t][1], checkpoints[t][2], policy_idx, string(round.(scores; digits = 3)))
        end
    end

    elapsed = time() - started
    final_conc = true_A_concentration(st)
    final_entropy = entropy_A(st)
    delta_f = bmr_delta_f(st.pA[1])
    @printf("summary candidate=v10_port trials=%d elapsed_sec=%.4f initial_true_A_concentration=%.4f final_true_A_concentration=%.4f final_A_entropy=%.4f growth_happened=%s bmr_delta_f_reduced_minus_full=%.4f\n",
            trials, elapsed, initial_conc, final_conc, final_entropy, string(st.growth_happened), delta_f)
end

run_spike()
