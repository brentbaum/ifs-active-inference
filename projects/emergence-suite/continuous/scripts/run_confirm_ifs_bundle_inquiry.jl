using Pkg

project_dir = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(project_dir)

include(joinpath(project_dir, "src", "GlobalPrecisionField.jl"))
include(joinpath(project_dir, "src", "UnifiedBeautifulLoop.jl"))
include(joinpath(project_dir, "src", "IFSBundleInquiry.jl"))
include(joinpath(project_dir, "src", "ConfirmIFSBundleInquiry.jl"))

using .IFSBundleInquiry
using .ConfirmIFSBundleInquiry

const FREEZE_COMMIT = "84c702a2bd7b83def669c999141674b9fcdccda7"

config = IFSBundleConfig(seeds = collect(17001:17020))
@assert config.seeds == collect(17001:17020)
@assert isempty(intersect(config.seeds, collect(16901:16910)))
@assert config.episodes == 96
@assert config.training_episodes == 32
@assert config.bundle_training_scenes == 256
@assert config.switch_episode == 65
@assert config.packet_samples == 2
@assert config.action_budget == 2
@assert config.local_fields == (0.15, 0.25, 0.06, 0.25)
@assert config.coupling_self_world == 0.80
@assert config.coupling_world_outcome == 1.50
@assert config.coupling_policy_outcome == 0.0
@assert config.conclusion_reliability == 0.68
@assert config.guide_noise_sd == 0.45

output_dir = joinpath(project_dir, "results", "confirm_ifs_bundle_inquiry")
@assert !isdir(output_dir) "confirmation output already exists; refusing a rerun"
summary = evaluate_ifs_bundle(output_dir; config = config,
    stage = "confirmation", freeze_commit = FREEZE_COMMIT,
    result_commit = "pending", write_full_traces = true)

println("Wrote the single frozen Experiment 43 confirmation to $output_dir")
println("Statuses: ", summary.statuses)
