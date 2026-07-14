---
date: 2026-07-14
topic: confirm-relational-action-interaction
---

# Frozen relational-action interaction

## Prediction

The Experiment 41 diagnostic suggests that precision-guided action is not an
independent additive benefit. The policy reallocates under both relational and
factorized scene structures, but targeted branch choice becomes useful when
joint dependence makes the observed combination consequential.

## Fixed paired design

Use untouched seeds `16001:16020` in two conditions with identical local
marginals, Gaussian hierarchy, precision field, context switch, action budget,
and inference schedule:

1. **Relational:** local causes come from the original relational prior and
   agents use the relational scene model.
2. **Factorized:** local causes come from the exact factorized projection and
   every agent uses that factorized scene model.

Set the violation rate to zero in both conditions so the comparison isolates
scene dependence rather than mixing coherent and adversarial episodes.

## Frozen criteria

1. The factorized projection matches every conditional local marginal within
   `1e-12`.
2. In the relational condition, full accuracy exceeds exact-action factorized
   replay by at least `0.030`, with at least 15/20 paired wins.
3. In the relational condition, full accuracy exceeds matched-budget random by
   at least `0.030`, with at least 15/20 paired wins.
4. In the factorized condition, the absolute full-minus-random difference is
   at most `0.015`, the declared negligible-effect region.
5. The relational action gain exceeds the factorized action gain by at least
   `0.030`.
6. The full policy reverses its first channel across context in both
   conditions, while the precision-blind policy does not acquire the new
   channel after the switch.
7. Budgets remain exact, factorized replay copies both actions, computed
   structural checks pass, and every full-agent free-energy trace is
   non-increasing.

No architecture, threshold, or seed may change after this protocol is
committed.
