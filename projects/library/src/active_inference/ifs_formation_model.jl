"""
    ifs_formation_model.jl - IFS Part Formation Simulation (Appendix A)

Demonstrates how part-like bundles form under overwhelm and low control
using Active Inference with Dirichlet learning.

Architecture:
  Hidden factors:
    1. Behavior:       avoid(1) / inspect(2) / stay(3)  -- controllable
    2. Self-state:     child_helpless(1) / adult_capable(2) -- inferred, static
    3. Threat meaning: danger(1) / safe(2) -- inferred, static

  Observation modalities:
    1. External cue:       ambiguous(1) / clear_safe(2) / clear_threat(3)
    2. Interoceptive:      calm(1) / activated(2) / panic(3)
    3. Outcome:            relief(1) / neutral(2) / harm(3)
    4. Support cue:        alone_overwhelmed(1) / supported(2)

  Policies (single-step, horizon=1):
    1. avoid  (action=1 on factor 1)
    2. inspect (action=2 on factor 1)
    3. stay   (action=3 on factor 1)

  Trial structure (T=2):
    t=1: observe cues, select policy
    t=2: observe outcome based on behavior x self-state x threat meaning

The key manipulation across conditions is how the outcome modality
relates to behavior and hidden states:
  - Condition A: Only avoid gives relief; inspect/stay lead to harm regardless
    of self-state (low control)
  - Condition B: adult_capable + inspect/stay can also yield relief/neutral
    (high control)
  - Condition C: Moderate differences; chronic low support
"""

using Random

# =============================================================================
# Formation Environment
# =============================================================================

"""
    IFSFormationEnvV2 <: AIFEnvironment

Environment for the IFS formation simulation. Generates observations
based on condition and true hidden states. At t=2, outcomes depend on
the behavioral action chosen at t=1.
"""
mutable struct IFSFormationEnvV2 <: AIFEnvironment
    condition::Symbol       # :A, :B, or :C
    phase::Symbol           # :acquisition or :readout
    timestep::Int
    last_action::Vector{Int}
    A::Vector{Array{Float64}}
    B::Vector{Array{Float64,3}}
end

function IFSFormationEnvV2(condition::Symbol, phase::Symbol,
                            A::Vector{<:Array}, B::Vector{<:Array{<:Real,3}})
    IFSFormationEnvV2(
        condition, phase, 1, [1, 1, 1],
        [Array{Float64}(a) for a in A],
        [Array{Float64,3}(b) for b in B]
    )
end

function reset!(env::IFSFormationEnvV2)
    env.timestep = 1
    env.last_action = [1, 1, 1]
    return env
end

function get_state(env::IFSFormationEnvV2)::Vector{Int}
    if env.phase == :acquisition
        # True state: start in avoid(1), child_helpless(1), danger(1)
        behavior = env.timestep == 1 ? 1 : env.last_action[1]
        return [behavior, 1, 1]
    else
        # Readout: safe context -> start avoid(1), adult_capable(2), safe(2)
        behavior = env.timestep == 1 ? 1 : env.last_action[1]
        return [behavior, 2, 2]
    end
end

function observe(env::IFSFormationEnvV2)::Vector{Int}
    state = get_state(env)
    Ng = length(env.A)
    obs = Vector{Int}(undef, Ng)

    for g in 1:Ng
        probs = env.A[g][:, state[1], state[2], state[3]]
        probs_sum = sum(probs)
        if probs_sum > 0
            probs = probs ./ probs_sum
        else
            probs = fill(1.0 / length(probs), length(probs))
        end
        obs[g] = sample_categorical(probs)
    end
    return obs
end

function step!(env::IFSFormationEnvV2, action::Vector{Int})
    env.last_action = copy(action)
    env.timestep += 1
    return env
end

# =============================================================================
# Model Construction
# =============================================================================

"""
    IFSFormationParams

Parameters for the IFS formation model.
"""
struct IFSFormationParams
    condition::Symbol
    n_acquisition::Int
    n_readout::Int
end

function IFSFormationParams(; condition::Symbol=:A, n_acquisition::Int=40, n_readout::Int=20)
    IFSFormationParams(condition, n_acquisition, n_readout)
end

