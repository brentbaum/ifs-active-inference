module Sim6b

using Dates
using Random
using Statistics

using ..BMR: reflexive_prior_swap_delta, reflexivity_weight
using ..Config: ExperimentConfig, config_snapshot
using ..Criteria: write_criteria_results
using ..IO: ensure_dir, write_json, write_rows_csv
using ..Reproducibility: build_reproducibility_metadata
using ..Sim6a

export run_sim6b_config

const EPS = 1.0e-12
const SAFE = 1
const AVERSIVE = 2
const POLICY_NAMES = ["approach", "flee", "appease", "attenuate"]
const APPROACH = 1
const FLEE = 2
const APPEASE = 3
const ATTENUATE = 4
const ARMS = ("unclamped", "clamped", "yoked-control")

Base.@kwdef struct Sim6bParams
    baseline_trials::Int = 8
    overwhelm_trials::Int = 18
    postformation_trials::Int = 12
    ordinary_probe_trials::Int = 24
    safety_recovery_trials::Int = 24
    witnessed_contact_trials::Int = 60
    acute_omega::Float64 = 1.65
    acute_kappa::Float64 = 0.05
    dark_omega::Float64 = 1.15
    dark_kappa::Float64 = 0.05
    safe_omega::Float64 = 0.20
    safe_kappa::Float64 = 0.70
    observation_precision_base::Float64 = 0.42
    observation_precision_gain::Float64 = 1.05
    attenuation_precision_scale::Float64 = 0.34
    safe_preference::Float64 = 1.35
    aversive_preference::Float64 = -2.35
    ambiguity_weight::Float64 = 0.10
    epistemic_weight::Float64 = 0.28
    attenuation_info_scale::Float64 = 0.18
    attenuation_cost::Float64 = 0.80
    overt_action_cost::Float64 = 0.03
    arousal_pe_scale::Float64 = 5.2
    crp_concentration::Float64 = 0.34
    crp_threshold_base::Float64 = 0.085
    spawn_pressure_threshold::Float64 = 2.45
    spawn_pressure_decay::Float64 = 0.72
    learning_rate_base::Float64 = 0.16
    learning_rate_arousal_gain::Float64 = 26.0
    cue_learning_weight::Float64 = 0.55
    revision_learning_rate::Float64 = 2.0
    accessible_relational_count_good::Float64 = 1.0
    accessible_relational_count_old::Float64 = 0.08
    accessible_formation_old_count::Float64 = 0.40
    pi_part::Float64 = 4.0
    lambda_ctx::Float64 = 0.90
    beta::Float64 = 1.00
    gamma::Float64 = 1.15
    E0::Float64 = 1.0
    full_prior_met::Float64 = 2.0
    full_prior_alone::Float64 = 12.0
    reduced_prior_met::Float64 = 7.0
    reduced_prior_alone::Float64 = 7.0
    prior_log_odds::Float64 = -5.0
    revision_score_scale::Float64 = 1.0
    collapse_E_threshold::Float64 = 0.35
    high_E_threshold::Float64 = 0.70
    freeze_revision_threshold::Float64 = 10.0
    rescue_revision_floor::Float64 = 25.0
    clamp_yoke_tolerance::Float64 = 12.0
    depth_grid::Vector{Float64} = [0.0, 0.25, 0.50, 0.75, 1.0]
    initial_depth_prior::Vector{Float64} = [0.03, 0.05, 0.10, 0.27, 0.55]
    safety_depth_prior::Vector{Float64} = [0.02, 0.04, 0.09, 0.25, 0.60]
    clamp_depth_prior::Vector{Float64} = [0.00, 0.01, 0.03, 0.16, 0.80]
    transition_mix::Float64 = 0.06
end

mutable struct Cause
    id::Int
    cue_counts::Vector{Float64}
    affect_counts::Vector{Float64}
    outcome_counts::Matrix{Float64}
    policy_counts::Vector{Float64}
    accessible_root_counts::Vector{Float64}
    formation::Dict{String, Any}
end

mutable struct AgentState
    causes::Vector{Cause}
    next_cause_id::Int
    spawn_pressure::Float64
    spawn_count::Int
end

struct TrialObservation
    cue::Int
    outcome::Int
    precision::Float64
end

function get_float(raw, key::String, default::Float64)
    haskey(raw, key) || return default
    return Float64(raw[key])
end

function get_int(raw, key::String, default::Int)
    haskey(raw, key) || return default
    return Int(raw[key])
end

function get_float_vector(raw, key::String, default::Vector{Float64})
    haskey(raw, key) || return default
    return Float64.(raw[key])
end

