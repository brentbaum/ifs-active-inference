const RNG_DOMAIN = "ifs-ai-51-rng-v1"

function u64be(value::Integer)
    value >= 0 || error("counter value must be nonnegative")
    return UInt8[(UInt64(value) >> shift) & 0xff for shift in 56:-8:0]
end

function counter_uniform(seed::UInt64, kind::Symbol, id::AbstractString,
        tick::Int, draw::Int)
    payload = UInt8[]
    append!(payload, codeunits(RNG_DOMAIN)); push!(payload, 0x00)
    append!(payload, u64be(seed)); push!(payload, 0x00)
    append!(payload, codeunits(String(kind))); push!(payload, 0x00)
    append!(payload, codeunits(id)); push!(payload, 0x00)
    append!(payload, u64be(tick)); push!(payload, 0x00)
    append!(payload, u64be(draw))
    digest = sha256(payload)
    x = foldl((acc, byte) -> (acc << 8) | UInt64(byte),
        digest[1:8]; init = UInt64(0))
    return ldexp(Float64(x), -64) + ldexp(0.5, -64)
end

function inverse_categorical(values, probabilities, u)
    cumulative = 0.0
    for (value, probability) in zip(values, probabilities)
        cumulative += probability
        u < cumulative && return value
    end
    return last(values)
end

function inverse_beta(u, a, b)
    u == 0 && return 0.0
    u == 1 && return 1.0
    lower, upper = 0.0, 1.0
    # Forty-eight bisections put the inverse below the declared 1e-12 engine
    # tolerance while avoiding the analysis routine's deliberately conservative
    # 128 steps for every world event.
    for _ in 1:48
        midpoint = lower + (upper - lower) / 2
        if regularized_incomplete_beta(midpoint, a, b) < u
            lower = midpoint
        else
            upper = midpoint
        end
    end
    return lower + (upper - lower) / 2
end

function paired_component(protocol::ProtocolIR, arm::String,
        kind::Symbol, id::String)
    any(arm in stream.arms && (kind, id) in stream.components
        for stream in protocol.paired_streams)
end

function scalar_component(distribution::DistributionIR,
        protocol::ProtocolIR, arm::String)
    return rng_component_id(protocol, arm, :distribution,
        getfield(distribution, :id))
end

function rng_component_id(protocol::ProtocolIR, arm::String,
        kind::Symbol, id::String)
    paired_component(protocol, arm, kind, id) ? id : "$arm/$id"
end

function scalar_draw(distribution::DistributionIR, seed::UInt64,
        component_id::String, tick::Int, episode_first_tick::Int, draw::Int)
    distribution isa FixedDistributionIR && return distribution.value
    scope = getfield(distribution, :scope)
    draw_tick = scope == :world ? 0 :
        scope == :episode ? episode_first_tick : tick
    draw_index = scope == :event ? draw : 0
    u = counter_uniform(seed, :distribution, component_id, draw_tick, draw_index)
    distribution isa UniformDistributionIR &&
        return distribution.lower +
            (distribution.upper - distribution.lower) * u
    distribution isa IntegerUniformDistributionIR &&
        return Float64(distribution.lower +
            floor(Int, (distribution.upper - distribution.lower + 1) * u))
    distribution isa BetaDistributionIR &&
        return inverse_beta(u, distribution.alpha, distribution.beta)
    error("categorical table used as scalar distribution")
end

function configuration_index(model::CompiledModel, factors::Vector{String},
        truth::Dict{String,String})
    index = 1
    for factor_id in factors
        factor = model.factors[factor_id]
        index = (index - 1) * length(factor.values) +
            findfirst(==(truth[factor_id]), factor.values)
    end
    return index
end

