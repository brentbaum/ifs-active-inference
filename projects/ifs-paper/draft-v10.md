
# Self-Energy, Witnessing, and the Revision of Part Beliefs
## An Active Inference Account of Internal Family Systems

## Abstract

Internal Family Systems is a widely adopted multiplicity-of-mind framework: it proposes that the mind contains distinct subpersonalities — *parts* — and that the quality of one's inner life depends on whether those parts are in the driver's seat or can be held in awareness from a stable center. Despite its clinical reach, IFS has lacked a formal computational account of what a part actually is. We propose that parts are identity-level precision bundles — coupled priors over self-state, world-state, policy, and expected outcome, with self-state as the organizing prior. This architecture predicts not only a revision cascade but a generalization gradient: interventions that revise the shared self-state prior should transfer beyond the originally treated stimulus, whereas interventions that remain at the threat level should stay more local. Active inference simulations confirm the ordering: under context-held activation (witnessing), self-state is revised first, threat meaning follows, protective policy lags; under matched exposure, all three move more uniformly and the cascade does not appear. A follow-on transfer test confirms the generalization prediction directly. The formal distinction between *capture* and *context-held activation* explains why only the latter permits lasting change. Inside the context-held window, the activated part encounters Self's present-moment self-state, generating relational prediction error that reaches the identity-level organizing prior rather than merely the threat expectation. The model positions Self-energy, relational prediction error, and the generalization gradient it implies as tractable targets for empirical comparison of IFS with exposure-based approaches.

---

## 1. Introduction

Sometimes *I am afraid.* Sometimes *a part of me is afraid.* Same activation, different relationship.

Consider a simple case. A person who was badly frightened by a dog as a child sees an off-leash dog running toward them in a park. Their chest tightens. Their body pulls back. One organization of the system becomes certain all at once: *dogs are dangerous; I am small; get away now.* In ordinary fear-learning language, that looks like a threat response. But existing active inference accounts of fear do not have a formal account of why this activation feels like *identity* rather than one belief among many, or why some activations revise while others merely repeat. A threat response is a belief about danger. What IFS describes is something more specific: a coupled bundle in which *who I am* is not separable from *what this means* and *what I must do*.

IFS describes the dog case in more specific terms. A *burdened part* — a subpersonality carrying old fear and its associated identity claims — is active. *Protectors*, other parts whose job is to prevent destabilizing activation, are organizing around it. The central question is whether the person is now *captured* by the part (speaking as it, from inside its local world) or can relate to it from a different vantage point — what IFS calls Self (the state in which no part dominates and the person can hold what is active with curiosity and care).

If the activation takes over, the fear is not experienced as one perspective among others; it becomes reality. The dog is dangerous now. The body is small now. Avoidance feels necessary now. If the same activation remains present while also being held in awareness, the fear is still there, but the system is no longer speaking only from inside the part. The person can relate to it.

IFS treats that relational difference as load-bearing. The therapist does not simply increase contact with the dog, the memory, or the feared affect. The therapist helps the client step back from the activated part, approach it from Self, and remain in relationship to it long enough for something new to happen. That is why the method keeps returning to questions like: *How do you feel toward this part?* *What does it fear would happen if it stopped?* *Will it let you get closer?* The intervention is organized not around activation alone but around who is relating to whom inside the system.

The claim of this paper is direct. The decisive therapeutic variable is not activation alone. It is the relation of the system to activated part-content. We propose that this relation is formalizable, tractable, and clinically consequential. The governing variable in the present account is **Self-energy**.

Because self-state is the organizing prior in the present model, the account makes two sharper predictions than a threat-primary fear model does. First, under witnessing, revision should reach self-state before threat meaning and protective policy. Second, if that revised prior is genuinely identity-level rather than cue-specific, its effects should generalize beyond the originally treated stimulus. The paper therefore argues not only that witnessing changes the relation to activation, but that this change should have a distinctive downstream profile.

This paper is not arguing that IFS replaces exposure, schema work, or other evidence-based approaches. The claim is narrower. Different therapies alter different inferential variables. Exposure changes what the system learns under contact with feared stimuli. IFS, at its core, changes whether the activated part takes over or can be held in context.

Section 2 explains the phenomenon in IFS language and introduces a translation between clinical and computational vocabularies. Section 3 defines the formal object — parts as identity-level precision bundles — and introduces the active inference machinery the argument needs. Sections 4–5 compress formation and persistence (full treatment in Appendix A). Section 6 introduces Self-energy and the inferential regimes it governs. Sections 7–8 formalize capture, context-held activation, and why only this combination permits lasting change. Section 9 identifies the relational prediction error that operates inside the context-held window. Section 10 extends the framework to protectors and polarization. Sections 11–12 present the main simulation and a short follow-on transfer test. Section 13 closes with what the model explains, where it is still thin, and what should come next.

---

## 2. IFS in Its Own Terms

IFS begins from a simple claim: the mind is multiple, and that multiplicity is organized. People have parts. Some parts carry terror, shame, grief, helplessness, or loneliness. These are often called *exiles* because the system keeps them out of ordinary consciousness when their pain would be too much. Other parts work to prevent that activation. These are *protectors*. Some are *managers*: they anticipate trouble, control situations, avoid risk, and keep life organized so the exile does not break through. Others are *firefighters*: they react after activation has already begun and try to shut it down fast, often through dissociation, numbing, rage, or impulsive action.

