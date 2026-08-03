using Pkg
using Printf

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(project_dir, "src", "IFSBundleInquiry.jl"))
include(joinpath(project_dir, "src", "ContextSplitRedescription.jl"))
include(joinpath(project_dir, "src", "ContextSplitRedescription44b.jl"))
include(joinpath(project_dir, "src",
    "ContextSplitRedescription44bExploratory.jl"))
using .ContextSplitRedescription44bExploratory

function csv_cell(value)
    return value isa AbstractFloat ? @sprintf("%.12g", value) : string(value)
end

function write_csv(path, rows)
    fields = collect(keys(first(rows)))
    open(path, "w") do io
        println(io, join(string.(fields), ","))
        for row in rows
            println(io, join((csv_cell(getfield(row, field))
                for field in fields), ","))
        end
    end
end

json_escape(value) = replace(string(value), "\\" => "\\\\",
    "\"" => "\\\"", "\n" => "\\n")

function json_value(io, value; indent = 0)
    pad = " "^indent
    if value isa NamedTuple
        println(io, "{")
        entries = collect(pairs(value))
        for (index, (key, item)) in enumerate(entries)
            print(io, " "^(indent + 2), "\"", json_escape(key), "\": ")
            json_value(io, item; indent = indent + 2)
            index < length(entries) && print(io, ",")
            println(io)
        end
        print(io, pad, "}")
    elseif value isa AbstractVector
        print(io, "[")
        for (index, item) in enumerate(value)
            json_value(io, item; indent = indent)
            index < length(value) && print(io, ", ")
        end
        print(io, "]")
    elseif value isa Bool
        print(io, value ? "true" : "false")
    elseif value isa Number
        print(io, isfinite(value) ? value : "\"$(value)\"")
    else
        print(io, "\"", json_escape(value), "\"")
    end
end

function write_json(path, value)
    open(path, "w") do io
        json_value(io, value)
        println(io)
    end
end

function write_table(path, aggregate, finding)
    open(path, "w") do io
        println(io, "# Exploratory narrowing dose response")
        println(io)
        println(io, "**Post-freeze; non-confirmatory.**")
        println(io)
        println(io, "| Narrowing | Part precision | Off-channel precision | Field breadth | Mean root | SD | Regulation floor | Gap |")
        println(io, "|---:|---:|---:|---:|---:|---:|---:|---:|")
        for row in aggregate
            println(io, "| ", @sprintf("%.2f", row.narrowing_strength),
                " | ", @sprintf("%.3f", row.part_precision),
                " | ", @sprintf("%.3f", row.off_channel_precision),
                " | ", @sprintf("%.4f", row.field_breadth),
                " | ", @sprintf("%.3f", row.mean_final_root),
                " | ", @sprintf("%.3f", row.sd_final_root),
                " | ", @sprintf("%.3f", row.mean_regulation_floor),
                " | ", @sprintf("%.3f", row.mean_above_regulation), " |")
        end
        println(io)
        println(io, "Finding: `", finding.reading, "`. The response was ",
            finding.monotone_nonincreasing ? "monotone" : "not monotone",
            ", and maximal narrowing remained ",
            @sprintf("%.3f", finding.maximal_narrowing_above_regulation),
            " above regulation.")
    end
end

function write_svg(path, aggregate)
    width, height = 720, 430
    left, right, top, bottom = 75, 30, 35, 65
    plot_width = width - left - right
    plot_height = height - top - bottom
    x(value) = left + value * plot_width
    y(value) = top + (1 - value) * plot_height
    root_points = join(("$(x(row.narrowing_strength)),$(y(row.mean_final_root))"
        for row in aggregate), " ")
    floor_points = join(("$(x(row.narrowing_strength)),$(y(row.mean_regulation_floor))"
        for row in aggregate), " ")
    open(path, "w") do io
        println(io, """<svg xmlns="http://www.w3.org/2000/svg" width="$width" height="$height" viewBox="0 0 $width $height">""")
        println(io, """<rect width="100%" height="100%" fill="#fbfaf7"/>""")
        println(io, """<text x="$(width/2)" y="22" text-anchor="middle" font-family="sans-serif" font-size="16">Exploratory narrowing dose response</text>""")
        for tick in 0:0.2:1
            println(io, """<line x1="$left" y1="$(y(tick))" x2="$(width-right)" y2="$(y(tick))" stroke="#ddd"/>""")
            println(io, """<text x="$(left-10)" y="$(y(tick)+5)" text-anchor="end" font-family="sans-serif" font-size="12">$(round(tick;digits=1))</text>""")
        end
        println(io, """<line x1="$left" y1="$top" x2="$left" y2="$(height-bottom)" stroke="#333"/>""")
        println(io, """<line x1="$left" y1="$(height-bottom)" x2="$(width-right)" y2="$(height-bottom)" stroke="#333"/>""")
        for row in aggregate
            println(io, """<text x="$(x(row.narrowing_strength))" y="$(height-bottom+22)" text-anchor="middle" font-family="sans-serif" font-size="12">$(row.narrowing_strength)</text>""")
        end
        println(io, """<polyline points="$floor_points" fill="none" stroke="#8a8a8a" stroke-width="2" stroke-dasharray="6 5"/>""")
        println(io, """<polyline points="$root_points" fill="none" stroke="#7b3fb2" stroke-width="3"/>""")
        for row in aggregate
            println(io, """<circle cx="$(x(row.narrowing_strength))" cy="$(y(row.mean_final_root))" r="5" fill="#7b3fb2"/>""")
        end
        println(io, """<text x="$(width/2)" y="$(height-15)" text-anchor="middle" font-family="sans-serif" font-size="13">Narrowing strength (0 = frozen, 1 = maximal)</text>""")
        println(io, """<text x="18" y="$(height/2)" transform="rotate(-90 18 $(height/2))" text-anchor="middle" font-family="sans-serif" font-size="13">Mean final root posterior</text>""")
        println(io, """<line x1="$(width-230)" y1="46" x2="$(width-195)" y2="46" stroke="#7b3fb2" stroke-width="3"/><text x="$(width-187)" y="51" font-family="sans-serif" font-size="12">narrowed contact</text>""")
        println(io, """<line x1="$(width-230)" y1="66" x2="$(width-195)" y2="66" stroke="#8a8a8a" stroke-width="2" stroke-dasharray="6 5"/><text x="$(width-187)" y="71" font-family="sans-serif" font-size="12">regulation floor</text>""")
        println(io, "</svg>")
    end
end

output_dir = joinpath(project_dir, "results", "context_split_redescription",
    "44b", "exploratory_narrowing")
isdir(output_dir) && error("exploratory output already exists; refusing overwrite")
mkpath(output_dir)
rows = run_sweep()
aggregate = aggregate_sweep(rows)
finding = exploratory_finding(aggregate)
write_csv(joinpath(output_dir, "per_seed.csv"), rows)
write_csv(joinpath(output_dir, "dose_response.csv"), aggregate)
write_json(joinpath(output_dir, "summary.json"), (
    label = "Exploratory addendum (post-freeze; non-confirmatory)",
    seeds = EXPLORATORY_SEEDS,
    strengths = NARROWING_STRENGTHS,
    aggregate = aggregate,
    finding = finding,
))
write_table(joinpath(output_dir, "table.md"), aggregate, finding)
write_svg(joinpath(output_dir, "narrowing-dose-response.svg"), aggregate)
println("Exploratory narrowing sweep complete: ", finding)
