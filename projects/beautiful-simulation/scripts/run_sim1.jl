using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

using BLTRxInfer

function main(args)
    config_path = nothing
    output_dir = joinpath(@__DIR__, "..", "results", "sim1")

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

    result = run_sim1(config_path = config_path, output_dir = output_dir)

    println("Simulation 1 summary")
    for model_name in ("FlatFixed", "LocalPrecision", "BLTGlobal")
        metrics = result.filtered_summary_by_model[model_name]
        println(
            string(
                model_name,
                " accuracy=", round(metrics.world_accuracy, digits = 4),
                " nll=", round(metrics.heldout_nll, digits = 4),
                " brier=", round(metrics.future_reliability_brier, digits = 4),
                " ece=", round(metrics.ece, digits = 4)
            )
        )
    end
    println("theory_result=", result.status.theory_result)
    println("smoothed_theory_result=", result.status.smoothed_theory_result)
end

main(ARGS)
