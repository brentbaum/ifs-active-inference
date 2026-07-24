using Pkg
using Dates
using Printf
using Statistics

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(project_dir, "src", "IFSBundleInquiry.jl"))
include(joinpath(project_dir, "src", "ContextSplitRedescription.jl"))
using .ContextSplitRedescription

function csv_cell(value)
    text = value isa AbstractFloat ? @sprintf("%.12g", value) : string(value)
    occursin(r"[\",\n]", text) || return text
    return "\"" * replace(text, "\"" => "\"\"") * "\""
end

function write_csv(path, rows)
    isempty(rows) && error("refusing to write empty CSV")
    fields = collect(keys(first(rows)))
    open(path, "w") do io
        println(io, join(string.(fields), ","))
        for row in rows
            println(io, join((csv_cell(getfield(row, field))
                for field in fields), ","))
        end
    end
end

json_escape(value) = replace(string(value), "\\" => "\\\\",
    "\"" => "\\\"", "\n" => "\\n")

function write_json_value(io, value; indent = 0)
    pad = " "^indent
    if value isa NamedTuple
        println(io, "{")
        pairs_list = collect(pairs(value))
        for (index, (key, item)) in enumerate(pairs_list)
            print(io, " "^(indent + 2), "\"", json_escape(key), "\": ")
            write_json_value(io, item; indent = indent + 2)
            index < length(pairs_list) && print(io, ",")
            println(io)
        end
        print(io, pad, "}")
    elseif value isa AbstractDict
        write_json_value(io, (; (Symbol(key) => item
            for (key, item) in value)...); indent = indent)
    elseif value isa AbstractVector
        print(io, "[")
        for (index, item) in enumerate(value)
            write_json_value(io, item; indent = indent)
            index < length(value) && print(io, ", ")
        end
        print(io, "]")
    elseif value isa Bool
        print(io, value ? "true" : "false")
    elseif value === nothing
        print(io, "null")
    elseif value isa Number
        print(io, isfinite(value) ? value : "\"$(value)\"")
    else
        print(io, "\"", json_escape(value), "\"")
    end
end

function write_json(path, value)
    open(path, "w") do io
        write_json_value(io, value)
        println(io)
    end
end

function parse_existing_csv(path)
    !isfile(path) && return NamedTuple[]
    lines = readlines(path)
    length(lines) <= 1 && return NamedTuple[]
    # The runner only needs to preserve an earlier pilot. Pilot rows contain no
    # commas in string fields, so this intentionally small reader is sufficient.
    headers = Symbol.(split(first(lines), ","))
    rows = NamedTuple[]
    for line in lines[2:end]
        values = split(line, ",")
        parsed = Any[]
        for (header, value) in zip(headers, values)
            if header in (:stage, :structured_selected, :null_selected,
                    :organization_register, :carrier_register)
                push!(parsed, value)
            elseif header in (:structured_split_selected, :null_split_selected,
                    :premature_failed, :premature_reversed)
                push!(parsed, value == "true")
            elseif header == :seed || endswith(String(header), "_time")
                push!(parsed, parse(Int, value))
            else
                push!(parsed, parse(Float64, value))
            end
        end
        push!(rows, NamedTuple{Tuple(headers)}(Tuple(parsed)))
    end
    return rows
end

