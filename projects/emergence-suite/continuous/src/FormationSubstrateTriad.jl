module FormationSubstrateTriad

using LinearAlgebra
using Random
using Statistics
using Main.IFSBundleInquiry

export FormationTriadConfig, PreparedCarrier, PartOrganization, default_carriers,
    capacity_audit, generate_world, run_world, run_block,
    summarize_block, run_exploratory_diagnostics,
    summarize_exploratory_diagnostics, self_check

const ORGANIZATION_CHANNELS = IFSBundleInquiry.BUNDLE_CHANNELS
const AFFECT_POLICY = (1, 3)
const BIOGRAPHICAL_COUPLINGS = (2, 4)
const MODEL_NAMES = (:assembly, :recruitment, :hybrid)
const CONDITIONS = (:prepared, :arbitrary, :shuffled)

"""
Persistent substrate used by recruitment and hybrid models.

`coupling_plasticity` is fixed at zero throughout Experiment 45 and is not read
by any transition equation here. Experiment 46 can reuse this type and pass a
non-zero value as its explicit carrier-level extension point.
"""
struct PreparedCarrier
    id::Int
    affect_prior::Float64
    policy_prior::Float64
    coupling_plasticity::Float64
end

"""
Experiment 43-compatible organization materialized from four free formation
coordinates. Bundle content, couplings, precisions, and the field profile stay
on the organization side of the frozen register; no carrier field appears here.
The precision and field profiles are fixed across models so the formation
comparison changes substrate, not evidence weighting.
"""
struct PartOrganization
    bundle::NTuple{4, Float64}
    couplings::NTuple{2, Float64}
    precisions::NTuple{4, Float64}
    field_profile::NTuple{4, Float64}
end

Base.@kwdef struct FormationTriadConfig
    pilot_seeds::Vector{Int} = collect(18101:18110)
    confirmation_seeds::Vector{Int} = collect(18201:18220)
    carrier_count::Int = 4
    parameter_count::Int = 4
    prior_sd::Float64 = 0.25
    observation_sd::Float64 = 0.55
    maximum_samples::Int = 72
    selection_samples::Int = 3
    formation_rmse_threshold::Float64 = 0.28
    stable_samples::Int = 2
    prepared_jitter_sd::Float64 = 0.10
    arbitrary_scale::Float64 = 0.65
    coupling_scale::Float64 = 0.38
    second_formation_offset::Float64 = 0.48
    recruitment_carrier_update::Float64 = 0.52
    hybrid_carrier_update::Float64 = 0.52
    assembly_coupling_retention::Float64 = 0.68
    hybrid_coupling_retention::Float64 = 0.62
    efficiency_advantage_required::Float64 = 0.20
    efficiency_vanish_threshold::Float64 = 0.05
    interference_margin::Float64 = 0.03
    residue_norm_threshold::Float64 = 0.15
    residue_ablation_threshold::Float64 = 0.10
    world_count_required::Int = 16
end

function default_carriers(; coupling_plasticities = zeros(4))
    length(coupling_plasticities) == 4 ||
        throw(ArgumentError("four coupling-plasticity values are required"))
    affect = (-1.20, -0.35, 0.55, 1.10)
    policy = (-0.95, 0.80, -0.45, 1.20)
    return [PreparedCarrier(index, affect[index], policy[index],
        Float64(coupling_plasticities[index])) for index in 1:4]
end

carrier_vector(carrier::PreparedCarrier) =
    [carrier.affect_prior, carrier.policy_prior]

function shuffled_carriers(carriers)
    policies = [carrier.policy_prior for carrier in carriers]
    shifted = circshift(policies, 1)
    return [PreparedCarrier(index, carriers[index].affect_prior,
        shifted[index], carriers[index].coupling_plasticity)
        for index in eachindex(carriers)]
end

function degraded_marginal_carriers(carriers)
    return [PreparedCarrier(index,
        carriers[index].affect_prior + 2.20,
        carriers[index].policy_prior - 2.20,
        carriers[index].coupling_plasticity)
        for index in eachindex(carriers)]
