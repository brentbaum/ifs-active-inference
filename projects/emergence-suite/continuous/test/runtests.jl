using Test
using Pkg

Pkg.activate(joinpath(@__DIR__, ".."))
include(joinpath(@__DIR__, "..", "src", "ContinuousSim6a.jl"))
include(joinpath(@__DIR__, "..", "src", "T48Robustness.jl"))

using .T48Robustness

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
