"""
    ifs_simulation.jl - IFS Model H1/H2 Simulation and Visualization

Runs all 5 conditions under H1 and H2 hypotheses, generates publication-quality
figures for the IFS-Active Inference paper.

Figures generated:
1. Belief trajectories (self-state, threat meaning) per condition
2. Policy selection (P(avoid)) across trials
3. Capture index C_t across trials
4. Comparison: witnessing vs exposure vs baseline
5. H1 vs H2 comparison

Usage:
    cd projects/library
    julia --project=. scripts/ifs_simulation.jl
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

include(joinpath(@__DIR__, "..", "src", "active_inference", "ActiveInferenceCore.jl"))
using .ActiveInferenceCore
using Plots
using Statistics

# ============================================================================
# CONFIGURATION
# ============================================================================

const N_TRIALS = 30
const SEED = 42
const FIGURE_DIR = joinpath(@__DIR__, "..", "..", "ifs-paper", "figures")

# Create figure directory
mkpath(FIGURE_DIR)

# Plot defaults
default(
    fontfamily="Helvetica",
    titlefontsize=11,
    guidefontsize=10,
    tickfontsize=8,
    legendfontsize=8,
    linewidth=2.0,
    markersize=3,
    framestyle=:box,
    grid=true,
    gridalpha=0.2,
    dpi=300,
    size=(800, 500)
)

# Color scheme
const COLORS = Dict(
    "Baseline"     => RGB(0.5, 0.5, 0.5),     # gray
    "Exposure"     => RGB(0.2, 0.5, 0.8),      # blue
    "Witnessing"   => RGB(0.2, 0.7, 0.3),      # green
    "Real Danger"  => RGB(0.85, 0.2, 0.2),     # red
    "Dissociation" => RGB(0.6, 0.3, 0.7),      # purple
)

const LINESTYLES = Dict(
    "Baseline"     => :dash,
    "Exposure"     => :solid,
    "Witnessing"   => :solid,
    "Real Danger"  => :solid,
    "Dissociation" => :dot,
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

"""Smooth a trajectory with rolling mean."""
function smooth(x::Vector{Float64}, window::Int=3)
    n = length(x)
    result = similar(x)
    for i in 1:n
        lo = max(1, i - div(window, 2))
        hi = min(n, i + div(window, 2))
        result[i] = mean(x[lo:hi])
    end
    return result
end

"""Get color for a condition name."""
get_color(name::String) = get(COLORS, name, RGB(0.5, 0.5, 0.5))
get_linestyle(name::String) = get(LINESTYLES, name, :solid)

# ============================================================================
# RUN SIMULATIONS
# ============================================================================

println("=" ^ 60)
println("IFS Active Inference Simulation")
println("=" ^ 60)

params = IFSModelParams()

println("\nModel parameters:")
println("  d_self_helpless = $(params.d_self_helpless)")
println("  d_threat_danger = $(params.d_threat_danger)")
println("  beta_se = $(params.beta_se), gamma_se = $(params.gamma_se)")
println("  pi_part = $(params.pi_part), lambda_ctx = $(params.lambda_ctx)")
println("  r_t = $(params.r_t)")
println("  eta_D_base = $(params.eta_D_base)")

println("\nSelf-energy -> Capture index mapping:")
for E in [0.0, 0.1, 0.15, 0.5, 0.85, 1.0]
    C = compute_capture_index(params, E)
    println("  E=$E -> C=$(round(C, digits=3))")
end

println("\nRunning H1 (self-state-upstream)...")
h1_results = run_all_ifs_conditions(hypothesis=:H1, params=params, n_trials=N_TRIALS, seed=SEED)
println("  Done.")

println("Running H2 (threat-primary)...")
h2_results = run_all_ifs_conditions(hypothesis=:H2, params=params, n_trials=N_TRIALS, seed=SEED+100)
println("  Done.")

# Print summary
println("\n" * "=" ^ 60)
println("RESULTS SUMMARY")
println("=" ^ 60)

for (label, results) in [("H1", h1_results), ("H2", h2_results)]
    println("\n--- $label ---")
    for r in results
        t1 = r.trials[1]
        t_end = r.trials[end]
        println("  $(r.condition):")
        println("    pD_child: $(round(t1.pD_child_helpless,digits=3)) -> $(round(t_end.pD_child_helpless,digits=3))")
        println("    pD_danger: $(round(t1.pD_danger,digits=3)) -> $(round(t_end.pD_danger,digits=3))")
        println("    P(avoid): $(round(t1.p_avoid,digits=3)) -> $(round(t_end.p_avoid,digits=3))")
    end
end

# ============================================================================
# FIGURE 1: BELIEF TRAJECTORIES PER CONDITION (H1)
# ============================================================================

println("\nGenerating figures...")

function plot_belief_trajectories(results::Vector{IFSSimulationResult}, hypothesis_label::String)
    trials = 1:N_TRIALS

    p1 = plot(title="Self-State: P(child_helpless) - $hypothesis_label",
              xlabel="Trial", ylabel="P(child_helpless)",
              ylims=(0.0, 1.0), legend=:topright)

    p2 = plot(title="Threat Meaning: P(danger) - $hypothesis_label",
              xlabel="Trial", ylabel="P(danger)",
              ylims=(0.0, 1.0), legend=:topright)

    p3 = plot(title="Avoidance Tendency: P(avoid) - $hypothesis_label",
              xlabel="Trial", ylabel="P(avoid)",
              ylims=(0.0, 1.0), legend=:topright)

    p4 = plot(title="Capture Index C_t - $hypothesis_label",
              xlabel="Trial", ylabel="C_t",
              ylims=(0.0, 1.0), legend=:topright)

    for r in results
        col = get_color(r.condition)
        ls = get_linestyle(r.condition)

        pD_child = smooth(extract_trajectory(r, :pD_child_helpless))
        pD_danger = smooth(extract_trajectory(r, :pD_danger))
        p_avoid = smooth(extract_trajectory(r, :p_avoid))
        c_t = extract_trajectory(r, :C_t)

        plot!(p1, trials, pD_child, label=r.condition, color=col, linestyle=ls)
        plot!(p2, trials, pD_danger, label=r.condition, color=col, linestyle=ls)
        plot!(p3, trials, p_avoid, label=r.condition, color=col, linestyle=ls)
        plot!(p4, trials, c_t, label=r.condition, color=col, linestyle=ls)
    end

    p = plot(p1, p2, p3, p4, layout=(2, 2), size=(1000, 700),
             plot_title="IFS Model: Belief Trajectories ($hypothesis_label)",
             plot_titlefontsize=13)

    return p
end

p_h1_all = plot_belief_trajectories(h1_results, "H1")
savefig(p_h1_all, joinpath(FIGURE_DIR, "fig1_h1_belief_trajectories.png"))
println("  Saved fig1_h1_belief_trajectories.png")

p_h2_all = plot_belief_trajectories(h2_results, "H2")
savefig(p_h2_all, joinpath(FIGURE_DIR, "fig1_h2_belief_trajectories.png"))
println("  Saved fig1_h2_belief_trajectories.png")

# ============================================================================
# FIGURE 2: WITNESSING vs EXPOSURE vs BASELINE COMPARISON (H1)
# ============================================================================

function plot_condition_comparison(results::Vector{IFSSimulationResult}, hypothesis_label::String)
    # Select baseline, exposure, witnessing
    selected = filter(r -> r.condition in ["Baseline", "Exposure", "Witnessing"], results)
    trials = 1:N_TRIALS

    p1 = plot(title="Self-State Revision",
              xlabel="Trial", ylabel="P(child_helpless)",
              ylims=(0.0, 1.0), legend=:topright)

    p2 = plot(title="Threat Meaning Revision",
              xlabel="Trial", ylabel="P(danger)",
              ylims=(0.0, 1.0), legend=:topright)

    p3 = plot(title="Avoidance Tendency",
              xlabel="Trial", ylabel="P(avoid)",
              ylims=(0.0, 1.0), legend=:topright)

    for r in selected
        col = get_color(r.condition)
        ls = get_linestyle(r.condition)
        lw = r.condition == "Witnessing" ? 3.0 : 2.0

        pD_child = smooth(extract_trajectory(r, :pD_child_helpless))
        pD_danger = smooth(extract_trajectory(r, :pD_danger))
        p_avoid = smooth(extract_trajectory(r, :p_avoid))

        plot!(p1, trials, pD_child, label=r.condition, color=col, linestyle=ls, linewidth=lw)
        plot!(p2, trials, pD_danger, label=r.condition, color=col, linestyle=ls, linewidth=lw)
        plot!(p3, trials, p_avoid, label=r.condition, color=col, linestyle=ls, linewidth=lw)
    end

    # Add reference lines
    hline!(p1, [0.5], color=:black, alpha=0.3, linestyle=:dot, label="")
    hline!(p2, [0.5], color=:black, alpha=0.3, linestyle=:dot, label="")
    hline!(p3, [0.5], color=:black, alpha=0.3, linestyle=:dot, label="")

    p = plot(p1, p2, p3, layout=(1, 3), size=(1200, 400),
             plot_title="Witnessing vs Exposure vs Baseline ($hypothesis_label)",
             plot_titlefontsize=13,
             bottom_margin=5Plots.mm, left_margin=5Plots.mm)

    return p
end

p_comparison = plot_condition_comparison(h1_results, "H1")
savefig(p_comparison, joinpath(FIGURE_DIR, "fig2_witnessing_vs_exposure.png"))
println("  Saved fig2_witnessing_vs_exposure.png")

# ============================================================================
# FIGURE 3: H1 vs H2 COMPARISON UNDER WITNESSING
# ============================================================================

function plot_h1_h2_comparison(h1_results, h2_results)
    # Find witnessing condition in each
    h1_wit = first(filter(r -> r.condition == "Witnessing", h1_results))
    h2_wit = first(filter(r -> r.condition == "Witnessing", h2_results))

    trials = 1:N_TRIALS

    p1 = plot(title="Self-State: P(child_helpless)",
              xlabel="Trial", ylabel="P(child_helpless)",
              ylims=(0.0, 1.0), legend=:topright)

    h1_child = smooth(extract_trajectory(h1_wit, :pD_child_helpless))
    h2_child = smooth(extract_trajectory(h2_wit, :pD_child_helpless))
    plot!(p1, trials, h1_child, label="H1 (self-upstream)", color=RGB(0.2, 0.7, 0.3), linewidth=2.5)
    plot!(p1, trials, h2_child, label="H2 (threat-primary)", color=RGB(0.8, 0.4, 0.0), linewidth=2.5, linestyle=:dash)

    p2 = plot(title="Threat Meaning: P(danger)",
              xlabel="Trial", ylabel="P(danger)",
              ylims=(0.0, 1.0), legend=:topright)

    h1_danger = smooth(extract_trajectory(h1_wit, :pD_danger))
    h2_danger = smooth(extract_trajectory(h2_wit, :pD_danger))
    plot!(p2, trials, h1_danger, label="H1 (self-upstream)", color=RGB(0.2, 0.7, 0.3), linewidth=2.5)
    plot!(p2, trials, h2_danger, label="H2 (threat-primary)", color=RGB(0.8, 0.4, 0.0), linewidth=2.5, linestyle=:dash)

    # Annotate ordering
    h1_child_cross = find_crossing_trial(extract_trajectory(h1_wit, :pD_child_helpless), 0.7; direction=:below)
    h1_danger_cross = find_crossing_trial(extract_trajectory(h1_wit, :pD_danger), 0.7; direction=:below)
    h2_child_cross = find_crossing_trial(extract_trajectory(h2_wit, :pD_child_helpless), 0.7; direction=:below)
    h2_danger_cross = find_crossing_trial(extract_trajectory(h2_wit, :pD_danger), 0.7; direction=:below)

    p3 = plot(title="Revision Order (0.7 threshold crossing)",
              xlabel="", ylabel="Trial of crossing",
              bar_width=0.6, legend=false, xticks=false)

    labels = ["H1\nchild", "H1\ndanger", "H2\nchild", "H2\ndanger"]
    vals = Float64[]
    cols = []
    for (v, c) in [(h1_child_cross, RGB(0.2,0.7,0.3)), (h1_danger_cross, RGB(0.2,0.7,0.3)),
                    (h2_child_cross, RGB(0.8,0.4,0.0)), (h2_danger_cross, RGB(0.8,0.4,0.0))]
        push!(vals, isnothing(v) ? N_TRIALS : Float64(v))
        push!(cols, c)
    end

    bar!(p3, 1:4, vals, color=cols, label="",
         xticks=(1:4, labels))
    hline!(p3, [N_TRIALS], color=:black, alpha=0.3, linestyle=:dot, label="")

    p = plot(p1, p2, p3, layout=(1, 3), size=(1200, 400),
             plot_title="H1 vs H2 Comparison Under Witnessing",
             plot_titlefontsize=13,
             bottom_margin=8Plots.mm, left_margin=5Plots.mm)

    return p
end

p_h1h2 = plot_h1_h2_comparison(h1_results, h2_results)
savefig(p_h1h2, joinpath(FIGURE_DIR, "fig3_h1_vs_h2_witnessing.png"))
println("  Saved fig3_h1_vs_h2_witnessing.png")

# ============================================================================
# FIGURE 4: REAL DANGER AND DISSOCIATION CONTROLS
# ============================================================================

function plot_controls(results::Vector{IFSSimulationResult})
    trials = 1:N_TRIALS

    # Real Danger
    rd = first(filter(r -> r.condition == "Real Danger", results))
    wit = first(filter(r -> r.condition == "Witnessing", results))
    dis = first(filter(r -> r.condition == "Dissociation", results))
    bas = first(filter(r -> r.condition == "Baseline", results))

    # Panel A: Real danger preserves adaptive fear
    p1 = plot(title="Real Danger vs Witnessing: P(danger)",
              xlabel="Trial", ylabel="P(danger)",
              ylims=(0.0, 1.0), legend=:right)

    plot!(p1, trials, smooth(extract_trajectory(rd, :pD_danger)),
          label="Real Danger", color=get_color("Real Danger"), linewidth=2.5)
    plot!(p1, trials, smooth(extract_trajectory(wit, :pD_danger)),
          label="Witnessing", color=get_color("Witnessing"), linewidth=2.5)

    # Panel B: Dissociation vs baseline
    p2 = plot(title="Dissociation vs Baseline: P(child_helpless)",
              xlabel="Trial", ylabel="P(child_helpless)",
              ylims=(0.0, 1.0), legend=:right)

    plot!(p2, trials, smooth(extract_trajectory(dis, :pD_child_helpless)),
          label="Dissociation", color=get_color("Dissociation"), linewidth=2.5)
    plot!(p2, trials, smooth(extract_trajectory(bas, :pD_child_helpless)),
          label="Baseline", color=get_color("Baseline"), linewidth=2.5, linestyle=:dash)

    # Panel C: Dissociation vs witnessing P(avoid)
    p3 = plot(title="Dissociation vs Witnessing: P(avoid)",
              xlabel="Trial", ylabel="P(avoid)",
              ylims=(0.0, 1.0), legend=:right)

    plot!(p3, trials, smooth(extract_trajectory(dis, :p_avoid)),
          label="Dissociation", color=get_color("Dissociation"), linewidth=2.5)
    plot!(p3, trials, smooth(extract_trajectory(wit, :p_avoid)),
          label="Witnessing", color=get_color("Witnessing"), linewidth=2.5)
    plot!(p3, trials, smooth(extract_trajectory(bas, :p_avoid)),
          label="Baseline", color=get_color("Baseline"), linewidth=2.5, linestyle=:dash)

    p = plot(p1, p2, p3, layout=(1, 3), size=(1200, 400),
             plot_title="Control Conditions: Real Danger and Dissociation (H1)",
             plot_titlefontsize=13,
             bottom_margin=5Plots.mm, left_margin=5Plots.mm)

    return p
end

p_controls = plot_controls(h1_results)
savefig(p_controls, joinpath(FIGURE_DIR, "fig4_control_conditions.png"))
println("  Saved fig4_control_conditions.png")

# ============================================================================
# FIGURE 5: CAPTURE INDEX AND SELF-ENERGY RELATIONSHIP
# ============================================================================

function plot_capture_and_energy(results::Vector{IFSSimulationResult}, params::IFSModelParams)
    # Panel A: Self-energy -> capture index curve
    E_range = 0.0:0.01:1.0
    C_range = [compute_capture_index(params, E) for E in E_range]

    p1 = plot(title="Self-Energy to Capture Index",
              xlabel="Self-Energy E_t", ylabel="Capture Index C_t",
              ylims=(0.0, 1.0), legend=:topright)

    plot!(p1, collect(E_range), C_range, color=:black, linewidth=2.5, label="C_t = f(E_t)")

    # Mark the conditions
    for config in all_ifs_configs()
        C = compute_capture_index(params, config.E_t)
        scatter!(p1, [config.E_t], [C],
                markersize=8, color=get_color(config.name),
                label=config.name, markerstrokewidth=1.5)
    end

    # Add threshold zones
    hline!(p1, [0.5], color=:gray, alpha=0.4, linestyle=:dot, label="")
    annotate!(p1, 0.02, 0.85, text("Blending\nzone", 8, :left, :gray))
    annotate!(p1, 0.98, 0.15, text("Witnessing\nzone", 8, :right, :gray))

    # Panel B: Capture index trajectories
    p2 = plot(title="Capture Index Across Trials",
              xlabel="Trial", ylabel="C_t",
              ylims=(0.0, 1.0), legend=:topright)

    for r in results
        c_t = extract_trajectory(r, :C_t)
        plot!(p2, 1:N_TRIALS, c_t, label=r.condition,
              color=get_color(r.condition), linestyle=get_linestyle(r.condition), linewidth=2)
    end

    hline!(p2, [0.5], color=:gray, alpha=0.4, linestyle=:dot, label="")

    # Panel C: Self-energy modulation of learning
    p3 = plot(title="Effective Learning Rate vs Self-Energy",
              xlabel="Self-Energy E_t", ylabel="Effective eta",
              legend=:topleft)

    E_vals = collect(0.0:0.01:1.0)
    eta_vals = Float64[]
    for E in E_vals
        C = compute_capture_index(params, E)
        eta_eff = params.eta_D_base * (1.0 - C) * 1.0  # ctx_scale = 1
        push!(eta_vals, eta_eff)
    end

    plot!(p3, E_vals, eta_vals, color=:black, linewidth=2.5, label="eta_eff")

    # Mark conditions
    for config in all_ifs_configs()
        C = compute_capture_index(params, config.E_t)
        eta_eff = params.eta_D_base * (1.0 - C) * config.context_precision_scale
        scatter!(p3, [config.E_t], [eta_eff],
                markersize=8, color=get_color(config.name),
                label=config.name, markerstrokewidth=1.5)
    end

    p = plot(p1, p2, p3, layout=(1, 3), size=(1300, 420),
             plot_title="Self-Energy, Capture, and Learning",
             plot_titlefontsize=13,
             bottom_margin=5Plots.mm, left_margin=5Plots.mm)

    return p
end

p_capture = plot_capture_and_energy(h1_results, params)
savefig(p_capture, joinpath(FIGURE_DIR, "fig5_capture_index.png"))
println("  Saved fig5_capture_index.png")

# ============================================================================
# FIGURE 6: REVISION ORDER UNDER H1 WITNESSING
# ============================================================================

function plot_revision_order(h1_results)
    wit = first(filter(r -> r.condition == "Witnessing", h1_results))
    exp = first(filter(r -> r.condition == "Exposure", h1_results))
    trials = 1:N_TRIALS

    p1 = plot(title="H1 Witnessing: Revision Order",
              xlabel="Trial", ylabel="Belief strength (pD-level)",
              ylims=(0.0, 1.0), legend=:topright)

    pD_child = smooth(extract_trajectory(wit, :pD_child_helpless))
    pD_danger = smooth(extract_trajectory(wit, :pD_danger))
    p_avoid = smooth(extract_trajectory(wit, :p_avoid))

    plot!(p1, trials, pD_child, label="P(child_helpless)", color=RGB(0.85, 0.4, 0.1), linewidth=2.5)
    plot!(p1, trials, pD_danger, label="P(danger)", color=RGB(0.2, 0.2, 0.8), linewidth=2.5)
    plot!(p1, trials, p_avoid, label="P(avoid)", color=RGB(0.5, 0.5, 0.5), linewidth=2.5, linestyle=:dash)

    hline!(p1, [0.5], color=:black, alpha=0.3, linestyle=:dot, label="")

    # Add crossing annotations
    child_cross = find_crossing_trial(extract_trajectory(wit, :pD_child_helpless), 0.7; direction=:below)
    danger_cross = find_crossing_trial(extract_trajectory(wit, :pD_danger), 0.7; direction=:below)
    avoid_cross = find_crossing_trial(extract_trajectory(wit, :p_avoid), 0.7; direction=:below)

    if !isnothing(child_cross)
        vline!(p1, [child_cross], color=RGB(0.85,0.4,0.1), alpha=0.5, linestyle=:dot, label="")
    end
    if !isnothing(danger_cross)
        vline!(p1, [danger_cross], color=RGB(0.2,0.2,0.8), alpha=0.5, linestyle=:dot, label="")
    end
    if !isnothing(avoid_cross)
        vline!(p1, [avoid_cross], color=RGB(0.5,0.5,0.5), alpha=0.5, linestyle=:dot, label="")
    end

    # Panel B: Exposure for comparison
    p2 = plot(title="H1 Exposure: Revision Order",
              xlabel="Trial", ylabel="Belief strength (pD-level)",
              ylims=(0.0, 1.0), legend=:topright)

    pD_child_e = smooth(extract_trajectory(exp, :pD_child_helpless))
    pD_danger_e = smooth(extract_trajectory(exp, :pD_danger))
    p_avoid_e = smooth(extract_trajectory(exp, :p_avoid))

    plot!(p2, trials, pD_child_e, label="P(child_helpless)", color=RGB(0.85, 0.4, 0.1), linewidth=2.5)
    plot!(p2, trials, pD_danger_e, label="P(danger)", color=RGB(0.2, 0.2, 0.8), linewidth=2.5)
    plot!(p2, trials, p_avoid_e, label="P(avoid)", color=RGB(0.5, 0.5, 0.5), linewidth=2.5, linestyle=:dash)

    hline!(p2, [0.5], color=:black, alpha=0.3, linestyle=:dot, label="")

    p = plot(p1, p2, layout=(1, 2), size=(1000, 450),
             plot_title="Revision Order: Witnessing vs Exposure",
             plot_titlefontsize=13,
             bottom_margin=5Plots.mm, left_margin=5Plots.mm)

    return p
end

p_order = plot_revision_order(h1_results)
savefig(p_order, joinpath(FIGURE_DIR, "fig6_revision_order.png"))
println("  Saved fig6_revision_order.png")

# ============================================================================
# FIGURE 7: COMBINED SUMMARY (MAIN PAPER FIGURE)
# ============================================================================

function plot_main_summary(h1_results, h2_results, params)
    trials = 1:N_TRIALS

    # Get key conditions
    h1_bas = first(filter(r -> r.condition == "Baseline", h1_results))
    h1_exp = first(filter(r -> r.condition == "Exposure", h1_results))
    h1_wit = first(filter(r -> r.condition == "Witnessing", h1_results))
    h1_rd = first(filter(r -> r.condition == "Real Danger", h1_results))
    h1_dis = first(filter(r -> r.condition == "Dissociation", h1_results))

    h2_wit = first(filter(r -> r.condition == "Witnessing", h2_results))
    h2_exp = first(filter(r -> r.condition == "Exposure", h2_results))

    # Panel A: Self-state under all H1 conditions
    p1 = plot(title="A. Self-State Beliefs (H1)",
              xlabel="Trial", ylabel="pD: P(child_helpless)",
              ylims=(0.0, 1.0), legend=:bottomleft)

    for r in h1_results
        traj = smooth(extract_trajectory(r, :pD_child_helpless))
        plot!(p1, trials, traj, label=r.condition,
              color=get_color(r.condition), linestyle=get_linestyle(r.condition),
              linewidth=r.condition == "Witnessing" ? 3.0 : 2.0)
    end
    hline!(p1, [0.5], color=:black, alpha=0.2, linestyle=:dot, label="")

    # Panel B: Threat meaning under all H1 conditions
    p2 = plot(title="B. Threat Meaning Beliefs (H1)",
              xlabel="Trial", ylabel="pD: P(danger)",
              ylims=(0.0, 1.0), legend=:bottomleft)

    for r in h1_results
        traj = smooth(extract_trajectory(r, :pD_danger))
        plot!(p2, trials, traj, label=r.condition,
              color=get_color(r.condition), linestyle=get_linestyle(r.condition),
              linewidth=r.condition == "Witnessing" ? 3.0 : 2.0)
    end
    hline!(p2, [0.5], color=:black, alpha=0.2, linestyle=:dot, label="")

    # Panel C: H1 vs H2 under witnessing
    p3 = plot(title="C. H1 vs H2: Witnessing",
              xlabel="Trial", ylabel="Belief strength",
              ylims=(0.0, 1.0), legend=:topright)

    plot!(p3, trials, smooth(extract_trajectory(h1_wit, :pD_child_helpless)),
          label="H1 child", color=RGB(0.2,0.7,0.3), linewidth=2.5)
    plot!(p3, trials, smooth(extract_trajectory(h1_wit, :pD_danger)),
          label="H1 danger", color=RGB(0.2,0.7,0.3), linewidth=2.5, linestyle=:dash)
    plot!(p3, trials, smooth(extract_trajectory(h2_wit, :pD_child_helpless)),
          label="H2 child", color=RGB(0.8,0.4,0.0), linewidth=2.5)
    plot!(p3, trials, smooth(extract_trajectory(h2_wit, :pD_danger)),
          label="H2 danger", color=RGB(0.8,0.4,0.0), linewidth=2.5, linestyle=:dash)
    hline!(p3, [0.5], color=:black, alpha=0.2, linestyle=:dot, label="")

    # Panel D: P(avoid) across conditions
    p4 = plot(title="D. Avoidance Tendency (H1)",
              xlabel="Trial", ylabel="P(avoid)",
              ylims=(0.0, 1.0), legend=:bottomleft)

    for r in h1_results
        traj = smooth(extract_trajectory(r, :p_avoid))
        plot!(p4, trials, traj, label=r.condition,
              color=get_color(r.condition), linestyle=get_linestyle(r.condition),
              linewidth=r.condition == "Witnessing" ? 3.0 : 2.0)
    end
    hline!(p4, [0.5], color=:black, alpha=0.2, linestyle=:dot, label="")

    # Panel E: Capture index mapping
    E_range = 0.0:0.01:1.0
    C_range = [compute_capture_index(params, E) for E in E_range]

    p5 = plot(title="E. Self-Energy -> Capture",
              xlabel="Self-Energy E_t", ylabel="Capture Index C_t",
              ylims=(0.0, 1.0), legend=false)

    plot!(p5, collect(E_range), C_range, color=:black, linewidth=2.5)

    for config in all_ifs_configs()
        C = compute_capture_index(params, config.E_t)
        scatter!(p5, [config.E_t], [C],
                markersize=7, color=get_color(config.name),
                markerstrokewidth=1.5)
    end
    hline!(p5, [0.5], color=:gray, alpha=0.3, linestyle=:dot)

    # Panel F: Revision order under witnessing
    p6 = plot(title="F. Revision Order (H1 Witnessing)",
              xlabel="Trial", ylabel="Belief strength",
              ylims=(0.0, 1.0), legend=:topright)

    plot!(p6, trials, smooth(extract_trajectory(h1_wit, :pD_child_helpless)),
          label="child_helpless", color=RGB(0.85, 0.4, 0.1), linewidth=2.5)
    plot!(p6, trials, smooth(extract_trajectory(h1_wit, :pD_danger)),
          label="danger", color=RGB(0.2, 0.2, 0.8), linewidth=2.5)
    plot!(p6, trials, smooth(extract_trajectory(h1_wit, :p_avoid)),
          label="P(avoid)", color=RGB(0.5, 0.5, 0.5), linewidth=2.5, linestyle=:dash)
    hline!(p6, [0.5], color=:black, alpha=0.2, linestyle=:dot, label="")

    p = plot(p1, p2, p3, p4, p5, p6,
             layout=(2, 3), size=(1400, 800),
             plot_title="IFS Active Inference: Main Simulation Results",
             plot_titlefontsize=14,
             bottom_margin=5Plots.mm, left_margin=5Plots.mm)

    return p
end

p_summary = plot_main_summary(h1_results, h2_results, params)
savefig(p_summary, joinpath(FIGURE_DIR, "fig7_main_summary.png"))
println("  Saved fig7_main_summary.png")

# ============================================================================
# PRINT DIAGNOSTIC TEST RESULTS
# ============================================================================

println("\n" * "=" ^ 60)
println("DIAGNOSTIC TESTS")
println("=" ^ 60)

function run_tests(h1_results, h2_results)
    h1_bas = first(filter(r -> r.condition == "Baseline", h1_results))
    h1_exp = first(filter(r -> r.condition == "Exposure", h1_results))
    h1_wit = first(filter(r -> r.condition == "Witnessing", h1_results))
    h1_rd = first(filter(r -> r.condition == "Real Danger", h1_results))
    h1_dis = first(filter(r -> r.condition == "Dissociation", h1_results))
    h2_wit = first(filter(r -> r.condition == "Witnessing", h2_results))

    # Test 1: Same activation, different relationship
    bas_final_child = h1_bas.trials[end].pD_child_helpless
    wit_final_child = h1_wit.trials[end].pD_child_helpless
    test1 = wit_final_child < bas_final_child
    println("\nTest 1 (Same activation, different relationship):")
    println("  Baseline final pD_child = $(round(bas_final_child, digits=3))")
    println("  Witnessing final pD_child = $(round(wit_final_child, digits=3))")
    println("  PASS: ", test1 ? "YES" : "NO")

    # Test 2: Order of revision under H1 witnessing
    wit_child_cross = find_crossing_trial(
        extract_trajectory(h1_wit, :pD_child_helpless), 0.7; direction=:below)
    wit_danger_cross = find_crossing_trial(
        extract_trajectory(h1_wit, :pD_danger), 0.7; direction=:below)
    wit_avoid_cross = find_crossing_trial(
        extract_trajectory(h1_wit, :p_avoid), 0.7; direction=:below)

    test2 = !isnothing(wit_child_cross) && !isnothing(wit_danger_cross) &&
            wit_child_cross <= wit_danger_cross
    println("\nTest 2 (Order of revision: child before danger under H1):")
    println("  child crosses at trial: ", isnothing(wit_child_cross) ? "never" : string(wit_child_cross))
    println("  danger crosses at trial: ", isnothing(wit_danger_cross) ? "never" : string(wit_danger_cross))
    println("  avoid crosses at trial: ", isnothing(wit_avoid_cross) ? "never" : string(wit_avoid_cross))
    println("  PASS: ", test2 ? "YES" : "NO")

    # Test 3: Exposure vs witnessing self-state comparison
    exp_final_child = h1_exp.trials[end].pD_child_helpless
    test3 = wit_final_child < exp_final_child
    println("\nTest 3 (Witnessing > Exposure self-state revision):")
    println("  Exposure final pD_child = $(round(exp_final_child, digits=3))")
    println("  Witnessing final pD_child = $(round(wit_final_child, digits=3))")
    println("  PASS: ", test3 ? "YES" : "NO")

    # Test 4: Real danger preserves fear
    rd_final_danger = h1_rd.trials[end].pD_danger
    test4 = rd_final_danger > 0.8
    println("\nTest 4 (Real danger preserves fear):")
    println("  Real Danger final pD_danger = $(round(rd_final_danger, digits=3))")
    println("  PASS: ", test4 ? "YES" : "NO")

    # Test 5: Dissociation shows weak updating
    dis_final_child = h1_dis.trials[end].pD_child_helpless
    test5 = dis_final_child > bas_final_child
    println("\nTest 5 (Dissociation < Baseline updating):")
    println("  Dissociation final pD_child = $(round(dis_final_child, digits=3))")
    println("  Baseline final pD_child = $(round(bas_final_child, digits=3))")
    println("  PASS: ", test5 ? "YES" : "NO")

    # Test 6: H1 vs H2 comparison
    h2_child_cross = find_crossing_trial(
        extract_trajectory(h2_wit, :pD_child_helpless), 0.7; direction=:below)
    h2_danger_cross = find_crossing_trial(
        extract_trajectory(h2_wit, :pD_danger), 0.7; direction=:below)
    # Under H2, danger should cross before child (reversed order)
    test6 = !isnothing(h2_danger_cross) && !isnothing(h2_child_cross) &&
            h2_danger_cross < h2_child_cross
    println("\nTest 6 (H2: danger before child under witnessing):")
    println("  H2 child crosses at trial: ", isnothing(h2_child_cross) ? "never" : string(h2_child_cross))
    println("  H2 danger crosses at trial: ", isnothing(h2_danger_cross) ? "never" : string(h2_danger_cross))
    println("  PASS: ", test6 ? "YES" : "NO")

    # Test 7: Policy ordering under H1
    test7 = !isnothing(wit_child_cross) && !isnothing(wit_avoid_cross) &&
            wit_child_cross < wit_avoid_cross
    println("\nTest 7 (Policy lags self-state under H1 witnessing):")
    println("  child crosses at trial: ", isnothing(wit_child_cross) ? "never" : string(wit_child_cross))
    println("  P(avoid) crosses at trial: ", isnothing(wit_avoid_cross) ? "never" : string(wit_avoid_cross))
    println("  PASS: ", test7 ? "YES" : "NO")

    n_pass = sum([test1, test2, test3, test4, test5, test6, test7])
    println("\n" * "=" ^ 40)
    println("TOTAL: $n_pass / 7 tests passed")
    println("=" ^ 40)
end

run_tests(h1_results, h2_results)

println("\nAll figures saved to: $FIGURE_DIR")
println("Done.")