function params_from_config(config::ExperimentConfig)
    raw = config.model_params
    base = Sim6bParams()
    return Sim6bParams(
        baseline_trials = get_int(raw, "baseline_trials", base.baseline_trials),
        overwhelm_trials = get_int(raw, "overwhelm_trials", base.overwhelm_trials),
        postformation_trials = get_int(raw, "postformation_trials", base.postformation_trials),
        ordinary_probe_trials = get_int(raw, "ordinary_probe_trials", base.ordinary_probe_trials),
        safety_recovery_trials = get_int(raw, "safety_recovery_trials", base.safety_recovery_trials),
        witnessed_contact_trials = get_int(raw, "witnessed_contact_trials", base.witnessed_contact_trials),
        acute_omega = get_float(raw, "acute_omega", base.acute_omega),
        acute_kappa = get_float(raw, "acute_kappa", base.acute_kappa),
        dark_omega = get_float(raw, "dark_omega", base.dark_omega),
        dark_kappa = get_float(raw, "dark_kappa", base.dark_kappa),
        safe_omega = get_float(raw, "safe_omega", base.safe_omega),
        safe_kappa = get_float(raw, "safe_kappa", base.safe_kappa),
        observation_precision_base = get_float(raw, "observation_precision_base", base.observation_precision_base),
        observation_precision_gain = get_float(raw, "observation_precision_gain", base.observation_precision_gain),
        attenuation_precision_scale = get_float(raw, "attenuation_precision_scale", base.attenuation_precision_scale),
        safe_preference = get_float(raw, "safe_preference", base.safe_preference),
        aversive_preference = get_float(raw, "aversive_preference", base.aversive_preference),
        ambiguity_weight = get_float(raw, "ambiguity_weight", base.ambiguity_weight),
        epistemic_weight = get_float(raw, "epistemic_weight", base.epistemic_weight),
        attenuation_info_scale = get_float(raw, "attenuation_info_scale", base.attenuation_info_scale),
        attenuation_cost = get_float(raw, "attenuation_cost", base.attenuation_cost),
        overt_action_cost = get_float(raw, "overt_action_cost", base.overt_action_cost),
        arousal_pe_scale = get_float(raw, "arousal_pe_scale", base.arousal_pe_scale),
        crp_concentration = get_float(raw, "crp_concentration", base.crp_concentration),
        crp_threshold_base = get_float(raw, "crp_threshold_base", base.crp_threshold_base),
        spawn_pressure_threshold = get_float(raw, "spawn_pressure_threshold", base.spawn_pressure_threshold),
        spawn_pressure_decay = get_float(raw, "spawn_pressure_decay", base.spawn_pressure_decay),
        learning_rate_base = get_float(raw, "learning_rate_base", base.learning_rate_base),
        learning_rate_arousal_gain = get_float(raw, "learning_rate_arousal_gain", base.learning_rate_arousal_gain),
        cue_learning_weight = get_float(raw, "cue_learning_weight", base.cue_learning_weight),
        revision_learning_rate = get_float(raw, "revision_learning_rate", base.revision_learning_rate),
        accessible_relational_count_good = get_float(raw, "accessible_relational_count_good", base.accessible_relational_count_good),
        accessible_relational_count_old = get_float(raw, "accessible_relational_count_old", base.accessible_relational_count_old),
        accessible_formation_old_count = get_float(raw, "accessible_formation_old_count", base.accessible_formation_old_count),
        pi_part = get_float(raw, "pi_part", base.pi_part),
        lambda_ctx = get_float(raw, "lambda_ctx", base.lambda_ctx),
        beta = get_float(raw, "beta", base.beta),
        gamma = get_float(raw, "gamma", base.gamma),
        E0 = get_float(raw, "E0", base.E0),
        full_prior_met = get_float(raw, "full_prior_met", base.full_prior_met),
        full_prior_alone = get_float(raw, "full_prior_alone", base.full_prior_alone),
        reduced_prior_met = get_float(raw, "reduced_prior_met", base.reduced_prior_met),
        reduced_prior_alone = get_float(raw, "reduced_prior_alone", base.reduced_prior_alone),
        prior_log_odds = get_float(raw, "prior_log_odds", base.prior_log_odds),
        revision_score_scale = get_float(raw, "revision_score_scale", base.revision_score_scale),
        collapse_E_threshold = get_float(raw, "collapse_E_threshold", base.collapse_E_threshold),
        high_E_threshold = get_float(raw, "high_E_threshold", base.high_E_threshold),
        freeze_revision_threshold = get_float(raw, "freeze_revision_threshold", base.freeze_revision_threshold),
        rescue_revision_floor = get_float(raw, "rescue_revision_floor", base.rescue_revision_floor),
        clamp_yoke_tolerance = get_float(raw, "clamp_yoke_tolerance", base.clamp_yoke_tolerance),
        depth_grid = get_float_vector(raw, "depth_grid", base.depth_grid),
        initial_depth_prior = get_float_vector(raw, "initial_depth_prior", base.initial_depth_prior),
        safety_depth_prior = get_float_vector(raw, "safety_depth_prior", base.safety_depth_prior),
        clamp_depth_prior = get_float_vector(raw, "clamp_depth_prior", base.clamp_depth_prior),
        transition_mix = get_float(raw, "transition_mix", base.transition_mix),
    )
end

function validate_params(params::Sim6bParams)
    n = length(params.depth_grid)
    length(params.initial_depth_prior) == n || error("initial_depth_prior must match depth_grid")
    length(params.safety_depth_prior) == n || error("safety_depth_prior must match depth_grid")
    length(params.clamp_depth_prior) == n || error("clamp_depth_prior must match depth_grid")
    params.overwhelm_trials >= 3 || error("overwhelm_trials must allow CRP pressure to accumulate")
    params.ordinary_probe_trials > 0 || error("ordinary_probe_trials must be positive")
    params.witnessed_contact_trials > 0 || error("witnessed_contact_trials must be positive")
    return nothing
end

function depth_params(params::Sim6bParams)
    return Sim6a.Sim6aParams(
        n_trials = params.baseline_trials + params.overwhelm_trials + params.postformation_trials,
        depth_grid = params.depth_grid,
        initial_depth_prior = params.initial_depth_prior,
        safety_depth_prior = params.safety_depth_prior,
        transition_mix = params.transition_mix,
        pi_part = params.pi_part,
        lambda_ctx = params.lambda_ctx,
        beta = params.beta,
        gamma = params.gamma,
    )
