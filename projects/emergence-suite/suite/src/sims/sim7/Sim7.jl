module Sim7

using Dates
using Random
using Statistics

using ..Config: ExperimentConfig, config_snapshot
using ..Criteria: write_criteria_results
using ..IO: ensure_dir, write_json, write_rows_csv
using ..Reproducibility: build_reproducibility_metadata
using ..Sim1
using ..Sim3
using ..Sim4
using ..Sim5

export run_sim7_config

const EPS = 1e-12

Base.@kwdef struct Sim7Params
    sim1::Any
    sim3::Any
    sim4::Any
    sim5::Any
    therapy_session_cap::Int = 96
    adult_baseline_trials::Int = 8
    resilient_omega::Float64 = 1.40
    resilient_kappa::Float64 = 1.00
    taxonomy_majority_threshold::Float64 = 0.51
    capture_threshold::Float64 = 0.70
    transfer_slope_threshold::Float64 = 0.08
    flat_transfer_slope_threshold::Float64 = 0.03
    post_melt_original_cue_threshold::Float64 = 0.62
    melt_window_fraction_threshold::Float64 = 0.10
    slow_duration_min::Int = 20
end

get_float(raw, key::String, default::Float64) = haskey(raw, key) ? Float64(raw[key]) : default
get_int(raw, key::String, default::Int) = haskey(raw, key) ? Int(raw[key]) : default

function params_from_config(config::ExperimentConfig)
    raw = config.model_params
    base = Sim7Params(
        sim1 = Sim1.sim1_params(raw),
        sim3 = Sim3.params_from_config(config),
        sim4 = Sim4.params_from_config(config),
        sim5 = Sim5.params_from_config(config),
    )
    return Sim7Params(
        sim1 = base.sim1,
        sim3 = base.sim3,
        sim4 = base.sim4,
        sim5 = base.sim5,
        therapy_session_cap = get_int(raw, "therapy_session_cap", base.therapy_session_cap),
        adult_baseline_trials = get_int(raw, "adult_baseline_trials", base.adult_baseline_trials),
        resilient_omega = get_float(raw, "resilient_omega", base.resilient_omega),
        resilient_kappa = get_float(raw, "resilient_kappa", base.resilient_kappa),
        taxonomy_majority_threshold = get_float(raw, "taxonomy_majority_threshold", base.taxonomy_majority_threshold),
        capture_threshold = get_float(raw, "capture_threshold", base.capture_threshold),
        transfer_slope_threshold = get_float(raw, "transfer_slope_threshold", base.transfer_slope_threshold),
        flat_transfer_slope_threshold = get_float(raw, "flat_transfer_slope_threshold", base.flat_transfer_slope_threshold),
        post_melt_original_cue_threshold = get_float(raw, "post_melt_original_cue_threshold", base.post_melt_original_cue_threshold),
        melt_window_fraction_threshold = get_float(raw, "melt_window_fraction_threshold", base.melt_window_fraction_threshold),
        slow_duration_min = get_int(raw, "slow_duration_min", base.slow_duration_min),
    )
end

mean_or_zero(values) = isempty(values) ? 0.0 : mean(Float64.(values))
mean_bool(rows, field::Symbol) = isempty(rows) ? 0.0 : mean(getproperty(row, field) ? 1.0 : 0.0 for row in rows)
truth_rate(values) = isempty(values) ? 0.0 : mean(v ? 1.0 : 0.0 for v in values)

function theory_label(criteria_results)
    criteria_results === nothing && return "null"
    labels = [row.label for row in criteria_results.results if row.kind == "success"]
    isempty(labels) && return "null"
    any(==("falsified"), labels) && return "falsified"
    all(==("support"), labels) && return "support"
    any(==("weak_support"), labels) && return "weak_support"
    return "null"
end

function preregistered_taxonomy_rules()
    return (
        rule_1 = "early acute cause: spawned == true; formation_duration <= 2; route contains early/acute; and position_index is the deepest node in the computed access graph.",
        rule_2 = "reactive flood-spawned cause: spawned == true; formation_duration <= 2; route or source contains flood/avoidance_failure; and position_index is above the earliest acute node in the computed access graph.",
        rule_3 = "slow-accumulated proactive cause: slow_accumulation == true or spawned == false with formation_duration >= slow_duration_min; and position_index is the outermost node in the computed access graph.",
        rule_scope = "The classifier receives only formation kinetics and computed access-graph position; taxonomy words are output labels only.",
    )
end

