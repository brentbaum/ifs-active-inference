RxInfer.@model function sim1_joint_hmm(yv, ya, transition, Bv, Ba, prior_state)
    state_prev = prior_state
    for t in 1:length(yv)
        state[t] ~ DiscreteTransition(state_prev, transition)
        yv[t] ~ DiscreteTransition(state[t], Bv)
        ya[t] ~ DiscreteTransition(state[t], Ba)
        state_prev = state[t]
    end
end

function infer_joint_hmm_rxinfer(
    yv_obs::Vector{Int},
    ya_obs::Vector{Int},
    transition::Matrix{Float64},
    Bv::Matrix{Float64},
    Ba::Matrix{Float64},
    prior::Vector{Float64}
)
    yv_data = [one_hot(y, size(Bv, 1)) for y in yv_obs]
    ya_data = [one_hot(y, size(Ba, 1)) for y in ya_obs]

    result = infer(
        model = sim1_joint_hmm(transition = transition, Bv = Bv, Ba = Ba, prior_state = prior),
        data = (yv = yv_data, ya = ya_data)
    )

    posteriors = result.posteriors[:state]
    rows = reduce(vcat, [reshape(probvec(q), 1, :) for q in posteriors])
    return rows, result
end

function forward_filter_joint_hmm(
    yv_obs::Vector{Int},
    ya_obs::Vector{Int},
    transition::Matrix{Float64},
    Bv::Matrix{Float64},
    Ba::Matrix{Float64},
    prior::Vector{Float64}
)
    T = length(yv_obs)
    n_joint = length(prior)
    posteriors = zeros(Float64, T, n_joint)
    log_evidence = 0.0
    previous = copy(prior)

    for t in 1:T
        prediction = transition * previous
        likelihood = Bv[yv_obs[t], :] .* Ba[ya_obs[t], :]
        unnormalized = prediction .* likelihood
        evidence = sum(unnormalized)
        evidence = max(evidence, 1e-12)
        posterior = unnormalized ./ evidence
        posteriors[t, :] = posterior
        log_evidence += log(evidence)
        previous = posterior
    end

    return posteriors, log_evidence
end

function joint_hmm_inference_bundle(
    yv_obs::Vector{Int},
    ya_obs::Vector{Int},
    transition::Matrix{Float64},
    Bv::Matrix{Float64},
    Ba::Matrix{Float64},
    prior::Vector{Float64}
)
    smoothed_posteriors, result = infer_joint_hmm_rxinfer(yv_obs, ya_obs, transition, Bv, Ba, prior)
    filtered_posteriors, log_evidence = forward_filter_joint_hmm(yv_obs, ya_obs, transition, Bv, Ba, prior)
    return (
        smoothed_joint_posteriors = smoothed_posteriors,
        filtered_joint_posteriors = filtered_posteriors,
        log_evidence = log_evidence,
        rxinfer_result = result
    )
end
