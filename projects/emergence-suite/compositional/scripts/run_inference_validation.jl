#!/usr/bin/env julia

using CompositionalOrganism
using Statistics
using TOML

const CO = CompositionalOrganism
const ROOT = normpath(joinpath(@__DIR__, ".."))
const OUTPUT = joinpath(ROOT, "results", "experiment51", "semantic-gate")
const FAMILIES = (
    :full_bundle, :reduced_bundle, :context_global, :context_cue_local,
    :context_split, :factorized_root, :shared_root,
)
const ENDPOINTS = [
    (:bundle_context, "context-main", "bundle-main"),
    (:cue_root, "cue-main", "bundle-main"),
    (:local_monitor, "bundle-main", "local-one"),
    (:local_to_global_broadcast, "local-one", "global-main"),
    (:global_precision_message, "global-main", "protector-one"),
    (:protector_joint_policy, "protector-one", "access-main"),
    (:protector_cross_prediction, "protector-one", "protector-two"),
    (:partner_regulation, "partner-main", "global-main"),
    (:partner_trust, "partner-main", "protector-one"),
    (:policy_access, "bundle-main", "access-main"),
    (:access_bundle, "access-main", "bundle-main"),
    (:episode_scope, "episode-main", "bundle-main"),
    (:structure_scope, "episode-main", "structure-main"),
    (:registration, "access-main", "bundle-main"),
    (:world_coupling, "context-main", "bundle-main"),
]
const TARGET_FIELDS = Dict(
    :bundle_context => "activation_probability",
    :cue_root => "root_probability",
    :local_monitor => "mean",
    :local_to_global_broadcast => "part",
    :global_precision_message => "forecast_outcome",
    :protector_joint_policy => "probability",
    :protector_cross_prediction => "forecast_coprotection",
    :partner_regulation => "relationship",
    :partner_trust => "forecast_partner_type",
    :policy_access => "probability",
    :access_bundle => "activation_probability",
    :episode_scope => "root_probability",
    :registration => "mandate_probability",
    :world_coupling => "expected_outcome",
)

function rebuild(model; nodes = model.nodes, edges = model.edges,
        channels = model.channels, policies = model.policies,
        candidates = model.candidates, factors = model.factors,
        distributions = model.distributions, emissions = model.emissions,
        genome = copy(model.genome))
    CO.CompiledModel(model.genome_id, model.configuration_id,
        model.initializer_id, model.history_generator_id,
        model.action_reconciler_id, model.world_id, model.family, model.horizon,
        model.episode_length, model.development_horizon, model.seed_namespace,
        model.development_emission_ids, nodes, edges, channels,
        policies, candidates, factors, distributions,
        model.processes, emissions, model.outcomes, model.contingencies,
        genome, model.action_costs, model.consumption)
end

function set_source!(state, model, source)
    node = model.nodes[source]
    state.node_beliefs[source] .= CO.normalize_distribution(vcat(
        fill(0.1 / (node.cardinality - 1), node.cardinality - 1), 0.9))
    values = state.node_values[source]
    node.kind == :ContextNode && (values["transition_entropy"] = 0.1)
    node.kind == :BundleNode && begin
        values["activation_probability"] = 0.9
        values["mandate_probability"] = 0.9
    end
    node.kind == :CueNode && (values["meaning_probability"] = 0.9)
    node.kind == :LocalPrecisionNode && (values["mean"] = 0.9)
    node.kind == :GlobalPrecisionNode && (values["depth"] = 0.9)
    node.kind == :ProtectorNode && begin
        values["permission_probability"] = 0.9
        values["forecast_outcome"] = 0.9
    end
    node.kind == :PartnerNode && begin
        values["trust_probability"] = 0.9
        values["regulation_probability"] = 0.9
    end
    node.kind == :AccessNode && (values["probability"] = 0.9)
    node.kind == :EpisodeNode && (values["joint_probability"] = 0.9)
end

function traced_field(state, model, target, field)
    world = CO.WorldState(Dict{String,String}(), Dict{String,Bool}(),
        Dict{Tuple{String,Int},Float64}(), Dict{String,Int}())
    row = CO.tick_row(UInt64(1), "micro", 0, 0, 0,
        false, "", state, model, world)
    path = only(key for key in keys(row.fields)
        if endswith(key, ".$target.$field"))
    return Float64(row.fields[path])
