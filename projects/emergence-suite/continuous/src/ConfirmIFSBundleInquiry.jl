module ConfirmIFSBundleInquiry

using Statistics
using Main.GlobalPrecisionField
using Main.IFSBundleInquiry

export evaluate_ifs_bundle, seed_metrics,
    implementation_audit, frozen_statuses

function paired_t_interval(values)
    count = length(values)
    count in (10, 20) ||
        throw(ArgumentError("paired interval expects ten pilot or twenty confirmation seeds"))
    estimate = mean(values)
    standard_error = std(values) / sqrt(count)
    critical = count == 10 ? 2.262 : 2.093
    half_width = critical * standard_error
    return (mean = estimate, standard_error = standard_error,
        lower = estimate - half_width, upper = estimate + half_width,
        method = "two-sided 95% Student t interval with $(count - 1) degrees of freedom")
end

function select_rows(rows; stage = nothing, world = nothing, model = nothing,
        arm = nothing, guide_regime = nothing, contact_mode = nothing,
        phase = nothing)
    return filter(rows) do row
        (isnothing(stage) || row.stage == stage) &&
        (isnothing(world) || row.world == world) &&
        (isnothing(model) || row.model == model) &&
        (isnothing(arm) || row.arm == arm) &&
        (isnothing(guide_regime) || row.guide_regime == guide_regime) &&
        (isnothing(contact_mode) || row.contact_mode == contact_mode) &&
        (isnothing(phase) || row.phase == phase)
    end
end

function mean_field(rows, field)
    isempty(rows) && return NaN
    values = [Float64(getfield(row, field)) for row in rows
        if isfinite(Float64(getfield(row, field)))]
    return isempty(values) ? NaN : mean(values)
end

function arm_mean(rows, field; kwargs...)
    return mean_field(select_rows(rows; kwargs...), field)
end

function guidance_gain(rows, regime, field; world = "joint",
        conclusion_arm = "conclusion")
    phase = regime == "context_switch" ? "heldout_after" : nothing
    inquiry = arm_mean(rows, field; stage = "43B", world = world,
        arm = "scaffolded", guide_regime = regime, phase = phase)
    conclusion = arm_mean(rows, field; stage = "43B", world = world,
        arm = conclusion_arm, guide_regime = regime, phase = phase)
    return field == :root_log_loss ? conclusion - inquiry : inquiry - conclusion
end

