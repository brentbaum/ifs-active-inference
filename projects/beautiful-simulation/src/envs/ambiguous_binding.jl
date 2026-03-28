const BIND = 1
const FRAG = 2

Base.@kwdef struct Sim2Config
    seeds::Vector{Int} = copy(DEFAULT_SEEDS)
    n_episodes::Int = 20
    T::Int = 200
    g_diag::Float64 = 0.97
    g_offdiag::Float64 = 0.03
    g_diag_bind::Float64 = 0.97
    g_diag_frag::Float64 = 0.999
    phi_diag::Float64 = 0.95
    phi_offdiag::Float64 = 0.05
    rho_bind::Float64 = 0.995
    rho_frag::Float64 = 0.35
    rho_fixed::Float64 = 0.45
    r_obs_bind::Float64 = 0.68
    r_obs_frag::Float64 = 0.97
    unambiguous_noise::Float64 = 0.05
    ambiguity_noise::Float64 = 0.10
    bias_g_prior::Float64 = 0.90
    bias_phi_bind_prior::Float64 = 0.85
    ambiguity_reveal_interval::Int = 24
    ambiguity_reveal_len::Int = 4
    ambiguity_frag_flip_len::Int = 8
end

default_sim2_config() = Sim2Config()

function load_sim2_config(path::AbstractString)
    defaults = default_sim2_config()
    raw = YAML.load_file(path)
    return Sim2Config(
        seeds = haskey(raw, "seeds") ? Int.(raw["seeds"]) : defaults.seeds,
        n_episodes = get(raw, "n_episodes", defaults.n_episodes),
        T = get(raw, "T", defaults.T),
        g_diag = get(raw, "g_diag", defaults.g_diag),
        g_offdiag = get(raw, "g_offdiag", defaults.g_offdiag),
        g_diag_bind = get(raw, "g_diag_bind", defaults.g_diag_bind),
        g_diag_frag = get(raw, "g_diag_frag", defaults.g_diag_frag),
        phi_diag = get(raw, "phi_diag", defaults.phi_diag),
        phi_offdiag = get(raw, "phi_offdiag", defaults.phi_offdiag),
        rho_bind = get(raw, "rho_bind", defaults.rho_bind),
        rho_frag = get(raw, "rho_frag", defaults.rho_frag),
        rho_fixed = get(raw, "rho_fixed", defaults.rho_fixed),
        r_obs_bind = get(raw, "r_obs_bind", defaults.r_obs_bind),
        r_obs_frag = get(raw, "r_obs_frag", defaults.r_obs_frag),
        unambiguous_noise = get(raw, "unambiguous_noise", defaults.unambiguous_noise),
        ambiguity_noise = get(raw, "ambiguity_noise", defaults.ambiguity_noise),
        bias_g_prior = get(raw, "bias_g_prior", defaults.bias_g_prior),
        bias_phi_bind_prior = get(raw, "bias_phi_bind_prior", defaults.bias_phi_bind_prior),
        ambiguity_reveal_interval = get(raw, "ambiguity_reveal_interval", defaults.ambiguity_reveal_interval),
        ambiguity_reveal_len = get(raw, "ambiguity_reveal_len", defaults.ambiguity_reveal_len),
        ambiguity_frag_flip_len = get(raw, "ambiguity_frag_flip_len", defaults.ambiguity_frag_flip_len)
    )
end

binary_emission(r::Float64, latent::Int) = latent == 1 ? [r, 1.0 - r] : [1.0 - r, r]

function sample_match_state(rng::AbstractRNG, g::Int, rho::Float64)
    return rand(rng) < rho ? g : 3 - g
end

function sample_binary_observation(rng::AbstractRNG, latent::Int, r::Float64)
    return rand(rng) < r ? latent : 3 - latent
end

function generate_sim2_natural_episode(rng::AbstractRNG, config::Sim2Config)
    A_phi = make_sticky_matrix(2, config.phi_diag, config.phi_offdiag)

    g = zeros(Int, config.T)
    phi = zeros(Int, config.T)
    z1 = zeros(Int, config.T)
    z2 = zeros(Int, config.T)
    o1 = zeros(Int, config.T)
    o2 = zeros(Int, config.T)

    g[1] = rand(rng, 1:2)
    phi[1] = rand(rng, 1:2)

    for t in 1:config.T
        if t > 1
            phi[t] = sample_categorical(rng, view(A_phi, :, phi[t - 1]))
            g_diag = phi[t] == BIND ? config.g_diag_bind : config.g_diag_frag
            A_g = make_sticky_matrix(2, g_diag, 1.0 - g_diag)
            g[t] = sample_categorical(rng, view(A_g, :, g[t - 1]))
        end
        rho = phi[t] == BIND ? config.rho_bind : config.rho_frag
        obs_r = phi[t] == BIND ? config.r_obs_bind : config.r_obs_frag
        z1[t] = sample_match_state(rng, g[t], rho)
        z2[t] = sample_match_state(rng, g[t], rho)
        o1[t] = sample_binary_observation(rng, z1[t], obs_r)
        o2[t] = sample_binary_observation(rng, z2[t], obs_r)
    end

    return (; g, phi, z1, z2, o1, o2, has_truth = true)
