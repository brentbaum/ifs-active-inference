# 1) One-page formulation

## Hook

**Sometimes “I am afraid.” Sometimes “a part of me is afraid.” Same activation, different relationship. This paper asks what determines which — and why only the second permits lasting change.**

## Central question

**When a part activates, what determines whether it takes over or can be held in context — and why does only the latter allow its outdated beliefs to change?**

## Core proposal

A part is a **high-precision local control model** within a single generative model.
The decisive variable is **Self-energy**.

* **Low Self-energy** → the active part captures inference (**blending**)
* **High Self-energy** → the same part activation is held in context (**witnessing**)

Only the second regime permits durable revision of the part’s outdated priors.

## Clinical vs computational ontology

**Clinical ontology**

* Parts are engaged as if they have intentions, fears, and trust conditions.
* Self is encountered as calm, curious, compassionate, clear, and connected.

**Computational ontology**

* Parts are not separate homunculi.
* A part is a learned bundle of priors over self-state, world-state, policy, and expected outcome.
* Self is modeled as a **regime**, indexed by **Self-energy**.

## Minimal formal vocabulary

This paper manipulates only three quantities:

* `π_part` = precision on the active part’s prior bundle
* `λ_ctx` = precision on present-context evidence
* `E_t` = Self-energy

All other precisions are held fixed in the core model.

## Part

A part bundles priors over:

* **self-state**: who I am here
* **world-state**: what kind of situation this is
* **policy**: what I must do
* **expected outcome**: what will happen if I do or don’t

Example bundle:

* “I am small / helpless”
* “this is dangerous”
* “I must avoid”
* “avoidance keeps me safe”

## Formation

A part forms when:

* prediction error is overwhelming
* perceived control is low
* attention narrows
* the action repertoire contracts
* one local solution reliably reduces acute free energy

This produces a rigid, high-precision control bundle.
No literal graph rewiring is required in the theory of v1.

## Self-energy

**Self-energy is the answer to the paper’s central question.**

Theoretically, Self-energy is **composite**, not atomic. It includes at least:

* **Autonomic-social safety / ventral-vagal availability** `V_t`
  The capacity to remain regulated, socially engaged, and non-defended under activation.

* **Metacognitive or epistemic depth** `M_t`
  The capacity for the model to represent its own current state as state rather than identity: “a part of me is afraid.”

In practice, Self-energy is not only endogenous; early in treatment it is often scaffolded interpersonally through the therapist's regulated presence.

So, in theory:

* `E_t = f(V_t, M_t)`
* `∂E/∂V > 0`, `∂E/∂M > 0`, and the interaction is positive

In the simulations:

* `E_t` is modeled as a scalar proxy

This means the simulation is a simplification of the theory, not the theory itself.

## Blending and witnessing

* **Blending** = the active part captures inference; present context drops offline; its beliefs feel like *me*
* **Witnessing** = the same part remains active, but present-context evidence stays online too; its beliefs feel like something I am with

In practice, blending is graded; the model treats it as a continuous balance between part dominance and context availability.

## Why only witnessing changes beliefs

Activation alone is not enough.

* Without activation, there is nothing live to revise.
* Without context, there is nothing live to revise it with.

Durable change requires:

1. the part to be active
2. present-context evidence to stay online
3. Self-energy high enough to prevent capture

That is why only witnessing permits lasting change.

## Formal sketch

Let:

* `r_t` = activation strength of the part bundle
* `π_part` = bundle prior precision
* `λ_ctx` = context evidence precision
* `E_t` = Self-energy

Then one simple operationalization is:

* `π_part_eff = r_t * π_part * exp(-βE_t)`
* `λ_ctx_eff = λ_ctx * exp(+γE_t)`

So Self-energy does not turn the part off.
It changes whether the part’s activation becomes **capture** or **context-held activation**.

## Main prediction

The same part activation should have two different outcomes:

* **Low Self-energy** → blending, repetition, low revision
* **High Self-energy** → witnessing, durable revision

## Quick map: phenomenon → how it falls out

