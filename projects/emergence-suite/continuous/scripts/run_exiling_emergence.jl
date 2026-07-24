using Pkg
using Dates
using Printf

const PROJECT_DIR = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(PROJECT_DIR)

include(joinpath(PROJECT_DIR, "src", "GlobalPrecisionField.jl"))
include(joinpath(PROJECT_DIR, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(PROJECT_DIR, "src", "IFSBundleInquiry.jl"))
include(joinpath(PROJECT_DIR, "src", "ExilingEmergence.jl"))

using .GlobalPrecisionField
using .ExilingEmergence

const OUTPUT_DIR = joinpath(PROJECT_DIR, "results", "exiling_emergence")
const FREEZE_LOG = joinpath(OUTPUT_DIR, "freeze-log.md")
const CONFIRMATION_MARKER =
    joinpath(OUTPUT_DIR, "confirmation-complete.txt")

number(value) = @sprintf("%.6f", value)
verdict(value) = value ? "PASS" : "FAIL"

function config_record(config)
    return (; (name => getfield(config, name)
        for name in fieldnames(ExilingConfig))...)
end

function write_magic_numbers(config)
    open(joinpath(OUTPUT_DIR, "magic-numbers.md"), "w") do io
        println(io, "# Experiment 48 magic numbers")
        println(io)
        println(io, "Every authored semantic and implementation constant used by `ExilingEmergence` is listed. Numeric identities, collection indices, and machine arithmetic are not fitted constants.")
        println(io)
        println(io, "| Constant | Value | Rationale |")
        println(io, "|---|---:|---|")
        for (name, value, rationale) in magic_numbers(config)
            rendered = value isa AbstractVector ?
                "$(first(value)):$(last(value))" : string(value)
            println(io, "| `", name, "` | `", rendered, "` | ",
                rationale, " |")
        end
        println(io)
        println(io, "The static tolerance was inspected on the pilot and frozen at `$(config.static_epsilon)` before confirmation. No confirmatory result was available when it was frozen.")
    end
end

function write_freeze_log(config, pilot_summary)
    open(FREEZE_LOG, "w") do io
        println(io, "# Experiment 48 freeze log")
        println(io)
        println(io, "- Frozen: $(Dates.format(now(), "yyyy-mm-dd HH:MM:SS")).")
        println(io, "- Pilot opened: `14801:14810` (10 worlds).")
        println(io, "- Confirmation remained unopened: `14851:14870` (20 fresh, disjoint worlds).")
        println(io, "- Measures, criteria, policy names, and register names were frozen before confirmation.")
        println(io, "- Operational definition of **static**: maximum absolute per-episode change in the aloneness prior `maxₜ|Δpriorₜ| ≤ $(config.static_epsilon)` over the $(config.episodes)-episode exclusion run. The maximum pilot off-channel episode change was `$(pilot_summary.consequences.maximum_off_episode_delta)`.")
        println(io, "- **Strengthening** remained a directional test: `Δprior > $(config.static_epsilon)`. The smallest pilot on-channel change was `$(number(pilot_summary.consequences.minimum_on_delta))`.")
        println(io, "- Provisional §7.4 count thresholds were retained unchanged: exclusion in at least `$(config.exclusion_favorable_threshold)/20` exclusion-favorable worlds and at most `$(config.competitor_exclusion_ceiling)/20` worlds when a competitor is favorable.")
        println(io, "- Threshold and design changes after pilot: **none**. No world parameters were tuned from pilot outcomes.")
        println(io, "- Confirmation access guard: the runner refuses `--confirm` unless this log exists and refuses a rerun after the confirmation marker exists.")
        println(io, "- Frozen register: *configural* means statistical organization within the four-element bundle; *relational* is interpersonal only; *witnessing* is reserved for context-held exile activation; protector contact would be *befriending*. *Organization* means the bundle, couplings, precisions, and field profile; *carrier* means independently parameterized substrate. This experiment introduces no carrier.")
    end
end

function report_selection(io, summary)
    selection = summary.selection
    wins = selection.favorable_policy_wins
    println(io, "- Exclusion won `$(selection.exclusion_favorable_wins)/$(summary.worlds)` exclusion-favorable worlds.")
    println(io, "- Exclusion appeared in `$(selection.exclusion_in_competitor_favorable_worlds)/$(summary.worlds)` worlds when any competitor was favorable.")
    println(io, "- Favorable-regime wins: exclusion `$(wins["exclusion"])/$(summary.worlds)`, hypervigilance `$(wins["hypervigilance"])/$(summary.worlds)`, internal attack `$(wins["internal_attack"])/$(summary.worlds)`, oscillation `$(wins["oscillation"])/$(summary.worlds)`.")
end

function report_consequences(io, summary)
    consequences = summary.consequences
    println(io, "- Registration off was static in `$(consequences.starvation_static_worlds)/$(summary.worlds)` worlds; maximum per-episode `|Δprior| = $(consequences.maximum_off_episode_delta)`.")
    println(io, "- Registration on strengthened the prior in `$(consequences.confirmation_strengthening_worlds)/$(summary.worlds)` worlds; minimum `Δprior = $(number(consequences.minimum_on_delta))`.")
    println(io, "- Registration ablation restored a static prior in `$(consequences.ablation_static_worlds)/$(summary.worlds)` worlds.")
    println(io, "- Selected policy and contact stream were matched across toggles in `$(consequences.toggle_only_matched_worlds)/$(summary.worlds)` worlds; mean attempts per world were `$(number(consequences.mean_contact_attempts))`.")
end

function write_report(config, pilot_summary;
        confirmation_summary = nothing)
    confirmed = !isnothing(confirmation_summary)
    open(joinpath(OUTPUT_DIR, "report.md"), "w") do io
        println(io, "# Experiment 48: exiling emergence")
        println(io)
        println(io, "## Design")
        println(io)
        println(io, "The vulnerable part reuses the Experiment 43 four-channel bundle (`self`, `world`, `policy`, `outcome`) and joint conditional table. It adds one mutable relational prior: the probability of *alone with this*. Across $(config.episodes) episodes the part generates contact attempts at a fixed base rate. A suppressed attempt reaches the vulnerable bundle only when the registration channel is open; if registered, it is Bayesian evidence for rejection.")
        println(io)
        println(io, "Four protective policies compete: attentional/relational exclusion, hypervigilant monitoring, internal attack, and suppression–flooding oscillation. A policy's comparison score is `direct cost + failure cost × (1 − reliability)`. Each seed instantiates four matched regimes, one making each policy cheap and reliable. The validation label is used only by world construction and scoring; `select_policy` receives a vector of policy objects and returns the minimum expected-cost policy.")
        println(io)
        println(io, "The public `register_contact!` function is the Experiment 49 extension point. A future protector gate can determine whether an attempted contact is suppressed and whether it reaches registration, while retaining the same vulnerable-bundle update.")
        println(io)
        println(io, "### Register guards")
        println(io)
        println(io, "*Configural* is reserved for within-bundle statistical organization. *Relational* refers only to interpersonal exclusion and the *alone with this* prior. *Witnessing* would name a context-held encounter with the vulnerable part; this protective policy comparison is not called witnessing. Protector contact is *befriending*. *Organization* is the fixed four-element bundle, couplings, precisions, and field profile. *Carrier* is independently parameterized substrate; none is modeled. These uses were fixed before confirmation.")
        println(io)
        println(io, "### Design decisions")
        println(io)
        println(io, "- The spec does not say whether the 20-world policy count should allocate worlds among four regimes or test every regime in every world. Testing four matched regimes per seed preserves the literal denominator of 20 for exclusion-favorable and competitor-favorable comparisons and lets every alternative face the same 20 fresh worlds.")
        println(io, "- “Where a competitor is [cheapest-reliable]” is operationalized conservatively at the world level: a world counts against exclusion if exclusion wins **any** of its three competitor-favorable comparisons.")
        println(io, "- “Cheapest-reliable” is represented by the expected-cost score rather than a two-stage eligibility rule. Reliability enters continuously through expected failure cost.")
        println(io, "- Policy selection is deterministic conditional on a world's authored costs and reliabilities. World stochasticity is in those parameters and the contact stream, not in an extra decision-noise term.")
        println(io, "- Starvation and confirmation use the exclusion-favorable comparison's selected policy. If exclusion failed to emerge there, attempts would not be marked suppressed and the consequence criteria would honestly fail.")
        println(io, "- Registration on, off, and ablated runs use the identical selected policy, initial prior, episode count, and pre-generated Boolean contact stream. The ablation is therefore marginally matched; it removes only representation of suppression as rejection.")
        println(io, "- Static is `maxₜ|Δpriorₜ| ≤ $(config.static_epsilon)` within each world, frozen after the pilot. Strengthening is endpoint `Δprior > $(config.static_epsilon)`; no post-pilot effect-size margin was introduced.")
        println(io, "- Both consequence regimes are paired within every world rather than assigned to different world subsets. Thus both are realized across the block and separated by the registration toggle alone.")
        println(io)
        println(io, "### Wiring note: why exclusion is not authored")
        println(io)
        println(io, "World construction writes `direct_cost` and `reliability` into four `ProtectivePolicy` records. `policy_expected_cost` combines those fields with the common failure cost. `select_policy` calls `argmin` on the four resulting scores. Its signature has no regime, intended-policy, or registration argument; `ProtectivePolicy` has no such field. No branch in selection reads the favorable-world label. The label is retained outside the selector only to verify whether the emergent winner tracks the authored cost structure.")
        println(io)
        check = self_check(config)
        println(io)
        println(io, "Structural audit: Experiment 43 channels match = `$(check.channels_match_experiment_43)`; base conditional rows normalized = `$(check.base_bundle_normalized)`; closed registration is a no-update path = `$(check.closed_registration_is_no_update)`; selector policy records contain no regime label = `$(check.policy_selector_has_no_regime_argument)`; registration is absent from policy records = `$(check.registration_absent_from_policy)`; selector returns the computed cheapest option = `$(check.selector_returns_cheapest)`; seed blocks are disjoint = `$(check.seed_blocks_disjoint)`.")
        println(io)
        println(io, "## Pilot")
        println(io)
        println(io, "Ten worlds (`14801:14810`) ran before freeze.")
        println(io)
        report_selection(io, pilot_summary)
        report_consequences(io, pilot_summary)
        println(io)
        println(io, "Pilot provisional verdicts: policy selection `$(verdict(pilot_summary.criteria.policy_selection))`; starvation `$(verdict(pilot_summary.criteria.starvation))`; confirmation `$(verdict(pilot_summary.criteria.confirmation))`; toggle separation `$(verdict(pilot_summary.criteria.toggle_separation))`. Pilot results were used only to freeze the static tolerance and inspect guards.")
        println(io)
        println(io, "## Freeze log")
        println(io)
        if isfile(FREEZE_LOG)
            println(io, "The static tolerance, directional strengthening test, provisional count thresholds, design, and vocabulary were frozen before confirmation. No threshold or parameter changed. Full details are in `freeze-log.md`.")
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
            println(io, "Twenty fresh worlds (`14851:14870`) ran after freeze; no seed overlaps the pilot.")
            println(io)
            report_selection(io, summary)
            report_consequences(io, summary)
            println(io)
            println(io, "### Verdict against §7.4")
            println(io)
            println(io, "1. `$(verdict(summary.criteria.policy_selection))` — exclusion ≥ `$(config.exclusion_favorable_threshold)/20` when cheapest-reliable and ≤ `$(config.competitor_exclusion_ceiling)/20` when a competitor is; every alternative appears in its own favorable regime.")
            println(io, "2. `$(verdict(summary.criteria.starvation))` — registration off keeps every episode at `|Δpriorₜ| ≤ $(config.static_epsilon)` during exclusion.")
            println(io, "3. `$(verdict(summary.criteria.confirmation))` — registration on strengthens the prior and registration ablation removes strengthening.")
            println(io, "4. `$(verdict(summary.criteria.toggle_separation))` — starvation and confirmation are both realized with selected policy and contact stream matched, so the registration toggle is the sole difference.")
            println(io)
            println(io, "Overall frozen-criterion verdict: **$(summary.all_criteria_pass ? "all four construction criteria passed" : "one or more construction criteria failed")**.")
        end
        println(io)
        println(io, "## Interpretation")
        println(io)
        if !confirmed
            println(io, "Pilot results are calibration only and license no confirmatory claim.")
        elseif confirmation_summary.all_criteria_pass
            println(io, "The implemented construction reproduces the specified conditional exiling result: exclusion is selected by expected-cost competition when it is the cheapest reliable protection, while each alternative wins under its own favorable costs. With exclusion held fixed, a closed registration channel starves the relational prior of evidence, whereas an open channel makes suppressed contact available as rejection and strengthens *alone with this*. Ablating registration removes that strengthening.")
            println(io)
            println(io, "This is an existence result inside an authored model. The construction shows that policy competition and the two consequence regimes can coexist computationally; it does not establish that these costs, likelihoods, update rules, or parts ontology describe people. In particular, the rejection likelihood and the mapping from a registered suppressed attempt to evidence are stipulated. The construction reproduces the strengthening under that stipulation; it does not derive the clinical mechanism.")
        else
            println(io, "The construction failed at least one frozen criterion. The failed counts above are retained without post-confirmatory retuning, so the conditional derived-exiling claim is not supported by this implementation.")
        end
    end
end

function summary_payload(config, pilot_summary;
        confirmation_summary = nothing)
    return (
        experiment = 48,
        name = "exiling_emergence",
        contract = "experiments-44-49-sufficiency-round-spec.md §7",
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
        experiment = 48,
        state = state,
        confirmation_complete = isfile(CONFIRMATION_MARKER),
        all_criteria_pass = all_criteria_pass,
        required_deliverables = required,
        present_deliverables = [file for file in required
            if isfile(joinpath(OUTPUT_DIR, file))],
        generated_at = string(now()),
    ))
