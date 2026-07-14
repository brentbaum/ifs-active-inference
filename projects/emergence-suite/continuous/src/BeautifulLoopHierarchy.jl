module BeautifulLoopHierarchy

using LinearAlgebra
using Random
using Statistics
using Main.GlobalPrecisionField

export LoopConfig, generate_hierarchy, infer_hierarchy, run_beautiful_loop_fidelity

Base.@kwdef struct LoopConfig
    seeds::Vector{Int} = collect(8301:8320)
    samples::Int = 120
    training_samples::Int = 28
    iterations::Int = 24
    hyper_newton_steps::Int = 16
    observation_precision::Float64 = 4.0
    global_variance::Float64 = 0.55
    local_variance::Float64 = 0.20
    ridge::Float64 = 1.0e-4
    training_contexts::Vector{Float64} = [-1.0, -0.4, 0.2, 0.8]
    test_context::Float64 = 1.4
    context_intercept::Float64 = 0.10
    context_slope::Float64 = 0.70
    layer_offsets::Vector{Float64} = [0.15, -0.10, 0.05]
end

function generate_hierarchy(seed::Int, true_phi::AbstractVector{<:Real};
        context_state::Float64 = 0.0, samples::Union{Nothing,Int} = nothing,
        config::LoopConfig = LoopConfig())
    length(true_phi) == 3 || error("true_phi must have one log precision per hierarchical link")
    sample_count = isnothing(samples) ? config.samples : samples
    rng = MersenneTwister(seed)
    latent = zeros(3, sample_count)
    observations = zeros(3, sample_count)
    transition_sd = exp.(-0.5 .* Float64.(true_phi))
    observation_sd = inv(sqrt(config.observation_precision))
    for sample in 1:sample_count
        latent[3, sample] = context_state + transition_sd[3] * randn(rng)
        latent[2, sample] = latent[3, sample] + transition_sd[2] * randn(rng)
        latent[1, sample] = latent[2, sample] + transition_sd[1] * randn(rng)
        observations[:, sample] .= latent[:, sample] .+ observation_sd .* randn(rng, 3)
    end
    return (observations = observations, latent = latent, context_state = context_state,
        true_phi = Float64.(true_phi))
end

function precision_map(global_model::Bool)
    if global_model
        # y = (global precision state, three layer deviations), Phi = A*y.
        return [1.0 1.0 0.0 0.0; 1.0 0.0 1.0 0.0; 1.0 0.0 0.0 1.0]
    end
    return Matrix{Float64}(I, 3, 3)
end

function hyper_prior(global_model::Bool, prior_phi::AbstractVector{<:Real}, config::LoopConfig)
    phi = Float64.(prior_phi)
    length(phi) == 3 || error("prior_phi must have length three")
    if global_model
        global_mean = mean(phi)
        mean_y = [global_mean; phi .- global_mean]
        covariance_y = Diagonal([config.global_variance; fill(config.local_variance, 3)]) |> Matrix
        return mean_y, covariance_y, precision_map(true)
    end
    marginal_variance = config.global_variance + config.local_variance
    return phi, Matrix{Float64}(I, 3, 3) * marginal_variance, precision_map(false)
end

