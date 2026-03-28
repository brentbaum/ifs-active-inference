function sim2_mode_fields(posterior_mode::Symbol)
    if posterior_mode == :filtered
        return (
            joint = :filtered_joint_posteriors,
            g = :filtered_g_posteriors
        )
    elseif posterior_mode == :smoothed
        return (
            joint = :smoothed_joint_posteriors,
            g = :smoothed_g_posteriors
        )
    else
        error("Unknown posterior mode: $posterior_mode")
    end
end

function sim2_coherence_from_joint(joint_posteriors::Matrix{Float64}, dims::Vector{Int})
    scores = Float64[]
    for t in axes(joint_posteriors, 1)
        score = 0.0
        for idx in axes(joint_posteriors, 2)
            state = unflatten_state(idx, dims)
            g = state[1]
            z1 = state[end - 1]
            z2 = state[end]
            if z1 == g && z2 == g
                score += joint_posteriors[t, idx]
            end
        end
        push!(scores, score)
    end
    return scores
end

function sim2_binding_from_g(g_posteriors::Matrix{Float64})
    return [abs(g_posteriors[t, 1] - g_posteriors[t, 2]) for t in axes(g_posteriors, 1)]
end

function sim2_stable_natural_window(episode; burn_in::Int = 20)
    return [
        t for t in eachindex(episode.g)
        if t > burn_in && episode.phi[t] == BIND
    ]
end

function sim2_episode_metrics(
    model_name::String,
    inference,
    episode,
    dims::Vector{Int};
    compute_accuracy::Bool = true,
    stable_window::Union{Nothing, Vector{Int}} = nothing,
    posterior_mode::Symbol = :filtered
)
    fields = sim2_mode_fields(posterior_mode)
    joint_posteriors = getproperty(inference, fields.joint)
    g_posteriors = getproperty(inference, fields.g)

    g_map = [argmax(view(g_posteriors, t, :)) for t in axes(g_posteriors, 1)]
    coherence_ts = sim2_coherence_from_joint(joint_posteriors, dims)
    binding_ts = sim2_binding_from_g(g_posteriors)
    coherence_idxs = isnothing(stable_window) || isempty(stable_window) ? collect(eachindex(coherence_ts)) : stable_window
    scene_accuracy = compute_accuracy ? state_accuracy(g_posteriors, episode.g) : NaN
    confident_wrong = mean(Float64[
        (g_map[t] != episode.g[t]) && (maximum(view(g_posteriors, t, :)) > 0.80)
        for t in eachindex(episode.g)
    ])

    return (
        posterior_mode = String(posterior_mode),
        model = model_name,
        scene_accuracy = scene_accuracy,
        coherence = mean(coherence_ts[coherence_idxs]),
        binding_index = mean(binding_ts),
        micro_switch_rate = micro_switch_rate(g_map),
        mean_dwell = mean_dwell(g_map),
        confident_wrong = confident_wrong,
        heldout_nll = negative_log_likelihood(inference.log_evidence, length(episode.g))
    )
end

function summarize_sim2_model_rows(rows)
    return (
        scene_accuracy = safe_mean(filter(!isnan, [row.scene_accuracy for row in rows])),
        coherence = safe_mean([row.coherence for row in rows]),
        binding_index = safe_mean([row.binding_index for row in rows]),
        micro_switch_rate = safe_mean([row.micro_switch_rate for row in rows]),
        mean_dwell = safe_mean([row.mean_dwell for row in rows]),
        confident_wrong = safe_mean([row.confident_wrong for row in rows]),
        heldout_nll = safe_mean([row.heldout_nll for row in rows])
    )
end

function delta_sim2_namedtuple(filtered_summary, smoothed_summary)
    return (
        scene_accuracy = filtered_summary.scene_accuracy - smoothed_summary.scene_accuracy,
        coherence = filtered_summary.coherence - smoothed_summary.coherence,
        binding_index = filtered_summary.binding_index - smoothed_summary.binding_index,
        micro_switch_rate = filtered_summary.micro_switch_rate - smoothed_summary.micro_switch_rate,
        mean_dwell = filtered_summary.mean_dwell - smoothed_summary.mean_dwell,
        confident_wrong = filtered_summary.confident_wrong - smoothed_summary.confident_wrong,
        heldout_nll = filtered_summary.heldout_nll - smoothed_summary.heldout_nll
    )
end

