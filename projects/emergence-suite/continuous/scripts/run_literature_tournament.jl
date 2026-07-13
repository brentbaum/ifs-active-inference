using Pkg
project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)
include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "LiteratureTournament.jl"))
using .LiteratureTournament
result = run_tournament(joinpath(project_dir, "results", "literature_tournament"))
println("Best single: $(result.best_single.name)")
println("Combination earned: $(result.combination_earned)")
