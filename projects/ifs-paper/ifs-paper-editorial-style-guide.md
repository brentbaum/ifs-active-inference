# Editorial and Style Guide
## *Self-Energy, Witnessing, and the Revision of Part Beliefs*

This is the manuscript's canonical editorial guide. It merges the original drafting rules with the v2 collaborator review; where the two differed, v2 governs. Its central purpose is to keep the paper fluent in three languages without blurring them:

1. IFS phenomenology and clinical practice;
2. formal active-inference mechanisms;
3. the paper’s deliberately limited bridge vocabulary.

The governing rule is:

> **Describe the lived phenomenon in IFS terms, specify the computational operation in active-inference terms, and introduce a bridge term only when it maps clearly between them and earns a distinctive prediction.**

---

## 1. Preserve three distinct registers

### 1.1 IFS / phenomenological register

Use this register to describe what the person or clinician encounters:

- a part is blended;
- a protector fears that contact will overwhelm the system;
- a young part expects to be alone;
- the client speaks *for* rather than *from* a part;
- Self remains with the part.

Do not force formal vocabulary into every phenomenological sentence. The clinical description should remain recognizable to an IFS reader.

### 1.2 Formal computational register

Use this register only when a sentence refers to a specified formal object or operation:

- posterior inference over a latent state;
- prior or posterior precision;
- effective precision after hyper-model modulation;
- conditional dependence in the generative model;
- likelihood or transition learning;
- policy selection under expected cost;
- epistemic action;
- latent-cause inference;
- context inference;
- Bayesian model comparison or reduction.

A computational noun should identify an object in the model. A computational verb should identify an operation the model can perform.

### 1.3 Bridge register

The paper may introduce a small set of terms that connect IFS experience to the formalism. The bridge vocabulary should remain closed and stable.

Current core bridge terms:

- **frozen identity**
- **uncaptured inference**
- **context-held activation**
- **Self-position**
- **root-relevant evidence**
- **relational prediction error**
- **melting** — descriptive summary only, not a separate latent mechanism

Every bridge term must do three things:

1. identify a recurring phenomenon not already named adequately by IFS or active inference;
2. map onto a specified formal relation or operation;
3. yield a distinctive consequence, contrast, or prediction.

If a proposed term cannot meet all three conditions, use ordinary prose instead.

### 1.4 Interpretive language

Some clinically meaningful correspondences are interpretations rather than implemented mechanisms:

- retrieval as context-indexed redescription enacted;
- unburdening as an invitation to selective release;
- imagery as an interface for joint representation;
- a do-over as resampling an alternative policy and outcome.

Mark these explicitly:

> “can be interpreted as,” “offers a candidate account,” “may function as,” or “is consistent with.”

Do not write interpretive correspondences as identities.

---

## 2. Use an internal provenance tag during editing

During drafting, privately label each nontrivial construct:

- `[IFS]` — term or mechanism belonging to IFS;
- `[AIF]` — established active-inference or Bayesian construct;
- `[BRIDGE]` — construct introduced by this paper;
- `[INTERPRETIVE]` — proposed correspondence;
- `[EMPIRICAL]` — prediction about people or therapy;
- `[SIM]` — result within an authored construction.

These tags need not appear in the submitted manuscript. They are an audit tool.

A sentence containing several untaggable constructs is likely “computational storytelling”: the prose sounds mechanistic but does not specify which theory or formal operation carries the claim.

---

## 3. Make every mechanism auditable

### 3.1 Nouns must map to objects

Ask of every computational noun:

> What is this in the generative model, variational posterior, policy model, or learning rule?

Examples:

| Phrase | Required clarification |
|---|---|
| “self-state root” | A shared latent state on which multiple world, policy, or outcome predictions depend |
| “precision field” | A posterior or forecast over channel-specific precision variables |
| “protector trust” | Specified forecasts over contact outcome, co-protection, and partner policy |
| “gate” | The current consequence of protector policy selection, not a separate hidden entity |
| “context” | A latent variable or model index controlling where an organization applies |
| “bundle” | A joint or conditionally dependent organization of self, world, policy, and outcome variables |

### 3.2 Verbs must map to operations

Audit these verbs especially carefully:

> becomes, carries, assigns, reaches, registers, opens, freezes, melts, uses, knows, holds

Prefer the explicit operation whenever the sentence is making a computational claim.

