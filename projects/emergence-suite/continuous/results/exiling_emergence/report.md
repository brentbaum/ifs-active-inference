# Experiment 48: exiling emergence

## Design

The vulnerable part reuses the Experiment 43 four-channel bundle (`self`, `world`, `policy`, `outcome`) and joint conditional table. It adds one mutable relational prior: the probability of *alone with this*. Across 64 episodes the part generates contact attempts at a fixed base rate. A suppressed attempt reaches the vulnerable bundle only when the registration channel is open; if registered, it is Bayesian evidence for rejection.

Four protective policies compete: attentional/relational exclusion, hypervigilant monitoring, internal attack, and suppression–flooding oscillation. A policy's comparison score is `direct cost + failure cost × (1 − reliability)`. Each seed instantiates four matched regimes, one making each policy cheap and reliable. The validation label is used only by world construction and scoring; `select_policy` receives a vector of policy objects and returns the minimum expected-cost policy.

The public `register_contact!` function is the Experiment 49 extension point. A future protector gate can determine whether an attempted contact is suppressed and whether it reaches registration, while retaining the same vulnerable-bundle update.

### Register guards

*Configural* is reserved for within-bundle statistical organization. *Relational* refers only to interpersonal exclusion and the *alone with this* prior. *Witnessing* would name a context-held encounter with the vulnerable part; this protective policy comparison is not called witnessing. Protector contact is *befriending*. *Organization* is the fixed four-element bundle, couplings, precisions, and field profile. *Carrier* is independently parameterized substrate; none is modeled. These uses were fixed before confirmation.

### Design decisions

- The spec does not say whether the 20-world policy count should allocate worlds among four regimes or test every regime in every world. Testing four matched regimes per seed preserves the literal denominator of 20 for exclusion-favorable and competitor-favorable comparisons and lets every alternative face the same 20 fresh worlds.
- “Where a competitor is [cheapest-reliable]” is operationalized conservatively at the world level: a world counts against exclusion if exclusion wins **any** of its three competitor-favorable comparisons.
- “Cheapest-reliable” is represented by the expected-cost score rather than a two-stage eligibility rule. Reliability enters continuously through expected failure cost.
- Policy selection is deterministic conditional on a world's authored costs and reliabilities. World stochasticity is in those parameters and the contact stream, not in an extra decision-noise term.
- Starvation and confirmation use the exclusion-favorable comparison's selected policy. If exclusion failed to emerge there, attempts would not be marked suppressed and the consequence criteria would honestly fail.
- Registration on, off, and ablated runs use the identical selected policy, initial prior, episode count, and pre-generated Boolean contact stream. The ablation is therefore marginally matched; it removes only representation of suppression as rejection.
- Static is `maxₜ|Δpriorₜ| ≤ 1.0e-12` within each world, frozen after the pilot. Strengthening is endpoint `Δprior > 1.0e-12`; no post-pilot effect-size margin was introduced.
- Both consequence regimes are paired within every world rather than assigned to different world subsets. Thus both are realized across the block and separated by the registration toggle alone.

### Wiring note: why exclusion is not authored

World construction writes `direct_cost` and `reliability` into four `ProtectivePolicy` records. `policy_expected_cost` combines those fields with the common failure cost. `select_policy` calls `argmin` on the four resulting scores. Its signature has no regime, intended-policy, or registration argument; `ProtectivePolicy` has no such field. No branch in selection reads the favorable-world label. The label is retained outside the selector only to verify whether the emergent winner tracks the authored cost structure.


Structural audit: Experiment 43 channels match = `true`; base conditional rows normalized = `true`; closed registration is a no-update path = `true`; selector policy records contain no regime label = `true`; registration is absent from policy records = `true`; selector returns the computed cheapest option = `true`; seed blocks are disjoint = `true`.

## Pilot

Ten worlds (`14801:14810`) ran before freeze.

- Exclusion won `10/10` exclusion-favorable worlds.
- Exclusion appeared in `0/10` worlds when any competitor was favorable.
- Favorable-regime wins: exclusion `10/10`, hypervigilance `10/10`, internal attack `10/10`, oscillation `10/10`.
- Registration off was static in `10/10` worlds; maximum per-episode `|Δprior| = 0.0`.
- Registration on strengthened the prior in `10/10` worlds; minimum `Δprior = 0.380000`.
- Registration ablation restored a static prior in `10/10` worlds.
- Selected policy and contact stream were matched across toggles in `10/10` worlds; mean attempts per world were `16.700000`.

Pilot provisional verdicts: policy selection `PASS`; starvation `PASS`; confirmation `PASS`; toggle separation `PASS`. Pilot results were used only to freeze the static tolerance and inspect guards.

## Freeze log

The static tolerance, directional strengthening test, provisional count thresholds, design, and vocabulary were frozen before confirmation. No threshold or parameter changed. Full details are in `freeze-log.md`.

## Confirmatory results

Twenty fresh worlds (`14851:14870`) ran after freeze; no seed overlaps the pilot.

- Exclusion won `20/20` exclusion-favorable worlds.
- Exclusion appeared in `0/20` worlds when any competitor was favorable.
- Favorable-regime wins: exclusion `20/20`, hypervigilance `20/20`, internal attack `20/20`, oscillation `20/20`.
- Registration off was static in `20/20` worlds; maximum per-episode `|Δprior| = 0.0`.
- Registration on strengthened the prior in `20/20` worlds; minimum `Δprior = 0.379998`.
- Registration ablation restored a static prior in `20/20` worlds.
- Selected policy and contact stream were matched across toggles in `20/20` worlds; mean attempts per world were `17.750000`.

### Verdict against §7.4

1. `PASS` — exclusion ≥ `16/20` when cheapest-reliable and ≤ `4/20` when a competitor is; every alternative appears in its own favorable regime.
2. `PASS` — registration off keeps every episode at `|Δpriorₜ| ≤ 1.0e-12` during exclusion.
3. `PASS` — registration on strengthens the prior and registration ablation removes strengthening.
4. `PASS` — starvation and confirmation are both realized with selected policy and contact stream matched, so the registration toggle is the sole difference.

Overall frozen-criterion verdict: **all four construction criteria passed**.

## Interpretation

The implemented construction reproduces the specified conditional exiling result: exclusion is selected by expected-cost competition when it is the cheapest reliable protection, while each alternative wins under its own favorable costs. With exclusion held fixed, a closed registration channel starves the relational prior of evidence, whereas an open channel makes suppressed contact available as rejection and strengthens *alone with this*. Ablating registration removes that strengthening.

This is an existence result inside an authored model. The construction shows that policy competition and the two consequence regimes can coexist computationally; it does not establish that these costs, likelihoods, update rules, or parts ontology describe people. In particular, the rejection likelihood and the mapping from a registered suppressed attempt to evidence are stipulated. The construction reproduces the strengthening under that stipulation; it does not derive the clinical mechanism.
