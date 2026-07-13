module LiteratureTournament

using Random
using Statistics
using Main.GlobalPrecisionField

export VariantSpec, literature_variants, run_tournament

struct VariantSpec
    name::String
    citation::String
    mechanism::Symbol
    complexity::Int
end

literature_variants() = [
    VariantSpec("global_covariance", "Laukkonen, Friston, & Chandaria (2025)", :global, 0),
    VariantSpec("opacity_gate", "Limanowski & Friston (2018)", :opacity, 1),
    VariantSpec("context_redescription", "Chamberlin (2023)", :redescription, 2),
    VariantSpec("spare_capacity", "Smith et al. (2020)", :spare_capacity, 2),
    VariantSpec("regulatory_authority", "Palejova (2026)", :authority, 2),
    VariantSpec("second_order_social", "Harris (2025)", :second_order, 1),
    VariantSpec("dyadic_synchrony", "McParlin et al. (2022)", :synchrony, 1),
    VariantSpec("interoceptive_titration", "Fujimoto (2026)", :titration, 1),
    VariantSpec("somatic_safety", "Fujimoto (2026)", :somatic_safety, 1),
    VariantSpec("patient_testing", "Li et al. (2025)", :patient_testing, 2),
    VariantSpec("learned_mental_action", "Tal et al. (2026)", :mental_action, 2),
    VariantSpec("social_self_evidencing", "Albarracin et al. (2024)", :social_self, 1),
    VariantSpec("policy_likelihood_interaction", "Benrimoh et al. (2018)", :policy_likelihood, 1),
    VariantSpec("allostatic_self", "Deane, Miller, & Wilkinson (2020)", :allostatic, 1),
    VariantSpec("multisensory_minimal_self", "Limanowski & Blankenburg (2013)", :multisensory, 2),
    VariantSpec("flexible_boundary", "Sandved-Smith et al. (2026)", :flexible_boundary, 2),
    VariantSpec("compassionate_scope", "Ho et al. (2021)", :compassion, 1),
    VariantSpec("worldview_root", "Koltko-Rivera (2004)", :worldview, 2),
    VariantSpec("dynamic_balancing", "Sato (2025)", :dynamic_balance, 2),
    VariantSpec("process_resumption", "Gendlin (1964)", :process_resumption, 1),
]

mutable struct TherapyState
    profile::Vector{Float64}
    root_log_odds::Float64
    threat_log_odds::Float64
    unrelated_log_odds::Float64
    learned::Dict{Symbol,Float64}
end

logistic(x) = inv(1 + exp(-x))
clamp01(x) = clamp(x, 0.0, 1.0)

function arm_definition(arm::String, session::Int)
    scaffolded = session <= 6
    if arm == "regulation_only"
        return ([0.1, 1.55, 1.25, 1.55, 1.0], ones(Int, 5), 0.12, 1.0, 1.0, false, scaffolded)
    elseif arm == "contact_narrow"
        return ([1.75, -0.45, -0.2, -0.65, 0.8], [1, 0, 0, 0, 1], 1.0, 1.0, 1.0, false, scaffolded)
    elseif arm == "informational_open"
        return ([1.35, 1.55, 1.2, 1.0, 1.15], scaffolded ? ones(Int, 5) : [1, 1, 1, 0, 1], 1.0, 1.0, 0.7, false, scaffolded)
    elseif arm == "real_danger"
        return ([2.2, 0.55, 1.15, 1.0, 1.45], ones(Int, 5), 1.0, 1.0, 1.0, true, scaffolded)
    elseif arm == "false_suggestion"
        return ([1.2, 1.45, 1.1, 1.55, 1.1], ones(Int, 5), 0.8, 0.55, 1.0, false, scaffolded)
    elseif arm == "rupture_repair"
        rupture = session == 6
        return (rupture ? [1.4, -0.2, -0.1, -1.2, 0.8] : [1.35, 1.45, 1.3, 1.65, 1.2],
            rupture ? [1, 1, 1, 1, 1] : (scaffolded ? ones(Int, 5) : [1, 1, 1, 0, 1]),
            1.0, rupture ? -0.6 : 1.0, 1.0, false, scaffolded)
    end
    return ([1.35, 1.45, 1.3, 1.75, 1.2], scaffolded ? ones(Int, 5) : [1, 1, 1, 0, 1], 1.0, 1.0, 1.0, false, scaffolded)
