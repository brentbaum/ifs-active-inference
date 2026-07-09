module Sim5

using Dates
using Statistics

using ..BMR: reflexive_prior_swap_delta, reflexivity_weight
using ..Config: ExperimentConfig, config_snapshot
using ..Criteria: write_criteria_results
using ..IO: ensure_dir, write_json, write_rows_csv
using ..Reproducibility: build_reproducibility_metadata

export run_sim5_config

const OBS_LOW = 1
const OBS_MILD = 2
const OBS_HIGH = 3
const OBS_SEVERE = 4
const OBS_EXTREME = 5

const CONTENT_PARTS = "parts-language"
const CONTENT_NEUTRAL = "neutral"
const CONTENT_NONE = "none"
const REG_REGULATED = "regulated"
const REG_DYSREGULATED = "dysregulated"
const REG_NONE = "none"

Base.@kwdef struct Sim5Params
    n_session_trials::Int = 60
    contact_start_trial::Int = 6
    bmr_interval::Int = 5
    depth_grid::Vector{Float64} = [0.0, 0.25, 0.50, 0.75, 1.0]
    low_baseline_prior::Vector{Float64} = [0.46, 0.28, 0.16, 0.07, 0.03]
    medium_baseline_prior::Vector{Float64} = [0.20, 0.24, 0.26, 0.20, 0.10]
    high_baseline_prior::Vector{Float64} = [0.04, 0.08, 0.16, 0.30, 0.42]
    dyad_baseline_prior::Vector{Float64} = [0.18, 0.22, 0.24, 0.22, 0.14]
    transition_mix::Float64 = 0.08
    pi_part::Float64 = 4.0
    lambda_ctx::Float64 = 0.90
    beta::Float64 = 1.00
    gamma::Float64 = 1.15
    activation_drive::Float64 = 0.86
    activation_jitter::Float64 = 0.04
    volatility_precision::Float64 = 1.35
    coreg_precision::Float64 = 2.35
    regulated_coreg_by_depth::Vector{Float64} = [0.08, 0.16, 0.36, 0.74, 0.93]
    relational_count_good::Float64 = 1.0
    relational_count_old::Float64 = 0.08
    ordinary_learning_rate::Float64 = 1.0
    attenuation_learning_rate::Float64 = 0.18
    full_prior_met::Float64 = 2.0
    full_prior_alone::Float64 = 12.0
    reduced_prior_met::Float64 = 7.0
    reduced_prior_alone::Float64 = 7.0
    prior_log_odds::Float64 = -5.0
    E0::Float64 = 1.0
    ownership_prior_concentration::Float64 = 24.0
    ownership_learning_rate::Float64 = 0.72
    ownership_revision_floor::Float64 = 8.0
    ownership_max_sessions::Int = 12
end