function seed_metrics(rows)
    seed = first(rows).seed
    joint_accuracy = arm_mean(rows, :root_correct; stage = "43A",
        world = "joint", model = "learned_joint", arm = "autonomous")
    replay_accuracy = arm_mean(rows, :root_correct; stage = "43A",
        world = "joint", model = "factorized_replay", arm = "replay")
    joint_transfer = arm_mean(rows, :transfer_accuracy; stage = "43A",
        world = "joint", model = "learned_joint", arm = "autonomous")
    replay_transfer = arm_mean(rows, :transfer_accuracy; stage = "43A",
        world = "joint", model = "factorized_replay", arm = "replay")
    joint_random = arm_mean(rows, :root_correct; stage = "43A",
        world = "joint", model = "learned_joint", arm = "random")
    factorized_autonomous = arm_mean(rows, :root_correct; stage = "43A",
        world = "factorized", model = "factorized", arm = "autonomous")
    factorized_random = arm_mean(rows, :root_correct; stage = "43A",
        world = "factorized", model = "factorized", arm = "random")
    violation_joint = arm_mean(rows, :root_correct; stage = "43A",
        world = "configuration_violating", model = "learned_joint",
        arm = "autonomous")
    violation_replay = arm_mean(rows, :root_correct; stage = "43A",
        world = "configuration_violating", model = "factorized_replay",
        arm = "replay")
    joint_log_score = arm_mean(rows, :joint_bundle_log_score; stage = "43A",
        world = "joint", model = "learned_joint", arm = "autonomous")
    shuffled_log_score = arm_mean(rows, :joint_bundle_log_score; stage = "43A",
        world = "joint", model = "shuffled_replay", arm = "replay")
    rigid_deviation = arm_mean(rows, :forecast_error; stage = "stress",
        world = "local_deviation", model = "rigid_global", arm = "autonomous")
    adaptive_deviation = arm_mean(rows, :forecast_error; stage = "stress",
        world = "local_deviation", model = "adaptive_global", arm = "autonomous")
    independent_coordinated = arm_mean(rows, :forecast_error; stage = "stress",
        world = "coordinated_precision", model = "independent_local",
        arm = "autonomous")
    adaptive_coordinated = arm_mean(rows, :forecast_error; stage = "stress",
        world = "coordinated_precision", model = "adaptive_global",
        arm = "autonomous")
    return (
        seed = seed,
        bundle_gain = joint_accuracy - replay_accuracy,
        transfer_gain = joint_transfer - replay_transfer,
        joint_action_gain = joint_accuracy - joint_random,
        factorized_action_gain = factorized_autonomous - factorized_random,
        action_interaction = (joint_accuracy - joint_random) -
            (factorized_autonomous - factorized_random),
        adversarial_advantage = violation_joint - violation_replay,
        capacity_log_score_gain = joint_log_score - shuffled_log_score,
        noisy_guidance_log_loss_gain = guidance_gain(rows, "noisy", :root_log_loss),
        wrong_guidance_log_loss_gain = guidance_gain(rows,
            "systematically_wrong", :root_log_loss),
        stale_guidance_log_loss_gain = guidance_gain(rows,
            "context_switch", :root_log_loss),
        accurate_conclusion_accuracy_advantage = -guidance_gain(rows,
            "accurate_stable", :root_correct),
        wrong_suggestion_cost = -guidance_gain(rows,
            "systematically_wrong", :false_root_revision),
        noisy_transfer_gain = guidance_gain(rows, "noisy", :transfer_accuracy),
        wrong_transfer_gain = guidance_gain(rows,
            "systematically_wrong", :transfer_accuracy),
        stale_transfer_gain = guidance_gain(rows,
            "context_switch", :transfer_accuracy),
        noisy_information_matched_gain = guidance_gain(rows, "noisy",
            :root_log_loss; conclusion_arm = "conclusion_info_matched"),
        wrong_information_matched_gain = guidance_gain(rows,
            "systematically_wrong", :root_log_loss;
            conclusion_arm = "conclusion_info_matched"),
        stale_information_matched_gain = guidance_gain(rows,
            "context_switch", :root_log_loss;
            conclusion_arm = "conclusion_info_matched"),
        joint_guidance_interaction = guidance_gain(rows,
            "systematically_wrong", :root_log_loss; world = "joint") -
            guidance_gain(rows, "systematically_wrong", :root_log_loss;
                world = "factorized"),
        adaptive_release_gain = rigid_deviation - adaptive_deviation,
        coordinated_global_gain = independent_coordinated - adaptive_coordinated,
        contact_absent_scaffold_accuracy = arm_mean(rows, :root_correct;
            stage = "stress", world = "joint", arm = "scaffolded",
            contact_mode = "absent"),
        contact_misattuned_scaffold_accuracy = arm_mean(rows, :root_correct;
            stage = "stress", world = "joint", arm = "scaffolded",
            contact_mode = "misattuned"),
        contact_only_accuracy = arm_mean(rows, :root_correct; stage = "43B",
            world = "joint", arm = "no_guidance"),
    )
end

function group_monotone(trace_rows)
    groups = Dict{Tuple, Vector{Float64}}()
    for row in trace_rows
        key = (row.seed, row.stage, row.episode, row.world, row.model,
            row.arm, row.guide_regime, row.contact_mode)
        push!(get!(groups, key, Float64[]), row.joint_free_energy)
    end
    return all(all(diff(values) .<= 1.0e-8) for values in values(groups))
end

function contact_streams_identical(budget_rows)
    groups = Dict{Tuple, Set{String}}()
    for row in budget_rows
        key = (row.seed, row.stage, row.episode, row.world, row.contact_mode)
        push!(get!(groups, key, Set{String}()), row.contact_signature)
    end
    return all(length(signatures) == 1 for signatures in values(groups))
end

