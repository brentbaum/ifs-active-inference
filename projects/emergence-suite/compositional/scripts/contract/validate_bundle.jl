#!/usr/bin/env julia

using TOML

const CONTRACT_ID = "ifs-ai-experiment-51-contract"
const CONTRACT_VERSION = "1.0.0"
const ID_PATTERN = r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$"
const EDGE_SIGNATURES = Dict(
    "bundle_context" => (Set(["ContextNode"]), Set(["BundleNode"])),
    "cue_root" => (Set(["CueNode"]), Set(["BundleNode"])),
    "local_monitor" => (Set(["BundleNode"]), Set(["LocalPrecisionNode"])),
    "local_to_global_broadcast" =>
        (Set(["LocalPrecisionNode"]), Set(["GlobalPrecisionNode"])),
    "global_precision_message" => (Set(["GlobalPrecisionNode"]),
        Set(["BundleNode", "ContextNode", "ProtectorNode"])),
    "protector_joint_policy" =>
        (Set(["ProtectorNode"]), Set(["AccessNode"])),
    "protector_cross_prediction" =>
        (Set(["ProtectorNode"]), Set(["ProtectorNode"])),
    "partner_regulation" =>
        (Set(["PartnerNode"]), Set(["GlobalPrecisionNode"])),
    "partner_trust" => (Set(["PartnerNode"]), Set(["ProtectorNode"])),
    "policy_access" => (Set(["BundleNode"]), Set(["AccessNode"])),
    "access_bundle" => (Set(["AccessNode"]), Set(["BundleNode"])),
    "episode_scope" => (Set(["EpisodeNode"]),
        Set(["BundleNode", "CueNode", "ContextNode"])),
    "structure_scope" => (Set(["BundleNode", "ContextNode", "EpisodeNode"]),
        Set(["StructureNode"])),
    "registration" => (Set(["AccessNode"]), Set(["BundleNode"])),
    "world_coupling" => (Set(["BundleNode", "ContextNode", "PartnerNode"]),
        Set(["BundleNode", "ContextNode", "PartnerNode"])),
)
const EXTERNAL_TRIGGER_PATHS = Set([
    "run.time", "action.selected", "action.success",
    "action.delivered_exposure", "observation.source",
    "observation.scope_size", "observation.is_imaginal",
    "observation.delivered_log_likelihood",
])
const ACTION_PRIORITY = [
    "withdraw", "suppress", "wait", "observe", "inspect",
    "request_support", "offer_support", "permit", "approach",
]

fail(message) = error("semantic bundle validation: $message")
require(condition, message) = condition || fail(message)

validate_id(value, label) = require(
    value isa AbstractString && occursin(ID_PATTERN, value) &&
        ncodeunits(value) <= 64,
    "$label is not a valid identifier: $value")

function unique_index(entries, label)
    result = Dict{String,Any}()
    for entry in entries
        id = String(entry["id"])
        validate_id(id, "$label.id")
        haskey(result, id) && fail("duplicate $label ID: $id")
        result[id] = entry
    end
    return result
end

function product_bounded(values, limit, label)
    total = 1
    for value in values
        value > 0 || fail("$label contains nonpositive cardinality")
        total > div(limit, value) && fail("$label exceeds aggregate limit $limit")
        total *= value
    end
    return total
end

function validate_configuration(raw)
    raw["contract_id"] == CONTRACT_ID || fail("configuration contract mismatch")
    raw["contract_version"] == CONTRACT_VERSION ||
        fail("configuration version mismatch")
    raw["initializer_id"] == "neutral-replay-v1" ||
        fail("unknown initializer")
    raw["history_generator_id"] == "world-replay-v1" ||
        fail("unknown history generator")
    raw["action_reconciler_id"] == "plurality-safety-priority-v1" ||
        fail("unknown action reconciler")
    nodes = unique_index(raw["nodes"], "node")
    edges = unique_index(raw["edges"], "edge")
    channels = unique_index(raw["observation_channels"], "observation channel")
    policies = unique_index(raw["policy_families"], "policy family")
    candidates = unique_index(raw["structure_candidates"], "structure candidate")

    node_types = Dict(id => String(entry["type"]) for (id, entry) in nodes)
    node_active = Dict(id => Bool(entry["active"]) for (id, entry) in nodes)
    active_cardinalities =
        Int[entry["cardinality"] for entry in values(nodes) if entry["active"]]
    product_bounded(active_cardinalities, 1_000_000,
        "active joint state space")
    slots = Set{Tuple{String,Int}}()
    for entry in values(nodes)
        key = (String(entry["type"]), Int(entry["slot"]))
        key in slots && fail("duplicate node type/slot: $key")
        push!(slots, key)
    end
    count(==("ProtectorNode"), values(node_types)) <= 8 ||
        fail("more than eight protector nodes")

    edge_triples = Set{Tuple{String,String,String}}()
    for (id, edge) in edges
        from = String(edge["from"])
        to = String(edge["to"])
        haskey(nodes, from) || fail("edge $id has dangling source")
        haskey(nodes, to) || fail("edge $id has dangling target")
        from == to && fail("self edge forbidden: $id")
        edge_type = String(edge["type"])
        source_types, target_types = EDGE_SIGNATURES[edge_type]
        node_types[from] in source_types ||
            fail("edge $id has invalid source type")
        node_types[to] in target_types ||
            fail("edge $id has invalid target type")
        (!node_active[from] || !node_active[to]) &&
            String(edge["state"]) != "inactive" &&
            fail("edge $id touches an inactive node but is not inactive")
        triple = (edge_type, from, to)
        triple in edge_triples && fail("duplicate semantic edge: $triple")
        push!(edge_triples, triple)
    end

    channel_sources = Dict{String,String}()
    channel_families = Dict{String,String}()
    channel_values = Dict{String,Vector{String}}()
    channel_bounds = Dict{String,Tuple{Float64,Float64}}()
    for (id, channel) in channels
        scope = String.(channel["scope"])
        all(haskey(nodes, node) for node in scope) ||
            fail("channel $id has dangling scope")
        all(node_active[node] for node in scope) ||
            fail("channel $id scopes an inactive node")
        channel_sources[id] = String(channel["source"])
        family = String(channel["likelihood_family"])
        channel_families[id] = family
        if family == "gaussian_bounded"
            lower, upper = Float64.(channel["bounds"])
            lower < upper || fail("channel $id has unordered Gaussian bounds")
            channel_bounds[id] = (lower, upper)
        else
            labels = String.(channel["value_labels"])
            if family == "bernoulli"
                length(labels) == 2 || fail("Bernoulli channel $id needs two labels")
            end
            channel_values[id] = labels
        end
    end

    protector_ids = sort!([id for (id, node_type) in node_types
        if node_type == "ProtectorNode" && node_active[id]])
    protector_count = length(protector_ids)
    protector_actions = Dict(id => Set{String}() for id in protector_ids)
    bundle_policy_actors = Set{String}()
    action_union = Set{String}()
    for (id, policy) in policies
        Bool(policy["enabled"]) ||
            fail("policy $id is permanently disabled")
        actors = String.(policy["actor_nodes"])
        all(haskey(nodes, actor) for actor in actors) ||
            fail("policy $id has dangling actor")
        all(node_active[actor] for actor in actors) ||
            fail("policy $id has an inactive actor")
        if protector_count > 0
            all(node_types[actor] == "ProtectorNode" for actor in actors) ||
                fail("policy $id must use only protectors when protectors exist")
        else
            length(actors) == 1 &&
                node_types[only(actors)] == "BundleNode" ||
                fail("policy $id must use exactly one bundle actor")
            push!(bundle_policy_actors, only(actors))
        end
        length(policy["actions"]) == length(unique(policy["actions"])) ||
            fail("policy $id repeats an action")
        actions = String.(policy["actions"])
        union!(action_union, actions)
        for actor in actors
            haskey(protector_actions, actor) &&
                union!(protector_actions[actor], actions)
        end
    end
    if protector_count > 0
        all(!isempty(protector_actions[id]) for id in protector_ids) ||
            fail("every active protector must belong to a policy family")
        product_bounded([length(protector_actions[id]) for id in protector_ids],
            4096, "joint protector policy space")
    else
        length(bundle_policy_actors) == 1 ||
            fail("all policy families must share one Bundle actor")
    end

    all_structure_nodes = Set(id for (id, node_type) in node_types
        if node_type == "StructureNode")
    structure_nodes = Set(id for id in all_structure_nodes if node_active[id])
    isempty(structure_nodes) == isempty(candidates) ||
        fail("active structure nodes and candidates must either both be present or absent")
    edge_order = sort!(collect(keys(edges)))
    patterns = Dict(node => Set{String}() for node in structure_nodes)
    candidate_counts = Dict(node => 0 for node in structure_nodes)
    for (id, candidate) in candidates
        structure_node = String(candidate["structure_node"])
        structure_node in structure_nodes ||
            fail("candidate $id references an inactive or non-StructureNode")
        candidate_counts[structure_node] += 1
        active = Set(String.(candidate["active_edges"]))
        inactive = Set(String.(candidate["inactive_edges"]))
        isempty(intersect(active, inactive)) ||
            fail("candidate $id activates and inactivates the same edge")
        all(haskey(edges, edge) for edge in union(active, inactive)) ||
            fail("candidate $id has dangling edge")
        all(node_active[String(edges[edge]["from"])] &&
            node_active[String(edges[edge]["to"])] for edge in active) ||
            fail("candidate $id activates an edge touching an inactive node")
        pattern = join((edge in active ? "active" :
            edge in inactive ? "inactive" : String(edges[edge]["state"])
            for edge in edge_order), '\0')
        pattern in patterns[structure_node] &&
            fail("candidate $id duplicates a complete edge-state pattern")
        push!(patterns[structure_node], pattern)
    end
    for structure_node in structure_nodes
        candidate_counts[structure_node] == Int(nodes[structure_node]["cardinality"]) ||
            fail("StructureNode $structure_node cardinality/candidate mismatch")
    end
    joint_action_labels = Set{String}()
    if isempty(protector_ids)
        union!(joint_action_labels, action_union)
    else
        function enumerate_joint(prefix, index)
            if index > length(protector_ids)
                push!(joint_action_labels, join(prefix, ";"))
                return
            end
            protector = protector_ids[index]
            for action in sort!(collect(protector_actions[protector]))
                enumerate_joint(vcat(prefix, ["$protector=$action"]), index + 1)
            end
        end
        enumerate_joint(String[], 1)
    end
    return (
        id = String(raw["configuration_id"]),
        nodes = nodes,
        node_types = node_types,
        node_active = node_active,
        edges = edges,
        channels = channels,
        channel_sources = channel_sources,
        channel_families = channel_families,
        channel_values = channel_values,
        channel_bounds = channel_bounds,
        policies = policies,
        action_union = action_union,
        joint_action_labels = joint_action_labels,
        candidates = candidates,
    )
