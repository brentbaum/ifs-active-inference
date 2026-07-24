using Pkg
using Dates
using Printf

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(project_dir, "src", "IFSBundleInquiry.jl"))
include(joinpath(project_dir, "src", "FormationSubstrateTriad.jl"))
include(joinpath(project_dir, "src", "WagerViolation.jl"))

using .GlobalPrecisionField
using .WagerViolation

const OUTPUT_DIR = joinpath(project_dir, "results", "wager_violation")
const FREEZE_LOG = joinpath(OUTPUT_DIR, "freeze-log.md")
const CONFIRMATION_MARKER = joinpath(OUTPUT_DIR,
    "confirmation-complete.txt")

number(value) = @sprintf("%.6f", value)
label(value) = value ? "PASS" : "FAIL"

function config_record(config)
    return (
        pilot_seeds = config.pilot_seeds,
        confirmation_seeds = config.confirmation_seeds,
        sessions = config.sessions,
        corrective_evidence_sd = config.corrective_evidence_sd,
        corrective_target_scale = config.corrective_target_scale,
        base_coupling_learning_rate = config.base_coupling_learning_rate,
        low_coupling_plasticity = config.low_coupling_plasticity,
        high_coupling_plasticity = config.high_coupling_plasticity,
        maximum_learning_rate = config.maximum_learning_rate,
        match_tolerance = config.match_tolerance,
        inert_divergence_tolerance = config.inert_divergence_tolerance,
        active_divergence_required = config.active_divergence_required,
        alpha_two_sided = config.alpha_two_sided,
        target_power = config.target_power,
        measurement_noise_levels = config.measurement_noise_levels,
    )
end

function write_magic_numbers(config)
    open(joinpath(OUTPUT_DIR, "magic-numbers.md"), "w") do io
        println(io, "# Experiment 46 magic numbers")
        println(io)
        println(io, "- Pilot seeds: `18401:18410` (10 worlds).")
        println(io, "- Confirmation seeds: `18501:18520` (20 fresh worlds).")
        println(io, "- Witnessing-style corrective-evidence sessions: `$(config.sessions)`.")
        println(io, "- Corrective-evidence SD: `$(config.corrective_evidence_sd)`.")
        println(io, "- Corrective target: `$(config.corrective_target_scale) ×` each initial coupling.")
        println(io, "- Organization-only base coupling learning rate: `$(config.base_coupling_learning_rate)`.")
        println(io, "- Carrier plasticities (low/high): `$(config.low_coupling_plasticity)` / `$(config.high_coupling_plasticity)`.")
        println(io, "- Maximum learning rate: `$(config.maximum_learning_rate)`.")
        println(io, "- Organization matching tolerance: `$(config.match_tolerance)`.")
        println(io, "- Revision-trajectory metric: RMS paired distance over both coupling coordinates and all `$(config.sessions)` post-baseline sessions.")
        println(io, "- Carrier-inert tolerance: `≤ $(config.inert_divergence_tolerance)`.")
        println(io, "- Carrier-active required mean divergence: `≥ $(config.active_divergence_required)`.")
        println(io, "- Power curve: two-sided alpha `$(config.alpha_two_sided)`, target power `$(config.target_power)`, `$(length(config.confirmation_seeds))` matched pairs.")
        println(io, "- Measurement-noise sweep: `$(join(config.measurement_noise_levels, ", "))`.")
        println(io)
        println(io, "Register frozen before confirmation: coupling plasticity is carrier; it is excluded from every organization component and organization measure.")
    end
end

