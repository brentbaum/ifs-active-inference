using Pkg

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "UnifiedBeautifulLoop.jl"))

using .UnifiedBeautifulLoop

output_dir = joinpath(project_dir, "results", "unified_beautiful_loop")
result = run_unified_beautiful_loop(output_dir)
println("Wrote experiment 33 to $output_dir")
println("Implementation checks passed: ",
    all(values(result.summary.implementation_checks)) &&
    all(values(result.summary.optimization_checks)))
println("Empirical criteria passed: ",
    all(values(result.summary.empirical_criteria)))
