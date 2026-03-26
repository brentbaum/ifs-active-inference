"""
    ifs_model_v2.jl - Three-Move IFS Active Inference Simulation

Minimal v2 implementation for the IFS paper:
- 3 hidden factors: self-state, threat meaning, expected outcome
- Context is environmental, not inferred as a hidden factor
- 5 observation channels, including depth-gated witnessed self-state
- Two-stage update per timestep:
  1. infer from channels 1-4
  2. compute capture and open channel 5 only if decapture is sufficient

This file does not force the v2 design through the generic `AIFModel` path because
the witnessed-self channel must open *after* channels 1-4 have already updated the
current timestep's beliefs.
"""

using Random
using Statistics

# ============================================================================
# INDEX CONSTANTS
# ============================================================================

# Hidden factor 1: self-state
const IFSV2_SELF_HELPLESS_ALONE = 1
const IFSV2_SELF_CAPABLE_PRESENT = 2

# Hidden factor 2: threat meaning
const IFSV2_THREAT_DANGEROUS = 1
const IFSV2_THREAT_SAFE = 2

# Hidden factor 3: expected outcome
const IFSV2_OUTCOME_AVOIDANCE_SAVES = 1
const IFSV2_OUTCOME_CONTACT_MANAGEABLE = 2

# Environmental context
const IFSV2_CONTEXT_SAFE = 1
const IFSV2_CONTEXT_DANGEROUS = 2

# Observation 1: external cue
const IFSV2_EXT_AMBIGUOUS = 1
const IFSV2_EXT_CLEAR_SAFE = 2
const IFSV2_EXT_CLEAR_THREAT = 3

# Observation 2: interoceptive arousal
const IFSV2_INT_CALM = 1
const IFSV2_INT_ACTIVATED = 2
const IFSV2_INT_PANIC = 3

# Observation 3: action outcome
const IFSV2_ACT_RELIEF = 1
const IFSV2_ACT_NEUTRAL = 2
const IFSV2_ACT_HARM = 3

# Observation 4: informational context
const IFSV2_INFO_ALONE_OVERWHELMED = 1
const IFSV2_INFO_SUPPORTED_HERE_NOW = 2

# Observation 5: witnessed self-state
const IFSV2_WIT_HELPLESS_ALONE = 1
const IFSV2_WIT_CAPABLE_PRESENT = 2

# Actions / policy labels
const IFSV2_POLICY_AVOID = 1
const IFSV2_POLICY_INSPECT = 2
const IFSV2_POLICY_STAY = 3

# Convenience dimensions
const IFSV2_NS = (2, 2, 2)
const IFSV2_NO = (3, 3, 3, 2, 2)

# ============================================================================
# PARAMETERS AND RESULT TYPES
# ============================================================================

Base.@kwdef struct IFSV2Params
    # Trial structure follows the spec directly.
    T_forced::Int = 20
    T_probe::Int = 3
    revision_threshold::Float64 = 0.50

    # Policy precision: high enough to separate probe choices without making
    # them deterministically brittle under small belief changes.
    policy_precision::Float64 = 4.0
    probe_policy_precision::Float64 = 4.6

    # Move 2: Self-energy rebalances part precision vs context precision.
    # These are inherited from the v1 logic, but slightly softened so the
    # three-condition gradient is visible across 20 forced steps.
    beta_se::Float64 = 2.2
    gamma_se::Float64 = 2.0
    pi_part::Float64 = 3.2
    lambda_ctx::Float64 = 0.9
    r_t::Float64 = 1.0

    # Move 3: witnessing opens from inverse capture only after context precision
    # clears an absolute floor. `alpha_witness > 1` makes opening superlinear.
    lambda_witness_max::Float64 = 5.5
    alpha_witness::Float64 = 3.0
    lambda_witness_floor::Float64 = 2.75

    # Modality weights. These are not fitted to a target curve; they only
    # express the intended asymmetry: informational context matters more than a
    # single external cue, and witnessed self-state should dominate once open.
    weight_external::Float64 = 0.18
    weight_intero::Float64 = 0.18
    weight_outcome::Float64 = 0.16
    weight_info::Float64 = 0.24
    weight_witness::Float64 = 1.0

    # Initial burdened priors. Strong but not locked: the model should revise
    # when the mechanism is right, not only under knife-edge parameters.
    d_self_helpless::Float64 = 18.0
    d_self_capable::Float64 = 2.0
    d_threat_dangerous::Float64 = 16.0
    d_threat_safe::Float64 = 4.0
    d_outcome_avoidance::Float64 = 15.0
    d_outcome_manageable::Float64 = 5.0
end

struct IFSV2ConditionConfig
    name::String
    context::Int
    E_t::Float64
    forced_action::Int
    T_forced::Int
    T_probe::Int
    freeze_probe_learning::Bool
    no_contact::Bool
end

struct IFSV2Environment
    context::Int
    actual_self::Int
    actual_threat::Int
    actual_outcome::Int
end

struct IFSV2Model
    architecture::Symbol
    params::IFSV2Params
    A_reference::Vector{Array{Float64,4}}
    B_self::Array{Float64,3}
    B_threat::Array{Float64,3}
    B_outcome::Array{Float64,3}
    D::Vector{Vector{Float64}}
end

struct IFSV2StepResult
    timestep::Int
    phase::Symbol
    action::Int
    observations::NTuple{5,Int}
    p_self_revised::Float64
    p_threat_safe::Float64
    p_outcome_manageable::Float64
    p_avoid::Float64
    p_inspect::Float64
    p_stay::Float64
    p_approach_stay::Float64
    capture::Float64
    witness_precision::Float64
end

struct IFSV2Metrics
    revision_threshold::Float64
    first_passage_self::Union{Nothing,Int}
    first_passage_threat::Union{Nothing,Int}
    first_passage_outcome::Union{Nothing,Int}
    first_passage_policy::Union{Nothing,Int}
    lag_self_to_threat::Union{Nothing,Int}
    lag_threat_to_outcome::Union{Nothing,Int}
    lag_outcome_to_policy::Union{Nothing,Int}
    cascade_present::Bool
end

struct IFSV2Run
    condition::String
    architecture::Symbol
    steps::Vector{IFSV2StepResult}
    metrics::IFSV2Metrics
    params::IFSV2Params
end

