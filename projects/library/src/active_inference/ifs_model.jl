"""
    ifs_model.jl - IFS Parts/Self-Energy Active Inference Model

Implements the H1/H2 model comparison for the IFS-Active Inference paper.
Tests whether Self-energy determines blending vs witnessing, and whether
only witnessing permits durable revision of part beliefs.

Architecture:
- 3 hidden factors: context (safe/dangerous), self-state (child_helpless/adult_capable),
  threat meaning (danger/safe)
- 4 observation modalities: external cue, interoceptive arousal, outcome,
  present-context support
- 3 policies: avoid, inspect, stay
- Self-energy precision modulation with capture index

Two causal hypotheses:
- H1 (self-state-upstream): o_ctx -> s -> m -> policy
- H2 (threat-primary): o_ext, o_int -> m -> s -> policy
"""

using Random
using Statistics

# ============================================================================
# INDEX CONSTANTS
# ============================================================================

# Factor 1: context (Ns1 = 2)
const IFS_CTX_SAFE = 1
const IFS_CTX_DANGEROUS = 2

# Factor 2: self-state (Ns2 = 2)
const IFS_SELF_CHILD_HELPLESS = 1
const IFS_SELF_ADULT_CAPABLE = 2

# Factor 3: threat meaning (Ns3 = 2)
const IFS_THREAT_DANGER = 1
const IFS_THREAT_SAFE = 2

# Observation 1: external cue (No1 = 3)
const IFS_EXT_AMBIGUOUS = 1
const IFS_EXT_CLEAR_SAFE = 2
const IFS_EXT_CLEAR_THREAT = 3

# Observation 2: interoceptive arousal (No2 = 3)
const IFS_INT_CALM = 1
const IFS_INT_ACTIVATED = 2
const IFS_INT_PANIC = 3

# Observation 3: outcome (No3 = 3)
const IFS_OUT_RELIEF = 1
const IFS_OUT_NEUTRAL = 2
const IFS_OUT_HARM = 3

# Observation 4: present-context support (No4 = 2)
const IFS_CTX_ALONE_OVERWHELMED = 1
const IFS_CTX_SUPPORTED_HERE_NOW = 2

# Policy indices
const IFS_POLICY_AVOID = 1
const IFS_POLICY_INSPECT = 2
const IFS_POLICY_STAY = 3

# Condition IDs
const IFS_COND_BASELINE = 1
const IFS_COND_EXPOSURE = 2
const IFS_COND_WITNESSING = 3
const IFS_COND_REAL_DANGER = 4
const IFS_COND_DISSOCIATION = 5

# ============================================================================
# MODEL PARAMETERS
# ============================================================================

Base.@kwdef struct IFSModelParams
    # Trial structure
    T::Int = 3                          # Timesteps per trial (cue, action, outcome)

    # Agent hyperparameters
    gamma::Float64 = 4.0               # Policy precision
    alpha::Float64 = 8.0               # Action precision

    # Self-energy parameters
    beta_se::Float64 = 2.5             # Part precision decay rate with Self-energy
    gamma_se::Float64 = 2.5            # Context precision growth rate with Self-energy

    # Part bundle parameters
    pi_part::Float64 = 8.0             # Base part prior precision
    lambda_ctx::Float64 = 2.0          # Base context evidence precision
    r_t::Float64 = 0.8                 # Part activation strength

    # Initial priors (Dirichlet concentrations)
    d_self_helpless::Float64 = 20.0    # Prior on child_helpless
    d_self_capable::Float64 = 2.0      # Prior on adult_capable
    d_threat_danger::Float64 = 20.0    # Prior on danger
    d_threat_safe::Float64 = 2.0       # Prior on safe

    # Learning rate: scaled by Self-energy modulation
    eta_D_base::Float64 = 1.0          # Base D learning rate
end

# ============================================================================
# SELF-ENERGY AND CAPTURE INDEX
# ============================================================================