function write_magic_numbers(path, config)
    open(path, "w") do io
        println(io, "# Magic numbers — Experiment 44")
        println(io)
        println(io, "All authored numeric constants in `ContextSplitConfig` are listed below.")
        println(io, "Algorithmic tolerances are identified separately.")
        println(io)
        println(io, "| Constant | Value | Rationale |")
        println(io, "|---|---:|---|")
        for (name, value, rationale) in magic_numbers(config)
            println(io, "| `", name, "` | `", value, "` | ", rationale, " |")
        end
        extras = [
            ("pilot_seeds", "174401:174410", "Ten-world pilot namespace."),
            ("confirm_seeds", "174601:174620", "Fresh, disjoint twenty-world namespace after the held-out scale audit."),
            ("contexts", "-1, +1", "The two latent states `then` and `now`."),
            ("context_emission_means", "-1.0, +1.0", "Noisy marker likelihood; labels are never observed."),
            ("context_initial_probability", "0.5", "Symmetric state prior."),
            ("context_fit_initial_stay", "0.75", "Neutral persistent initialization, replaced by inference."),
            ("context_em_iterations", "12", "Fixed deterministic coordinate-ascent budget."),
            ("transition_newton_steps", "8", "Fixed deterministic inner optimization budget."),
            ("cue_base", "-0.34, -0.11, 0.13, 0.32", "Predeclared four-bundle marginal offsets."),
            ("root_signal_generator", "0.55 + 0.28*c + Normal(0,0.55)", "Shared-root observation available to every class."),
            ("global_precision_grid", "[-2,2], 81 points", "One active global down-weight coordinate and its deterministic optimizer."),
            ("root_bundle_pattern", "1.00, 0.82, 0.65, 0.92", "Corrective four-element bundle means shared by revision arms."),
            ("root_contact_mean", "0.90", "Experiment-43-style supportive contact mean."),
            ("witnessing_field", "1.00, 0.92, 0.78, 0.96; contact 0.90", "Part active with broad precision field."),
            ("open_information_field", "0.92, 1.00, 0.84, 0.93; contact 0.78", "Broad informational comparison."),
            ("regulation_field", "0.13 x4; contact 0.12", "Regulation without a broad evidence route."),
            ("narrowed_field", "0.72, 0.04, 0.04, 0.04; contact 0.10", "Part-dominant narrow contact."),
            ("fixed_context_field", "0.22 x4; contact 0.16", "Matched-exposure single-belief stress readout."),
            ("reversed_contact_field", "0.18, 0.16, 0.12, 0.15; contact -0.05", "Sign-reversed root/contact likelihood control."),
            ("root_likelihood_means", "-1.0, +1.0", "Common identity-root hypotheses."),
            ("doover_initial_then_endings", "5", "Frozen catastrophic episode evidence before present observations."),
            ("doover_jitter", "0.03", "Small fractional-count noise preventing exact duplicate worlds."),
            ("premature_session", "1", "Do-over is deliberately applied before posterior revision begins."),
            ("criterion_selection_rates", "0.80 structured; 0.20 null", "Equivalent to §3.6 counts 16/20 and 4/20."),
            ("criterion_heldout_margin", "0.05", "Frozen §3.6 log-predictive margin."),
            ("criterion_pair_tolerance", "0.12", "Pilot-frozen operational meaning of approximately equal."),
            ("criterion_ordering_gap", "0.30", "Pilot-frozen operational meaning of much greater."),
            ("criterion_doover_shortening", "0.20", "Frozen §3.6 time-to-reduction improvement."),
            ("seed_namespace_offsets", "100000,200000,300000,400000,500000,600000", "Prevent streams for cells and measures from sharing random draws."),
        ]
        for (name, value, rationale) in extras
            println(io, "| `", name, "` | `", value, "` | ", rationale, " |")
        end
        println(io)
        println(io, "Numerical guards `1e-6`, `1e-10`, `1e-12`, and `1e-300` prevent")
        println(io, "singular curvature, division, logarithms, and inactive columns; they do not")
        println(io, "define a scientific result. The eight Lanczos coefficients implement the")
        println(io, "standard log-gamma approximation used only for beta-Bernoulli evidence.")
        println(io, "The provisional criteria (`16/20`, `4/20`, `0.05`, `20%`, and")
        println(io, "`16/20`) come from §3.6 of the round specification, not from the model.")
    end
end

