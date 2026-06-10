# Draft v11 — Claim-Architecture Outline

Working title: **Self-Energy, Witnessing, and the Revision of Part Beliefs: An Active Inference Account of Internal Family Systems**

This is an outline of claims, not topics. Every bullet is an assertion the paper makes (or scaffolding it needs). Reorder freely — the tags travel with the nodes.

**Tag conventions**
- `[C1] [C2] [C3]` — which core claim the node serves (`[S]` = scaffolding)
- `[v10 §x]` — prose exists in v10, keep/adapt
- `[v9 §x IMPORT]` — import from v9 (prose exists there)
- `[FIX]` — known precision repair; spec given inline
- `[NEW]` — needs new writing
- `[DEFER→v12]` — intentionally excluded; parked for the gating paper
- `[OPT]` — optional; cut first if claims feel spread

---

## Thesis (one sentence)

A part is an identity-level precision bundle organized around a self-state prior; Self-energy determines whether activation of that bundle produces capture or context-held activation; and inside the context-held window, relational prediction error reaches the shared self-state root — which is why witnessing-type change generalizes while threat-level change stays local.

## The claim spine

These replace the undefined "Moves 1/2/3" everywhere. Defined once in §1, referenced by name thereafter.

- **C1 — Architecture.** Parts are identity-level precision bundles (self-state, world-state, policy, expected outcome) in which self-state is the organizing, upstream prior.
- **C2 — Regime.** Self-energy sets the precision balance between part-bundle priors and present-context evidence; that balance determines whether activation becomes capture or context-held activation, and only context-held activation permits durable revision.
- **C3 — Content.** Inside the context-held window the operative corrective signal is relational prediction error — the activated part registering the system's present-moment self-state — and because it revises the *shared* self-state prior, the resulting change generalizes beyond the treated cue.

And one corollary, which is how hierarchical gating lives in this paper without becoming a fourth claim:

- **G — Gating corollary.** Because protectors are themselves parts (C1 applied recursively) and relational prediction error operates on their expectations too (C3 applied to protectors), protection organizes into a layered stack, and witnessing reaches the exile by descending it — each layer's cost prediction must update before the next layer becomes accessible. G introduces **no new mechanism and no new hidden factors**; it is the recursion of C1+C3 onto the protective system. It is stated as architecture, supported clinically (the protectors-first ordering), and tested only indirectly here; its formalization (gate as hidden factor, trust variables, stacked simulation) is the v12 paper.

Audit rule: every section node below should serve C1, C2, C3, G, or be tagged `[S]`. Anything that serves none is spread — cut it.

---

## §1. Introduction `[S → states C1–C3]`

- Hook: *Sometimes I am afraid. Sometimes a part of me is afraid. Same activation, different relationship.* `[v10 §1]`
- The dog case: activation that feels like identity, not one belief among many; existing fear models have no account of this. `[v10 §1]`
- IFS reading: burdened part, protectors, the capture-vs-Self question. `[v10 §1]`
- The paper's claim: the decisive therapeutic variable is the relation of the system to activated part-content; the governing variable is Self-energy. `[v10 §1]`
- State C1, C2, C3 explicitly as the paper's three claims and the roadmap. `[FIX — replaces the v10 ¶ "two sharper predictions"; purges all later "Move 1/2/3" references by giving them names here]` `[NEW: ~1 paragraph]`
- One-sentence trailer for G: the same architecture applies recursively to the parts that protect — yielding the layered structure IFS calls the protective system (§8) — with formal treatment deferred. `[G]` `[NEW: 1 sentence]`
- Non-claims: not replacing exposure/schema work; different therapies alter different inferential variables. `[v10 §1]`
- Section map (one short paragraph, rebuilt last once ordering is final). `[FIX — v10's map has stale numbering]`

## §2. IFS in Its Own Terms `[S]`

- Exiles, managers, firefighters; Self as non-part; Self-energy as clinical go/no-go. `[v10 §2]`
- Dog example in IFS terms; captured vs unblended; speaking *from* vs *for* the part. `[v10 §2]`
- *How do you feel toward this part?* measures relationship to activation, not activation. `[v10 §2]`
- Table 1: translation table. `[v10 §2]` `[FIX — align "Witnessing" and "Self" rows with the canonical formulations in §5–6, and the "Protectors" row with §8's framing (full parts whose policies produce the effective gate state, not "access-control tendencies"); one source of truth]`

