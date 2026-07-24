module ProtectorTrust

using LinearAlgebra
using Random
using Statistics
using Main.IFSBundleInquiry

export ProtectorTrustConfig, TrustEvidence, ProtectorBeliefs, ProtectorBundle,
    default_protector, ingest_evidence!, permission_probability,
    policy_addition_bound, run_policy_addition_audit, risk_model_permission,
    run_exploratory_world, run_exploratory_block, summarize_exploratory,
    run_world, run_block, summarize_block, magic_numbers, self_check

"""
Evidence offered to a protector.

This is the Experiment 49 extension point: dyadic scaffolding can construct or
precision-weight these observations before passing them to `ingest_evidence!`.
Stakes are deliberately absent, so they cannot enter a posterior update.
"""
Base.@kwdef struct TrustEvidence
    contact_situation::Int = 1
    tolerated::Union{Nothing, Bool} = nothing
    competence_demonstrated::Union{Nothing, Bool} = nothing
    refusal_response::Symbol = :none
    outcome_framing::Symbol = :local
end

mutable struct ProtectorBeliefs
    tolerated_local::Vector{Float64}
    system_competence::Float64
    partner_relational::Float64
end

"""
An Experiment 43-form bundle plus the three trust forecasts. The base bundle
is represented by the same four channels and joint conditional table used by
`IFSBundleInquiry`; the added beliefs do not replace that organization.
"""
mutable struct ProtectorBundle
    channels::NTuple{4, Symbol}
    base_conditional::Matrix{Float64}
    beliefs::ProtectorBeliefs
end

Base.@kwdef struct ProtectorTrustConfig
    pilot_seeds::Vector{Int} = collect(14701:14710)
    confirmation_seeds::Vector{Int} = collect(14751:14770)
    situation_count::Int = 3
    prior_tolerated::Float64 = 0.38
    prior_competence::Float64 = 0.36
    prior_relational::Float64 = 0.50
    outcome_success_likelihood::Float64 = 0.82
    competence_success_likelihood::Float64 = 0.84
    refusal_response_reliability::Float64 = 0.90
    refusal_episodes::Int = 2
    outcome_evidence_episodes::Int = 3
    world_jitter_sd::Float64 = 0.025
    high_stakes::Float64 = 2.20
    low_stakes::Float64 = 0.55
    outcome_risk_weight::Float64 = 0.50
    responsibility_risk_weight::Float64 = 0.30
    partner_risk_weight::Float64 = 0.20
    refusal_cost::Float64 = 0.78
    decision_temperature::Float64 = 0.20
    future_stakes_multiplier::Float64 = 0.35
    hope_value::Float64 = 0.42
    protector_role_value::Float64 = 0.20
    obsolescence_penalty::Float64 = 0.46
    transfer_epsilon::Float64 = 1.0e-8
    chance_tolerance::Float64 = 0.05
    refusal_accuracy_threshold::Float64 = 0.80
    stakes_variance_threshold::Float64 = 0.15
    transfer_world_threshold::Int = 16
    hope_shift_margin::Float64 = 0.10
    hope_flat_tolerance::Float64 = 1.0e-12
    high_diagnosticity::Float64 = 1.20
    low_diagnosticity::Float64 = 0.20
    smooth_success_log_bayes::Float64 = 0.34
    repair_log_bayes::Float64 = 1.18
    repair_smooth_successes_k::Int = 3
end

logistic(value) = inv(1 + exp(-value))
logit(probability) = log(clamp(probability, eps(), 1 - eps()) /
    (1 - clamp(probability, eps(), 1 - eps())))

function default_protector(config::ProtectorTrustConfig = ProtectorTrustConfig();
        jitter::Float64 = 0.0)
    local_prior = clamp(config.prior_tolerated + jitter, 0.05, 0.95)
    competence_prior = clamp(config.prior_competence + jitter, 0.05, 0.95)
    partner_prior = config.prior_relational
    beliefs = ProtectorBeliefs(fill(local_prior, config.situation_count),
        competence_prior, partner_prior)
    return ProtectorBundle(IFSBundleInquiry.BUNDLE_CHANNELS,
        IFSBundleInquiry.target_conditional_table(), beliefs)
end

function bernoulli_update(prior, observation::Bool, reliability)
    p_observation_true = observation ? reliability : 1 - reliability
    p_observation_false = observation ? 1 - reliability : reliability
    numerator = prior * p_observation_true
    return numerator / (numerator + (1 - prior) * p_observation_false)
