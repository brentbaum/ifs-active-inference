using Pkg
using Dates

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(project_dir, "src", "IFSBundleInquiry.jl"))
include(joinpath(project_dir, "src", "ConfirmIFSBundleInquiry.jl"))

using .IFSBundleInquiry
using .ConfirmIFSBundleInquiry

config = IFSBundleConfig(seeds = collect(16901:16910))
@assert config.seeds == collect(16901:16910)
@assert isempty(intersect(config.seeds, collect(17001:17020)))

output_dir = joinpath(project_dir, "results", "ifs_bundle_inquiry_pilot")
summary = evaluate_ifs_bundle(output_dir; config = config, stage = "pilot")

open(joinpath(output_dir, "attempt-ledger.md"), "a") do io
    println(io, "## $(Dates.format(now(), dateformat\"yyyy-mm-dd HH:MM:SS\"))")
    println(io)
    println(io, "- Seeds: `16901:16910`")
    println(io, "- Configuration: repository defaults in `IFSBundleConfig`")
    println(io, "- Stage 43A pilot status: `$(summary.statuses.stage_43A)`")
    println(io, "- Stage 43B pilot status: `$(summary.statuses.stage_43B)`")
    println(io, "- Stress pilot status: `$(summary.statuses.stress)`")
    println(io, "- No confirmation seeds opened.")
    println(io)
end

println("Wrote Experiment 43 pilot to $output_dir")
println("Statuses: ", summary.statuses)
