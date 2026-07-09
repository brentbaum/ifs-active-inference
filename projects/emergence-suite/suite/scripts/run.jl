#!/usr/bin/env julia

using EmergenceSuite

function main(args)
    length(args) == 1 || error("Usage: julia --project=projects/emergence-suite/suite projects/emergence-suite/suite/scripts/run.jl <config.yaml>")
    result = run_config(args[1])
    println("output_dir=", result.output_dir)
    println("theory_result=", result.status.theory_result)
    println("implementation_passed=", result.status.implementation_passed)
end

main(ARGS)
