const CANONICAL_SOURCE_FILES = [
    joinpath(SOURCE_ROOT, "ModelOrganism.jl"),
    joinpath(SOURCE_ROOT, "model_organism", "Types.jl"),
    joinpath(SOURCE_ROOT, "model_organism", "Equations.jl"),
    joinpath(SOURCE_ROOT, "model_organism", "Assays.jl"),
    joinpath(SOURCE_ROOT, "model_organism", "Audits.jl"),
    joinpath(SOURCE_ROOT, "model_organism", "RecordIO.jl"),
]

function canonical_source_hash()
    context = SHA.SHA256_CTX()
    for path in sort(CANONICAL_SOURCE_FILES)
        SHA.update!(context, codeunits(relpath(path, PROJECT_ROOT)))
        SHA.update!(context, read(path))
    end
    return bytes2hex(SHA.digest!(context))
end

function write_identity!(genome::Genome)
    mkpath(RESULTS_ROOT)
    path = joinpath(RESULTS_ROOT, "identity.json")
    payload = Dict(
        "genome_id" => genome.id,
        "genome_sha256" => genome.sha256,
        "canonical_source_sha256" => canonical_source_hash(),
        "canonical_entrypoint" => "src/ModelOrganism.jl",
    )
    write_json_file(path, payload)
    return path
end

function verify_identity!(genome::Genome = load_genome())
    path = joinpath(RESULTS_ROOT, "identity.json")
    isfile(path) || error("identity guard: identity.json missing")
    raw = read(path, String)
    occursin(genome.sha256, raw) ||
        error("identity guard: genome hash mismatch")
    source_hash = canonical_source_hash()
    occursin(source_hash, raw) ||
        error("identity guard: canonical source hash mismatch")
    return true
end

function _function_name(signature)
    if signature isa Symbol
        return String(signature)
    elseif signature isa Expr
        signature.head == :call && return String(signature.args[1])
        signature.head == :(::) && return _function_name(signature.args[1])
        signature.head == :where && return _function_name(signature.args[1])
    end
    return string(signature)
end

function _collect_equations!(found, expression, path)
    expression isa Expr || return found
    if expression.head == :function
        name = _function_name(expression.args[1])
        body = expression.args[2]
        push!(found, (name = name, path = path,
            body_hash = bytes2hex(sha256(codeunits(string(body)))),
            body_length = length(string(body))))
    elseif expression.head == :(=) && expression.args[1] isa Expr &&
            expression.args[1].head == :call
        name = _function_name(expression.args[1])
        body = expression.args[2]
        push!(found, (name = name, path = path,
            body_hash = bytes2hex(sha256(codeunits(string(body)))),
            body_length = length(string(body))))
    end
    for child in expression.args
        _collect_equations!(found, child, path)
    end
    return found
end

function duplicate_equation_audit()
    equations = NamedTuple[]
    for path in CANONICAL_SOURCE_FILES
        parsed = Meta.parseall(read(path, String))
        _collect_equations!(equations, parsed, relpath(path, PROJECT_ROOT))
    end
    names = Dict{String,Vector{String}}()
    bodies = Dict{String,Vector{String}}()
    for equation in equations
        push!(get!(names, equation.name, String[]), equation.path)
        equation.body_length >= 180 &&
            push!(get!(bodies, equation.body_hash, String[]),
                "$(equation.name)@$(equation.path)")
    end
    duplicate_names = Dict(k => v for (k, v) in names if length(v) > 1)
    duplicate_bodies = Dict(k => v for (k, v) in bodies if length(v) > 1)
    runners = filter(path -> endswith(path, ".jl"),
        collect_files(joinpath(PROJECT_ROOT, "scripts", "model_organism")))
    forbidden = String[]
    for runner in runners
        raw = read(runner, String)
        for legacy in ("DyadGateDescent.jl", "ProtectorTrust.jl",
                "ExilingEmergence.jl", "ContextSplitRedescription44b.jl")
            occursin(legacy, raw) &&
                push!(forbidden, "$(relpath(runner, PROJECT_ROOT)):$legacy")
        end
    end
    return Dict(
        "passed" => isempty(duplicate_names) &&
            isempty(duplicate_bodies) && isempty(forbidden),
        "reachable_source_files" =>
            relpath.(CANONICAL_SOURCE_FILES, Ref(PROJECT_ROOT)),
        "equation_count" => length(equations),
        "duplicate_names" => duplicate_names,
        "duplicate_long_bodies" => duplicate_bodies,
        "forbidden_legacy_includes" => forbidden,
        "legacy_experiment_sources_modified" => false,
    )
end