"""
    compute_effective_precisions(params, E_t)

Compute effective part and context precisions given Self-energy.

    pi_part_eff = r_t * pi_part * exp(-beta * E_t)
    lambda_ctx_eff = lambda_ctx * exp(+gamma * E_t)
"""
function compute_effective_precisions(params::IFSModelParams, E_t::Float64)
    pi_part_eff = params.r_t * params.pi_part * exp(-params.beta_se * E_t)
    lambda_ctx_eff = params.lambda_ctx * exp(params.gamma_se * E_t)
    return pi_part_eff, lambda_ctx_eff
end

"""
    compute_capture_index(params, E_t)

Compute capture index C_t = pi_part_eff / (pi_part_eff + lambda_ctx_eff).

C_t near 1 = blending (part captures inference)
C_t near 0 = witnessing (context holds part in awareness)
"""
function compute_capture_index(params::IFSModelParams, E_t::Float64)
    pi_eff, lambda_eff = compute_effective_precisions(params, E_t)
    return pi_eff / (pi_eff + lambda_eff)
end

# ============================================================================
# CONDITION CONFIGURATION
# ============================================================================

"""
    IFSConditionConfig

Configuration for a simulation condition.
"""
struct IFSConditionConfig
    name::String
    world_dangerous::Bool       # True context
    E_t::Float64               # Self-energy level
    forced_policy::Int          # 0 = free, 1-3 = forced policy
    context_precision_scale::Float64  # Multiplier on context precision (for dissociation)
end

"""Standard condition configurations."""
function baseline_ifs_config()
    IFSConditionConfig("Baseline", false, 0.1, 0, 1.0)
end

function exposure_ifs_config()
    IFSConditionConfig("Exposure", false, 0.15, IFS_POLICY_INSPECT, 1.0)
end

function witnessing_ifs_config()
    IFSConditionConfig("Witnessing", false, 0.85, IFS_POLICY_INSPECT, 1.0)
end

function real_danger_ifs_config()
    IFSConditionConfig("Real Danger", true, 0.85, 0, 1.0)
end

function dissociation_ifs_config()
    IFSConditionConfig("Dissociation", false, 0.1, 0, 0.15)
end

function all_ifs_configs()
    [baseline_ifs_config(), exposure_ifs_config(), witnessing_ifs_config(),
     real_danger_ifs_config(), dissociation_ifs_config()]
end

# ============================================================================
# A MATRIX CONSTRUCTION
# ============================================================================

"""
    build_ifs_A_h1(params) -> Vector{Array{Float64}}

Build observation likelihood matrices for H1 (self-state-upstream).

H1 structure:
- o_ctx primarily informs s (self-state)
- s strongly conditions m (threat meaning) via arousal modulation
- o_ext and o_int reflect m and context
"""
function build_ifs_A_h1(params::IFSModelParams)
    Ns = (2, 2, 2)  # context, self-state, threat
    No = [3, 3, 3, 2]  # ext_cue, arousal, outcome, ctx_support
    Ng = 4

    A = Vector{Array{Float64}}(undef, Ng)
    for g in 1:Ng
        A[g] = zeros(No[g], Ns...)
    end

    # --- A[1]: External cue ---
    # Moderately informative about threat meaning given context
    for s in 1:2
        # Safe context: ambiguous cues dominate
        A[1][:, IFS_CTX_SAFE, s, IFS_THREAT_DANGER] = [0.50, 0.20, 0.30]
        A[1][:, IFS_CTX_SAFE, s, IFS_THREAT_SAFE]   = [0.40, 0.40, 0.20]
        # Dangerous context: threat cues dominate
        A[1][:, IFS_CTX_DANGEROUS, s, IFS_THREAT_DANGER] = [0.20, 0.10, 0.70]
        A[1][:, IFS_CTX_DANGEROUS, s, IFS_THREAT_SAFE]   = [0.30, 0.30, 0.40]
    end

    # --- A[2]: Interoceptive arousal ---
    # H1: Self-state STRONGLY modulates arousal response to threat
    # This is the key H1 mechanism: child_helpless amplifies threat -> panic
    for c in 1:2
        # child_helpless + danger -> intense panic
        A[2][:, c, IFS_SELF_CHILD_HELPLESS, IFS_THREAT_DANGER] = [0.05, 0.20, 0.75]
        # child_helpless + safe -> residual activation
        A[2][:, c, IFS_SELF_CHILD_HELPLESS, IFS_THREAT_SAFE]   = [0.30, 0.50, 0.20]
        # adult_capable + danger -> activated but regulated
        A[2][:, c, IFS_SELF_ADULT_CAPABLE, IFS_THREAT_DANGER]  = [0.15, 0.55, 0.30]
        # adult_capable + safe -> calm
        A[2][:, c, IFS_SELF_ADULT_CAPABLE, IFS_THREAT_SAFE]    = [0.70, 0.22, 0.08]
    end

    # --- A[3]: Outcome ---
    # Depends on true context. Safe world -> no real harm.
    for s in 1:2
        A[3][:, IFS_CTX_SAFE, s, IFS_THREAT_DANGER] = [0.15, 0.70, 0.15]
        A[3][:, IFS_CTX_SAFE, s, IFS_THREAT_SAFE]   = [0.40, 0.50, 0.10]
        A[3][:, IFS_CTX_DANGEROUS, s, IFS_THREAT_DANGER] = [0.05, 0.25, 0.70]
        A[3][:, IFS_CTX_DANGEROUS, s, IFS_THREAT_SAFE]   = [0.10, 0.40, 0.50]
    end

    # --- A[4]: Present-context support ---
    # H1 KEY: This modality strongly distinguishes self-state
    for c in 1:2, m in 1:2
        A[4][:, c, IFS_SELF_CHILD_HELPLESS, m] = [0.85, 0.15]
        A[4][:, c, IFS_SELF_ADULT_CAPABLE, m]  = [0.15, 0.85]
    end

    return A
