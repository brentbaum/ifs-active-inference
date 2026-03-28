function sim3_posterior_content_precision(result)
    return mean(1.0 ./ max.(result.x_var, 1e-9))
end

function sim3_implied_local_precision(result, config::Sim3Config)
    if all(isnan, result.z_mean)
        return sim3_posterior_content_precision(result)
    end
    return mean(exp.(-(config.kappa .* result.z_mean .+ config.omega)))
end

function sim3_max_wrong_high_confidence_run(result, sequence)
    high_confidence = [
        abs(result.x_mean[t] - sequence.x[t]) > 1.96 * sqrt(max(result.x_var[t], 1e-9))
        for t in eachindex(sequence.x)
    ]
    best = 0
    current = 0
    for flag in high_confidence
        if flag
            current += 1
            best = max(best, current)
        else
            current = 0
        end
    end
    return best
end

function sim3_metrics(model_name::String, result, sequence, config::Sim3Config)
    coverage = coverage_90(result.x_mean, result.x_var, sequence.x)
    pred_var = Float64.(result.x_var) .+ sequence.params.v_y
    nll = mean([
        -logpdf(Normal(result.x_mean[t], sqrt(max(pred_var[t], 1e-9))), sequence.y[t])
        for t in eachindex(sequence.y)
    ])
    posterior_content_precision = sim3_posterior_content_precision(result)
    implied_local_precision = sim3_implied_local_precision(result, config)
    return (
        model = model_name,
        heldout_nll = nll,
        rmse_x = rmse(result.x_mean, sequence.x),
        coverage_90 = coverage,
        first_order_precision = implied_local_precision,
        implied_local_precision = implied_local_precision,
        posterior_content_precision = posterior_content_precision,
        hyper_certainty = all(isnan, result.h_var) ? NaN : mean(1.0 ./ max.(result.h_var, 1e-9)),
        content_complexity = var(result.x_mean),
        overconfidence_90 = max(0.0, 0.90 - coverage),
        wrong_high_confidence_run_length = sim3_max_wrong_high_confidence_run(result, sequence),
        free_energy_initial = first(result.free_energy),
        free_energy_final = last(result.free_energy)
    )
end

function summarize_sim3_rows(rows)
    return (
        heldout_nll = safe_mean([row.heldout_nll for row in rows]),
        rmse_x = safe_mean([row.rmse_x for row in rows]),
        coverage_90 = safe_mean([row.coverage_90 for row in rows]),
        first_order_precision = safe_mean([row.first_order_precision for row in rows]),
        implied_local_precision = safe_mean([row.implied_local_precision for row in rows]),
        posterior_content_precision = safe_mean([row.posterior_content_precision for row in rows]),
        hyper_certainty = safe_mean(filter(!isnan, [row.hyper_certainty for row in rows])),
        content_complexity = safe_mean([row.content_complexity for row in rows]),
        overconfidence_90 = safe_mean([row.overconfidence_90 for row in rows]),
        wrong_high_confidence_run_length = safe_mean([row.wrong_high_confidence_run_length for row in rows])
    )
end

function evaluate_sim3_theory(sweep_rows, scenario_rows)
    blt_rows = filter(row -> row.model == "BLT-HGF" && row.phase == "sweep", sweep_rows)
    hgf_rows = filter(row -> row.model == "HGF2" && row.phase == "sweep", sweep_rows)
    kalman_rows = filter(row -> row.model == "KalmanFixed" && row.phase == "sweep", sweep_rows)

    blt_nll = mean([row.heldout_nll for row in blt_rows])
    hgf_nll = mean([row.heldout_nll for row in hgf_rows])
    kalman_nll = mean([row.heldout_nll for row in kalman_rows])

    fop = [row.implied_local_precision for row in blt_rows]
    cc = [row.content_complexity for row in blt_rows]
    hc = filter(!isnan, [row.hyper_certainty for row in blt_rows])
    fop_q = quantile(fop, [0.25, 0.75])
    cc_q = quantile(cc, [0.25, 0.75])
    hc_q = quantile(hc, [0.25, 0.75])

    mpe_row = only(filter(row -> row.scenario == "mpe" && row.model == "BLT-HGF", scenario_rows))
    dream_row = only(filter(row -> row.scenario == "dream" && row.model == "BLT-HGF", scenario_rows))
    wake_row = only(filter(row -> row.scenario == "wake" && row.model == "BLT-HGF", scenario_rows))
    noetic_row = only(filter(row -> row.scenario == "noetic" && row.model == "BLT-HGF", scenario_rows))

    mpe_exists = mpe_row.implied_local_precision <= fop_q[1] &&
        mpe_row.content_complexity <= 1.05 * wake_row.content_complexity &&
        mpe_row.hyper_certainty >= hc_q[2]

    dream_exists = dream_row.hyper_certainty < mpe_row.hyper_certainty &&
        dream_row.content_complexity > mpe_row.content_complexity

    noetic_exists = noetic_row.hyper_certainty >= hc_q[2] &&
        noetic_row.overconfidence_90 > 0.05

    min_support = blt_nll < hgf_nll && blt_nll < kalman_nll && mpe_exists
    strong_support = dream_exists && noetic_exists
    label = if min_support && strong_support
        "support"
    elseif min_support
        "weak_support"
    elseif blt_nll < hgf_nll || mpe_exists
        "null"
    else
        "falsified"
    end

    return (label = label, minimum_support = min_support, stronger_support = strong_support)
