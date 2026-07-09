module Runner

using Dates
using Statistics

using ..Config: ExperimentConfig, config_snapshot, load_config
using ..Criteria: write_criteria_results
using ..DummyExperiment: run_dummy_seed
using ..IO: ensure_dir, write_json, write_placeholder_svg, write_rows_csv
using ..Reproducibility: build_reproducibility_metadata
using ..Sim1: run_sim1
using ..Sim3: run_sim3_config

export run_config

function timestamp_label()
    return Dates.format(Dates.now(Dates.UTC), Dates.dateformat"yyyymmddTHHMMSSZ")
end

function run_output_dir(config::ExperimentConfig)
    label = isnothing(config.label) ? timestamp_label() : config.label
    return normpath(joinpath(config.output_dir, config.experiment, label))
end

function summarize_seed_rows(seed_rows)
    gains = [row.concentration_gain for row in seed_rows]
    final_concentrations = [row.final_true_A_concentration for row in seed_rows]
    final_entropies = [row.final_A_entropy for row in seed_rows]
    return (
        n_seeds = length(seed_rows),
        mean_concentration_gain = mean(gains),
        min_concentration_gain = minimum(gains),
        mean_final_true_A_concentration = mean(final_concentrations),
        mean_final_A_entropy = mean(final_entropies),
        growth_rate = mean(row.growth_happened ? 1.0 : 0.0 for row in seed_rows)
    )
end

function flattened_seed_rows(seed_results)
    [(
        seed = row.seed,
        initial_true_A_concentration = row.initial_true_A_concentration,
        final_true_A_concentration = row.final_true_A_concentration,
        concentration_gain = row.concentration_gain,
        final_A_entropy = row.final_A_entropy,
        growth_happened = row.growth_happened,
        final_factor1_states = row.final_factor1_states,
        final_factor2_states = row.final_factor2_states
    ) for row in seed_results]
end

function trace_rows(seed_results)
    rows = NamedTuple[]
    for row in seed_results
        append!(rows, row.checkpoints)
    end
    return rows
end

function theory_label(results)
    isempty(results.results) && return "null"
    labels = [row.label for row in results.results if row.kind == "success"]
    isempty(labels) && return "null"
    any(==("falsified"), labels) && return "falsified"
    all(==("support"), labels) && return "support"
    any(==("weak_support"), labels) && return "weak_support"
    return "null"
end

function run_config(config::ExperimentConfig; config_path::Union{Nothing, AbstractString} = nothing, output_dir::Union{Nothing, AbstractString} = nothing)
    if config.experiment == "sim1"
        outdir = isnothing(output_dir) ? run_output_dir(config) : output_dir
        return run_sim1(config; config_path = config_path, output_dir = outdir)
    end

    if config.experiment == "sim3"
        return run_sim3_config(config; config_path = config_path, output_dir = output_dir)
    end

    started = time()
    outdir = isnothing(output_dir) ? run_output_dir(config) : output_dir
    ensure_dir(outdir)

    trials = Int(get(config.model_params, "trials", 120))
    growth_trial = Int(get(config.model_params, "growth_trial", max(2, cld(trials, 2))))

    seed_results = [run_dummy_seed(seed; trials = trials, growth_trial = growth_trial) for seed in config.seeds]
    per_seed = flattened_seed_rows(seed_results)
    traces = trace_rows(seed_results)
    aggregate = summarize_seed_rows(per_seed)

    summary = (
        experiment = config.experiment,
        config = config_snapshot(config),
        metrics = aggregate,
        per_seed_metric_count = length(per_seed),
        trace_row_count = length(traces)
    )

    summary_path = joinpath(outdir, "summary.json")
    write_json(summary_path, summary)
    write_rows_csv(joinpath(outdir, "per_seed_metrics.csv"), per_seed)
    write_rows_csv(joinpath(outdir, "posterior_traces.csv"), traces)
    ensure_dir(joinpath(outdir, "figures"))
    write_placeholder_svg(joinpath(outdir, "figures", "dummy_trace.svg"); title = "dummy experiment")

    criteria_results = nothing
    if !isnothing(config.criteria_path) && isfile(config.criteria_path)
        criteria_results = write_criteria_results(config.criteria_path, summary_path, joinpath(outdir, "criteria-results.json"))
    end
    status = (
        implementation_passed = all(row.growth_happened for row in per_seed) && all(isfinite, [row.concentration_gain for row in per_seed]),
        theory_result = isnothing(criteria_results) ? "null" : theory_label(criteria_results),
        criteria_results_path = isnothing(criteria_results) ? nothing : joinpath(outdir, "criteria-results.json")
    )
    write_json(joinpath(outdir, "status.json"), status)

    metadata = build_reproducibility_metadata(
        config;
        config_path = config_path,
        runtime_seconds = time() - started,
        repo_root = normpath(joinpath(@__DIR__, "..", "..", "..")),
        extra = (output_dir = abspath(outdir),)
    )
    write_json(joinpath(outdir, "metadata.json"), metadata)

    return (
        output_dir = outdir,
        summary = summary,
        status = status,
        criteria_results = criteria_results
    )
end

function run_config(config_path::AbstractString)
    config = load_config(config_path)
    return run_config(config; config_path = config_path)
end

end
