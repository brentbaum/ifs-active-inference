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
    n_training_trials::Int = 20
    n_probe_trials::Int = 1
    high_E::Float64 = 0.85
    low_E::Float64 = 0.15
    training_parity_epsilon::Float64 = 0.05
    continuum_root_couplings::Vector{Float64} = [1.0, 0.8, 0.6, 0.4, 0.2]
    continuum_perceptual_similarities::Vector{Float64} = [1.0, 0.35, 0.2, 0.70, 0.45]
    structural_confound_perceptual_similarity::Float64 = 0.9
    structural_confound_root_coupling::Float64 = 0.0
    e_sweep::Vector{Float64} = collect(0.05:0.10:0.95)
    pi_part::Float64 = 3.6
    beta_se::Float64 = 1.0
    lambda_self::Float64 = 0.7
    gamma_se::Float64 = 1.2
    eta_self::Float64 = 1.0
    eta_threat::Float64 = 1.6
    self_to_threat_coupling::Float64 = 1.35
    h2_threat_to_self_coupling::Float64 = 1.35
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
    readout_min_range::Float64 = 0.20
end

struct Cue
    id::Int
    label::String
    perceptual_similarity::Float64
    root_coupling::Float64
    root_id::Int
    trained::Bool
    structural_confound::Bool
end

Base.@kwdef mutable struct AgentState
    self_banks::Dict{Int, Vector{Float64}}
    threat_banks::Vector{Vector{Float64}}
    initial_threat_banks::Vector{Vector{Float64}}
end

Base.@kwdef struct TrialRow
    seed::Int
    condition::String
    architecture::String
    trial::Int
    phase::String
    cue::String
    E_t::Float64
    pi_part_eff::Float64
    lambda_self_eff::Float64
    structural_self_precision::Float64
    structural_threat_precision::Float64
    q_self_prior_resourced::Float64
    q_self_after_resourced::Float64
    q_threat_prior_safe::Float64
    q_threat_after_relational_safe::Float64
    q_threat_final_safe::Float64
    p_contact::Float64
    action::String
    outcome::String
end

Base.@kwdef struct SeedMetric
    seed::Int
    condition::String
    architecture::String
    E_t::Float64
    first_passage_self::Union{Nothing, Float64}
    first_passage_threat::Union{Nothing, Float64}
    first_passage_policy::Union{Nothing, Float64}
    ordered_cascade::Bool
    training_log_evidence::Float64
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

function mean_or_zero(values)
    isempty(values) && return 0.0
    return mean(values)
end

function ci95(values)
    n = length(values)
    n <= 1 && return 0.0
    return 1.96 * std(values) / sqrt(n)
end

function get_float(dict::Dict{String, Any}, key::String, default::Float64)
    haskey(dict, key) || return default
    return Float64(dict[key])
end

function get_int(dict::Dict{String, Any}, key::String, default::Int)
    haskey(dict, key) || return default
    return Int(dict[key])
end

function get_float_vector(dict::Dict{String, Any}, key::String, default::Vector{Float64})
    haskey(dict, key) || return default
    return Float64.(dict[key])
end

function params_from_config(config::ExperimentConfig)
    raw = config.model_params
    base = Sim3Params()
    return Sim3Params(
        n_training_trials = get_int(raw, "n_training_trials", base.n_training_trials),
        n_probe_trials = get_int(raw, "n_probe_trials", base.n_probe_trials),
        high_E = get_float(raw, "high_E", base.high_E),
        low_E = get_float(raw, "low_E", base.low_E),
        training_parity_epsilon = get_float(raw, "training_parity_epsilon", base.training_parity_epsilon),
        continuum_root_couplings = get_float_vector(raw, "continuum_root_couplings", get_float_vector(raw, "continuum_similarities", base.continuum_root_couplings)),
        continuum_perceptual_similarities = get_float_vector(raw, "continuum_perceptual_similarities", base.continuum_perceptual_similarities),
        structural_confound_perceptual_similarity = get_float(raw, "structural_confound_perceptual_similarity", get_float(raw, "structural_confound_similarity", base.structural_confound_perceptual_similarity)),
        structural_confound_root_coupling = get_float(raw, "structural_confound_root_coupling", base.structural_confound_root_coupling),
        e_sweep = get_float_vector(raw, "e_sweep", base.e_sweep),
    )
