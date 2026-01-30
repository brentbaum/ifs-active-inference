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
const N_DISTANCE_REPORT_STATES = 3

const DISTANCE_REPORTS = ["start", "Yes", "No"]

const SIZE_ROW2 = [0, 1, 0, 1, 0, 1, 0, 1]
const SIZE_ROW3 = [1, 0, 1, 0, 1, 0, 1, 0]

const COLOR_ROW2 = [1, 1, 0, 0, 1, 1, 0, 0]
const COLOR_ROW3 = [0, 0, 1, 1, 0, 0, 1, 1]

const SPECIES_ROW2 = [1, 1, 1, 1, 0, 0, 0, 0]
const SPECIES_ROW3 = [0, 0, 0, 0, 1, 1, 1, 1]

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

mutable struct ConceptsEnvironment <: AIFEnvironment
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

    for r in 1:N_REPORT_STATES
        A[MOD_SIZE][2, :, r] .= SIZE_ROW2
        A[MOD_SIZE][3, :, r] .= SIZE_ROW3

        A[MOD_COLOR][2, :, r] .= COLOR_ROW2
        A[MOD_COLOR][3, :, r] .= COLOR_ROW3

        A[MOD_SPECIES][2, :, r] .= SPECIES_ROW2
        A[MOD_SPECIES][3, :, r] .= SPECIES_ROW3
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
# Generalization (Distance Question) Variant
# =============================================================================

"""
    build_distance_A() -> Vector{Array{Float64}}

Build A for the distance-question task (report: Yes/No).
"""
function build_distance_A()
    Ns = (N_CONCEPTS, N_DISTANCE_REPORT_STATES)
    No = (3, 3, 3, 4)
    A = Vector{Array{Float64}}(undef, length(No))
    for g in 1:length(No)
        A[g] = zeros(Float64, No[g], Ns...)
    end

    for r in 1:N_DISTANCE_REPORT_STATES
        A[MOD_SIZE][2, :, r] .= SIZE_ROW2
        A[MOD_SIZE][3, :, r] .= SIZE_ROW3

        A[MOD_COLOR][2, :, r] .= COLOR_ROW2
        A[MOD_COLOR][3, :, r] .= COLOR_ROW3

        A[MOD_SPECIES][2, :, r] .= SPECIES_ROW2
        A[MOD_SPECIES][3, :, r] .= SPECIES_ROW3
    end

    # Distance rule: seen from afar if big + colorful
    seen_from_distance = [(SIZE_ROW2[i] == 1 && COLOR_ROW2[i] == 1) for i in 1:N_CONCEPTS]

    # Feedback modality
    A[MOD_FEEDBACK][FEEDBACK_START, :, 1] .= 1.0

    for animal in 1:N_CONCEPTS
        if seen_from_distance[animal]
            A[MOD_FEEDBACK][FEEDBACK_CORRECT_SPECIFIC, animal, 2] = 1.0
            A[MOD_FEEDBACK][FEEDBACK_INCORRECT, animal, 3] = 1.0
        else
            A[MOD_FEEDBACK][FEEDBACK_INCORRECT, animal, 2] = 1.0
            A[MOD_FEEDBACK][FEEDBACK_CORRECT_SPECIFIC, animal, 3] = 1.0
        end
    end

    return A
end

"""
    build_distance_B() -> Vector{Array{Float64,3}}
"""
function build_distance_B()
    B = Vector{Array{Float64,3}}(undef, 2)

    B[1] = zeros(Float64, N_CONCEPTS, N_CONCEPTS, 1)
    for s in 1:N_CONCEPTS
        B[1][s, s, 1] = 1.0
    end

    B[2] = zeros(Float64, N_DISTANCE_REPORT_STATES, N_DISTANCE_REPORT_STATES, N_DISTANCE_REPORT_STATES)
    for k in 1:N_DISTANCE_REPORT_STATES
        B[2][k, :, k] .= 1.0
    end

    for s in 2:N_DISTANCE_REPORT_STATES
        B[2][:, s, :] .= 0.0
        B[2][s, s, :] .= 1.0
    end

    return B
end