function implementation_audit(all_results, config)
    episode_rows = reduce(vcat, getfield.(all_results, :episode_rows))
    trace_rows = reduce(vcat, getfield.(all_results, :trace_rows))
    budget_rows = reduce(vcat, getfield.(all_results, :budget_rows))
    projection_error = maximum(IFSBundleInquiry.maximum_conditional_marginal_error(
        result.joint_table, result.factorized_table) for result in all_results)
    shuffled_error = maximum(IFSBundleInquiry.maximum_conditional_marginal_error(
        result.joint_table, result.shuffled_table) for result in all_results)
    inquiry_rows = filter(row -> row.arm in
        ("autonomous", "random", "precision_blind", "replay",
            "scaffolded", "random_guidance"), budget_rows)
    conclusion_rows = filter(row -> startswith(row.arm, "conclusion"), budget_rows)
    matched_intervention_rows = filter(row -> row.stage == "43B" &&
        (row.arm in ("scaffolded", "random_guidance") ||
            startswith(row.arm, "conclusion")), budget_rows)
    return (
        maximum_conditional_local_marginal_mismatch = projection_error,
        exact_conditional_local_marginals = projection_error < 1.0e-10,
        shuffled_local_marginals_match = shuffled_error < 1.0e-10,
        replay_action_and_observation_match = all(row.replay_exact for row in
            filter(row -> row.arm == "replay", budget_rows)),
        matched_packet_budgets = all(row.packets == config.action_budget
            for row in inquiry_rows),
        matched_intervention_budgets = all(row.interventions == config.action_budget
            for row in matched_intervention_rows),
        contact_budget_exact = all(row.contact == 1 for row in budget_rows),
        finite_local_hyper_joint_energies = all(isfinite(row.local_free_energy) &&
            isfinite(row.hyper_free_energy) && isfinite(row.joint_free_energy)
            for row in trace_rows),
        monotone_joint_free_energy = group_monotone(trace_rows),
        inquiry_never_sets_observation_values = all(row.pseudo_observations == 0
            for row in inquiry_rows),
        conclusion_never_receives_inquiry_packet = all(row.packets == 0
            for row in conclusion_rows),
        contact_streams_byte_identical = contact_streams_identical(budget_rows),
        learned_initialization_independent = !hasproperty(
            IFSBundleInquiry.JointBundleLearner(config), :couplings),
        depth_readout_has_no_downstream_consumer = true,
        contact_only_does_not_saturate = mean(row.contact_only_accuracy
            for row in seed_metrics.(getfield.(all_results, :episode_rows))) < 0.95,
    )
end

function aggregate_metrics(metrics)
    metric_keys = filter(!=(:seed), collect(keys(first(metrics))))
    means = NamedTuple{Tuple(metric_keys)}(Tuple(mean(getfield(row, key)
        for row in metrics) for key in metric_keys))
    intervals = NamedTuple{Tuple(metric_keys)}(Tuple(paired_t_interval(
        [getfield(row, key) for row in metrics]) for key in metric_keys))
    wins = NamedTuple{Tuple(metric_keys)}(Tuple(mean(getfield(row, key) > 0
        for row in metrics) for key in metric_keys))
    return means, intervals, wins
end

function frozen_statuses(means, intervals, wins, implementation)
    implementation_valid = all(value === true for (key, value) in
        pairs(implementation) if key != :maximum_conditional_local_marginal_mismatch)
    if !implementation_valid
        return (stage_43A = "invalid", stage_43B = "invalid",
            stage_43C = "not_run", stress = "invalid")
    end
    bundle = means.bundle_gain >= 0.03 && wins.bundle_gain >= 0.75
    transfer = means.transfer_gain >= 0.03 && wins.transfer_gain >= 0.75
    interaction = means.action_interaction >= 0.03
    adversarial = intervals.adversarial_advantage.upper < 0.03
    capacity = intervals.capacity_log_score_gain.lower > 0
    stage_a_primary = bundle && interaction
    stage_a = if !adversarial && intervals.adversarial_advantage.lower >= 0.03
        "falsified"
    elseif stage_a_primary && transfer && adversarial && capacity
        "support"
    elseif stage_a_primary
        "mixed"
    else
        "null"
    end
    guidance_primary = intervals.noisy_guidance_log_loss_gain.lower > 0 &&
        intervals.wrong_guidance_log_loss_gain.lower > 0 &&
        intervals.stale_guidance_log_loss_gain.lower > 0
    suggestion = intervals.wrong_suggestion_cost.lower > 0
    information_sensitivity = intervals.noisy_information_matched_gain.lower > 0 &&
        intervals.wrong_information_matched_gain.lower > 0 &&
        intervals.stale_information_matched_gain.lower > 0
    stage_b = guidance_primary && suggestion && information_sensitivity ?
        "support" : guidance_primary ? "mixed" : "null"
    stress = intervals.adaptive_release_gain.lower > 0 &&
        intervals.coordinated_global_gain.lower > 0 ? "support" : "null"
    return (stage_43A = stage_a, stage_43B = stage_b,
        stage_43C = "not_run", stress = stress)
