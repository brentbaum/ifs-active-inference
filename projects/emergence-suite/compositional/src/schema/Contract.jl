module PublicContractValidator
include(normpath(joinpath(@__DIR__, "..", "..", "scripts", "contract",
    "validate_bundle.jl")))
end

function load_documents(directory::AbstractString)
    PublicContractValidator.validate_bundle(directory)
    return BundleDocuments(
        TOML.parsefile(joinpath(directory, "configuration.toml")),
        TOML.parsefile(joinpath(directory, "world.toml")),
        TOML.parsefile(joinpath(directory, "protocol.toml")),
        TOML.parsefile(joinpath(directory, "analysis.toml")),
    )
end

function load_genome(path::AbstractString)
    raw = TOML.parsefile(path)
    expected = Set([
        "genome_id", "contract_id", "contract_version", "learning_rate",
        "message_gain", "policy_temperature", "structure_complexity_penalty",
        "precision_floor", "dirichlet_concentration",
        "approximation_iterations", "approximation_tolerance", "action_costs",
    ])
    Set(keys(raw)) == expected ||
        error("genome has unknown or missing fields")
    raw["contract_id"] == CONTRACT_ID || error("genome contract mismatch")
    raw["contract_version"] == CONTRACT_VERSION ||
        error("genome version mismatch")
    all(value isa Number && isfinite(Float64(value))
        for value in values(raw["action_costs"])) ||
        error("genome action costs must be finite")
    return raw
end