end

function available_joint_action_labels(configuration,
        disabled_actions::Set{String})
    return Set(label for label in configuration.joint_action_labels
        if all(!(last(split(assignment, '=')) in disabled_actions)
            for assignment in split(label, ';')))
end

function require_joint_action_support(configuration,
        disabled_actions::Set{String})
    support = available_joint_action_labels(configuration, disabled_actions)
    isempty(support) &&
        fail("architecture_failure:empty-policy-support")
    return support
end

function reconcile_joint_action(label::String, configuration)
    label in configuration.joint_action_labels ||
        fail("cannot reconcile unknown joint action label")
    if !occursin('=', label)
        return label
    end
    counts = Dict(action => 0 for action in ACTION_PRIORITY)
    for assignment in split(label, ';')
        fields = split(assignment, '=')
        length(fields) == 2 || fail("malformed joint action label")
        action = String(fields[2])
        haskey(counts, action) || fail("joint label has unknown action")
        counts[action] += 1
    end
    highest = maximum(values(counts))
    highest > 0 || fail("joint label contains no actions")
    return first(action for action in ACTION_PRIORITY
        if counts[action] == highest)
end

function distribution_values(distribution)
    return haskey(distribution, "values") ? String.(distribution["values"]) : String[]
end

function validate_probability_vector(probabilities, label)
    all(value -> value isa Number && isfinite(Float64(value)) &&
        0 <= value <= 1, probabilities) ||
        fail("$label has invalid probability")
    isapprox(sum(probabilities), 1.0; atol = 1e-10) ||
        fail("$label does not sum to one")
end

function validate_distributions(entries)
    distributions = unique_index(entries, "distribution")
    for (id, distribution) in distributions
        family = String(distribution["family"])
        if family == "uniform" || family == "integer_uniform"
            distribution["lower"] <= distribution["upper"] ||
                fail("distribution $id has unordered bounds")
        elseif family == "categorical"
            length(distribution["values"]) == length(distribution["probabilities"]) ||
                fail("distribution $id value/probability length mismatch")
            validate_probability_vector(distribution["probabilities"],
                "distribution $id")
        elseif family == "transition_matrix"
            values = distribution["values"]
            matrix = distribution["matrix"]
            length(matrix) == length(values) ||
                fail("distribution $id matrix row mismatch")
            for (row_index, row) in enumerate(matrix)
                length(row) == length(values) ||
                    fail("distribution $id row $row_index width mismatch")
                validate_probability_vector(row, "distribution $id row $row_index")
            end
        end
    end
    return distributions
end

function require_distribution(distributions, id, family, values = nothing)
    haskey(distributions, id) || fail("dangling distribution: $id")
    distribution = distributions[id]
    String(distribution["family"]) in family ||
        fail("distribution $id has incompatible family")
    if values !== nothing
        distribution_values(distribution) == values ||
            fail("distribution $id has incompatible values")
    end
    return distribution
end

