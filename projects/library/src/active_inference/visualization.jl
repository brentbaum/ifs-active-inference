"""
    visualization.jl - Visualization functions for Active Inference results

Provides plotting functions for:
- Spider phobia therapy simulation results
- T-maze benchmark results
- General belief evolution visualization
"""

using Plots
using Statistics: mean

# =============================================================================
# Spider Model Visualization
# =============================================================================

"""
    plot_spider_therapy(results; title="", save_path=nothing)

Plot P(safe) evolution over trials from spider therapy simulation.

# Arguments
- `results`: Vector of P(safe) values, one per trial (output of run_spider_aif_therapy)
- `title`: Optional plot title
- `save_path`: Optional path to save the figure

# Returns
A Plots.Plot object showing P(safe) over trials.

# Example
```julia
results = run_spider_aif_therapy(n_trials=200, spider_dangerous=false)
plot_spider_therapy(results; title="Safe Spider Exposure Therapy")
```
"""
function plot_spider_therapy(
    results::Vector{<:Real};
    title::String="Spider Phobia Exposure Therapy",
    save_path::Union{String,Nothing}=nothing
)
    n_trials = length(results)

    p = plot(1:n_trials, results,
        xlabel="Trial",
        ylabel="P(safe)",
        title=title,
        linewidth=2,
        color=:blue,
        legend=false,
        ylims=(0, 1),
        grid=true,
        size=(800, 500)
    )

    # Add reference lines
    hline!(p, [0.5], linestyle=:dash, color=:gray, alpha=0.5, label="")
    hline!(p, [0.1], linestyle=:dot, color=:red, alpha=0.3, label="")  # Initial prior

    if !isnothing(save_path)
        savefig(p, save_path)
        @info "Saved spider therapy plot to $save_path"
    end

    return p
end

"""
    plot_spider_comparison(safe_results, dangerous_results; save_path=nothing)

Plot side-by-side comparison of P(safe) evolution for safe vs dangerous spiders.

# Arguments
- `safe_results`: Vector of P(safe) values for safe spider condition
- `dangerous_results`: Vector of P(safe) values for dangerous spider condition
- `save_path`: Optional path to save the figure

# Returns
A Plots.Plot object with both learning curves.

# Example
```julia
safe_results = run_spider_aif_therapy(n_trials=200, spider_dangerous=false)
dangerous_results = run_spider_aif_therapy(n_trials=200, spider_dangerous=true)
plot_spider_comparison(safe_results, dangerous_results)
```
"""
function plot_spider_comparison(
    safe_results::Vector{<:Real},
    dangerous_results::Vector{<:Real};
    save_path::Union{String,Nothing}=nothing
)
    n_safe = length(safe_results)
    n_dangerous = length(dangerous_results)

    p = plot(1:n_safe, safe_results,
        xlabel="Trial",
        ylabel="P(safe)",
        title="Spider Phobia: Safe vs Dangerous Spider",
        label="Safe Spider",
        linewidth=2,
        color=:green,
        legend=:right,
        ylims=(0, 1),
        grid=true,
        size=(900, 500)
    )

    plot!(p, 1:n_dangerous, dangerous_results,
        label="Dangerous Spider",
        linewidth=2,
        color=:red
    )

    # Add reference line at 50%
    hline!(p, [0.5], linestyle=:dash, color=:gray, alpha=0.5, label="")

    # Add initial prior line (10%)
    hline!(p, [0.1], linestyle=:dot, color=:gray, alpha=0.3, label="Initial P(safe)")

    if !isnothing(save_path)
        savefig(p, save_path)
        @info "Saved spider comparison plot to $save_path"
    end

    return p
end

# =============================================================================
# General Belief Visualization
# =============================================================================

