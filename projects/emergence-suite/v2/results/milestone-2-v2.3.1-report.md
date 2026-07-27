# Suite v2 — V2.3.1 formation repair

Stage verdict: **PASS** for gates 1–5.

The committed C-V23 failure is retained as the reason for this strain. The
diagnosis classified the schedule-collapse defect as parametric and the
single-slice jump defect as representational. The repair makes
event-context controllability explicit, adds schedule-blind Markov structure
dynamics, and bounds every candidate-evidence contribution.

## Recovery and original assays

- Structure accuracy / ECE: `0.930` /
  `0.0894`.
- Controllability / broadcast accuracy:
  `0.992` /
  `1.000`.
- Acute / gradual final persistent posterior:
  `0.831` /
  `0.992`.
- Low-minus-high control without overwhelm:
  `0.152`.
- Closed-loop chain:
  policy `0.401` → transition
  `0.387` → observation
  `0.320` → persistent model
  `0.137` → root
  `0.316`.

## Expanded generalization assay

- Theory-variable curves monotone:
  `{'uncontrollability_log_evidence': True, 'cumulative_overwhelm_precision': True}`.
- These gate curves hold the other preregistered theory variable constant.
  The raw marginal curves are retained separately and are not used as a
  substitute for the independent surface-increment test.
- Surface incremental cross-validated R²:
  `0.025006`.
- Paired low-minus-high-control formation:
  `0.319`
  (95% interval
  `0.264`–
  `0.374`).

Across the original and expanded open batteries, the empirical p99
single-slice change is `0.097067116`, the maximum is
`0.168947789`, and the analytic bound is
`0.288306024` over `41664` changes. There were
`0` exceedances of the frozen V2.3 p99.

All three selective lesions and every cumulative V2.0, V2.1, and V2.2.1 gate
passed. The 32-point stage-local neighborhood and complete repeated
original-plus-varied seed blocks are retained. C-V23b remains sealed and was
not inferred or run.
