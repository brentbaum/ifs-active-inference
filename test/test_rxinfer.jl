"""
    test_rxinfer.jl - Unit tests for RxInfer.jl active inference implementation

Building up from basic components to the full spider phobia model.
"""

using Test
using RxInfer
using LinearAlgebra
using Random

# Include our module
using IFSActiveInference

# ============================================================================
# Helper functions
# ============================================================================

"""Convert integer to one-hot vector"""
function one_hot(idx::Int, n::Int)
    v = zeros(n)
    v[idx] = 1.0
    return v
end

# ============================================================================
# Model definitions (outside testsets to avoid scoping issues with @model macro)
# ============================================================================

# 1. Simple coin flip model
@model function coin_model(y)
    θ ~ Beta(1.0, 1.0)
    y ~ Bernoulli(θ)
end

# 2. Simple categorical model with one-hot observation
@model function categorical_model_onehot(y, n)
    p ~ Dirichlet(ones(n))
    y ~ Categorical(p)
end

# 3. Simple HMM-like model using Transition node
@model function simple_hmm_v2(y, A, B, prior_state)
    s ~ Categorical(prior_state)
    s_next ~ Transition(s, B)
    y ~ Transition(s_next, A)
end

# 4. Multi-timestep HMM
@model function multi_step_hmm_v2(y, A, B, prior_state, T)
    s = randomvar(T)
    s[1] ~ Categorical(prior_state)
    for t in 2:T
        s[t] ~ Transition(s[t-1], B)
    end
    for t in 1:T
        y[t] ~ Transition(s[t], A)
    end
end

# 5. Learning observation model with known states
@model function learning_obs_model_v2(y, s_onehot, a_prior, T)
    A ~ MatrixDirichlet(a_prior)
    for t in 1:T
        y[t] ~ Transition(s_onehot[t], A)
    end
end

# 6. Learning initial state prior
@model function prior_learning_model_v2(s_onehot, d_prior, T)
    D ~ Dirichlet(d_prior)
    for t in 1:T
        s_onehot[t] ~ Categorical(D)
    end
end

# ============================================================================
# Tests
# ============================================================================

