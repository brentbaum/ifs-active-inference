#!/usr/bin/env julia

using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

include(joinpath(@__DIR__, "..", "src", "ContinuousSim6a.jl"))
include(joinpath(@__DIR__, "..", "src", "T48Robustness.jl"))

using .T48Robustness

function main(args)
    config_path = joinpath(@__DIR__, "..", "configs", "t48-pilot.yaml")
    criteria_path = joinpath(@__DIR__, "..", "configs", "t48-criteria-pilot.yaml")
    output_dir = joinpath(@__DIR__, "..", "results", "t48_continuous_robustness_pilot")
    i = 1
    while i <= length(args)
        if args[i] == "--config"
            config_path = args[i + 1]
            i += 2
        elseif args[i] == "--criteria"
            criteria_path = args[i + 1]
            i += 2
        elseif args[i] == "--output"
            output_dir = args[i + 1]
            i += 2
        else
            error("Unknown argument: $(args[i])")
        end
    end
    T48Robustness.run_t48(config_path, criteria_path, output_dir)
end

main(ARGS)
