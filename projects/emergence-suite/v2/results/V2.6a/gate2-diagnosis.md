# V2.6a Gate-2 calibration diagnosis

Status: read-only localization over the retained 1,500 Gate-2 rows and the
frozen generator/scorer source. No repair, criterion change, new seed, or
Gate-3 evaluation was performed.

## Finding

The reported ECE does **not** contradict Bayesian calibration of exact
inference on draws from its own model. This Gate-2 recovery population is not
drawn from the scorer's path prior, and the vector evaluated for calibration
is not a posterior over the authored `truth_family` label.

The scorer performs exact inference over the time-indexed path
`L_1:48`. Its reported `q_partner` is the normalized sum of the 48 smoothed
state marginals: posterior expected **time occupancy**. Gate 2 instead scores
that occupancy vector against one world-level label, defined by the
constructor as the initial and majority-occupancy family. In switching worlds,
one third of the true path belongs to another family. A posterior occupancy
near `(2/3, 1/3, 0, 0)` can therefore be accurate and exact while its maximum
is about `2/3`; treating that maximum as confidence in a single global family
creates systematic apparent underconfidence.

## 1. Generator versus scorer priors

| Quantity | Scorer conditions on | Gate-2 generator uses | Match |
|---|---|---|---|
| Initial partner state | Uniform prior `(0.25, 0.25, 0.25, 0.25)` | Deterministic cycling, exactly 375 worlds per family | Population marginal matches; not sampled per world |
| Emissions | Frozen four-channel Bernoulli table | The exact same table passed to `sample_observation` | Yes |
| Transition process | Markov, stay `0.94`, each alternative `0.02` per slice | 752 paths with no switch; 748 paths with exactly one forced switch at slice 32 | No |
| Switch destination | Each of three alternatives equally likely | Always `(truth + 1) mod 4` | No |
| Switch time/count | Geometric Markov timing; any number of switches | Fixed time 32 and exactly one switch in switching worlds | No |
| Calibrated target | Posterior marginals over `L_t`, or a declared parameter posterior | Time-averaged occupancy compared with an authored initial/majority label | No |

For 48 slices, the scorer prior expects
`47 * (1 - 0.94) = 2.82` switches. The generator's observed design mean is
`748 / 1500 = 0.4986667`. A no-switch path has scorer-prior probability
`0.94^47 = 0.0545769`. Conditional on its initial state, the exact forced
one-switch schedule/destination has probability
`0.94^46 * 0.02 = 0.00116121` (or `0.000290303` including the initial-state
prior).

Thus the emission likelihood is correctly shared, but the partner-path draw
does not use the prior the scorer conditions on. The calibration theorem's
own-model sampling premise is void. The second mismatch—occupancy versus a
global label—would remain even if the path schedule happened to be sampled
from the Markov prior.

## 2. ECE decomposition

The frozen implementation uses ten equal-width bins of the **top-label
confidence**

`max_k q_partner[k]`

and compares each bin's mean maximum probability with argmax accuracy. It is
not a full-posterior or classwise calibration statistic. This is exactly the
same fixed ten-bin confidence-ECE convention used by V2.4.4
`_multiclass_ece`; V2.4.4 obtained `0.0315117` under that convention.

| Confidence bin | N | Mean confidence | Accuracy | Confidence − accuracy | Weighted absolute gap |
|---|---:|---:|---:|---:|---:|
| `[.3,.4)` | 7 | 0.354663 | 0.571429 | -0.216766 | 0.001012 |
| `[.4,.5)` | 24 | 0.460720 | 0.791667 | -0.330947 | 0.005295 |
| `[.5,.6)` | 128 | 0.563818 | 0.984375 | -0.420557 | 0.035888 |
| `[.6,.7)` | 541 | 0.650044 | 0.998152 | -0.348108 | 0.125551 |
| `[.7,.8)` | 74 | 0.733729 | 1.000000 | -0.266271 | 0.013136 |
| `[.8,.9)` | 87 | 0.859441 | 1.000000 | -0.140559 | 0.008152 |
| `[.9,1]` | 639 | 0.971878 | 1.000000 | -0.028122 | 0.011980 |

