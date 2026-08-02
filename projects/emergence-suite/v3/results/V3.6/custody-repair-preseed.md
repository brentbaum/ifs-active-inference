# V3.6 replacement-block custody repair

Verdict: **PASS_PRESEED_APPARATUS_REPAIR**.

The conditioned-support helper now keeps retained exact-zero programs in the
comparison support. A restricted scorer may omit their storage entry, but the
comparison still treats that entry as an exact zero rather than as absent.
The enumerable regression is exact (`0.0`).

A shared apparatus guard now recursively checks every worker row for `inf` or
`nan` before strict serialization. On rejection it writes a finite provenance
record and an incremental hash ledger before stopping. Two targeted,
seed-free tests passed. All scientific source hashes pinned by the bridge spec
remain bitwise unchanged. No seed was consumed by this repair verification.
