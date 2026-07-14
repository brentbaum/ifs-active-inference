# Experiment 30 — endogenous temporal hyper-model

**Date:** 2026-07-14

## Question

Can a precision hyper-model learn when cross-layer coupling should be trusted,
abandon that coupling when it breaks, and recover it when coordination returns,
without being told that the environmental regime changed?

## Construction

The model maintains two online Gaussian generative explanations of the next
three-layer precision field: a four-parameter model with one context slope
shared by all layers and a six-parameter model with independent layer slopes.
Both receive the same precision evidence. That evidence is generated from
expected residuals in the lower three-level hierarchy, so the forecast shapes
state inference and the resulting second-order errors update the forecast.

A posterior model weight selects between the shared and local explanations.
The environment has ninety steps: coordinated precision changes, independent
changes, then coordinated changes again. The agent observes context and
residual evidence but never the regime label.

## Iteration record

The first run correctly released coupling and beat forced global pooling, but
did not express confident global selection: initial global weight was `0.577`
and only 13/20 seeds recovered above `0.60`. The criteria were retained.

The successful revision added a fixed log prior of `0.55` for the simpler
four-parameter global model over the six-parameter local model. This is an
explicit Occam prior, not knowledge of the current regime. Independent
evidence still had to overcome it.

## Results

| Measure | Result |
|---|---:|
| Late first coordinated global weight | 0.704 |
| Late independent global weight | 0.080 |
| Late recovery global weight | 0.740 |
| Independent adaptive RMSE | 0.319 |
| Independent forced-global RMSE | 0.574 |
| First coordinated adaptive RMSE | 0.087 |
| First coordinated local RMSE | 0.098 |

All four model-selection effects held in 20/20 seeds. The result shows a
forecasting system that models not only layer precision but whether its own
global coupling assumption is currently useful.

## Boundary

The context itself remains observed, the two candidate coupling structures are
authored, and model selection uses a finite-memory Bayes-factor approximation.
The result is an endogenous temporal hyper-loop, not unrestricted structure
learning and not evidence for consciousness.
