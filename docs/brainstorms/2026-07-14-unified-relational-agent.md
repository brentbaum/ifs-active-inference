---
date: 2026-07-14
topic: unified-relational-agent
---

# One non-vacuous Beautiful Loop agent

## Problem

Experiment 33 contains temporal precision recursion and epistemic action, but
its binding collapses to ordinary pooling. Experiment 34 contains genuinely
joint binding, but sampling is fixed. A conjunction claim requires all three
operations to be load-bearing in one agent.

Parity is too easy a repair: it makes every local marginal exactly
uninformative and fixes the factorized control at chance. The new environment
instead uses a soft higher-order prior

\[
p(z_1,z_2,z_3\mid g)\propto
\exp\{\beta_1 g(z_1+z_2+z_3)+
\beta_2 g(z_1z_2+z_1z_3+z_2z_3)\}.
\]

The first term gives every local cause nonzero information about the scene; the
second adds information available only in pairwise relations. The initial
three-way parity pilot produced exactly zero relational gain because the third
unobserved cause marginalized the parity interaction away; this pairwise repair
keeps relational evidence available under the fixed two-action budget. The factorized
control receives the exact same local marginals and observations but omits the
higher-order interaction.

## Minimal unified loop

Each local cause generates the existing three-level Gaussian branch. A global
precision forecaster supplies the nine transition precisions. Within an
episode the agent chooses two distinct branches sequentially. Its policy score
is expected reduction in global-cause entropy under a binary-sensor
approximation whose reliability is computed from the current precision field.
After each choice, explicit state inference produces posterior residual moments,
the hyper-loop updates $q(\Phi)$, and the next policy reads the revised field.

Four agents share the same generated worlds:

- `full`: relational prior plus precision-guided action;
- `factorized_replay`: exact matched local marginals, replaying the full
  agent's actions and observation budget;
- `random`: relational prior with two random distinct actions; and
- `precision_blind`: relational prior whose policy treats all branches as
  equally reliable.

The first contrast isolates joint binding on identical data. The second tests
epistemic action at identical budget. The third tests whether inferred
precision actually controls reallocation across the context switch.

## Iteration rule

Pilot only on seeds `13001:13010`. The higher-order and local interaction
strengths may be adjusted during this exploratory phase, but every attempted
setting and failure must be retained in the experiment record. Once the
mechanics show nonzero local mutual information, relational gain over replay,
action gain over random, and context-sensitive reallocation, freeze the full
configuration and thresholds before opening a separate seed block.

The final pilot candidate uses $\beta_1=0.10$, $\beta_2=1.50$, and four
observations per selected branch. It was chosen after the original three-way
parity factor produced zero joint gain, two-observation pairwise screens missed
the `0.03` relational margin, and a three-observation candidate failed to
replicate from five to ten pilot seeds. The criterion was not changed.