function report_text(pilot_rows, confirm_rows, config)
    pilot_summary = summarize_rows(pilot_rows)
    pilot_verdicts = length(pilot_rows) == 10 ? criteria_verdicts(pilot_rows) : nothing
    confirm_complete = length(confirm_rows) == 20
    confirmation_summary = confirm_complete ? summarize_rows(confirm_rows) : nothing
    confirmation_verdicts = confirm_complete ? criteria_verdicts(confirm_rows) : nothing
    audit = complexity_audit(config)
    io = IOBuffer()
    println(io, "# Experiment 44 — Context-split redescription, revision derived")
    println(io)
    println(io, "## Design")
    println(io)
    println(io, "Three model classes receive identical observations and compete by an")
    println(io, "evidence lower bound: expected Gaussian log likelihood minus posterior–prior")
    println(io, "KL complexity. `global_downweight` uses one cue belief plus smooth global")
    println(io, "change; `cue_local` relearns cue-specific trajectories; `context_split`")
    println(io, "infers `c ∈ {then, now}` with a learned symmetric transition prior and")
    println(io, "indexes the four bundle parameters by that context. Its nine regression")
    println(io, "coordinates plus one transition coordinate equal the ten active coordinates")
    println(io, "in each comparator.")
    println(io)
    println(io, "The witnessing construction reuses Experiment 43's four-element bundle,")
    println(io, "precision-field weighting, and separate interpersonal contact observation.")
    println(io, "The identity root posterior starts frozen and changes only by accumulated")
    println(io, "observation likelihood ratios. No repeated-contact or arm-specific root update")
    println(io, "exists. Do-over packets are marked internally generated by weight `",
        config.imaginal_weight, "` and add no external world observation.")
    println(io)
    println(io, "## Register guards")
    println(io)
    println(io, "- **Organization:** the four-element bundle, its couplings, its precisions,")
    println(io, "  and its field profile. This exact string is recorded per seed.")
    println(io, "- **Carrier:** an independently parameterized substrate. No carrier variable")
    println(io, "  exists in Experiment 44, and the per-seed record says so.")
    println(io, "- `configural` is used only statistically; `relational` is reserved for the")
    println(io, "  interpersonal contact observation. Exile contact is called witnessing.")
    println(io)
    println(io, "## Controls")
    println(io)
    println(io, "Every model sees the same training and held-out behavior, cue identities,")
    println(io, "context marker, root signal, and budgets. `global_downweight` is the")
    println(io, "matched-exposure single-context comparator; the additional fixed-context")
    println(io, "root readout keeps the evidence count fixed while narrowing its field. The")
    println(io, "reversed-graph-style control reverses the contact/root likelihood while")
    println(io, "retaining the bundle marginals. The essential")
    println(io, "selectivity worlds retain identical marginals and context-marker statistics")
    println(io, "but generate behavior without true context structure.")
    println(io)
    println(io, "## Complexity audit")
    println(io)
    println(io, "| Model | Regression | Transition | Precision | Active total | Prior entropy |")
    println(io, "|---|---:|---:|---:|---:|---:|")
    for model in (:global_downweight, :cue_local, :context_split)
        entry = getfield(audit, model)
        println(io, "| `", model, "` | ", entry.regression_parameters, " | ",
            entry.transition_parameters, " | ", entry.precision_parameters,
            " | ", entry.active_parameters, " | ",
            @sprintf("%.6f", entry.prior_entropy), " nats |")
    end
    println(io)
    println(io, "All coordinates have independent `N(0, ",
        config.prior_variance, ")` priors. Parameter count and prior entropy")
    println(io, "therefore match exactly. The ELBO charges the learned transition posterior")
    println(io, "to the split model rather than treating context inference as free.")
    if confirm_complete
        println(io, "Mean confirmatory posterior complexities were `",
            @sprintf("%.3f", mean(row.global_complexity for row in confirm_rows)),
            "` nats (`global_downweight`), `",
            @sprintf("%.3f", mean(row.cue_local_complexity for row in confirm_rows)),
            "` (`cue_local`), and `",
            @sprintf("%.3f", mean(row.split_complexity for row in confirm_rows)),
            "` (`context_split`). Thus capacity and prior entropy are matched,")
        println(io, "while the data-dependent KL charge is allowed to differ and is explicitly paid.")
    end
    println(io)
    println(io, "## Pilot results (10 worlds)")
    println(io)
    println(io, "- Structured selection: ", pilot_summary.structured_split_selected, "/10.")
    println(io, "- No-structure split selection: ", pilot_summary.null_split_selected, "/10.")
    println(io, "- Mean held-out split margin: ",
        @sprintf("%.4f", pilot_summary.mean_structured_split_margin), ".")
    println(io, "- Mean root posteriors (witnessing/open/regulation/narrowed): ",
        join([@sprintf("%.3f", value) for value in (
            pilot_summary.mean_witnessing_final_root,
            pilot_summary.mean_open_final_root,
            pilot_summary.mean_regulation_final_root,
            pilot_summary.mean_narrowed_final_root)], " / "), ".")
    println(io, "- Mean post-revision do-over shortening: ",
        @sprintf("%.1f%%", 100 * pilot_summary.mean_doover_shortening),
        "; premature failures: ", pilot_summary.premature_failures, "/10.")
    println(io)
    println(io, "Pilot provisional verdicts: `", pilot_verdicts, "`.")
    println(io)
    println(io, "A preliminary implementation check on the same pilot seeds was invalidated")
    println(io, "before freeze for marginal-matching and model-allocation defects. It is")
    println(io, "retained verbatim in `attempt-ledger.md`; no confirmation seed was opened.")
    println(io, "A first confirmatory block (`174501:174520`) was later invalidated in full")
    println(io, "when audit found that held-out columns had not been transported with their")
    println(io, "training normalization scales. Its pre-invalidation outcomes and exact")
    println(io, "repair are also retained in the ledger. The replacement block below uses")
    println(io, "never-opened seeds.")
    println(io)
    println(io, "## Freeze decisions")
    println(io)
    println(io, "**Frozen after the ten pilot worlds and before any confirmation seed was")
    println(io, "opened.** The architecture, generator, authored constants, measures, and")
    println(io, "all four §3.6 thresholds were retained unchanged. No threshold moved at")
    println(io, "freeze. In particular, the held-out margin remains `0.05`; pilot scale did")
    println(io, "not justify replacing the specification's provisional value.")
    println(io)
    println(io, "Criterion 3 is operationalized in advance as: mean absolute within-pair")
    println(io, "difference ≤ `0.12` for both witnessing/open and regulation/narrowed, plus")
    println(io, "a high-pair minus low-pair posterior gap ≥ `0.30`. These numeric")
    println(io, "operational tolerances were authored before confirmation and are listed here")
    println(io, "rather than retrofitted after results.")
    println(io)
    println(io, "## Confirmatory results (20 fresh worlds)")
    println(io)
    if confirm_complete
        println(io, "Seeds `174601:174620` were disjoint from pilot seeds")
        println(io, "`174401:174410`.")
        println(io)
        println(io, "1. Context-split selection was ",
            confirmation_summary.structured_split_selected,
            "/20 in true-context worlds and ",
            confirmation_summary.null_split_selected,
            "/20 in no-structure worlds: **",
            confirmation_verdicts.criterion_1_selectivity ? "PASS" : "FAIL",
            "**.")
        println(io, "2. Mean held-out context-sensitive log-predictive margin was ",
            @sprintf("%.4f", confirmation_summary.mean_structured_split_margin),
            " against the better comparator (threshold `0.05`): **",
            confirmation_verdicts.criterion_2_heldout_margin ? "PASS" : "FAIL",
            "**.")
        println(io, "3. Mean final root posteriors (witnessing/open/regulation/narrowed)")
        println(io, "   were ", join([@sprintf("%.3f", value) for value in (
            confirmation_summary.mean_witnessing_final_root,
            confirmation_summary.mean_open_final_root,
            confirmation_summary.mean_regulation_final_root,
            confirmation_summary.mean_narrowed_final_root)], " / "),
            ". High-minus-low was ",
            @sprintf("%.3f", confirmation_verdicts.ordering_high_minus_low),
            ": **", confirmation_verdicts.criterion_3_derived_ordering ?
                "PASS" : "FAIL", "**.")
        println(io, "4. Mean post-revision shortening was ",
            @sprintf("%.1f%%", 100 * confirmation_summary.mean_doover_shortening),
            "; premature do-over failed in ",
            confirmation_summary.premature_failures, "/20 worlds and reduced")
        println(io, "   evidence reversed in ",
            confirmation_summary.premature_reversals, "/20: **",
            confirmation_verdicts.criterion_4_doover_timing ? "PASS" : "FAIL",
            "**.")
        println(io)
        println(io, "Overall frozen verdict: **",
            confirmation_verdicts.overall ? "SUPPORT" : "FAILED/MIXED", "**.")
        println(io)
        println(io, "The controls sharpen the failure. The essential selectivity control behaved")
        println(io, "correctly: split selection was `",
            confirmation_summary.null_split_selected,
            "/20` when the context marker and behavioral context effect were marginally")
        println(io, "preserved but their association was shuffled. However, the matched")
        println(io, "fixed-context and reversed-contact/root controls both ended with mean root")
        println(io, "posterior approximately `",
            @sprintf("%.3f", mean(row.fixed_context_final_root for row in confirm_rows)),
            "` and `",
            @sprintf("%.3f", mean(row.reversed_final_root for row in confirm_rows)),
            "`, respectively. The broad corrective bundle likelihood overwhelmed those")
        println(io, "control manipulations. They therefore do not supply the intended negative")
        println(io, "discrimination, and no derived-ordering claim is licensed.")
    else
        println(io, "Not opened. The frozen pilot record is complete; run `confirm` once.")
    end
    println(io)
    println(io, "## Honest interpretation")
    println(io)
    if confirm_complete
        if confirmation_verdicts.overall
            println(io, "Inside this authored construction, context-split redescription is a")
            println(io, "selective candidate mechanism: it is preferred where temporal structure")
            println(io, "exists, loses where it does not, and identity-root revision follows from")
            println(io, "inference. This is an existence result, not evidence for a clinical effect,")
            println(io, "a biological mechanism, or the ontology of parts.")
        else
            println(io, "Criteria 1 and 2 support a narrow construction result: model comparison")
            println(io, "selectively discovers context-split redescription and it predicts held-out")
            println(io, "context-sensitive behavior better than either comparator. The central")
            println(io, "revision claim does not follow. All four identity-root arms saturated, the")
            println(io, "negative root controls also saturated, and the do-over never shortened")
            println(io, "reduction. Per §3.7, the manuscript's stipulation confession therefore")
            println(io, "stands, and the unburdening do-over still lacks the proposed computational")
            println(io, "anchor. No world-generator retuning was used to rescue those failures.")
            println(io, "Passing sub-results are construction results only, not evidence for a")
            println(io, "clinical effect, biological mechanism, or ontology of parts.")
        end
    else
        println(io, "Interpretation is intentionally withheld until the fresh block is run.")
    end
    println(io)
    println(io, "## Design decisions")
    println(io)
    println(io, "The specification does not define a likelihood family. Gaussian behavior")
    println(io, "with exact conjugate variational scoring was chosen because its accuracy and")
    println(io, "KL complexity terms are auditable. The latent context marker is noisy and")
    println(io, "never supplied as a label. The do-over uses beta-Bernoulli Bayesian model")
    println(io, "reduction: the full model has separate then/now catastrophe rates; the")
    println(io, "reduced model shares one rate. This conservative choice lets timing emerge")
    println(io, "from evidence rather than a completion rule.")
    return String(take!(io))
