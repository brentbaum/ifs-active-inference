module IFSBundleInquiry

using LinearAlgebra
using Random
using Statistics
using Main.UnifiedBeautifulLoop

export IFSBundleConfig, JointBundleLearner, BUNDLE_CHANNELS,
    BUNDLE_CONFIGURATIONS, target_conditional_table, factorized_projection,
    maximum_conditional_marginal_error, update!, learned_conditional_table,
    configuration_score, violate_configuration, generate_ifs_bundle_episode,
    BundlePrecisionForecaster, forecast, update_forecaster!,
    infer_bundle_episode, depth_readout

const BUNDLE_CHANNELS = (:self, :world, :policy, :outcome)
const BUNDLE_CONFIGURATIONS = vec(NTuple{4, Int}[
    (b_self, b_world, b_policy, b_outcome)
    for b_self in (-1, 1), b_world in (-1, 1),
        b_policy in (-1, 1), b_outcome in (-1, 1)
])

Base.@kwdef struct IFSBundleConfig
    seeds::Vector{Int} = collect(16901:16910)
    episodes::Int = 120
    training_episodes::Int = 48
    switch_episode::Int = 85
    packet_samples::Int = 3
    action_budget::Int = 2
    inference_iterations::Int = 6
    hyper_newton_steps::Int = 5
    observation_precision::Float64 = 9.0
    contact_precision::Float64 = 5.0
    hyper_innovation_variance::Float64 = 0.30
    parameter_prior_variance::Float64 = 2.0
    regression_evidence_variance::Float64 = 0.45
    regression_forgetting::Float64 = 0.995
    cause_amplitude::Float64 = 0.90
    contact_amplitude::Float64 = 0.85
    dirichlet_alpha::Float64 = 0.75
    local_fields::NTuple{4, Float64} = (0.42, 0.36, 0.22, 0.48)
    coupling_self_world::Float64 = 0.70
    coupling_world_outcome::Float64 = 1.00
    coupling_policy_outcome::Float64 = 0.55
end

mutable struct BundlePrecisionForecaster
    mode::Symbol
    precision::Matrix{Float64}
    information::Vector{Float64}
    prior_precision::Matrix{Float64}
    updates::Int
end

function forecaster_dimensions(mode::Symbol)
    mode == :rigid_global && return 5
    mode == :adaptive_global && return 9
    mode == :independent_local && return 26
    throw(ArgumentError("unknown precision forecaster mode: $mode"))
end

function BundlePrecisionForecaster(mode::Symbol,
        config::IFSBundleConfig = IFSBundleConfig())
    dimensions = forecaster_dimensions(mode)
    prior_precision = Matrix{Float64}(I, dimensions, dimensions) /
        config.parameter_prior_variance
    if mode == :adaptive_global
        for column in 5:8
            prior_precision[column, column] = 6.0
        end
    end
    return BundlePrecisionForecaster(mode, copy(prior_precision),
        zeros(dimensions), prior_precision, 0)
end

mutable struct JointBundleLearner
    counts::Matrix{Float64}
end

JointBundleLearner(config::IFSBundleConfig = IFSBundleConfig()) =
    JointBundleLearner(fill(config.dirichlet_alpha, 2,
        length(BUNDLE_CONFIGURATIONS)))

root_index(root::Int) = root == -1 ? 1 : root == 1 ? 2 :
    throw(ArgumentError("root must be -1 or +1"))

function configuration_index(bundle)
    index = findfirst(==(Tuple(bundle)), BUNDLE_CONFIGURATIONS)
    isnothing(index) && throw(ArgumentError("bundle must contain four -1/+1 values"))
    return index
end

function configuration_score(bundle, root::Int, config::IFSBundleConfig)
    all(value in (-1, 1) for value in bundle) ||
        throw(ArgumentError("bundle must contain only -1/+1 values"))
    length(bundle) == 4 || throw(ArgumentError("bundle must contain four values"))
    local_score = sum(config.local_fields[channel] * root * bundle[channel]
        for channel in eachindex(BUNDLE_CHANNELS))
    coupling_score = root * (
        config.coupling_self_world * bundle[1] * bundle[2] +
        config.coupling_world_outcome * bundle[2] * bundle[4] +
        config.coupling_policy_outcome * bundle[3] * bundle[4])
    return local_score + coupling_score
end

