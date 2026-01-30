"""
    PMC7250191 Reproduction Script

Reproduce key qualitative results from the Concepts_model.m supplement:
- Full-knowledge reporting accuracy
- Granularity-removed (basic-level) accuracy
- Concept acquisition learning curve (A similarity) for a removed concept
- Optional BMR reduction of D

Usage:
  julia --project=. scripts/pmc7250191_reproduce.jl
"""

using Pkg
Pkg.activate(".")

include("../src/active_inference/ActiveInferenceCore.jl")
using .ActiveInferenceCore
using Random
using Statistics
using Plots

println("\nPMC7250191 reproduction (concept learning)...")

Random.seed!(42)

learning_model = build_concepts_model(allow_reports=false)
report_model = build_concepts_model(allow_reports=true)

# -----------------------------------------------------------------------------
# Sanity checks from paper
# -----------------------------------------------------------------------------
println("\n1) Sanity checks (paper ground truth)")

agent_full = init_concepts_agent(report_model)
full_results = evaluate_reporting(agent_full, report_model; trials_per_animal=4, deterministic=true)
println("  Full knowledge acc_specific = $(round(full_results.acc_specific, digits=3))")
println("  Full knowledge acc_basic    = $(round(full_results.acc_basic, digits=3))")

agent_gran = init_concepts_agent(report_model; remove_granularity=true)
gran_results = evaluate_reporting(agent_gran, report_model; trials_per_animal=4, deterministic=true)
println("  Granularity removed acc_basic = $(round(gran_results.acc_basic, digits=3))")
println("  Granularity removed acc_specific = $(round(gran_results.acc_specific, digits=3))")

# -----------------------------------------------------------------------------
# Generalization question (distance)
# -----------------------------------------------------------------------------
println("\n2) Generalization question (distance)")

distance_model = build_distance_model(allow_reports=true)
distance_agent = init_concepts_agent(distance_model)
distance_results = evaluate_distance_reporting(distance_agent, distance_model; trials_per_animal=4, deterministic=true)
println("  Distance question accuracy = $(round(distance_results.acc, digits=3))")

# -----------------------------------------------------------------------------
# Concept acquisition: remove a concept, then learn
# -----------------------------------------------------------------------------
println("\n3) Concept acquisition learning curve")

removed_concepts = [1, 2] # Parakeet + Parrot
agent_learn = init_concepts_agent(learning_model; remove_concepts=removed_concepts)

n_trials = 2000
probe_every = 100
probe_trials = 20

trial_counts = Int[]
acc_specific = Float64[]
similarity = Float64[]

function concept_feature_vector(A, concept_idx)
    v1 = vec(A[1][2:3, concept_idx, 1])
    v2 = vec(A[2][2:3, concept_idx, 1])
    v3 = vec(A[3][2:3, concept_idx, 1])
    return vcat(v1, v2, v3)
end

true_vec = concept_feature_vector(learning_model.A, removed_concepts[1])

function feature_signature(A, concept_idx)
    sig = zeros(Int, 3)
    sig[1] = argmax(A[1][2:3, concept_idx, 1])
    sig[2] = argmax(A[2][2:3, concept_idx, 1])
    sig[3] = argmax(A[3][2:3, concept_idx, 1])
    return sig
end

function build_feature_map(A_learned, A_true)
    true_map = Dict{Tuple{Int,Int,Int}, Int}()
    for i in 1:8
        sig = Tuple(feature_signature(A_true, i))
        true_map[sig] = i
    end
    mapping = Dict{Int, Int}()
    for i in 1:8
        sig = Tuple(feature_signature(A_learned, i))
        mapping[i] = get(true_map, sig, i)
    end
    return mapping
end

for step in 1:probe_every:n_trials
    run_concepts_learning!(
        agent_learn,
        learning_model;
        n_trials=probe_every,
        settings=concepts_settings(eta_A=1.0, eta_D=1.0)
    )

    report_agent = copy_agent_to_model(agent_learn, report_model)
    seq = fill(removed_concepts[1], probe_trials)
    probe = evaluate_reporting(
        report_agent,
        report_model;
        animal_sequence=seq,
        deterministic=true
    )

    push!(trial_counts, step)
    push!(acc_specific, probe.acc_specific)
    learned_A = get_A_from_pA(agent_learn.pA)
    learned_vec = concept_feature_vector(learned_A, removed_concepts[1])
    sim = 1.0 - mean(abs.(learned_vec .- true_vec))
    push!(similarity, sim)
    println("  Trials $(step): acc_specific = $(round(probe.acc_specific, digits=3)), similarity = $(round(sim, digits=3))")
end

mkpath("figures/pmc7250191")
plot(
    trial_counts,
    similarity,
    xlabel="Exposure trials",
    ylabel="A similarity to true concept",
    title="Concept acquisition (removed concept)",
    ylim=(0, 1),
    legend=false,
    linewidth=2
)

savefig("figures/pmc7250191/concept_learning_curve.png")
println("\nSaved: figures/pmc7250191/concept_learning_curve.png")

# -----------------------------------------------------------------------------
# Optional: Bayesian Model Reduction (D)
# -----------------------------------------------------------------------------
println("\n4) BMR reduction (D) demo")
agent_bmr = init_concepts_agent(learning_model)
sequence = vcat([fill(a, 50) for a in 3:8]...)
run_concepts_learning!(agent_bmr, learning_model; n_trials=length(sequence), animal_sequence=sequence)
prior_D = build_concepts_D()[1]
result = apply_bmr_D!(agent_bmr, prior_D)
println("  Best D prior (first 8 entries): $(round.(result.prior; digits=2))")
println("  Free energy = $(round(result.free_energy, digits=3))")

# -----------------------------------------------------------------------------
# Reporting accuracy with feature-aligned labels (permutes columns)
# -----------------------------------------------------------------------------
println("\n5) Reporting accuracy after learning (feature-aligned labels)")
report_agent = copy_agent_to_model(agent_learn, report_model)
mapping = build_feature_map(get_A_from_pA(report_agent.pA), report_model.A)
seq = vcat([fill(a, 20) for a in 1:8]...)
aligned_results = evaluate_reporting(report_agent, report_model; animal_sequence=seq, deterministic=true)
env = ConceptsEnvironment(report_model.A, report_model.B; animal_sequence=seq)
settings = concepts_settings(eta_A=0.0, eta_D=0.0)

let aligned_total = 0, aligned_correct = 0
    for _ in 1:length(seq)
        hist = run_trial!(report_agent, report_model, env, settings; learn_A=Int[], learn_B=Int[], learn_D=Int[], deterministic_actions=true)
        animal_idx = env.current_state[1]
        report_action = hist.actions[1][2]
        if 2 <= report_action <= 9
            reported_concept = report_action - 1
            aligned_concept = mapping[reported_concept]
            aligned_total += 1
            aligned_correct += (aligned_concept == animal_idx) ? 1 : 0
        end
    end

    aligned_acc = aligned_total > 0 ? aligned_correct / aligned_total : 0.0
    println("  Raw acc_specific = $(round(aligned_results.acc_specific, digits=3))")
    println("  Feature-aligned acc_specific = $(round(aligned_acc, digits=3))")
end

println("\nDone.")
