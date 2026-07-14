# Experiment 34 — binding as relational synergy

**Date:** 2026-07-14

## Question

Can the precision hyper-loop support a genuinely global inference—one whose
evidence exists only in the relation among local contents—and does the effect
disappear when the joint factor is removed without weakening local inference?

## Construction

A binary scene cause $g\in\{-1,+1\}$ constrains three binary local causes by

\[
g=z_1z_2z_3.
\]

Each $z_j$ generates a three-level Gaussian branch, and every transition
precision is inferred through the same residual-driven $\Phi$ loop used in
Experiment 33. Five percent of episodes violate the relation, providing an
explicit adversarial scope condition. Hidden global causes, local causes,
states, and true precisions are used only to generate and score episodes.

This parity construction is a minimal synergy benchmark. Marginally,
$I(g;z_j)=0$ for every branch: no local posterior, no matter how accurately
estimated, contains evidence about the scene. The information is present only
in the joint configuration. The full model enumerates the relational scene
hypotheses exactly. The control has the same cause space, Gaussian hierarchy,
observations, precision forecast, residual updates, parameter count, and
uniform local marginals, but factorizes the three local causes. Its posterior
over $g$ therefore remains at one half.

## Iteration record

The first attempt used a nonfactorized prior allowing either complete
coherence or exactly one discrepant cause. A small two-seed search suggested a
six-point advantage, but the full twenty-seed result shrank to `0.729` versus
`0.724`, with only 10/20 wins. Both agents retained essentially the same binary
decision boundary. That construction was rejected rather than tuned further.

The parity benchmark changes the causal question. It tests whether a joint
relation can carry information unavailable in any component. An identifiability
check set four observations per branch and cause amplitude `1.05`; weaker local
signals made the features themselves too noisy to test their relation.

## Exploratory results

Across twenty exploratory seeds:

| Measure | Relational model | Independent local marginals |
|---|---:|---:|
| Overall held-out accuracy | 0.722 | 0.507 |
| Relation-preserving accuracy | 0.747 | 0.506 |
| Relation-violating accuracy | 0.248 | 0.493 |
| Precision-forecast RMSE | 0.521 | 0.521 |

Because $I(g;z_j)=0$, the factorized model is at chance by construction and the
20/20 paired win count is not an empirical surprise. The informative outcomes
are the relational model's absolute accuracy, its stability across later stress
tests, and its reversal on adversarial relation violations. The identical
precision RMSE is an important negative control: the task effect comes from the
joint scene factor, not a better precision forecast.

## Interpretation

This is non-vacuous binding. The global variable does not rename a product of
locally informative likelihoods; it classifies a relational property that
cannot be read from any branch alone. Removing the relational factor removes
the information while leaving local sensing intact.

The result is still exploratory and deliberately minimal. Parity is a clean
synergy benchmark, not a realistic perceptual ontology, and the relational
form is supplied rather than learned. Sampling is fixed and there is no
structural break, so this repair does not create one end-to-end agent containing
joint binding, temporal precision recursion, and epistemic action. The next
experiment must ask whether a capacity-matched model can learn this structure
and whether the effect survives fresh seeds and perturbed relation strength.
