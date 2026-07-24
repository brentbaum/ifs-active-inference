# Magic numbers — Experiment 44

All authored numeric constants in `ContextSplitConfig` are listed below.
Algorithmic tolerances are identified separately.

| Constant | Value | Rationale |
|---|---:|---|
| `training_observations` | `64` | Enough repeated cue/context encounters to estimate all ten coordinates. |
| `heldout_observations` | `32` | Half the training budget; never used for fitting or freeze tuning. |
| `parameter_count` | `10` | Capacity is fixed equally across all three model classes. |
| `prior_variance` | `1.5` | Identical zero-mean Gaussian parameter prior in every class. |
| `observation_sd` | `0.52` | Keeps behavior informative without making context perfectly separable. |
| `context_marker_sd` | `0.42` | Makes context latent but inferable rather than observed as a label. |
| `context_effect` | `1.35` | World-level separation between past-valid and present-valid behavior. |
| `transition_stay_probability` | `0.88` | Produces persistent contexts while retaining learnable transitions. |
| `root_sessions` | `18` | Common external evidence budget for every revision arm. |
| `root_prior_positive` | `0.06` | Represents the initially frozen negative identity inference. |
| `root_observation_sd` | `0.72` | Shared bundle observation noise for all revision arms. |
| `contact_sd` | `0.6` | Experiment-43-style interpersonal observation remains informative but noisy. |
| `revision_begun_probability` | `0.62` | Timing marker fixed before the do-over comparison. |
| `revision_probability` | `0.8` | Common posterior crossing used for time-to-revision. |
| `reduction_log_bayes_threshold` | `0.35` | Positive evidence threshold for selecting the reduced burden model. |
| `doover_packets` | `4` | Fixed internally generated counterfactual ending budget. |
| `imaginal_weight` | `0.72` | Flags imaginal packets as less precise than external observations. |
| `beta_prior` | `1.0` | Uniform catastrophe-rate prior in full and reduced models. |
| `pilot_seeds` | `174401:174410` | Ten-world pilot namespace. |
| `confirm_seeds` | `174601:174620` | Fresh, disjoint twenty-world namespace after the held-out scale audit. |
| `contexts` | `-1, +1` | The two latent states `then` and `now`. |
| `context_emission_means` | `-1.0, +1.0` | Noisy marker likelihood; labels are never observed. |
| `context_initial_probability` | `0.5` | Symmetric state prior. |
| `context_fit_initial_stay` | `0.75` | Neutral persistent initialization, replaced by inference. |
| `context_em_iterations` | `12` | Fixed deterministic coordinate-ascent budget. |
| `transition_newton_steps` | `8` | Fixed deterministic inner optimization budget. |
| `cue_base` | `-0.34, -0.11, 0.13, 0.32` | Predeclared four-bundle marginal offsets. |
| `root_signal_generator` | `0.55 + 0.28*c + Normal(0,0.55)` | Shared-root observation available to every class. |
| `global_precision_grid` | `[-2,2], 81 points` | One active global down-weight coordinate and its deterministic optimizer. |
| `root_bundle_pattern` | `1.00, 0.82, 0.65, 0.92` | Corrective four-element bundle means shared by revision arms. |
| `root_contact_mean` | `0.90` | Experiment-43-style supportive contact mean. |
| `witnessing_field` | `1.00, 0.92, 0.78, 0.96; contact 0.90` | Part active with broad precision field. |
| `open_information_field` | `0.92, 1.00, 0.84, 0.93; contact 0.78` | Broad informational comparison. |
| `regulation_field` | `0.13 x4; contact 0.12` | Regulation without a broad evidence route. |
| `narrowed_field` | `0.72, 0.04, 0.04, 0.04; contact 0.10` | Part-dominant narrow contact. |
| `fixed_context_field` | `0.22 x4; contact 0.16` | Matched-exposure single-belief stress readout. |
| `reversed_contact_field` | `0.18, 0.16, 0.12, 0.15; contact -0.05` | Sign-reversed root/contact likelihood control. |
| `root_likelihood_means` | `-1.0, +1.0` | Common identity-root hypotheses. |
| `doover_initial_then_endings` | `5` | Frozen catastrophic episode evidence before present observations. |
| `doover_jitter` | `0.03` | Small fractional-count noise preventing exact duplicate worlds. |
| `premature_session` | `1` | Do-over is deliberately applied before posterior revision begins. |
| `criterion_selection_rates` | `0.80 structured; 0.20 null` | Equivalent to §3.6 counts 16/20 and 4/20. |
| `criterion_heldout_margin` | `0.05` | Frozen §3.6 log-predictive margin. |
| `criterion_pair_tolerance` | `0.12` | Pilot-frozen operational meaning of approximately equal. |
| `criterion_ordering_gap` | `0.30` | Pilot-frozen operational meaning of much greater. |
| `criterion_doover_shortening` | `0.20` | Frozen §3.6 time-to-reduction improvement. |
| `seed_namespace_offsets` | `100000,200000,300000,400000,500000,600000` | Prevent streams for cells and measures from sharing random draws. |

Numerical guards `1e-6`, `1e-10`, `1e-12`, and `1e-300` prevent
singular curvature, division, logarithms, and inactive columns; they do not
define a scientific result. The eight Lanczos coefficients implement the
standard log-gamma approximation used only for beta-Bernoulli evidence.
The provisional criteria (`16/20`, `4/20`, `0.05`, `20%`, and
`16/20`) come from §3.6 of the round specification, not from the model.
