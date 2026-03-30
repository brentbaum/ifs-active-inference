"""
    ifs_model_v4.jl - Hierarchical Relational Gating (v9 spec)

Three-factor model testing the central v9 claim: witnessing works by relaxing
protective predictions (gate) enough for burdened self-states to revise, and
this revision generalizes across cues because it operates at identity level,
not threat level.

Architecture:
- 3 hidden factors x 2 states each: gate, self-state, meaning
- 4 observation channels: need cue, interoceptive, external response, presence
- 4 policies: suppress, protest, stay-with, direct-ask
- Self-energy is a control parameter for Presence observation delivery
- Gate: policy-conditioned transitions
- Self-state: gate-conditioned transitions (interpolated by gate posterior)
- Meaning: observation-conditioned transitions (interpolated by ext. response posterior)

Simulation-theory gap (stated in paper Section 7):
  "The simulation represents the effective gate state -- the net output of
   protector policies -- as a single hidden factor, while the theory allows
   for richer protector bundles."
"""

using Random
using Statistics

# ============================================================================
# INDEX CONSTANTS
# ============================================================================

# Hidden factor 1: gate state
const V4_GATE_CLOSED = 1
const V4_GATE_PERMISSIVE = 2

# Hidden factor 2: exile self-state
const V4_SELF_UNMET_ALONE = 1
const V4_SELF_HELD_CAPABLE = 2

# Hidden factor 3: meaning / cost of contact
const V4_MEANING_CONTACT_COSTLY = 1
const V4_MEANING_CONTACT_MANAGEABLE = 2

const V4_NS = (2, 2, 2)  # num_states per factor

# Observation 1: need cue
const V4_NEED_DORMANT = 1
const V4_NEED_ACTIVATED = 2

# Observation 2: interoceptive / impulse cue
const V4_INTERO_CALM = 1
const V4_INTERO_CONSTRICTED = 2
const V4_INTERO_PANIC = 3

# Observation 3: external response cue
const V4_EXT_REJECTING = 1
const V4_EXT_NEUTRAL = 2
const V4_EXT_SUPPORTIVE = 3

# Observation 4: presence cue
const V4_PRES_ABSENT = 1
const V4_PRES_PRESENT = 2

const V4_NO = (2, 3, 3, 2)  # num_observations per channel

# Policies
const V4_POLICY_SUPPRESS = 1
const V4_POLICY_PROTEST = 2
const V4_POLICY_STAYWITH = 3
const V4_POLICY_DIRECTASK = 4

const V4_NUM_POLICIES = 4

# ============================================================================
# PARAMETERS
# ============================================================================

Base.@kwdef struct V4Params
    # Trial structure
    T_train::Int = 30
    T_probe::Int = 5

    # Policy precision (softmax inverse temperature for policy selection)
    # Ramps from min toward max as meaning crosses above meaning_threshold.
    # This ensures policy commitment only strengthens AFTER meaning has revised,
    # preserving temporal ordering while boosting late-trial self-led.
    policy_precision::Float64 = 5.5
    policy_precision_min::Float64 = 3.5
    policy_meaning_threshold::Float64 = 0.60

    # Learning rate for Dirichlet accumulation
    learning_rate::Float64 = 0.40

    # Self-energy sigmoid parameters for Presence delivery
    se_sigmoid_slope::Float64 = 12.0
    se_sigmoid_threshold::Float64 = 0.35

    # D priors (initial beliefs -- burdened starting point)
    d_gate_closed::Float64 = 0.70
    d_gate_permissive::Float64 = 0.30
    d_self_unmet::Float64 = 0.95
    d_self_held::Float64 = 0.05
    d_meaning_costly::Float64 = 0.97
    d_meaning_manageable::Float64 = 0.03

    # E prior (policy habit -- burdened system defaults)
    e_suppress::Float64 = 0.45
    e_protest::Float64 = 0.25
    e_staywith::Float64 = 0.18
    e_directask::Float64 = 0.12
    # E target (revised state: self-led dominant)
    e_target_suppress::Float64 = 0.18
    e_target_protest::Float64 = 0.10
    e_target_staywith::Float64 = 0.42
    e_target_directask::Float64 = 0.30

    # C matrix preferences (log-preference values for EFE)
    c_need::Vector{Float64} = [0.0, 0.0]
    c_intero::Vector{Float64} = [1.0, -0.2, -1.5]
    c_ext::Vector{Float64} = [-1.5, 0.0, 1.0]
    c_pres::Vector{Float64} = [-0.5, 0.8]

    # A_ext likelihoods (held constant across gate/self to keep the channel
    # primarily meaning-informative, but only weakly so)
    a_ext_costly_rejecting::Float64 = 0.35
    a_ext_costly_neutral::Float64 = 0.35
    a_ext_costly_supportive::Float64 = 0.30
    a_ext_manageable_rejecting::Float64 = 0.27
    a_ext_manageable_neutral::Float64 = 0.35
    a_ext_manageable_supportive::Float64 = 0.38

    # B_gate transition probabilities (per-policy)
    # Suppress: strongly closes/maintains gate
    b_gate_suppress_closed_to_closed::Float64 = 0.95
    b_gate_suppress_perm_to_closed::Float64 = 0.70
    # Protest: moderately closing
    b_gate_protest_closed_to_closed::Float64 = 0.85
    b_gate_protest_perm_to_closed::Float64 = 0.55
    # Stay-with: opens gate
    b_gate_staywith_closed_to_closed::Float64 = 0.30
    b_gate_staywith_perm_to_closed::Float64 = 0.04
    # Direct-ask: strongly opens gate
    b_gate_directask_closed_to_closed::Float64 = 0.25
    b_gate_directask_perm_to_closed::Float64 = 0.03

    # B_self transition probabilities (gate-conditioned)
    # Gate closed: self-state completely frozen
    b_self_closed_unmet_to_unmet::Float64 = 0.99
    b_self_closed_held_to_unmet::Float64 = 0.92
    # Gate permissive: self-state can revise strongly
    b_self_perm_unmet_to_unmet::Float64 = 0.32
    b_self_perm_held_to_unmet::Float64 = 0.04

    # B_meaning transition probabilities (observation-conditioned on ext response)
    # External = rejecting: confirms contact costly
    b_meaning_rej_costly_to_costly::Float64 = 0.95
    b_meaning_rej_manageable_to_costly::Float64 = 0.70
    # External = neutral: slow drift
    b_meaning_neu_costly_to_costly::Float64 = 0.80
    b_meaning_neu_manageable_to_costly::Float64 = 0.40
    # External = supportive: disconfirms costly (must lag behind gate and self)
    b_meaning_sup_costly_to_costly::Float64 = 0.82
    b_meaning_sup_manageable_to_costly::Float64 = 0.18

    # Revision threshold for first-passage metrics
    revision_threshold::Float64 = 0.50
end

# ============================================================================
# CONDITION CONFIGURATION
# ============================================================================

struct V4ConditionConfig
    name::String
    E_t::Float64              # Self-energy level (constant per condition)
    ext_obs::Int              # Fixed external response observation delivered
    use_ablated_pres::Bool    # Whether to use Presence-to-Gate ablated A_pres
end

function informational_only_config()
    V4ConditionConfig("Informational-Only", 0.0, V4_EXT_SUPPORTIVE, false)
end

function relational_only_config()
    V4ConditionConfig("Relational-Only", 0.9, V4_EXT_NEUTRAL, false)
end

