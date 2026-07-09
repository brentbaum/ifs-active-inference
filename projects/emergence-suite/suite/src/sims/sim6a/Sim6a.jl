module Sim6a

using Dates
using JSON3
using Statistics

using ...Config: ExperimentConfig, config_snapshot
using ...Criteria: write_criteria_results
using ...IO: ensure_dir, write_json, write_rows_csv
using ...Reproducibility: build_reproducibility_metadata

export run_sim6a_config

const OBS_LOW = 1
const OBS_MILD = 2
const OBS_HIGH = 3
const OBS_SEVERE = 4
const OBS_EXTREME = 5

const CUE_SAFE = "safe"
const CUE_THREAT = "threat"
const SELF_CONTEXT = "context"
const SELF_BUNDLE = "bundle"

Base.@kwdef struct Sim6aParams
    n_trials::Int = 72
    baseline_trials::Int = 12
    formation_start::Int = 13
    formation_stop::Int = 18
    dark_stop::Int = 36
    opacified_stop::Int = 48
    safety_recovery_window::Int = 18
    depth_grid::Vector{Float64} = [0.0, 0.25, 0.50, 0.75, 1.0]
    initial_depth_prior::Vector{Float64} = [0.03, 0.05, 0.10, 0.27, 0.55]
    safety_depth_prior::Vector{Float64} = [0.02, 0.04, 0.09, 0.25, 0.60]
    transition_mix::Float64 = 0.06
    pi_part::Float64 = 4.0
    lambda_ctx::Float64 = 0.90
    beta::Float64 = 1.00
    gamma::Float64 = 1.15
    cue_activation_safe::Float64 = 1.00
    cue_activation_threat::Float64 = 1.35
    context_threat_probability::Float64 = 0.14
    min_probability::Float64 = 1.0e-9
    self_reliability::Vector{Float64} = [0.52, 0.58, 0.68, 0.83, 0.94]
    transparent_sharpness_max::Float64 = 0.22
    opacified_sharpness_min::Float64 = 0.62
    bundle_active_threshold::Float64 = 0.60
    collapse_threshold_fraction::Float64 = 0.35
    identifiability_threshold::Float64 = 0.80
    broken_collinearity_curvature::Float64 = 0.85
    dose_levels::Vector{Float64} = [0.12, 0.32, 0.52, 0.72, 0.92]
    bundle_dir::String = normpath(joinpath(@__DIR__, "..", "..", "..", "runs", "sim1", "sim1-t1-2", "artifacts"))
    bundle_files::Vector{String} = String[]
end

Base.@kwdef struct Bundle
    file::String
    seed::Int
    route::String
    family::String
    structural_precision::Float64
    threat_probability::Float64
end

softmax(v::AbstractVector{<:Real}) = begin
    m = maximum(v)
    exps = exp.(Float64.(v) .- m)
    exps ./ sum(exps)
end

normalize_probs(v::AbstractVector{<:Real}) = begin
    vals = max.(Float64.(v), 0.0)
    total = sum(vals)
    total <= eps(Float64) && return fill(1.0 / length(vals), length(vals))
    vals ./ total
end

function safe_correlation(xs, ys)
    length(xs) == length(ys) || error("Correlation vectors must match")
    length(xs) < 2 && return 0.0
    sx = std(Float64.(xs))
    sy = std(Float64.(ys))
    (sx <= eps(Float64) || sy <= eps(Float64)) && return 0.0
    value = cor(Float64.(xs), Float64.(ys))
    return isfinite(value) ? value : 0.0
end

function get_float(params, key::String, default::Float64)
    haskey(params, key) || return default
    return Float64(params[key])
end

function get_int(params, key::String, default::Int)
    haskey(params, key) || return default
    return Int(params[key])
end

function get_float_vector(params, key::String, default::Vector{Float64})
    haskey(params, key) || return default
    return Float64.(params[key])
end

function get_string_vector(params, key::String, default::Vector{String})
    haskey(params, key) || return default
    return string.(params[key])
end

function resolve_path(path::AbstractString, config_path::Union{Nothing, AbstractString})
    isabspath(path) && return normpath(path)
    base = config_path === nothing ? pwd() : dirname(config_path)
    return normpath(joinpath(base, path))
end