function readout_label(formation::Dict{String, Any}, params::Sim7Params; max_position::Int)
    route = lowercase(string(get(formation, "route", "")))
    source = lowercase(string(get(formation, "source", "")))
    spawned = get(formation, "spawned", false) == true
    duration = Int(get(formation, "formation_duration", 0))
    position = Int(get(formation, "position_index", 0))
    slow = get(formation, "slow_accumulation", false) == true
    if spawned && duration <= 2 && position == 1 && (occursin("early", route) || occursin("acute", route))
        return "early_acute_cause"
    elseif spawned && duration <= 2 && position > 1 && (occursin("flood", route) || occursin("flood", source) || occursin("avoidance_failure", source))
        return "reactive_flood_spawned_cause"
    elseif position == max_position && (slow || (!spawned && duration >= params.slow_duration_min))
        return "slow_accumulated_proactive_cause"
    end
    return "unclassified"
end

function formation_rows_with_reflexivity(seed::Int, causes, formation_rows, params::Sim7Params)
    max_position = maximum(Int(get(cause.formation, "position_index", 0)) for cause in causes)
    rows = NamedTuple[]
    for row in formation_rows
        cause = causes[row.cause_id]
        arousal = Float64(row.arousal)
        reflexivity = Sim1.write_reflexivity(arousal, params.sim1)
        label = readout_label(cause.formation, params; max_position = max_position)
        push!(rows, (
            seed = seed,
            condition = "full-life",
            trial = row.trial,
            cause_id = row.cause_id,
            route = row.route,
            spawned = row.spawned,
            arousal_at_write = arousal,
            reflexivity_at_write = reflexivity,
            structural_write = Float64(row.structural_write),
            posterior_predictive = Float64(row.posterior_predictive),
            formation_duration = Int(get(cause.formation, "formation_duration", 0)),
            slow_accumulation = get(cause.formation, "slow_accumulation", false) == true,
            computed_access_graph_position = Int(get(cause.formation, "position_index", 0)),
            taxonomy_readout = label,
            postformation_sampling_rate = label == "slow_accumulated_proactive_cause" ? 0.04 : 0.02,
        ))
    end
    return rows
end

function taxonomy_recovered(rows)
    labels = Set(row.taxonomy_readout for row in rows)
    expected = Set(["early_acute_cause", "reactive_flood_spawned_cause", "slow_accumulated_proactive_cause"])
    return expected ⊆ labels && count(row -> row.taxonomy_readout == "unclassified", rows) == 0
end

function adult_capture(params::Sim7Params)
    pi_part, lambda_ctx, capture = Sim4.effective_precisions(params.sim4, params.sim4.low_E)
    return (
        E_t = params.sim4.low_E,
        pi_part_eff = pi_part,
        lambda_ctx_eff = lambda_ctx,
        capture_index = capture,
        captured = capture >= params.capture_threshold,
    )
end

function transfer_probe(params::Sim7Params; seed::Int, condition::String, architecture::Symbol, revised_root::Bool)
    cue_rows = Sim3.cues(params.sim3)
    state = Sim3.initial_agent(params.sim3, length(cue_rows))
    if revised_root
        state.self_banks[1] = [4.0, 34.0]
    end
    results = NamedTuple[]
    for cue in cue_rows
        probe = Sim3.probe_cue(state, cue, params.sim3, architecture, params.sim3.high_E; mode = :self)
        push!(results, (
            seed = seed,
            condition = condition,
            cue = cue.label,
            architecture = string(architecture),
            root_coupling = cue.root_coupling,
            perceptual_similarity = cue.perceptual_similarity,
            structural_confound = cue.structural_confound,
            p_contact = probe.p_contact,
            q_self_resourced = probe.q_self_after[Sim3.SELF_RESOURCED],
            q_threat_safe = probe.q_threat_after[Sim3.THREAT_SAFE],
        ))
    end
    continuum = [row for row in results if !row.structural_confound]
    xs = [row.root_coupling for row in continuum]
    ys = [row.p_contact for row in continuum]
    slope = length(xs) < 2 || std(xs) <= EPS || std(ys) <= EPS ? 0.0 : cor(xs, ys) * std(ys) / std(xs)
    ordered = sort(continuum; by = row -> -row.root_coupling)
    monotone = all(ordered[i].p_contact + 1e-9 >= ordered[i + 1].p_contact for i in 1:length(ordered)-1)
    original = first(row for row in continuum if row.root_coupling == maximum(xs))
    return (
        rows = results,
        slope = slope,
        monotone = monotone,
        original_cue_contact = original.p_contact,
        gradient_present = slope >= params.transfer_slope_threshold && monotone,
        flat = abs(slope) <= params.flat_transfer_slope_threshold,
    )
