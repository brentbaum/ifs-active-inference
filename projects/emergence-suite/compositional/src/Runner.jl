struct ScheduledOccurrence
    time::Int
    phase::Int
    ordinal::Int
    repeat_index::Int
    event_index::Int
    expanded_id::String
    event::EventIR
end

event_phase(event::InterventionEventIR) = 1
event_phase(event::ObservationEventIR) = 3
event_phase(event::StopEventIR) = 8

function expand_schedule(arm::ArmIR)
    raw = Tuple{Int,Int,Int,Int,String,EventIR}[]
    for (ordinal, event) in enumerate(arm.events)
        repeats = event isa ObservationEventIR ? event.repeat : 1
        interval = event isa ObservationEventIR ? event.interval : 1
        for repeat_index in 0:(repeats - 1)
            time = getfield(event, :time) + repeat_index * interval
            push!(raw, (time, event_phase(event), ordinal, repeat_index,
                "$(getfield(event, :id))#$repeat_index", event))
        end
    end
    sort!(raw; by = item -> item[1:4])
    return ScheduledOccurrence[ScheduledOccurrence(item[1], item[2], item[3],
        item[4], index - 1, item[5], item[6])
        for (index, item) in enumerate(raw)]
end

function scalar_event_ordinals(occurrences::Vector{ScheduledOccurrence})
    consumers = sort!([item for item in occurrences
        if item.phase == 3 &&
            (item.event::ObservationEventIR).emission_id !== nothing];
        by = item -> (
            String((item.event::ObservationEventIR).kind),
            something((item.event::ObservationEventIR).emission_id, ""),
            item.expanded_id))
    return Dict(item.expanded_id => index - 1
        for (index, item) in enumerate(consumers))
end

function compare_value(left, comparator::Symbol, right)
    comparator == :eq && return left == right
    comparator == :ne && return left != right
    comparator == :gt && return left isa Number && left > right
    comparator == :ge && return left isa Number && left >= right
    comparator == :lt && return left isa Number && left < right
    comparator == :le && return left isa Number && left <= right
    comparator == :in && return left in right
    error("unknown comparator: $comparator")
end

function trigger_passes(trigger::Union{Nothing,TriggerIR},
        trace::TraceTable, state::OrganismState, model::CompiledModel,
        world::WorldState, time::Int)
    trigger === nothing && return true
    context = Dict{String,Any}("run.time" => time)
    prior_ticks = [row for row in trace.rows if row isa TickTraceRow &&
        row.time < time]
    if !isempty(prior_ticks)
        prior = sort!(prior_ticks; by = row -> row.row_index)[end]
        merge!(context, prior.fields)
    else
        for (path, value) in state_fields(state, model, world)
            (startswith(path, "state.") || startswith(path, "policy.")) &&
                (context[path] = value)
        end
    end
    observations = [row for row in trace.rows if row isa EventTraceRow &&
        row.time < time && row.executed &&
        haskey(row.fields, "observation.source")]
    if !isempty(observations)
        prior = sort!(observations; by = row -> row.row_index)[end]
        for (key, value) in prior.fields
            startswith(key, "observation.") && (context[key] = value)
        end
    end
    haskey(context, trigger.field) || return false
    return compare_value(context[trigger.field], trigger.comparator, trigger.value)
end

function apply_operation(current::Bool, operation::Symbol)
    operation in (:disable, :sever) && return false
    operation == :enable && return true
    operation == :toggle && return !current
    error("unknown intervention operation: $operation")
end

function apply_intervention!(state::OrganismState, world::WorldState,
        model::CompiledModel, intervention::InterventionIR)
    if intervention.target_kind == :edge
        current = state.edge_enabled[intervention.target_id]
        state.edge_enabled[intervention.target_id] =
            apply_operation(current, intervention.operation)
    elseif intervention.target_kind == :observation_channel
        current = state.channel_enabled[intervention.target_id]
        state.channel_enabled[intervention.target_id] =
            apply_operation(current, intervention.operation)
    elseif intervention.target_kind == :policy_action
        current = state.action_enabled[intervention.target_id]
        state.action_enabled[intervention.target_id] =
            apply_operation(current, intervention.operation)
    elseif intervention.target_kind == :world_contingency
        current = world.contingency_enabled[intervention.target_id]
        world.contingency_enabled[intervention.target_id] =
            apply_operation(current, intervention.operation)
    else
        error("unknown intervention target kind: $(intervention.target_kind)")
    end
end