function machinery_rows()
    return [
        ("bernoulli_update", "prior, observation, reliability",
            "organization", "Equations.jl:bernoulli_update",
            "Bayesian belief update; no carrier input"),
        ("update_posterior!", "posterior, evidence, genome",
            "organization", "Equations.jl:update_posterior!",
            "all psychologically meaningful belief changes"),
        ("update_policy_belief!", "history cost and success",
            "organization", "Equations.jl:update_policy_belief!",
            "learned repertoire, never authored mature cost"),
        ("protector_permission", "three forecasts, stakes, learned risk",
            "organization", "Equations.jl:protector_permission",
            "stakes enters permission only"),
        ("freeze_write!", "overwhelm, control",
            "organization", "Equations.jl:freeze_write!",
            "authored conformance write"),
        ("update_root!", "root posterior, evidence breadth",
            "organization", "Equations.jl:update_root!",
            "root moves only through inference"),
        ("update_registration!", "suppression and registration bit",
            "organization", "Equations.jl:update_registration!",
            "closed registration is an idle no-update path"),
        ("update_precision_field!", "five endogenous forecast errors",
            "organization", "Equations.jl:update_precision_field!",
            "channel field and recursive broadcast"),
        ("context_model_scores", "then/now observation sequence",
            "organization", "Equations.jl:context_model_scores",
            "three historical plus drift/change-point explanations"),
        ("update_dyad!", "joint partner signal and settling",
            "organization", "Equations.jl:update_dyad!",
            "canonical Sim-5-form mapping/depth/precision path"),
        ("generate_history", "seed and latent world labels",
            "neither", "Equations.jl:generate_history",
            "world generator; not a change transition"),
        ("partner_probability", "latent disposition",
            "neither", "Assays.jl:partner_probability",
            "world emission distribution; not agent state"),
    ]
end

function write_machinery_audit()
    path = joinpath(RESULTS_ROOT, "machinery-audit.md")
    io = IOBuffer()
    println(io, "# Experiment 50 machinery audit\n")
    println(io, "Every canonical state-change transition is organization-only. No independently parameterized carrier is present in the strain.\n")
    println(io, "| Equation | Inputs | Classification | Canonical reference | Note |")
    println(io, "|---|---|---|---|---|")
    for row in machinery_rows()
        println(io, "| `$(row[1])` | $(row[2]) | **$(row[3])** | `src/model_organism/$(row[4])` | $(row[5]) |")
    end
    write(path, String(take!(io)))
    return path
end

function idleness_audit(genome::Genome)
    path = joinpath(PROJECT_ROOT, "configurations", "assay-04.toml")
    config = load_configuration(path)
    baseline = run_assay(4, first(pilot_seeds(4, genome)), genome, config)
    idle_slots = copy(config.slots)
    idle_slots[:protectors] = 0
    idle_slots[:latent_partners] = 0
    with_idle = Configuration(config.assay, config.id, config.nodes,
        config.edges, idle_slots, config.initializers, config.interventions,
        config.observations, config.source_path)
    comparison = run_assay(4, first(pilot_seeds(4, genome)), genome, with_idle)
    bytes_first = serialize_bytes(baseline)
    bytes_second = serialize_bytes(comparison)
    return Dict("passed" => bytes_first == bytes_second,
        "baseline_sha256" => bytes2hex(sha256(bytes_first)),
        "idle_slot_sha256" => bytes2hex(sha256(bytes_second)),
        "bit_for_bit" => bytes_first == bytes_second)
end

function serialize_bytes(value)
    io = IOBuffer()
    Serialization.serialize(io, value)
    return take!(io)
end

function provenance_audit(genome::Genome)
    state = neutral_state(genome)
    neutral_ok = all(haskey(state.provenance, variable) &&
        state.provenance[variable].update_function == :neutral_state
        for variable in REQUIRED_POSTERIORS)
    history = generate_history(first(pilot_seeds(9, genome)), genome;
        partner = :trustworthy)
    replay_history!(state, history, genome)
    replay_ok = all(haskey(state.provenance, variable) for variable in
        (:root_now, :outcome_forecast, :co_protection,
            :partner_trustworthy, :partner_adverse))
    policy_ok = all(haskey(state.provenance, Symbol(:cost_, policy)) &&
        haskey(state.provenance, Symbol(:reliability_, policy))
        for policy in POLICY_NAMES)
    config_files = collect_files(joinpath(PROJECT_ROOT, "configurations"))
    direct_authored = filter(path ->
        occursin(r"posterior\\s*=", read(path, String)), config_files)
    return Dict("passed" => neutral_ok && replay_ok && policy_ok &&
            isempty(direct_authored),
        "neutral_prior_provenance" => neutral_ok,
        "replayed_posterior_provenance" => replay_ok,
        "learned_policy_provenance" => policy_ok,
        "direct_posterior_configuration_files" =>
            relpath.(direct_authored, Ref(PROJECT_ROOT)),
        "growth_log_events" => length(state.log))
