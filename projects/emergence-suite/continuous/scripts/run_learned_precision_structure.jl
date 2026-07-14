using Pkg

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(project_dir, "src", "CompetitiveBinding.jl"))
include(joinpath(project_dir, "src", "LearnedPrecisionStructure.jl"))

using .LearnedPrecisionStructure

output_dir = joinpath(project_dir, "results", "learned_precision_structure")
result = run_learned_precision_structure(output_dir)
println("Wrote experiment 35 to $output_dir")
println("Passed empirical criteria: ", all(values(result.summary.empirical_criteria)))
