"""
Sim 8 — concurrent part activation: parts observe parts (EXPLORATORY register).

Iteration 12 rebuild ("no new machinery", Brent-approved; see README
preregistration): every special-purpose structure from iterations 1-11 is
replaced by the agent's ordinary machinery.

- ONE conditional table per cause: outcome counts conditioned on which cause
  was active entering the trial. Its marginal is the cause's experience bank
  (activations sum to one), so predictive fit, fear, and mass are reads of the
  same structure. "Parts observe parts" is ordinary contextual learning whose
  context happens to be internal.
- ONE write rule: the arousal-scaled personal rule, bilinear (observer's
  current posterior responsibility x observed cause's entering activation).
  No severity multipliers, no excess gains: conditional-vs-marginal contrast
  is hypothesized to discount expected storms automatically, because a
  marginal IS the agent's expectation.
- Access is a POLICY: contacting part i is an ordinary action each cause
  scores from its own conditional (allow vs leave-as-is) with the suite's
  standard preferences; the mass-prior mixture aggregates; access is the
  softmax share of allow. Protective disposition emerges as causes whose
  conditional about the target is worse than their marginal voting no.

Sim 1's frozen world is imported read-only. Nothing directional is coded:
direction, if any, must be grown from who was active entering the
unassimilable moments. Controls: pair-shuffle of conditional contexts, and a
standing no-gate (access=1) arm; descent only counts where the baseline
passes AND the no-gate arm fails (gate_earned).
"""
module Sim8

using Random
using Statistics
using ..Config: ExperimentConfig
using ..IO: ensure_dir, write_json, write_rows_csv
using ..Criteria: write_criteria_results
using ..Reproducibility: build_reproducibility_metadata
using ..Sim1

const SAFE = 1
const AVERSIVE = 2
const APPROACH = 1
const FLEE = 2
const APPEASE = 3
const ATTENUATE = 4
const EPS = 1e-12

Base.@kwdef struct Sim8Params
    # Inherited Sim 1 constants (provenance: sim1/magic-numbers.md; unchanged)
    learning_rate_base::Float64 = 0.16
    learning_rate_arousal_gain::Float64 = 60.0
    arousal_pe_scale::Float64 = 5.2
    assimilation_capacity::Float64 = 1.0
    spawn_pressure_threshold::Float64 = 1.2
    spawn_pressure_decay::Float64 = 0.72
    efe_flatness_threshold::Float64 = 0.55
    safe_preference::Float64 = 1.35
    aversive_preference::Float64 = -2.35
    overt_action_cost::Float64 = 0.03
    attenuation_cost::Float64 = 0.80
    policy_softmax_temperature::Float64 = 1.0
    # Formation schedule: episodes of (omega, kappa, acute, consolidation)
    episodes::Vector{NTuple{4, Float64}} = [
        (2.6, 0.2, 72.0, 128.0), (2.2, 0.35, 48.0, 96.0),
        (2.7, 0.15, 60.0, 110.0), (2.3, 0.3, 48.0, 96.0)]
    # Surviving Sim 8 constants (provenance sim8/magic-numbers.md)
    internal_conf_k::Float64 = 4.0
    contact_fraction::Float64 = 0.05
    therapy_sessions::Int = 40
    spawn_prior_count::Float64 = 1.0
end

function sim8_params(raw::AbstractDict)
    episodes = haskey(raw, "episodes") ?
        [Tuple(Float64.(ep)) for ep in raw["episodes"]] :
        Sim8Params().episodes
    base = Sim8Params()
    getf(k, d) = Float64(get(raw, k, d))
    return Sim8Params(
        learning_rate_base = getf("learning_rate_base", base.learning_rate_base),
        learning_rate_arousal_gain = getf("learning_rate_arousal_gain", base.learning_rate_arousal_gain),
        arousal_pe_scale = getf("arousal_pe_scale", base.arousal_pe_scale),
        assimilation_capacity = getf("assimilation_capacity", base.assimilation_capacity),
        spawn_pressure_threshold = getf("spawn_pressure_threshold", base.spawn_pressure_threshold),
        spawn_pressure_decay = getf("spawn_pressure_decay", base.spawn_pressure_decay),
        efe_flatness_threshold = getf("efe_flatness_threshold", base.efe_flatness_threshold),
        safe_preference = getf("safe_preference", base.safe_preference),
        aversive_preference = getf("aversive_preference", base.aversive_preference),
        overt_action_cost = getf("overt_action_cost", base.overt_action_cost),
        attenuation_cost = getf("attenuation_cost", base.attenuation_cost),
        policy_softmax_temperature = getf("policy_softmax_temperature", base.policy_softmax_temperature),
        episodes = episodes,
        internal_conf_k = getf("internal_conf_k", base.internal_conf_k),
        contact_fraction = getf("contact_fraction", base.contact_fraction),
        therapy_sessions = Int(get(raw, "therapy_sessions", base.therapy_sessions)),
        spawn_prior_count = getf("spawn_prior_count", base.spawn_prior_count),
    )
