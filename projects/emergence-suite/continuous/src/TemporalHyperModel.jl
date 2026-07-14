module TemporalHyperModel

using LinearAlgebra
using Random
using Statistics
using Main.GlobalPrecisionField
using Main.BeautifulLoopHierarchy

export TemporalConfig, run_temporal_seed, run_temporal_hypermodel

Base.@kwdef struct TemporalConfig
    seeds::Vector{Int} = collect(8401:8420)
    steps::Int = 90
    first_switch::Int = 31
    second_switch::Int = 61
    evidence_samples::Int = 28
    observation_precision::Float64 = 5.0
    evidence_variance::Float64 = 0.16
    prior_variance::Float64 = 2.5
    forgetting::Float64 = 0.93
    model_evidence_memory::Float64 = 0.82
    model_evidence_gain::Float64 = 0.55
    global_model_log_prior::Float64 = 0.55
end

mutable struct OnlineGaussianRegression
    precision::Matrix{Float64}
    information::Vector{Float64}
    prior_precision::Matrix{Float64}
end

function OnlineGaussianRegression(dimensions::Int, prior_variance::Float64)
    prior_precision = Matrix{Float64}(I, dimensions, dimensions) / prior_variance
    return OnlineGaussianRegression(copy(prior_precision), zeros(dimensions), prior_precision)
end

function design(context::Float64, global_model::Bool)
    if global_model
        return [1.0 0.0 0.0 context;
                0.0 1.0 0.0 context;
                0.0 0.0 1.0 context]
    end
    return [1.0 0.0 0.0 context 0.0 0.0;
            0.0 1.0 0.0 0.0 context 0.0;
            0.0 0.0 1.0 0.0 0.0 context]
end

function forecast(model::OnlineGaussianRegression, context, global_model, evidence_variance)
    x = design(context, global_model)
    covariance = inv(Symmetric(model.precision))
    mean_parameters = covariance * model.information
    mean_phi = x * mean_parameters
    predictive_covariance = x * covariance * x' +
        Matrix{Float64}(I, 3, 3) * evidence_variance
    return mean_phi, Matrix(predictive_covariance)
end