function target_conditional_table(config::IFSBundleConfig = IFSBundleConfig())
    table = zeros(2, length(BUNDLE_CONFIGURATIONS))
    for root in (-1, 1)
        row = root_index(root)
        log_weights = [configuration_score(bundle, root, config)
            for bundle in BUNDLE_CONFIGURATIONS]
        normalizer = UnifiedBeautifulLoop.logsumexp(log_weights)
        table[row, :] .= exp.(log_weights .- normalizer)
    end
    return table
end

function conditional_local_marginals(table)
    size(table) == (2, length(BUNDLE_CONFIGURATIONS)) ||
        throw(DimensionMismatch("conditional table must be 2 by 16"))
    marginals = zeros(2, length(BUNDLE_CHANNELS))
    for root_row in 1:2, channel in eachindex(BUNDLE_CHANNELS)
        marginals[root_row, channel] = sum(table[root_row, index]
            for (index, bundle) in enumerate(BUNDLE_CONFIGURATIONS)
            if bundle[channel] == 1)
    end
    return marginals
end

function factorized_projection(table)
    marginals = conditional_local_marginals(table)
    projection = zeros(size(table))
    for root_row in 1:2, (index, bundle) in enumerate(BUNDLE_CONFIGURATIONS)
        projection[root_row, index] = prod(bundle[channel] == 1 ?
            marginals[root_row, channel] : 1 - marginals[root_row, channel]
            for channel in eachindex(BUNDLE_CHANNELS))
    end
    projection ./= sum(projection; dims = 2)
    return projection
end

maximum_conditional_marginal_error(first_table, second_table) =
    maximum(abs.(conditional_local_marginals(first_table) .-
        conditional_local_marginals(second_table)))

function update!(learner::JointBundleLearner, root::Int, bundle)
    learner.counts[root_index(root), configuration_index(bundle)] += 1
    return learner
end

function learned_conditional_table(learner::JointBundleLearner)
    return learner.counts ./ sum(learner.counts; dims = 2)
end

function violate_configuration(bundle)
    length(bundle) == 4 || throw(ArgumentError("bundle must contain four values"))
    return (bundle[1], bundle[2], bundle[3], -bundle[4])
end

function context_at(episode::Int, config::IFSBundleConfig)
    training_contexts = (-1.0, -0.5, 0.0, 0.5, 1.0)
    episode <= config.training_episodes &&
        return training_contexts[mod1(episode, length(training_contexts))]
    episode < config.switch_episode && return -1.35
    return 1.35
end

phi_index(layer::Int, channel::Int) = (layer - 1) * 4 + channel

function precision_design(context::Float64, mode::Symbol)
    design = zeros(13, forecaster_dimensions(mode))
    channel_loading = (-1.15, -0.35, 0.35, 1.15)
    if mode == :rigid_global
        for layer in 1:3, channel in eachindex(BUNDLE_CHANNELS)
            row = phi_index(layer, channel)
            design[row, layer] = 1.0
            design[row, 4] = channel_loading[channel] * context
        end
        design[13, 5] = 1.0
    elseif mode == :adaptive_global
        for layer in 1:3, channel in eachindex(BUNDLE_CHANNELS)
            row = phi_index(layer, channel)
            design[row, layer] = 1.0
            design[row, 4] = channel_loading[channel] * context
            design[row, 4 + channel] = context
        end
        design[13, 9] = 1.0
    elseif mode == :independent_local
        for row in 1:13
            design[row, row] = 1.0
            design[row, 13 + row] = context
        end
    else
        throw(ArgumentError("unknown precision forecaster mode: $mode"))
    end
    return design
end

function forecast(model::BundlePrecisionForecaster, context,
        config::IFSBundleConfig = IFSBundleConfig())
    design = precision_design(Float64(context), model.mode)
    parameter_covariance = inv(Symmetric(model.precision))
    parameter_mean = parameter_covariance * model.information
    mean_phi = design * parameter_mean
    covariance_phi = design * parameter_covariance * design' +
        Matrix{Float64}(I, 13, 13) * config.hyper_innovation_variance
    return mean_phi, Matrix(covariance_phi)
end

