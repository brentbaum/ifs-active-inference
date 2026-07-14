# Beautiful Loop fidelity audit of the v11 global precision-field simulation

**Date:** 2026-07-13

**Code audited:** `projects/emergence-suite/continuous/src/GlobalPrecisionField.jl`

**Reference:** Laukkonen, Friston, and Chandaria (2025), especially Table 1 and
the five-step hyper-loop in §6.1.

## Bottom line

The current simulation is strongly in the *spirit* of the Beautiful Loop
account and materially closer than the retired scalar-depth models. It is not
yet an implementation of the paper's formal model. The accurate label is
**minimal precision-field analogue** or **construction check**.

It captures the proposed direction of causation:

1. a context-conditioned hyper-model predicts a multivariate precision field;
2. lower consumers receive the predicted precisions;
3. forecast errors return to the hyper-model;
4. the posterior over the field updates; and
5. the revised field is broadcast downward.

It also respects two conceptual constraints the paper emphasizes: epistemic
depth is global rather than a local metacognitive gain, and high epistemic
depth need not imply calm or low threat precision.

## Where it matches

| Beautiful Loop proposal | Current implementation | Fidelity |
|---|---|---|
| Multivariate $\Phi$ rather than one depth dial | Five log-precision components | Strong conceptual match |
| Context-sensitive hyper-prediction | Learned profile supplies the prior mean | Partial match |
| Second-order error on predicted precision | Realized minus predicted log precision | Structural match |
| Recursive hyper-update | Conjugate multivariate Gaussian update | Minimal match |
| Downward precision broadcast | $\exp(E_q[\Phi])$ controls lower consumers | Strong minimal match |
| Global rather than local coordination | Correlated prior couples all channels | Partial match |
| Danger can raise precision under depth | Accurate-danger construction is high dominance/high depth | Strong conceptual match |
| Scalar depth is not causal | Index is calculated after inference | Strong match |

## Where it does not yet match Table 1

1. **Channels replace hierarchical layers.** The paper defines
   $\Phi=\{\phi^{(1)},\ldots,\phi^{(L)}\}$ over a multilayer generative model.
   The code uses functional channels—part, context, interoception,
   relationship, policy—without explicit latent states $x^{(l)}$ at different
   levels of abstraction.

2. **There is no joint generative process.** Table 1 specifies
   $p(s,x^{(1)},\ldots,x^{(L)},\Phi)$ and a joint posterior. The code infers
   $\Phi$ from supplied log-precision observations but does not infer sensory
   causes and the hyper-field together.

3. **Precision errors are exogenous.** The "realized log precision" vector is
   scripted by each condition. It is not estimated from the residuals or
   curvature of lower-level inference. This makes the hyper-loop easy to
   satisfy because the answer is supplied in the form the hyper-model needs.

4. **Hyper free-energy is only an energy diagnostic.** The reported quadratic
   prediction energy is not the paper's
   $F_{hyper}=E_q[\ln q-\ln p(s,x^{(1)},\ldots,x^{(L)},\Phi)]$, and it does not
   include the complexity of the joint posterior.

5. **Globality is stipulated by covariance.** A fixed off-diagonal covariance
   makes errors spread across channels. In the paper, nonlocality follows from
   every layer being a child of the hyper-parameter in a factor graph and from
   recursive message passing between all levels.

6. **The clinical update is hand-written.** Identity revision is a logistic
   state updated by a chosen learning-rate equation. It is not a posterior
   consequence of the lower-level generative model or Bayesian model
   reduction.

7. **There is no inferential competition or unified reality model.** Beautiful
   Loop Theory requires a reality model, coherent binding, and epistemic depth.
   This simulation isolates only an analogue of the third condition.

8. **The depth index is ours.** Confidence × calibration × breadth × global
   integration is a useful diagnostic, but the source paper supplies no such
   scalar. Its thresholds and the binary global-integration term are
   construction choices, not derived quantities.

9. **Temporal prediction is weak.** The learned profile carries information
   between sessions, but the model does not forecast the next precision field
   from an explicit dynamical transition model.

## What an external critic would say

The favorable reading is: *This is a clean toy demonstration of the paper's
five-step verbal loop, and it correctly prevents a scalar depth score from
doing causal work.*

