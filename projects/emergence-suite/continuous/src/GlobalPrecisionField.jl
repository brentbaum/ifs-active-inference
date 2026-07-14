module GlobalPrecisionField

using LinearAlgebra
using Printf
using Random
using Statistics

export CHANNELS, PhiConfig, infer_precision_field, run_regime_probe,
    run_witnessing_probe, run_all

const CHANNELS = (:part, :context, :interoception, :relational, :policy)
const N_CHANNELS = length(CHANNELS)

Base.@kwdef struct PhiConfig
    seeds::Vector{Int} = collect(7101:7120)
    prior_variance::Float64 = 0.90
    global_correlation::Float64 = 0.35
    observation_variance::Float64 = 0.08
    unavailable_variance::Float64 = 1.0e6
    profile_learning_rate::Float64 = 0.32
    root_learning_rate::Float64 = 2.20
    sessions::Int = 12
    scaffolded_sessions::Int = 6
end

function covariance_matrix(config::PhiConfig; global_sharing::Bool = true)
    sigma = Matrix{Float64}(I, N_CHANNELS, N_CHANNELS) * config.prior_variance
    if global_sharing
        for i in 1:N_CHANNELS, j in 1:N_CHANNELS
            i == j && continue
            sigma[i, j] = config.global_correlation * config.prior_variance
        end
    end
    return sigma
end

function normalize_availability(available)
    length(available) == N_CHANNELS || error("availability must cover every precision-field channel")
    return Float64.(available .> 0)
end

"""
Infer q(Phi_t) from a context-conditioned hyper-prior and bottom-up errors
about the precision forecast, then broadcast exp(E_q[Phi_t]) to lower layers.

The scalar `depth_index` is computed after inference from posterior confidence,
calibration, and representational breadth. It is never used to produce the
precision field or any lower-level effective precision.
"""
function infer_precision_field(
        profile::AbstractVector{<:Real},
        realized_log_precision::AbstractVector{<:Real};
        observation_variance::Real = PhiConfig().observation_variance,
        available = ones(N_CHANNELS),
        global_sharing::Bool = true,
        broadcast_permutation = collect(1:N_CHANNELS),
        broadcast_signs = ones(N_CHANNELS),
        rng::AbstractRNG = MersenneTwister(1),
        config::PhiConfig = PhiConfig())
    length(profile) == N_CHANNELS || error("profile must cover every precision-field channel")
    length(realized_log_precision) == N_CHANNELS || error("realized field must cover every channel")
    sort(broadcast_permutation) == collect(1:N_CHANNELS) || error("broadcast_permutation must be a permutation")
    length(broadcast_signs) == N_CHANNELS || error("broadcast_signs must cover every channel")
    all(abs.(broadcast_signs) .== 1) || error("broadcast_signs entries must be -1 or 1")

    availability = normalize_availability(available)
    mu_prior = Float64.(profile)
    sigma_prior = covariance_matrix(config; global_sharing = global_sharing)

    y = copy(mu_prior)
    obs_vars = fill(config.unavailable_variance, N_CHANNELS)
    for i in eachindex(y)
        availability[i] == 0.0 && continue
        obs_vars[i] = Float64(observation_variance)
        y[i] = Float64(realized_log_precision[i]) + sqrt(obs_vars[i]) * randn(rng)
    end

    r = Diagonal(obs_vars)
    innovation_covariance = sigma_prior + r
    kalman_gain = sigma_prior / innovation_covariance
    second_order_error = y - mu_prior
    mu_posterior = mu_prior + kalman_gain * second_order_error
    sigma_posterior = Symmetric((Matrix{Float64}(I, N_CHANNELS, N_CHANNELS) - kalman_gain) * sigma_prior)

    broadcast_log_precision = mu_posterior[broadcast_permutation] .* broadcast_signs
    broadcast_precision = exp.(broadcast_log_precision)
    part_dominance = broadcast_precision[1] / (broadcast_precision[1] + broadcast_precision[2])

    active = findall(==(1.0), availability)
    normalized_error = isempty(active) ? 1.0 : mean(abs.(second_order_error[active]) ./ sqrt.(diag(innovation_covariance)[active]))
    residual_error = isempty(active) ? 1.0 : mean(abs.(y[active] - mu_posterior[active]))
    broadcast_error = isempty(active) ? 1.0 : mean(abs.(
        Float64.(realized_log_precision[active]) - broadcast_log_precision[active]))
    posterior_confidence = 1.0 / (1.0 + mean(diag(sigma_posterior)))
    posterior_calibration = exp(-residual_error)
    calibration = exp(-broadcast_error)
    breadth = mean(availability)
    global_integration = global_sharing ? 1.0 : 0.0
    depth_index = clamp(posterior_confidence * calibration * breadth * global_integration, 0.0, 1.0)
    opacity_index = clamp((1.0 / (1.0 + sigma_posterior[1, 1])) * breadth, 0.0, 1.0)
    hyper_prediction_energy = 0.5 * dot(second_order_error, innovation_covariance \ second_order_error)

    return (
        mu_prior = mu_prior,
        observed_log_precision = y,
        second_order_error = second_order_error,
        mu_posterior = mu_posterior,
        sigma_posterior = Matrix(sigma_posterior),
        broadcast_log_precision = broadcast_log_precision,
        broadcast_precision = broadcast_precision,
        part_dominance = part_dominance,
        posterior_confidence = posterior_confidence,
        posterior_calibration = posterior_calibration,
        calibration = calibration,
        breadth = breadth,
        global_integration = global_integration,
        depth_index = depth_index,
        opacity_index = opacity_index,
        normalized_forecast_error = normalized_error,
        hyper_prediction_energy = hyper_prediction_energy,
    )
