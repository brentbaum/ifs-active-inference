# V3.1 development failures

## Stage-0 initial efficacy construct

The initial safe-baseline efficacy pilot produced an identified-minus-
nonidentified contrast of `0.003814` with interval
`[-0.042436, 0.051490]`. Before criterion seeds, the unconsumed pilot tail
calibrated the contracted danger-present efficacy assay. The initial result
remains in `stage-0-attainability-pilot.json`; the prospective amendment is
recorded separately.

## Gate 3 — retained verbatim

`control = false`

High-control minus low-control revisability was `0.005241709145309157`
against the frozen `0.0071` floor. Its 95% interval was
`[-0.00039953177232204037, 0.011316189191591242]`.

The stage stopped. The evaluator later authorized mixed-verdict continuation,
with this revisability family non-blocking and every other criterion blocking.

## Gate 4 — retained verbatim

`mode_slot = undefined posterior`

The lesion restricted inference to `active_mode=0` programs while retaining
observed mode-one values. Every surviving candidate received log likelihood
`-inf`; posterior normalization produced `NaN`, and the finite-only custody
writer stopped the run. No lesion threshold was evaluated. Gate 5 and C-V31
were not opened.

The evaluator adjudicated candidate-common masking for the deleted slot's
typed channel. That repair passed exactly: masking error `0.0`, finite
posteriors, and normalization error below `1e-10`.

## Gate 4 repaired run — retained verbatim

`identity_edges = false`

The identity-edge lesion removed part-like posterior mass exactly, but only
182/333 worlds kept the retained `W→Y` posterior within the blocking `0.20`
survival band (`0.5465465465465466` versus the `0.90` survival floor). The
other five lesions passed. Gate 5 and C-V31 were not opened.