end

mutable struct Cause
    id::Int
    # THE table: outcome counts conditioned on which cause was active entering
    # the trial. Everything else is a read of this structure or of the policy
    # banks below.
    context_counts::Dict{Int, Vector{Float64}}
    outcome_counts::Matrix{Float64}         # 2 x 4 outcome given policy
    policy_counts::Vector{Float64}
    severity_counts::Vector{Float64}        # Sim 1 semantic: [ordinary, catastrophic] given aversive
    born_trial::Int
    spawned::Bool
end

# Newborns carry a FLAT severity prior — they are born of the event the
# ordinary-adapted world model could not claim; established causes carry
# Sim 1's ordinary-biased prior.
new_cause(id, born, spawned, prior) = Cause(
    id, Dict{Int, Vector{Float64}}(), fill(prior, 2, 4), fill(prior, 4),
    spawned ? [0.5, 0.5] : [1.0, 0.05], born, spawned)

mutable struct AgentState
    causes::Vector{Cause}
    activation::Vector{Float64}   # posterior responsibility from previous trial
    spawn_pressure::Float64
    spawn_count::Int
end

function init_agent(params::Sim8Params)
    root = new_cause(1, 0, false, 1.0)
    # Modest initial world knowledge under its own context (no direction).
    root.context_counts[1] = [6.0, 4.0]
    return AgentState([root], [1.0], 0.0, 0)
end

"Marginal of the conditional table = the cause's experience bank."
function marginal(c::Cause)
    m = [0.5, 0.5]  # symmetric prior mass, as each context row carries
    for bank in values(c.context_counts)
        m .+= bank .- 0.5
    end
    return m
end

function conditional(c::Cause, i_id::Int)
    get(c.context_counts, i_id, [0.5, 0.5])
end

affect_aversive(c::Cause) = (m = marginal(c); m[AVERSIVE] / sum(m))
cause_mass(c::Cause) = sum(marginal(c))

function predictive(c::Cause, outcome::Int, catastrophic::Bool)
    p = outcome == AVERSIVE ? affect_aversive(c) : 1.0 - affect_aversive(c)
    if outcome == AVERSIVE
        p_cat = c.severity_counts[2] / sum(c.severity_counts)
        p *= catastrophic ? p_cat : 1.0 - p_cat
    end
    return p
end

function responsibilities(agent::AgentState, outcome::Int, catastrophic::Bool)
    prior = [cause_mass(c) for c in agent.causes]
    prior ./= sum(prior)
    post = [prior[k] * predictive(agent.causes[k], outcome, catastrophic) for k in eachindex(agent.causes)]
    s = sum(post)
    return s > EPS ? post ./ s : prior
end

function policy_scores(agent::AgentState, params::Sim8Params)
    prior = [cause_mass(c) for c in agent.causes]
    prior ./= sum(prior)
    scores = zeros(4)
    for (k, c) in enumerate(agent.causes)
        for p in 1:4
            col = c.outcome_counts[:, p]
            p_av = col[AVERSIVE] / sum(col)
            util = params.safe_preference * (1.0 - p_av) + params.aversive_preference * p_av
            util -= p == ATTENUATE ? params.attenuation_cost : params.overt_action_cost
            scores[p] += prior[k] * util
        end
    end
    return scores
end

