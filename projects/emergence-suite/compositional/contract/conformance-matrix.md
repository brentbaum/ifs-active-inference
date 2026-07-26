# Public contract conformance matrix

`scripts/contract/test_schema_variants.py` materializes one accepted and one
rejected fixture for every discriminated contract `1.0.0` JSON-Schema branch:

- discrete and bounded-Gaussian configuration channels;
- six distribution families;
- five process forms;
- discrete and bounded-Gaussian emissions;
- the closed action-contingency form;
- action and hazard outcome forms;
- typed equality, numeric, membership, and finite predicates in both protocol
  and analysis schemas;
- four protocol event forms;
- four intervention target forms;
- external-proxy and latent-intervention triggers;
- fixed and crossing stopping rules;
- four control declarations;
- every closed analysis-expression form;
- none, exact-binomial, and bootstrap interval forms;
- lower, upper, between, and equivalence decision-rule forms.

Each rejected partner is derived from its accepted fixture by removing one
branch-required field. A single prefix-schema requires every accepted fixture to
match its exact `$defs` reference; a second prefix-schema requires every
rejected fixture not to match that reference.

`scripts/contract/test_semantic_conformance.jl` adds rejection fixtures for
cross-file and non-JSON-Schema rules:

- edge type signatures and duplicate semantic edges;
- inactive-node edge, trigger, and analysis restrictions;
- coupled-parent table dimensions;
- emission masked-scope containment;
- episode divisibility and action-contingency target typing;
- protector-only actors, structure cardinality, and candidate distinctness;
- inactive structure nodes with forbidden candidate declarations;
- joint-action plurality/safety reconciliation and empty-support failure;
- world truth in protocol triggers;
- channel/event source agreement and predicate type agreement;
- exact joint-action trace labels;
- complete action/hazard outcome mappings and change-point-only switch paths;
- scheduled intervention/control references;
- typed paired-stream namespaces;
- explicit oriented evidence-budget pairs, including a two-by-two accepted
  vector and reversed-pair rejection;
- analysis requested-trace closure;
- event-unit rejection for tick-only fields and cross-arm operators;
- exact controls for treatment contrasts;
- first-crossing operands, exact-binomial types, and structural argmax paths;
- circular `derived.*` analysis sources;
- structured interpretation locks;
- strict UTF-8 archive input.

`scripts/contract/test_analysis_math.jl` freezes arithmetic mean, odd/even
median, sample standard deviation, nearest-rank quantiles, ordinary and
cross-arm unit-key serialization, deterministic bootstrap indices, paired
bootstrap resampling, Clopper-Pearson endpoints, and exact decision-boundary
logic.

`scripts/contract/test_rng_transforms.jl` freezes continuous-uniform,
inclusive-integer-uniform, and inverse-categorical transforms at lower,
cumulative, upper, and rounding-fallback boundaries.

`scripts/contract/test_seed_escrow.jl` freezes seed-range, exact public-contract
commit/content-manifest binding, parsing, and purpose-suppression rules.

All suites plus the public dummy's authoritative validation and independent
archive verification must pass before private challenge authoring.
