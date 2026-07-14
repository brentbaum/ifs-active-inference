using Test
using Pkg
using LinearAlgebra

Pkg.activate(joinpath(@__DIR__, ".."))
include(joinpath(@__DIR__, "..", "src", "ContinuousSim6a.jl"))
include(joinpath(@__DIR__, "..", "src", "T48Robustness.jl"))
include(joinpath(@__DIR__, "..", "src", "GlobalPrecisionField.jl"))
include(joinpath(@__DIR__, "..", "src", "HierarchicalEpistemicDepth.jl"))
include(joinpath(@__DIR__, "..", "src", "LiteratureTournament.jl"))
include(joinpath(@__DIR__, "..", "src", "BeautifulLoopHierarchy.jl"))
include(joinpath(@__DIR__, "..", "src", "TemporalHyperModel.jl"))
include(joinpath(@__DIR__, "..", "src", "BayesianBinding.jl"))
include(joinpath(@__DIR__, "..", "src", "EpistemicAgency.jl"))
include(joinpath(@__DIR__, "..", "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(@__DIR__, "..", "src", "CompetitiveBinding.jl"))
include(joinpath(@__DIR__, "..", "src", "LearnedPrecisionStructure.jl"))
include(joinpath(@__DIR__, "..", "src", "ConfirmatoryBeautifulLoop.jl"))
include(joinpath(@__DIR__, "..", "src", "IdentifiablePrecisionStructure.jl"))
include(joinpath(@__DIR__, "..", "src", "IdentifiableGlobality.jl"))
include(joinpath(@__DIR__, "..", "src", "UnifiedRelationalAgent.jl"))
include(joinpath(@__DIR__, "..", "src", "ConfirmUnifiedRelationalAgent.jl"))
include(joinpath(@__DIR__, "..", "src", "MatchedMarginalRelationAblation.jl"))
include(joinpath(@__DIR__, "..", "src", "ConfirmRelationalActionInteraction.jl"))

using .T48Robustness
using .GlobalPrecisionField
using .HierarchicalEpistemicDepth
using .LiteratureTournament
using .BeautifulLoopHierarchy
using .TemporalHyperModel
using .BayesianBinding
using .EpistemicAgency
using .UnifiedBeautifulLoop
using .CompetitiveBinding
using .LearnedPrecisionStructure
using .ConfirmatoryBeautifulLoop
using .IdentifiablePrecisionStructure
using .IdentifiableGlobality
using .UnifiedRelationalAgent
using .ConfirmUnifiedRelationalAgent
using .MatchedMarginalRelationAblation
using .ConfirmRelationalActionInteraction

const CONFIG_PATH = joinpath(@__DIR__, "..", "configs", "t48-pilot.yaml")

@testset "T4.8 preregistered geometry" begin
    cfg = load_t48_config(CONFIG_PATH)
    @test length(cfg.seeds) == 10
    @test mapped_depth_component(0.0, "theory") == 1.0
    @test mapped_depth_component(1.0, "theory") == 0.0
    @test mapped_depth_component(0.0, "reversed") == 0.0
    @test mapped_depth_component(1.0, "reversed") == 1.0
    @test mapped_depth_component(0.1, "flat") == mapped_depth_component(0.9, "flat")
    @test mapped_depth_component(0.0, "nonmonotone") == mapped_depth_component(1.0, "nonmonotone")
    @test make_params(cfg).self_support ≈ 0.20
end

@testset "literature tournament defines twenty distinct mechanisms" begin
    variants = literature_variants()
    @test length(variants) == 20
    @test length(unique(spec.mechanism for spec in variants)) == 20
    @test all(spec.complexity >= 0 for spec in variants)
end

@testset "literature tournament retains the simplest earned mechanism" begin
    mktempdir() do output_dir
        result = run_tournament(output_dir)
        @test length(result.rows) == 24
        @test result.best_single.name == "context_redescription"
        @test result.best_combination.score > result.best_single.score
        @test result.best_combination.score < result.best_single.score + 0.02
        @test !result.combination_earned
        @test isfile(joinpath(output_dir, "ranked_experiments.csv"))
        @test isfile(joinpath(output_dir, "summary.json"))
    end
end

@testset "global precision field keeps depth and dominance orthogonal" begin
    result = run_regime_probe()
    @test result.metrics.high_dominance_high_depth == 1.0
    @test result.metrics.low_dominance_low_depth == 1.0
    @test result.metrics.blended_signature == 1.0
    @test result.metrics.self_led_signature == 1.0
end

@testset "epistemic depth is a readout, not a precision input" begin
    result = infer_precision_field(zeros(length(CHANNELS)), [1.2, 0.8, 1.0, 1.1, 0.9])
    @test length(result.broadcast_precision) == length(CHANNELS)
    @test result.depth_index == clamp(result.posterior_confidence * result.calibration * result.breadth * result.global_integration, 0.0, 1.0)
    @test result.part_dominance == result.broadcast_precision[1] / sum(result.broadcast_precision[1:2])
end

@testset "witnessing requires activation and an open precision field" begin
    result = run_witnessing_probe()
    @test result.metrics.witnessing_beats_regulation == 1.0
    @test result.metrics.witnessing_beats_contact == 1.0
    @test result.metrics.informational_revision_when_open == 1.0
    @test result.metrics.learned_unscaffolded_field == 1.0
    @test result.metrics.global_sharing_required == 1.0
    @test result.metrics.calibrated_broadcast_required == 1.0
end

@testset "hierarchical epistemic depth uses endogenous layer errors" begin
    config = FormalConfig(seeds = [8201, 8202], samples = 60, iterations = 12)
    episode = generate_episode(8201, [0.8, 0.8, 0.8]; config = config)
    result = infer_episode(episode; global_model = true, config = config)
    @test length(result.phi) == 3
    @test length(result.trace) == config.iterations
    @test last(result.trace).residual_1 > 0
    @test isfinite(last(result.trace).free_energy_proxy)
end

@testset "Beautiful Loop hierarchy exposes local and joint variational energies" begin
    config = LoopConfig(seeds = [8301], samples = 36, training_samples = 18,
        iterations = 10, hyper_newton_steps = 10)
    episode = generate_hierarchy(8301, [0.8, 0.7, 0.9]; samples = 36, config = config)
    global_result = infer_hierarchy(episode; global_model = true, config = config)
    local_result = infer_hierarchy(episode; global_model = false, config = config)
    @test size(global_result.state_means) == size(episode.latent)
    @test length(global_result.phi) == 3
    @test all(last(global_result.trace)[Symbol("residual_$layer")] > 0 for layer in 1:3)
    @test all(isfinite(last(global_result.trace)[field]) for field in
        (:local_free_energy_1, :local_free_energy_2, :local_free_energy_3,
            :hyper_free_energy, :joint_free_energy))
    @test all(diff(getfield.(global_result.trace, :joint_free_energy)) .<= 1.0e-8)
    global_marginal = diag(global_result.map_phi * global_result.prior_covariance * global_result.map_phi')
    local_marginal = diag(local_result.map_phi * local_result.prior_covariance * local_result.map_phi')
    @test global_marginal ≈ local_marginal
end

@testset "temporal hyper-model updates coupling from endogenous evidence" begin
    config = TemporalConfig(seeds = [8401], steps = 30, first_switch = 11,
        second_switch = 21, evidence_samples = 12)
    rows = run_temporal_seed(8401; config = config)
    @test length(rows) == 30
    @test Set(row.regime for row in rows) == Set(["coordinated_1", "independent", "coordinated_2"])
    @test all(0 < row.global_weight < 1 for row in rows)
    @test all(isfinite(row.adaptive_rmse) for row in rows)
    @test any(abs(row.global_log_evidence - row.local_log_evidence) > 1.0e-6 for row in rows)
end

@testset "Bayesian binding infers a global cause from local competitors" begin
    result = infer_bound_cause([0.4, 0.5, 0.3], fill(0.45, 3), fill(0.1, 3))
    @test 0 <= result.probability_positive <= 1
    @test result.decision == 1
    @test length(result.local_probabilities) == 3
    @test all(0 <= probability <= 1 for probability in result.local_probabilities)
end

@testset "epistemic agency values informative samples" begin
    @test expected_information_gain(0.5, 0.90) > expected_information_gain(0.5, 0.60)
    @test expected_information_gain(0.9, 0.90) < expected_information_gain(0.5, 0.90)
    config = AgencyConfig(seeds = [8601], episodes = 20, switch_episode = 11)
    rows = run_agency_seed(8601; config = config)
    @test length(rows) == 60
    @test Set(row.strategy for row in rows) == Set(["efe", "random", "fixed"])
    @test all(0 <= row.samples <= 3 for row in rows)
end

@testset "unified Beautiful Loop couples hierarchy, precision, binding, and policy" begin
    config = UnifiedConfig(seeds = [8701], episodes = 12, training_episodes = 5,
        switch_episode = 8, structural_break_episode = 10,
        inference_iterations = 6, hyper_newton_steps = 5)
    episode = generate_unified_episode(8701, 1; config = config)
    global_model = UnifiedBeautifulLoop.PrecisionForecaster(true, config)
    local_model = UnifiedBeautifulLoop.PrecisionForecaster(false, config)
    prior_mean, prior_covariance = UnifiedBeautifulLoop.forecast(
        global_model, episode.context, config)
    _, local_covariance = UnifiedBeautifulLoop.forecast(
        local_model, episode.context, config)
    @test size(episode.states) == (3, 3, config.samples_per_action)
    @test diag(prior_covariance) ≈ diag(local_covariance)
    bound = infer_unified_episode(episode.observations, [1, 2, 3],
        prior_mean, prior_covariance; binding = true, config = config)
    unbound = infer_unified_episode(episode.observations, [1, 2, 3],
        prior_mean, prior_covariance; binding = false, config = config)
    unbound_soft = infer_unified_episode(episode.observations, [1, 2, 3],
        prior_mean, prior_covariance; binding = false, local_aggregation = :soft_mean,
        config = config)
    @test length(bound.posterior_phi) == 9
    @test all(bound.residuals .> 0)
    @test all(diff(getfield.(bound.trace, :joint_free_energy)) .<= 1.0e-8)
    @test all(isfinite(row.hyper_free_energy) for row in bound.trace)
    @test abs(bound.probability_positive - unbound.probability_positive) > 1.0e-8
    @test unbound.probability_positive ≈
        UnifiedBeautifulLoop.aggregate_local_probabilities(
            unbound.local_probabilities, :log_odds)
    @test unbound_soft.probability_positive ≈
        sum(unbound_soft.local_probabilities) / length(unbound_soft.local_probabilities)
    policy = UnifiedBeautifulLoop.policy_posterior(bound.probability_positive,
        bound.posterior_phi, bound.posterior_covariance, [1, 2, 3], 0, config)
    @test sum(policy.probabilities) ≈ 1.0
end

@testset "competitive binding requires a joint relational factor" begin
    config = CompetitiveConfig(seeds = [8801], episodes = 12,
        training_episodes = 5, switch_episode = 8,
        inference_iterations = 4, hyper_newton_steps = 3)
    episode = generate_competitive_episode(8801, 1; config = config)
    unified = CompetitiveBinding.unified_config(config)
    model = UnifiedBeautifulLoop.PrecisionForecaster(true, unified)
    prior_mean, prior_covariance = UnifiedBeautifulLoop.forecast(
        model, episode.context, unified)
    relational = infer_competitive_episode(episode.observations, [1, 2, 3],
        prior_mean, prior_covariance; mode = :relational, config = config)
    independent = infer_competitive_episode(episode.observations, [1, 2, 3],
        prior_mean, prior_covariance; mode = :independent, config = config)
    @test prod(episode.local_causes) ==
        (episode.relation_violation ? -episode.global_cause : episode.global_cause)
    @test independent.probability_positive ≈ 0.5
    @test abs(relational.probability_positive - 0.5) > 1.0e-6
    @test all(diff(getfield.(relational.trace, :joint_free_energy)) .<= 1.0e-8)
end

@testset "precision structure is learned without a supplied loading basis" begin
    config = StructureConfig(seeds = [8901], episodes = 12,
        training_episodes = 5, switch_episode = 8,
        inference_iterations = 3, hyper_newton_steps = 2)
    loading = random_channel_loading(8901)
    @test abs(sum(loading) / length(loading)) <= 1.0e-12
    @test sqrt(sum(abs2, loading) / length(loading)) ≈ 1.30
    deviations = LearnedPrecisionStructure.random_local_deviations(8901, 0.5)
    @test length(deviations) == 9
    for channel in 1:3
        rows = [UnifiedBeautifulLoop.component_index(layer, channel) for layer in 1:3]
        @test abs(sum(deviations[rows])) <= 1.0e-12
    end
    global_model = LearnedGlobalForecaster(config)
    adaptive_model = AdaptiveLocalForecaster(config)
    global_mean, global_covariance = LearnedPrecisionStructure.forecast(
        global_model, 1.4, config)
    local_mean, local_covariance = LearnedPrecisionStructure.forecast(
        adaptive_model, 1.4, config)
    @test length(global_mean) == 9
    @test length(local_mean) == 9
    @test size(global_covariance) == (9, 9)
    @test size(local_covariance) == (9, 9)
end

@testset "layer monitoring identifies local precision structure" begin
    config = IdentifiableConfig(seeds = [11001], episodes = 12,
        training_episodes = 5, switch_episode = 8,
        inference_iterations = 3, hyper_newton_steps = 2,
        local_deviation_sd = 1.0)
    structure = IdentifiablePrecisionStructure.structure_config(config)
    loading = random_channel_loading(11001)
    deviations = LearnedPrecisionStructure.random_local_deviations(11001, 1.0)
    episode = generate_monitored_episode(11001, 1, loading, deviations;
        config = config)
    @test size(episode.monitored_observations) == size(episode.states)
    model = LearnedGlobalForecaster(structure)
    prior_mean, prior_covariance = LearnedPrecisionStructure.forecast(
        model, episode.context, structure)
    fit = infer_monitored_episode(episode.monitored_observations, [1, 2, 3],
        prior_mean, prior_covariance; config = config)
    @test length(fit.posterior_phi) == 9
    @test all(fit.residuals .> 0)
    @test all(diff(getfield.(fit.trace, :joint_free_energy)) .<= 1.0e-8)
end

@testset "identifiable globality includes a truly independent control" begin
    config = IdentifiableConfig(seeds = [11901], episodes = 12,
        training_episodes = 5, switch_episode = 8,
        inference_iterations = 3, hyper_newton_steps = 2)
    rows, snapshots = run_globality_seed(11901; config = config)
    @test Set(row.agent for row in rows) ==
        Set(["compact_global", "nested_global", "independent_local"])
    @test length(rows) == 3config.episodes
    @test Set(keys(snapshots)) ==
        Set(["compact_global", "nested_global", "independent_local"])
    @test all(values(IdentifiableGlobality.structural_checks(config)))
end

@testset "soft relational agent combines joint binding and action" begin
    config = RelationalAgentConfig(seeds = [12901], episodes = 12,
        training_episodes = 5, switch_episode = 8,
        inference_iterations = 3, hyper_newton_steps = 2)
    @test local_mutual_information(config) > 0
    episode = generate_relational_episode(12901, 1; config = config)
    @test size(episode.states) == (3, 3, config.packet_samples)
    rows = run_relational_agent_seed(12901; config = config)
    @test Set(row.agent for row in rows) == Set([
        "full", "factorized_replay", "random", "precision_blind"])
    @test all(row.sample_packets == config.action_budget for row in rows)
    for episode in 1:config.episodes
        full = only(filter(row -> row.episode == episode && row.agent == "full", rows))
        replay = only(filter(row -> row.episode == episode &&
            row.agent == "factorized_replay", rows))
        @test (full.first_action, full.second_action) ==
            (replay.first_action, replay.second_action)
    end
    @test all(values(UnifiedRelationalAgent.implementation_checks(config)))
end

@testset "factorized projection removes only joint scene structure" begin
    config = RelationalAgentConfig(seeds = [12902], episodes = 12,
        training_episodes = 5, switch_episode = 8,
        inference_iterations = 3, hyper_newton_steps = 2,
        violation_rate = 0.0)
    @test factorized_projection_error(config) <= 1.0e-12
    rows = run_relational_agent_seed(12902; config = config,
        scene_mode = :factorized, model_mode = :factorized)
    metrics = UnifiedRelationalAgent.seed_metrics(rows)
    @test metrics.full_accuracy == metrics.factorized_accuracy
    @test metrics.replay_action_match_rate == 1.0
    @test metrics.full_mean_packets == metrics.random_mean_packets
end

@testset "paired interaction intervals retain the frozen twenty-seed unit" begin
    interval = paired_t_interval(collect(1.0:20.0))
    @test interval.mean == 10.5
    @test interval.lower < interval.mean < interval.upper
    @test_throws ArgumentError paired_t_interval([1.0, 2.0])
end

@testset "autonomous reflected pilot path" begin
    cfg = load_t48_config(CONFIG_PATH)
    trace = driven_trace(first(cfg.seeds), "theory", cfg.pilot_observation_noise_sd, cfg)
    @test length(trace) == cfg.latent_trials
    @test minimum(row.true_depth for row in trace) <= 0.25
    first_low = findfirst(row -> row.true_depth <= 0.25, trace)
    @test any(row.true_depth >= 0.70 for row in trace[(first_low + 1):end])
    result = collapse_persistence_signature(trace, cfg)
    @test result.structurally_evaluable == 1.0
end

@testset "small bifurcation output shape" begin
    base = load_t48_config(CONFIG_PATH)
    cfg = T48Config(
        seeds = base.seeds,
        beta_grid = [base.default_beta],
        gamma_grid = [base.default_gamma],
        safety_prior_mass_grid = [base.default_safety_prior_mass],
        basin_initial_grid_size = 3,
        basin_steps = 10,
    )
    result = bifurcation_map(cfg)
    @test length(result.rows) == 1
    @test result.metrics.total_grid_cells == 1
end
