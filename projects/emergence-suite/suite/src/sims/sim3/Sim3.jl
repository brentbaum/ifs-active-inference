module Sim3

using Dates
using Random
using Statistics

using ...Config: ExperimentConfig, config_snapshot
using ...Criteria: write_criteria_results
using ...IO: ensure_dir, write_json, write_rows_csv
using ...Reproducibility: build_reproducibility_metadata

export run_sim3_config

const SELF_HELPLESS = 1
const SELF_RESOURCED = 2
const THREAT_DANGEROUS = 1
const THREAT_SAFE = 2
const POLICY_AVOID = 1
const POLICY_CONTACT = 2

Base.@kwdef struct Sim3Params
    n_association_pretraining_trials::Int = 48
    n_training_trials::Int = 20
    n_heldout_trials::Int = 6
    high_E::Float64 = 0.85
    low_E::Float64 = 0.15
    training_parity_epsilon::Float64 = 0.05
    continuum_root_context_rates::Vector{Float64} = [0.95, 0.80, 0.65, 0.45, 0.25]
    continuum_perceptual_similarities::Vector{Float64} = [1.0, 0.35, 0.20, 0.70, 0.45]
    structural_confound_perceptual_similarity::Float64 = 0.90
    structural_confound_root_context_rate::Float64 = 0.05
    association_prior::Float64 = 1.0
    perceptual_generalization_gain::Float64 = 0.45
    pi_part::Float64 = 3.6
    beta_se::Float64 = 1.0
    lambda_self::Float64 = 0.9
    gamma_se::Float64 = 1.2
    eta_self::Float64 = 7.0
    eta_threat::Float64 = 1.6
    cross_level_coupling::Float64 = 1.35
    outcome_precision::Float64 = 1.6
    policy_precision::Float64 = 3.2
    threat_policy_weight::Float64 = 2.4
    contact_self_bias::Float64 = 0.08
    avoid_bias::Float64 = 0.03
    utility_contact_harm::Float64 = -2.4
    utility_contact_neutral::Float64 = 1.4
    utility_avoid_harm::Float64 = -0.15
    utility_avoid_neutral::Float64 = 0.2
    d_self_helpless::Float64 = 18.0
    d_self_resourced::Float64 = 2.0
    d_threat_dangerous::Float64 = 17.0
    d_threat_safe::Float64 = 3.0
    self_truthfulness::Float64 = 0.88
    outcome_safe_contact_neutral::Float64 = 0.96
    outcome_danger_contact_neutral::Float64 = 0.08
    outcome_safe_avoid_neutral::Float64 = 0.97
    outcome_danger_avoid_neutral::Float64 = 0.78
    first_passage_threshold::Float64 = 0.60
    policy_threshold::Float64 = 0.60
end

"""A world stimulus. Root context rate generates pre-training data; it is never used in inference."""
struct Cue
    id::Int
    label::String
    perceptual_similarity::Float64
    root_context_rate::Float64
    trained::Bool
    structural_confound::Bool
end

Base.@kwdef mutable struct AgentState
    self_banks::Vector{Vector{Float64}}
    threat_banks::Vector{Vector{Float64}}
    initial_threat_banks::Vector{Vector{Float64}}
    cue_root_banks::Vector{Vector{Float64}}
end

Base.@kwdef struct TrialRow
    seed::Int
    condition::String
    architecture::String
    trial::Int
    phase::String
    cue::String
    E_t::Float64
    learned_root_association::Float64
    relational_observation::String
    pi_part_eff::Float64
    lambda_self_eff::Float64
    structural_self_precision::Float64
    structural_threat_precision::Float64
    q_self_prior_resourced::Float64
    q_self_after_resourced::Float64
    q_threat_local_prior_safe::Float64
    q_threat_generalized_prior_safe::Float64
    q_threat_after_relational_safe::Float64
    q_threat_final_safe::Float64
    p_contact::Float64
    action::String
    outcome::String
    log_likelihood::Float64
end

Base.@kwdef struct SeedMetric
    seed::Int
    condition::String
    architecture::String
    E_t::Float64
    first_passage_self::Union{Nothing, Int}
    first_passage_threat::Union{Nothing, Int}
    first_passage_policy::Union{Nothing, Int}
    ordered_cascade::Bool
    cascade_tie::Bool
    cascade_failed::Bool
    training_mean_log_likelihood::Float64
    heldout_mean_log_likelihood::Float64
    trained_cue_contact::Float64
    mean_untrained_contact::Float64
    confound_contact::Float64
    max_untrained_threat_l1_shift::Float64
    final_self_resourced::Float64
    final_trained_threat_safe::Float64
end

normalize(v::AbstractVector{<:Real}) = begin
    out = Float64.(v)
    total = sum(out)
    total <= 0.0 && return fill(1.0 / length(out), length(out))
    out ./ total
end

function softmax(v::AbstractVector{<:Real})
    shifted = Float64.(v) .- maximum(v)
    e = exp.(shifted)
    e ./ sum(e)
end

mean_or_zero(values) = isempty(values) ? 0.0 : mean(values)
ci95(values) = length(values) <= 1 ? 0.0 : 1.96 * std(values) / sqrt(length(values))