function sim2_per_seed_delta_row(filtered_row, smoothed_row)
    return (
        seed = filtered_row.seed,
        model = filtered_row.model,
        scene_accuracy_delta = filtered_row.scene_accuracy - smoothed_row.scene_accuracy,
        coherence_delta = filtered_row.coherence - smoothed_row.coherence,
        binding_index_delta = filtered_row.binding_index - smoothed_row.binding_index,
        micro_switch_rate_delta = filtered_row.micro_switch_rate - smoothed_row.micro_switch_rate,
        mean_dwell_delta = filtered_row.mean_dwell - smoothed_row.mean_dwell,
        confident_wrong_delta = filtered_row.confident_wrong - smoothed_row.confident_wrong,
        heldout_nll_delta = filtered_row.heldout_nll - smoothed_row.heldout_nll
    )
end

function evaluate_sim2_theory(summary_by_model)
    blt = summary_by_model["BLTGlobal"]
    hier = summary_by_model["HierFixed"]
    local_model = summary_by_model["LocalBranch"]
    min_support = (
        blt.coherence >= hier.coherence + 0.10 &&
        blt.micro_switch_rate <= 0.75 * hier.micro_switch_rate &&
        blt.mean_dwell >= 1.25 * hier.mean_dwell
    )
    strong_support = (
        blt.coherence > local_model.coherence || blt.mean_dwell > local_model.mean_dwell
    ) && blt.confident_wrong > 0.02

    label = if min_support && strong_support
        "support"
    elseif min_support
        "weak_support"
    elseif blt.coherence > hier.coherence || blt.mean_dwell > hier.mean_dwell
        "null"
    else
        "falsified"
    end

    return (label = label, minimum_support = min_support, stronger_support = strong_support)
end

function sim2_trace_rows(seed::Int, model_name::String, inference; posterior_mode::Symbol = :filtered)
    fields = sim2_mode_fields(posterior_mode)
    g_posteriors = getproperty(inference, fields.g)
    rows = NamedTuple[]
    for t in axes(g_posteriors, 1)
        push!(rows, (
            seed = seed,
            model = model_name,
            posterior_mode = String(posterior_mode),
            t = t,
            p_gA = g_posteriors[t, 1],
            p_gB = g_posteriors[t, 2]
        ))
    end
    return rows
end

function sim2_plot_and_save(output_dir::AbstractString, ambiguity_traces, filtered_rows)
    model_names = ["HierFixed", "LocalBranch", "BLTGlobal"]
    colors = [:gray40, :orange, :teal]

    p1 = plot(title = "Ambiguity Probe: P(g=A) (Filtered)", xlabel = "t", ylabel = "Posterior")
    for (i, model_name) in enumerate(model_names)
        plot!(p1, ambiguity_traces[model_name][:, 1], label = model_name, color = colors[i], lw = 2)
    end
    save_plot(joinpath(output_dir, "ambiguity_scene_posterior.png"), p1)

    means_coherence = [safe_mean([row.coherence for row in filtered_rows if row.model == m]) for m in model_names]
    means_switch = [safe_mean([row.micro_switch_rate for row in filtered_rows if row.model == m]) for m in model_names]
    p2 = bar(model_names, means_coherence, title = "Coherence by Model (Filtered)", legend = false, ylabel = "Mean coherence")
    save_plot(joinpath(output_dir, "coherence_bar.png"), p2)
    p3 = bar(model_names, means_switch, title = "Micro-switch Rate (Filtered)", legend = false, ylabel = "Rate")
    save_plot(joinpath(output_dir, "micro_switch_bar.png"), p3)
end

