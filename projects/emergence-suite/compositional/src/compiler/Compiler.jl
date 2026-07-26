function leaf_paths(value, prefix = "")
    paths = String[]
    if value isa AbstractDict
        for key in sort!(String.(collect(keys(value))))
            child = isempty(prefix) ? key : "$prefix.$key"
            append!(paths, leaf_paths(value[key], child))
        end
    elseif value isa AbstractVector
        for (index, item) in enumerate(value)
            append!(paths, leaf_paths(item, "$prefix[$index]"))
        end
    else
        push!(paths, prefix)
    end
    return paths
end

function consumption_report(configuration, genome)
    report = Dict{String,String}()
    for path in leaf_paths(configuration)
        root = first(split(path, '.'))
        consumer = root in ("nodes", "edges", "observation_channels",
            "policy_families", "structure_candidates") ?
            "typed-graph-compiler:$root" : "typed-graph-compiler:identity"
        haskey(report, "configuration.$path") &&
            error("configuration field has multiple consumers: $path")
        report["configuration.$path"] = consumer
    end
    source_root = normpath(joinpath(@__DIR__, ".."))
    source_files = String[]
    for (directory, _, files) in walkdir(source_root)
        append!(source_files, [joinpath(directory, file)
            for file in files if endswith(file, ".jl")])
    end
    source_text = Dict(path => read(path, String) for path in source_files)
    for path in leaf_paths(genome)
        key = first(split(path, '.'))
        consumers = if startswith(path, "action_costs")
            [file for (file, text) in source_text
                if occursin("model.action_costs", text)]
        elseif path in ("genome_id", "contract_id", "contract_version")
            [@__FILE__]
        else
            needle = "genome[\"$key\"]"
            [file for (file, text) in source_text if occursin(needle, text)]
        end
        isempty(consumers) &&
            error("genome field has no runtime source consumer: $path")
        consumer = join(sort!(relpath.(consumers, Ref(source_root))), ",")
        report["genome.$path"] = consumer
    end
    return report
end

function canonical_genome_hash(genome)
    io = IOBuffer()
    TOML.print(io, genome; sorted = true)
    return bytes2hex(sha256(take!(io)))
end

function compile_distribution(raw)
    id = String(raw["id"])
    family = Symbol(raw["family"])
    if family == :fixed
        return FixedDistributionIR(id, Symbol(raw["sampling_scope"]),
            Float64(raw["value"]))
    elseif family == :uniform
        return UniformDistributionIR(id, Symbol(raw["sampling_scope"]),
            Float64(raw["lower"]), Float64(raw["upper"]))
    elseif family == :integer_uniform
        return IntegerUniformDistributionIR(id, Symbol(raw["sampling_scope"]),
            Int(raw["lower"]), Int(raw["upper"]))
    elseif family == :beta
        return BetaDistributionIR(id, Symbol(raw["sampling_scope"]),
            Float64(raw["alpha"]), Float64(raw["beta"]))
    elseif family == :categorical
        return CategoricalDistributionIR(id, String.(raw["values"]),
            Float64.(raw["probabilities"]))
    elseif family == :transition_matrix
        rows = [Float64.(row) for row in raw["matrix"]]
        return TransitionDistributionIR(
            id, String.(raw["values"]), reduce(vcat, permutedims.(rows)))
    end
    error("uncompiled distribution family: $family")
end

function compile_process(raw)
    id = String(raw["id"])
    kind = Symbol(raw["type"])
    interval = Int(raw["update_interval"])
    target = String(raw["target_factor"])
    kind == :iid && return IIDProcessIR(id, target,
        String(raw["distribution_id"]), interval)
    kind in (:markov, :drift) && return MarkovProcessIR(id, kind, target,
        String(raw["transition_distribution_id"]), interval)
    kind == :change_point && return ChangePointProcessIR(id, target,
        String(raw["before_transition_id"]), String(raw["after_transition_id"]),
        String(raw["change_time_distribution_id"]), interval)
    kind == :action_contingent && return ActionProcessIR(id, target,
        String(raw["action"]), String(raw["baseline_transition_id"]),
        String(raw["action_transition_id"]), interval)
    kind == :coupled_latent && return CoupledProcessIR(id, target,
        String.(raw["source_factors"]),
        String.(raw["conditional_transition_ids"]), interval)
    error("uncompiled process type: $kind")
