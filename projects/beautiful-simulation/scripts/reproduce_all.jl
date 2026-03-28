using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

using BLTRxInfer

function require_config(path::AbstractString)
    isfile(path) || error("Missing config file: $path")
    return path
end

base = joinpath(@__DIR__, "..", "results")
sim1_config = require_config(joinpath(@__DIR__, "..", "configs", "sim1_default.yaml"))
sim2_config = require_config(joinpath(@__DIR__, "..", "configs", "sim2_default.yaml"))
sim3_config = require_config(joinpath(@__DIR__, "..", "configs", "sim3_default.yaml"))

run_sim1(config_path = sim1_config, output_dir = joinpath(base, "sim1_default"))
run_sim2(config_path = sim2_config, output_dir = joinpath(base, "sim2_default"))
run_sim3(config_path = sim3_config, output_dir = joinpath(base, "sim3_default"))

println("Reproduction complete.")
