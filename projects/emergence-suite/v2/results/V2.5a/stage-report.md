# V2.5a format-core status through Gate 3

Outcome: **Stage 0 complete; Gate 1 PASS; Gate 2 PASS; Gate 3 FAIL.** The
format-core ratchet stops at Gate 3. No Gate-4, Gate-5, master-spec
completion, or sealed-challenge block was opened.

## Stage 0

The frozen likelihood-interface design check passed: all three observation
channels have exact marginals through the existing missing-channel
semantics. Scoring-only presentation, derived-candidate, ΔI, and matching
operators were implemented with separately authored enumeration and matching
oracles.

The range-only pilot consumed `755000:755199`, 100 association-carrying and
100 independent worlds. It evaluated no criterion. The block is barred from
all later criteria. Defaults were frozen prospectively at:

- ΔI SESOI: `0.01` nats/token;
- matching KL tolerance: `0.01` nats;
- bridge root-movement SESOI: `0.01`.

## Gate 1

All ten semantic proofs passed. Maximum factorized per-slice error was
`4.440892098500626e-16`; maximum increment-identity error was
`8.881784197001252e-16`; independently enumerated CS ΔI differed by
`4.440892098500626e-16`. Matching and censoring reproduced exactly. The
association-dose dummy rose monotonically from numerical zero to
`0.12541971560214674` expected nats.

## Gate 2

The block `756000:756399` supplied 200 association-carrying and 200
independent worlds at 96 slices.

- carrying ΔI/token: `0.06272370289643629`, 95% bootstrap CI
  `[0.058370646392175825, 0.06708781225268459]`;
- frozen SESOI: `0.01`;
- independent maximum absolute ΔI: `1.1324274851176597e-14`;
- maximum increment-identity error: `2.6645352591003757e-14`;
- V2.4 source identity and its cumulative unit regression: PASS.

All Gate-2 blocking criteria passed. Full per-world distributions,
per-channel decompositions, and per-slice arrays are retained.

## Cumulative verification and constants

The full suite passed `101/101` in `442.173` seconds.

- `B_max_inherited_formation = 3.801426508560692`;
- `B_max_v24_common_emissions = 6.704414354964107`;
- `B_max_v25a_marginal_accounting = 6.704414354964107` (not distinct).

## Gate 3 honest stop

All four committed Epoch-A Gate-3 blocks were consumed once. Assay 1 passed:
the six raw ΔI/token means were monotone from `-0.05333` to `0.06817`, and
the slope was `0.12353`, 95% CI `[0.11399, 0.13292]`.

Gate 3 failed three blocking requirements:

1. information-matching median `m*/n` was not nondecreasing across dose:
   `[0.0625, 0.0625, 0.0625, 0.0625, 0.0520833, 0.0520833]`;
2. only `103/120` formed-P bridge worlds were within the frozen `0.01` KL
   tolerance, so the nominal bridge contrast is not an information-matched
   result;
3. the bridge per-slice decomposition failed to recombine in 64/120 worlds,
   with maximum error `0.2470998783239713`.

The nominal, unqualified bridge contrast was `0.06111`, 95% CI
`[0.04403, 0.08099]`, and exact G-fixed/zero-association controls passed, but
these do not override the matching and decomposition failures.

The post-stop full suite passed `103/103` in `417.148` seconds.
