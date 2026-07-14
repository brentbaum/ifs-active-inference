# Three-level Beautiful Loop fidelity model

**Date:** 2026-07-14

**Status:** construction passed; not confirmatory

## What changed

The new model implements the seven-part upgrade proposed in the fidelity
audit. It is separate from the clinical five-channel construction so that the
earlier results remain reproducible and their weaker status remains visible.

The generative process is

$$
x^{(3)} \sim \mathcal N(c, e^{-\phi^{(3)}}),\qquad
x^{(2)} \sim \mathcal N(x^{(3)}, e^{-\phi^{(2)}}),
$$

$$
x^{(1)} \sim \mathcal N(x^{(2)}, e^{-\phi^{(1)}}),\qquad
s^{(l)} \sim \mathcal N(x^{(l)}, \tau_s^{-1}).
$$

The global model factorizes each log precision as
$\phi^{(l)}=g+\delta_l$. Its ablation gives each layer an independent
$\phi^{(l)}$ with the same marginal prior variance. This matches the amount
of prior uncertainty while removing only the shared hyper-node.

## Fidelity checklist

| Requirement | Implementation |
|---|---|
| Explicit $x^{(1:3)}$ and $s$ | Three latent states and one noisy observation at every level |
| Layer-specific $\Phi$ | Three inferred log precisions control the three hierarchical links |
| Iterative $q(x),q(\Phi)$ | Exact Gaussian state update alternates with Gaussian variational precision inference |
| Endogenous second-order error | Expected squared residuals include posterior state uncertainty |
| Local and joint free energy | Three layer-local traces, hyper free energy, and the full joint variational free energy are emitted |
| Matched local ablation | Independent meta-loops have identical marginal prior variance but zero cross-layer covariance |
| Out-of-sample context switch | Four contexts train a forecast; a fifth, outside the training range, is tested before every local loop sees new residual evidence |

With all layers observed, the joint free-energy trace descends monotonically in
the construction check. This is stronger than the earlier diagnostic, which
reported a changing quadratic energy without showing that the implemented
updates minimized a coherent variational objective.

## Context-switch result

The training contexts were `[-1.0, -0.4, 0.2, 0.8]`; the test context was
`1.4`. The global forecaster learned one context slope shared across layers.
The local ablation learned three independent slopes. At the switch, only the
first layer supplied new second-order precision evidence. Layers two and three
therefore tested the forecast before their local loops could relearn.

| Measure | Global | Local | Global wins |
|---|---:|---:|---:|
| Out-of-sample precision forecast RMSE | 0.255 | 0.411 | 20/20 seeds |
| Early held-out precision RMSE | 0.205 | 0.414 | 15/20 seeds |
| Early latent-state RMSE | 0.3683 | 0.3740 | 18/20 seeds |

After all three local loops received residual evidence, local precision error
fell by `0.181` on average and improved in 17/20 seeds. The advantage is thus
specifically anticipatory: a shared hyper-model can use a learned contextual
regularity before each layer has accumulated its own new error.

The state-inference improvement is much smaller than the precision-forecast
improvement. The present result therefore supports efficient prediction of a
coordinated precision field more strongly than it supports a large downstream
behavioral benefit.

## Interpretation

This construction answers the strongest earlier objection. Globality is no
longer merely a fixed covariance attached to five clinical channels. A latent
global factor is a parent of every layer precision, the layer residuals create
second-order messages, and the downward precision forecast improves an
out-of-sample inference before independent loops can update.

It does not complete Beautiful Loop Theory. The hierarchy is linear Gaussian;
the context variable and shared training structure are authored; the context
regression is learned between episodes rather than end-to-end inside one
dynamical generative model; and no clinical identity model, policy selection,
or representational redescription is derived. The correct claim is therefore
**a substantially higher-fidelity minimal implementation of the precision
hyper-loop**, not a reproduction of the complete theory.

## Next discriminating test

Break the shared-slope assumption at test. A good global model should detect
that its context forecast has become miscalibrated and relax toward local
meta-inference. Without that reversal, the current experiment demonstrates
the benefit of correct pooling but not the ability of epistemic depth to learn
when global pooling itself should be distrusted.

## Artifacts

- Implementation: `projects/emergence-suite/continuous/src/BeautifulLoopHierarchy.jl`
- Runner: `projects/emergence-suite/continuous/scripts/run_beautiful_loop_hierarchy.jl`
- Summary: `projects/emergence-suite/continuous/results/beautiful_loop_hierarchy/summary.json`
- Per-seed results: `projects/emergence-suite/continuous/results/beautiful_loop_hierarchy/context_switch_per_seed.csv`
- Variational traces: `projects/emergence-suite/continuous/results/beautiful_loop_hierarchy/variational_trace.csv`