IFS also posits **Self**. Self is not another part with better ideas. It is the state in which the person is not captured by any one part and can relate with curiosity, calm, compassion, and clarity. In practice, therapists use Self as both diagnostic and therapeutic reality. If the client can feel warmth, respect, or curiosity toward an activated part, there is enough Self-energy in the system to proceed. If the client says *I hate this scared part* or *I need it gone*, the therapist assumes another protector is now blended and works there first.

The dog example makes the structure concrete. A child is bitten, cornered, or badly frightened by a dog. An exile comes to carry terror and helplessness. A manager learns to scan sidewalks, cross the street, and keep distance before the fear surges. If a dog gets too close anyway, a firefighter may take over with panic, collapse, dissociation, or an urgent need to flee. From the inside, the episode does not feel like a neutral memory being retrieved. It feels immediate: *this dog is dangerous; I am small; I have to get away*.

The therapeutic question is therefore not just whether the fear has been activated. It is whether the person is **captured** by the part or can become unblended enough to relate to it. Capture means the part is speaking as the whole person. Stepping back from capture means the person can speak *for* the part rather than only *from* it:

- *I am terrified of dogs. I need to leave.*
- *A young part of me is terrified of dogs. I can feel how sure it is that we are in danger.*

In the first, the part has the microphone. In the second, the part is still fully present, but there is now a witnessing relationship to it.

This is why the classic IFS question, *How do you feel toward this part?*, is so diagnostic. It does not ask how intense the fear is. It asks who is relating to the fear. The question does not measure activation. It measures relationship to activation. That is exactly what the model says matters.

Table 1 states the translation between IFS and computational vocabularies. A condensed glossary appears in Appendix C.

| IFS term | Computational translation |
|---|---|
| **Parts** | Identity-level precision bundles: learned local models coupling self-state, world-state, policy, and expected outcome |
| **Blending** | Clinical name for capture: the active bundle dominates inference; present context loses inferential weight |
| **Witnessing** | Context-held activation: the same bundle remains live while present evidence — including Self's present-moment self-state — stays online, enabling relational prediction error |
| **Self** | A regime of uncaptured inference; when this regime obtains, the system's present-moment self-state becomes available as a differentiated presence that parts can register |
| **Self-energy** | The governing variable for which regime obtains; a composite of autonomic safety and metacognitive depth |
| **Protectors** | Policy priors and access-control tendencies that prevent destabilizing activation of exiles |
| **Unburdening** | Durable revision of upstream priors under context-held activation |

---

## 3. Parts as Identity-Level Precision Bundles

In the present model, a part is a local control model. It is a bundle of priors that learned together and now reactivate together. Throughout this paper, "parts" is the clinical term, "identity-level precision bundle" is the formal definition, and "local control model" describes the computational role the bundle plays.

The bundle has four elements:

1. **Self-state** — who I am here
2. **World-state** — what kind of situation this is
3. **Policy** — what I must do
4. **Expected outcome** — what will happen if I do or do not

This bundle structure has an independent precedent in object relations theory, where a complete object relation is composed of a self-image, an object-image, a cause-image, and an effect-image. The computational bundle and the object-relational structure are tracking the same thing at different levels of description.

**Discriminant validity.** This structure may look like a relabeling, but it predicts things that nearby constructs cannot. *Schemas* can update without re-entering the identity position that organized them. *Latent contexts* select which model is operative, not who the agent is within it — a context switch says "now use model B"; a part activation says "now I am the self that model B was organized around." *Trait priors* are slowly-updated meta-parameters, not identity states coupled to world-meaning and policy in a single unit. Three things follow that none predict: (a) parts feel like whole worlds, because all four elements arrive together; (b) identity-level change generalizes while threat-level change stays local; (c) activation feels like regression to an earlier self-position, not recall of a fear memory.

A part is not a fear memory. It is an identity-level precision bundle in which self-state is the organizing prior — and revision that reaches the root generalizes in ways that revision of threat meaning alone cannot. Because self-state is the organizing prior, it is also where relational contact can do what threat-level intervention cannot — a point §9 takes up in detail.

That organizing role matters empirically as well as conceptually. If self-state is shared across situations in a way particular threat meanings are not, then revision that reaches self-state should travel further than revision that remains tied to one cue-threat pairing. The follow-on transfer test in §11.3 is included for that reason: not as a second theory of change, but as a sharper assay of whether the revised prior is genuinely identity-level.

Return to the dog case. Under overwhelm and low control, one bundle may consolidate around the following priors:

- **Self-state:** I am small and helpless
- **World-state:** dogs are dangerous
- **Policy:** avoid, freeze, get away
- **Expected outcome:** avoidance keeps me safe

That is more than a fear memory. It is a local solution to a world once experienced as both threatening and unmanageable. It contains an identity claim, a world claim, an action imperative, and a prediction about consequences.

