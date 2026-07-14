---
date: 2026-07-14
topic: hierarchical-crossover
---

# A nested global-to-local precision model

## What changes

Experiment 36 showed that the adaptive local model released shrinkage in the
right direction but too slowly to clear the frozen crossover threshold. A
learning-rate sweep and fixed-shrinkage audit showed that model weighting was
not the bottleneck. The local model wasted evidence by estimating eighteen
intercepts and slopes from scratch.

Experiment 37 replaces that comparator with a nested random-effects model:

\[
\phi_{\ell j}(c)=\alpha_\ell+(b_j+\delta_{\ell j})c.
\]

The six shared coefficients are identical to the global model. Nine local
deviations are then added under an evidence-weighted shrinkage prior. As
shrinkage tends to infinity the model becomes the global model; as shrinkage
falls it expresses component-specific departures. This is the simplest model
that can share when the world is global and untie when it is not.

An exploratory check exposed a prior problem in the observation model: three
additive link variances are not separately identifiable from observations of
the bottom state alone. More temporal samples estimate their sum more closely
but do not identify its decomposition. Experiment 37 therefore makes the
Beautiful Loop monitoring assumption explicit: every layer emits a noisy
observation to the hyper-loop. Latent states and true precisions remain hidden,
but layer-specific residual statistics become identifiable.

## Frozen second-confirmation criteria

After an exploratory mechanics check, another untouched seed block must show:

- at zero deviation, the compact global model retains at least `0.05` RMSE
  advantage over the nested model;
- at deviation `2.0`, the nested model is no worse than global;
- at deviation `3.0`, the nested model beats global by at least `0.05` and its
  effective shrinkage falls below the no-deviation value;
- the original relational-binding confirmation is not rerun or retuned.

This is a new experiment, not a relabeling of Experiment 36. Its failed status
and original thresholds remain in the record.

The paired confirmatory block is frozen as seeds `11001:11020`, evaluated at
local-deviation scales `0.0`, `1.0`, `2.0`, and `3.0`. Pairing preserves each
seed's hidden loading and episode noise across the structural conditions.
