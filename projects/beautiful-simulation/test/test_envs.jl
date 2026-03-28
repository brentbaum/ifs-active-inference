@testset "Sensor Fusion Environment" begin
    @testset "make_emission produces column stochastic matrix" begin
        emission = make_emission(0.9)
        @test size(emission) == (4, 4)
        @test matrix_is_column_stochastic(emission)
    end

    @testset "sticky transition matrices are valid" begin
        A_s = make_sticky_matrix(4, 0.85, 0.05)
        A_phi = make_sticky_matrix(4, 0.94, 0.02)
        @test matrix_is_column_stochastic(A_s)
        @test matrix_is_column_stochastic(A_phi)
    end

    @testset "probe schedule is generated exactly" begin
        config = Sim1Config(n_probe_episodes = 1)
        episode = generate_sim1_episode(default_rng(11), config; probe_schedule = config.probe_schedule)
        @test episode.phi == config.probe_schedule
    end
end
