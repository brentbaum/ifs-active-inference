# Experiment 47: protector trust, and where the hope merchant's promise has to land

**Status:** Standalone write-up of Experiment 47 (sufficiency-bet round, 2026-07-24). Full record: `projects/emergence-suite/continuous/results/protector_trust/report.md`. Frozen verdict 4/5 PASS; the (d) failure and its resolution are the subject of the second half.

## What was built

The experiment models a single protector as an active-inference agent deciding whether to permit contact with the part it guards. The protector is the four-channel bundle from the earlier suite (self, world, policy, outcome) extended with three learned forecasts, each a probability updated by Bayesian likelihood ratios as evidence arrives:

1. **Outcome forecast** — if contact happens, will the system tolerate it or flood?
2. **Co-protection forecast** — if I relax, is the rest of the system competent to carry what I've been carrying?
3. **Partner model** — a latent over what kind of policy is making the request: *instrumental* (wants access to the exile for its own purposes) or *relational* (will stay in relationship regardless of what I decide).

Trust, in this model, just *is* these three posteriors. Permission is something else: a soft expected-cost decision computed over the posteriors plus a **stakes parameter** — how much is riding on this moment — which multiplies the forecasted risk inside policy evaluation but is never allowed to touch the posteriors themselves. Concretely, the protector compares the expected cost of allowing contact (stakes × forecasted risk) against the cost of refusing (a fixed refusal cost, 0.78), through a softmax with temperature 0.20. So the architecture enforces the theoretical claim by construction: trust is what the protector has learned to expect; permission is what it decides to risk; and the two can come apart, because stakes live only in the decision.

Each world is one seeded run; paired contrasts within a world change exactly one thing, so every comparison is matched on evidence, priors, and capacity by construction. The protocol was pilot on 10 worlds, freeze all thresholds, then 20 fresh confirmatory worlds with disjoint seeds.

## The five tests

**(a) Refusal discrimination.** Two visiting partners are constructed to be observationally identical until the protector refuses — pre-refusal observations carry no type-dependent likelihood at all, so the partner posterior sits at exactly 0.5. The test: discrimination should be at chance without a refusal episode and rise only after one. Result: 0.500 without refusal, 0.988 after two refusal episodes. And the two measures dissociate as the clinical claim requires: a partner who pressures after refusal is *highly informative* (discrimination rises) while trust *falls* (−0.49); a partner who remains is equally informative and trust rises (+0.49). Refusal is the diagnostic event; what it diagnoses depends on what meets it. **Pass.**

**(b) Permission ≠ trust.** Take worlds with numerically identical posteriors and vary only stakes. If permission were a relabeled posterior, a regression of permission on the posteriors would leave nothing. It leaves a lot: adding stakes explains 96.7% of the residual variance. Same trust, different decision. **Pass.**

**(c) Transfer by inferred variable.** Deliver the *same* outcome evidence ("contact was tolerated") under two causal framings: one where it supports only a local forecast about this one situation, one where it supports a shared cause — *the system can bear this*. Then measure willingness in an untested situation. Willingness moved only under the shared-cause framing (0.037 vs. 0.000), in 20/20 worlds; the evidence label itself, held constant by construction, contributed exactly zero. Generalization tracks what the protector infers the evidence is *about*, not the evidence's surface. **Pass.**

**(d) Hope merchant.** The IFS claim: a protector's permission can shift when it is shown a possible future — exile healed, mandate unnecessary — even with no new evidence about the present. The control: that future must contain room for the protector; a future in which the protector is simply discarded should move permission less, or negatively. Implementation: the future was added as a third policy in the comparison set, carrying a hope value (0.42) plus a role value (0.20) in the role-preserving variant, or minus an obsolescence penalty (0.46) in the discard variant, with all posteriors frozen flat. Permission shifted with flat posteriors — the hope-merchant route exists — but the obsolescence variant shifted permission 0.16 against the role-preserving 0.20, failing the "at most half" criterion. The weak control was visible in the pilot and frozen unchanged rather than tuned. **Fail.**

**(e) Rupture asymmetry.** A diagnosticity parameter controls whether a failure is read as revealing partner type or as noise. With high diagnosticity, one misattunement outweighs one smooth success in 20/20 worlds; with low, in 0/20. And a repair that the old partner model cannot explain outweighs three smooth successes — the asymmetry cuts both ways under the same parameter. **Pass.**

## Why the obsolescence control had to fail

The post-freeze analysis showed the (d) failure wasn't a parameter problem. In the policy-addition form, adding any contact-enabling option to a softmax can only move probability mass toward contact. With A the weight on existing contact-enabling policies, B the weight on refusal, and w the weight of the added future:

> ΔP = wB / ((A+B)(A+B+w)) > 0, always.

The obsolescence shift is strictly positive no matter how large the penalty — the closed form matched all 20 confirmatory worlds to floating-point precision (2×10⁻¹⁶). Whether the shift lands under "half the role-preserving shift" reduces to arithmetic over three authored constants (penalty, role value, temperature). The §8 prediction — *less, or negatively* — is unreachable in this model class except by authoring it, which would prove nothing. The operationalization, not the theory, was the wrong object.

## The reoperationalization, and where bearing-absence comes from

The fix follows from asking what an offered future actually is to the protector. It is not another action on the menu. It is a *forecast of the system* — and the protector should evaluate it the way it evaluates everything: through its risk model.

So in the second form, no third policy is added and no penalty constant exists. Both futures depict the same healed exile and carry the same hope value. They differ in one place: who is in the picture. In the role-preserving future the protector is still present, so forecasted risk drops toward the healed baseline. In the obsolescence future the protector is absent — and the model has to answer *who carries the risk then*. The only honest place to route that question is the co-protection posterior **c**, the forecast the protector already maintains about whether the system can cope without it:

> r_obsolete = c · r_role + (1 − c) · r_max

If inferred competence is high, the protector's absence changes little — the forecast approaches the role-preserving one. If competence is low, its absence forecasts abandonment-level risk: permitting contact under that future means leaving the system unguarded with no one able to take over.

Run on 40 fresh worlds whose competence evidence spanned the range (posterior 0.001 to 0.998), the clinical prediction now emerges instead of being authored: the obsolescence future shifted permission *negatively* in 14 worlds and positively in 26, with an analytic crossover at c ≈ 0.26, and the sign matched the utility prediction in every world. Posteriors stayed flat throughout — this is still pure hope-merchant, no new evidence.

The crossover is the result. "The future must contain room for the protector" turns out not to be an absolute clause but a conditional one, and the condition is the protector's own co-protection belief: **a future without the protector repels permission exactly until the protector already believes the system can bear its absence.** Below the crossover, being written out of the future reads as abandonment of the system and makes contact *less* permissible than no future at all. Above it, obsolescence is tolerable — even attractive — because the forecast says the system no longer needs the mandate. Which is a formal restatement of something clinicians already do in sequence: co-protection is established first, and only then does "your job will be done" land as relief rather than threat.

The scoped conclusion, held to construction terms: within these model classes, §8's obsolescence clause requires the offered future to alter the protector's forecast of system risk, not merely to enter its option set. That is a finding about operationalization, not about people — but it is the kind that tells the theory where its own prediction lives.