This is why activated parts feel coherent. The bundle does not deliver one isolated belief. It delivers a whole local world. Helplessness makes danger more likely. Danger licenses avoidance. Avoidance confirms the original reading. The system is not merely remembering the past. It is re-entering a learned inferential regime.

This is also why activation tends to feel like identity rather than object. When the bundle's precision dominates inference, there is no vantage point outside it. The system does not report, "a bundle with helpless self-state is active." It reports, "I am afraid," "I am six," "I can't handle this."

### 3.1 Computational setup

The present model does not treat parts as literally separate agents with separate generative models. It models them as learned local control models within a single generative model. They are coherent because the priors that compose them were learned together. They feel intentional because they couple perception, prediction, and policy in a goal-directed way. They feel like subjects when active because their precision can dominate inference.

**Generative model.** A generative model is the system's model of how hidden states produce observations and how actions change what will be observed next. The main simulation uses a discrete state-space formulation with two hidden factors — **self-state** (child-helpless or adult-capable) and **threat meaning** (dangerous or safe) — observed through three channels (cue, self-evidence, outcome). It adds cross-trial Dirichlet learning with separate prior banks per stimulus, so the system can acquire and retain part-like beliefs.

**Precision.** Precision weights the influence of prediction error on inference. High precision means "trust this strongly." Low precision means "weight it lightly." Self-energy modulates the precision balance between part priors and present-context evidence. There is no explicit channel gating — self-evidence is always available, but its impact on inference depends on how much precision the system allocates to it versus the part bundle's prior. The paper manipulates two precision-bearing quantities:

- **Part-bundle prior precision** (`π_part`): how strongly the active bundle insists on its version of self, world, and action.
- **Present-context evidence precision** (`λ_ctx`): how much inferential weight the system gives to what is true here and now.

**Scope discipline.** The model is deliberately minimal. Only three quantities vary: `π_part`, `λ_ctx`, and `E_t` (Self-energy). The paper is isolating one mechanism: how part priors and present context compete under different levels of Self-energy. Most of the paper's claims are tested in this main model; a short follow-on transfer test later asks whether the same identity-level revision should carry into a novel stimulus in a way cue-specific threat revision does not.

---

## 4. Formation and Persistence

Parts form under overwhelm and low control. That is the paper's formation claim. High threat alone is not enough. A frightening event can be fully real and still not become a rigid part if the person retains agency, receives co-regulation, or can update their model through successful action. Threat matters. Control matters just as much.

The formation sequence: prediction error exceeds the system's capacity for orderly updating; perceived control is low; attention narrows to the most salient threat-relevant features; the action repertoire contracts; one local solution reliably reduces acute free energy and is retained with high precision. This is compression under overwhelm. The system narrows until one way of being small enough to survive becomes highly trusted. Two predictions follow. Not all fear becomes a part — fear plus available agency or support often leads to integration. And chronic neglect can be part-forming even without one catastrophic event, because moderate threat plus chronic low support consolidates diffuse persistent local models through repeated need-without-solution.

Once formed, parts persist through a self-sealing loop. High prior precision: the beliefs were learned under survival-relevant conditions, so incoming contradiction carries too little weight to move the posterior. Underweighted present context: when the part activates, present evidence does not vanish — it no longer matters enough computationally. Avoidant sampling: the part's policy priors steer the system away from the evidence that would weaken it. The channels remain available in principle; this is **functional isolation**, not structural disconnection. That matters because functional isolation admits of slow change under repeated safe contact — which is one reason exposure still produces some revision in the model, even when Self-energy is not raised into the witnessing regime.

Formation simulations (Appendix A) support the low-control claim: high-threat + low-control produces the strongest bundle rigidity; chronic low support produces an intermediate profile; high-threat + high-control attenuates bundle formation without eliminating threat learning. Control does not erase fear learning. It prevents fear learning from crystallizing into an identity-level bundle.

---

## 5. Self and Self-Energy

IFS gives Self a special status. This paper keeps that centrality while translating it into computationally tractable terms.

### 5.1 Self as regime

Self is not modeled here as a homunculus. It is a regime of uncaptured inference. When no part dominates, inference remains responsive across channels. Present evidence can register. Multiple action possibilities remain available. The system is not being run by one compressed local model.

But the regime has a further consequence. When no part's self-state dominates, the system's present-moment self-state becomes available: adult, located in the current context, not organized around the original danger. That self-state is not a homunculus. It is what self-modeling yields when inference is uncaptured. Parts, however, can register it — and as §9 argues, that registration is load-bearing.

### 5.2 Self-energy as composite

Self-energy is the paper's answer to its central question. It is what determines whether activation becomes capture or can be held in context. Theoretically, Self-energy is composite. At minimum it includes two components:

- **Autonomic-social regulation (`V_t`)**: ventral-vagal availability, embodied safety, the capacity to remain in contact without survival mode taking over.
- **Metacognitive depth (`M_t`)**: the capacity to represent one's own state as state rather than identity; to know *a part of me is afraid* instead of only *I am afraid*.

Neither component is sufficient on its own. A person can be somatically calm and still have no witnessing capacity. A person can describe their parts with elegant insight while their body remains in full sympathetic threat. Self-energy is high when both are available together. In the simulations, `E_t` is a scalar proxy for this composite.

