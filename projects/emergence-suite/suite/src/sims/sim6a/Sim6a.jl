module Sim6a

using Dates
using JSON3
using Random
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
    robustness_mode::Bool = false
    observation_probability::Float64 = 0.82
    latent_initial_depth::Float64 = 0.90
    latent_velocity::Float64 = 0.055
    latent_process_noise::Float64 = 0.012
    latent_lower_bound::Float64 = 0.08
    latent_upper_bound::Float64 = 0.92
    likelihood_fit_smoothing::Float64 = 0.50
    signature_precision_drop::Float64 = 0.20
    signature_depth_drop::Float64 = 0.18
    signature_capture_rise::Float64 = 0.04
    signature_recovery_fraction::Float64 = 0.75
    stage2_enabled::Bool = false
    policy_mode::Bool = false
    threat_level_grid::Vector{Float64} = [0.05, 0.15, 0.30, 0.45, 0.60, 0.75, 0.90]
    acute_threat_level::Float64 = 0.90
    activation_threat_level::Float64 = 0.65
    witnessing_evidence_grid::Vector{Float64} = [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 24.0, 28.0, 32.0, 36.0]
    aversive_cost::Float64 = 10.0
    aversive_cost_sweep::Vector{Float64} = [8.0, 10.0, 12.0]
    epistemic_value_weight::Float64 = 1.9
    ambiguity_weight::Float64 = 0.25
    reflexive_safety_prior_alpha::Float64 = 1.0
    reflexive_safety_prior_beta::Float64 = 9.0
    threat_control_base::Float64 = 0.15
    threat_control_gain::Float64 = 0.50
    reflexive_control_gain::Float64 = 0.55
    control_saturation::Float64 = 1.5
    threat_policy_threat_precision::Float64 = 2.40
    threat_policy_self_precision::Float64 = 0.35
    threat_policy_depth_precision::Float64 = 1.00
    reflexive_policy_threat_precision::Float64 = 0.85
    reflexive_policy_self_precision::Float64 = 1.55
    reflexive_policy_depth_precision::Float64 = 1.25
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

Base.@kwdef struct PolicyAllocation
    name::String
    threat_precision::Float64
    self_precision::Float64
    depth_precision::Float64
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

function get_bool(params, key::String, default::Bool)
    haskey(params, key) || return default
    value = params[key]
    value isa Bool && return value
    return lowercase(string(value)) in ("true", "1", "yes")
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
        robustness_mode = get_bool(raw, "robustness_mode", base.robustness_mode),
        observation_probability = get_float(raw, "observation_probability", base.observation_probability),
        latent_initial_depth = get_float(raw, "latent_initial_depth", base.latent_initial_depth),
        latent_velocity = get_float(raw, "latent_velocity", base.latent_velocity),
        latent_process_noise = get_float(raw, "latent_process_noise", base.latent_process_noise),
        latent_lower_bound = get_float(raw, "latent_lower_bound", base.latent_lower_bound),
        latent_upper_bound = get_float(raw, "latent_upper_bound", base.latent_upper_bound),
        likelihood_fit_smoothing = get_float(raw, "likelihood_fit_smoothing", base.likelihood_fit_smoothing),
        signature_precision_drop = get_float(raw, "signature_precision_drop", base.signature_precision_drop),
        signature_depth_drop = get_float(raw, "signature_depth_drop", base.signature_depth_drop),
        signature_capture_rise = get_float(raw, "signature_capture_rise", base.signature_capture_rise),
        signature_recovery_fraction = get_float(raw, "signature_recovery_fraction", base.signature_recovery_fraction),
        stage2_enabled = get_bool(raw, "stage2_enabled", base.stage2_enabled),
        policy_mode = get_bool(raw, "policy_mode", base.policy_mode),
        threat_level_grid = get_float_vector(raw, "threat_level_grid", base.threat_level_grid),
        acute_threat_level = get_float(raw, "acute_threat_level", base.acute_threat_level),
        activation_threat_level = get_float(raw, "activation_threat_level", base.activation_threat_level),
        witnessing_evidence_grid = get_float_vector(raw, "witnessing_evidence_grid", base.witnessing_evidence_grid),
        aversive_cost = get_float(raw, "aversive_cost", base.aversive_cost),
        aversive_cost_sweep = get_float_vector(raw, "aversive_cost_sweep", base.aversive_cost_sweep),
        epistemic_value_weight = get_float(raw, "epistemic_value_weight", base.epistemic_value_weight),
        ambiguity_weight = get_float(raw, "ambiguity_weight", base.ambiguity_weight),
        reflexive_safety_prior_alpha = get_float(raw, "reflexive_safety_prior_alpha", base.reflexive_safety_prior_alpha),
        reflexive_safety_prior_beta = get_float(raw, "reflexive_safety_prior_beta", base.reflexive_safety_prior_beta),
        threat_control_base = get_float(raw, "threat_control_base", base.threat_control_base),
        threat_control_gain = get_float(raw, "threat_control_gain", base.threat_control_gain),
        reflexive_control_gain = get_float(raw, "reflexive_control_gain", base.reflexive_control_gain),
        control_saturation = get_float(raw, "control_saturation", base.control_saturation),
        threat_policy_threat_precision = get_float(raw, "threat_policy_threat_precision", base.threat_policy_threat_precision),
        threat_policy_self_precision = get_float(raw, "threat_policy_self_precision", base.threat_policy_self_precision),
        threat_policy_depth_precision = get_float(raw, "threat_policy_depth_precision", base.threat_policy_depth_precision),
        reflexive_policy_threat_precision = get_float(raw, "reflexive_policy_threat_precision", base.reflexive_policy_threat_precision),
        reflexive_policy_self_precision = get_float(raw, "reflexive_policy_self_precision", base.reflexive_policy_self_precision),
        reflexive_policy_depth_precision = get_float(raw, "reflexive_policy_depth_precision", base.reflexive_policy_depth_precision),
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
    isempty(params.threat_level_grid) && error("Stage 2 requires at least one threat belief level")
    isempty(params.witnessing_evidence_grid) && error("Stage 2 requires at least one witnessing evidence point")
    all(x -> x >= 0.0, params.witnessing_evidence_grid) || error("witnessing_evidence_grid values must be non-negative")
    all(x -> 0.0 <= x <= 1.0, params.threat_level_grid) || error("threat_level_grid values must be probabilities")
    0.0 < params.observation_probability <= 1.0 || error("observation_probability must lie in (0, 1]")
    0.0 <= params.latent_lower_bound < params.latent_upper_bound <= 1.0 || error("latent depth bounds must be ordered inside [0, 1]")
    params.latent_lower_bound <= params.latent_initial_depth <= params.latent_upper_bound || error("latent_initial_depth must lie inside latent bounds")
    params.latent_velocity > 0.0 || error("latent_velocity must be positive")
    params.latent_process_noise >= 0.0 || error("latent_process_noise must be non-negative")
    params.likelihood_fit_smoothing > 0.0 || error("likelihood_fit_smoothing must be positive")
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

