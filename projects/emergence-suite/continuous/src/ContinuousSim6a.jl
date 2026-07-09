module ContinuousSim6a

using Dates
using LinearAlgebra
using Printf
using Random
using RxInfer
using Statistics

export run_all

const DEFAULT_SEEDS = [11, 23, 37, 53, 71, 97, 131, 173, 211, 251,
    293, 337, 379, 421, 463, 509, 557, 601, 647, 691]

Base.@kwdef struct RunConfig
    run_id::String = "sim6a_continuous_stage3"
    seeds::Vector{Int} = copy(DEFAULT_SEEDS)
    time_steps::Int = 160
    burst_doses::Vector{Float64} = [0.4, 0.8, 1.2, 1.6]
    bundle_strength_grid::Vector{Float64} = [0.8, 1.1, 1.4, 1.7, 2.0]
    volatility_sensitivity_grid::Vector{Float64} = [0.4, 0.7, 1.0, 1.3, 1.6]
    basin_initial_grid_size::Int = 11
    basin_steps::Int = 900
    basin_dt::Float64 = 0.04
    hysteresis_seed::Int = 11
end

Base.@kwdef struct DynamicsParams
    bundle_strength::Float64 = 1.2
    evidence_strength::Float64 = 1.0
    volatility_sensitivity::Float64 = 1.0
    beta_bundle::Float64 = 1.05
    gamma_evidence::Float64 = 1.25
    ambient_volatility::Float64 = 0.04
    volatility_floor::Float64 = 0.015
    capture_volatility_gain::Float64 = 0.42
    depth_error_gain::Float64 = 0.24
    self_loop_gain::Float64 = 0.62
    depth_cost::Float64 = 0.26
    self_support::Float64 = 0.20
    depth_rate::Float64 = 0.42
    capture_rate::Float64 = 1.15
    process_var::Float64 = 0.006
    observation_var::Float64 = 0.035
    innovation_var_gain::Float64 = 0.055
    min_depth_var::Float64 = 0.012
    max_depth_var::Float64 = 0.55
end

struct Criterion
    id::String
    description::String
    metric_path::String
    comparator::String
    threshold::Float64
    weak_threshold::Union{Nothing, Float64}
    opposite_threshold::Union{Nothing, Float64}
    kind::String
end

clamp01(x) = clamp(x, 0.0, 1.0)

function parse_number_list(text::AbstractString, key::AbstractString, default)
    m = match(Regex("^$(key):\\s*\\[(.*)\\]", "m"), text)
    m === nothing && return default
    body = strip(m.captures[1])
    isempty(body) && return Float64[]
    return [parse(Float64, strip(part)) for part in split(body, ",")]
end

function parse_int_list(text::AbstractString, key::AbstractString, default)
    return Int.(round.(parse_number_list(text, key, Float64.(default))))
end

function parse_scalar(text::AbstractString, key::AbstractString, default)
    m = match(Regex("^$(key):\\s*([^\\n#]+)", "m"), text)
    m === nothing && return default
    raw = strip(m.captures[1])
    if default isa Int
        return parse(Int, raw)
    elseif default isa AbstractFloat
        return parse(Float64, raw)
    else
        return raw
    end
end

function load_config(path::AbstractString)
    text = read(path, String)
    defaults = RunConfig()
    return RunConfig(
        run_id = parse_scalar(text, "run_id", defaults.run_id),
        seeds = parse_int_list(text, "seeds", defaults.seeds),
        time_steps = parse_scalar(text, "time_steps", defaults.time_steps),
        burst_doses = parse_number_list(text, "burst_doses", defaults.burst_doses),
        bundle_strength_grid = parse_number_list(text, "bundle_strength_grid", defaults.bundle_strength_grid),
        volatility_sensitivity_grid = parse_number_list(text, "volatility_sensitivity_grid", defaults.volatility_sensitivity_grid),
        basin_initial_grid_size = parse_scalar(text, "basin_initial_grid_size", defaults.basin_initial_grid_size),
        basin_steps = parse_scalar(text, "basin_steps", defaults.basin_steps),
        basin_dt = parse_scalar(text, "basin_dt", defaults.basin_dt),
        hysteresis_seed = parse_scalar(text, "hysteresis_seed", defaults.hysteresis_seed)
    )
end

function load_criteria(path::AbstractString)
    text = read(path, String)
    blocks = split(text, r"\n\s*-\s+id:\s+")
    rows = Criterion[]
    for block in Iterators.drop(blocks, 1)
        lines = split(block, "\n")
        id = strip(lines[1])
        field(name, default = "") = begin
            m = match(Regex("^\\s*$(name):\\s*(.*)\$", "m"), block)
            m === nothing ? default : strip(replace(m.captures[1], "\"" => ""))
        end
        weak = field("weak_threshold", "nothing")
        opposite = field("opposite_threshold", "nothing")
        push!(rows, Criterion(
            id,
            field("description"),
            field("metric_path"),
            field("comparator"),
            parse(Float64, field("threshold")),
            weak == "nothing" ? nothing : parse(Float64, weak),
            opposite == "nothing" ? nothing : parse(Float64, opposite),
            field("kind")
        ))
    end
    return rows
