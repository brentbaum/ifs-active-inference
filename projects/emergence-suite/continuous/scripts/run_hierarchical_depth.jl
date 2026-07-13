using Pkg

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "HierarchicalEpistemicDepth.jl"))

using .HierarchicalEpistemicDepth

output_dir = joinpath(project_dir, "results", "hierarchical_epistemic_depth")
run_formal_fidelity(output_dir)
println("Wrote hierarchical epistemic-depth results to $output_dir")
