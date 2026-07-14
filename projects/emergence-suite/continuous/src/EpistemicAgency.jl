module EpistemicAgency

using Random
using Statistics
using Main.GlobalPrecisionField

export AgencyConfig, expected_information_gain, run_agency_seed, run_epistemic_agency

Base.@kwdef struct AgencyConfig
    seeds::Vector{Int} = collect(8601:8620)
    episodes::Int = 200
    switch_episode::Int = 101
    sample_cost::Float64 = 0.045
    parameter_epistemic_weight::Float64 = 0.08
    forgetting::Float64 = 0.985
    surprise_memory::Float64 = 0.78
    change_threshold::Float64 = 0.30
    change_reset::Float64 = 0.45
end

mutable struct AgentBeliefs
    alpha::Vector{Float64}
    beta::Vector{Float64}
    surprise::Float64
end

AgentBeliefs() = AgentBeliefs(fill(2.0, 3), fill(2.0, 3), 0.0)

binary_entropy(probability) = begin
    p = clamp(probability, 1.0e-12, 1 - 1.0e-12)
    -p * log(p) - (1 - p) * log(1 - p)
end

function posterior_after_cue(prior_positive, reliability, cue)
    p = clamp(prior_positive, 1.0e-9, 1 - 1.0e-9)
    r = clamp(reliability, 0.501, 0.999)
    likelihood_positive = cue == 1 ? r : 1 - r
    likelihood_negative = cue == 1 ? 1 - r : r
    return p * likelihood_positive /
        (p * likelihood_positive + (1 - p) * likelihood_negative)
end

function expected_entropy(prior_positive, reliability)
    p = prior_positive
    r = clamp(reliability, 0.501, 0.999)
    probability_positive_cue = p * r + (1 - p) * (1 - r)
    posterior_positive = posterior_after_cue(p, r, 1)
    posterior_negative = posterior_after_cue(p, r, -1)
    return probability_positive_cue * binary_entropy(posterior_positive) +
        (1 - probability_positive_cue) * binary_entropy(posterior_negative)
end

expected_information_gain(prior_positive, reliability) =
    binary_entropy(prior_positive) - expected_entropy(prior_positive, reliability)

function reliability_moments(beliefs::AgentBeliefs, channel)
    alpha = beliefs.alpha[channel]
    beta = beliefs.beta[channel]
    total = alpha + beta
    mean_reliability = alpha / total
    variance = alpha * beta / (total^2 * (total + 1))
    return clamp(mean_reliability, 0.501, 0.999), variance
end

function efe_score(beliefs, probability_positive, channel, config)
    reliability, variance = reliability_moments(beliefs, channel)
    return expected_entropy(probability_positive, reliability) + config.sample_cost -
        config.parameter_epistemic_weight * sqrt(variance)
end

function select_action(rng, strategy, beliefs, probability_positive, available, config)
    isempty(available) && return 0
    stop_score = binary_entropy(probability_positive)
    if strategy == "efe"
        scores = [efe_score(beliefs, probability_positive, channel, config) for channel in available]
        index = argmin(scores)
        return scores[index] < stop_score ? available[index] : 0
    elseif strategy == "fixed"
        channel = first(sort(available))
        score = expected_entropy(probability_positive,
            first(reliability_moments(beliefs, channel))) + config.sample_cost
        return score < stop_score ? channel : 0
    end
    channel = rand(rng, available)
    score = expected_entropy(probability_positive,
        first(reliability_moments(beliefs, channel))) + config.sample_cost
    return score < stop_score ? channel : 0
end

