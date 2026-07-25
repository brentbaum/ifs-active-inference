#!/usr/bin/env julia

include(joinpath(@__DIR__, "..", "..", "src", "ModelOrganism.jl"))
using .ModelOrganism
using Random
using Statistics
using SHA
using Printf

const FREEZE_COMMIT = "274f8888f71ac590d7c15d6f9f59777ea919e182"
const STAGE_B_COMMIT = "1dcd051"
const REVEAL_COMMIT = "6419191"
const CHALLENGES = ("E3", "E4", "E5")
const SEED_START = Dict("E3" => 710107, "E4" => 711362, "E5" => 712457)
const WORLD_COUNT = Dict("E3" => 60, "E4" => 60, "E5" => 40)
const CONFIG_FILE = Dict(
    "E3" => "E3-polarization.toml",
    "E4" => "E4-evidence-format.toml",
    "E5" => "E5-selflike-part.toml",
)
const PROTOCOL_FILE = Dict(
    "E3" => "E3-polarization-protocol.md",
    "E4" => "E4-evidence-format-protocol.md",
    "E5" => "E5-selflike-part-protocol.md",
)
const FROZEN_PATHS = [
    "projects/emergence-suite/continuous/src/ModelOrganism.jl",
    "projects/emergence-suite/continuous/src/model_organism",
    "projects/emergence-suite/continuous/genome.toml",
    "projects/emergence-suite/continuous/organism-genome.md",
    "projects/emergence-suite/continuous/configurations/assay-01.toml",
    "projects/emergence-suite/continuous/configurations/assay-02.toml",
    "projects/emergence-suite/continuous/configurations/assay-03.toml",
    "projects/emergence-suite/continuous/configurations/assay-04.toml",
    "projects/emergence-suite/continuous/configurations/assay-05.toml",
    "projects/emergence-suite/continuous/configurations/assay-06.toml",
    "projects/emergence-suite/continuous/configurations/assay-07.toml",
    "projects/emergence-suite/continuous/configurations/assay-08.toml",
    "projects/emergence-suite/continuous/configurations/assay-09.toml",
    "projects/emergence-suite/continuous/configurations/assay-10.toml",
    "projects/emergence-suite/continuous/results/model_organism/configuration-grammar.md",
    "projects/emergence-suite/continuous/results/model_organism/rng-streams.md",
    "projects/emergence-suite/continuous/results/model_organism/world-populations.md",
    "projects/emergence-suite/continuous/results/model_organism/precalibration-lock.json",
    "projects/emergence-suite/continuous/results/model_organism/assays/1/analysis-plan.md",
    "projects/emergence-suite/continuous/results/model_organism/assays/2/analysis-plan.md",
    "projects/emergence-suite/continuous/results/model_organism/assays/3/analysis-plan.md",
    "projects/emergence-suite/continuous/results/model_organism/assays/4/analysis-plan.md",
    "projects/emergence-suite/continuous/results/model_organism/assays/5/analysis-plan.md",
    "projects/emergence-suite/continuous/results/model_organism/assays/6/analysis-plan.md",
    "projects/emergence-suite/continuous/results/model_organism/assays/7/analysis-plan.md",
    "projects/emergence-suite/continuous/results/model_organism/assays/8/analysis-plan.md",
    "projects/emergence-suite/continuous/results/model_organism/assays/9/analysis-plan.md",
    "projects/emergence-suite/continuous/results/model_organism/assays/10/analysis-plan.md",
]

challenge_root() = joinpath(ModelOrganism.RESULTS_ROOT, "challenges")
revealed_root() = joinpath(ModelOrganism.RESULTS_ROOT, "sealed-revealed")
config_root() = joinpath(ModelOrganism.PROJECT_ROOT, "configurations", "challenges")

function mean_ci(values)
    data = Float64.(values)
    isempty(data) && return [nothing, nothing]
    center = mean(data)
    length(data) == 1 && return [center, center]
    half_width = 1.96 * std(data) / sqrt(length(data))
    return [center - half_width, center + half_width]
end

function wilson_interval(successes::Integer, total::Integer)
    total == 0 && return [nothing, nothing]
    z = 1.96
    p = successes / total
    denominator = 1 + z^2 / total
    center = (p + z^2 / (2 * total)) / denominator
    half_width = z / denominator * sqrt(
        p * (1 - p) / total + z^2 / (4 * total^2))
    return [max(0.0, center - half_width),
        min(1.0, center + half_width)]
end

function criterion(label, estimate, interval, rule, passed;
        details = Dict{String,Any}())
    return Dict(
        "label" => label,
        "evidentiary_class" => "prospective challenge",
        "hypothesis_provenance" => "50-prospective sealed",
        "estimate" => estimate,
        "interval_95" => interval,
        "decision_rule" => rule,
        "passed" => passed,
        "details" => details,
    )
end

function verify_stage_c_inputs!(genome)
    head = readchomp(`git rev-parse HEAD`)
    startswith(head, REVEAL_COMMIT) ||
        error("Stage C blocked: HEAD $head is not reveal commit $REVEAL_COMMIT")
    changed = readchomp(Cmd(vcat(["git", "diff", "--name-only",
        FREEZE_COMMIT, "--"], FROZEN_PATHS)))
    isempty(changed) ||
        error("Stage C blocked: frozen inputs changed:\n$changed")
    revealed = readchomp(`git diff --name-only $REVEAL_COMMIT -- projects/emergence-suite/continuous/results/model_organism/sealed-revealed`)
    isempty(revealed) ||
        error("Stage C blocked: revealed protocols changed:\n$revealed")
    verify_identity!(genome)
    ModelOrganism.verify_precalibration_lock()
    identity = read(joinpath(ModelOrganism.RESULTS_ROOT, "identity.json"), String)
    occursin(ModelOrganism.canonical_source_hash(), identity) ||
        error("Stage C blocked: canonical source identity mismatch")
    occursin(genome.sha256, identity) ||
        error("Stage C blocked: genome identity mismatch")
    return true
end

function released_seeds(challenge)
    count = WORLD_COUNT[challenge]
    first_seed = SEED_START[challenge]
    seeds = collect(first_seed:first_seed + count - 1)
    last(seeds) <= first_seed + 199 ||
        error("$challenge requested more than its released block")
    last(seeds) < 713204 ||
        error("$challenge attempted to enter L-neighborhood escrow")
    return seeds
