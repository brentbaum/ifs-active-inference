# Sim 2 T4.3 Step A: single-gate pilot

This is the Phase 4 de-authoring pilot for Sim 2. It may run only with label
`pilot`, seeds 1001–1010, and output `runs/sim2/pilot/`. Confirmatory execution
is deliberately disabled in this Step A implementation.

## Preregistered primary and robustness arm

Both coherent D2 implementations are configuration-switchable. The primary is
**Option A (`primary_gate: write`)**:

```text
w_root(E_t, content) = D1_context_share(E_t) * content_root_route
a_BMR = b_full + n_actually_written
```

E_t enters the melt pathway once, through D1 evidence weighting at write time.
BMR is the canonical prior swap over the raw counts that were actually written;
its access weight is exactly one and contains no E_t.

**Option B (`primary_gate: access`)** is the robustness arm:

```text
w_root(content) = content_root_route                 # no E_t
a_BMR = b_full + rho(E_t) * n_actually_written      # sole E_t entry
```

The pilot always compares Option A with Option B using both registered
accessibility functions. Changing `primary_gate` changes which arm supplies the
headline four-regime, prompt, real-danger, and content-swap metrics; it does not
create a hybrid. Runtime E_t-flip probes explicitly audit the branch invariant.

## Why Option A is primary: argument against both D2 readings

D2 reading (i), the architectural reading, says an agent-internal reduction
requires an addressable representation of “this bundle as hypothesis.” We take
the D1-weighted write as the operational location of that representation for the
primary model: under transparency, little root-indexed evidence is registered,
so raw-count BMR later has little represented evidence to compare. Under
opacity, the evidence is registered and becomes a normal structural posterior.
No second access transformation is added at reduction time.

D2 reading (ii), inferential degeneration, does **not** follow from vanilla
raw-count BMR. D2 derives it only after adding the premise
`a_E = b_full + rho(E_t)n`. Option B takes that premise fully: its writes are
E_t-independent, and accessibility is the only E_t gate. It is a robustness
arm rather than the primary because the suite’s R2 constitution locates E_t in
the D1 effective-precision balance; Option A retains that location and leaves
canonical BMR untouched. The pilot therefore tests, rather than silently
combines, the two readings.

## A content swap that can fail

Informational observations now have a fixed weak root likelihood. They update
`met-in-this` at `0.20` of relational content’s root count on the same
observation budget. This is a weakly informative routing choice, not a learned
routing model: facts about the cue can bear weakly on “alone-with-this,” but the
observation is not itself evidence about how disclosure was met. The magnitude
is preregistered as a 1:5 likelihood-strength contrast before the pilot; it is
not zero and is logged per trial and per seed.

The C3 test is therefore live: relational witnessing and informational
content-swap both reach the root for 60 trials at high E_t. C3 survives only if
relational content melts while informational content does not. A content-swap
melt is reported as a negative result, not rerouted away.

## Formation-inherited root priors

The pilot imports existing `sim1.bundle.v2` artifacts while awaiting schema v3.
For each bundle, the v2 mapping is:

```text
p_met, p_alone = normalize(cause_banks.cue_counts.safe,
                           cause_banks.cue_counts.threat)
m_formation = log(1 + revision_probe.structural_precision)
b_full = [1, 1] + m_formation * [p_met, p_alone]
b_reduced = fill(sum(b_full) / 2, 2)
```

The unit vector is the ordinary Dirichlet base measure. The logarithm compresses
Sim 1’s modality-specific count scale when using it as an equivalent sample
size for the missing v2 relational modality. Both direction and concentration
therefore vary with formation output. Reduction preserves the inherited total
concentration while removing its directional coupling. Fixed `[2,12]` and
`[7,7]` priors are no longer used. Schema v3 should replace this documented
surrogate with direct relational formation fields.

## Accessibility robustness

Option B compares two independently motivated functions:

```text
saturating:       rho(E) = E / (E + E0)
threshold-linear: rho(E) = clamp((E - E_threshold) /
                                 (E_full - E_threshold), 0, 1)
```

The saturating form models graded effective sample size. The threshold-linear
form models an addressability threshold followed by proportional access. The
summary reports melt rate and mean melt trial for each at the primary BMR
interval, plus their melt-trial range. Neither function is used by Option A.

## Four regimes and probes

All four regimes receive 60 observations:

| Regime | Content | E_t | Other attenuation |
| --- | --- | ---: | ---: |
| informational | informational-safe | 0.05 | none |
| contact-under-capture | met-well | 0.05 | none |
| dissociative-quiet | met-well | 0.05 | 0.18 write scale |
| witnessing | met-well | 0.90 | none |

The pilot also runs premature/late prompted reduction, real danger, the live
high-E_t informational content swap, an E_t-flip audit for every gate arm, a
prior-odds sweep, and the complete gate × accessibility × interval comparison.

## Interval-independent discreteness

BMR intervals 3, 5, and 10 are all swept. Discreteness is no longer the
interval divided by a hand-chosen window. At each BMR check the code measures
the structural decrease across that check. The registered metric is:

```text
largest positive inter-check structural drop / sum of all positive inter-check drops
```

The criterion is greater than 0.50 and the witnessing melt rate must survive at
all three intervals. Because this model’s canonical prune is a discrete model
change, a value of one documents that property; the interval sweep tests whether
the event occurs, not whether `5/60` happens to fit a window criterion.

## Outputs

The pilot emits the standard run contract, primary per-seed metrics and traces,
probe CSVs, `single_gate_comparison_per_seed.csv`, the aggregated
`single_gate_comparison_metrics.csv`, `prior_odds_sweep_metrics.csv`, and the
primary four-regime hysteresis SVG. Constants and any post-pilot tuning history
are recorded in `magic-numbers.md`.