function initialize_world(model::CompiledModel, protocol::ProtocolIR,
        arm::String, seed::UInt64)
    truth = Dict{String,String}()
    for id in sort!(collect(keys(model.factors)))
        factor = model.factors[id]
        distribution = model.distributions[factor.initial_distribution_id]
        distribution isa CategoricalDistributionIR ||
            error("factor prior must be categorical")
        component = rng_component_id(protocol, arm, :latent_factor, id)
        truth[id] = inverse_categorical(distribution.values,
            distribution.probabilities,
            counter_uniform(seed, :latent_factor, component, 0, 0))
    end
    world = WorldState(truth,
        Dict(id => contingency.enabled
            for (id, contingency) in model.contingencies),
        Dict{Tuple{String,Int},Float64}(), Dict{String,Int}())
    for process in values(model.processes)
        process isa ChangePointProcessIR || continue
        distribution = model.distributions[process.change_time_id]
        component = scalar_component(distribution, protocol, arm)
        value = scalar_draw(distribution, seed, component, 0, 0, 0)
        world.change_times[process.target] = Int(value)
    end
    return world
end

function transition_values(distribution::TransitionDistributionIR,
        previous::String)
    row = findfirst(==(previous), distribution.values)
    return distribution.values, vec(distribution.matrix[row, :])
end

function process_distribution(model::CompiledModel, process::ProcessIR,
        prior::Dict{String,String}, world::WorldState, previous_action,
        previous_success, time::Int)
    if process isa IIDProcessIR
        return model.distributions[process.distribution_id]
    elseif process isa MarkovProcessIR
        return model.distributions[process.transition_id]
    elseif process isa ChangePointProcessIR
        switched = time >= world.change_times[process.target]
        return model.distributions[switched ? process.after_id : process.before_id]
    elseif process isa ActionProcessIR
        enabled = any(contingency.process_id == process.id &&
            get(world.contingency_enabled, contingency.id, false)
            for contingency in values(model.contingencies))
        return model.distributions[
            enabled && previous_action == process.action &&
                previous_success === true ?
                process.action_id : process.baseline_id]
    elseif process isa CoupledProcessIR
        index = configuration_index(model, process.source_factors, prior)
        return model.distributions[process.transition_ids[index]]
    end
    error("unimplemented process")
end

function update_world!(world::WorldState, model::CompiledModel,
        protocol::ProtocolIR, arm::String, seed::UInt64, time::Int,
        previous_action, previous_success = nothing)
    tick = model.development_horizon + time
    tick == 0 && return
    prior = copy(world.truth)
    updates = Dict{String,String}()
    for id in sort!(collect(keys(model.processes)))
        process = model.processes[id]
        tick % getfield(process, :update_interval) == 0 || continue
        distribution = process_distribution(
            model, process, prior, world, previous_action, previous_success,
            time)
        component = rng_component_id(protocol, arm, :process, id)
        u = counter_uniform(seed, :process, component, tick, 0)
        if distribution isa CategoricalDistributionIR
            updates[getfield(process, :target)] = inverse_categorical(
                distribution.values, distribution.probabilities, u)
        else
            values, probabilities = transition_values(distribution,
                prior[getfield(process, :target)])
            updates[getfield(process, :target)] =
                inverse_categorical(values, probabilities, u)
        end
    end
    merge!(world.truth, updates)
end

function emission_probabilities(model::CompiledModel, emission::EmissionIR,
        truth::Dict{String,String}, reliability::Float64)
    index = configuration_index(model, emission.source_factors, truth)
    distribution = model.distributions[
        emission.conditional_distribution_ids[index]]
    distribution isa CategoricalDistributionIR ||
        error("discrete emission must reference categorical distributions")
    n = length(distribution.values)
    probabilities = reliability .* distribution.probabilities .+
        (1 - reliability) / n
    return distribution.values, probabilities
end

normal_cdf(value) = 0.5 * erfc(-value / sqrt(2.0))

function configuration_at(model::CompiledModel, factors::Vector{String},
        index::Int)
    values = Vector{String}(undef, length(factors))
    remainder = index - 1
    for position in length(factors):-1:1
        support = model.factors[factors[position]].values
        values[position] = support[remainder % length(support) + 1]
        remainder ÷= length(support)
    end
    return values
end

