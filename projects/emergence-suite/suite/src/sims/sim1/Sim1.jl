module Sim1

using Random
using Statistics
using LinearAlgebra: dot

using ..Config: ExperimentConfig, config_snapshot
using ..Criteria: write_criteria_results
using ..DiscreteCore: DirichletBanks
using ..EFE: Policy, PolicyScore
using ..IO: ensure_dir, write_json, write_rows_csv
using ..Reproducibility: build_reproducibility_metadata

export run_sim1

const EPS = 1e-12
const SAFE = 1
const AVERSIVE = 2
const POLICY_NAMES = ["approach", "flee", "appease", "attenuate"]
const APPROACH = 1
const FLEE = 2
const APPEASE = 3
const ATTENUATE = 4

Base.@kwdef struct Sim1Params
    crp_concentration::Float64 = 0.34
    crp_threshold_base::Float64 = 0.085
    crp_threshold_control_relief::Float64 = 0.0
    formation_trials::Int = 72
    # Consolidation epoch (T4.6 step C follow-up): after the acute epoch the world's
    # catastrophe channel goes silent at the same omega. Ordinary hazards are
    # assimilable, so spawn pressure never exceeds capacity and formation stops on
    # its own — no agent-side spawn gate. Existing causes, including late spawns,
    # keep operating under the same loop and accrue capture mass before the probe
    # (§4's self-sealing loop needs time to run; probing mid-formation probes a
    # wound, not a part).
    consolidation_trials::Int = 128
    disconfirming_trials::Int = 96
    post_formation_trials::Int = 18
    slow_path_trials::Int = 600
    slow_path_omega::Float64 = 1.00
    slow_path_kappa::Float64 = 0.0
    bundle_seed_count::Int = 8
    spawn_pressure_threshold::Float64 = 1.2
    efe_flatness_threshold::Float64 = 0.55
    spawn_pressure_decay::Float64 = 0.72
    learning_rate_base::Float64 = 0.16
    learning_rate_arousal_gain::Float64 = 60.0
    cue_learning_weight::Float64 = 0.55
    revision_learning_rate::Float64 = 2.0
    behavior_frozen_max_change::Float64 = 0.15
    behavior_revisable_min_change::Float64 = 0.25
    threat_prediction_threshold::Float64 = 0.40
    cell_classification_rate::Float64 = 0.50
    connected_region_min_cells::Int = 2
    arm_contrast_margin_cells::Int = 2
    relief_trials_approach::Int = 1
    relief_trials_flee::Int = 3
    relief_trials_appease::Int = 2
    relief_trials_attenuate::Int = 0
    policy_softmax_temperature::Float64 = 1.0
    arousal_pe_scale::Float64 = 5.2
    reflexivity_arousal_slope::Float64 = 0.88
    evidence_precision::Float64 = 1.0
    attenuation_precision_scale::Float64 = 0.34
    safe_preference::Float64 = 1.35
    aversive_preference::Float64 = -2.35
    ambiguity_weight::Float64 = 0.10
    epistemic_weight::Float64 = 0.28
    attenuation_info_scale::Float64 = 0.18
    attenuation_cost::Float64 = 0.80
    overt_action_cost::Float64 = 0.03
    attenuation_extreme_omega::Float64 = 2.65
    attenuation_flat_kappa::Float64 = 0.16
    acute_region_omega_min::Float64 = 1.18
    # Probe-time capture (T4.6 step C): D1 tilt slopes shared with Sims 2/3/6a;
    # the two scale constants are pilot-swept and frozen.
    tilt_beta::Float64 = 1.0
    tilt_gamma::Float64 = 1.2
    probe_depth_scale::Float64 = 3.0
    capture_precision_scale::Float64 = 2.0
    context_precision::Float64 = 1.0
    # Acute-overwhelm channel (severity of rare catastrophic hazards)
    catastrophe_omega_floor::Float64 = 1.2
    catastrophe_rate::Float64 = 0.015
    catastrophe_max::Float64 = 0.08
    catastrophe_severity::Float64 = 6.0
    assimilation_capacity::Float64 = 1.0
    severity_prior_ordinary::Float64 = 1.0
    severity_prior_catastrophic::Float64 = 0.05
    # A1.5 redefinition (post two-arm falsification of the region-count contrast):
    # bands for the arm-by-kappa interaction of freezing. Pilot provenance in
    # magic-numbers.md; frozen before confirmatory.
    release_omega_min::Float64 = 2.0
    release_low_kappa_min::Float64 = 0.2
    release_low_kappa_max::Float64 = 0.6
    release_high_kappa_min::Float64 = 1.0
    # S1.4 amendment: attenuation is confined to kappa below this efficacy level.
    attenuation_efficacy_kappa::Float64 = 0.5
end

mutable struct Cause
    id::Int
    cue_counts::Vector{Float64}
    affect_counts::Vector{Float64}
    outcome_counts::Matrix{Float64}
    policy_counts::Vector{Float64}
    formation::Dict{String, Any}
    # Count-weighted write-reflexivity accumulators (Tier A aggregate: how much of
    # this cause's mass was written while reflexivity was collapsed). Drives the
    # probe-time capture weight per D1/§7; orchestrator addition, T4.6 step C.
    reflexive_mass::Float64
    total_mass::Float64
    # Severity beliefs: Dirichlet counts over {ordinary, catastrophic} given aversive.
    severity_counts::Vector{Float64}
end

is_catastrophic(obs) = obs.evidence_outcome == AVERSIVE && obs.evidence_severity > 1.5

function severity_predictive(cause::Cause, obs)
    obs.evidence_outcome == AVERSIVE || return 1.0
    return posterior_mean(cause.severity_counts, is_catastrophic(obs) ? 2 : 1)
end

mutable struct AgentState
    causes::Vector{Cause}
    next_cause_id::Int
    spawn_pressure::Float64
    spawn_count::Int
end

struct TrialObservation
    cue::Int
    potential_outcome::Int
    evidence_outcome::Int
    action_outcome::Int
    exposure_suppressed::Bool
    prior_policy_idx::Int
    prior_action_success::Bool
    action_success::Bool
    relief_trials_added::Int
    relief_remaining_after::Int
    evidence_aversive_probability::Float64
    action_aversive_probability::Float64
    evidence_severity::Float64
    precision::Float64
end

mutable struct WorldState
    relief_remaining::Int
    relief_policy_idx::Int
    previous_policy_idx::Int
    previous_action_success::Bool
end

function sim1_params(raw::Dict{String, Any})
    return Sim1Params(
        crp_concentration = Float64(get(raw, "crp_concentration", 0.34)),
        crp_threshold_base = Float64(get(raw, "crp_threshold_base", 0.085)),
        crp_threshold_control_relief = Float64(get(raw, "crp_threshold_control_relief", 0.0)),
        formation_trials = Int(get(raw, "formation_trials", get(raw, "post_formation_trials", 72) * 4)),
        consolidation_trials = Int(get(raw, "consolidation_trials", 128)),
        disconfirming_trials = Int(get(raw, "disconfirming_trials", 96)),
        post_formation_trials = Int(get(raw, "post_formation_trials", 18)),
        slow_path_trials = Int(get(raw, "slow_path_trials", 600)),
        slow_path_omega = Float64(get(raw, "slow_path_omega", 1.00)),
        slow_path_kappa = Float64(get(raw, "slow_path_kappa", 0.0)),
        bundle_seed_count = Int(get(raw, "bundle_seed_count", 8)),
        spawn_pressure_threshold = Float64(get(raw, "spawn_pressure_threshold", 1.2)),
        efe_flatness_threshold = Float64(get(raw, "efe_flatness_threshold", 0.55)),
        spawn_pressure_decay = Float64(get(raw, "spawn_pressure_decay", 0.72)),
        learning_rate_base = Float64(get(raw, "learning_rate_base", 0.16)),
        learning_rate_arousal_gain = Float64(get(raw, "learning_rate_arousal_gain", 60.0)),
        cue_learning_weight = Float64(get(raw, "cue_learning_weight", 0.55)),
        revision_learning_rate = Float64(get(raw, "revision_learning_rate", 2.0)),
        behavior_frozen_max_change = Float64(get(raw, "behavior_frozen_max_change", 0.15)),
        behavior_revisable_min_change = Float64(get(raw, "behavior_revisable_min_change", 0.25)),
        threat_prediction_threshold = Float64(get(raw, "threat_prediction_threshold", 0.40)),
        cell_classification_rate = Float64(get(raw, "cell_classification_rate", 0.50)),
        connected_region_min_cells = Int(get(raw, "connected_region_min_cells", 2)),
        arm_contrast_margin_cells = Int(get(raw, "arm_contrast_margin_cells", 2)),
        relief_trials_approach = Int(get(raw, "relief_trials_approach", 1)),
        relief_trials_flee = Int(get(raw, "relief_trials_flee", 3)),
        relief_trials_appease = Int(get(raw, "relief_trials_appease", 2)),
        relief_trials_attenuate = Int(get(raw, "relief_trials_attenuate", 0)),
        policy_softmax_temperature = Float64(get(raw, "policy_softmax_temperature", 1.0)),
        arousal_pe_scale = Float64(get(raw, "arousal_pe_scale", 5.2)),
        reflexivity_arousal_slope = Float64(get(raw, "reflexivity_arousal_slope", 0.88)),
        evidence_precision = Float64(get(raw, "evidence_precision", 1.0)),
        attenuation_precision_scale = Float64(get(raw, "attenuation_precision_scale", 0.34)),
        safe_preference = Float64(get(raw, "safe_preference", 1.35)),
        aversive_preference = Float64(get(raw, "aversive_preference", -2.35)),
        ambiguity_weight = Float64(get(raw, "ambiguity_weight", 0.10)),
        epistemic_weight = Float64(get(raw, "epistemic_weight", 0.28)),
        attenuation_info_scale = Float64(get(raw, "attenuation_info_scale", 0.18)),
        attenuation_cost = Float64(get(raw, "attenuation_cost", 0.80)),
        overt_action_cost = Float64(get(raw, "overt_action_cost", 0.03)),
        attenuation_extreme_omega = Float64(get(raw, "attenuation_extreme_omega", 2.65)),
        attenuation_flat_kappa = Float64(get(raw, "attenuation_flat_kappa", 0.16)),
        acute_region_omega_min = Float64(get(raw, "acute_region_omega_min", 1.18)),
        tilt_beta = Float64(get(raw, "tilt_beta", 1.0)),
        tilt_gamma = Float64(get(raw, "tilt_gamma", 1.2)),
        probe_depth_scale = Float64(get(raw, "probe_depth_scale", 3.0)),
        capture_precision_scale = Float64(get(raw, "capture_precision_scale", 2.0)),
        context_precision = Float64(get(raw, "context_precision", 1.0)),
        catastrophe_omega_floor = Float64(get(raw, "catastrophe_omega_floor", 1.2)),
        catastrophe_rate = Float64(get(raw, "catastrophe_rate", 0.015)),
        catastrophe_max = Float64(get(raw, "catastrophe_max", 0.08)),
        assimilation_capacity = Float64(get(raw, "assimilation_capacity", 1.0)),
        catastrophe_severity = Float64(get(raw, "catastrophe_severity", 6.0)),
        severity_prior_ordinary = Float64(get(raw, "severity_prior_ordinary", 1.0)),
        severity_prior_catastrophic = Float64(get(raw, "severity_prior_catastrophic", 0.05)),
        release_omega_min = Float64(get(raw, "release_omega_min", 2.0)),
        release_low_kappa_min = Float64(get(raw, "release_low_kappa_min", 0.2)),
        release_low_kappa_max = Float64(get(raw, "release_low_kappa_max", 0.6)),
        release_high_kappa_min = Float64(get(raw, "release_high_kappa_min", 1.0)),
        attenuation_efficacy_kappa = Float64(get(raw, "attenuation_efficacy_kappa", 0.5))
    )
end

function linspace_from_grid(grid::Dict{String, Any}, key::String)
    raw = Dict{String, Any}(string(k) => v for (k, v) in grid[key])
    lo = Float64(raw["min"])
    hi = Float64(raw["max"])
    count = Int(raw["count"])
    count >= 2 || error("$key grid count must be >= 2")
    return collect(range(lo, hi; length = count))
end

sample_categorical(rng::AbstractRNG, p::Vector{Float64}) = begin
    u = rand(rng)
    c = 0.0
    for i in eachindex(p)
        c += p[i]
        u <= c && return i
    end
    length(p)
