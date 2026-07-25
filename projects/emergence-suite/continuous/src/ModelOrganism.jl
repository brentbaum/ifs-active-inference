module ModelOrganism

using Random
using Statistics
using SHA
using TOML
using Dates
using Printf

const SOURCE_ROOT = @__DIR__
const PROJECT_ROOT = normpath(joinpath(SOURCE_ROOT, ".."))
const DEFAULT_GENOME_PATH = joinpath(PROJECT_ROOT, "genome.toml")
const RESULTS_ROOT = joinpath(PROJECT_ROOT, "results", "model_organism")

include("model_organism/Types.jl")
include("model_organism/Equations.jl")
include("model_organism/Assays.jl")
include("model_organism/Audits.jl")
include("model_organism/RecordIO.jl")

export Genome, Configuration, StrainState, ProvenanceEvent, load_genome,
    load_configuration, neutral_state, replay_history!, generate_history,
    run_assay, run_pilot, run_phase0, run_audits, write_freeze_manifest,
    genome_hash, verify_identity!, write_stage_a_report

end
