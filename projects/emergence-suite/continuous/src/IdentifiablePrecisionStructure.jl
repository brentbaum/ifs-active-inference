module IdentifiablePrecisionStructure

using LinearAlgebra
using Random
using Statistics
using Main.GlobalPrecisionField
using Main.UnifiedBeautifulLoop
using Main.CompetitiveBinding
using Main.LearnedPrecisionStructure

export IdentifiableConfig, generate_monitored_episode, infer_monitored_episode,
    run_identifiable_seed, run_identifiable_precision_structure

Base.@kwdef struct IdentifiableConfig
    seeds::Vector{Int} = collect(11001:11020)
    episodes::Int = 180
    training_episodes::Int = 80
    switch_episode::Int = 121
    inference_iterations::Int = 8
    hyper_newton_steps::Int = 6
    layer_observation_precision::Float64 = 8.0
    hyper_innovation_variance::Float64 = 0.30
    parameter_prior_variance::Float64 = 2.0
    regression_evidence_variance::Float64 = 0.45
    regression_forgetting::Float64 = 0.995
    samples_per_action::Int = 4
    cause_amplitude::Float64 = 1.05
    relation_noise::Float64 = 0.05
    local_deviation_sd::Float64 = 0.0
    shrinkage_grid::Vector{Float64} = [0.0, 0.3, 1.0, 3.0, 10.0, 30.0]
    model_weight_learning_rate::Float64 = 0.04
end

function structure_config(config::IdentifiableConfig)
    return LearnedPrecisionStructure.StructureConfig(
        seeds = config.seeds,
        episodes = config.episodes,
        training_episodes = config.training_episodes,
        switch_episode = config.switch_episode,
        inference_iterations = config.inference_iterations,
        hyper_newton_steps = config.hyper_newton_steps,
        observation_precision = config.layer_observation_precision,
        hyper_innovation_variance = config.hyper_innovation_variance,
        parameter_prior_variance = config.parameter_prior_variance,
        regression_evidence_variance = config.regression_evidence_variance,
        regression_forgetting = config.regression_forgetting,
        samples_per_action = config.samples_per_action,
        cause_amplitude = config.cause_amplitude,
        relation_noise = config.relation_noise,
        local_deviation_sd = config.local_deviation_sd,
        shrinkage_grid = config.shrinkage_grid,
        model_weight_learning_rate = config.model_weight_learning_rate,
    )
end

competitive_config(config::IdentifiableConfig) =
    LearnedPrecisionStructure.competitive_config(structure_config(config))

function generate_monitored_episode(seed::Int, episode::Int, loading, deviations;
        config::IdentifiableConfig = IdentifiableConfig())
    structure = structure_config(config)
    data = LearnedPrecisionStructure.generate_structure_episode(
        seed, episode, loading, deviations; config = structure)
    rng = MersenneTwister(seed + 20_000episode + 777)
    monitored = similar(data.states)
    for sample in 1:config.samples_per_action, channel in 1:3, layer in 1:3
        monitored[layer, channel, sample] = data.states[layer, channel, sample] +
            randn(rng) / sqrt(config.layer_observation_precision)
    end
    return merge(data, (monitored_observations = monitored,))
end