"""
    plot_belief_evolution(beliefs, factor; labels=nothing, title="", save_path=nothing)

Plot beliefs for one state factor over timesteps within a trial.

# Arguments
- `beliefs`: Vector of belief snapshots at each timestep (from trial_history.beliefs)
  Each beliefs[t] is a copy of agent.qs at time t, structured as [timestep][factor]
- `factor::Int`: Which state factor to plot (1-indexed)
- `labels`: Optional vector of state labels
- `title`: Optional plot title
- `save_path`: Optional path to save the figure

# Returns
A Plots.Plot showing belief probabilities over states at each timestep.

# Example
```julia
# Run a T-maze trial
model = build_tmaze_model()
agent = init_agent(model)
env = TMazeEnvironment()
trial = run_trial!(agent, model, env, AIFSettings())

# Plot beliefs about reward location (factor 2)
plot_belief_evolution(trial.beliefs, 2; labels=["Left", "Right"])
```
"""
function plot_belief_evolution(
    beliefs::Vector,
    factor::Int;
    labels::Union{Nothing, Vector{String}}=nothing,
    title::String="Belief Evolution",
    save_path::Union{String,Nothing}=nothing
)
    T = length(beliefs)

    # beliefs[t] is a copy of agent.qs at time t
    # agent.qs is Vector{Vector{Vector{T}}} indexed as qs[timestep][factor]
    # So beliefs[t][t][factor] gives us the belief at timestep t for the factor
    # (the belief about the current timestep, as estimated at the current timestep)
    n_states = length(beliefs[1][1][factor])

    # Create matrix of beliefs: timesteps x states
    # At timestep t, get the belief about the current timestep's state for this factor
    belief_matrix = zeros(T, n_states)
    for t in 1:T
        # beliefs[t][t][factor] = belief about state factor at timestep t (estimated at time t)
        belief_matrix[t, :] = beliefs[t][t][factor]
    end

    # Generate labels if not provided
    if isnothing(labels)
        labels = ["State $s" for s in 1:n_states]
    end

    p = plot(
        xlabel="Timestep",
        ylabel="Probability",
        title=title,
        legend=:outerright,
        ylims=(0, 1),
        grid=true,
        size=(800, 500)
    )

    colors = palette(:tab10)
    for s in 1:n_states
        plot!(p, 1:T, belief_matrix[:, s],
            label=labels[s],
            linewidth=2,
            marker=:circle,
            markersize=5,
            color=colors[mod1(s, length(colors))]
        )
    end

    if !isnothing(save_path)
        savefig(p, save_path)
        @info "Saved belief evolution plot to $save_path"
    end

    return p
end

"""
    plot_belief_heatmap(beliefs, factor; labels=nothing, title="", save_path=nothing)

Plot beliefs as a heatmap (timesteps x states).

# Arguments
- `beliefs`: Vector of belief vectors at each timestep
- `factor::Int`: Which state factor to plot
- `labels`: Optional vector of state labels for y-axis
- `title`: Optional plot title
- `save_path`: Optional path to save the figure

# Returns
A heatmap visualization of beliefs over time.
"""
function plot_belief_heatmap(
    beliefs::Vector,
    factor::Int;
    labels::Union{Nothing, Vector{String}}=nothing,
    title::String="Belief Heatmap",
    save_path::Union{String,Nothing}=nothing
)
    T = length(beliefs)
    n_states = length(beliefs[1][1][factor])

    # Create matrix: states x timesteps (for heatmap orientation)
    belief_matrix = zeros(n_states, T)
    for t in 1:T
        belief_matrix[:, t] = beliefs[t][t][factor]
    end

    if isnothing(labels)
        labels = ["State $s" for s in 1:n_states]
    end

    p = heatmap(1:T, labels, belief_matrix,
        xlabel="Timestep",
        ylabel="State",
        title=title,
        color=:viridis,
        clims=(0, 1),
        size=(800, 400)
    )

    if !isnothing(save_path)
        savefig(p, save_path)
        @info "Saved belief heatmap to $save_path"
    end

    return p
end

# =============================================================================
# T-Maze Visualization
# =============================================================================