function update_forecaster!(model::BundlePrecisionForecaster, context,
        posterior_phi, observed_channels,
        config::IFSBundleConfig = IFSBundleConfig())
    rows = [phi_index(layer, channel) for layer in 1:3
        for channel in observed_channels]
    push!(rows, 13)
    design = precision_design(Float64(context), model.mode)[rows, :]
    evidence = posterior_phi[rows]
    model.precision .= config.regression_forgetting .* model.precision .+
        (1 - config.regression_forgetting) .* model.prior_precision .+
        (design' * design) ./ config.regression_evidence_variance
    model.information .= config.regression_forgetting .* model.information .+
        (design' * evidence) ./ config.regression_evidence_variance
    model.updates += 1
    return model
end

function true_precision_field(context, episode, config::IFSBundleConfig;
        local_deviation::Bool = false)
    layer_intercepts = (1.25, 0.85, 0.55)
    channel_slopes = (-1.15, -0.35, 0.35, 1.15)
    bundle_phi = [layer_intercepts[layer] + channel_slopes[channel] * context
        for layer in 1:3 for channel in eachindex(BUNDLE_CHANNELS)]
    if local_deviation && episode >= config.switch_episode
        for layer in 1:3
            bundle_phi[phi_index(layer, 4)] -= 2.0channel_slopes[4] * context
        end
    end
    return vcat(bundle_phi, log(config.contact_precision))
end

function sample_configuration(rng, probabilities)
    threshold = rand(rng)
    cumulative = 0.0
    for (bundle, probability) in zip(BUNDLE_CONFIGURATIONS, probabilities)
        cumulative += probability
        threshold <= cumulative && return bundle
    end
    return last(BUNDLE_CONFIGURATIONS)
end

function contact_mean(bundle, root, mode::Symbol, config::IFSBundleConfig)
    mode == :present && return config.contact_amplitude *
        (0.70 + 0.20bundle[4] + 0.10root)
    mode == :misattuned && return -config.contact_amplitude *
        (0.70 - 0.20bundle[4] - 0.10root)
    mode == :absent && return 0.0
    throw(ArgumentError("unknown contact mode: $mode"))
end

function generate_ifs_bundle_episode(seed::Int, episode::Int;
        config::IFSBundleConfig = IFSBundleConfig(),
        scene_mode::Symbol = :joint, contact_mode::Symbol = :present,
        local_deviation::Bool = false)
    rng = MersenneTwister(seed + 10_000episode)
    root = rand(rng, Bool) ? 1 : -1
    joint = target_conditional_table(config)
    table = scene_mode == :joint || scene_mode == :configuration_violating ?
        joint : scene_mode == :factorized ? factorized_projection(joint) :
        throw(ArgumentError("unknown scene mode: $scene_mode"))
    bundle = sample_configuration(rng, view(table, root_index(root), :))
    scene_mode == :configuration_violating && (bundle = violate_configuration(bundle))
    context = context_at(episode, config)
    true_phi = true_precision_field(context, episode, config;
        local_deviation = local_deviation)
    states = zeros(3, length(BUNDLE_CHANNELS), config.packet_samples)
    observations = zeros(length(BUNDLE_CHANNELS), config.packet_samples)
    for sample in 1:config.packet_samples, channel in eachindex(BUNDLE_CHANNELS)
        states[3, channel, sample] = config.cause_amplitude * bundle[channel] +
            exp(-0.5true_phi[phi_index(3, channel)]) * randn(rng)
        states[2, channel, sample] = states[3, channel, sample] +
            exp(-0.5true_phi[phi_index(2, channel)]) * randn(rng)
        states[1, channel, sample] = states[2, channel, sample] +
            exp(-0.5true_phi[phi_index(1, channel)]) * randn(rng)
        observations[channel, sample] = states[1, channel, sample] +
            randn(rng) / sqrt(config.observation_precision)
    end
    contact_noise_precision = contact_mode == :absent ? 0.40 : config.contact_precision
    contact = contact_mean(bundle, root, contact_mode, config) +
        randn(rng) / sqrt(contact_noise_precision)
    return (root = root, bundle = bundle, scene_mode = scene_mode,
        context = context, true_phi = true_phi, states = states,
        observations = observations, contact = contact,
        contact_mode = contact_mode)
end

function unified_adapter_config(config::IFSBundleConfig)
    return UnifiedBeautifulLoop.UnifiedConfig(
        inference_iterations = config.inference_iterations,
        hyper_newton_steps = config.hyper_newton_steps,
        observation_precision = config.observation_precision,
        hyper_innovation_variance = config.hyper_innovation_variance,
        parameter_prior_variance = config.parameter_prior_variance,
        regression_evidence_variance = config.regression_evidence_variance,
        regression_forgetting = config.regression_forgetting,
        samples_per_action = config.packet_samples,
        cause_amplitude = config.cause_amplitude,
    )
end

function bundle_branch_posterior(observation, cause, mean_phi, variance_phi,
        channel, config::IFSBundleConfig)
    expected_precision = [exp(mean_phi[phi_index(layer, channel)] +
        0.5variance_phi[phi_index(layer, channel)]) for layer in 1:3]
    links = ([1.0, -1.0, 0.0], [0.0, 1.0, -1.0], [0.0, 0.0, 1.0])
    posterior_precision = Matrix{Float64}(I, 3, 3) * 1.0e-10
    information = zeros(3)
    posterior_precision[1, 1] += config.observation_precision
    information[1] += config.observation_precision * observation
    for layer in 1:3
        posterior_precision .+= expected_precision[layer] .*
            (links[layer] * links[layer]')
    end
    information .+= expected_precision[3] * config.cause_amplitude * cause .* links[3]
    covariance = inv(Symmetric(posterior_precision))
    state_mean = covariance * information
    residuals = [
        (state_mean[1] - state_mean[2])^2 + covariance[1, 1] +
            covariance[2, 2] - 2covariance[1, 2],
        (state_mean[2] - state_mean[3])^2 + covariance[2, 2] +
            covariance[3, 3] - 2covariance[2, 3],
        (state_mean[3] - config.cause_amplitude * cause)^2 + covariance[3, 3],
    ]
    observation_residual = (observation - state_mean[1])^2 + covariance[1, 1]
    transition_energy = [0.5 * (log(2pi) -
        mean_phi[phi_index(layer, channel)] +
        expected_precision[layer] * residuals[layer]) for layer in 1:3]
    observation_energy = 0.5 * (log(2pi) - log(config.observation_precision) +
        config.observation_precision * observation_residual)
    entropy = 0.5 * (3 * (1 + log(2pi)) + logdet(covariance))
    return (residuals = residuals,
        local_free_energy = observation_energy + sum(transition_energy) - entropy)
end

expected_contact_mean(bundle, root, config::IFSBundleConfig) =
    config.contact_amplitude * (0.70 + 0.20bundle[4] + 0.10root)

function bundle_state_update(observations, contact, selected_channels,
        mean_phi, covariance_phi, conditional_table,
        config::IFSBundleConfig; pseudo_root = nothing,
        pseudo_reliability::Float64 = 0.5)
    variance_phi = diag(covariance_phi)
    branch_results = Array{Any}(undef, 2, 4, config.packet_samples)
    branch_cost = zeros(2, 4)
    for (cause_index, cause) in enumerate((-1, 1)),
            channel in selected_channels, sample in 1:config.packet_samples
        result = bundle_branch_posterior(observations[channel, sample], cause,
            mean_phi, variance_phi, channel, config)
        branch_results[cause_index, channel, sample] = result
        branch_cost[cause_index, channel] += result.local_free_energy
    end
    contact_precision = exp(mean_phi[13] + 0.5variance_phi[13])
    hypotheses = NamedTuple[]
    log_weights = Float64[]
    for root in (-1, 1), (bundle_index, bundle) in enumerate(BUNDLE_CONFIGURATIONS)
        log_prior = -log(2) + log(max(conditional_table[root_index(root),
            bundle_index], 1.0e-300))
        sensory_cost = sum(branch_cost[bundle[channel] == 1 ? 2 : 1, channel]
            for channel in selected_channels; init = 0.0)
        contact_residual = (contact - expected_contact_mean(bundle, root, config))^2
        contact_cost = 0.5 * (log(2pi) - mean_phi[13] +
            contact_precision * contact_residual)
        conclusion_cost = if isnothing(pseudo_root)
            0.0
        else
            reliability = clamp(pseudo_reliability, 1.0e-6, 1 - 1.0e-6)
            -log(root == pseudo_root ? reliability : 1 - reliability)
        end
        total_cost = sensory_cost + contact_cost + conclusion_cost
        push!(hypotheses, (root = root, bundle = bundle,
            log_prior = log_prior, cost = total_cost,
            contact_residual = contact_residual))
        push!(log_weights, log_prior - total_cost)
    end
    normalizer = UnifiedBeautifulLoop.logsumexp(log_weights)
    weights = exp.(log_weights .- normalizer)
    probability_positive = sum(weight for (hypothesis, weight) in
        zip(hypotheses, weights) if hypothesis.root == 1)
    bundle_probability_positive = [sum(weight for (hypothesis, weight) in
        zip(hypotheses, weights) if hypothesis.bundle[channel] == 1)
        for channel in eachindex(BUNDLE_CHANNELS)]
    residuals = zeros(13)
    for (hypothesis, weight) in zip(hypotheses, weights),
            channel in selected_channels, sample in 1:config.packet_samples
        cause_index = hypothesis.bundle[channel] == 1 ? 2 : 1
        result = branch_results[cause_index, channel, sample]
        for layer in 1:3
            residuals[phi_index(layer, channel)] +=
                weight * result.residuals[layer] / config.packet_samples
        end
    end
    residuals[13] = sum(weight * hypothesis.contact_residual
        for (hypothesis, weight) in zip(hypotheses, weights))
    cause_term = sum(weight * (log(max(weight, 1.0e-300)) -
        hypothesis.log_prior) for (hypothesis, weight) in zip(hypotheses, weights))
    expected_local = sum(weight * hypothesis.cost
        for (hypothesis, weight) in zip(hypotheses, weights))
    return (probability_positive = probability_positive,
        bundle_probability_positive = bundle_probability_positive,
        hypotheses = hypotheses, weights = weights, residuals = residuals,
        cause_term = cause_term, expected_local = expected_local,
        local_free_energy = expected_local)
end

function infer_bundle_episode(observations, contact, selected_channels,
        prior_mean, prior_covariance, conditional_table;
        config::IFSBundleConfig = IFSBundleConfig(), pseudo_root = nothing,
        pseudo_reliability::Float64 = 0.5)
    unified = unified_adapter_config(config)
    mean_phi = copy(prior_mean)
    covariance_phi = copy(prior_covariance)
    active = zeros(13)
    for channel in selected_channels, layer in 1:3
        active[phi_index(layer, channel)] = config.packet_samples
    end
    active[13] = 1.0
    state = bundle_state_update(observations, contact, selected_channels,
        mean_phi, covariance_phi, conditional_table, config;
        pseudo_root = pseudo_root, pseudo_reliability = pseudo_reliability)
    current = UnifiedBeautifulLoop.joint_free_energy(state, mean_phi,
        covariance_phi, prior_mean, prior_covariance)
    trace = NamedTuple[]
    for iteration in 1:config.inference_iterations
        proposed_mean, proposed_covariance = UnifiedBeautifulLoop.hyper_update(
            prior_mean, prior_covariance, state.residuals, active,
            mean_phi, covariance_phi, unified)
        proposed_state = bundle_state_update(observations, contact,
            selected_channels, proposed_mean, proposed_covariance,
            conditional_table, config; pseudo_root = pseudo_root,
            pseudo_reliability = pseudo_reliability)
        proposed = UnifiedBeautifulLoop.joint_free_energy(proposed_state,
            proposed_mean, proposed_covariance, prior_mean, prior_covariance)
        scale = 1.0
        while proposed > current + 1.0e-8 && scale >= 1.0e-5
            scale *= 0.5
            candidate_mean = (1 - scale) .* mean_phi .+ scale .* proposed_mean
            candidate_covariance = (1 - scale) .* covariance_phi .+
                scale .* proposed_covariance
            candidate_state = bundle_state_update(observations, contact,
                selected_channels, candidate_mean, candidate_covariance,
                conditional_table, config; pseudo_root = pseudo_root,
                pseudo_reliability = pseudo_reliability)
            candidate = UnifiedBeautifulLoop.joint_free_energy(candidate_state,
                candidate_mean, candidate_covariance, prior_mean, prior_covariance)
            proposed_mean, proposed_covariance = candidate_mean, candidate_covariance
            proposed_state, proposed = candidate_state, candidate
        end
        if proposed <= current + 1.0e-8
            mean_phi, covariance_phi = proposed_mean, proposed_covariance
            state, current = proposed_state, proposed
        end
        hyper_energy = UnifiedBeautifulLoop.gaussian_kl(mean_phi,
            covariance_phi, prior_mean, prior_covariance)
        push!(trace, (iteration = iteration,
            local_free_energy = state.local_free_energy,
            hyper_free_energy = hyper_energy,
            joint_free_energy = current))
    end
    return merge(state, (posterior_phi = mean_phi,
        posterior_covariance = covariance_phi, trace = trace))
end

function depth_readout(result)
    confidence = 1 - mean(diag(result.posterior_covariance) ./
        (1 .+ diag(result.posterior_covariance)))
    breadth = mean(abs.(result.bundle_probability_positive .- 0.5)) * 2
    return clamp(confidence * (1 - breadth), 0.0, 1.0)
end

end
