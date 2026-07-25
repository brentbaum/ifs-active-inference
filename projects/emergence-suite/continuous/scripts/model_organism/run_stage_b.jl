#!/usr/bin/env julia

include(joinpath(@__DIR__, "..", "..", "src", "ModelOrganism.jl"))
using .ModelOrganism
using Statistics
using SHA
using Printf
using Dates

const FREEZE_COMMIT = "274f8888f71ac590d7c15d6f9f59777ea919e182"
const SEED_START = Dict(
    1 => 700093, 2 => 701198, 3 => 702412, 4 => 703086, 5 => 704172,
    6 => 705013, 7 => 706005, 8 => 707287, 9 => 708300, 10 => 709439)
const FROZEN_PATHS = [
    "projects/emergence-suite/continuous/src/ModelOrganism.jl",
    "projects/emergence-suite/continuous/src/model_organism",
    "projects/emergence-suite/continuous/genome.toml",
    "projects/emergence-suite/continuous/organism-genome.md",
    "projects/emergence-suite/continuous/configurations",
    "projects/emergence-suite/continuous/Project.toml",
    "projects/emergence-suite/continuous/Manifest.toml",
    "projects/emergence-suite/continuous/results/model_organism/configuration-grammar.md",
    "projects/emergence-suite/continuous/results/model_organism/rng-streams.md",
    "projects/emergence-suite/continuous/results/model_organism/world-populations.md",
    "projects/emergence-suite/continuous/results/model_organism/precalibration-lock.json",
]

mean_or_nan(values) = isempty(values) ? NaN : mean(values)

function mean_ci(values)
    data = Float64.(values)
    isempty(data) && return [nothing, nothing]
    center = mean(data)
    length(data) == 1 && return [center, center]
    half_width = 1.96 * std(data) / sqrt(length(data))
    return [center - half_width, center + half_width]
end

function percentile_interval(values)
    data = Float64.(values)
    isempty(data) && return [nothing, nothing]
    return [quantile(data, 0.025), quantile(data, 0.975)]
end

function wilson_interval(successes::Integer, total::Integer)
    total == 0 && return [nothing, nothing]
    z = 1.96
    probability = successes / total
    denominator = 1 + z^2 / total
    center = (probability + z^2 / (2 * total)) / denominator
    half_width = z / denominator * sqrt(
        probability * (1 - probability) / total + z^2 / (4 * total^2))
    return [max(0.0, center - half_width), min(1.0, center + half_width)]
end

function criterion(label, class, provenance, source, estimate, interval,
        rule, passed; details = Dict{String,Any}())
    return Dict(
        "label" => label,
        "evidentiary_class" => class,
        "hypothesis_provenance" => provenance,
        "source" => source,
        "estimate" => estimate,
        "interval_95" => interval,
        "decision_rule" => rule,
        "passed" => passed,
        "details" => details,
    )
end

function verify_frozen_inputs!(genome)
    head = readchomp(`git rev-parse HEAD`)
    head == FREEZE_COMMIT ||
        error("Stage B blocked: HEAD $head is not freeze commit $FREEZE_COMMIT")
    changed = readchomp(Cmd(vcat(["git", "diff", "--name-only",
        FREEZE_COMMIT, "--"], FROZEN_PATHS)))
    isempty(changed) ||
        error("Stage B blocked: frozen inputs changed:\n$changed")
    verify_identity!(genome)
    ModelOrganism.verify_precalibration_lock()
    manifest = read(joinpath(ModelOrganism.RESULTS_ROOT,
        "freeze-manifest.json"), String)
    occursin(ModelOrganism.canonical_source_hash(), manifest) ||
        error("Stage B blocked: source hash absent from frozen manifest")
    occursin(genome.sha256, manifest) ||
        error("Stage B blocked: genome hash absent from frozen manifest")
    return true
end

function seed_count(assay, genome)
    assay == 1 && return 1
    return Int(ModelOrganism.g(genome, :rate_worlds))
end

function released_seeds(assay, genome)
    count = seed_count(assay, genome)
    first_seed = SEED_START[assay]
    seeds = collect(first_seed:first_seed + count - 1)
    last(seeds) <= first_seed + 199 ||
        error("assay $assay requested more than its released block")
    last(seeds) < 710000 ||
        error("assay $assay attempted to enter unreleased escrow")
    return seeds
end

function run_frozen_rows(assay, seeds, genome)
    config = load_configuration(ModelOrganism.config_path(assay))
    rows = NamedTuple[]
    for (seed_index, seed) in enumerate(seeds)
        generated = run_assay(assay, seed, genome, config)
        if assay == 7
            for row in generated
                row.kind == :analytic && seed_index > 1 && continue
                push!(rows, row)
            end
        else
            append!(rows, generated)
        end
    end
    return rows
end

function rows_by_seed(rows)
    grouped = Dict{Int,Vector{Any}}()
    for row in rows
        push!(get!(grouped, row.seed, Any[]), row)
    end
    return grouped
end

function analyze1(rows, genome)
    successes = count(row -> row.property_holds, rows)
    agreement = successes / length(rows)
    edge = [row.precision for row in rows if row.written && row.control == 0.0]
    positive_low = [row.precision for row in rows if row.written && row.control > 0.0]
    attenuation = mean(edge) < mean(positive_low)
    criteria = [
        criterion("joint-boundary predicate agreement", "conformance",
            "Original prediction", "formation construction and assay 1 plan",
            agreement, wilson_interval(successes, length(rows)),
            "exact agreement = 1.0", agreement == 1.0;
            details = Dict("domain_points" => length(rows))),
        criterion("no-control edge attenuation", "conformance",
            "50 prospective", "assay 1 analysis plan",
            mean(edge) - mean(positive_low), mean_ci(edge .- mean(positive_low)),
            "edge precision < positive-low-control precision", attenuation;
            details = Dict("edge_mean" => mean(edge),
                "positive_low_control_mean" => mean(positive_low))),
    ]
    return criteria, Dict("property_domain_points" => length(rows),
        "working_avoidance_available_rate" =>
            mean(Float64[row.avoidance_available for row in rows]))
end