"""
    plot_tmaze_trial(trial_history; save_path=nothing)

Visualize a single T-maze trial showing observations, actions, and beliefs.

# Arguments
- `trial_history`: NamedTuple from run_trial! containing observations, actions, beliefs, etc.
- `save_path`: Optional path to save the figure

# Returns
A multi-panel plot showing the trial progression.

# Example
```julia
model = build_tmaze_model()
agent = init_agent(model)
env = TMazeEnvironment(reward_location=1)
settings = AIFSettings()
trial = run_trial!(agent, model, env, settings)
plot_tmaze_trial(trial)
```
"""
function plot_tmaze_trial(
    trial_history;
    save_path::Union{String,Nothing}=nothing
)
    T = length(trial_history.observations)

    # Location labels
    loc_labels = ["Center", "Cue", "Left", "Right"]
    rew_labels = ["Left", "Right"]
    cue_labels = ["Null", "Cue Left", "Cue Right"]
    reward_labels = ["No Reward", "Reward"]
    action_labels = ["Stay", "Go Cue", "Go Left", "Go Right"]

    # Extract data
    locations = [trial_history.states[t][1] for t in 1:T]
    reward_loc = trial_history.states[1][2]  # Doesn't change
    cue_obs = [trial_history.observations[t][2] for t in 1:T]
    reward_obs = [trial_history.observations[t][3] for t in 1:T]

    # Panel 1: Location trajectory
    p1 = plot(1:T, locations,
        ylabel="Location",
        title="Agent Location",
        yticks=(1:4, loc_labels),
        marker=:circle,
        markersize=8,
        linewidth=2,
        legend=false,
        ylims=(0.5, 4.5),
        xlims=(0.5, T+0.5)
    )

    # Panel 2: Belief about reward location
    # beliefs[t] is agent.qs snapshot at time t, structured as qs[timestep][factor]
    # We want beliefs[t][t][2] = belief about factor 2 at timestep t
    belief_matrix = zeros(T, 2)
    for t in 1:T
        belief_matrix[t, :] = trial_history.beliefs[t][t][2]  # Factor 2 = reward location
    end

    p2 = plot(1:T, belief_matrix[:, 1],
        label="P(Left)",
        ylabel="Probability",
        title="Belief: Reward Location (True: $(rew_labels[reward_loc]))",
        linewidth=2,
        marker=:circle,
        legend=:right,
        ylims=(0, 1)
    )
    plot!(p2, 1:T, belief_matrix[:, 2],
        label="P(Right)",
        linewidth=2,
        marker=:square
    )

    # Panel 3: Cue observation
    p3 = scatter(1:T, cue_obs,
        ylabel="Cue",
        title="Cue Observation",
        yticks=(1:3, cue_labels),
        markersize=10,
        legend=false,
        ylims=(0.5, 3.5),
        xlims=(0.5, T+0.5)
    )

    # Panel 4: Policy probabilities (if available)
    if trial_history.qpi[1] !== nothing
        n_policies = length(trial_history.qpi[1])
        p4 = plot(
            xlabel="Timestep",
            ylabel="Probability",
            title="Policy Probabilities",
            legend=:outerright,
            ylims=(0, 1)
        )

        policy_labels = ["Cue->Left", "Cue->Right", "Left->Stay", "Right->Stay"]
        for pi in 1:n_policies
            probs = [trial_history.qpi[t] === nothing ? NaN : trial_history.qpi[t][pi] for t in 1:T]
            plot!(p4, 1:T, probs,
                label=policy_labels[pi],
                linewidth=2,
                marker=:circle
            )
        end
    else
        p4 = plot(title="No Policy Data", legend=false)
    end

    # Combine panels
    p = plot(p1, p2, p3, p4,
        layout=(2, 2),
        size=(1000, 700),
        margin=5Plots.mm
    )

    if !isnothing(save_path)
        savefig(p, save_path)
        @info "Saved T-maze trial plot to $save_path"
    end

    return p
end

"""
    plot_tmaze_policy_probs(trial_history; save_path=nothing)

Plot policy probabilities over time for a T-maze trial.

# Arguments
- `trial_history`: NamedTuple from run_trial!
- `save_path`: Optional path to save the figure

# Returns
A Plots.Plot showing policy probabilities at each timestep.
"""
function plot_tmaze_policy_probs(
    trial_history;
    save_path::Union{String,Nothing}=nothing
)
    T = length(trial_history.observations)
    policy_labels = ["Cue->Left", "Cue->Right", "Left->Stay", "Right->Stay"]

    p = plot(
        xlabel="Timestep",
        ylabel="Policy Probability",
        title="T-Maze Policy Probabilities",
        legend=:outerright,
        ylims=(0, 1),
        grid=true,
        size=(800, 500)
    )

    colors = [:blue, :orange, :green, :red]

    for pi in 1:4
        probs = Float64[]
        for t in 1:T
            if trial_history.qpi[t] !== nothing && length(trial_history.qpi[t]) >= pi
                push!(probs, trial_history.qpi[t][pi])
            else
                push!(probs, NaN)
            end
        end

        plot!(p, 1:T, probs,
            label=policy_labels[pi],
            linewidth=2,
            marker=:circle,
            markersize=6,
            color=colors[pi]
        )
    end

    if !isnothing(save_path)
        savefig(p, save_path)
        @info "Saved T-maze policy plot to $save_path"
    end

    return p
