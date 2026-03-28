function sim1_mode_fields(posterior_mode::Symbol)
    if posterior_mode == :filtered
        return (
            world = :filtered_world_posteriors,
            phi = :filtered_phi_posteriors,
            future_v = :filtered_future_v,
            future_a = :filtered_future_a
        )
    elseif posterior_mode == :smoothed
        return (
            world = :smoothed_world_posteriors,
            phi = :smoothed_phi_posteriors,
            future_v = :smoothed_future_v,
            future_a = :smoothed_future_a
        )
    else
        error("Unknown posterior mode: $posterior_mode")
    end
end

function sim1_episode_metrics(
    model_name::String,
    inference,
    episode,
    config::Sim1Config;
    is_probe::Bool = false,
    posterior_mode::Symbol = :filtered
)
    fields = sim1_mode_fields(posterior_mode)
    world_posteriors = getproperty(inference, fields.world)
    phi_posteriors = getproperty(inference, fields.phi)
    future_v = getproperty(inference, fields.future_v)
    future_a = getproperty(inference, fields.future_a)

    truth = episode.s
    accuracy = state_accuracy(world_posteriors, truth)

    confidences = [maximum(view(world_posteriors, t, :)) for t in 1:size(world_posteriors, 1)]
    correctness = [argmax(view(world_posteriors, t, :)) == truth[t] for t in eachindex(truth)]
    ece = expected_calibration_error(confidences, correctness)
    nll = negative_log_likelihood(inference.log_evidence, length(truth))

    future_outcome_v = Float64[(episode.ov[t + 1] == episode.s[t + 1]) for t in 1:(length(truth) - 1)]
    future_outcome_a = Float64[(episode.oa[t + 1] == episode.s[t + 1]) for t in 1:(length(truth) - 1)]
    future_brier = mean([
        brier_score(Float64.(future_v), future_outcome_v),
        brier_score(Float64.(future_a), future_outcome_a)
    ])

    context_accuracy = NaN
    if !isnothing(phi_posteriors)
        start_t = min(config.burn_in + 1, size(phi_posteriors, 1))
        context_accuracy = state_accuracy(phi_posteriors[start_t:end, :], episode.phi[start_t:end])
    end

    switch_accuracy = NaN
    if is_probe
        windows = Int[]
        for start in (61, 121, 181)
            append!(windows, start:min(start + config.switch_window - 1, length(truth)))
        end
        switch_accuracy = mean([
            argmax(view(world_posteriors, t, :)) == truth[t] for t in windows
        ])
    end

    return (
        posterior_mode = String(posterior_mode),
        model = model_name,
        world_accuracy = accuracy,
        heldout_nll = nll,
        ece = ece,
        future_reliability_brier = future_brier,
        context_recovery_accuracy = context_accuracy,
        switch_recovery_accuracy = switch_accuracy
    )
end

function summarize_model_rows(rows)
    return (
        world_accuracy = safe_mean([row.world_accuracy for row in rows]),
        heldout_nll = safe_mean([row.heldout_nll for row in rows]),
        ece = safe_mean([row.ece for row in rows]),
        future_reliability_brier = safe_mean([row.future_reliability_brier for row in rows]),
        context_recovery_accuracy = safe_mean(filter(!isnan, [row.context_recovery_accuracy for row in rows])),
        switch_recovery_accuracy = safe_mean(filter(!isnan, [row.switch_recovery_accuracy for row in rows]))
    )
end

function delta_namedtuple(filtered_summary, smoothed_summary)
    return (
        world_accuracy = filtered_summary.world_accuracy - smoothed_summary.world_accuracy,
        heldout_nll = filtered_summary.heldout_nll - smoothed_summary.heldout_nll,
        ece = filtered_summary.ece - smoothed_summary.ece,
        future_reliability_brier = filtered_summary.future_reliability_brier - smoothed_summary.future_reliability_brier,
        context_recovery_accuracy = filtered_summary.context_recovery_accuracy - smoothed_summary.context_recovery_accuracy,
        switch_recovery_accuracy = filtered_summary.switch_recovery_accuracy - smoothed_summary.switch_recovery_accuracy
    )
