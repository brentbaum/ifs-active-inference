"""
    ifs_simulation_v3.jl - IFS Generalization Simulation

Usage:
    cd projects/library
    julia --project=. scripts/ifs_simulation_v3.jl

Environment flags:
    IFS_V3_N_REPS=60        Replications for main conditions
    IFS_V3_SENS_REPS=50     Replications per sensitivity variant
    IFS_V3_SKIP_FIGURES=1   Run numeric verification only
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

module IFSV3ScriptSupport
using LinearAlgebra
using Random
using Statistics

include(joinpath(@__DIR__, "..", "src", "active_inference", "core.jl"))
include(joinpath(@__DIR__, "..", "src", "active_inference", "ifs_model_v3.jl"))
end

using .IFSV3ScriptSupport
using .IFSV3ScriptSupport:
    IFSV3Params,
    IFSV3ConditionConfig,
    IFSV3TrialConfig,
    IFSV3Model,
    IFSV3Summary,
    IFSV3Run,
    IFSV3TrialResult,
    IFSV3_CHANNEL_CUE,
    IFSV3_CHANNEL_SELF,
    IFSV3_CHANNEL_OUTCOME,
    IFSV3_SELF_HELPLESS,
    IFSV3_SELF_RESOURCED,
    IFSV3_THREAT_SAFE,
    IFSV3_THREAT_DANGEROUS,
    IFSV3_STIMULUS_DOG,
    IFSV3_STIMULUS_CAT,
    IFSV3_POLICY_CONTACT,
    build_ifs_v3_model,
    build_ifs_v3_A_self,
    build_ifs_v3_A_outcome,
    build_ifs_v3_B,
    validate_ifs_v3_matrices,
    override_ifs_v3_params,
    compute_ifs_v3_precisions,
    ifs_v3_h1_highE_config,
    ifs_v3_h2_highE_config,
    ifs_v3_h1_lowE_config,
    main_ifs_v3_configs,
    initial_ifs_v3_banks,
    normalize_prob,
    run_ifs_v3_trial!,
    run_ifs_v3_condition,
    run_ifs_v3_replications,
    run_ifs_v3_suite,
    cue_label
using Random
using Statistics

const ENABLE_FIGURES = get(ENV, "IFS_V3_SKIP_FIGURES", "0") != "1"

if ENABLE_FIGURES
    ENV["GKSwstype"] = "100"
    ENV["GKS_NO_GUI"] = "1"
    using Plots

    const COL_H1 = RGB(0.72, 0.31, 0.22)
    const COL_H2 = RGB(0.22, 0.43, 0.66)
    const COL_LOW = RGB(0.48, 0.52, 0.34)
    const COL_SELF = RGB(0.74, 0.31, 0.23)
    const COL_OUTCOME = RGB(0.23, 0.44, 0.68)
    const COL_CUE = RGB(0.62, 0.62, 0.58)
    const COL_PRAGMATIC = RGB(0.23, 0.45, 0.69)
    const COL_EPISTEMIC = RGB(0.72, 0.31, 0.22)
    const COL_AMBIGUITY = RGB(0.76, 0.67, 0.28)
    const COL_ENERGY = RGB(0.15, 0.15, 0.15)
    const COL_BG = RGB(1.0, 1.0, 0.973)
    const COL_GRID = RGB(0.84, 0.84, 0.82)

    default(
        fontfamily="Georgia",
        linewidth=2.2,
        legendfontsize=8,
        guidefontsize=10,
        tickfontsize=8,
        titlefontsize=11,
        dpi=250,
        grid=false,
        framestyle=:axes,
        background_color=COL_BG,
        background_color_inside=COL_BG,
        foreground_color_grid=COL_GRID,
        size=(900, 520),
    )
end

const FIGURE_DIR = joinpath(@__DIR__, "..", "..", "ifs-paper", "figures", "v3")
mkpath(FIGURE_DIR)

const N_REPS = parse(Int, get(ENV, "IFS_V3_N_REPS", "60"))
const SENS_REPS = parse(Int, get(ENV, "IFS_V3_SENS_REPS", "50"))
const SEED = 42
const V3_CHANNEL_LABELS = ["Cue", "Self evidence", "Outcome"]
const V3_CHANNEL_COLORS = if ENABLE_FIGURES
    [COL_CUE, COL_SELF, COL_OUTCOME]
else
    Any[]
end

summary_by_name(summaries) = Dict(summary.condition => summary for summary in summaries)

training_ix(params::IFSV3Params) = 1:params.n_training_trials
probe_ix(params::IFSV3Params) = (params.n_training_trials + 1):(params.n_training_trials + params.n_probe_trials)
first_probe_ix(params::IFSV3Params) = params.n_training_trials + 1

function swapped_condition(config::IFSV3ConditionConfig)
    return IFSV3ConditionConfig(
        config.name * "-counterbalanced",
        config.architecture,
        config.E_t,
        config.learn_self,
        config.learn_threat,
        IFSV3_STIMULUS_CAT,
        IFSV3_STIMULUS_DOG,
        config.n_training_trials,
        config.n_probe_trials,
    )
end

function print_matrix_validation(params::IFSV3Params)
    model_h1 = build_ifs_v3_model(architecture=:H1, params=params)
    model_h2 = build_ifs_v3_model(architecture=:H2, params=params)
    println("Step 1: Matrix validation")
    println("  H1 matrices valid: $(validate_ifs_v3_matrices(model_h1.A_self, model_h1.A_outcome_contact, model_h1.A_outcome_avoid, model_h1.B_self, model_h1.B_threat))")
    println("  H2 matrices valid: $(validate_ifs_v3_matrices(model_h2.A_self, model_h2.A_outcome_contact, model_h2.A_outcome_avoid, model_h2.B_self, model_h2.B_threat))")
end

function print_single_trial_debug(params::IFSV3Params)
    println("\nStep 2: Single-trial debug (H1-highE, dog)")
    model = build_ifs_v3_model(architecture=:H1, params=params)
    pD_self, pD_dog, pD_cat = initial_ifs_v3_banks(params)
    _ = run_ifs_v3_trial!(
        model,
        pD_self,
        pD_dog,
        pD_cat,
        IFSV3TrialConfig(
            IFSV3_STIMULUS_DOG,
            params.high_E,
            IFSV3_POLICY_CONTACT,
            IFSV3_SELF_RESOURCED,
            IFSV3_THREAT_SAFE,
            true,
            true,
            false,
            :self,
        );
        trial_index=1,
        phase=:training,
        rng=MersenneTwister(SEED),
        verbose=true,
    )
    return nothing
end

function print_single_condition_check(summary::IFSV3Summary, params::IFSV3Params)
    println("\nStep 3: Single-condition dog training check (H1-highE)")
    self_delta = summary.mean_pD_self_resourced[params.n_training_trials] - summary.mean_pD_self_resourced[1]
    dog_delta = summary.mean_pD_dog_safe[params.n_training_trials] - summary.mean_pD_dog_safe[1]
    println("  ΔP(resourced self) over dog training = $(round(self_delta, digits=3))")
    println("  ΔP(safe dog) over dog training       = $(round(dog_delta, digits=3))")
    println("  final dog P(contact)                 = $(round(summary.mean_contact[params.n_training_trials], digits=3))")
end

function print_three_condition_gap(summaries::Dict{String,IFSV3Summary}, params::IFSV3Params)
    h1 = summaries["H1-highE"]
    h2 = summaries["H2-highE"]
    low = summaries["H1-lowE"]
    i_probe = first_probe_ix(params)
    println("\nStep 4: Three-condition transfer check")
    println("  first cat probe H1-highE = $(round(h1.mean_contact[i_probe], digits=3))")
    println("  first cat probe H2-highE = $(round(h2.mean_contact[i_probe], digits=3))")
    println("  first cat probe H1-lowE  = $(round(low.mean_contact[i_probe], digits=3))")
end

function print_matched_fit(summaries::Dict{String,IFSV3Summary}, params::IFSV3Params)
    h1 = summaries["H1-highE"]
    h2 = summaries["H2-highE"]
    dog_gap = abs(mean(h1.mean_contact[params.n_training_trials-4:params.n_training_trials]) -
                  mean(h2.mean_contact[params.n_training_trials-4:params.n_training_trials]))
    traj_gap = mean(abs.(h1.mean_contact[training_ix(params)] .- h2.mean_contact[training_ix(params)]))
    println("\nStep 5: H1 vs H2 matched dog fit")
    println("  final-5 dog gap       = $(round(dog_gap, digits=3))")
    println("  mean dog trajectory gap = $(round(traj_gap, digits=3))")
end

pairwise_l1(a::AbstractVector{<:Real}, b::AbstractVector{<:Real}) = sum(abs.(Float64.(a) .- Float64.(b)))

function criterion_row(name::String, passed::Bool, detail::String)
    return (name=name, passed=passed, detail=detail)
end

function evaluate_success_criteria(
    params::IFSV3Params,
    summaries::Dict{String,IFSV3Summary},
    ablation::IFSV3Summary,
)
    h1 = summaries["H1-highE"]
    h2 = summaries["H2-highE"]
    low = summaries["H1-lowE"]
    i_train = params.n_training_trials
    i_probe = first_probe_ix(params)

    dog_gap = abs(mean(h1.mean_contact[i_train-4:i_train]) - mean(h2.mean_contact[i_train-4:i_train]))
    h1_self_delta = h1.mean_pD_self_resourced[i_train] - h1.mean_pD_self_resourced[1]
    h1_dog_delta = h1.mean_pD_dog_safe[i_train] - h1.mean_pD_dog_safe[1]
    h2_dog_delta = h2.mean_pD_dog_safe[i_train] - h2.mean_pD_dog_safe[1]
    low_self_delta = low.mean_pD_self_resourced[i_train] - low.mean_pD_self_resourced[1]
    cat_gap_h1_h2 = h1.mean_contact[i_probe] - h2.mean_contact[i_probe]
    cat_gap_h1_low = h1.mean_contact[i_probe] - low.mean_contact[i_probe]
    cat_shift = mean(run.pD_threat_cat_l1_shift for run in h1.runs)
    ablation_gap_to_h2 = abs(ablation.mean_contact[i_probe] - h2.mean_contact[i_probe])
    ablation_drop = h1.mean_contact[i_probe] - ablation.mean_contact[i_probe]

    return [
        criterion_row(
            "1. Matched dog fit",
            dog_gap < 0.10,
            "|Δ final-5 dog contact| = $(round(dog_gap, digits=3))",
        ),
        criterion_row(
            "2. Shared-self revision",
            h1_self_delta > 0.25,
            "ΔP(resourced self)_H1-highE = $(round(h1_self_delta, digits=3))",
        ),
        criterion_row(
            "3. Threat-dog revision",
            h1_dog_delta > 0.25 && h2_dog_delta > 0.25,
            "ΔP(safe dog)_H1 = $(round(h1_dog_delta, digits=3)), H2 = $(round(h2_dog_delta, digits=3))",
        ),
        criterion_row(
            "4. Low-E blockade",
            low_self_delta < 0.10,
            "ΔP(resourced self)_H1-lowE = $(round(low_self_delta, digits=3))",
        ),
        criterion_row(
            "5. Cat transfer discriminant",
            cat_gap_h1_h2 > 0.20 && cat_gap_h1_low > 0.20,
            "H1-H2 gap = $(round(cat_gap_h1_h2, digits=3)); H1-low gap = $(round(cat_gap_h1_low, digits=3))",
        ),
        criterion_row(
            "6. Stimulus specificity",
            cat_shift < 0.05,
            "mean L1 shift in D_threat_cat = $(round(cat_shift, digits=4))",
        ),
        criterion_row(
            "7. Self-learning necessity",
            ablation_gap_to_h2 < 0.10 && ablation_drop > 0.20,
            "η_self=0 vs H2 gap = $(round(ablation_gap_to_h2, digits=3)); H1 drop = $(round(ablation_drop, digits=3))",
        ),
    ]
end

function run_fake_content_test(params::IFSV3Params)
    config = ifs_v3_h1_highE_config(params)
    summary = run_ifs_v3_replications(
        condition=config,
        params=params,
        n_replications=N_REPS,
        seed=SEED + 900,
        train_self_channel_mode=:threat,
        probe_self_channel_mode=:self,
    )
    i_train = params.n_training_trials
    i_probe = first_probe_ix(params)
    dog_final = mean(summary.mean_contact[i_train-4:i_train])
    cat_probe = summary.mean_contact[i_probe]
    passed = dog_final > 0.65 && cat_probe < 0.40
    return criterion_row(
        "A1. Fake-content test",
        passed,
        "dog final-5 = $(round(dog_final, digits=3)); first cat probe = $(round(cat_probe, digits=3))",
    ), summary
end

function run_counterbalanced_test(params::IFSV3Params, reference_h1::IFSV3Summary)
    config = swapped_condition(ifs_v3_h1_highE_config(params))
    summary = run_ifs_v3_replications(
        condition=config,
        params=params,
        n_replications=N_REPS,
        seed=SEED + 1000,
    )
    i_probe = first_probe_ix(params)
    reversed_gap = abs(summary.mean_contact[i_probe] - reference_h1.mean_contact[i_probe])
    passed = reversed_gap < 0.10
    return criterion_row(
        "A2. Counterbalanced training",
        passed,
        "first dog probe after cat training = $(round(summary.mean_contact[i_probe], digits=3)); symmetry gap = $(round(reversed_gap, digits=3))",
    ), summary
end

function run_real_danger_probe_test(params::IFSV3Params)
    config = ifs_v3_h1_highE_config(params)
    summary = run_ifs_v3_replications(
        condition=config,
        params=params,
        n_replications=N_REPS,
        seed=SEED + 1100,
        probe_actual_self=IFSV3_SELF_HELPLESS,
        probe_actual_threat=IFSV3_THREAT_DANGEROUS,
        probe_self_channel_mode=:threat,
    )
    i_probe = first_probe_ix(params)
    passed = summary.mean_contact[i_probe] < 0.40
    return criterion_row(
        "A3. Real-danger probe",
        passed,
        "first dangerous-cat probe P(contact) = $(round(summary.mean_contact[i_probe], digits=3)) with explicit danger cue",
    ), summary
end

function run_sensitivity_test(params::IFSV3Params)
    variants = [
        (:eta_self, 0.8), (:eta_self, 1.2),
        (:pi_part, 0.8), (:pi_part, 1.2),
        (:lambda_self, 0.8), (:lambda_self, 1.2),
        (:high_E, 0.8), (:high_E, 1.2),
        (:low_E, 0.8), (:low_E, 1.2),
    ]

    rows = NamedTuple[]
    for (name, multiplier) in variants
        base = getfield(params, name)
        value = clamp(base * multiplier, 0.01, 0.99)
        varied = if name == :eta_self
            override_ifs_v3_params(params; eta_self=value)
        elseif name == :pi_part
            override_ifs_v3_params(params; pi_part=value)
        elseif name == :lambda_self
            override_ifs_v3_params(params; lambda_self=value)
        elseif name == :high_E
            override_ifs_v3_params(params; high_E=value)
        elseif name == :low_E
            override_ifs_v3_params(params; low_E=value)
        else
            error("Unhandled sensitivity parameter: $name")
        end
        summaries = summary_by_name(run_ifs_v3_suite(params=varied, n_replications=SENS_REPS, seed=SEED + Int(abs(hash((name, multiplier))) % 10^6)))
        h1 = summaries["H1-highE"]
        h2 = summaries["H2-highE"]
        low = summaries["H1-lowE"]
        i_train = varied.n_training_trials
        i_probe = first_probe_ix(varied)
        dog_gap = abs(mean(h1.mean_contact[i_train-4:i_train]) - mean(h2.mean_contact[i_train-4:i_train]))
        cat_gap = min(h1.mean_contact[i_probe] - h2.mean_contact[i_probe], h1.mean_contact[i_probe] - low.mean_contact[i_probe])
        push!(rows, (
            parameter=name,
            multiplier=multiplier,
            dog_gap=dog_gap,
            cat_gap=cat_gap,
            pass=(dog_gap < 0.13 && cat_gap > 0.12),
        ))
    end

    pass_count = count(row -> row.pass, rows)
    weakest_gap = minimum(row.cat_gap for row in rows)
    worst_fit = maximum(row.dog_gap for row in rows)
    return criterion_row(
        "A4. Sensitivity sweep",
        pass_count == length(rows),
        "passes $(pass_count)/$(length(rows)); weakest transfer gap = $(round(weakest_gap, digits=3)); worst dog gap = $(round(worst_fit, digits=3))",
    ), rows
end

function run_matched_fit_test(params::IFSV3Params, h1::IFSV3Summary, h2::IFSV3Summary)
    traj_gap = mean(abs.(h1.mean_contact[training_ix(params)] .- h2.mean_contact[training_ix(params)]))
    passed = traj_gap < 0.12
    return criterion_row(
        "A5. Matched-fit verification",
        passed,
        "mean |dog trajectory gap| = $(round(traj_gap, digits=3))",
    )
end

function print_criteria(title::String, rows)
    println("\n" * title)
    for row in rows
        status = row.passed ? "PASS" : "FAIL"
        println("  [$status] $(row.name): $(row.detail)")
    end
end

function action_field_symbol(kind::Symbol, action::Int)
    suffix = action == IFSV3_POLICY_CONTACT ? "contact" : "avoid"
    return Symbol("efe_", String(kind), "_", suffix)
end

function action_channels_field_symbol(kind::Symbol, action::Int)
    suffix = action == IFSV3_POLICY_CONTACT ? "contact" : "avoid"
    return Symbol("efe_", String(kind), "_channels_", suffix)
end

function mean_action_total_series(
    summary::IFSV3Summary,
    action::Int,
    kind::Symbol;
    trial_indices,
)
    values = zeros(Float64, length(trial_indices), length(summary.runs))
    field = action_field_symbol(kind, action)
    for (j, run) in enumerate(summary.runs)
        for (k, t) in enumerate(trial_indices)
            values[k, j] = getfield(run.trials[t], field)
        end
    end
    return vec(mean(values; dims=2))
end

function mean_action_channel_matrix(
    summary::IFSV3Summary,
    action::Int,
    kind::Symbol;
    trial_indices,
)
    values = zeros(Float64, 3, length(trial_indices), length(summary.runs))
    field = action_channels_field_symbol(kind, action)
    for (j, run) in enumerate(summary.runs)
        for (k, t) in enumerate(trial_indices)
            channel_values = getfield(run.trials[t], field)
            for g in 1:3
                values[g, k, j] = channel_values[g]
            end
        end
    end
    return dropdims(mean(values; dims=3), dims=3)
end

function mean_action_components_at_trial(summary::IFSV3Summary, action::Int, trial_index::Int)
    pragmatic = zeros(Float64, length(summary.runs))
    epistemic = zeros(Float64, length(summary.runs))
    ambiguity = zeros(Float64, length(summary.runs))
    efe = zeros(Float64, length(summary.runs))
    for (j, run) in enumerate(summary.runs)
        trial = run.trials[trial_index]
        pragmatic[j] = getfield(trial, action_field_symbol(:pragmatic, action))
        epistemic[j] = getfield(trial, action_field_symbol(:epistemic, action))
        ambiguity[j] = getfield(trial, action_field_symbol(:ambiguity, action))
        efe[j] = getfield(trial, action == IFSV3_POLICY_CONTACT ? :efe_contact : :efe_avoid)
    end
    return (
        pragmatic=mean(pragmatic),
        epistemic=mean(epistemic),
        ambiguity=mean(ambiguity),
        efe=mean(efe),
    )
end

function extend_for_labels(xs)
    return (first(xs), last(xs) + 2.0)
end

function label_series_end!(p, x, series::Vector{Float64}, label::String, color; dy::Float64=0.0)
    annotate!(p, x[end] + 0.45, series[end] + dy, text(label, 8, :left, color))
    return p
end

function build_main_figure(params::IFSV3Params, summaries::Dict{String,IFSV3Summary})
    !ENABLE_FIGURES && return nothing
    xs = collect(training_ix(params))
    panels = Plots.Plot[]
    offsets = [0.01, 0.03, -0.02]
    for name in ["H1-highE", "H2-highE", "H1-lowE"]
        summary = summaries[name]
        epistemic = mean_action_channel_matrix(summary, IFSV3_POLICY_CONTACT, :epistemic; trial_indices=xs)
        ymax = max(maximum(epistemic) * 1.12, 0.02)
        p = plot(
            title=name,
            xlabel="Training trial",
            ylabel=name == "H1-highE" ? "Epistemic value" : "",
            xlims=extend_for_labels(xs),
            ylims=(0.0, ymax),
            legend=false,
            size=(360, 340),
        )
        for g in 1:3
            series = vec(epistemic[g, :])
            plot!(p, xs, series; color=V3_CHANNEL_COLORS[g], linewidth=g == IFSV3_CHANNEL_SELF ? 2.8 : 2.0, label="")
            label_series_end!(p, xs, series, V3_CHANNEL_LABELS[g], V3_CHANNEL_COLORS[g]; dy=offsets[g])
        end
        push!(panels, p)
    end

    fig = plot(
        panels...;
        layout=(1, 3),
        size=(1180, 340),
        plot_title="What Is the Agent Curious About During Therapy?",
        plot_titlefontsize=13,
    )
    savefig(fig, joinpath(FIGURE_DIR, "ifs_v3_epistemic_channels_training.png"))
    return nothing
end

function build_within_trial_figure(params::IFSV3Params, h1::IFSV3Summary)
    !ENABLE_FIGURES && return nothing
    xs = collect(training_ix(params))
    self_series = h1.mean_pD_self_resourced[xs]
    E_series = fill(h1.E_t, length(xs))
    self_epistemic = vec(mean_action_channel_matrix(h1, IFSV3_POLICY_CONTACT, :epistemic; trial_indices=xs)[IFSV3_CHANNEL_SELF, :])
    ymax = max(maximum(vcat(self_series, E_series, self_epistemic)) * 1.12, 0.05)

    p = plot(
        xs,
        self_series;
        color=COL_SELF,
        linewidth=2.8,
        xlabel="Training trial",
        ylabel="Value",
        title="The Full Picture",
        xlims=extend_for_labels(xs),
        ylims=(0.0, ymax),
        legend=false,
        size=(900, 420),
    )
    plot!(p, xs, E_series; color=COL_ENERGY, linestyle=:dash, linewidth=1.8, alpha=0.75, label="")
    plot!(p, xs, self_epistemic; color=COL_EPISTEMIC, linewidth=2.4, label="")

    label_series_end!(p, xs, self_series, "P(resourced self)", COL_SELF; dy=0.01)
    label_series_end!(p, xs, E_series, "E_t", COL_ENERGY; dy=0.0)
    label_series_end!(p, xs, self_epistemic, "Self epistemic", COL_EPISTEMIC; dy=0.01)

    savefig(p, joinpath(FIGURE_DIR, "ifs_v3_full_picture_training.png"))
    return nothing
end

function build_ablation_figure(params::IFSV3Params, summaries::Dict{String,IFSV3Summary}, ablation::IFSV3Summary)
    !ENABLE_FIGURES && return nothing
    xs = collect(training_ix(params))
    panels = Plots.Plot[]
    for name in ["H1-highE", "H2-highE"]
        summary = summaries[name]
        pragmatic = mean_action_total_series(summary, IFSV3_POLICY_CONTACT, :pragmatic; trial_indices=xs)
        epistemic = vec(mean_action_channel_matrix(summary, IFSV3_POLICY_CONTACT, :epistemic; trial_indices=xs)[IFSV3_CHANNEL_SELF, :])
        ymax = max(maximum(vcat(pragmatic, epistemic)) * 1.12, 0.05)
        p = plot(
            xs,
            pragmatic;
            color=COL_PRAGMATIC,
            linewidth=2.6,
            xlabel="Training trial",
            ylabel=name == "H1-highE" ? "Expected value" : "",
            title=name,
            xlims=extend_for_labels(xs),
            ylims=(0.0, ymax),
            legend=false,
            size=(470, 360),
        )
        plot!(p, xs, epistemic; color=COL_EPISTEMIC, linewidth=2.4, label="")
        label_series_end!(p, xs, pragmatic, "Pragmatic", COL_PRAGMATIC; dy=0.01)
        label_series_end!(p, xs, epistemic, "Self epistemic", COL_EPISTEMIC; dy=-0.01)
        push!(panels, p)
    end

    fig = plot(
        panels...;
        layout=(1, 2),
        size=(980, 360),
        plot_title="Motivation Shifts as Self Revises",
        plot_titlefontsize=13,
    )
    savefig(fig, joinpath(FIGURE_DIR, "ifs_v3_motivation_shift_training.png"))
    return nothing
end

function build_specificity_figure(params::IFSV3Params, summaries::Dict{String,IFSV3Summary})
    !ENABLE_FIGURES && return nothing
    trial_ix = first_probe_ix(params)
    panels = Plots.Plot[]
    for name in ["H1-highE", "H2-highE"]
        summary = summaries[name]
        avoid = mean_action_components_at_trial(summary, IFSV3_POLICY_AVOID, trial_ix)
        contact = mean_action_components_at_trial(summary, IFSV3_POLICY_CONTACT, trial_ix)
        components = Dict(
            "Ambiguity" => ([avoid.ambiguity, contact.ambiguity], COL_AMBIGUITY),
            "Pragmatic" => ([avoid.pragmatic, contact.pragmatic], COL_PRAGMATIC),
            "Epistemic" => ([-avoid.epistemic, -contact.epistemic], COL_EPISTEMIC),
            "Total EFE" => ([avoid.efe, contact.efe], COL_ENERGY),
        )
        xmin = minimum(vcat([vals for (vals, _) in values(components)]...)) - 0.08
        xmax = maximum(vcat([vals for (vals, _) in values(components)]...)) + 0.12
        p = plot(
            title=name,
            xlabel="Contribution",
            ylabel="",
            yticks=([1, 2], ["Avoid", "Contact"]),
            xlims=(xmin, xmax),
            ylims=(0.5, 2.5),
            legend=false,
            size=(470, 320),
        )
        vline!(p, [0.0]; color=:black, alpha=0.15, linestyle=:dot, label="")
        for (i, total) in enumerate([avoid.efe, contact.efe])
            plot!(p, [0.0, total], [i, i]; color=:black, alpha=0.12, linewidth=1.0, label="")
        end
        for (label, (vals, color)) in components
            scatter!(p, vals, [1, 2]; color=color, markersize=5, markerstrokewidth=0, label="")
        end
        annotate!(p, contact.ambiguity, 2.18, text("Ambiguity", 8, :left, COL_AMBIGUITY))
        annotate!(p, contact.pragmatic, 2.03, text("Pragmatic", 8, :left, COL_PRAGMATIC))
        annotate!(p, -contact.epistemic, 1.88, text("-Epistemic", 8, :left, COL_EPISTEMIC))
        annotate!(p, contact.efe, 1.73, text("Total EFE", 8, :left, COL_ENERGY))
        winner = contact.efe < avoid.efe ? "Contact lower" : "Avoid lower"
        annotate!(p, xmax - 0.02, 2.32, text(winner, 8, :right, COL_ENERGY))
        push!(panels, p)
    end

    fig = plot(
        panels...;
        layout=(1, 2),
        size=(980, 320),
        plot_title="Why H1-highE Approaches Cat",
        plot_titlefontsize=13,
    )
    savefig(fig, joinpath(FIGURE_DIR, "ifs_v3_cat_probe_efe_decomposition.png"))
    return nothing
end

function run_all_outputs()
    params = IFSV3Params()

    print_matrix_validation(params)
    print_single_trial_debug(params)

    summaries = summary_by_name(run_ifs_v3_suite(params=params, n_replications=N_REPS, seed=SEED))
    print_single_condition_check(summaries["H1-highE"], params)
    print_three_condition_gap(summaries, params)
    print_matched_fit(summaries, params)

    ablation_params = override_ifs_v3_params(params; eta_self=0.0)
    ablation = run_ifs_v3_replications(
        condition=ifs_v3_h1_highE_config(ablation_params),
        params=ablation_params,
        n_replications=N_REPS,
        seed=SEED + 700,
    )

    success = evaluate_success_criteria(params, summaries, ablation)
    fake_row, fake_summary = run_fake_content_test(params)
    counter_row, counter_summary = run_counterbalanced_test(params, summaries["H1-highE"])
    danger_row, danger_summary = run_real_danger_probe_test(params)
    sensitivity_row, sensitivity_rows = run_sensitivity_test(params)
    matched_row = run_matched_fit_test(params, summaries["H1-highE"], summaries["H2-highE"])
    adversarial = [fake_row, counter_row, danger_row, sensitivity_row, matched_row]

    print_criteria("Step 6: Success criteria", success)
    print_criteria("Step 6: Adversarial tests", adversarial)

    println("\nSensitivity detail")
    for row in sensitivity_rows
        status = row.pass ? "PASS" : "FAIL"
        println("  [$status] $(row.parameter) x$(row.multiplier): dog gap=$(round(row.dog_gap, digits=3)), cat gap=$(round(row.cat_gap, digits=3))")
    end

    build_main_figure(params, summaries)
    build_within_trial_figure(params, summaries["H1-highE"])
    build_ablation_figure(params, summaries, ablation)
    build_specificity_figure(params, summaries)

    println("\nStep 7: Figures")
    if ENABLE_FIGURES
        println("  saved: " * joinpath(FIGURE_DIR, "ifs_v3_epistemic_channels_training.png"))
        println("  saved: " * joinpath(FIGURE_DIR, "ifs_v3_motivation_shift_training.png"))
        println("  saved: " * joinpath(FIGURE_DIR, "ifs_v3_full_picture_training.png"))
        println("  saved: " * joinpath(FIGURE_DIR, "ifs_v3_cat_probe_efe_decomposition.png"))
    else
        println("  skipped figure generation")
    end

    return (
        params=params,
        summaries=summaries,
        ablation=ablation,
        fake_summary=fake_summary,
        counter_summary=counter_summary,
        danger_summary=danger_summary,
        success=success,
        adversarial=adversarial,
        sensitivity=sensitivity_rows,
    )
end

run_all_outputs()
