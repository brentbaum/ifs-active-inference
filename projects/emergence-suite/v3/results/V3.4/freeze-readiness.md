# V3.4 freeze readiness

Status: **FROZEN_ADJUDICATED_SHORT_HISTORY_CONJUNCTION_BOUND**.

This disposition preserves two records:

- the Stage-0 generator/scorer defect and the consumed invalid pilot;
- the original Gate-5 FAIL produced by transplanting the 48-slice
  exact-program floor onto the 32-slice robustness cell.

The authorized Stage-0 repair passed its fresh traced pilot. Gates 1–4 passed.
Under `gate5-adjudication.md`, Gate 5 passes every blocking criterion: the
primary 48-slice exact-program recovery is `0.837` against `0.78`; all
scientific robustness, custody, and cumulative checks pass.

The descriptive information curve is:

| Slices | Exact four-edge program | Minimum edge | Structure ECE | Coverage |
|---:|---:|---:|---:|---:|
| 32 | 0.733 | 0.845 | 0.02019 | 0.975 |
| 48 | 0.837 | 0.888 | 0.01582 | 0.990 |
| 96 | 0.915 | 0.935 | 0.01323 | 0.997 |

The short-history limitation is a conjunction bound: every individual edge
passes at 32 slices, but a world is counted wrong at the whole-program level
when any of four edge decisions is wrong.

Custody:

- all executed Gate 1–5 worlds were serialized at execution time;
- every Gate-5 trace ledger rehashes and has the declared record count;
- V3.0–V3.3 freeze manifests rehash without mismatch;
- C-V34 escrow `4040000:4043999` is untouched.

Regression:

- V3 unit suite: `43/43`;
- cumulative V2 fast suite: `26/26` modules.

V3.4 is ready for evaluator verification and C-V34 custody.
