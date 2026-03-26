#!/usr/bin/env julia
"""
    ifs_formation_simulation.jl

    Runs the IFS Part Formation simulation (Appendix A) across three conditions:
    - Condition A: High threat + low control (classic trauma formation)
    - Condition B: High threat + high control (distressing but not part-forming)
    - Condition C: Chronic low support (slow neglect-like formation)

    Generates publication-quality figures showing:
    1. Prior evolution during acquisition
    2. Readout comparison across conditions
    3. Controllability gradient effects

Usage:
    cd projects/library
    julia --project=. scripts/ifs_formation_simulation.jl
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

try
    using Plots
    using Random
    using Statistics
catch
    @info "Installing dependencies..."
    Pkg.instantiate()
    using Plots
    using Random
    using Statistics
end

# Include the ActiveInferenceCore module
include(joinpath(@__DIR__, "..", "src", "active_inference", "ActiveInferenceCore.jl"))
using .ActiveInferenceCore

# Output directory for figures
const FIGURE_DIR = joinpath(@__DIR__, "..", "..", "ifs-paper", "figures")
mkpath(FIGURE_DIR)

# =============================================================================
# Run Simulations
# =============================================================================

function run_all_simulations(;
    n_acquisition::Int=40,
    n_readout::Int=20,
    n_replications::Int=10,
    verbose::Bool=true
)
    println("="^60)
    println("IFS Part Formation Simulation (Appendix A)")
    println("="^60)
    println("  Acquisition trials: $n_acquisition")
    println("  Readout trials: $n_readout")
    println("  Replications: $n_replications")
    println()

    seeds = collect(1:n_replications)

    results = run_formation_comparison(
        n_acquisition=n_acquisition,
        n_readout=n_readout,
        seeds=seeds,
        eta_D=1.0,
        gamma=4.0,
        alpha=8.0,
        pD_scale=1.0,
        verbose=verbose
    )

    return results
end

# =============================================================================
# Plotting Functions
# =============================================================================

"""
    plot_acquisition_trajectories(results; save_path)

Plot how P(helpless), P(danger), P(avoid) evolve during acquisition.
"""
function plot_acquisition_trajectories(results::Dict; save_path::String="")
    conditions = [:A, :B, :C]
    labels = Dict(:A => "A: High threat + low control",
                  :B => "B: High threat + high control",
                  :C => "C: Chronic low support")
    colors = Dict(:A => :red, :B => :blue, :C => :orange)

    # --- Panel 1: P(child_helpless) ---
    p1 = plot(title="Prior: P(child_helpless)",
              xlabel="Acquisition Trial", ylabel="Probability",
              ylims=(0, 1), legend=:topleft, grid=true,
              titlefontsize=11, guidefontsize=9, legendfontsize=7)

    for cond in conditions
        reps = results[cond]
        n_trials = length(reps[1].p_helpless)
        all_traces = hcat([r.p_helpless for r in reps]...)
        mean_trace = vec(mean(all_traces, dims=2))
        std_trace = vec(std(all_traces, dims=2))

        plot!(p1, 1:n_trials, mean_trace,
              ribbon=std_trace, fillalpha=0.2,
              label=labels[cond], color=colors[cond], linewidth=2)
    end
    hline!(p1, [0.5], linestyle=:dash, color=:gray, alpha=0.5, label="Flat prior")

    # --- Panel 2: P(danger) ---
    p2 = plot(title="Prior: P(threat_meaning=danger)",
              xlabel="Acquisition Trial", ylabel="Probability",
              ylims=(0, 1), legend=:topleft, grid=true,
              titlefontsize=11, guidefontsize=9, legendfontsize=7)

    for cond in conditions
        reps = results[cond]
        n_trials = length(reps[1].p_danger)
        all_traces = hcat([r.p_danger for r in reps]...)
        mean_trace = vec(mean(all_traces, dims=2))
        std_trace = vec(std(all_traces, dims=2))

        plot!(p2, 1:n_trials, mean_trace,
              ribbon=std_trace, fillalpha=0.2,
              label=labels[cond], color=colors[cond], linewidth=2)
    end
    hline!(p2, [0.5], linestyle=:dash, color=:gray, alpha=0.5, label="Flat prior")

    # --- Panel 3: P(avoid) ---
    p3 = plot(title="Policy: P(avoid)",
              xlabel="Acquisition Trial", ylabel="Probability",
              ylims=(0, 1), legend=:topleft, grid=true,
              titlefontsize=11, guidefontsize=9, legendfontsize=7)

    for cond in conditions
        reps = results[cond]
        n_trials = length(reps[1].p_avoid)
        all_traces = hcat([r.p_avoid for r in reps]...)
        mean_trace = vec(mean(all_traces, dims=2))
        std_trace = vec(std(all_traces, dims=2))

        plot!(p3, 1:n_trials, mean_trace,
              ribbon=std_trace, fillalpha=0.2,
              label=labels[cond], color=colors[cond], linewidth=2)
    end
    hline!(p3, [1/3], linestyle=:dash, color=:gray, alpha=0.5, label="Uniform policy")

    fig = plot(p1, p2, p3, layout=(3, 1), size=(700, 900),
               left_margin=5Plots.mm, bottom_margin=3Plots.mm)

    if !isempty(save_path)
        savefig(fig, save_path)
        println("Saved: $save_path")
    end
    return fig
end

"""
    plot_readout_comparison(results; save_path)