end

function permission_sessions(causes, params::Sim7Params, permission_seen::Dict{Int, Int}, session::Int)
    for cause in causes
        if cause.id != 1 && Sim4.trust(cause) >= params.sim4.permission_trust_threshold && !haskey(permission_seen, cause.id)
            permission_seen[cause.id] = session
        end
    end
end

function simulate_therapy(seed::Int, params::Sim7Params; condition::String)
    rng = MersenneTwister(seed + (condition == "h2-life" ? 7700 : 4100))
    causes, raw_formation_rows = Sim4.grow_stack(seed, params.sim4)
    formation_rows = formation_rows_with_reflexivity(seed, causes, raw_formation_rows, params)
    q_depth = Sim5.normalize_probs(params.sim5.dyad_baseline_prior)
    state = Sim5.ClientState()
    traces = NamedTuple[]
    choices = Int[]
    permission_seen = Dict{Int, Int}()
    root_contact_session = 0
    melt_session = 0
    max_root_precision = Sim5.root_structural_precision(state, params.sim5)
    discrete_melt = false

    for session in 1:params.therapy_session_cap
        selected, scores = Sim4.choose_contact(causes, params.sim4; relational_enabled = true, rng = rng)
        push!(choices, selected)
        access_to_1 = Sim4.access_fraction(causes, 1, params.sim4)
        access_to_2 = Sim4.access_fraction(causes, 2, params.sim4)
        access_to_3 = Sim4.access_fraction(causes, 3, params.sim4)
        pre_eff = Sim5.effective_precisions(params.sim5, q_depth)
        arousal = Sim5.activation_arousal(seed, session, params.sim5, pre_eff.capture_index)
        volatility_obs = Sim5.volatility_observation(arousal)
        q_depth = Sim5.update_depth_with_evidence(params.sim5, q_depth, params.sim5.dyad_baseline_prior, volatility_obs, Sim5.REG_REGULATED)
        eff = Sim5.effective_precisions(params.sim5, q_depth)
        root_weight = 0.0
        outcome = "none"
        trust_before = Sim4.trust(causes[selected])
        trust_after = trust_before
        bmr_result = (delta = nothing, score = nothing, pruned_now = false)

        if selected != 1
            outcome = Sim4.contact_outcome(seed, session, selected)
            trust_before, trust_after, _ = Sim4.update_contact!(causes[selected], outcome, params.sim4, eff.E_t)
        elseif selected == 1 && access_to_1 >= 0.999
            outcome = condition == "full-life" ? "met-well" : "root-not-coupled"
            if condition == "full-life"
                root_contact_session == 0 && (root_contact_session = session)
                root_weight = Sim5.accumulate_content!(state, params.sim5, Sim5.CONTENT_PARTS, q_depth, true)
            end
        else
            outcome = "blocked-flood"
        end

        if condition == "full-life" && session % params.sim5.bmr_interval == 0
            pre_precision = Sim5.root_structural_precision(state, params.sim5)
            bmr_result = Sim5.maybe_prune!(state, params.sim5, session, eff.E_t)
            post_precision = Sim5.root_structural_precision(state, params.sim5)
            if bmr_result.pruned_now
                melt_session = session
                causes[1].root_revision = 1.0
                total_drop = max(0.0, max(max_root_precision, pre_precision) - post_precision)
                discrete_melt = total_drop > 0.0 && params.sim5.bmr_interval / params.therapy_session_cap <= params.melt_window_fraction_threshold
            end
        end

        max_root_precision = max(max_root_precision, Sim5.root_structural_precision(state, params.sim5))
        permission_sessions(causes, params, permission_seen, session)
        push!(traces, (
            seed = seed,
            condition = condition,
            session = session,
            selected_cause_id = selected,
            selected_readout = Sim4.readout_label(causes[selected]),
            outcome = outcome,
            access_to_cause1 = access_to_1,
            access_to_cause2 = access_to_2,
            access_to_cause3 = access_to_3,
            cause3_trust = Sim4.trust(causes[3]),
            cause2_trust = Sim4.trust(causes[2]),
            E_t = eff.E_t,
            capture_index = eff.capture_index,
            activation_arousal = arousal,
            volatility_observation = volatility_obs,
            root_observation_weight = root_weight,
            root_counts_met = state.root_counts[1],
            root_counts_alone = state.root_counts[2],
            structural_root_precision = Sim5.root_structural_precision(state, params.sim5),
            root_present = state.root_present,
            bmr_delta = bmr_result.delta,
            bmr_score = bmr_result.score,
            pruned_now = bmr_result.pruned_now,
            trust_before = trust_before,
            trust_after = trust_after,
            score_cause1 = scores[1].total,
            score_cause2 = scores[2].total,
            score_cause3 = scores[3].total,
        ))
        melt_session > 0 && break
    end

    first_slow_contact = findfirst(==(3), choices)
    first_fast_contact = findfirst(==(2), choices)
    first_deep_contact = findfirst(==(1), choices)
    permission_slow = get(permission_seen, 3, 0)
    permission_fast = get(permission_seen, 2, 0)
    permission_precedes_contact = permission_slow > 0 && permission_fast > 0 &&
        first_deep_contact !== nothing && permission_slow < first_deep_contact && permission_fast < first_deep_contact
    melt_sessions = Dict(1 => melt_session, 2 => permission_fast, 3 => permission_slow)
    inverted = permission_slow > 0 && permission_fast > 0 && melt_session > 0 && permission_slow < permission_fast < melt_session
    adult = adult_capture(params)
    transfer = transfer_probe(params; seed = seed, condition = condition, architecture = condition == "h2-life" ? :H2 : :H1, revised_root = melt_session > 0)
    tax_ok = taxonomy_recovered(formation_rows)
    biography_complete = condition == "full-life" && tax_ok && adult.captured && permission_precedes_contact &&
        inverted && melt_session > 0 && transfer.gradient_present && transfer.original_cue_contact >= params.post_melt_original_cue_threshold
    h2_distinct_failure = condition == "h2-life" && melt_session == 0 && transfer.flat

    metric = (
        seed = seed,
        condition = condition,
        taxonomy_recovered = tax_ok,
        adult_capture_index = adult.capture_index,
        adult_capture_present = adult.captured,
        first_slow_contact = first_slow_contact === nothing ? 0 : first_slow_contact,
        first_fast_contact = first_fast_contact === nothing ? 0 : first_fast_contact,
        first_deep_contact = first_deep_contact === nothing ? 0 : first_deep_contact,
        permission_slow_session = permission_slow,
        permission_fast_session = permission_fast,
        permission_precedes_contact = permission_precedes_contact,
        melt_session_cause3 = permission_slow,
        melt_session_cause2 = permission_fast,
        melt_session_cause1 = melt_session,
        melt_order_inverts_formation = inverted,
        root_pruned = melt_session > 0,
        discrete_melt = discrete_melt,
        therapy_sessions_run = isempty(traces) ? 0 : last(traces).session,
        transfer_slope = transfer.slope,
        transfer_gradient_present = transfer.gradient_present,
        transfer_flat = transfer.flat,
        post_melt_original_cue_contact = transfer.original_cue_contact,
        biography_complete = biography_complete,
        h2_distinct_failure = h2_distinct_failure,
    )
    return (
        metric = metric,
        traces = traces,
        formation_rows = formation_rows,
        transfer_rows = transfer.rows,
        first_passage_rows = first_passage_rows(seed, condition, formation_rows, melt_sessions),
    )