end

"""
    build_ifs_A_h2(params) -> Vector{Array{Float64}}

Build observation likelihood matrices for H2 (threat-primary).

H2 structure:
- o_ext and o_int primarily inform m (threat meaning)
- m then influences s (self-state is downstream)
- o_ctx reflects m more than s directly
"""
function build_ifs_A_h2(params::IFSModelParams)
    Ns = (2, 2, 2)
    No = [3, 3, 3, 2]
    Ng = 4

    A = Vector{Array{Float64}}(undef, Ng)
    for g in 1:Ng
        A[g] = zeros(No[g], Ns...)
    end

    # --- A[1]: External cue ---
    # H2: More informative about threat meaning
    for s in 1:2
        A[1][:, IFS_CTX_SAFE, s, IFS_THREAT_DANGER] = [0.45, 0.15, 0.40]
        A[1][:, IFS_CTX_SAFE, s, IFS_THREAT_SAFE]   = [0.30, 0.50, 0.20]
        A[1][:, IFS_CTX_DANGEROUS, s, IFS_THREAT_DANGER] = [0.15, 0.05, 0.80]
        A[1][:, IFS_CTX_DANGEROUS, s, IFS_THREAT_SAFE]   = [0.25, 0.35, 0.40]
    end

    # --- A[2]: Interoceptive arousal ---
    # H2: arousal reflects threat meaning, LESS modulated by self-state
    for c in 1:2
        A[2][:, c, IFS_SELF_CHILD_HELPLESS, IFS_THREAT_DANGER] = [0.05, 0.30, 0.65]
        A[2][:, c, IFS_SELF_ADULT_CAPABLE, IFS_THREAT_DANGER]  = [0.10, 0.35, 0.55]
        A[2][:, c, IFS_SELF_CHILD_HELPLESS, IFS_THREAT_SAFE]   = [0.50, 0.35, 0.15]
        A[2][:, c, IFS_SELF_ADULT_CAPABLE, IFS_THREAT_SAFE]    = [0.55, 0.30, 0.15]
    end

    # --- A[3]: Outcome (same as H1) ---
    for s in 1:2
        A[3][:, IFS_CTX_SAFE, s, IFS_THREAT_DANGER] = [0.15, 0.70, 0.15]
        A[3][:, IFS_CTX_SAFE, s, IFS_THREAT_SAFE]   = [0.40, 0.50, 0.10]
        A[3][:, IFS_CTX_DANGEROUS, s, IFS_THREAT_DANGER] = [0.05, 0.25, 0.70]
        A[3][:, IFS_CTX_DANGEROUS, s, IFS_THREAT_SAFE]   = [0.10, 0.40, 0.50]
    end

    # --- A[4]: Present-context support ---
    # H2: Context support reflects THREAT MEANING more than self-state
    for c in 1:2
        A[4][:, c, IFS_SELF_CHILD_HELPLESS, IFS_THREAT_DANGER] = [0.80, 0.20]
        A[4][:, c, IFS_SELF_CHILD_HELPLESS, IFS_THREAT_SAFE]   = [0.30, 0.70]
        A[4][:, c, IFS_SELF_ADULT_CAPABLE, IFS_THREAT_DANGER]  = [0.70, 0.30]
        A[4][:, c, IFS_SELF_ADULT_CAPABLE, IFS_THREAT_SAFE]    = [0.25, 0.75]
    end

    return A
