# Logical Structure of the IFS-Active Inference Draft

Extraction of the minimum logical content from `ifs-active-inference-outline-v1.md` and supporting documents. Each item is classified, given a dependency list, and traced to a source section.

---

## Axioms (Imported from Prior Work)

### AX1. Active inference generative model framework
**Statement**: The brain maintains a generative model of the causes of sensory data and minimizes variational free energy by updating beliefs or taking action.
**Depends on**: --
**Source**: Section 1.2 (standard active inference; Friston et al.)

### AX2. Precision as confidence weighting
**Statement**: Precision weights modulate the relative influence of predictions and prediction errors in inference. High precision on a signal means "trust this signal."
**Depends on**: AX1
**Source**: Section 1.2

### AX3. Epistemic vs. pragmatic priors
**Statement**: Epistemic priors are beliefs about the world (updated via prediction error). Pragmatic priors are preferences about outcomes (drive action to reduce discrepancy).
**Depends on**: AX1
**Source**: Section 1.2 (credited to conversations with Shamil)

### AX4. Factor graph message passing
**Statement**: Inference in a generative model can be represented as message passing on a factor graph. A node that receives no messages cannot update its parameters.
**Depends on**: AX1
**Source**: Section 2.8, recontextualization-as-unfreezing.md (standard Bayesian message passing)

### AX5. IFS clinical framework
**Statement**: IFS posits that the psyche contains parts (exiles, managers, firefighters), a core Self, and that therapeutic change involves accessing parts, witnessing their experience, and unburdening extreme beliefs/emotions.
**Depends on**: --
**Source**: Section 1.3 (Schwartz, IFS literature)

### AX6. Chamberlin's coherence therapy model
**Statement**: Pathological schemas are modular (isolated from other cognitive processes), described as "knowledge in the system but not yet knowledge to the system." Therapeutic change involves making implicit schemas explicit, enabling juxtaposition with contradictory evidence. Discovery alone resolves >50% of cases.
**Depends on**: AX1
**Source**: Section 2.8, Section 8.1, chamberlin-critique-three-mechanisms.md (Chamberlin 2022/2023)

### AX7. Memory reconsolidation
**Statement**: Consolidated memories can be returned to a labile (updatable) state when retrieved under specific conditions, allowing modification during a reconsolidation window.
**Depends on**: --
**Source**: Section 8.2 (Ecker et al., reconsolidation literature)

### AX8. Interoceptive inference
**Statement**: The generative model includes predictions about bodily states (heart rate, muscle tension, etc.). The body is part of the world model, not separate from it.
**Depends on**: AX1
**Source**: Section 8.2 (Seth; active inference accounts of interoception)

---

## Definitions

### D1. Part (computational definition)
**Statement**: A part is a cluster of associated priors within a single generative model, together with (i) a precision hyperprior governing how strongly those priors dominate inference, and (ii) an activation prior governing when the cluster activates.
**Formal**: Part := {associated_priors: [p_1...p_n], precision_hyperprior: pi_part, activation_prior: P("I am needed" | context)}
**Depends on**: AX1, AX2
**Source**: Section 2.1

### D2. Blending
**Statement**: Blending is the state in which a modular (disconnected) subgraph of the generative model captures policy selection, causing its context-blind beliefs to dominate both perception and action.
**Depends on**: D1, C2
**Source**: Section 2.2

### D3. Unblending
**Statement**: Unblending is the shift from a winner-take-all, high-precision state dominated by one part's priors back to a balanced, multi-modal predictive regime where multiple prior clusters compete.
**Depends on**: D1, D2
**Source**: Section 2.4

### D4. Self (as regime, not entity)
**Statement**: Self is a regime of the generative model characterized by: (i) no single prior cluster dominating precision allocation, (ii) high epistemic openness, (iii) pragmatic priors oriented toward organism-level thriving rather than part-specific survival.
**Depends on**: D1, AX1, AX2
**Source**: Section 2.5

### D5. Self-energy
**Statement**: Self-energy is a hyperprior on maximum precision bounds across all parts. Higher Self-energy means a lower ceiling on how much any individual part can dominate inference.
**Depends on**: D4, AX2
**Source**: Section 2.5, Section 2.8

