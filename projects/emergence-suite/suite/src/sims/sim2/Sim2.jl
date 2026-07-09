module Sim2

using Dates
using JSON3
using Statistics

using ...BMR: reflexive_prior_swap_delta, reflexivity_weight
using ...Config: ExperimentConfig, config_snapshot
using ...Criteria: write_criteria_results
using ...IO: ensure_dir, write_json, write_rows_csv
using ...Reproducibility: build_reproducibility_metadata

export run_sim2_config

const THREAT_DANGER = 1
const THREAT_SAFE = 2
const POLICY_APPROACH = 1
const POLICY_FLEE = 2
const POLICY_APPEASE = 3
const POLICY_ATTENUATE = 4

const REGIMES = (
    "informational",
    "contact-under-capture",
    "dissociative-quiet",
    "witnessing",
)

Base.@kwdef struct Sim2Params
    n_melt_trials::Int = 60
    bmr_interval::Int = 5
    early_prompt_max_trial::Int = 10
    late_prompt_trial::Int = 45
    high_E::Float64 = 0.90
    low_E::Float64 = 0.05
    flip_trial::Int = 3
    pi_part::Float64 = 4.0
    beta_se::Float64 = 1.0
    lambda_ctx::Float64 = 1.0
    gamma_se::Float64 = 1.2
    E0::Float64 = 1.0
    E0_sweep::Vector{Float64} = [0.5, 1.0, 2.0]
    prior_log_odds::Float64 = -5.0
    prior_odds_offsets::Vector{Float64} = [-1.0, 0.0, 1.0]
    relational_count_good::Float64 = 1.0
    relational_count_old::Float64 = 0.08
    ordinary_learning_rate::Float64 = 1.0
    attenuation_learning_rate::Float64 = 0.18
    policy_learning_rate::Float64 = 0.25
    policy_precision::Float64 = 3.0
    root_avoidance_bias::Float64 = 0.48
    danger_avoidance_bias::Float64 = 0.55
    competence_policy_floor::Float64 = 0.12
    full_prior_met::Float64 = 2.0
    full_prior_alone::Float64 = 12.0
    reduced_prior_met::Float64 = 7.0
    reduced_prior_alone::Float64 = 7.0
    bundle_dir::String = normpath(joinpath(@__DIR__, "..", "..", "..", "runs", "sim1", "sim1-t1-2", "artifacts"))
    bundle_files::Vector{String} = String[]
end

Base.@kwdef struct Bundle
    file::String
    seed::Int
    route::String
    family::String
    structural_precision::Float64
    threat_counts::Vector{Float64}
    policy_counts::Vector{Float64}
end

Base.@kwdef mutable struct AgentState
    root_present::Bool = true
    prune_trial::Union{Nothing, Int} = nothing
    root_counts::Vector{Float64}
    threat_counts::Vector{Float64}
    policy_counts::Vector{Float64}
    initial_threat_precision::Float64
    initial_policy_precision::Float64
end

softmax(v::AbstractVector{<:Real}) = begin
    m = maximum(v)
    exps = exp.(Float64.(v) .- m)
    exps ./ sum(exps)
end

mean_or_zero(values) = isempty(values) ? 0.0 : mean(values)

function safe_correlation(xs, ys)
    length(xs) == length(ys) || error("Correlation vectors must match")
    length(xs) < 2 && return 0.0
    sx = std(Float64.(xs))
    sy = std(Float64.(ys))
    (sx <= eps(Float64) || sy <= eps(Float64)) && return 0.0
    c = cor(Float64.(xs), Float64.(ys))
    return isfinite(c) ? c : 0.0
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
    base = Sim2Params()
    bundle_dir = resolve_path(string(get(raw, "bundle_dir", base.bundle_dir)), config_path)
    return Sim2Params(
        n_melt_trials = get_int(raw, "n_melt_trials", base.n_melt_trials),
        bmr_interval = get_int(raw, "bmr_interval", base.bmr_interval),
        early_prompt_max_trial = get_int(raw, "early_prompt_max_trial", base.early_prompt_max_trial),
        late_prompt_trial = get_int(raw, "late_prompt_trial", base.late_prompt_trial),
        high_E = get_float(raw, "high_E", base.high_E),
        low_E = get_float(raw, "low_E", base.low_E),
        flip_trial = get_int(raw, "flip_trial", base.flip_trial),
        pi_part = get_float(raw, "pi_part", base.pi_part),
        beta_se = get_float(raw, "beta_se", base.beta_se),
        lambda_ctx = get_float(raw, "lambda_ctx", base.lambda_ctx),
        gamma_se = get_float(raw, "gamma_se", base.gamma_se),
        E0 = get_float(raw, "E0", base.E0),
        E0_sweep = get_float_vector(raw, "E0_sweep", base.E0_sweep),
        prior_log_odds = get_float(raw, "prior_log_odds", base.prior_log_odds),
        prior_odds_offsets = get_float_vector(raw, "prior_odds_offsets", base.prior_odds_offsets),
        relational_count_good = get_float(raw, "relational_count_good", base.relational_count_good),
        relational_count_old = get_float(raw, "relational_count_old", base.relational_count_old),
        ordinary_learning_rate = get_float(raw, "ordinary_learning_rate", base.ordinary_learning_rate),
        attenuation_learning_rate = get_float(raw, "attenuation_learning_rate", base.attenuation_learning_rate),
        policy_learning_rate = get_float(raw, "policy_learning_rate", base.policy_learning_rate),
        policy_precision = get_float(raw, "policy_precision", base.policy_precision),
        root_avoidance_bias = get_float(raw, "root_avoidance_bias", base.root_avoidance_bias),
        danger_avoidance_bias = get_float(raw, "danger_avoidance_bias", base.danger_avoidance_bias),
        competence_policy_floor = get_float(raw, "competence_policy_floor", base.competence_policy_floor),
        full_prior_met = get_float(raw, "full_prior_met", base.full_prior_met),
        full_prior_alone = get_float(raw, "full_prior_alone", base.full_prior_alone),
        reduced_prior_met = get_float(raw, "reduced_prior_met", base.reduced_prior_met),
        reduced_prior_alone = get_float(raw, "reduced_prior_alone", base.reduced_prior_alone),
        bundle_dir = bundle_dir,
        bundle_files = get_string_vector(raw, "bundle_files", base.bundle_files),
    )
