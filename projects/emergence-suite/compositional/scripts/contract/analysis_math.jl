#!/usr/bin/env julia

using SHA

const ANALYSIS_CONTRACT_ID = "ifs-ai-experiment-51-contract"
const ANALYSIS_CONTRACT_VERSION = "1.0.0"

function arithmetic_mean(values)
    isempty(values) && error("analysis math: mean of empty series")
    return sum(values) / length(values)
end

function empirical_median(values)
    isempty(values) && error("analysis math: median of empty series")
    ordered = sort(collect(values))
    count = length(ordered)
    midpoint = div(count + 1, 2)
    return isodd(count) ? ordered[midpoint] :
        (ordered[midpoint] + ordered[midpoint + 1]) / 2
end

function sample_standard_deviation(values)
    length(values) >= 2 ||
        error("analysis math: sample standard deviation needs two values")
    center = arithmetic_mean(values)
    squared = sum((value - center)^2 for value in values)
    return sqrt(squared / (length(values) - 1))
end

function nearest_rank(values, probability)
    isempty(values) && error("analysis math: quantile of empty series")
    0 <= probability <= 1 ||
        error("analysis math: probability outside [0,1]")
    ordered = sort(collect(values))
    rank = clamp(ceil(Int, probability * length(ordered)), 1, length(ordered))
    return ordered[rank]
end

function unit_key(unit::String; seed = nothing, arm = nothing,
        episode = nothing, event = nothing, genome = nothing,
        paired = false)
    if paired
        unit == "seed" && return "seed=$(seed)"
        unit == "episode" &&
            return "seed=$(seed);episode=$(episode)"
        unit == "genome" && return "genome=$(genome)"
        unit == "event" &&
            error("analysis math: event cross-arm keys are undefined")
        error("analysis math: unknown paired unit")
    end
    if unit == "seed"
        return "seed=$(seed);arm=$(arm)"
    elseif unit == "episode"
        return "seed=$(seed);arm=$(arm);episode=$(episode)"
    elseif unit == "event"
        return "seed=$(seed);arm=$(arm);event=$(event)"
    elseif unit == "genome"
        return "genome=$(genome);arm=$(arm)"
    end
    error("analysis math: unknown unit")
end

function unit_accepts_row(unit::String, row_kind::String)
    row_kind in ("event", "tick") ||
        error("analysis math: unknown row kind")
    return unit == "event" ? row_kind == "event" : true
end

function u64be_analysis(value::Integer)
    number = UInt64(value)
    return UInt8[(number >> shift) & 0xff for shift in 56:-8:0]
end

function bootstrap_digest(analysis_id, estimand_id, replicate, position)
    fields = Any[
        "ifs-ai-51-bootstrap-v1",
        ANALYSIS_CONTRACT_ID,
        ANALYSIS_CONTRACT_VERSION,
        analysis_id,
        estimand_id,
        u64be_analysis(replicate),
        u64be_analysis(position),
    ]
    bytes = UInt8[]
    for (index, field) in enumerate(fields)
        index > 1 && push!(bytes, 0x00)
        append!(bytes, field isa AbstractVector{UInt8} ?
            field : Vector{UInt8}(codeunits(String(field))))
    end
    return sha256(bytes)
end

function bootstrap_index(unit_count, analysis_id, estimand_id, replicate, position)
    unit_count > 0 || error("analysis math: bootstrap needs units")
    digest = bootstrap_digest(analysis_id, estimand_id, replicate, position)
    integer = UInt64(0)
    for byte in digest[1:8]
        integer = (integer << 8) | UInt64(byte)
    end
    numerator = BigInt(unit_count) * (2 * BigInt(integer) + 1)
    return Int(div(numerator, BigInt(1) << 65))
end

function bootstrap_indices(unit_count, analysis_id, estimand_id, replicate)
    return [bootstrap_index(unit_count, analysis_id, estimand_id,
        replicate, position) for position in 0:(unit_count - 1)]
end

function log_gamma_lanczos(value)
    value > 0 || error("analysis math: log-gamma requires a positive value")
    coefficients = (
        0.99999999999980993,
        676.5203681218851,
        -1259.1392167224028,
        771.32342877765313,
        -176.61502916214059,
        12.507343278686905,
        -0.13857109526572012,
        9.9843695780195716e-6,
        1.5056327351493116e-7,
    )
    shifted = Float64(value) - 1.0
    series = coefficients[1]
    for index in 2:length(coefficients)
        series += coefficients[index] / (shifted + index - 1)
    end
    t = shifted + 7.5
    return 0.91893853320467274178 +
        (shifted + 0.5) * log(t) - t + log(series)