end

function write_current_outputs(config, pilot_rows, pilot_summary;
        confirmation_rows = NamedTuple[], confirmation_summary = nothing)
    rows = isempty(confirmation_rows) ?
        pilot_rows : vcat(pilot_rows, confirmation_rows)
    GlobalPrecisionField.write_csv(joinpath(OUTPUT_DIR, "per_seed.csv"), rows)
    write_magic_numbers(config)
    GlobalPrecisionField.write_json(joinpath(OUTPUT_DIR, "summary.json"),
        summary_payload(config, pilot_summary;
            confirmation_summary = confirmation_summary))
    write_report(config, pilot_summary;
        confirmation_summary = confirmation_summary)
end

function run_pilot(config)
    isfile(CONFIRMATION_MARKER) &&
        error("confirmation is complete; refusing to overwrite frozen results")
    mkpath(OUTPUT_DIR)
    rows = run_block(config.pilot_seeds; stage = :pilot, config = config)
    summary = summarize_block(rows, config)
    write_current_outputs(config, rows, summary)
    write_status("pilot_complete_awaiting_freeze")
    return rows, summary
end

function freeze_pilot(config)
    isfile(CONFIRMATION_MARKER) &&
        error("confirmation is complete; refusing to rewrite freeze")
    mkpath(OUTPUT_DIR)
    rows = run_block(config.pilot_seeds; stage = :pilot, config = config)
    summary = summarize_block(rows, config)
    maximum(row.prior_off_maximum_episode_delta for row in rows) <=
        config.static_epsilon ||
        error("pilot does not support the proposed static tolerance")
    minimum(row.prior_on_delta for row in rows) > config.static_epsilon ||
        error("pilot does not support directional strengthening")
    write_freeze_log(config, summary)
    write_current_outputs(config, rows, summary)
    write_status("frozen_confirmation_unopened")
    return rows, summary
