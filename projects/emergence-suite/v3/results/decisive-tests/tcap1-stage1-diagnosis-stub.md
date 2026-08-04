# T-CAP1 Stage 1 apparatus stop

Classification: **FAIL_APPARATUS_STAGE1_COMMON_WORLD_AND_READOUT_COMPLETENESS**.

Stage 0 remains PASS. The public census block `3824000:3831999` was consumed
once and its raw traces remain sealed under SHA-256
`c1cecb3232f43578ba45395a0b4b730469535ae44128f4677c268a845449f64e`.

The post-run audit found two apparatus defects. Transparent and represented
architectures do replay one byte-identical feedback stream, as proved. But the
other controls call the generator with arm-specific `bundle-stay:{arm}` RNG
keys. Their latent bundle paths can therefore differ, so they are not clean
counterfactual allocation controls on one common world.

Second, `fixed_point_count` is only a trajectory-end heuristic. The required
replay from low and high initial bundle posteriors—and therefore the explicit
fraction of worlds with two stable fixed points—was not computed. No
post-consumption retrofit was performed.

Separately, the frozen census grid did not span the requested dynamics panel:
all 324 cells fell in the clear-hysteresis region. The minimum cell-mean
transparent area was `0.08085224401195291`, just above the predeclared `0.08`
boundary. The missing no-hysteresis and near-boundary entries remain null.

No repair, rerun, prediction seal, confirmatory seed, or escrow access occurred.
The stage stops for evaluator adjudication.