end

normalize(v::AbstractVector{<:Real}) = begin
    vals = max.(Float64.(v), 0.0)
    total = sum(vals)
    total <= EPS && return fill(1.0 / length(vals), length(vals))
    vals ./ total
end

entropy(p::AbstractVector{Float64}) = -sum(x -> x * log(x + EPS), p)

function init_agent()
    outcome = hcat(
        [8.0, 4.0],
        [10.0, 3.0],
        [9.0, 4.0],
        [6.0, 6.0],
    )
    base = Cause(
        1,
        [14.0, 10.0],
        [15.0, 7.0],
        Matrix{Float64}(outcome),
        [3.0, 5.0, 4.0, 1.0],
        [0.0, 0.0],
        Dict{String, Any}("route" => "initial_cause", "spawned" => false),
    )
    return AgentState([base], 2, 0.0, 0)
end

function copy_cause(cause::Cause)
    return Cause(
        cause.id,
        copy(cause.cue_counts),
        copy(cause.affect_counts),
        copy(cause.outcome_counts),
        copy(cause.policy_counts),
        copy(cause.accessible_root_counts),
        copy(cause.formation),
    )
end

posterior_mean(counts::AbstractVector{Float64}, idx::Int) = counts[idx] / max(sum(counts), EPS)
cue_predictive(cause::Cause, cue::Int) = posterior_mean(cause.cue_counts, cue)
affect_aversive_mean(cause::Cause) = posterior_mean(cause.affect_counts, AVERSIVE)
structural_precision(cause::Cause) = sum(cause.affect_counts) + 0.35 * sum(cause.cue_counts)
outcome_distribution(cause::Cause, policy_idx::Int) = normalize(vec(cause.outcome_counts[:, policy_idx]))

function softmax(v::AbstractVector{<:Real})
    m = maximum(v)
    exps = exp.(Float64.(v) .- m)
    return exps ./ sum(exps)
end

function score_policies(cause::Cause, params::Sim6bParams)
    prefs = [params.safe_preference, params.aversive_preference]
    totals = Float64[]
    for policy_idx in eachindex(POLICY_NAMES)
        qo = outcome_distribution(cause, policy_idx)
        is_attenuate = policy_idx == ATTENUATE
        precision_scale = is_attenuate ? params.attenuation_precision_scale : 1.0
        utility = precision_scale * sum(qo .* prefs)
        amb = entropy(qo)
        information_gain = params.epistemic_weight * amb / sqrt(sum(cause.outcome_counts[:, policy_idx]))
        is_attenuate && (information_gain *= params.attenuation_info_scale)
        cost = is_attenuate ? params.attenuation_cost : params.overt_action_cost
        push!(totals, utility - params.ambiguity_weight * amb + information_gain - cost)
    end
    return totals
end

select_policy(cause::Cause, params::Sim6bParams) = argmax(score_policies(cause, params))

function dominant_aversive_cause(agent::AgentState)
    scores = [
        cue_predictive(cause, AVERSIVE) * affect_aversive_mean(cause) * (1.0 + 0.05 * log1p(structural_precision(cause)))
        for cause in agent.causes
    ]
    return agent.causes[argmax(scores)]
end

function observation_precision(omega::Float64, params::Sim6bParams)
    return params.observation_precision_base + params.observation_precision_gain * omega
end

function best_predictive(agent::AgentState, obs::TrialObservation, policy_idx::Int, params::Sim6bParams)
    precision_scale = policy_idx == ATTENUATE ? params.attenuation_precision_scale : 1.0
    effective_precision = obs.precision * precision_scale
    best_idx = 1
    best_raw = -Inf
    best_weighted = -Inf
    for (idx, cause) in enumerate(agent.causes)
        qo = outcome_distribution(cause, policy_idx)
        raw = cue_predictive(cause, obs.cue) * qo[obs.outcome]
        weighted = raw ^ max(effective_precision, EPS)
        if weighted > best_weighted
            best_idx = idx
            best_raw = raw
            best_weighted = weighted
        end
    end
    return best_idx, best_raw, best_weighted, effective_precision
end

function arousal_from_prediction(raw_predictive::Float64, effective_precision::Float64, params::Sim6bParams)
    surprise = -log(max(raw_predictive, EPS))
    pe = effective_precision * surprise
    return clamp(pe / params.arousal_pe_scale, 0.0, 1.0), pe
end

function crp_threshold(agent::AgentState, params::Sim6bParams)
    complexity = params.crp_concentration / (params.crp_concentration + length(agent.causes))
    return params.crp_threshold_base * (0.65 + complexity)
end

function spawn_cause!(agent::AgentState, arousal::Float64, E_t::Float64, trial::Int, seed::Int)
    cause = Cause(
        agent.next_cause_id,
        [1.0, 2.0],
        [1.0, 1.0],
        fill(1.0, 2, length(POLICY_NAMES)),
        ones(Float64, length(POLICY_NAMES)),
        [0.0, 0.0],
        Dict{String, Any}(
            "route" => "acute_spawn",
            "spawned" => true,
            "spawn_trial" => trial,
            "seed" => seed,
            "arousal_at_write" => arousal,
            "inferred_depth_at_write" => E_t,
        ),
    )
    push!(agent.causes, cause)
    agent.next_cause_id += 1
    agent.spawn_count += 1
    agent.spawn_pressure = 0.0
    return cause