The skeptical reading is: *The simulation has renamed a correlated Kalman
update as a global hyper-model. It supplies the target precision profile as
data, computes a bespoke depth score, and hand-codes the clinical outcome. It
therefore demonstrates logical compatibility, not emergence from the formal
model.*

Both readings are fair. The present manuscript is safe only when it calls the
run a minimal construction check and does not say that it implements Table 1.

## Likely Ruben-style response

The strongest part of the revision is the definitional correction: $E_t$ no
longer suppresses part precision by fiat, global and local depth are separated,
and accurate danger can remain precise. A technically sympathetic author of
Beautiful Loop Theory would likely recognize the five-step architecture.

The immediate questions would probably be:

- Where are the hierarchical latent states and their local free energies?
- How do lower-level residuals generate the second-order precision error?
- Is $q(\Phi)$ inferred jointly with the reality model or fitted to an external
  precision label?
- What makes the field global beyond a correlated prior?
- Can the same model distinguish one global hyper-model from several local
  parametric-depth loops?
- Does the downward broadcast improve out-of-sample inference, rather than
  merely reproduce a constructed regime?

## Minimum credible upgrade

The next model should be a small three-level Gaussian hierarchy with:

1. explicit states $x^{(1:3)}$ and observations $s$;
2. layer-specific log precisions controlled by $\Phi$;
3. iterative inference over $q(x^{(1:3)})$ and $q(\Phi)$;
4. second-order errors estimated from lower-level residuals;
5. local and joint free-energy traces;
6. an ablation replacing the global $\Phi$ with matched independent local
   meta-loops; and
7. an out-of-sample context switch where a learned global precision forecast
   improves inference before all local loops can relearn.

If the global model wins that final test with fewer effective degrees of
freedom, the simulation would add something the current construction cannot:
evidence that global recursive precision control is computationally useful,
not merely definable.

## Paper consequence now

Retain the dominance–depth distinction and the clinical precision-field
proposal. Continue calling the existing run a construction check. Replace any
claim that it "implements the Beautiful Loop formal model" with the narrower
claim that it instantiates a minimal analogue of the proposed five-step
hyper-loop. Treat a joint hierarchical implementation as required before the
paper can claim formal continuity with Table 1.

## Follow-up: three-level implementation completed

The follow-up model in `BeautifulLoopHierarchy.jl` now implements the seven
items under “Minimum credible upgrade”:

- three explicit Gaussian states and observations;
- three layer-specific log precisions generated by a shared global factor plus
  local deviations;
- alternating exact Gaussian $q(x^{(1:3)})$ and Gaussian variational
  $q(\Phi)$ updates;
- second-order messages computed from expected lower-level residuals;
- layer-local, hyper, and joint variational-free-energy traces;
- independent local precision loops with matched marginal prior variance; and
- an out-of-sample context switch after learning a context-conditioned
  precision forecast.

At the unseen context, the global model's mean forecast RMSE was `0.255`
against `0.411` for local loops. After only the first layer received new
precision evidence, held-out error at layers two and three was `0.205` versus
`0.414`; global won 15/20 seeds. Its latent-state RMSE was `0.3683` versus
`0.3740`, winning 18/20. Once all local loops received residual evidence, they
reduced their precision error by `0.181` on average.

This materially changes the fidelity judgment. The new model is not merely a
correlated update renamed as a hyper-model: the global node is an explicit
common parent, residual messages are endogenous, the variational objective is
tracked, and the forecast has an out-of-sample consequence. It is reasonably
described as a **higher-fidelity minimal implementation of the Beautiful Loop
precision hyper-loop**.

It remains short of the full theory. The hierarchy is linear Gaussian, the
context feature and shared slope are authored, between-context learning is a
separate regression rather than one end-to-end dynamical model, and the model
does not implement coherent binding, policy selection, clinical identity
revision, or representational redescription. An external critic can therefore
accept continuity with the formal precision loop while still rejecting any
claim that the full Beautiful Loop theory or the IFS application has been
derived.

## Follow-up: temporal recursion, binding, and action

Experiments 30–32 separately added the three missing operations emphasized in
the broader theory. An online hyper-model learned when context-conditioned
precision changes were globally coupled, released that coupling when the
structure broke, and recovered it when coordination returned. An exact
discrete binding model then let three local causes compete to support one
global cause; precision controlled both sensory gain and participation in the
coherence prior. Finally, an expected-free-energy policy redirected sampling
after an unannounced channel-reliability switch.

