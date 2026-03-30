"""
    ifs_simulation_v4.jl - Hierarchical Relational Gating Simulation (v9 spec)

Usage:
    julia projects/library/scripts/ifs_simulation_v4.jl

Environment flags:
    IFS_V4_SKIP_FIGURES=1   Run numeric verification only (no Plots dependency)
    IFS_V4_N_REPS=50        Replications per condition
"""

using Pkg
Pkg.activate(joinpath(@__DIR__, ".."))

# Load model inside a module to avoid polluting Main
module IFSV4
    using Random, Statistics
    include(joinpath(@__DIR__, "..", "src", "active_inference", "ifs_model_v4.jl"))
end

using .IFSV4
using Random, Statistics

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
const ENABLE_FIGURES = get(ENV, "IFS_V4_SKIP_FIGURES", "0") != "1"
const N_REPS = parse(Int, get(ENV, "IFS_V4_N_REPS", "50"))
const FIGURE_DIR = joinpath(@__DIR__, "..", "..", "ifs-paper", "figures", "v4")
mkpath(FIGURE_DIR)

if ENABLE_FIGURES
    ENV["GKSwstype"] = get(ENV, "GKSwstype", "100")
    ENV["GKS_NO_GUI"] = get(ENV, "GKS_NO_GUI", "1")
    using Plots
    default(
        fontfamily="Georgia", titlefontsize=11, guidefontsize=10,
        tickfontsize=8, legendfontsize=8, linewidth=2.0, framestyle=:semi,
        grid=false, background_color=RGB(1.0,1.0,0.973), dpi=300, size=(900,700)
    )
    const COL_WITNESS  = RGB(0.20, 0.47, 0.72)
    const COL_RELONLY  = RGB(0.90, 0.55, 0.20)
    const COL_INFOONLY = RGB(0.30, 0.68, 0.35)
    const COL_ABLATION = RGB(0.82, 0.22, 0.22)
end

# ---------------------------------------------------------------------------
# Run all conditions
# ---------------------------------------------------------------------------
println("=" ^ 60)
println("IFS v4 Simulation: Hierarchical Relational Gating")
println("Replications per condition: $N_REPS")
println("=" ^ 60)

params = IFSV4.V4Params()
model = IFSV4.build_v4_model(params)

# Build configs
config_info    = IFSV4.informational_only_config()
config_rel     = IFSV4.relational_only_config()
config_wit     = IFSV4.full_witnessing_config()
config_abl     = IFSV4.gate_ablation_config()

# Run main conditions (no transfer)
println("\nRunning main conditions (no transfer)...")
sum_info = IFSV4.v4_run_replications(model, config_info, N_REPS)
println("  Informational-only: done")
sum_rel  = IFSV4.v4_run_replications(model, config_rel, N_REPS)
println("  Relational-only: done")
sum_wit  = IFSV4.v4_run_replications(model, config_wit, N_REPS)
println("  Full witnessing: done")
sum_abl  = IFSV4.v4_run_replications(model, config_abl, N_REPS)
println("  Gate ablation: done")

# Run transfer conditions
println("\nRunning transfer probe conditions...")
sum_wit_xfer  = IFSV4.v4_run_replications(model, config_wit, N_REPS; use_transfer=true)
println("  Full witnessing (transfer): done")
sum_info_xfer = IFSV4.v4_run_replications(model, config_info, N_REPS; use_transfer=true)
println("  Informational-only (transfer): done")
sum_rel_xfer  = IFSV4.v4_run_replications(model, config_rel, N_REPS; use_transfer=true)
println("  Relational-only (transfer): done")

# ---------------------------------------------------------------------------
# Success Criteria
# ---------------------------------------------------------------------------
println("\n" * "=" ^ 60)
println("SUCCESS CRITERIA")
println("=" ^ 60)

T_train = params.T_train

