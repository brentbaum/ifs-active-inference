const EDGE_KINDS = Set([
    :bundle_context, :cue_root, :local_monitor, :local_to_global_broadcast,
    :global_precision_message, :protector_joint_policy,
    :protector_cross_prediction, :partner_regulation, :partner_trust,
    :policy_access, :access_bundle, :episode_scope, :structure_scope,
    :registration, :world_coupling,
])

logistic(value) = 1 / (1 + exp(-clamp(value, -40.0, 40.0)))
logit(value) = log(clamp(value, 1e-9, 1 - 1e-9) /
    clamp(1 - value, 1e-9, 1 - 1e-9))

function neutral_node(kind::Symbol)
    kind == :BundleNode && return Dict(
        "activation_probability" => 0.5, "root_probability" => 0.5,
        "expected_outcome" => 0.5, "mandate_probability" => 0.5)
    kind == :ContextNode && return Dict("transition_entropy" => 1.0)
    kind == :CueNode && return Dict(
        "meaning_probability" => 0.5, "root_association" => 0.5)
    kind == :LocalPrecisionNode && return Dict(
        "mean" => 0.5, "calibration_error" => 0.5)
    kind == :GlobalPrecisionNode && return Dict(
        "part" => 0.5, "context" => 0.5, "interoception" => 0.5,
        "relationship" => 0.5, "policy" => 0.5, "depth" => 0.5)
    kind == :ProtectorNode && return Dict(
        "permission_probability" => 0.5,
        "suppression_probability" => 0.5,
        "forecast_outcome" => 0.5, "forecast_coprotection" => 0.5,
        "forecast_partner_type" => 0.5)
    kind == :PartnerNode && return Dict(
        "trust_probability" => 0.5, "regulation_probability" => 0.5)
    kind == :AccessNode && return Dict("probability" => 0.5)
    kind == :EpisodeNode && return Dict("joint_probability" => 0.5)
    kind == :StructureNode && return Dict(
        "first_stable_reduced_win" => -1.0, "reversals_to_full" => 0.0)
    error("unknown node kind: $kind")
end

function configured_joint_labels(model::CompiledModel)
    protectors = sort!([id for (id, node) in model.nodes
        if node.active && node.kind == :ProtectorNode])
    if isempty(protectors)
        return sort!(unique(action for policy in values(model.policies)
            if policy.enabled for action in policy.actions))
    end
    supports = [sort!(unique(action for policy in values(model.policies)
        if policy.enabled && actor in policy.actors
        for action in policy.actions)) for actor in protectors]
    isempty(supports) && return String[]
    return [join(("$actor=$action" for (actor, action) in
        zip(protectors, choice)), ";") for choice in Iterators.product(supports...)]
end