end

# ============================================================================
# B MATRIX CONSTRUCTION
# ============================================================================

"""
    build_ifs_B() -> Vector{Array{Float64,3}}

Build transition matrices.
"""
function build_ifs_B()
    Nf = 3
    B = Vector{Array{Float64,3}}(undef, Nf)

    # Factor 1: context - identity, uncontrollable
    B[1] = reshape(Matrix{Float64}(I, 2, 2), 2, 2, 1)

    # Factor 2: self-state - depends on policy (3 actions)
    B[2] = zeros(2, 2, 3)
    # Avoid: reinforces helplessness
    B[2][:, :, IFS_POLICY_AVOID] = [0.95 0.15; 0.05 0.85]
    # Inspect: allows shift toward capable
    B[2][:, :, IFS_POLICY_INSPECT] = [0.80 0.05; 0.20 0.95]
    # Stay: strongest shift toward capable
    B[2][:, :, IFS_POLICY_STAY] = [0.70 0.05; 0.30 0.95]

    # Factor 3: threat meaning - identity, uncontrollable within trial
    B[3] = reshape(Matrix{Float64}(I, 2, 2), 2, 2, 1)

    return B
end

# ============================================================================
# C MATRIX CONSTRUCTION
# ============================================================================

"""
    build_ifs_C(T::Int) -> Vector{Matrix{Float64}}

Build preference matrices (log preferences).
"""
function build_ifs_C(T::Int)
    No = [3, 3, 3, 2]
    Ng = 4
    C = [zeros(No[g], T) for g in 1:Ng]

    C[1][IFS_EXT_CLEAR_SAFE, :] .= 0.5
    C[1][IFS_EXT_CLEAR_THREAT, :] .= -1.0

    C[2][IFS_INT_CALM, :] .= 1.0
    C[2][IFS_INT_ACTIVATED, :] .= -0.5
    C[2][IFS_INT_PANIC, :] .= -2.0

    C[3][IFS_OUT_RELIEF, :] .= 2.0
    C[3][IFS_OUT_NEUTRAL, :] .= 0.0
    C[3][IFS_OUT_HARM, :] .= -6.0

    C[4][IFS_CTX_SUPPORTED_HERE_NOW, :] .= 1.0
    C[4][IFS_CTX_ALONE_OVERWHELMED, :] .= -0.5

    return C
end

# ============================================================================
# D MATRIX CONSTRUCTION
# ============================================================================

"""
    build_ifs_D(params) -> Vector{Vector{Float64}}

Build initial state priors (normalized).
"""
function build_ifs_D(params::IFSModelParams)
    D = Vector{Vector{Float64}}(undef, 3)
    D[1] = [0.5, 0.5]
    total_s = params.d_self_helpless + params.d_self_capable
    D[2] = [params.d_self_helpless / total_s, params.d_self_capable / total_s]
    total_m = params.d_threat_danger + params.d_threat_safe
    D[3] = [params.d_threat_danger / total_m, params.d_threat_safe / total_m]
    return D
end

