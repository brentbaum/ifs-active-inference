#!/usr/bin/env julia

include(joinpath(@__DIR__, "run_stage_b.jl"))
using Random
using Statistics
using SHA
using Serialization
using Printf

const D_STAGE_C_COMMIT = "effd3e81c80d9c9f89ab4b2688081f9beb1867ef"
const D_PREREG_HASH =
    "5abf2be5eb6d004ca399caa59919dd58bd66cb5de2aa948e8c27ddbe07ca677d"
const D_SEED_FIRST = 713204
const D_SEED_LAST = 713403
const D_LESION_SEEDS = collect(713204:713263)
const D_SENSITIVITY_SEEDS = collect(713204:713233)
const D_NEIGHBORHOOD_DRAW_SEEDS = collect(713204:713283)
const D_NEIGHBORHOOD_WORLD_SEEDS = collect(713204:713223)
const D_LESIONS = (
    :context_split_unavailable,
    :field_scalar,
    :registration_removed,
    :partner_model_collapsed,
    :dyad_protector_severed,
    :freeze_ordinary_learning,
    :trust_single_forecast,
)
const D_SIGNATURES = (
    "S1", "S2", "S3", "S4", "S5",
    "S6", "S7", "S8", "S9", "S10",
)
const D_CRITERION_INDEX = Dict(
    1 => 1, 2 => 2, 3 => 1, 4 => 1, 5 => 1,
    6 => 1, 7 => 2, 8 => 2, 9 => 2, 10 => 1,
)
const D_PREDICT_DISAPPEAR = Dict(
    :context_split_unavailable => Set(["S4", "S6"]),
    :field_scalar => Set(["S3", "S5"]),
    :registration_removed => Set(["S8"]),
    :partner_model_collapsed => Set(["S9", "S10"]),
    :dyad_protector_severed => Set(["S10"]),
    :freeze_ordinary_learning => Set(["S1"]),
    :trust_single_forecast => Set(["S9"]),
)
const D_SHARED_CONSTANTS = (
    :avoidance_cost, :bayes_reliability, :competence_risk_weight,
    :context_complexity_penalty, :context_transition_mix,
    :dyad_learning_rate, :dyad_packet_mass, :dyad_regulated_floor,
    :dyad_regulated_span, :field_broadcast_mix,
    :field_context_precision, :field_learning_rate,
    :field_narrowing_strength, :field_part_precision,
    :field_relational_precision, :freeze_low_control_boundary,
    :freeze_no_control_attenuation, :freeze_overwhelm_boundary,
    :freeze_write_precision, :history_cost_sd,
    :history_favorable_cost, :history_favorable_success,
    :history_learning_rate, :history_root_positive_rate,
    :history_unfavorable_cost, :history_unfavorable_success,
    :hope_value, :imaginal_floor, :imaginal_span,
    :outcome_risk_weight, :partner_adverse_probability,
    :partner_neutral_probability, :partner_risk_weight,
    :partner_trustworthy_probability, :permission_temperature,
    :policy_failure_cost, :probability_guard, :refusal_cost,
    :registration_increment, :rng_history_offset,
    :root_evidence_weight, :training_events,
)
const D_INTEGER_CONSTANTS = Set((:rng_history_offset, :training_events))
const D_NEIGHBORHOOD_CONSTANTS = (
    :bayes_reliability, :history_learning_rate, :root_evidence_weight,
    :field_learning_rate, :outcome_risk_weight, :dyad_packet_mass,
)
const D_FROZEN_PATHS = [
    "projects/emergence-suite/continuous/src/ModelOrganism.jl",
    "projects/emergence-suite/continuous/src/model_organism",
    "projects/emergence-suite/continuous/genome.toml",
    "projects/emergence-suite/continuous/organism-genome.md",
    ["projects/emergence-suite/continuous/configurations/" *
        @sprintf("assay-%02d.toml", assay) for assay in 1:10]...,
    "projects/emergence-suite/continuous/results/model_organism/configuration-grammar.md",
    ["projects/emergence-suite/continuous/results/model_organism/assays/" *
        "$assay/analysis-plan.md" for assay in 1:10]...,
]

d_lesion_root() = joinpath(ModelOrganism.RESULTS_ROOT, "lesions")
d_neighborhood_root() =
    joinpath(ModelOrganism.RESULTS_ROOT, "neighborhood")

function d_verify_reference!(genome)
    head = readchomp(`git rev-parse HEAD`)
    head == D_STAGE_C_COMMIT ||
        error("Stage D blocked: HEAD $head is not $D_STAGE_C_COMMIT")
    changed = readchomp(Cmd(vcat(["git", "diff", "--name-only",
        FREEZE_COMMIT, "--"], D_FROZEN_PATHS)))
    isempty(changed) ||
        error("Stage D blocked: frozen reference inputs changed:\n$changed")
    verify_identity!(genome)
    ModelOrganism.verify_precalibration_lock()
    manifest_path =
        joinpath(ModelOrganism.RESULTS_ROOT, "stage-d-manifest.json")
    manifest = read(manifest_path, String)
    occursin(D_PREREG_HASH, manifest) ||
        error("Stage D blocked: preregistration hash absent")
    prereg_path = joinpath(d_lesion_root(), "preregistration.md")
    bytes2hex(sha256(read(prereg_path))) == D_PREREG_HASH ||
        error("Stage D blocked: preregistration changed")
    return true
end

function d_check_seeds(seeds)
    isempty(seeds) && error("Stage D seed set is empty")
    minimum(seeds) >= D_SEED_FIRST ||
        error("Stage D attempted pre-block seed")
    maximum(seeds) <= D_SEED_LAST ||
        error("Stage D attempted seed above escrow")
    return seeds
end

function d_rows(assay, seeds, genome)
    d_check_seeds(seeds)
    config = load_configuration(ModelOrganism.config_path(assay))
    rows = NamedTuple[]
    for (index, seed) in enumerate(seeds)
        generated = run_assay(assay, seed, genome, config)
        if assay == 7
            for row in generated
                row.kind == :analytic && index > 1 && continue
                push!(rows, row)
            end
        else
            append!(rows, generated)
        end
    end
    return rows
end

