---
date: 2026-07-14
topic: competitive-binding
---

# Non-vacuous Bayesian binding

## What we are building

Experiment 34 replaces ordinary conditionally independent evidence pooling
with competition among joint scene hypotheses. A binary global scene is
encoded by the parity relation among three local causes. Each local cause is
individually uniform and therefore contains zero information about the global
scene. The full model encodes their relation. Its control receives the same
evidence and precision hyper-loop but represents only the identical local
marginals.

The test is deliberately minimal. Both agents observe every branch, use exact
Bayesian inference over their respective cause spaces, alternate state and
precision updates, and update identical global precision forecasters from
posterior residual moments. Any difference is therefore due to joint causal
structure rather than evidence quantity, posterior truncation, or a hard-vote
decoder.

## Why this approach

A mere shared cause is insufficient: conditional independence makes its
posterior equivalent to a product of local likelihoods. The parity benchmark
is the smallest synergy test in which information exists in the configuration
but in none of its components. It makes coherence a property of a scene rather
than a relabeling of local evidence pooling, capturing the Beautiful Loop
paper's claim that mutually constraining explanations compete to enter a
unified reality model.

## Frozen pilot criteria

- full held-out accuracy exceeds the matched-independent model by 0.02 and in
  at least 15/20 seeds;
- the advantage is at least 0.20 on relation-preserving scenes and appears in
  at least 18/20 seeds;
- the report exposes relation-violating trials as a scope condition rather than
  hiding their expected failure;
- all structural checks are reported separately from empirical criteria.

Failure is informative. It would mean that this minimal exclusion relation is
not enough to turn the hyper-loop into a useful binding mechanism.

## Pilot iteration

The first symmetric pilot used 55% fully coherent scenes, four observations per
branch, and a weak local signal. The two models made identical decisions: the
joint prior altered confidence but almost never the decision boundary. A small
mechanism grid found one apparently positive setting on two seeds, but the full
twenty-seed run shrank to `0.729` versus `0.724`, with only 10/20 wins. The
exclusion relation was real but not behaviorally discriminating. The parity
benchmark replaces that geometry rather than tuning the small gap. Five percent
relation-violating trials remain as an explicit adversarial scope condition. A
small identifiability check then set four observations per feature and signal
amplitude `1.05`; weaker settings left the local features themselves too noisy
to test whether their relation could be recovered.
