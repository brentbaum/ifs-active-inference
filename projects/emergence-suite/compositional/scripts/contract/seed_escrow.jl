#!/usr/bin/env julia

using SHA
using TOML

const CONTRACT_ID = "ifs-ai-experiment-51-contract"
const CONTRACT_VERSION = "1.0.0"
const EXPERIMENT_ID = "experiment-51"
const ID_PATTERN = r"^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$"

fail(message) = error("seed escrow validation: $message")

function u64be(value::Integer)
    0 <= value <= typemax(UInt64) || fail("integer outside uint64")
    number = UInt64(value)
    return UInt8[(number >> shift) & 0xff for shift in 56:-8:0]
end

function digest_fields(fields)
    bytes = UInt8[]
    for (index, field) in enumerate(fields)
        index > 1 && push!(bytes, 0x00)
        append!(bytes, field isa AbstractVector{UInt8} ?
            field : Vector{UInt8}(codeunits(String(field))))
    end
    return sha256(bytes)
end

function exact_keys(table, expected, label)
    Set(String.(keys(table))) == Set(expected) ||
        fail("$label has unknown or missing keys")
end

function block_commitment(escrow, block)
    return bytes2hex(digest_fields(Any[
        "ifs-ai-51-seed-block-v1",
        escrow["experiment_id"],
        escrow["contract_id"],
        escrow["contract_version"],
        escrow["contract_commit"],
        block["id"],
        block["class"],
        block["purpose"],
        u64be(block["count"]),
        u64be(block["release_order"]),
        hex2bytes(block["master_seed_hex"]),
    ]))
end

function expanded_seed(block, index)
    digest = digest_fields(Any[
        "ifs-ai-51-seed-v1",
        hex2bytes(block["master_seed_hex"]),
        block["class"],
        block["id"],
        u64be(index),
    ])
    digest[1] &= 0x7f
    value = UInt64(0)
    for byte in digest[1:8]
        value = (value << 8) | UInt64(byte)
    end
    return value
end

function validate_escrow(path; expected_contract_commit = nothing)
    raw_bytes = read(path)
    isvalid(String, raw_bytes) || fail("escrow is not UTF-8")
    text = String(raw_bytes)
    occursin('\r', text) && fail("escrow contains CR")
    endswith(text, "\n") || fail("escrow lacks final newline")
    escrow = TOML.parse(text)
    exact_keys(escrow, [
        "experiment_id", "contract_id", "contract_version",
        "contract_commit", "rng_convention", "generation", "release_blocks",
    ], "escrow")
    escrow["experiment_id"] == EXPERIMENT_ID || fail("experiment mismatch")
    escrow["contract_id"] == CONTRACT_ID || fail("contract mismatch")
    escrow["contract_version"] == CONTRACT_VERSION || fail("version mismatch")
    occursin(r"^[0-9a-f]{40}$", escrow["contract_commit"]) ||
        fail("contract_commit must be 40 lowercase hex")
    expected_contract_commit !== nothing &&
        escrow["contract_commit"] != expected_contract_commit &&
        fail("contract_commit does not match expected public contract")
    escrow["rng_convention"] == "rng-51-v1" ||
        fail("RNG convention mismatch")
    escrow["generation"] == "os-csprng-256" || fail("generation mismatch")

    blocks = escrow["release_blocks"]
    isempty(blocks) && fail("no release blocks")
    ids = Set{String}()
    purposes = Set{String}()
    orders = Set{Int}()
    classes = Set{String}()
    seeds = Set{UInt64}()
    total = 0
    for (position, block) in enumerate(blocks)
        exact_keys(block, [
            "id", "class", "purpose", "count", "release_order",
            "master_seed_hex",
        ], "release block")
        id = String(block["id"])
        purpose = String(block["purpose"])
        occursin(ID_PATTERN, id) || fail("invalid block id: $id")
        occursin(ID_PATTERN, purpose) || fail("invalid purpose: $purpose")
        id in ids && fail("duplicate block id: $id")
        purpose in purposes && fail("duplicate purpose: $purpose")
        push!(ids, id)
        push!(purposes, purpose)
        class = String(block["class"])
        class in ("H", "C", "P", "L") || fail("invalid class: $class")
        push!(classes, class)
        count = Int(block["count"])
        1 <= count <= 512 || fail("block $id count outside 1...512")
        total += count
        total <= 4096 || fail("more than 4096 expanded seeds")
        order = Int(block["release_order"])
        order == position || fail("blocks are not in release order")
        order in orders && fail("duplicate release order")
        push!(orders, order)
        seed_hex = String(block["master_seed_hex"])
        occursin(r"^[0-9a-f]{64}$", seed_hex) ||
            fail("block $id master seed must be 64 lowercase hex")
        for index in 0:(count - 1)
            seed = expanded_seed(block, index)
            seed in seeds && fail("expanded seed collision")
            push!(seeds, seed)
        end
    end
    classes == Set(["H", "C", "P", "L"]) ||
        fail("escrow must contain H, C, P, and L classes")
    orders == Set(1:length(blocks)) || fail("release orders are not contiguous")
    return escrow, raw_bytes
end

function public_manifest(escrow, raw_bytes)
    lines = String[
        "contract_commit=$(escrow["contract_commit"])",
        "escrow_sha256=$(bytes2hex(sha256(raw_bytes)))",
        "escrow_bytes=$(length(raw_bytes))",
    ]
    for block in escrow["release_blocks"]
        push!(lines, join([
            "id=$(block["id"])",
            "class=$(block["class"])",
            "count=$(block["count"])",
            "release_order=$(block["release_order"])",
            "commitment=$(block_commitment(escrow, block))",
        ], " "))
    end
    return join(lines, "\n") * "\n"
end

function main(arguments)
    length(arguments) == 3 && arguments[1] == "manifest" || begin
        println("usage: seed_escrow.jl manifest ESCROW.toml EXPECTED_CONTRACT_COMMIT")
        return 2
    end
    expected = String(arguments[3])
    occursin(r"^[0-9a-f]{40}$", expected) ||
        fail("expected contract commit must be 40 lowercase hex")
    escrow, raw_bytes = validate_escrow(arguments[2];
        expected_contract_commit = expected)
    print(public_manifest(escrow, raw_bytes))
    return 0
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main(ARGS))
end
