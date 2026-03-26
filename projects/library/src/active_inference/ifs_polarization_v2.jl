"""
    ifs_polarization_v2.jl - Two-Part Polarization Simulation for the IFS paper

This extends the v2 IFS model with a mixture-of-experts architecture:
- Two burdened part-bundles run the v2 inference loop in parallel
- Both parts receive the same external observations
- Effective precision determines how much each part controls behavior
- Self-energy both reduces capture and adds a distinct non-captured
  inference weight (`pi_self`)
- Low Self-energy produces capture or anti-phase switching
- High Self-energy allows both parts to be witnessed simultaneously
"""

using Random
using Statistics

# ============================================================================
# PART AND MODEL TYPES
# ============================================================================

Base.@kwdef struct IFSPolarizationV2PartSpec
    name::String
    preferred_action::Int
    d_self_helpless::Float64
    d_self_capable::Float64
    d_threat_dangerous::Float64
    d_threat_safe::Float64
    d_outcome_avoidance::Float64
    d_outcome_manageable::Float64
    policy_bias::NTuple{3,Float64}
    precision_scale::Float64 = 1.0
    capture_scale::Float64 = 1.0
    witness_scale::Float64 = 1.0
end

Base.@kwdef struct IFSPolarizationV2Params
    base::IFSV2Params = IFSV2Params(
        T_forced=24,
        T_probe=1,
        policy_precision=4.2,
        probe_policy_precision=4.8,
        beta_se=2.2,
        gamma_se=2.0,
        pi_part=3.3,
        lambda_ctx=0.95,
        lambda_witness_max=5.7,
        alpha_witness=3.0,
        lambda_witness_floor=2.7
    )

    n_steps::Int = 24
    architecture::Symbol = :H1
    context::Int = IFSV2_CONTEXT_SAFE
    initial_action::Int = IFSV2_POLICY_STAY

    # Expert competition
    capture_power::Float64 = 1.25
    preference_power::Float64 = 1.10
    inertia_gain::Float64 = 0.45

    # Self precision opens only when Self-energy is high enough and both
    # bundles are sufficiently decaptured to be held together.
    self_precision_scale::Float64 = 8.0
    self_precision_power::Float64 = 2.6
    self_balance_gain::Float64 = 0.50
    self_witness_gain::Float64 = 0.28

    # Fatigue makes winner-take-all control unstable at low Self-energy,
    # producing the anti-phase "parts war" oscillation.
    fatigue_growth::Float64 = 0.42
    fatigue_decay::Float64 = 0.14
    fatigue_impact::Float64 = 1.15

    # The Self-policy should look flexible rather than like either part.
    self_policy_bias::NTuple{3,Float64} = (-0.20, 0.15, 0.95)
    part_a::IFSPolarizationV2PartSpec = IFSPolarizationV2PartSpec(
        name="Part A",
        preferred_action=IFSV2_POLICY_AVOID,
        d_self_helpless=20.0,
        d_self_capable=2.0,
        d_threat_dangerous=19.0,
        d_threat_safe=1.5,
        d_outcome_avoidance=18.0,
        d_outcome_manageable=2.5,
        policy_bias=(0.95, -0.20, -0.10),
        precision_scale=1.12,
        capture_scale=1.15,
        witness_scale=1.00
    )
    part_b::IFSPolarizationV2PartSpec = IFSPolarizationV2PartSpec(
        name="Part B",
        preferred_action=IFSV2_POLICY_INSPECT,
        d_self_helpless=15.0,
        d_self_capable=5.0,
        d_threat_dangerous=12.0,
        d_threat_safe=8.0,
        d_outcome_avoidance=4.0,
        d_outcome_manageable=16.0,
        policy_bias=(-0.85, 2.10, -0.05),
        precision_scale=1.12,
        capture_scale=1.05,
        witness_scale=1.05
    )
end

struct IFSPolarizationV2ConditionConfig
    name::String
    context::Int
    E_schedule::Vector{Float64}
end

struct IFSPolarizationV2PartModel
    spec::IFSPolarizationV2PartSpec
    model::IFSV2Model
end