end

function edge_validation(model)
    rows = NamedTuple[]
    for (kind, source, target) in ENDPOINTS
        edge = CO.EdgeIR("validation-$(kind)", kind, source, target, :active)
        micro = rebuild(model; edges = Dict(edge.id => edge),
            candidates = Dict{String,CO.CandidateIR}())
        state = CO.initialize_state(micro)
        set_source!(state, micro, source)
        unrelated = first(id for id in keys(state.node_values)
            if id ∉ (source, target))
        approximate = CO.belief_propagation(state, micro)
        exact = CO.exact_graph_marginals(state, micro)

        deleted = rebuild(micro; edges = Dict{String,CO.EdgeIR}())
        deleted_state = CO.initialize_state(deleted)
        set_source!(deleted_state, deleted, source)
        deleted_result = CO.belief_propagation(deleted_state, deleted)

        reversed_edge =
            CO.EdgeIR("reversed-$(kind)", kind, target, source, :active)
        reversed = rebuild(model; edges = Dict(reversed_edge.id => reversed_edge),
            candidates = Dict{String,CO.CandidateIR}())
        reversed_state = CO.initialize_state(reversed)
        set_source!(reversed_state, reversed, source)
        reversed_result = CO.belief_propagation(reversed_state, reversed)
        implementation_mutant = CO.belief_propagation(
            state, micro; muted_kind = kind)

        named_trace_delta = 0.0
        named_mutant_delta = 0.0
        if kind != :structure_scope
            observation = CO.Observation("edge-validation", 0, :world,
                "cue-signal", nothing, [source, target], Set{String}(),
                :categorical, "positive", 0.9, Dict{String,Float64}(),
                0.0, 0.0, false, "edge-validation")
            named, muted, removed =
                deepcopy(state), deepcopy(state), deepcopy(deleted_state)
            CO.apply_directed_semantics!(named, micro, observation)
            CO.apply_directed_semantics!(
                muted, micro, observation; muted_kind = kind)
            CO.apply_directed_semantics!(removed, deleted, observation)
            field = TARGET_FIELDS[kind]
            named_trace_delta = traced_field(named, micro, target, field) -
                traced_field(removed, deleted, target, field)
            named_mutant_delta = traced_field(named, micro, target, field) -
                traced_field(muted, micro, target, field)
        else
            structure_state = CO.initialize_state(model)
            structure_state.node_beliefs[source] .= state.node_beliefs[source]
            observation = CO.Observation("structure-validation", 0, :world,
                "episode-signal", nothing,
                ["episode-main", "bundle-main", "context-main"],
                Set{String}(), :categorical, "safe", 0.9,
                Dict{String,Float64}(), 0.0, 0.0, false,
                "structure-validation")
            present = CO.candidate_scores(
                structure_state, model, observation)
            no_scope_edges = Dict(id => value
                for (id, value) in model.edges
                if value.kind != :structure_scope)
            no_scope = rebuild(model; edges = no_scope_edges)
            absent = CO.candidate_scores(
                CO.initialize_state(no_scope), no_scope, observation)
            named_trace_delta = maximum(abs(present[id] - absent[id])
                for id in keys(present))
            named_mutant_delta = named_trace_delta
        end
        push!(rows, (
            edge_kind = String(kind),
            parity_error = maximum(abs(approximate[id] - exact[id])
                for id in keys(exact)),
            target_delta = exact[target] - deleted_result[target],
            reverse_target_delta =
                reversed_result[target] - deleted_result[target],
            implementation_mutant_delta =
                exact[target] - implementation_mutant[target],
            unrelated_delta = exact[unrelated] - deleted_result[unrelated],
            named_trace_delta = named_trace_delta,
            named_mutant_delta = named_mutant_delta,
        ))
    end
    return rows
end

