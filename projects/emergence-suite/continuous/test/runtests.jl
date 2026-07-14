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

using .T48Robustness
using .GlobalPrecisionField
using .HierarchicalEpistemicDepth
using .LiteratureTournament
using .BeautifulLoopHierarchy
using .TemporalHyperModel
using .BayesianBinding

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
