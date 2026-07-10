module Sim4

using Dates
using Random
using Statistics
using YAML

using ...Config: ExperimentConfig, config_snapshot
using ...Criteria: write_criteria_results
using ...IO: ensure_dir, write_json, write_rows_csv
using ...Reproducibility: build_reproducibility_metadata
using ...Sim1

export run_sim4_config

const EPS = 1e-12
const MET_WELL = 1
const MET_BADLY = 2
const CATASTROPHIC = 3
const HOLD_ACCESS = 1
const ALLOW_ACCESS = 2
const RAPID_ACTION = 3
const POLICY_NAMES = ["hold_access", "allow_access", "rapid_action"]

Base.@kwdef struct DevelopmentEpisode
    omega::Float64
    kappa::Float64
    acute_trials::Int
    consolidation_trials::Int
end

Base.@kwdef struct ReadoutThresholds
    written_reflexivity_max_exile::Float64 = 0.35
    catastrophic_belief_min_exile::Float64 = 0.25
    manager_structural_precision_min::Float64 = 120.0
    firefighter_dominant_policies::Vector{String} = ["flee", "attenuate"]
end

Base.@kwdef struct Sim4Params
    developmental_schedule::Vector{DevelopmentEpisode} = [
        DevelopmentEpisode(3.0, 0.0, 72, 128),
        DevelopmentEpisode(2.6, 0.2, 64, 64),
        DevelopmentEpisode(1.4, 0.9, 64, 32),
        DevelopmentEpisode(2.0, 0.7, 64, 64),
    ]
    therapy_sessions::Int = 96
    high_E::Float64 = 0.90
    low_E::Float64 = 0.05
    pi_part::Float64 = 4.0
    beta_se::Float64 = 1.0
    lambda_ctx::Float64 = 1.0
    gamma_se::Float64 = 1.2
    permission_trust_threshold::Float64 = 0.72
    relational_prior_count::Float64 = 1.0
    relational_prior_jitter::Float64 = 0.25
    contact_write_size::Float64 = 0.25
    contact_write_size_sweep::Vector{Float64} = [0.25, 0.5, 1.0, 2.0, 4.0]
    breach_probability::Float64 = 0.08
    policy_learning_rate::Float64 = 0.45
    efe_utility_good::Float64 = 2.2
    efe_utility_bad::Float64 = -1.15
    efe_utility_catastrophic::Float64 = -4.8
    efe_information_weight::Float64 = 5.0
    efe_settled_cost::Float64 = 1.05
end

"""A Sim 1-grown cause plus Sim 4 readout banks; no constructor is used to author a cause."""
mutable struct LayerCause
    id::Int
    formation::Dict{String, Any}
    blocking_strengths::Dict{Int, Float64}
    relational_counts::Vector{Float64}
    policy_counts::Vector{Float64}
    mandate_counts::Vector{Float64}
    root_revision::Float64
    written_reflexivity::Float64
    structural_precision::Float64
    dominant_policy::String
    catastrophic_belief::Float64
    authored::Bool
end

as_string_dict(value) = Dict{String, Any}(string(k) => v for (k, v) in value)
get_float(raw, key::String, default::Float64) = haskey(raw, key) ? Float64(raw[key]) : default
get_int(raw, key::String, default::Int) = haskey(raw, key) ? Int(raw[key]) : default

function parse_schedule(raw, default)
    haskey(raw, "developmental_schedule") || return default
    return [begin
        row = as_string_dict(item)
        DevelopmentEpisode(
            Float64(row["omega"]),
            Float64(row["kappa"]),
            Int(row["acute_trials"]),
            Int(row["consolidation_trials"]),
        )
    end for item in raw["developmental_schedule"]]
end

function params_from_config(config::ExperimentConfig)
    raw = config.model_params
    base = Sim4Params()
    return Sim4Params(
        developmental_schedule = parse_schedule(raw, base.developmental_schedule),
        therapy_sessions = get_int(raw, "therapy_sessions", base.therapy_sessions),
        high_E = get_float(raw, "high_E", base.high_E),
        low_E = get_float(raw, "low_E", base.low_E),
        pi_part = get_float(raw, "pi_part", base.pi_part),
        beta_se = get_float(raw, "beta_se", base.beta_se),
        lambda_ctx = get_float(raw, "lambda_ctx", base.lambda_ctx),
        gamma_se = get_float(raw, "gamma_se", base.gamma_se),
        permission_trust_threshold = get_float(raw, "permission_trust_threshold", base.permission_trust_threshold),
        relational_prior_count = get_float(raw, "relational_prior_count", base.relational_prior_count),
        relational_prior_jitter = get_float(raw, "relational_prior_jitter", base.relational_prior_jitter),
        contact_write_size = get_float(raw, "contact_write_size", base.contact_write_size),
        contact_write_size_sweep = haskey(raw, "contact_write_size_sweep") ? Float64.(raw["contact_write_size_sweep"]) : base.contact_write_size_sweep,
        breach_probability = get_float(raw, "breach_probability", base.breach_probability),
        policy_learning_rate = get_float(raw, "policy_learning_rate", base.policy_learning_rate),
        efe_utility_good = get_float(raw, "efe_utility_good", base.efe_utility_good),
        efe_utility_bad = get_float(raw, "efe_utility_bad", base.efe_utility_bad),
        efe_utility_catastrophic = get_float(raw, "efe_utility_catastrophic", base.efe_utility_catastrophic),
        efe_information_weight = get_float(raw, "efe_information_weight", base.efe_information_weight),
        efe_settled_cost = get_float(raw, "efe_settled_cost", base.efe_settled_cost),
    )
end

function readout_thresholds(path::Union{Nothing, AbstractString})
    path === nothing && return ReadoutThresholds()
    raw = as_string_dict(YAML.load_file(path))
    haskey(raw, "readout_classifier") || error("Sim 4 criteria must preregister readout_classifier thresholds")
    cls = as_string_dict(raw["readout_classifier"])
    return ReadoutThresholds(
        written_reflexivity_max_exile = Float64(cls["written_reflexivity_max_exile"]),
        catastrophic_belief_min_exile = Float64(cls["catastrophic_belief_min_exile"]),
        manager_structural_precision_min = Float64(cls["manager_structural_precision_min"]),
        firefighter_dominant_policies = String.(cls["firefighter_dominant_policies"]),
    )
