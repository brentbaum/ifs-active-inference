---
date: 2026-07-14
topic: confirm-unified-relational-agent
---

# Frozen confirmation of the unified relational agent

## Fixed architecture

Experiment 39's final pilot configuration is frozen unchanged:

- soft local field `0.10` and pairwise relational field `1.50`;
- three explicit Gaussian levels per branch;
- four observations in each of two sequentially selected branch packets;
- residual-driven updates of one global nine-component precision field;
- an entropy-reduction policy whose binary-sensor reliability comes from the
  current precision forecast;
- matched factorized replay, matched-budget random, and precision-blind
  controls.

No parameter, threshold, or observation budget may change after the new seed
block is opened.

## Primary untouched block

Seeds `14001:14020` are frozen for the primary confirmation. All of the
following must pass:

1. Local mutual information remains above `0.01` nats.
2. Full held-out accuracy exceeds factorized-replay accuracy by at least
   `0.030`, with at least `15/20` paired seed wins.
3. Full held-out accuracy exceeds matched-budget random accuracy by at least
   `0.030`, with at least `15/20` paired seed wins.
4. Relation-preserving accuracy exceeds factorized replay by at least `0.030`,
   while relation-violating accuracy is no better than factorized replay.
5. Before the context switch, channel 1 is selected first in at least 75% of
   held-out episodes; afterward channel 3 is selected first in at least 75%.
   The precision-blind policy selects channel 3 first in at most 20% afterward.
6. Full and random agents use exactly the same mean packet budget, and
   factorized replay matches the full agent's two actions in every episode.

## Stress and negative-control blocks

Eight separate five-seed blocks begin at `15011`, `15021`, ... `15081`:

- baseline;
- local field `0.08` and `0.12`;
- relational field `1.20` and `1.80`;
- three and five observations per selected branch; and
- relation-violation rate `0.10`.

A positive stress cell retains the conjunction when relational gain is at
least `0.015`, action gain at least `0.020`, the first-action channel reverses
across context, and the sample budget remains matched. At least six of eight
cells (baseline plus seven variations) must pass.

A separate zero-relation block, seeds `15101:15105`, sets the relational field
to zero. The absolute full-versus-factorized gain must be at most `0.015`, while
the precision-guided action advantage and context reversal must remain. This
tests whether the binding effect disappears specifically when the joint factor
is removed without disabling the other loop operations.

Optimization invariants, computed implementation checks, empirical criteria,
and authored assumptions are reported separately.