function write_freeze_log(config, pilot)
    open(FREEZE_LOG, "w") do io
        println(io, "# Experiment 46 freeze log")
        println(io)
        println(io, "- Frozen: $(Dates.format(now(), "yyyy-mm-dd HH:MM:SS")).")
        println(io, "- Pilot worlds opened: `18401:18410`.")
        println(io, "- Confirmation worlds remained unopened at freeze.")
        println(io, "- Seed blocks verified disjoint.")
        println(io, "- Revision metric fixed after pilot: RMS paired distance over both coupling trajectories, excluding the separately audited zero baseline.")
        println(io, "- Threshold changes after pilot: **none**. The provisional `0.02` inert ceiling and `0.10` active requirement were retained.")
        println(io, "- Pilot carrier-inert maximum divergence: `$(number(pilot.carrier_inert.maximum_divergence))`.")
        println(io, "- Pilot carrier-active mean divergence: `$(number(pilot.carrier_active.mean_divergence))`.")
        println(io, "- Pilot between-world active-effect SD frozen for the power curve: `$(number(pilot.carrier_active.sd_divergence))`.")
        println(io, "- Power analysis fixed as the normal-approximation paired-design MDE: `(z_.975 + z_.80) × sqrt(pilot_between_world_SD² + 2 × measurement_noise_SD²) / sqrt(20)`.")
        println(io, "- Register frozen: organization = bundle + couplings + precisions + field profile; carrier = independently parameterized substrate. Coupling plasticity remains carrier-only.")
        println(io, "- No confirmation result was available when this file was written.")
    end
end

function audit_markdown(io, audit)
    println(io, "| File/lines | Update equation | Inputs | Classification | Carrier read? | Scope |")
    println(io, "|---|---|---|---|---:|---|")
    for row in audit
        println(io, "| `$(row.file):$(row.lines)` | `$(row.equation)` | $(row.inputs) | $(row.classification) | $(row.carrier_read) | $(row.transition_scope) |")
    end
end