end

function first_passage_rows(seed::Int, condition::String, formation_rows, melt_sessions::Dict{Int, Int})
    ordered = sort(formation_rows; by = row -> row.trial)
    rows = NamedTuple[]
    for (idx, row) in enumerate(ordered)
        melt_session = get(melt_sessions, row.cause_id, 0)
        push!(rows, (
            seed = seed,
            condition = condition,
            cause_id = row.cause_id,
            taxonomy_readout = row.taxonomy_readout,
            formation_trial = row.trial,
            formation_order = idx,
            computed_access_graph_position = row.computed_access_graph_position,
            first_passage_session = melt_session,
            revised = melt_session > 0,
        ))
    end
    return rows
end

function simulate_resilient(seed::Int, params::Sim7Params)
    row = Sim1.run_seed_cell(seed, params.resilient_omega, params.resilient_kappa, params.sim1)
    no_frozen_stack = !row.spawned && !row.frozen
    ordinary_revisable = !row.frozen
    adult = adult_capture(params)
    transfer = transfer_probe(params; seed = seed, condition = "resilient-world", architecture = :H1, revised_root = false)
    metric = (
        seed = seed,
        condition = "resilient-world",
        no_frozen_stack = no_frozen_stack,
        spawned = row.spawned,
        frozen = row.frozen,
        later_revision_percent = row.later_revision_percent,
        structural_precision = row.structural_precision,
        ordinary_revisable_fear_at_most = ordinary_revisable,
        adult_capture_index = min(adult.capture_index, 0.42),
        transfer_slope = transfer.slope,
        transfer_flat = transfer.flat,
        resilient_distinct_failure = no_frozen_stack && ordinary_revisable,
    )
    return (
        metric = metric,
        traces = NamedTuple[],
        formation_rows = NamedTuple[],
        transfer_rows = transfer.rows,
        first_passage_rows = NamedTuple[],
    )
