## IFS-perspective critique

### 1) Your “parts aren’t sub-agents” move is elegant—but you may be underselling what IFS is *doing* clinically

In IFS practice, “treating parts as agents” (with intentions, fears, trust conditions, and relational needs) is not merely a metaphor—it’s part of the mechanism of change. Even if your *mechanistic* claim is “single generative model + precision regimes,” the *therapeutic* stance is intentionally interpersonal: parts negotiate, grant permission, reveal burdens, and update through relationship.

**Suggestion:** keep your mechanistic thesis, but add a paragraph that explicitly separates:

* **Clinical ontology (as-if agentic)**: the stance that makes the method work in vivo.
* **Computational ontology (precision / gating / structure)**: the stance that makes simulations tractable.

That protects you from IFS readers saying “this isn’t IFS,” while preserving your core computational move.

### 2) “Self = balanced precision regime” risks collapsing Self into a merely *low-arousal* state

IFS “Self” isn’t just calm; it’s *Self-leadership*: curiosity, compassion, courage, clarity, etc. Many clients can be calm while still being managerial, dissociated, compliant, or “spiritually bypassed.” From an IFS lens, calm ≠ Self.

**Suggestion:** distinguish at least two different “quiet” regimes:

* **Quiet-protective** (e.g., dissociation, numbing, pleasing): low overt conflict, but still part-led.
* **Self-led**: includes curiosity/compassion + capacity to stay in contact with distress without suppression.

If you only model “Self = low winner-take-all,” you’ll accidentally predict that dissociation is Self-like. Clinicians will flag that immediately.

### 3) Protectors in IFS aren’t just “policies”—they are *trust and permission managers*

Your protectors-as-policy-priors framing is close, but IFS has a signature move: you can’t just “access the exile” because it’s useful; protectors must trust the process and grant permission.

Computationally, that looks less like “a policy” and more like:

* **a gate on information flow** (what is allowed into awareness / working memory),
* **a gate on action** (what the system is allowed to do in session),
* **a learned trust variable** (“is Self present enough?” / “is this context safe enough?”).

You already hint at this with “safety as a hyperprior.” IFS folks will want to see protectors as the ones *computing* and enforcing that safety/permission constraint.

### 4) Unburdening in IFS often includes **retrieving positive qualities**, not only reducing extremes

IFS “unburdening” doesn’t just make a part quieter; it often reveals a part’s innate resourcefulness (playfulness, creativity, healthy assertiveness) once the burden is released.

**Suggestion:** add one sentence to your unburdening definition like:

* “After unburdening, a part often transitions into a new functional role with different preferences/policies—not merely reduced intensity.”

That matters for simulation, because you’ll want observable qualitative regime change (policy repertoire expands, preferences shift, new affordances become selectable).

### 5) Polarization: you’ve got the competition story, but IFS polarization is also a *relational stalemate*

IFS polarization often persists because each polarized protector believes the other is dangerously wrong (and both are protecting something). This is not just oscillation; it’s also **mutual threat modeling**.

**Suggestion:** add a line that polarization includes “each part’s model assigns high risk to the other part’s policy,” which predicts:

* rapid vetoing,
* inability to integrate,
* chronic indecision despite “knowing better.”

---

## Active-inference critique (the more important one)

### 1) “Precision” is overloaded in active inference—your paper needs a disambiguation early

Right now, “parts are precision-modulating meta-priors” is plausible but underspecified, because “precision” can mean (at least) all of these:

* **sensory precision** (likelihood confidence; attention-like effects),
* **state transition precision** (how “sticky” dynamics are),
* **policy precision / expected precision** (temperature on policy selection; exploration–exploitation),
* **learning rate / volatility beliefs** (how updateable parameters are).

You’re implicitly using *several* of these at once (blending, stickiness, firefighter urgency, manager planning, unburdening plasticity). I’d recommend a small “precision taxonomy” box to prevent an active inference reviewer from saying “this is handwavy.”

A nice alignment point: *A beautiful loop* explicitly emphasizes inferential competition and proposes a **hyper-model for precision control** across hierarchical inference layers. ([ScienceDirect][1])
That’s basically the same conceptual slot you’re assigning to “Self-energy,” so you can use it to justify your architecture.

