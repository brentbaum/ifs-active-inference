module DyadGateDescent

using Random
using Statistics
using Main.IFSBundleInquiry
using Main.ProtectorTrust
using Main.ExilingEmergence

export DyadGateConfig, DyadScaffold, VulnerableDescentState,
    update_scaffold!, root_probability, run_world, run_block,
    summarize_block, magic_numbers, self_check

const INFERENTIAL_ARMS = (:coupled, :no_dyad, :decoupled)
const ALL_ARMS = (INFERENTIAL_ARMS..., :authored_access)
const ROOT_STREAM_OFFSET = 49_000
const TRUST_STREAM_OFFSET = 147_000
const DYAD_REGULATED_EMISSION_XOR = UInt64(0x51a7)
const DYAD_SIGNAL_LABELS = (
    :coherent_safe, :coherent_threat,
    :incoherent_safe, :incoherent_threat)
const DYAD_VOLATILITY_LIKELIHOOD = [
    0.06 0.10 0.20 0.42 0.62;
    0.18 0.22 0.28 0.30 0.25;
    0.30 0.30 0.26 0.17 0.09;
    0.28 0.24 0.18 0.08 0.03;
    0.18 0.14 0.08 0.03 0.01;
]

"""
Frozen Experiment 49 calibration.

The protector and vulnerable-bundle configs are reused without alteration.
Experiment-specific constants describe the Sim 5 dyad adapter, coupling
schedule, gate readout, and the thin Bayesian root adapter required because
Experiment 48 exposes a relational prior but no identity-root posterior.
"""
Base.@kwdef struct DyadGateConfig
    pilot_seeds::Vector{Int} = collect(34901:34910)
    confirmation_seeds::Vector{Int} = collect(34951:34970)
    episodes::Int = 18
    dyad_depth_grid::Vector{Float64} =
        [0.0, 0.25, 0.50, 0.75, 1.0]
    dyad_baseline_prior::Vector{Float64} =
        [0.18, 0.22, 0.24, 0.22, 0.14]
    dyad_transition_mix::Float64 = 0.08
    dyad_mapping_prior_count::Float64 = 1.0
    dyad_mapping_learning_rate::Float64 = 1.0
    dyad_mapping_settle_probability::Vector{Float64} =
        [0.90, 0.60, 0.64, 0.10]
    dyad_surface_coherent_probability::Float64 = 0.92
    dyad_channel_safe_probability::Float64 = 0.90
    dyad_regulated_by_depth::Vector{Float64} =
        [0.08, 0.16, 0.36, 0.74, 0.93]
    dyad_activation_drive::Float64 = 0.86
    dyad_activation_jitter::Float64 = 0.04
    dyad_volatility_precision::Float64 = 1.35
    dyad_coreg_precision::Float64 = 2.35
    dyad_part_precision::Float64 = 4.0
    dyad_context_precision::Float64 = 0.90
    dyad_part_slope::Float64 = 1.0
    dyad_context_slope::Float64 = 1.15
    evidence_packet_mass::Float64 = 1.0
    tolerated_true_probability::Float64 = 0.82
    competence_true_probability::Float64 = 0.84
    remaining_true_probability::Float64 = 0.90
    permission_threshold::Float64 = 0.50
    root_prior_positive::Float64 = 0.06
    root_revision_begun_probability::Float64 = 0.62
    root_revision_probability::Float64 = 0.80
    witnessing_precision::Float64 = 0.38
    contact_required::Int = 16
    control_contact_ceiling::Int = 2
    protector::ProtectorTrustConfig = ProtectorTrustConfig()
    vulnerable::ExilingConfig = ExilingConfig()
end