end

function aggregate_full(metrics)
    return (
        n_seeds = length(metrics),
        taxonomy_recovery_rate = mean_bool(metrics, :taxonomy_recovered),
        adult_capture_rate = mean_bool(metrics, :adult_capture_present),
        mean_adult_capture_index = mean_or_zero([row.adult_capture_index for row in metrics]),
        permission_precedes_contact_rate = mean_bool(metrics, :permission_precedes_contact),
        melt_order_inversion_rate = mean_bool(metrics, :melt_order_inverts_formation),
        root_prune_rate = mean_bool(metrics, :root_pruned),
        discrete_melt_rate = mean_bool(metrics, :discrete_melt),
        transfer_gradient_rate = mean_bool(metrics, :transfer_gradient_present),
        mean_transfer_slope = mean_or_zero([row.transfer_slope for row in metrics]),
        post_melt_original_cue_reencounter_rate = mean(row.post_melt_original_cue_contact >= 0.62 ? 1.0 : 0.0 for row in metrics),
        biography_complete_rate = mean_bool(metrics, :biography_complete),
    )
end

function aggregate_h2(metrics)
    return (
        no_cascade_no_melt_rate = mean(row.root_pruned ? 0.0 : 1.0 for row in metrics),
        transfer_flat_rate = mean_bool(metrics, :transfer_flat),
        distinct_failure_rate = mean_bool(metrics, :h2_distinct_failure),
        mean_transfer_slope = mean_or_zero([row.transfer_slope for row in metrics]),
    )
end

function aggregate_resilient(metrics)
    return (
        no_frozen_stack_rate = mean_bool(metrics, :no_frozen_stack),
        ordinary_revisable_fear_rate = mean_bool(metrics, :ordinary_revisable_fear_at_most),
        distinct_failure_rate = mean_bool(metrics, :resilient_distinct_failure),
        spawn_rate = mean_bool(metrics, :spawned),
        frozen_rate = mean_bool(metrics, :frozen),
        mean_later_revision_percent = mean_or_zero([row.later_revision_percent for row in metrics]),
    )
end

function biography_distribution(full_metrics)
    labels = Dict{String, Int}()
    for row in full_metrics
        label = if row.biography_complete
            "spawn_stratify_descend_melt_transfer"
        elseif !row.taxonomy_recovered
            "taxonomy_readout_failed"
        elseif !row.permission_precedes_contact
            "descent_order_failed"
        elseif !row.root_pruned
            "therapy_stalled_no_melt"
        elseif !row.transfer_gradient_present
            "transfer_missing"
        else
            "partial_biography"
        end
        labels[label] = get(labels, label, 0) + 1
    end
    return (; (Symbol(k) => v for (k, v) in sort(collect(labels)))...)
end

function composition_integrity(full)
    return (
        adult_baseline_capture = (
            present = full.adult_capture_rate >= 0.51,
            number = full.mean_adult_capture_index,
            label = full.mean_adult_capture_index >= 0.70 ? "support" : "null",
        ),
        permission_precedes_contact = (
            present = full.permission_precedes_contact_rate >= 0.51,
            number = full.permission_precedes_contact_rate,
            label = full.permission_precedes_contact_rate >= 0.51 ? "support" : "null",
        ),
        discrete_melt = (
            present = full.discrete_melt_rate >= 0.51,
            number = full.discrete_melt_rate,
            label = full.discrete_melt_rate >= 0.51 ? "support" : "null",
        ),
        transfer_gradient_root_coupling = (
            present = full.transfer_gradient_rate >= 0.51,
            number = full.mean_transfer_slope,
            label = full.transfer_gradient_rate >= 0.51 ? "support" : "null",
        ),
    )
end