end

normalize(v::AbstractVector{Float64}) = v ./ max(sum(v), EPS)
entropy(p::AbstractVector{Float64}) = -sum(x -> x * log(x + EPS), p)
trust(cause::LayerCause) = cause.relational_counts[MET_WELL] / max(sum(cause.relational_counts), EPS)

function effective_precisions(params::Sim4Params, E_t::Float64)
    pi_eff = params.pi_part * exp(-params.beta_se * E_t)
    lambda_eff = params.lambda_ctx * exp(params.gamma_se * E_t)
    return pi_eff, lambda_eff, pi_eff / (pi_eff + lambda_eff)
end

function relational_weight(params::Sim4Params, E_t::Float64)
    pi_eff, lambda_eff, _ = effective_precisions(params, E_t)
    hi_pi, hi_lambda, _ = effective_precisions(params, params.high_E)
    share = lambda_eff / (pi_eff + lambda_eff)
    high_share = hi_lambda / (hi_pi + hi_lambda)
    return min(1.0, share / max(high_share, EPS))
end

function copy_cause(cause::LayerCause)
    return LayerCause(
        cause.id,
        Dict{String, Any}(cause.formation),
        copy(cause.blocking_strengths),
        copy(cause.relational_counts),
        copy(cause.policy_counts),
        copy(cause.mandate_counts),
        cause.root_revision,
        cause.written_reflexivity,
        cause.structural_precision,
        cause.dominant_policy,
        cause.catastrophic_belief,
        cause.authored,
    )
end

function classify_readout(cause::LayerCause, thresholds::ReadoutThresholds)
    if cause.written_reflexivity <= thresholds.written_reflexivity_max_exile &&
            cause.catastrophic_belief >= thresholds.catastrophic_belief_min_exile
        return "exile_readout"
    elseif cause.structural_precision >= thresholds.manager_structural_precision_min
        return "manager_readout"
    elseif cause.dominant_policy in thresholds.firefighter_dominant_policies
        return "firefighter_readout"
    end
    return "unclassified_readout"
end

readout_label(cause::LayerCause) = string(get(cause.formation, "readout_label", "unclassified_readout"))

function sim1_policy_readout(cause)
    idx = argmax(cause.policy_counts)
    return Sim1.POLICY_NAMES[idx]
end

function therapy_policy_counts(cause)
    mapped = [
        cause.policy_counts[Sim1.FLEE] + cause.policy_counts[Sim1.APPEASE],
        cause.policy_counts[Sim1.APPROACH],
        cause.policy_counts[Sim1.ATTENUATE],
    ]
    return normalize(Float64.(mapped))
end

function protective_policy_mass(cause)
    p = normalize(Float64.(cause.policy_counts))
    return p[Sim1.FLEE] + p[Sim1.APPEASE] + p[Sim1.ATTENUATE]
end

function randomized_forecast(rng::AbstractRNG, params::Sim4Params)
    base = params.relational_prior_count
    jitter = params.relational_prior_jitter
    return [base * (1.0 + jitter * (2.0 * rand(rng) - 1.0)) for _ in 1:3]
end

function development_rows(seed::Int, params::Sim4Params)
    sim1_params = Sim1.sim1_params(Dict{String, Any}())
    evidence_rng = MersenneTwister(seed)
    action_rng = MersenneTwister(seed + 1_000_003)
    agent = Sim1.init_agent()
    world = Sim1.WorldState(0, 0, 0, false)
    history = NamedTuple[]
    events = Dict{Int, NamedTuple}()
    events[1] = (
        seed = seed,
        trial = 0,
        cause_id = 1,
        route = string(get(agent.causes[1].formation, "route", "initial_cause")),
        spawned = false,
        origin_episode = 0,
        origin_epoch = "initial",
        formation_event_id = "sim1-$seed-initial-1",
        sim1_pathway = "Sim1.init_agent",
        arousal = 0.0,
        structural_write = Sim1.structural_precision(agent.causes[1]),
        posterior_predictive = 1.0,
    )

    trial = 0
    for (episode_idx, episode) in enumerate(params.developmental_schedule)
        for (epoch, n_trials, catastrophes) in (
            ("acute", episode.acute_trials, true),
            ("consolidation", episode.consolidation_trials, false),
        )
            for epoch_trial in 1:n_trials
                trial += 1
                potential = Sim1.sample_evidence(evidence_rng, episode.omega, sim1_params; catastrophes)
                active_cause_id = Sim1.dominant_aversive_cause(agent).id
                log = Sim1.run_trial!(
                    action_rng,
                    agent,
                    world,
                    potential,
                    episode.kappa,
                    sim1_params,
                    trial,
                    seed;
                    arm = :closed_loop,
                    allow_spawn = true,
                )
                if log.spawned
                    cause = agent.causes[log.cause_id]
                    event_id = "sim1-$seed-spawn-$(log.trial)-$(log.cause_id)"
                    cause.formation["origin_episode"] = episode_idx
                    cause.formation["origin_epoch"] = epoch
                    cause.formation["formation_event_id"] = event_id
                    cause.formation["sim1_pathway"] = "Sim1.run_trial!/spawn_cause!"
                    events[cause.id] = (
                        seed = seed,
                        trial = log.trial,
                        cause_id = cause.id,
                        route = string(get(cause.formation, "route", "acute_spawn")),
                        spawned = true,
                        origin_episode = episode_idx,
                        origin_epoch = epoch,
                        formation_event_id = event_id,
                        sim1_pathway = "Sim1.run_trial!/spawn_cause!",
                        arousal = log.arousal,
                        structural_write = log.learning_rate,
                        posterior_predictive = log.posterior_predictive,
                    )
                end
                push!(history, (
                    seed = seed,
                    trial = trial,
                    episode = episode_idx,
                    epoch = epoch,
                    epoch_trial = epoch_trial,
                    omega = episode.omega,
                    kappa = episode.kappa,
                    active_cause_id = active_cause_id,
                    cause_id = log.cause_id,
                    spawned = log.spawned,
                    policy = log.policy,
                    evidence_outcome = log.evidence_outcome,
                    evidence_severity = log.evidence_severity,
                    posterior_predictive = log.posterior_predictive,
                    spawn_pressure = log.spawn_pressure,
                    arousal = log.arousal,
                    reflexivity = log.reflexivity,
                    learning_rate = log.learning_rate,
                    cue_write_mass = sim1_params.cue_learning_weight * log.learning_rate,
                    affect_write_mass = log.learning_rate,
                    cue_affect_write_mass = (1.0 + sim1_params.cue_learning_weight) * log.learning_rate,
                ))
            end
        end
    end
    return agent, history, events