end

function regime_scenarios()
    return [
        (
            name = "blended_capture",
            realized = [3.00, -0.80, -0.20, -0.70, 1.10],
            available = [1, 0, 0, 0, 1],
            observation_variance = 2.40,
        ),
        (
            name = "known_urgent_threat",
            realized = [2.20, 0.55, 1.15, 1.00, 1.45],
            available = [1, 1, 1, 1, 1],
            observation_variance = 0.025,
        ),
        (
            name = "quiet_narrowing",
            realized = [-2.00, 1.50, -0.80, -0.80, -0.20],
            available = [1, 1, 0, 0, 0],
            observation_variance = 2.40,
        ),
        (
            name = "self_led_witnessing",
            realized = [1.15, 1.55, 1.35, 1.65, 1.25],
            available = [1, 1, 1, 1, 1],
            observation_variance = 0.025,
        ),
    ]
end

function run_regime_probe(; config::PhiConfig = PhiConfig())
    rows = NamedTuple[]
    for (scenario_index, scenario) in enumerate(regime_scenarios()), seed in config.seeds
        result = infer_precision_field(
            zeros(N_CHANNELS), scenario.realized;
            observation_variance = scenario.observation_variance,
            available = scenario.available,
            rng = MersenneTwister(seed + 100 * scenario_index),
            config = config,
        )
        push!(rows, (
            scenario = scenario.name,
            seed = seed,
            part_dominance = result.part_dominance,
            depth_index = result.depth_index,
            opacity_index = result.opacity_index,
            breadth = result.breadth,
            hyper_prediction_energy = result.hyper_prediction_energy,
        ))
    end

    summaries = [(
        scenario = scenario.name,
        mean_part_dominance = mean(row.part_dominance for row in rows if row.scenario == scenario.name),
        mean_depth_index = mean(row.depth_index for row in rows if row.scenario == scenario.name),
        mean_opacity_index = mean(row.opacity_index for row in rows if row.scenario == scenario.name),
    ) for scenario in regime_scenarios()]

    by_name = Dict(row.scenario => row for row in summaries)
    metrics = (
        high_dominance_high_depth = (
            by_name["known_urgent_threat"].mean_part_dominance >= 0.68 &&
            by_name["known_urgent_threat"].mean_depth_index >= 0.75) ? 1.0 : 0.0,
        low_dominance_low_depth = (
            by_name["quiet_narrowing"].mean_part_dominance <= 0.42 &&
            by_name["quiet_narrowing"].mean_depth_index <= 0.40) ? 1.0 : 0.0,
        blended_signature = (
            by_name["blended_capture"].mean_part_dominance >= 0.60 &&
            by_name["blended_capture"].mean_depth_index <= 0.40) ? 1.0 : 0.0,
        self_led_signature = (
            by_name["self_led_witnessing"].mean_part_dominance <= 0.50 &&
            by_name["self_led_witnessing"].mean_depth_index >= 0.75) ? 1.0 : 0.0,
    )
    return (rows = rows, summaries = summaries, metrics = metrics)
