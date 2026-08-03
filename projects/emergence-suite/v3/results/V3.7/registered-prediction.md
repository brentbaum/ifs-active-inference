# V3.7 registered prediction (sealed BEFORE any V3.7 implementation)

Registered by the evaluator (Fable) on 2026-08-03, under Brent's
authorization "ok let's try 3.7. predict. then go." At registration time no
V3.7 code, design draft, pilot, or seed exists; the only inputs are the
retained V3.6-R1 tournament decomposition and the frozen v3.6 grammar. This
file is committed and hashed before implementation begins; it may not be
edited afterward (amendments, if any, go in a separate dated file).

## The two additions (exhaustive — nothing else changes)

- **A1 — dynamic partner process.** The partner latent is promoted from a
  static binary trait to a two-state hidden Markov process: one latent state
  per slice, one persistence parameter with a coarse prior (three values,
  spanning high persistence; exact grid fixed at design time before any
  seed). No coupling to mode/context machinery.
- **A2 — exogenous danger source.** One binary world-state channel that can
  carry danger without any active mode; prior odds fixed at design time. It
  competes with mode-generated danger in the structure posterior.

Everything else in the v3.6 grammar, scorer, and adapter is bitwise
unchanged. If implementation discovers that either addition cannot be
expressed without touching other machinery, that discovery is recorded and
this prediction stands unamended against whatever is actually built.

## Predictions (V3.7 vs V2, same tournament design, same delta = log(1.02),
fresh seeds, per-family lower95[S_V37 - S_V2] >= -delta)

Mechanism claim: the v3.6 partner/contact deficits are the information rate
of an untracked two-state chain (uniform across strata); the identity/outcome
deficits are mode-mediated misattribution of non-mode danger (concentrated in
acute_one and real_danger_adaptive).

| family | v3.6 mean_D | predicted v3.7 mean_D | predicted verdict | confidence |
|---|---:|---:|---|---:|
| partner | -0.294 | in [-0.02, +0.05] | PASS | 0.85 |
| contact | -0.240 | in [-0.05, +0.02] | PASS | 0.75 |
| identity | -0.180 | in [-0.06, 0.00] | PASS (borderline) | 0.60 |
| outcome | -0.021 | in [-0.01, +0.01] | PASS | 0.70 |
| context | +0.269 | within +/-0.03 of +0.269 | PASS | 0.90 |

Per-stratum commitments (sharper than the means):

1. The partner and contact recoveries are UNIFORM across strata (post-fix
   stratum spread < 0.05), because the missing-state explanation is
   stratum-independent.
2. Identity's recovery is CONCENTRATED in acute_one and real_danger_adaptive
   (each deficit shrinks by >= 70%); chronic_one identity stays near its
   current -0.05.
3. Outcome's acute_one deficit (-0.096) shrinks by >= 60%; the other three
   strata stay within +/-0.02 of zero.
4. Context's per-stratum pattern is preserved (three recurrent strata >=
   +0.30, acute_one within +/-0.05 of +0.03) — the additions are orthogonal
   to the context machinery.

## Falsifiers (named in advance)

- If partner improves by less than half its deficit, the missing-state
  account is wrong and the residual is a different construct (e.g., emission
  model mismatch) — no further additions are licensed by this prediction.
- If context's gain drops by more than 0.05, the additions are NOT
  orthogonal and A1/A2 as built couple into the context machinery —
  an implementation red flag even if other families pass.
- If identity fails to improve in real_danger_adaptive specifically, the
  exogenous-danger account is wrong.

## Cost declaration

V3.7 is "minimal plus two atoms": one latent dimension + one parameter (A1),
one world-state bit (A2). If the implemented diff touches more than these
(beyond mechanical plumbing), the excess must be enumerated in the design
freeze and this prediction's scope note applies.