struct IFSV2Summary
    condition::String
    architecture::Symbol
    runs::Vector{IFSV2Run}
    mean_self::Vector{Float64}
    std_self::Vector{Float64}
    mean_threat::Vector{Float64}
    std_threat::Vector{Float64}
    mean_outcome::Vector{Float64}
    std_outcome::Vector{Float64}
    mean_policy::Vector{Float64}
    std_policy::Vector{Float64}
    mean_capture::Vector{Float64}
    std_capture::Vector{Float64}
    mean_witness::Vector{Float64}
    std_witness::Vector{Float64}
    mean_probe_policy::Matrix{Float64}
    std_probe_policy::Matrix{Float64}
    metric_means::Dict{Symbol,Float64}
    metric_stds::Dict{Symbol,Float64}
end

# ============================================================================
# CONDITION HELPERS
# ============================================================================

function baseline_ifs_v2_config(params::IFSV2Params=IFSV2Params())
    IFSV2ConditionConfig("Baseline", IFSV2_CONTEXT_SAFE, 0.10, IFSV2_POLICY_AVOID, params.T_forced, params.T_probe, true, true)
end

function exposure_ifs_v2_config(params::IFSV2Params=IFSV2Params())
    IFSV2ConditionConfig("Exposure", IFSV2_CONTEXT_SAFE, 0.15, IFSV2_POLICY_INSPECT, params.T_forced, params.T_probe, true, false)
end

function informational_ifs_v2_config(params::IFSV2Params=IFSV2Params())
    IFSV2ConditionConfig("Informational", IFSV2_CONTEXT_SAFE, 0.45, IFSV2_POLICY_INSPECT, params.T_forced, params.T_probe, true, false)
end

function relational_depth_ifs_v2_config(params::IFSV2Params=IFSV2Params())
    IFSV2ConditionConfig("Relational Depth", IFSV2_CONTEXT_SAFE, 0.85, IFSV2_POLICY_INSPECT, params.T_forced, params.T_probe, true, false)
end

function real_danger_ifs_v2_config(params::IFSV2Params=IFSV2Params())
    IFSV2ConditionConfig("Real Danger", IFSV2_CONTEXT_DANGEROUS, 0.85, IFSV2_POLICY_INSPECT, params.T_forced, params.T_probe, true, false)
end

function main_ifs_v2_configs(params::IFSV2Params=IFSV2Params())
    [exposure_ifs_v2_config(params), informational_ifs_v2_config(params), relational_depth_ifs_v2_config(params)]
end

function control_ifs_v2_configs(params::IFSV2Params=IFSV2Params())
    [baseline_ifs_v2_config(params), real_danger_ifs_v2_config(params)]
end

function all_ifs_v2_configs(params::IFSV2Params=IFSV2Params())
    [baseline_ifs_v2_config(params); main_ifs_v2_configs(params); real_danger_ifs_v2_config(params)]
end

function IFSV2Environment(context::Int)
    actual_self = context == IFSV2_CONTEXT_DANGEROUS ? IFSV2_SELF_HELPLESS_ALONE : IFSV2_SELF_CAPABLE_PRESENT
    actual_threat = context == IFSV2_CONTEXT_DANGEROUS ? IFSV2_THREAT_DANGEROUS : IFSV2_THREAT_SAFE
    actual_outcome = context == IFSV2_CONTEXT_DANGEROUS ? IFSV2_OUTCOME_AVOIDANCE_SAVES : IFSV2_OUTCOME_CONTACT_MANAGEABLE
    IFSV2Environment(context, actual_self, actual_threat, actual_outcome)
end

# ============================================================================
# UTILITY HELPERS
# ============================================================================

normalize_prob(v::AbstractVector{<:Real}) = begin
    out = Float64.(v)
    total = sum(out)
    total <= 0 && return fill(1.0 / length(out), length(out))
    out ./ total
end

function validate_probability_vector(v::AbstractVector{<:Real}; atol::Float64=1e-8)
    @assert all(v .>= -atol)
    @assert isapprox(sum(v), 1.0; atol=atol)
end

function validate_ifs_v2_A(A::Vector{Array{Float64,4}}; atol::Float64=1e-8)
    @assert length(A) == 5
    for g in eachindex(A)
        @assert size(A[g]) == (IFSV2_NO[g], IFSV2_NS...)
        colsums = sum(A[g], dims=1)
        @assert all(isapprox.(colsums, 1.0; atol=atol)) "A[$g] columns must sum to 1.0"
    end
    return true
end

function validate_ifs_v2_transitions(B_self::Array{Float64,3}, B_threat::Array{Float64,3}, B_outcome::Array{Float64,3}; architecture::Symbol)
    @assert size(B_self) == (2, 2, 3)
    if architecture == :H1
        @assert size(B_threat) == (2, 2, 2)
    else
        @assert size(B_threat) == (2, 2, 3)
    end
    @assert size(B_outcome) == (2, 2, 2)

    for a in axes(B_self, 3)
        @assert all(isapprox.(sum(B_self[:, :, a], dims=1), 1.0; atol=1e-8))
    end
    for k in axes(B_threat, 3)
        @assert all(isapprox.(sum(B_threat[:, :, k], dims=1), 1.0; atol=1e-8))
    end
    for k in axes(B_outcome, 3)
        @assert all(isapprox.(sum(B_outcome[:, :, k], dims=1), 1.0; atol=1e-8))
    end
    return true
end

function override_ifs_v2_params(params::IFSV2Params; kwargs...)
    values = Dict{Symbol,Any}(name => getfield(params, name) for name in fieldnames(IFSV2Params))
    for (k, v) in kwargs
        values[k] = v
    end
    return IFSV2Params(; (; (name => values[name] for name in fieldnames(IFSV2Params))...)...)
end

function compute_ifs_v2_precisions(params::IFSV2Params, E_t::Float64)
    pi_part_eff = params.r_t * params.pi_part * exp(-params.beta_se * E_t)
    lambda_ctx_eff = params.lambda_ctx * exp(params.gamma_se * E_t)
    return pi_part_eff, lambda_ctx_eff
end

