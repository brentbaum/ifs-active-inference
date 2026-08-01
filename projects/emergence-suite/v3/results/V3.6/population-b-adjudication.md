# V3.6-R1 Population-B adjudication (context-fixture defect)

Evaluator: Fable. Date: 2026-08-01.

## Findings adopted

1. **Fixture identity refuted.** The Population-B context fixture was not
   the frozen v2 context module's own prior predictive: it initialized
   every context path at `then` (module prior `[0.5, 0.5]`) and collapsed
   the three-valued marker CPT to binary by assigning `none`-marker mass to
   `then`. Maximum joint-atom error `0.0787` on the enumerable dummy;
   correcting both productions in isolation gives error exactly `0`.
2. **The ECE miss is fully explained by the wrong generator.** Observed
   context ECE `0.0575` sits at the 100th percentile of the parametric
   calibration null; the four correctly-built targets all sit inside their
   nulls (39th–95th percentiles). There is no evidence of a v2
   probabilistic-coherence defect. The `0.05` block itself is fair at this
   sample size (null q99 ≈ 0.037).
3. **Custody.** The unit-test sink note is retained as written (zero seeds,
   deterministic dummies, no data flow into the block). The Population-B
   block's own custody was perfect. The block `3690001:3691999` is burned
   regardless: its context fixtures were generated from the wrong joint.

## Ruling

Round 12 provides that another apparatus failure "returns to the
evaluator" — this is that return, and it is adjudicated as a **narrow
fixture repair**, not a new requalification cycle: the external criteria,
margins, definitions, and populations are untouched; the implementation
simply failed to construct the population round 12 defined. The V3.4
distributional-identity lesson already made this check mandatory; it was
run only after the block. That ordering defect is repaired permanently:

> **New permanent qualification proof (pre-block fixture identity).** For
> every native-prior fixture family, the fixture generator's joint over
> (latent path, observation tokens) must match the frozen module's own
> prior predictive by direct enumeration on an enumerable dummy at
> `1e-10`, PASSING BEFORE the fixture block opens. A post-hoc identity
> audit does not qualify.

Authorizations:

- Repair the context fixture only (module-prior initialization; exact
  three-valued marker bridge as the module defines it). No scorer, module,
  criterion, or definition changes; scientific source hashes bitwise
  unchanged.
- Replacement Population-B block: `3700000:3701999` (allocated from the
  unassigned dev namespace by this adjudication; recorded in the seed-map
  addendum). `3690001:3691999` is barred.
- Populations A and C and the tournament proceed per amendment 4 on their
  assigned blocks after Population B passes; Gate 4 parallelism stands.
- The next apparatus failure of any kind stops the program pending an
  external round; this adjudication is flagged for review in the next
  external consultation regardless of outcome.
