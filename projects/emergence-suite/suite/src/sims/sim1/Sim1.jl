module Sim1

using Random
using Statistics
using LinearAlgebra: dot

using ..Config: ExperimentConfig, config_snapshot
using ..Criteria: write_criteria_results
using ..DiscreteCore: DirichletBanks
using ..EFE: Policy, PolicyScore
using ..IO: ensure_dir, write_json, write_rows_csv
using ..Reproducibility: build_reproducibility_metadata

export run_sim1

const EPS = 1e-12
const SAFE = 1
const AVERSIVE = 2
const POLICY_NAMES = ["approach", "flee", "appease", "attenuate"]
const APPROACH = 1
const FLEE = 2
const APPEASE = 3
const ATTENUATE = 4

Base.@kwdef struct Sim1Params
    crp_concentration::Float64 = 0.34
    crp_threshold_base::Float64 = 0.085
    crp_threshold_control_relief::Float64 = 0.0
    formation_trials::Int = 72
    disconfirming_trials::Int = 24
    post_formation_trials::Int = 18
    slow_path_trials::Int = 600
    slow_path_omega::Float64 = 1.00
    slow_path_kappa::Float64 = 0.0
    bundle_seed_count::Int = 8
    spawn_pressure_threshold::Float64 = 2.45
    spawn_pressure_decay::Float64 = 0.72
    learning_rate_base::Float64 = 0.16
    learning_rate_arousal_gain::Float64 = 60.0
    cue_learning_weight::Float64 = 0.55
    revision_learning_rate::Float64 = 2.0
    behavior_frozen_max_change::Float64 = 0.15
    behavior_revisable_min_change::Float64 = 0.25
    threat_prediction_threshold::Float64 = 0.40
    cell_classification_rate::Float64 = 0.50
    connected_region_min_cells::Int = 2
    policy_softmax_temperature::Float64 = 1.0
    arousal_pe_scale::Float64 = 5.2
    reflexivity_arousal_slope::Float64 = 0.88
    evidence_precision::Float64 = 1.0
    attenuation_precision_scale::Float64 = 0.34
    safe_preference::Float64 = 1.35
    aversive_preference::Float64 = -2.35
    ambiguity_weight::Float64 = 0.10
    epistemic_weight::Float64 = 0.28
    attenuation_info_scale::Float64 = 0.18
    attenuation_cost::Float64 = 0.80
    overt_action_cost::Float64 = 0.03
    attenuation_extreme_omega::Float64 = 2.65
    attenuation_flat_kappa::Float64 = 0.16
    acute_region_omega_min::Float64 = 1.18
end

mutable struct Cause
    id::Int
    cue_counts::Vector{Float64}
    affect_counts::Vector{Float64}
    outcome_counts::Matrix{Float64}
    policy_counts::Vector{Float64}
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
    evidence_outcome::Int
    action_outcome::Int
    evidence_aversive_probability::Float64
    action_aversive_probability::Float64
    evidence_severity::Float64
    precision::Float64
end

function sim1_params(raw::Dict{String, Any})
    return Sim1Params(
        crp_concentration = Float64(get(raw, "crp_concentration", 0.34)),
        crp_threshold_base = Float64(get(raw, "crp_threshold_base", 0.085)),
        crp_threshold_control_relief = Float64(get(raw, "crp_threshold_control_relief", 0.0)),
        formation_trials = Int(get(raw, "formation_trials", get(raw, "post_formation_trials", 72) * 4)),
        disconfirming_trials = Int(get(raw, "disconfirming_trials", 24)),
        post_formation_trials = Int(get(raw, "post_formation_trials", 18)),
        slow_path_trials = Int(get(raw, "slow_path_trials", 600)),
        slow_path_omega = Float64(get(raw, "slow_path_omega", 1.00)),
        slow_path_kappa = Float64(get(raw, "slow_path_kappa", 0.0)),
        bundle_seed_count = Int(get(raw, "bundle_seed_count", 8)),
        spawn_pressure_threshold = Float64(get(raw, "spawn_pressure_threshold", 2.45)),
        spawn_pressure_decay = Float64(get(raw, "spawn_pressure_decay", 0.72)),
        learning_rate_base = Float64(get(raw, "learning_rate_base", 0.16)),
        learning_rate_arousal_gain = Float64(get(raw, "learning_rate_arousal_gain", 60.0)),
        cue_learning_weight = Float64(get(raw, "cue_learning_weight", 0.55)),
        revision_learning_rate = Float64(get(raw, "revision_learning_rate", 2.0)),
        behavior_frozen_max_change = Float64(get(raw, "behavior_frozen_max_change", 0.15)),
        behavior_revisable_min_change = Float64(get(raw, "behavior_revisable_min_change", 0.25)),
        threat_prediction_threshold = Float64(get(raw, "threat_prediction_threshold", 0.40)),
        cell_classification_rate = Float64(get(raw, "cell_classification_rate", 0.50)),
        connected_region_min_cells = Int(get(raw, "connected_region_min_cells", 2)),
        policy_softmax_temperature = Float64(get(raw, "policy_softmax_temperature", 1.0)),
        arousal_pe_scale = Float64(get(raw, "arousal_pe_scale", 5.2)),
        reflexivity_arousal_slope = Float64(get(raw, "reflexivity_arousal_slope", 0.88)),
        evidence_precision = Float64(get(raw, "evidence_precision", 1.0)),
        attenuation_precision_scale = Float64(get(raw, "attenuation_precision_scale", 0.34)),
        safe_preference = Float64(get(raw, "safe_preference", 1.35)),
        aversive_preference = Float64(get(raw, "aversive_preference", -2.35)),
        ambiguity_weight = Float64(get(raw, "ambiguity_weight", 0.10)),
        epistemic_weight = Float64(get(raw, "epistemic_weight", 0.28)),
        attenuation_info_scale = Float64(get(raw, "attenuation_info_scale", 0.18)),
        attenuation_cost = Float64(get(raw, "attenuation_cost", 0.80)),
        overt_action_cost = Float64(get(raw, "overt_action_cost", 0.03)),
        attenuation_extreme_omega = Float64(get(raw, "attenuation_extreme_omega", 2.65)),
        attenuation_flat_kappa = Float64(get(raw, "attenuation_flat_kappa", 0.16)),
        acute_region_omega_min = Float64(get(raw, "acute_region_omega_min", 1.18))
    )
end

function linspace_from_grid(grid::Dict{String, Any}, key::String)
    raw = Dict{String, Any}(string(k) => v for (k, v) in grid[key])
    lo = Float64(raw["min"])
    hi = Float64(raw["max"])
    count = Int(raw["count"])
    count >= 2 || error("$key grid count must be >= 2")
    return collect(range(lo, hi; length = count))
end

sample_categorical(rng::AbstractRNG, p::Vector{Float64}) = begin
    u = rand(rng)
    c = 0.0
    for i in eachindex(p)
        c += p[i]
        u <= c && return i
    end
    length(p)
end

normalize(v::AbstractVector{Float64}) = v ./ max(sum(v), EPS)
entropy(p::AbstractVector{Float64}) = -sum(x -> x * log(x + EPS), p)
control_value(kappa::Float64) = kappa / (kappa + 0.45 + EPS)