function validate_config(config::DyadGateConfig)
    depth_count = length(config.dyad_depth_grid)
    depth_count == 5 ||
        throw(ArgumentError("Sim 5 adapter requires five depth states"))
    length(config.dyad_baseline_prior) == depth_count ||
        throw(DimensionMismatch("dyad baseline prior must match depth grid"))
    length(config.dyad_regulated_by_depth) == depth_count ||
        throw(DimensionMismatch("regulated likelihood must match depth grid"))
    length(config.dyad_mapping_settle_probability) ==
        length(DYAD_SIGNAL_LABELS) ||
        throw(DimensionMismatch("mapping requires four joint signals"))
    abs(sum(config.dyad_baseline_prior) - 1) <= 1.0e-12 ||
        throw(ArgumentError("dyad baseline prior must sum to one"))
    all(value -> 0 < value < 1,
        config.dyad_mapping_settle_probability) ||
        throw(ArgumentError("mapping probabilities must be interior"))
    all(value -> 0 < value < 1,
        config.dyad_regulated_by_depth) ||
        throw(ArgumentError("regulated likelihoods must be interior"))
    config.dyad_mapping_prior_count > 0 ||
        throw(ArgumentError("mapping prior count must be positive"))
    config.dyad_mapping_learning_rate > 0 ||
        throw(ArgumentError("mapping learning rate must be positive"))
    config.dyad_volatility_precision > 0 ||
        throw(ArgumentError("volatility precision must be positive"))
    config.dyad_coreg_precision > 0 ||
        throw(ArgumentError("co-regulation precision must be positive"))
    return config
end

mutable struct DyadScaffold
    mapping_counts::Matrix{Float64}
    depth_posterior::Vector{Float64}
    route_accumulators::Vector{Float64}
    observations::Int
end

DyadScaffold(config::DyadGateConfig = DyadGateConfig()) =
    DyadScaffold(
        fill(config.dyad_mapping_prior_count,
            length(DYAD_SIGNAL_LABELS), 2),
        copy(config.dyad_baseline_prior),
        zeros(3), 0)

normalize_probability(values) = values ./ sum(values)

function learned_settle_probability(scaffold::DyadScaffold, signal::Int)
    counts = view(scaffold.mapping_counts, signal, :)
    return counts[1] / sum(counts)
end

function effective_precisions(depth_posterior, config::DyadGateConfig)
    expected_depth = sum(depth_posterior .* config.dyad_depth_grid)
    part = exp(log(config.dyad_part_precision) -
        config.dyad_part_slope * expected_depth)
    context = exp(log(config.dyad_context_precision) +
        config.dyad_context_slope * expected_depth)
    return (part = part, context = context,
        relational_share = context / (part + context))
end

function relational_precision_weight(depth_posterior,
        config::DyadGateConfig)
    current = effective_precisions(depth_posterior, config).relational_share
    high = zeros(length(config.dyad_depth_grid))
    high[end] = 1.0
    maximum_share = effective_precisions(high, config).relational_share
    return clamp(current / maximum_share, 0.0, 1.0)
end

function posterior_precision(depth_posterior)
    probabilities = normalize_probability(depth_posterior)
    entropy = -sum(probability <= 0 ? 0.0 :
        probability * log(probability) for probability in probabilities)
    return clamp(1 - entropy / log(length(probabilities)), 0.0, 1.0)
end

function volatility_observation(arousal::Float64)
    value = clamp(arousal, 0.0, 1.0)
    value < 0.18 && return 1
    value < 0.36 && return 2
    value < 0.56 && return 3
    value < 0.76 && return 4
    return 5
end

"""
Thin adapter to the committed Sim 5 dyad update.

The committed module exports only its full configuration runner, so Experiment
49 reproduces the load-bearing internal path here: joint therapist signal →
learned signal-to-settling mapping → categorical depth posterior → effective
relational precision. No protector evidence label enters this update.
"""
function update_scaffold!(scaffold::DyadScaffold, seed::Int, episode::Int,
        signal::Int, settled::Bool,
        config::DyadGateConfig = DyadGateConfig())
    outcome = settled ? 1 : 2
    scaffold.mapping_counts[signal, outcome] +=
        config.dyad_mapping_learning_rate
    learned_settle =
        learned_settle_probability(scaffold, signal)
    baseline_expected_depth = sum(
        config.dyad_baseline_prior .* config.dyad_depth_grid)
    capacity_mix = max(config.dyad_transition_mix,
        baseline_expected_depth^2)
    predicted = normalize_probability(
        (1 - capacity_mix) .*
            scaffold.depth_posterior .+
        capacity_mix .* config.dyad_baseline_prior)
    pre_effective =
        effective_precisions(scaffold.depth_posterior, config)
    capture_index = pre_effective.part /
        (pre_effective.part + pre_effective.context)
    jitter = config.dyad_activation_jitter *
        (((seed + episode) % 5) - 2)
    arousal = clamp(config.dyad_activation_drive *
        capture_index + jitter, 0.0, 1.0)
    volatility = volatility_observation(arousal)
    volatility_likelihood =
        view(DYAD_VOLATILITY_LIKELIHOOD, volatility, :) .^
            config.dyad_volatility_precision
    regulated = config.dyad_regulated_by_depth
    learned_likelihood = learned_settle .* regulated .+
        (1 - learned_settle) .* (1 .- regulated)
    scaffold.depth_posterior .= normalize_probability(
        predicted .* volatility_likelihood .*
            learned_likelihood .^
            config.dyad_coreg_precision)
    scaffold.observations += 1
    field_weight =
        relational_precision_weight(scaffold.depth_posterior, config)
    packets = zeros(Int, length(scaffold.route_accumulators))
    for route in eachindex(scaffold.route_accumulators)
        scaffold.route_accumulators[route] += field_weight
        while scaffold.route_accumulators[route] + eps() >=
                config.evidence_packet_mass
            scaffold.route_accumulators[route] -=
                config.evidence_packet_mass
            packets[route] += 1
        end
    end
    return (
        packets = packets,
        learned_settle = learned_settle,
        arousal = arousal,
        volatility_observation = volatility,
        field_weight = field_weight,
        posterior_precision =
            posterior_precision(scaffold.depth_posterior),
    )