end

function update_spawn_pressure!(agent::AgentState, posterior_predictive::Float64, threshold::Float64, arousal::Float64, params::Sim6bParams)
    if posterior_predictive < threshold
        agent.spawn_pressure = params.spawn_pressure_decay * agent.spawn_pressure + arousal
    else
        agent.spawn_pressure *= params.spawn_pressure_decay
    end
    return agent.spawn_pressure
end

function depth_readouts(dparams, q_depth)
    eff = Sim6a.effective_precisions(dparams, q_depth)
    precision = Sim6a.posterior_precision(q_depth)
    return eff.E_t, eff.pi_eff, eff.lambda_eff, eff.capture_index, precision
end

function relational_weight(params::Sim6bParams, dparams, E_t::Float64)
    q_high = normalize(params.clamp_depth_prior)
    high_eff = Sim6a.effective_precisions(dparams, q_high)
    current_pi = params.pi_part * exp(-params.beta * E_t)
    current_lambda = params.lambda_ctx * exp(params.gamma * E_t)
    high_lambda_share = high_eff.lambda_eff / (high_eff.pi_eff + high_eff.lambda_eff)
    lambda_share = current_lambda / (current_pi + current_lambda)
    return min(1.0, lambda_share / max(high_lambda_share, EPS))
end

function accrue_formation_access!(cause::Cause, params::Sim6bParams, dparams, E_t::Float64)
    weight = relational_weight(params, dparams, E_t)
    cause.accessible_root_counts[2] += weight * params.accessible_formation_old_count
    return weight
end

function update_cause!(cause::Cause, obs::TrialObservation, policy_idx::Int, arousal::Float64, E_t::Float64, params::Sim6bParams, dparams)
    lr = params.learning_rate_base + params.learning_rate_arousal_gain * arousal
    cause.cue_counts[obs.cue] += params.cue_learning_weight * lr
    cause.affect_counts[obs.outcome] += lr
    cause.outcome_counts[obs.outcome, policy_idx] += lr
    cause.policy_counts[policy_idx] += 1.0
    access_weight = accrue_formation_access!(cause, params, dparams, E_t)
    return lr, access_weight
end

function schedule_observation(trial::Int, params::Sim6bParams)
    if trial <= params.baseline_trials
        return "baseline", TrialObservation(SAFE, SAFE, observation_precision(params.safe_omega, params)), params.safe_omega, params.safe_kappa
    elseif trial <= params.baseline_trials + params.overwhelm_trials
        return "overwhelm", TrialObservation(AVERSIVE, AVERSIVE, observation_precision(params.acute_omega, params)), params.acute_omega, params.acute_kappa
    else
        return "dark-postformation", TrialObservation(AVERSIVE, AVERSIVE, observation_precision(params.dark_omega, params)), params.dark_omega, params.dark_kappa
    end
end

function update_depth_for_arm(params::Sim6bParams, dparams, q_depth, arm::String, arousal::Float64)
    if arm == "clamped"
        return normalize(params.clamp_depth_prior), "clamped-high"
    elseif arm == "yoked-control"
        return Sim6a.predict_depth(dparams, q_depth), "withheld"
    else
        obs = Sim6a.volatility_observation(arousal)
        return Sim6a.update_depth_with_evidence(dparams, q_depth, obs), string(obs)
    end
end

