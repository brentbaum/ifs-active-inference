module BayesianBinding

using Random
using Statistics
using Main.GlobalPrecisionField

export BindingConfig, infer_bound_cause, run_binding_seed, run_bayesian_binding

Base.@kwdef struct BindingConfig
    seeds::Vector{Int} = collect(8501:8520)
    trials_per_condition::Int = 240
    coherence::Float64 = 0.90
end

logistic(x) = inv(1 + exp(-x))

function logsumexp(values)
    maximum_value = maximum(values)
    return maximum_value + log(sum(exp(value - maximum_value) for value in values))
end

function trial_definition(condition)
    if condition == "coherent_ambiguous"
        return (signal = fill(0.60, 3), phi = fill(0.10, 3), distractor = false)
    elseif condition == "salient_distractor"
        return (signal = [1.60, 0.32, 0.32], phi = [-2.00, 1.40, 1.40], distractor = true)
    end
    return (signal = fill(0.90, 3), phi = fill(0.70, 3), distractor = false)
end

function generate_trial(rng, condition)
    definition = trial_definition(condition)
    cause = rand(rng, Bool) ? 1 : -1
    local_causes = fill(cause, 3)
    definition.distractor && (local_causes[1] = -cause)
    precision = exp.(definition.phi)
    observation = definition.signal .* local_causes .+ randn(rng, 3) ./ sqrt.(precision)
    return (cause = cause, local_causes = local_causes, observation = observation,
        signal = definition.signal, phi = definition.phi)
end

function log_normal(observation, mean, precision)
    return 0.5 * (log(precision) - log(2pi) - precision * (observation - mean)^2)
end

function infer_bound_cause(observation, signal, phi; coherence = 0.90)
    precision = exp.(phi)
    channel_coherence = 0.5 .+ (coherence - 0.5) .* precision ./ maximum(precision)
    states = NamedTuple[]
    log_weights = Float64[]
    for global_cause in (-1, 1), z1 in (-1, 1), z2 in (-1, 1), z3 in (-1, 1)
        local_causes = (z1, z2, z3)
        log_weight = -log(2)
        for channel in 1:3
            agreement = local_causes[channel] == global_cause
            log_weight += log(agreement ? channel_coherence[channel] :
                1 - channel_coherence[channel])
            log_weight += log_normal(observation[channel],
                signal[channel] * local_causes[channel], precision[channel])
        end
        push!(states, (global_cause = global_cause, local_causes = local_causes))
        push!(log_weights, log_weight)
    end
    normalizer = logsumexp(log_weights)
    weights = exp.(log_weights .- normalizer)
    probability_positive = sum(weight for (state, weight) in zip(states, weights)
        if state.global_cause == 1)
    local_probabilities = [logistic(
        2 * signal[channel] * precision[channel] * observation[channel]) for channel in 1:3]
    local_votes = [probability >= 0.5 ? 1 : -1 for probability in local_probabilities]
    local_decision = sum(local_votes) > 0 ? 1 : -1
    return (
        probability_positive = probability_positive,
        decision = probability_positive >= 0.5 ? 1 : -1,
        confidence = 2abs(probability_positive - 0.5),
        local_probabilities = local_probabilities,
        local_decision = local_decision,
        mean_local_confidence = mean(2abs(probability - 0.5) for probability in local_probabilities),
    )
end

function run_binding_seed(seed::Int; config::BindingConfig = BindingConfig())
    rng = MersenneTwister(seed)
    rows = NamedTuple[]
    for condition in ("coherent_ambiguous", "salient_distractor", "clear_coherent")
        for trial in 1:config.trials_per_condition
            generated = generate_trial(rng, condition)
            bound = infer_bound_cause(generated.observation, generated.signal, generated.phi;
                coherence = config.coherence)
            inverted = infer_bound_cause(generated.observation, generated.signal,
                .-generated.phi; coherence = config.coherence)
            push!(rows, (
                seed = seed, trial = trial, condition = condition,
                cause = generated.cause,
                bound_correct = bound.decision == generated.cause,
                local_correct = bound.local_decision == generated.cause,
                inverted_correct = inverted.decision == generated.cause,
                bound_confidence = bound.confidence,
                local_confidence = bound.mean_local_confidence,
                probability_positive = bound.probability_positive,
            ))
        end
    end
    return rows