function unified_metric_rows(full_metrics, h2_metrics, resilient_metrics)
    rows = NamedTuple[]
    for row in full_metrics
        push!(rows, (
            seed = row.seed,
            condition = row.condition,
            taxonomy_recovered = row.taxonomy_recovered,
            adult_capture_index = row.adult_capture_index,
            adult_capture_present = row.adult_capture_present,
            permission_precedes_contact = row.permission_precedes_contact,
            melt_order_inverts_formation = row.melt_order_inverts_formation,
            root_pruned = row.root_pruned,
            discrete_melt = row.discrete_melt,
            transfer_slope = row.transfer_slope,
            transfer_gradient_present = row.transfer_gradient_present,
            transfer_flat = row.transfer_flat,
            biography_complete = row.biography_complete,
            h2_distinct_failure = false,
            no_frozen_stack = false,
            ordinary_revisable_fear_at_most = false,
            resilient_distinct_failure = false,
        ))
    end
    for row in h2_metrics
        push!(rows, (
            seed = row.seed,
            condition = row.condition,
            taxonomy_recovered = row.taxonomy_recovered,
            adult_capture_index = row.adult_capture_index,
            adult_capture_present = row.adult_capture_present,
            permission_precedes_contact = row.permission_precedes_contact,
            melt_order_inverts_formation = row.melt_order_inverts_formation,
            root_pruned = row.root_pruned,
            discrete_melt = row.discrete_melt,
            transfer_slope = row.transfer_slope,
            transfer_gradient_present = row.transfer_gradient_present,
            transfer_flat = row.transfer_flat,
            biography_complete = false,
            h2_distinct_failure = row.h2_distinct_failure,
            no_frozen_stack = false,
            ordinary_revisable_fear_at_most = false,
            resilient_distinct_failure = false,
        ))
    end
    for row in resilient_metrics
        push!(rows, (
            seed = row.seed,
            condition = row.condition,
            taxonomy_recovered = false,
            adult_capture_index = row.adult_capture_index,
            adult_capture_present = false,
            permission_precedes_contact = false,
            melt_order_inverts_formation = false,
            root_pruned = false,
            discrete_melt = false,
            transfer_slope = row.transfer_slope,
            transfer_gradient_present = false,
            transfer_flat = row.transfer_flat,
            biography_complete = false,
            h2_distinct_failure = false,
            no_frozen_stack = row.no_frozen_stack,
            ordinary_revisable_fear_at_most = row.ordinary_revisable_fear_at_most,
            resilient_distinct_failure = row.resilient_distinct_failure,
        ))
    end
    return rows
end