end

function arm_definition(arm::String, scaffolded::Bool)
    if arm == "witnessing"
        return (
            realized = scaffolded ? [1.35, 1.45, 1.30, 1.75, 1.20] : [1.35, 1.35, 1.20, 1.15, 1.15],
            available = scaffolded ? [1, 1, 1, 1, 1] : [1, 1, 1, 0, 1],
            observation_variance = scaffolded ? 0.035 : 0.18,
            activation = 1.0,
            evidence_channel = 4,
        )
    elseif arm == "regulation_only"
        return (
            realized = [0.10, 1.55, 1.25, 1.55, 1.00],
            available = [1, 1, 1, 1, 1],
            observation_variance = 0.035,
            activation = 0.12,
            evidence_channel = 4,
        )
    elseif arm == "contact_only"
        return (
            realized = [1.75, -0.45, -0.20, -0.65, 0.80],
            available = [1, 0, 0, 0, 1],
            observation_variance = 1.80,
            activation = 1.0,
            evidence_channel = 4,
        )
    elseif arm == "informational_open"
        return (
            realized = scaffolded ? [1.35, 1.60, 1.25, 1.20, 1.20] : [1.35, 1.45, 1.15, 0.95, 1.15],
            available = scaffolded ? [1, 1, 1, 1, 1] : [1, 1, 1, 0, 1],
            observation_variance = scaffolded ? 0.035 : 0.18,
            activation = 1.0,
            evidence_channel = 2,
        )
    end
    error("unknown arm: $arm")
end

function run_witnessing_arm(seed::Int, arm::String;
        config::PhiConfig = PhiConfig(),
        global_sharing::Bool = true,
        learn_profile::Bool = true,
        broadcast_permutation = collect(1:N_CHANNELS),
        broadcast_signs = ones(N_CHANNELS),
        condition::String = "full")
    rng = MersenneTwister(seed)
    profile = zeros(N_CHANNELS)
    root_log_odds = log(0.90 / 0.10)
    rows = NamedTuple[]

    for session in 1:config.sessions
        scaffolded = session <= config.scaffolded_sessions
        definition = arm_definition(arm, scaffolded)
        result = infer_precision_field(
            profile, definition.realized;
            observation_variance = definition.observation_variance,
            available = definition.available,
            global_sharing = global_sharing,
            broadcast_permutation = broadcast_permutation,
            broadcast_signs = broadcast_signs,
            rng = rng,
            config = config,
        )

        if learn_profile
            profile .+= config.profile_learning_rate .* (result.mu_posterior .- profile)
        end

        evidence_precision = result.broadcast_precision[definition.evidence_channel]
        precision_share = evidence_precision / sum(result.broadcast_precision)
        representation = result.opacity_index * result.posterior_confidence
        revision_weight = definition.activation * representation * precision_share
        root_log_odds -= config.root_learning_rate * revision_weight
        root_belief = 1.0 / (1.0 + exp(-root_log_odds))

        push!(rows, (
            arm = arm,
            condition = condition,
            seed = seed,
            session = session,
            scaffolded = scaffolded ? 1.0 : 0.0,
            part_dominance = result.part_dominance,
            depth_index = result.depth_index,
            opacity_index = result.opacity_index,
            posterior_confidence = result.posterior_confidence,
            root_belief_alone = root_belief,
            revision_weight = revision_weight,
            profile_part = profile[1],
            profile_context = profile[2],
            profile_interoception = profile[3],
            profile_relational = profile[4],
            profile_policy = profile[5],
        ))
    end
    return rows
end

