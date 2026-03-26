#!/usr/bin/env julia
"""
    ifs_polarization_simulation.jl

    IFS Polarization Simulation (Appendix B)

Runs the polarization dynamics model across three Self-energy conditions
and generates publication-quality figures showing:
1. Activation time series (a_A and a_B) for each E_t level
2. Policy selection over time (color-coded)
3. Summary bar charts of key measures across E_t levels
4. Phase portraits (a_A vs a_B trajectories)
5. Combined panel figure for the paper

Usage:
    julia --project=projects/library projects/library/scripts/ifs_polarization_simulation.jl
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

try
    using Plots
catch
    @info "Installing Plots..."
    Pkg.add("Plots")
    using Plots
end

using Random
using Statistics

# Include the model directly
include(joinpath(@__DIR__, "..", "src", "active_inference", "ifs_polarization_model.jl"))

#==============================================================================#
# Figure Configuration
#==============================================================================#

# Publication-quality defaults
const TITLE_SIZE = 13
const LABEL_SIZE = 11
const TICK_SIZE = 9
const LEGEND_SIZE = 9
const LINE_WIDTH = 2.0
const DPI = 300

# Color palette
const COLOR_A = RGB(0.20, 0.47, 0.87)       # Blue for Part A (approach)
const COLOR_B = RGB(0.87, 0.24, 0.20)       # Red for Part B (withdraw)
const COLOR_MIXED = RGB(0.20, 0.73, 0.40)   # Green for mixed policy
const COLOR_SIMUL = RGB(0.95, 0.85, 0.30)   # Gold for simultaneous repr region

const COLOR_LOW = RGB(0.87, 0.24, 0.20)     # Red for low E_t
const COLOR_MED = RGB(0.95, 0.65, 0.15)     # Orange for medium E_t
const COLOR_HIGH = RGB(0.20, 0.60, 0.40)    # Green for high E_t

#==============================================================================#
# Output Directory
#==============================================================================#

const FIGURE_DIR = joinpath(@__DIR__, "..", "..", "ifs-paper", "figures")

function ensure_figure_dir()
    mkpath(FIGURE_DIR)
    println("Figures will be saved to: $(abspath(FIGURE_DIR))")
end

#==============================================================================#
# Figure 1: Activation Time Series (3 panels)
#==============================================================================#

"""
    plot_activation_timeseries(conditions)

Three-panel time series showing a_A and a_B for low, medium, and high E_t.
The key visual: low E_t shows anti-phase oscillation, high E_t shows stable coexistence.
"""
function plot_activation_timeseries(conditions::Dict{Symbol, PolarizationResults})
    panels = []

    for (idx, (label, title_str)) in enumerate([
        (:low,    "Low Self-Energy (E = 0.1)"),
        (:medium, "Medium Self-Energy (E = 0.5)"),
        (:high,   "High Self-Energy (E = 0.9)")
    ])
        res = conditions[label]
        t = 1:res.n_timesteps
        a_A = [s.a_A for s in res.states]
        a_B = [s.a_B for s in res.states]

        p = plot(
            title = title_str,
            titlefontsize = TITLE_SIZE,
            xlabel = idx == 3 ? "Timestep" : "",
            ylabel = "Activation",
            ylims = (-0.05, 1.05),
            xlims = (0, res.n_timesteps + 1),
            tickfontsize = TICK_SIZE,
            labelfontsize = LABEL_SIZE,
            legendfontsize = LEGEND_SIZE,
            legend = idx == 1 ? :topright : false,
            grid = true,
            gridstyle = :dot,
            gridlinewidth = 0.5,
            gridalpha = 0.3,
            left_margin = 5Plots.mm,
            bottom_margin = idx == 3 ? 5Plots.mm : 2Plots.mm,
        )

        # Shade simultaneous representation zones
        first_simul = true
        for i in 1:res.n_timesteps
            if res.states[i].simultaneous
                lbl = (first_simul && idx == 1) ? "Simultaneous" : ""
                vspan!(p, [i - 0.5, i + 0.5],
                       fillcolor = COLOR_SIMUL, fillalpha = 0.18,
                       label = lbl)
                first_simul = false
            end
        end

        # Reference lines for takeover thresholds
        hline!(p, [0.7], linestyle = :dash, color = :gray, alpha = 0.4,
               linewidth = 0.8, label = "")
        hline!(p, [0.3], linestyle = :dash, color = :gray, alpha = 0.4,
               linewidth = 0.8, label = "")

        # Part activations
        plot!(p, t, a_A, linewidth = LINE_WIDTH + 0.5, color = COLOR_A,
              label = idx == 1 ? "Part A (approach)" : "", alpha = 0.9)
        plot!(p, t, a_B, linewidth = LINE_WIDTH + 0.5, color = COLOR_B,
              label = idx == 1 ? "Part B (withdraw)" : "", alpha = 0.9)

        push!(panels, p)
    end

    fig = plot(panels..., layout = (3, 1), size = (750, 680),
               top_margin = 3Plots.mm)

    savefig(fig, joinpath(FIGURE_DIR, "polarization_timeseries.png"))
    println("  Saved: polarization_timeseries.png")
    return fig
end

#==============================================================================#
# Figure 2: Policy Selection Over Time
#==============================================================================#

"""
    plot_policy_timeseries(conditions)