end

function cues(params::Sim3Params)
    length(params.continuum_root_couplings) == length(params.continuum_perceptual_similarities) ||
        error("Sim 3 cue design requires matching root_coupling and perceptual_similarity vector lengths")
    rows = Cue[]
    for i in eachindex(params.continuum_root_couplings)
        push!(
            rows,
            Cue(
                i,
                "cue_$i",
                params.continuum_perceptual_similarities[i],
                params.continuum_root_couplings[i],
                1,
                i == 1,
                false,
            ),
        )
    end
    push!(
        rows,
        Cue(
            length(rows) + 1,
            "structural_confound",
            params.structural_confound_perceptual_similarity,
            params.structural_confound_root_coupling,
            2,
            false,
            true,
        ),
    )
    return rows
end

function initial_agent(params::Sim3Params, n_cues::Int)
    self_banks = Dict(
        1 => [params.d_self_helpless, params.d_self_resourced],
        2 => [params.d_self_helpless, params.d_self_resourced],
    )
    threat_banks = [[params.d_threat_dangerous, params.d_threat_safe] for _ in 1:n_cues]
    return AgentState(
        self_banks = self_banks,
        threat_banks = deepcopy(threat_banks),
        initial_threat_banks = deepcopy(threat_banks),
    )
end

function effective_precisions(params::Sim3Params, E_t::Float64)
    pi_part_eff = params.pi_part * exp(-params.beta_se * E_t)
    lambda_self_eff = params.lambda_self * exp(params.gamma_se * E_t)
    return pi_part_eff, lambda_self_eff
end

function infer_self(params::Sim3Params, prior_self, threat_prior, E_t::Float64; mode::Symbol)
    pi_part_eff, lambda_self_eff = effective_precisions(params, E_t)
    if mode != :self
        return copy(prior_self), pi_part_eff, lambda_self_eff
    end
    likelihood = [1.0 - params.self_truthfulness, params.self_truthfulness]
    ln_q = pi_part_eff .* log.(prior_self .+ eps(Float64)) .+
        lambda_self_eff .* log.(likelihood .+ eps(Float64))
    return softmax(ln_q), pi_part_eff, lambda_self_eff
end

function infer_threat_from_relational(
    params::Sim3Params,
    architecture::Symbol,
    prior_threat,
    q_self,
    cue::Cue,
    lambda_self_eff::Float64;
    mode::Symbol,
)
    if mode == :threat
        ln_q = log.(prior_threat .+ eps(Float64)) .+ lambda_self_eff .* [-1.0, 1.0]
        return softmax(ln_q)
    end
    architecture == :H2 && return copy(prior_threat)
    self_signal = q_self[SELF_RESOURCED] - q_self[SELF_HELPLESS]
    ln_q = log.(prior_threat .+ eps(Float64)) .+
        params.self_to_threat_coupling * cue.root_coupling * self_signal .* [-1.0, 1.0]
    return softmax(ln_q)
end

function infer_self_downstream_from_threat(params::Sim3Params, prior_self, q_threat)
    threat_signal = q_threat[THREAT_SAFE] - q_threat[THREAT_DANGEROUS]
    ln_q = log.(prior_self .+ eps(Float64)) .+
        params.h2_threat_to_self_coupling * threat_signal .* [-1.0, 1.0]
    return softmax(ln_q)
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
    ln_q = log.(q_threat .+ eps(Float64)) .+ params.outcome_precision .* log.(likelihood .+ eps(Float64))
    return softmax(ln_q)
end

