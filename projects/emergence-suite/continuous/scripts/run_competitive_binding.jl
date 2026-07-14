using Pkg

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(project_dir, "src", "CompetitiveBinding.jl"))

using .CompetitiveBinding

output_dir = joinpath(project_dir, "results", "competitive_binding")
result = run_competitive_binding(output_dir)
println("Wrote experiment 34 to $output_dir")
println("Passed empirical criteria: ", all(values(result.summary.empirical_criteria)))