function state_posterior(observation, context_state, expected_precision, config::LoopConfig)
    posterior_precision = Matrix{Float64}(I, 3, 3) * config.observation_precision
    information = config.observation_precision .* observation
    links = ([1.0, -1.0, 0.0], [0.0, 1.0, -1.0], [0.0, 0.0, 1.0])
    for layer in 1:3
        posterior_precision .+= expected_precision[layer] .* (links[layer] * links[layer]')
    end
    information .+= expected_precision[3] .* context_state .* links[3]
    covariance = inv(Symmetric(posterior_precision))
    return covariance * information, Matrix(covariance)
end

function state_statistics(episode, expected_precision, config::LoopConfig)
    samples = size(episode.observations, 2)
    means = zeros(3, samples)
    residuals = zeros(3)
    observation_error = zeros(3)
    covariance = zeros(3, 3)
    for (sample, observation) in enumerate(eachcol(episode.observations))
        mean_state, covariance = state_posterior(
            observation, episode.context_state, expected_precision, config)
        means[:, sample] .= mean_state
        residuals[1] += (mean_state[1] - mean_state[2])^2 +
            covariance[1, 1] + covariance[2, 2] - 2covariance[1, 2]
        residuals[2] += (mean_state[2] - mean_state[3])^2 +
            covariance[2, 2] + covariance[3, 3] - 2covariance[2, 3]
        residuals[3] += (mean_state[3] - episode.context_state)^2 + covariance[3, 3]
        observation_error .+= (observation .- mean_state).^2 .+ diag(covariance)
    end
    return (means = means, covariance = covariance, residuals = residuals ./ samples,
        observation_error = observation_error ./ samples)
end

function hyper_objective(y, covariance, prior_mean, prior_covariance, map_phi,
        residuals, active, samples)
    mean_phi = map_phi * y
    variance_phi = diag(map_phi * covariance * map_phi')
    evidence = 0.5samples * sum(active .* (
        exp.(mean_phi .+ 0.5 .* variance_phi) .* residuals .- mean_phi))
    return gaussian_kl(y, covariance, prior_mean, prior_covariance) + evidence
end

function variational_hyper_update(prior_mean, prior_covariance, map_phi, residuals, active,
        samples, initial_mean, initial_covariance, config::LoopConfig)
    prior_precision = inv(Symmetric(prior_covariance))
    y = copy(initial_mean)
    covariance = copy(initial_covariance)
    active_float = Float64.(active)
    for _ in 1:config.hyper_newton_steps
        mean_phi = map_phi * y
        variance_phi = diag(map_phi * covariance * map_phi')
        weighted = active_float .* exp.(mean_phi .+ 0.5 .* variance_phi) .* residuals
        gradient = prior_precision * (y - prior_mean) +
            0.5samples .* map_phi' * (weighted .- active_float)
        hessian = prior_precision + 0.5samples .* map_phi' * Diagonal(weighted) * map_phi
        step = hessian \ gradient
        proposed_covariance = inv(Symmetric(hessian))
        norm(step) < 1.0e-9 && norm(proposed_covariance - covariance) < 1.0e-9 && break
        current = hyper_objective(
            y, covariance, prior_mean, prior_covariance, map_phi,
            residuals, active_float, samples)
        scale = 1.0
        while scale > 1.0e-5
            candidate = y - scale .* step
            candidate_covariance = (1 - scale) .* covariance .+ scale .* proposed_covariance
            proposed = hyper_objective(
                candidate, candidate_covariance, prior_mean, prior_covariance, map_phi,
                residuals, active_float, samples)
            if proposed <= current
                y = candidate
                covariance = candidate_covariance
                break
            end
            scale *= 0.5
        end
    end
    return y, Matrix(covariance)
end

function gaussian_kl(mean_q, covariance_q, mean_p, covariance_p)
    dimensions = length(mean_q)
    precision_p = inv(Symmetric(covariance_p))
    delta = mean_q - mean_p
    return 0.5 * (tr(precision_p * covariance_q) + dot(delta, precision_p * delta) - dimensions +
        logdet(covariance_p) - logdet(covariance_q))
end

function free_energy_terms(stats, mean_y, covariance_y, prior_mean, prior_covariance,
        map_phi, active, config::LoopConfig, samples)
    mean_phi = map_phi * mean_y
    covariance_phi = map_phi * covariance_y * map_phi'
    expected_precision = exp.(mean_phi .+ 0.5 .* diag(covariance_phi))
    transition_energy = 0.5samples .* (
        log(2pi) .- mean_phi .+ expected_precision .* stats.residuals)
    observation_energy = 0.5samples .* (log(2pi) - log(config.observation_precision) .+
        config.observation_precision .* stats.observation_error)
    marginal_entropy = 0.5samples .* (1 + log(2pi) .+ log.(diag(stats.covariance)))
    local_energy = observation_energy .+ transition_energy .- marginal_entropy
    observation = sum(observation_energy)
    state_entropy = 0.5samples * (3 * (1 + log(2pi)) + logdet(stats.covariance))
    hyper_complexity = gaussian_kl(mean_y, covariance_y, prior_mean, prior_covariance)
    hyper_free_energy = sum(Float64.(active) .* transition_energy) + hyper_complexity
    joint = observation + sum(transition_energy) - state_entropy + hyper_complexity
    return (local_energy = local_energy, observation = observation, state_entropy = state_entropy,
        hyper_complexity = hyper_complexity, hyper_free_energy = hyper_free_energy, joint = joint,
        mean_phi = mean_phi, covariance_phi = covariance_phi,
        expected_precision = expected_precision)
end

function infer_hierarchy(episode; global_model::Bool = true, active = ones(3),
        prior_phi = zeros(3), config::LoopConfig = LoopConfig())
    prior_mean, prior_covariance, map_phi = hyper_prior(global_model, prior_phi, config)
    mean_y = copy(prior_mean)
    covariance_y = copy(prior_covariance)
    trace = NamedTuple[]
    final_stats = nothing
    for iteration in 1:config.iterations
        mean_phi = map_phi * mean_y
        covariance_phi = map_phi * covariance_y * map_phi'
        expected_precision = exp.(mean_phi .+ 0.5 .* diag(covariance_phi))
        stats = state_statistics(episode, expected_precision, config)
        mean_y, covariance_y = variational_hyper_update(
            prior_mean, prior_covariance, map_phi, stats.residuals, active,
            size(episode.observations, 2), mean_y, covariance_y, config)
        mean_phi = map_phi * mean_y
        covariance_phi = map_phi * covariance_y * map_phi'
        expected_precision = exp.(mean_phi .+ 0.5 .* diag(covariance_phi))
        final_stats = state_statistics(episode, expected_precision, config)
        energy = free_energy_terms(final_stats, mean_y, covariance_y,
            prior_mean, prior_covariance, map_phi, active, config,
            size(episode.observations, 2))
        push!(trace, (
            iteration = iteration,
            phi_1 = energy.mean_phi[1], phi_2 = energy.mean_phi[2], phi_3 = energy.mean_phi[3],
            residual_1 = final_stats.residuals[1], residual_2 = final_stats.residuals[2],
            residual_3 = final_stats.residuals[3],
            local_free_energy_1 = energy.local_energy[1], local_free_energy_2 = energy.local_energy[2],
            local_free_energy_3 = energy.local_energy[3], observation_free_energy = energy.observation,
            state_entropy = energy.state_entropy, hyper_complexity = energy.hyper_complexity,
            hyper_free_energy = energy.hyper_free_energy,
            joint_free_energy = energy.joint,
        ))
    end
    mean_phi = map_phi * mean_y
    covariance_phi = map_phi * covariance_y * map_phi'
    return (phi = mean_phi, phi_covariance = covariance_phi,
        expected_precision = exp.(mean_phi .+ 0.5 .* diag(covariance_phi)),
        state_means = final_stats.means, trace = trace,
        posterior_mean = mean_y, posterior_covariance = covariance_y,
        prior_mean = prior_mean, prior_covariance = prior_covariance, map_phi = map_phi)
end

function fit_context_forecast(contexts, estimates; global_model::Bool, ridge::Float64)
    context_count = length(contexts)
    size(estimates) == (3, context_count) || error("estimates must be a 3 x contexts matrix")
    columns = global_model ? 4 : 6
    design = zeros(3context_count, columns)
    target = zeros(3context_count)
    row = 0
    for (context_index, context) in enumerate(contexts), layer in 1:3
        row += 1
        target[row] = estimates[layer, context_index]
        design[row, layer] = 1.0
        if global_model
            design[row, 4] = context
        else
            design[row, 3 + layer] = context
        end
    end
    penalty = Matrix{Float64}(I, columns, columns) * ridge
    return (design' * design + penalty) \ (design' * target)
end

function predict_context(coefficients, context; global_model::Bool)
    if global_model
        return coefficients[1:3] .+ coefficients[4] .* context
    end
    return coefficients[1:3] .+ coefficients[4:6] .* context
end

rmse(estimate, truth) = sqrt(mean((estimate .- truth) .^ 2))

function context_truth(context, config::LoopConfig)
    return config.layer_offsets .+ config.context_intercept .+ config.context_slope .* context
end

function run_context_switch(seed::Int, config::LoopConfig)
    estimates = zeros(3, length(config.training_contexts))
    for (index, context) in enumerate(config.training_contexts)
        truth = context_truth(context, config)
        episode = generate_hierarchy(seed + 100index, truth;
            context_state = context, samples = config.training_samples, config = config)
        estimates[:, index] .= infer_hierarchy(
            episode; global_model = false, config = config).phi
    end
    global_coefficients = fit_context_forecast(
        config.training_contexts, estimates; global_model = true, ridge = config.ridge)
    local_coefficients = fit_context_forecast(
        config.training_contexts, estimates; global_model = false, ridge = config.ridge)
    global_forecast = predict_context(global_coefficients, config.test_context; global_model = true)
    local_forecast = predict_context(local_coefficients, config.test_context; global_model = false)
    truth = context_truth(config.test_context, config)
    test_episode = generate_hierarchy(seed + 9000, truth;
        context_state = config.test_context, samples = config.samples, config = config)
    global_early = infer_hierarchy(test_episode; global_model = true, active = [1, 0, 0],
        prior_phi = global_forecast, config = config)
    local_early = infer_hierarchy(test_episode; global_model = false, active = [1, 0, 0],
        prior_phi = local_forecast, config = config)
    global_full = infer_hierarchy(test_episode; global_model = true, active = ones(3),
        prior_phi = global_forecast, config = config)
    local_full = infer_hierarchy(test_episode; global_model = false, active = ones(3),
        prior_phi = local_forecast, config = config)
    return (
        seed = seed,
        global_forecast_error = rmse(global_forecast, truth),
        local_forecast_error = rmse(local_forecast, truth),
        global_early_heldout_error = rmse(global_early.phi[2:3], truth[2:3]),
        local_early_heldout_error = rmse(local_early.phi[2:3], truth[2:3]),
        global_early_state_rmse = rmse(global_early.state_means, test_episode.latent),
        local_early_state_rmse = rmse(local_early.state_means, test_episode.latent),
        global_full_phi_error = rmse(global_full.phi, truth),
        local_full_phi_error = rmse(local_full.phi, truth),
        local_relearning_gain = rmse(local_early.phi, truth) - rmse(local_full.phi, truth),
        global_trace = global_early.trace,
    )
end

function run_beautiful_loop_fidelity(output_dir::AbstractString =
        joinpath(@__DIR__, "..", "results", "beautiful_loop_hierarchy");
        config::LoopConfig = LoopConfig())
    mkpath(output_dir)
    rows = NamedTuple[]
    traces = NamedTuple[]
    for seed in config.seeds
        result = run_context_switch(seed, config)
        push!(rows, (
            seed = result.seed,
            global_forecast_error = result.global_forecast_error,
            local_forecast_error = result.local_forecast_error,
            global_early_heldout_error = result.global_early_heldout_error,
            local_early_heldout_error = result.local_early_heldout_error,
            global_early_state_rmse = result.global_early_state_rmse,
            local_early_state_rmse = result.local_early_state_rmse,
            global_full_phi_error = result.global_full_phi_error,
            local_full_phi_error = result.local_full_phi_error,
            local_relearning_gain = result.local_relearning_gain,
        ))
        for trace_row in result.global_trace
            push!(traces, merge((seed = seed, condition = "global_early_switch"), trace_row))
        end
    end
    metric_keys = Tuple(filter(!=(:seed), keys(first(rows))))
    means = NamedTuple{metric_keys}(Tuple(
        mean(getfield(row, key) for row in rows) for key in metric_keys))
    win_rates = (
        global_forecast = mean(row.global_forecast_error < row.local_forecast_error for row in rows),
        early_global_precision = mean(row.global_early_heldout_error < row.local_early_heldout_error for row in rows),
        early_global_state = mean(row.global_early_state_rmse < row.local_early_state_rmse for row in rows),
        local_relearning = mean(row.local_relearning_gain > 0 for row in rows),
    )
    example_truth = context_truth(config.test_context, config)
    example = generate_hierarchy(first(config.seeds), example_truth; config = config)
    example_fit = infer_hierarchy(example; global_model = true, config = config)
    marginal_global = diag(example_fit.map_phi * example_fit.prior_covariance * example_fit.map_phi')
    _, local_prior_covariance, local_map = hyper_prior(false, zeros(3), config)
    marginal_local = diag(local_map * local_prior_covariance * local_map')
    criteria = (
        explicit_states_and_observations = size(example.latent, 1) == 3 &&
            size(example.observations) == size(example.latent),
        layer_precision_field = length(example_fit.phi) == 3,
        iterative_joint_inference = length(example_fit.trace) == config.iterations &&
            abs(first(example_fit.trace).joint_free_energy - last(example_fit.trace).joint_free_energy) > 1.0e-8,
        joint_free_energy_descends = all(diff(getfield.(
            example_fit.trace, :joint_free_energy)) .<= 1.0e-8),
        endogenous_second_order_errors = all(last(example_fit.trace)[Symbol("residual_$layer")] > 0 for layer in 1:3),
        local_and_joint_free_energy = all(isfinite(last(example_fit.trace)[field]) for field in
            (:local_free_energy_1, :local_free_energy_2, :local_free_energy_3,
                :hyper_free_energy, :joint_free_energy)),
        matched_local_ablation = maximum(abs.(marginal_global .- marginal_local)) < 1.0e-10,
        out_of_sample_global_forecast = means.global_forecast_error < means.local_forecast_error &&
            win_rates.global_forecast >= 0.80,
        early_global_precision_advantage = means.global_early_heldout_error < means.local_early_heldout_error &&
            win_rates.early_global_precision >= 0.75,
        early_global_state_advantage = means.global_early_state_rmse < means.local_early_state_rmse &&
            win_rates.early_global_state >= 0.75,
        local_loops_relearn = means.local_relearning_gain > 0 && win_rates.local_relearning >= 0.75,
    )
    summary = (
        experiment = "beautiful_loop_three_level_fidelity",
        protocol = "construction and out-of-sample context-switch test; not confirmatory",
        generative_model = "three-level linear Gaussian hierarchy with Gaussian variational q(Phi)",
        training_contexts = config.training_contexts,
        out_of_sample_context = config.test_context,
        mean_results = means,
        win_rates = win_rates,
        criteria = criteria,
    )
    GlobalPrecisionField.write_csv(joinpath(output_dir, "context_switch_per_seed.csv"), rows)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "variational_trace.csv"), traces)
    GlobalPrecisionField.write_json(joinpath(output_dir, "summary.json"), summary)
    GlobalPrecisionField.write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = all(values(criteria)),
        theory_result = all(values(criteria)) ?
            "global context forecast improves early inference before independent loops relearn" :
            "one or more Beautiful Loop fidelity criteria failed",
    ))
    return (rows = rows, traces = traces, summary = summary)
end

end
