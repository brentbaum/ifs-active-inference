#!/usr/bin/env julia

module SeedEscrow
include(joinpath(@__DIR__, "seed_escrow.jl"))
end

function sample_escrow()
    blocks = String[]
    for (order, class) in enumerate(("H", "C", "P", "L"))
        push!(blocks, """
[[release_blocks]]
id = "block-$(lowercase(class))"
class = "$class"
purpose = "purpose-$(lowercase(class))"
count = 2
release_order = $order
master_seed_hex = "$(lpad(string(order, base = 16), 64, '0'))"
""")
    end
    return """
experiment_id = "experiment-51"
contract_id = "ifs-ai-experiment-51-contract"
contract_version = "1.0.0"
contract_commit = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
rng_convention = "rng-51-v1"
generation = "os-csprng-256"

$(join(blocks, "\n"))"""
end

function expect_failure(operation, label)
    try
        operation()
    catch
        println("rejected: $label")
        return
    end
    error("seed escrow rejection unexpectedly passed: $label")
end

function main()
    mktempdir() do directory
        path = joinpath(directory, "escrow.toml")
        write(path, sample_escrow())
        expected_commit = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        escrow, raw_bytes = SeedEscrow.validate_escrow(path;
            expected_contract_commit = expected_commit)
        commitments = [SeedEscrow.block_commitment(escrow, block)
            for block in escrow["release_blocks"]]
        length(unique(commitments)) == 4 ||
            error("sample commitments are not unique")

        changed = deepcopy(escrow)
        changed["release_blocks"][1]["purpose"] = "changed-purpose"
        SeedEscrow.block_commitment(changed, changed["release_blocks"][1]) !=
            commitments[1] || error("purpose is not commitment-bound")
        changed = deepcopy(escrow)
        changed["release_blocks"][1]["release_order"] = 2
        SeedEscrow.block_commitment(changed, changed["release_blocks"][1]) !=
            commitments[1] || error("release order is not commitment-bound")
        changed = deepcopy(escrow)
        changed["experiment_id"] = "experiment-52"
        SeedEscrow.block_commitment(changed, changed["release_blocks"][1]) !=
            commitments[1] || error("experiment ID is not commitment-bound")

        expect_failure("wrong expected contract commit") do
            SeedEscrow.validate_escrow(path;
                expected_contract_commit =
                    "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
        end
        manifest = SeedEscrow.public_manifest(escrow, raw_bytes)
        occursin("contract_commit=$expected_commit", manifest) ||
            error("public manifest omits expected contract commit")
        occursin("purpose-", manifest) &&
            error("public manifest leaks private purpose")

        write(path, replace(sample_escrow(),
            "release_order = 2" => "release_order = 1"))
        expect_failure("duplicate release order") do
            SeedEscrow.validate_escrow(path)
        end
    end
    println("seed escrow conformance passed")
    return true
end

main()
