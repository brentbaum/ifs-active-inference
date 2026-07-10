# Sim 3 Phase 4 Step A: De-authoring Pilot

This module implements T4.2 Step A. It may run only seeds 1001–1010 into
`runs/sim3/pilot/` until the orchestrator freezes the implementation and criteria.

## Architecture comparison

H1 and H2 receive the same cue stream, relational observations, outcome stream,
learning rates (including the shared pilot-tuned self rate), feature-overlap messages, policy equation, and self → threat →
policy micro-step clock. Both self and threat banks learn. Their one substantive
difference is conditioning direction:

- H1: relational evidence updates self at micro-step 1; threat conditions on
  self at micro-step 2.
- H2: self conditions on the prior threat message at micro-step 1; the same
  relational evidence updates threat at micro-step 2.

Policy is micro-step 3 in both models and reads both inferred states. First
passage uses these shared micro-step numbers directly. There are no architecture
labels or offsets in the metric. Equal timestamps are ties and never satisfy the
strict cascade test.

Training fit is the mean online outcome log likelihood on learned training-cue
trials. A difference above 0.05 nats/trial is a hard stop. Out-of-sample model
comparison uses subsequent training-cue trials with all banks frozen.

## Learned root association

Each cue has a world-level probability of co-occurring with root-1 versus root-2
context during 48 pre-training observations. The agent starts with symmetric
Dirichlet(1,1) counts and learns `P(root | cue)` from those observations. World
rates generate data only. They never enter inference or transfer metrics.

The transfer figure and gradient metrics use the association measured from each
agent's own `cue_root_banks`. Shared self evidence is read and written through
those learned posterior weights. `probe_metrics.csv` exposes both Dirichlet
counts, the posterior association, local/generalized threat readouts, and contact
for every seed × condition × cue so the analysis can be independently recomputed.

## Perceptual generalization and A3.2

Cue-local threat evidence is also available to other cues at inference, weighted
by feature overlap and the common gain 0.45. This is conventional stimulus
generalization: it changes the target cue's generalized threat prior but does not
write into the target threat bank.

A3.2 is two-sided. The perceptually near, root-poor `structural_confound` must
show positive threat-level generalization without a write to its local bank. Separately, the
predeclared low-perceptual, root-associated `cue_3` must exceed that perceptual
baseline, and contact must track learned root association after controlling for
perceptual similarity.
