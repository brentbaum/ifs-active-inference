# Experiment 47: protector trust

## Design

The construction extends the Experiment 43 four-channel protector bundle (`self`, `world`, `policy`, `outcome`) and its joint conditional table with three learned forecasts: tolerated versus flooding/collapse for contact, shared system competence if protection relaxes, and a latent partner policy type (instrumental versus relational). Evidence updates these forecasts by Bayesian likelihood ratios. The public `TrustEvidence` stream is the reuse point for Experiment 49: dyadic scaffolding can shape evidence before it enters the same update function.

Permission is a soft expected-cost choice among contact-enabling and protective policies. Contact risk is computed from all three posterior forecasts; stakes multiply that risk only inside policy evaluation. Counterfactual futures are additional representable policies. Therefore permission is neither stored in nor identified with any posterior.

### Register guards

*Configural* is used only for within-bundle statistical organization. *Relational* names an interpersonal contact-policy type. Protector contact is *befriending*, not witnessing. *Organization* retains the shared §2 definition: the bundle, couplings, precisions, and field profile. *Carrier* would mean independently parameterized substrate; no carrier variable appears here. These labels and readouts were fixed before results.

### Design decisions

- One seed is one paired world. All arms within a seed share the same jitter; contrasts change only the named manipulation.
- §6.4(a)'s “observationally identical until refusal” is literal: pre-refusal observations have no type-dependent likelihood and leave both partner posteriors at `0.5`. Accuracy is posterior mass assigned to the true type. Discrimination and trust growth are separate columns; pressuring increases discrimination while decreasing relational trust.
- §6.5(b)'s “stakes-attributable permission variance” is the partial variance fraction: reduction in posterior-only regression residual sum of squares after adding the paired stakes indicator. Posterior values are identical within each stakes pair.
- §6.4(c)'s evidence label is held exactly constant (`tolerated contact`) across framings. Local framing updates only situation 1; shared-cause framing updates system competence. Transfer is permission change in untested situation 2. Because the label has zero variance by construction, its incremental regression contribution is exactly zero.
- §6.4(d)'s future is an added contact-enabling policy. The role-preserving and obsolescence variants use identical trust posteriors and evidence; only future role value differs.
- §6.4(e)'s diagnosticity is a failure-attribution log-evidence magnitude. “Asymmetry iff high” means one failure outweighs one smooth success in every high-diagnosticity world and in no low-diagnosticity world. Repair is compared with the frozen integer `k` on the same log-evidence scale.
- “Remaining” is used rather than withdrawal for the relational refusal response; the instrumental contrast is pressure. This chooses one of the spec's allowed instrumental behaviors and keeps direction of trust change unambiguous.
- The pilot exposed a weak obsolescence control at penalty `0.46`. It was retained unchanged through confirmation under the no-tuning rule.

### Capacity and matching notes

All paired contrasts use the same three posterior state variables, priors, likelihood families, evidence budget, decision temperature, and base Experiment 43 bundle. Arm (a) partner types receive identical pre-refusal streams. Arm (b) changes only stakes after inference. Arm (c) reuses the same outcome observations and changes only their graphical attribution. Arm (d) reuses one frozen posterior snapshot and changes only the policy set. Arm (e) uses the same success and repair evidence scales while changing only failure diagnosticity. This is capacity and marginal matching by construction, not an ablation that changes available evidence.


Structural audit: Experiment 43 channels match = `true`; base conditional rows normalized = `true`; stakes absent from `TrustEvidence` = `true`; permission evaluation leaves posteriors unchanged = `true`; seed blocks disjoint = `true`.

## Pilot

Ten worlds (`14701:14710`) ran before freeze.

The pilot passed (a), (b), (c), and (e), but failed (d): role-preserving shift was `0.1940` and obsolescence shift `0.1508`. The failure was frozen unchanged.

- Refusal: no-refusal accuracy `0.5000`; after two refusals `0.9878`; remaining trust growth `0.4878`; pressuring trust growth `-0.4878`.
- Permission/stakes: posterior-only residual variance explained by stakes `0.9749`; mean permission gap `0.1598`.
- Transfer: inferred-variable tracking in `10/10`; mean local/shared transfer `0.0000` / `0.0360`.
- Hope: mean role-preserving shift `0.1940`; obsolescence shift `0.1508`; maximum posterior change `0.0`.
- Rupture: high/low diagnosticity asymmetry in `10/10` and `0/10`; repair exceeded `k=3` smooth successes in `10/10`.

## Freeze log

The pilot was reviewed and the hope margin (`0.1`) and repair comparator (`k=3`) were frozen before confirmation. No threshold changed. Full rationale and the access guard are in `freeze-log.md`.

## Confirmatory results

Twenty fresh worlds (`14751:14770`) ran after freeze; the seed set is disjoint from the pilot.

