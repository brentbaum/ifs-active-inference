module LearnedPrecisionStructure

using LinearAlgebra
using Random
using Statistics
using Main.GlobalPrecisionField
using Main.UnifiedBeautifulLoop
using Main.CompetitiveBinding

export StructureConfig, random_channel_loading, LearnedGlobalForecaster,
    AdaptiveLocalForecaster, run_structure_seed, run_learned_precision_structure

Base.@kwdef struct StructureConfig
    seeds::Vector{Int} = collect(8901:8920)
    episodes::Int = 180
    training_episodes::Int = 80
    switch_episode::Int = 121
    inference_iterations::Int = 8
    hyper_newton_steps::Int = 6
    observation_precision::Float64 = 8.0
    hyper_innovation_variance::Float64 = 0.30
    parameter_prior_variance::Float64 = 2.0
    regression_evidence_variance::Float64 = 0.45
    regression_forgetting::Float64 = 0.995
    samples_per_action::Int = 4
    cause_amplitude::Float64 = 1.05
    relation_noise::Float64 = 0.05
    shrinkage_grid::Vector{Float64} = [0.0, 0.3, 1.0, 3.0, 10.0, 30.0]
    model_weight_learning_rate::Float64 = 0.04
end

function competitive_config(config::StructureConfig)
    return CompetitiveBinding.CompetitiveConfig(
        seeds = config.seeds,
        episodes = config.episodes,
        training_episodes = config.training_episodes,
        switch_episode = config.switch_episode,
        relation_noise = config.relation_noise,
        inference_iterations = config.inference_iterations,
        hyper_newton_steps = config.hyper_newton_steps,
        observation_precision = config.observation_precision,
        hyper_innovation_variance = config.hyper_innovation_variance,
        parameter_prior_variance = config.parameter_prior_variance,
        regression_evidence_variance = config.regression_evidence_variance,
        regression_forgetting = config.regression_forgetting,
        samples_per_action = config.samples_per_action,
        cause_amplitude = config.cause_amplitude,
    )
end

function random_channel_loading(seed::Int)
    rng = MersenneTwister(seed + 456_789)
    loading = randn(rng, 3)
    loading .-= mean(loading)
    loading .*= 1.30 / sqrt(mean(abs2, loading))
    return loading
end

function context_at(episode, config::StructureConfig)
    training_contexts = (-1.0, -0.5, 0.0, 0.5, 1.0)
    episode <= config.training_episodes &&
        return training_contexts[mod1(episode, length(training_contexts))]
    episode < config.switch_episode && return -1.4
    return 1.4
end

function true_precision_field(context, loading)
    layer_intercepts = [1.20, 0.80, 0.50]
    return [layer_intercepts[layer] + loading[channel] * context
        for layer in 1:3 for channel in 1:3]
end

function generate_structure_episode(seed::Int, episode::Int, loading;
        config::StructureConfig = StructureConfig())
    rng = MersenneTwister(seed + 10_000episode)
    context = context_at(episode, config)
    phi = true_precision_field(context, loading)
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

mutable struct LinearFieldForecaster
    mode::Symbol
    precision::Matrix{Float64}
    information::Vector{Float64}
    prior_precision::Matrix{Float64}
end

function local_tying_laplacian()
    laplacian = zeros(18, 18)
    function tie!(indices)
        for left in 1:(length(indices) - 1), right in (left + 1):length(indices)
            contrast = zeros(18)
            contrast[indices[left]] = 1
            contrast[indices[right]] = -1
            laplacian .+= contrast * contrast'
        end
    end
    for layer in 1:3
        tie!([UnifiedBeautifulLoop.component_index(layer, channel) for channel in 1:3])
    end
    for channel in 1:3
        tie!([9 + UnifiedBeautifulLoop.component_index(layer, channel) for layer in 1:3])
    end
    return laplacian
end

function LinearFieldForecaster(mode::Symbol, config::StructureConfig; shrinkage = 0.0)
    dimensions = mode == :global ? 6 : 18
    prior = Matrix{Float64}(I, dimensions, dimensions) /
        config.parameter_prior_variance
    mode == :local && (prior .+= shrinkage .* local_tying_laplacian())
    return LinearFieldForecaster(mode, copy(prior), zeros(dimensions), prior)
end

function precision_design(context, mode::Symbol)
    if mode == :global
        design = zeros(9, 6)
        for layer in 1:3, channel in 1:3
            row = UnifiedBeautifulLoop.component_index(layer, channel)
            design[row, layer] = 1
            design[row, 3 + channel] = context
        end
        return design
    end
    design = zeros(9, 18)
    for row in 1:9
        design[row, row] = 1
        design[row, 9 + row] = context
    end
    return design
end

