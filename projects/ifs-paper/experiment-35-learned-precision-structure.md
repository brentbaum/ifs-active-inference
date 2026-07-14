# Experiment 35 — learning the precision field's structure

**Date:** 2026-07-14

## Question

Does global precision forecasting remain useful when the agent is not handed
the environment's loading vector, and can it beat a local model that is itself
allowed to discover the same tying structure?

## Construction

Each seed receives a newly sampled three-component channel loading $b$. It is
centered and normalized but otherwise unconstrained:

\[
\phi_{\ell j}(c)=\alpha_\ell+b_jc.
\]

The hidden loading replaces Experiment 33's supplied `(-1,0,1)` basis. A
six-parameter global forecaster learns three layer intercepts and all three
channel loadings online from inferred $q(\Phi)$; true precision and $b$ are
used only for scoring.

Two controls receive the same relational-binding episodes and posterior
residual updates. The independent control has eighteen unconstrained local
intercept/slope parameters. The stronger adaptive control has the same local
parameters but averages six Gaussian priors ranging from independence to
strong cross-component tying. Predictive evidence updates the model weights,
so it can discover the global regularity rather than being forbidden from
representing it.

## Exploratory results

Across twenty seeds:

| Measure | Learned global | Adaptive local | Independent local |
|---|---:|---:|---:|
| Out-of-sample forecast RMSE | 0.676 | 0.832 | 0.958 |
| Hidden-loading correlation | 0.981 | 0.988 | — |
| Held-out scene accuracy | 0.688 | 0.688 | 0.688 |

The global forecast beat the independent control in 19/20 seeds and the
adaptive hierarchical control in 20/20. The adaptive model nevertheless
recovered the loading orientation and shifted its evidence-weighted shrinkage
from a prior mean of `7.38` to `9.72`, showing that it was a capable structural
competitor rather than independent regressions under another name.

## Interpretation

The original result was not solely manufactured by supplying the correct
loading values. A compact global parameterization can learn an unfamiliar
field orientation from residual evidence and generalize it out of sample more
efficiently than both independent and tying-capable local models.

The result is specifically about forecasting. All three agents made the same
scene decisions, so lower precision RMSE did not improve task accuracy here.
The environment still contains exact cross-layer tying, which favors the
compact global model. Confirmation must therefore use fresh seeds and vary the
amount of local deviation; the adaptive model should eventually win as the
global regularity breaks down.
