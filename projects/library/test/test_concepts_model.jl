"""
    Concepts Model Tests (PMC7250191)
"""

using Test
using Random

if !isdefined(@__MODULE__, :ActiveInferenceCore)
    include("../src/active_inference/ActiveInferenceCore.jl")
end
using .ActiveInferenceCore

@testset "Concepts Model" begin
    Random.seed!(123)

    model = build_concepts_model(allow_reports=true)

    @testset "Full knowledge reports perfectly" begin
        agent = init_concepts_agent(model)
        results = evaluate_reporting(agent, model; trials_per_animal=4, deterministic=true)
        @test results.acc_specific == 1.0
        @test results.acc_basic == 1.0
    end

    @testset "Granularity removed yields basic-level accuracy" begin
        agent = init_concepts_agent(model; remove_granularity=true)
        results = evaluate_reporting(agent, model; trials_per_animal=4, deterministic=true)
        @test results.acc_basic == 1.0
        @test results.acc_specific < 1.0
    end

    @testset "Distance generalization question" begin
        distance_model = build_distance_model(allow_reports=true)
        agent = init_concepts_agent(distance_model)
        results = evaluate_distance_reporting(agent, distance_model; trials_per_animal=4, deterministic=true)
        @test results.acc == 1.0
    end

    @testset "BMR selects high prior for observed concept" begin
        q = [10.0, 1.0, 1.0]
        p = [1.0, 1.0, 1.0]
        result = bmr_reduce_D(q, p)
        @test result.prior[1] == 8.0
    end
end