end

"""
    plot_tmaze_summary(test_results; save_path=nothing)

Plot summary statistics from T-maze test runs.

# Arguments
- `test_results`: NamedTuple from run_tmaze_test or run_tmaze_comparison
- `save_path`: Optional path to save the figure

# Returns
A bar chart showing cue check rate, reward rate, and correct choice rate.

# Example
```julia
results = run_tmaze_test(n_trials=100)
plot_tmaze_summary(results)
```
"""
function plot_tmaze_summary(
    test_results;
    save_path::Union{String,Nothing}=nothing
)
    categories = ["Cue Check Rate", "Reward Rate", "Correct Choice"]
    values = [
        test_results.cue_check_rate * 100,
        test_results.reward_rate * 100,
        test_results.correct_rate * 100
    ]

    p = bar(categories, values,
        ylabel="Percentage (%)",
        title="T-Maze Performance Summary",
        legend=false,
        ylims=(0, 100),
        color=[:blue, :green, :purple],
        size=(600, 400)
    )

    # Add value labels on bars
    annotate!(p, [(i, values[i] + 3, text("$(round(values[i], digits=1))%", 10)) for i in 1:3])

    if !isnothing(save_path)
        savefig(p, save_path)
        @info "Saved T-maze summary to $save_path"
    end

    return p
end

"""
    plot_tmaze_comparison_summary(comparison_results; save_path=nothing)

Plot comparison of T-maze results with and without state information gain.

# Arguments
- `comparison_results`: NamedTuple from run_tmaze_comparison
- `save_path`: Optional path to save the figure

# Returns
A grouped bar chart comparing epistemic vs pragmatic agent behavior.
"""
function plot_tmaze_comparison_summary(
    comparison_results;
    save_path::Union{String,Nothing}=nothing
)
    epistemic = comparison_results.with_info_gain
    pragmatic = comparison_results.without_info_gain

    categories = ["Cue Check", "Reward", "Correct"]

    epistemic_vals = [
        epistemic.cue_check_rate * 100,
        epistemic.reward_rate * 100,
        epistemic.correct_rate * 100
    ]

    pragmatic_vals = [
        pragmatic.cue_check_rate * 100,
        pragmatic.reward_rate * 100,
        pragmatic.correct_rate * 100
    ]

    x = 1:3

    p = groupedbar(categories, [epistemic_vals pragmatic_vals],
        ylabel="Percentage (%)",
        title="T-Maze: Epistemic vs Pragmatic Agent",
        label=["With Info Gain" "Without Info Gain"],
        ylims=(0, 100),
        size=(700, 500),
        bar_width=0.7,
        legend=:topright
    )

    if !isnothing(save_path)
        savefig(p, save_path)
        @info "Saved T-maze comparison to $save_path"
    end

    return p
end

# =============================================================================
# Multi-Trial Analysis
# =============================================================================

"""
    plot_learning_curve(p_safe_history; window=10, title="", save_path=nothing)

Plot P(safe) learning curve with smoothing.

# Arguments
- `p_safe_history`: Vector of P(safe) values over trials
- `window`: Moving average window size (default: 10)
- `title`: Optional plot title
- `save_path`: Optional path to save the figure

# Returns
A plot with raw values and smoothed learning curve.
"""
function plot_learning_curve(
    p_safe_history::Vector{<:Real};
    window::Int=10,
    title::String="Learning Curve",
    save_path::Union{String,Nothing}=nothing
)
    n = length(p_safe_history)

    # Compute moving average
    smoothed = zeros(n)
    for i in 1:n
        start_idx = max(1, i - window + 1)
        smoothed[i] = mean(p_safe_history[start_idx:i])
    end

    p = plot(1:n, p_safe_history,
        label="Raw",
        alpha=0.3,
        color=:blue,
        xlabel="Trial",
        ylabel="P(safe)",
        title=title,
        ylims=(0, 1),
        size=(800, 500)
    )

    plot!(p, 1:n, smoothed,
        label="Smoothed (window=$window)",
        linewidth=3,
        color=:blue
    )

    if !isnothing(save_path)
        savefig(p, save_path)
        @info "Saved learning curve to $save_path"
    end

    return p
end

# =============================================================================
# Coherence Therapy Visualization
# =============================================================================