function validate_world(raw, configuration)
    raw["contract_id"] == CONTRACT_ID || fail("world contract mismatch")
    raw["contract_version"] == CONTRACT_VERSION || fail("world version mismatch")
    raw["history_generator_id"] == "world-replay-v1" ||
        fail("world history generator mismatch")
    raw["seed_namespace"] == raw["world_id"] ||
        fail("seed_namespace must equal world_id")
    episode_length = Int(raw["episode_length"])
    Int(raw["horizon"]) % episode_length == 0 ||
        fail("horizon must be divisible by episode_length")
    Int(raw["development_horizon"]) % episode_length == 0 ||
        fail("development_horizon must be divisible by episode_length")
    factors = unique_index(raw["latent_factors"], "latent factor")
    factor_values = Dict{String,Vector{String}}()
    factor_cardinality = Dict{String,Int}()
    for (id, factor) in factors
        values = String.(factor["values"])
        length(values) == factor["cardinality"] ||
            fail("factor $id cardinality/value mismatch")
        factor_values[id] = values
        factor_cardinality[id] = Int(factor["cardinality"])
    end
    distributions = validate_distributions(raw["distributions"])
    for (id, factor) in factors
        require_distribution(distributions,
            String(factor["initial_distribution_id"]), Set(["categorical"]),
            factor_values[id])
    end

    processes = unique_index(raw["processes"], "process")
    process_targets = Set{String}()
    for (id, process) in processes
        target = String(process["target_factor"])
        haskey(factors, target) || fail("process $id has dangling target")
        target in process_targets &&
            fail("multiple processes target factor $target")
        push!(process_targets, target)
        target_values = factor_values[target]
        process_type = String(process["type"])
        if process_type == "iid"
            require_distribution(distributions, String(process["distribution_id"]),
                Set(["categorical"]), target_values)
        elseif process_type in ("markov", "drift")
            require_distribution(distributions,
                String(process["transition_distribution_id"]),
                Set(["transition_matrix"]), target_values)
        elseif process_type == "change_point"
            for key in ("before_transition_id", "after_transition_id")
                require_distribution(distributions, String(process[key]),
                    Set(["transition_matrix"]), target_values)
            end
            change = require_distribution(distributions,
                String(process["change_time_distribution_id"]),
                Set(["fixed", "integer_uniform"]))
            String(change["sampling_scope"]) == "world" ||
                fail("process $id change time must have world scope")
            if change["family"] == "fixed"
                0 <= change["value"] < raw["horizon"] ||
                    fail("process $id change time outside horizon")
            else
                0 <= change["lower"] <= change["upper"] < raw["horizon"] ||
                    fail("process $id change range outside horizon")
            end
        elseif process_type == "action_contingent"
            String(process["action"]) in configuration.action_union ||
                fail("process $id references unavailable action")
            for key in ("baseline_transition_id", "action_transition_id")
                require_distribution(distributions, String(process[key]),
                    Set(["transition_matrix"]), target_values)
            end
        elseif process_type == "coupled_latent"
            sources = String.(process["source_factors"])
            all(haskey(factors, source) for source in sources) ||
                fail("process $id has dangling source factor")
            configurations = product_bounded(
                [factor_cardinality[source] for source in sources], 625,
                "process $id parent configurations")
            length(process["conditional_transition_ids"]) == configurations ||
                fail("process $id conditional table length mismatch")
            for distribution_id in process["conditional_transition_ids"]
                require_distribution(distributions, String(distribution_id),
                    Set(["transition_matrix"]), target_values)
            end
        end
    end

    emissions = unique_index(raw["emissions"], "emission")
    for (id, emission) in emissions
        sources = String.(emission["source_factors"])
        all(haskey(factors, source) for source in sources) ||
            fail("emission $id has dangling source factor")
        masked = Set(String.(emission["masked_scope"]))
        issubset(masked, Set(sources)) ||
            fail("emission $id masked scope is not a source subset")
        configurations = product_bounded(
            [factor_cardinality[source] for source in sources], 625,
            "emission $id parent configurations")
        channel = String(emission["channel_id"])
        haskey(configuration.channels, channel) ||
            fail("emission $id has dangling channel")
        family = String(emission["likelihood_family"])
        configuration.channel_families[channel] == family ||
            fail("emission $id likelihood does not match channel")
        require_distribution(distributions,
            String(emission["reliability_distribution_id"]), Set(["beta"]))
        if family == "gaussian_bounded"
            length(emission["mean_by_configuration"]) == configurations ||
                fail("emission $id mean table length mismatch")
            lower, upper = configuration.channel_bounds[channel]
            all(value -> lower <= value <= upper,
                emission["mean_by_configuration"]) ||
                fail("emission $id mean outside channel bounds")
            noise = require_distribution(distributions,
                String(emission["noise_scale_distribution_id"]),
                Set(["fixed", "uniform"]))
            if noise["family"] == "fixed"
                noise["value"] > 0 || fail("emission $id has nonpositive noise")
            else
                noise["lower"] > 0 || fail("emission $id has nonpositive noise")
            end
        else
            length(emission["conditional_distribution_ids"]) == configurations ||
                fail("emission $id conditional table length mismatch")
            labels = configuration.channel_values[channel]
            for distribution_id in emission["conditional_distribution_ids"]
                require_distribution(distributions, String(distribution_id),
                    Set(["categorical"]), labels)
            end
        end
    end

    development_ids = Set(String.(raw["development_emission_ids"]))
    all(haskey(emissions, id) for id in development_ids) ||
        fail("development_emission_ids contains a dangling emission")
    (raw["development_horizon"] == 0) == isempty(development_ids) ||
        fail("development horizon/emission declarations disagree")

    outcomes = unique_index(raw["outcomes"], "world outcome")
    action_outcomes = Dict{String,Any}()
    hazard_outcome = nothing
    for (id, outcome) in outcomes
        sources = String.(outcome["source_factors"])
        all(haskey(factors, source) for source in sources) ||
            fail("outcome $id has a dangling source factor")
        configurations = product_bounded(
            [factor_cardinality[source] for source in sources], 625,
            "outcome $id parent configurations")
        if String(outcome["type"]) == "action_outcome"
            action = String(outcome["action"])
            action in configuration.action_union ||
                fail("outcome $id references unavailable action")
            haskey(action_outcomes, action) &&
                fail("multiple outcome mappings for action $action")
            length(outcome["success_probabilities"]) == configurations ||
                fail("outcome $id success table length mismatch")
            length(outcome["exposure_values"]) == configurations ||
                fail("outcome $id exposure table length mismatch")
            all(value -> value isa Number && isfinite(Float64(value)) &&
                0 <= value <= 1, outcome["success_probabilities"]) ||
                fail("outcome $id has invalid success probability")
            all(value -> value isa Number && isfinite(Float64(value)) &&
                value >= 0, outcome["exposure_values"]) ||
                fail("outcome $id has invalid exposure")
            action_outcomes[action] = outcome
        else
            hazard_outcome === nothing ||
                fail("world declares multiple hazard outcomes")
            length(outcome["potential_probabilities"]) == configurations ||
                fail("outcome $id potential-hazard table length mismatch")
            all(value -> value isa Number && isfinite(Float64(value)) &&
                0 <= value <= 1, outcome["potential_probabilities"]) ||
                fail("outcome $id has invalid hazard probability")
            all(String(action) in configuration.action_union
                for action in outcome["mitigating_actions"]) ||
                fail("outcome $id has unavailable mitigating action")
            hazard_outcome = outcome
        end
    end

    contingencies = unique_index(raw["contingencies"], "world contingency")
    contingent_processes = Set{String}()
    for (id, contingency) in contingencies
        target_id = String(contingency["target_process"])
        haskey(processes, target_id) ||
            fail("contingency $id has dangling process")
        process = processes[target_id]
        String(process["type"]) == "action_contingent" ||
            fail("contingency $id must target an action_contingent process")
        action = String(contingency["action"])
        action in configuration.action_union ||
            fail("contingency $id references unavailable action")
        action == String(process["action"]) ||
            fail("contingency $id action does not match its process")
        String(contingency["effect"]) == "activate_action_transition" ||
            fail("contingency $id has unknown effect")
        target_id in contingent_processes &&
            fail("multiple contingencies target process $target_id")
        push!(contingent_processes, target_id)
    end
    return (
        id = String(raw["world_id"]),
        horizon = Int(raw["horizon"]),
        development_horizon = Int(raw["development_horizon"]),
        episode_length = episode_length,
        factors = factors,
        factor_values = factor_values,
        factor_cardinality = factor_cardinality,
        distributions = distributions,
        processes = processes,
        process_by_factor = Dict(String(process["target_factor"]) => process
            for process in values(processes)),
        emissions = emissions,
        outcomes = outcomes,
        action_outcomes = action_outcomes,
        hazard_outcome = hazard_outcome,
        contingencies = contingencies,
    )
end

