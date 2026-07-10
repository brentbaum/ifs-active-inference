module Sim2

using Dates
using JSON3
using Statistics

using ...BMR: accessibility_weight, bmr_delta_f_prior_swap
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
    primary_gate::String = "write"
    bmr_interval::Int = 5
    bmr_intervals::Vector{Int} = [3, 5, 10]
    accessibility_functions::Vector{String} = ["saturating", "threshold-linear"]
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
    access_threshold::Float64 = 0.20
    access_full::Float64 = 0.80
    prior_log_odds::Float64 = -5.0
    prior_odds_offsets::Vector{Float64} = [-1.0, 0.0, 1.0]
    relational_count_good::Float64 = 1.0
    relational_count_old::Float64 = 0.08
    informational_root_fraction::Float64 = 0.20
    ordinary_learning_rate::Float64 = 1.0
    attenuation_learning_rate::Float64 = 0.18
    policy_learning_rate::Float64 = 0.25
    policy_precision::Float64 = 3.0
    root_avoidance_bias::Float64 = 0.48
    danger_avoidance_bias::Float64 = 0.55
    competence_policy_floor::Float64 = 0.12
    bundle_dir::String = normpath(joinpath(@__DIR__, "..", "..", "..", "runs", "sim1", "sim1-t1-2", "artifacts"))
    bundle_files::Vector{String} = String[]
end

Base.@kwdef struct Bundle
    file::String
    schema_version::String
    seed::Int
    route::String
    family::String
    structural_precision::Float64
    threat_counts::Vector{Float64}
    policy_counts::Vector{Float64}
    root_full_prior::Vector{Float64}
    root_reduced_prior::Vector{Float64}
    root_prior_source_safe::Float64
    root_prior_source_threat::Float64
end

Base.@kwdef mutable struct AgentState
    root_present::Bool = true
    prune_trial::Union{Nothing, Int} = nothing
    root_counts::Vector{Float64}
    root_full_prior::Vector{Float64}
    root_reduced_prior::Vector{Float64}
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
    value = cor(Float64.(xs), Float64.(ys))
    return isfinite(value) ? value : 0.0
end

get_float(params, key::String, default::Float64) = haskey(params, key) ? Float64(params[key]) : default
get_int(params, key::String, default::Int) = haskey(params, key) ? Int(params[key]) : default
get_string(params, key::String, default::String) = haskey(params, key) ? string(params[key]) : default
get_float_vector(params, key::String, default::Vector{Float64}) = haskey(params, key) ? Float64.(params[key]) : default
get_int_vector(params, key::String, default::Vector{Int}) = haskey(params, key) ? Int.(params[key]) : default
get_string_vector(params, key::String, default::Vector{String}) = haskey(params, key) ? string.(params[key]) : default

function resolve_path(path::AbstractString, config_path::Union{Nothing, AbstractString})
    isabspath(path) && return normpath(path)
    base = config_path === nothing ? pwd() : dirname(config_path)
    return normpath(joinpath(base, path))
end

function params_from_config(config::ExperimentConfig, config_path::Union{Nothing, AbstractString})
    raw = config.model_params
    base = Sim2Params()
    params = Sim2Params(
        n_melt_trials = get_int(raw, "n_melt_trials", base.n_melt_trials),
        primary_gate = get_string(raw, "primary_gate", base.primary_gate),
        bmr_interval = get_int(raw, "bmr_interval", base.bmr_interval),
        bmr_intervals = get_int_vector(raw, "bmr_intervals", base.bmr_intervals),
        accessibility_functions = get_string_vector(raw, "accessibility_functions", base.accessibility_functions),
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
        access_threshold = get_float(raw, "access_threshold", base.access_threshold),
        access_full = get_float(raw, "access_full", base.access_full),
        prior_log_odds = get_float(raw, "prior_log_odds", base.prior_log_odds),
        prior_odds_offsets = get_float_vector(raw, "prior_odds_offsets", base.prior_odds_offsets),
        relational_count_good = get_float(raw, "relational_count_good", base.relational_count_good),
        relational_count_old = get_float(raw, "relational_count_old", base.relational_count_old),
        informational_root_fraction = get_float(raw, "informational_root_fraction", base.informational_root_fraction),
        ordinary_learning_rate = get_float(raw, "ordinary_learning_rate", base.ordinary_learning_rate),
        attenuation_learning_rate = get_float(raw, "attenuation_learning_rate", base.attenuation_learning_rate),
        policy_learning_rate = get_float(raw, "policy_learning_rate", base.policy_learning_rate),
        policy_precision = get_float(raw, "policy_precision", base.policy_precision),
        root_avoidance_bias = get_float(raw, "root_avoidance_bias", base.root_avoidance_bias),
        danger_avoidance_bias = get_float(raw, "danger_avoidance_bias", base.danger_avoidance_bias),
        competence_policy_floor = get_float(raw, "competence_policy_floor", base.competence_policy_floor),
        bundle_dir = resolve_path(string(get(raw, "bundle_dir", base.bundle_dir)), config_path),
        bundle_files = get_string_vector(raw, "bundle_files", base.bundle_files),
    )
    params.primary_gate in ("write", "access") || error("primary_gate must be write or access")
    sort(unique(params.bmr_intervals)) == [3, 5, 10] || error("T4.3 pilot must sweep BMR intervals 3, 5, and 10")
    Set(params.accessibility_functions) == Set(["saturating", "threshold-linear"]) || error("T4.3 requires saturating and threshold-linear accessibility functions")
    0.0 < params.informational_root_fraction < 1.0 || error("informational_root_fraction must be nonzero and weaker than relational routing")
    return params
