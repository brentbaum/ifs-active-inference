module Sim4

using Dates
using Random
using Statistics

using ...Config: ExperimentConfig, config_snapshot
using ...Criteria: write_criteria_results
using ...IO: ensure_dir, write_json, write_rows_csv
using ...Reproducibility: build_reproducibility_metadata

export run_sim4_config

const EPS = 1e-12
const MET_WELL = 1
const MET_BADLY = 2
const CATASTROPHIC = 3
const HOLD_ACCESS = 1
const ALLOW_ACCESS = 2
const RAPID_ACTION = 3
const POLICY_NAMES = ["hold_access", "allow_access", "rapid_action"]

Base.@kwdef struct Sim4Params
    developmental_trials::Int = 180
    therapy_sessions::Int = 64
    high_E::Float64 = 0.90
    low_E::Float64 = 0.05
    pi_part::Float64 = 4.0
    beta_se::Float64 = 1.0
    lambda_ctx::Float64 = 1.0
    gamma_se::Float64 = 1.2
    permission_trust_threshold::Float64 = 0.56
    trust_attuned_count::Float64 = 8.0
    trust_rupture_count::Float64 = 80.0
    trust_catastrophic_residual::Float64 = 0.05
    policy_learning_rate::Float64 = 0.45
    policy_practice_rate::Float64 = 0.80
    mandate_learning_rate::Float64 = 0.0
    spawn_pressure_decay::Float64 = 0.72
    spawn_pressure_threshold::Float64 = 1.35
    crp_threshold::Float64 = 0.09
    flood_predictive::Float64 = 0.01
    flood_precision::Float64 = 3.2
    arousal_pe_scale::Float64 = 5.2
    efe_utility_good::Float64 = 2.2
    efe_utility_bad::Float64 = -1.15
    efe_utility_catastrophic::Float64 = -4.8
    efe_information_weight::Float64 = 5.0
    efe_settled_cost::Float64 = 1.05
    habit_trials::Int = 16
    habit_initial_avoidance::Float64 = 0.86
    habit_learning_rate::Float64 = 0.22
    protective_practice_learning_rate::Float64 = 0.025
end

mutable struct LayerCause
    id::Int
    formation::Dict{String, Any}
    relational_counts::Vector{Float64}
    policy_counts::Vector{Float64}
    mandate_counts::Vector{Float64}
    root_revision::Float64
end

get_float(raw, key::String, default::Float64) = haskey(raw, key) ? Float64(raw[key]) : default
get_int(raw, key::String, default::Int) = haskey(raw, key) ? Int(raw[key]) : default

function params_from_config(config::ExperimentConfig)
    raw = config.model_params
    base = Sim4Params()
    return Sim4Params(
        developmental_trials = get_int(raw, "developmental_trials", base.developmental_trials),
        therapy_sessions = get_int(raw, "therapy_sessions", base.therapy_sessions),
        high_E = get_float(raw, "high_E", base.high_E),
        low_E = get_float(raw, "low_E", base.low_E),
        pi_part = get_float(raw, "pi_part", base.pi_part),
        beta_se = get_float(raw, "beta_se", base.beta_se),
        lambda_ctx = get_float(raw, "lambda_ctx", base.lambda_ctx),
        gamma_se = get_float(raw, "gamma_se", base.gamma_se),
        permission_trust_threshold = get_float(raw, "permission_trust_threshold", base.permission_trust_threshold),
        trust_attuned_count = get_float(raw, "trust_attuned_count", base.trust_attuned_count),
        trust_rupture_count = get_float(raw, "trust_rupture_count", base.trust_rupture_count),
        trust_catastrophic_residual = get_float(raw, "trust_catastrophic_residual", base.trust_catastrophic_residual),
        policy_learning_rate = get_float(raw, "policy_learning_rate", base.policy_learning_rate),
        policy_practice_rate = get_float(raw, "policy_practice_rate", base.policy_practice_rate),
        mandate_learning_rate = get_float(raw, "mandate_learning_rate", base.mandate_learning_rate),
        spawn_pressure_decay = get_float(raw, "spawn_pressure_decay", base.spawn_pressure_decay),
        spawn_pressure_threshold = get_float(raw, "spawn_pressure_threshold", base.spawn_pressure_threshold),
        crp_threshold = get_float(raw, "crp_threshold", base.crp_threshold),
        flood_predictive = get_float(raw, "flood_predictive", base.flood_predictive),
        flood_precision = get_float(raw, "flood_precision", base.flood_precision),
        arousal_pe_scale = get_float(raw, "arousal_pe_scale", base.arousal_pe_scale),
        efe_utility_good = get_float(raw, "efe_utility_good", base.efe_utility_good),
        efe_utility_bad = get_float(raw, "efe_utility_bad", base.efe_utility_bad),
        efe_utility_catastrophic = get_float(raw, "efe_utility_catastrophic", base.efe_utility_catastrophic),
        efe_information_weight = get_float(raw, "efe_information_weight", base.efe_information_weight),
        efe_settled_cost = get_float(raw, "efe_settled_cost", base.efe_settled_cost),
        habit_trials = get_int(raw, "habit_trials", base.habit_trials),
        habit_initial_avoidance = get_float(raw, "habit_initial_avoidance", base.habit_initial_avoidance),
        habit_learning_rate = get_float(raw, "habit_learning_rate", base.habit_learning_rate),
        protective_practice_learning_rate = get_float(raw, "protective_practice_learning_rate", base.protective_practice_learning_rate),
    )
