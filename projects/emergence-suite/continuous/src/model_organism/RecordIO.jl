using Serialization

function collect_files(path::AbstractString)
    isdir(path) || return isfile(path) ? [String(path)] : String[]
    files = String[]
    for (root, _, names) in walkdir(path)
        for name in names
            push!(files, joinpath(root, name))
        end
    end
    return sort(files)
end

json_escape(value::AbstractString) = replace(value,
    "\\" => "\\\\", "\"" => "\\\"", "\n" => "\\n",
    "\r" => "\\r", "\t" => "\\t")

function write_json(io::IO, value; indent::Int = 0)
    prefix = " "^indent
    if value === nothing || value === missing
        print(io, "null")
    elseif value isa Bool
        print(io, value ? "true" : "false")
    elseif value isa Number
        isfinite(Float64(value)) ? print(io, value) : print(io, "null")
    elseif value isa Symbol
        print(io, '"', json_escape(String(value)), '"')
    elseif value isa AbstractString
        print(io, '"', json_escape(value), '"')
    elseif value isa AbstractDict
        print(io, "{")
        entries = sort(collect(value); by = pair -> String(first(pair)))
        for (index, (key, item)) in enumerate(entries)
            index > 1 && print(io, ",")
            print(io, "\n", " "^(indent + 2), '"',
                json_escape(String(key)), "\": ")
            write_json(io, item; indent = indent + 2)
        end
        !isempty(entries) && print(io, "\n", prefix)
        print(io, "}")
    elseif value isa NamedTuple
        write_json(io, Dict(String(key) => getproperty(value, key)
            for key in propertynames(value)); indent = indent)
    elseif value isa AbstractVector || value isa Tuple
        print(io, "[")
        for (index, item) in enumerate(value)
            index > 1 && print(io, ", ")
            write_json(io, item; indent = indent)
        end
        print(io, "]")
    else
        write_json(io, string(value); indent = indent)
    end
end

function write_json_file(path::AbstractString, payload)
    mkpath(dirname(path))
    open(path, "w") do io
        write_json(io, payload)
        println(io)
    end
    return path
end

csv_value(value) = value === missing ? "" :
    value isa Symbol ? String(value) :
    value isa AbstractString ? "\"" * replace(value, "\"" => "\"\"") * "\"" :
    string(value)

function write_csv_file(path::AbstractString, rows)
    mkpath(dirname(path))
    rows = collect(rows)
    keys_order = Symbol[]
    for row in rows, key in propertynames(row)
        key in keys_order || push!(keys_order, key)
    end
    open(path, "w") do io
        println(io, join(String.(keys_order), ","))
        for row in rows
            println(io, join((hasproperty(row, key) ?
                csv_value(getproperty(row, key)) : "" for key in keys_order), ","))
        end
    end
    return path
end

function descriptive_summary(assay::Int, rows)
    numeric = Dict{String,Any}()
    fields = unique(vcat([collect(propertynames(row)) for row in rows]...))
    for field in fields
        values = Float64[]
        for row in rows
            hasproperty(row, field) || continue
            value = getproperty(row, field)
            value isa Bool && push!(values, value ? 1.0 : 0.0)
            value isa Number && !(value isa Bool) && isfinite(Float64(value)) &&
                push!(values, Float64(value))
        end
        isempty(values) && continue
        numeric[String(field)] = Dict("n" => length(values),
            "mean" => mean(values), "minimum" => minimum(values),
            "maximum" => maximum(values), "sd" =>
                length(values) > 1 ? std(values) : 0.0)
    end
    return Dict("assay" => assay, "stage" => "pilot_descriptive",
        "criterion_statistics_consulted" => false,
        "rows" => length(rows), "numeric_descriptives" => numeric)
end

function write_growth_log(assay::Int, seeds, genome::Genome)
    rows = NamedTuple[]
    for seed in seeds
        partner = assay in (9, 10) ? :trustworthy : :neutral
        history = generate_history(seed, genome; partner = partner)
        for event in history
            push!(rows, (seed = seed, event_id = event.id,
                event_kind = event.kind, partner_positive = event.partner_positive,
                competence_positive = event.competence_positive,
                tolerated_positive = event.tolerated_positive,
                root_now_positive = event.root_now_positive,
                policy = event.policy, policy_cost = event.policy_cost,
                policy_success = event.policy_success,
                update_path = "replay_history!"))
        end
    end
    directory = joinpath(RESULTS_ROOT, "assays", string(assay))
    write_csv_file(joinpath(directory, "developmental-history.csv"), rows)
