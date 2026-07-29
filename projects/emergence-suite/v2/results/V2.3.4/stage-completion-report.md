# V2.3.4 stage completion report

Status: **ALL GATES 1-5 PASS**

V2.3.4 implements counterfactual action attribution with exact danger,
efficacy-existence, efficacy-magnitude, prevention, outcome, and relief
semantics. Action is intervention-only. Relief is policy-only. The scientific
claim supported by the construction is that an agent can distinguish low
danger from danger successfully prevented by action without treating mere
nonoccurrence as positive threat evidence.

## Gate outcomes

- Gate 1: all ten semantic and independent-enumeration proofs passed. Masked
  observations had BF exactly one; the irrelevant spike, intervention
  separation, relief separation, confounding, and forced-probe proofs all met
  `1e-10`.
- Gate 2: recovery passed. Efficacy-existence accuracy was `0.992`, exact-zero
  accuracy `0.992366`, Brier `0.007025`, ECE `0.003495`,
  context-efficacy accuracy `0.875`, efficacy MAE `0.041781`, danger MAE
  `0.010905`, and parameter coverage `0.973333`. Pure-avoidance false
  certainty was `0.011333`; joint coverage was `0.958667`. Forced probes
  reduced median danger-efficacy posterior correlation by `0.680936`.
- Gate 3: all eleven assays passed. Full protection preserved threat by
  `0.399921`; partial protection restored corrective learning by `0.393772`.
  Forced probes reduced confounding by `0.395173 [0.387682, 0.402664]` and
  revised threat by `0.215516 [0.208353, 0.222679]`. Adaptive-threat recovery
  was `0.962222`, context-efficacy accuracy `0.805556`, and all exact
  separation identities were within tolerance.
- Gate 4: all seven lesions passed their target disappearance and survival
  mappings. Forced visibility restored correction by
  `0.302446 [0.298874, 0.306019]`; context specificity changed the targeted
  efficacy readout by `0.760589 [0.753667, 0.767510]`.
- Gate 5: cumulative regression, both constitutions, shared manifest-chain
  verification, and every robustness cell passed. Masking added truth error
  `0.067141 [0.062858, 0.071423]`; reduced precision added
  `0.033603 [0.030735, 0.036470]`; context classification was `0.793`; the
  low-probe cell still reduced confounding by
  `0.393812 [0.388750, 0.398875]`.

The final fast suite passed 23/23 modules. Escrow `2040000:2041999` was not
accessed.

Named finite-information bounds: formation `3.801426508560692`; V2.4 common
emissions `6.704414354964107`; V2.5a configural `6.084736253211209`;
V2.5a marginal accounting `6.704414354964107`; V2.5b
`11.302393144606405`; V2.6a relational `6.9920964274158885`; V2.6a root
`2.9444389791664394`; V2.3.4 `11.675460894331877`, with implied binary
change bound `0.9941860465116279`.