function observation_likelihoods(model::CompiledModel, emission::EmissionIR,
        value, reliability::Float64; scale::Union{Nothing,Float64} = nothing,
        bounds::Union{Nothing,Tuple{Float64,Float64}} = nothing)
    likelihoods = Dict{String,Float64}()
    marginal = Dict{String,Vector{Float64}}()
    for factor_id in emission.source_factors
        for factor_value in model.factors[factor_id].values
            marginal["$factor_id=$factor_value"] = Float64[]
        end
    end
    count = prod(length(model.factors[id].values)
        for id in emission.source_factors)
    for index in 1:count
        config = configuration_at(model, emission.source_factors, index)
        probability = if emission.likelihood_family == :gaussian_bounded
            mean_value = emission.means[index]
            lower_mass = normal_cdf((bounds[1] - mean_value) / scale)
            upper_mass = normal_cdf((bounds[2] - mean_value) / scale)
            exp(-0.5 * ((value - mean_value) / scale)^2) /
                (scale * sqrt(2pi) * max(upper_mass - lower_mass, eps()))
        else
            distribution = model.distributions[
                emission.conditional_distribution_ids[index]]
            position = findfirst(==(value), distribution.values)
            base = distribution.probabilities[position]
            reliability * base +
                (1 - reliability) / length(distribution.values)
        end
        joint_key = "joint|" * join(("$factor_id=$factor_value"
            for (factor_id, factor_value) in
                zip(emission.source_factors, config)), ";")
        likelihoods[joint_key] = probability
        for (factor_id, factor_value) in zip(emission.source_factors, config)
            push!(marginal["$factor_id=$factor_value"], probability)
        end
    end
    for (key, values) in marginal
        likelihoods[key] = isempty(values) ? 1.0 : mean(values)
    end
    return likelihoods
end

function learned_observation_likelihoods(state::OrganismState,
        model::CompiledModel, emission::EmissionIR, value,
        reliability::Float64; scale::Union{Nothing,Float64} = nothing,
        bounds::Union{Nothing,Tuple{Float64,Float64}} = nothing)
    emission.likelihood_family == :gaussian_bounded &&
        return observation_likelihoods(model, emission, value, reliability;
            scale = scale, bounds = bounds)
    likelihoods = Dict{String,Float64}()
    marginal = Dict{String,Vector{Float64}}()
    for factor_id in emission.source_factors
        for factor_value in model.factors[factor_id].values
            marginal["$factor_id=$factor_value"] = Float64[]
        end
    end
    concentration = model.genome["dirichlet_concentration"]
    count = prod(length(model.factors[id].values)
        for id in emission.source_factors)
    for index in 1:count
        config = configuration_at(model, emission.source_factors, index)
        distribution_id = emission.conditional_distribution_ids[index]
        distribution =
            model.distributions[distribution_id]::CategoricalDistributionIR
        counts = state.likelihood_counts[distribution_id]
        learned = counts ./ sum(counts)
        experience = max(sum(counts) -
            concentration * length(counts), 0.0)
        weight = experience /
            (experience + concentration * length(counts))
        probabilities = (1 - weight) .* distribution.probabilities .+
            weight .* learned
        position = findfirst(==(value), distribution.values)
        probability = reliability * probabilities[position] +
            (1 - reliability) / length(distribution.values)
        joint_key = "joint|" * join(("$factor_id=$factor_value"
            for (factor_id, factor_value) in
                zip(emission.source_factors, config)), ";")
        likelihoods[joint_key] = probability
        for (factor_id, factor_value) in zip(emission.source_factors, config)
            push!(marginal["$factor_id=$factor_value"], probability)
        end
    end
    for (key, entries) in marginal
        likelihoods[key] = isempty(entries) ? 1.0 : mean(entries)
    end
    return likelihoods
end