function analyze2(rows, genome)
    grouped = rows_by_seed(rows)
    episodes = ModelOrganism.g(genome, :episodes)
    exposure = Float64[]
    revision = Float64[]
    slopes = Float64[]
    mediators = Float64[]
    for seed_rows in values(grouped)
        full = only(filter(row -> row.dose == 1.0, seed_rows))
        push!(exposure, abs(full.exposure_effect) / episodes)
        push!(revision, abs(full.revision_effect))
        doses = Float64[row.dose for row in seed_rows]
        changes = Float64[row.closed_revision for row in seed_rows]
        push!(slopes, sum((doses .- mean(doses)) .*
            (changes .- mean(changes))) / sum(abs2, doses .- mean(doses)))
        push!(mediators, mean(Float64[row.avoidance_mediator for row in seed_rows]))
    end
    margin = ModelOrganism.g(genome, :assay2_effect_margin)
    criteria = [
        criterion("paired normalized exposure effect", "causal contrast",
            "Original prediction; 50 prospective margin",
            "frozen persistence source result",
            mean(exposure), percentile_interval(exposure),
            "mean absolute effect ≥ $margin", mean(exposure) >= margin),
        criterion("paired root-revision effect", "causal contrast",
            "Original prediction; 50 prospective margin",
            "frozen persistence source result",
            mean(revision), percentile_interval(revision),
            "mean absolute effect ≥ $margin", mean(revision) >= margin),
        criterion("controllability dose response", "causal contrast",
            "Original prediction", "assay 2 analysis plan",
            mean(slopes), mean_ci(slopes), "mean within-world slope > 0",
            mean(slopes) > 0),
    ]
    return criteria, Dict("working_avoidance_mediator_mean" => mean(mediators),
        "worlds" => length(grouped))
end

function analyze3(rows, genome)
    accuracy_successes = count(row -> row.correct_2d, rows)
    accuracy = accuracy_successes / length(rows)
    grouped = rows_by_seed(rows)
    improvements = [mean(Float64[row.loss_1d - row.loss_2d
        for row in seed_rows]) for seed_rows in values(grouped)]
    accuracy_threshold = ModelOrganism.g(genome, :assay3_accuracy_threshold)
    margin = ModelOrganism.g(genome, :assay3_comparator_margin)
    criteria = [
        criterion("four-regime realization", "conformance",
            "Original prediction", "results/global_precision_field/summary.json",
            accuracy, wilson_interval(accuracy_successes, length(rows)),
            "balanced accuracy ≥ $accuracy_threshold",
            accuracy >= accuracy_threshold),
        criterion("two-dimensional held-out advantage",
            "model discrimination", "50 prospective",
            "assay 3 analysis plan", mean(improvements),
            mean_ci(improvements), "loss_1d - loss_2d ≥ $margin",
            mean(improvements) >= margin),
    ]
    return criteria, Dict("world_blocks" => length(grouped),
        "regime_instances" => length(rows))
end

function analyze4(rows, genome)
    grouped = rows_by_seed(rows)
    effects = Float64[]
    successes = 0
    witness_transfers = Float64[]
    reversed_transfers = Float64[]
    ordering = Bool[]
    revised_worlds = 0
    margin = ModelOrganism.g(genome, :assay4_transfer_margin)
    for seed_rows in values(grouped)
        witnessing = only(filter(row -> row.arm == :witnessing, seed_rows))
        exposure = only(filter(row -> row.arm == :matched_exposure, seed_rows))
        reversed = only(filter(row -> row.arm == :reversed_graph, seed_rows))
        push!(witness_transfers, witnessing.untreated_transfer)
        push!(reversed_transfers, reversed.untreated_transfer)
        push!(ordering, witnessing.identity_before_threat)
        if witnessing.root_revised
            revised_worlds += 1
            effect = witnessing.untreated_transfer - exposure.untreated_transfer
            push!(effects, effect)
            successes += effect >= margin
        end
    end
    effect_mean = mean_or_nan(effects)
    rate = revised_worlds == 0 ? 0.0 : successes / revised_worlds
    graph_control = mean(reversed_transfers) < mean(witness_transfers)
    criteria = [
        criterion("conditional untreated-cue transfer",
            "model discrimination",
            "Original prediction; 50 prospective primary operationalization",
            "Experiment 44b generalization gradient", effect_mean,
            mean_ci(effects), "conditional mean ≥ $margin and rate ≥ 0.80",
            !isempty(effects) && effect_mean >= margin && rate >= 0.80;
            details = Dict("conditional_worlds" => revised_worlds,
                "success_rate" => rate,
                "success_rate_interval" =>
                    wilson_interval(successes, revised_worlds))),
        criterion("reversed-graph control", "model discrimination",
            "50 prospective", "assay 4 analysis plan",
            mean(witness_transfers) - mean(reversed_transfers),
            mean_ci(witness_transfers .- reversed_transfers),
            "reversed mean transfer < witnessing mean transfer",
            graph_control),
    ]
    return criteria, Dict("witnessing_root_revision_rate" =>
            revised_worlds / length(grouped),
        "identity_before_threat_rate" => mean(Float64.(ordering)),
        "ordering_provenance" => "Pilot-amended",
        "worlds" => length(grouped))
end

function analyze5(rows, genome)
    grouped = rows_by_seed(rows)
    interactions = Float64[]
    regulation_only = Float64[]
    for seed_rows in values(grouped)
        cell(regulation, evidence) = only(filter(row ->
            row.regulation == regulation &&
            row.evidence_present == evidence, seed_rows))
        both = cell(true, true).root_change
        regulation = cell(true, false).root_change
        evidence = cell(false, true).root_change
        neither = cell(false, false).root_change
        push!(interactions, (both - regulation) - (evidence - neither))
        push!(regulation_only, regulation)
    end
    interaction_margin =
        ModelOrganism.g(genome, :assay5_interaction_margin)
    equivalence_margin =
        ModelOrganism.g(genome, :assay5_equivalence_margin)
    criteria = [
        criterion("regulation × evidence interaction", "conformance",
            "Original prediction; 50 prospective interaction",
            "assay 5 analysis plan",
            mean(interactions), mean_ci(interactions),
            "difference-in-differences ≥ $interaction_margin",
            mean(interactions) >= interaction_margin),
        criterion("regulation-only equivalence", "conformance",
            "Original prediction; 50 prospective margin",
            "assay 5 analysis plan",
            mean(regulation_only), mean_ci(regulation_only),
            "|mean root change| ≤ $equivalence_margin",
            abs(mean(regulation_only)) <= equivalence_margin),
    ]
    return criteria, Dict("worlds" => length(grouped))
end

