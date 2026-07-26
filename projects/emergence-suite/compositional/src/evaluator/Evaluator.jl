include(normpath(joinpath(@__DIR__, "..", "..", "scripts", "contract",
    "analysis_math.jl")))

struct Datum
    seed::UInt64
    arm::String
    episode::Int
    event_index::Int
    genome_id::String
    time::Int
    row_index::Int
    path::String
    value::Any
    source_hashes::Vector{String}
end

function row_hash(row::AbstractTraceRow)
    fields = row.fields
    line = join(("$key=$(repr(fields[key]))"
        for key in sort!(collect(keys(fields)))), "\t")
    return bytes2hex(sha256(line))
end

datum(row::AbstractTraceRow, path::String, value) = Datum(
    row.seed, row.arm, row.episode,
    row isa EventTraceRow ? row.event_index : -1,
    String(row.fields["run.genome_id"]), row.time, row.row_index, path, value,
    [row_hash(row)])

function derived(item::Datum, path::String, value;
        hashes::Vector{String} = item.source_hashes)
    return Datum(item.seed, item.arm, item.episode, item.event_index,
        item.genome_id, item.time, item.row_index, path, value,
        sort!(unique(hashes)))
end

function unit_key(plan::AnalysisIR, item::Datum; include_arm::Bool = true)
    arm = include_arm ? item.arm : ""
    plan.unit == :seed && return (item.seed, arm)
    plan.unit == :episode && return (item.seed, arm, item.episode)
    plan.unit == :event &&
        return (item.seed, arm, item.event_index)
    plan.unit == :genome && return (item.genome_id, arm)
    error("unknown analysis unit: $(plan.unit)")
end

function unit_serialization(plan::AnalysisIR, item::Datum;
        include_arm::Bool = true)
    arm = include_arm ? ";arm=$(item.arm)" : ""
    plan.unit == :seed && return "seed=$(item.seed)$arm"
    plan.unit == :episode &&
        return "seed=$(item.seed)$arm;episode=$(item.episode)"
    plan.unit == :event &&
        return "seed=$(item.seed)$arm;event=$(item.event_index)"
    plan.unit == :genome && return "genome=$(item.genome_id)$arm"
    error("unknown analysis unit")
end

function field_data(trace::TraceTable, path::String, plan::AnalysisIR)
    result = Datum[]
    for row in trace.rows
        plan.unit == :event && !(row isa EventTraceRow) && continue
        for actual in sort!(collect(keys(row.fields)))
            startswith(actual, "_") && continue
            field_matches(path, actual) || continue
            push!(result, datum(row, actual, row.fields[actual]))
        end
    end
    return result
end

function predicate_passes(row::AbstractTraceRow, predicate::PredicateIR)
    haskey(row.fields, predicate.field) || return false
    value = row.fields[predicate.field]
    predicate.comparator == :finite &&
        return value isa Number && isfinite(value)
    return compare_value(value, predicate.comparator, predicate.value)
end

function latest_per_time(data::Vector{Datum})
    selected = Dict{Tuple{UInt64,String,String,Int},Datum}()
    for item in data
        key = (item.seed, item.arm, item.path, item.time)
        if !haskey(selected, key) ||
                item.row_index > selected[key].row_index
            selected[key] = item
        end
    end
    return sort!(collect(values(selected));
        by = item -> (item.seed, item.arm, item.path, item.time, item.row_index))
end

function temporal_groups(data::Vector{Datum})
    groups = Dict{Tuple{UInt64,String,String},Vector{Datum}}()
    for item in latest_per_time(data)
        push!(get!(groups, (item.seed, item.arm, item.path), Datum[]), item)
    end
    for group in values(groups)
        sort!(group; by = item -> item.time)
    end
    return groups
end

function missing_value(plan::AnalysisIR, context::String)
    plan.missing_cells == :fail && error("$context: missing analysis cell")
    plan.missing_cells == :drop_pair && return nothing
    return missing
end

