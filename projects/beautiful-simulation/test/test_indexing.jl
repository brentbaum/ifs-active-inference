@testset "Indexing" begin
    @testset "flatten/unflatten round-trip" begin
        dims = [4, 4, 4]
        for idx in 1:prod(dims)
            state = unflatten_state(idx, dims)
            @test flatten_state(state, dims) == idx
        end
    end

    @testset "sim1 joint helpers are bijective" begin
        for s in 1:4, phi in 1:4
            idx = joint_index_s_phi(s, phi)
            @test inverse_joint_index_s_phi(idx) == (s, phi)
        end

        for s in 1:4, phi_v in 1:4, phi_a in 1:4
            idx = joint_index_s_phi_phi(s, phi_v, phi_a)
            @test inverse_joint_index_s_phi_phi(idx) == (s, phi_v, phi_a)
        end
    end
end
