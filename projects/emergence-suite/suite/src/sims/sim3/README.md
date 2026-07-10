# Sim 3 Phase 4 Step A: De-authoring Pilot

This module implements T4.2 Step A. It may run only seeds 1001–1010 into
`runs/sim3/pilot/` until the orchestrator freezes the implementation and criteria.

## Architecture comparison

H1 and H2 receive the same cue stream, relational observations, outcome stream,
learning rates (including the shared pilot-tuned self rate), feature-overlap
messages, and policy equation. Both self and threat banks learn. Their one substantive
difference is conditioning direction:

- H1: relational evidence updates self; threat conditions on self.
- H2: self conditions on the prior threat message; the same relational evidence
  updates threat.

The model has one inference update per training trial, so first passage is logged
at the resolution the dynamics genuinely have: the integer training-trial index.
This is design (a), trial-resolution measurement. The sequential-inference design
(b) was rejected because the model has no iterative message-passing loop; adding
iteration labels without updating beliefs would recreate the audited defect.
Crossings on the same trial are ties and never satisfy the strict
`self < threat < policy` cascade test. Complete non-strict orderings and incomplete
crossing triples are failures. Pilot output reports earned, tied, and failed counts
separately for H1 witnessing, H1 exposure, and H2 witnessing.

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

## Criteria amendment (Step B, orchestrator, 2026-07-10 — pre-confirmatory)

The preregistered three-way strict cascade (self < threat < policy at trial resolution) is
structurally unearnable in this model: `policy_probs` is a deterministic softmax over the
CURRENT q_self/q_threat, with no independent policy state, so the policy crossing co-occurs
with the threat crossing by construction (pilot: 10/10 same-trial). The three-way criterion
and the tie-count adversarial are RETAINED and remain falsified for the record. The amended
evidential claim is the two-way ordering the model can actually resolve: identity-level
revision strictly precedes threat-level revision (S3.cascade.two_way_*), with exposure and
reversed-root controls. Pilot: witnessing 10/10, exposure 0/10, H2 0/10. Metric addition
(self_before_threat_count, threat_policy_same_trial_count) touched summary bookkeeping only;
no dynamics changed. Confirmatory runs on orchestrator seeds 3001-3020 against the freeze.
