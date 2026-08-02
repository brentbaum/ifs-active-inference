# V3.6 replacement Gate 4 — custody stop

Status: **HONEST_STOP_NONFINITE_WORKER_ROW**.

The replacement Gate-4 runner opened the authorized block
`3702000:3706999`. Its first returned worker row was seed `3702000`, lesion
`grow_mode_slot`. The permanent finite-row guard rejected
`restricted_prior_identity_error` and `masked_channel_neutrality_error` as
non-finite before the scientific row could be serialized. In this lesion the
masked statistic is assigned directly from the restricted-prior identity
statistic, so this is one localized non-finite computation, not two independent
failures.

The rejection provenance was fsynced as the first trace record. Its file hash,
`58cc82d0ffb764a5986adff907a5aeee6437bab5c454dff70525d1752315e2f8`,
matches the incremental hash ledger. No criterion was evaluated, no Gate-4
verdict was computed, and no repair or scientific-module change was attempted.

Because the runner used a multiprocessing pool with prefetch, the exact
executed seed prefix cannot be established from the single persisted rejection
record. No further seed was deliberately executed after the stop. Under the
binding adjudication, this custody incident returns the program to external
adjudication immediately.