## §3. Parts as Identity-Level Precision Bundles `[C1]`

- A part is a local control model: a bundle of priors that learned together and reactivate together. `[v10 §3]`
- The four elements; **self-state is the organizing prior** — the root from which the others inherit. `[v10 §3]`
- Object-relations precedent (self-image / object-image / cause / effect): same structure, different level of description. `[v10 §3]`
- Discriminant validity vs schemas, latent contexts, trait priors; the three predictions nearby constructs don't make. `[v10 §3]` (load-bearing — keep verbatim)
- Because self-state is shared across situations while threat meanings are cue-bound, revision that reaches self-state should travel; this is why the transfer test exists (forward pointer to C3). `[v10 §3]` `[FIX — repair pointer: transfer design is §9.3, results §10.4; v10 pointed at "§11.3," which is wrong]`
- Dog bundle example: the four priors; why parts feel coherent; why activation feels like identity (no vantage point outside the bundle). `[v10 §3]`
- 3.1 Computational setup `[S]`
  - Not separate agents; learned local models within one generative model. `[v10 §3.1]`
  - Generative model: two hidden factors (self-state, threat meaning), three channels, cross-trial Dirichlet learning. `[v10 §3.1]`
  - Precision defined for the non-technical reader. `[v10 §3.1]`
  - Scope discipline: only π_part, λ_ctx, E_t vary. `[v10 §3.1]`

## §4. Formation and Persistence `[S → supports C1]`

- Formation claim: overwhelm + low control; threat alone is not enough. `[v10 §4]`
- Formation sequence (compression under overwhelm); two predictions (not all fear becomes a part; chronic neglect is part-forming). `[v10 §4]`
- Persistence: self-sealing loop — high prior precision, underweighted present context, avoidant sampling. `[v10 §4]`
- Functional isolation, not structural disconnection → admits slow change under safe contact → why exposure still learns something in the model. `[v10 §4]`
- Formation simulation summary; control gates identity-level consolidation. `[v10 §4 + App A]`

## §5. Self and Self-Energy `[C2]`

- Self as regime of uncaptured inference (not a homunculus). `[v10 §5.1]`
- **The dual-role claim, stated once and squarely** `[FIX — this is the paper's most pressable point; currently implicit and scattered]` `[NEW: ~1 paragraph]`
  - Self has two formal appearances but one mechanism:
    - (i) **as regime** — the condition in which no bundle's precision dominates inference;
    - (ii) **as content** — the present-moment self-state that self-modeling yields when that regime obtains, which an activated part can register as evidence.
  - (ii) is available exactly when (i) obtains. Self-energy is the variable governing both. There is no third thing.
- Self-energy as composite: autonomic-social regulation (V_t) + metacognitive depth (M_t); neither sufficient alone; E_t as scalar proxy. `[v10 §5.2]`
- Scaffolding: Self-energy is dyadic before it is endogenous; therapist supplies co-regulation, pacing, a temporary relational bridge (Direct Access is explicitly temporary — sequence returns client-Self to the part). `[v10 §5.2 + v9 §5 IMPORT, 2–3 sentences]` `[OPT]`
- Self-led calm vs dissociative quiet; discriminator = whether present evidence stays online. `[v10 §5.3]`
- The therapeutic zone 2×2; lower-right cell unstable by default; therapy titrates both axes. `[v10 §5.4]`
- 8 C's as phenomenological signature; the self-like part as unsolved hard case. `[v10 §5.4]`

## §6. Capture and Context-Held Activation `[C2]`

(Merges v10 §6 + §7 — they are one argument: the two regimes, and why only one permits change.)

- The regimes are asymmetric: capture is the failure mode, context-held activation the goal; witnessing is its clinically cultivated form. `[v10 §6]`
- **Canonical Self-energy formalization** `[FIX — the single biggest repair; this wording becomes the only mechanism statement in the paper]`
  - E_t enters inference through one mechanism: the precision balance.
    π_eff_part = r_t · π_part · e^(−βE_t); λ_eff_ctx = λ_ctx · e^(+γE_t); capture index C_t = π_eff / (π_eff + λ_eff). `[v10 §6.1]`
  - Two consequences, not two mechanisms:
    - informational — as C_t falls, ordinary present-context evidence regains weight;
    - relational — the present-moment self-state is itself part of present context, so low capture is what makes it observable to the activated part.
  - The main simulation's "witnessed-self-state channel opens via inverse capture" is an *implementation* of the relational consequence, not an added gate; the transfer model's "self-evidence always available, weighted by the standard balance" is the same mechanism in a smaller model. Say this explicitly in §9. `[NEW: 2–3 sentences]`
  - Purge everywhere: any wording implying Self-energy toggles a channel on/off as a separate mechanism. The sigmoid in results is emergent (v10 §11.6 already says so — keep that sentence).