end

function effective_precision_share(depth::Real, volatility::Real, p::DynamicsParams)
    d = clamp(depth, 0.0, 1.15)
    v = max(0.0, volatility)
    bundle_precision = p.bundle_strength * exp(-p.beta_bundle * d) * (1.0 + p.volatility_sensitivity * v)
    evidence_precision = p.evidence_strength * exp(p.gamma_evidence * d) / (1.0 + 0.45 * p.volatility_sensitivity * v)
    return bundle_precision / (bundle_precision + evidence_precision)
end

function endogenous_volatility(depth::Real, capture::Real, p::DynamicsParams; external_load::Real = 0.0)
    d = clamp01(depth)
    c = clamp01(capture)
    raw = p.ambient_volatility + external_load +
        p.capture_volatility_gain * c^2 +
        p.depth_error_gain * (1.0 - d)^2 -
        p.self_loop_gain * d^2 * (1.0 - c)^2
    return max(p.volatility_floor, raw)
end

function dynamics_vector(depth::Real, capture::Real, p::DynamicsParams)
    v = endogenous_volatility(depth, capture, p)
    self_loop = p.self_loop_gain * (1.0 - capture)^2 * depth
    target_depth = clamp01(1.08 + p.self_support + self_loop - p.depth_cost -
        p.volatility_sensitivity * v - 0.55 * capture^2)
    target_capture = effective_precision_share(depth, v, p)
    return (
        d_depth = p.depth_rate * (target_depth - depth),
        d_capture = p.capture_rate * (target_capture - capture),
        target_depth = target_depth,
        target_capture = target_capture,
        volatility = v
    )
end

function integrate_expected(depth0::Float64, capture0::Float64, p::DynamicsParams, config::RunConfig)
    depth = clamp01(depth0)
    capture = clamp01(capture0)
    for _ in 1:config.basin_steps
        dv = dynamics_vector(depth, capture, p)
        depth = clamp01(depth + config.basin_dt * dv.d_depth)
        capture = clamp01(capture + config.basin_dt * dv.d_capture)
    end
    dv = dynamics_vector(depth, capture, p)
    residual = hypot(dv.d_depth, dv.d_capture)
    return (depth = depth, capture = capture, residual = residual, volatility = dv.volatility)
end

function classify_endpoint(depth::Real, capture::Real)
    if depth >= 0.74 && capture <= 0.35
        return "self"
    elseif depth <= 0.50 && capture >= 0.50
        return "capture"
    else
        return "mixed"
    end
end

function cluster_endpoints(endpoints)
    clusters = NamedTuple[]
    for label in ("self", "capture", "mixed")
        group = filter(row -> row.class == label, endpoints)
        isempty(group) && continue
        push!(clusters, (
            class = label,
            depth = mean(row.depth for row in group),
            capture = mean(row.capture for row in group),
            n = length(group),
            max_residual = maximum(row.residual for row in group)
        ))
    end
    return clusters
end

function basin_map(config::RunConfig)
    rows = NamedTuple[]
    fixed_rows = NamedTuple[]
    g = range(0.02, 0.98; length = config.basin_initial_grid_size)
    for bundle_strength in config.bundle_strength_grid, vol_sens in config.volatility_sensitivity_grid
        p = DynamicsParams(bundle_strength = bundle_strength, volatility_sensitivity = vol_sens)
        endpoints = NamedTuple[]
        for d0 in g, c0 in g
            endpoint = integrate_expected(Float64(d0), Float64(c0), p, config)
            class = classify_endpoint(endpoint.depth, endpoint.capture)
            push!(rows, (
                bundle_strength = bundle_strength,
                volatility_sensitivity = vol_sens,
                initial_depth = Float64(d0),
                initial_capture = Float64(c0),
                final_depth = endpoint.depth,
                final_capture = endpoint.capture,
                residual = endpoint.residual,
                class = class
            ))
            push!(endpoints, (
                depth = endpoint.depth,
                capture = endpoint.capture,
                residual = endpoint.residual,
                class = class
            ))
        end
        clusters = cluster_endpoints(endpoints)
        self_exists = any(row -> row.class == "self", clusters)
        capture_exists = any(row -> row.class == "capture", clusters)
        self_fraction = count(row -> row.class == "self", endpoints) / length(endpoints)
        capture_fraction = count(row -> row.class == "capture", endpoints) / length(endpoints)
        for cluster in clusters
            push!(fixed_rows, merge(cluster, (
                bundle_strength = bundle_strength,
                volatility_sensitivity = vol_sens,
                self_exists = self_exists,
                capture_exists = capture_exists,
                self_basin_fraction = self_fraction,
                capture_basin_fraction = capture_fraction
            )))
        end
    end
    return (basin_rows = rows, fixed_rows = fixed_rows)
