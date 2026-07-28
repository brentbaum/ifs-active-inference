# V2.4.2 Gate-3 diagnosis

Status: **diagnosis only**. No engine, constructor, parameter, criterion,
protocol, contract, prior-stage artifact, seal, or escrow block was changed
or accessed. The existing V2.4.2 criterion worlds were reanalyzed, and the
only fresh probes use seeds `786000:786359`. These seeds are below `800000`,
outside the barred blocks `774000:774524`, `776000:776144`,
`780000:780129`, and `781000:781499`, and disjoint from every V2.4.2
calibration and criterion block. They are permanently descriptive and may
not be used for criterion evaluation.

Supporting exact per-world files:

- `gate3-diagnosis-control-decomposition.csv` contains every Assay-7 and
  Assay-8 control world, every CS-versus-alternative comparison, the
  initial prior contribution, all 32 published per-slice log BFs, expected
  log-likelihood and complexity terms, and the recombination error. SHA-256:
  `cbf1b5bdb41e6f627fa6f1ca401ed8d7f72dd1f4f05e82f077a01bdefef07904`.
- `gate3-diagnosis-heldout-probe.csv` contains every fresh family/length
  probe world and its frozen matched-complexity held-out result. SHA-256:
  `ce189d59693e6ab174b90d9da92e64d31afc939faa2661321de56a2438306381`.

## Executive findings

1. **The formed bank does not preload context split.** The banked
   `q(P)`, root posterior, and association posterior never enter
   `compare_families`. Every arm starts from the same frozen family prior
   `(0.20,0.20,0.20,0.20,0.20)`. Its pairwise CS prior contribution is
   therefore exactly `0` nats in all 480 control-arm comparisons.
   Re-scoring every Assay-8 control stream as a neutral state gave maximum
   posterior difference exactly `0`.
2. **The Assay-7 and Assay-8 failures have the same apparatus cause.**
   In shuffled arms, the typical CS win is carried mainly by a lower
   posterior/path-complexity charge. In genuinely single-regime arms, it
   is carried mainly by predictive fit: CS can use one context table as a
   stationary cue table, while several alternatives pay for unnecessary
   dynamics. Assay-8's rates differ slightly only because it uses a
   different 120-seed stream block.
3. **The frozen `.01` held-out SESOI was not derived family by family.**
   It is half the smallest table-level Bernoulli KL, pooled across the
   design. On fresh 96-slice worlds it is criterion-level attainable for
   DR, borderline and below the mean threshold for GW, and not attained
   for CL.

## 1. Formed-state control selectivity

### Data-flow audit: what the serialized bank state contributes

The bank record is read by `_composition_world` to set:

- the initial root posterior;
- untreated-cue association reliability;
- the derived cue-root association strength;
- the direction of witnessing-style root tokens; and
- a descriptive copy of initial `q(P)`.

Temporal-family inference is then called as
`compare_families(observations)`. It receives neither the bank record nor
any of the five items above as a candidate-family prior. Root observations
are candidate-common. `compare_families` initializes every call from the
frozen uniform prior and computes

`log q(CS)/q(h) = log .20/.20`
`                    + [ELL_CS - ELL_h]`
`                    - [C_CS - C_h]`.

Thus the initial-state contribution is exactly `0` for CS versus GW, CL,
DR, and CP in every banked world. The serialized developmental history does
not contribute starting evidence to any redescription family.

This was also checked empirically. Each banked shuffled and single-regime
stream was re-submitted byte-for-byte to a neutral call to the public family
scorer. Across all 240 paired streams, the maximum absolute difference in
the five-family posterior was **`0.0`**. Selection and every evidence term
were identical.

Accordingly, the proposed phenomenon

> a formed organization prior-favors context-split interpretations of
> unstructured corrective input

is **not exhibited by this implementation**. It is not a candidate finding
from these results. There is no bank-prior evidence to overcome, so the
required corrective evidence against such a prior is `0` nats.

For completeness, the actual extra CS counterevidence required to reverse
the *final* winning comparison is the final CS log odds over the strongest
alternative:

| Assay-8 control | CS wins | median nats needed to reverse | range | 5th–95th percentile |
|---|---:|---:|---:|---:|
| shuffled | 72/120 | 1.8378 | 0.0847–9.1570 | 0.2512–6.5921 |
| single regime | 52/120 | 1.9637 | 0.0543–2.7214 | 0.1707–2.7123 |

These are accumulated likelihood/complexity advantages, not inherited
bank priors.

