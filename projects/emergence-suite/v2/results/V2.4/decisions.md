# V2.4 decisions

- Five candidates were implemented as complete replaceable initial,
  transition, parameter-sharing, and context process bundles. No family is
  an edge toggle.
- Cue, context-marker, and root observations use one candidate-common
  normalized emission interface.
- Context-split transition uncertainty is integrated by exact transition-
  count sufficient states. Change-point hazard uncertainty includes every
  possible onset and the no-change path.
- The fixed GW and CL transition matrices have degenerate scale posteriors;
  the frozen parameter block declares no nondegenerate scale prior for them.
- Experiments 44/44b supplied design lessons only: preserve selectivity
  marginals, charge complexity, and transport training coordinates. No old
  source, likelihood, parameter, or result was ported.
- The V2.3.3 qualified bank was not reached because Gate 2 failed.
- The original summed-class Brier result is retained, with the inherited
  mean-class scoring correction documented separately. It does not rescue
  the failed recovery diagonal.
- C-V24 remained sealed and no escrow seed was accessed.
