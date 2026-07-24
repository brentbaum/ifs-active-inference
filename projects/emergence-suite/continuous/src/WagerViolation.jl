module WagerViolation

using LinearAlgebra
using Random
using Statistics
using Main.IFSBundleInquiry
using Main.FormationSubstrateTriad

export WagerViolationConfig, organization_components, organization_match,
    run_pair, run_block, summarize_block, machinery_audit,
    machinery_ablation, power_curve, self_check

const ARMS = (:carrier_inert, :carrier_active)

Base.@kwdef struct WagerViolationConfig
    pilot_seeds::Vector{Int} = collect(18401:18410)
    confirmation_seeds::Vector{Int} = collect(18501:18520)
    sessions::Int = 12
    corrective_evidence_sd::Float64 = 0.06
    corrective_target_scale::Float64 = -0.35
    base_coupling_learning_rate::Float64 = 0.08
    low_coupling_plasticity::Float64 = 0.0
    high_coupling_plasticity::Float64 = 0.30
    maximum_learning_rate::Float64 = 0.85
    match_tolerance::Float64 = 1.0e-12
    inert_divergence_tolerance::Float64 = 0.02
    active_divergence_required::Float64 = 0.10
    alpha_two_sided::Float64 = 0.05
    target_power::Float64 = 0.80
    z_alpha_two_sided::Float64 = 1.959963984540054
    z_power::Float64 = 0.8416212335729143
    measurement_noise_levels::Vector{Float64} =
        [0.0, 0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30]
end

function organization_components(organization::FormationSubstrateTriad.PartOrganization)
    return (
        bundle = collect(organization.bundle),
        couplings = collect(organization.couplings),
        precisions = collect(organization.precisions),
        field_profile = collect(organization.field_profile),
    )
end

function organization_vector(organization::FormationSubstrateTriad.PartOrganization)
    components = organization_components(organization)
    return vcat(components.bundle, components.couplings,
        components.precisions, components.field_profile)
end

function organization_match(first, second; tolerance = 1.0e-12)
    first_components = organization_components(first)
    second_components = organization_components(second)
    component_differences = (
        bundle = maximum(abs.(first_components.bundle .-
            second_components.bundle)),
        couplings = maximum(abs.(first_components.couplings .-
            second_components.couplings)),
        precisions = maximum(abs.(first_components.precisions .-
            second_components.precisions)),
        field_profile = maximum(abs.(first_components.field_profile .-
            second_components.field_profile)),
    )
    maximum_difference = maximum(values(component_differences))
    return (
        component_max_abs_difference = component_differences,
        maximum_abs_difference = maximum_difference,
        within_tolerance = maximum_difference <= tolerance,
        bitwise_equal = isequal(first, second),
    )
end

function matched_pair(seed::Int, config::WagerViolationConfig)
    source = FormationSubstrateTriad.generate_world(seed, :prepared)
    initial = source.first_organization
    # Deep materialization prevents shared-object identity from masquerading as
    # matching. PartOrganization is immutable, but each side is reconstructed.
    low_organization = FormationSubstrateTriad.PartOrganization(
        Tuple(initial.bundle), Tuple(initial.couplings),
        Tuple(initial.precisions), Tuple(initial.field_profile))
    high_organization = FormationSubstrateTriad.PartOrganization(
        Tuple(initial.bundle), Tuple(initial.couplings),
        Tuple(initial.precisions), Tuple(initial.field_profile))
    affect, policy = initial.bundle[1], initial.bundle[3]
    low_carrier = FormationSubstrateTriad.PreparedCarrier(
        10_001, affect, policy, config.low_coupling_plasticity)
    high_carrier = FormationSubstrateTriad.PreparedCarrier(
        10_002, affect, policy, config.high_coupling_plasticity)
    return (
        low_organization = low_organization,
        high_organization = high_organization,
        low_carrier = low_carrier,
        high_carrier = high_carrier,
    )
end

function corrective_stream(seed::Int, initial_couplings, config)
    rng = MersenneTwister(seed + 4_600_046)
    target = config.corrective_target_scale .* collect(initial_couplings)
    evidence = [target[coupling] +
        config.corrective_evidence_sd * randn(rng)
        for session in 1:config.sessions, coupling in 1:2]
    return target, evidence
end

function rematerialize(initial, couplings)
    coordinates = [initial.bundle[1], couplings[1],
        initial.bundle[3], couplings[2]]
    return FormationSubstrateTriad.materialize_organization(coordinates)
