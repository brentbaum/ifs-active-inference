module UnifiedRelationalAgent

using LinearAlgebra
using Random
using Statistics
using Main.GlobalPrecisionField
using Main.UnifiedBeautifulLoop

export RelationalAgentConfig, local_mutual_information,
    generate_relational_episode, infer_relational_episode,
    run_relational_agent_seed, run_unified_relational_pilot

Base.@kwdef struct RelationalAgentConfig
    seeds::Vector{Int} = collect(13001:13010)
    episodes::Int = 180
    training_episodes::Int = 60
    switch_episode::Int = 101
    packet_samples::Int = 4
    action_budget::Int = 2
    local_field::Float64 = 0.10
    relational_field::Float64 = 1.50
    violation_rate::Float64 = 0.05
    inference_iterations::Int = 8
    hyper_newton_steps::Int = 6
    observation_precision::Float64 = 8.0
    hyper_innovation_variance::Float64 = 0.30
    parameter_prior_variance::Float64 = 2.0
    regression_evidence_variance::Float64 = 0.45
    regression_forgetting::Float64 = 0.995
    cause_amplitude::Float64 = 1.05
end

const LOCAL_CONFIGURATIONS = [
    (z1, z2, z3) for z1 in (-1, 1), z2 in (-1, 1), z3 in (-1, 1)
]

