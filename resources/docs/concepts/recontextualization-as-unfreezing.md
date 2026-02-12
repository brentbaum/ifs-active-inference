# Re-contextualization IS Unfreezing: Unifying the Mechanisms of IFS Change

*Analysis note — February 2026*

---

## Summary

The three-mechanism framework (Self-energy increase / Welcoming / Unburdening) can be reduced to two. "Welcoming subconscious parts" (breaking modularity, context-embedding) and "Unburdening" (restoring plasticity, unfreezing priors) are the same mechanism operating at different depths, not two categorically distinct operations.

---

## The Core Argument

### What makes a prior "frozen"?

The three-mechanisms doc says it's a meta-belief ("this belief is essential to who I am") plus a "closed learning window." But modularity itself explains frozenness without needing a separate mechanism.

A modular schema is a **disconnected subgraph** in the generative model's factor graph. It has no edges connecting it to context variables. Therefore:

1. It generates predictions without conditioning on current context
2. No context-sensitive prediction errors can reach it
3. Standard Bayesian updating cannot operate on it
4. It appears "frozen" — not because of a special lock, but because **no new information reaches it**

The "closed learning window" isn't a separate property layered on top of modularity. It's a **consequence** of the modularity itself. A walled-off belief can't update for the same reason a disconnected node in a factor graph can't receive messages: there are no edges.

### What re-contextualization actually does

When you reconnect the isolated subgraph to the broader network, several things happen simultaneously (not sequentially):

1. **New information pathways open.** The belief connects to nodes carrying contradictory evidence (current safety, adult capacity, secure relationships).

2. **Context tags attach.** "This belief was formed THEN, in THAT situation" — the schema acquires temporal and situational metadata it never had because it was formed under stress with "minimal parameters, no consideration of context" (Chamberlin, p12).

3. **The belief becomes an object rather than a lens.** You can see it rather than see through it. This is the shift from "I AM scared" to "a part of me carries fear from when I was 7." That shift IS re-contextualization — it's what it looks like from the inside when a subgraph gets embedded in a larger graph.

4. **Prediction errors can now propagate.** Because the belief now conditions on context, the standard active inference learning machinery can operate. "I predicted danger, but context says safe" becomes a computable prediction error for the first time.

All four of these together ARE what "unfreezing" means. Reconnecting the subgraph IS reopening the learning window.

---

## Clinical Evidence for the Unification

### Chamberlin's >50% Discovery-only resolution

For those cases, re-contextualization alone generates enough prediction error to update the beliefs. The moment the schema can "see" current context, the discrepancy between "I'm in danger" and "I'm 35, I'm safe, I have resources" is so large that beliefs update immediately.

### IFS therapists report the same convergence

When the exile is witnessed and "shown your life now," the burden often releases *during the witnessing*. There's no sharp boundary between "I made it conscious" and "it let go." The witnessing IS doing the work.

### This explains several phenomena

- **Why witnessing must precede unburdening**: you can't send information to a disconnected node. Integration is prerequisite because integration IS the mechanism.
- **Why burdens are "given to elements" rather than replaced**: the ritual marks the *release of isolation*, not content substitution. The belief doesn't need to be replaced — it needs to be reconnected, at which point normal inference handles the rest.
- **Why parts "look different" afterward**: a previously disconnected subgraph, once reconnected, gets reorganized by the information flowing through it. The frozen structure dissolves because the conditions that maintained it (isolation) are gone.
- **Why unburdening is quick but integration takes time**: reconnection is discrete (graph topology change), but the actual belief updating that follows requires subsequent experience flowing through the new edges.
- **Why protectors relax after exile unburdening**: the exile's beliefs are no longer dangerous frozen attractors — they're now normal updatable priors participating in inference.

---

## What Varies Is Depth, Not Kind

If welcoming and unburdening are the same mechanism, why do some cases resolve with Discovery alone while others need explicit unburdening? It's a spectrum governed by two variables:

### 1. Consolidation strength (Dirichlet concentration)