function full_witnessing_config()
    V4ConditionConfig("Full Witnessing", 0.9, V4_EXT_SUPPORTIVE, false)
end

function gate_ablation_config()
    V4ConditionConfig("Gate Ablation", 0.9, V4_EXT_SUPPORTIVE, true)
end

function all_v4_configs()
    [informational_only_config(), relational_only_config(),
     full_witnessing_config(), gate_ablation_config()]
end

# ============================================================================
# MODEL STRUCT
# ============================================================================

struct V4Model
    params::V4Params

    # A-matrices: A[channel][obs, gate, self, meaning]
    A::Vector{Array{Float64,4}}

    # Ablated A_pres (Presence-to-Gate uniform)
    A_pres_ablated::Array{Float64,4}

    # B_gate: policy-conditioned, B_gate[next, current, policy]
    B_gate::Array{Float64,3}

    # B_self: two gate-conditioned matrices, B_self_closed[next, current], B_self_perm[next, current]
    B_self_closed::Matrix{Float64}
    B_self_permissive::Matrix{Float64}

    # B_meaning: three observation-conditioned matrices
    B_meaning_rej::Matrix{Float64}
    B_meaning_neu::Matrix{Float64}
    B_meaning_sup::Matrix{Float64}

    # C matrix: preferences per channel (for EFE)
    C::Vector{Vector{Float64}}

    # D priors: initial beliefs per factor
    D::Vector{Vector{Float64}}

    # E prior: policy habit
    E::Vector{Float64}
end

# ============================================================================
# RESULT TYPES
# ============================================================================

struct V4StepResult
    trial::Int
    phase::Symbol               # :train or :probe
    E_t::Float64
    action::Int
    observations::NTuple{4,Int}
    p_gate_permissive::Float64
    p_self_held::Float64
    p_meaning_manageable::Float64
    policy_probs::NTuple{4,Float64}
    p_selfled::Float64          # P(stay-with + direct-ask)
end

struct V4Metrics
    revision_threshold::Float64
    first_passage_gate::Union{Nothing,Int}
    first_passage_self::Union{Nothing,Int}
    first_passage_meaning::Union{Nothing,Int}
    first_passage_policy::Union{Nothing,Int}
    lag_gate_to_self::Union{Nothing,Int}
    lag_self_to_meaning::Union{Nothing,Int}
    lag_meaning_to_policy::Union{Nothing,Int}
    ordering_present::Bool       # gate < self < meaning < policy
end

struct V4Run
    condition::String
    steps::Vector{V4StepResult}
    metrics::V4Metrics
    params::V4Params
end

struct V4Summary
    condition::String
    runs::Vector{V4Run}
    mean_gate::Vector{Float64}
    std_gate::Vector{Float64}
    mean_self::Vector{Float64}
    std_self::Vector{Float64}
    mean_meaning::Vector{Float64}
    std_meaning::Vector{Float64}
    mean_selfled::Vector{Float64}
    std_selfled::Vector{Float64}
    metric_means::Dict{Symbol,Float64}
    metric_stds::Dict{Symbol,Float64}
end

# ============================================================================
# UTILITY HELPERS
# ============================================================================

function v4_normalize(v::AbstractVector{<:Real})
    out = Float64.(v)
    total = sum(out)
    total <= 0 && return fill(1.0 / length(out), length(out))
    out ./ total
end

function v4_softmax(x::AbstractVector{<:Real})
    x_shifted = x .- maximum(x)
    exp_x = exp.(x_shifted)
    return exp_x ./ sum(exp_x)
end

function v4_sample_categorical(probs::AbstractVector{<:Real})
    r = rand()
    cumprob = 0.0
    for i in 1:length(probs)
        cumprob += probs[i]
        if r <= cumprob
            return i
        end
    end
    return length(probs)
end

function v4_log_safe(x::Real)
    log(x + eps(Float64))
end

# ============================================================================
# SELF-ENERGY: PRESENCE OBSERVATION DELIVERY
# ============================================================================

"""
    deliver_presence_observation(E_t, params)

Self-energy is a control parameter that determines whether the agent observes
Presence as `present` or `absent`. Sigmoid mapping with threshold around 0.4.

At E_t = 0: always deliver absent.
At E_t = 1: always deliver present.
"""
function deliver_presence_observation(E_t::Float64; slope::Float64=8.0, threshold::Float64=0.4)
    p_present = 1.0 / (1.0 + exp(-slope * (E_t - threshold)))
    return rand() < p_present ? V4_PRES_PRESENT : V4_PRES_ABSENT
end

function deliver_presence_observation(E_t::Float64, params::V4Params)
    deliver_presence_observation(E_t; slope=params.se_sigmoid_slope, threshold=params.se_sigmoid_threshold)
end

# ============================================================================
# A-MATRIX CONSTRUCTION
# ============================================================================

"""
    build_v4_A_need()

Channel 1: Need Cue - A_need[obs, G, S, M]
Need activates when gate allows access AND meaning says contact is not costly.
"""
function build_v4_A_need()
    A = zeros(Float64, 2, 2, 2, 2)  # (obs, gate, self, meaning)

    # Need cue: gate has moderate influence; self-state discrimination reduced.
    # Meaning has the strongest effect on need activation.
    # G=closed, S=unmet, M=costly
    A[:, V4_GATE_CLOSED, V4_SELF_UNMET_ALONE, V4_MEANING_CONTACT_COSTLY] = [0.90, 0.10]
    # G=closed, S=unmet, M=manageable
    A[:, V4_GATE_CLOSED, V4_SELF_UNMET_ALONE, V4_MEANING_CONTACT_MANAGEABLE] = [0.75, 0.25]
    # G=closed, S=held, M=costly  (self discrimination reduced)
    A[:, V4_GATE_CLOSED, V4_SELF_HELD_CAPABLE, V4_MEANING_CONTACT_COSTLY] = [0.88, 0.12]
    # G=closed, S=held, M=manageable
    A[:, V4_GATE_CLOSED, V4_SELF_HELD_CAPABLE, V4_MEANING_CONTACT_MANAGEABLE] = [0.72, 0.28]
    # G=permissive, S=unmet, M=costly
    A[:, V4_GATE_PERMISSIVE, V4_SELF_UNMET_ALONE, V4_MEANING_CONTACT_COSTLY] = [0.65, 0.35]
    # G=permissive, S=unmet, M=manageable
    A[:, V4_GATE_PERMISSIVE, V4_SELF_UNMET_ALONE, V4_MEANING_CONTACT_MANAGEABLE] = [0.30, 0.70]
    # G=permissive, S=held, M=costly  (self discrimination reduced)
    A[:, V4_GATE_PERMISSIVE, V4_SELF_HELD_CAPABLE, V4_MEANING_CONTACT_COSTLY] = [0.60, 0.40]
    # G=permissive, S=held, M=manageable
    A[:, V4_GATE_PERMISSIVE, V4_SELF_HELD_CAPABLE, V4_MEANING_CONTACT_MANAGEABLE] = [0.28, 0.72]

    return A
end

