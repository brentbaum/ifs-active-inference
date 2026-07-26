const ACTION_PRIORITY = [
    "withdraw", "suppress", "wait", "observe", "inspect", "request_support",
    "offer_support", "permit", "approach",
]

function product_labels(actors::Vector{String}, actions::Vector{Vector{String}})
    isempty(actors) && return String[]
    labels = String[]
    for choice in Iterators.product(actions...)
        push!(labels, join(("$actor=$action" for (actor, action) in
            zip(actors, choice)), ";"))
    end
    return labels
end

function joint_support(state::OrganismState, model::CompiledModel)
    protectors = sort!([id for (id, node) in model.nodes
        if node.active && node.kind == :ProtectorNode])
    if isempty(protectors)
        actors = sort!(unique(actor for policy in values(model.policies)
            if policy.enabled for actor in policy.actors
            if haskey(state.node_values, actor)))
        actions = sort!(unique(action for policy in values(model.policies)
            if policy.enabled for action in policy.actions
            if get(state.action_enabled, action, false)))
        return actions, actors
    end
    actor_actions = Vector{Vector{String}}()
    for actor in protectors
        actions = sort!(unique(action for policy in values(model.policies)
            if policy.enabled && actor in policy.actors for action in policy.actions
            if get(state.action_enabled, action, false)))
        isempty(actions) && return String[], protectors
        push!(actor_actions, actions)
    end
    return product_labels(protectors, actor_actions), protectors
end

function label_actions(label::String)
    occursin('=', label) ?
        [String(last(split(pair, '='; limit = 2)))
            for pair in split(label, ';')] :
        [label]
end

function learned_probability(counts::Vector{Float64})
    return counts[2] / sum(counts)
end

function actor_forecast(state::OrganismState, model::CompiledModel,
        actor::String, action::String, action_by_actor::Dict{String,String})
    forecast = learned_probability(state.policy_counts[(actor, action)])
    incoming = [edge for edge in values(model.edges)
        if edge.kind == :protector_cross_prediction &&
            edge.target == actor && get(state.edge_enabled, edge.id, false) &&
            haskey(action_by_actor, edge.source)]
    for edge in incoming
        other = learned_probability(state.policy_counts[
            (edge.source, action_by_actor[edge.source])])
        strength = state.edge_strength[edge.id] * model.genome["message_gain"]
        forecast = (forecast + strength * other) / (1 + strength)
    end
    trust = [learned_probability(state.trust_counts[
        (edge.source, edge.target)]) for edge in values(model.edges)
        if edge.kind == :partner_trust && edge.target == actor &&
            get(state.edge_enabled, edge.id, false) &&
            haskey(state.trust_counts, (edge.source, edge.target))]
    isempty(trust) || (forecast = mean((forecast, mean(trust))))
    return forecast
end

function joint_statistics(state::OrganismState, model::CompiledModel,
        label::String, actors::Vector{String})
    actions = label_actions(label)
    length(actions) == length(actors) ||
        error("joint label/actor dimension mismatch")
    action_by_actor = Dict(actor => action
        for (actor, action) in zip(actors, actions))
    forecasts = [actor_forecast(
        state, model, actor, action_by_actor[actor], action_by_actor)
        for actor in actors]
    access = haskey(state.joint_access_counts, label) ?
        learned_probability(state.joint_access_counts[label]) :
        mean(learned_probability(state.access_counts[action])
            for action in actions)
    if !isempty(actors) &&
            all(model.nodes[actor].kind == :ProtectorNode for actor in actors)
        contributing = count(actor -> any(
            edge.kind == :protector_joint_policy &&
                edge.source == actor &&
                get(state.edge_enabled, edge.id, false)
            for edge in values(model.edges)), actors)
        access *= contributing / length(actors)
    end
    outcome = haskey(state.joint_policy_counts, label) ?
        learned_probability(state.joint_policy_counts[label]) :
        mean(forecasts)
    return forecasts, access, outcome
end