"""
    plot_ct_trajectories(all_results; save_path=nothing)

Plot P(avoid) trajectories for all conditions in the Coherence Therapy simulation.
Shows the key comparison: CT step function vs CBT gradual resolution.

# Arguments
- `all_results`: NamedTuple with :baseline, :cbt, :ct, :ct_dangerous fields
- `save_path`: Optional path to save the figure

# Returns
A multi-panel plot showing all condition trajectories.
"""
function plot_ct_trajectories(all_results; save_path::Union{String,Nothing}=nothing)
    # Aggregate trajectories
    function agg(results)
        n_trials = length(results[1].p_avoid)
        n_reps = length(results)
        traj = zeros(n_trials, n_reps)
        for (i, r) in enumerate(results)
            traj[:, i] = r.p_avoid
        end
        m = vec(mean(traj, dims=2))
        s = vec(std(traj, dims=2))
        ci_lo = m .- 1.96 * s / sqrt(n_reps)
        ci_hi = m .+ 1.96 * s / sqrt(n_reps)
        return (mean=m, ci_lo=ci_lo, ci_hi=ci_hi)
    end

    baseline = agg(all_results.baseline)
    cbt = agg(all_results.cbt)
    ct = agg(all_results.ct)
    ctd = agg(all_results.ct_dangerous)

    n_trials = length(baseline.mean)
    trials = 1:n_trials

    # Create main comparison plot
    p = plot(
        xlabel="Trial",
        ylabel="P(avoid)",
        title="Coherence Therapy vs CBT: Avoidance Trajectories",
        legend=:right,
        ylims=(-0.05, 1.05),
        size=(900, 600),
        grid=true,
        gridlinewidth=0.5,
        gridalpha=0.3
    )

    # Colors
    c_baseline = RGB(0.7, 0.7, 0.7)
    c_cbt = RGB(0.2, 0.6, 0.9)
    c_ct = RGB(0.1, 0.7, 0.3)
    c_ctd = RGB(0.9, 0.4, 0.2)

    # Plot with confidence intervals
    plot!(p, trials, baseline.mean, ribbon=(baseline.mean .- baseline.ci_lo, baseline.ci_hi .- baseline.mean),
        fillalpha=0.2, color=c_baseline, linewidth=3, label="Baseline (modular)")

    plot!(p, trials, cbt.mean, ribbon=(cbt.mean .- cbt.ci_lo, cbt.ci_hi .- cbt.mean),
        fillalpha=0.2, color=c_cbt, linewidth=3, label="CBT (gradual learning)")

    plot!(p, trials, ct.mean, ribbon=(ct.mean .- ct.ci_lo, ct.ci_hi .- ct.mean),
        fillalpha=0.2, color=c_ct, linewidth=3, label="CT (modularity-breaking)")

    plot!(p, trials, ctd.mean, ribbon=(ctd.mean .- ctd.ci_lo, ctd.ci_hi .- ctd.mean),
        fillalpha=0.2, color=c_ctd, linewidth=3, label="CT-dangerous")

    # Add intervention marker
    vline!(p, [51], linestyle=:dash, color=:black, alpha=0.5, linewidth=2, label="CT Intervention")

    # Add annotations
    annotate!(p, [(75, 0.95, text("Baseline: maintains avoidance", 8, :gray)),
                  (75, 0.15, text("CBT: gradual resolution", 8, c_cbt)),
                  (60, 0.5, text("CT: step function", 8, c_ct, :left))])

    if !isnothing(save_path)
        savefig(p, save_path)
        @info "Saved CT trajectories to $save_path"
    end

    return p
end

