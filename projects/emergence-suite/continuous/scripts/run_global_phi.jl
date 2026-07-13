#!/usr/bin/env julia

using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

include(joinpath(@__DIR__, "..", "src", "GlobalPrecisionField.jl"))
using .GlobalPrecisionField

output_dir = isempty(ARGS) ?
    joinpath(@__DIR__, "..", "results", "global_precision_field") :
    abspath(first(ARGS))

result = GlobalPrecisionField.run_all(output_dir)
println("Wrote v11 global precision-field results to $(result.output_dir)")