"""
    build_distance_D() -> Vector{Vector{Float64}}
"""
function build_distance_D()
    D1 = ones(Float64, N_CONCEPTS)
    D2 = zeros(Float64, N_DISTANCE_REPORT_STATES)
    D2[1] = 1.0
    return [D1, D2]
end

"""
    build_distance_policies(T::Int=2; allow_reports::Bool=true) -> PolicySet
"""
function build_distance_policies(T::Int=2; allow_reports::Bool=true)
    horizon = T - 1
    n_factors = 2

    actions = allow_reports ? [2, 3] : [1]
    n_policies = length(actions)
    V = ones(Int, horizon, n_policies, n_factors)

    for (i, act) in enumerate(actions)
        V[:, i, 2] .= act
    end
    V[:, :, 1] .= 1

    E = fill(1.0 / n_policies, n_policies)
    return PolicySet(V, E)
end

"""
    build_distance_model(; T=2, allow_reports=true) -> AIFModel
"""
function build_distance_model(; T::Int=2, allow_reports::Bool=true)
    A = build_distance_A()
    B = build_distance_B()
    C = build_concepts_C(T)
    D = build_distance_D()
    policies = build_distance_policies(T; allow_reports=allow_reports)
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
# Training and Transfer Helpers
# =============================================================================

"""
    concepts_settings(; kwargs...) -> AIFSettings

Default settings for the concepts model (alpha=128, gamma=1).
"""
function concepts_settings(;
    gamma::Real=1.0,
    alpha::Real=128.0,
    eta_A::Real=1.0,
    eta_D::Real=1.0,
    eta_B::Real=0.0,
    use_param_info_gain::Bool=false,
    use_dirichlet_expectation::Bool=true
)
    return AIFSettings(
        gamma=gamma,
        alpha=alpha,
        eta_A=eta_A,
        eta_B=eta_B,
        eta_D=eta_D,
        use_param_info_gain=use_param_info_gain,
        use_dirichlet_expectation=use_dirichlet_expectation
    )
end

"""
    copy_agent_to_model(agent, model) -> AIFAgent

Create a new agent for `model` carrying over learned pA/pB/pD from `agent`.
Useful when switching between learning and reporting policy sets.
"""
function copy_agent_to_model(agent::AIFAgent, model::AIFModel)
    pA = [copy(pa) for pa in agent.pA]
    pB = [copy(pb) for pb in agent.pB]
    pD = [copy(pd) for pd in agent.pD]
    return init_agent(model, pA, pB, pD)
end

"""
    run_concepts_learning!(agent, model; n_trials=2000, animal_probs, animal_sequence, learn_A, learn_D, settings)

Run the learning phase with reporting disabled (policies restricted by model).
"""
function run_concepts_learning!(
    agent::AIFAgent,
    model::AIFModel;
    n_trials::Int=2000,
    animal_probs::Vector{Float64}=fill(1.0 / N_CONCEPTS, N_CONCEPTS),
    animal_sequence::Union{Nothing, Vector{Int}}=nothing,
    learn_A::Vector{Int}=[MOD_SIZE, MOD_COLOR, MOD_SPECIES],
    learn_D::Vector{Int}=[1],
    settings::AIFSettings=concepts_settings()
)
    env = ConceptsEnvironment(model.A, model.B;
        animal_probs=animal_probs,
        animal_sequence=animal_sequence
    )

    for _ in 1:n_trials
        run_trial!(agent, model, env, settings;
            learn_A=learn_A,
            learn_B=Int[],
            learn_D=learn_D
        )
        # Tie feature likelihoods across report states (A does not depend on report)
        for g in (MOD_SIZE, MOD_COLOR, MOD_SPECIES)
            for r in 2:N_REPORT_STATES
                agent.pA[g][:, :, r] .= agent.pA[g][:, :, 1]
            end
        end
    end

    return agent
end

# =============================================================================
# Bayesian Model Reduction (BMR) for D
# =============================================================================

"""
    bmr_log_evidence(q, p, r) -> Float64

Compute negative log-evidence (free energy) for a reduced Dirichlet prior `r`
given posterior `q` and full prior `p`.
"""
function bmr_log_evidence(q::AbstractVector, p::AbstractVector, r::AbstractVector)
    logB(x) = sum(loggamma.(x)) - loggamma(sum(x))
    n = q .- p
    log_evidence = logB(r .+ n) - logB(r)
    return -log_evidence