"""
    build_formation_A(condition)

Build observation likelihood matrices A[g].

A[g] has shape (No[g], Ns[1], Ns[2], Ns[3]) = (No[g], 3, 2, 2)

Factor 1 (behavior): avoid(1), inspect(2), stay(3)
Factor 2 (self-state): child_helpless(1), adult_capable(2)
Factor 3 (threat meaning): danger(1), safe(2)

The critical manipulation: in Condition A, outcomes are bad for inspect/stay
REGARDLESS of self-state (low control). In Condition B, adult_capable
protects against harm during inspect/stay (high control).
"""
function build_formation_A(condition::Symbol)
    # --- Modality 1: External cue (3 obs x 3 x 2 x 2 states) ---
    # Cues depend mainly on threat meaning, not behavior
    A1 = zeros(3, 3, 2, 2)
    # threat meaning = danger(1): mostly threat cues
    A1[1, :, :, 1] .= 0.3   # ambiguous
    A1[2, :, :, 1] .= 0.1   # clear_safe
    A1[3, :, :, 1] .= 0.6   # clear_threat
    # threat meaning = safe(2): mostly safe cues
    A1[1, :, :, 2] .= 0.3   # ambiguous
    A1[2, :, :, 2] .= 0.6   # clear_safe
    A1[3, :, :, 2] .= 0.1   # clear_threat
    # Normalize
    A1 ./= sum(A1, dims=1)

    # --- Modality 2: Interoceptive arousal (3 obs) ---
    # Depends on behavior x self-state x threat meaning
    A2 = zeros(3, 3, 2, 2)

    # avoid(1): reduced arousal regardless (escape response works)
    A2[:, 1, 1, 1] = [0.2, 0.5, 0.3]   # helpless+danger: still some arousal
    A2[:, 1, 2, 1] = [0.3, 0.5, 0.2]   # capable+danger: manageable
    A2[:, 1, 1, 2] = [0.5, 0.35, 0.15] # helpless+safe: calming
    A2[:, 1, 2, 2] = [0.7, 0.25, 0.05] # capable+safe: calm

    # inspect(2): moderate-high arousal
    A2[:, 2, 1, 1] = [0.05, 0.3, 0.65] # helpless+danger: panic
    A2[:, 2, 2, 1] = [0.15, 0.5, 0.35] # capable+danger: activated
    A2[:, 2, 1, 2] = [0.35, 0.45, 0.2] # helpless+safe: mildly activated
    A2[:, 2, 2, 2] = [0.6, 0.3, 0.1]   # capable+safe: fairly calm

    # stay(3): highest arousal (sustained exposure)
    A2[:, 3, 1, 1] = [0.03, 0.22, 0.75] # helpless+danger: intense panic
    A2[:, 3, 2, 1] = [0.1, 0.45, 0.45]  # capable+danger: high activation
    A2[:, 3, 1, 2] = [0.3, 0.45, 0.25]  # helpless+safe: uneasy
    A2[:, 3, 2, 2] = [0.55, 0.35, 0.1]  # capable+safe: calm enough
    # Normalize
    A2 ./= sum(A2, dims=1)

    # --- Modality 3: Outcome (3 obs) -- THE KEY MODALITY ---
    # relief(1), neutral(2), harm(3)
    A3 = zeros(3, 3, 2, 2)

    if condition == :A
        # HIGH THREAT + LOW CONTROL
        # Avoidance -> relief regardless of self-state
        A3[:, 1, 1, 1] = [0.65, 0.25, 0.1]  # avoid+helpless+danger: relief
        A3[:, 1, 2, 1] = [0.65, 0.25, 0.1]  # avoid+capable+danger: relief
        A3[:, 1, 1, 2] = [0.6, 0.3, 0.1]    # avoid+helpless+safe: relief
        A3[:, 1, 2, 2] = [0.6, 0.3, 0.1]    # avoid+capable+safe: relief

        # Inspect -> HARM regardless of self-state (LOW CONTROL)
        A3[:, 2, 1, 1] = [0.05, 0.1, 0.85]  # inspect+helpless+danger: HARM
        A3[:, 2, 2, 1] = [0.08, 0.12, 0.8]  # inspect+capable+danger: STILL HARM
        A3[:, 2, 1, 2] = [0.4, 0.35, 0.25]  # inspect+helpless+safe: ok
        A3[:, 2, 2, 2] = [0.45, 0.35, 0.2]  # inspect+capable+safe: ok

        # Stay -> HARM regardless of self-state (LOW CONTROL)
        A3[:, 3, 1, 1] = [0.03, 0.07, 0.9]  # stay+helpless+danger: SEVERE HARM
        A3[:, 3, 2, 1] = [0.05, 0.1, 0.85]  # stay+capable+danger: STILL HARM
        A3[:, 3, 1, 2] = [0.35, 0.35, 0.3]  # stay+helpless+safe: meh
        A3[:, 3, 2, 2] = [0.4, 0.35, 0.25]  # stay+capable+safe: ok

    elseif condition == :B
        # HIGH THREAT + HIGH CONTROL
        # Avoidance -> relief
        A3[:, 1, 1, 1] = [0.6, 0.25, 0.15]
        A3[:, 1, 2, 1] = [0.6, 0.25, 0.15]
        A3[:, 1, 1, 2] = [0.6, 0.3, 0.1]
        A3[:, 1, 2, 2] = [0.6, 0.3, 0.1]

        # Inspect + helpless + danger: still bad
        A3[:, 2, 1, 1] = [0.1, 0.15, 0.75]
        # Inspect + CAPABLE + danger: CONTROL WORKS -> neutral/relief
        A3[:, 2, 2, 1] = [0.35, 0.4, 0.25]
        A3[:, 2, 1, 2] = [0.4, 0.35, 0.25]
        A3[:, 2, 2, 2] = [0.55, 0.35, 0.1]

        # Stay + helpless + danger: bad
        A3[:, 3, 1, 1] = [0.08, 0.12, 0.8]
        # Stay + CAPABLE + danger: CONTROL WORKS
        A3[:, 3, 2, 1] = [0.3, 0.4, 0.3]
        A3[:, 3, 1, 2] = [0.35, 0.35, 0.3]
        A3[:, 3, 2, 2] = [0.5, 0.35, 0.15]

    elseif condition == :C
        # CHRONIC LOW SUPPORT / MODERATE THREAT
        # Avoidance mildly better
        A3[:, 1, 1, 1] = [0.45, 0.3, 0.25]
        A3[:, 1, 2, 1] = [0.5, 0.3, 0.2]
        A3[:, 1, 1, 2] = [0.45, 0.35, 0.2]
        A3[:, 1, 2, 2] = [0.5, 0.35, 0.15]

        # Inspect: moderately worse
        A3[:, 2, 1, 1] = [0.15, 0.3, 0.55]
        A3[:, 2, 2, 1] = [0.2, 0.35, 0.45]
        A3[:, 2, 1, 2] = [0.35, 0.35, 0.3]
        A3[:, 2, 2, 2] = [0.4, 0.35, 0.25]

        # Stay: similar to inspect
        A3[:, 3, 1, 1] = [0.12, 0.28, 0.6]
        A3[:, 3, 2, 1] = [0.18, 0.32, 0.5]
        A3[:, 3, 1, 2] = [0.3, 0.35, 0.35]
        A3[:, 3, 2, 2] = [0.4, 0.35, 0.25]
    end
    # Normalize
    A3 ./= sum(A3, dims=1)

    # --- Modality 4: Support cue (2 obs) ---
    # alone_overwhelmed(1), supported(2)
    A4 = zeros(2, 3, 2, 2)

    if condition == :C
        # Chronic low support: always alone_overwhelmed
        A4[1, :, :, :] .= 0.85
        A4[2, :, :, :] .= 0.15
    else
        # Support depends on self-state and threat meaning
        # helpless + danger -> alone
        A4[1, :, 1, 1] .= 0.8
        A4[2, :, 1, 1] .= 0.2
        # capable + danger -> some support
        A4[1, :, 2, 1] .= 0.6
        A4[2, :, 2, 1] .= 0.4
        # helpless + safe -> moderate support
        A4[1, :, 1, 2] .= 0.45
        A4[2, :, 1, 2] .= 0.55
        # capable + safe -> supported
        A4[1, :, 2, 2] .= 0.2
        A4[2, :, 2, 2] .= 0.8
    end
    # Normalize
    A4 ./= sum(A4, dims=1)

    return [A1, A2, A3, A4]