"""
    plot_ct_mechanism_comparison(all_results; save_path=nothing)

Plot side-by-side comparison highlighting the CT vs CBT mechanism difference.
"""
function plot_ct_mechanism_comparison(all_results; save_path::Union{String,Nothing}=nothing)
    function agg(results)
        n_trials = length(results[1].p_avoid)
        n_reps = length(results)
        traj = zeros(n_trials, n_reps)
        for (i, r) in enumerate(results)
            traj[:, i] = r.p_avoid
        end
        return vec(mean(traj, dims=2))
    end

    cbt = agg(all_results.cbt)
    ct = agg(all_results.ct)
    n_trials = length(cbt)
    trials = 1:n_trials

    # Create two-panel plot
    p1 = plot(trials, cbt,
        xlabel="Trial", ylabel="P(avoid)",
        title="CBT: Gradual Parameter Learning",
        linewidth=3, color=RGB(0.2, 0.6, 0.9),
        legend=false, ylims=(-0.05, 1.05),
        grid=true, gridlinewidth=0.5
    )
    hline!(p1, [0.5], linestyle=:dot, color=:gray, alpha=0.5)

    # Add gradient annotation
    annotate!(p1, [(50, 0.7, text("D₃ belief updating\nover many trials", 9, :center))])

    p2 = plot(trials, ct,
        xlabel="Trial", ylabel="P(avoid)",
        title="CT: Structural Change (Modularity-Breaking)",
        linewidth=3, color=RGB(0.1, 0.7, 0.3),
        legend=false, ylims=(-0.05, 1.05),
        grid=true, gridlinewidth=0.5
    )
    vline!(p2, [51], linestyle=:dash, color=:red, alpha=0.7, linewidth=2)
    hline!(p2, [0.5], linestyle=:dot, color=:gray, alpha=0.5)

    # Add step annotation
    annotate!(p2, [(51, 0.5, text("Intervention:\nSchema becomes\ncontext-sensitive", 9, :left))])

    p = plot(p1, p2, layout=(1, 2), size=(1100, 450), margin=5Plots.mm)

    if !isnothing(save_path)
        savefig(p, save_path)
        @info "Saved CT mechanism comparison to $save_path"
    end

    return p
end

"""
    plot_ct_schematic()

Create a schematic diagram showing the model structure and therapy mechanism.
"""
function plot_ct_schematic(; save_path::Union{String,Nothing}=nothing)
    # Create a conceptual diagram using annotations
    p = plot(
        xlims=(0, 10), ylims=(0, 8),
        aspect_ratio=:equal,
        axis=false, grid=false,
        legend=false,
        size=(900, 700),
        title="Coherence Therapy Active Inference Model"
    )

    # Box colors
    modular_color = RGB(0.9, 0.7, 0.7)
    integrated_color = RGB(0.7, 0.9, 0.7)

    # Modular mode box (left)
    plot!(p, Shape([1, 4, 4, 1], [4.5, 4.5, 7.5, 7.5]), color=modular_color, alpha=0.5)
    annotate!(p, [(2.5, 7.2, text("MODULAR MODE", 11, :bold, :center)),
                  (2.5, 6.5, text("Context-blind", 10, :center)),
                  (2.5, 6.0, text("• A₁ uniform (can't process cues)", 8, :left)),
                  (2.5, 5.5, text("• D₁ fearful prior", 8, :left)),
                  (2.5, 5.0, text("• D₃ learning blocked", 8, :left))])

    # Integrated mode box (right)
    plot!(p, Shape([6, 9, 9, 6], [4.5, 4.5, 7.5, 7.5]), color=integrated_color, alpha=0.5)
    annotate!(p, [(7.5, 7.2, text("INTEGRATED MODE", 11, :bold, :center)),
                  (7.5, 6.5, text("Context-aware", 10, :center)),
                  (7.5, 6.0, text("• A₁ identity (processes cues)", 8, :left)),
                  (7.5, 5.5, text("• D₁ accurate prior", 8, :left)),
                  (7.5, 5.0, text("• D₃ learning enabled", 8, :left))])

    # Arrow between modes
    plot!(p, [4.2, 5.8], [6, 6], arrow=true, color=:black, linewidth=2)
    annotate!(p, [(5, 6.3, text("Therapist\nIntervention", 9, :center))])

    # Outcome boxes
    # Avoidance outcome (left bottom)
    plot!(p, Shape([1, 4, 4, 1], [1, 1, 3, 3]), color=RGB(1.0, 0.8, 0.8), alpha=0.5)
    annotate!(p, [(2.5, 2.5, text("OUTCOME", 10, :bold, :center)),
                  (2.5, 2.0, text("P(avoid) ≈ 0.96", 9, :center)),
                  (2.5, 1.5, text("Pathological avoidance", 8, :center))])

    # Approach outcome (right bottom)
    plot!(p, Shape([6, 9, 9, 6], [1, 1, 3, 3]), color=RGB(0.8, 1.0, 0.8), alpha=0.5)
    annotate!(p, [(7.5, 2.5, text("OUTCOME", 10, :bold, :center)),
                  (7.5, 2.0, text("P(approach) ≈ 0.97", 9, :center)),
                  (7.5, 1.5, text("Context-appropriate engagement", 8, :center))])

    # Arrows from modes to outcomes
    plot!(p, [2.5, 2.5], [4.3, 3.2], arrow=true, color=:gray, linewidth=1.5)
    plot!(p, [7.5, 7.5], [4.3, 3.2], arrow=true, color=:gray, linewidth=1.5)

    # Key insight box at bottom
    annotate!(p, [(5, 0.4, text("Key Insight: Resolution via structural change, not belief updating (D₃ change ≈ 0)", 10, :center, RGB(0.3, 0.3, 0.6)))])

    if !isnothing(save_path)
        savefig(p, save_path)
        @info "Saved CT schematic to $save_path"
    end

    return p
