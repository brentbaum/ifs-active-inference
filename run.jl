#!/usr/bin/env julia
"""
    run.jl - Run the IFS Active Inference Exposure Therapy Simulation

This script demonstrates the full workflow:
1. Build the generative model (spider phobia scenario)
2. Run exposure therapy simulation
3. Visualize belief evolution

Usage:
    julia --project=. run.jl [--trials N] [--exposure] [--dangerous]
"""

using Pkg
Pkg.activate(@__DIR__)

# Check if we need to instantiate
try
    using IFSActiveInference
catch
    @info "Installing dependencies..."
    Pkg.instantiate()
    using IFSActiveInference
end

using Random

function main()
    println("=" ^ 60)
    println("IFS Active Inference - Spider Phobia Exposure Therapy")
    println("=" ^ 60)

    # Parse command line args
    n_trials = 200
    exposure_mode = false
    spider_dangerous = false

    for arg in ARGS
        if startswith(arg, "--trials=")
            n_trials = parse(Int, split(arg, "=")[2])
        elseif arg == "--exposure"
            exposure_mode = true
        elseif arg == "--dangerous"
            spider_dangerous = true
        end
    end

    # Determine output directory based on condition
    condition = spider_dangerous ? "dangerous" : "safe"
    output_dir = "results_$(condition)"

    println("\nConfiguration:")
    println("  Trials: $n_trials")
    println("  Exposure mode: $exposure_mode")
    println("  Spider actually: $(spider_dangerous ? "DANGEROUS" : "SAFE")")
    println("  Output: $output_dir/")

    # Set random seed for reproducibility
    Random.seed!(42)

    # Build the model
    println("\n[1/3] Building generative model...")
    params = ModelParams(
        CABi = 0.9,      # High cognitive-affective belief interaction
        Psafe = 0.1,     # Low prior that spider is safe
        N = n_trials,
        T = 4
    )
    model = build_model(params=params)

    println("  State factors: $(model.Ns)")
    println("  Observation modalities: $(model.No)")
    println("  Policies: $(size(model.V, 2))")

    # Run simulation
    println("\n[2/3] Running exposure therapy simulation...")
    settings = SimulationSettings(
        alpha = 4.0,            # Action precision (matches paper)
        beta = 1.0,
        gamma = 1.0,
        eta = 1.0,              # Full learning rate
        modalities_to_learn = [3],  # Learn affective consequences
        factors_to_learn = [3],     # Learn about safety
        exposure_mode = exposure_mode
    )

    results = run_exposure_therapy(model;
        n_trials = n_trials,
        settings = settings,
        spider_dangerous = spider_dangerous
    )

    # Results summary
    println("\n[3/3] Results Summary")
    println("-" ^ 40)
    println("Ground truth: Spider is $(spider_dangerous ? "DANGEROUS" : "SAFE")")
    println("\nBehavioral outcomes:")
    println("  Approach: $(results.approach_count) ($(round(100 * results.approach_count / n_trials, digits=1))%)")
    println("  Avoid: $(results.avoid_count) ($(round(100 * results.avoid_count / n_trials, digits=1))%)")

    # Final beliefs
    d3_final = results.agent.d[3]
    p_safe = softmax_tau(d3_final; tau=0.1)[2]
    p_dangerous = softmax_tau(d3_final; tau=0.1)[1]

    println("\nFinal beliefs about spider:")
    println("  P(safe): $(round(p_safe, digits=4))")
    println("  P(dangerous): $(round(p_dangerous, digits=4))")

    # Initial vs final comparison
    d3_initial = results.d_evolution[1][3]
    p_safe_initial = softmax_tau(d3_initial; tau=0.1)[2]

    println("\nBelief change:")
    println("  P(safe) initial: $(round(p_safe_initial, digits=4))")
    println("  P(safe) final: $(round(p_safe, digits=4))")
    println("  Change: $(round(p_safe - p_safe_initial, digits=4))")

    # Check if learning matched reality
    learned_correctly = (spider_dangerous && p_dangerous > 0.5) || (!spider_dangerous && p_safe > 0.5)
    println("\nLearning outcome: $(learned_correctly ? "CORRECT" : "INCORRECT") - Agent $(learned_correctly ? "learned" : "failed to learn") the true danger status")

    # Try to generate plots
    println("\nGenerating visualizations...")
    try
        generate_report(results; output_dir=output_dir)
        println("Results saved to $output_dir/")
    catch e
        @warn "Could not generate plots: $e"
        println("Install Plots.jl for visualizations: Pkg.add(\"Plots\")")
    end

    println("\n" * "=" ^ 60)
    println("Simulation complete!")
    println("=" ^ 60)

    return results
end

# Run if executed directly
if abspath(PROGRAM_FILE) == @__FILE__
    results = main()
end