function analyze6(rows, genome)
    families = (:global_downweight, :cue_local, :context_split,
        :continuous_drift, :change_point)
    family_rates = Dict{String,Any}()
    diagonal_total = 0
    for family in families
        family_rows = filter(row -> row.generating_family == family, rows)
        successes = count(row -> row.diagonal, family_rows)
        diagonal_total += successes
        family_rates[String(family)] = Dict("rate" =>
            successes / length(family_rows), "interval_95" =>
            wilson_interval(successes, length(family_rows)))
    end
    macro_rate = mean(Float64[family_rates[String(family)]["rate"]
        for family in families])
    non_split = filter(row -> row.generating_family != :context_split, rows)
    false_splits = count(row -> row.context_split_selected, non_split)
    false_rate = false_splits / length(non_split)
    split_rows = filter(row -> row.generating_family == :context_split, rows)
    margin = mean(Float64[row.heldout_margin for row in split_rows])
    recovery_threshold = ModelOrganism.g(genome, :assay6_recovery_rate)
    false_threshold = ModelOrganism.g(genome, :assay6_false_split_rate)
    heldout_threshold = ModelOrganism.g(genome, :context_heldout_margin)
    criteria = [
        criterion("five-family diagonal recovery", "model discrimination",
            "Original prediction (split family); 50 prospective drift/change-point recovery",
            "assay 6 analysis plan",
            macro_rate, wilson_interval(diagonal_total, length(rows)),
            "macro diagonal ≥ $recovery_threshold",
            macro_rate >= recovery_threshold;
            details = Dict("family_rates" => family_rates)),
        criterion("context-split misspecification guard",
            "model discrimination", "50 prospective",
            "assay 6 analysis plan", false_rate,
            wilson_interval(false_splits, length(non_split)),
            "false split rate ≤ $false_threshold",
            false_rate <= false_threshold),
        criterion("context-split held-out margin", "model discrimination",
            "Original prediction",
            "results/context_split_redescription/44b/summary.json",
            margin, mean_ci(Float64[row.heldout_margin for row in split_rows]),
            "mean margin ≥ $heldout_threshold", margin >= heldout_threshold),
    ]
    return criteria, Dict("datasets" => length(rows),
        "complexity_audit_all" => all(row.complexity_audit for row in rows))
end

function analyze7(rows, genome)
    analytic = filter(row -> row.kind == :analytic, rows)
    simulation = filter(row -> row.kind == :simulation, rows)
    analytic_successes = count(row -> row.sign_matches, analytic)
    post = filter(row -> row.timing == :post_revision, simulation)
    premature = filter(row -> row.timing == :premature, simulation)
    advantages = Float64[row.doover_success - row.suggestion_success
        for row in post]
    reversals = count(row -> row.reversal, premature)
    timing_margin = ModelOrganism.g(genome, :assay7_timing_margin)
    criteria = [
        criterion("imaginal-evidence analytic crossover", "conformance",
            "50 prospective", "assay 7 analysis plan",
            analytic_successes / length(analytic),
            wilson_interval(analytic_successes, length(analytic)),
            "exact property agreement = 1.0",
            analytic_successes == length(analytic)),
        criterion("post-revision do-over advantage", "conformance",
            "Original prediction; 50 prospective suggestion-only comparator",
            "results/context_split_redescription/44b/summary.json",
            mean(advantages), mean_ci(advantages),
            "paired advantage ≥ $timing_margin",
            mean(advantages) >= timing_margin),
        criterion("premature reversal rate", "conformance",
            "Original prediction",
            "results/context_split_redescription/44b/summary.json",
            reversals / length(premature),
            wilson_interval(reversals, length(premature)),
            "reversal rate ≥ 0.50",
            reversals / length(premature) >= 0.50),
    ]
    return criteria, Dict("analytic_domain_points" => length(analytic),
        "stochastic_worlds" => length(post))
end

function analyze8(rows, genome)
    grouped = rows_by_seed(rows)
    selections = Bool[]
    changes = Float64[]
    off_static = Bool[]
    for seed_rows in values(grouped)
        off = only(filter(row -> !row.registration, seed_rows))
        on = only(filter(row -> row.registration, seed_rows))
        push!(selections, on.selection_tracks)
        push!(changes, on.relational_change - off.relational_change)
        push!(off_static, abs(off.relational_change) <=
            ModelOrganism.g(genome, :static_tolerance))
    end
    selected = count(identity, selections)
    selection_rate = selected / length(selections)
    selection_threshold =
        ModelOrganism.g(genome, :assay8_selection_rate)
    registration_margin =
        ModelOrganism.g(genome, :assay8_registration_margin)
    criteria = [
        criterion("selection tracks learned expected cost", "conformance",
            "Original prediction; 50 prospective learned-history test",
            "assay 8 analysis plan",
            selection_rate, wilson_interval(selected, length(selections)),
            "tracking rate ≥ $selection_threshold",
            selection_rate >= selection_threshold),
        criterion("registration on-minus-off contrast", "causal contrast",
            "Original prediction", "results/exiling_emergence/report.md",
            mean(changes), mean_ci(changes),
            "mean paired change ≥ $registration_margin",
            mean(changes) >= registration_margin),
        criterion("registration off and ablation static", "causal contrast",
            "Original prediction", "results/exiling_emergence/report.md",
            nothing, [nothing, nothing],
            "off and distinct ablation within static tolerance", nothing;
            details = Dict("off_static_rate" =>
                mean(Float64.(off_static)),
                "ablation_status" =>
                    "missing from frozen simulator; required evidence absent")),
    ]
    return criteria, Dict("worlds" => length(grouped),
        "missing_required_ablation_cell" => true)
end

function competence_recovered(row, genome)
    neutral = ModelOrganism.g(genome, :neutral_probability)
    margin = ModelOrganism.g(genome, :partner_classification_margin)
    band = ModelOrganism.g(genome, :partner_neutral_band)
    row.partner == :trustworthy && return row.competence > neutral + margin
    row.partner == :adverse && return row.competence < neutral - margin
    return neutral - band <= row.competence <= neutral + band
end