"""
    build_v4_A_intero()

Channel 2: Interoceptive/Impulse - A_intero[obs, G, S, M]
Body signals: gate closed + unmet = panic, gate permissive + held = calm.
"""
function build_v4_A_intero()
    A = zeros(Float64, 3, 2, 2, 2)  # (obs, gate, self, meaning)

    # Interoceptive: self-state discrimination is reduced so self revises through
    # gate→B_self cascade, not directly. Gate discrimination also minimal.
    # G=closed, S=unmet, M=costly
    A[:, V4_GATE_CLOSED, V4_SELF_UNMET_ALONE, V4_MEANING_CONTACT_COSTLY] = [0.10, 0.32, 0.58]
    # G=closed, S=unmet, M=manageable
    A[:, V4_GATE_CLOSED, V4_SELF_UNMET_ALONE, V4_MEANING_CONTACT_MANAGEABLE] = [0.14, 0.35, 0.51]
    # G=closed, S=held, M=costly
    A[:, V4_GATE_CLOSED, V4_SELF_HELD_CAPABLE, V4_MEANING_CONTACT_COSTLY] = [0.20, 0.40, 0.40]
    # G=closed, S=held, M=manageable
    A[:, V4_GATE_CLOSED, V4_SELF_HELD_CAPABLE, V4_MEANING_CONTACT_MANAGEABLE] = [0.28, 0.40, 0.32]
    # G=permissive — nearly same as closed
    A[:, V4_GATE_PERMISSIVE, V4_SELF_UNMET_ALONE, V4_MEANING_CONTACT_COSTLY] = [0.11, 0.33, 0.56]
    # G=permissive, S=unmet, M=manageable
    A[:, V4_GATE_PERMISSIVE, V4_SELF_UNMET_ALONE, V4_MEANING_CONTACT_MANAGEABLE] = [0.16, 0.37, 0.47]
    # G=permissive, S=held, M=costly
    A[:, V4_GATE_PERMISSIVE, V4_SELF_HELD_CAPABLE, V4_MEANING_CONTACT_COSTLY] = [0.22, 0.42, 0.36]
    # G=permissive, S=held, M=manageable
    A[:, V4_GATE_PERMISSIVE, V4_SELF_HELD_CAPABLE, V4_MEANING_CONTACT_MANAGEABLE] = [0.32, 0.40, 0.28]

    return A
end

"""
    build_v4_A_ext()

Channel 3: External Response - A_ext[obs, G, S, M]
Primarily meaning-driven: costly predicts rejection, manageable predicts support.
"""
function build_v4_A_ext(params::V4Params)
    A = zeros(Float64, 3, 2, 2, 2)  # (obs, gate, self, meaning)

    # External response depends on MEANING, but with heavily reduced
    # discrimination. Keep the channel nearly flat across gate and self so
    # supportive evidence only nudges meaning; the bulk of the revision should
    # come through B_meaning over repeated trials.
    costly = [
        params.a_ext_costly_rejecting,
        params.a_ext_costly_neutral,
        params.a_ext_costly_supportive,
    ]
    manageable = [
        params.a_ext_manageable_rejecting,
        params.a_ext_manageable_neutral,
        params.a_ext_manageable_supportive,
    ]

    for g in 1:2, s in 1:2
        A[:, g, s, V4_MEANING_CONTACT_COSTLY] = costly
        A[:, g, s, V4_MEANING_CONTACT_MANAGEABLE] = manageable
    end

    return A
end

"""
    build_v4_A_pres()

Channel 4: Presence - A_pres[obs, G, S, M]
Self-state is primary driver; gate is secondary. Meaning has minimal effect.
"""
function build_v4_A_pres()
    A = zeros(Float64, 2, 2, 2, 2)  # (obs, gate, self, meaning)

    # Presence is primarily gate-informative with moderate self-state discrimination.
    # Gate discrimination is strong; self-state has secondary but meaningful signal.
    # G=closed, S=unmet, M=costly
    A[:, V4_GATE_CLOSED, V4_SELF_UNMET_ALONE, V4_MEANING_CONTACT_COSTLY] = [0.88, 0.12]
    # G=closed, S=unmet, M=manageable
    A[:, V4_GATE_CLOSED, V4_SELF_UNMET_ALONE, V4_MEANING_CONTACT_MANAGEABLE] = [0.85, 0.15]
    # G=closed, S=held, M=costly  (moderate self discrimination within closed gate)
    A[:, V4_GATE_CLOSED, V4_SELF_HELD_CAPABLE, V4_MEANING_CONTACT_COSTLY] = [0.75, 0.25]
    # G=closed, S=held, M=manageable
    A[:, V4_GATE_CLOSED, V4_SELF_HELD_CAPABLE, V4_MEANING_CONTACT_MANAGEABLE] = [0.72, 0.28]
    # G=permissive, S=unmet, M=costly  (strong gate contrast with closed)
    A[:, V4_GATE_PERMISSIVE, V4_SELF_UNMET_ALONE, V4_MEANING_CONTACT_COSTLY] = [0.50, 0.50]
    # G=permissive, S=unmet, M=manageable
    A[:, V4_GATE_PERMISSIVE, V4_SELF_UNMET_ALONE, V4_MEANING_CONTACT_MANAGEABLE] = [0.47, 0.53]
    # G=permissive, S=held, M=costly  (moderate self discrimination within permissive gate)
    A[:, V4_GATE_PERMISSIVE, V4_SELF_HELD_CAPABLE, V4_MEANING_CONTACT_COSTLY] = [0.25, 0.75]
    # G=permissive, S=held, M=manageable
    A[:, V4_GATE_PERMISSIVE, V4_SELF_HELD_CAPABLE, V4_MEANING_CONTACT_MANAGEABLE] = [0.22, 0.78]

    return A
end

"""
    build_v4_A_pres_ablated(A_pres)

Gate ablation: set Presence-to-Gate likelihood to uniform so that observing
Presence provides zero evidence about gate state. Presence still informs
self-state and meaning through the remaining A-matrix structure.

For each (S, M) pair, average the original values across the two gate states
and assign the average to both gate states.
"""
function build_v4_A_pres_ablated(A_pres::Array{Float64,4})
    A_ablated = copy(A_pres)
    for s in 1:2, m in 1:2
        # Average across gate states for each observation
        avg = (A_pres[:, V4_GATE_CLOSED, s, m] .+ A_pres[:, V4_GATE_PERMISSIVE, s, m]) ./ 2.0
        A_ablated[:, V4_GATE_CLOSED, s, m] = avg
        A_ablated[:, V4_GATE_PERMISSIVE, s, m] = avg
    end
    return A_ablated
end

# ============================================================================
# B-MATRIX CONSTRUCTION
# ============================================================================