function resolve_trace_path(path::String, configuration, world;
        wildcard_allowed = true)
    occursin("..", path) && fail("malformed trace path: $path")
    parts = split(path, '.')
    wildcard_allowed || "*" in parts && fail("wildcard forbidden here: $path")
    root = parts[1]
    if root == "run"
        path in ("run.seed", "run.arm", "run.time", "run.episode",
            "run.row_index", "run.row_kind", "run.event_index",
            "run.event_kind", "run.event_executed", "run.genome_id",
            "run.event_id", "run.stopped", "run.stop_reason") ||
            fail("unknown trace path: $path")
    elseif root == "action"
        path in ("action.selected", "action.success",
            "action.delivered_exposure") || fail("unknown trace path: $path")
        if path in ("action.success", "action.delivered_exposure")
            Set(keys(world.action_outcomes)) == configuration.action_union ||
                fail("$path requires outcome mappings for every action")
        end
    elseif root == "observation"
        if length(parts) == 2
            parts[2] in ("source", "scope_size", "is_imaginal",
                "delivered_log_likelihood", "marginal_equivalence_error") ||
                fail("unknown observation path: $path")
        elseif length(parts) == 3 && parts[2] == "log_likelihood"
            parts[3] == "*" || haskey(configuration.candidates, parts[3]) ||
                fail("unknown likelihood candidate: $path")
        else
            fail("unknown observation path: $path")
        end
    elseif root == "state"
        length(parts) >= 4 || fail("incomplete state path: $path")
        family, node = parts[2], parts[3]
        haskey(configuration.nodes, node) || fail("unknown state node: $path")
        expected_type = Dict(
            "bundle" => "BundleNode", "context" => "ContextNode",
            "cue" => "CueNode", "local_precision" => "LocalPrecisionNode",
            "global_precision" => "GlobalPrecisionNode",
            "protector" => "ProtectorNode", "partner" => "PartnerNode",
            "access" => "AccessNode", "episode" => "EpisodeNode",
            "structure" => "StructureNode",
        )
        haskey(expected_type, family) || fail("unknown state family: $path")
        configuration.node_types[node] == expected_type[family] ||
            fail("state path node type mismatch: $path")
        field = parts[4]
        if family == "context" && field == "posterior"
            length(parts) == 6 || fail("context posterior path needs factor/value")
            factor, value = parts[5], parts[6]
            haskey(world.factors, factor) || fail("unknown context factor: $path")
            value == "*" || value in world.factor_values[factor] ||
                fail("unknown context value: $path")
        elseif family == "structure" && field in
                ("log_evidence", "complexity", "selected")
            length(parts) == 5 || fail("structure candidate path malformed")
            candidate = parts[5]
            candidate == "*" ||
                (haskey(configuration.candidates, candidate) &&
                String(configuration.candidates[candidate]["structure_node"]) == node) ||
                fail("unknown structure candidate: $path")
        else
            length(parts) == 4 || fail("state path has extra segments: $path")
            allowed = Dict(
                "bundle" => Set(["activation_probability", "root_probability",
                    "expected_outcome", "mandate_probability"]),
                "context" => Set(["transition_entropy"]),
                "cue" => Set(["meaning_probability", "root_association"]),
                "local_precision" => Set(["mean", "calibration_error"]),
                "global_precision" => Set(["part", "context", "interoception",
                    "relationship", "policy", "depth"]),
                "protector" => Set(["permission_probability",
                    "suppression_probability", "forecast_outcome",
                    "forecast_coprotection", "forecast_partner_type"]),
                "partner" => Set(["trust_probability", "regulation_probability"]),
                "access" => Set(["probability"]),
                "episode" => Set(["joint_probability"]),
                "structure" => Set(["first_stable_reduced_win",
                    "reversals_to_full"]),
            )
            field in allowed[family] || fail("unknown state field: $path")
        end
    elseif root == "policy"
        if length(parts) == 2
            path == "policy.access_probability" ||
                fail("unknown policy path: $path")
        elseif parts[2] == "protector" && length(parts) == 4
            haskey(configuration.nodes, parts[3]) &&
                configuration.node_types[parts[3]] == "ProtectorNode" ||
                fail("unknown policy protector: $path")
            parts[4] == "permission_probability" ||
                fail("unknown protector policy field: $path")
        elseif parts[2] == "joint" && length(parts) == 4
            parts[3] in ("posterior", "expected_free_energy") ||
                fail("unknown joint policy field: $path")
            parts[4] == "*" ||
                parts[4] in configuration.joint_action_labels ||
                fail("unknown canonical joint action label: $path")
        else
            fail("unknown policy path: $path")
        end
    elseif root == "learning"
        if length(parts) == 4 && parts[2] == "edge"
            haskey(configuration.edges, parts[3]) ||
                fail("unknown learning edge: $path")
            parts[4] == "strength" || fail("unknown learning edge field")
        elseif length(parts) == 4 && parts[2] == "parameter"
            haskey(world.factors, parts[3]) ||
                fail("unknown learning factor: $path")
            parts[4] == "value" || fail("unknown learning parameter field")
        else
            fail("unknown learning path: $path")
        end
    elseif root == "provenance"
        path in ("provenance.update_function", "provenance.edge_id",
            "provenance.observation_event_id", "provenance.model_candidate",
            "provenance.rng_namespace") || fail("unknown provenance path: $path")
    elseif root == "world"
        if length(parts) == 3 && parts[2] == "truth"
            haskey(world.factors, parts[3]) || fail("unknown truth factor: $path")
        elseif length(parts) == 4 && parts[2] == "process"
            haskey(world.process_by_factor, parts[3]) ||
                fail("unknown process factor: $path")
            parts[4] == "switch" || fail("unknown process truth field")
            String(world.process_by_factor[parts[3]]["type"]) == "change_point" ||
                fail("process switch requires a change_point process")
        elseif path in ("world.potential_hazard", "world.realized_hazard")
            world.hazard_outcome !== nothing ||
                fail("hazard trace requires a hazard outcome mapping")
        else
            fail("unknown world path: $path")
        end
    elseif root == "derived"
        parts[2] in ("first_crossing_time", "non_crossing",
            "paired_difference", "slope", "classification_correct",
            "budget_relative_error") || fail("unknown derived path: $path")
    else
        fail("unknown trace root: $path")
    end
    return true
end

function path_references_inactive_node(path::String, configuration)
    parts = split(path, '.')
    if parts[1] == "state" && length(parts) >= 3
        return haskey(configuration.node_active, parts[3]) &&
            !configuration.node_active[parts[3]]
    elseif parts[1] == "policy" && length(parts) >= 3 &&
            parts[2] == "protector"
        return haskey(configuration.node_active, parts[3]) &&
            !configuration.node_active[parts[3]]
    elseif parts[1] == "learning" && length(parts) == 4 &&
            parts[2] == "edge" && haskey(configuration.edges, parts[3])
        edge = configuration.edges[parts[3]]
        return !configuration.node_active[String(edge["from"])] ||
            !configuration.node_active[String(edge["to"])]
    end
    return false
end

function path_matches(requested::String, dependency::String)
    requested == dependency && return true
    req = split(requested, '.')
    dep = split(dependency, '.')
    length(req) == length(dep) || return false
    return all(left == "*" || left == right for (left, right) in zip(req, dep))
end

function trigger_valid(trigger, configuration, world)
    path = String(trigger["predicate"]["field"])
    resolve_trace_path(path, configuration, world; wildcard_allowed = false)
    path_references_inactive_node(path, configuration) &&
        fail("protocol trigger reads an inactive-node path: $path")
    validate_predicate(trigger["predicate"], configuration, world)
    kind = String(trigger["kind"])
    if kind == "external_proxy"
        path in EXTERNAL_TRIGGER_PATHS ||
            fail("external_proxy trigger uses ineligible path: $path")
    else
        (startswith(path, "state.") || startswith(path, "policy.")) ||
            fail("latent_intervention trigger uses ineligible path: $path")
        occursin("structure.", path) &&
            fail("structure evidence is forbidden in protocol triggers")
    end
end

