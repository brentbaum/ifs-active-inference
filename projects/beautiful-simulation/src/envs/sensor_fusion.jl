const BG = 1
const VG = 2
const AG = 3
const BP = 4

Base.@kwdef struct Sim1Config
    seeds::Vector{Int} = copy(DEFAULT_SEEDS)
    n_episodes::Int = 20
    n_probe_episodes::Int = 20
    T::Int = 240
    n_states::Int = 4
    n_contexts::Int = 4
    state_diag::Float64 = 0.85
    state_offdiag::Float64 = 0.05
    context_diag::Float64 = 0.94
    context_offdiag::Float64 = 0.02
    burn_in::Int = 40
    switch_window::Int = 10
    probe_schedule::Vector{Int} = vcat(fill(BG, 60), fill(VG, 60), fill(AG, 60), fill(BP, 60))
end

default_sim1_config() = Sim1Config()

function load_sim1_config(path::AbstractString)
    defaults = default_sim1_config()
    raw = YAML.load_file(path)

    return Sim1Config(
        seeds = haskey(raw, "seeds") ? Int.(raw["seeds"]) : defaults.seeds,
        n_episodes = get(raw, "n_episodes", defaults.n_episodes),
        n_probe_episodes = get(raw, "n_probe_episodes", defaults.n_probe_episodes),
        T = get(raw, "T", defaults.T),
        n_states = get(raw, "n_states", defaults.n_states),
        n_contexts = get(raw, "n_contexts", defaults.n_contexts),
        state_diag = get(raw, "state_diag", defaults.state_diag),
        state_offdiag = get(raw, "state_offdiag", defaults.state_offdiag),
        context_diag = get(raw, "context_diag", defaults.context_diag),
        context_offdiag = get(raw, "context_offdiag", defaults.context_offdiag),
        burn_in = get(raw, "burn_in", defaults.burn_in),
        switch_window = get(raw, "switch_window", defaults.switch_window),
        probe_schedule = haskey(raw, "probe_schedule") ? Int.(raw["probe_schedule"]) : defaults.probe_schedule
    )
end

function make_sticky_matrix(n::Int, diag::Float64, offdiag::Float64)
    matrix = fill(offdiag, n, n)
    for i in 1:n
        matrix[i, i] = diag
    end
    return matrix
end

function make_emission(r::Float64)
    matrix = fill((1.0 - r) / 3.0, 4, 4)
    for s in 1:4
        matrix[s, s] = r
    end
    return matrix
end

function sim1_reliability_table()
    return (
        r_vision = [0.90, 0.90, 0.40, 0.40],
        r_audio = [0.90, 0.40, 0.90, 0.40]
    )
end

function sample_categorical(rng::AbstractRNG, probs::AbstractVector{<:Real})
    r = rand(rng)
    cumulative = 0.0
    for i in eachindex(probs)
        cumulative += probs[i]
        if r <= cumulative
            return i
        end
    end
    return length(probs)
end

function generate_sim1_episode(
    rng::AbstractRNG,
    config::Sim1Config;
    probe_schedule::Union{Nothing, Vector{Int}} = nothing
)
    A_s = make_sticky_matrix(config.n_states, config.state_diag, config.state_offdiag)
    A_phi = make_sticky_matrix(config.n_contexts, config.context_diag, config.context_offdiag)
    table = sim1_reliability_table()
    Bv = [make_emission(r) for r in table.r_vision]
    Ba = [make_emission(r) for r in table.r_audio]

    s = zeros(Int, config.T)
    phi = zeros(Int, config.T)
    ov = zeros(Int, config.T)
    oa = zeros(Int, config.T)

    s[1] = rand(rng, 1:config.n_states)
    phi[1] = isnothing(probe_schedule) ? rand(rng, 1:config.n_contexts) : probe_schedule[1]

    for t in 1:config.T
        if t > 1
            s[t] = sample_categorical(rng, view(A_s, :, s[t - 1]))
            phi[t] = isnothing(probe_schedule) ? sample_categorical(rng, view(A_phi, :, phi[t - 1])) : probe_schedule[t]
        end
        ov[t] = sample_categorical(rng, view(Bv[phi[t]], :, s[t]))
        oa[t] = sample_categorical(rng, view(Ba[phi[t]], :, s[t]))
    end

    return (; s, phi, ov, oa)
end

function generate_sim1_dataset(rng::AbstractRNG, config::Sim1Config)
    natural = [generate_sim1_episode(rng, config) for _ in 1:config.n_episodes]
    probe = [
        generate_sim1_episode(rng, config; probe_schedule = config.probe_schedule)
        for _ in 1:config.n_probe_episodes
    ]
    return (; natural, probe)
end