| Phenomenon                    | How it falls out                                                                                                                                                                                                 |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Parts                         | Learned local control models bundling self-state, world-state, policy, and expected outcome; formed under overwhelm and stabilized by high prior precision                                                       |
| Blending                      | The part captures inference, present context goes functionally offline, and its beliefs feel like *me*                                                                                                           |
| Witnessing                    | The same part stays active while present evidence stays online too; its beliefs feel like something I am with                                                                                                    |
| Self-energy                   | The variable that determines which relation holds; theoretically composite of autonomic-social safety and metacognitive depth, modeled in v1 by a scalar proxy                                                   |
| Outdated beliefs              | Priors that were adaptive under earlier conditions but are anachronistic now; capture prevents the system from fully registering the mismatch                                                                    |
| Age regression                | The active bundle carries a developmental self-state — “I am six” is modeled as a live prior, not reduced to metaphor                                                                                            |
| 8 C’s of Self                 | The phenomenological signature of sufficiently uncaptured inference under high Self-energy, not yet a fully derived theorem and not evidence for a separate inner homunculus                                     |
| Protectors                    | Policy priors and access-control tendencies that prevent destabilizing exile takeover; in practice they also have trust conditions for stepping back, though v1 formalizes only the minimal gatekeeping function |
| Polarization                  | Two or more part-bundles competing for takeover, each treating the other’s preferred policy as dangerous                                                                                                         |
| Exposure vs IFS               | Exposure: corrective evidence under activation with limited Self-energy support. Witnessing: corrective evidence under activation while context remains online                                                   |
| Unburdening                   | Durable revision of the part’s upstream priors, made possible because context was maintained during activation                                                                                                   |
| Dissociation vs Self-led calm | Both may look quiet. Dissociation = present evidence functionally turned down. Self-ledness = present evidence strongly online with no part dominating                                                           |
| Why change generalizes        | Witnessing revises “who I am here” before “what is dangerous,” allowing upstream change to cascade downstream when H1 holds                                                                                      |

---

# 2) Paper outline

## Title

**Self-Energy, Witnessing, and the Revision of Part Beliefs: An Active Inference Account of Internal Family Systems**

## Opening hook

Sometimes “I am afraid.” Sometimes “a part of me is afraid.” Same activation, different relationship. This paper asks what determines which — and why only the second permits lasting change.

## Central question

When a part activates, what determines whether it takes over or can be held in context — and why does only the latter allow its outdated beliefs to change?

## Thesis

IFS parts can be modeled as high-precision local control models within a single generative model. The key variable is Self-energy: a composite capacity involving autonomic-social regulation and metacognitive depth. Low Self-energy yields blending, in which the active part captures inference and remains effectively insulated from updating. High Self-energy yields witnessing, in which the same part activation is held in context and can revise its outdated priors. Durable therapeutic change depends on this second regime.

---

## Section 1. Introduction

Purpose:

* Introduce the phenomenon of same activation, different relationship
* Establish that IFS is distinctive because it targets the relation to activated content, not activation alone
* State the central question and thesis

Key moves:

* Activation is not sufficient for change
* Relationship to activation is the core issue
* Self-energy is proposed as the governing variable

Include early:

* The claim is not that IFS outperforms exposure in every context, but that it targets a different variable: not activation alone, but the relation of the system to activated part-content.
* Self-energy is treated here as a composite capacity involving autonomic-social regulation and metacognitive depth, operationalized in the simulations by a scalar proxy.

---

## Section 2. Clinical ontology and computational ontology

Purpose:

* Prevent confusion between the clinical language of IFS and the computational model
* Preserve the usefulness of both

Key points:

* Clinically, parts are approached as if they are intentional centers of concern
* Computationally, parts are local control models, not separate agents
* Self is not a hidden homunculus; Self-energy is the formal variable

**Include Table 1 here:**
**Phenomenon → how it falls out**
This is the right place for the table because it gives the reader an immediate map from IFS language to computational commitments.

Include:

* Some clinical constructs — especially protector negotiation, self-like parts, and the therapist's relational contribution — are only minimally formalized in this version and are treated as future elaborations rather than fully modeled elements.

---

## Section 3. Minimal active inference toolkit

Purpose:

* Introduce only the formal machinery needed for this paper

Include:

* generative model
* hidden states, observations, policies
* precision as confidence weighting
* active inference as control under uncertainty

Constrain the scope:

* only three manipulated quantities in v1:

  * part-bundle prior precision
  * present-context evidence precision
  * Self-energy

This section should be short and disciplined.

Include a practitioner-friendly gloss:

* For non-technical readers, precision can be read as confidence weighting: how much the system trusts a given source of information in determining what is true and what action is needed.

---

## Section 4. What is a part?

Purpose:

* Define parts in computational terms

Main claim:

* A part is a local control model that bundles priors over:

  * self-state
  * world-state
  * policy
  * expected outcome

Explain:

* why parts feel coherent
* why they can feel purposeful without being literal sub-agents
* why activation tends to feel like identity rather than object

Include:

* In practice, clinicians often encounter exiles and protectors as distinct parts with distinct identities; the present model captures the minimal computational unit that can underwrite that phenomenology, while remaining agnostic about whether all clinically distinct parts map one-to-one onto separate formal bundles.

---

## Section 5. How parts form

Purpose:

* Explain part formation without relying on structural rewiring

Main claim:

* Part formation is compression under overwhelm and low control

Mechanism:

* overwhelming prediction error
* low perceived control
* narrowed attention
* contracted action repertoire
* repeated success of one local solution

Important claim:

* high threat alone is not enough
* high threat plus low control is the critical formation condition

Implications:

* why not all frightening events form parts (high threat with high control may be distressing but not part-forming)
* why neglect can be part-forming even without acute trauma (chronic low control under moderate threat)

Include a gradient prediction:

* The model predicts that degree of helplessness during formation should scale subsequent bundle rigidity, such that more severe low-control conditions produce more treatment-resistant prior bundles.

This section motivates Appendix A.

---

## Section 6. How parts persist

Purpose:

* Explain why parts remain rigid and recurrent

Main claim:

* Persistence is functional isolation produced by precision and sampling, not necessarily literal disconnection

Mechanisms:

* high part-bundle prior precision
* underweighting of present-context evidence
* avoidant sampling that prevents disconfirmation

This section should explicitly distinguish:

* **functional isolation**
  from
* **literal structural isolation**

And it should note the empirical difference:

* functional isolation predicts that slow updating can still occur under repeated safe sampling
* structural isolation predicts near-zero updating until reconnection

Include:

* The present model treats most persistence as functional isolation: channels remain available in principle, but chronically underweighted. This predicts slow updating under repeated safe sampling. More extreme clinical presentations may approximate structural isolation, which would predict near-zero updating until reconnection-like conditions occur.

---

## Section 7. Self and Self-energy

Purpose:

* Make Self central without making it a homunculus

### 7.1 Self as regime

* Self is a regime of uncaptured inference, not a separate inner entity

Limitation:

* This account explains why Self emerges when no part dominates, but it does not yet fully explain why that regime has the particular positive phenomenology described in IFS practice.

### 7.2 Self-energy as composite

* Self-energy is the theoretical control variable
* It includes two clearly separated components:

  * **Ventral-vagal / autonomic-social regulation** `V_t` — the capacity to remain regulated, socially engaged, and non-defended under activation
  * **Metacognitive / epistemic depth** `M_t` — the capacity to represent one's own current state as state rather than identity
* The simulation uses a scalar proxy for this composite

Include:

* Although modeled here as an individual-level variable, Self-energy is often scaffolded interpersonally in treatment: the therapist's regulated, non-defended presence can function as an external support for the client's own Self-energy before that capacity is internally stable.

### 7.3 Self-led calm vs dissociative quiet

* low arousal is not enough
* dissociation and Self-ledness may look similar on the surface but arise from opposite inferential mechanisms

Include:

* Clinically, dissociation may present as apparent calm, insight, or even verbal fluency; what distinguishes it from Self-ledness is not surface composure but whether present evidence and embodied contact remain strongly online.

### 7.4 The 8 C’s

* The 8 C’s can be interpreted as the phenomenological signature of uncaptured inference under high Self-energy
* Keep this as a model-based interpretation, not as a fully derived theorem

Include:

* The 8 C’s likely reflect different aspects of the same regime rather than a homogeneous set; some are state qualities (calm, clarity), some relational stances (curiosity, compassion), and some action-enabling capacities (confidence, courage).

### 7.5 Self-like parts (short subsection — future direction)

This is the hardest real-world test case for the model.

* Self-like parts may mimic metacognitive language without generating actual revision
* They likely involve pseudo-witnessing: apparent M without sufficient V, or high verbal reflection without genuine uncaptured inference
* v1 does not yet distinguish them formally
* This is a major target for future models

---

## Section 8. Blending and witnessing

Purpose:

* Answer the first half of the central question

### 8.1 Blending

* low Self-energy + activation
* part priors dominate
* present context is functionally lost
* phenomenology: “I am afraid”

Include:

* Blending is not all-or-none; the model treats it as a graded balance between part dominance and context availability, with clinical thresholds corresponding to whether the system can still maintain dual awareness.

### 8.2 Witnessing

* high Self-energy + activation
* the same part stays active
* present context stays online
* phenomenology: “a part of me is afraid”

### 8.3 Why the distinction matters

* the key therapeutic issue is not whether a part activates
* it is whether activation occurs under capture or under context

This should be one of the conceptual centerpieces of the paper.

### 8.4 Clinical probe (new subsection)

* Clinically, the shift from blending to witnessing is often assessed not by the presence or absence of activation, but by the quality of the system's relation to the activated part — for example, whether the client can relate with curiosity or compassion rather than as or against the part. This can be understood as a real-time probe of Self-energy.

---

## Section 9. Why only witnessing permits lasting change

Purpose:

* Answer the second half of the central question

Main claim:

* Lasting change requires simultaneous activation and context

Explain:

* blending keeps the part active but context weak
* ordinary calm without activation keeps context online but the target priors dormant
* witnessing uniquely combines:

  * activation
  * context
  * non-capture

This is where you define unburdening as:

* durable revision of upstream priors in the part bundle

Include a partial revision prediction:

* The model predicts that revision can be partial. If activation is present and context is online but the witnessing window is brief or unstable, upstream priors may soften without fully revising. Clinically, this corresponds to burdens that lighten without fully releasing and to the repeated question in IFS practice: "Is there more?"

---

## Section 10. Protectors

Purpose:

* Give protectors a clear but bounded role in v1

Main claim:

* Protectors are policy priors plus access-control tendencies

Explain:

* they prevent exile takeover because takeover is destabilizing
* they are not fully formalized as separate agents in the main model
* this is sufficient for the paper’s scope

Include stronger simplification note:

* The present model formalizes only the minimum protector function: preventing destabilizing takeover. It does not yet model the full clinical richness of protectors, including trust assessment, conditional permission, role transformation, and distinct strategic styles across manager and firefighter configurations.

Include local optimality:

* Protector behavior is modeled as locally rational given the system’s history: if exile takeover has repeatedly been overwhelming, cautious gatekeeping is not pathology from the protector’s point of view but optimized prevention.

---

## Section 11. Multi-part polarization

Purpose:

* Show how the model explains a key IFS phenomenon beyond single-part activation

Main claim:

* Polarization occurs when two part-bundles assign high risk to each other’s preferred policy

Phenomenology explained:

* oscillation
* ambivalence
* rapid reversals
* each side feeling fully true when active
* exhaustion from unstable agency

State clearly:

* the main text provides the mechanism
* Appendix B provides the companion simulation

Include:

* Although the appendix formalizes polarization as a two-bundle system, clinical systems often contain larger polarization networks in which multiple protectors and exiles mutually recruit one another across several steps.

---

## Section 12. Main simulation

Purpose:

* Test the paper’s core claim in the minimal case

Main question:

* If the same part activates under different levels of Self-energy, does one regime yield blending and the other witnessing?
* Does only the second yield durable revision?

Use:

* one shared architecture
* same cue channels in all conditions
* same active part bundle
* different Self-energy regimes

Include explicitly:

* Exposure and witnessing are implemented over the same task structure, the same cue channels, and the same part-activation pathway; the manipulated difference is the inferential regime governed by Self-energy.
* The central comparison is meaningful only if part activation remains comparable across conditions, allowing the simulations to isolate relation-to-activation rather than activation magnitude itself.

Include model comparison:

* H1 self-state-upstream
* H2 threat-primary

---

## Section 13. Results / expected signatures

Purpose:

* Present the distinctive signatures of the theory

Core signatures:

* same activation can produce different relationships
* self-state shifts earlier under witnessing
* threat meaning shifts downstream
* generalization is better under witnessing
* adaptive fear remains in actual danger
* policy change should lag self-state change under H1: under witnessing, policy change should follow self-state revision rather than occurring simultaneously, consistent with the claim that protectors relax downstream of upstream revision

---

## Section 14. Discussion

Purpose:

* Clarify what the model explains and what it leaves open

Discuss:

* why the model counts as an IFS model despite being a minimal single-part model
* how it differs from exposure-only accounts
* how it differs from a pure schema model
* what Self-energy adds that ordinary safety or simple calm do not

Acknowledge what is not fully modeled:

* full protector negotiation
* therapist as explicit second agent
* multi-part clinical complexity in the main model
* neural implementation beyond the algorithmic level