end

"""
Experiment 48 bundle plus an inferred identity-root log odds.

This is a thin adapter rather than a replacement bundle. Contact observations
are scored with the bundle's own committed conditional table.
"""
mutable struct VulnerableDescentState
    bundle::ExilingEmergence.VulnerableBundle
    root_log_odds::Float64
    root_updates::Int
end

logistic(value) = inv(1 + exp(-value))
logit(probability) = log(clamp(probability, eps(), 1 - eps()) /
    (1 - clamp(probability, eps(), 1 - eps())))

VulnerableDescentState(config::DyadGateConfig = DyadGateConfig()) =
    VulnerableDescentState(
        ExilingEmergence.VulnerableBundle(config.vulnerable),
        logit(config.root_prior_positive), 0)

root_probability(state::VulnerableDescentState) =
    logistic(state.root_log_odds)

function sample_index(rng::AbstractRNG, probabilities)
    draw = rand(rng)
    cumulative = 0.0
    for index in eachindex(probabilities)
        cumulative += probabilities[index]
        draw <= cumulative && return index
    end
    return lastindex(probabilities)
end

function root_evidence_stream(seed::Int, config::DyadGateConfig)
    rng = MersenneTwister(seed + ROOT_STREAM_OFFSET)
    table = IFSBundleInquiry.target_conditional_table()
    return [sample_index(rng, view(table, 2, :))
        for _ in 1:config.episodes]
end

function update_root_from_witnessing!(state::VulnerableDescentState,
        configuration_index::Int, config::DyadGateConfig)
    table = state.bundle.base_conditional
    log_bayes = log(table[2, configuration_index] /
        table[1, configuration_index])
    state.root_log_odds += config.witnessing_precision * log_bayes
    state.root_updates += 1
    return root_probability(state)
end

function dyad_stream(seed::Int, config::DyadGateConfig)
    rng = Xoshiro(xor(UInt64(seed),
        DYAD_REGULATED_EMISSION_XOR))
    signals = Int[]
    settled = Bool[]
    for _ in 1:config.episodes
        coherent =
            rand(rng) < config.dyad_surface_coherent_probability
        safe = rand(rng) < config.dyad_channel_safe_probability
        signal = coherent ? (safe ? 1 : 2) : (safe ? 3 : 4)
        push!(signals, signal)
        push!(settled, rand(rng) <
            config.dyad_mapping_settle_probability[signal])
    end
    return signals, settled
end

function trust_stream(seed::Int, config::DyadGateConfig)
    rng = MersenneTwister(seed + TRUST_STREAM_OFFSET)
    return (
        tolerated = rand(rng, config.episodes) .<
            config.tolerated_true_probability,
        competence = rand(rng, config.episodes) .<
            config.competence_true_probability,
        remaining = rand(rng, config.episodes) .<
            config.remaining_true_probability,
    )
end