function imaginal_observation(state::OrganismState, model::CompiledModel,
        event::ObservationEventIR, event_id::String, time::Int)
    channel = model.channels[event.channel_id]
    related = [emission for emission in values(model.emissions)
        if !isempty(intersect(Set(model.channels[emission.channel_id].scope),
            Set(channel.scope)))]
    likelihoods = Dict{String,Float64}()
    factor_scope = sort!(unique(factor_id for emission in related
        for factor_id in emission.source_factors))
    if channel.likelihood_family == :gaussian_bounded
        predictions = Float64[]
        for emission in related
            emission.likelihood_family == :gaussian_bounded || continue
            configurations = length(emission.means)
            for index in 1:configurations
                config = configuration_at(model, emission.source_factors, index)
                weight = prod(state.factor_beliefs[factor_id][
                    findfirst(==(factor_value), model.factors[factor_id].values)]
                    for (factor_id, factor_value) in
                        zip(emission.source_factors, config); init = 1.0)
                push!(predictions, weight * emission.means[index])
            end
        end
        node_prediction = mean(primary_value(state, model, id)
            for id in channel.scope if haskey(state.node_values, id))
        value = isempty(predictions) ?
            channel.bounds[1] +
                node_prediction * (channel.bounds[2] - channel.bounds[1]) :
            clamp(sum(predictions), channel.bounds[1], channel.bounds[2])
    else
        probabilities = Dict(label => 0.0 for label in channel.values)
        contributors = 0
        for emission in related
            emission.likelihood_family == :gaussian_bounded && continue
            source_channel = model.channels[emission.channel_id]
            Set(source_channel.values) == Set(channel.values) || continue
            contributors += 1
            for (index, distribution_id) in
                    enumerate(emission.conditional_distribution_ids)
                config = configuration_at(model, emission.source_factors, index)
                weight = prod(state.factor_beliefs[factor_id][
                    findfirst(==(factor_value), model.factors[factor_id].values)]
                    for (factor_id, factor_value) in
                        zip(emission.source_factors, config); init = 1.0)
                distribution = model.distributions[distribution_id]
                learned = state.likelihood_counts[distribution_id]
                learned_probabilities = learned ./ sum(learned)
                for label in channel.values
                    label_index = findfirst(==(label), distribution.values)
                    probabilities[label] +=
                        weight * learned_probabilities[label_index]
                end
            end
        end
        if contributors == 0
            fill_probability = 1 / length(channel.values)
            for label in channel.values
                probabilities[label] = fill_probability
            end
        else
            for label in channel.values
                probabilities[label] /= contributors
            end
        end
        root_messages = Vector{Vector{Float64}}()
        root_strengths = Float64[]
        for cue_id in channel.scope
            haskey(model.nodes, cue_id) || continue
            model.nodes[cue_id].kind == :CueNode || continue
            for edge in values(model.edges)
                edge.kind == :cue_root && edge.source == cue_id &&
                    get(state.edge_enabled, edge.id, false) || continue
                push!(root_messages, project_distribution(
                    state.node_beliefs[edge.target], length(channel.values)))
                push!(root_strengths, state.edge_strength[edge.id])
            end
        end
        if !isempty(root_messages)
            learned_root = normalize_distribution(
                reduce((left, right) -> left .* right, root_messages))
            strength = mean(root_strengths)
            for (index, label) in enumerate(channel.values)
                probabilities[label] = (1 - strength) * probabilities[label] +
                    strength * learned_root[index]
            end
            total = sum(values(probabilities))
            for label in channel.values
                probabilities[label] /= total
            end
        end
        value = sort!(copy(channel.values);
            by = label -> (-probabilities[label], label))[1]
        for emission in related
            emission.likelihood_family == :gaussian_bounded && continue
            source_channel = model.channels[emission.channel_id]
            Set(source_channel.values) == Set(channel.values) || continue
            for factor_id in emission.source_factors
                factor = model.factors[factor_id]
                for factor_value in factor.values
                    terms = Float64[]
                    for (index, distribution_id) in
                            enumerate(emission.conditional_distribution_ids)
                        config = configuration_at(
                            model, emission.source_factors, index)
                        position = findfirst(==(factor_id),
                            emission.source_factors)
                        config[position] == factor_value || continue
                        distribution = model.distributions[distribution_id]
                        counts = state.likelihood_counts[distribution_id]
                        label_index = findfirst(==(value), distribution.values)
                        push!(terms, counts[label_index] / sum(counts))
                    end
                    likelihoods["$factor_id=$factor_value"] =
                        isempty(terms) ? 1.0 : mean(terms)
                end
            end
        end
    end
    return Observation(event_id, time, :imaginal, channel.id, nothing,
        unique(vcat(channel.scope, factor_scope)), Set{String}(),
        channel.likelihood_family, value,
        1.0, nothing, likelihoods, 0.0, 0.0, true,
        "posterior-predictive-mode-v1")
