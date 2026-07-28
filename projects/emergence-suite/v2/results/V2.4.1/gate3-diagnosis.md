# V2.4.1 Gate-3 diagnosis

Status: **diagnosis only**. No engine, parameter, criterion, protocol,
contract, prior-stage artifact, seal, or escrow block was changed or
accessed. Fresh probes use seeds `780000:780129`, all below `800000` and
disjoint from the V2.4/V2.4.1 protocol blocks and the permanently barred
diagnosis blocks `774000:774524` and `776000:776144`. These probe seeds are
descriptive and must not be used for later criterion evaluation.

## Executive findings

1. **Control-world selectivity is not another 32-slice information
   shortage.** All Gate-3 composition and bridge controls used 32 slices,
   while amended Gate 2 used 96. At 96 slices, however, shuffled-control CS
   selection rose from `0.575` to `0.725`; fixed-context selection remained
   `0.375`, far above `0.10`. In a stratum-balanced formed-bank probe,
   shuffled and nominal single-regime CS rates were `0.733` and `0.367`.
   CS is exploiting structure that the controls leave in place.
2. **Assay-3 matching is a pure feasibility-yield failure.** The procedure
   exhaustively considers all four alternative families. The frozen
   `0.05` complexity-distance tolerance is binding; neither search budget
   nor an adverse held-out margin explains the low yield.
3. **The Assay-8 negative transfer does not diagnose context-indexed
   isolation.** The implemented transfer is a global root-posterior change
   relative to a fixed-G readout. Root evidence is generated from a random
   root state independent of the banked root posterior and is never indexed
   by inferred context. The nominal single-regime arm is not the transfer
   comparator. The sign therefore reflects the direction of random global
   root evidence, not then/now re-indexing.

## 1. Control-world information adequacy

### Frozen lengths

The V2.4.1 amendment changed only Gate-2 recovery:

- Gate-2 recovery: **96 slices**.
- Assay-3 held-out worlds: **32 slices**.
- Assay-6 genuine worlds and their shuffled/fixed controls: **32 slices**.
- Assay-8 genuine, shuffled, and nominal single-regime arms: **32 slices**.

This follows directly from the call graph. `recovery_assay` supplies
`gate_2_recovery_length=96`; `_composition_world` calls `generate_world`
without a length argument, so it receives the still-frozen
`primary_length=32`. Both control transforms preserve that length.

### Paired 32/96 diagnostic probe

Seeds `780000:780039` generated context-split worlds with no missing
observations. For each seed, the 32-slice world is an exact prefix of its
96-slice counterpart. The same frozen shuffled and fixed-context
transformations were then applied, with all five candidate families
competing.

Rates have Wilson 95% intervals.

| control | 32-slice CS selection | 96-slice CS selection | mean paired change in `q(CS)` |
|---|---:|---:|---:|
| shuffled | 23/40 = 0.575 (0.422, 0.715) | 29/40 = 0.725 (0.572, 0.839) | +0.1415 |
| fixed-context / nominal single-regime | 17/40 = 0.425 (0.285, 0.578) | 15/40 = 0.375 (0.242, 0.530) | -0.0999 |

The 96-slice selected-family counts were:

- shuffled: GW 0, CL 2, **CS 29**, DR 8, CP 1;
- fixed-context: GW 11, CL 0, **CS 15**, DR 7, CP 7.

The same probe was repeated with 30 bitwise bank initial conditions, ten per
moderate/strong/very-strong stratum, and fresh seeds `780100:780129`.
Bank state is not supplied to temporal-family inference, so this is also an
explicit check that the control-selection result is invariant to the bank
initial condition:

| formed-bank control, 96 slices | CS selection | mean `q(CS)` |
|---|---:|---:|
| shuffled | 22/30 = 0.733 (0.556, 0.858) | 0.6969 |
| nominal single-regime | 11/30 = 0.367 (0.219, 0.545) | 0.2708 |

The single-regime rates by bank stratum were `0.20/0.40/0.50`; shuffled
rates were `0.80/0.70/0.70`. These apparent stratum differences cannot be
mechanistic effects of the initial states, because those states never enter
the family scorer; they are finite-sample differences among the ten seeds
assigned to each stratum.