"""
Risk-model counterfactual that keeps every Experiment 47 route causal.

The existing baseline risk reads tolerated outcome, shared competence, and
partner policy. In the obsolete future, inferred shared competence determines
whether that full risk can be carried without the protector. This preserves the
supported risk-mixture form without adding a contact-enabling policy.
"""
function permission_readout(protector, config::DyadGateConfig)
    beliefs = protector.beliefs
    baseline_risk =
        config.protector.outcome_risk_weight *
            (1 - beliefs.tolerated_local[1]) +
        config.protector.responsibility_risk_weight *
            (1 - beliefs.system_competence) +
        config.protector.partner_risk_weight *
            (1 - beliefs.partner_relational)
    competence = beliefs.system_competence
    obsolete_risk =
        competence * baseline_risk + (1 - competence)
    allow_utility = config.protector.hope_value -
        config.protector.high_stakes * obsolete_risk
    refuse_utility = -config.protector.refusal_cost
    return logistic((allow_utility - refuse_utility) /
        config.protector.decision_temperature)
end

function ingest_route!(protector, route::Int, value::Bool,
        config::DyadGateConfig)
    evidence = if route == 1
        ProtectorTrust.TrustEvidence(
            tolerated = value, outcome_framing = :local)
    elseif route == 2
        ProtectorTrust.TrustEvidence(
            competence_demonstrated = value)
    elseif route == 3
        ProtectorTrust.TrustEvidence(
            refusal_response = value ? :remaining : :pressuring)
    else
        throw(ArgumentError("unknown protector route: $route"))
    end
    ProtectorTrust.ingest_evidence!(
        protector, evidence, config.protector)
end

function empty_event()
    return 0
end

"""
Run one of the three inferential arms.

There is no access argument and no gate object. At every episode, contact is
exactly the current protector permission comparison against the frozen
threshold. The arm changes only whether the matched dyad stream exists and
whether its precision-weighted packets reach `ingest_evidence!`.
"""
function run_gate_arm(seed::Int, arm::Symbol, stage::Symbol,
        config::DyadGateConfig, protector_jitter::Float64,
        dyad_signals, dyad_settled, trust, root_stream)
    arm in INFERENTIAL_ARMS || throw(ArgumentError(
        "inferential arm required, got $arm"))
    protector = ProtectorTrust.default_protector(
        config.protector; jitter = protector_jitter)
    vulnerable = VulnerableDescentState(config)
    scaffold = DyadScaffold(config)
    initial_permission = permission_readout(protector, config)
    permission_path = Float64[initial_permission]
    root_path = Float64[root_probability(vulnerable)]
    permission_rise_episode = empty_event()
    first_contact_episode = empty_event()
    revision_begin_episode = empty_event()
    revision_complete_episode = empty_event()
    contacts = 0
    potential_packets = zeros(Int, 3)
    ingested_packets = zeros(Int, 3)
    field_path = Float64[]
    learned_settle_path = Float64[]
    depth_precision_path = Float64[]
    dyad_present = arm != :no_dyad
    coupled = arm == :coupled

    for episode in 1:config.episodes
        scaffold_update = dyad_present ?
            update_scaffold!(scaffold, seed, episode,
                dyad_signals[episode],
                dyad_settled[episode], config) :
            (packets = zeros(Int, 3), learned_settle = 0.5,
                arousal = 0.0, volatility_observation = 0,
                field_weight = 0.0, posterior_precision = 0.0)
        potential_packets .+= scaffold_update.packets
        push!(field_path, scaffold_update.field_weight)
        push!(learned_settle_path, scaffold_update.learned_settle)
        push!(depth_precision_path,
            scaffold_update.posterior_precision)
        if coupled
            route_values = (
                trust.tolerated[episode],
                trust.competence[episode],
                trust.remaining[episode])
            for route in 1:3, _ in
                    1:scaffold_update.packets[route]
                ingest_route!(protector, route,
                    route_values[route], config)
                ingested_packets[route] += 1
            end
        end

        permission = permission_readout(protector, config)
        push!(permission_path, permission)
        if permission_rise_episode == 0 &&
                initial_permission < config.permission_threshold &&
                permission >= config.permission_threshold
            permission_rise_episode = episode
        end

        permitted = permission >= config.permission_threshold
        ExilingEmergence.register_contact!(vulnerable.bundle;
            contact_attempted = true, suppressed = !permitted,
            registration_open = true, config = config.vulnerable)
        if permitted
            contacts += 1
            first_contact_episode == 0 && (first_contact_episode = episode)
            posterior = update_root_from_witnessing!(
                vulnerable, root_stream[episode], config)
            if revision_begin_episode == 0 &&
                    posterior >= config.root_revision_begun_probability
                revision_begin_episode = episode
            end
            if revision_complete_episode == 0 &&
                    posterior >= config.root_revision_probability
                revision_complete_episode = episode
            end
        end
        push!(root_path, root_probability(vulnerable))
    end

    descent = revision_begin_episode > 0
    ordered = !descent || (
        permission_rise_episode > 0 &&
        permission_rise_episode < revision_begin_episode &&
        first_contact_episode <= revision_begin_episode)
    return (
        stage = String(stage),
        seed = seed,
        arm = String(arm),
        dyad_present = dyad_present,
        dyad_coupled_to_evidence = coupled,
        authored_access_used = false,
        dyad_coherent_safe_signals = dyad_present ?
            count(==(1), dyad_signals) : 0,
        dyad_settled_observations = dyad_present ?
            count(dyad_settled) : 0,
        dyad_field_weight_final =
            isempty(field_path) ? 0.0 : last(field_path),
        dyad_depth_precision_final =
            isempty(depth_precision_path) ? 0.0 :
                last(depth_precision_path),
        learned_settle_final =
            isempty(learned_settle_path) ? 0.5 :
                last(learned_settle_path),
        potential_outcome_packets = potential_packets[1],
        potential_competence_packets = potential_packets[2],
        potential_partner_packets = potential_packets[3],
        ingested_outcome_packets = ingested_packets[1],
        ingested_competence_packets = ingested_packets[2],
        ingested_partner_packets = ingested_packets[3],
        initial_permission = initial_permission,
        final_permission = last(permission_path),
        maximum_permission = maximum(permission_path),
        permission_rise_episode = permission_rise_episode,
        first_contact_episode = first_contact_episode,
        contact_achieved = first_contact_episode > 0,
        contact_episodes = contacts,
        initial_root_probability = first(root_path),
        final_root_probability = last(root_path),
        revision_begin_episode = revision_begin_episode,
        revision_complete_episode = revision_complete_episode,
        descent_occurred = descent,
        permission_before_revision = ordered,
        permission_to_revision_lag = descent ?
            revision_begin_episode - permission_rise_episode : 0,
        root_updates = vulnerable.root_updates,
        vulnerable_registered_rejections =
            vulnerable.bundle.registered_rejections,
        vulnerable_aloneness_final =
            vulnerable.bundle.aloneness_probability,
        dyad_field_path = join(field_path, ";"),
        permission_path = join(permission_path, ";"),
        root_path = join(root_path, ";"),
    )
