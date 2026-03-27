"""
    ifs_model_v3.jl - IFS Generalization Simulation

Minimal v3 implementation for the IFS paper's generalization test:
- 2 hidden factors: shared self-state and stimulus-specific threat
- Stimulus context (dog/cat) is known, not inferred
- 3 observation channels: cue, self evidence, outcome
- Static within-trial state dynamics (identity B)
- Cross-trial Dirichlet learning on pD_self and stimulus-specific threat banks

The core discriminant is transfer to a novel stimulus after dog-only training:
shared self revision generalizes; stimulus-specific threat revision does not.
"""

using Random
using Statistics

# ============================================================================
# INDEX CONSTANTS
# ============================================================================

# Hidden factor 1: self-state
const IFSV3_SELF_HELPLESS = 1
const IFSV3_SELF_RESOURCED = 2

# Hidden factor 2: threat meaning
const IFSV3_THREAT_DANGEROUS = 1
const IFSV3_THREAT_SAFE = 2

# Known stimulus context
const IFSV3_STIMULUS_DOG = 1
const IFSV3_STIMULUS_CAT = 2

# Policy labels
const IFSV3_POLICY_AVOID = 1
const IFSV3_POLICY_CONTACT = 2

# Cue outcomes
const IFSV3_CUE_DOG = 1
const IFSV3_CUE_CAT = 2

# Self-evidence outcomes
const IFSV3_SELF_EVIDENCE_HELPLESS = 1
const IFSV3_SELF_EVIDENCE_RESOURCED = 2

# Outcome observations
const IFSV3_OUTCOME_HARM = 1
const IFSV3_OUTCOME_NEUTRAL = 2

const IFSV3_NS = (2, 2)
const IFSV3_NO = (2, 2, 2)

const IFSV3_CHANNEL_CUE = 1
const IFSV3_CHANNEL_SELF = 2
const IFSV3_CHANNEL_OUTCOME = 3

# ============================================================================
# PARAMETERS AND RESULT TYPES
# ============================================================================

Base.@kwdef struct IFSV3Params
    n_training_trials::Int = 20
    n_probe_trials::Int = 5
    high_E::Float64 = 0.85
    low_E::Float64 = 0.15

    # Move 2: rebalance prior rigidity vs self evidence precision.
    pi_part::Float64 = 3.6
    beta_se::Float64 = 1.0
    lambda_self::Float64 = 0.7
    gamma_se::Float64 = 1.2

    # Cross-trial learning rates.
    eta_self::Float64 = 1.00
    eta_threat::Float64 = 1.60

    # Shared-self revision should tilt the threat appraisal within a trial
    # without rewriting the stimulus-specific threat bank.
    self_to_threat_coupling::Float64 = 1.35
    outcome_precision::Float64 = 1.60
    policy_precision::Float64 = 3.2
    threat_policy_weight::Float64 = 2.4
    contact_self_bias::Float64 = 0.08
    avoid_bias::Float64 = 0.03

    # Outcome utilities.
    utility_contact_harm::Float64 = -2.40
    utility_contact_neutral::Float64 = 1.40
    utility_avoid_harm::Float64 = -0.15
    utility_avoid_neutral::Float64 = 0.20

    # Initial Dirichlet concentrations.
    pD_self_helpless::Float64 = 18.0
    pD_self_resourced::Float64 = 2.0
    pD_threat_dangerous::Float64 = 17.0
    pD_threat_safe::Float64 = 3.0

    # Observation reliability.
    self_truthfulness::Float64 = 0.88
    outcome_safe_contact_neutral::Float64 = 0.96
    outcome_danger_contact_neutral::Float64 = 0.08
    outcome_safe_avoid_neutral::Float64 = 0.97
    outcome_danger_avoid_neutral::Float64 = 0.78
end

struct IFSV3ConditionConfig
    name::String
    architecture::Symbol
    E_t::Float64
    learn_self::Bool
    learn_threat::Bool
    train_stimulus::Int
    probe_stimulus::Int
    n_training_trials::Int
    n_probe_trials::Int
end

Base.@kwdef struct IFSV3TrialConfig
    stimulus::Int
    E_t::Float64
    forced_action::Union{Nothing,Int}=nothing
    actual_self::Int=IFSV3_SELF_RESOURCED
    actual_threat::Int=IFSV3_THREAT_SAFE
    learn_self::Bool=false
    learn_threat::Bool=false
    freeze_learning::Bool=false
    self_channel_mode::Symbol=:self
end

struct IFSV3Model
    architecture::Symbol
    params::IFSV3Params
    A_self::Array{Float64,3}
    A_outcome_contact::Array{Float64,3}
    A_outcome_avoid::Array{Float64,3}
    B_self::Array{Float64,3}
    B_threat::Array{Float64,3}
end

struct IFSV3EFEDecomposition
    pragmatic_per_channel::NTuple{3,Float64}
    epistemic_per_channel::NTuple{3,Float64}
    ambiguity_per_channel::NTuple{3,Float64}
    pragmatic_total::Float64
    epistemic_total::Float64
    ambiguity_total::Float64