function predictive_log_likelihood(state::OrganismState,
        model::CompiledModel, observation::Observation)
    if observation.emission_id !== nothing
        emission = model.emissions[observation.emission_id]
        count = prod(length(model.factors[id].values)
            for id in emission.source_factors)
        probability = 0.0
        for index in 1:count
            config = configuration_at(model, emission.source_factors, index)
            key = "joint|" * join(("$factor_id=$factor_value"
                for (factor_id, factor_value) in
                    zip(emission.source_factors, config)), ";")
            prior = prod(state.factor_beliefs[factor_id][
                findfirst(==(factor_value), model.factors[factor_id].values)]
                for (factor_id, factor_value) in
                    zip(emission.source_factors, config); init = 1.0)
            probability += prior * observation.log_likelihoods[key]
        end
        return log(max(probability, eps()))
    end
    contributions = Float64[]
    for factor_id in observation.scope
        haskey(state.factor_beliefs, factor_id) || continue
        factor_id in observation.masked_scope && continue
        factor = model.factors[factor_id]
        likelihood = [get(observation.log_likelihoods,
            "$factor_id=$value", 1.0) for value in factor.values]
        push!(contributions,
            log(max(dot(state.factor_beliefs[factor_id], likelihood), eps())))
    end
    return isempty(contributions) ? 0.0 : sum(contributions)
end

function marginal_equivalence_error(state::OrganismState,
        model::CompiledModel, observation::Observation)
    observation.emission_id === nothing && return 0.0
    emission = model.emissions[observation.emission_id]
    length(emission.source_factors) <= 1 && return 0.0
    joint_log = predictive_log_likelihood(state, model, observation)
    marginal_log = 0.0
    for factor_id in emission.source_factors
        factor_id in observation.masked_scope && continue
        factor = model.factors[factor_id]
        probability = sum(state.factor_beliefs[factor_id][index] *
            observation.log_likelihoods["$factor_id=$value"]
            for (index, value) in enumerate(factor.values))
        marginal_log += log(max(probability, eps()))
    end
    return abs(joint_log - marginal_log)
end

function account_observation(observation::Observation,
        state::OrganismState, model::CompiledModel)
    likelihoods = observation.emission_id === nothing ?
        observation.log_likelihoods :
        learned_observation_likelihoods(state, model,
            model.emissions[observation.emission_id], observation.value,
            observation.reliability; scale = observation.effective_scale,
            bounds = model.channels[observation.channel_id].bounds)
    adjusted = Observation(observation.event_id, observation.time,
        observation.source, observation.channel_id, observation.emission_id,
        observation.scope, observation.masked_scope, observation.family,
        observation.value, observation.reliability,
        observation.effective_scale, likelihoods, 0.0, 0.0,
        observation.is_imaginal, observation.rng_namespace)
    equivalence_error = marginal_equivalence_error(
        state, model, adjusted)
    return Observation(adjusted.event_id, adjusted.time,
        adjusted.source, adjusted.channel_id, adjusted.emission_id,
        adjusted.scope, adjusted.masked_scope, adjusted.family,
        adjusted.value, adjusted.reliability, adjusted.effective_scale,
        adjusted.log_likelihoods,
        predictive_log_likelihood(state, model, adjusted),
        equivalence_error,
        adjusted.is_imaginal, adjusted.rng_namespace)
end