end

normalize(v::AbstractVector{Float64}) = v ./ max(sum(v), EPS)
entropy(p::AbstractVector{Float64}) = -sum(x -> x * log(x + EPS), p)
control_value(kappa::Float64) = kappa / (kappa + 0.45 + EPS)

function init_agent()
    outcome = hcat(
        [8.0, 4.0],
        [10.0, 3.0],
        [9.0, 4.0],
        [6.0, 6.0]
    )
    base = Cause(
        1,
        [14.0, 10.0],
        [15.0, 7.0],
        Matrix{Float64}(outcome),
        [3.0, 5.0, 4.0, 1.0],
        Dict{String, Any}("route" => "initial_cause", "spawned" => false),
        0.0,
        0.0,
        [1.0, 0.05]
    )
    return AgentState([base], 2, 0.0, 0)
end

function copy_cause(cause::Cause)
    return Cause(
        cause.id,
        copy(cause.cue_counts),
        copy(cause.affect_counts),
        copy(cause.outcome_counts),
        copy(cause.policy_counts),
        copy(cause.formation),
        cause.reflexive_mass,
        cause.total_mass,
        copy(cause.severity_counts)
    )
end

function cause_banks(cause::Cause)
    A_cue = reshape(copy(cause.cue_counts), 2, 1)
    A_affect = reshape(copy(cause.affect_counts), 2, 1)
    B_policy = reshape(copy(cause.outcome_counts), 2, 1, length(POLICY_NAMES))
    return DirichletBanks(Array{Float64}[A_cue, A_affect], Array{Float64, 3}[B_policy])
end

function posterior_mean(counts::AbstractVector{Float64}, idx::Int)
    return counts[idx] / max(sum(counts), EPS)
end

# T4.6 step C (orchestrator): the expected outcome of CONTACT conditions on the
# cause's threat belief — the bundle's own structure (what-this-is predicts
# what-happens-if-I-approach). Without this link, an avoidant agent's approach
# column is a near-empty bank that trivially revises the moment it is finally
# tested, making frozenness impossible by construction. Non-approach policies
# keep their learned action-consequence banks.
function outcome_distribution(cause::Cause, policy_idx::Int)
    if policy_idx == APPROACH
        mixed = vec(cause.outcome_counts[:, APPROACH]) .+ 0.5 .* cause.affect_counts
        return normalize(mixed)
    end
    return normalize(vec(cause.outcome_counts[:, policy_idx]))
end

function cue_predictive(cause::Cause, cue::Int)
    return posterior_mean(cause.cue_counts, cue)
end

function affect_aversive_mean(cause::Cause)
    return posterior_mean(cause.affect_counts, AVERSIVE)
end

function structural_precision(cause::Cause)
    return sum(cause.affect_counts) + 0.35 * sum(cause.cue_counts)
end

function base_aversive_probability(omega::Float64)
    return clamp(0.08 + 0.31 * omega, 0.06, 0.97)
end

function action_aversive_probabilities(evidence_outcome::Int, kappa::Float64)
    base = evidence_outcome == AVERSIVE ? 0.90 : 0.08
    control = control_value(kappa)
    return [
        clamp(base - 0.10 * control, 0.03, 0.98),
        clamp(base - 1.40 * control, 0.02, 0.98),
        clamp(base - 0.90 * control, 0.03, 0.98),
        base
    ]
end

function relief_trials(policy_idx::Int, params::Sim1Params)
    return (
        params.relief_trials_approach,
        params.relief_trials_flee,
        params.relief_trials_appease,
        params.relief_trials_attenuate
    )[policy_idx]
end

function sample_evidence(rng::AbstractRNG, omega::Float64, params::Sim1Params; catastrophes::Bool = true)
    p_av = base_aversive_probability(omega)
    outcome = rand(rng) < p_av ? AVERSIVE : SAFE
    # Acute-overwhelm channel (T4.6 step C, orchestrator): rare catastrophic-severity
    # hazards above an omega floor. Binary outcomes bound surprise, which killed both
    # spawning and collapsed writes; severity restores genuinely unassimilable events
    # (§4: "input no explanation on hand can absorb"). Stream is precomputed per
    # (seed, omega), so the yoked arm replays severity exactly. During the
    # consolidation epoch the channel is silent (catastrophes = false); the rand
    # draw is kept unconditional so outcome streams match across epoch structures.
    p_cata = catastrophes ?
        clamp(params.catastrophe_rate * (omega - params.catastrophe_omega_floor), 0.0, params.catastrophe_max) : 0.0
    severity = (outcome == AVERSIVE && rand(rng) < p_cata) ? params.catastrophe_severity : 1.0
    return (
        outcome = outcome,
        aversive_probability = p_av,
        severity = severity,
        precision = params.evidence_precision
    )
end

function evidence_stream(seed::Int, omega::Float64, trials::Int, params::Sim1Params)
    rng = MersenneTwister(seed)
    return [sample_evidence(rng, omega, params) for _ in 1:trials]
end

"""
Two-epoch potential-hazard stream: an acute epoch (catastrophe channel live) followed
by a consolidation epoch at the same omega with the channel silent. Shared per
(seed, omega) across arms and kappa, so yoking replays both epochs exactly.
"""
function formation_stream(seed::Int, omega::Float64, params::Sim1Params)
    rng = MersenneTwister(seed)
    acute = [sample_evidence(rng, omega, params) for _ in 1:params.formation_trials]
    chronic = [sample_evidence(rng, omega, params; catastrophes = false) for _ in 1:params.consolidation_trials]
    return vcat(acute, chronic)
end

function observe_environment(rng::AbstractRNG, potential, kappa::Float64, policy_idx::Int,
                             arm::Symbol, world::WorldState, params::Sim1Params)
    arm in (:closed_loop, :yoked) || error("Unknown Sim 1 arm: $arm")
    prior_policy_idx = world.previous_policy_idx
    prior_action_success = world.previous_action_success
    exposure_suppressed = arm == :closed_loop && potential.outcome == AVERSIVE && world.relief_remaining > 0
    evidence_outcome = exposure_suppressed ? SAFE : potential.outcome
    if arm == :closed_loop && world.relief_remaining > 0
        world.relief_remaining -= 1
        world.relief_remaining == 0 && (world.relief_policy_idx = 0)
    end
    probs = action_aversive_probabilities(evidence_outcome, kappa)
    action_p_av = probs[policy_idx]
    action_outcome = rand(rng) < action_p_av ? AVERSIVE : SAFE
    action_success = evidence_outcome == AVERSIVE && action_outcome == SAFE && relief_trials(policy_idx, params) > 0
    relief_added = arm == :closed_loop && action_success ? relief_trials(policy_idx, params) : 0
    if relief_added > 0
        world.relief_remaining = max(world.relief_remaining, relief_added)
        world.relief_policy_idx = policy_idx
    end
    world.previous_policy_idx = policy_idx
    world.previous_action_success = action_success
    return TrialObservation(
        AVERSIVE,
        potential.outcome,
        evidence_outcome,
        action_outcome,
        exposure_suppressed,
        prior_policy_idx,
        prior_action_success,
        action_success,
        relief_added,
        world.relief_remaining,
        potential.aversive_probability,
        action_p_av,
        potential.severity,
        potential.precision
    )
end

function score_policies(cause::Cause, params::Sim1Params; preference_scale::Float64 = 1.0)
    scores = PolicyScore{Float64}[]
    prefs = [params.safe_preference, params.aversive_preference .* preference_scale]
    for policy_idx in eachindex(POLICY_NAMES)
        qo = outcome_distribution(cause, policy_idx)
        is_attenuate = policy_idx == ATTENUATE
        precision_scale = is_attenuate ? params.attenuation_precision_scale : 1.0
        utility = precision_scale * dot(qo, prefs)
        amb = entropy(qo)
        information_gain = params.epistemic_weight * amb / sqrt(sum(cause.outcome_counts[:, policy_idx]))
        is_attenuate && (information_gain *= params.attenuation_info_scale)
        cost = is_attenuate ? params.attenuation_cost : params.overt_action_cost
        total = utility - params.ambiguity_weight * amb + information_gain - cost
        push!(scores, PolicyScore(Policy([policy_idx]), utility, amb, information_gain, total))
    end
    return scores
end

function select_policy(cause::Cause, params::Sim1Params; preference_scale::Float64 = 1.0)
    scores = score_policies(cause, params; preference_scale)
    totals = [score.total for score in scores]
    idx = argmax(totals)
    return idx, scores
end

function policy_probabilities(cause::Cause, params::Sim1Params; preference_scale::Float64 = 1.0)
    totals = [score.total for score in score_policies(cause, params; preference_scale)]
    scaled = totals ./ max(params.policy_softmax_temperature, EPS)
    weights = exp.(scaled .- maximum(scaled))
    return normalize(weights)
end

function best_predictive(agent::AgentState, obs::TrialObservation)
    best_idx = 1
    best_raw = -Inf
    best_weighted = -Inf
    for (idx, cause) in enumerate(agent.causes)
        affect_probability = posterior_mean(cause.affect_counts, obs.evidence_outcome)
        raw = cue_predictive(cause, obs.cue) * affect_probability * severity_predictive(cause, obs)
        weighted = raw ^ max(obs.precision, EPS)
        if weighted > best_weighted
            best_idx = idx
            best_raw = raw
            best_weighted = weighted
        end
    end
    return best_idx, best_raw, best_weighted
end

function arousal_from_prediction(raw_predictive::Float64, effective_precision::Float64, params::Sim1Params)
    surprise = -log(max(raw_predictive, EPS))
    pe = effective_precision * surprise
    return clamp(pe / params.arousal_pe_scale, 0.0, 1.0), pe
end

function write_reflexivity(arousal::Float64, params::Sim1Params)
    return clamp(1.0 - params.reflexivity_arousal_slope * arousal, 0.0, 1.0)
end

function crp_threshold(agent::AgentState, params::Sim1Params; concentration_factor::Float64 = 1.0)
    alpha = params.crp_concentration * concentration_factor
    complexity = alpha / (alpha + length(agent.causes))
    return params.crp_threshold_base * (0.65 + complexity)
end

function spawn_cause!(agent::AgentState, arousal::Float64, reflexivity::Float64, trial::Int, seed::Int)
    cause = Cause(
        agent.next_cause_id,
        [1.0, 2.0],
        [1.0, 1.0],
        fill(1.0, 2, length(POLICY_NAMES)),
        ones(Float64, length(POLICY_NAMES)),
        Dict{String, Any}(
            "route" => "acute_spawn",
            "spawned" => true,
            "spawn_trial" => trial,
            "seed" => seed,
            "arousal_at_write" => arousal,
            "reflexivity_at_write" => reflexivity
        ),
        0.0,
        0.0,
        [1.0, 0.05]
    )
    push!(agent.causes, cause)
    agent.next_cause_id += 1
    agent.spawn_count += 1
    agent.spawn_pressure = 0.0
    return cause
end

# T4.6 step C (orchestrator): spawn pressure is accumulated precision-weighted
# surprise IN EXCESS of assimilation capacity (§4: overwhelm = error beyond what
# existing causes can absorb). The previous form (decayed arousal, bounded at 1.0)
# could never reach the 2.45 gate — an unreachable-criterion bug, not a result.
function update_spawn_pressure!(agent::AgentState, posterior_predictive::Float64, threshold::Float64, pe::Float64, params::Sim1Params)
    excess = max(0.0, pe - params.assimilation_capacity)
    if posterior_predictive < threshold || excess > 0.0
        agent.spawn_pressure = params.spawn_pressure_decay * agent.spawn_pressure + excess
    else
        agent.spawn_pressure *= params.spawn_pressure_decay
    end
    return agent.spawn_pressure
end

function update_cause!(cause::Cause, obs::TrialObservation, policy_idx::Int, arousal::Float64, reflexivity::Float64, params::Sim1Params)
    lr = params.learning_rate_base + params.learning_rate_arousal_gain * arousal
    cause.cue_counts[obs.cue] += params.cue_learning_weight * lr
    cause.affect_counts[obs.evidence_outcome] += lr
    cause.outcome_counts[obs.action_outcome, policy_idx] += lr
    cause.policy_counts[policy_idx] += 1.0
    if obs.evidence_outcome == AVERSIVE
        cause.reflexive_mass += lr * reflexivity
        cause.total_mass += lr
        cause.severity_counts[is_catastrophic(obs) ? 2 : 1] += lr
    end
    return lr
