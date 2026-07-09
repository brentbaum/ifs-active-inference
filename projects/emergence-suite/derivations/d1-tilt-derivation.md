# D1 derivation: the tilt equation as a mean-field message

## Source target

The paper's Section 7 uses one mechanism: a hyper-layer depth variable changes the effective precision balance between a bundle-prior stream and a present-evidence stream,

```text
pi_eff     = r_t * pi_part * exp(-beta * E_t)
lambda_eff = lambda_ctx * exp(+gamma * E_t)
C_t        = pi_eff / (pi_eff + lambda_eff).
```

Appendix A.1 defines `E_t` as the inferred precision of the reflexive mapping, and Appendix A.5 asks whether this equation can be derived as the message sent by a hyper-layer that holds beliefs over discrete depth states. This note treats `E_t` as a readout of the hyper-posterior, not as an extra control input.

## Setup

Let `d in D` be a discrete hyper-layer depth state with posterior `q(d)`. Let `e(d)` be the scalar depth coordinate carried by that state. It may be the state index, a normalized depth value, or a calibrated log-precision coordinate. Define

```text
E_t := E_q[e(d)] = sum_d q(d) e(d).
```

At the lower level there are two precision-modulated information streams:

- bundle-prior stream, with learned structural precision `pi_part` and current cue activation `r_t`;
- present-evidence stream, with learned contextual precision `lambda_ctx`.

The hyper-state does not add gates, channels, or bonus terms. It only specifies the log-precisions used by these streams:

```text
ell_pi(d)     := log pi_bundle(d)
ell_lambda(d) := log lambda_context(d).
```

The mean-field factorization needed for the advertised result is

```text
q(lower variables, d) = q(lower variables) q(d),
```

with the hyper-layer entering the lower-level update only through the precision messages. The standard expected-log-precision message convention is:

```text
log pi_eff     = E_q[log pi_bundle(d)]     = E_q[ell_pi(d)]
log lambda_eff = E_q[log lambda_context(d)] = E_q[ell_lambda(d)].
```

Equivalently, the lower level uses geometric-mean effective precisions:

```text
pi_eff     = exp(E_q[ell_pi(d)])
lambda_eff = exp(E_q[ell_lambda(d)]).
```

This convention is the load-bearing assumption. A caveat about ordinary natural-precision Gaussian factors is given below.

## Exact affine result

Assume the depth-to-log-precision maps are affine in the same scalar depth coordinate:

```text
ell_pi(d)     = log r_t + log pi_part - beta  * e(d)
ell_lambda(d) =             log lambda_ctx + gamma * e(d).
```

Then the mean-field messages are

```text
log pi_eff
  = E_q[log r_t + log pi_part - beta e(d)]
  = log r_t + log pi_part - beta E_q[e(d)]
  = log r_t + log pi_part - beta E_t,

log lambda_eff
  = E_q[log lambda_ctx + gamma e(d)]
  = log lambda_ctx + gamma E_q[e(d)]
  = log lambda_ctx + gamma E_t.
```

Exponentiating gives exactly

```text
pi_eff     = r_t * pi_part * exp(-beta * E_t)
lambda_eff = lambda_ctx * exp(+gamma * E_t).
```

The capture index is therefore the normalized precision share

```text
C_t = pi_eff / (pi_eff + lambda_eff).
```

Under these assumptions, `beta` and `gamma` are not free phenomenological knobs. They are slopes of the generative model's depth-to-log-precision mapping:

```text
beta  = - d ell_pi / d e
gamma = + d ell_lambda / d e.
```

For discrete depth states, the same statement is finite-difference spacing. If adjacent states are separated by `Delta e`, then

```text
beta  = -(ell_pi(d+1) - ell_pi(d)) / Delta e
gamma = +(ell_lambda(d+1) - ell_lambda(d)) / Delta e
```

whenever those spacings are constant across depth states.

## When one scalar `E_t` exists

For arbitrary state-specific log-precisions, the expected-log message is still exact:

```text
pi_eff     = exp(sum_d q(d) ell_pi(d))
lambda_eff = exp(sum_d q(d) ell_lambda(d)).
```

But the paper's one-scalar tilt form is exact only when both log-precision vectors lie on the same one-dimensional affine coordinate. There must exist a scalar `e(d)` and constants `beta`, `gamma` such that

```text
ell_pi(d)     - log r_t - log pi_part = -beta  e(d)
ell_lambda(d) - log lambda_ctx         = +gamma e(d)
```