function init_agent()
    outcome = hcat(
        [8.0, 4.0],
        [10.0, 3.0],
        [9.0, 4.0],
        [6.0, 6.0]
    )
    base = Cause(
        1,
        [14.0, 10.0],
        [15.0, 7.0],
        Matrix{Float64}(outcome),
        [3.0, 5.0, 4.0, 1.0],
        Dict{String, Any}("route" => "initial_cause", "spawned" => false)
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
        copy(cause.formation)
    )
end

function cause_banks(cause::Cause)
    A_cue = reshape(copy(cause.cue_counts), 2, 1)
    A_affect = reshape(copy(cause.affect_counts), 2, 1)
    B_policy = reshape(copy(cause.outcome_counts), 2, 1, length(POLICY_NAMES))
    return DirichletBanks(Array{Float64}[A_cue, A_affect], Array{Float64, 3}[B_policy])
end

function posterior_mean(counts::AbstractVector{Float64}, idx::Int)
    return counts[idx] / max(sum(counts), EPS)
end

function outcome_distribution(cause::Cause, policy_idx::Int)
    return normalize(vec(cause.outcome_counts[:, policy_idx]))
end

function cue_predictive(cause::Cause, cue::Int)
    return posterior_mean(cause.cue_counts, cue)
end

function affect_aversive_mean(cause::Cause)
    return posterior_mean(cause.affect_counts, AVERSIVE)
end

function structural_precision(cause::Cause)
    return sum(cause.affect_counts) + 0.35 * sum(cause.cue_counts)
end

function base_aversive_probability(omega::Float64)
    return clamp(0.08 + 0.31 * omega, 0.06, 0.97)
end

function action_aversive_probabilities(evidence_outcome::Int, kappa::Float64)
    base = evidence_outcome == AVERSIVE ? 0.90 : 0.08
    control = control_value(kappa)
    return [
        clamp(base - 0.10 * control, 0.03, 0.98),
        clamp(base - 1.40 * control, 0.02, 0.98),
        clamp(base - 0.90 * control, 0.03, 0.98),
        base
    ]
end

function sample_evidence(rng::AbstractRNG, omega::Float64, params::Sim1Params)
    p_av = base_aversive_probability(omega)
    return (
        outcome = rand(rng) < p_av ? AVERSIVE : SAFE,
        aversive_probability = p_av,
        severity = 1.0,
        precision = params.evidence_precision
    )
end

function evidence_stream(seed::Int, omega::Float64, trials::Int, params::Sim1Params)
    rng = MersenneTwister(seed)
    return [sample_evidence(rng, omega, params) for _ in 1:trials]
end

function observe_environment(rng::AbstractRNG, evidence, kappa::Float64, policy_idx::Int)
    probs = action_aversive_probabilities(evidence.outcome, kappa)
    action_p_av = probs[policy_idx]
    action_outcome = rand(rng) < action_p_av ? AVERSIVE : SAFE
    return TrialObservation(
        AVERSIVE,
        evidence.outcome,
        action_outcome,
        evidence.aversive_probability,
        action_p_av,
        evidence.severity,
        evidence.precision
    )
end

function score_policies(cause::Cause, params::Sim1Params; preference_scale::Float64 = 1.0)
    scores = PolicyScore{Float64}[]
    prefs = [params.safe_preference, params.aversive_preference .* preference_scale]
    for policy_idx in eachindex(POLICY_NAMES)
        qo = outcome_distribution(cause, policy_idx)
        is_attenuate = policy_idx == ATTENUATE
        precision_scale = is_attenuate ? params.attenuation_precision_scale : 1.0
        utility = precision_scale * dot(qo, prefs)
        amb = entropy(qo)
        information_gain = params.epistemic_weight * amb / sqrt(sum(cause.outcome_counts[:, policy_idx]))
        is_attenuate && (information_gain *= params.attenuation_info_scale)
        cost = is_attenuate ? params.attenuation_cost : params.overt_action_cost
        total = utility - params.ambiguity_weight * amb + information_gain - cost
        push!(scores, PolicyScore(Policy([policy_idx]), utility, amb, information_gain, total))
    end
    return scores
end

function select_policy(cause::Cause, params::Sim1Params; preference_scale::Float64 = 1.0)
    scores = score_policies(cause, params; preference_scale)
    totals = [score.total for score in scores]
    idx = argmax(totals)
    return idx, scores
end

function policy_probabilities(cause::Cause, params::Sim1Params; preference_scale::Float64 = 1.0)
    totals = [score.total for score in score_policies(cause, params; preference_scale)]
    scaled = totals ./ max(params.policy_softmax_temperature, EPS)
    weights = exp.(scaled .- maximum(scaled))
    return normalize(weights)
end

function best_predictive(agent::AgentState, obs::TrialObservation)
    best_idx = 1
    best_raw = -Inf
    best_weighted = -Inf
    for (idx, cause) in enumerate(agent.causes)
        affect_probability = posterior_mean(cause.affect_counts, obs.evidence_outcome)
        raw = cue_predictive(cause, obs.cue) * affect_probability
        weighted = raw ^ max(obs.precision, EPS)
        if weighted > best_weighted
            best_idx = idx
            best_raw = raw
            best_weighted = weighted
        end
    end
    return best_idx, best_raw, best_weighted
end

function arousal_from_prediction(raw_predictive::Float64, effective_precision::Float64, params::Sim1Params)
    surprise = -log(max(raw_predictive, EPS))
    pe = effective_precision * surprise
    return clamp(pe / params.arousal_pe_scale, 0.0, 1.0), pe
end

function write_reflexivity(arousal::Float64, params::Sim1Params)
    return clamp(1.0 - params.reflexivity_arousal_slope * arousal, 0.0, 1.0)
end

function crp_threshold(agent::AgentState, params::Sim1Params; concentration_factor::Float64 = 1.0)
    alpha = params.crp_concentration * concentration_factor
    complexity = alpha / (alpha + length(agent.causes))
    return params.crp_threshold_base * (0.65 + complexity)
end

function spawn_cause!(agent::AgentState, arousal::Float64, reflexivity::Float64, trial::Int, seed::Int)
    cause = Cause(
        agent.next_cause_id,
        [1.0, 2.0],
        [1.0, 1.0],
        fill(1.0, 2, length(POLICY_NAMES)),
        ones(Float64, length(POLICY_NAMES)),
        Dict{String, Any}(
            "route" => "acute_spawn",
            "spawned" => true,
            "spawn_trial" => trial,
            "seed" => seed,
            "arousal_at_write" => arousal,
            "reflexivity_at_write" => reflexivity
        )
    )
    push!(agent.causes, cause)
    agent.next_cause_id += 1
    agent.spawn_count += 1
    agent.spawn_pressure = 0.0
    return cause
end

function update_spawn_pressure!(agent::AgentState, posterior_predictive::Float64, threshold::Float64, arousal::Float64, params::Sim1Params)
    if posterior_predictive < threshold
        agent.spawn_pressure = params.spawn_pressure_decay * agent.spawn_pressure + arousal
    else
        agent.spawn_pressure *= params.spawn_pressure_decay
    end
    return agent.spawn_pressure
end

function update_cause!(cause::Cause, obs::TrialObservation, policy_idx::Int, arousal::Float64, params::Sim1Params)
    lr = params.learning_rate_base + params.learning_rate_arousal_gain * arousal
    cause.cue_counts[obs.cue] += params.cue_learning_weight * lr
    cause.affect_counts[obs.evidence_outcome] += lr
    cause.outcome_counts[obs.action_outcome, policy_idx] += lr
    cause.policy_counts[policy_idx] += 1.0
    return lr
