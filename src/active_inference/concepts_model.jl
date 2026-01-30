"""
    concepts_model.jl - Concept learning task (PMC7250191)

Implements the generative model and helpers from the paper's
supplementary `Concepts_model.m`.
"""

# =============================================================================
# Constants and Labels
# =============================================================================

const CONCEPT_ANIMALS = [
    "Parakeet", "Parrot", "Pigeon", "Hawk",
    "Clownfish", "Manta ray", "Minnow", "Shark"
]

const CONCEPT_REPORTS = [
    "start",
    "Choose Parakeet",
    "Choose Parrot",
    "Choose Pigeon",
    "Choose Hawk",
    "Choose Clownfish",
    "Choose Manta ray",
    "Choose Sardine",
    "Choose Shark",
    "Choose Bird",
    "Choose Fish"
]

const CONCEPT_FEEDBACK = ["start", "correct-specific", "incorrect", "correct-basic"]

const N_CONCEPTS = 8
const N_REPORT_STATES = 11

const MOD_SIZE = 1
const MOD_COLOR = 2
const MOD_SPECIES = 3
const MOD_FEEDBACK = 4

const FEEDBACK_START = 1
const FEEDBACK_CORRECT_SPECIFIC = 2
const FEEDBACK_INCORRECT = 3
const FEEDBACK_CORRECT_BASIC = 4

# =============================================================================
# Environment
# =============================================================================

struct ConceptsEnvironment <: AIFEnvironment
    A::Vector{Array{Float64}}
    B::Vector{Array{Float64,3}}
    animal_probs::Vector{Float64}
    animal_sequence::Union{Nothing, Vector{Int}}
    sequence_idx::Int
    current_state::Vector{Int}
end

function ConceptsEnvironment(
    A::Vector{Array{Float64}},
    B::Vector{Array{Float64,3}};
    animal_probs::Vector{Float64}=fill(1.0 / N_CONCEPTS, N_CONCEPTS),
    animal_sequence::Union{Nothing, Vector{Int}}=nothing
)
    current_state = [1, 1] # [animal, report]
    return ConceptsEnvironment(A, B, animal_probs, animal_sequence, 1, current_state)
end

function reset!(env::ConceptsEnvironment)
    # Sample or set animal identity
    if isnothing(env.animal_sequence)
        env.current_state[1] = sample_categorical(env.animal_probs)
    else
        idx = env.sequence_idx
        env.current_state[1] = env.animal_sequence[idx]
        env.sequence_idx = min(idx + 1, length(env.animal_sequence))
    end
    # Reset report state to start
    env.current_state[2] = 1
    return env
end

function get_state(env::ConceptsEnvironment)::Vector{Int}
    return copy(env.current_state)
end

function observe(env::ConceptsEnvironment)::Vector{Int}
    Ng = length(env.A)
    obs = Vector{Int}(undef, Ng)
    s1, s2 = env.current_state

    for g in 1:Ng
        probs = env.A[g][:, s1, s2]
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

function step!(env::ConceptsEnvironment, action::Vector{Int})
    Nf = length(env.B)
    for f in 1:Nf
        s_current = env.current_state[f]
        Na_f = size(env.B[f], 3)
        a_f = Na_f > 1 ? action[f] : 1
        probs = env.B[f][:, s_current, a_f]
        probs_sum = sum(probs)
        if probs_sum > 0
            probs = probs ./ probs_sum
        else
            probs = zeros(length(probs))
            probs[s_current] = 1.0
        end
        env.current_state[f] = sample_categorical(probs)
    end
    return env
end

# =============================================================================
# Model Construction
# =============================================================================