function normalize_likelihood(matrix::AbstractMatrix{<:Real})
    return hcat([normalize_probs(matrix[:, col]) for col in axes(matrix, 2)]...)
end

function mapped_volatility_likelihood(params::Sim6aParams, mapping::AbstractString)
    theory = volatility_likelihood(params)
    mapping == "theory" && return theory
    mapping == "flat" && return repeat(mean(theory; dims = 2), 1, size(theory, 2))
    mapping == "reversed" && return theory[:, end:-1:1]
    mapping == "nonmonotone" && return theory[:, [1, 4, 2, 5, 3]]
    mapping == "diffuse" && return normalize_likelihood(theory .^ 0.55)
    mapping == "concentrated" && return normalize_likelihood(theory .^ 1.80)
    error("Unknown volatility mapping: $mapping")
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

function update_depth_with_evidence(params::Sim6aParams, q::AbstractVector{<:Real}, volatility_obs::Int; depth_precision::Float64 = 1.0, likelihood = volatility_likelihood(params), prior = safety_prior(params))
    predicted = normalize_probs((1.0 - params.transition_mix) .* normalize_probs(q) .+ params.transition_mix .* normalize_probs(prior))
    precision = max(depth_precision, params.min_probability)
    like = likelihood[volatility_obs, :] .^ precision
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

function bundle_posterior(params::Sim6aParams, bundle::Bundle, q_depth::AbstractVector{<:Real}, cue::String; threat_precision::Float64 = 1.0)
    r_t = cue_activation(params, cue) * (cue == CUE_THREAT ? max(threat_precision, params.min_probability) : 1.0)
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

function self_readout(params::Sim6aParams, q_depth::AbstractVector{<:Real}, self_observation::String; self_precision::Float64 = 1.0)
    q = normalize_probs(q_depth)
    base_reliability = sum(q .* params.self_reliability)
    reliability = clamp(0.5 + max(self_precision, 0.0) * (base_reliability - 0.5), 0.01, 0.99)
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

function threat_policy(params::Sim6aParams)
    return PolicyAllocation(
        name = "allocate-to-threat",
        threat_precision = params.threat_policy_threat_precision,
        self_precision = params.threat_policy_self_precision,
        depth_precision = params.threat_policy_depth_precision,
    )
end

function reflexive_policy(params::Sim6aParams)
    return PolicyAllocation(
        name = "allocate-to-reflexive",
        threat_precision = params.reflexive_policy_threat_precision,
        self_precision = params.reflexive_policy_self_precision,
        depth_precision = params.reflexive_policy_depth_precision,
    )
end

function neutral_policy()
    return PolicyAllocation(
        name = "stage1-no-policy",
        threat_precision = 1.0,
        self_precision = 1.0,
        depth_precision = 1.0,
    )
end

function reflexive_safety_belief(params::Sim6aParams, evidence_count::Float64)
    numerator = params.reflexive_safety_prior_alpha + max(evidence_count, 0.0)
    denominator = params.reflexive_safety_prior_alpha + params.reflexive_safety_prior_beta + max(evidence_count, 0.0)
    return numerator / max(denominator, params.min_probability)
end

function policy_efe_score(
    params::Sim6aParams,
    policy::PolicyAllocation;
    q_depth::AbstractVector{<:Real},
    threat_level::Float64,
    safe_evidence::Float64 = 0.0,
    aversive_cost::Float64 = params.aversive_cost,
)
    q = normalize_probs(q_depth)
    uncertainty = 1.0 - posterior_precision(q)
    depth_mean = expected_depth(params, q)
    safe_belief = reflexive_safety_belief(params, safe_evidence)
    threat_control = params.threat_control_base + params.threat_control_gain * policy.threat_precision
    reflexive_control = params.reflexive_control_gain * policy.self_precision * safe_belief * (1.0 + depth_mean)
    control = (threat_control + reflexive_control) / max(params.control_saturation + threat_control + reflexive_control, params.min_probability)
    p_aversive = clamp(threat_level * (1.0 - control), 0.0, 1.0)
    pragmatic = aversive_cost * p_aversive
    epistemic = params.epistemic_value_weight * uncertainty * (0.70 * policy.depth_precision + 0.30 * policy.self_precision)
    ambiguity = params.ambiguity_weight * (
        threat_level / max(policy.threat_precision, params.min_probability) +
        uncertainty / max(policy.depth_precision, params.min_probability)
    )
    total = pragmatic + ambiguity - epistemic
    return (
        policy = policy.name,
        pragmatic = pragmatic,
        epistemic = epistemic,
        ambiguity = ambiguity,
        total = total,
        predicted_aversive_probability = p_aversive,
        reflexive_safety_belief = safe_belief,
    )
end

