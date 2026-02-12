using Test
using IFSActiveInference

@testset "IFSActiveInference Tests" begin

    @testset "Model Construction" begin
        params = ModelParams()
        @test params.T == 4
        @test params.CABi == 0.9
        @test params.Psafe == 0.1

        model = build_model(params=params)

        @test model.Ns == [6, 2, 2]
        @test model.No == [2, 2, 3, 6]
        @test model.Nf == 3
        @test model.Ng == 4

        # Check D dimensions
        @test length(model.D) == 3
        @test length(model.D[1]) == 6
        @test length(model.D[2]) == 2
        @test length(model.D[3]) == 2

        # Check A dimensions
        @test length(model.A) == 4
        @test size(model.A[1]) == (2, 6, 2, 2)
        @test size(model.A[2]) == (2, 6, 2, 2)
        @test size(model.A[3]) == (3, 6, 2, 2)
        @test size(model.A[4]) == (6, 6, 2, 2)

        # Check B dimensions
        @test length(model.B) == 3
        @test size(model.B[1]) == (6, 6, 2)
        @test size(model.B[2]) == (2, 2, 1)
        @test size(model.B[3]) == (2, 2, 1)

        # Check V (policies)
        @test size(model.V) == (3, 2, 3)

        # Check C (preferences)
        @test length(model.C) == 4
        @test size(model.C[1]) == (2, 4)
        @test model.C[3][3, 1] == -12  # Strong aversion to harm

        # Check E (policy prior)
        @test length(model.E) == 2
        @test all(model.E .== 1.0)
    end

    @testset "Agent Initialization" begin
        model = build_model()
        agent = init_agent(model)

        @test length(agent.qs) == 3
        @test length(agent.qpi) == 2
        @test length(agent.a) == 4
        @test length(agent.d) == 3
    end

    @testset "Softmax Functions" begin
        x = [1.0, 2.0, 3.0]

        # Standard softmax
        p = softmax_tau(x)
        @test isapprox(sum(p), 1.0, atol=1e-10)
        @test all(p .> 0)
        @test argmax(p) == 3

        # Temperature scaling
        p_hot = softmax_tau(x; tau=10.0)
        p_cold = softmax_tau(x; tau=0.1)

        # Hot temperature -> more uniform
        @test p_hot[3] - p_hot[1] < p[3] - p[1]
        # Cold temperature -> more peaked
        @test p_cold[3] - p_cold[1] > p[3] - p[1]
    end

    @testset "Single Trial" begin
        using Random
        Random.seed!(42)

        model = build_model()
        agent = init_agent(model)
        settings = SimulationSettings()

        true_state = [1, 2, 2]  # start, spider, safe
        result = run_trial(model, agent, true_state; settings=settings)

        @test length(result.observations) == model.T
        @test length(result.actions) == model.T - 1
        @test length(result.states) == model.T
        @test length(result.beliefs) == model.T + 1

        # All observations should be valid indices
        for obs in result.observations
            for (g, o) in enumerate(obs)
                @test 1 <= o <= model.No[g]
            end
        end
    end

    @testset "Short Simulation" begin
        using Random
        Random.seed!(42)

        model = build_model(params=ModelParams(N=10))
        settings = SimulationSettings(
            exposure_mode = true,
            eta = 1.0
        )

        results = run_exposure_therapy(model; n_trials=10, settings=settings)

        @test results.n_trials == 10
        @test results.approach_count + results.avoid_count == 10
        @test length(results.d_evolution) == 10
        @test length(results.a_evolution) == 10
    end

end

# Include RxInfer tests
include("test_rxinfer.jl")

println("\nAll tests passed!")
