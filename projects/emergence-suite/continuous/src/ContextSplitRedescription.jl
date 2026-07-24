module ContextSplitRedescription

using LinearAlgebra
using Random
using Statistics
using Main.IFSBundleInquiry

export ContextSplitConfig, run_seed, summarize_rows, criteria_verdicts,
    complexity_audit, magic_numbers, PILOT_SEEDS, CONFIRM_SEEDS

const PILOT_SEEDS = collect(174401:174410)
const CONFIRM_SEEDS = collect(174601:174620)
const CUES = IFSBundleInquiry.BUNDLE_CHANNELS
const MODELS = (:global_downweight, :cue_local, :context_split)
const ARMS = (:witnessing, :open_field_informational, :regulation_only,
    :narrowed_contact)

Base.@kwdef struct ContextSplitConfig
    training_observations::Int = 64
    heldout_observations::Int = 32
    parameter_count::Int = 10
    prior_variance::Float64 = 1.50
    observation_sd::Float64 = 0.52
    context_marker_sd::Float64 = 0.42
    context_effect::Float64 = 1.35
    transition_stay_probability::Float64 = 0.88
    root_sessions::Int = 18
    root_prior_positive::Float64 = 0.06
    root_observation_sd::Float64 = 0.72
    contact_sd::Float64 = 0.60
    revision_begun_probability::Float64 = 0.62
    revision_probability::Float64 = 0.80
    reduction_log_bayes_threshold::Float64 = 0.35
    doover_packets::Int = 4
    imaginal_weight::Float64 = 0.72
    beta_prior::Float64 = 1.0
end

logistic(x) = 1 / (1 + exp(-x))
logit(p) = log(clamp(p, 1.0e-12, 1 - 1.0e-12) /
    clamp(1 - p, 1.0e-12, 1 - 1.0e-12))
logsumexp(a, b) = max(a, b) + log(exp(a - max(a, b)) + exp(b - max(a, b)))
normal_logpdf(y, μ, variance) =
    -0.5 * (log(2pi * variance) + (y - μ)^2 / variance)

function normalize_columns(X)
    output = copy(X)
    for column in axes(output, 2)
        scale = sqrt(mean(abs2, view(output, :, column)))
        scale > 1.0e-10 || error("inactive parameter column $column")
        output[:, column] ./= scale
    end
    return output
end

function column_scales(X)
    scales = [sqrt(mean(abs2, view(X, :, column)))
        for column in axes(X, 2)]
    all(>(1.0e-10), scales) || error("inactive parameter column")
    return scales
end

function cue_contrasts(cue)
    cue == 1 && return (1.0, 0.0, 0.0)
    cue == 2 && return (0.0, 1.0, 0.0)
    cue == 3 && return (0.0, 0.0, 1.0)
    return (-1.0, -1.0, -1.0)
end

function generate_contexts(rng, count, stay_probability)
    contexts = Vector{Int}(undef, count)
    contexts[1] = -1
    for index in 2:count
        contexts[index] = rand(rng) < stay_probability ?
            contexts[index - 1] : -contexts[index - 1]
    end
    # Both states are required for a meaningful structured world. This modifies
    # only a degenerate draw, not the agent's observations or inference.
    all(==(-1), contexts) && (contexts[end] = 1)
    all(==(1), contexts) && (contexts[1] = -1)
    return contexts
end