function update_reliability!(beliefs, sampled, cues, cause, config)
    beliefs.alpha .= 2 .+ config.forgetting .* (beliefs.alpha .- 2)
    beliefs.beta .= 2 .+ config.forgetting .* (beliefs.beta .- 2)
    surprises = Float64[]
    for channel in sampled
        reliability, _ = reliability_moments(beliefs, channel)
        correct = cues[channel] == cause
        beliefs.alpha[channel] += correct
        beliefs.beta[channel] += !correct
        push!(surprises, abs((correct ? 1.0 : 0.0) - reliability))
    end
    isempty(surprises) && return
    beliefs.surprise = config.surprise_memory * beliefs.surprise +
        (1 - config.surprise_memory) * mean(surprises)
    if beliefs.surprise > config.change_threshold
        beliefs.alpha .= 2 .+ config.change_reset .* (beliefs.alpha .- 2)
        beliefs.beta .= 2 .+ config.change_reset .* (beliefs.beta .- 2)
        beliefs.surprise *= config.change_reset
    end
end

function true_reliability(episode, config)
    if episode < config.switch_episode
        return [0.90, 0.68, 0.56]
    end
    return [0.55, 0.68, 0.90]
end

function run_strategy(seed, strategy, causes, all_cues, config)
    rng = MersenneTwister(seed + (strategy == "efe" ? 10_000 : strategy == "random" ? 20_000 : 30_000))
    beliefs = AgentBeliefs()
    rows = NamedTuple[]
    for episode in 1:config.episodes
        cause = causes[episode]
        cues = view(all_cues, :, episode)
        probability_positive = 0.5
        available = collect(1:3)
        sampled = Int[]
        first_channel = 0
        while !isempty(available)
            channel = select_action(
                rng, strategy, beliefs, probability_positive, available, config)
            if channel == 0 && isempty(sampled)
                channel = strategy == "fixed" ? first(sort(available)) : rand(rng, available)
            end
            channel == 0 && break
            isempty(sampled) && (first_channel = channel)
            push!(sampled, channel)
            filter!(!=(channel), available)
            reliability, _ = reliability_moments(beliefs, channel)
            probability_positive = posterior_after_cue(
                probability_positive, reliability, cues[channel])
        end
        decision = probability_positive >= 0.5 ? 1 : -1
        update_reliability!(beliefs, sampled, cues, cause, config)
        estimated = [first(reliability_moments(beliefs, channel)) for channel in 1:3]
        push!(rows, (
            seed = seed, strategy = strategy, episode = episode,
            regime = episode < config.switch_episode ? "before" : "after",
            correct = decision == cause, samples = length(sampled),
            first_channel = first_channel, posterior_confidence = 2abs(probability_positive - 0.5),
            estimated_reliability_1 = estimated[1],
            estimated_reliability_2 = estimated[2],
            estimated_reliability_3 = estimated[3],
            surprise = beliefs.surprise,
        ))
    end
    return rows
end

function run_agency_seed(seed::Int; config::AgencyConfig = AgencyConfig())
    rng = MersenneTwister(seed)
    causes = [rand(rng, Bool) ? 1 : -1 for _ in 1:config.episodes]
    all_cues = zeros(Int, 3, config.episodes)
    for episode in 1:config.episodes
        reliability = true_reliability(episode, config)
        for channel in 1:3
            all_cues[channel, episode] = rand(rng) < reliability[channel] ?
                causes[episode] : -causes[episode]
        end
    end
    return vcat(
        run_strategy(seed, "efe", causes, all_cues, config),
        run_strategy(seed, "random", causes, all_cues, config),
        run_strategy(seed, "fixed", causes, all_cues, config),
    )
end

function strategy_rows(rows, strategy)
    return filter(row -> row.strategy == strategy, rows)
end

function late_after(rows, config)
    matching = filter(row -> row.episode >= config.episodes - 29, rows)
    return matching
end

function early_after(rows, config)
    return filter(row -> config.switch_episode <= row.episode < config.switch_episode + 20, rows)
end