Bar charts comparing post-acquisition beliefs in safe context.
"""
function plot_readout_comparison(results::Dict; save_path::String="")
    conditions = [:A, :B, :C]
    cond_labels = ["A: Trauma\n(high threat,\nlow control)",
                   "B: Stress\n(high threat,\nhigh control)",
                   "C: Neglect\n(chronic low\nsupport)"]
    colors_list = [:red, :blue, :orange]

    mean_helpless = Float64[]
    std_helpless = Float64[]
    mean_danger = Float64[]
    std_danger = Float64[]
    mean_avoid = Float64[]
    std_avoid = Float64[]

    for cond in conditions
        reps = results[cond]
        h_vals = [mean(r.readout_helpless) for r in reps]
        d_vals = [mean(r.readout_danger) for r in reps]
        a_vals = [mean(r.readout_avoid) for r in reps]

        push!(mean_helpless, mean(h_vals))
        push!(std_helpless, std(h_vals))
        push!(mean_danger, mean(d_vals))
        push!(std_danger, std(d_vals))
        push!(mean_avoid, mean(a_vals))
        push!(std_avoid, std(a_vals))
    end

    p1 = bar(cond_labels, mean_helpless,
             yerr=std_helpless,
             title="Readout: P(child_helpless)\nin safe context",
             ylabel="Probability", ylims=(0, 1),
             color=colors_list, alpha=0.8,
             legend=false, grid=true,
             titlefontsize=10, guidefontsize=9,
             bar_width=0.6)
    hline!(p1, [0.5], linestyle=:dash, color=:gray, alpha=0.5)

    p2 = bar(cond_labels, mean_danger,
             yerr=std_danger,
             title="Readout: P(danger)\nin safe context",
             ylabel="Probability", ylims=(0, 1),
             color=colors_list, alpha=0.8,
             legend=false, grid=true,
             titlefontsize=10, guidefontsize=9,
             bar_width=0.6)
    hline!(p2, [0.5], linestyle=:dash, color=:gray, alpha=0.5)

    p3 = bar(cond_labels, mean_avoid,
             yerr=std_avoid,
             title="Readout: P(avoid)\nin safe context",
             ylabel="Probability", ylims=(0, 1),
             color=colors_list, alpha=0.8,
             legend=false, grid=true,
             titlefontsize=10, guidefontsize=9,
             bar_width=0.6)
    hline!(p3, [1/3], linestyle=:dash, color=:gray, alpha=0.5)

    fig = plot(p1, p2, p3, layout=(1, 3), size=(1100, 400),
               bottom_margin=8Plots.mm, top_margin=3Plots.mm)

    if !isempty(save_path)
        savefig(fig, save_path)
        println("Saved: $save_path")
    end
    return fig
end

"""
    plot_bundle_rigidity(results; save_path)