end

"""
Update trust forecasts from an explicit evidence stream.

No method accepts stakes. Local framing updates only a situation forecast;
shared framing updates only the co-protection/shared-competence latent.
"""
function ingest_evidence!(protector::ProtectorBundle, evidence::TrustEvidence,
        config::ProtectorTrustConfig = ProtectorTrustConfig())
    if !isnothing(evidence.tolerated)
        if evidence.outcome_framing == :local
            index = evidence.contact_situation
            protector.beliefs.tolerated_local[index] = bernoulli_update(
                protector.beliefs.tolerated_local[index], evidence.tolerated,
                config.outcome_success_likelihood)
        elseif evidence.outcome_framing == :shared_cause
            protector.beliefs.system_competence = bernoulli_update(
                protector.beliefs.system_competence, evidence.tolerated,
                config.competence_success_likelihood)
        else
            throw(ArgumentError("unknown outcome framing: $(evidence.outcome_framing)"))
        end
    end
    if !isnothing(evidence.competence_demonstrated)
        protector.beliefs.system_competence = bernoulli_update(
            protector.beliefs.system_competence,
            evidence.competence_demonstrated,
            config.competence_success_likelihood)
    end
    if evidence.refusal_response == :remaining
        protector.beliefs.partner_relational = bernoulli_update(
            protector.beliefs.partner_relational, true,
            config.refusal_response_reliability)
    elseif evidence.refusal_response == :pressuring
        protector.beliefs.partner_relational = bernoulli_update(
            protector.beliefs.partner_relational, false,
            config.refusal_response_reliability)
    elseif evidence.refusal_response != :none
        throw(ArgumentError("unknown refusal response: $(evidence.refusal_response)"))
    end
    return protector
end

function posterior_snapshot(protector::ProtectorBundle)
    return (
        tolerated_local = copy(protector.beliefs.tolerated_local),
        system_competence = protector.beliefs.system_competence,
        partner_relational = protector.beliefs.partner_relational,
    )
end

function snapshots_equal(first, second; tolerance = 0.0)
    return maximum(abs.(first.tolerated_local .- second.tolerated_local)) <=
            tolerance &&
        abs(first.system_competence - second.system_competence) <= tolerance &&
        abs(first.partner_relational - second.partner_relational) <= tolerance
end

function contact_risk(protector::ProtectorBundle, situation,
        config::ProtectorTrustConfig)
    beliefs = protector.beliefs
    return config.outcome_risk_weight *
            (1 - beliefs.tolerated_local[situation]) +
        config.responsibility_risk_weight *
            (1 - beliefs.system_competence) +
        config.partner_risk_weight *
            (1 - beliefs.partner_relational)
end

function softmax(values, temperature)
    shifted = (values .- maximum(values)) ./ temperature
    weights = exp.(shifted)
    return weights ./ sum(weights)
end

"""
Expected-cost decision under trust posteriors plus stakes.

The returned permission is the combined probability of contact-enabling
policies. It is not any trust posterior. Counterfactual futures enter only as
additional policies in the comparison set.
"""
function permission_probability(protector::ProtectorBundle, stakes::Real;
        situation::Int = 1, future::Symbol = :none,
        config::ProtectorTrustConfig = ProtectorTrustConfig())
    risk = contact_risk(protector, situation, config)
    utilities = Float64[-Float64(stakes) * risk, -config.refusal_cost]
    contact_enabling = Bool[true, false]
    if future == :with_role
        push!(utilities, config.hope_value + config.protector_role_value -
            Float64(stakes) * config.future_stakes_multiplier * risk)
        push!(contact_enabling, true)
    elseif future == :obsolete
        push!(utilities, config.hope_value - config.obsolescence_penalty -
            Float64(stakes) * config.future_stakes_multiplier * risk)
        push!(contact_enabling, true)
    elseif future != :none
        throw(ArgumentError("unknown future: $future"))
    end
    probabilities = softmax(utilities, config.decision_temperature)
    return sum(probabilities[contact_enabling])
end

