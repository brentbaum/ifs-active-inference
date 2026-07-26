#!/usr/bin/env julia

using TOML

module Validator
include(joinpath(@__DIR__, "validate_bundle.jl"))
end

module Canonical
include(joinpath(@__DIR__, "canonical_bundle.jl"))
end

const ROOT = normpath(joinpath(@__DIR__, "..", ".."))
const DUMMY = joinpath(ROOT, "protocols", "public-dummies", "51-P-00")

function documents()
    return (
        configuration = TOML.parsefile(joinpath(DUMMY, "configuration.toml")),
        world = TOML.parsefile(joinpath(DUMMY, "world.toml")),
        protocol = TOML.parsefile(joinpath(DUMMY, "protocol.toml")),
        analysis = TOML.parsefile(joinpath(DUMMY, "analysis.toml")),
    )
end

function expect_failure(operation, name)
    failed = false
    try
        operation()
    catch
        failed = true
    end
    failed || error("semantic rejection fixture unexpectedly passed: $name")
    println("rejected: $name")
end

function validate_through_protocol(docs)
    configuration = Validator.validate_configuration(docs.configuration)
    world = Validator.validate_world(docs.world, configuration)
    return Validator.validate_protocol(docs.protocol, configuration, world)
end

function deactivate_partner!(docs)
    partner = only(filter(node -> node["id"] == "partner-main",
        docs.configuration["nodes"]))
    partner["active"] = false
    for edge in docs.configuration["edges"]
        if edge["from"] == "partner-main" || edge["to"] == "partner-main"
            edge["state"] = "inactive"
        end
    end
    channel = only(filter(item -> item["id"] == "partner-signal",
        docs.configuration["observation_channels"]))
    filter!(node -> node != "partner-main", channel["scope"])
end

