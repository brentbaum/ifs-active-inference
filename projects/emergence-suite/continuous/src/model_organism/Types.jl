struct Genome
    id::String
    schema_version::Int
    values::Dict{Symbol,Float64}
    rationales::Dict{Symbol,String}
    path::String
    sha256::String
end

struct Configuration
    assay::Int
    id::String
    nodes::Vector{Symbol}
    edges::Vector{Symbol}
    slots::Dict{Symbol,Int}
    initializers::Vector{Symbol}
    interventions::Vector{Symbol}
    observations::Vector{Symbol}
    source_path::String
end

struct ProvenanceEvent
    step::Int
    variable::Symbol
    old_value::Float64
    new_value::Float64
    update_function::Symbol
    event_kind::Symbol
    event_id::String
end

mutable struct StrainState
    posterior::Dict{Symbol,Float64}
    policy_cost::Dict{Symbol,Float64}
    policy_reliability::Dict{Symbol,Float64}
    field::Dict{Symbol,Float64}
    dyad_mapping::Matrix{Float64}
    dyad_depth::Vector{Float64}
    dyad_accumulator::Float64
    episodic_write::Vector{Float64}
    provenance::Dict{Symbol,ProvenanceEvent}
    log::Vector{ProvenanceEvent}
end

const REQUIRED_POSTERIORS = (
    :root_then, :root_now, :outcome_forecast, :co_protection,
    :partner_trustworthy, :partner_adverse, :relational_prior,
)
const POLICY_NAMES = (:exclusion, :hypervigilance, :internal_attack, :oscillation)
const FIELD_CHANNELS = (:part, :context, :interoception, :relational, :policy)

function genome_hash(path::AbstractString = DEFAULT_GENOME_PATH)
    return bytes2hex(sha256(read(path)))
end

function load_genome(path::AbstractString = DEFAULT_GENOME_PATH)
    raw = TOML.parsefile(path)
    haskey(raw, "genome_id") || error("genome_id missing")
    haskey(raw, "schema_version") || error("schema_version missing")
    tables = get(raw, "constants", Dict())
    isempty(tables) && error("genome constants missing")
    values = Dict{Symbol,Float64}()
    rationales = Dict{Symbol,String}()
    for (name, entry) in tables
        haskey(entry, "value") || error("constant $name has no value")
        haskey(entry, "rationale") || error("constant $name has no rationale")
        value = Float64(entry["value"])
        isfinite(value) || error("constant $name is not finite")
        rationale = strip(String(entry["rationale"]))
        isempty(rationale) && error("constant $name has empty rationale")
        key = Symbol(name)
        haskey(values, key) && error("duplicate genome constant $name")
        values[key] = value
        rationales[key] = rationale
    end
    return Genome(String(raw["genome_id"]), Int(raw["schema_version"]),
        values, rationales, String(path), genome_hash(path))
end

g(genome::Genome, name::Symbol) =
    get(genome.values, name) do
        error("undeclared genome constant: $name")
    end

function _symbols(raw, key)
    return Symbol.(String.(get(raw, key, String[])))
end

function load_configuration(path::AbstractString)
    raw = TOML.parsefile(path)
    allowed = Set(["assay", "id", "nodes", "edges", "slots",
        "initializers", "interventions", "observations"])
    extras = setdiff(Set(keys(raw)), allowed)
    isempty(extras) || error("unknown configuration keys: $(collect(extras))")
    for key in ("assay", "id", "nodes", "edges", "slots",
            "initializers", "interventions", "observations")
        haskey(raw, key) || error("configuration missing $key")
    end
    slots = Dict{Symbol,Int}()
    for (name, value) in raw["slots"]
        value isa Integer ||
            error("slots may contain counts only; numeric agent overrides are forbidden")
        slots[Symbol(name)] = Int(value)
    end
    return Configuration(Int(raw["assay"]), String(raw["id"]),
        _symbols(raw, "nodes"), _symbols(raw, "edges"), slots,
        _symbols(raw, "initializers"), _symbols(raw, "interventions"),
        _symbols(raw, "observations"), String(path))
end

function neutral_state(genome::Genome)
    neutral = g(genome, :neutral_probability)
    posterior = Dict(name => neutral for name in REQUIRED_POSTERIORS)
    policy_cost = Dict(name => neutral for name in POLICY_NAMES)
    policy_reliability = Dict(name => neutral for name in POLICY_NAMES)
    field = Dict(name => 1.0 for name in FIELD_CHANNELS)
    depth_states = Int(g(genome, :dyad_depth_states))
    prior_count = g(genome, :dyad_mapping_prior_count)
    state = StrainState(posterior, policy_cost, policy_reliability, field,
        fill(prior_count, 4, 2), fill(inv(depth_states), depth_states),
        0.0, Float64[], Dict{Symbol,ProvenanceEvent}(), ProvenanceEvent[])
    step = 0
    for variable in REQUIRED_POSTERIORS
        step += 1
        event = ProvenanceEvent(step, variable, neutral, neutral,
            :neutral_state, :neutral_prior, "neutral:$variable")
        state.provenance[variable] = event
        push!(state.log, event)
    end
    for policy in POLICY_NAMES
        for prefix in (:cost_, :reliability_)
            step += 1
            variable = Symbol(prefix, policy)
            event = ProvenanceEvent(step, variable, neutral, neutral,
                :neutral_state, :neutral_prior, "neutral:$variable")
            state.provenance[variable] = event
            push!(state.log, event)
        end
    end
    return state
end