Include specific limitations:

* The model describes individual-level dynamics in what is, clinically, a deeply relational process. Early in treatment, the therapist's Self-energy often supplies the stability that the client cannot yet maintain alone; the present model therefore captures a minimal intra-agent mechanism but not the full dyadic therapeutic field.

* The model does not yet distinguish genuine witnessing from self-like managerial imitation of witnessing. This is one of the most important unresolved problems for a computational account of IFS, because apparent metacognitive fluency is not always equivalent to genuine Self-ledness.

---

## Appendix A. Formation simulation

Purpose:

* Show how part-like bundles can form under overwhelm and low control without invoking literal structural rewiring

---

## Appendix B. Polarization simulation

Purpose:

* Show how two incompatible part-bundles can alternate in takeover and how higher Self-energy dampens that oscillation

---

# 3) H1 / H2 simulation spec

## Main simulation goal

Test the paper’s central claim:

**When the same part activates, does Self-energy determine whether activation becomes blending or witnessing — and does only the latter produce durable updating of the part’s outdated priors?**

A secondary goal is to compare two causal structures:

* **H1:** self-state is upstream of threat meaning
* **H2:** threat meaning is primary

---

## Shared architecture

### Hidden variables

Use three hidden factors:

1. **External context**
   `c ∈ {safe, dangerous}`

2. **Self-state**
   `s ∈ {child_helpless, adult_capable}`

3. **Threat meaning**
   `m ∈ {danger, safe}`

### Part activation

Do not make “part” a separate agent in the main model.

Instead define a **part activation strength**:

* `r_t ∈ [0,1]`

`r_t` indexes how strongly current cues and arousal match the learned part bundle.

Conceptually:

* higher cue-match
* higher arousal-match
* stronger learned bundle
  → higher `r_t`

This lets the same part activate in multiple conditions without changing the model family.

### Observation modalities

Use four modalities:

1. **External cue**
   `o_ext ∈ {ambiguous, clear_safe, clear_threat}`

2. **Interoceptive arousal**
   `o_int ∈ {calm, activated, panic}`

3. **Outcome**
   `o_out ∈ {relief, neutral, harm}`

4. **Present-context support cue**
   `o_ctx ∈ {alone_overwhelmed, supported_here_now}`

Important:

* `o_ctx` exists in both exposure and witnessing conditions
* witnessing is not given a special channel unavailable to exposure
* the difference is inferential regime, not model architecture

### Policies

Use three policies:

* `π_avoid`
* `π_inspect`
* `π_stay`

Interpretation:

* **avoid**: fast protective disengagement, little corrective information
* **inspect**: approach and sample more information
* **stay**: maintain contact long enough to sample context and arousal without immediate escape

---

## Self-energy in the model

### Theoretical structure

Self-energy is composite:

* `V_t` = autonomic-social safety / ventral-vagal availability
* `M_t` = metacognitive / epistemic depth

The model assumes:

* `E_t = f(V_t, M_t)`
* both contribute positively
* neither alone is sufficient for witnessing

### Simulation proxy

Represent Self-energy as a scalar:

* `E_t ∈ [0,1]`

### Operational role

Let:

* `π_part` = prior precision of the active part bundle
* `λ_ctx` = precision on present-context evidence

Then:

* `π_part_eff = r_t * π_part * exp(-βE_t)`
* `λ_ctx_eff = λ_ctx * exp(+γE_t)`

Interpretation:

* higher Self-energy reduces the effective dominance of the part bundle
* higher Self-energy increases the impact of present-context evidence
* the part is not turned off; its activation becomes more holdable

### Phenomenology readout: capture index

Define a derived readout that maps the inferential regime directly to the paper's hook:

* `C_t = π_part_eff / (π_part_eff + λ_ctx_eff)`

Interpretation:

* if `C_t > θ_high`, the system is in "I am afraid" mode (blending / capture)
* if `C_t < θ_low` while activation `r_t` remains high, the system is in "a part of me is afraid" mode (witnessing / context-held)

This lets the simulation speak directly to the paper's central distinction.

### External support parameter (optional)

Without making the therapist a second agent, add an external support input to Self-energy:

* `u_t` = external support input (therapist presence, relational scaffolding)

So Self-energy dynamics become:

* `E_{t+1} = clip(E_t + u_t + α·W_t - β·B_t, 0, 1)`

