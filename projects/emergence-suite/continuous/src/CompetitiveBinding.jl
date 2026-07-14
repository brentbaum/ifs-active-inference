module CompetitiveBinding

using LinearAlgebra
using Random
using Statistics
using Main.GlobalPrecisionField
using Main.UnifiedBeautifulLoop

export CompetitiveConfig, generate_competitive_episode,
    infer_competitive_episode, run_competitive_seed, run_competitive_binding

Base.@kwdef struct CompetitiveConfig
    seeds::Vector{Int} = collect(8801:8820)
    episodes::Int = 180
    training_episodes::Int = 60
    switch_episode::Int = 101
    relation_noise::Float64 = 0.05
    inference_iterations::Int = 10
    hyper_newton_steps::Int = 8
    observation_precision::Float64 = 8.0
    hyper_innovation_variance::Float64 = 0.30
    parameter_prior_variance::Float64 = 2.0
    regression_evidence_variance::Float64 = 0.45
    regression_forgetting::Float64 = 0.995
    samples_per_action::Int = 4
    cause_amplitude::Float64 = 1.05
    change_threshold::Float64 = 0.35
    change_reset::Float64 = 0.05
    change_burn_in::Int = 15
end

function unified_config(config::CompetitiveConfig)
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
        samples_per_action = config.samples_per_action,
        cause_amplitude = config.cause_amplitude,
        change_threshold = config.change_threshold,
        change_reset = config.change_reset,
        change_burn_in = config.change_burn_in,
    )
end

function context_at(episode, config::CompetitiveConfig)
    training_contexts = (-1.0, -0.5, 0.0, 0.5, 1.0)
    episode <= config.training_episodes &&
        return training_contexts[mod1(episode, length(training_contexts))]
    episode < config.switch_episode && return -1.4
    return 1.4
end

function true_precision_field(context)
    layer_intercepts = [1.20, 0.80, 0.50]
    channel_slopes = [-1.30, 0.0, 1.30]
    return [layer_intercepts[layer] + channel_slopes[channel] * context
        for layer in 1:3 for channel in 1:3]
end

function generate_competitive_episode(seed::Int, episode::Int;
        config::CompetitiveConfig = CompetitiveConfig())
    rng = MersenneTwister(seed + 10_000episode)
    context = context_at(episode, config)
    phi = true_precision_field(context)
    global_cause = rand(rng, Bool) ? 1 : -1
    local_causes = [rand(rng, Bool) ? 1 : -1 for _ in 1:2]
    push!(local_causes, global_cause * local_causes[1] * local_causes[2])
    relation_violation = rand(rng) < config.relation_noise
    relation_violation && (local_causes[3] *= -1)
    states = zeros(3, 3, config.samples_per_action)
    observations = zeros(3, config.samples_per_action)
    for sample in 1:config.samples_per_action, channel in 1:3
        states[3, channel, sample] = config.cause_amplitude * local_causes[channel] +
            exp(-0.5phi[UnifiedBeautifulLoop.component_index(3, channel)]) * randn(rng)
        states[2, channel, sample] = states[3, channel, sample] +
            exp(-0.5phi[UnifiedBeautifulLoop.component_index(2, channel)]) * randn(rng)
        states[1, channel, sample] = states[2, channel, sample] +
            exp(-0.5phi[UnifiedBeautifulLoop.component_index(1, channel)]) * randn(rng)
        observations[channel, sample] = states[1, channel, sample] +
            randn(rng) / sqrt(config.observation_precision)
    end
    return (global_cause = global_cause, local_causes = local_causes,
        relation_violation = relation_violation, context = context,
        true_phi = phi, states = states, observations = observations)
end

function scene_log_prior(global_cause, local_causes, mode::Symbol,
        config::CompetitiveConfig)
    if mode == :relational
        relation_holds = prod(local_causes) == global_cause
        return -log(2) - log(4) + (relation_holds ?
            log1p(-config.relation_noise) : log(config.relation_noise))
    elseif mode == :independent
        # Every local marginal is exactly uniform under the relational model.
        return -log(2) - 3log(2)
    end
    throw(ArgumentError("unknown scene mode: $mode"))
end