function run_witnessing_probe(; config::PhiConfig = PhiConfig())
    arms = ("witnessing", "regulation_only", "contact_only", "informational_open")
    rows = NamedTuple[]
    for arm in arms, seed in config.seeds
        append!(rows, run_witnessing_arm(seed, arm; config = config))
    end

    ablation_rows = NamedTuple[]
    for seed in config.seeds
        append!(ablation_rows, run_witnessing_arm(seed, "witnessing";
            config = config, learn_profile = false, condition = "no_profile_learning"))
        append!(ablation_rows, run_witnessing_arm(seed, "witnessing";
            config = config, global_sharing = false, condition = "local_only"))
        append!(ablation_rows, run_witnessing_arm(seed, "witnessing";
            config = config, broadcast_signs = -ones(N_CHANNELS), condition = "inverted_broadcast"))
    end

    function final_mean(arm)
        return mean(row.root_belief_alone for row in rows if row.arm == arm && row.session == config.sessions)
    end
    function solo_depth(arm)
        return mean(row.depth_index for row in rows if row.arm == arm && row.session > config.scaffolded_sessions)
    end
    no_learning_solo_depth = mean(row.depth_index for row in ablation_rows
        if row.condition == "no_profile_learning" && row.session > config.scaffolded_sessions)
    local_only_solo_depth = mean(row.depth_index for row in ablation_rows
        if row.condition == "local_only" && row.session > config.scaffolded_sessions)
    inverted_solo_depth = mean(row.depth_index for row in ablation_rows
        if row.condition == "inverted_broadcast" && row.session > config.scaffolded_sessions)
    learned_final_relational_profile = mean(row.profile_relational for row in rows
        if row.arm == "witnessing" && row.session == config.sessions)
    no_learning_final_relational_profile = mean(row.profile_relational for row in ablation_rows
        if row.condition == "no_profile_learning" && row.session == config.sessions)

    summaries = [(
        arm = arm,
        final_root_belief_alone = final_mean(arm),
        mean_unscaffolded_depth = solo_depth(arm),
        mean_final_relational_profile = mean(row.profile_relational for row in rows if row.arm == arm && row.session == config.sessions),
    ) for arm in arms]

    metrics = (
        witnessing_beats_regulation = final_mean("witnessing") + 0.15 <= final_mean("regulation_only") ? 1.0 : 0.0,
        witnessing_beats_contact = final_mean("witnessing") + 0.15 <= final_mean("contact_only") ? 1.0 : 0.0,
        informational_revision_when_open = final_mean("informational_open") <= 0.60 ? 1.0 : 0.0,
        learned_unscaffolded_field = learned_final_relational_profile >= no_learning_final_relational_profile + 1.0 ? 1.0 : 0.0,
        global_sharing_required = solo_depth("witnessing") >= local_only_solo_depth + 0.40 ? 1.0 : 0.0,
        calibrated_broadcast_required = solo_depth("witnessing") >= inverted_solo_depth + 0.20 ? 1.0 : 0.0,
        learned_unscaffolded_depth_gain = solo_depth("witnessing") - no_learning_solo_depth,
        learned_relational_profile_gain = learned_final_relational_profile - no_learning_final_relational_profile,
        local_only_unscaffolded_depth = local_only_solo_depth,
        inverted_unscaffolded_depth = inverted_solo_depth,
    )
    return (rows = rows, ablation_rows = ablation_rows, summaries = summaries, metrics = metrics)
end

function csv_escape(value)
    raw = string(value)
    if occursin(',', raw) || occursin('"', raw) || occursin('\n', raw)
        return "\"" * replace(raw, "\"" => "\"\"") * "\""
    end
    return raw
end

function write_csv(path::AbstractString, rows)
    isempty(rows) && return
    names = propertynames(first(rows))
    open(path, "w") do io
        println(io, join(string.(names), ","))
        for row in rows
            println(io, join((csv_escape(getproperty(row, name)) for name in names), ","))
        end
    end
end

json_escape(value::AbstractString) = replace(value, "\\" => "\\\\", "\"" => "\\\"", "\n" => "\\n")