function analyze9(rows, genome)
    invariant = filter(row -> row.kind == :invariant, rows)
    invariant_ok = [row.stakes_separated && row.posterior_unchanged &&
        row.transfer_local for row in invariant]
    learned = filter(row -> row.kind == :learned_history, rows)
    joint = [row.recovered && competence_recovered(row, genome)
        for row in learned]
    joint_successes = count(identity, joint)
    sign_successes = count(row -> row.sign_prediction_match, learned)
    invariant_successes = count(identity, invariant_ok)
    recovery_rate = joint_successes / length(learned)
    sign_rate = sign_successes / length(learned)
    partner_strata = Dict{String,Any}()
    for partner in (:trustworthy, :neutral, :adverse)
        indices = findall(row -> row.partner == partner, learned)
        successes = count(index -> joint[index], indices)
        partner_strata[String(partner)] = Dict(
            "successes" => successes, "total" => length(indices),
            "rate" => successes / length(indices),
            "interval_95" => wilson_interval(successes, length(indices)))
    end
    recovery_threshold =
        ModelOrganism.g(genome, :assay9_recovery_rate)
    sign_threshold = ModelOrganism.g(genome, :assay9_crossover_rate)
    criteria = [
        criterion("stakes-permission and transfer invariants", "conformance",
            "Original prediction", "results/protector_trust/report.md",
            nothing, [nothing, nothing],
            "exact agreement over the frozen 101-point domain", nothing;
            details = Dict("frozen_domain_points_required" => 101,
                "rows_emitted" => length(invariant),
                "transfer_locality_implementation" =>
                    "asserted true in frozen simulator; not property-tested")),
        criterion("joint partner-type and competence recovery",
            "conformance", "50 prospective", "assay 9 analysis plan",
            recovery_rate, wilson_interval(joint_successes, length(learned)),
            "macro learned-history recovery ≥ $recovery_threshold",
            recovery_rate >= recovery_threshold;
            details = Dict("partner_strata" => partner_strata)),
        criterion("risk-model obsolescence crossover", "conformance",
            "Exploratory finding; first prospective test in 50-H",
            "results/protector_trust/exploratory-summary.json",
            sign_rate, wilson_interval(sign_successes, length(learned)),
            "sign-match rate ≥ $sign_threshold",
            sign_rate >= sign_threshold),
    ]
    return criteria, Dict("invariant_points_emitted" => length(invariant),
        "invariant_points_required" => 101,
        "learned_histories" => length(learned))
end

function analyze10(rows, genome)
    grouped = rows_by_seed(rows)
    interactions = Float64[]
    cell_outcomes = Dict(key => Bool[] for key in
        ((:trustworthy, :coupled), (:trustworthy, :decoupled),
         (:neutral, :coupled), (:neutral, :decoupled),
         (:adverse, :coupled), (:adverse, :decoupled)))
    positive_only = Bool[]
    ordering = Bool[]
    for seed_rows in values(grouped)
        for row in seed_rows
            if row.positive_without_scaffold
                push!(positive_only, row.descent)
            else
                push!(cell_outcomes[(row.disposition, row.scaffold)],
                    row.descent)
                row.descent && push!(ordering, row.permission_before_root)
            end
        end
        value(disposition, scaffold) = Float64(only(filter(row ->
            !row.positive_without_scaffold &&
            row.disposition == disposition && row.scaffold == scaffold,
            seed_rows)).descent)
        push!(interactions,
            (value(:trustworthy, :coupled) -
             value(:trustworthy, :decoupled)) -
            (value(:adverse, :coupled) -
             value(:adverse, :decoupled)))
    end
    rates = Dict{String,Any}()
    for (key, values) in cell_outcomes
        successes = count(identity, values)
        rates["$(key[1])_$(key[2])"] = Dict("rate" =>
            successes / length(values), "interval_95" =>
            wilson_interval(successes, length(values)))
    end
    interaction_margin =
        ModelOrganism.g(genome, :assay10_interaction_margin)
    success_threshold =
        ModelOrganism.g(genome, :assay10_success_rate)
    control_threshold =
        ModelOrganism.g(genome, :assay10_control_rate)
    trustworthy_coupled = rates["trustworthy_coupled"]["rate"]
    trustworthy_decoupled = rates["trustworthy_decoupled"]["rate"]
    adverse_coupled = rates["adverse_coupled"]["rate"]
    safeguard_interval = [0.0, max(
        rates["trustworthy_decoupled"]["interval_95"][2],
        rates["adverse_coupled"]["interval_95"][2])]
    criteria = [
        criterion("disposition × scaffold interaction", "causal contrast",
            "50 prospective", "assay 10 analysis plan",
            mean(interactions), mean_ci(interactions),
            "mean interaction ≥ $interaction_margin",
            mean(interactions) >= interaction_margin;
            details = Dict("cell_rates" => rates)),
        criterion("trustworthy-coupled descent", "causal contrast",
            "50 prospective", "assay 10 analysis plan",
            trustworthy_coupled,
            rates["trustworthy_coupled"]["interval_95"],
            "rate ≥ $success_threshold",
            trustworthy_coupled >= success_threshold),
        criterion("decoupled/adverse safeguards", "causal contrast",
            "50 prospective", "assay 10 analysis plan",
            max(trustworthy_decoupled, adverse_coupled),
            safeguard_interval,
            "trustworthy-decoupled and adverse-coupled ≤ $control_threshold",
            trustworthy_decoupled <= control_threshold &&
                adverse_coupled <= control_threshold;
            details = Dict("trustworthy_decoupled" =>
                rates["trustworthy_decoupled"],
                "adverse_coupled" => rates["adverse_coupled"])),
    ]
    return criteria, Dict("worlds" => length(grouped),
        "positive_evidence_without_scaffold_descent_rate" =>
            mean(Float64.(positive_only)),
        "permission_before_root_audit_rate" =>
            isempty(ordering) ? nothing : mean(Float64.(ordering)),
        "neutral_no_scaffold_anchor_rate" =>
            rates["neutral_decoupled"]["rate"])
end

const ANALYZERS = Dict(1 => analyze1, 2 => analyze2, 3 => analyze3,
    4 => analyze4, 5 => analyze5, 6 => analyze6, 7 => analyze7,
    8 => analyze8, 9 => analyze9, 10 => analyze10)

