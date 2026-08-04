# DT-S3-PERMISSION design freeze

This design was fixed before any seed in `3812000:3819999` was opened.
Permission is not a new state variable. It is the probability assigned by the
frozen internal-system policy posterior to `permit`, `allow_partial_contact`,
or `allow_full_contact`.

## S3-A — decomposition and clamp identity

The five named scientific inputs are partner reliability, learned contact
response, co-protection efficacy, predicted vulnerable-mode outcome, and
stakes. One input is moved at a time while the other four are clamped. The
first four are predicted to increase permission; stakes are predicted to
decrease it. Recomputing with all five inputs clamped must move permission by
exactly zero within `1e-10`.

The frozen base is `(partner=.62, contact=.65, co-protection=.60,
safe-outcome=.65, stakes=.75, horizon=1, protector=1)`. Positive inputs move
from `.25` to `.82`; stakes move from `.45` to `1.0`.

## S3-B — co-protection by current safety

Each seed runs the full `current safety x learned co-protection` 2x2. Current
safety should move immediate access. After a later danger probe, the
co-protection effect on durable permission must exceed the safety-history
effect by `log(1.02)`.

The later probe sets safe-outcome prediction to `.18` and stakes to `1.0`.

## S3-C — refusal as an epistemic policy

The four frozen families are highly informative, weakly informative, costly
but informative, and safe but uninformative refusal. The exact apparatus
computes `I(L, theta_contact; O_partner | do(refuse))`. The registered
estimand is the partial coefficient of this expected information gain in the
refusal-policy posterior after controlling predicted immediate safety and
refusal cost. Its direction is positive.

The exact four-policy softmax temperature is `4.0`, and the refusal score's
EIG coefficient is `1.8`.

## S3-D — diagnosticity-controlled revocation

Repeated weak supporting evidence and one opposing violation have matched
total log Bayes-factor magnitude. They are evaluated under a failure-diagnostic
partner process and a symmetric control. The failure-diagnostic process may
update temporal persistence from packet form; the symmetric control depends
only on the matched evidence total. A larger violation and a nondiagnostic bad
outcome complete the localization.

The registered criteria are: equal-BF revocation exceeds accrual by
`log(1.02)` in the failure-diagnostic model; that asymmetry is within the same
ROPE in the symmetric model; and the nondiagnostic outcome moves permission
less than the equal-BF violation.

The matched absolute log BF is `log(4) = 1.3862943611198906`. The frozen
failure-diagnostic temporal-persistence posterior shift is `.18`; it is absent
from the symmetric control.

## Cells and custody

The four contiguous cells are `3812000:3812999`, `3813000:3814999`,
`3815000:3816999`, and `3817000:3819999`. Every cell fsyncs its first world
before parallel dispatch, then persists ascending, gap-free rows and hashes
before aggregation. New code is apparatus and tests only. Frozen v3.6
scientific modules are untouched. Excess additions: none.