end

function dominant_aversive_cause(agent::AgentState)
    scores = [
        cue_predictive(cause, AVERSIVE) * affect_aversive_mean(cause) * (1.0 + 0.05 * log1p(structural_precision(cause)))
        for cause in agent.causes
    ]
    return agent.causes[argmax(scores)]
end

function measure_revision(cause::Cause, params::Sim1Params)
    probe = copy_cause(cause)
    pre_safe = probe.affect_counts[SAFE]
    pre_aversive = probe.affect_counts[AVERSIVE]
    pre_affect_aversive = affect_aversive_mean(probe)
    pre_predicted_aversive = outcome_distribution(probe, APPROACH)[AVERSIVE]
    pre_approach_probability = policy_probabilities(probe, params)[APPROACH]
    pre_precision = structural_precision(probe)
    for _ in 1:params.disconfirming_trials
        probe.cue_counts[AVERSIVE] += params.cue_learning_weight * params.revision_learning_rate
        probe.affect_counts[SAFE] += params.revision_learning_rate
        probe.outcome_counts[SAFE, APPROACH] += params.revision_learning_rate
        probe.policy_counts[APPROACH] += 1.0
    end
    post_affect_aversive = affect_aversive_mean(probe)
    post_predicted_aversive = outcome_distribution(probe, APPROACH)[AVERSIVE]
    post_approach_probability = policy_probabilities(probe, params)[APPROACH]
    predicted_aversive_reduction = max(pre_predicted_aversive - post_predicted_aversive, 0.0)
    approach_probability_increase = max(post_approach_probability - pre_approach_probability, 0.0)
    behavior_change = max(predicted_aversive_reduction, approach_probability_increase)
    return (
        behavior_change = behavior_change,
        predicted_aversive_reduction = predicted_aversive_reduction,
        approach_probability_increase = approach_probability_increase,
        pre_predicted_aversive = pre_predicted_aversive,
        post_predicted_aversive = post_predicted_aversive,
        pre_approach_probability = pre_approach_probability,
        post_approach_probability = post_approach_probability,
        pre_affect_aversive = pre_affect_aversive,
        post_affect_aversive = post_affect_aversive,
        pre_safe_count = pre_safe,
        pre_aversive_count = pre_aversive,
        pre_structural_precision = pre_precision,
        post_structural_precision = structural_precision(probe)
    )
end

function run_trial!(rng::AbstractRNG, agent::AgentState, evidence, kappa::Float64, params::Sim1Params, trial::Int, seed::Int;
                    concentration_factor::Float64 = 1.0, allow_spawn::Bool = true, preference_scale::Float64 = 1.0)
    current = dominant_aversive_cause(agent)
    policy_idx, scores = select_policy(current, params; preference_scale)
    obs = observe_environment(rng, evidence, kappa, policy_idx)
    best_idx, raw_pp, weighted_pp = best_predictive(agent, obs)
    arousal, pe = arousal_from_prediction(raw_pp, obs.precision, params)
    reflexivity = write_reflexivity(arousal, params)
    threshold = crp_threshold(agent, params; concentration_factor)
    pressure = update_spawn_pressure!(agent, weighted_pp, threshold, arousal, params)
    spawned = false
    cause = agent.causes[best_idx]
    if allow_spawn && weighted_pp < threshold && pressure >= params.spawn_pressure_threshold
        cause = spawn_cause!(agent, arousal, reflexivity, trial, seed)
        spawned = true
    end
    lr = update_cause!(cause, obs, policy_idx, arousal, params)
    return (
        trial = trial,
        policy_idx = policy_idx,
        policy = POLICY_NAMES[policy_idx],
        evidence_outcome = obs.evidence_outcome == AVERSIVE ? "aversive" : "safe",
        action_outcome = obs.action_outcome == AVERSIVE ? "aversive" : "safe",
        evidence_aversive_probability = obs.evidence_aversive_probability,
        action_aversive_probability = obs.action_aversive_probability,
        evidence_severity = obs.evidence_severity,
        evidence_precision = obs.precision,
        posterior_predictive = weighted_pp,
        raw_predictive = raw_pp,
        crp_threshold = threshold,
        spawn_pressure = agent.spawn_pressure,
        spawned = spawned,
        cause_id = cause.id,
        arousal = arousal,
        reflexivity = reflexivity,
        precision_weighted_pe = pe,
        learning_rate = lr,
        policy_totals = [score.total for score in scores]
    )
end

function postformation_sampling_rate(trial_logs, target_id::Int, params::Sim1Params)
    target_logs = [row for row in trial_logs if row.cause_id == target_id]
    isempty(target_logs) && return 0.0
    window = last(target_logs, min(params.post_formation_trials, length(target_logs)))
    return mean(row.policy_idx == APPROACH ? 1.0 : 0.0 for row in window)
end

function run_seed_cell(seed::Int, omega::Float64, kappa::Float64, params::Sim1Params; concentration_factor::Float64 = 1.0,
                       preference_scale::Float64 = 1.0)
    action_rng = MersenneTwister(seed + 1_000_003)
    evidence = evidence_stream(seed, omega, params.formation_trials, params)
    agent = init_agent()
    trial_logs = NamedTuple[]
    for trial in 1:params.formation_trials
        push!(trial_logs, run_trial!(action_rng, agent, evidence[trial], kappa, params, trial, seed; concentration_factor, preference_scale))
    end
    target = dominant_aversive_cause(agent)
    revision = measure_revision(target, params)
    sampling = postformation_sampling_rate(trial_logs, target.id, params)
    spawned_logs = [row for row in trial_logs if row.spawned]
    write_log = isempty(spawned_logs) ? trial_logs[argmax([row.arousal for row in trial_logs])] : first(spawned_logs)
    target_is_aversive = revision.pre_predicted_aversive >= params.threat_prediction_threshold
    is_frozen = target_is_aversive && revision.behavior_change <= params.behavior_frozen_max_change
    is_revisable = target_is_aversive && revision.behavior_change >= params.behavior_revisable_min_change
    target_spawned = get(target.formation, "spawned", false) == true
    return (
        seed = seed,
        omega = omega,
        kappa = kappa,
        target_cause_id = target.id,
        target_route = String(get(target.formation, "route", target_spawned ? "acute_spawn" : "initial_cause")),
        spawn_count = agent.spawn_count,
        spawned = agent.spawn_count > 0,
        target_spawned = target_spawned,
        dominant_policy = POLICY_NAMES[argmax(target.policy_counts)],
        attenuation_rate = mean(row.policy_idx == ATTENUATE ? 1.0 : 0.0 for row in trial_logs),
        approach_sampling_rate = sampling,
        reflexivity_at_write = write_log.reflexivity,
        arousal_at_write = write_log.arousal,
        max_precision_weighted_pe = maximum(row.precision_weighted_pe for row in trial_logs),
        mean_precision_weighted_pe = mean(row.precision_weighted_pe for row in trial_logs),
        revision_behavior_change = revision.behavior_change,
        predicted_aversive_reduction = revision.predicted_aversive_reduction,
        approach_probability_increase = revision.approach_probability_increase,
        pre_probe_predicted_aversive = revision.pre_predicted_aversive,
        post_probe_predicted_aversive = revision.post_predicted_aversive,
        pre_probe_approach_probability = revision.pre_approach_probability,
        post_probe_approach_probability = revision.post_approach_probability,
        pre_probe_affect_aversive = revision.pre_affect_aversive,
        post_probe_affect_aversive = revision.post_affect_aversive,
        structural_precision = revision.pre_structural_precision,
        target_aversive = target_is_aversive,
        frozen = is_frozen,
        revisable = is_revisable,
        aversive_evidence_count = count(row.evidence_outcome == "aversive" for row in trial_logs),
        aversive_evidence_severity_sum = sum(row.evidence_outcome == "aversive" ? row.evidence_severity : 0.0 for row in trial_logs),
        mean_evidence_precision = mean(row.evidence_precision for row in trial_logs),
        aversive_action_outcome_count = count(row.action_outcome == "aversive" for row in trial_logs),
        posterior_predictive_min = minimum(row.posterior_predictive for row in trial_logs),
        crp_threshold_last = last(trial_logs).crp_threshold,
        cause_bank_cue_safe = target.cue_counts[SAFE],
        cause_bank_cue_threat = target.cue_counts[AVERSIVE],
        cause_bank_affect_safe = target.affect_counts[SAFE],
        cause_bank_affect_threat = target.affect_counts[AVERSIVE],
        cause_bank_policy_approach = target.policy_counts[APPROACH],
        cause_bank_policy_flee = target.policy_counts[FLEE],
        cause_bank_policy_appease = target.policy_counts[APPEASE],
        cause_bank_policy_attenuate = target.policy_counts[ATTENUATE],
        outcome_approach_safe = target.outcome_counts[SAFE, APPROACH],
        outcome_approach_threat = target.outcome_counts[AVERSIVE, APPROACH],
        outcome_flee_safe = target.outcome_counts[SAFE, FLEE],
        outcome_flee_threat = target.outcome_counts[AVERSIVE, FLEE],
        outcome_appease_safe = target.outcome_counts[SAFE, APPEASE],
        outcome_appease_threat = target.outcome_counts[AVERSIVE, APPEASE],
        outcome_attenuate_safe = target.outcome_counts[SAFE, ATTENUATE],
        outcome_attenuate_threat = target.outcome_counts[AVERSIVE, ATTENUATE]
    )
