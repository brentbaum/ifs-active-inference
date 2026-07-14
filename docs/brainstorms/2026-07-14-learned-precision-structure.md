---
date: 2026-07-14
topic: learned-precision-structure
---

# Learning the global precision structure

## What we are building

Experiment 35 removes the privileged loading basis from the precision field.
Each seed receives a newly sampled, centered channel-loading vector with fixed
norm. The vector controls all three hierarchical levels but is never shown to
an agent. A six-parameter global forecaster must infer three layer intercepts
and three channel loadings from posterior residual evidence.

The key comparator is not a deliberately high-variance collection of local
regressions. It is an 18-parameter local model averaged over six hierarchical
shrinkage priors. Its model weights are updated by predictive evidence. At high
shrinkage the model can discover exactly the tying used by the global model;
at low shrinkage it can retain component-specific deviations. A zero-shrinkage
local model remains as a reference.

## Frozen exploratory criteria

- the learned global loading correlates at least `0.75` with the hidden loading
  on average and in at least 15/20 seeds;
- it improves out-of-sample forecast RMSE over independent local loops by at
  least `0.10` and wins in at least 15/20 seeds;
- the adaptive local model learns nonzero tying and recovers the loading;
- the global forecast must improve on the adaptive local model by at least
  `0.10` in 15/20 seeds before a distinctive forecasting claim is made;
- task accuracy is reported separately and must not be inferred from forecast
  advantage when the difference is within `0.03`.

## Interpretation rule

If the global model beats only the independent reference, the result supports
structured shrinkage rather than a unique global node. If it also beats the
adaptive local model on fresh seeds, that would support a more distinctive
global-depth claim. Either result is publishable if reported without moving the
criterion.