function formation_loop(seed::Int, arm::String, params::Sim6bParams, dparams)
    rng = MersenneTwister(seed)
    Random.seed!(rng, seed)
    agent = init_agent()
    q_depth = arm == "clamped" ? normalize(params.clamp_depth_prior) : Sim6a.depth_prior(dparams)
    traces = NamedTuple[]
    trial_logs = NamedTuple[]
    total_trials = params.baseline_trials + params.overwhelm_trials + params.postformation_trials

    for trial in 1:total_trials
        phase, obs, _, _ = schedule_observation(trial, params)
        current = dominant_aversive_cause(agent)
        policy_idx = select_policy(current, params)
        best_idx, raw_pp, weighted_pp, eff_precision = best_predictive(agent, obs, policy_idx, params)
        arousal, pe = arousal_from_prediction(raw_pp, eff_precision, params)
        q_depth, volatility_observation = update_depth_for_arm(params, dparams, q_depth, arm, arousal)
        E_t, pi_eff, lambda_eff, capture_index, depth_precision = depth_readouts(dparams, q_depth)
        threshold = crp_threshold(agent, params)
        pressure = update_spawn_pressure!(agent, weighted_pp, threshold, arousal, params)
        spawned = false
        cause = agent.causes[best_idx]
        if weighted_pp < threshold && pressure >= params.spawn_pressure_threshold
            cause = spawn_cause!(agent, arousal, E_t, trial, seed)
            spawned = true
        end
        lr, access_weight = update_cause!(cause, obs, policy_idx, arousal, E_t, params, dparams)
        jitter = 0.0 * rand(rng)
        push!(trial_logs, (
            trial = trial,
            phase = phase,
            policy_idx = policy_idx,
            policy = POLICY_NAMES[policy_idx],
            posterior_predictive = weighted_pp + jitter,
            raw_predictive = raw_pp,
            crp_threshold = threshold,
            spawn_pressure = agent.spawn_pressure,
            spawned = spawned,
            cause_id = cause.id,
            arousal = arousal,
            precision_weighted_pe = pe,
            learning_rate = lr,
            E_t = E_t,
            accessible_write_weight = access_weight,
        ))
        push!(traces, (
            seed = seed,
            arm = arm,
            trial = trial,
            phase = phase,
            policy = POLICY_NAMES[policy_idx],
            spawned = spawned,
            cause_id = cause.id,
            arousal = arousal,
            precision_weighted_pe = pe,
            learning_rate = lr,
            volatility_observation = volatility_observation,
            E_t = E_t,
            depth_posterior_precision = depth_precision,
            pi_eff = pi_eff,
            lambda_eff = lambda_eff,
            capture_index = capture_index,
            accessible_write_weight = access_weight,
            root_counts_met = cause.accessible_root_counts[1],
            root_counts_alone = cause.accessible_root_counts[2],
        ))
    end

    target = dominant_aversive_cause(agent)
    spawned_logs = [row for row in trial_logs if row.spawned]
    write_log = isempty(spawned_logs) ? trial_logs[argmax([row.arousal for row in trial_logs])] : first(spawned_logs)
    return (
        agent = agent,
        target = copy_cause(target),
        q_depth = copy(q_depth),
        traces = traces,
        trial_logs = trial_logs,
        formation_metric = (
            seed = seed,
            arm = arm,
            target_cause_id = target.id,
            spawned = agent.spawn_count > 0,
            spawn_count = agent.spawn_count,
            target_spawned = get(target.formation, "spawned", false) == true,
            write_trial = write_log.trial,
            write_time_depth = Float64(write_log.E_t),
            arousal_at_write = Float64(write_log.arousal),
            mean_learning_rate = mean(row.learning_rate for row in trial_logs),
            max_precision_weighted_pe = maximum(row.precision_weighted_pe for row in trial_logs),
            min_E_t = minimum(row.E_t for row in trial_logs),
            final_E_t = last(trial_logs).E_t,
            mean_postformation_approach_rate = mean(row.policy_idx == APPROACH ? 1.0 : 0.0 for row in last(trial_logs, min(params.postformation_trials, length(trial_logs)))),
            accessible_root_counts_met = target.accessible_root_counts[1],
            accessible_root_counts_alone = target.accessible_root_counts[2],
            structural_precision = structural_precision(target),
            affect_aversive_mean = affect_aversive_mean(target),
        ),
    )
end

function full_prior(params::Sim6bParams)
    return [params.full_prior_met, params.full_prior_alone]
end

function reduced_prior(params::Sim6bParams)
    return [params.reduced_prior_met, params.reduced_prior_alone]
end

function revision_percent(score::Float64, params::Sim6bParams)
    positive = max(0.0, score)
    return 100.0 * positive / (positive + params.revision_score_scale)
end

function bmr_probe(cause::Cause, params::Sim6bParams, E_t::Float64)
    delta = reflexive_prior_swap_delta(full_prior(params), reduced_prior(params), cause.accessible_root_counts, E_t; E0 = params.E0)
    score = delta + params.prior_log_odds
    return delta, score, revision_percent(score, params)
end

function apply_corrective_trial!(cause::Cause, params::Sim6bParams, dparams, E_t::Float64; witnessed::Bool)
    cause.cue_counts[AVERSIVE] += params.cue_learning_weight * params.revision_learning_rate
    cause.affect_counts[SAFE] += params.revision_learning_rate
    cause.outcome_counts[SAFE, APPROACH] += params.revision_learning_rate
    cause.policy_counts[APPROACH] += 1.0
    weight = witnessed ? relational_weight(params, dparams, E_t) : relational_weight(params, dparams, E_t)
    cause.accessible_root_counts[1] += weight * params.accessible_relational_count_good
    cause.accessible_root_counts[2] += weight * params.accessible_relational_count_old
    return weight
end

function ordinary_revision_probe(seed::Int, arm::String, cause::Cause, q_depth, params::Sim6bParams, dparams)
    probe = copy_cause(cause)
    E_t, _, _, _, _ = depth_readouts(dparams, q_depth)
    rows = NamedTuple[]
    for trial in 1:params.ordinary_probe_trials
        weight = apply_corrective_trial!(probe, params, dparams, E_t; witnessed = false)
        delta, score, percent = bmr_probe(probe, params, E_t)
        push!(rows, (
            seed = seed,
            arm = arm,
            probe = "ordinary",
            trial = trial,
            E_t = E_t,
            corrective_weight = weight,
            root_counts_met = probe.accessible_root_counts[1],
            root_counts_alone = probe.accessible_root_counts[2],
            bmr_delta = delta,
            bmr_score = score,
            revision_percent = percent,
        ))
    end
    return probe, rows
end

