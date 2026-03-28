using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

using BLTRxInfer

function main(args)
    config_path = nothing
    output_dir = joinpath(@__DIR__, "..", "results", "sim2")

    i = 1
    while i <= length(args)
        if args[i] == "--config"
            config_path = args[i + 1]
            i += 2
        elseif args[i] == "--output"
            output_dir = args[i + 1]
            i += 2
        else
            error("Unknown argument: $(args[i])")
        end
    end

    result = run_sim2(config_path = config_path, output_dir = output_dir)
    println("Simulation 2 summary")
    for model_name in ("HierFixed", "LocalBranch", "BLTGlobal")
        metrics = result.filtered_summary_by_model[model_name]
        println(string(
            model_name,
            " coherence=", round(metrics.coherence, digits = 4),
            " dwell=", round(metrics.mean_dwell, digits = 4),
            " micro_switch=", round(metrics.micro_switch_rate, digits = 4),
            " scene_accuracy=", round(metrics.scene_accuracy, digits = 4)
        ))
    end
    println("theory_result=", result.status.theory_result)
    println("smoothed_theory_result=", result.status.smoothed_theory_result)
end

main(ARGS)