end

function accuracy(rows, field)
    return mean(getfield(row, field) for row in rows)
end

function seed_metrics(rows)
    ambiguous = filter(row -> row.condition == "coherent_ambiguous", rows)
    distractor = filter(row -> row.condition == "salient_distractor", rows)
    return (
        seed = first(rows).seed,
        overall_bound_accuracy = accuracy(rows, :bound_correct),
        overall_local_accuracy = accuracy(rows, :local_correct),
        ambiguous_bound_accuracy = accuracy(ambiguous, :bound_correct),
        ambiguous_local_accuracy = accuracy(ambiguous, :local_correct),
        ambiguous_bound_confidence = mean(row.bound_confidence for row in ambiguous),
        ambiguous_local_confidence = mean(row.local_confidence for row in ambiguous),
        distractor_bound_accuracy = accuracy(distractor, :bound_correct),
        distractor_inverted_accuracy = accuracy(distractor, :inverted_correct),
    )
end

function run_bayesian_binding(output_dir::AbstractString =
        joinpath(@__DIR__, "..", "results", "bayesian_binding");
        config::BindingConfig = BindingConfig())
    mkpath(output_dir)
    trials = NamedTuple[]
    metrics = NamedTuple[]
    for seed in config.seeds
        rows = run_binding_seed(seed; config = config)
        append!(trials, rows)
        push!(metrics, seed_metrics(rows))
    end
    means = (
        overall_bound_accuracy = mean(row.overall_bound_accuracy for row in metrics),
        overall_local_accuracy = mean(row.overall_local_accuracy for row in metrics),
        ambiguous_bound_accuracy = mean(row.ambiguous_bound_accuracy for row in metrics),
        ambiguous_local_accuracy = mean(row.ambiguous_local_accuracy for row in metrics),
        ambiguous_bound_confidence = mean(row.ambiguous_bound_confidence for row in metrics),
        ambiguous_local_confidence = mean(row.ambiguous_local_confidence for row in metrics),
        distractor_bound_accuracy = mean(row.distractor_bound_accuracy for row in metrics),
        distractor_inverted_accuracy = mean(row.distractor_inverted_accuracy for row in metrics),
    )
    win_rates = (
        overall_binding = mean(
            row.overall_bound_accuracy > row.overall_local_accuracy for row in metrics),
        ambiguous_binding = mean(
            row.ambiguous_bound_accuracy > row.ambiguous_local_accuracy for row in metrics),
        precision_calibration = mean(
            row.distractor_bound_accuracy > row.distractor_inverted_accuracy for row in metrics),
    )
    criteria = (
        global_binding_advantage = means.overall_bound_accuracy >=
            means.overall_local_accuracy + 0.03 && win_rates.overall_binding >= 0.80,
        ambiguous_coherence_advantage = means.ambiguous_bound_accuracy >=
            means.ambiguous_local_accuracy + 0.03 && win_rates.ambiguous_binding >= 0.80,
        jointly_coherent_ignition = means.ambiguous_bound_confidence >=
            means.ambiguous_local_confidence + 0.05,
        salient_distractor_rejected = means.distractor_bound_accuracy >= 0.75,
        calibrated_precision_required = means.distractor_bound_accuracy >=
            means.distractor_inverted_accuracy + 0.15 && win_rates.precision_calibration >= 0.80,
    )
    summary = (
        experiment = 31,
        protocol = "exact inference over one global cause and three locally competing causes",
        mean_metrics = means,
        win_rates = win_rates,
        criteria = criteria,
    )
    GlobalPrecisionField.write_csv(joinpath(output_dir, "trials.csv"), trials)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "per_seed.csv"), metrics)
    GlobalPrecisionField.write_json(joinpath(output_dir, "summary.json"), summary)
    GlobalPrecisionField.write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = all(values(criteria)),
        theory_result = all(values(criteria)) ?
            "precision-weighted coherence binds a global cause from competing local explanations" :
            "Bayesian-binding criteria not yet satisfied",
    ))
    return (trials = trials, metrics = metrics, summary = summary)
end

end
