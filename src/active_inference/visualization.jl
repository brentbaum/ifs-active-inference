"""
    visualization.jl - Visualization functions for Active Inference results

Provides plotting functions for:
- Spider phobia therapy simulation results
- T-maze benchmark results
- General belief evolution visualization
"""

using Plots

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

# Helper function
function mean(x::AbstractVector)
    return sum(x) / length(x)
end
