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
include(joinpath(project_dir, "src", "ContextSplitRedescription44b.jl"))
using .ContextSplitRedescription44b

function csv_cell(value)
    text = value isa AbstractFloat ? @sprintf("%.12g", value) : string(value)
    occursin(r"[\",\n]", text) || return text
    return "\"" * replace(text, "\"" => "\"\"") * "\""
end

function write_csv(path, rows)
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

function json_value(io, value; indent = 0)
    pad = " "^indent
    if value isa NamedTuple
        println(io, "{")
        entries = collect(pairs(value))
        for (index, (key, item)) in enumerate(entries)
            print(io, " "^(indent + 2), "\"", json_escape(key), "\": ")
            json_value(io, item; indent = indent + 2)
            index < length(entries) && print(io, ",")
            println(io)
        end
        print(io, pad, "}")
    elseif value isa AbstractVector
        print(io, "[")
        for (index, item) in enumerate(value)
            json_value(io, item; indent = indent)
            index < length(value) && print(io, ", ")
        end
        print(io, "]")
    elseif value isa Bool
        print(io, value ? "true" : "false")
    elseif value isa Number
        print(io, isfinite(value) ? value : "\"$(value)\"")
    elseif value === nothing
        print(io, "null")
    else
        print(io, "\"", json_escape(value), "\"")
    end
end

function write_json(path, value)
    open(path, "w") do io
        json_value(io, value)
        println(io)
    end
end

function config_record(config)
    c = config.calibration
    return (
        id = c.id,
        root_sessions = c.root_sessions,
        root_amplitude = c.root_amplitude,
        root_observation_sd = c.root_observation_sd,
        contact_amplitude = c.contact_amplitude,
        contact_sd = c.contact_sd,
        evidence_scale = c.evidence_scale,
        safe_prior_mass = c.safe_prior_mass,
        full_prior_mass = c.full_prior_mass,
        reduced_model_log_prior_penalty =
            c.reduced_model_log_prior_penalty,
    )
end