function compute_ifs_v2_capture(params::IFSV2Params, E_t::Float64, q_stage1::Vector{Vector{Float64}})
    pi_part_eff, lambda_ctx_eff = compute_ifs_v2_precisions(params, E_t)
    context_signal =
        0.25 +
        0.20 * q_stage1[1][IFSV2_SELF_CAPABLE_PRESENT] +
        0.30 * q_stage1[2][IFSV2_THREAT_SAFE] +
        0.25 * q_stage1[3][IFSV2_OUTCOME_CONTACT_MANAGEABLE]
    effective_context = lambda_ctx_eff * context_signal
    capture = pi_part_eff / (pi_part_eff + effective_context + eps(Float64))
    return clamp(capture, 0.0, 1.0), pi_part_eff, lambda_ctx_eff
end

function compute_ifs_v2_witness_precision(
    params::IFSV2Params,
    capture::Float64,
    lambda_ctx_eff::Float64
)
    floor_term = clamp((lambda_ctx_eff - params.lambda_witness_floor) / params.lambda_witness_floor, 0.0, 1.0)
    witness = params.lambda_witness_max * (1.0 - capture)^params.alpha_witness * floor_term
    return params.weight_witness * witness
end

# ============================================================================
# MATRIX CONSTRUCTION
# ============================================================================

function build_ifs_v2_D(params::IFSV2Params)
    D = Vector{Vector{Float64}}(undef, 3)
    D[1] = normalize_prob([params.d_self_helpless, params.d_self_capable])
    D[2] = normalize_prob([params.d_threat_dangerous, params.d_threat_safe])
    D[3] = normalize_prob([params.d_outcome_avoidance, params.d_outcome_manageable])
    return D
end

function build_ifs_v2_A_h1(
    params::IFSV2Params=IFSV2Params();
    context::Int=IFSV2_CONTEXT_SAFE,
    action::Int=IFSV2_POLICY_INSPECT
)
    A = [zeros(Float64, IFSV2_NO[g], IFSV2_NS...) for g in 1:5]

    # Channel 1: external cue. Primarily threat-informative.
    for s in 1:2, o in 1:2
        if action == IFSV2_POLICY_AVOID
            if context == IFSV2_CONTEXT_SAFE
                A[1][:, s, IFSV2_THREAT_DANGEROUS, o] = [0.82, 0.13, 0.05]
                A[1][:, s, IFSV2_THREAT_SAFE, o] = [0.78, 0.18, 0.04]
            else
                A[1][:, s, IFSV2_THREAT_DANGEROUS, o] = [0.55, 0.10, 0.35]
                A[1][:, s, IFSV2_THREAT_SAFE, o] = [0.60, 0.20, 0.20]
            end
        elseif action == IFSV2_POLICY_STAY
            if context == IFSV2_CONTEXT_SAFE
                A[1][:, s, IFSV2_THREAT_DANGEROUS, o] = [0.65, 0.20, 0.15]
                A[1][:, s, IFSV2_THREAT_SAFE, o] = [0.45, 0.45, 0.10]
            else
                A[1][:, s, IFSV2_THREAT_DANGEROUS, o] = [0.25, 0.15, 0.60]
                A[1][:, s, IFSV2_THREAT_SAFE, o] = [0.35, 0.30, 0.35]
            end
        elseif context == IFSV2_CONTEXT_SAFE
            A[1][:, s, IFSV2_THREAT_DANGEROUS, o] = [0.46, 0.30, 0.24]
            A[1][:, s, IFSV2_THREAT_SAFE, o] = [0.30, 0.52, 0.18]
        else
            A[1][:, s, IFSV2_THREAT_DANGEROUS, o] = [0.15, 0.10, 0.75]
            A[1][:, s, IFSV2_THREAT_SAFE, o] = [0.25, 0.25, 0.50]
        end
    end

    # Channel 2: interoception. In H1 this is strongly self-modulated.
    for o in 1:2
        A[2][:, IFSV2_SELF_HELPLESS_ALONE, IFSV2_THREAT_DANGEROUS, o] = [0.05, 0.20, 0.75]
        A[2][:, IFSV2_SELF_HELPLESS_ALONE, IFSV2_THREAT_SAFE, o] = [0.25, 0.50, 0.25]
        A[2][:, IFSV2_SELF_CAPABLE_PRESENT, IFSV2_THREAT_DANGEROUS, o] = [0.10, 0.60, 0.30]
        A[2][:, IFSV2_SELF_CAPABLE_PRESENT, IFSV2_THREAT_SAFE, o] = [0.70, 0.22, 0.08]
    end

    # Channel 3: action outcome. Depends on expected outcome and environment.
    outcome_avoid = zeros(3)
    outcome_manage = zeros(3)
    if context == IFSV2_CONTEXT_SAFE
        if action == IFSV2_POLICY_AVOID
            outcome_avoid .= [0.78, 0.19, 0.03]
            outcome_manage .= [0.22, 0.68, 0.10]
        elseif action == IFSV2_POLICY_INSPECT
            outcome_avoid .= [0.15, 0.45, 0.40]
            outcome_manage .= [0.25, 0.65, 0.10]
        else
            outcome_avoid .= [0.20, 0.50, 0.30]
            outcome_manage .= [0.45, 0.45, 0.10]
        end
    else
        if action == IFSV2_POLICY_AVOID
            outcome_avoid .= [0.78, 0.18, 0.04]
            outcome_manage .= [0.70, 0.22, 0.08]
        elseif action == IFSV2_POLICY_INSPECT
            outcome_avoid .= [0.10, 0.20, 0.70]
            outcome_manage .= [0.08, 0.22, 0.70]
        else
            outcome_avoid .= [0.10, 0.25, 0.65]
            outcome_manage .= [0.10, 0.25, 0.65]
        end
    end
    for s in 1:2, m in 1:2
        A[3][:, s, m, IFSV2_OUTCOME_AVOIDANCE_SAVES] = outcome_avoid
        A[3][:, s, m, IFSV2_OUTCOME_CONTACT_MANAGEABLE] = outcome_manage
    end

    # Channel 4: informational context. In H1 this helps, but does not by itself
    # force self revision; it mostly scaffolds later opening of channel 5.
    if context == IFSV2_CONTEXT_SAFE
        A[4][:, IFSV2_SELF_HELPLESS_ALONE, IFSV2_THREAT_DANGEROUS, :] .= [0.60, 0.40]
        A[4][:, IFSV2_SELF_HELPLESS_ALONE, IFSV2_THREAT_SAFE, :] .= [0.57, 0.43]
        A[4][:, IFSV2_SELF_CAPABLE_PRESENT, IFSV2_THREAT_DANGEROUS, :] .= [0.46, 0.54]
        A[4][:, IFSV2_SELF_CAPABLE_PRESENT, IFSV2_THREAT_SAFE, :] .= [0.38, 0.62]
    else
        A[4][:, IFSV2_SELF_HELPLESS_ALONE, IFSV2_THREAT_DANGEROUS, :] .= [0.72, 0.28]
        A[4][:, IFSV2_SELF_HELPLESS_ALONE, IFSV2_THREAT_SAFE, :] .= [0.65, 0.35]
        A[4][:, IFSV2_SELF_CAPABLE_PRESENT, IFSV2_THREAT_DANGEROUS, :] .= [0.60, 0.40]
        A[4][:, IFSV2_SELF_CAPABLE_PRESENT, IFSV2_THREAT_SAFE, :] .= [0.55, 0.45]
    end
    if action == IFSV2_POLICY_AVOID
        neutral_context = context == IFSV2_CONTEXT_SAFE ? [0.56, 0.44] : [0.68, 0.32]
        for s in 1:2, m in 1:2
            A[4][:, s, m, :] .= neutral_context
        end
    elseif action == IFSV2_POLICY_STAY
        muted_context = context == IFSV2_CONTEXT_SAFE ? [0.52, 0.48] : [0.62, 0.38]
        for s in 1:2, m in 1:2
            A[4][:, s, m, :] .= 0.5 .* A[4][:, s, m, :] .+ 0.5 .* muted_context
        end
    end

    # Channel 5: witnessed self-state. The key modality; precision gating happens
    # during inference, not in the raw likelihood table.
    for m in 1:2, o in 1:2
        A[5][:, IFSV2_SELF_HELPLESS_ALONE, m, o] = [0.995, 0.005]
        A[5][:, IFSV2_SELF_CAPABLE_PRESENT, m, o] = [0.005, 0.995]
    end

    validate_ifs_v2_A(A)
    return A