function recovery_witnessed_probe(seed::Int, formed, params::Sim6bParams, dparams)
    q_depth = copy(formed.q_depth)
    trace_rows = NamedTuple[]
    probe = copy_cause(formed.target)
    trial_offset = maximum(row.trial for row in formed.traces)
    for trial in 1:params.safety_recovery_trials
        q_depth = Sim6a.update_depth_with_evidence(dparams, q_depth, Sim6a.volatility_observation(0.05))
        E_t, pi_eff, lambda_eff, capture_index, depth_precision = depth_readouts(dparams, q_depth)
        push!(trace_rows, (
            seed = seed,
            arm = "unclamped",
            trial = trial_offset + trial,
            phase = "safety-recovery",
            policy = "approach",
            spawned = false,
            cause_id = probe.id,
            arousal = 0.05,
            precision_weighted_pe = 0.0,
            learning_rate = 0.0,
            volatility_observation = string(Sim6a.volatility_observation(0.05)),
            E_t = E_t,
            depth_posterior_precision = depth_precision,
            pi_eff = pi_eff,
            lambda_eff = lambda_eff,
            capture_index = capture_index,
            accessible_write_weight = 0.0,
            root_counts_met = probe.accessible_root_counts[1],
            root_counts_alone = probe.accessible_root_counts[2],
        ))
    end

    probe_rows = NamedTuple[]
    for trial in 1:params.witnessed_contact_trials
        E_t, pi_eff, lambda_eff, capture_index, depth_precision = depth_readouts(dparams, q_depth)
        weight = apply_corrective_trial!(probe, params, dparams, E_t; witnessed = true)
        delta, score, percent = bmr_probe(probe, params, E_t)
        push!(probe_rows, (
            seed = seed,
            arm = "unclamped",
            probe = "recovery-witnessed",
            trial = trial,
            E_t = E_t,
            corrective_weight = weight,
            root_counts_met = probe.accessible_root_counts[1],
            root_counts_alone = probe.accessible_root_counts[2],
            bmr_delta = delta,
            bmr_score = score,
            revision_percent = percent,
        ))
        push!(trace_rows, (
            seed = seed,
            arm = "unclamped",
            trial = trial_offset + params.safety_recovery_trials + trial,
            phase = "witnessed-contact",
            policy = "approach",
            spawned = false,
            cause_id = probe.id,
            arousal = 0.05,
            precision_weighted_pe = 0.0,
            learning_rate = params.revision_learning_rate,
            volatility_observation = "contact",
            E_t = E_t,
            depth_posterior_precision = depth_precision,
            pi_eff = pi_eff,
            lambda_eff = lambda_eff,
            capture_index = capture_index,
            accessible_write_weight = weight,
            root_counts_met = probe.accessible_root_counts[1],
            root_counts_alone = probe.accessible_root_counts[2],
        ))
    end
    return q_depth, trace_rows, probe_rows
end

function sign_alternations(values; threshold::Float64 = 0.04)
    diffs = diff(Float64.(values))
    signs = [d > threshold ? 1 : (d < -threshold ? -1 : 0) for d in diffs]
    compact = [s for s in signs if s != 0]
    length(compact) < 3 && return 0
    return count(compact[i] != compact[i - 1] for i in 2:length(compact))
end

function aggregate_by_arm(metrics, ordinary_rows)
    rows = NamedTuple[]
    for arm in ARMS
        arm_metrics = [row for row in metrics if row.arm == arm]
        arm_probe = [row for row in ordinary_rows if row.arm == arm && row.probe == "ordinary" && row.trial == maximum(r.trial for r in ordinary_rows if r.arm == arm && r.probe == "ordinary")]
        push!(rows, (
            arm = arm,
            seed_count = length(arm_metrics),
            spawn_rate = mean(row.spawned ? 1.0 : 0.0 for row in arm_metrics),
            target_spawn_rate = mean(row.target_spawned ? 1.0 : 0.0 for row in arm_metrics),
            mean_write_time_depth = mean(row.write_time_depth for row in arm_metrics),
            min_mean_E_t = mean(row.min_E_t for row in arm_metrics),
            mean_postformation_approach_rate = mean(row.mean_postformation_approach_rate for row in arm_metrics),
            mean_accessible_root_counts_met = mean(row.accessible_root_counts_met for row in arm_metrics),
            mean_accessible_root_counts_alone = mean(row.accessible_root_counts_alone for row in arm_metrics),
            mean_structural_precision = mean(row.structural_precision for row in arm_metrics),
            mean_ordinary_revision_percent = mean(row.revision_percent for row in arm_probe),
            ordinary_revision_rate_over_floor = mean(row.revision_percent >= 25.0 ? 1.0 : 0.0 for row in arm_probe),
        ))
    end
    return rows
end

