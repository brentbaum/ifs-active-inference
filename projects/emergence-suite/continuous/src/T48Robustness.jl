module T48Robustness

using Dates
using Printf
using Random
using Statistics
using Main.ContinuousSim6a

const C = ContinuousSim6a

export T48Config, load_t48_config, mapped_depth_component, make_params,
    driven_trace, collapse_persistence_signature, bifurcation_map, run_t48

Base.@kwdef struct T48Config
    run_id::String = "t48_continuous_robustness_pilot"
    label::String = "pilot"
    seeds::Vector{Int} = [11, 23, 37, 53, 71, 97, 131, 173, 211, 251]
    bundle_strength::Float64 = 1.7
    volatility_sensitivity::Float64 = 1.3
    default_beta::Float64 = 1.05
    default_gamma::Float64 = 1.25
    default_safety_prior_mass::Float64 = 0.60
    safety_prior_gain::Float64 = 1 / 3
    latent_trials::Int = 72
    latent_initial_depth::Float64 = 0.90
    latent_velocity::Float64 = 0.055
    latent_process_noise::Float64 = 0.012
    latent_lower_bound::Float64 = 0.08
    latent_upper_bound::Float64 = 0.92
    latent_load_gain::Float64 = 0.95
    state_substeps_per_observation::Int = 3
    state_dt::Float64 = 0.14
    post_recovery_window::Int = 5
    mapping_names::Vector{String} = ["theory", "flat", "reversed", "nonmonotone"]
    null_mapping_names::Vector{String} = ["flat", "reversed", "nonmonotone"]
    pilot_observation_noise_sd::Float64 = 0.012
    noise_sd_grid::Vector{Float64} = [0.0, 0.012, 0.035, 0.07, 0.14, 0.28]
    beta_grid::Vector{Float64} = [0.35, 0.70, 1.05, 1.40, 1.75]
    gamma_grid::Vector{Float64} = [0.40, 0.825, 1.25, 1.675, 2.10]
    safety_prior_mass_grid::Vector{Float64} = [0.20, 0.40, 0.60, 0.80, 1.00]
    basin_initial_grid_size::Int = 9
    basin_steps::Int = 900
    basin_dt::Float64 = 0.04
    fixed_point_residual_tolerance::Float64 = 0.005
    null_max_signature_seeds::Int = 2
    theory_min_signature_seeds::Int = 8
    decoupled_min_capture_seeds::Int = 8
    noise_survival_min_seeds::Int = 8
end

function string_list(text::AbstractString, key::AbstractString, default)
    m = match(Regex("^$(key):\\s*\\[(.*)\\]", "m"), text)
    m === nothing && return default
    body = strip(m.captures[1])
    isempty(body) && return String[]
    return [strip(replace(part, "\"" => "")) for part in split(body, ",")]
end

