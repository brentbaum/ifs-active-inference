# V3.1 stage report

Status: **FROZEN_ADJUDICATED_MIXED_REVISABILITY_LIMITATION**.

- Stage 0: thresholds frozen from the barred 3100000–3101999 block, including
  a prospective efficacy construct amendment on its previously unconsumed
  tail.
- Gate 1: PASS. The 128-program prior and posterior normalize; the independent
  oracle matches exactly; missing outcome BF is zero; graph classifiers
  partition posterior mass.
- Gate 2: PASS on 1,000 scorer-prior worlds. Field accuracy `0.834286`,
  whole-program accuracy `0.292`, ECE `0.032916`, 95% coverage `0.956`, and
  oracle error `0`.
- Gate 3: FAIL. Seven results passed. High-control histories were far less
  mode-structured, but their revisability advantage was `0.005242` versus the
  frozen `0.0071` floor, with a 95% interval crossing zero.
- Gate-3 adjudication: mixed-verdict continuation authorized the revisability
  family as non-blocking; every other criterion remained blocking.
- Gate 4 original run: software stop before criterion evaluation. Removing the
  only mode slot left observed mode-one values with zero support under every
  surviving program. All candidate scores were `-inf`, so the posterior was
  undefined.
- Gate-4 repair: candidate-common masking passed with exact error `0.0`; all
  lesioned posteriors were finite and normalized.
- Gate 4 repaired run: FAIL. Five lesions passed. The identity-edge lesion
  removed part-like mass exactly, but retained-edge survival was only 182/333
  (`0.546547`) against the blocking `0.90` floor.
- Gate-4 selectivity adjudication: the absolute-movement statistic was
  reclassified and replaced by a restricted-prior identity. An initial custody
  stop found that the prior runner had not serialized its worlds.
- Gate-4 amended rescore: PASS. The evaluator authorized deterministic
  reconstruction of the consumed block. The complete prior aggregate object
  reproduced exactly. All six declared consequences passed; the largest
  restricted-prior and independent-oracle errors were below `1e-14`.
  Absolute retained-edge movement is descriptive and decomposes into
  typed-evidence transformation, prior renormalization, and numerical
  residual.
- Gate 5: PASS. All four V3.1 robustness cells passed field-accuracy,
  coverage, and exact-log-probability criteria. Standing V3.0 robustness
  across missingness, cue count, slot bounds, code prior, and concentration
  remained PASS.
- Gate-5 report assembly: a stale interval key caused a post-scoring crash.
  All 800 traces had already been serialized and hashed. The report was
  assembled from those hash-verified traces without rerunning a world.

Final regression status: V3 23/23 green; frozen V2 180/180 green.

The formal Gate-3 verdict remains FAIL. Its sole revisability-floor miss is
retained verbatim and non-blocking under `gate3-adjudication.md`; it is not
converted to a pass.

C-V31 escrow 4010000–4013999 was not accessed.