end

"""
    build_formation_B()

Build transition matrices.

Factor 1 (behavior): 3 states, 3 actions - action directly sets behavior
Factor 2 (self-state): 2 states, 1 action - identity (static)
Factor 3 (threat meaning): 2 states, 1 action - identity (static)
"""
function build_formation_B()
    # Factor 1: behavior is controllable
    # Action i transitions to state i deterministically
    B1 = zeros(3, 3, 3)
    for a in 1:3
        # Action a transitions ANY current state to state a
        B1[a, :, a] .= 1.0
    end

    # Factor 2: self-state is static (identity)
    B2 = zeros(2, 2, 1)
    B2[:, :, 1] = [1.0 0.0; 0.0 1.0]

    # Factor 3: threat meaning is static (identity)
    B3 = zeros(2, 2, 1)
    B3[:, :, 1] = [1.0 0.0; 0.0 1.0]

    return [B1, B2, B3]
end

# Keep the old name as an alias
build_formation_B_with_actions() = build_formation_B()

"""
    build_formation_C(; trial_length=2)

Build preference matrices C[g] (log preferences).
"""
function build_formation_C(condition::Symbol=:A; trial_length::Int=2)
    # Modality 1: External cue - mild preference for safe
    C1 = zeros(3, trial_length)
    C1[1, :] .= 0.0    # ambiguous
    C1[2, :] .= 0.5    # clear_safe
    C1[3, :] .= -0.5   # clear_threat

    # Modality 2: Interoceptive - prefer calm
    C2 = zeros(3, trial_length)
    C2[1, :] .= 1.0    # calm
    C2[2, :] .= 0.0    # activated
    C2[3, :] .= -2.0   # panic

    # Modality 3: Outcome - strongly prefer relief, avoid harm
    C3 = zeros(3, trial_length)
    C3[1, :] .= 2.0    # relief
    C3[2, :] .= 0.0    # neutral
    C3[3, :] .= -3.0   # harm

    # Modality 4: Support
    C4 = zeros(2, trial_length)
    C4[1, :] .= -0.5   # alone
    C4[2, :] .= 0.5    # supported

    return [C1, C2, C3, C4]
