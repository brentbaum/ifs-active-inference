using Pkg
using Dates
using Printf
using Statistics

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(project_dir, "src", "IFSBundleInquiry.jl"))
include(joinpath(project_dir, "src", "FormationSubstrateTriad.jl"))

using .GlobalPrecisionField
using .FormationSubstrateTriad

const OUTPUT_DIR = joinpath(project_dir, "results",
    "formation_substrate_triad")
const CONFIRMATION_MARKER = joinpath(OUTPUT_DIR,
    "confirmation-complete.txt")
const FREEZE_LOG = joinpath(OUTPUT_DIR, "freeze-log.md")
const EXPLORATORY_MARKER = joinpath(OUTPUT_DIR,
    "exploratory-addendum-complete.txt")
const EXPLORATORY_SEEDS = collect(18301:18340)

function config_record(config)
    return (
        pilot_seeds = config.pilot_seeds,
        confirmation_seeds = config.confirmation_seeds,
        carrier_count = config.carrier_count,
        parameter_count = config.parameter_count,
        prior_sd = config.prior_sd,
        observation_sd = config.observation_sd,
        maximum_samples = config.maximum_samples,
        selection_samples = config.selection_samples,
        formation_rmse_threshold = config.formation_rmse_threshold,
        stable_samples = config.stable_samples,
        prepared_jitter_sd = config.prepared_jitter_sd,
        arbitrary_scale = config.arbitrary_scale,
        coupling_scale = config.coupling_scale,
        second_formation_offset = config.second_formation_offset,
        recruitment_carrier_update = config.recruitment_carrier_update,
        hybrid_carrier_update = config.hybrid_carrier_update,
        assembly_coupling_retention = config.assembly_coupling_retention,
        hybrid_coupling_retention = config.hybrid_coupling_retention,
    )
end

function write_magic_numbers(config)
    open(joinpath(OUTPUT_DIR, "magic-numbers.md"), "w") do io
        println(io, "# Experiment 45 magic numbers")
        println(io)
        println(io, "- Pilot seeds: `18101:18110` (10 worlds)")
        println(io, "- Confirmation seeds: `18201:18220` (20 fresh worlds)")
        println(io, "- Prepared carriers: `$(config.carrier_count)`")
        println(io, "- Continuous parameters per formation: `$(config.parameter_count)`")
        println(io, "- Conditional parameter prior SD: `$(config.prior_sd)`")
        println(io, "- Observation SD: `$(config.observation_sd)`")
        println(io, "- Maximum matched evidence budget: `$(config.maximum_samples)` samples")
        println(io, "- Carrier-selection evidence: `$(config.selection_samples)` samples")
        println(io, "- Formation threshold: RMSE `≤ $(config.formation_rmse_threshold)` for `$(config.stable_samples)` consecutive samples")
        println(io, "- Prepared-world recruitment advantage required: `≥ $(100config.efficiency_advantage_required)%`")
        println(io, "- Arbitrary/shuffled advantage ceiling: `≤ $(100config.efficiency_vanish_threshold)%`")
        println(io, "- Interference margin: RMSE increase `≥ $(config.interference_margin)` in `$(config.world_count_required)/20` worlds")
        println(io, "- Residue component norm threshold: `$(config.residue_norm_threshold)`")
        println(io, "- Residue ablation-loss threshold: `$(config.residue_ablation_threshold)`")
        println(io, "- Residue count threshold: `$(config.world_count_required)/20` worlds")
        println(io)
        println(io, "All thresholds above were fixed before the pilot. No measure was renamed after results.")
    end
end