end

"""
    plot_ct_all_panels(all_results; save_dir=nothing)

Generate all Coherence Therapy visualization panels.

# Arguments
- `all_results`: Results from run_all_conditions()
- `save_dir`: Optional directory to save all plots

# Returns
NamedTuple with all plot objects
"""
function plot_ct_all_panels(all_results; save_dir::Union{String,Nothing}=nothing)
    plots = Dict{Symbol, Any}()

    # Main trajectory plot
    plots[:trajectories] = plot_ct_trajectories(all_results)

    # Mechanism comparison
    plots[:mechanism] = plot_ct_mechanism_comparison(all_results)

    # Schematic
    plots[:schematic] = plot_ct_schematic()

    if !isnothing(save_dir)
        mkpath(save_dir)
        savefig(plots[:trajectories], joinpath(save_dir, "ct_trajectories.png"))
        savefig(plots[:mechanism], joinpath(save_dir, "ct_mechanism_comparison.png"))
        savefig(plots[:schematic], joinpath(save_dir, "ct_schematic.png"))

        # Also save as PDF for publication
        savefig(plots[:trajectories], joinpath(save_dir, "ct_trajectories.pdf"))
        savefig(plots[:mechanism], joinpath(save_dir, "ct_mechanism_comparison.pdf"))

        @info "Saved all CT plots to $save_dir"
    end

    return (plots...,)
end

# =============================================================================
# Discovery Process Visualization (Chamberlin 2022 Extension)
# =============================================================================

"""
    plot_discovery_trajectory(result::CTDiscoveryResult; title="Discovery Process")

Plot Discovery simulation showing P(avoid), access level, and precision over trials.
"""
function plot_discovery_trajectory(result; title::String="Discovery Process: Gradual Schema Accessibility")
    n_trials = length(result.p_avoid)

    # Create 3-panel plot
    l = @layout [a; b; c]

    # Panel 1: P(avoid) trajectory
    p1 = plot(1:n_trials, result.p_avoid,
        ylabel="P(avoid)",
        linewidth=2,
        color=:red,
        legend=false,
        ylims=(0, 1),
        grid=true,
        title=title)

    # Add P(approach) on same axis
    plot!(p1, 1:n_trials, result.p_approach,
        linewidth=2,
        color=:green,
        linestyle=:dash,
        label="")

    # Panel 2: Schema access level (as step function)
    access_labels = ["Implicit", "Partial", "Explicit"]
    p2 = plot(1:n_trials, result.access_trajectory,
        ylabel="Access Level",
        linewidth=2,
        color=:purple,
        seriestype=:steppost,
        legend=false,
        ylims=(0.5, 3.5),
        yticks=(1:3, access_labels),
        grid=true)

    # Shade regions by access level
    for i in 1:3
        mask = result.access_trajectory .== i
        if any(mask)
            first_trial = findfirst(mask)
            last_trial = findlast(mask)
            if !isnothing(first_trial) && !isnothing(last_trial)
                vspan!(p2, [first_trial, last_trial], alpha=0.1,
                    color=[:red, :yellow, :green][i], label="")
            end
        end
    end

    # Panel 3: Annealed precision (exploration → exploitation)
    p3 = plot(1:n_trials, result.precision_trajectory,
        xlabel="Trial",
        ylabel="Policy Precision (γ)",
        linewidth=2,
        color=:blue,
        legend=false,
        grid=true)

    # Annotations
    annotate!(p3, [(n_trials * 0.1, minimum(result.precision_trajectory) + 0.5,
        text("Exploration", 8, :left)),
        (n_trials * 0.9, maximum(result.precision_trajectory) - 0.5,
        text("Exploitation", 8, :right))])

    return plot(p1, p2, p3, layout=l, size=(800, 700))
end

