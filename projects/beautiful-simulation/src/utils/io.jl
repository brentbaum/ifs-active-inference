sanitize_json(value::Nothing) = nothing
sanitize_json(value::Bool) = value
sanitize_json(value::Integer) = value
sanitize_json(value::AbstractString) = value
sanitize_json(value::AbstractFloat) = isfinite(value) ? value : nothing

function sanitize_json(values::AbstractVector)
    return [sanitize_json(value) for value in values]
end

function sanitize_json(values::Tuple)
    return tuple((sanitize_json(value) for value in values)...)
end

function sanitize_json(values::NamedTuple)
    named_pairs = ((key, sanitize_json(val)) for (key, val) in Base.pairs(values))
    return (; named_pairs...)
end

function sanitize_json(values::Dict)
    return Dict(key => sanitize_json(val) for (key, val) in values)
end

sanitize_json(value) = value

function ensure_dir(path::AbstractString)
    mkpath(path)
    return path
end

function write_json(path::AbstractString, value)
    open(path, "w") do io
        JSON3.pretty(io, sanitize_json(value))
    end
    return path
end

function write_rows_csv(path::AbstractString, rows)
    CSV.write(path, DataFrame(rows))
    return path
end