end

function per_seed_delta_row(filtered_row, smoothed_row)
    return (
        seed = filtered_row.seed,
        model = filtered_row.model,
        world_accuracy_delta = filtered_row.world_accuracy - smoothed_row.world_accuracy,
        heldout_nll_delta = filtered_row.heldout_nll - smoothed_row.heldout_nll,
        ece_delta = filtered_row.ece - smoothed_row.ece,
        future_reliability_brier_delta = filtered_row.future_reliability_brier - smoothed_row.future_reliability_brier,
        context_recovery_accuracy_delta = filtered_row.context_recovery_accuracy - smoothed_row.context_recovery_accuracy,
        switch_recovery_accuracy_delta = filtered_row.switch_recovery_accuracy - smoothed_row.switch_recovery_accuracy
    )
end

function evaluate_sim1_theory(summary_by_model)
    blt = summary_by_model["BLTGlobal"]
    flat = summary_by_model["FlatFixed"]
    local_model = summary_by_model["LocalPrecision"]

    min_support = (
        blt.heldout_nll <= 0.95 * flat.heldout_nll &&
        blt.future_reliability_brier <= 0.90 * flat.future_reliability_brier &&
        blt.context_recovery_accuracy > 0.65
    )
    strong_support = (
        blt.future_reliability_brier <= 0.97 * local_model.future_reliability_brier &&
        blt.switch_recovery_accuracy >= flat.switch_recovery_accuracy + 0.05
    )

    label = if min_support && strong_support
        "support"
    elseif min_support
        "weak_support"
    elseif blt.heldout_nll < flat.heldout_nll || blt.future_reliability_brier < flat.future_reliability_brier
        "null"
    else
        "falsified"
    end

    return (label = label, minimum_support = min_support, stronger_support = strong_support)
end

function trace_rows_for_episode(
    seed::Int,
    model_name::String,
    episode_kind::String,
    episode_index::Int,
    inference;
    posterior_mode::Symbol = :filtered
)
    fields = sim1_mode_fields(posterior_mode)
    world_posteriors = getproperty(inference, fields.world)
    phi_posteriors = getproperty(inference, fields.phi)

    rows = NamedTuple[]
    T = size(world_posteriors, 1)
    for t in 1:T
        push!(rows, (
            seed = seed,
            model = model_name,
            posterior_mode = String(posterior_mode),
            episode_kind = episode_kind,
            episode_index = episode_index,
            t = t,
            p_s1 = world_posteriors[t, 1],
            p_s2 = world_posteriors[t, 2],
            p_s3 = world_posteriors[t, 3],
            p_s4 = world_posteriors[t, 4],
            p_phi1 = isnothing(phi_posteriors) ? NaN : phi_posteriors[t, 1],
            p_phi2 = isnothing(phi_posteriors) ? NaN : phi_posteriors[t, 2],
            p_phi3 = isnothing(phi_posteriors) ? NaN : phi_posteriors[t, 3],
            p_phi4 = isnothing(phi_posteriors) ? NaN : phi_posteriors[t, 4]
        ))
    end
    return rows
end