**Conclusion:** accumulated evidence does not move these controls toward the
`0.10` ceiling. Shuffled controls become more CS-favoring. Fixed controls
decline modestly but remain several times the ceiling. The Gate-2
information-budget diagnosis does not propagate to this failure.

### Where CS obtains evidence in control wins

For the first five 96-slice CS wins in each control, exact channel-level
Shapley values were computed from all eight subsets of the candidate-common
outcome (`Y`), marker (`X`), and root (`R`) channels. This decomposition is
order-independent and recombined the full CS-versus-best-alternative
prequential log BF within `2.0e-15`.

| control CS wins | mean total CS log BF | outcome contribution | marker contribution | root contribution |
|---|---:|---:|---:|---:|
| shuffled, n=5 | +2.4398 | **-5.7563** | **+8.1961** | 0.0000 |
| fixed-context, n=5 | +0.1565 | **+3.0893** | **-2.9328** | 0.0000 |

For shuffled wins, CS had *worse* expected log likelihood than the best
alternative by `-10.3081` nats, but its posterior/path complexity was lower
by `12.7479` nats. The exact evidence identity is

`log BF = expected-log-likelihood difference - complexity difference`

`       = -10.3081 - (-12.7479) = +2.4398`.

Thus shuffled CS wins are not supplied by the outcome-context association
that the shuffle was intended to test. They are supplied by the marker
channel and a larger reduction in posterior/path complexity than the loss
in fit. The within-cue shuffle destroys marker–outcome pairing but preserves
realized marker marginals and can leave finite-sample temporal/noise
patterns. The learnable CS path absorbs those patterns. This is evidence of
a flexibility/control-accounting problem, not a normalization artifact:
all candidate rows normalize and the prequential partition identities pass.

For fixed-context wins, the opposite occurs. Constant `now_marker` evidence
favors CP over CS, but outcomes favor CS enough to leave a small positive
balance. Apparatus-first, `_fixed_context_control` changes only the marker:

`marker := now_marker`

It leaves untouched the outcome series generated by a recurrent
context-split latent process. The nominal “single-regime” arm is therefore
not single-regime in its outcomes. CS legitimately recovers the recurrent
outcome structure that the transformation preserved.

### Control-world failure classification

Two distinct issues must not be pooled:

1. **Fixed/single-regime realization — repair-class candidate.** The code's
   marker-only rewrite does not realize the plan's named “single-regime
   global corrective evidence” arm. Whether this is adjudicated as pure
   software/protocol-realization error is for the evaluator, but it is not
   repaired here.
2. **Shuffled-control construct — pilot-amendment/theory-definition
   candidate.** The implemented shuffle faithfully destroys the declared
   marker–outcome pairing while preserving marginals, but the CS family can
   infer a temporal path from marker noise or outcomes separately. If the
   intended null is “no genuine reusable context,” the public control must
   specify which temporal sufficient statistics must also be neutralized or
   matched. Changing that null is an analysis-plan amendment, not an engine
   patch.

## 2. Assay-3 matching power

### Implemented matcher

For every 32-slice held-out world:

1. the first 24 slices form the pre-held-out posterior;
2. each family's total posterior/path complexity is divided by 24;
3. for generating family `h`, every one of the other four families is
   declared matched when
   `|C_g - C_h| <= 0.05` nats per pre-held-out observation;
4. the held-out margin uses the best-scoring member of that already-frozen
   matched set.

There is no stochastic search and no search-budget parameter. All four
alternatives are exhaustively scored. The population is exactly 80 worlds
per generating family.

### Feasibility geometry

| truth | matched at 0.05 | nearest-gap median | empirical gap needed for 60/80 | nearest family on most worlds |
|---|---:|---:|---:|---|
| GW | 45/80 | 0.04561 | **0.06602** | CS, 61/80 |
| CL | 80/80 | 0.01458 | 0.01929 | DR, 79/80 |
| CS | 60/80 | 0.02865 | 0.04975 | GW, 55/80 |
| DR | 80/80 | 0.01394 | 0.02227 | CL, 76/80 |
| CP | 3/80 | 0.09921 | **0.11908** | CS, 71/80 |