function initialize_state(model::CompiledModel)
    factor_beliefs = Dict(id => fill(1 / length(factor.values),
        length(factor.values)) for (id, factor) in model.factors)
    node_beliefs = Dict(id => fill(1 / node.cardinality, node.cardinality)
        for (id, node) in model.nodes if node.active)
    node_values = Dict(id => neutral_node(node.kind) for (id, node) in model.nodes
        if node.active)
    edge_enabled = Dict(id => edge.initial_state == :active
        for (id, edge) in model.edges)
    edge_strength = Dict(id => edge.initial_state == :learnable ? 0.5 : 1.0
        for (id, edge) in model.edges)
    channel_enabled = Dict(id => channel.enabled for (id, channel) in model.channels)
    actions = Set(action for policy in values(model.policies) if policy.enabled
        for action in policy.actions)
    action_enabled = Dict(action => true for action in actions)
    complexity = Dict(id => model.genome["structure_complexity_penalty"] *
        count(edge -> candidate_edge_state(candidate, edge),
            values(model.edges)) for (id, candidate) in model.candidates)
    evidence = Dict(id => -complexity[id] for id in keys(model.candidates))
    concentration = model.genome["dirichlet_concentration"]
    likelihood_ids = Set(id for emission in values(model.emissions)
        for id in emission.conditional_distribution_ids)
    likelihood_counts = Dict(id => fill(concentration,
        length((model.distributions[id]::CategoricalDistributionIR).values))
        for id in likelihood_ids)
    transition_ids = Set{String}()
    for process in values(model.processes)
        process isa MarkovProcessIR && push!(transition_ids, process.transition_id)
        if process isa ChangePointProcessIR
            push!(transition_ids, process.before_id)
            push!(transition_ids, process.after_id)
        elseif process isa ActionProcessIR
            push!(transition_ids, process.baseline_id)
            push!(transition_ids, process.action_id)
        elseif process isa CoupledProcessIR
            union!(transition_ids, process.transition_ids)
        end
    end
    transition_counts = Dict(id => fill(concentration,
        size((model.distributions[id]::TransitionDistributionIR).matrix))
        for id in transition_ids)
    transition_prior = deepcopy(factor_beliefs)
    policy_counts = Dict((actor, action) => fill(concentration, 2)
        for policy in values(model.policies) if policy.enabled
        for actor in policy.actors for action in policy.actions)
    access_counts = Dict(action => fill(concentration, 2) for action in actions)
    joint_labels = configured_joint_labels(model)
    joint_policy_counts =
        Dict(label => fill(concentration, 2) for label in joint_labels)
    joint_access_counts =
        Dict(label => fill(concentration, 2) for label in joint_labels)
    trust_counts = Dict((edge.source, edge.target) => fill(concentration, 2)
        for edge in values(model.edges) if edge.kind == :partner_trust)
    selection = Dict{String,String}()
    stability = Dict{String,Int}()
    return OrganismState(factor_beliefs, node_beliefs, node_values,
        edge_enabled, edge_strength, channel_enabled, action_enabled,
        Dict{String,Float64}(), Dict{String,Float64}(), evidence, complexity,
        likelihood_counts, transition_counts, transition_prior, policy_counts,
        access_counts, joint_policy_counts, joint_access_counts, trust_counts,
        selection, stability, nothing, nothing, nothing,
        nothing, nothing, nothing, nothing, 0, 0)
end

function bayes_update!(belief::Vector{Float64}, likelihood::Vector{Float64})
    posterior = belief .* max.(likelihood, eps())
    total = sum(posterior)
    belief .= total > 0 ? posterior ./ total :
        fill(1 / length(belief), length(belief))
end

function infer_factors!(state::OrganismState, model::CompiledModel,
        observation::Observation)
    if observation.emission_id !== nothing
        emission = model.emissions[observation.emission_id]
        factors = emission.source_factors
        count = prod(length(model.factors[id].values) for id in factors)
        weights = zeros(count)
        configurations = Vector{Vector{String}}(undef, count)
        for index in 1:count
            config = configuration_at(model, factors, index)
            configurations[index] = config
            key = "joint|" * join(("$factor_id=$factor_value"
                for (factor_id, factor_value) in zip(factors, config)), ";")
            prior = prod(state.factor_beliefs[factor_id][
                findfirst(==(factor_value), model.factors[factor_id].values)]
                for (factor_id, factor_value) in zip(factors, config);
                init = 1.0)
            weights[index] = prior * observation.log_likelihoods[key]
        end
        total = sum(weights)
        total > 0 && (weights ./= total)
        for (factor_position, factor_id) in enumerate(factors)
            factor_id in observation.masked_scope && continue
            posterior = zeros(length(model.factors[factor_id].values))
            for (config, weight) in zip(configurations, weights)
                value_index = findfirst(==(config[factor_position]),
                    model.factors[factor_id].values)
                posterior[value_index] += weight
            end
            state.factor_beliefs[factor_id] .= posterior
        end
        return
    end
    for factor_id in observation.scope
        factor_id in observation.masked_scope && continue
        haskey(state.factor_beliefs, factor_id) || continue
        factor = model.factors[factor_id]
        likelihood = [get(observation.log_likelihoods,
            "$factor_id=$value", 1.0) for value in factor.values]
        bayes_update!(state.factor_beliefs[factor_id], likelihood)
    end
end

function normalize_distribution(values::AbstractVector{<:Real})
    result = max.(Float64.(values), eps())
    return result ./ sum(result)
end

