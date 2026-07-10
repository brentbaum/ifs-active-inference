module Sim7

using Dates
using Random
using Statistics

using ..Config: ExperimentConfig, config_snapshot
using ..Criteria: write_criteria_results
using ..IO: ensure_dir, write_json, write_rows_csv
using ..Reproducibility: build_reproducibility_metadata
using ..Sim1
using ..Sim4
using ..Sim5

export run_sim7_config

const EPS = 1e-12
const ROOT_NODE = 1
const CONTEXT_NODE = 2
const SAFE_EVIDENCE = 1
const DANGER_EVIDENCE = 2

"""The sole H1/H2 parameter: which node receives the suppressive depth tilt."""
struct GraphDirection
    depth_tilt_target::Int
    function GraphDirection(depth_tilt_target::Int)
        depth_tilt_target in (ROOT_NODE, CONTEXT_NODE) || error("depth_tilt_target must name one of the two graph nodes")
        new(depth_tilt_target)
    end
end

Base.@kwdef struct Sim7Params
    sim1::Any
    sim4::Any
    sim5::Any
    adult_trials::Int = 48
    adult_heldout_trials::Int = 12
    therapy_sessions::Int = 96
    posttherapy_heldout_trials::Int = 12
    adult_adversity_probability::Float64 = 0.68
    adult_trigger_every::Int = 6
    trigger_adversity_probability::Float64 = 0.90
    posttherapy_safe_probability::Float64 = 0.82
    witnessing_write_size::Float64 = 18.0
    adult_write_size::Float64 = 1.0
    therapy_safe_probability::Float64 = 0.92
    capture_threshold::Float64 = 0.30
    melt_capture_drop_threshold::Float64 = 0.08
    carried_correlation_threshold::Float64 = -0.25
    adult_capture_rate_threshold::Float64 = 0.60
    therapy_melt_rate_threshold::Float64 = 0.60
    h1_loglik_advantage_threshold::Float64 = 0.02
    h1_win_rate_threshold::Float64 = 0.70
end

get_float(raw, key::String, default::Float64) = haskey(raw, key) ? Float64(raw[key]) : default
get_int(raw, key::String, default::Int) = haskey(raw, key) ? Int(raw[key]) : default

function params_from_config(config::ExperimentConfig)
    raw = config.model_params
    base = Sim7Params(
        sim1 = Sim1.sim1_params(raw),
        sim4 = Sim4.params_from_config(config),
        sim5 = Sim5.params_from_config(config),
    )
    return Sim7Params(
        sim1 = base.sim1,
        sim4 = base.sim4,
        sim5 = base.sim5,
        adult_trials = get_int(raw, "adult_trials", base.adult_trials),
        adult_heldout_trials = get_int(raw, "adult_heldout_trials", base.adult_heldout_trials),
        therapy_sessions = get_int(raw, "therapy_sessions", base.therapy_sessions),
        posttherapy_heldout_trials = get_int(raw, "posttherapy_heldout_trials", base.posttherapy_heldout_trials),
        adult_adversity_probability = get_float(raw, "adult_adversity_probability", base.adult_adversity_probability),
        adult_trigger_every = get_int(raw, "adult_trigger_every", base.adult_trigger_every),
        trigger_adversity_probability = get_float(raw, "trigger_adversity_probability", base.trigger_adversity_probability),
        posttherapy_safe_probability = get_float(raw, "posttherapy_safe_probability", base.posttherapy_safe_probability),
        witnessing_write_size = get_float(raw, "witnessing_write_size", base.witnessing_write_size),
        adult_write_size = get_float(raw, "adult_write_size", base.adult_write_size),
        therapy_safe_probability = get_float(raw, "therapy_safe_probability", base.therapy_safe_probability),
        capture_threshold = get_float(raw, "capture_threshold", base.capture_threshold),
        melt_capture_drop_threshold = get_float(raw, "melt_capture_drop_threshold", base.melt_capture_drop_threshold),
        carried_correlation_threshold = get_float(raw, "carried_correlation_threshold", base.carried_correlation_threshold),
        adult_capture_rate_threshold = get_float(raw, "adult_capture_rate_threshold", base.adult_capture_rate_threshold),
        therapy_melt_rate_threshold = get_float(raw, "therapy_melt_rate_threshold", base.therapy_melt_rate_threshold),
        h1_loglik_advantage_threshold = get_float(raw, "h1_loglik_advantage_threshold", base.h1_loglik_advantage_threshold),
        h1_win_rate_threshold = get_float(raw, "h1_win_rate_threshold", base.h1_win_rate_threshold),
    )
