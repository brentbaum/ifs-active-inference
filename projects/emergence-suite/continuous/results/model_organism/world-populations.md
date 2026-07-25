# Frozen world and history populations

Status: **frozen definition of every rate population**.

All numeric distribution parameters below are genome entries, not assay overrides. Exact algorithms are canonical in `src/model_organism/Equations.jl` and `Assays.jl`.

| Assay | Frozen population |
|---:|---|
| 1 | Complete 5×5 overwhelm/control property grid around the genome boundaries; stochastic seed is irrelevant to the write predicate. |
| 2 | Bernoulli corrective streams of length `episodes`, reliability `bayes_reliability`, paired across closed/open loops and three controllability doses. |
| 3 | Balanced four-cell dominance × depth population with Gaussian coordinate noise `regime_observation_sd` and equal evidence budgets. |
| 4 | Bernoulli root/cue evidence streams paired across witnessing, matched exposure, and reversed graph. |
| 5 | Complete regulation × root-evidence 2×2, with one matched evidence stream and matched field-error world per seed. |
| 6 | Equal allocation to global-downweight, cue-local, context-split, continuous-drift, and change-point generators, each with matched `generator_noise_sd`. |
| 7 | Complete analytic posterior grid plus paired limited-budget Bernoulli imaginal/suggestion outcomes at premature and post-revision states. |
| 8 | Cycled favorable-policy labels; noisy direct costs and Bernoulli successes are replayed into learned beliefs. Registration arms share policy and suppression histories. |
| 9 | Equal trustworthy, neutral, and adverse latent-partner histories. Each disposition emits noisy outcome, competence, and tolerance events from its genome probability. |
| 10 | Complete trustworthy/neutral/adverse × coupled/decoupled factorial plus positive-evidence-without-scaffolding. One latent disposition stream generates both regulation and trust outcomes and is replayed across scaffold arms. |

One seed is one paired world. Stochastic rate confirmations are planned at `rate_worlds = 80` worlds (or 80 per generator/partner stratum where the analysis plan says so), within the public spec's 60–100 range. Analytic properties use `property_grid_points = 101` or the complete finite grid. Stage A uses only `pilot_worlds = 12`.

Developmental histories contain `training_events` joint events. Every history begins from the neutral initializer and is replayed through `replay_history!`; the per-assay generated event logs are frozen pilot evidence, not directly authored states.