end

function grown_blocking_strengths(source, history, cause_ids)
    source_writes = [row for row in history if row.cause_id == source.id]
    total_write_mass = sum(row.cue_affect_write_mass for row in source_writes)
    policy_mass = protective_policy_mass(source)
    coupled_write_mass = Dict{Int, Float64}()
    strengths = Dict{Int, Float64}()
    for target_id in cause_ids
        mass = 0.0
        if target_id != source.id
            for row in source_writes
                row.active_cause_id == target_id && (mass += row.cue_affect_write_mass)
            end
        end
        coupled_write_mass[target_id] = mass
        strengths[target_id] = policy_mass * mass / max(total_write_mass, EPS)
    end
    return strengths, coupled_write_mass, total_write_mass, policy_mass
end

"""
Run one neutral biography through Sim 1's actual state, policy, spawn-pressure,
spawn, and bank-update pathways. Sim 4 only wraps the returned population.
"""
function grow_stack_with_history(seed::Int, params::Sim4Params, thresholds::ReadoutThresholds)
    agent, history, events = development_rows(seed, params)
    forecast_rng = MersenneTwister(seed + 4_000_009)
    cause_ids = [source.id for source in agent.causes]
    causes = LayerCause[]
    for source in agent.causes
        haskey(events, source.id) || error("Sim 1 cause $(source.id) lacks a formation event for seed $seed")
        cause_history = [row for row in history if row.cause_id == source.id]
        event = events[source.id]
        first_write = isempty(cause_history) ? event.trial : first(cause_history).trial
        last_write = isempty(cause_history) ? event.trial : last(cause_history).trial
        formation = Dict{String, Any}(source.formation)
        formation["route"] = event.route
        formation["spawned"] = event.spawned
        formation["origin_episode"] = event.origin_episode
        formation["origin_epoch"] = event.origin_epoch
        formation["formation_event_id"] = event.formation_event_id
        formation["sim1_pathway"] = event.sim1_pathway
        formation["formation_duration"] = max(1, last_write - first_write + 1)
        formation["max_arousal"] = isempty(cause_history) ? event.arousal : maximum(row.arousal for row in cause_history)
        formation["slow_accumulation"] = formation["formation_duration"] > maximum(ep.acute_trials for ep in params.developmental_schedule)
        formation["position_index"] = source.id # measured formation order; never read by the classifier or EFE

        reflexivity = Sim1.written_reflexivity(source)
        precision = Sim1.structural_precision(source)
        dominant = sim1_policy_readout(source)
        catastrophic = source.severity_counts[2] / max(sum(source.severity_counts), EPS)
        blocking_strengths, coupled_write_mass, total_write_mass, policy_mass =
            grown_blocking_strengths(source, history, cause_ids)
        layer = LayerCause(
            source.id,
            formation,
            blocking_strengths,
            randomized_forecast(forecast_rng, params),
            therapy_policy_counts(source),
            copy(source.severity_counts),
            0.0,
            reflexivity,
            precision,
            dominant,
            catastrophic,
            false,
        )
        layer.formation["protective_policy_mass"] = policy_mass
        layer.formation["cue_affect_total_write_mass"] = total_write_mass
        layer.formation["blocking_write_mass_by_target"] = Dict(string(k) => v for (k, v) in coupled_write_mass)
        layer.formation["blocking_strength_by_target"] = Dict(string(k) => v for (k, v) in blocking_strengths)
        layer.formation["initial_relational_counts"] = copy(layer.relational_counts)
        layer.formation["readout_label"] = classify_readout(layer, thresholds)
        push!(causes, layer)
    end
    formation_rows = [events[id] for id in sort(collect(keys(events)))]
    return causes, formation_rows, history
end

# Compatibility with Sim 7's existing read-only dependency.
function grow_stack(seed::Int, params::Sim4Params)
    causes, events, _ = grow_stack_with_history(seed, params, ReadoutThresholds())
    return causes, events
end

function active_policy(cause::LayerCause, params::Sim4Params)
    trust(cause) >= params.permission_trust_threshold && return ALLOW_ACCESS
    return argmax(cause.policy_counts)
end

function cause_by_id(causes::Vector{LayerCause}, target_id::Int)
    idx = findfirst(cause -> cause.id == target_id, causes)
    idx === nothing && error("Unknown Sim 4 cause id $target_id")
    return causes[idx]
end

function access_fraction(causes::Vector{LayerCause}, target_id::Int, params::Sim4Params)
    target = cause_by_id(causes, target_id)
    pair_access = map(causes) do blocker
        strength = get(blocker.blocking_strengths, target.id, 0.0)
        permission = active_policy(blocker, params) == ALLOW_ACCESS ? 1.0 :
            clamp(trust(blocker) / params.permission_trust_threshold, 0.0, 1.0)
        return clamp(1.0 - strength * (1.0 - permission), 0.0, 1.0)
    end
    return isempty(pair_access) ? 1.0 : minimum(pair_access)
end

function relational_forecast(cause::LayerCause; relational_enabled::Bool = true)
    return relational_enabled ? copy(cause.relational_counts) : ones(Float64, 3)
end

