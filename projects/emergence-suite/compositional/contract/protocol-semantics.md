# Protocol execution semantics

Contract version `1.0.1` compiles every arm into a deterministic event schedule.
The executable protocol domain is the half-open interval
`0 <= time < world.horizon`; every declared and expanded occurrence must lie in
that domain.

## Schedule expansion and ordering

An event with `repeat = n` and `interval = q` expands to occurrences at
`time + k*q` for zero-based `k < n`. Its expanded ID is
`<declared-id>#<k>`. The original arm-array position is its declaration
ordinal. The engine sorts simultaneous work by:

1. phase number below;
2. declaration ordinal;
3. repeat index.

At each protocol time `t`, the phases are:

1. evaluate event triggers against the trigger context defined below and apply
   enabled `intervene` events in schedule order, emitting one event row after
   each occurrence;
2. update due world processes, using the action committed at `t-1`;
3. generate enabled `observe`, `probe`, and `imaginal` occurrences in schedule
   order, applying the inference update and emitting an event row after each
   occurrence;
4. apply persistent learning after each `observe` only;
5. infer the joint policy; if its support is nonempty, reconcile it with
   `plurality-safety-priority-v1` to one scalar environment action, and commit
   that action;
6. generate declared action and hazard outcomes;
7. emit the single tick row with the final state/action/world snapshot;
8. evaluate only the stopping rules named by enabled `stop_check` events, in
   schedule order, emitting each event row after evaluation and stopping on the
   first satisfied rule.

The trigger context sets `run.time` to the occurrence's scheduled time,
`action.*`, `state.*`, and `policy.*` from the preceding tick row, and
`observation.*` from the greatest-`row_index` executed observation row at a
strictly earlier time. If no such prior row or field exists, that predicate is
false. Same-time observations never affect another same-time trigger. At
`t = 0`, no preceding action or observation exists; latent triggers read the
initialized state. An action-contingent process uses its baseline transition.
A trigger is reevaluated independently for every expanded occurrence reached
before the run stops. Every reached occurrence gets an event row. A false
trigger or disabled target sets
`run.event_executed = false`, defines no observation value, and does not shift
any RNG stream.

Within a time, rows are emitted in phase and schedule order; the tick row comes
after all observation rows and before stop-check rows. `run.row_index` makes
that order explicit. Protocol temporal operators first reduce their source to
at most one defined value per time, retaining the greatest `row_index` when
several source values share a time. `initial`/`terminal` select the first/last
reduced time, `lag` counts reduced rows, a persistent crossing requires
successive integer times, and `slope` is ordinary least squares over the
reduced `(run.time, value)` pairs.

## Observation kinds

`observe` draws from its declared world emission, updates current inference,
and runs the normal persistent-learning update.

`probe` uses exactly the same world emission and inference update as `observe`
but disables every persistent parameter, association, edge-strength, and
structure-evidence write for that occurrence. State beliefs may change;
learned parameters may not.

`imaginal` has no world emission reference. Its channel must have
`source = "imaginal"` and its generator is
`posterior-predictive-mode-v1`. The engine constructs the channel's posterior
predictive distribution exclusively from the agent's committed beliefs and
learned likelihood parameters, never evaluator truth. It emits the
lexicographically first maximum-probability label for a discrete channel or the
posterior-predictive mean for a Gaussian channel. The occurrence updates
current inference but performs no persistent learning and consumes no world
RNG draw.

## Joint-action reconciliation

Configuration declares the exact
`action_reconciler_id = "plurality-safety-priority-v1"`. The engine selects the
maximum-posterior canonical joint label; equal posterior masses are broken by
UTF-8 byte order of the complete label. If there are no protectors, the
single Bundle actor's selected symbol is `action.selected`.

With protectors, count the action symbols in the selected joint label and
choose the plurality action. A count tie uses this first-match priority:

```text
withdraw, suppress, wait, observe, inspect, request_support,
offer_support, permit, approach
```

The result is the sole scalar `action.selected` used by world contingencies.
If phase-1 interventions leave any active actor with no action, phase 2 world
updates and phase 3/4 observations and learning for the current time have
already occurred when phase 5 detects that no joint label exists. The engine
then emits the current time's failure tick row immediately, with the current
state and world snapshot, `run.stopped = true`, and
`run.stop_reason = "architecture_failure:empty-policy-support"`. Action,
policy-selection, and outcome fields are structurally absent on that row.
Phases 6 and 8 do not run, and no later tick or scheduled-event rows are
emitted. The engine never reuses a preceding action or invents a fallback.

## Interventions and stopping

Intervention state changes persist until a later intervention changes the same
target. `toggle` negates the current Boolean state. `sever` is persistent
disable and differs from `disable` only in provenance labeling.

For an edge, `enable` means active message passing and `disable/toggle-off`
means inactive; enabling a learnable edge does not erase its learned strength.
For a channel, the Boolean gates delivery. For a policy action, the Boolean
gates that symbol in every enabled policy family that declares it, and every
joint label containing a disabled symbol is unavailable. For a world
contingency, the Boolean gates the action-transition rule in
`world-semantics.md`.

A fixed-horizon or crossing rule is not monitored continuously. It is evaluated
only when a named `stop_check` occurrence runs, using the tick row committed in
phase 7. A fixed-horizon rule is satisfied when `run.time >= max_time`. A
crossing rule reduces its source to one value per time as above and is satisfied
when its numeric predicate holds for `persistence` successive integer times
ending at the current tick, or when `run.time >= max_time`. Fewer than
`persistence` tick values cannot satisfy the crossing. `max_time` is checked
only at a named occurrence; it is not an implicit event.
