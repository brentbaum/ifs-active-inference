# Experiment 51 reference genome rationale

The reference genome contains only strain-wide numerical choices. None is
selected by a protocol ID.

| Parameter | Rationale | Used by |
|---|---|---|
| `learning_rate` | Conservative online likelihood/state update | every delivered observation and persistent learning update |
| `message_gain` | Bounded strength for one typed graph message | every active semantic edge |
| `policy_temperature` | Common softmax scale for the joint policy posterior | every policy family |
| `structure_complexity_penalty` | Shared evidence penalty per active candidate edge | every structure candidate |
| `precision_floor` | Prevents zero precision and undefined likelihood scaling | local/global precision and observation updates |
| `dirichlet_concentration` | Symmetric neutral initialization | every learnable categorical table |
| `approximation_iterations` | Fixed point budget of 32, sufficient for the declared `1e-10` loopy parity gate and independent of topology names | every approximate inference pass |
| `approximation_tolerance` | Common convergence criterion | every approximate inference pass |
| `action_costs.*` | Public action-symbol costs in the single policy objective | every policy family that exposes the symbol |

The genome deliberately has no format bonus, polarization coefficient,
transfer weight, readiness threshold, regime label, or protocol-specific
constant.