end

Base.@kwdef struct WorldEvent
    stage::Symbol
    step::Int
    target_id::Int
    observed_safe::Bool
    trigger::Bool = false
    therapist_signal::Int = 0
    observed_settled::Bool = false
    evidence_mass::Float64 = 0.0
    learn::Bool = true
end

"""One object owns every mutable agent quantity for one simulated life."""
mutable struct LifeState
    seed::Int
    graph::GraphDirection
    causes::Vector{Sim4.LayerCause}
    q_depth::Vector{Float64}
    depth_baseline::Vector{Float64}
    coreg_counts::Matrix{Float64}
    focal_cause_id::Int
    initial_bank_objects::Vector{UInt}
    childhood_written_reflexivity::Float64
    adult_pretherapy_captures::Dict{Int, Float64}
    first_contacts::Dict{Int, Int}
    melt_sessions::Dict{Int, Int}
    witnessing_evidence_mass::Float64
    trace::Vector{NamedTuple}
end

normalize(v) = Float64.(v) ./ max(sum(v), EPS)
architecture_label(state::LifeState) = ("H1", "H2")[state.graph.depth_tilt_target]
cause_by_id(state::LifeState, id::Int) = Sim4.cause_by_id(state.causes, id)
danger_probability(cause) = normalize(cause.mandate_counts)[DANGER_EVIDENCE]

function bank_objects(state::LifeState)
    ids = UInt[]
    for cause in state.causes
        append!(ids, UInt[objectid(cause.relational_counts), objectid(cause.policy_counts), objectid(cause.mandate_counts)])
    end
    append!(ids, UInt[objectid(state.q_depth), objectid(state.coreg_counts)])
    return ids
end

function sim1_probe_base_precisions(cause, params::Sim7Params)
    written_depth = cause.written_reflexivity * params.sim1.probe_depth_scale
    root = (cause.structural_precision / params.sim1.capture_precision_scale) * exp(-params.sim1.tilt_beta * written_depth)
    context = params.sim1.context_precision * exp(params.sim1.tilt_gamma * written_depth)
    return root, context
end

function precision_readout(state::LifeState, cause, params::Sim7Params)
    root, context = sim1_probe_base_precisions(cause, params)
    E_t = Sim5.expected_depth(params.sim5, state.q_depth)
    suppress = exp(-params.sim1.tilt_beta * E_t)
    amplify = exp(params.sim1.tilt_gamma * E_t)
    tilt_rows = ((suppress, amplify), (amplify, suppress))
    tilt = tilt_rows[state.graph.depth_tilt_target]
    root_eff = root * tilt[ROOT_NODE]
    context_eff = context * tilt[CONTEXT_NODE]
    root_share = root_eff / max(root_eff + context_eff, EPS)
    capture = root_share * danger_probability(cause)
    return (E_t = E_t, root_eff = root_eff, context_eff = context_eff, root_share = root_share, capture = capture)
end

capture_readout(state::LifeState, params::Sim7Params) = precision_readout(state, cause_by_id(state, state.focal_cause_id), params)