- **(a) Refusal discrimination:** no-refusal accuracy `0.5000`; after two refusals `0.9878`. Pre-refusal equality held in `20/20`. Mean trust growth was `0.4878` after remaining and `-0.4878` after pressure.
- **(b) Permission ≠ trust:** adding stakes explained `96.7%` of posterior-only residual permission variance; all `20/20` stakes pairs had identical posteriors. Mean low-minus-high-stakes permission was `0.1693`.
- **(c) Transfer by inferred variable:** `20/20` worlds transferred more under shared-cause inference. Mean transfer was local `0.0000`, shared `0.0369`; evidence-label incremental variance was `0.0`.
- **(d) Hope merchant:** role-preserving mean permission shift `0.2039` against frozen margin `0.1`; obsolescence shift `0.1595`; maximum posterior change `0.0`.
- **(e) Conditional rupture asymmetry:** high diagnosticity produced asymmetry in `20/20`, low in `0/20`; repair exceeded `k=3` smooth successes in `20/20`.

### Verdict against §6.5

1. (a) `PASS` — chance ±`0.05` without refusal and ≥ `0.8` after two refusals.
2. (b) `PASS` — stakes-attributable variance ≥ `0.15` with matched posteriors.
3. (c) `PASS` — inferred-variable tracking in ≥ `16/20`, with no evidence-label increment.
4. (d) `FAIL` — role shift ≥ `0.1`, posteriors flat, obsolescence ≤ half the role shift.
5. (e) `PASS` — asymmetry iff diagnosticity high and repair > `k=3` smooth successes.

Overall frozen-criterion verdict: **one or more construction criteria failed**.

## Interpretation

The construction failed at least one frozen criterion. Specifically, the role-preserving future shifted permission with flat posteriors, but the obsolescence control also shifted it too strongly; the full hope-merchant criterion is therefore not reproduced by this implementation.

The strongest scope limitation is that the likelihoods, causal framing, policy utilities, and diagnosticity regimes are authored. The model infers posterior values and makes permission decisions from them, but it does not learn the model class or utility function. Experiment 49 may feed dyadic scaffolding through `TrustEvidence`; it must not treat the present construction as a derived clinical mechanism.

## Exploratory addendum (post-freeze; non-confirmatory)

This addendum does not alter the frozen 4/5 verdict, thresholds, confirmatory rows, or interpretation of criterion (d) as failed. The pre-addendum `summary.json` SHA-256 was `4e9e0f923d4bc411e38a845d1b83519bad9bf07b665ae4b4cb13baf41685c7c2`.

### Analytic bound for the frozen policy-addition form

Let `A > 0` be the total softmax weight of existing contact-enabling policies, `B > 0` the total weight of non-enabling policies, and `w = exp(U_new / T) > 0` the weight of an added contact-enabling future at finite decision temperature `T > 0`. Baseline permission is `P = A/(A+B)` and permission after addition is `P' = (A+w)/(A+B+w)`. Therefore:

```text
P' - P = wB / ((A+B)(A+B+w)) > 0.
```

The obsolescence shift is thus bounded below by zero and is strictly positive whenever refusal retained nonzero mass. It cannot become negative in this model class. For the two added futures, `w_obsolete / w_role = exp(-(obsolescence_penalty + protector_role_value)/T)`. With frozen constants this is `exp(-(0.46 + 0.2)/0.2) = 0.0369`. The ≤ half criterion is consequently arithmetic over the authored penalty, role value, and temperature rather than an inference result.

Re-evaluation of the 20 frozen confirmation posteriors matched the closed form to maximum absolute error `1.942890293094024e-16`. All `20/20` obsolete shifts were strictly positive; their minimum was `0.1124`.

### Risk-model operationalization

The exploratory form retains the existing allow-versus-refuse policy set. Both counterfactuals represent the same healed exile and receive the same existing hope value; neither adds a third policy. The role-preserving future removes the healed outcome hazard while retaining co-protection and partner risks. In the obsolete future, protector absence makes risk conditional on the inferred competence posterior `c`: `r_obsolete = c*r_role + (1-c)*1`, where `1` is the normalized maximal-risk endpoint. Thus high inferred competence approaches the role-preserving forecast, while low competence forecasts abandonment-level risk. The existing posterior, risk weights, stakes, refusal cost, hope value, and temperature do all the work; `obsolescence_penalty` is not read.

Forty fresh worlds (`14801:14840`) each generated four co-protection demonstrations from a seed-specific competence probability and inferred `c` through the existing likelihood. The posterior range was `0.0007`–`0.9977`. Role-preserving futures increased permission by mean `0.7637`. Obsolescence shifted permission positively in `26/40` worlds and negatively in `14/40`, with an analytic crossover at competence posterior `0.2618` (largest observed negative `0.0200`; smallest observed positive `0.3600`). The analytic utility-sign prediction matched all worlds, all policy evaluations left posteriors flat, and no exploratory path read an obsolescence penalty.

### Scoped conclusion

Within these authored model classes, §8's obsolescence clause requires the future to change the protector's forecast of system risk, not merely append another contact-enabling softmax option. Policy addition guarantees a nonnegative shift and makes the control depend on authored utility constants. The risk-model form instead produces the predicted competence-dependent crossover: room for the protector matters when inferred co-protection is weak, while obsolescence can be tolerable when the system is already expected to bear its absence. This is a finding about operationalization and model class, not about people or clinical effectiveness.