function run_formation_trial!(rng::AbstractRNG, agent::AgentState, world, potential, kappa::Float64,
                              params::Sim8Params, trial::Int)
    scores = policy_scores(agent, params)
    policy_idx = argmax(scores)
    s1p = Sim1.Sim1Params()  # world semantics only (relief windows, efficacy map)
    obs = Sim1.observe_environment(rng, potential, kappa, policy_idx, :closed_loop, world, s1p)
    outcome = obs.evidence_outcome == Sim1.AVERSIVE ? AVERSIVE : SAFE
    severity = obs.evidence_severity
    catastrophic = outcome == AVERSIVE && severity > 1.5
    prior = [cause_mass(c) for c in agent.causes]; prior ./= sum(prior)
    mix_pred = sum(prior[k] * predictive(agent.causes[k], outcome, catastrophic) for k in eachindex(agent.causes))
    pe = -log(max(mix_pred, EPS)) * severity
    arousal = 1.0 - exp(-pe / params.arousal_pe_scale)
    # Spawn gate: surprise excess + flat overt landscape (Sim 1's fork).
    overt = scores[1:3]
    spread = maximum(overt) - minimum(overt)
    agent.spawn_pressure = agent.spawn_pressure * params.spawn_pressure_decay +
        max(0.0, pe - params.assimilation_capacity)
    spawned = false
    if agent.spawn_pressure >= params.spawn_pressure_threshold && spread < params.efe_flatness_threshold
        push!(agent.causes, new_cause(length(agent.causes) + 1, trial, true, params.spawn_prior_count))
        push!(agent.activation, 0.0)
        agent.spawn_count += 1
        agent.spawn_pressure = 0.0
        spawned = true
    end
    # Sim 1's spawn semantic: the triggering trial's write is assigned wholly
    # to the newborn — spawning IS the assignment of the unassimilable event
    # to the new cause. All later trials use the ordinary mixture.
    r = if spawned
        onehot = zeros(length(agent.causes)); onehot[end] = 1.0; onehot
    else
        responsibilities(agent, outcome, catastrophic)
    end
    # THE single write rule: arousal-scaled, bilinear (observer's current
    # posterior responsibility x observed cause's entering activation), into
    # the observer's conditional table under the observed cause's context.
    # Summing a cause's writes over contexts gives exactly its old personal
    # write (activations sum to one) — the marginal IS the experience bank.
    lr = params.learning_rate_base * (1.0 + params.learning_rate_arousal_gain * arousal / params.arousal_pe_scale)
    for (jk, j) in enumerate(agent.causes)
        for (ik, i) in enumerate(agent.causes)
            ik <= length(agent.activation) || continue
            w = lr * r[jk] * agent.activation[ik]
            w <= EPS && continue
            bank = get!(j.context_counts, i.id, [0.5, 0.5])
            bank[outcome] += w
        end
        # Policy banks unchanged (world-action learning).
        wj = lr * r[jk]
        j.outcome_counts[outcome, policy_idx] += wj
        j.policy_counts[policy_idx] += r[jk]
        outcome == AVERSIVE && (j.severity_counts[catastrophic ? 2 : 1] += lr * r[jk])
    end
    agent.activation = r
    return (trial = trial, outcome = outcome, spawned = spawned, policy = policy_idx,
            pe = pe, arousal = arousal, n_causes = length(agent.causes))
end

"""
Learned contrast of j about i: conditional aversive fraction (shrunk toward
j's own marginal at fixed pseudo-count, so equal risk reads zero at any
exposure) minus the marginal. The marginal is j's expectation, so expected
storms raise both terms together and self-discount (iteration-12 hypothesis).
"""
function aversion(j::Cause, i_id::Int, params::Sim8Params)
    haskey(j.context_counts, i_id) || return 0.0
    bank = j.context_counts[i_id]
    n = sum(bank) - 1.0
    n <= EPS && return 0.0
    m = marginal(j)
    base = m[AVERSIVE] / sum(m)
    frac = (bank[AVERSIVE] + params.internal_conf_k * base) / (sum(bank) + params.internal_conf_k)
    return max(0.0, 2.0 * (frac - base))
end

"""
Access as an ordinary policy: each cause scores allowing contact with i from
its own conditional about i (shrunk toward its marginal) versus leaving
things as they are (its marginal), with the suite's standard preferences; the
mass-prior mixture aggregates; access is the softmax share of allow. No gain
constants; protective disposition emerges as causes whose conditional about
the target is worse than their marginal voting no.
"""
function access_fraction(agent::AgentState, target::Cause, params::Sim8Params)
    prior = [cause_mass(c) for c in agent.causes]
    prior ./= sum(prior)
    u_allow = 0.0
    u_leave = 0.0
    for (k, c) in enumerate(agent.causes)
        m = marginal(c)
        base = m[AVERSIVE] / sum(m)
        p_av = if c.id == target.id
            base
        else
            bank = conditional(c, target.id)
            (bank[AVERSIVE] + params.internal_conf_k * base) / (sum(bank) + params.internal_conf_k)
        end
        u_allow += prior[k] * (params.safe_preference * (1.0 - p_av) + params.aversive_preference * p_av)
        u_leave += prior[k] * (params.safe_preference * (1.0 - base) + params.aversive_preference * base)
    end
    t = max(params.policy_softmax_temperature, EPS)
    ea = exp(u_allow / t)
    return ea / (ea + exp(u_leave / t))