function generate_observation(model::CompiledModel, world::WorldState,
        protocol::ProtocolIR, arm::String, seed::UInt64, event_id::String,
        time::Int, emission_id::String, occurrence::Int,
        scalar_occurrence::Int = occurrence)
    emission = model.emissions[emission_id]
    channel = model.channels[emission.channel_id]
    tick = model.development_horizon + time
    episode_first_tick = tick - tick % model.episode_length
    component = rng_component_id(protocol, arm, :emission, emission_id)
    reliability_distribution = model.distributions[emission.reliability_id]
    reliability_component = scalar_component(
        reliability_distribution, protocol, arm)
    reliability = scalar_draw(reliability_distribution, seed,
        reliability_component, tick, episode_first_tick, scalar_occurrence)
    u = counter_uniform(seed, :emission, component, tick, occurrence)
    if emission.likelihood_family == :gaussian_bounded
        index = configuration_index(model, emission.source_factors, world.truth)
        mean_value = emission.means[index]
        scale_distribution = model.distributions[emission.noise_scale_id]
        scale_component = scalar_component(scale_distribution, protocol, arm)
        scale = scalar_draw(scale_distribution, seed, scale_component,
            tick, episode_first_tick, scalar_occurrence) /
            max(reliability, 1e-6)
        lower_probability = normal_cdf((channel.bounds[1] - mean_value) / scale)
        upper_probability = normal_cdf((channel.bounds[2] - mean_value) / scale)
        probability = lower_probability +
            u * (upper_probability - lower_probability)
        z = sqrt(2.0) * erfinv(2probability - 1)
        value = clamp(mean_value + scale * z,
            channel.bounds[1], channel.bounds[2])
        likelihoods = observation_likelihoods(model, emission, value,
            reliability; scale = scale, bounds = channel.bounds)
        effective_scale = scale
    else
        values, probabilities = emission_probabilities(
            model, emission, world.truth, reliability)
        value = inverse_categorical(values, probabilities, u)
        likelihoods = observation_likelihoods(
            model, emission, value, reliability)
        effective_scale = nothing
    end
    visible_scope = unique(vcat(emission.source_factors, channel.scope))
    return Observation(event_id, time, channel.source, channel.id, emission_id,
        visible_scope, emission.masked_scope,
        emission.likelihood_family, value, reliability, effective_scale,
        likelihoods, 0.0, 0.0, false,
        "emission:$component;distribution:$reliability_component;" *
        "scalar_ordinal=$scalar_occurrence")
end

function joint_coordination(state::OrganismState, model::CompiledModel)
    label = state.selected_policy_label
    label === nothing && return 1.0
    occursin('=', label) || return 1.0
    action_by_actor = Dict(String(first(split(pair, '='; limit = 2))) =>
        String(last(split(pair, '='; limit = 2)))
        for pair in split(label, ';'))
    isempty(action_by_actor) && return 1.0
    reconciled = state.selected_action
    actor_agreement = mean(action == reconciled ? 1.0 : 0.0
        for action in values(action_by_actor))
    active_cross = [edge for edge in values(model.edges)
        if edge.kind == :protector_cross_prediction &&
            get(state.edge_enabled, edge.id, false) &&
            haskey(action_by_actor, edge.source) &&
            haskey(action_by_actor, edge.target)]
    isempty(active_cross) && return actor_agreement
    edge_agreement = mean(
        action_by_actor[edge.source] == action_by_actor[edge.target] ?
            1.0 : 0.0 for edge in active_cross)
    return mean((actor_agreement, edge_agreement))
end

function generate_outcomes!(state::OrganismState, world::WorldState,
        model::CompiledModel, protocol::ProtocolIR, arm::String,
        seed::UInt64, time::Int)
    state.action_success = nothing
    state.delivered_exposure = nothing
    state.potential_hazard = nothing
    state.realized_hazard = nothing
    action = state.selected_action
    action === nothing && return
    tick = model.development_horizon + time
    action_mapping = findfirst(outcome ->
        outcome isa ActionOutcomeIR && outcome.action == action,
        collect(values(model.outcomes)))
    if action_mapping !== nothing
        outcome = collect(values(model.outcomes))[action_mapping]
        index = configuration_index(model, outcome.source_factors, world.truth)
        component = rng_component_id(protocol, arm, :outcome, outcome.id)
        success_probability = outcome.success_probabilities[index] *
            joint_coordination(state, model)
        success = counter_uniform(
            seed, :outcome, component, tick, 0) < success_probability
        state.action_success = success
        state.delivered_exposure = success ? outcome.exposure_values[index] : 0.0
    end
    hazards = [outcome for outcome in values(model.outcomes)
        if outcome isa HazardOutcomeIR]
    if !isempty(hazards)
        outcome = only(hazards)
        index = configuration_index(model, outcome.source_factors, world.truth)
        component = rng_component_id(protocol, arm, :outcome, outcome.id)
        potential = counter_uniform(
            seed, :outcome, component, tick, 0) < outcome.probabilities[index]
        state.potential_hazard = potential
        state.realized_hazard = potential &&
            !(state.action_success === true && action in outcome.mitigating_actions)
    end
end
