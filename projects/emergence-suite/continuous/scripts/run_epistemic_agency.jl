using Pkg

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "EpistemicAgency.jl"))

using .EpistemicAgency

output_dir = joinpath(project_dir, "results", "epistemic_agency")
result = run_epistemic_agency(output_dir)
println("Wrote experiment 32 to $output_dir")
println("Passed all criteria: $(all(values(result.summary.criteria)))")