function policy_probs(params::Sim3Params, q_self, q_threat; architecture::Symbol = :H1)
    self_signal = architecture == :H2 ? 0.0 : q_self[SELF_RESOURCED] - q_self[SELF_HELPLESS]
    threat_signal = q_threat[THREAT_SAFE] - q_threat[THREAT_DANGEROUS]
    contact_score =
        params.threat_policy_weight * threat_signal +
        params.contact_self_bias * self_signal +
        q_threat[THREAT_SAFE] * params.utility_contact_neutral +
        q_threat[THREAT_DANGEROUS] * params.utility_contact_harm
    avoid_score =
        -params.threat_policy_weight * threat_signal +
        params.avoid_bias * -self_signal +
        q_threat[THREAT_SAFE] * params.utility_avoid_neutral +
        q_threat[THREAT_DANGEROUS] * params.utility_avoid_harm
    return softmax(params.policy_precision .* [avoid_score, contact_score])
end

function update_banks!(state::AgentState, cue::Cue, q_self, q_threat, params::Sim3Params; learn_self::Bool, learn_threat::Bool)
    if learn_self
        state.self_banks[cue.root_id] .+= params.eta_self .* q_self
    end
    if learn_threat
        state.threat_banks[cue.id] .+= params.eta_threat .* q_threat
    end
    return nothing
end

function train_trial!(
    state::AgentState,
    cue::Cue,
    params::Sim3Params,
    seed::Int,
    condition::String,
    architecture::Symbol,
    E_t::Float64,
    trial::Int;
    learn_self::Bool,
    learn_threat::Bool,
    mode::Symbol = :self,
    actual_threat::Int = THREAT_SAFE,
)
    self_bank = state.self_banks[cue.root_id]
    threat_bank = state.threat_banks[cue.id]
    q_self_prior = normalize(self_bank)
    q_threat_prior = normalize(threat_bank)
    self_mode = architecture == :H2 ? :self : mode
    q_self_relational, pi_part_eff, lambda_self_eff = infer_self(params, q_self_prior, q_threat_prior, E_t; mode = self_mode)
    q_threat_after = infer_threat_from_relational(
        params,
        architecture,
        q_threat_prior,
        q_self_relational,
        cue,
        lambda_self_eff;
        mode = mode,
    )
    q_self_for_policy = architecture == :H2 ? infer_self_downstream_from_threat(params, q_self_relational, q_threat_after) : q_self_relational
    qpi = policy_probs(params, q_self_for_policy, q_threat_after; architecture = architecture)
    action = POLICY_CONTACT
    outcome = actual_threat == THREAT_SAFE ? :neutral : :harm
    predicted_neutral = sum(q_threat_after[i] * outcome_neutral_probability(params, action, i) for i in 1:2)
    log_evidence = log((outcome == :neutral ? predicted_neutral : 1.0 - predicted_neutral) + eps(Float64))
    q_threat_final = infer_threat_from_outcome(params, q_threat_after, action, outcome)
    q_self_after = architecture == :H2 ? infer_self_downstream_from_threat(params, q_self_relational, q_threat_final) : q_self_relational
    update_banks!(
        state,
        cue,
        q_self_after,
        q_threat_final,
        params;
        learn_self = learn_self,
        learn_threat = learn_threat,
    )
    return TrialRow(
        seed = seed,
        condition = condition,
        architecture = string(architecture),
        trial = trial,
        phase = "training",
        cue = cue.label,
        E_t = E_t,
        pi_part_eff = pi_part_eff,
        lambda_self_eff = lambda_self_eff,
        structural_self_precision = sum(self_bank),
        structural_threat_precision = sum(threat_bank),
        q_self_prior_resourced = q_self_prior[SELF_RESOURCED],
        q_self_after_resourced = q_self_after[SELF_RESOURCED],
        q_threat_prior_safe = q_threat_prior[THREAT_SAFE],
        q_threat_after_relational_safe = q_threat_after[THREAT_SAFE],
        q_threat_final_safe = q_threat_final[THREAT_SAFE],
        p_contact = qpi[POLICY_CONTACT],
        action = "contact",
        outcome = string(outcome),
    ), log_evidence
end

