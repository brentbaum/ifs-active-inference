module IO

using JSON3

export ensure_dir, sanitize_json, write_json, write_rows_csv, write_placeholder_svg

sanitize_json(value::Nothing) = nothing
sanitize_json(value::Bool) = value
sanitize_json(value::Integer) = value
sanitize_json(value::AbstractString) = value
sanitize_json(value::AbstractFloat) = isfinite(value) ? value : nothing
sanitize_json(value::Symbol) = string(value)

function sanitize_json(values::AbstractVector)
    [sanitize_json(value) for value in values]
end

function sanitize_json(values::Tuple)
    tuple((sanitize_json(value) for value in values)...)
end

function sanitize_json(values::NamedTuple)
    named_pairs = ((key, sanitize_json(val)) for (key, val) in Base.pairs(values))
    (; named_pairs...)
end

function sanitize_json(values::Dict)
    keys_sorted = sort!(collect(keys(values)); by = string)
    named_values = Tuple(sanitize_json(values[key]) for key in keys_sorted)
    return NamedTuple{Tuple(Symbol(string(key)) for key in keys_sorted)}(named_values)
end

sanitize_json(value) = value

function ensure_dir(path::AbstractString)
    mkpath(path)
    return path
end

function write_json(path::AbstractString, value)
    open(path, "w") do io
        JSON3.pretty(io, sanitize_json(value))
        write(io, "\n")
    end
    return path
end

function csv_escape(value)
    if value === nothing
        return ""
    end
    text = string(value)
    if occursin(r"[,\n\r\"]", text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function write_rows_csv(path::AbstractString, rows)
    open(path, "w") do io
        if isempty(rows)
            return
        end
        columns = collect(propertynames(first(rows)))
        println(io, join(string.(columns), ","))
        for row in rows
            println(io, join((csv_escape(getproperty(row, column)) for column in columns), ","))
        end
    end
    return path
end

function write_placeholder_svg(path::AbstractString; title::AbstractString = "dummy experiment")
    svg = """
    <svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 640 360">
      <rect width="640" height="360" fill="#f7f7f4"/>
      <line x1="70" y1="290" x2="590" y2="290" stroke="#333" stroke-width="2"/>
      <line x1="70" y1="50" x2="70" y2="290" stroke="#333" stroke-width="2"/>
      <polyline points="90,245 170,220 250,190 330,160 410,125 490,105 570,85"
        fill="none" stroke="#2b6cb0" stroke-width="5"/>
      <text x="70" y="32" font-family="Arial, sans-serif" font-size="20" fill="#222">$title</text>
      <text x="250" y="332" font-family="Arial, sans-serif" font-size="14" fill="#444">trial checkpoint</text>
      <text x="16" y="180" font-family="Arial, sans-serif" font-size="14" fill="#444" transform="rotate(-90 16 180)">true A concentration</text>
    </svg>
    """
    open(path, "w") do io
        write(io, svg)
    end
    return path
end

end
