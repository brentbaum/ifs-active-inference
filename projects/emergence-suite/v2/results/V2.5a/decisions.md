# V2.5a decisions through Gate 2

## Exact channel marginalization

The frozen missing-channel semantics make every current-slice marginal exact:
the derived candidate uses three copies of the same frozen family, receiving
outcome-only, marker-only, and root-only histories. Missing channels
contribute likelihood one and are therefore summed out exactly. The product
of the three exact prequential evidences is the marginal presentation.

This choice preserves a genuine posterior trajectory for each component of
the derived composite candidate, keeps the original candidate untouched, and
makes the factorized-family zero identity exact. A current-slice-only mask
conditioned on the joint candidate's posterior was rejected because it would
not define an independently updating derived candidate.

## Calibration constructors

Association-carrying cells use the frozen
`generate_world("context_split", seed, length=96)` constructor and are scored
under CS. Independent-channel cells use the frozen
`generate_world("cue_local_relearning", seed, length=96)` constructor and are
scored under CL. No observation, generator, likelihood, prior, or transition
was changed.

## Matching target

The matching target is declared before scoring as
`root_prior_to_posterior_kl`. It uses the persistent binary-root posterior
under the frozen root-observation CPT and scans the same seed's extended
frozen-generator prefix one slice at a time through `8n`. Unattained targets
are censored. The independent oracle separately implements the binary Bayes
scan and censor boundary.

## Numeric freeze

The criterion-free pilot inspected ranges only. Carrying mean ΔI/token was
`0.06240828127319835` and its fifth percentile was
`0.022193786004870927`; maximum observed matching error was
`0.007691801712895963`. The default `0.01` ΔI SESOI and `0.01` matching
tolerance were therefore attainable. The `0.01` bridge root-movement SESOI
was also retained from the pilot's non-criterial root-information range.
All three values were committed before Gate 1 and before opening Gate 2.

## Finite-information bound

Product-marginal accounting has the exact table supremum
`6.704414354964107`. It equals the inherited V2.4 common-emissions bound, so
there is no third *distinct* constant. Reports name the marginal accounting
value explicitly alongside the inherited formation bound
`3.801426508560692` and V2.4 bound `6.704414354964107`.

## Retained software preflight

The first pilot invocation failed before generating a world because the
sandbox denied Python's process-pool semaphore-limit query. The replacement
uses the already-established subprocess-partition orchestration pattern.
The failure, zero-seed status, and unchanged scientific definitions are
retained in `development-failures.md`.