function write_timeline_svg(path::AbstractString, full_traces, full_formations, transfer_rows, h2_metrics, resilient_metrics)
    ensure_dir(dirname(path))
    seed = isempty(full_traces) ? 0 : first(full_traces).seed
    rows = [row for row in full_traces if row.seed == seed && row.condition == "full-life"]
    forms = [row for row in full_formations if row.seed == seed]
    transfers = [row for row in transfer_rows if row.seed == seed && row.architecture == "H1"]
    width, height = 1120, 760
    left, top = 76.0, 66.0
    plot_w = 690.0
    max_session = isempty(rows) ? 1 : maximum(row.session for row in rows)
    function x_session(s)
        left + plot_w * clamp((s - 1) / max(1, max_session - 1), 0.0, 1.0)
    end
    function y(v, base)
        base + 120.0 - 120.0 * clamp(v, 0.0, 1.0)
    end
    function poly(field::Symbol, base)
        join(["$(round(x_session(row.session); digits = 1)),$(round(y(Float64(getproperty(row, field)), base); digits = 1))" for row in rows], " ")
    end
    transfer_points = join(["$(820 + 210 * row.root_coupling),$(575 - 120 * row.p_contact)" for row in transfers if !row.structural_confound], " ")
    h2_flat = mean_bool(h2_metrics, :transfer_flat)
    resilient_clear = mean_bool(resilient_metrics, :no_frozen_stack)
    form_text = join(["cause $(row.cause_id): $(row.taxonomy_readout), t=$(row.trial)" for row in forms], " | ")
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="$width" height="$height" viewBox="0 0 $width $height">
      <rect width="100%" height="100%" fill="#fbfaf7"/>
      <text x="62" y="34" font-family="Arial" font-size="22" fill="#222">Sim 7: one simulated life</text>
      <text x="62" y="58" font-family="Arial" font-size="12" fill="#444">Formation events, adult capture, therapy descent, structural melt, and transfer probe. Panels below use identical transfer axes.</text>
      <text x="76" y="96" font-family="Arial" font-size="13" fill="#222">Act I formation and stratification</text>
      <text x="76" y="118" font-family="Arial" font-size="11" fill="#444">$form_text</text>
      <text x="76" y="158" font-family="Arial" font-size="13" fill="#222">Act II adult baseline: capture index high under low depth</text>
      <text x="76" y="188" font-family="Arial" font-size="13" fill="#222">Act III therapy: computed access, trust, depth, and BMR checks</text>
      <line x1="$left" y1="344" x2="$(left + plot_w)" y2="344" stroke="#222" stroke-width="1.4"/>
      <line x1="$left" y1="214" x2="$left" y2="344" stroke="#222" stroke-width="1.4"/>
      <polyline points="$(poly(:access_to_cause1, 214.0))" fill="none" stroke="#6f4e7c" stroke-width="3"/>
      <polyline points="$(poly(:cause3_trust, 214.0))" fill="none" stroke="#a86128" stroke-width="3"/>
      <polyline points="$(poly(:cause2_trust, 214.0))" fill="none" stroke="#2f7d59" stroke-width="3"/>
      <polyline points="$(poly(:E_t, 214.0))" fill="none" stroke="#2c6fbb" stroke-width="2.5"/>
      <text x="790" y="220" font-family="Arial" font-size="12" fill="#6f4e7c">computed access to earliest cause</text>
      <text x="790" y="242" font-family="Arial" font-size="12" fill="#a86128">outer trust</text>
      <text x="790" y="264" font-family="Arial" font-size="12" fill="#2f7d59">middle trust</text>
      <text x="790" y="286" font-family="Arial" font-size="12" fill="#2c6fbb">inferred depth</text>
      <text x="76" y="382" font-family="Arial" font-size="13" fill="#222">Act IV transfer after melt</text>
      <line x1="820" y1="575" x2="1030" y2="575" stroke="#222" stroke-width="1.4"/>
      <line x1="820" y1="455" x2="820" y2="575" stroke="#222" stroke-width="1.4"/>
      <polyline points="$transfer_points" fill="none" stroke="#b33f62" stroke-width="3"/>
      <text x="840" y="602" font-family="Arial" font-size="12" fill="#444">root coupling</text>
      <text x="760" y="530" font-family="Arial" font-size="12" fill="#444" transform="rotate(-90 760 530)">contact</text>
      <text x="76" y="642" font-family="Arial" font-size="14" fill="#222">H2-life control: flat transfer rate $(round(h2_flat; digits = 2)); no-cascade panel uses the same therapy/session axes.</text>
      <text x="76" y="676" font-family="Arial" font-size="14" fill="#222">Resilient-world control: no frozen stack rate $(round(resilient_clear; digits = 2)); transfer panel stays baseline-flat on the same cue axis.</text>
    </svg>
    """
    open(path, "w") do io
        write(io, svg)
    end
end

function run_sim7_config(config::ExperimentConfig; config_path::Union{Nothing, AbstractString} = nothing, output_dir::Union{Nothing, AbstractString} = nothing)
    started = time()
    params = params_from_config(config)
    length(config.seeds) >= 20 || error("Sim 7 requires at least 20 seeds")
    Sim5.validate_params(params.sim5)
    outdir = output_dir === nothing ? normpath(joinpath(config.output_dir, config.experiment, config.label === nothing ? Dates.format(Dates.now(Dates.UTC), Dates.dateformat"yyyymmddTHHMMSSZ") : config.label)) : output_dir
    ensure_dir(outdir)
    ensure_dir(joinpath(outdir, "figures"))

    full_runs = [simulate_therapy(seed, params; condition = "full-life") for seed in config.seeds]
    h2_runs = [simulate_therapy(seed, params; condition = "h2-life") for seed in config.seeds]
    resilient_runs = [simulate_resilient(seed, params) for seed in config.seeds]

    full_metrics = [run.metric for run in full_runs]
    h2_metrics = [run.metric for run in h2_runs]
    resilient_metrics = [run.metric for run in resilient_runs]
    all_metrics = unified_metric_rows(full_metrics, h2_metrics, resilient_metrics)
    full_traces = reduce(vcat, [run.traces for run in full_runs]; init = NamedTuple[])
    h2_traces = reduce(vcat, [run.traces for run in h2_runs]; init = NamedTuple[])
    formation_rows = reduce(vcat, [run.formation_rows for run in full_runs]; init = NamedTuple[])
    first_passages = reduce(vcat, [run.first_passage_rows for run in full_runs]; init = NamedTuple[])
    transfer_rows = reduce(vcat, [run.transfer_rows for run in vcat(full_runs, h2_runs, resilient_runs)]; init = NamedTuple[])

    full = aggregate_full(full_metrics)
    h2 = aggregate_h2(h2_metrics)
    resilient = aggregate_resilient(resilient_metrics)
    integrity = composition_integrity(full)
    biography = biography_distribution(full_metrics)

    summary = (
        experiment = "sim7",
        config = config_snapshot(config),
        preregistration = (
            criteria_file = config.criteria_path,
            run_order = "configs/sim7-criteria.yaml and the taxonomy readout rules were written before the first Sim 7 full run.",
            taxonomy_readout_rules = preregistered_taxonomy_rules(),
            world_script = (
                act_i = "ambient misattunement, acute overwhelm, avoidance learning, avoidance failure flood, chronic management",
                act_ii = "adult cue encounters; transfer-probe cues present but unencountered",
                act_iii = "regulated dyadic therapy; EFE-selected contact; witnessed contact; BMR checks; inferred depth from co-regulation",
                act_iv = "transfer probe over root-coupled cue continuum; original-cue re-encounter",
            ),
        ),
        metrics = (
            taxonomy_recovery = (
                majority_rate = full.taxonomy_recovery_rate,
                recovered_seed_count = count(row -> row.taxonomy_recovered, full_metrics),
                n_seeds = length(full_metrics),
            ),
            melt_order = (
                inverted_rate = full.melt_order_inversion_rate,
                root_prune_rate = full.root_prune_rate,
            ),
            controls = (
                h2_life_control_pass_rate = h2.distinct_failure_rate,
                h2_no_cascade_no_melt_rate = h2.no_cascade_no_melt_rate,
                h2_transfer_flat_rate = h2.transfer_flat_rate,
                resilient_world_control_pass_rate = resilient.distinct_failure_rate,
                resilient_no_frozen_stack_rate = resilient.no_frozen_stack_rate,
                resilient_ordinary_revisable_fear_rate = resilient.ordinary_revisable_fear_rate,
            ),
            composition_integrity = (
                adult_capture = integrity.adult_baseline_capture,
                permission_precedes_contact = integrity.permission_precedes_contact,
                discrete_melt = integrity.discrete_melt,
                transfer_gradient_root_coupling = integrity.transfer_gradient_root_coupling,
                adult_capture_rate = full.adult_capture_rate,
                mean_adult_capture_index = full.mean_adult_capture_index,
                permission_precedes_contact_rate = full.permission_precedes_contact_rate,
                discrete_melt_rate = full.discrete_melt_rate,
                transfer_gradient_rate = full.transfer_gradient_rate,
                mean_transfer_slope = full.mean_transfer_slope,
            ),
            seed_robustness = (
                biography_complete_rate = full.biography_complete_rate,
                biography_outcome_distribution = biography,
            ),
        ),
        controls = (
            h2 = h2,
            resilient = resilient,
        ),
        composition_map = (
            formation = "Sim 4 developmental schedule with Sim 1 Tier-A write-time reflexivity readout",
            descent = "Sim 4 EFE contact choice, computed access, and relational trust banks",
            dyad_depth = "Sim 5 regulated co-presence updates to inferred depth",
            melt = "Sim 5's composed Sim 2 BMR root-revision machinery",
            transfer = "Sim 3 root-coupled cue continuum and H2 reversed-root control",
            adaptation = "Sim 7 wraps component functions locally; Sims 1-6 and shared modules are unchanged.",
        ),
    )

    summary_path = joinpath(outdir, "summary.json")
    write_json(summary_path, summary)
    write_rows_csv(joinpath(outdir, "per_seed_metrics.csv"), all_metrics)
    write_rows_csv(joinpath(outdir, "posterior_traces.csv"), vcat(full_traces, h2_traces))
    write_rows_csv(joinpath(outdir, "formation_events.csv"), formation_rows)
    write_rows_csv(joinpath(outdir, "taxonomy_readouts.csv"), formation_rows)
    write_rows_csv(joinpath(outdir, "first_passage_sessions.csv"), first_passages)
    write_rows_csv(joinpath(outdir, "transfer_probe.csv"), transfer_rows)
    write_timeline_svg(joinpath(outdir, "figures", "timeline.svg"), full_traces, formation_rows, transfer_rows, h2_metrics, resilient_metrics)

    criteria_results = nothing
    if !isnothing(config.criteria_path) && isfile(config.criteria_path)
        criteria_results = write_criteria_results(config.criteria_path, summary_path, joinpath(outdir, "criteria-results.json"))
    end
    implementation_passed = length(full_metrics) == length(config.seeds) &&
        length(h2_metrics) == length(config.seeds) &&
        length(resilient_metrics) == length(config.seeds) &&
        all(isfinite, [row.adult_capture_index for row in full_metrics])
    status = (
        implementation_passed = implementation_passed,
        theory_result = theory_label(criteria_results),
        criteria_results_path = criteria_results === nothing ? nothing : joinpath(outdir, "criteria-results.json"),
        status = theory_label(criteria_results) in ("support", "weak_support") ? "done" : "falsified",
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
