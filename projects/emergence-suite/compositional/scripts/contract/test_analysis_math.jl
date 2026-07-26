#!/usr/bin/env julia

module AnalysisMath
include(joinpath(@__DIR__, "analysis_math.jl"))
end

function main()
    AnalysisMath.arithmetic_mean([1.0, 2.0, 6.0]) == 3.0 ||
        error("mean vector failed")
    AnalysisMath.empirical_median([8.0, 1.0, 4.0]) == 4.0 ||
        error("odd median vector failed")
    AnalysisMath.empirical_median([8.0, 1.0, 4.0, 2.0]) == 3.0 ||
        error("even median vector failed")
    AnalysisMath.sample_standard_deviation([1.0, 2.0, 3.0]) == 1.0 ||
        error("sample standard-deviation vector failed")
    AnalysisMath.nearest_rank([4.0, 1.0, 3.0, 2.0], 0.0) == 1.0 ||
        error("zero quantile vector failed")
    AnalysisMath.nearest_rank([4.0, 1.0, 3.0, 2.0], 0.5) == 2.0 ||
        error("median-rank vector failed")
    AnalysisMath.nearest_rank([4.0, 1.0, 3.0, 2.0], 1.0) == 4.0 ||
        error("one quantile vector failed")
    AnalysisMath.unit_key("episode"; seed = 7, arm = "arm-one", episode = 2) ==
        "seed=7;arm=arm-one;episode=2" ||
        error("unit serialization vector failed")
    AnalysisMath.unit_key("episode"; seed = 7, episode = 2, paired = true) ==
        "seed=7;episode=2" ||
        error("paired-unit serialization vector failed")
    AnalysisMath.unit_accepts_row("event", "event") &&
        !AnalysisMath.unit_accepts_row("event", "tick") ||
        error("event-unit implicit row-domain vector failed")

    digest = bytes2hex(AnalysisMath.bootstrap_digest(
        "analysis-one", "estimand-one", 0, 0))
    digest == "5e9812f2897168fdceb9411f3c8e83af23f59e6c4380f85e2691f741913812af" ||
        error("bootstrap digest vector failed: $digest")
    index = AnalysisMath.bootstrap_index(
        17, "analysis-one", "estimand-one", 0, 0)
    index == 6 ||
        error("bootstrap index vector failed: $index")
    paired_keys = [
        AnalysisMath.unit_key("seed"; seed = 2, paired = true),
        AnalysisMath.unit_key("seed"; seed = 10, paired = true),
    ]
    paired_values = [7.0, 3.0]
    order = sortperm(paired_keys)
    ordered_pairs = paired_values[order]
    pair_indices = AnalysisMath.bootstrap_indices(
        2, "paired-analysis", "paired-estimand", 0)
    pair_indices == [0, 0] ||
        error("paired bootstrap index vector failed: $pair_indices")
    AnalysisMath.arithmetic_mean(ordered_pairs[pair_indices .+ 1]) == 3.0 ||
        error("paired bootstrap value vector failed")
    lower, upper = AnalysisMath.clopper_pearson(5, 10, 0.95)
    isapprox(lower, 0.18708602844739852; atol = 1e-14, rtol = 0) ||
        error("Clopper-Pearson lower vector failed: $lower")
    isapprox(upper, 0.8129139715526015; atol = 1e-14, rtol = 0) ||
        error("Clopper-Pearson upper vector failed: $upper")
    zero_lower, zero_upper = AnalysisMath.clopper_pearson(0, 10, 0.95)
    zero_lower == 0.0 ||
        error("Clopper-Pearson zero-success lower boundary failed")
    isapprox(zero_upper, 0.3084971078187608; atol = 1e-14, rtol = 0) ||
        error("Clopper-Pearson zero-success upper vector failed: $zero_upper")
    !AnalysisMath.point_comparison(1.0, "gt", 1.0) ||
        error("strict greater-than boundary failed")
    AnalysisMath.point_comparison(1.0, "ge", 1.0) ||
        error("inclusive greater-than boundary failed")
    AnalysisMath.point_comparison(-1.0, "between", [-1.0, 1.0]) ||
        error("closed between boundary failed")
    !AnalysisMath.interval_comparison(
        0.0, 1.0, "lower_above_zero", 0.0) ||
        error("strict lower-above-zero boundary failed")
    !AnalysisMath.interval_comparison(
        -1.0, 1.0, "inside_equivalence", [-1.0, 1.0]) ||
        error("strict equivalence interval boundary failed")
    !AnalysisMath.decision_pass(
        1.0, 0.0, 2.0, "ge", 1.0, "lower_above_threshold") ||
        error("decision conjunction vector failed")
    println("analysis math conformance passed")
    return true
end

main()
