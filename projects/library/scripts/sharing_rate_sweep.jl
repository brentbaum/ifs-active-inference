"""
Short sweep of sharing rates for paper profiles.

Usage:
  julia --project=. scripts/sharing_rate_sweep.jl
"""

using Pkg
Pkg.activate(".")

include("../src/active_inference/ActiveInferenceCore.jl")
using .ActiveInferenceCore
using Statistics
using Random

# Config
n_trials = 40
n_runs = 10
partners = [:friendly, :hostile]
profiles = all_paper_profiles()

println("Sharing-rate sweep (n_trials=$(n_trials), n_runs=$(n_runs))")
println("deterministic_actions=true, gamma=profile.gamma, env p_share=(0.8,0.2,0.5)")
println("")

Random.seed!(42)

for profile in profiles
    println("Profile: ", profile.name)
    for partner in partners
        rates = Float64[]
        for _ in 1:n_runs
            res = run_trust_game_simulation(
                profile=profile,
                partner_type=partner,
                n_trials=n_trials,
                deterministic_actions=true
            )
            push!(rates, res.sharing_rate)
        end
        println("  ", rpad(String(partner), 8),
                " mean=", round(mean(rates), digits=3),
                " std=", round(std(rates), digits=3),
                " min=", round(minimum(rates), digits=3),
                " max=", round(maximum(rates), digits=3))
    end
    println("")
end
