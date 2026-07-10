# T4.5 Step A report — Sim 7 one-state rebuild and pilot

## Status

- **Implementation:** PASS. Sim 7 was rebuilt around one mutable `LifeState`
  per simulated model/life. Cause banks returned by `Sim4.grow_stack`, the
  categorical depth posterior, and the learned co-regulation mapping retained
  object identity through adulthood, therapy, and held-out probing (identity
  rate 1.0 across all H1/H2 lives).
- **Pilot theory result:** **FALSIFIED** under the frozen all-success-criteria
  aggregation. The carried-capture audit passed, but adult capture prevalence,
  therapy melt prevalence, and the H2 model-comparison prediction did not.
- **Protocol:** exactly one pilot execution, seeds 1001–1010, label `pilot`, at
  `projects/emergence-suite/suite/runs/sim7/pilot/`. No constants were changed
  after observing results. No pilot rerun, confirmatory seed, or git commit was
  performed.
- **Tests:** `Pkg.test()` passed: 39/39 assertions across the six suite testsets.

## Preregistered criteria

| Criterion | Frozen standard | Pilot result | Verdict |
| --- | --- | ---: | --- |
| S7R1.bank_identity | identity rate >= 1.00 | 1.00 | SUPPORT |
| S7R1.carried_capture | childhood written-reflexivity/adult-capture correlation <= -0.25 | -0.990 | SUPPORT |
| S7R1.adult_capture | >= 6/10 H1 lives at capture >= 0.30 | 4/10 | NULL / failed threshold |
| S7R1.therapy_melt | >= 6/10 H1 lives with capture drop >= 0.08 | 4/10 | NULL / failed threshold |
| S7R1.h2_loglik | mean H1-H2 held-out advantage >= 0.02 nats/event | -0.090 | FALSIFIED (opposite direction) |
| A7R1.h2_seed_robustness | H1 wins >= 7/10 paired seeds | 3/10 | FALSIFIED |

The old S7.1–S7.4/A7.1 criteria remain in
`configs/sim7-criteria.yaml` as `dead_falsified` records and are not evaluated.
No melt-order criterion exists in R1.

## Per-seed results

`probe Δ` is post-therapy minus pre-therapy revisability under the fixed
Sim-1-style counterfactual probe. `LL Δ` is H1 minus H2 mean held-out log
likelihood on the identical adult and post-therapy world segments.

| Seed | Childhood WR | Adult capture | Captured? | Post capture | Capture drop | Melt? | Probe Δ | H1 LL | H2 LL | LL Δ |
| ---: | ---: | ---: | :---: | ---: | ---: | :---: | ---: | ---: | ---: | ---: |
| 1001 | 0.1441 | 0.9412 | yes | 0.2087 | 0.7325 | yes | -0.0144 | -1.0618 | -1.0578 | -0.0040 |
| 1002 | 0.8833 | 0.000013 | no | 0.000008 | 0.000005 | no | -0.0073 | -1.3175 | -1.3175 | 0.0000 |
| 1003 | 1.0000 | 0.000040 | no | 0.000004 | 0.000036 | no | -0.7178 | -1.4796 | -1.4796 | 0.0000 |
| 1004 | 0.7212 | 0.1403 | no | 0.0702 | 0.0702 | no | -0.0378 | -0.8531 | -0.6359 | -0.2172 |
| 1005 | 0.1200 | 0.9400 | yes | 0.2362 | 0.7038 | yes | -0.0104 | -0.7223 | -0.7639 | 0.0415 |
| 1006 | 0.8993 | 0.000011 | no | 0.000007 | 0.000004 | no | -0.0066 | -1.6418 | -1.6418 | 0.0000 |
| 1007 | 0.1555 | 0.9380 | yes | 0.1711 | 0.7669 | yes | -0.0164 | -1.0681 | -1.0991 | 0.0309 |
| 1008 | 0.7268 | 0.1212 | no | 0.0583 | 0.0630 | no | -0.0367 | -1.1139 | -0.7601 | -0.3538 |
| 1009 | 0.1323 | 0.9301 | yes | 0.2464 | 0.6837 | yes | -0.0121 | -0.5486 | -0.6665 | 0.1179 |
| 1010 | 0.7433 | 0.1069 | no | 0.0519 | 0.0550 | no | -0.0325 | -1.6603 | -1.1494 | -0.5109 |

Adult capture is sharply bimodal: the four low-written-reflexivity lives carry
strong capture, while six lives do not. Therapy lowers mean capture by 0.308,
but the mean is driven by those same four high-capture lives; prevalence is
4/10. Witnessing evidence was live in every H1 seed (mean accumulated mass
1440.82), yet fixed-probe revisability worsened in all ten seeds (mean change
-0.089). Thus the honest result is not “therapy restores revisability”: capture
melts in a minority, while the inherited high-precision banks become harder to
move under the fixed subsequent probe.

