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

## Gate-3 protocol definitions frozen before execution

The six association doses are `{0,.2,.4,.6,.8,1}`. The protocol-level
presentation operator retains a nested fraction of each cue's original
markers and permutes the remaining marker multiset within that cue. Outcomes,
roots, cue order, missingness, and every channel multiset are unchanged.
Dose one is bitwise identity; dose zero is the complete
marginal-preserving presentation. No likelihood parameter is interpolated.

The preregistered isotonic test requires the six raw population means to be
nondecreasing and their equal-weight pool-adjacent-violators fit to require
no adjustment beyond `1e-12`. The dose slope is the ordinary slope across
the six means; its 95% interval uses 10,000 whole-world bootstrap replicates
resampling independently within each frozen dose cell.

Information-matching doses use 50 worlds per level. The association label
does not enter the frozen root-channel matching likelihood; it tests the
declared expectation that median `m*/n` is nondecreasing, with equality
allowed by “monotone.”

For the formed-P seam, joint presentation uses the frozen context-indexed
root posterior. Marginal presentation factorizes marker context and root
evidence: its present-root posterior is the exact model average
`q(now)q(G|R) + q(then)q_0(G)` from the two independently scored marginal
components. Matching scans the same seed's extended root channel to the
joint root-KL target. The root-movement difference is decomposed by
telescoping the joint and matched-marginal prediction trajectories, including
any marginal extension beyond the joint history.
