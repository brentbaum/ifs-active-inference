"""
    ifs_simulation_v2.jl - Three-Move IFS Active Inference Simulation

Usage:
    cd projects/library
    julia --project=. scripts/ifs_simulation_v2.jl

Environment flags:
    IFS_V2_SKIP_FIGURES=1   Run numeric verification only (no Plots dependency)
    IFS_V2_N_REPS=60        Replications for the main conditions
    IFS_V2_SWEEP_REPS=40    Replications for the Self-energy sweep
    IFS_V2_SENS_REPS=50     Replications per +/-20% sensitivity run
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

module IFSV2ScriptSupport
using LinearAlgebra
using Random
using Statistics

include(joinpath(@__DIR__, "..", "src", "active_inference", "core.jl"))
include(joinpath(@__DIR__, "..", "src", "active_inference", "inference.jl"))
include(joinpath(@__DIR__, "..", "src", "active_inference", "efe.jl"))
include(joinpath(@__DIR__, "..", "src", "active_inference", "ifs_model_v2.jl"))
end

using .IFSV2ScriptSupport
using .IFSV2ScriptSupport:
    IFSV2Params,
    IFSV2ConditionConfig,
    IFSV2Summary,
    IFSV2_CONTEXT_SAFE,
    IFSV2_POLICY_AVOID,
    IFSV2_POLICY_INSPECT,
    IFSV2_POLICY_STAY,
    all_ifs_v2_configs,
    build_ifs_v2_model,
    validate_ifs_v2_A,
    validate_ifs_v2_transitions,
    run_ifs_v2_condition,
    relational_depth_ifs_v2_config,
    run_ifs_v2_suite,
    run_ifs_v2_replications,
    run_ifs_v2_sensitivity,
    override_ifs_v2_params,
    baseline_ifs_v2_config,
    exposure_ifs_v2_config,
    informational_ifs_v2_config,
    constant_ifs_v2_schedule,
    witnessing_onset_ifs_v2_config
using Statistics

const ENABLE_FIGURES = get(ENV, "IFS_V2_SKIP_FIGURES", "0") != "1"

if ENABLE_FIGURES
    ENV["GKSwstype"] = get(ENV, "GKSwstype", "100")
    ENV["GKS_NO_GUI"] = get(ENV, "GKS_NO_GUI", "1")
    using Plots

    # --- Tufte palette ---
    const COL_GRAY       = RGB(0.4, 0.4, 0.4)        # #666 -- Exposure & Baseline
    const COL_BLUE       = RGB(0.33, 0.47, 0.65)      # muted blue -- Informational
    const COL_ACCENT     = RGB(0.77, 0.35, 0.24)      # #c45a3c -- Relational Depth
    const COL_BG         = RGB(1.0, 1.0, 0.973)       # #fffff8 -- Tufte off-white
    const COL_GRID       = RGB(0.85, 0.85, 0.85)      # light gray for sparse gridlines
    const COL_ANNOTATION = RGB(0.3, 0.3, 0.3)
    const COL_LIGHT_GRAY = RGB(0.72, 0.72, 0.72)
    const COL_SOFT_BLUE  = RGB(0.57, 0.67, 0.78)
    const COL_SOFT_TAUPE = RGB(0.70, 0.65, 0.58)
    const COL_CHANNELS   = [COL_LIGHT_GRAY, COL_SOFT_BLUE, COL_SOFT_TAUPE, COL_BLUE, COL_ACCENT]
    const COL_PRAGMATIC  = COL_GRAY
    const COL_EPISTEMIC  = COL_ACCENT
    const COL_AMBIGUITY  = COL_LIGHT_GRAY

    default(
        fontfamily="Georgia",
        titlefontsize=11,
        guidefontsize=10,
        tickfontsize=8,
        legendfontsize=8,
        linewidth=2.0,
        framestyle=:semi,
        grid=false,
        background_color=COL_BG,
        background_color_inside=COL_BG,
        foreground_color_grid=COL_GRID,
        dpi=300,
        size=(750, 500)
    )
end

const FIGURE_DIR = joinpath(@__DIR__, "..", "..", "ifs-paper", "figures", "v2")
mkpath(FIGURE_DIR)

const N_REPS = parse(Int, get(ENV, "IFS_V2_N_REPS", "60"))
const SWEEP_REPS = parse(Int, get(ENV, "IFS_V2_SWEEP_REPS", string(max(80, N_REPS))))
const SENS_REPS = parse(Int, get(ENV, "IFS_V2_SENS_REPS", string(max(50, N_REPS))))
const FOCUSED_REPS = parse(Int, get(ENV, "IFS_V2_FOCUSED_REPS", string(max(40, N_REPS))))
const SEED = 42

const ROW_LABELS = ["Self-state", "Threat", "Expected Outcome", "P(approach/stay)"]
const STRIP_LABELS = ["Capture", "Witness"]
const CHANNEL_LABELS = [
    "External cue",
    "Arousal",
    "Action outcome",
    "Informational context",
    "Witnessed self-state",
]
const ACTION_LABELS = Dict(
    IFSV2_POLICY_AVOID => "Avoid",
    IFSV2_POLICY_INSPECT => "Inspect",
    IFSV2_POLICY_STAY => "Stay",
)

summary_by_name(summaries) = Dict(summary.condition => summary for summary in summaries)

function condition_config_by_name(name::String, params::IFSV2Params)
    for config in all_ifs_v2_configs(params)
        config.name == name && return config
    end
    error("Unknown condition name: $name")
end

function mean_crossing(series::Vector{Float64}, threshold::Float64)
    for i in eachindex(series)
        series[i] >= threshold && return i
    end
    return nothing
end

function print_matrix_validation(params::IFSV2Params)
    model_h1 = build_ifs_v2_model(architecture=:H1, params=params)
    model_h2 = build_ifs_v2_model(architecture=:H2, params=params)
    println("Matrix validation")
    println("  H1 A columns sum to 1.0: $(validate_ifs_v2_A(model_h1.A_reference))")
    println("  H2 A columns sum to 1.0: $(validate_ifs_v2_A(model_h2.A_reference))")
    println("  H1 transitions validated: $(validate_ifs_v2_transitions(model_h1.B_self, model_h1.B_threat, model_h1.B_outcome; architecture=:H1))")
    println("  H2 transitions validated: $(validate_ifs_v2_transitions(model_h2.B_self, model_h2.B_threat, model_h2.B_outcome; architecture=:H2))")
end

function print_single_trial_debug(params::IFSV2Params)
    println("\nSingle-trial debug: Relational Depth / H1")
    model = build_ifs_v2_model(architecture=:H1, params=params)
    _ = run_ifs_v2_condition(model, relational_depth_ifs_v2_config(params); seed=SEED, verbose=true)
    return nothing
end

function print_condition_summary(summary::IFSV2Summary)
    metrics = summary.metric_means
    println("  $(summary.condition):")
    println("    final self      = $(round(summary.mean_self[end], digits=3)) ± $(round(summary.std_self[end], digits=3))")
    println("    final threat    = $(round(summary.mean_threat[end], digits=3)) ± $(round(summary.std_threat[end], digits=3))")
    println("    final outcome   = $(round(summary.mean_outcome[end], digits=3)) ± $(round(summary.std_outcome[end], digits=3))")
    println("    probe policy    = $(round(summary.mean_policy[end], digits=3)) ± $(round(summary.std_policy[end], digits=3))")
    println("    first passage   = self $(round(metrics[:first_passage_self], digits=2)), threat $(round(metrics[:first_passage_threat], digits=2)), outcome $(round(metrics[:first_passage_outcome], digits=2)), policy $(round(metrics[:first_passage_policy], digits=2))")
    println("    cascade rate    = $(round(metrics[:cascade_rate], digits=3))")
end

function build_sweep_summary(params::IFSV2Params; architecture::Symbol=:H1, n_replications::Int=SWEEP_REPS)
    Es = collect(0.0:0.05:1.0)
    mean_final = zeros(Float64, length(Es))
    std_final = zeros(Float64, length(Es))
    for (i, E_t) in enumerate(Es)
        config = IFSV2ConditionConfig(
            "Sweep $(round(E_t, digits=2))",
            IFSV2_CONTEXT_SAFE,
            constant_ifs_v2_schedule(params.T_forced, params.T_probe, E_t),
            IFSV2_POLICY_INSPECT,
            params.T_forced,
            params.T_probe,
            true,
            false
        )
        summary = run_ifs_v2_replications(
            architecture=architecture,
            config=config,
            params=params,
            n_replications=n_replications,
            seed=SEED + 10 * i
        )
        mean_final[i] = summary.mean_self[end]
        std_final[i] = summary.std_self[end]
    end
    return Es, mean_final, std_final
end

function print_sensitivity_summary(rows)
    println("\nSensitivity (+/-20%)")
    red_flags = 0
    for row in rows
        fragile = row.relational_self_std > 0.15 || row.baseline_drift > 0.10 || row.danger_policy > 0.50
        red_flags += fragile ? 1 : 0
    end
    println("  runs checked      = $(length(rows))")
    println("  red flags         = $red_flags")
    println("  worst self std    = $(round(maximum(row.relational_self_std for row in rows), digits=3))")
    println("  worst baseline    = $(round(maximum(row.baseline_drift for row in rows), digits=3))")
    println("  worst danger pol  = $(round(maximum(row.danger_policy for row in rows), digits=3))")
    println("  weakest self gap  = $(round(minimum(row.self_gap for row in rows), digits=3))")
end

pairwise_l1(a::AbstractVector{<:Real}, b::AbstractVector{<:Real}) = sum(abs.(Float64.(a) .- Float64.(b)))

function run_step_matrix(summary::IFSV2Summary, getter::Function)
    T = length(summary.runs[1].steps)
    N = length(summary.runs)
    data = zeros(Float64, T, N)
    for (j, run) in enumerate(summary.runs)
        for (t, step) in enumerate(run.steps)
            data[t, j] = getter(step)
        end
    end
    return data
end

function mean_step_series(summary::IFSV2Summary, getter::Function)
    data = run_step_matrix(summary, getter)
    return vec(mean(data; dims=2)), vec(std(data; dims=2))
end

function mean_channel_series(summary::IFSV2Summary, getter::Function)
    T = length(summary.runs[1].steps)
    N = length(summary.runs)
    data = zeros(Float64, 5, T, N)
    for (j, run) in enumerate(summary.runs)
        for (t, step) in enumerate(run.steps)
            values = getter(step)
            for g in 1:5
                data[g, t, j] = values[g]
            end
        end
    end
    return dropdims(mean(data; dims=3), dims=3)
end

function mean_action_filtered_series(summary::IFSV2Summary, action::Int, getter::Function)
    return mean_step_series(summary) do step
        step.action == action ? getter(step) : 0.0
    end
end

function condition_decomposition_payload(summary::IFSV2Summary)
    pragmatic_channels = mean_channel_series(summary, step -> step.efe_pragmatic_channels)
    epistemic_channels = mean_channel_series(summary, step -> step.efe_epistemic_channels)
    pragmatic, _ = mean_step_series(summary, step -> step.efe_pragmatic)
    epistemic, _ = mean_step_series(summary, step -> step.efe_epistemic)
    ambiguity, _ = mean_step_series(summary, step -> step.efe_ambiguity)
    return (
        pragmatic_channels=pragmatic_channels,
        epistemic_channels=epistemic_channels,
        pragmatic=pragmatic,
        epistemic=epistemic,
        ambiguity=ambiguity,
    )
end

function time_axis(summary::IFSV2Summary)
    return collect(1:length(summary.runs[1].steps))
end

function forced_phase_indices(summary::IFSV2Summary)
    return findall(step -> step.phase == :forced, summary.runs[1].steps)
end

function forced_time_axis(summary::IFSV2Summary)
    return collect(1:length(forced_phase_indices(summary)))
end

function forced_step_series(summary::IFSV2Summary, getter::Function)
    idx = forced_phase_indices(summary)
    values, spreads = mean_step_series(summary, getter)
    return values[idx], spreads[idx]
end

function forced_channel_series(summary::IFSV2Summary, getter::Function)
    idx = forced_phase_indices(summary)
    return mean_channel_series(summary, getter)[:, idx]
end

function forced_E_series(summary::IFSV2Summary)
    idx = forced_phase_indices(summary)
    return [summary.runs[1].steps[i].E_t for i in idx]
end

function onset_index(series::AbstractVector{<:Real}; min_fraction::Float64=0.15, floor::Float64=1e-3)
    peak = maximum(Float64.(series))
    threshold = max(floor, peak * min_fraction)
    for i in eachindex(series)
        series[i] >= threshold && return i
    end
    return nothing
end

function evaluate_success_criteria(
    h1_lookup::Dict{String,IFSV2Summary},
    h2_relational::IFSV2Summary,
    sensitivity_rows
)
    exposure = h1_lookup["Exposure"]
    informational = h1_lookup["Informational"]
    relational = h1_lookup["Relational Depth"]

    probe_vectors = [
        exposure.mean_probe_policy[:, end],
        informational.mean_probe_policy[:, end],
        relational.mean_probe_policy[:, end],
    ]
    probe_l1 = minimum(pairwise_l1(probe_vectors[i], probe_vectors[j]) for i in 1:2 for j in (i + 1):3)

    self_cross = relational.metric_means[:first_passage_self]
    threat_cross = relational.metric_means[:first_passage_threat]
    outcome_cross = relational.metric_means[:first_passage_outcome]
    policy_cross = relational.metric_means[:first_passage_policy]

    criteria = (
        cascade_diagonal =
            !isnan(self_cross) &&
            !isnan(threat_cross) &&
            !isnan(outcome_cross) &&
            !isnan(policy_cross) &&
            self_cross <= threat_cross <= outcome_cross <= policy_cross &&
            self_cross < policy_cross,
        relational_gap_nonoverlap =
            (relational.mean_self[end] - relational.std_self[end]) >
            max(
                exposure.mean_self[end] + exposure.std_self[end],
                informational.mean_self[end] + informational.std_self[end],
            ),
        free_choice_differentiates = probe_l1 > 0.15,
        h1_vs_h2_differentiates =
            (relational.mean_self[end] - h2_relational.mean_self[end]) > 0.40 &&
            (relational.mean_policy[end] - h2_relational.mean_policy[end]) > 0.30,
        sensitivity_stable = all(
            row.relational_self_std <= 0.15 &&
            row.baseline_drift <= 0.10 &&
            row.danger_policy <= 0.50
            for row in sensitivity_rows
        ),
    )

    return criteria, probe_l1
end

function print_success_criteria(criteria, probe_l1)
    println("\nSuccess criteria")
    println("  cascade diagonal  = $(criteria.cascade_diagonal)")
    println("  relational gap    = $(criteria.relational_gap_nonoverlap)")
    println("  free-choice probe = $(criteria.free_choice_differentiates) (min L1 = $(round(probe_l1, digits=3)))")
    println("  H1 vs H2          = $(criteria.h1_vs_h2_differentiates)")
    println("  sensitivity stab. = $(criteria.sensitivity_stable)")
end

function build_ratio_varied_params(params::IFSV2Params, target_ratio::Float64)
    product = params.beta_se * params.gamma_se
    beta = sqrt(product * target_ratio)
    gamma = sqrt(product / target_ratio)
    return override_ifs_v2_params(params; beta_se=beta, gamma_se=gamma)
end

function run_focused_sensitivity(params::IFSV2Params; n_replications::Int=FOCUSED_REPS, seed::Int=SEED + 4000)
    specs = [
        (:lambda_witness_max, collect(2.0:1.0:10.0)),
        (:alpha_witness, collect(1.5:0.5:5.0)),
        (:beta_gamma_ratio, [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]),
        (:policy_precision, collect(2.0:1.0:8.0)),
    ]

    rows = NamedTuple[]
    for (name, values) in specs
        for (idx, value) in enumerate(values)
            varied = if name == :beta_gamma_ratio
                build_ratio_varied_params(params, value)
            else
                override_ifs_v2_params(params; NamedTuple{(name,)}((value,))...)
            end

            seed_base = seed + Int(mod(hash((name, value, :base)), 10^8))
            exposure = run_ifs_v2_replications(
                architecture=:H1,
                config=exposure_ifs_v2_config(varied),
                params=varied,
                n_replications=n_replications,
                seed=seed_base + idx
            )
            informational = run_ifs_v2_replications(
                architecture=:H1,
                config=informational_ifs_v2_config(varied),
                params=varied,
                n_replications=n_replications,
                seed=seed_base + 100 + idx
            )
            relational = run_ifs_v2_replications(
                architecture=:H1,
                config=relational_depth_ifs_v2_config(varied),
                params=varied,
                n_replications=n_replications,
                seed=seed_base + 200 + idx
            )
            baseline = run_ifs_v2_replications(
                architecture=:H1,
                config=baseline_ifs_v2_config(varied),
                params=varied,
                n_replications=n_replications,
                seed=seed_base + 300 + idx
            )
            danger = run_ifs_v2_replications(
                architecture=:H1,
                config=condition_config_by_name("Real Danger", varied),
                params=varied,
                n_replications=n_replications,
                seed=seed_base + 400 + idx
            )
            h2_relational = run_ifs_v2_replications(
                architecture=:H2,
                config=relational_depth_ifs_v2_config(varied),
                params=varied,
                n_replications=n_replications,
                seed=seed_base + 500 + idx
            )

            probe_vectors = [
                exposure.mean_probe_policy[:, end],
                informational.mean_probe_policy[:, end],
                relational.mean_probe_policy[:, end],
            ]
            min_probe_l1 = minimum(pairwise_l1(probe_vectors[i], probe_vectors[j]) for i in 1:2 for j in (i + 1):3)
            rel_gap = relational.mean_self[end] - max(exposure.mean_self[end] + exposure.std_self[end], informational.mean_self[end] + informational.std_self[end])
            self_gap = relational.mean_self[end] - informational.mean_self[end]
            h1_h2_gap = relational.mean_self[end] - h2_relational.mean_self[end]

            pass =
                !isnan(relational.metric_means[:first_passage_policy]) &&
                relational.metric_means[:first_passage_self] <= relational.metric_means[:first_passage_threat] <= relational.metric_means[:first_passage_outcome] <= relational.metric_means[:first_passage_policy] &&
                relational.metric_means[:first_passage_self] < relational.metric_means[:first_passage_policy] &&
                rel_gap > 0.0 &&
                min_probe_l1 > 0.15 &&
                h1_h2_gap > 0.40 &&
                abs(baseline.mean_self[end] - baseline.mean_self[1]) <= 0.10 &&
                danger.mean_policy[end] <= 0.50

            push!(rows, (
                parameter=name,
                value=value,
                relational_self=relational.mean_self[end],
                self_gap=self_gap,
                relational_gap=rel_gap,
                baseline_drift=abs(baseline.mean_self[end] - baseline.mean_self[1]),
                danger_policy=danger.mean_policy[end],
                h1_h2_gap=h1_h2_gap,
                cascade_rate=relational.metric_means[:cascade_rate],
                probe_l1=min_probe_l1,
                pass=pass,
            ))
        end
    end

    return rows
end

function print_focused_sensitivity(rows)
    println("\nFocused sensitivity")
    for parameter in (:lambda_witness_max, :alpha_witness, :beta_gamma_ratio, :policy_precision)
        subset = filter(row -> row.parameter == parameter, rows)
        pass_count = count(row -> row.pass, subset)
        worst_gap = minimum(row.relational_gap for row in subset)
        worst_probe = minimum(row.probe_l1 for row in subset)
        best_baseline = maximum(row.baseline_drift for row in subset)
        println("  $(parameter):")
        println("    pass values      = $pass_count / $(length(subset))")
        println("    relational gap   = $(round(worst_gap, digits=3)) min")
        println("    probe separation = $(round(worst_probe, digits=3)) min L1")
        println("    baseline drift   = $(round(best_baseline, digits=3)) max")
    end
end

function summarize_parameter_dependence(rows)
    summary = NamedTuple[]
    for parameter in (:lambda_witness_max, :alpha_witness, :beta_gamma_ratio, :policy_precision)
        subset = filter(row -> row.parameter == parameter, rows)
        pass_rate = count(row -> row.pass, subset) / length(subset)
        rel_span = maximum(row.relational_self for row in subset) - minimum(row.relational_self for row in subset)
        gap_span = maximum(row.self_gap for row in subset) - minimum(row.self_gap for row in subset)
        fragility = (1.0 - pass_rate) + rel_span + gap_span
        push!(summary, (parameter=parameter, pass_rate=pass_rate, rel_span=rel_span, gap_span=gap_span, fragility=fragility))
    end
    return sort(summary; by=row -> -row.fragility)
end

if ENABLE_FIGURES
    function format_panel!(p, forced_boundary::Int, ymax::Float64, x_end::Int)
        vline!(p, [forced_boundary + 0.5], color=COL_GRID, linestyle=:dash, linewidth=1.0, label="")
        ylims!(p, (0.0, ymax))
        xlims!(p, (1.0, x_end + 3.0))
        return p
    end

    function plot_stacked_channel_panel(
        series::Matrix{Float64},
        title_text::String,
        forced_boundary::Int;
        ylabel::String=""
    )
        x = 1:size(series, 2)
        ymax = max(maximum(vec(sum(series; dims=1))) * 1.10, 1e-3)
        p = plot(
            title=title_text,
            xlabel="Time step",
            ylabel=ylabel,
            legend=false,
            size=(750, 500),
            grid=false,
            background_color=COL_BG,
            background_color_inside=COL_BG,
        )

        lower = zeros(Float64, length(x))
        for g in 1:5
            upper = lower .+ vec(series[g, :])
            plot!(
                p,
                x,
                upper,
                fillrange=lower,
                fillalpha=g == 5 ? 0.92 : 0.82,
                color=COL_CHANNELS[g],
                linecolor=COL_CHANNELS[g],
                linewidth=g == 5 ? 1.8 : 1.2,
                label="",
            )
            lower = upper
        end

        format_panel!(p, forced_boundary, ymax, length(x))

        cumulative = cumsum(series; dims=1)
        for g in 1:5
            lower_band = g == 1 ? 0.0 : cumulative[g - 1, end]
            upper_band = cumulative[g, end]
            band_height = upper_band - lower_band
            if g == 5 || band_height >= 0.06 * ymax
                annotate!(
                    p,
                    x[end] + 0.6,
                    (lower_band + upper_band) / 2,
                    text(CHANNEL_LABELS[g], 7, :left, COL_CHANNELS[g]),
                )
            end
        end
        return p
    end

    function plot_decomposition_line_panel(
        pragmatic::Vector{Float64},
        epistemic::Vector{Float64},
        title_text::String,
        forced_boundary::Int;
        ylabel::String=""
    )
        x = 1:length(pragmatic)
        ymax = max(maximum(vcat(pragmatic, epistemic)) * 1.10, 1e-3)
        p = plot(
            x,
            pragmatic,
            title=title_text,
            xlabel="Time step",
            ylabel=ylabel,
            color=COL_PRAGMATIC,
            linewidth=2.2,
            label="",
            legend=false,
            size=(750, 500),
            grid=false,
            background_color=COL_BG,
            background_color_inside=COL_BG,
        )
        plot!(p, x, epistemic, color=COL_EPISTEMIC, linewidth=2.2, label="")
        format_panel!(p, forced_boundary, ymax, length(x))
        annotate!(p, x[end] + 0.5, pragmatic[end], text("Pragmatic", 8, :left, COL_PRAGMATIC))
        annotate!(p, x[end] + 0.5, epistemic[end], text("Epistemic", 8, :left, COL_EPISTEMIC))
        return p
    end

    function plot_action_fingerprint_panel(
        summary::IFSV2Summary,
        action::Int,
        forced_boundary::Int;
        title_text::String="",
        ylabel::String="",
        annotate_components::Bool=false
    )
        pragmatic, _ = mean_action_filtered_series(summary, action, step -> step.efe_pragmatic)
        epistemic, _ = mean_action_filtered_series(summary, action, step -> step.efe_epistemic)
        ambiguity, _ = mean_action_filtered_series(summary, action, step -> step.efe_ambiguity)
        x = 1:length(pragmatic)
        ymax = max(maximum(pragmatic .+ ambiguity .+ epistemic) * 1.12, 1e-3)

        p = plot(
            title=title_text,
            xlabel="Time step",
            ylabel=ylabel,
            legend=false,
            size=(500, 333),
            grid=false,
            background_color=COL_BG,
            background_color_inside=COL_BG,
        )

        lower = zeros(Float64, length(x))
        for (label, values, color) in [
            ("Pragmatic", pragmatic, COL_PRAGMATIC),
            ("Ambiguity", ambiguity, COL_AMBIGUITY),
            ("Epistemic", epistemic, COL_EPISTEMIC),
        ]
            upper = lower .+ values
            plot!(
                p,
                x,
                upper,
                fillrange=lower,
                fillalpha=0.85,
                color=color,
                linecolor=color,
                linewidth=1.2,
                label="",
            )
            if annotate_components && maximum(values) > 0.02
                annotate!(p, x[end] + 0.35, (lower[end] + upper[end]) / 2, text(label, 7, :left, color))
            end
            lower = upper
        end

        format_panel!(p, forced_boundary, ymax, length(x))
        return p
    end

    function condition_heatmap_data(summary::IFSV2Summary)
        [
            summary.mean_self';
            summary.mean_threat';
            summary.mean_outcome';
            summary.mean_policy'
        ]
    end

    function condition_strip_data(summary::IFSV2Summary)
        witness = summary.mean_witness ./ max(maximum(summary.mean_witness), eps(Float64))
        [
            summary.mean_capture';
            witness'
        ]
    end

    function plot_condition_strip(summary::IFSV2Summary, forced_boundary::Int)
        data = condition_strip_data(summary)
        p = heatmap(
            1:size(data, 2),
            1:2,
            reverse(data; dims=1),
            color=:viridis,
            clims=(0.0, 1.0),
            legend=false,
            yticks=(1:2, reverse(STRIP_LABELS)),
            xticks=false,
            title="",
            framestyle=:box,
            background_color=COL_BG
        )
        vline!(p, [forced_boundary + 0.5], color=:white, linewidth=1.0, alpha=0.8)
        return p
    end

    function plot_condition_heatmap(summary::IFSV2Summary, forced_boundary::Int)
        data = condition_heatmap_data(summary)
        data_plot = reverse(data; dims=1)
        p = heatmap(
            1:size(data, 2),
            1:4,
            data_plot,
            color=:thermal,
            clims=(0.0, 1.0),
            legend=false,
            yticks=(1:4, reverse(ROW_LABELS)),
            xlabel="Time step",
            title=summary.condition,
            framestyle=:box,
            background_color=COL_BG
        )
        vline!(p, [forced_boundary + 0.5], color=:white, linewidth=1.4, alpha=0.9)

        # First-passage markers with annotation
        series_list = [summary.mean_self, summary.mean_threat, summary.mean_outcome, summary.mean_policy]
        y_positions = [4, 3, 2, 1]
        for (series, y) in zip(series_list, y_positions)
            t_cross = mean_crossing(series, 0.5)
            isnothing(t_cross) && continue
            scatter!(p, [t_cross], [y], markersize=4, markercolor=:white, markerstrokecolor=:black, label="")
        end
        return p
    end

    function save_one_figure(main_summaries::Vector{IFSV2Summary}, params::IFSV2Params)
        forced_boundary = params.T_forced
        plots = Any[]
        for summary in main_summaries
            push!(plots, plot_condition_strip(summary, forced_boundary))
            push!(plots, plot_condition_heatmap(summary, forced_boundary))
        end
        layout = grid(6, 1, heights=[0.08, 0.25, 0.08, 0.25, 0.08, 0.26])
        fig = plot(plots..., layout=layout, size=(1100, 1200),
            plot_title="Self-State Revises First Under Relational Depth",
            background_color=COL_BG)
        savefig(fig, joinpath(FIGURE_DIR, "ifs_v2_one_figure.png"))
        println("  saved ifs_v2_one_figure.png")
    end

    function save_relational_depth_gap(main_lookup::Dict{String,IFSV2Summary})
        p = plot(
            title="Relational Contact Opens the Identity Channel",
            xlabel="Time step",
            ylabel="P(capable / present)",
            ylims=(0.0, 1.05),
            legend=false,
            grid=false,
            size=(750, 500),
            background_color=COL_BG,
            background_color_inside=COL_BG
        )
        # Gray first: Exposure and Informational as background context
        exp_s = main_lookup["Exposure"]
        inf_s = main_lookup["Informational"]
        rel_s = main_lookup["Relational Depth"]

        plot!(p, exp_s.mean_self, ribbon=exp_s.std_self,
            color=COL_GRAY, fillalpha=0.12, label="")
        plot!(p, inf_s.mean_self, ribbon=inf_s.std_self,
            color=COL_BLUE, fillalpha=0.15, label="")
        # Accent: Relational Depth as the highlight
        plot!(p, rel_s.mean_self, ribbon=rel_s.std_self,
            color=COL_ACCENT, fillalpha=0.18, linewidth=2.5, label="")

        # Forced/probe boundary
        T_f = IFSV2Params().T_forced
        vline!(p, [T_f + 0.5], color=COL_GRID, linestyle=:dash, linewidth=1.0, label="")

        # Direct labels near the end of each line
        T_end = length(rel_s.mean_self)
        annotate!(p, T_end + 0.5, exp_s.mean_self[end],
            text("Exposure", 8, :left, COL_GRAY))
        annotate!(p, T_end + 0.5, inf_s.mean_self[end],
            text("Informational", 8, :left, COL_BLUE))
        annotate!(p, T_end + 0.5, rel_s.mean_self[end],
            text("Relational\nDepth", 8, :left, COL_ACCENT))

        # Annotate the depth gap
        gap_y = (rel_s.mean_self[end] + inf_s.mean_self[end]) / 2
        annotate!(p, T_end - 2, gap_y,
            text("depth gap", 7, :right, COL_ANNOTATION))

        savefig(p, joinpath(FIGURE_DIR, "ifs_v2_relational_depth_gap.png"))
        println("  saved ifs_v2_relational_depth_gap.png")
    end

    function save_self_energy_sweep(Es, mean_final, std_final)
        p = plot(
            Es,
            mean_final,
            ribbon=std_final,
            xlabel="Self-energy (E_t)",
            ylabel="Final P(capable / present)",
            title="Move 3 Emerges at E_t ~ 0.65",
            ylims=(0.0, 1.05),
            legend=false,
            color=COL_ACCENT,
            fillalpha=0.18,
            linewidth=2.5,
            grid=false,
            size=(750, 500),
            background_color=COL_BG,
            background_color_inside=COL_BG
        )
        # Annotate the emergence threshold around E_t ~ 0.65
        # Find where mean crosses 0.5
        cross_idx = findfirst(x -> x >= 0.5, mean_final)
        if !isnothing(cross_idx)
            cross_E = Es[cross_idx]
            vline!(p, [cross_E], color=COL_GRID, linestyle=:dot, linewidth=1.0, label="")
            annotate!(p, cross_E + 0.03, 0.55,
                text("onset ~ $(round(cross_E, digits=2))", 8, :left, COL_ANNOTATION))
        end
        savefig(p, joinpath(FIGURE_DIR, "ifs_v2_self_energy_sweep.png"))
        println("  saved ifs_v2_self_energy_sweep.png")
    end

    function save_h1_vs_h2(rel_h1::IFSV2Summary, rel_h2::IFSV2Summary, params::IFSV2Params)
        forced_boundary = params.T_forced
        fig = plot(
            plot_condition_strip(rel_h1, forced_boundary),
            plot_condition_heatmap(rel_h1, forced_boundary),
            plot_condition_strip(rel_h2, forced_boundary),
            plot_condition_heatmap(rel_h2, forced_boundary),
            layout=grid(4, 1, heights=[0.08, 0.42, 0.08, 0.42]),
            size=(1100, 950),
            plot_title="Cascade Requires Self-State Upstream (H1)",
            background_color=COL_BG
        )
        savefig(fig, joinpath(FIGURE_DIR, "ifs_v2_h1_vs_h2.png"))
        println("  saved ifs_v2_h1_vs_h2.png")
    end

    function save_free_choice_probe(main_lookup::Dict{String,IFSV2Summary})
        conditions = ["Exposure", "Informational", "Relational Depth"]
        colors = [COL_GRAY COL_BLUE COL_ACCENT]
        labels_ax = ["Avoid", "Inspect", "Stay"]
        final_probe = hcat([main_lookup[name].mean_probe_policy[:, end] for name in conditions]...)
        p = bar(
            labels_ax,
            final_probe,
            label=permutedims(conditions),
            color=colors,
            xlabel="",
            ylabel="Probability",
            title="Revised Beliefs Produce Different Behavior",
            ylims=(0.0, 1.05),
            legend=false,
            bar_width=0.7,
            grid=false,
            size=(750, 500),
            background_color=COL_BG,
            background_color_inside=COL_BG
        )
        # Direct labels above each group
        n_actions = length(labels_ax)
        n_conds = length(conditions)
        cond_labels_short = ["Exp", "Info", "Rel"]
        for (ci, cname) in enumerate(conditions)
            for ai in 1:n_actions
                val = final_probe[ai, ci]
                if val > 0.05
                    annotate!(p, ai + (ci - 2) * 0.25, val + 0.03,
                        text("$(round(val, digits=2))", 7, :center, colors[ci]))
                end
            end
        end
        savefig(p, joinpath(FIGURE_DIR, "ifs_v2_free_choice_probe.png"))
        println("  saved ifs_v2_free_choice_probe.png")
    end

    function save_focused_sensitivity(rows)
        param_names = [:lambda_witness_max, :alpha_witness, :beta_gamma_ratio, :policy_precision]
        param_display = Dict(
            :lambda_witness_max => "Witness precision cap",
            :alpha_witness => "Witness exponent",
            :beta_gamma_ratio => "Beta / gamma ratio",
            :policy_precision => "Policy precision"
        )
        panels = Any[]
        for parameter in param_names
            subset = filter(row -> row.parameter == parameter, rows)
            xs = [row.value for row in subset]
            rel = [row.relational_self for row in subset]
            gap = [row.self_gap for row in subset]
            probe = [row.probe_l1 for row in subset]
            ymax = max(1.0, maximum(probe))
            p = plot(
                xs, rel,
                color=COL_ACCENT, linewidth=2.0,
                xlabel=get(param_display, parameter, String(parameter)),
                ylabel="",
                title=get(param_display, parameter, String(parameter)),
                legend=false,
                ylims=(0.0, ymax + 0.05),
                grid=false,
                size=(600, 400),
                background_color=COL_BG,
                background_color_inside=COL_BG,
                label=""
            )
            plot!(p, xs, gap, color=COL_BLUE, linewidth=1.5, linestyle=:dash, label="")
            plot!(p, xs, probe, color=COL_GRAY, linewidth=1.5, linestyle=:dot, label="")
            # Pass/fail markers
            for row in subset
                mc = row.pass ? COL_ACCENT : COL_GRAY
                ms = row.pass ? :circle : :xcross
                scatter!(p, [row.value], [row.pass ? ymax - 0.02 : 0.02],
                    markersize=4, markercolor=mc, markershape=ms,
                    markerstrokewidth=0, label="")
            end
            # Direct labels at end of each series
            if length(xs) > 0
                annotate!(p, xs[end], rel[end] + 0.03,
                    text("self", 7, :left, COL_ACCENT))
                annotate!(p, xs[end], gap[end] + 0.03,
                    text("gap", 7, :left, COL_BLUE))
                annotate!(p, xs[end], probe[end] + 0.03,
                    text("probe", 7, :left, COL_GRAY))
            end
            push!(panels, p)
        end
        fig = plot(panels..., layout=(2, 2), size=(1200, 800),
            plot_title="Parameter Sensitivity: All Criteria Hold Across Ranges",
            background_color=COL_BG)
        savefig(fig, joinpath(FIGURE_DIR, "ifs_v2_focused_sensitivity.png"))
        println("  saved ifs_v2_focused_sensitivity.png")
    end

    function save_epistemic_by_channel(main_lookup::Dict{String,IFSV2Summary}, params::IFSV2Params)
        names = ["Exposure", "Informational", "Relational Depth"]
        panels = Any[]
        for (idx, name) in enumerate(names)
            payload = condition_decomposition_payload(main_lookup[name])
            ylabel = idx == 2 ? "Epistemic value" : ""
            push!(panels, plot_stacked_channel_panel(payload.epistemic_channels, name, params.T_forced; ylabel=ylabel))
        end
        fig = plot(
            panels...,
            layout=(3, 1),
            size=(900, 600),
            plot_title="What Is the Agent Curious About?",
            background_color=COL_BG,
        )
        savefig(fig, joinpath(FIGURE_DIR, "ifs_v2_epistemic_by_channel.png"))
        println("  saved ifs_v2_epistemic_by_channel.png")
    end

    function save_pragmatic_by_channel(main_lookup::Dict{String,IFSV2Summary}, params::IFSV2Params)
        names = ["Exposure", "Informational", "Relational Depth"]
        panels = Any[]
        for (idx, name) in enumerate(names)
            payload = condition_decomposition_payload(main_lookup[name])
            ylabel = idx == 2 ? "Pragmatic value" : ""
            push!(panels, plot_stacked_channel_panel(payload.pragmatic_channels, name, params.T_forced; ylabel=ylabel))
        end
        fig = plot(
            panels...,
            layout=(3, 1),
            size=(900, 600),
            plot_title="What Drives Action?",
            background_color=COL_BG,
        )
        savefig(fig, joinpath(FIGURE_DIR, "ifs_v2_pragmatic_by_channel.png"))
        println("  saved ifs_v2_pragmatic_by_channel.png")
    end

    function save_efe_decomposition(main_lookup::Dict{String,IFSV2Summary}, params::IFSV2Params)
        names = ["Exposure", "Informational", "Relational Depth"]
        panels = Any[]
        for (idx, name) in enumerate(names)
            payload = condition_decomposition_payload(main_lookup[name])
            ylabel = idx == 2 ? "Component value" : ""
            push!(panels, plot_decomposition_line_panel(payload.pragmatic, payload.epistemic, name, params.T_forced; ylabel=ylabel))
        end
        fig = plot(
            panels...,
            layout=(3, 1),
            size=(900, 600),
            plot_title="Pragmatic vs Epistemic Over Time",
            background_color=COL_BG,
        )
        savefig(fig, joinpath(FIGURE_DIR, "ifs_v2_efe_decomposition.png"))
        println("  saved ifs_v2_efe_decomposition.png")
    end

    function save_witnessing_onset(summary::IFSV2Summary)
        x = forced_time_axis(summary)
        E_series = forced_E_series(summary)
        channel5, channel5_std = forced_step_series(summary, step -> step.efe_epistemic_channels[5])
        ymax = max(maximum(vcat(channel5 .+ channel5_std, E_series)) * 1.10, 1.0)

        p = plot(
            x,
            channel5,
            ribbon=channel5_std,
            color=COL_ACCENT,
            fillalpha=0.12,
            linewidth=2.6,
            label="",
            title="Self-Curiosity Emerges at Relational Depth",
            xlabel="Time step",
            ylabel="Channel 5 epistemic value",
            legend=false,
            size=(750, 500),
            grid=false,
            background_color=COL_BG,
            background_color_inside=COL_BG,
        )
        plot!(
            p,
            x,
            E_series,
            color=COL_ANNOTATION,
            linewidth=1.6,
            linestyle=:dash,
            alpha=0.9,
            label="",
        )
        ylims!(p, (0.0, ymax))
        xlims!(p, (1.0, length(x) + 4.0))

        onset = onset_index(channel5; min_fraction=0.10, floor=0.01)
        if !isnothing(onset)
            onset_E = E_series[onset]
            vline!(p, [onset], color=COL_ACCENT, linestyle=:dot, linewidth=1.1, alpha=0.8, label="")
            scatter!(p, [onset], [channel5[onset]], markersize=4, markercolor=COL_ACCENT, markerstrokewidth=0, label="")
            annotate!(
                p,
                onset + 0.5,
                min(ymax * 0.92, channel5[onset] + 0.15 * ymax),
                text("onset\nE_t ≈ $(round(onset_E, digits=2))", 8, :left, COL_ACCENT),
            )
            annotate!(p, max(3, onset - 3), ymax * 0.07, text("captured", 8, :center, COL_GRAY))
            annotate!(p, min(length(x) - 3, onset + 6), ymax * 0.90, text("witnessing", 8, :center, COL_ACCENT))
        end

        annotate!(p, x[end] + 0.6, channel5[end], text("Channel 5", 8, :left, COL_ACCENT))
        annotate!(p, x[end] + 0.6, E_series[end], text("Self-energy E_t", 8, :left, COL_ANNOTATION))

        savefig(p, joinpath(FIGURE_DIR, "ifs_v2_witnessing_onset.png"))
        println("  saved ifs_v2_witnessing_onset.png")
    end

    function save_epistemic_emergence(summary::IFSV2Summary)
        series = forced_channel_series(summary, step -> step.efe_epistemic_channels)
        x = forced_time_axis(summary)
        E_series = forced_E_series(summary)
        total = vec(sum(series; dims=1))
        ymax = max(maximum(total) * 1.10, 1e-3)

        p = plot(
            title="What the Agent Is Curious About Shifts as Self-Energy Rises",
            xlabel="Time step",
            ylabel="Epistemic value",
            legend=:topleft,
            legendfontsize=7,
            legendbackground=RGBA(1, 1, 0.973, 0.85),
            size=(750, 500),
            grid=false,
            background_color=COL_BG,
            background_color_inside=COL_BG,
        )

        # Stacked areas with legend labels
        lower = zeros(Float64, length(x))
        for g in 1:5
            upper = lower .+ vec(series[g, :])
            plot!(
                p,
                x,
                upper,
                fillrange=lower,
                fillalpha=g == 5 ? 0.92 : 0.82,
                color=COL_CHANNELS[g],
                linecolor=COL_CHANNELS[g],
                linewidth=g == 5 ? 1.8 : 1.1,
                label=CHANNEL_LABELS[g],
            )
            lower = upper
        end

        # E_t overlay on secondary y-axis (scaled to fit)
        E_scaled = E_series .* ymax
        plot!(p, x, E_scaled,
            color=:black, linewidth=1.5, linestyle=:dash, alpha=0.5,
            label="Self-energy (E_t)",
        )

        ylims!(p, (0.0, ymax))
        xlims!(p, (1.0, length(x) + 4.0))

        onset = onset_index(vec(series[5, :]); min_fraction=0.10, floor=0.01)
        if !isnothing(onset)
            vline!(p, [onset], color=COL_ACCENT, linestyle=:dot, linewidth=1.1, alpha=0.8, label="")
            annotate!(p, onset + 0.5, min(ymax * 0.95, total[onset] + 0.10 * ymax), text("onset", 8, :left, COL_ACCENT))
            annotate!(p, max(4, onset - 3), ymax * 0.14, text("captured", 8, :center, COL_GRAY))
            annotate!(p, min(length(x) - 3, onset + 6), ymax * 0.95, text("witnessing", 8, :center, COL_ACCENT))
        end

        savefig(p, joinpath(FIGURE_DIR, "ifs_v2_epistemic_emergence.png"))
        println("  saved ifs_v2_epistemic_emergence.png")
    end

    function save_motivation_fingerprint(main_lookup::Dict{String,IFSV2Summary}, params::IFSV2Params)
        names = ["Exposure", "Informational", "Relational Depth"]
        actions = [IFSV2_POLICY_AVOID, IFSV2_POLICY_INSPECT, IFSV2_POLICY_STAY]
        panels = Any[]
        for action in actions
            for (idx, name) in enumerate(names)
                title_text = action == IFSV2_POLICY_AVOID ? name : ""
                ylabel = idx == 1 ? ACTION_LABELS[action] : ""
                annotate_components = action == IFSV2_POLICY_STAY && name == "Relational Depth"
                push!(panels, plot_action_fingerprint_panel(
                    main_lookup[name],
                    action,
                    params.T_forced;
                    title_text=title_text,
                    ylabel=ylabel,
                    annotate_components=annotate_components,
                ))
            end
        end
        fig = plot(
            panels...,
            layout=(3, 3),
            size=(1500, 1000),
            plot_title="Why the Agent Switches Actions",
            background_color=COL_BG,
        )
        savefig(fig, joinpath(FIGURE_DIR, "ifs_v2_motivation_fingerprint.png"))
        println("  saved ifs_v2_motivation_fingerprint.png")
    end
end

println("=" ^ 72)
println("IFS v2 Three-Move Simulation")
println("=" ^ 72)

params = IFSV2Params()

println("\nRegistered parameters")
println("  T_forced = $(params.T_forced), T_probe = $(params.T_probe)")
println("  beta_se = $(params.beta_se), gamma_se = $(params.gamma_se)")
println("  pi_part = $(params.pi_part), lambda_ctx = $(params.lambda_ctx)")
println("  lambda_witness_max = $(params.lambda_witness_max), alpha_witness = $(params.alpha_witness), witness_floor = $(params.lambda_witness_floor)")
println("  witness_to_info_ratio = $(params.witness_to_info_ratio), info_to_external_ratio = $(params.info_to_external_ratio)")

print_matrix_validation(params)
print_single_trial_debug(params)

println("\nRunning H1 conditions ($N_REPS replications each)")
h1_summaries = run_ifs_v2_suite(
    architecture=:H1,
    configs=all_ifs_v2_configs(params),
    params=params,
    n_replications=N_REPS,
    seed=SEED
)
h1_lookup = summary_by_name(h1_summaries)

for summary in h1_summaries
    print_condition_summary(summary)
end

println("\nRunning H2 structural control")
h2_relational = run_ifs_v2_replications(
    architecture=:H2,
    config=relational_depth_ifs_v2_config(params),
    params=params,
    n_replications=N_REPS,
    seed=SEED + 1000
)
print_condition_summary(h2_relational)

println("\nSelf-energy sweep ($SWEEP_REPS replications per level)")
Es, sweep_mean, sweep_std = build_sweep_summary(params; architecture=:H1, n_replications=SWEEP_REPS)
println("  sweep endpoints   = E=0.0 -> $(round(first(sweep_mean), digits=3)), E=1.0 -> $(round(last(sweep_mean), digits=3))")

onset_config = witnessing_onset_ifs_v2_config(params)
onset_reps = max(N_REPS, 60)
println("\nWitnessing onset ramp ($onset_reps replications, $(onset_config.T_forced) forced steps)")
onset_summary = run_ifs_v2_replications(
    architecture=:H1,
    config=onset_config,
    params=params,
    n_replications=onset_reps,
    seed=SEED + 1500
)
onset_channel5, _ = forced_step_series(onset_summary, step -> step.efe_epistemic_channels[5])
onset_E = forced_E_series(onset_summary)
onset_t = onset_index(onset_channel5; min_fraction=0.10, floor=0.01)
if !isnothing(onset_t)
    println("  channel 5 onset  = t=$(onset_t), E_t=$(round(onset_E[onset_t], digits=3)), final=$(round(onset_channel5[end], digits=3))")
end

println("\nParameter sensitivity ($SENS_REPS replications per perturbation)")
sensitivity_rows = run_ifs_v2_sensitivity(
    architecture=:H1,
    params=params,
    n_replications=SENS_REPS,
    seed=SEED + 2000
)
print_sensitivity_summary(sensitivity_rows)

println("\nFocused sensitivity ($FOCUSED_REPS replications per value)")
focused_rows = run_focused_sensitivity(params; n_replications=FOCUSED_REPS, seed=SEED + 3000)
print_focused_sensitivity(focused_rows)

criteria, probe_l1 = evaluate_success_criteria(h1_lookup, h2_relational, sensitivity_rows)
print_success_criteria(criteria, probe_l1)

println("\nParameter dependence")
for row in summarize_parameter_dependence(focused_rows)
    label = row.pass_rate == 1.0 ? "can vary freely" : row.pass_rate >= 0.5 ? "moderately constrained" : "most constraining"
    println("  $(row.parameter): $label (pass_rate=$(round(row.pass_rate, digits=2)), rel_span=$(round(row.rel_span, digits=3)), gap_span=$(round(row.gap_span, digits=3)))")
end

if ENABLE_FIGURES
    println("\nGenerating figures")
    main_summaries = [h1_lookup["Exposure"], h1_lookup["Informational"], h1_lookup["Relational Depth"]]
    save_one_figure(main_summaries, params)
    save_relational_depth_gap(h1_lookup)
    save_self_energy_sweep(Es, sweep_mean, sweep_std)
    save_h1_vs_h2(h1_lookup["Relational Depth"], h2_relational, params)
    save_free_choice_probe(h1_lookup)
    save_focused_sensitivity(focused_rows)
    save_epistemic_by_channel(h1_lookup, params)
    save_pragmatic_by_channel(h1_lookup, params)
    save_efe_decomposition(h1_lookup, params)
    save_witnessing_onset(onset_summary)
    save_epistemic_emergence(onset_summary)
    try
        save_motivation_fingerprint(h1_lookup, params)
    catch e
        println("  skipped motivation fingerprint: $(e)")
    end
else
    println("\nSkipping figure generation because IFS_V2_SKIP_FIGURES=1")
end

println("\nDone.")
