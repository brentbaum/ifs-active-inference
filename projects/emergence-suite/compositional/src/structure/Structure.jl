function candidate_edge_state(candidate::CandidateIR, edge::EdgeIR)
    edge.id in candidate.active_edges && return true
    edge.id in candidate.inactive_edges && return false
    return edge.initial_state == :active
end

function candidate_edge_map(model::CompiledModel, candidate::CandidateIR)
    return Dict(id => candidate_edge_state(candidate, edge)
        for (id, edge) in model.edges)
end

function candidate_node_beliefs(state::OrganismState,
        model::CompiledModel, candidate::CandidateIR)
    return directed_node_beliefs(state, model;
        edge_enabled = candidate_edge_map(model, candidate))
end

function candidate_applies(model::CompiledModel, observation::Observation,
        candidate::CandidateIR)
    scopes = [edge for edge in values(model.edges)
        if edge.kind == :structure_scope &&
            edge.target == candidate.structure_node &&
            candidate_edge_state(candidate, edge)]
    isempty(scopes) && return false
    return any(edge.source in observation.scope for edge in scopes)
end

function candidate_factor_beliefs(state::OrganismState,
        model::CompiledModel, emission::EmissionIR, channel::ChannelIR,
        node_beliefs::Dict{String,Vector{Float64}})
    result = Dict{String,Vector{Float64}}()
    scoped_nodes = [id for id in channel.scope if haskey(node_beliefs, id)]
    for factor_id in emission.source_factors
        prior = copy(state.factor_beliefs[factor_id])
        if !isempty(scoped_nodes)
            structural = ones(length(prior))
            for node_id in scoped_nodes
                structural .*= project_distribution(
                    node_beliefs[node_id], length(prior))
            end
            prior .*= normalize_distribution(structural)
        end
        result[factor_id] = normalize_distribution(prior)
    end
    return result
end

function learned_emission_probabilities(state::OrganismState,
        model::CompiledModel, distribution_id::String)
    distribution =
        model.distributions[distribution_id]::CategoricalDistributionIR
    counts = state.likelihood_counts[distribution_id]
    learned = counts ./ sum(counts)
    concentration = model.genome["dirichlet_concentration"]
    experience = max(sum(counts) - concentration * length(counts), 0.0)
    weight = experience / (experience + concentration * length(counts))
    return (1 - weight) .* distribution.probabilities .+ weight .* learned
end

function categorical_candidate_probabilities(state::OrganismState,
        model::CompiledModel, observation::Observation,
        candidate::CandidateIR)
    channel = model.channels[observation.channel_id]
    beliefs = candidate_node_beliefs(state, model, candidate)
    if observation.emission_id === nothing
        scoped = [project_distribution(beliefs[id], length(channel.values))
            for id in channel.scope if haskey(beliefs, id)]
        isempty(scoped) &&
            return Dict(label => 1 / length(channel.values)
                for label in channel.values)
        raw = normalize_distribution(reduce(.*, scoped))
        return Dict(label => raw[index]
            for (index, label) in enumerate(channel.values))
    end
    emission = model.emissions[observation.emission_id]
    factor_beliefs = candidate_factor_beliefs(
        state, model, emission, channel, beliefs)
    probabilities = Dict(label => 0.0 for label in channel.values)
    configurations = prod(length(model.factors[id].values)
        for id in emission.source_factors)
    for index in 1:configurations
        config = configuration_at(model, emission.source_factors, index)
        prior = prod(factor_beliefs[factor_id][
            findfirst(==(factor_value), model.factors[factor_id].values)]
            for (factor_id, factor_value) in
                zip(emission.source_factors, config); init = 1.0)
        distribution_id = emission.conditional_distribution_ids[index]
        distribution =
            model.distributions[distribution_id]::CategoricalDistributionIR
        learned = learned_emission_probabilities(
            state, model, distribution_id)
        for label in channel.values
            position = findfirst(==(label), distribution.values)
            probabilities[label] += prior * (
                observation.reliability * learned[position] +
                (1 - observation.reliability) / length(channel.values))
        end
    end
    total = sum(values(probabilities))
    return Dict(label => probability / total
        for (label, probability) in probabilities)
end