struct IFSPolarizationV2Model
    params::IFSPolarizationV2Params
    architecture::Symbol
    part_a::IFSPolarizationV2PartModel
    part_b::IFSPolarizationV2PartModel
    shared_model::IFSV2Model
end

struct IFSPolarizationV2PartStep
    p_self_revised::Float64
    p_threat_safe::Float64
    p_outcome_manageable::Float64
    p_avoid::Float64
    p_approach::Float64
    p_flexible::Float64
    preferred_prob::Float64
    capture::Float64
    witness_precision::Float64
    effective_precision::Float64
    fatigue::Float64
end

struct IFSPolarizationV2StepResult
    timestep::Int
    E_t::Float64
    action::Int
    behavior::Symbol
    observations::NTuple{5,Int}
    part_a::IFSPolarizationV2PartStep
    part_b::IFSPolarizationV2PartStep
    weight_part_a::Float64
    weight_part_b::Float64
    weight_self::Float64
    p_avoid::Float64
    p_approach::Float64
    p_flexible::Float64
end

struct IFSPolarizationV2Metrics
    switching_rate::Float64
    mean_self_weight::Float64
    mean_balance::Float64
    flexible_rate::Float64
    mean_antiphase::Float64
    dual_cascade::Bool
    first_flexible::Union{Nothing,Int}
end

struct IFSPolarizationV2Run
    condition::String
    architecture::Symbol
    steps::Vector{IFSPolarizationV2StepResult}
    metrics::IFSPolarizationV2Metrics
    params::IFSPolarizationV2Params
end

struct IFSPolarizationV2Summary
    condition::String
    architecture::Symbol
    runs::Vector{IFSPolarizationV2Run}
    mean_E::Vector{Float64}
    mean_part_a_self::Vector{Float64}
    std_part_a_self::Vector{Float64}
    mean_part_b_self::Vector{Float64}
    std_part_b_self::Vector{Float64}
    mean_part_a_threat::Vector{Float64}
    std_part_a_threat::Vector{Float64}
    mean_part_b_threat::Vector{Float64}
    std_part_b_threat::Vector{Float64}
    mean_part_a_outcome::Vector{Float64}
    std_part_a_outcome::Vector{Float64}
    mean_part_b_outcome::Vector{Float64}
    std_part_b_outcome::Vector{Float64}
    mean_weight_part_a::Vector{Float64}
    std_weight_part_a::Vector{Float64}
    mean_weight_part_b::Vector{Float64}
    std_weight_part_b::Vector{Float64}
    mean_weight_self::Vector{Float64}
    std_weight_self::Vector{Float64}
    mean_behavior::Matrix{Float64}
    std_behavior::Matrix{Float64}
    metric_means::Dict{Symbol,Float64}
    metric_stds::Dict{Symbol,Float64}
end

# ============================================================================
# CONDITION HELPERS
# ============================================================================

constant_schedule(n_steps::Int, E_t::Float64) = fill(E_t, n_steps)

function ramp_schedule(n_steps::Int, E_start::Float64, E_end::Float64)
    n_steps == 1 && return [E_end]
    return collect(range(E_start, E_end; length=n_steps))
end

function low_ifs_polarization_v2_config(params::IFSPolarizationV2Params=IFSPolarizationV2Params())
    IFSPolarizationV2ConditionConfig("Low Self-Energy", params.context, constant_schedule(params.n_steps, 0.15))
end

function medium_ifs_polarization_v2_config(params::IFSPolarizationV2Params=IFSPolarizationV2Params())
    IFSPolarizationV2ConditionConfig("Medium Self-Energy", params.context, constant_schedule(params.n_steps, 0.50))
end

function high_ifs_polarization_v2_config(params::IFSPolarizationV2Params=IFSPolarizationV2Params())
    IFSPolarizationV2ConditionConfig("High Self-Energy", params.context, constant_schedule(params.n_steps, 0.85))
end

function oscillation_ifs_polarization_v2_config(params::IFSPolarizationV2Params=IFSPolarizationV2Params())
    IFSPolarizationV2ConditionConfig("Oscillation Demo", params.context, constant_schedule(params.n_steps, 0.20))
end