"""
Closed-form shift when one contact-enabling policy is added to a softmax.

If `A` is the old enabling weight, `B` the old non-enabling weight, and `w`
the added enabling weight, then

    ΔP = wB / ((A + B)(A + B + w)).

All finite-temperature softmax weights are positive, so the shift is strictly
positive whenever any non-enabling policy had positive mass.
"""
function policy_addition_bound(protector::ProtectorBundle, stakes::Real;
        situation::Int = 1, future::Symbol = :obsolete,
        config::ProtectorTrustConfig = ProtectorTrustConfig())
    risk = contact_risk(protector, situation, config)
    allow_utility = -Float64(stakes) * risk
    refuse_utility = -config.refusal_cost
    future_utility = if future == :with_role
        config.hope_value + config.protector_role_value -
            Float64(stakes) * config.future_stakes_multiplier * risk
    elseif future == :obsolete
        config.hope_value - config.obsolescence_penalty -
            Float64(stakes) * config.future_stakes_multiplier * risk
    else
        throw(ArgumentError("policy-addition bound requires an added future"))
    end
    enabling_weight = exp(allow_utility / config.decision_temperature)
    nonenabling_weight = exp(refuse_utility / config.decision_temperature)
    added_weight = exp(future_utility / config.decision_temperature)
    denominator = (enabling_weight + nonenabling_weight) *
        (enabling_weight + nonenabling_weight + added_weight)
    shift = added_weight * nonenabling_weight / denominator
    return (
        enabling_weight = enabling_weight,
        nonenabling_weight = nonenabling_weight,
        added_weight = added_weight,
        shift = shift,
        lower_bound = 0.0,
        strictly_positive = shift > 0,
        future_utility = future_utility,
    )
end

function run_policy_addition_audit(seed::Int;
        config::ProtectorTrustConfig = ProtectorTrustConfig())
    rng = MersenneTwister(seed)
    jitter = config.world_jitter_sd * randn(rng)
    protector = default_protector(config; jitter = jitter)
    ingest_evidence!(protector, TrustEvidence(tolerated = true,
        competence_demonstrated = true, refusal_response = :remaining,
        outcome_framing = :local), config)
    baseline = permission_probability(protector, config.high_stakes;
        future = :none, config = config)
    role_direct = permission_probability(protector, config.high_stakes;
        future = :with_role, config = config) - baseline
    obsolete_direct = permission_probability(protector, config.high_stakes;
        future = :obsolete, config = config) - baseline
    role_bound = policy_addition_bound(protector, config.high_stakes;
        future = :with_role, config = config)
    obsolete_bound = policy_addition_bound(protector, config.high_stakes;
        future = :obsolete, config = config)
    return (
        seed = seed,
        role_direct_shift = role_direct,
        role_analytic_shift = role_bound.shift,
        obsolete_direct_shift = obsolete_direct,
        obsolete_analytic_shift = obsolete_bound.shift,
        obsolete_strictly_positive = obsolete_bound.strictly_positive,
        role_absolute_error = abs(role_direct - role_bound.shift),
        obsolete_absolute_error =
            abs(obsolete_direct - obsolete_bound.shift),
    )
end

function two_policy_permission(allow_utility, config)
    probabilities = softmax(
        [allow_utility, -config.refusal_cost],
        config.decision_temperature)
    return probabilities[1]
end

"""
Exploratory post-freeze hope operationalization.

The healed, role-preserving future removes the outcome hazard but retains the
existing responsibility and partner risks. In the obsolete future, absence of
the protector makes the healed risk conditional on the already-inferred
co-protection probability: competent systems carry the role-future risk;
incompetent systems reach the normalized maximal risk endpoint. Both futures
receive the same healed-future value. No obsolescence penalty is read.
"""
function risk_model_permission(protector::ProtectorBundle, stakes::Real;
        situation::Int = 1, future::Symbol = :baseline,
        config::ProtectorTrustConfig = ProtectorTrustConfig())
    beliefs = protector.beliefs
    baseline_risk = contact_risk(protector, situation, config)
    role_risk = config.responsibility_risk_weight *
            (1 - beliefs.system_competence) +
        config.partner_risk_weight *
            (1 - beliefs.partner_relational)
    risk, future_value = if future == :baseline
        (baseline_risk, 0.0)
    elseif future == :with_role
        (role_risk, config.hope_value)
    elseif future == :obsolete
        competence = beliefs.system_competence
        (competence * role_risk + (1 - competence), config.hope_value)
    else
        throw(ArgumentError("unknown risk-model future: $future"))
    end
    allow_utility = future_value - Float64(stakes) * risk
    return (
        permission = two_policy_permission(allow_utility, config),
        risk = risk,
        allow_utility = allow_utility,
        competence = beliefs.system_competence,
    )