function sanitize_value(plan::AnalysisIR, value, context::String)
    value === missing && return missing_value(plan, context)
    if value isa Number && !isfinite(value)
        plan.non_finite == :fail && error("$context: non-finite analysis value")
        plan.non_finite == :drop_pair && return nothing
        return missing
    end
    return value
end

function first_crossing(values::Vector{Datum}, expression::TemporalExpr,
        trace::TraceTable, plan::AnalysisIR)
    for stop in eachindex(values)
        stop >= expression.persistence || continue
        recent = values[(stop - expression.persistence + 1):stop]
        all(diff([item.time for item in recent]) .== 1) || continue
        all(compare_value(item.value, expression.comparator,
            expression.threshold) for item in recent) || continue
        item = values[stop]
        hashes = reduce(vcat, (entry.source_hashes for entry in recent);
            init = String[])
        return derived(item, "derived.first_crossing_time", item.time;
            hashes = hashes)
    end
    item = last(values)
    plan.non_crossing == :fail &&
        error("first_crossing: configured crossing did not occur")
    value = plan.non_crossing == :missing ? missing : trace.horizon
    return derived(item, "derived.first_crossing_time", value)
end

function aggregate_scalar(op::Symbol, values::Vector)
    op == :count && return length(values)
    isempty(values) && return missing
    any(ismissing, values) && return missing
    op == :mean && return mean(Float64.(values))
    op == :sum && return sum(values)
    op == :min && return minimum(values)
    op == :max && return maximum(values)
    op == :std && return length(values) < 2 ? missing :
        sample_standard_deviation(Float64.(values))
    op == :rate && return mean(Float64.(Bool.(values)))
    error("unsupported aggregate: $op")
end

apply_unary(op::Symbol, value) =
    op == :abs ? abs(value) :
    op == :negate ? -value :
    op == :log ? log(value) :
    op == :exp ? exp(value) : error("unknown unary operator")

apply_binary(op::Symbol, left, right) =
    op == :add ? left + right :
    op == :subtract ? left - right :
    op == :multiply ? left * right :
    op == :divide ? left / right :
    op == :min2 ? min(left, right) :
    op == :max2 ? max(left, right) : error("unknown binary operator")

function alignment_key(item::Datum)
    return (item.seed, item.arm, item.episode, item.event_index,
        item.genome_id, item.time, item.row_index)
end

function aligned_binary(left::Vector{Datum}, right::Vector{Datum},
        op::Symbol, plan::AnalysisIR)
    right_lookup = Dict(alignment_key(item) => item for item in right)
    length(right_lookup) == length(right) ||
        error("binary expression: multiply-defined right key")
    result = Datum[]
    for item in left
        key = alignment_key(item)
        if !haskey(right_lookup, key)
            value = missing_value(plan, "binary expression")
            value === nothing || push!(result,
                derived(item, item.path, value))
            continue
        end
        other = right_lookup[key]
        value = item.value === missing || other.value === missing ? missing :
            apply_binary(op, item.value, other.value)
        value = sanitize_value(plan, value, "binary expression")
        value === nothing || push!(result, derived(item, item.path, value;
            hashes = vcat(item.source_hashes, other.source_hashes)))
    end
    extra = setdiff(Set(keys(right_lookup)), Set(alignment_key(item)
        for item in left))
    isempty(extra) || plan.missing_cells == :fail &&
        error("binary expression: unpaired right keys")
    return result
end

