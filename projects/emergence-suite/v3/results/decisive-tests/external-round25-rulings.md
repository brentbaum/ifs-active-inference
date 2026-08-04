# External round-25 rulings (GPT-5.6 Pro, verbatim; pasted by Brent 2026-08-04)

Review of the evaluator's proposed decisive tests for protector
trust/permission, protective descent, and identity revision. Brent's
execution instruction: "please design and run." Full verbatim text below;
execution plan in the registered-predictions and design-freeze documents in
this directory.

---

Overall

The proposed tests are pointed in the right direction. The strongest ideas are:
1. permission revocation and refusal as information-seeking;
2. unscripted protective descent;
3. identity-sharing versus cue-similarity generalization.
Those are substantially more decisive than simply demonstrating the existing mechanism again.

I would tighten several claims, though. The draft occasionally slides from "the organism exhibited this trajectory" to "the underlying construct has been established." The next tests should explicitly distinguish:
- posterior inference from an authored state update;
- policy selection from a scripted therapy protocol;
- relational-state inference from contact-specific outcome learning;
- identity-mediated transfer from ordinary stimulus generalization.

1. Protector trust and permission

What is already established: discrimination between contingent and noncontingent relational support; effects of partner reliability on protection/access; stakes changing policy without changing the scientific posterior; policy-derived access in the composed organism; the V3.7 finding that partner-state inference and contact prediction are separable capacities.

It does not yet fully establish that "permission" itself is a continuously updated, partial, revocable posterior. Permission may currently be a policy probability or expected-cost consequence rather than a latent belief. That distinction matters.

Phrase the open claim as: Permission is the probability of selecting access-permitting policies under current partner, efficacy, outcome, and stakes posteriors; it should therefore be graded and reversibly responsive to new evidence. That is cleaner than treating permission as another psychological object.

Best computational tests:

A. Permission decomposition. Before testing revocation, prove what drives permission. Run a factorial intervention on: partner reliability posterior; contact-response posterior; co-protection efficacy; predicted vulnerable-mode outcome; stakes. For each intervention, recompute the policy posterior while clamping the other scientific posteriors. Required output: q(pi_permit) and its change under each intervention. This establishes that permission is actually derived from the claimed beliefs rather than from an indirect protocol branch. A strong falsifier: permission changes materially when all claimed inputs are clamped. That would expose an authored or hidden route.

B. Co-protection versus mere safety. The suggested 2x2 is excellent, but "co-protection present while safety absent" needs careful interpretation. Co-protection should mean evidence that another agent will share responsibility under future danger, not simply a comforting signal. Primary prediction: immediate access may respond to current safety; durable permission under a later danger probe should depend more strongly on learned co-protection. This creates a better distinction than merely looking for a main effect.

C. Refusal as an epistemic policy. Give the system a choice between: accepting a request; refusing; requesting clarification; withdrawing. Construct worlds where refusal is: (1) highly informative about the partner's policy; (2) weakly informative; (3) costly but informative; (4) safe but uninformative. Measure EIG(refuse) = I(L, theta_contact; O_partner | do(refuse)) and the posterior probability of refusal. The decisive prediction is not merely that refusal occurs. It is: refusal probability increases with the expected information it provides, holding predicted immediate safety and refusal cost constant. That would support "refusal as experiment." If refusal merely follows danger or cost, the epistemic interpretation fails.

D. Revocation asymmetry. Useful but underspecified as drafted. "Permission retracts faster than it accrued" could result from: a likelihood asymmetry; a volatile partner model; asymmetric preferences; a floor/ceiling effect; the violation being more diagnostic than the earlier successes. The test should manipulate diagnosticity directly. Use matched evidence packets with known log Bayes factors: repeated weak evidence supporting reliability; one violation with equal total BF against reliability; one violation with larger BF; a surprising but nondiagnostic bad outcome. Then compare permission changes after controlling for total evidence. A genuine rupture-asymmetry result: equal-and-opposite evidence causes a larger policy change when the partner model predicts failures to be more diagnostic, and the asymmetry disappears when that model is made symmetric. Without that control, "fast revocation" is not theoretically localized.