function load_t48_config(path::AbstractString)
    text = read(path, String)
    d = T48Config()
    return T48Config(
        run_id = C.parse_scalar(text, "run_id", d.run_id),
        label = C.parse_scalar(text, "label", d.label),
        seeds = C.parse_int_list(text, "seeds", d.seeds),
        bundle_strength = C.parse_scalar(text, "bundle_strength", d.bundle_strength),
        volatility_sensitivity = C.parse_scalar(text, "volatility_sensitivity", d.volatility_sensitivity),
        default_beta = C.parse_scalar(text, "default_beta", d.default_beta),
        default_gamma = C.parse_scalar(text, "default_gamma", d.default_gamma),
        default_safety_prior_mass = C.parse_scalar(text, "default_safety_prior_mass", d.default_safety_prior_mass),
        safety_prior_gain = C.parse_scalar(text, "safety_prior_gain", d.safety_prior_gain),
        latent_trials = C.parse_scalar(text, "latent_trials", d.latent_trials),
        latent_initial_depth = C.parse_scalar(text, "latent_initial_depth", d.latent_initial_depth),
        latent_velocity = C.parse_scalar(text, "latent_velocity", d.latent_velocity),
        latent_process_noise = C.parse_scalar(text, "latent_process_noise", d.latent_process_noise),
        latent_lower_bound = C.parse_scalar(text, "latent_lower_bound", d.latent_lower_bound),
        latent_upper_bound = C.parse_scalar(text, "latent_upper_bound", d.latent_upper_bound),
        latent_load_gain = C.parse_scalar(text, "latent_load_gain", d.latent_load_gain),
        state_substeps_per_observation = C.parse_scalar(text, "state_substeps_per_observation", d.state_substeps_per_observation),
        state_dt = C.parse_scalar(text, "state_dt", d.state_dt),
        post_recovery_window = C.parse_scalar(text, "post_recovery_window", d.post_recovery_window),
        mapping_names = string_list(text, "mapping_names", d.mapping_names),
        null_mapping_names = string_list(text, "null_mapping_names", d.null_mapping_names),
        pilot_observation_noise_sd = C.parse_scalar(text, "pilot_observation_noise_sd", d.pilot_observation_noise_sd),
        noise_sd_grid = C.parse_number_list(text, "noise_sd_grid", d.noise_sd_grid),
        beta_grid = C.parse_number_list(text, "beta_grid", d.beta_grid),
        gamma_grid = C.parse_number_list(text, "gamma_grid", d.gamma_grid),
        safety_prior_mass_grid = C.parse_number_list(text, "safety_prior_mass_grid", d.safety_prior_mass_grid),
        basin_initial_grid_size = C.parse_scalar(text, "basin_initial_grid_size", d.basin_initial_grid_size),
        basin_steps = C.parse_scalar(text, "basin_steps", d.basin_steps),
        basin_dt = C.parse_scalar(text, "basin_dt", d.basin_dt),
        fixed_point_residual_tolerance = C.parse_scalar(text, "fixed_point_residual_tolerance", d.fixed_point_residual_tolerance),
        null_max_signature_seeds = C.parse_scalar(text, "null_max_signature_seeds", d.null_max_signature_seeds),
        theory_min_signature_seeds = C.parse_scalar(text, "theory_min_signature_seeds", d.theory_min_signature_seeds),
        decoupled_min_capture_seeds = C.parse_scalar(text, "decoupled_min_capture_seeds", d.decoupled_min_capture_seeds),
        noise_survival_min_seeds = C.parse_scalar(text, "noise_survival_min_seeds", d.noise_survival_min_seeds),
    )
end

function validate_config(cfg::T48Config)
    length(cfg.seeds) == 10 || error("T4.8 Step A must use exactly 10 pilot seeds")
    all(m -> m in ("theory", "flat", "reversed", "nonmonotone"), cfg.mapping_names) || error("unknown mapping")
    all(m -> m != "theory" && m in cfg.mapping_names, cfg.null_mapping_names) || error("null mappings must be non-theory registered mappings")
    cfg.default_beta in cfg.beta_grid || error("default beta must be an exact grid point")
    cfg.default_gamma in cfg.gamma_grid || error("default gamma must be an exact grid point")
    cfg.default_safety_prior_mass in cfg.safety_prior_mass_grid || error("default safety mass must be an exact grid point")
    cfg.latent_lower_bound < 0.25 < 0.70 < cfg.latent_upper_bound || error("latent bounds must span signature thresholds")
    return cfg
end

function mapped_depth_component(depth::Real, mapping::AbstractString)
    d = clamp(Float64(depth), 0.0, 1.0)
    mapping == "theory" && return (1.0 - d)^2
    mapping == "flat" && return 1.0 / 3.0
    mapping == "reversed" && return d^2
    mapping == "nonmonotone" && return 4.0 * (d - 0.5)^2
    error("unknown volatility mapping: $mapping")
end

function make_params(cfg::T48Config; beta = cfg.default_beta, gamma = cfg.default_gamma,
        safety_mass = cfg.default_safety_prior_mass)
    return C.DynamicsParams(
        bundle_strength = cfg.bundle_strength,
        volatility_sensitivity = cfg.volatility_sensitivity,
        beta_bundle = Float64(beta),
        gamma_evidence = Float64(gamma),
        self_support = cfg.safety_prior_gain * Float64(safety_mass),
    )
end