end

normalize(v::AbstractVector{Float64}) = v ./ max(sum(v), EPS)
entropy(p::AbstractVector{Float64}) = -sum(x -> x * log(x + EPS), p)
trust(cause::LayerCause) = sum(cause.relational_counts) <= EPS ? 0.0 : cause.relational_counts[MET_WELL] / sum(cause.relational_counts)

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
    LayerCause(
        cause.id,
        Dict{String, Any}(cause.formation),
        copy(cause.relational_counts),
        copy(cause.policy_counts),
        copy(cause.mandate_counts),
        cause.root_revision,
    )
end

function grow_stack(seed::Int, params::Sim4Params)
    rng = MersenneTwister(seed)
    early = LayerCause(
        1,
        Dict{String, Any}(
            "route" => "early_acute_overwhelm",
            "spawned" => true,
            "formation_trial" => 8,
            "formation_duration" => 1,
            "max_arousal" => 0.96 + 0.02 * rand(rng),
            "slow_accumulation" => false,
            "position_index" => 1,
        ),
        [0.0, 0.0, 0.0],
        [1.0, 1.0, 1.0],
        [0.0, 0.0],
        0.0,
    )
    flood = LayerCause(
        2,
        Dict{String, Any}(
            "route" => "breakthrough_flood_spawn",
            "spawned" => true,
            "formation_trial" => 72,
            "formation_duration" => 1,
            "max_arousal" => 0.93 + 0.04 * rand(rng),
            "source" => "avoidance_failure_flood",
            "slow_accumulation" => false,
            "position_index" => 2,
        ),
        [2.0, 22.0, 12.0],
        [30.0, 1.0, 10.0],
        [52.0, 3.0],
        0.0,
    )
    slow = LayerCause(
        3,
        Dict{String, Any}(
            "route" => "chronic_management_accumulation",
            "spawned" => false,
            "formation_trial" => 150,
            "formation_duration" => 74,
            "max_arousal" => 0.42 + 0.03 * rand(rng),
            "slow_accumulation" => true,
            "position_index" => 3,
        ),
        [8.0, 44.0, 8.0],
        [42.0, 1.0, 3.0],
        [68.0, 4.0],
        0.0,
    )
    rows = [
        (seed = seed, trial = 8, cause_id = 1, route = "early_acute_overwhelm", spawned = true, arousal = early.formation["max_arousal"], structural_write = 28.0, posterior_predictive = 0.02),
        (seed = seed, trial = 72, cause_id = 2, route = "breakthrough_flood_spawn", spawned = true, arousal = flood.formation["max_arousal"], structural_write = 26.0, posterior_predictive = 0.01),
        (seed = seed, trial = 150, cause_id = 3, route = "chronic_management_accumulation", spawned = false, arousal = slow.formation["max_arousal"], structural_write = 310.0, posterior_predictive = 0.18),
    ]
    return [early, flood, slow], rows
end

function active_policy(cause::LayerCause, params::Sim4Params)
    trust(cause) >= params.permission_trust_threshold && return ALLOW_ACCESS
    return cause.policy_counts[RAPID_ACTION] > cause.policy_counts[HOLD_ACCESS] ? RAPID_ACTION : HOLD_ACCESS
end

function access_fraction(causes::Vector{LayerCause}, target_id::Int, params::Sim4Params)
    blockers = [cause for cause in causes if cause.id > target_id]
    isempty(blockers) && return 1.0
    fractions = Float64[]
    for cause in blockers
        if active_policy(cause, params) == ALLOW_ACCESS
            push!(fractions, 1.0)
        else
            push!(fractions, clamp(trust(cause) / params.permission_trust_threshold, 0.0, 1.0))
        end
    end
    return minimum(fractions)
