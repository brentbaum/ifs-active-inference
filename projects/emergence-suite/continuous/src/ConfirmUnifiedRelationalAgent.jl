module ConfirmUnifiedRelationalAgent

using Statistics
using Main.GlobalPrecisionField
using Main.UnifiedRelationalAgent

export run_confirm_unified_relational_agent

function copy_config(base; seeds = base.seeds, local_field = base.local_field,
        relational_field = base.relational_field,
        packet_samples = base.packet_samples,
        violation_rate = base.violation_rate)
    return UnifiedRelationalAgent.RelationalAgentConfig(
        seeds = seeds,
        episodes = base.episodes,
        training_episodes = base.training_episodes,
        switch_episode = base.switch_episode,
        packet_samples = packet_samples,
        action_budget = base.action_budget,
        local_field = local_field,
        relational_field = relational_field,
        violation_rate = violation_rate,
        inference_iterations = base.inference_iterations,
        hyper_newton_steps = base.hyper_newton_steps,
        observation_precision = base.observation_precision,
        hyper_innovation_variance = base.hyper_innovation_variance,
        parameter_prior_variance = base.parameter_prior_variance,
        regression_evidence_variance = base.regression_evidence_variance,
        regression_forgetting = base.regression_forgetting,
        cause_amplitude = base.cause_amplitude,
    )
end

function evaluate(config)
    metrics = NamedTuple[]
    for seed in config.seeds
        rows = UnifiedRelationalAgent.run_relational_agent_seed(seed; config = config)
        push!(metrics, UnifiedRelationalAgent.seed_metrics(rows))
    end
    result = UnifiedRelationalAgent.summarize(metrics, config)
    return metrics, result
end

function stress_grid(base)
    specifications = [
        (name = "baseline", local_field = 0.10, relational = 1.50, samples = 4, violation = 0.05),
        (name = "local_008", local_field = 0.08, relational = 1.50, samples = 4, violation = 0.05),
        (name = "local_012", local_field = 0.12, relational = 1.50, samples = 4, violation = 0.05),
        (name = "relation_120", local_field = 0.10, relational = 1.20, samples = 4, violation = 0.05),
        (name = "relation_180", local_field = 0.10, relational = 1.80, samples = 4, violation = 0.05),
        (name = "samples_3", local_field = 0.10, relational = 1.50, samples = 3, violation = 0.05),
        (name = "samples_5", local_field = 0.10, relational = 1.50, samples = 5, violation = 0.05),
        (name = "violation_010", local_field = 0.10, relational = 1.50, samples = 4, violation = 0.10),
    ]
    rows = NamedTuple[]
    for (index, specification) in enumerate(specifications)
        config = copy_config(base;
            seeds = collect((15001 + 10index):(15005 + 10index)),
            local_field = specification.local_field,
            relational_field = specification.relational,
            packet_samples = specification.samples,
            violation_rate = specification.violation)
        _, result = evaluate(config)
        means, wins, _, _, _ = result
        relational_gain = means.full_accuracy - means.factorized_accuracy
        action_gain = means.full_accuracy - means.random_accuracy
        push!(rows, (
            cell = specification.name,
            seed_start = first(config.seeds),
            seed_end = last(config.seeds),
            local_field = specification.local_field,
            relational_field = specification.relational,
            packet_samples = specification.samples,
            violation_rate = specification.violation,
            local_mutual_information = local_mutual_information(config),
            relational_gain = relational_gain,
            action_gain = action_gain,
            relational_seed_win_rate = wins.relational_over_factorized,
            action_seed_win_rate = wins.active_over_random,
            before_channel_1 = means.full_before_channel_1,
            after_channel_3 = means.full_after_channel_3,
            budget_difference = means.full_mean_packets - means.random_mean_packets,
            signature_retained = relational_gain >= 0.015 && action_gain >= 0.020 &&
                means.full_before_channel_1 >= 0.55 && means.full_after_channel_3 >= 0.55 &&
                means.full_mean_packets == means.random_mean_packets,
        ))
    end
    return rows