end

# Count-weighted write-reflexivity of the AVERSIVE content specifically: the frozen
# quantity is the aversive expectation, so what matters is the watching-state when
# that content was written (safe-trial mass would otherwise dilute the aggregate).
written_reflexivity(cause::Cause) = cause.total_mass > 0.0 ? cause.reflexive_mass / cause.total_mass : 1.0

"""
Probe-time capture weight (T4.6 step C, orchestrator). The disconfirming probe's
evidence is weighted by the present-context share of the D1 tilt, with the depth
coordinate set by the cause's count-weighted write-reflexivity: a cause whose mass
was written under collapsed reflexivity is transparent at test (§3), so probe
evidence is discounted by capture (§7). One mechanism, imported from D1/Sims 2-6a,
not invented here. beta/gamma are the suite's tilt slopes; the two scale constants
are swept on pilot and frozen (magic-numbers.md).
"""
function probe_evidence_weight(cause::Cause, params::Sim1Params)
    E = written_reflexivity(cause) * params.probe_depth_scale
    pi_eff = (structural_precision(cause) / params.capture_precision_scale) * exp(-params.tilt_beta * E)
    lambda_eff = params.context_precision * exp(params.tilt_gamma * E)
    return lambda_eff / (pi_eff + lambda_eff)
end

function dominant_aversive_cause(agent::AgentState)
    scores = [
        cue_predictive(cause, AVERSIVE) * affect_aversive_mean(cause) * (1.0 + 0.05 * log1p(structural_precision(cause)))
        for cause in agent.causes
    ]
    return agent.causes[argmax(scores)]
end

function measure_revision(cause::Cause, params::Sim1Params)
    probe = copy_cause(cause)
    pre_safe = probe.affect_counts[SAFE]
    pre_aversive = probe.affect_counts[AVERSIVE]
    pre_affect_aversive = affect_aversive_mean(probe)
    pre_predicted_aversive = outcome_distribution(probe, APPROACH)[AVERSIVE]
    pre_approach_probability = policy_probabilities(probe, params)[APPROACH]
    pre_precision = structural_precision(probe)
    capture_weight = probe_evidence_weight(probe, params)
    for _ in 1:params.disconfirming_trials
        w = capture_weight * params.revision_learning_rate
        probe.cue_counts[AVERSIVE] += params.cue_learning_weight * w
        probe.affect_counts[SAFE] += w
        probe.outcome_counts[SAFE, APPROACH] += w
        probe.policy_counts[APPROACH] += capture_weight
    end
    post_affect_aversive = affect_aversive_mean(probe)
    post_predicted_aversive = outcome_distribution(probe, APPROACH)[AVERSIVE]
    post_approach_probability = policy_probabilities(probe, params)[APPROACH]
    # Relative reduction (T4.6 step C): frozen means resisting a full extinction
    # course; absolute-probability change saturates for beliefs starting near 0.4.
    predicted_aversive_reduction = max(pre_predicted_aversive - post_predicted_aversive, 0.0) / max(pre_predicted_aversive, EPS)
    approach_probability_increase = max(post_approach_probability - pre_approach_probability, 0.0)
    behavior_change = max(predicted_aversive_reduction, approach_probability_increase)
    return (
        behavior_change = behavior_change,
        capture_weight = capture_weight,
        predicted_aversive_reduction = predicted_aversive_reduction,
        approach_probability_increase = approach_probability_increase,
        pre_predicted_aversive = pre_predicted_aversive,
        post_predicted_aversive = post_predicted_aversive,
        pre_approach_probability = pre_approach_probability,
        post_approach_probability = post_approach_probability,
        pre_affect_aversive = pre_affect_aversive,
        post_affect_aversive = post_affect_aversive,
        pre_safe_count = pre_safe,
        pre_aversive_count = pre_aversive,
        pre_structural_precision = pre_precision,
        post_structural_precision = structural_precision(probe)
    )
end

function run_trial!(rng::AbstractRNG, agent::AgentState, world::WorldState, potential, kappa::Float64,
                    params::Sim1Params, trial::Int, seed::Int; arm::Symbol = :closed_loop,
                    concentration_factor::Float64 = 1.0, allow_spawn::Bool = true,
                    preference_scale::Float64 = 1.0)
    current = dominant_aversive_cause(agent)
    policy_idx, scores = select_policy(current, params; preference_scale)
    obs = observe_environment(rng, potential, kappa, policy_idx, arm, world, params)
    best_idx, raw_pp, weighted_pp = best_predictive(agent, obs)
    arousal, pe = arousal_from_prediction(raw_pp, obs.precision, params)
    reflexivity = write_reflexivity(arousal, params)
    threshold = crp_threshold(agent, params; concentration_factor)
    pressure = update_spawn_pressure!(agent, weighted_pp, threshold, pe, params)
    spawned = false
    cause = agent.causes[best_idx]
    # §4's fork, both conditions explicit: overwhelm (pressure = accumulated surprise
    # excess) AND flat overt-policy landscape (no action is expected to help). With
    # efficacy learned, high-kappa cells develop spread in their overt scores and do
    # not spawn even on catastrophic surprise — S1.2 emerges from the fork itself.
    overt_totals = [scores[i].total for i in (APPROACH, FLEE, APPEASE)]
    overt_spread = maximum(overt_totals) - minimum(overt_totals)
    if allow_spawn && pressure >= params.spawn_pressure_threshold && overt_spread < params.efe_flatness_threshold
        cause = spawn_cause!(agent, arousal, reflexivity, trial, seed)
        spawned = true
    end
    lr = update_cause!(cause, obs, policy_idx, arousal, reflexivity, params)
    return (
        trial = trial,
        policy_idx = policy_idx,
        policy = POLICY_NAMES[policy_idx],
        potential_outcome = obs.potential_outcome == AVERSIVE ? "aversive" : "safe",
        evidence_outcome = obs.evidence_outcome == AVERSIVE ? "aversive" : "safe",
        action_outcome = obs.action_outcome == AVERSIVE ? "aversive" : "safe",
        exposure_suppressed = obs.exposure_suppressed,
        prior_policy_idx = obs.prior_policy_idx,
        prior_policy = obs.prior_policy_idx == 0 ? "none" : POLICY_NAMES[obs.prior_policy_idx],
        prior_action_success = obs.prior_action_success,
        action_success = obs.action_success,
        relief_trials_added = obs.relief_trials_added,
        relief_remaining_after = obs.relief_remaining_after,
        evidence_aversive_probability = obs.evidence_aversive_probability,
        action_aversive_probability = obs.action_aversive_probability,
        evidence_severity = obs.evidence_severity,
        evidence_precision = obs.precision,
        posterior_predictive = weighted_pp,
        raw_predictive = raw_pp,
        crp_threshold = threshold,
        spawn_pressure = agent.spawn_pressure,
        spawned = spawned,
        cause_id = cause.id,
        arousal = arousal,
        reflexivity = reflexivity,
        precision_weighted_pe = pe,
        learning_rate = lr,
        policy_totals = [score.total for score in scores]
    )
end

function postformation_sampling_rate(trial_logs, target_id::Int, params::Sim1Params)
    target_logs = [row for row in trial_logs if row.cause_id == target_id]
    isempty(target_logs) && return 0.0
    window = last(target_logs, min(params.post_formation_trials, length(target_logs)))
    return mean(row.policy_idx == APPROACH ? 1.0 : 0.0 for row in window)
end

function run_seed_cell(seed::Int, omega::Float64, kappa::Float64, params::Sim1Params; concentration_factor::Float64 = 1.0,
                       preference_scale::Float64 = 1.0, arm::Symbol = :closed_loop)
    action_rng = MersenneTwister(seed + 1_000_003)
    potential_stream = formation_stream(seed, omega, params)
    total_trials = params.formation_trials + params.consolidation_trials
    agent = init_agent()
    world = WorldState(0, 0, 0, false)
    trial_logs = NamedTuple[]
    for trial in 1:total_trials
        row = run_trial!(action_rng, agent, world, potential_stream[trial], kappa, params, trial, seed;
                         arm, concentration_factor, preference_scale)
        push!(trial_logs, merge(row, (phase = trial <= params.formation_trials ? "acute" : "consolidation",)))
    end
    target = dominant_aversive_cause(agent)
    revision = measure_revision(target, params)
    sampling = postformation_sampling_rate(trial_logs, target.id, params)
    spawned_logs = [row for row in trial_logs if row.spawned]
    write_log = isempty(spawned_logs) ? trial_logs[argmax([row.arousal for row in trial_logs])] : first(spawned_logs)
    target_is_aversive = revision.pre_predicted_aversive >= params.threat_prediction_threshold
    is_frozen = target_is_aversive && revision.behavior_change <= params.behavior_frozen_max_change
    is_revisable = target_is_aversive && revision.behavior_change >= params.behavior_revisable_min_change
    target_spawned = get(target.formation, "spawned", false) == true
    potential_aversive_count = count(row.potential_outcome == "aversive" for row in trial_logs)
    aversive_evidence_count = count(row.evidence_outcome == "aversive" for row in trial_logs)
    suppressed_aversive_count = count(row.exposure_suppressed for row in trial_logs)
    potential_aversive_count == aversive_evidence_count + suppressed_aversive_count ||
        error("Sim 1 exposure accounting invariant failed for seed=$seed omega=$omega kappa=$kappa arm=$arm")
    exposure_after = Dict(policy => (potential = 0, exposed = 0) for policy in ("none", POLICY_NAMES...))
    for row in trial_logs
        row.potential_outcome == "aversive" || continue
        key = row.prior_policy
        counts = exposure_after[key]
        exposure_after[key] = (potential = counts.potential + 1, exposed = counts.exposed + (row.evidence_outcome == "aversive" ? 1 : 0))
    end
    exposure_rate_after(policy) = exposure_after[policy].potential == 0 ? 0.0 : exposure_after[policy].exposed / exposure_after[policy].potential
    return (
        arm = String(arm),
        seed = seed,
        omega = omega,
        kappa = kappa,
        target_cause_id = target.id,
        target_route = String(get(target.formation, "route", target_spawned ? "acute_spawn" : "initial_cause")),
        spawn_count = agent.spawn_count,
        spawned = agent.spawn_count > 0,
        target_spawned = target_spawned,
        dominant_policy = POLICY_NAMES[argmax(target.policy_counts)],
        attenuation_rate = mean(row.policy_idx == ATTENUATE ? 1.0 : 0.0 for row in trial_logs),
        policy_approach_count = count(row.policy_idx == APPROACH for row in trial_logs),
        policy_flee_count = count(row.policy_idx == FLEE for row in trial_logs),
        policy_appease_count = count(row.policy_idx == APPEASE for row in trial_logs),
        policy_attenuate_count = count(row.policy_idx == ATTENUATE for row in trial_logs),
        successful_relief_action_count = count(row.action_success && row.relief_trials_added > 0 for row in trial_logs),
        potential_aversive_count = potential_aversive_count,
        suppressed_aversive_count = suppressed_aversive_count,
        exposure_rate = potential_aversive_count == 0 ? 0.0 : aversive_evidence_count / potential_aversive_count,
        potential_after_approach_count = exposure_after["approach"].potential,
        exposed_after_approach_count = exposure_after["approach"].exposed,
        exposure_rate_after_approach = exposure_rate_after("approach"),
        potential_after_flee_count = exposure_after["flee"].potential,
        exposed_after_flee_count = exposure_after["flee"].exposed,
        exposure_rate_after_flee = exposure_rate_after("flee"),
        potential_after_appease_count = exposure_after["appease"].potential,
        exposed_after_appease_count = exposure_after["appease"].exposed,
        exposure_rate_after_appease = exposure_rate_after("appease"),
        potential_after_attenuate_count = exposure_after["attenuate"].potential,
        exposed_after_attenuate_count = exposure_after["attenuate"].exposed,
        exposure_rate_after_attenuate = exposure_rate_after("attenuate"),
        approach_sampling_rate = sampling,
        reflexivity_at_write = write_log.reflexivity,
        arousal_at_write = write_log.arousal,
        max_precision_weighted_pe = maximum(row.precision_weighted_pe for row in trial_logs),
        mean_precision_weighted_pe = mean(row.precision_weighted_pe for row in trial_logs),
        revision_behavior_change = revision.behavior_change,
        probe_capture_weight = revision.capture_weight,
        predicted_aversive_reduction = revision.predicted_aversive_reduction,
        approach_probability_increase = revision.approach_probability_increase,
        pre_probe_predicted_aversive = revision.pre_predicted_aversive,
        post_probe_predicted_aversive = revision.post_predicted_aversive,
        pre_probe_approach_probability = revision.pre_approach_probability,
        post_probe_approach_probability = revision.post_approach_probability,
        pre_probe_affect_aversive = revision.pre_affect_aversive,
        post_probe_affect_aversive = revision.post_affect_aversive,
        structural_precision = revision.pre_structural_precision,
        target_aversive = target_is_aversive,
        frozen = is_frozen,
        revisable = is_revisable,
        aversive_evidence_count = aversive_evidence_count,
        aversive_evidence_severity_sum = sum(row.evidence_outcome == "aversive" ? row.evidence_severity : 0.0 for row in trial_logs),
        mean_evidence_precision = mean(row.evidence_precision for row in trial_logs),
        aversive_action_outcome_count = count(row.action_outcome == "aversive" for row in trial_logs),
        posterior_predictive_min = minimum(row.posterior_predictive for row in trial_logs),
        prediction_failure_count = count(row.posterior_predictive < row.crp_threshold for row in trial_logs),
        max_spawn_pressure = maximum(row.spawn_pressure for row in trial_logs),
        crp_threshold_last = last(trial_logs).crp_threshold,
        cause_bank_cue_safe = target.cue_counts[SAFE],
        cause_bank_cue_threat = target.cue_counts[AVERSIVE],
        cause_bank_affect_safe = target.affect_counts[SAFE],
        cause_bank_affect_threat = target.affect_counts[AVERSIVE],
        cause_bank_policy_approach = target.policy_counts[APPROACH],
        cause_bank_policy_flee = target.policy_counts[FLEE],
        cause_bank_policy_appease = target.policy_counts[APPEASE],
        cause_bank_policy_attenuate = target.policy_counts[ATTENUATE],
        outcome_approach_safe = target.outcome_counts[SAFE, APPROACH],
        outcome_approach_threat = target.outcome_counts[AVERSIVE, APPROACH],
        outcome_flee_safe = target.outcome_counts[SAFE, FLEE],
        outcome_flee_threat = target.outcome_counts[AVERSIVE, FLEE],
        outcome_appease_safe = target.outcome_counts[SAFE, APPEASE],
        outcome_appease_threat = target.outcome_counts[AVERSIVE, APPEASE],
        outcome_attenuate_safe = target.outcome_counts[SAFE, ATTENUATE],
        outcome_attenuate_threat = target.outcome_counts[AVERSIVE, ATTENUATE]
    )