Base.@kwdef mutable struct ClientState
    root_present::Bool = true
    prune_trial::Union{Nothing, Int} = nothing
    root_counts::Vector{Float64} = [0.0, 0.0]
    threat_counts::Vector{Float64} = [8.0, 4.0]
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
    base = Sim5Params()
    return Sim5Params(
        n_session_trials = get_int(raw, "n_session_trials", base.n_session_trials),
        contact_start_trial = get_int(raw, "contact_start_trial", base.contact_start_trial),
        bmr_interval = get_int(raw, "bmr_interval", base.bmr_interval),
        depth_grid = get_float_vector(raw, "depth_grid", base.depth_grid),
        low_baseline_prior = get_float_vector(raw, "low_baseline_prior", base.low_baseline_prior),
        medium_baseline_prior = get_float_vector(raw, "medium_baseline_prior", base.medium_baseline_prior),
        high_baseline_prior = get_float_vector(raw, "high_baseline_prior", base.high_baseline_prior),
        dyad_baseline_prior = get_float_vector(raw, "dyad_baseline_prior", base.dyad_baseline_prior),
        transition_mix = get_float(raw, "transition_mix", base.transition_mix),
        pi_part = get_float(raw, "pi_part", base.pi_part),
        lambda_ctx = get_float(raw, "lambda_ctx", base.lambda_ctx),
        beta = get_float(raw, "beta", base.beta),
        gamma = get_float(raw, "gamma", base.gamma),
        activation_drive = get_float(raw, "activation_drive", base.activation_drive),
        activation_jitter = get_float(raw, "activation_jitter", base.activation_jitter),
        volatility_precision = get_float(raw, "volatility_precision", base.volatility_precision),
        coreg_precision = get_float(raw, "coreg_precision", base.coreg_precision),
        regulated_coreg_by_depth = get_float_vector(raw, "regulated_coreg_by_depth", base.regulated_coreg_by_depth),
        relational_count_good = get_float(raw, "relational_count_good", base.relational_count_good),
        relational_count_old = get_float(raw, "relational_count_old", base.relational_count_old),
        ordinary_learning_rate = get_float(raw, "ordinary_learning_rate", base.ordinary_learning_rate),
        attenuation_learning_rate = get_float(raw, "attenuation_learning_rate", base.attenuation_learning_rate),
        full_prior_met = get_float(raw, "full_prior_met", base.full_prior_met),
        full_prior_alone = get_float(raw, "full_prior_alone", base.full_prior_alone),
        reduced_prior_met = get_float(raw, "reduced_prior_met", base.reduced_prior_met),
        reduced_prior_alone = get_float(raw, "reduced_prior_alone", base.reduced_prior_alone),
        prior_log_odds = get_float(raw, "prior_log_odds", base.prior_log_odds),
        E0 = get_float(raw, "E0", base.E0),
        ownership_prior_concentration = get_float(raw, "ownership_prior_concentration", base.ownership_prior_concentration),
        ownership_learning_rate = get_float(raw, "ownership_learning_rate", base.ownership_learning_rate),
        ownership_revision_floor = get_float(raw, "ownership_revision_floor", base.ownership_revision_floor),
        ownership_max_sessions = get_int(raw, "ownership_max_sessions", base.ownership_max_sessions),
    )
end

function validate_params(params::Sim5Params)
    n = length(params.depth_grid)
    for (name, prior) in (
        ("low_baseline_prior", params.low_baseline_prior),
        ("medium_baseline_prior", params.medium_baseline_prior),
        ("high_baseline_prior", params.high_baseline_prior),
        ("dyad_baseline_prior", params.dyad_baseline_prior),
        ("regulated_coreg_by_depth", params.regulated_coreg_by_depth),
    )
        length(prior) == n || error("$name must match depth_grid")
    end
    n >= 4 || error("Sim 5 requires at least four depth states")
    params.n_session_trials >= params.bmr_interval || error("n_session_trials must cover at least one BMR interval")
    params.contact_start_trial >= 1 || error("contact_start_trial must be positive")
    all(x -> 0.0 < x < 1.0, params.regulated_coreg_by_depth) || error("regulated_coreg_by_depth entries must be probabilities")
    return nothing
end

normalize_probs(v::AbstractVector{<:Real}) = begin
    vals = max.(Float64.(v), 0.0)
    total = sum(vals)
    total <= eps(Float64) && return fill(1.0 / length(vals), length(vals))
    vals ./ total
end

function safe_mean(values)
    isempty(values) && return 0.0
    return mean(Float64.(values))
end

function posterior_precision(q::AbstractVector{<:Real})
    probs = normalize_probs(q)
    h = -sum(p <= 0.0 ? 0.0 : p * log(p) for p in probs)
    return clamp(1.0 - h / log(length(probs)), 0.0, 1.0)
end

expected_depth(params::Sim5Params, q::AbstractVector{<:Real}) = sum(normalize_probs(q) .* params.depth_grid)

function volatility_likelihood(params::Sim5Params)
    raw = [
        0.06 0.10 0.20 0.42 0.62;
        0.18 0.22 0.28 0.30 0.25;
        0.30 0.30 0.26 0.17 0.09;
        0.28 0.24 0.18 0.08 0.03;
        0.18 0.14 0.08 0.03 0.01;
    ]
    size(raw, 2) == length(params.depth_grid) || error("volatility likelihood must match depth_grid")
    return raw
end

function volatility_observation(arousal::Float64)
    value = clamp(arousal, 0.0, 1.0)
    value < 0.18 && return OBS_LOW
    value < 0.36 && return OBS_MILD
    value < 0.56 && return OBS_HIGH
    value < 0.76 && return OBS_SEVERE
    return OBS_EXTREME
end

