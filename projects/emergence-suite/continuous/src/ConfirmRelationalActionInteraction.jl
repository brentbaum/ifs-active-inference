module ConfirmRelationalActionInteraction

using Statistics
using Main.GlobalPrecisionField
using Main.UnifiedRelationalAgent
using Main.MatchedMarginalRelationAblation

export run_confirm_relational_action_interaction

function evaluate_condition(config, scene_mode, model_mode)
    metrics = NamedTuple[]
    for seed in config.seeds
        rows = UnifiedRelationalAgent.run_relational_agent_seed(seed;
            config = config, scene_mode = scene_mode, model_mode = model_mode)
        push!(metrics, UnifiedRelationalAgent.seed_metrics(rows))
    end
    result = UnifiedRelationalAgent.summarize(metrics, config)
    return metrics, result
end

function run_confirm_relational_action_interaction(output_dir::AbstractString =
        joinpath(@__DIR__, "..", "results", "confirm_relational_action_interaction"))
    mkpath(output_dir)
    config = UnifiedRelationalAgent.RelationalAgentConfig(
        seeds = collect(16001:16020), violation_rate = 0.0)
    relational_metrics, relational_result = evaluate_condition(
        config, :relational, :relational)
    factorized_metrics, factorized_result = evaluate_condition(
        config, :factorized, :factorized)
    relational_means, relational_wins, _, relational_implementation,
        relational_optimization = relational_result
    factorized_means, factorized_wins, _, factorized_implementation,
        factorized_optimization = factorized_result

    relational_binding_gain = relational_means.full_accuracy -
        relational_means.factorized_accuracy
    relational_action_gain = relational_means.full_accuracy -
        relational_means.random_accuracy
    factorized_action_gain = factorized_means.full_accuracy -
        factorized_means.random_accuracy
    interaction = relational_action_gain - factorized_action_gain
    projection_error = MatchedMarginalRelationAblation.factorized_projection_error(config)

    implementation = (
        exact_conditional_local_marginals = projection_error <= 1.0e-12,
        relational_checks = all(values(relational_implementation)),
        factorized_checks = all(values(factorized_implementation)),
        relational_replay_exact = relational_means.replay_action_match_rate >= 0.999,
        factorized_replay_exact = factorized_means.replay_action_match_rate >= 0.999,
        matched_packet_budgets = relational_means.full_mean_packets ==
            relational_means.random_mean_packets ==
            factorized_means.full_mean_packets ==
            factorized_means.random_mean_packets,
    )
    optimization = (
        relational_line_search = all(values(relational_optimization)),
        factorized_line_search = all(values(factorized_optimization)),
    )
    empirical = (
        relational_binding_present = relational_binding_gain >= 0.030 &&
            relational_wins.relational_over_factorized >= 0.75,
        relational_action_advantage = relational_action_gain >= 0.030 &&
            relational_wins.active_over_random >= 0.75,
        factorized_action_negligible = abs(factorized_action_gain) <= 0.015,
        relational_action_interaction = interaction >= 0.030,
        relational_policy_reallocates = relational_means.full_before_channel_1 >= 0.75 &&
            relational_means.full_after_channel_3 >= 0.75 &&
            relational_means.blind_after_channel_3 <= 0.20,
        factorized_policy_reallocates = factorized_means.full_before_channel_1 >= 0.75 &&
            factorized_means.full_after_channel_3 >= 0.75 &&
            factorized_means.blind_after_channel_3 <= 0.20,
    )
    summary = (
        experiment = 42,
        stage = "frozen paired confirmation",
        protocol = "relational structure by precision-guided epistemic action interaction at exactly matched conditional local marginals",
        seeds = config.seeds,
        projection_error = projection_error,
        effect_summary = (
            relational_binding_gain = relational_binding_gain,
            relational_action_gain = relational_action_gain,
            factorized_action_gain = factorized_action_gain,
            action_interaction = interaction,
        ),
        relational_mean_metrics = relational_means,
        factorized_mean_metrics = factorized_means,
        relational_win_rates = relational_wins,
        factorized_win_rates = factorized_wins,
        empirical_criteria = empirical,
        implementation_checks = implementation,
        optimization_checks = optimization,
    )
    GlobalPrecisionField.write_csv(joinpath(output_dir, "relational_per_seed.csv"),
        relational_metrics)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "factorized_per_seed.csv"),
        factorized_metrics)
    GlobalPrecisionField.write_json(joinpath(output_dir, "summary.json"), summary)
    GlobalPrecisionField.write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = all(values(implementation)) &&
            all(values(optimization)),
        empirical_passed = all(values(empirical)),
        theory_result = all(values(empirical)) ?
            "relational dependence makes precision-guided sampling instrumentally valuable" :
            "one or more frozen relational-action interaction criteria failed",
    ))
    return summary
end

end