function probe_cue(state::AgentState, cue::Cue, params::Sim3Params, architecture::Symbol, E_t::Float64; mode::Symbol = :self)
    q_self_prior = normalize(state.self_banks[cue.root_id])
    q_threat_prior = normalize(state.threat_banks[cue.id])
    self_mode = architecture == :H2 ? :self : mode
    q_self_relational, pi_part_eff, lambda_self_eff = infer_self(params, q_self_prior, q_threat_prior, E_t; mode = self_mode)
    q_threat_after = infer_threat_from_relational(
        params,
        architecture,
        q_threat_prior,
        q_self_relational,
        cue,
        lambda_self_eff;
        mode = mode,
    )
    q_self_after = architecture == :H2 ? infer_self_downstream_from_threat(params, q_self_relational, q_threat_after) : q_self_relational
    qpi = policy_probs(params, q_self_after, q_threat_after; architecture = architecture)
    return (
        q_self_prior = q_self_prior,
        q_self_after = q_self_after,
        q_threat_prior = q_threat_prior,
        q_threat_after = q_threat_after,
        p_contact = qpi[POLICY_CONTACT],
        pi_part_eff = pi_part_eff,
        lambda_self_eff = lambda_self_eff,
    )
end

function first_passage(rows::Vector{TrialRow}, params::Sim3Params)
    self_time = nothing
    threat_time = nothing
    policy_time = nothing
    for row in rows
        base = 3.0 * (row.trial - 1)
        self_offset = row.architecture == "H2" ? 2.0 : 1.0
        threat_offset = row.architecture == "H2" ? 1.0 : 2.0
        if self_time === nothing && row.q_self_after_resourced >= params.first_passage_threshold
            self_time = base + self_offset
        end
        if threat_time === nothing && row.q_threat_after_relational_safe >= params.first_passage_threshold
            threat_time = base + threat_offset
        end
        if policy_time === nothing && row.p_contact >= params.policy_threshold
            policy_time = base + 3.0
        end
    end
    return self_time, threat_time, policy_time
end

function run_condition_seed(
    seed::Int,
    params::Sim3Params,
    cue_rows::Vector{Cue};
    condition::String,
    architecture::Symbol,
    E_t::Float64,
    learn_self::Bool,
    learn_threat::Bool,
    train_mode::Symbol = :self,
    probe_mode::Symbol = :self,
    train_cue_id::Int = 1,
)
    rng = MersenneTwister(seed)
    Random.seed!(rng, seed)
    state = initial_agent(params, length(cue_rows))
    train_cue = cue_rows[train_cue_id]
    rows = TrialRow[]
    log_evidence = 0.0
    for trial in 1:params.n_training_trials
        row, ll = train_trial!(
            state,
            train_cue,
            params,
            seed,
            condition,
            architecture,
            E_t,
            trial;
            learn_self = learn_self,
            learn_threat = learn_threat,
            mode = train_mode,
        )
        push!(rows, row)
        log_evidence += ll
    end
    probe_results = Dict(cue.label => probe_cue(state, cue, params, architecture, E_t; mode = probe_mode) for cue in cue_rows)
    trained_probe = probe_cue(state, train_cue, params, architecture, E_t; mode = train_mode)
    final_predicted_neutral = sum(
        trained_probe.q_threat_after[i] * outcome_neutral_probability(params, POLICY_CONTACT, i)
        for i in 1:2
    )
    fit_log_evidence = params.n_training_trials * log(final_predicted_neutral + eps(Float64))
    self_time, threat_time, policy_time = first_passage(rows, params)
    ordered = self_time !== nothing && threat_time !== nothing && policy_time !== nothing &&
        self_time < threat_time && threat_time < policy_time
    shifts = Float64[]
    for cue in cue_rows
        cue.trained && continue
        initial = normalize(state.initial_threat_banks[cue.id])
        final = normalize(state.threat_banks[cue.id])
        push!(shifts, sum(abs.(final .- initial)))
    end
    untrained = [probe_results[cue.label].p_contact for cue in cue_rows if !cue.trained && !cue.structural_confound]
    confound = only([probe_results[cue.label].p_contact for cue in cue_rows if cue.structural_confound])
    metric = SeedMetric(
        seed = seed,
        condition = condition,
        architecture = string(architecture),
        E_t = E_t,
        first_passage_self = self_time,
        first_passage_threat = threat_time,
        first_passage_policy = policy_time,
        ordered_cascade = ordered,
        training_log_evidence = fit_log_evidence,
        trained_cue_contact = probe_results[train_cue.label].p_contact,
        mean_untrained_contact = mean_or_zero(untrained),
        confound_contact = confound,
        max_untrained_threat_l1_shift = isempty(shifts) ? 0.0 : maximum(shifts),
        final_self_resourced = normalize(state.self_banks[train_cue.root_id])[SELF_RESOURCED],
        final_trained_threat_safe = normalize(state.threat_banks[train_cue.id])[THREAT_SAFE],
    )
    return metric, rows, probe_results, state