function recovery_candidates(model)
    edge_ids = Set(keys(model.edges))
    common = Set(["structure-episode"])
    patterns = [
        union(common, Set(["bundle-context", "episode-bundle"])),
        union(common, Set(["bundle-context"])),
        union(common, Set(["partner-regulation", "local-broadcast"])),
        union(common, Set(["cue-root", "local-monitor"])),
        union(common, Set(["bundle-context", "partner-regulation",
            "local-monitor"])),
        union(common, Set(["episode-bundle"])),
        union(common, Set(["cue-root", "episode-bundle", "access-bundle"])),
    ]
    candidates = Dict{String,CO.CandidateIR}()
    for (ordinal, (family, active)) in enumerate(zip(FAMILIES, patterns))
        id = "recovery-$(replace(String(family), '_' => '-'))"
        candidates[id] = CO.CandidateIR(id, "structure-main", family,
            active, setdiff(edge_ids, active), ordinal)
    end
    return candidates
end

function model_recovery(model)
    candidates = recovery_candidates(model)
    channels = Dict{String,CO.ChannelIR}()
    emissions = copy(model.emissions)
    for edge in values(model.edges)
        edge.kind == :structure_scope && continue
        id = "recovery-channel-$(edge.id)"
        channels[id] = CO.ChannelIR(id, :world,
            unique(["episode-main", edge.source, edge.target]),
            :categorical, ["observed-a", "observed-b"], nothing, true)
        emission_id = "$id-emission"
        emissions[emission_id] = CO.EmissionIR(
            emission_id, ["recovery-factor"], id, :categorical,
            ["recovery-a-emission", "recovery-b-emission"],
            Float64[], nothing, "reliable-signal", Set{String}())
    end
    factors = copy(model.factors)
    factors["recovery-factor"] =
        CO.FactorIR("recovery-factor", ["latent-a", "latent-b"],
            "recovery-prior")
    distributions = copy(model.distributions)
    distributions["recovery-prior"] = CO.CategoricalDistributionIR(
        "recovery-prior", ["latent-a", "latent-b"], [0.5, 0.5])
    distributions["recovery-a-emission"] = CO.CategoricalDistributionIR(
        "recovery-a-emission", ["observed-a", "observed-b"], [0.9, 0.1])
    distributions["recovery-b-emission"] = CO.CategoricalDistributionIR(
        "recovery-b-emission", ["observed-a", "observed-b"], [0.1, 0.9])
    recovery_model = rebuild(model; channels = channels,
        candidates = candidates, factors = factors,
        distributions = distributions, emissions = emissions)
    state = CO.initialize_state(recovery_model)
    for (ordinal, id) in enumerate(sort!(collect(keys(state.node_beliefs))))
        cardinality = length(state.node_beliefs[id])
        selected = mod(3ordinal + sum(codeunits(id)), cardinality) + 1
        state.node_beliefs[id] .= fill(0.02 / (cardinality - 1), cardinality)
        state.node_beliefs[id][selected] = 0.98
    end

    scoring = Dict{String,Dict{String,Dict{String,Float64}}}()
    generating = Dict{String,Dict{String,Vector{Float64}}}()
    for (id, candidate) in candidates
        scoring[id] = Dict{String,Dict{String,Float64}}()
        generating[id] = Dict{String,Vector{Float64}}()
        truth_beliefs = CO.exact_graph_beliefs(state, recovery_model;
            edge_enabled = CO.candidate_edge_map(recovery_model, candidate))
        for (channel_id, channel) in channels
            emission_id = "$channel_id-emission"
            observation_a = CO.Observation("recovery", 0, :world, channel_id,
                emission_id, unique(vcat(["recovery-factor"], channel.scope)),
                Set{String}(), :categorical, "observed-a", 1.0,
                Dict{String,Float64}(), 0.0, 0.0, false,
                "independent-model-recovery")
            scoring[id][channel_id] =
                CO.categorical_candidate_probabilities(
                    state, recovery_model, observation_a, candidate)
            projected = [
                CO.project_distribution(truth_beliefs[node_id], 2)
                for node_id in channel.scope
                if haskey(truth_beliefs, node_id)]
            generating[id][channel_id] =
                CO.normalize_distribution(reduce(.*, projected))
        end
    end

    counts = Dict((truth, predicted) => 0
        for truth in keys(candidates) for predicted in keys(candidates))
    channel_ids = sort!(collect(keys(channels)))
    for truth in sort!(collect(keys(candidates))), replicate in 0:23
        evidence = Dict(id => 0.0 for id in keys(candidates))
        for event in 0:65535
            channel_id = channel_ids[event % length(channel_ids) + 1]
            latent = CO.inverse_categorical(
                ["latent-a", "latent-b"], generating[truth][channel_id],
                CO.counter_uniform(UInt64(90_000 + replicate),
                    :latent_factor, "$truth/$channel_id", event, 0))
            emission = recovery_model.emissions["$channel_id-emission"]
            labels, probabilities = CO.emission_probabilities(
                recovery_model, emission,
                Dict("recovery-factor" => latent), 1.0)
            label = CO.inverse_categorical(labels, probabilities,
                CO.counter_uniform(UInt64(90_000 + replicate), :emission,
                    "$truth/$channel_id", event, 0))
            for id in keys(candidates)
                evidence[id] += log(scoring[id][channel_id][label])
            end
        end
        predicted = first(sort!(collect(keys(evidence));
            by = id -> (-evidence[id], candidates[id].ordinal)))
        counts[(truth, predicted)] += 1
    end
    return candidates, scoring, counts