end

mode = isempty(ARGS) ? "pilot" : ARGS[1]
mode in ("pilot", "confirm") || error("usage: run_context_split_redescription.jl [pilot|confirm]")

config = ContextSplitConfig()
output_dir = joinpath(project_dir, "results", "context_split_redescription")
mkpath(output_dir)
per_seed_path = joinpath(output_dir, "per_seed.csv")
status_path = joinpath(output_dir, "status.json")

if isfile(status_path) &&
        occursin("\"confirmation_complete\": true", read(status_path, String))
    error("confirmation output already exists; refusing to overwrite frozen results")
end

if mode == "pilot"
    @assert isempty(intersect(PILOT_SEEDS, CONFIRM_SEEDS))
    rows = [run_seed(seed; stage = :pilot, config = config)
        for seed in PILOT_SEEDS]
    write_csv(per_seed_path, rows)
    write_json(joinpath(output_dir, "freeze.json"), (
        frozen_at = string(now()), pilot_seeds = PILOT_SEEDS,
        confirmation_seeds = CONFIRM_SEEDS,
        thresholds_moved = false,
        heldout_margin = 0.05, ordering_pair_tolerance = 0.12,
        ordering_gap = 0.30, design_frozen = true,
    ))
    write_magic_numbers(joinpath(output_dir, "magic-numbers.md"), config)
    write_json(joinpath(output_dir, "summary.json"), (
        stage = "pilot", pilot = summarize_rows(rows),
        pilot_verdicts = criteria_verdicts(rows),
        complexity = complexity_audit(config),
    ))
    write_json(status_path, (
        stage = "pilot_frozen", pilot_complete = true,
        confirmation_complete = false, valid = true,
    ))
    write(joinpath(output_dir, "report.md"),
        report_text(rows, NamedTuple[], config))
    println("Pilot complete and frozen: $output_dir")