- Capture: graded, not binary; the part's local world becomes the only reality model. `[v10 §6.1]`
- Context-held activation: activation live, capture prevented; distinct from distraction, suppression, dissociation. `[v10 §6.2]`
- The clinical probe as regime assay. `[v10 §6.3]`
- Why only context-held activation permits lasting change: the three simultaneous conditions (active part, online context, no capture); why capture fails; why calm-without-activation fails. `[v10 §7]`
- Unburdening as upstream revision; why deep change feels sudden; role transformation after unburdening. `[v10 §7.1]`
- Exposure vs context-held activation: informational PE without relational PE; transition to C3. `[v10 §7.2]` `[FIX — repair stale cross-refs ("§11.3 and §12.8" → transfer design §9.3, results §10.4)]`

## §7. Relational Prediction Error `[C3]`

- Present context includes more than the room: the present-moment self-state becomes registrable by the part. `[v10 §8]`
- The part's generative model includes relational expectations (*I am alone with this*), which belong to the self-state element. `[v10 §8]`
- **The exile form:** expected isolation meets presence; the mismatch reaches the self-state prior directly, not threat meaning. `[v10 §8]`
- **The protector form** `[C3, G]` `[v9 §6 IMPORT — the single most valuable import; ~2 paragraphs]`
  - Protectors carry expectations too: contact with the exile will produce flooding, humiliation, destabilization.
  - Under witnessing, the protector encounters what its model did not predict: Self remains present, does not collapse, the catastrophe does not arrive. Its cost estimate updates; access relaxes.
  - Clinical ordering follows: protectors change *before* exiles, and are often the rate-limiting step. (What this implies about the *structure* of protection — the stack — is developed in §8.)
- Two channels inside the window, not interchangeable: relational primary, informational secondary; the shift often precedes any explicit life-updating. `[v10 §8]`
- Clinical anchors: Anderson on relationship-building; *She sees me now.* `[v10 §8]`
- Reconsolidation: compatible, not demonstrated — the destabilizing mismatch is relational. `[v10 §8]` `[FIX — adopt v9's hedged wording ("compatible with… remains an empirical question") over v10's "offers independent support"]`
- Modality independence. `[v10 §8]`

## §8. Layered Protection: The Architecture Applied to Protectors `[G]`