end

function validate_config!(challenge)
    config = load_configuration(joinpath(config_root(), CONFIG_FILE[challenge]))
    config.assay == 500 + parse(Int, string(last(challenge))) ||
        error("$challenge configuration identifier mismatch")
    challenge == "E3" && get(config.slots, :protectors, 0) == 2 ||
        challenge != "E3" || error("E3 requires two protector slots")
    challenge == "E5" &&
        (:local_monitor in config.edges) &&
        (:recursive_broadcast_off in config.interventions) ||
        challenge != "E5" ||
        error("E5 local-monitor/no-broadcast configuration is inexpressible")
    return config
end

function update_befriending!(protector, observation, genome, event_prefix)
    reliability = ModelOrganism.g(genome, :bayes_reliability)
    ModelOrganism.update_posterior!(protector, :partner_trustworthy,
        observation, reliability, genome; event_kind = :experiment,
        event_id = event_prefix * ":partner")
    ModelOrganism.update_posterior!(protector, :co_protection,
        observation, reliability, genome; event_kind = :experiment,
        event_id = event_prefix * ":competence")
    ModelOrganism.update_posterior!(protector, :outcome_forecast,
        observation, reliability, genome; event_kind = :experiment,
        event_id = event_prefix * ":outcome")
end

function e3_contact_arm(seed, arm, genome, outcomes)
    p1 = ModelOrganism.seeded_state(seed, genome;
        partner = :adverse, favorable_policy = :exclusion)
    p2 = ModelOrganism.seeded_state(seed, genome;
        partner = :adverse, favorable_policy = :oscillation)
    root = ModelOrganism.seeded_state(seed, genome; partner = :adverse)
    dyad = neutral_state(genome)
    initial_root = root.posterior[:root_now]
    permission_episode = 0
    root_episode = 0
    p1_permission_episode = 0
    p2_permission_episode = 0
    for episode in eachindex(outcomes)
        observation = outcomes[episode]
        signal = observation ? 1 : 4
        packet = ModelOrganism.update_dyad!(
            dyad, signal, observation, genome)
        for packet_index in 1:packet.packets
            if arm == :befriend_both
                update_befriending!(p1, observation, genome,
                    "E3:$arm:$seed:$episode:$packet_index:P1")
                update_befriending!(p2, observation, genome,
                    "E3:$arm:$seed:$episode:$packet_index:P2")
            elseif arm == :befriend_one
                update_befriending!(p1, observation, genome,
                    "E3:$arm:$seed:$episode:$packet_index:P1:first")
                update_befriending!(p1, observation, genome,
                    "E3:$arm:$seed:$episode:$packet_index:P1:second")
            end
        end
        permission1 = ModelOrganism.protector_permission(
            p1, ModelOrganism.g(genome, :high_stakes), genome)
        permission2 = ModelOrganism.protector_permission(
            p2, ModelOrganism.g(genome, :high_stakes), genome)
        threshold = ModelOrganism.g(genome, :permission_threshold)
        p1_permission_episode == 0 && permission1 >= threshold &&
            (p1_permission_episode = episode)
        p2_permission_episode == 0 && permission2 >= threshold &&
            (p2_permission_episode = episode)
        if permission1 >= threshold && permission2 >= threshold
            permission_episode == 0 && (permission_episode = episode)
            ModelOrganism.update_root!(root, observation,
                packet.field_weight, genome;
                event_id = "E3:$arm:$seed:$episode:root")
        end
        root_episode == 0 &&
            root.posterior[:root_now] >=
                ModelOrganism.g(genome, :root_revision_begin) &&
            (root_episode = episode)
    end
    descent = permission_episode > 0 && root_episode > 0
    audit = descent && p1_permission_episode > 0 &&
        p2_permission_episode > 0 &&
        p1_permission_episode < root_episode &&
        p2_permission_episode < root_episode
    return (seed = seed, arm = arm, contact_descent = descent,
        root_change = root.posterior[:root_now] - initial_root,
        p1_permission_episode = p1_permission_episode,
        p2_permission_episode = p2_permission_episode,
        conjunction_episode = permission_episode,
        root_revision_episode = root_episode,
        both_permissions_before_root = audit,
        p1_final_permission = ModelOrganism.protector_permission(
            p1, ModelOrganism.g(genome, :high_stakes), genome),
        p2_final_permission = ModelOrganism.protector_permission(
            p2, ModelOrganism.g(genome, :high_stakes), genome),
        p1_probe_strengthening = missing, p2_probe_strengthening = missing,
        p1_opposed_effect = missing, p2_opposed_effect = missing,
        escalation_coupled = missing)
end

function expected_cost(state, policy, genome)
    return ModelOrganism.expected_policy_cost(state, policy, genome)
end

function e3_escalation_arm(seed, genome)
    p1 = ModelOrganism.seeded_state(seed, genome;
        partner = :adverse, favorable_policy = :exclusion)
    p2 = ModelOrganism.seeded_state(seed, genome;
        partner = :adverse, favorable_policy = :oscillation)
    p2_before = expected_cost(p2, :exclusion, genome) -
        expected_cost(p2, :oscillation, genome)
    p1_before = expected_cost(p1, :oscillation, genome) -
        expected_cost(p1, :exclusion, genome)
    p1_probe = deepcopy(p1)
    for episode in 1:Int(ModelOrganism.g(genome, :episodes))
        ModelOrganism.update_policy_belief!(p1_probe, :exclusion,
            ModelOrganism.g(genome, :history_favorable_cost), true, genome;
            event_id = "E3:escalation:$seed:P1:$episode")
    end
    p1_strengthening =
        (expected_cost(p1_probe, :oscillation, genome) -
            expected_cost(p1_probe, :exclusion, genome)) - p1_before
    p2_after = expected_cost(p2, :exclusion, genome) -
        expected_cost(p2, :oscillation, genome)
    p2_effect = p2_after - p2_before
    p2_probe = deepcopy(p2)
    for episode in 1:Int(ModelOrganism.g(genome, :episodes))
        ModelOrganism.update_policy_belief!(p2_probe, :oscillation,
            ModelOrganism.g(genome, :history_favorable_cost), true, genome;
            event_id = "E3:escalation:$seed:P2:$episode")
    end
    p2_strengthening =
        (expected_cost(p2_probe, :exclusion, genome) -
            expected_cost(p2_probe, :oscillation, genome)) - p2_before
    p1_after = expected_cost(p1, :oscillation, genome) -
        expected_cost(p1, :exclusion, genome)
    p1_effect = p1_after - p1_before
    return (seed = seed, arm = :escalation_probe,
        contact_descent = missing, root_change = missing,
        p1_permission_episode = missing, p2_permission_episode = missing,
        conjunction_episode = missing, root_revision_episode = missing,
        both_permissions_before_root = missing,
        p1_final_permission = missing, p2_final_permission = missing,
        p1_probe_strengthening = p1_strengthening,
        p2_probe_strengthening = p2_strengthening,
        p1_opposed_effect = p1_effect, p2_opposed_effect = p2_effect,
        escalation_coupled = p1_effect > 0 && p2_effect > 0)
