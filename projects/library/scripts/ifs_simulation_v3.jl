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
    const COL_BG = RGB(0.99, 0.98, 0.95)
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
        framestyle=:semi,
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

function build_main_figure(params::IFSV3Params, summaries::Dict{String,IFSV3Summary})
    !ENABLE_FIGURES && return nothing
    xs = collect(training_ix(params))
    probe_x = ["H1-highE", "H2-highE", "H1-lowE"]
    colors = [COL_H1, COL_H2, COL_LOW]

    p_left = plot(title="Dog Training", xlabel="Training trial", ylabel="Probability")
    for (name, color) in zip(probe_x, colors)
        summary = summaries[name]
        plot!(p_left, xs, summary.mean_pD_self_resourced[xs], color=color, label="$(name) self", linestyle=:solid)
        plot!(p_left, xs, summary.mean_pD_dog_safe[xs], color=color, label="$(name) dog threat", linestyle=:dash)
    end
    hline!(p_left, [0.5], color=:black, alpha=0.15, linestyle=:dot, label="")

    p_right = bar(
        probe_x,
        [summaries[name].mean_contact[first_probe_ix(params)] for name in probe_x];
        color=colors,
        legend=false,
        ylabel="P(contact)",
        title="First Cat Probe",
        ylim=(0, 1),
    )

    fig = plot(p_left, p_right; layout=(1, 2), size=(1100, 450))
    savefig(fig, joinpath(FIGURE_DIR, "ifs_generalization_main_v3.png"))
    return nothing
end

function build_within_trial_figure(params::IFSV3Params)
    !ENABLE_FIGURES && return nothing
    model = build_ifs_v3_model(architecture=:H1, params=params)
    pD_self, pD_dog, pD_cat = initial_ifs_v3_banks(params)
    trial = run_ifs_v3_trial!(
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
            false,
            false,
            true,
            :self,
        );
        trial_index=1,
        phase=:training,
        rng=MersenneTwister(SEED),
    )

    steps = 1:3
    labels = ["Prior", "After self", "After outcome"]
    self_vals = [trial.p_self_resourced_prior, trial.p_self_resourced_after_self, trial.p_self_resourced_final]
    threat_vals = [trial.p_threat_safe_prior, trial.p_threat_safe_after_self, trial.p_threat_safe_final]

    p = plot(steps, self_vals; label="P(resourced self)", marker=:circle, color=COL_H1,
        xticks=(steps, labels), ylabel="Posterior", xlabel="Inference stage",
        title="Within-Trial Cascade", ylim=(0, 1))
    plot!(p, steps, threat_vals; label="P(safe threat)", marker=:diamond, color=COL_H2)
    savefig(p, joinpath(FIGURE_DIR, "ifs_generalization_within_trial_v3.png"))
    return nothing
end

function build_ablation_figure(params::IFSV3Params, summaries::Dict{String,IFSV3Summary}, ablation::IFSV3Summary)
    !ENABLE_FIGURES && return nothing
    labels = ["H1-highE", "H1-highE η_self=0", "H2-highE"]
    vals = [
        summaries["H1-highE"].mean_contact[first_probe_ix(params)],
        ablation.mean_contact[first_probe_ix(params)],
        summaries["H2-highE"].mean_contact[first_probe_ix(params)],
    ]
    p = bar(labels, vals; color=[COL_H1, RGB(0.55, 0.55, 0.55), COL_H2], ylim=(0, 1),
        ylabel="P(contact)", title="Self-Learning Necessity")
    savefig(p, joinpath(FIGURE_DIR, "ifs_generalization_self_learning_necessity_v3.png"))
    return nothing
end

function build_specificity_figure(params::IFSV3Params, summaries::Dict{String,IFSV3Summary})
    !ENABLE_FIGURES && return nothing
    labels = ["H1-highE", "H2-highE", "H1-lowE"]
    pre = fill(normalize_prob([params.pD_threat_dangerous, params.pD_threat_safe])[2], 3)
    post = [summaries[name].runs[1].pD_threat_cat_final[2] for name in labels]

    p = plot(title="Stimulus Specificity", xlabel="Condition", ylabel="P(cat safe prior)", ylim=(0, 1))
    scatter!(p, labels, pre; label="Before dog training", color=:black, marker=:circle)
    scatter!(p, labels, post; label="After dog training", color=COL_LOW, marker=:diamond)
    for i in eachindex(labels)
        plot!(p, [labels[i], labels[i]], [pre[i], post[i]]; color=:black, alpha=0.25, label="")
    end
    savefig(p, joinpath(FIGURE_DIR, "ifs_generalization_stimulus_specificity_v3.png"))
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
    build_within_trial_figure(params)
    build_ablation_figure(params, summaries, ablation)
    build_specificity_figure(params, summaries)

    println("\nStep 7: Figures")
    if ENABLE_FIGURES
        println("  saved: " * joinpath(FIGURE_DIR, "ifs_generalization_main_v3.png"))
        println("  saved: " * joinpath(FIGURE_DIR, "ifs_generalization_within_trial_v3.png"))
        println("  saved: " * joinpath(FIGURE_DIR, "ifs_generalization_self_learning_necessity_v3.png"))
        println("  saved: " * joinpath(FIGURE_DIR, "ifs_generalization_stimulus_specificity_v3.png"))
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