for every depth state `d`. Equivalently, after subtracting intercepts, the two log-precision maps must be collinear with opposite/specified signs. If the bundle stream and context stream require different depth coordinates, the exact result is instead

```text
pi_eff     = r_t * pi_part * exp(-beta  * E_q[e_pi(d)])
lambda_eff = lambda_ctx  * exp(+gamma * E_q[e_lambda(d)]),
```

which no longer licenses the paper's single `E_t` unless `e_pi(d)` and `e_lambda(d)` are the same coordinate up to absorbed scale.

## Approximation regimes

If the depth-to-log-precision maps are nonlinear,

```text
ell_pi(d)     = log r_t + log pi_part + f_pi(e(d))
ell_lambda(d) = log lambda_ctx         + f_lambda(e(d)),
```

then the exact expected-log messages are

```text
pi_eff     = r_t * pi_part * exp(E_q[f_pi(e)])
lambda_eff = lambda_ctx  * exp(E_q[f_lambda(e)]).
```

The paper's form replaces `E_q[f(e)]` with an affine function of `E_q[e]`. This is exact for affine `f`. Otherwise it is a first-order approximation around a reference depth `e0`:

```text
f(e) ~= f(e0) + f'(e0) (e - e0).
```

The intercept can be absorbed into `pi_part` or `lambda_ctx`; the slopes identify local `beta` and `gamma`. The omitted terms include both distance from the linearization point and posterior spread. For example, if

```text
f(e) = a + s e + k e^2,
```

and the affine tilt uses the first-order expansion at `e0`, then

```text
E_q[f(e)] - [f(e0) + f'(e0) (E_q[e] - e0)]
  = k (Var_q[e] + (E_q[e] - e0)^2).
```

If instead one allowed a nonlinear one-scalar formula `exp(f(E_t))`, the remaining Jensen term would be

```text
E_q[f(e)] - f(E_q[e]) = k Var_q[e].
```

So the closed-form affine tilt remains accurate when the hyper-posterior is concentrated near the calibration point, the depth grid is narrow, or the curvature is small. It diverges for broad `q(d)` under curved mappings, and can also diverge for concentrated `q(d)` far from the linearization point.

## Important caveat: natural-precision VMP

The derivation above uses the expected-log-precision message requested by D1:

```text
pi_eff = exp(E_q[log pi]).
```

For a conventional Gaussian likelihood factor with precision `tau(d)`,

```text
log p(y | x, d) = 0.5 log tau(d) - 0.5 tau(d) (y - x)^2 + const,
```

the VMP message to `x` is

```text
E_q[log p(y | x, d)]
  = 0.5 E_q[log tau(d)] - 0.5 E_q[tau(d)] (y - x)^2 + const.
```

The curvature of the message, and therefore the precision multiplying the squared error, is `E_q[tau(d)]`, not `exp(E_q[log tau(d)])`. Under affine log-precision `log tau(d) = a + s e(d)`, this gives

```text
tau_eff,natural = E_q[exp(a + s e(d))]
                = exp(a + s E_t) * E_q[exp(s (e(d) - E_t))].
```

The last factor is a moment correction. It equals 1 only when `q(d)` is degenerate, `s = 0`, or the correction is deliberately approximated away for small `s^2 Var_q[e]`. Thus, if the lower-level factor is an ordinary Gaussian likelihood parameterized by precision as its natural parameter, the paper's exact tilt equation does not follow from mean-field factorization alone. The correct message is the arithmetic expected precision.

This is not fatal to D1, but it fixes the modeling commitment. The equation lands exactly when the hyper-layer sends log-precision messages, or when the lower-level approximation explicitly treats the effective gain as the geometric mean of the hyper-posterior over precisions. It is only approximate for a raw mixture over ordinary precision-weighted Gaussian likelihoods.

## What this licenses the paper to say

The paper may say that Section 7's tilt equation is a derived mean-field message in the log-precision-message model: `E_t` is the posterior mean of the depth coordinate, and `beta` and `gamma` are fixed slopes/finite-difference spacings in the generative mapping from depth states to stream log-precisions. The exact claim requires affine log-precision maps sharing one scalar depth coordinate and a lower-level update that uses expected log-precision. If the implemented substrate instead averages natural precisions, or if depth-to-log-precision maps are nonlinear or non-collinear, the equation is an approximation with an explicit moment/curvature error, not a theorem.
