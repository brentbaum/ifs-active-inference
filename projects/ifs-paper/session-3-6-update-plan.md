# v2 Draft Update Plan — Based on Working Session 3/6

## Key Insights from Session

The session surfaced several significant shifts and refinements to the model. The co-author (active inference researcher) pushed hard on **precision vs. structure** as the primary mechanism, and several new formulations emerged.

---

## Major Updates Needed

### 1. Precision-First Reframing (affects Sections 2.1, 2.2, 2.8)

**Current v2**: Parts are "modular subgraphs" with "weak or absent edges" to context — frozenness comes from structural disconnection (no edges = no prediction errors = no updating).

**Session insight**: The co-author argued convincingly that you may not need structural disconnection at all. The same phenomena can be explained by **extremely high precision on the part's priors** — so high that incoming sensory evidence gets discarded (the likelihood is overwhelmed by the prior). The graph edges may exist but have functionally zero influence because the prior is so rigid.

**Proposed update**: Reframe parts as **high-precision prior clusters** whose rigidity makes them *functionally* disconnected from context, even if edges nominally exist. Keep the graph metaphor as an intuition-builder but note that the formal mechanism is precision-based, not topological. This simplifies the formalism considerably — no need for structure learning / edge creation. The "reconnection" in therapy is really **precision reduction** that allows existing (but functionally suppressed) channels to transmit evidence again.

**Impact**: This resolves the exposure therapy puzzle — exposure therapy works (slowly) because there ARE connections, just overwhelmed by prior precision. IFS witnessing works faster because it directly reduces prior precision through dual-perspective holding.

### 2. Unblending vs. Witnessing — Formal Distinction (new subsection or revise 2.4)

**Current v2**: Unblending and witnessing are somewhat conflated in Section 2.4.

**Session insight**: These are formally distinct:
- **Unblending** = any operation that makes the part's priors not dominate the computation. Can be done by distraction, shifting attention, etc. Is purely about precision redistribution. Not inherently therapeutic.
- **Witnessing** = a specific form of unblending where you hold both the part's perspective AND current context simultaneously. This is the therapeutic operation because it (a) reduces precision on the part's priors and (b) creates a channel for sensory evidence to update those priors.

**Proposed update**: Split Section 2.4 into:
- 2.4a: Unblending (precision redistribution — not inherently healing)
- 2.4b: Witnessing (dual-perspective holding — the therapeutic mechanism)

### 3. The 2x2 Matrix: Part Activation x Self-Establishment (new figure/subsection in Section 4)

**Session insight**: A clarifying 2x2:

| | Low Self/Context | High Self/Context |
|---|---|---|
| **Low Part Activation** | Baseline / normal | Presence / Self |
| **High Part Activation** | Blending | Therapy / Witnessing |

The therapeutic zone requires BOTH high part activation AND high self-establishment. This explains why you need to activate the part (can't update what's not active) but also need the skill to not get dominated by it.

**Proposed update**: Add this as a figure in Section 4 (session dynamics). It's a powerful clinical intuition-builder.

### 4. Causal Chain Within Parts — Age, Capability, Danger (revise Section 2.1, add to Section 5)

**Session insight**: Parts don't just have one prior — they have a causal chain of priors:
- **Age prior** ("I'm 6") ->
- **Capability prior** ("I'm helpless") ->
- **Danger assessment** ("dogs are dangerous to me") ->
- **Action policy** ("run!")

Therapeutic targeting works on the UPSTREAM priors (telling the part your actual age, which cascades to capability, which cascades to danger assessment). This is why "how old do you think I am?" is such a powerful therapeutic question — it targets the root of the causal chain.

**Proposed update**: Add this causal structure to Section 2.1 (what is a part) and use it in the dog phobia example (Section 5) to show how therapy targets upstream priors.

### 5. Presence vs. Dissociation — Precision Location (revise Section 2.5)

**Current v2**: Distinguishes presence from dissociation via "prior entropy" — presence = high entropy, dissociation = low entropy (selectively avoidant).

**Session insight**: A cleaner formulation:
- **Presence** = low precision on priors + high precision on sensory evidence (responsive, permeable, not constrained by expectations)
- **Dissociation** = low precision on sensory evidence + high precision on priors (impermeable, stuck, not responsive)
- Both can look "quiet" but the mechanism is opposite: presence is quiet because open; dissociation is quiet because closed.

**Proposed update**: Revise Section 2.5 to use this precision-location framing alongside (or instead of) the entropy framing. The precision formulation is more mechanistically precise and directly ties to the attention/precision literature.

### 6. Exposure Therapy Comparison (add to Section 8 or Section 4)

**Session insight**: The precision model naturally explains why exposure therapy works but is slow:
- Exposure therapy = blended with the part + presenting contradictory sensory evidence. Works because connections exist, but the prior is so rigid it takes massive repeated evidence.
- IFS witnessing = unblended (holding both perspectives) + targeted evidence to upstream priors. Works faster because (a) dual-perspective reduces precision, making priors more permeable, and (b) you target the root priors (age, capability) not just the surface prior (dogs are dangerous).

**Proposed update**: Add an explicit comparison section — this is a strong selling point for the model because it explains differential efficacy of therapeutic approaches.

### 7. How Parts Form (new section — flagged in session)

**Session insight**: "We should have a section on how parts are formed." Currently missing from v2. The mechanism: during an overwhelming experience, priors get formed with extremely high precision (extreme stress -> extreme consolidation). The causal chain crystallizes: "I was 6, I was helpless, there was a dog, I was in danger, I had to run." The high precision on these priors means subsequent contradictory evidence gets discarded.

**Proposed update**: Add a brief Section 2.0 or early 2.1 subsection on part formation. This grounds the rest of the model.

---

## Minor Updates

### 8. "Context" -> "Baseline" or "Current Priors" terminology
The session established that what the v2 draft calls "context" is really just "the rest of the generative model" or "current priors." "Baseline" was the agreed-upon term during the session.

### 9. Simulation Updates
Brent committed to building a POMDP simulation based on the discussed model. The simulation should show:
- Before therapy: ambiguous dog -> exile activates -> terror -> blending -> run
- During therapy: witnessing (dual perspective) -> precision reduction -> prior updating
- After therapy: ambiguous dog -> brief flicker -> return to presence

### 10. Deliverables Discussed
- Send co-author: IFS phenomenology section (written up), model description, witnessing -> contextualization mechanism
- Co-author needs: paper version of IFS phenomenology to connect formal model to clinical reality
- Shared: figures, POMDP simulation, paper draft in collaborative format

---

## Prioritized Edit Sequence

1. **Reframe Section 2.1** — Parts as high-precision prior clusters with causal structure (age -> capability -> danger -> action). Keep graph metaphor but note precision is the formal mechanism.
2. **Split Section 2.4** — Unblending (generic) vs. Witnessing (therapeutic)
3. **Revise Section 2.5** — Add precision-location framing for presence vs. dissociation
4. **Add part formation** — Brief section on how parts crystallize during overwhelming experience
5. **Add 2x2 matrix figure** — Part activation x self-establishment
6. **Revise Section 5 (dog example)** — Use causal chain, show upstream targeting
7. **Add exposure therapy comparison** — Explain differential efficacy
8. **Revise Section 2.8 (therapeutic mechanisms)** — "Reconnection" is really precision reduction allowing existing channels to transmit. Structure learning may not be needed.
9. **Update terminology** — "Context" -> "baseline" or "current priors" where appropriate
10. **Build POMDP simulation** — Based on agreed model