function resolution_ifs_polarization_v2_config(params::IFSPolarizationV2Params=IFSPolarizationV2Params())
    IFSPolarizationV2ConditionConfig("Oscillation to Resolution", params.context, ramp_schedule(params.n_steps, 0.20, 0.85))
end

function main_ifs_polarization_v2_configs(params::IFSPolarizationV2Params=IFSPolarizationV2Params())
    [
        low_ifs_polarization_v2_config(params),
        medium_ifs_polarization_v2_config(params),
        high_ifs_polarization_v2_config(params)
    ]
end

function all_ifs_polarization_v2_configs(params::IFSPolarizationV2Params=IFSPolarizationV2Params())
    [
        low_ifs_polarization_v2_config(params),
        medium_ifs_polarization_v2_config(params),
        high_ifs_polarization_v2_config(params),
        oscillation_ifs_polarization_v2_config(params),
        resolution_ifs_polarization_v2_config(params)
    ]
end

# ============================================================================
# PARAMETER HELPERS
# ============================================================================

function override_ifs_polarization_v2_params(params::IFSPolarizationV2Params; kwargs...)
    values = Dict{Symbol,Any}(name => getfield(params, name) for name in fieldnames(IFSPolarizationV2Params))
    for (k, v) in kwargs
        values[k] = v
    end
    return IFSPolarizationV2Params(; (; (name => values[name] for name in fieldnames(IFSPolarizationV2Params))...)...)
end

function _part_model(
    spec::IFSPolarizationV2PartSpec,
    architecture::Symbol,
    base::IFSV2Params
)
    params = override_ifs_v2_params(
        base;
        d_self_helpless=spec.d_self_helpless,
        d_self_capable=spec.d_self_capable,
        d_threat_dangerous=spec.d_threat_dangerous,
        d_threat_safe=spec.d_threat_safe,
        d_outcome_avoidance=spec.d_outcome_avoidance,
        d_outcome_manageable=spec.d_outcome_manageable,
        policy_precision=base.policy_precision * spec.precision_scale,
        probe_policy_precision=base.probe_policy_precision * spec.precision_scale
    )
    return IFSPolarizationV2PartModel(spec, build_ifs_v2_model(architecture=architecture, params=params))
end

function build_ifs_polarization_v2_model(; params::IFSPolarizationV2Params=IFSPolarizationV2Params())
    architecture = params.architecture
    shared_model = build_ifs_v2_model(architecture=architecture, params=params.base)
    part_a = _part_model(params.part_a, architecture, params.base)
    part_b = _part_model(params.part_b, architecture, params.base)
    return IFSPolarizationV2Model(params, architecture, part_a, part_b, shared_model)
end

# ============================================================================
# INFERENCE HELPERS
# ============================================================================

function _apply_policy_bias(
    base_probs::Vector{Float64},
    bias::NTuple{3,Float64}
)
    scores = log.(base_probs .+ eps(Float64)) .+ collect(bias)
    return softmax(scores)
end