end

gaussian_entropy(dimensions, sd) =
    dimensions / 2 * log(2pi * exp(1) * sd^2)

function capacity_audit(config::FormationTriadConfig = FormationTriadConfig())
    conditional = gaussian_entropy(config.parameter_count, config.prior_sd)
    index_entropy = log(config.carrier_count)
    per_model = Dict(String(model) => (
        continuous_parameter_count = config.parameter_count,
        discrete_latent_categories = config.carrier_count,
        conditional_gaussian_prior_entropy_nats = conditional,
        uniform_index_prior_entropy_nats = index_entropy,
        labeled_joint_prior_entropy_nats = conditional + index_entropy,
        parameter_prior_sd = config.prior_sd,
        maximum_evidence_samples = config.maximum_samples,
        observation_sd = config.observation_sd,
    ) for model in MODEL_NAMES)
    counts = [entry.continuous_parameter_count for entry in values(per_model)]
    entropies = [entry.labeled_joint_prior_entropy_nats for entry in values(per_model)]
    return (
        per_model = per_model,
        parameter_counts_equal = length(unique(counts)) == 1,
        prior_entropies_equal = maximum(entropies) - minimum(entropies) < 1.0e-12,
        evidence_budgets_equal = true,
        audit_valid = length(unique(counts)) == 1 &&
            maximum(entropies) - minimum(entropies) < 1.0e-12,
    )
end

function organization_vector(affect, policy, coupling_self_world,
        coupling_policy_outcome)
    # These are free sufficient coordinates for organization, never carrier.
    return [affect, coupling_self_world, policy, coupling_policy_outcome]
end

function materialize_organization(coordinates)
    affect, self_world, policy, policy_outcome = coordinates
    bundle = (
        affect,
        tanh(affect + self_world),
        policy,
        tanh(policy + policy_outcome),
    )
    couplings = (self_world, policy_outcome)
    precisions = (1.20, 1.00, 1.10, 0.90)
    field_profile = tuple(log.(precisions)...)
    return PartOrganization(bundle, couplings, precisions, field_profile)
end

function carrier_coordinates(organization)
    return [organization[AFFECT_POLICY[1]], organization[AFFECT_POLICY[2]]]
end

function coupling_coordinates(organization)
    return [organization[BIOGRAPHICAL_COUPLINGS[1]],
        organization[BIOGRAPHICAL_COUPLINGS[2]]]
end

function generate_world(seed::Int, condition::Symbol;
        config::FormationTriadConfig = FormationTriadConfig())
    condition in CONDITIONS || throw(ArgumentError("unknown condition: $condition"))
    rng = MersenneTwister(seed + 100_003findfirst(==(condition), CONDITIONS))
    carriers = default_carriers()
    carrier_id = mod1(seed, config.carrier_count)
    base = carrier_vector(carriers[carrier_id])
    affect_policy = if condition == :arbitrary
        config.arbitrary_scale .* randn(rng, 2)
    else
        base .+ config.prepared_jitter_sd .* randn(rng, 2)
    end
    coupling = config.coupling_scale .* randn(rng, 2)
    first_target = organization_vector(affect_policy[1], affect_policy[2],
        coupling[1], coupling[2])

    direction = isodd(seed) ? 1.0 : -1.0
    offset = direction .* config.second_formation_offset .* [1.0, -0.85]
    second_affect_policy = condition == :arbitrary ?
        config.arbitrary_scale .* randn(rng, 2) : affect_policy .+ offset
    second_coupling = config.coupling_scale .* randn(rng, 2)
    second_target = organization_vector(second_affect_policy[1],
        second_affect_policy[2], second_coupling[1], second_coupling[2])

    first_observations = [first_target[channel] +
        config.observation_sd * randn(rng)
        for sample in 1:config.maximum_samples, channel in 1:4]
    second_observations = [second_target[channel] +
        config.observation_sd * randn(rng)
        for sample in 1:config.maximum_samples, channel in 1:4]
    return (
        seed = seed,
        condition = condition,
        generating_carrier_id = condition == :arbitrary ? 0 : carrier_id,
        first_target = first_target,
        second_target = second_target,
        first_organization = materialize_organization(first_target),
        second_organization = materialize_organization(second_target),
        first_observations = first_observations,
        second_observations = second_observations,
    )
