@testset "Simulation 3 Correctness" begin
    config = Sim3Config(seeds = [11], T = 80, vmp_iters = 5, alpha_local_values = [0.5, 2.0], alpha_hyper_values = [0.5, 2.0])
    sequence = generate_sim3_sequence(default_rng(11), config; alpha_local = 4.0, alpha_hyper = 4.0, input_scale = 1.0, biased_priors = false)

    @testset "generator produces finite trajectories" begin
        @test all(isfinite, sequence.h)
        @test all(isfinite, sequence.z)
        @test all(isfinite, sequence.x)
        @test all(isfinite, sequence.y)
    end

    @testset "easy recovery and free energy sanity" begin
        kalman = sim3_kalman_fixed_infer(sequence, config)
        hgf2 = sim3_hgf2_infer(sequence, config)
        blt = sim3_blt_hgf_infer(sequence, config)

        @test rmse(blt.x_mean, sequence.x) < 0.8
        @test isfinite(first(blt.free_energy)) && isfinite(last(blt.free_energy))
        @test isfinite(first(hgf2.free_energy)) && isfinite(last(hgf2.free_energy))
        @test isfinite(first(kalman.free_energy)) && isfinite(last(kalman.free_energy))
        @test last(blt.free_energy) <= first(blt.free_energy) + 0.05
        @test last(hgf2.free_energy) <= first(hgf2.free_energy) + 0.05
        @test last(kalman.free_energy) <= first(kalman.free_energy) + 1e-9
        @test all(blt.x_var .> 0.0)
        @test all(hgf2.x_var .> 0.0)
    end
end