end

function summarize_condition(seed_metrics::Vector{SeedMetric}, probe_maps, cue_rows::Vector{Cue})
    cue_summaries = NamedTuple[]
    for cue in cue_rows
        values = [probes[cue.label].p_contact for probes in probe_maps]
        push!(cue_summaries, (
            cue = cue.label,
            perceptual_similarity = cue.perceptual_similarity,
            root_coupling = cue.root_coupling,
            root_id = cue.root_id,
            trained = cue.trained,
            structural_confound = cue.structural_confound,
            mean_contact = mean(values),
            ci95_contact = ci95(values),
        ))
    end
    return (
        n_seeds = length(seed_metrics),
        mean_training_log_evidence = mean(row.training_log_evidence for row in seed_metrics),
        ordered_cascade_rate = mean(row.ordered_cascade ? 1.0 : 0.0 for row in seed_metrics),
        mean_trained_cue_contact = mean(row.trained_cue_contact for row in seed_metrics),
        mean_untrained_contact = mean(row.mean_untrained_contact for row in seed_metrics),
        mean_confound_contact = mean(row.confound_contact for row in seed_metrics),
        max_untrained_threat_l1_shift = maximum(row.max_untrained_threat_l1_shift for row in seed_metrics),
        mean_final_self_resourced = mean(row.final_self_resourced for row in seed_metrics),
        mean_final_trained_threat_safe = mean(row.final_trained_threat_safe for row in seed_metrics),
        cues = cue_summaries,
    )
end

function continuum_values(condition_summary)
    rows = [row for row in condition_summary.cues if !row.trained && !row.structural_confound]
    sort!(rows; by = row -> -row.root_coupling)
    return [row.mean_contact for row in rows]
end

function continuum_slope(condition_summary)
    rows = [row for row in condition_summary.cues if !row.trained && !row.structural_confound]
    xs = [row.root_coupling for row in rows]
    ys = [row.mean_contact for row in rows]
    xbar = mean(xs)
    ybar = mean(ys)
    denom = sum((x - xbar)^2 for x in xs)
    denom <= eps(Float64) && return 0.0
    return sum((xs[i] - xbar) * (ys[i] - ybar) for i in eachindex(xs)) / denom
end

function monotone_decreasing_score(values)
    length(values) <= 1 && return 0.0
    good = sum(values[i] >= values[i + 1] - 1e-9 for i in 1:(length(values) - 1))
    return good / (length(values) - 1)
end

function readout_shape_score(E_values, transfer_values, params::Sim3Params)
    length(transfer_values) < 5 && return 0.0
    monotone = sum(transfer_values[i + 1] >= transfer_values[i] - 1e-9 for i in 1:(length(transfer_values) - 1)) /
        (length(transfer_values) - 1)
    total_range = maximum(transfer_values) - minimum(transfer_values)
    range_score = min(1.0, total_range / params.readout_min_range)
    increments = diff(transfer_values)
    peak_ix = argmax(increments)
    interior_score = peak_ix in 2:(length(increments) - 1) ? 1.0 : 0.0
    edge_mean = mean([increments[1], increments[end]])
    peak_score = maximum(increments) > edge_mean ? 1.0 : 0.0
    return mean([monotone, range_score, interior_score, peak_score])
end