function _infer_part_step(
    part::IFSPolarizationV2PartModel,
    params::IFSPolarizationV2Params,
    env::IFSV2Environment,
    prior::Vector{Vector{Float64}},
    obs::NTuple{5,Int},
    action::Int,
    E_t::Float64
)
    A = build_ifs_v2_A(part.model, env, action)
    pi_eff, lambda_ctx_eff = compute_ifs_v2_precisions(part.model.params, E_t)
    stage1_weights = (
        part.model.params.weight_external * lambda_ctx_eff,
        part.model.params.weight_intero * (0.60 * pi_eff + 0.40 * lambda_ctx_eff),
        part.model.params.weight_outcome * lambda_ctx_eff * max(0.25, prior[2][IFSV2_THREAT_SAFE]),
        part.model.params.weight_info * lambda_ctx_eff,
        0.0,
    )

    q_stage1 = infer_ifs_v2_stage(prior, A, obs, stage1_weights; active_modalities=1:4)
    capture_base, _, lambda_ctx_eff = compute_ifs_v2_capture(part.model.params, E_t, q_stage1)
    capture = clamp(part.spec.capture_scale * capture_base, 0.0, 1.0)
    witness_precision = part.spec.witness_scale * compute_ifs_v2_witness_precision(part.model.params, capture, lambda_ctx_eff)

    q_final = infer_ifs_v2_stage(
        prior,
        A,
        obs,
        (
            stage1_weights[1],
            stage1_weights[2],
            stage1_weights[3],
            stage1_weights[4],
            witness_precision,
        );
        active_modalities=1:5
    )

    native_policy = compute_ifs_v2_policy_probs(q_final, part.model.params)
    behavior_probs = _apply_policy_bias(native_policy, part.spec.policy_bias)
    preferred_prob = behavior_probs[part.spec.preferred_action]

    step = IFSPolarizationV2PartStep(
        q_final[1][IFSV2_SELF_CAPABLE_PRESENT],
        q_final[2][IFSV2_THREAT_SAFE],
        q_final[3][IFSV2_OUTCOME_CONTACT_MANAGEABLE],
        behavior_probs[IFSV2_POLICY_AVOID],
        behavior_probs[IFSV2_POLICY_INSPECT],
        behavior_probs[IFSV2_POLICY_STAY],
        preferred_prob,
        capture,
        witness_precision,
        0.0,
        0.0
    )

    return q_final, step
end

function _blend_posteriors(
    q_a::Vector{Vector{Float64}},
    q_b::Vector{Vector{Float64}}
)
    q_self = Vector{Vector{Float64}}(undef, 3)
    for f in 1:3
        q_self[f] = normalize_prob(0.5 .* q_a[f] .+ 0.5 .* q_b[f])
    end
    return q_self
end

function _self_policy_probs(
    q_self::Vector{Vector{Float64}},
    params::IFSPolarizationV2Params,
    part_a::IFSPolarizationV2PartStep,
    part_b::IFSPolarizationV2PartStep,
    E_t::Float64
)
    mean_capture = 0.5 * (part_a.capture + part_b.capture)
    base_policy = compute_ifs_v2_policy_probs(q_self, params.base; probe=true, capture=mean_capture)

    balance = 1.0 - abs(part_a.preferred_prob - part_b.preferred_prob)
    flexible_bonus = clamp(E_t, 0.0, 1.0) * (0.6 + 0.4 * balance)
    bias = (
        params.self_policy_bias[1],
        params.self_policy_bias[2],
        params.self_policy_bias[3] + flexible_bonus
    )

    return _apply_policy_bias(base_policy, bias)
end

function _effective_part_precision(
    params::IFSPolarizationV2Params,
    spec::IFSPolarizationV2PartSpec,
    step::IFSPolarizationV2PartStep,
    E_t::Float64,
    prev_weight::Float64,
    fatigue::Float64
)
    pi_part_eff, _ = compute_ifs_v2_precisions(params.base, E_t)
    drive =
        spec.precision_scale *
        pi_part_eff *
        step.capture^params.capture_power *
        step.preferred_prob^params.preference_power

    inertia = 1.0 + params.inertia_gain * prev_weight
    fatigue_factor = clamp(1.0 - params.fatigue_impact * (1.0 - E_t) * fatigue, 0.05, 1.0)
    return max(drive * inertia * fatigue_factor, eps(Float64))
end

function _self_precision(
    params::IFSPolarizationV2Params,
    step_a::IFSPolarizationV2PartStep,
    step_b::IFSPolarizationV2PartStep,
    E_t::Float64
)
    balance = 1.0 - abs(step_a.preferred_prob - step_b.preferred_prob)
    balance = clamp(balance, 0.0, 1.0)
    decapture = clamp(1.0 - 0.5 * (step_a.capture + step_b.capture), 0.0, 1.0)
    witness_term =
        0.5 * (
            step_a.witness_precision / max(params.base.lambda_witness_max, eps(Float64)) +
            step_b.witness_precision / max(params.base.lambda_witness_max, eps(Float64))
        )

    return params.self_precision_scale *
        E_t^params.self_precision_power *
        (0.12 + params.self_balance_gain * balance + 0.32 * decapture + params.self_witness_gain * witness_term)
end

