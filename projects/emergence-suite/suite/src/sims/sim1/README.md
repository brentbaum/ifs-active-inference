# Sim 1: Two-Arm Action-Mediated Formation Test

This is the T4.6 Step A continued criteria amendment, recorded before any
confirmatory run. The checked-in configuration remains PILOT only: seeds
1001–1010, label `pilot`, output `runs/sim1/pilot/`. The prior Step A pilot is
superseded and its pilot directory is overwritten by this two-arm run.

## Criteria amendment and claim status

The original S1.1a-as-stated died under full evidence yoking: its frozen cells
did not form a connected region. That null is retained as the expected result
of Arm 2, not reclassified as support for the original claim. The formation
claim is reformulated here, before confirmatory execution, as a paired
mechanism claim:

> Control-dependent freezing is carried by action-mediated evidence sampling.
> Low-efficacy action can write threat evidence but cannot change the evidence
> stream enough to generate a test; exact replay removes this action-to-evidence
> loop and should remove the cross-kappa freezing difference.

The two arms use identical agent learning, priors, policy scoring, potential
hazard schedules, observation precision, safe-probe revision, grid, and seeds.
They differ only in whether realized action success can suppress later hazard
exposure.

## Arm 1 — closed loop (primary)

For each `(seed, omega)`, the world generates a fixed trial-by-trial sequence of
potential hazards with probability `clamp(0.08 + 0.31*omega, 0.06, 0.97)`.
This potential-hazard schedule is identical at every kappa. At trial `t`, an
unsuppressed potential hazard is delivered as aversive evidence; otherwise the
delivered observation is safe. Observation precision and aversive severity are
fixed at 1.0.

After observing and choosing a policy, the agent receives a stochastic action
consequence. Kappa enters only this efficacy calculation. A safe consequence
while responding to delivered aversive evidence is a realized success. A
successful overt action suppresses subsequent potential hazards for a fixed
world-contingency window: approach 1 trial, flee 3 trials, appease 2 trials.
Attenuation suppresses 0 trials. Relief windows do not vary with kappa, omega,
seed, arm, or experimenter-selected dosage. Failed or ineffective actions add
no relief, leaving subsequent potential hazards exposed. Relief is consumed by
elapsed trials, and the world does not chase or replace suppressed hazards.

Thus all differences between potential and delivered exposure in Arm 1 are
mediated by the agent's realized policy and success. `per_seed_metrics.csv` and
`cell_metrics.csv` log potential, delivered, and suppressed hazard counts;
realized policy counts; successful relief actions; and exposure after each
prior policy. `action_mediation.csv` is the closed-loop per-cell audit table.

## Arm 2 — exact-replay yoked control

Arm 2 retains the prior Step A environment. The fixed potential-hazard stream
is delivered exactly, trial by trial, at every kappa. Actions still receive
kappa-dependent consequences and update policy-specific outcome banks, but
they cannot alter later exposure. A1.4 requires exact equality of potential and
delivered aversive counts, severity, and precision across kappa for every
fixed `(seed, omega)`.

The expected mechanism demonstration is a connected high-omega/low-kappa
frozen region in Arm 1 and disappearance of the cross-kappa region in Arm 2.
A1.5 preregisters the arm contrast as closed-loop frozen-region cells minus
yoked frozen-region cells >= 2. Two cells is the minimum nontrivial margin
consistent with S1.1a's independently required connected component size >= 2.

## Behavioral revision and criteria

The safe probe runs for 24 trials on a copied cause. Revision is
`max(pre-post predicted aversive probability under approach,
post-pre softmax approach probability, 0)`. KL is not used. A target is
threat-relevant at pre-probe predicted aversive probability >= 0.40, frozen at
behavior change <= 0.15, and revisable at change >= 0.25. Values in the gap are
unclassified. A cell needs at least 5/10 seeds with a label; a 5/10 frozen and
5/10 revisable tie is mixed and enters neither region. Regions use orthogonal
adjacency and require at least two cells.

`configs/sim1-criteria.yaml` now defines S1.1a–S1.4 and A1.1–A1.3 on Arm 1,
A1.4 on Arm 2, and A1.5 on their contrast. S1.3 compares the chronic
closed-loop path with the acute closed-loop frozen region on the same
precision-weighted-PE scale. Specifically, it compares the maximum PE on the
crossing trial among crossed chronic seeds with the minimum acute seed-cell
maximum; it does not use the maximum surprise anywhere in an arbitrarily long
chronic history. This crossing-event clarification was made during pilot
calibration, before confirmatory work. The three formation traits—spawn, reflexivity at
write, and postformation sampling—are logged by arm.

## Spawn diagnosis

The superseding pilot must diagnose the zero spawn rate. The report and
`spawn_diagnostic` block distinguish a posterior-predictive threshold that is
mis-scaled for the binary observation model from an environment that produces
no persistent unassimilable error. Any threshold rescaling is selected only on
pilot seeds, recorded with candidate results and provenance in
`magic-numbers.md`, then frozen before confirmatory work. If no defensible
rescaling produces prediction failures, formation-by-spawning is reported dead
in this environment class.

## Bundle schema v3 and outputs

Representative Arm 1 causes produced by the formation loop are exported as
`sim1.bundle.v3`. Formation provenance includes arm, potential/delivered/
suppressed exposure, policy-mediated exposure counts, spawn diagnostics, and
all three traits. Hardened initial causes are labeled honestly; route strings
do not imply spawning.

- `summary.json`: two-arm headline, mechanism contrast, spawn diagnosis,
  chronic path, traits, sensitivities, and criteria metrics.
- `per_seed_metrics.csv`: raw seed/cell values for both arms.
- `cell_metrics.csv`: per-arm cell aggregates.
- `action_mediation.csv`: closed-loop exposure as a function of realized
  policy, per cell.
- `posterior_traces.csv`: closed-loop chronic trace for pilot seed 1001.
- `artifacts/`: Arm 1 formation bundles and v3 manifest.
- `figures/phase_diagram.svg`: side-by-side closed-loop and yoked phase maps.

## T4.6 step C status (orchestrator hands-on, 2026-07-10 — NOT frozen for confirmatory)

State: closed-loop connected frozen region exists (omega 2.4-2.8, kappa 0.1-0.6, boundary
rising in kappa); spawning alive (274 events) via surprise-excess pressure + EFE-flatness
fork; kappa=0 closed-loop == yoked at the corner (coherence check passes).

OPEN ANOMALY (next iteration's first target): freshly-spawned causes are the probe target
at kappa=0 and revise at ~0.33 relative — a ~75-count bank moves under any nonzero probe
weight. The theory's own answer: freezing = write + the self-sealing loop (§4); late
spawns get no consolidation window in a 200-trial schedule. Candidate fix: extend the
formation schedule so spawned causes accrue loop-hardened mass before probing (world-side
change), then re-check the kappa profile and the two-arm contrast (A1.5 needs redefining
as the kappa-GRADIENT of freezing: present in closed loop, flat under yoking).
All step-C constants are pilot-provenance and unfrozen; sweep before Step B.