### D6. Manager
**Statement**: A manager is a high-level policy prior that plans trajectories to keep the system away from exile-activating states, operating with high temporal depth.
**Depends on**: D1, D8, AX1
**Source**: Section 2.3.1

### D7. Firefighter
**Statement**: A firefighter is a low-level reactive policy prior that rapidly minimizes acute free energy when a trigger slips through protector defenses, operating with low temporal depth.
**Depends on**: D1, AX1
**Source**: Section 2.3.2

### D8. Exile
**Statement**: An exile is a modular (disconnected) prior cluster encoding the emotional, somatic, and belief state from an overwhelming experience. It is frozen because it is isolated from context-bearing nodes in the factor graph.
**Depends on**: D1, C2, AX4
**Source**: Section 2.3.3

### D9. Polarization
**Statement**: Polarization is the state in which two parts alternate in winning inferential competition, with neither achieving stable dominance, producing oscillation or limit cycles.
**Depends on**: D1, D2
**Source**: Section 2.7

### D10. Re-contextualization
**Statement**: Re-contextualization is the addition of edges between an isolated schema subgraph and the broader context network, enabling message passing where none previously existed.
**Depends on**: AX4, C2
**Source**: Section 2.8, recontextualization-as-unfreezing.md

---

## Core Claims (Novel Assertions)

### C1. Parts are precision-modulating patterns within a single generative model, not separate sub-agents
**Statement**: Parts are not separate sub-agents with their own generative models. They are patterns of precision allocation within a single model that, when activated, shape both perception and action.
**Depends on**: AX1, AX2, AX5
**Source**: Working thesis, Section 2.1
**Status**: This is the paper's central ontological claim -- a specific bridge between AX1/AX2 (active inference) and AX5 (IFS). The critique notes this is "elegant but undersells what IFS is doing clinically."

### C2. Parts persist and dominate through modularity (graph disconnection)
**Statement**: Parts maintain extreme beliefs and dominate computation because they are modular subgraphs lacking edges to context variables. This disconnection means they (i) cannot generate context-dependent prediction errors, (ii) cannot receive disconfirming evidence, and (iii) therefore cannot update via standard Bayesian inference.
**Depends on**: AX4, C1
**Source**: Working thesis, Section 2.2
**Status**: This is the paper's core mechanistic claim. It unifies frozenness and dominance as two faces of the same structural property. Distinct from Chamberlin (AX6) in that Chamberlin describes modularity phenomenologically; this claim gives it a specific factor-graph interpretation within active inference.

### C3. Frozenness is a consequence of modularity, not a separate property
**Statement**: A prior is "frozen" (non-updating) not because of a special plasticity lock or closed learning window, but because it is disconnected from context nodes. No messages can reach it, so no prediction errors can drive updating. Disconnection IS the closed learning window.
**Depends on**: C2, AX4
**Source**: Section 2.8, recontextualization-as-unfreezing.md
**Status**: Novelty here is the reductive identification: frozen = disconnected. Prior work (Chamberlin, reconsolidation literature) treats frozenness and modularity as distinct or loosely related properties.

### C4. Welcoming and unburdening are the same mechanism at different depths
**Statement**: The previously proposed three mechanisms of IFS change (Self-energy increase, welcoming, unburdening) reduce to two. Welcoming and unburdening are both re-contextualization (reconnecting modular subgraphs), differing only in depth of modularity and consolidation strength, not in kind.
**Depends on**: C2, C3, D10, AX6
**Source**: Section 2.8, recontextualization-as-unfreezing.md
**Status**: This is the paper's strongest novel theoretical claim. It contradicts the three-mechanism model (chamberlin-critique-three-mechanisms.md) that the draft itself previously entertained. Predicts that resolution speed is a function of consolidation strength x context mismatch, not of a separate plasticity parameter.

### C5. Depth of modularity determines whether witnessing alone suffices
**Statement**: Cases that resolve with witnessing/Discovery alone (~50%) have shallow modularity. Cases requiring explicit unburdening have deeper isolation: either (i) strongly consolidated priors needing vivid juxtaposition, or (ii) hierarchical identity locks (meta-beliefs wrapping the schema at a higher graph level).
**Depends on**: C4, C2, AX6
**Source**: Section 2.8, recontextualization-as-unfreezing.md
**Status**: Derives from C4 but adds a specific predictive framework (three levels: shallow modularity, deep modularity, hierarchical identity lock).