end

struct IFSV3TrialResult
    trial_index::Int
    phase::Symbol
    stimulus::Int
    E_t::Float64
    action::Int
    cue_obs::Int
    self_obs::Int
    outcome_obs::Int
    p_self_resourced_prior::Float64
    p_self_resourced_after_self::Float64
    p_self_resourced_final::Float64
    p_threat_safe_prior::Float64
    p_threat_safe_after_self::Float64
    p_threat_safe_final::Float64
    p_contact::Float64
    p_avoid::Float64
    efe_avoid::Float64
    efe_contact::Float64
    efe_pragmatic_avoid::Float64
    efe_pragmatic_contact::Float64
    efe_epistemic_avoid::Float64
    efe_epistemic_contact::Float64
    efe_ambiguity_avoid::Float64
    efe_ambiguity_contact::Float64
    efe_pragmatic_channels_avoid::NTuple{3,Float64}
    efe_pragmatic_channels_contact::NTuple{3,Float64}
    efe_epistemic_channels_avoid::NTuple{3,Float64}
    efe_epistemic_channels_contact::NTuple{3,Float64}
    efe_ambiguity_channels_avoid::NTuple{3,Float64}
    efe_ambiguity_channels_contact::NTuple{3,Float64}
    pD_self_resourced::Float64
    pD_threat_dog_safe::Float64
    pD_threat_cat_safe::Float64
end

struct IFSV3Run
    condition::String
    architecture::Symbol
    E_t::Float64
    train_stimulus::Int
    probe_stimulus::Int
    learn_self::Bool
    learn_threat::Bool
    trials::Vector{IFSV3TrialResult}
    pD_self_final::Vector{Float64}
    pD_threat_dog_final::Vector{Float64}
    pD_threat_cat_final::Vector{Float64}
    pD_threat_cat_l1_shift::Float64
end

struct IFSV3Summary
    condition::String
    architecture::Symbol
    E_t::Float64
    learn_self::Bool
    learn_threat::Bool
    runs::Vector{IFSV3Run}
    mean_self_prior::Vector{Float64}
    mean_self_after_self::Vector{Float64}
    mean_self_final::Vector{Float64}
    mean_threat_prior::Vector{Float64}
    mean_threat_after_self::Vector{Float64}
    mean_threat_final::Vector{Float64}
    mean_contact::Vector{Float64}
    std_contact::Vector{Float64}
    mean_pD_self_resourced::Vector{Float64}
    mean_pD_dog_safe::Vector{Float64}
    mean_pD_cat_safe::Vector{Float64}
end

# ============================================================================
# CONDITION HELPERS
# ============================================================================

function ifs_v3_h1_highE_config(params::IFSV3Params=IFSV3Params())
    IFSV3ConditionConfig(
        "H1-highE",
        :H1,
        params.high_E,
        true,
        true,
        IFSV3_STIMULUS_DOG,
        IFSV3_STIMULUS_CAT,
        params.n_training_trials,
        params.n_probe_trials,
    )
end

function ifs_v3_h2_highE_config(params::IFSV3Params=IFSV3Params())
    IFSV3ConditionConfig(
        "H2-highE",
        :H2,
        params.high_E,
        false,
        true,
        IFSV3_STIMULUS_DOG,
        IFSV3_STIMULUS_CAT,
        params.n_training_trials,
        params.n_probe_trials,
    )
end

function ifs_v3_h1_lowE_config(params::IFSV3Params=IFSV3Params())
    IFSV3ConditionConfig(
        "H1-lowE",
        :H1,
        params.low_E,
        true,
        true,
        IFSV3_STIMULUS_DOG,
        IFSV3_STIMULUS_CAT,
        params.n_training_trials,
        params.n_probe_trials,
    )
end

main_ifs_v3_configs(params::IFSV3Params=IFSV3Params()) = [
    ifs_v3_h1_highE_config(params),
    ifs_v3_h2_highE_config(params),
    ifs_v3_h1_lowE_config(params),
]

# ============================================================================
# UTILITY HELPERS
# ============================================================================

normalize_prob(v::AbstractVector{<:Real}) = begin
    out = Float64.(v)
    total = sum(out)
    total <= 0 && return fill(1.0 / length(out), length(out))
    out ./ total
end

as_ifs_v3_channel_tuple(v::AbstractVector{<:Real}) = (Float64(v[1]), Float64(v[2]), Float64(v[3]))

function sample_ifs_v3_categorical(rng::AbstractRNG, probs::AbstractVector{<:Real})
    r = rand(rng)
    cumprob = 0.0
    for i in eachindex(probs)
        cumprob += probs[i]
        if r <= cumprob
            return i
        end
    end
    return length(probs)
end