end

function generate_sim2_unambiguous_probe(rng::AbstractRNG, config::Sim2Config)
    g = fill(1, config.T)
    phi = fill(BIND, config.T)
    z1 = fill(1, config.T)
    z2 = fill(1, config.T)
    o1 = [rand(rng) < 1.0 - config.unambiguous_noise ? 1 : 2 for _ in 1:config.T]
    o2 = [rand(rng) < 1.0 - config.unambiguous_noise ? 1 : 2 for _ in 1:config.T]
    return (; g, phi, z1, z2, o1, o2, has_truth = true)
end

function ambiguity_reveal_schedule(T::Int, interval::Int, len::Int)
    phi = fill(FRAG, T)
    t = max(interval, 1)
    while t <= T
        stop_t = min(t + len - 1, T)
        phi[t:stop_t] .= BIND
        t += interval
    end
    return phi
end

function frag_leader_schedule(T::Int, flip_len::Int)
    return [isodd(fld(t - 1, max(flip_len, 1)) + 1) ? 1 : 2 for t in 1:T]
end

function generate_sim2_ambiguity_probe(rng::AbstractRNG, config::Sim2Config)
    g = fill(2, config.T)
    phi = ambiguity_reveal_schedule(config.T, config.ambiguity_reveal_interval, config.ambiguity_reveal_len)
    leader = frag_leader_schedule(config.T, config.ambiguity_frag_flip_len)
    z1 = zeros(Int, config.T)
    z2 = zeros(Int, config.T)
    o1 = zeros(Int, config.T)
    o2 = zeros(Int, config.T)

    for t in 1:config.T
        if phi[t] == BIND
            z1[t] = g[t]
            z2[t] = g[t]
            o1[t] = sample_binary_observation(rng, z1[t], config.r_obs_bind)
            o2[t] = sample_binary_observation(rng, z2[t], config.r_obs_bind)
        else
            if leader[t] == 1
                z1[t] = 1
                z2[t] = 2
            else
                z1[t] = 2
                z2[t] = 1
            end
            o1[t] = sample_binary_observation(rng, z1[t], config.r_obs_frag)
            o2[t] = sample_binary_observation(rng, z2[t], config.r_obs_frag)
        end
    end

    return (; g, phi, z1, z2, o1, o2, has_truth = true)
end

function generate_sim2_bias_probe(rng::AbstractRNG, config::Sim2Config)
    g = fill(2, config.T)
    phi = ambiguity_reveal_schedule(config.T, config.ambiguity_reveal_interval, config.ambiguity_reveal_len)
    leader = frag_leader_schedule(config.T, config.ambiguity_frag_flip_len)
    z1 = zeros(Int, config.T)
    z2 = zeros(Int, config.T)
    o1 = zeros(Int, config.T)
    o2 = zeros(Int, config.T)
    for t in 1:config.T
        if phi[t] == BIND
            z1[t] = g[t]
            z2[t] = g[t]
            o1[t] = sample_binary_observation(rng, z1[t], config.r_obs_bind)
            o2[t] = sample_binary_observation(rng, z2[t], config.r_obs_bind)
        else
            if leader[t] == 1
                z1[t] = 1
                z2[t] = 2
            else
                z1[t] = 2
                z2[t] = 1
            end
            o1[t] = sample_binary_observation(rng, z1[t], config.r_obs_frag)
            o2[t] = sample_binary_observation(rng, z2[t], config.r_obs_frag)
        end
    end
    return (; g, phi, z1, z2, o1, o2, has_truth = true)
end

function generate_sim2_dataset(rng::AbstractRNG, config::Sim2Config)
    return (
        natural = [generate_sim2_natural_episode(rng, config) for _ in 1:config.n_episodes],
        unambiguous = generate_sim2_unambiguous_probe(rng, config),
        ambiguity = generate_sim2_ambiguity_probe(rng, config),
        bias = generate_sim2_bias_probe(rng, config)
    )
end