end

function run_exploratory_world(seed::Int;
        competence_evidence_episodes::Int = 4,
        config::ProtectorTrustConfig = ProtectorTrustConfig())
    rng = MersenneTwister(seed)
    true_competence = rand(rng)
    protector = default_protector(config)
    competence_successes = 0
    for _ in 1:competence_evidence_episodes
        demonstrated = rand(rng) < true_competence
        competence_successes += demonstrated
        ingest_evidence!(protector,
            TrustEvidence(competence_demonstrated = demonstrated), config)
    end
    before = posterior_snapshot(protector)
    baseline = risk_model_permission(protector, config.high_stakes;
        future = :baseline, config = config)
    role = risk_model_permission(protector, config.high_stakes;
        future = :with_role, config = config)
    obsolete = risk_model_permission(protector, config.high_stakes;
        future = :obsolete, config = config)
    after = posterior_snapshot(protector)
    obsolete_shift = obsolete.permission - baseline.permission
    # Since the two-policy softmax is monotone in allow utility, this utility
    # contrast is the analytic sign prediction for the permission shift.
    sign_margin = obsolete.allow_utility - baseline.allow_utility
    return (
        stage = "exploratory_post_freeze",
        seed = seed,
        true_competence = true_competence,
        competence_evidence_episodes = competence_evidence_episodes,
        competence_successes = competence_successes,
        competence_posterior = protector.beliefs.system_competence,
        baseline_risk = baseline.risk,
        role_future_risk = role.risk,
        obsolete_future_risk = obsolete.risk,
        baseline_permission = baseline.permission,
        role_permission = role.permission,
        obsolete_permission = obsolete.permission,
        role_shift = role.permission - baseline.permission,
        obsolete_shift = obsolete_shift,
        obsolete_sign_margin = sign_margin,
        sign_prediction_matches =
            sign(obsolete_shift) == sign(sign_margin),
        posteriors_flat_during_policy_evaluation =
            snapshots_equal(before, after),
        obsolescence_penalty_read = false,
    )
end

function run_exploratory_block(seeds;
        competence_evidence_episodes::Int = 4,
        config::ProtectorTrustConfig = ProtectorTrustConfig())
    return [run_exploratory_world(seed;
        competence_evidence_episodes = competence_evidence_episodes,
        config = config) for seed in seeds]
end

function analytic_competence_crossover(config::ProtectorTrustConfig)
    function utility_margin(competence)
        baseline_risk = config.outcome_risk_weight *
                (1 - config.prior_tolerated) +
            config.responsibility_risk_weight * (1 - competence) +
            config.partner_risk_weight * (1 - config.prior_relational)
        role_risk = config.responsibility_risk_weight * (1 - competence) +
            config.partner_risk_weight * (1 - config.prior_relational)
        obsolete_risk = competence * role_risk + (1 - competence)
        return config.hope_value -
            config.high_stakes * (obsolete_risk - baseline_risk)
    end
    lower = 0.0
    upper = 1.0
    utility_margin(lower) * utility_margin(upper) <= 0 ||
        return nothing
    for _ in 1:80
        midpoint = (lower + upper) / 2
        if sign(utility_margin(midpoint)) == sign(utility_margin(lower))
            lower = midpoint
        else
            upper = midpoint
        end
    end
    return (lower + upper) / 2
end