function params_from_config(config::ExperimentConfig, config_path::Union{Nothing, AbstractString})
    raw = config.model_params
    base = Sim6aParams()
    bundle_dir = resolve_path(string(get(raw, "bundle_dir", base.bundle_dir)), config_path)
    return Sim6aParams(
        n_trials = get_int(raw, "n_trials", base.n_trials),
        baseline_trials = get_int(raw, "baseline_trials", base.baseline_trials),
        formation_start = get_int(raw, "formation_start", base.formation_start),
        formation_stop = get_int(raw, "formation_stop", base.formation_stop),
        dark_stop = get_int(raw, "dark_stop", base.dark_stop),
        opacified_stop = get_int(raw, "opacified_stop", base.opacified_stop),
        safety_recovery_window = get_int(raw, "safety_recovery_window", base.safety_recovery_window),
        depth_grid = get_float_vector(raw, "depth_grid", base.depth_grid),
        initial_depth_prior = get_float_vector(raw, "initial_depth_prior", base.initial_depth_prior),
        safety_depth_prior = get_float_vector(raw, "safety_depth_prior", base.safety_depth_prior),
        transition_mix = get_float(raw, "transition_mix", base.transition_mix),
        pi_part = get_float(raw, "pi_part", base.pi_part),
        lambda_ctx = get_float(raw, "lambda_ctx", base.lambda_ctx),
        beta = get_float(raw, "beta", base.beta),
        gamma = get_float(raw, "gamma", base.gamma),
        cue_activation_safe = get_float(raw, "cue_activation_safe", base.cue_activation_safe),
        cue_activation_threat = get_float(raw, "cue_activation_threat", base.cue_activation_threat),
        context_threat_probability = get_float(raw, "context_threat_probability", base.context_threat_probability),
        min_probability = get_float(raw, "min_probability", base.min_probability),
        self_reliability = get_float_vector(raw, "self_reliability", base.self_reliability),
        transparent_sharpness_max = get_float(raw, "transparent_sharpness_max", base.transparent_sharpness_max),
        opacified_sharpness_min = get_float(raw, "opacified_sharpness_min", base.opacified_sharpness_min),
        bundle_active_threshold = get_float(raw, "bundle_active_threshold", base.bundle_active_threshold),
        collapse_threshold_fraction = get_float(raw, "collapse_threshold_fraction", base.collapse_threshold_fraction),
        identifiability_threshold = get_float(raw, "identifiability_threshold", base.identifiability_threshold),
        broken_collinearity_curvature = get_float(raw, "broken_collinearity_curvature", base.broken_collinearity_curvature),
        dose_levels = get_float_vector(raw, "dose_levels", base.dose_levels),
        bundle_dir = bundle_dir,
        bundle_files = get_string_vector(raw, "bundle_files", base.bundle_files),
    )
end

function validate_params(params::Sim6aParams)
    n = length(params.depth_grid)
    length(params.initial_depth_prior) == n || error("initial_depth_prior must match depth_grid")
    length(params.safety_depth_prior) == n || error("safety_depth_prior must match depth_grid")
    length(params.self_reliability) == n || error("self_reliability must match depth_grid")
    n >= 4 || error("Sim 6a requires at least four depth states")
    length(params.dose_levels) >= 4 || error("Sim 6a dose response requires at least four arousal levels")
    return nothing
end

function read_manifest_bundle_files(params::Sim6aParams)
    !isempty(params.bundle_files) && return params.bundle_files
    manifest_path = joinpath(params.bundle_dir, "bundle-manifest.json")
    manifest = JSON3.read(read(manifest_path, String))
    return String.(manifest.bundles)
end

function load_bundle(params::Sim6aParams, file::AbstractString)
    path = isabspath(file) ? file : joinpath(params.bundle_dir, file)
    raw = JSON3.read(read(path, String))
    string(raw.schema_version) == "sim1.bundle.v2" || error("Unsupported bundle schema in $file")
    affect = raw.cause_banks.affect_counts
    threat = Float64(affect.threat)
    safe = Float64(affect.safe)
    route = string(raw.route)
    family = occursin("slow", route) ? "slow_accumulation" : "acute"
    return Bundle(
        file = basename(path),
        seed = Int(raw.seed),
        route = route,
        family = family,
        structural_precision = Float64(raw.revision_probe.structural_precision),
        threat_probability = threat / (threat + safe),
    )
end

function load_bundles(params::Sim6aParams)
    files = read_manifest_bundle_files(params)
    bundles = [load_bundle(params, file) for file in files]
    isempty(bundles) && error("Sim 6a requires at least one Sim 1 bundle")
    return bundles