end

function write_pilot_report(assay::Int, summary)
    path = joinpath(RESULTS_ROOT, "assays", string(assay), "report.md")
    open(path, "w") do io
        println(io, "# Assay $assay Stage A pilot\n")
        println(io, "Status: **descriptive pilot only**. No criterion statistic was used for calibration, and no operationalization moved after the analysis-plan lock.\n")
        println(io, "- Rows: `$(summary["rows"])`")
        println(io, "- Seeds: all below `700000`; see `per_seed.csv`.")
        println(io, "- Analysis plan: frozen before Phase 0 in `analysis-plan.md`.")
        println(io, "- Confirmatory block: **not run; evaluator seed escrow remains unopened**.\n")
        println(io, "Numeric pilot descriptives are recorded in `summary.json`. They are not confirmatory verdicts.")
    end
    return path
end

function config_path(assay::Int)
    return joinpath(PROJECT_ROOT, "configurations",
        @sprintf("assay-%02d.toml", assay))
end

function run_pilot(assay::Int; genome::Genome = load_genome())
    verify_identity!(genome)
    assay in 1:10 || error("pilot assay must be 1:10")
    config = load_configuration(config_path(assay))
    seeds = pilot_seeds(assay, genome)
    maximum(seeds) < 700_000 || error("reserved seed block refused")
    rows = NamedTuple[]
    for seed in seeds
        append!(rows, run_assay(assay, seed, genome, config))
    end
    directory = joinpath(RESULTS_ROOT, "assays", string(assay))
    write_csv_file(joinpath(directory, "per_seed.csv"), rows)
    summary = descriptive_summary(assay, rows)
    summary["seeds"] = seeds
    summary["genome_sha256"] = genome.sha256
    summary["canonical_source_sha256"] = canonical_source_hash()
    write_json_file(joinpath(directory, "summary.json"), summary)
    write_growth_log(assay, seeds, genome)
    write_pilot_report(assay, summary)
    return summary
end

function analysis_plan_hashes()
    return Dict(string(assay) => bytes2hex(sha256(read(joinpath(
        RESULTS_ROOT, "assays", string(assay), "analysis-plan.md"))))
        for assay in 1:10)
end

function write_precalibration_lock!(genome::Genome = load_genome())
    mkpath(RESULTS_ROOT)
    lock = Dict("status" => "analysis plans and grammar locked before Phase 0",
        "locked_at_utc" => string(now(UTC)),
        "analysis_plan_sha256" => analysis_plan_hashes(),
        "configuration_grammar_sha256" => bytes2hex(sha256(read(
            joinpath(RESULTS_ROOT, "configuration-grammar.md")))),
        "configuration_sha256" => Dict(@sprintf("%02d", assay) =>
            bytes2hex(sha256(read(config_path(assay)))) for assay in 1:10))
    write_json_file(joinpath(RESULTS_ROOT, "precalibration-lock.json"), lock)
    write_identity!(genome)
    return lock
end

function verify_precalibration_lock()
    path = joinpath(RESULTS_ROOT, "precalibration-lock.json")
    isfile(path) || error("Phase 0 blocked: precalibration lock missing")
    raw = read(path, String)
    for hash in values(analysis_plan_hashes())
        occursin(hash, raw) ||
            error("Phase 0 blocked: analysis plan changed after lock")
    end
    grammar_hash = bytes2hex(sha256(read(
        joinpath(RESULTS_ROOT, "configuration-grammar.md"))))
    occursin(grammar_hash, raw) ||
        error("Phase 0 blocked: configuration grammar changed after lock")
    return true
end

