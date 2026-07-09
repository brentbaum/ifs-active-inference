#!/usr/bin/env python3
"""Toy BMR-opacity demo for D2.

This script uses only numpy plus the Python standard library. It compares a
full coupling prior against a reduced/pruned prior with the Dirichlet BMR
identity. Reflexivity precision E controls how much of the coupling evidence is
available as a self-indexed posterior: alpha_E = b_full + rho(E) * counts.
"""

import math

import numpy as np


def log_beta(alpha):
    alpha = np.asarray(alpha, dtype=float)
    return float(sum(math.lgamma(x) for x in alpha) - math.lgamma(float(alpha.sum())))


def rho(E, E0=1.0):
    E = float(E)
    if E <= 0.0:
        return 0.0
    return E / (E + E0)


def bmr_delta_full_to_reduced(b_full, b_reduced, counts, E, E0=1.0):
    """Return log evidence difference log p(y|reduced) - log p(y|full)."""
    b_full = np.asarray(b_full, dtype=float)
    b_reduced = np.asarray(b_reduced, dtype=float)
    counts = np.asarray(counts, dtype=float)
    r = rho(E, E0)

    alpha = b_full + r * counts
    alpha_reduced = alpha + b_reduced - b_full
    if np.any(alpha_reduced <= 0.0):
        raise ValueError("Reduced posterior parameters must stay positive.")

    return (
        log_beta(b_full)
        - log_beta(b_reduced)
        + log_beta(alpha_reduced)
        - log_beta(alpha)
    )


def find_threshold(b_full, b_reduced, counts, margin, E0=1.0):
    grid = np.r_[0.0, np.geomspace(1e-4, 100.0, 2000)]
    deltas = np.array(
        [bmr_delta_full_to_reduced(b_full, b_reduced, counts, E, E0) for E in grid]
    )
    hits = np.flatnonzero(deltas >= margin)
    if len(hits) == 0:
        return None
    index = int(hits[0])
    return float(grid[index]), float(deltas[index])


def print_table(title, b_full, b_reduced, counts, margin):
    print(title)
    print(f"  full prior     b_F = {np.asarray(b_full, dtype=float).tolist()}")
    print(f"  reduced prior  b_R = {np.asarray(b_reduced, dtype=float).tolist()}")
    print(f"  counts           n = {np.asarray(counts, dtype=float).tolist()}")
    print(f"  prune margin kappa = {margin:.3f} nats")
    print()
    print("  E_t      rho(E_t)   delta_F_R-F   decision")
    print("  ------   --------   -----------   --------")
    for E in [0.0, 0.01, 0.1, 0.5, 1.0, 5.0, 20.0]:
        delta = bmr_delta_full_to_reduced(b_full, b_reduced, counts, E)
        decision = "prune" if delta >= margin else "keep"
        print(f"  {E:6.2f}   {rho(E):8.3f}   {delta:11.3f}   {decision}")
    threshold = find_threshold(b_full, b_reduced, counts, margin)
    if threshold is None:
        print("  threshold: not reached on E_t in [0, 100]")
    else:
        E_star, delta_star = threshold
        print(f"  threshold: E_t ~= {E_star:.4f}, delta_F ~= {delta_star:.3f}")
    print()


def main():
    # Full prior encodes the frozen coupling: state 1 is expected.
    # Reduced prior is the pruned/no-coupling alternative: no strong preference.
    b_full = np.array([2.0, 12.0])
    b_reduced = np.array([7.0, 7.0])
    margin = 3.0

    # Late witnessed contact: evidence now favors state 0, so reduction wins once
    # enough of the counts are reflexively accessible.
    late_counts = np.array([36.0, 4.0])

    # Premature prompt: the old coupling still predicts the data, so reduction
    # does not win even at high reflexivity.
    early_counts = np.array([4.0, 36.0])

    print("D2 toy demo: BMR informativeness scales with reflexivity precision")
    print("delta_F_R-F > 0 favors the reduced/pruned model.")
    print("At E_t = 0, rho = 0 and delta_F_R-F = 0: no data-driven comparison.")
    print()
    print_table("Late witnessed evidence", b_full, b_reduced, late_counts, margin)
    print_table("Premature evidence", b_full, b_reduced, early_counts, margin)


if __name__ == "__main__":
    main()