### Exact Assay-8 decomposition

The table compares CS to the highest-posterior non-CS family in each CS
win. “Complexity contribution” is `C_alt - C_CS`, so a positive value
favors CS. The exact identity recombined within `3.8e-14`.

| control | CS rate | mean / median ELL contribution | mean / median complexity contribution | wins with positive ELL | wins with positive complexity |
|---|---:|---:|---:|---:|---:|
| shuffled | 0.600 | +1.4214 / +0.7667 | +0.9833 / **+2.9016** | 40/72 | 50/72 |
| single regime | 0.433 | +1.4928 / **+2.9665** | -0.0216 / -1.4270 | 40/52 | 12/52 |

The strongest alternatives in shuffled CS wins were CL 24 times, CP 22,
DR 13, and GW 13. In single-regime wins they were CP 40 times, CL 8, GW 3,
and DR 1.

The repaired-null Gate-1 audit remains correct:

| exact product null | expected per-slice log BF, CS minus alternative |
|---|---:|
| GW product | -0.331920 |
| CL product | -0.447714 |
| DR product | -0.299171 |
| CP product | -0.445909 |

There is no contradiction. Those are population expectations under each
alternative's exact predictive-product null. The control assay selects the
largest integrated evidence among five overlapping temporal families on a
finite, marginal-preserving permutation of a realized CS stream. A negative
pairwise population expectation does not imply a `<=.10` finite-sample
winner rate after five-way selection. The per-world file shows that the
realized shuffled wins are usually helped by CS's lower inferred path
complexity; the single-regime wins instead reflect overlap between the CS
family's one-active-context subcase and a stationary cue process.

## 2. Assay-7 persistence

Assay 7 is neutral-state inference. `_composition_world(seed)` initializes
the inherited root to `(0.5,0.5)`, and—as in Assay 8—no root or formation
state is supplied to family comparison. Its initial pairwise prior
contribution is exactly `0` nats.

| Assay-7 control | CS rate | mean / median ELL contribution in CS wins | mean / median complexity contribution | positive ELL | positive complexity |
|---|---:|---:|---:|---:|---:|
| shuffled | 0.633 | +0.5134 / -0.0611 | +2.0746 / **+3.2626** | 38/76 | 59/76 |
| single regime | 0.417 | +1.9314 / **+3.5466** | -0.2784 / -1.4859 | 40/50 | 10/50 |

Maximum decomposition error was `4.3e-14`. In shuffled wins the best
alternative was CL 26 times, GW 18, DR 17, and CP 15. In single-regime wins
it was CP 40 times, CL 7, and GW 3.

Assay 7 and Assay 8 therefore do **not** fail for different mechanisms:

- shuffled controls fail predominantly through the relative path-complexity
  geometry of the five candidate families;
- single-regime controls fail predominantly because the one-context region
  of CS predicts these stationary cue streams well.

The `0.633/0.417` versus `0.600/0.433` rates are different finite seed
realizations of the same family scorer, not formed-versus-neutral effects.
The earlier V2.4.1 diagnosis already showed that longer histories did not
drive the old controls toward the ceiling. Those old constructor probes are
barred and are not reused as evidence about the repaired constructor here.

## 3. Assay-3 held-out margins

### V2.4.2 criterion population, 32 slices

Margins are the generating family's held-out log score minus the
best-scoring comparator within the prospectively calibrated `0.13`
nats/token pre-held-out complexity tolerance.

| truth | n | mean | SD | 5th / median / 95th percentile | `>0` | `>=.01` |
|---|---:|---:|---:|---:|---:|---:|
| GW | 80 | **-0.04957** | 0.10547 | -0.26298 / -0.02565 / 0.07939 | 0.388 | 0.350 |
| CL | 80 | **-0.02051** | 0.10741 | -0.20982 / 0.01108 / 0.09963 | 0.538 | 0.525 |
| DR | 80 | **+0.00192** | 0.13341 | -0.23041 / -0.01439 / 0.22038 | 0.425 | 0.400 |

GW and CL do not beat their best matched competitor on average. DR does,
but only by `0.00192` nats/token, below the `.01` SESOI and with a negative
median. The failure is therefore not merely a confidence-interval problem.

### Fresh family-specific attainable-margin probe

The same frozen generator, matching tolerance, split rule, and held-out
estimand were applied to 60 fresh worlds for each weak family at 32 and 96
slices. Bootstrap intervals use 10,000 whole-world resamples and are
descriptive.

