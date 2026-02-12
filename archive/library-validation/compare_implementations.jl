#!/usr/bin/env julia
"""
    compare_implementations.jl - Compare Custom vs ActiveInference.jl vs RxInfer implementations

Runs all three implementations on the same spider phobia model and compares:
1. Belief evolution (d-vector updates)
2. Behavioral outcomes (approach vs avoid)
"""

using Pkg
Pkg.activate(@__DIR__)

using IFSActiveInference
using Random
using Plots

"""
    extract_p_safe_rxinfer(d_evolution, matrices)

Extract P(safe) from RxInfer's flattened state space d_evolution.
"""
function extract_p_safe_rxinfer(d_evolution, matrices)
    p_safe = Float64[]
    for d in d_evolution
        # Sum probability mass for states where danger=2 (safe)
        total_safe = 0.0
        total = sum(d)
        for s_flat in 1:length(d)
            s = unflatten_state(s_flat, matrices.Ns)
            if s[3] == 2  # danger factor = 2 (safe)
                total_safe += d[s_flat]
            end
        end
        push!(p_safe, total_safe / total)
    end
    return p_safe
end

function run_comparison(; n_trials::Int = 200, spider_dangerous::Bool = false)
    condition = spider_dangerous ? "dangerous" : "safe"

    println("=" ^ 70)
    println("Comparing implementations: $condition spider, $n_trials trials")
    println("=" ^ 70)

    # ========== Custom Implementation ==========
    println("\n[1/3] Running CUSTOM implementation...")
    Random.seed!(42)

    params = ModelParams(CABi=0.9, Psafe=0.1, N=n_trials, T=4)
    model = build_model(params=params)

    settings = SimulationSettings(
        alpha=4.0, beta=1.0, gamma=1.0, eta=1.0,
        modalities_to_learn=[3], factors_to_learn=[3],
        exposure_mode=true
    )

    custom_results = run_exposure_therapy(model;
        n_trials=n_trials,
        settings=settings,
        spider_dangerous=spider_dangerous
    )

    # Extract P(safe) evolution for custom
    custom_p_safe = [d[3][2]/sum(d[3]) for d in custom_results.d_evolution]

    println("  Custom: P(safe) $(round(custom_p_safe[1]*100, digits=2))% → $(round(custom_p_safe[end]*100, digits=2))%")
    println("  Custom: Approach=$(custom_results.approach_count), Avoid=$(custom_results.avoid_count)")

    # ========== ActiveInference.jl Implementation ==========
    aif_results = nothing
    aif_p_safe = nothing

    if ACTIVEINFERENCE_AVAILABLE
        println("\n[2/3] Running ACTIVEINFERENCE.JL implementation...")
        Random.seed!(42)

        try
            # Use low_concentration=true to demonstrate learning dynamics
            aif_results = run_aif_exposure_therapy(
                n_trials=n_trials,
                spider_dangerous=spider_dangerous,
                params=params,
                low_concentration=true
            )

            # Extract P(safe) evolution
            aif_p_safe = [d[3][2]/sum(d[3]) for d in aif_results.d_evolution]

            println("  AIF: P(safe) $(round(aif_p_safe[1]*100, digits=2))% → $(round(aif_p_safe[end]*100, digits=2))%")
            println("  AIF: Approach=$(aif_results.approach_count), Avoid=$(aif_results.avoid_count)")
        catch e
            @warn "ActiveInference.jl implementation failed: $e"
        end
    else
        println("\n[2/3] SKIPPING ActiveInference.jl (not installed)")
        println("  Install with: using Pkg; Pkg.add(url=\"https://github.com/ilabcode/ActiveInference.jl\")")
    end

    # ========== RxInfer.jl Implementation ==========
    rxinfer_results = nothing
    rxinfer_p_safe = nothing

    if RXINFER_AVAILABLE
        println("\n[3/3] Running RXINFER.JL implementation...")
        Random.seed!(42)

        try
            rxinfer_results = run_rxinfer_exposure_therapy(
                n_trials=n_trials,
                spider_dangerous=spider_dangerous,
                params=params,
                low_concentration=true
            )

            # Extract P(safe) evolution from flattened state space
            rxinfer_p_safe = extract_p_safe_rxinfer(rxinfer_results.d_evolution, rxinfer_results.matrices)

            println("  RxInfer: P(safe) $(round(rxinfer_p_safe[1]*100, digits=2))% → $(round(rxinfer_p_safe[end]*100, digits=2))%")
            println("  RxInfer: Approach=$(rxinfer_results.approach_count), Avoid=$(rxinfer_results.avoid_count)")
        catch e
            @warn "RxInfer.jl implementation failed: $e"
            println("  Error details: $(sprint(showerror, e))")
        end
    else
        println("\n[3/3] SKIPPING RxInfer.jl (not installed)")
        println("  Install with: using Pkg; Pkg.add(\"RxInfer\")")
    end

    # ========== Generate Comparison Plot ==========
    println("\nGenerating comparison plot...")

    p = plot(1:n_trials, custom_p_safe,
        label="Custom Implementation",
        xlabel="Trial",
        ylabel="P(safe)",
        title="Belief Evolution Comparison ($condition spider)",
        linewidth=2,
        color=:blue,
        legend=:right
    )

    if aif_p_safe !== nothing
        plot!(p, 1:n_trials, aif_p_safe,
            label="ActiveInference.jl",
            linewidth=2,
            color=:red,
            linestyle=:dash
        )
    end

    if rxinfer_p_safe !== nothing
        plot!(p, 1:n_trials, rxinfer_p_safe,
            label="RxInfer.jl",
            linewidth=2,
            color=:green,
            linestyle=:dashdot
        )
    end

    hline!(p, [0.1], label="Initial prior (10%)", color=:gray, linestyle=:dot)

    output_file = "comparison_$(condition).png"
    savefig(p, output_file)
    println("Saved: $output_file")

    # ========== Summary ==========
    println("\n" * "=" ^ 70)
    println("SUMMARY: $condition spider")
    println("=" ^ 70)
    println("\n| Metric                | Custom      | ActiveInference.jl | RxInfer.jl      |")
    println("|----------------------|-------------|-------------------|-----------------|")
    println("| Initial P(safe)      | $(round(custom_p_safe[1]*100, digits=2))%       | $(aif_p_safe !== nothing ? "$(round(aif_p_safe[1]*100, digits=2))%" : "N/A")              | $(rxinfer_p_safe !== nothing ? "$(round(rxinfer_p_safe[1]*100, digits=2))%" : "N/A")             |")
    println("| Final P(safe)        | $(round(custom_p_safe[end]*100, digits=2))%       | $(aif_p_safe !== nothing ? "$(round(aif_p_safe[end]*100, digits=2))%" : "N/A")              | $(rxinfer_p_safe !== nothing ? "$(round(rxinfer_p_safe[end]*100, digits=2))%" : "N/A")             |")
    println("| Belief shift         | $(round((custom_p_safe[end]-custom_p_safe[1])*100, digits=2))%       | $(aif_p_safe !== nothing ? "$(round((aif_p_safe[end]-aif_p_safe[1])*100, digits=2))%" : "N/A")              | $(rxinfer_p_safe !== nothing ? "$(round((rxinfer_p_safe[end]-rxinfer_p_safe[1])*100, digits=2))%" : "N/A")             |")
    println("| Approach count       | $(custom_results.approach_count)         | $(aif_results !== nothing ? aif_results.approach_count : "N/A")                 | $(rxinfer_results !== nothing ? rxinfer_results.approach_count : "N/A")               |")

    return (
        custom=custom_results,
        aif=aif_results,
        rxinfer=rxinfer_results,
        custom_p_safe=custom_p_safe,
        aif_p_safe=aif_p_safe,
        rxinfer_p_safe=rxinfer_p_safe
    )
end

# Run comparisons for both conditions
if abspath(PROGRAM_FILE) == @__FILE__
    println("\n" * "=" ^ 70)
    println("SPIDER PHOBIA MODEL: THREE-WAY IMPLEMENTATION COMPARISON")
    println("=" ^ 70)

    # Safe spider (exposure therapy should work)
    safe_results = run_comparison(n_trials=200, spider_dangerous=false)

    println("\n\n")

    # Dangerous spider (should learn spider IS dangerous)
    dangerous_results = run_comparison(n_trials=200, spider_dangerous=true)

    println("\n\nComparison complete! Check comparison_safe.png and comparison_dangerous.png")
end
