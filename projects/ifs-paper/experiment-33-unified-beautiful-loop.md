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
Current-state free energy and policy free energy are also recorded together as
the active-inference objective. Epistemic depth is computed afterward from
posterior hyper-uncertainty and never feeds inference or action.

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
- independent branch-specific cause posteriors, removing Bayesian binding from
  inference rather than merely changing the final decision;
- random branch selection with the full policy's exact per-episode sample
  budget; and
- fixed sampling of the branch preferred before the switch.

The pre-update structural-break estimate uses forty frozen held-out probes per
seed. These probes score the immediate shock but cannot train the agent.

## Iteration record

The first unified run failed. One observation per action could identify total
branch variance but not three link-specific precisions, leaving the hyper-loop
without enough endogenous evidence. Actions were changed to acquire four-draw
temporal packets under one stable cause. This resolved the identifiability
failure without supplying labels.

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
estimate. No outcome threshold was lowered.

## Results

Across twenty seeds:

| Contrast | Unified | Control | Seed wins |
|---|---:|---:|---:|
| Out-of-sample precision forecast RMSE | 0.579 | 0.881 local | 19/20 |
| Held-out cause accuracy | 0.954 | 0.927 no binding | 16/20 |
| Matched-budget cause accuracy | 0.954 | 0.833 random | 20/20 |
| Mean observation packets | 1.650 | 1.650 random | matched |
| Held-out cause accuracy | 0.954 | 0.621 fixed | 20/20 |
| Immediate break to late accuracy | 0.706 | 0.968 late | 20/20 recovered |

The first action changed from branch one before the out-of-sample switch to
branch three afterward, then returned to branch one after the hidden structural
break, in 20/20 seeds. Late mean log precision was `1.540` for the newly useful
branch and `-0.569` for the formerly useful branch. Joint variational free
energy was non-increasing in every recorded episode. All eight perturbation
cells spanning observation precision, action cost, and hyper-prior variance
preserved the full qualitative signature.

## External-reader verdict

At the level of computational construction: **yes, this is it**. The model now
contains the paper's multilayer world model, global precision hyper-model,
ascending second-order errors, descending precision broadcast, Bayesian
binding, temporal recursion, and epistemic policy selection in one loop. Each
operation disappears or weakens under its relevant matched ablation.

That verdict has a strict boundary. The construction is a faithful minimal
*realization*, not a unique derivation of Beautiful Loop Theory. Its low-rank
field orientation, Gaussian branches, action set, change detector, and
four-draw observation packets are authored inductive biases. The results show
what computational work global recursive precision can perform under those
assumptions. They do not show that such a field emerges in arbitrary agents,
that it is necessary or sufficient for phenomenal consciousness, or that the
IFS clinical mapping is true.
