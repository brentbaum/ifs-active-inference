# V3.2 Stage-0 attainability diagnosis

Status: **STOP — no criterion block opened**.

The prospective pilot used all 2,000 assigned seeds (`3200000:3201999`) and
serialized each trace before aggregation. Those seeds are now barred. Gate 2
through Gate 5 and evaluator escrow `4020000:4023999` remain untouched.

## Blocking finding

The required witnessing contrast is not attainable under the implemented
draft. Across 200 same-seed pilot pairs, sustained witnessing evidence minus a
single-regime comparator changed posterior context-specific-scope probability
by a mean of `-1.4481277843536589e-11`. This is numerical zero, not a positive
effect from which a defensible SESOI can be frozen. The runner’s mechanical
default of `0.01` is therefore rejected and left unfrozen.

## Apparatus-first localization

The single-regime comparator observes only context slot 0, but the current
context-specific likelihood already assigns that slot a distinct emission/root
probability (`0.18`) while the shared production assigns `0.50`. Consequently,
even without a then/now contrast, the comparator strongly identifies
context-specific scope. Sustained evidence in slot 1 adds observations but does
not create the missing comparison; posterior scope mass is already saturated.

This is a construct-design defect, not a sampling-power defect:

- recovery itself is strong (macro region recovery `0.9565`);
- scope accuracy is `1.0`;
- recurrent worlds have mean context-specific-scope posterior
  `0.9999997442`;
- the paired contrast remains zero despite 200 worlds and 48 slices.

The grammar can represent context-specific scope, recurrence, drift, one-way
change, and mixed temporal parents. What is missing is a prospectively declared
neutral pre-witness likelihood in which one observed context alone does not
already identify context-specific scope. Changing that likelihood after seeing
this pilot would tune the mechanism on its attainability block, violating the
stage discipline.

## Required next decision

A new prospective repair cycle must specify the pre-witness observational
equivalence before allocating a fresh pilot block. Legitimate options would be
generic likelihood parameterization or a scope prior/parameter family that
makes the unobserved context contrast unidentified. No schedule-aware branch,
split operation, or authored conclusion is warranted.

No Gate-1 verdict is claimed from the pre-pilot development smoke check.

