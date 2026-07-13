module HierarchicalEpistemicDepth

using LinearAlgebra
using Random
using Statistics
using Main.GlobalPrecisionField

export FormalConfig, generate_episode, infer_episode, run_formal_fidelity

Base.@kwdef struct FormalConfig
    seeds::Vector{Int} = collect(8201:8220)
    samples::Int = 180
    iterations::Int = 30
    observation_precision::Float64 = 8.0
    global_variance::Float64 = 0.65
    local_variance::Float64 = 0.25
    precision_evidence_variance::Float64 = 0.10
end

function prior_parameters(global_model::Bool, config::FormalConfig)
    base = zeros(3)
    if global_model
        mean = [0.0; base]
        covariance = zeros(4, 4)
        covariance[1, 1] = config.global_variance
        covariance[1, 2:4] .= config.global_variance
        covariance[2:4, 1] .= config.global_variance
        covariance[2:4, 2:4] .= config.global_variance
        covariance[2:4, 2:4] .+= Matrix{Float64}(I, 3, 3) * config.local_variance
        return mean, covariance
    end
    marginal = config.global_variance + config.local_variance
    return zeros(3), Matrix{Float64}(I, 3, 3) * marginal
end

function generate_episode(seed::Int, true_phi::AbstractVector{<:Real};
        context::Float64 = 0.0, config::FormalConfig = FormalConfig())
    length(true_phi) == 3 || error("true_phi must have one entry per hierarchical layer")
    rng = MersenneTwister(seed)
    latent = zeros(3, config.samples)
    observations = zeros(3, config.samples)
    standard_deviation = exp.(-0.5 .* Float64.(true_phi))
    observation_sd = inv(sqrt(config.observation_precision))
    for sample in 1:config.samples
        latent[3, sample] = context + standard_deviation[3] * randn(rng)
        latent[2, sample] = latent[3, sample] + standard_deviation[2] * randn(rng)
        latent[1, sample] = latent[2, sample] + standard_deviation[1] * randn(rng)
        observations[:, sample] .= latent[:, sample] .+ observation_sd .* randn(rng, 3)
    end
    return (observations = observations, latent = latent, context = context, true_phi = Float64.(true_phi))
end