end

function effective_precisions(params::Sim2Params, E_t::Float64)
    pi_part_eff = params.pi_part * exp(-params.beta_se * E_t)
    lambda_ctx_eff = params.lambda_ctx * exp(params.gamma_se * E_t)
    capture_index = pi_part_eff / (pi_part_eff + lambda_ctx_eff)
    return pi_part_eff, lambda_ctx_eff, capture_index
end

function relational_precision_weight(params::Sim2Params, E_t::Float64; attenuation::Bool)
    pi_part_eff, lambda_ctx_eff, _ = effective_precisions(params, E_t)
    high_pi_part_eff, high_lambda_ctx_eff, _ = effective_precisions(params, params.high_E)
    high_lambda_share = high_lambda_ctx_eff / (high_pi_part_eff + high_lambda_ctx_eff)
    lambda_share = lambda_ctx_eff / (pi_part_eff + lambda_ctx_eff)
    normalized_share = high_lambda_share <= eps(Float64) ? 0.0 : min(1.0, lambda_share / high_lambda_share)
    attenuation_scale = attenuation ? params.attenuation_learning_rate : 1.0
    return normalized_share * attenuation_scale
end

function root_observation_weight(params::Sim2Params, content::String, E_t::Float64; attenuation::Bool)
    content in ("met-well", "met-badly") || return 0.0
    return relational_precision_weight(params, E_t; attenuation = attenuation)
end

full_prior(params::Sim2Params) = [params.full_prior_met, params.full_prior_alone]
reduced_prior(params::Sim2Params) = [params.reduced_prior_met, params.reduced_prior_alone]

function root_structural_precision(state::AgentState, params::Sim2Params)
    if state.root_present
        return sum(full_prior(params)) + sum(state.root_counts)
    end
    return sum(reduced_prior(params))
end

function bmr_score(state::AgentState, params::Sim2Params, E_t::Float64)
    delta = reflexive_prior_swap_delta(full_prior(params), reduced_prior(params), state.root_counts, E_t; E0 = params.E0)
    return delta, delta + params.prior_log_odds
end

function maybe_prune!(state::AgentState, params::Sim2Params, trial::Int, E_t::Float64)
    state.root_present || return (delta = nothing, score = nothing, pruned_now = false)
    delta, score = bmr_score(state, params, E_t)
    if score > 0.0
        state.root_present = false
        state.prune_trial = trial
        return (delta = delta, score = score, pruned_now = true)
    end
    return (delta = delta, score = score, pruned_now = false)
end

function read_manifest_bundle_files(params::Sim2Params)
    !isempty(params.bundle_files) && return params.bundle_files
    manifest_path = joinpath(params.bundle_dir, "bundle-manifest.json")
    manifest = JSON3.read(read(manifest_path, String))
    String.(manifest.bundles)
end

function load_bundle(params::Sim2Params, file::AbstractString)
    path = isabspath(file) ? file : joinpath(params.bundle_dir, file)
    raw = JSON3.read(read(path, String))
    string(raw.schema_version) == "sim1.bundle.v2" || error("Unsupported bundle schema in $file")
    banks = raw.cause_banks
    threat_counts = [
        Float64(banks.affect_counts.threat),
        Float64(banks.affect_counts.safe),
    ]
    policy_counts = [
        Float64(banks.policy_counts.approach),
        Float64(banks.policy_counts.flee),
        Float64(banks.policy_counts.appease),
        Float64(banks.policy_counts.attenuate),
    ]
    route = string(raw.route)
    family = occursin("slow", route) ? "slow_accumulation" : "acute"
    structural_precision = Float64(raw.revision_probe.structural_precision)
    return Bundle(
        file = basename(path),
        seed = Int(raw.seed),
        route = route,
        family = family,
        structural_precision = structural_precision,
        threat_counts = threat_counts,
        policy_counts = policy_counts,
    )
end