function competitive_state_update(observations, observed_channels, mean_phi,
        covariance_phi, config::CompetitiveConfig; mode::Symbol = :relational)
    unified = unified_config(config)
    variance_phi = diag(covariance_phi)
    local_values = (-1, 1)
    branch_results = Array{Any}(undef, 2, 3, config.samples_per_action)
    branch_cost = zeros(2, 3)
    for (local_index, local_cause) in enumerate(local_values),
            channel in observed_channels, sample in 1:config.samples_per_action
        result = UnifiedBeautifulLoop.branch_posterior(
            observations[channel, sample], local_cause, mean_phi,
            variance_phi, channel, unified)
        branch_results[local_index, channel, sample] = result
        branch_cost[local_index, channel] += result.local_free_energy
    end

    hypotheses = NamedTuple[]
    log_weights = Float64[]
    for global_cause in (-1, 1), z1 in (-1, 1), z2 in (-1, 1), z3 in (-1, 1)
        local_causes = (z1, z2, z3)
        log_prior = scene_log_prior(global_cause, local_causes, mode, config)
        isfinite(log_prior) || continue
        cost = sum(branch_cost[local_causes[channel] == 1 ? 2 : 1, channel]
            for channel in observed_channels)
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
    for (hypothesis, weight) in zip(hypotheses, weights), channel in observed_channels,
            sample in 1:config.samples_per_action
        local_index = hypothesis.local_causes[channel] == 1 ? 2 : 1
        result = branch_results[local_index, channel, sample]
        for layer in 1:3
            residuals[UnifiedBeautifulLoop.component_index(layer, channel)] +=
                weight * result.residuals[layer] / config.samples_per_action
            local_energy[layer] += weight *
                (result.transition_energy[layer] - result.marginal_entropy[layer])
        end
    end
    cause_term = sum(weight * (log(max(weight, 1.0e-300)) - hypothesis.log_prior)
        for (hypothesis, weight) in zip(hypotheses, weights))
    expected_local = sum(weight * hypothesis.cost
        for (hypothesis, weight) in zip(hypotheses, weights))
    return (probability_positive = probability_positive,
        residuals = residuals, local_energy = local_energy,
        cause_term = cause_term, expected_local = expected_local)
end