| Avoid as the only explanation | Prefer |
|---|---|
| “Overwhelm becomes small.” | “Observations under high error, failed action, and absent support increase belief in a low-capacity self-state.” |
| “Evidence reaches the root.” | “The observation likelihood depends on the shared self-state and retains enough effective precision to update its posterior.” |
| “The part registers care.” | “Relational observations update the part’s expectations about contact, support, or conditional acceptance.” |
| “The system assigns the event to a new cause.” | Specify whether the agent selects an existing latent cause or expands the model with a new cause. |
| “The bundle determines the present.” | “Fast inference proceeds within the high-precision identity context, while slower structural learning remains capable of revising it.” |
| “The gate opens.” | “Updated forecasts change the expected-cost comparison, making a contact policy preferable.” |
| “The part melts.” | “Root beliefs revise, context dependence changes, and the compulsory coupling loses model evidence.” |

Evocative summaries may follow the formal explanation. They should not replace it.

### 3.3 Distinguish latent-cause inference from model expansion

These are different claims:

- **Latent-cause inference:** the model already contains candidate causes and assigns posterior probability among them.
- **Model expansion:** the system creates or recruits a new cause or model component.
- **Structure learning:** the system changes dependencies or model class.

Use the term matching the actual model. Do not say “creates a new cause” if the implementation only selects from authored alternatives.

---

## 4. Resolve the “hypothesis versus architecture” issue with timescales

Do not say that the frozen bundle literally ceases to be a model or hypothesis.

Preferred formulation:

> **Formally, the bundle remains a model. Functionally, at the timescale of ordinary inference, its precision and position in the dependency structure make inference proceed within it rather than repeatedly compare it with live alternatives. At a slower learning or structural timescale, it remains revisable.**

This permits all three claims to coexist:

- present evidence still reaches the organization;
- ordinary evidence usually produces little change;
- sustained, well-admitted evidence can alter its parameters or structure.

Use “functions as architecture” as phenomenological or timescale-relative shorthand, not as an unsupported ontological transition.

---

## 5. Let sections have one job

### Introduction

The Introduction should establish the explanandum and claim spine, not teach the whole theory.

Keep:

- *I am afraid* versus *a part of me is afraid*;
- the dog example;
- the basic IFS distinction;
- one short active-inference bridge;
- one sentence each for C1, C2, and C3;
- scope and simulation status.

Move detailed material to its proper section:

- four-element bundle → §3;
- formation dynamics → §4;
- Self-position and precision hyper-model → §6;
- dominance–depth distinction → §7;
- loving contact, inquiry, and root evidence → §8;
- sufficiency wager and losing conditions → Discussion;
- contemplative implications → Discussion.

Recommended compact claim spine:

> We propose that a burdened part is a frozen identity organization linking self, world, action, and expected outcome (C1). Self-energy is reconstructed as the inferential regime in which that organization can remain active without transparently controlling the wider system (C2). Within that regime, present evidence can update the identity at the bundle’s root, producing a broader transfer structure than cue-level correction alone (C3).

### §2 — IFS in Its Own Terms

Use IFS language first. Do not prematurely translate every construct computationally.

Place the translation table at the end of §2. Signpost it briefly from the Introduction.

### §3 — Architecture of Frozen Identity

Define:

- the four-element organization;
- the self-state as shared parent or root;
- the characteristic whole-world signature;
- the phase/timescale meaning of freezing.

### §4 — Formation and Persistence of Frozen Identity

Define:

- overwhelm;
- low control;
- latent-cause or structure-learning claim;
- precision increase;
- policy-mediated evidence censorship;
- acute versus gradual routes, with their differing evidential standing.

### §5 — Protective System

Derive only what the architecture supports:

- locally intelligible policy;
- protector as identity-bearing organization;
- exiling as a conditional consequence of policy;
- gate as policy output;
- layered or networked protection.

Keep manager/firefighter developmental stories explicitly hypothetical unless formally supported.

### §6 — Self, Self-Energy, and Self-Position

Separate:

- Self-capacity;
- Self-energy as regime;
- Self-position as present self-context;
- care as an additional valuational condition, not a consequence of precision alone.

### §7 — Capture and Context-Held Activation

Formalize:

- the five-channel field;
- local dominance versus global epistemic depth;
- the four regimes;
- context-held activation;
- witnessing as its sustained clinical form.

### §8 — Relational Revision

Maintain the causal sequence:

1. access is not revision;
2. evidence at the identity root;
3. protector trust and permission;
4. context-indexed redescription;
5. reduction and unburdening;
6. descent through the protective system.

### Computational section

Explain the common model once. Organize results under C1, C2, C3, and G—not by experiment chronology.

For each result use:

1. theoretical commitment;
2. assay;
3. decisive control;
4. characteristic result;
5. theoretical update or restriction.

### Discussion

Organize around:

- what formalization changed;
- relation to IFS orthodoxy;
- discriminating empirical commitments;
- boundary conditions and losing conditions;
- concise conclusion.

Do not end with a development backlog.

---

## 6. Use the paragraph sequence: phenomenon → formalization → consequence → standing

A strong theory paragraph usually performs these functions in order:

1. **Phenomenon:** what happens experientially or clinically?
2. **Formalization:** which formal variables or dependencies represent it?
3. **Consequence:** what distinctive pattern follows?
4. **Standing:** is this implemented, interpretive, architecture-conditional, or empirically open?

Example:

> Clinically, a burdened part reactivates as a whole perspective rather than a single proposition. We represent this as a dependent organization of self-state, world-state, policy, and expected outcome, with several predictions conditioned on a shared self-state. This architecture predicts that revising the shared state should transfer across untreated cues more broadly than revising one cue likelihood. The current simulations establish that consequence within an authored shared-root construction; they do not establish that human parts have this architecture.

Not every paragraph needs all four sentences, but every conceptual unit should make the sequence recoverable.

---

## 7. Limit the vocabulary budget

### Terms that may remain as named bridge constructs

- frozen identity
- uncaptured inference
- context-held activation
- Self-position
- root-relevant evidence
- relational prediction error
- melting, with an explicit “descriptive bridge term” guard

### Terms to use cautiously or replace

- **collapsed reflexivity** — retain only if explicitly defined as failed higher-order representation of the current state; otherwise use plain language;
- **local control model** — replace with “identity-conditioned generative submodel,” “recurrently activated identity organization,” or a direct graph description;
- **maximal write / minimal test** — use as a memorable summary after specifying precision increase and lack of discriminating action;
- **joint representational event** — keep only when immediately unpacked as concurrent inference over named states and observations;
- **care availability** — ordinary prose condition, not a formal latent variable;
- **unfinished inference** — temporal interpretation, not a separate computational process.

Do not create a new named mechanism merely by capitalizing a phrase.

---

## 8. Introduce mathematics only when it resolves ambiguity

Equations should perform explanatory work.

### Early formal anchor 1: bundle dependency

Show the graph or factorization that makes “root” computationally meaningful. For example:

\[
p(s,w,\pi,o)
=
p(s)\,
p(w\mid s)\,
p(\pi\mid s,w)\,
p(o\mid s,w,\pi).
\]

Use the factorization actually implemented or defended; do not include a decorative equation that the model later violates.

### Early formal anchor 2: formation and control

Define overwhelm and control in terms that can later be implemented:

- overwhelm as poor model fit or prediction error relative to expected uncertainty and available model capacity;
- control as expected differentiation among policy-conditioned outcomes or information gain.

### Equation rules

- Introduce every symbol in the sentence before or after the equation.
- State the clinical meaning immediately afterward.
- Keep notation stable across theory, figures, simulations, and appendices.
- Do not add equations simply to make prose appear computational.
- If an equation is only schematic, label it schematic.

---

## 9. Make figures part of the argument

Every figure needs:

1. a number;
2. a descriptive title;
3. a caption explaining what is represented;
4. the claim or distinction it clarifies;
5. a boundary on interpretation where needed.

Caption template:

> **Figure X. [Descriptive title].** [What variables, states, or relations are shown.] [What theoretical distinction the figure clarifies.] [What the figure should not be read as establishing.]

Example:

> **Figure 3. Formation and persistence of frozen identity.** (A) Conceptual space defined by overwhelm and control; dissociative attenuation occupies the high-overwhelm, low-control region. (B) Once formed, protective policies reduce access to discriminating observations, preserving the identity organization through a closed action–evidence loop. Region boundaries are schematic rather than empirically estimated.

Figure rules:

- Refer to a figure in the prose before it appears.
- Group managers and firefighters visually under **Protectors**.
- Show dissociative attenuation as a region within the formation space, not as an unrelated mechanism.
- Mark protective topology as illustrative and many-to-many.
- Do not draw a sharp boundary unless it is formally or empirically justified.
- Do not let a diagram imply that an interpretive mechanism has been derived.
- Use the same names in figures, prose, equations, and code.