function fixed_probe_readout(state::LifeState, params::Sim7Params)
    cause = cause_by_id(state, state.focal_cause_id)
    precision = precision_readout(state, cause, params)
    before = danger_probability(cause)
    safe_write = params.sim1.disconfirming_trials * params.sim1.revision_learning_rate * (1.0 - precision.root_share)
    after = cause.mandate_counts[DANGER_EVIDENCE] / max(sum(cause.mandate_counts) + safe_write, EPS)
    revision = max(before - after, 0.0) / max(before, EPS)
    return (danger_before = before, danger_after = after, revision = revision, evidence_weight = 1.0 - precision.root_share)
end

function focal_cause_id(causes, params::Sim7Params)
    scores = map(causes) do cause
        root, context = sim1_probe_base_precisions(cause, params)
        root / max(root + context, EPS) * danger_probability(cause)
    end
    return causes[argmax(scores)].id
end

function initialize_life(seed::Int, graph::GraphDirection, params::Sim7Params)
    # This is the sole bank-producing call. Every returned Sim 1-grown/Sim 4-wrapped
    # array is retained by identity for the rest of the biography.
    causes, _ = Sim4.grow_stack(seed, params.sim4)
    q_depth = Sim5.normalize_probs(params.sim5.low_baseline_prior)
    baseline = copy(q_depth)
    mapping = fill(params.sim5.mapping_prior_count, 4, 2)
    focal = focal_cause_id(causes, params)
    state = LifeState(
        seed,
        graph,
        causes,
        q_depth,
        baseline,
        mapping,
        focal,
        UInt[],
        Sim4.cause_by_id(causes, focal).written_reflexivity,
        Dict{Int, Float64}(),
        Dict{Int, Int}(),
        Dict{Int, Int}(),
        0.0,
        NamedTuple[],
    )
    append!(state.initial_bank_objects, bank_objects(state))
    return state
end

function learned_settle_probability(state::LifeState, signal::Int)
    counts = view(state.coreg_counts, signal, :)
    return counts[1] / max(sum(counts), EPS)
end

function update_depth!(state::LifeState, event::WorldEvent, arousal::Float64, params::Sim7Params)
    volatility = Sim5.volatility_observation(arousal)
    learned_settle = 0.5
    if event.therapist_signal > 0
        if event.learn
            outcome = event.observed_settled ? 1 : 2
            state.coreg_counts[event.therapist_signal, outcome] += params.sim5.mapping_learning_rate
        end
        learned_settle = learned_settle_probability(state, event.therapist_signal)
        next_q = Sim5.update_depth_with_learned_mapping(params.sim5, state.q_depth, state.depth_baseline, volatility, learned_settle)
        state.q_depth .= next_q
    else
        next_q = Sim5.update_depth_with_evidence(params.sim5, state.q_depth, state.depth_baseline, volatility, Sim5.REG_NONE)
        state.q_depth .= next_q
    end
    return volatility, learned_settle
end

"""Shared update for adult adversity, therapy, and frozen held-out segments."""
function update_life!(state::LifeState, event::WorldEvent, params::Sim7Params)
    cause = cause_by_id(state, event.target_id)
    pre = precision_readout(state, cause, params)
    p_safe = clamp(1.0 - pre.capture, 0.02, 0.98)
    log_likelihood = log(event.observed_safe ? p_safe : 1.0 - p_safe)
    arousal = Sim5.activation_arousal(state.seed, event.step, params.sim5, pre.capture)
    volatility, learned_settle = update_depth!(state, event, arousal, params)
    relational_write = 0.0
    root_write = 0.0

    if event.learn
        outcome = event.observed_safe ? "met-well" : "met-badly"
        _, _, relational_write = Sim4.update_contact!(cause, outcome, params.sim4, Sim5.expected_depth(params.sim5, state.q_depth); write_size = event.evidence_mass)
        evidence_index = event.observed_safe ? SAFE_EVIDENCE : DANGER_EVIDENCE
        post_depth = precision_readout(state, cause, params)
        evidence_access = event.observed_safe ? 1.0 - post_depth.capture : post_depth.capture
        root_write = event.evidence_mass * evidence_access
        cause.mandate_counts[evidence_index] += root_write
        cause.structural_precision += root_write
        if event.stage === :therapy && event.observed_safe
            state.witnessing_evidence_mass += root_write
        end
    end

    post = precision_readout(state, cause, params)
    push!(state.trace, (
        seed = state.seed,
        architecture = architecture_label(state),
        stage = string(event.stage),
        step = event.step,
        target_id = event.target_id,
        trigger = event.trigger,
        observed_safe = event.observed_safe,
        learn = event.learn,
        therapist_signal = event.therapist_signal,
        observed_settled = event.observed_settled,
        learned_settle_probability = learned_settle,
        volatility_observation = volatility,
        E_t = post.E_t,
        capture_before = pre.capture,
        capture_after = post.capture,
        root_safe_count = cause.mandate_counts[SAFE_EVIDENCE],
        root_danger_count = cause.mandate_counts[DANGER_EVIDENCE],
        relational_write_weight = relational_write,
        root_evidence_write = root_write,
        log_likelihood = log_likelihood,
    ))
    return log_likelihood