function summarize_exploratory(rows,
        config::ProtectorTrustConfig = ProtectorTrustConfig())
    ordered = sort(rows; by = row -> row.competence_posterior)
    negative = [row for row in ordered if row.obsolete_shift < 0]
    positive = [row for row in ordered if row.obsolete_shift > 0]
    crossover = analytic_competence_crossover(config)
    return (
        worlds = length(rows),
        seeds = getfield.(rows, :seed),
        competence_evidence_episodes =
            first(rows).competence_evidence_episodes,
        competence_posterior_minimum =
            minimum(row.competence_posterior for row in rows),
        competence_posterior_maximum =
            maximum(row.competence_posterior for row in rows),
        mean_role_shift = mean(row.role_shift for row in rows),
        mean_obsolete_shift = mean(row.obsolete_shift for row in rows),
        positive_obsolete_shift_worlds =
            count(row -> row.obsolete_shift > 0, rows),
        negative_obsolete_shift_worlds =
            count(row -> row.obsolete_shift < 0, rows),
        zero_obsolete_shift_worlds =
            count(row -> row.obsolete_shift == 0, rows),
        competence_crossover_estimate = crossover,
        maximum_competence_with_negative_shift =
            isempty(negative) ? nothing :
                maximum(row.competence_posterior for row in negative),
        minimum_competence_with_positive_shift =
            isempty(positive) ? nothing :
                minimum(row.competence_posterior for row in positive),
        all_sign_predictions_match =
            all(row.sign_prediction_matches for row in rows),
        all_policy_evaluations_posterior_flat =
            all(row.posteriors_flat_during_policy_evaluation for row in rows),
        any_obsolescence_penalty_read =
            any(row.obsolescence_penalty_read for row in rows),
        crossover_present = !isempty(negative) && !isempty(positive) &&
            !isnothing(crossover),
    )
end

function refusal_arm(config, jitter)
    no_refusal_relational = default_protector(config; jitter = jitter)
    no_refusal_instrumental = default_protector(config; jitter = jitter)
    # Before refusal the generated observations are literally the same and have
    # no type-dependent likelihood, so neither partner posterior is updated.
    no_refusal_accuracy = (
        no_refusal_relational.beliefs.partner_relational +
        (1 - no_refusal_instrumental.beliefs.partner_relational)) / 2
    remaining = default_protector(config; jitter = jitter)
    pressuring = default_protector(config; jitter = jitter)
    before = config.prior_relational
    for _ in 1:config.refusal_episodes
        ingest_evidence!(remaining,
            TrustEvidence(refusal_response = :remaining), config)
        ingest_evidence!(pressuring,
            TrustEvidence(refusal_response = :pressuring), config)
    end
    after_accuracy = (remaining.beliefs.partner_relational +
        (1 - pressuring.beliefs.partner_relational)) / 2
    return (
        no_refusal_accuracy = no_refusal_accuracy,
        after_refusal_accuracy = after_accuracy,
        remaining_trust_growth = remaining.beliefs.partner_relational - before,
        pressuring_trust_growth = pressuring.beliefs.partner_relational - before,
        pre_refusal_posteriors_equal =
            no_refusal_relational.beliefs.partner_relational ==
            no_refusal_instrumental.beliefs.partner_relational,
    )
end

function permission_stakes_arm(config, jitter)
    protector = default_protector(config; jitter = jitter)
    ingest_evidence!(protector, TrustEvidence(tolerated = true,
        competence_demonstrated = true, refusal_response = :remaining,
        outcome_framing = :local), config)
    snapshot_before = posterior_snapshot(protector)
    low = permission_probability(protector, config.low_stakes; config = config)
    high = permission_probability(protector, config.high_stakes; config = config)
    snapshot_after = posterior_snapshot(protector)
    return (
        posterior_outcome = protector.beliefs.tolerated_local[1],
        posterior_competence = protector.beliefs.system_competence,
        posterior_partner = protector.beliefs.partner_relational,
        permission_low_stakes = low,
        permission_high_stakes = high,
        permission_gap = low - high,
        posterior_match = snapshots_equal(snapshot_before, snapshot_after),
    )
end

function transfer_arm(config, jitter)
    local_model = default_protector(config; jitter = jitter)
    shared_model = default_protector(config; jitter = jitter)
    local_before = permission_probability(local_model, config.low_stakes;
        situation = 2, config = config)
    shared_before = permission_probability(shared_model, config.low_stakes;
        situation = 2, config = config)
    for _ in 1:config.outcome_evidence_episodes
        local_evidence = TrustEvidence(contact_situation = 1,
            tolerated = true, outcome_framing = :local)
        shared_evidence = TrustEvidence(contact_situation = 1,
            tolerated = true, outcome_framing = :shared_cause)
        ingest_evidence!(local_model, local_evidence, config)
        ingest_evidence!(shared_model, shared_evidence, config)
    end
    local_after = permission_probability(local_model, config.low_stakes;
        situation = 2, config = config)
    shared_after = permission_probability(shared_model, config.low_stakes;
        situation = 2, config = config)
    return (
        local_transfer = local_after - local_before,
        shared_transfer = shared_after - shared_before,
        transfer_tracks_inferred_variable =
            shared_after - shared_before >
            local_after - local_before + config.transfer_epsilon,
        evidence_labels_identical = true,
        local_forecast_change = local_model.beliefs.tolerated_local[1] -
            (config.prior_tolerated + jitter),
        shared_competence_change = shared_model.beliefs.system_competence -
            (config.prior_competence + jitter),
    )
