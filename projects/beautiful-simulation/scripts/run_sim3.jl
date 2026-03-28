using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

using BLTRxInfer

function main(args)
    config_path = nothing
    output_dir = joinpath(@__DIR__, "..", "results", "sim3")

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

    result = run_sim3(config_path = config_path, output_dir = output_dir)
    println("Simulation 3 summary")
    for model_name in ("KalmanFixed", "HGF2", "BLT-HGF")
        metrics = result.summary_by_model[model_name]
        println(string(
            model_name,
            " nll=", round(metrics.heldout_nll, digits = 4),
            " rmse=", round(metrics.rmse_x, digits = 4),
            " coverage=", round(metrics.coverage_90, digits = 4)
        ))
    end
    println("theory_result=", result.status.theory_result)
end

main(ARGS)