end

function run_e3(genome)
    validate_config!("E3")
    rows = NamedTuple[]
    for seed in released_seeds("E3")
        rng = ModelOrganism.partner_rng(seed, genome)
        outcomes = rand(rng, Int(ModelOrganism.g(genome, :episodes))) .<
            ModelOrganism.g(genome, :partner_trustworthy_probability)
        for arm in (:befriend_both, :befriend_one, :befriend_none)
            push!(rows, e3_contact_arm(seed, arm, genome, outcomes))
        end
        push!(rows, e3_escalation_arm(seed, genome))
    end
    contact = filter(row -> row.arm != :escalation_probe, rows)
    arm_rows(arm) = filter(row -> row.arm == arm, contact)
    rate(arm) = mean(Float64[row.contact_descent for row in arm_rows(arm)])
    successes(arm) = count(row -> row.contact_descent, arm_rows(arm))
    both_rate, one_rate, none_rate =
        rate(:befriend_both), rate(:befriend_one), rate(:befriend_none)
    escalation = filter(row -> row.arm == :escalation_probe, rows)
    coupled = count(row -> row.escalation_coupled, escalation)
    coupling_rate = coupled / length(escalation)
    opposed = Float64[(row.p1_opposed_effect + row.p2_opposed_effect) / 2
        for row in escalation]
    primary_pass = both_rate >= 0.70 && one_rate <= 0.10 &&
        none_rate <= 0.05
    secondary_pass = coupling_rate >= 0.70 &&
        mean_ci(opposed)[1] !== nothing && mean_ci(opposed)[1] > 0
    achieved = filter(row -> row.arm == :befriend_both &&
        row.contact_descent, rows)
    audit_rate = isempty(achieved) ? 0.0 :
        mean(Float64[row.both_permissions_before_root for row in achieved])
    criteria = [
        criterion("compositional descent", both_rate,
            wilson_interval(successes(:befriend_both), WORLD_COUNT["E3"]),
            "both ≥ 0.70; one ≤ 0.10; none ≤ 0.05", primary_pass;
            details = Dict(
                "befriend_both_rate" => both_rate,
                "befriend_both_interval_95" =>
                    wilson_interval(successes(:befriend_both), WORLD_COUNT["E3"]),
                "befriend_one_rate" => one_rate,
                "befriend_one_interval_95" =>
                    wilson_interval(successes(:befriend_one), WORLD_COUNT["E3"]),
                "befriend_none_rate" => none_rate,
                "befriend_none_interval_95" =>
                    wilson_interval(successes(:befriend_none), WORLD_COUNT["E3"]))),
        criterion("escalation coupling", coupling_rate,
            wilson_interval(coupled, length(escalation)),
            "opposed-direction rate ≥ 0.70 and mean effect 95% interval above zero",
            secondary_pass; details = Dict(
                "mean_opposed_direction_effect" => mean(opposed),
                "mean_effect_interval_95" => mean_ci(opposed))),
    ]
    descriptive = Dict(
        "permissions_before_root_audit_rate" => audit_rate,
        "permissions_before_root_audit_interval_95" =>
            wilson_interval(count(row -> row.both_permissions_before_root,
                achieved), length(achieved)),
        "audit_denominator" => length(achieved),
        "paired_worlds" => WORLD_COUNT["E3"],
        "mean_p1_probe_strengthening" =>
            mean(Float64[row.p1_probe_strengthening for row in escalation]),
        "p1_probe_strengthening_interval_95" =>
            mean_ci(Float64[row.p1_probe_strengthening for row in escalation]),
        "mean_p2_probe_strengthening" =>
            mean(Float64[row.p2_probe_strengthening for row in escalation]),
        "p2_probe_strengthening_interval_95" =>
            mean_ci(Float64[row.p2_probe_strengthening for row in escalation]),
    )
    return rows, criteria, descriptive
end

function cue_step(value, observation, genome)
    return value + (observation ?
        ModelOrganism.g(genome, :cue_positive_step) :
        -ModelOrganism.g(genome, :cue_negative_step))
end

