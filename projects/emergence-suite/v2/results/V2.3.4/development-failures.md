# V2.3.4 development-failures ledger

No assigned gate criterion failed.

## Prospective Gate-5 diagnostic rejection

Before opening Gate 5, two single-world diagnostic formulations failed their
public-dummy screen:

- `masking_direction`: a masked-minus-visible posterior displacement was not
  reliably signed because its sign depended on the prior and generating truth.
- `precision_direction`: full-precision update magnitude was not reliably
  larger than low-precision update magnitude in a saturated full-efficacy
  world.

These were not gate results and no assigned Gate-5 seed had been evaluated.
They were replaced apparatus-first by truth-relative error costs and screened
on public seeds `1299900:1299999`. The retained screen is
`gate-5-attainability-public-dummies.json`.

## Execution-backend preflight

The first Gate-5 invocation stopped before assigned-world execution because
the sandbox denied the process-pool semaphore query:

`PermissionError: [Errno 1] Operation not permitted`

The ordered thread fallback changed no scientific code or result.