Plot bundle rigidity (P(helpless) * P(danger) * P(avoid)) over acquisition.
"""
function plot_bundle_rigidity(results::Dict; save_path::String="")
    conditions = [:A, :B, :C]
    labels = Dict(:A => "A: High threat + low control",
                  :B => "B: High threat + high control",
                  :C => "C: Chronic low support")
    colors = Dict(:A => :red, :B => :blue, :C => :orange)

    p = plot(title="Bundle Rigidity: P(helpless) x P(danger) x P(avoid)",
             xlabel="Acquisition Trial",
             ylabel="Bundle Strength",
             legend=:topleft, grid=true,
             titlefontsize=11, guidefontsize=9, legendfontsize=8)

    for cond in conditions
        reps = results[cond]
        n_trials = length(reps[1].p_helpless)

        all_rigidity = hcat([
            reps[i].p_helpless .* reps[i].p_danger .* reps[i].p_avoid
            for i in 1:length(reps)
        ]...)

        mean_rigidity = vec(mean(all_rigidity, dims=2))
        std_rigidity = vec(std(all_rigidity, dims=2))

        plot!(p, 1:n_trials, mean_rigidity,
              ribbon=std_rigidity, fillalpha=0.2,
              label=labels[cond], color=colors[cond], linewidth=2.5)
    end

    hline!(p, [0.5 * 0.5 * (1/3)], linestyle=:dash, color=:gray, alpha=0.5,
           label="Flat-prior baseline")

    if !isempty(save_path)
        savefig(p, save_path)
        println("Saved: $save_path")
    end
    return p
end

"""
    plot_controllability_gradient(results; save_path)

Summary figure showing the controllability gradient across conditions.
Uses separate bar panels instead of groupedbar for compatibility.
"""
function plot_controllability_gradient(results::Dict; save_path::String="")
    conditions = [:A, :B, :C]
    x_labels = ["A: Trauma", "B: Stress", "C: Neglect"]
    colors_list = [:red, :blue, :orange]

    # Compute final acquisition and readout values
    acq_helpless = Float64[]
    acq_danger = Float64[]
    acq_avoid = Float64[]
    read_helpless = Float64[]
    read_danger = Float64[]
    read_avoid = Float64[]

    for cond in conditions
        reps = results[cond]
        n = min(5, length(reps[1].p_helpless))
        push!(acq_helpless, mean([mean(r.p_helpless[end-n+1:end]) for r in reps]))
        push!(acq_danger, mean([mean(r.p_danger[end-n+1:end]) for r in reps]))
        push!(acq_avoid, mean([mean(r.p_avoid[end-n+1:end]) for r in reps]))
        push!(read_helpless, mean([mean(r.readout_helpless) for r in reps]))
        push!(read_danger, mean([mean(r.readout_danger) for r in reps]))
        push!(read_avoid, mean([mean(r.readout_avoid) for r in reps]))
    end

    acq_bundle = acq_helpless .* acq_danger .* acq_avoid
    read_bundle = read_helpless .* read_danger .* read_avoid

    # Panel 1: End-of-acquisition bundle
    p1 = bar(x_labels, acq_bundle,
             title="End-of-Acquisition\nBundle Strength",
             ylabel="P(helpless) x P(danger)\nx P(avoid)",
             color=colors_list, alpha=0.8,
             legend=false, grid=true,
             titlefontsize=10, guidefontsize=8,
             bar_width=0.6)

    # Panel 2: Readout bundle
    p2 = bar(x_labels, read_bundle,
             title="Readout (Safe Context)\nBundle Strength",
             ylabel="P(helpless) x P(danger)\nx P(avoid)",
             color=colors_list, alpha=0.8,
             legend=false, grid=true,
             titlefontsize=10, guidefontsize=8,
             bar_width=0.6)

    # Panel 3: Individual readout components as stacked bars
    # Use separate bars for each metric
    p3 = plot(title="Readout Components\nin Safe Context",
              ylabel="Probability", ylims=(0, 1),
              grid=true, titlefontsize=10, guidefontsize=8, legendfontsize=7,
              xticks=(1:3, x_labels))

    bar_w = 0.25
    for (i, cond) in enumerate(conditions)
        bar!(p3, [i - bar_w], [read_helpless[i]],
             bar_width=bar_w, color=:darkred, alpha=0.8,
             label=(i == 1 ? "P(helpless)" : ""))
        bar!(p3, [i], [read_danger[i]],
             bar_width=bar_w, color=:darkblue, alpha=0.8,
             label=(i == 1 ? "P(danger)" : ""))
        bar!(p3, [i + bar_w], [read_avoid[i]],
             bar_width=bar_w, color=:darkgreen, alpha=0.8,
             label=(i == 1 ? "P(avoid)" : ""))
    end
    hline!(p3, [0.5], linestyle=:dash, color=:gray, alpha=0.3, label="")

    fig = plot(p1, p2, p3, layout=(1, 3), size=(1200, 400),
               bottom_margin=8Plots.mm, top_margin=5Plots.mm)

    if !isempty(save_path)
        savefig(fig, save_path)
        println("Saved: $save_path")
    end
    return fig
end

"""
    print_summary(results)