function robust_dynamics_vector(depth::Real, capture::Real, p::C.DynamicsParams;
        mapping::AbstractString = "theory", external_load::Real = 0.0)
    d = C.clamp01(depth)
    c = C.clamp01(capture)
    raw = p.ambient_volatility + max(0.0, external_load) +
        p.capture_volatility_gain * c^2 +
        p.depth_error_gain * mapped_depth_component(d, mapping) -
        p.self_loop_gain * d^2 * (1.0 - c)^2
    volatility = max(p.volatility_floor, raw)
    self_loop = p.self_loop_gain * (1.0 - c)^2 * d
    target_depth = C.clamp01(1.08 + p.self_support + self_loop - p.depth_cost -
        p.volatility_sensitivity * volatility - 0.55 * c^2)
    target_capture = C.effective_precision_share(d, volatility, p)
    return (
        d_depth = p.depth_rate * (target_depth - d),
        d_capture = p.capture_rate * (target_capture - c),
        target_depth = target_depth,
        target_capture = target_capture,
        volatility = volatility,
    )
end

function integrate_endpoint(depth0::Real, capture0::Real, p::C.DynamicsParams, cfg::T48Config;
        mapping::AbstractString = "theory")
    depth = C.clamp01(depth0)
    capture = C.clamp01(capture0)
    for _ in 1:cfg.basin_steps
        dv = robust_dynamics_vector(depth, capture, p; mapping = mapping)
        depth = C.clamp01(depth + cfg.basin_dt * dv.d_depth)
        capture = C.clamp01(capture + cfg.basin_dt * dv.d_capture)
    end
    dv = robust_dynamics_vector(depth, capture, p; mapping = mapping)
    return (depth = depth, capture = capture,
        residual = hypot(dv.d_depth, dv.d_capture),
        class = C.classify_endpoint(depth, capture))
end

function cell_basin(beta::Float64, gamma::Float64, safety_mass::Float64, cfg::T48Config)
    p = make_params(cfg; beta = beta, gamma = gamma, safety_mass = safety_mass)
    starts = range(0.02, 0.98; length = cfg.basin_initial_grid_size)
    endpoints = [integrate_endpoint(d, c, p, cfg) for d in starts for c in starts]
    converged = filter(row -> row.residual <= cfg.fixed_point_residual_tolerance, endpoints)
    self_n = count(row -> row.class == "self", converged)
    capture_n = count(row -> row.class == "capture", converged)
    return (
        beta = beta,
        gamma = gamma,
        safety_prior_mass = safety_mass,
        bistable = self_n > 0 && capture_n > 0,
        self_basin_fraction = self_n / length(endpoints),
        capture_basin_fraction = capture_n / length(endpoints),
        mixed_or_unconverged_fraction = 1.0 - (self_n + capture_n) / length(endpoints),
        max_residual = maximum(row.residual for row in endpoints),
    )
end

function connected_components(points::Set{NTuple{3, Int}})
    remaining = copy(points)
    components = Vector{Vector{NTuple{3, Int}}}()
    directions = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    while !isempty(remaining)
        seed = first(remaining)
        delete!(remaining, seed)
        queue = [seed]
        component = NTuple{3, Int}[]
        while !isempty(queue)
            point = popfirst!(queue)
            push!(component, point)
            for delta in directions
                neighbor = (point[1] + delta[1], point[2] + delta[2], point[3] + delta[3])
                if neighbor in remaining
                    delete!(remaining, neighbor)
                    push!(queue, neighbor)
                end
            end
        end
        push!(components, component)
    end
    sort!(components; by = length, rev = true)
    return components
end