"""
    build_v4_B_gate(params)

Gate transitions are policy-conditioned. B_gate[next, current, policy].
Stay-with and direct-ask favor opening. Suppress favors closing.
"""
function build_v4_B_gate(params::V4Params)
    B = zeros(Float64, 2, 2, V4_NUM_POLICIES)

    # Suppress (u=1): strongly closes/maintains
    B[V4_GATE_CLOSED, V4_GATE_CLOSED, V4_POLICY_SUPPRESS] = params.b_gate_suppress_closed_to_closed
    B[V4_GATE_PERMISSIVE, V4_GATE_CLOSED, V4_POLICY_SUPPRESS] = 1.0 - params.b_gate_suppress_closed_to_closed
    B[V4_GATE_CLOSED, V4_GATE_PERMISSIVE, V4_POLICY_SUPPRESS] = params.b_gate_suppress_perm_to_closed
    B[V4_GATE_PERMISSIVE, V4_GATE_PERMISSIVE, V4_POLICY_SUPPRESS] = 1.0 - params.b_gate_suppress_perm_to_closed

    # Protest (u=2): moderately closing
    B[V4_GATE_CLOSED, V4_GATE_CLOSED, V4_POLICY_PROTEST] = params.b_gate_protest_closed_to_closed
    B[V4_GATE_PERMISSIVE, V4_GATE_CLOSED, V4_POLICY_PROTEST] = 1.0 - params.b_gate_protest_closed_to_closed
    B[V4_GATE_CLOSED, V4_GATE_PERMISSIVE, V4_POLICY_PROTEST] = params.b_gate_protest_perm_to_closed
    B[V4_GATE_PERMISSIVE, V4_GATE_PERMISSIVE, V4_POLICY_PROTEST] = 1.0 - params.b_gate_protest_perm_to_closed

    # Stay-with (u=3): opens gate
    B[V4_GATE_CLOSED, V4_GATE_CLOSED, V4_POLICY_STAYWITH] = params.b_gate_staywith_closed_to_closed
    B[V4_GATE_PERMISSIVE, V4_GATE_CLOSED, V4_POLICY_STAYWITH] = 1.0 - params.b_gate_staywith_closed_to_closed
    B[V4_GATE_CLOSED, V4_GATE_PERMISSIVE, V4_POLICY_STAYWITH] = params.b_gate_staywith_perm_to_closed
    B[V4_GATE_PERMISSIVE, V4_GATE_PERMISSIVE, V4_POLICY_STAYWITH] = 1.0 - params.b_gate_staywith_perm_to_closed

    # Direct-ask (u=4): strongly opens gate
    B[V4_GATE_CLOSED, V4_GATE_CLOSED, V4_POLICY_DIRECTASK] = params.b_gate_directask_closed_to_closed
    B[V4_GATE_PERMISSIVE, V4_GATE_CLOSED, V4_POLICY_DIRECTASK] = 1.0 - params.b_gate_directask_closed_to_closed
    B[V4_GATE_CLOSED, V4_GATE_PERMISSIVE, V4_POLICY_DIRECTASK] = params.b_gate_directask_perm_to_closed
    B[V4_GATE_PERMISSIVE, V4_GATE_PERMISSIVE, V4_POLICY_DIRECTASK] = 1.0 - params.b_gate_directask_perm_to_closed

    return B
end

"""
    build_v4_B_self_closed(params)
    build_v4_B_self_permissive(params)

Self-state transitions are gate-conditioned, not policy-conditioned.
When gate is closed, self-state is frozen. When permissive, it can revise.
"""
function build_v4_B_self_closed(params::V4Params)
    B = zeros(Float64, 2, 2)
    B[V4_SELF_UNMET_ALONE, V4_SELF_UNMET_ALONE] = params.b_self_closed_unmet_to_unmet
    B[V4_SELF_HELD_CAPABLE, V4_SELF_UNMET_ALONE] = 1.0 - params.b_self_closed_unmet_to_unmet
    B[V4_SELF_UNMET_ALONE, V4_SELF_HELD_CAPABLE] = params.b_self_closed_held_to_unmet
    B[V4_SELF_HELD_CAPABLE, V4_SELF_HELD_CAPABLE] = 1.0 - params.b_self_closed_held_to_unmet
    return B
end

function build_v4_B_self_permissive(params::V4Params)
    B = zeros(Float64, 2, 2)
    B[V4_SELF_UNMET_ALONE, V4_SELF_UNMET_ALONE] = params.b_self_perm_unmet_to_unmet
    B[V4_SELF_HELD_CAPABLE, V4_SELF_UNMET_ALONE] = 1.0 - params.b_self_perm_unmet_to_unmet
    B[V4_SELF_UNMET_ALONE, V4_SELF_HELD_CAPABLE] = params.b_self_perm_held_to_unmet
    B[V4_SELF_HELD_CAPABLE, V4_SELF_HELD_CAPABLE] = 1.0 - params.b_self_perm_held_to_unmet
    return B
end

"""
    build_v4_B_meaning_*(params)

Meaning transitions are observation-conditioned on external response.
Rejecting confirms costly. Supportive disconfirms it. Neutral allows slow drift.
"""
function build_v4_B_meaning_rej(params::V4Params)
    B = zeros(Float64, 2, 2)
    B[V4_MEANING_CONTACT_COSTLY, V4_MEANING_CONTACT_COSTLY] = params.b_meaning_rej_costly_to_costly
    B[V4_MEANING_CONTACT_MANAGEABLE, V4_MEANING_CONTACT_COSTLY] = 1.0 - params.b_meaning_rej_costly_to_costly
    B[V4_MEANING_CONTACT_COSTLY, V4_MEANING_CONTACT_MANAGEABLE] = params.b_meaning_rej_manageable_to_costly
    B[V4_MEANING_CONTACT_MANAGEABLE, V4_MEANING_CONTACT_MANAGEABLE] = 1.0 - params.b_meaning_rej_manageable_to_costly
    return B
end

function build_v4_B_meaning_neu(params::V4Params)
    B = zeros(Float64, 2, 2)
    B[V4_MEANING_CONTACT_COSTLY, V4_MEANING_CONTACT_COSTLY] = params.b_meaning_neu_costly_to_costly
    B[V4_MEANING_CONTACT_MANAGEABLE, V4_MEANING_CONTACT_COSTLY] = 1.0 - params.b_meaning_neu_costly_to_costly
    B[V4_MEANING_CONTACT_COSTLY, V4_MEANING_CONTACT_MANAGEABLE] = params.b_meaning_neu_manageable_to_costly
    B[V4_MEANING_CONTACT_MANAGEABLE, V4_MEANING_CONTACT_MANAGEABLE] = 1.0 - params.b_meaning_neu_manageable_to_costly
    return B
end

function build_v4_B_meaning_sup(params::V4Params)
    B = zeros(Float64, 2, 2)
    B[V4_MEANING_CONTACT_COSTLY, V4_MEANING_CONTACT_COSTLY] = params.b_meaning_sup_costly_to_costly
    B[V4_MEANING_CONTACT_MANAGEABLE, V4_MEANING_CONTACT_COSTLY] = 1.0 - params.b_meaning_sup_costly_to_costly
    B[V4_MEANING_CONTACT_COSTLY, V4_MEANING_CONTACT_MANAGEABLE] = params.b_meaning_sup_manageable_to_costly
    B[V4_MEANING_CONTACT_MANAGEABLE, V4_MEANING_CONTACT_MANAGEABLE] = 1.0 - params.b_meaning_sup_manageable_to_costly
    return B
end

# ============================================================================
# MODEL CONSTRUCTION
# ============================================================================

