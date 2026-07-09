module Criteria

using JSON3
using YAML

using ..IO: write_json

export Criterion, evaluate_criteria, label_for_value, load_criteria, write_criteria_results

struct Criterion
    id::String
    description::String
    metric_path::String
    comparator::String
    threshold::Float64
    kind::Symbol
    weak_threshold::Union{Nothing, Float64}
    opposite_threshold::Union{Nothing, Float64}
end

function as_string_dict(value)
    out = Dict{String, Any}()
    for (key, val) in value
        out[string(key)] = val
    end
    return out
end

function criterion_from_raw(raw)
    row = as_string_dict(raw)
    kind = Symbol(string(row["kind"]))
    kind in (:success, :adversarial) || error("Criterion kind must be success or adversarial")
    return Criterion(
        string(row["id"]),
        string(row["description"]),
        string(row["metric_path"]),
        string(row["comparator"]),
        Float64(row["threshold"]),
        kind,
        haskey(row, "weak_threshold") && row["weak_threshold"] !== nothing ? Float64(row["weak_threshold"]) : nothing,
        haskey(row, "opposite_threshold") && row["opposite_threshold"] !== nothing ? Float64(row["opposite_threshold"]) : nothing
    )
end

function load_criteria(path::AbstractString)
    raw = YAML.load_file(path)
    raw isa AbstractDict || error("criteria.yaml must be a mapping")
    root = as_string_dict(raw)
    rows = get(root, "criteria", nothing)
    rows === nothing && error("criteria.yaml requires a criteria list")
    return [criterion_from_raw(row) for row in rows]
end

function compare_value(value::Real, comparator::AbstractString, threshold::Real; tolerance::Real = 1e-12)
    c = string(comparator)
    if c == ">="
        return value >= threshold
    elseif c == ">"
        return value > threshold
    elseif c == "<="
        return value <= threshold
    elseif c == "<"
        return value < threshold
    elseif c == "=="
        return abs(value - threshold) <= tolerance
    elseif c == "!="
        return abs(value - threshold) > tolerance
    else
        error("Unsupported comparator: $comparator")
    end
end

function opposite_passes(value::Real, criterion::Criterion)
    threshold = criterion.opposite_threshold
    threshold === nothing && return false
    c = criterion.comparator
    if c in (">=", ">")
        return value <= threshold
    elseif c in ("<=", "<")
        return value >= threshold
    elseif c == "=="
        return abs(value - threshold) <= 1e-12
    elseif c == "!="
        return abs(value - threshold) <= 1e-12
    else
        error("Unsupported comparator: $c")
    end
end

function label_for_value(value, criterion::Criterion)
    value isa Real || return :null
    if compare_value(value, criterion.comparator, criterion.threshold)
        return :support
    end
    if criterion.weak_threshold !== nothing && compare_value(value, criterion.comparator, criterion.weak_threshold)
        return :weak_support
    end
    if opposite_passes(value, criterion)
        return :falsified
    end
    return :null
end

function read_json(path::AbstractString)
    return JSON3.read(read(path, String))
end

function child_value(value, part::AbstractString)
    if value isa AbstractDict
        haskey(value, part) && return value[part]
        sym = Symbol(part)
        haskey(value, sym) && return value[sym]
    end
    sym = Symbol(part)
    if hasproperty(value, sym)
        return getproperty(value, sym)
    end
    if value isa AbstractVector
        idx = tryparse(Int, part)
        idx !== nothing && return value[idx]
    end
    error("Metric path component '$part' not found")
end

function metric_value(summary, path::AbstractString)
    current = summary
    for part in split(path, ".")
        current = child_value(current, part)
    end
    return current
end

function evaluate_criteria(criteria_path::AbstractString, summary_path::AbstractString)
    criteria = load_criteria(criteria_path)
    summary = read_json(summary_path)
    results = NamedTuple[]
    for criterion in criteria
        value = try
            metric_value(summary, criterion.metric_path)
        catch
            nothing
        end
        label = label_for_value(value, criterion)
        push!(results, (
            id = criterion.id,
            description = criterion.description,
            kind = string(criterion.kind),
            metric_path = criterion.metric_path,
            comparator = criterion.comparator,
            threshold = criterion.threshold,
            weak_threshold = criterion.weak_threshold,
            opposite_threshold = criterion.opposite_threshold,
            value = value,
            label = string(label)
        ))
    end
    return (
        criteria_path = abspath(criteria_path),
        summary_path = abspath(summary_path),
        results = results
    )
end

function write_criteria_results(criteria_path::AbstractString, summary_path::AbstractString, output_path::AbstractString)
    results = evaluate_criteria(criteria_path, summary_path)
    write_json(output_path, results)
    return results
end

end