function bifurcation_map(cfg::T48Config)
    rows = [cell_basin(Float64(beta), Float64(gamma), Float64(safety), cfg)
        for safety in cfg.safety_prior_mass_grid for gamma in cfg.gamma_grid for beta in cfg.beta_grid]
    points = Set{NTuple{3, Int}}()
    for (k, safety) in enumerate(cfg.safety_prior_mass_grid),
            (j, gamma) in enumerate(cfg.gamma_grid), (i, beta) in enumerate(cfg.beta_grid)
        row = only(filter(r -> r.beta == beta && r.gamma == gamma && r.safety_prior_mass == safety, rows))
        row.bistable && push!(points, (i, j, k))
    end
    components = connected_components(points)
    largest = isempty(components) ? NTuple{3, Int}[] : first(components)
    default_index = (
        only(findall(==(cfg.default_beta), cfg.beta_grid)),
        only(findall(==(cfg.default_gamma), cfg.gamma_grid)),
        only(findall(==(cfg.default_safety_prior_mass), cfg.safety_prior_mass_grid)),
    )
    default_bistable = default_index in points
    default_in_largest = default_index in Set(largest)
    by_safety = [(
        safety_prior_mass = Float64(safety),
        bistable_cells = count(row -> row.safety_prior_mass == safety && row.bistable, rows),
        slice_cells = length(cfg.beta_grid) * length(cfg.gamma_grid),
    ) for safety in cfg.safety_prior_mass_grid]
    largest_rows = [rows[(point[3] - 1) * length(cfg.beta_grid) * length(cfg.gamma_grid) +
        (point[2] - 1) * length(cfg.beta_grid) + point[1]] for point in largest]
    shape = isempty(largest_rows) ? (
        beta_min = nothing, beta_max = nothing, gamma_min = nothing, gamma_max = nothing,
        safety_min = nothing, safety_max = nothing,
    ) : (
        beta_min = minimum(row.beta for row in largest_rows),
        beta_max = maximum(row.beta for row in largest_rows),
        gamma_min = minimum(row.gamma for row in largest_rows),
        gamma_max = maximum(row.gamma for row in largest_rows),
        safety_min = minimum(row.safety_prior_mass for row in largest_rows),
        safety_max = maximum(row.safety_prior_mass for row in largest_rows),
    )
    total = length(rows)
    metrics = (
        total_grid_cells = total,
        bistable_cell_count = length(points),
        volume_fraction = length(points) / total,
        connected_component_count = length(components),
        largest_component_cell_count = length(largest),
        largest_component_volume_fraction = length(largest) / total,
        default_bistable = default_bistable ? 1.0 : 0.0,
        default_in_largest_component = default_in_largest ? 1.0 : 0.0,
        connected_default_inside = (!isempty(largest) && default_in_largest) ? 1.0 : 0.0,
        by_safety = by_safety,
        largest_component_shape = shape,
    )
    return (rows = rows, metrics = metrics)
end

function latent_depth_path(seed::Int, cfg::T48Config)
    rng = MersenneTwister(seed + 61_000)
    depth = cfg.latent_initial_depth
    velocity = -cfg.latent_velocity * (0.90 + 0.20 * rand(rng))
    path = Float64[]
    for trial in 1:cfg.latent_trials
        if trial > 1
            candidate = depth + velocity + cfg.latent_process_noise * randn(rng)
            if candidate <= cfg.latent_lower_bound
                candidate = cfg.latent_lower_bound + (cfg.latent_lower_bound - candidate)
                velocity = abs(velocity)
            elseif candidate >= cfg.latent_upper_bound
                candidate = cfg.latent_upper_bound - (candidate - cfg.latent_upper_bound)
                velocity = -abs(velocity)
            end
            depth = clamp(candidate, cfg.latent_lower_bound, cfg.latent_upper_bound)
        end
        push!(path, depth)
    end
    return path
end

function driven_trace(seed::Int, mapping::AbstractString, noise_sd::Float64, cfg::T48Config;
        initial_depth::Float64 = 0.86, initial_capture::Union{Nothing, Float64} = nothing)
    p = make_params(cfg)
    depth = initial_depth
    capture = initial_capture === nothing ? C.effective_precision_share(depth, p.ambient_volatility, p) : initial_capture
    latent_path = latent_depth_path(seed, cfg)
    observation_rng = MersenneTwister(seed + 63_000)
    rows = NamedTuple[]
    for (trial, latent_depth) in enumerate(latent_path)
        noiseless_load = cfg.latent_load_gain * mapped_depth_component(latent_depth, mapping)
        observed_load = max(0.0, noiseless_load + noise_sd * randn(observation_rng))
        for _ in 1:cfg.state_substeps_per_observation
            dv = robust_dynamics_vector(depth, capture, p; mapping = "theory", external_load = observed_load)
            depth = C.clamp01(depth + cfg.state_dt * dv.d_depth)
            capture = C.clamp01(capture + cfg.state_dt * dv.d_capture)
        end
        push!(rows, (
            mapping = mapping,
            seed = seed,
            trial = trial,
            true_depth = latent_depth,
            noiseless_external_load = noiseless_load,
            observed_external_load = observed_load,
            state_depth = depth,
            capture = capture,
            class = C.classify_endpoint(depth, capture),
        ))
    end
    return rows