"""
    build_concepts_A() -> Vector{Array{Float64}}

Constructs the A matrices from Concepts_model.m.
"""
function build_concepts_A()
    Ns = (N_CONCEPTS, N_REPORT_STATES)
    No = (3, 3, 3, 4)
    A = Vector{Array{Float64}}(undef, length(No))
    for g in 1:length(No)
        A[g] = zeros(Float64, No[g], Ns...)
    end

    size_row2 = [0, 1, 0, 1, 0, 1, 0, 1]
    size_row3 = [1, 0, 1, 0, 1, 0, 1, 0]

    color_row2 = [1, 1, 0, 0, 1, 1, 0, 0]
    color_row3 = [0, 0, 1, 1, 0, 0, 1, 1]

    species_row2 = [1, 1, 1, 1, 0, 0, 0, 0]
    species_row3 = [0, 0, 0, 0, 1, 1, 1, 1]

    for r in 1:N_REPORT_STATES
        A[MOD_SIZE][2, :, r] .= size_row2
        A[MOD_SIZE][3, :, r] .= size_row3

        A[MOD_COLOR][2, :, r] .= color_row2
        A[MOD_COLOR][3, :, r] .= color_row3

        A[MOD_SPECIES][2, :, r] .= species_row2
        A[MOD_SPECIES][3, :, r] .= species_row3
    end

    # Feedback modality
    # Start action (report state = 1)
    A[MOD_FEEDBACK][FEEDBACK_START, :, 1] .= 1.0

    # Specific reports (2..9)
    for action in 2:9
        animal_idx = action - 1
        for animal in 1:N_CONCEPTS
            if animal == animal_idx
                A[MOD_FEEDBACK][FEEDBACK_CORRECT_SPECIFIC, animal, action] = 1.0
            else
                A[MOD_FEEDBACK][FEEDBACK_INCORRECT, animal, action] = 1.0
            end
        end
    end

    # Basic report: Bird (10) -> animals 1..4
    for animal in 1:N_CONCEPTS
        if animal <= 4
            A[MOD_FEEDBACK][FEEDBACK_CORRECT_BASIC, animal, 10] = 1.0
        else
            A[MOD_FEEDBACK][FEEDBACK_INCORRECT, animal, 10] = 1.0
        end
    end

    # Basic report: Fish (11) -> animals 5..8
    for animal in 1:N_CONCEPTS
        if animal >= 5
            A[MOD_FEEDBACK][FEEDBACK_CORRECT_BASIC, animal, 11] = 1.0
        else
            A[MOD_FEEDBACK][FEEDBACK_INCORRECT, animal, 11] = 1.0
        end
    end

    return A
end

"""
    build_concepts_B() -> Vector{Array{Float64,3}}

Construct B matrices from Concepts_model.m.
"""
function build_concepts_B()
    B = Vector{Array{Float64,3}}(undef, 2)

    # Animal factor (identity, single action)
    B[1] = zeros(Float64, N_CONCEPTS, N_CONCEPTS, 1)
    for s in 1:N_CONCEPTS
        B[1][s, s, 1] = 1.0
    end

    # Report factor (controllable)
    B[2] = zeros(Float64, N_REPORT_STATES, N_REPORT_STATES, N_REPORT_STATES)

    for k in 1:N_REPORT_STATES
        B[2][k, :, k] .= 1.0
    end

    # Absorb in report states 2..11
    for s in 2:N_REPORT_STATES
        B[2][:, s, :] .= 0.0
        B[2][s, s, :] .= 1.0
    end

    return B
end

"""
    build_concepts_C(T::Int=2) -> Vector{Matrix{Float64}}
"""
function build_concepts_C(T::Int=2)
    C = [zeros(3, T), zeros(3, T), zeros(3, T), zeros(4, T)]
    # Feedback preferences
    C[MOD_FEEDBACK][FEEDBACK_CORRECT_SPECIFIC, :] .= 4.0
    C[MOD_FEEDBACK][FEEDBACK_CORRECT_BASIC, :] .= 0.0
    C[MOD_FEEDBACK][FEEDBACK_INCORRECT, :] .= -4.0
    return C
end

"""
    build_concepts_D() -> Vector{Vector{Float64}}
"""
function build_concepts_D()
    D1 = ones(Float64, N_CONCEPTS)
    D2 = zeros(Float64, N_REPORT_STATES)
    D2[1] = 1.0
    return [D1, D2]
end

"""
    build_concepts_policies(T::Int=2; allow_reports::Bool=true) -> PolicySet

If `allow_reports=false`, only the "stay/start" policy is allowed.
"""
function build_concepts_policies(T::Int=2; allow_reports::Bool=true)
    horizon = T - 1
    n_factors = 2

    if allow_reports
        actions = collect(2:N_REPORT_STATES)
    else
        actions = [1]
    end

    n_policies = length(actions)
    V = ones(Int, horizon, n_policies, n_factors)

    # Action for report factor
    for (i, act) in enumerate(actions)
        V[:, i, 2] .= act
    end
    # Animal factor has only one action
    V[:, :, 1] .= 1

    E = fill(1.0 / n_policies, n_policies)

    return PolicySet(V, E)
