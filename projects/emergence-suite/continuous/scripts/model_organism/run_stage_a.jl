#!/usr/bin/env julia

include(joinpath(@__DIR__, "..", "..", "src", "ModelOrganism.jl"))
using .ModelOrganism

function usage()
    error("""
    usage:
      run_stage_a.jl --prepare
      run_stage_a.jl --phase0
      run_stage_a.jl --pilot <1-10|all>
      run_stage_a.jl --audit
      run_stage_a.jl --report
      run_stage_a.jl --freeze
      run_stage_a.jl --stage-a

    No confirmatory mode exists. Seeds at or above 700000 are refused by the
    canonical pilot runner.
    """)
end

function prepare()
    genome = load_genome()
    ModelOrganism.write_precalibration_lock!(genome)
    println("precalibration lock and identity written")
end

function pilot(argument)
    genome = load_genome()
    if argument == "all"
        for assay in 1:10
            run_pilot(assay; genome = genome)
            println("assay $assay pilot complete")
        end
    else
        assay = tryparse(Int, argument)
        assay === nothing && usage()
        run_pilot(assay; genome = genome)
        println("assay $assay pilot complete")
    end
end

function stage_a()
    genome = load_genome()
    ModelOrganism.write_precalibration_lock!(genome)
    run_phase0(; genome = genome)
    for assay in 1:10
        run_pilot(assay; genome = genome)
    end
    run_audits(genome)
    write_stage_a_report(; genome = genome)
    write_freeze_manifest(; genome = genome)
    println("Stage A complete; stopped before confirmatory execution")
end

isempty(ARGS) && usage()
if ARGS == ["--prepare"]
    prepare()
elseif ARGS == ["--phase0"]
    run_phase0()
    println("Phase 0 complete")
elseif length(ARGS) == 2 && ARGS[1] == "--pilot"
    pilot(ARGS[2])
elseif ARGS == ["--audit"]
    run_audits()
    println("assay 0 audits complete")
elseif ARGS == ["--report"]
    write_stage_a_report()
    println("Stage A report written")
elseif ARGS == ["--freeze"]
    write_freeze_manifest()
    println("freeze candidate manifest written; evaluator commit pending")
elseif ARGS == ["--stage-a"]
    stage_a()
else
    usage()
end