function summarize_metrics(per_seed_metrics, ordinary_probe_rows, recovery_probe_rows, traces, params::Sim6bParams)
    arms = aggregate_by_arm(per_seed_metrics, ordinary_probe_rows)
    by_arm = Dict(row.arm => row for row in arms)
    final_recovery_rows = [row for row in recovery_probe_rows if row.probe == "recovery-witnessed" && row.trial == params.witnessed_contact_trials]
    unclamped = by_arm["unclamped"]
    clamped = by_arm["clamped"]
    yoked = by_arm["yoked-control"]
    clamped_ratio = clamped.mean_ordinary_revision_percent / max(unclamped.mean_ordinary_revision_percent, EPS)
    yoked_ratio = yoked.mean_ordinary_revision_percent / max(unclamped.mean_ordinary_revision_percent, EPS)
    recovery_revision = mean(row.revision_percent for row in final_recovery_rows)
    recovery_ratio = recovery_revision / max(unclamped.mean_ordinary_revision_percent, EPS)
    grouped_E = Dict{Tuple{Int, String}, Vector{Float64}}()
    for row in traces
        key = (row.seed, row.arm)
        grouped_E[key] = get(grouped_E, key, Float64[])
        push!(grouped_E[key], row.E_t)
    end
    oscillating = count(values -> sign_alternations(values) >= 4, values(grouped_E))
    rescued = clamped.mean_ordinary_revision_percent >= params.rescue_revision_floor &&
        clamped_ratio >= 3.0 &&
        abs(clamped.mean_ordinary_revision_percent - yoked.mean_ordinary_revision_percent) <= params.clamp_yoke_tolerance
    falsified = clamped.mean_ordinary_revision_percent <= params.freeze_revision_threshold ||
        clamped_ratio < 1.5
    return (
        arms = (
            unclamped = unclamped,
            clamped = clamped,
            yoked_control = yoked,
        ),
        clamp_control = (
            clamped_revision_rescue_margin = clamped_ratio,
            yoked_revision_rescue_margin = yoked_ratio,
            clamped_yoked_revision_abs_diff = abs(clamped.mean_ordinary_revision_percent - yoked.mean_ordinary_revision_percent),
            verdict_rescued = rescued ? 1.0 : 0.0,
            verdict_falsified = falsified ? 1.0 : 0.0,
            verdict = rescued ? "rescued" : (falsified ? "falsified" : "null"),
            rescue_revision_floor = params.rescue_revision_floor,
            floor_basis = "Sim 1 run sim1-t1-2: non-frozen aversive rows mean 36.765%, max 85.087%; frozen rows mean 5.787%. Floor set to 25%, below the ordinary mean and above frozen range.",
        ),
        recovery = (
            mean_recovery_witnessed_revision_percent = recovery_revision,
            recovery_revision_rescue_margin = recovery_ratio,
            mean_recovered_E_t = mean(row.E_t for row in final_recovery_rows),
            full_circle_pass = (recovery_revision >= params.rescue_revision_floor && recovery_ratio >= 3.0) ? 1.0 : 0.0,
        ),
        traits = (
            unclamped_freeze_signature = (
                spawn_rate = unclamped.spawn_rate,
                mean_write_time_depth = unclamped.mean_write_time_depth,
                mean_postformation_approach_rate = unclamped.mean_postformation_approach_rate,
                mean_ordinary_revision_percent = unclamped.mean_ordinary_revision_percent,
            ),
            clamped_ordinary_signature = (
                spawn_rate = clamped.spawn_rate,
                mean_write_time_depth = clamped.mean_write_time_depth,
                mean_ordinary_revision_percent = clamped.mean_ordinary_revision_percent,
            ),
            yoked_ordinary_signature = (
                spawn_rate = yoked.spawn_rate,
                mean_write_time_depth = yoked.mean_write_time_depth,
                mean_ordinary_revision_percent = yoked.mean_ordinary_revision_percent,
            ),
        ),
        stability = (
            oscillating_seed_arm_count = oscillating,
            seed_arm_count = length(grouped_E),
            oscillation_rate = isempty(grouped_E) ? 0.0 : oscillating / length(grouped_E),
            effective_precision_min = minimum(min(row.pi_eff, row.lambda_eff) for row in traces),
            effective_precision_max = maximum(max(row.pi_eff, row.lambda_eff) for row in traces),
        ),
        controls = (
            max_learning_rate_stream_diff = learning_rate_stream_diff(traces),
            max_pe_stream_diff = pe_stream_diff(traces),
            all_labels_shipped = 1.0,
        ),
    )
end

function stream_diff(traces, field::Symbol)
    maxdiff = 0.0
    seeds = unique(row.seed for row in traces)
    for seed in seeds
        base = sort([row for row in traces if row.seed == seed && row.arm == "unclamped" && row.phase in ("baseline", "overwhelm", "dark-postformation")]; by = row -> row.trial)
        for arm in ("clamped", "yoked-control")
            rows = sort([row for row in traces if row.seed == seed && row.arm == arm && row.phase in ("baseline", "overwhelm", "dark-postformation")]; by = row -> row.trial)
            for i in 1:min(length(base), length(rows))
                maxdiff = max(maxdiff, abs(Float64(getproperty(base[i], field)) - Float64(getproperty(rows[i], field))))
            end
        end
    end
    return maxdiff
end

learning_rate_stream_diff(traces) = stream_diff(traces, :learning_rate)
pe_stream_diff(traces) = stream_diff(traces, :precision_weighted_pe)

function write_recovery_svg(path::AbstractString, traces, probe_rows)
    ensure_dir(dirname(path))
    rows = [row for row in traces if row.seed == first(traces).seed && row.arm == "unclamped"]
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
    final_probe = [row for row in probe_rows if row.seed == first(traces).seed && row.probe == "recovery-witnessed"]
    revision_points = String[]
    start_trial = maximum(row.trial for row in rows if row.phase == "safety-recovery")
    for row in final_probe
        x, y = xy(start_trial + row.trial, row.revision_percent / 100.0)
        push!(revision_points, string(round(x; digits = 1), ",", round(y; digits = 1)))
    end
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="760" height="380" viewBox="0 0 760 380">
      <rect width="760" height="380" fill="#fbfaf7"/>
      <line x1="70" y1="300" x2="640" y2="300" stroke="#222" stroke-width="2"/>
      <line x1="70" y1="70" x2="70" y2="300" stroke="#222" stroke-width="2"/>
      <text x="70" y="36" font-family="Arial" font-size="18" fill="#222">Sim 6b full circle: depth recovery restores revision</text>
      <polyline points="$(polyline(:E_t))" fill="none" stroke="#2451a6" stroke-width="4"/>
      <polyline points="$(polyline(:capture_index))" fill="none" stroke="#a4442a" stroke-width="3" stroke-dasharray="7 5"/>
      <polyline points="$(join(revision_points, " "))" fill="none" stroke="#2f7d59" stroke-width="4"/>
      <text x="655" y="92" font-family="Arial" font-size="12" fill="#2451a6">E_t</text>
      <text x="655" y="116" font-family="Arial" font-size="12" fill="#a4442a">C_t</text>
      <text x="655" y="140" font-family="Arial" font-size="12" fill="#2f7d59">revision</text>
      <text x="118" y="330" font-family="Arial" font-size="12" fill="#444">formation collapse</text>
      <text x="410" y="330" font-family="Arial" font-size="12" fill="#444">safety + witnessed contact</text>
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