end

function mean_bool(rows, field::Symbol)
    isempty(rows) && return 0.0
    return mean(getproperty(row, field) ? 1.0 : 0.0 for row in rows)
end

function mean_field(rows, field::Symbol; default::Float64 = 0.0)
    isempty(rows) && return default
    return mean(Float64(getproperty(row, field)) for row in rows)
end

function summarize_cell(rows)
    return (
        arm = first(rows).arm,
        omega = first(rows).omega,
        kappa = first(rows).kappa,
        n_seeds = length(rows),
        spawn_rate = mean_bool(rows, :spawned),
        target_spawn_rate = mean_bool(rows, :target_spawned),
        frozen_rate = mean_bool(rows, :frozen),
        revisable_rate = mean_bool(rows, :revisable),
        attenuation_rate = mean_field(rows, :attenuation_rate),
        mean_reflexivity_at_write = mean_field(rows, :reflexivity_at_write),
        mean_arousal_at_write = mean_field(rows, :arousal_at_write),
        mean_postformation_sampling_rate = mean_field(rows, :approach_sampling_rate),
        mean_revision_behavior_change = mean_field(rows, :revision_behavior_change),
        mean_predicted_aversive_reduction = mean_field(rows, :predicted_aversive_reduction),
        mean_approach_probability_increase = mean_field(rows, :approach_probability_increase),
        mean_pre_probe_predicted_aversive = mean_field(rows, :pre_probe_predicted_aversive),
        mean_post_probe_predicted_aversive = mean_field(rows, :post_probe_predicted_aversive),
        mean_pre_probe_approach_probability = mean_field(rows, :pre_probe_approach_probability),
        mean_post_probe_approach_probability = mean_field(rows, :post_probe_approach_probability),
        mean_aversive_evidence_count = mean_field(rows, :aversive_evidence_count),
        mean_potential_aversive_count = mean_field(rows, :potential_aversive_count),
        mean_suppressed_aversive_count = mean_field(rows, :suppressed_aversive_count),
        mean_exposure_rate = mean_field(rows, :exposure_rate),
        mean_aversive_action_outcome_count = mean_field(rows, :aversive_action_outcome_count),
        mean_successful_relief_action_count = mean_field(rows, :successful_relief_action_count),
        mean_policy_approach_count = mean_field(rows, :policy_approach_count),
        mean_policy_flee_count = mean_field(rows, :policy_flee_count),
        mean_policy_appease_count = mean_field(rows, :policy_appease_count),
        mean_policy_attenuate_count = mean_field(rows, :policy_attenuate_count),
        potential_after_approach_count = sum(row.potential_after_approach_count for row in rows),
        exposed_after_approach_count = sum(row.exposed_after_approach_count for row in rows),
        exposure_rate_after_approach = sum(row.potential_after_approach_count for row in rows) == 0 ? 0.0 : sum(row.exposed_after_approach_count for row in rows) / sum(row.potential_after_approach_count for row in rows),
        potential_after_flee_count = sum(row.potential_after_flee_count for row in rows),
        exposed_after_flee_count = sum(row.exposed_after_flee_count for row in rows),
        exposure_rate_after_flee = sum(row.potential_after_flee_count for row in rows) == 0 ? 0.0 : sum(row.exposed_after_flee_count for row in rows) / sum(row.potential_after_flee_count for row in rows),
        potential_after_appease_count = sum(row.potential_after_appease_count for row in rows),
        exposed_after_appease_count = sum(row.exposed_after_appease_count for row in rows),
        exposure_rate_after_appease = sum(row.potential_after_appease_count for row in rows) == 0 ? 0.0 : sum(row.exposed_after_appease_count for row in rows) / sum(row.potential_after_appease_count for row in rows),
        potential_after_attenuate_count = sum(row.potential_after_attenuate_count for row in rows),
        exposed_after_attenuate_count = sum(row.exposed_after_attenuate_count for row in rows),
        exposure_rate_after_attenuate = sum(row.potential_after_attenuate_count for row in rows) == 0 ? 0.0 : sum(row.exposed_after_attenuate_count for row in rows) / sum(row.potential_after_attenuate_count for row in rows),
        mean_prediction_failure_count = mean_field(rows, :prediction_failure_count),
        max_spawn_pressure = maximum(row.max_spawn_pressure for row in rows),
        mean_structural_precision = mean_field(rows, :structural_precision),
        max_precision_weighted_pe = maximum(row.max_precision_weighted_pe for row in rows)
    )
end

function component_sizes(mask::AbstractMatrix{Bool})
    seen = falses(size(mask))
    sizes = Int[]
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
    for start in CartesianIndices(mask)
        (!mask[start] || seen[start]) && continue
        queue = [start]
        seen[start] = true
        count = 0
        while !isempty(queue)
            idx = popfirst!(queue)
            count += 1
            for (di, dj) in dirs
                ni, nj = idx[1] + di, idx[2] + dj
                if 1 <= ni <= size(mask, 1) && 1 <= nj <= size(mask, 2) && mask[ni, nj] && !seen[ni, nj]
                    seen[ni, nj] = true
                    push!(queue, CartesianIndex(ni, nj))
                end
            end
        end
        push!(sizes, count)
    end
    return sizes
end

function boundary_by_kappa(cell_rows, omegas, kappas; field::Symbol = :frozen_rate, threshold::Float64 = 0.5)
    boundary = Float64[]
    for kappa in kappas
        rows = sort([row for row in cell_rows if row.kappa == kappa]; by = row -> row.omega)
        hits = [row.omega for row in rows if getproperty(row, field) >= threshold]
        push!(boundary, isempty(hits) ? NaN : minimum(hits))
    end
    return boundary
end

function boundary_smoothness(cell_rows, omegas, kappas; threshold::Float64 = 0.5)
    boundary = boundary_by_kappa(cell_rows, omegas, kappas; threshold)
    finite = [x for x in boundary if isfinite(x)]
    length(finite) <= 1 && return 0.0
    jumps = abs.(diff(finite)) ./ max(maximum(omegas) - minimum(omegas), EPS)
    return isempty(jumps) ? 0.0 : maximum(jumps)
end

function classify_grid(cell_rows, omegas, kappas, params::Sim1Params)
    frozen = falses(length(omegas), length(kappas))
    revisable = falses(length(omegas), length(kappas))
    mixed = falses(length(omegas), length(kappas))
    for row in cell_rows
        i = findfirst(==(row.omega), omegas)
        j = findfirst(==(row.kappa), kappas)
        frozen_majority = row.frozen_rate >= params.cell_classification_rate
        revisable_majority = row.revisable_rate >= params.cell_classification_rate
        mixed[i, j] = frozen_majority && revisable_majority
        frozen[i, j] = frozen_majority && !mixed[i, j]
        revisable[i, j] = revisable_majority && !mixed[i, j]
    end
    frozen_components = component_sizes(frozen)
    revisable_components = component_sizes(revisable)
    return (
        frozen = frozen,
        revisable = revisable,
        mixed = mixed,
        frozen_largest_component = isempty(frozen_components) ? 0 : maximum(frozen_components),
        revisable_largest_component = isempty(revisable_components) ? 0 : maximum(revisable_components),
        frozen_cell_count = count(frozen),
        frozen_region_cell_count = sum(size for size in frozen_components if size >= params.connected_region_min_cells),
        revisable_cell_count = count(revisable),
        revisable_region_cell_count = sum(size for size in revisable_components if size >= params.connected_region_min_cells),
        mixed_cell_count = count(mixed)
    )
end

function run_sweep(seeds, omegas, kappas, params::Sim1Params; concentration_factor::Float64 = 1.0,
                   preference_scale::Float64 = 1.0, arm::Symbol = :closed_loop)
    seed_rows = NamedTuple[]
    cell_rows = NamedTuple[]
    for omega in omegas, kappa in kappas
        rows = [run_seed_cell(seed, omega, kappa, params; concentration_factor, preference_scale, arm) for seed in seeds]
        append!(seed_rows, rows)
        push!(cell_rows, summarize_cell(rows))
    end
    return seed_rows, cell_rows
end

function slow_condition_sequence(params::Sim1Params)
    return [
        params.slow_path_omega * (0.94 + 0.12 * ((i - 1) % 11) / 10)
        for i in 1:params.slow_path_trials
    ]
end