end

function effective_precisions(params::Sim2Params, E_t::Float64)
    pi_part_eff = params.pi_part * exp(-params.beta_se * E_t)
    lambda_ctx_eff = params.lambda_ctx * exp(params.gamma_se * E_t)
    capture_index = pi_part_eff / (pi_part_eff + lambda_ctx_eff)
    return pi_part_eff, lambda_ctx_eff, capture_index
end

function d1_write_weight(params::Sim2Params, E_t::Float64)
    pi_eff, lambda_eff, _ = effective_precisions(params, E_t)
    high_pi, high_lambda, _ = effective_precisions(params, params.high_E)
    share = lambda_eff / (pi_eff + lambda_eff)
    high_share = high_lambda / (high_pi + high_lambda)
    return min(1.0, share / high_share)
end

content_root_route(params::Sim2Params, content::String) = content in ("met-well", "met-badly") ? 1.0 : content == "informational-safe" ? params.informational_root_fraction : 0.0

function root_write_weight(params::Sim2Params, content::String, E_t::Float64; attenuation::Bool, gate_mode::String)
    gate_mode in ("write", "access") || error("Unknown gate mode: $gate_mode")
    route = content_root_route(params, content)
    precision_weight = gate_mode == "write" ? d1_write_weight(params, E_t) : 1.0
    attenuation_weight = attenuation ? params.attenuation_learning_rate : 1.0
    return route * precision_weight * attenuation_weight
end

function access_form(name::String)
    name == "saturating" && return :saturating
    name == "threshold-linear" && return :threshold_linear
    error("Unknown accessibility function: $name")
end

function bmr_access_weight(params::Sim2Params, E_t::Float64, gate_mode::String, accessibility_function::String)
    gate_mode == "write" && return 1.0
    return accessibility_weight(E_t;
        form = access_form(accessibility_function),
        E0 = params.E0,
        threshold = params.access_threshold,
        full_access = params.access_full,
    )
end

function read_manifest_bundle_files(params::Sim2Params)
    !isempty(params.bundle_files) && return params.bundle_files
    manifest = JSON3.read(read(joinpath(params.bundle_dir, "bundle-manifest.json"), String))
    return String.(manifest.bundles)
end

function formation_root_priors(structural_precision::Float64, cue_safe::Float64, cue_threat::Float64)
    cue_total = cue_safe + cue_threat
    cue_total > 0 || error("Bundle cue counts must have positive mass")
    probabilities = [cue_safe, cue_threat] ./ cue_total
    inherited_mass = log1p(structural_precision)
    full = ones(2) .+ inherited_mass .* probabilities
    reduced = fill(sum(full) / 2.0, 2)
    return full, reduced
end

function load_bundle(params::Sim2Params, file::AbstractString)
    path = isabspath(file) ? file : joinpath(params.bundle_dir, file)
    raw = JSON3.read(read(path, String))
    schema = string(raw.schema_version)
    schema == "sim1.bundle.v2" || error("T4.3 pilot supports existing sim1.bundle.v2 artifacts; got $schema")
    banks = raw.cause_banks
    cue_safe = Float64(banks.cue_counts.safe)
    cue_threat = Float64(banks.cue_counts.threat)
    structural_precision = Float64(raw.revision_probe.structural_precision)
    full, reduced = formation_root_priors(structural_precision, cue_safe, cue_threat)
    route = string(raw.route)
    return Bundle(
        file = basename(path),
        schema_version = schema,
        seed = Int(raw.seed),
        route = route,
        family = occursin("slow", route) ? "slow_accumulation" : "acute",
        structural_precision = structural_precision,
        threat_counts = [Float64(banks.affect_counts.threat), Float64(banks.affect_counts.safe)],
        policy_counts = [Float64(banks.policy_counts.approach), Float64(banks.policy_counts.flee), Float64(banks.policy_counts.appease), Float64(banks.policy_counts.attenuate)],
        root_full_prior = full,
        root_reduced_prior = reduced,
        root_prior_source_safe = cue_safe,
        root_prior_source_threat = cue_threat,
    )
end

function load_bundles(params::Sim2Params)
    bundles = [load_bundle(params, file) for file in read_manifest_bundle_files(params)]
    any(bundle -> bundle.family == "slow_accumulation", bundles) || error("Sim 2 requires a slow-accumulation bundle")
    any(bundle -> bundle.family == "acute", bundles) || error("Sim 2 requires an acute bundle")
    return bundles