end

function world_schedule(seed::Int, params::Sim7Params)
    rng = Xoshiro(UInt64(seed) + 0x7a11)
    adult = NamedTuple[]
    for trial in 1:params.adult_trials
        trigger = trial % params.adult_trigger_every == 0
        probability = trigger ? params.trigger_adversity_probability : params.adult_adversity_probability
        push!(adult, (observed_safe = rand(rng) >= probability, trigger = trigger))
    end
    adult_heldout = [(observed_safe = rand(rng) >= params.adult_adversity_probability, trigger = false) for _ in 1:params.adult_heldout_trials]
    therapy = NamedTuple[]
    for _ in 1:params.therapy_sessions
        signal = Sim5.emit_therapist_signal(rng, params.sim5, "regulated")
        settled = rand(rng) < params.sim5.mapping_settle_probability_by_signal[signal]
        safe = rand(rng) < params.therapy_safe_probability
        push!(therapy, (signal = signal, settled = settled, observed_safe = safe))
    end
    post = [(observed_safe = rand(rng) < params.posttherapy_safe_probability, trigger = false) for _ in 1:params.posttherapy_heldout_trials]
    return (adult = adult, adult_heldout = adult_heldout, therapy = therapy, post = post)
end

function active_adult_cause(state::LifeState, params::Sim7Params)
    scores = [precision_readout(state, cause, params).capture for cause in state.causes]
    return state.causes[argmax(scores)].id
end

function record_pretherapy!(state::LifeState, params::Sim7Params)
    for cause in state.causes
        state.adult_pretherapy_captures[cause.id] = precision_readout(state, cause, params).capture
    end
end

function record_therapy_passages!(state::LifeState, target_id::Int, session::Int, params::Sim7Params)
    haskey(state.first_contacts, target_id) || (state.first_contacts[target_id] = session)
    before = state.adult_pretherapy_captures[target_id]
    after = precision_readout(state, cause_by_id(state, target_id), params).capture
    if before - after >= params.melt_capture_drop_threshold && !haskey(state.melt_sessions, target_id)
        state.melt_sessions[target_id] = session
    end
end