end

function run_confirmation(config)
    isfile(FREEZE_LOG) ||
        error("confirmation blocked: run --pilot and --freeze first")
    isfile(CONFIRMATION_MARKER) &&
        error("confirmation already complete; refusing to rerun")
    pilot_rows = run_block(config.pilot_seeds; stage = :pilot, config = config)
    pilot_summary = summarize_block(pilot_rows, config)
    confirmation_rows = run_block(config.confirmation_seeds;
        stage = :confirm, config = config)
    confirmation_summary = summarize_block(confirmation_rows, config)
    write_current_outputs(config, pilot_rows, pilot_summary;
        confirmation_rows = confirmation_rows,
        confirmation_summary = confirmation_summary)
    open(CONFIRMATION_MARKER, "w") do io
        println(io, "Experiment 48 confirmation completed at $(now())")
        println(io, "Seeds: 14851:14870")
    end
    write_status("confirmation_complete";
        all_criteria_pass = confirmation_summary.all_criteria_pass)
    return confirmation_rows, confirmation_summary
end

function main()
    length(ARGS) == 1 ||
        error("usage: run_exiling_emergence.jl --pilot|--freeze|--confirm")
    config = ExilingConfig()
    if ARGS[1] == "--pilot"
        _, summary = run_pilot(config)
        println("Experiment 48 pilot complete: all provisional checks = ",
            summary.all_criteria_pass)
    elseif ARGS[1] == "--freeze"
        freeze_pilot(config)
        println("Experiment 48 frozen; confirmation remains unopened.")
    elseif ARGS[1] == "--confirm"
        _, summary = run_confirmation(config)
        println("Experiment 48 confirmation complete: all criteria = ",
            summary.all_criteria_pass)
    else
        error("unknown mode $(ARGS[1])")
    end
end

main()
