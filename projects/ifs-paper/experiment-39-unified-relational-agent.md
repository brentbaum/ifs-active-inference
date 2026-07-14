# Experiment 39 — one non-vacuous Beautiful Loop agent

**Date:** 2026-07-14

## Missing conjunction

Experiment 33 combined a hierarchical precision hyper-loop with epistemic
action, but its binding result collapsed to ordinary evidence pooling under a
fair control. Experiment 34 introduced genuinely joint binding, but used fixed
sampling and no temporal change. The missing test was one agent in which joint
binding, residual-driven precision recursion, and action were all load-bearing.

## Construction

A binary scene cause $g$ and three binary local causes have the prior

\[
p(z_1,z_2,z_3\mid g)\propto
\exp\{0.10g(z_1+z_2+z_3)+
1.50g(z_1z_2+z_1z_3+z_2z_3)\}.
\]

The first term gives each local cause nonzero information about the scene
($I(g;z_j)=0.0133$ nats). The second creates additional evidence in relations
among causes. This avoids both earlier easy cases: conditionally independent
pooling and parity with exactly uninformative local marginals.

Every local cause generates the same explicit three-level Gaussian branch used
in the Beautiful Loop hierarchy. A global nine-component precision field is
forecast from context, used in state inference, corrected from posterior
residual moments, and rebroadcast before the next action. The policy chooses
two distinct branches sequentially by expected reduction in scene entropy
under a precision-sensitive binary-sensor approximation. Each choice acquires
four observations.

The controls receive the same generated worlds:

- `factorized_replay` removes the relational interaction but preserves its
  exact local marginals, then replays the full agent's exact actions and data;
- `random` retains the relational model but chooses two distinct branches at
  random with the same budget; and
- `precision_blind` retains the relational model and entropy policy but treats
  every branch as equally reliable.

## Honest iteration record

The first pilot reused the three-way parity interaction from Experiment 34. It
produced exactly zero relational gain because observing only two causes leaves
the unobserved cause to marginalize the parity term away. A pairwise relational
factor made the joint term visible, but two observations per chosen branch
produced gains of only `0.006--0.027`, below the declared `0.030`. A
three-observation setting passed a five-seed screen and failed the full ten-seed
pilot (`0.021`, 6/10 wins). The final candidate increased evidence, not model
complexity: four observations per selected branch, local field `0.10`, and
relational field `1.50`. No criterion was weakened.

## Exploratory results

Across pilot seeds `13001:13010`:

| Measure | Full | Control |
|---|---:|---:|
| Held-out scene accuracy | 0.782 | 0.723 factorized replay |
| Held-out scene accuracy | 0.782 | 0.704 random |
| Held-out scene accuracy | 0.782 | 0.713 precision-blind |
| Relation-preserving accuracy | 0.794 | 0.729 factorized replay |
| Relation-violating accuracy | 0.502 | 0.557 factorized replay |
| Mean branch packets | 2.000 | 2.000 random |

The joint-binding gain won 8/10 seeds and the action gain won 10/10. Before the
context switch the full policy chose the predicted reliable channel first in
100% of held-out episodes; afterward it chose the oppositely loaded channel in
100%. The precision-blind policy chose that post-switch channel only `3.8%` of
the time. All six exploratory criteria passed.

## Interpretation boundary

This is the first construction in the sequence where the three relevant
operations coexist and affect behavior. The factorized replay isolates the
relational term on identical data; random action isolates policy at identical
budget; the blind policy isolates precision-sensitive reallocation.

It remains an authored toy. The relational family is supplied rather than
learned, the policy uses an expected-information-gain surrogate rather than
exact expected free energy under the continuous model, the precision loading
basis is given, and free-energy descent is enforced by line search. These
exploratory seeds were used to select the final evidence packet and interaction
strengths. A separate frozen seed block is required before any conjunction
claim enters v11.