get_float(dict::Dict{String, Any}, key::String, default::Float64) = haskey(dict, key) ? Float64(dict[key]) : default
get_int(dict::Dict{String, Any}, key::String, default::Int) = haskey(dict, key) ? Int(dict[key]) : default
get_float_vector(dict::Dict{String, Any}, key::String, default::Vector{Float64}) = haskey(dict, key) ? Float64.(dict[key]) : default

function params_from_config(config::ExperimentConfig)
    raw = config.model_params
    base = Sim3Params()
    return Sim3Params(
        n_association_pretraining_trials = get_int(raw, "n_association_pretraining_trials", base.n_association_pretraining_trials),
        n_training_trials = get_int(raw, "n_training_trials", base.n_training_trials),
        n_heldout_trials = get_int(raw, "n_heldout_trials", base.n_heldout_trials),
        high_E = get_float(raw, "high_E", base.high_E),
        low_E = get_float(raw, "low_E", base.low_E),
        training_parity_epsilon = get_float(raw, "training_parity_epsilon", base.training_parity_epsilon),
        continuum_root_context_rates = get_float_vector(raw, "continuum_root_context_rates", base.continuum_root_context_rates),
        continuum_perceptual_similarities = get_float_vector(raw, "continuum_perceptual_similarities", base.continuum_perceptual_similarities),
        structural_confound_perceptual_similarity = get_float(raw, "structural_confound_perceptual_similarity", base.structural_confound_perceptual_similarity),
        structural_confound_root_context_rate = get_float(raw, "structural_confound_root_context_rate", base.structural_confound_root_context_rate),
        association_prior = get_float(raw, "association_prior", base.association_prior),
        perceptual_generalization_gain = get_float(raw, "perceptual_generalization_gain", base.perceptual_generalization_gain),
        pi_part = get_float(raw, "pi_part", base.pi_part),
        beta_se = get_float(raw, "beta_se", base.beta_se),
        lambda_self = get_float(raw, "lambda_self", base.lambda_self),
        gamma_se = get_float(raw, "gamma_se", base.gamma_se),
        eta_self = get_float(raw, "eta_self", base.eta_self),
        eta_threat = get_float(raw, "eta_threat", base.eta_threat),
        cross_level_coupling = get_float(raw, "cross_level_coupling", base.cross_level_coupling),
        outcome_precision = get_float(raw, "outcome_precision", base.outcome_precision),
        policy_precision = get_float(raw, "policy_precision", base.policy_precision),
        threat_policy_weight = get_float(raw, "threat_policy_weight", base.threat_policy_weight),
        contact_self_bias = get_float(raw, "contact_self_bias", base.contact_self_bias),
        avoid_bias = get_float(raw, "avoid_bias", base.avoid_bias),
        first_passage_threshold = get_float(raw, "first_passage_threshold", base.first_passage_threshold),
        policy_threshold = get_float(raw, "policy_threshold", base.policy_threshold),
    )
end

function cues(params::Sim3Params)
    length(params.continuum_root_context_rates) == length(params.continuum_perceptual_similarities) ||
        error("Sim 3 requires matching root-context-rate and perceptual-similarity vector lengths")
    rows = Cue[]
    for i in eachindex(params.continuum_root_context_rates)
        push!(rows, Cue(
            i,
            "cue_$i",
            params.continuum_perceptual_similarities[i],
            params.continuum_root_context_rates[i],
            i == 1,
            false,
        ))
    end
    push!(rows, Cue(
        length(rows) + 1,
        "structural_confound",
        params.structural_confound_perceptual_similarity,
        params.structural_confound_root_context_rate,
        false,
        true,
    ))
    return rows
end

function initial_agent(params::Sim3Params, n_cues::Int)
    self_banks = [[params.d_self_helpless, params.d_self_resourced] for _ in 1:2]
    threat_banks = [[params.d_threat_dangerous, params.d_threat_safe] for _ in 1:n_cues]
    cue_root_banks = [fill(params.association_prior, 2) for _ in 1:n_cues]
    return AgentState(
        self_banks = self_banks,
        threat_banks = deepcopy(threat_banks),
        initial_threat_banks = deepcopy(threat_banks),
        cue_root_banks = cue_root_banks,
    )
end

function pretrain_associations!(state::AgentState, cue_rows::Vector{Cue}, params::Sim3Params, rng::AbstractRNG)
    for _ in 1:params.n_association_pretraining_trials
        for cue in cue_rows
            observed_root = rand(rng) < cue.root_context_rate ? 1 : 2
            state.cue_root_banks[cue.id][observed_root] += 1.0
        end
    end
    return nothing
end

association_weights(state::AgentState, cue::Cue) = normalize(state.cue_root_banks[cue.id])
learned_root_association(state::AgentState, cue::Cue) = association_weights(state, cue)[1]

function cue_self_prior(state::AgentState, cue::Cue)
    weights = association_weights(state, cue)
    q = zeros(2)
    for root in eachindex(weights)
        q .+= weights[root] .* normalize(state.self_banks[root])
    end
    return normalize(q)
end

function update_self_banks!(state::AgentState, cue::Cue, q_self, params::Sim3Params)
    weights = association_weights(state, cue)
    for root in eachindex(weights)
        state.self_banks[root] .+= params.eta_self .* weights[root] .* q_self
    end
    return nothing
