# C-V233-M-bank

Sealed verdict: **FAIL**.

The frozen `3e9bad2` identity check passed for all
`25` manifest files. The official run then
stopped at the first released candidate seed, `815001`, before constructing a
state:

> `ValueError: development seeds must be in [0, 799999]`

The error is raised by frozen `ref/rng.py` through the frozen
`construct_bank_state` call. Remapping the seed, replacing the RNG, or
monkeypatching the guard would change the frozen instrument and was not done.

## Scientific precondition — FAIL (unexecutable)

No q0(P) value was generated, so moderate/strong/very-strong eligibility
counts, rates, 95% intervals, and fill positions do not exist. Reporting
zeros would incorrectly describe observed formation yield; reporting inferred
values would fabricate data.

## Semantic integrity — NOT RUN

No bank state exists for the retained-state provenance reconstruction or the
ten-state one-posterior sample.

## Process custody — FAIL (architecture)

The frozen identity passed, but the frozen constructor cannot consume the
released Gate-6 seed domain. `per_seed.csv` records all 800 intended seeds in
order: seed 815001 is marked rejected by the frozen guard and seeds
815002–815800 are marked not consumed after the mandatory stop. There are no
eligibility decisions or serialize/rehash results to claim.

## Distributional stress — unavailable, descriptive only

No q0(P) distribution or fill curve can be published because no candidate
posterior was generated. This descriptive class is non-criterial.

## Standing

Scientific precondition: **FAIL_UNEXECUTABLE**. Semantic integrity:
**NOT_RUN**. Process custody: **FAIL_ARCHITECTURE**. Distributional stress:
**UNAVAILABLE_DESCRIPTIVE**. Under the precommitted interpretation, this is an
architecture/prospection failure of the frozen bank procedure. The
maintenance challenge and seeds `816001:816900` remain closed and were not
accessed.
