# V2.7 Gate-4 repair diff summary

Authorization: `gate4-software-repair-authorization.md`.

The scientific repair changes one path only:

- when the `reduction` lesion is present,
  `score_world_with_reduction` now returns through the identical unreduced
  `score_world` exact candidate-model-average path;
- it no longer replaces the three-candidate mandate mixture with a scalar
  posterior mean.

The restoration-identity regression test pins the structure posterior,
expected costs, and joint-policy posterior byte-for-byte. The repaired Gate-4
execution reports `0.0` reduction residual. All 2,572 non-reduction lesion
worlds are byte-identical to the retained execution.

No likelihood, prior, parameter, threshold, generator, observation,
registration rule, shared-outcome rule, assigned block, or intact reduction
composition changed.