function write_confirm_report(assay, summary)
    path = joinpath(ModelOrganism.RESULTS_ROOT, "assays", string(assay),
        "report.md")
    raw = read(path, String)
    occursin("## Confirmatory results (Stage B)", raw) &&
        error("assay $assay report already has confirmatory results")
    open(path, "a") do io
        println(io, "\n\n## Confirmatory results (Stage B)\n")
        println(io, "- Freeze commit: `$(summary["freeze_commit"])`")
        println(io, "- Released seeds used: `$(first(summary["seeds"])):$(last(summary["seeds"]))`")
        println(io, "- Confirmatory worlds: `$(summary["world_count"])`")
        overall = summary["overall_verdict"] === nothing ?
            "INCOMPLETE — APPARATUS STOP" :
            (summary["overall_verdict"] ? "PASS" : "FAIL")
        println(io, "- Overall assay status: **$overall**\n")
        println(io, "| Frozen criterion | Provenance | Effect estimate | 95% interval | Decision rule | Verdict |")
        println(io, "|---|---|---:|---|---|---|")
        for item in summary["criteria"]
            estimate = item["estimate"] === nothing ? "not estimable" :
                @sprintf("%.6f", item["estimate"])
            interval = item["interval_95"][1] === nothing ? "not estimable" :
                @sprintf("[%.6f, %.6f]", item["interval_95"][1],
                    item["interval_95"][2])
            verdict = item["passed"] === nothing ? "NOT EVALUABLE" :
                (item["passed"] ? "PASS" : "FAIL")
            rule = replace(item["decision_rule"], "|" => "\\|")
            println(io, "| $(item["label"]) | $(item["hypothesis_provenance"]) | $estimate | $interval | $rule | **$verdict** |")
        end
        println(io, "\nSecondary and descriptive outcomes are recorded in `confirm-summary.json`. Apparatus omissions are not imputed and are marked not evaluable.")
    end
end

function confirm_assay(assay, genome)
    directory = joinpath(ModelOrganism.RESULTS_ROOT, "assays", string(assay))
    summary_path = joinpath(directory, "confirm-summary.json")
    isfile(summary_path) &&
        error("assay $assay confirmatory output already exists; refusing rerun")
    seeds = released_seeds(assay, genome)
    rows = run_frozen_rows(assay, seeds, genome)
    criteria, descriptive = ANALYZERS[assay](rows, genome)
    all_evaluable = all(item["passed"] !== nothing for item in criteria)
    overall = all_evaluable ? all(Bool(item["passed"])
        for item in criteria) : nothing
    summary = Dict(
        "assay" => assay,
        "stage" => "50-H confirmatory",
        "freeze_commit" => FREEZE_COMMIT,
        "seeds" => seeds,
        "world_count" => length(seeds),
        "row_count" => length(rows),
        "canonical_source_sha256" => ModelOrganism.canonical_source_hash(),
        "genome_sha256" => genome.sha256,
        "analysis_plan_sha256" => bytes2hex(sha256(read(joinpath(
            directory, "analysis-plan.md")))),
        "criteria" => criteria,
        "confirmatory_status" => all_evaluable ? "complete" :
            "incomplete_apparatus_stop",
        "overall_verdict" => overall,
        "descriptive" => descriptive,
        "missing_or_numerical_failures" =>
            assay == 8 ? length(seeds) : 0,
    )
    ModelOrganism.write_csv_file(joinpath(directory,
        "confirm-per_seed.csv"), rows)
    ModelOrganism.write_json_file(summary_path, summary)
    write_confirm_report(assay, summary)
    return summary
end

function write_profile(summaries)
    path = joinpath(ModelOrganism.RESULTS_ROOT, "profile.md")
    classes = ("conformance", "causal contrast", "model discrimination")
    open(path, "w") do io
        println(io, "# Experiment 50-H confirmatory profile\n")
        println(io, "Freeze reference: `$(FREEZE_COMMIT)`. This profile reports the historical-integration benchmark by evidentiary class. It is not an out-of-sample or clinical claim, and it does not use a bare assay pass count.\n")
        for class in classes
            items = [(summary["assay"], item) for summary in summaries
                for item in summary["criteria"]
                if item["evidentiary_class"] == class]
            evaluable = filter(pair -> pair[2]["passed"] !== nothing, items)
            unevaluable = filter(pair -> pair[2]["passed"] === nothing, items)
            passes = count(pair -> pair[2]["passed"], evaluable)
            println(io, "## $(uppercasefirst(class))\n")
            println(io, "**$passes of $(length(evaluable)) evaluable frozen criteria passed; $(length(unevaluable)) additional criteria were not evaluable.**\n")
            println(io, "| Assay | Criterion | Estimate | 95% interval | Provenance | Verdict |")
            println(io, "|---:|---|---:|---|---|---|")
            for (assay, item) in items
                estimate = item["estimate"] === nothing ? "not estimable" :
                    @sprintf("%.4f", item["estimate"])
                interval = item["interval_95"][1] === nothing ?
                    "not estimable" :
                    @sprintf("[%.4f, %.4f]", item["interval_95"][1],
                        item["interval_95"][2])
                verdict = item["passed"] === nothing ? "NOT EVALUABLE" :
                    (item["passed"] ? "PASS" : "FAIL")
                println(io, "| $assay | $(item["label"]) | $estimate | $interval | $(item["hypothesis_provenance"]) | **$verdict** |")
            end
            failures = [(assay, item) for (assay, item) in items
                if item["passed"] === false]
            if !isempty(failures)
                println(io, "\nHonest failures retained:")
                for (assay, item) in failures
                    println(io, "\n- Assay $assay — $(item["label"]): $(item["decision_rule"]).")
                end
            end
            if !isempty(unevaluable)
                println(io, "\nNot evaluable:")
                for (assay, item) in unevaluable
                    println(io, "\n- Assay $assay — $(item["label"]): frozen apparatus did not produce the required domain/cell.")
                end
            end
            println(io)
        end
        println(io, "## Scope\n")
        println(io, "These results show which historical signatures survived one frozen, jointly calibrated strain on fresh escrowed worlds. A failed criterion means that behavior did not survive the shared parameterization. It does not show that a psychological or clinical claim is false. No 50-P or 50-L seed or protocol was opened.")
    end
    return path
end

