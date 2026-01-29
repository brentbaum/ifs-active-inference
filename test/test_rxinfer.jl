"""
    test_rxinfer.jl - Unit tests for RxInfer.jl active inference implementation

Building up from basic components to the full spider phobia model.
"""

using Test
using LinearAlgebra
using Random

# Include our module
using IFSActiveInference

# Conditionally import RxInfer
const RXINFER_TEST_AVAILABLE = try
    @eval using RxInfer
    true
catch
    false
end

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
# Model definitions (only if RxInfer is available)
# ============================================================================

if RXINFER_TEST_AVAILABLE

# 1. Simple coin flip model
RxInfer.@model function coin_model(y)
    θ ~ Beta(1.0, 1.0)
    y ~ Bernoulli(θ)
end

# 2. Simple categorical model with one-hot observation
RxInfer.@model function categorical_model_onehot(y, n)
    p ~ Dirichlet(ones(n))
    y ~ Categorical(p)
end

# 3. Simple HMM-like model using Transition node
RxInfer.@model function simple_hmm_v2(y, A, B, prior_state)
    s ~ Categorical(prior_state)
    s_next ~ Transition(s, B)
    y ~ Transition(s_next, A)
end

# 4. Multi-timestep HMM
RxInfer.@model function multi_step_hmm_v2(y, A, B, prior_state, T)
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
RxInfer.@model function learning_obs_model_v2(y, s_onehot, a_prior, T)
    A ~ MatrixDirichlet(a_prior)
    for t in 1:T
        y[t] ~ Transition(s_onehot[t], A)
    end
end

# 6. Learning initial state prior
RxInfer.@model function prior_learning_model_v2(s_onehot, d_prior, T)
    D ~ Dirichlet(d_prior)
    for t in 1:T
        s_onehot[t] ~ Categorical(D)
    end
end

end # if RXINFER_TEST_AVAILABLE

# ============================================================================
# Tests
# ============================================================================

@testset "RxInfer Active Inference Tests" begin

    @testset "1. Basic RxInfer Setup" begin
        @testset "1.1 RxInfer is available" begin
            @test RXINFER_TEST_AVAILABLE || @test_skip "RxInfer not installed"
        end

        if RXINFER_TEST_AVAILABLE
            @testset "1.2 Can create basic Beta-Bernoulli model" begin
                result = RxInfer.infer(
                    model = coin_model(),
                    data = (y = 1,),
                    iterations = 5
                )

                @test haskey(result.posteriors, :θ)
                posterior_history = result.posteriors[:θ]
                @test length(posterior_history) == 5
                final_posterior = last(posterior_history)
                @test final_posterior isa RxInfer.Beta
            end

            @testset "1.3 Can use Categorical with one-hot" begin
                obs_onehot = one_hot(2, 3)

                result = RxInfer.infer(
                    model = categorical_model_onehot(n=3),
                    data = (y = obs_onehot,),
                    iterations = 5
                )

                @test haskey(result.posteriors, :p)
                final_p = last(result.posteriors[:p])
                @test final_p isa RxInfer.Dirichlet
                p_mean = mean(final_p)
                @test p_mean[2] > p_mean[1]
            end
        end
    end

    if RXINFER_TEST_AVAILABLE
        @testset "2. Discrete State Space Model" begin
            @testset "2.1 Simple HMM-like model with Transition" begin
                B = [0.9 0.1; 0.1 0.9]
                A = [0.8 0.2; 0.2 0.8]
                prior = [0.5, 0.5]
                obs_onehot = one_hot(1, 2)

                result = RxInfer.infer(
                    model = simple_hmm_v2(A=A, B=B, prior_state=prior),
                    data = (y = obs_onehot,),
                    iterations = 10
                )

                @test haskey(result.posteriors, :s_next)
                posterior = last(result.posteriors[:s_next])
                probs = RxInfer.probvec(posterior)
                @test sum(probs) ≈ 1.0
                @test probs[1] > 0.5
            end

            @testset "2.2 Multi-timestep inference" begin
                B = [0.9 0.1; 0.1 0.9]
                A = [0.8 0.2; 0.2 0.8]
                T = 3
                observations = [one_hot(1, 2), one_hot(1, 2), one_hot(2, 2)]
                prior = [0.5, 0.5]

                result = RxInfer.infer(
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
                a_prior = ones(2, 2) .+ 0.1
                T = 6

                states = [one_hot(1, 2), one_hot(1, 2), one_hot(1, 2),
                         one_hot(2, 2), one_hot(2, 2), one_hot(2, 2)]
                observations = [one_hot(1, 2), one_hot(1, 2), one_hot(1, 2),
                              one_hot(2, 2), one_hot(2, 2), one_hot(2, 2)]

                result = RxInfer.infer(
                    model = learning_obs_model_v2(a_prior=a_prior, T=T),
                    data = (y = observations, s_onehot = states),
                    iterations = 10
                )

                @test haskey(result.posteriors, :A)
                A_posterior = mean(last(result.posteriors[:A]))
                @test A_posterior[1, 1] > A_posterior[1, 2]
                @test A_posterior[2, 2] > A_posterior[2, 1]
            end

            @testset "3.2 Learning initial state priors" begin
                d_prior = [1.0, 1.0]
                T = 5

                states = [one_hot(2, 2), one_hot(2, 2), one_hot(2, 2),
                         one_hot(2, 2), one_hot(1, 2)]

                result = RxInfer.infer(
                    model = prior_learning_model_v2(d_prior=d_prior, T=T),
                    data = (s_onehot = states,),
                    iterations = 10
                )

                @test haskey(result.posteriors, :D)
                D_posterior = mean(last(result.posteriors[:D]))
                @test D_posterior[2] > D_posterior[1]
            end
        end
    end

    @testset "4. Utility Functions" begin
        @testset "4.1 flatten_state/unflatten_state round-trip" begin
            dims = [6, 2, 2]  # Spider model dimensions
            n_states = prod(dims)

            for idx in 1:n_states
                state = unflatten_state(idx, dims)
                idx_back = flatten_state(state, dims)
                @test idx == idx_back
            end
        end

        @testset "4.2 State conversion boundaries" begin
            dims = [6, 2, 2]

            # First state
            @test flatten_state([1, 1, 1], dims) == 1
            # Last state
            @test flatten_state([6, 2, 2], dims) == 24
            # Some middle states
            @test unflatten_state(1, dims) == [1, 1, 1]
            @test unflatten_state(24, dims) == [6, 2, 2]
        end

        @testset "4.3 one_hot function" begin
            v = one_hot(2, 3)
            @test v == [0.0, 1.0, 0.0]
            @test sum(v) == 1.0

            v2 = one_hot(1, 5)
            @test v2[1] == 1.0
            @test sum(v2) == 1.0
        end
    end

    @testset "5. Spider Phobia Model Components" begin
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

    @testset "6. RxInfer Spider Model" begin
        @testset "6.1 Can build RxInfer matrices" begin
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

        @testset "6.2 Can run RxInfer state inference" begin
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

        @testset "6.3 Can run RxInfer simulation" begin
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