"""
    build_ifs_pD(params) -> Vector{Vector{Float64}}

Build Dirichlet concentration parameters for initial state priors.
"""
function build_ifs_pD(params::IFSModelParams)
    pD = Vector{Vector{Float64}}(undef, 3)
    pD[1] = [50.0, 50.0]
    pD[2] = [params.d_self_helpless, params.d_self_capable]
    pD[3] = [params.d_threat_danger, params.d_threat_safe]
    return pD
end

# ============================================================================
# POLICY CONSTRUCTION
# ============================================================================

"""
    build_ifs_policies(T::Int) -> PolicySet
"""
function build_ifs_policies(T::Int)
    Np = 3
    Nf = 3

    V = ones(Int, T - 1, Np, Nf)
    V[:, :, 1] .= 1
    V[:, IFS_POLICY_AVOID, 2] .= IFS_POLICY_AVOID
    V[:, IFS_POLICY_INSPECT, 2] .= IFS_POLICY_INSPECT
    V[:, IFS_POLICY_STAY, 2] .= IFS_POLICY_STAY
    V[:, :, 3] .= 1

    E = [4.0, 1.0, 1.0]
    return PolicySet(V, E)
end

# ============================================================================
# MODEL CONSTRUCTION
# ============================================================================

"""
    build_ifs_model(; hypothesis=:H1, params=IFSModelParams()) -> AIFModel
"""
function build_ifs_model(; hypothesis::Symbol=:H1, params::IFSModelParams=IFSModelParams())
    A = hypothesis == :H1 ? build_ifs_A_h1(params) : build_ifs_A_h2(params)
    B = build_ifs_B()
    C = build_ifs_C(params.T)
    D = build_ifs_D(params)
    policies = build_ifs_policies(params.T)
    return AIFModel(A, B, C, D; policies=policies, trial_length=params.T)
end

# ============================================================================
# IFS ENVIRONMENT
# ============================================================================

"""
    IFSEnvironment <: AIFEnvironment

Environment for the IFS simulation.
"""
mutable struct IFSEnvironment <: AIFEnvironment
    world_dangerous::Bool
    current_state::Vector{Int}
    A::Vector{Array{Float64}}
    B::Vector{Array{Float64,3}}
    initial_state::Vector{Int}
end

function IFSEnvironment(world_dangerous::Bool, A::Vector{<:Array}, B::Vector{<:Array{<:Real,3}})
    ctx = world_dangerous ? IFS_CTX_DANGEROUS : IFS_CTX_SAFE
    self_true = IFS_SELF_ADULT_CAPABLE
    threat_true = world_dangerous ? IFS_THREAT_DANGER : IFS_THREAT_SAFE

    initial_state = [ctx, self_true, threat_true]
    current_state = copy(initial_state)

    A_typed = [Array{Float64}(a) for a in A]
    B_typed = [Array{Float64,3}(b) for b in B]

    IFSEnvironment(world_dangerous, current_state, A_typed, B_typed, initial_state)
end

function reset!(env::IFSEnvironment)
    env.current_state .= env.initial_state
    return env
end

function get_state(env::IFSEnvironment)::Vector{Int}
    return copy(env.current_state)
end

function observe(env::IFSEnvironment)::Vector{Int}
    Ng = length(env.A)
    obs = Vector{Int}(undef, Ng)
    s1, s2, s3 = env.current_state
    for g in 1:Ng
        probs = env.A[g][:, s1, s2, s3]
        probs_sum = sum(probs)
        probs = probs_sum > 0 ? probs ./ probs_sum : fill(1.0 / length(probs), length(probs))
        obs[g] = sample_categorical(probs)
    end
    return obs
end

function step!(env::IFSEnvironment, action::Vector{Int})
    Nf = length(env.B)
    for f in 1:Nf
        s_current = env.current_state[f]
        Na_f = size(env.B[f], 3)
        a_f = Na_f > 1 ? clamp(action[f], 1, Na_f) : 1
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

# ============================================================================
# SIMULATION RESULTS
# ============================================================================