function run_e4_world(seed, genome)
    rng = ModelOrganism.world_rng(seed, genome)
    evidence = rand(rng, Int(ModelOrganism.g(genome, :episodes))) .<
        ModelOrganism.g(genome, :bayes_reliability)
    configural = ModelOrganism.seeded_state(seed, genome)
    cue = ModelOrganism.seeded_state(seed, genome)
    configural_initial = configural.posterior[:root_now]
    cue_initial = cue.posterior[:root_now]
    configural_freeze = ModelOrganism.freeze_write!(configural,
        ModelOrganism.g(genome, :freeze_overwhelm_boundary),
        ModelOrganism.g(genome, :freeze_low_control_boundary), genome;
        event_id = "E4:configural:$seed:freeze")
    cue_freeze = ModelOrganism.freeze_write!(cue,
        ModelOrganism.g(genome, :freeze_overwhelm_boundary),
        ModelOrganism.g(genome, :freeze_low_control_boundary), genome;
        event_id = "E4:cue:$seed:freeze")
    configural_cues = fill(ModelOrganism.g(genome, :cue_initial_belief), 4)
    cue_cues = fill(ModelOrganism.g(genome, :cue_initial_belief), 4)
    reliability = ModelOrganism.g(genome, :bayes_reliability)
    log_lr = abs(log(reliability / (1 - reliability)))
    configural_budget = 0.0
    cue_budget = 0.0
    for episode in eachindex(evidence)
        observation = evidence[episode]
        for feature in 1:4
            configural_cues[feature] =
                cue_step(configural_cues[feature], observation, genome)
            configural_budget += log_lr
        end
        ModelOrganism.update_root!(configural, observation, 1.0, genome;
            event_id = "E4:configural:$seed:$episode")
        for feature in 1:4
            cue_cues[feature] =
                cue_step(cue_cues[feature], observation, genome)
            cue_budget += log_lr
        end
    end
    configural_revision =
        configural.posterior[:root_now] - configural_initial
    cue_revision = cue.posterior[:root_now] - cue_initial
    initial_cue = ModelOrganism.g(genome, :cue_initial_belief)
    configural_transfer =
        ModelOrganism.g(genome, :cue_transfer_weight) * configural_revision
    cue_transfer =
        ModelOrganism.g(genome, :cue_transfer_weight) * cue_revision
    mismatch = abs(configural_budget - cue_budget) /
        max(configural_budget, cue_budget, eps())
    treated_configural = mean(configural_cues) - initial_cue
    treated_cue = mean(cue_cues) - initial_cue
    return (seed = seed,
        configural_root_revision = configural_revision,
        cue_root_revision = cue_revision,
        paired_root_difference = configural_revision - cue_revision,
        configural_root_revised = configural.posterior[:root_now] >=
            ModelOrganism.g(genome, :root_revision_begin),
        cue_root_revised = cue.posterior[:root_now] >=
            ModelOrganism.g(genome, :root_revision_begin),
        configural_untreated_transfer = configural_transfer,
        cue_untreated_transfer = cue_transfer,
        configural_treated_revision = treated_configural,
        cue_treated_revision = treated_cue,
        cue_control_difference = treated_cue - treated_configural,
        configural_loglik_budget = configural_budget,
        cue_loglik_budget = cue_budget,
        budget_mismatch_fraction = mismatch,
        budget_valid = mismatch <= 0.01,
        freeze_written = configural_freeze.written && cue_freeze.written)
end

function run_e4(genome)
    error("E4 scientific execution disabled by apparatus erratum C-002: " *
        "no common likelihood-accounted configural/cue evidence path")
    validate_config!("E4")
    rows = [run_e4_world(seed, genome) for seed in released_seeds("E4")]
    valid = filter(row -> row.budget_valid, rows)
    invalid = length(rows) - length(valid)
    differences = Float64[row.paired_root_difference for row in valid]
    greater = count(row -> row.paired_root_difference > 0, valid)
    greater_rate = isempty(valid) ? 0.0 : greater / length(valid)
    primary_pass = !isempty(valid) && greater_rate >= 0.70 &&
        mean(differences) >= 0.10 && invalid / length(rows) <= 0.10
    transfer_margin = ModelOrganism.g(genome, :assay4_transfer_margin)
    transfer_success = count(row ->
        (row.configural_root_revised ==
            (row.configural_untreated_transfer >= transfer_margin)) &&
        !row.cue_root_revised &&
        row.cue_untreated_transfer < transfer_margin, valid)
    transfer_rate = isempty(valid) ? 0.0 : transfer_success / length(valid)
    configural_revised = count(row -> row.configural_root_revised, valid)
    configural_transfer_present = count(row ->
        row.configural_untreated_transfer >= transfer_margin, valid)
    cue_revised = count(row -> row.cue_root_revised, valid)
    cue_transfer_present = count(row ->
        row.cue_untreated_transfer >= transfer_margin, valid)
    control_differences = Float64[row.cue_control_difference for row in valid]
    control_success = count(row -> row.cue_control_difference >= 0, valid)
    control_rate = isempty(valid) ? 0.0 : control_success / length(valid)
    control_pass = !isempty(valid) && mean(control_differences) >= 0
    budget_pass = invalid / length(rows) <= 0.10
    criteria = [
        criterion("episodic-configural root advantage", mean(differences),
            mean_ci(differences),
            "greater in ≥ 0.70 of valid pairs and mean difference ≥ 0.10",
            primary_pass; details = Dict(
                "paired_greater_rate" => greater_rate,
                "paired_greater_interval_95" =>
                    wilson_interval(greater, length(valid)))),
        criterion("untreated-cue transfer follows root revision",
            transfer_rate, wilson_interval(transfer_success, length(valid)),
            "transfer present where root revised and absent where not",
            transfer_rate == 1.0; details = Dict(
                "configural_root_revised_rate" =>
                    configural_revised / length(valid),
                "configural_root_revised_interval_95" =>
                    wilson_interval(configural_revised, length(valid)),
                "configural_transfer_present_rate" =>
                    configural_transfer_present / length(valid),
                "configural_transfer_present_interval_95" =>
                    wilson_interval(configural_transfer_present, length(valid)),
                "cue_root_revised_rate" => cue_revised / length(valid),
                "cue_root_revised_interval_95" =>
                    wilson_interval(cue_revised, length(valid)),
                "cue_transfer_present_rate" =>
                    cue_transfer_present / length(valid),
                "cue_transfer_present_interval_95" =>
                    wilson_interval(cue_transfer_present, length(valid)))),
        criterion("cue-level treated-cue endpoint", mean(control_differences),
            mean_ci(control_differences),
            "cue-level treated-cue revision at least configural",
            control_pass; details = Dict(
                "world_rate" => control_rate,
                "world_rate_interval_95" =>
                    wilson_interval(control_success, length(valid)))),
        criterion("corrective evidence budget audit",
            invalid / length(rows),
            wilson_interval(invalid, length(rows)),
            "per-world mismatch ≤ 0.01 and invalid worlds ≤ 0.10",
            budget_pass; details = Dict("invalid_worlds" => invalid)),
    ]
    descriptive = Dict(
        "paired_worlds" => length(rows),
        "valid_worlds" => length(valid),
        "freeze_write_rate" =>
            mean(Float64[row.freeze_written for row in rows]),
        "freeze_write_interval_95" => wilson_interval(
            count(row -> row.freeze_written, rows), length(rows)),
        "configural_root_revision_mean" =>
            mean(Float64[row.configural_root_revision for row in rows]),
        "configural_root_revision_interval_95" =>
            mean_ci(Float64[row.configural_root_revision for row in rows]),
        "cue_root_revision_mean" =>
            mean(Float64[row.cue_root_revision for row in rows]),
        "cue_root_revision_interval_95" =>
            mean_ci(Float64[row.cue_root_revision for row in rows]),
    )
    return rows, criteria, descriptive