end

function observation_fields(observation::Observation,
        candidate_scores::Dict{String,Float64})
    fields = Dict{String,Any}(
        "observation.source" => String(observation.source),
        "observation.scope_size" => length(observation.scope) -
            length(observation.masked_scope),
        "observation.is_imaginal" => observation.is_imaginal,
        "_observation.scope_ids" => copy(observation.scope),
        "observation.delivered_log_likelihood" =>
            observation.delivered_log_likelihood,
        "observation.marginal_equivalence_error" =>
            observation.marginal_equivalence_error,
        "provenance.update_function" => "common-observation-update-v1",
        "provenance.observation_event_id" => observation.event_id,
        "provenance.rng_namespace" => observation.rng_namespace,
    )
    for (candidate, score) in candidate_scores
        fields["observation.log_likelihood.$candidate"] = score
    end
    fields["provenance.model_candidate"] = isempty(candidate_scores) ? "" :
        first(sort!(collect(keys(candidate_scores));
            by = id -> (-candidate_scores[id], id)))
    return fields
end

function stopping_satisfied(rule::StoppingRuleIR, trace::TraceTable,
        current_tick::TickTraceRow)
    current_tick.time >= rule.max_time && return true
    rule.kind == :fixed_horizon && return false
    rule.field === nothing && return false
    ticks = sort!([row for row in trace.rows if row isa TickTraceRow &&
        haskey(row.fields, rule.field) && row.time <= current_tick.time];
        by = row -> row.time)
    length(ticks) >= rule.persistence || return false
    recent = ticks[(end - rule.persistence + 1):end]
    all(diff([row.time for row in recent]) .== 1) || return false
    return all(compare_value(row.fields[rule.field], rule.comparator,
        rule.threshold) for row in recent)
end

function replay_development!(state::OrganismState, world::WorldState,
        model::CompiledModel, protocol::ProtocolIR, arm::String, seed::UInt64)
    ledger = InitializationAuditRow[]
    for tick in 0:(model.development_horizon - 1)
        time = tick - model.development_horizon
        tick > 0 && update_world!(world, model, protocol, arm, seed,
            time, nothing, nothing)
        predict_factors!(state, model; time = time)
        for (occurrence, emission_id) in enumerate(
                sort!(copy(model.development_emission_ids)))
            observation = generate_observation(model, world, protocol, arm,
                seed, "development-$tick-$emission_id", time, emission_id,
                occurrence - 1, occurrence - 1)
            observation = account_observation(observation, state, model)
            candidate_scores = score_structures!(state, model, observation)
            infer!(state, model, observation)
            learn!(state, model, observation)
            push!(ledger, InitializationAuditRow(seed, arm, tick, time,
                emission_id, observation.rng_namespace,
                "common-observation-update-v1",
                sort!(collect(keys(candidate_scores)))))
        end
    end
    return ledger
end