function run_slow_path(seed::Int, params::Sim1Params; shuffle::Bool = false)
    evidence_rng = MersenneTwister(seed)
    action_rng = MersenneTwister(seed + 1_000_003)
    shuffle_rng = MersenneTwister(seed + 2_000_003)
    omegas = slow_condition_sequence(params)
    shuffle && Random.shuffle!(shuffle_rng, omegas)
    agent = init_agent()
    world = WorldState(0, 0, 0, false)
    rows = NamedTuple[]
    crossed = false
    cross_trial = 0
    cross_precision = NaN
    cross_trial_pe = NaN
    max_pe = 0.0
    spawn_seen = false
    write_reflexivity_value = 1.0
    write_arousal_value = 0.0
    for (trial, omega_t) in enumerate(omegas)
        potential = sample_evidence(evidence_rng, omega_t, params)
        log = run_trial!(action_rng, agent, world, potential, params.slow_path_kappa, params, trial, seed;
                         arm = :closed_loop, allow_spawn = true)
        spawn_seen |= log.spawned
        if log.spawned || log.arousal > write_arousal_value
            write_reflexivity_value = log.reflexivity
            write_arousal_value = log.arousal
        end
        target = dominant_aversive_cause(agent)
        revision = measure_revision(target, params)
        is_frozen = revision.pre_predicted_aversive >= params.threat_prediction_threshold &&
            revision.behavior_change <= params.behavior_frozen_max_change
        if !crossed && is_frozen
            crossed = true
            cross_trial = trial
            cross_precision = revision.pre_structural_precision
            cross_trial_pe = log.precision_weighted_pe
        end
        max_pe = max(max_pe, log.precision_weighted_pe)
        push!(rows, (
            seed = seed,
            trial = trial,
            per_trial_omega = omega_t,
            kappa = params.slow_path_kappa,
            target_cause_id = target.id,
            cause_id = log.cause_id,
            structural_precision = revision.pre_structural_precision,
            revision_behavior_change = revision.behavior_change,
            predicted_aversive_reduction = revision.predicted_aversive_reduction,
            approach_probability_increase = revision.approach_probability_increase,
            pre_probe_predicted_aversive = revision.pre_predicted_aversive,
            pre_probe_approach_probability = revision.pre_approach_probability,
            precision_weighted_pe = log.precision_weighted_pe,
            potential_outcome = log.potential_outcome,
            evidence_outcome = log.evidence_outcome,
            exposure_suppressed = log.exposure_suppressed,
            policy_idx = log.policy_idx,
            policy = log.policy,
            action_success = log.action_success,
            spawned = spawn_seen,
            crossed = crossed
        ))
    end
    target = dominant_aversive_cause(agent)
    revision = measure_revision(target, params)
    return (
        seed = seed,
        omega_center = params.slow_path_omega,
        kappa = params.slow_path_kappa,
        trials = params.slow_path_trials,
        crossed = crossed,
        cross_trial = crossed ? cross_trial : nothing,
        cross_structural_precision = crossed ? cross_precision : nothing,
        cross_trial_pe = crossed ? cross_trial_pe : nothing,
        max_per_trial_pe = max_pe,
        spawned = spawn_seen,
        potential_aversive_count = count(row.potential_outcome == "aversive" for row in rows),
        aversive_evidence_count = count(row.evidence_outcome == "aversive" for row in rows),
        suppressed_aversive_count = count(row.exposure_suppressed for row in rows),
        successful_relief_action_count = count(row.action_success for row in rows),
        arousal_at_write = write_arousal_value,
        reflexivity_at_write = write_reflexivity_value,
        postformation_sampling_rate = postformation_sampling_rate(rows, target.id, params),
        final_revision_behavior_change = revision.behavior_change,
        final_predicted_aversive_reduction = revision.predicted_aversive_reduction,
        final_approach_probability_increase = revision.approach_probability_increase,
        final_pre_probe_predicted_aversive = revision.pre_predicted_aversive,
        final_post_probe_predicted_aversive = revision.post_predicted_aversive,
        final_pre_probe_approach_probability = revision.pre_approach_probability,
        final_post_probe_approach_probability = revision.post_approach_probability,
        final_structural_precision = revision.pre_structural_precision,
        target_cause = copy_cause(target),
        path = rows
    )
end

"""
A1.5 redefined (post two-arm falsification of the frozen-region cell-count
contrast, which is retained falsified in the criteria for the record): the
loop-closure signature is the arm-by-kappa INTERACTION of freezing, plus a
capture-not-mass check.

1. kappa release: in the closed loop, control releases freezing — frozen cells
   in the acute band (omega >= release_omega_min) concentrate at low kappa and
   vanish at high kappa. Under exact replay, kappa cannot alter exposure, so the
   frozen count is flat across kappa. The interaction is
   (closed_low - closed_high) - (yoked_low - yoked_high), in frozen-cell counts.
2. capture-not-mass: over the same acute low-kappa band, the closed loop
   receives strictly LESS delivered aversive evidence than yoked (suppression),
   yet revises LESS. A count-mass account predicts the opposite ordering. The
   preregistered mediator is the probe capture weight (D1 tilt over written
   reflexivity): suppression removes later expected transparent aversive writes,
   so early collapsed writes stay dominant and capture stays low.
"""
function kappa_release_metrics(closed_seed_rows, yoked_seed_rows, params::Sim1Params)
    in_band(row, lo, hi) = row.omega >= params.release_omega_min && lo <= row.kappa <= hi
    frozen_cells(rows, lo, hi) = begin
        cells = Dict{Tuple{Float64, Float64}, Vector{Bool}}()
        for row in rows
            in_band(row, lo, hi) || continue
            push!(get!(cells, (row.omega, row.kappa), Bool[]), row.frozen)
        end
        count(mean(flags) >= params.cell_classification_rate for flags in values(cells))
    end
    low = (params.release_low_kappa_min, params.release_low_kappa_max)
    high = (params.release_high_kappa_min, Inf)
    closed_low = frozen_cells(closed_seed_rows, low...)
    closed_high = frozen_cells(closed_seed_rows, high...)
    yoked_low = frozen_cells(yoked_seed_rows, low...)
    yoked_high = frozen_cells(yoked_seed_rows, high...)
    band_rows(rows) = [row for row in rows if in_band(row, low...)]
    closed_band = band_rows(closed_seed_rows)
    yoked_band = band_rows(yoked_seed_rows)
    closed_change = mean(row.revision_behavior_change for row in closed_band)
    yoked_change = mean(row.revision_behavior_change for row in yoked_band)
    closed_exposure = mean(row.aversive_evidence_count for row in closed_band)
    yoked_exposure = mean(row.aversive_evidence_count for row in yoked_band)
    closed_capture = mean(row.probe_capture_weight for row in closed_band)
    yoked_capture = mean(row.probe_capture_weight for row in yoked_band)
    return (
        closed_low_kappa_frozen_cells = closed_low,
        closed_high_kappa_frozen_cells = closed_high,
        yoked_low_kappa_frozen_cells = yoked_low,
        yoked_high_kappa_frozen_cells = yoked_high,
        interaction_cells = (closed_low - closed_high) - (yoked_low - yoked_high),
        closed_band_mean_revision = closed_change,
        yoked_band_mean_revision = yoked_change,
        yoked_minus_closed_revision_gap = yoked_change - closed_change,
        closed_band_mean_aversive_exposure = closed_exposure,
        yoked_band_mean_aversive_exposure = yoked_exposure,
        closed_to_yoked_exposure_ratio = yoked_exposure > 0 ? closed_exposure / yoked_exposure : 1.0,
        closed_band_mean_capture_weight = closed_capture,
        yoked_band_mean_capture_weight = yoked_capture,
        yoked_minus_closed_capture_gap = yoked_capture - closed_capture
    )
end

function high_high_frozen_rate(cell_rows, omegas, kappas)
    omega_cut = quantile(omegas, 0.80)
    kappa_cut = quantile(kappas, 0.80)
    rows = [row for row in cell_rows if row.omega >= omega_cut && row.kappa >= kappa_cut]
    return isempty(rows) ? 0.0 : mean(row.frozen_rate for row in rows)
end

"""
S1.2 amended (pilot 2026-07-10): cell-level version, consistent with the region
classification standard used everywhere else in this sim. The seed-level rate in
the corner is nonzero (~0.20) and is retained in the summary as a discovered
trait: seeds whose catastrophes land before efficacy is learned freeze even at
high kappa, because successful avoidance then keeps the early collapsed writes
dominant — control prevents chronic freezing, not freezing outright.
"""
function high_high_frozen_cell_fraction(cell_rows, omegas, kappas, params::Sim1Params)
    omega_cut = quantile(omegas, 0.80)
    kappa_cut = quantile(kappas, 0.80)
    rows = [row for row in cell_rows if row.omega >= omega_cut && row.kappa >= kappa_cut]
    return isempty(rows) ? 0.0 : mean(row.frozen_rate >= params.cell_classification_rate ? 1.0 : 0.0 for row in rows)
end

function kappa_yoking_metrics(seed_rows, omegas, kappas)
    potential_count_ranges = Float64[]
    count_ranges = Float64[]
    suppressed_counts = Float64[]
    severity_ranges = Float64[]
    precision_ranges = Float64[]
    complete_groups = true
    for omega in omegas, seed in unique(row.seed for row in seed_rows)
        rows = [row for row in seed_rows if row.omega == omega && row.seed == seed]
        complete_groups &= length(rows) == length(kappas)
        isempty(rows) && continue
        push!(potential_count_ranges, maximum(row.potential_aversive_count for row in rows) - minimum(row.potential_aversive_count for row in rows))
        push!(count_ranges, maximum(row.aversive_evidence_count for row in rows) - minimum(row.aversive_evidence_count for row in rows))
        append!(suppressed_counts, Float64[row.suppressed_aversive_count for row in rows])
        push!(severity_ranges, maximum(row.aversive_evidence_severity_sum for row in rows) - minimum(row.aversive_evidence_severity_sum for row in rows))
        push!(precision_ranges, maximum(row.mean_evidence_precision for row in rows) - minimum(row.mean_evidence_precision for row in rows))
    end
    max_potential_count_range = isempty(potential_count_ranges) ? Inf : maximum(potential_count_ranges)
    max_count_range = isempty(count_ranges) ? Inf : maximum(count_ranges)
    max_suppressed_count = isempty(suppressed_counts) ? Inf : maximum(suppressed_counts)
    max_severity_range = isempty(severity_ranges) ? Inf : maximum(severity_ranges)
    max_precision_range = isempty(precision_ranges) ? Inf : maximum(precision_ranges)
    return (
        exact_yoking = complete_groups && max_potential_count_range == 0.0 && max_count_range == 0.0 &&
            max_suppressed_count == 0.0 && max_severity_range <= EPS && max_precision_range <= EPS ? 1.0 : 0.0,
        complete_groups = complete_groups,
        max_potential_aversive_count_range = max_potential_count_range,
        max_aversive_count_range = max_count_range,
        max_suppressed_aversive_count = max_suppressed_count,
        max_aversive_severity_range = max_severity_range,
        max_observation_precision_range = max_precision_range
    )
end

function action_mediation_rows(closed_cells)
    return [(
        arm = row.arm,
        omega = row.omega,
        kappa = row.kappa,
        n_seeds = row.n_seeds,
        mean_potential_aversive_count = row.mean_potential_aversive_count,
        mean_delivered_aversive_count = row.mean_aversive_evidence_count,
        mean_suppressed_aversive_count = row.mean_suppressed_aversive_count,
        mean_exposure_rate = row.mean_exposure_rate,
        mean_successful_relief_action_count = row.mean_successful_relief_action_count,
        mean_policy_approach_count = row.mean_policy_approach_count,
        mean_policy_flee_count = row.mean_policy_flee_count,
        mean_policy_appease_count = row.mean_policy_appease_count,
        mean_policy_attenuate_count = row.mean_policy_attenuate_count,
        potential_after_approach_count = row.potential_after_approach_count,
        exposed_after_approach_count = row.exposed_after_approach_count,
        exposure_rate_after_approach = row.exposure_rate_after_approach,
        potential_after_flee_count = row.potential_after_flee_count,
        exposed_after_flee_count = row.exposed_after_flee_count,
        exposure_rate_after_flee = row.exposure_rate_after_flee,
        potential_after_appease_count = row.potential_after_appease_count,
        exposed_after_appease_count = row.exposed_after_appease_count,
        exposure_rate_after_appease = row.exposure_rate_after_appease,
        potential_after_attenuate_count = row.potential_after_attenuate_count,
        exposed_after_attenuate_count = row.exposed_after_attenuate_count,
        exposure_rate_after_attenuate = row.exposure_rate_after_attenuate,
        exposure_accounting_error = row.mean_potential_aversive_count - row.mean_aversive_evidence_count - row.mean_suppressed_aversive_count
    ) for row in closed_cells]
end

"""
S1.4 amended (pilot 2026-07-10): the original omega-extreme/kappa-near-zero corner
claim is falsified in this model class — attenuation tracks HELPLESSNESS, not
hazard extremity. Observed: mean attenuation is monotone-decreasing in kappa
(0.195 at kappa=0) and exactly zero for kappa >= 0.5, at every omega. Within the
helpless column it is U-shaped in omega (traps at low omega where evidence is too
sparse to resolve; high rates at extreme omega under relentless hazard) — logged
as a discovered trait, not a criterion. The amended claim: attenuation is
confined to the inefficacy margin.
"""
function attenuation_kappa_localization(cell_rows, params::Sim1Params)
    helpless = [row for row in cell_rows if row.kappa == 0.0]
    efficacious = [row for row in cell_rows if row.kappa >= params.attenuation_efficacy_kappa]
    helpless_rate = isempty(helpless) ? 0.0 : mean(row.attenuation_rate for row in helpless)
    outside_max = isempty(efficacious) ? 0.0 : maximum(row.attenuation_rate for row in efficacious)
    return (
        helpless_column_mean_rate = helpless_rate,
        efficacious_max_rate = outside_max,
        kappa_gradient = helpless_rate - outside_max
    )