end

function calibration_score(predictions, targets)
    return 1 - mean(abs.(predictions .- targets))
end

function policy_vector(state, genome)
    return Float64[expected_cost(state, policy, genome)
        for policy in ModelOrganism.POLICY_NAMES]
end

function e5_regime(dominance, depth)
    high_dominance = dominance >= 0.5
    high_depth = depth >= 0.5
    return high_dominance ?
        (high_depth ? :known_urgent_threat : :blended_capture) :
        (high_depth ? :self_led_witnessing : :quiet_narrowing)
end

function run_e5_world(seed, genome)
    rng = ModelOrganism.field_rng(seed, genome)
    self_global = ModelOrganism.seeded_state(seed, genome;
        favorable_policy = :oscillation)
    full_global = deepcopy(self_global)
    self_local = neutral_state(genome)
    full_local = neutral_state(genome)
    self_initial_root = self_global.posterior[:root_now]
    full_initial_root = full_global.posterior[:root_now]
    self_initial_policy = policy_vector(self_global, genome)
    full_initial_policy = policy_vector(full_global, genome)
    self_predictions = Float64[]
    full_predictions = Float64[]
    targets = Float64[]
    episodes = Int(ModelOrganism.g(genome, :episodes))
    evidence = rand(rng, episodes) .<
        ModelOrganism.g(genome, :bayes_reliability)
    for episode in 1:episodes
        errors = Dict(channel => abs(randn(rng))
            for channel in ModelOrganism.FIELD_CHANNELS)
        part_only = Dict(:part => errors[:part])
        ModelOrganism.update_precision_field!(
            self_local, part_only, false, genome)
        ModelOrganism.update_precision_field!(
            full_local, part_only, false, genome)
        push!(self_predictions, self_local.field[:part])
        push!(full_predictions, full_local.field[:part])
        push!(targets, exp(-errors[:part]))
        ModelOrganism.update_precision_field!(
            full_global, errors, true, genome)
        observation = evidence[episode]
        ModelOrganism.update_root!(self_global, observation, 0.0, genome;
            event_id = "E5:self:$seed:$episode:root")
        ModelOrganism.update_root!(full_global, observation,
            full_global.field[:relational], genome;
            event_id = "E5:full:$seed:$episode:root")
        policy = :oscillation
        ModelOrganism.update_policy_belief!(full_global, policy,
            observation ?
                ModelOrganism.g(genome, :history_favorable_cost) :
                ModelOrganism.g(genome, :history_unfavorable_cost),
            observation, genome;
            event_id = "E5:full:$seed:$episode:policy")
    end
    self_calibration = calibration_score(self_predictions, targets)
    full_calibration = calibration_score(full_predictions, targets)
    self_global_confidence = mean(values(self_global.field))
    full_global_confidence = mean(values(full_global.field))
    self_dominance = self_local.field[:part] /
        (self_local.field[:part] + self_global_confidence)
    full_dominance = full_local.field[:part] /
        (full_local.field[:part] + full_global_confidence)
    self_depth = 0.0
    full_depth = 1.0
    self_regime = e5_regime(self_dominance, self_depth)
    full_regime = e5_regime(full_dominance, full_depth)
    self_policy_change = mean(abs.(
        policy_vector(self_global, genome) .- self_initial_policy))
    full_policy_change = mean(abs.(
        policy_vector(full_global, genome) .- full_initial_policy))
    self_root_revision =
        self_global.posterior[:root_now] - self_initial_root
    full_root_revision =
        full_global.posterior[:root_now] - full_initial_root
    return (seed = seed,
        self_local_calibration = self_calibration,
        full_local_calibration = full_calibration,
        local_calibration_ratio = self_calibration / full_calibration,
        self_local_confidence = mean(self_predictions),
        full_local_confidence = mean(full_predictions),
        self_dominance = self_dominance,
        full_dominance = full_dominance,
        self_depth = self_depth,
        full_depth = full_depth,
        self_regime = self_regime,
        full_regime = full_regime,
        self_not_context_held =
            self_regime != :self_led_witnessing,
        global_separated = full_depth > self_depth &&
            self_regime != :self_led_witnessing,
        self_policy_change = self_policy_change,
        full_policy_change = full_policy_change,
        policy_change_advantage =
            full_policy_change - self_policy_change,
        self_root_revision = self_root_revision,
        full_root_revision = full_root_revision,
        root_revision_advantage =
            full_root_revision - self_root_revision,
        self_root_lower = self_root_revision < full_root_revision)
end