end

function mean_bool(rows, field::Symbol)
    isempty(rows) && return 0.0
    return mean(getproperty(row, field) ? 1.0 : 0.0 for row in rows)
end

function mean_field(rows, field::Symbol; default::Float64 = 0.0)
    isempty(rows) && return default
    return mean(Float64(getproperty(row, field)) for row in rows)
end

function summarize_cell(rows)
    return (
        omega = first(rows).omega,
        kappa = first(rows).kappa,
        n_seeds = length(rows),
        spawn_rate = mean_bool(rows, :spawned),
        target_spawn_rate = mean_bool(rows, :target_spawned),
        frozen_rate = mean_bool(rows, :frozen),
        revisable_rate = mean_bool(rows, :revisable),
        attenuation_rate = mean_field(rows, :attenuation_rate),
        mean_reflexivity_at_write = mean_field(rows, :reflexivity_at_write),
        mean_arousal_at_write = mean_field(rows, :arousal_at_write),
        mean_postformation_sampling_rate = mean_field(rows, :approach_sampling_rate),
        mean_revision_behavior_change = mean_field(rows, :revision_behavior_change),
        mean_predicted_aversive_reduction = mean_field(rows, :predicted_aversive_reduction),
        mean_approach_probability_increase = mean_field(rows, :approach_probability_increase),
        mean_pre_probe_predicted_aversive = mean_field(rows, :pre_probe_predicted_aversive),
        mean_post_probe_predicted_aversive = mean_field(rows, :post_probe_predicted_aversive),
        mean_pre_probe_approach_probability = mean_field(rows, :pre_probe_approach_probability),
        mean_post_probe_approach_probability = mean_field(rows, :post_probe_approach_probability),
        mean_aversive_evidence_count = mean_field(rows, :aversive_evidence_count),
        mean_aversive_action_outcome_count = mean_field(rows, :aversive_action_outcome_count),
        mean_structural_precision = mean_field(rows, :structural_precision),
        max_precision_weighted_pe = maximum(row.max_precision_weighted_pe for row in rows)
    )
end

function component_sizes(mask::AbstractMatrix{Bool})
    seen = falses(size(mask))
    sizes = Int[]
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for start in CartesianIndices(mask)
        (!mask[start] || seen[start]) && continue
        queue = [start]
        seen[start] = true
        count = 0
        while !isempty(queue)
            idx = popfirst!(queue)
            count += 1
            for (di, dj) in dirs
                ni, nj = idx[1] + di, idx[2] + dj
                if 1 <= ni <= size(mask, 1) && 1 <= nj <= size(mask, 2) && mask[ni, nj] && !seen[ni, nj]
                    seen[ni, nj] = true
                    push!(queue, CartesianIndex(ni, nj))
                end
            end
        end
        push!(sizes, count)
    end
    return sizes
end

function boundary_by_kappa(cell_rows, omegas, kappas; field::Symbol = :frozen_rate, threshold::Float64 = 0.5)
    boundary = Float64[]
    for kappa in kappas
        rows = sort([row for row in cell_rows if row.kappa == kappa]; by = row -> row.omega)
        hits = [row.omega for row in rows if getproperty(row, field) >= threshold]
        push!(boundary, isempty(hits) ? NaN : minimum(hits))
    end
    return boundary
end

function boundary_smoothness(cell_rows, omegas, kappas; threshold::Float64 = 0.5)
    boundary = boundary_by_kappa(cell_rows, omegas, kappas; threshold)
    finite = [x for x in boundary if isfinite(x)]
    length(finite) <= 1 && return 0.0
    jumps = abs.(diff(finite)) ./ max(maximum(omegas) - minimum(omegas), EPS)
    return isempty(jumps) ? 0.0 : maximum(jumps)
end

function classify_grid(cell_rows, omegas, kappas, params::Sim1Params)
    frozen = falses(length(omegas), length(kappas))
    revisable = falses(length(omegas), length(kappas))
    for row in cell_rows
        i = findfirst(==(row.omega), omegas)
        j = findfirst(==(row.kappa), kappas)
        frozen[i, j] = row.frozen_rate >= params.cell_classification_rate
        revisable[i, j] = row.revisable_rate >= params.cell_classification_rate
    end
    frozen_components = component_sizes(frozen)
    revisable_components = component_sizes(revisable)
    return (
        frozen = frozen,
        revisable = revisable,
        frozen_largest_component = isempty(frozen_components) ? 0 : maximum(frozen_components),
        revisable_largest_component = isempty(revisable_components) ? 0 : maximum(revisable_components),
        frozen_cell_count = count(frozen),
        revisable_cell_count = count(revisable)
    )
end

function run_sweep(seeds, omegas, kappas, params::Sim1Params; concentration_factor::Float64 = 1.0,
                   preference_scale::Float64 = 1.0)
    seed_rows = NamedTuple[]
    cell_rows = NamedTuple[]
    for omega in omegas, kappa in kappas
        rows = [run_seed_cell(seed, omega, kappa, params; concentration_factor, preference_scale) for seed in seeds]
        append!(seed_rows, rows)
        push!(cell_rows, summarize_cell(rows))
    end
    return seed_rows, cell_rows
