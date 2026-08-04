# T-CAP1 Stages 0–1 design freeze

T-CAP1 is a focused variant organism. Frozen v3.6 scientific modules are not
modified. It contains one binary bundle and five typed evidence channels:
threat cue, body state, partner face, present context, and safety evidence.

Exactly two productions are added. First, the current bundle posterior selects
the next cycle's allocation policy. Second, a noisy metacognitive observation
reports that allocation. The update order is strictly
`q_t -> A_{t+1} -> Lambda_{t+1} -> O_{t+1} -> q_{t+1}`. No likelihood can read
the posterior produced by its own slice.

The transparent and represented architectures replay one serialized generated
stream. Transparent scoring assumes baseline allocation. Represented scoring
marginalizes the allocation state using its metacognitive observation. This is
the ruling-3 limitation resolution; reliability is swept at `.60`, `.80`, and
`.95`. Representation adds no context token, posterior clamp, recovery policy,
transition change, or calmer first-order likelihood.

All seven required controls are explicit arms alongside the primary transparent
feedback arm: candidate-common no-feedback, represented feedback, random
allocation, sign-reversed allocation, matched persistence, full-information
replay, and filter-awareness only.

The public census uses `3824000:3831999` once over the frozen 324-cell Cartesian
grid recorded in the JSON companion. It is descriptive and non-criterial. The
panel selects the first lexicographic cell in each occupied region: no
hysteresis (`H<.02`), near boundary (`.02<=H<.08`), and clear hysteresis
(`H>=.08`). Empty regions are reported rather than manufactured.