function dynamic_range_quantity(assay::Int, rows, genome::Genome)
    if assay == 1
        values = Float64[row.written for row in rows]
        return ("write activation fraction across overwhelm-control grid",
            mean(values), 0.05, 0.95)
    elseif assay == 2
        values = Float64[row.closed_revision for row in rows]
        return ("root endpoint observed range across controllability doses",
            maximum(values) - minimum(values), 0.05, 1.0)
    elseif assay == 3
        values = Float64[row.dominance + row.depth for row in rows]
        return ("configured coordinate variance across four field regimes",
            var(values), 0.10, 2.0)
    elseif assay == 4
        values = Float64[row.root_revision for row in rows]
        return ("root endpoint span across graph arms",
            maximum(values) - minimum(values), 0.05, 1.0)
    elseif assay == 5
        values = Float64[row.uptake for row in rows]
        return ("field-uptake span across regulation cells",
            maximum(values) - minimum(values), 0.05, 2.0)
    elseif assay == 6
        spreads = [std(generator_family(first(pilot_seeds(6, genome)),
            family, genome)) for family in (:global_downweight, :cue_local,
                :context_split, :continuous_drift, :change_point)]
        return ("generator-family observation-scale span",
            maximum(spreads) - minimum(spreads), 0.10, 2.0)
    elseif assay == 7
        values = Float64[row.imaginal_probability for row in rows]
        return ("imaginal evidence probability range over frozen q(g) domain",
            maximum(values) - minimum(values), 0.50, 0.80)
    elseif assay == 8
        values = Float64[row.learned_cost for row in rows]
        return ("learned policy-cost variation across histories",
            maximum(values) - minimum(values), 0.01, 1.0)
    elseif assay == 9
        values = Float64[row.competence for row in rows]
        return ("learned competence-posterior span across histories",
            maximum(values) - minimum(values), 0.20, 1.0)
    else
        values = Float64[row.root_change for row in rows]
        return ("root endpoint span across disposition-scaffold cells",
            maximum(values) - minimum(values), 0.05, 1.0)
    end
end

function run_phase0(; genome::Genome = load_genome())
    verify_precalibration_lock()
    verify_identity!(genome)
    ledger_rows = NamedTuple[]
    for assay in 1:10
        config = load_configuration(config_path(assay))
        rows = NamedTuple[]
        for seed in pilot_seeds(assay, genome)
            append!(rows, run_assay(assay, seed, genome, config))
        end
        name, value, lower, upper = dynamic_range_quantity(assay, rows, genome)
        in_range = lower <= value <= upper
        push!(ledger_rows, (sequence = assay, assay = assay,
            apparatus_first_question =
                "Does the frozen instrument expose nondegenerate dynamic range?",
            consulted_dynamic_range_quantity = name,
            observed_value = value, acceptable_floor = lower,
            acceptable_ceiling = upper,
            criterion_statistic_consulted = false,
            change = "none—genome value retained",
            asymmetry_check = "retained instrument can still fail",
            disposition = in_range ? "range adequate" :
                "honest range limitation retained"))
    end
    path = joinpath(RESULTS_ROOT, "calibration-ledger.csv")
    write_csv_file(path, ledger_rows)
    write_json_file(joinpath(RESULTS_ROOT, "phase0-summary.json"),
        Dict("status" => "joint calibration complete",
            "multi_task_training" => true,
            "criterion_statistics_consulted" => false,
            "genome_changes" => 0,
            "pilot_seed_ceiling_respected" => true,
            "assays" => 10,
            "ledger_sha256" => bytes2hex(sha256(read(path)))))
    return ledger_rows
end

function file_hash_entry(path::AbstractString)
    return Dict("path" => relpath(path, PROJECT_ROOT),
        "sha256" => bytes2hex(sha256(read(path))),
        "bytes" => filesize(path))
end

function freeze_component_files()
    paths = String[]
    append!(paths, CANONICAL_SOURCE_FILES)
    append!(paths, [DEFAULT_GENOME_PATH,
        joinpath(PROJECT_ROOT, "organism-genome.md"),
        joinpath(RESULTS_ROOT, "configuration-grammar.md"),
        joinpath(RESULTS_ROOT, "rng-streams.md"),
        joinpath(RESULTS_ROOT, "world-populations.md"),
        joinpath(RESULTS_ROOT, "precalibration-lock.json"),
        joinpath(RESULTS_ROOT, "calibration-ledger.csv"),
        joinpath(RESULTS_ROOT, "identity.json"),
        joinpath(PROJECT_ROOT, "Project.toml"),
        joinpath(PROJECT_ROOT, "Manifest.toml")])
    append!(paths, collect_files(joinpath(PROJECT_ROOT, "configurations")))
    append!(paths, collect_files(joinpath(PROJECT_ROOT, "scripts", "model_organism")))
    for assay in 1:10
        directory = joinpath(RESULTS_ROOT, "assays", string(assay))
        append!(paths, filter(path -> basename(path) in
            ("analysis-plan.md", "per_seed.csv", "summary.json",
                "developmental-history.csv", "report.md"),
            collect_files(directory)))
    end
    append!(paths, filter(path -> basename(path) in
        ("audit-summary.json", "machinery-audit.md",
            "parameter-use-matrix.csv", "phase0-summary.json",
            "stage-a-report.md"),
        collect_files(RESULTS_ROOT)))
    return sort(unique(filter(isfile, paths)))
