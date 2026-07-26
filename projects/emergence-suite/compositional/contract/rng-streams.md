# RNG namespaces and paired streams

Contract version `rng-51-v1` uses counter-derived SHA-256 draws so execution
order and arm divergence cannot shift a paired stream.

For escrowed unsigned 64-bit seed `s`, component kind `k`, component ID `i`,
time `t`, and zero-based draw index `d`, compute:

```text
SHA256(
  "ifs-ai-51-rng-v1" || NUL ||
  uint64be(s) || NUL ||
  utf8(k) || NUL ||
  utf8(i) || NUL ||
  uint64be(t) || NUL ||
  uint64be(d)
)
```

The first eight digest bytes, interpreted as an unsigned big-endian integer,
give `u = (x + 0.5) / 2^64`. Distribution transforms consume declared draw
indices; rejection sampling is forbidden.

The elementary transforms are exact:

- `uniform(lower, upper)` returns `lower + (upper - lower) * u`;
- inclusive `integer_uniform(lower, upper)` returns
  `lower + floor((upper - lower + 1) * u)`;
- categorical sampling, including a transition-matrix row, returns the first
  declared value whose cumulative probability is strictly greater than `u`.
  If floating-point accumulation leaves no such bucket, it returns the final
  declared value as a rounding fallback.

`scripts/contract/test_rng_transforms.jl` freezes boundary vectors, including
categorical equality at a cumulative boundary and the final-bucket fallback.
Beta and truncated-Gaussian numerical inverses remain frozen-engine
implementations and must pass their high-precision engine vectors.

World-generation component kinds are `latent_factor`, `process`, `emission`,
`distribution`, `outcome`, and `world_contingency`. A paired-stream component
is the typed table
`{ kind = "...", id = "..." }`.

For a component declared paired across arms, the key above contains no arm ID.
For an unpaired component, the component ID is replaced by
`<arm-id>/<component-id>`. Paired components therefore remain identical even
when one arm disables an observation or contingency.

Factor-initialization and process-transition categorical draws consume index
`0`. Emission draws use the zero-based occurrence ordinal among scheduled
occurrences of the same emission ID at that tick, including occurrences later
skipped by a false trigger. Beta and truncated-Gaussian transforms use fixed
inverse-CDF algorithms declared by the frozen engine; their indices follow the
scalar lifetime rule.

Action-success and potential-hazard Bernoulli draws use component kind
`outcome`, the mapping ID, canonical tick, and draw index `0`. Exposure is
deterministic conditional on the selected configuration and success, so it
consumes no additional draw.

Canonical RNG ticks and scalar-distribution draw indices are defined in
`world-semantics.md`. Analysis resampling does not consume world streams; it
uses the public deterministic construction in
`analysis-expression-grammar.md`.