end

function zero_relation_control(base)
    config = copy_config(base; seeds = collect(15101:15105), relational_field = 0.0)
    _, result = evaluate(config)
    means, wins, _, _, _ = result
    return (
        seed_start = first(config.seeds),
        seed_end = last(config.seeds),
        relational_gain = means.full_accuracy - means.factorized_accuracy,
        action_gain = means.full_accuracy - means.random_accuracy,
        relational_seed_win_rate = wins.relational_over_factorized,
        action_seed_win_rate = wins.active_over_random,
        before_channel_1 = means.full_before_channel_1,
        after_channel_3 = means.full_after_channel_3,
        joint_effect_removed = abs(means.full_accuracy - means.factorized_accuracy) <= 0.015,
        action_preserved = means.full_accuracy >= means.random_accuracy + 0.020 &&
            means.full_before_channel_1 >= 0.55 && means.full_after_channel_3 >= 0.55,
    )
end

function run_confirm_unified_relational_agent(output_dir::AbstractString = joinpath(
        @__DIR__, "..", "results", "confirm_unified_relational_agent"))
    mkpath(output_dir)
    config = UnifiedRelationalAgent.RelationalAgentConfig(seeds = collect(14001:14020))
    metrics, result = evaluate(config)
    means, wins, exploratory, implementation, optimization = result
    stress = stress_grid(config)
    zero_relation = zero_relation_control(config)
    empirical = (
        partially_informative_local_causes = local_mutual_information(config) > 0.01,
        relational_binding_confirmed = means.full_accuracy >=
            means.factorized_accuracy + 0.030 && wins.relational_over_factorized >= 0.75,
        epistemic_action_confirmed = means.full_accuracy >=
            means.random_accuracy + 0.030 && wins.active_over_random >= 0.75,
        coherent_relational_gain = means.full_coherent_accuracy >=
            means.factorized_coherent_accuracy + 0.030,
        adversarial_relation_scope = means.full_violation_accuracy <=
            means.factorized_violation_accuracy,
        precision_guided_reallocation = means.full_before_channel_1 >= 0.75 &&
            means.full_after_channel_3 >= 0.75 && means.blind_after_channel_3 <= 0.20,
        matched_budget_and_replay = means.full_mean_packets == means.random_mean_packets &&
            means.replay_action_match_rate >= 0.999,
        stress_signature = count(row.signature_retained for row in stress) >= 6,
        zero_relation_removes_only_joint_gain = zero_relation.joint_effect_removed &&
            zero_relation.action_preserved,
    )
    summary = (
        experiment = 40,
        stage = "frozen confirmation",
        protocol = "fresh confirmation and load-bearing stress of unified relational binding, precision recursion, and action",
        confirmatory_seeds = config.seeds,
        local_mutual_information = local_mutual_information(config),
        mean_metrics = means,
        win_rates = wins,
        pilot_threshold_checks = exploratory,
        empirical_criteria = empirical,
        implementation_checks = implementation,
        optimization_checks = optimization,
        stress_tests = (
            cells_passed = count(row.signature_retained for row in stress),
            cells_total = length(stress),
        ),
        zero_relation_control = zero_relation,
    )
    GlobalPrecisionField.write_csv(joinpath(output_dir, "per_seed.csv"), metrics)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "stress.csv"), stress)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "zero_relation.csv"), [zero_relation])
    GlobalPrecisionField.write_json(joinpath(output_dir, "summary.json"), summary)
    GlobalPrecisionField.write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = all(values(implementation)) && all(values(optimization)),
        empirical_passed = all(values(empirical)),
        theory_result = all(values(empirical)) ?
            "one fresh-seed agent combines nonvacuous joint binding, recursive precision inference, and epistemic action" :
            "one or more frozen unified-agent criteria failed",
    ))
    return summary
end

end