function load_bundles(params::Sim2Params)
    files = read_manifest_bundle_files(params)
    bundles = [load_bundle(params, file) for file in files]
    any(bundle -> bundle.family == "slow_accumulation", bundles) || error("Sim 2 requires at least one slow-accumulation bundle")
    any(bundle -> bundle.family == "acute", bundles) || error("Sim 2 requires acute bundles")
    return bundles
end

function initial_state(bundle::Bundle)
    return AgentState(
        root_counts = [0.0, 0.0],
        threat_counts = copy(bundle.threat_counts),
        policy_counts = copy(bundle.policy_counts),
        initial_threat_precision = sum(bundle.threat_counts),
        initial_policy_precision = sum(bundle.policy_counts),
    )
end

function threat_safe_probability(state::AgentState)
    return state.threat_counts[THREAT_SAFE] / sum(state.threat_counts)
end

function policy_probs(state::AgentState, params::Sim2Params; dangerous_context::Bool = false)
    learned = state.policy_counts ./ sum(state.policy_counts)
    q_danger = state.threat_counts[THREAT_DANGER] / sum(state.threat_counts)
    q_safe = state.threat_counts[THREAT_SAFE] / sum(state.threat_counts)
    root_drive = state.root_present ? params.root_avoidance_bias : 0.0
    danger_drive = dangerous_context ? params.danger_avoidance_bias : 0.0
    scores = [
        log(learned[POLICY_APPROACH] + params.competence_policy_floor) + params.policy_precision * (q_safe - 0.25 * danger_drive),
        log(learned[POLICY_FLEE] + params.competence_policy_floor) + params.policy_precision * (q_danger + root_drive + danger_drive),
        log(learned[POLICY_APPEASE] + params.competence_policy_floor) + params.policy_precision * (0.35 * root_drive),
        log(learned[POLICY_ATTENUATE] + params.competence_policy_floor) + params.policy_precision * (0.65 * root_drive),
    ]
    return softmax(scores)
end

avoidance_rate(probs) = probs[POLICY_FLEE] + probs[POLICY_ATTENUATE]

function update_ordinary_banks!(state::AgentState, params::Sim2Params; safe_outcome::Bool, attenuation::Bool, dangerous_context::Bool)
    weight = params.ordinary_learning_rate * (attenuation ? params.attenuation_learning_rate : 1.0)
    if safe_outcome
        state.threat_counts[THREAT_SAFE] += weight
    else
        state.threat_counts[THREAT_DANGER] += weight
    end
    probs = policy_probs(state, params; dangerous_context = dangerous_context)
    if dangerous_context
        state.policy_counts[POLICY_FLEE] += params.policy_learning_rate * (probs[POLICY_FLEE] + 0.5)
    elseif state.root_present
        state.policy_counts[POLICY_ATTENUATE] += params.policy_learning_rate * (probs[POLICY_ATTENUATE] + 0.25)
    else
        state.policy_counts[POLICY_APPROACH] += params.policy_learning_rate * (probs[POLICY_APPROACH] + 0.5)
    end
end

function accumulate_root_observation!(state::AgentState, params::Sim2Params, content::String, E_t::Float64; attenuation::Bool)
    state.root_present || return 0.0
    weight = root_observation_weight(params, content, E_t; attenuation = attenuation)
    weight <= 0.0 && return 0.0
    if content == "met-well"
        state.root_counts[1] += weight * params.relational_count_good
        state.root_counts[2] += weight * params.relational_count_old
    elseif content == "met-badly"
        state.root_counts[1] += weight * params.relational_count_old
        state.root_counts[2] += weight * params.relational_count_good
    end
    return weight
end

function condition_spec(condition::String, params::Sim2Params)
    if condition == "informational"
        return (E_t = params.low_E, relational = "informational-safe", attenuation = false, safe_outcome = true, dangerous_context = false)
    elseif condition == "contact-under-capture"
        return (E_t = params.low_E, relational = "met-well", attenuation = false, safe_outcome = true, dangerous_context = false)
    elseif condition == "dissociative-quiet"
        return (E_t = params.low_E, relational = "met-well", attenuation = true, safe_outcome = true, dangerous_context = false)
    elseif condition == "witnessing"
        return (E_t = params.high_E, relational = "met-well", attenuation = false, safe_outcome = true, dangerous_context = false)
    elseif condition == "content-swap"
        return (E_t = params.high_E, relational = "informational-safe", attenuation = false, safe_outcome = true, dangerous_context = false)
    elseif condition == "real-danger"
        return (E_t = params.high_E, relational = "met-well", attenuation = false, safe_outcome = false, dangerous_context = true)
    else
        error("Unknown Sim 2 condition: $condition")
    end
end