end

function collapse_persistence_signature(rows, cfg::T48Config)
    first_low = findfirst(row -> row.true_depth <= 0.25, rows)
    first_low === nothing && return (signature = 0.0, structurally_evaluable = 0.0,
        baseline_self = 0.0, captured_during_low = 0.0, persistent_after_recovery = 0.0,
        first_low_trial = nothing, first_recovery_trial = nothing, first_capture_trial = nothing,
        first_state_recovery_trial = nothing, collapse_load = nothing, state_recovery_load = nothing,
        hysteresis_load_width = nothing)
    first_recovery = findfirst(i -> i > first_low && rows[i].true_depth >= 0.70, eachindex(rows))
    first_recovery === nothing && return (signature = 0.0, structurally_evaluable = 0.0,
        baseline_self = 0.0, captured_during_low = 0.0, persistent_after_recovery = 0.0,
        first_low_trial = first_low, first_recovery_trial = nothing, first_capture_trial = nothing,
        first_state_recovery_trial = nothing, collapse_load = nothing, state_recovery_load = nothing,
        hysteresis_load_width = nothing)
    baseline_start = max(1, first_low - 3)
    baseline_self = all(rows[i].class == "self" for i in baseline_start:(first_low - 1))
    capture_index = findfirst(i -> rows[i].class == "capture", first_low:(first_recovery - 1))
    first_capture = capture_index === nothing ? nothing : first_low + capture_index - 1
    window_stop = min(length(rows), first_recovery + cfg.post_recovery_window - 1)
    recovery_window = first_recovery:window_stop
    persistent = count(i -> rows[i].class == "capture", recovery_window) >=
        min(4, length(recovery_window))
    state_recovery = findfirst(i -> i >= first_recovery && rows[i].class == "self", eachindex(rows))
    collapse_load = first_capture === nothing ? nothing : rows[first_capture].observed_external_load
    recovery_load = state_recovery === nothing ? nothing : rows[state_recovery].observed_external_load
    width = collapse_load === nothing || recovery_load === nothing ? nothing : collapse_load - recovery_load
    signature = baseline_self && first_capture !== nothing && persistent
    return (
        signature = signature ? 1.0 : 0.0,
        structurally_evaluable = 1.0,
        baseline_self = baseline_self ? 1.0 : 0.0,
        captured_during_low = first_capture === nothing ? 0.0 : 1.0,
        persistent_after_recovery = persistent ? 1.0 : 0.0,
        first_low_trial = first_low,
        first_recovery_trial = first_recovery,
        first_capture_trial = first_capture,
        first_state_recovery_trial = state_recovery,
        collapse_load = collapse_load,
        state_recovery_load = recovery_load,
        hysteresis_load_width = width,
    )
end

function mapping_analysis(cfg::T48Config)
    rows = NamedTuple[]
    traces = NamedTuple[]
    counts = Dict{String, Int}()
    for mapping in cfg.mapping_names
        mapping_rows = NamedTuple[]
        for seed in cfg.seeds
            trace = driven_trace(seed, mapping, cfg.pilot_observation_noise_sd, cfg)
            append!(traces, trace)
            result = merge((mapping = mapping, seed = seed), collapse_persistence_signature(trace, cfg))
            push!(mapping_rows, result)
        end
        append!(rows, mapping_rows)
        counts[mapping] = count(row -> row.signature == 1.0, mapping_rows)
    end
    null_counts = [counts[mapping] for mapping in cfg.null_mapping_names]
    theory_count = counts["theory"]
    max_null = maximum(null_counts)
    specificity = theory_count >= cfg.theory_min_signature_seeds && max_null <= cfg.null_max_signature_seeds
    return (rows = rows, traces = traces, counts = counts, metrics = (
        theory_signature_seed_count = theory_count,
        flat_signature_seed_count = get(counts, "flat", 0),
        reversed_signature_seed_count = get(counts, "reversed", 0),
        nonmonotone_signature_seed_count = get(counts, "nonmonotone", 0),
        max_null_signature_seed_count = max_null,
        specificity_pass = specificity ? 1.0 : 0.0,
    ))