function write_report(pilot, confirmation, audit, ablation, curve;
        confirmation_opened)
    open(joinpath(OUTPUT_DIR, "report.md"), "w") do io
        println(io, "# Experiment 46: the wager-violation construction")
        println(io)
        println(io, "## Design")
        println(io)
        println(io, "This construction gives Experiment 45 recruitment-style carriers one transition-relevant parameter: coupling plasticity under corrective evidence. Each seed creates a pair with separately materialized but numerically identical pre-intervention organizations. The paired carriers have identical affect and policy priors and differ only in coupling plasticity (`0.00` versus `0.30`). Both members receive the same twelve-session witnessing-style corrective-evidence stream.")
        println(io)
        println(io, "In arm (a), the carrier-inert transition reads the current couplings, their fixed organization precisions, and corrective evidence; plasticity has no input path. In arm (b), the carrier-active transition adds carrier plasticity to the coupling learning rate. The revision-trajectory metric is the RMS paired distance across both coupling coordinates and every post-baseline session. Couplings are organization variables; carrier plasticity is not included in this or any organization measure.")
        println(io)
        println(io, "### Register guards")
        println(io)
        println(io, "*Organization* is the four-element bundle, its couplings, its precisions, and the field profile, fixed in advance. *Carrier* is independently parameterized substrate. Coupling plasticity is a **carrier** parameter and never enters the organization-matching vector, revision measure, precision profile, or field profile. No measure was renamed after results.")
        println(io)
        println(io, "### Design decisions")
        println(io)
        println(io, "- One seed is one matched agent pair; arms are paired within seed and replay identical evidence.")
        println(io, "- “Witnessing-style” is operationalized as context-held repeated corrective evidence with the complete, fixed organization precision profile available on every update. This is a construction, not a claim that the two-coupling update exhausts witnessing.")
        println(io, "- The spec did not define a revision-trajectory metric. After the pilot, RMS distance over both coupling coordinates and all post-baseline sessions was frozen; baseline matching is audited separately.")
        println(io, "- The active criterion is applied to the mean paired divergence across worlds; the inert criterion uses the stricter maximum paired divergence.")
        println(io, "- The power curve's “carrier effect” is response divergence on the frozen trajectory metric, not a biological parameter estimate. Measurement noise is modeled as independent error of SD `σ` on each member's organization-derived effect measurement.")
        println(io, "- Normal-approximation MDE uses two-sided α = `0.05`, power = `0.80`, twenty matched pairs, and the pilot-frozen between-world SD.")
        println(io, "- Exact matching means independent reconstruction plus bitwise equality and maximum componentwise absolute error at or below `1e-12`.")
        println(io)
        println(io, "## Organization matching procedure")
        println(io)
        println(io, "Experiment 45 generates one prepared-world organization. The procedure reconstructs two independent immutable `PartOrganization` values from its bundle, couplings, precisions, and field profile. Only after those copies exist are two new `PreparedCarrier` values attached. Their affect and policy fields are equal; IDs distinguish the substrates; coupling plasticity is the sole parameter difference.")
        println(io)
        println(io, "Pilot verification: maximum absolute mismatch `$(number(pilot.organization_matching.maximum_abs_difference))`; all pairs bitwise equal `$(pilot.organization_matching.all_bitwise_equal)`; all within tolerance `$(pilot.organization_matching.all_within_tolerance)`.")
        if confirmation_opened
            println(io, "Confirmation verification: maximum absolute mismatch `$(number(confirmation.organization_matching.maximum_abs_difference))`; all pairs bitwise equal `$(confirmation.organization_matching.all_bitwise_equal)`; all within tolerance `$(confirmation.organization_matching.all_within_tolerance)`.")
        end
        println(io)
        println(io, "This audit compares all four registered components separately in `per_seed.csv`: bundle, couplings, precisions, and field profile. Carrier plasticity is recorded in separate carrier columns and is never concatenated into the matching vector.")
        println(io)
        println(io, "## Machinery audit")
        println(io)
        println(io, "The analytic audit distinguishes corrective/revision transitions from formation and residue machinery. The existing IFS inquiry revision loop has no carrier input. Experiment 45's interference shift reads organization targets and fixed model rates but not `coupling_plasticity`; its formation prior, carrier-identity gate, and residue decomposition do read carrier information and are explicitly shown rather than hidden. Thus the narrow claim supported by the audit is: **the pre-Experiment-46 corrective/revision equations have no coupling-plasticity path**. A broader claim that every Experiment 45 equation is organization-only would be false.")
        println(io)
        audit_markdown(io, audit)
        println(io)
        println(io, "### Ablation")
        println(io)
        println(io, "- Experiment 45 formation replay with carrier plasticities changed from all zero to `[-10, 3, 50, 1000]`: maximum estimate difference `$(number(ablation.formation_triad.maximum_estimate_difference))`; exact invariance `$(ablation.formation_triad.exact_invariance)`.")
        println(io, "- IFS bundle-count update replay while an external carrier value changes from `0` to `1000`: carrier input port exists `$(ablation.ifs_bundle_inquiry.carrier_input_port_exists)`; maximum update difference `$(number(ablation.ifs_bundle_inquiry.maximum_update_difference))`; exact invariance `$(ablation.ifs_bundle_inquiry.exact_invariance)`.")
        println(io, "- Experiment 46 active transition before ablation: divergence `$(number(ablation.wager_transition.active_divergence))`; with the carrier read ablated: `$(number(ablation.wager_transition.ablated_divergence))`; inert comparator: `$(number(ablation.wager_transition.inert_divergence))`; ablation restores inert behavior `$(ablation.wager_transition.ablation_restores_inert)`.")
        println(io)
        println(io, "## Pilot")
        println(io)
        println(io, "Ten worlds (`18401:18410`) were run. Carrier-inert mean/maximum divergence was `$(number(pilot.carrier_inert.mean_divergence))` / `$(number(pilot.carrier_inert.maximum_divergence))`. Carrier-active mean divergence was `$(number(pilot.carrier_active.mean_divergence))` (range `$(number(pilot.carrier_active.minimum_divergence))`–`$(number(pilot.carrier_active.maximum_divergence))`; SD `$(number(pilot.carrier_active.sd_divergence))`).")
        println(io)
        println(io, "## Freeze log")
        println(io)
        println(io, "The trajectory metric was fixed at pilot and the provisional thresholds were retained. Confirmation remained unopened until the register, metric, thresholds, power formula, and noise sweep were written to `freeze-log.md` and `magic-numbers.md`.")
        println(io)
        println(io, "## Confirmatory results")
        println(io)
        if !confirmation_opened
            println(io, "The twenty-world confirmatory block has not been opened.")
        else
            println(io, "Twenty fresh worlds (`18501:18520`) were run after freeze; the seed block is disjoint from the pilot.")
            println(io)
            println(io, "- Arm (a), carrier-inert: mean divergence `$(number(confirmation.carrier_inert.mean_divergence))`; maximum `$(number(confirmation.carrier_inert.maximum_divergence))`; required maximum `≤ $(confirmation.carrier_inert.tolerance)`.")
            println(io, "- Arm (b), carrier-active: mean divergence `$(number(confirmation.carrier_active.mean_divergence))`; range `$(number(confirmation.carrier_active.minimum_divergence))`–`$(number(confirmation.carrier_active.maximum_divergence))`; required mean `≥ $(confirmation.carrier_active.required)`.")
            println(io, "- Organization match: maximum absolute mismatch `$(number(confirmation.organization_matching.maximum_abs_difference))`; every pair bitwise equal and within tolerance `$(confirmation.criteria.organization_matching_verified)`.")
            println(io)
            println(io, "### Verdicts")
            println(io)
            println(io, "1. **$(label(confirmation.criteria.criterion_1_inert_invariance)) — carrier-inert invariance.**")
            println(io, "2. **$(label(confirmation.criteria.criterion_2_active_divergence)) — carrier-moderated divergence with verified organization matching.**")
            println(io, "3. **$(label(confirmation.criteria.organization_matching_verified)) — organization-matching audit.**")
            overall = confirmation.criteria.criterion_1_inert_invariance &&
                confirmation.criteria.criterion_2_active_divergence &&
                confirmation.criteria.organization_matching_verified
            println(io)
            println(io, "Overall frozen conjunction: **$(label(overall))**.")
        end
        println(io)
        println(io, "## Power curve")
        println(io)
        println(io, "The dedicated `power_curve.csv` gives the minimum response-divergence effect detectable with 80% power in twenty matched pairs as organization measurement noise increases. It combines independent measurement error from both members (`2σ²`) with the pilot-frozen between-world effect variance. These values are feasibility calculations for a future measurement design, not confirmatory outcomes.")
        println(io)
        println(io, "| Organization measurement noise SD | Minimum detectable carrier effect |")
        println(io, "|---:|---:|")
        for row in curve
            println(io, "| $(number(row.organization_measurement_noise_sd)) | $(number(row.minimum_detectable_carrier_effect)) |")
        end
        println(io)
        println(io, "## Interpretation guard")
        println(io)
        println(io, "Arm (b) is not evidence the wager is false of people. It is the pattern the wager stakes itself against, made concrete — and the demonstration that the losing condition is coherent, detectable, and not absorbable once organization is fixed in advance.")
    end