function override_ifs_v3_params(params::IFSV3Params; kwargs...)
    values = Dict{Symbol,Any}(name => getfield(params, name) for name in fieldnames(IFSV3Params))
    for (k, v) in kwargs
        values[k] = v
    end
    return IFSV3Params(; (; (name => values[name] for name in fieldnames(IFSV3Params))...)...)
end

cue_label(stimulus::Int) = stimulus == IFSV3_STIMULUS_DOG ? "dog" : "cat"

function threat_bank_index(stimulus::Int)
    stimulus == IFSV3_STIMULUS_DOG && return 1
    stimulus == IFSV3_STIMULUS_CAT && return 2
    error("Unknown stimulus index: $stimulus")
end

function initial_ifs_v3_banks(params::IFSV3Params)
    pD_self = [params.pD_self_helpless, params.pD_self_resourced]
    pD_threat_dog = [params.pD_threat_dangerous, params.pD_threat_safe]
    pD_threat_cat = [params.pD_threat_dangerous, params.pD_threat_safe]
    return pD_self, pD_threat_dog, pD_threat_cat
end

function copy_ifs_v3_banks(
    pD_self::Vector{Float64},
    pD_threat_dog::Vector{Float64},
    pD_threat_cat::Vector{Float64},
)
    return copy(pD_self), copy(pD_threat_dog), copy(pD_threat_cat)
end

# ============================================================================
# MATRIX CONSTRUCTION
# ============================================================================

function build_ifs_v3_A_self(params::IFSV3Params=IFSV3Params())
    A = zeros(Float64, 2, 2, 2)
    truth = clamp(params.self_truthfulness, 0.5, 0.999)
    for threat in 1:2
        A[:, IFSV3_SELF_HELPLESS, threat] = [truth, 1.0 - truth]
        A[:, IFSV3_SELF_RESOURCED, threat] = [1.0 - truth, truth]
    end
    return A
end

function build_ifs_v3_A_cue(stimulus::Int)
    A = zeros(Float64, 2, 2, 2)
    cue_obs = stimulus == IFSV3_STIMULUS_DOG ? IFSV3_CUE_DOG : IFSV3_CUE_CAT
    for self in 1:2, threat in 1:2
        A[cue_obs, self, threat] = 1.0
    end
    return A
end

function build_ifs_v3_A_outcome(params::IFSV3Params=IFSV3Params(); action::Int=IFSV3_POLICY_CONTACT)
    A = zeros(Float64, 2, 2, 2)
    neutral_safe = action == IFSV3_POLICY_CONTACT ?
        params.outcome_safe_contact_neutral :
        params.outcome_safe_avoid_neutral
    neutral_danger = action == IFSV3_POLICY_CONTACT ?
        params.outcome_danger_contact_neutral :
        params.outcome_danger_avoid_neutral

    harm_safe = 1.0 - neutral_safe
    harm_danger = 1.0 - neutral_danger
    for self in 1:2
        A[:, self, IFSV3_THREAT_DANGEROUS] = [harm_danger, neutral_danger]
        A[:, self, IFSV3_THREAT_SAFE] = [harm_safe, neutral_safe]
    end
    return A
end

function build_ifs_v3_B()
    B_self = zeros(Float64, 2, 2, 2)
    B_threat = zeros(Float64, 2, 2, 2)
    for action in 1:2
        B_self[:, :, action] = Matrix{Float64}(I, 2, 2)
        B_threat[:, :, action] = Matrix{Float64}(I, 2, 2)
    end
    return B_self, B_threat
end

function validate_ifs_v3_matrices(
    A_self::Array{Float64,3},
    A_outcome_contact::Array{Float64,3},
    A_outcome_avoid::Array{Float64,3},
    B_self::Array{Float64,3},
    B_threat::Array{Float64,3};
    atol::Float64=1e-8,
)
    @assert size(A_self) == (2, IFSV3_NS...)
    @assert size(A_outcome_contact) == (2, IFSV3_NS...)
    @assert size(A_outcome_avoid) == (2, IFSV3_NS...)
    @assert size(B_self) == (2, 2, 2)
    @assert size(B_threat) == (2, 2, 2)
    @assert all(isapprox.(sum(A_self, dims=1), 1.0; atol=atol))
    @assert all(isapprox.(sum(A_outcome_contact, dims=1), 1.0; atol=atol))
    @assert all(isapprox.(sum(A_outcome_avoid, dims=1), 1.0; atol=atol))
    for action in 1:2
        @assert all(isapprox.(sum(B_self[:, :, action], dims=1), 1.0; atol=atol))
        @assert all(isapprox.(sum(B_threat[:, :, action], dims=1), 1.0; atol=atol))
    end
    return true
end

function build_ifs_v3_model(; architecture::Symbol=:H1, params::IFSV3Params=IFSV3Params())
    A_self = build_ifs_v3_A_self(params)
    A_outcome_contact = build_ifs_v3_A_outcome(params; action=IFSV3_POLICY_CONTACT)
    A_outcome_avoid = build_ifs_v3_A_outcome(params; action=IFSV3_POLICY_AVOID)
    B_self, B_threat = build_ifs_v3_B()
    validate_ifs_v3_matrices(A_self, A_outcome_contact, A_outcome_avoid, B_self, B_threat)
    return IFSV3Model(architecture, params, A_self, A_outcome_contact, A_outcome_avoid, B_self, B_threat)