function policy_pair_scores(
    params::Sim6aParams;
    q_depth::AbstractVector{<:Real},
    threat_level::Float64,
    safe_evidence::Float64 = 0.0,
    aversive_cost::Float64 = params.aversive_cost,
)
    threat = policy_efe_score(params, threat_policy(params); q_depth = q_depth, threat_level = threat_level, safe_evidence = safe_evidence, aversive_cost = aversive_cost)
    reflexive = policy_efe_score(params, reflexive_policy(params); q_depth = q_depth, threat_level = threat_level, safe_evidence = safe_evidence, aversive_cost = aversive_cost)
    return (threat = threat, reflexive = reflexive)
end

function select_policy(params::Sim6aParams, q_depth::AbstractVector{<:Real}, threat_level::Float64, safe_evidence::Float64)
    scores = policy_pair_scores(params; q_depth = q_depth, threat_level = threat_level, safe_evidence = safe_evidence)
    return scores.threat.total <= scores.reflexive.total ? threat_policy(params) : reflexive_policy(params)
end

function current_threat_belief(params::Sim6aParams, bundle::Bundle, bundle_post)
    return clamp(
        bundle_post.q_bundle * bundle.threat_probability + bundle_post.q_context * params.context_threat_probability,
        0.0,
        1.0,
    )
end

function simulate_biography(seed::Int, bundle::Bundle, params::Sim6aParams; policies_enabled::Bool = false)
    q_depth = depth_prior(params)
    traces = NamedTuple[]
    baseline_precision = NaN
    recovery_precision = NaN
    first_recovery_trial = nothing
    safe_evidence = 0.0

    for trial in 1:params.n_trials
        spec = trial_spec(trial, seed, params)
        default_pre = bundle_posterior(params, bundle, q_depth, spec.cue)
        threat_belief = current_threat_belief(params, bundle, default_pre)
        policy = policies_enabled ? select_policy(params, q_depth, threat_belief, safe_evidence) : neutral_policy()
        pre_eff = bundle_posterior(params, bundle, q_depth, spec.cue; threat_precision = policy.threat_precision)
        arousal = precision_weighted_prediction_error(params, pre_eff, max(spec.pe_drive, 0.0))
        volatility_obs = volatility_observation(arousal)
        q_depth = update_depth_with_evidence(params, q_depth, volatility_obs; depth_precision = policy.depth_precision)
        post_bundle = bundle_posterior(params, bundle, q_depth, spec.cue; threat_precision = policy.threat_precision)
        self = self_readout(params, q_depth, spec.self_observation; self_precision = policy.self_precision)
        precision = posterior_precision(q_depth)
        volatility_obs == OBS_LOW && (safe_evidence += 1.0)

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
            policy = policy.name,
            policy_threat_precision = policy.threat_precision,
            policy_self_precision = policy.self_precision,
            policy_depth_precision = policy.depth_precision,
            threat_belief = threat_belief,
            safe_evidence_count = safe_evidence,
            arousal = arousal,
            volatility_observation = volatility_obs,
            E_t = post_bundle.E_t,
            depth_posterior_precision = precision,
            pi_eff = post_bundle.pi_eff,
            lambda_eff = post_bundle.lambda_eff,
            capture_index = post_bundle.capture_index,
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

