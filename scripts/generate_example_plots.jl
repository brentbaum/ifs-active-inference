"""
    generate_example_plots.jl

Test script for visualization functions. Generates example plots and saves them to figures/.
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

include(joinpath(@__DIR__, "..", "src", "active_inference", "ActiveInferenceCore.jl"))
using .ActiveInferenceCore
using Random

# Set random seed for reproducibility
Random.seed!(42)

# Output directory
FIGURES_DIR = joinpath(@__DIR__, "..", "figures")
mkpath(FIGURES_DIR)

println("=" ^ 60)
println("Generating Example Plots for Active Inference")
println("=" ^ 60)

# =============================================================================
# 1. Spider Therapy Plots
# =============================================================================

println("\n[1/4] Running Spider Therapy Simulations...")

# Run safe spider therapy
println("  - Safe spider simulation (100 trials)...")
safe_results = run_spider_aif_therapy(
    n_trials=100,
    spider_dangerous=false
)

# Run dangerous spider therapy
println("  - Dangerous spider simulation (100 trials)...")
dangerous_results = run_spider_aif_therapy(
    n_trials=100,
    spider_dangerous=true
)

# Generate plots
println("  - Generating spider therapy plots...")

p1 = plot_spider_therapy(safe_results;
    title="Safe Spider Exposure Therapy",
    save_path=joinpath(FIGURES_DIR, "spider_therapy_safe.png")
)
println("    Saved: figures/spider_therapy_safe.png")

p2 = plot_spider_comparison(safe_results, dangerous_results;
    save_path=joinpath(FIGURES_DIR, "spider_comparison.png")
)
println("    Saved: figures/spider_comparison.png")

p3 = plot_learning_curve(safe_results;
    window=15,
    title="Safe Spider Learning Curve (smoothed)",
    save_path=joinpath(FIGURES_DIR, "spider_learning_curve.png")
)
println("    Saved: figures/spider_learning_curve.png")

# =============================================================================
# 2. T-Maze Plots
# =============================================================================

println("\n[2/4] Running T-Maze Simulations...")

# Build model and run a single trial
model = build_tmaze_model()
settings = AIFSettings(
    gamma=16.0,
    alpha=16.0,
    use_ambiguity=true,
    use_utility=true,
    use_states_info_gain=true
)

# Run a trial with reward on the left
println("  - Single trial simulation (reward left)...")
env = TMazeEnvironment(reward_location=1)
agent = init_agent(model)
trial_history = run_trial!(agent, model, env, settings)

# Plot the trial
println("  - Generating T-maze trial plot...")
p4 = plot_tmaze_trial(trial_history;
    save_path=joinpath(FIGURES_DIR, "tmaze_trial.png")
)
println("    Saved: figures/tmaze_trial.png")

# Policy probabilities plot
p5 = plot_tmaze_policy_probs(trial_history;
    save_path=joinpath(FIGURES_DIR, "tmaze_policy_probs.png")
)
println("    Saved: figures/tmaze_policy_probs.png")

# =============================================================================
# 3. T-Maze Test Summary
# =============================================================================

println("\n[3/4] Running T-Maze Test (50 trials)...")

test_results = run_tmaze_test(n_trials=50)
println("  - Cue check rate: $(round(test_results.cue_check_rate * 100, digits=1))%")
println("  - Reward rate: $(round(test_results.reward_rate * 100, digits=1))%")
println("  - Correct rate: $(round(test_results.correct_rate * 100, digits=1))%")

p6 = plot_tmaze_summary(test_results;
    save_path=joinpath(FIGURES_DIR, "tmaze_summary.png")
)
println("    Saved: figures/tmaze_summary.png")

# =============================================================================
# 4. Belief Evolution Plot
# =============================================================================

println("\n[4/4] Generating Belief Evolution Plots...")

# Use the trial history from above
p7 = plot_belief_evolution(trial_history.beliefs, 2;
    labels=["Reward Left", "Reward Right"],
    title="T-Maze: Belief About Reward Location",
    save_path=joinpath(FIGURES_DIR, "tmaze_belief_evolution.png")
)
println("    Saved: figures/tmaze_belief_evolution.png")

p8 = plot_belief_heatmap(trial_history.beliefs, 1;
    labels=["Center", "Cue", "Left", "Right"],
    title="T-Maze: Location Belief Heatmap",
    save_path=joinpath(FIGURES_DIR, "tmaze_belief_heatmap.png")
)
println("    Saved: figures/tmaze_belief_heatmap.png")

# =============================================================================
# Summary
# =============================================================================

println("\n" * "=" ^ 60)
println("All plots saved to: $FIGURES_DIR")
println("=" ^ 60)

# List generated files
files = readdir(FIGURES_DIR)
png_files = filter(f -> endswith(f, ".png"), files)
println("\nGenerated $(length(png_files)) figures:")
for f in sort(png_files)
    println("  - $f")
end
