module ContextSplitRedescription44b

using Random
using Statistics
using Main.ContextSplitRedescription

export Config44b, Calibration44b, PILOT_44B_SEEDS, CONFIRM_44B_SEEDS,
    calibration_candidates, run_seed_44b, summarize_44b, verdicts_44b,
    saturation_guard, wiring_audit_44a

const PILOT_44B_SEEDS = collect(174701:174710)
const CONFIRM_44B_SEEDS = collect(174801:174820)
const ROOT_ARMS = (:witnessing, :open_field_informational,
    :regulation_only, :narrowed_contact)

Base.@kwdef struct Calibration44b
    id::String
    root_sessions::Int
    root_amplitude::Float64
    root_observation_sd::Float64
    contact_amplitude::Float64
    contact_sd::Float64
    evidence_scale::Float64 = 1.0
    safe_prior_mass::Float64 = 8.0
    full_prior_mass::Float64 = 1.0
    reduced_model_log_prior_penalty::Float64 = 1.20
end

Base.@kwdef struct Config44b
    base::ContextSplitRedescription.ContextSplitConfig =
        ContextSplitRedescription.ContextSplitConfig()
    calibration::Calibration44b
    saturation_upper::Float64 = 0.90
    witnessing_lower::Float64 = 0.65
    witnessing_upper::Float64 = 0.995
    dynamic_range_minimum::Float64 = 0.20
    baseline_reachable_rate::Float64 = 0.80
end

function calibration_candidates()
    return [
        Calibration44b(
            id = "44b-cal-01",
            root_sessions = 18,
            root_amplitude = 0.55,
            root_observation_sd = 0.90,
            contact_amplitude = 0.45,
            contact_sd = 0.90,
        ),
        Calibration44b(
            id = "44b-cal-02",
            root_sessions = 14,
            root_amplitude = 0.35,
            root_observation_sd = 1.00,
            contact_amplitude = 0.30,
            contact_sd = 1.00,
        ),
        Calibration44b(
            id = "44b-cal-03",
            root_sessions = 12,
            root_amplitude = 0.30,
            root_observation_sd = 1.05,
            contact_amplitude = 0.25,
            contact_sd = 1.05,
        ),
    ]
end

function root_world_44b(seed, calibration)
    rng = MersenneTwister(seed + 700_000)
    pattern = (1.00, 0.82, 0.65, 0.92)
    observations = [
        calibration.root_amplitude .* collect(pattern) .+
            calibration.root_observation_sd .* randn(rng, length(pattern))
        for _ in 1:calibration.root_sessions
    ]
    contacts = calibration.contact_amplitude .+
        calibration.contact_sd .* randn(rng, calibration.root_sessions)
    return (observations = observations, contacts = contacts)
end

function arm_structure(arm)
    profile = ContextSplitRedescription.arm_profile(arm)
    if arm == :witnessing
        return (field = profile.field, contact_precision = profile.contact,
            contact_root_link = true, graph = :identity_root)
    elseif arm == :open_field_informational
        return (field = profile.field, contact_precision = 0.0,
            contact_root_link = false, graph = :identity_root)
    elseif arm == :regulation_only
        return (field = profile.field, contact_precision = 0.0,
            contact_root_link = false, graph = :identity_root)
    elseif arm == :narrowed_contact
        return (field = profile.field, contact_precision = profile.contact,
            contact_root_link = true, graph = :identity_root)
    elseif arm == :matched_fixed_context
        return (field = profile.field, contact_precision = 0.0,
            contact_root_link = false, graph = :identity_root)
    elseif arm == :reversed_graph
        # The matched reversed graph gives bundle observations cue-local
        # parents and makes g their child. Thus p(y | g=+1) == p(y | g=-1);
        # both bundle and contact likelihood ratios cancel without changing
        # any observed marginal.
        return (field = profile.field, contact_precision = 0.0,
            contact_root_link = false, graph = :cue_local_root_child)
    end
    error("unknown 44b arm $arm")
end

geometric_breadth(field) = exp(mean(log(max(value, 1.0e-12))
    for value in field))