function project_distribution(source::Vector{Float64}, cardinality::Int)
    length(source) == cardinality && return copy(source)
    projected = zeros(cardinality)
    for (index, probability) in enumerate(source)
        target = length(source) == 1 ? 1 :
            round(Int, 1 + (index - 1) *
                (cardinality - 1) / (length(source) - 1))
        projected[target] += probability
    end
    return normalize_distribution(projected)
end

function normalized_entropy(probabilities::Vector{Float64})
    length(probabilities) <= 1 && return 0.0
    return -sum(p * log(max(p, eps())) for p in probabilities) /
        log(length(probabilities))
end

distribution_signal(probabilities::Vector{Float64}) = maximum(probabilities)

function evidence_signal(state::OrganismState, model::CompiledModel,
        node_id::String)
    return distribution_signal(state.node_beliefs[node_id])
end

function primary_value(state::OrganismState, model::CompiledModel, id::String)
    node = model.nodes[id]
    values = state.node_values[id]
    node.kind == :BundleNode && return values["activation_probability"]
    node.kind == :ContextNode && return 1 - values["transition_entropy"]
    node.kind == :CueNode && return values["meaning_probability"]
    node.kind == :LocalPrecisionNode && return values["mean"]
    node.kind == :GlobalPrecisionNode && return values["depth"]
    node.kind == :ProtectorNode && return values["permission_probability"]
    node.kind == :PartnerNode && return values["trust_probability"]
    node.kind == :AccessNode && return values["probability"]
    node.kind == :EpisodeNode && return values["joint_probability"]
    node.kind == :StructureNode && return isempty(state.structure_evidence) ?
        0.5 : logistic(maximum(Base.values(state.structure_evidence)))
    return 0.5
end

function commit_node!(values::Dict{String,Float64}, kind::Symbol, value::Float64)
    value = clamp(value, 1e-9, 1 - 1e-9)
    kind == :BundleNode && (values["activation_probability"] = value)
    kind == :ContextNode && (values["transition_entropy"] = 1 - value)
    kind == :CueNode && (values["meaning_probability"] = value)
    if kind == :LocalPrecisionNode
        values["mean"] = value
        values["calibration_error"] = abs(value - 0.5)
    end
    kind == :PartnerNode && begin
        values["trust_probability"] = value
        values["regulation_probability"] = value
    end
    kind == :AccessNode && (values["probability"] = value)
    kind == :EpisodeNode && (values["joint_probability"] = value)
    return values
end

function update_scoped_node_beliefs!(state::OrganismState,
        model::CompiledModel, observation::Observation)
    sources = observation.emission_id === nothing ?
        [id for id in observation.scope if haskey(state.factor_beliefs, id)] :
        [id for id in model.emissions[observation.emission_id].source_factors
            if id ∉ observation.masked_scope]
    for node_id in observation.scope
        haskey(state.node_beliefs, node_id) || continue
        isempty(sources) && continue
        evidence = ones(length(state.node_beliefs[node_id]))
        for factor_id in sources
            evidence .*= project_distribution(
                state.factor_beliefs[factor_id], length(evidence))
        end
        state.node_beliefs[node_id] .= normalize_distribution(evidence)
        node = model.nodes[node_id]
        values = state.node_values[node_id]
        signal = distribution_signal(state.node_beliefs[node_id])
        if node.kind == :BundleNode
            values["activation_probability"] = signal
        elseif node.kind == :ContextNode
            values["transition_entropy"] =
                normalized_entropy(state.node_beliefs[node_id])
        elseif node.kind == :CueNode
            values["meaning_probability"] = signal
        elseif node.kind == :PartnerNode
            values["trust_probability"] = signal
            values["regulation_probability"] = signal
        elseif node.kind == :EpisodeNode
            values["joint_probability"] = signal
        end
    end
end

function active_graph_edges(state::OrganismState, model::CompiledModel;
        edge_enabled::Dict{String,Bool} = state.edge_enabled)
    return sort!([edge for edge in values(model.edges)
        if get(edge_enabled, edge.id, false) &&
            haskey(state.node_beliefs, edge.source) &&
            haskey(state.node_beliefs, edge.target)]; by = edge -> edge.id)