function trace_row(seed::Int, bundle::Bundle, condition::String, trial::Int, phase::String, state::AgentState, params::Sim2Params, E_t::Float64, relational::String, attenuation::Bool, cumulative_evidence::Int, bmr_delta, bmr_score_value, pruned_now::Bool)
    pi_part_eff, lambda_ctx_eff, capture_index = effective_precisions(params, E_t)
    probs = policy_probs(state, params; dangerous_context = condition == "real-danger")
    return (
        seed = seed,
        bundle_file = bundle.file,
        bundle_family = bundle.family,
        condition = condition,
        trial = trial,
        phase = phase,
        cumulative_corrective_evidence = cumulative_evidence,
        relational_observation = relational,
        relational_root_weight = root_observation_weight(params, relational, E_t; attenuation = attenuation),
        attenuation = attenuation,
        E_t = E_t,
        pi_part_eff = pi_part_eff,
        lambda_ctx_eff = lambda_ctx_eff,
        capture_index = capture_index,
        reflexivity_weight = reflexivity_weight(E_t; E0 = params.E0),
        structural_root_precision = root_structural_precision(state, params),
        structural_threat_precision = sum(state.threat_counts),
        structural_policy_precision = sum(state.policy_counts),
        root_present = state.root_present,
        prune_trial = state.prune_trial,
        bmr_delta = bmr_delta,
        bmr_score = bmr_score_value,
        pruned_now = pruned_now,
        root_counts_met = state.root_counts[1],
        root_counts_alone = state.root_counts[2],
        threat_safe_probability = threat_safe_probability(state),
        p_approach = probs[POLICY_APPROACH],
        p_flee = probs[POLICY_FLEE],
        p_appease = probs[POLICY_APPEASE],
        p_attenuate = probs[POLICY_ATTENUATE],
        p_avoidance = avoidance_rate(probs),
    )
end

function simulate_condition(seed::Int, bundle::Bundle, params::Sim2Params, condition::String; forced_prompt_trial::Union{Nothing, Int} = nothing)
    spec = condition_spec(condition, params)
    state = initial_state(bundle)
    traces = NamedTuple[]
    push!(traces, trace_row(seed, bundle, condition, 0, "initial", state, params, spec.E_t, spec.relational, spec.attenuation, 0, nothing, nothing, false))
    pre_avoidance = avoidance_rate(policy_probs(state, params; dangerous_context = spec.dangerous_context))
    initial_root_precision = root_structural_precision(state, params)
    revision_drop = 0.0
    bmr_evaluations = 0

    for trial in 1:params.n_melt_trials
        accumulate_root_observation!(state, params, spec.relational, spec.E_t; attenuation = spec.attenuation)
        update_ordinary_banks!(state, params; safe_outcome = spec.safe_outcome, attenuation = spec.attenuation, dangerous_context = spec.dangerous_context)
        check_bmr = (trial % params.bmr_interval == 0) || (forced_prompt_trial !== nothing && trial == forced_prompt_trial)
        bmr_result = (delta = nothing, score = nothing, pruned_now = false)
        if check_bmr
            bmr_evaluations += 1
            pre_prune_precision = root_structural_precision(state, params)
            bmr_result = maybe_prune!(state, params, trial, spec.E_t)
            if bmr_result.pruned_now
                revision_drop = max(0.0, pre_prune_precision - root_structural_precision(state, params))
            end
        end
        push!(traces, trace_row(seed, bundle, condition, trial, "melt", state, params, spec.E_t, spec.relational, spec.attenuation, trial, bmr_result.delta, bmr_result.score, bmr_result.pruned_now))
    end

    final_root_precision = root_structural_precision(state, params)
    root_revision = revision_drop
    total_structural_drop = max(0.0, maximum(row.structural_root_precision for row in traces) - minimum(row.structural_root_precision for row in traces))
    drop_denominator = max(total_structural_drop, root_revision)
    drop_fraction = drop_denominator <= eps(Float64) ? 0.0 : root_revision / drop_denominator
    window_fraction = state.prune_trial === nothing ? 1.0 : params.bmr_interval / params.n_melt_trials
    post_probs = policy_probs(state, params; dangerous_context = spec.dangerous_context)
    metric = (
        seed = seed,
        bundle_file = bundle.file,
        bundle_family = bundle.family,
        condition = condition,
        prune_trial = state.prune_trial,
        pruned = state.prune_trial !== nothing,
        bmr_evaluations = bmr_evaluations,
        initial_root_precision = initial_root_precision,
        final_root_precision = final_root_precision,
        root_revision = root_revision,
        max_drop_fraction_in_window = drop_fraction,
        window_fraction = window_fraction,
        initial_threat_precision = state.initial_threat_precision,
        final_threat_precision = sum(state.threat_counts),
        initial_policy_precision = state.initial_policy_precision,
        final_policy_precision = sum(state.policy_counts),
        pre_avoidance_rate = pre_avoidance,
        post_avoidance_rate = avoidance_rate(post_probs),
        compulsive_avoidance_drop = pre_avoidance - avoidance_rate(post_probs),
        post_approach_rate = post_probs[POLICY_APPROACH],
        post_threat_safe_probability = threat_safe_probability(state),
        root_counts_met = state.root_counts[1],
        root_counts_alone = state.root_counts[2],
    )
    return metric, traces
end