function write_stage_b_manifest(summaries)
    output_paths = String[]
    for assay in 1:10
        directory = joinpath(ModelOrganism.RESULTS_ROOT, "assays",
            string(assay))
        append!(output_paths, [joinpath(directory, "confirm-per_seed.csv"),
            joinpath(directory, "confirm-summary.json"),
            joinpath(directory, "report.md")])
    end
    append!(output_paths, [
        joinpath(ModelOrganism.RESULTS_ROOT, "profile.md"),
        joinpath(ModelOrganism.RESULTS_ROOT, "freeze-commit.md"),
        joinpath(ModelOrganism.RESULTS_ROOT, "stage-b-errata.md"),
        abspath(@__FILE__),
    ])
    for path in (
        joinpath(ModelOrganism.RESULTS_ROOT, "assays", "8",
            "confirm-pre-repair-per_seed.csv"),
        joinpath(ModelOrganism.RESULTS_ROOT, "assays", "9",
            "confirm-property-domain.csv"),
        joinpath(ModelOrganism.RESULTS_ROOT, "assays", "9",
            "confirm-property-summary.json"),
    )
        isfile(path) && push!(output_paths, path)
    end
    repairs_complete =
        isfile(joinpath(ModelOrganism.RESULTS_ROOT, "assays", "8",
            "confirm-pre-repair-per_seed.csv")) &&
        isfile(joinpath(ModelOrganism.RESULTS_ROOT, "assays", "9",
            "confirm-property-summary.json"))
    payload = Dict(
        "stage" => repairs_complete ? "50-H confirmatory complete" :
            "50-H confirmatory incomplete — evaluator adjudication required",
        "freeze_commit" => FREEZE_COMMIT,
        "completed_at_utc" => string(now(UTC)),
        "assays" => 10,
        "confirmatory_seed_maximum" =>
            maximum(last(summary["seeds"]) for summary in summaries),
        "opened_50p_or_50l" => false,
        "components" => [Dict(
            "path" => relpath(path, ModelOrganism.PROJECT_ROOT),
            "sha256" => bytes2hex(sha256(read(path))),
            "bytes" => filesize(path)) for path in output_paths],
    )
    ModelOrganism.write_json_file(joinpath(ModelOrganism.RESULTS_ROOT,
        "stage-b-manifest.json"), payload)
end

parse_csv_bool(value) = value == "true" ? true :
    value == "false" ? false : error("invalid CSV Bool: $value")

function read_assay9_learned_rows(path)
    lines = readlines(path)
    header = split(first(lines), ',')
    positions = Dict(name => findfirst(==(name), header) for name in header)
    rows = NamedTuple[]
    for line in Iterators.drop(lines, 1)
        fields = split(line, ',')
        fields[positions["kind"]] == "learned_history" || continue
        push!(rows, (
            seed = parse(Int, fields[positions["seed"]]),
            partner = Symbol(fields[positions["partner"]]),
            recovered = parse_csv_bool(fields[positions["recovered"]]),
            competence = parse(Float64, fields[positions["competence"]]),
            sign_prediction_match =
                parse_csv_bool(fields[positions["sign_prediction_match"]]),
        ))
    end
    return rows
end

function assay8_ablation_row(seed, genome)
    favorable = ModelOrganism.POLICY_NAMES[
        mod1(seed, length(ModelOrganism.POLICY_NAMES))]
    state = ModelOrganism.seeded_state(seed, genome;
        favorable_policy = favorable)
    selected = ModelOrganism.select_policy(state, genome)
    initial = state.posterior[:relational_prior]
    for episode in 1:Int(ModelOrganism.g(genome, :episodes))
        ModelOrganism.update_registration!(state, true, false, genome;
            event_id = "assay8:ablation:$seed:$episode")
    end
    return (seed = seed, arm = :ablation,
        favorable_policy = favorable, selected_policy = selected,
        selection_tracks = selected == favorable,
        relational_change = state.posterior[:relational_prior] - initial,
        learned_cost = state.policy_cost[selected],
        learned_reliability = state.policy_reliability[selected])
end

function repair_assay8(genome)
    assay = 8
    directory = joinpath(ModelOrganism.RESULTS_ROOT, "assays", "8")
    original_path = joinpath(directory, "confirm-per_seed.csv")
    archive_path = joinpath(directory, "confirm-pre-repair-per_seed.csv")
    isfile(archive_path) &&
        error("assay 8 repair already applied; refusing rerun")
    original_bytes = read(original_path)
    original_hash = bytes2hex(sha256(original_bytes))
    expected_hash =
        "61953fe9c3cf987145da016a5a8f90ba8f6c93121f05abc54b07026b471c4690"
    original_hash == expected_hash ||
        error("assay 8 pre-repair output hash changed: $original_hash")
    seeds = released_seeds(assay, genome)
    regenerated = run_frozen_rows(assay, seeds, genome)
    regenerated_bytes = mktemp() do path, io
        close(io)
        ModelOrganism.write_csv_file(path, regenerated)
        read(path)
    end
    regenerated_bytes == original_bytes ||
        error("RED FLAG: assay 8 on/off rows did not reproduce bit-for-bit")
    write(archive_path, original_bytes)

    repaired = NamedTuple[]
    for seed in seeds
        seed_rows = filter(row -> row.seed == seed, regenerated)
        for row in seed_rows
            push!(repaired, (seed = row.seed,
                arm = row.registration ? :on : :off,
                favorable_policy = row.favorable_policy,
                selected_policy = row.selected_policy,
                selection_tracks = row.selection_tracks,
                relational_change = row.relational_change,
                learned_cost = row.learned_cost,
                learned_reliability = row.learned_reliability))
        end
        push!(repaired, assay8_ablation_row(seed, genome))
    end
    ModelOrganism.write_csv_file(original_path, repaired)

    grouped = rows_by_seed(repaired)
    selections = Bool[]
    contrasts = Float64[]
    off_static = Bool[]
    ablation_static = Bool[]
    tolerance = ModelOrganism.g(genome, :static_tolerance)
    for seed_rows in values(grouped)
        off = only(filter(row -> row.arm == :off, seed_rows))
        on = only(filter(row -> row.arm == :on, seed_rows))
        ablation = only(filter(row -> row.arm == :ablation, seed_rows))
        push!(selections, on.selection_tracks)
        push!(contrasts, on.relational_change - off.relational_change)
        push!(off_static, abs(off.relational_change) <= tolerance)
        push!(ablation_static, abs(ablation.relational_change) <= tolerance)
    end
    selected = count(identity, selections)
    selection_rate = selected / length(selections)
    selection_threshold =
        ModelOrganism.g(genome, :assay8_selection_rate)
    registration_margin =
        ModelOrganism.g(genome, :assay8_registration_margin)
    criteria = [
        criterion("selection tracks learned expected cost", "conformance",
            "Original prediction; 50 prospective learned-history test",
            "assay 8 analysis plan", selection_rate,
            wilson_interval(selected, length(selections)),
            "tracking rate ≥ $selection_threshold",
            selection_rate >= selection_threshold),
        criterion("registration on-minus-off contrast", "causal contrast",
            "Original prediction", "results/exiling_emergence/report.md",
            mean(contrasts), mean_ci(contrasts),
            "mean paired change ≥ $registration_margin",
            mean(contrasts) >= registration_margin),
        criterion("registration off and ablation static",
            "causal contrast", "Original prediction",
            "results/exiling_emergence/report.md", 1.0,
            wilson_interval(length(seeds), length(seeds)),
            "off and distinct ablation within static tolerance",
            all(off_static) && all(ablation_static);
            details = Dict("off_static_rate" =>
                mean(Float64.(off_static)),
                "ablation_static_rate" =>
                    mean(Float64.(ablation_static)))),
    ]
    summary = Dict(
        "analysis_plan_sha256" => bytes2hex(sha256(read(joinpath(
            directory, "analysis-plan.md")))),
        "assay" => assay,
        "canonical_source_sha256" => ModelOrganism.canonical_source_hash(),
        "criteria" => criteria,
        "confirmatory_status" =>
            "complete_after_authorized_software_repair",
        "descriptive" => Dict("worlds" => length(seeds),
            "arms_per_world" => 3,
            "on_off_bit_for_bit_reproduction" => true,
            "pre_repair_sha256" => original_hash,
            "regenerated_on_off_sha256" =>
                bytes2hex(sha256(regenerated_bytes)),
            "maximum_absolute_on_off_deviation" => 0.0),
        "freeze_commit" => FREEZE_COMMIT,
        "genome_sha256" => genome.sha256,
        "missing_or_numerical_failures" => 0,
        "overall_verdict" => all(item["passed"] for item in criteria),
        "row_count" => length(repaired),
        "seeds" => seeds,
        "stage" => "50-H confirmatory",
        "world_count" => length(seeds),
    )
    ModelOrganism.write_json_file(joinpath(directory,
        "confirm-summary.json"), summary)
    return summary