end

function write_outputs(pilot_rows, confirmation_rows, config;
        confirmation_opened)
    mkpath(OUTPUT_DIR)
    pilot = summarize_block(pilot_rows, config)
    confirmation = confirmation_opened ?
        summarize_block(confirmation_rows, config) : nothing
    audit = machinery_audit()
    ablation = machinery_ablation(config)
    curve = power_curve(pilot_rows, config)
    all_rows = confirmation_opened ?
        vcat(pilot_rows, confirmation_rows) : pilot_rows
    GlobalPrecisionField.write_csv(joinpath(OUTPUT_DIR, "per_seed.csv"),
        all_rows)
    GlobalPrecisionField.write_csv(joinpath(OUTPUT_DIR, "power_curve.csv"),
        curve)
    summary = (
        experiment = 46,
        title = "wager-violation construction",
        stage = confirmation_opened ? "confirmation" : "pilot",
        seeds = (
            pilot = config.pilot_seeds,
            confirmation = config.confirmation_seeds,
            disjoint = isempty(intersect(config.pilot_seeds,
                config.confirmation_seeds)),
        ),
        register = (
            organization = "bundle + couplings + precisions + field profile",
            carrier = "independently parameterized substrate",
            coupling_plasticity_classification = "carrier",
            coupling_plasticity_in_organization_measure = false,
        ),
        config = config_record(config),
        pilot = pilot,
        confirmation = confirmation,
        machinery_audit = audit,
        machinery_ablation = ablation,
        power_curve = curve,
    )
    GlobalPrecisionField.write_json(joinpath(OUTPUT_DIR, "summary.json"),
        summary)
    criteria = confirmation_opened ? confirmation.criteria : pilot.criteria
    overall = confirmation_opened &&
        criteria.criterion_1_inert_invariance &&
        criteria.criterion_2_active_divergence &&
        criteria.organization_matching_verified
    GlobalPrecisionField.write_json(joinpath(OUTPUT_DIR, "status.json"), (
        experiment = 46,
        stage = confirmation_opened ? "confirmation" : "pilot",
        pilot_complete = true,
        frozen = isfile(FREEZE_LOG),
        confirmation_opened = confirmation_opened,
        confirmation_complete = confirmation_opened,
        seed_blocks_disjoint = true,
        criteria = criteria,
        overall = confirmation_opened ?
            (overall ? "passed" : "failed") : "pilot_only",
    ))
    write_magic_numbers(config)
    write_report(pilot, confirmation, audit, ablation, curve;
        confirmation_opened = confirmation_opened)
    return summary