function score_contact(causes::Vector{LayerCause}, target_id::Int, params::Sim4Params; relational_enabled::Bool = true)
    cause = cause_by_id(causes, target_id)
    counts = relational_forecast(cause; relational_enabled)
    p = normalize(counts)
    access = access_fraction(causes, target_id, params)
    effective = [access * p[MET_WELL], access * p[MET_BADLY], (1.0 - access) + access * p[CATASTROPHIC]]
    expected_outcome = params.efe_utility_good * effective[MET_WELL] +
        params.efe_utility_bad * effective[MET_BADLY] +
        params.efe_utility_catastrophic * effective[CATASTROPHIC]
    settled = trust(cause) >= params.permission_trust_threshold
    information_gain = settled ? 0.0 : access * params.efe_information_weight * entropy(p) / sqrt(sum(counts))
    settled_cost = settled ? params.efe_settled_cost * sqrt(sum(counts)) : 0.0
    return (
        target_id = target_id,
        expected_outcome = expected_outcome,
        information_gain = information_gain,
        settled_forecast_cost = settled_cost,
        computed_access = access,
        total = expected_outcome + information_gain - settled_cost,
        forecast_met_well = p[MET_WELL],
        forecast_met_badly = p[MET_BADLY],
        forecast_catastrophic = p[CATASTROPHIC],
    )
end

function choose_contact(causes::Vector{LayerCause}, params::Sim4Params; relational_enabled::Bool = true, rng::AbstractRNG = MersenneTwister(1))
    scores = [score_contact(causes, cause.id, params; relational_enabled) for cause in causes]
    totals = [row.total for row in scores]
    best = maximum(totals)
    tied = findall(x -> abs(x - best) <= 1e-9, totals)
    selected = scores[tied[rand(rng, eachindex(tied))]]
    return selected.target_id, scores
end

function contact_outcome(seed::Int, session::Int, target_id::Int)
    rng = MersenneTwister(seed + 10_007 * session + 101 * target_id)
    return rand(rng) < Sim4Params().breach_probability ? "met-badly" : "met-well"
end

function update_contact!(cause::LayerCause, outcome::String, params::Sim4Params, E_t::Float64; write_size::Float64 = params.contact_write_size)
    weight = relational_weight(params, E_t)
    write = weight * write_size
    before = trust(cause)
    if outcome == "met-well"
        cause.relational_counts[MET_WELL] += write
        cause.policy_counts[ALLOW_ACCESS] += params.policy_learning_rate * write
    elseif outcome == "met-badly"
        cause.relational_counts[MET_BADLY] += write
        cause.policy_counts[HOLD_ACCESS] += params.policy_learning_rate * write
    elseif outcome == "catastrophic"
        cause.relational_counts[CATASTROPHIC] += write
        cause.policy_counts[RAPID_ACTION] += params.policy_learning_rate * write
        cause.mandate_counts[2] += write
    end
    return before, trust(cause), weight
end

function maybe_revise_inner!(cause::LayerCause, contacted::Bool)
    contacted || return 0.0
    before = cause.root_revision
    cause.root_revision = min(1.0, cause.root_revision + 0.35)
    return cause.root_revision - before
end

function permute_forecasts!(causes::Vector{LayerCause}, seed::Int)
    permutation = collect(eachindex(causes))
    Random.shuffle!(MersenneTwister(seed + 8_000_021), permutation)
    original = [copy(cause.relational_counts) for cause in causes]
    for (target, source) in enumerate(permutation)
        causes[target].relational_counts .= original[source]
    end
    return permutation
end

function permute_blocking_strengths!(causes::Vector{LayerCause}, seed::Int)
    pairs = [(blocker, target.id) for blocker in causes for target in causes if blocker !== target]
    permutation = collect(eachindex(pairs))
    Random.shuffle!(MersenneTwister(seed + 9_000_031), permutation)
    original = [get(blocker.blocking_strengths, target_id, 0.0) for (blocker, target_id) in pairs]
    for (destination, source) in enumerate(permutation)
        blocker, target_id = pairs[destination]
        blocker.blocking_strengths[target_id] = original[source]
    end
    return permutation
end

function complete_outside_in(first_contacts::Dict{Int, Int}, causes)
    order = sort([cause.id for cause in causes]; rev = true)
    sessions = [get(first_contacts, id, 0) for id in order]
    return length(order) >= 2 && all(>(0), sessions) && all(diff(sessions) .> 0), order, sessions
end