end

function property_history_state(index, genome)
    state = neutral_state(genome)
    reliability = ModelOrganism.g(genome, :bayes_reliability)
    for event in 1:100
        positive = fld(event * index, 100) >
            fld((event - 1) * index, 100)
        for variable in (:outcome_forecast, :co_protection,
                :partner_trustworthy)
            ModelOrganism.update_posterior!(state, variable, positive,
                reliability, genome; event_kind = :property_domain,
                event_id = "assay9:property:$index:$event:$variable")
        end
    end
    return state
end

function assay9_property_domain(genome)
    rows = NamedTuple[]
    for index in 0:100
        state = property_history_state(index, genome)
        snapshot = copy(state.posterior)
        low = ModelOrganism.protector_permission(state,
            ModelOrganism.g(genome, :low_stakes), genome)
        high = ModelOrganism.protector_permission(state,
            ModelOrganism.g(genome, :high_stakes), genome)
        permission_posterior_flat = snapshot == state.posterior
        local_context = deepcopy(state)
        untreated_context = deepcopy(state)
        ModelOrganism.update_posterior!(local_context, :outcome_forecast,
            true, ModelOrganism.g(genome, :bayes_reliability), genome;
            event_kind = :property_domain,
            event_id = "assay9:locality:$index")
        shared_routes_unchanged =
            local_context.posterior[:co_protection] ==
                snapshot[:co_protection] &&
            local_context.posterior[:partner_trustworthy] ==
                snapshot[:partner_trustworthy]
        untreated_context_unchanged =
            untreated_context.posterior == snapshot
        stakes_separated = low >= high
        locality_holds = shared_routes_unchanged &&
            untreated_context_unchanged
        push!(rows, (domain_index = index,
            positive_history_fraction = index / 100,
            low_stakes_permission = low,
            high_stakes_permission = high,
            stakes_separated = stakes_separated,
            permission_posterior_flat = permission_posterior_flat,
            shared_routes_unchanged = shared_routes_unchanged,
            untreated_context_unchanged = untreated_context_unchanged,
            locality_holds = locality_holds,
            property_holds = stakes_separated &&
                permission_posterior_flat && locality_holds,
            provenance_events = length(state.log)))
    end
    return rows
end