end

function perceptual_overlap(target::Cue, source::Cue)
    target.id == source.id && return 0.0
    source.trained && return target.perceptual_similarity
    target.trained && return source.perceptual_similarity
    return target.perceptual_similarity * source.perceptual_similarity
end

function generalized_threat_prior(state::AgentState, cue::Cue, cue_rows::Vector{Cue}, params::Sim3Params; gain::Float64 = params.perceptual_generalization_gain)
    counts = copy(state.threat_banks[cue.id])
    for source in cue_rows
        source.id == cue.id && continue
        learned_evidence = max.(state.threat_banks[source.id] .- state.initial_threat_banks[source.id], 0.0)
        counts .+= gain * perceptual_overlap(cue, source) .* learned_evidence
    end
    return normalize(counts)
end

function effective_precisions(params::Sim3Params, E_t::Float64)
    return params.pi_part * exp(-params.beta_se * E_t), params.lambda_self * exp(params.gamma_se * E_t)
end

function direct_relational_update(params::Sim3Params, prior, observed_resourced::Bool, pi_part_eff::Float64, lambda_self_eff::Float64)
    resourced_likelihood = [1.0 - params.self_truthfulness, params.self_truthfulness]
    likelihood = observed_resourced ? resourced_likelihood : 1.0 .- resourced_likelihood
    ln_q = pi_part_eff .* log.(prior .+ eps(Float64)) .+ lambda_self_eff .* log.(likelihood .+ eps(Float64))
    return softmax(ln_q)
end

function condition_threat_on_self(params::Sim3Params, prior_threat, q_self)
    self_signal = q_self[SELF_RESOURCED] - q_self[SELF_HELPLESS]
    return softmax(log.(prior_threat .+ eps(Float64)) .+ params.cross_level_coupling * self_signal .* [-1.0, 1.0])
end

function condition_self_on_threat(params::Sim3Params, prior_self, q_threat)
    threat_signal = q_threat[THREAT_SAFE] - q_threat[THREAT_DANGEROUS]
    return softmax(log.(prior_self .+ eps(Float64)) .+ params.cross_level_coupling * threat_signal .* [-1.0, 1.0])
end

function outcome_neutral_probability(params::Sim3Params, action::Int, threat_state::Int)
    if action == POLICY_CONTACT
        return threat_state == THREAT_SAFE ? params.outcome_safe_contact_neutral : params.outcome_danger_contact_neutral
    end
    return threat_state == THREAT_SAFE ? params.outcome_safe_avoid_neutral : params.outcome_danger_avoid_neutral
end

function infer_threat_from_outcome(params::Sim3Params, q_threat, action::Int, outcome::Symbol)
    neutral_likelihood = [
        outcome_neutral_probability(params, action, THREAT_DANGEROUS),
        outcome_neutral_probability(params, action, THREAT_SAFE),
    ]
    likelihood = outcome == :neutral ? neutral_likelihood : 1.0 .- neutral_likelihood
    return softmax(log.(q_threat .+ eps(Float64)) .+ params.outcome_precision .* log.(likelihood .+ eps(Float64)))
end

function policy_probs(params::Sim3Params, q_self, q_threat)
    self_signal = q_self[SELF_RESOURCED] - q_self[SELF_HELPLESS]
    threat_signal = q_threat[THREAT_SAFE] - q_threat[THREAT_DANGEROUS]
    contact_score =
        params.threat_policy_weight * threat_signal +
        params.contact_self_bias * self_signal +
        q_threat[THREAT_SAFE] * params.utility_contact_neutral +
        q_threat[THREAT_DANGEROUS] * params.utility_contact_harm
    avoid_score =
        -params.threat_policy_weight * threat_signal -
        params.avoid_bias * self_signal +
        q_threat[THREAT_SAFE] * params.utility_avoid_neutral +
        q_threat[THREAT_DANGEROUS] * params.utility_avoid_harm
    return softmax(params.policy_precision .* [avoid_score, contact_score])
end

