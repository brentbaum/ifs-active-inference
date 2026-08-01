# V3.6-R1 native-fixture proof diagnosis stub

Status: **HONEST_STOP_PRE_BLOCK_NATIVE_FIXTURE_PROOF_FAILURE**.

The new permanent proof was serialized and hashed before its verdict was
printed. It consumed no seed. It returned `FAIL_APPARATUS_STOP`, so replacement
Population B and every later block remain unopened.

The failure is localized to the V2 partner-fixture proof. Production and oracle
agree within `2.7755575615628914e-17`, but both enumerated probability sums are
`1.7912000000000001`, not one. Both proof paths made the same semantic indexing
mistake: they treated `v26a.EMISSIONS[state, token]` as a two-category emission
row. In the frozen module, the four columns are separate typed channels
(`regulation`, `remaining`, `respect`, `trust`), each holding a Bernoulli
success probability. The native fixture uses the `remaining` channel at column
1 and then samples a binary observation. Columns 0 and 1 are not complementary
outcomes.

Thus separate code paths repeated the same apparatus mistake. The frozen
partner generator and scorer are not implicated by this record; the mandatory
proof itself is non-normalized and therefore cannot authorize a block.

All other finite comparisons passed: V2 identity `0`, outcome `0`, context
`8.67e-19`, contact `0`; V3 protect `5.42e-20`, temporal `6.94e-18`. Frozen
scientific source hashes remain bitwise identical.

Per the binding stop rule, there is no local proof repair. Blocks
`3700000:3701999`, `3692001:3693999`, `3694001:3695999`,
`3684000:3689999`, `3630000:3634999`, and Gate 5 remain unopened pending an
external ruling.