end

function run_therapy!(rng::AbstractRNG, agent::AgentState, params::Sim8Params; force_access::Bool = false)
    first_selection = Dict{Int, Int}()
    rows = NamedTuple[]
    for session in 1:params.therapy_sessions
        best_score, best = -Inf, 0
        order = shuffle(rng, collect(eachindex(agent.causes)))
        for k in order
            c = agent.causes[k]
            acc_k = force_access ? 1.0 : access_fraction(agent, c, params)
            score = acc_k * affect_aversive(c)
            if score > best_score + EPS
                best_score, best = score, k
            end
        end
        target = agent.causes[best]
        acc = force_access ? 1.0 : access_fraction(agent, target, params)
        haskey(first_selection, target.id) || (first_selection[target.id] = session)
        # Contact = a trial in which the target is active and the outcome is
        # safe; everyone writes through the SAME conditional-table path.
        # Mass-relative so ordering cannot come from small-banks-move-faster.
        w = params.contact_fraction * cause_mass(target) * acc
        for j in agent.causes
            bank = get!(j.context_counts, target.id, [0.5, 0.5])
            bank[SAFE] += w
        end
        push!(rows, (session = session, target_id = target.id, access = acc,
                     target_aversive = affect_aversive(target)))
    end
    return first_selection, rows
end

"Shuffle control: permute learned conditional banks across ordered pairs."
function shuffle_internal!(rng::AbstractRNG, agent::AgentState)
    pairs = [(j, i_id) for j in agent.causes for i_id in keys(j.context_counts) if i_id != j.id]
    banks = [copy(j.context_counts[i_id]) for (j, i_id) in pairs]
    perm = shuffle(rng, collect(eachindex(banks)))
    for (idx, (j, i_id)) in enumerate(pairs)
        j.context_counts[i_id] = banks[perm[idx]]
    end
    return agent
end

snapshot(agent::AgentState) = deepcopy(agent)

function run_seed(seed::Int, params::Sim8Params)
    action_rng = MersenneTwister(seed + 1_000_003)
    agent = init_agent(params)
    world = Sim1.WorldState(0, 0, 0, false)
    s1p = Sim1.Sim1Params()
    trial = 0
    for (ei, ep) in enumerate(params.episodes)
        omega, kappa, acute, consolidation = ep
        rng = MersenneTwister(seed + 7919 * ei)
        stream = vcat(
            [Sim1.sample_evidence(rng, omega, s1p) for _ in 1:Int(acute)],
            [Sim1.sample_evidence(rng, omega, s1p; catastrophes = false) for _ in 1:Int(consolidation)])
        for potential in stream
            trial += 1
            run_formation_trial!(action_rng, agent, world, potential, kappa, params, trial)
        end
    end
    causes = agent.causes
    n = length(causes)
    pair_rows = NamedTuple[]
    directional = 0; total_pairs = 0
    for j in causes, i in causes
        j.born_trial > i.born_trial || continue
        a_ji = aversion(j, i.id, params)
        a_ij = aversion(i, j.id, params)
        total_pairs += 1
        directional += a_ji > a_ij + EPS ? 1 : 0
        push!(pair_rows, (seed = seed, later_id = j.id, earlier_id = i.id,
                          later_about_earlier = a_ji, earlier_about_later = a_ij))
    end
    therapy_rng = MersenneTwister(seed + 5_000_011)
    base_agent = snapshot(agent)
    first_sel, session_rows = run_therapy!(therapy_rng, base_agent, params)
    shuf_agent = shuffle_internal!(MersenneTwister(seed + 6_000_029), snapshot(agent))
    shuf_first, _ = run_therapy!(MersenneTwister(seed + 5_000_011), shuf_agent, params)
    nogate_agent = snapshot(agent)
    nogate_first, _ = run_therapy!(MersenneTwister(seed + 5_000_011), nogate_agent, params; force_access = true)
    outside_in(fs) = begin
        n < 2 && return false
        sels = [get(fs, c.id, typemax(Int)) for c in causes]
        births = [c.born_trial for c in causes]
        order = sortperm(births, rev = true)
        sorted = sels[order]
        all(sorted[k] < sorted[k + 1] for k in 1:(n - 1)) && all(s -> s != typemax(Int), sels)
    end
    return (
        seed = seed,
        n_causes = n,
        spawn_count = agent.spawn_count,
        evaluable = n >= 2,
        directional_pairs = directional,
        total_pairs = total_pairs,
        coupling_directional = total_pairs > 0 && directional > total_pairs / 2,
        descent_pass = outside_in(first_sel),
        shuffled_descent_pass = outside_in(shuf_first),
        nogate_descent_pass = outside_in(nogate_first),
        first_selections = join(["$(c.id):$(get(first_sel, c.id, 0))" for c in causes], " "),
        pair_rows = pair_rows,
        session_rows = session_rows,
    )