end

function build_ifs_v2_A_h2(
    params::IFSV2Params=IFSV2Params();
    context::Int=IFSV2_CONTEXT_SAFE,
    action::Int=IFSV2_POLICY_INSPECT
)
    A = build_ifs_v2_A_h1(params; context=context, action=action)

    # H2: interoception and informational context are more threat-primary and
    # less directly diagnostic of self-state.
    for o in 1:2
        A[2][:, IFSV2_SELF_HELPLESS_ALONE, IFSV2_THREAT_DANGEROUS, o] = [0.05, 0.28, 0.67]
        A[2][:, IFSV2_SELF_CAPABLE_PRESENT, IFSV2_THREAT_DANGEROUS, o] = [0.07, 0.33, 0.60]
        A[2][:, IFSV2_SELF_HELPLESS_ALONE, IFSV2_THREAT_SAFE, o] = [0.50, 0.35, 0.15]
        A[2][:, IFSV2_SELF_CAPABLE_PRESENT, IFSV2_THREAT_SAFE, o] = [0.56, 0.29, 0.15]
    end

    if context == IFSV2_CONTEXT_SAFE
        A[4][:, IFSV2_SELF_HELPLESS_ALONE, IFSV2_THREAT_DANGEROUS, :] .= [0.70, 0.30]
        A[4][:, IFSV2_SELF_HELPLESS_ALONE, IFSV2_THREAT_SAFE, :] .= [0.24, 0.76]
        A[4][:, IFSV2_SELF_CAPABLE_PRESENT, IFSV2_THREAT_DANGEROUS, :] .= [0.68, 0.32]
        A[4][:, IFSV2_SELF_CAPABLE_PRESENT, IFSV2_THREAT_SAFE, :] .= [0.20, 0.80]
    else
        A[4][:, IFSV2_SELF_HELPLESS_ALONE, IFSV2_THREAT_DANGEROUS, :] .= [0.88, 0.12]
        A[4][:, IFSV2_SELF_HELPLESS_ALONE, IFSV2_THREAT_SAFE, :] .= [0.60, 0.40]
        A[4][:, IFSV2_SELF_CAPABLE_PRESENT, IFSV2_THREAT_DANGEROUS, :] .= [0.85, 0.15]
        A[4][:, IFSV2_SELF_CAPABLE_PRESENT, IFSV2_THREAT_SAFE, :] .= [0.58, 0.42]
    end
    if action == IFSV2_POLICY_AVOID
        neutral_context = context == IFSV2_CONTEXT_SAFE ? [0.58, 0.42] : [0.72, 0.28]
        for s in 1:2, m in 1:2
            A[4][:, s, m, :] .= neutral_context
        end
    elseif action == IFSV2_POLICY_STAY
        muted_context = context == IFSV2_CONTEXT_SAFE ? [0.50, 0.50] : [0.64, 0.36]
        for s in 1:2, m in 1:2
            A[4][:, s, m, :] .= 0.5 .* A[4][:, s, m, :] .+ 0.5 .* muted_context
        end
    end

    validate_ifs_v2_A(A)
    return A
end

function build_ifs_v2_B_h1()
    B_self = zeros(Float64, 2, 2, 3)
    B_self[:, :, IFSV2_POLICY_AVOID] = [0.97 0.16; 0.03 0.84]
    B_self[:, :, IFSV2_POLICY_INSPECT] = [0.94 0.10; 0.06 0.90]
    B_self[:, :, IFSV2_POLICY_STAY] = [0.93 0.08; 0.07 0.92]

    # Conditioned on self-state.
    B_threat = zeros(Float64, 2, 2, 2)
    B_threat[:, :, IFSV2_SELF_HELPLESS_ALONE] = [0.98 0.42; 0.02 0.58]
    B_threat[:, :, IFSV2_SELF_CAPABLE_PRESENT] = [0.58 0.02; 0.42 0.98]

    # Conditioned on threat meaning.
    B_outcome = zeros(Float64, 2, 2, 2)
    B_outcome[:, :, IFSV2_THREAT_DANGEROUS] = [0.94 0.28; 0.06 0.72]
    B_outcome[:, :, IFSV2_THREAT_SAFE] = [0.72 0.05; 0.28 0.95]

    validate_ifs_v2_transitions(B_self, B_threat, B_outcome; architecture=:H1)
    return B_self, B_threat, B_outcome
end