end

rmse(first, second) = sqrt(mean((first .- second).^2))

function select_carrier(observations, carriers, config)
    evidence = vec(mean(observations[1:config.selection_samples,
        collect(AFFECT_POLICY)]; dims = 1))
    distances = [sum((evidence .- carrier_vector(carrier)).^2)
        for carrier in carriers]
    return argmin(distances)
end

function posterior_mean(observations, prior_mean, samples, config)
    prior_precision = 1 / config.prior_sd^2
    observation_precision = 1 / config.observation_sd^2
    information = prior_precision .* prior_mean .+
        observation_precision .* vec(sum(observations[1:samples, :]; dims = 1))
    return information ./ (prior_precision + samples * observation_precision)
end

function prior_for_model(model::Symbol, selected_carrier, carriers)
    model == :assembly && return zeros(4)
    carrier = carriers[selected_carrier]
    return organization_vector(carrier.affect_prior, carrier.policy_prior,
        0.0, 0.0)
end

function fit_formation(model::Symbol, observations, target, carriers, config;
        forced_carrier = nothing)
    selected = isnothing(forced_carrier) ?
        select_carrier(observations, carriers, config) : Int(forced_carrier)
    selected in eachindex(carriers) ||
        throw(ArgumentError("forced carrier is outside the repertoire"))
    prior_mean = prior_for_model(model, selected, carriers)
    first_eligible = model == :assembly ? 1 : config.selection_samples
    stable = 0
    samples_to_formation = config.maximum_samples
    estimate = posterior_mean(observations, prior_mean,
        config.maximum_samples, config)
    for samples in first_eligible:config.maximum_samples
        candidate = posterior_mean(observations, prior_mean, samples, config)
        if rmse(candidate, target) <= config.formation_rmse_threshold
            stable += 1
            if stable >= config.stable_samples
                samples_to_formation = samples
                estimate = candidate
                break
            end
        else
            stable = 0
        end
    end
    return (
        estimate = estimate,
        consolidated_estimate = posterior_mean(observations, prior_mean,
            config.maximum_samples, config),
        selected_carrier = selected,
        samples = samples_to_formation,
        formed = samples_to_formation < config.maximum_samples,
        final_rmse = rmse(estimate, target),
    )
end

function carrier_target_distance(carriers, carrier_id, target)
    return norm(carrier_vector(carriers[carrier_id]) .-
        carrier_coordinates(target))
end

function run_exploratory_diagnostics(seeds;
        config::FormationTriadConfig = FormationTriadConfig())
    rows = NamedTuple[]
    for seed in seeds
        world = generate_world(seed, :shuffled; config = config)
        carriers = shuffled_carriers(default_carriers())
        degraded = degraded_marginal_carriers(carriers)
        assembly = fit_formation(:assembly, world.first_observations,
            world.first_target, carriers, config)
        selected = fit_formation(:recruitment, world.first_observations,
            world.first_target, carriers, config)
        fixed_rng = MersenneTwister(seed + 9_000_001)
        fixed_id = rand(fixed_rng, eachindex(carriers))
        fixed = fit_formation(:recruitment, world.first_observations,
            world.first_target, carriers, config;
            forced_carrier = fixed_id)
        degraded_selected = fit_formation(:recruitment,
            world.first_observations, world.first_target, degraded, config)
        push!(rows, (
            stage = "exploratory_post_freeze",
            seed = seed,
            assembly_samples = assembly.samples,
            shuffled_selected_samples = selected.samples,
            shuffled_fixed_random_samples = fixed.samples,
            degraded_marginals_selected_samples = degraded_selected.samples,
            shuffled_selected_carrier = selected.selected_carrier,
            shuffled_fixed_random_carrier = fixed.selected_carrier,
            degraded_selected_carrier = degraded_selected.selected_carrier,
            shuffled_selected_target_distance = carrier_target_distance(
                carriers, selected.selected_carrier, world.first_target),
            shuffled_fixed_target_distance = carrier_target_distance(
                carriers, fixed.selected_carrier, world.first_target),
            degraded_selected_target_distance = carrier_target_distance(
                degraded, degraded_selected.selected_carrier,
                world.first_target),
            selected_formed = selected.formed,
            fixed_random_formed = fixed.formed,
            degraded_marginals_formed = degraded_selected.formed,
        ))
    end
    return rows