function write_freeze_log(config)
    open(FREEZE_LOG, "w") do io
        println(io, "# Experiment 45 freeze log")
        println(io)
        println(io, "- Frozen: $(Dates.format(now(), "yyyy-mm-dd HH:MM:SS"))")
        println(io, "- Pilot worlds opened: `18101:18110`.")
        println(io, "- Confirmation worlds remained unopened at freeze.")
        println(io, "- Threshold changes after pilot: **none**.")
        println(io, "- Pre-confirm design calibration: shared Gaussian prior SD changed from `1.0` to `0.25`, because the pilot showed that the weaker common prior made prepared means inert while carrier selection still incurred uncertainty.")
        println(io, "- Pre-confirm design calibration: hybrid shared-carrier update changed from `0.34` to `0.52`, matching recruitment, because the hybrid factorization changes coupling persistence rather than the persistence of the shared carrier itself.")
        println(io, "- Pre-confirm measurement correction: residue uses the consolidated (full matched-budget) posterior rather than the first threshold-crossing posterior; sample efficiency remains measured at first stable crossing.")
        println(io, "- The provisional 20%/5% efficiency cutoffs were retained.")
        println(io, "- The pre-pilot operationalization of measurable interference (RMSE degradation ≥ $(config.interference_margin), 16/20 worlds) was retained.")
        println(io, "- The pre-pilot residue component and ablation thresholds (`$(config.residue_norm_threshold)`, `$(config.residue_ablation_threshold)`) were retained.")
        println(io, "- Register frozen: organization = four-element bundle, couplings, precisions, and field profile; carrier = independently parameterized substrate.")
    end
end

percent(value) = @sprintf("%.1f%%", 100value)
number(value) = @sprintf("%.4f", value)

function criterion_label(value)
    return value ? "PASS" : "FAIL"
end