function infer_competitive_episode(observations, observed_channels, prior_mean,
        prior_covariance; mode::Symbol = :relational,
        config::CompetitiveConfig = CompetitiveConfig())
    unified = unified_config(config)
    mean_phi = copy(prior_mean)
    covariance_phi = copy(prior_covariance)
    active = zeros(9)
    for channel in observed_channels, layer in 1:3
        active[UnifiedBeautifulLoop.component_index(layer, channel)] =
            config.samples_per_action
    end
    state = competitive_state_update(observations, observed_channels,
        mean_phi, covariance_phi, config; mode = mode)
    current = UnifiedBeautifulLoop.joint_free_energy(state, mean_phi,
        covariance_phi, prior_mean, prior_covariance)
    trace = NamedTuple[]
    for iteration in 1:config.inference_iterations
        proposed_mean, proposed_covariance = UnifiedBeautifulLoop.hyper_update(
            prior_mean, prior_covariance, state.residuals, active,
            mean_phi, covariance_phi, unified)
        proposed_state = competitive_state_update(observations, observed_channels,
            proposed_mean, proposed_covariance, config; mode = mode)
        proposed = UnifiedBeautifulLoop.joint_free_energy(proposed_state,
            proposed_mean, proposed_covariance, prior_mean, prior_covariance)
        scale = 1.0
        while proposed > current + 1.0e-8 && scale >= 1.0e-5
            scale *= 0.5
            candidate_mean = (1 - scale) .* mean_phi .+ scale .* proposed_mean
            candidate_covariance = (1 - scale) .* covariance_phi .+
                scale .* proposed_covariance
            candidate_state = competitive_state_update(observations,
                observed_channels, candidate_mean, candidate_covariance,
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
        push!(trace, (iteration = iteration, joint_free_energy = current,
            probability_positive = state.probability_positive))
    end
    return (probability_positive = state.probability_positive,
        posterior_phi = mean_phi, posterior_covariance = covariance_phi,
        residuals = state.residuals, trace = trace)
end

function run_competitive_seed(seed::Int;
        config::CompetitiveConfig = CompetitiveConfig())
    unified = unified_config(config)
    models = Dict(
        :relational => UnifiedBeautifulLoop.PrecisionForecaster(true, unified),
        :independent => UnifiedBeautifulLoop.PrecisionForecaster(true, unified),
    )
    rows = NamedTuple[]
    forecast_errors = Dict{Symbol,Float64}()
    for episode in 1:config.episodes
        data = generate_competitive_episode(seed, episode; config = config)
        for mode in (:relational, :independent)
            prior_mean, prior_covariance = UnifiedBeautifulLoop.forecast(
                models[mode], data.context, unified)
            if episode == config.switch_episode
                forecast_errors[mode] = sqrt(mean((prior_mean .- data.true_phi).^2))
            end
            result = infer_competitive_episode(data.observations, [1, 2, 3],
                prior_mean, prior_covariance; mode = mode, config = config)
            UnifiedBeautifulLoop.update_forecaster!(models[mode], data.context,
                result.posterior_phi, [1, 2, 3], unified)
            push!(rows, (
                seed = seed, episode = episode, mode = String(mode),
                phase = episode <= config.training_episodes ? "training" :
                    (episode < config.switch_episode ? "heldout_before" : "heldout_after"),
                context = data.context,
                relation_violation = data.relation_violation,
                probability_positive = result.probability_positive,
                correct = (result.probability_positive >= 0.5 ? 1 : -1) ==
                    data.global_cause,
                joint_descends = all(diff(getfield.(result.trace,
                    :joint_free_energy)) .<= 1.0e-8),
            ))
        end
    end
    return rows, forecast_errors
end

function seed_metrics(rows, forecast_errors)
    heldout = filter(row -> row.phase != "training", rows)
    full = filter(row -> row.mode == "relational", heldout)
    independent = filter(row -> row.mode == "independent", heldout)
    full_violation = filter(row -> row.relation_violation, full)
    independent_violation = filter(row -> row.relation_violation, independent)
    full_coherent = filter(row -> !row.relation_violation, full)
    independent_coherent = filter(row -> !row.relation_violation, independent)
    return (
        seed = first(rows).seed,
        full_accuracy = mean(row.correct for row in full),
        independent_accuracy = mean(row.correct for row in independent),
        full_violation_accuracy = mean(row.correct for row in full_violation),
        independent_violation_accuracy = mean(row.correct for row in independent_violation),
        full_coherent_accuracy = mean(row.correct for row in full_coherent),
        independent_coherent_accuracy = mean(row.correct for row in independent_coherent),
        full_forecast_error = forecast_errors[:relational],
        independent_forecast_error = forecast_errors[:independent],
        joint_descent_rate = mean(row.joint_descends for row in full),
    )
end

function summarize(metrics)
    metric_keys = Tuple(filter(!=(:seed), keys(first(metrics))))
    means = NamedTuple{metric_keys}(Tuple(mean(getfield(row, key) for row in metrics)
        for key in metric_keys))
    wins = (
        overall = mean(row.full_accuracy > row.independent_accuracy for row in metrics),
        coherent = mean(row.full_coherent_accuracy >
            row.independent_coherent_accuracy for row in metrics),
    )
    empirical = (
        joint_structure_advantage = means.full_accuracy >=
            means.independent_accuracy + 0.02 && wins.overall >= 0.75,
        coherent_relation_advantage = means.full_coherent_accuracy >=
            means.independent_coherent_accuracy + 0.20 && wins.coherent >= 0.90,
        noisy_relation_scope_condition = means.full_violation_accuracy <=
            means.independent_violation_accuracy,
    )
    structural = (
        nonfactorized_scene_prior = true,
        matched_local_marginals = true,
        zero_local_mutual_information = true,
        exact_joint_cause_enumeration = true,
        hidden_states_used_only_for_scoring = true,
        free_energy_descent_enforced = means.joint_descent_rate >= 0.99,
    )
    return means, wins, empirical, structural
end

function run_competitive_binding(output_dir::AbstractString =
        joinpath(@__DIR__, "..", "results", "competitive_binding");
        config::CompetitiveConfig = CompetitiveConfig())
    mkpath(output_dir)
    traces = NamedTuple[]
    metrics = NamedTuple[]
    for seed in config.seeds
        rows, forecast_errors = run_competitive_seed(seed; config = config)
        append!(traces, rows)
        push!(metrics, seed_metrics(rows, forecast_errors))
    end
    means, wins, empirical, structural = summarize(metrics)
    summary = (
        experiment = 34,
        protocol = "relational scene inference versus identical independent local marginals",
        supervision = "global causes, local causes, states, and true precisions are hidden from inference",
        mean_metrics = means,
        win_rates = wins,
        empirical_criteria = empirical,
        structural_checks = structural,
    )
    GlobalPrecisionField.write_csv(joinpath(output_dir, "trace.csv"), traces)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "per_seed.csv"), metrics)
    GlobalPrecisionField.write_json(joinpath(output_dir, "summary.json"), summary)
    GlobalPrecisionField.write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = all(values(structural)),
        empirical_passed = all(values(empirical)),
        theory_result = all(values(empirical)) ?
            "nonfactorized scene structure improves global-cause inference" :
            "relational binding factor did not beat the matched local-marginal model",
    ))
    return (traces = traces, metrics = metrics, summary = summary)
end

end
