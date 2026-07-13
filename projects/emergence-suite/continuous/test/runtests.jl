using Test
using Pkg

Pkg.activate(joinpath(@__DIR__, ".."))
include(joinpath(@__DIR__, "..", "src", "ContinuousSim6a.jl"))
include(joinpath(@__DIR__, "..", "src", "T48Robustness.jl"))
include(joinpath(@__DIR__, "..", "src", "GlobalPrecisionField.jl"))
include(joinpath(@__DIR__, "..", "src", "HierarchicalEpistemicDepth.jl"))

using .T48Robustness
using .GlobalPrecisionField
using .HierarchicalEpistemicDepth

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