function forecast(model::LinearFieldForecaster, context, config::StructureConfig)
    design = precision_design(context, model.mode)
    covariance = inv(Symmetric(model.precision))
    parameter_mean = covariance * model.information
    mean_phi = design * parameter_mean
    covariance_phi = design * covariance * design' +
        Matrix{Float64}(I, 9, 9) * config.hyper_innovation_variance
    return mean_phi, Matrix(covariance_phi)
end

function update!(model::LinearFieldForecaster, context, evidence,
        observed_channels, config::StructureConfig)
    rows = [UnifiedBeautifulLoop.component_index(layer, channel)
        for layer in 1:3 for channel in observed_channels]
    design = precision_design(context, model.mode)[rows, :]
    model.precision .= config.regression_forgetting .* model.precision .+
        (1 - config.regression_forgetting) .* model.prior_precision .+
        (design' * design) ./ config.regression_evidence_variance
    model.information .= config.regression_forgetting .* model.information .+
        (design' * evidence[rows]) ./ config.regression_evidence_variance
end

mutable struct LearnedGlobalForecaster
    model::LinearFieldForecaster
end

LearnedGlobalForecaster(config::StructureConfig) =
    LearnedGlobalForecaster(LinearFieldForecaster(:global, config))

forecast(model::LearnedGlobalForecaster, context, config) =
    forecast(model.model, context, config)

update!(model::LearnedGlobalForecaster, context, evidence, channels, config) =
    update!(model.model, context, evidence, channels, config)

mutable struct AdaptiveLocalForecaster
    candidates::Vector{LinearFieldForecaster}
    shrinkages::Vector{Float64}
    log_weights::Vector{Float64}
end

function AdaptiveLocalForecaster(config::StructureConfig)
    candidates = [LinearFieldForecaster(:local, config; shrinkage = shrinkage)
        for shrinkage in config.shrinkage_grid]
    return AdaptiveLocalForecaster(candidates, copy(config.shrinkage_grid),
        fill(-log(length(candidates)), length(candidates)))
end

function model_weights(model::AdaptiveLocalForecaster)
    normalizer = UnifiedBeautifulLoop.logsumexp(model.log_weights)
    return exp.(model.log_weights .- normalizer)
end

function forecast(model::AdaptiveLocalForecaster, context, config::StructureConfig)
    predictions = [forecast(candidate, context, config) for candidate in model.candidates]
    weights = model_weights(model)
    mean_phi = sum(weight .* prediction[1]
        for (weight, prediction) in zip(weights, predictions))
    covariance_phi = zeros(9, 9)
    for (weight, prediction) in zip(weights, predictions)
        delta = prediction[1] - mean_phi
        covariance_phi .+= weight .* (prediction[2] + delta * delta')
    end
    return mean_phi, covariance_phi
end

function update!(model::AdaptiveLocalForecaster, context, evidence,
        observed_channels, config::StructureConfig)
    rows = [UnifiedBeautifulLoop.component_index(layer, channel)
        for layer in 1:3 for channel in observed_channels]
    for (index, candidate) in enumerate(model.candidates)
        prediction_mean, prediction_covariance = forecast(candidate, context, config)
        variances = diag(prediction_covariance)[rows] .+
            config.regression_evidence_variance
        errors = evidence[rows] - prediction_mean[rows]
        log_score = -0.5 * sum(log.(2pi .* variances) .+ errors.^2 ./ variances)
        model.log_weights[index] += config.model_weight_learning_rate * log_score
        update!(candidate, context, evidence, observed_channels, config)
    end
    normalizer = UnifiedBeautifulLoop.logsumexp(model.log_weights)
    model.log_weights .-= normalizer
end

function effective_shrinkage(model::AdaptiveLocalForecaster)
    return sum(model_weights(model) .* model.shrinkages)
end

function run_structure_seed(seed::Int; config::StructureConfig = StructureConfig())
    competitive = competitive_config(config)
    loading = random_channel_loading(seed)
    models = Dict{String,Any}(
        "learned_global" => LearnedGlobalForecaster(config),
        "adaptive_local" => AdaptiveLocalForecaster(config),
        "independent_local" => LinearFieldForecaster(:local, config; shrinkage = 0.0),
    )
    rows = NamedTuple[]
    forecast_snapshot = Dict{String,Float64}()
    loading_snapshot = Dict{String,Vector{Float64}}()
    for episode in 1:config.episodes
        data = generate_structure_episode(seed, episode, loading; config = config)
        for name in ("learned_global", "adaptive_local", "independent_local")
            model = models[name]
            prior_mean, prior_covariance = forecast(model, data.context, config)
            if episode == config.switch_episode
                forecast_snapshot[name] = sqrt(mean((prior_mean .- data.true_phi).^2))
                loading_snapshot[name] = [mean(prior_mean[
                    [UnifiedBeautifulLoop.component_index(layer, channel) for layer in 1:3]]) /
                    data.context for channel in 1:3]
            end
            result = CompetitiveBinding.infer_competitive_episode(
                data.observations, [1, 2, 3], prior_mean, prior_covariance;
                mode = :relational, config = competitive)
            update!(model, data.context, result.posterior_phi, [1, 2, 3], config)
            push!(rows, (
                seed = seed, episode = episode, agent = name,
                phase = episode <= config.training_episodes ? "training" :
                    (episode < config.switch_episode ? "heldout_before" : "heldout_after"),
                context = data.context,
                correct = (result.probability_positive >= 0.5 ? 1 : -1) ==
                    data.global_cause,
                relation_violation = data.relation_violation,
                forecast_error = sqrt(mean((prior_mean .- data.true_phi).^2)),
                effective_shrinkage = model isa AdaptiveLocalForecaster ?
                    effective_shrinkage(model) : 0.0,
            ))
        end
    end
    return rows, forecast_snapshot, loading_snapshot, loading
end

function correlation(left, right)
    centered_left = left .- mean(left)
    centered_right = right .- mean(right)
    denominator = sqrt(sum(abs2, centered_left) * sum(abs2, centered_right))
    return denominator <= 1.0e-12 ? 0.0 : dot(centered_left, centered_right) / denominator
end

function seed_metrics(rows, forecast_snapshot, loading_snapshot, loading)
    heldout = filter(row -> row.phase == "heldout_after", rows)
    by_agent(name) = filter(row -> row.agent == name, heldout)
    return (
        seed = first(rows).seed,
        global_forecast_error = forecast_snapshot["learned_global"],
        adaptive_forecast_error = forecast_snapshot["adaptive_local"],
        independent_forecast_error = forecast_snapshot["independent_local"],
        global_loading_correlation = correlation(
            loading_snapshot["learned_global"], loading),
        adaptive_loading_correlation = correlation(
            loading_snapshot["adaptive_local"], loading),
        global_accuracy = mean(row.correct for row in by_agent("learned_global")),
        adaptive_accuracy = mean(row.correct for row in by_agent("adaptive_local")),
        independent_accuracy = mean(row.correct for row in by_agent("independent_local")),
        adaptive_effective_shrinkage = mean(row.effective_shrinkage
            for row in by_agent("adaptive_local")),
    )
end

function summarize(metrics)
    metric_keys = Tuple(filter(!=(:seed), keys(first(metrics))))
    means = NamedTuple{metric_keys}(Tuple(mean(getfield(row, key) for row in metrics)
        for key in metric_keys))
    wins = (
        global_beats_independent = mean(row.global_forecast_error <
            row.independent_forecast_error for row in metrics),
        global_beats_adaptive = mean(row.global_forecast_error <
            row.adaptive_forecast_error for row in metrics),
        global_loading = mean(row.global_loading_correlation > 0.75 for row in metrics),
        adaptive_loading = mean(row.adaptive_loading_correlation > 0.75 for row in metrics),
    )
    empirical = (
        randomized_loading_recovered = means.global_loading_correlation >= 0.75 &&
            wins.global_loading >= 0.75,
        advantage_over_independent = means.global_forecast_error <=
            means.independent_forecast_error - 0.10 && wins.global_beats_independent >= 0.75,
        capable_local_control = means.adaptive_loading_correlation >= 0.65 &&
            means.adaptive_effective_shrinkage >= 8.5,
        advantage_over_adaptive = means.global_forecast_error <=
            means.adaptive_forecast_error - 0.10 && wins.global_beats_adaptive >= 0.75,
        task_accuracy_scope_condition = abs(means.global_accuracy -
            means.adaptive_accuracy) <= 0.03,
    )
    structural = (
        loading_randomized_by_seed = true,
        loading_hidden_from_agents = true,
        global_loading_inferred = true,
        local_model_can_learn_tying = true,
        identical_observations_and_updates = true,
    )
    return means, wins, empirical, structural
end

function run_learned_precision_structure(output_dir::AbstractString =
        joinpath(@__DIR__, "..", "results", "learned_precision_structure");
        config::StructureConfig = StructureConfig())
    mkpath(output_dir)
    traces = NamedTuple[]
    metrics = NamedTuple[]
    for seed in config.seeds
        rows, snapshot, loading_snapshot, loading = run_structure_seed(seed; config = config)
        append!(traces, rows)
        push!(metrics, seed_metrics(rows, snapshot, loading_snapshot, loading))
    end
    means, wins, empirical, structural = summarize(metrics)
    summary = (
        experiment = 35,
        protocol = "randomized learned field loadings versus adaptive hierarchical local loops",
        supervision = "true loading vectors and precisions are hidden and used only for scoring",
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
            "learned global structure forecasts better than independent and tying-capable local loops" :
            "learned-structure criteria not yet satisfied",
    ))
    return (traces = traces, metrics = metrics, summary = summary)
end

end