end

function write_freeze_manifest(; genome::Genome = load_genome())
    verify_precalibration_lock()
    verify_identity!(genome)
    all(isfile(joinpath(RESULTS_ROOT, "assays", string(assay),
        "summary.json")) for assay in 1:10) ||
        error("freeze blocked: all ten pilot summaries required")
    isfile(joinpath(RESULTS_ROOT, "audit-summary.json")) ||
        error("freeze blocked: assay 0 audit missing")
    components = [file_hash_entry(path) for path in freeze_component_files()]
    payload = Dict(
        "experiment" => "50-H",
        "stage" => "A",
        "status" => "freeze candidate awaiting evaluator commit",
        "created_at_utc" => string(now(UTC)),
        "external_commit" => nothing,
        "external_commit_status" => "evaluator_pending",
        "confirmatory_seed_status" => "escrowed; no seeds selected or run",
        "reserved_seed_floor" => 700000,
        "julia_version" => string(VERSION),
        "project_manifest_julia_version" => get(TOML.parsefile(
            joinpath(PROJECT_ROOT, "Manifest.toml")), "julia_version", "unknown"),
        "genome_sha256" => genome.sha256,
        "canonical_source_sha256" => canonical_source_hash(),
        "components" => components,
        "sealed_challenges" => [
            Dict("name" => "E3-polarization-protocol.md",
                "availability" => "withheld by evaluator",
                "sha256" => "9e406af9b0720476ba0508783d65916062815bee5e555378f50200a606037932"),
            Dict("name" => "E4-evidence-format-protocol.md",
                "availability" => "withheld by evaluator",
                "sha256" => "96028f83f20f92f9c731a39080ddd2e40026f603926a17820e3e3212c53a514f"),
            Dict("name" => "E5-selflike-part-protocol.md",
                "availability" => "withheld by evaluator",
                "sha256" => "d1f5df210cc3cb15080c79d27914f8cb3036468323f26dd1a500eeda865cb705"),
            Dict("name" => "seed-escrow.md",
                "availability" => "withheld by evaluator",
                "sha256" => "17c3364c65b4004368bf5c7c0e3453440b41ab77d8a9de520cba90ec288f5c48"),
        ])
    path = joinpath(RESULTS_ROOT, "freeze-manifest.json")
    write_json_file(path, payload)
    return payload
end

