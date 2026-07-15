module IFSBundleInquiry

using LinearAlgebra
using Random
using Statistics
using Main.UnifiedBeautifulLoop

export IFSBundleConfig, JointBundleLearner, BUNDLE_CHANNELS,
    BUNDLE_CONFIGURATIONS, target_conditional_table, factorized_projection,
    maximum_conditional_marginal_error, update!, learned_conditional_table,
    configuration_score, violate_configuration, generate_ifs_bundle_episode

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
    cause_amplitude::Float64 = 0.90
    contact_amplitude::Float64 = 0.85
    dirichlet_alpha::Float64 = 0.75
    local_fields::NTuple{4, Float64} = (0.42, 0.36, 0.22, 0.48)
    coupling_self_world::Float64 = 0.70
    coupling_world_outcome::Float64 = 1.00
    coupling_policy_outcome::Float64 = 0.55
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

end