end

function initial_state(bundle::Bundle)
    return AgentState(
        root_counts = zeros(2),
        root_full_prior = copy(bundle.root_full_prior),
        root_reduced_prior = copy(bundle.root_reduced_prior),
        threat_counts = copy(bundle.threat_counts),
        policy_counts = copy(bundle.policy_counts),
        initial_threat_precision = sum(bundle.threat_counts),
        initial_policy_precision = sum(bundle.policy_counts),
    )
end

root_structural_precision(state::AgentState) = state.root_present ? sum(state.root_full_prior) + sum(state.root_counts) : sum(state.root_reduced_prior)
threat_safe_probability(state::AgentState) = state.threat_counts[THREAT_SAFE] / sum(state.threat_counts)

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
    state.threat_counts[safe_outcome ? THREAT_SAFE : THREAT_DANGER] += weight
    probs = policy_probs(state, params; dangerous_context = dangerous_context)
    if dangerous_context
        state.policy_counts[POLICY_FLEE] += params.policy_learning_rate * (probs[POLICY_FLEE] + 0.5)
    elseif state.root_present
        state.policy_counts[POLICY_ATTENUATE] += params.policy_learning_rate * (probs[POLICY_ATTENUATE] + 0.25)
    else
        state.policy_counts[POLICY_APPROACH] += params.policy_learning_rate * (probs[POLICY_APPROACH] + 0.5)
    end
end

function accumulate_root_observation!(state::AgentState, params::Sim2Params, content::String, E_t::Float64; attenuation::Bool, gate_mode::String)
    state.root_present || return 0.0
    weight = root_write_weight(params, content, E_t; attenuation = attenuation, gate_mode = gate_mode)
    weight <= 0 && return 0.0
    if content == "met-badly"
        state.root_counts[1] += weight * params.relational_count_old
        state.root_counts[2] += weight * params.relational_count_good
    else
        state.root_counts[1] += weight * params.relational_count_good
        state.root_counts[2] += weight * params.relational_count_old
    end
    return weight
end

function bmr_score(state::AgentState, params::Sim2Params, E_t::Float64; gate_mode::String, accessibility_function::String, prior_log_odds::Float64 = params.prior_log_odds)
    rho = bmr_access_weight(params, E_t, gate_mode, accessibility_function)
    posterior = state.root_full_prior .+ rho .* state.root_counts
    delta = bmr_delta_f_prior_swap(posterior, state.root_full_prior, state.root_reduced_prior)
    return delta, delta + prior_log_odds, rho
end

function maybe_prune!(state::AgentState, params::Sim2Params, trial::Int, E_t::Float64; gate_mode::String, accessibility_function::String, prior_log_odds::Float64 = params.prior_log_odds)
    state.root_present || return (delta = nothing, score = nothing, access = nothing, pruned_now = false)
    delta, score, rho = bmr_score(state, params, E_t; gate_mode = gate_mode, accessibility_function = accessibility_function, prior_log_odds = prior_log_odds)
    if score > 0
        state.root_present = false
        state.prune_trial = trial
        return (delta = delta, score = score, access = rho, pruned_now = true)
    end
    return (delta = delta, score = score, access = rho, pruned_now = false)
end

function condition_spec(condition::String, params::Sim2Params)
    condition == "informational" && return (E_t = params.low_E, content = "informational-safe", attenuation = false, safe_outcome = true, dangerous_context = false)
    condition == "contact-under-capture" && return (E_t = params.low_E, content = "met-well", attenuation = false, safe_outcome = true, dangerous_context = false)
    condition == "dissociative-quiet" && return (E_t = params.low_E, content = "met-well", attenuation = true, safe_outcome = true, dangerous_context = false)
    condition == "witnessing" && return (E_t = params.high_E, content = "met-well", attenuation = false, safe_outcome = true, dangerous_context = false)
    condition == "content-swap" && return (E_t = params.high_E, content = "informational-safe", attenuation = false, safe_outcome = true, dangerous_context = false)
    condition == "real-danger" && return (E_t = params.high_E, content = "met-well", attenuation = false, safe_outcome = false, dangerous_context = true)
    error("Unknown Sim 2 condition: $condition")
end

