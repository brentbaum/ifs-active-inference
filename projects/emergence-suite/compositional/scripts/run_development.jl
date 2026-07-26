#!/usr/bin/env julia

using CompositionalOrganism
using SHA
using TOML

const CO = CompositionalOrganism
const ROOT = normpath(joinpath(@__DIR__, ".."))
const INPUT = joinpath(ROOT, "protocols", "development")
const OUTPUT = joinpath(ROOT, "results", "experiment51", "development")
const GENOME = joinpath(ROOT, "genome.toml")
const PUBLIC_DEVELOPMENT_SEEDS = UInt64[71_001, 71_002, 71_003, 71_004,
    71_005, 71_006, 71_007, 71_008]

function bundle_directories(root)
    result = String[]
    for (directory, _, files) in walkdir(root)
        required = Set(["configuration.toml", "world.toml", "protocol.toml",
            "analysis.toml", "interpretation-lock.md"])
        required ⊆ Set(files) && push!(result, directory)
    end
    return sort!(result)
end

function clean_cell(value)
    return replace(string(value), '\t' => "\\t", '\n' => "\\n",
        '\r' => "\\r")
end

function write_trace(path, trace)
    fields = sort!(unique(reduce(vcat,
        [collect(keys(row.fields)) for row in trace.rows];
        init = String[])))
    open(path, "w") do io
        println(io, join(fields, '\t'))
        for row in trace.rows
            println(io, join((haskey(row.fields, field) ?
                clean_cell(row.fields[field]) : "" for field in fields), '\t'))
        end
    end
end

function write_evaluation(path, result)
    document = Dict{String,Any}(
        "decisions" => result.decisions,
        "estimands" => Dict(id => Dict(
            "value" => something(estimand.value, "missing"),
            "lower" => something(estimand.lower, "missing"),
            "upper" => something(estimand.upper, "missing"),
            "expression" => estimand.expression_ast,
            "source_hashes" => estimand.source_row_hashes,
        ) for (id, estimand) in result.estimands),
    )
    open(path, "w") do io
        TOML.print(io, document; sorted = true)
    end
end

mkpath(joinpath(OUTPUT, "raw-traces"))
mkpath(joinpath(OUTPUT, "evaluations"))
rows = NamedTuple[]
for directory in bundle_directories(INPUT)
    label = relpath(directory, INPUT)
    safe_label = replace(label, '/' => '_')
    for seed in PUBLIC_DEVELOPMENT_SEEDS
        trace_path = joinpath(
            OUTPUT, "raw-traces", "$safe_label-$seed.tsv")
        evaluation_path = joinpath(
            OUTPUT, "evaluations", "$safe_label-$seed.toml")
        try
            documents = CO.load_documents(directory)
            model = CO.compile_model(documents, CO.load_genome(GENOME))
            protocol = CO.compile_protocol(documents.protocol)
            analysis = CO.compile_analysis(documents.analysis)
            trace = CO.run_protocol(model, protocol, seed)
            sealed_hash = CO.trace_hash(trace)
            write_trace(trace_path, trace)
            file_hash = bytes2hex(sha256(read(trace_path)))
            result = CO.evaluate_trace(trace, analysis)
            write_evaluation(evaluation_path, result)
            push!(rows, (bundle = label, seed = seed,
                status = all(values(result.decisions)) ?
                    "success" : "scientific_failure",
                trace_hash = sealed_hash, raw_file_hash = file_hash,
                row_count = length(trace.rows), error = ""))
        catch exception
            push!(rows, (bundle = label, seed = seed,
                status = "semantic_inexpressibility", trace_hash = "",
                raw_file_hash = "", row_count = 0,
                error = sprint(showerror, exception)))
        end
    end
end

manifest = joinpath(OUTPUT, "manifest.tsv")
open(manifest, "w") do io
    println(io, join(fieldnames(typeof(first(rows))), '\t'))
    for row in rows
        println(io, join((clean_cell(getfield(row, field))
            for field in fieldnames(typeof(row))), '\t'))
    end
end

println("development outputs written to $OUTPUT")
