using Pkg

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(project_dir, "src", "CompetitiveBinding.jl"))
include(joinpath(project_dir, "src", "LearnedPrecisionStructure.jl"))
include(joinpath(project_dir, "src", "IdentifiablePrecisionStructure.jl"))

using .IdentifiablePrecisionStructure

output_dir = joinpath(project_dir, "results", "identifiable_precision_structure")
summary = run_identifiable_precision_structure(output_dir)
println("Wrote experiment 37 to $output_dir")
println(summary)