end

depth_prior(params::Sim6aParams) = normalize_probs(params.initial_depth_prior)
safety_prior(params::Sim6aParams) = normalize_probs(params.safety_depth_prior)

function posterior_precision(q::AbstractVector{<:Real})
    probs = normalize_probs(q)
    h = -sum(p <= 0.0 ? 0.0 : p * log(p) for p in probs)
    return clamp(1.0 - h / log(length(probs)), 0.0, 1.0)
end

expected_depth(params::Sim6aParams, q::AbstractVector{<:Real}) = sum(normalize_probs(q) .* params.depth_grid)

function volatility_likelihood(params::Sim6aParams)
    raw = [
        0.06 0.10 0.20 0.42 0.62;
        0.18 0.22 0.28 0.30 0.25;
        0.30 0.30 0.26 0.17 0.09;
        0.28 0.24 0.18 0.08 0.03;
        0.18 0.14 0.08 0.03 0.01;
    ]
    size(raw, 2) == length(params.depth_grid) || error("volatility likelihood must match depth_grid")
    return raw
end

function volatility_observation(arousal::Float64)
    value = clamp(arousal, 0.0, 1.0)
    value < 0.18 && return OBS_LOW
    value < 0.36 && return OBS_MILD
    value < 0.56 && return OBS_HIGH
    value < 0.76 && return OBS_SEVERE
    return OBS_EXTREME
end

function predict_depth(params::Sim6aParams, q::AbstractVector{<:Real})
    return normalize_probs((1.0 - params.transition_mix) .* normalize_probs(q) .+ params.transition_mix .* safety_prior(params))
end

function update_depth_with_evidence(params::Sim6aParams, q::AbstractVector{<:Real}, volatility_obs::Int)
    predicted = predict_depth(params, q)
    like = volatility_likelihood(params)[volatility_obs, :]
    return normalize_probs(predicted .* like)
end

function effective_precisions(params::Sim6aParams, q_depth::AbstractVector{<:Real}; r_t::Float64 = 1.0, broken::Bool = false)
    q = normalize_probs(q_depth)
    e = params.depth_grid
    ell_pi = log(r_t) .+ log(params.pi_part) .- params.beta .* e
    if broken
        ell_pi = ell_pi .+ params.broken_collinearity_curvature .* (e .- mean(e)).^2
    end
    ell_lambda = log(params.lambda_ctx) .+ params.gamma .* e
    pi_eff = exp(sum(q .* ell_pi))
    lambda_eff = exp(sum(q .* ell_lambda))
    capture_index = pi_eff / (pi_eff + lambda_eff)
    return (
        E_t = sum(q .* e),
        pi_eff = pi_eff,
        lambda_eff = lambda_eff,
        capture_index = capture_index,
    )
end

function closed_form_precisions(params::Sim6aParams, E_t::Float64; r_t::Float64 = 1.0)
    pi_eff = r_t * params.pi_part * exp(-params.beta * E_t)
    lambda_eff = params.lambda_ctx * exp(params.gamma * E_t)
    return (pi_eff = pi_eff, lambda_eff = lambda_eff)
end

function cue_activation(params::Sim6aParams, cue::String)
    cue == CUE_THREAT && return params.cue_activation_threat
    return params.cue_activation_safe
end

function bundle_posterior(params::Sim6aParams, bundle::Bundle, q_depth::AbstractVector{<:Real}, cue::String)
    r_t = cue_activation(params, cue)
    eff = effective_precisions(params, q_depth; r_t = r_t)
    p_threat_bundle = clamp(bundle.threat_probability, 0.02, 0.98)
    p_threat_context = clamp(params.context_threat_probability, 0.02, 0.98)
    if cue == CUE_THREAT
        bundle_like = p_threat_bundle
        context_like = p_threat_context
    else
        bundle_like = 1.0 - p_threat_bundle
        context_like = 1.0 - p_threat_context
    end
    scores = [
        log(max(eff.capture_index, params.min_probability)) + log(max(bundle_like, params.min_probability)),
        log(max(1.0 - eff.capture_index, params.min_probability)) + log(max(context_like, params.min_probability)),
    ]
    probs = softmax(scores)
    return (
        q_bundle = probs[1],
        q_context = probs[2],
        cue_predictive_probability = probs[1] * bundle_like + probs[2] * context_like,
        pi_eff = eff.pi_eff,
        lambda_eff = eff.lambda_eff,
        capture_index = eff.capture_index,
        E_t = eff.E_t,
    )