function run_e5(genome)
    error("E5 scientific execution disabled by apparatus erratum C-002: " *
        "no endogenous local-forecast broadcast/depth path")
    validate_config!("E5")
    rows = [run_e5_world(seed, genome) for seed in released_seeds("E5")]
    ratios = Float64[row.local_calibration_ratio for row in rows]
    fluency_success = count(ratio -> ratio >= 0.90, ratios)
    fluency_rate = fluency_success / length(rows)
    fluency_pass = mean(Float64[row.self_local_calibration for row in rows]) >=
        0.90 * mean(Float64[row.full_local_calibration for row in rows])
    separated = count(row -> row.global_separated, rows)
    separation_rate = separated / length(rows)
    separation_pass = separation_rate >= 0.80
    policy_advantage = Float64[row.policy_change_advantage for row in rows]
    root_advantage = Float64[row.root_revision_advantage for row in rows]
    lower = count(row -> row.self_root_lower, rows)
    lower_rate = lower / length(rows)
    agenda_pass = mean_ci(policy_advantage)[1] > 0 &&
        lower_rate >= 0.70
    criteria = [
        criterion("local fluency", mean(ratios), mean_ci(ratios),
            "self-like local calibration within 10% of full agent",
            fluency_pass; details = Dict(
                "within_10_percent_rate" => fluency_rate,
                "rate_interval_95" =>
                    wilson_interval(fluency_success, length(rows)))),
        criterion("global dissociation", separation_rate,
            wilson_interval(separated, length(rows)),
            "global measures separate in ≥ 0.80 and self-like is not context-held witnessing",
            separation_pass; details = Dict(
                "mean_self_depth" =>
                    mean(Float64[row.self_depth for row in rows]),
                "mean_full_depth" =>
                    mean(Float64[row.full_depth for row in rows]))),
        criterion("agenda intactness", mean(policy_advantage),
            mean_ci(policy_advantage),
            "policy-change advantage 95% interval above zero and self-like root revision lower in ≥ 0.70",
            agenda_pass; details = Dict(
                "root_revision_advantage_mean" => mean(root_advantage),
                "root_revision_advantage_interval_95" =>
                    mean_ci(root_advantage),
                "self_root_lower_rate" => lower_rate,
                "self_root_lower_interval_95" =>
                    wilson_interval(lower, length(rows)))),
    ]
    descriptive = Dict(
        "paired_worlds" => length(rows),
        "mean_self_local_confidence" =>
            mean(Float64[row.self_local_confidence for row in rows]),
        "self_local_confidence_interval_95" =>
            mean_ci(Float64[row.self_local_confidence for row in rows]),
        "mean_full_local_confidence" =>
            mean(Float64[row.full_local_confidence for row in rows]),
        "full_local_confidence_interval_95" =>
            mean_ci(Float64[row.full_local_confidence for row in rows]),
        "self_context_held_classifications" =>
            count(row -> row.self_regime == :self_led_witnessing, rows),
        "self_context_held_rate_interval_95" => wilson_interval(
            count(row -> row.self_regime == :self_led_witnessing, rows),
            length(rows)),
        "full_context_held_classifications" =>
            count(row -> row.full_regime == :self_led_witnessing, rows),
        "full_context_held_rate_interval_95" => wilson_interval(
            count(row -> row.full_regime == :self_led_witnessing, rows),
            length(rows)),
    )
    return rows, criteria, descriptive
end

function fmt(value)
    value === nothing && return "NA"
    value isa Number || return string(value)
    return @sprintf("%.6f", Float64(value))
end

function write_challenge_report(challenge, summary)
    directory = joinpath(challenge_root(), challenge)
    path = joinpath(directory, "report.md")
    protocol = PROTOCOL_FILE[challenge]
    interpretation = read(joinpath(directory, "interpretation-lock.md"), String)
    open(path, "w") do io
        println(io, "# $challenge prospective challenge report\n")
        println(io, "Status: **50-P prospective challenge complete**. Protocol: `sealed-revealed/$protocol`. The organism identity is the Stage A freeze at `$FREEZE_COMMIT`.\n")
        println(io, "## Pre-run conservative interpretation\n")
        for line in split(interpretation, '\n')
            startswith(line, "# ") && continue
            occursin("Locked before", line) && continue
            println(io, line)
        end
        println(io, "\n## Results\n")
        println(io, "- Released seeds: `$(first(summary["seeds"])):$(last(summary["seeds"]))`")
        println(io, "- Paired worlds: `$(summary["world_count"])`")
        println(io, "- Overall verdict: **$(summary["overall_verdict"] ? "PASS" : "FAIL")**\n")
        println(io, "| Sealed criterion | Effect estimate | 95% interval | Decision rule | Verdict |")
        println(io, "|---|---:|---|---|---|")
        for item in summary["criteria"]
            interval = item["interval_95"]
            interval_text = "[$(fmt(interval[1])), $(fmt(interval[2]))]"
            println(io, "| $(item["label"]) | $(fmt(item["estimate"])) | $interval_text | $(item["decision_rule"]) | **$(item["passed"] ? "PASS" : "FAIL")** |")
        end
        println(io, "\n## Secondary and descriptive outcomes\n")
        for (key, value) in sort(collect(summary["descriptive"]);
                by = first)
            println(io, "- `$(key)`: `$(value)`")
        end
        if challenge == "E3"
            primary = summary["criteria"][1]["details"]
            coupling = summary["criteria"][2]["details"]
            println(io, "\nCompound primary cells:")
            println(io, "\n- Befriend both: `$(primary["befriend_both_rate"])`, 95% interval `$(primary["befriend_both_interval_95"])`.")
            println(io, "- Befriend one: `$(primary["befriend_one_rate"])`, 95% interval `$(primary["befriend_one_interval_95"])`.")
            println(io, "- Befriend none: `$(primary["befriend_none_rate"])`, 95% interval `$(primary["befriend_none_interval_95"])`.")
            println(io, "- Mean opposed-direction effect: `$(coupling["mean_opposed_direction_effect"])`, 95% interval `$(coupling["mean_effect_interval_95"])`.")
        elseif challenge == "E4"
            transfer = summary["criteria"][2]["details"]
            println(io, "\nTransfer decomposition:")
            println(io, "\n- Configural root revised: `$(transfer["configural_root_revised_rate"])`, 95% interval `$(transfer["configural_root_revised_interval_95"])`.")
            println(io, "- Configural untreated transfer present: `$(transfer["configural_transfer_present_rate"])`, 95% interval `$(transfer["configural_transfer_present_interval_95"])`.")
            println(io, "- Cue-level root revised: `$(transfer["cue_root_revised_rate"])`, 95% interval `$(transfer["cue_root_revised_interval_95"])`.")
            println(io, "- Cue-level untreated transfer present: `$(transfer["cue_transfer_present_rate"])`, 95% interval `$(transfer["cue_transfer_present_interval_95"])`.")
        end
        failures = filter(item -> !item["passed"], summary["criteria"])
        println(io, "\n## Pre-committed failure interpretation\n")
        if isempty(failures)
            println(io, "No sealed criterion failed.")
        elseif challenge == "E3"
            primary = summary["criteria"][1]["details"]
            println(io, "The compositional criterion failed because befriend-both descent was only `$(primary["befriend_both_rate"])`; befriend-one and befriend-none produced none and remained within their control ceilings. This is failure to achieve compositional descent, not evidence that one gate carried the conjunction. Both befriend-both descents fail the separate ordering audit: one root endpoint preceded the eventual conjunction, and one tied it. Escalation coupling was absent with exactly zero opposed-direction response, so the strain composes the protectors independently and does not reproduce polarization. Both findings are retained without repair.")
        elseif challenge == "E4"
            println(io, "The primary format claim did not fail: configural correction exceeded cue-level root revision in every paired world and cleared the mean margin. The secondary transfer-gradient criterion failed because untreated transfer crossed its margin in configural worlds whose root endpoint had not crossed `root_revision_begin`. The cue-level arm had zero root change and zero transfer, although 3/60 worlds began and remained above the frozen endpoint threshold. Thus the root/transfer threshold concordance did not reproduce exactly, and that narrower failure is retained.")
        else
            println(io, "Indistinguishable global measures would mean the paper's self-like-part description has no computational face in this architecture. Any such result is retained as a scope limit.")
        end
    end
    return path
