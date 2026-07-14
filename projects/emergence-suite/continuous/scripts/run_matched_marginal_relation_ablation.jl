using Pkg

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(project_dir, "src", "UnifiedRelationalAgent.jl"))
include(joinpath(project_dir, "src", "MatchedMarginalRelationAblation.jl"))

using .MatchedMarginalRelationAblation

output_dir = joinpath(project_dir, "results", "matched_marginal_relation_ablation")
summary = run_matched_marginal_relation_ablation(output_dir)
println("Wrote experiment 41 diagnostic to $output_dir")
println("All diagnostic criteria passed: ",
    all(values(summary.empirical_criteria)))