end

function driven_basin_maps(cfg::T48Config)
    starts = range(0.02, 0.98; length = cfg.basin_initial_grid_size)
    p = make_params(cfg)
    rows = NamedTuple[]
    for mapping in cfg.mapping_names, d0 in starts, c0 in starts
        classes = String[]
        signatures = Float64[]
        for seed in cfg.seeds
            trace = driven_trace(seed, mapping, cfg.pilot_observation_noise_sd, cfg;
                initial_depth = Float64(d0), initial_capture = Float64(c0))
            result = collapse_persistence_signature(trace, cfg)
            recovery_trial = result.first_recovery_trial
            if recovery_trial === nothing
                push!(classes, "mixed")
            else
                endpoint_trial = min(length(trace), recovery_trial + cfg.post_recovery_window - 1)
                push!(classes, trace[endpoint_trial].class)
            end
            push!(signatures, result.signature)
        end
        push!(rows, (
            mapping = mapping,
            initial_depth = Float64(d0),
            initial_capture = Float64(c0),
            post_recovery_self_fraction = count(==("self"), classes) / length(classes),
            post_recovery_capture_fraction = count(==("capture"), classes) / length(classes),
            post_recovery_mixed_fraction = count(==("mixed"), classes) / length(classes),
            complete_signature_fraction = mean(signatures),
        ))
    end
    return rows
end

function noise_analysis(cfg::T48Config)
    rows = NamedTuple[]
    aggregate = NamedTuple[]
    death_sd = nothing
    for noise_sd in cfg.noise_sd_grid
        local_rows = NamedTuple[]
        for seed in cfg.seeds
            trace = driven_trace(seed, "theory", Float64(noise_sd), cfg)
            push!(local_rows, merge((noise_sd = Float64(noise_sd), seed = seed),
                collapse_persistence_signature(trace, cfg)))
        end
        append!(rows, local_rows)
        signature_count = count(row -> row.signature == 1.0, local_rows)
        push!(aggregate, (
            noise_sd = Float64(noise_sd),
            signature_seed_count = signature_count,
            seed_count = length(cfg.seeds),
            survives = signature_count >= cfg.noise_survival_min_seeds,
        ))
        if death_sd === nothing && signature_count < cfg.noise_survival_min_seeds
            death_sd = Float64(noise_sd)
        end
    end
    return (rows = rows, aggregate = aggregate, metrics = (
        hysteresis_death_noise_sd = death_sd,
        death_observed_in_sweep = death_sd === nothing ? 0.0 : 1.0,
        maximum_tested_noise_sd = maximum(cfg.noise_sd_grid),
    ))
end