end

function slow_condition_sequence(params::Sim1Params)
    return [
        params.slow_path_omega * (0.94 + 0.12 * ((i - 1) % 11) / 10)
        for i in 1:params.slow_path_trials
    ]
end

function run_slow_path(seed::Int, params::Sim1Params; shuffle::Bool = false)
    evidence_rng = MersenneTwister(seed)
    action_rng = MersenneTwister(seed + 1_000_003)
    shuffle_rng = MersenneTwister(seed + 2_000_003)
    omegas = slow_condition_sequence(params)
    shuffle && Random.shuffle!(shuffle_rng, omegas)
    agent = init_agent()
    rows = NamedTuple[]
    crossed = false
    cross_trial = 0
    cross_precision = NaN
    max_pe = 0.0
    spawn_seen = false
    for (trial, omega_t) in enumerate(omegas)
        evidence = sample_evidence(evidence_rng, omega_t, params)
        log = run_trial!(action_rng, agent, evidence, params.slow_path_kappa, params, trial, seed; allow_spawn = true)
        spawn_seen |= log.spawned
        target = dominant_aversive_cause(agent)
        revision = measure_revision(target, params)
        is_frozen = revision.pre_predicted_aversive >= params.threat_prediction_threshold &&
            revision.behavior_change <= params.behavior_frozen_max_change
        if !crossed && is_frozen
            crossed = true
            cross_trial = trial
            cross_precision = revision.pre_structural_precision
        end
        max_pe = max(max_pe, log.precision_weighted_pe)
        push!(rows, (
            seed = seed,
            trial = trial,
            per_trial_omega = omega_t,
            kappa = params.slow_path_kappa,
            target_cause_id = target.id,
            structural_precision = revision.pre_structural_precision,
            revision_behavior_change = revision.behavior_change,
            predicted_aversive_reduction = revision.predicted_aversive_reduction,
            approach_probability_increase = revision.approach_probability_increase,
            pre_probe_predicted_aversive = revision.pre_predicted_aversive,
            pre_probe_approach_probability = revision.pre_approach_probability,
            precision_weighted_pe = log.precision_weighted_pe,
            evidence_outcome = log.evidence_outcome,
            spawned = spawn_seen,
            crossed = crossed
        ))
    end
    target = dominant_aversive_cause(agent)
    revision = measure_revision(target, params)
    return (
        seed = seed,
        omega_center = params.slow_path_omega,
        kappa = params.slow_path_kappa,
        trials = params.slow_path_trials,
        crossed = crossed,
        cross_trial = crossed ? cross_trial : nothing,
        cross_structural_precision = crossed ? cross_precision : nothing,
        max_per_trial_pe = max_pe,
        spawned = spawn_seen,
        final_revision_behavior_change = revision.behavior_change,
        final_predicted_aversive_reduction = revision.predicted_aversive_reduction,
        final_approach_probability_increase = revision.approach_probability_increase,
        final_pre_probe_predicted_aversive = revision.pre_predicted_aversive,
        final_post_probe_predicted_aversive = revision.post_predicted_aversive,
        final_pre_probe_approach_probability = revision.pre_approach_probability,
        final_post_probe_approach_probability = revision.post_approach_probability,
        final_structural_precision = revision.pre_structural_precision,
        target_cause = copy_cause(target),
        path = rows
    )
end

function high_high_frozen_rate(cell_rows, omegas, kappas)
    omega_cut = quantile(omegas, 0.80)
    kappa_cut = quantile(kappas, 0.80)
    rows = [row for row in cell_rows if row.omega >= omega_cut && row.kappa >= kappa_cut]
    return isempty(rows) ? 0.0 : mean(row.frozen_rate for row in rows)
end

function kappa_yoking_metrics(seed_rows, omegas, kappas)
    count_ranges = Float64[]
    severity_ranges = Float64[]
    precision_ranges = Float64[]
    complete_groups = true
    for omega in omegas, seed in unique(row.seed for row in seed_rows)
        rows = [row for row in seed_rows if row.omega == omega && row.seed == seed]
        complete_groups &= length(rows) == length(kappas)
        isempty(rows) && continue
        push!(count_ranges, maximum(row.aversive_evidence_count for row in rows) - minimum(row.aversive_evidence_count for row in rows))
        push!(severity_ranges, maximum(row.aversive_evidence_severity_sum for row in rows) - minimum(row.aversive_evidence_severity_sum for row in rows))
        push!(precision_ranges, maximum(row.mean_evidence_precision for row in rows) - minimum(row.mean_evidence_precision for row in rows))
    end
    max_count_range = isempty(count_ranges) ? Inf : maximum(count_ranges)
    max_severity_range = isempty(severity_ranges) ? Inf : maximum(severity_ranges)
    max_precision_range = isempty(precision_ranges) ? Inf : maximum(precision_ranges)
    return (
        exact_yoking = complete_groups && max_count_range == 0.0 && max_severity_range <= EPS && max_precision_range <= EPS ? 1.0 : 0.0,
        complete_groups = complete_groups,
        max_aversive_count_range = max_count_range,
        max_aversive_severity_range = max_severity_range,
        max_observation_precision_range = max_precision_range
    )
end

function attenuation_corner_metric(cell_rows, params::Sim1Params)
    corner = [row for row in cell_rows if row.omega >= params.attenuation_extreme_omega && row.kappa <= params.attenuation_flat_kappa]
    outside = [row for row in cell_rows if !(row.omega >= params.attenuation_extreme_omega && row.kappa <= params.attenuation_flat_kappa)]
    corner_rate = isempty(corner) ? 0.0 : mean(row.attenuation_rate for row in corner)
    outside_rate = isempty(outside) ? 0.0 : maximum(row.attenuation_rate for row in outside)
    return (
        pass = (corner_rate >= 0.80 && outside_rate <= 0.05) ? 1.0 : 0.0,
        corner_rate = corner_rate,
        max_outside_rate = outside_rate
    )
end

function omega_only_frozen_metric(seeds, omegas, params::Sim1Params)
    moderate_kappa = 0.70
    rows = NamedTuple[]
    for omega in omegas
        seed_rows = [run_seed_cell(seed, omega, moderate_kappa, params) for seed in seeds]
        push!(rows, summarize_cell(seed_rows))
    end
    frozen_cells = count(row.frozen_rate >= params.cell_classification_rate for row in rows)
    return frozen_cells > 0 ? 1.0 : 0.0
end

function concentration_boundary_smoothness(seeds, omegas, kappas, params::Sim1Params)
    traces = NamedTuple[]
    for factor in (0.5, 1.0, 1.5)
        _, cells = run_sweep(seeds, omegas, kappas, params; concentration_factor = factor)
        push!(traces, (
            concentration_factor = factor,
            smoothness = boundary_smoothness(cells, omegas, kappas; threshold = params.cell_classification_rate),
            frozen_boundary_min_omega_by_kappa = boundary_by_kappa(cells, omegas, kappas; threshold = params.cell_classification_rate)
        ))
    end
    return maximum(row.smoothness for row in traces), traces
end

function attenuation_preference_sensitivity(seeds, omegas, kappas, params::Sim1Params)
    traces = NamedTuple[]
    for scale in (0.85, 1.0, 1.15)
        _, cells = run_sweep(seeds, omegas, kappas, params; preference_scale = scale)
        metric = attenuation_corner_metric(cells, params)
        push!(traces, (
            aversive_preference_scale = scale,
            attenuate_corner_only = metric.pass,
            corner_rate = metric.corner_rate,
            max_outside_rate = metric.max_outside_rate
        ))
    end
    return traces
