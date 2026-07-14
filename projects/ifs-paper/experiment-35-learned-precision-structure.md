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
at a deliberately tempered learning rate of `0.04`, so it can discover the
global regularity but commits to a shrinkage regime slowly. All models receive
the correct linear context family; they learn its coefficients, not its
functional form.

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
loading values: the unfamiliar field orientation was recovered from residual
evidence. The forecast horse race is not clean, however. Bottom-only
observations do not identify the scored layerwise precision vector, and the
tying-capable comparator's model evidence is tempered. Experiment 37 therefore
supersedes the compact-versus-adaptive advantage rather than merely adding a
scope condition.

The result is specifically about forecasting. All three agents made the same
scene decisions, so lower precision RMSE did not improve task accuracy here.
The environment still contains exact cross-layer tying, which favors the
compact global model. Confirmation must therefore use an identifiable
observation graph, fresh seeds, and a truly independent local control.
Experiments 37 and 38 supply those tests.