"""
Run the same self → threat → policy schedule for both models. The only model
branch reverses the conditioning edge: H1 receives relational evidence at self
and conditions threat on self; H2 conditions self on the prior threat message
and receives the same relational evidence at threat.
"""
function trial_step!(
    state::AgentState,
    cue::Cue,
    cue_rows::Vector{Cue},
    params::Sim3Params,
    rng::AbstractRNG,
    seed::Int,
    condition::String,
    architecture::Symbol,
    E_t::Float64,
    trial::Int,
    phase::String;
    learn::Bool,
)
    architecture in (:H1, :H2) || error("Unknown Sim 3 architecture: $architecture")
    q_self_prior = cue_self_prior(state, cue)
    q_threat_local = normalize(state.threat_banks[cue.id])
    q_threat_generalized = generalized_threat_prior(state, cue, cue_rows, params)
    pi_part_eff, lambda_self_eff = effective_precisions(params, E_t)
    observed_resourced = rand(rng) < params.self_truthfulness

    if architecture == :H1
        q_self_after = direct_relational_update(params, q_self_prior, observed_resourced, pi_part_eff, lambda_self_eff)
        q_threat_after = condition_threat_on_self(params, q_threat_generalized, q_self_after)
    else
        q_self_after = condition_self_on_threat(params, q_self_prior, q_threat_generalized)
        q_threat_after = direct_relational_update(params, q_threat_generalized, observed_resourced, pi_part_eff, lambda_self_eff)
    end

    qpi = policy_probs(params, q_self_after, q_threat_after)
    action = POLICY_CONTACT
    neutral_probability = params.outcome_safe_contact_neutral
    outcome = rand(rng) < neutral_probability ? :neutral : :harm
    predicted_neutral = sum(q_threat_after[i] * outcome_neutral_probability(params, action, i) for i in 1:2)
    log_likelihood = log((outcome == :neutral ? predicted_neutral : 1.0 - predicted_neutral) + eps(Float64))
    q_threat_final = infer_threat_from_outcome(params, q_threat_after, action, outcome)

    if learn
        update_self_banks!(state, cue, q_self_after, params)
        state.threat_banks[cue.id] .+= params.eta_threat .* q_threat_final
    end

    return TrialRow(
        seed = seed,
        condition = condition,
        architecture = string(architecture),
        trial = trial,
        phase = phase,
        cue = cue.label,
        E_t = E_t,
        learned_root_association = learned_root_association(state, cue),
        relational_observation = observed_resourced ? "resourced" : "helpless",
        pi_part_eff = pi_part_eff,
        lambda_self_eff = lambda_self_eff,
        structural_self_precision = sum(sum, state.self_banks),
        structural_threat_precision = sum(state.threat_banks[cue.id]),
        q_self_prior_resourced = q_self_prior[SELF_RESOURCED],
        q_self_after_resourced = q_self_after[SELF_RESOURCED],
        q_threat_local_prior_safe = q_threat_local[THREAT_SAFE],
        q_threat_generalized_prior_safe = q_threat_generalized[THREAT_SAFE],
        q_threat_after_relational_safe = q_threat_after[THREAT_SAFE],
        q_threat_final_safe = q_threat_final[THREAT_SAFE],
        p_contact = qpi[POLICY_CONTACT],
        action = "contact",
        outcome = string(outcome),
        log_likelihood = log_likelihood,
    )
end

function probe_cue(state::AgentState, cue::Cue, params::Sim3Params, architecture::Symbol, E_t::Float64; cue_rows::Vector{Cue} = cues(params))
    q_self_prior = cue_self_prior(state, cue)
    q_threat_local = normalize(state.threat_banks[cue.id])
    q_threat_generalized = generalized_threat_prior(state, cue, cue_rows, params)
    if architecture == :H1
        q_self_after = q_self_prior
        q_threat_after = condition_threat_on_self(params, q_threat_generalized, q_self_after)
        q_threat_no_perceptual = condition_threat_on_self(params, q_threat_local, q_self_after)
        q_self_no_perceptual = q_self_after
    else
        q_self_after = condition_self_on_threat(params, q_self_prior, q_threat_generalized)
        q_threat_after = q_threat_generalized
        q_self_no_perceptual = condition_self_on_threat(params, q_self_prior, q_threat_local)
        q_threat_no_perceptual = q_threat_local
    end
    qpi = policy_probs(params, q_self_after, q_threat_after)
    qpi_no_perceptual = policy_probs(params, q_self_no_perceptual, q_threat_no_perceptual)
    pi_part_eff, lambda_self_eff = effective_precisions(params, E_t)
    return (
        learned_root_association = learned_root_association(state, cue),
        q_self_prior = q_self_prior,
        q_self_after = q_self_after,
        q_threat_local = q_threat_local,
        q_threat_generalized = q_threat_generalized,
        q_threat_after = q_threat_after,
        p_contact = qpi[POLICY_CONTACT],
        p_contact_no_perceptual = qpi_no_perceptual[POLICY_CONTACT],
        pi_part_eff = pi_part_eff,
        lambda_self_eff = lambda_self_eff,
    )
end

function first_passage(rows::Vector{TrialRow}, params::Sim3Params)
    self_time = nothing
    threat_time = nothing
    policy_time = nothing
    for row in rows
        row.phase == "training" || continue
        if self_time === nothing && row.q_self_after_resourced >= params.first_passage_threshold
            self_time = row.trial
        end
        if threat_time === nothing && row.q_threat_after_relational_safe >= params.first_passage_threshold
            threat_time = row.trial
        end
        if policy_time === nothing && row.p_contact >= params.policy_threshold
            policy_time = row.trial
        end
    end
    return self_time, threat_time, policy_time
end

function cascade_flags(self_time, threat_time, policy_time)
    complete = self_time !== nothing && threat_time !== nothing && policy_time !== nothing
    complete || return false, false, true
    tie = self_time == threat_time || self_time == policy_time || threat_time == policy_time
    ordered = self_time < threat_time && threat_time < policy_time
    return ordered, tie, !ordered && !tie
end