Print a text summary of the results.
"""
function print_summary(results::Dict)
    println("\n" * "="^60)
    println("FORMATION SIMULATION RESULTS SUMMARY")
    println("="^60)

    for cond in [:A, :B, :C]
        reps = results[cond]
        println("\nCondition $cond:")

        final_h = mean([r.p_helpless[end] for r in reps])
        final_d = mean([r.p_danger[end] for r in reps])
        final_a = mean([r.p_avoid[end] for r in reps])
        println("  End of acquisition:")
        println("    P(child_helpless) = $(round(final_h, digits=3))")
        println("    P(danger)         = $(round(final_d, digits=3))")
        println("    P(avoid)          = $(round(final_a, digits=3))")
        println("    Bundle strength   = $(round(final_h * final_d * final_a, digits=4))")

        read_h = mean([mean(r.readout_helpless) for r in reps])
        read_d = mean([mean(r.readout_danger) for r in reps])
        read_a = mean([mean(r.readout_avoid) for r in reps])
        println("  Readout (safe context):")
        println("    P(child_helpless) = $(round(read_h, digits=3))")
        println("    P(danger)         = $(round(read_d, digits=3))")
        println("    P(avoid)          = $(round(read_a, digits=3))")
        println("    Bundle strength   = $(round(read_h * read_d * read_a, digits=4))")
    end

    reps_A = results[:A]
    reps_B = results[:B]
    reps_C = results[:C]

    bundle_A = mean([mean(r.readout_helpless) * mean(r.readout_danger) * mean(r.readout_avoid) for r in reps_A])
    bundle_B = mean([mean(r.readout_helpless) * mean(r.readout_danger) * mean(r.readout_avoid) for r in reps_B])
    bundle_C = mean([mean(r.readout_helpless) * mean(r.readout_danger) * mean(r.readout_avoid) for r in reps_C])

    println("\n" * "-"^60)
    println("KEY PREDICTION CHECK:")
    println("  A (rigid bundle) > C (slow formation) > B (no bundle)")
    println("  Bundle A = $(round(bundle_A, digits=4))")
    println("  Bundle B = $(round(bundle_B, digits=4))")
    println("  Bundle C = $(round(bundle_C, digits=4))")
    println("  A > B: $(bundle_A > bundle_B ? "PASS" : "FAIL")")
    println("  A > C: $(bundle_A > bundle_C ? "PASS" : "FAIL")")
    println("  C > B: $(bundle_C > bundle_B ? "PASS" : "FAIL")")
    println("-"^60)
end

# =============================================================================
# Main
# =============================================================================

function main()
    results = run_all_simulations(
        n_acquisition=40,
        n_readout=20,
        n_replications=10,
        verbose=true
    )

    print_summary(results)

    println("\nGenerating figures...")

    plot_acquisition_trajectories(results,
        save_path=joinpath(FIGURE_DIR, "formation_acquisition_trajectories.png"))

    plot_readout_comparison(results,
        save_path=joinpath(FIGURE_DIR, "formation_readout_comparison.png"))

    plot_bundle_rigidity(results,
        save_path=joinpath(FIGURE_DIR, "formation_bundle_rigidity.png"))

    plot_controllability_gradient(results,
        save_path=joinpath(FIGURE_DIR, "formation_controllability_gradient.png"))

    println("\nAll figures saved to: $FIGURE_DIR")
    println("Done!")

    return results
end

if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
