"""
    Paper Figure Comparison Script

Reproduce Figure 2 from Eckertal et al. (2023) with our implementation.

KEY FIX: We now plot the INFERRED POSTERIOR (qs) instead of the Dirichlet prior (pD).
- qs is the belief AFTER seeing the observation - highly responsive
- pD is the slowly accumulating Dirichlet concentration - very slow
We overlay pD with dashed lines for comparison.

Paper setup (from Figure 2):
- T = 40 trials
- Context switch at t=20 (friendly → hostile or hostile → friendly)
- Beliefs swing from ~0.05 to ~0.95 based on observations

Usage:
    julia --project=. scripts/paper_figure_comparison.jl
"""

using Pkg
Pkg.activate(".")

include("../src/active_inference/ActiveInferenceCore.jl")
using .ActiveInferenceCore
using Plots

println("Testing belief dynamics (plotting qs posterior + dashed pD prior)...")

# =============================================================================
# Test 1: Figure 2A pattern - friendly → hostile
# =============================================================================
println("\n1. Figure 2A pattern (friendly → hostile):")
results_2A = run_trust_game_phases(
    profile=healthy_profile_paper(),
    phases=[(:friendly, 20), (:hostile, 20)],
    verbose=true
)
println("   Final P(friendly) = $(round(results_2A.belief_friendly[end]*100, digits=1))%")

# =============================================================================
# Test 2: Figure 2B pattern - hostile → friendly
# =============================================================================
println("\n2. Figure 2B pattern (hostile → friendly):")
results_2B = run_trust_game_phases(
    profile=healthy_profile_paper(),
    phases=[(:hostile, 20), (:friendly, 20)],
    verbose=true
)
println("   Final P(friendly) = $(round(results_2B.belief_friendly[end]*100, digits=1))%")

# =============================================================================
# Create comparison figure (2A and 2B side by side)
# =============================================================================
println("\n\nGenerating comparison plot...")

fig = plot(
    layout=(1, 2),
    size=(1400, 500),
    plot_title="Trust Game: Healthy Agent Belief Dynamics (qs posterior)"
)

# Plot 2A (friendly → hostile)
for (i, (results, title)) in enumerate([
    (results_2A, "Figure 2A: Friendly → Hostile"),
    (results_2B, "Figure 2B: Hostile → Friendly")
])
    n = length(results.choices)
    phase_switch = results.phase_boundaries[2]

    plot!(fig, subplot=i,
        title=title,
        xlabel="Trial (t)",
        ylabel="P(context)",
        ylims=(-0.05, 1.05),
        xlims=(0, n),
        legend=:right
    )

    # Phase shading
    first_partner = results.partner_types[1]
    second_partner = results.partner_types[phase_switch]

    color1 = first_partner == :friendly ? :lightblue : :mistyrose
    color2 = second_partner == :friendly ? :lightblue : :mistyrose

    vspan!(fig, subplot=i, [0, phase_switch-0.5],
           fillcolor=color1, fillalpha=0.4, linecolor=:transparent, label="")
    vspan!(fig, subplot=i, [phase_switch-0.5, n],
           fillcolor=color2, fillalpha=0.4, linecolor=:transparent, label="")

    # Belief lines (qs posterior)
    plot!(fig, subplot=i, 0:n-1, results.belief_friendly,
          label="cooperative", color=:blue, linewidth=2, marker=:circle, markersize=4)
    plot!(fig, subplot=i, 0:n-1, results.belief_hostile,
          label="hostile", color=:red, linewidth=2, marker=:circle, markersize=4)
    plot!(fig, subplot=i, 0:n-1, results.belief_neutral,
          label="random", color=:gray, linewidth=1.5, marker=:diamond, markersize=3)

    # Dirichlet priors (pD) as dashed lines
    plot!(fig, subplot=i, 0:n-1, results.pD_friendly,
          label="cooperative (pD)", color=:blue, linewidth=1.2, linestyle=:dash, alpha=0.7)
    plot!(fig, subplot=i, 0:n-1, results.pD_hostile,
          label="hostile (pD)", color=:red, linewidth=1.2, linestyle=:dash, alpha=0.7)
    plot!(fig, subplot=i, 0:n-1, results.pD_neutral,
          label="random (pD)", color=:gray, linewidth=1.0, linestyle=:dash, alpha=0.7)

    # Action markers at belief_hostile + offset
    for t in 1:n
        x = t - 1
        choice = results.choices[t]
        reward = results.rewards[t]
        y_marker = min(results.belief_hostile[t] + 0.08, 0.95)

        if choice == 1  # CHOICE_SHARE
            if reward == 1  # REWARD_HIGH
                scatter!(fig, subplot=i, [x], [y_marker],
                        marker=:utriangle, markersize=5, color=:blue, label="")
            else
                scatter!(fig, subplot=i, [x], [y_marker],
                        marker=:dtriangle, markersize=5, color=:red, label="")
            end
        else
            scatter!(fig, subplot=i, [x], [y_marker],
                    marker=:star5, markersize=4, color=:black, label="")
        end
    end
end

savefig(fig, "paper_figure_comparison.png")
println("Saved to paper_figure_comparison.png")

# =============================================================================
# Create individual paper-style figures
# =============================================================================
println("\n\nGenerating individual paper-style figures...")

plot_trust_game_paper_style(
    results_2A,
    title="Healthy-optimistic (Friendly → Hostile)",
    save_path="trust_game_figure2A_style.png",
    plot_pD=true
)

plot_trust_game_paper_style(
    results_2B,
    title="Healthy-optimistic (Hostile → Friendly)",
    save_path="trust_game_figure2B_style.png",
    plot_pD=true
)

println("\n✓ All figures generated!")
println("\nFiles created:")
println("  - paper_figure_comparison.png   (side-by-side 2A and 2B)")
println("  - trust_game_figure2A_style.png (friendly → hostile)")
println("  - trust_game_figure2B_style.png (hostile → friendly)")