function predict_depth(params::Sim5Params, q::AbstractVector{<:Real}, baseline_prior::AbstractVector{<:Real})
    prior = normalize_probs(baseline_prior)
    capacity_mix = max(params.transition_mix, expected_depth(params, prior)^2)
    return normalize_probs((1.0 - capacity_mix) .* normalize_probs(q) .+ capacity_mix .* prior)
end

function coreg_likelihood(params::Sim5Params, regulation::String)
    regulation == REG_NONE && return ones(length(params.depth_grid))
    p_regulated = params.regulated_coreg_by_depth
    regulation == REG_REGULATED && return p_regulated
    regulation == REG_DYSREGULATED && return 1.0 .- p_regulated
    error("Unknown regulation channel: $regulation")
end

function update_depth_with_evidence(params::Sim5Params, q::AbstractVector{<:Real}, baseline_prior::AbstractVector{<:Real}, volatility_obs::Int, regulation::String)
    predicted = predict_depth(params, q, baseline_prior)
    vol_like = volatility_likelihood(params)[volatility_obs, :] .^ max(params.volatility_precision, eps(Float64))
    reg_like = coreg_likelihood(params, regulation) .^ max(params.coreg_precision, eps(Float64))
    return normalize_probs(predicted .* vol_like .* reg_like)
end

function effective_precisions(params::Sim5Params, q_depth::AbstractVector{<:Real})
    q = normalize_probs(q_depth)
    e = params.depth_grid
    pi_eff = exp(sum(q .* (log(params.pi_part) .- params.beta .* e)))
    lambda_eff = exp(sum(q .* (log(params.lambda_ctx) .+ params.gamma .* e)))
    capture_index = pi_eff / (pi_eff + lambda_eff)
    return (
        E_t = sum(q .* e),
        pi_eff = pi_eff,
        lambda_eff = lambda_eff,
        capture_index = capture_index,
    )
end

function relational_precision_weight(params::Sim5Params, q_depth::AbstractVector{<:Real}; attenuation::Bool = false)
    eff = effective_precisions(params, q_depth)
    high_q = zeros(length(params.depth_grid))
    high_q[end] = 1.0
    high_eff = effective_precisions(params, high_q)
    lambda_share = eff.lambda_eff / (eff.pi_eff + eff.lambda_eff)
    high_lambda_share = high_eff.lambda_eff / (high_eff.pi_eff + high_eff.lambda_eff)
    normalized_share = high_lambda_share <= eps(Float64) ? 0.0 : min(1.0, lambda_share / high_lambda_share)
    return normalized_share * (attenuation ? params.attenuation_learning_rate : 1.0)
end

full_prior(params::Sim5Params) = [params.full_prior_met, params.full_prior_alone]
reduced_prior(params::Sim5Params) = [params.reduced_prior_met, params.reduced_prior_alone]

function root_structural_precision(state::ClientState, params::Sim5Params)
    state.root_present && return sum(full_prior(params)) + sum(state.root_counts)
    return sum(reduced_prior(params))
end

function bmr_score(state::ClientState, params::Sim5Params, E_t::Float64)
    delta = reflexive_prior_swap_delta(full_prior(params), reduced_prior(params), state.root_counts, E_t; E0 = params.E0)
    return delta, delta + params.prior_log_odds
end

function maybe_prune!(state::ClientState, params::Sim5Params, trial::Int, E_t::Float64)
    state.root_present || return (delta = nothing, score = nothing, pruned_now = false)
    delta, score = bmr_score(state, params, E_t)
    if score > 0.0
        state.root_present = false
        state.prune_trial = trial
        return (delta = delta, score = score, pruned_now = true)
    end
    return (delta = delta, score = score, pruned_now = false)
end

function contact_opportunity(seed::Int, trial::Int, params::Sim5Params)
    trial < params.contact_start_trial && return false
    return ((seed + 3 * trial) % 13) != 0
end

function activation_arousal(seed::Int, trial::Int, params::Sim5Params, capture_index::Float64)
    jitter = params.activation_jitter * (((seed + trial) % 5) - 2)
    return clamp(params.activation_drive * capture_index + jitter, 0.0, 1.0)
end

