module Config

using YAML

export ExperimentConfig, config_snapshot, load_config, suite_root, default_runs_root

Base.@kwdef struct ExperimentConfig
    experiment::String
    seeds::Vector{Int}
    output_dir::String
    label::Union{Nothing, String} = nothing
    model_params::Dict{String, Any} = Dict{String, Any}()
    sweep_grid::Dict{String, Any} = Dict{String, Any}()
    criteria_path::Union{Nothing, String} = nothing
end

suite_root() = normpath(joinpath(@__DIR__, ".."))
default_runs_root() = normpath(joinpath(suite_root(), "..", "runs"))

function as_string_dict(value)
    out = Dict{String, Any}()
    for (key, val) in value
        out[string(key)] = val
    end
    return out
end

function string_or_nothing(value)
    value === nothing && return nothing
    return string(value)
end

function load_config(path::AbstractString)
    raw_any = YAML.load_file(path)
    raw_any isa AbstractDict || error("Config must be a YAML mapping: $path")
    raw = as_string_dict(raw_any)
    experiment = string(get(raw, "experiment", "dummy"))
    seeds = haskey(raw, "seeds") ? Int.(raw["seeds"]) : error("Config requires an explicit seeds list")
    isempty(seeds) && error("Config seeds list cannot be empty")

    model_params = as_string_dict(get(raw, "model_params", Dict{String, Any}()))
    sweep_grid = as_string_dict(get(raw, "sweep_grid", Dict{String, Any}()))
    output_dir = string(get(raw, "output_dir", default_runs_root()))
    if !isabspath(output_dir)
        output_dir = normpath(joinpath(dirname(path), output_dir))
    end
    criteria_path = string_or_nothing(get(raw, "criteria_path", joinpath(dirname(path), "criteria.yaml")))
    if !isnothing(criteria_path) && !isabspath(criteria_path)
        criteria_path = normpath(joinpath(dirname(path), criteria_path))
    end

    return ExperimentConfig(
        experiment = experiment,
        seeds = seeds,
        output_dir = output_dir,
        label = string_or_nothing(get(raw, "label", nothing)),
        model_params = model_params,
        sweep_grid = sweep_grid,
        criteria_path = criteria_path
    )
end

function canonicalize(value)
    if value isa AbstractDict
        keys_sorted = sort!(collect(keys(value)); by = string)
        values_tuple = Tuple(canonicalize(value[key]) for key in keys_sorted)
        return NamedTuple{Tuple(Symbol(string(key)) for key in keys_sorted)}(values_tuple)
    elseif value isa AbstractVector
        return [canonicalize(item) for item in value]
    elseif value isa Symbol
        return string(value)
    else
        return value
    end
end

function config_snapshot(config::ExperimentConfig)
    return (
        experiment = config.experiment,
        seeds = copy(config.seeds),
        output_dir = config.output_dir,
        label = config.label,
        model_params = canonicalize(config.model_params),
        sweep_grid = canonicalize(config.sweep_grid),
        criteria_path = config.criteria_path
    )
end

end