function simulate_life(seed::Int, graph::GraphDirection, schedule, params::Sim7Params)
    state = initialize_life(seed, graph, params)
    initial_objects = copy(state.initial_bank_objects)
    childhood_counts = copy(cause_by_id(state, state.focal_cause_id).mandate_counts)
    childhood_precision = cause_by_id(state, state.focal_cause_id).structural_precision

    for (trial, world) in enumerate(schedule.adult)
        target = active_adult_cause(state, params)
        event = WorldEvent(
            stage = :adult,
            step = trial,
            target_id = target,
            observed_safe = world.observed_safe,
            trigger = world.trigger,
            evidence_mass = params.adult_write_size,
        )
        update_life!(state, event, params)
    end
    adult = capture_readout(state, params)
    pretherapy_probe = fixed_probe_readout(state, params)
    adult_counts = copy(cause_by_id(state, state.focal_cause_id).mandate_counts)

    heldout_loglik = Float64[]
    heldout_offset = params.adult_trials
    for (trial, world) in enumerate(schedule.adult_heldout)
        event = WorldEvent(
            stage = :adult_heldout,
            step = heldout_offset + trial,
            target_id = active_adult_cause(state, params),
            observed_safe = world.observed_safe,
            learn = false,
        )
        push!(heldout_loglik, update_life!(state, event, params))
    end

    record_pretherapy!(state, params)
    therapy_rng = Xoshiro(UInt64(seed) + 0x7e21)
    therapy_offset = heldout_offset + params.adult_heldout_trials
    for (session, world) in enumerate(schedule.therapy)
        selected, _ = Sim4.choose_contact(state.causes, params.sim4; relational_enabled = true, rng = therapy_rng)
        access = Sim4.access_fraction(state.causes, selected, params.sim4)
        event = WorldEvent(
            stage = :therapy,
            step = therapy_offset + session,
            target_id = selected,
            observed_safe = world.observed_safe,
            therapist_signal = world.signal,
            observed_settled = world.settled,
            evidence_mass = params.witnessing_write_size * access,
        )
        update_life!(state, event, params)
        record_therapy_passages!(state, selected, session, params)
    end

    posttherapy = capture_readout(state, params)
    posttherapy_probe = fixed_probe_readout(state, params)
    posttherapy_counts = copy(cause_by_id(state, state.focal_cause_id).mandate_counts)
    post_offset = therapy_offset + params.therapy_sessions
    for (trial, world) in enumerate(schedule.post)
        event = WorldEvent(
            stage = :posttherapy_heldout,
            step = post_offset + trial,
            target_id = state.focal_cause_id,
            observed_safe = world.observed_safe,
            learn = false,
        )
        push!(heldout_loglik, update_life!(state, event, params))
    end

    final_objects = bank_objects(state)
    bank_identity_intact = initial_objects == final_objects
    melt_order = sort(collect(state.melt_sessions); by = last)
    metric = (
        seed = seed,
        architecture = architecture_label(state),
        focal_cause_id = state.focal_cause_id,
        n_causes = length(state.causes),
        childhood_written_reflexivity = state.childhood_written_reflexivity,
        childhood_root_safe = childhood_counts[SAFE_EVIDENCE],
        childhood_root_danger = childhood_counts[DANGER_EVIDENCE],
        childhood_structural_precision = childhood_precision,
        adult_root_safe = adult_counts[SAFE_EVIDENCE],
        adult_root_danger = adult_counts[DANGER_EVIDENCE],
        adult_capture = adult.capture,
        adult_captured = adult.capture >= params.capture_threshold,
        pretherapy_probe_revision = pretherapy_probe.revision,
        posttherapy_root_safe = posttherapy_counts[SAFE_EVIDENCE],
        posttherapy_root_danger = posttherapy_counts[DANGER_EVIDENCE],
        posttherapy_capture = posttherapy.capture,
        capture_drop = adult.capture - posttherapy.capture,
        therapy_melted = adult.capture - posttherapy.capture >= params.melt_capture_drop_threshold,
        posttherapy_probe_revision = posttherapy_probe.revision,
        probe_revision_change = posttherapy_probe.revision - pretherapy_probe.revision,
        witnessing_evidence_mass = state.witnessing_evidence_mass,
        heldout_mean_log_likelihood = mean(heldout_loglik),
        first_contact_order = join([string(pair.first) for pair in sort(collect(state.first_contacts); by = last)], ">"),
        melt_order = join([string(pair.first) for pair in melt_order], ">"),
        bank_identity_intact = bank_identity_intact,
    )
    return (state = state, metric = metric, initial_objects = initial_objects, final_objects = final_objects)
end

function safe_correlation(xs, ys)
    length(xs) < 2 && return 0.0
    (std(xs) <= EPS || std(ys) <= EPS) && return 0.0
    return cor(xs, ys)
end