function simulate_descent(seed::Int, params::Sim4Params, thresholds::ReadoutThresholds;
                          forecast_mode::Symbol = :baseline, history_mode::Symbol = :baseline,
                          write_size::Float64 = params.contact_write_size,
                          keep_history::Bool = true)
    choice_rng = MersenneTwister(seed + 41)
    outcome_rng = MersenneTwister(seed + 2_000_033)
    causes, formation_rows, history = grow_stack_with_history(seed, params, thresholds)
    forecast_permutation = forecast_mode == :permuted ? permute_forecasts!(causes, seed) : collect(eachindex(causes))
    history_permutation = history_mode == :permuted ? permute_blocking_strengths!(causes, seed) : Int[]
    condition = history_mode == :permuted ? "history-shuffled" : string(forecast_mode)
    rows = NamedTuple[]
    choices = Int[]
    first_contacts = Dict{Int, Int}()
    permission_sessions = Dict{Int, Int}()
    last_repair_gain = Dict{Int, Float64}()
    rupture_ratios = Float64[]
    policy_write_events = 0
    mandate_write_events = 0
    policy_write_mass = 0.0
    mandate_write_mass = 0.0

    for session in 1:params.therapy_sessions
        selected, scores = choose_contact(causes, params; relational_enabled = true, rng = choice_rng)
        push!(choices, selected)
        access = access_fraction(causes, selected, params)
        selected_cause = cause_by_id(causes, selected)
        score_row = only(row for row in scores if row.target_id == selected)
        pre_policy = copy(selected_cause.policy_counts)
        pre_mandate = copy(selected_cause.mandate_counts)
        trust_before = trust(selected_cause)
        trust_after = trust_before
        outcome_draw = rand(outcome_rng)
        outcome = "blocked"
        relational_write = 0.0
        rupture_ratio = nothing

        if access >= 1.0 - 1e-9
            outcome = outcome_draw < params.breach_probability ? "met-badly" : "met-well"
            trust_before, trust_after, relational_write = update_contact!(
                selected_cause, outcome, params, params.high_E; write_size
            )
            get!(first_contacts, selected, session)
            if outcome == "met-well"
                last_repair_gain[selected] = max(0.0, trust_after - trust_before)
            elseif haskey(last_repair_gain, selected)
                drop = max(0.0, trust_before - trust_after)
                rupture_ratio = drop / max(last_repair_gain[selected], EPS)
                push!(rupture_ratios, rupture_ratio)
            end
            selected == 1 && outcome == "met-well" && maybe_revise_inner!(selected_cause, true)
        end

        policy_delta = sum(abs.(selected_cause.policy_counts .- pre_policy))
        mandate_delta = sum(abs.(selected_cause.mandate_counts .- pre_mandate))
        policy_delta > EPS && (policy_write_events += 1)
        mandate_delta > EPS && (mandate_write_events += 1)
        policy_write_mass += policy_delta
        mandate_write_mass += mandate_delta
        for cause in causes
            if trust(cause) >= params.permission_trust_threshold && !haskey(permission_sessions, cause.id)
                permission_sessions[cause.id] = session
            end
        end

        push!(rows, (
            seed = seed,
            condition = condition,
            session = session,
            selected_cause_id = selected,
            selected_readout = readout_label(selected_cause),
            outcome = outcome,
            computed_access = access,
            relational_write_weight = relational_write,
            trust_before = trust_before,
            trust_after = trust_after,
            rupture_ratio = rupture_ratio,
            policy_write_mass = policy_delta,
            mandate_write_mass = mandate_delta,
            selected_score = score_row.total,
            selected_expected_outcome = score_row.expected_outcome,
            selected_information_gain = score_row.information_gain,
            selected_settled_cost = score_row.settled_forecast_cost,
            deepest_revision = cause_by_id(causes, 1).root_revision,
        ))
    end

    ordered, outside_in_ids, first_contact_sessions = complete_outside_in(first_contacts, causes)
    grown_ratio = isempty(rupture_ratios) ? 0.0 : mean(rupture_ratios)
    return (
        seed = seed,
        causes = causes,
        formation_rows = formation_rows,
        development_history = keep_history ? history : NamedTuple[],
        traces = rows,
        choices = choices,
        forecast_mode = string(forecast_mode),
        forecast_permutation = forecast_permutation,
        history_mode = string(history_mode),
        history_permutation = history_permutation,
        outside_in_ids = outside_in_ids,
        first_contact_sessions = first_contact_sessions,
        complete_outside_in = ordered,
        grown_rupture_ratio = grown_ratio,
        breach_with_prior_repair_count = length(rupture_ratios),
        rupture_asymmetric = grown_ratio > 1.0,
        policy_write_events = policy_write_events,
        mandate_write_events = mandate_write_events,
        policy_write_mass = policy_write_mass,
        mandate_write_mass = mandate_write_mass,
        contacted_event_count = count(row.outcome != "blocked" for row in rows),
    )
end

function taxonomy_rows(seed::Int, causes)
    return [(
        seed = seed,
        cause_id = cause.id,
        formation_event_id = string(cause.formation["formation_event_id"]),
        sim1_pathway = string(cause.formation["sim1_pathway"]),
        formation_route = string(cause.formation["route"]),
        spawned = cause.formation["spawned"],
        origin_episode = cause.formation["origin_episode"],
        origin_epoch = string(cause.formation["origin_epoch"]),
        formation_order = cause.id,
        written_reflexivity = cause.written_reflexivity,
        structural_precision = cause.structural_precision,
        dominant_policy = cause.dominant_policy,
        catastrophic_belief = cause.catastrophic_belief,
        initial_forecast_met_well = cause.formation["initial_relational_counts"][MET_WELL],
        initial_forecast_met_badly = cause.formation["initial_relational_counts"][MET_BADLY],
        initial_forecast_catastrophic = cause.formation["initial_relational_counts"][CATASTROPHIC],
        readout_label = readout_label(cause),
        authored = cause.authored,
    ) for cause in causes]
end

formation_trial(cause::LayerCause) = Int(get(cause.formation, "spawn_trial", 0))

function blocking_strength_values(causes)
    return sort([get(blocker.blocking_strengths, target.id, 0.0)
                 for blocker in causes for target in causes if blocker !== target])
end

function blocking_direction_audit(causes)
    later_to_earlier = 0.0
    earlier_to_later = 0.0
    for blocker in causes, target in causes
        blocker === target && continue
        strength = get(blocker.blocking_strengths, target.id, 0.0)
        blocker_trial = formation_trial(blocker)
        target_trial = formation_trial(target)
        if blocker_trial > target_trial
            later_to_earlier += strength
        elseif blocker_trial < target_trial
            earlier_to_later += strength
        end
    end
    total = later_to_earlier + earlier_to_later
    return (
        later_to_earlier = later_to_earlier,
        earlier_to_later = earlier_to_later,
        later_share = total <= EPS ? 0.0 : later_to_earlier / total,
    )
end

function structural_precision_order_correlation(causes)
    length(causes) >= 2 || return 0.0, false
    order = Float64[cause.id for cause in causes]
    precision = Float64[cause.structural_precision for cause in causes]
    (std(order) <= EPS || std(precision) <= EPS) && return 0.0, false
    return cor(order, precision), true
end