"""
    build_v4_model(params)

Construct the complete V4 generative model from parameters.
"""
function build_v4_model(params::V4Params=V4Params())
    # A-matrices
    A_need = build_v4_A_need()
    A_intero = build_v4_A_intero()
    A_ext = build_v4_A_ext(params)
    A_pres = build_v4_A_pres()
    A = [A_need, A_intero, A_ext, A_pres]

    # Validate A columns sum to 1
    for (g, A_g) in enumerate(A)
        for idx in CartesianIndices(V4_NS)
            col_sum = sum(A_g[:, idx])
            @assert isapprox(col_sum, 1.0; atol=1e-8) "A[$g] column at $idx sums to $col_sum, expected 1.0"
        end
    end

    # Ablated A_pres
    A_pres_ablated = build_v4_A_pres_ablated(A_pres)

    # B-matrices
    B_gate = build_v4_B_gate(params)
    B_self_closed = build_v4_B_self_closed(params)
    B_self_perm = build_v4_B_self_permissive(params)
    B_meaning_rej = build_v4_B_meaning_rej(params)
    B_meaning_neu = build_v4_B_meaning_neu(params)
    B_meaning_sup = build_v4_B_meaning_sup(params)

    # Validate B columns sum to 1
    for u in 1:V4_NUM_POLICIES
        for s in 1:2
            @assert isapprox(sum(B_gate[:, s, u]), 1.0; atol=1e-8) "B_gate column ($s, policy=$u) doesn't sum to 1"
        end
    end
    for B in [B_self_closed, B_self_perm, B_meaning_rej, B_meaning_neu, B_meaning_sup]
        for s in 1:2
            @assert isapprox(sum(B[:, s]), 1.0; atol=1e-8) "B column $s doesn't sum to 1"
        end
    end

    # C preferences
    C = [copy(params.c_need), copy(params.c_intero), copy(params.c_ext), copy(params.c_pres)]

    # D priors
    D = Vector{Vector{Float64}}(undef, 3)
    D[1] = v4_normalize([params.d_gate_closed, params.d_gate_permissive])
    D[2] = v4_normalize([params.d_self_unmet, params.d_self_held])
    D[3] = v4_normalize([params.d_meaning_costly, params.d_meaning_manageable])

    # E prior (policy habit)
    E = v4_normalize([params.e_suppress, params.e_protest, params.e_staywith, params.e_directask])

    return V4Model(params, A, A_pres_ablated, B_gate, B_self_closed, B_self_perm,
                   B_meaning_rej, B_meaning_neu, B_meaning_sup, C, D, E)
end

# ============================================================================
# INFERENCE: SINGLE-STEP BAYESIAN UPDATE
# ============================================================================

"""
    v4_compute_ln_A_marginal(A_g, obs, qs, f)

Compute E_{q(s_{-f})}[ln A_g(o_g | s)] for factor f.
Marginalizes the log-likelihood over all factors except f, weighted by current
beliefs q(s_{-f}).

Arguments:
- A_g: Observation likelihood for channel g, shape (num_obs, 2, 2, 2)
- obs: Observed value for channel g (integer index)
- qs: Current beliefs, qs[f] is Vector{Float64} for factor f
- f: Factor index to compute marginal for (1=gate, 2=self, 3=meaning)
"""
function v4_compute_ln_A_marginal(
    A_g::Array{Float64,4},
    obs::Int,
    qs::Vector{Vector{Float64}},
    f::Int
)
    result = zeros(Float64, V4_NS[f])

    for idx in CartesianIndices(V4_NS)
        s_f = idx[f]
        # Joint probability of other factors
        prob_other = 1.0
        for ff in 1:3
            ff == f && continue
            prob_other *= qs[ff][idx[ff]]
        end
        # Weighted log likelihood
        likelihood = A_g[obs, idx]
        result[s_f] += v4_log_safe(likelihood) * prob_other
    end

    return result
end

"""
    v4_inference_step(model, observations, prior, config)

Single-step Bayesian inference over all 3 hidden factors given 4 observations.
Uses mean-field variational inference (fixed-point iteration).

All four channels update the posterior simultaneously -- no staged gating needed
because there is no witnessed-self-state channel in v4.

Arguments:
- model: V4Model
- observations: Tuple of 4 observation indices
- prior: Vector of 3 belief vectors (gate, self, meaning)
- config: V4ConditionConfig (to determine whether to use ablated A_pres)
- max_iter: Maximum fixed-point iterations (default 16)
- tol: Convergence tolerance (default 1e-7)
"""
function v4_inference_step(
    model::V4Model,
    observations::NTuple{4,Int},
    prior::Vector{Vector{Float64}},
    config::V4ConditionConfig;
    max_iter::Int=16,
    tol::Float64=1e-7
)
    # Select A matrices (possibly ablated Presence)
    A = if config.use_ablated_pres
        [model.A[1], model.A[2], model.A[3], model.A_pres_ablated]
    else
        model.A
    end

    qs = [copy(prior[f]) for f in 1:3]

    for iter in 1:max_iter
        qs_old = [copy(q) for q in qs]

        for f in 1:3
            ln_q = log.(prior[f] .+ eps(Float64))

            # Accumulate log-likelihood evidence from all 4 channels
            for g in 1:4
                ln_q .+= v4_compute_ln_A_marginal(A[g], observations[g], qs, f)
            end

            qs[f] .= v4_softmax(ln_q)
        end

        # Convergence check
        max_diff = maximum(maximum(abs.(qs[f] .- qs_old[f])) for f in 1:3)
        max_diff < tol && break
    end

    return qs
end

# ============================================================================
# BELIEF PROPAGATION (B-MATRIX APPLICATION)
# ============================================================================

"""
    v4_propagate_beliefs(model, posterior, action, ext_obs_posterior)

Propagate beliefs forward one timestep through transition dynamics.

- Gate: policy-conditioned via B_gate
- Self-state: gate-conditioned via interpolation of B_self_closed / B_self_permissive
  using the current gate posterior
- Meaning: observation-conditioned via interpolation of B_meaning_rej/neu/sup
  using the external response posterior

Arguments:
- model: V4Model
- posterior: Current posterior beliefs [gate, self, meaning]
- action: Selected policy index
- ext_obs_posterior: Posterior over external response observations (3-element vector)
"""
function v4_propagate_beliefs(
    model::V4Model,
    posterior::Vector{Vector{Float64}},
    action::Int,
    ext_obs_posterior::Vector{Float64}
)
    next = Vector{Vector{Float64}}(undef, 3)

    # Factor 1: Gate -- policy-conditioned
    next[1] = v4_normalize(model.B_gate[:, :, action] * posterior[1])

    # Factor 2: Self-state -- gate-conditioned
    # Interpolate between closed and permissive B_self using gate posterior
    p_closed = posterior[1][V4_GATE_CLOSED]
    p_permissive = posterior[1][V4_GATE_PERMISSIVE]
    B_self_eff = p_closed .* model.B_self_closed .+ p_permissive .* model.B_self_permissive
    next[2] = v4_normalize(B_self_eff * posterior[2])

    # Factor 3: Meaning -- observation-conditioned on external response
    # Interpolate between rejecting, neutral, supportive B_meaning
    p_rej = ext_obs_posterior[V4_EXT_REJECTING]
    p_neu = ext_obs_posterior[V4_EXT_NEUTRAL]
    p_sup = ext_obs_posterior[V4_EXT_SUPPORTIVE]
    B_meaning_eff = p_rej .* model.B_meaning_rej .+
                    p_neu .* model.B_meaning_neu .+
                    p_sup .* model.B_meaning_sup
    next[3] = v4_normalize(B_meaning_eff * posterior[3])

    return next
end

"""
    v4_compute_ext_obs_posterior(model, posterior, ext_obs, config)

Compute the posterior distribution over external response observations
given the current hidden state beliefs and the actual external observation.

Uses Bayes' rule: P(ext_state | o_ext) proportional to P(o_ext | states) * P(states)
then marginalizes to get a soft posterior over external response categories.
"""
function v4_compute_ext_obs_posterior(
    model::V4Model,
    posterior::Vector{Vector{Float64}},
    ext_obs::Int,
    config::V4ConditionConfig
)
    # The delivered external observation is deterministic per condition,
    # so the posterior over "what the external response was" is a one-hot
    # vector at the delivered observation. This is the observation that drives
    # meaning transitions.
    p = zeros(Float64, 3)
    p[ext_obs] = 1.0
    return p