Clinically, Self-energy is often scaffolded before it is endogenous. The therapist's regulated presence, pacing, and stance supply part of what the client cannot yet stably generate alone. The simulations include this only minimally through an external support term. The model is intra-agent by design. Therapy is not.

### 5.3 Self-led calm vs. dissociative quiet

The paper distinguishes two superficially similar states that are clinically opposite. **Self-led calm** keeps present evidence strongly online. The system is quiet because nothing has captured it. **Dissociative quiet** reduces the impact of incoming evidence. The system is quiet because contact has been turned down. The control simulations make this distinction visible: dissociation reduces apparent disturbance but produces little upstream revision.

### 5.4 What Self-energy governs: the therapeutic zone

|  | Low Self-energy | High Self-energy |
|---|---|---|
| **Low activation** | ordinary cognition | presence / Self |
| **High activation** | capture | context-held activation |

IFS therapy aims for the lower-right cell. That cell is unstable by default: activation tends to lower Self-energy, and high Self-energy tends to prevent full activation. Therapy titrates both at once — enough activation for the target priors to come online, enough Self-energy for context to remain present.

The 8 C's of Self (calm, curiosity, clarity, compassion, confidence, courage, creativity, connectedness) can be read as the phenomenological signature of uncaptured inference under sufficiently high Self-energy. The hardest test case is the self-like part: a manager that sounds reflective and compassionate without producing the inferential regime in which revision can occur. The model flags that problem but does not solve it.

---

## 6. Capture and Context-Held Activation

Same activation, different relationship. That is the paper's center of gravity.

The two regimes are not symmetric. Capture is the failure mode — the active bundle dominates inference and makes revision impossible. Context-held activation is the goal — the same bundle remains live while the system retains contact with present reality. Witnessing is the clinically named form of context-held activation.

### 6.1 Capture

Capture occurs when an activated part takes over inference. The part's priors dominate the posterior strongly enough that present context loses inferential force. The person does not merely have fear. The fear organizes the whole field.

Formally, capture corresponds to a high **capture index**:

\[
C_t = \frac{\pi^{\mathrm{eff}}_{\mathrm{part}}}{\pi^{\mathrm{eff}}_{\mathrm{part}} + \lambda^{\mathrm{eff}}_{\mathrm{ctx}}}
\]

where

\[
\pi^{\mathrm{eff}}_{\mathrm{part}} = r_t \cdot \pi_{\mathrm{part}} \cdot e^{-\beta E_t}, \qquad \lambda^{\mathrm{eff}}_{\mathrm{ctx}} = \lambda_{\mathrm{ctx}} \cdot e^{+\gamma E_t}
\]

Here `r_t` is activation strength. Self-energy does not have to turn activation off. It changes how much that activation can dominate. Capture is graded, not binary.

![Figure: Capture index across conditions](figures/fig5_capture_index.png)

*Figure 1. Capture index as a function of Self-energy. Low Self-energy places baseline, exposure, and dissociation in the capture zone. High Self-energy places witnessing in the context-held regime.*

### 6.2 Context-Held Activation

Context-held activation is not the absence of activation. It is activation held in context. The part still fires. The body may still accelerate. The old priors still come online. But the system is not captured by them. Self's present-moment self-state remains available — adult, capable, not organized around the original danger — and so does informational context: *I am in this room; this body is adult; this moment is not the original one.* The activated part becomes something the system can relate to rather than only speak from.

Context-held activation is formally distinct from distraction, suppression, or dissociation. Distraction lowers activation. Dissociation lowers context impact. Context-held activation leaves activation live while preventing capture.

### 6.3 The clinical probe

Clinicians do not ask for the capture index. They ask, "How do you feel toward this part?" If the client answers from the part — *I am terrified; I hate this; I need to get away* — the system is still captured. If the client answers with curiosity, compassion, or respectful interest, the system is more likely in context-held activation.

---

## 7. Why Only Context-Held Activation Permits Lasting Change

Durable revision requires three conditions at once:

1. **The part must be active.** Otherwise the target priors are dormant.
2. **Present context must be online.** Otherwise there is nothing to revise the priors with.
3. **The part must not capture inference.** Otherwise the mismatch between past model and present reality cannot register with enough force.

Context-held activation is the only regime that satisfies all three simultaneously.

Under capture, the part's priors dominate too strongly for present contradiction to gain traction. The system may be surrounded by safety and still infer danger because the active model interprets everything through its own lens. The result is repetition without revision.

Calm by itself is not enough. A person can be regulated, insightful, and articulate while the relevant bundle remains offline. Dormant priors do not update because they are not currently generating predictions that can be contradicted.

### 7.1 Unburdening as upstream revision

At the algorithmic level, the paper interprets unburdening as durable revision of upstream priors. In H1, self-state sits upstream of threat meaning, which sits upstream of protective policy. A revision in self-state — from *I am helpless here* to *I am capable here* — changes what counts as dangerous. A change in threat meaning changes what policies remain necessary. This gives a formal answer to a familiar clinical observation: why does deep change sometimes feel sudden? Because once an upstream prior shifts far enough, several downstream expectations lose support together.