end

# ============================================================================
# INFERENCE AND POLICY
# ============================================================================

function compute_ifs_v3_precisions(params::IFSV3Params, E_t::Float64)
    pi_part_eff = params.pi_part * exp(-params.beta_se * E_t)
    lambda_self_eff = params.lambda_self * exp(params.gamma_se * E_t)
    return pi_part_eff, lambda_self_eff
end

function compute_ifs_v3_predicted_obs(
    A::Array{Float64,3},
    q_self::Vector{Float64},
    q_threat::Vector{Float64},
)
    qo = zeros(Float64, size(A, 1))
    for self in 1:2, threat in 1:2
        qo .+= (q_self[self] * q_threat[threat]) .* view(A, :, self, threat)
    end
    return normalize_prob(qo)
end

function compute_ifs_v3_ambiguity(
    A::Array{Float64,3},
    q_self::Vector{Float64},
    q_threat::Vector{Float64},
)
    ambiguity = 0.0
    for self in 1:2, threat in 1:2
        p_state = q_self[self] * q_threat[threat]
        p_state <= eps(Float64) && continue

        entropy = 0.0
        for p in view(A, :, self, threat)
            p <= eps(Float64) && continue
            entropy -= p * log(p)
        end
        ambiguity += p_state * entropy
    end
    return ambiguity
end

function compute_ifs_v3_posterior_given_obs(
    A::Array{Float64,3},
    obs::Int,
    q_self::Vector{Float64},
    q_threat::Vector{Float64},
)
    joint = zeros(Float64, 2, 2)
    for self in 1:2, threat in 1:2
        joint[self, threat] = A[obs, self, threat] * q_self[self] * q_threat[threat]
    end

    evidence = sum(joint)
    evidence <= eps(Float64) && return copy(q_self), copy(q_threat)
    joint ./= evidence
    return vec(sum(joint; dims=2)), vec(sum(joint; dims=1))
end

function compute_ifs_v3_state_info_gain(
    A::Array{Float64,3},
    q_self::Vector{Float64},
    q_threat::Vector{Float64},
    qo::Vector{Float64},
)
    info_gain = 0.0
    for obs in 1:length(qo)
        qo[obs] <= eps(Float64) && continue
        q_self_given_obs, q_threat_given_obs = compute_ifs_v3_posterior_given_obs(A, obs, q_self, q_threat)
        kl = 0.0
        for self in 1:2
            p = q_self_given_obs[self]
            p > eps(Float64) && (kl += p * log(p / (q_self[self] + eps(Float64))))
        end
        for threat in 1:2
            p = q_threat_given_obs[threat]
            p > eps(Float64) && (kl += p * log(p / (q_threat[threat] + eps(Float64))))
        end
        info_gain += qo[obs] * kl
    end
    return info_gain
end

function compute_ifs_v3_channel_weights(
    model::IFSV3Model,
    E_t::Float64;
    learn_self::Bool=true,
    self_channel_mode::Symbol=:self,
)
    _, lambda_self_eff = compute_ifs_v3_precisions(model.params, E_t)
    cue_weight = 1.0
    self_weight = model.architecture == :H1 && learn_self && self_channel_mode == :self ?
        E_t * lambda_self_eff :
        0.0
    outcome_weight = 1.0
    return cue_weight, self_weight, outcome_weight
end

function compute_ifs_v3_log_preferences(params::IFSV3Params, action::Int)
    cue_log_prefs = zeros(Float64, 2)
    self_log_prefs = zeros(Float64, 2)
    outcome_raw = action == IFSV3_POLICY_CONTACT ?
        [params.utility_contact_harm, params.utility_contact_neutral] :
        [params.utility_avoid_harm, params.utility_avoid_neutral]
    outcome_log_prefs = log.(softmax(outcome_raw) .+ eps(Float64))
    return cue_log_prefs, self_log_prefs, outcome_log_prefs
end