end

function run_challenge(challenge, genome)
    challenge == "E3" ||
        error("$challenge is not scientifically executable; see apparatus erratum C-002")
    rows, criteria, descriptive = run_e3(genome)
    directory = joinpath(challenge_root(), challenge)
    mkpath(directory)
    csv_path = joinpath(directory, "per_seed.csv")
    ModelOrganism.write_csv_file(csv_path, rows)
    protocol_path = joinpath(revealed_root(), PROTOCOL_FILE[challenge])
    config_path = joinpath(config_root(), CONFIG_FILE[challenge])
    lock_path = joinpath(directory, "interpretation-lock.md")
    summary = Dict(
        "challenge" => challenge,
        "stage" => "50-P prospective",
        "freeze_commit" => FREEZE_COMMIT,
        "stage_b_commit" => STAGE_B_COMMIT,
        "reveal_commit" => REVEAL_COMMIT,
        "world_count" => WORLD_COUNT[challenge],
        "seeds" => released_seeds(challenge),
        "criteria" => criteria,
        "overall_verdict" => all(item["passed"] for item in criteria),
        "challenge_verdict" =>
            all(item["passed"] for item in criteria) ? "PASS" : "FAIL",
        "scientific_criteria_evaluated" => true,
        "prospection_failure" => false,
        "descriptive" => descriptive,
        "genome_sha256" => genome.sha256,
        "canonical_source_sha256" => ModelOrganism.canonical_source_hash(),
        "protocol_sha256" => bytes2hex(sha256(read(protocol_path))),
        "configuration_sha256" => bytes2hex(sha256(read(config_path))),
        "interpretation_lock_sha256" => bytes2hex(sha256(read(lock_path))),
        "per_seed_sha256" => bytes2hex(sha256(read(csv_path))),
        "maximum_seed_used" => last(released_seeds(challenge)),
        "l_neighborhood_opened" => false,
    )
    ModelOrganism.write_json_file(joinpath(directory, "summary.json"), summary)
    write_challenge_report(challenge, summary)
    return summary
end

function write_prospection_failure(challenge, reason, finding, genome)
    validate_config!(challenge)
    directory = joinpath(challenge_root(), challenge)
    mkpath(directory)
    invalid_path = joinpath(directory, "invalid-apparatus-per_seed.csv")
    current_path = joinpath(directory, "per_seed.csv")
    if isfile(current_path) && !isfile(invalid_path)
        cp(current_path, invalid_path)
    end
    rows = [(seed = seed, status = :not_evaluable,
        prospection_failure = true, organism_changed = false,
        reason_code = challenge == "E4" ?
            :no_common_likelihood_path :
            :no_endogenous_broadcast_depth_path)
        for seed in released_seeds(challenge)]
    ModelOrganism.write_csv_file(current_path, rows)
    protocol_path = joinpath(revealed_root(), PROTOCOL_FILE[challenge])
    config_path = joinpath(config_root(), CONFIG_FILE[challenge])
    lock_path = joinpath(directory, "interpretation-lock.md")
    summary = Dict(
        "challenge" => challenge,
        "stage" => "50-P prospective",
        "freeze_commit" => FREEZE_COMMIT,
        "stage_b_commit" => STAGE_B_COMMIT,
        "reveal_commit" => REVEAL_COMMIT,
        "world_count" => WORLD_COUNT[challenge],
        "seeds" => released_seeds(challenge),
        "criteria" => Any[],
        "overall_verdict" => nothing,
        "challenge_verdict" => "PROSPECTION FAILURE",
        "scientific_criteria_evaluated" => false,
        "prospection_failure" => true,
        "apparatus_first_reason" => reason,
        "protocol_defined_finding" => finding,
        "genome_sha256" => genome.sha256,
        "canonical_source_sha256" => ModelOrganism.canonical_source_hash(),
        "protocol_sha256" => bytes2hex(sha256(read(protocol_path))),
        "configuration_sha256" => bytes2hex(sha256(read(config_path))),
        "interpretation_lock_sha256" => bytes2hex(sha256(read(lock_path))),
        "per_seed_sha256" => bytes2hex(sha256(read(current_path))),
        "invalid_apparatus_trace_sha256" =>
            bytes2hex(sha256(read(invalid_path))),
        "maximum_seed_opened" => last(released_seeds(challenge)),
        "l_neighborhood_opened" => false,
    )
    ModelOrganism.write_json_file(joinpath(directory, "summary.json"), summary)
    open(joinpath(directory, "report.md"), "w") do io
        println(io, "# $challenge prospective challenge report\n")
        println(io, "Status: **PROSPECTION FAILURE — SCIENTIFIC CRITERIA NOT EVALUATED**. Protocol: `sealed-revealed/$(PROTOCOL_FILE[challenge])`.\n")
        println(io, "## Apparatus-first stop\n")
        println(io, reason, "\n")
        println(io, "The frozen grammar configuration parses, but the required causal measurement cannot be executed through the frozen organism without adding semantics or an equation. Rule 2 therefore stops this protocol; no runner-authored substitute is scored.\n")
        println(io, "## Protocol-defined finding\n")
        println(io, finding, "\n")
        println(io, "## Seed and trace handling\n")
        println(io, "- Released block opened during the invalid apparatus attempt: `$(first(summary["seeds"])):$(last(summary["seeds"]))`.")
        println(io, "- `per_seed.csv` records the non-evaluable status for all planned units.")
        println(io, "- The invalid initial runner trace is retained separately as `invalid-apparatus-per_seed.csv`; it is not evidence and no effect estimate or interval is reported from it.")
        println(io, "- Organism, genome, grammar, frozen configurations, generators, and frozen analysis code remained unchanged.")
    end
    return summary
end

