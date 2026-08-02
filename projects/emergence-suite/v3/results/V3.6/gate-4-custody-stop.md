# V3.6 Gate 4 custody stop

Verdict: **STOP**. No Gate-4 criterion was evaluated.

The one authorized Gate-4 execution opened block `3630000:3634999`. The first
returned worker row could not be serialized because
`masked_channel_neutrality_error` was the non-finite sentinel `inf`. Strict
JSON custody correctly rejected it with:

> `ValueError: Out of range float values are not JSON compliant: inf`

The runner's conditioned-support helper had treated the scorer's retained
zero-probability entries as a support mismatch. That is an apparatus defect,
not a scientific lesion result.

## Custody consequence

The trace file exists but is zero bytes, with SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
No record or event ledger was persisted, and no hash ledger was written. Seed
`3630000` certainly executed. Because the multiprocessing pool may prefetch
tasks, the exact additional unpersisted executed prefix cannot be established.
The block therefore cannot be resumed without risking double consumption.

No repair or rerun was attempted. Gate 5 remained closed. No escrow or barred
block was touched. Under the round-13 persist-before-output rule and the prior
closed V3.6 custody incident, work stops here for evaluator adjudication.
