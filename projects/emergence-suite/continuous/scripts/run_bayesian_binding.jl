using Pkg

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "BayesianBinding.jl"))

using .BayesianBinding

output_dir = joinpath(project_dir, "results", "bayesian_binding")
result = run_bayesian_binding(output_dir)
println("Wrote experiment 31 to $output_dir")
println("Passed all criteria: $(all(values(result.summary.criteria)))")