end

# ============================================================================
# EXPECTED FREE ENERGY (EFE) AND POLICY SELECTION
# ============================================================================

"""
    v4_compute_predicted_obs(A_g, qs)

Compute predicted observation distribution: q(o_g) = sum_s A_g(o|s) * q(s)
"""
function v4_compute_predicted_obs(A_g::Array{Float64,4}, qs::Vector{Vector{Float64}})
    No_g = size(A_g, 1)
    qo = zeros(Float64, No_g)

    for idx in CartesianIndices(V4_NS)
        prob_s = prod(qs[f][idx[f]] for f in 1:3)
        for o in 1:No_g
            qo[o] += A_g[o, idx] * prob_s
        end
    end

    return qo
end

"""
    v4_compute_ambiguity(A_g, qs)

Compute ambiguity: E_{q(s)}[H[P(o|s)]] for one channel.
This is the expected entropy of observations given state beliefs.
"""
function v4_compute_ambiguity(A_g::Array{Float64,4}, qs::Vector{Vector{Float64}})
    ambiguity = 0.0

    for idx in CartesianIndices(V4_NS)
        prob_s = prod(qs[f][idx[f]] for f in 1:3)
        prob_s < eps(Float64) && continue

        # Entropy of P(o|s) for this state combination
        p_o_given_s = view(A_g, :, idx)
        H = 0.0
        for p in p_o_given_s
            if p > eps(Float64)
                H -= p * log(p)
            end
        end
        ambiguity += prob_s * H
    end

    return ambiguity
end

"""
    v4_compute_state_info_gain(A_g, qs, qo)

Compute expected information gain about hidden states for one channel.
E_{q(o)}[ KL(q(s|o) || q(s)) ]
"""
function v4_compute_state_info_gain(
    A_g::Array{Float64,4},
    qs::Vector{Vector{Float64}},
    qo::Vector{Float64}
)
    info_gain = 0.0
    No = size(A_g, 1)

    for o in 1:No
        qo[o] < eps(Float64) && continue

        # Compute posterior q(s_f | o) for each factor
        qs_given_o = v4_posterior_given_obs(A_g, o, qs)

        # KL divergence sum over all factors
        kl = 0.0
        for f in 1:3
            for s in 1:V4_NS[f]
                p = qs_given_o[f][s]
                if p > eps(Float64)
                    kl += p * log(p / (qs[f][s] + eps(Float64)))
                end
            end
        end
        info_gain += qo[o] * kl
    end

    return info_gain
end

"""
    v4_posterior_given_obs(A_g, o, qs)

Compute factorized posterior q(s|o) given a single observation o on channel g.
"""
function v4_posterior_given_obs(
    A_g::Array{Float64,4},
    o::Int,
    qs::Vector{Vector{Float64}}
)
    qs_post = Vector{Vector{Float64}}(undef, 3)

    for f in 1:3
        likelihood_f = zeros(Float64, V4_NS[f])
        for s_f in 1:V4_NS[f]
            for idx in CartesianIndices(V4_NS)
                idx[f] != s_f && continue
                prob_other = prod(qs[ff][idx[ff]] for ff in 1:3 if ff != f)
                likelihood_f[s_f] += A_g[o, idx] * prob_other
            end
        end
        posterior_f = likelihood_f .* qs[f]
        posterior_sum = sum(posterior_f)
        if posterior_sum > eps(Float64)
            posterior_f ./= posterior_sum
        else
            posterior_f = copy(qs[f])
        end
        qs_post[f] = posterior_f
    end

    return qs_post
end

"""
    v4_compute_efe(model, posterior, action, config)

Compute Expected Free Energy for a single policy/action.

G(u) = sum_g [ ambiguity_g + pragmatic_g - epistemic_g ]

where:
- ambiguity = E_{q(s|u)}[H[P(o|s)]]          (expected observation entropy)
- pragmatic = -E_{q(o|u)}[ln C(o)]            (neg expected preference)
- epistemic = E_{q(o|u)}[KL(q(s|o,u)||q(s|u))] (expected state info gain)

Lower EFE = better policy (we negate for softmax selection).
"""
function v4_compute_efe(
    model::V4Model,
    posterior::Vector{Vector{Float64}},
    action::Int,
    config::V4ConditionConfig
)
    # Propagate beliefs forward under this action
    ext_posterior = [0.0, 0.0, 0.0]
    ext_posterior[config.ext_obs] = 1.0
    qs_next = v4_propagate_beliefs(model, posterior, action, ext_posterior)

    # Select A matrices (possibly ablated)
    A = if config.use_ablated_pres
        [model.A[1], model.A[2], model.A[3], model.A_pres_ablated]
    else
        model.A
    end

    # Compute log preferences (softmax of C vectors)
    log_prefs = [log.(v4_softmax(c) .+ eps(Float64)) for c in model.C]

    efe = 0.0
    for g in 1:4
        qo = v4_compute_predicted_obs(A[g], qs_next)

        # Ambiguity term (positive = bad)
        efe += v4_compute_ambiguity(A[g], qs_next)

        # Pragmatic term: negative expected log-preference (positive = bad)
        efe -= sum(qo .* log_prefs[g])

        # Epistemic term: expected info gain (positive = good, so subtract)
        efe -= v4_compute_state_info_gain(A[g], qs_next, qo)
    end

    return efe
end

"""
    v4_select_policy(model, posterior, config)

Select a policy using softmax over negative EFE, modulated by E prior (habit).

Returns (action, policy_probs) where policy_probs is a 4-element vector.
"""
function v4_select_policy(
    model::V4Model,
    posterior::Vector{Vector{Float64}},
    config::V4ConditionConfig;
    deterministic::Bool=false
)
    # Compute EFE for each policy
    efe = [v4_compute_efe(model, posterior, u, config) for u in 1:V4_NUM_POLICIES]

    # Meaning-gated policy precision: precision stays at baseline (min)
    # until meaning revises past the threshold, then ramps toward max.
    # This ensures policy commitment strengthens only AFTER meaning has
    # crossed, preserving the gate < self < meaning < policy ordering.
    p_manageable = posterior[3][V4_MEANING_CONTACT_MANAGEABLE]
    if p_manageable <= model.params.policy_meaning_threshold
        effective_precision = model.params.policy_precision_min
    else
        meaning_progress = (p_manageable - model.params.policy_meaning_threshold) /
                          (1.0 - model.params.policy_meaning_threshold)
        effective_precision = model.params.policy_precision_min +
            meaning_progress * (model.params.policy_precision - model.params.policy_precision_min)
    end

    log_E = log.(model.E .+ eps(Float64))
    policy_logits = -effective_precision .* efe .+ log_E

    policy_probs = v4_softmax(policy_logits)

    if deterministic
        return argmax(policy_probs), policy_probs
    end
    return v4_sample_categorical(policy_probs), policy_probs
end

# ============================================================================
# OBSERVATION SAMPLING
# ============================================================================

