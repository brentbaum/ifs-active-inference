# DT-S1-IDGEN design freeze

Frozen on 2026-08-04 before any criterion seed. Scientific target: frozen
V3.6. Code-audit standing: **2**; S1-B/C are architecture-conditional.

## Seed cells

| Sub-test | Seeds | Worlds per family / pairing |
|---|---|---:|
| S1-A identity-coupled therapy | `3790000:3791999` | 2,000 |
| S1-A exposure-rational control | `3792000:3793999` | 2,000 |
| S1-B three-arm paired lesion table | `3794000:3795499` | 1,500 seeds, all arms per seed |
| S1-C 2x2 plus comparator | `3795500:3797999` | 2,500 seeds, all four cells and both models per seed |
| S1-D four danger families | `3798000:3799999` | 500 per family |

All 10,000 seeds are used exactly once, ascending and gap-free. Within-seed
contrasts reuse component streams.

## S1-A: evidence-equivalent event thresholds

`t_G` and `t_Y` are first crossings of cumulative posterior log Bayes factors.
Before criterion scoring, an exact zero-seed prior-predictive enumerator visits
all `2^8` token strings under the candidate-common binary reference channel
`p(o=1|h=1)=0.84`, `p(o=1|h=0)=0.16`, with uniform hypothesis prior. Candidate
thresholds are the positive attainable absolute cumulative log-BF values. The
chosen threshold is the value whose exact probability of a crossing by slice 8
is closest to `0.75`; ties select the smaller value. The same rule is run under
the labels `G` and `Y`; validity requires exactly equal thresholds and crossing
probabilities. Thus `b_G` and `b_Y` express identical evidence strength without
criterion seeds or differently scaled posterior cutoffs.

Identity-coupled worlds deliver a high-diagnosticity root channel and a weak
outcome channel. Exposure-control worlds exchange those diagnosticities. The
zero-seed oracle must verify that outcome information exceeds identity
information in the control (`E log BF_Y > E log BF_G`), making outcome-first
the rational ordering there. Crossing times within one slice are simultaneous.

## S1-B: root-sharing lesion

The full query predicts an untreated identity-sharing cue by marginalizing its
frozen root-conditioned emission over `q(G)`. The support-preserving lesion
conditions the query on absence of only the shared `G -> cue` dependency.
It preserves, bitwise: delivered treated-cue tokens, cue-local beta-Bernoulli
learning, `q(G)`, outcome-token count, and treated-cue prediction. The lesioned
untreated predictive is the candidate-common prior predictive. The third arm
masks cue-local evidence to likelihood one, leaving both predictions at prior.
Restricted-prior identity, support positivity, normalization, and an independent
enumerator are blocking zero-seed proofs.

Movement is `log p_after(safe) - log p_before(safe)` with ROPE
`+/- log(1.02)`. Registered pattern: full treated and untreated positive beyond
ROPE; root lesion treated positive and untreated within ROPE; cue-local removal
both within ROPE.

## S1-C: orthogonal cue construction and comparator

Each seed constructs all four combinations of:

- identity-parent sharing: no / yes;
- perceptual similarity: no / yes.

The dimensions are independent metadata in the generator and are never
collapsed into one flag. V3.6 queries use identity-parent sharing only. The
matched associative comparator is an apparatus-only exact beta-Bernoulli model
fit to the same treated tokens and the same held-out safe token; it shares its
learned cue parameter only along perceptual similarity and has no identity
variable. Both models score identical observables and use normalized uniform
priors. Primary effects are paired main effects in predictive movement. V3.6:
identity-share effect greater than similarity effect. Comparator: similarity
effect greater than identity-share effect. The registered falsifier is V3.6
similarity effect greater than or equal to its identity-share effect.

## S1-D: danger families

All use the frozen V3.1 generator and exact structure posterior:

1. `persistent_external`: repeated adversity, broad precision, high control,
   real danger, effective action; correct class is danger without part-like
   identity organization.
2. `recurrent_identity_coupled`: repeated adversity, broad precision, low
   control, safe external field; correct class is part-like organization.
3. `mixed`: repeated adversity, broad precision, low control, real danger;
   correct class requires both part-like organization and `W_Y`.
4. `acute_transient`: acute adversity, broad precision, high control, safe
   external field; correct class is transient.

Each family passes only if mean correct-class posterior mass exceeds `0.5` and
more than half its worlds place majority mass on that class. Pure external also
requires mean part-like mass below `0.5`.

## New files and excess audit

Authorized additions:

- `scripts/run_decisive_s1.py` — apparatus, custody, proofs, runner, reporting;
- `scripts/s1_associative_comparator.py` — matched comparator only;
- `tests/test_decisive_s1.py` — zero-seed regression proofs;
- `results/decisive-tests/s1-*` — frozen design, proofs, traces, verdict, and
  prediction scoring.

Excess additions: **none**. Frozen `ref/v31.py` through `ref/v36.py` are not
modified. No Study-2/3 block or escrow is in scope.
