# Sim 7 R1: one-state life (T4.5 Step A)

This rebuild removes the stitched biography rejected by the 2026-07-10
adversarial review. Only pilot seeds 1001–1010 and label `pilot` are accepted;
the runner rejects every confirmatory seed or label.

## State and update contract

`LifeState` owns one set of Sim 1-grown / Sim 4-wrapped cause banks, one
categorical depth posterior, and one learned co-regulation mapping. Formation
calls `Sim4.grow_stack` once. The arrays it returns are retained by object
identity through adult adversity, therapy, and frozen probes. `bank_audit.csv`
records initial and final object IDs for every bank.

Adult adversity, therapy contact, and held-out probes all call
`update_life!`. Stage boundaries change only the world event schedule. Adult
and therapy observations increment the carried cause banks; no later stage
creates, replaces, or injects a bank. Frozen held-out events use the same update
function with learning disabled.

## Graph comparison

H1 and H2 receive identical per-seed world schedules. Their only difference is
the `GraphDirection(depth_tilt_target)` constructor argument: H1 tilts the root
node and H2 tilts the context node. Shared precision and learning functions
consume that node index without architecture or condition branches. Failure is
measured as frozen out-of-sample log likelihood on held-out adult and
post-therapy life segments.

## Preregistered readouts

- Carried adult capture: correlation with childhood written reflexivity of the
  same focal cause, plus adult capture prevalence.
- Therapy melt: pre/post capture and fixed-probe revisability on that same bank;
  `root_evidence_write` gives the witnessing audit trail.
- H2 prediction: paired held-out log-likelihood difference and seed win rate.
- Melt/contact order: descriptive output only. Sim 4's outside-in claim remains
  falsified and no ordered or ID-based access rule is introduced.

The dead original S7 criteria are retained as `dead_falsified` records in
`configs/sim7-criteria.yaml`; they are not evaluated.

## Pilot outputs

- `summary.json`, `status.json`, `metadata.json`, `criteria-results.json`
- `per_seed_metrics.csv`, `model_comparison.csv`
- `posterior_traces.csv`, `formation_events.csv`
- `bank_audit.csv`, `melt_order_descriptive.csv`
- `figures/timeline.svg`

Run from the repository root:

```sh
~/.juliaup/bin/julia --project=projects/emergence-suite/suite projects/emergence-suite/suite/scripts/run.jl projects/emergence-suite/suite/configs/sim7.yaml
```

## T4.5 Step B verdict (orchestrator, 2026-07-10): rebuild PASSED audit; life-scale claims FALSIFIED at frozen thresholds — three separable diagnoses

The one-state rebuild is real: bank identity 1.0 through all stages, no
condition branches, H1/H2 = one constructor index, melt order descriptive.
What the lived biography produced: carried capture r=-0.990 (childhood written
reflexivity IS adult capture, evolved not recomputed) and sharply bimodal adult
outcomes — 4/10 lives captured, all four melting under witnessing (drops
0.68-0.77). Three failures, each with a distinct diagnosis for any cycle 2:
(1) prevalence 4/10 vs 6/10 — world-schedule calibration, not mechanism;
(2) fixed-probe revisability worsened in 10/10 because witnessing ADDS bank
mass — the probe inherited Sim 1's superseded absolute standard instead of its
mass-fair relative-reduction fix; (3) H1-H2 held-out advantage reversed
(-0.090) — raw adversity prediction cannot discriminate graph direction; Sim 3
discriminated via contact-transfer structure absent from this likelihood.
Any cycle 2 must preregister those three changes on fresh grounds; this record
stands. No retuning was performed after observing results.
