# Canonical trace vocabulary

Contract version `1.0.0` uses typed dot paths. `<node>`, `<factor>`,
`<candidate>`, `<action>`, and `<channel>` are resolved IDs, not wildcards in a
stored trace. Analysis plans may use `*` in one placeholder position when an
aggregation consumes all matching scalar fields.

## Run and protocol

| Path | Type | Visibility |
|---|---|---|
| `run.seed` | integer | evaluator |
| `run.arm` | string | evaluator |
| `run.time` | integer | public |
| `run.episode` | integer | public |
| `run.row_index` | integer | public |
| `run.row_kind` | string: `event` or `tick` | public |
| `run.event_index` | integer | public |
| `run.event_kind` | string | public |
| `run.event_executed` | boolean | public |
| `run.genome_id` | string | evaluator |
| `run.event_id` | string | public |
| `run.stopped` | boolean | public |
| `run.stop_reason` | string | public |
| `action.selected` | string | public |
| `action.success` | boolean | public |
| `action.delivered_exposure` | number | public |

Every arm emits one `tick` row per protocol time reached through the stopping
time and one `event` row per expanded scheduled occurrence reached before the
run stops, including false-trigger and disabled-target occurrences.
`run.row_index` is the zero-based row ordinal in emission order. Event rows use
their zero-based expanded-schedule `run.event_index`,
`run.event_id = "<declared-id>#<repeat-index>"`, declared event kind, and an
execution flag. `run.event_index`, `run.event_id`, `run.event_kind`, and
`run.event_executed` are structurally absent on tick rows; no sentinel event is
created for a tick.

State, policy, action, learning, and world fields are defined on ordinary tick
rows. An empty-policy-support failure tick defines state and world fields but
not action, policy-selection, or outcome fields. Every ordinary tick has
`run.stopped = false` and `run.stop_reason = ""`; the empty-support failure tick
sets them to true and the architecture-failure reason.
Observation fields and observation provenance are defined only on executed
observation-event rows. An executed `stop_check` event row defines
`run.stopped` and `run.stop_reason` after evaluating the preceding tick: an
unsatisfied check uses `false` and `""`, while a satisfied check uses `true` and
`"stopping_rule:<rule-id>"`. The preceding tick is never retroactively
modified. Intervention/stop rows contain their applicable provenance. A field
expression returns only rows on which its field is defined; structural absence
on another row kind is not a missing cell. A predicate whose field is undefined
on a row is false.

## Observation and likelihood accounting

| Path | Type | Visibility |
|---|---|---|
| `observation.source` | string | public |
| `observation.scope_size` | integer | public |
| `observation.is_imaginal` | boolean | public |
| `observation.delivered_log_likelihood` | number | public |
| `observation.log_likelihood.<candidate>` | number | public |
| `observation.marginal_equivalence_error` | number | audit |

## Canonical state

| Path pattern | Type |
|---|---|
| `state.bundle.<node>.activation_probability` | number |
| `state.bundle.<node>.root_probability` | number |
| `state.bundle.<node>.expected_outcome` | number |
| `state.bundle.<node>.mandate_probability` | number |
| `state.context.<node>.posterior.<factor>.<value>` | number |
| `state.context.<node>.transition_entropy` | number |
| `state.cue.<node>.meaning_probability` | number |
| `state.cue.<node>.root_association` | number |
| `state.local_precision.<node>.mean` | number |
| `state.local_precision.<node>.calibration_error` | number |
| `state.global_precision.<node>.part` | number |
| `state.global_precision.<node>.context` | number |
| `state.global_precision.<node>.interoception` | number |
| `state.global_precision.<node>.relationship` | number |
| `state.global_precision.<node>.policy` | number |
| `state.global_precision.<node>.depth` | number |
| `state.protector.<node>.permission_probability` | number |
| `state.protector.<node>.suppression_probability` | number |
| `state.protector.<node>.forecast_outcome` | number |
| `state.protector.<node>.forecast_coprotection` | number |
| `state.protector.<node>.forecast_partner_type` | number |
| `state.partner.<node>.trust_probability` | number |
| `state.partner.<node>.regulation_probability` | number |
| `state.access.<node>.probability` | number |
| `state.episode.<node>.joint_probability` | number |
| `state.structure.<node>.log_evidence.<candidate>` | number |
| `state.structure.<node>.complexity.<candidate>` | number |
| `state.structure.<node>.selected.<candidate>` | boolean |
| `state.structure.<node>.first_stable_reduced_win` | integer |
| `state.structure.<node>.reversals_to_full` | integer |

## Joint policy

| Path pattern | Type |
|---|---|
| `policy.joint.posterior.<action>` | number |
| `policy.joint.expected_free_energy.<action>` | number |
| `policy.protector.<node>.permission_probability` | number |
| `policy.access_probability` | number |

`<action>` is the canonical joint label obtained by sorting protector IDs and
joining `protector_id=action` pairs with `;`.

`action.selected` is instead the one scalar environment action produced by the
`plurality-safety-priority-v1` reconciliation step in
`protocol-semantics.md`. World contingencies compare only that scalar field. A
joint posterior suffix must be either a declared scalar action in a no-protector
configuration or an exact canonical label from the configuration's cross-product
of each active protector and the actions declared by policy families containing
that protector. Every active protector must belong to at least one enabled
policy family.

## Learning and provenance

| Path pattern | Type |
|---|---|
| `learning.edge.<edge>.strength` | number |
| `learning.parameter.<factor>.value` | number |
| `provenance.update_function` | string |
| `provenance.edge_id` | string |
| `provenance.observation_event_id` | string |
| `provenance.model_candidate` | string |
| `provenance.rng_namespace` | string |

## Evaluator-only world truth

| Path pattern | Type |
|---|---|
| `world.truth.<factor>` | string |
| `world.process.<factor>.switch` | boolean |
| `world.potential_hazard` | boolean |
| `world.realized_hazard` | boolean |

World-truth paths cannot appear in any protocol trigger or agent input. They may
appear in analysis predicates and model-recovery estimands after the trace is
sealed.

## Trigger eligibility

- `external_proxy`: `run.time`, `action.selected`, `action.success`,
  `action.delivered_exposure`, `observation.source`,
  `observation.scope_size`, `observation.is_imaginal`, and
  `observation.delivered_log_likelihood`.
- `latent_intervention`: scalar or Boolean `state.*` and `policy.*` paths.
- forbidden for every trigger: `world.*`, `provenance.*`, `learning.*`,
  structure evidence, evaluator-derived fields, IDs, and free text.

## Derived evaluator fields

The generic evaluator may produce only these derived paths:

| Path | Type |
|---|---|
| `derived.first_crossing_time` | integer |
| `derived.non_crossing` | boolean |
| `derived.paired_difference` | number |
| `derived.slope` | number |
| `derived.classification_correct` | boolean |
| `derived.budget_relative_error` | number |

Every derived value must retain the expression AST and source-row hashes in the
evaluation record.