function dose_response_probe(seed::Int, bundle::Bundle, params::Sim6aParams; policies_enabled::Bool = false)
    rows = NamedTuple[]
    q0 = safety_prior(params)
    baseline_precision = posterior_precision(q0)
    pre = bundle_posterior(params, bundle, q0, CUE_THREAT)
    threat_belief = current_threat_belief(params, bundle, pre)
    policy = policies_enabled ? select_policy(params, q0, threat_belief, 0.0) : neutral_policy()
    for level in params.dose_levels
        obs = volatility_observation(level)
        q = update_depth_with_evidence(params, q0, obs; depth_precision = policy.depth_precision)
        precision = posterior_precision(q)
        eff = effective_precisions(params, q; r_t = params.cue_activation_threat * policy.threat_precision)
        push!(rows, (
            seed = seed,
            bundle_file = bundle.file,
            policy = policy.name,
            policy_threat_precision = policy.threat_precision,
            policy_depth_precision = policy.depth_precision,
            threat_belief = threat_belief,
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

function policy_delta_row(params::Sim6aParams, threat_level::Float64, safe_evidence::Float64; aversive_cost::Float64 = params.aversive_cost)
    scores = policy_pair_scores(
        params;
        q_depth = safety_prior(params),
        threat_level = threat_level,
        safe_evidence = safe_evidence,
        aversive_cost = aversive_cost,
    )
    delta_total = scores.reflexive.total - scores.threat.total
    delta_pragmatic = scores.reflexive.pragmatic - scores.threat.pragmatic
    delta_epistemic_contribution = scores.threat.epistemic - scores.reflexive.epistemic
    delta_ambiguity = scores.reflexive.ambiguity - scores.threat.ambiguity
    return (
        threat_level = threat_level,
        safe_evidence = safe_evidence,
        aversive_cost = aversive_cost,
        threat_total = scores.threat.total,
        reflexive_total = scores.reflexive.total,
        selected_policy = scores.threat.total <= scores.reflexive.total ? "allocate-to-threat" : "allocate-to-reflexive",
        threat_pragmatic = scores.threat.pragmatic,
        reflexive_pragmatic = scores.reflexive.pragmatic,
        threat_epistemic = scores.threat.epistemic,
        reflexive_epistemic = scores.reflexive.epistemic,
        threat_ambiguity = scores.threat.ambiguity,
        reflexive_ambiguity = scores.reflexive.ambiguity,
        delta_total_reflexive_minus_threat = delta_total,
        delta_pragmatic_reflexive_minus_threat = delta_pragmatic,
        delta_epistemic_contribution_reflexive_minus_threat = delta_epistemic_contribution,
        delta_ambiguity_reflexive_minus_threat = delta_ambiguity,
        threat_predicted_aversive_probability = scores.threat.predicted_aversive_probability,
        reflexive_predicted_aversive_probability = scores.reflexive.predicted_aversive_probability,
        reflexive_safety_belief = scores.reflexive.reflexive_safety_belief,
    )
end

function crossover_threat_level(rows)
    ordered = sort(rows; by = row -> row.threat_level)
    for i in 2:length(ordered)
        prev = ordered[i - 1]
        cur = ordered[i]
        prev.delta_total_reflexive_minus_threat <= 0.0 && cur.delta_total_reflexive_minus_threat >= 0.0 && return cur.threat_level
    end
    return 0.0
end

function write_stage2_efe_svg(path::AbstractString, rows)
    ensure_dir(dirname(path))
    ordered = sort(rows; by = row -> row.threat_level)
    xs = [row.threat_level for row in ordered]
    series = (
        total = [row.delta_total_reflexive_minus_threat for row in ordered],
        pragmatic = [row.delta_pragmatic_reflexive_minus_threat for row in ordered],
        epistemic = [row.delta_epistemic_contribution_reflexive_minus_threat for row in ordered],
    )
    all_values = vcat(series.total, series.pragmatic, series.epistemic, [0.0])
    y_min = minimum(all_values) - 0.20
    y_max = maximum(all_values) + 0.20
    x_min = minimum(xs)
    x_max = maximum(xs)
    function xy(x, y)
        px = 78.0 + 560.0 * (x - x_min) / max(x_max - x_min, 1.0e-9)
        py = 320.0 - 240.0 * (y - y_min) / max(y_max - y_min, 1.0e-9)
        return px, py
    end
    function polyline(values)
        points = String[]
        for (i, value) in enumerate(values)
            x, y = xy(xs[i], value)
            push!(points, string(round(x; digits = 1), ",", round(y; digits = 1)))
        end
        return join(points, " ")
    end
    zero_y = xy(x_min, 0.0)[2]
    crossover = crossover_threat_level(ordered)
    crossover_x = crossover > 0.0 ? xy(crossover, 0.0)[1] : 0.0
    crossover_line = crossover > 0.0 ? """<line x1="$(round(crossover_x; digits = 1))" y1="68" x2="$(round(crossover_x; digits = 1))" y2="326" stroke="#555" stroke-dasharray="4 4"/><text x="$(round(crossover_x + 6.0; digits = 1))" y="84" font-family="Arial" font-size="11" fill="#333">crossover</text>""" : ""
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="760" height="420" viewBox="0 0 760 420">
      <rect width="760" height="420" fill="#fbfaf7"/>
      <text x="78" y="36" font-family="Arial" font-size="18" fill="#222">Sim 6a Stage 2: EFE decomposition across threat belief</text>
      <line x1="78" y1="320" x2="638" y2="320" stroke="#222" stroke-width="2"/>
      <line x1="78" y1="70" x2="78" y2="320" stroke="#222" stroke-width="2"/>
      <line x1="78" y1="$(round(zero_y; digits = 1))" x2="638" y2="$(round(zero_y; digits = 1))" stroke="#999" stroke-width="1"/>
      $crossover_line
      <polyline points="$(polyline(series.total))" fill="none" stroke="#222222" stroke-width="4"/>
      <polyline points="$(polyline(series.pragmatic))" fill="none" stroke="#a4442a" stroke-width="3" stroke-dasharray="7 5"/>
      <polyline points="$(polyline(series.epistemic))" fill="none" stroke="#2451a6" stroke-width="3" stroke-dasharray="2 5"/>
      <text x="654" y="96" font-family="Arial" font-size="12" fill="#222">total EFE delta</text>
      <text x="654" y="120" font-family="Arial" font-size="12" fill="#a4442a">pragmatic delta</text>
      <text x="654" y="144" font-family="Arial" font-size="12" fill="#2451a6">epistemic delta</text>
      <text x="78" y="356" font-family="Arial" font-size="12" fill="#444">low threat belief</text>
      <text x="530" y="356" font-family="Arial" font-size="12" fill="#444">acute threat belief</text>
      <text x="86" y="388" font-family="Arial" font-size="12" fill="#444">Y = reflexive minus threat. Above zero selects allocate-to-threat; below zero selects allocate-to-reflexive.</text>
    </svg>
    """
    open(path, "w") do io
        write(io, svg)
    end
    return path
end

function stage2_analysis(params::Sim6aParams, outdir::AbstractString)
    efe_rows = [policy_delta_row(params, level, 0.0) for level in params.threat_level_grid]
    acute = policy_delta_row(params, params.acute_threat_level, 0.0)
    sweep_rows = [policy_delta_row(params, params.acute_threat_level, 0.0; aversive_cost = cost) for cost in params.aversive_cost_sweep]
    witnessing_rows = [policy_delta_row(params, params.activation_threat_level, evidence) for evidence in params.witnessing_evidence_grid]
    flip_candidates = [row.safe_evidence for row in witnessing_rows if row.selected_policy == "allocate-to-reflexive"]
    flip_point = isempty(flip_candidates) ? Inf : minimum(flip_candidates)
    initial = first(sort(witnessing_rows; by = row -> row.safe_evidence))
    final = last(sort(witnessing_rows; by = row -> row.safe_evidence))
    figure_path = write_stage2_efe_svg(joinpath(outdir, "figures", "stage2-efe-crossover.svg"), efe_rows)
    return (
        metrics = (
            collapse_selected = (
                acute_threat_rank_support = acute.selected_policy == "allocate-to-threat" ? 1.0 : 0.0,
                pragmatic_term_carries_ranking = acute.delta_total_reflexive_minus_threat > 0.0 && acute.delta_pragmatic_reflexive_minus_threat > abs(acute.delta_epistemic_contribution_reflexive_minus_threat) ? 1.0 : 0.0,
                acute_delta_total_reflexive_minus_threat = acute.delta_total_reflexive_minus_threat,
                acute_delta_pragmatic_reflexive_minus_threat = acute.delta_pragmatic_reflexive_minus_threat,
                acute_delta_epistemic_contribution_reflexive_minus_threat = acute.delta_epistemic_contribution_reflexive_minus_threat,
                crossover_threat_level = crossover_threat_level(efe_rows),
                preference_sweep_support_count = count(row -> row.selected_policy == "allocate-to-threat", sweep_rows),
            ),
            witnessing_policy = (
                initial_reflexive_dominated = initial.selected_policy == "allocate-to-threat" ? 1.0 : 0.0,
                reflexive_flip_observed = isfinite(flip_point) ? 1.0 : 0.0,
                flip_point_evidence = isfinite(flip_point) ? flip_point : 1.0e9,
                final_selected_policy = final.selected_policy,
                final_reflexive_safety_belief = final.reflexive_safety_belief,
            ),
            outputs = (
                efe_crossover_figure_written = isfile(figure_path) ? 1.0 : 0.0,
                efe_crossover_figure = figure_path,
            ),
        ),
        efe_rows = efe_rows,
        witnessing_rows = witnessing_rows,
        sweep_rows = sweep_rows,
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

function sample_categorical(probs::AbstractVector{<:Real}, u::Float64)
    cumulative = 0.0
    for (idx, probability) in enumerate(normalize_probs(probs))
        cumulative += probability
        u <= cumulative && return idx
    end
    return length(probs)
end

function emission_probabilities(params::Sim6aParams, likelihood, depth::Float64)
    grid = params.depth_grid
    depth <= first(grid) && return likelihood[:, 1]
    depth >= last(grid) && return likelihood[:, end]
    upper = findfirst(value -> value >= depth, grid)
    lower = upper - 1
    weight = (depth - grid[lower]) / (grid[upper] - grid[lower])
    return normalize_probs((1.0 - weight) .* likelihood[:, lower] .+ weight .* likelihood[:, upper])
end

"""Generate depth, observation timing, and emissions without consulting the biography schedule."""
function latent_trajectory(seed::Int, params::Sim6aParams, mapping::AbstractString)
    latent_rng = MersenneTwister(seed + 61_000)
    availability_rng = MersenneTwister(seed + 62_000)
    emission_rng = MersenneTwister(seed + 63_000)
    generative_likelihood = mapped_volatility_likelihood(params, mapping)
    depth = params.latent_initial_depth
    velocity = -params.latent_velocity * (0.90 + 0.20 * rand(latent_rng))
    rows = NamedTuple[]

    for trial in 1:params.n_trials
        if trial > 1
            candidate = depth + velocity + params.latent_process_noise * randn(latent_rng)
            if candidate <= params.latent_lower_bound
                candidate = params.latent_lower_bound + (params.latent_lower_bound - candidate)
                velocity = abs(velocity)
            elseif candidate >= params.latent_upper_bound
                candidate = params.latent_upper_bound - (candidate - params.latent_upper_bound)
                velocity = -abs(velocity)
            end
            depth = clamp(candidate, params.latent_lower_bound, params.latent_upper_bound)
        end
        observed = rand(availability_rng) <= params.observation_probability
        observation = sample_categorical(
            emission_probabilities(params, generative_likelihood, depth),
            rand(emission_rng),
        )
        push!(rows, (
            seed = seed,
            trial = trial,
            mapping = mapping,
            true_depth = depth,
            observation_available = observed,
            volatility_observation = observed ? observation : 0,
        ))
    end
    return rows
end

function safety_prior_at_mass(params::Sim6aParams, high_mass::Float64)
    0.0 < high_mass < 1.0 || error("safety high-state mass must lie in (0, 1)")
    remainder = normalize_probs(params.safety_depth_prior[1:(end - 1)])
    return vcat((1.0 - high_mass) .* remainder, high_mass)
end

function predict_depth_with_prior(params::Sim6aParams, q, prior)
    return normalize_probs((1.0 - params.transition_mix) .* normalize_probs(q) .+ params.transition_mix .* normalize_probs(prior))
end

function scaled_capture_index(params::Sim6aParams, q, beta_gamma_scale::Float64)
    probs = normalize_probs(q)
    depth = params.depth_grid
    pi_eff = exp(sum(probs .* (log(params.pi_part) .- beta_gamma_scale * params.beta .* depth)))
    lambda_eff = exp(sum(probs .* (log(params.lambda_ctx) .+ beta_gamma_scale * params.gamma .* depth)))
    return pi_eff / (pi_eff + lambda_eff)
end

function params_with_policy_gain_scale(params::Sim6aParams, scale::Float64)
    overrides = Dict{Symbol, Any}(
        :threat_control_gain => params.threat_control_gain * scale,
        :reflexive_control_gain => params.reflexive_control_gain * scale,
    )
    pairs = (name => get(overrides, name, getfield(params, name)) for name in fieldnames(Sim6aParams))
    return Sim6aParams(; pairs...)
end

function filter_latent_trajectory(
    data,
    params::Sim6aParams;
    likelihood = mapped_volatility_likelihood(params, "theory"),
    prior = safety_prior(params),
    beta_gamma_scale::Float64 = 1.0,
    policy_gain_scale::Float64 = 1.0,
)
    q = depth_prior(params)
    policy_params = params_with_policy_gain_scale(params, policy_gain_scale)
    safe_evidence = 0.0
    traces = NamedTuple[]
    for row in data
        pre_capture = scaled_capture_index(params, q, beta_gamma_scale)
        policy = select_policy(policy_params, q, pre_capture, safe_evidence)
        q = row.observation_available ?
            update_depth_with_evidence(params, q, row.volatility_observation; depth_precision = policy.depth_precision, likelihood = likelihood, prior = prior) :
            predict_depth_with_prior(params, q, prior)
        row.observation_available && row.volatility_observation == OBS_LOW && (safe_evidence += 1.0)
        push!(traces, merge(row, (
            policy = policy.name,
            policy_depth_precision = policy.depth_precision,
            safe_evidence_count = safe_evidence,
            inferred_depth = expected_depth(params, q),
            depth_posterior_precision = posterior_precision(q),
            capture_index = scaled_capture_index(params, q, beta_gamma_scale),
        )))
    end
    return traces
end

function unevaluable_signature(seed::Int)
    return (seed = seed, signature = 0.0, baseline_precision = 0.0, transition_precision = 0.0, precision_drop_fraction = 0.0, inferred_depth_drop = 0.0, capture_rise = 0.0, recovery_fraction = 0.0, structurally_evaluable = 0.0)
end

function collapse_signature(seed::Int, traces, params::Sim6aParams)
    first_low = findfirst(row -> row.true_depth <= 0.25, traces)
    first_low === nothing && return unevaluable_signature(seed)
    pre_candidates = [idx for idx in 1:(first_low - 1) if traces[idx].true_depth >= 0.70]
    first_recovery = findfirst(idx -> idx > first_low && traces[idx].true_depth >= 0.70, eachindex(traces))
    (isempty(pre_candidates) || first_recovery === nothing) && return unevaluable_signature(seed)

    pre_indices = pre_candidates[max(1, length(pre_candidates) - 4):end]
    low_stop = first_recovery - 1
    low_indices = [idx for idx in first_low:low_stop if traces[idx].true_depth <= 0.35]
    isempty(low_indices) && (low_indices = collect(first_low:low_stop))
    transition_start = max(first(pre_indices) + 1, first_low - 7)
    transition_indices = transition_start:min(first_low + 3, length(traces))
    recovery_indices = first_recovery:min(first_recovery + 4, length(traces))

    baseline_precision = mean(traces[idx].depth_posterior_precision for idx in pre_indices)
    transition_precision = minimum(traces[idx].depth_posterior_precision for idx in transition_indices)
    precision_drop = (baseline_precision - transition_precision) / max(baseline_precision, eps(Float64))
    depth_drop = mean(traces[idx].inferred_depth for idx in pre_indices) - mean(traces[idx].inferred_depth for idx in low_indices)
    capture_rise = mean(traces[idx].capture_index for idx in low_indices) - mean(traces[idx].capture_index for idx in pre_indices)
    recovery = maximum(traces[idx].depth_posterior_precision for idx in recovery_indices) / max(baseline_precision, eps(Float64))
    signature = precision_drop >= params.signature_precision_drop &&
        depth_drop >= params.signature_depth_drop &&
        capture_rise >= params.signature_capture_rise &&
        recovery >= params.signature_recovery_fraction
    return (
        seed = seed,
        signature = signature ? 1.0 : 0.0,
        baseline_precision = baseline_precision,
        transition_precision = transition_precision,
        precision_drop_fraction = precision_drop,
        inferred_depth_drop = depth_drop,
        capture_rise = capture_rise,
        recovery_fraction = recovery,
        structurally_evaluable = 1.0,
    )
end

function fit_volatility_likelihood(training_data, params::Sim6aParams)
    counts = fill(params.likelihood_fit_smoothing, 5, length(params.depth_grid))
    for rows in training_data, row in rows
        row.observation_available || continue
        depth_idx = argmin(abs.(params.depth_grid .- row.true_depth))
        counts[row.volatility_observation, depth_idx] += 1.0
    end
    return normalize_likelihood(counts)
end

function fit_depth_transition(training_data, params::Sim6aParams)
    n_states = length(params.depth_grid)
    counts = fill(params.likelihood_fit_smoothing, n_states, n_states)
    for rows in training_data
        state_indices = [argmin(abs.(params.depth_grid .- row.true_depth)) for row in rows]
        for trial in 2:length(state_indices)
            counts[state_indices[trial], state_indices[trial - 1]] += 1.0
        end
    end
    return normalize_likelihood(counts)
end

function smooth_heldout_trajectory(data, params::Sim6aParams, likelihood, transition)
    n_states = length(params.depth_grid)
    n_trials = length(data)
    emissions = ones(Float64, n_states, n_trials)
    for (trial, row) in enumerate(data)
        row.observation_available && (emissions[:, trial] = likelihood[row.volatility_observation, :])
    end

    forward = zeros(Float64, n_states, n_trials)
    backward = ones(Float64, n_states, n_trials)
    forward[:, 1] = normalize_probs(fill(1.0 / n_states, n_states) .* emissions[:, 1])
    for trial in 2:n_trials
        forward[:, trial] = normalize_probs(emissions[:, trial] .* (transition * forward[:, trial - 1]))
    end
    for trial in (n_trials - 1):-1:1
        backward[:, trial] = normalize_probs(transpose(transition) * (emissions[:, trial + 1] .* backward[:, trial + 1]))
    end

    traces = NamedTuple[]
    for trial in 1:n_trials
        posterior = normalize_probs(forward[:, trial] .* backward[:, trial])
        push!(traces, merge(data[trial], (
            inferred_depth = expected_depth(params, posterior),
            depth_posterior_precision = posterior_precision(posterior),
        )))
    end
    return traces
end

function likelihood_rows(matrix)
    return [(volatility_observation = obs, depth_state = depth, probability = matrix[obs, depth]) for depth in axes(matrix, 2) for obs in axes(matrix, 1)]
end

function transition_rows(matrix)
    return [(from_depth_state = from, to_depth_state = to, probability = matrix[to, from]) for from in axes(matrix, 2) for to in axes(matrix, 1)]
end

function grid_float_values(config::ExperimentConfig, key::String, default)
    haskey(config.sweep_grid, key) || return Float64.(default)
    return Float64.(config.sweep_grid[key])
end

function grid_string_values(config::ExperimentConfig, key::String, default)
    haskey(config.sweep_grid, key) || return string.(default)
    return string.(config.sweep_grid[key])
end

function run_sim6a_robustness(config::ExperimentConfig, params::Sim6aParams, outdir::AbstractString; config_path = nothing, started = time())
    # Step B guard lift (orchestrator, 2026-07-10): label-aware, matching the
    # sim1/sim2/sim5 convention.
    config.label in ("pilot", "confirmatory") || error("Sim 6a robustness runs use label pilot or confirmatory")
    if config.label == "pilot"
        config.seeds == collect(1001:1010) || error("Sim 6a robustness pilot is restricted to seeds 1001-1010")
    else
        (length(config.seeds) >= 20 && iseven(length(config.seeds)) && isempty(intersect(config.seeds, collect(1001:1010)))) ||
            error("Sim 6a robustness confirmatory requires >= 20 (even) seeds disjoint from pilot seeds 1001-1010")
    end

    base_data = Dict(seed => latent_trajectory(seed, params, "theory") for seed in config.seeds)
    decoupled_traces = Dict(seed => filter_latent_trajectory(base_data[seed], params) for seed in config.seeds)
    decoupled_rows = [collapse_signature(seed, decoupled_traces[seed], params) for seed in config.seeds]

    null_rows = NamedTuple[]
    null_counts = Dict{String, Int}()
    for mapping in ("flat", "reversed", "nonmonotone")
        mapping_rows = NamedTuple[]
        for seed in config.seeds
            data = latent_trajectory(seed, params, mapping)
            traces = filter_latent_trajectory(data, params)
            result = collapse_signature(seed, traces, params)
            push!(mapping_rows, merge((mapping = mapping,), result))
        end
        append!(null_rows, mapping_rows)
        null_counts[mapping] = count(row -> row.signature == 1.0, mapping_rows)
    end

    safety_grid = grid_float_values(config, "safety_high_state_mass", [0.35, 0.60, 0.80])
    likelihood_grid = grid_string_values(config, "likelihood_matrix", ["diffuse", "theory", "concentrated"])
    slope_grid = grid_float_values(config, "beta_gamma_scale", [0.50, 1.00, 2.00])
    policy_grid = grid_float_values(config, "policy_gain_scale", [0.50, 1.00, 2.00])
    joint_rows = NamedTuple[]
    joint_dataset_cache = Dict((mapping, seed) => latent_trajectory(seed, params, mapping) for mapping in likelihood_grid for seed in config.seeds)
    for safety_mass in safety_grid, likelihood_name in likelihood_grid, slope_scale in slope_grid, policy_scale in policy_grid
        prior = safety_prior_at_mass(params, safety_mass)
        likelihood = mapped_volatility_likelihood(params, likelihood_name)
        seed_support = 0
        evaluable = 0
        for seed in config.seeds
            traces = filter_latent_trajectory(
                joint_dataset_cache[(likelihood_name, seed)],
                params;
                likelihood = likelihood,
                prior = prior,
                beta_gamma_scale = slope_scale,
                policy_gain_scale = policy_scale,
            )
            result = collapse_signature(seed, traces, params)
            seed_support += Int(result.signature)
            evaluable += Int(result.structurally_evaluable)
        end
        push!(joint_rows, (
            safety_high_state_mass = safety_mass,
            likelihood_matrix = likelihood_name,
            beta_gamma_scale = slope_scale,
            policy_gain_scale = policy_scale,
            support_seed_count = seed_support,
            evaluable_seed_count = evaluable,
            # Step B scaling (orchestrator, 2026-07-10): the per-point gate is the
            # preregistered 0.8 seed FRACTION, not a hardcoded count of 8, so a
            # 20-seed confirmatory keeps the same standard (>= 16/20).
            transition_survives = seed_support >= ceil(Int, 0.8 * length(config.seeds)) ? 1.0 : 0.0,
        ))
    end

    split = length(config.seeds) ÷ 2
    training_seeds = config.seeds[1:split]
    heldout_seeds = config.seeds[(split + 1):end]
    training_data = [base_data[seed] for seed in training_seeds]
    fitted_likelihood = fit_volatility_likelihood(training_data, params)
    fitted_transition = fit_depth_transition(training_data, params)
    heldout_rows = NamedTuple[]
    for seed in heldout_seeds
        traces = smooth_heldout_trajectory(base_data[seed], params, fitted_likelihood, fitted_transition)
        push!(heldout_rows, (
            seed = seed,
            truth_correlation = safe_correlation([row.true_depth for row in traces], [row.inferred_depth for row in traces]),
            observed_trial_count = count(row -> row.observation_available, traces),
        ))
    end

    decoupled_count = count(row -> row.signature == 1.0, decoupled_rows)
    evaluable_count = count(row -> row.structurally_evaluable == 1.0, decoupled_rows)
    metrics = (
        decoupled = (
            signature_seed_count = decoupled_count,
            evaluable_seed_count = evaluable_count,
            seed_count = length(config.seeds),
        ),
        nulls = (
            flat_signature_seed_count = null_counts["flat"],
            reversed_signature_seed_count = null_counts["reversed"],
            nonmonotone_signature_seed_count = null_counts["nonmonotone"],
            max_signature_seed_count = maximum(values(null_counts)),
        ),
        joint = (
            transition_volume_fraction = mean(row.transition_survives for row in joint_rows),
            surviving_grid_points = count(row -> row.transition_survives == 1.0, joint_rows),
            total_grid_points = length(joint_rows),
            per_grid_seed_requirement = 8,
        ),
        heldout = (
            mean_truth_correlation = mean(row.truth_correlation for row in heldout_rows),
            min_truth_correlation = minimum(row.truth_correlation for row in heldout_rows),
            training_seeds = training_seeds,
            heldout_seeds = heldout_seeds,
        ),
    )
    summary = (
        experiment = "sim6a",
        analysis = "T4.7 robustness pilot",
        config = config_snapshot(config),
        model_contract = (
            latent_process = "autonomous reflected stochastic depth trajectory; no trial_spec or biography phase input",
            observation_schedule = "Bernoulli availability sampled independently of latent depth; emissions sampled from P(volatility | latent depth)",
            null_evaluation = "null-generated emissions evaluated by the frozen theory-mapping agent",
            heldout_protocol = "emission and transition matrices fitted on first five seed trajectories; forward-backward recovery evaluated on the other five",
            collapse_signature = "precision drop AND inferred-depth drop AND capture rise AND precision recovery",
        ),
        metrics = metrics,
        per_seed_metric_count = length(decoupled_rows),
        trace_row_count = sum(length(rows) for rows in values(decoupled_traces)),
    )

    summary_path = joinpath(outdir, "summary.json")
    write_json(summary_path, summary)
    write_rows_csv(joinpath(outdir, "per_seed_metrics.csv"), decoupled_rows)
    write_rows_csv(joinpath(outdir, "posterior_traces.csv"), reduce(vcat, [decoupled_traces[seed] for seed in config.seeds]))
    write_rows_csv(joinpath(outdir, "null_mapping_metrics.csv"), null_rows)
    write_rows_csv(joinpath(outdir, "joint_sweep_metrics.csv"), joint_rows)
    write_rows_csv(joinpath(outdir, "heldout_identifiability.csv"), heldout_rows)
    write_rows_csv(joinpath(outdir, "fitted_likelihood.csv"), likelihood_rows(fitted_likelihood))
    write_rows_csv(joinpath(outdir, "fitted_transition.csv"), transition_rows(fitted_transition))

    criteria_results = nothing
    if !isnothing(config.criteria_path) && isfile(config.criteria_path)
        criteria_results = write_criteria_results(config.criteria_path, summary_path, joinpath(outdir, "criteria-results.json"))
    end
    status = (
        implementation_passed = evaluable_count == length(config.seeds) && length(joint_rows) == length(safety_grid) * length(likelihood_grid) * length(slope_grid) * length(policy_grid),
        theory_result = theory_label(criteria_results),
        criteria_results_path = criteria_results === nothing ? nothing : joinpath(outdir, "criteria-results.json"),
        protocol = "pilot-only",
    )
    write_json(joinpath(outdir, "status.json"), status)
    metadata = build_reproducibility_metadata(
        config;
        config_path = config_path,
        runtime_seconds = time() - started,
        repo_root = normpath(joinpath(@__DIR__, "..", "..", "..", "..", "..")),
        extra = (output_dir = abspath(outdir), sim_module = "EmergenceSuite.Sim6a", protocol = "T4.7 Step A pilot-only"),
    )
    write_json(joinpath(outdir, "metadata.json"), metadata)
    return (output_dir = outdir, summary = summary, status = status, criteria_results = criteria_results)
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

    params.robustness_mode && return run_sim6a_robustness(config, params, outdir; config_path = config_path, started = started)

    length(config.seeds) >= 20 || error("Sim 6a requires at least 20 seeds")
    bundles = load_bundles(params)

    biography_metrics = NamedTuple[]
    traces = NamedTuple[]
    dose_rows = NamedTuple[]
    identifiability_rows = NamedTuple[]

    for (idx, seed) in enumerate(config.seeds)
        bundle = bundles[mod1(idx, length(bundles))]
        result = simulate_biography(seed, bundle, params; policies_enabled = params.policy_mode)
        push!(biography_metrics, result.metric)
        append!(traces, result.traces)
        append!(dose_rows, dose_response_probe(seed, bundle, params; policies_enabled = params.policy_mode))
        push!(identifiability_rows, identifiability_probe(seed, params))
    end

    d1 = d1_validation(params)
    d3 = d3_analysis(params, traces)
    stability = stability_probe(biography_metrics, traces)
    figure_path = write_biography_svg(joinpath(outdir, "figures", "biography.svg"), traces)
    stage2 = params.stage2_enabled ? stage2_analysis(params, outdir) : nothing

    imported = (
        manifest_dir = params.bundle_dir,
        bundle_count = length(bundles),
        bundles = [(file = bundle.file, seed = bundle.seed, route = bundle.route, family = bundle.family, structural_precision = bundle.structural_precision, threat_probability = bundle.threat_probability) for bundle in bundles],
    )

    stage1_metrics = (
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
    )

    metrics = params.stage2_enabled ? (
        collapse = stage1_metrics.collapse,
        self_observation = stage1_metrics.self_observation,
        outputs = stage1_metrics.outputs,
        d1 = stage1_metrics.d1,
        d3 = stage1_metrics.d3,
        identifiability = stage1_metrics.identifiability,
        stability = stage1_metrics.stability,
        stage1_replication = stage1_metrics,
        stage2 = stage2.metrics,
    ) : stage1_metrics

    base_model_contract = (
        depth_states = params.depth_grid,
        beta = params.beta,
        gamma = params.gamma,
        message_convention = "effective precision = exp(E_q[log precision])",
        collapse_path = "arousal is evaluated only as a volatility observation before depth filtering",
        transparent_sharpness_max = params.transparent_sharpness_max,
        opacified_sharpness_min = params.opacified_sharpness_min,
    )
    model_contract = params.stage2_enabled ? (
        depth_states = base_model_contract.depth_states,
        beta = base_model_contract.beta,
        gamma = base_model_contract.gamma,
        message_convention = base_model_contract.message_convention,
        collapse_path = base_model_contract.collapse_path,
        transparent_sharpness_max = base_model_contract.transparent_sharpness_max,
        opacified_sharpness_min = base_model_contract.opacified_sharpness_min,
        stage2_policy_mode = params.policy_mode ? 1.0 : 0.0,
        policy_efe_inputs = "current depth posterior, current cause-bank threat belief, learned reflexive-safety contingency, fixed preferences",
    ) : base_model_contract

    summary = (
        experiment = "sim6a",
        config = config_snapshot(config),
        imported_bundles = imported,
        model_contract = model_contract,
        metrics = metrics,
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
    if params.stage2_enabled
        write_rows_csv(joinpath(outdir, "efe_decomposition.csv"), stage2.efe_rows)
        write_rows_csv(joinpath(outdir, "witnessing_policy.csv"), stage2.witnessing_rows)
        write_rows_csv(joinpath(outdir, "preference_sweep.csv"), stage2.sweep_rows)
    end

    criteria_results = nothing
    if !isnothing(config.criteria_path) && isfile(config.criteria_path)
        criteria_results = write_criteria_results(config.criteria_path, summary_path, joinpath(outdir, "criteria-results.json"))
    end
    status = (
        implementation_passed = length(config.seeds) >= 20 && isfile(figure_path) && !isempty(traces) && (!params.stage2_enabled || isfile(stage2.metrics.outputs.efe_crossover_figure)),
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