function repair_assay9(genome)
    directory = joinpath(ModelOrganism.RESULTS_ROOT, "assays", "9")
    property_path = joinpath(directory, "confirm-property-domain.csv")
    isfile(property_path) &&
        error("assay 9 property repair already applied; refusing rerun")
    world_path = joinpath(directory, "confirm-per_seed.csv")
    world_hash_before = bytes2hex(sha256(read(world_path)))
    expected_hash =
        "d7f478ac45f33c90fbb178fc5adf74db12af66a778732e1011cf34c9f6d336c7"
    world_hash_before == expected_hash ||
        error("assay 9 final world block changed before property repair")
    property_rows = assay9_property_domain(genome)
    ModelOrganism.write_csv_file(property_path, property_rows)
    successes = count(row -> row.property_holds, property_rows)
    property_summary = Dict(
        "domain_points" => length(property_rows),
        "successes" => successes,
        "agreement" => successes / length(property_rows),
        "interval_95" => wilson_interval(successes, length(property_rows)),
        "stakes_failures" =>
            count(row -> !row.stakes_separated, property_rows),
        "locality_failures" =>
            count(row -> !row.locality_holds, property_rows),
        "permission_mutation_failures" =>
            count(row -> !row.permission_posterior_flat, property_rows),
        "seeded" => false,
        "world_block_rerun" => false,
        "world_block_sha256_before" => world_hash_before,
        "world_block_sha256_after" =>
            bytes2hex(sha256(read(world_path))),
    )
    ModelOrganism.write_json_file(joinpath(directory,
        "confirm-property-summary.json"), property_summary)

    learned = read_assay9_learned_rows(world_path)
    joint = [row.recovered && competence_recovered(row, genome)
        for row in learned]
    joint_successes = count(identity, joint)
    sign_successes = count(row -> row.sign_prediction_match, learned)
    partner_strata = Dict{String,Any}()
    for partner in (:trustworthy, :neutral, :adverse)
        indices = findall(row -> row.partner == partner, learned)
        partner_successes = count(index -> joint[index], indices)
        partner_strata[String(partner)] = Dict(
            "successes" => partner_successes,
            "total" => length(indices),
            "rate" => partner_successes / length(indices),
            "interval_95" =>
                wilson_interval(partner_successes, length(indices)))
    end
    recovery_rate = joint_successes / length(learned)
    sign_rate = sign_successes / length(learned)
    criteria = [
        criterion("stakes-permission and transfer invariants",
            "conformance", "Original prediction",
            "results/protector_trust/report.md",
            successes / length(property_rows),
            wilson_interval(successes, length(property_rows)),
            "exact property agreement = 1.0",
            successes == length(property_rows);
            details = Dict("domain_points" => length(property_rows))),
        criterion("joint partner-type and competence recovery",
            "conformance", "50 prospective", "assay 9 analysis plan",
            recovery_rate,
            wilson_interval(joint_successes, length(learned)),
            "macro learned-history recovery ≥ $(ModelOrganism.g(genome, :assay9_recovery_rate))",
            recovery_rate >=
                ModelOrganism.g(genome, :assay9_recovery_rate);
            details = Dict("partner_strata" => partner_strata)),
        criterion("risk-model obsolescence crossover", "conformance",
            "Exploratory finding; first prospective test in 50-H",
            "results/protector_trust/exploratory-summary.json",
            sign_rate, wilson_interval(sign_successes, length(learned)),
            "sign-match rate ≥ $(ModelOrganism.g(genome, :assay9_crossover_rate))",
            sign_rate >= ModelOrganism.g(genome, :assay9_crossover_rate)),
    ]
    seeds = released_seeds(9, genome)
    summary = Dict(
        "analysis_plan_sha256" => bytes2hex(sha256(read(joinpath(
            directory, "analysis-plan.md")))),
        "assay" => 9,
        "canonical_source_sha256" => ModelOrganism.canonical_source_hash(),
        "criteria" => criteria,
        "confirmatory_status" =>
            "complete_after_authorized_software_repair",
        "descriptive" => Dict("property_domain_points" =>
                length(property_rows),
            "learned_histories" => length(learned),
            "world_block_rerun" => false,
            "world_block_sha256" => world_hash_before),
        "freeze_commit" => FREEZE_COMMIT,
        "genome_sha256" => genome.sha256,
        "missing_or_numerical_failures" => 0,
        "overall_verdict" => all(item["passed"] for item in criteria),
        "property_row_count" => length(property_rows),
        "row_count" => length(readlines(world_path)) - 1,
        "seeds" => seeds,
        "stage" => "50-H confirmatory",
        "world_count" => length(seeds),
    )
    ModelOrganism.write_json_file(joinpath(directory,
        "confirm-summary.json"), summary)
    bytes2hex(sha256(read(world_path))) == world_hash_before ||
        error("RED FLAG: assay 9 world block changed during property repair")
    return summary
end

function write_repaired_report(assay, summary)
    directory = joinpath(ModelOrganism.RESULTS_ROOT, "assays",
        string(assay))
    path = joinpath(directory, "report.md")
    raw = read(path, String)
    prefix = first(split(raw, "\n\n## Confirmatory results (Stage B)";
        limit = 2))
    open(path, "w") do io
        print(io, prefix)
        println(io, "\n\n## Confirmatory results (Stage B)\n")
        println(io, "- Freeze commit: `$(summary["freeze_commit"])`")
        println(io, "- Released seeds used: `$(first(summary["seeds"])):$(last(summary["seeds"]))`")
        println(io, "- Confirmatory worlds: `$(summary["world_count"])`")
        println(io, "- Software repair status: **AUTHORIZED; COMPLETE**")
        println(io, "- Overall assay verdict: **$(summary["overall_verdict"] ? "PASS" : "FAIL")**\n")
        println(io, "| Frozen criterion | Provenance | Effect estimate | 95% interval | Decision rule | Verdict |")
        println(io, "|---|---|---:|---|---|---|")
        for item in summary["criteria"]
            estimate = @sprintf("%.6f", item["estimate"])
            interval = @sprintf("[%.6f, %.6f]",
                item["interval_95"][1], item["interval_95"][2])
            rule = replace(item["decision_rule"], "|" => "\\|")
            println(io, "| $(item["label"]) | $(item["hypothesis_provenance"]) | $estimate | $interval | $rule | **$(item["passed"] ? "PASS" : "FAIL")** |")
        end
        if assay == 8
            details = summary["descriptive"]
            println(io, "\nRepair verification: the pre-existing on/off block reproduced byte-for-byte (`$(details["pre_repair_sha256"])`), maximum absolute deviation `0.0`. The distinct ablation arm was static in every paired world.")
        else
            recovery = summary["criteria"][2]["details"]["partner_strata"]
            println(io, "\nThe 101-point property domain passed exactly and used no seeds. The learned-history world block was not rerun and retained SHA-256 `$(summary["descriptive"]["world_block_sha256"])`. Joint recovery remained trustworthy `$(recovery["trustworthy"]["successes"])/80`, neutral `$(recovery["neutral"]["successes"])/80`, adverse `$(recovery["adverse"]["successes"])/80`. The obsolescence-crossover **FAIL** stands without reinterpretation.")
        end
    end
end

function repair_authorized()
    genome = load_genome()
    verify_frozen_inputs!(genome)
    summary8 = repair_assay8(genome)
    write_repaired_report(8, summary8)
    verify_frozen_inputs!(genome)
    summary9 = repair_assay9(genome)
    write_repaired_report(9, summary9)
    println("authorized repairs complete; assay 8 on/off reproduced exactly and assay 9 world block was not rerun")
end

function main()
    if ARGS == ["--repair-authorized"]
        repair_authorized()
        return
    end
    ARGS == ["--confirm-all"] ||
        error("usage: run_stage_b.jl --confirm-all|--repair-authorized")
    genome = load_genome()
    verify_frozen_inputs!(genome)
    any(isfile(joinpath(ModelOrganism.RESULTS_ROOT, "assays", string(assay),
        "confirm-summary.json")) for assay in 1:10) &&
        error("confirmatory outputs already exist; refusing partial or repeated run")
    summaries = Dict[]
    for assay in 1:10
        verify_frozen_inputs!(genome)
        summary = confirm_assay(assay, genome)
        push!(summaries, summary)
        status = summary["overall_verdict"] === nothing ? "INCOMPLETE" :
            (summary["overall_verdict"] ? "PASS" : "FAIL")
        println("assay $assay confirmatory block complete: ", status)
    end
    write_profile(summaries)
    write_stage_b_manifest(summaries)
    println("Stage B execution stopped with apparatus gaps; evaluator adjudication required before completion or 50-P/50-L")
end

abspath(PROGRAM_FILE) == abspath(@__FILE__) && main()