function trace_row(seed, bundle, condition, trial, state, params, spec, cumulative_evidence, bmr_result; gate_mode, accessibility_function, bmr_interval)
    pi_eff, lambda_eff, capture = effective_precisions(params, spec.E_t)
    probs = policy_probs(state, params; dangerous_context = spec.dangerous_context)
    return (
        seed = seed, bundle_file = bundle.file, bundle_family = bundle.family,
        condition = condition, gate_mode = gate_mode, accessibility_function = gate_mode == "write" ? "none-raw-count" : accessibility_function,
        bmr_interval = bmr_interval, trial = trial, cumulative_corrective_evidence = cumulative_evidence,
        observation_content = spec.content, content_root_route = content_root_route(params, spec.content),
        root_write_weight = root_write_weight(params, spec.content, spec.E_t; attenuation = spec.attenuation, gate_mode = gate_mode),
        attenuation = spec.attenuation, E_t = spec.E_t, pi_part_eff = pi_eff, lambda_ctx_eff = lambda_eff, capture_index = capture,
        bmr_access_weight = bmr_access_weight(params, spec.E_t, gate_mode, accessibility_function),
        structural_root_precision = root_structural_precision(state), structural_threat_precision = sum(state.threat_counts), structural_policy_precision = sum(state.policy_counts),
        root_present = state.root_present, prune_trial = state.prune_trial,
        bmr_delta = bmr_result.delta, bmr_score = bmr_result.score, pruned_now = bmr_result.pruned_now,
        root_counts_met = state.root_counts[1], root_counts_alone = state.root_counts[2], threat_safe_probability = threat_safe_probability(state),
        p_approach = probs[POLICY_APPROACH], p_flee = probs[POLICY_FLEE], p_appease = probs[POLICY_APPEASE], p_attenuate = probs[POLICY_ATTENUATE], p_avoidance = avoidance_rate(probs),
    )
end

function simulate_condition(seed::Int, bundle::Bundle, params::Sim2Params, condition::String; gate_mode::String = params.primary_gate, accessibility_function::String = first(params.accessibility_functions), bmr_interval::Int = params.bmr_interval, forced_prompt_trial::Union{Nothing, Int} = nothing, prior_log_odds::Float64 = params.prior_log_odds)
    spec = condition_spec(condition, params)
    state = initial_state(bundle)
    traces = NamedTuple[]
    empty_bmr = (delta = nothing, score = nothing, access = nothing, pruned_now = false)
    push!(traces, trace_row(seed, bundle, condition, 0, state, params, spec, 0, empty_bmr; gate_mode = gate_mode, accessibility_function = accessibility_function, bmr_interval = bmr_interval))
    pre_avoidance = avoidance_rate(policy_probs(state, params; dangerous_context = spec.dangerous_context))
    initial_root_precision = root_structural_precision(state)
    check_drops = Float64[]
    evaluations = 0

    for trial in 1:params.n_melt_trials
        accumulate_root_observation!(state, params, spec.content, spec.E_t; attenuation = spec.attenuation, gate_mode = gate_mode)
        update_ordinary_banks!(state, params; safe_outcome = spec.safe_outcome, attenuation = spec.attenuation, dangerous_context = spec.dangerous_context)
        check_bmr = trial % bmr_interval == 0 || (forced_prompt_trial !== nothing && trial == forced_prompt_trial)
        result = empty_bmr
        if check_bmr
            evaluations += 1
            pre_check = root_structural_precision(state)
            result = maybe_prune!(state, params, trial, spec.E_t; gate_mode = gate_mode, accessibility_function = accessibility_function, prior_log_odds = prior_log_odds)
            push!(check_drops, max(0.0, pre_check - root_structural_precision(state)))
        end
        push!(traces, trace_row(seed, bundle, condition, trial, state, params, spec, trial, result; gate_mode = gate_mode, accessibility_function = accessibility_function, bmr_interval = bmr_interval))
    end

    total_drop = sum(check_drops)
    largest_fraction = total_drop <= eps(Float64) ? 0.0 : maximum(check_drops) / total_drop
    post_probs = policy_probs(state, params; dangerous_context = spec.dangerous_context)
    metric = (
        seed = seed, bundle_file = bundle.file, bundle_family = bundle.family, condition = condition,
        gate_mode = gate_mode, accessibility_function = gate_mode == "write" ? "none-raw-count" : accessibility_function, bmr_interval = bmr_interval,
        prune_trial = state.prune_trial, pruned = state.prune_trial !== nothing, bmr_evaluations = evaluations,
        initial_root_precision = initial_root_precision, final_root_precision = root_structural_precision(state), root_revision = total_drop,
        largest_intercheck_drop_fraction = largest_fraction,
        initial_threat_precision = state.initial_threat_precision, final_threat_precision = sum(state.threat_counts),
        initial_policy_precision = state.initial_policy_precision, final_policy_precision = sum(state.policy_counts),
        pre_avoidance_rate = pre_avoidance, post_avoidance_rate = avoidance_rate(post_probs), compulsive_avoidance_drop = pre_avoidance - avoidance_rate(post_probs),
        post_approach_rate = post_probs[POLICY_APPROACH], post_threat_safe_probability = threat_safe_probability(state),
        root_counts_met = state.root_counts[1], root_counts_alone = state.root_counts[2],
        content_root_route = content_root_route(params, spec.content),
        root_write_weight = root_write_weight(params, spec.content, spec.E_t; attenuation = spec.attenuation, gate_mode = gate_mode),
        bmr_access_weight = bmr_access_weight(params, spec.E_t, gate_mode, accessibility_function),
    )
    return metric, traces