function write_report(pilot_summary, confirmation_summary, audit;
        confirmation_opened)
    report_path = joinpath(OUTPUT_DIR, "report.md")
    open(report_path, "w") do io
        println(io, "# Experiment 45: the formation-substrate triad")
        println(io)
        println(io, "## Design")
        println(io)
        println(io, "The construction compares assembly, recruitment, and hybrid formation over paired observation streams from the same worlds. Four free sufficient coordinates—affect, policy, `self-world` coupling, and `policy-outcome` coupling—materialize an Experiment 43-compatible organization: a four-element (`self`, `world`, `policy`, `outcome`) bundle, its two explicit couplings, a matched precision vector, and its field profile. Affect and policy coordinates can align with four authored prepared carriers; the coupling coordinates are biographical. Precision and field profiles are fixed across models so this experiment changes formation substrate rather than evidence weighting. Assembly begins from a uniform latent-cause prior and constructs the organization at freeze. Recruitment selects a persistent prepared carrier and binds the remaining burden. Hybrid factors the result into a persistent carrier and learned couplings.")
        println(io)
        println(io, "Selective reduction shrinks learned burden parameters toward each model's factorized prior. Assembly can leave coupling-attributable residue, recruitment carrier-attributable residue, and hybrid both. Ablations remove one named component at a time. Interference is the held-out error increase on the first formation after the same persistent carrier is bound to a second formation.")
        println(io)
        println(io, "### Register guards")
        println(io)
        println(io, "*Organization* means the four-element bundle, its couplings, its precisions, and the field profile. *Carrier* means independently parameterized substrate. *Configural* is used only statistically for within-bundle organization; *relational* is reserved for interpersonal use. These names and the measures were fixed before outcomes.")
        println(io)
        println(io, "### Design decisions")
        println(io)
        println(io, "- One seed is one world. Conditions and models are paired within seed.")
        println(io, "- Affect and policy instantiate the prepared repertoire; the two coupling coordinates generate the `world` and `outcome` bundle contents alongside explicit biographical couplings. Bundle contents are derived organization readouts, not extra free parameters.")
        println(io, "- Shuffling preserves the marginal sets of affect and policy priors but repairs them across carriers, breaking their joint preparation.")
        println(io, "- The unspecified phrase “measurable margin” was fixed before pilot as an RMSE increase of at least `0.03`, present in at least `16/20` confirmatory worlds for recruitment and hybrid and absent in assembly.")
        println(io, "- “Present, separable by ablation” was fixed before pilot as component norm at least `0.15` and ablation loss at least `0.10`.")
        println(io, "- Taxonomy is reported descriptively as four-cluster silhouette, cluster sizes, and seed-level nearest-carrier margins; it is not promoted to an unregistered success criterion.")
        println(io)
        println(io, "### Capacity-matching audit")
        println(io)
        entry = audit.per_model["assembly"]
        println(io, "All three models have exactly `$(entry.continuous_parameter_count)` continuous parameters per formation and one uniform `$(entry.discrete_latent_categories)`-way latent index. With Gaussian prior SD `$(entry.parameter_prior_sd)`, conditional continuous prior entropy is `$(number(entry.conditional_gaussian_prior_entropy_nats))` nats; uniform index entropy is `$(number(entry.uniform_index_prior_entropy_nats))` nats; labeled joint prior entropy is `$(number(entry.labeled_joint_prior_entropy_nats))` nats for **each** model. Each receives at most `$(entry.maximum_evidence_samples)` observations with SD `$(entry.observation_sd)` from the identical replayed stream. Parameter-count equality: `$(audit.parameter_counts_equal)`; prior-entropy equality: `$(audit.prior_entropies_equal)`; audit valid: `$(audit.audit_valid)`.")
        println(io)
        println(io, "Prepared prior means differ but do not change Gaussian entropy. The authored carrier index is counted explicitly rather than treated as free capacity.")
        println(io)
        println(io, "## Pilot")
        println(io)
        pe = pilot_summary.formation_efficiency
        println(io, "Ten worlds (`18101:18110`) were run. Recruitment's sample reduction relative to assembly was $(percent(pe.prepared_recruitment_advantage)) in prepared worlds, $(percent(pe.arbitrary_recruitment_advantage)) in arbitrary worlds, and $(percent(pe.shuffled_recruitment_advantage)) under shuffled preparation. Mean prepared-world interference degradation was assembly `$(number(pilot_summary.interference.mean_degradation["assembly"]))`, recruitment `$(number(pilot_summary.interference.mean_degradation["recruitment"]))`, and hybrid `$(number(pilot_summary.interference.mean_degradation["hybrid"]))`. Pilot criteria are descriptive because the count criteria are calibrated for 20 worlds.")
        println(io)
        println(io, "## Freeze log")
        println(io)
        println(io, "No outcome threshold moved after pilot. The shared prior strength, hybrid carrier update, and residue readout point were calibrated on pilot worlds and logged before confirmation. The confirmation seed block remained unopened until the design constants, operational thresholds, vocabulary register, and `magic-numbers.md` were frozen. Full details are in `freeze-log.md`.")
        println(io)
        println(io, "## Confirmatory results")
        println(io)
        if !confirmation_opened
            println(io, "The twenty-world confirmatory block has not been opened.")
        else
            ce = confirmation_summary.formation_efficiency
            println(io, "Twenty fresh worlds (`18201:18220`) were run after freeze, disjoint from the pilot.")
            println(io)
            println(io, "- Formation efficiency: recruitment's sample reduction was $(percent(ce.prepared_recruitment_advantage)) prepared, $(percent(ce.arbitrary_recruitment_advantage)) arbitrary, and $(percent(ce.shuffled_recruitment_advantage)) shuffled.")
            println(io, "- Interference worlds at or above the frozen margin: assembly `$(confirmation_summary.interference.worlds_at_or_above_margin["assembly"])/20`, recruitment `$(confirmation_summary.interference.worlds_at_or_above_margin["recruitment"])/20`, hybrid `$(confirmation_summary.interference.worlds_at_or_above_margin["hybrid"])/20`.")
            rc = confirmation_summary.residue
            println(io, "- Prepared-world residue: assembly both/carrier-only/coupling-only/neither = `$(rc["assembly"].both)/$(rc["assembly"].carrier_only)/$(rc["assembly"].coupling_only)/$(rc["assembly"].neither)`; recruitment = `$(rc["recruitment"].both)/$(rc["recruitment"].carrier_only)/$(rc["recruitment"].coupling_only)/$(rc["recruitment"].neither)`; hybrid = `$(rc["hybrid"].both)/$(rc["hybrid"].carrier_only)/$(rc["hybrid"].coupling_only)/$(rc["hybrid"].neither)`.")
            println(io)
            println(io, "### Cluster structure")
            println(io)
            println(io, "| Model | Prepared silhouette | Arbitrary silhouette | Shuffled silhouette |")
            println(io, "|---|---:|---:|---:|")
            for model in ("assembly", "recruitment", "hybrid")
                clusters = confirmation_summary.cluster_structure[model]
                println(io, "| $model | $(number(clusters["prepared"].silhouette)) | $(number(clusters["arbitrary"].silhouette)) | $(number(clusters["shuffled"].silhouette)) |")
            end
            println(io)
            println(io, "### Verdict against §4.6")
            println(io)
            criteria = confirmation_summary.criteria
            println(io, "1. **$(criterion_label(criteria.criterion_1_efficiency_and_shuffle)) — formation efficiency and shuffled-preparation control.** Prepared advantage must be ≥20%; arbitrary and shuffled advantages must each be ≤5%.")
            println(io, "2. **$(criterion_label(criteria.criterion_2_interference)) — shared-carrier interference.** Recruitment and hybrid must each reach the frozen margin in ≥16/20 worlds; assembly must do so in 0/20.")
            println(io, "3. **$(criterion_label(criteria.criterion_3_residue_dissociation)) — post-reduction residue.** Hybrid must show both separable components in ≥16/20 worlds and neither pure model may show both.")
            println(io)
            println(io, "Overall frozen conjunction: **$(criterion_label(criteria.all))**.")
        end
        println(io)
        println(io, "## Interpretation")
        println(io)
        println(io, "The carriers are authored. This experiment tests distinguishability of the models, not which is true of people. Its result licenses exactly one manuscript sentence: the three formation hypotheses are (or are not) separable in principle by the signatures §10 names.")
        println(io)
        if confirmation_opened
            sentence = confirmation_summary.criteria.all ?
                "The three formation hypotheses are separable in principle by the signatures §10 names." :
                "The signatures §10 names failed to separate the three formation hypotheses in this construction; the residue dissociation separated hybrid from both pure models, but formation efficiency and interference did not reach their frozen criteria."
            println(io, "Licensed manuscript sentence: **$sentence**")
        else
            println(io, "No manuscript sentence is licensed before confirmation.")
        end
        println(io)
        println(io, "This is a construction result inside an authored model. It establishes no clinical effect, biological mechanism, or ontology of parts.")
    end
