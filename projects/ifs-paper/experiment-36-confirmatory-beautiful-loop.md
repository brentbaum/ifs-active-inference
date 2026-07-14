# Experiment 36 — frozen confirmation and stress tests

**Date:** 2026-07-14

## Protocol

Experiments 34 and 35 were frozen before opening two new twenty-seed blocks:
`9801:9820` for relational binding and `9901:9920` for learned precision
structure. Eighteen load-bearing stress cells used separate five-seed blocks.
The written protocol fixed all thresholds, including a predicted crossover in
which sufficiently large local deviations would make the adaptive local model
beat the compact global forecaster.

## Confirmatory results

| Test | Full/global | Strong control | Seed wins |
|---|---:|---:|---:|
| Relational binding accuracy | 0.726 | 0.503 local marginals | 20/20 |
| Relation-preserving accuracy | 0.750 | 0.504 local marginals | 20/20 |
| Learned precision RMSE | 0.673 | 0.835 adaptive local | 17/20 |
| Learned precision RMSE | 0.673 | 0.977 independent local | 17/20 |
| Hidden-loading correlation | 0.987 | 0.992 adaptive local | — |
| Scene accuracy | 0.686 | 0.686 adaptive local | tied |

Both primary fresh-seed confirmations passed. The binding stress signature also
passed all seven cells spanning signal amplitude, sample count, and relation
noise. The global precision advantage passed every non-deviation cell spanning
regression evidence variance, forgetting, and training duration.

## Frozen failure

The local-deviation crossover was directionally present but smaller than
declared. At deviation scale `2.0`, global RMSE remained lower by `0.028`; the
protocol required adaptive local to be no worse. At `3.0`, adaptive local was
better by `0.023`, below the required `0.050`. Its effective shrinkage did fall
from about `9.72` to `5.71`, showing evidence-sensitive untying, but not enough
to clear the predicted performance crossover. Nine of eleven precision stress
predictions passed; the overall frozen status is therefore **failed**.

## Interpretation

The positive results are confirmatory: relational synergy, learned hidden
loadings, and a compact global forecasting advantage all replicate on fresh
seeds. The failed crossover matters. The adaptive local model can represent
deviations but its conservative model averaging does not release tying quickly
enough. The next experiment may improve that learner and use another untouched
seed block, but it may not relabel this run as passed or weaken the original
crossover threshold.