function write_magic(path, config)
    c = config.calibration
    open(path, "w") do io
        println(io, "# Magic numbers — Experiment 44b")
        println(io)
        println(io, "| Constant | Value | Rationale |")
        println(io, "|---|---:|---|")
        rows = [
            ("pilot seeds", "174701:174710", "Calibration-only worlds."),
            ("confirm seeds", "174801:174820", "Never-opened confirmation worlds."),
            ("calibration 01", "18, 0.55, 0.90, 0.45, 0.90", "Preregistered sessions, root amplitude/SD, and contact amplitude/SD; failed pilot guard."),
            ("calibration 02", "14, 0.35, 1.00, 0.30, 1.00", "First preregistered calibration passing the pilot guard."),
            ("calibration 03", "12, 0.30, 1.05, 0.25, 1.05", "Preregistered fallback evaluated only during runner debugging after calibration 02 passed; ineligible for selection."),
            ("root sessions", c.root_sessions, "First pilot calibration with a passing dynamic-range guard."),
            ("root amplitude", c.root_amplitude, "Weakens each bundle likelihood ratio without changing its sign."),
            ("root observation SD", c.root_observation_sd, "Keeps weak arms away from the ceiling."),
            ("contact amplitude", c.contact_amplitude, "Makes contact informative but not individually decisive."),
            ("contact SD", c.contact_sd, "Matches the calibrated root evidence scale."),
            ("evidence scale", c.evidence_scale, "Common likelihood multiplier; never arm-specific."),
            ("safe prior mass", c.safe_prior_mass, "Reduced-model prior favoring a non-catastrophic present ending."),
            ("full prior mass", c.full_prior_mass, "Uniform full-model ending prior."),
            ("reduced prior penalty", c.reduced_model_log_prior_penalty, "Prevents reduction before sufficient present evidence."),
            ("saturation upper", config.saturation_upper, "Pilot-frozen guard for regulation and negative controls."),
            ("witnessing band", "$(config.witnessing_lower):$(config.witnessing_upper)", "Requires revision to be visible but not pinned."),
            ("dynamic range minimum", config.dynamic_range_minimum, "Manipulation check, not criterion 3."),
            ("baseline reachable rate", config.baseline_reachable_rate, "Makes time-to-reduction measurable before testing shortening."),
            ("criterion pair tolerance", 0.12, "Unchanged from 44a freeze."),
            ("criterion high-low gap", 0.30, "Unchanged from 44a freeze."),
            ("criterion heldout margin", 0.05, "Unchanged §3.6 threshold."),
            ("criterion do-over shortening", 0.20, "Unchanged §3.6 threshold."),
            ("criterion success rate", 0.80, "Unchanged 16/20 threshold."),
            ("imaginal outcome probabilities", "0.15 + 0.70*q(g+)", "Posterior predictive probability under the reduced model."),
            ("full imaginal probability", 0.50, "Root-independent full-model prediction."),
            ("bundle pattern", "1.00, 0.82, 0.65, 0.92", "Experiment-43 four-element corrective bundle shape."),
            ("contact breadth", "geometric mean of four field values", "Contact reaches the root only through a broad context-held field."),
            ("reversed graph LLR", 0.0, "Cue-local parents make observation likelihood identical under both roots."),
            ("root prior positive", 0.06, "Inherited unchanged from 44a."),
            ("revision begun/crossing", "0.62 / 0.80", "Inherited unchanged from 44a."),
            ("reduction threshold", 0.35, "Inherited unchanged from 44a."),
            ("imaginal packets/weight", "4 / 0.72", "Inherited unchanged from 44a."),
            ("reduced catastrophe prior", 1.0, "Completes the asymmetric Beta(8,1) reduced prior."),
            ("premature session", 1, "Fixed pre-revision application point."),
            ("root RNG offset", 700000, "Independent 44b root stream."),
            ("do-over RNG offset", 800000, "Independent 44b ending stream."),
            ("catastrophe jitter", 0.03, "Fractional outcome noise shared across do-over arms."),
            ("breadth numerical guard", "1e-12", "Prevents log zero and has no scientific role."),
        ]
        for (name, value, reason) in rows
            println(io, "| `", name, "` | `", value, "` | ", reason, " |")
        end
    end
end

mode = isempty(ARGS) ? "pilot" : ARGS[1]
mode in ("pilot", "confirm") ||
    error("usage: run_context_split_redescription_44b.jl [pilot|confirm]")

output_dir = joinpath(project_dir, "results",
    "context_split_redescription", "44b")
mkpath(output_dir)
status_path = joinpath(output_dir, "status.json")
if isfile(status_path) &&
        occursin("\"confirmation_complete\": true", read(status_path, String))
    error("44b confirmation already exists; refusing overwrite")
end