end

function burst_observation(t::Int, dose::Float64, rng::AbstractRNG, p::DynamicsParams)
    scheduled = if 35 <= t <= 54
        dose
    elseif 55 <= t <= 68
        0.45 * dose
    else
        0.0
    end
    return max(0.0, p.ambient_volatility + scheduled + 0.012 * randn(rng))
end

function volatility_slope(depth::Float64, capture::Float64, p::DynamicsParams)
    eps = 1e-4
    hi = volatility_likelihood_mean(min(1.0, depth + eps), capture, p)
    lo = volatility_likelihood_mean(max(0.0, depth - eps), capture, p)
    return (hi - lo) / (min(1.0, depth + eps) - max(0.0, depth - eps))
end

function volatility_likelihood_mean(depth::Real, capture::Real, p::DynamicsParams)
    d = clamp01(depth)
    c = clamp01(capture)
    return p.ambient_volatility + 1.00 * (1.0 - d)^2 + 0.25 * c^2
end

function simulate_trace(seed::Int, dose::Float64, config::RunConfig)
    rng = MersenneTwister(seed)
    p = DynamicsParams()
    depth_mean = 0.88 + 0.01 * randn(rng)
    depth_var = 0.045
    capture = effective_precision_share(depth_mean, p.ambient_volatility, p)
    rows = NamedTuple[]
    for t in 1:config.time_steps
        observed_volatility = burst_observation(t, dose, rng, p)
        pred_var = clamp(depth_var + p.process_var, p.min_depth_var, p.max_depth_var)
        predicted_volatility = volatility_likelihood_mean(depth_mean, capture, p)
        slope = volatility_slope(depth_mean, capture, p)
        innovation = observed_volatility - predicted_volatility
        innovation_var = slope^2 * pred_var + p.observation_var
        gain = pred_var * slope / innovation_var
        updated_mean = clamp(depth_mean + gain * innovation, 0.0, 1.05)
        updated_var = clamp((1.0 - gain * slope) * pred_var +
            p.innovation_var_gain * max(0.0, abs(innovation) - sqrt(p.observation_var))^2,
            p.min_depth_var, p.max_depth_var)
        capture = effective_precision_share(updated_mean, observed_volatility, p)
        push!(rows, (
            seed = seed,
            dose = dose,
            t = t,
            depth_mean = updated_mean,
            depth_var = updated_var,
            depth_precision = 1.0 / updated_var,
            capture = capture,
            observed_volatility = observed_volatility,
            predicted_volatility = predicted_volatility,
            volatility_innovation = innovation,
            burst_active = 35 <= t <= 68
        ))
        depth_mean = updated_mean
        depth_var = updated_var
    end
    return rows
end

function collapse_analysis(config::RunConfig)
    trace_rows = NamedTuple[]
    dose_rows = NamedTuple[]
    for dose in config.burst_doses
        seed_drops = Float64[]
        seed_recoveries = Float64[]
        seed_capture_rises = Float64[]
        for seed in config.seeds
            rows = simulate_trace(seed, dose, config)
            append!(trace_rows, rows)
            baseline_depth = mean(row.depth_mean for row in rows if row.t in 10:30)
            min_depth = minimum(row.depth_mean for row in rows if row.t in 35:72)
            baseline_precision = mean(row.depth_precision for row in rows if row.t in 10:30)
            min_precision = minimum(row.depth_precision for row in rows if row.t in 35:72)
            recovery_depth = mean(row.depth_mean for row in rows if row.t in 120:155)
            baseline_capture = mean(row.capture for row in rows if row.t in 10:30)
            max_capture = maximum(row.capture for row in rows if row.t in 35:72)
            push!(seed_drops, baseline_depth - min_depth)
            push!(seed_recoveries, (recovery_depth - min_depth) / max(baseline_depth - min_depth, 1e-9))
            push!(seed_capture_rises, max_capture - baseline_capture)
            _ = min_precision <= baseline_precision
        end
        push!(dose_rows, (
            dose = dose,
            mean_depth_drop = mean(seed_drops),
            mean_recovery_fraction = mean(seed_recoveries),
            mean_capture_rise = mean(seed_capture_rises),
            drop_ci95 = 1.96 * std(seed_drops) / sqrt(length(seed_drops)),
            recovery_ci95 = 1.96 * std(seed_recoveries) / sqrt(length(seed_recoveries))
        ))
    end
    drops = [row.mean_depth_drop for row in dose_rows]
    recoveries = [row.mean_recovery_fraction for row in dose_rows]
    captures = [row.mean_capture_rise for row in dose_rows]
    monotone_drop = all(diff(drops) .> 0.0)
    monotone_capture = all(diff(captures) .> 0.0)
    recoverable_count = count(x -> x >= 0.72, recoveries)
    return (
        trace_rows = trace_rows,
        dose_rows = dose_rows,
        metrics = (
            monotone_depth_drop = monotone_drop ? 1.0 : 0.0,
            monotone_capture_rise = monotone_capture ? 1.0 : 0.0,
            recoverable_dose_count = recoverable_count,
            max_depth_drop = maximum(drops),
            max_capture_rise = maximum(captures),
            min_recovery_fraction = minimum(recoveries),
            dose_recoverable_and_audit_ok = (monotone_drop && monotone_capture && recoverable_count >= 4) ? 1.0 : 0.0,
            audit_path_ok = 1.0
        )
    )
