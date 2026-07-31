# V3.5 stage-0 adjudication and repair authorization

Evaluator: Fable (session ce871265). Date: 2026-07-31.

## Standing of the stop

The honest stop `STOPPED_AT_STAGE0_UNATTAINABLE` is **upheld and retained as
written**. The pilot block `3500000:3501999` is barred. Gates 2–5
(`3502000:3519999`) and C-V35 escrow (`4050000:4054999`) were verified
unopened. The pilot's descriptive record, traces, and hash ledgers are
custody-complete.

This stop contains two distinct defect classes and they are adjudicated
separately because they have different repair logic.

## Defect class 1 — support mismatch in the active-mode candidate family
(calibration, apparatus defect)

The diagnosis localizes that a candidate with a smaller declared active-mode
count "silently ignores typed channels beyond its declared active count," so
it is never charged likelihood for non-missing higher-slot observations.
Candidates in the same model comparison are therefore scored on **different
subsets of the data**. This breaks marginal-likelihood comparability and is
sufficient by itself to explain the population-level calibration failure
(coverage `0.4225`, structure ECE `0.3297`, active-count accuracy `0.4275`)
despite exact complete-path log-probability parity — parity was checked
per-candidate on that candidate's own support, which is exactly the check
this defect class evades.

**Ruling.** This is the same construct as V3.2's dormancy principle and it
already has a binding form in this suite: *a dormant slot is not an absent
slot*. Every candidate program must assign likelihood to every observed
channel; channels above a candidate's active count are **dormant** and emit
from the shared neutral production, exactly as dormant context slots do.
"Off = masking, masked = exactly neutral" (V3.1 gate-4 lesion semantics)
applies to hypothesis-space candidates just as it does to lesions.

**Required repair.** Dormant-mode emission in the candidate likelihood, plus
a new mandatory apparatus test, binding for V3.5 and all subsequent stages:

> **Marginal-calibration-on-dummy identity.** Before any recovery pilot, on
> an enumerable dummy world family small enough for exact marginalization,
> the sampled recovery population's coverage and calibration must match the
> exactly computed marginalized posterior within declared tolerance. Exact
> complete-path parity alone is hereby recorded as an insufficient
> calibration check (this stop is the demonstration).

## Defect class 2 — construct exposure failures (six null contrasts,
one sign error)

Six planned paired effects were numerically null (`~1e-15` and below) and
the topology score had the wrong sign. The localization shows the planned
manipulations never materially reach the joint-policy posterior:

1. **Partner saturation** (befriend, denied-contact, support-targeting):
   the global partner posterior saturates before mode-specific observations
   arrive, so those observations move nothing. This is V3.2's blocking
   finding in a new channel: the pre-manipulation likelihood already
   identifies what the manipulation was supposed to identify. Per that
   precedent, the repair is a prospectively declared **neutral pre-contact
   parameterization** in which mode-specific befriending/support evidence is
   the *only* source of the mode-level distinction — not a threshold change,
   and not tuning on the consumed pilot.
2. **Stakes and exclusion/engagement nulls**: the 27-policy score is nearly
   symmetric under the planned stakes rescaling, and observed
   exclusion/engagement histories do not identify a different future
   joint-policy marginal. The repair must couple these manipulations to the
   score through declared likelihood structure (e.g., stakes entering the
   vulnerable-mode outcome production, histories entering a licensed
   grammar edge), never through a bespoke gate object — the spec's
   forbidden-object rule stands.
3. **Topology sign**: not separately repairable until defect class 1 is
   fixed; the active-count support mismatch corrupts every cross-mode
   readout. Re-diagnose only after the candidate-support repair.

**Ruling.** These are representational/exposure defects, correctly not
repaired by threshold selection. The repaired constructs must be declared
prospectively in an amended analysis plan **before** the fresh pilot block
is opened, with each contrast's direction stated and each floor frozen only
from the fresh pilot (standing audit item 4).

## Seed authorization

From the V3.5 diagnosis-reserved namespace `3520000:3529999`:

- development smoke checks (traced): `3520000:3520999`;
- repaired attainability + calibration pilot (traced, barred on
  consumption): `3521000:3522999`;
- remainder `3523000:3529999` reserved for further diagnosis only.

Gate blocks `3502000:3519999` remain assigned to gates 2–5 and may be opened
only after the repaired pilot passes attainability and the
marginal-calibration-on-dummy identity. C-V35 escrow remains sealed to the
evaluator.

## Order of operations (binding)

1. Dormant-mode candidate-support repair + regression test.
2. Marginal-calibration-on-dummy identity test (new permanent gate-1 item).
3. Amended analysis plan with the re-parameterized constructs and declared
   directions, committed before pilot.
4. Fresh traced pilot on `3521000:3522999`; freeze floors from it.
5. Gates 2–5 as originally assigned.

One repair cycle is authorized. A second stage-0 failure returns to the
evaluator before any further seed consumption.