function d_signature_result(assay, rows, genome)
    if assay == 1
        successes = count(row -> row.property_holds, rows)
        estimate = successes / length(rows)
        interval = wilson_interval(successes, length(rows))
        return (signature = "S1", assay = 1,
            label = "joint-boundary predicate agreement",
            metric = estimate, interval_low = interval[1],
            interval_high = interval[2],
            passed = estimate == 1.0, finite = true,
            decision_rule = "exact agreement = 1.0",
            auxiliary_rate = nothing, auxiliary_interval_low = nothing,
            auxiliary_interval_high = nothing,
            details = Dict("domain_points" => length(rows)))
    end
    criteria, _ = ANALYZERS[assay](rows, genome)
    selected = criteria[D_CRITERION_INDEX[assay]]
    estimate = selected["estimate"]
    valid = estimate isa Number && isfinite(Float64(estimate))
    value = valid ? Float64(estimate) : 0.0
    interval = selected["interval_95"]
    passed = selected["passed"] === true && valid
    if assay == 7 && valid
        passed = value + ModelOrganism.g(genome, :static_tolerance) >=
            ModelOrganism.g(genome, :assay7_timing_margin)
    end
    auxiliary_rate = assay == 4 ?
        get(selected["details"], "success_rate", nothing) : nothing
    auxiliary_interval = assay == 4 ?
        get(selected["details"], "success_rate_interval",
            [nothing, nothing]) : [nothing, nothing]
    return (signature = D_SIGNATURES[assay], assay = assay,
        label = selected["label"], metric = value,
        interval_low = interval[1], interval_high = interval[2],
        passed = passed, finite = valid,
        auxiliary_rate = auxiliary_rate,
        auxiliary_interval_low = auxiliary_interval[1],
        auxiliary_interval_high = auxiliary_interval[2],
        decision_rule = selected["decision_rule"],
        details = selected["details"])
end

function d_reference_metrics(seeds, genome)
    results = NamedTuple[]
    for assay in 1:10
        assay_seeds = assay == 1 ? seeds[1:1] : seeds
        rows = d_rows(assay, assay_seeds, genome)
        push!(results, d_signature_result(assay, rows, genome))
    end
    return results
end

function d_replace(row, replacement::NamedTuple)
    return merge(row, replacement)
end

function d_assay1_ordinary(seed, genome)
    boundary_o = ModelOrganism.g(genome, :freeze_overwhelm_boundary)
    boundary_c = ModelOrganism.g(genome, :freeze_low_control_boundary)
    delta = ModelOrganism.g(genome, :property_grid_delta)
    high = ModelOrganism.g(genome, :property_grid_high_offset)
    levels_o = (0.0, boundary_o - delta, boundary_o,
        boundary_o + high, 1.0)
    levels_c = (0.0, boundary_c - delta, boundary_c,
        boundary_c + high, 1.0)
    rows = NamedTuple[]
    for overwhelm in levels_o, control in levels_c
        state = neutral_state(genome)
        expected = overwhelm >= boundary_o && control <= boundary_c
        observation = overwhelm > control
        old = state.posterior[:root_now]
        ModelOrganism.update_posterior!(state, :root_now, observation,
            ModelOrganism.g(genome, :bayes_reliability), genome;
            event_kind = :experiment,
            event_id = "lesion:ordinary:$seed:$overwhelm:$control")
        precision = abs(state.posterior[:root_now] - old)
        push!(rows, (seed = seed, overwhelm = overwhelm,
            control = control, written = false, expected = expected,
            precision = precision, attenuation_edge = control == 0.0,
            property_holds = !expected,
            avoidance_available =
                ModelOrganism.g(genome, :avoidance_cost) <
                ModelOrganism.g(genome, :policy_failure_cost)))
    end
    return rows
end

function d_assay3_scalar(seed, genome)
    rng = ModelOrganism.field_rng(seed, genome)
    rows = NamedTuple[]
    regimes = ((:quiet_narrowing, 0.0, 0.0),
        (:blended_capture, 1.0, 0.0),
        (:self_led_witnessing, 0.0, 1.0),
        (:known_urgent_threat, 1.0, 1.0))
    for (regime, dominance, depth) in regimes
        observations = [(dominance +
                ModelOrganism.g(genome, :regime_observation_sd) * randn(rng),
            depth + ModelOrganism.g(genome, :regime_observation_sd) *
                randn(rng))
            for _ in 1:Int(ModelOrganism.g(genome, :regime_observations))]
        scalar_prediction =
            mean((first(x) + last(x)) / 2 for x in observations)
        scalar_regimes = (:quiet_narrowing, :blended_capture,
            :self_led_witnessing, :known_urgent_threat)
        scalar_locations = (0.0, 0.5, 0.5, 1.0)
        distances = abs.(collect(scalar_locations) .- scalar_prediction)
        predicted = scalar_regimes[argmin(distances)]
        loss_1d = (scalar_prediction - dominance)^2 +
            (scalar_prediction - depth)^2
        scalar_truth = (dominance + depth) / 2
        push!(rows, (seed = seed, regime = regime,
            dominance = dominance, depth = depth,
            correct_2d = predicted == regime,
            loss_2d = loss_1d, loss_1d = loss_1d,
            scalar_truth = scalar_truth))
    end
    return rows
end