function _update_fatigue(
    fatigue::Float64,
    part_weight::Float64,
    params::IFSPolarizationV2Params
)
    next = (1.0 - params.fatigue_decay) * fatigue + params.fatigue_growth * part_weight
    return clamp(next, 0.0, 2.0)
end

action_to_behavior(action::Int) = action == IFSV2_POLICY_AVOID ? :avoid : action == IFSV2_POLICY_INSPECT ? :approach : :flexible

# ============================================================================
# METRICS
# ============================================================================

function _behavior_entropy(step::IFSPolarizationV2StepResult)
    probs = [step.p_avoid, step.p_approach, step.p_flexible]
    h = 0.0
    for p in probs
        p <= 1e-10 && continue
        h -= p * log2(p)
    end
    return h
end

function compute_ifs_polarization_v2_metrics(
    steps::Vector{IFSPolarizationV2StepResult},
    params::IFSPolarizationV2Params
)
    behaviors = [step.behavior for step in steps]
    switches = 0
    for i in 2:length(behaviors)
        behaviors[i] != behaviors[i - 1] && (switches += 1)
    end

    part_a_pref = [step.part_a.p_avoid for step in steps]
    part_b_pref = [step.part_b.p_approach for step in steps]
    part_a_centered = part_a_pref .- mean(part_a_pref)
    part_b_centered = part_b_pref .- mean(part_b_pref)
    denom = sqrt(sum(part_a_centered .^ 2) * sum(part_b_centered .^ 2))
    anticorr = denom <= 1e-10 ? 0.0 : -sum(part_a_centered .* part_b_centered) / denom

    flexible_rate = mean([step.behavior == :flexible ? 1.0 : 0.0 for step in steps])
    mean_self_weight = mean(step.weight_self for step in steps)
    mean_balance = mean(1.0 - abs(step.weight_part_a - step.weight_part_b) for step in steps)

    first_flexible = nothing
    for (i, step) in enumerate(steps)
        if step.behavior == :flexible
            first_flexible = i
            break
        end
    end

    dual_cascade = let
        last_step = steps[end]
        last_step.part_a.p_self_revised >= params.base.revision_threshold &&
        last_step.part_b.p_self_revised >= params.base.revision_threshold &&
        last_step.part_a.p_threat_safe >= params.base.revision_threshold &&
        last_step.part_b.p_threat_safe >= params.base.revision_threshold &&
        last_step.part_a.p_outcome_manageable >= params.base.revision_threshold &&
        last_step.part_b.p_outcome_manageable >= params.base.revision_threshold
    end

    IFSPolarizationV2Metrics(
        length(steps) <= 1 ? 0.0 : switches / (length(steps) - 1),
        mean_self_weight,
        mean_balance,
        flexible_rate,
        anticorr,
        dual_cascade,
        first_flexible
    )
end

# ============================================================================
# MAIN SIMULATION
# ============================================================================

