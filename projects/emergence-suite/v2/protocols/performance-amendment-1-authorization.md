# Performance amendment 1 (evaluator authorization, 2026-07-29)

## Classification
Apparatus performance amendment under the pure-software tier: every change below must produce **bit-identical published outputs** (same floats, same RNG draws, same classifications) on the retained verification fixtures, or it is not authorized. Basis: the Fable profiling report (session scratchpad `perf/speed-report.md`); user directive to accelerate execution.

## Authorized changes (tier 1 only)
1. **Oracle audit vectorization** (`ref/oracle.py::brute_force` and its call path in `ExactEngine.infer`): numpy broadcast-joint implementation of the audit. `infer` continues to return the elimination-engine result unchanged, so published outputs are byte-identical by construction; the audit itself must still fire at the 1e-10 tolerance. The pure-Python oracle is retained as a slow reference selectable by flag, and one regression test compares fast-vs-slow audit verdicts on the standing reduced fixtures.
2. **World-loop parallelism** (`run_v244_gates.py` gate2/gate4/misspecification blocks, and equivalent serial loops in the V2.5a runners): extend the existing 8-way subprocess worker pattern already used by gates 3/5 in the same file. Seed-keyed RNG makes per-world results order-independent; the aggregation must collect in deterministic seed order.
3. **CRT graph memoization** (`v244._dynamic`/`_graph`): cache the count lattice keyed by (T, frozen parameters). Verified 1.63x with bit-equal null vectors; the regression test pins bit equality of full 999-replicate null vectors on two retained public seeds.
4. **CRT edge-propagation vectorization**: cached (src, dst, p) arrays + np.add.at ONLY IF accumulation order is provably preserved; the test pins bit equality as in (3). If bit equality cannot be achieved, this item is dropped without appeal.
5. **CS lattice scalarization** (`v24._cs_transition`): same-operation-order scalar arithmetic (measured 1.98x, all score fields bit-equal); regression test pins bit equality of compare_families outputs on retained public seeds.
6. **Test-suite parallelization**: module-parallel execution wrapper (no test content changes).

## Not authorized here
- The R0 enumeration→DP replacement (tier 2): changes float summation order and touches the sampling support; requires its own design (dual validation at small lengths, RNG-custody ruling) and is deferred to the V2.5b-era apparatus work or an explicit follow-up authorization.
- Any change to frozen scientific definitions, criteria, seeds, or results.

## Mandatory verification before merge
1. Bit-equality fixture run: re-score retained public seeds (V2.4.4 identity audit seed 790700 at 32/64/96; two CRT worlds; one V2.5a world) — every published float and classification identical pre/post.
2. Full unit suite green (old and new tests).
3. Timing report (before/after per kernel) committed alongside.
4. Diff summary limited to the six items above.

Disclosed at the next external consultation. Original result files are never regenerated; the amendment affects future runs only.