end

function write_phase_svg(path::AbstractString, cell_rows, slow_path_rows, omegas, kappas)
    width, height = 900, 640
    left, top = 82, 48
    plot_w, plot_h = 680, 500
    cell_w = plot_w / length(omegas)
    cell_h = plot_h / length(kappas)
    omega_min, omega_max = extrema(omegas)
    kappa_min, kappa_max = extrema(kappas)
    x_for(omega) = left + (omega - omega_min) / max(omega_max - omega_min, EPS) * plot_w
    y_for(kappa) = top + plot_h - (kappa - kappa_min) / max(kappa_max - kappa_min, EPS) * plot_h
    open(path, "w") do io
        println(io, "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"$width\" height=\"$height\" viewBox=\"0 0 $width $height\">")
        println(io, "<rect width=\"100%\" height=\"100%\" fill=\"#fbfaf7\"/>")
        println(io, "<text x=\"$left\" y=\"28\" font-family=\"Arial\" font-size=\"20\" fill=\"#202020\">Sim 1 freezing phase diagram</text>")
        for row in cell_rows
            i = findfirst(==(row.omega), omegas)
            j = findfirst(==(row.kappa), kappas)
            x = left + (i - 1) * cell_w
            y = top + (length(kappas) - j) * cell_h
            fill = row.frozen_rate >= 0.5 ? "#8f2d2d" : row.revisable_rate >= 0.5 ? "#2f7d59" : row.spawn_rate >= 0.5 ? "#d9a441" : "#e8e3d7"
            opacity = 0.32 + 0.62 * max(row.frozen_rate, row.revisable_rate, row.spawn_rate)
            println(io, "<rect x=\"$x\" y=\"$y\" width=\"$cell_w\" height=\"$cell_h\" fill=\"$fill\" fill-opacity=\"$opacity\" stroke=\"#ffffff\" stroke-width=\"1\"/>")
        end
        path_points = join(["$(x_for(row.per_trial_omega)),$(y_for(row.kappa))" for row in slow_path_rows], " ")
        println(io, "<polyline points=\"$path_points\" fill=\"none\" stroke=\"#1f4e79\" stroke-width=\"4\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>")
        println(io, "<circle cx=\"$(x_for(2.85))\" cy=\"$(y_for(0.00))\" r=\"7\" fill=\"#111111\"/>")
        println(io, "<text x=\"$(x_for(2.85) - 112)\" y=\"$(y_for(0.00) - 12)\" font-family=\"Arial\" font-size=\"12\" fill=\"#111111\">single-strike corner</text>")
        println(io, "<text x=\"$(left + 250)\" y=\"$(top + plot_h + 42)\" font-family=\"Arial\" font-size=\"14\" fill=\"#333333\">overwhelm omega</text>")
        println(io, "<text x=\"22\" y=\"$(top + 280)\" font-family=\"Arial\" font-size=\"14\" fill=\"#333333\" transform=\"rotate(-90 22 $(top + 280))\">control kappa</text>")
        println(io, "<rect x=\"790\" y=\"90\" width=\"20\" height=\"20\" fill=\"#8f2d2d\"/><text x=\"818\" y=\"106\" font-family=\"Arial\" font-size=\"13\" fill=\"#333\">frozen</text>")
        println(io, "<rect x=\"790\" y=\"124\" width=\"20\" height=\"20\" fill=\"#2f7d59\"/><text x=\"818\" y=\"140\" font-family=\"Arial\" font-size=\"13\" fill=\"#333\">revisable</text>")
        println(io, "<rect x=\"790\" y=\"158\" width=\"20\" height=\"20\" fill=\"#d9a441\"/><text x=\"818\" y=\"174\" font-family=\"Arial\" font-size=\"13\" fill=\"#333\">spawned</text>")
        println(io, "<line x1=\"790\" y1=\"204\" x2=\"830\" y2=\"204\" stroke=\"#1f4e79\" stroke-width=\"4\"/><text x=\"838\" y=\"208\" font-family=\"Arial\" font-size=\"13\" fill=\"#333\">slow path</text>")
        println(io, "<rect x=\"$left\" y=\"$top\" width=\"$plot_w\" height=\"$plot_h\" fill=\"none\" stroke=\"#333\" stroke-width=\"1.5\"/>")
        println(io, "</svg>")
    end
    return path
end

function bundle_artifact(row)
    return (
        schema_version = "sim1.bundle.v3",
        seed = row.seed,
        route = row.target_route,
        formation = (
            omega = row.omega,
            kappa = row.kappa,
            evidence_yoking_key = "seed=$(row.seed);omega=$(row.omega)",
            aversive_evidence_count = row.aversive_evidence_count,
            aversive_evidence_severity_sum = row.aversive_evidence_severity_sum,
            mean_evidence_precision = row.mean_evidence_precision,
            aversive_action_outcome_count = row.aversive_action_outcome_count,
            arousal_at_write = row.arousal_at_write,
            reflexivity_at_write = row.reflexivity_at_write,
            spawned = row.target_spawned,
            spawn_count = row.spawn_count,
            posterior_predictive_min = row.posterior_predictive_min,
            crp_threshold_last = row.crp_threshold_last
        ),
        revision_probe = (
            disconfirming_trials_measured = true,
            metric = "posterior_predictive_behavior",
            behavior_change = row.revision_behavior_change,
            predicted_aversive_reduction = row.predicted_aversive_reduction,
            approach_probability_increase = row.approach_probability_increase,
            pre_probe_predicted_aversive = row.pre_probe_predicted_aversive,
            post_probe_predicted_aversive = row.post_probe_predicted_aversive,
            pre_probe_approach_probability = row.pre_probe_approach_probability,
            post_probe_approach_probability = row.post_probe_approach_probability,
            structural_precision = row.structural_precision
        ),
        cause_banks = (
            cue_counts = (safe = row.cause_bank_cue_safe, threat = row.cause_bank_cue_threat),
            affect_counts = (safe = row.cause_bank_affect_safe, threat = row.cause_bank_affect_threat),
            policy_counts = (
                approach = row.cause_bank_policy_approach,
                flee = row.cause_bank_policy_flee,
                appease = row.cause_bank_policy_appease,
                attenuate = row.cause_bank_policy_attenuate
            ),
            outcome_counts = (
                approach = (safe = row.outcome_approach_safe, threat = row.outcome_approach_threat),
                flee = (safe = row.outcome_flee_safe, threat = row.outcome_flee_threat),
                appease = (safe = row.outcome_appease_safe, threat = row.outcome_appease_threat),
                attenuate = (safe = row.outcome_attenuate_safe, threat = row.outcome_attenuate_threat)
            )
        )
    )
end

