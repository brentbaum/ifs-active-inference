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

## Experiment 31 — precision-weighted Bayesian binding

Enumerated one global cause and three locally competing causes under an exact
discrete posterior. The initial fixed-coherence construction increased
confidence but did not reliably beat local majority decisions or reject a
salient distractor. Raising coherence did not fix correctness. A repaired
benchmark distributed correct evidence across individually ambiguous channels,
revealing that the remaining failure came from forcing unreliable channels to
bind as strongly as reliable ones.

The successful construction made the local-to-global coherence prior depend on
the precision field. Overall cause accuracy was `0.888` versus `0.822` for
local decisions; ambiguous coherent accuracy was `0.863` versus `0.830`, and
confidence was `0.631` versus `0.472`. The model rejected the salient
distractor in `0.814` of trials; inverting the precision field reduced this to
`0.288`. Overall binding and calibrated-precision advantages held in 20/20
seeds; ambiguous accuracy won in 19/20.

**Decision:** advance precision-weighted binding to the policy experiment.
Treat the result as evidence that global coherence must be precision-sensitive,
not as evidence that stronger coherence alone creates better binding.

## Experiment 32 — epistemic agency

Added expected-free-energy selection among three evidence channels. Policies
minimized expected posterior entropy plus sampling cost and a small parameter-
learning bonus. The unannounced switch made channel one unreliable and channel
three reliable. Second-order surprise relaxed the learned precision profile so
the agent could explore again.

The first run was invalid because random and fixed controls stopped without
sampling while the epistemic bonus made the EFE agent sample nearly everything.
The successful revision required one initial observation for all strategies
and reduced the parameter bonus. A final review corrected below-chance
reliability handling and extended each hidden regime to 100 episodes to remove
seed-sensitive short-window effects. Post-switch accuracy was `0.822` for EFE,
`0.749` for random, and `0.558` for fixed sampling. EFE used `1.000` sample per
episode versus `1.128` for random. Late accuracy recovered from `0.692` to
`0.887`, while first actions shifted from channel one (`0.750` before) to
channel three (`0.937` late). All frozen criteria passed.

**Decision:** retain this as evidence for adaptive precision-guided epistemic
sampling. Keep the stronger binding claim in experiment 31: experiment 32
usually selects one channel and therefore does not independently demonstrate
multi-channel binding.

## Experiment 33 — unified Beautiful Loop agent

Combined the explicit three-level Gaussian hierarchy, global cause binding,
temporal precision forecasting, second-order hyper-updates, and expected-free-
energy action in one model. The agent learns only from its observations and
posterior residual moments. It is never given the cause, latent states, true
precision, switch label, or experimental regime.

The first implementation exposed three real failures. A single observation
could not identify link-specific precision; a supposedly global field still
contained independent channel slopes; and accumulated parameter certainty
prevented structural revision. Four-draw temporal packets supplied identifiable
residual structure, one latent field orientation created genuinely nonlocal
sharing, and a second-order change detector released obsolete precision. A
known training-boundary gate was removed after adversarial review.

Final forecast RMSE was `0.579` versus `0.881` for matched independent loops.
The original cause-accuracy contrast was later found to use an unfair hard
vote. With graded local evidence retained, full accuracy was `0.954`, versus
`0.950` for summed local log odds and `0.947` for soft pooling. The full model
won only 5/20 and 6/20 seeds. Matched-budget random action scored `0.833`; fixed
sampling scored `0.621`. Frozen structural-break accuracy was `0.706` and late
accuracy was `0.968`; field and action reversal occurred in 20/20 seeds. Only
four of eight original perturbation cells retained a fair-control advantage.

**Decision:** the binding claim is falsified and the earlier external-reader
verdict is withdrawn. Retain the precision-forecasting and adaptive-action
results, explicitly report the near-match to local loops, and build a new
environment with genuine local competition before claiming binding.

## Experiment 34 — binding as relational synergy

The first nonfactorized exclusion model failed its full pilot (`0.729` versus
`0.724`; 10/20 wins), despite a positive two-seed screen. It was replaced with
a parity benchmark in which the global scene is encoded only in the relation
among three locally uniform causes. The control has identical local marginals
and an identical precision loop but no relational factor.