end

function run_sim8_config(config::ExperimentConfig; config_path = nothing, output_dir = nothing)
    started = time()
    config.label == "pilot" || error("Sim 8 is EXPLORATORY: pilot label only until a preregistered confirmatory cycle exists")
    config.seeds == collect(1001:1010) || error("Sim 8 pilot is restricted to seeds 1001-1010")
    params = sim8_params(config.model_params)
    outdir = output_dir === nothing ? normpath(joinpath(config.output_dir, config.experiment, config.label)) : output_dir
    ensure_dir(outdir)
    results = [run_seed(seed, params) for seed in config.seeds]
    evaluable = [r for r in results if r.evaluable]
    metrics = (
        formation = (
            multi_cause_seed_count = length(evaluable),
            mean_cause_count = mean(r.n_causes for r in results),
            total_spawns = sum(r.spawn_count for r in results),
        ),
        coupling = (
            directional_seed_count = count(r.coupling_directional for r in evaluable),
            mean_directional_fraction = isempty(evaluable) ? 0.0 :
                mean(r.total_pairs > 0 ? r.directional_pairs / r.total_pairs : 0.0 for r in evaluable),
        ),
        descent = (
            baseline_pass_count = count(r.descent_pass for r in evaluable),
            shuffled_pass_count = count(r.shuffled_descent_pass for r in evaluable),
            shuffle_degradation = count(r.descent_pass for r in evaluable) - count(r.shuffled_descent_pass for r in evaluable),
            nogate_pass_count = count(r.nogate_descent_pass for r in evaluable),
            gate_earned_count = count(r.descent_pass && !r.nogate_descent_pass for r in evaluable),
        ),
    )
    summary = (
        experiment = "sim8",
        register = "EXPLORATORY (sol re-review convention): pilot-shaped; nothing here is confirmatory evidence",
        config = (label = config.label, seeds = config.seeds),
        mechanism = "iteration 12: one conditional table (internal state as context), one arousal-scaled bilinear write rule, access as an ordinary softmax policy; no severity/excess/gain constants",
        metrics = metrics,
        per_seed = [(seed = r.seed, n_causes = r.n_causes, spawns = r.spawn_count,
                     directional_pairs = r.directional_pairs, total_pairs = r.total_pairs,
                     descent = r.descent_pass, shuffled_descent = r.shuffled_descent_pass, nogate = r.nogate_descent_pass,
                     first_selections = r.first_selections) for r in results],
    )
    summary_path = joinpath(outdir, "summary.json")
    write_json(summary_path, summary)
    write_rows_csv(joinpath(outdir, "pair_metrics.csv"), reduce(vcat, [r.pair_rows for r in results]))
    write_rows_csv(joinpath(outdir, "therapy_sessions.csv"), reduce(vcat, [r.session_rows for r in results]))
    criteria_results = nothing
    if !isnothing(config.criteria_path) && isfile(config.criteria_path)
        criteria_results = write_criteria_results(config.criteria_path, summary_path, joinpath(outdir, "criteria-results.json"))
    end
    labels = criteria_results === nothing ? String[] : [row.label for row in criteria_results.results if row.kind == "success"]
    theory = isempty(labels) ? "null" :
        any(==("falsified"), labels) ? "falsified" :
        all(==("support"), labels) ? "support" :
        any(==("weak_support"), labels) ? "weak_support" : "null"
    status = (
        implementation_passed = length(results) == length(config.seeds),
        theory_result = theory,
        register = "exploratory",
        run_phase = "pilot",
        criteria_results_path = criteria_results === nothing ? nothing : joinpath(outdir, "criteria-results.json"),
    )
    write_json(joinpath(outdir, "status.json"), status)
    metadata = build_reproducibility_metadata(
        config;
        config_path = config_path,
        runtime_seconds = time() - started,
        repo_root = normpath(joinpath(@__DIR__, "..", "..", "..", "..", "..")),
        extra = (output_dir = abspath(outdir), sim_module = "EmergenceSuite.Sim8", protocol = "exploratory Step A pilot"),
    )
    write_json(joinpath(outdir, "metadata.json"), metadata)
    return (output_dir = outdir, summary = summary, status = status, criteria_results = criteria_results)
end

export run_sim8_config

end # module