end

function mixed_message(message::Vector{Float64}, gain::Float64,
        cardinality::Int)
    neutral = fill(1 / cardinality, cardinality)
    return normalize_distribution((1 - gain) .* neutral .+ gain .* message)
end

function typed_edge_message(edge::EdgeIR, source::Vector{Float64},
        target_cardinality::Int, strength::Float64, gain::Float64;
        muted_kind::Union{Nothing,Symbol} = nothing)
    edge.kind in EDGE_KINDS || error("edge kind has no semantics: $(edge.kind)")
    edge.kind == muted_kind &&
        return fill(1 / target_cardinality, target_cardinality)
    projected = project_distribution(source, target_cardinality)
    message = if edge.kind == :bundle_context
        projected
    elseif edge.kind == :cue_root
        projected
    elseif edge.kind == :local_monitor
        projected
    elseif edge.kind == :local_to_global_broadcast
        projected
    elseif edge.kind == :global_precision_message
        projected
    elseif edge.kind == :protector_joint_policy
        projected
    elseif edge.kind == :protector_cross_prediction
        projected
    elseif edge.kind == :partner_regulation
        projected
    elseif edge.kind == :partner_trust
        projected
    elseif edge.kind == :policy_access
        projected
    elseif edge.kind == :access_bundle
        projected
    elseif edge.kind == :episode_scope
        projected
    elseif edge.kind == :structure_scope
        projected
    elseif edge.kind == :registration
        reverse(projected)
    elseif edge.kind == :world_coupling
        projected
    else
        error("unimplemented edge message: $(edge.kind)")
    end
    return mixed_message(message, clamp(strength * gain, 0.0, 1.0),
        target_cardinality)
end

function belief_propagation(state::OrganismState, model::CompiledModel;
        base_beliefs::Dict{String,Vector{Float64}} = state.node_beliefs,
        local_probabilities::Union{Nothing,Dict{String,Float64}} = nothing,
        edge_enabled::Dict{String,Bool} = state.edge_enabled,
        iterations::Int = Int(model.genome["approximation_iterations"]),
        muted_kind::Union{Nothing,Symbol} = nothing,
        reverse_order::Bool = false)
    bases = if local_probabilities === nothing
        deepcopy(base_beliefs)
    else
        Dict(id => length(base_beliefs[id]) == 2 ?
            [1 - local_probabilities[id], local_probabilities[id]] :
            project_distribution(
                [1 - local_probabilities[id], local_probabilities[id]],
                length(base_beliefs[id])) for id in keys(base_beliefs))
    end
    current = deepcopy(bases)
    edges = active_graph_edges(state, model; edge_enabled = edge_enabled)
    reverse_order && reverse!(edges)
    tolerance = model.genome["approximation_tolerance"]
    for _ in 1:iterations
        incoming = Dict(id => Vector{Float64}[] for id in keys(current))
        for edge in edges
            push!(incoming[edge.target], typed_edge_message(edge,
                current[edge.source], length(current[edge.target]),
                state.edge_strength[edge.id], model.genome["message_gain"];
                muted_kind = muted_kind))
        end
        next = Dict{String,Vector{Float64}}()
        maximum_delta = 0.0
        for id in sort!(collect(keys(current)))
            posterior = copy(bases[id])
            for message in incoming[id]
                posterior .*= message
            end
            next[id] = normalize_distribution(posterior)
            maximum_delta = max(maximum_delta,
                maximum(abs.(next[id] .- current[id])))
        end
        current = next
        maximum_delta <= tolerance && break
    end
    return Dict(id => distribution_signal(probability)
        for (id, probability) in current)
end

