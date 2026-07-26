function transition_learning_targets(state::OrganismState,
        model::CompiledModel, process::ProcessIR, time::Int)
    if process isa MarkovProcessIR
        return [(process.transition_id, 1.0)]
    elseif process isa ChangePointProcessIR
        id = change_point_after(model, process, time) ?
            process.after_id : process.before_id
        return [(id, 1.0)]
    elseif process isa ActionProcessIR
        id = state.selected_action == process.action ?
            process.action_id : process.baseline_id
        return [(id, 1.0)]
    elseif process isa CoupledProcessIR
        result = Tuple{String,Float64}[]
        for (index, id) in enumerate(process.transition_ids)
            configuration =
                configuration_at(model, process.source_factors, index)
            weight = prod(state.factor_beliefs[factor_id][
                findfirst(==(value), model.factors[factor_id].values)]
                for (factor_id, value) in
                    zip(process.source_factors, configuration); init = 1.0)
            push!(result, (id, weight))
        end
        total = sum(last, result)
        return [(id, weight / total) for (id, weight) in result]
    end
    return Tuple{String,Float64}[]
end

function learn!(state::OrganismState, model::CompiledModel,
        observation::Observation)
    rate = model.genome["learning_rate"]
    for edge in values(model.edges)
        edge.initial_state == :learnable || continue
        edge.source in observation.scope && edge.target in observation.scope ||
            continue
        source = primary_value(state, model, edge.source)
        target = primary_value(state, model, edge.target)
        agreement = source * target + (1 - source) * (1 - target)
        state.edge_strength[edge.id] =
            clamp((1 - rate) * state.edge_strength[edge.id] +
                rate * agreement, 0.0, 1.0)
        state.edge_enabled[edge.id] = state.edge_strength[edge.id] > 0.5
        if edge.kind == :cue_root
            state.node_values[edge.source]["root_association"] =
                state.edge_strength[edge.id]
        end
    end
    for edge in values(model.edges)
        edge.kind == :partner_trust || continue
        edge.source in observation.scope || continue
        pair = (edge.source, edge.target)
        haskey(state.trust_counts, pair) || continue
        trust = primary_value(state, model, edge.source)
        update_binary_counts!(state.trust_counts[pair], trust, rate)
        learned = learned_probability(state.trust_counts[pair])
        state.node_values[edge.source]["trust_probability"] = learned
        state.node_values[edge.target]["forecast_partner_type"] = learned
    end
    if observation.emission_id !== nothing
        emission = model.emissions[observation.emission_id]
        if !isempty(emission.conditional_distribution_ids)
            configurations = length(emission.conditional_distribution_ids)
            weights = zeros(configurations)
            for index in 1:configurations
                config = configuration_at(
                    model, emission.source_factors, index)
                weights[index] = prod(state.factor_beliefs[factor_id][
                    findfirst(==(factor_value),
                        model.factors[factor_id].values)]
                    for (factor_id, factor_value) in
                        zip(emission.source_factors, config); init = 1.0)
            end
            total = sum(weights)
            total > 0 && (weights ./= total)
            for (index, distribution_id) in
                    enumerate(emission.conditional_distribution_ids)
                distribution =
                    model.distributions[distribution_id]::CategoricalDistributionIR
                value_index =
                    findfirst(==(observation.value), distribution.values)
                state.likelihood_counts[distribution_id][value_index] +=
                    rate * weights[index]
            end
        end
        for process in values(model.processes)
            factor_id = getfield(process, :target)
            factor_id in emission.source_factors || continue
            prior = state.transition_prior[factor_id]
            posterior = state.factor_beliefs[factor_id]
            sufficient_statistic = prior * posterior'
            for (id, weight) in
                    transition_learning_targets(
                        state, model, process, observation.time)
                state.transition_counts[id] .+=
                    rate * weight .* sufficient_statistic
            end
        end
    end
    state.update_count += 1
    return state
end

function update_binary_counts!(counts::Vector{Float64},
        probability::Float64, rate::Float64)
    counts[1] += rate * (1 - probability)
    counts[2] += rate * probability
end

function learn_outcomes!(state::OrganismState, model::CompiledModel)
    state.selected_action === nothing && return state
    state.action_success === nothing && return state
    rate = model.genome["learning_rate"]
    successful = state.action_success &&
        something(state.realized_hazard, false) == false
    outcome = successful ? 1.0 : 0.0
    access = state.action_success ? 1.0 : 0.0
    label = something(state.selected_policy_label, state.selected_action)
    haskey(state.joint_policy_counts, label) &&
        update_binary_counts!(
            state.joint_policy_counts[label], outcome, rate)
    haskey(state.joint_access_counts, label) &&
        update_binary_counts!(
            state.joint_access_counts[label], access, rate)
    actors = sort!([id for (id, node) in model.nodes
        if node.active && node.kind == :ProtectorNode])
    actions = label_actions(label)
    if length(actions) == length(actors)
        for (actor, action) in zip(actors, actions)
            update_binary_counts!(
                state.policy_counts[(actor, action)], outcome, rate)
        end
    end
    haskey(state.access_counts, state.selected_action) &&
        update_binary_counts!(
            state.access_counts[state.selected_action], access, rate)
    bundle_nodes = [id for (id, node) in model.nodes
        if node.active && node.kind == :BundleNode]
    forecast = haskey(state.joint_policy_counts, label) ?
        learned_probability(state.joint_policy_counts[label]) : outcome
    for id in bundle_nodes
        state.node_values[id]["expected_outcome"] = forecast
    end
    return state
end
