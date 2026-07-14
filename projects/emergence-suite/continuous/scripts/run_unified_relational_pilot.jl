using Pkg

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(project_dir, "src", "UnifiedRelationalAgent.jl"))

using .UnifiedRelationalAgent

output_dir = joinpath(project_dir, "results", "unified_relational_pilot")
summary = run_unified_relational_pilot(output_dir)
println("Wrote experiment 39 pilot to $output_dir")
println("Empirical criteria passed: ", all(values(summary.empirical_criteria)))