end

function compile_emission(raw)
    family = Symbol(raw["likelihood_family"])
    return EmissionIR(
        String(raw["id"]),
        String.(raw["source_factors"]),
        String(raw["channel_id"]),
        family,
        String.(get(raw, "conditional_distribution_ids", String[])),
        Float64.(get(raw, "mean_by_configuration", Float64[])),
        haskey(raw, "noise_scale_distribution_id") ?
            String(raw["noise_scale_distribution_id"]) : nothing,
        String(raw["reliability_distribution_id"]),
        Set(String.(raw["masked_scope"])),
    )
end

function compile_outcome(raw)
    kind = Symbol(raw["type"])
    if kind == :action_outcome
        return ActionOutcomeIR(String(raw["id"]), String(raw["action"]),
            String.(raw["source_factors"]),
            Float64.(raw["success_probabilities"]),
            Float64.(raw["exposure_values"]))
    elseif kind == :hazard_outcome
        return HazardOutcomeIR(String(raw["id"]),
            String.(raw["source_factors"]),
            Float64.(raw["potential_probabilities"]),
            Set(String.(raw["mitigating_actions"])))
    end
    error("uncompiled outcome type: $kind")
end

function compile_model(documents::BundleDocuments, genome_raw)
    configuration = documents.configuration
    world = documents.world
    nodes = Dict(String(raw["id"]) => NodeIR(
        String(raw["id"]), Symbol(raw["type"]), Int(raw["cardinality"]),
        Int(raw["slot"]), Bool(raw["active"])) for raw in configuration["nodes"])
    edges = Dict(String(raw["id"]) => EdgeIR(
        String(raw["id"]), Symbol(raw["type"]), String(raw["from"]),
        String(raw["to"]), Symbol(raw["state"])) for raw in configuration["edges"])
    channels = Dict(String(raw["id"]) => ChannelIR(
        String(raw["id"]), Symbol(raw["source"]), String.(raw["scope"]),
        Symbol(raw["likelihood_family"]),
        String.(get(raw, "value_labels", String[])),
        haskey(raw, "bounds") ?
            Tuple(Float64.(raw["bounds"])) : nothing,
        Bool(raw["enabled"])) for raw in configuration["observation_channels"])
    policies = Dict(String(raw["id"]) => PolicyIR(
        String(raw["id"]), Symbol(raw["family"]),
        String.(raw["actor_nodes"]), String.(raw["actions"]),
        Bool(raw["enabled"])) for raw in configuration["policy_families"])
    candidates = Dict(String(raw["id"]) => CandidateIR(
        String(raw["id"]), String(raw["structure_node"]),
        Symbol(raw["family"]), Set(String.(raw["active_edges"])),
        Set(String.(raw["inactive_edges"])), ordinal)
        for (ordinal, raw) in enumerate(configuration["structure_candidates"]))
    factors = Dict(String(raw["id"]) => FactorIR(
        String(raw["id"]), String.(raw["values"]),
        String(raw["initial_distribution_id"])) for raw in world["latent_factors"])
    distributions = Dict(String(raw["id"]) => compile_distribution(raw)
        for raw in world["distributions"])
    processes = Dict(String(raw["id"]) => compile_process(raw)
        for raw in world["processes"])
    emissions = Dict(String(raw["id"]) => compile_emission(raw)
        for raw in world["emissions"])
    outcomes = Dict(String(raw["id"]) => compile_outcome(raw)
        for raw in world["outcomes"])
    contingencies = Dict(String(raw["id"]) => ContingencyIR(
        String(raw["id"]), String(raw["action"]),
        String(raw["target_process"]), Bool(raw["enabled"]))
        for raw in world["contingencies"])
    genome = Dict(String(key) => Float64(genome_raw[key]) for key in (
        "learning_rate", "message_gain", "policy_temperature",
        "structure_complexity_penalty", "precision_floor",
        "dirichlet_concentration", "approximation_iterations",
        "approximation_tolerance"))
    action_costs = Dict(String(key) => Float64(value)
        for (key, value) in genome_raw["action_costs"])
    return CompiledModel(
        canonical_genome_hash(genome_raw),
        String(configuration["configuration_id"]),
        String(configuration["initializer_id"]),
        String(configuration["history_generator_id"]),
        String(configuration["action_reconciler_id"]),
        String(world["world_id"]),
        Symbol(world["family"]),
        Int(world["horizon"]),
        Int(world["episode_length"]),
        Int(world["development_horizon"]),
        String(world["seed_namespace"]),
        String.(world["development_emission_ids"]),
        nodes, edges, channels, policies, candidates, factors, distributions,
        processes, emissions, outcomes, contingencies, genome, action_costs,
        consumption_report(configuration, genome_raw),
    )