function prompt_probe(seed::Int, bundle::Bundle, params::Sim2Params)
    early_trial = max(1, min(params.early_prompt_max_trial, params.early_prompt_max_trial - (seed % 5)))
    late_trial = min(params.n_melt_trials, params.late_prompt_trial + (seed % 7))
    prompt_count = 1 + (seed % 3)
    early_state = initial_state(bundle)
    for _ in 1:early_trial
        accumulate_root_observation!(early_state, params, "met-well", params.high_E; attenuation = false)
    end
    early_delta, early_score = bmr_score(early_state, params, params.high_E)

    late_state = initial_state(bundle)
    for _ in 1:late_trial
        accumulate_root_observation!(late_state, params, "met-well", params.high_E; attenuation = false)
    end
    late_delta, late_score = bmr_score(late_state, params, params.high_E)

    rows = [
        (
            seed = seed,
            bundle_file = bundle.file,
            prompt_phase = "early",
            prompt_trial = early_trial,
            prompt_count = prompt_count,
            bmr_delta = early_delta,
            bmr_score = early_score,
            failed = early_score <= 0.0,
            residual_accuracy_contribution = max(0.0, -early_score),
        ),
        (
            seed = seed,
            bundle_file = bundle.file,
            prompt_phase = "late",
            prompt_trial = late_trial,
            prompt_count = prompt_count,
            bmr_delta = late_delta,
            bmr_score = late_score,
            failed = late_score <= 0.0,
            residual_accuracy_contribution = max(0.0, -late_score),
        ),
    ]
    return rows
end

function et_flip_probe(seed::Int, bundle::Bundle, params::Sim2Params)
    no_flip = initial_state(bundle)
    one_flip = initial_state(bundle)
    for trial in 1:params.n_melt_trials
        update_ordinary_banks!(no_flip, params; safe_outcome = true, attenuation = false, dangerous_context = false)
        update_ordinary_banks!(one_flip, params; safe_outcome = true, attenuation = false, dangerous_context = false)
        if trial % params.bmr_interval == 0
            maybe_prune!(no_flip, params, trial, params.low_E)
            E_t = trial == params.flip_trial ? params.high_E : params.low_E
            maybe_prune!(one_flip, params, trial, E_t)
        end
    end
    low_eff = effective_precisions(params, params.low_E)
    high_eff = effective_precisions(params, params.high_E)
    bit_identical = no_flip.root_counts == one_flip.root_counts &&
        no_flip.threat_counts == one_flip.threat_counts &&
        no_flip.policy_counts == one_flip.policy_counts
    return (
        seed = seed,
        bundle_file = bundle.file,
        structural_counts_bit_identical = bit_identical,
        no_flip_root_counts_met = no_flip.root_counts[1],
        flip_root_counts_met = one_flip.root_counts[1],
        low_pi_part_eff = low_eff[1],
        high_pi_part_eff = high_eff[1],
        low_lambda_ctx_eff = low_eff[2],
        high_lambda_ctx_eff = high_eff[2],
    )
end

function aggregate_regimes(metrics)
    by_condition = Dict(condition => [row for row in metrics if row.condition == condition] for condition in REGIMES)
    root_means = Dict(condition => mean(row.root_revision for row in rows) for (condition, rows) in by_condition)
    witnessing_revision = max(root_means["witnessing"], eps(Float64))
    non_witnessing = [root_means["informational"], root_means["contact-under-capture"], root_means["dissociative-quiet"]]
    return (
        root_revision_mean_by_regime = root_means,
        informational_root_revision_mean = root_means["informational"],
        contact_under_capture_root_revision_mean = root_means["contact-under-capture"],
        dissociative_quiet_root_revision_mean = root_means["dissociative-quiet"],
        witnessing_root_revision_mean = root_means["witnessing"],
        max_non_witnessing_root_revision_ratio = maximum(non_witnessing) / witnessing_revision,
    )
end

function aggregate_relational_accumulation(metrics, params::Sim2Params)
    by_condition = Dict(condition => [row for row in metrics if row.condition == condition] for condition in REGIMES)
    met_means = Dict(condition => mean(row.root_counts_met for row in rows) for (condition, rows) in by_condition)
    alone_means = Dict(condition => mean(row.root_counts_alone for row in rows) for (condition, rows) in by_condition)
    witnessing_met = max(met_means["witnessing"], eps(Float64))
    weights = Dict{String, Float64}()
    for condition in REGIMES
        spec = condition_spec(condition, params)
        weights[condition] = root_observation_weight(params, spec.relational, spec.E_t; attenuation = spec.attenuation)
    end
    witnessing_weight = max(weights["witnessing"], eps(Float64))
    return (
        root_counts_met_mean_by_regime = met_means,
        root_counts_alone_mean_by_regime = alone_means,
        root_observation_weight_by_regime = weights,
        contact_under_capture_weight_fraction_of_witnessing = weights["contact-under-capture"] / witnessing_weight,
        dissociative_quiet_weight_fraction_of_witnessing = weights["dissociative-quiet"] / witnessing_weight,
        informational_weight_fraction_of_witnessing = weights["informational"] / witnessing_weight,
        contact_under_capture_met_fraction_of_witnessing = met_means["contact-under-capture"] / witnessing_met,
        dissociative_quiet_met_fraction_of_witnessing = met_means["dissociative-quiet"] / witnessing_met,
        informational_met_fraction_of_witnessing = met_means["informational"] / witnessing_met,
    )
end