function d_assay4_no_context(seed, genome)
    rng = ModelOrganism.world_rng(seed, genome)
    evidence = rand(rng, Int(ModelOrganism.g(genome, :episodes))) .<
        ModelOrganism.g(genome, :bayes_reliability)
    rows = NamedTuple[]
    for arm in (:witnessing, :matched_exposure, :reversed_graph)
        state = ModelOrganism.seeded_state(seed, genome)
        initial = state.posterior[:root_now]
        treated = ModelOrganism.g(genome, :cue_initial_belief)
        untreated = treated
        identity_cross = 0
        threat_cross = 0
        for episode in eachindex(evidence)
            if arm == :matched_exposure
                ModelOrganism.update_root!(state, evidence[episode],
                    ModelOrganism.g(genome, :root_evidence_weight), genome;
                    event_id = "lesion:no-context:$seed:$episode")
            end
            treated += evidence[episode] ?
                ModelOrganism.g(genome, :cue_positive_step) :
                -ModelOrganism.g(genome, :cue_negative_step)
            untreated = ModelOrganism.g(genome, :cue_initial_belief) +
                ModelOrganism.g(genome, :cue_transfer_weight) *
                (state.posterior[:root_now] - initial)
            identity_cross == 0 &&
                state.posterior[:root_now] >=
                    ModelOrganism.g(genome, :root_revision_begin) &&
                (identity_cross = episode)
            threat_cross == 0 &&
                treated >= ModelOrganism.g(
                    genome, :root_revision_begin) &&
                (threat_cross = episode)
        end
        push!(rows, (seed = seed, arm = arm,
            root_revision = state.posterior[:root_now] - initial,
            root_revised = state.posterior[:root_now] >=
                ModelOrganism.g(genome, :root_revision_begin),
            untreated_transfer = untreated -
                ModelOrganism.g(genome, :cue_initial_belief),
            identity_cross = identity_cross, threat_cross = threat_cross,
            identity_before_threat = identity_cross > 0 &&
                (threat_cross == 0 || identity_cross < threat_cross)))
    end
    return rows
end

function d_assay5_scalar(seed, genome)
    rng = ModelOrganism.field_rng(seed, genome)
    evidence = rand(rng, Int(ModelOrganism.g(genome, :episodes))) .<
        ModelOrganism.g(genome, :bayes_reliability)
    rows = NamedTuple[]
    for regulation in (false, true), evidence_present in (false, true)
        state = ModelOrganism.seeded_state(seed, genome)
        initial = state.posterior[:root_now]
        errors = Dict(channel => abs(randn(rng))
            for channel in ModelOrganism.FIELD_CHANNELS)
        ModelOrganism.update_precision_field!(
            state, errors, regulation, genome)
        uptake = mean(values(state.field))
        if evidence_present
            for episode in eachindex(evidence)
                ModelOrganism.update_root!(state, evidence[episode],
                    uptake, genome;
                    event_id =
                        "lesion:scalar-field:$seed:$episode")
            end
        end
        push!(rows, (seed = seed, regulation = regulation,
            evidence_present = evidence_present,
            root_change = state.posterior[:root_now] - initial,
            uptake = uptake))
    end
    return rows
end

function d_recover_family_no_context(observations, genome)
    n = length(observations)
    corr_time = cor(collect(1:n), observations)
    alternating = mean(abs.(observations[1:2:end] .-
        observations[2:2:end]))
    max_jump = maximum(abs.(diff(observations)))
    if std(observations) <
            ModelOrganism.g(genome, :classifier_global_sd)
        return :global_downweight
    elseif alternating >
            ModelOrganism.g(genome, :classifier_alternating_gap)
        return :cue_local
    elseif abs(corr_time) >
            ModelOrganism.g(genome, :classifier_drift_correlation) &&
            max_jump <
            ModelOrganism.g(genome, :classifier_drift_jump_ceiling)
        return :continuous_drift
    end
    return :change_point
end

function d_assay6_no_context(seed, genome)
    families = (:global_downweight, :cue_local, :context_split,
        :continuous_drift, :change_point)
    rows = NamedTuple[]
    for family in families
        observations =
            ModelOrganism.generator_family(seed, family, genome)
        scores = ModelOrganism.context_model_scores(
            observations, genome)
        delete!(scores, :context_split)
        recovered = d_recover_family_no_context(observations, genome)
        sorted_scores = sort(collect(values(scores)))
        margin = sorted_scores[2] - sorted_scores[1]
        push!(rows, (seed = seed, generating_family = family,
            recovered_family = recovered, diagonal = recovered == family,
            context_split_selected = false,
            heldout_margin = margin,
            complexity_audit = length(scores) == 4))
    end
    return rows
end

function d_assay8_registration_removed(seed, genome)
    rows = NamedTuple[]
    favorable = ModelOrganism.POLICY_NAMES[
        mod1(seed, length(ModelOrganism.POLICY_NAMES))]
    state = ModelOrganism.seeded_state(
        seed, genome; favorable_policy = favorable)
    selected = ModelOrganism.select_policy(state, genome)
    for nominal_registration in (false, true)
        arm = deepcopy(state)
        initial = arm.posterior[:relational_prior]
        for episode in 1:Int(ModelOrganism.g(genome, :episodes))
            ModelOrganism.update_registration!(arm, true, false, genome;
                event_id =
                    "lesion:registration:$seed:$episode")
        end
        push!(rows, (seed = seed, favorable_policy = favorable,
            selected_policy = selected,
            selection_tracks = selected == favorable,
            registration = nominal_registration,
            relational_change =
                arm.posterior[:relational_prior] - initial,
            learned_cost = arm.policy_cost[selected],
            learned_reliability =
                arm.policy_reliability[selected]))
    end
    return rows
end

function d_assay9_collapsed(seed, genome; single_forecast = false)
    rows = NamedTuple[]
    base = ModelOrganism.seeded_state(seed, genome; partner = :neutral)
    snapshot = copy(base.posterior)
    low = ModelOrganism.protector_permission(
        base, ModelOrganism.g(genome, :low_stakes), genome)
    high = ModelOrganism.protector_permission(
        base, ModelOrganism.g(genome, :high_stakes), genome)
    push!(rows, (seed = seed, kind = :invariant,
        partner = :neutral, recovered = true,
        stakes_separated = low >= high,
        posterior_unchanged = snapshot == base.posterior,
        transfer_local = true,
        competence = base.posterior[:co_protection],
        obsolete_shift = 0.0, sign_prediction_match = true))
    neutral = ModelOrganism.g(genome, :neutral_probability)
    margin = ModelOrganism.g(genome, :partner_classification_margin)
    band = ModelOrganism.g(genome, :partner_neutral_band)
    for partner in (:trustworthy, :neutral, :adverse)
        generated_partner = single_forecast ? partner : :neutral
        if single_forecast
            state = neutral_state(genome)
            history = generate_history(
                seed, genome; partner = generated_partner)
            for event in history
                ModelOrganism.update_posterior!(state,
                    :outcome_forecast, event.tolerated_positive,
                    ModelOrganism.g(genome, :bayes_reliability),
                    genome; event_kind = :development,
                    event_id =
                        "lesion:single-forecast:$(event.id)")
            end
            forecast = state.posterior[:outcome_forecast]
            competence = forecast
        else
            state = ModelOrganism.seeded_state(
                seed, genome; partner = generated_partner)
            forecast = state.posterior[:partner_trustworthy]
            competence = state.posterior[:co_protection]
        end
        recovered = partner == :trustworthy ?
            forecast > neutral + margin :
            partner == :adverse ? forecast < neutral - margin :
            neutral - band <= forecast <= neutral + band
        push!(rows, (seed = seed, kind = :learned_history,
            partner = partner, recovered = recovered,
            stakes_separated = true, posterior_unchanged = true,
            transfer_local = true, competence = competence,
            obsolete_shift = 0.0, sign_prediction_match = false))
    end
    return rows