function joint_gfe(state::OrganismState, model::CompiledModel,
        label::String, actors::Vector{String})
    actions = label_actions(label)
    cost = mean(get(model.action_costs, action, 0.0) for action in actions)
    forecasts, access, outcome = joint_statistics(
        state, model, label, actors)
    bundle_prediction = mean(primary_value(state, model, id)
        for (id, node) in model.nodes if node.active &&
            node.kind == :BundleNode)
    risk = 1 - outcome
    shared_outcome_risk = abs(bundle_prediction - access * outcome)
    ambiguity = length(forecasts) <= 1 ? 0.0 : var(forecasts; corrected = false)
    epistemic_value = mean(inv(sqrt(sum(state.policy_counts[(actor, action)])))
        for (actor, action) in zip(actors, actions))
    return cost + risk + shared_outcome_risk + ambiguity - epistemic_value
end

function reconcile_action(label::String)
    actions = label_actions(label)
    counts = Dict(action => count(==(action), actions) for action in unique(actions))
    maximum_count = maximum(values(counts))
    tied = Set(action for (action, count) in counts if count == maximum_count)
    for action in ACTION_PRIORITY
        action in tied && return action
    end
    return sort!(collect(tied))[1]
end

function infer_policy!(state::OrganismState, model::CompiledModel)
    support, actors = joint_support(state, model)
    empty!(state.policy_gfe)
    empty!(state.policy_posterior)
    isempty(support) && return false
    for label in support
        state.policy_gfe[label] = joint_gfe(state, model, label, actors)
    end
    temperature = model.genome["policy_temperature"]
    scores = Dict(label => -gfe / temperature
        for (label, gfe) in state.policy_gfe)
    offset = maximum(values(scores))
    total = sum(exp(score - offset) for score in values(scores))
    for (label, score) in scores
        state.policy_posterior[label] = exp(score - offset) / total
    end
    selected_label = sort!(collect(keys(state.policy_posterior));
        by = label -> (-state.policy_posterior[label], label))[1]
    state.previous_action = state.selected_action
    state.selected_policy_label = selected_label
    state.selected_action = reconcile_action(selected_label)
    protectors = [actor for actor in actors
        if model.nodes[actor].kind == :ProtectorNode]
    for protector in protectors
        permission = 0.0
        forecast_outcome = 0.0
        forecast_coprotection = 0.0
        for (label, probability) in state.policy_posterior
            pairs = Dict(split(pair, '='; limit = 2)
                for pair in split(label, ';'))
            forecasts, access, _ = joint_statistics(
                state, model, label, actors)
            actor_index = findfirst(==(protector), actors)
            access > 0.5 && (permission += probability)
            forecast_outcome += probability * forecasts[actor_index]
            others = [value for (index, value) in enumerate(forecasts)
                if index != actor_index]
            forecast_coprotection += probability *
                (isempty(others) ? forecasts[actor_index] : mean(others))
        end
        state.node_values[protector]["permission_probability"] = permission
        state.node_values[protector]["suppression_probability"] = 1 - permission
        state.node_values[protector]["forecast_outcome"] = forecast_outcome
        state.node_values[protector]["forecast_coprotection"] =
            forecast_coprotection
        partner_forecasts = [state.node_values[id]["trust_probability"]
            for (id, node) in model.nodes if node.active &&
                node.kind == :PartnerNode]
        state.node_values[protector]["forecast_partner_type"] =
            isempty(partner_forecasts) ? 0.5 : mean(partner_forecasts)
    end
    access_nodes = [id for (id, node) in model.nodes
        if node.active && node.kind == :AccessNode]
    access_probability = sum(probability *
        joint_statistics(state, model, label, actors)[2]
        for (label, probability) in state.policy_posterior)
    for id in access_nodes
        state.node_values[id]["probability"] = access_probability
    end
    global_nodes = [id for (id, node) in model.nodes
        if node.active && node.kind == :GlobalPrecisionNode]
    policy_precision = maximum(values(state.policy_posterior))
    for id in global_nodes
        state.node_values[id]["policy"] = policy_precision
        state.node_values[id]["depth"] = mean(state.node_values[id][field]
            for field in ("part", "context", "interoception",
                "relationship", "policy"))
    end
    return true
end