where `W_t` indexes successful witnessing episodes and `B_t` indexes blending episodes. This captures therapist-scaffolded Self-energy without complicating the model architecture.

---

## Part bundle representation

Represent the active part as a learned bundle:

* strong prior on `s = child_helpless`
* strong prior on `m = danger`
* strong policy prior on `π_avoid`

This bundle is the local control model that gets activated when `r_t` rises.

---

## Trial structure

### Trial timeline

Use a 3-step trial:

**t1: cue phase**

* observe `o_ext`
* observe `o_ctx`
* observe baseline `o_int`
* compute part activation `r_t`

**t2: action phase**

* infer hidden states
* choose policy among avoid / inspect / stay

**t3: outcome phase**

* observe `o_out`
* observe updated `o_int`
* update posteriors and learning variables

---

## H1: Self-state-upstream model

### Hypothesis

Self-state is causally upstream of threat meaning.

### Structural dependencies

* `o_ctx` primarily informs `s`
* `s` strongly conditions `m`
* `m` conditions policy

In words:

* if the system infers “I am still small and helpless,” ambiguous cues are more likely to mean danger
* if the system infers “I am adult and capable now,” the same ambiguous cues are more likely to be reinterpreted as safe or manageable

### Expected dynamics

Under witnessing:

* `P(s = adult_capable)` should rise first
* `P(m = safe)` should rise next
* `P(avoid)` should fall afterward
* generalization to new ambiguous-safe cues should be strong

Under exposure:

* `P(m = safe)` may rise gradually
* `P(s = adult_capable)` may shift weakly or later
* generalization should be narrower

---

## H2: Threat-primary model

### Hypothesis

Threat meaning is primary; self-state is downstream or secondary.

### Structural dependencies

* `o_ext` and `o_int` primarily inform `m`
* `m` then influences `s`
* policy follows from `m`

In words:

* the model treats the world as dangerous first, then derives helplessness from that interpretation

### Expected dynamics

* exposure and witnessing should look more similar
* self-state should change only after or alongside threat meaning
* the generalization advantage of witnessing should shrink

---

## Conditions

### Condition 1: Baseline

* safe world
* ambiguous cue
* low Self-energy
* free policy selection

Predicted signature:

* high part capture
* high avoidance
* little durable updating

### Condition 2: Exposure

* same safe world
* same ambiguous cue
* same part activation channel
* forced contact through `inspect` or equivalent
* Self-energy not specially elevated

Predicted signature:

* some threat updating
* weaker or slower self-state revision
* slower and narrower change

### Condition 3: Witnessing

* same safe world
* same ambiguous cue
* same part activation channel
* same cue contact as exposure
* Self-energy elevated

Predicted signature:

* same activation, different relationship
* part remains active but held in context
* earlier self-state revision
* downstream threat revision
* broader generalization

### Condition 4: Real-danger control

* dangerous world
* witnessing regime present

Predicted signature:

* adaptive fear remains
* the model does not predict indiscriminate calm

### Condition 5: Optional dissociation control

* safe world
* part activation present
* no Self-energy increase
* reduce effective context-evidence impact or increase disengagement tendency

Predicted signature:

* disturbance may drop
* durable updating remains poor
* distinguishes witnessing from numbed disengagement

---

## Main dependent measures

Track over trials:

* `P(avoid)`
* posterior over `s = child_helpless`
* posterior over `m = danger`
* Self-energy trajectory `E_t`
* generalization to a new ambiguous-safe cue after learning
* capture index `C_t` (phenomenology readout)

### Policy-ordering analysis

Under H1, test the temporal ordering explicitly:

* `P(s = adult_capable)` should rise first
* `P(m = safe)` should rise second
* `P(avoid)` should fall third

This tests the claim that protectors relax downstream of upstream self-state revision.

### Partial revision regime

Not every witnessing event should fully unburden. Test by:

* varying duration of high `E_t` (brief vs sustained witnessing windows)
* varying magnitude of context mismatch

Predicted result:

* short or unstable witnessing windows soften but do not fully revise upstream priors
* maps to the clinical observation of partial unburdening ("Is there more?")

---

## Core discriminating tests

### Test 1: Same activation, different relationship

For matched `r_t`, does:

* low `E_t` produce blending-like capture?
* high `E_t` produce witnessing-like context holding?

### Test 2: Order of revision

Under witnessing, does `s` shift before `m`?

### Test 3: Exposure comparison