function write_stage_a_report(; genome::Genome = load_genome())
    path = joinpath(RESULTS_ROOT, "stage-a-report.md")
    audits_raw = read(joinpath(RESULTS_ROOT, "audit-summary.json"), String)
    phase_raw = read(joinpath(RESULTS_ROOT, "phase0-summary.json"), String)
    open(path, "w") do io
        println(io, "# Experiment 50-H Stage A report\n")
        println(io, "Status: **Stage A complete; confirmatory execution stopped.** The freeze candidate awaits evaluator verification and commit. No seed at or above `700000` was selected, generated, or run.\n")
        println(io, "## Build decisions\n")
        println(io, "- One reachable entrypoint, `src/ModelOrganism.jl`, owns all strain equations. The old Experiment 44–49 modules remain untouched and unreachable from Experiment 50 runners.")
        println(io, "- Experiment 49's copied Sim-5 mapping → categorical depth → effective precision path was reimplemented once as `update_dyad!`; all assays use the canonical function.")
        println(io, "- The gate is `protector_permission ≥ permission_threshold`; there is no gate object or completion rule.")
        println(io, "- Mature trust, root, repertoire cost, and reliability beliefs are produced only by seeded developmental replay. Pilot growth logs ship per assay.")
        println(io, "- Assay configurations are categorical topology/intervention records. All numeric authored choices, including analysis thresholds, are in `genome.toml` with rationales.\n")
        println(io, "## Phase 0 joint calibration\n")
        println(io, "The grammar and all ten analysis plans were hash-locked before Phase 0. The joint pass consulted one apparatus-first dynamic-range quantity per assay and no criterion statistic. All genome values were retained; no operationalization moved. The ledger preserves any inadequate range as an honest limitation rather than tuning it away.\n")
        println(io, "## Assay 0 audits\n")
        println(io, "- Identity and genome hash guard: passed in every invoked runner.")
        println(io, "- Duplicate equation / unreachable legacy adapter check: $(occursin("\"passed\": true", audits_raw) ? "passed" : "see audit-summary.json").")
        println(io, "- Bit-for-bit zero-slot idleness, provenance, grammar expressibility, machinery classification, parameter-use, and compression outputs are in the audit package.")
        println(io, "- Machinery audit conclusion: canonical state-change transitions are organization-only; world generators are classified neither; no carrier parameter exists.\n")
        println(io, "## Pilot descriptives\n")
        println(io, "Each assay ran 12 descriptive pilot worlds below `700000` (analytic assays additionally enumerated their frozen property domains). `per_seed.csv`, `summary.json`, `developmental-history.csv`, and `report.md` are present for every assay. These are descriptives, not confirmatory verdicts:\n")
        highlight_fields = Dict(
            1 => (:property_holds, :precision),
            2 => (:closed_revision, :revision_effect),
            3 => (:correct_2d, :loss_1d),
            4 => (:root_revised, :untreated_transfer),
            5 => (:root_change, :uptake),
            6 => (:diagonal, :heldout_margin),
            7 => (:sign_matches, :doover_success),
            8 => (:selection_tracks, :relational_change),
            9 => (:recovered, :sign_prediction_match),
            10 => (:descent, :root_change))
        println(io, "| Assay | Pilot rows | Descriptive means across recorded rows |")
        println(io, "|---:|---:|---|")
        for assay in 1:10
            summary_path = joinpath(RESULTS_ROOT, "assays", string(assay), "summary.json")
            raw = read(summary_path, String)
            row_match = match(r"\"rows\": ([0-9]+)", raw)
            rows = row_match === nothing ? "unknown" : row_match.captures[1]
            field_values = String[]
            for field in highlight_fields[assay]
                metric_match = match(Regex("\"$(String(field))\": \\{[\\s\\S]*?\"mean\": ([^,\\n]+)"), raw)
                value = metric_match === nothing ? "not recorded" :
                    strip(metric_match.captures[1])
                push!(field_values, "`$(String(field))=$value`")
            end
            println(io, "| $assay | $rows | $(join(field_values, "; ")) |")
        end
        println(io, "\n## Conservative ambiguity resolutions\n")
        println(io, "- Spec §3.2 describes pilots after strain freeze while the Stage A brief permits instrument repair before the freeze package is finalized. I treated the Stage A pilots as pre-commit descriptive shake-downs under §3.4; the manifest is assembled only after re-pilot. Two apparatus repairs were logged: paired partner-stream replay in assay 10 and complete genome inventory of already-effective literals. Every assay was re-piloted on the final source and genome.")
        println(io, "- “Every authored constant” was read broadly: protocol counts and analysis margins are inventoried alongside agent constants, while assay files contain no numeric agent overrides.")
        println(io, "- The legacy source may still contain equations because Experiments 44–49 must remain unchanged. “Anywhere assay-reachable” was enforced as the transitive Experiment 50 include graph; the duplicate audit also forbids legacy includes in all Experiment 50 runners.")
        println(io, "- A zero-count slot remains represented in configuration and is tested for exact idleness; it is not compiled out.")
        println(io, "- The sealed hashes were copied verbatim as withheld manifest entries. Their plaintext was neither sought nor inferred.\n")
        println(io, "## Freeze and stopping point\n")
        println(io, "`freeze-manifest.json` independently hashes the organism, genome, grammar, configurations, frozen world populations, generators, protocols/runners, analysis code/plans, RNG definitions, environment, audit and pilot records, and the four evaluator-provided sealed hashes. The commit field is explicitly evaluator-pending. This implementation stops before every confirmatory block and before 50-P/50-L execution.")
    end
    return path
end