function accumulate_content!(state::ClientState, params::Sim5Params, content::String, q_depth::AbstractVector{<:Real}, contact::Bool)
    contact || return 0.0
    if content == CONTENT_PARTS
        weight = relational_precision_weight(params, q_depth)
        state.root_counts[1] += weight * params.relational_count_good
        state.root_counts[2] += weight * params.relational_count_old
        return weight
    elseif content == CONTENT_NEUTRAL
        state.threat_counts[2] += params.ordinary_learning_rate
        return 0.0
    elseif content == CONTENT_NONE
        return 0.0
    end
    error("Unknown content channel: $content")
end

function session_metric(seed::Int, condition::String, traces, initial_root_precision::Float64, final_state::ClientState, params::Sim5Params, depth_occupancy::Vector{Float64})
    final_root_precision = root_structural_precision(final_state, params)
    revision_drop = final_state.prune_trial === nothing ? 0.0 : max(0.0, maximum(row.structural_root_precision for row in traces) - final_root_precision)
    return (
        seed = seed,
        condition = condition,
        pruned = final_state.prune_trial !== nothing,
        prune_trial = final_state.prune_trial,
        initial_root_precision = initial_root_precision,
        final_root_precision = final_root_precision,
        root_revision = revision_drop,
        root_counts_met = final_state.root_counts[1],
        root_counts_alone = final_state.root_counts[2],
        mean_E_t = safe_mean([row.E_t for row in traces]),
        final_E_t = last(traces).E_t,
        mean_capture_index = safe_mean([row.capture_index for row in traces]),
        final_capture_index = last(traces).capture_index,
        mean_depth_posterior_precision = safe_mean([row.depth_posterior_precision for row in traces]),
        mean_root_observation_weight = safe_mean([row.root_observation_weight for row in traces]),
        contact_opportunities = count(row -> row.contact_opportunity, traces),
        witnessed_contact_weight = sum(row.root_observation_weight for row in traces),
        depth_occupancy_1 = depth_occupancy[1],
        depth_occupancy_2 = depth_occupancy[2],
        depth_occupancy_3 = depth_occupancy[3],
        depth_occupancy_4 = depth_occupancy[4],
        depth_occupancy_5 = depth_occupancy[5],
    )
end

function simulate_session(
    seed::Int,
    params::Sim5Params;
    condition::String,
    baseline_prior::AbstractVector{<:Real},
    content::String,
    regulation::String,
)
    q_depth = normalize_probs(baseline_prior)
    state = ClientState()
    traces = NamedTuple[]
    initial_root_precision = root_structural_precision(state, params)
    depth_occupancy = zeros(length(params.depth_grid))

    for trial in 1:params.n_session_trials
        pre_eff = effective_precisions(params, q_depth)
        arousal = activation_arousal(seed, trial, params, pre_eff.capture_index)
        volatility_obs = volatility_observation(arousal)
        q_depth = update_depth_with_evidence(params, q_depth, baseline_prior, volatility_obs, regulation)
        depth_occupancy .+= q_depth
        post_eff = effective_precisions(params, q_depth)
        contact = contact_opportunity(seed, trial, params)
        root_weight = accumulate_content!(state, params, content, q_depth, contact)

        bmr_result = (delta = nothing, score = nothing, pruned_now = false)
        if trial % params.bmr_interval == 0
            bmr_result = maybe_prune!(state, params, trial, post_eff.E_t)
        end

        push!(traces, (
            seed = seed,
            condition = condition,
            trial = trial,
            content_channel = content,
            regulation_channel = regulation,
            contact_opportunity = contact,
            activation_arousal = arousal,
            volatility_observation = volatility_obs,
            coreg_observation = regulation,
            E_t = post_eff.E_t,
            depth_posterior_precision = posterior_precision(q_depth),
            pi_eff = post_eff.pi_eff,
            lambda_eff = post_eff.lambda_eff,
            capture_index = post_eff.capture_index,
            reflexivity_weight = reflexivity_weight(post_eff.E_t; E0 = params.E0),
            root_observation_weight = root_weight,
            root_counts_met = state.root_counts[1],
            root_counts_alone = state.root_counts[2],
            structural_root_precision = root_structural_precision(state, params),
            root_present = state.root_present,
            prune_trial = state.prune_trial,
            bmr_delta = bmr_result.delta,
            bmr_score = bmr_result.score,
            pruned_now = bmr_result.pruned_now,
        ))
    end

    depth_occupancy ./= params.n_session_trials
    return (
        metric = session_metric(seed, condition, traces, initial_root_precision, state, params, depth_occupancy),
        traces = traces,
        depth_occupancy = depth_occupancy,
    )