function update!(model::OnlineGaussianRegression, context, evidence, global_model,
        config::TemporalConfig)
    x = design(context, global_model)
    model.precision .= config.forgetting .* model.precision .+
        (1 - config.forgetting) .* model.prior_precision .+
        (x' * x) ./ config.evidence_variance
    model.information .= config.forgetting .* model.information .+
        (x' * evidence) ./ config.evidence_variance
end

function logpdf_gaussian(observation, mean, covariance)
    delta = observation - mean
    return -0.5 * (length(observation) * log(2pi) + logdet(covariance) +
        dot(delta, covariance \ delta))
end

logistic(x) = inv(1 + exp(-x))

function context_at(step)
    return sin(2pi * step / 13) + 0.35cos(2pi * step / 7)
end

function true_precision(step, context, config::TemporalConfig)
    offsets = [0.20, -0.05, 0.10]
    if config.first_switch <= step < config.second_switch
        return offsets .+ [1.05, -0.90, 0.30] .* context
    end
    return offsets .+ 0.72 .* context
end

function precision_evidence(seed, step, true_phi, context_state, forecast_phi,
        config::TemporalConfig)
    hierarchy_config = BeautifulLoopHierarchy.LoopConfig(
        seeds = [seed], samples = config.evidence_samples,
        observation_precision = config.observation_precision)
    episode = BeautifulLoopHierarchy.generate_hierarchy(seed + 100step, true_phi;
        context_state = context_state, samples = config.evidence_samples,
        config = hierarchy_config)
    stats = BeautifulLoopHierarchy.state_statistics(
        episode, exp.(forecast_phi), hierarchy_config)
    return -log.(max.(stats.residuals, 1.0e-8))
end

function run_temporal_seed(seed::Int; config::TemporalConfig = TemporalConfig())
    global_model = OnlineGaussianRegression(4, config.prior_variance)
    local_model = OnlineGaussianRegression(6, config.prior_variance)
    log_global_odds = config.global_model_log_prior
    rows = NamedTuple[]
    for step in 1:config.steps
        context = context_at(step)
        truth = true_precision(step, context, config)
        global_phi, global_covariance = forecast(
            global_model, context, true, config.evidence_variance)
        local_phi, local_covariance = forecast(
            local_model, context, false, config.evidence_variance)
        global_weight = logistic(log_global_odds)
        adaptive_phi = global_weight .* global_phi .+ (1 - global_weight) .* local_phi
        evidence = precision_evidence(
            seed, step, truth, context, adaptive_phi, config)
        global_log_evidence = logpdf_gaussian(evidence, global_phi, global_covariance)
        local_log_evidence = logpdf_gaussian(evidence, local_phi, local_covariance)
        log_global_odds = clamp(
            config.model_evidence_memory * log_global_odds +
            (1 - config.model_evidence_memory) * config.global_model_log_prior +
            config.model_evidence_gain * (global_log_evidence - local_log_evidence),
            -7.0, 7.0)
        update!(global_model, context, evidence, true, config)
        update!(local_model, context, evidence, false, config)
        regime = step < config.first_switch ? "coordinated_1" :
            (step < config.second_switch ? "independent" : "coordinated_2")
        push!(rows, (
            seed = seed, step = step, regime = regime, context = context,
            true_phi_1 = truth[1], true_phi_2 = truth[2], true_phi_3 = truth[3],
            evidence_1 = evidence[1], evidence_2 = evidence[2], evidence_3 = evidence[3],
            global_weight = logistic(log_global_odds),
            adaptive_rmse = sqrt(mean((adaptive_phi .- truth).^2)),
            forced_global_rmse = sqrt(mean((global_phi .- truth).^2)),
            local_rmse = sqrt(mean((local_phi .- truth).^2)),
            global_log_evidence = global_log_evidence,
            local_log_evidence = local_log_evidence,
        ))
    end
    return rows
end

function window(rows, regime, last_n)
    matching = filter(row -> row.regime == regime, rows)
    return matching[(end - last_n + 1):end]
end

function per_seed_metrics(rows)
    first_shared = window(rows, "coordinated_1", 10)
    independent = window(rows, "independent", 10)
    recovered = window(rows, "coordinated_2", 10)
    return (
        seed = first(rows).seed,
        initial_global_weight = mean(row.global_weight for row in first_shared),
        broken_global_weight = mean(row.global_weight for row in independent),
        recovered_global_weight = mean(row.global_weight for row in recovered),
        shared_adaptive_rmse = mean(row.adaptive_rmse for row in first_shared),
        shared_local_rmse = mean(row.local_rmse for row in first_shared),
        broken_adaptive_rmse = mean(row.adaptive_rmse for row in independent),
        broken_forced_global_rmse = mean(row.forced_global_rmse for row in independent),
        recovery_adaptive_rmse = mean(row.adaptive_rmse for row in recovered),
        recovery_local_rmse = mean(row.local_rmse for row in recovered),
    )
end

function run_temporal_hypermodel(output_dir::AbstractString =
        joinpath(@__DIR__, "..", "results", "temporal_hypermodel");
        config::TemporalConfig = TemporalConfig())
    mkpath(output_dir)
    traces = NamedTuple[]
    metrics = NamedTuple[]
    for seed in config.seeds
        rows = run_temporal_seed(seed; config = config)
        append!(traces, rows)
        push!(metrics, per_seed_metrics(rows))
    end
    mean_metrics = (
        initial_global_weight = mean(row.initial_global_weight for row in metrics),
        broken_global_weight = mean(row.broken_global_weight for row in metrics),
        recovered_global_weight = mean(row.recovered_global_weight for row in metrics),
        shared_adaptive_rmse = mean(row.shared_adaptive_rmse for row in metrics),
        shared_local_rmse = mean(row.shared_local_rmse for row in metrics),
        broken_adaptive_rmse = mean(row.broken_adaptive_rmse for row in metrics),
        broken_forced_global_rmse = mean(row.broken_forced_global_rmse for row in metrics),
        recovery_adaptive_rmse = mean(row.recovery_adaptive_rmse for row in metrics),
        recovery_local_rmse = mean(row.recovery_local_rmse for row in metrics),
    )
    win_rates = (
        global_detected = mean(row.initial_global_weight > 0.60 for row in metrics),
        coupling_released = mean(row.broken_global_weight < 0.40 for row in metrics),
        coupling_recovered = mean(row.recovered_global_weight > 0.60 for row in metrics),
        broken_beats_forced_global = mean(
            row.broken_adaptive_rmse < row.broken_forced_global_rmse for row in metrics),
    )
    criteria = (
        learns_global_coupling = mean_metrics.initial_global_weight > 0.60 &&
            win_rates.global_detected >= 0.75,
        releases_broken_coupling = mean_metrics.broken_global_weight < 0.40 &&
            win_rates.coupling_released >= 0.75,
        recovers_global_coupling = mean_metrics.recovered_global_weight > 0.60 &&
            win_rates.coupling_recovered >= 0.75,
        broken_regime_advantage = mean_metrics.broken_adaptive_rmse <
            mean_metrics.broken_forced_global_rmse && win_rates.broken_beats_forced_global >= 0.75,
        coordinated_regime_competitive = mean_metrics.shared_adaptive_rmse <=
            mean_metrics.shared_local_rmse + 0.05,
    )
    summary = (
        experiment = 30,
        protocol = "online endogenous precision forecasting with unannounced structure switches",
        mean_metrics = mean_metrics,
        win_rates = win_rates,
        criteria = criteria,
    )
    GlobalPrecisionField.write_csv(joinpath(output_dir, "trace.csv"), traces)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "per_seed.csv"), metrics)
    GlobalPrecisionField.write_json(joinpath(output_dir, "summary.json"), summary)
    GlobalPrecisionField.write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = all(values(criteria)),
        theory_result = all(values(criteria)) ?
            "hyper-model learns when global precision coupling should be trusted" :
            "temporal hyper-model criteria not yet satisfied",
    ))
    return (traces = traces, metrics = metrics, summary = summary)
end

end