end

function sim3_plot_heatmap(output_dir::AbstractString, rows, metric::Symbol, filename::String, title::String, config::Sim3Config)
    blt_rows = filter(row -> row.model == "BLT-HGF" && row.phase == "sweep", rows)
    mat = zeros(Float64, length(config.alpha_hyper_values), length(config.alpha_local_values))
    for (j, ah) in enumerate(config.alpha_hyper_values), (i, al) in enumerate(config.alpha_local_values)
        vals = [getproperty(row, metric) for row in blt_rows if row.alpha_local == al && row.alpha_hyper == ah]
        mat[j, i] = safe_mean(vals)
    end
    plt = heatmap(config.alpha_local_values, config.alpha_hyper_values, mat, xlabel = "alpha_local", ylabel = "alpha_hyper", title = title)
    save_plot(joinpath(output_dir, filename), plt)
end

function sim3_plot_scenarios(output_dir::AbstractString, scenario_outputs)
    order = ["wake", "dream", "mpe", "noetic"]
    plots = Any[]
    for scenario in order
        out = scenario_outputs[scenario]
        p = plot(title = scenario, xlabel = "t", ylabel = "x")
        plot!(p, out.sequence.x, label = "true x", color = :black, lw = 2)
        plot!(p, out.result.x_mean, ribbon = sqrt.(max.(out.result.x_var, 1e-9)), label = "BLT estimate", color = :teal)
        push!(plots, p)
    end
    combo = plot(plots..., layout = (2, 2), size = (1000, 700))
    save_plot(joinpath(output_dir, "scenario_trajectories.png"), combo)

    xs = [scenario_outputs[s].metrics.implied_local_precision for s in order]
    ys = [scenario_outputs[s].metrics.hyper_certainty for s in order]
    plt = scatter(xs, ys, xlabel = "implied_local_precision", ylabel = "hyper_certainty", title = "Scenario Phase Space", legend = false)
    annotate!(plt, xs, ys, order)
    save_plot(joinpath(output_dir, "scenario_phase_scatter.png"), plt)
end

