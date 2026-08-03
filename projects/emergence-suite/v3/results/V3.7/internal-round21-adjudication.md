# V3.7 Round-21 adjudication (INTERNAL)

**Authority.** Evaluator (Fable) as advisor per Brent's 2026-08-03
instruction; INTERNAL labeling, open to retroactive external review.

## Subject: Population-A37 apparatus custody stop

`FAIL_APPARATUS_CUSTODY_STOP` at seed 3734001: the v3.7 worker row embeds a
nested `MappingProxyType`, which the multiprocessing pool cannot pickle. One
seed (3734000) persisted; prefetch ambiguity makes the executed suffix
unprovable; the block is burned under the standing prefix-ambiguity rule.
This is a pre-scientific infrastructure defect — no world was scored
incorrectly, no criterion touched. The zero-seed proof battery (max error
2.22e-16) and design freeze stand.

## Ruling 21.1 — repair

Authorized, serialization-boundary only: convert immutable mapping views to
plain dicts at the worker-row serialization boundary (or make the row type
natively picklable). No scientific computation changes; differential audit
required; v3.6 frozen hashes and the v3.7 design-freeze scientific content
bitwise unchanged.

## Ruling 21.2 — permanent pre-block serialization round-trip proof

New standing rule, joining the defense battery: before ANY parallel block
opens, the exact worker-row type produced by the runner must be proven to
round-trip through the pool's serialization (pickle → unpickle → equality
check against the original, including nested types) on the enumerable dummy,
zero seeds. This would have caught this stop and converts the entire defect
class from block-burning to pre-block.

## Ruling 21.3 — seeds

Block `3734000:3735999` is barred (one-seed prefix retained as evidence).
Replacement A37-R1: `3746000:3747999`. C37 (`3736000:3737999`) and T37
(`3740000:3745999`) were never opened and remain live. Chain unchanged:
A37-R1 → C37 → T37 → prediction scoring.