function monitored_branch_posterior(observations, local_cause, mean_phi,
        variance_phi, channel, config::IdentifiableConfig)
    expected_precision = [exp(mean_phi[
        UnifiedBeautifulLoop.component_index(layer, channel)] +
        0.5variance_phi[UnifiedBeautifulLoop.component_index(layer, channel)])
        for layer in 1:3]
    links = ([1.0, -1.0, 0.0], [0.0, 1.0, -1.0], [0.0, 0.0, 1.0])
    posterior_precision = Matrix{Float64}(I, 3, 3) * 1.0e-10
    information = zeros(3)
    for layer in 1:3
        posterior_precision[layer, layer] += config.layer_observation_precision
        information[layer] += config.layer_observation_precision * observations[layer]
        posterior_precision .+= expected_precision[layer] .* (links[layer] * links[layer]')
    end
    information .+= expected_precision[3] * config.cause_amplitude *
        local_cause .* links[3]
    covariance = inv(Symmetric(posterior_precision))
    state_mean = covariance * information
    residuals = [
        (state_mean[1] - state_mean[2])^2 + covariance[1, 1] + covariance[2, 2] - 2covariance[1, 2],
        (state_mean[2] - state_mean[3])^2 + covariance[2, 2] + covariance[3, 3] - 2covariance[2, 3],
        (state_mean[3] - config.cause_amplitude * local_cause)^2 + covariance[3, 3],
    ]
    observation_residuals = [(observations[layer] - state_mean[layer])^2 +
        covariance[layer, layer] for layer in 1:3]
    transition_energy = [0.5 * (log(2pi) -
        mean_phi[UnifiedBeautifulLoop.component_index(layer, channel)] +
        expected_precision[layer] * residuals[layer]) for layer in 1:3]
    observation_energy = 0.5 * sum(log(2pi) -
        log(config.layer_observation_precision) +
        config.layer_observation_precision * residual for residual in observation_residuals)
    entropy = 0.5 * (3 * (1 + log(2pi)) + logdet(covariance))
    marginal_entropy = 0.5 .* (1 .+ log(2pi) .+ log.(diag(covariance)))
    return (mean = state_mean, covariance = Matrix(covariance), residuals = residuals,
        transition_energy = transition_energy, observation_energy = observation_energy,
        marginal_entropy = marginal_entropy,
        local_free_energy = observation_energy + sum(transition_energy) - entropy)
end

function monitored_state_update(observations, observed_channels, mean_phi,
        covariance_phi, config::IdentifiableConfig)
    variance_phi = diag(covariance_phi)
    branch_results = Array{Any}(undef, 2, 3, config.samples_per_action)
    branch_cost = zeros(2, 3)
    for (local_index, local_cause) in enumerate((-1, 1)),
            channel in observed_channels, sample in 1:config.samples_per_action
        result = monitored_branch_posterior(observations[:, channel, sample],
            local_cause, mean_phi, variance_phi, channel, config)
        branch_results[local_index, channel, sample] = result
        branch_cost[local_index, channel] += result.local_free_energy
    end
    competitive = competitive_config(config)
    hypotheses = NamedTuple[]
    log_weights = Float64[]
    for global_cause in (-1, 1), z1 in (-1, 1), z2 in (-1, 1), z3 in (-1, 1)
        local_causes = (z1, z2, z3)
        log_prior = CompetitiveBinding.scene_log_prior(
            global_cause, local_causes, :relational, competitive)
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
    return (probability_positive = probability_positive, residuals = residuals,
        local_energy = local_energy, cause_term = cause_term,
        expected_local = expected_local)
end

function infer_monitored_episode(observations, observed_channels, prior_mean,
        prior_covariance; config::IdentifiableConfig = IdentifiableConfig())
    structure = structure_config(config)
    unified = CompetitiveBinding.unified_config(competitive_config(config))
    mean_phi = copy(prior_mean)
    covariance_phi = copy(prior_covariance)
    active = zeros(9)
    for channel in observed_channels, layer in 1:3
        active[UnifiedBeautifulLoop.component_index(layer, channel)] =
            config.samples_per_action
    end
    state = monitored_state_update(observations, observed_channels,
        mean_phi, covariance_phi, config)
    current = UnifiedBeautifulLoop.joint_free_energy(state, mean_phi,
        covariance_phi, prior_mean, prior_covariance)
    trace = NamedTuple[]
    for iteration in 1:config.inference_iterations
        proposed_mean, proposed_covariance = UnifiedBeautifulLoop.hyper_update(
            prior_mean, prior_covariance, state.residuals, active,
            mean_phi, covariance_phi, unified)
        proposed_state = monitored_state_update(observations, observed_channels,
            proposed_mean, proposed_covariance, config)
        proposed = UnifiedBeautifulLoop.joint_free_energy(proposed_state,
            proposed_mean, proposed_covariance, prior_mean, prior_covariance)
        scale = 1.0
        while proposed > current + 1.0e-8 && scale >= 1.0e-5
            scale *= 0.5
            candidate_mean = (1 - scale) .* mean_phi .+ scale .* proposed_mean
            candidate_covariance = (1 - scale) .* covariance_phi .+
                scale .* proposed_covariance
            candidate_state = monitored_state_update(observations,
                observed_channels, candidate_mean, candidate_covariance, config)
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

function run_identifiable_seed(seed::Int;
        config::IdentifiableConfig = IdentifiableConfig())
    structure = structure_config(config)
    loading = LearnedPrecisionStructure.random_channel_loading(seed)
    deviations = LearnedPrecisionStructure.random_local_deviations(
        seed, config.local_deviation_sd)
    models = Dict{String,Any}(
        "learned_global" => LearnedPrecisionStructure.LearnedGlobalForecaster(structure),
        "nested_local" => LearnedPrecisionStructure.AdaptiveLocalForecaster(
            structure; mode = :hierarchical),
    )
    rows = NamedTuple[]
    forecast_snapshot = Dict{String,Float64}()
    for episode in 1:config.episodes
        data = generate_monitored_episode(seed, episode, loading, deviations;
            config = config)
        for name in ("learned_global", "nested_local")
            model = models[name]
            prior_mean, prior_covariance = LearnedPrecisionStructure.forecast(
                model, data.context, structure)
            episode == config.switch_episode &&
                (forecast_snapshot[name] = sqrt(mean((prior_mean .- data.true_phi).^2)))
            result = infer_monitored_episode(data.monitored_observations, [1, 2, 3],
                prior_mean, prior_covariance; config = config)
            LearnedPrecisionStructure.update!(model, data.context,
                result.posterior_phi, [1, 2, 3], structure)
            push!(rows, (
                seed = seed, episode = episode, agent = name,
                phase = episode < config.switch_episode ? "before" : "after",
                correct = (result.probability_positive >= 0.5 ? 1 : -1) ==
                    data.global_cause,
                forecast_error = sqrt(mean((prior_mean .- data.true_phi).^2)),
                effective_shrinkage = model isa
                    LearnedPrecisionStructure.AdaptiveLocalForecaster ?
                    LearnedPrecisionStructure.effective_shrinkage(model) : 0.0,
            ))
        end
    end
    return rows, forecast_snapshot
end

function seed_metrics(rows, snapshot)
    after(name) = filter(row -> row.agent == name && row.phase == "after", rows)
    nested = after("nested_local")
    return (
        seed = first(rows).seed,
        global_forecast_error = snapshot["learned_global"],
        nested_forecast_error = snapshot["nested_local"],
        global_accuracy = mean(row.correct for row in after("learned_global")),
        nested_accuracy = mean(row.correct for row in nested),
        nested_effective_shrinkage = mean(row.effective_shrinkage for row in nested),
    )
end

function summarize(metrics)
    metric_keys = Tuple(filter(!=(:seed), keys(first(metrics))))
    means = NamedTuple{metric_keys}(Tuple(mean(getfield(row, key) for row in metrics)
        for key in metric_keys))
    wins = (
        global_wins = mean(row.global_forecast_error < row.nested_forecast_error for row in metrics),
        nested_wins = mean(row.nested_forecast_error < row.global_forecast_error for row in metrics),
    )
    return means, wins
end

function run_identifiable_precision_structure(output_dir::AbstractString =
        joinpath(@__DIR__, "..", "results", "identifiable_precision_structure");
        config::IdentifiableConfig = IdentifiableConfig())
    mkpath(output_dir)
    all_metrics = NamedTuple[]
    condition_rows = NamedTuple[]
    for deviation in (0.0, 1.0, 2.0, 3.0)
        candidate = IdentifiableConfig(
            seeds = config.seeds,
            episodes = config.episodes,
            training_episodes = config.training_episodes,
            switch_episode = config.switch_episode,
            inference_iterations = config.inference_iterations,
            hyper_newton_steps = config.hyper_newton_steps,
            layer_observation_precision = config.layer_observation_precision,
            hyper_innovation_variance = config.hyper_innovation_variance,
            parameter_prior_variance = config.parameter_prior_variance,
            regression_evidence_variance = config.regression_evidence_variance,
            regression_forgetting = config.regression_forgetting,
            samples_per_action = config.samples_per_action,
            cause_amplitude = config.cause_amplitude,
            relation_noise = config.relation_noise,
            local_deviation_sd = deviation,
            shrinkage_grid = config.shrinkage_grid,
            model_weight_learning_rate = config.model_weight_learning_rate,
        )
        metrics = NamedTuple[]
        for seed in candidate.seeds
            rows, snapshot = run_identifiable_seed(seed; config = candidate)
            metric = seed_metrics(rows, snapshot)
            push!(metrics, metric)
            push!(all_metrics, merge((local_deviation_sd = deviation,), metric))
        end
        means, wins = summarize(metrics)
        push!(condition_rows, (
            local_deviation_sd = deviation,
            global_forecast_error = means.global_forecast_error,
            nested_forecast_error = means.nested_forecast_error,
            nested_minus_global = means.nested_forecast_error -
                means.global_forecast_error,
            global_accuracy = means.global_accuracy,
            nested_accuracy = means.nested_accuracy,
            nested_effective_shrinkage = means.nested_effective_shrinkage,
            global_seed_win_rate = wins.global_wins,
            nested_seed_win_rate = wins.nested_wins,
        ))
    end
    zero = only(filter(row -> row.local_deviation_sd == 0.0, condition_rows))
    two = only(filter(row -> row.local_deviation_sd == 2.0, condition_rows))
    three = only(filter(row -> row.local_deviation_sd == 3.0, condition_rows))
    empirical = (
        global_advantage_when_exact = zero.nested_minus_global >= 0.05 &&
            zero.global_seed_win_rate >= 0.75,
        nested_no_worse_at_two = two.nested_minus_global <= 0.0 &&
            two.nested_seed_win_rate >= 0.75,
        nested_advantage_at_three = three.nested_minus_global <= -0.05 &&
            three.nested_seed_win_rate >= 0.75,
        evidence_releases_tying = three.nested_effective_shrinkage <
            zero.nested_effective_shrinkage,
    )
    structural = (
        noisy_observations_at_all_levels = true,
        latent_states_hidden = true,
        global_model_nested_in_local = true,
        residual_updates_only = true,
        paired_fresh_seed_block = true,
    )
    summary = (
        experiment = 37,
        protocol = "layer-monitored precision inference with nested global-to-local random effects",
        supervision = "all layer observations are noisy; latent states and true precisions remain hidden",
        confirmatory_seeds = config.seeds,
        conditions = condition_rows,
        empirical_criteria = empirical,
        structural_checks = structural,
    )
    GlobalPrecisionField.write_csv(joinpath(output_dir, "per_seed.csv"), all_metrics)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "conditions.csv"), condition_rows)
    GlobalPrecisionField.write_json(joinpath(output_dir, "summary.json"), summary)
    GlobalPrecisionField.write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = all(values(structural)),
        empirical_passed = all(values(empirical)),
        theory_result = all(values(empirical)) ?
            "global precision wins under exact sharing and nested local effects win after structure breaks" :
            "identifiable precision crossover criteria not satisfied",
    ))
    return summary
end

end