function stage_c_table(io, summaries)
    println(io, "| Challenge | Criterion | Estimate | 95% interval | Verdict |")
    println(io, "|---|---|---:|---|---|")
    for challenge in CHALLENGES
        for item in summaries[challenge]["criteria"]
            interval = item["interval_95"]
            println(io, "| $challenge | $(item["label"]) | $(fmt(item["estimate"])) | [$(fmt(interval[1])), $(fmt(interval[2]))] | **$(item["passed"] ? "PASS" : "FAIL")** |")
        end
    end
end

function write_stage_c_report(summaries, genome)
    path = joinpath(ModelOrganism.RESULTS_ROOT, "stage-c-report.md")
    open(path, "w") do io
        println(io, "# Experiment 50-P prospective challenge report\n")
        println(io, "The three evaluator-sealed protocols were revealed at commit `$REVEAL_COMMIT` after the strain freeze (`$FREEZE_COMMIT`) and Stage B (`$STAGE_B_COMMIT`). E3 was scientifically evaluable. E4 and E5 stopped apparatus-first because their required measurements cannot be supplied by the frozen organism interface without new semantics; their initial invalid runner traces are quarantined and unscored.\n")
        println(io, "## Challenge-level verdicts\n")
        println(io, "| Challenge | Verdict | Interpretation |")
        println(io, "|---|---|---|")
        println(io, "| E3 | **FAIL** | Compositional descent and escalation coupling failed. |")
        println(io, "| E4 | **PROSPECTION FAILURE** | No common likelihood-accounted configural/cue evidence path; scientific criteria not evaluated. |")
        println(io, "| E5 | **PROSPECTION FAILURE** | No endogenous local-forecast broadcast/depth readout; computational-face scope limit. |")
        println(io, "## Verdicts by prospective criterion\n")
        stage_c_table(io, summaries)
        println(io, "\nE4 and E5 have no criterion rows because their scientific criteria were not evaluated.")
        println(io, "\nThis is an out-of-sample prospective class, not a retrospective assay-count extension. Every failed criterion and its protocol-defined interpretation is retained in its challenge report.\n")
        println(io, "## Integrity\n")
        println(io, "- Canonical source SHA-256: `$(ModelOrganism.canonical_source_hash())`")
        println(io, "- Genome SHA-256: `$(genome.sha256)`")
        println(io, "- Maximum seed used: `$(maximum(last(summary["seeds"]) for summary in values(summaries)))`")
        println(io, "- L-neighborhood seeds opened: **no**")
        println(io, "- 50-L begun: **no**")
        println(io, "- Apparatus errata: `stage-c-errata.md` (C-001 corrected two E3 endpoint classifications; C-002 quarantined invalid E4/E5 traces)")
    end
    return path
end

function append_prospective_profile!(summaries)
    path = joinpath(ModelOrganism.RESULTS_ROOT, "profile.md")
    raw = read(path, String)
    marker = "\n## Prospective challenge battery (50-P)\n"
    if occursin(marker, raw)
        raw = first(split(raw, marker; limit = 2))
    end
    raw = replace(raw,
        "No 50-P or 50-L seed or protocol was opened." =>
        "At the close of Stage B, no 50-P or 50-L seed or protocol had been opened; Stage C results are reported separately below.")
    io = IOBuffer()
    print(io, raw)
    println(io, marker)
    println(io, "These results are from evaluator-sealed, out-of-sample protocols revealed only after the organism and 50-H results were committed. They are reported separately from historical conformance, causal-contrast, and model-discrimination evidence.\n")
    println(io, "| Challenge | Challenge-level verdict |")
    println(io, "|---|---|")
    println(io, "| E3 | **FAIL** |")
    println(io, "| E4 | **PROSPECTION FAILURE — not scientifically evaluated** |")
    println(io, "| E5 | **PROSPECTION FAILURE — not scientifically evaluated** |\n")
    stage_c_table(io, summaries)
    println(io, "\nE4 and E5 are absent from the criterion table because the frozen organism could not execute their required measurements without new semantics. Their invalid apparatus traces are retained but unscored.")
    failures = [(challenge, item["label"]) for challenge in CHALLENGES
        for item in summaries[challenge]["criteria"] if !item["passed"]]
    println(io, "\nProspective failures retained:")
    if isempty(failures)
        println(io, "\n- None.")
    else
        for (challenge, label) in failures
            println(io, "\n- $challenge — $label.")
        end
    end
    println(io, "\n- E4 — prospection failure; scientific criteria not evaluated.")
    println(io, "\n- E5 — prospection failure; scientific criteria not evaluated.")
    write(path, String(take!(io)))
end

function main()
    genome = load_genome()
    verify_stage_c_inputs!(genome)
    summaries = Dict{String,Any}()
    verify_stage_c_inputs!(genome)
    summaries["E3"] = run_challenge("E3", genome)
    println("E3 complete: ",
        summaries["E3"]["overall_verdict"] ? "PASS" : "FAIL")
    verify_stage_c_inputs!(genome)
    summaries["E4"] = write_prospection_failure("E4",
        "The protocol requires matched total corrective log-likelihood across episodic-configural and isolated cue updates. The frozen root path exposes a logit update, while the frozen cue path is an assay-local additive cue step with no likelihood contribution or provenance record. A common delivered-likelihood audit would therefore require a new evidence equation or analysis semantic.",
        "The evidence-format challenge is not prospectively testable in this frozen architecture; the primary, transfer, control, and budget criteria receive no scientific verdict.",
        genome)
    println("E4 complete: PROSPECTION FAILURE")
    verify_stage_c_inputs!(genome)
    summaries["E5"] = write_prospection_failure("E5",
        "The grammar names local monitoring and recursive broadcast, but the frozen canonical state has no part-local forecast coordinate, no operation that broadcasts that forecast into q(Φ), and no endogenous assay-3 depth readout. Assigning depth from the arm label or updating an unrelated global error field would author the result in the runner.",
        "The paper's self-like-part description has no computational face in this frozen architecture; this is the protocol's anticipated scope-limit finding.",
        genome)
    println("E5 complete: PROSPECTION FAILURE")
    write_stage_c_report(summaries, genome)
    append_prospective_profile!(summaries)
    verify_stage_c_inputs!(genome)
    println("Stage C complete; maximum seed used = ",
        maximum(last(summary["seeds"]) for summary in values(summaries)))
end

main()
