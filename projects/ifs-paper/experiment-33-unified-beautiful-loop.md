# Experiment 33 — a unified Beautiful Loop agent

**Date:** 2026-07-14

## Central move

Epistemic depth is not another layer of content. It is the loop by which a
model predicts, tests, and redeploys the precision structure of all its layers.

Experiments 30–32 established temporal forecasting, binding, and epistemic
action separately. This experiment asks whether those effects survive when
they are consequences of one small generative model rather than interfaces
between three constructions.

## Construction

One binary global cause generates three conditionally Gaussian branches. Each
branch contains three explicit states:

\[
\begin{aligned}
g_t &\sim \operatorname{Cat}(1/2,1/2),\\
x^{(3)}_{tj} &\sim \mathcal N(\alpha g_t,e^{-\phi^{(3)}_{tj}}),\\
x^{(2)}_{tj} &\sim \mathcal N(x^{(3)}_{tj},e^{-\phi^{(2)}_{tj}}),\\
x^{(1)}_{tj} &\sim \mathcal N(x^{(2)}_{tj},e^{-\phi^{(1)}_{tj}}),\\
s_{tj}\mid a_t=j &\sim \mathcal N(x^{(1)}_{tj},\tau_s^{-1}).
\end{aligned}
\]

The nine-component field $\Phi_t$ controls every transition. Its prior is a
context forecast from one low-rank hyper-model with three layer intercepts and
one global field orientation. Alternating analytic Gaussian state inference,
exact enumeration of $q(g_t)$, and a Gaussian variational update of
$q(\Phi_t)$ minimizes one current-state variational free energy. Posterior
transition residual moments provide the only precision evidence. Hidden
causes, latent states, and true precisions are never passed to an update.

Policies minimize expected posterior entropy plus observation cost and an
epistemic term for uncertainty about $\Phi$. The resulting
$q(\pi)\propto\exp[-G(\pi)/T]$ determines which branch becomes observable.
Current-state and policy free energy are recorded separately; their numerical
sum is not treated as a common objective across policies. Epistemic depth is
computed afterward from posterior hyper-uncertainty and never feeds inference
or action.

## Discriminating tests

The agent first learns across five contexts with all branches available. It is
then evaluated at two out-of-range contexts. The learned field should forecast
which branch will be useful before independent meta-loops can estimate every
transition. Later, with context held fixed, the environment reverses the field
orientation without notifying the agent. Second-order forecast error must
release confidence in the old hyper-model, revise the global orientation, and
broadcast the new field.

Four controls isolate the proposed operations:

- eighteen independent context-sensitive precision parameters with matched
  marginal prior variance;
- independent branch-specific cause posteriors combined by either soft
  posterior pooling or summed log odds, both of which retain graded evidence;
- random branch selection with the full policy's exact per-episode sample
  budget; and
- fixed sampling of the branch preferred before the switch.

The pre-update structural-break estimate uses forty frozen held-out probes per
seed. These probes score the immediate shock but cannot train the agent.

## Iteration record

The first unified run failed. One observation per action could identify total
branch variance but not three link-specific precisions, leaving the hyper-loop
without enough endogenous evidence. Actions were changed to acquire four-draw
temporal packets under one stable cause. This stabilized the inferred residual
moments without supplying labels, but it did **not** resolve structural
identifiability. Experiment 37 later showed that bottom-only observations in an
additive Gaussian chain identify only the sum of link variances; the apparent
layerwise solution here inherits the model's constrained field basis.

The next benchmark incorrectly asked a correct context forecast to show slow
relearning. The evaluation was split into a predicted out-of-sample context
change and a separate unannounced structural break. A second architectural
failure then became visible: three channel-specific slopes shared information
across levels but not across the whole field. Replacing them with one inferred
field orientation made a precision error in one branch informative about every
branch and level.

The accumulated hyper-posterior initially resisted the hidden break. A
second-order change detector was added to release old parameter precision when
forecast error exceeded its own scale. The original implementation enabled
this detector at the known training boundary; external review replaced that
shortcut with a regime-independent evidence burn-in.

Finally, the random control was matched for sample budget, the no-binding
control was factorized inside inference, local and hyper free-energy traces
were corrected, and a frozen shock probe replaced a noisy five-trial recovery
estimate. A subsequent external audit found that the factorized control still
threw away its graded posterior at the decision boundary and used a hard
majority vote. The model was therefore rerun with soft and log-odds pooling;
the original hard vote remains only as a labeled historical diagnostic.

## Results

Across twenty seeds:

| Contrast | Unified | Control | Seed wins |
|---|---:|---:|---:|
| Out-of-sample precision forecast RMSE | 0.579 | 0.881 local | 19/20 |
| Held-out cause accuracy | 0.954 | 0.950 log-odds pooling | 5/20 |
| Held-out cause accuracy | 0.954 | 0.947 soft pooling | 6/20 |
| Historical hard-vote accuracy | 0.954 | 0.937 hard vote | 14/20 |
| Matched-budget cause accuracy | 0.954 | 0.833 random | 20/20 |
| Mean observation packets | 1.650 | 1.650 random | matched |
| Held-out cause accuracy | 0.954 | 0.621 fixed | 20/20 |
| Immediate break to late accuracy | 0.706 | 0.968 late | 20/20 recovered |

The first action changed from branch one before the out-of-sample switch to
branch three afterward, then returned to branch one after the hidden structural
break, in 20/20 seeds. Late mean log precision was `1.540` for the newly useful
branch and `-0.569` for the formerly useful branch. Joint variational free
energy was non-increasing because line search enforces that implementation
invariant. Only four of eight perturbation cells retained an advantage over
the fair log-odds control.

## External-reader verdict

**The original binding claim is falsified.** Once independent local posteriors
are combined without discarding their magnitude, the apparent binding
advantage falls from 2.8 points to 0.4--0.8 points and loses its seed-wise
criterion. In this environment the branches are conditionally independent
given the global cause, so a bound posterior is ordinary Bayesian pooling, not
a nontrivial inferential competition. The construction therefore demonstrates
a precision hyper-loop and adaptive epistemic sampling, but not binding.

The remaining positive results also retain strict boundaries. The global field
receives the correct low-rank loading basis, its task accuracy nearly matches
the independent local meta-loops (`0.954` versus `0.937`), and its policy uses
an information-gain surrogate rather than exact expected free energy under the
same continuous model. The strongest surviving result is precision forecasting
(`0.579` versus `0.881` RMSE) and useful adaptive sampling relative to a
matched-budget random policy. Experiments 34--37 separately repair the binding,
structure-learning, and identifiability tests; they do not retroactively turn
this construction into evidence for those claims.
