using Pkg

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "BeautifulLoopHierarchy.jl"))

using .BeautifulLoopHierarchy

output_dir = joinpath(project_dir, "results", "beautiful_loop_hierarchy")
result = run_beautiful_loop_fidelity(output_dir)
println("Wrote higher-fidelity Beautiful Loop results to $output_dir")
println("Passed all criteria: $(all(values(result.summary.criteria)))")