function infer_root_44b(data, arm, config)
    calibration = config.calibration
    structure = arm_structure(arm)
    log_odds = ContextSplitRedescription.logit(
        config.base.root_prior_positive)
    path = Float64[]
    bundle_path = Float64[]
    contact_path = Float64[]
    cumulative_bundle = 0.0
    cumulative_contact = 0.0
    pattern = (1.00, 0.82, 0.65, 0.92)
    for session in 1:calibration.root_sessions
        if structure.graph == :identity_root
            for channel in eachindex(pattern)
                observation = data.observations[session][channel]
                mean_positive = calibration.root_amplitude * pattern[channel]
                mean_negative = -mean_positive
                precision = calibration.evidence_scale *
                    structure.field[channel] /
                    calibration.root_observation_sd^2
                increment = precision * (
                    -0.5(observation - mean_positive)^2 +
                    0.5(observation - mean_negative)^2)
                log_odds += increment
                cumulative_bundle += increment
            end
        end
        if structure.contact_root_link
            breadth = geometric_breadth(structure.field)
            precision = calibration.evidence_scale *
                structure.contact_precision * breadth /
                calibration.contact_sd^2
            observation = data.contacts[session]
            increment = precision * (
                -0.5(observation - calibration.contact_amplitude)^2 +
                0.5(observation + calibration.contact_amplitude)^2)
            log_odds += increment
            cumulative_contact += increment
        end
        push!(bundle_path, cumulative_bundle)
        push!(contact_path, cumulative_contact)
        push!(path, ContextSplitRedescription.logistic(log_odds))
    end
    crossing = findfirst(>=(config.base.revision_probability), path)
    begun = findfirst(>=(config.base.revision_begun_probability), path)
    return (
        path = path,
        final = last(path),
        crossing = isnothing(crossing) ? calibration.root_sessions + 1 :
            crossing,
        begun = isnothing(begun) ? calibration.root_sessions + 1 : begun,
        cumulative_bundle_llr = cumulative_bundle,
        cumulative_contact_llr = cumulative_contact,
        bundle_path = bundle_path,
        contact_path = contact_path,
    )
end

function asymmetric_bernoulli_evidence(noncat, catastrophe,
        noncat_prior, catastrophe_prior)
    return ContextSplitRedescription.logbeta(noncat_prior + noncat,
        catastrophe_prior + catastrophe) -
        ContextSplitRedescription.logbeta(noncat_prior, catastrophe_prior)
end

function baseline_reduction_bayes(noncat, catastrophe, calibration)
    reduced = asymmetric_bernoulli_evidence(noncat, catastrophe,
        calibration.safe_prior_mass, 1.0)
    full = asymmetric_bernoulli_evidence(noncat, catastrophe,
        calibration.full_prior_mass, calibration.full_prior_mass)
    return reduced - full - calibration.reduced_model_log_prior_penalty
end

function imaginal_log_bayes(root_probability, calibration)
    reduced_safe_probability = 0.15 + 0.70root_probability
    full_safe_probability = 0.50
    return calibration.evidence_scale *
        log(reduced_safe_probability / full_safe_probability)
end

function doover_44b(seed, root, config)
    calibration = config.calibration
    rng = MersenneTwister(seed + 800_000)
    catastrophe_fraction = 0.03 .* rand(rng, calibration.root_sessions)
    noncat_fraction = 1 .- catastrophe_fraction
    baseline_path = Float64[]
    for session in 1:calibration.root_sessions
        push!(baseline_path, baseline_reduction_bayes(
            sum(noncat_fraction[1:session]),
            sum(catastrophe_fraction[1:session]), calibration))
    end
    threshold = config.base.reduction_log_bayes_threshold
    baseline_time = something(findfirst(>=(threshold), baseline_path),
        calibration.root_sessions + 1)

    insertion = min(root.begun, calibration.root_sessions)
    post_path = Float64[]
    for session in 1:calibration.root_sessions
        value = baseline_path[session]
        if session >= insertion
            readiness = root.path[insertion]
            value += config.base.doover_packets * config.base.imaginal_weight *
                imaginal_log_bayes(readiness, calibration)
        end
        push!(post_path, value)
    end
    post_time = something(findfirst(>=(threshold), post_path),
        calibration.root_sessions + 1)

    premature_session = 1
    premature_before = baseline_path[premature_session]
    premature_after = premature_before +
        config.base.doover_packets * config.base.imaginal_weight *
        imaginal_log_bayes(root.path[premature_session], calibration)
    premature_reversed = premature_after < premature_before
    premature_failed = premature_after < threshold
    shortening = baseline_time > calibration.root_sessions ? 0.0 :
        max(0.0, (baseline_time - post_time) / baseline_time)
    return (
        baseline_time = baseline_time,
        post_time = post_time,
        shortening = shortening,
        insertion = insertion,
        premature_before = premature_before,
        premature_after = premature_after,
        premature_failed = premature_failed,
        premature_reversed = premature_reversed,
    )