function write_mapping_basin_svg(path::AbstractString, rows, mapping::String)
    selected = filter(row -> row.mapping == mapping, rows)
    starts_d = sort(unique(row.initial_depth for row in selected))
    starts_c = sort(unique(row.initial_capture for row in selected))
    cell = 42
    width = 130 + cell * length(starts_c)
    height = 110 + cell * length(starts_d)
    open(path, "w") do io
        write(io, """<svg xmlns="http://www.w3.org/2000/svg" width="$width" height="$height" viewBox="0 0 $width $height">
        <rect width="$width" height="$height" fill="#fbfaf7"/>
        <text x="58" y="28" font-family="Arial" font-size="18">Driven basin map: $mapping</text>
        <text x="$(width ÷ 2 - 30)" y="$(height - 12)" font-family="Arial" font-size="12">initial capture</text>
        <text x="15" y="$(height ÷ 2 + 25)" font-family="Arial" font-size="12" transform="rotate(-90 15 $(height ÷ 2 + 25))">initial depth</text>
        """)
        for (i, c0) in enumerate(starts_c), (j, d0) in enumerate(starts_d)
            row = only(filter(r -> r.initial_capture == c0 && r.initial_depth == d0, selected))
            frac = row.post_recovery_capture_fraction
            red = round(Int, 245 - 55 * frac)
            green = round(Int, 242 - 125 * frac)
            blue = round(Int, 235 - 145 * frac)
            x = 55 + (i - 1) * cell
            y = 42 + (length(starts_d) - j) * cell
            write(io, """<rect x="$x" y="$y" width="38" height="38" fill="rgb($red,$green,$blue)" stroke="#555"/>
            <text x="$(x + 9)" y="$(y + 24)" font-family="Arial" font-size="11">$(round(frac; digits=1))</text>""")
        end
        write(io, "</svg>\n")
    end
end

function write_bifurcation_svg(path::AbstractString, rows, cfg::T48Config)
    panel_w, panel_h = 205, 220
    width = panel_w * length(cfg.safety_prior_mass_grid)
    height = panel_h + 45
    cell = 32
    open(path, "w") do io
        write(io, """<svg xmlns="http://www.w3.org/2000/svg" width="$width" height="$height" viewBox="0 0 $width $height">
        <rect width="$width" height="$height" fill="#fbfaf7"/>
        <text x="22" y="25" font-family="Arial" font-size="18">Bistability in beta x gamma x safety-prior mass</text>
        """)
        for (k, safety) in enumerate(cfg.safety_prior_mass_grid)
            x0 = (k - 1) * panel_w + 34
            y0 = 58
            write(io, """<text x="$x0" y="48" font-family="Arial" font-size="13">safety=$(safety)</text>""")
            for (i, beta) in enumerate(cfg.beta_grid), (j, gamma) in enumerate(cfg.gamma_grid)
                row = only(filter(r -> r.beta == beta && r.gamma == gamma && r.safety_prior_mass == safety, rows))
                color = row.bistable ? "#c96f4a" : "#d9e6e1"
                x = x0 + (i - 1) * cell
                y = y0 + (length(cfg.gamma_grid) - j) * cell
                write(io, """<rect x="$x" y="$y" width="29" height="29" fill="$color" stroke="#555"/>""")
                if beta == cfg.default_beta && gamma == cfg.default_gamma && safety == cfg.default_safety_prior_mass
                    write(io, """<text x="$(x + 8)" y="$(y + 21)" font-family="Arial" font-size="20" fill="#111">★</text>""")
                end
            end
        end
        write(io, """<rect x="22" y="$(height - 27)" width="15" height="15" fill="#c96f4a"/><text x="43" y="$(height - 15)" font-family="Arial" font-size="12">bistable; star = historical default</text></svg>\n""")
    end
end

function criteria_theory_result(labels)
    all(row -> row.label == "support", labels) && return "support"
    any(row -> row.label == "falsified", labels) && return "falsified"
    any(row -> row.label == "weak_support", labels) && return "weak_support"
    return "null"
end