end

function attenuation_corner_metric(cell_rows, params::Sim1Params)
    corner = [row for row in cell_rows if row.omega >= params.attenuation_extreme_omega && row.kappa <= params.attenuation_flat_kappa]
    outside = [row for row in cell_rows if !(row.omega >= params.attenuation_extreme_omega && row.kappa <= params.attenuation_flat_kappa)]
    corner_rate = isempty(corner) ? 0.0 : mean(row.attenuation_rate for row in corner)
    outside_rate = isempty(outside) ? 0.0 : maximum(row.attenuation_rate for row in outside)
    return (
        pass = (corner_rate >= 0.80 && outside_rate <= 0.05) ? 1.0 : 0.0,
        corner_rate = corner_rate,
        max_outside_rate = outside_rate
    )
end

function omega_only_frozen_metric(seeds, omegas, params::Sim1Params)
    moderate_kappa = 0.70
    rows = NamedTuple[]
    for omega in omegas
        seed_rows = [run_seed_cell(seed, omega, moderate_kappa, params) for seed in seeds]
        push!(rows, summarize_cell(seed_rows))
    end
    frozen_cells = count(row.frozen_rate >= params.cell_classification_rate for row in rows)
    return frozen_cells > 0 ? 1.0 : 0.0
end

function concentration_boundary_smoothness(seeds, omegas, kappas, params::Sim1Params)
    traces = NamedTuple[]
    for factor in (0.5, 1.0, 1.5)
        _, cells = run_sweep(seeds, omegas, kappas, params; concentration_factor = factor)
        push!(traces, (
            concentration_factor = factor,
            smoothness = boundary_smoothness(cells, omegas, kappas; threshold = params.cell_classification_rate),
            frozen_boundary_min_omega_by_kappa = boundary_by_kappa(cells, omegas, kappas; threshold = params.cell_classification_rate)
        ))
    end
    return maximum(row.smoothness for row in traces), traces
end

function attenuation_preference_sensitivity(seeds, omegas, kappas, params::Sim1Params)
    traces = NamedTuple[]
    for scale in (0.85, 1.0, 1.15)
        _, cells = run_sweep(seeds, omegas, kappas, params; preference_scale = scale)
        metric = attenuation_corner_metric(cells, params)
        push!(traces, (
            aversive_preference_scale = scale,
            attenuate_corner_only = metric.pass,
            corner_rate = metric.corner_rate,
            max_outside_rate = metric.max_outside_rate
        ))
    end
    return traces
end

function write_phase_svg(path::AbstractString, closed_cells, yoked_cells, slow_path_rows, omegas, kappas)
    width, height = 1560, 650
    left, top = 82, 70
    plot_w, plot_h = 620, 500
    panel_gap = 92
    cell_w = plot_w / length(omegas)
    cell_h = plot_h / length(kappas)
    omega_min, omega_max = extrema(omegas)
    kappa_min, kappa_max = extrema(kappas)
    x_for(omega, panel_left) = panel_left + (omega - omega_min) / max(omega_max - omega_min, EPS) * plot_w
    y_for(kappa) = top + plot_h - (kappa - kappa_min) / max(kappa_max - kappa_min, EPS) * plot_h
    open(path, "w") do io
        println(io, "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"$width\" height=\"$height\" viewBox=\"0 0 $width $height\">")
        println(io, "<rect width=\"100%\" height=\"100%\" fill=\"#fbfaf7\"/>")
        println(io, "<text x=\"$left\" y=\"30\" font-family=\"Arial\" font-size=\"20\" fill=\"#202020\">Sim 1 two-arm freezing phase diagram</text>")
        for (panel, rows, title) in ((0, closed_cells, "Arm 1 — closed loop"), (1, yoked_cells, "Arm 2 — exact replay"))
            panel_left = left + panel * (plot_w + panel_gap)
            println(io, "<text x=\"$panel_left\" y=\"57\" font-family=\"Arial\" font-size=\"16\" fill=\"#202020\">$title</text>")
            for row in rows
                i = findfirst(==(row.omega), omegas)
                j = findfirst(==(row.kappa), kappas)
                x = panel_left + (i - 1) * cell_w
                y = top + (length(kappas) - j) * cell_h
                fill = row.frozen_rate >= 0.5 && row.revisable_rate >= 0.5 ? "#705191" : row.frozen_rate >= 0.5 ? "#8f2d2d" : row.revisable_rate >= 0.5 ? "#2f7d59" : row.spawn_rate >= 0.5 ? "#d9a441" : "#e8e3d7"
                opacity = 0.32 + 0.62 * max(row.frozen_rate, row.revisable_rate, row.spawn_rate)
                println(io, "<rect x=\"$x\" y=\"$y\" width=\"$cell_w\" height=\"$cell_h\" fill=\"$fill\" fill-opacity=\"$opacity\" stroke=\"#ffffff\" stroke-width=\"1\"/>")
            end
            println(io, "<rect x=\"$panel_left\" y=\"$top\" width=\"$plot_w\" height=\"$plot_h\" fill=\"none\" stroke=\"#333\" stroke-width=\"1.5\"/>")
            println(io, "<text x=\"$(panel_left + 220)\" y=\"$(top + plot_h + 38)\" font-family=\"Arial\" font-size=\"14\" fill=\"#333333\">overwhelm omega</text>")
        end
        path_points = join(["$(x_for(row.per_trial_omega, left)),$(y_for(row.kappa))" for row in slow_path_rows], " ")
        println(io, "<polyline points=\"$path_points\" fill=\"none\" stroke=\"#1f4e79\" stroke-width=\"4\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>")
        println(io, "<text x=\"22\" y=\"$(top + 280)\" font-family=\"Arial\" font-size=\"14\" fill=\"#333333\" transform=\"rotate(-90 22 $(top + 280))\">control kappa</text>")
        legend_x = left + plot_w + 16
        println(io, "<rect x=\"$legend_x\" y=\"110\" width=\"20\" height=\"20\" fill=\"#8f2d2d\"/><text x=\"$(legend_x + 25)\" y=\"126\" font-family=\"Arial\" font-size=\"12\" fill=\"#333\">frozen</text>")
        println(io, "<rect x=\"$legend_x\" y=\"144\" width=\"20\" height=\"20\" fill=\"#2f7d59\"/><text x=\"$(legend_x + 25)\" y=\"160\" font-family=\"Arial\" font-size=\"12\" fill=\"#333\">revisable</text>")
        println(io, "<rect x=\"$legend_x\" y=\"178\" width=\"20\" height=\"20\" fill=\"#d9a441\"/><text x=\"$(legend_x + 25)\" y=\"194\" font-family=\"Arial\" font-size=\"12\" fill=\"#333\">spawned</text>")
        println(io, "<rect x=\"$legend_x\" y=\"212\" width=\"20\" height=\"20\" fill=\"#705191\"/><text x=\"$(legend_x + 25)\" y=\"228\" font-family=\"Arial\" font-size=\"12\" fill=\"#333\">mixed</text>")
        println(io, "<line x1=\"$legend_x\" y1=\"270\" x2=\"$(legend_x + 38)\" y2=\"270\" stroke=\"#1f4e79\" stroke-width=\"4\"/><text x=\"$(legend_x + 42)\" y=\"274\" font-family=\"Arial\" font-size=\"12\" fill=\"#333\">slow</text>")
        println(io, "</svg>")
    end
    return path
end

function bundle_artifact(row)
    return (
        schema_version = "sim1.bundle.v3",
        seed = row.seed,
        route = row.target_route,
        formation = (
            arm = row.arm,
            omega = row.omega,
            kappa = row.kappa,
            potential_stream_key = "seed=$(row.seed);omega=$(row.omega)",
            potential_aversive_count = row.potential_aversive_count,
            aversive_evidence_count = row.aversive_evidence_count,
            suppressed_aversive_count = row.suppressed_aversive_count,
            exposure_rate = row.exposure_rate,
            aversive_evidence_severity_sum = row.aversive_evidence_severity_sum,
            mean_evidence_precision = row.mean_evidence_precision,
            aversive_action_outcome_count = row.aversive_action_outcome_count,
            realized_policy_counts = (
                approach = row.policy_approach_count,
                flee = row.policy_flee_count,
                appease = row.policy_appease_count,
                attenuate = row.policy_attenuate_count
            ),
            successful_relief_action_count = row.successful_relief_action_count,
            exposure_after_realized_policy = (
                approach = (potential = row.potential_after_approach_count, exposed = row.exposed_after_approach_count, rate = row.exposure_rate_after_approach),
                flee = (potential = row.potential_after_flee_count, exposed = row.exposed_after_flee_count, rate = row.exposure_rate_after_flee),
                appease = (potential = row.potential_after_appease_count, exposed = row.exposed_after_appease_count, rate = row.exposure_rate_after_appease),
                attenuate = (potential = row.potential_after_attenuate_count, exposed = row.exposed_after_attenuate_count, rate = row.exposure_rate_after_attenuate)
            ),
            arousal_at_write = row.arousal_at_write,
            reflexivity_at_write = row.reflexivity_at_write,
            postformation_sampling_rate = row.approach_sampling_rate,
            spawned = row.target_spawned,
            spawn_count = row.spawn_count,
            posterior_predictive_min = row.posterior_predictive_min,
            prediction_failure_count = row.prediction_failure_count,
            max_spawn_pressure = row.max_spawn_pressure,
            crp_threshold_last = row.crp_threshold_last
        ),
        revision_probe = (
            disconfirming_trials_measured = true,
            metric = "posterior_predictive_behavior",
            behavior_change = row.revision_behavior_change,
            predicted_aversive_reduction = row.predicted_aversive_reduction,
            approach_probability_increase = row.approach_probability_increase,
            pre_probe_predicted_aversive = row.pre_probe_predicted_aversive,
            post_probe_predicted_aversive = row.post_probe_predicted_aversive,
            pre_probe_approach_probability = row.pre_probe_approach_probability,
            post_probe_approach_probability = row.post_probe_approach_probability,
            structural_precision = row.structural_precision
        ),
        cause_banks = (
            cue_counts = (safe = row.cause_bank_cue_safe, threat = row.cause_bank_cue_threat),
            affect_counts = (safe = row.cause_bank_affect_safe, threat = row.cause_bank_affect_threat),
            policy_counts = (
                approach = row.cause_bank_policy_approach,
                flee = row.cause_bank_policy_flee,
                appease = row.cause_bank_policy_appease,
                attenuate = row.cause_bank_policy_attenuate
            ),
            outcome_counts = (
                approach = (safe = row.outcome_approach_safe, threat = row.outcome_approach_threat),
                flee = (safe = row.outcome_flee_safe, threat = row.outcome_flee_threat),
                appease = (safe = row.outcome_appease_safe, threat = row.outcome_appease_threat),
                attenuate = (safe = row.outcome_attenuate_safe, threat = row.outcome_attenuate_threat)
            )
        )
    )
end