function validate_budget_pairs(rule, valid_arms::Set{String})
    declared_arms = Set(String.(rule["arms"]))
    all(arm in valid_arms for arm in declared_arms) ||
        fail("budget rule $(rule["id"]) has dangling arm")
    pairs = Set{Tuple{String,String}}()
    unordered = Set{Tuple{String,String}}()
    endpoints = Set{String}()
    for pair in rule["arm_pairs"]
        left, right = String(pair["left"]), String(pair["right"])
        left in declared_arms && right in declared_arms ||
            fail("budget rule $(rule["id"]) pair leaves declared arms")
        left != right || fail("budget rule $(rule["id"]) has a self pair")
        key = (left, right)
        key in pairs && fail("budget rule $(rule["id"]) repeats a pair")
        push!(pairs, key)
        canonical = left < right ? (left, right) : (right, left)
        canonical in unordered &&
            fail("budget rule $(rule["id"]) repeats a reversed pair")
        push!(unordered, canonical)
        union!(endpoints, (left, right))
    end
    endpoints == declared_arms ||
        fail("budget rule $(rule["id"]) does not cover every arm")
    return pairs
end

function validate_protocol(raw, configuration, world)
    raw["contract_id"] == CONTRACT_ID || fail("protocol contract mismatch")
    raw["contract_version"] == CONTRACT_VERSION ||
        fail("protocol version mismatch")
    interventions = unique_index(raw["interventions"], "intervention")
    for (id, intervention) in interventions
        kind = String(intervention["target_kind"])
        target = String(intervention["target_id"])
        valid = kind == "edge" ? haskey(configuration.edges, target) :
            kind == "observation_channel" ? haskey(configuration.channels, target) :
            kind == "policy_action" ? target in configuration.action_union :
            haskey(world.contingencies, target)
        valid || fail("intervention $id has dangling target")
    end
    stopping_rules = unique_index(raw["stopping_rules"], "stopping rule")
    for (id, rule) in stopping_rules
        rule["max_time"] < world.horizon ||
            fail("stopping rule $id exceeds horizon")
        if rule["kind"] == "trace_crossing"
            path = String(rule["field"])
            resolve_trace_path(path, configuration, world; wildcard_allowed = false)
            path_references_inactive_node(path, configuration) &&
                fail("stopping rule $id reads an inactive-node path")
            trace_value_type(path) == :number ||
                fail("stopping rule $id field must be numeric")
            startswith(path, "world.") &&
                fail("stopping rule $id reads world truth")
            startswith(path, "derived.") &&
                fail("stopping rule $id reads derived output")
        end
    end

    arms = unique_index(raw["arms"], "arm")
    event_ids = Set{String}()
    latent_trigger_arms = Set{String}()
    arm_interventions = Dict(id => Set{String}() for id in keys(arms))
    used_interventions = Set{String}()
    used_stopping_rules = Set{String}()
    total_expanded_events = 0
    for (arm_id, arm) in arms
        arm["world_id"] == world.id || fail("arm $arm_id has wrong world")
        last_time = -1
        expanded = 0
        for event in arm["events"]
            event_id = String(event["id"])
            event_id in event_ids && fail("duplicate event ID: $event_id")
            push!(event_ids, event_id)
            event["time"] < world.horizon ||
                fail("event $event_id is outside executable time")
            event["time"] >= last_time || fail("arm $arm_id events are unordered")
            last_time = Int(event["time"])
            kind = String(event["kind"])
            if kind in ("observe", "probe")
                channel = String(event["channel_id"])
                emission = String(event["emission_id"])
                haskey(configuration.channels, channel) ||
                    fail("event $event_id has dangling channel")
                haskey(world.emissions, emission) ||
                    fail("event $event_id has dangling emission")
                world.emissions[emission]["channel_id"] == channel ||
                    fail("event $event_id channel/emission mismatch")
                configuration.channel_sources[channel] == event["source"] ||
                    fail("event $event_id source/channel mismatch")
                final_time = event["time"] +
                    (event["repeat"] - 1) * event["interval"]
                final_time < world.horizon ||
                    fail("event $event_id expands past horizon")
                expanded += Int(event["repeat"])
            elseif kind == "imaginal"
                channel = String(event["channel_id"])
                haskey(configuration.channels, channel) ||
                    fail("event $event_id has dangling channel")
                configuration.channel_sources[channel] == "imaginal" ||
                    fail("event $event_id must use an imaginal channel")
                String(event["generator_id"]) == "posterior-predictive-mode-v1" ||
                    fail("event $event_id has unknown imaginal generator")
                final_time = event["time"] +
                    (event["repeat"] - 1) * event["interval"]
                final_time < world.horizon ||
                    fail("event $event_id expands past horizon")
                expanded += Int(event["repeat"])
            elseif kind == "intervene"
                intervention_id = String(event["intervention_id"])
                haskey(interventions, intervention_id) ||
                    fail("event $event_id has dangling intervention")
                push!(arm_interventions[arm_id], intervention_id)
                push!(used_interventions, intervention_id)
                expanded += 1
            elseif kind == "stop_check"
                stopping_rule_id = String(event["stopping_rule_id"])
                haskey(stopping_rules, stopping_rule_id) ||
                    fail("event $event_id has dangling stopping rule")
                push!(used_stopping_rules, stopping_rule_id)
                expanded += 1
            end
            if haskey(event, "trigger")
                trigger_valid(event["trigger"], configuration, world)
                event["trigger"]["kind"] == "latent_intervention" &&
                    push!(latent_trigger_arms, arm_id)
            end
        end
        expanded <= 4096 || fail("arm $arm_id exceeds 4096 expanded events")
        total_expanded_events += expanded
    end
    used_interventions == Set(keys(interventions)) ||
        fail("protocol declares an unscheduled intervention")
    used_stopping_rules == Set(keys(stopping_rules)) ||
        fail("protocol declares an unchecked stopping rule")

    paired_streams = unique_index(raw["paired_streams"], "paired stream")
    component_indexes = Dict(
        "latent_factor" => world.factors,
        "process" => world.processes,
        "emission" => world.emissions,
        "distribution" => world.distributions,
        "outcome" => world.outcomes,
        "world_contingency" => world.contingencies,
    )
    for (id, stream) in paired_streams
        all(haskey(arms, String(arm)) for arm in stream["arms"]) ||
            fail("paired stream $id has dangling arm")
        seen = Set{Tuple{String,String}}()
        for component in stream["components"]
            key = (String(component["kind"]), String(component["id"]))
            key in seen && fail("paired stream $id repeats component $key")
            push!(seen, key)
            haskey(component_indexes[key[1]], key[2]) ||
                fail("paired stream $id has dangling typed component $key")
        end
    end

    budgets = unique_index(raw["evidence_budget_rules"], "evidence budget rule")
    budget_pairs = Dict{String,Set{Tuple{String,String}}}()
    for (id, rule) in budgets
        budget_pairs[id] = validate_budget_pairs(rule, Set(keys(arms)))
        all(haskey(configuration.nodes, String(node)) for node in rule["scope"]) ||
            fail("budget rule $id has dangling scope")
        all(configuration.node_active[String(node)] for node in rule["scope"]) ||
            fail("budget rule $id scopes an inactive node")
    end

    controls = unique_index(raw["controls"], "control")
    for (id, control) in controls
        treatment_arms = Set(String.(control["treatment_arms"]))
        control_arms = Set(String.(control["control_arms"]))
        isempty(intersect(treatment_arms, control_arms)) ||
            fail("control $id repeats an arm on both sides")
        declared_arms = union(treatment_arms, control_arms)
        all(haskey(arms, arm) for arm in declared_arms) ||
            fail("control $id has dangling arm")
        all(haskey(interventions, String(item)) for item in
            control["intervention_ids"]) ||
            fail("control $id has dangling intervention")
        all(haskey(budgets, String(item)) for item in control["budget_rule_ids"]) ||
            fail("control $id has dangling budget rule")
        kind = String(control["kind"])
        kind == "matched_capacity" && isempty(control["intervention_ids"]) &&
            fail("matched-capacity control $id has no intervention")
        kind == "matched_budget" && isempty(control["budget_rule_ids"]) &&
            fail("matched-budget control $id has no budget rule")
        kind == "external_proxy" && isempty(control["intervention_ids"]) &&
            fail("external-proxy control $id has no intervention")
        kind in ("external_proxy", "matched_capacity") &&
            !isempty(control["budget_rule_ids"]) &&
            fail("$kind control $id may not name a budget rule")
        kind == "matched_budget" && !isempty(control["intervention_ids"]) &&
            fail("matched-budget control $id may not name an intervention")
        if kind == "impossibility"
            isempty(control["intervention_ids"]) &&
                isempty(control["budget_rule_ids"]) ||
                fail("impossibility control $id may name no apparatus")
            length(strip(String(get(control, "explanation", "")))) >= 20 ||
                fail("impossibility control $id needs an explanation")
        elseif haskey(control, "explanation")
            fail("only impossibility controls may have an explanation")
        end
        for intervention_id in String.(control["intervention_ids"])
            occurring = Set(arm for arm in declared_arms
                if intervention_id in arm_interventions[arm])
            isempty(occurring) &&
                fail("control $id names an intervention absent from its arms")
            occurring != declared_arms ||
                fail("control $id intervention occurs identically on both sides")
        end
        for budget_id in String.(control["budget_rule_ids"])
            budget_arms = Set(String.(budgets[budget_id]["arms"]))
            budget_arms == declared_arms ||
                fail("control $id budget arms do not match its contrast")
            all(left in treatment_arms && right in control_arms
                for (left, right) in budget_pairs[budget_id]) ||
                fail("control $id budget pairs must orient treatment to control")
        end
    end
    used_budget_rules = Set(String(budget_id)
        for control in values(controls)
        for budget_id in control["budget_rule_ids"])
    used_budget_rules == Set(keys(budgets)) ||
        fail("protocol declares an uncontrolled evidence budget")
    for arm_id in latent_trigger_arms
        any(control["kind"] == "external_proxy" &&
            arm_id in control["treatment_arms"] for control in values(controls)) ||
            fail("latent intervention in $arm_id lacks external/proxy control")
    end

    requested = String.(raw["requested_trace_fields"])
    foreach(path -> resolve_trace_path(path, configuration, world), requested)
    length(unique(requested)) == length(requested) ||
        fail("duplicate requested trace path")
    trace_rows = world.horizon * length(arms) + total_expanded_events
    raw_cells = trace_rows * length(requested)
    raw_cells <= 1_000_000 ||
        fail("declared trace cells per seed exceed 1,000,000")
    return (
        id = String(raw["protocol_id"]),
        arms = arms,
        arm_ids = Set(keys(arms)),
        interventions = interventions,
        stopping_rules = stopping_rules,
        budgets = budgets,
        budget_pairs = budget_pairs,
        controls = controls,
        arm_interventions = arm_interventions,
        requested = requested,
    )