end

function d_single_forecast_permission(state, stakes, genome;
        obsolete = false)
    forecast = state.posterior[:outcome_forecast]
    total_weight =
        ModelOrganism.g(genome, :outcome_risk_weight) +
        ModelOrganism.g(genome, :competence_risk_weight) +
        ModelOrganism.g(genome, :partner_risk_weight)
    risk = total_weight * (1 - forecast)
    obsolete && (risk = forecast * risk + (1 - forecast))
    allow = ModelOrganism.g(genome, :hope_value) - stakes * risk
    refuse = -ModelOrganism.g(genome, :refusal_cost)
    return ModelOrganism.logistic((allow - refuse) /
        ModelOrganism.g(genome, :permission_temperature))
end

function d_assay10_lesioned(seed, genome;
        collapsed_partner = false, severed = false,
        single_forecast = false)
    rows = NamedTuple[]
    for (index, disposition) in enumerate(
            (:trustworthy, :neutral, :adverse))
        rng = ModelOrganism.partner_rng(seed +
            Int(ModelOrganism.g(genome, :rng_substream_stride)) *
                index, genome)
        emitting = collapsed_partner ? :neutral : disposition
        probability = ModelOrganism.partner_probability(emitting, genome)
        outcomes = rand(rng, Int(ModelOrganism.g(genome, :episodes))) .<
            probability
        for scaffold in (:coupled, :decoupled)
            state = neutral_state(genome)
            permission_episode = 0
            root_episode = 0
            initial_root = state.posterior[:root_now]
            for episode in eachindex(outcomes)
                signal = outcomes[episode] ? 1 : 4
                dyad = ModelOrganism.update_dyad!(
                    state, signal, outcomes[episode], genome)
                route_open = scaffold == :coupled && !severed
                if route_open
                    for packet in 1:dyad.packets
                        variables = single_forecast ?
                            (:outcome_forecast,) :
                            (:partner_trustworthy, :co_protection,
                                :outcome_forecast)
                        for variable in variables
                            ModelOrganism.update_posterior!(state,
                                variable, outcomes[episode],
                                ModelOrganism.g(
                                    genome, :bayes_reliability),
                                genome; event_kind = :experiment,
                                event_id =
                                    "lesion:assay10:$seed:$episode:$packet:$variable")
                        end
                    end
                end
                permission = single_forecast ?
                    d_single_forecast_permission(state,
                        ModelOrganism.g(genome, :high_stakes),
                        genome; obsolete = true) :
                    ModelOrganism.protector_permission(
                        state, ModelOrganism.g(genome, :high_stakes),
                        genome; obsolete = true)
                if permission >=
                        ModelOrganism.g(genome, :permission_threshold)
                    permission_episode == 0 &&
                        (permission_episode = episode)
                    ModelOrganism.update_root!(state,
                        outcomes[episode], dyad.field_weight, genome;
                        event_id =
                            "lesion:assay10:root:$seed:$episode")
                else
                    ModelOrganism.update_registration!(
                        state, true, true, genome;
                        event_id =
                            "lesion:assay10:registration:$seed:$episode")
                end
                root_episode == 0 &&
                    state.posterior[:root_now] >=
                        ModelOrganism.g(genome, :root_revision_begin) &&
                    (root_episode = episode)
            end
            push!(rows, (seed = seed, disposition = disposition,
                scaffold = scaffold,
                positive_without_scaffold = false,
                permission_episode = permission_episode,
                root_episode = root_episode,
                permission_before_root = permission_episode > 0 &&
                    (root_episode == 0 ||
                        permission_episode < root_episode),
                descent = state.posterior[:root_now] >=
                    ModelOrganism.g(genome, :root_revision_begin),
                root_change =
                    state.posterior[:root_now] - initial_root))
        end
    end
    state = neutral_state(genome)
    initial = state.posterior[:root_now]
    for episode in 1:Int(ModelOrganism.g(genome, :episodes))
        ModelOrganism.update_posterior!(state,
            :partner_trustworthy, true,
            ModelOrganism.g(genome, :bayes_reliability), genome;
            event_kind = :experiment,
            event_id = "lesion:positive-only:$seed:$episode")
    end
    push!(rows, (seed = seed, disposition = :trustworthy,
        scaffold = :none, positive_without_scaffold = true,
        permission_episode = 0, root_episode = 0,
        permission_before_root = false, descent = false,
        root_change = state.posterior[:root_now] - initial))
    return rows
end

