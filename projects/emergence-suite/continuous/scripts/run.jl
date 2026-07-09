#!/usr/bin/env julia

using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

include(joinpath(@__DIR__, "..", "src", "ContinuousSim6a.jl"))

using .ContinuousSim6a

function main(args)
    config_path = joinpath(@__DIR__, "..", "configs", "default.yaml")
    criteria_path = joinpath(@__DIR__, "..", "configs", "criteria.yaml")
    output_dir = joinpath(@__DIR__, "..", "results", "sim6a_continuous_stage3")

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

    ContinuousSim6a.run_all(config_path, criteria_path, output_dir)
end

main(ARGS)