"""
    IFSTrialResult

Results from a single trial.
"""
struct IFSTrialResult
    # Within-trial posterior (end of trial)
    p_avoid::Float64           # Behavioral avoidance tendency (derived from pD beliefs)
    p_child_helpless::Float64  # Within-trial P(s=child_helpless)
    p_danger::Float64          # Within-trial P(m=danger)
    E_t::Float64               # Self-energy
    C_t::Float64               # Capture index
    p_inspect::Float64         # P(inspect)
    p_stay::Float64            # P(stay)

    # Cross-trial beliefs (from pD -- the "durable" learning)
    pD_child_helpless::Float64
    pD_danger::Float64
end

"""
    IFSSimulationResult

Results from a full simulation run.
"""
struct IFSSimulationResult
    condition::String
    hypothesis::Symbol
    trials::Vector{IFSTrialResult}
    params::IFSModelParams
end

# ============================================================================
# SELF-ENERGY MODULATION OF A MATRICES
# ============================================================================

"""
    build_modulated_A(A_base, params, E_t, config) -> Vector{Array{Float64}}

Create A matrices modulated by Self-energy.

Self-energy determines how informative the context modality (A[4]) is:
- High E_t (witnessing): A[4] is fully informative -> self-state can be inferred
- Low E_t (blending): A[4] is nearly uniform -> self-state not informed by context
"""
function build_modulated_A(
    A_base::Vector{<:Array{Float64}},
    params::IFSModelParams,
    E_t::Float64,
    config::IFSConditionConfig
)
    A_mod = [copy(a) for a in A_base]

    pi_eff, lambda_eff = compute_effective_precisions(params, E_t)
    ctx_scale = config.context_precision_scale

    # Context sharpness: how informative A[4] is (range ~[0.05, 0.95])
    context_sharpness = lambda_eff / (lambda_eff + pi_eff) * ctx_scale
    context_sharpness = clamp(context_sharpness, 0.05, 0.95)

    # Modulate A[4] (context support): interpolate between base and uniform
    uniform_4 = [0.5, 0.5]
    for c in 1:2, s in 1:2, m in 1:2
        base_col = A_base[4][:, c, s, m]
        A_mod[4][:, c, s, m] .= context_sharpness .* base_col .+ (1.0 - context_sharpness) .* uniform_4
        A_mod[4][:, c, s, m] ./= sum(A_mod[4][:, c, s, m])
    end

    # Part capture also amplifies threat-consistent arousal
    part_capture = pi_eff / (pi_eff + lambda_eff)
    for c in 1:2, s in 1:2, m in 1:2
        base_col = A_base[2][:, c, s, m]
        if m == IFS_THREAT_DANGER
            threat_amplified = [0.02, 0.18, 0.80]
            mix = part_capture * 0.4
            A_mod[2][:, c, s, m] .= (1.0 - mix) .* base_col .+ mix .* threat_amplified
        end
        A_mod[2][:, c, s, m] ./= sum(A_mod[2][:, c, s, m])
    end

    return A_mod
end

# ============================================================================
# AVOIDANCE TENDENCY
# ============================================================================

"""
    compute_avoidance_tendency(pD, params)

Compute behavioral avoidance tendency from current beliefs.
P(avoid) reflects the part bundle's hold: high when both P(child_helpless)
and P(danger) are high, low when either revises toward safety.

Uses softmax over a weighted combination of danger and helplessness beliefs.
"""
function compute_avoidance_tendency(pD::Vector{Vector{Float64}}, params::IFSModelParams)
    p_child = pD[2][IFS_SELF_CHILD_HELPLESS] / sum(pD[2])
    p_danger = pD[3][IFS_THREAT_DANGER] / sum(pD[3])

    # Avoidance drive = part bundle activation
    # Both child_helpless AND danger must be high for strong avoidance
    avoid_drive = p_child * p_danger
    approach_drive = (1 - p_child) * (1 - p_danger)
    inspect_drive = 0.5 * (1 - avoid_drive)

    # Apply softmax with policy precision
    drives = [avoid_drive * 4.0, inspect_drive, approach_drive]  # 4x weight on avoidance base
    exp_drives = exp.(drives .- maximum(drives))
    probs = exp_drives ./ sum(exp_drives)

    return probs  # [p_avoid, p_inspect, p_stay]