function compute_ifs_v3_policy_efe_decomposed(
    model::IFSV3Model,
    stimulus::Int,
    q_self::Vector{Float64},
    q_threat::Vector{Float64},
    E_t::Float64,
    action::Int;
    learn_self::Bool=true,
    self_channel_mode::Symbol=:self,
)
    A_channels = (
        build_ifs_v3_A_cue(stimulus),
        model.A_self,
        action == IFSV3_POLICY_CONTACT ? model.A_outcome_contact : model.A_outcome_avoid,
    )
    log_prefs = compute_ifs_v3_log_preferences(model.params, action)
    channel_weights = compute_ifs_v3_channel_weights(
        model,
        E_t;
        learn_self=learn_self,
        self_channel_mode=self_channel_mode,
    )

    pragmatic_per_channel = zeros(Float64, 3)
    epistemic_per_channel = zeros(Float64, 3)
    ambiguity_per_channel = zeros(Float64, 3)

    for g in 1:3
        weight = channel_weights[g]
        weight <= 0.0 && continue

        qo = compute_ifs_v3_predicted_obs(A_channels[g], q_self, q_threat)
        ambiguity_per_channel[g] = weight * compute_ifs_v3_ambiguity(A_channels[g], q_self, q_threat)
        pragmatic_per_channel[g] = -weight * sum(qo .* log_prefs[g])
        epistemic_per_channel[g] = weight * compute_ifs_v3_state_info_gain(A_channels[g], q_self, q_threat, qo)
    end

    self_signal = q_self[IFSV3_SELF_RESOURCED] - q_self[IFSV3_SELF_HELPLESS]
    threat_signal = q_threat[IFSV3_THREAT_SAFE] - q_threat[IFSV3_THREAT_DANGEROUS]
    if action == IFSV3_POLICY_CONTACT
        pragmatic_per_channel[IFSV3_CHANNEL_OUTCOME] -= model.params.threat_policy_weight * threat_signal
        if model.architecture == :H1 && self_channel_mode == :self
            pragmatic_per_channel[IFSV3_CHANNEL_SELF] -= model.params.contact_self_bias * self_signal
        end
    else
        pragmatic_per_channel[IFSV3_CHANNEL_OUTCOME] += model.params.threat_policy_weight * threat_signal
        if model.architecture == :H1 && self_channel_mode == :self
            pragmatic_per_channel[IFSV3_CHANNEL_SELF] += model.params.avoid_bias * self_signal
        end
    end

    decomposition = IFSV3EFEDecomposition(
        as_ifs_v3_channel_tuple(pragmatic_per_channel),
        as_ifs_v3_channel_tuple(epistemic_per_channel),
        as_ifs_v3_channel_tuple(ambiguity_per_channel),
        sum(pragmatic_per_channel),
        sum(epistemic_per_channel),
        sum(ambiguity_per_channel),
    )
    efe = decomposition.ambiguity_total + decomposition.pragmatic_total - decomposition.epistemic_total
    return efe, decomposition
end

function compute_ifs_v3_policy_efe(
    model::IFSV3Model,
    stimulus::Int,
    q_self::Vector{Float64},
    q_threat::Vector{Float64},
    E_t::Float64,
    action::Int;
    learn_self::Bool=true,
    self_channel_mode::Symbol=:self,
)
    efe, _ = compute_ifs_v3_policy_efe_decomposed(
        model,
        stimulus,
        q_self,
        q_threat,
        E_t,
        action;
        learn_self=learn_self,
        self_channel_mode=self_channel_mode,
    )
    return efe
end

function infer_ifs_v3_self(
    model::IFSV3Model,
    prior_self::Vector{Float64},
    threat_prior::Vector{Float64},
    obs::Int,
    E_t::Float64;
    mode::Symbol=:self,
)
    params = model.params
    pi_part_eff, lambda_self_eff = compute_ifs_v3_precisions(params, E_t)

    if mode == :threat
        return copy(prior_self), pi_part_eff, lambda_self_eff
    end

    likelihood = vec(model.A_self[obs, :, :] * threat_prior)
    ln_q = pi_part_eff .* log.(prior_self .+ eps(Float64)) .+
        lambda_self_eff .* log.(likelihood .+ eps(Float64))
    return softmax(ln_q), pi_part_eff, lambda_self_eff
end

function infer_ifs_v3_threat_from_self(
    model::IFSV3Model,
    prior_threat::Vector{Float64},
    q_self::Vector{Float64},
    params::IFSV3Params;
    obs::Int=IFSV3_SELF_EVIDENCE_RESOURCED,
    mode::Symbol=:self,
    lambda_self_eff::Float64=1.0,
)
    if mode == :threat
        signal = obs == IFSV3_SELF_EVIDENCE_RESOURCED ? lambda_self_eff : -lambda_self_eff
        ln_q = log.(prior_threat .+ eps(Float64)) .+ signal .* [-1.0, 1.0]
        return softmax(ln_q)
    end

    if model.architecture == :H2
        return copy(prior_threat)
    end

    self_signal = q_self[IFSV3_SELF_RESOURCED] - q_self[IFSV3_SELF_HELPLESS]
    ln_q = log.(prior_threat .+ eps(Float64)) .+
        params.self_to_threat_coupling .* self_signal .* [-1.0, 1.0]
    return softmax(ln_q)
end

function infer_ifs_v3_threat_from_outcome(
    model::IFSV3Model,
    q_threat_pre::Vector{Float64},
    action::Int,
    outcome_obs::Int,
)
    A = action == IFSV3_POLICY_CONTACT ? model.A_outcome_contact : model.A_outcome_avoid
    likelihood = vec(sum(A[outcome_obs, :, :]; dims=1)) ./ 2.0
    ln_q = log.(q_threat_pre .+ eps(Float64)) .+
        model.params.outcome_precision .* log.(likelihood .+ eps(Float64))
    return softmax(ln_q)