function unified_config(config::RelationalAgentConfig)
    return UnifiedBeautifulLoop.UnifiedConfig(
        seeds = config.seeds,
        episodes = config.episodes,
        training_episodes = config.training_episodes,
        switch_episode = config.switch_episode,
        structural_break_episode = config.episodes + 1,
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

function context_at(episode, config::RelationalAgentConfig)
    training_contexts = (-1.0, -0.5, 0.0, 0.5, 1.0)
    episode <= config.training_episodes &&
        return training_contexts[mod1(episode, length(training_contexts))]
    episode < config.switch_episode && return -1.4
    return 1.4
end

function true_precision_field(context)
    intercepts = [1.20, 0.80, 0.50]
    slopes = [-1.30, 0.0, 1.30]
    return [intercepts[layer] + slopes[channel] * context
        for layer in 1:3 for channel in 1:3]
end

function relational_log_weights(global_cause, config)
    return [config.local_field * global_cause * sum(local_causes) +
        config.relational_field * global_cause *
            (local_causes[1] * local_causes[2] +
             local_causes[1] * local_causes[3] +
             local_causes[2] * local_causes[3])
        for local_causes in LOCAL_CONFIGURATIONS]
end

function relational_probabilities(global_cause, config)
    values = relational_log_weights(global_cause, config)
    normalizer = UnifiedBeautifulLoop.logsumexp(values)
    return exp.(values .- normalizer)
end

function local_positive_probability(global_cause, channel, config)
    probabilities = relational_probabilities(global_cause, config)
    return sum(probability for (local_causes, probability) in
        zip(LOCAL_CONFIGURATIONS, probabilities) if local_causes[channel] == 1)
end

function scene_log_prior(global_cause, local_causes, mode::Symbol, config)
    if mode == :relational
        values = relational_log_weights(global_cause, config)
        normalizer = UnifiedBeautifulLoop.logsumexp(values)
        index = findfirst(==(local_causes), LOCAL_CONFIGURATIONS)
        return -log(2) + values[index] - normalizer
    elseif mode == :factorized
        value = -log(2)
        for channel in 1:3
            positive = local_positive_probability(global_cause, channel, config)
            value += log(local_causes[channel] == 1 ? positive : 1 - positive)
        end
        return value
    end
    throw(ArgumentError("unknown scene mode: $mode"))
end

function local_mutual_information(config::RelationalAgentConfig)
    information = 0.0
    for global_cause in (-1, 1), local_cause in (-1, 1)
        conditional = local_cause == 1 ?
            local_positive_probability(global_cause, 1, config) :
            1 - local_positive_probability(global_cause, 1, config)
        joint = 0.5conditional
        marginal = 0.5sum(local_cause == 1 ?
            local_positive_probability(g, 1, config) :
            1 - local_positive_probability(g, 1, config) for g in (-1, 1))
        information += joint * log(joint / (0.5marginal))
    end
    return information
end

function sample_local_causes(rng, global_cause, mode, config)
    probabilities = mode == :relational ?
        relational_probabilities(global_cause, config) :
        [exp(scene_log_prior(global_cause, local_causes, :factorized, config) + log(2))
            for local_causes in LOCAL_CONFIGURATIONS]
    threshold = rand(rng)
    cumulative = 0.0
    for (local_causes, probability) in zip(LOCAL_CONFIGURATIONS, probabilities)
        cumulative += probability
        threshold <= cumulative && return local_causes
    end
    return last(LOCAL_CONFIGURATIONS)
end

function generate_relational_episode(seed::Int, episode::Int;
        config::RelationalAgentConfig = RelationalAgentConfig())
    rng = MersenneTwister(seed + 10_000episode)
    context = context_at(episode, config)
    true_phi = true_precision_field(context)
    global_cause = rand(rng, Bool) ? 1 : -1
    violation = rand(rng) < config.violation_rate
    local_causes = sample_local_causes(rng, global_cause,
        violation ? :factorized : :relational, config)
    states = zeros(3, 3, config.packet_samples)
    observations = zeros(3, config.packet_samples)
    for sample in 1:config.packet_samples, channel in 1:3
        states[3, channel, sample] = config.cause_amplitude * local_causes[channel] +
            exp(-0.5true_phi[UnifiedBeautifulLoop.component_index(3, channel)]) * randn(rng)
        states[2, channel, sample] = states[3, channel, sample] +
            exp(-0.5true_phi[UnifiedBeautifulLoop.component_index(2, channel)]) * randn(rng)
        states[1, channel, sample] = states[2, channel, sample] +
            exp(-0.5true_phi[UnifiedBeautifulLoop.component_index(1, channel)]) * randn(rng)
        observations[channel, sample] = states[1, channel, sample] +
            randn(rng) / sqrt(config.observation_precision)
    end
    return (global_cause = global_cause, local_causes = local_causes,
        violation = violation, context = context, true_phi = true_phi,
        states = states, observations = observations)
end

function relational_state_update(observations, selected_channels, mean_phi,
        covariance_phi, config::RelationalAgentConfig; mode::Symbol = :relational)
    unified = unified_config(config)
    variance_phi = diag(covariance_phi)
    branch_results = Array{Any}(undef, 2, 3, config.packet_samples)
    branch_cost = zeros(2, 3)
    for (local_index, local_cause) in enumerate((-1, 1)),
            channel in selected_channels, sample in 1:config.packet_samples
        result = UnifiedBeautifulLoop.branch_posterior(
            observations[channel, sample], local_cause, mean_phi,
            variance_phi, channel, unified)
        branch_results[local_index, channel, sample] = result
        branch_cost[local_index, channel] += result.local_free_energy
    end
    hypotheses = NamedTuple[]
    log_weights = Float64[]
    for global_cause in (-1, 1), local_causes in LOCAL_CONFIGURATIONS
        log_prior = scene_log_prior(global_cause, local_causes, mode, config)
        cost = sum(branch_cost[local_causes[channel] == 1 ? 2 : 1, channel]
            for channel in selected_channels; init = 0.0)
        push!(hypotheses, (global_cause = global_cause,
            local_causes = local_causes, log_prior = log_prior, cost = cost))
        push!(log_weights, log_prior - cost)
    end
    normalizer = UnifiedBeautifulLoop.logsumexp(log_weights)
    weights = exp.(log_weights .- normalizer)
    probability_positive = sum(weight for (hypothesis, weight) in zip(hypotheses, weights)
        if hypothesis.global_cause == 1)
    residuals = zeros(9)
    local_energy = zeros(3)
    for (hypothesis, weight) in zip(hypotheses, weights),
            channel in selected_channels, sample in 1:config.packet_samples
        local_index = hypothesis.local_causes[channel] == 1 ? 2 : 1
        result = branch_results[local_index, channel, sample]
        for layer in 1:3
            residuals[UnifiedBeautifulLoop.component_index(layer, channel)] +=
                weight * result.residuals[layer] / config.packet_samples
            local_energy[layer] += weight *
                (result.transition_energy[layer] - result.marginal_entropy[layer])
        end
    end
    cause_term = sum(weight * (log(max(weight, 1.0e-300)) - hypothesis.log_prior)
        for (hypothesis, weight) in zip(hypotheses, weights))
    expected_local = sum(weight * hypothesis.cost
        for (hypothesis, weight) in zip(hypotheses, weights))
    return (probability_positive = probability_positive,
        hypotheses = hypotheses, weights = weights, residuals = residuals,
        local_energy = local_energy, cause_term = cause_term,
        expected_local = expected_local)
end

function infer_relational_episode(observations, selected_channels, prior_mean,
        prior_covariance; mode::Symbol = :relational,
        config::RelationalAgentConfig = RelationalAgentConfig())
    unified = unified_config(config)
    mean_phi = copy(prior_mean)
    covariance_phi = copy(prior_covariance)
    active = zeros(9)
    for channel in selected_channels, layer in 1:3
        active[UnifiedBeautifulLoop.component_index(layer, channel)] =
            config.packet_samples
    end
    state = relational_state_update(observations, selected_channels,
        mean_phi, covariance_phi, config; mode = mode)
    current = UnifiedBeautifulLoop.joint_free_energy(state, mean_phi,
        covariance_phi, prior_mean, prior_covariance)
    trace = NamedTuple[]
    for iteration in 1:config.inference_iterations
        proposed_mean, proposed_covariance = UnifiedBeautifulLoop.hyper_update(
            prior_mean, prior_covariance, state.residuals, active,
            mean_phi, covariance_phi, unified)
        proposed_state = relational_state_update(observations, selected_channels,
            proposed_mean, proposed_covariance, config; mode = mode)
        proposed = UnifiedBeautifulLoop.joint_free_energy(proposed_state,
            proposed_mean, proposed_covariance, prior_mean, prior_covariance)
        scale = 1.0
        while proposed > current + 1.0e-8 && scale >= 1.0e-5
            scale *= 0.5
            candidate_mean = (1 - scale) .* mean_phi .+ scale .* proposed_mean
            candidate_covariance = (1 - scale) .* covariance_phi .+
                scale .* proposed_covariance
            candidate_state = relational_state_update(observations,
                selected_channels, candidate_mean, candidate_covariance,
                config; mode = mode)
            candidate = UnifiedBeautifulLoop.joint_free_energy(candidate_state,
                candidate_mean, candidate_covariance, prior_mean, prior_covariance)
            proposed_mean, proposed_covariance = candidate_mean, candidate_covariance
            proposed_state, proposed = candidate_state, candidate
        end
        if proposed <= current + 1.0e-8
            mean_phi, covariance_phi = proposed_mean, proposed_covariance
            state, current = proposed_state, proposed
        end
        push!(trace, (iteration = iteration, joint_free_energy = current))
    end
    return merge(state, (posterior_phi = mean_phi,
        posterior_covariance = covariance_phi, trace = trace))
end

binary_entropy(probability) = probability <= 1.0e-12 || probability >= 1 - 1.0e-12 ?
    0.0 : -probability * log(probability) - (1 - probability) * log(1 - probability)

function sensor_reliability(mean_phi, channel, config; precision_blind = false)
    if precision_blind
        transition_variance = mean(exp(-mean(mean_phi)) for _ in 1:3)
    else
        transition_variance = sum(exp(-mean_phi[
            UnifiedBeautifulLoop.component_index(layer, channel)]) for layer in 1:3)
    end
    signal_to_noise = config.cause_amplitude /
        sqrt(transition_variance + inv(config.observation_precision))
    return 1 / (1 + exp(-1.702signal_to_noise))
end

function expected_information_gain(state, mean_phi, channel, config;
        precision_blind = false)
    current_entropy = binary_entropy(state.probability_positive)
    reliability = sensor_reliability(mean_phi, channel, config;
        precision_blind = precision_blind)
    expected_entropy = 0.0
    for outcome in (-1, 1)
        likelihoods = [outcome == hypothesis.local_causes[channel] ?
            reliability : 1 - reliability for hypothesis in state.hypotheses]
        outcome_probability = dot(state.weights, likelihoods)
        positive_mass = sum(weight * likelihood for (hypothesis, weight, likelihood)
            in zip(state.hypotheses, state.weights, likelihoods)
            if hypothesis.global_cause == 1)
        posterior_positive = positive_mass / max(outcome_probability, 1.0e-12)
        expected_entropy += outcome_probability * binary_entropy(posterior_positive)
    end
    return current_entropy - expected_entropy
end

function choose_channel(state, mean_phi, selected, config;
        precision_blind = false)
    available = setdiff(collect(1:3), selected)
    gains = [expected_information_gain(state, mean_phi, channel, config;
        precision_blind = precision_blind) for channel in available]
    return available[argmax(gains)]
end

function run_agent_episode(model, data, strategy::Symbol, mode::Symbol,
        seed, episode, config; replay_actions = Int[])
    unified = unified_config(config)
    prior_mean, prior_covariance = UnifiedBeautifulLoop.forecast(
        model, data.context, unified)
    state = relational_state_update(data.observations, Int[], prior_mean,
        prior_covariance, config; mode = mode)
    result = nothing
    selected = Int[]
    rng = MersenneTwister(seed + 30_000episode + Int(strategy == :random) * 991)
    for action_index in 1:config.action_budget
        channel = if strategy == :replay
            replay_actions[action_index]
        elseif strategy == :random
            rand(rng, setdiff(collect(1:3), selected))
        else
            choose_channel(state, result === nothing ? prior_mean : result.posterior_phi,
                selected, config; precision_blind = strategy == :precision_blind)
        end
        push!(selected, channel)
        result = infer_relational_episode(data.observations, selected,
            prior_mean, prior_covariance; mode = mode, config = config)
        state = result
    end
    UnifiedBeautifulLoop.update_forecaster!(model, data.context,
        result.posterior_phi, selected, unified)
    return (probability_positive = result.probability_positive,
        selected = selected, posterior_phi = result.posterior_phi,
        posterior_covariance = result.posterior_covariance,
        trace = result.trace, prior_mean = prior_mean)
end

function run_relational_agent_seed(seed::Int;
        config::RelationalAgentConfig = RelationalAgentConfig())
    unified = unified_config(config)
    models = Dict(
        "full" => UnifiedBeautifulLoop.PrecisionForecaster(true, unified),
        "factorized_replay" => UnifiedBeautifulLoop.PrecisionForecaster(true, unified),
        "random" => UnifiedBeautifulLoop.PrecisionForecaster(true, unified),
        "precision_blind" => UnifiedBeautifulLoop.PrecisionForecaster(true, unified),
    )
    rows = NamedTuple[]
    for episode in 1:config.episodes
        data = generate_relational_episode(seed, episode; config = config)
        full = run_agent_episode(models["full"], data, :active, :relational,
            seed, episode, config)
        results = Dict(
            "full" => full,
            "factorized_replay" => run_agent_episode(models["factorized_replay"],
                data, :replay, :factorized, seed, episode, config;
                replay_actions = full.selected),
            "random" => run_agent_episode(models["random"], data, :random,
                :relational, seed, episode, config),
            "precision_blind" => run_agent_episode(models["precision_blind"],
                data, :precision_blind, :relational, seed, episode, config),
        )
        for name in ("full", "factorized_replay", "random", "precision_blind")
            result = results[name]
            push!(rows, (
                seed = seed,
                episode = episode,
                agent = name,
                phase = episode <= config.training_episodes ? "training" :
                    (episode < config.switch_episode ? "heldout_before" : "heldout_after"),
                violation = data.violation,
                probability_positive = result.probability_positive,
                correct = (result.probability_positive >= 0.5 ? 1 : -1) ==
                    data.global_cause,
                first_action = first(result.selected),
                second_action = last(result.selected),
                sample_packets = length(result.selected),
                forecast_error = sqrt(mean((result.prior_mean .- data.true_phi).^2)),
                line_search_invariant = all(diff(getfield.(result.trace,
                    :joint_free_energy)) .<= 1.0e-8),
            ))
        end
    end
    return rows
end

function seed_metrics(rows)
    heldout(name) = filter(row -> row.agent == name && row.phase != "training", rows)
    before(name) = filter(row -> row.agent == name && row.phase == "heldout_before", rows)
    after(name) = filter(row -> row.agent == name && row.phase == "heldout_after", rows)
    coherent(name) = filter(row -> !row.violation, heldout(name))
    violations(name) = filter(row -> row.violation, heldout(name))
    accuracy(subset) = isempty(subset) ? NaN : mean(row.correct for row in subset)
    full_rows = sort(filter(row -> row.agent == "full", rows); by = row -> row.episode)
    replay_rows = sort(filter(row -> row.agent == "factorized_replay", rows);
        by = row -> row.episode)
    return (
        seed = first(rows).seed,
        full_accuracy = accuracy(heldout("full")),
        factorized_accuracy = accuracy(heldout("factorized_replay")),
        random_accuracy = accuracy(heldout("random")),
        blind_accuracy = accuracy(heldout("precision_blind")),
        full_coherent_accuracy = accuracy(coherent("full")),
        factorized_coherent_accuracy = accuracy(coherent("factorized_replay")),
        full_violation_accuracy = accuracy(violations("full")),
        factorized_violation_accuracy = accuracy(violations("factorized_replay")),
        full_before_channel_1 = mean(row.first_action == 1 for row in before("full")),
        full_after_channel_3 = mean(row.first_action == 3 for row in after("full")),
        blind_after_channel_3 = mean(row.first_action == 3 for row in after("precision_blind")),
        full_mean_packets = mean(row.sample_packets for row in heldout("full")),
        random_mean_packets = mean(row.sample_packets for row in heldout("random")),
        replay_action_match_rate = mean(full.first_action == replay.first_action &&
            full.second_action == replay.second_action
            for (full, replay) in zip(full_rows, replay_rows)),
        line_search_invariant_rate = mean(row.line_search_invariant for row in heldout("full")),
    )
end

function implementation_checks(config)
    episode = generate_relational_episode(first(config.seeds), 1; config = config)
    unified = unified_config(config)
    model = UnifiedBeautifulLoop.PrecisionForecaster(true, unified)
    prior_mean, prior_covariance = UnifiedBeautifulLoop.forecast(
        model, episode.context, unified)
    fit = infer_relational_episode(episode.observations, [1, 2], prior_mean,
        prior_covariance; config = config)
    perturbed = copy(episode.observations)
    perturbed[1, 1] += 0.50
    perturbed_fit = infer_relational_episode(perturbed, [1, 2], prior_mean,
        prior_covariance; config = config)
    marginal_error = maximum(abs(
        sum(exp(scene_log_prior(g, local_causes, :factorized, config) + log(2))
            for local_causes in LOCAL_CONFIGURATIONS if local_causes[channel] == 1) -
        local_positive_probability(g, channel, config))
        for g in (-1, 1), channel in 1:3)
    return (
        explicit_three_level_states = size(episode.states) ==
            (3, 3, config.packet_samples),
        factorized_prior_matches_local_marginals = marginal_error <= 1.0e-10,
        residual_messages_respond_to_observations =
            norm(fit.residuals - perturbed_fit.residuals) > 1.0e-6,
        partially_informative_local_causes = local_mutual_information(config) > 0.01,
    )
end

function finite_mean(metrics, key)
    values = [Float64(getfield(row, key)) for row in metrics
        if isfinite(Float64(getfield(row, key)))]
    return isempty(values) ? NaN : mean(values)
end

function summarize(metrics, config)
    keys_to_average = Tuple(filter(!=(:seed), keys(first(metrics))))
    means = NamedTuple{keys_to_average}(Tuple(finite_mean(metrics, key)
        for key in keys_to_average))
    wins = (
        relational_over_factorized = mean(row.full_accuracy > row.factorized_accuracy
            for row in metrics),
        active_over_random = mean(row.full_accuracy > row.random_accuracy
            for row in metrics),
    )
    empirical = (
        partially_informative_local_causes = local_mutual_information(config) > 0.01,
        relational_gain = means.full_accuracy >= means.factorized_accuracy + 0.03 &&
            wins.relational_over_factorized >= 0.70,
        active_sampling_gain = means.full_accuracy >= means.random_accuracy + 0.03 &&
            wins.active_over_random >= 0.70,
        precision_guided_reallocation = means.full_before_channel_1 >= 0.55 &&
            means.full_after_channel_3 >= 0.55 && means.blind_after_channel_3 <= 0.20,
        matched_sample_budget = means.full_mean_packets == means.random_mean_packets,
        adversarial_scope = means.full_violation_accuracy <=
            means.factorized_violation_accuracy,
    )
    implementation = merge(implementation_checks(config), (
        factorized_replay_uses_full_actions = means.replay_action_match_rate >= 0.999,
    ))
    optimization = (
        line_search_invariant_holds = means.line_search_invariant_rate >= 0.99,
    )
    return means, wins, empirical, implementation, optimization
end

function run_unified_relational_pilot(output_dir::AbstractString = joinpath(
        @__DIR__, "..", "results", "unified_relational_pilot");
        config::RelationalAgentConfig = RelationalAgentConfig())
    mkpath(output_dir)
    traces = NamedTuple[]
    metrics = NamedTuple[]
    for seed in config.seeds
        rows = run_relational_agent_seed(seed; config = config)
        append!(traces, rows)
        push!(metrics, seed_metrics(rows))
    end
    means, wins, empirical, implementation, optimization = summarize(metrics, config)
    summary = (
        experiment = 39,
        stage = "exploratory pilot",
        protocol = "soft relational binding plus precision-guided sequential sampling",
        local_mutual_information = local_mutual_information(config),
        config = (
            local_field = config.local_field,
            relational_field = config.relational_field,
            violation_rate = config.violation_rate,
            packet_samples = config.packet_samples,
            action_budget = config.action_budget,
        ),
        mean_metrics = means,
        win_rates = wins,
        empirical_criteria = empirical,
        implementation_checks = implementation,
        optimization_checks = optimization,
    )
    GlobalPrecisionField.write_csv(joinpath(output_dir, "trace.csv"), traces)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "per_seed.csv"), metrics)
    GlobalPrecisionField.write_json(joinpath(output_dir, "summary.json"), summary)
    GlobalPrecisionField.write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = all(values(implementation)) && all(values(optimization)),
        empirical_passed = all(values(empirical)),
        theory_result = all(values(empirical)) ?
            "one agent combines nonvacuous joint binding, recursive precision inference, and epistemic action" :
            "unified relational pilot criteria not yet satisfied",
    ))
    return summary
end

end
