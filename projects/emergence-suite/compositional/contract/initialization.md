# Initialization and developmental replay

Contract version `1.0.0` has one initializer and one history generator.

`initializer_id = "neutral-replay-v1"` initializes every active categorical
state uniformly, every active Bernoulli state at `0.5`, every policy at equal
mass, and every learnable categorical/transition parameter at the symmetric
Dirichlet concentration named by the frozen genome. Inactive slots are
bit-for-bit absent from inference and tracing. No posterior value is accepted
from configuration or world files.

`history_generator_id = "world-replay-v1"` generates
`development_horizon` pre-protocol steps using the same world processes,
emissions, likelihoods, RNG convention, and canonical update schedule used
during the protocol. Only the world's declared `development_emission_ids` are
delivered once per developmental tick. Events are replayed in canonical tick
order, then emission-ID byte order. Development occupies canonical RNG ticks
`0...(development_horizon-1)` and maps to reported negative times
`-development_horizon...-1`.
Protocol actions and interventions do not run at negative time.

Those reported negative times exist only in the initialization audit ledger,
which records tick, reported time, emission ID, draw namespace, and update
provenance. Developmental rows are not protocol `tick` or `event` rows, are
excluded from the sealed analysis trace and its cell bound, and cannot be read
by the analysis-expression grammar. Consequently `initial`, `terminal`, and
predicates over `run.time` see only the nonnegative protocol domain. The
initialization audit ledger is provenance, not an additional analysis input.

Configuration and world must declare these exact IDs. A world with
`development_horizon = 0` declares an empty `development_emission_ids` list.