end

function summarize_exploratory_diagnostics(rows)
    assembly = mean(row.assembly_samples for row in rows)
    selected = mean(row.shuffled_selected_samples for row in rows)
    fixed = mean(row.shuffled_fixed_random_samples for row in rows)
    degraded = mean(row.degraded_marginals_selected_samples for row in rows)
    advantage(samples) = (assembly - samples) / assembly
    observed_savings = assembly - selected
    selection_contribution = fixed - selected
    coverage_contribution = degraded - selected
    return (
        world_count = length(rows),
        mean_samples = (
            assembly = assembly,
            shuffled_best_fitting = selected,
            shuffled_fixed_random = fixed,
            degraded_marginals_best_fitting = degraded,
        ),
        recruitment_advantage_vs_assembly = (
            shuffled_best_fitting = advantage(selected),
            shuffled_fixed_random = advantage(fixed),
            degraded_marginals_best_fitting = advantage(degraded),
        ),
        attribution = (
            observed_best_fit_samples_saved = observed_savings,
            samples_attributable_to_selection_vs_fixed_random =
                selection_contribution,
            selection_share_of_observed_savings = observed_savings == 0 ?
                nothing : selection_contribution / observed_savings,
            selection_removal_reverses_advantage =
                advantage(fixed) < 0,
            samples_attributable_to_marginal_coverage_vs_degraded =
                coverage_contribution,
            selection_and_coverage_explain_control_failure =
                advantage(selected) > 0.05 &&
                advantage(fixed) <= 0.05 &&
                advantage(degraded) <= 0.05,
        ),
        carrier_target_distance = (
            shuffled_best_fitting = mean(
                row.shuffled_selected_target_distance for row in rows),
            shuffled_fixed_random = mean(
                row.shuffled_fixed_target_distance for row in rows),
            degraded_marginals_best_fitting = mean(
                row.degraded_selected_target_distance for row in rows),
        ),
        all_formed = (
            shuffled_best_fitting = all(row.selected_formed for row in rows),
            shuffled_fixed_random = all(
                row.fixed_random_formed for row in rows),
            degraded_marginals_best_fitting = all(
                row.degraded_marginals_formed for row in rows),
        ),
    )
end

function shared_carrier_shift(model, first_fit, second_fit, world, config)
    model == :assembly && return zeros(2)
    first_coordinates = carrier_coordinates(world.first_target)
    second_coordinates = carrier_coordinates(world.second_target)
    update_rate = model == :recruitment ?
        config.recruitment_carrier_update : config.hybrid_carrier_update
    return update_rate .* (second_coordinates .- first_coordinates)
end

function interference_measure(model, first_fit, second_fit, world, config)
    baseline = rmse(first_fit.estimate, world.first_target)
    after = copy(first_fit.estimate)
    if model != :assembly &&
            first_fit.selected_carrier == second_fit.selected_carrier
        after[collect(AFFECT_POLICY)] .+=
            shared_carrier_shift(model, first_fit, second_fit, world, config)
    end
    return (
        baseline_rmse = baseline,
        after_rmse = rmse(after, world.first_target),
        degradation = rmse(after, world.first_target) - baseline,
        shared_carrier = first_fit.selected_carrier ==
            second_fit.selected_carrier,
    )