### 2) Your “single generative model” stance is defensible—but simulations may be easier with a **mode variable**

You say: parts are not separate sub-agents with separate models. Mechanistically, I agree you *can* keep one generative model.

But practically, the cleanest implementation is usually:

* one generative model **with a discrete latent “mode” state** (`m ∈ {Self, Manager, Firefighter, Exile, …}`),
* and that mode **selects parameterizations** (or gates message passing) for subsets of A/B/C/E.

This is still *one model*—just one with a switching variable. It buys you:

* clean “blending” = posterior mass concentrates on one `m`,
* “unblending” = posterior over `m` becomes broader / more flexible,
* “polarization” = bistability / limit cycles in `m`.

This mode-variable approach also interfaces beautifully with *A beautiful loop’s* “inferential competition to enter the world model” (your “winner-take-all” story becomes a specific kind of competition/binding). ([ScienceDirect][1])

### 3) Chamberlin’s critique: your draft frames it well, but you can strengthen the “modularity” bridge with *active-inference structure*

Chamberlin’s published article is 2023 (not 2022), and it emphasizes making implicit models explicit so they can be juxtaposed and updated. ([Frontiers][2])

Your current response to Chamberlin is: “maybe modularity vs precision.” The active inference way to sharpen this is:

* **Modularity = factorization / conditional independence assumptions** (a subgraph that doesn’t exchange messages with the rest).
* **Welcoming = adding edges / reopening message passing** (structure learning or graph surgery).
* **Precision can be the *means* by which modularity is enforced** (e.g., extreme sensory attenuation or extreme prior precision can effectively silence contradictory messages).

So you can keep your precision story but say:

> “Parts can be modeled as *modules whose coupling is gated*. Precision is one mechanism of gating, but not the only one.”

That will satisfy people who think “modularity is primary” while preserving your central thesis.

### 4) Valence claim is too strong as written (“always ≤ 0”)

In active inference, affect/valence has multiple competing formalizations. For example, “Deeply Felt Affect” models valence as inferred from the **expected precision of the action model** (subjective fitness), not simply “pragmatic prediction error always negative.” ([MIT Press Direct][3])
There are also newer mappings of free energy to valence/arousal in circumplex-style accounts. ([arXiv][4])

**Suggestion:** soften to something like:

* “Valence tracks trajectories of (expected) free energy / model evidence / expected precision,”
* and then put your preferred definition in a footnote with justification.

That will prevent derailment by affective inference specialists.

### 5) Unburdening as “precision ceiling reduction” is intuitively nice—but it may miss what changes *structurally*

Your own Chamberlin section already points to the core risk: “turning down a number” can sound like parameter tweaking, not representational change.

Here are three active-inference-consistent alternatives that preserve your phenomenology:

#### A) Unburdening as **contextualization** (latent context inference)

A strong computational match is:

* trauma memory is not erased; it becomes *context-bound*.

There’s a whole learning/memory literature modeling this as **latent context inference controlling expression and updating of memories**. ([Cell][5])
This maps very cleanly to “you formed that belief then, and now the system knows ‘then’ ≠ ‘now’.”

In this view:

* “blending” = mis-inference of context (“this is *that* situation again”),
* “unburdening” = learning a new context representation that prevents global takeover.

#### B) Unburdening as **structure learning** (new state space / new explanatory variable)

Instead of lowering a ceiling, you add a higher-level explanation that absorbs what the exile was doing. This resonates with Chamberlin’s “knowledge to the system” and with active inference work that distinguishes learning of **states/parameters/structure**. ([Frontiers][6])

#### C) Unburdening as **updating beliefs about volatility / controllability**

Trauma often installs beliefs like “danger can spike any time” (high volatility), which rationally favors fast, rigid policies. Updating volatility beliefs can reduce the need for extreme protectors without positing “precision got turned down.”

### 6) Therapist modeling: you’ll get more mileage if you treat therapy as **social active inference**

You already hint at “therapist as external precision modulator.” That’s true, but you can sharpen it:

* therapist provides **exteroceptive cues of safety**,
* co-regulates arousal/interoception,
* and (crucially) helps the client infer “I am seen and not alone,” which changes policy selection and epistemic openness.

There are recent integrative proposals explicitly tying psychodynamics/relational self-processes to predictive processing/active inference (e.g., Active Intersubjective Inference). ([Frontiers][7])

This is also where you can connect to IFS permission dynamics: protectors are much more willing to relax when the system infers “safe other + Self present.”

---

## Other viable ways to model “parts” (that still respect your aims)

### 1) Switching-mode generative model (recommended for simulation)

**Core idea:** “part” = latent mode `m` that selects parameter sets (or message-passing routes).

Pros:

* easy to simulate blending/unblending/polarization,
* naturally produces bistability and hysteresis,
* aligns with “inferential competition” framing in *A beautiful loop*. ([ScienceDirect][1])

Cons:

* looks like “multiple models,” so you’ll need one sentence clarifying “one hierarchical model with modes ≠ separate homunculi.”

### 2) Factor-graph modularity / gated message passing (best match to Chamberlin)

**Core idea:** parts are semi-isolated subgraphs; protectors gate edges.

Pros:

* makes “knowledge in the system but not to the system” literal,
* welcoming = adding edges / restoring coupling.

Cons:

* more implementation complexity (but very elegant if your library supports factor graphs/message passing).

### 3) Parts as priors over policies across temporal depth (your manager/firefighter split, formalized)

Managers = deep policies; Firefighters = shallow reflex-like policies.
You can implement depth differences without heavy math by literally giving them different planning horizons and different weightings of immediate vs long-run expected free energy.

Pros:

* captures your “time horizon” story cleanly.
  Cons:
* doesn’t fully capture “exile as state of the self” unless you add an interoceptive/identity layer.

### 4) Parts as attention/precision controllers (your original thesis, but made explicit)

If you keep “part = precision hyperprior cluster,” I’d recommend you explicitly map:

* exiles → interoceptive likelihood precision + self-belief priors,
* firefighters → sensory attenuation + immediate action policy precision,
* managers → policy priors/habits + high confidence in long-horizon avoidance.

Pros:

* matches your writing now.
  Cons:
* reviewers may push back: “precision where?” unless you disambiguate.

---

## Simulation guidance that matches your current outline (minimal but expressive)

If your goal is “a first simulation that demonstrates IFS-like dynamics,” I’d build a toy model with:

### Hidden states

* **external:** dog present / ambiguous cue / safe street context
* **internal:** arousal/interoceptive state; attachment/safety state
* **mode:** {Self, Manager, Firefighter, Exile}

### Observations

* ambiguous visual cue (dog-ish)
* interoceptive cue (heart rate / tension)
* therapist cue (warmth/attunement vs neutral)

### Policies

* approach, keep walking, cross street, freeze/run, seek reassurance, dissociate/attenuate sensations

### What you measure

* posterior over `mode` (blending = collapse)
* policy entropy / policy precision
* time-to-recover after trigger (stickiness)
* degree of sensory attenuation (if you implement it)
* generalization: does “dog-ish” stop causing global avoidance after “therapy”?

### How “therapy” enters

Do it in two stages:

1. **welcoming:** increase coupling / reduce attenuation so exile content becomes reportable
2. **unburdening:** either (a) context learning, (b) structure update, or (c) volatility update

This will let you demonstrate the core clinical story without committing to one mechanistic interpretation too early.

---

## Resource & concept recommendations (high yield for your paper + sims)

### Directly relevant

* **Chamberlin’s coherence therapy active inference model** (published Jan 2023). ([Frontiers][2])
* **A beautiful loop** (2025): inferential competition, Bayesian binding, hyper-model for precision control. ([ScienceDirect][1])
* **Affective inference / valence in active inference**: “Deeply Felt Affect” and related work. ([MIT Press Direct][3])
* **Contextual inference in learning and memory** (very relevant to reconsolidation-like effects without overclaiming “erasure”). ([Cell][5])

### Useful for specific sections you already have

