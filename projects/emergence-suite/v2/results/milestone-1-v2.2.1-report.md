# Suite v2 milestone 1 — V2.2.1 repair section

This additive strain responds to the retained C-V22 failure. The prerepair
diagnosis found verdict (b): calibrated continuous association learning, but no
finite model component for exact non-association.

## Repair

V2.2.1 compares an exact `theta=.5` association spike against a learnable
Beta(match=9,mismatch=1) slab under prior model probabilities `.6/.4`.
Downstream inference receives the posterior-model-averaged CPT. No transfer
threshold, association clamp, target write, or mediation lesion was added.

## Gate reruns

### V2.0 under V2.2.1

- gate_1_semantic: PASS
- gate_2_recovery: PASS
- gate_3_comparison: PASS
- gate_4_batch_mutation: PASS
- gate_5_one_posterior: PASS

State accuracy/Brier/ECE remained
`0.848` /
`0.129` /
`0.005`.

### V2.1 under V2.2.1

- gate_1_semantic: PASS
- gate_2_recovery: PASS
- gate_3_composition: PASS
- gate_4_selective_lesion: PASS
- gate_5_cumulative_regression: PASS

Broadcast depth effect remained `0.397`;
cross-latent delivered log-odds effect remained
`0.902`.

### Repaired V2.2

- gate_1_structure_semantics: PASS
- gate_2_recovery: PASS
- gate_3_precision_root_transfer: PASS
- gate_4_selective_lesions: PASS
- gate_5_cumulative_regression: PASS

- Analytic/exact structure-posterior error:
  `3.21e-17`.
- True-zero / true-associated component posterior:
  `0.9975` /
  `1.0000`.
- Existence recovery accuracy:
  `1.000`.
- Slab parameter MAE / 95% coverage:
  `0.021` /
  `1.000`.
- True-zero floor-clean rate:
  `0.988` over
  `256` worlds.
- Mean true-zero transfer, 95% interval:
  `0.0010`
  `[0.0006,
  0.0015]`.
- Mean associated transfer, 95% interval:
  `0.324`
  `[0.323,
  0.326]`.

## Status

All gates 1–5 pass in the V2.2.1 strain. The original V2.2 and Gate-6
artifacts remain unchanged. C-V22b remains sealed and unrun; its plaintext and
seeds were not accessed. Work stops at this freeze candidate.