end

function compile_trigger(raw)
    raw === nothing && return nothing
    predicate = raw["predicate"]
    return TriggerIR(Symbol(raw["kind"]), String(predicate["field"]),
        Symbol(predicate["comparator"]), get(predicate, "value", nothing))
end

function compile_event(raw)
    kind = Symbol(raw["kind"])
    trigger = haskey(raw, "trigger") ? compile_trigger(raw["trigger"]) : nothing
    if kind in (:observe, :probe, :imaginal)
        return ObservationEventIR(String(raw["id"]), Int(raw["time"]), kind,
            Symbol(raw["source"]), String(raw["channel_id"]),
            haskey(raw, "emission_id") ? String(raw["emission_id"]) : nothing,
            haskey(raw, "generator_id") ? String(raw["generator_id"]) : nothing,
            Int(raw["repeat"]), Int(raw["interval"]), trigger)
    elseif kind == :intervene
        return InterventionEventIR(String(raw["id"]), Int(raw["time"]),
            String(raw["intervention_id"]), trigger)
    elseif kind == :stop_check
        return StopEventIR(String(raw["id"]), Int(raw["time"]),
            String(raw["stopping_rule_id"]), trigger)
    end
    error("uncompiled event kind: $kind")
end

function compile_protocol(raw)
    interventions = Dict(String(item["id"]) => InterventionIR(
        String(item["id"]), Symbol(item["target_kind"]),
        String(item["target_id"]), Symbol(item["operation"]))
        for item in raw["interventions"])
    arms = ArmIR[ArmIR(String(arm["id"]), String(arm["world_id"]),
        EventIR[compile_event(event) for event in arm["events"]])
        for arm in raw["arms"]]
    stopping = Dict(String(item["id"]) => StoppingRuleIR(
        String(item["id"]), Symbol(item["kind"]), Int(item["max_time"]),
        haskey(item, "field") ? String(item["field"]) : nothing,
        haskey(item, "comparator") ? Symbol(item["comparator"]) : nothing,
        haskey(item, "threshold") ? Float64(item["threshold"]) : nothing,
        Int(get(item, "persistence", 1))) for item in raw["stopping_rules"])
    streams = PairedStreamIR[PairedStreamIR(
        String(item["id"]), Set(String.(item["arms"])),
        Set((Symbol(component["kind"]), String(component["id"]))
            for component in item["components"])) for item in raw["paired_streams"]]
    budgets = Dict(String(item["id"]) => EvidenceBudgetIR(
        String(item["id"]), Set(String.(item["arms"])),
        [(String(pair["left"]), String(pair["right"]))
            for pair in item["arm_pairs"]],
        Symbol(item["metric"]), Set(String.(item["scope"])),
        Float64(item["tolerance_fraction"]))
        for item in raw["evidence_budget_rules"])
    controls = Dict(String(item["id"]) => ControlIR(
        String(item["id"]), Symbol(item["kind"]),
        Set(String.(item["treatment_arms"])),
        Set(String.(item["control_arms"])),
        Set(String.(item["intervention_ids"])),
        Set(String.(item["budget_rule_ids"])),
        haskey(item, "explanation") ? String(item["explanation"]) : nothing)
        for item in raw["controls"])
    return ProtocolIR(String(raw["protocol_id"]),
        String.(raw["requested_trace_fields"]), interventions, arms, stopping,
        streams, budgets, controls)
