using Pkg

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(project_dir, "src", "UnifiedRelationalAgent.jl"))
include(joinpath(project_dir, "src", "ConfirmUnifiedRelationalAgent.jl"))

using .ConfirmUnifiedRelationalAgent

output_dir = joinpath(project_dir, "results", "confirm_unified_relational_agent")
summary = run_confirm_unified_relational_agent(output_dir)
println("Wrote experiment 40 to $output_dir")
println("All frozen empirical criteria passed: ",
    all(values(summary.empirical_criteria)))
