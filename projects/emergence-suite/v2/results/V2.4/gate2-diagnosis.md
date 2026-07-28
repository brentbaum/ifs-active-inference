# V2.4 Gate-2 diagnosis: GW / CL / DR confusion

Status: **diagnosis only**. This document changes no engine, parameter,
criterion, protocol, freeze, or sealed artifact. All additional worlds use
development seeds below `800000`.

## Verdict

The Gate-2 failure is **(b) design-limited**, with a specific finite-sample
Bayesian mechanism: the frozen 32-slice recovery worlds supply too little
information to distinguish global down-weight (GW), cue-local relearning
(CL), and continuous drift (DR) reliably. The exact posterior is usually
diffuse when the selected nuisance family is wrong, so the engine is not
discarding information that an oracle could use. But the families are not
intrinsically non-identifiable: a disjoint 96-slice probe, with all five
families still competing, raises GW/CL/DR recovery from
`0.56/0.49/0.59` to `0.80/0.80/1.00` at the frozen missingness rate.

Thus the immediate confusion is Bayes-limited **at the frozen world size**,
but the reason the preregistered `0.60` point-recovery floor failed is that
the recovery design under-expressed the families' temporal differences. The
recommended pilot amendment is a recovery-world design revision, not a
post-hoc relaxation of the recovery criterion.

## Data and computation

- Frozen recovery population: seeds `770000:770499`, 100 worlds from each
  family, 32 slices per world.
- Exact one-slice enumeration: all 36 observable tokens for each of three
  cue identities (`outcome ∈ {missing,0,1}`, four marker values, and
  `root ∈ {missing,0,1}`), with the frozen independent `0.15` masking law.
  Each family's enumerated distribution normalized to within
  `2.22e-16`.
- Finite-history information population: 25 worlds per generating family
  at each frozen supported length. Seeds were `774000:774124` for length
  16, `774200:774324` for length 32, and `774400:774524` for length 64.
  Every world's likelihood was evaluated by exact finite-state filtering.
- Design probes: 15 worlds per nuisance family. The length-96/frozen-
  missingness cell used `776000:776044`; the length-96/complete-delivery
  cell used `776100:776144`. These are descriptive probes and are not
  criterion-evaluation data.
- Intervals on mean log Bayes factors and continuous summaries are normal
  95% intervals over independent worlds. Recovery-rate intervals are
  Wilson 95% intervals. These small diagnostic populations are sufficient
  to locate the information limitation, not to qualify a repaired stage.

For a row-generating family \(f\) and column comparison family \(g\), the
reported quantity is

\[
E_f[\log BF_{f:g}]
=E_{x\sim p_f}[\log p_f(x)-\log p_g(x)].
\]

Positive values favor the generating family. One-slice values below are
exact KL divergences. Full-history expectations are Monte Carlo expectations
over generated worlds, but each history's evidence and log BF are exact.
The exponential path sum makes exact enumeration of the full history
impractical; no approximate likelihood was substituted.

## 1. Identifiability analysis

### Exact expected one-slice log BF

Values are nats per slice; rows generate and columns score.

| truth \ alternative | GW | CL | CS | DR | CP |
|---|---:|---:|---:|---:|---:|
| GW | 0 | 0.03498 | 0.27384 | 0.00831 | 0.57471 |
| CL | 0.03133 | 0 | 0.37227 | 0.06954 | 0.55519 |
| CS | 0.25675 | 0.37531 | 0 | 0.22747 | 0.73714 |
| DR | 0.00857 | 0.08014 | 0.24601 | 0 | 0.61115 |
| CP | 0.50833 | 0.49043 | 0.39029 | 0.54042 | 0 |

GW and DR are nearly indistinguishable at a single slice: their directed
KLs are only `0.00831` and `0.00857` nat. GW/CL is also weak
(`0.03498/0.03133`), while CL/DR is modestly stronger but still far below
the contrasts involving CP and most contrasts involving CS. The nuisance
families must therefore be separated mainly through repeated temporal and
cross-cue structure, not a single observation.

### Cumulative nuisance-triad log BF