function arm_contrast(data::Vector{Datum}, treatment::String, control::String,
        plan::AnalysisIR)
    groups = Dict{Any,Dict{String,Vector{Datum}}}()
    for item in data
        item.arm in (treatment, control) || continue
        push!(get!(get!(groups, unit_key(plan, item; include_arm = false),
            Dict{String,Vector{Datum}}()), item.arm, Datum[]), item)
    end
    result = Datum[]
    for key in sort!(collect(keys(groups)); by = repr)
        arms = groups[key]
        valid = all(haskey(arms, arm) && length(arms[arm]) == 1
            for arm in (treatment, control))
        if !valid
            value = missing_value(plan, "arm_difference")
            value === nothing && continue
            representative = first(first(values(arms)))
            push!(result, derived(representative,
                "derived.paired_difference", value))
            continue
        end
        left, right = only(arms[treatment]), only(arms[control])
        value = left.value === missing || right.value === missing ? missing :
            left.value - right.value
        push!(result, Datum(left.seed, "", left.episode, -1, left.genome_id,
            max(left.time, right.time), max(left.row_index, right.row_index),
            "derived.paired_difference", value,
            sort!(unique(vcat(left.source_hashes, right.source_hashes)))))
    end
    return result
end

function budget_errors(trace::TraceTable, budget_id::String,
        plan::AnalysisIR)
    budget = trace.budgets[budget_id]
    result = Datum[]
    seeds = sort!(unique(row.seed for row in trace.rows))
    for seed in seeds
        totals = Dict{String,Float64}()
        representatives = Dict{String,AbstractTraceRow}()
        for arm in budget.arms
            rows = [row for row in trace.rows if row.seed == seed &&
                row.arm == arm &&
                haskey(row.fields, "observation.delivered_log_likelihood") &&
                !isempty(intersect(Set(get(row.fields,
                    "_observation.scope_ids", String[])), budget.scope))]
            totals[arm] = sum((abs(Float64(row.fields[
                "observation.delivered_log_likelihood"])) for row in rows);
                init = 0.0)
            isempty(rows) || (representatives[arm] = last(rows))
        end
        for (left, right) in budget.arm_pairs
            if !haskey(representatives, left) || !haskey(representatives, right)
                value = missing_value(plan, "evidence budget")
                value === nothing && continue
                rows = [row for row in trace.rows if row.seed == seed]
                representative = first(rows)
            else
                denominator = max(abs(totals[left]), abs(totals[right]), eps())
                value = abs(totals[left] - totals[right]) / denominator
                representative = representatives[left]
            end
            push!(result, derived(datum(representative,
                "derived.budget_relative_error", value),
                "derived.budget_relative_error", value))
        end
    end
    return result
end