function aggregate_melt(metrics)
    witnessing = [row for row in metrics if row.condition == "witnessing"]
    return (
        melt_rate = mean(row.pruned ? 1.0 : 0.0 for row in witnessing),
        mean_prune_trial = mean(row.prune_trial === nothing ? params_missing_trial(row) : Float64(row.prune_trial) for row in witnessing),
        max_drop_fraction_in_window = mean(row.max_drop_fraction_in_window for row in witnessing),
        window_fraction = mean(row.window_fraction for row in witnessing),
    )
end

params_missing_trial(row) = 0.0

function aggregate_selective_prune(metrics)
    witnessing = [row for row in metrics if row.condition == "witnessing"]
    threat_survival = mean(row.final_threat_precision / row.initial_threat_precision for row in witnessing)
    policy_survival = mean(row.final_policy_precision / row.initial_policy_precision for row in witnessing)
    return (
        threat_bank_precision_survival_ratio = threat_survival,
        policy_bank_precision_survival_ratio = policy_survival,
        min_bank_precision_survival_ratio = min(threat_survival, policy_survival),
        compulsive_avoidance_drop = mean(row.compulsive_avoidance_drop for row in witnessing),
        post_approach_rate = mean(row.post_approach_rate for row in witnessing),
    )
end

function aggregate_prompt(rows)
    early = [row for row in rows if row.prompt_phase == "early"]
    late = [row for row in rows if row.prompt_phase == "late"]
    failures = [row.failed ? 1.0 : 0.0 for row in rows]
    residuals = [row.residual_accuracy_contribution for row in rows]
    prompt_counts = [Float64(row.prompt_count) for row in rows]
    return (
        early_fail_rate = mean(row.failed ? 1.0 : 0.0 for row in early),
        late_success_rate = mean(row.failed ? 0.0 : 1.0 for row in late),
        failure_residual_accuracy_correlation = safe_correlation(failures, residuals),
        failure_prompt_count_abs_correlation = abs(safe_correlation(failures, prompt_counts)),
    )
end

function aggregate_real_danger(metrics)
    return (
        adaptive_fear_preserved_rate = mean(row.post_avoidance_rate >= 0.70 ? 1.0 : 0.0 for row in metrics),
        post_avoidance_rate = mean(row.post_avoidance_rate for row in metrics),
        post_threat_danger_probability = mean(1.0 - row.post_threat_safe_probability for row in metrics),
        root_revision_mean = mean(row.root_revision for row in metrics),
    )
end

function aggregate_content_swap(metrics)
    return (
        melt_rate = mean(row.pruned ? 1.0 : 0.0 for row in metrics),
        root_revision_mean = mean(row.root_revision for row in metrics),
    )
end

function aggregate_et_flip(rows)
    return (
        structural_counts_bit_identical_rate = mean(row.structural_counts_bit_identical ? 1.0 : 0.0 for row in rows),
        low_pi_part_eff = mean(row.low_pi_part_eff for row in rows),
        high_pi_part_eff = mean(row.high_pi_part_eff for row in rows),
        low_lambda_ctx_eff = mean(row.low_lambda_ctx_eff for row in rows),
        high_lambda_ctx_eff = mean(row.high_lambda_ctx_eff for row in rows),
    )
end

function run_witnessing_variant(seeds, bundles, params::Sim2Params; E0::Float64 = params.E0, prior_log_odds::Float64 = params.prior_log_odds)
    variant = Sim2Params(;
        n_melt_trials = params.n_melt_trials,
        bmr_interval = params.bmr_interval,
        early_prompt_max_trial = params.early_prompt_max_trial,
        late_prompt_trial = params.late_prompt_trial,
        high_E = params.high_E,
        low_E = params.low_E,
        flip_trial = params.flip_trial,
        pi_part = params.pi_part,
        beta_se = params.beta_se,
        lambda_ctx = params.lambda_ctx,
        gamma_se = params.gamma_se,
        E0 = E0,
        E0_sweep = params.E0_sweep,
        prior_log_odds = prior_log_odds,
        prior_odds_offsets = params.prior_odds_offsets,
        relational_count_good = params.relational_count_good,
        relational_count_old = params.relational_count_old,
        ordinary_learning_rate = params.ordinary_learning_rate,
        attenuation_learning_rate = params.attenuation_learning_rate,
        policy_learning_rate = params.policy_learning_rate,
        policy_precision = params.policy_precision,
        root_avoidance_bias = params.root_avoidance_bias,
        danger_avoidance_bias = params.danger_avoidance_bias,
        competence_policy_floor = params.competence_policy_floor,
        full_prior_met = params.full_prior_met,
        full_prior_alone = params.full_prior_alone,
        reduced_prior_met = params.reduced_prior_met,
        reduced_prior_alone = params.reduced_prior_alone,
        bundle_dir = params.bundle_dir,
        bundle_files = params.bundle_files,
    )
    rows = NamedTuple[]
    for (idx, seed) in enumerate(seeds)
        bundle = bundles[mod1(idx, length(bundles))]
        metric, _ = simulate_condition(seed, bundle, variant, "witnessing")
        push!(rows, metric)
    end
    return rows
end