function build_ifs_v2_B_h2()
    B_self = zeros(Float64, 2, 2, 3)
    B_self[:, :, IFSV2_POLICY_AVOID] = [0.95 0.18; 0.05 0.82]
    B_self[:, :, IFSV2_POLICY_INSPECT] = [0.92 0.14; 0.08 0.86]
    B_self[:, :, IFSV2_POLICY_STAY] = [0.86 0.08; 0.14 0.92]

    # Threat is upstream in H2, so action contact moves threat first.
    B_threat = zeros(Float64, 2, 2, 3)
    B_threat[:, :, IFSV2_POLICY_AVOID] = [0.96 0.20; 0.04 0.80]
    B_threat[:, :, IFSV2_POLICY_INSPECT] = [0.82 0.10; 0.18 0.90]
    B_threat[:, :, IFSV2_POLICY_STAY] = [0.88 0.12; 0.12 0.88]

    # Self is downstream of threat in H2.
    B_outcome = zeros(Float64, 2, 2, 2)
    B_outcome[:, :, IFSV2_THREAT_DANGEROUS] = [0.93 0.24; 0.07 0.76]
    B_outcome[:, :, IFSV2_THREAT_SAFE] = [0.80 0.08; 0.20 0.92]

    validate_ifs_v2_transitions(B_self, B_threat, B_outcome; architecture=:H2)
    return B_self, B_threat, B_outcome
end

function build_ifs_v2_model(; architecture::Symbol=:H1, params::IFSV2Params=IFSV2Params())
    D = build_ifs_v2_D(params)
    if architecture == :H1
        B_self, B_threat, B_outcome = build_ifs_v2_B_h1()
        A_reference = build_ifs_v2_A_h1(params; context=IFSV2_CONTEXT_SAFE, action=IFSV2_POLICY_INSPECT)
    elseif architecture == :H2
        B_self, B_threat, B_outcome = build_ifs_v2_B_h2()
        A_reference = build_ifs_v2_A_h2(params; context=IFSV2_CONTEXT_SAFE, action=IFSV2_POLICY_INSPECT)
    else
        error("Unknown architecture: $architecture")
    end
    return IFSV2Model(architecture, params, A_reference, B_self, B_threat, B_outcome, D)
end

# ============================================================================
# INFERENCE, POLICY, AND DYNAMICS
# ============================================================================

function build_ifs_v2_A(
    model::IFSV2Model,
    env::IFSV2Environment,
    action::Int
)
    if model.architecture == :H1
        return build_ifs_v2_A_h1(model.params; context=env.context, action=action)
    end
    return build_ifs_v2_A_h2(model.params; context=env.context, action=action)
end

function sample_ifs_v2_observation(
    A::Vector{Array{Float64,4}},
    env::IFSV2Environment
)
    s = env.actual_self
    m = env.actual_threat
    o = env.actual_outcome
    obs = ntuple(5) do g
        sample_categorical(A[g][:, s, m, o])
    end
    return obs
end

function infer_ifs_v2_stage(
    prior::Vector{Vector{Float64}},
    A::Vector{Array{Float64,4}},
    obs::NTuple{5,Int},
    weights::NTuple{5,Float64};
    active_modalities=1:5,
    max_iter::Int=12,
    tol::Float64=1e-7
)
    qs = [copy(prior[f]) for f in 1:3]
    for iter in 1:max_iter
        qs_old = [copy(q) for q in qs]
        for f in 1:3
            ln_q = log.(prior[f] .+ eps(Float64))
            for g in active_modalities
                weight = weights[g]
                weight <= 0 && continue
                ln_q .+= weight .* compute_ln_A_marginal(A[g], obs[g], qs, f, IFSV2_NS)
            end
            qs[f] .= softmax(ln_q)
        end
        max_diff = maximum(maximum(abs.(qs[f] .- qs_old[f])) for f in 1:3)
        max_diff < tol && break
    end
    return qs
end

function compute_ifs_v2_policy_probs(q::Vector{Vector{Float64}}, params::IFSV2Params)
    return compute_ifs_v2_policy_probs(q, params; probe=false)
end

function compute_ifs_v2_policy_probs(
    q::Vector{Vector{Float64}},
    params::IFSV2Params;
    probe::Bool=false,
    capture::Union{Nothing,Float64}=nothing
)
    p_self_helpless = q[1][IFSV2_SELF_HELPLESS_ALONE]
    p_self_capable = q[1][IFSV2_SELF_CAPABLE_PRESENT]
    p_threat_danger = q[2][IFSV2_THREAT_DANGEROUS]
    p_threat_safe = q[2][IFSV2_THREAT_SAFE]
    p_outcome_avoid = q[3][IFSV2_OUTCOME_AVOIDANCE_SAVES]
    p_outcome_manage = q[3][IFSV2_OUTCOME_CONTACT_MANAGEABLE]

    uncertainty_bonus = 1.0 - abs(2.0 * p_threat_safe - 1.0)
    if probe
        capture_value = isnothing(capture) ? 0.5 : clamp(capture, 0.0, 1.0)
        mid_capture_bonus = clamp(1.0 - abs(capture_value - 0.40) / 0.40, 0.0, 1.0)
        avoid_score = 1.7 * p_self_helpless + 1.3 * p_threat_danger + 2.0 * p_outcome_avoid
        inspect_score = 0.75 * p_self_capable + 0.40 * p_threat_safe + 0.40 * p_outcome_manage + 1.05 * uncertainty_bonus
        stay_score = 0.82 * p_self_capable + 0.20 * p_threat_safe + 1.05 * p_outcome_manage
        avoid_score += 1.10 * capture_value
        inspect_score += 0.95 * mid_capture_bonus
        stay_score += 0.95 * (1.0 - capture_value)
        scores = params.probe_policy_precision .* [avoid_score, inspect_score, stay_score]
        return softmax(scores)
    end

    avoid_score = 1.5 * p_self_helpless + 1.1 * p_threat_danger + 2.2 * p_outcome_avoid
    inspect_score = 0.5 * p_self_capable + 0.2 * p_threat_safe + 0.7 * p_outcome_manage + 0.7 * uncertainty_bonus
    stay_score = 1.0 * p_self_capable + 0.3 * p_threat_safe + 2.4 * p_outcome_manage

    scores = params.policy_precision .* [avoid_score, inspect_score, stay_score]
    return softmax(scores)
end

