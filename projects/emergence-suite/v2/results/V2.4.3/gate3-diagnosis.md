# V2.4.3 Gate-3 decomposition diagnosis

Status: **diagnosis only**. No engine, likelihood, transition, prior,
threshold, protocol, or criterion was changed. No new seeds were opened.
The analysis reuses retained Gate-3 worlds and descriptively regenerates
the already-consumed Gate-2 block `787000:787499` at its frozen 96-slice
length. It does not alter either verdict.

Supporting per-world decompositions:

- `gate3-diagnosis-shuffled-per_world.csv`
- `gate3-diagnosis-bma32-per_world.csv`
- `gate3-diagnosis-bma96-per_world.csv`
- `gate3-diagnosis-cs-margins-per_world.csv`

Both finite-information bounds remain explicit and unchanged:

- `B_max_inherited_formation = 3.801426508560692`
- `B_max_v24_common_emissions = 6.704414354964107`

## 1. Shuffled-control material redescription

### What the constructor actually destroys

`_shuffle_marker_association` groups observations by cue and independently
permutes that cue's complete outcome vector and marker vector over all of
its occurrences. It preserves:

- cue order;
- each cue's global outcome marginal;
- each cue's global marker marginal;
- missingness counts; and
- root tokens.

It destroys:

- the original marker–outcome pairing;
- systematic alignment of either permutation with the original latent
  context schedule; and
- the original temporal order of outcomes and markers within each cue.

It does **not** preserve per-slice or context-conditioned marginals.
The latent context path is not supplied to the scorer. Root tokens retain
their original schedule, but the CS path likelihood uses the
candidate-common root predictive, so root evidence cancels from the
one-versus-two-context path odds.

The conditional-product shuffle therefore does instantiate its named
independence null. It does not secretly leave the original recurrent
context structure in place. However, independent finite permutations can
realize accidental marker/outcome sequences that are strongly fit by a
two-context CS path. The posterior is coherent for those realized streams;
the population-level `<=0.10` ceiling fails because such chance sequences
occur in `45–47%` of these null worlds.

### Path-class decomposition

All classification uses the 24-slice pre-held-out prefix. Its exact CS
two-context prior mass is constant:

`pi1 = 0.92741935483871`.

The `BF >= 4` condition therefore remains essential: high `q1` alone would
mostly reproduce a switching-favoring prior.

| population | material | n | mean `q1` | mean BF | minimum-context occupancy | posterior `P(then→then)` | posterior `P(now→now)` |
|---|---:|---:|---:|---:|---:|---:|---:|
| neutral | no | 66 | 0.8754 | 5.88e5 | 0.2328 | 0.7735 | 0.7764 |
| neutral | yes | 54 | **0.9993** | **2.42e7** | **0.3704** | 0.7156 | 0.7173 |
| formed bank | no | 64 | 0.8019 | 6.67e4 | 0.2013 | 0.7791 | 0.7905 |
| formed bank | yes | 56 | **0.9988** | **2.28e6** | **0.3318** | 0.7305 | 0.7170 |

“Minimum-context occupancy” is the smaller exact expected occupancy divided
by 24, reconstructed from posterior transition-count row sums plus the
final-context posterior. Material worlds genuinely place substantial
posterior mass in both contexts. Their lower self-transition means show
that this is switching/recurrence evidence, not a nearly constant path
barely touching the second context.

The per-world file publishes `q1`, `BF`, `pi1`, all four posterior expected
transition counts, transition means, and occupancy for every shuffled
world that did and did not pass.

### Which cue statistics carry the signal

| population | material | cue outcome contrast: then-marker minus now-marker | marker-aligned cue log signal | first-half minus second-half cue contrast | marker switch rate |
|---|---:|---:|---:|---:|---:|
| neutral | no | -0.0794 | 1.508 | +0.0404 | 0.499 |
| neutral | yes | **+0.1448** | **4.345** | -0.0201 | **0.599** |
| formed bank | no | -0.1145 | 2.071 | +0.0247 | 0.503 |
| formed bank | yes | **+0.2151** | **5.754** | -0.0372 | **0.567** |

The dominant separation is cue-specific outcome alignment with the
independently shuffled context markers. Material worlds happen to put more
positive outcomes under `then_marker` and more corrective outcomes under
`now_marker`; the exact CS likelihood appropriately reads this as
two-context evidence. They also contain more marker switching and yield
more balanced occupancy. The near-zero first/second-half contrasts show
that the original broad then/now schedule is not what survives.

**Construct answer:** the generator destroys the intended systematic
two-context structure. The false-redescription rate is instead generated
by finite-null realizations that accidentally contain the very cue/marker
statistics the material readout defines as two-context evidence. Thus the
posterior is correct conditional on individual realized streams, while the
absolute ceiling is not met by this null/readout combination. This is not a
hidden formed-state effect: neutral and formed-bank decompositions are the
same phenomenon.

## 2. BMA regret

### 32-slice worlds: posterior dilution

The frozen split supplies only 24 pre-held-out slices and 8 held-out
slices. Family-weight entropy and generating-family weight before the
held-out suffix were:

| truth | mean entropy (nats) | mean truth weight | off-truth weight | mean regret |
|---|---:|---:|---:|---:|
| GW | 0.9999 | 0.4062 | 0.5938 | 0.01219 |
| CL | 0.9967 | 0.4101 | 0.5899 | 0.01424 |
| CS | 0.5764 | 0.6637 | 0.3363 | 0.02154 |
| DR | 0.8443 | 0.4869 | 0.5131 | 0.01434 |
| CP | 0.6147 | 0.7570 | 0.2430 | 0.02141 |

The weights are not concentrated even though the families are recoverable
at 96 slices. The principal off-truth weight and its mean true-minus-
comparator held-out gap, in nats/token, were:

| truth | principal absorbers: mean weight (`true − comparator` gap) |
|---|---|
| GW | CL 0.293 (`+0.0226`), DR 0.230 (`+0.0394`) |
| CL | GW 0.253 (`+0.0230`), DR 0.227 (`+0.0295`) |
| CS | CP 0.188 (`+0.3336`); GW/CL/DR each about 0.05 (`+0.123–0.165`) |
| DR | GW 0.218 (`+0.0990`), CL 0.216 (`+0.0482`) |
| CP | CS 0.157 (`+0.0576`) |

GW, CL, and DR mainly dilute one another through large weights on nearby
families with modest but positive held-out gaps. CS and CP usually have
more concentrated posteriors, but their remaining off-truth mass can sit
on a comparator that predicts the short suffix much worse. Exact
log-sum-exp then produces positive generator-family regret without any
held-out feedback into the weights.

### Existing Gate-2 worlds at 96 slices

The same descriptive calculation was applied to all 500 already-consumed
Gate-2 worlds: 72 pre-held-out slices and 24 held-out slices.

| truth | entropy 32 → 96 | truth weight 32 → 96 | regret 32 → 96 | descriptive 96-slice bootstrap CI |
|---|---:|---:|---:|---:|
| GW | 1.000 → 0.662 | 0.406 → 0.637 | 0.01219 → **0.00456** | 0.00016–0.00868 |
| CL | 0.997 → 0.624 | 0.410 → 0.638 | 0.01424 → **0.00389** | 0.00035–0.00737 |
| CS | 0.576 → 0.055 | 0.664 → 0.967 | 0.02154 → **-0.00034** | -0.00331–0.00197 |
| DR | 0.844 → 0.369 | 0.487 → 0.724 | 0.01434 → **0.00737** | 0.00234–0.01275 |
| CP | 0.615 → 0.166 | 0.757 → 0.945 | 0.02141 → **0.00109** | 0.00032–0.00207 |

Regret shrinks for every family as entropy falls and generating-family
weight rises. Four descriptive upper bounds fall below `.01`; DR's mean is
also below `.01`, although its upper bound remains `0.01275` because a
minority of DR worlds remain ambiguous.

**Answer:** the across-family Gate-3 failure is primarily finite-information
posterior dilution at the 24-slice prefix, not persistent model-average
miscalibration. The same exact BMA becomes nearly generator-equivalent
when existing worlds supply three times as much pre-held-out evidence.
DR retains a localized long-tail ambiguity, so the descriptive comparison
does not establish perfect calibration for every family; it does reject a
general failure of the mixture calculation.

## 3. CS matched margin

The CS population had **79/80 matched worlds**, exceeding the frozen
`60/80` power requirement. The missing world had no comparator within the
frozen `0.13` pre-held-out complexity tolerance and was not assigned an
invented margin.

| statistic | margin, nats/token |
|---|---:|
| mean | 0.03438 |
| SD | 0.16530 |
| 5th percentile | -0.18480 |
| median | 0.01585 |
| 95th percentile | 0.38525 |
| minimum / maximum | -0.30117 / +0.47281 |

Best already-matched comparator:

| comparator | worlds |
|---|---:|
| GW | 33 |
| CP | 24 |
| DR | 13 |
| CL | 9 |

The distribution is broad and two-sided. The five lowest margins ranged
from `-0.3012` to `-0.1813`; the five highest ranged from `+0.3852` to
`+0.4728`. Both tails involve several worlds and multiple comparators.

Leave-one-out whole-world bootstrap diagnostics:

- LOO mean range: `0.02876–0.03869`;
- LOO lower-bound range: `-0.00589–+0.00350`;
- LOO upper-bound range: `0.06422–0.07564`.

No single world creates the positive mean: omitting any one leaves it at
least `0.0288`. But individual extremes can move the lower bootstrap bound
across zero, so the original `[-0.00068, 0.07080]` interval width is driven
by genuine between-world heterogeneity in a small number of tail worlds,
not by inadequate matching yield. The criterion failure is specifically
uncertainty in the population advantage, not a zero or negative central
estimate.

## Diagnostic conclusion

The three failures have distinct apparatus explanations:

1. The shuffled constructor implements its independence null, but finite
   permutations frequently create marker-aligned cue statistics that
   legitimately support both-context occupancy under the current exact
   path model.
2. BMA regret is mostly short-prefix posterior dilution and collapses with
   the existing 96-slice information budget; DR retains a smaller
   long-tail ambiguity.
3. The CS point margin has adequate matching and a positive central
   estimate, but a wide, two-sided world distribution leaves its lower
   interval just below zero.

No repair or criterion change is proposed here. External adjudication is
required.
