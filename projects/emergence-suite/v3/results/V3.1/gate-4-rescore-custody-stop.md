# V3.1 Gate-4 rescore custody stop

Status: **STOPPED — RETAINED WORLDS NOT AVAILABLE**.

The selectivity adjudication requires the exact retained 2,000 Gate-4 worlds
to be rescored and explicitly prohibits world regeneration. A complete
custody inventory found:

- the two aggregate verdict records, `gate-4.json` and
  `gate-4-repaired.json`;
- no serialized `FormationWorld` records;
- no per-world slice traces;
- no per-world state hashes;
- no temporary or committed retained-world artifact for seeds
  3110000–3111999.

The repaired Gate-4 runner generated each world in memory, reduced the
population to aggregate statistics, and discarded the world objects when the
process exited. The aggregate record is insufficient to compute a
restricted-prior identity per world or to support an independent-oracle
cross-check.

Regenerating the worlds from their seeds and the committed deterministic
generator would probably reproduce them, but it is still world regeneration
and is therefore excluded by the binding adjudication. Reconstructing worlds
from aggregate metrics is impossible.

No inference or oracle code was changed. No Gate-4 rescore was started. The
Gate-5 block and C-V31 escrow remain untouched. Continuation requires either
the original serialized worlds or explicit evaluator authorization to
reconstruct them from the committed generator, seed-to-lesion partition, and
seed block.