function select_ifs_v2_action(
    q::Vector{Vector{Float64}},
    params::IFSV2Params;
    deterministic::Bool=false,
    probe::Bool=false,
    capture::Union{Nothing,Float64}=nothing
)
    policy_probs = compute_ifs_v2_policy_probs(q, params; probe=probe, capture=capture)
    if deterministic
        return argmax(policy_probs), policy_probs
    end
    return sample_categorical(policy_probs), policy_probs
end

function infer_ifs_v2_probe_beliefs(
    model::IFSV2Model,
    env::IFSV2Environment,
    prior::Vector{Vector{Float64}},
    config::IFSV2ConditionConfig
)
    params = model.params
    probe_A = build_ifs_v2_A(model, env, IFSV2_POLICY_INSPECT)
    probe_obs = (
        IFSV2_EXT_AMBIGUOUS,
        IFSV2_INT_ACTIVATED,
        IFSV2_ACT_NEUTRAL,
        IFSV2_INFO_SUPPORTED_HERE_NOW,
        env.actual_self == IFSV2_SELF_CAPABLE_PRESENT ? IFSV2_WIT_CAPABLE_PRESENT : IFSV2_WIT_HELPLESS_ALONE,
    )

    pi_eff, lambda_ctx_eff = compute_ifs_v2_precisions(params, config.E_t)
    stage1_weights = (
        params.weight_external * 1.20 * lambda_ctx_eff,
        params.weight_intero * (1.15 * pi_eff + 0.05 * lambda_ctx_eff),
        0.0,
        params.weight_info * 0.55 * lambda_ctx_eff,
        0.0,
    )

    q_stage1 = infer_ifs_v2_stage(prior, probe_A, probe_obs, stage1_weights; active_modalities=(1, 2, 4))
    capture, _, lambda_ctx_eff = compute_ifs_v2_capture(params, config.E_t, q_stage1)
    witness_precision = compute_ifs_v2_witness_precision(params, capture, lambda_ctx_eff)

    stage2_weights = (
        stage1_weights[1],
        stage1_weights[2],
        stage1_weights[3],
        stage1_weights[4],
        model.architecture == :H2 ? 0.0 : witness_precision,
    )
    q_probe = infer_ifs_v2_stage(prior, probe_A, probe_obs, stage2_weights; active_modalities=(1, 2, 4, 5))
    return q_probe, probe_obs, capture, witness_precision
end

function propagate_ifs_v2_beliefs(
    model::IFSV2Model,
    q::Vector{Vector{Float64}},
    action::Int
)
    next_q = Vector{Vector{Float64}}(undef, 3)

    # Self transitions are action-conditioned in both architectures.
    next_q[1] = normalize_prob(model.B_self[:, :, action] * q[1])

    if model.architecture == :H1
        threat_next = zeros(Float64, 2)
        for s in 1:2
            threat_next .+= q[1][s] .* (model.B_threat[:, :, s] * q[2])
        end
        next_q[2] = normalize_prob(threat_next)
    else
        next_q[2] = normalize_prob(model.B_threat[:, :, action] * q[2])
    end

    outcome_next = zeros(Float64, 2)
    for m in 1:2
        outcome_next .+= next_q[2][m] .* (model.B_outcome[:, :, m] * q[3])
    end
    next_q[3] = normalize_prob(outcome_next)

    if model.architecture == :H2
        self_downstream = zeros(Float64, 2)
        safe_matrix = [0.95 0.30; 0.05 0.70]
        danger_matrix = [0.98 0.42; 0.02 0.58]
        for m in 1:2
            matrix = m == IFSV2_THREAT_SAFE ? safe_matrix : danger_matrix
            self_downstream .+= next_q[2][m] .* (matrix * next_q[1])
        end
        next_q[1] = normalize_prob(self_downstream)
    end

    return next_q
end

function first_passage_time(x::Vector{Float64}, threshold::Float64)
    for t in eachindex(x)
        x[t] >= threshold && return t
    end
    return nothing
end

function compute_ifs_v2_metrics(steps::Vector{IFSV2StepResult}, params::IFSV2Params)
    self_traj = [s.p_self_revised for s in steps]
    threat_traj = [s.p_threat_safe for s in steps]
    outcome_traj = [s.p_outcome_manageable for s in steps]
    probe_steps = filter(s -> s.phase == :probe, steps)
    probe_policy_traj = [s.p_approach_stay for s in probe_steps]
    forced_steps = count(s -> s.phase == :forced, steps)

    t_self = first_passage_time(self_traj, params.revision_threshold)
    t_threat = first_passage_time(threat_traj, params.revision_threshold)
    t_outcome = first_passage_time(outcome_traj, params.revision_threshold)
    t_policy_probe = first_passage_time(probe_policy_traj, params.revision_threshold)
    t_policy = isnothing(t_policy_probe) ? nothing : forced_steps + t_policy_probe

    lag_self_to_threat = isnothing(t_self) || isnothing(t_threat) ? nothing : (t_threat - t_self)
    lag_threat_to_outcome = isnothing(t_threat) || isnothing(t_outcome) ? nothing : (t_outcome - t_threat)
    lag_outcome_to_policy = isnothing(t_outcome) || isnothing(t_policy) ? nothing : (t_policy - t_outcome)

    cascade_present = !isnothing(t_self) &&
        !isnothing(t_threat) &&
        !isnothing(t_outcome) &&
        !isnothing(t_policy) &&
        t_self < t_threat < t_outcome < t_policy

    return IFSV2Metrics(
        params.revision_threshold,
        t_self, t_threat, t_outcome, t_policy,
        lag_self_to_threat, lag_threat_to_outcome, lag_outcome_to_policy,
        cascade_present
    )
end

# ============================================================================
# MAIN SIMULATION LOOP
# ============================================================================