if mode == "pilot"
    audit_rows = reduce(vcat,
        wiring_audit_44a(seed) for seed in PILOT_44B_SEEDS)
    write_csv(joinpath(output_dir, "wiring-audit-44a.csv"), audit_rows)

    calibration_records = NamedTuple[]
    selected = Ref{Any}(nothing)
    selected_rows = Ref(NamedTuple[])
    for calibration in calibration_candidates()
        candidate_config = Config44b(calibration = calibration)
        rows = [run_seed_44b(seed; stage = :pilot,
            config = candidate_config)
            for seed in PILOT_44B_SEEDS]
        candidate_guard = saturation_guard(rows, candidate_config)
        push!(calibration_records, (
            calibration_id = calibration.id,
            root_sessions = calibration.root_sessions,
            root_amplitude = calibration.root_amplitude,
            root_observation_sd = calibration.root_observation_sd,
            contact_amplitude = calibration.contact_amplitude,
            contact_sd = calibration.contact_sd,
            mean_witnessing = mean(row.witnessing_final_root for row in rows),
            mean_open = mean(row.open_final_root for row in rows),
            mean_regulation = mean(row.regulation_final_root for row in rows),
            mean_narrowed = mean(row.narrowed_final_root for row in rows),
            mean_fixed = mean(row.fixed_context_final_root for row in rows),
            mean_reversed = mean(row.reversed_final_root for row in rows),
            baseline_reachable = count(row.baseline_reduction_time <=
                calibration.root_sessions for row in rows),
            guard_passed = candidate_guard.passed,
        ))
        if candidate_guard.passed
            selected[] = candidate_config
            selected_rows[] = rows
            break
        end
    end
    isnothing(selected[]) &&
        error("no preregistered calibration passed; confirmation remains closed")
    write_csv(joinpath(output_dir, "calibration-ledger.csv"),
        calibration_records)
    write_csv(joinpath(output_dir, "per_seed.csv"), selected_rows[])
    guard = saturation_guard(selected_rows[], selected[])
    write_json(joinpath(output_dir, "freeze.json"), (
        frozen_at = string(now()),
        pilot_seeds = PILOT_44B_SEEDS,
        confirmation_seeds = CONFIRM_44B_SEEDS,
        selected_calibration = config_record(selected[]),
        saturation_guard = guard,
        criterion_thresholds_changed = false,
    ))
    write_json(joinpath(output_dir, "summary.json"), (
        stage = "pilot_frozen",
        pilot = summarize_44b(selected_rows[]),
        guard = guard,
        pilot_verdicts = verdicts_44b(selected_rows[]),
        calibration_attempts = calibration_records,
    ))
    write_json(status_path, (
        stage = "pilot_frozen",
        pilot_complete = true,
        confirmation_complete = false,
        saturation_guard_passed = true,
        selected_calibration = selected[].calibration.id,
    ))
    write_magic(joinpath(output_dir, "magic-numbers.md"), selected[])
    println("44b pilot calibrated and frozen with ",
        selected[].calibration.id)
else
    freeze_path = joinpath(output_dir, "freeze.json")
    isfile(freeze_path) || error("44b freeze missing")
    freeze_text = read(freeze_path, String)
    selected_calibration = only(filter(candidate ->
        occursin("\"id\": \"$(candidate.id)\"", freeze_text),
        calibration_candidates()))
    config = Config44b(calibration = selected_calibration)
    pilot_rows = [run_seed_44b(seed; stage = :pilot, config = config)
        for seed in PILOT_44B_SEEDS]
    saturation_guard(pilot_rows, config).passed ||
        error("frozen 44b manipulation guard no longer passes")
    confirm_rows = [run_seed_44b(seed; stage = :confirm, config = config)
        for seed in CONFIRM_44B_SEEDS]
    write_csv(joinpath(output_dir, "per_seed.csv"),
        vcat(pilot_rows, confirm_rows))
    summary = summarize_44b(confirm_rows)
    verdicts = verdicts_44b(confirm_rows)
    guard = saturation_guard(confirm_rows, config)
    write_json(joinpath(output_dir, "summary.json"), (
        stage = "confirmation",
        pilot = summarize_44b(pilot_rows),
        confirmation = summary,
        confirmation_manipulation_check = guard,
        confirmation_verdicts = verdicts,
        selected_calibration = config_record(config),
    ))
    write_json(status_path, (
        stage = "confirmation_complete",
        pilot_complete = true,
        confirmation_complete = true,
        valid = true,
        pilot_saturation_guard_passed = true,
        weak_and_negative_controls_informative =
            guard.regulation_informative &&
            guard.fixed_context_not_saturated &&
            guard.reversed_not_saturated &&
            guard.dynamic_range,
        confirmation_witnessing_upper_band_passed =
            guard.witnessing_informative,
        saturation_guard_passed_in_confirmation = guard.passed,
        overall = verdicts.overall ? "support" : "failed_or_mixed",
        criteria = verdicts,
    ))
    write_magic(joinpath(output_dir, "magic-numbers.md"), config)
    println("44b confirmation complete: ", verdicts)
end