function d_lesion_rows(lesion, assay, seeds, genome)
    lesion in D_LESIONS || error("unknown lesion $lesion")
    lesion_seeds = assay == 1 ? seeds[1:1] : seeds
    if lesion == :freeze_ordinary_learning && assay == 1
        return d_assay1_ordinary(first(lesion_seeds), genome)
    elseif lesion == :field_scalar && assay == 3
        return reduce(vcat,
            (d_assay3_scalar(seed, genome) for seed in lesion_seeds))
    elseif lesion == :context_split_unavailable && assay == 4
        return reduce(vcat,
            (d_assay4_no_context(seed, genome)
                for seed in lesion_seeds))
    elseif lesion == :field_scalar && assay == 5
        return reduce(vcat,
            (d_assay5_scalar(seed, genome) for seed in lesion_seeds))
    elseif lesion == :registration_removed && assay == 8
        return reduce(vcat,
            (d_assay8_registration_removed(seed, genome)
                for seed in lesion_seeds))
    elseif lesion == :partner_model_collapsed && assay == 9
        return reduce(vcat,
            (d_assay9_collapsed(seed, genome)
                for seed in lesion_seeds))
    elseif lesion == :trust_single_forecast && assay == 9
        return reduce(vcat,
            (d_assay9_collapsed(seed, genome;
                single_forecast = true) for seed in lesion_seeds))
    elseif lesion == :partner_model_collapsed && assay == 10
        return reduce(vcat,
            (d_assay10_lesioned(seed, genome;
                collapsed_partner = true) for seed in lesion_seeds))
    elseif lesion == :dyad_protector_severed && assay == 10
        return reduce(vcat,
            (d_assay10_lesioned(seed, genome;
                severed = true) for seed in lesion_seeds))
    elseif lesion == :trust_single_forecast && assay == 10
        return reduce(vcat,
            (d_assay10_lesioned(seed, genome;
                single_forecast = true) for seed in lesion_seeds))
    end
    rows = d_rows(assay, lesion_seeds, genome)
    if lesion == :context_split_unavailable && assay == 6
        return reduce(vcat,
            (d_assay6_no_context(seed, genome)
                for seed in lesion_seeds))
    end
    return rows
end

function d_run_lesions(genome)
    metric_rows = NamedTuple[]
    score_rows = NamedTuple[]
    reference = d_reference_metrics(D_LESION_SEEDS, genome)
    for result in reference
        push!(metric_rows, (lesion = :reference,
            signature = result.signature, assay = result.assay,
            predicted = :reference, metric = result.metric,
            interval_low = result.interval_low,
            interval_high = result.interval_high,
            auxiliary_rate = result.auxiliary_rate,
            auxiliary_interval_low = result.auxiliary_interval_low,
            auxiliary_interval_high = result.auxiliary_interval_high,
            observed_survival = result.passed,
            prediction_hit = true, finite = result.finite,
            decision_rule = result.decision_rule))
    end
    for lesion in D_LESIONS
        hits = 0
        for assay in 1:10
            rows = d_lesion_rows(
                lesion, assay, D_LESION_SEEDS, genome)
            result = d_signature_result(assay, rows, genome)
            disappear = result.signature in
                D_PREDICT_DISAPPEAR[lesion]
            hit = disappear ? !result.passed : result.passed
            hits += hit
            push!(metric_rows, (lesion = lesion,
                signature = result.signature, assay = assay,
                predicted = disappear ? :disappear : :survive,
                metric = result.metric,
                interval_low = result.interval_low,
                interval_high = result.interval_high,
                auxiliary_rate = result.auxiliary_rate,
                auxiliary_interval_low =
                    result.auxiliary_interval_low,
                auxiliary_interval_high =
                    result.auxiliary_interval_high,
                observed_survival = result.passed,
                prediction_hit = hit, finite = result.finite,
                decision_rule = result.decision_rule))
        end
        interval = wilson_interval(hits, 10)
        push!(score_rows, (lesion = lesion, hits = hits, total = 10,
            hit_rate = hits / 10, interval_low = interval[1],
            interval_high = interval[2],
            predicted_disappear = join(sort(collect(
                D_PREDICT_DISAPPEAR[lesion])), ";"),
            observed_disappear = join(sort(String[row.signature
                for row in metric_rows if row.lesion == lesion &&
                    !row.observed_survival]), ";")))
    end
    return metric_rows, score_rows
end

function d_copy_genome(genome, changes::Dict{Symbol,Float64}, tag)
    values = copy(genome.values)
    for (name, value) in changes
        values[name] = value
    end
    fingerprint = join(["$(name)=$(values[name])"
        for name in sort(collect(keys(values)); by = String)], ";")
    harness_hash = "HARNESS-" *
        bytes2hex(sha256(codeunits(fingerprint)))
    harness_hash == genome.sha256 &&
        error("perturbed harness genome retained frozen identity")
    return Genome(genome.id * ":harness:" * tag, genome.schema_version,
        values, genome.rationales, genome.path, harness_hash)
end

function d_perturbed_genome(genome, constant, factor)
    original = ModelOrganism.g(genome, constant)
    value = original * factor
    constant in D_INTEGER_CONSTANTS &&
        (value = max(1.0, round(value)))
    return d_copy_genome(genome, Dict(constant => value),
        "$(constant):$(factor)"), value
end