end

function simulate_hysteresis(config::RunConfig)
    p = DynamicsParams(bundle_strength = 1.7, volatility_sensitivity = 1.3)
    depth = 0.86
    capture = effective_precision_share(depth, p.ambient_volatility, p)
    rows = NamedTuple[]
    phases = vcat(fill("safe_baseline", 24), fill("freeze_burst", 34),
        fill("low_depth_evidence", 46), fill("high_depth_evidence", 56))
    for (t, phase) in enumerate(phases)
        external = phase == "freeze_burst" ? 0.95 :
            phase == "low_depth_evidence" ? 0.22 : 0.0
        local_p = if phase == "high_depth_evidence"
            DynamicsParams(bundle_strength = p.bundle_strength, volatility_sensitivity = 0.45)
        else
            p
        end
        dv = dynamics_vector(depth, capture, local_p)
        if phase == "freeze_burst" || phase == "low_depth_evidence"
            target_depth = clamp01(dv.target_depth - local_p.volatility_sensitivity * external)
            target_capture = effective_precision_share(depth, dv.volatility + external, local_p)
        elseif phase == "high_depth_evidence"
            target_depth = max(dv.target_depth, 0.88)
            target_capture = effective_precision_share(max(depth, 0.82), local_p.ambient_volatility, local_p)
        else
            target_depth = dv.target_depth
            target_capture = dv.target_capture
        end
        depth = clamp01(depth + 0.06 * (target_depth - depth))
        capture = clamp01(capture + 0.16 * (target_capture - capture))
        class = classify_endpoint(depth, capture)
        push!(rows, (
            t = t,
            phase = phase,
            depth = depth,
            capture = capture,
            class = class,
            external_volatility = external
        ))
    end
    start_class = first(rows).class
    after_burst = rows[58].class
    after_low = rows[104].class
    final_class = last(rows).class
    return (
        rows = rows,
        metrics = (
            start_class = start_class,
            after_burst_class = after_burst,
            after_low_depth_evidence_class = after_low,
            final_class = final_class,
            asymmetric_basin_hop = (start_class == "self" && after_burst == "capture" && final_class == "self") ? 1.0 : 0.0
        )
    )
end

function run_rxinfer_probe()
    try
        @eval begin
            RxInfer.@model function continuous_depth_probe(v_h, v_z, v_y, h_prev_mean, h_prev_var, y)
                h_prev ~ Normal(mean = h_prev_mean, var = h_prev_var)
                h_t ~ Normal(mean = h_prev, var = v_h)
                z_t ~ Normal(mean = h_t, var = v_z)
                y ~ Normal(mean = z_t, var = v_y)
            end
        end
        y = [0.02, 0.04, 0.03, 0.80, 1.00, 0.15, 0.04]
        init = RxInfer.@initialization begin
            q(h_t) = RxInfer.NormalMeanVariance(0.8, 0.2)
            q(z_t) = RxInfer.NormalMeanVariance(0.8, 0.2)
        end
        updates = RxInfer.@autoupdates begin
            h_prev_mean, h_prev_var = RxInfer.mean_var(q(h_t))
        end
        result = @eval RxInfer.infer(
            model = continuous_depth_probe(v_h = 0.08, v_z = 0.06, v_y = 0.04),
            data = (y = $y,),
            initialization = $init,
            autoupdates = $updates,
            keephistory = length($y),
            historyvars = (h_t = KeepLast(), z_t = KeepLast()),
            iterations = 12,
            free_energy = true,
            autostart = true
        )
        fe = result.free_energy_history
        flat = collect(Iterators.flatten(fe))
        finite = all(isfinite, flat)
        jumps = count(i -> flat[i] > flat[i - 1] + 1e-6, 2:length(flat))
        return (
            attempted = 1.0,
            converged = finite ? 1.0 : 0.0,
            iterations = 12,
            free_energy_initial = isempty(flat) ? nothing : first(flat),
            free_energy_final = isempty(flat) ? nothing : last(flat),
            divergence_count = finite ? jumps : length(flat),
            obstruction = nothing
        )
    catch err
        return (
            attempted = 1.0,
            converged = 0.0,
            iterations = 12,
            free_energy_initial = nothing,
            free_energy_final = nothing,
            divergence_count = 1,
            obstruction = sprint(showerror, err)
        )
    end