Three-panel policy selection showing approach (blue), withdraw (red),
mixed (green) as probability lines with the selected policy marked.
"""
function plot_policy_timeseries(conditions::Dict{Symbol, PolarizationResults})
    panels = []

    for (idx, (label, title_str)) in enumerate([
        (:low,    "Low Self-Energy (E = 0.1)"),
        (:medium, "Medium Self-Energy (E = 0.5)"),
        (:high,   "High Self-Energy (E = 0.9)")
    ])
        res = conditions[label]
        t = 1:res.n_timesteps
        prob_approach = [s.policy_probs[1] for s in res.states]
        prob_withdraw = [s.policy_probs[2] for s in res.states]
        prob_mixed    = [s.policy_probs[3] for s in res.states]

        p = plot(
            title = title_str,
            titlefontsize = TITLE_SIZE,
            xlabel = idx == 3 ? "Timestep" : "",
            ylabel = "Policy Probability",
            ylims = (-0.05, 1.05),
            xlims = (0, res.n_timesteps + 1),
            tickfontsize = TICK_SIZE,
            labelfontsize = LABEL_SIZE,
            legendfontsize = LEGEND_SIZE,
            legend = idx == 1 ? :topright : false,
            grid = true,
            gridstyle = :dot,
            gridlinewidth = 0.5,
            gridalpha = 0.3,
            left_margin = 5Plots.mm,
            bottom_margin = idx == 3 ? 5Plots.mm : 2Plots.mm,
        )

        # Policy probability lines with filled ribbons
        plot!(p, t, prob_approach, fillrange = 0, fillalpha = 0.25,
              color = COLOR_A, linewidth = LINE_WIDTH, alpha = 0.85,
              label = idx == 1 ? "Approach" : "")
        plot!(p, t, prob_withdraw, fillrange = 0, fillalpha = 0.25,
              color = COLOR_B, linewidth = LINE_WIDTH, alpha = 0.85,
              label = idx == 1 ? "Withdraw" : "")
        plot!(p, t, prob_mixed, fillrange = 0, fillalpha = 0.25,
              color = COLOR_MIXED, linewidth = LINE_WIDTH, alpha = 0.85,
              label = idx == 1 ? "Mixed" : "")

        push!(panels, p)
    end

    fig = plot(panels..., layout = (3, 1), size = (750, 680),
               top_margin = 3Plots.mm)

    savefig(fig, joinpath(FIGURE_DIR, "polarization_policy.png"))
    println("  Saved: polarization_policy.png")
    return fig
end

#==============================================================================#
# Figure 3: Summary Bar Charts
#==============================================================================#

"""
    plot_summary_bars(conditions)