end

function aggregate_regimes(metrics)
    by_condition = Dict(condition => [row for row in metrics if row.condition == condition] for condition in REGIMES)
    revisions = Dict(condition => mean(row.root_revision for row in rows) for (condition, rows) in by_condition)
    melt_rates = Dict(condition => mean(row.pruned ? 1.0 : 0.0 for row in rows) for (condition, rows) in by_condition)
    witness = max(revisions["witnessing"], eps(Float64))
    return (
        root_revision_mean_by_regime = revisions,
        melt_rate_by_regime = melt_rates,
        informational_root_revision_mean = revisions["informational"],
        contact_under_capture_root_revision_mean = revisions["contact-under-capture"],
        dissociative_quiet_root_revision_mean = revisions["dissociative-quiet"],
        witnessing_root_revision_mean = revisions["witnessing"],
        max_non_witnessing_root_revision_ratio = maximum(revisions[name] for name in REGIMES if name != "witnessing") / witness,
    )
end

function aggregate_melt(metrics)
    witnessing = [row for row in metrics if row.condition == "witnessing"]
    pruned_trials = [Float64(row.prune_trial) for row in witnessing if row.prune_trial !== nothing]
    return (
        melt_rate = mean(row.pruned ? 1.0 : 0.0 for row in witnessing),
        mean_prune_trial = mean_or_zero(pruned_trials),
        largest_intercheck_drop_fraction = mean(row.largest_intercheck_drop_fraction for row in witnessing),
    )
end

function aggregate_selective_prune(metrics)
    rows = [row for row in metrics if row.condition == "witnessing"]
    threat_survival = mean(row.final_threat_precision / row.initial_threat_precision for row in rows)
    policy_survival = mean(row.final_policy_precision / row.initial_policy_precision for row in rows)
    return (
        min_bank_precision_survival_ratio = min(threat_survival, policy_survival),
        threat_bank_precision_survival_ratio = threat_survival,
        policy_bank_precision_survival_ratio = policy_survival,
        compulsive_avoidance_drop = mean(row.compulsive_avoidance_drop for row in rows),
    )
end

function prompt_probe(seed::Int, bundle::Bundle, params::Sim2Params; gate_mode::String = params.primary_gate, accessibility_function::String = first(params.accessibility_functions))
    early_trial = max(1, params.early_prompt_max_trial - (seed % 5))
    late_trial = min(params.n_melt_trials, params.late_prompt_trial + (seed % 7))
    prompt_count = 1 + (seed % 3)
    rows = NamedTuple[]
    for (phase, trial) in (("early", early_trial), ("late", late_trial))
        state = initial_state(bundle)
        for _ in 1:trial
            accumulate_root_observation!(state, params, "met-well", params.high_E; attenuation = false, gate_mode = gate_mode)
        end
        delta, score, access = bmr_score(state, params, params.high_E; gate_mode = gate_mode, accessibility_function = accessibility_function)
        push!(rows, (
            seed = seed, bundle_file = bundle.file, prompt_phase = phase, prompt_trial = trial, prompt_count = prompt_count,
            gate_mode = gate_mode, accessibility_function = gate_mode == "write" ? "none-raw-count" : accessibility_function,
            bmr_delta = delta, bmr_score = score, bmr_access_weight = access,
            failed = score <= 0.0, residual_accuracy_contribution = max(0.0, -score),
        ))
    end
    return rows
end

function aggregate_prompt(rows)
    early = [row for row in rows if row.prompt_phase == "early"]
    late = [row for row in rows if row.prompt_phase == "late"]
    failures = [row.failed ? 1.0 : 0.0 for row in rows]
    return (
        early_fail_rate = mean(row.failed ? 1.0 : 0.0 for row in early),
        late_success_rate = mean(row.failed ? 0.0 : 1.0 for row in late),
        failure_residual_accuracy_correlation = safe_correlation(failures, [row.residual_accuracy_contribution for row in rows]),
        failure_prompt_count_abs_correlation = abs(safe_correlation(failures, Float64.([row.prompt_count for row in rows]))),
    )
end

function et_flip_probe(seed::Int, bundle::Bundle, params::Sim2Params, gate_mode::String, accessibility_function::String)
    baseline = initial_state(bundle)
    flipped = initial_state(bundle)
    for trial in 1:params.n_melt_trials
        accumulate_root_observation!(baseline, params, "met-well", params.low_E; attenuation = false, gate_mode = gate_mode)
        E_t = trial == params.flip_trial ? params.high_E : params.low_E
        accumulate_root_observation!(flipped, params, "met-well", E_t; attenuation = false, gate_mode = gate_mode)
    end
    low_access = bmr_access_weight(params, params.low_E, gate_mode, accessibility_function)
    high_access = bmr_access_weight(params, params.high_E, gate_mode, accessibility_function)
    counts_identical = baseline.root_counts == flipped.root_counts
    passed = gate_mode == "write" ? (!counts_identical && low_access == high_access == 1.0) : (counts_identical && high_access > low_access)
    return (
        seed = seed, bundle_file = bundle.file, gate_mode = gate_mode,
        accessibility_function = gate_mode == "write" ? "none-raw-count" : accessibility_function,
        counts_bit_identical = counts_identical, low_bmr_access_weight = low_access, high_bmr_access_weight = high_access,
        baseline_root_counts_met = baseline.root_counts[1], flipped_root_counts_met = flipped.root_counts[1],
        exactly_one_melt_entry_changed = passed,
    )
