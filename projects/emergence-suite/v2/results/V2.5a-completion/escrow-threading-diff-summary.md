# V2.5a completion escrow-threading diff summary

Authorization:
`results/V2.5a-completion/escrow-threading-amendment-authorization.md`.

## Source change

Only `ref/v25a_completion.py` changes:

- `_development_rng` accepts optional `released_block`;
- `generate_world` exposes and threads optional `released_block` to every
  component RNG stream;
- `shuffled_episodes`, the only sibling public entry point drawing
  seed-keyed RNG, exposes and threads the same parameter;
- omission or `None` resolves to the unchanged Epoch-B development block
  `1000000:1899999`;
- an explicitly supplied block is validated by the standing
  `component_rng` release guard.

`score` and all other scoring/readout entry points draw no RNG and therefore
require no parameter.

## Verification change

`tests/test_v25a_completion.py` adds:

- two pinned development-world byte fixtures;
- two pinned shuffled-presentation byte fixtures;
- default-versus-explicit-development-block equality;
- rejection without release authority and acceptance with an explicit
  matching release block.

No escrow seed was used. No likelihood, prior, normalized table, posterior,
readout, threshold, protocol, scientific result, or existing world ledger
changed. The full fast suite passed 20/20 modules in `53.250s`.