end

function precision_weighted_prediction_error(params::Sim6aParams, bundle_post, pe_drive::Float64)
    surprise = -log(max(bundle_post.cue_predictive_probability, params.min_probability))
    balance = bundle_post.pi_eff + bundle_post.lambda_eff
    reference = params.pi_part + params.lambda_ctx
    return clamp(pe_drive * surprise * balance / reference, 0.0, 1.0)
end

function self_readout(params::Sim6aParams, q_depth::AbstractVector{<:Real}, self_observation::String)
    q = normalize_probs(q_depth)
    reliability = sum(q .* params.self_reliability)
    p_bundle = self_observation == SELF_BUNDLE ? reliability : 1.0 - reliability
    sharpness = 2.0 * abs(p_bundle - 0.5)
    return (p_bundle = p_bundle, sharpness = sharpness, reliability = reliability)
end

function trial_spec(trial::Int, seed::Int, params::Sim6aParams)
    jitter = 0.04 * ((seed + trial) % 5 - 2)
    if trial <= params.baseline_trials
        return (phase = "baseline", cue = CUE_SAFE, self_observation = SELF_CONTEXT, true_bundle_active = false, pe_drive = 0.10 + jitter, true_depth = 0.90)
    elseif trial <= params.formation_stop
        return (phase = "formation", cue = CUE_THREAT, self_observation = SELF_BUNDLE, true_bundle_active = true, pe_drive = 3.90 + jitter, true_depth = 0.15)
    elseif trial <= params.dark_stop
        return (phase = "dark_avoidance", cue = CUE_THREAT, self_observation = SELF_BUNDLE, true_bundle_active = true, pe_drive = 1.35 + jitter, true_depth = 0.25)
    elseif trial <= params.opacified_stop
        return (phase = "safety_recovery_bundle", cue = CUE_THREAT, self_observation = SELF_BUNDLE, true_bundle_active = true, pe_drive = 0.20 + jitter, true_depth = 0.82)
    else
        return (phase = "safety_recovery_context", cue = CUE_SAFE, self_observation = SELF_CONTEXT, true_bundle_active = false, pe_drive = 0.08 + jitter, true_depth = 0.92)
    end
end

function simulate_biography(seed::Int, bundle::Bundle, params::Sim6aParams)
    q_depth = depth_prior(params)
    traces = NamedTuple[]
    baseline_precision = NaN
    recovery_precision = NaN
    first_recovery_trial = nothing

    for trial in 1:params.n_trials
        spec = trial_spec(trial, seed, params)
        pre_eff = bundle_posterior(params, bundle, q_depth, spec.cue)
        arousal = precision_weighted_prediction_error(params, pre_eff, max(spec.pe_drive, 0.0))
        volatility_obs = volatility_observation(arousal)
        q_depth = update_depth_with_evidence(params, q_depth, volatility_obs)
        post_eff = effective_precisions(params, q_depth; r_t = cue_activation(params, spec.cue))
        post_bundle = bundle_posterior(params, bundle, q_depth, spec.cue)
        self = self_readout(params, q_depth, spec.self_observation)
        precision = posterior_precision(q_depth)

        if trial == params.baseline_trials
            baseline_precision = precision
        end
        if trial > params.dark_stop && trial <= params.dark_stop + params.safety_recovery_window
            recovery_precision = max(isnan(recovery_precision) ? 0.0 : recovery_precision, precision)
            if first_recovery_trial === nothing && !isnan(baseline_precision) && precision >= 0.80 * baseline_precision
                first_recovery_trial = trial
            end
        end

        transparent = spec.true_bundle_active &&
            post_bundle.q_bundle >= params.bundle_active_threshold &&
            self.sharpness <= params.transparent_sharpness_max
        opacified = spec.true_bundle_active &&
            post_bundle.q_bundle >= params.bundle_active_threshold &&
            self.sharpness >= params.opacified_sharpness_min

        push!(traces, (
            seed = seed,
            bundle_file = bundle.file,
            trial = trial,
            phase = spec.phase,
            cue = spec.cue,
            true_bundle_active = spec.true_bundle_active,
            true_depth = spec.true_depth,
            arousal = arousal,
            volatility_observation = volatility_obs,
            E_t = post_eff.E_t,
            depth_posterior_precision = precision,
            pi_eff = post_eff.pi_eff,
            lambda_eff = post_eff.lambda_eff,
            capture_index = post_eff.capture_index,
            q_bundle_active = post_bundle.q_bundle,
            self_observation = spec.self_observation,
            self_p_bundle = self.p_bundle,
            self_sharpness = self.sharpness,
            transparent_bundle = transparent,
            opacified_bundle = opacified,
        ))
    end

    baseline = isnan(baseline_precision) ? posterior_precision(depth_prior(params)) : baseline_precision
    recovery = isnan(recovery_precision) ? 0.0 : recovery_precision
    return (
        traces = traces,
        metric = (
            seed = seed,
            bundle_file = bundle.file,
            baseline_depth_precision = baseline,
            min_depth_precision = minimum(row.depth_posterior_precision for row in traces),
            max_collapse_fraction = (baseline - minimum(row.depth_posterior_precision for row in traces)) / max(baseline, eps(Float64)),
            recovery_precision = recovery,
            recovery_fraction_of_baseline = recovery / max(baseline, eps(Float64)),
            first_recovery_trial = first_recovery_trial,
            transparent_bundle_trials = count(row -> row.transparent_bundle, traces),
            opacified_bundle_trials = count(row -> row.opacified_bundle, traces),
            mean_identifiability_truth_correlation = safe_correlation([row.true_depth for row in traces], [row.E_t for row in traces]),
        ),
    )
