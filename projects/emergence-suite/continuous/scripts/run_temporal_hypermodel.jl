using Pkg

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "BeautifulLoopHierarchy.jl"))
include(joinpath(project_dir, "src", "TemporalHyperModel.jl"))

using .TemporalHyperModel

output_dir = joinpath(project_dir, "results", "temporal_hypermodel")
result = run_temporal_hypermodel(output_dir)
println("Wrote experiment 30 to $output_dir")
println("Passed all criteria: $(all(values(result.summary.criteria)))")
