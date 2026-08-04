# External round-28 rulings (GPT-5.6 Pro, verbatim; pasted by Brent 2026-08-04)

Review of the T-CAP1 proposal (triggered capture as model-relative precision
filtering). Ruling: PROCEED TO DESIGN with ten required amendments. Full
verbatim text preserved below.

---

1. Overall ruling: pursue it, but revise the construct before registration.
This is a high-value extension targeting a real gap: the existing work
represents captured and context-held precision profiles, but has not derived
the rapid transition from cue activation into a self-reinforcing captured
regime. The proposed feedback loop is plausible and aligned, but three
aspects need correction: (1) the posterior may not directly rewrite its own
same-step likelihood; (2) "transparency" needs an exact probabilistic
meaning; (3) the proposed mutual-information filtering estimand does not
cleanly measure attenuation.

Revised core (binding): "Capture is a sequential feedback loop in which the
current bundle posterior selects a channel-precision policy for the next
inferential cycle. When that endogenous precision policy is not represented
in the higher-level model, evidence is evaluated as though the selection and
attenuation were exogenous, producing miscalibrated self-confirmation. When
the policy is represented, inference conditions on the filter that generated
the evidence, limiting the feedback."

2. Main formal correction: make the loop SEQUENTIAL, one-cycle delay:
q_t(B) -> A^Phi_{t+1} -> Lambda_{t+1} -> O_{t+1} -> q_{t+1}(B).
No same-update circular likelihood. Candidate allocation policy:
q(A^Phi_{t+1}=a) proportional to exp[beta_Phi * E_{q_t(B)} U_Phi(a,B)];
allocation changes the observation model p(O_{t+1} | X_{t+1}, Lambda_{t+1}).
Connects to the established slow loop (bundle-driven policies determine
delivered observations).

3. Transparency defined exactly as two inference architectures over the SAME
generated stream. Transparent: q_tr(B_{t+1}) prop p(B) p(O_{t+1} | B,
Lambda-bar) — inference assumes baseline reliability while the data were
generated under Lambda_{t+1}. Opaque/represented: joint inference over
(B, Lambda) with p(Lambda | A^Phi, B), or metacognitive observation of the
allocation. "In the transparent regime, inference mistakes filter-shaped
evidence for unfiltered evidence. In the opaque regime, inference conditions
on the filter that shaped it." LIMITATION (binding design requirement):
representing the filter cannot recover never-sampled information; the
opaque condition needs at least one of partial disconfirming-channel access,
a metacognitive allocation observation, a prior over the reliability state,
or occasional candidate-common calibration observations.

4. "Rational per-model" retained but narrowed. Binding wording: "The
sampling policy is rational under the bundle model; capture arises because
the system fails to represent how that model has shaped the evidence
subsequently used to confirm it." Never: "the captured posterior remains
fully rational."

5. CAP-A approved as primary assay. Cue SWEEP (stepwise up, frozen holds,
stepwise down); hysteresis area H = integral of [q_down(B;c) -
q_up(B;c)]_+ dc; report capture-on threshold, release threshold,
posterior after full withdrawal, recovery time, fraction of worlds with two
stable fixed points, sensitivity to initial posterior. CAPTURE DEFINITION
requires ALL of: abrupt transition/strong nonlinear gain; material
elevation after withdrawal; release threshold below capture threshold;
persistence without further bundle-congruent external evidence;
disappearance when bundle-to-precision coupling is severed. NOT q(B)>0.9.
CRITICAL COMPARATOR: matched high-persistence bundle with no precision
feedback — feedback account passes only if hysteresis exceeds it.

6. CAP-B: MI estimand REPLACED by three direct quantities: (6.1) delivered
per-channel effective precision lambda_eff; (6.2) counterfactual evidence
influence of a disconfirming token (logit-difference vs masked); (6.3)
selection-aware vs selection-naive log Bayes factors (computed under
Lambda_t vs Lambda-bar), whose systematic divergence is the filtering
signature. STRONG FALSIFIER: hysteresis survives candidate-common or
lesioned allocation — filtering is not the cause.

7. CAP-C: "no hysteresis in accurate danger" is TOO STRONG. The correct
distinction is CALIBRATION to the danger process. Five matched world
classes: obsolete bundle; continuing danger; danger ended with reliable
safety evidence; intermittent; ambiguous. Miscalibration M_t = q_t(danger
or bundle active) - p_t^oracle(danger active); capture is persistent
POSITIVE M_t, not persistent threat probability. Urgency in continuing
danger is never counted as pathological capture.

8. CAP-D witnessing: the represented condition may differ ONLY in access to
the allocation state/meta-observation. Witnessing must not lower bundle
precision, raise context precision, cap the posterior, alter transition
persistence, or inject a recovery policy. Decisive pattern: activation
high, allocation represented, selection-naive overconfidence falls,
disconfirming influence retained/regained, hysteresis area falls. Include a
CALM COMPARATOR (lower all first-order precisions without representing the
filter): calm may reduce peak activation; only representation removes
hysteresis while preserving channel availability. Distinguishes quiet from
depth.