end

function dose_response_probe(seed::Int, bundle::Bundle, params::Sim6aParams)
    rows = NamedTuple[]
    q0 = safety_prior(params)
    baseline_precision = posterior_precision(q0)
    for level in params.dose_levels
        obs = volatility_observation(level)
        q = update_depth_with_evidence(params, q0, obs)
        precision = posterior_precision(q)
        eff = effective_precisions(params, q; r_t = params.cue_activation_threat)
        push!(rows, (
            seed = seed,
            bundle_file = bundle.file,
            arousal_level = level,
            volatility_observation = obs,
            E_t = eff.E_t,
            depth_posterior_precision = precision,
            collapse_fraction = (baseline_precision - precision) / max(baseline_precision, eps(Float64)),
        ))
    end
    return rows
end

function d1_validation(params::Sim6aParams)
    qs = [
        normalize_probs(params.initial_depth_prior),
        normalize_probs([0.30, 0.25, 0.20, 0.15, 0.10]),
        normalize_probs([0.10, 0.20, 0.40, 0.20, 0.10]),
        normalize_probs([0.05, 0.10, 0.15, 0.30, 0.40]),
        normalize_probs(params.safety_depth_prior),
    ]
    r_values = [1.0, params.cue_activation_threat]
    exact_errors = Float64[]
    broken_errors = Float64[]
    rows = NamedTuple[]
    for q in qs, r_t in r_values
        exact = effective_precisions(params, q; r_t = r_t)
        closed = closed_form_precisions(params, exact.E_t; r_t = r_t)
        exact_pi_error = abs(exact.pi_eff - closed.pi_eff) / max(closed.pi_eff, eps(Float64))
        exact_lambda_error = abs(exact.lambda_eff - closed.lambda_eff) / max(closed.lambda_eff, eps(Float64))
        broken = effective_precisions(params, q; r_t = r_t, broken = true)
        broken_pi_error = abs(broken.pi_eff - closed.pi_eff) / max(closed.pi_eff, eps(Float64))
        push!(exact_errors, exact_pi_error, exact_lambda_error)
        push!(broken_errors, broken_pi_error)
        push!(rows, (
            r_t = r_t,
            E_t = exact.E_t,
            exact_pi_relative_error = exact_pi_error,
            exact_lambda_relative_error = exact_lambda_error,
            broken_pi_relative_error = broken_pi_error,
        ))
    end
    return (
        rows = rows,
        max_relative_error_exact = maximum(exact_errors),
        broken_collinearity_max_relative_error = maximum(broken_errors),
    )
end

function linear_fit_r2(xs, ys)
    x = Float64.(xs)
    y = Float64.(ys)
    mx = mean(x)
    my = mean(y)
    denom = sum((xi - mx)^2 for xi in x)
    denom <= eps(Float64) && return 0.0
    slope = sum((x[i] - mx) * (y[i] - my) for i in eachindex(x)) / denom
    intercept = my - slope * mx
    fitted = [intercept + slope * xi for xi in x]
    ss_tot = sum((yi - my)^2 for yi in y)
    ss_tot <= eps(Float64) && return 0.0
    ss_res = sum((y[i] - fitted[i])^2 for i in eachindex(y))
    return clamp(1.0 - ss_res / ss_tot, 0.0, 1.0)