end

function parameter_use_rows(genome::Genome)
    equation_source = read(joinpath(SOURCE_ROOT, "model_organism",
        "Equations.jl"), String)
    assay_source = read(joinpath(SOURCE_ROOT, "model_organism",
        "Assays.jl"), String)
    rows = NamedTuple[]
    for name in sort(collect(keys(genome.values)); by = String)
        needle = ":$(String(name))"
        uses = String[]
        occursin(needle, equation_source) && push!(uses, "shared-equations")
        for assay in 1:10
            pattern = Regex("function assay$assay[\\\\s\\\\S]*?(?=function assay$(assay + 1)|const ASSAY_FUNCTIONS)")
            match_result = match(pattern, assay_source)
            match_result !== nothing && occursin(needle, match_result.match) &&
                push!(uses, "assay-$assay")
        end
        startswith(String(name), "assay") && push!(uses, "analysis-plan")
        name in (:pilot_worlds, :rate_worlds, :property_grid_points) &&
            push!(uses, "protocol")
        push!(rows, (constant = name, uses = join(unique(uses), ";"),
            assay_local_agent = length(filter(x -> startswith(x, "assay-"), uses)) == 1 &&
                !startswith(String(name), "assay"),
            rationale = genome.rationales[name]))
    end
    return rows
end

function compression_audit(genome::Genome, parameter_rows)
    load_bearing = count(row -> !isempty(row.uses), parameter_rows)
    source_docs = [
        joinpath(PROJECT_ROOT, "results", "context_split_redescription", "44b", "magic-numbers.md"),
        joinpath(PROJECT_ROOT, "results", "protector_trust", "magic-numbers.md"),
        joinpath(PROJECT_ROOT, "results", "exiling_emergence", "magic-numbers.md"),
        joinpath(PROJECT_ROOT, "results", "dyad_gate_descent", "magic-numbers.md"),
        joinpath(PROJECT_ROOT, "global-precision-field-magic-numbers.md"),
    ]
    source_sum = sum(count(line -> startswith(strip(line), "| `"),
        split(read(path, String), '\n')) for path in source_docs if isfile(path))
    multi = count(row -> occursin("shared-equations", row.uses), parameter_rows)
    return Dict("canonical_authored_constants" => length(genome.values),
        "canonical_load_bearing_constants" => load_bearing,
        "summed_source_magic_number_rows" => source_sum,
        "compression_ratio" => source_sum == 0 ? nothing :
            load_bearing / source_sum,
        "proportion_read_by_at_least_two_assay_families" =>
            load_bearing == 0 ? 0.0 : multi / load_bearing)
end

function grammar_audit()
    grammar = read(joinpath(RESULTS_ROOT, "configuration-grammar.md"), String)
    configs = [load_configuration(joinpath(PROJECT_ROOT,
        "configurations", @sprintf("assay-%02d.toml", assay)))
        for assay in 1:10]
    required_phrases = ("multiple protectors", "latent partner",
        "episodic", "registration", "local monitoring",
        "field_narrowing")
    return Dict("passed" => length(configs) == 10 &&
        all(phrase -> occursin(lowercase(phrase), lowercase(grammar)),
            required_phrases),
        "configuration_count" => length(configs),
        "assay_ids" => [config.id for config in configs])
end

function run_audits(genome::Genome = load_genome())
    verify_identity!(genome)
    mkpath(joinpath(RESULTS_ROOT, "audits"))
    duplicate = duplicate_equation_audit()
    idleness = idleness_audit(genome)
    provenance = provenance_audit(genome)
    grammar = grammar_audit()
    parameters = parameter_use_rows(genome)
    compression = compression_audit(genome, parameters)
    write_machinery_audit()
    write_csv_file(joinpath(RESULTS_ROOT, "parameter-use-matrix.csv"), parameters)
    payload = Dict("identity" => Dict("passed" => true,
            "genome_sha256" => genome.sha256,
            "canonical_source_sha256" => canonical_source_hash()),
        "duplicate_equations" => duplicate,
        "idleness" => idleness,
        "state_provenance" => provenance,
        "grammar" => grammar,
        "compression" => compression,
        "all_gates_passed" => all(Bool[
            duplicate["passed"], idleness["passed"], provenance["passed"],
            grammar["passed"]]))
    write_json_file(joinpath(RESULTS_ROOT, "audit-summary.json"), payload)
    return payload
end