Bar chart comparing key measures across E_t levels:
- Oscillation frequency
- Switching rate
- Time in simultaneous representation
- Policy entropy (mean)
"""
function plot_summary_bars(conditions::Dict{Symbol, PolarizationResults})
    labels_str = ["Low (0.1)", "Med (0.5)", "High (0.9)"]
    keys = [:low, :medium, :high]
    bar_colors = [COLOR_LOW, COLOR_MED, COLOR_HIGH]

    # Extract measures
    osc_freq = [conditions[k].oscillation_frequency for k in keys]
    switch_rate = [conditions[k].switching_rate for k in keys]
    time_simul = [conditions[k].time_in_simultaneous * 100 for k in keys]
    mean_entropy = [mean([s.policy_entropy for s in conditions[k].states]) for k in keys]

    # Normalize policy entropy to [0, 1] (max is log2(3) for 3 policies)
    max_h = log2(3)
    mean_entropy_norm = mean_entropy ./ max_h

    p1 = bar(labels_str, osc_freq, color = bar_colors,
             title = "Oscillation Frequency", ylabel = "Frequency",
             titlefontsize = TITLE_SIZE, tickfontsize = TICK_SIZE,
             labelfontsize = LABEL_SIZE, legend = false,
             bar_width = 0.6, fillalpha = 0.85,
             linewidth = 0.5, linecolor = :gray40)

    p2 = bar(labels_str, switch_rate, color = bar_colors,
             title = "Policy Switching Rate", ylabel = "Rate",
             titlefontsize = TITLE_SIZE, tickfontsize = TICK_SIZE,
             labelfontsize = LABEL_SIZE, legend = false,
             bar_width = 0.6, fillalpha = 0.85,
             linewidth = 0.5, linecolor = :gray40)

    p3 = bar(labels_str, time_simul, color = bar_colors,
             title = "Time in Simultaneous\nRepresentation", ylabel = "% Timesteps",
             titlefontsize = TITLE_SIZE, tickfontsize = TICK_SIZE,
             labelfontsize = LABEL_SIZE, legend = false,
             bar_width = 0.6, fillalpha = 0.85,
             linewidth = 0.5, linecolor = :gray40)

    p4 = bar(labels_str, mean_entropy_norm, color = bar_colors,
             title = "Mean Policy Entropy\n(normalized)", ylabel = "H / H_max",
             titlefontsize = TITLE_SIZE, tickfontsize = TICK_SIZE,
             labelfontsize = LABEL_SIZE, legend = false,
             bar_width = 0.6, fillalpha = 0.85,
             linewidth = 0.5, linecolor = :gray40)

    fig = plot(p1, p2, p3, p4, layout = (2, 2), size = (700, 550),
               top_margin = 3Plots.mm, left_margin = 5Plots.mm,
               bottom_margin = 5Plots.mm)

    savefig(fig, joinpath(FIGURE_DIR, "polarization_summary.png"))
    println("  Saved: polarization_summary.png")
    return fig
end

#==============================================================================#
# Figure 4: Phase Portraits
#==============================================================================#

"""
    plot_phase_portraits(conditions)

Phase portrait: a_A vs a_B trajectory for each E_t level, overlaid.
Shows the geometry of polarization dynamics in activation space.
"""
function plot_phase_portraits(conditions::Dict{Symbol, PolarizationResults})
    fig = plot(
        title = "Phase Portrait: Part A vs Part B Activation",
        titlefontsize = TITLE_SIZE + 1,
        xlabel = "Part A activation (approach)",
        ylabel = "Part B activation (withdraw)",
        xlims = (-0.05, 1.05),
        ylims = (-0.05, 1.05),
        aspect_ratio = :equal,
        tickfontsize = TICK_SIZE,
        labelfontsize = LABEL_SIZE,
        legendfontsize = LEGEND_SIZE,
        legend = :topright,
        grid = true,
        gridstyle = :dot,
        gridlinewidth = 0.5,
        gridalpha = 0.3,
        size = (600, 580),
        left_margin = 5Plots.mm,
        bottom_margin = 5Plots.mm,
    )

    # Shade the "simultaneous representation" zone (both between 0.3 and 0.7)
    rect_x = [0.3, 0.7, 0.7, 0.3, 0.3]
    rect_y = [0.3, 0.3, 0.7, 0.7, 0.3]
    plot!(fig, Shape(rect_x, rect_y),
          fillcolor = COLOR_SIMUL, fillalpha = 0.15,
          linecolor = COLOR_SIMUL, linestyle = :dash, linewidth = 1,
          label = "Simultaneous zone")

    # Diagonal line a_A = a_B (balance line)
    plot!(fig, [0, 1], [0, 1], linestyle = :dot, color = :gray,
          alpha = 0.4, linewidth = 1, label = "")

    # Plot trajectories for each condition
    for (label, name, color, alpha_val) in [
        (:low,    "Low E (0.1)",    COLOR_LOW,  0.60),
        (:medium, "Medium E (0.5)", COLOR_MED,  0.75),
        (:high,   "High E (0.9)",   COLOR_HIGH, 0.85)
    ]
        res = conditions[label]
        a_A = [s.a_A for s in res.states]
        a_B = [s.a_B for s in res.states]

        plot!(fig, a_A, a_B, linewidth = LINE_WIDTH, color = color,
              alpha = alpha_val, label = name)

        # Mark start and end
        scatter!(fig, [a_A[1]], [a_B[1]], color = color, markersize = 7,
                 markershape = :circle, markerstrokewidth = 1.5,
                 markerstrokecolor = :white, label = "")
        scatter!(fig, [a_A[end]], [a_B[end]], color = color, markersize = 7,
                 markershape = :diamond, markerstrokewidth = 1.5,
                 markerstrokecolor = :white, label = "")
    end

    # Legend markers for start/end
    scatter!(fig, [-10], [-10], color = :gray, markersize = 6,
             markershape = :circle, label = "Start")
    scatter!(fig, [-10], [-10], color = :gray, markersize = 6,
             markershape = :diamond, label = "End")

    savefig(fig, joinpath(FIGURE_DIR, "polarization_phase.png"))
    println("  Saved: polarization_phase.png")
    return fig
end

#==============================================================================#
# Figure 5: Combined Panel (main paper figure)
#==============================================================================#

"""
    plot_combined_panel(conditions)