function seed_metrics(rows, config)
    efe = strategy_rows(rows, "efe")
    random = strategy_rows(rows, "random")
    fixed = strategy_rows(rows, "fixed")
    efe_after = filter(row -> row.regime == "after", efe)
    random_after = filter(row -> row.regime == "after", random)
    fixed_after = filter(row -> row.regime == "after", fixed)
    efe_before = filter(row -> row.regime == "before", efe)
    late = late_after(efe, config)
    early = early_after(efe, config)
    return (
        seed = first(rows).seed,
        efe_after_accuracy = mean(row.correct for row in efe_after),
        random_after_accuracy = mean(row.correct for row in random_after),
        fixed_after_accuracy = mean(row.correct for row in fixed_after),
        efe_mean_samples = mean(row.samples for row in efe),
        random_mean_samples = mean(row.samples for row in random),
        fixed_mean_samples = mean(row.samples for row in fixed),
        early_after_accuracy = mean(row.correct for row in early),
        late_after_accuracy = mean(row.correct for row in late),
        before_channel_1 = mean(row.first_channel == 1 for row in efe_before),
        late_channel_3 = mean(row.first_channel == 3 for row in late),
        late_reliability_1 = mean(row.estimated_reliability_1 for row in late),
        late_reliability_3 = mean(row.estimated_reliability_3 for row in late),
    )
end

function run_epistemic_agency(output_dir::AbstractString =
        joinpath(@__DIR__, "..", "results", "epistemic_agency");
        config::AgencyConfig = AgencyConfig())
    mkpath(output_dir)
    traces = NamedTuple[]
    metrics = NamedTuple[]
    for seed in config.seeds
        rows = run_agency_seed(seed; config = config)
        append!(traces, rows)
        push!(metrics, seed_metrics(rows, config))
    end
    means = NamedTuple{Tuple(filter(!=(:seed), keys(first(metrics))))}(Tuple(
        mean(getfield(row, key) for row in metrics)
        for key in filter(!=(:seed), keys(first(metrics)))))
    win_rates = (
        beats_random = mean(row.efe_after_accuracy > row.random_after_accuracy for row in metrics),
        beats_fixed = mean(row.efe_after_accuracy > row.fixed_after_accuracy for row in metrics),
        efficient = mean(row.efe_mean_samples <= row.random_mean_samples for row in metrics),
        recovered = mean(row.late_after_accuracy >= row.early_after_accuracy + 0.10 for row in metrics),
        policy_shifted = mean(row.before_channel_1 > 0.55 && row.late_channel_3 > 0.55 for row in metrics),
    )
    criteria = (
        active_binding_advantage = means.efe_after_accuracy >=
            max(means.random_after_accuracy, means.fixed_after_accuracy) + 0.03 &&
            win_rates.beats_random >= 0.75 && win_rates.beats_fixed >= 0.75,
        sampling_efficiency = means.efe_mean_samples <= means.random_mean_samples &&
            win_rates.efficient >= 0.75,
        post_switch_recovery = means.late_after_accuracy >= 0.80 &&
            means.late_after_accuracy >= means.early_after_accuracy + 0.10 &&
            win_rates.recovered >= 0.75,
        policy_reallocation = means.before_channel_1 > 0.55 && means.late_channel_3 > 0.55 &&
            win_rates.policy_shifted >= 0.75,
        precision_beliefs_reversed = means.late_reliability_3 >=
            means.late_reliability_1 + 0.15,
    )
    summary = (
        experiment = 32,
        protocol = "expected-free-energy channel selection with an unannounced reliability switch",
        mean_metrics = means,
        win_rates = win_rates,
        criteria = criteria,
    )
    GlobalPrecisionField.write_csv(joinpath(output_dir, "trace.csv"), traces)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "per_seed.csv"), metrics)
    GlobalPrecisionField.write_json(joinpath(output_dir, "summary.json"), summary)
    GlobalPrecisionField.write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = all(values(criteria)),
        theory_result = all(values(criteria)) ?
            "expected-free-energy policies redirect sampling when precision beliefs change" :
            "epistemic-agency criteria not yet satisfied",
    ))
    return (traces = traces, metrics = metrics, summary = summary)
end

end
