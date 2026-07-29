# Pre-seal linter template (four-layer, per round-8 adjudication + master spec §1.9)

**Every future sealed challenge completes this before its plaintext hash is committed. The linter output and constructor-call hashes commit FIRST. A "no" on the final question blocks sealing.**

## Layer checklist
1. **Inference expressibility** — every requested posterior, evidence term, query, and metric exists as a frozen public field. List each with its field name.
2. **World expressibility** — every requested world generates through a frozen public constructor (post-R0: through the public grammar IR). No constructor may be assumed; each is named and dry-run.
3. **Protocol expressibility** — every intervention, schedule, and stopping rule is declarable without hidden code.
4. **Composition expressibility** — required combinations of supported primitives coexist in one world and protocol via an actual public composition operator (having each component separately is insufficient).

## Traceability table (one row per private cell)

| Field | Required entry |
|---|---|
| Public obligation | Exact contract/spec clause authorizing the cell |
| Constructor | Frozen function/API call (post-R0: grammar IR expression) |
| Arguments | All declared arguments and supported domains |
| World-process composition | Exact frozen composition operation |
| Bridge path | Frozen bridge function and family parameter |
| Conditioning | Whether rejection, post-selection, or conditioning occurs (must be publicly exposed as a scientific generator operation, else forbidden) |
| Requested readouts | Frozen fields proving they exist |
| Dry-run result | Constructor/schema success on ≥2 public development seeds |
| Scientific scoring during dry-run | Must be false (construction success, schema, lengths, supports, field presence ONLY) |
| New code required | Must be false |

## Freeze rules
- Dry-run each cell on at least two public development seeds; never inspect family selection, evidence, margins, transfer, or any criterion statistic.
- Mixed-process cells must invoke an actual public composition operator.
- Every formed-state bridge must accept the requested world family through a public parameter.
- Criteria pass the 7-item adjudication-criterion audit (distinct; construct interpretation; calibrated null or SESOI; attainable power evaluated without criterion worlds; no contradiction with already-viewed data from the same frozen generator and budget; failure interpretation pre-committed; class assigned).
- Linter output + constructor-call hashes committed before the challenge plaintext hash.

## Final blocking question
**Could the exact sealed population be generated and scored after reveal with zero source-code change?** [YES required]
