"""
    ifs_polarization_simulation_v2.jl - Two-Part Polarization Simulation

Usage:
    cd projects/library
    julia --project=. scripts/ifs_polarization_simulation_v2.jl

Environment flags:
    IFS_POLARIZATION_V2_SKIP_FIGURES=1   Run numeric verification only
    IFS_POLARIZATION_V2_N_REPS=60        Replications for each main condition
    IFS_POLARIZATION_V2_SENS_REPS=50     Replications per +/-20% sensitivity run
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

module IFSPolarizationV2ScriptSupport
using LinearAlgebra
using Random
using Statistics

include(joinpath(@__DIR__, "..", "src", "active_inference", "core.jl"))
include(joinpath(@__DIR__, "..", "src", "active_inference", "inference.jl"))
include(joinpath(@__DIR__, "..", "src", "active_inference", "ifs_model_v2.jl"))
include(joinpath(@__DIR__, "..", "src", "active_inference", "ifs_polarization_v2.jl"))
end

using .IFSPolarizationV2ScriptSupport
using .IFSPolarizationV2ScriptSupport:
    IFSPolarizationV2Params,
    IFSPolarizationV2Summary,
    build_ifs_polarization_v2_model,
    low_ifs_polarization_v2_config,
    medium_ifs_polarization_v2_config,
    high_ifs_polarization_v2_config,
    oscillation_ifs_polarization_v2_config,
    resolution_ifs_polarization_v2_config,
    all_ifs_polarization_v2_configs,
    run_ifs_polarization_v2_condition,
    run_ifs_polarization_v2_suite,
    run_ifs_polarization_v2_sensitivity
using DelimitedFiles
using Statistics

const ENABLE_FIGURES = get(ENV, "IFS_POLARIZATION_V2_SKIP_FIGURES", "0") != "1"

if ENABLE_FIGURES
    ENV["GKSwstype"] = "100"
    ENV["MPLCONFIGDIR"] = get(ENV, "MPLCONFIGDIR", mktempdir())
end

const FIGURE_DIR = joinpath(@__DIR__, "..", "..", "ifs-paper", "figures", "v2")
mkpath(FIGURE_DIR)

const N_REPS = parse(Int, get(ENV, "IFS_POLARIZATION_V2_N_REPS", "60"))
const SENS_REPS = parse(Int, get(ENV, "IFS_POLARIZATION_V2_SENS_REPS", "50"))
const SEED = 42

summary_by_name(summaries) = Dict(summary.condition => summary for summary in summaries)

function print_condition_summary(summary::IFSPolarizationV2Summary)
    println("  $(summary.condition):")
    println("    final part A self    = $(round(summary.mean_part_a_self[end], digits=3)) ± $(round(summary.std_part_a_self[end], digits=3))")
    println("    final part B self    = $(round(summary.mean_part_b_self[end], digits=3)) ± $(round(summary.std_part_b_self[end], digits=3))")
    println("    final weights        = A $(round(summary.mean_weight_part_a[end], digits=3)), B $(round(summary.mean_weight_part_b[end], digits=3)), Self $(round(summary.mean_weight_self[end], digits=3))")
    println("    final behavior       = avoid $(round(summary.mean_behavior[1, end], digits=3)), approach $(round(summary.mean_behavior[2, end], digits=3)), flexible $(round(summary.mean_behavior[3, end], digits=3))")
    println("    switching rate       = $(round(summary.metric_means[:switching_rate], digits=3))")
    println("    flexible rate        = $(round(summary.metric_means[:flexible_rate], digits=3))")
    println("    dual cascade rate    = $(round(summary.metric_means[:dual_cascade_rate], digits=3))")
end

function print_sensitivity_summary(rows)
    red_flags = count(row ->
        row.low_switching < 0.20 ||
        row.medium_approach < 0.20 ||
        row.medium_flexible > 0.75 ||
        row.high_self_weight < 0.35 ||
        row.high_dual_cascade < 0.55,
        rows
    )

    println("\nSensitivity (+/-20%)")
    println("  runs checked      = $(length(rows))")
    println("  red flags         = $red_flags")
    println("  weakest low switch= $(round(minimum(row.low_switching for row in rows), digits=3))")
    println("  weakest med appr  = $(round(minimum(row.medium_approach for row in rows), digits=3))")
    println("  strongest med flex= $(round(maximum(row.medium_flexible for row in rows), digits=3))")
    println("  weakest high self = $(round(minimum(row.high_self_weight for row in rows), digits=3))")
    println("  weakest dual rate = $(round(minimum(row.high_dual_cascade for row in rows), digits=3))")
end

if ENABLE_FIGURES
    const FIGURE_DATA_DIR = mktempdir()

    function write_summary_table(summary::IFSPolarizationV2Summary, path::String)
        header = [
            "t", "E",
            "part_a_self", "part_a_self_std",
            "part_b_self", "part_b_self_std",
            "part_a_threat", "part_a_threat_std",
            "part_b_threat", "part_b_threat_std",
            "part_a_outcome", "part_a_outcome_std",
            "part_b_outcome", "part_b_outcome_std",
            "weight_part_a", "weight_part_a_std",
            "weight_part_b", "weight_part_b_std",
            "weight_self", "weight_self_std",
            "p_avoid", "p_avoid_std",
            "p_approach", "p_approach_std",
            "p_flexible", "p_flexible_std"
        ]

        open(path, "w") do io
            println(io, join(header, '\t'))
            for t in eachindex(summary.mean_E)
                row = [
                    string(t),
                    string(summary.mean_E[t]),
                    string(summary.mean_part_a_self[t]), string(summary.std_part_a_self[t]),
                    string(summary.mean_part_b_self[t]), string(summary.std_part_b_self[t]),
                    string(summary.mean_part_a_threat[t]), string(summary.std_part_a_threat[t]),
                    string(summary.mean_part_b_threat[t]), string(summary.std_part_b_threat[t]),
                    string(summary.mean_part_a_outcome[t]), string(summary.std_part_a_outcome[t]),
                    string(summary.mean_part_b_outcome[t]), string(summary.std_part_b_outcome[t]),
                    string(summary.mean_weight_part_a[t]), string(summary.std_weight_part_a[t]),
                    string(summary.mean_weight_part_b[t]), string(summary.std_weight_part_b[t]),
                    string(summary.mean_weight_self[t]), string(summary.std_weight_self[t]),
                    string(summary.mean_behavior[1, t]), string(summary.std_behavior[1, t]),
                    string(summary.mean_behavior[2, t]), string(summary.std_behavior[2, t]),
                    string(summary.mean_behavior[3, t]), string(summary.std_behavior[3, t]),
                ]
                println(io, join(row, '\t'))
            end
        end
        return path
    end

    function run_python_plot(script::String, args::Vector{String})
        script_path = tempname() * ".py"
        io = open(script_path, "w")
        write(io, script)
        close(io)
        cmd = Cmd(["python3", script_path, args...])
        run(setenv(cmd, ENV))
    end

    function save_regimes_figure(lookup)
        low_path = write_summary_table(lookup["Low Self-Energy"], joinpath(FIGURE_DATA_DIR, "low.tsv"))
        med_path = write_summary_table(lookup["Medium Self-Energy"], joinpath(FIGURE_DATA_DIR, "medium.tsv"))
        high_path = write_summary_table(lookup["High Self-Energy"], joinpath(FIGURE_DATA_DIR, "high.tsv"))
        output_path = joinpath(FIGURE_DIR, "ifs_v2_polarization_regimes.png")

        script = """
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sys

