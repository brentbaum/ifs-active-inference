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
    context_diag::Float64 = 0.995
    context_offdiag::Float64 = 0.0016666666666666668
    burn_in::Int = 40
    switch_window::Int = 10
    r_vision::Vector{Float64} = [0.95, 0.95, 0.05, 0.05]
    r_audio::Vector{Float64} = [0.95, 0.05, 0.95, 0.05]
    shift_vision::Vector{Int} = [0, 0, 1, 1]
    shift_audio::Vector{Int} = [0, 1, 0, 1]
    probe_schedule::Vector{Int} = vcat(fill(BG, 60), fill(VG, 60), fill(AG, 60), fill(BP, 60))
    probe_state_schedule::Vector{Int} = vcat(fill(1, 65), fill(4, 60), fill(3, 60), fill(2, 55))
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
        r_vision = haskey(raw, "r_vision") ? Float64.(raw["r_vision"]) : defaults.r_vision,
        r_audio = haskey(raw, "r_audio") ? Float64.(raw["r_audio"]) : defaults.r_audio,
        shift_vision = haskey(raw, "shift_vision") ? Int.(raw["shift_vision"]) : defaults.shift_vision,
        shift_audio = haskey(raw, "shift_audio") ? Int.(raw["shift_audio"]) : defaults.shift_audio,
        probe_schedule = haskey(raw, "probe_schedule") ? Int.(raw["probe_schedule"]) : defaults.probe_schedule,
        probe_state_schedule = haskey(raw, "probe_state_schedule") ? Int.(raw["probe_state_schedule"]) : defaults.probe_state_schedule
    )
end

function make_sticky_matrix(n::Int, diag::Float64, offdiag::Float64)
    matrix = fill(offdiag, n, n)
    for i in 1:n
        matrix[i, i] = diag
    end
    return matrix
end

function make_emission(r::Float64, shift::Int = 0)
    matrix = fill(0.0, 4, 4)
    for s in 1:4
        matrix[s, s] = r
        if shift == 0
            spill = (1.0 - r) / 3.0
            for o in 1:4
                if o != s
                    matrix[o, s] = spill
                end
            end
        else
            wrong_state = mod1(s + shift, 4)
            matrix[wrong_state, s] = 1.0 - r
        end
    end
    return matrix
end

function sim1_reliability_table(config::Sim1Config)
    return (
        r_vision = config.r_vision,
        r_audio = config.r_audio,
        shift_vision = config.shift_vision,
        shift_audio = config.shift_audio
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
    probe_schedule::Union{Nothing, Vector{Int}} = nothing,
    probe_state_schedule::Union{Nothing, Vector{Int}} = nothing
)
    A_s = make_sticky_matrix(config.n_states, config.state_diag, config.state_offdiag)
    A_phi = make_sticky_matrix(config.n_contexts, config.context_diag, config.context_offdiag)
    table = sim1_reliability_table(config)
    Bv = [make_emission(table.r_vision[i], table.shift_vision[i]) for i in 1:config.n_contexts]
    Ba = [make_emission(table.r_audio[i], table.shift_audio[i]) for i in 1:config.n_contexts]

    s = zeros(Int, config.T)
    phi = zeros(Int, config.T)
    ov = zeros(Int, config.T)
    oa = zeros(Int, config.T)

    s[1] = rand(rng, 1:config.n_states)
    phi[1] = isnothing(probe_schedule) ? rand(rng, 1:config.n_contexts) : probe_schedule[1]

    for t in 1:config.T
        if t > 1
            s[t] = isnothing(probe_state_schedule) ? sample_categorical(rng, view(A_s, :, s[t - 1])) : probe_state_schedule[t]
            phi[t] = isnothing(probe_schedule) ? sample_categorical(rng, view(A_phi, :, phi[t - 1])) : probe_schedule[t]
        elseif !isnothing(probe_state_schedule)
            s[t] = probe_state_schedule[t]
        end
        ov[t] = sample_categorical(rng, view(Bv[phi[t]], :, s[t]))
        oa[t] = sample_categorical(rng, view(Ba[phi[t]], :, s[t]))
    end

    return (; s, phi, ov, oa)
end

function generate_sim1_dataset(rng::AbstractRNG, config::Sim1Config)
    natural = [generate_sim1_episode(rng, config) for _ in 1:config.n_episodes]
    probe = [
        generate_sim1_episode(rng, config; probe_schedule = config.probe_schedule, probe_state_schedule = config.probe_state_schedule)
        for _ in 1:config.n_probe_episodes
    ]
    return (; natural, probe)
end
