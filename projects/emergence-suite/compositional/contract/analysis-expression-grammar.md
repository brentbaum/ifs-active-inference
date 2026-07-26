# Analysis expression grammar

Analysis expressions are TOML inline tables parsed as a closed, typed abstract
syntax tree. No source-language expression, interpolation, reflection, or custom
function is allowed.

## Leaf expressions

```toml
{ op = "literal", value = 0.10 }
{ op = "field", path = "state.access.access-main.probability" }
```

`field` resolves one canonical trace path. A `*` placeholder is permitted only
when the immediate parent is `mean`, `sum`, `min`, `max`, `count`, or `rate`.

## Row selection

```toml
{ op = "where", source = { op = "field", path = "..." },
  predicates = [
    { field = "run.arm", comparator = "eq", value = "treatment" },
    { field = "run.time", comparator = "ge", value = 20 }
  ] }
```

Comparators are `eq`, `ne`, `lt`, `le`, `gt`, `ge`, `in`, and `finite`.
Protocol arm IDs and evaluator-only world truth may be used in analysis
predicates. Agent inference never receives them.

`eq` and `ne` require one scalar value with the field's exact type. Numeric
ordering comparators require one finite numeric value and a numeric field. `in`
requires a nonempty array whose elements all have the field's exact type.
`finite` requires a numeric field and forbids `value`.

## Temporal operators

```toml
{ op = "initial", arg = { ... } }
{ op = "terminal", arg = { ... } }
{ op = "lag", arg = { ... }, steps = 1 }
{ op = "first_crossing", arg = { ... }, comparator = "ge",
  threshold = 0.70, persistence = 2 }
{ op = "slope", arg = { ... }, time_path = "run.time" }
```

## Aggregation operators

`mean`, `sum`, `min`, `max`, `std`, `count`, and `rate` each accept `arg`.
`std` is sample standard deviation with denominator `n-1` and is missing for
`n < 2`. Expression-level `rate` accepts Boolean series only. `quantile`
accepts `probability q` in `[0,1]` and uses the nearest-rank rule: sort `n`
values and select one-based rank `clamp(ceil(q*n), 1, n)`.

Aggregation order is:

1. evaluate leaf paths;
2. apply row predicates;
3. apply temporal operators within `(seed, arm, node)` groups;
4. apply pairwise or cross-arm algebra while preserving unit pairing;
5. apply the estimand's top-level aggregation across declared units;
6. construct the declared interval by resampling those units.

The declared `unit_of_analysis` fixes the within-arm resampling and aggregation
key:

- `seed`: `(run.seed, run.arm)`;
- `episode`: `(run.seed, run.arm, run.episode)`;
- `event`: `(run.seed, run.arm, run.event_index)`;
- `genome`: `(run.genome_id, run.arm)`.

`run.episode` follows the world episode boundary. `run.event_index` is the
zero-based index after schedule expansion and canonical ordering and exists
only on event rows. A plan with `unit_of_analysis = "event"` may therefore
depend only on event-row or all-row fields; any estimand dependency on a
tick-only field is a compile error. Before row predicates or grouping, event
unit evaluation implicitly restricts every all-row field source and predicate
(`run.time`, `run.arm`, and their peers) to rows with
`run.row_kind = "event"`, so a tick row can never enter an event unit without
an `event_index`.
`run.genome_id` is the SHA-256 of the canonical genome TOML. Every grouping key
is emitted even when the plan chooses another unit.

The canonical ASCII/UTF-8 grouping-key serializations are:

```text
seed=<unsigned-decimal>;arm=<arm-id>
seed=<unsigned-decimal>;arm=<arm-id>;episode=<unsigned-decimal>
seed=<unsigned-decimal>;arm=<arm-id>;event=<unsigned-decimal>
genome=<64-lowercase-hex>;arm=<arm-id>
```

They correspond to `seed`, `episode`, `event`, and `genome`. Decimal integers
have no leading zero except zero itself. IDs and hashes are already closed by
their schemas, so no escaping is permitted or needed.

Top-level aggregation is closed and typed:

- `identity` accepts exactly one scalar result and returns it unchanged;
- `mean` accepts a finite numeric unit series and uses the arithmetic mean;
- `median` accepts a finite sorted numeric unit series and returns the middle
  value for odd `n` or the arithmetic mean of the two middle values for even
  `n`;