end

"""
    bmr_reduce_D(q, p; values=[1.0, 8.0]) -> NamedTuple

Search over combinations of `values` for each element of D to find the
reduced prior that maximizes log evidence (minimizes free energy).
"""
function bmr_reduce_D(q::AbstractVector, p::AbstractVector; values::Vector{Float64}=[1.0, 8.0])
    n = length(q)
    n_models = length(values)^n
    best_r = copy(p)
    best_f = Inf

    for mask in 0:(n_models - 1)
        r = similar(q, Float64)
        idx = mask
        for i in 1:n
            choice = (idx % length(values)) + 1
            r[i] = values[choice]
            idx ÷= length(values)
        end
        f = bmr_log_evidence(q, p, r)
        if f < best_f
            best_f = f
            best_r .= r
        end
    end

    return (prior=best_r, free_energy=best_f)
end

"""
    apply_bmr_D!(agent, prior; values=[1.0, 8.0]) -> NamedTuple

Apply BMR to factor 1 (concept identity) and overwrite agent.pD[1].
"""
function apply_bmr_D!(agent::AIFAgent, prior::Vector{Float64}; values::Vector{Float64}=[1.0, 8.0])
    result = bmr_reduce_D(agent.pD[1], prior; values=values)
    agent.pD[1] .= result.prior
    return result
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
    classify_distance_report(animal_idx, report_action) -> Symbol

Return :correct or :incorrect for the distance question (Yes/No).
"""
function classify_distance_report(animal_idx::Int, report_action::Int)
    seen_from_distance = (SIZE_ROW2[animal_idx] == 1 && COLOR_ROW2[animal_idx] == 1)
    if report_action == 1
        return :no_report
    elseif report_action == 2
        return seen_from_distance ? :correct : :incorrect
    elseif report_action == 3
        return seen_from_distance ? :incorrect : :correct
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
    trials_per_animal::Int=20,
    animal_sequence::Union{Nothing, Vector{Int}}=nothing,
    deterministic::Bool=true,
    settings::AIFSettings=concepts_settings(eta_A=0.0, eta_B=0.0, eta_D=0.0)
)
    total = 0
    correct_specific = 0
    correct_basic = 0
    incorrect = 0

    seq = isnothing(animal_sequence) ?
        vcat([fill(a, trials_per_animal) for a in 1:N_CONCEPTS]...) :
        animal_sequence
    env = ConceptsEnvironment(model.A, model.B; animal_sequence=seq)

    for _ in 1:length(seq)
        hist = run_trial!(
            agent,
            model,
            env,
            settings;
            learn_A=Int[],
            learn_B=Int[],
            learn_D=Int[],
            deterministic_actions=deterministic
        )
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

"""
    evaluate_distance_reporting(agent, model; trials_per_animal=20, deterministic=true, settings=...)

Evaluate accuracy on the distance question (Yes/No).
"""
function evaluate_distance_reporting(
    agent::AIFAgent,
    model::AIFModel;
    trials_per_animal::Int=20,
    animal_sequence::Union{Nothing, Vector{Int}}=nothing,
    deterministic::Bool=true,
    settings::AIFSettings=concepts_settings(eta_A=0.0, eta_B=0.0, eta_D=0.0)
)
    total = 0
    correct = 0
    incorrect = 0

    seq = isnothing(animal_sequence) ?
        vcat([fill(a, trials_per_animal) for a in 1:N_CONCEPTS]...) :
        animal_sequence
    env = ConceptsEnvironment(model.A, model.B; animal_sequence=seq)

    for _ in 1:length(seq)
        hist = run_trial!(
            agent,
            model,
            env,
            settings;
            learn_A=Int[],
            learn_B=Int[],
            learn_D=Int[],
            deterministic_actions=deterministic
        )
        animal_idx = env.current_state[1]
        report_action = hist.actions[1][2]
        result = classify_distance_report(animal_idx, report_action)
        total += 1
        if result == :correct
            correct += 1
        elseif result == :incorrect
            incorrect += 1
        end
    end

    return (
        total=total,
        correct=correct,
        incorrect=incorrect,
        acc=correct / total
    )
end