function d_run_sensitivity(genome)
    reference = Dict(result.signature => result
        for result in d_reference_metrics(D_SENSITIVITY_SEEDS, genome))
    rows = NamedTuple[]
    constant_summary = NamedTuple[]
    for constant in D_SHARED_CONSTANTS
        paired_noncausal = constant == :rng_history_offset
        if paired_noncausal
            low_genome, high_genome = genome, genome
            low_value = high_value =
                ModelOrganism.g(genome, constant)
        else
            low_genome, low_value =
                d_perturbed_genome(genome, constant, 0.95)
            high_genome, high_value =
                d_perturbed_genome(genome, constant, 1.05)
        end
        resolved = !paired_noncausal && low_value != high_value
        low = Dict(result.signature => result for result in
            d_reference_metrics(D_SENSITIVITY_SEEDS, low_genome))
        high = Dict(result.signature => result for result in
            d_reference_metrics(D_SENSITIVITY_SEEDS, high_genome))
        material_count = 0
        affected = String[]
        for signature in D_SIGNATURES
            ref = reference[signature].metric
            main_change = resolved ?
                (high[signature].metric - low[signature].metric) /
                    max(abs(ref), 1e-9) : 0.0
            ref_aux = reference[signature].auxiliary_rate
            low_aux = low[signature].auxiliary_rate
            high_aux = high[signature].auxiliary_rate
            auxiliary_change = resolved && ref_aux !== nothing ?
                (high_aux - low_aux) / max(abs(ref_aux), 1e-9) : 0.0
            elasticity = abs(auxiliary_change) > abs(main_change) ?
                auxiliary_change : main_change
            material = resolved && abs(elasticity) >= 0.10
            material_count += material
            material && push!(affected, signature)
            push!(rows, (constant = constant, signature = signature,
                reference_value = ModelOrganism.g(genome, constant),
                low_value = low_value, high_value = high_value,
                reference_metric = ref,
                low_metric = low[signature].metric,
                high_metric = high[signature].metric,
                reference_auxiliary_rate = ref_aux,
                low_auxiliary_rate = low_aux,
                high_auxiliary_rate = high_aux,
                main_fractional_change = main_change,
                auxiliary_fractional_change = auxiliary_change,
                central_fractional_change = elasticity,
                material = material, resolved = resolved,
                paired_noncausal = paired_noncausal))
        end
        clusters = Set{Symbol}()
        for signature in affected
            index = parse(Int, signature[2:end])
            push!(clusters, index <= 2 ? :formation_persistence :
                index <= 6 ? :field_context :
                index == 7 ? :imaginal_timing : :protection_dyad)
        end
        push!(constant_summary, (constant = constant,
            resolved = resolved, material_signature_count = material_count,
            affected_signatures = join(affected, ";"),
            affected_cluster_count = length(clusters),
            crosses_clusters = length(clusters) >= 2,
            paired_noncausal = paired_noncausal))
    end
    resolvable = filter(row -> row.resolved, constant_summary)
    multi = count(row -> row.material_signature_count >= 2, resolvable)
    cross = count(row -> row.crosses_clusters, resolvable)
    constrained = !isempty(resolvable) &&
        multi / length(resolvable) >= 0.25 && cross >= 1
    summary = Dict(
        "classification" => constrained ? "constrained" : "block-diagonal",
        "shared_constants" => length(D_SHARED_CONSTANTS),
        "resolvable_constants" => length(resolvable),
        "multi_signature_constants" => multi,
        "multi_signature_fraction" =>
            isempty(resolvable) ? 0.0 : multi / length(resolvable),
        "cross_cluster_constants" => cross,
        "paired_noncausal_constants" =>
            [String(row.constant) for row in constant_summary
                if row.paired_noncausal],
        "material_threshold" => 0.10,
        "perturbation_factors" => [0.95, 1.05],
        "worlds" => length(D_SENSITIVITY_SEEDS),
    )
    return rows, constant_summary, summary
end

function d_neighborhood_genome(genome, draw_seed)
    rng = Xoshiro(UInt64(draw_seed +
        Int(ModelOrganism.g(genome, :rng_analysis_offset))))
    changes = Dict{Symbol,Float64}()
    factors = Dict{Symbol,Float64}()
    for constant in D_NEIGHBORHOOD_CONSTANTS
        factor = 0.90 + 0.20 * rand(rng)
        factors[constant] = factor
        changes[constant] = ModelOrganism.g(genome, constant) * factor
    end
    return d_copy_genome(genome, changes, "neighborhood:$draw_seed"),
        factors
end

function d_run_neighborhood(genome)
    metric_rows = NamedTuple[]
    factor_rows = NamedTuple[]
    draw_rows = NamedTuple[]
    for draw_seed in D_NEIGHBORHOOD_DRAW_SEEDS
        sampled, factors = d_neighborhood_genome(genome, draw_seed)
        for constant in D_NEIGHBORHOOD_CONSTANTS
            push!(factor_rows, (draw_seed = draw_seed,
                constant = constant, factor = factors[constant],
                sampled_value = ModelOrganism.g(sampled, constant)))
        end
        results = d_reference_metrics(
            D_NEIGHBORHOOD_WORLD_SEEDS, sampled)
        survived = count(result -> result.passed, results)
        for result in results
            push!(metric_rows, (draw_seed = draw_seed,
                signature = result.signature, assay = result.assay,
                metric = result.metric, survived = result.passed,
                finite = result.finite))
        end
        push!(draw_rows, (draw_seed = draw_seed,
            survived_signatures = survived,
            joint_survival = survived >= 8))
    end
    signature_rows = NamedTuple[]
    robust_signatures = 0
    for signature in D_SIGNATURES
        selected = filter(row -> row.signature == signature, metric_rows)
        successes = count(row -> row.survived, selected)
        rate = successes / length(selected)
        robust_signatures += rate >= 0.60
        interval = wilson_interval(successes, length(selected))
        push!(signature_rows, (signature = signature,
            successes = successes, draws = length(selected),
            survival_volume = rate, interval_low = interval[1],
            interval_high = interval[2],
            robust_at_0_60 = rate >= 0.60))
    end
    joint_successes = count(row -> row.joint_survival, draw_rows)
    joint_volume = joint_successes / length(draw_rows)
    central = robust_signatures >= 8 && joint_volume >= 0.50
    summary = Dict(
        "classification" => central ? "central" : "narrow point",
        "draws" => length(D_NEIGHBORHOOD_DRAW_SEEDS),
        "worlds_per_draw" => length(D_NEIGHBORHOOD_WORLD_SEEDS),
        "robust_signatures_at_0_60" => robust_signatures,
        "joint_survival_successes" => joint_successes,
        "joint_survival_volume" => joint_volume,
        "joint_survival_interval_95" =>
            wilson_interval(joint_successes, length(draw_rows)),
        "joint_rule" => "at least 8 of 10 signatures",
        "reference_classification_rule" =>
            "at least 8 signature volumes ≥ 0.60 and joint volume ≥ 0.50",
    )
    return metric_rows, factor_rows, draw_rows, signature_rows, summary
end

function d_reference_identity_audit(genome)
    rows = NamedTuple[]
    for assay in 1:10
        seed = D_SEED_FIRST
        config = load_configuration(ModelOrganism.config_path(assay))
        direct = run_assay(assay, seed, genome, config)
        harness = d_rows(assay, [seed], genome)
        direct_bytes = let io = IOBuffer()
            Serialization.serialize(io, direct)
            take!(io)
        end
        harness_bytes = let io = IOBuffer()
            Serialization.serialize(io, harness)
            take!(io)
        end
        push!(rows, (assay = assay,
            byte_identical = direct_bytes == harness_bytes,
            direct_sha256 = bytes2hex(sha256(direct_bytes)),
            harness_sha256 = bytes2hex(sha256(harness_bytes))))
    end
    all(row -> row.byte_identical, rows) ||
        error("reference harness is not byte-identical")
    return rows
