using Pkg
using Dates
using Printf
using SHA
using Serialization

const PROJECT_DIR = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(PROJECT_DIR)

include(joinpath(PROJECT_DIR, "src", "GlobalPrecisionField.jl"))
include(joinpath(PROJECT_DIR, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(PROJECT_DIR, "src", "IFSBundleInquiry.jl"))
include(joinpath(PROJECT_DIR, "src", "ProtectorTrust.jl"))
include(joinpath(PROJECT_DIR, "src", "ExilingEmergence.jl"))
include(joinpath(PROJECT_DIR, "src", "DyadGateDescent.jl"))

using .GlobalPrecisionField
using .DyadGateDescent

const OUTPUT_DIR =
    joinpath(PROJECT_DIR, "results", "dyad_gate_descent")
const FREEZE_LOG = joinpath(OUTPUT_DIR, "freeze-log.md")
const CONFIRMATION_MARKER =
    joinpath(OUTPUT_DIR, "confirmation-complete.txt")
const PILOT_MARKER = joinpath(OUTPUT_DIR, "pilot-complete.txt")
const PILOT_CACHE = joinpath(OUTPUT_DIR, "pilot-rows.bin")
const FREEZE_MANIFEST = joinpath(OUTPUT_DIR, "freeze-manifest.json")
const FROZEN_PILOT_CSV =
    joinpath(OUTPUT_DIR, "frozen-pilot-per_seed.csv")
const FROZEN_PILOT_SUMMARY =
    joinpath(OUTPUT_DIR, "frozen-pilot-summary.json")
const SOURCE_FILE =
    joinpath(PROJECT_DIR, "src", "DyadGateDescent.jl")
const RUNNER_FILE = @__FILE__
const PROTECTOR_SOURCE =
    joinpath(PROJECT_DIR, "src", "ProtectorTrust.jl")
const EXILING_SOURCE =
    joinpath(PROJECT_DIR, "src", "ExilingEmergence.jl")
const SIM5_SOURCE = normpath(joinpath(PROJECT_DIR, "..", "suite",
    "src", "sims", "sim5", "Sim5.jl"))

number(value) = @sprintf("%.6f", value)
verdict(value) = value ? "PASS" : "FAIL"

function config_record(config)
    return (; (name => begin
        value = getfield(config, name)
        if name == :protector
            (; (field => getfield(value, field)
                for field in fieldnames(typeof(value)))...)
        elseif name == :vulnerable
            (; (field => getfield(value, field)
                for field in fieldnames(typeof(value)))...)
        else
            value
        end
    end for name in fieldnames(DyadGateConfig))...)
end

function render_value(value)
    if value isa AbstractVector
        return string(value)
    elseif value isa ProtectorTrust.ProtectorTrustConfig
        return "Experiment 47 frozen config"
    elseif value isa ExilingEmergence.ExilingConfig
        return "Experiment 48 frozen config"
    end
    return string(value)
end

file_sha256(path) = bytes2hex(SHA.sha256(read(path)))

function extract_json_string(path, key)
    raw = read(path, String)
    matched = match(Regex("\"$(key)\"\\s*:\\s*\"([0-9a-f]+)\""), raw)
    isnothing(matched) && error("missing $key in freeze manifest")
    return matched.captures[1]
end

function write_freeze_manifest()
    GlobalPrecisionField.write_json(FREEZE_MANIFEST, (
        source_sha256 = file_sha256(SOURCE_FILE),
        runner_sha256 = file_sha256(RUNNER_FILE),
        protector_source_sha256 = file_sha256(PROTECTOR_SOURCE),
        exiling_source_sha256 = file_sha256(EXILING_SOURCE),
        sim5_source_sha256 = file_sha256(SIM5_SOURCE),
        pilot_csv_sha256 =
            file_sha256(FROZEN_PILOT_CSV),
        pilot_summary_sha256 =
            file_sha256(FROZEN_PILOT_SUMMARY),
        pilot_cache_sha256 = file_sha256(PILOT_CACHE),
        frozen_at = string(now()),
    ))
end

function verify_freeze_manifest()
    isfile(FREEZE_MANIFEST) ||
        error("confirmation blocked: freeze manifest missing")
    checks = (
        source_sha256 = SOURCE_FILE,
        runner_sha256 = RUNNER_FILE,
        protector_source_sha256 = PROTECTOR_SOURCE,
        exiling_source_sha256 = EXILING_SOURCE,
        sim5_source_sha256 = SIM5_SOURCE,
        pilot_csv_sha256 = FROZEN_PILOT_CSV,
        pilot_summary_sha256 = FROZEN_PILOT_SUMMARY,
        pilot_cache_sha256 = PILOT_CACHE,
    )
    for (key, path) in pairs(checks)
        expected = extract_json_string(FREEZE_MANIFEST, String(key))
        actual = file_sha256(path)
        actual == expected ||
            error("freeze mismatch for $key: confirmation blocked")
    end
    return true
end

function write_magic_numbers(config)
    open(joinpath(OUTPUT_DIR, "magic-numbers.md"), "w") do io
        println(io, "# Experiment 49 magic numbers")
        println(io)
        println(io, "Every Experiment 49 semantic, calibration, and implementation constant is listed below. Dyad constants reproduce the load-bearing committed Sim 5 mapping→depth→effective-precision path. The nested Experiment 47 and 48 configs are reused unchanged and remain enumerated in their own committed magic-number records.")
        println(io)
        println(io, "| Constant | Value | Rationale |")
        println(io, "|---|---:|---|")
        for (name, value, rationale) in magic_numbers(config)
            println(io, "| `", name, "` | `", render_value(value),
                "` | ", rationale, " |")
        end
        println(io)
        println(io, "The final fidelity-corrected calibration above was declared before `34901:34910` was opened. It was not strengthened in response to pilot or confirmatory outcomes. Two architecturally invalid attempts are retained under `invalidated-attempt-1/` and `invalidated-attempt-2/`; neither is evidence for Experiment 49.")
    end
end

function write_freeze_log(config, pilot_summary)
    open(FREEZE_LOG, "w") do io
        println(io, "# Experiment 49 freeze log")
        println(io)
        println(io, "- Frozen: $(Dates.format(now(), "yyyy-mm-dd HH:MM:SS")).")
        println(io, "- Final fidelity-corrected pilot opened once: `34901:34910` (10 worlds per arm).")
        println(io, "- Final fidelity-corrected confirmation remained unopened: `34951:34970` (20 fresh, disjoint worlds per arm).")
        println(io, "- This final protocol's first and only pilot used the calibration recorded in `magic-numbers.md`; no alternative profile was run.")
        println(io, "- **Permission rises** at the first episode where the protector's competence-conditioned obsolete-future risk-model permission reaches `$(config.permission_threshold)`, provided it began below that threshold.")
        println(io, "- **Root revision begins** at the first permitted witnessing update where the vulnerable-bundle identity-root posterior reaches `$(config.root_revision_begun_probability)`.")
        println(io, "- Within an episode the event order is fixed: dyad signal and own-state outcome → learned mapping/depth/field update → optional field-weighted `TrustEvidence` route updates → protector permission decision → attempted-contact registration → permitted witnessing → bundle likelihood update.")
        println(io, "- §8.5 thresholds retained unchanged: coupled contact ≥ `$(config.contact_required)/20`; no-dyad and decoupled contact ≤ `$(config.control_contact_ceiling)/20`; permission precedes revision in every inferential descent.")
        println(io, "- Pilot contact counts: coupled `$(pilot_summary.arms["coupled"].contact_worlds)/10`, no-dyad `$(pilot_summary.arms["no_dyad"].contact_worlds)/10`, decoupled `$(pilot_summary.arms["decoupled"].contact_worlds)/10`; authored calibration `$(pilot_summary.arms["authored_access"].contact_worlds)/10`.")
        println(io, "- Threshold, parameter, architecture, measure, and vocabulary changes after pilot: **none**.")
        println(io, "- Confirmation access guard: the runner requires the pilot marker, cache, freeze log, and hash manifest; verifies Experiment 49, Experiment 47, Experiment 48, and Sim 5 source hashes plus the runner, immutable pilot CSV, immutable pilot summary, and cached-row hashes; and refuses a rerun after the confirmation marker exists.")
        println(io, "- Frozen register: *configural* means within-bundle statistical organization; *relational* is interpersonal only; vulnerable-bundle contact is *witnessing* and protector contact is *befriending*. *Organization* means the bundle, couplings, precisions, and field profile; *carrier* means independently parameterized substrate. The dyad scaffold is a learned precision state, not a renamed carrier.")
    end
end

function timing_text(summary)
    timing = summary.timing
    timing.descent_worlds == 0 &&
        return "no descent worlds (timing distribution empty)"
    return "permission rise min/median/max `$(timing.permission_rise_minimum)`/`$(timing.permission_rise_median)`/`$(timing.permission_rise_maximum)`; revision begin `$(timing.revision_begin_minimum)`/`$(timing.revision_begin_median)`/`$(timing.revision_begin_maximum)`; lag `$(timing.lag_minimum)`/`$(timing.lag_median)`/`$(timing.lag_maximum)` episodes"
end

function report_arm(io, label, summary)
    println(io, "- **$(label):** contact `$(summary.contact_worlds)/$(summary.worlds)`; descent `$(summary.descent_worlds)/$(summary.worlds)`; ordered descent `$(summary.ordered_descent_worlds)/$(summary.worlds)`; mean initial/final permission `$(number(summary.mean_initial_permission))` / `$(number(summary.mean_final_permission))`; mean final root `$(number(summary.mean_final_root_probability))`; mean dyad field `$(number(summary.mean_final_dyad_field_weight))`; mean registered rejections `$(number(summary.mean_registered_rejections))`; $(timing_text(summary)).")
end

function write_report(config, pilot_summary;
        confirmation_summary = nothing)
    confirmed = !isnothing(confirmation_summary)
    check = self_check(config)
    open(joinpath(OUTPUT_DIR, "report.md"), "w") do io
        println(io, "# Experiment 49: dyad-gate coupling and derived descent")
        println(io)
        println(io, "## Design")
        println(io)
        println(io, "The construction stacks the unmodified Experiment 47 protector over the unmodified Experiment 48 `VulnerableBundle`. A small adapter stores an identity-root log odds beside that bundle because Experiment 48 exposes a relational prior and registration channel but no root posterior. The adapter uses the bundle's committed 2×16 conditional table: each permitted witnessing observation contributes `$(config.witnessing_precision) × log p(bundle|g=+1)/p(bundle|g=-1)`. Root revision therefore proceeds by Bayesian inference; no repeated-contact assignment or arm-specific root update appears.")
        println(io)
        println(io, "The committed Sim 5 dyad module exports only its full runner, so a thin adapter reproduces its load-bearing internal path without modifying it: the same regulated Xoshiro emission generates a joint therapist signal (surface coherence × relational safety); Dirichlet counts learn its mapping to the client's observed settling; current capture generates arousal and the same five-state volatility observation; the exact capacity-mixed volatility × learned-co-regulation likelihood updates categorical depth; and that posterior yields the same effective part/context precisions and normalized relational-field weight. Coupled and decoupled arms receive identical dyad signals and settling outcomes. The field weight controls the rate at which three independently generated protector observations enter `TrustEvidence`; the dyad outcome itself never supplies a trust-evidence sign.")
        println(io)
        println(io, "Permission is the protector's risk-model decision under the obsolete future. Its baseline risk reads tolerated outcome, shared competence, and partner policy; inferred shared competence then determines how much of that full risk can be carried without the protector. All three Experiment 47 routes therefore change permission (single-route positive-evidence effects at the structural audit were `$(join(number.(check.protector_route_permission_effects), ", "))`). Contact is permitted exactly when permission reaches `$(config.permission_threshold)`. The gate is not stored separately.")
        println(io)
        println(io, "Every denied attempt is passed to Experiment 48's committed `register_contact!` with suppression and registration active, strengthening the vulnerable bundle's *alone with this* prior. When permission is granted, suppression ends and a witnessing configuration reaches the identity-root likelihood adapter. Thus the relational prior/registration channel and the four-channel bundle are both live.")
        println(io)
        println(io, "### Wiring note: no access by fiat")
        println(io)
        println(io, "`run_gate_arm` has no access-rule argument. It learns the Sim 5 field, calls `ingest_evidence!` only through the coupled field edge, computes the protector's risk-model permission, and defines contact as that probability crossing the frozen threshold. Only then does `update_root_from_witnessing!` read one matched bundle observation. The coupled, no-dyad, and decoupled paths contain no branch that grants access from an arm label. The historical authored-access comparator is isolated in `run_authored_calibration`; it bypasses the gate by definition, is reported as a calibration benchmark, and is excluded from every inferential success criterion.")
        println(io)
        println(io, "### Register guards")
        println(io)
        println(io, "*Configural* refers only to organization within the four-element bundle. *Relational* refers to the interpersonal partner route. Permitted contact with the vulnerable bundle is *witnessing*; protector engagement is *befriending*. *Organization* means the bundle, couplings, precisions, and field profile. *Carrier* means independently parameterized substrate; the learned dyad precision is not renamed a carrier.")
        println(io)
        println(io, "### Design decisions")
        println(io)
        println(io, "- The spec requires an authored-access baseline while also saying no arm may require authored access. These conflict literally. The comparator is therefore an isolated calibration benchmark, not one of the three inferential gate arms and not evidence for any criterion. Criterion 3 is evaluated over coupled, no-dyad, and decoupled worlds.")
        println(io, "- Sim 5's useful mapping, depth, and precision functions are internal and its module exports only `run_sim5_config`. The adapter duplicates only that committed path and constants; this is the genuine interface block allowed by the brief.")
        println(io, "- Experiment 48 has no identity-root state or witnessing update. A second thin adapter is necessary for §8.3 and uses its committed conditional table rather than modifying `ExilingEmergence.jl` or inventing an endpoint assignment. Its relational prior and registration channel remain active for denied attempts.")
        println(io, "- The risk-model obsolete future was chosen because Experiment 47's post-freeze audit showed that co-protection posterior risk, unlike policy addition, supports the intended differential. The adapter retains the full baseline risk inside the competence-conditioned mixture so no route is causally idle.")
        println(io, "- One seed is one matched world. Protector jitter, dyad signals/outcomes, independent protector observations, and the complete witnessing stream are shared across arms. The coupled/decoupled contrast changes only whether field-weighted packets reach `TrustEvidence`.")
        println(io, "- One normalized relational-field unit emits one packet on each protector route. Route signs come from an independent matched stream, not from the dyad outcome used to learn the field.")
        println(io, "- `$(config.permission_threshold)` operationalizes permission rising; `$(config.root_revision_begun_probability)` operationalizes revision beginning. Both were declared before the corrected pilot. The ordering predicate requires a strictly earlier episode (`permission < revision`), not a tie.")
        println(io, "- Contact is measured separately from descent. A world may contact the bundle yet fail to accumulate enough likelihood evidence for root revision; such a failure is retained.")
        println(io, "- Two implementation attempts are retained and excluded. Attempt 1 mislabeled a safe-rate posterior as precision. Attempt 2 fixed that architecture but omitted Sim 5's volatility likelihood and realized capacity mix. Both were rejected before completion was claimed. This final equation-faithful protocol uses entirely fresh seeds and contains no rescue sweep.")
        println(io)
        println(io, "### Structural audit")
        println(io)
        println(io, "Seed blocks disjoint = `$(check.seed_blocks_disjoint)`; Sim 5 mapping/field adapter active = `$(check.sim5_mapping_adapter_active)`; Experiment 48 bundle reused = `$(check.vulnerable_bundle_reused)`; Experiment 48 registration active = `$(check.experiment48_registration_active)`; Experiment 47 `TrustEvidence` reused = `$(check.protector_evidence_extension_reused)`; all protector evidence routes causally change permission = `$(check.all_protector_routes_active)`; gate equals permission threshold = `$(check.gate_is_permission_threshold)`; coupled/decoupled dyad marginals matched = `$(check.coupled_decoupled_dyad_marginals_matched)`; decoupled ingests no evidence = `$(check.decoupled_ingests_no_evidence)`; no-dyad emits no scaffold packets = `$(check.no_dyad_has_no_scaffold_packets)`; closed gate has no root update = `$(check.closed_gate_has_no_root_update)`; authored comparator isolated = `$(check.authored_baseline_isolated)`.")
        println(io)
        println(io, "## Pilot")
        println(io)
        println(io, "Ten final fidelity-corrected worlds per arm (`34901:34910`) ran once before freeze.")
        println(io)
        report_arm(io, "Coupled", pilot_summary.arms["coupled"])
        report_arm(io, "No dyad", pilot_summary.arms["no_dyad"])
        report_arm(io, "Decoupled", pilot_summary.arms["decoupled"])
        report_arm(io, "Authored-access calibration", pilot_summary.arms["authored_access"])
        println(io)
        println(io, "Pilot provisional verdicts: contact separation `$(verdict(pilot_summary.criteria.contact_separation))`; permission-before-revision `$(verdict(pilot_summary.criteria.permission_before_revision))`; no authored access in inferential arms `$(verdict(pilot_summary.criteria.no_authored_access_in_inferential_arms))`.")
        println(io)
        println(io, "## Freeze log")
        println(io)
        if isfile(FREEZE_LOG)
            println(io, "The design, moderate calibration, thresholds, event ordering, measures, seed blocks, and register guards were frozen before confirmation. No value changed after the pilot. Full details are in `freeze-log.md`.")
        else
            println(io, "Not frozen. Confirmation is blocked.")
        end
        println(io)
        println(io, "## Confirmatory results")
        println(io)
        if !confirmed
            println(io, "The confirmatory block has not been opened.")
        else
            summary = confirmation_summary
            println(io, "Twenty fresh, disjoint final worlds per arm (`34951:34970`) ran after freeze.")
            println(io)
            report_arm(io, "Coupled", summary.arms["coupled"])
            report_arm(io, "No dyad", summary.arms["no_dyad"])
            report_arm(io, "Decoupled", summary.arms["decoupled"])
            report_arm(io, "Authored-access calibration", summary.arms["authored_access"])
            println(io)
            println(io, "### Verdict against §8.5")
            println(io)
            println(io, "1. `$(verdict(summary.criteria.contact_separation))` — coupled contact ≥ `$(config.contact_required)/20`; no-dyad and decoupled contact ≤ `$(config.control_contact_ceiling)/20`.")
            println(io, "2. `$(verdict(summary.criteria.permission_before_revision))` — protector permission rose before the first root-posterior crossing in every inferential world where descent occurred.")
            println(io, "3. `$(verdict(summary.criteria.no_authored_access_in_inferential_arms))` — no coupled, no-dyad, or decoupled world used authored access; the intentionally authored historical comparator remained isolated.")
            println(io)
            println(io, "Overall frozen-criterion verdict: **$(summary.all_criteria_pass ? "all three construction criteria passed" : "one or more construction criteria failed")**.")
        end
        println(io)
        println(io, "## Interpretation")
        println(io)
        if !confirmed
            println(io, "Pilot results are calibration only and license no confirmatory claim.")
        elseif confirmation_summary.all_criteria_pass
            println(io, "The construction reproduces the specified coupling result: the Sim 5-form learned mapping changes the categorical depth posterior and relational precision field; coupling that field into three independent protector evidence routes changes the protector's forecast enough to earn permission, while severing the same learned field does not. Denied attempts strengthen Experiment 48's relational prior through registration; once permission is present, witnessing observations revise the vulnerable-bundle identity root by likelihood accumulation. The measured event order supports the secondary prediction inside this construction.")
            println(io)
            println(io, "This is a computational sufficiency result, not a clinical mechanism or effectiveness claim. The construction can be read as a candidate account of how dyadic precision scaffolding could alter a protector's risk forecast. The evidence likelihoods, future semantics, permission threshold, dyad generator, and bundle graph remain authored.")
        else
            println(io, "Coupled descent failed at least one frozen criterion. The obstruction is therefore deeper than the implemented coupling hypothesis: moderate learned scaffolding, passed through all Experiment 47 evidence routes and evaluated by its supported risk-model form, was insufficient to produce the required outside-in descent. This deadlock is retained without rescue tuning and sharpens the account of what remains missing.")
        end
        println(io)
        println(io, "## What failure means")
        println(io)
        println(io, "If descent deadlocks even when coupled, the obstruction is deeper than the coupling hypothesis, and §10's Limits gains a sharper statement of what is missing. That is a better outcome than an authored success. No coupled-arm deadlock was rescued by strengthening scaffolding after results were observed.")
    end
end

function summary_payload(config, pilot_summary;
        confirmation_summary = nothing)
    return (
        experiment = 49,
        name = "dyad_gate_descent",
        contract = "experiments-44-49-sufficiency-round-spec.md §8",
        pilot = pilot_summary,
        confirmation = confirmation_summary,
        config = config_record(config),
        structural_audit = self_check(config),
    )
end

function write_status(state; all_criteria_pass = nothing)
    required = ["per_seed.csv", "summary.json", "status.json",
        "magic-numbers.md", "freeze-log.md", "report.md"]
    GlobalPrecisionField.write_json(joinpath(OUTPUT_DIR, "status.json"), (
        experiment = 49,
        state = state,
        confirmation_complete = isfile(CONFIRMATION_MARKER),
        all_criteria_pass = all_criteria_pass,
        required_deliverables = required,
        present_deliverables = [file for file in required
            if isfile(joinpath(OUTPUT_DIR, file))],
        generated_at = string(now()),
    ))
end

function write_outputs(config, pilot_rows, pilot_summary;
        confirmation_rows = nothing, confirmation_summary = nothing)
    all_rows = isnothing(confirmation_rows) ?
        pilot_rows : vcat(pilot_rows, confirmation_rows)
    GlobalPrecisionField.write_csv(joinpath(OUTPUT_DIR, "per_seed.csv"),
        all_rows)
    write_magic_numbers(config)
    GlobalPrecisionField.write_json(joinpath(OUTPUT_DIR, "summary.json"),
        summary_payload(config, pilot_summary;
            confirmation_summary = confirmation_summary))
    write_report(config, pilot_summary;
        confirmation_summary = confirmation_summary)
end

function run_pilot(config)
    (isfile(PILOT_MARKER) || isfile(FREEZE_MANIFEST) ||
        isfile(CONFIRMATION_MARKER)) &&
        error("pilot already opened; refusing to rerun")
    mkpath(OUTPUT_DIR)
    pilot_rows = run_block(config.pilot_seeds;
        stage = :pilot, config = config)
    pilot_summary = summarize_block(pilot_rows, config)
    write_outputs(config, pilot_rows, pilot_summary)
    open(PILOT_CACHE, "w") do io
        serialize(io, pilot_rows)
    end
    open(PILOT_MARKER, "w") do io
        println(io, "Corrected Experiment 49 pilot completed at $(now())")
        println(io, "Seeds: 34901:34910")
    end
    write_status("pilot_complete_awaiting_freeze")
    return pilot_rows, pilot_summary
end

function freeze_pilot(config)
    isfile(PILOT_MARKER) ||
        error("freeze blocked: pilot marker missing")
    isfile(PILOT_CACHE) ||
        error("freeze blocked: pilot cache missing")
    (isfile(FREEZE_MANIFEST) || isfile(CONFIRMATION_MARKER)) &&
        error("freeze already recorded; refusing to rewrite")
    pilot_rows = open(deserialize, PILOT_CACHE)
    pilot_summary = summarize_block(pilot_rows, config)
    write_freeze_log(config, pilot_summary)
    write_outputs(config, pilot_rows, pilot_summary)
    cp(joinpath(OUTPUT_DIR, "per_seed.csv"),
        FROZEN_PILOT_CSV; force = false)
    cp(joinpath(OUTPUT_DIR, "summary.json"),
        FROZEN_PILOT_SUMMARY; force = false)
    write_freeze_manifest()
    write_status("frozen_confirmation_unopened")
    return pilot_rows, pilot_summary
end

function run_confirmation(config)
    isfile(CONFIRMATION_MARKER) &&
        error("confirmation already complete; refusing to rerun")
    isfile(PILOT_MARKER) ||
        error("confirmation blocked: pilot marker missing")
    isfile(FREEZE_LOG) ||
        error("confirmation blocked: freeze log missing")
    verify_freeze_manifest()
    pilot_rows = open(deserialize, PILOT_CACHE)
    pilot_summary = summarize_block(pilot_rows, config)
    confirmation_rows = run_block(config.confirmation_seeds;
        stage = :confirm, config = config)
    confirmation_summary = summarize_block(confirmation_rows, config)
    write_outputs(config, pilot_rows, pilot_summary;
        confirmation_rows = confirmation_rows,
        confirmation_summary = confirmation_summary)
    open(CONFIRMATION_MARKER, "w") do io
        println(io, "Experiment 49 confirmation completed at $(now())")
        println(io, "Seeds: 34951:34970")
    end
    write_status("confirmation_complete";
        all_criteria_pass = confirmation_summary.all_criteria_pass)
    return confirmation_rows, confirmation_summary
end

function main(args)
    config = DyadGateConfig()
    if args == ["--pilot"]
        _, summary = run_pilot(config)
        println("Pilot complete: ", summary.criteria)
    elseif args == ["--freeze"]
        _, summary = freeze_pilot(config)
        println("Frozen: ", summary.criteria)
    elseif args == ["--confirm"]
        _, summary = run_confirmation(config)
        println("Confirmation complete: ", summary.criteria)
    elseif args == ["--self-check"]
        println(self_check(config))
    else
        error("usage: julia ... run_dyad_gate_descent.jl --pilot|--freeze|--confirm|--self-check")
    end
end

main(ARGS)
