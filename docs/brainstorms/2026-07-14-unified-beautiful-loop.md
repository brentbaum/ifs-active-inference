---
date: 2026-07-14
topic: unified-beautiful-loop
---

# A minimal unified Beautiful Loop agent

## What we are building

Experiment 33 will place temporal precision prediction, hierarchical state
inference, Bayesian binding, and epistemic action inside one small generative
model. A binary global cause generates three three-level Gaussian branches.
One global precision field, `Phi`, sets the precision of every transition in
the branches. Alternating inference over the global cause, the explicit states
`x^(1:3)`, and `Phi` minimizes one variational objective. The posterior over
`Phi` is broadcast back into every branch and also determines a posterior over
the next sampling policy through expected free energy.

The environment changes its context-to-precision relation without announcing
the change. The agent never receives the true cause or channel reliability.
It must learn precision only from posterior residual moments and cross-channel
coherence. This removes the strongest shortcut in experiment 32.

## Approaches considered

1. **Join experiments 30–32 as a pipeline.** Simple, but it would preserve
   three objectives and three state spaces. Rejected because an external reader
   could correctly call it a collage.
2. **Extend the categorical RxInfer simulations.** Exact and useful for
   binding, but it would move away from Table 1's explicit multilayer Gaussian
   construction and obscure second-order residuals.
3. **One conditionally Gaussian hierarchy with a discrete global cause.** This
   retains explicit levels, permits analytic state inference, makes binding a
   consequence of a shared cause, and keeps policy evaluation small. Chosen.

## Generative model

For episode `t`, branch `j`, and level `l`:

```text
g_t ~ Categorical(1/2, 1/2)
x^(3)_{tj} ~ Normal(g_t, exp(-phi^(3)_{tj}))
x^(2)_{tj} ~ Normal(x^(3)_{tj}, exp(-phi^(2)_{tj}))
x^(1)_{tj} ~ Normal(x^(2)_{tj}, exp(-phi^(1)_{tj}))
s_{tj} | a_t=j ~ Normal(x^(1)_{tj}, observation_variance)
Phi_t ~ Normal(H(c_t; theta), Sigma_Phi)
q(pi_t) = softmax(-G(pi_t))
```

`H` is one online context model for the complete precision field. It is updated
from `q(Phi_t)`, not from true precisions. Independent local meta-loops receive
matched marginal prior variance but cannot share second-order evidence across
levels. Derived depth, binding, and coherence scores are analysis outputs only.

## Frozen external-reader fidelity rubric

The construction passes only if every item below holds without lowering a
threshold after the first run.

1. The code contains observations and three explicit latent levels on every
   branch, plus a global cause and `Phi`.
2. Every hierarchical transition receives precision from the same inferred
   global field; no derived depth score enters inference.
3. `q(g, x^(1:3))` and `q(Phi)` are updated iteratively and the recorded joint
   variational free energy is non-increasing within tolerance.
4. Precision updates use posterior residual moments only—never the hidden
   cause, latent states, true precision, or a reliability label.
5. `Phi` is forecast before observation, corrected afterward, and rebroadcast
   to every level; a matched local-loop ablation has equal marginal variance.
6. Binding is an exact posterior consequence of the common global cause, with
   no coherence reward, supervised binding label, or winner-take-all rule.
7. Policies are inferred from expected free energy and determine which
   observations become available; there is no scripted policy switch.
8. Under a held-out context switch, the complete model beats fixed precision,
   matched local meta-loops, no-binding inference, and random sampling on their
   relevant accuracy, calibration, adaptation, or efficiency contrasts.
9. The full model reallocates action, reverses the relevant precision forecast,
   and recovers late accuracy in at least 16/20 seeds.
10. Removing global sharing, binding, or epistemic action selectively removes
    the corresponding effect, rather than all ablations failing generically.
11. The qualitative result survives a predeclared small perturbation grid over
    observation noise, action cost, and hyper-prior variance.
12. The report states the remaining ontological boundary: computational
    sufficiency is not evidence of phenomenal consciousness or clinical effect.

## Key decisions

- Keep the state space minimal: one binary cause, three branches, three scalar
  states per branch, and one nine-component precision field.
- Use exact enumeration for the global cause and analytic Gaussian updates for
  states; use a Gaussian variational/Laplace update for `Phi`.
- Distinguish current-state variational free energy from policy expected free
  energy while recording their sum as the active-inference objective.
- Treat failure as informative. If the unified model cannot beat a relevant
  matched ablation without supervision or fragile parameters, report that the
  current formal commitments are insufficient.

## Open question

The paper does not uniquely specify the transition law for `Phi` or a policy
factor. Success can establish a faithful minimal realization of the stated
architecture, not that this realization is *the* uniquely correct Beautiful
Loop model.

## Next step

Implement experiment 33 and iterate its inference mechanics—not its frozen
rubric—until the model either passes or exposes a principled insufficiency.