end

"""
Historical authored-access calibration.

This comparator is deliberately isolated from `run_gate_arm`: it bypasses the
gate and exposes the full matched witnessing stream. It is never counted as an
inferential success and cannot alter any other arm.
"""
function run_authored_calibration(seed::Int, stage::Symbol,
        config::DyadGateConfig, protector_jitter::Float64,
        root_stream)
    protector = ProtectorTrust.default_protector(
        config.protector; jitter = protector_jitter)
    vulnerable = VulnerableDescentState(config)
    initial_permission = permission_readout(protector, config)
    permission_path = fill(initial_permission, config.episodes + 1)
    root_path = Float64[root_probability(vulnerable)]
    revision_begin_episode = 0
    revision_complete_episode = 0
    for episode in 1:config.episodes
        posterior = update_root_from_witnessing!(
            vulnerable, root_stream[episode], config)
        if revision_begin_episode == 0 &&
                posterior >= config.root_revision_begun_probability
            revision_begin_episode = episode
        end
        if revision_complete_episode == 0 &&
                posterior >= config.root_revision_probability
            revision_complete_episode = episode
        end
        push!(root_path, posterior)
    end
    return (
        stage = String(stage),
        seed = seed,
        arm = "authored_access",
        dyad_present = false,
        dyad_coupled_to_evidence = false,
        authored_access_used = true,
        dyad_coherent_safe_signals = 0,
        dyad_settled_observations = 0,
        dyad_field_weight_final = 0.0,
        dyad_depth_precision_final = 0.0,
        learned_settle_final = 0.5,
        potential_outcome_packets = 0,
        potential_competence_packets = 0,
        potential_partner_packets = 0,
        ingested_outcome_packets = 0,
        ingested_competence_packets = 0,
        ingested_partner_packets = 0,
        initial_permission = initial_permission,
        final_permission = initial_permission,
        maximum_permission = initial_permission,
        permission_rise_episode = 0,
        first_contact_episode = 1,
        contact_achieved = true,
        contact_episodes = config.episodes,
        initial_root_probability = first(root_path),
        final_root_probability = last(root_path),
        revision_begin_episode = revision_begin_episode,
        revision_complete_episode = revision_complete_episode,
        descent_occurred = revision_begin_episode > 0,
        permission_before_revision = false,
        permission_to_revision_lag = 0,
        root_updates = vulnerable.root_updates,
        vulnerable_registered_rejections =
            vulnerable.bundle.registered_rejections,
        vulnerable_aloneness_final =
            vulnerable.bundle.aloneness_probability,
        dyad_field_path = join(zeros(config.episodes), ";"),
        permission_path = join(permission_path, ";"),
        root_path = join(root_path, ";"),
    )
