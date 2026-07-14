using Pkg

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(project_dir, "src", "UnifiedRelationalAgent.jl"))
include(joinpath(project_dir, "src", "MatchedMarginalRelationAblation.jl"))
include(joinpath(project_dir, "src", "ConfirmRelationalActionInteraction.jl"))

using .ConfirmRelationalActionInteraction

output_dir = joinpath(project_dir, "results", "confirm_relational_action_interaction")
summary = run_confirm_relational_action_interaction(output_dir)
println("Wrote experiment 42 to $output_dir")
println("All frozen empirical criteria passed: ",
    all(values(summary.empirical_criteria)))
