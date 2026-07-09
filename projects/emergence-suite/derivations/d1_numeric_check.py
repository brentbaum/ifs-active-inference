#!/usr/bin/env python3
"""Numeric checks for D1 tilt derivation.

Uses numpy only. It compares:

1. expected-log-precision message vs. closed-form tilt under affine maps;
2. expected-log-precision message vs. affine tilt under nonlinear maps;
3. natural-precision averaging vs. geometric tilt under affine maps.
"""

import itertools
import numpy as np


def simplex_grid(n_states, step):
    """Yield probability vectors on an n-state simplex with coordinates on a grid."""
    units = int(round(1.0 / step))
    if abs(units * step - 1.0) > 1e-12:
        raise ValueError("step must divide 1.0 exactly")

    def compositions(total, parts):
        if parts == 1:
            yield (total,)
            return
        for first in range(total + 1):
            for rest in compositions(total - first, parts - 1):
                yield (first,) + rest

    for counts in compositions(units, n_states):
        yield np.array(counts, dtype=float) / units


def rel_err(actual, expected):
    denom = np.maximum(np.abs(expected), 1e-300)
    return np.abs(actual - expected) / denom


def exact_affine_check():
    e = np.array([0.0, 0.5, 1.0, 1.5])
    q_grid = list(simplex_grid(len(e), 0.1))
    r_values = [0.2, 1.0, 3.0]
    pi_part_values = [0.4, 1.5, 7.0]
    lambda_ctx_values = [0.3, 2.0, 9.0]
    beta_values = [0.0, 0.15, 0.7, 1.4]
    gamma_values = [0.0, 0.2, 0.9, 1.8]

    max_error = 0.0
    worst = None
    for q, r_t, pi_part, lambda_ctx, beta, gamma in itertools.product(
        q_grid, r_values, pi_part_values, lambda_ctx_values, beta_values, gamma_values
    ):
        e_t = float(q @ e)
        ell_pi = np.log(r_t) + np.log(pi_part) - beta * e
        ell_lambda = np.log(lambda_ctx) + gamma * e

        pi_msg = np.exp(float(q @ ell_pi))
        lambda_msg = np.exp(float(q @ ell_lambda))

        pi_closed = r_t * pi_part * np.exp(-beta * e_t)
        lambda_closed = lambda_ctx * np.exp(gamma * e_t)

        err = max(
            float(rel_err(pi_msg, pi_closed)),
            float(rel_err(lambda_msg, lambda_closed)),
        )
        if err > max_error:
            max_error = err
            worst = (q, r_t, pi_part, lambda_ctx, beta, gamma)

    return max_error, worst


def nonlinear_expected_log_divergence():
    e = np.array([0.0, 0.5, 1.0, 1.5])
    q_grid = list(simplex_grid(len(e), 0.05))
    beta = 0.7
    gamma = 0.9
    r_t = 1.0
    pi_part = 2.0
    lambda_ctx = 3.0
    k_pi_values = [0.05, 0.15, 0.35, 0.75]
    k_lambda_values = [-0.05, -0.2, 0.25, 0.6]

    errors = []
    worst = None
    for q, k_pi, k_lambda in itertools.product(q_grid, k_pi_values, k_lambda_values):
        e_t = float(q @ e)
        ell_pi = np.log(r_t) + np.log(pi_part) - beta * e + k_pi * e**2
        ell_lambda = np.log(lambda_ctx) + gamma * e + k_lambda * e**2

        pi_msg = np.exp(float(q @ ell_pi))
        lambda_msg = np.exp(float(q @ ell_lambda))

        # The paper tilt using only the affine slope terms.
        pi_closed = r_t * pi_part * np.exp(-beta * e_t)
        lambda_closed = lambda_ctx * np.exp(gamma * e_t)

        err = max(
            float(rel_err(pi_msg, pi_closed)),
            float(rel_err(lambda_msg, lambda_closed)),
        )
        errors.append(err)
        if worst is None or err > worst[0]:
            worst = (err, q, k_pi, k_lambda, e_t)

    return np.array(errors), worst


def natural_precision_obstruction():
    e = np.array([0.0, 0.5, 1.0, 1.5])
    q_grid = list(simplex_grid(len(e), 0.05))
    beta_values = [0.2, 0.7, 1.4, 2.0]
    gamma_values = [0.2, 0.9, 1.8, 2.5]
    r_t = 1.0
    pi_part = 2.0
    lambda_ctx = 3.0

    errors = []
    worst = None
    for q, beta, gamma in itertools.product(q_grid, beta_values, gamma_values):
        e_t = float(q @ e)
        ell_pi = np.log(r_t) + np.log(pi_part) - beta * e
        ell_lambda = np.log(lambda_ctx) + gamma * e

        # Natural-precision VMP curvature averages tau, not log tau.
        pi_natural = float(q @ np.exp(ell_pi))
        lambda_natural = float(q @ np.exp(ell_lambda))

        pi_closed = r_t * pi_part * np.exp(-beta * e_t)
        lambda_closed = lambda_ctx * np.exp(gamma * e_t)

        err = max(
            float(rel_err(pi_natural, pi_closed)),
            float(rel_err(lambda_natural, lambda_closed)),
        )
        errors.append(err)
        if worst is None or err > worst[0]:
            worst = (err, q, beta, gamma, e_t)

    return np.array(errors), worst


def main():
    exact_error, exact_worst = exact_affine_check()
    nonlinear_errors, nonlinear_worst = nonlinear_expected_log_divergence()
    natural_errors, natural_worst = natural_precision_obstruction()

    print("D1 numeric check")
    print("================")
    print(
        "Exact affine log-precision message: "
        f"max relative error = {exact_error:.3e}"
    )
    print(f"  worst case = {exact_worst}")
    print(
        "  pass < 1%: "
        f"{'YES' if exact_error < 0.01 else 'NO'}"
    )
    print()

    print("Nonlinear log-precision mapping, compared to affine tilt:")
    print(f"  median relative error = {np.median(nonlinear_errors):.3%}")
    print(f"  95th percentile error = {np.quantile(nonlinear_errors, 0.95):.3%}")
    print(f"  max relative error = {np.max(nonlinear_errors):.3%}")
    err, q, k_pi, k_lambda, e_t = nonlinear_worst
    print(
        "  worst case: "
        f"error={err:.3%}, q={q}, E_t={e_t:.3f}, "
        f"k_pi={k_pi}, k_lambda={k_lambda}"
    )
    print()

    print("Natural-precision averaging under affine log-precision maps:")
    print(f"  median relative error = {np.median(natural_errors):.3%}")
    print(f"  95th percentile error = {np.quantile(natural_errors, 0.95):.3%}")
    print(f"  max relative error = {np.max(natural_errors):.3%}")
    err, q, beta, gamma, e_t = natural_worst
    print(
        "  worst case: "
        f"error={err:.3%}, q={q}, E_t={e_t:.3f}, "
        f"beta={beta}, gamma={gamma}"
    )


if __name__ == "__main__":
    main()
