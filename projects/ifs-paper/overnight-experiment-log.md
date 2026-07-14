# Adaptive epistemic-depth experiment log

**Branch:** `codex/epistemic-depth-experiment-tournament`

**Maximum:** 30 experiments

**Rule:** added complexity must create a new discrimination or improve robust
out-of-sample performance. Simplicity wins ties.

## Tranche A — formal fidelity

### Experiment 1 — Existing five-channel construction

Reproduced the committed global precision-field construction as the reference.
It instantiates the five verbal steps of the Beautiful Loop hyper-loop but
supplies realized precision evidence exogenously and has no explicit hierarchy.

**Decision:** retain as a clinical construction check, not as the formal
baseline for literature combinations.

### Experiment 2 — Explicit three-level hierarchy

Added latent states $x^{(1:3)}$, fixed observations at each level, and
layer-specific precision hyperparameters. State inference now runs inside the
same loop as precision inference.

**Result:** implementation and finite-posterior criteria passed across all test
seeds.

### Experiment 3 — Endogenous second-order errors

Replaced scripted realized precision with the expected residual variance of
the inferred lower-level states. The residual evidence updates the posterior
over layer precision, which is rebroadcast into the next state-inference pass.

**Result:** residuals were positive and finite, and the joint free-energy proxy
changed across iterative state/precision updates.

### Experiment 4 — Global versus local meta-inference

Compared a shared global hyper-node against independent local precision loops.
In a coordinated precision shift, evidence from two layers had to predict a
held-out third layer. In a second environment, layer precisions shifted in
different directions and every layer was observed.

**Result:** on the coordinated held-out test, mean error was `0.223` for the
global model versus `1.000` for local loops. On independent shifts, the local
model correctly won: RMSE `0.167` versus `0.344` for the global model.

**Interpretation:** global pooling earns its complexity only when precision
changes share real cross-layer structure. This is more compelling than a claim
that globality is always better. It supplies a falsifiable scope condition:
epistemic depth should help when context predicts coordinated changes across
levels, and should become a liability when those changes are genuinely
independent.

**Decision:** advance the hierarchical global model, while retaining the local
model as a standing adversarial control. Do not add further global machinery
unless it improves a held-out prediction.

## Tranche B — twenty literature-derived operators

Experiments 5–24 translated twenty papers into one minimal operator each and
ran every operator through the same seven arms, twenty seeds, and three
strengths. The arms tested witnessing, regulation without activation, contact
under narrowing, information through an open field, accurate danger, false
suggestion, rupture and repair, and removal of the relational scaffold.

The top single operators were:

| Experiment | Operator | Source | Score | Robustness |
|---:|---|---|---:|---:|
| 7 | Context redescription | Chamberlin (2023) | 0.866 | 1.00 |
| 20 | Flexible boundary | Sandved-Smith et al. (2026) | 0.842 | 1.00 |
| 14 | Patient testing | Li et al. (2025) | 0.841 | 1.00 |
| 8 | Spare capacity | Smith et al. (2020) | 0.835 | 1.00 |
| 9 | Regulatory authority | Palejova (2026) | 0.830 | 1.00 |

The global covariance baseline scored `0.815`. Context redescription improved
the benchmark by adding a new state that learned that the active schema
belonged to one context and need not govern another. It preserved the
distinction between opening access and changing the representation itself.
The result is therefore more interesting than a stronger learning rate, but
it is not independent evidence for Chamberlin's theory: the operator and score
are construction choices derived from that theory.

Somatic safety and policy-likelihood interaction failed the across-strength
robustness criterion in this implementation. This does not falsify their
source theories. It shows that these minimal translations did not preserve
the common benchmark's witnessing-versus-control discrimination.

## Tranche C — earned recombinations

Experiments 25–28 recombined the top three nonidentical operators:

25. context redescription + flexible boundary;
26. context redescription + patient testing;
27. flexible boundary + patient testing; and
28. all three operators.

The best combination was context redescription plus patient testing at
`0.868`, only `0.0016` above context redescription alone. The preregistered
complexity margin was `0.020`. No combination earned retention.

**Decision:** stop at twenty-eight experiments. Retain global recursive
precision control as the access mechanism and context redescription as the
leading candidate change mechanism. Do not add a second named force or a
multi-operator stack. Flexible boundaries and patient-led testing remain
useful experimental contrasts rather than components of the core theory.

## What was learned

The simplest surviving account has two operations, not one:

1. epistemic depth keeps precision allocation recursively available across the
   hierarchy while the part is active; and
2. representational redescription can use that access to construct a
   context-indexed model in which an old protective inference was coherent
   then without being compulsory now.

The formal comparison adds a scope condition: global coordination should help
when precision changes share real structure across levels. Independent local
changes should be handled locally. The literature tournament adds a second
boundary: access is not itself revision. These two constraints sharpen the
theory without multiplying its central machinery.

All numerical results are in
`projects/emergence-suite/continuous/results/literature_tournament/`. The
tournament is hypothesis-generating and post-baseline; it did not test human
outcomes, reproduce the cited papers, or supply clinical effect sizes.

## Experiment 29 — higher-fidelity Beautiful Loop hierarchy

Implemented the seven-part upgrade proposed by the fidelity audit as a
separate three-level Gaussian generative model. The model alternates exact
state inference with Gaussian variational inference over a shared global
precision factor and layer-specific deviations. Expected residuals provide
the second-order errors. The run records three layer-local free energies, a
hyper free energy, and a joint variational free energy; the joint objective
descended monotonically in the all-layers construction check.

The matched ablation replaced the global factor with three independent local
meta-loops while preserving each layer's marginal prior variance. Four
training contexts taught either one shared precision slope or three local
slopes. At an out-of-range fifth context, only layer one initially received
new residual evidence.

**Result:** global forecast RMSE was `0.255` versus `0.411` for local loops
(20/20 seed wins). Early held-out layer error was `0.205` versus `0.414`
(15/20), and latent-state RMSE was `0.3683` versus `0.3740` (18/20). After all
layers received evidence, local loops reduced precision error by `0.181` on
average and improved in 17/20 seeds.

**Decision:** retain as the new formal fidelity baseline. The main effect is
anticipatory precision forecasting, not a large state-inference effect. The
remaining experiment slot should test whether the global model can detect and
recover when the assumed cross-layer context structure breaks.

## Experiment 30 — endogenous temporal hyper-model

Moved context-conditioned precision learning inside an online hyper-process.
The agent compared a shared global context slope with independent layer slopes,
using lower-level residuals as second-order evidence. The environment changed
from coordinated to independent precision shifts and back without exposing
the regime label.

The first construction released coupling but did not confidently learn or
recover it. A second construction retained the criteria and added a mild
Occam prior for the four-parameter shared model over the six-parameter local
model. The successful model's global weight moved from `0.704` to `0.080` and
back to `0.740`. It beat forced global pooling during the broken regime
(`0.319` versus `0.574` RMSE) and remained competitive with local loops during
coordination (`0.087` versus `0.098`). All model-selection criteria passed in
20/20 seeds.

**Decision:** advance the temporal hyper-model to the Bayesian-binding
experiment. Retain the explicit complexity prior in the model specification;
do not describe the selection as emerging without inductive bias.
