# Experiment 38 — identifiable globality control

**Date:** 2026-07-14

## Missing comparison

Experiment 37 compared a compact shared precision field with a nested
shared-plus-local field. Both are global hyper-models: one joint posterior
receives evidence from all levels and returns the entire field to all levels.
It therefore did not compare global recursive inference with independent local
meta-loops. Earlier global-versus-independent results used bottom-only sensing,
which cannot identify layer-specific transition precision.

The protocol and code for this follow-up were committed before seeds
`12001:12020` were opened. The three paired agents were:

- a six-parameter compact global field;
- a fifteen-parameter nested global field with evidence-weighted local
  deviations; and
- eighteen independent local intercepts and slopes with no shared parameters.

The compact and independent agents had identical marginal prior predictive
variance. All agents received the same noisy monitoring observations at every
layer and updated only from their own posterior residual moments.

## Fresh-seed results

| Local deviation | Compact global RMSE | Nested global RMSE | Independent local RMSE |
|---:|---:|---:|---:|
| 0.0 | 0.340 | 0.359 | 0.637 |
| 2.0 | 2.716 | 1.068 | 1.090 |

Under exact sharing, compact and nested global inference beat independent
loops in 20/20 paired seeds, by mean RMSE margins `0.298` and `0.278`. Under
strong local deviations, the nested global model beat the compact model in
20/20 seeds and was slightly better than independent loops on average. Its
effective shrinkage fell from `8.32` to `1.88`. Mean scene accuracies differed
by less than one percentage point in both conditions.

All five frozen empirical criteria passed.

## Interpretation

This supplies the missing globality test in an identifiable regime. When the
environment shares precision structure, joint recursive inference borrows
evidence across the hierarchy and forecasts a new context more efficiently
than matched independent meta-loops. When the environment contains large local
departures, a capable global hyper-model represents them instead of forcing
uniformity and performs on par with fully independent learning.

The result supports global message passing, not a unique anatomical node or a
scalar amount of tying. It also retains Experiment 37's fidelity boundary:
layerwise transition precision is identifiable here because every level emits
a noisy monitoring observation with known precision. Beautiful Loop Theory's
bottom-sensed Table 1 does not provide those observations, so this construction
chooses identifiability at the cost of a less faithful observation graph.