function slow_bundle_artifact(run)
    cause = run.target_cause
    _ = cause_banks(cause)
    return (
        schema_version = "sim1.bundle.v3",
        seed = run.seed,
        route = "slow_accumulation",
        formation = (
            arm = "closed_loop",
            omega = run.omega_center,
            kappa = run.kappa,
            trials = run.trials,
            spawned = run.spawned,
            cross_trial = run.cross_trial,
            cross_structural_precision = run.cross_structural_precision,
            cross_trial_pe = run.cross_trial_pe,
            max_per_trial_pe = run.max_per_trial_pe,
            potential_aversive_count = run.potential_aversive_count,
            aversive_evidence_count = run.aversive_evidence_count,
            suppressed_aversive_count = run.suppressed_aversive_count,
            successful_relief_action_count = run.successful_relief_action_count,
            arousal_at_write = run.arousal_at_write,
            reflexivity_at_write = run.reflexivity_at_write,
            postformation_sampling_rate = run.postformation_sampling_rate
        ),
        revision_probe = (
            disconfirming_trials_measured = true,
            metric = "posterior_predictive_behavior",
            behavior_change = run.final_revision_behavior_change,
            predicted_aversive_reduction = run.final_predicted_aversive_reduction,
            approach_probability_increase = run.final_approach_probability_increase,
            pre_probe_predicted_aversive = run.final_pre_probe_predicted_aversive,
            post_probe_predicted_aversive = run.final_post_probe_predicted_aversive,
            pre_probe_approach_probability = run.final_pre_probe_approach_probability,
            post_probe_approach_probability = run.final_post_probe_approach_probability,
            structural_precision = run.final_structural_precision
        ),
        cause_banks = (
            cue_counts = (safe = cause.cue_counts[SAFE], threat = cause.cue_counts[AVERSIVE]),
            affect_counts = (safe = cause.affect_counts[SAFE], threat = cause.affect_counts[AVERSIVE]),
            policy_counts = (
                approach = cause.policy_counts[APPROACH],
                flee = cause.policy_counts[FLEE],
                appease = cause.policy_counts[APPEASE],
                attenuate = cause.policy_counts[ATTENUATE]
            ),
            outcome_counts = (
                approach = (safe = cause.outcome_counts[SAFE, APPROACH], threat = cause.outcome_counts[AVERSIVE, APPROACH]),
                flee = (safe = cause.outcome_counts[SAFE, FLEE], threat = cause.outcome_counts[AVERSIVE, FLEE]),
                appease = (safe = cause.outcome_counts[SAFE, APPEASE], threat = cause.outcome_counts[AVERSIVE, APPEASE]),
                attenuate = (safe = cause.outcome_counts[SAFE, ATTENUATE], threat = cause.outcome_counts[AVERSIVE, ATTENUATE])
            )
        )
    )
end

function safe_bundle_name(prefix::String, seed, tag)
    name = replace("$(prefix)_seed$(seed)_$(tag).json", "." => "p")
    return replace(name, "pjson" => ".json")
end

function write_bundle_artifacts(outdir::AbstractString, seed_rows, slow_runs, params::Sim1Params)
    artifacts_dir = ensure_dir(joinpath(outdir, "artifacts"))
    for name in readdir(artifacts_dir)
        startswith(name, "bundle") && endswith(name, ".json") && rm(joinpath(artifacts_dir, name))
    end
    frozen_cells = Set{Tuple{Float64, Float64}}()
    for row in seed_rows
        cell = [other for other in seed_rows if other.omega == row.omega && other.kappa == row.kappa]
        frozen_rate = mean(other.frozen for other in cell)
        revisable_rate = mean(other.revisable for other in cell)
        frozen_rate >= params.cell_classification_rate && revisable_rate < params.cell_classification_rate && push!(frozen_cells, (row.omega, row.kappa))
    end
    frozen = sort(
        [row for row in seed_rows if row.frozen && (row.omega, row.kappa) in frozen_cells];
        by = row -> (row.target_spawned ? 0 : 1, row.omega, row.kappa, row.seed)
    )
    selected = first(frozen, min(params.bundle_seed_count, length(frozen)))
    bundle_paths = String[]
    routes = String[]
    for row in selected
        name = safe_bundle_name("bundle", row.seed, "omega$(round(row.omega; digits = 2))_kappa$(round(row.kappa; digits = 2))")
        path = joinpath(artifacts_dir, name)
        write_json(path, bundle_artifact(row))
        push!(bundle_paths, path)
        push!(routes, row.target_route)
    end
    slow_selected = first([run for run in slow_runs if run.crossed && !run.spawned], min(2, count(run -> run.crossed && !run.spawned, slow_runs)))
    for run in slow_selected
        name = safe_bundle_name("bundle_slow", run.seed, "trial$(run.cross_trial)")
        path = joinpath(artifacts_dir, name)
        write_json(path, slow_bundle_artifact(run))
        push!(bundle_paths, path)
        push!(routes, "slow_accumulation")
    end
    manifest = (
        schema_version = "sim1.bundle-manifest.v3",
        bundle_count = length(bundle_paths),
        slow_accumulation_bundle_count = count(==("slow_accumulation"), routes),
        bundles = [basename(path) for path in bundle_paths],
        schema = "sim1.bundle.v3"
    )
    write_json(joinpath(artifacts_dir, "bundle-manifest.json"), manifest)
    return artifacts_dir, bundle_paths
end

# Verdict aggregation matches the suite convention (Runner.theory_label): only
# success-kind criteria gate the headline result. Adversarial rows never gate —
# including deliberately retained falsified records like the original A1.5 —
# but any adversarial falsification is surfaced in status.json so a genuinely
# failed control cannot hide behind this rule.
function theory_label(results)
    isempty(results.results) && return "null"
    labels = [row.label for row in results.results if row.kind == "success"]
    isempty(labels) && return "null"
    any(==("falsified"), labels) && return "falsified"
    all(==("support"), labels) && return "support"
    any(==("weak_support"), labels) && return "weak_support"
    return "null"
end

adversarial_falsified_ids(results) =
    [row.id for row in results.results if row.kind == "adversarial" && row.label == "falsified"]

function write_run_readme(path::AbstractString, summary)
    phase_title = summary.run_phase == "pilot" ? "Step A Pilot" : "Step B Confirmatory"
    open(path, "w") do io
        println(io, "# Sim 1 T4.6 $phase_title")
        println(io)
        println(io, "Run phase: $(summary.run_phase). Arm 1 lets successful overt action suppress later potential hazards; Arm 2 replays the potential-hazard stream exactly. Kappa changes action efficacy only.")
        println(io)
        println(io, "## Behavioral Revision")
        println(io)
        println(io, "Revision is the larger expected-direction change in cue-level approach outcome prediction or softmax approach probability after the safe probe. No KL score enters classification.")
        println(io)
        println(io, "## Headline Metrics")
        println(io)
        println(io, "- Closed-loop frozen region cells: $(summary.arm_1_closed_loop.frozen_region_cell_count)")
        println(io, "- Closed-loop largest frozen component: $(summary.arm_1_closed_loop.frozen_largest_component)")
        println(io, "- Yoked frozen region cells: $(summary.arm_2_yoked.frozen_region_cell_count)")
        println(io, "- Yoked largest frozen component: $(summary.arm_2_yoked.frozen_largest_component)")
        println(io, "- A1.5 cell contrast: $(summary.two_arm_contrast.frozen_region_cell_contrast)")
        println(io, "- Slow-path crossed rate: $(summary.slow_path.crossed_rate)")
        println(io, "- Spawn diagnosis: $(summary.spawn_diagnostic.outcome)")
        println(io, "- Yoked max delivered aversive-count range: $(summary.arm_2_yoked.exact_replay.max_aversive_count_range)")
        println(io, "- Bundle schema: $(summary.artifacts.bundle_schema)")
    end
end

