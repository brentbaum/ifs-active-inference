# Experiment 50 machinery audit

Every canonical state-change transition is organization-only. No independently parameterized carrier is present in the strain.

| Equation | Inputs | Classification | Canonical reference | Note |
|---|---|---|---|---|
| `bernoulli_update` | prior, observation, reliability | **organization** | `src/model_organism/Equations.jl:bernoulli_update` | Bayesian belief update; no carrier input |
| `update_posterior!` | posterior, evidence, genome | **organization** | `src/model_organism/Equations.jl:update_posterior!` | all psychologically meaningful belief changes |
| `update_policy_belief!` | history cost and success | **organization** | `src/model_organism/Equations.jl:update_policy_belief!` | learned repertoire, never authored mature cost |
| `protector_permission` | three forecasts, stakes, learned risk | **organization** | `src/model_organism/Equations.jl:protector_permission` | stakes enters permission only |
| `freeze_write!` | overwhelm, control | **organization** | `src/model_organism/Equations.jl:freeze_write!` | authored conformance write |
| `update_root!` | root posterior, evidence breadth | **organization** | `src/model_organism/Equations.jl:update_root!` | root moves only through inference |
| `update_registration!` | suppression and registration bit | **organization** | `src/model_organism/Equations.jl:update_registration!` | closed registration is an idle no-update path |
| `update_precision_field!` | five endogenous forecast errors | **organization** | `src/model_organism/Equations.jl:update_precision_field!` | channel field and recursive broadcast |
| `context_model_scores` | then/now observation sequence | **organization** | `src/model_organism/Equations.jl:context_model_scores` | three historical plus drift/change-point explanations |
| `update_dyad!` | joint partner signal and settling | **organization** | `src/model_organism/Equations.jl:update_dyad!` | canonical Sim-5-form mapping/depth/precision path |
| `generate_history` | seed and latent world labels | **neither** | `src/model_organism/Equations.jl:generate_history` | world generator; not a change transition |
| `partner_probability` | latent disposition | **neither** | `src/model_organism/Assays.jl:partner_probability` | world emission distribution; not agent state |