Overall held-out accuracy was `0.722` versus `0.507`; on relation-preserving
scenes it was `0.747` versus `0.506`. The relational model won both contrasts
in 20/20 exploratory seeds. On the five-percent adversarial relation violations
the result reversed (`0.248` versus `0.493`), exposing the scope condition.
Precision-forecast RMSE was identical (`0.521`) by construction.

**Decision:** retain as the first non-vacuous binding result, but label it
exploratory. The relation is supplied rather than learned; capacity-matched
structure learning and fresh confirmation are required next.

## Experiment 35 — learned precision structure

Replaced the supplied channel basis with a different hidden, randomized loading
vector in every seed. The global model inferred three layer intercepts and
three loadings. Its strong control was an eighteen-parameter local model with
predictive model averaging over six shrinkage strengths, allowing it to learn
the same tying rather than forbidding global regularity.

Global out-of-sample forecast RMSE was `0.676`, versus `0.832` for the adaptive
local model and `0.958` for independent loops. It won 20/20 and 19/20 seeds.
Both structured models recovered the hidden orientation (`r=0.981` global,
`0.988` adaptive), and the adaptive model increased effective shrinkage from
`7.38` to `9.72`. Scene accuracy was identical at `0.688`.

**Decision:** the compact global structure earns a forecasting advantage even
without a supplied loading basis and against a tying-capable control. Do not
convert that result into a task-level claim. Freeze the architecture and test
fresh seeds plus environments with increasing local deviations.

## Experiment 36 — frozen fresh-seed confirmation

Relational binding confirmed at `0.726` versus `0.503` with 20/20 wins.
Learned global precision confirmed at `0.673` RMSE, versus `0.835` adaptive
local and `0.977` independent, with 17/20 wins against both. Scene accuracy was
identical (`0.686`). All seven binding stress cells and all ordinary precision
stress cells passed.

The frozen scope crossover failed its magnitude criterion. Global remained
better by `0.028` at deviation `2.0`; adaptive local won by only `0.023` at
deviation `3.0`, below the declared `0.050`. Effective local shrinkage fell to
`5.71`, so the direction was right but adaptation was too conservative.

**Decision:** preserve the overall failed status (9/11 precision predictions).
The two primary confirmations remain positive. Improve the local learner, keep
the crossover threshold, and use another untouched seed block.

## Experiment 37 — identifiable nested precision structure

The attempted random-effects rebuild exposed that bottom-only observations
cannot identify three additive link variances. The final construction added
noisy observations at every level while keeping latent states and true
precisions hidden. It compared the compact global field with a nested model
containing the same six shared coefficients plus nine shrinkage-controlled
local deviations.

On paired fresh seeds, RMSE was `0.345` global versus `0.357` nested under exact
sharing. At deviation scales `1`, `2`, and `3`, nested RMSE was `0.670`, `1.032`,
and `1.340`, versus global `1.355`, `2.665`, and `3.997`; nested won 20/20 seeds
in every nonzero condition. Effective shrinkage fell from `8.31` to `0.90`.

The frozen overall status remains failed because the exact-sharing global
advantage was only `0.012`, below `0.050`. The better theoretical conclusion is
not architectural uniqueness. The shrinkage estimate describes how much
cross-layer structure the environment supports; it is not epistemic depth.
Epistemic depth instead belongs to the recursively closed joint hyper-model
that can infer either shared structure or warranted local deviations and
rebroadcast the resulting field throughout the hierarchy.

## Experiment 38 — identifiable globality control

An external review found that Experiment 37's compact and nested models were
both global and that the independent control had disappeared precisely when
layerwise precision became identifiable. A new protocol was committed before
opening seeds `12001:12020`. It compared compact global, nested global, and
eighteen genuinely independent local coefficients with matched marginal priors
and identical noisy layer evidence.

Under exact sharing, forecast RMSE was `0.340` compact and `0.359` nested,
versus `0.637` independent; both global models won 20/20 seeds. At deviation
scale `2.0`, nested global reached `1.068`, independent `1.090`, and compact
`2.716`; nested beat compact in 20/20 while shrinkage fell from `8.32` to
`1.88`. Accuracy remained tied and all five frozen criteria passed.

**Decision:** the identifiable globality gap is closed. Joint precision
inference earns sample efficiency when structure is shared, and the same global
hyper-model can release tying until it matches independent learning when the
environment warrants local structure. Preserve the direct-layer-monitoring
fidelity cost and do not convert this into a universal global advantage.