function run_sim2(; config_path::Union{Nothing, String} = nothing, output_dir::Union{Nothing, String} = nothing)
    started = time()
    config = isnothing(config_path) ? default_sim2_config() : load_sim2_config(config_path)
    filtered_rows = NamedTuple[]
    smoothed_rows = NamedTuple[]
    traces = NamedTuple[]
    filtered_ambiguity_traces = Dict{String, Matrix{Float64}}()

    models = [
        ("HierFixed", sim2_hier_fixed_infer, [2, 2, 2]),
        ("LocalBranch", sim2_local_branch_infer, [2, 2, 2, 2, 2]),
        ("BLTGlobal", sim2_blt_global_infer, [2, 2, 2, 2])
    ]

    for seed in config.seeds
        dataset = generate_sim2_dataset(default_rng(seed), config)

        for (model_name, infer_fn, dims) in models
            natural_filtered = NamedTuple[]
            natural_smoothed = NamedTuple[]
            for episode in dataset.natural
                inference = infer_fn(episode, config)
                stable_window = sim2_stable_natural_window(episode)
                push!(natural_filtered, sim2_episode_metrics(model_name, inference, episode, dims; stable_window = stable_window, posterior_mode = :filtered))
                push!(natural_smoothed, sim2_episode_metrics(model_name, inference, episode, dims; stable_window = stable_window, posterior_mode = :smoothed))
            end

            unambiguous_inference = infer_fn(dataset.unambiguous, config)
            ambiguity_inference = infer_fn(dataset.ambiguity, config)
            bias_inference = infer_fn(dataset.bias, config; bias_probe = true)

            unambiguous_filtered = sim2_episode_metrics(model_name, unambiguous_inference, dataset.unambiguous, dims; posterior_mode = :filtered)
            unambiguous_smoothed = sim2_episode_metrics(model_name, unambiguous_inference, dataset.unambiguous, dims; posterior_mode = :smoothed)
            ambiguity_filtered = sim2_episode_metrics(model_name, ambiguity_inference, dataset.ambiguity, dims; posterior_mode = :filtered)
            ambiguity_smoothed = sim2_episode_metrics(model_name, ambiguity_inference, dataset.ambiguity, dims; posterior_mode = :smoothed)
            bias_filtered = sim2_episode_metrics(model_name, bias_inference, dataset.bias, dims; posterior_mode = :filtered)
            bias_smoothed = sim2_episode_metrics(model_name, bias_inference, dataset.bias, dims; posterior_mode = :smoothed)

            if seed == first(config.seeds)
                filtered_ambiguity_traces[model_name] = ambiguity_inference.filtered_g_posteriors
                append!(traces, sim2_trace_rows(seed, model_name, ambiguity_inference; posterior_mode = :filtered))
                append!(traces, sim2_trace_rows(seed, model_name, ambiguity_inference; posterior_mode = :smoothed))
            end

            push!(filtered_rows, (
                seed = seed,
                model = model_name,
                scene_accuracy = safe_mean([row.scene_accuracy for row in natural_filtered]),
                coherence = safe_mean([row.coherence for row in natural_filtered]),
                binding_index = ambiguity_filtered.binding_index,
                micro_switch_rate = ambiguity_filtered.micro_switch_rate,
                mean_dwell = ambiguity_filtered.mean_dwell,
                confident_wrong = bias_filtered.confident_wrong,
                heldout_nll = safe_mean([row.heldout_nll for row in natural_filtered]),
                unambiguous_accuracy = unambiguous_filtered.scene_accuracy
            ))

            push!(smoothed_rows, (
                seed = seed,
                model = model_name,
                scene_accuracy = safe_mean([row.scene_accuracy for row in natural_smoothed]),
                coherence = safe_mean([row.coherence for row in natural_smoothed]),
                binding_index = ambiguity_smoothed.binding_index,
                micro_switch_rate = ambiguity_smoothed.micro_switch_rate,
                mean_dwell = ambiguity_smoothed.mean_dwell,
                confident_wrong = bias_smoothed.confident_wrong,
                heldout_nll = safe_mean([row.heldout_nll for row in natural_smoothed]),
                unambiguous_accuracy = unambiguous_smoothed.scene_accuracy
            ))
        end
    end

    delta_rows = [sim2_per_seed_delta_row(filtered_rows[i], smoothed_rows[i]) for i in eachindex(filtered_rows)]

    filtered_summary_by_model = Dict{String, NamedTuple}()
    smoothed_summary_by_model = Dict{String, NamedTuple}()
    delta_by_model = Dict{String, NamedTuple}()
    for model_name in ("HierFixed", "LocalBranch", "BLTGlobal")
        filtered_summary_by_model[model_name] = summarize_sim2_model_rows(filter(row -> row.model == model_name, filtered_rows))
        smoothed_summary_by_model[model_name] = summarize_sim2_model_rows(filter(row -> row.model == model_name, smoothed_rows))
        delta_by_model[model_name] = delta_sim2_namedtuple(filtered_summary_by_model[model_name], smoothed_summary_by_model[model_name])
    end

    theory_filtered = evaluate_sim2_theory(filtered_summary_by_model)
    theory_smoothed = evaluate_sim2_theory(smoothed_summary_by_model)
    implementation_passed = all(row.unambiguous_accuracy > 0.90 for row in filtered_rows)

    summary = (
        simulation = "sim2",
        config = (seeds = config.seeds, n_episodes = config.n_episodes, T = config.T),
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
        sim2_plot_and_save(output_dir, filtered_ambiguity_traces, filtered_rows)
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