function run_condition_seed(seed::Int, params::Sim3Params, cue_rows::Vector{Cue}; condition::String, architecture::Symbol, E_t::Float64)
    rng = MersenneTwister(seed)
    state = initial_agent(params, length(cue_rows))
    pretrain_associations!(state, cue_rows, params, rng)
    train_cue = only(filter(cue -> cue.trained, cue_rows))
    rows = TrialRow[]
    for trial in 1:params.n_training_trials
        push!(rows, trial_step!(state, train_cue, cue_rows, params, rng, seed, condition, architecture, E_t, trial, "training"; learn = true))
    end
    for heldout in 1:params.n_heldout_trials
        trial = params.n_training_trials + heldout
        push!(rows, trial_step!(state, train_cue, cue_rows, params, rng, seed, condition, architecture, E_t, trial, "heldout"; learn = false))
    end

    probe_results = Dict(cue.label => probe_cue(state, cue, params, architecture, E_t; cue_rows = cue_rows) for cue in cue_rows)
    self_time, threat_time, policy_time = first_passage(rows, params)
    ordered, tie, failed = cascade_flags(self_time, threat_time, policy_time)
    training_ll = [row.log_likelihood for row in rows if row.phase == "training"]
    heldout_ll = [row.log_likelihood for row in rows if row.phase == "heldout"]
    untrained = [probe_results[cue.label].p_contact for cue in cue_rows if !cue.trained && !cue.structural_confound]
    confound = only([probe_results[cue.label].p_contact for cue in cue_rows if cue.structural_confound])
    shifts = [
        sum(abs.(normalize(state.threat_banks[cue.id]) .- normalize(state.initial_threat_banks[cue.id])))
        for cue in cue_rows if !cue.trained
    ]
    metric = SeedMetric(
        seed = seed,
        condition = condition,
        architecture = string(architecture),
        E_t = E_t,
        first_passage_self = self_time,
        first_passage_threat = threat_time,
        first_passage_policy = policy_time,
        ordered_cascade = ordered,
        cascade_tie = tie,
        cascade_failed = failed,
        training_mean_log_likelihood = mean(training_ll),
        heldout_mean_log_likelihood = mean(heldout_ll),
        trained_cue_contact = probe_results[train_cue.label].p_contact,
        mean_untrained_contact = mean_or_zero(untrained),
        confound_contact = confound,
        max_untrained_threat_l1_shift = maximum(shifts),
        final_self_resourced = normalize(state.self_banks[1])[SELF_RESOURCED],
        final_trained_threat_safe = normalize(state.threat_banks[train_cue.id])[THREAT_SAFE],
    )
    return metric, rows, probe_results, state
end

function summarize_condition(seed_metrics::Vector{SeedMetric}, probe_maps, cue_rows::Vector{Cue})
    cue_summaries = NamedTuple[]
    for cue in cue_rows
        probes = [probe_map[cue.label] for probe_map in probe_maps]
        contacts = [probe.p_contact for probe in probes]
        push!(cue_summaries, (
            cue = cue.label,
            perceptual_similarity = cue.perceptual_similarity,
            generative_root_context_rate = cue.root_context_rate,
            mean_learned_root_association = mean(probe.learned_root_association for probe in probes),
            ci95_learned_root_association = ci95([probe.learned_root_association for probe in probes]),
            trained = cue.trained,
            structural_confound = cue.structural_confound,
            mean_local_threat_safe = mean(probe.q_threat_local[THREAT_SAFE] for probe in probes),
            mean_generalized_threat_safe = mean(probe.q_threat_generalized[THREAT_SAFE] for probe in probes),
            mean_contact = mean(contacts),
            mean_contact_no_perceptual = mean(probe.p_contact_no_perceptual for probe in probes),
            ci95_contact = ci95(contacts),
        ))
    end
    return (
        n_seeds = length(seed_metrics),
        mean_training_log_likelihood = mean(row.training_mean_log_likelihood for row in seed_metrics),
        mean_heldout_log_likelihood = mean(row.heldout_mean_log_likelihood for row in seed_metrics),
        ordered_cascade_count = count(row -> row.ordered_cascade, seed_metrics),
        cascade_tie_count = count(row -> row.cascade_tie, seed_metrics),
        cascade_failed_count = count(row -> row.cascade_failed, seed_metrics),
        self_before_threat_count = count(row -> row.first_passage_self !== nothing && row.first_passage_threat !== nothing && row.first_passage_self < row.first_passage_threat, seed_metrics),
        threat_policy_same_trial_count = count(row -> row.first_passage_threat !== nothing && row.first_passage_policy !== nothing && row.first_passage_threat == row.first_passage_policy, seed_metrics),
        ordered_cascade_rate = mean(row.ordered_cascade for row in seed_metrics),
        cascade_tie_rate = mean(row.cascade_tie for row in seed_metrics),
        cascade_failed_rate = mean(row.cascade_failed for row in seed_metrics),
        mean_trained_cue_contact = mean(row.trained_cue_contact for row in seed_metrics),
        mean_untrained_contact = mean(row.mean_untrained_contact for row in seed_metrics),
        mean_confound_contact = mean(row.confound_contact for row in seed_metrics),
        max_untrained_threat_l1_shift = maximum(row.max_untrained_threat_l1_shift for row in seed_metrics),
        mean_final_self_resourced = mean(row.final_self_resourced for row in seed_metrics),
        mean_final_trained_threat_safe = mean(row.final_trained_threat_safe for row in seed_metrics),
        cues = cue_summaries,
    )