end

function run_seed_44b(seed; stage, config)
    structured = ContextSplitRedescription.generate_world(seed, true,
        config.base)
    no_structure = ContextSplitRedescription.generate_world(seed, false,
        config.base)
    structured_result = ContextSplitRedescription.model_tournament(
        structured, config.base)
    null_result = ContextSplitRedescription.model_tournament(
        no_structure, config.base)

    root_data = root_world_44b(seed, config.calibration)
    roots = Dict(arm => infer_root_44b(root_data, arm, config)
        for arm in ROOT_ARMS)
    fixed = infer_root_44b(root_data, :matched_fixed_context, config)
    reversed = infer_root_44b(root_data, :reversed_graph, config)
    doover = doover_44b(seed, roots[:witnessing], config)
    return (
        stage = String(stage),
        calibration_id = config.calibration.id,
        seed = seed,
        structured_split_selected =
            structured_result.selected == :context_split,
        null_split_selected = null_result.selected == :context_split,
        structured_split_margin = structured_result.split_heldout_margin,
        null_split_margin = null_result.split_heldout_margin,
        witnessing_final_root = roots[:witnessing].final,
        open_final_root = roots[:open_field_informational].final,
        regulation_final_root = roots[:regulation_only].final,
        narrowed_final_root = roots[:narrowed_contact].final,
        fixed_context_final_root = fixed.final,
        reversed_final_root = reversed.final,
        witnessing_time = roots[:witnessing].crossing,
        open_time = roots[:open_field_informational].crossing,
        regulation_time = roots[:regulation_only].crossing,
        narrowed_time = roots[:narrowed_contact].crossing,
        witnessing_begun = roots[:witnessing].begun,
        witnessing_bundle_llr = roots[:witnessing].cumulative_bundle_llr,
        witnessing_contact_llr = roots[:witnessing].cumulative_contact_llr,
        open_bundle_llr =
            roots[:open_field_informational].cumulative_bundle_llr,
        regulation_bundle_llr =
            roots[:regulation_only].cumulative_bundle_llr,
        narrowed_bundle_llr =
            roots[:narrowed_contact].cumulative_bundle_llr,
        baseline_reduction_time = doover.baseline_time,
        post_doover_reduction_time = doover.post_time,
        doover_insertion = doover.insertion,
        doover_shortening = doover.shortening,
        premature_log_bayes_before = doover.premature_before,
        premature_log_bayes_after = doover.premature_after,
        premature_failed = doover.premature_failed,
        premature_reversed = doover.premature_reversed,
        organization_register =
            "bundle(self,world,policy,outcome)+couplings+precisions+field_profile",
        carrier_register =
            "none; no independently parameterized substrate enters this experiment",
    )
end

meanfield(rows, field) = mean(Float64(getfield(row, field)) for row in rows)

function summarize_44b(rows)
    return (
        worlds = length(rows),
        structured_split_selected =
            count(row.structured_split_selected for row in rows),
        null_split_selected = count(row.null_split_selected for row in rows),
        mean_structured_split_margin =
            meanfield(rows, :structured_split_margin),
        mean_null_split_margin = meanfield(rows, :null_split_margin),
        mean_witnessing_final_root =
            meanfield(rows, :witnessing_final_root),
        mean_open_final_root = meanfield(rows, :open_final_root),
        mean_regulation_final_root =
            meanfield(rows, :regulation_final_root),
        mean_narrowed_final_root = meanfield(rows, :narrowed_final_root),
        mean_fixed_context_final_root =
            meanfield(rows, :fixed_context_final_root),
        mean_reversed_final_root = meanfield(rows, :reversed_final_root),
        mean_doover_shortening = meanfield(rows, :doover_shortening),
        baseline_reachable = count(
            row.baseline_reduction_time <=
                calibration_sessions(rows) for row in rows),
        premature_failures = count(row.premature_failed for row in rows),
        premature_reversals = count(row.premature_reversed for row in rows),
    )
end

function calibration_sessions(rows)
    calibration = only(filter(candidate ->
        candidate.id == first(rows).calibration_id, calibration_candidates()))
    return calibration.root_sessions
end