function generate_block(seed, count, offset, structured, config)
    rng = MersenneTwister(seed + offset)
    contexts = generate_contexts(rng, count,
        config.transition_stay_probability)
    cues = [mod1(index + rand(rng, 0:3), length(CUES)) for index in 1:count]
    marker = contexts .+ config.context_marker_sd .* randn(rng, count)
    cue_base = (-0.34, -0.11, 0.13, 0.32)
    behavior = zeros(count)
    root_signal = zeros(count)
    behavior_contexts = copy(contexts)
    if !structured
        # Preserve the exact context-effect marginal while destroying its
        # association with the independently inferred context marker.
        shuffle!(rng, behavior_contexts)
    end
    for index in 1:count
        contextual = config.context_effect * behavior_contexts[index]
        behavior[index] = cue_base[cues[index]] + contextual +
            config.observation_sd * randn(rng)
        # Broad-field root evidence is observed and shared by every model.
        root_signal[index] = 0.55 + 0.28contexts[index] + 0.55randn(rng)
    end
    return (contexts = contexts, cues = cues, marker = marker,
        behavior = behavior, root_signal = root_signal)
end

function generate_world(seed, structured, config)
    training = generate_block(seed, config.training_observations,
        structured ? 100_000 : 200_000, structured, config)
    heldout = generate_block(seed, config.heldout_observations,
        structured ? 300_000 : 400_000, structured, config)
    return (structured = structured, training = training, heldout = heldout)
end

function forward_backward(marker, stay_then, stay_now, config)
    count = length(marker)
    transition = [stay_then 1 - stay_then; 1 - stay_now stay_now]
    emission = zeros(count, 2)
    for index in 1:count
        emission[index, 1] = normal_logpdf(marker[index], -1.0,
            config.context_marker_sd^2)
        emission[index, 2] = normal_logpdf(marker[index], 1.0,
            config.context_marker_sd^2)
    end
    alpha = fill(-Inf, count, 2)
    alpha[1, :] .= log(0.5) .+ emission[1, :]
    scales = zeros(count)
    scales[1] = logsumexp(alpha[1, 1], alpha[1, 2])
    alpha[1, :] .-= scales[1]
    for index in 2:count, state in 1:2
        alpha[index, state] = emission[index, state] + logsumexp(
            alpha[index - 1, 1] + log(transition[1, state]),
            alpha[index - 1, 2] + log(transition[2, state]))
        if state == 2
            scales[index] = logsumexp(alpha[index, 1], alpha[index, 2])
            alpha[index, :] .-= scales[index]
        end
    end
    beta = zeros(count, 2)
    for index in (count - 1):-1:1, state in 1:2
        beta[index, state] = logsumexp(
            log(transition[state, 1]) + emission[index + 1, 1] +
                beta[index + 1, 1],
            log(transition[state, 2]) + emission[index + 1, 2] +
                beta[index + 1, 2]) - scales[index + 1]
    end
    gamma = zeros(count, 2)
    xi = zeros(count - 1, 2, 2)
    for index in 1:count
        norm = logsumexp(alpha[index, 1] + beta[index, 1],
            alpha[index, 2] + beta[index, 2])
        gamma[index, :] .= exp.(alpha[index, :] .+ beta[index, :] .- norm)
    end
    for index in 1:(count - 1)
        values = [alpha[index, from] + log(transition[from, to]) +
            emission[index + 1, to] + beta[index + 1, to]
            for from in 1:2, to in 1:2]
        norm = maximum(values) + log(sum(exp.(values .- maximum(values))))
        xi[index, :, :] .= exp.(values .- norm)
    end
    return (gamma = gamma, xi = xi, log_evidence = sum(scales))
end

function fit_context(marker, config)
    logits = [logit(0.75)]
    posterior = nothing
    covariance = Matrix{Float64}(I, 1, 1) * config.prior_variance
    for _ in 1:12
        probability = logistic(logits[1])
        posterior = forward_backward(marker, probability, probability, config)
        stays = sum(posterior.xi[:, 1, 1]) +
            sum(posterior.xi[:, 2, 2])
        exits = sum(posterior.xi[:, 1, 2]) +
            sum(posterior.xi[:, 2, 1])
        value = logits[1]
        for _ in 1:8
            probability = logistic(value)
            gradient = stays - (stays + exits) * probability -
                value / config.prior_variance
            curvature = -(stays + exits) * probability *
                (1 - probability) - 1 / config.prior_variance
            value -= gradient / curvature
        end
        logits[1] = value
        probability = logistic(value)
        covariance[1, 1] = inv((stays + exits) * probability *
            (1 - probability) + inv(config.prior_variance))
    end
    probability = logistic(logits[1])
    posterior = forward_backward(marker, probability, probability, config)
    return (posterior = posterior, logits = logits, covariance = covariance,
        transition = (probability, probability))