H1 beat H2 only for seeds 1005, 1007, and 1009; seeds 1002, 1003, and 1006 tied;
H2 was better for the other four. The reversed graph is therefore not the
predicted inferior model in this pilot.

## Carried versus recomputed: audit trail

### Carried and evolved

1. Childhood formation calls `Sim4.grow_stack(seed, params.sim4)` once for each
   model/life. This uses Sim 1 formation and Sim 4's de-authored access wrapper.
2. Every cause's `relational_counts`, `policy_counts`, and `mandate_counts`
   arrays are stored directly in `LifeState`. Their initial and final object IDs
   match in `bank_audit.csv`.
3. Adult adversity and triggers call the common `update_life!`: relational and
   policy evidence goes through `Sim4.update_contact!`; safe/danger evidence
   increments the existing mandate/severity bank and its carried structural
   precision.
4. The categorical depth posterior and learned co-regulation count matrix are
   initialized once, mutated in place, and retain object identity.
5. Therapy uses the same `update_life!`. Sim 5's noisy regulated signal and
   observed own-state change update the carried mapping and depth posterior.
   Sim 4 EFE chooses the contacted cause; de-authored access grades the amount
   of witnessing evidence written to that cause's existing bank.
6. Held-out adult/post-therapy events call the same update with parameter
   learning disabled. Sequential depth inference continues, but no cause or
   mapping counts are written.

H1/H2 receive identical world schedules. Their only model parameter difference
is `GraphDirection(depth_tilt_target)`: root node for H1, context node for H2.
Shared functions consume this as an array index. There are no condition-string
branches in dynamics and no H2 suppression of evidence, mapping learning, or
revision.

### Recomputed readouts only (never fed back as replacement state)

- Effective root/context precisions, capture index, and Bernoulli predictive
  likelihood are read from the current carried banks and current depth
  posterior at each event.
- The fixed probe computes a counterfactual safe-evidence response using the
  same fixed disconfirming-trial count, learning rate, written-reflexivity depth
  scale, and D1 context-share standard used by Sim 1. It does not replace or
  mutate the life bank.
- Childhood/adult/post-therapy count copies are output snapshots only.
- Contact and melt order are read from first-passage dictionaries and reported
  descriptively. No ID ordering or desired-order term enters EFE/access.

There is no formula assignment from configured `low_E`, no post-melt root-bank
replacement, and no taxonomy/route string in dynamics.

## Descriptive melt/contact order

Among H1 lives, six had no cause cross the melt threshold. Two first melted
cause 2 (seeds 1001, 1007), and two first melted cause 3 (1005, 1009). First
contact sequences varied with the de-authored EFE/access computation (for
example `1>2`, `2>3>1`, and `2>1`). This is reported without an outside-in or
formation-inversion claim, consistent with Sim 4's falsification.

## Frozen pilot-only constants

| Constant | Value | Provenance / role |
| --- | ---: | --- |
| adult learning events | 48 | Pilot-only chronic ordinary-adversity window |
| adult held-out events | 12 | Frozen Sim-3-style OOS segment |
| therapy sessions | 96 | Inherited Sim 4 upper window |
| post-therapy held-out events | 12 | Paired OOS segment |
| ordinary adversity probability | 0.68 | World schedule only |
| trigger cadence | every 6 events | World schedule only |
| trigger adversity probability | 0.90 | World schedule only |
| post-therapy safe probability | 0.82 | Held-out world generator only |
| adult write size | 1.0 | Unit evidence event |
| witnessing write size | 18.0 | Pre-pilot scale debt to reach Sim 1-grown bank mass through graded access |
| therapy safe probability | 0.92 | Sim 5 regulated reliability scale |
| adult capture threshold | 0.30 | Frozen readout |
| melt capture-drop threshold | 0.08 | Frozen absolute readout |
| carried correlation threshold | -0.25 | Frozen association readout |
| adult capture prevalence | 0.60 | 6/10 criterion |
| therapy melt prevalence | 0.60 | 6/10 criterion |
| H1 log-likelihood advantage | 0.02 nats/event | Frozen OOS criterion |
| H1 seed win rate | 0.70 | 7/10 adversarial criterion |

The complete inherited Sim 1/4/5 constants and provenance are recorded in
`configs/sim7.yaml` and `src/sims/sim7/magic-numbers.md`.

## Blockers / stop condition

- No technical blocker remains: implementation integrity and the full suite
  tests pass.
- The empirical blocker to a confirmatory Step B is substantive: adult capture
  and therapy melt occur in only 4/10 lives, fixed-probe revisability worsens,
  and H2 outpredicts H1 on average. These are recorded failures, not tuning
  targets inside this Step A.
- Per instruction, work stops here. Any redesign, amended criterion, new pilot,
  or confirmatory run requires a separately authorized preregistration cycle.