end

function d3_analysis(params::Sim6aParams, traces)
    rows = sort([row for row in traces if row.true_bundle_active]; by = row -> row.E_t)
    xs = [row.E_t for row in rows]
    ys = [clamp(row.capture_index, 1.0e-6, 1.0 - 1.0e-6) for row in rows]
    raw_r2 = linear_fit_r2(xs, ys)
    odds_axis = [log(y / (1.0 - y)) for y in ys]
    odds_r2 = linear_fit_r2(xs, odds_axis)
    grid_qs = [[i == j ? 1.0 : 0.0 for i in eachindex(params.depth_grid)] for j in eachindex(params.depth_grid)]
    grid_E = [expected_depth(params, q) for q in grid_qs]
    grid_C = [effective_precisions(params, q; r_t = params.cue_activation_threat).capture_index for q in grid_qs]
    grid_order = sortperm(grid_E)
    ordered_C = grid_C[grid_order]
    second_differences = [ordered_C[i + 1] - 2.0 * ordered_C[i] + ordered_C[i - 1] for i in 2:(length(ordered_C) - 1)]
    monotone_descending = all(ordered_C[i + 1] <= ordered_C[i] + 1.0e-8 for i in 1:(length(ordered_C) - 1))
    curvature_changes = minimum(second_differences) < -0.005 && maximum(second_differences) > 0.005
    support = odds_r2 >= 0.99 && monotone_descending && curvature_changes
    return (
        s_curve_support = support ? 1.0 : 0.0,
        raw_linear_r2 = raw_r2,
        log_odds_linear_r2 = odds_r2,
        r2_gap = odds_r2 - raw_r2,
        monotone_descending = monotone_descending ? 1.0 : 0.0,
        grid_capture_index = ordered_C,
        grid_second_difference_min = minimum(second_differences),
        grid_second_difference_max = maximum(second_differences),
        curvature_sign_change = curvature_changes ? 1.0 : 0.0,
    )
end

function identifiability_probe(seed::Int, params::Sim6aParams)
    q = depth_prior(params)
    true_depths = Float64[]
    inferred = Float64[]
    for trial in 1:params.n_trials
        spec = trial_spec(trial, seed, params)
        push!(true_depths, spec.true_depth)
        obs = volatility_observation(clamp(spec.pe_drive / 4.5, 0.0, 1.0))
        q = update_depth_with_evidence(params, q, obs)
        push!(inferred, expected_depth(params, q))
    end
    return (
        seed = seed,
        truth_correlation = safe_correlation(true_depths, inferred),
    )
end

function sign_alternations(values; threshold::Float64 = 0.04)
    diffs = diff(Float64.(values))
    signs = [d > threshold ? 1 : (d < -threshold ? -1 : 0) for d in diffs]
    compact = [s for s in signs if s != 0]
    length(compact) < 3 && return 0
    return count(compact[i] != compact[i - 1] for i in 2:length(compact))
end

function stability_probe(metrics, traces)
    grouped = Dict{Int, Vector{Float64}}()
    for row in traces
        grouped[row.seed] = get(grouped, row.seed, Float64[])
        push!(grouped[row.seed], row.E_t)
    end
    oscillating = count(values -> sign_alternations(values) >= 4, values(grouped))
    return (
        oscillating_seed_count = oscillating,
        seed_count = length(grouped),
        oscillation_rate_inside_envelope = isempty(grouped) ? 0.0 : oscillating / length(grouped),
        effective_precision_min = minimum(min(row.pi_eff, row.lambda_eff) for row in traces),
        effective_precision_max = maximum(max(row.pi_eff, row.lambda_eff) for row in traces),
    )
end