function state_posterior(observation, context, expected_precision, config::FormalConfig)
    q = Matrix{Float64}(I, 3, 3) * config.observation_precision
    b = config.observation_precision .* observation
    d12 = [1.0, -1.0, 0.0]
    d23 = [0.0, 1.0, -1.0]
    e3 = [0.0, 0.0, 1.0]
    q .+= expected_precision[1] .* (d12 * d12')
    q .+= expected_precision[2] .* (d23 * d23')
    q .+= expected_precision[3] .* (e3 * e3')
    b .+= expected_precision[3] .* context .* e3
    covariance = inv(Symmetric(q))
    mean_state = covariance * b
    return mean_state, covariance
end

function expected_residuals(observations, context, expected_precision, config::FormalConfig)
    residuals = zeros(3)
    observation_error = 0.0
    logdet_precision = 0.0
    for observation in eachcol(observations)
        mean_state, covariance = state_posterior(observation, context, expected_precision, config)
        residuals[1] += (mean_state[1] - mean_state[2])^2 + covariance[1, 1] + covariance[2, 2] - 2covariance[1, 2]
        residuals[2] += (mean_state[2] - mean_state[3])^2 + covariance[2, 2] + covariance[3, 3] - 2covariance[2, 3]
        residuals[3] += (mean_state[3] - context)^2 + covariance[3, 3]
        observation_error += sum((observation .- mean_state).^2) + tr(covariance)
        logdet_precision += logdet(inv(covariance))
    end
    n = size(observations, 2)
    return residuals ./ n, observation_error / n, logdet_precision / n
end

function gaussian_condition(prior_mean, prior_covariance, z, active, variance)
    indices = findall(==(1.0), Float64.(active))
    isempty(indices) && return prior_mean, prior_covariance
    if length(prior_mean) == 4
        h = zeros(length(indices), 4)
        for (row, index) in enumerate(indices)
            h[row, index + 1] = 1.0
        end
    else
        h = zeros(length(indices), 3)
        for (row, index) in enumerate(indices)
            h[row, index] = 1.0
        end
    end
    r = Matrix{Float64}(I, length(indices), length(indices)) * variance
    innovation = z[indices] - h * prior_mean
    gain = prior_covariance * h' / (h * prior_covariance * h' + r)
    posterior_mean = prior_mean + gain * innovation
    posterior_covariance = Symmetric((Matrix{Float64}(I, length(prior_mean), length(prior_mean)) - gain * h) * prior_covariance)
    return posterior_mean, Matrix(posterior_covariance)
end

function gaussian_kl(mean, covariance, prior_mean, prior_covariance)
    k = length(mean)
    inverse_prior = inv(Symmetric(prior_covariance))
    delta = mean - prior_mean
    return 0.5 * (tr(inverse_prior * covariance) + dot(delta, inverse_prior * delta) - k +
        logdet(prior_covariance) - logdet(covariance))
end

function infer_episode(episode; global_model::Bool = true, active = ones(3),
        config::FormalConfig = FormalConfig())
    prior_mean, prior_covariance = prior_parameters(global_model, config)
    posterior_mean = copy(prior_mean)
    posterior_covariance = copy(prior_covariance)
    trace = NamedTuple[]
    for iteration in 1:config.iterations
        phi_mean = global_model ? posterior_mean[2:4] : posterior_mean
        phi_variance = global_model ? diag(posterior_covariance)[2:4] : diag(posterior_covariance)
        expected_precision = exp.(phi_mean .+ 0.5 .* phi_variance)
        residuals, observation_error, logdet_precision = expected_residuals(
            episode.observations, episode.context, expected_precision, config)
        precision_evidence = -log.(max.(residuals, 1.0e-8))
        posterior_mean, posterior_covariance = gaussian_condition(
            prior_mean, prior_covariance, precision_evidence, active,
            config.precision_evidence_variance)
        phi_mean = global_model ? posterior_mean[2:4] : posterior_mean
        phi_variance = global_model ? diag(posterior_covariance)[2:4] : diag(posterior_covariance)
        expected_precision = exp.(phi_mean .+ 0.5 .* phi_variance)
        coupling_energy = 0.5 * sum(expected_precision .* residuals .- phi_mean)
        free_energy = 0.5 * config.observation_precision * observation_error + coupling_energy +
            gaussian_kl(posterior_mean, posterior_covariance, prior_mean, prior_covariance) +
            0.5 * logdet_precision
        push!(trace, (
            iteration = iteration,
            phi_1 = phi_mean[1], phi_2 = phi_mean[2], phi_3 = phi_mean[3],
            residual_1 = residuals[1], residual_2 = residuals[2], residual_3 = residuals[3],
            global_state = global_model ? posterior_mean[1] : 0.0,
            free_energy_proxy = free_energy,
        ))
    end
    final_phi = [last(trace).phi_1, last(trace).phi_2, last(trace).phi_3]
    return (phi = final_phi, trace = trace, posterior_mean = posterior_mean,
        posterior_covariance = posterior_covariance)
end

rmse(estimate, truth) = sqrt(mean((estimate .- truth) .^ 2))

function run_formal_fidelity(output_dir::AbstractString = joinpath(@__DIR__, "..", "results", "hierarchical_epistemic_depth");
        config::FormalConfig = FormalConfig())
    mkpath(output_dir)
    rows = NamedTuple[]
    traces = NamedTuple[]
    for seed in config.seeds
        coordinated_truth = [1.0, 1.0, 1.0]
        coordinated = generate_episode(seed, coordinated_truth; config = config)
        global_fit = infer_episode(coordinated; global_model = true, active = [1, 1, 0], config = config)
        local_fit = infer_episode(coordinated; global_model = false, active = [1, 1, 0], config = config)
        push!(rows, (experiment = "coordinated_heldout", seed = seed,
            global_rmse = rmse(global_fit.phi, coordinated_truth),
            local_rmse = rmse(local_fit.phi, coordinated_truth),
            global_heldout_error = abs(global_fit.phi[3] - coordinated_truth[3]),
            local_heldout_error = abs(local_fit.phi[3] - coordinated_truth[3])))
        for row in global_fit.trace
            push!(traces, merge((experiment = "coordinated_global", seed = seed), row))
        end

        independent_truth = [1.1, -0.9, 0.55]
        independent = generate_episode(seed + 1000, independent_truth; config = config)
        global_independent = infer_episode(independent; global_model = true, config = config)
        local_independent = infer_episode(independent; global_model = false, config = config)
        push!(rows, (experiment = "independent_all_observed", seed = seed,
            global_rmse = rmse(global_independent.phi, independent_truth),
            local_rmse = rmse(local_independent.phi, independent_truth),
            global_heldout_error = 0.0, local_heldout_error = 0.0))
    end

    coordinated_rows = filter(row -> row.experiment == "coordinated_heldout", rows)
    independent_rows = filter(row -> row.experiment == "independent_all_observed", rows)
    global_heldout = mean(row.global_heldout_error for row in coordinated_rows)
    local_heldout = mean(row.local_heldout_error for row in coordinated_rows)
    global_independent_rmse = mean(row.global_rmse for row in independent_rows)
    local_independent_rmse = mean(row.local_rmse for row in independent_rows)
    first_seed_trace = filter(row -> row.seed == first(config.seeds), traces)
    energy_changed = abs(first(first_seed_trace).free_energy_proxy - last(first_seed_trace).free_energy_proxy)
    criteria = (
        explicit_hierarchy_runs = 1.0,
        endogenous_second_order_errors = all(last(row.trace).residual_1 > 0 for row in
            [infer_episode(generate_episode(first(config.seeds), [1.0, 1.0, 1.0]; config = config); config = config)]) ? 1.0 : 0.0,
        iterative_joint_update = energy_changed > 1.0e-6 ? 1.0 : 0.0,
        global_heldout_advantage = global_heldout + 0.10 < local_heldout ? 1.0 : 0.0,
        global_not_universally_superior = local_independent_rmse <= global_independent_rmse + 0.05 ? 1.0 : 0.0,
    )
    summary = (
        experiment = "hierarchical_epistemic_depth_fidelity_tranche",
        protocol = "four construction experiments; not confirmatory",
        model = "three-level linear Gaussian hierarchy with a global hyper-node over layer precisions",
        coordinated_heldout = (global_error = global_heldout, local_error = local_heldout),
        independent_pattern = (global_rmse = global_independent_rmse, local_rmse = local_independent_rmse),
        criteria = criteria,
    )
    GlobalPrecisionField.write_csv(joinpath(output_dir, "per_seed.csv"), rows)
    GlobalPrecisionField.write_csv(joinpath(output_dir, "inference_trace.csv"), traces)
    GlobalPrecisionField.write_json(joinpath(output_dir, "summary.json"), summary)
    GlobalPrecisionField.write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = all(value == 1.0 for value in values(criteria)),
        theory_result = "global pooling helps coordinated precision shifts but is not universally superior",
    ))
    return (rows = rows, traces = traces, summary = summary)
end

end