end

function expected_ifs_v3_outcome(model::IFSV3Model, q_threat::Vector{Float64}, action::Int)
    A = action == IFSV3_POLICY_CONTACT ? model.A_outcome_contact : model.A_outcome_avoid
    predicted = zeros(Float64, 2)
    for self in 1:2
        predicted .+= 0.5 .* (A[:, self, :] * q_threat)
    end
    return normalize_prob(predicted)
end

function compute_ifs_v3_policy_probs(
    model::IFSV3Model,
    stimulus::Int,
    q_self::Vector{Float64},
    q_threat::Vector{Float64},
    E_t::Float64;
    learn_self::Bool=true,
    self_channel_mode::Symbol=:self,
)
    efe_avoid = compute_ifs_v3_policy_efe(
        model,
        stimulus,
        q_self,
        q_threat,
        E_t,
        IFSV3_POLICY_AVOID;
        learn_self=learn_self,
        self_channel_mode=self_channel_mode,
    )
    efe_contact = compute_ifs_v3_policy_efe(
        model,
        stimulus,
        q_self,
        q_threat,
        E_t,
        IFSV3_POLICY_CONTACT;
        learn_self=learn_self,
        self_channel_mode=self_channel_mode,
    )
    return softmax((-model.params.policy_precision) .* [efe_avoid, efe_contact])
end

function sample_ifs_v3_outcome(model::IFSV3Model, action::Int, actual_self::Int, actual_threat::Int)
    return sample_ifs_v3_outcome(Random.default_rng(), model, action, actual_self, actual_threat)
end

function sample_ifs_v3_outcome(
    rng::AbstractRNG,
    model::IFSV3Model,
    action::Int,
    actual_self::Int,
    actual_threat::Int,
)
    A = action == IFSV3_POLICY_CONTACT ? model.A_outcome_contact : model.A_outcome_avoid
    return sample_ifs_v3_categorical(rng, A[:, actual_self, actual_threat])
end

function update_ifs_v3_banks!(
    pD_self::Vector{Float64},
    pD_threat_dog::Vector{Float64},
    pD_threat_cat::Vector{Float64},
    q_self_final::Vector{Float64},
    q_threat_final::Vector{Float64},
    stimulus::Int,
    params::IFSV3Params;
    learn_self::Bool=false,
    learn_threat::Bool=false,
)
    if learn_self
        pD_self .+= params.eta_self .* q_self_final
    end

    if learn_threat
        bank = stimulus == IFSV3_STIMULUS_DOG ? pD_threat_dog : pD_threat_cat
        bank .+= params.eta_threat .* q_threat_final
    end
    return nothing
end

# ============================================================================
# SINGLE-TRIAL AND CONDITION RUNNERS
# ============================================================================