end

function expression_dependencies(expression, protocol, configuration, world;
        parent_op = nothing, counter = Ref(0), depth = 1)
    counter[] += 1
    counter[] <= 256 || fail("analysis AST exceeds 256 nodes")
    depth <= 32 || fail("analysis AST exceeds depth 32")
    op = String(expression["op"])
    dependencies = Set{String}()
    if op == "field"
        path = String(expression["path"])
        startswith(path, "derived.") &&
            fail("derived fields cannot be analysis sources")
        resolve_trace_path(path, configuration, world)
        occursin("*", path) && !(parent_op in
            ("mean", "sum", "min", "max", "count", "rate")) &&
            fail("wildcard field lacks direct aggregation parent: $path")
        push!(dependencies, path)
    end
    for key in ("source", "arg", "left", "right")
        if haskey(expression, key)
            union!(dependencies, expression_dependencies(expression[key],
                protocol, configuration, world; parent_op = op,
                counter = counter, depth = depth + 1))
        end
    end
    if haskey(expression, "value") && expression["value"] isa AbstractDict
        union!(dependencies, expression_dependencies(expression["value"],
            protocol, configuration, world; parent_op = op,
            counter = counter, depth = depth + 1))
    end
    for key in ("time_path", "prediction_path", "truth_path", "strata_path",
            "evidence_path", "selected_path")
        if haskey(expression, key)
            path = String(expression[key])
            startswith(path, "derived.") &&
                fail("derived fields cannot be analysis sources")
            resolve_trace_path(path, configuration, world)
            if key in ("evidence_path", "selected_path")
                occursin("*", path) ||
                    fail("$key must end in a candidate wildcard")
            end
            push!(dependencies, path)
        end
    end
    if haskey(expression, "predicates")
        for predicate in expression["predicates"]
            path = String(predicate["field"])
            startswith(path, "derived.") &&
                fail("derived fields cannot be analysis predicates")
            resolve_trace_path(path, configuration, world;
                wildcard_allowed = false)
            validate_predicate(predicate, configuration, world)
            push!(dependencies, path)
        end
    end
    for key in ("treatment", "control", "treatment_present",
            "treatment_absent", "control_present", "control_absent")
        haskey(expression, key) &&
            String(expression[key]) in protocol.arm_ids ||
            !haskey(expression, key) ||
            fail("analysis references unknown arm")
    end
    if op == "budget_relative_error"
        budget_id = String(expression["evidence_budget_rule_id"])
        haskey(protocol.budgets, budget_id) ||
            fail("analysis references unknown evidence budget rule")
        union!(dependencies, Set(["run.seed", "run.arm",
            "observation.delivered_log_likelihood"]))
    end
    return dependencies
end

function trace_value_type(path::String)
    if path in ("run.arm", "run.row_kind", "run.event_kind",
            "run.genome_id", "run.event_id", "run.stop_reason",
            "action.selected", "observation.source",
            "provenance.update_function", "provenance.edge_id",
            "provenance.observation_event_id", "provenance.model_candidate",
            "provenance.rng_namespace") || startswith(path, "world.truth.")
        return :string
    elseif path in ("run.stopped", "run.event_executed", "action.success",
            "observation.is_imaginal", "world.potential_hazard",
            "world.realized_hazard", "derived.non_crossing",
            "derived.classification_correct") ||
            occursin(".selected.", path) ||
            (startswith(path, "world.process.") && endswith(path, ".switch"))
        return :bool
    end
    return :number
end

function trace_row_domain(path::String)
    path in ("run.seed", "run.arm", "run.time", "run.episode",
            "run.row_index", "run.row_kind", "run.genome_id") &&
        return :all_rows
    path in ("run.stopped", "run.stop_reason") && return :stop_or_tick
    (path in ("run.event_index", "run.event_kind", "run.event_executed",
            "run.event_id") || startswith(path, "observation.") ||
            startswith(path, "provenance.")) && return :event
    return :tick
end

function validate_unit_row_domains(unit::String, dependencies, estimand_id)
    if unit == "event"
        tick_dependencies = Set(path for path in dependencies
            if trace_row_domain(path) == :tick)
        isempty(tick_dependencies) ||
            fail("event-unit estimand $estimand_id reads tick-only fields")
    end
    return true
end

function scalar_type(value)
    value isa Bool && return :bool
    value isa Number && return :number
    value isa AbstractString && return :string
    fail("predicate value is not scalar")
end