GW's pre-held-out complexity ranged `0.1577–0.3705`, median `0.2817`;
CS's score on those same worlds ranged `0.1201–0.3380`, median `0.2336`.
Their regions overlap, but not enough for 60 matches inside a `0.05` band.

CP's complexity ranged `0.0262–0.2181`, median `0.08095`. Its nearest
competitor was CS on 71/80 worlds, but CS complexity on CP worlds had median
`0.1968`. Only three realized gaps were at most `0.05`. The observed CP
matching yield is `0.0375` (Wilson 95% interval `0.0128–0.1045`); GW yield
is `0.5625` (`0.4534–0.6659`).

The positive held-out margins do not change this localization. They are
computed only for the selected feasible subset:

- GW: 45 matches, mean margin `0.1796`, 95% interval
  `0.1085–0.2538`;
- CP: 3 matches, mean margin `0.0926`, interval `0.0600–0.1474`.

### Binding parameter

- **Tolerance:** binding. An empirical tolerance of `0.0661` would include
  60 GW worlds; CP would require approximately `0.1191`. These are
  diagnostic coordinates, not proposed thresholds.
- **Search budget:** not binding and in fact nonexistent; the four
  alternatives are exhaustively enumerated.
- **Population size:** affects interval precision and absolute count, but
  not the feasibility proportion. At the observed yield, roughly 1,600 CP
  worlds would be needed merely to accumulate 60 rare matches, which would
  still be a selected 3.75% subset rather than the frozen 60/80
  matched-population claim.

**Failure class recommendation — pilot-amendment needed.** The matching
estimand and its power gate are internally incompatible for CP at the
frozen tolerance. A future public amendment must decide prospectively
whether to change the complexity coordinate, construct matched world
strata, widen the tolerance from an independent attainable-range
calculation, or replace subset matching with an adjustment that reports the
whole population. This is not an engine repair, and none of the diagnostic
coordinates above may be used as both calibration and evaluation data.

## 3. Assay-8 negative transfer

### (a) Wiring and sign convention

The implemented chain is:

1. load a banked `root_posterior` and untreated-cue association;
2. generate a 32-slice CS world whose binary `root_state` is newly sampled
   with probability 0.5, independently of the banked root posterior;
3. update one global root posterior from every nonmissing root observation
   using reliability 0.85;
4. compute
   `now_after = 0.5 + association*(q_final(G=1)-0.5)`;
5. compute
   `fixed_g_now = 0.5 + association*(q_initial(G=1)-0.5)`;
6. report `transfer = now_after - fixed_g_now`.

The arithmetic sign is not inverted: positive means the observed stream
moved the associated untreated-cue prediction upward relative to holding
the initial G posterior fixed. But the baseline is **fixed G**, not the
single-regime/global-revision arm. Shuffling or fixing context markers does
not change the root tokens, and the transfer calculation is not performed
as a genuine-minus-control contrast.

One negative world makes the wiring concrete:

| field | value |
|---|---:|
| protocol seed / bank seed | `779001` / `820002` |
| bank stratum | strong |
| initial `q(G=1)` | 0.576726 |
| independently generated root state | 0 |
| root observations | 23 zero, 9 one |
| final `q(G=1)` | `3.87e-11` |
| association | 0.849558 |
| `fixed_g_now` | 0.565183 |
| `now_after` | 0.075221 |
| reported transfer | **-0.489962** |

Across all 120 Gate-3 bridge worlds, 62 generated root state 0 and 58
generated state 1. Mean transfer was `-0.5236` in root-0 worlds and
`+0.2342` in root-1 worlds; root-state/transfer correlation was `0.874`.
Only 48.3% of worlds had positive transfer. The aggregate negative interval
is therefore explained by randomly directed root evidence acting on bank
states whose mean initial `q(G=1)` was already `0.6909`.

The plan's exact operative text was:

> “present-context root-mediated transfer `>=.05` with lower 95% bound
> `>0`”

and the contract says:

> “Revision of `G` changes untreated-cue posterior predictions in the
> inferred `now` context”

The preregistered positive direction is coherent only if the
“witnessing-style corrective evidence” is prospectively oriented to revise
G in that declared direction. The implementation instead samples its root
truth independently. This is a world-construction/wiring mismatch, not a
mere subtraction typo.