end

function selective_reduction(model, fit, carriers, config)
    carrier = carriers[fit.selected_carrier]
    carrier_component = zeros(4)
    coupling_component = zeros(4)
    if model == :recruitment || model == :hybrid
        carrier_component[collect(AFFECT_POLICY)] .= carrier_vector(carrier)
    end
    if model == :assembly
        coupling_component[collect(BIOGRAPHICAL_COUPLINGS)] .=
            config.assembly_coupling_retention .*
            fit.consolidated_estimate[collect(BIOGRAPHICAL_COUPLINGS)]
    elseif model == :hybrid
        coupling_component[collect(BIOGRAPHICAL_COUPLINGS)] .=
            config.hybrid_coupling_retention .*
            fit.consolidated_estimate[collect(BIOGRAPHICAL_COUPLINGS)]
    end
    residue = carrier_component + coupling_component
    carrier_norm = norm(carrier_component)
    coupling_norm = norm(coupling_component)
    carrier_ablation_loss = norm(residue - coupling_component)
    coupling_ablation_loss = norm(residue - carrier_component)
    return (
        carrier_component = carrier_component,
        coupling_component = coupling_component,
        residue = residue,
        carrier_norm = carrier_norm,
        coupling_norm = coupling_norm,
        carrier_ablation_loss = carrier_ablation_loss,
        coupling_ablation_loss = coupling_ablation_loss,
        carrier_present = carrier_norm >= config.residue_norm_threshold &&
            carrier_ablation_loss >= config.residue_ablation_threshold,
        coupling_present = coupling_norm >= config.residue_norm_threshold &&
            coupling_ablation_loss >= config.residue_ablation_threshold,
    )
end

function cluster_margin(estimate, carriers)
    point = carrier_coordinates(estimate)
    distances = sort([norm(point .- carrier_vector(carrier))
        for carrier in carriers])
    return distances[2] - distances[1]
end

function run_world(seed::Int, condition::Symbol;
        stage::Symbol = :pilot,
        config::FormationTriadConfig = FormationTriadConfig())
    world = generate_world(seed, condition; config = config)
    prepared = default_carriers()
    model_carriers = condition == :shuffled ?
        shuffled_carriers(prepared) : prepared
    rows = NamedTuple[]
    for model in MODEL_NAMES
        first_fit = fit_formation(model, world.first_observations,
            world.first_target, model_carriers, config)
        # Force the stated shared-carrier probe by binding the second formation
        # through the first formation's selected carrier for persistent models.
        second_fit_raw = fit_formation(model, world.second_observations,
            world.second_target, model_carriers, config)
        second_fit = model == :assembly ? second_fit_raw :
            merge(second_fit_raw,
                (selected_carrier = first_fit.selected_carrier,))
        interference = interference_measure(model, first_fit, second_fit,
            world, config)
        residue = selective_reduction(model, first_fit, model_carriers, config)
        target_cluster = world.generating_carrier_id
        push!(rows, (
            stage = String(stage),
            seed = seed,
            condition = String(condition),
            model = String(model),
            generating_carrier_id = target_cluster,
            selected_carrier_id = first_fit.selected_carrier,
            samples_to_formation = first_fit.samples,
            formed = first_fit.formed,
            formation_rmse = first_fit.final_rmse,
            interference_shared_carrier = interference.shared_carrier,
            interference_baseline_rmse = interference.baseline_rmse,
            interference_after_rmse = interference.after_rmse,
            interference_degradation = interference.degradation,
            cluster_margin = cluster_margin(first_fit.estimate, model_carriers),
            estimate_affect = first_fit.estimate[1],
            estimate_self_world_coupling = first_fit.estimate[2],
            estimate_policy = first_fit.estimate[3],
            estimate_policy_outcome_coupling = first_fit.estimate[4],
            carrier_residue_norm = residue.carrier_norm,
            coupling_residue_norm = residue.coupling_norm,
            carrier_ablation_loss = residue.carrier_ablation_loss,
            coupling_ablation_loss = residue.coupling_ablation_loss,
            carrier_residue_present = residue.carrier_present,
            coupling_residue_present = residue.coupling_present,
        ))
    end
    return rows