- `rate` accepts a Boolean unit series and maps false/true to `0/1` before the
  arithmetic mean;
- `matrix` accepts the one count matrix produced by `confusion_matrix` and
  returns it unchanged.

An empty input follows `missing_cells`; non-finite input follows `non_finite`.

## Algebra

Binary operators `add`, `subtract`, `multiply`, `divide`, `min2`, and `max2`
accept `left` and `right`. Unary operators `abs`, `negate`, `log`, and `exp`
accept `arg`. Division by zero and non-finite results use the plan's explicit
`non_finite` rule.

## Paired and factorial operators

```toml
{ op = "arm_difference",
  value = { op = "terminal", arg = { op = "field", path = "..." } },
  treatment = "treatment", control = "control" }

{ op = "difference_in_differences", value = { ... },
  treatment_present = "regulation-evidence",
  treatment_absent = "evidence-only",
  control_present = "regulation-only",
  control_absent = "neither" }
```

`arm_difference` and `difference_in_differences` first require exactly one
inner value for every named arm at each otherwise-identical unit key. They then
remove the arm component and emit one indivisible paired value. Their output
keys and canonical serializations are:

- `seed`: `(run.seed)`, `seed=<unsigned-decimal>`;
- `episode`: `(run.seed, run.episode)`,
  `seed=<unsigned-decimal>;episode=<unsigned-decimal>`;
- `genome`: `(run.genome_id)`, `genome=<64-lowercase-hex>`.

Cross-arm operators are forbidden when `unit_of_analysis = "event"` because
arm schedules need not have aligned expanded event indices. A missing or
multiply-defined named-arm value applies `missing_cells` to the entire pair:
`fail` aborts evaluation, `drop_pair` removes the paired key from the estimand,
and `missing` retains one missing paired value. No component arm may be
resampled independently. Bootstrap sorts the paired keys by their exact UTF-8
serializations and resamples the resulting paired values as indivisible units.
The public analysis-math suite includes a paired-key/bootstrap vector.

`classification_accuracy` accepts `prediction_path`, `truth_path`, and optional
`strata_path`. `confusion_matrix` uses the same arguments and is descriptive
and must remain matrix-valued. Prediction and truth paths have the same scalar
type.

## Structural and ordering operators

- `argmax_match`: `evidence_path` (ending in `.*`) versus `selected_path`
  (ending in `.*`) for one declared `StructureNode`.
- `event_precedes`: first crossing of `left` occurs before first crossing of
  `right`; ties follow the plan's tie rule.
- `budget_relative_error`: relative error for one declared
  `evidence_budget_rule_id`.
- `survival_fraction`: fraction for which numeric or Boolean `arg` satisfies
  `comparator` and `threshold` across seeds or genome perturbations.

## Closed operator signatures

Unknown or extra keys are errors. `E` means a nested expression.

| Operator | Required keys besides `op` | Result |
|---|---|---|
| `literal` | `value` scalar | scalar |
| `field` | `path` | trace series |
| `where` | `source=E`, `predicates` | trace series |
| `initial`, `terminal` | `arg=E` | unit series |
| `lag` | `arg=E`, `steps` | trace series |
| `first_crossing` | `arg=E`, `comparator`, `threshold`, `persistence` | unit series |
| `slope` | `arg=E`, `time_path` | unit series |
| `mean`, `sum`, `min`, `max`, `std`, `count`, `rate` | `arg=E` | scalar |
| `quantile` | `arg=E`, `probability` | scalar |
| `add`, `subtract`, `multiply`, `divide`, `min2`, `max2` | `left=E`, `right=E` | numeric |
| `abs`, `negate`, `log`, `exp` | `arg=E` | numeric |
| `arm_difference` | `value=E`, `treatment`, `control` | unit series |
| `difference_in_differences` | `value=E`, four named arm keys | unit series |
| `classification_accuracy`, `confusion_matrix` | `prediction_path`, `truth_path`; optional `strata_path` | scalar or matrix |
| `argmax_match` | `evidence_path`, `selected_path` | unit Boolean series |
| `event_precedes` | `left=E`, `right=E` | unit Boolean series |
| `budget_relative_error` | `evidence_budget_rule_id` | unit series |
| `survival_fraction` | `arg=E`, `comparator`, `threshold` | scalar |