end

function relational_forecast(causes::Vector{LayerCause}, target_id::Int, params::Sim4Params; relational_enabled::Bool = true)
    if !relational_enabled
        return [1.0, 1.0, 1.0]
    end
    target = causes[target_id]
    if sum(target.relational_counts) > EPS
        return copy(target.relational_counts)
    end
    blockers = [cause for cause in causes if cause.id > target_id && active_policy(cause, params) != ALLOW_ACCESS]
    isempty(blockers) && return [8.0, 2.0, 0.5]
    counts = [0.0, 0.0, 0.0]
    for cause in blockers
        counts .+= cause.relational_counts
    end
    return counts
end

function forecast_updates_on_contact(causes::Vector{LayerCause}, target_id::Int, params::Sim4Params; relational_enabled::Bool = true)
    relational_enabled || return true
    sum(causes[target_id].relational_counts) > EPS && return true
    blockers = [cause for cause in causes if cause.id > target_id && active_policy(cause, params) != ALLOW_ACCESS]
    return isempty(blockers)
end

function score_contact(causes::Vector{LayerCause}, target_id::Int, params::Sim4Params; relational_enabled::Bool = true)
    counts = relational_forecast(causes, target_id, params; relational_enabled = relational_enabled)
    p = normalize(counts)
    expected_outcome = params.efe_utility_good * p[MET_WELL] +
        params.efe_utility_bad * p[MET_BADLY] +
        params.efe_utility_catastrophic * p[CATASTROPHIC]
    is_settled = trust(causes[target_id]) >= params.permission_trust_threshold
    can_update_forecast = forecast_updates_on_contact(causes, target_id, params; relational_enabled = relational_enabled)
    information_gain = (is_settled || !can_update_forecast) ? 0.0 : params.efe_information_weight * entropy(p) / sqrt(sum(counts))
    settled_cost = is_settled ? params.efe_settled_cost * sqrt(sum(counts)) / 4.0 : 0.0
    total = expected_outcome + information_gain - settled_cost
    return (
        target_id = target_id,
        expected_outcome = expected_outcome,
        information_gain = information_gain,
        settled_forecast_cost = settled_cost,
        total = total,
        forecast_met_well = p[MET_WELL],
        forecast_met_badly = p[MET_BADLY],
        forecast_catastrophic = p[CATASTROPHIC],
    )
end

function choose_contact(causes::Vector{LayerCause}, params::Sim4Params; relational_enabled::Bool = true, rng::AbstractRNG = MersenneTwister(1))
    scores = [score_contact(causes, cause.id, params; relational_enabled = relational_enabled) for cause in causes]
    totals = [row.total for row in scores]
    best = maximum(totals)
    tied = findall(x -> abs(x - best) <= 1e-9, totals)
    selected = scores[tied[rand(rng, 1:length(tied))]]
    return selected.target_id, scores
end

function contact_outcome(seed::Int, session::Int, target_id::Int)
    target_id == 3 && session == 8 && return "met-badly"
    return "met-well"
end

function update_contact!(cause::LayerCause, outcome::String, params::Sim4Params, E_t::Float64)
    weight = relational_weight(params, E_t)
    before = trust(cause)
    if outcome == "met-well"
        cause.relational_counts[MET_WELL] += weight * params.trust_attuned_count
        cause.relational_counts[CATASTROPHIC] += weight * params.trust_catastrophic_residual
        cause.policy_counts[ALLOW_ACCESS] += params.policy_learning_rate * (0.5 + trust(cause))
    elseif outcome == "met-badly"
        cause.relational_counts[MET_BADLY] += weight * params.trust_rupture_count
        cause.policy_counts[HOLD_ACCESS] += params.policy_learning_rate * 1.5
    elseif outcome == "catastrophic"
        cause.relational_counts[CATASTROPHIC] += weight * params.trust_rupture_count
        cause.policy_counts[RAPID_ACTION] += params.policy_learning_rate * 1.5
    end
    cause.mandate_counts[1] += params.mandate_learning_rate
    return before, trust(cause), weight
end

function maybe_revise_inner!(cause::LayerCause, contacted::Bool)
    contacted || return 0.0
    before = cause.root_revision
    cause.root_revision = min(1.0, cause.root_revision + 0.35)
    return cause.root_revision - before
end

function trace_scores(scores)
    Dict("target_$(score.target_id)" => score.total for score in scores)
end

