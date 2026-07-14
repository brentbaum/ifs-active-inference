using Pkg

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(project_dir, "src", "CompetitiveBinding.jl"))
include(joinpath(project_dir, "src", "LearnedPrecisionStructure.jl"))
include(joinpath(project_dir, "src", "IdentifiablePrecisionStructure.jl"))
include(joinpath(project_dir, "src", "IdentifiableGlobality.jl"))

using .IdentifiableGlobality

output_dir = joinpath(project_dir, "results", "identifiable_globality")
summary = run_identifiable_globality(output_dir)
println("Wrote experiment 38 to $output_dir")
println(summary)