end

function sbc_ranks(model)
    emission = model.emissions["partner-emission"]
    factor = model.factors["partner-state"]
    rank_counts = zeros(Int, 21)
    for replicate in 0:419
        seed = UInt64(200_000 + replicate)
        truth = CO.inverse_categorical(factor.values,
            fill(1 / length(factor.values), length(factor.values)),
            CO.counter_uniform(seed, :latent_factor, factor.id, 0, 0))
        truth_index = findfirst(==(truth), factor.values)
        reliability = 0.8
        configuration = Dict(factor.id => truth)
        labels, probabilities =
            CO.emission_probabilities(model, emission, configuration, reliability)
        value = CO.inverse_categorical(labels, probabilities,
            CO.counter_uniform(seed, :emission, emission.id, 1, 0))
        likelihoods =
            CO.observation_likelihoods(model, emission, value, reliability)
        state = CO.initialize_state(model)
        observation = CO.Observation("sbc", 0, :partner,
            emission.channel_id, emission.id, copy(emission.source_factors),
            Set{String}(), :categorical, value, reliability, likelihoods,
            0.0, 0.0, false, "sbc")
        CO.infer_factors!(state, model, observation)
        posterior = state.factor_beliefs[factor.id]
        truth_tie =
            CO.counter_uniform(seed, :distribution, "sbc-truth-tie", 2, 0)
        rank = 0
        for draw in 0:19
            sampled = CO.inverse_categorical(factor.values, posterior,
                CO.counter_uniform(seed, :distribution,
                    "sbc-posterior", 2, draw))
            sampled_index = findfirst(==(sampled), factor.values)
            rank += sampled_index < truth_index ||
                (sampled_index == truth_index &&
                    CO.counter_uniform(seed, :distribution,
                        "sbc-sample-tie", 2, draw) < truth_tie)
        end
        rank_counts[rank + 1] += 1
    end
    expected = sum(rank_counts) / length(rank_counts)
    return rank_counts,
        sum((count - expected)^2 / expected for count in rank_counts)
end

function partner_recovery(model)
    emission = model.emissions["partner-emission"]
    factor = model.factors["partner-state"]
    confusion = Dict((truth, predicted) => 0
        for truth in factor.values for predicted in factor.values)
    for truth in factor.values, replicate in 0:31
        state = CO.initialize_state(model)
        for event in 0:23
            labels, probabilities = CO.emission_probabilities(
                model, emission, Dict(factor.id => truth), 0.9)
            value = CO.inverse_categorical(labels, probabilities,
                CO.counter_uniform(UInt64(300_000 + replicate),
                    :emission, truth, event, 0))
            observation = CO.Observation("partner-recovery", event, :partner,
                emission.channel_id, emission.id,
                copy(emission.source_factors), Set{String}(), :categorical,
                value, 0.9,
                CO.observation_likelihoods(model, emission, value, 0.9),
                0.0, 0.0, false, "generated-partner-recovery")
            CO.infer_factors!(state, model, observation)
        end
        predicted = factor.values[argmax(state.factor_beliefs[factor.id])]
        confusion[(truth, predicted)] += 1
    end
    accuracy = sum(count for ((truth, predicted), count) in confusion
        if truth == predicted) / sum(values(confusion))
    return confusion, accuracy
end