function json_write(io::IO, value; indent::Int = 0)
    pad = " " ^ indent
    next_pad = " " ^ (indent + 2)
    if value isa NamedTuple
        json_write(io, Dict(string(k) => getproperty(value, k) for k in propertynames(value)); indent = indent)
    elseif value isa AbstractDict
        entries = collect(value)
        print(io, "{")
        if !isempty(entries)
            print(io, "\n")
            for (index, (key, item)) in enumerate(entries)
                print(io, next_pad, "\"", json_escape(string(key)), "\": ")
                json_write(io, item; indent = indent + 2)
                index < length(entries) && print(io, ",")
                print(io, "\n")
            end
            print(io, pad)
        end
        print(io, "}")
    elseif value isa AbstractVector || value isa Tuple
        print(io, "[")
        for (index, item) in enumerate(value)
            index > 1 && print(io, ", ")
            json_write(io, item; indent = indent)
        end
        print(io, "]")
    elseif value isa AbstractString || value isa Symbol
        print(io, "\"", json_escape(string(value)), "\"")
    elseif value isa Bool
        print(io, value ? "true" : "false")
    elseif value === nothing
        print(io, "null")
    elseif value isa Real
        print(io, isfinite(value) ? value : "null")
    else
        print(io, "\"", json_escape(string(value)), "\"")
    end
end

function write_summary(path::AbstractString, regime, witnessing, config::PhiConfig)
    payload = (
        experiment = "v11_global_precision_field",
        definition = (
            epistemic_depth = "recursive global inference over a channel-specific precision field Phi",
            scalar_depth_index = "posterior readout only; absent from all effective-precision equations",
            hyper_loop = ["predict precision field", "weight lower-level errors", "receive error on precision forecast", "update q(Phi)", "broadcast revised Phi"],
            channels = string.(CHANNELS),
        ),
        config = (
            seeds = config.seeds,
            sessions = config.sessions,
            scaffolded_sessions = config.scaffolded_sessions,
            prior_variance = config.prior_variance,
            global_correlation = config.global_correlation,
        ),
        regime_probe = (summaries = regime.summaries, metrics = regime.metrics),
        witnessing_probe = (summaries = witnessing.summaries, metrics = witnessing.metrics),
    )
    open(path, "w") do io
        json_write(io, payload)
        println(io)
    end
end

function write_json(path::AbstractString, payload)
    open(path, "w") do io
        json_write(io, payload)
        println(io)
    end
end

