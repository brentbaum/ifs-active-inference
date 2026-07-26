#!/usr/bin/env julia

using CompositionalOrganism
using TOML

const CO = CompositionalOrganism
const ROOT = normpath(joinpath(@__DIR__, ".."))
const OUTPUT = joinpath(ROOT, "results", "experiment51", "semantic-gate")
const DUMMIES = ("51-P-00", "51-P-90", "51-P-91")
const SEEDS = (10_001, 10_002, 10_003)

mkpath(OUTPUT)

validation_log = joinpath(OUTPUT, "inference-validation.log")
open(validation_log, "w") do io
    run(pipeline(`julia --project=$ROOT $(joinpath(
        ROOT, "scripts", "run_inference_validation.jl"))`,
        stdout = io, stderr = io))
end
validation = TOML.parsefile(joinpath(
    OUTPUT, "inference-validation.toml"))

test_log = joinpath(OUTPUT, "fast-tests.log")
fast_tests_pass = open(test_log, "w") do io
    process = run(pipeline(addenv(
        `julia --project=$ROOT $(joinpath(ROOT, "test", "runtests.jl"))`,
        "CO_FAST_TEST" => "1"), stdout = io, stderr = io); wait = false)
    wait(process)
    success(process)
end
fast_test_output = read(test_log, String)

rows = NamedTuple[]
for (name, seed) in zip(DUMMIES, SEEDS)
    directory = joinpath(ROOT, "protocols", "public-dummies", name)
    documents = load_documents(directory)
    genome = load_genome(joinpath(ROOT, "genome.toml"))
    model = compile_model(documents, genome)
    protocol = CompositionalOrganism.compile_protocol(documents.protocol)
    analysis = CompositionalOrganism.compile_analysis(documents.analysis)
    first_trace = run_protocol(model, protocol, seed)
    first_result = evaluate_trace(first_trace, analysis)
    second_trace = run_protocol(model, protocol, seed)
    second_result = evaluate_trace(second_trace, analysis)
    first_hash = CompositionalOrganism.trace_hash(first_trace)
    second_hash = CompositionalOrganism.trace_hash(second_trace)
    push!(rows, (
        bundle = name,
        seed = seed,
        rows = length(first_trace.rows),
        first_hash = first_hash,
        second_hash = second_hash,
        bitwise_reproducible = first_hash == second_hash,
        decisions_reproducible =
            first_result.decisions == second_result.decisions,
        initialization_reproducible =
            CO.initialization_hash(first_trace) ==
                CO.initialization_hash(second_trace),
        initialization_rows = length(first_trace.initialization_rows),
        model_provenance_complete = all(
            haskey(row.fields, "provenance.model_candidate")
            for row in first_trace.rows if row isa CO.EventTraceRow &&
                row.executed &&
                haskey(row.fields, "observation.source")),
        requested_fields_complete =
            isempty(CO.audit_requested_fields(first_trace, protocol)),
    ))
end

open(joinpath(OUTPUT, "public-dry-runs.tsv"), "w") do io
    println(io, join(fieldnames(typeof(first(rows))), '\t'))
    for row in rows
        println(io, join((getfield(row, field)
            for field in fieldnames(typeof(row))), '\t'))
    end
end

_, model, _, _ = let
    directory = joinpath(ROOT, "protocols", "public-dummies", first(DUMMIES))
    documents = load_documents(directory)
    genome = load_genome(joinpath(ROOT, "genome.toml"))
    (documents, compile_model(documents, genome),
        CompositionalOrganism.compile_protocol(documents.protocol),
        CompositionalOrganism.compile_analysis(documents.analysis))
end

model_gates = CompositionalOrganism.semantic_gate(model)
parameter_recovery = validation["parameter_recovery"]
architecture_gate = Dict{String,Bool}(
    String(key) => value for (key, value) in pairs(model_gates))