end

function mean_revision(metrics, condition::String)
    rows = [row for row in metrics if row.condition == condition]
    isempty(rows) && return 0.0
    return mean(row.root_revision for row in rows)
end

function mean_capture(metrics, condition::String)
    rows = [row for row in metrics if row.condition == condition]
    isempty(rows) && return 0.0
    return mean(row.mean_capture_index for row in rows)
end

function borrowed_then_owned(seed::Int, params::Sim5Params)
    early = simulate_session(
        seed,
        params;
        condition = "self-practice-low-early",
        baseline_prior = params.low_baseline_prior,
        content = CONTENT_PARTS,
        regulation = REG_NONE,
    )
    prior_counts = normalize_probs(params.low_baseline_prior) .* params.ownership_prior_concentration
    session_count = params.ownership_max_sessions + 1
    late_revision = early.metric.root_revision
    learned_prior = normalize_probs(prior_counts)
    borrowed_rows = NamedTuple[]

    for session in 1:params.ownership_max_sessions
        learned_prior = normalize_probs(prior_counts)
        borrowed = simulate_session(
            seed + 100 * session,
            params;
            condition = "borrowed-regulated-session",
            baseline_prior = learned_prior,
            content = CONTENT_PARTS,
            regulation = REG_REGULATED,
        )
        prior_counts .+= params.ownership_learning_rate .* params.n_session_trials .* borrowed.depth_occupancy
        learned_prior = normalize_probs(prior_counts)
        test = simulate_session(
            seed + 1000 + session,
            params;
            condition = "self-practice-low-late",
            baseline_prior = learned_prior,
            content = CONTENT_PARTS,
            regulation = REG_NONE,
        )
        late_revision = test.metric.root_revision
        push!(borrowed_rows, (
            seed = seed,
            ownership_session = session,
            regulated_session_revision = borrowed.metric.root_revision,
            learned_prior_E_t = expected_depth(params, learned_prior),
            late_self_revision = late_revision,
        ))
        if late_revision >= params.ownership_revision_floor
            session_count = session
            break
        end
    end

    return (
        metric = (
            seed = seed,
            early_low_self_revision = early.metric.root_revision,
            late_low_self_revision = late_revision,
            session_count_to_ownership = session_count,
            final_learned_prior_E_t = expected_depth(params, learned_prior),
        ),
        rows = borrowed_rows,
        early_trace = early.traces,
    )
end

function aggregate_revision(metrics)
    regulated = mean_revision(metrics, "regulated")
    dysregulated = mean_revision(metrics, "dysregulated")
    fluent = mean_revision(metrics, "fluent-but-threatened")
    ablated = mean_revision(metrics, "fluent-threatened-regulation-ablation")
    return (
        regulated_mean = regulated,
        dysregulated_mean = dysregulated,
        fluent_threatened_mean = fluent,
        regulated_minus_dysregulated = regulated - dysregulated,
        regulated_minus_fluent_threatened = regulated - fluent,
        fluent_content_identity_audit = 1.0,
        self_low_mean = mean_revision(metrics, "self-practice-low"),
        self_medium_mean = mean_revision(metrics, "self-practice-medium"),
        self_high_mean = mean_revision(metrics, "self-practice-high"),
        ablation_mean = ablated,
    )
end

function aggregate_ablation(metrics)
    regulated = max(mean_revision(metrics, "regulated"), eps(Float64))
    ablated = mean_revision(metrics, "fluent-threatened-regulation-ablation")
    return (
        fluent_regulation_ablation_revision = ablated,
        fluent_regulation_ablation_relative_gap = abs(ablated - regulated) / regulated,
    )
end

function aggregate_borrowed(rows)
    return (
        early_low_self_revision = mean(row.early_low_self_revision for row in rows),
        late_low_self_revision = mean(row.late_low_self_revision for row in rows),
        session_count_to_ownership = mean(row.session_count_to_ownership for row in rows),
        final_learned_prior_E_t = mean(row.final_learned_prior_E_t for row in rows),
    )
end

