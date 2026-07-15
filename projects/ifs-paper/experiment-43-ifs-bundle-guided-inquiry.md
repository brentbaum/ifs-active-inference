# Experiment 43: an IFS bundle found through guided inquiry

**Status:** Frozen confirmation complete

**Stage statuses:** 43A `support`; 43B `support`; 43C `support`; precision stress `support`

**Freeze commit:** `84c702a2bd7b83def669c999141674b9fcdccda7`

**Result commit:** `a2fceafbc36602eb9644af496d0e1b7b71283539`

## What was tested

The model gives one binary identity root four explicit binary components:
`self`, `world`, `policy`, and `outcome`. The data-generating table contains the
smallest pilot-retained configural pattern that could support both binding and
untreated-component transfer: a two-edge `self-world-outcome` chain. A
Dirichlet learner estimates the complete 16-configuration conditional table
from 256 independent complete scenes per seed; it never receives the authored
generator coefficients.

Every component has a three-level Gaussian branch. A 13-component precision
field contains the twelve branch precisions plus one scalar contact-likelihood
precision. Contact enters as an observation, never as a gate, precision
assignment, action bonus, or depth input. The scalar depth summary remains a
readout with no downstream consumer.

The confirmation used the frozen seeds `17001:17020` exactly once. All exact
marginal, replay, packet, intervention, contact, finite-energy, and monotone
line-search checks passed. The maximum conditional local-marginal mismatch was
`2.22e-16`; exact actions and observations replayed at rate `1.0`.

## Confirmed results

All intervals below are paired two-sided 95% Student t intervals over twenty
seeds.

| Result | Mean effect | 95% interval | Paired wins |
|---|---:|---:|---:|
| Learned joint root accuracy over exact-action factorized replay | `0.0813` | `[0.0577, 0.1048]` | `19/20` |
| Untreated-component transfer over factorized replay | `0.0496` | `[0.0291, 0.0702]` | `17/20` |
| Joint-versus-factorized precision-guided action interaction | `0.0977` | `[0.0576, 0.1377]` | `18/20` |
| Joint held-out log score over shuffled-configuration learner | `0.6629` | `[0.5985, 0.7273]` | `20/20` |
| Joint advantage in configuration-violating scenes | `-0.0328` | `[-0.0749, 0.0093]` | — |

The joint action gain was `0.1094`; the matched-factorized action gain was
`0.0117`. The result therefore supports a learned configural bundle rather than
mere use of a shared identity root, extra model capacity, or better actions
alone. Flipping the outcome component in configuration-violating scenes
removed and numerically reversed the joint advantage.

## Inquiry versus supplied conclusions

An accurate, stable conclusion remained faster: it exceeded inquiry's
immediate root accuracy by `0.2133` (`[0.1916, 0.2349]`). This was allowed by
the frozen design.

Inquiry was better calibrated when the content source was unreliable:

| Guide regime | Inquiry log-loss improvement over conclusion | 95% interval |
|---|---:|---:|
| Noisy | `0.0773` | `[0.0406, 0.1141]` |
| Systematically wrong | `1.0064` | `[0.9935, 1.0192]` |
| Stale after context switch | `1.0204` | `[0.9929, 1.0478]` |

The information-budget sensitivity also favored inquiry for noisy (`0.1437`),
wrong (`0.6041`), and stale (`0.6188`) sources; every interval excluded zero.
Under systematically wrong guidance, conclusion injection increased false-root
revision by `0.6188` (`[0.5894, 0.6481]`). In the inquiry arm, guide error could
only redirect attention; the sampled value still came from the environment.

One proposed interaction did not appear. The inquiry-over-conclusion log-loss
advantage was `0.0219` smaller in the joint world than in the factorized world
(`[-0.0371, -0.0068]`). The confirmation supports robustness of inquiry under
guide error, but not the stronger idea that this robustness grows specifically
because the target is configural.

## Contact

Contact carried `0.0357` nats of mutual information with the identity root,
and contact alone reached only `0.6063` root accuracy, so it was informative
without saturating inference. Accurate scaffolded inquiry reached `0.7867`
with present contact, `0.7609` with contact absent, and `0.7703` with
misattuned contact.

This construction therefore shows contact contributing evidence while inquiry
still adds value. It does not show that loving contact is necessary, sufficient,
or the only revising content.

## Scaffold removal

Stage 43C added a contextual Dirichlet action table only after 43B passed. The
table learned first-action frequencies from guided sessions; a matched table
learned from random guidance. After removal, the guided table improved root
accuracy by `0.0625` (`[0.0056, 0.1194]`) and selected the newly informative
channel first in `100%` of removal episodes, exceeding the frozen `0.03` and
`75%` criteria.

The narrower unsampled-component transfer difference after removal was only
`0.0125` (`[-0.0292, 0.0542]`). The earned result is retained sampling-policy
and root-performance transfer, not a broad post-scaffold component-transfer
claim. No policy change is attributed to precision-profile learning alone.

## Coordinated but releasable precision

In the local-deviation regime, adaptive global precision forecasting improved
over rigid tying by `0.2618` (`[0.1906, 0.3331]`). In the coordinated regime it
retained a `0.2889` advantage over independent local loops (`[0.2294, 0.3483]`).
This supports conditional coordination and release, not rigid global
confidence as epistemic depth.

## Interpretation boundary

These are construction-level simulation results. They support a computational
distinction among learned configural targets, observational interpersonal
evidence, guided sampling, supplied content, precision forecasting, and policy
learning. They do not establish a clinical effect, biological implementation,
the ontology of parts, or identification of Self-energy.

The direct result is that a small learned joint model can use an organized
self-world-policy-outcome pattern, and that question-like guidance is less
suggestion-prone than content injection when a guide is wrong or stale. The
theory-grounded clinical implication is narrower: relationship may make
evidence available and guided attention may make relevant evidence easier to
find. The simulation does not prescribe a therapeutic technique or show that
either mechanism substitutes for the other.

## Artifacts

- Frozen configuration: `projects/emergence-suite/continuous/configs/experiment-43-frozen.toml`
- Confirmation summary: `projects/emergence-suite/continuous/results/confirm_ifs_bundle_inquiry/summary.json`
- Stage status: `projects/emergence-suite/continuous/results/confirm_ifs_bundle_inquiry/status.json`
- Per-seed effects: `projects/emergence-suite/continuous/results/confirm_ifs_bundle_inquiry/per_seed.csv`
- Episode, free-energy, and budget audits are in the same result directory.