function slow_bundle_artifact(run)
    cause = run.target_cause
    _ = cause_banks(cause)
    return (
        schema_version = "sim1.bundle.v3",
        seed = run.seed,
        route = "slow_accumulation",
        formation = (
            omega = run.omega_center,
            kappa = run.kappa,
            trials = run.trials,
            spawned = run.spawned,
            cross_trial = run.cross_trial,
            cross_structural_precision = run.cross_structural_precision,
            max_per_trial_pe = run.max_per_trial_pe
        ),
        revision_probe = (
            disconfirming_trials_measured = true,
            metric = "posterior_predictive_behavior",
            behavior_change = run.final_revision_behavior_change,
            predicted_aversive_reduction = run.final_predicted_aversive_reduction,
            approach_probability_increase = run.final_approach_probability_increase,
            pre_probe_predicted_aversive = run.final_pre_probe_predicted_aversive,
            post_probe_predicted_aversive = run.final_post_probe_predicted_aversive,
            pre_probe_approach_probability = run.final_pre_probe_approach_probability,
            post_probe_approach_probability = run.final_post_probe_approach_probability,
            structural_precision = run.final_structural_precision
        ),
        cause_banks = (
            cue_counts = (safe = cause.cue_counts[SAFE], threat = cause.cue_counts[AVERSIVE]),
            affect_counts = (safe = cause.affect_counts[SAFE], threat = cause.affect_counts[AVERSIVE]),
            policy_counts = (
                approach = cause.policy_counts[APPROACH],
                flee = cause.policy_counts[FLEE],
                appease = cause.policy_counts[APPEASE],
                attenuate = cause.policy_counts[ATTENUATE]
            ),
            outcome_counts = (
                approach = (safe = cause.outcome_counts[SAFE, APPROACH], threat = cause.outcome_counts[AVERSIVE, APPROACH]),
                flee = (safe = cause.outcome_counts[SAFE, FLEE], threat = cause.outcome_counts[AVERSIVE, FLEE]),
                appease = (safe = cause.outcome_counts[SAFE, APPEASE], threat = cause.outcome_counts[AVERSIVE, APPEASE]),
                attenuate = (safe = cause.outcome_counts[SAFE, ATTENUATE], threat = cause.outcome_counts[AVERSIVE, ATTENUATE])
            )
        )
    )
end

function safe_bundle_name(prefix::String, seed, tag)
    name = replace("$(prefix)_seed$(seed)_$(tag).json", "." => "p")
    return replace(name, "pjson" => ".json")
end

function write_bundle_artifacts(outdir::AbstractString, seed_rows, slow_runs, params::Sim1Params)
    artifacts_dir = ensure_dir(joinpath(outdir, "artifacts"))
    for name in readdir(artifacts_dir)
        startswith(name, "bundle") && endswith(name, ".json") && rm(joinpath(artifacts_dir, name))
    end
    frozen_cells = Set(
        (row.omega, row.kappa) for row in seed_rows
        if mean(other.frozen for other in seed_rows if other.omega == row.omega && other.kappa == row.kappa) >= params.cell_classification_rate
    )
    frozen = sort(
        [row for row in seed_rows if row.frozen && (row.omega, row.kappa) in frozen_cells];
        by = row -> (row.target_spawned ? 0 : 1, row.omega, row.kappa, row.seed)
    )
    selected = first(frozen, min(params.bundle_seed_count, length(frozen)))
    bundle_paths = String[]
    routes = String[]
    for row in selected
        name = safe_bundle_name("bundle", row.seed, "omega$(round(row.omega; digits = 2))_kappa$(round(row.kappa; digits = 2))")
        path = joinpath(artifacts_dir, name)
        write_json(path, bundle_artifact(row))
        push!(bundle_paths, path)
        push!(routes, row.target_route)
    end
    slow_selected = first([run for run in slow_runs if run.crossed && !run.spawned], min(2, count(run -> run.crossed && !run.spawned, slow_runs)))
    for run in slow_selected
        name = safe_bundle_name("bundle_slow", run.seed, "trial$(run.cross_trial)")
        path = joinpath(artifacts_dir, name)
        write_json(path, slow_bundle_artifact(run))
        push!(bundle_paths, path)
        push!(routes, "slow_accumulation")
    end
    manifest = (
        schema_version = "sim1.bundle-manifest.v3",
        bundle_count = length(bundle_paths),
        slow_accumulation_bundle_count = count(==("slow_accumulation"), routes),
        bundles = [basename(path) for path in bundle_paths],
        schema = "sim1.bundle.v3"
    )
    write_json(joinpath(artifacts_dir, "bundle-manifest.json"), manifest)
    return artifacts_dir, bundle_paths
end

function theory_label(results)
    isempty(results.results) && return "null"
    labels = [row.label for row in results.results]
    any(==("falsified"), labels) && return "falsified"
    all(==("support"), labels) && return "support"
    any(==("weak_support"), labels) && return "weak_support"
    return "null"
end

function write_run_readme(path::AbstractString, summary)
    open(path, "w") do io
        println(io, "# Sim 1 T4.6 Step A Pilot")
        println(io)
        println(io, "Pilot seeds only. The exogenous aversive-evidence stream is replayed exactly across kappa; kappa changes only post-challenge overt-action efficacy. Omega changes challenge frequency while delivered observation precision is fixed.")
        println(io)
        println(io, "## Behavioral Revision")
        println(io)
        println(io, "Revision is the larger expected-direction change in cue-level approach outcome prediction or softmax approach probability after the safe probe. No KL score enters classification.")
        println(io)
        println(io, "## Headline Metrics")
        println(io)
        println(io, "- Frozen cells: $(summary.metrics.frozen_cell_count)")
        println(io, "- Revisable cells: $(summary.metrics.revisable_cell_count)")
        println(io, "- Slow-path crossed rate: $(summary.slow_path.crossed_rate)")
        println(io, "- Attenuate corner rate: $(summary.metrics.attenuate_corner_rate)")
        println(io, "- Attenuate max outside rate: $(summary.metrics.attenuate_max_outside_rate)")
        println(io, "- Kappa yoking max aversive-count range: $(summary.evidence_yoking.max_aversive_count_range)")
        println(io, "- Bundle schema: $(summary.artifacts.bundle_schema)")
    end
end