end

# ============================================================================
# SINGLE TRIAL EXECUTION
# ============================================================================

"""
    run_ifs_trial!(agent, model, env, settings, params, E_t, config;
                   learn_D) -> IFSTrialResult

Run a single IFS trial with Self-energy precision modulation.

The key mechanism: Self-energy modulates the A matrices used for inference.
Under blending (low E_t), context evidence (A[4]) is uninformative, so
the agent's beliefs remain captured by the part bundle prior.
Under witnessing (high E_t), context evidence reaches inference and
drives revision of self-state (and downstream threat meaning).

Learning rate is also modulated by Self-energy:
- Under blending: learning from corrective evidence is attenuated
  (the system doesn't fully register the mismatch)
- Under witnessing: learning is enhanced (the system registers mismatch)
"""
function run_ifs_trial!(
    agent::AIFAgent{Float64},
    model::AIFModel{Float64},
    env::IFSEnvironment,
    settings::AIFSettings,
    params::IFSModelParams,
    E_t::Float64,
    config::IFSConditionConfig;
    learn_D::Vector{Int}=Int[2, 3]
)
    reset_trial!(agent, model)
    reset!(env)

    Nf = length(model.D)
    forced_policy = config.forced_policy
    C_t = compute_capture_index(params, E_t)

    # Create modulated A matrices and set as agent's pA
    A_mod = build_modulated_A(model.A, params, E_t, config)
    for g in 1:model.Ng
        agent.pA[g] .= A_mod[g]
    end

    # Set context prior based on condition
    if config.world_dangerous
        agent.pD[1] .= [1.0, 99.0]
    else
        agent.pD[1] .= [99.0, 1.0]
    end

    # Initialize beliefs from current pD
    for f in 1:Nf
        for t in 1:model.T
            agent.qs[t][f] .= agent.pD[f] ./ sum(agent.pD[f])
        end
    end

    # Determine forced action if applicable
    if forced_policy > 0
        forced_action = ones(Int, Nf)
        forced_action[2] = forced_policy
    end

    # Main trial loop
    for t in 1:model.T
        agent.t = t
        obs = observe(env)
        infer_states!(agent, model, obs, settings)

        if t < model.T
            if forced_policy > 0
                push!(agent.actions, copy(forced_action))
                step!(env, forced_action)
            else
                infer_policies!(agent, model, settings)
                action = sample_action(agent, model; alpha=settings.alpha, deterministic=true)
                step!(env, action)
            end
        end
    end

    # Update pD based on final beliefs
    # Learning rate is modulated by Self-energy:
    # Under witnessing: full learning rate (corrective evidence registers)
    # Under blending: attenuated learning (system insulated from evidence)
    # Under dissociation: reduced learning (evidence doesn't register)
    if !isempty(learn_D)
        # Effective learning rate: higher Self-energy -> more learning
        # But also modulated by context precision scale (dissociation blocks learning)
        eta_eff = params.eta_D_base * (1.0 - C_t) * config.context_precision_scale

        # For forced contact (exposure/witnessing), ensure minimum learning
        if forced_policy > 0
            eta_eff = max(eta_eff, 0.15 * params.eta_D_base)
        end

        qs_final = agent.qs[model.T]
        for f in learn_D
            if f >= 1 && f <= length(agent.pD)
                for s in 1:length(agent.pD[f])
                    agent.pD[f][s] += eta_eff * qs_final[f][s]
                end
            end
        end
    end

    # Extract within-trial results
    qs_final = agent.qs[model.T]
    p_child = qs_final[2][IFS_SELF_CHILD_HELPLESS]
    p_danger = qs_final[3][IFS_THREAT_DANGER]

    # Cross-trial beliefs from pD
    pD_child = agent.pD[2][IFS_SELF_CHILD_HELPLESS] / sum(agent.pD[2])
    pD_danger = agent.pD[3][IFS_THREAT_DANGER] / sum(agent.pD[3])

    # Behavioral avoidance tendency from current pD beliefs
    avoid_probs = compute_avoidance_tendency(agent.pD, params)
    p_avoid = avoid_probs[1]
    p_inspect = avoid_probs[2]
    p_stay = avoid_probs[3]

    return IFSTrialResult(
        p_avoid, p_child, p_danger, E_t, C_t, p_inspect, p_stay,
        pD_child, pD_danger
    )
