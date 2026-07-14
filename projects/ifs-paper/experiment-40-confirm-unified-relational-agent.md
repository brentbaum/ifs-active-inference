# Experiment 40 — frozen confirmation of the unified relational agent

**Date:** 2026-07-14

## Frozen question

Experiment 39 was the first exploratory agent in which non-vacuous relational
binding, residual-driven inference over a global precision field, and
precision-guided action were simultaneously load-bearing. Before any fresh
outcomes were inspected, its architecture was frozen together with a
twenty-seed confirmation block, eight five-seed stress cells, and a
zero-relation negative control.

## Primary confirmation

On untouched seeds `14001:14020`, held-out scene accuracy was `0.798` for the
full agent, `0.712` for factorized replay, `0.719` for matched-budget random,
and `0.718` for the precision-blind policy. The full agent beat both primary
controls on 20/20 seeds. Its joint-binding gain was `0.086`; its active-sampling
gain was `0.079`.

The factorized arm replayed both full-agent actions in every episode and
preserved the relational prior's exact conditional local marginals. Full and
random agents each acquired exactly two branch packets. Before the context
switch the full policy selected channel 1 first in every held-out episode;
afterward it selected channel 3 first in every episode. The precision-blind
policy selected channel 3 first only `3.8%` of the time after the switch.

On relation-preserving scenes, accuracy was `0.809` full versus `0.714`
factorized. On deliberately relation-violating scenes, the direction reversed:
`0.629` full versus `0.674` factorized. This is the predicted scope boundary,
not robustness to arbitrary relation failure.

## Stress result

All eight preregistered cells retained the joint signature. They varied the
local field (`0.08`, `0.12`), relational field (`1.20`, `1.80`), observations
per selected branch (`3`, `5`), and violation rate (`0.10`), alongside a
separate baseline block. Relational gains ranged from `0.047` to `0.092` and
active-sampling gains from `0.058` to `0.102`; every cell preserved the context
reallocation and exact sample budget.

## The failed negative control

The experiment did not pass in full. Setting the relational coefficient to
zero removed the full-versus-factorized gain exactly, but the action advantage
fell to `0.007`, below the frozen `0.020` criterion, even though the full policy
still reversed its selected channel perfectly across context. This failure is
not evidence against the primary conjunction. It shows that the negative
control changed two things at once: it removed higher-order dependence and
also changed the conditional local marginals. With the remaining local signal
weakened, reliability-sensitive allocation still occurred but had little
classification value.

The appropriate repair is not to weaken the criterion. It is to sample from
the already-defined factorized distribution that matches both conditional
local marginals of the relational prior exactly, and to use factorized
inference for all arms. That removes only the joint factor while leaving the
precision environment, local evidence, action budget, and local causal signal
unchanged. This repair requires a new frozen seed block.

## Interpretation

Experiment 40 confirms the main end-to-end construction on fresh seeds and a
broad local stress grid. It does not license saying that every preregistered
criterion passed: one negative control was mismatched and failed. The
conjunction claim is therefore strongly supported, while the intended
separability claim awaits the matched-marginal repair.