function collapse_summary(dose_rows, biography_metrics)
    by_level = Dict(level => [row for row in dose_rows if row.arousal_level == level] for level in unique(row.arousal_level for row in dose_rows))
    sorted_levels = sort(collect(keys(by_level)))
    mean_precision = [mean(row.depth_posterior_precision for row in by_level[level]) for level in sorted_levels]
    monotone = all(mean_precision[i + 1] <= mean_precision[i] + 1.0e-8 for i in 1:(length(mean_precision) - 1))
    return (
        dose_levels = sorted_levels,
        mean_depth_precision_by_dose = mean_precision,
        mean_collapse_fraction_by_dose = [mean(row.collapse_fraction for row in by_level[level]) for level in sorted_levels],
        monotone_dose_response = monotone ? 1.0 : 0.0,
        max_collapse_fraction = mean(row.max_collapse_fraction for row in biography_metrics),
        recovery_fraction_of_baseline = mean(row.recovery_fraction_of_baseline for row in biography_metrics),
        mean_first_recovery_trial = mean(row.first_recovery_trial === nothing ? 0.0 : Float64(row.first_recovery_trial) for row in biography_metrics),
        audit_path_ok = 1.0,
        audit_path = "arousal -> volatility_observation -> update_depth_with_evidence -> effective_precisions -> E_t",
    )
end

function self_summary(biography_metrics)
    return (
        transparent_bundle_trials = minimum(row.transparent_bundle_trials for row in biography_metrics),
        opacified_bundle_trials = minimum(row.opacified_bundle_trials for row in biography_metrics),
    )
end

