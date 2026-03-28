Base.@kwdef struct Sim3Config
    seeds::Vector{Int} = copy(DEFAULT_SEEDS)
    T::Int = 300
    rho::Float64 = 0.95
    kappa::Float64 = -1.0
    omega::Float64 = 0.0
    v_z::Float64 = 0.20
    base_v_h::Float64 = 0.10
    base_v_y::Float64 = 0.10
    kalman_process_var::Float64 = 1.0
    vmp_iters::Int = 10
    init_var::Float64 = 5.0
    alpha_local_values::Vector{Float64} = [0.25, 0.5, 1.0, 2.0, 4.0]
    alpha_hyper_values::Vector{Float64} = [0.25, 0.5, 1.0, 2.0, 4.0]
    input_scale_values::Vector{Float64} = [0.1, 1.0, 2.0]
    scale_y_by_local::Bool = false
end

default_sim3_config() = Sim3Config()

function load_sim3_config(path::AbstractString)
    defaults = default_sim3_config()
    raw = YAML.load_file(path)
    return Sim3Config(
        seeds = haskey(raw, "seeds") ? Int.(raw["seeds"]) : defaults.seeds,
        T = get(raw, "T", defaults.T),
        rho = get(raw, "rho", defaults.rho),
        kappa = get(raw, "kappa", defaults.kappa),
        omega = get(raw, "omega", defaults.omega),
        v_z = get(raw, "v_z", defaults.v_z),
        base_v_h = get(raw, "base_v_h", defaults.base_v_h),
        base_v_y = get(raw, "base_v_y", defaults.base_v_y),
        kalman_process_var = get(raw, "kalman_process_var", defaults.kalman_process_var),
        vmp_iters = get(raw, "vmp_iters", defaults.vmp_iters),
        init_var = get(raw, "init_var", defaults.init_var),
        alpha_local_values = haskey(raw, "alpha_local_values") ? Float64.(raw["alpha_local_values"]) : defaults.alpha_local_values,
        alpha_hyper_values = haskey(raw, "alpha_hyper_values") ? Float64.(raw["alpha_hyper_values"]) : defaults.alpha_hyper_values,
        input_scale_values = haskey(raw, "input_scale_values") ? Float64.(raw["input_scale_values"]) : defaults.input_scale_values,
        scale_y_by_local = get(raw, "scale_y_by_local", defaults.scale_y_by_local)
    )
end

function sim3_input_drive(
    rng::AbstractRNG,
    T::Int,
    input_scale::Float64;
    mode::Symbol = :sine,
    conflict_offset::Float64 = 0.0,
    conflict_onset::Int = max(2, cld(T, 4))
)
    noise_scale = max(0.05, 0.25 * max(input_scale, abs(conflict_offset)))
    if mode == :sine
        return [
            input_scale * sin(2π * t / 30) + noise_scale * randn(rng)
            for t in 1:T
        ]
    elseif mode == :counterevidence
        onset = clamp(conflict_onset, 2, T)
        drive = zeros(Float64, T)
        for t in 1:T
            base = t < onset ? 0.25 * input_scale : -abs(conflict_offset)
            drive[t] = base + noise_scale * randn(rng)
        end
        return drive
    else
        error("Unknown sim3 input mode: $(mode)")
    end
end

function generate_sim3_sequence(
    rng::AbstractRNG,
    config::Sim3Config;
    alpha_local::Float64,
    alpha_hyper::Float64,
    input_scale::Float64,
    biased_priors::Bool = false,
    input_mode::Symbol = :sine,
    conflict_offset::Float64 = input_scale,
    conflict_onset::Int = max(2, cld(config.T, 4)),
    observation_bias::Float64 = 0.0,
    observation_bias_onset::Int = 1,
    prior_bias_sign::Float64 = 1.0,
    h_prior_bias_sigma::Float64 = 6.0,
    x_prior_bias_sigma::Float64 = 6.0,
    prior_var_shrink::Float64 = 25.0
)
    T = config.T
    h = zeros(Float64, T)
    z = zeros(Float64, T)
    x = zeros(Float64, T)
    y = zeros(Float64, T)
    u = sim3_input_drive(rng, T, input_scale; mode = input_mode, conflict_offset = conflict_offset, conflict_onset = conflict_onset)

    v_h = config.base_v_h / alpha_hyper
    v_y = config.scale_y_by_local ? config.base_v_y / alpha_local : config.base_v_y
    h0 = log(alpha_local)

    h_prev = h0
    x_prev = 0.0
    for t in 1:T
        h[t] = rand(rng, Normal(h_prev, sqrt(v_h)))
        z[t] = rand(rng, Normal(h[t], sqrt(config.v_z)))
        local_var = exp(config.kappa * z[t] + config.omega)
        x[t] = rand(rng, Normal(config.rho * x_prev + u[t], sqrt(local_var)))
        bias_t = t >= observation_bias_onset ? observation_bias : 0.0
        y[t] = rand(rng, Normal(x[t] + bias_t, sqrt(v_y)))
        h_prev = h[t]
        x_prev = x[t]
    end

    h_prior_mean = biased_priors ? h0 + prior_bias_sign * h_prior_bias_sigma * sqrt(v_h) : h0
    h_prior_var = biased_priors ? max(v_h / prior_var_shrink, 1e-4) : config.init_var
    x_prior_mean = biased_priors ? prior_bias_sign * x_prior_bias_sigma * sqrt(var(x) + 1e-6) : 0.0
    x_prior_var = biased_priors ? max(var(x) / prior_var_shrink, 1e-4) : config.init_var

    return (
        h = h,
        z = z,
        x = x,
        y = y,
        u = u,
        params = (
            alpha_local = alpha_local,
            alpha_hyper = alpha_hyper,
            input_scale = input_scale,
            input_mode = String(input_mode),
            conflict_offset = conflict_offset,
            conflict_onset = conflict_onset,
            observation_bias = observation_bias,
            observation_bias_onset = observation_bias_onset,
            v_h = v_h,
            v_y = v_y,
            biased_priors = biased_priors,
            prior_bias_sign = prior_bias_sign,
            h_prior_bias_sigma = h_prior_bias_sigma,
            x_prior_bias_sigma = x_prior_bias_sigma,
            prior_var_shrink = prior_var_shrink,
            h_prior_mean = h_prior_mean,
            h_prior_var = h_prior_var,
            x_prior_mean = x_prior_mean,
            x_prior_var = x_prior_var
        )
    )
end