function run_ifs_polarization_v2_condition(
    model::IFSPolarizationV2Model,
    config::IFSPolarizationV2ConditionConfig;
    seed::Int=42,
    deterministic::Bool=false,
    verbose::Bool=false
)
    Random.seed!(seed)
    params = model.params
    env = IFSV2Environment(config.context)

    prior_a = [copy(q) for q in model.part_a.model.D]
    prior_b = [copy(q) for q in model.part_b.model.D]
    fatigue_a = 0.0
    fatigue_b = 0.0
    prev_weight_a = 0.56
    prev_weight_b = 0.44
    action = params.initial_action

    steps = IFSPolarizationV2StepResult[]

    for (t, E_t) in enumerate(config.E_schedule)
        shared_A = build_ifs_v2_A(model.shared_model, env, action)
        obs = sample_ifs_v2_observation(shared_A, env)

        q_a, step_a0 = _infer_part_step(model.part_a, params, env, prior_a, obs, action, E_t)
        q_b, step_b0 = _infer_part_step(model.part_b, params, env, prior_b, obs, action, E_t)

        eff_a = _effective_part_precision(params, model.part_a.spec, step_a0, E_t, prev_weight_a, fatigue_a)
        eff_b = _effective_part_precision(params, model.part_b.spec, step_b0, E_t, prev_weight_b, fatigue_b)
        eff_self = _self_precision(params, step_a0, step_b0, E_t)
        weights = normalize_prob([eff_a, eff_b, eff_self])

        q_self = _blend_posteriors(q_a, q_b)
        self_policy = _self_policy_probs(q_self, params, step_a0, step_b0, E_t)
        behavior_probs = normalize_prob(
            weights[1] .* [step_a0.p_avoid, step_a0.p_approach, step_a0.p_flexible] .+
            weights[2] .* [step_b0.p_avoid, step_b0.p_approach, step_b0.p_flexible] .+
            weights[3] .* self_policy
        )

        behavior_action = deterministic ? argmax(behavior_probs) : sample_categorical(behavior_probs)
        behavior = action_to_behavior(behavior_action)

        step_a = IFSPolarizationV2PartStep(
            step_a0.p_self_revised,
            step_a0.p_threat_safe,
            step_a0.p_outcome_manageable,
            step_a0.p_avoid,
            step_a0.p_approach,
            step_a0.p_flexible,
            step_a0.preferred_prob,
            step_a0.capture,
            step_a0.witness_precision,
            eff_a,
            fatigue_a
        )
        step_b = IFSPolarizationV2PartStep(
            step_b0.p_self_revised,
            step_b0.p_threat_safe,
            step_b0.p_outcome_manageable,
            step_b0.p_avoid,
            step_b0.p_approach,
            step_b0.p_flexible,
            step_b0.preferred_prob,
            step_b0.capture,
            step_b0.witness_precision,
            eff_b,
            fatigue_b
        )

        push!(steps, IFSPolarizationV2StepResult(
            t,
            E_t,
            behavior_action,
            behavior,
            obs,
            step_a,
            step_b,
            weights[1],
            weights[2],
            weights[3],
            behavior_probs[1],
            behavior_probs[2],
            behavior_probs[3]
        ))

        verbose && println(
            "t=$t E=$(round(E_t, digits=3)) obs=$(collect(obs)) behavior=$behavior ",
            "w=$(round.(weights, digits=3)) ",
            "A[self=$(round(step_a.p_self_revised, digits=3)) cap=$(round(step_a.capture, digits=3)) pref=$(round(step_a.preferred_prob, digits=3))] ",
            "B[self=$(round(step_b.p_self_revised, digits=3)) cap=$(round(step_b.capture, digits=3)) pref=$(round(step_b.preferred_prob, digits=3))]"
        )

        prior_a = propagate_ifs_v2_beliefs(model.part_a.model, q_a, behavior_action)
        prior_b = propagate_ifs_v2_beliefs(model.part_b.model, q_b, behavior_action)
        fatigue_a = _update_fatigue(fatigue_a, weights[1], params)
        fatigue_b = _update_fatigue(fatigue_b, weights[2], params)
        prev_weight_a = weights[1]
        prev_weight_b = weights[2]
        action = behavior_action
    end

    metrics = compute_ifs_polarization_v2_metrics(steps, params)
    return IFSPolarizationV2Run(config.name, model.architecture, steps, metrics, params)
end

# ============================================================================
# AGGREGATION
# ============================================================================

function _mean_std_series(mat::Matrix{Float64})
    vec(mean(mat; dims=2)), vec(std(mat; dims=2))
end

function _metric_values(runs::Vector{IFSPolarizationV2Run}, getter::Function)
    values = Float64[]
    for run in runs
        value = getter(run.metrics)
        isnothing(value) && continue
        push!(values, Float64(value))
    end
    isempty(values) && return NaN, NaN
    return mean(values), std(values)
end