Clinically, unburdening often does more than reduce intensity. A part that carried helplessness may, after unburdening, take on a new functional role — playfulness, healthy assertiveness, creativity. In the present model, that transition corresponds to the bundle adopting new policy priors and expected-outcome priors once the old self-state no longer constrains the solution space.

### 7.2 Exposure versus context-held activation

Exposure and context-held activation both supply corrective contact under activation. Exposure generates informational prediction error: the feared outcome does not occur, and threat meaning can update. But Self-energy remains outside the witnessing regime — the person's relation to the activation is unchanged. Learning therefore occurs locally. Threat meaning can move; self-state shifts later, less deeply, with less generalization.

Context-held activation supplies both channels: informational context is present *and* Self's present-moment self-state is available to the part. The relational prediction error reaches self-state directly. Under H1, that allows self-state revision to occur earlier and to cascade forward.

The distinction has a further implication not visible from within-session trajectories alone. If witnessing revises the shared self-state prior, its effects should extend beyond the specific cue under treatment. If exposure revises only threat meaning, its effects should remain more local. The follow-on transfer test reported in §11.3 and §12.8 asks exactly that question.

---

## 8. Relational Prediction Error

The previous sections established what parts are and what governs the therapeutic regime. This section identifies what happens inside the context-held window that produces revision.

When present context stays online, this paper has so far emphasized informational context: the room, the therapist, the adult body, the fact that this moment is not the original one. But present context also includes something more specific. When no part's self-state dominates, the system's present-moment self-state becomes available — adult, capable, not organized around the original danger. Under context-held activation, that self-state can be registered by the activated part.

The part's generative model includes relational expectations, not only threat expectations. A bundle consolidated under overwhelm and isolation encodes not just *dogs are dangerous* and *avoidance keeps me safe* but also *I am alone with this* and *no one can be here with me in this.* These relational priors belong to the self-state element — they encode who-I-am-in-relation, not what-is-dangerous.

When Self is present as a differentiated self-state, those relational expectations generate prediction error at the identity level. The part expected isolation. It encountered presence. The part expected that its wound would overwhelm or repel. Instead, the wound was met with curiosity and care. That mismatch does not update threat meaning. It reaches the self-state prior directly — the organizing root of the bundle.

Two channels of evidence are available inside the window, and they are not interchangeable. The primary channel is relational: the part registers Self's current self-state — adult, capable, present, not overwhelmed by what the part carries. The secondary channel is informational: the part can be shown the current life, the current body, the fact that the original danger is past. In practice, the shift often occurs during witnessing itself — the part sees Self and something opens — before any explicit life-updating. That confirms the identity-level mismatch, not the informational update, is doing the deeper work.

This is what IFS clinicians are pointing at when they say the core of the work is relational. "Relationship building is our job throughout IFS therapy. We want parts to be in relationship with the client's Self" (Anderson, *Skills Training Manual*). The moment of shift, when it comes, is often marked by exactly this registration: *She sees me now* (Schwartz, *Shame and Guilt*).

The memory reconsolidation literature offers independent support. Reconsolidation requires a prediction error strong enough to destabilize a consolidated memory trace. In IFS, that prediction error is relational: "The mismatch unfolds as the exiled part feels fully understood, validated and loved by the Self during witnessing" (Anderson, *Skills Training Manual*). The mismatch is not re-exposure to the feared stimulus under new conditions. It is the part encountering a relational context that contradicts its deepest expectation.

Modality independence follows directly. IFS works through visual imagery, inner dialogue, and somatic felt-sense. What matters is not the sensory modality but whether the part registers that it is being met. "'Seeing' a part is not necessary in the sense that a clear visual image appears in the person's mind. Many people simply sense the presence of parts and interact with them on that basis" (Goulding & Schwartz, *Mosaic Mind*).

---

## 9. Extensions: Protectors and Polarization

The core argument is complete by §8. The following extends the framework to protectors and multi-part polarization.

A protector is a learned policy prior plus an access-control tendency: if cue patterns predict that an exile may activate, and if available Self-energy is judged insufficient, favor policies that reduce activation or block access. That minimal story already captures avoidance, intellectualization, perfectionism, numbing, distraction, rage, and dissociation. IFS's distinction between **managers** (prospective) and **firefighters** (reactive) maps cleanly onto temporal depth.

What the model does not yet formalize is equally important. A protector's willingness to relax is not simply a function of reduced threat. It depends on whether the protector believes Self is present enough, the context is safe enough, and the process can be trusted. Computationally, that looks less like a simple policy prior and more like a gate on information flow with a learned trust variable. Those dynamics are clinically central and formally deferred here.

**Polarization.** Two bundles are active; each assigns high cost to the other's preferred action. Part A wants approach, disclose, attach. Part B wants withdraw, protect, avoid. Part A experiences withdrawal as abandonment; Part B experiences approach as danger. Under low Self-energy, this produces the familiar phenomenology: ambivalence, reversals, exhaustion, each side wholly true when it has the floor. Under high Self-energy, both remain simultaneously representable without either taking over, and a negotiated policy becomes possible. The polarization simulations (Appendix B) support a three-regime picture: low Self-energy produces anti-phase oscillation; medium Self-energy increases exploration and switching; high Self-energy produces stable simultaneous representation.

