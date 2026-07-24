module ExilingEmergence

using Random
using Statistics
using Main.IFSBundleInquiry

export ExilingConfig, ProtectivePolicy, VulnerableBundle, policy_expected_cost,
    select_policy, make_repertoire, register_contact!, run_world, run_block,
    summarize_block, magic_numbers, self_check

const POLICIES = (:exclusion, :hypervigilance, :internal_attack, :oscillation)
const REGIME_SEED_STRIDE = 1000
const CONTACT_SEED_OFFSET = 9000
const BUNDLE_NORMALIZATION_TOLERANCE = 1.0e-12

Base.@kwdef struct ExilingConfig
    pilot_seeds::Vector{Int} = collect(14801:14810)
    confirmation_seeds::Vector{Int} = collect(14851:14870)
    episodes::Int = 64
    contact_attempt_rate::Float64 = 0.28
    prior_aloneness_alpha::Float64 = 3.10
    prior_aloneness_beta::Float64 = 1.90
    rejection_evidence_reliability::Float64 = 0.78
    failure_cost::Float64 = 1.00
    favorable_direct_cost::Float64 = 0.18
    unfavorable_direct_cost::Float64 = 0.64
    favorable_reliability::Float64 = 0.91
    unfavorable_reliability::Float64 = 0.68
    cost_jitter_sd::Float64 = 0.025
    reliability_jitter_sd::Float64 = 0.020
    probability_floor::Float64 = 0.02
    probability_ceiling::Float64 = 0.98
    static_epsilon::Float64 = 1.0e-12
    exclusion_favorable_threshold::Int = 16
    competitor_exclusion_ceiling::Int = 4
end

struct ProtectivePolicy
    name::Symbol
    direct_cost::Float64
    reliability::Float64
end

"""
Experiment 43-form vulnerable bundle with a mutable relational prior.

`register_contact!` is the Experiment 49 extension point: a protector gate can
decide whether an attempted contact is suppressed and whether that event is
available on the registration channel, without replacing this bundle.
"""
mutable struct VulnerableBundle
    channels::NTuple{4, Symbol}
    base_conditional::Matrix{Float64}
    aloneness_probability::Float64
    registered_rejections::Int
end

function VulnerableBundle(config::ExilingConfig = ExilingConfig())
    prior = config.prior_aloneness_alpha /
        (config.prior_aloneness_alpha + config.prior_aloneness_beta)
    return VulnerableBundle(IFSBundleInquiry.BUNDLE_CHANNELS,
        IFSBundleInquiry.target_conditional_table(), prior, 0)
end

policy_expected_cost(policy::ProtectivePolicy,
        config::ExilingConfig = ExilingConfig()) =
    policy.direct_cost + config.failure_cost * (1 - policy.reliability)

"""
Select the minimum-expected-cost policy.

The function accepts only a repertoire and the common failure cost. It cannot
read a world's validation label, intended winner, or registration setting.
"""
function select_policy(repertoire,
        config::ExilingConfig = ExilingConfig())
    costs = policy_expected_cost.(repertoire, Ref(config))
    return repertoire[argmin(costs)], costs
end

function make_repertoire(rng::AbstractRNG, favorable::Symbol,
        config::ExilingConfig = ExilingConfig())
    favorable in POLICIES ||
        throw(ArgumentError("unknown favorable policy: $favorable"))
    return [ProtectivePolicy(
        name,
        max(0.0, (name == favorable ? config.favorable_direct_cost :
            config.unfavorable_direct_cost) +
            config.cost_jitter_sd * randn(rng)),
        clamp((name == favorable ? config.favorable_reliability :
            config.unfavorable_reliability) +
            config.reliability_jitter_sd * randn(rng),
            config.probability_floor, config.probability_ceiling),
    ) for name in POLICIES]
end

function bayes_rejection_update(prior::Float64, reliability::Float64)
    numerator = prior * reliability
    denominator = numerator + (1 - prior) * (1 - reliability)
    return numerator / denominator
end

"""
Expose a suppressed contact attempt to the vulnerable bundle.

No observation and no update occur when registration is closed. An open
channel represents a suppressed attempt as rejection and updates the relational
prior by the frozen likelihood ratio.
"""
function register_contact!(bundle::VulnerableBundle;
        contact_attempted::Bool, suppressed::Bool, registration_open::Bool,
        config::ExilingConfig = ExilingConfig())
    if contact_attempted && suppressed && registration_open
        bundle.aloneness_probability = bayes_rejection_update(
            bundle.aloneness_probability,
            config.rejection_evidence_reliability)
        bundle.registered_rejections += 1
    end
    return bundle
end

function consequence_arm(attempts, selected_policy::Symbol,
        registration_open::Bool, config::ExilingConfig)
    bundle = VulnerableBundle(config)
    initial = bundle.aloneness_probability
    suppressed = selected_policy == :exclusion
    maximum_episode_delta = 0.0
    for attempted in attempts
        before = bundle.aloneness_probability
        register_contact!(bundle; contact_attempted = attempted,
            suppressed = suppressed, registration_open = registration_open,
            config = config)
        maximum_episode_delta = max(maximum_episode_delta,
            abs(bundle.aloneness_probability - before))
    end
    return (
        initial_prior = initial,
        final_prior = bundle.aloneness_probability,
        delta_prior = bundle.aloneness_probability - initial,
        maximum_episode_delta = maximum_episode_delta,
        registered_rejections = bundle.registered_rejections,
    )