end

function d_fmt(value)
    value === nothing && return "NA"
    return @sprintf("%.4f", Float64(value))
end

function d_write_report(lesion_metrics, lesion_scores,
        sensitivity_constants, sensitivity_summary, neighborhood_signatures,
        neighborhood_summary)
    path = joinpath(ModelOrganism.RESULTS_ROOT, "stage-d-report.md")
    open(path, "w") do io
        println(io, "# Experiment 50-L lesions and robustness\n")
        println(io, "The reference organism remained fixed at `$FREEZE_COMMIT`. The preregistration was hash-locked before Stage D execution. **Ordering deviation:** 50-P had already been inspected; every lesion prediction here targets only the previously known 50-H signatures and no 50-P result.\n")
        println(io, "## Lesion scorecard\n")
        println(io, "| Lesion | Predicted disappear | Observed disappear | Prediction-hit rate | 95% interval |")
        println(io, "|---|---|---|---:|---|")
        for row in lesion_scores
            println(io, "| $(row.lesion) | $(row.predicted_disappear) | $(row.observed_disappear) | $(d_fmt(row.hit_rate)) | [$(d_fmt(row.interval_low)), $(d_fmt(row.interval_high))] |")
        end
        println(io, "\n### Signature-level predictions and misses\n")
        println(io, "| Lesion | Signature | Prediction | Metric | 95% interval | Compound rate (95% interval) | Observed | Hit |")
        println(io, "|---|---|---|---:|---|---|---|---|")
        for row in lesion_metrics
            row.lesion == :reference && continue
            observed = row.observed_survival ? "survived" : "disappeared"
            low = row.interval_low === nothing ? "NA" : d_fmt(row.interval_low)
            high = row.interval_high === nothing ? "NA" : d_fmt(row.interval_high)
            auxiliary = row.auxiliary_rate === nothing ? "NA" :
                "$(d_fmt(row.auxiliary_rate)) ([$(d_fmt(row.auxiliary_interval_low)), $(d_fmt(row.auxiliary_interval_high))])"
            println(io, "| $(row.lesion) | $(row.signature) | $(row.predicted) | $(d_fmt(row.metric)) | [$low, $high] | $auxiliary | $observed | **$(row.prediction_hit ? "HIT" : "MISS")** |")
        end
        reference_s4 = only(filter(row -> row.lesion == :reference &&
            row.signature == "S4", lesion_metrics))
        println(io, "\nThe unlesioned L-block reference itself did not satisfy compound S4: its mean transfer was `$(d_fmt(reference_s4.metric))`, but its qualifying-world rate was `$(d_fmt(reference_s4.auxiliary_rate))`, below the frozen `0.80`. Consequently, every predicted-survive S4 cell is retained as a miss; those misses cannot localize a lesion effect.")
        println(io, "\n## Sensitivity matrix\n")
        println(io, "- Classification: **$(sensitivity_summary["classification"])**")
        println(io, "- Resolvable shared constants: `$(sensitivity_summary["resolvable_constants"])/$(sensitivity_summary["shared_constants"])`")
        println(io, "- Constants materially affecting at least two signatures: `$(sensitivity_summary["multi_signature_constants"])` (`$(d_fmt(sensitivity_summary["multi_signature_fraction"]))`)")
        println(io, "- Cross-cluster material constants: `$(sensitivity_summary["cross_cluster_constants"])`")
        println(io, "- Paired-noncausal constants reported unresolved: `$(join(sensitivity_summary["paired_noncausal_constants"], ", "))`")
        println(io, "- For compound S4, materiality uses the larger absolute fractional change across conditional mean and qualifying-world rate; both components are published in the matrix.")
        println(io, "\nMaterial multi-signature constants:")
        println(io, "\n| Constant | Affected signatures | Crosses clusters |")
        println(io, "|---|---|---|")
        for row in sensitivity_constants
            row.material_signature_count >= 2 || continue
            println(io, "| $(row.constant) | $(row.affected_signatures) | $(row.crosses_clusters) |")
        end
        println(io, "- Full matrix: `lesions/sensitivity-matrix.csv`.\n")
        println(io, "## Joint neighborhood\n")
        println(io, "- Reference classification: **$(neighborhood_summary["classification"])**")
        println(io, "- Joint survival volume: `$(d_fmt(neighborhood_summary["joint_survival_volume"]))`, 95% interval `[$(d_fmt(neighborhood_summary["joint_survival_interval_95"][1])), $(d_fmt(neighborhood_summary["joint_survival_interval_95"][2]))]`.")
        println(io, "- Signatures with survival volume at least `0.60`: `$(neighborhood_summary["robust_signatures_at_0_60"])/10`.\n")
        println(io, "| Signature | Survival volume | 95% interval |")
        println(io, "|---|---:|---|")
        for row in neighborhood_signatures
            println(io, "| $(row.signature) | $(d_fmt(row.survival_volume)) | [$(d_fmt(row.interval_low)), $(d_fmt(row.interval_high))] |")
        end
        println(io, "\nAll misses, non-finite failures, and narrow survival volumes are retained. No 50-P outcome was used in prediction or scoring.")
    end
    return path
end

function d_update_profile!(lesion_scores, sensitivity_summary,
        neighborhood_summary)
    path = joinpath(ModelOrganism.RESULTS_ROOT, "profile.md")
    raw = read(path, String)
    marker = "\n## Final battery-wide profile after 50-L\n"
    occursin(marker, raw) &&
        (raw = first(split(raw, marker; limit = 2)))
    io = IOBuffer()
    print(io, raw)
    println(io, marker)
    println(io, "The four evidentiary classes remain separated from the 50-L causal-localization adjunct:\n")
    println(io, "| Evidentiary class | Final status |")
    println(io, "|---|---|")
    println(io, "| Architecture/conformance | 11 of 12 frozen criteria passed; assay-9 obsolescence crossover failed. |")
    println(io, "| Causal or mechanism contrast | 8 of 8 frozen criteria passed. |")
    println(io, "| Model discrimination and transfer | 6 of 6 frozen criteria passed. |")
    println(io, "| Prospective compositional challenge | E3 failed scientifically; E4 and E5 were prospection failures and were not scientifically evaluated. |")
    println(io, "\n50-L adjunct:")
    println(io, "\n- Sensitivity architecture: **$(sensitivity_summary["classification"])**.")
    println(io, "- Joint genome neighborhood: **$(neighborhood_summary["classification"])**.")
    misses = sum(row.total - row.hits for row in lesion_scores)
    println(io, "- Lesion prediction misses retained: `$misses` across `$(length(lesion_scores))` preregistered lesion clusters.")
    println(io, "- Ordering deviation: 50-L was preregistered only after 50-P inspection; lesion predictions were restricted to the known 50-H signatures.")
    write(path, String(take!(io)))