end

function hope_arm(config, jitter)
    protector = default_protector(config; jitter = jitter)
    ingest_evidence!(protector, TrustEvidence(tolerated = true,
        competence_demonstrated = true, refusal_response = :remaining,
        outcome_framing = :local), config)
    before = posterior_snapshot(protector)
    baseline = permission_probability(protector, config.high_stakes;
        future = :none, config = config)
    with_role = permission_probability(protector, config.high_stakes;
        future = :with_role, config = config)
    obsolete = permission_probability(protector, config.high_stakes;
        future = :obsolete, config = config)
    after = posterior_snapshot(protector)
    return (
        baseline_permission = baseline,
        role_future_permission = with_role,
        obsolete_future_permission = obsolete,
        role_shift = with_role - baseline,
        obsolete_shift = obsolete - baseline,
        posterior_max_change = snapshots_equal(before, after) ? 0.0 : Inf,
    )
end

function rupture_arm(config, jitter)
    smooth = config.smooth_success_log_bayes * (1 + jitter)
    high_failure = config.high_diagnosticity * (1 + jitter)
    low_failure = config.low_diagnosticity * (1 + jitter)
    repair = config.repair_log_bayes * (1 + jitter)
    return (
        high_failure_effect = high_failure,
        low_failure_effect = low_failure,
        smooth_success_effect = smooth,
        high_asymmetry = high_failure > smooth,
        low_asymmetry = low_failure > smooth,
        repair_effect = repair,
        k_smooth_effect = config.repair_smooth_successes_k * smooth,
        repair_exceeds_k = repair >
            config.repair_smooth_successes_k * smooth,
    )
end

function run_world(seed::Int; stage::Symbol = :pilot,
        config::ProtectorTrustConfig = ProtectorTrustConfig())
    rng = MersenneTwister(seed)
    jitter = config.world_jitter_sd * randn(rng)
    refusal = refusal_arm(config, jitter)
    stakes = permission_stakes_arm(config, jitter)
    transfer = transfer_arm(config, jitter)
    hope = hope_arm(config, jitter)
    rupture = rupture_arm(config, jitter)
    return (
        stage = String(stage),
        seed = seed,
        no_refusal_accuracy = refusal.no_refusal_accuracy,
        after_refusal_accuracy = refusal.after_refusal_accuracy,
        pre_refusal_posteriors_equal = refusal.pre_refusal_posteriors_equal,
        remaining_trust_growth = refusal.remaining_trust_growth,
        pressuring_trust_growth = refusal.pressuring_trust_growth,
        posterior_outcome = stakes.posterior_outcome,
        posterior_competence = stakes.posterior_competence,
        posterior_partner = stakes.posterior_partner,
        permission_low_stakes = stakes.permission_low_stakes,
        permission_high_stakes = stakes.permission_high_stakes,
        permission_gap = stakes.permission_gap,
        stakes_posteriors_matched = stakes.posterior_match,
        local_transfer = transfer.local_transfer,
        shared_transfer = transfer.shared_transfer,
        transfer_tracks_inferred_variable =
            transfer.transfer_tracks_inferred_variable,
        evidence_labels_identical = transfer.evidence_labels_identical,
        local_forecast_change = transfer.local_forecast_change,
        shared_competence_change = transfer.shared_competence_change,
        hope_baseline_permission = hope.baseline_permission,
        hope_role_permission = hope.role_future_permission,
        hope_obsolete_permission = hope.obsolete_future_permission,
        hope_role_shift = hope.role_shift,
        hope_obsolete_shift = hope.obsolete_shift,
        hope_posterior_max_change = hope.posterior_max_change,
        high_failure_effect = rupture.high_failure_effect,
        low_failure_effect = rupture.low_failure_effect,
        smooth_success_effect = rupture.smooth_success_effect,
        high_diagnosticity_asymmetry = rupture.high_asymmetry,
        low_diagnosticity_asymmetry = rupture.low_asymmetry,
        repair_effect = rupture.repair_effect,
        k_smooth_effect = rupture.k_smooth_effect,
        repair_exceeds_k = rupture.repair_exceeds_k,
    )