end

function regime_result(seed::Int, favorable::Symbol, config::ExilingConfig)
    rng = MersenneTwister(seed +
        REGIME_SEED_STRIDE * findfirst(==(favorable), POLICIES))
    repertoire = make_repertoire(rng, favorable, config)
    selected, expected_costs = select_policy(repertoire, config)
    return (
        selected = selected.name,
        selected_expected_cost = minimum(expected_costs),
        favorable_expected_cost =
            expected_costs[findfirst(==(favorable), POLICIES)],
        favorable_is_cheapest =
            argmin(expected_costs) == findfirst(==(favorable), POLICIES),
        repertoire = repertoire,
        expected_costs = expected_costs,
    )
end

function run_world(seed::Int; stage::Symbol = :pilot,
        config::ExilingConfig = ExilingConfig())
    regimes = Dict(policy => regime_result(seed, policy, config)
        for policy in POLICIES)
    exclusion_result = regimes[:exclusion]
    attempt_rng = MersenneTwister(seed + CONTACT_SEED_OFFSET)
    attempts = rand(attempt_rng, config.episodes) .<
        config.contact_attempt_rate
    registration_off = consequence_arm(attempts,
        exclusion_result.selected, false, config)
    registration_on = consequence_arm(attempts,
        exclusion_result.selected, true, config)
    registration_ablated = consequence_arm(attempts,
        exclusion_result.selected, false, config)
    return (
        stage = String(stage),
        seed = seed,
        exclusion_regime_selection = String(regimes[:exclusion].selected),
        hypervigilance_regime_selection =
            String(regimes[:hypervigilance].selected),
        internal_attack_regime_selection =
            String(regimes[:internal_attack].selected),
        oscillation_regime_selection = String(regimes[:oscillation].selected),
        exclusion_selected_when_competitor_favorable =
            any(regimes[policy].selected == :exclusion
                for policy in POLICIES if policy != :exclusion),
        each_favorable_policy_cheapest =
            all(regimes[policy].favorable_is_cheapest for policy in POLICIES),
        contact_attempts = count(attempts),
        selected_policy_matched_across_registration = true,
        contact_stream_matched_across_registration = true,
        prior_initial = registration_off.initial_prior,
        prior_off_final = registration_off.final_prior,
        prior_off_delta = registration_off.delta_prior,
        prior_off_maximum_episode_delta =
            registration_off.maximum_episode_delta,
        prior_on_final = registration_on.final_prior,
        prior_on_delta = registration_on.delta_prior,
        prior_on_maximum_episode_delta =
            registration_on.maximum_episode_delta,
        prior_ablation_final = registration_ablated.final_prior,
        prior_ablation_delta = registration_ablated.delta_prior,
        prior_ablation_maximum_episode_delta =
            registration_ablated.maximum_episode_delta,
        registered_rejections_off =
            registration_off.registered_rejections,
        registered_rejections_on =
            registration_on.registered_rejections,
        registered_rejections_ablation =
            registration_ablated.registered_rejections,
        exclusion_expected_cost =
            regimes[:exclusion].selected_expected_cost,
        hypervigilance_expected_cost =
            regimes[:hypervigilance].selected_expected_cost,
        internal_attack_expected_cost =
            regimes[:internal_attack].selected_expected_cost,
        oscillation_expected_cost =
            regimes[:oscillation].selected_expected_cost,
    )
end

run_block(seeds; stage::Symbol,
        config::ExilingConfig = ExilingConfig()) =
    [run_world(seed; stage = stage, config = config) for seed in seeds]

