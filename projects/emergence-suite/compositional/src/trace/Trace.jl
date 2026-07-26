function set_if!(fields::Dict{String,Any}, path::String, value)
    value === nothing || (fields[path] = value)
end

function state_fields(state::OrganismState, model::CompiledModel,
        world::WorldState)
    fields = Dict{String,Any}()
    for (id, node) in model.nodes
        node.active || continue
        values = state.node_values[id]
        prefix = node.kind == :BundleNode ? "state.bundle" :
            node.kind == :ContextNode ? "state.context" :
            node.kind == :CueNode ? "state.cue" :
            node.kind == :LocalPrecisionNode ? "state.local_precision" :
            node.kind == :GlobalPrecisionNode ? "state.global_precision" :
            node.kind == :ProtectorNode ? "state.protector" :
            node.kind == :PartnerNode ? "state.partner" :
            node.kind == :AccessNode ? "state.access" :
            node.kind == :EpisodeNode ? "state.episode" :
            node.kind == :StructureNode ? "state.structure" : ""
        for (field, value) in values
            fields["$prefix.$id.$field"] = value
        end
        if node.kind == :ContextNode
            for (factor_id, belief) in state.factor_beliefs
                factor = model.factors[factor_id]
                for (value, probability) in zip(factor.values, belief)
                    fields["state.context.$id.posterior.$factor_id.$value"] =
                        probability
                end
            end
        end
    end
    selected = selected_candidates(state, model)
    for (id, candidate) in model.candidates
        node = candidate.structure_node
        fields["state.structure.$node.log_evidence.$id"] =
            state.structure_evidence[id]
        fields["state.structure.$node.complexity.$id"] =
            state.structure_complexity[id]
        fields["state.structure.$node.selected.$id"] = selected[id]
    end
    for (label, probability) in state.policy_posterior
        fields["policy.joint.posterior.$label"] = probability
        fields["policy.joint.expected_free_energy.$label"] =
            state.policy_gfe[label]
    end
    protectors = [id for (id, node) in model.nodes
        if node.active && node.kind == :ProtectorNode]
    for id in protectors
        fields["policy.protector.$id.permission_probability"] =
            state.node_values[id]["permission_probability"]
    end
    access = [state.node_values[id]["probability"] for (id, node) in model.nodes
        if node.active && node.kind == :AccessNode]
    fields["policy.access_probability"] = isempty(access) ? 0.0 : mean(access)
    for (id, strength) in state.edge_strength
        fields["learning.edge.$id.strength"] = strength
    end
    for (factor_id, belief) in state.factor_beliefs
        matching = [counts for (id, counts) in state.likelihood_counts
            if any(emission -> factor_id in emission.source_factors &&
                id in emission.conditional_distribution_ids,
                values(model.emissions))]
        fields["learning.parameter.$factor_id.value"] = isempty(matching) ?
            maximum(belief) :
            mean(maximum(counts ./ sum(counts)) for counts in matching)
    end
    for (factor_id, value) in world.truth
        fields["world.truth.$factor_id"] = value
    end
    set_if!(fields, "action.selected", state.selected_action)
    set_if!(fields, "action.success", state.action_success)
    set_if!(fields, "action.delivered_exposure", state.delivered_exposure)
    set_if!(fields, "world.potential_hazard", state.potential_hazard)
    set_if!(fields, "world.realized_hazard", state.realized_hazard)
    return fields
end

function base_fields(seed::UInt64, arm::String, time::Int, episode::Int,
        row_index::Int, row_kind::String, genome_id::String)
    Dict{String,Any}(
        "run.seed" => seed, "run.arm" => arm, "run.time" => time,
        "run.episode" => episode, "run.row_index" => row_index,
        "run.row_kind" => row_kind, "run.genome_id" => genome_id,
    )
end

function tick_row(seed::UInt64, arm::String, time::Int, episode::Int,
        row_index::Int, stopped::Bool, reason::String, state::OrganismState,
        model::CompiledModel, world::WorldState)
    fields = base_fields(seed, arm, time, episode, row_index, "tick",
        model.genome_id)
    merge!(fields, state_fields(state, model, world))
    fields["run.stopped"] = stopped
    fields["run.stop_reason"] = reason
    for process in values(model.processes)
        process isa ChangePointProcessIR || continue
        fields["world.process.$(process.target).switch"] =
            time >= world.change_times[process.target]
    end
    return TickTraceRow(seed, arm, time, episode, row_index, stopped,
        reason, fields)
end

function event_row(seed::UInt64, arm::String, time::Int, episode::Int,
        row_index::Int, event_index::Int, event_id::String, kind::Symbol,
        executed::Bool, extra::Dict{String,Any}, genome_id::String)
    fields = base_fields(seed, arm, time, episode, row_index, "event",
        genome_id)
    merge!(fields, Dict{String,Any}(
        "run.event_index" => event_index, "run.event_id" => event_id,
        "run.event_kind" => String(kind), "run.event_executed" => executed,
    ))
    merge!(fields, extra)
    return EventTraceRow(seed, arm, time, episode, row_index, event_index,
        event_id, kind, executed, fields)
end

function trace_hash(trace::TraceTable)
    lines = String[]
    for row in trace.rows
        fields = getfield(row, :fields)
        push!(lines, join(("$key=$(repr(fields[key]))"
            for key in sort!(collect(keys(fields)))), "\t"))
    end
    return bytes2hex(sha256(join(lines, "\n") * "\n"))
end

function initialization_hash(trace::TraceTable)
    lines = [join((
        "seed=$(row.seed)", "arm=$(row.arm)", "tick=$(row.tick)",
        "time=$(row.time)", "emission=$(row.emission_id)",
        "rng=$(row.rng_namespace)", "update=$(row.update_provenance)",
        "candidates=$(join(row.model_candidates, ','))"), "\t")
        for row in trace.initialization_rows]
    return bytes2hex(sha256(join(lines, "\n") * "\n"))
end

function field_matches(pattern::String, path::String)
    occursin('*', pattern) || return pattern == path
    pieces = split(pattern, '*'; keepempty = true)
    length(pieces) == 2 || return false
    return startswith(path, pieces[1]) && endswith(path, pieces[2])
end

function audit_requested_fields(trace::TraceTable, protocol::ProtocolIR)
    all_paths = Set(path for row in trace.rows for path in keys(row.fields))
    missing = String[]
    for pattern in protocol.requested_fields
        any(path -> field_matches(pattern, path), all_paths) ||
            push!(missing, pattern)
    end
    return missing
end