---

## 10. Simulation Design

### 10.1 Main model

The main simulation tests within-trial cascade dynamics. A person badly frightened by a dog as a child encounters a friendly off-leash dog under different inferential regimes. The model tracks whether self-state, threat meaning, expected outcome, and policy revise in the predicted cascade order and whether that cascade depends on Self-energy depth.

**Architecture.** Three hidden factors, each with two states: self-state (helpless-alone / capable-present), threat meaning (dangerous / safe), and expected outcome (avoidance-saves / contact-manageable). Context is environmental, not inferred — the dog encounter is always safe. Five observation channels deliver evidence: external cue, interoceptive arousal, action outcome, informational context, and witnessed self-state. The witnessed-self-state channel is precision-modulated by Self-energy through inverse capture: when capture is high, it is functionally silent; when capture drops below threshold, it opens superlinearly.

**Causal structure.** H1 places self-state upstream: self-state conditions threat meaning, threat meaning conditions expected outcome, expected outcome biases policy through expected free energy. H2 reverses the chain: threat meaning is upstream and self-state follows.

**Conditions.** Three Self-energy levels cross the regime boundary:

- **Exposure** (E_t = 0.15): high capture, witnessed-self channel off.
- **Informational** (E_t = 0.50): moderate capture, channel weak.
- **Relational depth** (E_t = 0.85): low capture, channel open.

**Protocol.** Each condition runs in two phases. Phase 1 (T = 20): forced contact with active learning. Phase 2 (T = 3): free-choice probe with learning frozen.

### 10.2 H1 versus H2

Under the same relational depth condition, reversing the causal architecture tests Move 1. H1 predicts self-state first, threat second, outcome third, policy last. H2 predicts the reverse. Matching the depth condition while reversing causal structure isolates whether the cascade requires self-state at the root.

### 10.3 Follow-on transfer test

Within-run revision order does not by itself establish that what changed was identity-level rather than threat-level. For that reason, the paper adds a short follow-on transfer test. The question is simple: after safe training with the original dog cue, does the learned change carry into a novel safe cat cue? If the revised prior is genuinely self-state, transfer should appear; if learning remained dog-specific, it should not.

The transfer model is intentionally smaller than the main model. Two hidden factors — self-state (helpless / resourced) and threat meaning (dangerous / safe) — with a shared self-state prior across stimuli and separate threat priors for dog and cat. Three conditions are compared: high Self-energy with self-state learning intact, high Self-energy with self-state learning frozen, and low Self-energy with self-state learning permitted in principle but functionally weak under capture.

Training consists of 20 safe dog trials with forced contact and active learning. Transfer is assessed on the first safe cat probe with learning frozen. If dog training changed only dog-specific threat meaning, cat behavior should remain avoidant. If dog training changed the shared self-state prior, cat approach should rise despite the absence of cat-specific safety learning.

One methodological note. Because within-run cascade timing alone does not prove content specificity, the transfer test is the content-specific discriminant. Detailed adversarial history is recorded in Appendix B.

---

## 11. Results

### 11.1 Same activation, different relationship

Matched activation under three Self-energy levels produces cleanly different revision trajectories. The cue structure is identical across conditions. What changes is only the regime in which contact is made.

### 11.2 The revision cascade under H1

Under relational depth, the cascade is visible and unambiguous. Self-state crosses the revision threshold first. Threat meaning follows. Expected outcome follows threat. Policy — tracked as P(approach/stay) during the free-choice probe — shifts last.

![Figure: The cascade under three conditions](figures/v2/ifs_v2_one_figure.png)

*Figure 2. The cascade diagonal. Under relational depth (E_t = 0.85), self-state revises first, pulling threat meaning, expected outcome, and policy behind it. Under informational contact (E_t = 0.50), threat meaning moves but self-state barely budges. Under exposure (E_t = 0.15), all move slowly and uniformly — no cascade.*

The separation between informational and relational depth conditions on self-state revision is the sharpest result. Confidence bands do not overlap. Informational contact moves threat meaning but leaves self-state largely intact. Relational depth moves self-state first and everything else follows.

### 11.3 H2 flips the order

Reversing the causal architecture eliminates the cascade. H1 (self-state upstream) produces the predicted ordering: self-state first, threat second, outcome third, policy last. H2 (threat upstream) produces the opposite — threat meaning leads and self-state lags. The cascade is not an artifact of Self-energy alone. It requires self-state at the root of the generative model.

### 11.4 Witnessing outperforms exposure

Under exposure, all four bundle elements move slowly and together. There is revision — contact with a safe stimulus does produce some learning — but no separation between elements and no clear ordering. The system learns locally, without the cascade.

![Figure: Witnessing vs exposure belief trajectories](figures/fig2_witnessing_vs_exposure.png)

*Figure 3. Context-held activation (witnessing) versus exposure under matched contact. Witnessing produces faster and deeper revision across all three target variables. The separation is attributable to inferential regime, not privileged information.*

### 11.5 Real danger and dissociation