function sim1_plot_and_save(output_dir::AbstractString, filtered_rows, traces)
    model_names = ["FlatFixed", "LocalPrecision", "BLTGlobal"]
    accs = [mean([row.world_accuracy for row in filtered_rows if row.model == m]) for m in model_names]
    briers = [mean([row.future_reliability_brier for row in filtered_rows if row.model == m]) for m in model_names]
    p1 = bar(model_names, accs, title = "Sim1 World Accuracy (Filtered)", ylabel = "accuracy", legend = false)
    p2 = bar(model_names, briers, title = "Sim1 Future Reliability Brier (Filtered)", ylabel = "brier", legend = false)
    save_plot(joinpath(output_dir, "accuracy_bar.png"), p1)
    save_plot(joinpath(output_dir, "future_reliability_brier_bar.png"), p2)

    blt_probe = filter(row -> row.model == "BLTGlobal" && row.episode_kind == "probe" && row.posterior_mode == "filtered", traces)
    if !isempty(blt_probe)
        p3 = plot(title = "Sim1 BLTGlobal Probe Context Posterior (Filtered)", xlabel = "t", ylabel = "probability")
        plot!(p3, [row.p_phi1 for row in blt_probe], label = "BG", lw = 2)
        plot!(p3, [row.p_phi2 for row in blt_probe], label = "VG", lw = 2)
        plot!(p3, [row.p_phi3 for row in blt_probe], label = "AG", lw = 2)
        plot!(p3, [row.p_phi4 for row in blt_probe], label = "BP", lw = 2)
        save_plot(joinpath(output_dir, "blt_probe_context_posterior.png"), p3)
    end
end