function validate_predicate(predicate, configuration, world)
    path = String(predicate["field"])
    resolve_trace_path(path, configuration, world; wildcard_allowed = false)
    field_type = trace_value_type(path)
    comparator = String(predicate["comparator"])
    if comparator == "finite"
        field_type == :number ||
            fail("finite predicate requires a numeric field: $path")
        haskey(predicate, "value") &&
            fail("finite predicate must omit value")
    elseif comparator in ("lt", "le", "gt", "ge")
        field_type == :number ||
            fail("$comparator predicate requires a numeric field: $path")
        haskey(predicate, "value") &&
            scalar_type(predicate["value"]) == :number ||
            fail("$comparator predicate requires a numeric value")
    elseif comparator in ("eq", "ne")
        haskey(predicate, "value") ||
            fail("$comparator predicate requires value")
        scalar_type(predicate["value"]) == field_type ||
            fail("$comparator predicate value type does not match $path")
    elseif comparator == "in"
        haskey(predicate, "value") && predicate["value"] isa AbstractVector &&
            !isempty(predicate["value"]) ||
            fail("in predicate requires a nonempty array")
        all(scalar_type(value) == field_type for value in predicate["value"]) ||
            fail("in predicate values do not match $path")
    else
        fail("unknown predicate comparator: $comparator")
    end
    return true
end

is_series(type) = type in (:series_number, :series_bool, :series_string)
series_type(type) = type == :number ? :series_number :
    type == :bool ? :series_bool : :series_string

function expression_result_type(expression, protocol, configuration, world)
    op = String(expression["op"])
    if op == "literal"
        value = expression["value"]
        return value isa Bool ? :bool : value isa Number ? :number : :string
    elseif op == "field"
        return series_type(trace_value_type(String(expression["path"])))
    elseif op == "where"
        type = expression_result_type(expression["source"], protocol,
            configuration, world)
        is_series(type) || fail("where source must be a trace series")
        return type
    elseif op in ("initial", "terminal", "lag")
        type = expression_result_type(expression["arg"], protocol,
            configuration, world)
        is_series(type) || fail("$op requires a series")
        return type
    elseif op == "first_crossing"
        type = expression_result_type(expression["arg"], protocol,
            configuration, world)
        type == :series_number || fail("first_crossing requires a numeric series")
        return :series_number
    elseif op == "slope"
        type = expression_result_type(expression["arg"], protocol,
            configuration, world)
        type == :series_number || fail("slope requires a numeric series")
        trace_value_type(String(expression["time_path"])) == :number ||
            fail("slope time_path must be numeric")
        return :series_number
    elseif op in ("mean", "sum", "min", "max", "std", "quantile")
        type = expression_result_type(expression["arg"], protocol,
            configuration, world)
        type == :series_number || fail("$op requires a numeric series")
        return :number
    elseif op == "count"
        is_series(expression_result_type(expression["arg"], protocol,
            configuration, world)) || fail("count requires a series")
        return :number
    elseif op == "rate"
        type = expression_result_type(expression["arg"], protocol,
            configuration, world)
        type == :series_bool ||
            fail("rate requires a Boolean series")
        return :number
    elseif op in ("abs", "negate", "log", "exp")
        type = expression_result_type(expression["arg"], protocol,
            configuration, world)
        type in (:number, :series_number) ||
            fail("$op requires numeric input")
        return type
    elseif op in ("add", "subtract", "multiply", "divide", "min2", "max2")
        left = expression_result_type(expression["left"], protocol,
            configuration, world)
        right = expression_result_type(expression["right"], protocol,
            configuration, world)
        left in (:number, :series_number) &&
            right in (:number, :series_number) ||
            fail("$op requires numeric inputs")
        return left == :series_number || right == :series_number ?
            :series_number : :number
    elseif op == "event_precedes"
        String(expression["left"]["op"]) == "first_crossing" &&
            String(expression["right"]["op"]) == "first_crossing" ||
            fail("event_precedes operands must be first_crossing expressions")
        left = expression_result_type(expression["left"], protocol,
            configuration, world)
        right = expression_result_type(expression["right"], protocol,
            configuration, world)
        left == :series_number && right == :series_number ||
            fail("event_precedes requires two crossing-time series")
        return :series_bool
    elseif op in ("arm_difference", "difference_in_differences")
        type = expression_result_type(expression["value"], protocol,
            configuration, world)
        type == :series_number || fail("$op requires a numeric unit series")
        return :series_number
    elseif op == "classification_accuracy"
        prediction_type = trace_value_type(String(expression["prediction_path"]))
        truth_type = trace_value_type(String(expression["truth_path"]))
        prediction_type == truth_type ||
            fail("classification paths have incompatible types")
        return :number
    elseif op == "confusion_matrix"
        prediction_type = trace_value_type(String(expression["prediction_path"]))
        truth_type = trace_value_type(String(expression["truth_path"]))
        prediction_type == truth_type ||
            fail("classification paths have incompatible types")
        return :matrix
    elseif op == "argmax_match"
        evidence = split(String(expression["evidence_path"]), '.')
        selected = split(String(expression["selected_path"]), '.')
        length(evidence) == 5 && length(selected) == 5 &&
            evidence[1] == "state" && selected[1] == "state" &&
            evidence[2] == "structure" && selected[2] == "structure" &&
            evidence[3] == selected[3] &&
            evidence[4] == "log_evidence" &&
            selected[4] == "selected" &&
            evidence[5] == "*" && selected[5] == "*" ||
            fail("argmax_match paths must address one StructureNode")
        return :series_bool
    elseif op == "budget_relative_error"
        return :series_number
    elseif op == "survival_fraction"
        type = expression_result_type(expression["arg"], protocol,
            configuration, world)
        type in (:number, :bool, :series_number, :series_bool) ||
            fail("survival_fraction requires numeric or Boolean input")
        base_type = type in (:number, :series_number) ? :number : :bool
        scalar_type(expression["threshold"]) == base_type ||
            fail("survival_fraction threshold type mismatch")
        base_type == :bool &&
            !(String(expression["comparator"]) in ("eq", "ne")) &&
            fail("Boolean survival_fraction permits only eq/ne")
        return :number
    end
    fail("untyped analysis operator: $op")
end

function expression_contains_op(expression, target::String)
    String(expression["op"]) == target && return true
    for key in ("source", "arg", "left", "right", "value")
        if haskey(expression, key) && expression[key] isa AbstractDict &&
                expression_contains_op(expression[key], target)
            return true
        end
    end
    return false
end

function contrast_specs(expression, result = NamedTuple[])
    op = String(expression["op"])
    if op == "arm_difference"
        push!(result, (
            treatment = Set([String(expression["treatment"])]),
            control = Set([String(expression["control"])]),
        ))
    elseif op == "difference_in_differences"
        push!(result, (
            treatment = Set(String.([
                expression["treatment_present"],
                expression["treatment_absent"],
            ])),
            control = Set(String.([
                expression["control_present"],
                expression["control_absent"],
            ])),
        ))
    end
    for key in ("source", "arg", "left", "right", "value")
        if haskey(expression, key) && expression[key] isa AbstractDict
            contrast_specs(expression[key], result)
        end
    end
    return result
end