end

"""
    build_formation_D_flat()

Flat (uniform) initial state priors.
"""
function build_formation_D_flat()
    D1 = [1/3, 1/3, 1/3]  # behavior: uniform over avoid/inspect/stay
    D2 = [0.5, 0.5]        # self-state: uniform
    D3 = [0.5, 0.5]        # threat meaning: uniform
    return [D1, D2, D3]
end

"""
    build_formation_policies()

Three single-step policies:
  1. avoid  (action=1 on factor 1, action=1 on factors 2,3)
  2. inspect (action=2 on factor 1, action=1 on factors 2,3)
  3. stay   (action=3 on factor 1, action=1 on factors 2,3)
"""
function build_formation_policies()
    # V has shape (horizon, n_policies, n_factors) = (1, 3, 3)
    V = zeros(Int, 1, 3, 3)
    V[1, 1, :] = [1, 1, 1]  # avoid
    V[1, 2, :] = [2, 1, 1]  # inspect
    V[1, 3, :] = [3, 1, 1]  # stay

    # Uniform policy prior
    E = [1.0, 1.0, 1.0]
    return PolicySet(V, E)
end

# =============================================================================
# Results Type
# =============================================================================

"""
    FormationResults

Results from a formation simulation run.
"""
struct FormationResults
    condition::Symbol
    # Per-trial tracking during acquisition
    p_helpless::Vector{Float64}
    p_danger::Vector{Float64}
    p_avoid::Vector{Float64}
    pD_history::Vector{Vector{Vector{Float64}}}
    # Readout phase
    readout_helpless::Vector{Float64}
    readout_danger::Vector{Float64}
    readout_avoid::Vector{Float64}
end

# =============================================================================
# Main Simulation
# =============================================================================