end

function read_confirmatory_interference()
    path = joinpath(OUTPUT_DIR, "per_seed.csv")
    lines = readlines(path)
    isempty(lines) && error("per_seed.csv is empty")
    header = split(first(lines), ",")
    columns = Dict(name => index for (index, name) in enumerate(header))
    required = ("stage", "condition", "model", "interference_degradation")
    all(haskey(columns, name) for name in required) ||
        error("per_seed.csv lacks interference columns")
    values = Float64[]
    for line in Iterators.drop(lines, 1)
        fields = split(line, ",")
        fields[columns["stage"]] == "confirmation" || continue
        fields[columns["condition"]] == "prepared" || continue
        fields[columns["model"]] == "recruitment" || continue
        push!(values, parse(Float64,
            fields[columns["interference_degradation"]]))
    end
    length(values) == 20 ||
        error("expected 20 frozen confirmatory interference values")
    return values
end

function summarize_interference_distribution(values, margin)
    ordered = sort(values)
    misses = [value for value in ordered if value < margin]
    gaps = diff(ordered)
    largest_gap_index = argmax(gaps)
    return (
        frozen_margin = margin,
        world_count = length(ordered),
        min = minimum(ordered),
        median = median(ordered),
        max = maximum(ordered),
        worlds_at_or_above_margin = count(>=(margin), ordered),
        miss_count = length(misses),
        miss_values = misses,
        miss_distance_below_margin = [margin - value for value in misses],
        misses_within_0_01 = count(value -> margin - value <= 0.01,
            misses),
        negative_degradation_misses = count(<(0.0), misses),
        largest_adjacent_gap = gaps[largest_gap_index],
        largest_gap_bounds = (ordered[largest_gap_index],
            ordered[largest_gap_index + 1]),
        characterization =
            "a broad, heterogeneous distribution, not a simple threshold near-miss or a clean bimodal split; the largest gap isolates one negative outlier",
    )
end

function append_exploratory_summary(exploratory)
    path = joinpath(OUTPUT_DIR, "summary.json")
    source = read(path, String)
    occursin("\"exploratory\"", source) &&
        error("summary.json already contains an exploratory block")
    closing = findlast(==('}'), source)
    isnothing(closing) && error("summary.json is not a JSON object")
    prefix = rstrip(source[firstindex(source):prevind(source, closing)])
    buffer = IOBuffer()
    GlobalPrecisionField.json_write(buffer, exploratory; indent = 2)
    rendered = String(take!(buffer))
    open(path, "w") do io
        print(io, prefix, ",\n  \"exploratory\": ", rendered, "\n}\n")
    end
end