end

function transition(initial, carrier, evidence, arm::Symbol, config;
        ablate_carrier_read::Bool = false)
    arm in ARMS || throw(ArgumentError("unknown arm: $arm"))
    couplings = collect(initial.couplings)
    trajectory = [copy(couplings)]
    for session in axes(evidence, 1)
        carrier_increment = arm == :carrier_active && !ablate_carrier_read ?
            carrier.coupling_plasticity : 0.0
        learning_rate = clamp(config.base_coupling_learning_rate +
            carrier_increment, 0.0, config.maximum_learning_rate)
        # Corrective evidence is precision-weighted using the fixed organization
        # profile. coupling_plasticity is not part of that profile.
        organization_precision = collect(initial.precisions)[[2, 4]]
        normalized_precision = organization_precision ./ maximum(organization_precision)
        couplings .+= learning_rate .* normalized_precision .*
            (view(evidence, session, :) .- couplings)
        push!(trajectory, copy(couplings))
    end
    organizations = [rematerialize(initial, point) for point in trajectory]
    return (
        trajectory = trajectory,
        organizations = organizations,
        final_organization = last(organizations),
    )
end

function trajectory_divergence(first, second)
    first_matrix = reduce(hcat, first.trajectory)
    second_matrix = reduce(hcat, second.trajectory)
    # Baseline is excluded because it is audited separately and identically zero.
    differences = first_matrix[:, 2:end] .- second_matrix[:, 2:end]
    return sqrt(mean(differences .^ 2))
end

function run_pair(seed::Int, arm::Symbol;
        stage::Symbol = :pilot,
        config::WagerViolationConfig = WagerViolationConfig(),
        ablate_carrier_read::Bool = false)
    pair = matched_pair(seed, config)
    matching = organization_match(pair.low_organization,
        pair.high_organization; tolerance = config.match_tolerance)
    target, evidence = corrective_stream(seed,
        pair.low_organization.couplings, config)
    low = transition(pair.low_organization, pair.low_carrier, evidence, arm,
        config; ablate_carrier_read = ablate_carrier_read)
    high = transition(pair.high_organization, pair.high_carrier, evidence, arm,
        config; ablate_carrier_read = ablate_carrier_read)
    divergence = trajectory_divergence(low, high)
    return (
        stage = String(stage),
        seed = seed,
        arm = String(arm),
        organization_match_max_abs = matching.maximum_abs_difference,
        organization_match_bitwise = matching.bitwise_equal,
        organization_match_within_tolerance = matching.within_tolerance,
        match_bundle_max_abs =
            matching.component_max_abs_difference.bundle,
        match_couplings_max_abs =
            matching.component_max_abs_difference.couplings,
        match_precisions_max_abs =
            matching.component_max_abs_difference.precisions,
        match_field_profile_max_abs =
            matching.component_max_abs_difference.field_profile,
        low_carrier_plasticity = pair.low_carrier.coupling_plasticity,
        high_carrier_plasticity = pair.high_carrier.coupling_plasticity,
        plasticity_difference = pair.high_carrier.coupling_plasticity -
            pair.low_carrier.coupling_plasticity,
        corrective_target_coupling_1 = target[1],
        corrective_target_coupling_2 = target[2],
        low_final_coupling_1 = low.final_organization.couplings[1],
        low_final_coupling_2 = low.final_organization.couplings[2],
        high_final_coupling_1 = high.final_organization.couplings[1],
        high_final_coupling_2 = high.final_organization.couplings[2],
        revision_trajectory_divergence = divergence,
        carrier_read_ablated = ablate_carrier_read,
    )
end

function run_block(seeds; stage::Symbol,
        config::WagerViolationConfig = WagerViolationConfig())
    return [run_pair(seed, arm; stage = stage, config = config)
        for seed in seeds for arm in ARMS]
end

