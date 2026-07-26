#!/usr/bin/env julia

function uniform_transform(lower, upper, u)
    0 <= u < 1 || error("rng transform: uniform variate outside [0,1)")
    lower <= upper || error("rng transform: unordered uniform bounds")
    return lower + (upper - lower) * u
end

function integer_uniform_transform(lower::Integer, upper::Integer, u)
    0 <= u < 1 ||
        error("rng transform: uniform variate outside [0,1)")
    lower <= upper ||
        error("rng transform: unordered integer-uniform bounds")
    return lower + floor(Int, (upper - lower + 1) * u)
end

function inverse_categorical(values, probabilities, u)
    0 <= u < 1 ||
        error("rng transform: uniform variate outside [0,1)")
    length(values) == length(probabilities) && !isempty(values) ||
        error("rng transform: categorical dimension mismatch")
    cumulative = zero(Float64)
    for (value, probability) in zip(values, probabilities)
        cumulative += Float64(probability)
        u < cumulative && return value
    end
    return last(values)
end