function run_sim1(config::ExperimentConfig; config_path::Union{Nothing, AbstractString} = nothing, output_dir::Union{Nothing, AbstractString} = nothing)
    started = time()
    run_phase = config.label == "pilot" ? "pilot" : "confirmatory"
    params = sim1_params(config.model_params)
    omegas = linspace_from_grid(config.sweep_grid, "omega")
    kappas = linspace_from_grid(config.sweep_grid, "kappa")
    outdir = ensure_dir(output_dir)

    closed_seed_rows, closed_cell_rows = run_sweep(config.seeds, omegas, kappas, params; arm = :closed_loop)
    yoked_seed_rows, yoked_cell_rows = run_sweep(config.seeds, omegas, kappas, params; arm = :yoked)
    seed_rows = vcat(closed_seed_rows, yoked_seed_rows)
    cell_rows = vcat(closed_cell_rows, yoked_cell_rows)
    mediation_rows = action_mediation_rows(closed_cell_rows)
    closed_classification = classify_grid(closed_cell_rows, omegas, kappas, params)
    yoked_classification = classify_grid(yoked_cell_rows, omegas, kappas, params)

    slow_runs = [run_slow_path(seed, params) for seed in config.seeds]
    shuffle_runs = [run_slow_path(seed, params; shuffle = true) for seed in config.seeds]
    slow_path = first(slow_runs).path
    attenuation = attenuation_corner_metric(closed_cell_rows, params)
    a11 = omega_only_frozen_metric(config.seeds, omegas, params)
    a12_smoothness, a12_traces = concentration_boundary_smoothness(config.seeds, omegas, kappas, params)
    attenuation_sensitivity = attenuation_preference_sensitivity(config.seeds, omegas, kappas, params)
    artifacts_dir, bundle_paths = write_bundle_artifacts(outdir, closed_seed_rows, slow_runs, params)

    high_high_frozen = high_high_frozen_rate(closed_cell_rows, omegas, kappas)
    high_high_cells = high_high_frozen_cell_fraction(closed_cell_rows, omegas, kappas, params)
    yoking = kappa_yoking_metrics(yoked_seed_rows, omegas, kappas)
    release = kappa_release_metrics(closed_seed_rows, yoked_seed_rows, params)
    attenuation_kappa = attenuation_kappa_localization(closed_cell_rows, params)
    closed_potential_ranges = [maximum(row.potential_aversive_count for row in closed_seed_rows if row.seed == seed && row.omega == omega) -
                               minimum(row.potential_aversive_count for row in closed_seed_rows if row.seed == seed && row.omega == omega)
                               for seed in config.seeds, omega in omegas]
    closed_accounting_error = maximum(abs(row.exposure_accounting_error) for row in mediation_rows)
    slow_cross_rate = mean(row.crossed ? 1.0 : 0.0 for row in slow_runs)
    shuffle_cross_rate = mean(row.crossed ? 1.0 : 0.0 for row in shuffle_runs)
    slow_max_pe = maximum(row.max_per_trial_pe for row in slow_runs)
    slow_crossing_pes = [row.cross_trial_pe for row in slow_runs if row.crossed]
    slow_max_crossing_pe = isempty(slow_crossing_pes) ? Inf : maximum(slow_crossing_pes)
    closed_frozen_rows = [row for row in closed_seed_rows if row.frozen]
    yoked_frozen_rows = [row for row in yoked_seed_rows if row.frozen]
    acute_frozen_rows = [row for row in closed_frozen_rows if row.omega >= params.acute_region_omega_min]
    acute_region_present = !isempty(acute_frozen_rows)
    acute_min = acute_region_present ? minimum(row.max_precision_weighted_pe for row in acute_frozen_rows) : 0.0
    frozen_region_contrast = closed_classification.frozen_region_cell_count - yoked_classification.frozen_region_cell_count

    all_prediction_failures = sum(row.prediction_failure_count for row in seed_rows)
    total_spawn_events = sum(row.spawn_count for row in seed_rows)
    spawn_outcome = total_spawn_events > 0 ?
        (params.crp_threshold_base == 0.085 ? "spawning_present_at_original_scale" : "posterior_predictive_threshold_rescaled_on_pilot") :
        "formation_by_spawning_dead_in_binary_environment_class"

    criteria_metrics = (
        connected_frozen_region_closed_loop = closed_classification.frozen_largest_component >= params.connected_region_min_cells ? 1.0 : 0.0,
        connected_revisable_region_closed_loop = closed_classification.revisable_largest_component >= params.connected_region_min_cells ? 1.0 : 0.0,
        high_omega_high_kappa_frozen_rate_closed_loop = high_high_frozen,
        high_omega_high_kappa_frozen_cell_fraction_closed_loop = high_high_cells,
        slow_path_crosses_below_acute_min_closed_loop = (acute_region_present && slow_cross_rate >= 0.80 && slow_max_crossing_pe < acute_min) ? 1.0 : 0.0,
        attenuate_corner_only_closed_loop = attenuation.pass,
        s14_attenuation_efficacious_max_rate = attenuation_kappa.efficacious_max_rate,
        s14_attenuation_kappa_gradient = attenuation_kappa.kappa_gradient,
        three_traits_logged = 1.0,
        a11_omega_only_frozen_region_closed_loop = a11,
        a12_boundary_smoothness_max_jump_closed_loop = a12_smoothness,
        a13_shuffle_cross_rate_closed_loop = shuffle_cross_rate,
        a14_yoked_max_count_range = yoking.max_aversive_count_range,
        a15_frozen_region_cell_contrast = frozen_region_contrast,
        a15r_kappa_release_interaction_cells = Float64(release.interaction_cells),
        a15r_yoked_kappa_flatness_cells = Float64(abs(release.yoked_low_kappa_frozen_cells - release.yoked_high_kappa_frozen_cells)),
        a15r_yoked_minus_closed_revision_gap = release.yoked_minus_closed_revision_gap,
        a15r_closed_to_yoked_exposure_ratio = release.closed_to_yoked_exposure_ratio,
        a15r_yoked_minus_closed_capture_gap = release.yoked_minus_closed_capture_gap
    )

    arm_summary(cell_rows_for_arm, seed_rows_for_arm, classification) = (
        spawn_rate_mean = mean(row.spawn_rate for row in cell_rows_for_arm),
        spawn_events = sum(row.spawn_count for row in seed_rows_for_arm),
        frozen_cell_count = classification.frozen_cell_count,
        frozen_region_cell_count = classification.frozen_region_cell_count,
        frozen_largest_component = classification.frozen_largest_component,
        revisable_cell_count = classification.revisable_cell_count,
        revisable_region_cell_count = classification.revisable_region_cell_count,
        revisable_largest_component = classification.revisable_largest_component,
        mixed_cell_count = classification.mixed_cell_count
    )

    summary = (
        experiment = config.experiment,
        run_phase = run_phase,
        config = config_snapshot(config),
        grid = (omega = omegas, kappa = kappas, cells_per_arm = length(closed_cell_rows), seeds_per_cell = length(config.seeds)),
        arm_1_closed_loop = merge(arm_summary(closed_cell_rows, closed_seed_rows, closed_classification), (
            high_omega_high_kappa_frozen_rate = high_high_frozen,
            mean_potential_aversive_count = mean(row.mean_potential_aversive_count for row in closed_cell_rows),
            mean_delivered_aversive_count = mean(row.mean_aversive_evidence_count for row in closed_cell_rows),
            mean_suppressed_aversive_count = mean(row.mean_suppressed_aversive_count for row in closed_cell_rows),
            max_potential_count_range_across_kappa = maximum(closed_potential_ranges),
            max_exposure_accounting_error = closed_accounting_error,
            attenuation_corner_rate = attenuation.corner_rate,
            attenuation_max_outside_rate = attenuation.max_outside_rate
        )),
        arm_2_yoked = merge(arm_summary(yoked_cell_rows, yoked_seed_rows, yoked_classification), (exact_replay = yoking,)),
        two_arm_contrast = (
            frozen_region_cell_contrast = frozen_region_contrast,
            preregistered_margin_cells = params.arm_contrast_margin_cells,
            margin_met = frozen_region_contrast >= params.arm_contrast_margin_cells,
            interpretation = "closed-loop minus exact-replay frozen-region cells (original A1.5, falsified 2026-07-10, retained for the record)"
        ),
        discovered_traits = (
            high_kappa_seed_level_freezing = (
                rate = high_high_frozen,
                cell_fraction = high_high_cells,
                note = "seeds whose catastrophes land before efficacy is learned freeze even at high kappa: successful avoidance keeps the early collapsed writes dominant. Control prevents chronic freezing, not freezing outright. No corner CELL reaches majority-frozen."
            ),
            attenuation_traps = (
                note = "per-seed attenuation rates above 0.5 occur only for kappa < 0.5, concentrated at LOW omega in the helpless margin: attenuated evidence is too sparse to resolve, so attenuation self-sustains. None of these seeds are frozen; the trap is a distinct dissociative mode, not the freezing mechanism.",
                helpless_column_mean_rate = attenuation_kappa.helpless_column_mean_rate,
                efficacious_max_rate = attenuation_kappa.efficacious_max_rate
            ),
            uncontrollable_adversity_revises = (
                note = "at kappa=0 the spawned causes keep tracking the world (no avoidance loop can seal them) and revise under the probe in BOTH arms: uncontrollable adversity produces honest suffering, not frozen parts. Freezing requires partial control."
            )
        ),
        kappa_release = merge(release, (
            bands = (
                omega_min = params.release_omega_min,
                low_kappa = (params.release_low_kappa_min, params.release_low_kappa_max),
                high_kappa_min = params.release_high_kappa_min
            ),
            interpretation = "A1.5 redefined: arm-by-kappa interaction of freezing (control releases in closed loop, kappa-flat under replay) plus capture-not-mass (closed loop frozen harder on less delivered aversive evidence, mediated by probe capture weight)"
        )),
        behavioral_revision = (
            frozen_max_change = params.behavior_frozen_max_change,
            revisable_min_change = params.behavior_revisable_min_change,
            threat_prediction_threshold = params.threat_prediction_threshold,
            change_definition = "max(pre-minus-post predicted aversive probability, post-minus-pre approach policy probability, zero)"
        ),
        action_mediation = (
            mechanism = "a successful overt response to delivered aversive evidence suppresses subsequent potential hazards for policy-fixed relief trials",
            relief_trials = (approach = params.relief_trials_approach, flee = params.relief_trials_flee, appease = params.relief_trials_appease, attenuate = params.relief_trials_attenuate),
            potential_stream_exact_across_kappa = maximum(closed_potential_ranges) == 0,
            max_exposure_accounting_error = closed_accounting_error,
            per_cell_log = "action_mediation.csv"
        ),
        spawn_diagnostic = (
            outcome = spawn_outcome,
            crp_threshold_base = params.crp_threshold_base,
            total_spawn_events = total_spawn_events,
            total_prediction_failures = all_prediction_failures,
            global_min_posterior_predictive = minimum(row.posterior_predictive_min for row in seed_rows),
            global_max_spawn_pressure = maximum(row.max_spawn_pressure for row in seed_rows),
            spawn_pressure_threshold = params.spawn_pressure_threshold,
            closed_loop_spawn_events = sum(row.spawn_count for row in closed_seed_rows),
            yoked_spawn_events = sum(row.spawn_count for row in yoked_seed_rows),
            pilot_cutoff_candidates = [0.085, 0.12, 0.16, 0.20, 0.24, 0.30, 0.40, 0.50, 0.60, 0.80],
            closed_loop_candidate_spawn_events = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            closed_loop_candidate_max_pressures = [0.6177015404517628, 0.6177015404517628, 0.6177015404517628, 0.6177015404517628, 0.6999321874451618, 0.6999321874451618, 0.6999321874451618, 0.6999328267474814, 0.7393009031293605, 0.7806154926545406],
            diagnosis = "raising the posterior-predictive cutoff through 0.80 created many flagged failures but no sustained arousal pressure; the original 0.085 cutoff is retained"
        ),
        three_traits_log = (
            closed_loop = (
                spawn_events = sum(row.spawn_count for row in closed_seed_rows),
                write_time_reflexivity_mean = mean(row.reflexivity_at_write for row in closed_seed_rows),
                postformation_sampling_rate_mean = mean(row.approach_sampling_rate for row in closed_seed_rows),
                frozen_postformation_sampling_rate_mean = isempty(closed_frozen_rows) ? 0.0 : mean(row.approach_sampling_rate for row in closed_frozen_rows)
            ),
            yoked = (
                spawn_events = sum(row.spawn_count for row in yoked_seed_rows),
                write_time_reflexivity_mean = mean(row.reflexivity_at_write for row in yoked_seed_rows),
                postformation_sampling_rate_mean = mean(row.approach_sampling_rate for row in yoked_seed_rows),
                frozen_postformation_sampling_rate_mean = isempty(yoked_frozen_rows) ? 0.0 : mean(row.approach_sampling_rate for row in yoked_frozen_rows)
            )
        ),
        phase_boundary = (
            closed_loop_frozen_min_omega_by_kappa = boundary_by_kappa(closed_cell_rows, omegas, kappas; threshold = params.cell_classification_rate),
            yoked_frozen_min_omega_by_kappa = boundary_by_kappa(yoked_cell_rows, omegas, kappas; threshold = params.cell_classification_rate),
            closed_loop_revisable_min_omega_by_kappa = boundary_by_kappa(closed_cell_rows, omegas, kappas; field = :revisable_rate, threshold = params.cell_classification_rate),
            closed_loop_smoothness = boundary_smoothness(closed_cell_rows, omegas, kappas; threshold = params.cell_classification_rate)
        ),
        slow_path = (
            arm = "closed_loop",
            crossed_rate = slow_cross_rate,
            first_seed_cross_trial = first(slow_runs).cross_trial,
            first_seed_cross_structural_precision = first(slow_runs).cross_structural_precision,
            max_per_trial_pe = slow_max_pe,
            max_crossing_trial_pe = slow_max_crossing_pe,
            acute_region_min_pe = acute_min,
            below_acute_min = acute_region_present && slow_max_crossing_pe < acute_min,
            pe_comparison = "maximum PE on each crossed seed's crossing trial versus minimum max-per-trial PE among acute closed-loop frozen seed-cells",
            shuffle_cross_rate = shuffle_cross_rate,
            no_spawn_cross_rate = mean((row.crossed && !row.spawned) ? 1.0 : 0.0 for row in slow_runs)
        ),
        adversarial = (
            a11_omega_only_frozen_region_closed_loop = a11,
            a12_boundary_smoothness_traces_closed_loop = a12_traces,
            a13_shuffle_cross_rate_closed_loop = shuffle_cross_rate,
            a14_exact_yoking = yoking,
            a15_frozen_region_cell_contrast = frozen_region_contrast
        ),
        sensitivity = (attenuation_preference_scale_closed_loop = attenuation_sensitivity,),
        criteria = criteria_metrics,
        artifacts = (
            bundle_dir = artifacts_dir,
            bundle_manifest = joinpath(artifacts_dir, "bundle-manifest.json"),
            bundle_schema = "sim1.bundle.v3",
            representative_bundle_count = length(bundle_paths),
            source_arm = "closed_loop"
        ),
        criteria_amendments = (
            original_s11a_status = "died under full evidence yoking in the superseded Step A pilot",
            reformulated_claim = "control-dependent formation is carried by action-mediated evidence sampling; the two-arm contrast is the claim",
            amendment_timing = "before any confirmatory run",
            a15_preregistered_margin_cells = params.arm_contrast_margin_cells
        ),
        per_seed_metric_count = length(seed_rows),
        cell_metric_count = length(cell_rows)
    )

    summary_path = joinpath(outdir, "summary.json")
    write_json(summary_path, summary)
    write_rows_csv(joinpath(outdir, "per_seed_metrics.csv"), seed_rows)
    write_rows_csv(joinpath(outdir, "posterior_traces.csv"), slow_path)
    write_rows_csv(joinpath(outdir, "cell_metrics.csv"), cell_rows)
    write_rows_csv(joinpath(outdir, "action_mediation.csv"), mediation_rows)
    ensure_dir(joinpath(outdir, "figures"))
    write_phase_svg(joinpath(outdir, "figures", "phase_diagram.svg"), closed_cell_rows, yoked_cell_rows, slow_path, omegas, kappas)
    write_run_readme(joinpath(outdir, "README.md"), summary)

    criteria_results = nothing
    if !isnothing(config.criteria_path) && isfile(config.criteria_path)
        criteria_results = write_criteria_results(config.criteria_path, summary_path, joinpath(outdir, "criteria-results.json"))
    end
    status = (
        implementation_passed = (run_phase == "pilot" ? config.seeds == collect(1001:1010) : (length(config.seeds) >= 20 && isempty(intersect(config.seeds, collect(1001:1010))))) &&
            length(omegas) >= 15 &&
            length(kappas) >= 15 &&
            isfile(joinpath(outdir, "action_mediation.csv")) &&
            isfile(joinpath(outdir, "figures", "phase_diagram.svg")) &&
            isfile(joinpath(artifacts_dir, "bundle-manifest.json")),
        theory_result = isnothing(criteria_results) ? "null" : theory_label(criteria_results),
        adversarial_falsified = isnothing(criteria_results) ? String[] : adversarial_falsified_ids(criteria_results),
        run_phase = run_phase,
        criteria_results_path = isnothing(criteria_results) ? nothing : joinpath(outdir, "criteria-results.json")
    )
    write_json(joinpath(outdir, "status.json"), status)

    metadata = build_reproducibility_metadata(
        config;
        config_path = config_path,
        runtime_seconds = time() - started,
        repo_root = normpath(joinpath(@__DIR__, "..", "..", "..", "..", "..")),
        extra = (
            output_dir = abspath(outdir),
            sim_module = "EmergenceSuite.Sim1",
            design = "two-arm closed-loop versus exact-replay",
            criteria_preregistered = config.criteria_path
        )
    )
    write_json(joinpath(outdir, "metadata.json"), metadata)

    return (
        output_dir = outdir,
        summary = summary,
        status = status,
        criteria_results = criteria_results
    )
end

end
