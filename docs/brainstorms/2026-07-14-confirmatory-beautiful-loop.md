---
date: 2026-07-14
topic: confirmatory-beautiful-loop
---

# Frozen confirmation of binding and learned precision depth

## Confirmatory tests

The architecture and all thresholds are frozen before fresh seeds are run.

1. **Relational binding:** seeds `9801:9820`, using Experiment 34 unchanged.
   Overall accuracy must exceed the matched local-marginal control by `0.15`,
   relation-preserving accuracy by `0.20`, and seed-wise wins must be at least
   `18/20` on both measures.
2. **Learned global precision:** seeds `9901:9920`, using Experiment 35
   unchanged. Loading correlation must exceed `0.75`; forecast RMSE must beat
   independent loops by `0.10` and the tying-capable adaptive model by `0.10`,
   each in at least `15/20` seeds. Task accuracy remains a separate outcome.

## Load-bearing stress tests

Fresh seed blocks are used for every cell rather than recycling confirmatory
seeds. Binding cells vary local signal amplitude, samples per branch, and
relation noise. Precision cells vary regression evidence variance, forgetting,
training duration, and component-specific slope deviations.

The binding grid contains seven one-factor cells: baseline; amplitudes `0.85`
and `1.25`; three and five samples; and relation noise `0.00` and `0.10`. A cell
retains the signature when the relation-preserving advantage is at least `0.15`
and the overall advantage at least `0.10`; at least six of seven must pass.

The precision grid contains baseline; regression evidence variance `0.30` and
`0.70`; forgetting `0.990` and `0.999`; training lengths 60 and 100; and local
deviation scales `0.30`, `1.00`, `2.00`, and `3.00`. Non-deviation cells retain
the signature when global RMSE beats adaptive-local RMSE by `0.05`. Deviation
`1.00` is the transition band. At `2.00` adaptive local must be no worse; at
`3.00` it must win by `0.05` and lower its effective shrinkage below the prior
mean of `7.38`.

The deviation test is a scope prediction, not an invariance test. Compact
global structure should win when deviations are zero or small; the adaptive
local model should catch and eventually beat it as deviations become large.
A crossover is stronger evidence than universal global victory because it
shows that each model wins in the environment matching its structural bias.

## Reporting rule

Structural checks, enforced optimization invariants, confirmatory empirical
criteria, and stress-test scope conditions are reported in separate blocks.
No cell is removed and no threshold is changed after fresh-seed results are
opened.