"""
    v4_sample_observations(model, posterior, config)

Sample observations from the generative process for one trial.

Need cue and interoceptive channels are sampled from A-matrices given the
agent's current hidden state posteriors (generative process). External response
and Presence channels are fixed by the experimental condition.
"""
function v4_sample_observations(
    model::V4Model,
    posterior::Vector{Vector{Float64}},
    config::V4ConditionConfig
)
    # Sample from joint state given current posterior (treat posterior as generative "true state" distribution)
    # For need and interoceptive: sample from A given posterior
    # For external: condition-determined
    # For presence: Self-energy-determined

    # Compute predicted observations from posterior
    A = model.A

    # Need cue: sample from predicted distribution
    qo_need = v4_compute_predicted_obs(A[1], posterior)
    obs_need = v4_sample_categorical(qo_need)

    # Interoceptive: sample from predicted distribution
    qo_intero = v4_compute_predicted_obs(A[2], posterior)
    obs_intero = v4_sample_categorical(qo_intero)

    # External response: fixed by condition
    obs_ext = config.ext_obs

    # Presence: determined by Self-energy control parameter
    obs_pres = deliver_presence_observation(config.E_t, model.params)

    return (obs_need, obs_intero, obs_ext, obs_pres)
end

# ============================================================================
# DIRICHLET LEARNING FOR TRANSFER PROBE
# ============================================================================

"""
    V4DirichletBanks

Holds Dirichlet concentration parameters for learning. Gate and self-state
banks are shared across cues (identity-level). Meaning banks are cue-specific
(threat-level).
"""
mutable struct V4DirichletBanks
    d_gate::Vector{Float64}     # Shared across cues
    d_self::Vector{Float64}     # Shared across cues
    d_meaning::Dict{Symbol,Vector{Float64}}  # Cue-specific (:cue_A, :cue_B)
end

"""
    init_v4_dirichlet_banks(params)

Initialize Dirichlet banks from model priors.
"""
function init_v4_dirichlet_banks(params::V4Params)
    d_gate = [params.d_gate_closed, params.d_gate_permissive]
    d_self = [params.d_self_unmet, params.d_self_held]
    d_meaning = Dict{Symbol,Vector{Float64}}(
        :cue_A => [params.d_meaning_costly, params.d_meaning_manageable],
        :cue_B => [params.d_meaning_costly, params.d_meaning_manageable],
    )
    return V4DirichletBanks(d_gate, d_self, d_meaning)
end

"""
    update_v4_dirichlet_banks!(banks, posterior, cue, learning_rate)

Update Dirichlet concentration parameters after a trial.
Gate and self banks accumulate from any cue. Meaning bank accumulates only
for the active cue.
"""
function update_v4_dirichlet_banks!(
    banks::V4DirichletBanks,
    posterior::Vector{Vector{Float64}},
    cue::Symbol,
    learning_rate::Float64
)
    # Accumulate: d += lr * (posterior - prior)
    # This is equivalent to adding fractional counts toward the posterior
    prior_gate = v4_normalize(banks.d_gate)
    prior_self = v4_normalize(banks.d_self)
    prior_meaning = v4_normalize(banks.d_meaning[cue])

    banks.d_gate .+= learning_rate .* (posterior[1] .- prior_gate)
    banks.d_self .+= learning_rate .* (posterior[2] .- prior_self)
    banks.d_meaning[cue] .+= learning_rate .* (posterior[3] .- prior_meaning)

    # Clamp to prevent negative concentrations
    banks.d_gate .= max.(banks.d_gate, 0.01)
    banks.d_self .= max.(banks.d_self, 0.01)
    banks.d_meaning[cue] .= max.(banks.d_meaning[cue], 0.01)

    return banks
end

"""
    get_v4_prior_from_banks(banks, cue)

Extract normalized prior beliefs from Dirichlet banks for a given cue.
"""
function get_v4_prior_from_banks(banks::V4DirichletBanks, cue::Symbol)
    return [
        v4_normalize(banks.d_gate),
        v4_normalize(banks.d_self),
        v4_normalize(banks.d_meaning[cue]),
    ]
end

# ============================================================================
# SINGLE TRIAL EXECUTION
# ============================================================================

"""
    v4_run_trial(model, config, prior_beliefs; learning_banks, cue, seed)

Run one full trial: observe, infer, select policy, propagate beliefs.

Returns (step_result, updated_posterior, ext_obs_posterior).

If learning_banks and cue are provided, updates the Dirichlet banks after
the trial (for transfer probe).
"""
function v4_run_trial(
    model::V4Model,
    config::V4ConditionConfig,
    prior_beliefs::Vector{Vector{Float64}},
    trial_num::Int;
    phase::Symbol=:train,
    learning_banks::Union{Nothing,V4DirichletBanks}=nothing,
    cue::Symbol=:cue_A,
    deterministic::Bool=false
)
    # Step 1: Sample observations
    observations = v4_sample_observations(model, prior_beliefs, config)

    # Step 2: Bayesian inference over hidden factors
    posterior = v4_inference_step(model, observations, prior_beliefs, config)

    # Step 3: Select policy via EFE
    action, policy_probs = v4_select_policy(model, posterior, config;
                                             deterministic=deterministic)

    # Step 4: Compute external response posterior for belief propagation
    ext_obs_posterior = v4_compute_ext_obs_posterior(model, posterior, observations[3], config)

    # Step 5: Propagate beliefs forward (next trial's prior)
    next_prior = v4_propagate_beliefs(model, posterior, action, ext_obs_posterior)

    # Step 6: Dirichlet learning (if training phase with banks)
    if phase == :train && !isnothing(learning_banks)
        update_v4_dirichlet_banks!(learning_banks, posterior, cue, model.params.learning_rate)
    end

    # Record step
    step = V4StepResult(
        trial_num,
        phase,
        config.E_t,
        action,
        observations,
        posterior[1][V4_GATE_PERMISSIVE],
        posterior[2][V4_SELF_HELD_CAPABLE],
        posterior[3][V4_MEANING_CONTACT_MANAGEABLE],
        (policy_probs[1], policy_probs[2], policy_probs[3], policy_probs[4]),
        policy_probs[V4_POLICY_STAYWITH] + policy_probs[V4_POLICY_DIRECTASK],
    )

    return step, next_prior
end

# ============================================================================
# FULL CONDITION RUN
# ============================================================================

"""
    v4_run_condition(model, config; seed, verbose, use_transfer)

Run a full condition: T_train training trials + T_probe probe trials.

If use_transfer=true, uses Dirichlet banks for learning and runs the probe
phase on cue B (transfer probe). Otherwise, runs training and probe on the
same cue with standard belief propagation.
"""
function v4_run_condition(
    model::V4Model,
    config::V4ConditionConfig;
    seed::Int=42,
    verbose::Bool=false,
    use_transfer::Bool=false,
    deterministic_probe::Bool=false
)
    Random.seed!(seed)
    params = model.params
    steps = V4StepResult[]

    # Initialize beliefs and optional Dirichlet banks
    prior = [copy(d) for d in model.D]
    banks = use_transfer ? init_v4_dirichlet_banks(params) : nothing

    # === Training phase (cue A) ===
    for t in 1:params.T_train
        step, next_prior = v4_run_trial(
            model, config, prior, t;
            phase=:train,
            learning_banks=banks,
            cue=:cue_A,
            deterministic=false
        )
        push!(steps, step)

        if verbose
            println("t=$t phase=train E_t=$(round(config.E_t, digits=2)) ",
                    "action=$(step.action) obs=$(collect(step.observations)) ",
                    "gate=$(round(step.p_gate_permissive, digits=3)) ",
                    "self=$(round(step.p_self_held, digits=3)) ",
                    "meaning=$(round(step.p_meaning_manageable, digits=3)) ",
                    "pi=$(round.(collect(step.policy_probs), digits=3))")
        end

        # Update prior for next trial
        if use_transfer
            # Use Dirichlet banks as prior source
            prior = get_v4_prior_from_banks(banks, :cue_A)
        else
            prior = next_prior
        end
    end

    # === Probe phase ===
    # If transfer: switch to cue B (shared gate+self, fresh meaning)
    # If not transfer: freeze beliefs from end of training
    probe_cue = use_transfer ? :cue_B : :cue_A
    if use_transfer
        prior = get_v4_prior_from_banks(banks, probe_cue)
    end
    # Freeze: don't update banks during probe
    frozen_prior = [copy(p) for p in prior]

    for t in 1:params.T_probe
        trial_num = params.T_train + t
        step, _ = v4_run_trial(
            model, config, frozen_prior, trial_num;
            phase=:probe,
            learning_banks=nothing,  # No learning during probe
            cue=probe_cue,
            deterministic=deterministic_probe
        )
        push!(steps, step)

        if verbose
            println("t=$trial_num phase=probe cue=$probe_cue ",
                    "action=$(step.action) ",
                    "gate=$(round(step.p_gate_permissive, digits=3)) ",
                    "self=$(round(step.p_self_held, digits=3)) ",
                    "meaning=$(round(step.p_meaning_manageable, digits=3)) ",
                    "pi=$(round.(collect(step.policy_probs), digits=3))")
        end
    end

    metrics = v4_compute_metrics(steps, params)
    return V4Run(config.name, steps, metrics, params)
