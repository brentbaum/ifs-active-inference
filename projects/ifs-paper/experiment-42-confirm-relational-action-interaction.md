# Experiment 42 — frozen relational-action interaction

**Date:** 2026-07-14

## Frozen prediction

Experiment 41 suggested that relational dependence amplifies the instrumental
value of precision-guided sampling. Experiment 42 froze a paired comparison on
untouched seeds `16001:16020`. Both worlds had identical conditional local
marginals, Gaussian hierarchies, precision fields, context switches, and
two-packet action budgets. They differed only in whether the three local causes
retained their higher-order relational dependence.

## Fresh result

| Effect | Relational world | Factorized world |
|---|---:|---:|
| Full accuracy | 0.814 | 0.593 |
| Exact-action replay accuracy | 0.723 | 0.593 |
| Matched-budget random accuracy | 0.728 | 0.577 |
| Full minus replay | 0.090 | 0.000 |
| Full minus random | 0.086 | 0.0158 |

In the relational world, full beat factorized replay and random on all 20
seeds. The preregistered relational-action interaction was `0.070`, more than
twice its `0.030` criterion. In both worlds the full policy chose channel 1
first before the context switch and channel 3 first afterward in every held-out
episode. The blind policy almost never acquired channel 3 first after the
switch (`3.8%` relational; `6.9%` factorized). Thus the policy mechanism
continued to reallocate when the relation was absent, but its advantage over
random sampling was much smaller.

The factorized projection matched all six conditional local probabilities with
maximum error `2.22e-16`. Both action replay and two-packet budgets were exact,
all computed implementation checks passed, and every full-agent free-energy
trace was non-increasing.

## The one frozen miss

The overall status remains failed. The protocol defined the factorized action
effect as negligible only when its absolute value was at most `0.015`; the
observed value was `0.01583`, a miss of `0.00083`. Twelve of twenty factorized
seeds favored active over random. It would be inappropriate to round this down
or rerun until the cutoff passes.

The central interaction criterion did pass. The result supports *amplification*,
not an all-or-none gate: relational dependence increased the active-sampling
advantage by `0.070`, while a small residual advantage remained without it.
This is also the simpler mechanistic claim. Nothing in the construction implies
that channel reliability becomes wholly irrelevant when local causes are
factorized.

## Interpretation boundary

Across Experiments 40 and 42, the same frozen agent twice reproduced
non-vacuous binding and matched-budget epistemic action on fresh seeds. The
paired ablation shows that their conjunction is more than coexistence:
relational scene structure materially increases the payoff from
precision-guided evidence selection. The relation family, precision loading
basis, and EIG-shaped policy remain authored, so this is a construction result
about interacting operations, not autonomous discovery of a Beautiful Loop.
