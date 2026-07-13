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
