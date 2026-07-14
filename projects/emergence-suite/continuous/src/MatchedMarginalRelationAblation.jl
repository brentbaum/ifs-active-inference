module MatchedMarginalRelationAblation

using Statistics
using Main.GlobalPrecisionField
using Main.UnifiedRelationalAgent

export factorized_projection_error, run_matched_marginal_relation_ablation

function conditional_local_probability(global_cause, channel, mode, config)
    return sum(exp(UnifiedRelationalAgent.scene_log_prior(
            global_cause, local_causes, mode, config) + log(2))
        for local_causes in UnifiedRelationalAgent.LOCAL_CONFIGURATIONS
        if local_causes[channel] == 1)
end

function factorized_projection_error(config)
    return maximum([abs(
        conditional_local_probability(g, channel, :relational, config) -
        conditional_local_probability(g, channel, :factorized, config)
        ) for g in (-1, 1), channel in 1:3])
end

function evaluate(seeds, config)
    metrics = NamedTuple[]
    for seed in seeds
        rows = UnifiedRelationalAgent.run_relational_agent_seed(seed;
            config = config, scene_mode = :factorized, model_mode = :factorized)
        push!(metrics, UnifiedRelationalAgent.seed_metrics(rows))
    end
    result = UnifiedRelationalAgent.summarize(metrics, config)
    return metrics, result
end

function run_matched_marginal_relation_ablation(output_dir::AbstractString;
        seeds = collect(15101:15105), stage = "recycled-seed diagnostic",
        minimum_action_gain = 0.020, minimum_win_rate = 0.60)
    mkpath(output_dir)
    config = UnifiedRelationalAgent.RelationalAgentConfig(
        seeds = collect(seeds), violation_rate = 0.0)
    metrics, result = evaluate(config.seeds, config)
    means, wins, _, implementation, optimization = result
    projection_error = factorized_projection_error(config)
    empirical = (
        exact_conditional_local_marginals = projection_error <= 1.0e-12,
        joint_effect_removed = abs(means.full_accuracy -
            means.factorized_accuracy) <= 1.0e-12,
        epistemic_action_retained = means.full_accuracy >=
            means.random_accuracy + minimum_action_gain &&
            wins.active_over_random >= minimum_win_rate,
        precision_guided_reallocation = means.full_before_channel_1 >= 0.75 &&
            means.full_after_channel_3 >= 0.75 &&
            means.blind_after_channel_3 <= 0.20,
        matched_budget_and_replay = means.full_mean_packets ==
            means.random_mean_packets && means.replay_action_match_rate >= 0.999,
    )
    summary = (
        experiment = 41,
        stage = stage,
        protocol = "exact factorized projection preserves conditional local marginals while removing relational synergy",
        seeds = config.seeds,
        projection_error = projection_error,
        thresholds = (
            minimum_action_gain = minimum_action_gain,
            minimum_win_rate = minimum_win_rate,
        ),
        mean_metrics = means,
        win_rates = wins,
        empirical_criteria = empirical,
        implementation_checks = implementation,
        optimization_checks = optimization,
    )
    GlobalPrecisionField.write_csv(joinpath(output_dir, "per_seed.csv"), metrics)
    GlobalPrecisionField.write_json(joinpath(output_dir, "summary.json"), summary)
    GlobalPrecisionField.write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = all(values(implementation)) &&
            all(values(optimization)),
        empirical_passed = all(values(empirical)),
        theory_result = all(values(empirical)) ?
            "joint binding is removed while precision-guided action survives at matched local marginals" :
            "matched-marginal ablation diagnostic did not retain every target operation",
    ))
    return summary
end

end