| family | slices | matched | mean margin (95% interval) | median | `>0` | `>=.01` |
|---|---:|---:|---:|---:|---:|---:|
| GW | 32 | 60/60 | -0.05070 (-0.07305, -0.02998) | -0.03467 | 0.283 | 0.250 |
| GW | 96 | 60/60 | **+0.00902** (-0.00175, 0.01899) | +0.01948 | 0.717 | 0.600 |
| CL | 32 | 60/60 | -0.03443 (-0.05423, -0.01554) | -0.01903 | 0.400 | 0.300 |
| CL | 96 | 60/60 | **-0.00671** (-0.01724, 0.00312) | -0.00330 | 0.450 | 0.300 |
| DR | 32 | 60/60 | -0.02507 (-0.05273, 0.00492) | -0.02738 | 0.333 | 0.283 |
| DR | 96 | 60/60 | **+0.01897** (0.00328, 0.03551) | +0.01329 | 0.600 | 0.533 |

At the support level, margins above `.01` occur for all three families.
At the frozen *population-criterion* level—mean `>=.01` with lower 95%
bound `>0`—the probe supports attainability for DR only. GW improves
substantially but its mean is `0.00902` and its interval crosses zero. CL
remains negative on average.

The SESOI derivation did pool across families. The frozen plan defines
`.01` as approximately half
`KL(Bern(.6)||Bern(.5)) = .0201355`, the smallest separation between
distinct public likelihood-table rows. It did not compute the attainable
held-out advantage of GW, CL, or DR against each one's best
matched-complexity comparator. The fresh calculation shows that table-level
separation is not equivalent to family-specific attainable held-out
separation.

## 4. Recommendations by failure class

These recommendations classify the evidence; none changes a criterion or
implements a repair.

### A. Formed-state-prior hypothesis — not supported; no repair

There is no initial-state family-prior effect to repair or reinterpret.
The exact banked-versus-neutral identity is `0`, and the bank's
developmental posterior never enters redescription-family evidence.

Therefore the absolute control ceilings should **not** be removed on the
claim that formed organizations legitimately prior-favor CS: that claim is
not implemented or observed. If the theory later requires a formed
organization to alter priors over redescription families, that is a new
generative coupling and strain-version change, not a contract-fidelity
repair.

### B. Absolute ceiling versus differential — theory adjudication needed

A differential such as

`Pr(select CS | genuine then/now) - Pr(select CS | repaired control)`

would ask whether genuine context structure adds selective evidence beyond
the model's baseline tendency to choose CS. It is a coherent potential
estimand, but substituting it for the absolute `<=.10` ceilings would be a
pilot amendment that relinquishes the current false-positive guarantee.
It cannot be called a repair and should not be adopted merely because it
would pass.

Conditional clinical reading, **if a future model actually demonstrated a
formed-state prior effect**: an established protective organization would
bias ambiguous corrective experience toward contextual compartmentalization
rather than global revision. That could be read as adaptive preservation of
historical predictions or as resistance to present generalization,
depending on the genuine-versus-control differential. The present
construction supplies no evidence for that reading.

### C. Persistent control selection — structure/design adjudication needed

The repaired constructors satisfy their declared marginal and
single-regime semantics, and all normalization and recombination audits
pass. No software error is localized.

- Shuffled failures expose the relative prequential path-complexity geometry
  of the five-family comparison after finite five-way selection.
- Single-regime failures expose a real overlap: CS with one occupied
  context can behave as a stationary cue model.

If an absolute `<=.10` false-CS guarantee remains load-bearing, the
candidate-family design or complexity accounting must be changed and
revalidated as a new strain. Re-editing the null to suppress whatever CS
currently uses would repeat schedule-aware control authoring and is not
recommended.

### D. Weak-family held-out SESOI — pilot amendment or world redesign

The frozen `.01` threshold was table-derived, not family-calibrated.
Family-specific probing shows:

- DR reaches the population criterion at 96 slices;
- GW is borderline but below the mean SESOI;
- CL does not attain it.

An adjudication may either:

1. preserve `.01` and redesign prospectively generated worlds so GW and CL
   express the predictive differences the claim requires; or
2. pilot-amend the held-out requirement using an independent,
   family-specific attainable-range calculation, possibly scoring
   calibrated model-averaged regret where point-family advantage is not
   identifiable.

The fresh `786000:786359` probes are barred from evaluating either choice.
There is no basis for an engine repair, and no threshold should be selected
from these observed values and then tested on the same worlds.
