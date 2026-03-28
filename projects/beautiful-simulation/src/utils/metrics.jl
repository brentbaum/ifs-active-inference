safe_mean(xs) = isempty(xs) ? NaN : mean(xs)

function state_accuracy(posteriors::Matrix{Float64}, truth::Vector{Int})
    correct = 0
    for t in eachindex(truth)
        correct += argmax(view(posteriors, t, :)) == truth[t]
    end
    return correct / length(truth)
end

function negative_log_likelihood(log_evidence::Float64, n_steps::Int)
    return -log_evidence / n_steps
end

rmse(pred::AbstractVector{<:Real}, truth::AbstractVector{<:Real}) = sqrt(mean((Float64.(pred) .- Float64.(truth)) .^ 2))

function brier_score(predictions::Vector{Float64}, outcomes::Vector{Float64})
    return mean((predictions .- outcomes) .^ 2)
end

function expected_calibration_error(
    confidences::Vector{Float64},
    correctness::Vector{Bool};
    n_bins::Int = 10
)
    if isempty(confidences)
        return NaN
    end

    edges = collect(range(0.0, 1.0; length = n_bins + 1))
    total = length(confidences)
    ece = 0.0
    for b in 1:n_bins
        left = edges[b]
        right = edges[b + 1]
        indices = findall(i -> confidences[i] >= left &&
            (b == n_bins ? confidences[i] <= right : confidences[i] < right), eachindex(confidences))
        isempty(indices) && continue
        acc = mean(Float64.(correctness[indices]))
        conf = mean(confidences[indices])
        ece += abs(acc - conf) * (length(indices) / total)
    end
    return ece
end

function matrix_is_column_stochastic(matrix::AbstractMatrix{<:Real}; atol::Float64 = 1e-8)
    return all(matrix .>= -atol) && all(abs.(sum(matrix, dims = 1) .- 1.0) .<= atol)
end

function coverage_90(means::AbstractVector{<:Real}, vars::AbstractVector{<:Real}, truth::AbstractVector{<:Real})
    z = 1.6448536269514722
    hits = map(eachindex(truth)) do i
        width = z * sqrt(max(Float64(vars[i]), 1e-12))
        lower = Float64(means[i]) - width
        upper = Float64(means[i]) + width
        lower <= Float64(truth[i]) <= upper
    end
    return mean(Float64.(hits))
end

function micro_switch_rate(map_states::Vector{Int})
    length(map_states) <= 1 && return 0.0
    return sum(map_states[i] != map_states[i - 1] for i in 2:length(map_states)) / (length(map_states) - 1)
end

function mean_dwell(map_states::Vector{Int})
    isempty(map_states) && return NaN
    runs = Int[]
    current = map_states[1]
    length_run = 1
    for i in 2:length(map_states)
        if map_states[i] == current
            length_run += 1
        else
            push!(runs, length_run)
            current = map_states[i]
            length_run = 1
        end
    end
    push!(runs, length_run)
    return mean(runs)
end