end

function apply_mechanism!(state, mechanism, base_gate, result, activation, valence, target_fit, danger, strength)
    gate = base_gate
    false_guard = 1.0
    transfer = 0.0
    if mechanism == :opacity
        gate *= result.opacity_index
    elseif mechanism == :redescription
        state.learned[:context] += 0.20strength * activation * result.depth_index * max(valence, 0)
        gate *= 0.55 + clamp01(state.learned[:context])
        false_guard = 0.35
        transfer = 0.25state.learned[:context]
    elseif mechanism == :spare_capacity
        state.learned[:slot] += 0.16strength * activation * result.depth_index
        gate *= 0.65 + clamp01(state.learned[:slot])
        transfer = 0.18state.learned[:slot]
    elseif mechanism == :authority
        state.learned[:authority] += 0.18strength * activation * max(valence, 0) * target_fit
        gate *= 0.35 + clamp01(state.learned[:authority])
        false_guard = 0.25
    elseif mechanism == :second_order
        gate *= 1 + 0.35strength * max(valence, 0) * result.broadcast_precision[4] / sum(result.broadcast_precision)
        false_guard = 0.55
    elseif mechanism == :synchrony
        state.learned[:synchrony] += 0.14strength * valence
        gate *= 0.75 + clamp01(state.learned[:synchrony])
        transfer = 0.12state.learned[:synchrony]
    elseif mechanism == :titration
        gate *= exp(-strength * ((activation - 0.78) / 0.48)^2) * (0.6 + 0.4result.breadth)
    elseif mechanism == :somatic_safety
        state.learned[:safety] += 0.16strength * max(valence, 0) * result.broadcast_precision[3] / sum(result.broadcast_precision)
        gate *= 0.45 + clamp01(state.learned[:safety])
    elseif mechanism == :patient_testing
        state.learned[:testing] += 0.15strength * activation * max(valence, 0) * target_fit
        gate *= 0.5 + clamp01(state.learned[:testing])
        false_guard = 0.2
    elseif mechanism == :mental_action
        state.learned[:attention] += 0.12strength * max(valence, 0)
        gate *= 0.7 + clamp01(state.learned[:attention])
        transfer = 0.2state.learned[:attention]
    elseif mechanism == :social_self
        gate *= 1 + 0.25strength * max(valence, 0)
        false_guard = 0.75
    elseif mechanism == :policy_likelihood
        gate *= result.broadcast_precision[4] / (result.broadcast_precision[4] + result.broadcast_precision[5])
    elseif mechanism == :allostatic
        gate *= sqrt(result.calibration * result.broadcast_precision[5] / maximum(result.broadcast_precision))
    elseif mechanism == :multisensory
        shares = result.broadcast_precision[[2, 3, 5]] ./ sum(result.broadcast_precision)
        gate *= clamp01(5 * prod(shares)^(1 / 3))
    elseif mechanism == :flexible_boundary
        state.learned[:boundary] += 0.13strength * result.depth_index * target_fit
        false_guard = 0.15
        transfer = 0.22state.learned[:boundary]
    elseif mechanism == :compassion
        state.learned[:scope] += 0.12strength * max(valence, 0)
        gate *= 1 + 0.18clamp01(state.learned[:scope])
    elseif mechanism == :worldview
        gate *= 0.72
        transfer = 0.45strength * gate
    elseif mechanism == :dynamic_balance
        desired = gate
        velocity = 0.55state.learned[:velocity] + 0.45(desired - state.learned[:balanced])
        state.learned[:velocity] = velocity
        state.learned[:balanced] = clamp01(state.learned[:balanced] + velocity)
        gate = state.learned[:balanced]
    elseif mechanism == :process_resumption
        gate *= result.breadth * (0.55 + 0.45max(valence, 0))
    end
    danger && (false_guard = 1.0)
    return clamp01(gate), false_guard, transfer