@testset "RxInfer Active Inference Tests" begin

    @testset "1. Basic RxInfer Setup" begin
        @testset "1.1 RxInfer is available" begin
            @test @isdefined(RxInfer)
        end

        @testset "1.2 Can create basic Beta-Bernoulli model" begin
            result = infer(
                model = coin_model(),
                data = (y = 1,),
                iterations = 5
            )

            @test haskey(result.posteriors, :θ)
            # Returns array of iterations
            posterior_history = result.posteriors[:θ]
            @test length(posterior_history) == 5
            final_posterior = last(posterior_history)
            @test final_posterior isa Beta
        end

        @testset "1.3 Can use Categorical with one-hot" begin
            # Use one-hot observation
            obs_onehot = one_hot(2, 3)

            result = infer(
                model = categorical_model_onehot(n=3),
                data = (y = obs_onehot,),
                iterations = 5
            )

            @test haskey(result.posteriors, :p)
            final_p = last(result.posteriors[:p])
            @test final_p isa Dirichlet
            p_mean = mean(final_p)
            @test p_mean[2] > p_mean[1]  # Learned from observation
        end
    end

    @testset "2. Discrete State Space Model" begin
        @testset "2.1 Simple HMM-like model with Transition" begin
            # Hidden Markov Model with 2 states, 2 observations
            B = [0.9 0.1; 0.1 0.9]  # Transition matrix
            A = [0.8 0.2; 0.2 0.8]  # Observation matrix
            prior = [0.5, 0.5]

            obs_onehot = one_hot(1, 2)  # Observed state 1

            result = infer(
                model = simple_hmm_v2(A=A, B=B, prior_state=prior),
                data = (y = obs_onehot,),
                iterations = 10
            )

            @test haskey(result.posteriors, :s_next)
            posterior = last(result.posteriors[:s_next])
            probs = probvec(posterior)
            @test sum(probs) ≈ 1.0
            # Observation of state 1 should bias posterior toward state 1
            @test probs[1] > 0.5
        end

        @testset "2.2 Multi-timestep inference" begin
            B = [0.9 0.1; 0.1 0.9]
            A = [0.8 0.2; 0.2 0.8]
            T = 3
            # Observations as one-hot vectors
            observations = [one_hot(1, 2), one_hot(1, 2), one_hot(2, 2)]
            prior = [0.5, 0.5]

            result = infer(
                model = multi_step_hmm_v2(A=A, B=B, prior_state=prior, T=T),
                data = (y = observations,),
                iterations = 10
            )

            @test haskey(result.posteriors, :s)
            @test length(last(result.posteriors[:s])) == T
        end
    end

    @testset "3. Dirichlet-Categorical Learning" begin
        @testset "3.1 Learning observation likelihoods" begin
            # Prior: uniform over 2x2
            a_prior = ones(2, 2) .+ 0.1
            T = 6

            # States as one-hot vectors
            states = [one_hot(1, 2), one_hot(1, 2), one_hot(1, 2),
                     one_hot(2, 2), one_hot(2, 2), one_hot(2, 2)]
            # Observations matching states
            observations = [one_hot(1, 2), one_hot(1, 2), one_hot(1, 2),
                          one_hot(2, 2), one_hot(2, 2), one_hot(2, 2)]

            result = infer(
                model = learning_obs_model_v2(a_prior=a_prior, T=T),
                data = (y = observations, s_onehot = states),
                iterations = 10
            )

            @test haskey(result.posteriors, :A)
            A_posterior = mean(last(result.posteriors[:A]))
            # Should learn diagonal-ish structure
            @test A_posterior[1, 1] > A_posterior[1, 2]
            @test A_posterior[2, 2] > A_posterior[2, 1]
        end

        @testset "3.2 Learning initial state priors" begin
            d_prior = [1.0, 1.0]  # Uniform prior
            T = 5

            # Data: mostly state 2 (as one-hot)
            states = [one_hot(2, 2), one_hot(2, 2), one_hot(2, 2),
                     one_hot(2, 2), one_hot(1, 2)]

            result = infer(
                model = prior_learning_model_v2(d_prior=d_prior, T=T),
                data = (s_onehot = states,),
                iterations = 10
            )

            @test haskey(result.posteriors, :D)
            D_posterior = mean(last(result.posteriors[:D]))
            # Should learn preference for state 2
            @test D_posterior[2] > D_posterior[1]
        end
    end

    @testset "4. Spider Phobia Model Components" begin
        @testset "4.1 Model parameter dimensions" begin
            params = ModelParams()
            model = build_model(params=params)

            @test length(model.Ns) == 3  # 3 state factors
            @test length(model.No) == 4  # 4 observation modalities
            @test model.Ns == [6, 2, 2]  # behavior, spider, danger
            @test model.No == [2, 2, 3, 6]  # visual, arousal, affect, behavior
        end

        @testset "4.2 A matrices are valid probabilities" begin
            params = ModelParams()
            model = build_model(params=params)

            for (g, A_g) in enumerate(model.A)
                for idx in CartesianIndices(size(A_g)[2:end])
                    col_sum = sum(A_g[:, idx])
                    @test col_sum ≈ 1.0 atol=1e-10
                end
            end
        end

        @testset "4.3 B matrices are valid probabilities" begin
            params = ModelParams()
            model = build_model(params=params)

            for (f, B_f) in enumerate(model.B)
                for a in 1:size(B_f, 3)
                    for s in 1:size(B_f, 2)
                        col_sum = sum(B_f[:, s, a])
                        @test col_sum ≈ 1.0 atol=1e-10
                    end
                end
            end
        end

        @testset "4.4 D priors are valid probabilities" begin
            params = ModelParams()
            model = build_model(params=params)

            for (f, D_f) in enumerate(model.D)
                @test sum(D_f) ≈ 1.0 atol=1e-10
                @test all(D_f .>= 0)
            end
        end
    end

    @testset "5. RxInfer Spider Model" begin
        @testset "5.1 Can build RxInfer matrices" begin
            if isdefined(IFSActiveInference, :build_rxinfer_matrices)
                params = ModelParams()
                matrices = IFSActiveInference.build_rxinfer_matrices(params=params)

                @test haskey(matrices, :A)
                @test haskey(matrices, :B)
                @test haskey(matrices, :D)
            else
                @test_skip "build_rxinfer_matrices not yet implemented"
            end
        end

        @testset "5.2 Can run RxInfer state inference" begin
            if isdefined(IFSActiveInference, :run_rxinfer_state_inference)
                params = ModelParams()
                result = IFSActiveInference.run_rxinfer_state_inference(
                    observation=[1, 1, 1, 1],
                    params=params
                )

                @test haskey(result, :qs)
            else
                @test_skip "run_rxinfer_state_inference not yet implemented"
            end
        end

        @testset "5.3 Can run RxInfer simulation" begin
            if isdefined(IFSActiveInference, :run_rxinfer_exposure_therapy)
                params = ModelParams(N=10, T=4)
                result = IFSActiveInference.run_rxinfer_exposure_therapy(
                    n_trials=10,
                    spider_dangerous=false,
                    params=params
                )

                @test haskey(result, :d_evolution)
                @test length(result.d_evolution) == 10
            else
                @test_skip "run_rxinfer_exposure_therapy not yet implemented"
            end
        end
    end

end

println("\nRxInfer tests completed!")