"""
    plot_discovery_comparison(results_dict; save_path=nothing)

Compare different Discovery conditions (fast, standard, slow).
"""
function plot_discovery_comparison(results_dict; save_path::Union{String,Nothing}=nothing)
    colors = Dict(
        :fast => :green,
        :standard => :blue,
        :slow => :orange
    )

    labels = Dict(
        :fast => "Fast Discovery",
        :standard => "Standard Discovery",
        :slow => "Slow Discovery"
    )

    # P(avoid) comparison
    p1 = plot(title="Discovery Process Comparison: P(avoid)",
        xlabel="Trial", ylabel="Mean P(avoid)",
        ylims=(0, 1), grid=true, legend=:topright)

    for (name, results) in results_dict
        agg = aggregate_discovery_trajectories(results, :p_avoid)
        n_trials = length(agg.mean)
        plot!(p1, 1:n_trials, agg.mean,
            ribbon=(agg.mean .- agg.ci_lower, agg.ci_upper .- agg.mean),
            fillalpha=0.2,
            linewidth=2,
            color=get(colors, name, :gray),
            label=get(labels, name, string(name)))
    end

    # Access level comparison
    p2 = plot(title="Schema Accessibility Over Time",
        xlabel="Trial", ylabel="Mean Access Level",
        ylims=(0.5, 3.5),
        yticks=(1:3, ["Implicit", "Partial", "Explicit"]),
        grid=true, legend=:bottomright)

    for (name, results) in results_dict
        agg = aggregate_discovery_trajectories(results, :access_trajectory)
        n_trials = length(agg.mean)
        plot!(p2, 1:n_trials, agg.mean,
            ribbon=(agg.mean .- agg.ci_lower, agg.ci_upper .- agg.mean),
            fillalpha=0.2,
            linewidth=2,
            color=get(colors, name, :gray),
            label=get(labels, name, string(name)))
    end

    # Combined plot
    combined = plot(p1, p2, layout=(2, 1), size=(900, 700))

    if !isnothing(save_path)
        savefig(combined, save_path)
        @info "Saved Discovery comparison plot to $save_path"
    end

    return combined
end

"""
    plot_discovery_mechanism(result; title="Discovery Mechanism")

Detailed view of Discovery mechanism showing how interpolation works.
"""
function plot_discovery_mechanism(result; title::String="Discovery: Simulated Annealing Mechanism")
    n_trials = length(result.p_avoid)

    l = @layout [a b; c d]

    # Panel 1: Behavioral trajectory
    p1 = plot(1:n_trials, result.p_avoid,
        ylabel="P(avoid)",
        linewidth=2,
        color=:red,
        label="Avoid",
        title="Behavioral Change",
        ylims=(0, 1),
        legend=:right)
    plot!(p1, 1:n_trials, result.p_approach,
        linewidth=2,
        color=:green,
        label="Approach")

    # Mark transitions
    for i in 2:n_trials
        if result.access_trajectory[i] > result.access_trajectory[i-1]
            vline!(p1, [i], color=:purple, linestyle=:dash, alpha=0.5, label="")
        end
    end

    # Panel 2: Mixing coefficient (α) over time
    α_trajectory = [CT_ACCESS_MIXING[a] for a in result.access_trajectory]
    p2 = plot(1:n_trials, α_trajectory,
        ylabel="Mixing Coef. (α)",
        linewidth=2,
        color=:purple,
        seriestype=:steppost,
        title="Context-Sensitivity",
        ylims=(0, 1),
        legend=false)
    annotate!(p2, [(10, 0.1, text("Modular", 8)), (90, 0.9, text("Integrated", 8))])

    # Panel 3: Policy precision (γ)
    p3 = plot(1:n_trials, result.precision_trajectory,
        xlabel="Trial",
        ylabel="Precision (γ)",
        linewidth=2,
        color=:blue,
        title="Simulated Annealing",
        legend=false)
    annotate!(p3, [(10, minimum(result.precision_trajectory) + 1, text("Exploration", 8)),
        (90, maximum(result.precision_trajectory) - 1, text("Exploitation", 8))])

    # Panel 4: D3 belief trajectory
    p_threat = [d[1] / sum(d) for d in result.d3_trajectory]
    p4 = plot(1:n_trials, p_threat,
        xlabel="Trial",
        ylabel="P(threatening)",
        linewidth=2,
        color=:orange,
        title="Schema Belief (D3)",
        ylims=(0, 1),
        legend=false)

    return plot(p1, p2, p3, p4, layout=l, size=(1000, 700), plot_title=title)
end