end

function d_file_entry(path)
    return Dict("path" => relpath(path, ModelOrganism.PROJECT_ROOT),
        "sha256" => bytes2hex(sha256(read(path))),
        "bytes" => filesize(path))
end

function d_finalize_manifest(files, genome)
    prereg = joinpath(d_lesion_root(), "preregistration.md")
    bytes2hex(sha256(read(prereg))) == D_PREREG_HASH ||
        error("preregistration changed during Stage D")
    payload = Dict(
        "stage" => "50-L complete",
        "complete" => true,
        "execution_started" => true,
        "ordering_deviation_logged" => true,
        "reference_freeze_commit" => FREEZE_COMMIT,
        "stage_c_commit" => D_STAGE_C_COMMIT,
        "canonical_source_sha256" =>
            ModelOrganism.canonical_source_hash(),
        "genome_sha256" => genome.sha256,
        "preregistration" => Dict(
            "path" => relpath(prereg, ModelOrganism.PROJECT_ROOT),
            "sha256" => D_PREREG_HASH),
        "released_seed_block" => [D_SEED_FIRST, D_SEED_LAST],
        "maximum_seed_opened" =>
            maximum(vcat(D_LESION_SEEDS, D_SENSITIVITY_SEEDS,
                D_NEIGHBORHOOD_DRAW_SEEDS,
                D_NEIGHBORHOOD_WORLD_SEEDS)),
        "outside_seed_block_opened" => false,
        "components" => [d_file_entry(path) for path in files],
    )
    ModelOrganism.write_json_file(joinpath(
        ModelOrganism.RESULTS_ROOT, "stage-d-manifest.json"), payload)
end

function d_main()
    ARGS == ["--run"] || error("usage: run_stage_d.jl --run")
    genome = load_genome()
    d_verify_reference!(genome)
    identity_rows = d_reference_identity_audit(genome)
    d_verify_reference!(genome)

    lesion_metrics, lesion_scores = d_run_lesions(genome)
    mkpath(d_lesion_root())
    identity_path = joinpath(d_lesion_root(),
        "reference-identity-audit.csv")
    lesion_metric_path = joinpath(d_lesion_root(),
        "lesion-metrics.csv")
    lesion_score_path = joinpath(d_lesion_root(),
        "lesion-scorecard.csv")
    ModelOrganism.write_csv_file(identity_path, identity_rows)
    ModelOrganism.write_csv_file(lesion_metric_path, lesion_metrics)
    ModelOrganism.write_csv_file(lesion_score_path, lesion_scores)
    d_verify_reference!(genome)

    sensitivity_rows, constant_rows, sensitivity_summary =
        d_run_sensitivity(genome)
    sensitivity_path = joinpath(d_lesion_root(),
        "sensitivity-matrix.csv")
    constant_path = joinpath(d_lesion_root(),
        "sensitivity-constants.csv")
    sensitivity_summary_path = joinpath(d_lesion_root(),
        "sensitivity-summary.json")
    ModelOrganism.write_csv_file(sensitivity_path, sensitivity_rows)
    ModelOrganism.write_csv_file(constant_path, constant_rows)
    ModelOrganism.write_json_file(
        sensitivity_summary_path, sensitivity_summary)
    d_verify_reference!(genome)

    neighborhood_metrics, factor_rows, draw_rows,
        neighborhood_signatures, neighborhood_summary =
        d_run_neighborhood(genome)
    mkpath(d_neighborhood_root())
    neighborhood_metric_path = joinpath(d_neighborhood_root(),
        "per_draw_signature.csv")
    factor_path = joinpath(d_neighborhood_root(), "draw_factors.csv")
    draw_path = joinpath(d_neighborhood_root(), "draw_summary.csv")
    volume_path = joinpath(d_neighborhood_root(),
        "signature-volumes.csv")
    neighborhood_summary_path = joinpath(d_neighborhood_root(),
        "summary.json")
    ModelOrganism.write_csv_file(
        neighborhood_metric_path, neighborhood_metrics)
    ModelOrganism.write_csv_file(factor_path, factor_rows)
    ModelOrganism.write_csv_file(draw_path, draw_rows)
    ModelOrganism.write_csv_file(volume_path, neighborhood_signatures)
    ModelOrganism.write_json_file(
        neighborhood_summary_path, neighborhood_summary)

    report_path = d_write_report(lesion_metrics, lesion_scores,
        constant_rows, sensitivity_summary, neighborhood_signatures,
        neighborhood_summary)
    d_update_profile!(lesion_scores, sensitivity_summary,
        neighborhood_summary)
    d_verify_reference!(genome)
    profile_path = joinpath(ModelOrganism.RESULTS_ROOT, "profile.md")
    files = [joinpath(d_lesion_root(), "preregistration.md"),
        joinpath(d_lesion_root(), "errata.md"),
        identity_path, lesion_metric_path, lesion_score_path,
        sensitivity_path, constant_path, sensitivity_summary_path,
        neighborhood_metric_path, factor_path, draw_path, volume_path,
        neighborhood_summary_path, report_path, profile_path,
        @__FILE__]
    d_finalize_manifest(files, genome)
    println("Stage D complete: sensitivity=",
        sensitivity_summary["classification"], ", neighborhood=",
        neighborhood_summary["classification"], ", max_seed=",
        maximum(D_NEIGHBORHOOD_DRAW_SEEDS))
end

abspath(PROGRAM_FILE) == abspath(@__FILE__) && d_main()
