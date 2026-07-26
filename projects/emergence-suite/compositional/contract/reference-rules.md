# Reference and identifier rules

These rules are normative for contract version `1.0.1`.

## Identifiers

All IDs match:

```text
^[a-z][a-z0-9]*(?:[-_][a-z0-9]+)*$
```

IDs are ASCII, case-sensitive, and unique within their declared namespace.
Challenge-directory IDs are the exception and match `^51-P-[0-9]{2}$`.

## Namespaces

Configuration namespaces:

- `nodes`
- `edges`
- `observation_channels`
- `policy_families`
- `structure_candidates`

World namespaces:

- `latent_factors`
- `distributions`
- `processes`
- `emissions`
- `contingencies`

Protocol namespaces:

- `arms`
- `events` within each arm
- `interventions`
- `paired_streams`
- `stopping_rules`
- `evidence_budget_rules`

Analysis namespaces:

- `estimands`
- `decision_rules`

An ID may equal an ID in another namespace. Every reference is resolved against
the namespace stated by its field.

## Cross-file references

- A world emission's `channel_id` references a configuration observation
  channel.
- A protocol event's `channel_id` references a configuration observation
  channel.
- A protocol event's `intervention_id` references a protocol intervention.
- A protocol intervention target references a configuration edge, observation
  channel, policy action, or world contingency according to `target_kind`.
- A protocol arm's `world_id` equals the loaded world's `world_id`.
- An outcome's source factors reference world factors; action and mitigating
  action references resolve against the configuration policy action set.
- A paired stream references two or more protocol arm IDs.
- An analysis arm selector references a protocol arm ID.
- Requested trace paths must match the public trace vocabulary.
- Node, world-factor/value, candidate, and action placeholders in trace paths
  must resolve to declarations of the required type.

Dangling, duplicate, or type-incompatible references are build failures.

## Node references

Edges reference nodes by exact ID. Observation channel scopes are non-empty sets
of node IDs. A policy family's `actor_nodes` contains only `ProtectorNode` IDs
or, when no protector exists, one `BundleNode` ID. In the latter case every
enabled policy family shares the same Bundle actor.

Inactive nodes may be referenced only by inactive edges or audit-only requested
trace paths. Candidate declarations for inactive `StructureNode`s are
forbidden; only active structure nodes have candidate arrays. Learnable edges
are initially absent from message passing and enter only through the generic
structural-learning schedule.

A structure candidate is a complete edge-state pattern. An edge named in
`active_edges` is active, one named in `inactive_edges` is inactive, and every
omitted edge inherits its configuration `state`. Candidate lists for one
active `StructureNode` have exactly that node's cardinality, and no two
candidates for the node may resolve to the same complete pattern. Candidate
array order is the only tie breaker. The `family` value is an interpretation
label, not an
additional equation; dynamic drift and change points belong to typed world
processes rather than structure-family labels.

Every edge satisfies the source/target type signature in `CONTRACT.md`.
Duplicate `(type, from, to)` triples are forbidden.

## Ordering

Array order is not scientific semantics except for:

- protocol event order when two events share a time;
- factor value order within an explicitly declared categorical distribution;
- protector-ID byte order when serializing a joint policy label;
- latent-factor `values` and observation-channel `value_labels`;
- parent order in coupled processes and emissions;
- structure-candidate order only as a deterministic tie breaker;
- stopping-rule order, with the first satisfied rule winning.

The compiler must otherwise canonicalize by ID. Reordering independent nodes or
edges must not change the mathematical result.

## Controls and evidence budgets

A control's treatment and control arm sets are disjoint. Every named
intervention occurs in at least one of those arms and cannot occur identically
on both sides. A matched-capacity control names at least one such intervention.
A matched-budget control names a budget rule whose arm set is exactly the union
of its two sides. The rule declares exact ordered `arm_pairs`; every pair's
`left` is a treatment arm and `right` a control arm, reverse duplicates are
forbidden, and every declared arm appears in at least one pair. No implicit
all-pairs or positional matching is performed.

For `delivered_log_likelihood_abs`, an observation occurrence is included when
its channel scope intersects the budget rule's active-node `scope`; its full
absolute delivered log likelihood is counted exactly once. For each seed and
arm, sum included executed observation-event rows. For each exact `(left,right)`
pair the relative error is `abs(left-right) / max(left,right,10^-12)`.
`budget_relative_error` yields one numeric value per `(seed, arm_pair)`. A
budget passes only when every value is at most `tolerance_fraction`; a decision
rule for that gate therefore applies `max` before comparing the tolerance.

## Challenge opacity

Private challenge directory IDs are opaque sequence numbers. Scientific labels
may appear only inside the sealed `interpretation-lock.md`, not in IDs consumed
by the engine.
