module ConfirmatoryBeautifulLoop

using Statistics
using Main.GlobalPrecisionField
using Main.CompetitiveBinding
using Main.LearnedPrecisionStructure

export run_confirmatory_beautiful_loop

function binding_metrics(config)
    metrics = NamedTuple[]
    for seed in config.seeds
        rows, forecast_errors = CompetitiveBinding.run_competitive_seed(seed;
            config = config)
        push!(metrics, CompetitiveBinding.seed_metrics(rows, forecast_errors))
    end
    return metrics, CompetitiveBinding.summarize(metrics)
end

function structure_metrics(config)
    metrics = NamedTuple[]
    for seed in config.seeds
        rows, snapshot, loading_snapshot, loading =
            LearnedPrecisionStructure.run_structure_seed(seed; config = config)
        push!(metrics, LearnedPrecisionStructure.seed_metrics(
            rows, snapshot, loading_snapshot, loading))
    end
    return metrics, LearnedPrecisionStructure.summarize(metrics)
end

function binding_stress_grid()
    specifications = [
        (name = "baseline", amplitude = 1.05, samples = 4, relation_noise = 0.05),
        (name = "low_signal", amplitude = 0.85, samples = 4, relation_noise = 0.05),
        (name = "high_signal", amplitude = 1.25, samples = 4, relation_noise = 0.05),
        (name = "fewer_samples", amplitude = 1.05, samples = 3, relation_noise = 0.05),
        (name = "more_samples", amplitude = 1.05, samples = 5, relation_noise = 0.05),
        (name = "exact_relation", amplitude = 1.05, samples = 4, relation_noise = 0.00),
        (name = "noisy_relation", amplitude = 1.05, samples = 4, relation_noise = 0.10),
    ]
    rows = NamedTuple[]
    for (index, specification) in enumerate(specifications)
        config = CompetitiveBinding.CompetitiveConfig(
            seeds = collect((10_001 + 10index):(10_005 + 10index)),
            cause_amplitude = specification.amplitude,
            samples_per_action = specification.samples,
            relation_noise = specification.relation_noise,
        )
        _, result = binding_metrics(config)
        means, wins, _, _, _ = result
        overall_gain = means.full_accuracy - means.independent_accuracy
        coherent_gain = means.full_coherent_accuracy - means.independent_coherent_accuracy
        push!(rows, (
            cell = specification.name,
            seed_start = first(config.seeds),
            seed_end = last(config.seeds),
            cause_amplitude = specification.amplitude,
            samples_per_action = specification.samples,
            relation_noise = specification.relation_noise,
            full_accuracy = means.full_accuracy,
            independent_accuracy = means.independent_accuracy,
            overall_gain = overall_gain,
            coherent_gain = coherent_gain,
            seed_win_rate = wins.overall,
            signature_retained = overall_gain >= 0.10 && coherent_gain >= 0.15,
        ))
    end
    return rows
end

function structure_stress_grid()
    specifications = [
        (name = "baseline", evidence = 0.45, forgetting = 0.995, training = 80, deviation = 0.0),
        (name = "evidence_030", evidence = 0.30, forgetting = 0.995, training = 80, deviation = 0.0),
        (name = "evidence_070", evidence = 0.70, forgetting = 0.995, training = 80, deviation = 0.0),
        (name = "forget_0990", evidence = 0.45, forgetting = 0.990, training = 80, deviation = 0.0),
        (name = "forget_0999", evidence = 0.45, forgetting = 0.999, training = 80, deviation = 0.0),
        (name = "training_060", evidence = 0.45, forgetting = 0.995, training = 60, deviation = 0.0),
        (name = "training_100", evidence = 0.45, forgetting = 0.995, training = 100, deviation = 0.0),
        (name = "deviation_030", evidence = 0.45, forgetting = 0.995, training = 80, deviation = 0.30),
        (name = "deviation_100", evidence = 0.45, forgetting = 0.995, training = 80, deviation = 1.00),
        (name = "deviation_200", evidence = 0.45, forgetting = 0.995, training = 80, deviation = 2.00),
        (name = "deviation_300", evidence = 0.45, forgetting = 0.995, training = 80, deviation = 3.00),
    ]
    rows = NamedTuple[]
    for (index, specification) in enumerate(specifications)
        config = LearnedPrecisionStructure.StructureConfig(
            seeds = collect((10_201 + 10index):(10_205 + 10index)),
            regression_evidence_variance = specification.evidence,
            regression_forgetting = specification.forgetting,
            training_episodes = specification.training,
            local_deviation_sd = specification.deviation,
        )
        _, result = structure_metrics(config)
        means, wins, _, _ = result
        global_gain = means.adaptive_forecast_error - means.global_forecast_error
        if specification.deviation < 1.0
            prediction_passed = global_gain >= 0.05
        elseif specification.deviation == 1.0
            prediction_passed = abs(global_gain) <= 0.10
        elseif specification.deviation == 2.0
            prediction_passed = global_gain <= 0.0
        else
            prediction_passed = global_gain <= -0.05 &&
                means.adaptive_effective_shrinkage < 7.38
        end
        push!(rows, (
            cell = specification.name,
            seed_start = first(config.seeds),
            seed_end = last(config.seeds),
            regression_evidence_variance = specification.evidence,
            regression_forgetting = specification.forgetting,
            training_episodes = specification.training,
            local_deviation_sd = specification.deviation,
            global_forecast_error = means.global_forecast_error,
            adaptive_forecast_error = means.adaptive_forecast_error,
            independent_forecast_error = means.independent_forecast_error,
            adaptive_minus_global = global_gain,
            adaptive_effective_shrinkage = means.adaptive_effective_shrinkage,
            global_seed_win_rate = wins.global_beats_adaptive,
            prediction_passed = prediction_passed,
        ))
    end
    return rows