end

function run_named_condition(seeds, params, cue_rows; kwargs...)
    metrics = SeedMetric[]
    traces = TrialRow[]
    probes = Any[]
    states = AgentState[]
    for seed in seeds
        metric, rows, probe_map, state = run_condition_seed(seed, params, cue_rows; kwargs...)
        push!(metrics, metric)
        append!(traces, rows)
        push!(probes, probe_map)
        push!(states, state)
    end
    return metrics, traces, probes, states, summarize_condition(metrics, probes, cue_rows)
end

function continuum_rows(condition_summary)
    return [row for row in condition_summary.cues if !row.trained && !row.structural_confound]
end

function monotone_gradient_score(condition_summary)
    rows = sort(continuum_rows(condition_summary); by = row -> -row.mean_learned_root_association)
    length(rows) <= 1 && return 0.0
    return mean(rows[i].mean_contact >= rows[i + 1].mean_contact - 1e-9 for i in 1:(length(rows) - 1))
end

function pearson(xs, ys)
    length(xs) == length(ys) || error("Pearson vectors must match")
    length(xs) <= 1 && return 0.0
    xbar, ybar = mean(xs), mean(ys)
    xdev = xs .- xbar
    ydev = ys .- ybar
    denom = sqrt(sum(abs2, xdev) * sum(abs2, ydev))
    denom <= eps(Float64) && return 0.0
    return sum(xdev .* ydev) / denom
end

function partial_correlation(xs, ys, controls)
    rxy = pearson(xs, ys)
    rxc = pearson(xs, controls)
    ryc = pearson(ys, controls)
    denom = sqrt(max((1.0 - rxc^2) * (1.0 - ryc^2), 0.0))
    denom <= eps(Float64) && return 0.0
    return (rxy - rxc * ryc) / denom
end

function learned_association_metrics(probe_maps, cue_rows::Vector{Cue})
    xs = Float64[]
    ys = Float64[]
    perceptual = Float64[]
    for probe_map in probe_maps
        for cue in cue_rows
            cue.trained && continue
            probe = probe_map[cue.label]
            push!(xs, probe.learned_root_association)
            push!(ys, probe.p_contact)
            push!(perceptual, cue.perceptual_similarity)
        end
    end
    return (
        correlation = pearson(xs, ys),
        partial_correlation_controlling_perceptual = partial_correlation(xs, ys, perceptual),
    )
end

function flatten_probe_rows(seeds, condition::String, architecture::Symbol, probe_maps, states, cue_rows::Vector{Cue})
    rows = NamedTuple[]
    for (seed_ix, seed) in enumerate(seeds)
        state = states[seed_ix]
        probes = probe_maps[seed_ix]
        for cue in cue_rows
            probe = probes[cue.label]
            root_counts = state.cue_root_banks[cue.id]
            push!(rows, (
                seed = seed,
                condition = condition,
                architecture = string(architecture),
                cue = cue.label,
                trained = cue.trained,
                structural_confound = cue.structural_confound,
                perceptual_similarity = cue.perceptual_similarity,
                generative_root_context_rate = cue.root_context_rate,
                learned_root_1_count = root_counts[1],
                learned_root_2_count = root_counts[2],
                learned_root_association = probe.learned_root_association,
                local_threat_safe = probe.q_threat_local[THREAT_SAFE],
                generalized_threat_safe = probe.q_threat_generalized[THREAT_SAFE],
                inferred_threat_safe = probe.q_threat_after[THREAT_SAFE],
                p_contact = probe.p_contact,
                p_contact_no_perceptual = probe.p_contact_no_perceptual,
            ))
        end
    end
    return rows
end

function theory_label(results)
    results === nothing && return "null"
    labels = [row.label for row in results.results]
    isempty(labels) && return "null"
    any(==("falsified"), labels) && return "falsified"
    all(==("support"), labels) && return "support"
    any(==("weak_support"), labels) && return "weak_support"
    return "null"
end