---

## 10. Match verbs to epistemic standing

### Theory and reconstruction

Use:

- propose
- reconstruct
- model
- define
- distinguish
- interpret
- predict

### Simulation results

Use:

- the construction exhibits
- the assay produces
- within the authored model
- the intervention removes
- the result is consistent with
- the result supports the consequence of
- the result is architecture-conditional

Avoid:

- proves
- validates IFS
- confirms the psychological mechanism
- demonstrates that people work this way

### Human empirical claims

Use:

- predicts
- would be supported if
- would be weakened if
- would count against the account if

### Adjacent biology or contemplative theory

Use:

- is compatible with
- offers a candidate implementation
- suggests a possible extension
- neighboring traditions propose

Never allow “is compatible with” to become evidence that the mechanism is true.

---

## 11. Preserve terminology guards across paper and code

Use these distinctions consistently:

- **organization** — bundle, couplings, precisions, field profile;
- **carrier** — independently parameterized substrate;
- **configural** — statistical dependence within a representation;
- **relational** — interpersonal or intrapersonal relationship;
- **witnessing** — contact with vulnerable material;
- **befriending** — protector contact;
- **trust** — learned forecast;
- **permission** — policy choice under that forecast;
- **gate** — policy consequence, not another entity;
- **Self-energy** — regime;
- **Self-position** — present self-context;
- **care** — valuational condition not currently derived.

Do not rename a construct after seeing results. Do not use “relational” merely to mean “joint” or “configural.”

---

## 12. Define once; refer back lightly

A term should have one canonical definition.

Afterward:

- use the same wording or a short form;
- do not redefine it from a different angle in every section;
- avoid repeated mini-summaries;
- use cross-references only when they help navigation.

Prefer:

> “Section 8 returns to imagery as a possible interface through which the active bundle and present relational observations become jointly available.”

Avoid:

> “Why this works is a question the account must eventually answer (§8).”

A cross-reference should say what the later section contributes, not narrate the author’s deferred obligation.

---

## 13. Sentence-level style

### Introduce one difficult idea at a time

When a paragraph introduces a new bridge term, keep surrounding sentences simple.

Avoid stacking:

- a new IFS term;
- a new active-inference term;
- a new bridge construct;
- and a prediction

inside one sentence.

### Preserve evocative sentences, then unpack them

The paper’s memorable sentences are an asset:

> “The inference never closed.”

> “The unfinished moment meets the present.”

> “Contemporary tactics serving an old identity.”

Keep them, but place the formal account immediately before or after.

### Prefer concrete subjects

Prefer:

> “The posterior over the shared self-state changes…”

over:

> “Revision happens…”

Prefer:

> “The protector’s expected-cost comparison favors contact…”

over:

> “The gate opens…”

### Control sentence length

Use shorter sentences around:

- definitions;
- corrections;
- caveats;
- model standing.

Longer rhythmic sentences can remain in phenomenological openings and conclusions.

### Use phenomenological beliefs consistently

Italicize model content:

- *I am helpless.*
- *No one will come.*
- *This will overwhelm us.*

Do not alternate unpredictably among italics, quotation marks, and bare text.

### Introduce the clinical frame before “client”

Use “person” in the opening phenomenology. Introduce “client” when the text first enters a therapy encounter.

### Spell out specialized shorthand once

Write “the eight Cs” on first use before “8 Cs,” if the shorthand is retained.

### Preserve the manuscript's voice