end

function run_world(seed::Int; stage::Symbol = :pilot,
        config::DyadGateConfig = DyadGateConfig())
    validate_config(config)
    world_rng = MersenneTwister(seed)
    protector_jitter = config.protector.world_jitter_sd * randn(world_rng)
    dyad_signals, dyad_settled = dyad_stream(seed, config)
    trust = trust_stream(seed, config)
    root_stream = root_evidence_stream(seed, config)
    inferential = [run_gate_arm(seed, arm, stage, config,
        protector_jitter, dyad_signals, dyad_settled, trust,
        root_stream)
        for arm in INFERENTIAL_ARMS]
    authored = run_authored_calibration(seed, stage, config,
        protector_jitter, root_stream)
    return vcat(inferential, [authored])
end

run_block(seeds; stage::Symbol,
        config::DyadGateConfig = DyadGateConfig()) =
    reduce(vcat, [run_world(seed; stage = stage, config = config)
        for seed in seeds])

function timing_distribution(rows)
    descents = [row for row in rows if row.descent_occurred]
    isempty(descents) && return (
        descent_worlds = 0,
        permission_rise_episodes = Int[],
        revision_begin_episodes = Int[],
        lags = Int[],
        permission_rise_minimum = nothing,
        permission_rise_median = nothing,
        permission_rise_maximum = nothing,
        revision_begin_minimum = nothing,
        revision_begin_median = nothing,
        revision_begin_maximum = nothing,
        lag_minimum = nothing,
        lag_median = nothing,
        lag_maximum = nothing,
    )
    permission = getfield.(descents, :permission_rise_episode)
    revision = getfield.(descents, :revision_begin_episode)
    lags = getfield.(descents, :permission_to_revision_lag)
    return (
        descent_worlds = length(descents),
        permission_rise_episodes = permission,
        revision_begin_episodes = revision,
        lags = lags,
        permission_rise_minimum = minimum(permission),
        permission_rise_median = median(permission),
        permission_rise_maximum = maximum(permission),
        revision_begin_minimum = minimum(revision),
        revision_begin_median = median(revision),
        revision_begin_maximum = maximum(revision),
        lag_minimum = minimum(lags),
        lag_median = median(lags),
        lag_maximum = maximum(lags),
    )
end

function summarize_arm(rows)
    return (
        worlds = length(rows),
        contact_worlds = count(row -> row.contact_achieved, rows),
        descent_worlds = count(row -> row.descent_occurred, rows),
        ordered_descent_worlds = count(row ->
            row.descent_occurred && row.permission_before_revision, rows),
        mean_initial_permission =
            mean(row.initial_permission for row in rows),
        mean_final_permission =
            mean(row.final_permission for row in rows),
        mean_final_root_probability =
            mean(row.final_root_probability for row in rows),
        mean_contact_episodes =
            mean(row.contact_episodes for row in rows),
        mean_ingested_evidence_packets =
            mean(row.ingested_outcome_packets +
                row.ingested_competence_packets +
                row.ingested_partner_packets for row in rows),
        mean_registered_rejections =
            mean(row.vulnerable_registered_rejections for row in rows),
        mean_final_aloneness =
            mean(row.vulnerable_aloneness_final for row in rows),
        mean_final_dyad_field_weight =
            mean(row.dyad_field_weight_final for row in rows),
        timing = timing_distribution(rows),
    )
