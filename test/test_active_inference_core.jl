"""
    ActiveInferenceCore Tests
"""

using Test

include("../src/active_inference/ActiveInferenceCore.jl")
using .ActiveInferenceCore
include("../src/model.jl")

@testset "ActiveInferenceCore Tests" begin

    @testset "Core Types" begin

        @testset "AIFSettings defaults valid" begin
            settings = AIFSettings()
            @test settings.gamma > 0
            @test settings.alpha > 0
            @test settings.eta > 0
            @test settings.fpi_max_iter >= 1
            @test settings.fpi_tol > 0
        end

        @testset "PolicySet construction" begin
            V = ones(Int, 2, 2, 2)
            V[:, 1, 1] .= 1
            V[:, 2, 1] .= 2
            E = [0.5, 0.5]

            ps = PolicySet(V, E)
            @test ps.n_policies == 2
            @test ps.horizon == 2
            @test sum(ps.E) ≈ 1.0
        end

        @testset "AIFModel construction" begin
            model = build_tmaze_model()
            @test model.Ng == 3
            @test model.T == 3

            # A matrices normalized
            for g in 1:model.Ng
                for idx in CartesianIndices(model.Ns)
                    @test sum(model.A[g][:, idx]) ≈ 1.0 atol=1e-10
                end
            end

            # D vectors normalized
            for f in 1:length(model.D)
                @test sum(model.D[f]) ≈ 1.0 atol=1e-10
            end
        end

        @testset "init_agent and reset_trial!" begin
            model = build_tmaze_model()
            agent = init_agent(model)

            @test length(agent.qs) == model.T
            @test length(agent.pD) == length(model.D)
            @test length(agent.pA) == model.Ng

            # Beliefs normalized
            Nf = length(model.Ns)
            for t in 1:model.T
                for f in 1:Nf
                    @test sum(agent.qs[t][f]) ≈ 1.0 atol=1e-10
                end
            end

            # Test reset
            agent.t = 3
            push!(agent.observations, [1, 1, 1])
            push!(agent.actions, [1, 1])

            reset_trial!(agent, model)
            @test agent.t == 1
            @test isempty(agent.observations)
            @test isempty(agent.actions)
        end
    end

    @testset "State Inference" begin

        @testset "infer_states! updates beliefs" begin
            model = build_tmaze_model()
            agent = init_agent(model)
            settings = AIFSettings()

            obs = [1, 1, 1]
            infer_states!(agent, model, obs, settings)

            @test length(agent.observations) == 1
            @test agent.observations[1] == obs

            Nf = length(model.Ns)
            for f in 1:Nf
                @test sum(agent.qs[1][f]) ≈ 1.0 atol=1e-10
                @test all(agent.qs[1][f] .>= 0)
            end
        end

        @testset "posterior normalization across timesteps" begin
            model = build_tmaze_model()
            agent = init_agent(model)
            settings = AIFSettings()
            Nf = length(model.Ns)

            for t in 1:model.T
                agent.t = t
                obs = [1, 1, 1]
                if t > 1
                    push!(agent.actions, ones(Int, Nf))
                end
                infer_states!(agent, model, obs, settings)

                for f in 1:Nf
                    @test sum(agent.qs[t][f]) ≈ 1.0 atol=1e-10
                    @test all(agent.qs[t][f] .>= 0)
                    @test all(isfinite.(agent.qs[t][f]))
                end
            end
        end
    end

    @testset "Expected Free Energy" begin

        @testset "calculate_efe returns finite values" begin
            model = build_tmaze_model()
            agent = init_agent(model)
            settings = AIFSettings()

            # Need to do state inference first
            agent.t = 1
            infer_states!(agent, model, [1,1,1], settings)

            for pi in 1:model.policies.n_policies
                efe = calculate_efe(agent, model, pi, settings)
                @test isfinite(efe)
            end
        end

        @testset "EFE prefers informative policies" begin
            model = build_tmaze_model()
            agent = init_agent(model)
            settings = AIFSettings()

            agent.t = 1
            infer_states!(agent, model, [1,1,1], settings)

            # All policies should have finite EFE
            efes = [calculate_efe(agent, model, pi, settings) 
                    for pi in 1:model.policies.n_policies]
            @test all(isfinite.(efes))
        end
    end

    @testset "Policy Inference" begin

        @testset "infer_policies! normalizes qpi" begin
            model = build_tmaze_model()
            agent = init_agent(model)
            settings = AIFSettings()

            agent.t = 1
            obs = [1, 1, 1]
            infer_states!(agent, model, obs, settings)
            infer_policies!(agent, model, settings)

            @test sum(agent.qpi) ≈ 1.0 atol=1e-10
            @test all(agent.qpi .>= 0)
            @test all(isfinite.(agent.qpi))
        end

        @testset "sample_action returns valid actions" begin
            model = build_tmaze_model()
            agent = init_agent(model)
            settings = AIFSettings()
            Nf = length(model.Ns)

            agent.t = 1
            obs = [1, 1, 1]
            infer_states!(agent, model, obs, settings)
            infer_policies!(agent, model, settings)

            action = sample_action(agent, model; alpha=settings.alpha)

            @test length(action) == Nf
            for f in 1:Nf
                @test 1 <= action[f] <= model.Na[f]
            end
        end

        @testset "high precision selects consistently" begin
            model = build_tmaze_model()
            agent = init_agent(model)
            settings = AIFSettings(gamma=1.0, alpha=100.0, eta=1.0)

            agent.t = 1
            obs = [1, 1, 1]
            infer_states!(agent, model, obs, settings)
            infer_policies!(agent, model, settings)

            actions = [sample_action(agent, model; alpha=100.0) for _ in 1:10]
            @test all(a == actions[1] for a in actions)
        end
    end

    @testset "Learning" begin

        @testset "update_pA increments counts" begin
            model = build_tmaze_model()
            agent = init_agent(model)
            settings = AIFSettings()

            agent.t = 1
            obs = [1, 1, 1]
            infer_states!(agent, model, obs, settings)

            initial_pA_sum = sum(sum(pa) for pa in agent.pA)
            update_learning!(agent, model, obs, settings; learn_A=[1], learn_B=Int[], learn_D=Int[])
            final_pA_sum = sum(sum(pa) for pa in agent.pA)

            @test final_pA_sum > initial_pA_sum
        end

        @testset "learning rate scales update" begin
            model = build_tmaze_model()

            # eta=0 -> no change
            agent_zero = init_agent(model)
            settings_zero = AIFSettings(gamma=1.0, alpha=4.0, eta=0.0)
            agent_zero.t = 1
            obs = [1, 1, 1]
            infer_states!(agent_zero, model, obs, settings_zero)
            initial = sum(sum(pa) for pa in agent_zero.pA)
            update_learning!(agent_zero, model, obs, settings_zero; learn_A=[1], learn_B=Int[], learn_D=Int[])
            @test sum(sum(pa) for pa in agent_zero.pA) ≈ initial atol=1e-10

            # eta=1 -> change
            agent_one = init_agent(model)
            settings_one = AIFSettings(gamma=1.0, alpha=4.0, eta=1.0)
            agent_one.t = 1
            infer_states!(agent_one, model, obs, settings_one)
            initial = sum(sum(pa) for pa in agent_one.pA)
            update_learning!(agent_one, model, obs, settings_one; learn_A=[1], learn_B=Int[], learn_D=Int[])
            @test sum(sum(pa) for pa in agent_one.pA) > initial
        end
    end

    @testset "T-Maze Regression" begin
        results = run_tmaze_test(n_trials=20, verbose=false)
        @test results.cue_check_rate >= 0.9
        @test results.reward_rate >= 0.9
        @test results.correct_rate >= 0.9
    end

    @testset "Spider Model Regression" begin
        @testset "Safe spider" begin
            p_safe = run_spider_aif_therapy(n_trials=100, spider_dangerous=false)
            @test p_safe[1] < 0.2
            @test p_safe[end] > 0.5
            @test p_safe[end] > p_safe[1]
        end

        @testset "Dangerous spider" begin
            p_safe = run_spider_aif_therapy(n_trials=100, spider_dangerous=true)
            @test p_safe[1] < 0.2
            @test p_safe[end] < 0.1
            @test p_safe[end] < p_safe[1]
        end
    end

    @testset "Edge Cases" begin
        @testset "no NaN or Inf" begin
            model = build_tmaze_model()
            agent = init_agent(model)
            settings = AIFSettings()
            Nf = length(model.Ns)

            for _ in 1:5
                env = TMazeEnvironment(reward_location=rand(1:2))
                run_trial!(agent, model, env, settings)

                for t in 1:model.T
                    for f in 1:Nf
                        @test !any(isnan.(agent.qs[t][f]))
                        @test !any(isinf.(agent.qs[t][f]))
                    end
                end
                @test !any(isnan.(agent.qpi))
                @test !any(isinf.(agent.qpi))
            end
        end
    end

    @testset "Utilities" begin
        @testset "softmax" begin
            s = softmax([1.0, 2.0, 3.0])
            @test sum(s) ≈ 1.0
            @test all(s .> 0)
            @test s[3] > s[2] > s[1]
        end

        @testset "entropy" begin
            uniform = [0.25, 0.25, 0.25, 0.25]
            peaked = [0.97, 0.01, 0.01, 0.01]
            @test entropy(uniform) > entropy(peaked)
        end

        @testset "sample_categorical" begin
            probs = [0.1, 0.2, 0.3, 0.4]
            for _ in 1:100
                idx = sample_categorical(probs)
                @test 1 <= idx <= 4
            end
        end
    end

end

include("test_concepts_model.jl")

println("\nActiveInferenceCore tests completed!")