function evaluate_expression(expression::ExpressionIR, trace::TraceTable,
        plan::AnalysisIR)
    expression isa LiteralExpr && return expression.value
    expression isa FieldExpr && return field_data(trace, expression.path, plan)
    if expression isa WhereExpr
        data = evaluate_expression(expression.source, trace, plan)
        return [item for item in data if begin
            row = first(row for row in trace.rows
                if row.seed == item.seed && row.arm == item.arm &&
                    row.row_index == item.row_index)
            all(predicate_passes(row, predicate)
                for predicate in expression.predicates)
        end]
    elseif expression isa UnaryExpr
        value = evaluate_expression(expression.arg, trace, plan)
        if value isa Vector
            result = Datum[]
            for item in value
                transformed = item.value === missing ? missing :
                    apply_unary(expression.op, item.value)
                transformed = sanitize_value(plan, transformed,
                    "unary expression")
                transformed === nothing || push!(result,
                    derived(item, item.path, transformed))
            end
            return result
        end
        return sanitize_value(plan, apply_unary(expression.op, value),
            "unary expression")
    elseif expression isa BinaryExpr
        left = evaluate_expression(expression.left, trace, plan)
        right = evaluate_expression(expression.right, trace, plan)
        left isa Vector && right isa Vector &&
            return aligned_binary(left, right, expression.op, plan)
        if left isa Vector
            result = Datum[]
            for item in left
                value = item.value === missing ? missing :
                    apply_binary(expression.op, item.value, right)
                value = sanitize_value(plan, value, "binary expression")
                value === nothing || push!(result,
                    derived(item, item.path, value))
            end
            return result
        elseif right isa Vector
            result = Datum[]
            for item in right
                value = item.value === missing ? missing :
                    apply_binary(expression.op, left, item.value)
                value = sanitize_value(plan, value, "binary expression")
                value === nothing || push!(result,
                    derived(item, item.path, value))
            end
            return result
        end
        return sanitize_value(plan, apply_binary(expression.op, left, right),
            "binary expression")
    elseif expression isa TemporalExpr
        data = evaluate_expression(expression.arg, trace, plan)
        groups = temporal_groups(data)
        result = Datum[]
        for (_, values) in sort!(collect(groups); by = first)
            if expression.op == :initial
                push!(result, first(values))
            elseif expression.op == :terminal
                push!(result, last(values))
            elseif expression.op == :lag
                for index in (expression.steps + 1):length(values)
                    prior, current = values[index - expression.steps], values[index]
                    push!(result, derived(current, current.path, prior.value;
                        hashes = vcat(prior.source_hashes, current.source_hashes)))
                end
            elseif expression.op == :first_crossing
                push!(result, first_crossing(values, expression, trace, plan))
            elseif expression.op == :slope
                times = Float64[item.time for item in values]
                observations = Float64[item.value for item in values]
                slope = length(times) < 2 ? missing :
                    sum((times .- mean(times)) .*
                        (observations .- mean(observations))) /
                    sum((times .- mean(times)).^2)
                push!(result, derived(last(values), "derived.slope", slope;
                    hashes = reduce(vcat,
                        (item.source_hashes for item in values);
                        init = String[])))
            end
        end
        return result
    elseif expression isa AggregateExpr
        data = evaluate_expression(expression.arg, trace, plan)
        groups = Dict{Any,Vector{Datum}}()
        for item in data
            push!(get!(groups, unit_key(plan, item), Datum[]), item)
        end
        result = Datum[]
        for key in sort!(collect(keys(groups)); by = repr)
            group = groups[key]
            values = [item.value for item in group]
            value = expression.op == :quantile ?
                (any(ismissing, values) ? missing :
                    nearest_rank(Float64.(values), expression.probability)) :
                aggregate_scalar(expression.op, values)
            value = sanitize_value(plan, value, "aggregate expression")
            value === nothing || push!(result, derived(last(group),
                "derived.$(expression.op)", value;
                hashes = reduce(vcat,
                    (item.source_hashes for item in group);
                    init = String[])))
        end
        return result
    elseif expression isa ArmDifferenceExpr
        return arm_contrast(
            evaluate_expression(expression.value, trace, plan),
            expression.treatment, expression.control, plan)
    elseif expression isa DifferenceInDifferencesExpr
        data = evaluate_expression(expression.value, trace, plan)
        first_difference = arm_contrast(data, expression.treatment_present,
            expression.treatment_absent, plan)
        second_difference = arm_contrast(data, expression.control_present,
            expression.control_absent, plan)
        lookup = Dict(unit_key(plan, item; include_arm = false) => item
            for item in second_difference)
        result = Datum[]
        for item in first_difference
            key = unit_key(plan, item; include_arm = false)
            if !haskey(lookup, key)
                value = missing_value(plan, "difference_in_differences")
                value === nothing || push!(result,
                    derived(item, "derived.paired_difference", value))
                continue
            end
            other = lookup[key]
            value = item.value === missing || other.value === missing ?
                missing : item.value - other.value
            push!(result, derived(item, "derived.paired_difference", value;
                hashes = vcat(item.source_hashes, other.source_hashes)))
        end
        return result
    elseif expression isa ClassificationExpr
        predictions = field_data(trace, expression.prediction_path, plan)
        truths = field_data(trace, expression.truth_path, plan)
        truth_lookup = Dict((item.seed, item.arm, item.time, item.row_index) =>
            item for item in truths)
        strata = expression.strata_path === nothing ? Datum[] :
            field_data(trace, expression.strata_path, plan)
        strata_lookup = Dict((item.seed, item.arm, item.time, item.row_index) =>
            item.value for item in strata)
        groups = Dict{Any,Vector{Tuple{Any,Any,Vector{String},Datum}}}()
        for prediction in predictions
            row_key = (prediction.seed, prediction.arm,
                prediction.time, prediction.row_index)
            haskey(truth_lookup, row_key) || continue
            truth = truth_lookup[row_key]
            stratum = get(strata_lookup, row_key, nothing)
            group_key = (unit_key(plan, prediction), stratum)
            push!(get!(groups, group_key,
                Tuple{Any,Any,Vector{String},Datum}[]),
                (truth.value, prediction.value,
                    vcat(truth.source_hashes, prediction.source_hashes),
                    prediction))
        end
        result = Datum[]
        for key in sort!(collect(keys(groups)); by = repr)
            cells = groups[key]
            if expression.op == :classification_accuracy
                value = mean(truth == prediction
                    for (truth, prediction, _, _) in cells)
            else
                value = Dict{Tuple{Any,Any},Int}()
                for (truth, prediction, _, _) in cells
                    cell = (truth, prediction)
                    value[cell] = get(value, cell, 0) + 1
                end
            end
            representative = last(cells)[4]
            hashes = reduce(vcat, (cell[3] for cell in cells);
                init = String[])
            path = key[2] === nothing ? "derived.classification_correct" :
                "derived.classification_correct;stratum=$(key[2])"
            push!(result, derived(representative, path, value;
                hashes = hashes))
        end
        return result
    elseif expression isa ArgmaxExpr
        evidence = field_data(trace, expression.evidence_path, plan)
        selected = field_data(trace, expression.selected_path, plan)
        groups = Dict{Tuple{UInt64,String,Int},Vector{Datum}}()
        for item in evidence
            push!(get!(groups, (item.seed, item.arm, item.row_index),
                Datum[]), item)
        end
        result = Datum[]
        for (key, values) in groups
            winner = first(sort!(values; by = item -> (-item.value, item.path)))
            suffix = last(split(winner.path, '.'))
            selected_item = findfirst(item -> item.seed == key[1] &&
                item.arm == key[2] && item.row_index == key[3] &&
                endswith(item.path, ".$suffix"), selected)
            match = selected_item !== nothing &&
                selected[selected_item].value === true
            hashes = selected_item === nothing ? winner.source_hashes :
                vcat(winner.source_hashes,
                    selected[selected_item].source_hashes)
            push!(result, derived(winner, "derived.argmax_match", match;
                hashes = hashes))
        end
        return result
    elseif expression isa EventPrecedesExpr
        left = evaluate_expression(expression.left, trace, plan)
        right = evaluate_expression(expression.right, trace, plan)
        lookup = Dict(unit_key(plan, item) => item for item in right)
        result = Datum[]
        for item in left
            key = unit_key(plan, item)
            haskey(lookup, key) || continue
            other = lookup[key]
            value = if item.value === missing || other.value === missing
                missing
            elseif item.value < other.value
                true
            elseif item.value > other.value
                false
            elseif plan.tie_handling == :pass
                true
            elseif plan.tie_handling == :fail
                false
            else
                missing
            end
            push!(result, derived(item, "derived.event_precedes", value;
                hashes = vcat(item.source_hashes, other.source_hashes)))
        end
        return result
    elseif expression isa BudgetErrorExpr
        return budget_errors(trace, expression.budget_id, plan)
    elseif expression isa SurvivalExpr
        data = evaluate_expression(expression.arg, trace, plan)
        groups = Dict{Any,Vector{Datum}}()
        for item in data
            push!(get!(groups, unit_key(plan, item), Datum[]), item)
        end
        return [derived(last(group), "derived.survival_fraction",
            mean(compare_value(item.value, expression.comparator,
                expression.threshold) for item in group);
            hashes = reduce(vcat, (item.source_hashes for item in group);
                init = String[]))
            for group in values(groups)]
    end
    error("unimplemented typed analysis expression")
