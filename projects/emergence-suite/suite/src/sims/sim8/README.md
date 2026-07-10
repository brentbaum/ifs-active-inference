# Sim 8 — parts observe parts (EXPLORATORY)

Decision record: Brent approved mechanism 2 on substrate 1 (2026-07-10; see
projects/emergence-suite/concurrent-activation-sketch.md). Everything here is
EXPLORATORY under the sol re-review convention: mechanism iterated on the
pilot seeds, logged per iteration below; nothing is confirmatory evidence; the
run guard forbids any label but `pilot` until a frozen fresh-seed cycle exists.

## What this sim is

The missing carrier behind Sim 4's falsified descent claim (three cycles,
reviews/2026-07-10-t41c-sim4-identifying-experiment.md): the current model
class never lets a protector learn ON a live exile. Sim 8 adds concurrent
activation: soft responsibility (every cause learns and acts in proportion to
its posterior share — winner-take-all was the approximation) plus internal
observation (every cause writes evidence about every other cause, weighted by
the observed cause's activation ENTERING the trial). Formation runs in Sim 1's
frozen two-epoch world, imported read-only. Nothing directional is coded:
direction, if any, must be grown from who was active entering the
unassimilable moments.

## Iteration log (all on pilot seeds 1001-1010, all exploratory)

1. **Valence-only internal writes, absolute 0.5 aversion baseline**: coupling
   nondirectional (1/7). Diagnosis: consolidation silences only catastrophes —
   ordinary hazard rate is identical across epochs, so valence carries no
   epoch asymmetry.
2. **Severity-weighted internal writes**: unchanged. Diagnosis: at these
   coordinates the closed loop's own avoidance suppresses delivered aversive
   evidence below 50%, so NO bank crosses an absolute 0.5 line — the absolute
   baseline is wrong in a world containing avoidance.
3. **Contrastive aversion** (conditional-on-i frac minus the observer's own
   unconditional baseline, both severity-weighted): direction appears
   (fraction 0.14 -> 0.36) but root-involving pairs point backwards.
   Diagnosis: the formative spawn-trial attribution (exile active entering
   the catastrophe, newborn writes it at severity 6) is washed out by
   hundreds of ordinary co-existence trials.
4. **Unified write rule**: internal writes use the same arousal-scaled
   learning rate as personal banks (flat rate was an inconsistency, not a
   dial). The formative event now carries ~12x weight; reverse pairs drop to
   0.0 in most seeds; directional 4/7 (fraction 0.57). Remaining reversals
   (1009, 1010, partially 1007): catastrophes cluster, and a spawn already
   active entering catastrophe #2 collects blame from the root — mid-cluster
   attribution.
5. **Attribution-share blocking**: the internal bank supplies the TARGET of a
   protector's fear; the magnitude is its own aversive expectation. Block =
   protective policy share x own aversion x normalized attribution. Result:
   the full chain works — seed 1001 descends perfectly newest-to-oldest and
   the shuffle destroys it; seed 1009 (reversed coupling) descends
   OLDEST-first, i.e. the gate faithfully expresses whatever direction was
   grown. Earnable-both-ways demonstrated inside one pilot.

## State at commit

Stacks 7/10; coupling directional 4/10 (below the preregistered 8); descent
3/10; shuffle degradation 1. theory_result=null — mid-iteration, undecided,
recorded as such. The mechanism chain (world -> coupling -> gate -> ordering)
is functional; the open question is narrowed to one thing: why coupling
direction emerges in only ~half the seeds.

## Next iteration's target (preregister before running)

Mid-cluster attribution is the suspected reversal source. The theory's own
distinction: the exile's activity precedes DANGER; the protector's activity
precedes RELIEF (its policies suppress exposure). Candidate mechanisms, in
order of parsimony: (a) attribution discounts outcomes the observed cause's
own policy contributed to (actor vs bystander — uses only quantities already
in the trial log); (b) lag the attribution window past the acute cluster; (c)
weight attribution by counterfactual exposure (needs the relief bookkeeping
Sim 1 already logs). Whichever is chosen: preregister, run once, log here.

### Iteration 6 (preregistered 2026-07-10, BEFORE running)

Chosen mechanism: attribution forms from UNASSIMILABLE events only. Internal
aversive mass is weighted by (1 + excess), where excess = max(0, pe -
assimilation_capacity) — the identical quantity that gates spawning; no new
concept enters. Rationale is §4's own language: the part absorbs what cannot
be assimilated, so the attribution content IS the unassimilable event. An
expected storm (a mid-cluster catastrophe arriving after beliefs have adapted,
pe ~0.6 < capacity 1.0) is assimilated and carries no attribution — which is
precisely the mid-cluster blame the reversal seeds collect. The raw severity
multiplier and arousal-scaled rate leave the internal write rule (severity
already enters pe multiplicatively, so excess carries it by the principled
route); baseline uses the identical rule so the contrast stays
apples-to-apples. Predictions, falsifiable both ways: reversal seeds (1009,
1010, 1007) should lose their backwards attribution; if instead spawn-to-spawn
chains lose their coupling too (episode-2 events may all be assimilable once
beliefs have adapted), directional fraction will DROP and that is the honest
result. Exactly one run, logged below either way.

**Iteration 6 RESULT: prediction falsified.** Directional fell to 1/10 and
seed 1001's perfect descent was destroyed. Diagnosis: excess-gating killed the
mid-cluster blame (excess is exactly zero for assimilated events — that part
worked) AND the formative attribution, whose weight fell from ~36x (iteration
5's arousal x severity) to ~3x (1 + excess of 2), too weak against hundreds of
ordinary co-existence writes at 1x. The two effects need different scales.

### Iteration 7 (preregistered before running)

weight = 1 + internal_excess_gain x excess, internal_excess_gain = 30 — chosen
to restore the formative write to the personal banks' own formative scale
((1 + 60 x 0.44 / 5.2) x severity 6 ~ 36), documented in magic-numbers.md.
Because excess is IDENTICALLY ZERO for assimilated events, no value of the
gain can resurrect the mid-cluster blame iteration 6 killed — the constant
only restores formative dominance. Prediction: 1001's descent returns;
reversal seeds stay decoupled or flip to directional. If instead reversals
return WITH the gain, the excess mechanism is wrong, not mis-scaled, and
candidate (a) (actor-vs-bystander) is next. One run, logged either way.

**Iteration 7 RESULT: best state; prediction partially confirmed.** Coupling
4/10 directional seeds but mean directional fraction 0.67 (was 0.57), descent
4/10 with shuffle degradation 2. The marquee: seed 1004 grew a FOUR-layer
stack, 6/6 pairs directional, and descended it perfectly outside-in
(4->3->2->1, sessions 1/2/3/7); the shuffle destroys it. Seed 1001 likewise
(3/3, perfect, shuffle-destroyed). Against prediction: seeds 1009/1010 did not
decouple — their backwards attribution persisted THROUGH the excess gate
(identical 2/6 and 0/1 in iterations 6 and 7), meaning genuinely unassimilable
events landed while a spawn was carrying the moment in those worlds. The
excess mechanism is therefore necessary but not sufficient; per the
preregistration, candidate (a) actor-vs-bystander attribution is next: the
exile's activity precedes danger it cannot act on, the protector's precedes
relief its own policies produce — attribution should discount outcomes the
observed cause's own activity was managing. NOT yet implemented; next
session's first preregistration.

### Standing state after iteration 7

Stacks 7/10; coupling 4/10 directional (fraction 0.67); descent 4/10
(including one four-deep chain); shuffle degradation 2. All exploratory. The
chain world -> coupling -> gate -> ordering is proven functional and
bidirectionally honest; the single open question remains why two worlds grow
reversed attribution, with a preregistered next mechanism.

## Sol adversarial review (2026-07-10) — orchestrator verification

Review at reviews/2026-07-10-gpt56sol-sim8-review.md. Verdict REJECT of the
paper-register claim. Verified against code; findings CONFIRMED:
(1) the newborn observes its own birth trial at full rate (observer writes are
not weighted by the observer's own activation) while the reverse is zero —
the formative asymmetry's STRENGTH is a design choice, not purely time's
arrow; (2) the confidence term n/(n+4) converts exposure asymmetry
(mass-prior keeps old causes active, so later-about-earlier banks are simply
BIGGER) into directional strength even at equal conditional risk — a real
confound; (3) protective_share reads 0.94-0.99 for every cause (global argmax
policy credited to all by responsibility) — it does no role-differentiating
work; (4) the 0.01 attribution smoothing is the same order as observed
contrasts (independently caught by the explainer build); (5) sol's access=1
diagnostic arm descends 3/7 vs baseline 4/7 — much of the descent readout is
fixed-write peeling of small young banks, not the gate; only seed 1004's
order requires the gate. CONTESTED in part: the birth-boundary asymmetry is
partially time's arrow (a cause cannot be observed before existing, and the
part IS the explanation of its birth event) — but the burden is now to earn
direction with the confounds controlled, not to argue the point.

Next-iteration obligations (preregister before any run): observer writes
weighted by the observer's own current responsibility; exposure-fair aversion
(no raw n/(n+k) asymmetry); per-cause counterfactual policy preference for
protective_share; documented shrinkage replacing the 0.01; the access=1
no-gate arm as a STANDING control that descent must beat; contact writes
relative to bank mass to kill the peeling artifact. Sol's one-sentence honest
claim stands as the current register: this pilot shows a functioning
concurrent-activation testbed whose ordering behavior is not yet separable
from its own selection and exposure dynamics.

### Iterations 8-11 plan (preregistered 2026-07-10, before any run; Occam pass)

The unifying diagnosis of the sol review: every confound is an ASYMMETRIC
weighting rule. The elegant fix is removal, not addition.

- **It8 — bilinear observation**: internal write weight = observer's own
  current-trial posterior responsibility x observed cause's entering
  activation (x the excess term). One rule, no observer special case. The
  newborn's birth write is now weighted by its GROWN posterior share of the
  event it spawned to explain — earned by inference, not by append order.
  Prediction: direction survives if the newborn genuinely absorbs its birth
  event (its posterior share is high); dies if not — either is the result.
- **It9 — shrinkage-to-baseline aversion, normalization removed**: aversion =
  contrast from a bank smoothed toward the observer's own baseline at fixed
  pseudo-count k (equal risks read ZERO contrast at any exposure — kills the
  n/(n+k) exposure confound). Blocking uses ABSOLUTE aversion x own fear; the
  attribution normalization layer and its 0.01 smoothing are deleted.
- **It10 — grown protective preference**: protective_share replaced by each
  cause's counterfactual own-policy argmax (what would I do, from my own
  banks) — a real role readout, not global-action bookkeeping.
- **It11 — peeling-proof therapy**: contact writes proportional to target
  bank mass (relative, not fixed count), and the no-gate (access=1) arm runs
  as a STANDING control inside the sim; S8.descent only counts seeds where
  the baseline descends AND the no-gate arm does not.

One run per iteration, logged honestly below, exploratory throughout.

### Iterations 8-11 results (one run each, logged 2026-07-10)

- **It8 (bilinear observation)**: coupling ROSE to 5/10 directional (fraction
  0.69), descent 4/10, shuffle degradation 3 — removing sol's fatal-1
  confound made the result stronger. The newborn's formative write survives
  being weighted by its own grown posterior share of the event it spawned to
  explain: direction is earned at the birth event by inference, not by
  append order.
- **It9 (shrinkage-to-baseline aversion; normalization + 0.01 deleted)**:
  coupling unchanged (readout is now exposure-fair); descent fell to 3 with
  zero shuffle degradation — the un-normalized gate (raw contrasts ~0.007-
  0.04) was too weak to carry ordering, which reverted to bank dynamics.
  Logged as the honest cost of deleting the laundering layer.
- **It10 (counterfactual protective preference)**: role readout now grown
  (softmax over each cause's own outcome banks, sharpness 4); metrics
  unchanged pending gate magnitude.
- **It11 (mass-relative contact writes, contact_fraction 0.05; block_gain 12
  = ~1/(2 x observed max contrast 0.039), pilot-scale-derived; STANDING
  no-gate control)**: descent 4/10, shuffle degradation 3, no-gate arm passes
  3 — **gate_earned = 1/7** (seed 1001: descends with the gate, fails
  without, shuffle destroys it). Two-cause seeds descend gate-free because
  the catastrophe-born spawn's own aversive fraction orders selection;
  that is initial-condition ordering, not coupling. Seed 1004's four-layer
  order muddles at strong gating (root gated to session 17, but 2 before 3).

### Honest standing after the Occam pass

The architecture now satisfies every sol obligation: bilinear symmetric
observation, exposure-fair contrast, grown roles, no normalization layer,
mass-relative therapy, and a standing no-gate control inside the metric.
Correspondingly the result shrank to its unconfounded core: coupling
directional in 5/10 seeds, and exactly ONE seed whose descent is carried by
grown coupling alone. That is the true current size of the descent result in
this model class — smaller and real. Next candidates (preregister first):
richer worlds (more episodes -> deeper stacks and more formative events),
and the actor-vs-bystander discount for the reversal seeds (1009 unchanged
through every iteration).
