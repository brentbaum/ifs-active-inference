# V2.2.1 prerepair diagnosis

This diagnosis was run before any repair code or parameter block existed. It
uses 256 paired open development worlds, seeds `50000–50255`, and
the frozen V2.2 Beta(1,1) association family. A true-zero cue means
`P(M=G)=0.5`.

## Calibration curve

| History n | Mean posterior | Signed bias | Mean absolute deviation | 95% coverage | Floor violations |
|---:|---:|---:|---:|---:|---:|
| 20 | 0.5011 | 0.0011 | 0.0813 | 0.973 | 0.840 |
| 50 | 0.5042 | 0.0042 | 0.0500 | 0.949 | 0.645 |
| 100 | 0.5015 | 0.0015 | 0.0382 | 0.969 | 0.629 |
| 180 | 0.4982 | -0.0018 | 0.0270 | 0.969 | 0.375 |
| 400 | 0.4999 | -0.0001 | 0.0193 | 0.969 | 0.238 |
| 800 | 0.5005 | 0.0005 | 0.0141 | 0.957 | 0.098 |
| 1600 | 0.4998 | -0.0002 | 0.0108 | 0.945 | 0.020 |

At the challenge-relevant history length 180, signed bias was
`-0.0018`, 95% interval coverage was
`0.969`, and
`0.375` of open worlds exceeded the 0.02
untreated-transfer floor after the same broad–narrowed–broad correction
pattern. At n=1600 the rate fell to `0.020`;
the soft-zero leak shrinks at the expected sampling rate rather than showing
systematic estimator bias.

## Can the existing family concentrate on zero?

It can concentrate *around* `theta=0.5` asymptotically: mean absolute deviation
falls from `0.0813` at n=20 to
`0.0108` at n=1600. It cannot assign any
posterior mass to the structural hypothesis `theta=0.5`, because a point has
measure zero under every continuous Beta posterior. Exact-zero posterior mass
is therefore `0` at every history length.

## Verdict

**(b): correct finite-evidence Bayesian behavior under a badly represented
structure prior.** The existing conjugate learner is calibrated
(`0.969` coverage and
`-0.0018` signed bias at n=180), but V2.2 lacks a
factorized point component. It consequently treats ordinary finite-sample
deviation from 0.5 as weak root association and legitimately propagates it
through G.

The legitimate repair is an explicit zero-association candidate under finite
model comparison, with posterior model averaging over a point null and a
learnable associated slab. This is a structure-prior repair—not a transfer
threshold, posterior clamp, or mediation lesion.