function blocking_rows(seed::Int, grown_causes, shuffled_causes)
    rows = NamedTuple[]
    for blocker in grown_causes, target in grown_causes
        blocker === target && continue
        shuffled_blocker = cause_by_id(shuffled_causes, blocker.id)
        blocker_trial = formation_trial(blocker)
        target_trial = formation_trial(target)
        push!(rows, (
            seed = seed,
            blocker_cause_id = blocker.id,
            target_cause_id = target.id,
            blocker_formation_trial = blocker_trial,
            target_formation_trial = target_trial,
            blocker_formed_later = blocker_trial > target_trial,
            protective_policy_mass = Float64(blocker.formation["protective_policy_mass"]),
            blocker_total_cue_affect_write_mass = Float64(blocker.formation["cue_affect_total_write_mass"]),
            coupled_cue_affect_write_mass = Float64(blocker.formation["blocking_write_mass_by_target"][string(target.id)]),
            grown_blocking_strength = get(blocker.blocking_strengths, target.id, 0.0),
            history_shuffled_blocking_strength = get(shuffled_blocker.blocking_strengths, target.id, 0.0),
        ))
    end
    return rows
end

mean_bool(rows, field::Symbol) = isempty(rows) ? 0.0 : mean(getproperty(row, field) ? 1.0 : 0.0 for row in rows)
mean_field(rows, field::Symbol) = isempty(rows) ? 0.0 : mean(Float64(getproperty(row, field)) for row in rows)
choice_sequence(choices) = join(string.(choices), "-")

function write_size_sweep(config::ExperimentConfig, params::Sim4Params, thresholds::ReadoutThresholds)
    rows = NamedTuple[]
    for write_size in params.contact_write_size_sweep
        runs = [simulate_descent(seed, params, thresholds; write_size, keep_history = false) for seed in config.seeds]
        push!(rows, (
            contact_write_size = write_size,
            seed_count = length(runs),
            ordering_rate = mean(run.complete_outside_in ? 1.0 : 0.0 for run in runs),
            breach_observed_rate = mean(run.breach_with_prior_repair_count > 0 ? 1.0 : 0.0 for run in runs),
            asymmetry_seed_rate = mean(run.rupture_asymmetric ? 1.0 : 0.0 for run in runs),
            mean_grown_rupture_ratio = mean(run.grown_rupture_ratio for run in runs),
            mean_breach_with_prior_repair_count = mean(run.breach_with_prior_repair_count for run in runs),
        ))
    end
    return rows
end

function theory_label(criteria_results)
    criteria_results === nothing && return "null"
    labels = [row.label for row in criteria_results.results]
    isempty(labels) && return "null"
    any(==("falsified"), labels) && return "falsified"
    all(==("support"), labels) && return "support"
    any(==("weak_support"), labels) && return "weak_support"
    return "null"
end