The total is `0.2010134`. This is not a sparse-bin artifact: the two bins
from `.5` to `.7` contain 669 worlds and contribute `0.1614383`, 80.3% of
the ECE. Every occupied bin has the same direction—confidence below
accuracy. Overall mean top confidence is `0.7916532`, while accuracy is
`0.9926667`; because every bin has the same sign, ECE is exactly their
difference up to floating-point rounding.

The stratification localizes the effect:

| History | N | Mean confidence | Accuracy | Fixed-bin ECE | Multiclass Brier |
|---|---:|---:|---:|---:|---:|
| Stable | 752 | 0.949621 | 0.998670 | 0.049049 | 0.012314 |
| Forced switching | 748 | 0.632841 | 0.986631 | 0.353791 | 0.246957 |

In switching worlds, mean posterior mass on the authored truth family ranges
from `0.595948` to `0.666118` across families, while mean mass on the forced
adjacent state ranges from `0.296278` to `0.332304`. That is the expected
occupancy geometry of the constructed path, not diffuse uncertainty about a
single family identity.

## 3. Binning-robust descriptive calibration

Splitting the same top-label confidences into ten equal-count adaptive bins
gives ECE `0.2010134` again. Adaptive-bin gaps range from `-0.397794` in the
lowest decile to `-0.004025` in the highest; all remain underconfident. The
result is invariant here because all bins have the same gap direction.

A different descriptive statistic—adaptive, classwise full-posterior ECE,
computed separately for each `q_partner[k]` against `I(truth_family=k)` and
then averaged—equals `0.0673164` (class values `0.055494`, `0.075593`,
`0.057207`, `0.080971`). Fixed-bin classwise ECE is `0.0992195`.

The adaptive classwise number should not replace the frozen criterion. It
answers a different question and still compares occupancy probabilities to
the world-level label. Its contrast with top-label ECE shows that the frozen
failure is specifically driven by interpreting maximum occupancy as
confidence in one global family. The standing V2.4.4 comparison does not
change this conclusion: V2.4.4 used the same top-label convention, but its
posterior was actually over mutually exclusive world families, so the
quantity and truth target were aligned there.

## 4. Brier decomposition

The full multiclass Brier is `0.1293227`. A Murphy-style decomposition using
predicted-family × fixed-confidence bins gives:

- uncertainty: `0.7500000` (the balanced four-class base rate);
- resolution: `0.7451716`;
- reliability: `0.1218802`;
- reconstructed `uncertainty - resolution + reliability`: `0.1267085`;
- within-bin residual: `0.0026141`.

The small residual is from variation of the full posterior vectors within
the coarse bins. The corresponding top-label correctness Brier is
`0.0719144`; its binned decomposition has uncertainty `0.0072796`,
resolution `0.0015199`, reliability `0.0657502`, and residual `0.0004045`.

These numbers are consistent with, rather than contrary to, the ECE result.
The occupancy readout has extremely high resolution: it almost always ranks
the authored majority family first, so resolution nearly cancels the large
four-class uncertainty and the multiclass Brier remains below `.15`.
Reliability is nevertheless the dominant remaining Brier component because
the forced-switch occupancy assigns substantial, correct mass to the second
state while the evaluation target is one-hot. Coverage `1.0` is likewise
expected: the authored majority family remains in every 95% posterior set.

## Localization conclusion

The failure has two apparatus-level sources:

1. **Generator/scorer mismatch:** Gate-2 transition paths are designed rather
   than sampled from the declared Markov prior.
2. **Posterior/target mismatch:** posterior expected state occupancy is scored
   as though it were posterior confidence in a single world-level partner
   family.

The ECE is systematic underconfidence under that mismatched scoring
interpretation, not noise from sparse bins, not approximate inference, and
not evidence that the exact HMM posterior violates Bayesian calibration.
This diagnosis makes no recommendation and leaves the frozen failure and all
criteria unchanged.
