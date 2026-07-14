# Experiment 37 — identifiable global-to-local precision structure

**Date:** 2026-07-14

## Problem exposed by Experiment 36

Observing only the bottom of an additive three-level Gaussian chain identifies
the sum of its transition variances, not their layer-specific decomposition.
More temporal samples estimate that sum more accurately but do not solve the
structural ambiguity. This weakens Experiment 33's claim that four draws alone
identified three link precisions.

## Construction

Every latent level now emits a noisy observation with known precision. The
hidden states themselves are never supplied to inference, and true precision
remains scoring-only. This makes the layerwise transition residuals
identifiable but changes the observation graph: higher levels are directly
monitored rather than constrained only through bottom-level sensations. It is
one possible implementation of system-wide error monitoring, not a literal
reproduction of Beautiful Loop Theory's Table 1.

The strong comparator is nested rather than parallel. Both alternatives are
global hyper-models:

\[
\phi_{\ell j}(c)=\alpha_\ell+(b_j+\delta_{\ell j})c.
\]

The six shared terms are the compact global model. Nine local deviations are
added under an evidence-weighted shrinkage hyperprior. Infinite shrinkage gives
the global model exactly; decreasing shrinkage releases component-specific
structure. Thus the comparator can share globally or become local as evidence
requires.

## Paired fresh-seed results

The frozen paired block `11001:11020` reused the same hidden loading vectors and
episode noise across four deviation levels:

| Local deviation | Compact global RMSE | Nested RMSE | Nested shrinkage |
|---:|---:|---:|---:|
| 0.0 | 0.345 | 0.357 | 8.31 |
| 1.0 | 1.355 | 0.670 | 5.26 |
| 2.0 | 2.665 | 1.032 | 1.93 |
| 3.0 | 3.997 | 1.340 | 0.90 |

The nested model won 20/20 seeds at every nonzero deviation. Scene accuracy
remained nearly identical throughout; the largest difference was half a
percentage point.

## Frozen result and theory update

The experiment's overall frozen status is **failed** because the compact global
model's exact-sharing advantage was only `0.012`, below the preregistered
`0.050`, and appeared in 13/20 rather than 15/20 seeds. The remaining three
criteria passed by wide margins.

That failure is theoretically useful. A capable hierarchical model should
approximate its nested global limit when the world is globally tied. The data
identify an effective degree of cross-layer coupling, not one unique
architectural node. The more defensible operational statement is therefore:

> Epistemic depth is the recursively closed, system-wide inference by which a
> precision field—including both shared structure and warranted local
> deviations—is monitored and rebroadcast to constrain lower-level inference
> and action.

The shrinkage hyperbelief is **not** itself a depth variable. It estimates a
property of the current environment: how similarly precision changes across
layers. A deep, well-calibrated system should infer low shrinkage when the
layers genuinely differ. What distinguishes the nested hyper-model from
independent local loops is instead its message-passing graph: evidence from all
levels informs one joint posterior, whose whole field is returned to all
levels. This is closer to the Beautiful Loop's functional claim while avoiding
both unsupported shortcuts—that epistemic depth requires one anatomical node,
or that more uniform precision is necessarily deeper.

Experiment 38 adds the missing independent local loops under the same monitored
observation graph. It is the globality test; this experiment is the internal
global-to-local structure test.