function write_descent_svg(path::AbstractString, traces)
    ensure_dir(dirname(path))
    rows = [row for row in traces if row.condition == "baseline" && row.seed == first(traces).seed]
    width, height = 980, 420
    left, top = 70.0, 55.0
    plot_w, plot_h = 820.0, 250.0
    n_causes = maximum(row.selected_cause_id for row in rows)
    x_for(s) = left + plot_w * (s - 1) / max(length(rows) - 1, 1)
    y_for(id) = top + plot_h - plot_h * (id - 1) / max(n_causes - 1, 1)
    points = join(["$(round(x_for(row.session); digits=1)),$(round(y_for(row.selected_cause_id); digits=1))" for row in rows], " ")
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="$width" height="$height" viewBox="0 0 $width $height">
      <rect width="100%" height="100%" fill="#fbfaf7"/>
      <text x="70" y="30" font-family="Arial" font-size="20" fill="#222">Sim 4: EFE contact over Sim 1-grown causes</text>
      <line x1="$left" y1="$(top + plot_h)" x2="$(left + plot_w)" y2="$(top + plot_h)" stroke="#222"/>
      <line x1="$left" y1="$top" x2="$left" y2="$(top + plot_h)" stroke="#222"/>
      <polyline points="$points" fill="none" stroke="#6f4e7c" stroke-width="2.5"/>
      <text x="390" y="355" font-family="Arial" font-size="13" fill="#444">therapy session</text>
      <text x="18" y="220" font-family="Arial" font-size="13" fill="#444" transform="rotate(-90 18 220)">Sim 1 formation order (newer is higher)</text>
    </svg>
    """
    open(path, "w") do io
        write(io, svg)
    end
end

function write_run_readme(path::AbstractString, summary)
    open(path, "w") do io
        println(io, "# Sim 4 grown-for-real pilot")
        println(io)
        println(io, "Every cause in this run was returned by Sim1.init_agent/run_trial!/spawn machinery under the neutral configured schedule. Taxonomy is a frozen property readout, and initial relational forecasts are randomized independently of formation order.")
        println(io)
        println(io, "- Baseline outside-in rate: $(summary.metrics.descent.ordering_rate)")
        println(io, "- Forecast-permutation outside-in rate: $(summary.metrics.forecast_permutation.ordering_rate)")
        println(io, "- History-shuffle outside-in rate: $(summary.metrics.history_shuffle.ordering_rate)")
        println(io, "- History-shuffle degradation: $(summary.metrics.history_shuffle.ordering_rate_degradation)")
        println(io, "- Provenance-complete/zero-authored audit: $(summary.metrics.grown.zero_authored_complete_provenance)")
        println(io, "- Grown rupture asymmetry seed rate: $(summary.metrics.rupture.asymmetry_seed_rate)")
        println(io, "- Mean grown breach/repair ratio: $(summary.metrics.rupture.mean_grown_ratio)")
    end
end

function run_sim4_config(config::ExperimentConfig; config_path::Union{Nothing, AbstractString} = nothing, output_dir::Union{Nothing, AbstractString} = nothing)
    started = time()
    params = params_from_config(config)
    thresholds = readout_thresholds(config.criteria_path)
    config.label == "pilot" || error("T4.1 Step A permits only label=pilot")
    config.seeds == collect(1001:1010) || error("T4.1 Step A permits only pilot seeds 1001-1010")
    outdir = output_dir === nothing ? normpath(joinpath(config.output_dir, config.experiment, "pilot")) : output_dir
    ensure_dir(outdir)

    baseline_runs = [simulate_descent(seed, params, thresholds; forecast_mode = :baseline) for seed in config.seeds]
    permutation_runs = [simulate_descent(seed, params, thresholds; forecast_mode = :permuted, keep_history = false) for seed in config.seeds]
    history_shuffle_runs = [simulate_descent(seed, params, thresholds; history_mode = :permuted, keep_history = false) for seed in config.seeds]
    sweep_rows = write_size_sweep(config, params, thresholds)

    traces = vcat([run.traces for run in baseline_runs]..., [run.traces for run in permutation_runs]...,
                  [run.traces for run in history_shuffle_runs]...)
    formation_rows = vcat([run.formation_rows for run in baseline_runs]...)
    development_history = vcat([run.development_history for run in baseline_runs]...)
    tax_rows = vcat([taxonomy_rows(run.seed, run.causes) for run in baseline_runs]...)
    pair_rows = vcat([blocking_rows(run.seed, run.causes, history_shuffle_runs[idx].causes)
                      for (idx, run) in enumerate(baseline_runs)]...)
    per_seed = [begin
        perm = permutation_runs[idx]
        shuffled = history_shuffle_runs[idx]
        direction = blocking_direction_audit(run.causes)
        precision_correlation, precision_correlation_evaluable = structural_precision_order_correlation(run.causes)
        (
            seed = run.seed,
            grown_cause_count = length(run.causes),
            descent_evaluable = length(run.causes) >= 2,
            formation_order_newest_to_oldest = join(run.outside_in_ids, "-"),
            first_contact_sessions = join(run.first_contact_sessions, "-"),
            complete_outside_in = run.complete_outside_in,
            permuted_first_contact_sessions = join(perm.first_contact_sessions, "-"),
            permutation_complete_outside_in = perm.complete_outside_in,
            ordering_same_after_permutation = run.complete_outside_in == perm.complete_outside_in,
            forecast_permutation = join(perm.forecast_permutation, "-"),
            history_shuffled_first_contact_sessions = join(shuffled.first_contact_sessions, "-"),
            history_shuffle_complete_outside_in = shuffled.complete_outside_in,
            history_shuffle_seed_degradation = (run.complete_outside_in ? 1 : 0) - (shuffled.complete_outside_in ? 1 : 0),
            history_permutation = join(shuffled.history_permutation, "-"),
            blocking_multiset_preserved = blocking_strength_values(run.causes) ≈ blocking_strength_values(shuffled.causes),
            grown_blocking_later_to_earlier_mass = direction.later_to_earlier,
            grown_blocking_earlier_to_later_mass = direction.earlier_to_later,
            grown_blocking_later_share = direction.later_share,
            structural_precision_order_correlation = precision_correlation,
            structural_precision_order_correlation_evaluable = precision_correlation_evaluable,
            grown_rupture_ratio = run.grown_rupture_ratio,
            breach_with_prior_repair_count = run.breach_with_prior_repair_count,
            rupture_asymmetric = run.rupture_asymmetric,
            policy_write_events = run.policy_write_events,
            mandate_write_events = run.mandate_write_events,
            policy_write_mass = run.policy_write_mass,
            mandate_write_mass = run.mandate_write_mass,
            contacted_event_count = run.contacted_event_count,
            contact_choice_sequence = choice_sequence(run.choices),
        )
    end for (idx, run) in enumerate(baseline_runs)]

    authored_count = count(row.authored for row in tax_rows)
    provenance_complete = all(!isempty(row.formation_event_id) && startswith(row.sim1_pathway, "Sim1.") for row in tax_rows)
    total_causes = length(tax_rows)
    baseline_ordering = mean_bool(per_seed, :complete_outside_in)
    perm_ordering = mean_bool(per_seed, :permutation_complete_outside_in)
    shuffled_ordering = mean_bool(per_seed, :history_shuffle_complete_outside_in)
    asymmetry_rate = mean_bool(per_seed, :rupture_asymmetric)
    observed_rate = mean(row.breach_with_prior_repair_count > 0 ? 1.0 : 0.0 for row in per_seed)
    policy_events = sum(row.policy_write_events for row in per_seed)
    mandate_events = sum(row.mandate_write_events for row in per_seed)
    contacted_events = sum(row.contacted_event_count for row in per_seed)

    summary = (
        experiment = "sim4",
        protocol = (stage = "Step A", label = "pilot", confirmatory_run = false, seeds = copy(config.seeds)),
        config = config_snapshot(config),
        preregistration = (
            thresholds_frozen_before_pilot = true,
            criteria_file = config.criteria_path,
            readout_classifier = thresholds,
            active_criteria = ["S4.descent", "A4.perm", "A4.shuffle-history", "A4.grown", "S4.rupture"],
            original_scripted_criteria_retained_falsified = true,
        ),
        pilot_tuning = (
            initial_schedule_result = "one initial cause in every seed; descent structurally untestable",
            schedule_amendment = "moved the acute omega=3.0/kappa=0.0 Sim 1 formation block before assimilative episodes; no Sim 1 parameter or cause target changed",
            contact_write_size_selection = "selected 0.25, the smallest preregistered equal-write candidate; all five candidates produced asymmetry in 10/10 pilot seeds",
        ),
        formation = (
            machinery = "EmergenceSuite.Sim1.init_agent + run_trial! + spawn_cause! + update_cause!",
            neutral_schedule = params.developmental_schedule,
            total_grown_causes = total_causes,
            per_seed_min_causes = minimum(row.grown_cause_count for row in per_seed),
            per_seed_max_causes = maximum(row.grown_cause_count for row in per_seed),
            descent_evaluable_seed_count = count(row.descent_evaluable for row in per_seed),
            taxonomy_counts = Dict(label => count(row.readout_label == label for row in tax_rows) for label in unique(row.readout_label for row in tax_rows)),
        ),
        forecast_control = (
            initialization = "iid bounded symmetric pseudo-counts independent of cause formation order",
            inheritance = false,
            permutation_arm = true,
        ),
        history_coupling = (
            formula = "blocker learned (flee + appease + attenuate) policy mass * fraction of blocker cue/affect write mass accrued while target was active",
            zero_when_no_coupled_writes = true,
            permutation_arm = "all off-diagonal directed-pair strengths shuffled within seed",
            permutation_rng_offset = 9_000_031,
        ),
        efe_audit = (
            terms = ["access-conditioned expected_outcome", "accessible information_gain", "settled_forecast_cost"],
            direct_depth_or_position_term = false,
            taxonomy_term = false,
            structural_precision_term = false,
            ordering_bonus = false,
            formation_order_comparison = false,
            note = "Access is computed from grown directed-pair strengths and current permission only; pair identity is looked up by cause ID, never ordered by it.",
        ),
        metrics = (
            descent = (
                ordering_rate = baseline_ordering,
                ordering_seed_count = count(row.complete_outside_in for row in per_seed),
            ),
            forecast_permutation = (
                ordering_rate = perm_ordering,
                ordering_seed_count = count(row.permutation_complete_outside_in for row in per_seed),
                outcome_agreement_rate = mean_bool(per_seed, :ordering_same_after_permutation),
                forecasts_carry_ordering_when = [row.seed for row in per_seed if row.complete_outside_in != row.permutation_complete_outside_in],
            ),
            history_shuffle = (
                ordering_rate = shuffled_ordering,
                ordering_seed_count = count(row.history_shuffle_complete_outside_in for row in per_seed),
                ordering_rate_degradation = baseline_ordering - shuffled_ordering,
                degraded_seeds = [row.seed for row in per_seed if row.complete_outside_in && !row.history_shuffle_complete_outside_in],
                improved_seeds = [row.seed for row in per_seed if !row.complete_outside_in && row.history_shuffle_complete_outside_in],
                blocking_multiset_preserved = all(row.blocking_multiset_preserved for row in per_seed),
                ordering_carried_by_grown_coupling = baseline_ordering - shuffled_ordering >= 0.20,
            ),
            ordering_proxy_audit = (
                structural_precision_used_in_access_or_efe = false,
                per_seed_structural_precision_order_correlations = [(
                    seed = row.seed,
                    correlation = row.structural_precision_order_correlation,
                    evaluable = row.structural_precision_order_correlation_evaluable,
                ) for row in per_seed],
                mean_grown_blocking_later_share = mean(row.grown_blocking_later_share for row in per_seed if row.descent_evaluable),
            ),
            grown = (
                authored_cause_count = authored_count,
                provenance_complete_rate = total_causes == 0 ? 0.0 : mean((!isempty(row.formation_event_id) && startswith(row.sim1_pathway, "Sim1.")) ? 1.0 : 0.0 for row in tax_rows),
                zero_authored_complete_provenance = authored_count == 0 && provenance_complete && total_causes > 0 ? 1.0 : 0.0,
            ),
            rupture = (
                per_event_repair_write_size = params.contact_write_size,
                per_event_breach_write_size = params.contact_write_size,
                authored_80_to_8_ratio_retired = true,
                breach_observed_seed_rate = observed_rate,
                asymmetry_seed_rate = asymmetry_rate,
                mean_grown_ratio = mean_field(per_seed, :grown_rupture_ratio),
                min_grown_ratio = minimum(row.grown_rupture_ratio for row in per_seed),
            ),
            bank_writes = (
                policy_write_events = policy_events,
                mandate_write_events = mandate_events,
                policy_write_event_rate = policy_events / max(contacted_events, 1),
                mandate_write_event_rate = mandate_events / max(contacted_events, 1),
                policy_write_mass = sum(row.policy_write_mass for row in per_seed),
                mandate_write_mass = sum(row.mandate_write_mass for row in per_seed),
                measurement = "counted nonzero before/after deltas on actual update_contact! pathways",
            ),
        ),
        pilot_write_size_sweep = sweep_rows,
        per_seed_metric_count = length(per_seed),
        trace_row_count = length(traces),
    )

    summary_path = joinpath(outdir, "summary.json")
    write_json(summary_path, summary)
    write_rows_csv(joinpath(outdir, "per_seed_metrics.csv"), per_seed)
    write_rows_csv(joinpath(outdir, "posterior_traces.csv"), traces)
    write_rows_csv(joinpath(outdir, "formation_events.csv"), formation_rows)
    write_rows_csv(joinpath(outdir, "developmental_history.csv"), development_history)
    write_rows_csv(joinpath(outdir, "taxonomy_readouts.csv"), tax_rows)
    write_rows_csv(joinpath(outdir, "blocking_strengths.csv"), pair_rows)
    write_rows_csv(joinpath(outdir, "write_size_sweep.csv"), sweep_rows)
    write_descent_svg(joinpath(outdir, "figures", "descent.svg"), traces)
    write_run_readme(joinpath(outdir, "README.md"), summary)

    criteria_results = write_criteria_results(config.criteria_path, summary_path, joinpath(outdir, "criteria-results.json"))
    implementation_passed = config.seeds == collect(1001:1010) && config.label == "pilot" &&
        authored_count == 0 && provenance_complete &&
        all(isfile(joinpath(outdir, name)) for name in ("summary.json", "per_seed_metrics.csv", "posterior_traces.csv", "formation_events.csv", "developmental_history.csv", "taxonomy_readouts.csv", "blocking_strengths.csv", "write_size_sweep.csv"))
    status = (
        implementation_passed = implementation_passed,
        theory_result = theory_label(criteria_results),
        stage = "pilot",
        confirmatory_run = false,
        criteria_results_path = joinpath(outdir, "criteria-results.json"),
    )
    write_json(joinpath(outdir, "status.json"), status)
    metadata = build_reproducibility_metadata(
        config;
        config_path = config_path,
        runtime_seconds = time() - started,
        repo_root = normpath(joinpath(@__DIR__, "..", "..", "..", "..", "..")),
        extra = (output_dir = abspath(outdir), sim_module = "EmergenceSuite.Sim4", stage = "pilot", confirmatory = false),
    )
    write_json(joinpath(outdir, "metadata.json"), metadata)

    return (output_dir = outdir, summary = summary, status = status, criteria_results = criteria_results)
end

end
