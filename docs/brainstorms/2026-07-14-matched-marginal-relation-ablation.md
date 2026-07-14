---
date: 2026-07-14
topic: matched-marginal-relation-ablation
---

# Matched-marginal relation ablation

## What failed

Experiment 40 set the relational coefficient to zero while leaving the local
coefficient at `0.10`. That removed joint dependence, but it did not preserve
the original conditional local distributions. The relational interaction also
changes `p(z_j | g)`, asymmetrically across the two values of `g`. The control
therefore weakened the local classification problem at the same time that it
removed relational binding.

## Approaches considered

1. **Keep the raw zero coefficient.** This preserves parameter-count
   simplicity but repeats the confound already exposed by Experiment 40.
2. **Retune one local coefficient to match mutual information.** One scalar can
   match a summary such as mutual information, but cannot match both
   `p(z_j=1 | g=1)` and `p(z_j=1 | g=-1)` because the relational prior makes
   them asymmetric.
3. **Use the existing exact factorized projection.** The factorized prior
   already multiplies the relational model's three exact conditional local
   marginals. Sampling worlds from this projection and giving every agent the
   same factorized inference model removes only higher-order dependence.

Approach 3 is the simplest valid control. It adds no learned parameters and no
new probability family.

## Fixed comparison

- Keep the original global-cause prior, conditional local marginals, Gaussian
  hierarchy, precision field, context switch, packet size, and two-action
  budget.
- Generate local causes from the exact factorized projection of the original
  relational prior.
- Give full, replay, random, and precision-blind arms that same factorized
  scene model.
- Let the full arm retain precision-guided sequential action; replay copies its
  exact actions; random retains the exact budget; precision-blind retains the
  entropy policy without channel-specific precision.

The full-versus-replay difference must collapse, because their scene models,
data, and actions are now identical. The full-versus-random difference tests
whether epistemic action survives when relational synergy is specifically
removed.

## Sequence

First run a diagnostic on the already-opened failed-control seeds
`15101:15105`; these cannot count as confirmation. If the mechanism behaves as
specified, freeze a separate twenty-seed block before inspecting it. Do not
change the agent architecture or acceptance thresholds after that block is
opened.