function summarize_block(rows,
        config::WagerViolationConfig = WagerViolationConfig())
    inert = [row.revision_trajectory_divergence for row in rows
        if row.arm == "carrier_inert"]
    active = [row.revision_trajectory_divergence for row in rows
        if row.arm == "carrier_active"]
    matches = [row.organization_match_max_abs for row in rows]
    return (
        world_count = length(unique(row.seed for row in rows)),
        organization_matching = (
            maximum_abs_difference = maximum(matches),
            all_bitwise_equal = all(row.organization_match_bitwise for row in rows),
            all_within_tolerance =
                all(row.organization_match_within_tolerance for row in rows),
        ),
        carrier_inert = (
            mean_divergence = mean(inert),
            maximum_divergence = maximum(inert),
            tolerance = config.inert_divergence_tolerance,
        ),
        carrier_active = (
            mean_divergence = mean(active),
            minimum_divergence = minimum(active),
            maximum_divergence = maximum(active),
            sd_divergence = length(active) > 1 ? std(active) : 0.0,
            required = config.active_divergence_required,
        ),
        criteria = (
            criterion_1_inert_invariance =
                maximum(inert) <= config.inert_divergence_tolerance,
            criterion_2_active_divergence =
                mean(active) >= config.active_divergence_required &&
                all(row.organization_match_within_tolerance for row in rows),
            organization_matching_verified =
                all(row.organization_match_within_tolerance for row in rows) &&
                all(row.organization_match_bitwise for row in rows),
        ),
    )
end

"""
Analytic inventory of state-update equations in the two required source files.
The table distinguishes therapeutic/revision transitions from formation and
residue operations so an organization-only claim is not overgeneralized.
"""
function machinery_audit()
    return [
        (
            file = "src/IFSBundleInquiry.jl",
            lines = "68-70",
            equation = "update_policy!",
            inputs = "policy-count state; context; selected channel",
            classification = "organization + neither",
            carrier_read = false,
            transition_scope = "policy learning",
        ),
        (
            file = "src/IFSBundleInquiry.jl",
            lines = "168-170",
            equation = "update!(JointBundleLearner)",
            inputs = "bundle-count state; identity root; four-element bundle",
            classification = "organization + neither",
            carrier_read = false,
            transition_scope = "bundle learning",
        ),
        (
            file = "src/IFSBundleInquiry.jl",
            lines = "232-246",
            equation = "update_forecaster!",
            inputs = "precision state; context; posterior field; observed channels; fixed config",
            classification = "organization + neither",
            carrier_read = false,
            transition_scope = "precision-field learning",
        ),
        (
            file = "src/IFSBundleInquiry.jl",
            lines = "332-363",
            equation = "bundle_branch_posterior",
            inputs = "observation; candidate cause; field mean/variance; channel; fixed config",
            classification = "organization + neither",
            carrier_read = false,
            transition_scope = "state inference",
        ),
        (
            file = "src/IFSBundleInquiry.jl",
            lines = "369-435",
            equation = "bundle_state_update",
            inputs = "observations; contact; channels; field; bundle table; optional conclusion; fixed config",
            classification = "organization + neither",
            carrier_read = false,
            transition_scope = "state inference",
        ),
        (
            file = "src/IFSBundleInquiry.jl",
            lines = "438-493",
            equation = "infer_bundle_episode",
            inputs = "observations; contact; channels; field prior; bundle table; fixed config",
            classification = "organization + neither",
            carrier_read = false,
            transition_scope = "revision/inference loop",
        ),
        (
            file = "src/FormationSubstrateTriad.jl",
            lines = "212-217",
            equation = "posterior_mean",
            inputs = "formation observations; prior mean; sample count; fixed config",
            classification = "organization + neither (prior may be carrier-authored upstream)",
            carrier_read = false,
            transition_scope = "formation, not intervention response",
        ),
        (
            file = "src/FormationSubstrateTriad.jl",
            lines = "220-225",
            equation = "prior_for_model",
            inputs = "model label; selected carrier id; carrier affect/policy priors",
            classification = "carrier + neither",
            carrier_read = true,
            transition_scope = "formation, not intervention response",
        ),
        (
            file = "src/FormationSubstrateTriad.jl",
            lines = "366-372",
            equation = "shared_carrier_shift",
            inputs = "model label; two organization targets; fixed model-level update rate",
            classification = "organization + neither",
            carrier_read = false,
            transition_scope = "interference transition",
        ),
        (
            file = "src/FormationSubstrateTriad.jl",
            lines = "375-389",
            equation = "interference_measure",
            inputs = "formation estimates; selected-carrier equality; organization targets; fixed config",
            classification = "organization + carrier identity + neither",
            carrier_read = true,
            transition_scope = "interference gate; no carrier parameter read",
        ),
        (
            file = "src/FormationSubstrateTriad.jl",
            lines = "392-425",
            equation = "selective_reduction",
            inputs = "model label; formation fit; carrier affect/policy priors; fixed retention rates",
            classification = "organization + carrier + neither",
            carrier_read = true,
            transition_scope = "post-formation residue, not corrective revision",
        ),
    ]