end

function comparison_variants(params::Sim2Params)
    variants = [(gate_mode = "write", accessibility_function = first(params.accessibility_functions))]
    append!(variants, [(gate_mode = "access", accessibility_function = name) for name in params.accessibility_functions])
    return variants
end

function aggregate_comparison(rows)
    groups = Dict{Tuple{String, String, Int, String}, Vector{NamedTuple}}()
    for row in rows
        key = (row.gate_mode, row.accessibility_function, row.bmr_interval, row.condition)
        push!(get!(groups, key, NamedTuple[]), row)
    end
    out = NamedTuple[]
    for key in sort(collect(keys(groups)))
        members = groups[key]
        pruned_trials = [Float64(row.prune_trial) for row in members if row.prune_trial !== nothing]
        push!(out, (
            gate_mode = key[1], accessibility_function = key[2], bmr_interval = key[3], condition = key[4],
            melt_rate = mean(row.pruned ? 1.0 : 0.0 for row in members), mean_prune_trial = mean_or_zero(pruned_trials),
            mean_root_revision = mean(row.root_revision for row in members),
            mean_largest_intercheck_drop_fraction = mean(row.largest_intercheck_drop_fraction for row in members),
            mean_root_counts_met = mean(row.root_counts_met for row in members),
            mean_root_write_weight = mean(row.root_write_weight for row in members), mean_bmr_access_weight = mean(row.bmr_access_weight for row in members),
        ))
    end
    return out
end

function interval_robustness(rows, params::Sim2Params)
    access_name = params.primary_gate == "write" ? "none-raw-count" : first(params.accessibility_functions)
    selected = [row for row in rows if row.gate_mode == params.primary_gate && row.accessibility_function == access_name && row.condition == "witnessing"]
    return (
        intervals = sort([row.bmr_interval for row in selected]),
        min_witnessing_melt_rate = minimum(row.melt_rate for row in selected),
        min_largest_intercheck_drop_fraction = minimum(row.mean_largest_intercheck_drop_fraction for row in selected),
        melt_trial_range = maximum(row.mean_prune_trial for row in selected) - minimum(row.mean_prune_trial for row in selected),
    )
end

function accessibility_sensitivity(rows, params::Sim2Params)
    selected = [row for row in rows if row.gate_mode == "access" && row.bmr_interval == params.bmr_interval && row.condition == "witnessing"]
    return (
        functions = [row.accessibility_function for row in selected],
        min_witnessing_melt_rate = minimum(row.melt_rate for row in selected),
        melt_trial_range = maximum(row.mean_prune_trial for row in selected) - minimum(row.mean_prune_trial for row in selected),
        rows = selected,
    )
end