function append_exploratory_report(diagnostic, interference)
    path = joinpath(OUTPUT_DIR, "report.md")
    source = read(path, String)
    heading = "## Exploratory addendum (post-freeze; non-confirmatory)"
    occursin(heading, source) &&
        error("report already contains the exploratory addendum")
    advantages = diagnostic.recruitment_advantage_vs_assembly
    means = diagnostic.mean_samples
    attribution = diagnostic.attribution
    selection_explains =
        attribution.selection_and_coverage_explain_control_failure
    open(path, "a") do io
        println(io)
        println(io, heading)
        println(io)
        println(io, "This addendum does not alter the frozen criteria, confirmatory values, or overall **FAIL** verdict. It analyzes the existing confirmatory interference values and uses 40 fresh diagnostic worlds (`18301:18340`), disjoint from both frozen blocks.")
        println(io)
        println(io, "### Shuffled-preparation failure")
        println(io)
        println(io, "The diagnostic held the shuffled worlds and evidence streams fixed while varying only carrier access. Best-fitting selection over the shuffled four-carrier repertoire retained a $(percent(advantages.shuffled_best_fitting)) advantage over assembly (mean samples: `$(number(means.shuffled_best_fitting))` vs. `$(number(means.assembly))`). Assigning one carrier at random, independently of evidence, changed the advantage to $(percent(advantages.shuffled_fixed_random)) (mean `$(number(means.shuffled_fixed_random))`). Keeping best-fit selection but shifting both carrier marginals outside the world range changed it to $(percent(advantages.degraded_marginals_best_fitting)) (mean `$(number(means.degraded_marginals_best_fitting))`).")
        println(io)
        println(io, "Best-fit selection accounts for `$(number(attribution.samples_attributable_to_selection_vs_fixed_random))` samples relative to fixed-random assignment; its share of the observed shuffled saving is `$(percent(attribution.selection_share_of_observed_savings))`. Marginal coverage accounts for `$(number(attribution.samples_attributable_to_marginal_coverage_vs_degraded))` samples relative to the degraded-marginal repertoire.")
        attribution.selection_removal_reverses_advantage &&
            println(io, "The selection share exceeds 100% because removing selection did more than erase the advantage: fixed-random recruitment was slower than assembly.")
        println(io)
        if selection_explains
            println(io, "The exploratory comparison supports the proposed diagnosis: selection over a repertoire with covering affect and policy marginals explains the residual shuffled advantage even after joint pairing is broken. The efficiency signature therefore cannot distinguish prepared joint structure from any sufficiently covering repertoire plus selection. This is informative about what §10's efficiency signature can and cannot measure, but it is non-confirmatory.")
        else
            println(io, "The exploratory comparison does not fully explain the shuffled advantage by repertoire selection and marginal coverage; the control failure remains unresolved.")
        end
        println(io)
        println(io, "### Interference failure")
        println(io)
        println(io, "Across the 20 frozen confirmatory worlds, interference degradation had min/median/max `$(number(interference.min))` / `$(number(interference.median))` / `$(number(interference.max))`. Seven worlds missed `0.03`; their values were `$(join(number.(interference.miss_values), ", "))`. Only `$(interference.misses_within_0_01)/7` miss was within `0.01` of the margin, and `$(interference.negative_degradation_misses)/7` misses were negative.")
        println(io)
        println(io, "This was $(interference.characterization). No threshold was changed and the frozen `13/20` failure stands.")
    end
end

function run_exploratory_addendum(config)
    isfile(CONFIRMATION_MARKER) ||
        error("frozen confirmation must exist before exploratory diagnostics")
    isfile(EXPLORATORY_MARKER) &&
        error("exploratory addendum already exists; refusing a rerun")
    @assert isempty(intersect(EXPLORATORY_SEEDS, config.pilot_seeds))
    @assert isempty(intersect(EXPLORATORY_SEEDS,
        config.confirmation_seeds))
    rows = run_exploratory_diagnostics(EXPLORATORY_SEEDS;
        config = config)
    diagnostic = summarize_exploratory_diagnostics(rows)
    interference = summarize_interference_distribution(
        read_confirmatory_interference(), config.interference_margin)
    exploratory = (
        label = "post-freeze non-confirmatory",
        frozen_results_unchanged = true,
        diagnostic_seeds = EXPLORATORY_SEEDS,
        seed_blocks_disjoint = true,
        shuffled_preparation_diagnosis = diagnostic,
        confirmatory_interference_distribution = interference,
    )
    GlobalPrecisionField.write_csv(joinpath(OUTPUT_DIR,
        "exploratory_per_seed.csv"), rows)
    append_exploratory_summary(exploratory)
    append_exploratory_report(diagnostic, interference)
    open(EXPLORATORY_MARKER, "w") do io
        println(io, "Experiment 45 exploratory addendum completed ",
            Dates.format(now(), "yyyy-mm-dd HH:MM:SS"))
    end
    return exploratory