The results make the construction closer in three specific senses: precision
is forecast and corrected across time; a global posterior is selected through
precision-weighted inferential competition; and learned precision beliefs
guide epistemic action. They do not form one end-to-end model. The temporal,
binding, and policy experiments remain separate constructions with authored
state spaces, and the policy experiment receives outcome feedback after each
episode. The defensible claim is therefore that each proposed operation is
computationally sufficient under a minimal model—not that their conjunction,
consciousness, or the clinical IFS mechanism has been derived.

## Unified construction and fair-control audit

Experiment 33 places the separate operations into one conditionally
Gaussian generative model that contains three explicit levels on three branches,
one global cause, one nine-component precision field, and one posterior over
epistemic policies. Alternating inference over states, the global cause, and
the precision field minimizes the recorded current-state variational free
energy. A score combining expected information gain and sampling cost supplies
the policy factor; it is expected-free-energy-shaped, not exact expected free
energy under the same continuous generative model. The revised field is
broadcast into every transition and into the next action; the next packet of
posterior residual moments then corrects that field. No hidden state or
reliability label is used for learning.

The matched controls are internal rather than comparisons across separate
experiments. Independent local precision regressions have the same marginal
prior variance. The no-binding agent factorizes its cause posterior by branch,
then combines the graded local evidence by summed log odds or soft posterior
pooling. The random policy receives the exact sample budget chosen by the full
policy.

That fair-control audit falsifies the unified model's binding claim. Full cause
accuracy was `0.954`, compared with `0.950` under log-odds pooling and `0.947`
under soft pooling; seed-wise wins were only 5/20 and 6/20. Because the branches
are conditionally independent under one binary cause, the full posterior is
ordinary Bayesian evidence pooling rather than nontrivial competition. The
precision forecast (`0.579` versus `0.881` RMSE) and matched-budget action
advantage remain, but global and local task accuracy are close (`0.954` versus
`0.937`).

## Relational binding and learned structure

Experiments 34--36 implement and confirm the two required repairs. The binding
environment makes the scene cause a parity relation among three local causes.
Every local marginal carries zero information about the scene, while the joint
configuration identifies it. On untouched seeds, the relational model reached
`0.726` accuracy against `0.503` for a capacity-matched factorized control and
won 20/20 paired worlds. All seven load-bearing stress cells passed, and the
relational prior became harmful on deliberately relation-violating scenes.
This is non-vacuous binding, but the relation itself is supplied rather than
learned.

The structure-learning environment samples a new hidden loading vector in each
world. A compact six-parameter global forecaster learns it from posterior
residuals; its strong comparator has eighteen local coefficients plus
evidence-weighted shrinkage and can discover the same tying. Fresh-seed RMSE
was `0.673` globally, `0.835` for that adaptive comparator, and `0.977` for
independent loops, with 17/20 paired wins against each. Scene accuracy was
identical. The claimed result is therefore sample-efficient precision
forecasting, not improved decisions. The declared local-deviation crossover
failed its magnitude criterion and remains recorded as a failed confirmation.

## Identifiability correction and current verdict

Experiment 37 corrects an error in the earlier construction. Bottom-only
observations in an additive Gaussian hierarchy identify total transition
variance, not its layerwise decomposition; repeated temporal draws cannot fix
that structural ambiguity. The corrected model emits noisy observations at
every level and compares the compact global field with a nested hyper-model
that contains the same shared terms plus shrinkage-controlled local
deviations. The compact model gained only `0.012` RMSE under exact sharing,
failing the declared `0.050` criterion. At deviation scales one, two, and three,
the nested model won 20/20 seeds and its shrinkage adapted downward.

The strongest defensible external-reader verdict is now **yes for a minimal
computational construction of the three Beautiful Loop operations, no for a
reproduction or unique architecture**. The sequence contains a hierarchical
precision hyper-loop with endogenous residual messages, a genuinely joint
binding problem, and epistemic sampling; the two central effects replicate on
fresh seeds against strong controls. But binding and action remain coupled only
in an authored toy environment, the parity relation is not learned, free-energy
descent is partly guaranteed by line search, and the policy is a surrogate.
Most importantly, globality should not be equated with identical precision or
one privileged node. A global hyper-model is defined by joint recursive message
passing across the hierarchy and may correctly infer substantial local
structure. Its shrinkage estimates environmental coupling; it does not measure
epistemic depth.
