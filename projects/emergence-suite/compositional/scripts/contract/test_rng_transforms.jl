#!/usr/bin/env julia

module RngTransforms
include(joinpath(@__DIR__, "rng_transforms.jl"))
end

function main()
    RngTransforms.uniform_transform(2.0, 6.0, 0.25) == 3.0 ||
        error("uniform transform vector failed")
    RngTransforms.uniform_transform(2.0, 2.0, 0.75) == 2.0 ||
        error("degenerate uniform transform vector failed")

    RngTransforms.integer_uniform_transform(2, 4, 0.0) == 2 ||
        error("integer-uniform lower boundary failed")
    RngTransforms.integer_uniform_transform(2, 4, 1 / 3) == 3 ||
        error("integer-uniform internal boundary failed")
    RngTransforms.integer_uniform_transform(2, 4, prevfloat(1.0)) == 4 ||
        error("integer-uniform upper boundary failed")

    values = ["first", "second", "third"]
    probabilities = [0.25, 0.50, 0.25]
    RngTransforms.inverse_categorical(values, probabilities, 0.0) == "first" ||
        error("categorical lower boundary failed")
    RngTransforms.inverse_categorical(values, probabilities, 0.25) == "second" ||
        error("categorical strict cumulative boundary failed")
    RngTransforms.inverse_categorical(values, probabilities, 0.75) == "third" ||
        error("categorical second cumulative boundary failed")
    RngTransforms.inverse_categorical(
        values, [0.25, 0.50, prevfloat(0.25)], prevfloat(1.0)) == "third" ||
        error("categorical rounding fallback failed")

    println("RNG transform conformance passed")
    return true
end

main()