function run_t48(config_path::AbstractString, criteria_path::AbstractString, output_dir::AbstractString)
    started = time()
    started_at = Dates.format(now(), dateformat"yyyy-mm-ddTHH:MM:SS")
    cfg = validate_config(load_t48_config(config_path))
    criteria = C.load_criteria(criteria_path)
    mkpath(output_dir)

    mappings = mapping_analysis(cfg)
    driven_basins = driven_basin_maps(cfg)
    bifurcation = bifurcation_map(cfg)
    noise = noise_analysis(cfg)

    summary = (
        simulation = "sim6a-continuous-t48",
        analysis = "T4.8 Step A pilot",
        run_id = cfg.run_id,
        label = cfg.label,
        config = (
            seeds = cfg.seeds,
            mapping_names = cfg.mapping_names,
            historical_default = (
                bundle_strength = cfg.bundle_strength,
                volatility_sensitivity = cfg.volatility_sensitivity,
                beta = cfg.default_beta,
                gamma = cfg.default_gamma,
                safety_prior_mass = cfg.default_safety_prior_mass,
            ),
            beta_grid = cfg.beta_grid,
            gamma_grid = cfg.gamma_grid,
            safety_prior_mass_grid = cfg.safety_prior_mass_grid,
            noise_sd_grid = cfg.noise_sd_grid,
        ),
        model_contract = (
            nulls = "null-generated continuous volatility loads are evaluated by frozen theory-response dynamics",
            latent_drive = "autonomous reflected stochastic latent depth; no biography phase or state feedback enters the latent process",
            signature = "Self baseline AND capture during first low-depth excursion AND capture in at least 4/5 states after autonomous latent recovery",
            bifurcation = "two classified converged attractors from the same autonomous theory dynamics; 6-neighbor connectivity in beta x gamma x safety mass",
            safety_mapping = "continuous self_support = safety_prior_mass / 3; mass 0.60 exactly preserves historical self_support 0.20",
        ),
        metrics = (
            nulls = mappings.metrics,
            bifurcation = bifurcation.metrics,
            decoupled = (
                signature_seed_count = mappings.metrics.theory_signature_seed_count,
                evaluable_seed_count = count(row -> row.mapping == "theory" && row.structurally_evaluable == 1.0, mappings.rows),
                seed_count = length(cfg.seeds),
            ),
            noise = noise.metrics,
        ),
    )

    C.write_rows_csv(joinpath(output_dir, "null_mapping_metrics.csv"), mappings.rows)
    C.write_rows_csv(joinpath(output_dir, "decoupled_traces.csv"), filter(row -> row.mapping == "theory", mappings.traces))
    C.write_rows_csv(joinpath(output_dir, "driven_basin_map.csv"), driven_basins)
    C.write_rows_csv(joinpath(output_dir, "bifurcation_map.csv"), bifurcation.rows)
    C.write_rows_csv(joinpath(output_dir, "noise_robustness_per_seed.csv"), noise.rows)
    C.write_rows_csv(joinpath(output_dir, "noise_robustness.csv"), noise.aggregate)
    for mapping in cfg.mapping_names
        write_mapping_basin_svg(joinpath(output_dir, "basin_map_$(mapping).svg"), driven_basins, mapping)
    end
    write_bifurcation_svg(joinpath(output_dir, "bifurcation_map.svg"), bifurcation.rows, cfg)

    labels = C.evaluate_criteria(criteria, summary)
    theory_result = criteria_theory_result(labels)
    required = ["summary.json", "status.json", "metadata.json", "criteria-results.json",
        "null_mapping_metrics.csv", "decoupled_traces.csv", "driven_basin_map.csv",
        "bifurcation_map.csv", "bifurcation_map.svg", "noise_robustness.csv"]
    C.write_json(joinpath(output_dir, "summary.json"), merge(summary, (theory_result = theory_result,)))
    C.write_json(joinpath(output_dir, "criteria-results.json"), (
        criteria_path = abspath(criteria_path),
        summary_path = abspath(joinpath(output_dir, "summary.json")),
        results = labels,
    ))
    C.write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = true,
        pilot_only = true,
        theory_result = theory_result,
        confirmatory_seeds_run = false,
    ))
    C.write_json(joinpath(output_dir, "metadata.json"), (
        started_at = started_at,
        completed_at = Dates.format(now(), dateformat"yyyy-mm-ddTHH:MM:SS"),
        runtime_seconds = time() - started,
        julia_version = string(VERSION),
        git_hash = C.git_hash(),
        config_path = abspath(config_path),
        criteria_path = abspath(criteria_path),
        output_dir = abspath(output_dir),
        preregistered_before_run = true,
        pilot_seed_count = length(cfg.seeds),
    ))
    missing = filter(name -> !isfile(joinpath(output_dir, name)), required)
    isempty(missing) || error("missing run-contract files: $(join(missing, ", "))")
    println("Wrote T4.8 continuous Step A pilot to $(abspath(output_dir))")
    return merge(summary, (theory_result = theory_result, criteria = labels))
end

end