`arm` and `paired_slope` are not contract `1.0.0` operators. All temporal
operators group by `(seed, arm)` plus a node placeholder when present. An
explicit wildcard is valid only when the direct parent is an aggregation or
`argmax_match`.

Both operands of `event_precedes` must be direct `first_crossing` expressions.
For `argmax_match`, the paths are exactly
`state.structure.<same-node>.log_evidence.*` and
`state.structure.<same-node>.selected.*`; candidates must belong to that node.
`event_precedes` is Boolean: a crossing-time tie follows `fail`, `pass`, or
`missing`; an analysis containing this operator is invalid when global
`tie_handling = "half"`.

## Intervals and deterministic resampling

`none` reports no interval and has no `level`. `exact_binomial` is allowed only
for a Boolean unit series aggregated as `rate`; it is the two-sided
Clopper-Pearson interval with tail probability `(1-level)/2`. Beta quantiles
use the public inverse regularized incomplete-beta implementation in
`scripts/contract/analysis_math.jl` and are checked against high-precision
conformance vectors.

Bootstrap methods resample the plan's declared units, never trace rows. They are
allowed only for top-level `mean`, `median`, and `rate`. Units are sorted by the
UTF-8 byte ordering of the exact grouping-key serialization above. For
zero-based replicate `r` and sample position `p`, select index `floor(n*u)`,
where `n` is unit count and `u` is obtained from the first eight big-endian
digest bytes of:

```text
SHA256(
  "ifs-ai-51-bootstrap-v1" || NUL ||
  utf8(contract_id) || NUL ||
  utf8(contract_version) || NUL ||
  utf8(analysis_id) || NUL ||
  utf8(estimand_id) || NUL ||
  uint64be(r) || NUL ||
  uint64be(p)
)
```

If those bytes represent unsigned integer `x`, implementations calculate the
index exactly as `floor(n*(2*x+1)/2^65)`; floating-point rounding is forbidden.

Let `R = resamples`. The percentile interval sorts the `R` replicate estimates
and uses ranks `clamp(ceil(q*R), 1, R)`. The basic interval reflects those
endpoints around the observed estimate: if percentile endpoints are `(lo, hi)`
and the observed value is `v`, the basic endpoints are
`(2v-hi, 2v-lo)`. Replicates are evaluated in increasing `r`; no world or
escrow seed is consumed.

## Decision rules

Decision rules compare one estimand ID to a threshold:

```toml
[[decision_rules]]
id = "primary-pass"
estimand_id = "access-effect"
comparator = "ge"
threshold = 0.10
interval_requirement = "lower_above_threshold"
```

Comparators are `gt`, `ge`, `lt`, `le`, `between`, and `equivalent`.
`interval_requirement` is `none`, `lower_above_zero`,
`upper_below_zero`, `lower_above_threshold`, `upper_below_threshold`, or
`inside_equivalence`.

`gt/ge` require a scalar threshold and permit only `none`,
`lower_above_zero`, or `lower_above_threshold`. `lt/le` require a scalar and
permit the corresponding upper requirements. `between` requires an ordered
two-scalar interval and `none`. `equivalent` requires an ordered interval and
`inside_equivalence`. Matrix estimands cannot have decision rules.

Decision success is the logical AND of the point comparator and interval
requirement. Exact point formulas are:

```text
gt: v > t                 ge: v >= t
lt: v < t                 le: v <= t
between: lo <= v <= hi    equivalent: lo <= v <= hi
```

`between` and `equivalent` therefore use closed point endpoints. Interval
requirements use strict inequalities:

```text
lower_above_zero:      interval.lower > 0
upper_below_zero:      interval.upper < 0
lower_above_threshold: interval.lower > t
upper_below_threshold: interval.upper < t
inside_equivalence:    interval.lower > lo && interval.upper < hi
none:                  true
```

An equality at an interval boundary fails the interval requirement.

Every contrast control named by an estimand must have exactly the same treatment
and control arm sets as that contrast. Each contrast declares both
`matched_capacity` and `matched_budget` controls, or one `impossibility`
control explaining why that pair cannot be constructed.

## Rejection rules

The validator rejects unknown operators/keys, type-incompatible nesting,
unbounded recursion deeper than 32 nodes, unknown trace paths, analysis
plug-ins, code strings, and missing policies for ties, missing cells,
non-crossings, and non-finite values.