function write_transfer_svg(path::AbstractString, summary_by_condition)
    h1 = summary_by_condition["H1-witnessing"].cues
    exposure = summary_by_condition["H1-exposure"].cues
    h2 = summary_by_condition["H2-witnessing"].cues
    function points(rows)
        plotted = sort([row for row in rows if !row.trained]; by = row -> row.mean_learned_root_association)
        coords = String[]
        for row in plotted
            x = 70 + row.mean_learned_root_association * 420
            y = 300 - row.mean_contact * 210
            push!(coords, "$(round(x, digits=1)),$(round(y, digits=1))")
        end
        return join(coords, " ")
    end
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="680" height="360" viewBox="0 0 680 360">
      <rect width="680" height="360" fill="#fbfaf7"/>
      <line x1="70" y1="300" x2="520" y2="300" stroke="#222" stroke-width="2"/>
      <line x1="70" y1="70" x2="70" y2="300" stroke="#222" stroke-width="2"/>
      <text x="70" y="38" font-family="Arial" font-size="18" fill="#222">Sim 3 learned-association transfer</text>
      <text x="190" y="338" font-family="Arial" font-size="13" fill="#444">learned P(root 1 | cue)</text>
      <text x="18" y="225" font-family="Arial" font-size="13" fill="#444" transform="rotate(-90 18 225)">P(contact)</text>
      <polyline points="$(points(h1))" fill="none" stroke="#8f3f2d" stroke-width="4"/>
      <polyline points="$(points(exposure))" fill="none" stroke="#3f6f92" stroke-width="4"/>
      <polyline points="$(points(h2))" fill="none" stroke="#557a46" stroke-width="4"/>
      <text x="535" y="110" font-family="Arial" font-size="12" fill="#8f3f2d">H1 witnessing</text>
      <text x="535" y="135" font-family="Arial" font-size="12" fill="#3f6f92">H1 exposure</text>
      <text x="535" y="160" font-family="Arial" font-size="12" fill="#557a46">H2 witnessing</text>
    </svg>
    """
    open(path, "w") do io
        write(io, svg)
    end
    return path
end

function run_sim3_config(config::ExperimentConfig; config_path::Union{Nothing, AbstractString} = nothing, output_dir::Union{Nothing, AbstractString} = nothing)
    started = time()
    params = params_from_config(config)
    cue_rows = cues(params)
    outdir = output_dir === nothing ? normpath(joinpath(config.output_dir, config.experiment, config.label === nothing ? Dates.format(Dates.now(Dates.UTC), Dates.dateformat"yyyymmddTHHMMSSZ") : config.label)) : output_dir
    ensure_dir(outdir)

    h1_metrics, h1_traces, h1_probes, h1_states, h1_summary = run_named_condition(
        config.seeds, params, cue_rows;
        condition = "H1-witnessing", architecture = :H1, E_t = params.high_E,
    )
    h2_metrics, h2_traces, h2_probes, h2_states, h2_summary = run_named_condition(
        config.seeds, params, cue_rows;
        condition = "H2-witnessing", architecture = :H2, E_t = params.high_E,
    )

    parity_diff = abs(h1_summary.mean_training_log_likelihood - h2_summary.mean_training_log_likelihood)
    parity_diff <= params.training_parity_epsilon || error(
        "Sim 3 training parity stop: H1/H2 mean training log-likelihood diff $(parity_diff) exceeds epsilon $(params.training_parity_epsilon)",
    )

    exposure_metrics, exposure_traces, exposure_probes, exposure_states, exposure_summary = run_named_condition(
        config.seeds, params, cue_rows;
        condition = "H1-exposure", architecture = :H1, E_t = params.low_E,
    )

    assoc = learned_association_metrics(h1_probes, cue_rows)
    structural_cue = cue_rows[3]
    confound_cue = only(filter(cue -> cue.structural_confound, cue_rows))
    structural_contacts = [probes[structural_cue.label].p_contact for probes in h1_probes]
    confound_contacts = [probes[confound_cue.label].p_contact for probes in h1_probes]
    confound_perceptual_contact_gains = [
        probes[confound_cue.label].p_contact - probes[confound_cue.label].p_contact_no_perceptual
        for probes in h1_probes
    ]
    confound_perceptual_threat_gains = [
        probes[confound_cue.label].q_threat_generalized[THREAT_SAFE] - probes[confound_cue.label].q_threat_local[THREAT_SAFE]
        for probes in h1_probes
    ]

    initial_self_resourced = params.d_self_resourced / (params.d_self_helpless + params.d_self_resourced)
    initial_threat_safe = params.d_threat_safe / (params.d_threat_dangerous + params.d_threat_safe)
    metrics = (
        training_parity = (
            abs_mean_log_likelihood_diff = parity_diff,
            epsilon = params.training_parity_epsilon,
        ),
        out_of_sample = (
            h1_mean_log_likelihood = h1_summary.mean_heldout_log_likelihood,
            h2_mean_log_likelihood = h2_summary.mean_heldout_log_likelihood,
            h1_minus_h2_mean_log_likelihood = h1_summary.mean_heldout_log_likelihood - h2_summary.mean_heldout_log_likelihood,
        ),
        cascade = (
            resolution = "trial",
            witnessing_earned_count = h1_summary.ordered_cascade_count,
            witnessing_self_before_threat_count = h1_summary.self_before_threat_count,
            witnessing_threat_policy_same_trial_count = h1_summary.threat_policy_same_trial_count,
            exposure_self_before_threat_count = exposure_summary.self_before_threat_count,
            h2_self_before_threat_count = h2_summary.self_before_threat_count,
            witnessing_tie_count = h1_summary.cascade_tie_count,
            witnessing_failed_count = h1_summary.cascade_failed_count,
            witnessing_order_rate = h1_summary.ordered_cascade_rate,
            witnessing_tie_rate = h1_summary.cascade_tie_rate,
            witnessing_failed_rate = h1_summary.cascade_failed_rate,
            exposure_earned_count = exposure_summary.ordered_cascade_count,
            exposure_tie_count = exposure_summary.cascade_tie_count,
            exposure_failed_count = exposure_summary.cascade_failed_count,
            exposure_order_rate = exposure_summary.ordered_cascade_rate,
            exposure_tie_rate = exposure_summary.cascade_tie_rate,
            exposure_failed_rate = exposure_summary.cascade_failed_rate,
            h2_earned_count = h2_summary.ordered_cascade_count,
            h2_tie_count = h2_summary.cascade_tie_count,
            h2_failed_count = h2_summary.cascade_failed_count,
            h2_order_rate = h2_summary.ordered_cascade_rate,
            h2_tie_rate = h2_summary.cascade_tie_rate,
            h2_failed_rate = h2_summary.cascade_failed_rate,
        ),
        transfer = (
            h1_witnessing_mean = h1_summary.mean_untrained_contact,
            exposure_mean = exposure_summary.mean_untrained_contact,
            h2_mean = h2_summary.mean_untrained_contact,
            h1_witnessing_minus_exposure_mean = h1_summary.mean_untrained_contact - exposure_summary.mean_untrained_contact,
            learned_association_gradient_score = monotone_gradient_score(h1_summary),
            learned_association_contact_correlation = assoc.correlation,
            learned_association_partial_correlation = assoc.partial_correlation_controlling_perceptual,
        ),
        perceptual_generalization = (
            root_poor_threat_safe_gain = mean(confound_perceptual_threat_gains),
            root_poor_contact_gain = mean(confound_perceptual_contact_gains),
            structural_cue_minus_root_poor_perceptual_contact = mean(structural_contacts .- confound_contacts),
            max_untrained_threat_bank_l1_shift = maximum([
                h1_summary.max_untrained_threat_l1_shift,
                exposure_summary.max_untrained_threat_l1_shift,
                h2_summary.max_untrained_threat_l1_shift,
            ]),
        ),
        h2_liveness = (
            self_bank_absolute_shift = abs(h2_summary.mean_final_self_resourced - initial_self_resourced),
            trained_threat_safe_shift = h2_summary.mean_final_trained_threat_safe - initial_threat_safe,
            mean_untrained_contact = h2_summary.mean_untrained_contact,
        ),
    )

    summary_by_condition = Dict(
        "H1-witnessing" => h1_summary,
        "H1-exposure" => exposure_summary,
        "H2-witnessing" => h2_summary,
    )
    all_seed_metrics = vcat(h1_metrics, exposure_metrics, h2_metrics)
    all_traces = vcat(h1_traces, exposure_traces, h2_traces)
    all_probe_rows = vcat(
        flatten_probe_rows(config.seeds, "H1-witnessing", :H1, h1_probes, h1_states, cue_rows),
        flatten_probe_rows(config.seeds, "H1-exposure", :H1, exposure_probes, exposure_states, cue_rows),
        flatten_probe_rows(config.seeds, "H2-witnessing", :H2, h2_probes, h2_states, cue_rows),
    )
    summary = (
        experiment = config.experiment,
        config = config_snapshot(config),
        design = (
            protocol_stage = "Phase 4 Step A pilot",
            cues = [(
                label = cue.label,
                perceptual_similarity = cue.perceptual_similarity,
                generative_root_context_rate = cue.root_context_rate,
                trained = cue.trained,
                structural_confound = cue.structural_confound,
            ) for cue in cue_rows],
            root_pathway = "agent-learned Dirichlet P(root | cue) from pre-training co-occurrences",
            perceptual_generalization_channel = "feature-overlap-weighted sharing of learned cue-local threat evidence at inference; target banks are not mutated",
            architecture_difference = "conditioning direction only: H1 self→threat; H2 threat→self",
            first_passage_resolution = "integer training-trial index; same-trial crossings are ties",
            heldout_design = "frozen-bank predictive likelihood on subsequent training-cue trials",
            structural_test_cue = structural_cue.label,
            perceptual_root_poor_cue = confound_cue.label,
        ),
        conditions = summary_by_condition,
        metrics = metrics,
        per_seed_metric_count = length(all_seed_metrics),
        trace_row_count = length(all_traces),
        probe_row_count = length(all_probe_rows),
    )
    write_json(joinpath(outdir, "summary.json"), summary)
    write_rows_csv(joinpath(outdir, "per_seed_metrics.csv"), all_seed_metrics)
    write_rows_csv(joinpath(outdir, "posterior_traces.csv"), all_traces)
    write_rows_csv(joinpath(outdir, "probe_metrics.csv"), all_probe_rows)
    ensure_dir(joinpath(outdir, "figures"))
    write_transfer_svg(joinpath(outdir, "figures", "transfer_gradient.svg"), summary_by_condition)

    criteria_results = nothing
    if config.criteria_path !== nothing && isfile(config.criteria_path)
        criteria_results = write_criteria_results(config.criteria_path, joinpath(outdir, "summary.json"), joinpath(outdir, "criteria-results.json"))
    end
    status = (
        implementation_passed = true,
        theory_result = theory_label(criteria_results),
        criteria_results_path = criteria_results === nothing ? nothing : joinpath(outdir, "criteria-results.json"),
    )
    write_json(joinpath(outdir, "status.json"), status)
    metadata = build_reproducibility_metadata(
        config;
        config_path = config_path,
        runtime_seconds = time() - started,
        repo_root = normpath(joinpath(@__DIR__, "..", "..", "..", "..", "..")),
        extra = (output_dir = abspath(outdir),),
    )
    write_json(joinpath(outdir, "metadata.json"), metadata)
    return (output_dir = outdir, summary = summary, status = status, criteria_results = criteria_results)
end

end