function validate_analysis(raw, protocol, configuration, world)
    raw["contract_id"] == CONTRACT_ID || fail("analysis contract mismatch")
    raw["contract_version"] == CONTRACT_VERSION ||
        fail("analysis version mismatch")
    estimands = unique_index(raw["estimands"], "estimand")
    controls_used = Set{String}()
    ast_counter = Ref(0)
    dependencies = Set{String}()
    inactive_audit_dependencies = Set{String}()
    estimand_result_types = Dict{String,Symbol}()
    estimand_final_types = Dict{String,Symbol}()
    for (id, estimand) in estimands
        control_ids = String.(estimand["control_ids"])
        all(haskey(protocol.controls, control) for control in control_ids) ||
            fail("estimand $id references unknown control")
        union!(controls_used, control_ids)
        expression = estimand["expression"]
        raw["unit_of_analysis"] == "event" &&
            (expression_contains_op(expression, "arm_difference") ||
                expression_contains_op(expression, "difference_in_differences")) &&
            fail("event-unit cross-arm contrasts are undefined")
        raw["tie_handling"] == "half" &&
            expression_contains_op(expression, "event_precedes") &&
            fail("event_precedes is incompatible with half tie handling")
        estimand_dependencies = expression_dependencies(expression, protocol,
            configuration, world; counter = ast_counter)
        validate_unit_row_domains(
            String(raw["unit_of_analysis"]), estimand_dependencies, id)
        union!(dependencies, estimand_dependencies)
        inactive_dependencies = Set(path for path in estimand_dependencies
            if path_references_inactive_node(path, configuration))
        if !isempty(inactive_dependencies)
            String(estimand["status"]) == "audit" ||
                fail("estimand $id reads an inactive node but is not audit")
            union!(inactive_audit_dependencies, inactive_dependencies)
        end
        result_type = expression_result_type(expression, protocol,
            configuration, world)
        estimand_result_types[id] = result_type
        aggregation = String(estimand["aggregation"])
        if aggregation == "identity"
            result_type in (:number, :bool, :string) ||
                fail("estimand $id identity requires one scalar result")
            estimand_final_types[id] = result_type
        elseif aggregation in ("mean", "median")
            result_type == :series_number ||
                fail("estimand $id $aggregation requires a numeric unit series")
            estimand_final_types[id] = :number
        elseif aggregation == "rate"
            result_type == :series_bool ||
                fail("estimand $id rate requires a Boolean unit series")
            estimand_final_types[id] = :number
        elseif aggregation == "matrix"
            result_type == :matrix ||
                fail("estimand $id matrix aggregation requires a matrix")
            estimand_final_types[id] = :matrix
        else
            fail("unknown top-level aggregation: $aggregation")
        end
        interval_method = String(estimand["interval"]["method"])
        if interval_method == "exact_binomial"
            result_type == :series_bool &&
                aggregation == "rate" ||
                fail("exact_binomial requires a Boolean unit series and rate")
        elseif interval_method in ("percentile_bootstrap", "basic_bootstrap")
            aggregation in ("mean", "median", "rate") ||
                fail("bootstrap requires mean, median, or rate aggregation")
        end
        specs = contrast_specs(expression)
        for spec in specs
            isempty(control_ids) &&
                fail("treatment estimand $id has no declared control")
            for control_id in control_ids
                control = protocol.controls[control_id]
                Set(String.(control["treatment_arms"])) == spec.treatment &&
                    Set(String.(control["control_arms"])) == spec.control ||
                    fail("estimand $id control $control_id does not match its contrast")
            end
            kinds = Set(String(protocol.controls[control_id]["kind"])
                for control_id in control_ids)
            ("impossibility" in kinds ||
                ("matched_capacity" in kinds && "matched_budget" in kinds)) ||
                fail("estimand $id lacks matched-capacity and matched-budget controls")
        end
    end
    controls_used == Set(keys(protocol.controls)) ||
        fail("protocol declares an unused control")
    for dependency in dependencies
        any(path_matches(requested, dependency)
            for requested in protocol.requested) ||
            fail("analysis dependency is not requested: $dependency")
    end
    for requested in protocol.requested
        if path_references_inactive_node(requested, configuration)
            any(path_matches(requested, dependency)
                for dependency in inactive_audit_dependencies) ||
                fail("inactive-node trace request lacks an audit estimand")
        end
    end
    rules = unique_index(raw["decision_rules"], "decision rule")
    for (id, rule) in rules
        estimand_id = String(rule["estimand_id"])
        haskey(estimands, estimand_id) ||
            fail("decision rule $id has dangling estimand")
        estimand_final_types[estimand_id] == :number ||
            fail("decision rule $id requires a numeric scalar estimand")
        String(rule["interval_requirement"]) != "none" &&
            String(estimands[estimand_id]["interval"]["method"]) == "none" &&
            fail("decision rule $id requires an interval but estimand has none")
        threshold = rule["threshold"]
        threshold isa AbstractVector &&
            threshold[1] >= threshold[2] &&
            fail("decision rule $id has unordered threshold")
    end
    return (estimands = estimands, rules = rules,
        rule_ids = Set(keys(rules)), dependencies = dependencies)
end

function validate_interpretation(path, bundle_id, analysis)
    text = read(path, String)
    startswith(text, "# ") || fail("interpretation lock needs one title")
    contract_line = "Contract: `$(CONTRACT_ID)@$(CONTRACT_VERSION)`"
    occursin(contract_line, text) || fail("interpretation lock contract mismatch")
    occursin("Challenge: `$bundle_id`", text) ||
        fail("interpretation lock challenge mismatch")
    metadata = match(r"(?m)^Decision rules: (.+)$", text)
    metadata === nothing && fail("interpretation lock lacks decision-rule metadata")
    named_rules = Set(String(rule_match.captures[1]) for rule_match in
        eachmatch(r"`([a-z][a-z0-9_-]+)`", metadata.captures[1]))
    named_rules == analysis.rule_ids ||
        fail("interpretation lock decision rules do not match analysis")
    headings = [
        "## Success",
        "## Scientific failure",
        "## Semantic inexpressibility",
    ]
    positions = Int[]
    for heading in headings
        matches = collect(eachmatch(Regex("(?m)^" *
            replace(heading, "#" => "\\#") * "\$"), text))
        length(matches) == 1 || fail("interpretation lock needs exactly one $heading")
        push!(positions, matches[1].offset)
    end
    issorted(positions) || fail("interpretation headings are out of order")
    for index in eachindex(headings)
        start = positions[index] + ncodeunits(headings[index])
        stop = index == length(headings) ? ncodeunits(text) : positions[index + 1] - 1
        length(strip(text[nextind(text, start):stop])) >= 20 ||
            fail("interpretation section $(headings[index]) is empty")
    end
    return true
end

function validate_bundle(directory::AbstractString)
    bundle_id = basename(normpath(directory))
    occursin(r"^51-P-[0-9]{2}$", bundle_id) ||
        fail("bundle directory must match 51-P-NN")
    files = [
        "configuration.toml", "world.toml", "protocol.toml", "analysis.toml",
        "interpretation-lock.md",
    ]
    sort(readdir(directory)) == sort(files) ||
        fail("bundle directory must contain exactly five files")
    for filename in files
        filesize(joinpath(directory, filename)) <= 262_144 ||
            fail("$filename exceeds 262,144 bytes")
    end
    configuration = validate_configuration(
        TOML.parsefile(joinpath(directory, "configuration.toml")))
    world = validate_world(TOML.parsefile(joinpath(directory, "world.toml")),
        configuration)
    protocol = validate_protocol(
        TOML.parsefile(joinpath(directory, "protocol.toml")),
        configuration, world)
    analysis = validate_analysis(
        TOML.parsefile(joinpath(directory, "analysis.toml")),
        protocol, configuration, world)
    validate_interpretation(joinpath(directory, "interpretation-lock.md"),
        bundle_id, analysis)
    return (
        configuration_id = configuration.id,
        world_id = world.id,
        protocol_id = protocol.id,
        nodes = length(configuration.nodes),
        arms = length(protocol.arms),
        analysis_dependencies = length(analysis.dependencies),
    )
end

function main(arguments)
    length(arguments) == 1 || begin
        println("usage: validate_bundle.jl BUNDLE_DIRECTORY")
        println("Run validate_contract.sh for authoritative schema + semantics.")
        return 2
    end
    result = validate_bundle(arguments[1])
    println("semantic bundle validation passed")
    println("configuration_id=$(result.configuration_id)")
    println("world_id=$(result.world_id)")
    println("protocol_id=$(result.protocol_id)")
    println("nodes=$(result.nodes)")
    println("arms=$(result.arms)")
    println("analysis_dependencies=$(result.analysis_dependencies)")
    return 0
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main(ARGS))
end