Combined 2x2 panel figure suitable for the paper:
- Top left: Low E_t time series
- Top right: High E_t time series
- Bottom left: Phase portrait
- Bottom right: Summary bars (time in simultaneous + switching rate)
"""
function plot_combined_panel(conditions::Dict{Symbol, PolarizationResults})
    # Panel A: Low E_t time series
    res_low = conditions[:low]
    t = 1:res_low.n_timesteps
    a_A_low = [s.a_A for s in res_low.states]
    a_B_low = [s.a_B for s in res_low.states]

    p1 = plot(
        title = "A. Low Self-Energy (E = 0.1)",
        titlefontsize = TITLE_SIZE,
        xlabel = "Timestep", ylabel = "Activation",
        ylims = (-0.05, 1.05),
        tickfontsize = TICK_SIZE,
        labelfontsize = LABEL_SIZE,
        legendfontsize = LEGEND_SIZE - 1,
        legend = :topright,
        grid = true, gridstyle = :dot, gridalpha = 0.3,
    )
    hline!(p1, [0.7], linestyle = :dash, color = :gray, alpha = 0.35, linewidth = 0.8, label = "")
    hline!(p1, [0.3], linestyle = :dash, color = :gray, alpha = 0.35, linewidth = 0.8, label = "")
    plot!(p1, t, a_A_low, linewidth = LINE_WIDTH + 0.3, color = COLOR_A,
          label = "Part A (approach)", alpha = 0.9)
    plot!(p1, t, a_B_low, linewidth = LINE_WIDTH + 0.3, color = COLOR_B,
          label = "Part B (withdraw)", alpha = 0.9)

    # Panel B: High E_t time series
    res_high = conditions[:high]
    a_A_high = [s.a_A for s in res_high.states]
    a_B_high = [s.a_B for s in res_high.states]

    p2 = plot(
        title = "B. High Self-Energy (E = 0.9)",
        titlefontsize = TITLE_SIZE,
        xlabel = "Timestep", ylabel = "Activation",
        ylims = (-0.05, 1.05),
        tickfontsize = TICK_SIZE,
        labelfontsize = LABEL_SIZE,
        legend = false,
        grid = true, gridstyle = :dot, gridalpha = 0.3,
    )
    # Shade simultaneous zone
    for i in 1:res_high.n_timesteps
        if res_high.states[i].simultaneous
            vspan!(p2, [i - 0.5, i + 0.5],
                   fillcolor = COLOR_SIMUL, fillalpha = 0.15, label = "")
        end
    end
    hline!(p2, [0.7], linestyle = :dash, color = :gray, alpha = 0.35, linewidth = 0.8, label = "")
    hline!(p2, [0.3], linestyle = :dash, color = :gray, alpha = 0.35, linewidth = 0.8, label = "")
    plot!(p2, t, a_A_high, linewidth = LINE_WIDTH + 0.3, color = COLOR_A,
          label = "", alpha = 0.9)
    plot!(p2, t, a_B_high, linewidth = LINE_WIDTH + 0.3, color = COLOR_B,
          label = "", alpha = 0.9)

    # Panel C: Phase portrait
    p3 = plot(
        title = "C. Phase Portrait",
        titlefontsize = TITLE_SIZE,
        xlabel = "Part A activation", ylabel = "Part B activation",
        xlims = (-0.05, 1.05), ylims = (-0.05, 1.05),
        aspect_ratio = :equal,
        tickfontsize = TICK_SIZE,
        labelfontsize = LABEL_SIZE,
        legendfontsize = LEGEND_SIZE - 1,
        legend = :topright,
        grid = true, gridstyle = :dot, gridalpha = 0.3,
    )
    # Simultaneous zone
    plot!(p3, Shape([0.3, 0.7, 0.7, 0.3], [0.3, 0.3, 0.7, 0.7]),
          fillcolor = COLOR_SIMUL, fillalpha = 0.12,
          linecolor = COLOR_SIMUL, linestyle = :dash, linewidth = 0.8, label = "")

    for (label, name, color, alpha_val) in [
        (:low,    "E=0.1",  COLOR_LOW,  0.55),
        (:medium, "E=0.5",  COLOR_MED,  0.70),
        (:high,   "E=0.9",  COLOR_HIGH, 0.85)
    ]
        res = conditions[label]
        a_A = [s.a_A for s in res.states]
        a_B = [s.a_B for s in res.states]
        plot!(p3, a_A, a_B, linewidth = LINE_WIDTH, color = color,
              alpha = alpha_val, label = name)
        scatter!(p3, [a_A[1]], [a_B[1]], color = color, markersize = 5,
                 markershape = :circle, markerstrokewidth = 1, markerstrokecolor = :white,
                 label = "")
        scatter!(p3, [a_A[end]], [a_B[end]], color = color, markersize = 5,
                 markershape = :diamond, markerstrokewidth = 1, markerstrokecolor = :white,
                 label = "")
    end

    # Panel D: Key summary bars (side-by-side using regular bar)
    keys = [:low, :medium, :high]
    time_simul = [conditions[k].time_in_simultaneous * 100 for k in keys]
    switch_rate = [conditions[k].switching_rate * 100 for k in keys]
    osc_freq = [conditions[k].oscillation_frequency * 100 for k in keys]

    x_positions = [1, 2, 3]
    bar_w = 0.25

    p4 = plot(
        title = "D. Key Measures by Self-Energy",
        titlefontsize = TITLE_SIZE,
        ylabel = "% of Timesteps / Frequency x100",
        tickfontsize = TICK_SIZE,
        labelfontsize = LABEL_SIZE,
        legendfontsize = LEGEND_SIZE - 1,
        legend = :topleft,
        xticks = (x_positions, ["Low\n(0.1)", "Med\n(0.5)", "High\n(0.9)"]),
        grid = true, gridstyle = :dot, gridalpha = 0.3,
    )

    # Simultaneous representation bars
    bar!(p4, x_positions .- bar_w, time_simul,
         bar_width = bar_w * 1.8,
         color = COLOR_HIGH, fillalpha = 0.8,
         linewidth = 0.5, linecolor = :gray40,
         label = "Simult. repr. %")

    # Switching rate bars
    bar!(p4, x_positions .+ bar_w, switch_rate,
         bar_width = bar_w * 1.8,
         color = COLOR_LOW, fillalpha = 0.8,
         linewidth = 0.5, linecolor = :gray40,
         label = "Policy switch %")

    fig = plot(p1, p2, p3, p4, layout = (2, 2), size = (900, 700),
               top_margin = 4Plots.mm, left_margin = 5Plots.mm,
               bottom_margin = 5Plots.mm, right_margin = 3Plots.mm)

    savefig(fig, joinpath(FIGURE_DIR, "polarization_combined.png"))
    println("  Saved: polarization_combined.png")
    return fig
end

#==============================================================================#
# Main
#==============================================================================#

function main()
    println("=" ^ 65)
    println("IFS Polarization Simulation (Appendix B)")
    println("=" ^ 65)

    ensure_figure_dir()

    # Run simulations
    println("\n[1/6] Running simulations...")
    params = default_params()
    conditions = run_all_conditions(params=params, n_timesteps=100, seed=42)

    # Print summaries
    println("\n[2/6] Computing summary statistics...")
    print_all_summaries(conditions)

    # Generate figures
    println("\n[3/6] Generating activation time series...")
    plot_activation_timeseries(conditions)

    println("\n[4/6] Generating policy time series...")
    plot_policy_timeseries(conditions)

    println("\n[5/6] Generating summary bar charts...")
    plot_summary_bars(conditions)

    println("\n[6/6] Generating phase portraits...")
    plot_phase_portraits(conditions)

    # Combined panel for the paper
    println("\n[Bonus] Generating combined panel figure...")
    plot_combined_panel(conditions)

    println("\n" * "=" ^ 65)
    println("All figures saved to: $(abspath(FIGURE_DIR))")
    println("=" ^ 65)

    return conditions
end

# Run
conditions = main()
