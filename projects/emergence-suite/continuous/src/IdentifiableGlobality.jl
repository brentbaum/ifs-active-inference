module IdentifiableGlobality

using LinearAlgebra
using Statistics
using Main.GlobalPrecisionField
using Main.LearnedPrecisionStructure
using Main.IdentifiablePrecisionStructure

export run_globality_seed, run_identifiable_globality

function with_deviation(config::IdentifiablePrecisionStructure.IdentifiableConfig,
        deviation::Float64)
    return IdentifiablePrecisionStructure.IdentifiableConfig(
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
end

function run_globality_seed(seed::Int;
        config::IdentifiablePrecisionStructure.IdentifiableConfig =
            IdentifiablePrecisionStructure.IdentifiableConfig(seeds = [seed]))
    structure = IdentifiablePrecisionStructure.structure_config(config)
    loading = LearnedPrecisionStructure.random_channel_loading(seed)
    deviations = LearnedPrecisionStructure.random_local_deviations(
        seed, config.local_deviation_sd)
    models = Dict{String,Any}(
        "compact_global" => LearnedPrecisionStructure.LearnedGlobalForecaster(structure),
        "nested_global" => LearnedPrecisionStructure.AdaptiveLocalForecaster(
            structure; mode = :hierarchical),
        "independent_local" => LearnedPrecisionStructure.LinearFieldForecaster(
            :local, structure; shrinkage = 0.0),
    )
    rows = NamedTuple[]
    snapshots = Dict{String,Float64}()
    for episode in 1:config.episodes
        data = IdentifiablePrecisionStructure.generate_monitored_episode(
            seed, episode, loading, deviations; config = config)
        for name in ("compact_global", "nested_global", "independent_local")
            model = models[name]
            prior_mean, prior_covariance = LearnedPrecisionStructure.forecast(
                model, data.context, structure)
            if episode == config.switch_episode
                snapshots[name] = sqrt(mean((prior_mean .- data.true_phi).^2))
            end
            result = IdentifiablePrecisionStructure.infer_monitored_episode(
                data.monitored_observations, [1, 2, 3], prior_mean,
                prior_covariance; config = config)
            LearnedPrecisionStructure.update!(model, data.context,
                result.posterior_phi, [1, 2, 3], structure)
            push!(rows, (
                seed = seed,
                episode = episode,
                agent = name,
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
    return rows, snapshots
end

function seed_metrics(rows, snapshots)
    after(name) = filter(row -> row.agent == name && row.phase == "after", rows)
    nested = after("nested_global")
    return (
        seed = first(rows).seed,
        compact_forecast_error = snapshots["compact_global"],
        nested_forecast_error = snapshots["nested_global"],
        independent_forecast_error = snapshots["independent_local"],
        compact_accuracy = mean(row.correct for row in after("compact_global")),
        nested_accuracy = mean(row.correct for row in nested),
        independent_accuracy = mean(row.correct for row in after("independent_local")),
        nested_effective_shrinkage = mean(row.effective_shrinkage for row in nested),
    )
end

function condition_summary(metrics, deviation)
    mean_field(key) = mean(getfield(row, key) for row in metrics)
    compact_error = mean_field(:compact_forecast_error)
    nested_error = mean_field(:nested_forecast_error)
    independent_error = mean_field(:independent_forecast_error)
    return (
        local_deviation_sd = deviation,
        compact_forecast_error = compact_error,
        nested_forecast_error = nested_error,
        independent_forecast_error = independent_error,
        compact_gain_over_independent = independent_error - compact_error,
        nested_gain_over_independent = independent_error - nested_error,
        nested_gain_over_compact = compact_error - nested_error,
        compact_accuracy = mean_field(:compact_accuracy),
        nested_accuracy = mean_field(:nested_accuracy),
        independent_accuracy = mean_field(:independent_accuracy),
        nested_effective_shrinkage = mean_field(:nested_effective_shrinkage),
        compact_beats_independent_rate = mean(row.compact_forecast_error <
            row.independent_forecast_error for row in metrics),
        nested_beats_independent_rate = mean(row.nested_forecast_error <
            row.independent_forecast_error for row in metrics),
        nested_beats_compact_rate = mean(row.nested_forecast_error <
            row.compact_forecast_error for row in metrics),
    )
end

function structural_checks(config)
    structure = IdentifiablePrecisionStructure.structure_config(config)
    compact = LearnedPrecisionStructure.LearnedGlobalForecaster(structure)
    independent = LearnedPrecisionStructure.LinearFieldForecaster(
        :local, structure; shrinkage = 0.0)
    _, compact_covariance = LearnedPrecisionStructure.forecast(compact, 1.4, structure)
    _, independent_covariance = LearnedPrecisionStructure.forecast(
        independent, 1.4, structure)
    old_seeds = vcat(collect(8701:8720), collect(8801:8820), collect(8901:8920),
        collect(9801:9820), collect(9901:9920), collect(11001:11020))
    return (
        matched_marginal_prior_variance = diag(compact_covariance) ≈
            diag(independent_covariance),
        independent_control_has_no_shared_parameters = independent.mode == :local &&
            all(abs.(independent.prior_precision .-
                Diagonal(diag(independent.prior_precision))) .<= 1.0e-12),
        fresh_seed_block = isempty(intersect(config.seeds, old_seeds)),
        layer_monitoring_is_noisy = isfinite(config.layer_observation_precision) &&
            config.layer_observation_precision > 0,
    )
end

function run_identifiable_globality(output_dir::AbstractString = joinpath(
        @__DIR__, "..", "results", "identifiable_globality");
        config::IdentifiablePrecisionStructure.IdentifiableConfig =
            IdentifiablePrecisionStructure.IdentifiableConfig(
                seeds = collect(12001:12020)),
        deviations = (0.0, 2.0))
    mkpath(output_dir)
    all_metrics = NamedTuple[]
    conditions = NamedTuple[]
    for deviation in deviations
        candidate = with_deviation(config, Float64(deviation))
        metrics = NamedTuple[]
        for seed in candidate.seeds
            rows, snapshots = run_globality_seed(seed; config = candidate)
            metric = seed_metrics(rows, snapshots)
            push!(metrics, metric)
            push!(all_metrics, merge((local_deviation_sd = deviation,), metric))
        end
        push!(conditions, condition_summary(metrics, deviation))
    end
    exact = only(filter(row -> row.local_deviation_sd == 0.0, conditions))
    heterogeneous = only(filter(row -> row.local_deviation_sd == 2.0, conditions))
    maximum_accuracy_spread = maximum(maximum((row.compact_accuracy,
        row.nested_accuracy, row.independent_accuracy)) - minimum((row.compact_accuracy,
        row.nested_accuracy, row.independent_accuracy)) for row in conditions)
    empirical = (
        exact_compact_beats_independent = exact.compact_gain_over_independent >= 0.10 &&
            exact.compact_beats_independent_rate >= 0.75,
        exact_nested_beats_independent = exact.nested_gain_over_independent >= 0.05 &&
            exact.nested_beats_independent_rate >= 0.75,
        heterogeneous_nested_beats_compact = heterogeneous.nested_gain_over_compact >= 0.05 &&
            heterogeneous.nested_beats_compact_rate >= 0.75,
        heterogeneous_nested_no_worse_than_independent =
            heterogeneous.nested_gain_over_independent >= -0.05,
        forecast_claim_does_not_become_task_claim = maximum_accuracy_spread <= 0.03,
    )
    structural = structural_checks(config)
    summary = (
        experiment = 38,
        protocol = "fresh identifiable joint precision hyper-models versus independent local meta-loops",
        supervision = "noisy layer observations only; latent states, true precisions, and loading vectors remain scoring-only",
        confirmatory_seeds = config.seeds,
        conditions = conditions,
        empirical_criteria = empirical,
        structural_checks = structural,
        interpretation_boundary = "direct layer monitoring identifies transition precision but is not bottom-sensed Table 1",
    )
    GlobalPrecisionField.write_csv(joinpath(output_dir, "per_seed.csv"), all_metrics)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "conditions.csv"), conditions)
    GlobalPrecisionField.write_json(joinpath(output_dir, "summary.json"), summary)
    GlobalPrecisionField.write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = all(values(structural)),
        empirical_passed = all(values(empirical)),
        theory_result = all(values(empirical)) ?
            "joint precision inference beats independent local loops when structure is shared and releases tying when it is not" :
            "identifiable globality criteria not satisfied",
    ))
    return summary
end

end
