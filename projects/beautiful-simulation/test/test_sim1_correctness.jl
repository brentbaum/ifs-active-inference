@testset "Simulation 1 Correctness" begin
    config = Sim1Config(seeds = [11], n_episodes = 1, n_probe_episodes = 1, T = 24, burn_in = 5, switch_window = 4)
    dataset = generate_sim1_dataset(default_rng(11), config)
    episode = dataset.natural[1]

    @testset "component matrices are valid" begin
        flat = build_sim1_flat_fixed_components(config)
        local_model = build_sim1_local_precision_components(config)
        blt = build_sim1_blt_global_components(config)

        @test matrix_is_column_stochastic(flat.transition)
        @test matrix_is_column_stochastic(flat.Bv)
        @test matrix_is_column_stochastic(flat.Ba)

        @test matrix_is_column_stochastic(local_model.transition)
        @test matrix_is_column_stochastic(local_model.Bv)
        @test matrix_is_column_stochastic(local_model.Ba)

        @test matrix_is_column_stochastic(blt.transition)
        @test matrix_is_column_stochastic(blt.Bv)
        @test matrix_is_column_stochastic(blt.Ba)
    end

    @testset "posterior normalization holds for all sim1 models" begin
        for infer_fn in (sim1_flat_fixed_infer, sim1_local_precision_infer, sim1_blt_global_infer)
            inference = infer_fn(episode, config)
            @test all(abs.(sum(inference.world_posteriors, dims = 2) .- 1.0) .<= 1e-6)
            if !isnothing(inference.phi_posteriors)
                @test all(abs.(sum(inference.phi_posteriors, dims = 2) .- 1.0) .<= 1e-6)
            end
            if !isnothing(inference.phi_v_posteriors)
                @test all(abs.(sum(inference.phi_v_posteriors, dims = 2) .- 1.0) .<= 1e-6)
                @test all(abs.(sum(inference.phi_a_posteriors, dims = 2) .- 1.0) .<= 1e-6)
            end
        end
    end

    @testset "degenerate BG equivalence sanity" begin
        probe = generate_sim1_episode(default_rng(23), config; probe_schedule = fill(BG, config.T))
        flat_bg = sim1_flat_fixed_infer(probe, config; context_override = BG)
        blt = sim1_blt_global_infer(probe, config)

        flat_acc = state_accuracy(flat_bg.world_posteriors, probe.s)
        blt_acc = state_accuracy(blt.world_posteriors, probe.s)
        @test abs(flat_acc - blt_acc) <= 0.1
        @test abs(
            negative_log_likelihood(flat_bg.log_evidence, config.T) -
            negative_log_likelihood(blt.log_evidence, config.T)
        ) <= 0.12
    end
end