function real_danger_avoidance(seed::Int, params::Sim3Params, cue_rows::Vector{Cue})
    metric, _, _, state = run_condition_seed(
        seed,
        params,
        cue_rows;
        condition = "H1-witnessing-real-danger-pretrain",
        architecture = :H1,
        E_t = params.high_E,
        learn_self = true,
        learn_threat = true,
    )
    probe = probe_cue(state, cue_rows[2], params, :H1, params.high_E)
    q_after_harm = infer_threat_from_outcome(params, probe.q_threat_after, POLICY_CONTACT, :harm)
    qpi = policy_probs(params, probe.q_self_after, q_after_harm)
    return qpi[POLICY_AVOID]
end

function run_named_condition(seeds, params, cue_rows; kwargs...)
    metrics = SeedMetric[]
    traces = TrialRow[]
    probes = Any[]
    for seed in seeds
        metric, rows, probe_map, _ = run_condition_seed(seed, params, cue_rows; kwargs...)
        push!(metrics, metric)
        append!(traces, rows)
        push!(probes, probe_map)
    end
    return metrics, traces, probes, summarize_condition(metrics, probes, cue_rows)
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
    function points(rows, yoff)
        vals = [row.mean_contact for row in rows if !row.structural_confound]
        roots = [row.root_coupling for row in rows if !row.structural_confound]
        coords = String[]
        for i in eachindex(vals)
            x = 70 + (1.0 - roots[i]) * 420
            y = yoff - vals[i] * 180
            push!(coords, "$(round(x, digits=1)),$(round(y, digits=1))")
        end
        return join(coords, " ")
    end
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">
      <rect width="640" height="360" fill="#fbfaf7"/>
      <line x1="70" y1="300" x2="520" y2="300" stroke="#222" stroke-width="2"/>
      <line x1="70" y1="70" x2="70" y2="300" stroke="#222" stroke-width="2"/>
      <text x="70" y="38" font-family="Arial" font-size="18" fill="#222">Sim 3 transfer gradient</text>
      <text x="230" y="338" font-family="Arial" font-size="13" fill="#444">decreasing root coupling</text>
      <text x="18" y="225" font-family="Arial" font-size="13" fill="#444" transform="rotate(-90 18 225)">P(contact)</text>
      <polyline points="$(points(h1, 300))" fill="none" stroke="#8f3f2d" stroke-width="4"/>
      <polyline points="$(points(exposure, 300))" fill="none" stroke="#3f6f92" stroke-width="4"/>
      <polyline points="$(points(h2, 300))" fill="none" stroke="#557a46" stroke-width="4"/>
      <text x="535" y="110" font-family="Arial" font-size="12" fill="#8f3f2d">H1 witnessing</text>
      <text x="535" y="135" font-family="Arial" font-size="12" fill="#3f6f92">exposure</text>
      <text x="535" y="160" font-family="Arial" font-size="12" fill="#557a46">H2</text>
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

    h1_metrics, h1_traces, h1_probes, h1_summary = run_named_condition(
        config.seeds,
        params,
        cue_rows;
        condition = "H1-witnessing",
        architecture = :H1,
        E_t = params.high_E,
        learn_self = true,
        learn_threat = true,
    )
    h2_metrics, h2_traces, h2_probes, h2_summary = run_named_condition(
        config.seeds,
        params,
        cue_rows;
        condition = "H2-witnessing",
        architecture = :H2,
        E_t = params.high_E,
        learn_self = true,
        learn_threat = true,
        train_mode = :threat,
        probe_mode = :self,
    )
    parity_diff = abs(h1_summary.mean_training_log_evidence - h2_summary.mean_training_log_evidence) / params.n_training_trials
    if parity_diff > params.training_parity_epsilon
        error("Sim 3 training parity stop: H1/H2 treated-cue log-evidence diff $(parity_diff) exceeds epsilon $(params.training_parity_epsilon)")
    end

    exposure_metrics, exposure_traces, exposure_probes, exposure_summary = run_named_condition(
        config.seeds,
        params,
        cue_rows;
        condition = "H1-exposure",
        architecture = :H1,
        E_t = params.low_E,
        learn_self = true,
        learn_threat = true,
    )
    eta_self0 = Sim3Params(; eta_self = 0.0)
    self0_metrics, _, self0_probes, self0_summary = run_named_condition(
        config.seeds,
        eta_self0,
        cue_rows;
        condition = "H1-witnessing-eta-self-0",
        architecture = :H1,
        E_t = eta_self0.high_E,
        learn_self = true,
        learn_threat = true,
    )
    eta_threat0 = Sim3Params(; eta_threat = 0.0)
    threat0_metrics, _, threat0_probes, threat0_summary = run_named_condition(
        config.seeds,
        eta_threat0,
        cue_rows;
        condition = "H1-witnessing-eta-threat-0",
        architecture = :H1,
        E_t = eta_threat0.high_E,
        learn_self = true,
        learn_threat = true,
    )
    fake_metrics, _, fake_probes, fake_summary = run_named_condition(
        config.seeds,
        params,
        cue_rows;
        condition = "H1-witnessing-fake-content",
        architecture = :H1,
        E_t = params.high_E,
        learn_self = true,
        learn_threat = true,
        train_mode = :threat,
        probe_mode = :self,
    )
    counter_metrics, _, counter_probes, counter_summary = run_named_condition(
        config.seeds,
        params,
        cue_rows;
        condition = "H1-witnessing-counterbalanced",
        architecture = :H1,
        E_t = params.high_E,
        learn_self = true,
        learn_threat = true,
        train_cue_id = 2,
    )

    sweep_values = Float64[]
    for E in params.e_sweep
        _, _, _, sweep_summary = run_named_condition(
            config.seeds,
            params,
            cue_rows;
            condition = "H1-E-sweep",
            architecture = :H1,
            E_t = E,
            learn_self = true,
            learn_threat = true,
        )
        push!(sweep_values, sweep_summary.mean_untrained_contact - exposure_summary.mean_untrained_contact)
    end

    sensitivity_support = Float64[]
    for variant in (
        Sim3Params(; eta_self = params.eta_self * 0.8),
        Sim3Params(; eta_self = params.eta_self * 1.2),
        Sim3Params(; pi_part = params.pi_part * 0.8),
        Sim3Params(; pi_part = params.pi_part * 1.2),
        Sim3Params(; lambda_self = params.lambda_self * 0.8),
        Sim3Params(; lambda_self = params.lambda_self * 1.2),
    )
        _, _, _, variant_summary = run_named_condition(
            config.seeds,
            variant,
            cues(variant);
            condition = "H1-witnessing-sensitivity",
            architecture = :H1,
            E_t = variant.high_E,
            learn_self = true,
            learn_threat = true,
        )
        push!(sensitivity_support, variant_summary.mean_untrained_contact - exposure_summary.mean_untrained_contact >= 0.12 ? 1.0 : 0.0)
    end

    h1_values = continuum_values(h1_summary)
    exposure_values = continuum_values(exposure_summary)
    h2_values = continuum_values(h2_summary)
    structural_contrast = begin
        candidates = [row for row in h1_summary.cues if !row.trained && !row.structural_confound && row.root_coupling > 0.0]
        isempty(candidates) && error("Sim 3 A3.2 requires a root-sharing structural contrast cue")
        sort!(candidates; by = row -> (abs(row.perceptual_similarity - 0.2), abs(row.root_coupling - 0.6)))
        first(candidates)
    end
    confound_gap = structural_contrast.mean_contact - h1_summary.mean_confound_contact
    h1_transfer_gap = h1_summary.mean_untrained_contact - exposure_summary.mean_untrained_contact
    h2_transfer_gap = h1_summary.mean_untrained_contact - h2_summary.mean_untrained_contact
    self0_drop = h1_summary.mean_untrained_contact - self0_summary.mean_untrained_contact
    threat0_ratio = threat0_summary.mean_untrained_contact / max(h1_summary.mean_untrained_contact, eps(Float64))
    fake_drop = h1_summary.mean_untrained_contact - fake_summary.mean_untrained_contact
    counter_gap = counter_summary.mean_untrained_contact - exposure_summary.mean_untrained_contact
    real_danger = mean(real_danger_avoidance(seed, params, cue_rows) for seed in config.seeds)

    summary_by_condition = Dict(
        "H1-witnessing" => h1_summary,
        "H1-exposure" => exposure_summary,
        "H2-witnessing" => h2_summary,
        "H1-witnessing-eta-self-0" => self0_summary,
        "H1-witnessing-eta-threat-0" => threat0_summary,
        "H1-witnessing-fake-content" => fake_summary,
        "H1-witnessing-counterbalanced" => counter_summary,
    )

    metrics = (
        training_parity = (
            abs_log_evidence_diff = parity_diff,
            epsilon = params.training_parity_epsilon,
        ),
        cascade = (
            witnessing_order_rate = h1_summary.ordered_cascade_rate,
            exposure_order_rate = exposure_summary.ordered_cascade_rate,
        ),
        transfer = (
            h1_witnessing_mean = h1_summary.mean_untrained_contact,
            exposure_mean = exposure_summary.mean_untrained_contact,
            h2_mean = h2_summary.mean_untrained_contact,
            h1_witnessing_minus_exposure_mean = h1_transfer_gap,
            h1_witnessing_minus_h2_mean = h2_transfer_gap,
            h1_witnessing_monotone_gradient = monotone_decreasing_score(h1_values),
            exposure_abs_slope = abs(continuum_slope(exposure_summary)),
            h2_abs_slope = abs(continuum_slope(h2_summary)),
        ),
        leakage = (
            max_untrained_threat_l1_shift = maximum([
                h1_summary.max_untrained_threat_l1_shift,
                exposure_summary.max_untrained_threat_l1_shift,
                h2_summary.max_untrained_threat_l1_shift,
            ]),
        ),
        ablations = (
            eta_self_zero_transfer_drop = self0_drop,
            eta_threat_zero_transfer_ratio = threat0_ratio,
        ),
        e_t_readout = (
            E_values = params.e_sweep,
            transfer_values = sweep_values,
            shape_score = readout_shape_score(params.e_sweep, sweep_values, params),
        ),
        adversarial = (
            fake_content_transfer_drop = fake_drop,
            counterbalanced_transfer_gap = counter_gap,
            real_danger_avoidance = real_danger,
            sensitivity_support_rate = mean(sensitivity_support),
            training_trajectory_gap = abs(mean(row.p_contact for row in h1_traces) - mean(row.p_contact for row in h2_traces)),
            structural_confound_gap = confound_gap,
        ),
    )

    all_seed_metrics = vcat(h1_metrics, exposure_metrics, h2_metrics, self0_metrics, threat0_metrics, fake_metrics, counter_metrics)
    all_traces = vcat(h1_traces, exposure_traces, h2_traces)
    summary = (
        experiment = config.experiment,
        config = config_snapshot(config),
        design = (
            cues = [(
                label = cue.label,
                perceptual_similarity = cue.perceptual_similarity,
                root_coupling = cue.root_coupling,
                root_id = cue.root_id,
                trained = cue.trained,
                structural_confound = cue.structural_confound,
            ) for cue in cue_rows],
            h2_architecture = "threat root; self-state bank updates downstream from inferred threat and relational evidence; policy ignores self-state",
            perceptual_generalization_channel = "none; exposure has no added stimulus-generalization channel in this preregistered run",
            relational_modality = (always_on = true, always_truthful = true, weight_varies_by = "D1 effective-precision balance"),
            structural_precision_logged_separately = true,
            effective_precision_logged_separately = true,
        ),
        conditions = summary_by_condition,
        metrics = metrics,
        per_seed_metric_count = length(all_seed_metrics),
        trace_row_count = length(all_traces),
    )
    write_json(joinpath(outdir, "summary.json"), summary)
    write_rows_csv(joinpath(outdir, "per_seed_metrics.csv"), all_seed_metrics)
    write_rows_csv(joinpath(outdir, "posterior_traces.csv"), all_traces)
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
        extra = (output_dir = abspath(outdir),)
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
