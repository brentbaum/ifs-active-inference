---
date: 2026-07-14
topic: identifiable-globality-control
---

# Frozen identifiable globality control

## Why this experiment is required

Experiment 37 made layer-specific transition precision identifiable by adding
noisy monitoring at every latent level. It then compared a compact shared field
with a nested shared-plus-local field. Both are global hyper-models: evidence
from every level enters one joint posterior and the resulting field is returned
to every level. The experiment therefore tested the degree of sharing inside a
global model, not global recursive inference against independent local
meta-loops.

Earlier global-versus-independent comparisons used bottom-only observations,
which identify total transition variance but not its layerwise decomposition.
This follow-up supplies the missing control in the identifiable regime.

## Frozen construction

The inference code, episode count, training contexts, held-out context,
layer-observation precision, and regression updates remain those of Experiment
37. A third forecaster is added:

- `compact_global`: six shared intercept/loading coefficients;
- `nested_global`: the same six coefficients plus nine shrinkage-controlled
  local slope deviations; and
- `independent_local`: eighteen unrelated intercept/slope coefficients with no
  cross-layer or cross-channel parameter sharing.

The compact and independent models have identical marginal prior predictive
variance for every precision component. Every model sees the same noisy layer
observations and the same inferred posterior residual moments. Hidden states,
true precisions, and loading vectors remain scoring-only.

## Untouched seed block and criteria

Seeds `12001:12020` are frozen before results are opened. The paired block is
run at local-deviation scales `0.0` and `2.0`.

At exact sharing (`0.0`):

1. compact-global forecast RMSE must beat independent-local RMSE by at least
   `0.10`, with at least `15/20` paired seed wins;
2. nested-global RMSE must beat independent-local RMSE by at least `0.05`, with
   at least `15/20` paired seed wins.

At deviation scale `2.0`:

3. nested-global RMSE must beat compact-global RMSE by at least `0.05`, with at
   least `15/20` paired seed wins; and
4. nested-global must be no more than `0.05` RMSE worse than independent local
   loops. This is a scope check: global recursive inference must be able to
   represent warranted local structure, not force uniformity.

Across both conditions, mean scene-accuracy differences among the three agents
must remain within `0.03`; forecast claims may not be relabeled as task gains.

## Interpretation boundary

Passing would support a sample-efficiency advantage for joint precision
inference over independent local meta-loops when layerwise errors are
identifiable and genuinely share structure. It would not show that global
models always win, that one anatomical node is required, or that direct noisy
monitoring of every layer reproduces Beautiful Loop Theory's bottom-sensed
Table 1. The direct-monitoring route trades hierarchical fidelity for
identifiability and that trade remains part of the result.