function run_sim1(config::ExperimentConfig; config_path::Union{Nothing, AbstractString} = nothing, output_dir::Union{Nothing, AbstractString} = nothing)
    started = time()
    params = sim1_params(config.model_params)
    omegas = linspace_from_grid(config.sweep_grid, "omega")
    kappas = linspace_from_grid(config.sweep_grid, "kappa")
    outdir = ensure_dir(output_dir)

    seed_rows, cell_rows = run_sweep(config.seeds, omegas, kappas, params)
    classification = classify_grid(cell_rows, omegas, kappas, params)
    slow_runs = [run_slow_path(seed, params) for seed in config.seeds]
    shuffle_runs = [run_slow_path(seed, params; shuffle = true) for seed in config.seeds]
    slow_path = first(slow_runs).path
    attenuation = attenuation_corner_metric(cell_rows, params)
    a11 = omega_only_frozen_metric(config.seeds, omegas, params)
    a12_smoothness, a12_traces = concentration_boundary_smoothness(config.seeds, omegas, kappas, params)
    attenuation_sensitivity = attenuation_preference_sensitivity(config.seeds, omegas, kappas, params)
    artifacts_dir, bundle_paths = write_bundle_artifacts(outdir, seed_rows, slow_runs, params)

    high_high_frozen = high_high_frozen_rate(cell_rows, omegas, kappas)
    yoking = kappa_yoking_metrics(seed_rows, omegas, kappas)
    slow_cross_rate = mean(row.crossed ? 1.0 : 0.0 for row in slow_runs)
    shuffle_cross_rate = mean(row.crossed ? 1.0 : 0.0 for row in shuffle_runs)
    slow_max_pe = maximum(row.max_per_trial_pe for row in slow_runs)
    frozen_rows = [row for row in seed_rows if row.frozen]
    acute_frozen_rows = [row for row in frozen_rows if row.omega >= params.acute_region_omega_min]
    acute_region_present = !isempty(acute_frozen_rows)
    acute_min = acute_region_present ? minimum(row.max_precision_weighted_pe for row in acute_frozen_rows) : 0.0

    criteria_metrics = (
        connected_frozen_region = classification.frozen_largest_component >= params.connected_region_min_cells ? 1.0 : 0.0,
        connected_revisable_region = classification.revisable_largest_component >= params.connected_region_min_cells ? 1.0 : 0.0,
        high_omega_high_kappa_frozen_rate = high_high_frozen,
        slow_path_crosses_below_acute_min = (acute_region_present && slow_cross_rate >= 0.80 && slow_max_pe < acute_min) ? 1.0 : 0.0,
        attenuate_corner_only = attenuation.pass,
        three_traits_logged = 1.0,
        a11_omega_only_frozen_region = a11,
        a12_boundary_smoothness_max_jump = a12_smoothness,
        a13_shuffle_cross_rate = shuffle_cross_rate,
        a14_kappa_yoking_max_count_range = yoking.max_aversive_count_range
    )

    summary = (
        experiment = config.experiment,
        config = config_snapshot(config),
        grid = (
            omega = omegas,
            kappa = kappas,
            cell_count = length(cell_rows),
            seeds_per_cell = length(config.seeds)
        ),
        metrics = (
            spawn_rate_mean = mean(row.spawn_rate for row in cell_rows),
            frozen_cell_count = classification.frozen_cell_count,
            frozen_largest_component = classification.frozen_largest_component,
            revisable_cell_count = classification.revisable_cell_count,
            revisable_largest_component = classification.revisable_largest_component,
            high_omega_high_kappa_frozen_rate = high_high_frozen,
            slow_cross_rate = slow_cross_rate,
            slow_max_per_trial_pe = slow_max_pe,
            acute_region_min_pe = acute_min,
            attenuate_corner_rate = attenuation.corner_rate,
            attenuate_max_outside_rate = attenuation.max_outside_rate,
            representative_bundle_count = length(bundle_paths)
        ),
        behavioral_revision = (
            frozen_max_change = params.behavior_frozen_max_change,
            revisable_min_change = params.behavior_revisable_min_change,
            threat_prediction_threshold = params.threat_prediction_threshold,
            change_definition = "max(pre-minus-post predicted aversive probability, post-minus-pre approach policy probability, zero)"
        ),
        evidence_yoking = yoking,
        three_traits_log = (
            spawn_events = count(row.spawned for row in seed_rows),
            write_time_reflexivity_mean = mean(row.reflexivity_at_write for row in seed_rows),
            postformation_sampling_rate_mean = mean(row.approach_sampling_rate for row in seed_rows),
            frozen_region_postformation_sampling_rate_mean = isempty(frozen_rows) ? 0.0 : mean(row.approach_sampling_rate for row in frozen_rows)
        ),
        phase_boundary = (
            frozen_boundary_min_omega_by_kappa = boundary_by_kappa(cell_rows, omegas, kappas; threshold = params.cell_classification_rate),
            revisable_boundary_min_omega_by_kappa = boundary_by_kappa(cell_rows, omegas, kappas; field = :revisable_rate, threshold = params.cell_classification_rate),
            smoothness = boundary_smoothness(cell_rows, omegas, kappas; threshold = params.cell_classification_rate),
            connected_frozen = criteria_metrics.connected_frozen_region,
            connected_revisable = criteria_metrics.connected_revisable_region
        ),
        slow_path = (
            crossed_rate = slow_cross_rate,
            first_seed_cross_trial = first(slow_runs).cross_trial,
            first_seed_cross_structural_precision = first(slow_runs).cross_structural_precision,
            max_per_trial_pe = slow_max_pe,
            acute_region_min_pe = acute_min,
            shuffle_cross_rate = shuffle_cross_rate,
            no_spawn_cross_rate = mean((row.crossed && !row.spawned) ? 1.0 : 0.0 for row in slow_runs)
        ),
        adversarial = (
            a11_omega_only_frozen_region = a11,
            a12_boundary_smoothness_traces = a12_traces,
            a13_shuffle_cross_rate = shuffle_cross_rate,
            a14_kappa_yoking = yoking
        ),
        sensitivity = (
            attenuation_preference_scale = attenuation_sensitivity
        ),
        criteria = criteria_metrics,
        artifacts = (
            bundle_dir = artifacts_dir,
            bundle_manifest = joinpath(artifacts_dir, "bundle-manifest.json"),
            bundle_schema = "sim1.bundle.v3"
        ),
        criteria_amendments = (
            deconfound = "exogenous challenge evidence is exactly replayed across kappa; kappa changes only overt-action consequence probabilities",
            omega_coupling = "omega changes exogenous challenge frequency; evidence precision is fixed",
            revision_readout = "behavioral change in approach outcome prediction or approach policy probability after the disconfirming probe; KL is not computed"
        ),
        per_seed_metric_count = length(seed_rows),
        cell_metric_count = length(cell_rows)
    )

    summary_path = joinpath(outdir, "summary.json")
    write_json(summary_path, summary)
    write_rows_csv(joinpath(outdir, "per_seed_metrics.csv"), seed_rows)
    write_rows_csv(joinpath(outdir, "posterior_traces.csv"), slow_path)
    write_rows_csv(joinpath(outdir, "cell_metrics.csv"), cell_rows)
    ensure_dir(joinpath(outdir, "figures"))
    write_phase_svg(joinpath(outdir, "figures", "phase_diagram.svg"), cell_rows, slow_path, omegas, kappas)
    write_run_readme(joinpath(outdir, "README.md"), summary)

    criteria_results = nothing
    if !isnothing(config.criteria_path) && isfile(config.criteria_path)
        criteria_results = write_criteria_results(config.criteria_path, summary_path, joinpath(outdir, "criteria-results.json"))
    end
    status = (
        implementation_passed = length(config.seeds) == 10 &&
            config.seeds == collect(1001:1010) &&
            length(omegas) >= 15 &&
            length(kappas) >= 15 &&
            isfile(joinpath(outdir, "figures", "phase_diagram.svg")) &&
            isfile(joinpath(artifacts_dir, "bundle-manifest.json")),
        theory_result = isnothing(criteria_results) ? "null" : theory_label(criteria_results),
        run_phase = "pilot",
        criteria_results_path = isnothing(criteria_results) ? nothing : joinpath(outdir, "criteria-results.json")
    )
    write_json(joinpath(outdir, "status.json"), status)

    metadata = build_reproducibility_metadata(
        config;
        config_path = config_path,
        runtime_seconds = time() - started,
        repo_root = normpath(joinpath(@__DIR__, "..", "..", "..", "..", "..")),
        extra = (
            output_dir = abspath(outdir),
            sim_module = "EmergenceSuite.Sim1",
            criteria_preregistered = config.criteria_path
        )
    )
    write_json(joinpath(outdir, "metadata.json"), metadata)

    return (
        output_dir = outdir,
        summary = summary,
        status = status,
        criteria_results = criteria_results
    )
end

end