function run_ifs_v3_trial!(
    model::IFSV3Model,
    pD_self::Vector{Float64},
    pD_threat_dog::Vector{Float64},
    pD_threat_cat::Vector{Float64},
    config::IFSV3TrialConfig;
    trial_index::Int,
    phase::Symbol,
    rng::AbstractRNG=Random.default_rng(),
    verbose::Bool=false,
)
    threat_bank = config.stimulus == IFSV3_STIMULUS_DOG ? pD_threat_dog : pD_threat_cat
    q_self_prior = normalize_prob(pD_self)
    q_threat_prior = normalize_prob(threat_bank)

    cue_obs = config.stimulus == IFSV3_STIMULUS_DOG ? IFSV3_CUE_DOG : IFSV3_CUE_CAT
    self_obs = config.actual_self == IFSV3_SELF_RESOURCED ?
        IFSV3_SELF_EVIDENCE_RESOURCED :
        IFSV3_SELF_EVIDENCE_HELPLESS

    q_self_after, pi_part_eff, lambda_self_eff = infer_ifs_v3_self(
        model,
        q_self_prior,
        q_threat_prior,
        self_obs,
        config.E_t;
        mode=config.self_channel_mode,
    )

    q_threat_after_self = infer_ifs_v3_threat_from_self(
        model,
        q_threat_prior,
        q_self_after,
        model.params;
        obs=self_obs,
        mode=config.self_channel_mode,
        lambda_self_eff=lambda_self_eff,
    )
    policy_threat = isnothing(config.forced_action) || config.self_channel_mode == :threat ?
        q_threat_after_self :
        q_threat_prior

    efe_avoid, efe_decomp_avoid = compute_ifs_v3_policy_efe_decomposed(
        model,
        config.stimulus,
        q_self_after,
        policy_threat,
        config.E_t,
        IFSV3_POLICY_AVOID;
        learn_self=config.learn_self,
        self_channel_mode=config.self_channel_mode,
    )
    efe_contact, efe_decomp_contact = compute_ifs_v3_policy_efe_decomposed(
        model,
        config.stimulus,
        q_self_after,
        policy_threat,
        config.E_t,
        IFSV3_POLICY_CONTACT;
        learn_self=config.learn_self,
        self_channel_mode=config.self_channel_mode,
    )
    qpi = softmax((-model.params.policy_precision) .* [efe_avoid, efe_contact])
    action = isnothing(config.forced_action) ? sample_ifs_v3_categorical(rng, qpi) : config.forced_action

    outcome_obs = sample_ifs_v3_outcome(rng, model, action, config.actual_self, config.actual_threat)
    q_threat_final = infer_ifs_v3_threat_from_outcome(model, q_threat_after_self, action, outcome_obs)
    q_self_final = copy(q_self_after)

    if !(config.freeze_learning)
        update_ifs_v3_banks!(
            pD_self,
            pD_threat_dog,
            pD_threat_cat,
            q_self_final,
            q_threat_final,
            config.stimulus,
            model.params;
            learn_self=config.learn_self,
            learn_threat=config.learn_threat,
        )
    end

    verbose && println(
        "trial=$(trial_index) phase=$(phase) stimulus=$(cue_label(config.stimulus)) ",
        "E_t=$(round(config.E_t, digits=3)) pi_part=$(round(pi_part_eff, digits=3)) ",
        "lambda_self=$(round(lambda_self_eff, digits=3)) q_self_prior=$(round(q_self_prior[2], digits=3)) ",
        "q_self_after=$(round(q_self_after[2], digits=3)) q_threat_prior=$(round(q_threat_prior[2], digits=3)) ",
        "q_threat_after_self=$(round(q_threat_after_self[2], digits=3)) q_threat_final=$(round(q_threat_final[2], digits=3)) ",
        "qpi=$(round.(qpi, digits=3)) efe=$(round.([efe_avoid, efe_contact], digits=3)) ",
        "action=$(action) outcome=$(outcome_obs)"
    )

    return IFSV3TrialResult(
        trial_index,
        phase,
        config.stimulus,
        config.E_t,
        action,
        cue_obs,
        self_obs,
        outcome_obs,
        q_self_prior[IFSV3_SELF_RESOURCED],
        q_self_after[IFSV3_SELF_RESOURCED],
        q_self_final[IFSV3_SELF_RESOURCED],
        q_threat_prior[IFSV3_THREAT_SAFE],
        q_threat_after_self[IFSV3_THREAT_SAFE],
        q_threat_final[IFSV3_THREAT_SAFE],
        qpi[IFSV3_POLICY_CONTACT],
        qpi[IFSV3_POLICY_AVOID],
        efe_avoid,
        efe_contact,
        efe_decomp_avoid.pragmatic_total,
        efe_decomp_contact.pragmatic_total,
        efe_decomp_avoid.epistemic_total,
        efe_decomp_contact.epistemic_total,
        efe_decomp_avoid.ambiguity_total,
        efe_decomp_contact.ambiguity_total,
        efe_decomp_avoid.pragmatic_per_channel,
        efe_decomp_contact.pragmatic_per_channel,
        efe_decomp_avoid.epistemic_per_channel,
        efe_decomp_contact.epistemic_per_channel,
        efe_decomp_avoid.ambiguity_per_channel,
        efe_decomp_contact.ambiguity_per_channel,
        normalize_prob(pD_self)[IFSV3_SELF_RESOURCED],
        normalize_prob(pD_threat_dog)[IFSV3_THREAT_SAFE],
        normalize_prob(pD_threat_cat)[IFSV3_THREAT_SAFE],
    )
end

function run_ifs_v3_condition(
    model::IFSV3Model,
    condition::IFSV3ConditionConfig;
    seed::Int=42,
    train_actual_self::Int=IFSV3_SELF_RESOURCED,
    train_actual_threat::Int=IFSV3_THREAT_SAFE,
    probe_actual_self::Int=IFSV3_SELF_RESOURCED,
    probe_actual_threat::Int=IFSV3_THREAT_SAFE,
    train_self_channel_mode::Symbol=:self,
    probe_self_channel_mode::Symbol=:self,
    verbose::Bool=false,
)
    rng = MersenneTwister(seed)
    pD_self, pD_threat_dog, pD_threat_cat = initial_ifs_v3_banks(model.params)
    pD_cat_initial = normalize_prob(pD_threat_cat)
    trials = IFSV3TrialResult[]

    for t in 1:condition.n_training_trials
        push!(trials, run_ifs_v3_trial!(
            model,
            pD_self,
            pD_threat_dog,
            pD_threat_cat,
            IFSV3TrialConfig(
                condition.train_stimulus,
                condition.E_t,
                IFSV3_POLICY_CONTACT,
                train_actual_self,
                train_actual_threat,
                condition.learn_self,
                condition.learn_threat,
                false,
                train_self_channel_mode,
            );
            trial_index=t,
            phase=:training,
            rng=rng,
            verbose=verbose,
        ))
    end

    for k in 1:condition.n_probe_trials
        push!(trials, run_ifs_v3_trial!(
            model,
            pD_self,
            pD_threat_dog,
            pD_threat_cat,
            IFSV3TrialConfig(
                condition.probe_stimulus,
                condition.E_t,
                nothing,
                probe_actual_self,
                probe_actual_threat,
                false,
                false,
                true,
                probe_self_channel_mode,
            );
            trial_index=condition.n_training_trials + k,
            phase=:probe,
            rng=rng,
            verbose=verbose,
        ))
    end

    pD_cat_final = normalize_prob(pD_threat_cat)
    return IFSV3Run(
        condition.name,
        condition.architecture,
        condition.E_t,
        condition.train_stimulus,
        condition.probe_stimulus,
        condition.learn_self,
        condition.learn_threat,
        trials,
        normalize_prob(pD_self),
        normalize_prob(pD_threat_dog),
        normalize_prob(pD_threat_cat),
        sum(abs.(pD_cat_final .- pD_cat_initial)),
    )