function write_svg(path::AbstractString, rows, config::PhiConfig)
    arms = ["witnessing", "informational_open", "regulation_only", "contact_only"]
    colors = Dict("witnessing" => "#1f6f78", "informational_open" => "#7b6ca8", "regulation_only" => "#c48b35", "contact_only" => "#9b3d2e")
    dashes = Dict("witnessing" => "none", "informational_open" => "9,5", "regulation_only" => "3,4", "contact_only" => "12,4,2,4")
    mean_rows = Dict(arm => [mean(row.root_belief_alone for row in rows if row.arm == arm && row.session == session)
        for session in 1:config.sessions] for arm in arms)
    x(session) = 70 + (session - 1) / (config.sessions - 1) * 710
    y(value) = 350 - value * 280
    open(path, "w") do io
        println(io, "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1060\" height=\"430\" viewBox=\"0 0 1060 430\">")
        println(io, "<rect width=\"1060\" height=\"430\" fill=\"#fbfaf7\"/>")
        println(io, "<text x=\"55\" y=\"35\" font-family=\"Arial\" font-size=\"20\" fill=\"#222\">Identity-root belief across repeated contact</text>")
        println(io, "<line x1=\"70\" y1=\"350\" x2=\"800\" y2=\"350\" stroke=\"#555\"/>")
        println(io, "<line x1=\"70\" y1=\"70\" x2=\"70\" y2=\"350\" stroke=\"#555\"/>")
        println(io, "<text x=\"45\" y=\"76\" font-family=\"Arial\" font-size=\"12\" fill=\"#555\">1.0</text>")
        println(io, "<text x=\"52\" y=\"354\" font-family=\"Arial\" font-size=\"12\" fill=\"#555\">0</text>")
        scaffold_x = x(config.scaffolded_sessions)
        println(io, "<line x1=\"$scaffold_x\" y1=\"70\" x2=\"$scaffold_x\" y2=\"350\" stroke=\"#999\" stroke-dasharray=\"5,5\"/>")
        println(io, "<text x=\"$(scaffold_x + 8)\" y=\"90\" font-family=\"Arial\" font-size=\"12\" fill=\"#666\">scaffold removed</text>")
        for (index, arm) in enumerate(arms)
            for session in 1:(config.sessions - 1)
                println(io, "<line x1=\"$(x(session))\" y1=\"$(y(mean_rows[arm][session]))\" x2=\"$(x(session + 1))\" y2=\"$(y(mean_rows[arm][session + 1]))\" stroke=\"$(colors[arm])\" stroke-width=\"4\" stroke-dasharray=\"$(dashes[arm])\" stroke-linecap=\"round\"/>")
            end
            for session in 1:2:config.sessions
                cx, cy = x(session), y(mean_rows[arm][session])
                if arm == "witnessing"
                    println(io, "<circle cx=\"$cx\" cy=\"$cy\" r=\"4\" fill=\"$(colors[arm])\"/>")
                elseif arm == "informational_open"
                    println(io, "<rect x=\"$(cx - 4)\" y=\"$(cy - 4)\" width=\"8\" height=\"8\" fill=\"$(colors[arm])\"/>")
                elseif arm == "regulation_only"
                    println(io, "<polygon points=\"$cx,$(cy - 5) $(cx - 5),$(cy + 4) $(cx + 5),$(cy + 4)\" fill=\"$(colors[arm])\"/>")
                else
                    println(io, "<polygon points=\"$cx,$(cy - 5) $(cx - 5),$cy $cx,$(cy + 5) $(cx + 5),$cy\" fill=\"$(colors[arm])\"/>")
                end
            end
            legend_y = 88 + 25 * (index - 1)
            println(io, "<line x1=\"815\" y1=\"$legend_y\" x2=\"855\" y2=\"$legend_y\" stroke=\"$(colors[arm])\" stroke-width=\"4\" stroke-dasharray=\"$(dashes[arm])\"/>")
            println(io, "<text x=\"865\" y=\"$(legend_y + 4)\" font-family=\"Arial\" font-size=\"13\" fill=\"$(colors[arm])\">$arm</text>")
        end
        println(io, "<text x=\"370\" y=\"400\" font-family=\"Arial\" font-size=\"14\" fill=\"#333\">session</text>")
        println(io, "<text x=\"20\" y=\"260\" font-family=\"Arial\" font-size=\"14\" fill=\"#333\" transform=\"rotate(-90 20 260)\">P(I am alone with this)</text>")
        println(io, "</svg>")
    end
end

function run_all(output_dir::AbstractString = joinpath(@__DIR__, "..", "results", "global_precision_field");
        config::PhiConfig = PhiConfig())
    mkpath(output_dir)
    regime = run_regime_probe(; config = config)
    witnessing = run_witnessing_probe(; config = config)
    write_csv(joinpath(output_dir, "regime_probe.csv"), regime.rows)
    write_csv(joinpath(output_dir, "witnessing_probe.csv"), witnessing.rows)
    write_csv(joinpath(output_dir, "witnessing_ablations.csv"), witnessing.ablation_rows)
    write_summary(joinpath(output_dir, "summary.json"), regime, witnessing, config)
    criteria = merge(regime.metrics, witnessing.metrics)
    required = (:high_dominance_high_depth, :low_dominance_low_depth,
        :blended_signature, :self_led_signature, :witnessing_beats_regulation,
        :witnessing_beats_contact, :informational_revision_when_open,
        :learned_unscaffolded_field, :global_sharing_required,
        :calibrated_broadcast_required)
    implementation_passed = all(getproperty(criteria, key) == 1.0 for key in required)
    write_json(joinpath(output_dir, "criteria-results.json"), (
        protocol = "post-definition construction check; not preregistered confirmation",
        results = criteria,
    ))
    write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = implementation_passed,
        theory_result = implementation_passed ? "construction_support" : "construction_failure",
        scope = "internal sufficiency of the global precision-field architecture",
    ))
    write_json(joinpath(output_dir, "metadata.json"), (
        seeds = config.seeds,
        source = "projects/emergence-suite/continuous/src/GlobalPrecisionField.jl",
        paper = "projects/ifs-paper/draft-v11-theory.md",
        preregistered = false,
    ))
    write_svg(joinpath(output_dir, "identity_revision.svg"), witnessing.rows, config)
    return (regime = regime, witnessing = witnessing, output_dir = output_dir)
end

end