end

function main()
    mode = isempty(ARGS) ? "pilot" : ARGS[1]
    mode in ("pilot", "confirm", "smoke") ||
        error("usage: run_wager_violation.jl [pilot|confirm|smoke]")
    config = WagerViolationConfig()
    @assert config.pilot_seeds == collect(18401:18410)
    @assert config.confirmation_seeds == collect(18501:18520)
    @assert isempty(intersect(config.pilot_seeds, config.confirmation_seeds))
    if mode == "smoke"
        self_check(config)
        println("Experiment 46 smoke checks passed.")
        return
    end
    isfile(CONFIRMATION_MARKER) &&
        error("confirmation output already exists; refusing a rerun")
    if mode == "pilot"
        mkpath(OUTPUT_DIR)
        pilot_rows = run_block(config.pilot_seeds; stage = :pilot,
            config = config)
        pilot = summarize_block(pilot_rows, config)
        write_freeze_log(config, pilot)
        summary = write_outputs(pilot_rows, NamedTuple[], config;
            confirmation_opened = false)
        println("Wrote and froze Experiment 46 pilot to $OUTPUT_DIR")
        println("Pilot active mean divergence: ",
            summary.pilot.carrier_active.mean_divergence)
        println("Confirmation seeds were not opened.")
        return
    end
    isfile(FREEZE_LOG) ||
        error("pilot freeze log missing; run pilot before confirm")
    pilot_rows = run_block(config.pilot_seeds; stage = :pilot,
        config = config)
    confirmation_rows = run_block(config.confirmation_seeds;
        stage = :confirmation, config = config)
    summary = write_outputs(pilot_rows, confirmation_rows, config;
        confirmation_opened = true)
    open(CONFIRMATION_MARKER, "w") do io
        println(io, "Experiment 46 confirmation completed ",
            Dates.format(now(), "yyyy-mm-dd HH:MM:SS"))
    end
    println("Wrote the single frozen Experiment 46 confirmation to $OUTPUT_DIR")
    println("Confirmation criteria: ", summary.confirmation.criteria)
end

main()