(Upgraded from v10's "Extensions" — this is where the gating picture lives, framed as recursion of C1+C3, not as new machinery.)

- **Protectors are full parts, not switches** — C1 applies to them. Each protector bundle carries a role/self-position ("I'm the one who keeps us composed"), a target-part model (beliefs about what happens if the exile comes forward), policy priors (suppress, perfect, numb, charm, dissociate), and feared consequences (humiliation, flooding, abandonment). `[G ← C1]` `[v9 §3 IMPORT — compressed to one paragraph]`
- **The gate is what protector policies produce, not what protectors are.** The effective gate state — whether access to a lower layer is currently open, closed, or partial — is the net output of currently active protector policies. This is why IFS negotiates with protectors rather than removing obstacles: a gate has no beliefs to update; a part does. `[G]` `[v9 §3 IMPORT — short, load-bearing; this sentence is what keeps "gating" in the paper without a gate mechanism]`
- Managers gate prospectively, firefighters reactively — temporal depth of the same function. `[v10 §9]`
- **Protection layers.** New protectors form when prior protective strategies themselves become costly, shameful, or ineffective: need goes unmet → protest → protest punished → suppression protector → suppression suffocates → intellectualization/achievement protector → even the wish to ask becomes shameful → a further layer seals the wish itself. Each layer encodes a developmentally later self-state and a more socially elaborated policy; the exile below stays frozen. `[G ← C1]` `[v9 §4 IMPORT — the developmental story, 1–2 paragraphs]`
- **Witnessing descends the stack** — C3 applies at each layer. Access to layer *n* depends on layer *n−1* updating its cost prediction via protector-form relational PE (§7). The clinical sequence — permission before contact, protectors before exiles, why the work "takes so long" — falls out of the architecture rather than being a procedural convention. `[G ← C3]` `[v9 §4 IMPORT, adapted]`
- **Terminological guard:** witnessing remains a *state* (context-held activation, §6); the descent is the *trajectory* that repeated witnessing traces through the stack. One sentence, so v9's "witnessing = gate traversal" definition doesn't silently reenter. `[FIX — reconciles the v9/v10 definitional conflict]` `[NEW: 1 sentence]`
- **Why G is a corollary, not a fourth claim:** no new hidden factors, no new precision quantities — only C1 and C3 applied recursively to the protective system. The simulations do not test the stack; they collapse it into the part's policy priors. The stacked formalization (gate as inferred hidden factor, per-layer trust variables) is the next paper. `[NEW: 2–3 sentences — the honesty marker that keeps claims tight]` `[DEFER→v12]`
- Realistic protectors: some operate on accurate current contingencies (unsafe partner, shaming family); the model formalizes anachronistic protection, it does not pathologize protection as such. `[v9 §4/§8 IMPORT — could live here or in §11; pick one place]`
- Polarization: a part's world-model naturally includes other parts, so cross-part dynamics need no separate mechanism — mutual high-cost policies; alternation of rival local realities under low E_t; simultaneous representability under high E_t; three-regime picture with the medium exploration band. `[G ← C1]` `[v10 §9 + App A + v9 §4 one-line import]`

## §9. Simulation Design `[S → tests C1–C3]`

- 9.1 Main model: three hidden factors, five channels, witnessed-self-state channel precision-modulated by inverse capture `[FIX — describe as implementation of §6's relational consequence, per the canonical formulation]`; three E_t conditions (exposure / informational / relational depth); two-phase protocol. `[v10 §10.1]`
- 9.2 H1 vs H2: reversing the causal chain isolates whether the cascade requires self-state at the root — **this tests C1.** `[v10 §10.2]` `[FIX — "tests Move 1" → "tests C1"]`
- 9.3 Follow-on transfer test: shared self-state prior, cue-specific threat priors; dog training → first cat probe — **this tests C3** (and the E_t contrast within it tests C2). `[v10 §10.3]`
- Methodological note: within-run timing alone cannot prove content specificity; transfer is the content discriminant; adversarial history in Appendix B. `[v10 §10.3]`

## §10. Results `[S → results keyed to claims]`

- 10.1 Same activation, different relationship: matched cue structure, divergent trajectories across E_t. `[v10 §11.1]` → **C2**
- 10.2 The cascade under H1: self-state first, threat second, outcome third, policy last; the informational/relational gap on self-state. `[v10 §11.2]` → **C2, C3**
- 10.3 H2 flips the order: cascade requires self-state at the root. `[v10 §11.3]` → **C1**
- 10.4 Transfer: identity-level revision generalizes to the untreated cue; threat-level revision does not; low E_t does not transfer; cat-specific threat prior unchanged (no leakage). `[v10 §11.8]` → **C3**
- 10.5 Controls: real danger preserves adaptive fear; dissociation reduces disturbance without upstream revision. `[v10 §11.5]`
- 10.6 E_t sweep: emergent sigmoid ≈ 0.60–0.65. `[v10 §11.6]`
- 10.7 Free-choice probe: avoid / inspect / stay; behavior tracks the cascade. Parameter sensitivity ±20%. `[v10 §11.7]`
- `[FIX — ordering above moves transfer (10.4) up next to the cascade results so C3's two halves sit together; v10 buried it at §11.8 after controls. Reorder freely.]`

## §11. Discussion

- What the model explains — rekey the seven points to the claim spine (worlds-not-beliefs → C1; activation-alone-insufficient, calm-insufficient, dissociation-vs-Self → C2; relational PE, generalization gradient → C3; "why this is still an IFS model" → thesis). `[v10 §12.1]` `[FIX — currently an unordered list of seven; grouping by claim makes the architecture audible]`
- Add an eighth: it explains the clinical ordering — protectors before exiles, permission before contact — as architectural (G: each layer's cost prediction must update before descent) rather than as procedural convention. `[G]` `[v9 §8 IMPORT — 2–3 sentences]`
- **What the model does not claim** `[v9 §8 IMPORT — reviewer armor; ~3 short paragraphs]`
  - Agnostic on parts pre-existing their burdens; formalizes how extreme roles form/persist/revise, not IFS's full ontology.
  - The matched-contact foil is not the strongest form of AEDP / Coherence Therapy / EFT; the simulation isolates one variable (corrective contact ± Self-led relational contact).
  - Realistic protection is not pathologized (if not placed in §8).
- What it does not yet explain: protector negotiation/trust, self-like parts, the dyad, multi-part networks; timing-vs-content limitation of the cascade and how transfer partially addresses it. `[v10 §12.2]`
- **Implications** `[v10 §12.3 widened — pointers, not new claims]`
  - Therapy comparison: exposure learns, but learns differently; witnessing should revise a broader downstream class. `[v10 §12.3]`
  - The clinical probe as a *measurement instrument*: "How do you feel toward this part?" is a regime assay with a formal correlate (C_t) — a candidate session-level process measure. `[NEW: 2–3 sentences]`
  - The generalization gradient as a trial-design signature: transfer to structurally similar untreated fears as the discriminating outcome variable between modalities. `[NEW: 1–2 sentences; currently implicit in predictions]`
  - Why purely informational interventions (psychoeducation, cognitive restructuring on identity-level material) underperform: they supply the secondary channel without the primary one. `[NEW: 1–2 sentences]`
  - `[OPT]` One sentence, no more: any agent architecture with learned local control models admits capture/witnessing-like regimes — the formalism is not specific to human therapy. Cut first if it smells like spread.
- Empirical predictions (keep all three, keyed to claims): revision order (C1+C2), generalization gradient (C3), relational channel primacy (C3). `[v10 §12.4]`
  - `[OPT]` A fourth, from G: under IFS-informed work, protector relaxation (willingness to allow contact) should precede exile-level identity revision; under matched exposure no such ordering should appear. `[v9 §8 IMPORT — only if it doesn't crowd the three; it is the natural v12 bridge]`
- Next steps: **stacked relational gating is the marquee next model — making G formal**: gate as inferred hidden factor, multiple protector layers each with cost model and trust variable, sequential relaxation as the test `[DEFER→v12, named explicitly]`; dyadic regulation; self-like parts; empirical fitting. `[v10 §12.4]`
- Closing paragraph: what was defined, what was shown, the sharpest edge. `[v10 §12.4]`

## Appendices

- **A. Formation and polarization simulations.** `[v10 App A]`
- **B. Adversarial testing.** Tests 1–3 passed; Test 4 (gated threat channel mimics cascade) motivated the transfer design. `[v10 App B]`
- **C. Condensed glossary.** `[v10 App C]` `[FIX — re-derive rows from final §5–7 wording after prose pass; v10's glossary predates the canonical formulations]`

---

## Explicitly deferred to v12 (the gating paper)

The division of labor: **v11 states G as a corollary in prose; v12 makes G formal and tests it.** Listed so the formal machinery doesn't re-import by accident:

- "IFS as hierarchical relational gating" as a *center claim* (in v11 it is a corollary of C1+C3)
- Gate as a true hidden factor inferred via A-matrices (v4 simulation, gate ablation)
- Per-layer trust variables and protector cost models as formal quantities
- Witnessing *redefined* as gate traversal (v11 keeps witnessing = the state; descent = the trajectory; see §8 terminological guard)
- Presence as a distinct construct from Self-energy
- Sequential-relaxation simulation of a multi-layer stack

What v11 now carries from the v9 material (all prose, no new formal objects): the protector *form* of relational PE (§7), protector bundle anatomy and the gate-as-policy-output framing (§8), the layered developmental story and witnessing-as-descent (§8), the architectural reading of clinical ordering (§11), and the "does not claim" section (§11).

## Open items (logistics, not claims)

- Figures and simulation code are no longer in this repo (moved out in the PARA restructure, c13214b). Relocate or re-link `figures/`, `figures/v2/`, `figures/v3/` before assembly.
- Decide final length target. v10 ≈ 9.5k words; the merge of §6–7 and the discussion regrouping should land v11 slightly under it despite the three imports.
- Rebuild §1's section map and all cross-references last, after ordering is frozen.