end

function run_confirmatory_beautiful_loop(output_dir::AbstractString =
        joinpath(@__DIR__, "..", "results", "confirmatory_beautiful_loop"))
    mkpath(output_dir)
    binding_config = CompetitiveBinding.CompetitiveConfig(seeds = collect(9801:9820))
    structure_config = LearnedPrecisionStructure.StructureConfig(seeds = collect(9901:9920))
    binding_per_seed, binding_result = binding_metrics(binding_config)
    structure_per_seed, structure_result = structure_metrics(structure_config)
    binding_means, binding_wins, binding_empirical, binding_structural,
        binding_optimization = binding_result
    structure_means, structure_wins, structure_empirical, structure_structural = structure_result
    binding_stress = binding_stress_grid()
    structure_stress = structure_stress_grid()

    binding_confirmed = all(values(binding_empirical)) &&
        binding_wins.overall >= 0.90 && binding_wins.coherent >= 0.90
    structure_confirmed = all(values(structure_empirical))
    binding_stress_passed = count(row.signature_retained for row in binding_stress) >= 6
    regular_structure_cells = filter(row -> row.local_deviation_sd < 1.0,
        structure_stress)
    structure_stress_passed = count(row.prediction_passed for row in regular_structure_cells) >= 7 &&
        all(row.prediction_passed for row in filter(row -> row.local_deviation_sd >= 2.0,
            structure_stress))
    empirical = (
        relational_binding_confirmed = binding_confirmed,
        learned_precision_structure_confirmed = structure_confirmed,
        binding_stress_signature = binding_stress_passed,
        precision_scope_crossover = structure_stress_passed,
    )
    summary = (
        experiment = 36,
        protocol = "frozen fresh-seed confirmation and load-bearing stress tests",
        confirmatory_seed_blocks = (
            binding = binding_config.seeds,
            learned_precision = structure_config.seeds,
        ),
        binding = (
            mean_metrics = binding_means,
            win_rates = binding_wins,
            empirical_criteria = binding_empirical,
            structural_checks = binding_structural,
            optimization_checks = binding_optimization,
        ),
        learned_precision = (
            mean_metrics = structure_means,
            win_rates = structure_wins,
            empirical_criteria = structure_empirical,
            structural_checks = structure_structural,
        ),
        stress_tests = (
            binding_cells_passed = count(row.signature_retained for row in binding_stress),
            binding_cells_total = length(binding_stress),
            structure_predictions_passed = count(row.prediction_passed for row in structure_stress),
            structure_cells_total = length(structure_stress),
        ),
        empirical_criteria = empirical,
    )
    GlobalPrecisionField.write_csv(joinpath(output_dir, "binding_per_seed.csv"),
        binding_per_seed)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "structure_per_seed.csv"),
        structure_per_seed)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "binding_stress.csv"),
        binding_stress)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "structure_stress.csv"),
        structure_stress)
    GlobalPrecisionField.write_json(joinpath(output_dir, "summary.json"), summary)
    GlobalPrecisionField.write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = all(values(binding_structural)) &&
            all(values(binding_optimization)) &&
            all(values(structure_structural)),
        empirical_passed = all(values(empirical)),
        theory_result = all(values(empirical)) ?
            "relational binding and learned global precision confirmed with an earned local-deviation crossover" :
            "one or more frozen confirmatory criteria failed",
    ))
    return summary
end

end
