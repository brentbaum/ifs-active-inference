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
    IFSV2_POLICY_INSPECT,
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
    informational_ifs_v2_config
using Statistics

const ENABLE_FIGURES = get(ENV, "IFS_V2_SKIP_FIGURES", "0") != "1"

if ENABLE_FIGURES
    ENV["GKSwstype"] = get(ENV, "GKSwstype", "100")
    using Plots

    default(
        fontfamily="Helvetica",
        titlefontsize=11,
        guidefontsize=10,
        tickfontsize=8,
        legendfontsize=8,
        linewidth=2.0,
        framestyle=:box,
        grid=true,
        gridalpha=0.15,
        dpi=300,
        size=(1000, 700)
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
            E_t,
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
            title=""
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
            xlabel="Time",
            title=summary.condition
        )
        vline!(p, [forced_boundary + 0.5], color=:white, linewidth=1.4, alpha=0.9)

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
        fig = plot(plots..., layout=layout, size=(1100, 1200), plot_title="Three-Move Cascade: H1")
        savefig(fig, joinpath(FIGURE_DIR, "ifs_v2_one_figure.png"))
        println("  saved ifs_v2_one_figure.png")
    end

    function save_relational_depth_gap(main_lookup::Dict{String,IFSV2Summary})
        p = plot(
            title="Relational Depth Gap",
            xlabel="Time",
            ylabel="P(capable/present)",
            ylims=(0.0, 1.0),
            legend=:bottomright
        )
        for name in ["Exposure", "Informational", "Relational Depth"]
            summary = main_lookup[name]
            plot!(p, summary.mean_self, ribbon=summary.std_self, label=name)
        end
        vline!(p, [IFSV2Params().T_forced + 0.5], color=:black, linestyle=:dash, alpha=0.5, label="")
        savefig(p, joinpath(FIGURE_DIR, "ifs_v2_relational_depth_gap.png"))
        println("  saved ifs_v2_relational_depth_gap.png")
    end

    function save_self_energy_sweep(Es, mean_final, std_final)
        p = plot(
            Es,
            mean_final,
            ribbon=std_final,
            xlabel="Self-energy (E_t)",
            ylabel="Final P(capable/present)",
            title="Self-Energy Sweep",
            ylims=(0.0, 1.0),
            label="H1"
        )
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
            plot_title="H1 vs H2 Under Relational Depth"
        )
        savefig(fig, joinpath(FIGURE_DIR, "ifs_v2_h1_vs_h2.png"))
        println("  saved ifs_v2_h1_vs_h2.png")
    end

    function save_free_choice_probe(main_lookup::Dict{String,IFSV2Summary})
        conditions = ["Exposure", "Informational", "Relational Depth"]
        labels = ["Avoid", "Inspect", "Stay"]
        final_probe = hcat([main_lookup[name].mean_probe_policy[:, end] for name in conditions]...)
        p = bar(
            labels,
            final_probe,
            label=conditions,
            xlabel="Probe Policy",
            ylabel="Probability",
            title="Free-Choice Probe",
            ylims=(0.0, 1.0)
        )
        savefig(p, joinpath(FIGURE_DIR, "ifs_v2_free_choice_probe.png"))
        println("  saved ifs_v2_free_choice_probe.png")
    end

    function save_focused_sensitivity(rows)
        params = [:lambda_witness_max, :alpha_witness, :beta_gamma_ratio, :policy_precision]
        panels = Any[]
        for parameter in params
            subset = filter(row -> row.parameter == parameter, rows)
            xs = [row.value for row in subset]
            rel = [row.relational_self for row in subset]
            gap = [row.self_gap for row in subset]
            probe = [row.probe_l1 for row in subset]
            p = plot(
                xs,
                rel,
                label="Relational self",
                xlabel=String(parameter),
                ylabel="Metric",
                title=String(parameter),
                legend=:best,
                ylims=(0.0, max(1.0, maximum(probe)))
            )
            plot!(p, xs, gap, label="Self gap")
            plot!(p, xs, probe, label="Probe L1")
            scatter!(p, xs, [row.pass ? 0.98 : 0.02 for row in subset], label="Pass", markersize=4)
            push!(panels, p)
        end
        fig = plot(panels..., layout=(2, 2), size=(1200, 800), plot_title="Focused Sensitivity")
        savefig(fig, joinpath(FIGURE_DIR, "ifs_v2_focused_sensitivity.png"))
        println("  saved ifs_v2_focused_sensitivity.png")
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
else
    println("\nSkipping figure generation because IFS_V2_SKIP_FIGURES=1")
end

println("\nDone.")
