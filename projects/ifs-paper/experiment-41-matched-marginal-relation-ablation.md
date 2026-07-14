# Experiment 41 — matched-marginal relation ablation

**Date:** 2026-07-14

## Why the control changed

Experiment 40's raw zero-coefficient ablation did not preserve the conditional
local marginals of the relational prior. Experiment 41 instead samples local
causes from that prior's exact factorized projection. For every branch and both
values of the global cause, `p(z_j | g)` is identical to the relational model
to numerical precision (`2.22e-16` maximum error). Only higher-order dependence
among the three local causes is removed.

Every arm also uses the factorized inference model. Full and replay therefore
have identical models, actions, and data; their equality is an implementation
identity rather than an empirical discovery. Random retains the same two-packet
budget, and precision-blind retains the same entropy policy without
channel-specific precision forecasts.

## Recycled-seed diagnostic

The first run deliberately reused Experiment 40's already-opened negative-
control seeds `15101:15105`. It is diagnostic, not confirmation.

| Measure | Full | Control |
|---|---:|---:|
| Held-out scene accuracy | 0.582 | 0.582 factorized replay |
| Held-out scene accuracy | 0.582 | 0.582 random |
| Held-out scene accuracy | 0.582 | 0.558 precision-blind |
| Mean branch packets | 2.000 | 2.000 random |

Full and replay were exactly equal and replayed both actions in every episode.
The full policy still chose channel 1 first before the context switch and
channel 3 first afterward in every held-out episode. The blind policy chose
channel 3 first only `5.5%` of the time after the switch. Nevertheless, targeted
sampling produced no mean advantage over random and won only 2/5 seeds.

## Theory update

This is not a reason to weaken the action criterion. It suggests that the
action advantage in Experiments 39--40 is relationally enabled. Under a
two-of-three sampling budget, random sampling is already adequate when each
branch contributes only its weak marginal cue. Higher-order dependence makes
*which combination* of branches is observed consequential; precision-guided
selection then becomes instrumentally valuable.

The revised prediction is an interaction: the precision policy should continue
to reallocate in both worlds, but its accuracy advantage should be large in the
relational world and negligible in the exact matched-marginal factorized world.
That prediction requires a fresh paired seed block.