merge!(architecture_gate, Dict(
    "static_source_boundary" =>
        isempty(CompositionalOrganism.static_architecture_audit(ROOT)),
    "fast_test_suite" => fast_tests_pass,
    "joint_masked_gaussian_evidence_accounting" => fast_tests_pass &&
        occursin("joint, masked, and bounded-Gaussian evidence accounting",
            fast_test_output),
    "loopy_schedule_reorder_zero_slot_conformance" => fast_tests_pass &&
        occursin("loopy schedules, node ordering, and zero-slot idleness",
            fast_test_output),
    "counter_rng_namespace_lifetime_conformance" => fast_tests_pass &&
        occursin("counter RNG and high-precision transforms",
            fast_test_output),
    "closed_evaluator_policy_conformance" => fast_tests_pass &&
        occursin("analysis policies and evaluation provenance are executable",
            fast_test_output),
    "success_change_point_global_joint_conformance" => fast_tests_pass &&
        occursin("canonical success, change-point, global-field, and joint semantics",
            fast_test_output),
    "public_bitwise_reproducibility" =>
        all(row.bitwise_reproducible for row in rows),
    "public_decision_reproducibility" =>
        all(row.decisions_reproducible for row in rows),
    "initialization_ledger_reproducibility" =>
        all(row.initialization_reproducible for row in rows),
    "initialization_ledger_complete" =>
        all(row.initialization_rows > 0 for row in rows),
    "model_candidate_provenance_complete" =>
        all(row.model_provenance_complete for row in rows),
    "requested_trace_fields_complete" =>
        all(row.requested_fields_complete for row in rows),
    "all_fifteen_edge_micrographs" => validation["edge_count"] == 15,
    "exact_approximate_parity" =>
        validation["maximum_exact_parity_error"] <= 1e-10,
    "edge_deletion_mutants_detected" =>
        validation["minimum_edge_mutation_delta"] > 1e-6,
    "implementation_mutants_detected" =>
        validation["minimum_implementation_mutant_delta"] > 1e-6,
    "named_trace_mutants_detected" =>
        validation["minimum_named_trace_delta"] > 1e-6,
    "edge_direction_is_causal" =>
        validation["maximum_reverse_target_delta"] <= 1e-10,
    "unrelated_fields_invariant" =>
        validation["maximum_unrelated_mutation_delta"] <= 1e-10,
    "sbc_rank_calibration" => validation["sbc_chi_square"] <= 31.41,
    "seven_edge_subset_family_recovery_at_least_0_80" =>
        validation["model_recovery_accuracy"] >= 0.80,
    "partner_parameter_recovery" =>
        validation["parameter_recovery_accuracy"] >= 0.75,
    "cue_root_generated_history_recovery" =>
        parameter_recovery["cue_root_aligned_strength"] >
            parameter_recovery["cue_root_reversed_strength"],
    "joint_outcome_recovery" =>
        parameter_recovery["policy_outcome_recovery_delta"] > 0.0,
    "joint_access_recovery" =>
        parameter_recovery["access_recovery_delta"] > 0.0,
    "coprotection_lesion_recovery" =>
        parameter_recovery["coprotection_edge_forecast_delta"] > 0.0,
    "precision_forecast_recovery" =>
        parameter_recovery["precision_forecast_delta"] > 0.0,
))

summary = Dict{String,Any}(
    "contract_id" => CompositionalOrganism.CONTRACT_ID,
    "contract_version" => CompositionalOrganism.CONTRACT_VERSION,
    "public_bundles" => length(rows),
    "all_bitwise_reproducible" =>
        all(row.bitwise_reproducible for row in rows),
    "all_decisions_reproducible" =>
        all(row.decisions_reproducible for row in rows),
    "node_kinds_exercised" =>
        sort!(String.(unique(node.kind for node in values(model.nodes)))),
    "edge_kinds_implemented" =>
        sort!(String.(CompositionalOrganism.EDGE_KINDS)),
    "static_source_violations" =>
        CompositionalOrganism.static_architecture_audit(ROOT),
    "architecture_gate" => architecture_gate,
    "all_architecture_gates_pass" => all(values(architecture_gate)),
)
open(joinpath(OUTPUT, "summary.toml"), "w") do io
    TOML.print(io, summary; sorted = true)
end

open(joinpath(OUTPUT, "parameter-use.tsv"), "w") do io
    println(io, "field\tconsumer")
    for field in sort!(collect(keys(model.consumption)))
        println(io, field, '\t', model.consumption[field])
    end
end

all(values(architecture_gate)) ||
    error("semantic architecture gate failed; see summary.toml")

println("semantic gate outputs written to $OUTPUT")