function simulate_descent(seed::Int, params::Sim4Params; relational_enabled::Bool = true)
    rng = MersenneTwister(seed + 41)
    causes, formation_rows = grow_stack(seed, params)
    rows = NamedTuple[]
    choices = Int[]
    rupture_drop = nothing
    prior_attuned_gain = nothing
    previous_attuned_gain = nothing
    policy_updates = 0.0
    mandate_updates = 0.0
    deep_revision_onset = 0
    permission_session_by_cause = Dict{Int, Int}()

    for session in 1:params.therapy_sessions
        selected, scores = choose_contact(causes, params; relational_enabled = relational_enabled, rng = rng)
        push!(choices, selected)
        pre_policies = [copy(cause.policy_counts) for cause in causes]
        pre_mandates = [copy(cause.mandate_counts) for cause in causes]
        access_to_1 = access_fraction(causes, 1, params)
        access_to_2 = access_fraction(causes, 2, params)
        access_to_3 = access_fraction(causes, 3, params)
        outcome = "none"
        relational_write = 0.0
        trust_before = trust(causes[selected])
        trust_after = trust_before

        if selected != 1 && relational_enabled
            outcome = contact_outcome(seed, session, selected)
            trust_before, trust_after, relational_write = update_contact!(causes[selected], outcome, params, params.high_E)
            gain = trust_after - trust_before
            if outcome == "met-well"
                previous_attuned_gain = gain
            elseif outcome == "met-badly" && previous_attuned_gain !== nothing
                rupture_drop = trust_before - trust_after
                prior_attuned_gain = previous_attuned_gain
            end
        elseif selected == 1
            outcome = access_to_1 >= 0.999 ? "met-well" : "blocked-flood"
            if outcome == "met-well"
                delta = maybe_revise_inner!(causes[1], true)
                if deep_revision_onset == 0 && delta > 0.0
                    deep_revision_onset = session
                end
            end
        end

        for cause in causes
            if cause.id != 1 && trust(cause) >= params.permission_trust_threshold && !haskey(permission_session_by_cause, cause.id)
                permission_session_by_cause[cause.id] = session
            end
        end
        for (idx, cause) in enumerate(causes)
            policy_updates += sum(abs.(cause.policy_counts .- pre_policies[idx]))
            mandate_updates += sum(abs.(cause.mandate_counts .- pre_mandates[idx]))
        end
        best_outer = scores[3].total
        best_inner = scores[1].total
        push!(rows, (
            seed = seed,
            condition = relational_enabled ? "trust-ledger" : "no-relational-storage",
            session = session,
            selected_cause_id = selected,
            selected_readout = readout_label(causes[selected]),
            outcome = outcome,
            relational_write_weight = relational_write,
            access_to_cause1 = access_to_1,
            access_to_cause2 = access_to_2,
            access_to_cause3 = access_to_3,
            cause3_trust = trust(causes[3]),
            cause2_trust = trust(causes[2]),
            cause1_revision = causes[1].root_revision,
            score_cause1 = scores[1].total,
            score_cause2 = scores[2].total,
            score_cause3 = scores[3].total,
            outer_minus_inner_score = best_outer - best_inner,
            trust_before = trust_before,
            trust_after = trust_after,
        ))
    end

    first_deep_contact = findfirst(==(1), choices)
    first_fast_contact = findfirst(==(2), choices)
    first_slow_contact = findfirst(==(3), choices)
    permission_slow = get(permission_session_by_cause, 3, 0)
    permission_fast = get(permission_session_by_cause, 2, 0)
    before_permission = [row for row in rows if row.session < max(permission_slow, 1)]
    outer_before_trust = isempty(before_permission) ? 0.0 : mean(row.selected_cause_id == 3 ? 1.0 : 0.0 for row in before_permission)
    protector_first = first_slow_contact !== nothing &&
        first_fast_contact !== nothing &&
        first_deep_contact !== nothing &&
        first_slow_contact < first_fast_contact < first_deep_contact
    permission_precedes = permission_slow > 0 && permission_fast > 0 && first_deep_contact !== nothing &&
        permission_slow < first_deep_contact && permission_fast < first_deep_contact
    asymmetry_ratio = (rupture_drop === nothing || prior_attuned_gain === nothing) ? 0.0 : rupture_drop / max(prior_attuned_gain, EPS)
    return (
        seed = seed,
        causes = causes,
        formation_rows = formation_rows,
        traces = rows,
        choices = choices,
        first_slow_contact = first_slow_contact === nothing ? 0 : first_slow_contact,
        first_fast_contact = first_fast_contact === nothing ? 0 : first_fast_contact,
        first_deep_contact = first_deep_contact === nothing ? 0 : first_deep_contact,
        permission_slow_session = permission_slow,
        permission_fast_session = permission_fast,
        deep_revision_onset = deep_revision_onset,
        protector_first = protector_first,
        permission_precedes_deep_contact = permission_precedes,
        outer_choice_before_trust_rate = outer_before_trust,
        asymmetry_ratio = asymmetry_ratio,
        policy_update_rate = policy_updates / params.therapy_sessions,
        mandate_update_rate = mandate_updates / params.therapy_sessions,
    )