end

function summarize_ifs_v3_runs(runs::Vector{IFSV3Run})
    @assert !isempty(runs)
    T = length(runs[1].trials)
    N = length(runs)

    self_prior = zeros(Float64, T, N)
    self_after = zeros(Float64, T, N)
    self_final = zeros(Float64, T, N)
    threat_prior = zeros(Float64, T, N)
    threat_after = zeros(Float64, T, N)
    threat_final = zeros(Float64, T, N)
    contact = zeros(Float64, T, N)
    pD_self_resourced = zeros(Float64, T, N)
    pD_dog_safe = zeros(Float64, T, N)
    pD_cat_safe = zeros(Float64, T, N)

    for (j, run) in enumerate(runs)
        for (t, trial) in enumerate(run.trials)
            self_prior[t, j] = trial.p_self_resourced_prior
            self_after[t, j] = trial.p_self_resourced_after_self
            self_final[t, j] = trial.p_self_resourced_final
            threat_prior[t, j] = trial.p_threat_safe_prior
            threat_after[t, j] = trial.p_threat_safe_after_self
            threat_final[t, j] = trial.p_threat_safe_final
            contact[t, j] = trial.p_contact
            pD_self_resourced[t, j] = trial.pD_self_resourced
            pD_dog_safe[t, j] = trial.pD_threat_dog_safe
            pD_cat_safe[t, j] = trial.pD_threat_cat_safe
        end
    end

    return IFSV3Summary(
        runs[1].condition,
        runs[1].architecture,
        runs[1].E_t,
        runs[1].learn_self,
        runs[1].learn_threat,
        runs,
        vec(mean(self_prior; dims=2)),
        vec(mean(self_after; dims=2)),
        vec(mean(self_final; dims=2)),
        vec(mean(threat_prior; dims=2)),
        vec(mean(threat_after; dims=2)),
        vec(mean(threat_final; dims=2)),
        vec(mean(contact; dims=2)),
        vec(std(contact; dims=2)),
        vec(mean(pD_self_resourced; dims=2)),
        vec(mean(pD_dog_safe; dims=2)),
        vec(mean(pD_cat_safe; dims=2)),
    )
end

function run_ifs_v3_replications(;
    condition::IFSV3ConditionConfig=ifs_v3_h1_highE_config(),
    params::IFSV3Params=IFSV3Params(),
    n_replications::Int=60,
    seed::Int=42,
    train_actual_self::Int=IFSV3_SELF_RESOURCED,
    train_actual_threat::Int=IFSV3_THREAT_SAFE,
    probe_actual_self::Int=IFSV3_SELF_RESOURCED,
    probe_actual_threat::Int=IFSV3_THREAT_SAFE,
    train_self_channel_mode::Symbol=:self,
    probe_self_channel_mode::Symbol=:self,
    verbose::Bool=false,
)
    model = build_ifs_v3_model(architecture=condition.architecture, params=params)
    runs = Vector{IFSV3Run}(undef, n_replications)
    for i in 1:n_replications
        runs[i] = run_ifs_v3_condition(
            model,
            condition;
            seed=seed + i,
            train_actual_self=train_actual_self,
            train_actual_threat=train_actual_threat,
            probe_actual_self=probe_actual_self,
            probe_actual_threat=probe_actual_threat,
            train_self_channel_mode=train_self_channel_mode,
            probe_self_channel_mode=probe_self_channel_mode,
            verbose=verbose && i == 1,
        )
    end
    return summarize_ifs_v3_runs(runs)
end

function run_ifs_v3_suite(;
    params::IFSV3Params=IFSV3Params(),
    n_replications::Int=60,
    seed::Int=42,
)
    configs = main_ifs_v3_configs(params)
    summaries = Vector{IFSV3Summary}(undef, length(configs))
    for (i, config) in enumerate(configs)
        summaries[i] = run_ifs_v3_replications(
            condition=config,
            params=params,
            n_replications=n_replications,
            seed=seed + 100 * i,
        )
    end
    return summaries
end