- **Write in the Beautiful Loop register, not outline compression.** Begin difficult moves in lived experience, then restate the mechanism in formal language. Let memorable metaphors have room, vary sentence length, and keep scene-setting sentences to one idea each.
- **State; do not persuade.** Name a construct and show its work. Cut announcements, defensive anticipation, and checklists of rebuttals. Use “we propose” for genuinely novel claims.
- **Describe capture from inside.** A transparent part-state does not feel like a remembered age or a visible transition between models. It feels like present threat, incapacity, and urgency. The wider vantage appears retrospectively or when a Self-position becomes available.
- **Use parataxis for scenes and restrained hypotaxis for theory.** Clinical events should arrive in experiential order. Formal prose may subordinate clauses where the dependency is the claim, but it should still land on a short declarative sentence.
- **Triangulate with adjacent traditions; do not lean on them.** Gendlin, March, object relations, contemplative theory, and neighboring clinical models can provide independent bearings. Distinguish what they claim, what this paper borrows, and what this paper adds.
- **Do not attack a literature the paper borrows from.** State the explanandum positively and make comparative claims only where the relevant alternative has been represented fairly.
- **Reconstruct IFS where the architecture licenses reconstruction.** Prefer one formal operation that explains several clinical loci over a list of translated labels. When a clinical ordering or mechanism has not been implemented—or an implementation deadlocked—present it as a candidate, conditional corollary, or open problem rather than as something derived.
- **Use plain definitional asides.** Prefer “When we say X, we mean…” to clever language-policing.
- **Remove metadiscourse, triumphal landings, and editorializing intensifiers.** Sentences should be about the mind, model, evidence, or clinical encounter—not about what the paper is about to do or how striking its own result is.
- **Cross-reference only to aid navigation.** A reference should name what the destination contributes. Do not use pointer tags as substitutes for restating the claim or its support.

---

## 14. Tables should compress, not duplicate

Use tables when they reduce conceptual load:

- IFS term → computational reconstruction;
- claim → mechanism → prediction → standing;
- dominance × depth;
- trust forecast → evidence → expected transfer;
- theory revision forced by simulation.

Do not restate the complete table in surrounding prose.

Every table needs a caption that says whether it is:

- a definition;
- a conceptual taxonomy;
- a summary of results;
- or an interpretive mapping.

---

## 15. Citation discipline

At first use, distinguish clearly between:

- what the cited source claims;
- what the present paper borrows;
- what the present paper adds.

Example:

> Gendlin describes structure-bound experience as failing to change through contact with present detail. We reconstruct that phenomenological contrast through precision and context-sensitive updating; the identity-root claim is our addition.

Do not cite an active-inference paper as if it directly supports an IFS-specific clinical claim unless it actually does.

Verify every citation that carries a load-bearing mechanism, especially:

- latent-cause inference;
- model expansion;
- Bayesian model reduction;
- Beautiful Loop Theory;
- Self-in-context models;
- compassion and secure-base accounts;
- reconsolidation;
- physiological shutdown.

---

## 16. Editorial workflow

### Pass 1 — Claim architecture

For every paragraph, mark whether it serves:

- C1
- C2
- C3
- G
- scaffolding
- empirical prediction
- interpretive extension

If it serves none, cut or relocate it.

### Pass 2 — Register and provenance

Tag every important term `[IFS]`, `[AIF]`, `[BRIDGE]`, `[INTERPRETIVE]`, `[EMPIRICAL]`, or `[SIM]`.

Resolve any untaggable term.

### Pass 3 — Verb audit

Search for:

- becomes
- reaches
- registers
- carries
- assigns
- opens
- freezes
- melts
- knows
- holds

For each, decide whether to retain it as phenomenology or replace it with a formal operation.

### Pass 4 — Placement and repetition

Ask:

- Is this introduced before the reader needs it?
- Is it defined again later?
- Does it belong in Discussion rather than the claim spine?
- Is it a secondary implication receiving central rhetorical weight?

### Pass 5 — Epistemic standing

Label every result internally as:

- analytic consequence;
- construction;
- causal intervention within a construction;
- model-discrimination result;
- architecture-conditional;
- interpretive;
- empirically open;
- failed.

Adjust verbs accordingly.

### Pass 6 — Figure and table audit

Check:

- numbering;
- captions;
- terminology;
- textual callouts;
- whether the visual implies more than the evidence supports.

### Pass 7 — Compression

Cut:

- repeated definitions;
- deferred-obligation cross-references;
- taxonomies that do not alter a claim;
- future-work catalogues;
- caveats repeated in every section.

Preserve:

- the lived phenomenon;
- the formal relation;
- the discriminating consequence;
- the honest limitation.

---

## 17. Final paragraph checklist

Before accepting a theory paragraph, ask:

- What register is each sentence in?
- Is every bridge construct already defined?
- Does every computational term map to a formal object?
- Does every mechanistic verb map to an operation?
- Is the causal direction clear?
- Is this a theory claim, simulation result, interpretation, or human prediction?
- Does the paragraph make a distinctive prediction or merely retell the phenomenon?
- Is any secondary idea competing with C1–C3 or G?
- Could the same point be said with fewer new terms?
- Is the sentence beautiful **and** computationally accountable?

The target style is:

> **Phenomenologically faithful, computationally explicit, editorially sparse.**