"""
    run_formation_simulation(condition; kwargs...)

Run the full formation simulation for a given condition.
"""
function run_formation_simulation(condition::Symbol;
    n_acquisition::Int=40,
    n_readout::Int=20,
    seed::Int=42,
    eta_D::Float64=1.0,
    gamma::Float64=4.0,
    alpha::Float64=8.0,
    pD_scale::Float64=1.0,
    verbose::Bool=false
)
    Random.seed!(seed)

    # Build model
    A = build_formation_A(condition)
    B = build_formation_B()
    C = build_formation_C(condition, trial_length=2)
    D = build_formation_D_flat()
    policies = build_formation_policies()

    model = AIFModel(A, B, C, D; policies=policies, trial_length=2)

    settings = AIFSettings(
        gamma=gamma,
        alpha=alpha,
        eta_D=eta_D,
        use_ambiguity=true,
        use_utility=true,
        use_states_info_gain=true,
        fpi_max_iter=16
    )

    agent = init_agent(model, pD_scale=pD_scale)

    # Storage
    p_helpless = Float64[]
    p_danger = Float64[]
    p_avoid = Float64[]
    pD_history = Vector{Vector{Float64}}[]

    # =========================================================================
    # ACQUISITION PHASE
    # =========================================================================
    env = IFSFormationEnvV2(condition, :acquisition, A, B)

    for trial in 1:n_acquisition
        reset_trial!(agent, model)
        reset!(env)

        # t=1: Observe cues
        agent.t = 1
        obs = observe(env)
        infer_states!(agent, model, obs, settings)

        # Policy selection
        infer_policies!(agent, model, settings)

        # Sample action
        action = sample_action(agent, model; alpha=settings.alpha)

        # Step environment (sets behavior state for t=2)
        step!(env, action)

        # t=2: Observe outcome
        agent.t = 2
        obs2 = observe(env)
        infer_states!(agent, model, obs2, settings)

        # Learn D priors from final beliefs
        update_pD_final!(agent, eta_D, [2, 3])  # Learn self-state and threat meaning

        # Record metrics
        D_norm = get_D_from_pD(agent.pD)
        push!(p_helpless, D_norm[2][1])
        push!(p_danger, D_norm[3][1])
        push!(p_avoid, agent.qpi[1])  # Policy 1 = avoid
        push!(pD_history, [copy(d) for d in agent.pD])

        if verbose && (trial % 10 == 0 || trial == 1)
            println("  Trial $trial: P(helpless)=$(round(D_norm[2][1], digits=3)), " *
                    "P(danger)=$(round(D_norm[3][1], digits=3)), " *
                    "P(avoid)=$(round(agent.qpi[1], digits=3))")
        end
    end

    # =========================================================================
    # READOUT PHASE - Safe ambiguous context
    # =========================================================================
    env_readout = IFSFormationEnvV2(condition, :readout, A, B)

    readout_helpless = Float64[]
    readout_danger = Float64[]
    readout_avoid = Float64[]

    for trial in 1:n_readout
        reset_trial!(agent, model)
        reset!(env_readout)

        agent.t = 1
        obs = observe(env_readout)
        infer_states!(agent, model, obs, settings)

        infer_policies!(agent, model, settings)
        action = sample_action(agent, model; alpha=settings.alpha)

        step!(env_readout, action)

        agent.t = 2
        obs2 = observe(env_readout)
        infer_states!(agent, model, obs2, settings)

        # No learning in readout
        D_norm = get_D_from_pD(agent.pD)
        push!(readout_helpless, D_norm[2][1])
        push!(readout_danger, D_norm[3][1])
        push!(readout_avoid, agent.qpi[1])
    end

    return FormationResults(
        condition,
        p_helpless, p_danger, p_avoid, pD_history,
        readout_helpless, readout_danger, readout_avoid
    )
end

"""
    run_formation_comparison(; kwargs...)

Run all three conditions and return results for comparison.
"""
function run_formation_comparison(;
    n_acquisition::Int=40,
    n_readout::Int=20,
    seeds::Vector{Int}=[42],
    eta_D::Float64=1.0,
    gamma::Float64=4.0,
    alpha::Float64=8.0,
    pD_scale::Float64=1.0,
    verbose::Bool=true
)
    all_results = Dict{Symbol, Vector{FormationResults}}()

    for condition in [:A, :B, :C]
        if verbose
            println("\n" * "="^50)
            println("Condition $condition")
            println("="^50)
        end

        condition_results = FormationResults[]
        for seed in seeds
            result = run_formation_simulation(condition;
                n_acquisition=n_acquisition,
                n_readout=n_readout,
                seed=seed,
                eta_D=eta_D,
                gamma=gamma,
                alpha=alpha,
                pD_scale=pD_scale,
                verbose=verbose
            )
            push!(condition_results, result)
        end
        all_results[condition] = condition_results
    end

    return all_results
end