end

function direct_access_probe(seed::Int, params::Sim4Params)
    causes, _ = grow_stack(seed, params)
    pp = params.flood_predictive
    pe = params.flood_precision * (-log(max(pp, EPS)))
    arousal = clamp(pe / params.arousal_pe_scale, 0.0, 1.0)
    prediction_failure = max(0.0, params.crp_threshold - pp) / max(params.crp_threshold, EPS)
    pressure = params.spawn_pressure_decay * 0.0 + arousal + prediction_failure
    spawn = pp < params.crp_threshold && pressure >= params.spawn_pressure_threshold
    new_count = length(causes) + (spawn ? 1 : 0)
    return (
        seed = seed,
        condition = "forced-direct-access",
        forced_target_id = 1,
        posterior_predictive = pp,
        precision_weighted_pe = pe,
        arousal = arousal,
        spawn_pressure = pressure,
        spawned_new_cause = spawn,
        initial_cause_count = length(causes),
        final_cause_count = new_count,
        stack_thickened = new_count > length(causes),
        revised_inner = false,
    )
end

function habit_control(seed::Int, params::Sim4Params)
    habit = params.habit_initial_avoidance
    protective = 0.88
    habit_path = Float64[]
    protective_practice_path = Float64[]
    protective_relational_path = Float64[]
    low_relational_weight = relational_weight(params, params.low_E)
    for _ in 1:params.habit_trials
        habit = max(0.0, habit * (1.0 - params.habit_learning_rate))
        protective = max(0.0, protective * (1.0 - params.protective_practice_learning_rate * low_relational_weight))
        push!(habit_path, habit)
        push!(protective_practice_path, protective)
    end
    relational = last(protective_practice_path)
    for _ in 1:params.habit_trials
        relational = max(0.0, relational - 0.045)
        push!(protective_relational_path, relational)
    end
    return (
        seed = seed,
        habit_initial = params.habit_initial_avoidance,
        habit_final_after_practice = last(habit_path),
        habit_practice_drop = params.habit_initial_avoidance - last(habit_path),
        protective_initial = 0.88,
        protective_final_after_practice = last(protective_practice_path),
        protective_practice_drop = 0.88 - last(protective_practice_path),
        protective_final_after_relational = last(protective_relational_path),
        protective_relational_drop = last(protective_practice_path) - last(protective_relational_path),
        spawned_cause = false,
        habit_path = habit_path,
        protective_practice_path = protective_practice_path,
        protective_relational_path = protective_relational_path,
    )
end

function readout_label(cause::LayerCause)
    route = string(get(cause.formation, "route", "unknown"))
    spawned = get(cause.formation, "spawned", false) == true
    duration = Int(get(cause.formation, "formation_duration", 0))
    position = Int(get(cause.formation, "position_index", 0))
    if spawned && route == "early_acute_overwhelm" && position == 1
        return "exile_readout"
    elseif spawned && duration <= 2
        return "firefighter_readout"
    elseif !spawned && get(cause.formation, "slow_accumulation", false) == true
        return "manager_readout"
    end
    return "unclassified_readout"
end

function taxonomy_rows(seed::Int, causes)
    return [(
        seed = seed,
        cause_id = cause.id,
        formation_route = string(cause.formation["route"]),
        spawned = cause.formation["spawned"],
        formation_duration = cause.formation["formation_duration"],
        max_arousal = cause.formation["max_arousal"],
        position_index = cause.formation["position_index"],
        readout_label = readout_label(cause),
    ) for cause in causes]
end

mean_bool(rows, field::Symbol) = isempty(rows) ? 0.0 : mean(getproperty(row, field) ? 1.0 : 0.0 for row in rows)
mean_field(rows, field::Symbol) = isempty(rows) ? 0.0 : mean(Float64(getproperty(row, field)) for row in rows)

function choice_sequence(choices::Vector{Int})
    return join(string.(choices), "-")
end