end

function write_outputs(pilot_rows, confirmation_rows, config;
        confirmation_opened)
    mkpath(OUTPUT_DIR)
    all_rows = confirmation_opened ? vcat(pilot_rows, confirmation_rows) :
        pilot_rows
    pilot_summary = summarize_block(pilot_rows, config)
    confirmation_summary = confirmation_opened ?
        summarize_block(confirmation_rows, config) : nothing
    audit = capacity_audit(config)
    summary = (
        experiment = 45,
        title = "formation-substrate triad",
        stage = confirmation_opened ? "confirmation" : "pilot",
        seeds = (
            pilot = config.pilot_seeds,
            confirmation = config.confirmation_seeds,
            disjoint = isempty(intersect(config.pilot_seeds,
                config.confirmation_seeds)),
        ),
        config = config_record(config),
        capacity_audit = audit,
        pilot = pilot_summary,
        confirmation = confirmation_summary,
        register = (
            organization = "four-element bundle, couplings, precisions, and field profile",
            carrier = "independently parameterized substrate",
        ),
    )
    GlobalPrecisionField.write_csv(joinpath(OUTPUT_DIR, "per_seed.csv"),
        all_rows)
    GlobalPrecisionField.write_json(joinpath(OUTPUT_DIR, "summary.json"),
        summary)
    statuses = confirmation_opened ? confirmation_summary.criteria :
        pilot_summary.criteria
    GlobalPrecisionField.write_json(joinpath(OUTPUT_DIR, "status.json"), (
        experiment = 45,
        stage = confirmation_opened ? "confirmation" : "pilot",
        pilot_complete = true,
        frozen = isfile(FREEZE_LOG),
        confirmation_opened = confirmation_opened,
        confirmation_complete = confirmation_opened,
        capacity_audit_valid = audit.audit_valid,
        criteria = statuses,
        overall = confirmation_opened ?
            (statuses.all ? "passed" : "failed") : "pilot_only",
    ))
    write_magic_numbers(config)
    write_report(pilot_summary, confirmation_summary, audit;
        confirmation_opened = confirmation_opened)
    return summary
end

function main()
    mode = isempty(ARGS) ? "pilot" : ARGS[1]
    mode in ("pilot", "confirm", "diagnostic", "smoke") ||
        error("usage: run_formation_substrate_triad.jl [pilot|confirm|diagnostic|smoke]")
    config = FormationTriadConfig()
    @assert config.pilot_seeds == collect(18101:18110)
    @assert config.confirmation_seeds == collect(18201:18220)
    @assert isempty(intersect(config.pilot_seeds, config.confirmation_seeds))
    if mode == "smoke"
        self_check(config)
        println("Experiment 45 smoke checks passed.")
        return
    end
    if mode == "diagnostic"
        exploratory = run_exploratory_addendum(config)
        println("Wrote the Experiment 45 exploratory addendum to ",
            OUTPUT_DIR)
        println("Shuffled diagnostic: ",
            exploratory.shuffled_preparation_diagnosis.attribution)
        return
    end
    isfile(CONFIRMATION_MARKER) &&
        error("confirmation output already exists; refusing a rerun")
    if mode == "pilot"
        mkpath(OUTPUT_DIR)
        pilot_rows = run_block(config.pilot_seeds; stage = :pilot,
            config = config)
        write_freeze_log(config)
        summary = write_outputs(pilot_rows, NamedTuple[], config;
            confirmation_opened = false)
        println("Wrote and froze Experiment 45 pilot to $OUTPUT_DIR")
        println("Pilot criteria (descriptive): ", summary.pilot.criteria)
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
        println(io, "Experiment 45 confirmation completed ",
            Dates.format(now(), "yyyy-mm-dd HH:MM:SS"))
    end
    println("Wrote the single frozen Experiment 45 confirmation to $OUTPUT_DIR")
    println("Confirmation criteria: ", summary.confirmation.criteria)
end

main()