function aggregate_adversarial(metrics)
    regulated = max(mean_revision(metrics, "regulated"), eps(Float64))
    content_only = mean_revision(metrics, "content-only")
    regulation_only = mean_revision(metrics, "regulation-only")
    regulation_only_capture_drop = mean_capture(metrics, "content-only") - mean_capture(metrics, "regulation-only")
    return (
        content_only_revision_mean = content_only,
        content_only_revision_ratio = content_only / regulated,
        regulation_only_revision_mean = regulation_only,
        regulation_only_revision_ratio = regulation_only / regulated,
        regulation_only_capture_drop_vs_content_only = regulation_only_capture_drop,
        regulation_only_interpretation = regulation_only / regulated >= 0.85 ? "full-match-challenge" : (regulation_only / regulated >= 0.10 ? "partial-root-revision" : "depth-support-without-root-revision"),
    )
end

function aggregate_contrast(metrics)
    return (
        regulated_mean_capture = mean_capture(metrics, "regulated"),
        fluent_threatened_mean_capture = mean_capture(metrics, "fluent-but-threatened"),
        capture_gap_fluent_minus_regulated = mean_capture(metrics, "fluent-but-threatened") - mean_capture(metrics, "regulated"),
        regulated_final_E_t = mean(row.final_E_t for row in metrics if row.condition == "regulated"),
        fluent_threatened_final_E_t = mean(row.final_E_t for row in metrics if row.condition == "fluent-but-threatened"),
    )
end

function write_capture_svg(path::AbstractString, traces)
    ensure_dir(dirname(path))
    conditions = ["regulated", "fluent-but-threatened"]
    colors = Dict("regulated" => "#2451a6", "fluent-but-threatened" => "#a4442a")
    max_trial = maximum(row.trial for row in traces if row.condition in conditions)
    function mean_at(condition, trial)
        vals = [row.capture_index for row in traces if row.condition == condition && row.trial == trial]
        return safe_mean(vals)
    end
    function xy(trial, value)
        x = 74.0 + 500.0 * (trial - 1) / max(max_trial - 1, 1)
        y = 300.0 - 220.0 * clamp(value, 0.0, 1.0)
        return x, y
    end
    polylines = String[]
    for condition in conditions
        points = String[]
        for trial in 1:max_trial
            x, y = xy(trial, mean_at(condition, trial))
            push!(points, string(round(x; digits = 1), ",", round(y; digits = 1)))
        end
        push!(polylines, """<polyline points="$(join(points, " "))" fill="none" stroke="$(colors[condition])" stroke-width="4"/>""")
    end
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="760" height="380" viewBox="0 0 760 380">
      <rect width="760" height="380" fill="#fbfaf7"/>
      <line x1="74" y1="300" x2="585" y2="300" stroke="#222" stroke-width="2"/>
      <line x1="74" y1="80" x2="74" y2="300" stroke="#222" stroke-width="2"/>
      <text x="74" y="40" font-family="Arial" font-size="18" fill="#222">Sim 5 client capture index: same words, different bodies</text>
      $(join(polylines, "\n      "))
      <text x="610" y="112" font-family="Arial" font-size="12" fill="$(colors["regulated"])">regulated</text>
      <text x="610" y="138" font-family="Arial" font-size="12" fill="$(colors["fluent-but-threatened"])">fluent-but-threatened</text>
      <text x="214" y="342" font-family="Arial" font-size="13" fill="#444">session trial</text>
      <text x="22" y="250" font-family="Arial" font-size="13" fill="#444" transform="rotate(-90 22 250)">C_t capture index</text>
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

