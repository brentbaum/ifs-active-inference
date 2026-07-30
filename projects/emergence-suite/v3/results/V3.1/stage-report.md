# V3.1 stage report

Status: **STOPPED_AT_GATE_4_SOFTWARE_FAILURE**. No freeze manifest exists.

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
- Gate 4: software stop before criterion evaluation. Removing the only mode
  slot left observed mode-one values with zero support under every surviving
  program. All candidate scores were `-inf`, so the posterior was undefined.
- Gate 5: not opened.

No repair was attempted. Post-stop regression status: V3 21/21 green; frozen
V2 180/180 green.

C-V31 escrow 4010000–4013999 was not accessed.