function aggregate_prior_odds_sweep(seeds, bundles, params::Sim2Params)
    rows = NamedTuple[]
    access_name = first(params.accessibility_functions)
    for offset in params.prior_odds_offsets, interval in params.bmr_intervals
        metrics = NamedTuple[]
        for (idx, seed) in enumerate(seeds)
            metric, _ = simulate_condition(seed, bundles[mod1(idx, length(bundles))], params, "witnessing";
                gate_mode = params.primary_gate, accessibility_function = access_name, bmr_interval = interval, prior_log_odds = params.prior_log_odds + offset)
            push!(metrics, metric)
        end
        push!(rows, (
            prior_log_odds = params.prior_log_odds + offset, offset = offset, bmr_interval = interval,
            melt_rate = mean(row.pruned ? 1.0 : 0.0 for row in metrics),
            largest_intercheck_drop_fraction = mean(row.largest_intercheck_drop_fraction for row in metrics),
        ))
    end
    return (
        rows = rows,
        min_melt_rate = minimum(row.melt_rate for row in rows),
        min_largest_intercheck_drop_fraction = minimum(row.largest_intercheck_drop_fraction for row in rows),
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
    colors = Dict("informational" => "#345995", "contact-under-capture" => "#7a5c00", "dissociative-quiet" => "#5f6b6d", "witnessing" => "#b33f62")
    max_trial = maximum(row.trial for row in traces)
    max_y = maximum(row.structural_root_precision for row in traces)
    min_y = minimum(row.structural_root_precision for row in traces)
    yspan = max(max_y - min_y, 1.0)
    xy(trial, value) = (70.0 + 470.0 * trial / max_trial, 300.0 - 220.0 * (value - min_y) / yspan)
    polylines = String[]
    labels = String[]
    for (idx, regime) in enumerate(REGIMES)
        rows = [row for row in traces if row.condition == regime]
        points = String[]
        for trial in 0:max_trial
            values = [row.structural_root_precision for row in rows if row.trial == trial]
            isempty(values) && continue
            x, y = xy(trial, mean(values))
            push!(points, "$(round(x; digits=1)),$(round(y; digits=1))")
        end
        push!(polylines, """<polyline points="$(join(points, " "))" fill="none" stroke="$(colors[regime])" stroke-width="4"/>""")
        push!(labels, """<text x="555" y="$(95 + 24 * (idx - 1))" font-family="Arial" font-size="12" fill="$(colors[regime])">$regime</text>""")
    end
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="720" height="380" viewBox="0 0 720 380">
      <rect width="720" height="380" fill="#fbfaf7"/><line x1="70" y1="300" x2="540" y2="300" stroke="#222" stroke-width="2"/><line x1="70" y1="70" x2="70" y2="300" stroke="#222" stroke-width="2"/>
      <text x="70" y="38" font-family="Arial" font-size="18" fill="#222">Sim 2 pilot: single-gate structural trajectories</text>
      <text x="210" y="342" font-family="Arial" font-size="13" fill="#444">cumulative corrective observations</text>
      <text x="18" y="252" font-family="Arial" font-size="13" fill="#444" transform="rotate(-90 18 252)">root structural precision</text>
      $(join(labels, "\n      "))
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
    config.label in ("pilot", "confirmatory") || error("Sim 2 runs only as pilot (Step A) or confirmatory (Step B, orchestrator-executed)")
    config.seeds == collect(1001:1010) || error("T4.3 STEP A is restricted to pilot seeds 1001-1010")
    outdir = output_dir === nothing ? normpath(joinpath(config.output_dir, config.experiment, "pilot")) : output_dir
    occursin(joinpath("runs", "sim2", "preregistered"), normpath(outdir)) && error("T4.3 STEP A must not write preregistered outputs")
    ensure_dir(outdir)

    bundles = load_bundles(params)
    seeds = config.seeds
    primary_access = first(params.accessibility_functions)
    regime_metrics = NamedTuple[]
    traces = NamedTuple[]
    prompt_rows = NamedTuple[]
    real_danger_metrics = NamedTuple[]
    content_swap_metrics = NamedTuple[]
    et_flip_rows = NamedTuple[]

    for (idx, seed) in enumerate(seeds)
        bundle = bundles[mod1(idx, length(bundles))]
        for condition in REGIMES
            metric, condition_traces = simulate_condition(seed, bundle, params, condition; gate_mode = params.primary_gate, accessibility_function = primary_access)
            push!(regime_metrics, metric)
            append!(traces, condition_traces)
        end
        append!(prompt_rows, prompt_probe(seed, bundle, params; gate_mode = params.primary_gate, accessibility_function = primary_access))
        real_metric, _ = simulate_condition(seed, bundle, params, "real-danger"; gate_mode = params.primary_gate, accessibility_function = primary_access)
        swap_metric, _ = simulate_condition(seed, bundle, params, "content-swap"; gate_mode = params.primary_gate, accessibility_function = primary_access)
        push!(real_danger_metrics, real_metric)
        push!(content_swap_metrics, swap_metric)
        for variant in comparison_variants(params)
            push!(et_flip_rows, et_flip_probe(seed, bundle, params, variant.gate_mode, variant.accessibility_function))
        end
    end

    comparison_per_seed = NamedTuple[]
    for variant in comparison_variants(params), interval in params.bmr_intervals, (idx, seed) in enumerate(seeds), condition in (REGIMES..., "content-swap")
        metric, _ = simulate_condition(seed, bundles[mod1(idx, length(bundles))], params, condition;
            gate_mode = variant.gate_mode, accessibility_function = variant.accessibility_function, bmr_interval = interval)
        push!(comparison_per_seed, metric)
    end
    comparison_rows = aggregate_comparison(comparison_per_seed)
    prior_sweep = aggregate_prior_odds_sweep(seeds, bundles, params)

    regime_summary = aggregate_regimes(regime_metrics)
    melt_summary = aggregate_melt(regime_metrics)
    selective_summary = aggregate_selective_prune(regime_metrics)
    prompt_summary = aggregate_prompt(prompt_rows)
    real_danger_summary = (
        adaptive_fear_preserved_rate = mean(row.post_avoidance_rate >= 0.70 ? 1.0 : 0.0 for row in real_danger_metrics),
        post_avoidance_rate = mean(row.post_avoidance_rate for row in real_danger_metrics),
        post_threat_danger_probability = mean(1.0 - row.post_threat_safe_probability for row in real_danger_metrics),
        root_revision_mean = mean(row.root_revision for row in real_danger_metrics),
    )
    content_swap_summary = (
        root_route_nonzero_rate = mean(row.content_root_route > 0 ? 1.0 : 0.0 for row in content_swap_metrics),
        mean_root_write_weight = mean(row.root_write_weight for row in content_swap_metrics),
        mean_root_counts_met = mean(row.root_counts_met for row in content_swap_metrics),
        melt_rate = mean(row.pruned ? 1.0 : 0.0 for row in content_swap_metrics),
        root_revision_mean = mean(row.root_revision for row in content_swap_metrics),
        relational_minus_informational_melt_rate = melt_summary.melt_rate - mean(row.pruned ? 1.0 : 0.0 for row in content_swap_metrics),
    )
    et_flip_summary = (
        single_entry_invariant_rate = mean(row.exactly_one_melt_entry_changed ? 1.0 : 0.0 for row in et_flip_rows),
        rows = et_flip_rows,
    )

    imported = (
        manifest_dir = params.bundle_dir,
        mapping = "v2 cue safe/threat proportions times log1p(revision_probe.structural_precision), plus unit Dirichlet base; reduced prior preserves inherited concentration and equalizes the two states",
        bundles = [(
            file = bundle.file, schema_version = bundle.schema_version, seed = bundle.seed, route = bundle.route, family = bundle.family,
            structural_precision = bundle.structural_precision, source_cue_safe = bundle.root_prior_source_safe, source_cue_threat = bundle.root_prior_source_threat,
            root_full_prior = bundle.root_full_prior, root_reduced_prior = bundle.root_reduced_prior,
        ) for bundle in bundles],
    )

    summary = (
        experiment = "sim2", phase4_ticket = "T4.3 STEP A", run_class = "pilot", config = config_snapshot(config),
        single_gate_design = (
            primary = "Option A / write: E_t changes D1 evidence weighting; canonical BMR reads raw actually-written counts",
            robustness = "Option B / access: writes are E_t-independent; rho(E_t) is the sole gate",
            primary_gate = params.primary_gate,
            option_a_bmr_access = "raw-count prior-swap (rho=1)",
            option_b_accessibility_functions = params.accessibility_functions,
        ),
        imported_bundles = imported,
        metrics = (
            regimes = regime_summary,
            melt_discreteness = melt_summary,
            selective_prune = selective_summary,
            premature_late = prompt_summary,
            real_danger = real_danger_summary,
            content_swap = content_swap_summary,
            et_flip = et_flip_summary,
            interval_robustness = interval_robustness(comparison_rows, params),
            accessibility_sensitivity = accessibility_sensitivity(comparison_rows, params),
            single_gate_comparison = comparison_rows,
            prior_odds_sweep = prior_sweep,
        ),
        per_seed_metric_count = length(regime_metrics), trace_row_count = length(traces),
    )

    summary_path = joinpath(outdir, "summary.json")
    write_json(summary_path, summary)
    write_rows_csv(joinpath(outdir, "per_seed_metrics.csv"), regime_metrics)
    write_rows_csv(joinpath(outdir, "posterior_traces.csv"), traces)
    write_rows_csv(joinpath(outdir, "prompt_probe_metrics.csv"), prompt_rows)
    write_rows_csv(joinpath(outdir, "real_danger_metrics.csv"), real_danger_metrics)
    write_rows_csv(joinpath(outdir, "content_swap_metrics.csv"), content_swap_metrics)
    write_rows_csv(joinpath(outdir, "et_flip_metrics.csv"), et_flip_rows)
    write_rows_csv(joinpath(outdir, "single_gate_comparison_per_seed.csv"), comparison_per_seed)
    write_rows_csv(joinpath(outdir, "single_gate_comparison_metrics.csv"), comparison_rows)
    write_rows_csv(joinpath(outdir, "prior_odds_sweep_metrics.csv"), prior_sweep.rows)
    write_hysteresis_svg(joinpath(outdir, "figures", "hysteresis.svg"), traces)

    criteria_results = !isnothing(config.criteria_path) && isfile(config.criteria_path) ? write_criteria_results(config.criteria_path, summary_path, joinpath(outdir, "criteria-results.json")) : nothing
    status = (
        implementation_passed = config.seeds == collect(1001:1010) && config.label == "pilot" && isfile(joinpath(outdir, "figures", "hysteresis.svg")),
        theory_result = theory_label(criteria_results), criteria_results_path = criteria_results === nothing ? nothing : joinpath(outdir, "criteria-results.json"),
        stop_after_pilot = true,
    )
    write_json(joinpath(outdir, "status.json"), status)
    metadata = build_reproducibility_metadata(config;
        config_path = config_path, runtime_seconds = time() - started,
        repo_root = normpath(joinpath(@__DIR__, "..", "..", "..", "..", "..")),
        extra = (output_dir = abspath(outdir), sim_module = "EmergenceSuite.Sim2", phase4_protocol = "STEP A PILOT ONLY"),
    )
    write_json(joinpath(outdir, "metadata.json"), metadata)
    return (output_dir = outdir, summary = summary, status = status, criteria_results = criteria_results)
end

end