mean_bool(rows, field::Symbol) = mean(getproperty(row, field) ? 1.0 : 0.0 for row in rows)

function theory_label(criteria_results)
    criteria_results === nothing && return "null"
    labels = [row.label for row in criteria_results.results if row.kind == "success"]
    any(==("falsified"), labels) && return "falsified"
    all(==("support"), labels) && return "support"
    any(==("weak_support"), labels) && return "weak_support"
    return "null"
end

function formation_rows(seed::Int, architecture::String, state::LifeState)
    return [(
        seed = seed,
        architecture = architecture,
        cause_id = cause.id,
        formation_event_id = string(get(cause.formation, "formation_event_id", "")),
        sim1_pathway = string(get(cause.formation, "sim1_pathway", "")),
        route = string(get(cause.formation, "route", "")),
        spawned = get(cause.formation, "spawned", false),
        written_reflexivity = cause.written_reflexivity,
        structural_precision_at_end_of_life = cause.structural_precision,
        root_safe_at_end_of_life = cause.mandate_counts[SAFE_EVIDENCE],
        root_danger_at_end_of_life = cause.mandate_counts[DANGER_EVIDENCE],
    ) for cause in state.causes]
end

function bank_audit_rows(run)
    rows = NamedTuple[]
    state = run.state
    cursor = 1
    for cause in state.causes
        for bank in ("relational_counts", "policy_counts", "mandate_counts")
            push!(rows, (
                seed = state.seed,
                architecture = architecture_label(state),
                owner = "cause_$(cause.id)",
                bank = bank,
                initial_object_id = run.initial_objects[cursor],
                final_object_id = run.final_objects[cursor],
                same_object = run.initial_objects[cursor] == run.final_objects[cursor],
            ))
            cursor += 1
        end
    end
    for bank in ("depth_posterior", "learned_coreg_mapping")
        push!(rows, (
            seed = state.seed,
            architecture = architecture_label(state),
            owner = "life_state",
            bank = bank,
            initial_object_id = run.initial_objects[cursor],
            final_object_id = run.final_objects[cursor],
            same_object = run.initial_objects[cursor] == run.final_objects[cursor],
        ))
        cursor += 1
    end
    return rows
end

function melt_rows(run)
    state = run.state
    rows = NamedTuple[]
    for cause in state.causes
        push!(rows, (
            seed = state.seed,
            architecture = architecture_label(state),
            cause_id = cause.id,
            formation_order = Int(get(cause.formation, "position_index", cause.id)),
            first_contact_session = get(state.first_contacts, cause.id, 0),
            melt_session = get(state.melt_sessions, cause.id, 0),
        ))
    end
    return rows
end