function directed_node_beliefs(state::OrganismState, model::CompiledModel;
        base_beliefs::Dict{String,Vector{Float64}} = state.node_beliefs,
        edge_enabled::Dict{String,Bool} = state.edge_enabled,
        iterations::Int = Int(model.genome["approximation_iterations"]),
        muted_kind::Union{Nothing,Symbol} = nothing,
        reverse_order::Bool = false)
    current = deepcopy(base_beliefs)
    edges = active_graph_edges(state, model; edge_enabled = edge_enabled)
    reverse_order && reverse!(edges)
    tolerance = model.genome["approximation_tolerance"]
    for _ in 1:iterations
        incoming = Dict(id => Vector{Float64}[] for id in keys(current))
        for edge in edges
            push!(incoming[edge.target], typed_edge_message(edge,
                current[edge.source], length(current[edge.target]),
                state.edge_strength[edge.id], model.genome["message_gain"];
                muted_kind = muted_kind))
        end
        next = Dict{String,Vector{Float64}}()
        maximum_delta = 0.0
        for id in sort!(collect(keys(current)))
            posterior = copy(base_beliefs[id])
            for message in incoming[id]
                posterior .*= message
            end
            next[id] = normalize_distribution(posterior)
            maximum_delta = max(maximum_delta,
                maximum(abs.(next[id] .- current[id])))
        end
        current = next
        maximum_delta <= tolerance && break
    end
    return current
end

function exact_edge_kernel_row(edge::EdgeIR, source_index::Int,
        source_cardinality::Int, target_cardinality::Int,
        strength::Float64, gain::Float64)
    mapped = source_cardinality == 1 ? 1 :
        round(Int, 1 + (source_index - 1) *
            (target_cardinality - 1) / (source_cardinality - 1))
    edge.kind == :registration &&
        (mapped = target_cardinality - mapped + 1)
    projected = zeros(target_cardinality)
    projected[mapped] = 1.0
    projected = normalize_distribution(projected)
    weight = clamp(strength * gain, 0.0, 1.0)
    return normalize_distribution(
        fill((1 - weight) / target_cardinality, target_cardinality) .+
            weight .* projected)
end

function weak_edge_components(node_ids::Vector{String},
        edges::Vector{EdgeIR})
    adjacency = Dict(id => String[] for id in node_ids)
    for edge in edges
        push!(adjacency[edge.source], edge.target)
        push!(adjacency[edge.target], edge.source)
    end
    components = Vector{Vector{String}}()
    unseen = Set(node_ids)
    while !isempty(unseen)
        start = minimum(unseen)
        queue = [start]
        delete!(unseen, start)
        component = String[]
        while !isempty(queue)
            node = popfirst!(queue)
            push!(component, node)
            for neighbor in sort!(adjacency[node])
                neighbor in unseen || continue
                delete!(unseen, neighbor)
                push!(queue, neighbor)
            end
        end
        push!(components, sort!(component))
    end
    return components
end

function topological_component(component::Vector{String},
        edges::Vector{EdgeIR})
    member = Set(component)
    local_edges = [edge for edge in edges
        if edge.source in member && edge.target in member]
    indegree = Dict(id => 0 for id in component)
    outgoing = Dict(id => String[] for id in component)
    for edge in local_edges
        indegree[edge.target] += 1
        push!(outgoing[edge.source], edge.target)
    end
    ready = sort!([id for id in component if indegree[id] == 0])
    order = String[]
    while !isempty(ready)
        node = popfirst!(ready)
        push!(order, node)
        for target in sort!(outgoing[node])
            indegree[target] -= 1
            indegree[target] == 0 && begin
                push!(ready, target)
                sort!(ready)
            end
        end
    end
    length(order) == length(component) ||
        error("exact directed oracle requires an acyclic reduced graph")
    return order, local_edges
end