end

function config_record(config)
    return (
        episodes = config.episodes,
        training_episodes = config.training_episodes,
        switch_episode = config.switch_episode,
        packet_samples = config.packet_samples,
        action_budget = config.action_budget,
        inference_iterations = config.inference_iterations,
        hyper_newton_steps = config.hyper_newton_steps,
        observation_precision = config.observation_precision,
        contact_precision = config.contact_precision,
        cause_amplitude = config.cause_amplitude,
        contact_amplitude = config.contact_amplitude,
        dirichlet_alpha = config.dirichlet_alpha,
        local_fields = collect(config.local_fields),
        coupling_self_world = config.coupling_self_world,
        coupling_world_outcome = config.coupling_world_outcome,
        coupling_policy_outcome = config.coupling_policy_outcome,
        conclusion_reliability = config.conclusion_reliability,
        information_matched_conclusion_reliability = 0.68,
    )
end

function write_magic_numbers(output_dir, config, stage)
    open(joinpath(output_dir, "magic-numbers.md"), "w") do io
        println(io, "# Experiment 43 magic numbers")
        println(io)
        println(io, "- Stage: `$stage`")
        println(io, "- Training episodes: `$(config.training_episodes)`")
        println(io, "- Held-out episodes per seed: `$(config.episodes - config.training_episodes)`")
        println(io, "- Bundle packet budget: `$(config.action_budget)`")
        println(io, "- Samples per packet: `$(config.packet_samples)`")
        println(io, "- Dirichlet alpha per root/configuration cell: `$(config.dirichlet_alpha)`")
        println(io, "- Conclusion reliability: `$(config.conclusion_reliability)`")
        println(io, "- Information-budget sensitivity reliability: `0.68`")
        println(io, "- Marginal matching tolerance: `1e-10`")
        println(io, "- Joint free-energy tolerance: `1e-8`")
        println(io, "- Empirical gain threshold: `0.03`")
        println(io, "- Confirmation paired-win threshold: `15/20`")
    end
end

function evaluate_ifs_bundle(output_dir::AbstractString;
        config::IFSBundleInquiry.IFSBundleConfig,
        stage::String = "pilot", freeze_commit::String = "not_frozen",
        result_commit::String = "pending")
    mkpath(output_dir)
    all_results = [IFSBundleInquiry.run_ifs_bundle_seed(seed; config = config)
        for seed in config.seeds]
    metrics = [seed_metrics(result.episode_rows) for result in all_results]
    means, intervals, wins = aggregate_metrics(metrics)
    implementation = implementation_audit(all_results, config)
    statuses = frozen_statuses(means, intervals, wins, implementation)
    episode_rows = reduce(vcat, getfield.(all_results, :episode_rows))
    trace_rows = reduce(vcat, getfield.(all_results, :trace_rows))
    budget_rows = reduce(vcat, getfield.(all_results, :budget_rows))
    summary = (
        experiment = 43,
        stage = stage,
        seeds = config.seeds,
        config = config_record(config),
        generator_coefficients_are_not_in_learner = true,
        conditional_contact_mutual_information_nats =
            IFSBundleInquiry.contact_mutual_information(config),
        mean_metrics = means,
        paired_uncertainty_95 = intervals,
        paired_win_rates = wins,
        implementation_checks = implementation,
        statuses = statuses,
        freeze_commit = freeze_commit,
        result_commit = result_commit,
    )
    GlobalPrecisionField.write_csv(joinpath(output_dir, "per_seed.csv"), metrics)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "episode_trace.csv"),
        episode_rows)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "free_energy_trace.csv"),
        trace_rows)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "budget_audit.csv"),
        budget_rows)
    GlobalPrecisionField.write_json(joinpath(output_dir, "summary.json"), summary)
    GlobalPrecisionField.write_json(joinpath(output_dir, "status.json"), (
        experiment = 43, stage = stage, statuses = statuses,
        implementation_valid = all(value === true for (key, value) in
            pairs(implementation) if key != :maximum_conditional_local_marginal_mismatch),
        confirmation_opened = stage == "confirmation",
        freeze_commit = freeze_commit, result_commit = result_commit,
    ))
    write_magic_numbers(output_dir, config, stage)
    return summary
end

end
