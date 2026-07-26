using CompositionalOrganism
using Statistics
using Test

const CO = CompositionalOrganism
const ROOT = normpath(joinpath(@__DIR__, ".."))
const GENOME = joinpath(ROOT, "genome.toml")
const DUMMY_ROOT = joinpath(ROOT, "protocols", "public-dummies")

function load_compiled(name = "51-P-00")
    documents = CO.load_documents(joinpath(DUMMY_ROOT, name))
    genome = CO.load_genome(GENOME)
    return documents, CO.compile_model(documents, genome),
        CO.compile_protocol(documents.protocol),
        CO.compile_analysis(documents.analysis)
end

function rebuild(model; nodes = model.nodes, edges = model.edges,
        channels = model.channels, policies = model.policies,
        candidates = model.candidates, factors = model.factors,
        distributions = model.distributions, processes = model.processes,
        emissions = model.emissions,
        genome = copy(model.genome))
    CO.CompiledModel(model.genome_id, model.configuration_id,
        model.initializer_id, model.history_generator_id,
        model.action_reconciler_id, model.world_id, model.family, model.horizon,
        model.episode_length, model.development_horizon, model.seed_namespace,
        model.development_emission_ids, nodes, edges, channels, policies,
        candidates, factors, distributions, processes,
        emissions, model.outcomes, model.contingencies, genome,
        model.action_costs, model.consumption)
end

function terminal_field(trace, arm, path)
    rows = [row for row in trace.rows if row isa CO.TickTraceRow &&
        row.arm == arm && haskey(row.fields, path)]
    return sort!(rows; by = row -> row.time)[end].fields[path]
end

@testset "closed typed compiler and genome identity" begin
    documents, model, protocol, analysis = load_compiled()
    @test model.configuration_id == "public-contract-dummy"
    @test length(model.nodes) == 12
    @test Set(node.kind for node in values(model.nodes)) == Set([
        :BundleNode, :ContextNode, :CueNode, :LocalPrecisionNode,
        :GlobalPrecisionNode, :ProtectorNode, :PartnerNode, :AccessNode,
        :EpisodeNode, :StructureNode,
    ])
    @test all(value isa CO.DistributionIR
        for value in values(model.distributions))
    @test all(value isa CO.ProcessIR for value in values(model.processes))
    @test all(value isa CO.ExpressionIR for value in
        (estimand.expression for estimand in analysis.estimands))
    @test Set(keys(model.consumption)) ==
        Set(vcat(["configuration.$path" for path in
            CO.leaf_paths(documents.configuration)],
            ["genome.$path" for path in
                CO.leaf_paths(CO.load_genome(GENOME))]))
    @test model.genome_id == CO.canonical_genome_hash(CO.load_genome(GENOME))
    @test length(model.genome_id) == 64
    @test protocol.protocol_id == "public-contract-dummy"
end

@testset "counter RNG and high-precision transforms" begin
    @test CO.counter_uniform(UInt64(7), :emission, "signal", 3, 0) ==
        CO.counter_uniform(UInt64(7), :emission, "signal", 3, 0)
    @test CO.counter_uniform(UInt64(7), :emission, "signal", 3, 0) !=
        CO.counter_uniform(UInt64(7), :emission, "signal", 3, 1)
    @test CO.inverse_categorical(["a", "b"], [0.25, 0.75], 0.25) == "b"
    @test CO.inverse_categorical(["a", "b"], [0.1, 0.1], 0.99) == "b"
    @test CO.normal_cdf(0.0) == 0.5
    @test CO.normal_cdf(1.959963984540054) ≈ 0.975 atol = 2e-12
    @test CO.erfinv(0.5) ≈ 0.4769362762044699 atol = 2e-15
    @test CO.inverse_beta(0.5, 8.0, 2.0) ≈
        CO.inverse_regularized_incomplete_beta(0.5, 8.0, 2.0) atol = 1e-12

    _, model, protocol, _ = load_compiled()
    distribution = model.distributions["reliable-signal"]
    on_component = CO.scalar_component(
        distribution, protocol, "broadcast-on")
    off_component = CO.scalar_component(
        distribution, protocol, "broadcast-off")
    @test on_component == "broadcast-on/reliable-signal"
    @test off_component == "broadcast-off/reliable-signal"
    @test on_component != off_component

    episode_distribution = CO.BetaDistributionIR(
        "episode-parameter", :episode, 4.0, 3.0)
    same_episode_a = CO.scalar_draw(episode_distribution, UInt64(3),
        "episode-parameter", 9, 8, 0)
    same_episode_b = CO.scalar_draw(episode_distribution, UInt64(3),
        "episode-parameter", 11, 8, 0)
    next_episode = CO.scalar_draw(episode_distribution, UInt64(3),
        "episode-parameter", 12, 12, 0)
    @test same_episode_a == same_episode_b
    @test same_episode_a != next_episode

    first_event = CO.ObservationEventIR("z-event", 1, :observe, :world,
        "cue-signal", "cue-emission", nothing, 1, 1, nothing)
    second_event = CO.ObservationEventIR("a-event", 1, :observe, :partner,
        "partner-signal", "partner-emission", nothing, 1, 1,
        CO.TriggerIR(:external_proxy, "action.success", :eq, true))
    occurrences = [
        CO.ScheduledOccurrence(1, 3, 1, 0, 0, "z-event#0", first_event),
        CO.ScheduledOccurrence(1, 3, 2, 0, 1, "a-event#0", second_event),
    ]
    ordinals = CO.scalar_event_ordinals(occurrences)
    @test ordinals == Dict("z-event#0" => 0, "a-event#0" => 1)
    @test CO.counter_uniform(UInt64(4), :distribution,
        "reliable-signal", 8, ordinals["a-event#0"]) !=
        CO.counter_uniform(UInt64(4), :distribution,
            "reliable-signal", 8, ordinals["z-event#0"])