### (b) Mechanism routing

Corrective root evidence does **not** land in a THEN-specific posterior:

- `_root_update` accepts only the current root posterior and a binary root
  observation;
- it never receives the marker, latent context, CS posterior, or arm;
- every root observation updates one global G posterior;
- `then_after` is set directly equal to `then_before`;
- `now_after` alone reads the updated global root.

Thus historical retention is imposed by the readout assignment
`then_after = then_before`, while present prediction reads the globally
updated root. There is no inferred context-indexed root table and no
mechanism by which revision is routed to THEN rather than NOW.

The topology partially resembles V2.2.1: changing G is transmitted through
a learned cue-root association, and setting association to zero makes the
transfer exactly zero. But V2.2.1's correction stream was constructed to
move G in the preregistered direction; it measured
`probe(G_after)-probe(G_before)`. V2.4.1 supplies randomly directed root
evidence independent of the banked state. The mediation topology survives,
but the corrective-evidence semantics do not.

The V2.3.2 frozen sign table concerns one-slice evidence among T/D/P
formation candidates over event, precision, control, broadcast, danger,
and masking cells. It contains no V2.4 context-indexed G-transfer sign.
It can establish evidence neutrality and candidate-BF directions within
formation; it cannot validate this bridge's positive or negative transfer
direction. The present routing therefore cannot be defended as following
that sign table.

**Mechanism conclusion:** the negative aggregate is not evidence that
revision was correctly indexed to THEN. Evidence is globally routed, and
its sign is dominated by a new random root truth.

### (c) Theory exposure

If a correctly implemented, genuinely context-indexed comparison still
produced a negative genuine-minus-global contrast, its meaning would be:

**“re-indexing isolates revision to the historical context and reduces
present-context generalization relative to global revision.”**

That would refine—or contradict—the frozen plan's preregistered positive
present-context transfer direction. It could be a scientifically coherent
redescription result: preserving an old-context model may prevent a
historical correction from becoming globally current. It could also violate
the intended claim that shared-root revision transfers within the inferred
present context. The current run cannot decide between those theories,
because it never computes that contrast and never context-indexes G.

### Transfer failure recommendations

These recommendations are deliberately separated:

1. **Wiring/world-construction: repair-class adjudication needed.** Determine
   whether independent random root truth, the absence of a context input to
   root revision, and the fixed-G rather than global-revision comparator are
   implementation failures relative to the frozen contract. If so, this is
   a repair with invalidate-and-repeat provenance, not a threshold
   amendment.
2. **Estimand direction: theory-adjudication-needed.** Before any repair,
   choose whether the scientific contrast is (i) positive within-present
   transfer versus fixed G, or (ii) genuine context indexing versus
   single-regime global revision. Those are different questions. The
   existing result answers only the first under randomly directed evidence.
3. **No result-contingent sign change.** The positive threshold must not be
   reversed merely because this run was negative. Any new direction must
   follow a public theory adjudication and be frozen before fresh worlds.

## 4. Recommendation matrix

| failure | apparatus finding | provenance class | independent recommendation |
|---|---|---|---|
| shuffled control selectivity | CS gains marker-channel evidence and lower path complexity after the declared shuffle | **pilot amendment / theory-definition** | specify the null's temporal sufficient statistics and construct controls that remove or match all context-diagnostic structure; evaluate on fresh worlds |
| fixed/single-regime selectivity | marker is fixed but CS-generated recurrent outcomes remain | **repair-class candidate** | adjudicate whether the named arm was misimplemented; if authorized, repair the arm constructor without changing candidate scoring |
| GW/CP matching power | exhaustive matcher; `0.05` tolerance excludes most feasible comparators | **pilot analysis amendment** | prospectively redesign the complexity match or whole-population adjustment; do not tune to `0.0660/0.1191` on these data |
| negative formed-bank transfer | global randomly directed root update versus fixed G; no context-indexed G and no global-revision comparator | **repair-class adjudication plus theory-adjudication-needed** | adjudicate wiring first, then separately freeze which theoretical contrast and direction is claimed |

None of these recommendations depends on making the failed result pass.
They follow from the implemented data flow, exact evidence decomposition,
and feasibility geometry. No repair or amendment is made in this diagnosis.