end

function machinery_ablation(
        config::WagerViolationConfig = WagerViolationConfig())
    triad_config = FormationSubstrateTriad.FormationTriadConfig()
    world = FormationSubstrateTriad.generate_world(18400, :prepared;
        config = triad_config)
    zero = FormationSubstrateTriad.default_carriers(
        coupling_plasticities = zeros(4))
    extreme = FormationSubstrateTriad.default_carriers(
        coupling_plasticities = [-10.0, 3.0, 50.0, 1_000.0])
    zero_fit = FormationSubstrateTriad.fit_formation(:recruitment,
        world.first_observations, world.first_target, zero, triad_config)
    extreme_fit = FormationSubstrateTriad.fit_formation(:recruitment,
        world.first_observations, world.first_target, extreme, triad_config)
    triad_difference = maximum(abs.(zero_fit.estimate .- extreme_fit.estimate))

    ifs_config = IFSBundleInquiry.IFSBundleConfig()
    learner_first = IFSBundleInquiry.JointBundleLearner(ifs_config)
    learner_second = IFSBundleInquiry.JointBundleLearner(ifs_config)
    bundle = first(IFSBundleInquiry.BUNDLE_CONFIGURATIONS)
    # The external carrier values deliberately have no input port.
    external_carrier_plasticities = (0.0, 1_000.0)
    IFSBundleInquiry.update!(learner_first, -1, bundle)
    IFSBundleInquiry.update!(learner_second, -1, bundle)
    ifs_difference = maximum(abs.(learner_first.counts .- learner_second.counts))

    active = run_pair(first(config.pilot_seeds), :carrier_active;
        stage = :ablation, config = config)
    ablated = run_pair(first(config.pilot_seeds), :carrier_active;
        stage = :ablation, config = config, ablate_carrier_read = true)
    inert = run_pair(first(config.pilot_seeds), :carrier_inert;
        stage = :ablation, config = config)
    return (
        formation_triad = (
            plasticity_values = (zero = [carrier.coupling_plasticity
                for carrier in zero], extreme = [carrier.coupling_plasticity
                for carrier in extreme]),
            maximum_estimate_difference = triad_difference,
            exact_invariance = triad_difference == 0.0,
        ),
        ifs_bundle_inquiry = (
            external_carrier_plasticities = external_carrier_plasticities,
            carrier_input_port_exists = false,
            maximum_update_difference = ifs_difference,
            exact_invariance = ifs_difference == 0.0,
        ),
        wager_transition = (
            active_divergence = active.revision_trajectory_divergence,
            ablated_divergence = ablated.revision_trajectory_divergence,
            inert_divergence = inert.revision_trajectory_divergence,
            ablation_restores_inert =
                ablated.revision_trajectory_divergence ==
                inert.revision_trajectory_divergence,
        ),
    )
end

function power_curve(pilot_rows,
        config::WagerViolationConfig = WagerViolationConfig())
    active = [row.revision_trajectory_divergence for row in pilot_rows
        if row.arm == "carrier_active"]
    between_world_sd = std(active)
    multiplier = config.z_alpha_two_sided + config.z_power
    return [(
        organization_measurement_noise_sd = noise,
        confirmation_pairs = length(config.confirmation_seeds),
        alpha_two_sided = config.alpha_two_sided,
        target_power = config.target_power,
        pilot_between_world_effect_sd = between_world_sd,
        minimum_detectable_carrier_effect =
            multiplier * sqrt(between_world_sd^2 + 2noise^2) /
            sqrt(length(config.confirmation_seeds)),
    ) for noise in config.measurement_noise_levels]
end

function self_check(config::WagerViolationConfig = WagerViolationConfig())
    @assert isempty(intersect(config.pilot_seeds, config.confirmation_seeds))
    @assert all(row.organization_match_bitwise for row in
        run_block(first(config.pilot_seeds, 2); stage = :smoke, config = config))
    inert = run_pair(first(config.pilot_seeds), :carrier_inert; config = config)
    active = run_pair(first(config.pilot_seeds), :carrier_active; config = config)
    @assert inert.revision_trajectory_divergence == 0.0
    @assert active.revision_trajectory_divergence > 0.0
    ablation = machinery_ablation(config)
    @assert ablation.formation_triad.exact_invariance
    @assert ablation.ifs_bundle_inquiry.exact_invariance
    @assert ablation.wager_transition.ablation_restores_inert
    @assert length(machinery_audit()) == 11
    return true
end

end
