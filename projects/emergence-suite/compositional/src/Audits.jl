function static_architecture_audit(root::AbstractString)
    source_files = filter(path -> endswith(path, ".jl"),
        readdir(joinpath(root, "src"); join = true))
    # Recursive collection without shell dependencies.
    pending = [joinpath(root, "src")]
    source_files = String[]
    while !isempty(pending)
        directory = pop!(pending)
        for path in readdir(directory; join = true)
            isdir(path) ? push!(pending, path) :
                endswith(path, ".jl") && push!(source_files, path)
        end
    end
    forbidden = Regex("\\b" * join(["ass" * "ay", "chall" * "enge"], "|") * "\\b", "i")
    violations = String[]
    for path in source_files
        occursin(forbidden, read(path, String)) &&
            push!(violations, relpath(path, root))
    end
    return violations
end

function semantic_gate(model::CompiledModel)
    node_kinds = Set(node.kind for node in values(model.nodes))
    edge_kinds = Set(edge.kind for edge in values(model.edges))
    active_protectors = [id for (id, node) in model.nodes
        if node.active && node.kind == :ProtectorNode]
    joint_labels = configured_joint_labels(model)
    return (
        all_node_kinds_present =
            all(kind in node_kinds for kind in Set([
            :BundleNode, :ContextNode, :CueNode, :LocalPrecisionNode,
            :GlobalPrecisionNode, :ProtectorNode, :PartnerNode, :AccessNode,
            :EpisodeNode, :StructureNode])),
        configured_edge_kinds_known =
            all(kind in EDGE_KINDS for kind in edge_kinds),
        all_nodes_full_cardinality =
            all(node.cardinality >= 2 for node in values(model.nodes)),
        all_configuration_fields_consumed = !isempty(model.consumption) &&
            all(!isempty(consumer) for consumer in values(model.consumption)),
        categorical_observation_api_configured =
            any(channel.likelihood_family == :categorical
                for channel in values(model.channels)),
        joint_policy_is_compositional = length(active_protectors) >= 2 &&
            length(joint_labels) > sum(length(policy.actions)
                for policy in values(model.policies) if policy.enabled),
        full_and_reduced_candidates_present =
            length(model.candidates) >= 2 &&
            length(unique(count(edge -> candidate_edge_state(candidate, edge),
                values(model.edges)) for candidate in values(model.candidates))) >= 2,
        learnable_parameters_present =
            any(edge.initial_state == :learnable for edge in values(model.edges)) &&
            !isempty(model.processes) && !isempty(model.emissions),
    )
end