function exact_graph_beliefs(state::OrganismState, model::CompiledModel;
        base_beliefs::Dict{String,Vector{Float64}} = state.node_beliefs,
        edge_enabled::Dict{String,Bool} = state.edge_enabled)
    nodes = sort!(collect(keys(base_beliefs)))
    edges = active_graph_edges(state, model; edge_enabled = edge_enabled)
    result = Dict(id => copy(base_beliefs[id]) for id in nodes)
    connected = sort!(collect(Set(vcat(
        [edge.source for edge in edges],
        [edge.target for edge in edges]))))
    isempty(connected) && return result
    for component in weak_edge_components(connected, edges)
        order, local_edges = topological_component(component, edges)
        positions = Dict(id => index for (index, id) in enumerate(order))
        incoming = Dict(id => EdgeIR[] for id in order)
        for edge in local_edges
            push!(incoming[edge.target], edge)
        end
        marginals = Dict(id => zeros(length(base_beliefs[id])) for id in order)
        total = 0.0
        ranges = (1:length(base_beliefs[id]) for id in order)
        for assignment in Iterators.product(ranges...)
            weight = 1.0
            for node in order
                conditional = copy(base_beliefs[node])
                for edge in incoming[node]
                    source_index = assignment[positions[edge.source]]
                    conditional .*= exact_edge_kernel_row(edge, source_index,
                        length(base_beliefs[edge.source]),
                        length(base_beliefs[node]),
                        state.edge_strength[edge.id],
                        model.genome["message_gain"])
                end
                conditional = normalize_distribution(conditional)
                weight *= conditional[assignment[positions[node]]]
            end
            total += weight
            for node in order
                marginals[node][assignment[positions[node]]] += weight
            end
        end
        total > 0 || error("exact directed oracle has zero probability mass")
        for node in order
            result[node] = marginals[node] ./ total
        end
    end
    return result
end

function exact_graph_marginals(state::OrganismState, model::CompiledModel;
        local_probabilities::Union{Nothing,Dict{String,Float64}} = nothing,
        edge_enabled::Dict{String,Bool} = state.edge_enabled)
    bases = local_probabilities === nothing ? state.node_beliefs :
        Dict(id => length(state.node_beliefs[id]) == 2 ?
            [1 - local_probabilities[id], local_probabilities[id]] :
            project_distribution(
                [1 - local_probabilities[id], local_probabilities[id]],
                length(state.node_beliefs[id]))
            for id in keys(state.node_beliefs))
    beliefs = exact_graph_beliefs(state, model;
        base_beliefs = bases, edge_enabled = edge_enabled)
    return Dict(id => distribution_signal(probability)
        for (id, probability) in beliefs)
end

function graph_local_probabilities(state::OrganismState, model::CompiledModel)
    return Dict(id => distribution_signal(probability)
        for (id, probability) in state.node_beliefs)
end

function queue_update!(updates, target::String, field::String,
        value::Float64, weight::Float64)
    push!(get!(updates, (target, field),
        Tuple{Float64,Float64}[]),
        (clamp(value, 0.0, 1.0), clamp(weight, 0.0, 1.0)))
end