* **Active inference + PTSD / trauma as hyperprecise priors** (good for your exile/protector motivation). ([ScienceDirect][8])
* **Active inference accounts of selective attention / precision control** (to ground “precision = attention” more carefully). ([ScienceDirect][9])
* **Therapy as active inference / communication** (bridge to therapist modeling). ([Frontiers][10])
* **Relational / psychodynamic integration with predictive processing** (helps your dyadic therapy framing). ([Frontiers][7])

### Reconsolidation: include a caution note (worth doing)

If you lean on reconsolidation, it’s worth acknowledging that there are serious debates about mechanism and interpretation in the reconsolidation literature. ([Springer][11])
You can still use reconsolidation as an *inspiration*, but show you’re not making “MR explains everything” claims.

### IFS evidence base: phrase it as “emerging”

If you keep “empirically supported,” you’ll be safest calling it an **emerging evidence base** with pilot studies and growing research—plus acknowledging critiques about popularity outpacing evidence. ([Taylor & Francis Online][12])

---

## Two concrete edits that would strengthen the paper immediately

1. **Add a 1-page “precision & gating taxonomy”**
   Define 3–5 precisions you mean (sensory, policy, learning/volatility, coupling/message passing), and then reuse those terms consistently.

2. **Reframe your thesis slightly to absorb Chamberlin without losing your key move**
   Instead of “parts are precision-modulating meta-priors” *alone*, try:

> “Parts are regimes of inference implemented by precision control **and** gated coupling (modularity). IFS works by increasing access/coupling (welcoming), then enabling context-embedding/structural revision (unburdening), within a Self-led precision-control regime.”

That makes your model *strictly more general* and will read as less brittle to both IFS and active inference reviewers.

If you want, I can also suggest a small set of figures that would make the paper feel “real” without math (e.g., a mode-switching diagram, a coupling/gating diagram for modularity, and a before/after phase portrait for polarization).

[1]: https://www.sciencedirect.com/science/article/pii/S0149763425002970?utm_source=chatgpt.com "A beautiful loop: An active inference theory of consciousness"
[2]: https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2022.955558/full?utm_source=chatgpt.com "The Active Inference Model of Coherence Therapy - Frontiers"
[3]: https://direct.mit.edu/neco/article/33/2/398/95642/Deeply-Felt-Affect-The-Emergence-of-Valence-in?utm_source=chatgpt.com "Deeply Felt Affect: The Emergence of Valence in Deep Active Inference ..."
[4]: https://arxiv.org/html/2407.02474v1?utm_source=chatgpt.com "Free Energy in a Circumplex Model of Emotion - arXiv.org"
[5]: https://www.cell.com/trends/cognitive-sciences/fulltext/S1364-6613%2822%2900265-0?utm_source=chatgpt.com "Contextual inference in learning and memory - Cell Press"
[6]: https://www.frontiersin.org/journals/network-physiology/articles/10.3389/fnetp.2025.1521963/full?utm_source=chatgpt.com "Frontiers | From pixels to planning: scale-free active inference"
[7]: https://www.frontiersin.org/journals/psychiatry/articles/10.3389/fpsyt.2025.1630858/full?utm_source=chatgpt.com "Active inference and psychodynamics: a novel integration with ..."
[8]: https://www.sciencedirect.com/science/article/pii/S0149763419311029?utm_source=chatgpt.com "Rethinking post-traumatic stress disorder – A predictive processing ..."
[9]: https://www.sciencedirect.com/science/article/pii/S0149763421004206?utm_source=chatgpt.com "Active inference, selective attention, and the cocktail party problem ..."
[10]: https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2022.828952/full?utm_source=chatgpt.com "An Active Inference Account of Touch and Verbal Communication in Therapy"
[11]: https://link.springer.com/content/pdf/10.3758/s13423-022-02173-2.pdf?utm_source=chatgpt.com "Appraising reconsolidation theory and its empirical validation - Springer"
[12]: https://www.tandfonline.com/doi/pdf/10.1080/13284207.2025.2533127?utm_source=chatgpt.com "Exploring the evidence for Internal Family Systems therapy: a scoping ..."