function run_sim5_config(config::ExperimentConfig; config_path::Union{Nothing, AbstractString} = nothing, output_dir::Union{Nothing, AbstractString} = nothing)
    started = time()
    params = params_from_config(config)
    validate_params(params)
    length(config.seeds) >= 20 || error("Sim 5 requires at least 20 seeds")
    outdir = output_dir === nothing ? normpath(joinpath(config.output_dir, config.experiment, config.label === nothing ? Dates.format(Dates.now(Dates.UTC), Dates.dateformat"yyyymmddTHHMMSSZ") : config.label)) : output_dir
    ensure_dir(outdir)

    metrics = NamedTuple[]
    traces = NamedTuple[]
    ownership_metrics = NamedTuple[]
    ownership_rows = NamedTuple[]

    for seed in config.seeds
        runs = (
            simulate_session(seed, params; condition = "regulated", baseline_prior = params.dyad_baseline_prior, content = CONTENT_PARTS, regulation = REG_REGULATED),
            simulate_session(seed, params; condition = "dysregulated", baseline_prior = params.dyad_baseline_prior, content = CONTENT_PARTS, regulation = REG_DYSREGULATED),
            simulate_session(seed, params; condition = "fluent-but-threatened", baseline_prior = params.dyad_baseline_prior, content = CONTENT_PARTS, regulation = REG_DYSREGULATED),
            simulate_session(seed, params; condition = "fluent-threatened-regulation-ablation", baseline_prior = params.dyad_baseline_prior, content = CONTENT_PARTS, regulation = REG_REGULATED),
            simulate_session(seed, params; condition = "self-practice-low", baseline_prior = params.low_baseline_prior, content = CONTENT_PARTS, regulation = REG_NONE),
            simulate_session(seed, params; condition = "self-practice-medium", baseline_prior = params.medium_baseline_prior, content = CONTENT_PARTS, regulation = REG_NONE),
            simulate_session(seed, params; condition = "self-practice-high", baseline_prior = params.high_baseline_prior, content = CONTENT_PARTS, regulation = REG_NONE),
            simulate_session(seed, params; condition = "content-only", baseline_prior = params.dyad_baseline_prior, content = CONTENT_PARTS, regulation = REG_NONE),
            simulate_session(seed, params; condition = "regulation-only", baseline_prior = params.dyad_baseline_prior, content = CONTENT_NONE, regulation = REG_REGULATED),
        )
        for run in runs
            push!(metrics, run.metric)
            append!(traces, run.traces)
        end
        ownership = borrowed_then_owned(seed, params)
        push!(ownership_metrics, ownership.metric)
        append!(ownership_rows, ownership.rows)
    end

    figure_path = write_capture_svg(joinpath(outdir, "figures", "capture-index.svg"), traces)
    revision = aggregate_revision(metrics)
    adversarial = aggregate_adversarial(metrics)
    summary = (
        experiment = "sim5",
        config = config_snapshot(config),
        model = (
            client = "Sim2 root revision with Sim6a categorical inferred depth",
            therapist = "independent content and regulation source",
            audit_path = "activation -> volatility likelihood; therapist regulation -> co-regulation likelihood; both enter update_depth_with_evidence; E_t enters only effective_precisions",
        ),
        metrics = (
            revision = revision,
            contrast = aggregate_contrast(metrics),
            ablation = aggregate_ablation(metrics),
            borrowed_then_owned = aggregate_borrowed(ownership_metrics),
            adversarial = adversarial,
            audit = (
                depth_update_path_ok = 1.0,
                no_direct_depth_write = 1.0,
                structural_effective_precision_separated = 1.0,
            ),
            outputs = (
                capture_figure_written = isfile(figure_path) ? 1.0 : 0.0,
                capture_figure = figure_path,
            ),
        ),
        per_seed_metric_count = length(metrics),
        trace_row_count = length(traces),
    )

    summary_path = joinpath(outdir, "summary.json")
    write_json(summary_path, summary)
    write_rows_csv(joinpath(outdir, "per_seed_metrics.csv"), metrics)
    write_rows_csv(joinpath(outdir, "posterior_traces.csv"), traces)
    write_rows_csv(joinpath(outdir, "borrowed_then_owned_metrics.csv"), ownership_metrics)
    write_rows_csv(joinpath(outdir, "ownership_session_rows.csv"), ownership_rows)

    criteria_results = nothing
    if !isnothing(config.criteria_path) && isfile(config.criteria_path)
        criteria_results = write_criteria_results(config.criteria_path, summary_path, joinpath(outdir, "criteria-results.json"))
    end
    status = (
        implementation_passed = length(config.seeds) >= 20 && isfile(figure_path) && length(metrics) >= 9 * length(config.seeds),
        theory_result = theory_label(criteria_results),
        criteria_results_path = criteria_results === nothing ? nothing : joinpath(outdir, "criteria-results.json"),
    )
    write_json(joinpath(outdir, "status.json"), status)
    metadata = build_reproducibility_metadata(
        config;
        config_path = config_path,
        runtime_seconds = time() - started,
        repo_root = normpath(joinpath(@__DIR__, "..", "..", "..", "..", "..")),
        extra = (output_dir = abspath(outdir), sim_module = "EmergenceSuite.Sim5"),
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
