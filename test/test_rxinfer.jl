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

# 3. Simple HMM-like model using DiscreteTransition node
RxInfer.@model function simple_hmm_v2(y, A, B, prior_state)
    s ~ Categorical(prior_state)
    s_next ~ DiscreteTransition(s, B)
    y ~ DiscreteTransition(s_next, A)
end

# 4. Multi-timestep HMM (new GraphPPL syntax - no randomvar)
RxInfer.@model function multi_step_hmm_v2(y, A, B, prior_state)
    s_prev = prior_state
    for t in 1:length(y)
        s[t] ~ DiscreteTransition(s_prev, B)
        y[t] ~ DiscreteTransition(s[t], A)
        s_prev = s[t]
    end
end

# 5. Learning observation model - skip for now, DirichletCollection has issues
# This requires more complex setup with proper inference constraints

# 6. Learning initial state prior
RxInfer.@model function prior_learning_model_v2(s_onehot, d_prior)
    D ~ Dirichlet(d_prior)
    for t in 1:length(s_onehot)
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
            @testset "2.1 Simple HMM-like model with DiscreteTransition" begin
                A = [0.9 0.1; 0.2 0.8]  # 2x2 emission matrix
                B = [0.7 0.3; 0.3 0.7]  # 2x2 transition matrix
                prior = [0.5, 0.5]
                obs = [1.0, 0.0]  # one-hot observation: state 1

                result = RxInfer.infer(
                    model = simple_hmm_v2(A=A, B=B, prior_state=prior),
                    data = (y=obs,)
                )

                @test haskey(result.posteriors, :s)
                @test haskey(result.posteriors, :s_next)

                # With observation [1,0] and A[1,1]=0.9, state 1 should be more likely
                s_next_probs = probvec(result.posteriors[:s_next])
                @test s_next_probs[1] > s_next_probs[2]
            end

            @testset "2.2 Multi-timestep inference" begin
                A = [0.9 0.1; 0.2 0.8]
                B = [0.7 0.3; 0.3 0.7]
                prior = [0.5, 0.5]
                obs = [[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]]

                result = RxInfer.infer(
                    model = multi_step_hmm_v2(A=A, B=B, prior_state=prior),
                    data = (y=obs,)
                )

                @test haskey(result.posteriors, :s)
                s_posteriors = result.posteriors[:s]
                @test length(s_posteriors) == 3  # 3 timesteps
            end
        end

        @testset "3. Dirichlet-Categorical Learning" begin
            @testset "3.1 Learning observation likelihoods (external Dirichlet)" begin
                # Using external closed-form Dirichlet updates instead of in-graph
                # DirichletCollection (which has stack overflow issues in RxInfer 4.6)
                # See rxinfer_native.jl for tradeoff analysis

                if isdefined(IFSActiveInference, :learn_likelihood_external)
                    # 2 observation outcomes, 2 states
                    a_prior = ones(2, 2)  # Uniform Dirichlet prior

                    # Observations: state 1 -> usually obs 1, state 2 -> usually obs 2
                    observations = [
                        [0.9, 0.1],  # t=1: mostly obs 1
                        [0.1, 0.9],  # t=2: mostly obs 2
                        [0.8, 0.2],  # t=3: mostly obs 1
                        [0.2, 0.8],  # t=4: mostly obs 2
                    ]
                    states = [
                        [1.0, 0.0],  # t=1: state 1
                        [0.0, 1.0],  # t=2: state 2
                        [1.0, 0.0],  # t=3: state 1
                        [0.0, 1.0],  # t=4: state 2
                    ]

                    a_post, A_mean = IFSActiveInference.learn_likelihood_external(
                        a_prior, observations, states
                    )

                    # A should learn: state 1 -> obs 1, state 2 -> obs 2
                    @test size(A_mean) == (2, 2)
                    @test all(sum(A_mean, dims=1) .≈ 1.0)  # Columns sum to 1
                    @test A_mean[1, 1] > A_mean[2, 1]  # State 1 -> obs 1 more likely
                    @test A_mean[2, 2] > A_mean[1, 2]  # State 2 -> obs 2 more likely
                else
                    @test_skip "learn_likelihood_external not available"
                end
            end

            @testset "3.2 Learning initial state priors" begin
                d_prior = [1.0, 1.0]

                states = [one_hot(2, 2), one_hot(2, 2), one_hot(2, 2),
                         one_hot(2, 2), one_hot(1, 2)]

                result = RxInfer.infer(
                    model = prior_learning_model_v2(d_prior=d_prior),
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

    @testset "7. Native RxInfer Factor Graph Models" begin
        @testset "7.1 State inference with native model" begin
            if isdefined(IFSActiveInference, :infer_state_rxinfer)
                # Build matrices
                params = ModelParams()
                matrices = IFSActiveInference.build_rxinfer_matrices(params=params)

                # Create a test observation (one-hot for each modality)
                obs = [
                    one_hot(1, 2),  # Visual: see spider
                    one_hot(1, 2),  # Arousal: high
                    one_hot(1, 3),  # Affect: fearful
                    one_hot(1, 6)   # Behavior: at safe distance
                ]

                # Uniform prior
                prior = ones(matrices.n_states) ./ matrices.n_states

                # Run inference
                qs, result = IFSActiveInference.infer_state_rxinfer(obs, matrices.A, prior)

                @test length(qs) == matrices.n_states
                @test sum(qs) ≈ 1.0 atol=1e-6
                @test all(qs .>= 0)
            else
                @test_skip "infer_state_rxinfer not available"
            end
        end

        @testset "7.2 Prior learning with native model" begin
            if isdefined(IFSActiveInference, :learn_prior_rxinfer)
                # Create some observed initial states
                n_states = 24
                s_observations = [
                    one_hot(1, n_states),  # State 1 observed
                    one_hot(1, n_states),  # State 1 again
                    one_hot(2, n_states),  # State 2
                    one_hot(1, n_states),  # State 1
                    one_hot(1, n_states)   # State 1
                ]

                # Uniform prior
                d_prior = ones(n_states)

                # Learn updated prior
                d_posterior, D_mean = IFSActiveInference.learn_prior_rxinfer(
                    s_observations, d_prior; iterations=5
                )

                @test length(d_posterior) == n_states
                @test length(D_mean) == n_states
                @test sum(D_mean) ≈ 1.0 atol=1e-6
                # State 1 was observed most often, should have highest posterior
                @test D_mean[1] > D_mean[3]
            else
                @test_skip "learn_prior_rxinfer not available"
            end
        end

        @testset "7.3 Native therapy simulation" begin
            if isdefined(IFSActiveInference, :run_rxinfer_native_therapy)
                params = ModelParams(N=5, T=4)
                result = IFSActiveInference.run_rxinfer_native_therapy(
                    n_trials=5,
                    spider_dangerous=false,
                    params=params,
                    gamma=1.0
                )

                @test haskey(result, :d_evolution)
                @test haskey(result, :approach_count)
                @test haskey(result, :avoid_count)
                @test length(result.d_evolution) == 5
                @test result.approach_count + result.avoid_count == 5
            else
                @test_skip "run_rxinfer_native_therapy not available"
            end
        end
    end

end

println("\nRxInfer tests completed!")