else
    isfile(joinpath(output_dir, "freeze.json")) ||
        error("pilot freeze record missing; refusing to open confirmation")
    # The seed functions are deterministic. Reconstruct the frozen pilot rows
    # under the frozen source so quoted audit strings never need a lossy CSV
    # round trip before concatenation.
    pilot_rows = [run_seed(seed; stage = :pilot, config = config)
        for seed in PILOT_SEEDS]
    @assert isempty(intersect(PILOT_SEEDS, CONFIRM_SEEDS))
    confirm_rows = [run_seed(seed; stage = :confirm, config = config)
        for seed in CONFIRM_SEEDS]
    all_rows = vcat(pilot_rows, confirm_rows)
    write_csv(per_seed_path, all_rows)
    write_magic_numbers(joinpath(output_dir, "magic-numbers.md"), config)
    write_json(joinpath(output_dir, "summary.json"), (
        stage = "confirmation", pilot = summarize_rows(pilot_rows),
        confirmation = summarize_rows(confirm_rows),
        confirmation_verdicts = criteria_verdicts(confirm_rows),
        complexity = complexity_audit(config),
    ))
    verdicts = criteria_verdicts(confirm_rows)
    write_json(status_path, (
        stage = "confirmation_complete", pilot_complete = true,
        confirmation_complete = true, valid = true,
        overall = verdicts.overall ? "support" : "failed_or_mixed",
        criteria = verdicts,
    ))
    write(joinpath(output_dir, "report.md"),
        report_text(pilot_rows, confirm_rows, config))
    println("Confirmation complete: $output_dir")
    println("Verdicts: ", verdicts)
end