function write_timeline_svg(path::AbstractString, traces)
    ensure_dir(dirname(path))
    rows = [row for row in traces if row.architecture == "H1"]
    width, height = 960, 420
    max_step = isempty(rows) ? 1 : maximum(row.step for row in rows)
    x(row) = 60.0 + 840.0 * (row.step - 1) / max(max_step - 1, 1)
    y(row) = 350.0 - 270.0 * clamp(row.capture_after, 0.0, 1.0)
    points = join(["$(round(x(row); digits = 1)),$(round(y(row); digits = 1))" for row in rows], " ")
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="$width" height="$height" viewBox="0 0 $width $height">
      <rect width="100%" height="100%" fill="#fbfaf7"/>
      <text x="50" y="32" font-family="Arial" font-size="20" fill="#222">Sim 7 pilot: carried focal-cause capture across one life</text>
      <text x="50" y="54" font-family="Arial" font-size="12" fill="#555">Stage boundaries change the world schedule only; the plotted bank is never replaced.</text>
      <line x1="60" y1="350" x2="900" y2="350" stroke="#333"/>
      <line x1="60" y1="80" x2="60" y2="350" stroke="#333"/>
      <polyline points="$points" fill="none" stroke="#6f4e7c" stroke-width="3"/>
      <text x="420" y="390" font-family="Arial" font-size="12">life-event index</text>
      <text x="18" y="230" font-family="Arial" font-size="12" transform="rotate(-90 18 230)">capture</text>
    </svg>
    """
    open(path, "w") do io
        write(io, svg)
    end
end

function validate_step_a(config::ExperimentConfig)
    config.label == "pilot" || error("Sim 7 Step A accepts label: pilot only")
    config.seeds == collect(1001:1010) || error("Sim 7 Step A accepts pilot seeds 1001-1010 only; confirmatory seeds are forbidden")
end

function run_sim7_config(config::ExperimentConfig; config_path::Union{Nothing, AbstractString} = nothing, output_dir::Union{Nothing, AbstractString} = nothing)
    started = time()
    validate_step_a(config)
    params = params_from_config(config)
    Sim5.validate_params(params.sim5)
    outdir = output_dir === nothing ? normpath(joinpath(config.output_dir, config.experiment, "pilot")) : output_dir
    ensure_dir(outdir)
    ensure_dir(joinpath(outdir, "figures"))

    schedules = Dict(seed => world_schedule(seed, params) for seed in config.seeds)
    h1_runs = [simulate_life(seed, GraphDirection(ROOT_NODE), schedules[seed], params) for seed in config.seeds]
    h2_runs = [simulate_life(seed, GraphDirection(CONTEXT_NODE), schedules[seed], params) for seed in config.seeds]
    h1_metrics = [run.metric for run in h1_runs]
    h2_metrics = [run.metric for run in h2_runs]
    paired = [(
        seed = h1.seed,
        h1_heldout_mean_log_likelihood = h1.heldout_mean_log_likelihood,
        h2_heldout_mean_log_likelihood = h2.heldout_mean_log_likelihood,
        h1_minus_h2 = h1.heldout_mean_log_likelihood - h2.heldout_mean_log_likelihood,
        h1_wins = h1.heldout_mean_log_likelihood > h2.heldout_mean_log_likelihood,
    ) for (h1, h2) in zip(h1_metrics, h2_metrics)]

    carried_correlation = safe_correlation(
        [row.childhood_written_reflexivity for row in h1_metrics],
        [row.adult_capture for row in h1_metrics],
    )
    adult_capture_rate = mean_bool(h1_metrics, :adult_captured)
    therapy_melt_rate = mean_bool(h1_metrics, :therapy_melted)
    mean_capture_drop = mean(row.capture_drop for row in h1_metrics)
    mean_probe_revision_change = mean(row.probe_revision_change for row in h1_metrics)
    h1_advantage = mean(row.h1_minus_h2 for row in paired)
    h1_win_rate = mean(row.h1_wins ? 1.0 : 0.0 for row in paired)
    all_runs = vcat(h1_runs, h2_runs)
    identity_rate = mean(run.metric.bank_identity_intact ? 1.0 : 0.0 for run in all_runs)

    descriptive_orders = Dict{String, Int}()
    for row in h1_metrics
        descriptive_orders[row.melt_order] = get(descriptive_orders, row.melt_order, 0) + 1
    end

    summary = (
        experiment = "sim7",
        phase = "Step A pilot",
        config = config_snapshot(config),
        preregistration = (
            criteria_file = config.criteria_path,
            readouts_frozen_before_pilot = true,
            adult_capture = "Focal Sim 1-grown cause: carried written reflexivity, structural precision, and severity bank under the Sim 1 probe precision standard.",
            therapy_melt = "Adult-to-post-therapy capture drop on the same focal bank, with fixed safe witnessing writes routed through de-authored Sim 4 access.",
            model_comparison = "Mean frozen out-of-sample Bernoulli log likelihood on identical adult and post-therapy held-out world segments.",
            melt_order = "Descriptive only; no ordering criterion is evaluated.",
        ),
        metrics = (
            carried_capture = (
                childhood_written_reflexivity_adult_capture_correlation = carried_correlation,
                threshold = params.carried_correlation_threshold,
            ),
            adult_capture = (
                rate = adult_capture_rate,
                mean = mean(row.adult_capture for row in h1_metrics),
                threshold = params.capture_threshold,
            ),
            therapy_melt = (
                rate = therapy_melt_rate,
                mean_capture_drop = mean_capture_drop,
                mean_probe_revision_change = mean_probe_revision_change,
                mean_witnessing_evidence_mass = mean(row.witnessing_evidence_mass for row in h1_metrics),
            ),
            h2_model_comparison = (
                mean_h1_minus_h2_log_likelihood = h1_advantage,
                h1_win_rate = h1_win_rate,
            ),
            descriptive_melt_order = (
                counts = (; (Symbol(isempty(k) ? "no_melt" : "order_$(replace(k, ">" => "_"))") => v for (k, v) in sort(collect(descriptive_orders)))...),
                claim_status = "not_claimed_after_Sim4_falsification",
            ),
            audit = (
                bank_identity_rate = identity_rate,
                condition_branch_count = 0,
                root_bank_replacement_count = 0,
            ),
        ),
        state_audit = (
            formation = "Sim4.grow_stack called once per seed/model; its Sim1-grown arrays are retained by object identity.",
            adult = "Same cause arrays, depth posterior, and learned mapping mutated by update_life!.",
            therapy = "Same arrays mutated by update_life!; witnessing evidence increments the carried mandate/severity bank.",
            probe = "Learning disabled; reads the same arrays without replacement or manual posterior injection.",
            h1_h2_difference = "GraphDirection.depth_tilt_target constructor argument only.",
        ),
    )

    all_metrics = vcat(h1_metrics, h2_metrics)
    traces = reduce(vcat, [run.state.trace for run in all_runs]; init = NamedTuple[])
    formations = reduce(vcat, [formation_rows(run.state.seed, architecture_label(run.state), run.state) for run in all_runs]; init = NamedTuple[])
    audits = reduce(vcat, [bank_audit_rows(run) for run in all_runs]; init = NamedTuple[])
    melts = reduce(vcat, [melt_rows(run) for run in all_runs]; init = NamedTuple[])

    summary_path = joinpath(outdir, "summary.json")
    write_json(summary_path, summary)
    write_rows_csv(joinpath(outdir, "per_seed_metrics.csv"), all_metrics)
    write_rows_csv(joinpath(outdir, "model_comparison.csv"), paired)
    write_rows_csv(joinpath(outdir, "posterior_traces.csv"), traces)
    write_rows_csv(joinpath(outdir, "formation_events.csv"), formations)
    write_rows_csv(joinpath(outdir, "bank_audit.csv"), audits)
    write_rows_csv(joinpath(outdir, "melt_order_descriptive.csv"), melts)
    write_timeline_svg(joinpath(outdir, "figures", "timeline.svg"), [row for row in traces if row.seed == first(config.seeds)])

    criteria_results = nothing
    if !isnothing(config.criteria_path) && isfile(config.criteria_path)
        criteria_results = write_criteria_results(config.criteria_path, summary_path, joinpath(outdir, "criteria-results.json"))
    end
    result_label = theory_label(criteria_results)
    status = (
        implementation_passed = identity_rate == 1.0 && length(h1_metrics) == 10 && length(h2_metrics) == 10,
        theory_result = result_label,
        status = result_label in ("support", "weak_support") ? "pilot_complete" : "pilot_falsified",
        confirmatory_run_permitted = false,
    )
    write_json(joinpath(outdir, "status.json"), status)
    metadata = build_reproducibility_metadata(
        config;
        config_path = config_path,
        runtime_seconds = time() - started,
        repo_root = normpath(joinpath(@__DIR__, "..", "..", "..", "..", "..")),
        extra = (output_dir = abspath(outdir), phase = "pilot", confirmatory_seeds_run = false),
    )
    write_json(joinpath(outdir, "metadata.json"), metadata)
    return (output_dir = outdir, summary = summary, status = status, criteria_results = criteria_results)
end

end