function summarize_block(rows,
        config::ExilingConfig = ExilingConfig())
    worlds = length(rows)
    exclusion_favorable_wins = count(row ->
        row.exclusion_regime_selection == "exclusion", rows)
    competitor_exclusion_worlds = count(row ->
        row.exclusion_selected_when_competitor_favorable, rows)
    favorable_wins = Dict(String(policy) => count(row ->
        getproperty(row, Symbol(String(policy), "_regime_selection")) ==
            String(policy), rows) for policy in POLICIES)
    static_worlds = count(row ->
        row.prior_off_maximum_episode_delta <= config.static_epsilon, rows)
    strengthening_worlds = count(row ->
        row.prior_on_delta > config.static_epsilon, rows)
    ablation_static_worlds = count(row ->
        row.prior_ablation_maximum_episode_delta <= config.static_epsilon,
        rows)
    toggle_only_worlds = count(row ->
        row.selected_policy_matched_across_registration &&
        row.contact_stream_matched_across_registration, rows)
    scale_threshold(threshold) = min(threshold, worlds)
    criteria = (
        policy_selection =
            exclusion_favorable_wins >=
                scale_threshold(config.exclusion_favorable_threshold) &&
            competitor_exclusion_worlds <=
                min(config.competitor_exclusion_ceiling, worlds) &&
            all(value > 0 for value in values(favorable_wins)),
        starvation =
            static_worlds == worlds,
        confirmation =
            strengthening_worlds == worlds &&
            ablation_static_worlds == worlds,
        toggle_separation =
            toggle_only_worlds == worlds &&
            static_worlds == worlds &&
            strengthening_worlds == worlds,
    )
    return (
        worlds = worlds,
        selection = (
            exclusion_favorable_wins = exclusion_favorable_wins,
            exclusion_in_competitor_favorable_worlds =
                competitor_exclusion_worlds,
            favorable_policy_wins = favorable_wins,
        ),
        consequences = (
            starvation_static_worlds = static_worlds,
            confirmation_strengthening_worlds = strengthening_worlds,
            ablation_static_worlds = ablation_static_worlds,
            toggle_only_matched_worlds = toggle_only_worlds,
            maximum_off_episode_delta =
                maximum(row.prior_off_maximum_episode_delta for row in rows),
            maximum_ablation_episode_delta =
                maximum(row.prior_ablation_maximum_episode_delta
                    for row in rows),
            minimum_on_delta =
                minimum(row.prior_on_delta for row in rows),
            mean_contact_attempts =
                mean(row.contact_attempts for row in rows),
        ),
        criteria = criteria,
        all_criteria_pass = all(values(criteria)),
    )
end

function magic_numbers(config::ExilingConfig = ExilingConfig())
    rationales = Dict(
        :pilot_seeds => "Ten-world pilot namespace.",
        :confirmation_seeds => "Fresh, disjoint twenty-world namespace.",
        :episodes => "Matched observation budget for every registration arm.",
        :contact_attempt_rate => "Base-rate pressure from the vulnerable bundle.",
        :prior_aloneness_alpha => "Prior pseudo-count supporting 'alone with this'.",
        :prior_aloneness_beta => "Counterweight keeping the prior non-degenerate.",
        :rejection_evidence_reliability => "Likelihood that a registered suppressed attempt denotes rejection.",
        :failure_cost => "Common consequence cost for unreliable protection.",
        :favorable_direct_cost => "Low policy burden in a policy's favorable regime.",
        :unfavorable_direct_cost => "Higher burden outside a policy's favorable regime.",
        :favorable_reliability => "Reliable protection in the favorable regime.",
        :unfavorable_reliability => "Imperfect protection outside the favorable regime.",
        :cost_jitter_sd => "Authored between-world variation in direct costs.",
        :reliability_jitter_sd => "Authored between-world variation in reliability.",
        :probability_floor => "Numerical bound on jittered reliability.",
        :probability_ceiling => "Numerical bound on jittered reliability.",
        :static_epsilon => "Pilot-frozen operational tolerance for a static prior.",
        :exclusion_favorable_threshold => "Spec §7.4 confirmatory lower bound.",
        :competitor_exclusion_ceiling => "Spec §7.4 confirmatory upper bound.",
    )
    configured = [(name, getfield(config, name), rationales[name])
        for name in fieldnames(ExilingConfig)]
    implementation = [
        (:policy_count, length(POLICIES),
            "The four protective policies named by spec §7.3."),
        (:regime_seed_stride, REGIME_SEED_STRIDE,
            "Separates matched policy-regime random streams."),
        (:contact_seed_offset, CONTACT_SEED_OFFSET,
            "Separates contact attempts from policy parameters."),
        (:bundle_normalization_tolerance, BUNDLE_NORMALIZATION_TOLERANCE,
            "Floating-point structural-audit tolerance."),
    ]
    return vcat(configured, implementation)
end

function self_check(config::ExilingConfig = ExilingConfig())
    bundle = VulnerableBundle(config)
    dummy = [ProtectivePolicy(policy, config.favorable_direct_cost +
        (index - 1) * config.unfavorable_direct_cost,
        config.favorable_reliability)
        for (index, policy) in enumerate(POLICIES)]
    selected, _ = select_policy(dummy, config)
    before = bundle.aloneness_probability
    register_contact!(bundle; contact_attempted = true, suppressed = true,
        registration_open = false, config = config)
    return (
        channels_match_experiment_43 =
            bundle.channels == IFSBundleInquiry.BUNDLE_CHANNELS,
        base_bundle_normalized =
            maximum(abs.(sum(bundle.base_conditional; dims = 2) .- 1)) <
                BUNDLE_NORMALIZATION_TOLERANCE,
        closed_registration_is_no_update =
            bundle.aloneness_probability == before,
        policy_selector_has_no_regime_argument =
            !(:favorable in fieldnames(ProtectivePolicy)),
        registration_absent_from_policy =
            !(:registration_open in fieldnames(ProtectivePolicy)),
        selector_returns_cheapest =
            selected.name == POLICIES[1],
        seed_blocks_disjoint =
            isempty(intersect(config.pilot_seeds, config.confirmation_seeds)),
    )
end

end
