# V2.7 gate 4 diagnosis stub

Execution stopped honestly at gate 4. The sole new blocking failure is the
`reduction` lesion. No Gate 5 seed was opened.

The maximum residual between the reduction-lesioned future joint-policy
posterior and the unreduced baseline is `8.425920094643456e-05`, above the
declared `1e-10` semantic tolerance. The other six lesions pass, with maximum
target residuals at or below `5.551115123125783e-17`.

Apparatus-first localization: the intact reduction composition converts the
frozen V2.5b posterior mass on `000` into a lower effective mandate forecast.
The lesion path restores a scalar posterior-mean mandate override. The
unreduced baseline instead retains the exact model average across the three
mandate candidates. Since softmax normalization is nonlinear, those two
computations are close but not identical. Thus the failure is in the lesion
implementation's claimed restoration identity, not in normalization,
registration, cross-outcome mediation, or the frozen V2.5b posterior.

No repair, parameter change, criterion change, or Gate 5 execution is
authorized in this run.