end

function summarize_block(rows,
        config::DyadGateConfig = DyadGateConfig())
    arms = Dict(String(arm) => summarize_arm(
        [row for row in rows if row.arm == String(arm)])
        for arm in ALL_ARMS)
    worlds = arms["coupled"].worlds
    required = worlds == length(config.confirmation_seeds) ?
        config.contact_required : ceil(Int, 0.8 * worlds)
    ceiling = worlds == length(config.confirmation_seeds) ?
        config.control_contact_ceiling : floor(Int, 0.1 * worlds)
    inferential_rows = [row for row in rows
        if row.arm != "authored_access"]
    descent_rows = [row for row in inferential_rows if row.descent_occurred]
    criteria = (
        contact_separation =
            arms["coupled"].contact_worlds >= required &&
            arms["no_dyad"].contact_worlds <= ceiling &&
            arms["decoupled"].contact_worlds <= ceiling,
        permission_before_revision =
            all(row.permission_before_revision for row in descent_rows),
        no_authored_access_in_inferential_arms =
            all(!row.authored_access_used for row in inferential_rows),
    )
    return (
        worlds_per_arm = worlds,
        arms = arms,
        thresholds = (
            coupled_contact_required = required,
            control_contact_ceiling = ceiling,
            permission_threshold = config.permission_threshold,
            root_revision_begun_probability =
                config.root_revision_begun_probability,
        ),
        criteria = criteria,
        all_criteria_pass = all(values(criteria)),
    )
end

function magic_numbers(config::DyadGateConfig = DyadGateConfig())
    rationales = Dict(
        :pilot_seeds => "Ten-world pilot namespace following Experiments 47–48.",
        :confirmation_seeds => "Fresh, disjoint twenty-world namespace.",
        :episodes => "Moderate common dyad and witnessing evidence budget.",
        :dyad_depth_grid => "Committed Sim 5 categorical depth support.",
        :dyad_baseline_prior => "Committed Sim 5 dyad baseline depth prior.",
        :dyad_transition_mix => "Committed Sim 5 transition floor toward the dyad prior.",
        :dyad_mapping_prior_count => "Committed Sim 5 uniform count for each signal-outcome row.",
        :dyad_mapping_learning_rate => "Committed Sim 5 count increment per observed contingency.",
        :dyad_mapping_settle_probability => "Committed Sim 5 signal-to-settling contingencies.",
        :dyad_surface_coherent_probability => "Committed Sim 5 regulated surface emission.",
        :dyad_channel_safe_probability => "Committed Sim 5 regulated relational-channel emission.",
        :dyad_regulated_by_depth => "Committed Sim 5 co-regulation likelihood over depth.",
        :dyad_activation_drive => "Committed Sim 5 bundle-live activation strength.",
        :dyad_activation_jitter => "Committed Sim 5 deterministic arousal variation.",
        :dyad_volatility_precision => "Committed Sim 5 volatility-likelihood precision.",
        :dyad_coreg_precision => "Committed Sim 5 co-regulation likelihood precision.",
        :dyad_part_precision => "Committed Sim 5 base part precision.",
        :dyad_context_precision => "Committed Sim 5 base context precision.",
        :dyad_part_slope => "Committed Sim 5 depth-to-part precision slope.",
        :dyad_context_slope => "Committed Sim 5 depth-to-context precision slope.",
        :evidence_packet_mass => "One normalized relational-field unit supports one TrustEvidence packet per route.",
        :tolerated_true_probability => "Independent tolerated-outcome evidence generator.",
        :competence_true_probability => "Independent co-protection evidence generator.",
        :remaining_true_probability => "Independent partner-response evidence generator.",
        :permission_threshold => "Predeclared operational definition of protector permission rising.",
        :root_prior_positive => "Experiment 44 frozen-negative identity-root prior.",
        :root_revision_begun_probability => "Experiment 44 operational definition of revision beginning.",
        :root_revision_probability => "Experiment 44 operational definition of completed revision.",
        :witnessing_precision => "Moderate tempering of the committed bundle likelihood ratio.",
        :contact_required => "Spec §8.5 coupled confirmatory threshold.",
        :control_contact_ceiling => "Spec §8.5 no-dyad and decoupled ceiling.",
        :protector => "Unmodified committed Experiment 47 config.",
        :vulnerable => "Unmodified committed Experiment 48 config.",
    )
    configured = [(name, getfield(config, name), rationales[name])
        for name in fieldnames(DyadGateConfig)]
    implementation = [
        (:root_stream_offset, ROOT_STREAM_OFFSET,
            "Separates witnessing configurations from world jitter."),
        (:dyad_regulated_emission_xor,
            DYAD_REGULATED_EMISSION_XOR,
            "Committed Sim 5 regulated-emission RNG namespace."),
        (:dyad_volatility_likelihood,
            DYAD_VOLATILITY_LIKELIHOOD,
            "Committed Sim 5 five-state volatility likelihood."),
        (:trust_stream_offset, TRUST_STREAM_OFFSET,
            "Separates protector evidence signs from dyad learning and witnessing."),
        (:inferential_arm_count, length(INFERENTIAL_ARMS),
            "Coupled, no-dyad, and decoupled gate arms."),
        (:authored_calibration_count, 1,
            "Historical comparator isolated from inferential success."),
    ]
    return vcat(configured, implementation)
