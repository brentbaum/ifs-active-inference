using Pkg

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(project_dir, "src", "CompetitiveBinding.jl"))
include(joinpath(project_dir, "src", "LearnedPrecisionStructure.jl"))
include(joinpath(project_dir, "src", "ConfirmatoryBeautifulLoop.jl"))

using .ConfirmatoryBeautifulLoop

output_dir = joinpath(project_dir, "results", "confirmatory_beautiful_loop")
summary = run_confirmatory_beautiful_loop(output_dir)
println("Wrote experiment 36 to $output_dir")
println("Passed all empirical criteria: ", all(values(summary.empirical_criteria)))
