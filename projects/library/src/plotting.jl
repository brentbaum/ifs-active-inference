"""
    plotting.jl - Visualization utilities for IFS Active Inference

Generates plots for belief evolution and behavioral outcomes.
"""

using Plots

"""
    plot_belief_evolution(results; save_path=nothing)

Plot the evolution of safety beliefs (d[3]) over trials.
Reproduces the key figure from the exposure therapy simulation.
"""
function plot_belief_evolution(results; save_path::Union{String,Nothing} = nothing)
    d_evo = results.d_evolution
    n_trials = length(d_evo)

    # Extract P(safe) over trials using raw normalization
    # Shows actual belief dynamics (temperature-scaled version compresses the range too much)
    p_safe = [d[3][2] / sum(d[3]) for d in d_evo]
    p_dangerous = [d[3][1] / sum(d[3]) for d in d_evo]

    p1 = plot(1:n_trials, p_safe,
        label="P(safe | experience)",
        xlabel="Trial",
        ylabel="Probability",
        title="Evolution of Safety Beliefs During Exposure",
        linewidth=2,
        legend=:bottomright
    )
    plot!(p1, 1:n_trials, p_dangerous,
        label="P(dangerous | experience)",
        linewidth=2,
        linestyle=:dash
    )

    if save_path !== nothing
        savefig(p1, save_path)
        @info "Saved belief evolution plot to $save_path"
    end

    return p1
end

"""
    plot_affective_learning(results; save_path=nothing)

Plot the evolution of affective consequence beliefs (a[3]).
Shows how the agent learns that approaching the spider is safe.
"""
function plot_affective_learning(results; save_path::Union{String,Nothing} = nothing)
    a_evo = results.a_evolution
    n_trials = length(a_evo)

    # Extract beliefs about consequences at interact state (state 4)
    # when spider present (factor 2 = 2) and dangerous (factor 3 = 1)
    # vs safe (factor 3 = 2)

    # Normalize to probabilities
    function get_harm_prob(a_matrix, spider_idx, danger_idx)
        slice = a_matrix[:, 4, spider_idx, danger_idx]  # interact state
        probs = slice ./ sum(slice)
        return probs[3]  # P(harm)
    end

    p_harm_dangerous = [get_harm_prob(a, 2, 1) for a in a_evo]
    p_harm_safe = [get_harm_prob(a, 2, 2) for a in a_evo]

    p1 = plot(1:n_trials, p_harm_dangerous,
        label="P(harm | interact, spider, dangerous)",
        xlabel="Trial",
        ylabel="Probability of Harm",
        title="Learning About Affective Consequences",
        linewidth=2,
        legend=:topright
    )
    plot!(p1, 1:n_trials, p_harm_safe,
        label="P(harm | interact, spider, safe)",
        linewidth=2,
        linestyle=:dash
    )

    if save_path !== nothing
        savefig(p1, save_path)
        @info "Saved affective learning plot to $save_path"
    end

    return p1
end

"""
    plot_behavioral_summary(results; save_path=nothing)

Bar chart showing approach vs avoid behavior.
"""
function plot_behavioral_summary(results; save_path::Union{String,Nothing} = nothing)
    p1 = bar(["Approach", "Avoid"],
        [results.approach_count, results.avoid_count],
        title="Behavioral Outcomes",
        ylabel="Number of Trials",
        legend=false,
        color=[:green, :red]
    )

    if save_path !== nothing
        savefig(p1, save_path)
        @info "Saved behavioral summary to $save_path"
    end

    return p1
end

"""
    generate_report(results; output_dir="results")

Generate all plots and a summary report.
"""
function generate_report(results; output_dir::String = "results")
    mkpath(output_dir)

    # Generate plots
    plot_belief_evolution(results; save_path=joinpath(output_dir, "belief_evolution.png"))
    plot_affective_learning(results; save_path=joinpath(output_dir, "affective_learning.png"))
    plot_behavioral_summary(results; save_path=joinpath(output_dir, "behavioral_summary.png"))

    # Write summary
    summary = """
    IFS Active Inference Simulation Results
    =======================================

    Trials: $(results.n_trials)
    Approach choices: $(results.approach_count) ($(round(100 * results.approach_count / results.n_trials, digits=1))%)
    Avoid choices: $(results.avoid_count) ($(round(100 * results.avoid_count / results.n_trials, digits=1))%)

    Final beliefs:
    - P(spider is safe): $(round(softmax_tau(results.agent.d[3]; tau=0.1)[2], digits=3))
    - P(spider is dangerous): $(round(softmax_tau(results.agent.d[3]; tau=0.1)[1], digits=3))

    Files generated:
    - belief_evolution.png
    - affective_learning.png
    - behavioral_summary.png
    """

    open(joinpath(output_dir, "summary.txt"), "w") do f
        write(f, summary)
    end

    println(summary)
    return summary
end