function run_sim3(; config_path::Union{Nothing, String} = nothing, output_dir::Union{Nothing, String} = nothing)
    started = time()
    config = isnothing(config_path) ? default_sim3_config() : load_sim3_config(config_path)
    rows = NamedTuple[]

    model_specs = [
        ("KalmanFixed", sim3_kalman_fixed_infer),
        ("HGF2", sim3_hgf2_infer),
        ("BLT-HGF", sim3_blt_hgf_infer)
    ]

    for alpha_local in config.alpha_local_values, alpha_hyper in config.alpha_hyper_values, seed in config.seeds
        seq = generate_sim3_sequence(default_rng(seed), config; alpha_local, alpha_hyper, input_scale = 1.0, biased_priors = false)
        for (model_name, infer_fn) in model_specs
            result = infer_fn(seq, config)
            metrics = sim3_metrics(model_name, result, seq, config)
            push!(rows, merge(metrics, (
                phase = "sweep",
                scenario = "none",
                seed = seed,
                alpha_local = alpha_local,
                alpha_hyper = alpha_hyper,
                input_scale = 1.0,
                biased_priors = false
            )))
        end
    end

    scenario_defs = Dict(
        "mpe" => (alpha_local = 0.8, alpha_hyper = 4.0, input_scale = 0.0, biased = false),
        "dream" => (alpha_local = 0.5, alpha_hyper = 0.5, input_scale = 2.0, biased = false),
        "wake" => (alpha_local = 2.0, alpha_hyper = 2.0, input_scale = 1.0, biased = false),
        "noetic" => (alpha_local = 0.5, alpha_hyper = 4.0, input_scale = 0.25, biased = true)
    )

    metric_definitions = (
        phase_metric = "implied_local_precision",
        implied_local_precision = "mean(exp(-(kappa * z_t + omega))) from inferred z_t; used for the phase diagram and theory evaluation",
        posterior_content_precision = "mean(1 / var_q(x_t)); retained as a comparator and explicit deviation from the original var_q(x_t)-based draft reading",
        first_order_precision = "backward-compatible alias for implied_local_precision"
    )

    spec_deviations = (
        first_order_precision = "The phase metric is the inferred implied_local_precision from z_t rather than only posterior variance of x_t.",
        scenario_defaults = "Scenario defaults were tuned relative to the original spec and are recorded explicitly in scenario_definitions.",
        scale_y_by_local = "Observation noise coupling scale_y_by_local remains configurable and is currently $(config.scale_y_by_local)."
    )

    scenario_outputs = Dict{String, Any}()
    scenario_rows = NamedTuple[]
    scenario_seed = first(config.seeds)
    for (scenario_name, params) in scenario_defs
        seq = generate_sim3_sequence(default_rng(scenario_seed), config;
            alpha_local = params.alpha_local,
            alpha_hyper = params.alpha_hyper,
            input_scale = params.input_scale,
            biased_priors = params.biased
        )
        for (model_name, infer_fn) in model_specs
            result = infer_fn(seq, config)
            metrics = sim3_metrics(model_name, result, seq, config)
            row = merge(metrics, (
                phase = "scenario",
                scenario = scenario_name,
                seed = scenario_seed,
                alpha_local = params.alpha_local,
                alpha_hyper = params.alpha_hyper,
                input_scale = params.input_scale,
                biased_priors = params.biased
            ))
            push!(scenario_rows, row)
            if model_name == "BLT-HGF"
                scenario_outputs[scenario_name] = (sequence = seq, result = result, metrics = metrics)
            end
        end
    end

    theory = evaluate_sim3_theory(rows, scenario_rows)
    all_rows = vcat(rows, scenario_rows)
    summary_by_model = Dict{String, NamedTuple}()
    for model_name in ("KalmanFixed", "HGF2", "BLT-HGF")
        summary_by_model[model_name] = summarize_sim3_rows(filter(row -> row.model == model_name && row.phase == "sweep", rows))
    end

    implementation_passed = all(
        isfinite(row.heldout_nll) &&
        isfinite(row.rmse_x) &&
        isfinite(row.coverage_90) &&
        isfinite(row.implied_local_precision) &&
        isfinite(row.posterior_content_precision) &&
        isfinite(row.content_complexity) &&
        isfinite(row.overconfidence_90)
        for row in all_rows
    )
    summary = (
        simulation = "sim3",
        config = (
            seeds = config.seeds,
            T = config.T,
            alpha_local_values = config.alpha_local_values,
            alpha_hyper_values = config.alpha_hyper_values,
            scale_y_by_local = config.scale_y_by_local
        ),
        summary_by_model = summary_by_model,
        metric_definitions = metric_definitions,
        spec_deviations = spec_deviations,
        scenario_definitions = scenario_defs,
        theory_result = theory.label
    )
    status = (implementation_passed = implementation_passed, theory_result = theory.label)
    metadata = build_reproducibility_metadata(
        config;
        config_path = config_path,
        runtime_seconds = time() - started,
        repo_root = abspath(joinpath(@__DIR__, "..", "..", "..", "..")),
        extra = Dict(
            "metric_definitions" => metric_definitions,
            "spec_deviations" => spec_deviations,
            "scenario_definitions" => scenario_defs
        )
    )

    if !isnothing(output_dir)
        ensure_dir(output_dir)
        write_json(joinpath(output_dir, "summary.json"), summary)
        write_rows_csv(joinpath(output_dir, "per_seed_metrics.csv"), all_rows)
        trace_rows = NamedTuple[]
        for (scenario, out) in scenario_outputs
            for t in eachindex(out.sequence.y)
                push!(trace_rows, (
                    scenario = scenario,
                    t = t,
                    x_true = out.sequence.x[t],
                    y = out.sequence.y[t],
                    x_mean = out.result.x_mean[t],
                    x_var = out.result.x_var[t],
                    z_mean = out.result.z_mean[t],
                    h_mean = out.result.h_mean[t]
                ))
            end
        end
        write_rows_csv(joinpath(output_dir, "posterior_traces.csv"), trace_rows)
        write_json(joinpath(output_dir, "status.json"), status)
        write_json(joinpath(output_dir, "metadata.json"), metadata)
        sim3_plot_heatmap(output_dir, rows, :implied_local_precision, "heatmap_first_order_precision.png", "Implied local precision", config)
        sim3_plot_heatmap(output_dir, rows, :implied_local_precision, "heatmap_implied_local_precision.png", "Implied local precision", config)
        sim3_plot_heatmap(output_dir, rows, :posterior_content_precision, "heatmap_posterior_content_precision.png", "Posterior content precision", config)
        sim3_plot_heatmap(output_dir, rows, :hyper_certainty, "heatmap_hyper_certainty.png", "Hyper certainty", config)
        sim3_plot_heatmap(output_dir, rows, :content_complexity, "heatmap_content_complexity.png", "Content complexity", config)
        sim3_plot_heatmap(output_dir, rows, :overconfidence_90, "heatmap_overconfidence.png", "Overconfidence", config)
        sim3_plot_scenarios(output_dir, scenario_outputs)
    end

    return (
        config = config,
        per_seed_metrics = all_rows,
        summary_by_model = summary_by_model,
        summary = summary,
        status = status,
        metadata = metadata
    )
end