function run_ifs_v2_condition(
    model::IFSV2Model,
    config::IFSV2ConditionConfig;
    seed::Int=42,
    verbose::Bool=false,
    deterministic_probe::Bool=false
)
    Random.seed!(seed)
    env = IFSV2Environment(config.context)
    params = model.params

    @assert config.T_forced > 0
    @assert config.T_probe >= 1

    prior = [copy(d) for d in model.D]
    steps = IFSV2StepResult[]

    total_steps = config.T_forced + config.T_probe
    final_forced_belief = nothing
    final_forced_capture = 1.0
    final_forced_witness = 0.0

    for t in 1:total_steps
        phase = t <= config.T_forced ? :forced : :probe

        if phase == :forced
            action = config.forced_action > 0 ? config.forced_action : select_ifs_v2_action(prior, params; deterministic=true)[1]
            A = build_ifs_v2_A(model, env, action)
            obs = sample_ifs_v2_observation(A, env)

            if config.no_contact
                capture, _, lambda_ctx_eff = compute_ifs_v2_capture(params, config.E_t, prior)
                witness_precision = compute_ifs_v2_witness_precision(params, capture, lambda_ctx_eff)
                policy_probs = compute_ifs_v2_policy_probs(prior, params)
                push!(steps, IFSV2StepResult(
                    t,
                    phase,
                    action,
                    obs,
                    prior[1][IFSV2_SELF_CAPABLE_PRESENT],
                    prior[2][IFSV2_THREAT_SAFE],
                    prior[3][IFSV2_OUTCOME_CONTACT_MANAGEABLE],
                    policy_probs[IFSV2_POLICY_AVOID],
                    policy_probs[IFSV2_POLICY_INSPECT],
                    policy_probs[IFSV2_POLICY_STAY],
                    policy_probs[IFSV2_POLICY_INSPECT] + policy_probs[IFSV2_POLICY_STAY],
                    capture,
                    witness_precision
                ))
                final_forced_belief = [copy(q) for q in prior]
                final_forced_capture = capture
                final_forced_witness = witness_precision
                continue
            end

            pi_eff, lambda_ctx_eff = compute_ifs_v2_precisions(params, config.E_t)
            stage1_weights = (
                params.weight_external * lambda_ctx_eff,
                params.weight_intero * (0.6 * pi_eff + 0.4 * lambda_ctx_eff),
                params.weight_outcome * lambda_ctx_eff * max(0.25, prior[2][IFSV2_THREAT_SAFE]),
                params.weight_info * lambda_ctx_eff,
                0.0,
            )

            q_stage1 = infer_ifs_v2_stage(prior, A, obs, stage1_weights; active_modalities=1:4)
            capture, _, lambda_ctx_eff = compute_ifs_v2_capture(params, config.E_t, q_stage1)
            witness_precision = compute_ifs_v2_witness_precision(params, capture, lambda_ctx_eff)

            witness_scale = model.architecture == :H2 ? 0.0 : 1.0
            stage2_weights = (
                stage1_weights[1],
                stage1_weights[2],
                stage1_weights[3],
                stage1_weights[4],
                witness_scale * witness_precision,
            )
            q_final = infer_ifs_v2_stage(prior, A, obs, stage2_weights; active_modalities=1:5)
            policy_probs = compute_ifs_v2_policy_probs(q_final, params)

            push!(steps, IFSV2StepResult(
                t,
                phase,
                action,
                obs,
                q_final[1][IFSV2_SELF_CAPABLE_PRESENT],
                q_final[2][IFSV2_THREAT_SAFE],
                q_final[3][IFSV2_OUTCOME_CONTACT_MANAGEABLE],
                policy_probs[IFSV2_POLICY_AVOID],
                policy_probs[IFSV2_POLICY_INSPECT],
                policy_probs[IFSV2_POLICY_STAY],
                policy_probs[IFSV2_POLICY_INSPECT] + policy_probs[IFSV2_POLICY_STAY],
                capture,
                witness_precision
            ))

            verbose && println(
                "t=$t phase=$phase action=$action obs=$(collect(obs)) ",
                "self=$(round(q_final[1][2], digits=3)) threat=$(round(q_final[2][2], digits=3)) ",
                "outcome=$(round(q_final[3][2], digits=3)) capture=$(round(capture, digits=3)) ",
                "witness=$(round(witness_precision, digits=3)) qpi=$(round.(policy_probs, digits=3))"
            )

            prior = propagate_ifs_v2_beliefs(model, q_final, action)
            final_forced_belief = [copy(q) for q in q_final]
            final_forced_capture = capture
            final_forced_witness = witness_precision
        else
            @assert final_forced_belief !== nothing "Forced phase must run before the probe."
            frozen = final_forced_belief::Vector{Vector{Float64}}
            q_probe, obs, capture, witness_precision = infer_ifs_v2_probe_beliefs(model, env, frozen, config)
            action, policy_probs = select_ifs_v2_action(q_probe, params; deterministic=deterministic_probe, probe=true, capture=capture)
            push!(steps, IFSV2StepResult(
                t,
                phase,
                action,
                obs,
                q_probe[1][IFSV2_SELF_CAPABLE_PRESENT],
                q_probe[2][IFSV2_THREAT_SAFE],
                q_probe[3][IFSV2_OUTCOME_CONTACT_MANAGEABLE],
                policy_probs[IFSV2_POLICY_AVOID],
                policy_probs[IFSV2_POLICY_INSPECT],
                policy_probs[IFSV2_POLICY_STAY],
                policy_probs[IFSV2_POLICY_INSPECT] + policy_probs[IFSV2_POLICY_STAY],
                capture,
                witness_precision
            ))
        end
    end

    metrics = compute_ifs_v2_metrics(steps, params)
    return IFSV2Run(config.name, model.architecture, steps, metrics, params)
end

# ============================================================================
# AGGREGATION
# ============================================================================

function _mean_std_matrix(data::Matrix{Float64})
    return vec(mean(data; dims=2)), vec(std(data; dims=2))
end

function _metric_values(runs::Vector{IFSV2Run}, getter::Function)
    values = Float64[]
    for run in runs
        value = getter(run.metrics)
        isnothing(value) && continue
        push!(values, Float64(value))
    end
    isempty(values) && return NaN, NaN
    return mean(values), std(values)
end