# Criterion 1: Temporal ordering in full witnessing
ordering_rate = sum_wit.metric_means[:ordering_rate]
fp_gate = sum_wit.metric_means[:first_passage_gate]
fp_self = sum_wit.metric_means[:first_passage_self]
fp_meaning = sum_wit.metric_means[:first_passage_meaning]
fp_policy = sum_wit.metric_means[:first_passage_policy]
c1_pass = ordering_rate > 0.60
println("\n1. TEMPORAL ORDERING (full witnessing)")
println("   Ordering rate: $(round(ordering_rate, digits=3))")
println("   First passage — gate: $(round(fp_gate, digits=1)), self: $(round(fp_self, digits=1)), meaning: $(round(fp_meaning, digits=1)), policy: $(round(fp_policy, digits=1))")
println("   $(c1_pass ? "PASS" : "FAIL") (ordering rate > 0.60)")

# Criterion 2: Unburdening (final 5 training trials)
final_gate = mean(sum_wit.mean_gate[max(1,T_train-4):T_train])
final_self = mean(sum_wit.mean_self[max(1,T_train-4):T_train])
final_selfled = mean(sum_wit.mean_selfled[max(1,T_train-4):T_train])
# Check suppress not dominant: mean_selfled > 0.50 means stay-with+direct-ask > suppress+protest
c2_pass = final_gate > 0.50 && final_self > 0.50 && final_selfled > 0.50
println("\n2. UNBURDENING (full witnessing, final 5 trials)")
println("   Gate: $(round(final_gate, digits=3)), Self: $(round(final_self, digits=3)), Self-led policy: $(round(final_selfled, digits=3))")
println("   $(c2_pass ? "PASS" : "FAIL") (all > 0.50)")

# Criterion 3: Transfer
# Get first probe trial (T_train+1) values from transfer runs
T_total = T_train + params.T_probe
probe_idx = T_train + 1
wit_xfer_gate = sum_wit_xfer.mean_gate[probe_idx]
wit_xfer_self = sum_wit_xfer.mean_self[probe_idx]
info_xfer_gate = sum_info_xfer.mean_gate[probe_idx]
info_xfer_self = sum_info_xfer.mean_self[probe_idx]
c3_pass = wit_xfer_gate > 0.50 && wit_xfer_self > 0.50 &&
          info_xfer_gate < 0.30 && info_xfer_self < 0.30
println("\n3. TRANSFER (first cue B probe)")
println("   Witnessing — gate: $(round(wit_xfer_gate, digits=3)), self: $(round(wit_xfer_self, digits=3))")
println("   Informational — gate: $(round(info_xfer_gate, digits=3)), self: $(round(info_xfer_self, digits=3))")
println("   $(c3_pass ? "PASS" : "FAIL") (witnessing > 0.50, informational < 0.30)")

# Criterion 4: Ablation
abl_gate_final = sum_abl.mean_gate[T_train]
abl_self_final = sum_abl.mean_self[T_train]
info_gate_final = sum_info.mean_gate[T_train]
info_self_final = sum_info.mean_self[T_train]
wit_gate_final = sum_wit.mean_gate[T_train]
wit_self_final = sum_wit.mean_self[T_train]
abl_closer_to_info = (abs(abl_gate_final - info_gate_final) + abs(abl_self_final - info_self_final)) <
                     (abs(abl_gate_final - wit_gate_final) + abs(abl_self_final - wit_self_final))
c4_pass = abl_gate_final < 0.40 && abl_self_final < 0.40 && abl_closer_to_info
println("\n4. ABLATION (Presence→Gate blocked, full witnessing obs)")
println("   Gate: $(round(abl_gate_final, digits=3)), Self: $(round(abl_self_final, digits=3))")
println("   Closer to informational than witnessing: $abl_closer_to_info")
println("   $(c4_pass ? "PASS" : "FAIL") (gate < 0.40, self < 0.40, closer to info)")