COLORS = {"A": "#c33d2f", "B": "#1f6ba7", "Self": "#22824f"}

def load(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\\t"))

def col(rows, key):
    return [float(r[key]) for r in rows]

fig, axes = plt.subplots(3, 1, figsize=(11, 12), sharex=True)
for ax, path, title in zip(
    axes,
    sys.argv[1:4],
    ["Low Self-Energy", "Medium Self-Energy", "High Self-Energy"],
):
    rows = load(path)
    t = col(rows, "t")
    ax.plot(t, col(rows, "part_a_self"), color=COLORS["A"], label="Part A self", linewidth=2.3)
    ax.fill_between(t,
                    [a - b for a, b in zip(col(rows, "part_a_self"), col(rows, "part_a_self_std"))],
                    [a + b for a, b in zip(col(rows, "part_a_self"), col(rows, "part_a_self_std"))],
                    color=COLORS["A"], alpha=0.12)
    ax.plot(t, col(rows, "part_b_self"), color=COLORS["B"], label="Part B self", linewidth=2.3)
    ax.fill_between(t,
                    [a - b for a, b in zip(col(rows, "part_b_self"), col(rows, "part_b_self_std"))],
                    [a + b for a, b in zip(col(rows, "part_b_self"), col(rows, "part_b_self_std"))],
                    color=COLORS["B"], alpha=0.12)
    ax.plot(t, col(rows, "weight_part_a"), color=COLORS["A"], linestyle="--", label="w_A", linewidth=1.8)
    ax.plot(t, col(rows, "weight_part_b"), color=COLORS["B"], linestyle="--", label="w_B", linewidth=1.8)
    ax.plot(t, col(rows, "weight_self"), color=COLORS["Self"], linestyle="-.", label="w_Self", linewidth=1.8)
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel("Probability / weight")
    ax.set_title(title)
    ax.grid(alpha=0.16)
axes[-1].set_xlabel("Time")
axes[0].legend(loc="upper right", ncol=5, frameon=False)
fig.suptitle("Two Parts, Three Regimes", fontsize=14)
fig.tight_layout(rect=(0, 0, 1, 0.98))
fig.savefig(sys.argv[4], dpi=300)
"""

        run_python_plot(script, [low_path, med_path, high_path, output_path])
        println("  saved ifs_v2_polarization_regimes.png")
    end

    function save_oscillation_resolution(summary::IFSPolarizationV2Summary)
        summary_path = write_summary_table(summary, joinpath(FIGURE_DATA_DIR, "resolution.tsv"))
        output_path = joinpath(FIGURE_DIR, "ifs_v2_oscillation_to_resolution.png")

        script = """
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sys

def load(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\\t"))

def col(rows, key):
    return [float(r[key]) for r in rows]

rows = load(sys.argv[1])
t = col(rows, "t")

fig, axes = plt.subplots(2, 1, figsize=(11, 8.5), sharex=True)
axes[0].plot(t, col(rows, "weight_part_a"), color="#c33d2f", label="w_A", linewidth=2.2)
axes[0].plot(t, col(rows, "weight_part_b"), color="#1f6ba7", label="w_B", linewidth=2.2)
axes[0].plot(t, col(rows, "weight_self"), color="#22824f", label="w_Self", linewidth=2.2)
axes[0].plot(t, col(rows, "E"), color="black", linestyle=":", label="E_t", linewidth=2.0)
axes[0].set_ylim(0.0, 1.0)
axes[0].set_ylabel("Mixing weight")
axes[0].set_title("Oscillation to Resolution")
axes[0].legend(loc="upper left", ncol=4, frameon=False)
axes[0].grid(alpha=0.16)

axes[1].plot(t, col(rows, "part_a_self"), color="#c33d2f", label="Part A self", linewidth=2.2)
axes[1].plot(t, col(rows, "part_b_self"), color="#1f6ba7", label="Part B self", linewidth=2.2)
axes[1].plot(t, col(rows, "p_approach"), color="black", linestyle="--", label="P(approach)", linewidth=1.9)
axes[1].plot(t, col(rows, "p_flexible"), color="#6248a6", linestyle="-.", label="P(flexible)", linewidth=1.9)
axes[1].set_ylim(0.0, 1.0)
axes[1].set_ylabel("Probability")
axes[1].set_xlabel("Time")
axes[1].grid(alpha=0.16)
axes[1].legend(loc="upper left", ncol=4, frameon=False)

fig.tight_layout()
fig.savefig(sys.argv[2], dpi=300)
"""

        run_python_plot(script, [summary_path, output_path])
        println("  saved ifs_v2_oscillation_to_resolution.png")
    end

    function save_dual_cascade(summary::IFSPolarizationV2Summary)
        summary_path = write_summary_table(summary, joinpath(FIGURE_DATA_DIR, "high.tsv"))
        output_path = joinpath(FIGURE_DIR, "ifs_v2_dual_cascade.png")

        script = """
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import sys

def load(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\\t"))

def col(rows, key):
    return [float(r[key]) for r in rows]

rows = load(sys.argv[1])
t = col(rows, "t")

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)

axes[0].plot(t, col(rows, "part_a_self"), color="#c33d2f", label="Self-state", linewidth=2.3)
axes[0].plot(t, col(rows, "part_a_threat"), color="#d97706", label="Threat meaning", linewidth=2.3)
axes[0].plot(t, col(rows, "part_a_outcome"), color="#7f1d1d", label="Expected outcome", linewidth=2.3)
axes[0].plot(t, col(rows, "p_avoid"), color="black", linestyle="--", label="P(avoid)", linewidth=1.9)
axes[0].set_title("Part A: exile / protector")
axes[0].set_xlabel("Time")
axes[0].set_ylabel("Probability")
axes[0].set_ylim(0.0, 1.0)
axes[0].grid(alpha=0.16)
axes[0].legend(loc="lower right", frameon=False)

axes[1].plot(t, col(rows, "part_b_self"), color="#1f6ba7", label="Self-state", linewidth=2.3)
axes[1].plot(t, col(rows, "part_b_threat"), color="#0f4c81", label="Threat meaning", linewidth=2.3)
axes[1].plot(t, col(rows, "part_b_outcome"), color="#0b1f4d", label="Expected outcome", linewidth=2.3)
axes[1].plot(t, col(rows, "p_approach"), color="black", linestyle="--", label="P(approach)", linewidth=1.9)
axes[1].set_title("Part B: social manager")
axes[1].set_xlabel("Time")
axes[1].grid(alpha=0.16)
axes[1].legend(loc="lower right", frameon=False)

fig.suptitle("Dual Cascade Under High Self-Energy", fontsize=14)
fig.tight_layout(rect=(0, 0, 1, 0.97))
fig.savefig(sys.argv[2], dpi=300)
"""

        run_python_plot(script, [summary_path, output_path])
        println("  saved ifs_v2_dual_cascade.png")
    end
end

println("=" ^ 72)
println("IFS v2 Two-Part Polarization Simulation")
println("=" ^ 72)

params = IFSPolarizationV2Params()

println("\nRegistered parameters")
println("  n_steps = $(params.n_steps)")
println("  self_precision_scale = $(params.self_precision_scale)")
println("  self_precision_power = $(params.self_precision_power)")
println("  fatigue_growth = $(params.fatigue_growth), fatigue_decay = $(params.fatigue_decay), fatigue_impact = $(params.fatigue_impact)")
println("  part A preferred action = avoid")
println("  part B preferred action = approach")

println("\nSingle-run debug: Oscillation Demo")
debug_model = build_ifs_polarization_v2_model(params=params)
_ = run_ifs_polarization_v2_condition(
    debug_model,
    oscillation_ifs_polarization_v2_config(params);
    seed=SEED,
    verbose=true,
    deterministic=false
)

println("\nRunning main conditions ($N_REPS replications each)")
summaries = run_ifs_polarization_v2_suite(
    params=params,
    configs=all_ifs_polarization_v2_configs(params),
    n_replications=N_REPS,
    seed=SEED
)
lookup = summary_by_name(summaries)

for summary in summaries
    print_condition_summary(summary)
end

println("\nParameter sensitivity ($SENS_REPS replications per perturbation)")
sensitivity_rows = run_ifs_polarization_v2_sensitivity(
    params=params,
    n_replications=SENS_REPS,
    seed=SEED + 1000
)
print_sensitivity_summary(sensitivity_rows)

if ENABLE_FIGURES
    println("\nGenerating figures")
    save_regimes_figure(lookup)
    save_oscillation_resolution(lookup["Oscillation to Resolution"])
    save_dual_cascade(lookup["High Self-Energy"])
else
    println("\nSkipping figure generation because IFS_POLARIZATION_V2_SKIP_FIGURES=1")
end

println("\nDone.")
