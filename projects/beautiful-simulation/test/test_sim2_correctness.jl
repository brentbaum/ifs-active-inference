best_binary_state_accuracy(posteriors::Matrix{Float64}, truth::Vector{Int}) =
    max(state_accuracy(posteriors, truth), state_accuracy(posteriors, 3 .- truth))

@testset "Simulation 2 Correctness" begin
    config = Sim2Config(seeds = [11], n_episodes = 2, T = 60)
    dataset = generate_sim2_dataset(default_rng(11), config)

    @testset "component matrices are valid" begin
        hier = build_sim2_hier_fixed_components(config)
        local_model = build_sim2_local_branch_components(config)
        blt = build_sim2_blt_global_components(config)
        @test matrix_is_column_stochastic(hier.transition)
        @test matrix_is_column_stochastic(hier.B1)
        @test matrix_is_column_stochastic(hier.B2)
        @test matrix_is_column_stochastic(local_model.transition)
        @test matrix_is_column_stochastic(local_model.B1)
        @test matrix_is_column_stochastic(local_model.B2)
        @test matrix_is_column_stochastic(blt.transition)
        @test matrix_is_column_stochastic(blt.B1)
        @test matrix_is_column_stochastic(blt.B2)
    end

    @testset "unambiguous control is solved by all models" begin
        for (infer_fn, dims) in (
            (sim2_hier_fixed_infer, [2, 2, 2]),
            (sim2_local_branch_infer, [2, 2, 2, 2, 2]),
            (sim2_blt_global_infer, [2, 2, 2, 2])
        )
            inference = infer_fn(dataset.unambiguous, config)
            @test best_binary_state_accuracy(inference.g_posteriors, dataset.unambiguous.g) > 0.90
            @test all(abs.(sum(inference.g_posteriors, dims = 2) .- 1.0) .<= 1e-6)
        end
    end
end