function cue_root_recovery(model, protocol)
    episode_emission = model.emissions["episode-emission"]
    cue_emission = model.emissions["cue-emission"]
    aligned = CO.initialize_state(model)
    reversed = CO.initialize_state(model)
    # Mixed and repair form a declared monotone cue/root contrast.  The
    # reversed history swaps only the cue-generating truth; both histories
    # first infer the root from an independently generated episode signal.
    truth_pair = ("mixed", "repair")
    reversed_truth = Dict("mixed" => "repair", "repair" => "mixed")
    for event in 0:191
        truth = truth_pair[event % length(truth_pair) + 1]
        for (state, cue_truth, namespace) in (
                (aligned, truth, "aligned"),
                (reversed, reversed_truth[truth], "reversed"))
            seed = UInt64(400_000 + event)
            episode_world = CO.WorldState(
                Dict("episode-state" => truth),
                Dict{String,Bool}(), Dict{Tuple{String,Int},Float64}(),
                Dict{String,Int}())
            cue_world = CO.WorldState(
                Dict("episode-state" => cue_truth),
                Dict{String,Bool}(), Dict{Tuple{String,Int},Float64}(),
                Dict{String,Int}())
            CO.predict_factors!(state, model)
            episode_observation = CO.account_observation(
                CO.generate_observation(model, episode_world, protocol,
                    "broadcast-on", seed, "cue-root-$namespace-episode",
                    event + 1, episode_emission.id, event, 2event),
                state, model)
            CO.infer!(state, model, episode_observation)
            CO.learn!(state, model, episode_observation)
            cue_observation = CO.account_observation(
                CO.generate_observation(model, cue_world, protocol,
                    "broadcast-on", seed, "cue-root-$namespace-cue",
                    event + 1, cue_emission.id, event, 2event + 1),
                state, model)
            CO.infer!(state, model, cue_observation)
            CO.learn!(state, model, cue_observation)
        end
    end
    return aligned.edge_strength["cue-root"],
        reversed.edge_strength["cue-root"]
end

function outcome_recovery(model, protocol)
    low, high = CO.initialize_state(model), CO.initialize_state(model)
    for action in ("approach", "observe")
        for state in (low, high)
            for candidate_action in keys(state.action_enabled)
                state.action_enabled[candidate_action] =
                    candidate_action == action
            end
        end
        for seed_value in 500_000:502_047
            world = CO.initialize_world(
                model, protocol, "broadcast-on", UInt64(seed_value))
            target = world.truth["exposure-state"] == "high" ? high : low
            CO.infer_policy!(target, model)
            CO.generate_outcomes!(target, world, model, protocol,
                "broadcast-on", UInt64(seed_value), 1)
            CO.learn_outcomes!(target, model)
        end
    end
    for state in (low, high), action in keys(state.action_enabled)
        state.action_enabled[action] = true
    end
    actors = sort!([id for (id, node) in model.nodes
        if node.active && node.kind == :ProtectorNode])
    label = join(("$actor=approach" for actor in actors), ";")
    outcome_delta = CO.learned_probability(high.joint_policy_counts[label]) -
        CO.learned_probability(low.joint_policy_counts[label])
    access_delta = CO.learned_probability(high.joint_access_counts[label]) -
        CO.learned_probability(low.joint_access_counts[label])

    cross_edge = only(edge for edge in values(model.edges)
        if edge.kind == :protector_cross_prediction &&
            edge.source == "protector-one" && edge.target == "protector-two")
    action_by_actor = Dict(actor => "approach" for actor in actors)
    action_by_actor[cross_edge.source] = "observe"
    with_edge = CO.actor_forecast(low, model,
        cross_edge.target, "approach", action_by_actor)
    no_cross = rebuild(model; edges = Dict(id => edge
        for (id, edge) in model.edges
        if edge.kind != :protector_cross_prediction))
    without_edge = CO.actor_forecast(low, no_cross,
        cross_edge.target, "approach", action_by_actor)
    return outcome_delta, access_delta, with_edge - without_edge
end

