# Typed world and emission semantics

Contract version `1.0.1` uses closed, dimension-checked world objects.

## Latent factors

Each latent factor declares ordered `values`, with length equal to
`cardinality`. Truth is evaluator-only. A factor's initial distribution is a
`categorical` distribution with exactly the same values in the same order.

## Time, episodes, and distribution lifetime

The world declares `episode_length`. Both `development_horizon` and `horizon`
must be integer multiples of it. The canonical RNG tick is zero-based over the
concatenated developmental and protocol timelines:

- developmental replay step `d` uses tick `d`, for
  `0 <= d < development_horizon`;
- protocol time is exactly `0 <= t < horizon` and uses tick
  `development_horizon + t`;
- the episode index is `floor(tick / episode_length)`.

Thus `horizon` is a maximum tick-row count, not an executable time value. A run
that does not stop early has exactly `horizon` committed protocol tick rows; an
early-stopped run has one row for every reached time through its stopping row.
`horizon_plus_one` non-crossing is reported as the integer `horizon`, one past
the final possible time. Schedule events, expanded repeats, stopping maxima,
and sampled change times must all be less than `horizon`.

`categorical` and `transition_matrix` objects are immutable probability tables.
They do not declare `sampling_scope`. Their consumers draw at factor
initialization, process update, or emission time using the consumer's RNG
component.

`fixed`, `uniform`, `integer_uniform`, and `beta` are scalar parameter
distributions and declare `sampling_scope`:

- `world`: one draw for the distribution ID at RNG tick `0`, shared by every
  consumer in the world;
- `episode`: one draw at the episode's first tick, shared by every consumer of
  that distribution during that episode;
- `event`: one draw for each consumer occurrence at its canonical RNG tick.

For an event-scoped scalar distribution, draw index is the zero-based ordinal
of the consumer occurrence after sorting simultaneous consumers by
`(consumer-kind, consumer-id, expanded-event-id)`. World- and episode-scoped
scalar draws use index `0`. A fixed distribution consumes no entropy but obeys
the same refresh lifetime. Any scalar distribution used where its declared
lifetime cannot be identified is a compile error.

| Family | Required fields | Rules |
|---|---|---|
| `fixed` | `value` | finite scalar |
| `uniform` | `lower`, `upper` | finite and `lower <= upper` |
| `integer_uniform` | `lower`, `upper` | integers and `lower <= upper` |
| `beta` | `alpha`, `beta` | both positive |
| `categorical` | `values`, `probabilities` | immutable table; same length `2...5`; unique values; probabilities sum to one |
| `transition_matrix` | `values`, `matrix` | immutable table; `N` unique values and an `N×N` row-stochastic matrix |

Matrix row `i` is the distribution of the next value given previous value `i`.
No silent normalization is allowed.

## Processes

Exactly one process may target a latent factor. Initialization occurs at
canonical RNG tick `0`. Thereafter a process updates at every canonical tick
greater than zero that is divisible by `update_interval`. Simultaneous
processes execute by process-ID byte order; because targets are unique, their
new values are computed from the same prior-tick snapshot and committed
together.

- `iid`: `distribution_id` is categorical and matches the target values.
- `markov` and `drift`: `transition_distribution_id` is a transition matrix
  matching the target values. `drift` is a candidate-family label; it does not
  change the transition equation.
- `change_point`: `before_transition_id` and `after_transition_id` both match
  the target; `change_time_distribution_id` is fixed or integer-uniform within
  the horizon and has `world` scope. Change time is protocol time: development
  always uses the before matrix, and main-protocol updates at or after the
  sampled time use the after matrix.
- `action_contingent`: `baseline_transition_id` and
  `action_transition_id` both match the target. The action matrix is used
  exactly when an enabled contingency targets this process and the scalar
  executed action in `action.selected` at the preceding policy step equals
  both the process and contingency `action`; otherwise the baseline matrix is
  used. `action.selected` is the reconciled environment action, not the
  semicolon-delimited joint-policy label.
- `coupled_latent`: ordered `source_factors` defines lexicographic parent
  configurations using each factor's declared value order.
  `conditional_transition_ids` has exactly the product of source cardinalities
  entries. Each referenced transition matrix matches the target. The last
  source factor varies fastest.

## Emissions

An event references exactly one emission ID, which references exactly one
configuration channel. Source-factor combinations use the same lexicographic
rule as coupled processes.

For `categorical`, `bernoulli`, and `ordinal` emissions:

- channel `value_labels` defines the observation support;
- `conditional_distribution_ids` has one categorical distribution per source
  configuration;
- each categorical distribution's values exactly equal the channel labels;
- `reliability_distribution_id` is beta and yields `r`;
- emitted probabilities are `r * p_base + (1-r) * uniform`.

For `gaussian_bounded` emissions:

- channel `bounds = [lower, upper]`;
- `mean_by_configuration` has one finite mean per source configuration, each
  inside the bounds;
- `noise_scale_distribution_id` is fixed or uniform and yields positive `σ`;
- `reliability_distribution_id` is beta and yields `r`;
- effective scale is `σ / max(r, 10^-6)`;
- the likelihood is a Gaussian density truncated to the declared bounds and
  normalized by its exact truncated mass.

`masked_scope` must be a subset of `source_factors`. It removes those factors
from the agent-visible observation scope but not from world generation.
Likelihood scoring marginalizes masked factors; it may not substitute truth.

## Contingencies

A contingency has the sole effect
`effect = "activate_action_transition"` and may target only an
`action_contingent` process with the same `action`. Its `enabled` value is the
initial state. A protocol `enable`, `disable`, or `toggle` intervention changes
that state at the intervention phase and the state persists until another
intervention changes it.

At process-update time, an enabled contingency activates the target process's
`action_transition_id` only when the preceding committed
`action.selected` equals the named action. At time zero, and whenever no
preceding action exists, the baseline transition is used. Multiple
contingencies may not target the same process; validation rejects such a world.

## Action and hazard outcomes

World `outcomes` are the only source of `action.success`,
`action.delivered_exposure`, `world.potential_hazard`, and
`world.realized_hazard`.

An `action_outcome` maps one declared scalar action and an ordered list of zero
or more source factors to parallel `success_probabilities` and
`exposure_values`. Tables have exactly the product of source cardinalities
entries using declared factor/value order with the last source factor varying
fastest (one entry when sources are empty). At phase 6, let `p` be the indexed
success probability and `u` the outcome RNG uniform:
`action.success = (u < p)`. Delivered exposure is the indexed nonnegative value
when success is true and exactly zero otherwise. A trace or trigger requesting
either action-outcome field is valid only when every selectable action has
exactly one mapping.

At most one `hazard_outcome` may exist. Its indexed
`potential_probabilities` uses the same indexing. With indexed `p_h` and its
own outcome RNG uniform `u_h`,
`potential_hazard = (u_h < p_h)`. Realized hazard is:

```text
potential_hazard &&
!(action.success && action.selected in mitigating_actions)
```

Hazard trace fields require that mapping. Outcomes are evaluator-generated and
never agent inputs except through an explicitly scheduled observation emission.

`world.process.<factor>.switch` is defined only when that factor is targeted by
a `change_point` process. It is false before the sampled protocol change time
and true at and after it. Other process forms cannot expose a switch path.

## Parameter visibility

Distribution draws and truth values are inaccessible to the agent and protocol.
Only emitted observations and declared reliability metadata enter the common
observation interface.