function typed_edge_field_updates!(updates, edge::EdgeIR,
        values::Dict{String,Dict{String,Float64}}, model::CompiledModel,
        observation::Observation, strength::Float64)
    source = values[edge.source]
    weight = model.genome["message_gain"] * strength
    source_kind = model.nodes[edge.source].kind
    source_signal = source_kind == :ContextNode ?
        1 - source["transition_entropy"] :
        source_kind == :BundleNode ? source["activation_probability"] :
        source_kind == :CueNode ? source["meaning_probability"] :
        source_kind == :LocalPrecisionNode ? source["mean"] :
        source_kind == :GlobalPrecisionNode ? source["depth"] :
        source_kind == :ProtectorNode ? source["permission_probability"] :
        source_kind == :PartnerNode ? source["trust_probability"] :
        source_kind == :AccessNode ? source["probability"] :
        source_kind == :EpisodeNode ? source["joint_probability"] : 0.5
    if edge.kind == :bundle_context
        queue_update!(updates, edge.target, "activation_probability",
            source_signal, weight)
    elseif edge.kind == :cue_root
        queue_update!(updates, edge.target, "root_probability",
            source_signal, weight)
    elseif edge.kind == :local_monitor
        edge.source in observation.scope &&
            queue_update!(updates, edge.target, "mean",
                max(model.genome["precision_floor"],
                    observation.reliability), weight)
    elseif edge.kind == :local_to_global_broadcast
        queue_update!(updates, edge.target, "part", source_signal, weight)
    elseif edge.kind == :global_precision_message
        target_kind = model.nodes[edge.target].kind
        field = target_kind == :BundleNode ? "activation_probability" :
            target_kind == :ContextNode ? "transition_entropy" :
            "forecast_outcome"
        value = target_kind == :ContextNode ? 1 - source_signal : source_signal
        queue_update!(updates, edge.target, field, value, weight)
    elseif edge.kind == :protector_joint_policy
        queue_update!(
            updates, edge.target, "probability", source_signal, weight)
    elseif edge.kind == :protector_cross_prediction
        queue_update!(updates, edge.target, "forecast_coprotection",
            source["forecast_outcome"], weight)
    elseif edge.kind == :partner_regulation
        queue_update!(updates, edge.target, "relationship",
            source["regulation_probability"], weight)
    elseif edge.kind == :partner_trust
        queue_update!(updates, edge.target, "forecast_partner_type",
            source["trust_probability"], weight)
    elseif edge.kind == :policy_access
        queue_update!(updates, edge.target, "probability",
            source["mandate_probability"], weight)
    elseif edge.kind == :access_bundle
        queue_update!(updates, edge.target, "activation_probability",
            source_signal, weight)
    elseif edge.kind == :episode_scope
        target_kind = model.nodes[edge.target].kind
        field = target_kind == :BundleNode ? "root_probability" :
            target_kind == :CueNode ? "meaning_probability" :
            "transition_entropy"
        value = target_kind == :ContextNode ? 1 - source_signal : source_signal
        queue_update!(updates, edge.target, field, value, weight)
    elseif edge.kind == :structure_scope
        return
    elseif edge.kind == :registration
        queue_update!(updates, edge.target, "mandate_probability",
            1 - source_signal, weight)
    elseif edge.kind == :world_coupling
        target_kind = model.nodes[edge.target].kind
        field = target_kind == :BundleNode ? "expected_outcome" :
            target_kind == :ContextNode ? "transition_entropy" :
            "trust_probability"
        value = target_kind == :ContextNode ? 1 - source_signal : source_signal
        queue_update!(updates, edge.target, field, value, weight)
    else
        error("edge field semantics missing: $(edge.kind)")
    end
end

function apply_directed_semantics!(state::OrganismState,
        model::CompiledModel, observation::Observation;
        muted_kind::Union{Nothing,Symbol} = nothing)
    updates =
        Dict{Tuple{String,String},Vector{Tuple{Float64,Float64}}}()
    snapshot = deepcopy(state.node_values)
    for edge in active_graph_edges(state, model)
        edge.kind == muted_kind && continue
        typed_edge_field_updates!(updates, edge, snapshot, model, observation,
            state.edge_strength[edge.id])
    end
    for ((target, field), contributions) in sort!(collect(updates); by = first)
        current = state.node_values[target][field]
        total = sum(last, contributions)
        weight = clamp(total, 0.0, 1.0)
        proposed = total == 0 ? current :
            sum(value * contribution_weight
                for (value, contribution_weight) in contributions) / total
        state.node_values[target][field] =
            (1 - weight) * current + weight * proposed
    end
    for (id, node) in model.nodes
        node.active || continue
        values = state.node_values[id]
        if node.kind == :LocalPrecisionNode
            values["mean"] = max(model.genome["precision_floor"], values["mean"])
            values["calibration_error"] =
                abs(values["mean"] - observation.reliability)
        elseif node.kind == :GlobalPrecisionNode
            contexts = [1 - state.node_values[source]["transition_entropy"]
                for source in observation.scope
                if haskey(model.nodes, source) &&
                    model.nodes[source].active &&
                    model.nodes[source].kind == :ContextNode]
            isempty(contexts) ||
                (values["context"] = mean(contexts))
            local_monitors = [state.node_values[source]["mean"]
                for source in observation.scope
                if haskey(model.nodes, source) &&
                    model.nodes[source].active &&
                    model.nodes[source].kind == :LocalPrecisionNode]
            if observation.source == :body
                values["interoception"] = max(
                    model.genome["precision_floor"],
                    observation.reliability)
            elseif !isempty(local_monitors)
                values["interoception"] = mean(local_monitors)
            end
            values["depth"] = mean(values[field] for field in
                ("part", "context", "interoception", "relationship", "policy"))
        elseif node.kind == :ProtectorNode
            values["suppression_probability"] =
                1 - values["permission_probability"]
        end
    end
end

