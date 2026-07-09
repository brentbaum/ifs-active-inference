using Test
using JSON3

using EmergenceSuite
using EmergenceSuite.BMR
using EmergenceSuite.Config
using EmergenceSuite.Criteria

const SUITE_ROOT = normpath(joinpath(@__DIR__, ".."))
const DUMMY_CONFIG = joinpath(SUITE_ROOT, "configs", "dummy.yaml")

function tmp_run_dir(name)
    path = mktempdir(; prefix = "emergence-suite-$name-")
    return path
end

@testset "config load" begin
    config = load_config(DUMMY_CONFIG)
    @test config.experiment == "dummy"
    @test config.seeds == [11, 23, 37]
    @test config.model_params["trials"] == 120
    @test isabspath(config.output_dir)
    @test endswith(config.criteria_path, joinpath("configs", "criteria.yaml"))
end

@testset "seed reproducibility" begin
    config = load_config(DUMMY_CONFIG)
    out1 = tmp_run_dir("repro-1")
    out2 = tmp_run_dir("repro-2")
    run_config(config; config_path = DUMMY_CONFIG, output_dir = out1)
    run_config(config; config_path = DUMMY_CONFIG, output_dir = out2)
    summary1 = read(joinpath(out1, "summary.json"), String)
    summary2 = read(joinpath(out2, "summary.json"), String)
    @test summary1 == summary2
end

@testset "contract completeness" begin
    config = load_config(DUMMY_CONFIG)
    out = tmp_run_dir("contract")
    run_config(config; config_path = DUMMY_CONFIG, output_dir = out)
    @test isfile(joinpath(out, "summary.json"))
    @test isfile(joinpath(out, "status.json"))
    @test isfile(joinpath(out, "metadata.json"))
    @test isfile(joinpath(out, "per_seed_metrics.csv"))
    @test isfile(joinpath(out, "posterior_traces.csv"))
    @test isfile(joinpath(out, "criteria-results.json"))
    @test isfile(joinpath(out, "figures", "dummy_trace.svg"))

    status = JSON3.read(read(joinpath(out, "status.json"), String))
    @test status.implementation_passed == true
    @test status.theory_result in ("support", "weak_support")
end

@testset "BMR D2 demo values" begin
    b_full = reshape([2.0, 12.0], 2, 1)
    b_reduced = reshape([7.0, 7.0], 2, 1)
    late_counts = reshape([36.0, 4.0], 2, 1)
    early_counts = reshape([4.0, 36.0], 2, 1)

    late_expected = Dict(
        0.0 => 0.0,
        0.01 => 0.465681993749131,
        0.1 => 3.0407349858244537,
        0.5 => 6.557802243314928,
        1.0 => 7.84108968238834,
        5.0 => 9.44299264246909,
        20.0 => 9.845622710243017
    )
    early_expected = Dict(
        0.0 => 0.0,
        0.01 => -0.1419637422091906,
        0.1 => -1.0827430204300974,
        0.5 => -2.6848817759980754,
        1.0 => -3.315660713684796,
        5.0 => -4.104622770997413,
        20.0 => -4.3002849441039395
    )

    for (E, expected) in late_expected
        @test reflexive_prior_swap_delta(b_full, b_reduced, late_counts, E) ≈ expected atol = 1e-6
    end
    for (E, expected) in early_expected
        @test reflexive_prior_swap_delta(b_full, b_reduced, early_counts, E) ≈ expected atol = 1e-6
    end
end

@testset "criteria evaluator labels" begin
    fixture_dir = joinpath(@__DIR__, "fixtures", "criteria")
    results = evaluate_criteria(joinpath(fixture_dir, "criteria.yaml"), joinpath(fixture_dir, "summary.json"))
    labels = Dict(row.id => row.label for row in results.results)
    @test labels["strong"] == "support"
    @test labels["weak"] == "weak_support"
    @test labels["none"] == "null"
    @test labels["opposite"] == "falsified"
end