end

function unit_values(data, plan::AnalysisIR)
    data isa Vector || return [(nothing, data, String[])]
    groups = Dict{Any,Vector{Datum}}()
    for item in data
        push!(get!(groups, unit_key(plan, item), Datum[]), item)
    end
    result = Tuple{Any,Any,Vector{String}}[]
    ordered_keys = sort!(collect(keys(groups)); by = key -> begin
        representative = first(groups[key])
        unit_serialization(plan, representative;
            include_arm = !isempty(representative.arm))
    end)
    for key in ordered_keys
        group = groups[key]
        length(group) == 1 ||
            error("top-level aggregation requires one scalar per unit")
        item = only(group)
        push!(result, (key, item.value, item.source_hashes))
    end
    return result
end

function aggregate_estimand(data, estimand::EstimandIR, plan::AnalysisIR)
    units = unit_values(data, plan)
    if isempty(units)
        plan.missing_cells == :fail &&
            error("estimand $(estimand.id): empty unit series")
        return missing, units
    end
    values = [unit[2] for unit in units]
    if any(ismissing, values)
        plan.missing_cells == :fail &&
            error("estimand $(estimand.id): missing unit")
        plan.missing_cells == :drop_pair &&
            (units = [unit for unit in units if unit[2] !== missing];
             values = [unit[2] for unit in units])
        plan.missing_cells == :missing && return missing, units
    end
    isempty(values) && return missing, units
    estimand.aggregation == :identity && return only(values), units
    estimand.aggregation == :mean &&
        return mean(Float64.(values)), units
    estimand.aggregation == :median &&
        return empirical_median(Float64.(values)), units
    estimand.aggregation == :rate &&
        return mean(Float64.(Bool.(values))), units
    estimand.aggregation == :matrix && return only(values), units
    error("unknown estimand aggregation: $(estimand.aggregation)")
