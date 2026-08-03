# V3.6 Round-18 Gate-4 diagnosis

This is a read-only diagnosis. It consumed no new scientific seed, changed no
scientific module, recomputed no Gate-4 criterion statistic, and amended no
verdict. The retained trace hash is `dd28d295cfd793e9848ec4becdfe1179e0fdef6940ef0a4fbbb257118ec48bd0`. Seed `3713860` was only
deterministically reconstructed to recover the exact retained configuration;
its world hash matched `d94e862381618c78aabb83bdd613da4fc70746df73ce46598f85514005e07865`.

## D1 — protect_joint_policy

Classification: **ORACLE_CONSTRUCT**.

The retained maximum is seed `3713860`, with oracle disagreement
`0.8999336559889483`. The production restricted-prior
identity is `4.74e-14`. A fresh hand enumeration from
the declared atomic productions agrees with the production posterior to
`3.04e-17` for the full model and `3.27e-17`
for the lesioned model.

The disagreeing factor is the **partner-reliability latent `L`**, including
its `p(L)=0.5` factor and partner/support/contact likelihood terms. The scorer
stores probabilities for `(structure, cross_sign, reliable)` but exposes
component keys only as `(structure, cross_sign)`. The existing oracle builds
a dictionary from those incomplete keys, so the reliable=1 atom overwrites
the reliable=0 atom. At the argmax coordinate the collapsed comparison is
`0.8999336559889483`. The fresh coordinate-complete oracle agrees with the
production path; there is no production defect.

## D2 — split_context_slot

Classification: **APPARATUS_SUPPORT_ACCOUNTING_ERROR**, not structural
class-heterogeneity.

All 1,000 retained worlds use the same planned configuration: two active
contexts, context-specific cue and outcome scopes, recurrent dynamics,
witnessing evidence, 48 slices, and three cues. Every row reports 144 licensed
structures and positive restricted prior mass `4/7 = 0.5714285714285714`.
Exactly **zero** licensed structures lose prior mass. The grammar contains 144
licensed active-context-count-1 structures, all with positive prior, and 288
excluded active-count-2/3 structures. Those 288 exclusions are grammar-forced:
their only derivations use the deleted active-context-count production.

The failing quantity is not structural prior support. It is
`exp(restricted.log_evidence)`. In all 1,000 worlds this exponentiation
underflows to `0.0` even though the restricted posterior is finite and
normalized within `1e-10`. The apparatus then treats numerical evidence-scale
underflow as empty support. The exact structure tables are included in the
JSON record.

## Standing record

Gate 4 remains **FAIL_RETAINED_UNAMENDED** and Gate 5 remains its retained
derivative FAIL. No repair is made or authorized by this diagnosis. No seed
block or escrow was opened.