function saturation_guard(rows, config)
    summary = summarize_44b(rows)
    finals = [
        summary.mean_witnessing_final_root,
        summary.mean_open_final_root,
        summary.mean_regulation_final_root,
        summary.mean_narrowed_final_root,
        summary.mean_fixed_context_final_root,
        summary.mean_reversed_final_root,
    ]
    return (
        regulation_informative =
            summary.mean_regulation_final_root <= config.saturation_upper,
        fixed_context_not_saturated =
            summary.mean_fixed_context_final_root <= config.saturation_upper,
        reversed_not_saturated =
            summary.mean_reversed_final_root <= config.saturation_upper,
        witnessing_informative =
            config.witnessing_lower <=
                summary.mean_witnessing_final_root <=
                config.witnessing_upper,
        dynamic_range = maximum(finals) - minimum(finals) >=
            config.dynamic_range_minimum,
        baseline_reduction_askable =
            summary.baseline_reachable >=
                ceil(Int, config.baseline_reachable_rate * length(rows)),
        passed = (
            summary.mean_regulation_final_root <= config.saturation_upper &&
            summary.mean_fixed_context_final_root <= config.saturation_upper &&
            summary.mean_reversed_final_root <= config.saturation_upper &&
            config.witnessing_lower <=
                summary.mean_witnessing_final_root <=
                config.witnessing_upper &&
            maximum(finals) - minimum(finals) >=
                config.dynamic_range_minimum &&
            summary.baseline_reachable >=
                ceil(Int, config.baseline_reachable_rate * length(rows))
        ),
    )
end

function verdicts_44b(rows)
    summary = summarize_44b(rows)
    required = ceil(Int, 0.80length(rows))
    allowed = floor(Int, 0.20length(rows))
    criterion_1 = summary.structured_split_selected >= required &&
        summary.null_split_selected <= allowed
    criterion_2 = summary.mean_structured_split_margin >= 0.05
    high = mean((row.witnessing_final_root + row.open_final_root) / 2
        for row in rows)
    low = mean((row.regulation_final_root + row.narrowed_final_root) / 2
        for row in rows)
    high_pair = mean(abs(row.witnessing_final_root -
        row.open_final_root) for row in rows)
    low_pair = mean(abs(row.regulation_final_root -
        row.narrowed_final_root) for row in rows)
    criterion_3 = high_pair <= 0.12 && low_pair <= 0.12 &&
        high - low >= 0.30
    criterion_4 = summary.mean_doover_shortening >= 0.20 &&
        summary.premature_failures >= required &&
        summary.premature_reversals >= required
    return (
        criterion_1_selectivity = criterion_1,
        criterion_2_heldout_margin = criterion_2,
        criterion_3_derived_ordering = criterion_3,
        criterion_4_doover_timing = criterion_4,
        overall = criterion_1 && criterion_2 && criterion_3 && criterion_4,
        ordering_high_minus_low = high - low,
        witnessing_open_mean_difference = high_pair,
        regulation_narrowed_mean_difference = low_pair,
    )
end

function wiring_audit_44a(seed)
    config = ContextSplitRedescription.ContextSplitConfig()
    data = ContextSplitRedescription.root_world(seed, config)
    rows = NamedTuple[]
    for arm in (ROOT_ARMS..., :matched_fixed_context, :reversed_graph)
        profile = ContextSplitRedescription.arm_profile(arm)
        bundle = 0.0
        contact = 0.0
        for session in 1:config.root_sessions
            for channel in eachindex(ContextSplitRedescription.CUES)
                observation = data.observations[session][channel]
                precision = profile.field[channel] /
                    config.root_observation_sd^2
                bundle += precision * (
                    -0.5(observation - 1.0)^2 +
                    0.5(observation + 1.0)^2)
            end
            contact_observation = data.contacts[session]
            contact_precision = abs(profile.contact) / config.contact_sd^2
            positive_mean = profile.contact >= 0 ? 0.90 : -0.90
            contact += contact_precision * (
                -0.5(contact_observation - positive_mean)^2 +
                0.5(contact_observation + positive_mean)^2)
        end
        final = ContextSplitRedescription.logistic(
            ContextSplitRedescription.logit(config.root_prior_positive) +
            bundle + contact)
        push!(rows, (arm = String(arm), bundle_llr = bundle,
            contact_llr = contact, total_llr = bundle + contact,
            final_root = final))
    end
    return rows
end

end
