"""
Sim 8 — concurrent part activation: parts observe parts (EXPLORATORY register).

Decision record: mechanism 2 on substrate 1 (Brent, 2026-07-10; see
projects/emergence-suite/concurrent-activation-sketch.md). Sim 1's frozen
confirmatory record is untouched; its world functions are imported read-only
so formation runs in the SAME two-epoch world (acute catastrophe-live, then
same-omega consolidation).

Substrate: soft responsibility. Every cause receives writes and contributes to
policy in proportion to its posterior responsibility — winner-take-all was the
approximation, this is the mixture it approximated.

Mechanism: a cause's observation space includes the ACTIVATION of other
causes. Each trial, every cause j writes evidence about every other cause i
into an internal bank, weighted by i's activation entering the trial. Nothing
directional is coded anywhere: if the later-formed cause ends up expecting
catastrophe when the earlier one is active, that must come from the epoch
structure of the world (the protector's formative sample of the exile is the
crisis; the exile's sample of the protector is the aftermath).

Therapy: contact target selected by draw-toward-pain gated by GROWN access;
blocking strength for target i = each other cause j's protective policy share
times j's learned catastrophe expectation about i. Contacts write safe
evidence into the target AND into every witness's internal bank about the
target (survived contact relaxes the gate). Access-weighted writes (T4.1c Arm
W rule) — no all-or-nothing gate anywhere. Descent, if it appears, is read
out; it is never encoded. The claim is earnable in both directions.
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
const POLICY_NAMES = ["approach", "flee", "appease", "attenuate"]
const EPS = 1e-12

Base.@kwdef struct Sim8Params
    # Inherited Sim 1 constants (provenance: sim1/magic-numbers.md; unchanged)
    learning_rate_base::Float64 = 0.16
    learning_rate_arousal_gain::Float64 = 60.0
    arousal_pe_scale::Float64 = 5.2
    reflexivity_arousal_slope::Float64 = 0.88
    assimilation_capacity::Float64 = 1.0
    spawn_pressure_threshold::Float64 = 1.2
    spawn_pressure_decay::Float64 = 0.72
    efe_flatness_threshold::Float64 = 0.55
    safe_preference::Float64 = 1.35
    aversive_preference::Float64 = -2.35
    overt_action_cost::Float64 = 0.03
    attenuation_cost::Float64 = 0.80
    # Formation schedule: episodes of (omega, kappa, acute, consolidation)
    episodes::Vector{NTuple{4, Float64}} = [(2.6, 0.2, 72.0, 128.0), (2.2, 0.35, 48.0, 96.0)]
    # New Sim 8 constants (pilot provenance in sim8/magic-numbers.md)
    internal_write_rate::Float64 = 0.16
    internal_conf_k::Float64 = 4.0
    block_gain::Float64 = 1.0
    contact_write::Float64 = 6.0
    therapy_sessions::Int = 40
    spawn_prior_count::Float64 = 1.0
end

function sim8_params(raw::AbstractDict)
    episodes = haskey(raw, "episodes") ?
        [Tuple(Float64.(ep)) for ep in raw["episodes"]] :
        [(2.6, 0.2, 72.0, 128.0), (2.2, 0.35, 48.0, 96.0)]
    base = Sim8Params()
    getf(k, d) = Float64(get(raw, k, d))
    return Sim8Params(
        learning_rate_base = getf("learning_rate_base", base.learning_rate_base),
        learning_rate_arousal_gain = getf("learning_rate_arousal_gain", base.learning_rate_arousal_gain),
        arousal_pe_scale = getf("arousal_pe_scale", base.arousal_pe_scale),
        reflexivity_arousal_slope = getf("reflexivity_arousal_slope", base.reflexivity_arousal_slope),
        assimilation_capacity = getf("assimilation_capacity", base.assimilation_capacity),
        spawn_pressure_threshold = getf("spawn_pressure_threshold", base.spawn_pressure_threshold),
        spawn_pressure_decay = getf("spawn_pressure_decay", base.spawn_pressure_decay),
        efe_flatness_threshold = getf("efe_flatness_threshold", base.efe_flatness_threshold),
        safe_preference = getf("safe_preference", base.safe_preference),
        aversive_preference = getf("aversive_preference", base.aversive_preference),
        overt_action_cost = getf("overt_action_cost", base.overt_action_cost),
        attenuation_cost = getf("attenuation_cost", base.attenuation_cost),
        episodes = episodes,
        internal_write_rate = getf("internal_write_rate", base.internal_write_rate),
        internal_conf_k = getf("internal_conf_k", base.internal_conf_k),
        block_gain = getf("block_gain", base.block_gain),
        contact_write = getf("contact_write", base.contact_write),
        therapy_sessions = Int(get(raw, "therapy_sessions", base.therapy_sessions)),
        spawn_prior_count = getf("spawn_prior_count", base.spawn_prior_count),
    )
end

mutable struct Cause
    id::Int
    affect_counts::Vector{Float64}          # [safe, aversive]
    outcome_counts::Matrix{Float64}         # 2 x 4 outcome given policy
    policy_counts::Vector{Float64}
    reflexive_mass::Float64
    total_mass::Float64
    internal::Dict{Int, Vector{Float64}}    # other cause id => [safe, aversive]
    witness_baseline::Vector{Float64}       # same write rule, unconditional
    born_trial::Int
    spawned::Bool
end

new_cause(id, born, spawned, prior) = Cause(
    id, fill(prior, 2), fill(prior, 2, 4), fill(prior, 4), 0.0, 0.0,
    Dict{Int, Vector{Float64}}(), fill(0.5, 2), born, spawned)

mutable struct AgentState
    causes::Vector{Cause}
    activation::Vector{Float64}   # posterior responsibility from previous trial
    spawn_pressure::Float64
    spawn_count::Int
end

function init_agent(params::Sim8Params)
    root = new_cause(1, 0, false, 1.0)
    # Modest initial world knowledge, symmetric across policies (no direction).
    root.affect_counts .= [6.0, 4.0]
    return AgentState([root], [1.0], 0.0, 0)
end

affect_aversive(c::Cause) = c.affect_counts[AVERSIVE] / sum(c.affect_counts)
predictive(c::Cause, outcome::Int) = outcome == AVERSIVE ? affect_aversive(c) : 1.0 - affect_aversive(c)
cause_mass(c::Cause) = sum(c.affect_counts)

function responsibilities(agent::AgentState, outcome::Int)
    prior = [cause_mass(c) for c in agent.causes]
    prior ./= sum(prior)
    post = [prior[k] * predictive(agent.causes[k], outcome) for k in eachindex(agent.causes)]
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
    # Mixture prediction error and arousal (Sim 1 formulas, mixture predictive).
    prior = [cause_mass(c) for c in agent.causes]; prior ./= sum(prior)
    mix_pred = sum(prior[k] * predictive(agent.causes[k], outcome) for k in eachindex(agent.causes))
    pe = -log(max(mix_pred, EPS)) * severity
    arousal = 1.0 - exp(-pe / params.arousal_pe_scale)
    reflexivity = max(0.0, 1.0 - params.reflexivity_arousal_slope * arousal)
    # Spawn gate: surprise excess + flat overt landscape (Sim 1's fork).
    overt = scores[1:3]
    spread = maximum(overt) - minimum(overt)
    agent.spawn_pressure = agent.spawn_pressure * params.spawn_pressure_decay +
        max(0.0, pe - params.assimilation_capacity)
    spawned = false
    if agent.spawn_pressure >= params.spawn_pressure_threshold && spread < params.efe_flatness_threshold
        c = new_cause(length(agent.causes) + 1, trial, true, params.spawn_prior_count)
        push!(agent.causes, c)
        push!(agent.activation, 0.0)
        agent.spawn_count += 1
        agent.spawn_pressure = 0.0
        spawned = true
    end
    r = responsibilities(agent, outcome)
    # Soft writes: every cause learns in proportion to responsibility.
    lr = params.learning_rate_base * (1.0 + params.learning_rate_arousal_gain * arousal / params.arousal_pe_scale)
    for (k, c) in enumerate(agent.causes)
        w = lr * r[k]
        c.affect_counts[outcome] += w
        c.outcome_counts[outcome, policy_idx] += w
        c.policy_counts[policy_idx] += r[k]
        if outcome == AVERSIVE
            c.reflexive_mass += reflexivity * w
            c.total_mass += w
        end
    end
    # Parts observe parts: j writes about i, weighted by i's activation ENTERING
    # the trial and by the outcome's SEVERITY (iteration 2: what the protector
    # learns about the exile is the catastrophe — the unassimilable input, §4 —
    # not mere valence; both epochs share the ordinary hazard rate, so severity
    # is the only quantity the world makes asymmetric between them). One
    # symmetric rule; any direction must be grown by the epoch structure.
    # Iteration 4: internal observation uses the SAME arousal-scaled write rule
    # as the personal banks (using a flat rate was the inconsistency, not a
    # missing dial). The formative attribution then does the directional work:
    # at a spawn trial, the activation ENTERING the catastrophe is the old
    # cause's, written at ~12x arousal weight and severity 6 into the newborn's
    # bank about it — while the old cause records nothing about the newborn
    # (its entering activation was zero). Ordinary co-existence trials write at
    # ~1x and cannot wash that out. Same lag rule for everyone; direction can
    # only come from who was active entering the unassimilable moments.
    sev_w = outcome == AVERSIVE ? severity : 1.0
    ilr = params.internal_write_rate * (1.0 + params.learning_rate_arousal_gain * arousal / params.arousal_pe_scale)
    for (jk, j) in enumerate(agent.causes)
        # Unconditional baseline: what j's world is like, same rule, weight 1.
        j.witness_baseline[outcome] += ilr * sev_w
        for (ik, i) in enumerate(agent.causes)
            jk == ik && continue
            ik <= length(agent.activation) || continue
            w = ilr * agent.activation[ik]
            w <= EPS && continue
            bank = get!(j.internal, i.id, fill(0.5, 2))
            bank[outcome] += w * sev_w
        end
    end
    agent.activation = r
    return (trial = trial, outcome = outcome, spawned = spawned, policy = policy_idx,
            pe = pe, arousal = arousal, n_causes = length(agent.causes))
end

"""
Learned catastrophe expectation of j about i, CONTRASTIVE (iteration 3): the
excess of j's severity-weighted aversive fraction conditioned on i's activity
over j's own unconditional baseline — "when i is active, things are worse than
my normal." An absolute 0.5 baseline is wrong in a world containing avoidance
(suppression drives everyone's delivered aversive fraction below half, reading
all coupling as zero). Conditional-vs-marginal risk is the quantity a Dirichlet
observer of another part should report. Symmetric rule; earnable either way.
"""
function aversion(j::Cause, i_id::Int, params::Sim8Params)
    haskey(j.internal, i_id) || return 0.0
    bank = j.internal[i_id]
    n = sum(bank) - 1.0  # subtract the symmetric init mass
    n <= EPS && return 0.0
    frac = bank[AVERSIVE] / sum(bank)
    baseline = j.witness_baseline[AVERSIVE] / sum(j.witness_baseline)
    conf = n / (n + params.internal_conf_k)
    return max(0.0, 2.0 * (frac - baseline)) * conf
end

protective_share(c::Cause) = (c.policy_counts[FLEE] + c.policy_counts[APPEASE] + c.policy_counts[ATTENUATE]) / sum(c.policy_counts)

"""
Iteration 5: the internal bank supplies the TARGET of the protector's fear,
not its magnitude — the magnitude is the protector's own catastrophic
expectation (its personal banks are what the catastrophe made them). Blocking
of i by j = j's protective policy share x j's own aversive expectation x the
share of j's danger-attribution that points at i. A cause with no attribution
anywhere blocks nothing; attribution is normalized over the causes j has
actually coupled to, so weak-but-directional contrasts still aim the gate.
"""
function access_fraction(agent::AgentState, target::Cause, params::Sim8Params)
    acc = 1.0
    for j in agent.causes
        j.id == target.id && continue
        total_attr = sum(aversion(j, i.id, params) for i in agent.causes if i.id != j.id; init = 0.0)
        total_attr <= EPS && continue
        attribution = aversion(j, target.id, params) / (total_attr + 0.01)
        block = clamp(params.block_gain * protective_share(j) * affect_aversive(j) * attribution, 0.0, 1.0)
        acc *= 1.0 - block
    end
    return acc
end

function run_therapy!(rng::AbstractRNG, agent::AgentState, params::Sim8Params)
    first_selection = Dict{Int, Int}()
    rows = NamedTuple[]
    for session in 1:params.therapy_sessions
        best_score, best = -Inf, 0
        order = shuffle(rng, collect(eachindex(agent.causes)))  # tie-break without ids
        for k in order
            c = agent.causes[k]
            score = access_fraction(agent, c, params) * affect_aversive(c)
            if score > best_score + EPS
                best_score, best = score, k
            end
        end
        target = agent.causes[best]
        acc = access_fraction(agent, target, params)
        haskey(first_selection, target.id) || (first_selection[target.id] = session)
        w = params.contact_write * acc
        target.affect_counts[SAFE] += w
        for j in agent.causes
            j.id == target.id && continue
            bank = get!(j.internal, target.id, fill(0.5, 2))
            bank[SAFE] += w
        end
        push!(rows, (session = session, target_id = target.id, access = acc,
                     target_aversive = affect_aversive(target)))
    end
    return first_selection, rows
end

"Shuffle control: permute learned aversion banks across ordered pairs."
function shuffle_internal!(rng::AbstractRNG, agent::AgentState)
    pairs = [(j, i_id) for j in agent.causes for i_id in keys(j.internal)]
    banks = [copy(j.internal[i_id]) for (j, i_id) in pairs]
    perm = shuffle(rng, collect(eachindex(banks)))
    for (idx, (j, i_id)) in enumerate(pairs)
        j.internal[i_id] = banks[perm[idx]]
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
    formation_rows = NamedTuple[]
    for (ei, ep) in enumerate(params.episodes)
        omega, kappa, acute, consolidation = ep
        rng = MersenneTwister(seed + 7919 * ei)
        stream = vcat(
            [Sim1.sample_evidence(rng, omega, s1p) for _ in 1:Int(acute)],
            [Sim1.sample_evidence(rng, omega, s1p; catastrophes = false) for _ in 1:Int(consolidation)])
        for potential in stream
            trial += 1
            push!(formation_rows, run_formation_trial!(action_rng, agent, world, potential, kappa, params, trial))
        end
    end
    causes = agent.causes
    n = length(causes)
    # Coupling readout: later-onto-earlier aversion vs the reverse, per pair.
    pair_rows = NamedTuple[]
    directional = 0; total_pairs = 0
    for j in causes, i in causes
        j.born_trial > i.born_trial || continue
        a_ji = aversion(j, i.id, params)   # later about earlier
        a_ij = aversion(i, j.id, params)   # earlier about later
        total_pairs += 1
        directional += a_ji > a_ij + EPS ? 1 : 0
        push!(pair_rows, (seed = seed, later_id = j.id, earlier_id = i.id,
                          later_about_earlier = a_ji, earlier_about_later = a_ij))
    end
    # Therapy: baseline arm and shuffled-internal control arm on copies.
    therapy_rng = MersenneTwister(seed + 5_000_011)
    base_agent = snapshot(agent)
    first_sel, session_rows = run_therapy!(therapy_rng, base_agent, params)
    shuf_agent = shuffle_internal!(MersenneTwister(seed + 6_000_029), snapshot(agent))
    shuf_first, _ = run_therapy!(MersenneTwister(seed + 5_000_011), shuf_agent, params)
    # Descent readout: complete newest-to-oldest first-selection ordering.
    outside_in(fs) = begin
        n < 2 && return false
        sels = [get(fs, c.id, typemax(Int)) for c in causes]
        births = [c.born_trial for c in causes]
        order = sortperm(births, rev = true)  # newest first
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
        ),
    )
    summary = (
        experiment = "sim8",
        register = "EXPLORATORY (sol re-review convention): pilot-shaped; nothing here is confirmatory evidence",
        config = (label = config.label, seeds = config.seeds),
        mechanism = "parts observe parts on soft responsibility; direction, if any, grown from the two-epoch world",
        metrics = metrics,
        per_seed = [(seed = r.seed, n_causes = r.n_causes, spawns = r.spawn_count,
                     directional_pairs = r.directional_pairs, total_pairs = r.total_pairs,
                     descent = r.descent_pass, shuffled_descent = r.shuffled_descent_pass,
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