end

@testset "directed typed edges, reversals, implementation mutants, and oracle" begin
    _, model, _, _ = load_compiled()
    endpoints = Dict(
        :bundle_context => ("context-main", "bundle-main"),
        :cue_root => ("cue-main", "bundle-main"),
        :local_monitor => ("bundle-main", "local-one"),
        :local_to_global_broadcast => ("local-one", "global-main"),
        :global_precision_message => ("global-main", "protector-one"),
        :protector_joint_policy => ("protector-one", "access-main"),
        :protector_cross_prediction => ("protector-one", "protector-two"),
        :partner_regulation => ("partner-main", "global-main"),
        :partner_trust => ("partner-main", "protector-one"),
        :policy_access => ("bundle-main", "access-main"),
        :access_bundle => ("access-main", "bundle-main"),
        :episode_scope => ("episode-main", "bundle-main"),
        :structure_scope => ("episode-main", "structure-main"),
        :registration => ("access-main", "bundle-main"),
        :world_coupling => ("context-main", "bundle-main"),
    )
    target_fields = Dict(
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
    function set_source!(state, micro, source)
        node = micro.nodes[source]
        values = state.node_values[source]
        state.node_beliefs[source] .=
            CO.normalize_distribution(vcat(
                fill(0.1 / (node.cardinality - 1),
                    node.cardinality - 1), 0.9))
        if node.kind == :ContextNode
            values["transition_entropy"] = 0.1
        elseif node.kind == :BundleNode
            values["activation_probability"] = 0.9
            values["mandate_probability"] = 0.9
        elseif node.kind == :CueNode
            values["meaning_probability"] = 0.9
        elseif node.kind == :LocalPrecisionNode
            values["mean"] = 0.9
        elseif node.kind == :GlobalPrecisionNode
            values["depth"] = 0.9
        elseif node.kind == :ProtectorNode
            values["permission_probability"] = 0.9
            values["forecast_outcome"] = 0.9
        elseif node.kind == :PartnerNode
            values["trust_probability"] = 0.9
            values["regulation_probability"] = 0.9
        elseif node.kind == :AccessNode
            values["probability"] = 0.9
        elseif node.kind == :EpisodeNode
            values["joint_probability"] = 0.9
        end
    end
    function traced_value(state, micro, target, field)
        world = CO.WorldState(Dict{String,String}(),
            Dict{String,Bool}(), Dict{Tuple{String,Int},Float64}(),
            Dict{String,Int}())
        row = CO.tick_row(UInt64(1), "micro", 0, 0, 0,
            false, "", state, micro, world)
        path = only(key for key in keys(row.fields)
            if endswith(key, ".$target.$field"))
        return row.fields[path]
    end
    @test Set(keys(endpoints)) == CO.EDGE_KINDS
    for kind in sort!(collect(CO.EDGE_KINDS))
        source, target = endpoints[kind]
        edge = CO.EdgeIR("micro-$(kind)", kind, source, target, :active)
        micro = rebuild(model; edges = Dict(edge.id => edge),
            candidates = Dict{String,CO.CandidateIR}())
        state = CO.initialize_state(micro)
        set_source!(state, micro, source)
        unrelated = first(id for id in keys(state.node_values)
            if id ∉ (source, target))
        approximate = CO.belief_propagation(state, micro)
        exact = CO.exact_graph_marginals(state, micro)
        @test maximum(abs(approximate[id] - exact[id])
            for id in keys(exact)) < 1e-12

        deleted = rebuild(micro; edges = Dict{String,CO.EdgeIR}())
        deleted_state = CO.initialize_state(deleted)
        set_source!(deleted_state, deleted, source)
        mutant = CO.belief_propagation(deleted_state, deleted)
        @test exact[target] != mutant[target]
        @test exact[unrelated] ≈ mutant[unrelated] atol = 1e-12

        reversed_edge = CO.EdgeIR(
            "reversed-$(kind)", kind, target, source, :active)
        reversed = rebuild(model; edges = Dict(
            reversed_edge.id => reversed_edge),
            candidates = Dict{String,CO.CandidateIR}())
        reversed_state = CO.initialize_state(reversed)
        set_source!(reversed_state, reversed, source)
        reversed_result = CO.belief_propagation(reversed_state, reversed)
        @test reversed_result[target] ≈ mutant[target] atol = 1e-12

        implementation_mutant = CO.belief_propagation(
            state, micro; muted_kind = kind)
        @test implementation_mutant[target] ≈ mutant[target] atol = 1e-12

        if kind != :structure_scope
            observation = CO.Observation("edge-semantic", 0, :world,
                "cue-signal", nothing, [source, target], Set{String}(),
                :categorical, "positive", 0.9,
                Dict{String,Float64}(), 0.0, 0.0, false,
                "edge-semantic")
            named = deepcopy(state)
            muted = deepcopy(state)
            removed = deepcopy(deleted_state)
            CO.apply_directed_semantics!(named, micro, observation)
            CO.apply_directed_semantics!(
                muted, micro, observation; muted_kind = kind)
            CO.apply_directed_semantics!(removed, deleted, observation)
            field = target_fields[kind]
            @test traced_value(named, micro, target, field) !=
                traced_value(removed, deleted, target, field)
            @test traced_value(muted, micro, target, field) ==
                traced_value(removed, deleted, target, field)
        end
    end

    state = CO.initialize_state(model)
    state.node_beliefs["episode-main"] .= [0.02, 0.03, 0.05, 0.90]
    observation = CO.Observation("structure-semantic", 0, :world,
        "episode-signal", nothing,
        ["episode-main", "bundle-main", "context-main"], Set{String}(),
        :categorical, "safe", 0.9, Dict{String,Float64}(), 0.0, 0.0,
        false, "structure-semantic")
    present = CO.candidate_scores(state, model, observation)
    no_scope_edges = Dict(id => edge for (id, edge) in model.edges
        if edge.kind != :structure_scope)
    no_scope = rebuild(model; edges = no_scope_edges)
    absent = CO.candidate_scores(CO.initialize_state(no_scope),
        no_scope, observation)
    @test any(present[id] != absent[id] for id in keys(present))
end

@testset "loopy schedules, node ordering, and zero-slot idleness" begin
    _, model, _, _ = load_compiled()
    state = CO.initialize_state(model)
    for (ordinal, id) in enumerate(sort!(collect(keys(state.node_beliefs))))
        cardinality = length(state.node_beliefs[id])
        state.node_beliefs[id] .= CO.normalize_distribution(
            [ordinal + index for index in 1:cardinality])
    end
    approximate = CO.directed_node_beliefs(state, model)
    oracle = CO.directed_node_beliefs(state, model; iterations = 512)
    reverse_schedule = CO.directed_node_beliefs(
        state, model; iterations = 512, reverse_order = true)
    @test maximum(maximum(abs.(approximate[id] .- oracle[id]))
        for id in keys(oracle)) < 1e-10
    @test maximum(maximum(abs.(oracle[id] .- reverse_schedule[id]))
        for id in keys(oracle)) < 1e-12

    reversed_nodes = Dict(reverse(collect(model.nodes)))
    reversed_edges = Dict(reverse(collect(model.edges)))
    reordered = rebuild(model; nodes = reversed_nodes, edges = reversed_edges)
    reordered_state = CO.initialize_state(reordered)
    for id in keys(state.node_beliefs)
        reordered_state.node_beliefs[id] .= state.node_beliefs[id]
    end
    reordered_beliefs = CO.directed_node_beliefs(
        reordered_state, reordered; iterations = 512)
    @test all(isapprox(oracle[id], reordered_beliefs[id]; atol = 1e-12)
        for id in keys(oracle))

    inactive_ids = Set(["protector-two", "protector-three"])
    slotted_nodes = Dict(id => CO.NodeIR(node.id, node.kind,
        node.cardinality, node.slot, id in inactive_ids ? false : node.active)
        for (id, node) in model.nodes)
    removed_nodes = Dict(id => node for (id, node) in slotted_nodes
        if id ∉ inactive_ids)
    kept_edges = Dict(id => edge for (id, edge) in model.edges
        if edge.source ∉ inactive_ids && edge.target ∉ inactive_ids)
    filtered_policies = Dict(id => CO.PolicyIR(policy.id, policy.family,
        [actor for actor in policy.actors if actor ∉ inactive_ids],
        policy.actions, policy.enabled)
        for (id, policy) in model.policies)
    slotted = rebuild(model; nodes = slotted_nodes, edges = kept_edges,
        policies = filtered_policies,
        candidates = Dict{String,CO.CandidateIR}())
    removed = rebuild(model; nodes = removed_nodes, edges = kept_edges,
        policies = filtered_policies,
        candidates = Dict{String,CO.CandidateIR}())
    slotted_state = CO.initialize_state(slotted)
    removed_state = CO.initialize_state(removed)
    @test slotted_state.node_beliefs == removed_state.node_beliefs
    @test slotted_state.node_values == removed_state.node_values
    @test slotted_state.policy_counts == removed_state.policy_counts
    @test CO.infer_policy!(slotted_state, slotted)
    @test CO.infer_policy!(removed_state, removed)
    @test slotted_state.policy_posterior == removed_state.policy_posterior
    @test slotted_state.selected_action == removed_state.selected_action
end

@testset "neutral learnable parameters enter only through learning" begin
    _, model, protocol, _ = load_compiled()
    state = CO.initialize_state(model)
    learnable = only(edge for edge in values(model.edges)
        if edge.initial_state == :learnable)
    @test !state.edge_enabled[learnable.id]
    @test all(all(==(model.genome["dirichlet_concentration"]), counts)
        for counts in values(state.likelihood_counts))
    @test all(all(==(model.genome["dirichlet_concentration"]), counts)
        for counts in values(state.transition_counts))
    world = CO.initialize_world(model, protocol, "broadcast-on", UInt64(5))
    observation = CO.account_observation(CO.generate_observation(model, world,
        protocol, "broadcast-on", UInt64(5), "observe#0", 1,
        "cue-emission", 0), state, model)
    before = deepcopy(state.likelihood_counts)
    CO.infer!(state, model, observation)
    CO.learn!(state, model, observation)
    @test state.likelihood_counts != before
    @test state.edge_enabled[learnable.id] ==
        (state.edge_strength[learnable.id] > 0.5)

    state.node_values["local-one"]["mean"] = 0.001
    low_reliability = CO.Observation("precision-floor", 0, :world,
        "cue-signal", nothing, ["bundle-main", "local-one"],
        Set{String}(), :categorical, "positive", 0.001,
        Dict{String,Float64}(), 0.0, 0.0, false, "precision-floor")
    CO.apply_directed_semantics!(state, model, low_reliability)
    @test state.node_values["local-one"]["mean"] >=
        model.genome["precision_floor"]
end

@testset "joint, masked, and bounded-Gaussian evidence accounting" begin
    _, model, _, _ = load_compiled()
    distributions = copy(model.distributions)
    categorical_ids = String[]
    for index in 1:6
        id = "joint-table-$index"
        push!(categorical_ids, id)
        p = 0.15 + 0.10 * index
        distributions[id] =
            CO.CategoricalDistributionIR(id, ["x", "y"], [p, 1 - p])
    end
    distributions["gaussian-noise"] =
        CO.FixedDistributionIR("gaussian-noise", :event, 0.12)
    channels = copy(model.channels)
    channels["joint-test"] = CO.ChannelIR("joint-test", :world,
        ["partner-main", "bundle-main"], :categorical,
        ["x", "y"], nothing, true)
    channels["gaussian-test"] = CO.ChannelIR("gaussian-test", :body,
        ["partner-main", "bundle-main"], :gaussian_bounded,
        String[], (0.0, 1.0), true)
    emissions = copy(model.emissions)
    emissions["joint-test-emission"] = CO.EmissionIR(
        "joint-test-emission", ["partner-state", "exposure-state"],
        "joint-test", :categorical, categorical_ids, Float64[], nothing,
        "reliable-signal", Set(["exposure-state"]))
    emissions["gaussian-test-emission"] = CO.EmissionIR(
        "gaussian-test-emission", ["partner-state", "exposure-state"],
        "gaussian-test", :gaussian_bounded, String[],
        collect(range(0.15, 0.85; length = 6)), "gaussian-noise",
        "reliable-signal", Set{String}())
    joint_model = rebuild(model; channels = channels,
        distributions = distributions, emissions = emissions)
    state = CO.initialize_state(joint_model)

    categorical_likelihoods = CO.observation_likelihoods(joint_model,
        emissions["joint-test-emission"], "x", 0.8)
    categorical = CO.Observation("joint-test", 0, :world, "joint-test",
        "joint-test-emission",
        ["partner-state", "exposure-state", "partner-main", "bundle-main"],
        Set(["exposure-state"]), :categorical, "x", 0.8, nothing,
        categorical_likelihoods, 0.0, 0.0, false, "joint-test")
    accounted = CO.account_observation(categorical, state, joint_model)
    exposure_before = copy(state.factor_beliefs["exposure-state"])
    CO.infer!(state, joint_model, accounted)
    @test isfinite(accounted.delivered_log_likelihood)
    @test isfinite(accounted.marginal_equivalence_error)
    @test state.factor_beliefs["exposure-state"] == exposure_before

    gaussian_emission = emissions["gaussian-test-emission"]
    gaussian_likelihoods = CO.observation_likelihoods(joint_model,
        gaussian_emission, 0.42, 0.9;
        scale = 0.12 / 0.9, bounds = (0.0, 1.0))
    gaussian = CO.Observation("gaussian-test", 0, :body,
        "gaussian-test", "gaussian-test-emission",
        ["partner-state", "exposure-state", "partner-main", "bundle-main"],
        Set{String}(), :gaussian_bounded, 0.42, 0.9, 0.12 / 0.9,
        gaussian_likelihoods, 0.0, 0.0, false, "gaussian-test")
    gaussian_accounted =
        CO.account_observation(gaussian, state, joint_model)
    @test isfinite(gaussian_accounted.delivered_log_likelihood)
    @test isfinite(gaussian_accounted.marginal_equivalence_error)
    grid = range(0.0, 1.0; length = 2001)
    first_key = "joint|partner-state=helpful;exposure-state=low"
    densities = [CO.observation_likelihoods(joint_model,
        gaussian_emission, value, 0.9;
        scale = 0.12 / 0.9, bounds = (0.0, 1.0))[first_key]
        for value in grid]
    integral = step(grid) *
        (sum(densities) - (first(densities) + last(densities)) / 2)
    @test integral ≈ 1.0 atol = 2e-4
end

@testset "joint generative policy supports zero, two, and three protectors" begin
    _, model, _, _ = load_compiled()
    for protector_count in (0, 2, 3)
        nodes = Dict(id => CO.NodeIR(node.id, node.kind, node.cardinality,
            node.slot, node.kind != :ProtectorNode ||
                node.slot <= protector_count)
            for (id, node) in model.nodes)
        policies = if protector_count == 0
            actions = first(values(model.policies)).actions
            Dict("bundle-policy" => CO.PolicyIR("bundle-policy", :contact,
                ["bundle-main"], actions, true))
        else
            Dict(id => CO.PolicyIR(policy.id, policy.family,
                [actor for actor in policy.actors
                    if nodes[actor].active],
                policy.actions, policy.enabled)
                for (id, policy) in model.policies)
        end
        variant = rebuild(model; nodes = nodes, policies = policies)
        state = CO.initialize_state(variant)
        @test CO.infer_policy!(state, variant)
        @test isapprox(sum(values(state.policy_posterior)), 1.0; atol = 1e-12)
        expected = protector_count == 0 ? 6 : 6^protector_count
        @test length(state.policy_posterior) == expected
        @test state.selected_action in keys(state.action_enabled)
        @test all(isfinite, values(state.policy_gfe))
    end
end

@testset "replay learning is consumed by transitions and joint outcomes" begin
    _, model, protocol, _ = load_compiled()
    state = CO.initialize_state(model)
    world = CO.initialize_world(model, protocol, "broadcast-on", UInt64(41))
    transition_before = deepcopy(state.transition_counts)
    CO.predict_factors!(state, model)
    observation = CO.account_observation(CO.generate_observation(
        model, world, protocol, "broadcast-on", UInt64(41),
        "transition-learning", 1, "partner-emission", 0, 0),
        state, model)
    CO.infer!(state, model, observation)
    CO.learn!(state, model, observation)
    @test state.transition_counts != transition_before
    learned_matrix = CO.learned_process_matrix(
        state, model, model.processes["partner-process"])
    @test any(abs.(learned_matrix .- 1 / size(learned_matrix, 2)) .> 1e-8)
    state.factor_beliefs["partner-state"] .= [0.8, 0.1, 0.1]
    prior = copy(state.factor_beliefs["partner-state"])
    CO.predict_factors!(state, model)
    @test state.factor_beliefs["partner-state"] != prior

    policy_state = CO.initialize_state(model)
    @test CO.infer_policy!(policy_state, model)
    selected_label = policy_state.selected_policy_label
    selected_action = policy_state.selected_action
    joint_before = copy(policy_state.joint_policy_counts[selected_label])
    access_before = copy(policy_state.joint_access_counts[selected_label])
    trust_before = deepcopy(policy_state.trust_counts)
    policy_world =
        CO.initialize_world(model, protocol, "broadcast-on", UInt64(42))
    trust_observation = CO.account_observation(CO.generate_observation(
        model, policy_world, protocol, "broadcast-on", UInt64(42),
        "trust-learning", 1, "partner-emission", 0, 0),
        policy_state, model)
    CO.infer!(policy_state, model, trust_observation)
    CO.learn!(policy_state, model, trust_observation)
    @test policy_state.trust_counts != trust_before
    trust_after_observation = deepcopy(policy_state.trust_counts)
    CO.generate_outcomes!(policy_state, policy_world, model, protocol,
        "broadcast-on", UInt64(42), 1)
    CO.learn_outcomes!(policy_state, model)
    @test policy_state.joint_policy_counts[selected_label] != joint_before
    @test policy_state.joint_access_counts[selected_label] != access_before
    @test policy_state.trust_counts == trust_after_observation
    @test selected_action == policy_state.selected_action

    gfe_before = policy_state.policy_gfe[selected_label]
    policy_state.joint_policy_counts[selected_label] .= [1.0, 20.0]
    CO.infer_policy!(policy_state, model)
    @test policy_state.policy_gfe[selected_label] != gfe_before
end

@testset "probe and imaginal paths preserve persistent state" begin
    _, model, protocol, _ = load_compiled()
    state = CO.initialize_state(model)
    world = CO.initialize_world(model, protocol, "broadcast-on", UInt64(5))
    observation = CO.account_observation(CO.generate_observation(model, world,
        protocol, "broadcast-on", UInt64(5), "probe#0", 1,
        "cue-emission", 0), state, model)
    edges_before = copy(state.edge_strength)
    structures_before = copy(state.structure_evidence)
    scores = CO.candidate_scores(state, model, observation)
    CO.infer!(state, model, observation)
    @test !isempty(scores)
    @test state.edge_strength == edges_before
    @test state.structure_evidence == structures_before

    channel = model.channels["episode-signal"]
    imaginal_channel = CO.ChannelIR("imaginal-test", :imaginal,
        copy(channel.scope), channel.likelihood_family, copy(channel.values),
        channel.bounds, true)
    imaginal_model = rebuild(model)
    imaginal_model.channels["imaginal-test"] = imaginal_channel
    event = CO.ObservationEventIR("imaginal", 1, :imaginal, :imaginal,
        "imaginal-test", nothing, "posterior-predictive-mode-v1",
        1, 1, nothing)
    imagined = CO.imaginal_observation(
        state, imaginal_model, event, "imaginal#0", 1)
    @test imagined.is_imaginal
    @test imagined.value in imaginal_channel.values
    @test imagined.value == CO.imaginal_observation(
        state, imaginal_model, event, "imaginal#0", 1).value
    imaginal_evidence = copy(state.structure_evidence)
    CO.score_structures!(state, imaginal_model, imagined)
    @test state.structure_evidence != imaginal_evidence
end

@testset "canonical success, change-point, global-field, and joint semantics" begin
    _, model, protocol, _ = load_compiled()
    action_process = model.processes["exposure-process"]
    world = CO.initialize_world(model, protocol, "broadcast-on", UInt64(91))
    world.contingency_enabled["success-enables-approach-transition"] = true
    prior = copy(world.truth)
    failed = CO.process_distribution(model, action_process, prior, world,
        "approach", false, 2)
    successful = CO.process_distribution(model, action_process, prior, world,
        "approach", true, 2)
    @test failed === model.distributions[action_process.baseline_id]
    @test successful === model.distributions[action_process.action_id]

    distributions = copy(model.distributions)
    values = model.factors["episode-state"].values
    before = fill(0.05, 4, 4)
    after = fill(0.05, 4, 4)
    for index in 1:4
        before[index, index] = 0.85
        after[index, 5 - index] = 0.85
    end
    distributions["semantic-before"] =
        CO.TransitionDistributionIR("semantic-before", values, before)
    distributions["semantic-after"] =
        CO.TransitionDistributionIR("semantic-after", values, after)
    distributions["semantic-change-time"] =
        CO.FixedDistributionIR("semantic-change-time", :world, 5.0)
    process = CO.ChangePointProcessIR("semantic-change-point",
        "episode-state", "semantic-before", "semantic-after",
        "semantic-change-time", 1)
    change_model = rebuild(model; distributions = distributions,
        processes = Dict(process.id => process))
    change_state = CO.initialize_state(change_model)
    change_state.transition_counts["semantic-before"] .= before
    change_state.transition_counts["semantic-after"] .= after
    @test CO.learned_process_matrix(
        change_state, change_model, process, 0) ≈ before
    @test CO.learned_process_matrix(
        change_state, change_model, process, 10) ≈ after

    global_state = CO.initialize_state(model)
    global_values = global_state.node_values["global-main"]
    global_state.node_values["context-main"]["transition_entropy"] = 0.1
    context_observation = CO.Observation("global-context", 0, :world,
        "episode-signal", nothing, ["context-main"], Set{String}(),
        :categorical, "safe", 0.7, Dict{String,Float64}(),
        0.0, 0.0, false, "global-context")
    CO.apply_directed_semantics!(global_state, model, context_observation)
    @test global_values["context"] > 0.5
    body_observation = CO.Observation("global-body", 0, :body,
        "cue-signal", nothing, ["local-one"], Set{String}(),
        :categorical, "positive", 0.8, Dict{String,Float64}(),
        0.0, 0.0, false, "global-body")
    CO.apply_directed_semantics!(global_state, model, body_observation)
    @test global_values["interoception"] == 0.8
    global_state.node_values["local-one"]["mean"] = 0.9
    global_state.node_values["partner-main"]["regulation_probability"] = 0.8
    CO.apply_directed_semantics!(global_state, model, body_observation)
    @test global_values["part"] > 0.5
    @test global_values["relationship"] > 0.5
    @test CO.infer_policy!(global_state, model)
    @test global_values["policy"] != 0.5
    @test global_values["depth"] == mean(global_values[field] for field in
        ("part", "context", "interoception", "relationship", "policy"))

    joint_state = CO.initialize_state(model)
    actors = sort!([id for (id, node) in model.nodes
        if node.active && node.kind == :ProtectorNode])
    joint_state.selected_action = "approach"
    joint_state.selected_policy_label =
        join(("$actor=approach" for actor in actors), ";")
    @test CO.joint_coordination(joint_state, model) == 1.0
    joint_state.selected_policy_label =
        join(("$actor=$(index == 1 ? "observe" : "approach")"
            for (index, actor) in enumerate(actors)), ";")
    @test CO.joint_coordination(joint_state, model) < 1.0

    edges = Dict(
        "field-cue" => CO.EdgeIR("field-cue", :cue_root,
            "cue-main", "bundle-main", :active),
        "field-registration" => CO.EdgeIR("field-registration", :registration,
            "access-main", "bundle-main", :active),
    )
    field_model = rebuild(model; edges = edges,
        candidates = Dict{String,CO.CandidateIR}())
    weak_registration = CO.initialize_state(field_model)
    strong_registration = CO.initialize_state(field_model)
    for state in (weak_registration, strong_registration)
        state.node_values["cue-main"]["meaning_probability"] = 0.9
        state.node_values["access-main"]["probability"] = 0.2
    end
    weak_registration.edge_strength["field-registration"] = 0.1
    strong_registration.edge_strength["field-registration"] = 1.0
    field_observation = CO.Observation("field-weight", 0, :world,
        "cue-signal", nothing, ["cue-main", "access-main", "bundle-main"],
        Set{String}(), :categorical, "positive", 0.8,
        Dict{String,Float64}(), 0.0, 0.0, false, "field-weight")
    CO.apply_directed_semantics!(
        weak_registration, field_model, field_observation)
    CO.apply_directed_semantics!(
        strong_registration, field_model, field_observation)
    @test weak_registration.node_values["bundle-main"]["root_probability"] ==
        strong_registration.node_values["bundle-main"]["root_probability"]
    @test weak_registration.node_values["bundle-main"]["mandate_probability"] !=
        strong_registration.node_values["bundle-main"]["mandate_probability"]
end

@testset "candidate generative evidence, label invariance, and BMR history" begin
    _, model, protocol, _ = load_compiled()
    state = CO.initialize_state(model)
    state.node_beliefs["episode-main"] .= [0.02, 0.03, 0.05, 0.90]
    state.node_beliefs["bundle-main"] .= [0.15, 0.85]
    world = CO.initialize_world(model, protocol, "broadcast-on", UInt64(77))
    observation = CO.account_observation(CO.generate_observation(
        model, world, protocol, "broadcast-on", UInt64(77),
        "candidate-evidence", 1, "episode-emission", 0, 0),
        state, model)
    for candidate in values(model.candidates)
        probabilities = CO.categorical_candidate_probabilities(
            state, model, observation, candidate)
        @test sum(values(probabilities)) ≈ 1.0 atol = 1e-12
        @test all(>(0.0), values(probabilities))
    end
    scores = CO.candidate_scores(state, model, observation)
    @test length(unique(values(scores))) > 1
    initial = copy(state.structure_evidence)
    CO.score_structures!(state, model, observation)
    @test all(state.structure_evidence[id] ≈ initial[id] + scores[id]
        for id in keys(scores))

    channels = copy(model.channels)
    original_channel = channels["episode-signal"]
    channels["episode-signal"] = CO.ChannelIR(original_channel.id,
        original_channel.source, copy(original_channel.scope),
        original_channel.likelihood_family,
        reverse(copy(original_channel.values)), original_channel.bounds,
        original_channel.enabled)
    distributions = copy(model.distributions)
    for distribution_id in
            model.emissions["episode-emission"].conditional_distribution_ids
        distribution =
            model.distributions[distribution_id]::CO.CategoricalDistributionIR
        distributions[distribution_id] = CO.CategoricalDistributionIR(
            distribution.id, reverse(copy(distribution.values)),
            reverse(copy(distribution.probabilities)))
    end
    relabeled = rebuild(model; channels = channels,
        distributions = distributions)
    relabeled_state = CO.initialize_state(relabeled)
    relabeled_state.node_beliefs = deepcopy(state.node_beliefs)
    relabeled_scores =
        CO.candidate_scores(relabeled_state, relabeled, observation)
    @test all(isapprox(scores[id], relabeled_scores[id]; atol = 1e-12)
        for id in keys(scores))

    history = CO.initialize_state(model)
    candidates = CO.ordered_candidates(model, "structure-main")
    active_counts = Dict(candidate.id => count(edge_id ->
        CO.candidate_edge_state(candidate, model.edges[edge_id]),
        keys(model.edges)) for candidate in candidates)
    reduced = first(sort!(copy(candidates);
        by = candidate -> (active_counts[candidate.id], candidate.ordinal)))
    full = first(sort!(copy(candidates);
        by = candidate -> (-active_counts[candidate.id], candidate.ordinal)))
    for id in keys(history.structure_evidence)
        history.structure_evidence[id] = 0.0
    end
    history.structure_evidence[reduced.id] = 2.0
    CO.update_structure_history!(history, model, 3)
    CO.update_structure_history!(history, model, 4)
    @test history.node_values["structure-main"][
        "first_stable_reduced_win"] == 4
    history.structure_evidence[full.id] = 3.0
    CO.update_structure_history!(history, model, 5)
    @test history.node_values["structure-main"]["reversals_to_full"] == 1

    for id in keys(history.structure_evidence)
        history.structure_evidence[id] = 1.0
    end
    @test CO.candidate_winner(history, candidates).id == first(candidates).id
end

@testset "analysis policies and evaluation provenance are executable" begin
    _, model, protocol, analysis = load_compiled()
    trace = CO.run_protocol(model, protocol, 123)
    result = CO.evaluate_trace(trace, analysis)
    @test all(!isempty(item.expression_ast)
        for item in values(result.estimands))
    @test all(!isempty(item.source_row_hashes)
        for item in values(result.estimands))
    @test all(row.fields["run.genome_id"] == model.genome_id
        for row in trace.rows)

    crossing = CO.TemporalExpr(:first_crossing,
        CO.FieldExpr("state.access.access-main.probability"), 0, :ge,
        2.0, 1, nothing)
    for (non_crossing, expected) in
            ((:horizon_plus_one, model.horizon), (:missing, missing))
        plan = CO.AnalysisIR("policy-test", :seed, :pass, non_crossing,
            :missing, :fail, CO.EstimandIR[], CO.DecisionIR[])
        data = CO.evaluate_expression(crossing, trace, plan)
        @test all(item.value === expected for item in data)
    end
    failure_plan = CO.AnalysisIR("policy-test", :seed, :pass, :fail,
        :fail, :fail, CO.EstimandIR[], CO.DecisionIR[])
    @test_throws ErrorException CO.evaluate_expression(
        crossing, trace, failure_plan)

    one_value = CO.AggregateExpr(:std,
        CO.WhereExpr(CO.FieldExpr("run.time"),
            [CO.PredicateIR("run.time", :eq, 0),
                CO.PredicateIR("run.row_kind", :eq, "tick")]), nothing)
    missing_plan = CO.AnalysisIR("policy-test", :episode, :missing,
        :missing, :missing, :missing, CO.EstimandIR[], CO.DecisionIR[])
    std_data = CO.evaluate_expression(one_value, trace, missing_plan)
    @test all(item.value === missing for item in std_data)

    divide_by_zero = CO.BinaryExpr(:divide,
        CO.FieldExpr("run.time"), CO.LiteralExpr(0.0))
    nonfinite_fail = CO.AnalysisIR("policy-test", :seed, :pass,
        :missing, :fail, :fail, CO.EstimandIR[], CO.DecisionIR[])
    @test_throws ErrorException CO.evaluate_expression(
        divide_by_zero, trace, nonfinite_fail)
    nonfinite_missing = CO.AnalysisIR("policy-test", :seed, :pass,
        :missing, :missing, :missing, CO.EstimandIR[], CO.DecisionIR[])
    divided = CO.evaluate_expression(
        divide_by_zero, trace, nonfinite_missing)
    @test any(item.value === missing for item in divided)
    nonfinite_drop = CO.AnalysisIR("policy-test", :seed, :pass,
        :missing, :drop_pair, :drop_pair, CO.EstimandIR[], CO.DecisionIR[])
    dropped = CO.evaluate_expression(divide_by_zero, trace, nonfinite_drop)
    @test all(item.value isa Number && isfinite(item.value)
        for item in dropped)

    empty_expression = CO.AggregateExpr(:mean,
        CO.WhereExpr(CO.FieldExpr("run.time"),
            [CO.PredicateIR("run.time", :eq, 999)]), nothing)
    empty_estimand = CO.EstimandIR("empty", :audit, :development,
        empty_expression, :identity, CO.IntervalIR(:none, nothing, 0),
        Set{String}())
    empty_decision = CO.DecisionIR(
        "empty-fails", "empty", :ge, 0.0, :none)
    empty_plan = CO.AnalysisIR("empty-policy", :seed, :pass, :missing,
        :missing, :missing, [empty_estimand], [empty_decision])
    empty_result = CO.evaluate_trace(trace, empty_plan)
    @test empty_result.estimands["empty"].value === missing
    @test !empty_result.decisions["empty-fails"]

    event_plan = CO.AnalysisIR("event-policy", :event, :pass, :missing,
        :fail, :fail, CO.EstimandIR[], CO.DecisionIR[])
    event_values = CO.evaluate_expression(CO.AggregateExpr(:mean,
        CO.FieldExpr("run.event_index"), nothing), trace, event_plan)
    @test !isempty(event_values)
    genome_plan = CO.AnalysisIR("genome-policy", :genome, :pass, :missing,
        :fail, :fail, CO.EstimandIR[], CO.DecisionIR[])
    genome_values = CO.evaluate_expression(CO.AggregateExpr(:mean,
        CO.FieldExpr("run.time"), nothing), trace, genome_plan)
    @test length(genome_values) == length(protocol.arms)

    classification = CO.ClassificationExpr(:classification_accuracy,
        "world.truth.partner-state", "world.truth.partner-state", "run.arm")
    classified = CO.evaluate_expression(
        classification, trace, analysis)
    @test !isempty(classified)
    @test all(item.value == 1.0 for item in classified)
    @test all(occursin("stratum=", item.path) for item in classified)
end

if get(ENV, "CO_FAST_TEST", "0") != "1"
@testset "public dry runs discriminate topology and reproduce exactly" begin
    traces = Dict{String,CO.TraceTable}()
    results = Dict{String,CO.EvaluationResult}()
    for name in ("51-P-00", "51-P-90", "51-P-91")
        documents, model, protocol, analysis = load_compiled(name)
        first_trace = CO.run_protocol(model, protocol, 10_001)
        first_result = CO.evaluate_trace(first_trace, analysis)
        second_trace = CO.run_protocol(model, protocol, 10_001)
        second_result = CO.evaluate_trace(second_trace, analysis)
        @test CO.trace_hash(first_trace) == CO.trace_hash(second_trace)
        @test first_result.decisions == second_result.decisions
        @test CO.initialization_hash(first_trace) ==
            CO.initialization_hash(second_trace)
        @test length(first_trace.initialization_rows) ==
            length(protocol.arms) * model.development_horizon *
                length(model.development_emission_ids)
        @test all(!isempty(row.model_candidates)
            for row in first_trace.initialization_rows)
        @test all(haskey(row.fields, "provenance.model_candidate")
            for row in first_trace.rows if row isa CO.EventTraceRow &&
                row.executed && haskey(row.fields, "observation.source"))
        @test isempty(CO.audit_requested_fields(first_trace, protocol))
        @test count(row -> row isa CO.TickTraceRow, first_trace.rows) ==
            2 * model.horizon
        traces[name] = first_trace
        results[name] = first_result
    end
    @test length(unique(CO.trace_hash(trace) for trace in values(traces))) == 3
    coprotection_path =
        "state.protector.protector-two.forecast_coprotection"
    @test terminal_field(traces["51-P-00"], "broadcast-on",
        coprotection_path) != terminal_field(
        traces["51-P-90"], "broadcast-on", coprotection_path)
    local_path = "state.local_precision.local-one.mean"
    global_path = "state.global_precision.global-main.depth"
    @test terminal_field(traces["51-P-00"], "broadcast-on", local_path) ==
        terminal_field(traces["51-P-91"], "broadcast-on", local_path)
    @test terminal_field(traces["51-P-00"], "broadcast-on", global_path) !=
        terminal_field(traces["51-P-91"], "broadcast-on", global_path)
    @test isfinite(results["51-P-00"].estimands["budget-match"].value)
end
end

@testset "world truth boundary and static source boundary" begin
    @test :truth in fieldnames(CO.WorldState)
    @test :truth ∉ fieldnames(CO.OrganismState)
    @test :factor_beliefs in fieldnames(CO.OrganismState)
    @test isempty(CO.static_architecture_audit(ROOT))
    _, model, _, _ = load_compiled()
    @test all(CO.semantic_gate(model))
end