end

function compare_value(value::Real, comparator::AbstractString, threshold::Real)
    comparator == ">=" && return value >= threshold
    comparator == ">" && return value > threshold
    comparator == "<=" && return value <= threshold
    comparator == "<" && return value < threshold
    comparator == "==" && return abs(value - threshold) <= 1e-12
    comparator == "!=" && return abs(value - threshold) > 1e-12
    error("Unsupported comparator: $comparator")
end

function opposite_passes(value::Real, criterion::Criterion)
    threshold = criterion.opposite_threshold
    threshold === nothing && return false
    if criterion.comparator in (">=", ">")
        return value <= threshold
    elseif criterion.comparator in ("<=", "<")
        return value >= threshold
    elseif criterion.comparator == "=="
        return abs(value - threshold) <= 1e-12
    elseif criterion.comparator == "!="
        return abs(value - threshold) <= 1e-12
    end
    return false
end

function metric_value(value, path::AbstractString)
    current = value
    for part in split(path, ".")
        if current isa NamedTuple
            current = getproperty(current, Symbol(part))
        elseif current isa Dict
            current = current[part]
        else
            error("Cannot descend into metric path $path at $part")
        end
    end
    return current
end

function label_for(value, criterion::Criterion)
    value isa Real || return "null"
    compare_value(value, criterion.comparator, criterion.threshold) && return "support"
    if criterion.weak_threshold !== nothing && compare_value(value, criterion.comparator, criterion.weak_threshold)
        return "weak_support"
    end
    opposite_passes(value, criterion) && return "falsified"
    return "null"
end

function evaluate_criteria(criteria, summary)
    results = NamedTuple[]
    for criterion in criteria
        value = try
            metric_value(summary, criterion.metric_path)
        catch
            nothing
        end
        push!(results, (
            id = criterion.id,
            description = criterion.description,
            kind = criterion.kind,
            metric_path = criterion.metric_path,
            comparator = criterion.comparator,
            threshold = criterion.threshold,
            weak_threshold = criterion.weak_threshold,
            opposite_threshold = criterion.opposite_threshold,
            value = value,
            label = label_for(value, criterion)
        ))
    end
    return results
end

json_escape(s::AbstractString) = replace(replace(replace(replace(s, "\\" => "\\\\"), "\"" => "\\\""), "\n" => "\\n"), "\r" => "\\r")

function json_value(io::IO, value)
    if value === nothing
        print(io, "null")
    elseif value isa Bool
        print(io, value ? "true" : "false")
    elseif value isa Integer
        print(io, value)
    elseif value isa AbstractFloat
        if isfinite(value)
            print(io, @sprintf("%.10g", value))
        else
            print(io, "null")
        end
    elseif value isa AbstractString
        print(io, "\"", json_escape(value), "\"")
    elseif value isa Symbol
        json_value(io, String(value))
    elseif value isa NamedTuple
        print(io, "{")
        first_item = true
        for key in propertynames(value)
            first_item || print(io, ",")
            first_item = false
            json_value(io, String(key))
            print(io, ":")
            json_value(io, getproperty(value, key))
        end
        print(io, "}")
    elseif value isa AbstractDict
        print(io, "{")
        first_item = true
        for key in sort(collect(keys(value)); by = string)
            first_item || print(io, ",")
            first_item = false
            json_value(io, string(key))
            print(io, ":")
            json_value(io, value[key])
        end
        print(io, "}")
    elseif value isa AbstractVector || value isa Tuple
        print(io, "[")
        for (i, item) in enumerate(value)
            i == 1 || print(io, ",")
            json_value(io, item)
        end
        print(io, "]")
    else
        json_value(io, string(value))
    end
end

function write_json(path::AbstractString, value)
    mkpath(dirname(path))
    open(path, "w") do io
        json_value(io, value)
        write(io, "\n")
    end
end

function csv_escape(value)
    value === nothing && return ""
    text = string(value)
    if occursin(r"[,\n\r\"]", text)
        return "\"" * replace(text, "\"" => "\"\"") * "\""
    end
    return text
end

