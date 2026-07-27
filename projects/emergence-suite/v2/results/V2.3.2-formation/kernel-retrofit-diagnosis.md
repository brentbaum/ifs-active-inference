# Kernel-retrofit diagnosis after evaluator full-suite verification

## Finding

The V2.0 constitution retrofit did **not** change V2.3.1 outputs. The two
failures were stale tests that predated this build and contradicted the
committed v2.3.1r rescinded ledger.

## Apparatus-first trace

The only V2.0 scientific-code change extracted the existing body that creates
the finite nested comparison into `model_comparison_model()`. Before and
after extraction it declares the same variables, prior, factor table,
observation `D=8`, exact engine call, and analytic comparison. No factor,
normalizer, inference function, RNG stream, seed, or parameter changed.

V2.3.1 imports `run_v20` only inside `run_v231()` and calls it after
`semantic_proofs()`, `recovery_assay()`, `original_open_assays()`, and
`generalization_assay()` have already computed the two disputed metrics.
The returned V2.0 report is used only for the cumulative-regression Boolean
and report field. There is no shared mutable parameter or context between
V2.0 and V2.3.1.

The current full v2.3.1r rerun is numerically identical at every shared
numeric leaf to the committed pre-build v2.3.1r report. In particular:

- recovery ECE remains `0.10579451215553712`, above the retired `.10`
  threshold;
- full generalization surface incremental CV R² remains
  `0.6173327730910273`, above `.05`;
- the 128-world smoke subset observed by evaluator verification is
  `0.6756`; it is a different sample-size readout of the same already
  rescinded property, not the frozen full-block metric.

Thus the declared-correct behavior is unchanged exact kernel evidence plus
the already-corrected historical ledger: v2.3.1r Gates 2 and 3 remain false.

## Live-stage regression result

Every numeric leaf matches the pre-build committed cumulative report exactly:

| Stage | Numeric leaves compared | Moved | Maximum absolute difference |
|---|---:|---:|---:|
| V2.0 | 22 | 0 | 0 |
| V2.1 | 65 | 0 | 0 |
| V2.2.1 | 97 | 0 | 0 |

The exhaustive metric-by-metric table is
`live-stage-metric-comparison.md`.

## Corrective action

The two stale v2.3.1 threshold tests are now historical ledger pins. They
assert the exact rescinded values and false gate statuses. No live criterion
was weakened or removed.