9. CAP-E: interaction summary, not a separate mechanism. Cue intensity x
filter observability surface; trajectory classes: no activation; reminder
(excursion with recovery); triggered capture (hysteretic persistence);
accurate urgency. Estimand: cue threshold per class;
c*_capture,transparent < c*_capture,represented, possibly no capture
threshold in range for well-calibrated represented systems. The threshold
must be a READOUT of dynamics, never authored.

10. Minimum model addition: TWO explicit productions, not one coupling:
(10.1) bundle-to-allocation policy p(A^Phi_{t+1} | q_t(B), C_t) — lives in
the inference/control algorithm, analogous to policy selection; (10.2)
allocation observability p(O^Phi_{t+1} | A^Phi_{t+1}, D_t) with D_t
controlling metacognitive access (equivalently model classes with/without
Lambda_t). Preferred organism: T-CAP1 VARIANT — v3.6 stays frozen — one
bundle, bundle-dependent precision policy, five existing channel types,
transparent vs represented inference, no partner/protector/whole-therapy
machinery unless needed, exact or bounded inference, common world
generator. A focused dynamical study, not another full V3 stage.

11. REQUIRED CONTROLS: (1) no feedback (candidate-common allocation); (2)
feedback represented (same allocation/observations, only the inference
model knows); (3) random allocation (equal magnitude, independent of
posterior); (4) sign-reversed allocation (expect negative feedback, faster
recovery); (5) matched persistence (sticky state without feedback); (6)
full-information replay (unfiltered stream to both architectures —
posteriors must agree, localizing the difference to filtering); (7)
filter-awareness only (representation without added context evidence — may
improve calibration without full recovery; informative either way).

12. REGISTRATION STYLE: no narrow numerical intervals before a public
dynamics census. Directional predictions, exact identities, ROPEs,
qualitative bifurcation fingerprints, falsifiers. Primary predictions:
feedback necessity (transparent hysteresis > no-feedback and
random-feedback); transparency interaction (represented < transparent under
identical generated streams); filtering mechanism (counterfactual
disconfirming influence decreases with activation only under
bundle-dependent allocation); activation-capture dissociation (represented
runs can peak high without persistent hysteresis); real-danger calibration
(urgency retained during danger under both regimes; excess persistence
after danger ends greater under transparent); witnessing identity
(representation changes no raw observation, no intervention, no allocation
policy). Exact identities: same canonical world and raw evidence across
transparency arms; same allocation across transparency arms; allocation
lesion removes the hysteresis contribution; full-information replay
equalizes updates; identical cue-withdrawal timing; no posterior clamp; no
bundle-transition modification. Falsifiers: proposal's plus —
matched-persistence reproduces the full signature; awareness works only by
changing the generated allocation; filtering metric changes without
posterior-dynamics change; capture with feedback severed; architectures
differ on full-information replay; accurate danger systematically
underweighted in the represented condition.

13. STAGE SEQUENCE: Stage 0 exact semantic proof on an enumerable
two-channel two-state dummy (generator normalization; transparent
likelihood; represented likelihood; identical generated stream;
one-cycle-delay identity; selection-aware BF; full-information replay
identity; no within-slice posterior feedback). Stage 1 DYNAMICS CENSUS on
public seeds only (coupling strength x cue intensity x allocation
persistence x bundle transition persistence x meta-observation
reliability); do not pick one successful point — freeze a parameter PANEL
spanning no-hysteresis, near-boundary, and clear-hysteresis regions. Stage
2 prediction seal (CAP-A-E, controls, ROPEs, falsifiers) before any
confirmatory seed. Stage 3 one-shot confirmatory battery on paired
canonical worlds across all arms. Stage 4 sealed challenge (fresh cue
schedules, danger transitions, channel-reliability patterns through the
frozen public API; at least one world where intense activation is correct
and one where mild cue exposure generates maladaptive persistence).

14. PAPER VALUE: if it passes — "A bundle-conditioned precision policy can
create self-reinforcing capture when the policy's influence on evidence is
not represented by the higher-level model. Representing the same filter
reduces hysteresis without requiring the bundle's activation to disappear."
Supports: seeing-through-the-part's-eyes as selection-naive inference;
triggered capture as a dynamical regime; witnessing as representation
rather than suppression; urgency/capture dissociation. Does NOT prove:
human triggering is always precision feedback; all blending is hysteretic;
metacognitive awareness alone is clinically sufficient; literal biological
channel mapping. If it fails cleanly: "the established precision
architecture supports captured states but does not generate autonomous
capture transitions through model-relative filtering alone" — the oldest
ledger failure stays honest.

FINAL RULING: proceed to design with ten amendments: (1) sequential
feedback; (2) transparency = selection-aware vs selection-naive; (3)
delivered precision + counterfactual influence + aware-vs-naive log BF
instead of MI; (4) capture defined by hysteresis relative to
matched-persistence controls; (5) real-danger success = calibration, not
absence of persistence; (6) witnessing changes representation only; (7)
precision policy and observability as two explicit productions; (8) focused
T-CAP1 variant organism, frozen v3.6 untouched; (9) seal only after open
dynamics census; (10) retain all seven controls.