| length | generating contrast | mean cumulative log BF (95% CI) | mean per slice |
|---:|---|---:|---:|
| 16 | GW : CL | 0.485 (0.194, 0.776) | 0.0303 |
| 16 | CL : GW | 0.121 (-0.236, 0.477) | 0.0075 |
| 16 | GW : DR | 0.394 (0.093, 0.695) | 0.0246 |
| 16 | DR : GW | 0.923 (0.066, 1.780) | 0.0577 |
| 16 | CL : DR | 0.529 (0.287, 0.771) | 0.0330 |
| 16 | DR : CL | 0.875 (0.278, 1.471) | 0.0547 |
| 32 | GW : CL | 0.283 (-0.234, 0.800) | 0.0088 |
| 32 | CL : GW | 1.337 (0.712, 1.961) | 0.0418 |
| 32 | GW : DR | 1.048 (0.645, 1.452) | 0.0328 |
| 32 | DR : GW | 1.545 (0.219, 2.872) | 0.0483 |
| 32 | CL : DR | 0.993 (0.267, 1.718) | 0.0310 |
| 32 | DR : CL | 1.222 (0.297, 2.147) | 0.0382 |
| 64 | GW : CL | 1.307 (0.593, 2.020) | 0.0204 |
| 64 | CL : GW | 1.415 (0.488, 2.341) | 0.0221 |
| 64 | GW : DR | 1.633 (0.958, 2.308) | 0.0255 |
| 64 | DR : GW | 4.716 (3.116, 6.316) | 0.0737 |
| 64 | CL : DR | 1.947 (1.286, 2.607) | 0.0304 |
| 64 | DR : CL | 3.050 (1.974, 4.126) | 0.0477 |

At the primary length of 32, all directed triad contrasts average only
`0.283` to `1.545` cumulative nats. Equal-prior pairwise oracle
classification is correspondingly limited: GW/CL `0.70`, GW/DR `0.72`,
and CL/DR `0.70`. These are ceilings for the realized histories, not
evidence that a different decision rule could reach the frozen five-family
point-recovery target.

At length 64, the directed evidence increases, especially for DR, and
pairwise accuracies rise to `0.72`, `0.90`, and `0.86`, respectively. This
length dependence is evidence against structural non-identifiability.

### Contrast with well-recovered candidates

At length 32, the directed mean cumulative log BFs against the nuisance
families were:

| generating family | versus GW | versus CL | versus DR |
|---|---:|---:|---:|
| CS | 4.930 | 4.325 | 4.365 |
| CP | 7.024 | 5.381 | 5.003 |

In the reverse direction, GW/CL/DR against CP yielded
`11.674/13.172/13.045` nats. Against CS they yielded
`4.560/8.485/7.632` nats. Equal-prior pairwise accuracies for nuisance
families versus CS or CP were `0.90–0.98` at length 32. The information
ceiling is therefore selective: it affects the GW/CL/DR neighborhood, not
the whole five-family model comparison.

The observed full five-family recoveries agree with this contrast:

| family | frozen recovery (Wilson 95% CI) |
|---|---:|
| GW | 0.56 (0.462, 0.653) |
| CL | 0.49 (0.394, 0.587) |
| CS | 0.80 (0.711, 0.867) |
| DR | 0.59 (0.492, 0.681) |
| CP | 0.97 (0.915, 0.990) |

## 2. Bayes-optimality check

The committed 500 rows were reconstructed from their seeds. For each
history, the five exact family evidences were freshly normalized under the
frozen uniform candidate prior, independently of the committed selected
label. The reconstructed posterior's maximum absolute difference from the
recorded posterior was `0.0`, and its argmax agreed on `500/500` worlds.
The separately authored path-summation oracle already frozen at Gate 1
checks the same family scorers on enumerably short histories to
`1.57e-17`.

There were 136 worlds generated by GW, CL, or DR on which the selected
family was not the generator. The exact Bayes oracle made the same
selection in all 136:

- 119/136 selected another member of GW/CL/DR;
- 17/136 selected CS or CP;
- the triad retained mean posterior mass `0.8926`
  (95% CI `0.8513–0.9339`);
- the generating family remained in the oracle's 95% posterior set in
  132/136 worlds (`0.9706`).

On the 119 errors that stayed within the nuisance triad, triad posterior
mass was `0.9795`, mean generating-family probability was `0.2741`, and
mean triad entropy was `0.8850` nat (95% CI `0.8575–0.9125`). Thus the
committed point error normally reflects posterior ambiguity among the
three nearby families. A different argmax implementation cannot recover
information absent from the history.

## 3. Calibration of the confusion

Across all 136 misclassified GW/CL/DR worlds:

| quantity | mean (95% CI) | range |
|---|---:|---:|
| triad entropy, nats | 0.8758 (0.8462, 0.9055) | 0.0188–1.0964 |
| normalized triad entropy | 0.7972 (0.7702, 0.8242) | 0.0171–0.9980 |
| generating-family posterior | 0.2585 (0.2379, 0.2792) | 0.0136–0.4819 |
| selected wrong-family posterior | 0.5679 (0.5461, 0.5896) | 0.3222–0.9565 |

The held-out calculation obeyed the frozen split: 24 pre-held-out slices
formed the candidate posterior and the last eight slices were scored
without using them to select or match a candidate. Scores are nats per
held-out slice:

| held-out quantity | mean (95% CI) | range |
|---|---:|---:|
| posterior model average | -2.0107 (-2.0493, -1.9721) | -2.5297 to -1.4545 |
| hindsight best family | -1.9340 (-1.9737, -1.8943) | -2.5038 to -1.3630 |
| generating family | -2.0166 (-2.0561, -1.9771) | -2.6103 to -1.3870 |
| best-minus-average regret | 0.0767 (0.0648, 0.0886) | 0.0046–0.4423 |

The model average slightly outscored the generating family on average
(`0.0059` nat/slice), consistent with the generator itself being uncertain
from a finite realized sample. The hindsight-best comparison is optimistic
by construction; its small average advantage over model averaging does not
support a missed deterministic classification rule.

False certainty is uncommon but not absent. Four of 136 wrong selections
had posterior probability at least `0.90`; one exceeded `0.95`:

| seed | truth → selected | selected posterior |
|---:|---|---:|
| 770000 | GW → CS | 0.9251 |
| 770009 | GW → CS | 0.9319 |
| 770108 | CL → DR | 0.9456 |
| 770111 | CL → CS | 0.9565 |

Only seed `770108` is false certainty wholly within the nuisance triad.
The other three are unusual histories that strongly resemble a
context-coupled process. These cases must remain visible in any amended
calibration report; they rule out describing the frozen confusion as
perfectly calibrated.

## 4. Descriptive design probe

No criterion was evaluated. Both probes retained the complete five-family
candidate set and frozen family parameters.

| probe | GW recovery | CL recovery | DR recovery | triad macro |
|---|---:|---:|---:|---:|
| frozen Gate 2: length 32, missingness 0.15, n=100/family | 0.56 | 0.49 | 0.59 | 0.547 |
| length 96, missingness 0.15, n=15/family | 0.80 (0.548, 0.930) | 0.80 (0.548, 0.930) | 1.00 (0.796, 1.000) | 0.867 |
| length 96, missingness 0, n=15/family | 0.733 (0.480, 0.891) | 0.933 (0.702, 0.988) | 0.867 (0.621, 0.963) | 0.844 |

The frozen-missingness probe is the cleaner intervention: only history
length changed. Its mean truth-versus-nearest-triad-alternative log BFs
were:

- GW: `2.338` versus CL and `3.453` versus DR;
- CL: `2.722` versus GW and `3.420` versus DR;
- DR: `9.536` versus GW and `7.445` versus CL.

The complete-delivery probe provides more observed family-diagnostic
statistics and gives the same qualitative result. Its modest GW decrease
relative to the first 15-world probe is within the wide sampling interval;
the aggregate result does not depend on removing missingness.

The decisive comparison is length 32 versus length 96 at the same frozen
missingness. Separability rises substantially while the candidate family,
priors, likelihoods, temporal processes, and selection rule remain fixed.
That establishes the design-limited verdict.

## 5. Pilot-amended recommendation for V2.4.1

This is a recommendation, not an enacted criterion or repair.

1. Label V2.4.1 **pilot-amended** in its provenance record. Retain the
   failed V2.4 Gate-2 result verbatim and cite this diagnosis as the reason
   for changing the recovery-world information budget.
2. Change the primary recovery population from 32 to **96 slices**, while
   keeping the frozen `0.15` missingness, cue count, candidate priors,
   family parameters, exact prequential scoring, and all five competing
   families. Length 32 should remain a prespecified descriptive
   finite-information stress cell, not the point-recovery cell.
3. Keep the load-bearing criteria unchanged:
   - every-family recovery, including CS and CP, at least `0.60`;
   - macro recovery at least `0.60`;
   - false-CS rate in DR worlds at most `0.10`;
   - false-CS rate in CP worlds at most `0.10`;
   - the frozen calibration, posterior-set, and parameter-recovery
     requirements.
4. Preserve the full five-family confusion matrix, familywise Wilson
   intervals, posterior entropy, 95% posterior-set coverage, and
   high-confidence-wrong counts in the Gate-2 report. These are
   diagnostics, not substitutes for the unchanged point-recovery floor.
5. Freeze the amended design and analysis before running any new Gate-2
   population. Seeds `774000:774524` and `776000:776144` are pilot/
   diagnostic data and must be permanently excluded from criterion
   evaluation. No criterion may be calibrated and evaluated on the same
   worlds.

A calibrated-confusion replacement gate is **not** recommended for this
failure because the longer-history probe shows that point recovery becomes
attainable without changing the scientific model. If a future, independently
seeded 96-slice population still shows exact-posterior non-identifiability,
that would justify returning to the V2.3.2-F precedent and preregistering
posterior coverage, an entropy floor, a regret bound, and a
no-false-certainty condition. The present data do not justify spending that
escape hatch before testing the information-adequate design.