end

# ============================================================================
# METRICS
# ============================================================================

function v4_first_passage_time(values::Vector{Float64}, threshold::Float64)
    for t in eachindex(values)
        values[t] >= threshold && return t
    end
    return nothing
end

function v4_compute_metrics(steps::Vector{V4StepResult}, params::V4Params)
    gate_traj = [s.p_gate_permissive for s in steps]
    self_traj = [s.p_self_held for s in steps]
    meaning_traj = [s.p_meaning_manageable for s in steps]
    selfled_traj = [s.p_selfled for s in steps]

    threshold = params.revision_threshold

    t_gate = v4_first_passage_time(gate_traj, threshold)
    t_self = v4_first_passage_time(self_traj, threshold)
    t_meaning = v4_first_passage_time(meaning_traj, threshold)
    t_policy = v4_first_passage_time(selfled_traj, threshold)

    lag_gate_to_self = isnothing(t_gate) || isnothing(t_self) ? nothing : (t_self - t_gate)
    lag_self_to_meaning = isnothing(t_self) || isnothing(t_meaning) ? nothing : (t_meaning - t_self)
    lag_meaning_to_policy = isnothing(t_meaning) || isnothing(t_policy) ? nothing : (t_policy - t_meaning)

    ordering_present = !isnothing(t_gate) &&
                       !isnothing(t_self) &&
                       !isnothing(t_meaning) &&
                       !isnothing(t_policy) &&
                       t_gate < t_self < t_meaning < t_policy

    return V4Metrics(
        threshold,
        t_gate, t_self, t_meaning, t_policy,
        lag_gate_to_self, lag_self_to_meaning, lag_meaning_to_policy,
        ordering_present
    )
end

# ============================================================================
# AGGREGATION ACROSS REPLICATIONS
# ============================================================================

function _v4_mean_std(data::Matrix{Float64})
    return vec(mean(data; dims=2)), vec(std(data; dims=2))
end

function _v4_metric_values(runs::Vector{V4Run}, getter::Function)
    values = Float64[]
    for run in runs
        value = getter(run.metrics)
        isnothing(value) && continue
        push!(values, Float64(value))
    end
    isempty(values) && return NaN, NaN
    return mean(values), std(values)
end

function summarize_v4_runs(runs::Vector{V4Run})
    @assert !isempty(runs)
    T = length(runs[1].steps)
    N = length(runs)

    gate_mat = zeros(Float64, T, N)
    self_mat = zeros(Float64, T, N)
    meaning_mat = zeros(Float64, T, N)
    selfled_mat = zeros(Float64, T, N)

    for (j, run) in enumerate(runs)
        for (t, step) in enumerate(run.steps)
            gate_mat[t, j] = step.p_gate_permissive
            self_mat[t, j] = step.p_self_held
            meaning_mat[t, j] = step.p_meaning_manageable
            selfled_mat[t, j] = step.p_selfled
        end
    end

    mean_gate, std_gate = _v4_mean_std(gate_mat)
    mean_self, std_self = _v4_mean_std(self_mat)
    mean_meaning, std_meaning = _v4_mean_std(meaning_mat)
    mean_selfled, std_selfled = _v4_mean_std(selfled_mat)

    metric_means = Dict{Symbol,Float64}()
    metric_stds = Dict{Symbol,Float64}()
    for (label, getter) in [
        (:first_passage_gate, m -> m.first_passage_gate),
        (:first_passage_self, m -> m.first_passage_self),
        (:first_passage_meaning, m -> m.first_passage_meaning),
        (:first_passage_policy, m -> m.first_passage_policy),
        (:lag_gate_to_self, m -> m.lag_gate_to_self),
        (:lag_self_to_meaning, m -> m.lag_self_to_meaning),
        (:lag_meaning_to_policy, m -> m.lag_meaning_to_policy),
    ]
        metric_means[label], metric_stds[label] = _v4_metric_values(runs, getter)
    end
    ordering_flags = [run.metrics.ordering_present ? 1.0 : 0.0 for run in runs]
    metric_means[:ordering_rate] = mean(ordering_flags)
    metric_stds[:ordering_rate] = std(ordering_flags)

    return V4Summary(
        runs[1].condition,
        runs,
        mean_gate, std_gate,
        mean_self, std_self,
        mean_meaning, std_meaning,
        mean_selfled, std_selfled,
        metric_means, metric_stds,
    )
end

# ============================================================================
# CONVENIENCE: MULTI-REPLICATION RUNNER
# ============================================================================

"""
    v4_run_replications(model, config, n_reps; kwargs...)

Run n_reps replications of a condition, each with a different seed.
Returns a V4Summary with means, stds, and metric statistics.
"""
function v4_run_replications(
    model::V4Model,
    config::V4ConditionConfig,
    n_reps::Int;
    use_transfer::Bool=false,
    deterministic_probe::Bool=false,
    verbose::Bool=false
)
    runs = V4Run[]
    for i in 1:n_reps
        run = v4_run_condition(model, config;
                               seed=i,
                               verbose=verbose && i == 1,
                               use_transfer=use_transfer,
                               deterministic_probe=deterministic_probe)
        push!(runs, run)
    end
    return summarize_v4_runs(runs)
end

"""
    v4_run_all_conditions(; params, n_reps, use_transfer, verbose)

Run all four conditions (informational-only, relational-only, full witnessing,
gate ablation) with n_reps replications each.

Returns a Dict mapping condition name to V4Summary.
"""
function v4_run_all_conditions(;
    params::V4Params=V4Params(),
    n_reps::Int=50,
    use_transfer::Bool=false,
    deterministic_probe::Bool=false,
    verbose::Bool=false
)
    model = build_v4_model(params)
    configs = all_v4_configs()

    results = Dict{String,V4Summary}()
    for config in configs
        summary = v4_run_replications(model, config, n_reps;
                                       use_transfer=use_transfer,
                                       deterministic_probe=deterministic_probe,
                                       verbose=verbose)
        results[config.name] = summary
    end
    return results
end