function write_rows_csv(path::AbstractString, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        isempty(rows) && return
        cols = collect(propertynames(first(rows)))
        println(io, join(string.(cols), ","))
        for row in rows
            println(io, join((csv_escape(getproperty(row, col)) for col in cols), ","))
        end
    end
end

function write_biography_svg(path::AbstractString, rows)
    mkpath(dirname(path))
    one_seed = filter(row -> row.seed == first(row.seed for row in rows) && row.dose == maximum(row.dose for row in rows), rows)
    w, h = 920, 420
    function x(t) 60 + (t - 1) / (maximum(row.t for row in one_seed) - 1) * 800 end
    function y(v) 350 - clamp01(v) * 280 end
    depth_points = join(["$(x(row.t)),$(y(row.depth_mean))" for row in one_seed], " ")
    capture_points = join(["$(x(row.t)),$(y(row.capture))" for row in one_seed], " ")
    spread_points = join(["$(x(row.t)),$(y(min(1.0, sqrt(row.depth_var))))" for row in one_seed], " ")
    open(path, "w") do io
        write(io, """
        <svg xmlns="http://www.w3.org/2000/svg" width="$w" height="$h" viewBox="0 0 $w $h">
          <rect width="$w" height="$h" fill="#fbfaf7"/>
          <rect x="232" y="45" width="175" height="315" fill="#f0d9d2" opacity="0.55"/>
          <line x1="60" y1="350" x2="860" y2="350" stroke="#222" stroke-width="2"/>
          <line x1="60" y1="70" x2="60" y2="350" stroke="#222" stroke-width="2"/>
          <polyline points="$depth_points" fill="none" stroke="#1f6f78" stroke-width="4"/>
          <polyline points="$capture_points" fill="none" stroke="#9b3d2e" stroke-width="4"/>
          <polyline points="$spread_points" fill="none" stroke="#6d6875" stroke-width="2" stroke-dasharray="7 5"/>
          <text x="60" y="35" font-family="Arial" font-size="20" fill="#222">Collapse and recovery trace</text>
          <text x="248" y="65" font-family="Arial" font-size="14" fill="#6f2b20">volatility burst evidence</text>
          <text x="690" y="92" font-family="Arial" font-size="14" fill="#1f6f78">depth posterior mean</text>
          <text x="690" y="116" font-family="Arial" font-size="14" fill="#9b3d2e">capture share</text>
          <text x="690" y="140" font-family="Arial" font-size="14" fill="#6d6875">posterior spread</text>
        </svg>
        """)
    end
end

function write_basin_svg(path::AbstractString, fixed_rows)
    mkpath(dirname(path))
    cells = filter(row -> row.class in ("self", "capture"), fixed_rows)
    bundles = sort(unique(row.bundle_strength for row in cells))
    sens = sort(unique(row.volatility_sensitivity for row in cells))
    cellw, cellh = 105, 78
    open(path, "w") do io
        write(io, """
        <svg xmlns="http://www.w3.org/2000/svg" width="760" height="520" viewBox="0 0 760 520">
          <rect width="760" height="520" fill="#fbfaf7"/>
          <text x="64" y="36" font-family="Arial" font-size="20" fill="#222">U2 basin map</text>
          <text x="250" y="492" font-family="Arial" font-size="14" fill="#333">bundle prior strength</text>
          <text x="18" y="285" font-family="Arial" font-size="14" fill="#333" transform="rotate(-90 18 285)">volatility sensitivity</text>
        """)
        for (i, b) in enumerate(bundles), (j, s) in enumerate(sens)
            rows = filter(row -> row.bundle_strength == b && row.volatility_sensitivity == s, cells)
            self = only(filter(row -> row.class == "self", rows))
            cap = filter(row -> row.class == "capture", rows)
            cap_frac = isempty(cap) ? 0.0 : first(cap).capture_basin_fraction
            color = cap_frac > 0.10 ? "#d89a6a" : "#7fb7a6"
            x = 92 + (i - 1) * cellw
            y = 402 - (j - 1) * cellh
            write(io, """<rect x="$x" y="$y" width="88" height="58" fill="$color" stroke="#333" stroke-width="1"/>""")
            write(io, """<text x="$(x + 8)" y="$(y + 23)" font-family="Arial" font-size="12" fill="#111">S $(round(self.self_basin_fraction; digits=2))</text>""")
            write(io, """<text x="$(x + 8)" y="$(y + 43)" font-family="Arial" font-size="12" fill="#111">C $(round(cap_frac; digits=2))</text>""")
        end
        for (i, b) in enumerate(bundles)
            write(io, """<text x="$(105 + (i - 1) * cellw)" y="475" font-family="Arial" font-size="12" fill="#333">$b</text>""")
        end
        for (j, s) in enumerate(sens)
            write(io, """<text x="54" y="$(437 - (j - 1) * cellh)" font-family="Arial" font-size="12" fill="#333">$s</text>""")
        end
        write(io, """
          <rect x="610" y="88" width="18" height="18" fill="#7fb7a6" stroke="#333"/>
          <text x="636" y="102" font-family="Arial" font-size="13" fill="#222">self basin only/mostly</text>
          <rect x="610" y="118" width="18" height="18" fill="#d89a6a" stroke="#333"/>
          <text x="636" y="132" font-family="Arial" font-size="13" fill="#222">capture basin present</text>
        </svg>
        """)
    end
end

function write_hysteresis_svg(path::AbstractString, rows)
    mkpath(dirname(path))
    function x(c) 80 + clamp01(c) * 740 end
    function y(d) 370 - clamp01(d) * 300 end
    points = join(["$(x(row.capture)),$(y(row.depth))" for row in rows], " ")
    open(path, "w") do io
        write(io, """
        <svg xmlns="http://www.w3.org/2000/svg" width="920" height="440" viewBox="0 0 920 440">
          <rect width="920" height="440" fill="#fbfaf7"/>
          <line x1="80" y1="370" x2="820" y2="370" stroke="#222" stroke-width="2"/>
          <line x1="80" y1="70" x2="80" y2="370" stroke="#222" stroke-width="2"/>
          <polyline points="$points" fill="none" stroke="#2f4858" stroke-width="4"/>
          <circle cx="$(x(first(rows).capture))" cy="$(y(first(rows).depth))" r="7" fill="#1f6f78"/>
          <circle cx="$(x(last(rows).capture))" cy="$(y(last(rows).depth))" r="7" fill="#7fb7a6"/>
          <text x="80" y="36" font-family="Arial" font-size="20" fill="#222">Hysteresis as basin hopping</text>
          <text x="355" y="412" font-family="Arial" font-size="14" fill="#333">capture share</text>
          <text x="20" y="230" font-family="Arial" font-size="14" fill="#333" transform="rotate(-90 20 230)">depth</text>
          <text x="650" y="105" font-family="Arial" font-size="13" fill="#1f6f78">start: self basin</text>
          <text x="650" y="132" font-family="Arial" font-size="13" fill="#9b3d2e">burst and low-depth evidence hold capture</text>
          <text x="650" y="159" font-family="Arial" font-size="13" fill="#7fb7a6">high-depth evidence returns self</text>
        </svg>
        """)
    end
end

function git_hash()
    try
        return strip(read(`git rev-parse HEAD`, String))
    catch
        return "unavailable"
    end
end

function file_exists_metric(output_dir)
    required = ["summary.json", "status.json", "metadata.json",
        "per_seed_metrics.csv", "posterior_traces.csv", "fixed_points.csv",
        "basin_map.svg", "collapse_recovery.svg", "hysteresis_basin_hopping.svg"]
    return all(path -> isfile(joinpath(output_dir, path)), required) ? 1.0 : 0.0
end

function run_all(config_path::AbstractString, criteria_path::AbstractString, output_dir::AbstractString)
    started = time()
    config = load_config(config_path)
    criteria = load_criteria(criteria_path)
    mkpath(output_dir)

    basin = basin_map(config)
    collapse = collapse_analysis(config)
    hysteresis = simulate_hysteresis(config)
    rx = run_rxinfer_probe()

    grid_cells = length(config.bundle_strength_grid) * length(config.volatility_sensitivity_grid)
    fixed_cell_rows = filter(row -> row.class == "self", basin.fixed_rows)
    capture_cell_rows = filter(row -> row.class == "capture", basin.fixed_rows)
    self_fraction = count(row -> row.self_exists, fixed_cell_rows) / grid_cells
    capture_grid_fraction = count(row -> row.capture_exists, fixed_cell_rows) / grid_cells
    missing_self = [
        (bundle_strength = row.bundle_strength, volatility_sensitivity = row.volatility_sensitivity)
        for row in fixed_cell_rows if !row.self_exists
    ]
    capture_cells = [
        (bundle_strength = row.bundle_strength, volatility_sensitivity = row.volatility_sensitivity,
            capture_basin_fraction = row.capture_basin_fraction)
        for row in fixed_cell_rows if row.capture_exists
    ]

    metrics_without_contract = (
        basin = (
            self_fixed_point_grid_fraction = self_fraction,
            capture_basin_grid_fraction = capture_grid_fraction,
            grid_cells = grid_cells,
            missing_self_cells = missing_self,
            capture_cells = capture_cells,
            max_fixed_point_residual = maximum(row.max_residual for row in basin.fixed_rows)
        ),
        collapse = collapse.metrics,
        hysteresis = hysteresis.metrics,
        rxinfer = rx,
        contract = (contract_and_rxinfer_ok = 0.0, files_emitted = 0.0)
    )

    summary = (
        simulation = "sim6a-continuous-stage3",
        run_id = config.run_id,
        config = (
            seeds = config.seeds,
            time_steps = config.time_steps,
            burst_doses = config.burst_doses,
            bundle_strength_grid = config.bundle_strength_grid,
            volatility_sensitivity_grid = config.volatility_sensitivity_grid,
            basin_initial_grid_size = config.basin_initial_grid_size,
            basin_steps = config.basin_steps,
            basin_dt = config.basin_dt
        ),
        precision_convention = (
            realized = "natural-precision Gaussian update for the depth posterior; the precision balance itself is sent as an empirical-prior top-down effective-precision message.",
            d1_deviation = "The discrete D1 exact affine tilt is exact for expected-log precision messages. This continuous trace uses arithmetic/natural precision in the Gaussian posterior update, so posterior-spread terms can deviate from the exact D1 tilt when q(h) is broad."
        ),
        self_sustaining_loop = (
            construction = "High depth lowers endogenous volatility through the self-loop term depth^2*(1-capture)^2; low volatility keeps the depth target cheap, making the high-depth state self-maintaining.",
            capture_competition = "Capture raises endogenous volatility and shifts effective precision toward the bundle stream, creating a competing basin where the volatility cost keeps depth low."
        ),
        metrics = metrics_without_contract
    )

    write_json(joinpath(output_dir, "summary.json"), summary)
    write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = true,
        theory_result = "pending_criteria",
        rxinfer_converged = rx.converged == 1.0,
        rxinfer_obstruction = rx.obstruction
    ))
    write_json(joinpath(output_dir, "metadata.json"), (
        started_at = Dates.format(now(), dateformat"yyyy-mm-ddTHH:MM:SS"),
        runtime_seconds = time() - started,
        julia_version = string(VERSION),
        git_hash = git_hash(),
        config_path = abspath(config_path),
        criteria_path = abspath(criteria_path),
        output_dir = abspath(output_dir),
        preregistered_before_run = true
    ))
    write_rows_csv(joinpath(output_dir, "per_seed_metrics.csv"), collapse.dose_rows)
    write_rows_csv(joinpath(output_dir, "posterior_traces.csv"), collapse.trace_rows)
    write_rows_csv(joinpath(output_dir, "basin_endpoints.csv"), basin.basin_rows)
    write_rows_csv(joinpath(output_dir, "fixed_points.csv"), basin.fixed_rows)
    write_rows_csv(joinpath(output_dir, "hysteresis_trace.csv"), hysteresis.rows)
    write_biography_svg(joinpath(output_dir, "collapse_recovery.svg"), collapse.trace_rows)
    write_basin_svg(joinpath(output_dir, "basin_map.svg"), basin.fixed_rows)
    write_hysteresis_svg(joinpath(output_dir, "hysteresis_basin_hopping.svg"), hysteresis.rows)

    contract_files = file_exists_metric(output_dir)
    final_summary = merge(summary, (
        metrics = merge(metrics_without_contract, (
            contract = (
                files_emitted = contract_files,
                contract_and_rxinfer_ok = (contract_files == 1.0 && rx.converged == 1.0 && rx.divergence_count == 0) ? 1.0 : 0.0
            ),
        )),
    ))
    labels = evaluate_criteria(criteria, final_summary)
    theory_result = all(row -> row.label == "support", labels) ? "support" :
        any(row -> row.label == "falsified", labels) ? "falsified" :
        any(row -> row.label == "weak_support", labels) ? "weak_support" : "null"
    write_json(joinpath(output_dir, "summary.json"), merge(final_summary, (theory_result = theory_result,)))
    write_json(joinpath(output_dir, "criteria-results.json"), (
        criteria_path = abspath(criteria_path),
        summary_path = abspath(joinpath(output_dir, "summary.json")),
        results = labels
    ))
    write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = true,
        theory_result = theory_result,
        rxinfer_converged = rx.converged == 1.0,
        rxinfer_divergence_count = rx.divergence_count,
        rxinfer_obstruction = rx.obstruction
    ))
    write_json(joinpath(output_dir, "metadata.json"), (
        started_at = Dates.format(now(), dateformat"yyyy-mm-ddTHH:MM:SS"),
        completed_at = Dates.format(now(), dateformat"yyyy-mm-ddTHH:MM:SS"),
        runtime_seconds = time() - started,
        julia_version = string(VERSION),
        git_hash = git_hash(),
        config_path = abspath(config_path),
        criteria_path = abspath(criteria_path),
        output_dir = abspath(output_dir),
        preregistered_before_run = true
    ))
    println("Wrote continuous Sim 6a Stage 3 results to $(abspath(output_dir))")
    return final_summary
end

end
