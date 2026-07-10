# Sim 8 constants and provenance (EXPLORATORY)

Inherited unchanged from Sim 1 (provenance sim1/magic-numbers.md):
learning_rate_base 0.16, learning_rate_arousal_gain 60, arousal_pe_scale 5.2,
reflexivity_arousal_slope 0.88, assimilation_capacity 1.0,
spawn_pressure_threshold 1.2, spawn_pressure_decay 0.72,
efe_flatness_threshold 0.55, preferences 1.35/-2.35, action costs 0.03/0.80,
plus Sim 1's world (formation stream, relief windows, efficacy map) imported
read-only.

| Constant | Value | Provenance |
|---|---:|---|
| episodes | (2.6,0.2,72,128), (2.2,0.35,48,96) | Two crises so stacks of >=3 causes can form; omega/kappa from Sim 1's frozen-band coordinates; acute/consolidation lengths are Sim 1's frozen schedule. Not swept. |
| internal_write_rate | 0.16 | Set equal to learning_rate_base (iteration 4 unified the write rule; a separate value was the iteration-1..3 inconsistency). |
| internal_conf_k | 4.0 | Small-sample damping for the aversion readout. Not swept. |
| block_gain | 1.0 | Neutral units; blocking magnitude comes from grown quantities (policy share x own aversion x attribution). Not swept. |
| contact_write | 6.0 | Therapy safe-evidence write per session at full access. Not swept. |
| therapy_sessions | 40 | Enough sessions for a 4-cause chain to unlock; not swept. |
| spawn_prior_count | 1.0 | Flat newborn banks. |
| attribution smoothing | 0.01 | Prevents zero-attribution division; fixed before iteration-5 run. |

All values were fixed before the run of the iteration that introduced them;
no constant was tuned against pilot outcomes (mechanism STRUCTURE was iterated
instead, which is exactly why this sim is exploratory — see README iteration
log). Anything promoted to a confirmatory cycle must re-freeze this table
first and run fresh seeds under a scaled criteria file.