function summarize_ifs_v2_runs(runs::Vector{IFSV2Run})
    @assert !isempty(runs)
    T = length(runs[1].steps)
    N = length(runs)

    self_mat = zeros(Float64, T, N)
    threat_mat = zeros(Float64, T, N)
    outcome_mat = zeros(Float64, T, N)
    policy_mat = zeros(Float64, T, N)
    capture_mat = zeros(Float64, T, N)
    witness_mat = zeros(Float64, T, N)
    probe_policy_mat = zeros(Float64, 3, runs[1].params.T_probe, N)

    for (j, run) in enumerate(runs)
        for (t, step) in enumerate(run.steps)
            self_mat[t, j] = step.p_self_revised
            threat_mat[t, j] = step.p_threat_safe
            outcome_mat[t, j] = step.p_outcome_manageable
            policy_mat[t, j] = step.p_approach_stay
            capture_mat[t, j] = step.capture
            witness_mat[t, j] = step.witness_precision
        end

        probe_steps = filter(s -> s.phase == :probe, run.steps)
        for (k, step) in enumerate(probe_steps)
            probe_policy_mat[1, k, j] = step.p_avoid
            probe_policy_mat[2, k, j] = step.p_inspect
            probe_policy_mat[3, k, j] = step.p_stay
        end
    end

    mean_probe_policy = dropdims(mean(probe_policy_mat; dims=3), dims=3)
    std_probe_policy = dropdims(std(probe_policy_mat; dims=3), dims=3)

    metric_means = Dict{Symbol,Float64}()
    metric_stds = Dict{Symbol,Float64}()
    for (label, getter) in [
        (:first_passage_self, m -> m.first_passage_self),
        (:first_passage_threat, m -> m.first_passage_threat),
        (:first_passage_outcome, m -> m.first_passage_outcome),
        (:first_passage_policy, m -> m.first_passage_policy),
        (:lag_self_to_threat, m -> m.lag_self_to_threat),
        (:lag_threat_to_outcome, m -> m.lag_threat_to_outcome),
        (:lag_outcome_to_policy, m -> m.lag_outcome_to_policy),
    ]
        metric_means[label], metric_stds[label] = _metric_values(runs, getter)
    end
    cascade_flags = [run.metrics.cascade_present ? 1.0 : 0.0 for run in runs]
    metric_means[:cascade_rate] = mean(cascade_flags)
    metric_stds[:cascade_rate] = std(cascade_flags)

    mean_self, std_self = _mean_std_matrix(self_mat)
    mean_threat, std_threat = _mean_std_matrix(threat_mat)
    mean_outcome, std_outcome = _mean_std_matrix(outcome_mat)
    mean_policy, std_policy = _mean_std_matrix(policy_mat)
    mean_capture, std_capture = _mean_std_matrix(capture_mat)
    mean_witness, std_witness = _mean_std_matrix(witness_mat)

    return IFSV2Summary(
        runs[1].condition,
        runs[1].architecture,
        runs,
        mean_self, std_self,
        mean_threat, std_threat,
        mean_outcome, std_outcome,
        mean_policy, std_policy,
        mean_capture, std_capture,
        mean_witness, std_witness,
        mean_probe_policy, std_probe_policy,
        metric_means, metric_stds
    )
end

function run_ifs_v2_replications(;
    architecture::Symbol=:H1,
    config::IFSV2ConditionConfig=relational_depth_ifs_v2_config(),
    params::IFSV2Params=IFSV2Params(),
    n_replications::Int=60,
    seed::Int=42,
    verbose::Bool=false
)
    model = build_ifs_v2_model(architecture=architecture, params=params)
    runs = Vector{IFSV2Run}(undef, n_replications)
    for i in 1:n_replications
        runs[i] = run_ifs_v2_condition(
            model,
            config;
            seed=seed + i,
            verbose=verbose && i == 1
        )
    end
    return summarize_ifs_v2_runs(runs)
end

function run_ifs_v2_suite(;
    architecture::Symbol=:H1,
    configs::Vector{IFSV2ConditionConfig}=all_ifs_v2_configs(),
    params::IFSV2Params=IFSV2Params(),
    n_replications::Int=60,
    seed::Int=42
)
    summaries = Vector{IFSV2Summary}(undef, length(configs))
    for (i, config) in enumerate(configs)
        summaries[i] = run_ifs_v2_replications(
            architecture=architecture,
            config=config,
            params=params,
            n_replications=n_replications,
            seed=seed + 100 * i
        )
    end
    return summaries
end

function run_ifs_v2_sensitivity(;
    architecture::Symbol=:H1,
    params::IFSV2Params=IFSV2Params(),
    n_replications::Int=50,
    seed::Int=42
)
    params_to_scale = [
        :beta_se,
        :gamma_se,
        :pi_part,
        :lambda_ctx,
        :lambda_witness_max,
        :alpha_witness,
        :policy_precision,
        :d_self_helpless,
        :d_threat_dangerous,
        :d_outcome_avoidance,
    ]

    relational = relational_depth_ifs_v2_config(params)
    informational = informational_ifs_v2_config(params)
    baseline = baseline_ifs_v2_config(params)
    danger = real_danger_ifs_v2_config(params)

    rows = NamedTuple[]
    for name in params_to_scale
        base_value = getfield(params, name)
        for multiplier in (0.8, 1.2)
            kwargs = NamedTuple{(name,)}((base_value * multiplier,))
            varied = override_ifs_v2_params(params; kwargs...)
            seed_rel = seed + Int(mod(hash((name, multiplier)), 10^8))
            seed_info = seed + Int(mod(hash((name, multiplier, :info)), 10^8))
            seed_base = seed + Int(mod(hash((name, multiplier, :base)), 10^8))
            seed_danger = seed + Int(mod(hash((name, multiplier, :danger)), 10^8))
            rel = run_ifs_v2_replications(
                architecture=architecture,
                config=relational_depth_ifs_v2_config(varied),
                params=varied,
                n_replications=n_replications,
                seed=seed_rel
            )
            info = run_ifs_v2_replications(
                architecture=architecture,
                config=informational_ifs_v2_config(varied),
                params=varied,
                n_replications=n_replications,
                seed=seed_info
            )
            base = run_ifs_v2_replications(
                architecture=architecture,
                config=baseline_ifs_v2_config(varied),
                params=varied,
                n_replications=n_replications,
                seed=seed_base
            )
            dang = run_ifs_v2_replications(
                architecture=architecture,
                config=real_danger_ifs_v2_config(varied),
                params=varied,
                n_replications=n_replications,
                seed=seed_danger
            )

            push!(rows, (
                parameter=name,
                multiplier=multiplier,
                relational_final_self=rel.mean_self[end],
                relational_self_std=rel.std_self[end],
                informational_final_self=info.mean_self[end],
                self_gap=rel.mean_self[end] - info.mean_self[end],
                baseline_drift=abs(base.mean_self[end] - base.mean_self[1]),
                danger_policy= dang.mean_policy[end],
                cascade_rate=rel.metric_means[:cascade_rate],
            ))
        end
    end

    return rows
end