end

function design_matrix(model, data, context_fit, config)
    count = length(data.behavior)
    t = collect(range(-1.0, 1.0; length = count))
    X = zeros(count, model == :cue_local ? config.parameter_count : 9)
    if model == :global_downweight
        for index in 1:count
            contrasts = cue_contrasts(data.cues[index])
            X[index, :] .= (1.0, contrasts..., t[index], t[index]^2,
                sin(pi * t[index]), cos(pi * t[index]),
                data.root_signal[index])
        end
    elseif model == :cue_local
        for index in 1:count
            cue = data.cues[index]
            X[index, cue] = 1.0
            X[index, 4 + cue] = t[index]
            X[index, 9] = t[index]^2
            X[index, 10] = sin(pi * t[index])
        end
    elseif model == :context_split
        gamma = context_fit.posterior.gamma
        for index in 1:count
            cue = data.cues[index]
            X[index, cue] = gamma[index, 1]
            X[index, 4 + cue] = gamma[index, 2]
            X[index, 9] = data.root_signal[index]
        end
    else
        error("unknown model $model")
    end
    return X
end

function bayesian_regression(X, y, config;
        noise_variance = config.observation_sd^2)
    prior_precision = inv(config.prior_variance)
    precision = prior_precision * Matrix{Float64}(I, size(X, 2), size(X, 2)) +
        (X' * X) / noise_variance
    covariance = inv(Symmetric(precision))
    mean_parameters = covariance * (X' * y / noise_variance)
    residual = y - X * mean_parameters
    expected_squared_error = dot(residual, residual) +
        tr(X * covariance * X')
    expected_log_likelihood = -0.5length(y) * log(2pi * noise_variance) -
        0.5expected_squared_error / noise_variance
    kl = 0.5 * (prior_precision *
        (dot(mean_parameters, mean_parameters) + tr(covariance)) -
        size(X, 2) - logdet(covariance) -
        size(X, 2) * log(prior_precision))
    return (mean = mean_parameters, covariance = covariance,
        expected_log_likelihood = expected_log_likelihood,
        complexity = kl, elbo = expected_log_likelihood - kl)
end

function transition_complexity(context_fit, config)
    prior_precision = inv(config.prior_variance)
    μ = context_fit.logits
    Σ = context_fit.covariance
    return 0.5 * (prior_precision * (dot(μ, μ) + tr(Σ)) - 1 -
        logdet(Σ) - log(prior_precision))
end

function fit_global_downweight(X, y, config)
    candidates = collect(range(-2.0, 2.0; length = 81))
    objectives = Float64[]
    regressions = Any[]
    for log_precision in candidates
        noise_variance = config.observation_sd^2 * exp(-log_precision)
        regression = bayesian_regression(X, y, config;
            noise_variance = noise_variance)
        push!(regressions, regression)
        push!(objectives, regression.elbo -
            0.5log_precision^2 / config.prior_variance)
    end
    best = argmax(objectives)
    log_precision = candidates[best]
    step = candidates[2] - candidates[1]
    curvature = if 1 < best < length(candidates)
        max(1.0e-6, -(objectives[best + 1] - 2objectives[best] +
            objectives[best - 1]) / step^2)
    else
        inv(config.prior_variance)
    end
    variance = inv(curvature)
    prior_precision = inv(config.prior_variance)
    precision_complexity = 0.5 * (prior_precision *
        (log_precision^2 + variance) - 1 - log(variance) -
        log(prior_precision))
    regression = regressions[best]
    complexity = regression.complexity + precision_complexity
    elbo = regression.expected_log_likelihood - complexity
    return (regression = regression, log_precision = log_precision,
        noise_variance = config.observation_sd^2 * exp(-log_precision),
        precision_complexity = precision_complexity,
        complexity = complexity, elbo = elbo)
end

function fit_model(model, data, config)
    context_fit = fit_context(data.marker, config)
    raw_X = design_matrix(model, data, context_fit, config)
    scales = column_scales(raw_X)
    X = raw_X ./ reshape(scales, 1, :)
    if model == :global_downweight
        global_fit = fit_global_downweight(X, data.behavior, config)
        regression = global_fit.regression
        complexity = global_fit.complexity
        elbo = global_fit.elbo
        noise_variance = global_fit.noise_variance
    else
        regression = bayesian_regression(X, data.behavior, config)
        noise_variance = config.observation_sd^2
    end
    if model == :context_split
        complexity = regression.complexity +
            transition_complexity(context_fit, config)
        elbo = regression.expected_log_likelihood - complexity
    elseif model == :cue_local
        complexity = regression.complexity
        elbo = regression.elbo
    end
    return (model = model, context_fit = context_fit, X = X,
        regression = regression, complexity = complexity, elbo = elbo,
        noise_variance = noise_variance, column_scales = scales)
end

function heldout_design(model, training, heldout, fit, config)
    count = length(heldout.behavior)
    t = collect(range(-1.0, 1.0; length = count))
    X = zeros(count, model == :cue_local ? config.parameter_count : 9)
    if model == :global_downweight
        for index in 1:count
            contrasts = cue_contrasts(heldout.cues[index])
            X[index, :] .= (1.0, contrasts..., t[index], t[index]^2,
                sin(pi * t[index]), cos(pi * t[index]),
                heldout.root_signal[index])
        end
    elseif model == :cue_local
        for index in 1:count
            cue = heldout.cues[index]
            X[index, cue] = 1.0
            X[index, 4 + cue] = t[index]
            X[index, 9] = t[index]^2
            X[index, 10] = sin(pi * t[index])
        end
    else
        transition = fit.context_fit.transition
        heldout_context = forward_backward(heldout.marker, transition[1],
            transition[2], config)
        for index in 1:count
            cue = heldout.cues[index]
            X[index, cue] = heldout_context.gamma[index, 1]
            X[index, 4 + cue] = heldout_context.gamma[index, 2]
            X[index, 9] = heldout.root_signal[index]
        end
    end
    # Apply the exact training scales, preserving the fitted coordinate system.
    return X ./ reshape(fit.column_scales, 1, :)
end

function heldout_score(fit, world, config)
    X = heldout_design(fit.model, world.training, world.heldout, fit, config)
    μ = X * fit.regression.mean
    predictive_variance = fit.noise_variance .+
        diag(X * fit.regression.covariance * X')
    return mean(normal_logpdf(world.heldout.behavior[index], μ[index],
        predictive_variance[index]) for index in eachindex(μ))
end

function model_tournament(world, config)
    fits = Dict(model => fit_model(model, world.training, config)
        for model in MODELS)
    scores = Dict(model => fits[model].elbo for model in MODELS)
    heldout = Dict(model => heldout_score(fits[model], world, config)
        for model in MODELS)
    selected = argmax(scores)
    best_control = max(heldout[:global_downweight], heldout[:cue_local])
    return (fits = fits, scores = scores, heldout = heldout,
        selected = selected,
        split_heldout_margin = heldout[:context_split] - best_control)
end

function root_world(seed, config)
    rng = MersenneTwister(seed + 500_000)
    bundle_pattern = (1.0, 0.82, 0.65, 0.92)
    observations = [collect(bundle_pattern) .+
        config.root_observation_sd .* randn(rng, length(CUES))
        for _ in 1:config.root_sessions]
    contacts = 0.90 .+ config.contact_sd .* randn(rng, config.root_sessions)
    return (observations = observations, contacts = contacts)
end

function arm_profile(arm)
    arm == :witnessing && return (
        field = (1.00, 0.92, 0.78, 0.96), contact = 0.90)
    arm == :open_field_informational && return (
        field = (0.92, 1.00, 0.84, 0.93), contact = 0.78)
    arm == :regulation_only && return (
        field = (0.13, 0.13, 0.13, 0.13), contact = 0.12)
    arm == :narrowed_contact && return (
        field = (0.72, 0.04, 0.04, 0.04), contact = 0.10)
    arm == :matched_fixed_context && return (
        field = (0.22, 0.22, 0.22, 0.22), contact = 0.16)
    arm == :reversed_graph && return (
        field = (0.18, 0.16, 0.12, 0.15), contact = -0.05)
    error("unknown arm $arm")
end

function infer_root_trajectory(data, arm, config)
    profile = arm_profile(arm)
    log_odds = logit(config.root_prior_positive)
    path = Float64[]
    # Identity root g is the only state updated here. Every increment is a
    # likelihood ratio from an observation; no arm-specific root assignment
    # or repeated-contact update is present.
    for session in 1:config.root_sessions
        for channel in eachindex(CUES)
            observation = data.observations[session][channel]
            precision = profile.field[channel] / config.root_observation_sd^2
            log_odds += precision * (
                -0.5(observation - 1.0)^2 + 0.5(observation + 1.0)^2)
        end
        contact = data.contacts[session]
        contact_precision = abs(profile.contact) / config.contact_sd^2
        positive_mean = profile.contact >= 0 ? 0.90 : -0.90
        negative_mean = -positive_mean
        log_odds += contact_precision * (
            -0.5(contact - positive_mean)^2 + 0.5(contact - negative_mean)^2)
        push!(path, logistic(log_odds))
    end
    crossing = findfirst(>=(config.revision_probability), path)
    begun = findfirst(>=(config.revision_begun_probability), path)
    return (path = path, final = last(path),
        crossing = isnothing(crossing) ? config.root_sessions + 1 : crossing,
        begun = isnothing(begun) ? config.root_sessions + 1 : begun)
end

function loggamma_positive(z)
    z > 0 || throw(DomainError(z, "log-gamma approximation requires z > 0"))
    coefficients = (676.5203681218851, -1259.1392167224028,
        771.3234287776531, -176.6150291621406, 12.507343278686905,
        -0.13857109526572012, 9.984369578019572e-6,
        1.5056327351493116e-7)
    if z < 0.5
        return log(pi) - log(sin(pi * z)) - loggamma_positive(1 - z)
    end
    shifted = z - 1
    series = 0.99999999999980993
    for (index, coefficient) in enumerate(coefficients)
        series += coefficient / (shifted + index)
    end
    t = shifted + length(coefficients) - 0.5
    return 0.5log(2pi) + (shifted + 0.5) * log(t) - t + log(series)
end

logbeta(a, b) =
    loggamma_positive(a) + loggamma_positive(b) - loggamma_positive(a + b)

function bernoulli_log_evidence(success_weight, failure_weight, alpha)
    return logbeta(alpha + success_weight, alpha + failure_weight) -
        logbeta(alpha, alpha)
end

function reduction_log_bayes(catastrophes, noncatastrophes, contexts,
        weights, config)
    then_cat = sum(weights[index] * catastrophes[index]
        for index in eachindex(contexts) if contexts[index] == -1; init = 0.0)
    then_ok = sum(weights[index] * noncatastrophes[index]
        for index in eachindex(contexts) if contexts[index] == -1; init = 0.0)
    now_cat = sum(weights[index] * catastrophes[index]
        for index in eachindex(contexts) if contexts[index] == 1; init = 0.0)
    now_ok = sum(weights[index] * noncatastrophes[index]
        for index in eachindex(contexts) if contexts[index] == 1; init = 0.0)
    full = bernoulli_log_evidence(then_cat, then_ok, config.beta_prior) +
        bernoulli_log_evidence(now_cat, now_ok, config.beta_prior)
    reduced = bernoulli_log_evidence(then_cat + now_cat, then_ok + now_ok,
        config.beta_prior)
    return reduced - full
end

function doover_arm(seed, root, config)
    rng = MersenneTwister(seed + 600_000)
    initial_then = 5
    contexts = vcat(fill(-1, initial_then), fill(1, config.root_sessions))
    catastrophes = vcat(ones(initial_then), zeros(config.root_sessions))
    noncatastrophes = 1 .- catastrophes
    # Small observational noise is represented as fractional Bernoulli counts.
    jitter = 0.03 .* rand(rng, length(contexts))
    catastrophes .= clamp.(catastrophes .+ (2rand(rng, length(contexts)) .- 1) .* jitter,
        0.0, 1.0)
    noncatastrophes .= 1 .- catastrophes
    weights = ones(length(contexts))
    baseline_path = Float64[]
    for external_session in 1:config.root_sessions
        endpoint = initial_then + external_session
        push!(baseline_path, reduction_log_bayes(
            catastrophes[1:endpoint], noncatastrophes[1:endpoint],
            contexts[1:endpoint], weights[1:endpoint], config))
    end
    baseline_time = something(findfirst(>=(config.reduction_log_bayes_threshold),
        baseline_path), config.root_sessions + 1)
    post_time = config.root_sessions + 1
    post_insert = min(root.begun, config.root_sessions)
    post_path = Float64[]
    for external_session in 1:config.root_sessions
        endpoint = initial_then + external_session
        local_contexts = copy(contexts[1:endpoint])
        local_cat = copy(catastrophes[1:endpoint])
        local_ok = copy(noncatastrophes[1:endpoint])
        local_weights = copy(weights[1:endpoint])
        if external_session >= post_insert
            append!(local_contexts, fill(-1, config.doover_packets))
            append!(local_cat, zeros(config.doover_packets))
            append!(local_ok, ones(config.doover_packets))
            append!(local_weights, fill(config.imaginal_weight,
                config.doover_packets))
        end
        push!(post_path, reduction_log_bayes(local_cat, local_ok,
            local_contexts, local_weights, config))
    end
    post_time = something(findfirst(>=(config.reduction_log_bayes_threshold),
        post_path), config.root_sessions + 1)

    premature_session = 1
    endpoint = initial_then + premature_session
    before = reduction_log_bayes(catastrophes[1:endpoint],
        noncatastrophes[1:endpoint], contexts[1:endpoint],
        weights[1:endpoint], config)
    premature_contexts = vcat(contexts[1:endpoint],
        fill(-1, config.doover_packets))
    premature_cat = vcat(catastrophes[1:endpoint],
        zeros(config.doover_packets))
    premature_ok = 1 .- premature_cat
    premature_weights = vcat(weights[1:endpoint],
        fill(config.imaginal_weight, config.doover_packets))
    after = reduction_log_bayes(premature_cat, premature_ok,
        premature_contexts, premature_weights, config)
    premature_failed = after < config.reduction_log_bayes_threshold
    premature_reversed = after < before
    shortening = baseline_time > config.root_sessions ? 0.0 :
        max(0.0, (baseline_time - post_time) / baseline_time)
    return (baseline_time = baseline_time, post_time = post_time,
        shortening = shortening, premature_before = before,
        premature_after = after, premature_failed = premature_failed,
        premature_reversed = premature_reversed)
end

function complexity_audit(config = ContextSplitConfig())
    prior_entropy = 0.5config.parameter_count *
        log(2pi * exp(1) * config.prior_variance)
    return (
        global_downweight = (active_parameters = 10,
            regression_parameters = 9, transition_parameters = 0,
            precision_parameters = 1,
            prior_entropy = prior_entropy),
        cue_local = (active_parameters = 10, regression_parameters = 10,
            transition_parameters = 0, precision_parameters = 0,
            prior_entropy = prior_entropy),
        context_split = (active_parameters = 10, regression_parameters = 9,
            transition_parameters = 1, precision_parameters = 0,
            prior_entropy = prior_entropy),
        matched = config.parameter_count == 10,
    )
end

function run_seed(seed; stage, config = ContextSplitConfig())
    structured = generate_world(seed, true, config)
    no_structure = generate_world(seed, false, config)
    structured_result = model_tournament(structured, config)
    null_result = model_tournament(no_structure, config)
    root_data = root_world(seed, config)
    roots = Dict(arm => infer_root_trajectory(root_data, arm, config)
        for arm in ARMS)
    fixed_context = infer_root_trajectory(root_data, :matched_fixed_context,
        config)
    reversed = infer_root_trajectory(root_data, :reversed_graph, config)
    doover = doover_arm(seed, roots[:witnessing], config)
    organization = "bundle(self,world,policy,outcome)+couplings+precisions+field_profile"
    carrier = "none; no independently parameterized substrate enters this experiment"
    return (
        stage = String(stage), seed = seed,
        structured_selected = String(structured_result.selected),
        null_selected = String(null_result.selected),
        structured_split_selected =
            structured_result.selected == :context_split,
        null_split_selected = null_result.selected == :context_split,
        structured_split_margin = structured_result.split_heldout_margin,
        null_split_margin = null_result.split_heldout_margin,
        global_elbo = structured_result.scores[:global_downweight],
        cue_local_elbo = structured_result.scores[:cue_local],
        split_elbo = structured_result.scores[:context_split],
        global_complexity =
            structured_result.fits[:global_downweight].complexity,
        cue_local_complexity = structured_result.fits[:cue_local].complexity,
        split_complexity = structured_result.fits[:context_split].complexity,
        learned_then_stay = structured_result.fits[:context_split].
            context_fit.transition[1],
        learned_now_stay = structured_result.fits[:context_split].
            context_fit.transition[2],
        witnessing_final_root = roots[:witnessing].final,
        open_final_root = roots[:open_field_informational].final,
        regulation_final_root = roots[:regulation_only].final,
        narrowed_final_root = roots[:narrowed_contact].final,
        witnessing_time = roots[:witnessing].crossing,
        open_time = roots[:open_field_informational].crossing,
        regulation_time = roots[:regulation_only].crossing,
        narrowed_time = roots[:narrowed_contact].crossing,
        fixed_context_final_root = fixed_context.final,
        reversed_final_root = reversed.final,
        baseline_reduction_time = doover.baseline_time,
        post_doover_reduction_time = doover.post_time,
        doover_shortening = doover.shortening,
        premature_log_bayes_before = doover.premature_before,
        premature_log_bayes_after = doover.premature_after,
        premature_failed = doover.premature_failed,
        premature_reversed = doover.premature_reversed,
        organization_register = organization,
        carrier_register = carrier,
    )
end

function meanfield(rows, field)
    return mean(Float64(getfield(row, field)) for row in rows)
end

function summarize_rows(rows)
    return (
        worlds = length(rows),
        structured_split_selected = count(row.structured_split_selected
            for row in rows),
        null_split_selected = count(row.null_split_selected for row in rows),
        mean_structured_split_margin =
            meanfield(rows, :structured_split_margin),
        mean_null_split_margin = meanfield(rows, :null_split_margin),
        mean_witnessing_final_root = meanfield(rows, :witnessing_final_root),
        mean_open_final_root = meanfield(rows, :open_final_root),
        mean_regulation_final_root = meanfield(rows, :regulation_final_root),
        mean_narrowed_final_root = meanfield(rows, :narrowed_final_root),
        mean_doover_shortening = meanfield(rows, :doover_shortening),
        premature_failures = count(row.premature_failed for row in rows),
        premature_reversals = count(row.premature_reversed for row in rows),
    )
end

function criteria_verdicts(rows)
    summary = summarize_rows(rows)
    required_successes = ceil(Int, 0.80length(rows))
    allowed_null_wins = floor(Int, 0.20length(rows))
    criterion_1 = summary.structured_split_selected >= required_successes &&
        summary.null_split_selected <= allowed_null_wins
    criterion_2 = summary.mean_structured_split_margin >= 0.05
    high = mean((row.witnessing_final_root +
        row.open_final_root) / 2 for row in rows)
    low = mean((row.regulation_final_root +
        row.narrowed_final_root) / 2 for row in rows)
    pair_close = mean(abs(row.witnessing_final_root -
        row.open_final_root) for row in rows) <= 0.12
    low_pair_close = mean(abs(row.regulation_final_root -
        row.narrowed_final_root) for row in rows) <= 0.12
    criterion_3 = pair_close && low_pair_close && high - low >= 0.30
    criterion_4 = summary.mean_doover_shortening >= 0.20 &&
        summary.premature_failures >= required_successes
    return (
        criterion_1_selectivity = criterion_1,
        criterion_2_heldout_margin = criterion_2,
        criterion_3_derived_ordering = criterion_3,
        criterion_4_doover_timing = criterion_4,
        overall = criterion_1 && criterion_2 && criterion_3 && criterion_4,
        ordering_high_minus_low = high - low,
        witnessing_open_mean_difference = mean(abs(
            row.witnessing_final_root - row.open_final_root) for row in rows),
        regulation_narrowed_mean_difference = mean(abs(
            row.regulation_final_root - row.narrowed_final_root) for row in rows),
    )
end

function magic_numbers(config = ContextSplitConfig())
    return [
        ("training_observations", config.training_observations,
            "Enough repeated cue/context encounters to estimate all ten coordinates."),
        ("heldout_observations", config.heldout_observations,
            "Half the training budget; never used for fitting or freeze tuning."),
        ("parameter_count", config.parameter_count,
            "Capacity is fixed equally across all three model classes."),
        ("prior_variance", config.prior_variance,
            "Identical zero-mean Gaussian parameter prior in every class."),
        ("observation_sd", config.observation_sd,
            "Keeps behavior informative without making context perfectly separable."),
        ("context_marker_sd", config.context_marker_sd,
            "Makes context latent but inferable rather than observed as a label."),
        ("context_effect", config.context_effect,
            "World-level separation between past-valid and present-valid behavior."),
        ("transition_stay_probability", config.transition_stay_probability,
            "Produces persistent contexts while retaining learnable transitions."),
        ("root_sessions", config.root_sessions,
            "Common external evidence budget for every revision arm."),
        ("root_prior_positive", config.root_prior_positive,
            "Represents the initially frozen negative identity inference."),
        ("root_observation_sd", config.root_observation_sd,
            "Shared bundle observation noise for all revision arms."),
        ("contact_sd", config.contact_sd,
            "Experiment-43-style interpersonal observation remains informative but noisy."),
        ("revision_begun_probability", config.revision_begun_probability,
            "Timing marker fixed before the do-over comparison."),
        ("revision_probability", config.revision_probability,
            "Common posterior crossing used for time-to-revision."),
        ("reduction_log_bayes_threshold", config.reduction_log_bayes_threshold,
            "Positive evidence threshold for selecting the reduced burden model."),
        ("doover_packets", config.doover_packets,
            "Fixed internally generated counterfactual ending budget."),
        ("imaginal_weight", config.imaginal_weight,
            "Flags imaginal packets as less precise than external observations."),
        ("beta_prior", config.beta_prior,
            "Uniform catastrophe-rate prior in full and reduced models."),
    ]
end

end