function gaussian_candidate_density(state::OrganismState,
        model::CompiledModel, observation::Observation,
        candidate::CandidateIR)
    emission = model.emissions[observation.emission_id]
    channel = model.channels[observation.channel_id]
    scale = observation.effective_scale
    scale === nothing && error("Gaussian candidate evidence requires event scale")
    beliefs = candidate_node_beliefs(state, model, candidate)
    factor_beliefs = candidate_factor_beliefs(
        state, model, emission, channel, beliefs)
    density = 0.0
    configurations = prod(length(model.factors[id].values)
        for id in emission.source_factors)
    for index in 1:configurations
        config = configuration_at(model, emission.source_factors, index)
        prior = prod(factor_beliefs[factor_id][
            findfirst(==(factor_value), model.factors[factor_id].values)]
            for (factor_id, factor_value) in
                zip(emission.source_factors, config); init = 1.0)
        mean_value = emission.means[index]
        lower_mass = normal_cdf((channel.bounds[1] - mean_value) / scale)
        upper_mass = normal_cdf((channel.bounds[2] - mean_value) / scale)
        component = exp(-0.5 *
            ((Float64(observation.value) - mean_value) / scale)^2) /
            (scale * sqrt(2pi) *
                max(upper_mass - lower_mass, eps()))
        density += prior * component
    end
    return density
end

function candidate_predictive_score(state::OrganismState,
        model::CompiledModel, observation::Observation,
        candidate::CandidateIR)
    candidate_applies(model, observation, candidate) || return 0.0
    if observation.family == :gaussian_bounded
        return log(max(gaussian_candidate_density(
            state, model, observation, candidate), eps()))
    end
    probabilities = categorical_candidate_probabilities(
        state, model, observation, candidate)
    return log(max(probabilities[String(observation.value)], eps()))
end

function candidate_scores(state::OrganismState, model::CompiledModel,
        observation::Observation)
    return Dict(id => candidate_predictive_score(
        state, model, observation, candidate)
        for (id, candidate) in model.candidates)
end

function ordered_candidates(model::CompiledModel, structure_node::String)
    return sort!([candidate for candidate in values(model.candidates)
        if candidate.structure_node == structure_node];
        by = candidate -> candidate.ordinal)
end

function candidate_winner(state::OrganismState,
        candidates::Vector{CandidateIR})
    best = first(candidates)
    best_score = state.structure_evidence[best.id]
    for candidate in Iterators.drop(candidates, 1)
        score = state.structure_evidence[candidate.id]
        if score > best_score
            best = candidate
            best_score = score
        end
    end
    return best
end

function update_structure_history!(state::OrganismState,
        model::CompiledModel, time::Int)
    structure_nodes = sort!(unique(candidate.structure_node
        for candidate in values(model.candidates)))
    for node_id in structure_nodes
        candidates = ordered_candidates(model, node_id)
        winner = candidate_winner(state, candidates)
        previous = get(state.structure_selection, node_id, "")
        state.structure_stability[node_id] =
            previous == winner.id ?
                get(state.structure_stability, node_id, 0) + 1 : 1
        active_counts = Dict(candidate.id => count(edge_id ->
            candidate_edge_state(candidate, model.edges[edge_id]),
            keys(model.edges)) for candidate in candidates)
        minimum_count = minimum(values(active_counts))
        winner_is_reduced = active_counts[winner.id] == minimum_count
        previous_is_reduced = !isempty(previous) &&
            active_counts[previous] == minimum_count
        values_for_node = state.node_values[node_id]
        if winner_is_reduced && state.structure_stability[node_id] >= 2 &&
                values_for_node["first_stable_reduced_win"] < 0
            values_for_node["first_stable_reduced_win"] = time
        end
        if previous_is_reduced && !winner_is_reduced
            values_for_node["reversals_to_full"] += 1
        end
        state.structure_selection[node_id] = winner.id
    end
end

function score_structures!(state::OrganismState, model::CompiledModel,
        observation::Observation)
    scores = candidate_scores(state, model, observation)
    updated = false
    for (id, score) in scores
        candidate_applies(model, observation, model.candidates[id]) || continue
        state.structure_evidence[id] += score
        updated = true
    end
    updated && update_structure_history!(state, model, observation.time)
    return scores
end

function selected_candidates(state::OrganismState, model::CompiledModel)
    selected = Dict{String,Bool}()
    nodes = unique(candidate.structure_node
        for candidate in values(model.candidates))
    for node_id in nodes
        candidates = ordered_candidates(model, node_id)
        winner = candidate_winner(state, candidates)
        for candidate in candidates
            selected[candidate.id] = candidate.id == winner.id
        end
    end
    return selected
end