end

function interval_for(analysis_id::String, estimand::EstimandIR,
        units, point)
    method = estimand.interval.method
    (method == :none || point === missing || isempty(units)) &&
        return nothing, nothing
    values = [unit[2] for unit in units]
    if method == :exact_binomial
        return clopper_pearson(count(identity, Bool.(values)),
            length(values), estimand.interval.level)
    end
    replicates = Float64[]
    n = length(values)
    for replicate in 0:(estimand.interval.resamples - 1)
        indices = bootstrap_indices(
            n, analysis_id, estimand.id, replicate) .+ 1
        sample = values[indices]
        estimate = estimand.aggregation == :median ?
            empirical_median(Float64.(sample)) :
            estimand.aggregation == :rate ?
                mean(Float64.(Bool.(sample))) : mean(Float64.(sample))
        push!(replicates, estimate)
    end
    level = estimand.interval.level
    lo = nearest_rank(replicates, (1 - level) / 2)
    hi = nearest_rank(replicates, 1 - (1 - level) / 2)
    method == :basic_bootstrap && return 2 * point - hi, 2 * point - lo
    return lo, hi
end

function evaluate_trace(trace::TraceTable, analysis::AnalysisIR)
    estimands = Dict{String,EvaluatedEstimand}()
    for estimand in analysis.estimands
        data = evaluate_expression(estimand.expression, trace, analysis)
        point, units = aggregate_estimand(data, estimand, analysis)
        lower, upper = interval_for(
            analysis.analysis_id, estimand, units, point)
        hashes = sort!(unique(reduce(vcat,
            (unit[3] for unit in units); init = String[])))
        estimands[estimand.id] = EvaluatedEstimand(
            estimand.id, point, lower, upper, repr(estimand.expression), hashes)
    end
    decisions = Dict{String,Bool}()
    for rule in analysis.decisions
        estimate = estimands[rule.estimand_id]
        if estimate.value === missing
            decisions[rule.id] = false
        else
            decisions[rule.id] = decision_pass(estimate.value, estimate.lower,
                estimate.upper, String(rule.comparator), rule.threshold,
                String(rule.interval_requirement))
        end
    end
    return EvaluationResult(estimands, decisions)
end