function run_arm(model::CompiledModel, protocol::ProtocolIR, arm::ArmIR,
        seed::UInt64)
    state = initialize_state(model)
    world = initialize_world(model, protocol, arm.id, seed)
    ledger = replay_development!(
        state, world, model, protocol, arm.id, seed)
    trace = TraceTable(AbstractTraceRow[], protocol.budgets, model.horizon,
        ledger)
    schedule = expand_schedule(arm)
    row_index = 0
    stopped = false
    for time in 0:(model.horizon - 1)
        occurrences = [item for item in schedule if item.time == time]
        for occurrence in occurrences
            occurrence.phase == 1 || continue
            event = occurrence.event::InterventionEventIR
            passes = trigger_passes(
                event.trigger, trace, state, model, world, time)
            intervention = protocol.interventions[event.intervention_id]
            if passes
                apply_intervention!(state, world, model, intervention)
            end
            extra = Dict{String,Any}(
                "provenance.update_function" =>
                    "typed-intervention-$(intervention.operation)",
                "provenance.edge_id" =>
                    intervention.target_kind == :edge ?
                        intervention.target_id : "",
            )
            push!(trace.rows, event_row(seed, arm.id, time,
                (model.development_horizon + time) ÷ model.episode_length,
                row_index, occurrence.event_index, occurrence.expanded_id,
                :intervene, passes, extra, model.genome_id))
            row_index += 1
        end
        update_world!(world, model, protocol, arm.id, seed, time,
            state.selected_action, state.action_success)
        predict_factors!(state, model; time = time)
        emission_ordinals = Dict{String,Int}()
        scalar_ordinals = scalar_event_ordinals(occurrences)
        for occurrence in occurrences
            occurrence.phase == 3 || continue
            event = occurrence.event::ObservationEventIR
            emission_key = something(event.emission_id, event.channel_id)
            ordinal = get(emission_ordinals, emission_key, 0)
            emission_ordinals[emission_key] = ordinal + 1
            passes = trigger_passes(
                event.trigger, trace, state, model, world, time) &&
                get(state.channel_enabled, event.channel_id, false)
            extra = Dict{String,Any}()
            if passes
                observation = event.kind == :imaginal ?
                    imaginal_observation(state, model, event,
                        occurrence.expanded_id, time) :
                    generate_observation(model, world, protocol, arm.id, seed,
                        occurrence.expanded_id, time, event.emission_id, ordinal,
                        scalar_ordinals[occurrence.expanded_id])
                observation = account_observation(observation, state, model)
                event_scores = event.kind in (:observe, :imaginal) ?
                    score_structures!(state, model, observation) :
                    candidate_scores(state, model, observation)
                infer!(state, model, observation)
                merge!(extra, observation_fields(
                    observation, event_scores))
                if event.kind == :observe
                    learn!(state, model, observation)
                end
            end
            push!(trace.rows, event_row(seed, arm.id, time,
                (model.development_horizon + time) ÷ model.episode_length,
                row_index, occurrence.event_index, occurrence.expanded_id,
                event.kind, passes, extra, model.genome_id))
            row_index += 1
        end
        if !infer_policy!(state, model)
            state.selected_action = nothing
            state.action_success = nothing
            state.delivered_exposure = nothing
            state.potential_hazard = nothing
            state.realized_hazard = nothing
            push!(trace.rows, tick_row(seed, arm.id, time,
                (model.development_horizon + time) ÷ model.episode_length,
                row_index, true,
                "architecture_failure:empty-policy-support",
                state, model, world))
            break
        end
        generate_outcomes!(state, world, model, protocol, arm.id, seed, time)
        learn_outcomes!(state, model)
        tick = tick_row(seed, arm.id, time,
            (model.development_horizon + time) ÷ model.episode_length,
            row_index, false, "", state, model, world)
        push!(trace.rows, tick)
        row_index += 1
        for occurrence in occurrences
            occurrence.phase == 8 || continue
            event = occurrence.event::StopEventIR
            passes = trigger_passes(
                event.trigger, trace, state, model, world, time)
            satisfied = passes &&
                stopping_satisfied(protocol.stopping_rules[event.rule_id],
                    trace, tick)
            reason = satisfied ? "stopping_rule:$(event.rule_id)" : ""
            extra = Dict{String,Any}(
                "run.stopped" => satisfied, "run.stop_reason" => reason,
                "provenance.update_function" => "typed-stop-check-v1",
            )
            push!(trace.rows, event_row(seed, arm.id, time,
                tick.episode, row_index, occurrence.event_index,
                occurrence.expanded_id, :stop_check, passes, extra,
                model.genome_id))
            row_index += 1
            if satisfied
                stopped = true
                break
            end
        end
        stopped && break
    end
    return trace
end

function run_protocol(model::CompiledModel, protocol::ProtocolIR,
        seed::Integer)
    combined = TraceTable(AbstractTraceRow[], protocol.budgets, model.horizon)
    for arm in protocol.arms
        trace = run_arm(model, protocol, arm, UInt64(seed))
        append!(combined.rows, trace.rows)
        append!(combined.initialization_rows, trace.initialization_rows)
    end
    missing = audit_requested_fields(combined, protocol)
    isempty(missing) ||
        error("requested trace fields were not produced: $(join(missing, ", "))")
    return combined
end

function execute_bundle(directory::AbstractString, genome_path::AbstractString,
        seed::Integer)
    documents = load_documents(directory)
    genome = load_genome(genome_path)
    model = compile_model(documents, genome)
    protocol = compile_protocol(documents.protocol)
    analysis = compile_analysis(documents.analysis)
    trace = run_protocol(model, protocol, seed)
    return trace, evaluate_trace(trace, analysis)
end