end

function run_block(seeds; stage::Symbol,
        config::FormationTriadConfig = FormationTriadConfig())
    rows = NamedTuple[]
    for seed in seeds, condition in CONDITIONS
        append!(rows, run_world(seed, condition; stage = stage, config = config))
    end
    return rows
end

subset(rows; model = nothing, condition = nothing) = [
    row for row in rows
    if (isnothing(model) || row.model == String(model)) &&
        (isnothing(condition) || row.condition == String(condition))]

mean_field(rows, field) = mean(Float64(getproperty(row, field)) for row in rows)
count_field(rows, field) = count(row -> Bool(getproperty(row, field)), rows)

function efficiency_advantage(rows, condition)
    assembly = mean_field(subset(rows; model = :assembly,
        condition = condition), :samples_to_formation)
    recruitment = mean_field(subset(rows; model = :recruitment,
        condition = condition), :samples_to_formation)
    return (assembly - recruitment) / assembly
end

function kmeans_affect_policy(rows; clusters = 4, iterations = 40)
    points = [[row.estimate_affect, row.estimate_policy] for row in rows]
    length(points) >= clusters || return (
        silhouette = 0.0, cluster_sizes = Int[], centers = Vector{Float64}[])
    order = sortperm(points; by = point -> (point[1], point[2]))
    indices = round.(Int, range(1, length(points); length = clusters))
    centers = [copy(points[order[index]]) for index in indices]
    assignments = ones(Int, length(points))
    for _ in 1:iterations
        next_assignments = [argmin([sum((point .- center).^2)
            for center in centers]) for point in points]
        next_centers = [begin
            members = [points[index] for index in eachindex(points)
                if next_assignments[index] == cluster]
            isempty(members) ? copy(centers[cluster]) :
                vec(mean(reduce(hcat, members); dims = 2))
        end for cluster in 1:clusters]
        assignments == next_assignments && (centers = next_centers; break)
        assignments = next_assignments
        centers = next_centers
    end
    silhouettes = Float64[]
    for index in eachindex(points)
        own = assignments[index]
        own_members = [other for other in eachindex(points)
            if assignments[other] == own && other != index]
        a = isempty(own_members) ? 0.0 :
            mean(norm(points[index] .- points[other]) for other in own_members)
        other_means = [mean(norm(points[index] .- points[other])
            for other in eachindex(points) if assignments[other] == cluster)
            for cluster in 1:clusters if cluster != own &&
                any(==(cluster), assignments)]
        b = isempty(other_means) ? 0.0 : minimum(other_means)
        push!(silhouettes, max(a, b) == 0 ? 0.0 : (b - a) / max(a, b))
    end
    return (
        silhouette = mean(silhouettes),
        cluster_sizes = [count(==(cluster), assignments)
            for cluster in 1:clusters],
        centers = centers,
    )
end