function main()
    Validator.validate_bundle(DUMMY)
    two_by_two_budget = Dict(
        "id" => "two-by-two",
        "arms" => ["treatment-one", "treatment-two",
            "control-one", "control-two"],
        "arm_pairs" => [
            Dict("left" => "treatment-one", "right" => "control-one"),
            Dict("left" => "treatment-two", "right" => "control-two"),
        ],
    )
    length(Validator.validate_budget_pairs(two_by_two_budget,
        Set(String.(two_by_two_budget["arms"])))) == 2 ||
        error("two-by-two budget pair validation failed")
    println("accepted: explicit two-by-two budget pairs")
    configuration = Validator.validate_configuration(
        documents().configuration)
    tie_label = join([
        "protector-one=approach",
        "protector-three=permit",
        "protector-two=withdraw",
    ], ";")
    Validator.reconcile_joint_action(tie_label, configuration) == "withdraw" ||
        error("joint-action safety-priority tie break failed")
    plurality_label = join([
        "protector-one=approach",
        "protector-three=withdraw",
        "protector-two=approach",
    ], ";")
    Validator.reconcile_joint_action(plurality_label, configuration) ==
        "approach" || error("joint-action plurality failed")
    println("accepted: joint-action reconciliation")
    enabled_except_approach = Set(String.(collect(configuration.action_union)))
    delete!(enabled_except_approach, "approach")
    length(Validator.require_joint_action_support(
        configuration, enabled_except_approach)) == 1 ||
        error("last-action support vector failed")
    expect_failure("disabling last available policy action") do
        Validator.require_joint_action_support(
            configuration, Set(String.(configuration.action_union)))
    end
    expect_failure("event unit over tick-only state field") do
        Validator.validate_unit_row_domains("event",
            Set(["state.access.access-main.probability"]), "bad-event-unit")
    end
    expect_failure("event-unit cross-arm contrast") do
        docs = documents()
        docs.analysis["unit_of_analysis"] = "event"
        configuration = Validator.validate_configuration(docs.configuration)
        world = Validator.validate_world(docs.world, configuration)
        protocol = Validator.validate_protocol(
            docs.protocol, configuration, world)
        Validator.validate_analysis(
            docs.analysis, protocol, configuration, world)
    end

    expect_failure("unknown action reconciler") do
        docs = documents()
        docs.configuration["action_reconciler_id"] = "unknown-resolver"
        Validator.validate_configuration(docs.configuration)
    end

    expect_failure("edge source/target signature") do
        docs = documents()
        docs.configuration["edges"][1]["from"] = "protector-one"
        Validator.validate_configuration(docs.configuration)
    end

    expect_failure("duplicate semantic edge") do
        docs = documents()
        duplicate = deepcopy(docs.configuration["edges"][1])
        duplicate["id"] = "duplicate-edge"
        push!(docs.configuration["edges"], duplicate)
        Validator.validate_configuration(docs.configuration)
    end

    expect_failure("active edge touches inactive node") do
        docs = documents()
        partner = only(filter(node -> node["id"] == "partner-main",
            docs.configuration["nodes"]))
        partner["active"] = false
        Validator.validate_configuration(docs.configuration)
    end

    expect_failure("coupled parent-table dimension") do
        docs = documents()
        pop!(docs.world["processes"][2]["conditional_transition_ids"])
        configuration = Validator.validate_configuration(docs.configuration)
        Validator.validate_world(docs.world, configuration)
    end

    expect_failure("masked scope outside emission source") do
        docs = documents()
        docs.world["emissions"][2]["masked_scope"] = ["partner-state"]
        configuration = Validator.validate_configuration(docs.configuration)
        Validator.validate_world(docs.world, configuration)
    end

    expect_failure("episode boundary divisibility") do
        docs = documents()
        docs.world["episode_length"] = 7
        configuration = Validator.validate_configuration(docs.configuration)
        Validator.validate_world(docs.world, configuration)
    end

    expect_failure("contingency targets non-action process") do
        docs = documents()
        push!(docs.world["contingencies"], Dict(
            "id" => "bad-contingency",
            "action" => "approach",
            "target_process" => "episode-process",
            "effect" => "activate_action_transition",
            "enabled" => true,
        ))
        configuration = Validator.validate_configuration(docs.configuration)
        Validator.validate_world(docs.world, configuration)
    end

    expect_failure("action outcome table dimension") do
        docs = documents()
        outcome = only(filter(item -> item["id"] == "approach-outcome",
            docs.world["outcomes"]))
        pop!(outcome["success_probabilities"])
        configuration = Validator.validate_configuration(docs.configuration)
        Validator.validate_world(docs.world, configuration)
    end

    expect_failure("inactive StructureNode with candidates") do
        docs = documents()
        structure = only(filter(node -> node["id"] == "structure-main",
            docs.configuration["nodes"]))
        structure["active"] = false
        Validator.validate_configuration(docs.configuration)
    end

    expect_failure("mixed bundle and protector policy actors") do
        docs = documents()
        push!(docs.configuration["policy_families"][1]["actor_nodes"],
            "bundle-main")
        Validator.validate_configuration(docs.configuration)
    end

    expect_failure("multiple bundle policy actors") do
        docs = documents()
        for node in docs.configuration["nodes"]
            if node["type"] == "ProtectorNode"
                node["active"] = false
            end
        end
        for edge in docs.configuration["edges"]
            source = only(filter(node -> node["id"] == edge["from"],
                docs.configuration["nodes"]))
            target = only(filter(node -> node["id"] == edge["to"],
                docs.configuration["nodes"]))
            if !source["active"] || !target["active"]
                edge["state"] = "inactive"
            end
        end
        docs.configuration["policy_families"][1]["actor_nodes"] = ["bundle-main"]
        push!(docs.configuration["nodes"], Dict(
            "id" => "bundle-other",
            "type" => "BundleNode",
            "cardinality" => 2,
            "slot" => 2,
            "active" => true,
        ))
        push!(docs.configuration["policy_families"], Dict(
            "id" => "other-policy",
            "family" => "observe",
            "actor_nodes" => ["bundle-other"],
            "actions" => ["observe"],
            "enabled" => true,
        ))
        Validator.validate_configuration(docs.configuration)
    end

    expect_failure("structure candidate cardinality") do
        docs = documents()
        structure = only(filter(node -> node["id"] == "structure-main",
            docs.configuration["nodes"]))
        structure["cardinality"] = 3
        Validator.validate_configuration(docs.configuration)
    end

    expect_failure("duplicate complete candidate pattern") do
        docs = documents()
        docs.configuration["structure_candidates"][2]["active_edges"] =
            copy(docs.configuration["structure_candidates"][1]["active_edges"])
        docs.configuration["structure_candidates"][2]["inactive_edges"] =
            copy(docs.configuration["structure_candidates"][1]["inactive_edges"])
        Validator.validate_configuration(docs.configuration)
    end

    expect_failure("world truth protocol trigger") do
        docs = documents()
        docs.protocol["arms"][1]["events"][1]["trigger"] = Dict(
            "kind" => "latent_intervention",
            "predicate" => Dict(
                "field" => "world.truth.partner-state",
                "comparator" => "eq",
                "value" => "helpful",
            ),
        )
        validate_through_protocol(docs)
    end

    expect_failure("channel source mismatch") do
        docs = documents()
        event = first(event for event in docs.protocol["arms"][1]["events"]
            if event["kind"] == "observe")
        event["source"] = "world"
        validate_through_protocol(docs)
    end

    expect_failure("event at exclusive horizon") do
        docs = documents()
        docs.protocol["arms"][1]["events"][end]["time"] = docs.world["horizon"]
        validate_through_protocol(docs)
    end

    expect_failure("predicate value type mismatch") do
        docs = documents()
        docs.protocol["arms"][1]["events"][1]["trigger"] = Dict(
            "kind" => "external_proxy",
            "predicate" => Dict(
                "field" => "run.time",
                "comparator" => "eq",
                "value" => "one",
            ),
        )
        validate_through_protocol(docs)
    end

    expect_failure("arbitrary joint action trace suffix") do
        docs = documents()
        push!(docs.protocol["requested_trace_fields"],
            "policy.joint.posterior.not-a-joint-action")
        validate_through_protocol(docs)
    end

    expect_failure("action trace without complete outcome mappings") do
        docs = documents()
        filter!(outcome -> outcome["action"] != "observe",
            docs.world["outcomes"])
        validate_through_protocol(docs)
    end

    expect_failure("hazard trace without outcome mapping") do
        docs = documents()
        push!(docs.protocol["requested_trace_fields"], "world.potential_hazard")
        validate_through_protocol(docs)
    end

    expect_failure("switch trace for non-change-point process") do
        docs = documents()
        push!(docs.protocol["requested_trace_fields"],
            "world.process.partner-state.switch")
        validate_through_protocol(docs)
    end

    expect_failure("protocol trigger reads inactive node") do
        docs = documents()
        deactivate_partner!(docs)
        docs.protocol["arms"][1]["events"][1]["trigger"] = Dict(
            "kind" => "latent_intervention",
            "predicate" => Dict(
                "field" => "state.partner.partner-main.trust_probability",
                "comparator" => "ge",
                "value" => 0.5,
            ),
        )
        validate_through_protocol(docs)
    end

    expect_failure("control names absent intervention") do
        docs = documents()
        filter!(event -> get(event, "intervention_id", "") != "sever-broadcast",
            docs.protocol["arms"][2]["events"])
        validate_through_protocol(docs)
    end

    expect_failure("reversed evidence-budget pair") do
        docs = documents()
        push!(docs.protocol["evidence_budget_rules"][1]["arm_pairs"],
            Dict("left" => "broadcast-off", "right" => "broadcast-on"))
        validate_through_protocol(docs)
    end

    expect_failure("typed paired-stream namespace") do
        docs = documents()
        docs.protocol["paired_streams"][1]["components"][1]["kind"] =
            "latent_factor"
        validate_through_protocol(docs)
    end

    expect_failure("analysis dependency not requested") do
        docs = documents()
        filter!(path -> path != "state.global_precision.global-main.depth",
            docs.protocol["requested_trace_fields"])
        configuration = Validator.validate_configuration(docs.configuration)
        world = Validator.validate_world(docs.world, configuration)
        protocol = Validator.validate_protocol(docs.protocol, configuration, world)
        Validator.validate_analysis(docs.analysis, protocol, configuration, world)
    end

    expect_failure("treatment contrast without control") do
        docs = documents()
        docs.analysis["estimands"][2]["control_ids"] = String[]
        configuration = Validator.validate_configuration(docs.configuration)
        world = Validator.validate_world(docs.world, configuration)
        protocol = Validator.validate_protocol(docs.protocol, configuration, world)
        Validator.validate_analysis(docs.analysis, protocol, configuration, world)
    end

    expect_failure("contrast control arms do not match") do
        docs = documents()
        docs.protocol["controls"][1]["treatment_arms"] = ["broadcast-off"]
        docs.protocol["controls"][1]["control_arms"] = ["broadcast-on"]
        configuration = Validator.validate_configuration(docs.configuration)
        world = Validator.validate_world(docs.world, configuration)
        protocol = Validator.validate_protocol(docs.protocol, configuration, world)
        Validator.validate_analysis(docs.analysis, protocol, configuration, world)
    end

    expect_failure("event precedes non-crossing operand") do
        docs = documents()
        docs.analysis["estimands"][3]["expression"]["left"] = Dict(
            "op" => "field",
            "path" => "state.access.access-main.probability",
        )
        configuration = Validator.validate_configuration(docs.configuration)
        world = Validator.validate_world(docs.world, configuration)
        protocol = Validator.validate_protocol(docs.protocol, configuration, world)
        Validator.validate_analysis(docs.analysis, protocol, configuration, world)
    end

    expect_failure("half tie handling for Boolean event ordering") do
        docs = documents()
        docs.analysis["tie_handling"] = "half"
        configuration = Validator.validate_configuration(docs.configuration)
        world = Validator.validate_world(docs.world, configuration)
        protocol = Validator.validate_protocol(docs.protocol, configuration, world)
        Validator.validate_analysis(docs.analysis, protocol, configuration, world)
    end

    expect_failure("exact binomial on numeric series") do
        docs = documents()
        docs.analysis["estimands"][3]["expression"] = Dict(
            "op" => "field",
            "path" => "state.access.access-main.probability",
        )
        configuration = Validator.validate_configuration(docs.configuration)
        world = Validator.validate_world(docs.world, configuration)
        protocol = Validator.validate_protocol(docs.protocol, configuration, world)
        Validator.validate_analysis(docs.analysis, protocol, configuration, world)
    end

    expect_failure("argmax paths use wrong structural fields") do
        docs = documents()
        push!(docs.protocol["requested_trace_fields"],
            "state.structure.structure-main.selected.*")
        docs.analysis["estimands"][3]["expression"] = Dict(
            "op" => "argmax_match",
            "evidence_path" =>
                "state.structure.structure-main.log_evidence.*",
            "selected_path" =>
                "state.structure.structure-main.log_evidence.*",
        )
        docs.analysis["estimands"][3]["interval"] = Dict("method" => "none")
        docs.analysis["estimands"][3]["aggregation"] = "rate"
        configuration = Validator.validate_configuration(docs.configuration)
        world = Validator.validate_world(docs.world, configuration)
        protocol = Validator.validate_protocol(docs.protocol, configuration, world)
        Validator.validate_analysis(docs.analysis, protocol, configuration, world)
    end

    expect_failure("derived analysis source") do
        docs = documents()
        docs.analysis["estimands"][2]["expression"]["value"]["arg"]["path"] =
            "derived.slope"
        configuration = Validator.validate_configuration(docs.configuration)
        world = Validator.validate_world(docs.world, configuration)
        protocol = Validator.validate_protocol(docs.protocol, configuration, world)
        Validator.validate_analysis(docs.analysis, protocol, configuration, world)
    end

    expect_failure("inactive node used by non-audit estimand") do
        docs = documents()
        deactivate_partner!(docs)
        inactive_path = "state.partner.partner-main.trust_probability"
        push!(docs.protocol["requested_trace_fields"], inactive_path)
        estimand = docs.analysis["estimands"][3]
        estimand["status"] = "descriptive"
        estimand["expression"] = Dict("op" => "field", "path" => inactive_path)
        estimand["aggregation"] = "mean"
        estimand["interval"] = Dict("method" => "none")
        configuration = Validator.validate_configuration(docs.configuration)
        world = Validator.validate_world(docs.world, configuration)
        protocol = Validator.validate_protocol(docs.protocol, configuration, world)
        Validator.validate_analysis(docs.analysis, protocol, configuration, world)
    end

    expect_failure("interpretation heading structure") do
        docs = documents()
        configuration = Validator.validate_configuration(docs.configuration)
        world = Validator.validate_world(docs.world, configuration)
        protocol = Validator.validate_protocol(docs.protocol, configuration, world)
        analysis = Validator.validate_analysis(
            docs.analysis, protocol, configuration, world)
        mktempdir() do directory
            path = joinpath(directory, "interpretation-lock.md")
            write(path, replace(read(joinpath(DUMMY, "interpretation-lock.md"),
                String), "## Success" => "## Outcome"))
            Validator.validate_interpretation(path, "51-P-00", analysis)
        end
    end

    expect_failure("invalid UTF-8 archive input") do
        mktempdir() do directory
            bundle = joinpath(directory, "51-P-00")
            cp(DUMMY, bundle; force = true)
            open(joinpath(bundle, "configuration.toml"), "w") do io
                write(io, UInt8[0xff, 0x0a])
            end
            Canonical.validate_bundle_directory(bundle)
        end
    end

    println("semantic conformance passed: 40 rejection fixtures")
    return true
end

main()