function precision_recovery(model, protocol)
    rows = Tuple{Float64,Float64}[]
    for seed_value in 600_000:600_255
        state = CO.initialize_state(model)
        world =
            CO.initialize_world(model, protocol, "broadcast-on", UInt64(seed_value))
        observation = CO.account_observation(CO.generate_observation(
            model, world, protocol, "broadcast-on", UInt64(seed_value),
            "precision-recovery", 1, "cue-emission", 0, 0), state, model)
        CO.infer!(state, model, observation)
        push!(rows, (observation.reliability,
            state.node_values["local-one"]["mean"]))
    end
    sorted = sort(rows; by = first)
    low = mean(last.(first(sorted, 64)))
    high = mean(last.(last(sorted, 64)))
    return high - low
end

function parameter_recovery(model, protocol)
    confusion, accuracy = partner_recovery(model)
    cue_aligned, cue_reversed = cue_root_recovery(model, protocol)
    outcome_delta, access_delta, coprotection_delta =
        outcome_recovery(model, protocol)
    metrics = Dict{String,Float64}(
        "cue_root_aligned_strength" => cue_aligned,
        "cue_root_reversed_strength" => cue_reversed,
        "policy_outcome_recovery_delta" => outcome_delta,
        "access_recovery_delta" => access_delta,
        "coprotection_edge_forecast_delta" => coprotection_delta,
        "precision_forecast_delta" => precision_recovery(model, protocol),
    )
    return confusion, accuracy, metrics
end

mkpath(OUTPUT)
documents = CO.load_documents(joinpath(
    ROOT, "protocols", "public-dummies", "51-P-00"))
model = CO.compile_model(
    documents, CO.load_genome(joinpath(ROOT, "genome.toml")))
protocol = CO.compile_protocol(documents.protocol)

edge_rows = edge_validation(model)
candidates, _, recovery_counts = model_recovery(model)
rank_counts, chi_square = sbc_ranks(model)
parameter_confusion, parameter_accuracy, parameter_metrics =
    parameter_recovery(model, protocol)

open(joinpath(OUTPUT, "edge-exact-mutation.tsv"), "w") do io
    println(io, join(fieldnames(typeof(first(edge_rows))), '\t'))
    for row in edge_rows
        println(io, join((getfield(row, field)
            for field in fieldnames(typeof(row))), '\t'))
    end
end

open(joinpath(OUTPUT, "model-recovery.tsv"), "w") do io
    println(io, "truth_family\tpredicted_family\tcount")
    for truth in sort!(collect(keys(candidates));
            by = id -> candidates[id].ordinal)
        for predicted in sort!(collect(keys(candidates));
                by = id -> candidates[id].ordinal)
            println(io, candidates[truth].family, '\t',
                candidates[predicted].family, '\t',
                recovery_counts[(truth, predicted)])
        end
    end
end

open(joinpath(OUTPUT, "parameter-recovery.tsv"), "w") do io
    println(io, "truth\tprediction\tcount")
    for ((truth, prediction), count) in sort!(collect(parameter_confusion);
            by = item -> first(item))
        println(io, truth, '\t', prediction, '\t', count)
    end
end

summary = Dict{String,Any}(
    "edge_count" => length(edge_rows),
    "maximum_exact_parity_error" =>
        maximum(abs(row.parity_error) for row in edge_rows),
    "minimum_edge_mutation_delta" =>
        minimum(abs(row.target_delta) for row in edge_rows),
    "minimum_implementation_mutant_delta" =>
        minimum(abs(row.implementation_mutant_delta) for row in edge_rows),
    "minimum_named_trace_delta" =>
        minimum(abs(row.named_trace_delta) for row in edge_rows),
    "maximum_reverse_target_delta" =>
        maximum(abs(row.reverse_target_delta) for row in edge_rows),
    "maximum_unrelated_mutation_delta" =>
        maximum(abs(row.unrelated_delta) for row in edge_rows),
    "sbc_rank_counts" => rank_counts,
    "sbc_chi_square" => chi_square,
    "parameter_recovery_accuracy" => parameter_accuracy,
    "parameter_recovery" => parameter_metrics,
    "model_recovery_accuracy" =>
        sum(count for ((truth, predicted), count) in recovery_counts
            if truth == predicted) / sum(values(recovery_counts)),
    "model_families" => collect(String.(FAMILIES)),
)
open(joinpath(OUTPUT, "inference-validation.toml"), "w") do io
    TOML.print(io, summary; sorted = true)
end

println("inference validation outputs written to $OUTPUT")