function run_sim1(; config_path::Union{Nothing, String} = nothing, output_dir::Union{Nothing, String} = nothing)
    started = time()
    config = isnothing(config_path) ? default_sim1_config() : load_sim1_config(config_path)
    models = [
        ("FlatFixed", sim1_flat_fixed_infer),
        ("LocalPrecision", sim1_local_precision_infer),
        ("BLTGlobal", sim1_blt_global_infer)
    ]

    filtered_rows = NamedTuple[]
    smoothed_rows = NamedTuple[]
    traces = NamedTuple[]

    for seed in config.seeds
        rng = default_rng(seed)
        dataset = generate_sim1_dataset(rng, config)

        for (model_name, model_fn) in models
            natural_filtered = NamedTuple[]
            natural_smoothed = NamedTuple[]
            probe_filtered = NamedTuple[]
            probe_smoothed = NamedTuple[]

            for (episode_index, episode) in enumerate(dataset.natural)
                inference = model_fn(episode, config)
                push!(natural_filtered, sim1_episode_metrics(model_name, inference, episode, config; is_probe = false, posterior_mode = :filtered))
                push!(natural_smoothed, sim1_episode_metrics(model_name, inference, episode, config; is_probe = false, posterior_mode = :smoothed))
                if seed == first(config.seeds) && episode_index == 1
                    append!(traces, trace_rows_for_episode(seed, model_name, "natural", episode_index, inference; posterior_mode = :filtered))
                    append!(traces, trace_rows_for_episode(seed, model_name, "natural", episode_index, inference; posterior_mode = :smoothed))
                end
            end

            for (episode_index, episode) in enumerate(dataset.probe)
                inference = model_fn(episode, config)
                push!(probe_filtered, sim1_episode_metrics(model_name, inference, episode, config; is_probe = true, posterior_mode = :filtered))
                push!(probe_smoothed, sim1_episode_metrics(model_name, inference, episode, config; is_probe = true, posterior_mode = :smoothed))
                if seed == first(config.seeds) && episode_index == 1
                    append!(traces, trace_rows_for_episode(seed, model_name, "probe", episode_index, inference; posterior_mode = :filtered))
                    append!(traces, trace_rows_for_episode(seed, model_name, "probe", episode_index, inference; posterior_mode = :smoothed))
                end
            end

            push!(filtered_rows, (
                seed = seed,
                model = model_name,
                world_accuracy = safe_mean([row.world_accuracy for row in natural_filtered]),
                heldout_nll = safe_mean([row.heldout_nll for row in probe_filtered]),
                ece = safe_mean([row.ece for row in natural_filtered]),
                future_reliability_brier = safe_mean([row.future_reliability_brier for row in probe_filtered]),
                context_recovery_accuracy = safe_mean(filter(!isnan, [row.context_recovery_accuracy for row in natural_filtered])),
                switch_recovery_accuracy = safe_mean(filter(!isnan, [row.switch_recovery_accuracy for row in probe_filtered]))
            ))

            push!(smoothed_rows, (
                seed = seed,
                model = model_name,
                world_accuracy = safe_mean([row.world_accuracy for row in natural_smoothed]),
                heldout_nll = safe_mean([row.heldout_nll for row in probe_smoothed]),
                ece = safe_mean([row.ece for row in natural_smoothed]),
                future_reliability_brier = safe_mean([row.future_reliability_brier for row in probe_smoothed]),
                context_recovery_accuracy = safe_mean(filter(!isnan, [row.context_recovery_accuracy for row in natural_smoothed])),
                switch_recovery_accuracy = safe_mean(filter(!isnan, [row.switch_recovery_accuracy for row in probe_smoothed]))
            ))
        end
    end

    delta_rows = [per_seed_delta_row(filtered_rows[i], smoothed_rows[i]) for i in eachindex(filtered_rows)]

    filtered_summary_by_model = Dict{String, NamedTuple}()
    smoothed_summary_by_model = Dict{String, NamedTuple}()
    delta_by_model = Dict{String, NamedTuple}()
    for model_name in ("FlatFixed", "LocalPrecision", "BLTGlobal")
        filtered_summary_by_model[model_name] = summarize_model_rows(filter(row -> row.model == model_name, filtered_rows))
        smoothed_summary_by_model[model_name] = summarize_model_rows(filter(row -> row.model == model_name, smoothed_rows))
        delta_by_model[model_name] = delta_namedtuple(filtered_summary_by_model[model_name], smoothed_summary_by_model[model_name])
    end

    theory_filtered = evaluate_sim1_theory(filtered_summary_by_model)
    theory_smoothed = evaluate_sim1_theory(smoothed_summary_by_model)
    implementation_passed = all(all(isfinite, [
        row.world_accuracy,
        row.heldout_nll,
        row.ece,
        row.future_reliability_brier
    ]) for row in filtered_rows)

    summary = (
        simulation = "sim1",
        config = (
            seeds = config.seeds,
            n_episodes = config.n_episodes,
            n_probe_episodes = config.n_probe_episodes,
            T = config.T
        ),
        metric_source_for_theory = "filtered",
        filtered_summary_by_model = filtered_summary_by_model,
        smoothed_summary_by_model = smoothed_summary_by_model,
        delta_by_model = delta_by_model,
        theory_result = theory_filtered.label,
        filtered_theory_result = theory_filtered.label,
        smoothed_theory_result = theory_smoothed.label
    )

    status = (
        implementation_passed = implementation_passed,
        theory_result = theory_filtered.label,
        filtered_theory_result = theory_filtered.label,
        smoothed_theory_result = theory_smoothed.label
    )

    metadata = build_reproducibility_metadata(
        config;
        config_path = config_path,
        runtime_seconds = time() - started,
        repo_root = abspath(joinpath(@__DIR__, "..", "..", "..", ".."))
    )

    if !isnothing(output_dir)
        ensure_dir(output_dir)
        write_json(joinpath(output_dir, "summary.json"), summary)
        write_rows_csv(joinpath(output_dir, "per_seed_metrics.csv"), filtered_rows)
        write_rows_csv(joinpath(output_dir, "per_seed_metrics_filtered.csv"), filtered_rows)
        write_rows_csv(joinpath(output_dir, "per_seed_metrics_smoothed.csv"), smoothed_rows)
        write_rows_csv(joinpath(output_dir, "metric_deltas.csv"), delta_rows)
        write_rows_csv(joinpath(output_dir, "posterior_traces.csv"), traces)
        write_json(joinpath(output_dir, "status.json"), status)
        write_json(joinpath(output_dir, "metadata.json"), metadata)
        sim1_plot_and_save(output_dir, filtered_rows, traces)
    end

    return (
        config = config,
        filtered_per_seed_metrics = filtered_rows,
        smoothed_per_seed_metrics = smoothed_rows,
        metric_deltas = delta_rows,
        filtered_summary_by_model = filtered_summary_by_model,
        smoothed_summary_by_model = smoothed_summary_by_model,
        summary = summary,
        status = status,
        metadata = metadata
    )
end