Human validation: transcript coding alone can show ordering and association, but cannot establish that refusal is epistemic or permission is a posterior. A reasonable observational study codes, at event level: protector concern; evidence type offered; explicit appreciation; present-day orientation; co-protection commitment; access granted; access later revoked; subsequent rupture or failed contact. Model P(access_{t+1}) and P(revocation_{t+1}) with session and client random effects. The more decisive human study uses standardized therapist responses following protector concern, randomized or quasi-randomized among: reassurance; appreciation; present-day evidence; explicit co-protection; clarification/refusal-respecting response.

2. Protective descent

The key open issue: V2.8 showed that descent can occur in a composed trajectory, but not that the sequence is autonomously selected. This is probably the highest-value remaining computational test. However, "give the organism an open action menu" needs a clearer agent architecture. In therapy there are at least two policy makers: the internal system choosing protection, contact, or access; the therapist or guiding process choosing interventions. If one agent controls both sides, descent may become artificially easy.

A. A two-agent or controller-system policy game. Let the therapeutic controller choose: inquire; appreciate; offer present orientation; offer co-protection; request access; contact vulnerable material; retreat. Let the internal system choose: permit; refuse; intensify protection; withdraw; allow partial contact; allow full contact. The controller cannot directly set access or descent. It chooses observations/interventions; the internal system selects its own policy. Then ask whether the coupled policy process generates protector contact -> trust change -> permission -> vulnerable contact without that sequence being encoded as a transition rule. This is stronger than a single-agent menu.

B. Competing strategies. Include viable alternatives: direct-to-vulnerable contact; repeated reassurance; repeated exposure; protector appreciation; present-day evidence; co-protection; retreat. The test is meaningful only if at least some non-IFS strategies win in appropriate worlds. Otherwise the action space has simply been authored so that descent is optimal.

C. Deadlock boundary mapping. Use a causal factorial rather than serially removing whichever module seems important. Candidate factors: persistent partner-state inference; contact-response learning; co-protection efficacy; protector appreciation evidence; future-outcome horizon; stakes; registration channel. Measure: probability of eventual contact; first-contact time; policy entropy; protector pressure; durable access following a return probe. The central result should be a minimal sufficient set, not just a list of lesions that reduce descent. Example: partner reliability is insufficient without contact-response learning; contact-response learning is insufficient without co-protection; their interaction unlocks descent. That would integrate the V3.7 capacity findings directly.

D. Bypass/backlash test. Compare: (1) controller requests contact only after protector-selected permission; (2) controller requests contact while permission probability is low; (3) controller forces contact; (4) controller retreats after refusal. Primary prediction: forced or premature contact causes later protector pressure, reduced contact probability, or stronger exclusion policies; respecting refusal should preserve or increase future information-seeking and access. This gives "protectors should not be bypassed" a concrete computational meaning.

Human validation: the strongest observational prediction is not simply "more protector trust precedes exile contact" — that could be tautological if coders infer trust from the fact that access follows. Code trust evidence and access independently: protector-specific concerns; partner/therapist reliability evidence; contact-contingency evidence; explicit permission; degree of vulnerable contact; subsequent backlash. Then test whether independent trust markers prospectively predict access above: therapist pressure; session number; general alliance; current distress; prior access history. A within-client event analysis is much stronger than comparing clients.

3. Identity revision as posterior inference

First perform a code-level construct audit. Do not relabel the row yet merely because V3 calls something a posterior. The audit should answer:
1. What exact random variable is "identity"?
2. Is its posterior computed through ordinary likelihood and marginalization?
3. Does any protocol directly assign or increment it?
4. Does "root evidence uptake" modify the identity posterior through the same graph used outside therapy?
5. Are downstream world/action/outcome effects recalculated from that posterior, or written separately?
6. Is transfer obtained by shared parent structure, or by an explicit transfer function?
Three possible standings: posterior computed but therapy evidence route authored; therapy evidence updates identity by ordinary inference, but transfer authored; identity revision and transfer both arise from ordinary inference over shared structure. Only the third licenses the strongest ledger upgrade.