function aggregate_e0_sweep(seeds, bundles, params::Sim2Params)
    rows = NamedTuple[]
    for E0 in params.E0_sweep
        metrics = run_witnessing_variant(seeds, bundles, params; E0 = E0)
        push!(rows, (
            E0 = E0,
            melt_rate = mean(row.pruned ? 1.0 : 0.0 for row in metrics),
            mean_prune_trial = mean(row.prune_trial === nothing ? 0.0 : Float64(row.prune_trial) for row in metrics),
            mean_root_revision = mean(row.root_revision for row in metrics),
            mean_drop_fraction_in_window = mean(row.max_drop_fraction_in_window for row in metrics),
        ))
    end
    return rows
end

function aggregate_prior_odds_sweep(seeds, bundles, params::Sim2Params)
    rows = NamedTuple[]
    for offset in params.prior_odds_offsets
        prior_log_odds = params.prior_log_odds + offset
        metrics = run_witnessing_variant(seeds, bundles, params; prior_log_odds = prior_log_odds)
        push!(rows, (
            prior_log_odds = prior_log_odds,
            offset = offset,
            melt_rate = mean(row.pruned ? 1.0 : 0.0 for row in metrics),
            mean_prune_trial = mean(row.prune_trial === nothing ? 0.0 : Float64(row.prune_trial) for row in metrics),
            max_drop_fraction_in_window = mean(row.max_drop_fraction_in_window for row in metrics),
            window_fraction = mean(row.window_fraction for row in metrics),
        ))
    end
    return (
        rows = rows,
        min_max_drop_fraction_in_window = minimum(row.max_drop_fraction_in_window for row in rows),
        max_window_fraction = maximum(row.window_fraction for row in rows),
    )
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