end

# ============================================================================
# FULL SIMULATION
# ============================================================================

"""
    run_ifs_simulation(; hypothesis, config, params, n_trials, seed) -> IFSSimulationResult

Run a full IFS simulation for one condition.
"""
function run_ifs_simulation(;
    hypothesis::Symbol=:H1,
    config::IFSConditionConfig=baseline_ifs_config(),
    params::IFSModelParams=IFSModelParams(),
    n_trials::Int=30,
    seed::Int=42
)
    Random.seed!(seed)

    model = build_ifs_model(hypothesis=hypothesis, params=params)

    pA = [copy(a) for a in model.A]
    pB = [copy(b) for b in model.B]
    pD = build_ifs_pD(params)

    agent = init_agent(model, pA, pB, pD)
    env = IFSEnvironment(config.world_dangerous, model.A, model.B)

    settings = AIFSettings(
        gamma=params.gamma,
        alpha=params.alpha,
        eta=params.eta_D_base,
        use_ambiguity=true,
        use_utility=true,
        use_states_info_gain=true,
        use_param_info_gain=false,
        fpi_max_iter=16,
        fpi_tol=1e-6
    )

    trial_results = Vector{IFSTrialResult}(undef, n_trials)
    for trial in 1:n_trials
        result = run_ifs_trial!(
            agent, model, env, settings, params, config.E_t, config;
            learn_D=[2, 3]
        )
        trial_results[trial] = result
    end

    return IFSSimulationResult(config.name, hypothesis, trial_results, params)
end

"""
    run_all_ifs_conditions(; hypothesis, params, n_trials, seed) -> Vector{IFSSimulationResult}

Run all 5 conditions for a hypothesis.
"""
function run_all_ifs_conditions(;
    hypothesis::Symbol=:H1,
    params::IFSModelParams=IFSModelParams(),
    n_trials::Int=30,
    seed::Int=42
)
    configs = all_ifs_configs()
    results = Vector{IFSSimulationResult}(undef, length(configs))
    for (i, config) in enumerate(configs)
        results[i] = run_ifs_simulation(
            hypothesis=hypothesis, config=config, params=params,
            n_trials=n_trials, seed=seed + i
        )
    end
    return results
end

"""
    run_h1_h2_comparison(; params, n_trials, seed) -> (h1_results, h2_results)

Run all conditions under both H1 and H2.
"""
function run_h1_h2_comparison(;
    params::IFSModelParams=IFSModelParams(),
    n_trials::Int=30,
    seed::Int=42
)
    h1_results = run_all_ifs_conditions(hypothesis=:H1, params=params, n_trials=n_trials, seed=seed)
    h2_results = run_all_ifs_conditions(hypothesis=:H2, params=params, n_trials=n_trials, seed=seed + 100)
    return h1_results, h2_results
end

# ============================================================================
# ANALYSIS UTILITIES
# ============================================================================

"""Extract trajectory of a measure across trials."""
function extract_trajectory(result::IFSSimulationResult, field::Symbol)
    return [getfield(t, field) for t in result.trials]
end

"""Compute rolling mean of a trajectory."""
function rolling_mean(x::Vector{Float64}, window::Int=5)
    n = length(x)
    result = similar(x)
    for i in 1:n
        lo = max(1, i - window + 1)
        result[i] = mean(x[lo:i])
    end
    return result
end

"""Find the trial at which a measure crosses a threshold."""
function find_crossing_trial(trajectory::Vector{Float64}, threshold::Float64; direction=:below)
    smoothed = rolling_mean(trajectory, 3)
    for i in 1:length(smoothed)
        if direction == :below && smoothed[i] < threshold
            return i
        elseif direction == :above && smoothed[i] > threshold
            return i
        end
    end
    return nothing
end