function summarize_ifs_polarization_v2_runs(runs::Vector{IFSPolarizationV2Run})
    @assert !isempty(runs)
    T = length(runs[1].steps)
    N = length(runs)

    E_mat = zeros(Float64, T, N)
    part_a_self = zeros(Float64, T, N)
    part_b_self = zeros(Float64, T, N)
    part_a_threat = zeros(Float64, T, N)
    part_b_threat = zeros(Float64, T, N)
    part_a_outcome = zeros(Float64, T, N)
    part_b_outcome = zeros(Float64, T, N)
    w_a = zeros(Float64, T, N)
    w_b = zeros(Float64, T, N)
    w_self = zeros(Float64, T, N)
    behavior = zeros(Float64, 3, T, N)

    for (j, run) in enumerate(runs)
        for (t, step) in enumerate(run.steps)
            E_mat[t, j] = step.E_t
            part_a_self[t, j] = step.part_a.p_self_revised
            part_b_self[t, j] = step.part_b.p_self_revised
            part_a_threat[t, j] = step.part_a.p_threat_safe
            part_b_threat[t, j] = step.part_b.p_threat_safe
            part_a_outcome[t, j] = step.part_a.p_outcome_manageable
            part_b_outcome[t, j] = step.part_b.p_outcome_manageable
            w_a[t, j] = step.weight_part_a
            w_b[t, j] = step.weight_part_b
            w_self[t, j] = step.weight_self
            behavior[1, t, j] = step.p_avoid
            behavior[2, t, j] = step.p_approach
            behavior[3, t, j] = step.p_flexible
        end
    end

    metric_means = Dict{Symbol,Float64}()
    metric_stds = Dict{Symbol,Float64}()
    for (label, getter) in [
        (:switching_rate, m -> m.switching_rate),
        (:mean_self_weight, m -> m.mean_self_weight),
        (:mean_balance, m -> m.mean_balance),
        (:flexible_rate, m -> m.flexible_rate),
        (:mean_antiphase, m -> m.mean_antiphase),
        (:first_flexible, m -> m.first_flexible),
    ]
        metric_means[label], metric_stds[label] = _metric_values(runs, getter)
    end
    dual_flags = [run.metrics.dual_cascade ? 1.0 : 0.0 for run in runs]
    metric_means[:dual_cascade_rate] = mean(dual_flags)
    metric_stds[:dual_cascade_rate] = std(dual_flags)

    mean_behavior = dropdims(mean(behavior; dims=3), dims=3)
    std_behavior = dropdims(std(behavior; dims=3), dims=3)

    mean_E, _ = _mean_std_series(E_mat)
    mean_part_a_self, std_part_a_self = _mean_std_series(part_a_self)
    mean_part_b_self, std_part_b_self = _mean_std_series(part_b_self)
    mean_part_a_threat, std_part_a_threat = _mean_std_series(part_a_threat)
    mean_part_b_threat, std_part_b_threat = _mean_std_series(part_b_threat)
    mean_part_a_outcome, std_part_a_outcome = _mean_std_series(part_a_outcome)
    mean_part_b_outcome, std_part_b_outcome = _mean_std_series(part_b_outcome)
    mean_weight_part_a, std_weight_part_a = _mean_std_series(w_a)
    mean_weight_part_b, std_weight_part_b = _mean_std_series(w_b)
    mean_weight_self, std_weight_self = _mean_std_series(w_self)

    return IFSPolarizationV2Summary(
        runs[1].condition,
        runs[1].architecture,
        runs,
        mean_E,
        mean_part_a_self, std_part_a_self,
        mean_part_b_self, std_part_b_self,
        mean_part_a_threat, std_part_a_threat,
        mean_part_b_threat, std_part_b_threat,
        mean_part_a_outcome, std_part_a_outcome,
        mean_part_b_outcome, std_part_b_outcome,
        mean_weight_part_a, std_weight_part_a,
        mean_weight_part_b, std_weight_part_b,
        mean_weight_self, std_weight_self,
        mean_behavior, std_behavior,
        metric_means, metric_stds
    )
end

function run_ifs_polarization_v2_replications(;
    params::IFSPolarizationV2Params=IFSPolarizationV2Params(),
    config::IFSPolarizationV2ConditionConfig=high_ifs_polarization_v2_config(params),
    n_replications::Int=60,
    seed::Int=42,
    verbose::Bool=false,
    deterministic::Bool=false
)
    model = build_ifs_polarization_v2_model(params=params)
    runs = Vector{IFSPolarizationV2Run}(undef, n_replications)
    for i in 1:n_replications
        runs[i] = run_ifs_polarization_v2_condition(
            model,
            config;
            seed=seed + i,
            verbose=verbose && i == 1,
            deterministic=deterministic
        )
    end
    return summarize_ifs_polarization_v2_runs(runs)