The real-danger condition preserves adaptive fear under high Self-energy: the agent correctly learns to avoid when the environment is genuinely harmful, confirming that witnessing does not collapse threat sensitivity. The dissociation condition reduces apparent disturbance without revising upstream priors — the diagnostic difference between Self-led calm and dissociative quiet.

### 11.6 Capture and the Self-energy sweep

Sweeping E_t from 0 to 1 reveals a sharp sigmoid in self-state revision at E_t ≈ 0.60–0.65. Below that threshold, self-state barely moves regardless of contact duration. Above it, self-state revision rises steeply. The threshold emerges from the interaction of capture dynamics and channel precision gating, not from a separate parameter.

### 11.7 Free-choice probe

During the three-timestep free-choice phase with learning frozen, the three conditions produce cleanly separable behavioral profiles. Exposure agents predominantly avoid. Informational agents inspect — they approach tentatively but do not commit. Relational depth agents stay. Behavioral revision tracks the cascade.

Parameter sensitivity is stable under ±20% variation in all key parameters; the qualitative pattern holds.

### 11.8 Identity-level revision generalizes; threat-level revision does not

A short follow-on transfer test sharpens the paper's main claim. During dog training, the high-Self conditions converge on comparable approach behavior, ensuring that any divergence on the later cat probe reflects what was learned rather than how much was learned.

The cat probe cleanly separates identity-level from threat-level change. When self-state revised during dog training, approach generalized to the untreated cat cue. When dog-specific threat meaning revised without self-state change, transfer did not occur. Low Self-energy likewise produced little or no transfer, because the self-state prior never moved enough during training.

Stimulus specificity supports the interpretation. The cat-specific threat prior remains essentially unchanged across conditions. Transfer therefore operates through the shared self-state prior rather than through leakage of dog-specific safety learning.

This follow-on result matters because the main H1/H2 cascade alone cannot distinguish identity-level revision from a cleverly timed threat-level update. The transfer contrast can. Witnessing is not simply faster safety learning. It produces a different kind of revision — identity-level rather than cue-local — and that difference becomes visible when the system encounters a structurally similar but untreated cue.

![Figure: Transfer result](figures/v3/ifs_generalization_main_v3.png)

*Figure 4. Transfer test. Left: dog training trajectories for self-state and threat revision — high-Self conditions converge on matched dog performance. Right: first cat probe P(contact_cat). Shared self-state revision transfers; cue-specific threat revision does not.*

---

## 12. Discussion

The paper set out to answer a narrow but clinically important question: when a part activates, what determines whether it takes over or can be held in context, and why does only the latter permit lasting change?

The answer proposed here is structural. Self-energy governs the precision balance between active part priors and present-context evidence. That balance determines inferential regime. Under capture, the part dominates the field. Under context-held activation, the same part remains active while context stays online — and, critically, Self's present-moment self-state becomes available as a differentiated presence the part can register.

### 12.1 What the model explains

First, it explains why parts feel like whole worlds rather than isolated beliefs. The bundle structure couples self-state, world-state, policy, and outcome.

Second, it explains why activation alone is not therapeutic. Without context, activation repeats. Without activation, context cannot reach the dormant prior. Context-held activation uniquely provides both.

Third, it explains why IFS-like change often feels upstream and generalizing. Under H1, revising self-state changes what counts as dangerous, which then changes what protectors need to do.

Fourth, it distinguishes Self-led calm from dissociative quiet. Both may look regulated. Only one preserves contact.

Fifth, it shows why this still counts as an IFS model despite being minimal. What makes the model specifically IFS is not plurality alone. It is the claim that the decisive therapeutic variable is the Self-mediated relation to activated part-content.

Sixth, it identifies the specific prediction error that does the work inside the context-held window: the part's relational expectation — isolation, overwhelm, rejection — is contradicted by Self's present-moment self-state, generating identity-level mismatch that reaches the organizing prior directly.

Seventh, it predicts a generalization gradient: identity-level revision should transfer to novel feared stimuli while threat-level revision should remain more local. The follow-on transfer test supports that prediction. Agents whose self-state revised during dog training approached a novel untreated cat cue; agents whose learning remained threat-specific did not.

### 12.2 What it does not yet explain

The paper leaves several clinically important structures under-modeled. It does not yet formalize full protector negotiation. Protectors in clinical IFS do not merely block — they compute trust, grant permission, and have conditions under which they will step back. It does not distinguish genuine Self from self-like managerial imitation — a distinction that probably requires separating embodied regulation from reportable meta-awareness more sharply than a single scalar allows. It does not model the therapist as a second agent, even though the clinical process is often dyadic long before it becomes stably intra-psychic.

The main H1/H2 cascade also does not by itself prove content specificity. A late-opening threat channel can mimic the same within-run ordering. The transfer test partially addresses that concern by shifting the discriminant from timing to cross-cue generalization, where shared self-state revision and cue-specific threat revision come apart.

### 12.3 Implications for therapy comparison

The strongest comparative implication concerns exposure. The paper does not claim that exposure fails. The simulations show the opposite: exposure learns. What they show is that exposure and context-held activation learn differently. Exposure alters threat expectations under contact. Context-held activation alters the relation in which that contact occurs. If self-state truly sits upstream, then witnessing should revise a broader class of downstream appraisals. That is the paper's clearest comparative claim and probably its cleanest empirical target.