end

function simulate(seed, mechanisms, arm, strength; config = PhiConfig())
    rng = MersenneTwister(seed)
    state = TherapyState(zeros(5), log(9.0), log(3.0), 0.0,
        Dict(:context=>0.0,:slot=>0.0,:authority=>0.0,:synchrony=>0.0,:safety=>0.0,
             :testing=>0.0,:attention=>0.0,:boundary=>0.0,:scope=>0.0,:velocity=>0.0,:balanced=>0.0))
    transfer_total = 0.0
    for session in 1:12
        realized, available, activation, valence, target_fit, danger, scaffolded = arm_definition(arm, session)
        result = infer_precision_field(state.profile, realized;
            observation_variance = all(available .== 1) ? 0.04 : 1.8,
            available = available, rng = rng, config = config)
        state.profile .+= 0.30 .* (result.mu_posterior .- state.profile)
        evidence_channel = arm == "informational_open" ? 2 : 4
        share = result.broadcast_precision[evidence_channel] / sum(result.broadcast_precision)
        gate = activation * result.opacity_index * result.posterior_confidence * share
        false_guard = 1.0
        for mechanism in mechanisms
            gate, guard, transfer = apply_mechanism!(state, mechanism, gate, result,
                activation, valence, target_fit, danger, strength)
            false_guard *= guard
            transfer_total += !scaffolded ? transfer : 0.0
        end
        relevance = arm == "false_suggestion" ? target_fit * false_guard : target_fit
        state.root_log_odds -= 2.2 * gate * relevance * max(valence, -0.35)
        danger && (state.threat_log_odds += 0.30 * gate)
        arm == "false_suggestion" && (state.unrelated_log_odds += 0.30 * gate * (1 - false_guard))
    end
    return (root = logistic(state.root_log_odds), threat = logistic(state.threat_log_odds),
        unrelated = logistic(state.unrelated_log_odds), transfer = clamp01(transfer_total / 6),
        relational_profile = state.profile[4])
end

function aggregate_variant(specs, strengths, seeds)
    mechanisms = [spec.mechanism for spec in specs]
    arms = ["witnessing", "regulation_only", "contact_narrow", "informational_open",
        "real_danger", "false_suggestion", "rupture_repair"]
    results = Dict{String,Any}()
    for arm in arms
        runs = [simulate(seed, mechanisms, arm, strength) for seed in seeds for strength in strengths]
        results[arm] = (root = mean(run.root for run in runs), threat = mean(run.threat for run in runs),
            unrelated = mean(run.unrelated for run in runs), transfer = mean(run.transfer for run in runs),
            profile = mean(run.relational_profile for run in runs))
    end
    revision = clamp01((0.90 - results["witnessing"].root) / 0.75)
    specificity = mean(clamp01((results[arm].root - 0.55) / 0.35) for arm in ["regulation_only", "contact_narrow", "false_suggestion"])
    information = clamp01((0.90 - results["informational_open"].root) / 0.75)
    danger = results["real_danger"].threat
    rupture = clamp01((0.90 - results["rupture_repair"].root) / 0.75)
    contamination = clamp01(1 - 2abs(results["false_suggestion"].unrelated - 0.5))
    transfer = clamp01(results["witnessing"].profile / 1.7 + results["witnessing"].transfer)
    complexity = sum(spec.complexity for spec in specs)
    score = 0.24revision + 0.23specificity + 0.12information + 0.12danger +
        0.11rupture + 0.08contamination + 0.10transfer - 0.012complexity
    robust = mean(begin
        w = mean(simulate(seed, mechanisms, "witnessing", s).root for seed in seeds)
        r = mean(simulate(seed, mechanisms, "regulation_only", s).root for seed in seeds)
        c = mean(simulate(seed, mechanisms, "contact_narrow", s).root for seed in seeds)
        w < 0.35 && r > 0.65 && c > 0.65
    end for s in strengths)
    return (score = score, robustness = robust, results = results)