end

function run_ifs_polarization_v2_suite(;
    params::IFSPolarizationV2Params=IFSPolarizationV2Params(),
    configs::Vector{IFSPolarizationV2ConditionConfig}=all_ifs_polarization_v2_configs(params),
    n_replications::Int=60,
    seed::Int=42
)
    summaries = Vector{IFSPolarizationV2Summary}(undef, length(configs))
    for (i, config) in enumerate(configs)
        summaries[i] = run_ifs_polarization_v2_replications(
            params=params,
            config=config,
            n_replications=n_replications,
            seed=seed + 100 * i
        )
    end
    return summaries
end

function run_ifs_polarization_v2_sensitivity(;
    params::IFSPolarizationV2Params=IFSPolarizationV2Params(),
    n_replications::Int=50,
    seed::Int=42
)
    rows = NamedTuple[]
    top_level_params = [
        :self_precision_scale,
        :self_precision_power,
        :fatigue_growth,
        :fatigue_impact,
        :capture_power,
        :inertia_gain,
    ]
    base_level_params = [
        :beta_se,
        :gamma_se,
        :lambda_witness_max,
        :pi_part,
    ]

    for name in top_level_params
        base_value = getfield(params, name)
        for multiplier in (0.8, 1.2)
            varied = override_ifs_polarization_v2_params(params; NamedTuple{(name,)}((base_value * multiplier,))...)
            low = run_ifs_polarization_v2_replications(
                params=varied,
                config=low_ifs_polarization_v2_config(varied),
                n_replications=n_replications,
                seed=seed + Int(mod(hash((name, multiplier, :low)), 10^8))
            )
            med = run_ifs_polarization_v2_replications(
                params=varied,
                config=medium_ifs_polarization_v2_config(varied),
                n_replications=n_replications,
                seed=seed + Int(mod(hash((name, multiplier, :med)), 10^8))
            )
            high = run_ifs_polarization_v2_replications(
                params=varied,
                config=high_ifs_polarization_v2_config(varied),
                n_replications=n_replications,
                seed=seed + Int(mod(hash((name, multiplier, :high)), 10^8))
            )
            push!(rows, (
                parameter=name,
                level=:polarization,
                multiplier=multiplier,
                low_switching=low.metric_means[:switching_rate],
                medium_approach=med.mean_behavior[2, end],
                medium_flexible=med.mean_behavior[3, end],
                high_self_weight=high.mean_weight_self[end],
                high_dual_cascade=high.metric_means[:dual_cascade_rate],
            ))
        end
    end

    for name in base_level_params
        base_value = getfield(params.base, name)
        for multiplier in (0.8, 1.2)
            varied_base = override_ifs_v2_params(params.base; NamedTuple{(name,)}((base_value * multiplier,))...)
            varied = override_ifs_polarization_v2_params(params; base=varied_base)
            low = run_ifs_polarization_v2_replications(
                params=varied,
                config=low_ifs_polarization_v2_config(varied),
                n_replications=n_replications,
                seed=seed + Int(mod(hash((name, multiplier, :base_low)), 10^8))
            )
            med = run_ifs_polarization_v2_replications(
                params=varied,
                config=medium_ifs_polarization_v2_config(varied),
                n_replications=n_replications,
                seed=seed + Int(mod(hash((name, multiplier, :base_med)), 10^8))
            )
            high = run_ifs_polarization_v2_replications(
                params=varied,
                config=high_ifs_polarization_v2_config(varied),
                n_replications=n_replications,
                seed=seed + Int(mod(hash((name, multiplier, :base_high)), 10^8))
            )
            push!(rows, (
                parameter=name,
                level=:base,
                multiplier=multiplier,
                low_switching=low.metric_means[:switching_rate],
                medium_approach=med.mean_behavior[2, end],
                medium_flexible=med.mean_behavior[3, end],
                high_self_weight=high.mean_weight_self[end],
                high_dual_cascade=high.metric_means[:dual_cascade_rate],
            ))
        end
    end

    return rows
end