The model also generates a comparative prediction that standard fear-learning formulations do not naturally make: identity-level revision should transfer across untreated cues more than threat-level revision does. If multiple fears are organized around the same burdened self-position, then revising that identity should alter a broader class of downstream appraisals. The follow-on transfer test is meant as a first demonstration of that point rather than a final proof.

### 12.4 Next steps

Three empirical predictions follow directly.

**Revision order.** Under IFS-informed witnessing, self-state should cross its revision threshold before threat meaning does, and threat meaning should cross before policy and avoidance change. Under standard exposure, all three should move more uniformly. The prediction requires purpose-built measures that cleanly separate the bundle elements.

**Generalization gradient.** After treatment targeting one fear, measure transfer to a structurally similar but untrained fear. The model predicts that IFS transfer will exceed exposure transfer because IFS revises the identity-level prior that organized the bundle.

**Relational channel primacy.** Comparing IFS sessions in which witnessing occurs with and without the retrieval step should show that relational contact alone is sufficient for identity-level revision to begin.

Beyond these, the next modeling extensions are: dyadic regulation (therapist and client as interacting agents); self-like parts (separating autonomic regulation from meta-awareness); richer protector computation (trust, conditional permission, role transformation); multi-part networks; and empirical fitting against session-level data.

This paper has defined what a part formally is — an identity-level precision bundle organized around a self-state prior — and shown that Self-energy determines whether activation of that bundle produces revision or repetition. It has identified the relational prediction error that operates inside the witnessing window and argued that change reaching the identity-level root should generalize more broadly than change that remains cue-specific. The mechanism is visible, the cascade from self-state through threat meaning to policy is real, and the generalization gradient is the formalism's sharpest empirical edge.

---

## Appendix A. Formation and Polarization Simulations

**Formation.** The formation simulation asks whether part-like bundle rigidity can arise through precision-weighted learning alone. Across three acquisition environments: high-threat + low-control produces the strongest helpless self-state consolidation and the highest integrated bundle rigidity; high-threat + high-control produces strong danger learning but much weaker helpless self-state consolidation; chronic low support produces an intermediate, slower-forming profile. Low control converts threat learning into identity-weighted part formation.

**Polarization.** Two mutually threatening bundles (approach/disclose/attach vs. withdraw/protect/avoid) are activated across Self-energy levels. Low Self-energy: activations alternate in anti-phase, each bundle locally true when active and intolerable when not. Medium Self-energy: exploration band with high policy entropy and switching. High Self-energy: stable simultaneous representation with reduced switching. The middle band is theoretically useful — de-polarization may first look like more policy experimentation rather than immediate calm.

---

## Appendix B. Adversarial Testing of the Main Simulation

The main simulation was subjected to four pre-registered adversarial tests. Three passed cleanly: shuffled observation channels broke the cascade (Test 1), flat priors eliminated the depth gap (Test 2), and an intermediate-E_t condition produced intermediate results (Test 3). Test 4 did not pass. Replacing the witnessed-self-state channel's content with a gated threat channel produced similar within-trial dynamics — the same cascade shape, the same depth gap, the same sigmoid threshold. The model could not distinguish *where* the late-opening evidence entered the causal chain.

That failure motivated the follow-on transfer test in §10.3. Within-trial cascade timing is necessary but not sufficient for the paper's claims. Cross-trial transfer provides the content-specific discriminant: identity-level revision transfers because the self-state prior is shared; threat-level revision stays local because threat priors are stimulus-specific. No manipulation of within-trial timing can produce that pattern without shared self-state learning.

---

## Appendix C. Condensed Glossary

| Term | Computational translation |
|---|---|
| **Parts** | Identity-level precision bundles coupling self-state, world-state, policy, expected outcome |
| **Blending / Capture** | Active bundle dominates inference; present context loses inferential weight |
| **Context-held activation** | Same bundle live while present evidence stays online; the part is present but not dominant |
| **Witnessing** | Therapeutically cultivated form of context-held activation |
| **Self** | Regime of uncaptured inference; present-moment self-state becomes available as a differentiated presence parts can register |
| **Self-energy (E_t)** | Governing regime variable; composite of autonomic-social regulation and metacognitive depth |
| **Protectors** | Policy priors and access-control tendencies preventing destabilizing exile activation; managers (prospective) and firefighters (reactive) |
| **Exiles** | Parts carrying high-precision bundles formed under overwhelm and low control |
| **Unburdening** | Durable revision of upstream priors under context-held activation; begins with self-state and cascades |
| **Polarization** | Bundles assigning high cost to one another's preferred policies |
| **Capture index (C_t)** | Effective part precision over sum of effective part and context precision |
| **Relational prediction error** | Identity-level mismatch when a part's relational expectation encounters Self's present-moment self-state; reaches the organizing prior directly |
| **Informational prediction error** | Mismatch that updates threat meaning without reaching the self-state root |
| **H1 (self-state upstream)** | Causal architecture producing the revision cascade and generalization gradient |
| **H2 (threat-primary)** | Competing architecture; no cascade, local generalization only |