end

function beta_continued_fraction(a, b, x)
    max_iterations = 256
    epsilon = 3e-14
    floor_value = 1e-300
    qab = a + b
    qap = a + 1
    qam = a - 1
    c = 1.0
    d = 1.0 - qab * x / qap
    abs(d) < floor_value && (d = floor_value)
    d = inv(d)
    h = d
    for iteration in 1:max_iterations
        even = 2 * iteration
        coefficient = iteration * (b - iteration) * x /
            ((qam + even) * (a + even))
        d = 1.0 + coefficient * d
        abs(d) < floor_value && (d = floor_value)
        c = 1.0 + coefficient / c
        abs(c) < floor_value && (c = floor_value)
        d = inv(d)
        h *= d * c
        coefficient = -(a + iteration) * (qab + iteration) * x /
            ((a + even) * (qap + even))
        d = 1.0 + coefficient * d
        abs(d) < floor_value && (d = floor_value)
        c = 1.0 + coefficient / c
        abs(c) < floor_value && (c = floor_value)
        d = inv(d)
        delta = d * c
        h *= delta
        abs(delta - 1.0) <= epsilon && return h
    end
    error("analysis math: incomplete-beta continued fraction did not converge")
end

function regularized_incomplete_beta(x, a, b)
    a > 0 && b > 0 ||
        error("analysis math: incomplete-beta shapes must be positive")
    0 <= x <= 1 ||
        error("analysis math: incomplete-beta x outside [0,1]")
    x == 0 && return 0.0
    x == 1 && return 1.0
    front = exp(log_gamma_lanczos(a + b) - log_gamma_lanczos(a) -
        log_gamma_lanczos(b) + a * log(x) + b * log1p(-x))
    if x < (a + 1) / (a + b + 2)
        return front * beta_continued_fraction(a, b, x) / a
    end
    return 1.0 -
        front * beta_continued_fraction(b, a, 1.0 - x) / b
end

function inverse_regularized_incomplete_beta(probability, a, b)
    0 <= probability <= 1 ||
        error("analysis math: beta probability outside [0,1]")
    probability == 0 && return 0.0
    probability == 1 && return 1.0
    lower = 0.0
    upper = 1.0
    for _ in 1:128
        midpoint = lower + (upper - lower) / 2
        if regularized_incomplete_beta(midpoint, a, b) < probability
            lower = midpoint
        else
            upper = midpoint
        end
    end
    return lower + (upper - lower) / 2
end

function clopper_pearson(successes::Integer, trials::Integer, level)
    trials > 0 || error("analysis math: binomial interval needs trials")
    0 <= successes <= trials ||
        error("analysis math: successes outside [0,trials]")
    0 < level < 1 || error("analysis math: interval level outside (0,1)")
    tail = (1.0 - level) / 2
    lower = successes == 0 ? 0.0 :
        inverse_regularized_incomplete_beta(
            tail, successes, trials - successes + 1)
    upper = successes == trials ? 1.0 :
        inverse_regularized_incomplete_beta(
            1.0 - tail, successes + 1, trials - successes)
    return (lower, upper)
end

function point_comparison(value, comparator::String, threshold)
    comparator == "gt" && return value > threshold
    comparator == "ge" && return value >= threshold
    comparator == "lt" && return value < threshold
    comparator == "le" && return value <= threshold
    comparator in ("between", "equivalent") &&
        return threshold[1] <= value <= threshold[2]
    error("analysis math: unknown decision comparator")
end

function interval_comparison(lower, upper, requirement::String, threshold)
    requirement == "none" && return true
    requirement == "lower_above_zero" && return lower > 0
    requirement == "upper_below_zero" && return upper < 0
    requirement == "lower_above_threshold" && return lower > threshold
    requirement == "upper_below_threshold" && return upper < threshold
    requirement == "inside_equivalence" &&
        return lower > threshold[1] && upper < threshold[2]
    error("analysis math: unknown interval requirement")
end

function decision_pass(value, lower, upper, comparator, threshold, requirement)
    return point_comparison(value, comparator, threshold) &&
        interval_comparison(lower, upper, requirement, threshold)
end