### C6. Self qualities (8 C's) are default properties of unimpeded Bayesian inference
**Statement**: The eight qualities IFS attributes to Self (curiosity, calm, clarity, compassion, courage, creativity, connectedness, confidence) are not a special state but what Bayesian inference naturally produces when no modular subgraph dominates. Each quality maps to a specific computational property of unimpeded inference (e.g., curiosity = high epistemic drive, calm = danger estimates reflecting actual base rates).
**Depends on**: D4, C1, C2
**Source**: Section 2.5
**Status**: Novel mapping. Testable prediction: these qualities should co-occur and all increase as modularity decreases.

### C7. Re-contextualization simultaneously achieves accessibility, context-embedding, and plasticity restoration
**Statement**: Adding edges between an isolated subgraph and the broader context network does not produce three sequential effects (making explicit, embedding in context, restoring updateability). It produces one graph-topological change that manifests as all three simultaneously.
**Depends on**: C3, C4, D10, AX4
**Source**: Section 2.8, recontextualization-as-unfreezing.md
**Status**: Stronger than C4 -- not just "same mechanism" but "literally the same single operation with multiple descriptions."

### C8. The fundamental operation of therapeutic change is graph-topological, not parametric
**Statement**: The primary operation of IFS therapeutic change is adding edges to the factor graph (structure learning), not tuning precision parameters. Precision may be one means by which modularity is enforced, but the change that matters is graph surgery.
**Depends on**: C2, C4, D10, AX6
**Source**: Section 2.8, Appendix B item 10
**Status**: This shifts the paper's own thesis from "parts are precision-modulating meta-priors" (the original working thesis) toward "parts are modular subgraphs whose coupling is gated, and change is reconnection." The critique (v1-draft-critique.md, AI critique point 3) explicitly suggests this reframing.

---

## Inferences (Derived Consequences)

### I1. Blending is self-reinforcing
**Statement**: When a part's modular subgraph captures policy selection, its own predictions are self-consistent within its closed loop, and its activation increases precision on its associated priors, further suppressing competing signals. This creates a positive feedback loop that requires external intervention to break.
**Depends on**: C2, D2, AX2
**Source**: Section 2.2

### I2. Blending produces age regression because the subgraph preserves developmental state
**Statement**: The subjective experience of feeling younger/smaller during blending occurs because the modular subgraph preserves the developmental state at which it was formed, including somatic signatures.
**Depends on**: C2, D2, AX8
**Source**: Section 2.2

### I3. Protectors exist because exile priors are dangerous frozen attractors
**Statement**: Protectors (managers, firefighters) exist because activated exile priors, being non-updatable and high-precision, hijack the system (blending). Protectors prevent this by avoiding or rapidly suppressing exile activation. After unburdening, protectors relax because exile priors become normal updatable priors.
**Depends on**: C2, C3, D6, D7, D8
**Source**: Section 2.8

### I4. Witnessing must precede unburdening (not merely as clinical convention but by logical necessity)
**Statement**: You cannot send information to a disconnected node. Therefore, reconnection (witnessing/welcoming) is not merely a clinical prerequisite for unburdening -- it IS the mechanism. The ordering is not convention but graph-topological necessity.
**Depends on**: C4, C7, AX4
**Source**: Section 2.8

### I5. Self does not need explicit modeling
**Statement**: Self falls out as "what inference looks like on a fully connected generative model" and need not be represented as a distinct entity or module.
**Depends on**: C6, D4, C2
**Source**: Section 2.5

### I6. Therapist functions as external bypass of modularity
**Statement**: Breaking blending requires an external intervention that can bypass the modular subgraph's closed loop. The therapist (or Self-energy, or environmental change) provides this external pathway.
**Depends on**: I1, C2
**Source**: Section 2.2, Section 4.1