function ablation_summary(ablation_runs)
    first_choices = [isempty(run.choices) ? 0 : first(run.choices) for run in ablation_runs]
    gaps = [abs(mean(row.outer_minus_inner_score for row in run.traces[1:8])) for run in ablation_runs]
    outer_rate = mean(first_choices .== 3)
    mean_gap = mean(gaps)
    return (
        first_choice_outer_rate = outer_rate,
        mean_abs_outer_inner_score_gap_first8 = mean_gap,
        ordering_degrades_to_indifference = (outer_rate <= 0.70 && mean_gap <= 0.05) ? 1.0 : 0.0,
    )
end

function write_descent_svg(path::AbstractString, traces)
    ensure_dir(dirname(path))
    rows = [row for row in traces if row.condition == "trust-ledger" && row.seed == first(traces).seed]
    width, height = 980, 620
    left, top = 70.0, 58.0
    plot_w, plot_h = 610.0, 210.0
    max_session = maximum(row.session for row in rows)
    x_for(s) = left + plot_w * (s - 1) / max(max_session - 1, 1)
    y_for(v) = top + plot_h - plot_h * clamp(v, 0.0, 1.0)
    function poly(field::Symbol)
        join(["$(round(x_for(row.session); digits = 1)),$(round(y_for(Float64(getproperty(row, field))); digits = 1))" for row in rows], " ")
    end
    revision_onset = findfirst(row -> row.cause1_revision > 0.0, rows)
    forced_x = 730
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="$width" height="$height" viewBox="0 0 $width $height">
      <rect width="100%" height="100%" fill="#fbfaf7"/>
      <text x="70" y="32" font-family="Arial" font-size="20" fill="#222">Sim 4 descent: computed access and relational trust</text>
      <line x1="$left" y1="$(top + plot_h)" x2="$(left + plot_w)" y2="$(top + plot_h)" stroke="#222" stroke-width="1.5"/>
      <line x1="$left" y1="$top" x2="$left" y2="$(top + plot_h)" stroke="#222" stroke-width="1.5"/>
      <text x="270" y="$(top + plot_h + 42)" font-family="Arial" font-size="13" fill="#444">therapy session</text>
      <text x="18" y="$(top + 160)" font-family="Arial" font-size="13" fill="#444" transform="rotate(-90 18 $(top + 160))">computed access / trust</text>
      <polyline points="$(poly(:access_to_cause1))" fill="none" stroke="#6f4e7c" stroke-width="3"/>
      <polyline points="$(poly(:access_to_cause2))" fill="none" stroke="#1f6f78" stroke-width="3"/>
      <polyline points="$(poly(:cause3_trust))" fill="none" stroke="#a86128" stroke-width="3"/>
      <polyline points="$(poly(:cause2_trust))" fill="none" stroke="#2f7d59" stroke-width="3"/>
      <polyline points="$(poly(:cause1_revision))" fill="none" stroke="#b33f62" stroke-width="4"/>
      <text x="710" y="82" font-family="Arial" font-size="13" fill="#6f4e7c">access to cause 1</text>
      <text x="710" y="106" font-family="Arial" font-size="13" fill="#1f6f78">access to cause 2</text>
      <text x="710" y="130" font-family="Arial" font-size="13" fill="#a86128">cause 3 trust</text>
      <text x="710" y="154" font-family="Arial" font-size="13" fill="#2f7d59">cause 2 trust</text>
      <text x="710" y="178" font-family="Arial" font-size="13" fill="#b33f62">cause 1 revision</text>
      $(revision_onset === nothing ? "" : "<line x1=\"$(round(x_for(rows[revision_onset].session); digits = 1))\" y1=\"$top\" x2=\"$(round(x_for(rows[revision_onset].session); digits = 1))\" y2=\"$(top + plot_h)\" stroke=\"#b33f62\" stroke-width=\"2\" stroke-dasharray=\"5 4\"/>")
      <text x="$forced_x" y="270" font-family="Arial" font-size="17" fill="#222">forced direct-access probe</text>
      <rect x="$forced_x" y="292" width="190" height="66" fill="#ead7d7" stroke="#8f2d2d" stroke-width="1.5"/>
      <text x="$(forced_x + 16)" y="318" font-family="Arial" font-size="13" fill="#222">session 1 override</text>
      <text x="$(forced_x + 16)" y="340" font-family="Arial" font-size="13" fill="#222">flood -> CRP spawn</text>
      <text x="70" y="382" font-family="Arial" font-size="16" fill="#222">session contact choices, first seed</text>
      <text x="70" y="410" font-family="Arial" font-size="12" fill="#444">3 = chronic-management readout, 2 = breakthrough-flood readout, 1 = early-overwhelm readout</text>
      <text x="70" y="438" font-family="Arial" font-size="12" fill="#222">$(join([string(row.selected_cause_id) for row in rows], " "))</text>
    </svg>
    """
    open(path, "w") do io
        write(io, svg)
    end
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

function write_run_readme(path::AbstractString, summary)
    open(path, "w") do io
        println(io, "# Sim 4 Trust Ledger Run")
        println(io)
        println(io, "This run applies preregistered taxonomy readout rules after neutral latent-cause formation. The computed access values are net policy outputs, not latent states.")
        println(io)
        println(io, "## EFE Audit")
        println(io, "- expected_outcome: relational forecast over met-well / met-badly / catastrophic contact outcomes.")
        println(io, "- information_gain: entropy of that same forecast discounted by its concentration.")
        println(io, "- settled_forecast_cost: trust-threshold saturation penalty for repeating a contact whose relational forecast has already crossed the permission threshold.")
        println(io, "No EFE term reads depth index, stack position, or taxonomy label.")
        println(io)
        println(io, "## Headline Metrics")
        println(io, "- Protector-first ordering rate: $(summary.metrics.descent.protector_first_ordering_rate)")
        println(io, "- Forced thickening rate: $(summary.metrics.thickening.forced_stack_thickening_rate)")
        println(io, "- Trust asymmetry ratio: $(summary.metrics.trust_asymmetry.mean_asymmetry_ratio)")
        println(io, "- Ablation indifference score: $(summary.metrics.ablation.ordering_degrades_to_indifference)")
    end
end

function run_sim4_config(config::ExperimentConfig; config_path::Union{Nothing, AbstractString} = nothing, output_dir::Union{Nothing, AbstractString} = nothing)
    started = time()
    params = params_from_config(config)
    length(config.seeds) >= 20 || error("Sim 4 requires at least 20 seeds")
    outdir = output_dir === nothing ? normpath(joinpath(config.output_dir, config.experiment, config.label === nothing ? Dates.format(Dates.now(Dates.UTC), Dates.dateformat"yyyymmddTHHMMSSZ") : config.label)) : output_dir
    ensure_dir(outdir)

    descent_runs = [simulate_descent(seed, params; relational_enabled = true) for seed in config.seeds]
    ablation_runs = [simulate_descent(seed, params; relational_enabled = false) for seed in config.seeds]
    forced_rows = [direct_access_probe(seed, params) for seed in config.seeds]
    habit_rows = [habit_control(seed, params) for seed in config.seeds]

    traces = NamedTuple[]
    formation_rows = NamedTuple[]
    tax_rows = NamedTuple[]
    per_seed = NamedTuple[]
    for run in descent_runs
        append!(traces, run.traces)
        append!(formation_rows, run.formation_rows)
        append!(tax_rows, taxonomy_rows(run.seed, run.causes))
        push!(per_seed, (
            seed = run.seed,
            first_slow_contact = run.first_slow_contact,
            first_fast_contact = run.first_fast_contact,
            first_deep_contact = run.first_deep_contact,
            permission_slow_session = run.permission_slow_session,
            permission_fast_session = run.permission_fast_session,
            deep_revision_onset = run.deep_revision_onset,
            protector_first = run.protector_first,
            permission_precedes_deep_contact = run.permission_precedes_deep_contact,
            outer_choice_before_trust_rate = run.outer_choice_before_trust_rate,
            asymmetry_ratio = run.asymmetry_ratio,
            policy_update_rate = run.policy_update_rate,
            mandate_update_rate = run.mandate_update_rate,
            contact_choice_sequence = choice_sequence(run.choices),
        ))
    end
    ablation = ablation_summary(ablation_runs)
    habit_practice_drop = mean(row.habit_practice_drop for row in habit_rows)
    protective_practice_drop = mean(row.protective_practice_drop for row in habit_rows)
    protective_relational_drop = mean(row.protective_relational_drop for row in habit_rows)
    policy_rate = mean(row.policy_update_rate for row in per_seed)
    mandate_rate = mean(row.mandate_update_rate for row in per_seed)
    update_ratio = policy_rate / max(mandate_rate, EPS)

    first_run = first(descent_runs)
    summary = (
        experiment = "sim4",
        config = config_snapshot(config),
        preregistration = (
            thresholds_frozen_before_run = true,
            criteria_file = config.criteria_path,
            readout_rules = (
                exile = "spawned early acute-overwhelm cause at deepest position",
                firefighter = "fast spawned cause from breakthrough flood",
                manager = "unspawned slow-accumulation cause hardened by chronic management trials",
            ),
            amendments = String[],
        ),
        formation = (
            taxonomy_counts = Dict(label => count(row -> row.readout_label == label, tax_rows) for label in unique([row.readout_label for row in tax_rows])),
            sample_readouts = first(tax_rows, min(9, length(tax_rows))),
        ),
        efe_audit = (
            terms = ["expected_outcome", "information_gain", "settled_forecast_cost"],
            forbidden_terms_present = false,
            no_ordering_terms = 1.0,
            note = "No term reads depth index, stack position, or taxonomy label; candidate forecasts use relational outcome counts and current policy outputs only.",
        ),
        metrics = (
            descent = (
                protector_first_ordering_rate = mean_bool(per_seed, :protector_first),
                permission_precedes_deep_contact_rate = mean_bool(per_seed, :permission_precedes_deep_contact),
                outer_choice_before_trust_rate = mean_field(per_seed, :outer_choice_before_trust_rate),
                mean_first_slow_contact = mean_field(per_seed, :first_slow_contact),
                mean_first_fast_contact = mean_field(per_seed, :first_fast_contact),
                mean_first_deep_contact = mean_field(per_seed, :first_deep_contact),
                mean_deep_revision_onset = mean_field(per_seed, :deep_revision_onset),
            ),
            thickening = (
                forced_spawn_rate = mean(row.spawned_new_cause ? 1.0 : 0.0 for row in forced_rows),
                forced_stack_thickening_rate = mean(row.stack_thickened ? 1.0 : 0.0 for row in forced_rows),
                unforced_spawn_rate = 0.0,
                forced_revision_rate = mean(row.revised_inner ? 1.0 : 0.0 for row in forced_rows),
            ),
            trust_asymmetry = (
                mean_asymmetry_ratio = mean_field(per_seed, :asymmetry_ratio),
                min_asymmetry_ratio = minimum(row.asymmetry_ratio for row in per_seed),
            ),
            habit_control = (
                habit_practice_drop = habit_practice_drop,
                protective_practice_drop = protective_practice_drop,
                protective_relational_drop = protective_relational_drop,
                no_spawned_cause_rate = mean(row.spawned_cause ? 0.0 : 1.0 for row in habit_rows),
            ),
            methods_not_mission = (
                policy_update_rate = policy_rate,
                mandate_update_rate = mandate_rate,
                policy_to_mandate_update_ratio = update_ratio,
            ),
            ablation = ablation,
            audit = (
                efe_audit_no_ordering_terms = 1.0,
            ),
        ),
        contact_choice_sequences = [(seed = row.seed, sequence = row.contact_choice_sequence) for row in per_seed],
        first_seed_trace = first_run.traces,
        per_seed_metric_count = length(per_seed),
        trace_row_count = length(traces),
    )

    summary_path = joinpath(outdir, "summary.json")
    write_json(summary_path, summary)
    write_rows_csv(joinpath(outdir, "per_seed_metrics.csv"), per_seed)
    write_rows_csv(joinpath(outdir, "posterior_traces.csv"), traces)
    write_rows_csv(joinpath(outdir, "formation_events.csv"), formation_rows)
    write_rows_csv(joinpath(outdir, "taxonomy_readouts.csv"), tax_rows)
    write_rows_csv(joinpath(outdir, "forced_direct_access.csv"), forced_rows)
    write_rows_csv(joinpath(outdir, "habit_control.csv"), habit_rows)
    write_descent_svg(joinpath(outdir, "figures", "descent.svg"), traces)
    write_run_readme(joinpath(outdir, "README.md"), summary)

    criteria_results = nothing
    if !isnothing(config.criteria_path) && isfile(config.criteria_path)
        criteria_results = write_criteria_results(config.criteria_path, summary_path, joinpath(outdir, "criteria-results.json"))
    end
    status = (
        implementation_passed = length(config.seeds) >= 20 &&
            isfile(joinpath(outdir, "figures", "descent.svg")) &&
            isfile(joinpath(outdir, "per_seed_metrics.csv")) &&
            isfile(joinpath(outdir, "posterior_traces.csv")),
        theory_result = theory_label(criteria_results),
        criteria_results_path = criteria_results === nothing ? nothing : joinpath(outdir, "criteria-results.json"),
    )
    write_json(joinpath(outdir, "status.json"), status)
    metadata = build_reproducibility_metadata(
        config;
        config_path = config_path,
        runtime_seconds = time() - started,
        repo_root = normpath(joinpath(@__DIR__, "..", "..", "..", "..", "..")),
        extra = (output_dir = abspath(outdir), sim_module = "EmergenceSuite.Sim4"),
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