all_pass = c1_pass && c2_pass && c3_pass && c4_pass
println("\n" * "=" ^ 60)
println("OVERALL: $(all_pass ? "ALL PASS" : "SOME FAIL")")
println("=" ^ 60)

# ---------------------------------------------------------------------------
# Key metrics dump
# ---------------------------------------------------------------------------
println("\n--- Key Metrics ---")
for (name, s) in [("Informational", sum_info), ("Relational", sum_rel),
                   ("Witnessing", sum_wit), ("Ablation", sum_abl)]
    println("\n$name:")
    println("  Gate final:    $(round(s.mean_gate[T_train], digits=3)) ± $(round(s.std_gate[T_train], digits=3))")
    println("  Self final:    $(round(s.mean_self[T_train], digits=3)) ± $(round(s.std_self[T_train], digits=3))")
    println("  Meaning final: $(round(s.mean_meaning[T_train], digits=3)) ± $(round(s.std_meaning[T_train], digits=3))")
    println("  Self-led final:$(round(s.mean_selfled[T_train], digits=3)) ± $(round(s.std_selfled[T_train], digits=3))")
end

# ---------------------------------------------------------------------------
# Figure generation
# ---------------------------------------------------------------------------
if ENABLE_FIGURES
    println("\nGenerating figures...")

    trials = 1:T_train

    # Figure 2: 5-panel main results
    p_a = plot(title="A. Gate: P(permissive)", xlabel="Trial", ylabel="P(permissive)")
    plot!(p_a, trials, sum_wit.mean_gate[trials],
          ribbon=sum_wit.std_gate[trials], label="Full witnessing", color=COL_WITNESS, fillalpha=0.2)
    plot!(p_a, trials, sum_rel.mean_gate[trials],
          ribbon=sum_rel.std_gate[trials], label="Relational-only", color=COL_RELONLY, fillalpha=0.2)
    plot!(p_a, trials, sum_info.mean_gate[trials],
          ribbon=sum_info.std_gate[trials], label="Informational", color=COL_INFOONLY, fillalpha=0.2)
    plot!(p_a, trials, sum_abl.mean_gate[trials],
          ribbon=sum_abl.std_gate[trials], label="Ablation", color=COL_ABLATION, linestyle=:dash, fillalpha=0.2)
    hline!(p_a, [0.5], color=:gray, linestyle=:dot, label=nothing)
    # First-passage marker for witnessing
    if !isnan(fp_gate) && fp_gate <= T_train
        vline!(p_a, [fp_gate], color=COL_WITNESS, linestyle=:dot, alpha=0.5, label=nothing)
    end

    p_b = plot(title="B. Self-state: P(held-capable)", xlabel="Trial", ylabel="P(held)")
    plot!(p_b, trials, sum_wit.mean_self[trials],
          ribbon=sum_wit.std_self[trials], label="Full witnessing", color=COL_WITNESS, fillalpha=0.2)
    plot!(p_b, trials, sum_rel.mean_self[trials],
          ribbon=sum_rel.std_self[trials], label="Relational-only", color=COL_RELONLY, fillalpha=0.2)
    plot!(p_b, trials, sum_info.mean_self[trials],
          ribbon=sum_info.std_self[trials], label="Informational", color=COL_INFOONLY, fillalpha=0.2)
    plot!(p_b, trials, sum_abl.mean_self[trials],
          ribbon=sum_abl.std_self[trials], label="Ablation", color=COL_ABLATION, linestyle=:dash, fillalpha=0.2)
    hline!(p_b, [0.5], color=:gray, linestyle=:dot, label=nothing)
    if !isnan(fp_self) && fp_self <= T_train
        vline!(p_b, [fp_self], color=COL_WITNESS, linestyle=:dot, alpha=0.5, label=nothing)
    end

    p_c = plot(title="C. Meaning: P(contact-manageable)", xlabel="Trial", ylabel="P(manageable)")
    plot!(p_c, trials, sum_wit.mean_meaning[trials],
          ribbon=sum_wit.std_meaning[trials], label="Full witnessing", color=COL_WITNESS, fillalpha=0.2)
    plot!(p_c, trials, sum_rel.mean_meaning[trials],
          ribbon=sum_rel.std_meaning[trials], label="Relational-only", color=COL_RELONLY, fillalpha=0.2)
    plot!(p_c, trials, sum_info.mean_meaning[trials],
          ribbon=sum_info.std_meaning[trials], label="Informational", color=COL_INFOONLY, fillalpha=0.2)
    plot!(p_c, trials, sum_abl.mean_meaning[trials],
          ribbon=sum_abl.std_meaning[trials], label="Ablation", color=COL_ABLATION, linestyle=:dash, fillalpha=0.2)
    hline!(p_c, [0.5], color=:gray, linestyle=:dot, label=nothing)
    if !isnan(fp_meaning) && fp_meaning <= T_train
        vline!(p_c, [fp_meaning], color=COL_WITNESS, linestyle=:dot, alpha=0.5, label=nothing)
    end

    p_d = plot(title="D. Policy: P(stay-with + direct-ask)", xlabel="Trial", ylabel="P(Self-led)")
    plot!(p_d, trials, sum_wit.mean_selfled[trials],
          ribbon=sum_wit.std_selfled[trials], label="Full witnessing", color=COL_WITNESS, fillalpha=0.2)
    plot!(p_d, trials, sum_rel.mean_selfled[trials],
          ribbon=sum_rel.std_selfled[trials], label="Relational-only", color=COL_RELONLY, fillalpha=0.2)
    plot!(p_d, trials, sum_info.mean_selfled[trials],
          ribbon=sum_info.std_selfled[trials], label="Informational", color=COL_INFOONLY, fillalpha=0.2)
    plot!(p_d, trials, sum_abl.mean_selfled[trials],
          ribbon=sum_abl.std_selfled[trials], label="Ablation", color=COL_ABLATION, linestyle=:dash, fillalpha=0.2)
    hline!(p_d, [0.5], color=:gray, linestyle=:dot, label=nothing)
    if !isnan(fp_policy) && fp_policy <= T_train
        vline!(p_d, [fp_policy], color=COL_WITNESS, linestyle=:dot, alpha=0.5, label=nothing)
    end

    # Panel E: Transfer bar chart
    conditions_transfer = ["Witnessing", "Relational", "Informational"]
    gate_vals = [wit_xfer_gate, sum_rel_xfer.mean_gate[probe_idx], info_xfer_gate]
    self_vals = [wit_xfer_self, sum_rel_xfer.mean_self[probe_idx], info_xfer_self]
    x_pos = 1:3
    p_e = plot(title="E. Transfer: first cue B probe", xlabel="", ylabel="Posterior",
               xticks=(x_pos, conditions_transfer), ylim=(0, 1.05))
    bar!(p_e, x_pos .- 0.15, gate_vals, bar_width=0.3, label="P(gate permissive)",
         color=[COL_WITNESS, COL_RELONLY, COL_INFOONLY], alpha=0.7)
    bar!(p_e, x_pos .+ 0.15, self_vals, bar_width=0.3, label="P(self held)",
         color=[COL_WITNESS, COL_RELONLY, COL_INFOONLY], alpha=0.4)
    hline!(p_e, [0.5], color=:gray, linestyle=:dot, label=nothing)

    fig = plot(
        p_a, p_b, p_c, p_d, p_e;
        layout=Plots.grid(3, 2, heights=[0.42, 0.42, 0.16]),
        size=(900, 900),
        margin=5Plots.mm,
    )
    savefig(fig, joinpath(FIGURE_DIR, "ifs_v4_main_results.png"))
    println("  Saved: ifs_v4_main_results.png")

    println("Figures complete.")
end

println("\nDone.")