end

function self_check(config::DyadGateConfig = DyadGateConfig())
    rows = run_world(first(config.pilot_seeds);
        stage = :structural_audit, config = config)
    coupled = only(row for row in rows if row.arm == "coupled")
    decoupled = only(row for row in rows if row.arm == "decoupled")
    no_dyad = only(row for row in rows if row.arm == "no_dyad")
    protector = ProtectorTrust.default_protector(config.protector)
    baseline_permission = permission_readout(protector, config)
    route_effects = Float64[]
    for route in 1:3
        perturbed = deepcopy(protector)
        ingest_route!(perturbed, route, true, config)
        push!(route_effects,
            permission_readout(perturbed, config) -
                baseline_permission)
    end
    initial_aloneness =
        ExilingEmergence.VulnerableBundle(
            config.vulnerable).aloneness_probability
    return (
        seed_blocks_disjoint =
            isempty(intersect(config.pilot_seeds,
                config.confirmation_seeds)),
        vulnerable_bundle_reused =
            VulnerableDescentState(config).bundle isa
                ExilingEmergence.VulnerableBundle,
        protector_evidence_extension_reused =
            ProtectorTrust.TrustEvidence() isa
                ProtectorTrust.TrustEvidence,
        all_protector_routes_active =
            all(effect > 0 for effect in route_effects),
        protector_route_permission_effects = route_effects,
        sim5_mapping_adapter_active =
            coupled.dyad_field_weight_final > 0 &&
            coupled.dyad_depth_precision_final > 0,
        gate_is_permission_threshold =
            no_dyad.contact_achieved ==
                (no_dyad.maximum_permission >=
                    config.permission_threshold),
        coupled_decoupled_dyad_marginals_matched =
            coupled.dyad_coherent_safe_signals ==
                decoupled.dyad_coherent_safe_signals &&
            coupled.dyad_settled_observations ==
                decoupled.dyad_settled_observations &&
            coupled.dyad_field_weight_final ==
                decoupled.dyad_field_weight_final &&
            coupled.potential_outcome_packets ==
                decoupled.potential_outcome_packets &&
            coupled.potential_competence_packets ==
                decoupled.potential_competence_packets &&
            coupled.potential_partner_packets ==
                decoupled.potential_partner_packets,
        decoupled_ingests_no_evidence =
            decoupled.ingested_outcome_packets == 0 &&
            decoupled.ingested_competence_packets == 0 &&
            decoupled.ingested_partner_packets == 0,
        no_dyad_has_no_scaffold_packets =
            no_dyad.potential_outcome_packets == 0 &&
            no_dyad.potential_competence_packets == 0 &&
            no_dyad.potential_partner_packets == 0,
        closed_gate_has_no_root_update =
            !no_dyad.contact_achieved ? no_dyad.root_updates == 0 : true,
        experiment48_registration_active =
            no_dyad.vulnerable_registered_rejections ==
                config.episodes &&
            no_dyad.vulnerable_aloneness_final >
                initial_aloneness,
        authored_baseline_isolated =
            all(!row.authored_access_used for row in rows
                if row.arm != "authored_access"),
    )
end

end