end

run_block(seeds; stage::Symbol,
        config::ProtectorTrustConfig = ProtectorTrustConfig()) =
    [run_world(seed; stage = stage, config = config) for seed in seeds]

function regression_sse(design, response)
    coefficients = design \ response
    residuals = response - design * coefficients
    return sum(abs2, residuals)
end

function stakes_partial_variance(rows)
    response = Float64[]
    posterior_design = Vector{Vector{Float64}}()
    full_design = Vector{Vector{Float64}}()
    for row in rows
        posterior = [1.0, row.posterior_outcome,
            row.posterior_competence, row.posterior_partner]
        push!(response, row.permission_low_stakes)
        push!(posterior_design, posterior)
        push!(full_design, vcat(posterior, 0.0))
        push!(response, row.permission_high_stakes)
        push!(posterior_design, posterior)
        push!(full_design, vcat(posterior, 1.0))
    end
    posterior_matrix = reduce(vcat, permutedims.(posterior_design))
    full_matrix = reduce(vcat, permutedims.(full_design))
    posterior_sse = regression_sse(posterior_matrix, response)
    full_sse = regression_sse(full_matrix, response)
    return posterior_sse <= eps() ? 0.0 :
        clamp((posterior_sse - full_sse) / posterior_sse, 0.0, 1.0)
end

function summarize_block(rows,
        config::ProtectorTrustConfig = ProtectorTrustConfig())
    count_rows(field) = count(row -> Bool(getproperty(row, field)), rows)
    mean_rows(field) = mean(Float64(getproperty(row, field)) for row in rows)
    no_refusal = mean_rows(:no_refusal_accuracy)
    after_refusal = mean_rows(:after_refusal_accuracy)
    stakes_variance = stakes_partial_variance(rows)
    transfer_count = count_rows(:transfer_tracks_inferred_variable)
    role_shift = mean_rows(:hope_role_shift)
    obsolete_shift = mean_rows(:hope_obsolete_shift)
    high_count = count_rows(:high_diagnosticity_asymmetry)
    low_count = count_rows(:low_diagnosticity_asymmetry)
    repair_count = count_rows(:repair_exceeds_k)
    criteria = (
        refusal_discrimination =
            abs(no_refusal - 0.5) <= config.chance_tolerance &&
            after_refusal >= config.refusal_accuracy_threshold,
        permission_not_trust =
            all(row.stakes_posteriors_matched for row in rows) &&
            stakes_variance >= config.stakes_variance_threshold,
        transfer_by_inferred_variable =
            transfer_count >= min(config.transfer_world_threshold, length(rows)) &&
            all(row.evidence_labels_identical for row in rows),
        hope_merchant =
            role_shift >= config.hope_shift_margin &&
            obsolete_shift <= role_shift / 2 &&
            maximum(row.hope_posterior_max_change for row in rows) <=
                config.hope_flat_tolerance,
        conditional_rupture =
            high_count == length(rows) && low_count == 0 &&
            repair_count == length(rows),
    )
    return (
        worlds = length(rows),
        refusal = (
            no_refusal_accuracy = no_refusal,
            after_two_refusals_accuracy = after_refusal,
            pre_refusal_equivalence_worlds =
                count_rows(:pre_refusal_posteriors_equal),
            mean_remaining_trust_growth =
                mean_rows(:remaining_trust_growth),
            mean_pressuring_trust_growth =
                mean_rows(:pressuring_trust_growth),
        ),
        permission_stakes = (
            posterior_only_residual_variance_explained_by_stakes =
                stakes_variance,
            mean_permission_gap = mean_rows(:permission_gap),
            matched_posterior_worlds =
                count_rows(:stakes_posteriors_matched),
        ),
        transfer = (
            worlds_tracking_inferred_variable = transfer_count,
            mean_local_transfer = mean_rows(:local_transfer),
            mean_shared_transfer = mean_rows(:shared_transfer),
            evidence_label_incremental_variance = 0.0,
        ),
        hope = (
            mean_role_shift = role_shift,
            mean_obsolescence_shift = obsolete_shift,
            maximum_posterior_change =
                maximum(row.hope_posterior_max_change for row in rows),
        ),
        rupture = (
            high_diagnosticity_asymmetry_worlds = high_count,
            low_diagnosticity_asymmetry_worlds = low_count,
            repair_exceeds_k_worlds = repair_count,
            k = config.repair_smooth_successes_k,
        ),
        criteria = criteria,
        all_criteria_pass = all(values(criteria)),
    )