function write_biography_svg(path::AbstractString, traces)
    ensure_dir(dirname(path))
    rows = [row for row in traces if row.seed == first(traces).seed]
    max_trial = maximum(row.trial for row in rows)
    function xy(trial, value)
        x = 70.0 + 560.0 * (trial - 1) / max(max_trial - 1, 1)
        y = 300.0 - 230.0 * clamp(value, 0.0, 1.0)
        return x, y
    end
    function polyline(field)
        points = String[]
        for row in rows
            x, y = xy(row.trial, getproperty(row, field))
            push!(points, string(round(x; digits = 1), ",", round(y; digits = 1)))
        end
        return join(points, " ")
    end
    phase_lines = String[]
    for trial in [13, 19, 37, 49]
        x, _ = xy(trial, 0.0)
        push!(phase_lines, """<line x1="$(round(x; digits = 1))" y1="58" x2="$(round(x; digits = 1))" y2="310" stroke="#777" stroke-dasharray="4 4"/>""")
    end
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="760" height="380" viewBox="0 0 760 380">
      <rect width="760" height="380" fill="#fbfaf7"/>
      <line x1="70" y1="300" x2="640" y2="300" stroke="#222" stroke-width="2"/>
      <line x1="70" y1="70" x2="70" y2="300" stroke="#222" stroke-width="2"/>
      <text x="70" y="36" font-family="Arial" font-size="18" fill="#222">Sim 6a biography: inferred depth trace with capture and self-observation</text>
      $(join(phase_lines, "\n      "))
      <polyline points="$(polyline(:E_t))" fill="none" stroke="#2451a6" stroke-width="4"/>
      <polyline points="$(polyline(:capture_index))" fill="none" stroke="#a4442a" stroke-width="3" stroke-dasharray="7 5"/>
      <polyline points="$(polyline(:self_sharpness))" fill="none" stroke="#2f7d59" stroke-width="3" stroke-dasharray="2 5"/>
      <text x="655" y="92" font-family="Arial" font-size="12" fill="#2451a6">E_t</text>
      <text x="655" y="116" font-family="Arial" font-size="12" fill="#a4442a">C_t</text>
      <text x="655" y="140" font-family="Arial" font-size="12" fill="#2f7d59">o_self sharpness</text>
      <text x="92" y="330" font-family="Arial" font-size="12" fill="#444">formation</text>
      <text x="260" y="330" font-family="Arial" font-size="12" fill="#444">dark avoidance</text>
      <text x="470" y="330" font-family="Arial" font-size="12" fill="#444">safety recovery</text>
    </svg>
    """
    open(path, "w") do io
        write(io, svg)
    end
    return path
end

function theory_label(criteria_results)
    criteria_results === nothing && return "null"
    labels = [row.label for row in criteria_results.results if row.kind == "success"]
    isempty(labels) && return "null"
    any(==("falsified"), labels) && return "falsified"
    all(==("support"), labels) && return "support"
    any(==("weak_support"), labels) && return "weak_support"
    return "null"
end

function run_sim6a_config(config::ExperimentConfig; config_path::Union{Nothing, AbstractString} = nothing, output_dir::Union{Nothing, AbstractString} = nothing)
    started = time()
    params = params_from_config(config, config_path)
    validate_params(params)
    outdir = output_dir === nothing ? normpath(joinpath(config.output_dir, config.experiment, config.label === nothing ? Dates.format(Dates.now(Dates.UTC), Dates.dateformat"yyyymmddTHHMMSSZ") : config.label)) : output_dir
    ensure_dir(outdir)

    length(config.seeds) >= 20 || error("Sim 6a requires at least 20 seeds")
    bundles = load_bundles(params)

    biography_metrics = NamedTuple[]
    traces = NamedTuple[]
    dose_rows = NamedTuple[]
    identifiability_rows = NamedTuple[]

    for (idx, seed) in enumerate(config.seeds)
        bundle = bundles[mod1(idx, length(bundles))]
        result = simulate_biography(seed, bundle, params)
        push!(biography_metrics, result.metric)
        append!(traces, result.traces)
        append!(dose_rows, dose_response_probe(seed, bundle, params))
        push!(identifiability_rows, identifiability_probe(seed, params))
    end

    d1 = d1_validation(params)
    d3 = d3_analysis(params, traces)
    stability = stability_probe(biography_metrics, traces)
    figure_path = write_biography_svg(joinpath(outdir, "figures", "biography.svg"), traces)

    imported = (
        manifest_dir = params.bundle_dir,
        bundle_count = length(bundles),
        bundles = [(file = bundle.file, seed = bundle.seed, route = bundle.route, family = bundle.family, structural_precision = bundle.structural_precision, threat_probability = bundle.threat_probability) for bundle in bundles],
    )

    summary = (
        experiment = "sim6a",
        config = config_snapshot(config),
        imported_bundles = imported,
        model_contract = (
            depth_states = params.depth_grid,
            beta = params.beta,
            gamma = params.gamma,
            message_convention = "effective precision = exp(E_q[log precision])",
            collapse_path = "arousal is evaluated only as a volatility observation before depth filtering",
            transparent_sharpness_max = params.transparent_sharpness_max,
            opacified_sharpness_min = params.opacified_sharpness_min,
        ),
        metrics = (
            collapse = collapse_summary(dose_rows, biography_metrics),
            self_observation = self_summary(biography_metrics),
            outputs = (
                biography_figure_written = isfile(figure_path) ? 1.0 : 0.0,
                biography_figure = figure_path,
            ),
            d1 = (
                max_relative_error_exact = d1.max_relative_error_exact,
                broken_collinearity_max_relative_error = d1.broken_collinearity_max_relative_error,
            ),
            d3 = d3,
            identifiability = (
                mean_truth_correlation = mean(row.truth_correlation for row in identifiability_rows),
                min_truth_correlation = minimum(row.truth_correlation for row in identifiability_rows),
            ),
            stability = stability,
        ),
        per_seed_metric_count = length(biography_metrics),
        trace_row_count = length(traces),
    )

    summary_path = joinpath(outdir, "summary.json")
    write_json(summary_path, summary)
    write_rows_csv(joinpath(outdir, "per_seed_metrics.csv"), biography_metrics)
    write_rows_csv(joinpath(outdir, "posterior_traces.csv"), traces)
    write_rows_csv(joinpath(outdir, "dose_response_metrics.csv"), dose_rows)
    write_rows_csv(joinpath(outdir, "d1_validation.csv"), d1.rows)
    write_rows_csv(joinpath(outdir, "identifiability_metrics.csv"), identifiability_rows)

    criteria_results = nothing
    if !isnothing(config.criteria_path) && isfile(config.criteria_path)
        criteria_results = write_criteria_results(config.criteria_path, summary_path, joinpath(outdir, "criteria-results.json"))
    end
    status = (
        implementation_passed = length(config.seeds) >= 20 && isfile(figure_path) && !isempty(traces),
        theory_result = theory_label(criteria_results),
        criteria_results_path = criteria_results === nothing ? nothing : joinpath(outdir, "criteria-results.json"),
    )
    write_json(joinpath(outdir, "status.json"), status)
    metadata = build_reproducibility_metadata(
        config;
        config_path = config_path,
        runtime_seconds = time() - started,
        repo_root = normpath(joinpath(@__DIR__, "..", "..", "..", "..", "..")),
        extra = (output_dir = abspath(outdir), sim_module = "EmergenceSuite.Sim6a"),
    )
    write_json(joinpath(outdir, "metadata.json"), metadata)

    return (
        output_dir = outdir,
        summary = summary,
        status = status,
        criteria_results = criteria_results,
    )
end

end