end

function compile_predicate(raw)
    return PredicateIR(String(raw["field"]), Symbol(raw["comparator"]),
        get(raw, "value", nothing))
end

function compile_expression(raw)::ExpressionIR
    op = Symbol(raw["op"])
    op == :literal && return LiteralExpr(raw["value"])
    op == :field && return FieldExpr(String(raw["path"]))
    op == :where && return WhereExpr(compile_expression(raw["source"]),
        PredicateIR[compile_predicate(item) for item in raw["predicates"]])
    op in (:abs, :negate, :log, :exp) &&
        return UnaryExpr(op, compile_expression(raw["arg"]))
    op in (:add, :subtract, :multiply, :divide, :min2, :max2) &&
        return BinaryExpr(op, compile_expression(raw["left"]),
            compile_expression(raw["right"]))
    if op in (:initial, :terminal, :lag, :first_crossing, :slope)
        return TemporalExpr(op, compile_expression(raw["arg"]),
            Int(get(raw, "steps", 0)),
            haskey(raw, "comparator") ? Symbol(raw["comparator"]) : nothing,
            get(raw, "threshold", nothing),
            Int(get(raw, "persistence", 1)),
            haskey(raw, "time_path") ? String(raw["time_path"]) : nothing)
    end
    if op in (:mean, :sum, :min, :max, :std, :count, :rate, :quantile)
        return AggregateExpr(op, compile_expression(raw["arg"]),
            haskey(raw, "probability") ? Float64(raw["probability"]) : nothing)
    end
    op == :arm_difference && return ArmDifferenceExpr(
        compile_expression(raw["value"]), String(raw["treatment"]),
        String(raw["control"]))
    op == :difference_in_differences && return DifferenceInDifferencesExpr(
        compile_expression(raw["value"]), String(raw["treatment_present"]),
        String(raw["treatment_absent"]), String(raw["control_present"]),
        String(raw["control_absent"]))
    op in (:classification_accuracy, :confusion_matrix) &&
        return ClassificationExpr(op, String(raw["prediction_path"]),
            String(raw["truth_path"]),
            haskey(raw, "strata_path") ? String(raw["strata_path"]) : nothing)
    op == :argmax_match && return ArgmaxExpr(
        String(raw["evidence_path"]), String(raw["selected_path"]))
    op == :event_precedes && return EventPrecedesExpr(
        compile_expression(raw["left"]), compile_expression(raw["right"]))
    op == :budget_relative_error &&
        return BudgetErrorExpr(String(raw["evidence_budget_rule_id"]))
    op == :survival_fraction && return SurvivalExpr(
        compile_expression(raw["arg"]), Symbol(raw["comparator"]),
        raw["threshold"])
    error("uncompiled analysis operator: $op")
end

function compile_analysis(raw)
    estimands = EstimandIR[]
    for item in raw["estimands"]
        interval = item["interval"]
        push!(estimands, EstimandIR(
            String(item["id"]), Symbol(item["status"]),
            Symbol(item["hypothesis_provenance"]),
            compile_expression(item["expression"]), Symbol(item["aggregation"]),
            IntervalIR(Symbol(interval["method"]),
                haskey(interval, "level") ? Float64(interval["level"]) : nothing,
                Int(get(interval, "resamples", 0))),
            Set(String.(item["control_ids"]))))
    end
    decisions = DecisionIR[DecisionIR(
        String(item["id"]), String(item["estimand_id"]),
        Symbol(item["comparator"]), item["threshold"],
        Symbol(item["interval_requirement"])) for item in raw["decision_rules"]]
    return AnalysisIR(String(raw["analysis_id"]),
        Symbol(raw["unit_of_analysis"]), Symbol(raw["tie_handling"]),
        Symbol(raw["non_crossing"]), Symbol(raw["missing_cells"]),
        Symbol(raw["non_finite"]), estimands, decisions)
end