Does exposure show slower or weaker self-state revision than witnessing under the same basic cue contact?

### Test 4: Generalization

Does witnessing generalize better to novel ambiguous-safe cues?

### Test 5: Real danger preservation

Does witnessing preserve adaptive fear in dangerous contexts?

### Test 6: Model comparison

Does H1 fit the resulting trajectories better than H2?

### Test 7: Policy ordering under H1

Under witnessing, does policy change lag self-state change? Specifically: does `P(avoid)` decrease only after `P(s = adult_capable)` has risen?

### Test 8: Partial revision

Under brief or unstable witnessing windows, do upstream priors soften without fully revising?

---

## Falsifiers

The proposed account is weakened if:

* high Self-energy does not change the relation to activation
* witnessing does not move self-state earlier than exposure
* exposure produces equal or better generalization
* H2 fits as well as H1
* witnessing collapses fear globally, including in real danger
* dissociation control looks indistinguishable from witnessing

---

## Appendix A simulation: Formation

### Question

Can a part-like bundle form under overwhelm and low control without invoking literal structural rewiring?

### Setup

Use the same hidden variables:

* context
* self-state
* threat meaning

Start with relatively flat priors and low Self-energy.

### Acquisition phase

Expose the agent to repeated episodes with:

* dangerous context
* ambiguous or threat-weighted cues
* low support cue
* low controllability

Allow:

* avoidance to succeed in short-term error reduction
* inspect / stay to fail or be costly

### Learning targets

Across episodes, strengthen:

* prior on `s = child_helpless`
* prior on `m = danger`
* policy prior on `π_avoid`

### Controllability gradient

Compare at least two conditions:

* **Condition A:** high threat + low control (classic acute trauma formation)
* **Condition B:** high threat + high control (frightening but not part-forming)

Optional third condition:

* **Condition C:** moderate chronic threat + chronic low support (neglect-like formation)

### Main prediction

Formation should depend more strongly on:

* **low control under threat**
  than on:
* threat alone

The controllability gradient tests this directly: Condition A should produce rigid bundles, Condition B should not, and Condition C should produce bundles with different characteristics (slower formation, potentially different rigidity profile).

### Readout

After acquisition, place the agent in a safe ambiguous context.

If formation occurred, the agent should:

* infer helplessness too readily
* infer danger too readily
* avoid despite safety

This demonstrates formation of a part-like bundle without requiring explicit structural rewiring.

---

## Appendix B simulation: Multi-part polarization

### Question

How does the model explain multi-part polarization and its phenomenology?

### Core idea

Polarization occurs when two part-bundles assign high expected danger to each other’s preferred policy.

### Additional appendix-only variable

Introduce:

* `p ∈ {A, B, none}` or two continuous activation strengths `a_A`, `a_B`

### Example pair

* **Part A**: approach / attach / disclose
* **Part B**: withdraw / protect / avoid

Each bundle includes:

* self-state
* world-state
* preferred policy
* expected outcome
* threat estimate about the other bundle’s policy

### Dynamics

Low Self-energy:

* activation of A increases expected danger of B’s policy
* activation of B increases expected danger of A’s policy
* mutual triggering produces anti-phase oscillation

Example dynamical form:

* `a_A,t+1 = σ(θ_A cue_A + κ_A I[action_B,t] - ηE_t)`
* `a_B,t+1 = σ(θ_B cue_B + κ_B I[action_A,t] - ηE_t)`

where:

* `κ_A, κ_B > 0` encode mutual threating
* higher `E_t` dampens takeover dynamics

### Predicted phenomenology

Low Self-energy:

* rapid reversals
* unstable commitments
* “both feel true, but not at the same time”
* exhaustion and loss of coherent agency

Higher Self-energy:

* both part-bundles can be represented without either taking over
* oscillation dampens
* mixed or negotiated policy becomes available
* the contradiction becomes observable rather than identity-level

### Dependent measures

* oscillation frequency
* switching rate
* part activation anti-correlation
* policy entropy
* duration of mixed-policy stability as Self-energy increases
* **time spent in simultaneous representation without takeover** (both parts active, neither dominating)
* **time to negotiated policy emergence** (first trial where the selected policy is not the preferred policy of either dominant part)

These last two measures are closer to what clinicians actually care about: the transition from "stuck oscillation" to "both perspectives held, new possibility available."

This appendix provides a compact computational account of polarization without forcing the main paper to become a full multi-part parliament model.