A. Identity-first ordering. "Identity moves first" must not be defined through differently scaled thresholds. Use comparable event definitions based on posterior evidence: t_G = inf{t: log BF_G(t) >= b_G}, t_Y = inf{t: log BF_Y(t) >= b_Y}. Select b_G, b_Y through prior-predictive calibration so they represent equivalent evidential strength, not arbitrary probability cutoffs. Compare: identity-first; outcome-first; simultaneous; no crossing. Include worlds where ordinary exposure should rationally produce outcome-first revision. Otherwise identity-first ordering is built into the evidence.

B. Root-mediated transfer. Treat one cue and measure untreated cues. The key lesion must preserve: treated-cue evidence; cue-specific learning; identity inference; outcome observation count. It removes only the shared identity-to-cue dependency. Predicted pattern: full shared root — treated revises, untreated identity-sharing cues revise; root-sharing lesion — treated revises, untreated do not; cue-local evidence removed — neither revises. One of the cleanest causal tests available.

C. Identity-sharing versus cue-similarity generalization. Probably the strongest overall test. Create cues on two orthogonal dimensions: perceptual similarity; identity-parent sharing. 2x2: (no,no), (yes,no), (no,yes), (yes,yes). Treat one cue. Predictions: an identity-mediated model transfers primarily by shared identity parent; an associative/exposure comparator transfers primarily by perceptual similarity; a hybrid may show both gradients. This gives a true model comparison rather than merely another positive transfer result.

D. Real-danger negative control. The current identity weakness in real_danger_adaptive makes this especially important. The identity model should not infer identity pathology merely because danger is persistent and action is protective. Test: persistent external danger; recurrent identity-coupled threat; mixed external and identity-generated danger; acute transient danger. A good identity posterior should distinguish them while preserving accurate outcome prediction. The V3.7 result showed that adding exogenous danger can help identity attribution while harming outcome prediction, so this is genuinely unresolved rather than a box already checked.

Human validation: the identity-sharing versus cue-similarity design is also the best human study. Independently measure: cue similarity; perceived common identity meaning; expectancy of threat; self-identification or identity belief. Then examine generalization after a targeted therapeutic change. The prediction: changes generalize more strongly to situations sharing the revised identity meaning than to equally perceptually similar situations lacking that meaning. Temporal ordering can be tested with dense within-session ratings, but self-report timing alone will be noisy.

What I would prioritize

Not one giant registered cycle — three different levels of question.

Study 1 — Identity-mediated generalization: code audit; identity-first ordering; shared-root lesion; identity-sharing x cue-similarity factorial; real-danger control. Could materially upgrade a central C3 claim.

Study 2 — Autonomous protective descent: separate controller and internal-system policies; open action menu; free-policy sequence; deadlock factorial; bypass/backlash arms. Determines whether "descent" is genuinely derived or remains protocol-carried.

Study 3 — Permission dynamics: decomposition/clamp proof; co-protection x safety; refusal information gain; diagnosticity-controlled revocation. Sharpens the trust/permission claim beyond C-V36B.

Ledger recommendations now (interim standings):
- Protector trust: Supported under sealed composed challenge.
- Policy-derived access/permission: Supported construction under sealed composed challenge; graded/revocable-posterior interpretation untested.
- Protective descent: Supported in composed protocol; autonomous policy selection untested.
- Identity as posterior inference: Pending code-level route audit.
- Identity-mediated transfer: Supported construction, but derived-vs-authored status requires audit.
- Identity-first temporal ordering: Untested in the compressed organism.
- Refusal as epistemic action: Untested.
- Rupture/revocation asymmetry: Untested.

The most important correction: do not treat "trust," "permission," "descent," and "identity revision" as unitary claims. Each contains a supported behavioral result and a stronger mechanistic interpretation that remains open. That separation will make Appendix A more credible and make the decisive-tests section much clearer.