How strong is the prior? A mildly consolidated belief updates easily once reconnected — ordinary prediction errors suffice. A strongly consolidated belief (formed under extreme stress, reinforced over years) needs *vivid, high-precision contradictory evidence* (Chamberlin's juxtaposition) even after the channel opens.

### 2. Hierarchical depth of isolation

Some schemas are modular at one level — walled off from context but not wrapped in self-referential protection. Others have an additional layer: a higher-order variable encoding "this schema is definitional to my identity." This is the meta-belief: "this IS who I am."

### The continuum

| Depth | What's happening | Clinical presentation | Resolution |
|-------|-----------------|----------------------|------------|
| **Shallow modularity** | Schema isolated from context, moderate consolidation | Part steps forward easily, burden feels "ready" | Discovery alone (~50%+) |
| **Deep modularity** | Schema isolated + strongly consolidated | Part accessible but beliefs feel immovable | Discovery + juxtaposition (vivid mismatch through the new channel) |
| **Hierarchical identity lock** | Schema isolated + identity-level meta-belief wrapping it | "I can see the belief but I can't let it go — it's who I am" | Discovery + explicit unburdening targeting the meta-level variable |

The IFS protocol (witness, ask permission, access exile, witness exile, unburden) isn't three separate mechanisms — it's a **progressive deepening of the same reconnection operation**, moving through layers of modularity until the belief can participate in normal inference.

---

## Active Inference Formalization

### Factor graph representation

```
Frozen state:
  Schema subgraph S = {nodes n_1...n_k}
  Context subgraph C = {nodes c_1...c_m}
  Edges between S and C: empty set
  -> No messages flow from C to S
  -> S cannot generate context-dependent prediction errors
  -> S's parameters are fixed (effectively eta = 0, but not by design -- by isolation)

Re-contextualization:
  Add edges E_new between S and C (structure learning)
  -> Messages now flow: C -> S
  -> Context-dependent prediction errors become computable
  -> Standard learning (Dirichlet updates) can operate on S's parameters
  -> Prior "thaws" -- not because we flipped a plasticity switch, but because
     information can now reach it

Degree of thawing depends on:
  1. |E_new| -- how many edges were added (breadth of reconnection)
  2. precision(messages via E_new) -- how vivid the contradictory evidence is
  3. concentration(S's Dirichlet params) -- how much evidence needed to move the prior
  4. depth(identity wrapping) -- whether higher-level nodes also need reconnection
```

### Implications for the Chamberlin simulation

The existing Chamberlin model's three-state `schema_mode` (implicit, explicit, labile) implicitly treats "making accessible" and "making updatable" as separate state transitions. Under the unified view:

- `schema_mode` governs **connectivity** (edge presence/absence between schema and context subgraphs)
- **Learning rate** isn't a separate switch — it's a natural consequence of whether prediction errors can reach the schema
- The `labile` state isn't needed as a separate construct. Updating happens whenever (a) edges exist AND (b) prediction error exceeds the prior's consolidation strength

Simulation prediction: resolution speed is a function of `prior_consolidation_strength x context_mismatch_magnitude^-1`, not of a separate plasticity parameter.

---

## The Revised Two-Mechanism Model

The three-mechanism model becomes two:

1. **Self-energy** = global precision gating (enables the work; system-wide parameter)
2. **Re-contextualization** = progressive reconnection of modular subgraphs (IS the work, including what was previously called "unburdening")

Self-energy remains distinct because it's a system-wide parameter affecting the probability of any part achieving winner-take-all dominance. It facilitates reconnection (you can't do graph surgery while fully blended) but isn't reconnection itself.

---

## References

- Chamberlin, D. E. (2022). "The Active Inference Model of Coherence Therapy." *Frontiers in Human Neuroscience*, 16, 955558.
- Contextual inference in learning and memory (Cell, 2022) — latent context inference controlling expression and updating of memories
- Karmiloff-Smith, A. (1992). *Beyond Modularity: A Developmental Perspective on Cognitive Science.*

---

*Last updated: February 2026*