### I7. Part activation is triggered by interoceptive as well as exteroceptive state matching
**Statement**: Because the generative model includes bodily states, a racing heart can activate a part as effectively as seeing a dog, since the physiological signature matches the encoding context.
**Depends on**: D1, AX8, C2
**Source**: Section 2.1, Section 8.2

### I8. Unburdening is quick but integration takes time
**Statement**: Reconnection is a discrete graph topology change (instantaneous), but actual belief updating through the new edges requires subsequent experience flowing through them.
**Depends on**: C7, AX4
**Source**: Section 2.8

### I9. Phenomenological predictions from the Self-qualities mapping
**Statement**: If C6 is correct, then: (i) Self qualities should co-occur, (ii) they should all increase as modularity decreases, (iii) you should not find curiosity without compassion or vice versa -- they share the same underlying condition.
**Depends on**: C6
**Source**: Section 2.5

---

## Dependency Graph (Simplified)

```
AX1 (active inference) ──┬── AX2 (precision) ──┬── C1 (parts = precision patterns)
                         │                      │
AX4 (factor graphs) ─────┤                      ├── D1 (part definition)
                         │                      │
AX5 (IFS framework) ─────┤                      ├── C2 (modularity is the mechanism) ──┬── C3 (frozen = disconnected)
                         │                                                              │
AX6 (Chamberlin) ────────┘                                                              ├── C4 (welcoming = unburdening)
                                                                                        │        │
AX7 (reconsolidation) ──── [background support, not load-bearing]                       │        ├── C5 (depth spectrum)
                                                                                        │        │
AX8 (interoception) ─────── I7 (body triggers parts)                                   │        ├── C7 (one operation, multiple descriptions)
                                                                                        │        │
                                                                                        ├── C6 (Self = default inference)
                                                                                        │
                                                                                        ├── C8 (change is topological)
                                                                                        │
                                                                                        └── I1-I9 (derived consequences)
```

---

## What Is Genuinely New

### The Core Novel Contribution (one sentence)

**Parts are modular subgraphs in a single generative model's factor graph, and IFS therapeutic change is the progressive reconnection of these subgraphs to context -- a graph-topological operation, not a parametric one.**

### Decomposed into its minimum novel claims:

1. **C1 + C2: The modularity-as-mechanism thesis.** Parts are not sub-agents, not just "high-precision priors," but disconnected subgraphs. This is a specific factor-graph formalization that goes beyond both IFS clinical ontology (which treats parts as quasi-agents) and simple precision accounts (which treat them as loud signals in an open market). The key insight is that disconnection explains both persistence (frozenness) and dominance (blending) with a single structural property.

2. **C3 + C4 + C7: The unification of frozenness and modularity.** The identification "frozen = disconnected" and the consequent collapse of three therapeutic mechanisms into two (welcoming and unburdening are both re-contextualization at different depths). This is the draft's most distinctive theoretical move -- it takes what appeared to be three separate phenomena and shows they are aspects of one graph-topological property.

3. **C6: Self-qualities as default properties of connected inference.** The specific mapping of each of the 8 C's to a computational property of unimpeded Bayesian inference, with the testable co-occurrence prediction.

4. **C8: Change is topological, not parametric.** The claim that the fundamental operation is structure learning (adding edges), not parameter tuning (adjusting precision), even though the paper's own working thesis is phrased in precision terms. This represents an evolution within the draft itself.

### Everything else is:

- **Imported framework**: AX1-AX8 (active inference, IFS, Chamberlin, reconsolidation, interoception)
- **Definitional work**: D1-D10 (translating IFS terms into active inference notation -- useful but not novel theory)
- **Derived consequences**: I1-I9 (follow logically from the core claims + axioms)

### Key tensions the critique identifies:

- The working thesis says "precision-modulating meta-priors" but the developed argument says "modular subgraphs." The paper needs to decide which is primary (the critique and the draft's own evolution point toward modularity).
- "Precision" is overloaded -- the draft uses it to mean sensory precision, policy precision, learning rate, and coupling strength without disambiguation.
- The Self = balanced-precision regime risks conflating Self-leadership with mere low arousal (dissociation is also "quiet").
- The valence claim (always <= 0) is too strong and not load-bearing for the main argument.
- Reconsolidation is invoked as supporting evidence but the reconsolidation literature itself is contested.