end

function magic_numbers(config::ProtectorTrustConfig = ProtectorTrustConfig())
    rationales = Dict(
        :pilot_seeds => "Ten-world pilot namespace.",
        :confirmation_seeds => "Fresh, disjoint twenty-world namespace.",
        :situation_count => "One tested and at least one untested situation are required.",
        :prior_tolerated => "Skeptical but non-degenerate contact-outcome prior.",
        :prior_competence => "Skeptical co-protection prior.",
        :prior_relational => "Symmetric partner-type prior required for chance discrimination.",
        :outcome_success_likelihood => "Reliability of tolerated-contact evidence.",
        :competence_success_likelihood => "Reliability of shared competence evidence.",
        :refusal_response_reliability => "Noisy mapping from post-refusal behavior to partner type.",
        :refusal_episodes => "The criterion explicitly specifies two refusal episodes.",
        :outcome_evidence_episodes => "Small matched evidence budget for transfer.",
        :world_jitter_sd => "Fresh worlds vary priors/effect sizes without changing arm matching.",
        :high_stakes => "High consequence multiplier in permission only.",
        :low_stakes => "Low consequence multiplier in permission only.",
        :outcome_risk_weight => "Half of expected permission cost concerns flooding/collapse.",
        :responsibility_risk_weight => "Co-protection contributes separately to expected cost.",
        :partner_risk_weight => "Partner policy contributes separately to expected cost.",
        :refusal_cost => "Cost of maintaining protection in the policy comparison.",
        :decision_temperature => "Soft policy-selection temperature.",
        :future_stakes_multiplier => "Healing future reduces, but does not erase, contact risk.",
        :hope_value => "Value of a representable healed future.",
        :protector_role_value => "Future value when the protector retains a chosen role.",
        :obsolescence_penalty => "Cost when the same future discards the protector.",
        :transfer_epsilon => "Algorithmic strict-comparison tolerance.",
        :chance_tolerance => "Spec §6.5 chance band.",
        :refusal_accuracy_threshold => "Spec §6.5 post-refusal threshold.",
        :stakes_variance_threshold => "Spec §6.5 stakes-attributable variance threshold.",
        :transfer_world_threshold => "Spec §6.5 confirmatory world count.",
        :hope_shift_margin => "Pilot-frozen permission-shift margin.",
        :hope_flat_tolerance => "Floating-point audit tolerance for flat posteriors.",
        :high_diagnosticity => "Failure log-evidence under diagnostic attribution.",
        :low_diagnosticity => "Failure log-evidence under non-diagnostic attribution.",
        :smooth_success_log_bayes => "Log-evidence from one explainable smooth success.",
        :repair_log_bayes => "Log-evidence from repair inexplicable under the old model.",
        :repair_smooth_successes_k => "Pilot-frozen smooth-success comparator.",
    )
    configured = [(name, getfield(config, name), rationales[name])
        for name in fieldnames(ProtectorTrustConfig)]
    safeguards = [
        (:chance_accuracy, 0.50,
            "Posterior mass under the symmetric two-type prior."),
        (:probability_floor, 0.05,
            "Numerical safeguard on jittered skeptical priors."),
        (:probability_ceiling, 0.95,
            "Numerical safeguard on jittered skeptical priors."),
        (:base_bundle_normalization_tolerance, 1.0e-12,
            "Floating-point structural-audit tolerance."),
    ]
    return vcat(configured, safeguards)
end

function self_check(config::ProtectorTrustConfig = ProtectorTrustConfig())
    protector = default_protector(config)
    before = posterior_snapshot(protector)
    permission_probability(protector, config.low_stakes; config = config)
    after = posterior_snapshot(protector)
    return (
        channels_match_experiment_43 =
            protector.channels == IFSBundleInquiry.BUNDLE_CHANNELS,
        base_bundle_normalized =
            maximum(abs.(sum(protector.base_conditional; dims = 2) .- 1)) <
                1.0e-12,
        stakes_absent_from_evidence =
            !(:stakes in fieldnames(TrustEvidence)),
        permission_does_not_update =
            snapshots_equal(before, after),
        seed_blocks_disjoint =
            isempty(intersect(config.pilot_seeds, config.confirmation_seeds)),
    )
end

end