end

"""
    build_concepts_model(; T=2, allow_reports=true) -> AIFModel
"""
function build_concepts_model(; T::Int=2, allow_reports::Bool=true)
    A = build_concepts_A()
    B = build_concepts_B()
    C = build_concepts_C(T)
    D = build_concepts_D()
    policies = build_concepts_policies(T; allow_reports=allow_reports)

    return AIFModel(A, B, C, D; policies=policies, trial_length=T)
end

# =============================================================================
# Agent Initialization
# =============================================================================

"""
    init_concepts_agent(model; remove_granularity=false, remove_concepts=Int[], remove_all=false)

Initialize agent with prior pA/pD matching Concepts_model.m.
"""
function init_concepts_agent(
    model::AIFModel;
    remove_granularity::Bool=false,
    remove_concepts::Vector{Int}=Int[],
    remove_all::Bool=false,
    noise::Float64=0.01
)
    pA = [copy(model.A[g]) for g in 1:model.Ng]
    pB = [copy(model.B[f]) for f in 1:length(model.D)]
    pD = [copy(model.D[f]) for f in 1:length(model.D)]

    # Flatten helper for feature modalities
    function flatten_feature!(Amod::Array{Float64,3}, animal_idx::Int)
        for r in 1:size(Amod, 3)
            vec = [0.5, 0.5] .+ noise .* randn(2)
            vec .= max.(vec, eps(Float64))
            vec ./= sum(vec)
            Amod[2, animal_idx, r] = vec[1]
            Amod[3, animal_idx, r] = vec[2]
        end
    end

    if remove_all
        for animal in 1:N_CONCEPTS
            flatten_feature!(pA[MOD_SIZE], animal)
            flatten_feature!(pA[MOD_COLOR], animal)
            flatten_feature!(pA[MOD_SPECIES], animal)
        end
    elseif remove_granularity
        for animal in 1:N_CONCEPTS
            flatten_feature!(pA[MOD_SIZE], animal)
            flatten_feature!(pA[MOD_COLOR], animal)
        end
    else
        for animal in remove_concepts
            flatten_feature!(pA[MOD_SIZE], animal)
            flatten_feature!(pA[MOD_COLOR], animal)
            flatten_feature!(pA[MOD_SPECIES], animal)
        end
    end

    return init_agent(model, pA, pB, pD)
end

# =============================================================================
# Evaluation Helpers
# =============================================================================

"""
    classify_report(animal_idx, report_action) -> Symbol

Return :correct_specific, :correct_basic, or :incorrect.
"""
function classify_report(animal_idx::Int, report_action::Int)
    if report_action == 1
        return :no_report
    elseif 2 <= report_action <= 9
        return (report_action - 1 == animal_idx) ? :correct_specific : :incorrect
    elseif report_action == 10
        return (animal_idx <= 4) ? :correct_basic : :incorrect
    elseif report_action == 11
        return (animal_idx >= 5) ? :correct_basic : :incorrect
    else
        return :incorrect
    end
end

"""
    evaluate_reporting(agent, model; trials_per_animal=20) -> NamedTuple
"""
function evaluate_reporting(
    agent::AIFAgent,
    model::AIFModel;
    trials_per_animal::Int=20
)
    total = 0
    correct_specific = 0
    correct_basic = 0
    incorrect = 0

    seq = vcat([fill(a, trials_per_animal) for a in 1:N_CONCEPTS]...)
    env = ConceptsEnvironment(model.A, model.B; animal_sequence=seq)

    settings = AIFSettings(
        gamma=1.0,
        alpha=128.0,
        eta_A=0.0,
        eta_D=0.0,
        eta_B=0.0,
        use_param_info_gain=false
    )

    for _ in 1:length(seq)
        hist = run_trial!(agent, model, env, settings; learn_A=Int[], learn_B=Int[], learn_D=Int[])
        animal_idx = env.current_state[1]
        report_action = hist.actions[1][2]
        result = classify_report(animal_idx, report_action)
        total += 1
        if result == :correct_specific
            correct_specific += 1
        elseif result == :correct_basic
            correct_basic += 1
        elseif result == :incorrect
            incorrect += 1
        end
    end

    return (
        total=total,
        correct_specific=correct_specific,
        correct_basic=correct_basic,
        incorrect=incorrect,
        acc_specific=correct_specific / total,
        acc_basic=(correct_specific + correct_basic) / total
    )
end