function message_fixed_point!(state::OrganismState, model::CompiledModel,
        observation::Observation)
    state.node_beliefs = directed_node_beliefs(state, model)
    apply_directed_semantics!(state, model, observation)
end

function normalized_transition(counts::Matrix{Float64})
    matrix = copy(counts)
    for row in axes(matrix, 1)
        matrix[row, :] ./= sum(matrix[row, :])
    end
    return matrix
end

function distribution_expectation(distribution::DistributionIR)
    distribution isa FixedDistributionIR && return distribution.value
    distribution isa UniformDistributionIR &&
        return (distribution.lower + distribution.upper) / 2
    distribution isa IntegerUniformDistributionIR &&
        return (distribution.lower + distribution.upper) / 2
    distribution isa BetaDistributionIR &&
        return distribution.alpha / (distribution.alpha + distribution.beta)
    error("categorical distribution has no scalar change-time expectation")
end

function change_point_after(model::CompiledModel,
        process::ChangePointProcessIR, time::Int)
    threshold = distribution_expectation(
        model.distributions[process.change_time_id])
    return time >= threshold
end

function learned_process_matrix(state::OrganismState,
        model::CompiledModel, process::ProcessIR,
        time::Int = state.observation_count)
    if process isa MarkovProcessIR
        return normalized_transition(state.transition_counts[process.transition_id])
    elseif process isa ChangePointProcessIR
        id = change_point_after(model, process, time) ?
            process.after_id : process.before_id
        return normalized_transition(state.transition_counts[id])
    elseif process isa ActionProcessIR
        id = state.selected_action == process.action ?
            process.action_id : process.baseline_id
        return normalized_transition(state.transition_counts[id])
    elseif process isa CoupledProcessIR
        weights = Float64[]
        matrices = Matrix{Float64}[]
        for (index, id) in enumerate(process.transition_ids)
            configuration = configuration_at(model, process.source_factors, index)
            weight = prod(state.factor_beliefs[factor_id][
                findfirst(==(value), model.factors[factor_id].values)]
                for (factor_id, value) in
                    zip(process.source_factors, configuration); init = 1.0)
            push!(weights, weight)
            push!(matrices, normalized_transition(state.transition_counts[id]))
        end
        total = sum(weights)
        return sum(weight .* matrix for (weight, matrix) in
            zip(weights ./ total, matrices))
    end
    return nothing
end

function predict_factors!(state::OrganismState, model::CompiledModel;
        time::Int = state.observation_count)
    for process in sort!(collect(values(model.processes)); by = process -> process.id)
        factor_id = getfield(process, :target)
        prior = copy(state.factor_beliefs[factor_id])
        state.transition_prior[factor_id] = prior
        if process isa IIDProcessIR
            distribution =
                model.distributions[process.distribution_id]::CategoricalDistributionIR
            state.factor_beliefs[factor_id] .= distribution.probabilities
            continue
        end
        matrix = learned_process_matrix(state, model, process, time)
        matrix === nothing && continue
        state.factor_beliefs[factor_id] .=
            normalize_distribution(vec(prior' * matrix))
    end
    return state
end

function infer!(state::OrganismState, model::CompiledModel,
        observation::Observation)
    infer_factors!(state, model, observation)
    update_scoped_node_beliefs!(state, model, observation)
    message_fixed_point!(state, model, observation)
    state.observation_count += 1
    return state
end

function exact_enumerable_state(state::OrganismState, model::CompiledModel;
        local_probabilities::Union{Nothing,Dict{String,Float64}} = nothing)
    clone = deepcopy(state)
    beliefs = if local_probabilities === nothing
        directed_node_beliefs(state, model; iterations = 512)
    else
        bases = Dict(id => length(state.node_beliefs[id]) == 2 ?
            [1 - local_probabilities[id], local_probabilities[id]] :
            project_distribution(
                [1 - local_probabilities[id], local_probabilities[id]],
                length(state.node_beliefs[id]))
            for id in keys(state.node_beliefs))
        directed_node_beliefs(state, model;
            base_beliefs = bases, iterations = 512)
    end
    clone.node_beliefs = beliefs
    return clone
end