function write_hysteresis_svg(path::AbstractString, traces)
    ensure_dir(dirname(path))
    regimes = collect(REGIMES)
    colors = Dict(
        "informational" => "#345995",
        "contact-under-capture" => "#7a5c00",
        "dissociative-quiet" => "#5f6b6d",
        "witnessing" => "#b33f62",
    )
    max_trial = maximum(row.trial for row in traces if row.condition in regimes)
    max_y = maximum(row.structural_root_precision for row in traces if row.condition in regimes)
    min_y = minimum(row.structural_root_precision for row in traces if row.condition in regimes)
    yspan = max(max_y - min_y, 1.0)

    function xy(trial, value)
        x = 70.0 + 470.0 * trial / max_trial
        y = 300.0 - 220.0 * (value - min_y) / yspan
        return x, y
    end

    polylines = String[]
    markers = String[]
    for (i, regime) in enumerate(regimes)
        rows = [row for row in traces if row.condition == regime]
        points = String[]
        for trial in 0:max_trial
            vals = [row.structural_root_precision for row in rows if row.trial == trial]
            isempty(vals) && continue
            x, y = xy(trial, mean(vals))
            push!(points, string(round(x; digits = 1), ",", round(y; digits = 1)))
        end
        push!(polylines, """<polyline points="$(join(points, " "))" fill="none" stroke="$(colors[regime])" stroke-width="4"/>""")
        prune_trials = [row.prune_trial for row in rows if row.prune_trial !== nothing]
        if !isempty(prune_trials)
            trial = round(Int, mean(Float64.(prune_trials)))
            x, _ = xy(trial, min_y)
            push!(markers, """<line x1="$(round(x; digits = 1))" y1="70" x2="$(round(x; digits = 1))" y2="305" stroke="$(colors[regime])" stroke-width="2" stroke-dasharray="5 4"/>""")
        end
        push!(markers, """<text x="555" y="$(95 + 24 * (i - 1))" font-family="Arial" font-size="12" fill="$(colors[regime])">$regime</text>""")
    end

    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="720" height="380" viewBox="0 0 720 380">
      <rect width="720" height="380" fill="#fbfaf7"/>
      <line x1="70" y1="300" x2="540" y2="300" stroke="#222" stroke-width="2"/>
      <line x1="70" y1="70" x2="70" y2="300" stroke="#222" stroke-width="2"/>
      <text x="70" y="38" font-family="Arial" font-size="18" fill="#222">Sim 2 hysteresis: structural precision vs corrective evidence</text>
      <text x="210" y="342" font-family="Arial" font-size="13" fill="#444">cumulative corrective observations</text>
      <text x="18" y="252" font-family="Arial" font-size="13" fill="#444" transform="rotate(-90 18 252)">root-coupling structural precision</text>
      $(join(markers, "\n      "))
      $(join(polylines, "\n      "))
    </svg>
    """
    open(path, "w") do io
        write(io, svg)
    end
    return path
end

function run_sim2_config(config::ExperimentConfig; config_path::Union{Nothing, AbstractString} = nothing, output_dir::Union{Nothing, AbstractString} = nothing)
    started = time()
    params = params_from_config(config, config_path)
    outdir = output_dir === nothing ? normpath(joinpath(config.output_dir, config.experiment, config.label === nothing ? Dates.format(Dates.now(Dates.UTC), Dates.dateformat"yyyymmddTHHMMSSZ") : config.label)) : output_dir
    ensure_dir(outdir)

    bundles = load_bundles(params)
    seeds = config.seeds
    length(seeds) >= 20 || error("Sim 2 requires at least 20 seeds")

    regime_metrics = NamedTuple[]
    traces = NamedTuple[]
    prompt_rows = NamedTuple[]
    real_danger_metrics = NamedTuple[]
    content_swap_metrics = NamedTuple[]
    et_flip_rows = NamedTuple[]

    for (idx, seed) in enumerate(seeds)
        bundle = bundles[mod1(idx, length(bundles))]
        for condition in REGIMES
            metric, condition_traces = simulate_condition(seed, bundle, params, condition)
            push!(regime_metrics, metric)
            append!(traces, condition_traces)
        end
        append!(prompt_rows, prompt_probe(seed, bundle, params))
        real_metric, _ = simulate_condition(seed, bundle, params, "real-danger")
        push!(real_danger_metrics, real_metric)
        swap_metric, _ = simulate_condition(seed, bundle, params, "content-swap")
        push!(content_swap_metrics, swap_metric)
        push!(et_flip_rows, et_flip_probe(seed, bundle, params))
    end

    e0_sweep_rows = aggregate_e0_sweep(seeds, bundles, params)
    prior_sweep = aggregate_prior_odds_sweep(seeds, bundles, params)
    regime_summary = aggregate_regimes(regime_metrics)
    relational_summary = aggregate_relational_accumulation(regime_metrics, params)
    melt_summary = aggregate_melt(regime_metrics)
    selective_summary = aggregate_selective_prune(regime_metrics)
    prompt_summary = aggregate_prompt(prompt_rows)
    real_danger_summary = aggregate_real_danger(real_danger_metrics)
    content_swap_summary = aggregate_content_swap(content_swap_metrics)
    et_flip_summary = aggregate_et_flip(et_flip_rows)

    imported = (
        manifest_dir = params.bundle_dir,
        bundle_count = length(bundles),
        acute_bundle_count = count(bundle -> bundle.family == "acute", bundles),
        slow_accumulation_bundle_count = count(bundle -> bundle.family == "slow_accumulation", bundles),
        bundles = [(file = bundle.file, seed = bundle.seed, route = bundle.route, family = bundle.family, structural_precision = bundle.structural_precision) for bundle in bundles],
    )

    summary = (
        experiment = "sim2",
        config = config_snapshot(config),
        imported_bundles = imported,
        d2_melt_gate = (
            implementation = "canonical prior-swap BMR over reflexively accessible counts",
            posterior = "a_E = b_F + rho(E_t) * n",
            rho = "E_t / (E_t + E_0)",
            E0 = params.E0,
            prior_log_odds = params.prior_log_odds,
            delta_at_E0_zero = 0.0,
        ),
        metrics = (
            regimes = regime_summary,
            relational_accumulation = relational_summary,
            melt_discreteness = melt_summary,
            selective_prune = selective_summary,
            premature_late = prompt_summary,
            real_danger = real_danger_summary,
            content_swap = content_swap_summary,
            et_flip = et_flip_summary,
            prior_odds_sweep = (
                min_max_drop_fraction_in_window = prior_sweep.min_max_drop_fraction_in_window,
                max_window_fraction = prior_sweep.max_window_fraction,
                rows = prior_sweep.rows,
            ),
            E0_sweep = e0_sweep_rows,
        ),
        per_seed_metric_count = length(regime_metrics),
        trace_row_count = length(traces),
    )

    summary_path = joinpath(outdir, "summary.json")
    write_json(summary_path, summary)
    write_rows_csv(joinpath(outdir, "per_seed_metrics.csv"), regime_metrics)
    write_rows_csv(joinpath(outdir, "posterior_traces.csv"), traces)
    write_rows_csv(joinpath(outdir, "prompt_probe_metrics.csv"), prompt_rows)
    write_rows_csv(joinpath(outdir, "real_danger_metrics.csv"), real_danger_metrics)
    write_rows_csv(joinpath(outdir, "content_swap_metrics.csv"), content_swap_metrics)
    write_rows_csv(joinpath(outdir, "et_flip_metrics.csv"), et_flip_rows)
    write_rows_csv(joinpath(outdir, "e0_sweep_metrics.csv"), e0_sweep_rows)
    write_rows_csv(joinpath(outdir, "prior_odds_sweep_metrics.csv"), prior_sweep.rows)
    write_hysteresis_svg(joinpath(outdir, "figures", "hysteresis.svg"), traces)

    criteria_results = nothing
    if !isnothing(config.criteria_path) && isfile(config.criteria_path)
        criteria_results = write_criteria_results(config.criteria_path, summary_path, joinpath(outdir, "criteria-results.json"))
    end
    status = (
        implementation_passed = length(seeds) >= 20 && !isempty(regime_metrics) && isfile(joinpath(outdir, "figures", "hysteresis.svg")),
        theory_result = theory_label(criteria_results),
        criteria_results_path = criteria_results === nothing ? nothing : joinpath(outdir, "criteria-results.json"),
    )
    write_json(joinpath(outdir, "status.json"), status)
    metadata = build_reproducibility_metadata(
        config;
        config_path = config_path,
        runtime_seconds = time() - started,
        repo_root = normpath(joinpath(@__DIR__, "..", "..", "..", "..", "..")),
        extra = (output_dir = abspath(outdir), sim_module = "EmergenceSuite.Sim2"),
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
