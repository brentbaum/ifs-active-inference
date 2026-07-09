# Sim 6b T2.5 Obstruction

STATUS: obstruction

## What Ran

The preregistered Sim 6b run completed and emitted the full run contract at:

`projects/emergence-suite/suite/runs/sim6b/preregistered/`

Artifacts include `summary.json`, `status.json`, `metadata.json`,
`criteria-results.json`, `per_seed_metrics.csv`, `posterior_traces.csv`,
`ordinary_revision_probe_metrics.csv`, `recovery_witnessed_probe_metrics.csv`,
and `figures/depth_recovery.svg`.

## What Breaks

The Stage 4 coupling did not actually enter the required experimental regime:
the Sim 1-style CRP formation loop never spawned a new latent cause.

Observed run evidence:

- `metrics.arms.unclamped.spawn_rate = 0.0`
- `metrics.arms.clamped.spawn_rate = 0.0`
- `metrics.arms.yoked_control.spawn_rate = 0.0`
- `metrics.arms.unclamped.mean_write_time_depth = 0.8958853380047777`
- `metrics.arms.unclamped.min_mean_E_t = 0.2654856659937621`
- `metrics.controls.max_pe_stream_diff = 0.0`
- `metrics.controls.max_learning_rate_stream_diff = 0.0`

The depth machinery does collapse transiently in the unclamped arm
(`min_mean_E_t = 0.2655`), and the three arms are correctly yoked on realized
PE and learning-rate streams. However, CRP pressure never crosses the spawn
threshold before the existing cause assimilates the acute evidence. Because no
spawn occurs, write-time depth is the max-arousal fallback trial rather than a
spawn-time posterior. The clamp-control question is therefore not tested.

## What Was Tried

Implemented a bounded Stage 4 attempt in `Sim6b.jl`:

- Own `EmergenceSuite.Sim6b` module and minimal runner dispatch.
- Sim 1-style latent causes, CRP pressure, policy selection, arousal from
  precision-weighted surprise, and PE-scaled structural writes.
- Sim 6a categorical depth filtering reused through `Sim6a.Sim6aParams`,
  `volatility_observation`, `update_depth_with_evidence`, `predict_depth`,
  `effective_precisions`, and depth readouts.
- Clamp intervention as fixed high `q(d)`.
- Yoked control with volatility observation withheld from level 3.
- Sim 2-style accessible root statistics and canonical
  `BMR.reflexive_prior_swap_delta`.
- Ordinary disconfirming probe and post-recovery witnessed-contact probe.

The run is numerically stable and produces labels, but the state-space growth
event required by T2.5 does not occur.

## Why This Is Not A Clamp Verdict

`status.json` records `theory_result = falsified` because preregistered
criteria evaluate the observed metrics mechanically. That label is correctly
shipped, but it should not be interpreted as the paper-level clamp-control
falsification described in Appendix A.8. The clamped arm did not freeze after a
spawn; no arm spawned.

The clamped and yoked ordinary revision values are also zero because the
ordinary probe is operating on the assimilated initial cause under the current
BMR/readout setup, not on a spawned cause with a formation-time transparency
state.

## What v12 Needs

A v12 solution needs one of the following before the clamp test is meaningful:

- A CRP proposal schedule that evaluates spawn before the existing cause's
  high-PE assimilation can erase the low posterior predictive condition.
- A mid-inference state-growth interface that scores a new-cause proposal
  inside the hyper-model's current free-energy state rather than after the
  lower-level cause has already absorbed the trial.
- A two-pass trial schedule: compute posterior predictive and CRP proposal
  under pre-write banks, freeze the selected structural event, then perform the
  PE-scaled write with the same realized PE stream.
- A validation harness that fails fast when `spawn_rate == 0` so the clamp
  criteria are reported as obstruction rather than a theory verdict.

The current implementation should be treated as a runnable obstruction
artifact: it verifies the yoking, the imported depth pathway, and stability,
but not the decisive spawn-during-collapse manipulation.