function summarize_block(rows,
        config::FormationTriadConfig = FormationTriadConfig())
    prepared_advantage = efficiency_advantage(rows, :prepared)
    arbitrary_advantage = efficiency_advantage(rows, :arbitrary)
    shuffled_advantage = efficiency_advantage(rows, :shuffled)
    recruitment_interference = subset(rows; model = :recruitment,
        condition = :prepared)
    hybrid_interference = subset(rows; model = :hybrid,
        condition = :prepared)
    assembly_interference = subset(rows; model = :assembly,
        condition = :prepared)
    residue_counts = Dict(String(model) => begin
        model_rows = subset(rows; model = model, condition = :prepared)
        (
            both = count(row -> row.carrier_residue_present &&
                row.coupling_residue_present, model_rows),
            carrier_only = count(row -> row.carrier_residue_present &&
                !row.coupling_residue_present, model_rows),
            coupling_only = count(row -> !row.carrier_residue_present &&
                row.coupling_residue_present, model_rows),
            neither = count(row -> !row.carrier_residue_present &&
                !row.coupling_residue_present, model_rows),
        )
    end for model in MODEL_NAMES)
    cluster_structure = Dict(String(model) => Dict(String(condition) =>
        kmeans_affect_policy(subset(rows; model = model,
            condition = condition))
        for condition in CONDITIONS) for model in MODEL_NAMES)
    efficiency_pass = prepared_advantage >=
        config.efficiency_advantage_required &&
        arbitrary_advantage <= config.efficiency_vanish_threshold &&
        shuffled_advantage <= config.efficiency_vanish_threshold
    recruitment_interference_count = count(row ->
        row.interference_degradation >= config.interference_margin,
        recruitment_interference)
    hybrid_interference_count = count(row ->
        row.interference_degradation >= config.interference_margin,
        hybrid_interference)
    assembly_interference_count = count(row ->
        row.interference_degradation >= config.interference_margin,
        assembly_interference)
    interference_pass = recruitment_interference_count >=
        config.world_count_required &&
        hybrid_interference_count >= config.world_count_required &&
        assembly_interference_count == 0
    hybrid_both = residue_counts["hybrid"].both
    pure_both = residue_counts["assembly"].both +
        residue_counts["recruitment"].both
    residue_pass = hybrid_both >= config.world_count_required &&
        pure_both == 0
    return (
        world_count = length(unique(row.seed for row in rows)),
        formation_efficiency = (
            prepared_recruitment_advantage = prepared_advantage,
            arbitrary_recruitment_advantage = arbitrary_advantage,
            shuffled_recruitment_advantage = shuffled_advantage,
            mean_samples = Dict(String(model) => Dict(String(condition) =>
                mean_field(subset(rows; model = model,
                    condition = condition), :samples_to_formation)
                for condition in CONDITIONS) for model in MODEL_NAMES),
        ),
        interference = (
            mean_degradation = Dict(
                "assembly" => mean_field(assembly_interference,
                    :interference_degradation),
                "recruitment" => mean_field(recruitment_interference,
                    :interference_degradation),
                "hybrid" => mean_field(hybrid_interference,
                    :interference_degradation),
            ),
            worlds_at_or_above_margin = Dict(
                "assembly" => assembly_interference_count,
                "recruitment" => recruitment_interference_count,
                "hybrid" => hybrid_interference_count,
            ),
        ),
        cluster_structure = cluster_structure,
        residue = residue_counts,
        criteria = (
            criterion_1_efficiency_and_shuffle = efficiency_pass,
            criterion_2_interference = interference_pass,
            criterion_3_residue_dissociation = residue_pass,
            all = efficiency_pass && interference_pass && residue_pass,
        ),
    )
end

function self_check(config::FormationTriadConfig = FormationTriadConfig())
    audit = capacity_audit(config)
    @assert audit.audit_valid
    @assert isempty(intersect(config.pilot_seeds, config.confirmation_seeds))
    @assert ORGANIZATION_CHANNELS == (:self, :world, :policy, :outcome)
    rows = run_block(first(config.pilot_seeds, 2); stage = :smoke,
        config = config)
    @assert length(rows) == 2 * length(CONDITIONS) * length(MODEL_NAMES)
    @assert all(row.samples_to_formation <= config.maximum_samples for row in rows)
    @assert all(isfinite(row.interference_degradation) for row in rows)
    diagnostic_seeds = collect(18301:18302)
    diagnostics = run_exploratory_diagnostics(diagnostic_seeds;
        config = config)
    @assert length(diagnostics) == length(diagnostic_seeds)
    @assert summarize_exploratory_diagnostics(diagnostics).world_count == 2
    return true
end

end