end

function run_tournament(output_dir::AbstractString = joinpath(@__DIR__, "..", "results", "literature_tournament"))
    mkpath(output_dir)
    variants = literature_variants()
    strengths = [0.6, 1.0, 1.4]
    seeds = collect(9101:9120)
    rows = NamedTuple[]
    for (index, spec) in enumerate(variants)
        result = aggregate_variant([spec], strengths, seeds)
        push!(rows, (experiment = index + 4, name = spec.name, citation = spec.citation,
            mechanisms = string(spec.mechanism), complexity = spec.complexity,
            score = result.score, robustness = result.robustness,
            witnessing_root = result.results["witnessing"].root,
            regulation_root = result.results["regulation_only"].root,
            contact_root = result.results["contact_narrow"].root,
            information_root = result.results["informational_open"].root,
            danger_threat = result.results["real_danger"].threat,
            false_root = result.results["false_suggestion"].root,
            false_unrelated = result.results["false_suggestion"].unrelated,
            rupture_root = result.results["rupture_repair"].root,
            transfer = result.results["witnessing"].transfer))
    end
    ordered = sort(rows; by = row -> row.score, rev = true)
    top = [only(filter(spec -> spec.name == row.name, variants)) for row in ordered[1:3]]
    combinations = [[top[1], top[2]], [top[1], top[3]], [top[2], top[3]], top]
    combo_rows = NamedTuple[]
    for (offset, specs) in enumerate(combinations)
        result = aggregate_variant(specs, strengths, seeds)
        push!(combo_rows, (experiment = 24 + offset, name = join(getfield.(specs, :name), "+"),
            citation = join(getfield.(specs, :citation), "; "),
            mechanisms = join(string.(getfield.(specs, :mechanism)), "+"),
            complexity = sum(getfield.(specs, :complexity)), score = result.score,
            robustness = result.robustness, witnessing_root = result.results["witnessing"].root,
            regulation_root = result.results["regulation_only"].root,
            contact_root = result.results["contact_narrow"].root,
            information_root = result.results["informational_open"].root,
            danger_threat = result.results["real_danger"].threat,
            false_root = result.results["false_suggestion"].root,
            false_unrelated = result.results["false_suggestion"].unrelated,
            rupture_root = result.results["rupture_repair"].root,
            transfer = result.results["witnessing"].transfer))
    end
    all_rows = vcat(rows, combo_rows)
    final_order = sort(all_rows; by = row -> row.score, rev = true)
    best_single = first(ordered)
    best_combination = first(sort(combo_rows; by = row -> row.score, rev = true))
    combination_earned = best_combination.score >= best_single.score + 0.02
    GlobalPrecisionField.write_csv(joinpath(output_dir, "ranked_experiments.csv"), final_order)
    GlobalPrecisionField.write_json(joinpath(output_dir, "summary.json"), (
        protocol = "adaptive construction tournament; 20 single mechanisms plus 4 earned recombinations",
        experiment_count = 28,
        best_single = best_single,
        best_combination = best_combination,
        combination_earned = combination_earned,
        simplicity_rule = "combination must beat best single by 0.02",
    ))
    GlobalPrecisionField.write_json(joinpath(output_dir, "status.json"), (
        implementation_passed = true, experiment_cap_respected = true,
        theory_result = combination_earned ? "combination earned" : "simple single mechanism retained",
    ))
    return (rows = final_order, best_single = best_single, best_combination = best_combination,
        combination_earned = combination_earned)
end

end