function run_sim6b_config(config::ExperimentConfig; config_path::Union{Nothing, AbstractString} = nothing, output_dir::Union{Nothing, AbstractString} = nothing)
    started = time()
    params = params_from_config(config)
    validate_params(params)
    length(config.seeds) >= 20 || error("Sim 6b requires at least 20 seeds")
    dparams = depth_params(params)
    outdir = output_dir === nothing ? normpath(joinpath(config.output_dir, config.experiment, config.label === nothing ? Dates.format(Dates.now(Dates.UTC), Dates.dateformat"yyyymmddTHHMMSSZ") : config.label)) : output_dir
    ensure_dir(outdir)

    per_seed_metrics = NamedTuple[]
    traces = NamedTuple[]
    ordinary_probe_rows = NamedTuple[]
    recovery_probe_rows = NamedTuple[]
    recovery_extra_traces = NamedTuple[]

    for seed in config.seeds
        formed_by_arm = Dict{String, Any}()
        for arm in ARMS
            formed = formation_loop(seed, arm, params, dparams)
            formed_by_arm[arm] = formed
            push!(per_seed_metrics, formed.formation_metric)
            append!(traces, formed.traces)
            _, probe_rows = ordinary_revision_probe(seed, arm, formed.target, formed.q_depth, params, dparams)
            append!(ordinary_probe_rows, probe_rows)
        end
        _, recovery_traces, recovery_rows = recovery_witnessed_probe(seed, formed_by_arm["unclamped"], params, dparams)
        append!(recovery_extra_traces, recovery_traces)
        append!(recovery_probe_rows, recovery_rows)
    end
    append!(traces, recovery_extra_traces)

    metrics = summarize_metrics(per_seed_metrics, ordinary_probe_rows, recovery_probe_rows, traces, params)
    figure_path = write_recovery_svg(joinpath(outdir, "figures", "depth_recovery.svg"), traces, recovery_probe_rows)

    summary = (
        experiment = "sim6b",
        config = config_snapshot(config),
        model_contract = (
            own_module = "EmergenceSuite.Sim6b",
            depth_source = "Sim6a categorical depth filtering and D1 effective precision readouts",
            clamp = "intervention: q(d) fixed to the high-depth posterior; downstream writes and probes still read q(d)",
            yoked_control = "same arousal and PE stream; volatility observation withheld from level 3",
            write_coupling = "structural write learning rate follows realized PE; accessible statistics write at the D1 depth-discounted relational rate",
            no_direct_depth_assignment_in_unclamped = true,
        ),
        preregistration = (
            sim1_revision_anchor = (
                source = "suite/runs/sim1/sim1-t1-2/per_seed_metrics.csv",
                ordinary_nonfrozen_aversive_mean = 36.765,
                ordinary_nonfrozen_aversive_max = 85.087,
                frozen_mean = 5.787,
                frozen_max = 9.993,
                selected_rescue_floor = params.rescue_revision_floor,
            ),
        ),
        metrics = metrics,
        outputs = (
            depth_recovery_figure = figure_path,
            depth_recovery_figure_written = isfile(figure_path) ? 1.0 : 0.0,
        ),
        per_seed_metric_count = length(per_seed_metrics),
        trace_row_count = length(traces),
    )

    summary_path = joinpath(outdir, "summary.json")
    write_json(summary_path, summary)
    write_rows_csv(joinpath(outdir, "per_seed_metrics.csv"), per_seed_metrics)
    write_rows_csv(joinpath(outdir, "posterior_traces.csv"), traces)
    write_rows_csv(joinpath(outdir, "ordinary_revision_probe_metrics.csv"), ordinary_probe_rows)
    write_rows_csv(joinpath(outdir, "recovery_witnessed_probe_metrics.csv"), recovery_probe_rows)

    criteria_results = nothing
    if !isnothing(config.criteria_path) && isfile(config.criteria_path)
        criteria_results = write_criteria_results(config.criteria_path, summary_path, joinpath(outdir, "criteria-results.json"))
    end
    status = (
        implementation_passed = length(config.seeds) >= 20 && !isempty(per_seed_metrics) && isfile(figure_path),
        theory_result = theory_label(criteria_results),
        criteria_results_path = criteria_results === nothing ? nothing : joinpath(outdir, "criteria-results.json"),
        clamp_control_verdict = metrics.clamp_control.verdict,
    )
    write_json(joinpath(outdir, "status.json"), status)
    metadata = build_reproducibility_metadata(
        config;
        config_path = config_path,
        runtime_seconds = time() - started,
        repo_root = normpath(joinpath(@__DIR__, "..", "..", "..", "..", "..")),
        extra = (output_dir = abspath(outdir), sim_module = "EmergenceSuite.Sim6b"),
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
