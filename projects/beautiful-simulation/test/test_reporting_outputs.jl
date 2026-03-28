@testset "Reporting Outputs" begin
    sim1_config = joinpath(@__DIR__, "..", "configs", "sim1_smoke.yaml")
    sim2_config = joinpath(@__DIR__, "..", "configs", "sim2_smoke.yaml")
    sim3_config = joinpath(@__DIR__, "..", "configs", "sim3_smoke.yaml")

    mktempdir() do tmpdir
        sim1_dir = joinpath(tmpdir, "sim1")
        sim2_dir = joinpath(tmpdir, "sim2")
        sim3_dir = joinpath(tmpdir, "sim3")

        sim1 = run_sim1(config_path = sim1_config, output_dir = sim1_dir)
        sim2 = run_sim2(config_path = sim2_config, output_dir = sim2_dir)
        sim3 = run_sim3(config_path = sim3_config, output_dir = sim3_dir)

        @test isfile(joinpath(sim1_dir, "summary.json"))
        @test isfile(joinpath(sim1_dir, "per_seed_metrics_filtered.csv"))
        @test isfile(joinpath(sim1_dir, "per_seed_metrics_smoothed.csv"))
        @test isfile(joinpath(sim1_dir, "metric_deltas.csv"))
        @test isfile(joinpath(sim1_dir, "metadata.json"))
        @test sim1.summary.metric_source_for_theory == "filtered"
        @test haskey(sim1.summary.filtered_summary_by_model, "BLTGlobal")
        @test haskey(sim1.summary.smoothed_summary_by_model, "BLTGlobal")

        @test isfile(joinpath(sim2_dir, "summary.json"))
        @test isfile(joinpath(sim2_dir, "per_seed_metrics_filtered.csv"))
        @test isfile(joinpath(sim2_dir, "per_seed_metrics_smoothed.csv"))
        @test isfile(joinpath(sim2_dir, "metric_deltas.csv"))
        @test isfile(joinpath(sim2_dir, "metadata.json"))
        @test sim2.summary.metric_source_for_theory == "filtered"
        @test haskey(sim2.summary.filtered_summary_by_model, "BLTGlobal")
        @test haskey(sim2.summary.smoothed_summary_by_model, "BLTGlobal")

        @test isfile(joinpath(sim3_dir, "summary.json"))
        @test isfile(joinpath(sim3_dir, "metadata.json"))
        @test isfile(joinpath(sim3_dir, "heatmap_implied_local_precision.png"))
        @test isfile(joinpath(sim3_dir, "heatmap_posterior_content_precision.png"))
        @test sim3.summary.metric_definitions.phase_metric == "implied_local_precision"
        @test haskey(sim3.summary.scenario_definitions, "noetic")
    end
end
