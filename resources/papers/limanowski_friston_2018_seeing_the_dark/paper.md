# 'Seeing the Dark': Grounding Phenomenal Transparency and Opacity in Precision Estimation for Active Inference

**Authors:** Jakub Limanowski<sup>1</sup>, Karl Friston<sup>1</sup>

**Affiliations:**
1. The Wellcome Centre for Human Neuroimaging, Institute of Neurology, University College London, London, United Kingdom

**Journal:** Frontiers in Psychology
**Published:** May 4, 2018
**DOI:** [10.3389/fpsyg.2018.00643](https://doi.org/10.3389/fpsyg.2018.00643)
**PMCID:** PMC5945877

---

## Abstract

We propose that phenomenal transparency and opacity can be grounded in precision estimation within the active inference framework. Transparency—the default mode of conscious experience where mental representations feel like direct contact with reality—is linked to high precision beliefs about action. Opacity—the introspective awareness that experience is constructed—emerges when precision is deployed to specific prediction errors via attentional mechanisms.

A minimal sense of agency and selfhood cannot become opaque because beliefs about action necessarily remain transparent: these are the beliefs that generate the prior precision expectations enabling opacity elsewhere. This reconciles the Self-model Theory of Subjectivity (SMT) with predictive processing accounts of brain function and illuminates why conscious experience is necessarily perspectival.

---

## Introduction

Phenomenal consciousness has both transparent and opaque aspects. When we perceive a red apple, we typically experience direct contact with the apple itself—not awareness of our brain's construction of "redness." Yet we can also become aware that our experiences are representations: in dreams, illusions, or philosophical reflection, the constructed nature of experience becomes apparent.

Thomas Metzinger's Self-model Theory of Subjectivity (SMT) provides a comprehensive account of this transparency-opacity distinction. We propose that active inference—specifically, the estimation and deployment of precision—provides the computational mechanism underlying these phenomenal properties.

Our central claim: **transparency is a necessary aspect of beliefs about action**, while **opacity involves deploying introspective attention via precision expectations**. The wordplay in our title—"seeing the dark"—captures this: holding beliefs about our very low precision (uncertainty) enables phenomenal opacity. We can, metaphorically, "see" the darkness of our own uncertainty.

---

## Phenomenal Transparency and Opacity

### Definitions

**Phenomenal Transparency:** A mental representation is phenomenally transparent when its construction process remains inaccessible to introspective attention. The result is an experience of direct, unmediated contact with mind-independent reality—"like looking through a window onto the world."

**Phenomenal Opacity:** A representation is phenomenally opaque when its construction process becomes introspectively accessible. The representation then appears as "being constructed by one's mind" rather than as direct contact with reality.

### Key Properties

**Epistemic Reliability:** The transparency-opacity gradient marks subjective certainty about whether experience originates internally or externally. This is independent of actual veridicality—a transparent perception can be illusory, and an opaque one can be accurate.

**Cognitive Impenetrability:** One cannot simply "think oneself out of" phenomenal transparency. Knowing that the Müller-Lyer lines are equal length doesn't make them look equal. Transparency resists rational override.

**Graded Character:** Transparency and opacity exist on a continuum. Experiences can be more or less transparent depending on context and attention.

### Examples

| Transparent | Opaque |
|-------------|--------|
| Seeing colors | Lucid dreaming |
| Experiencing body location | Deliberate thought |
| Perceiving objects | Pseudo-hallucinations |
| Sense of agency | Introspecting on perception |
| Flow states | Mindfulness meditation |

---

## Active Inference Framework

### Core Principles

**Free Energy Principle:** Living systems minimize surprise by performing inference—selecting and inverting probabilistic generative models to explain sensory input.

**Hierarchical Generative Models (HGM):** The brain implements stacked predictive mappings where higher levels contextualize and modulate lower levels. Higher levels encode more abstract, temporally extended regularities.

**Predictive Coding:** Free energy approximates as precision-weighted prediction errors passed up the hierarchy. Descending predictions attempt to explain away ascending errors.

### Precision: The Key Mechanism

**Definition:** Precision is the inverse variance of a probability distribution—a measure of certainty or confidence. In neural terms, precision corresponds to synaptic gain.

**Precision Estimation:** The brain must not only estimate hidden states but also estimate the precision (reliability) of its predictions and prediction errors. This is a form of second-order inference.

**Precision and Attention:** Attention is implemented as precision weighting. Attended signals have their precision increased, giving them greater influence on inference.

```
Weighted prediction error = Precision × Raw prediction error
                         = (1/σ²) × (observation - prediction)
```

### Active Inference and Policy Selection

Active inference extends predictive coding to action. Agents select policies (action sequences) that minimize expected free energy—essentially, they act to confirm their predictions.

**Critical insight:** Policies necessarily entail a specification of precision. To plan an action, the agent must represent:
1. Expected outcomes of the action
2. Expected precision (reliability) of those outcomes
3. The action-dependent changes in precision

This means beliefs about action inherently carry precision expectations.

---

## Central Argument: Precision Grounds Transparency/Opacity

### Transparency as Default

We propose that **transparent states are the default for conscious inference**. When predictive models are working well—when prediction errors are successfully suppressed—experience feels like direct contact with reality. The machinery of inference is invisible precisely because it's working.

### Opacity Through Introspective Attention

**Opaque states emerge when precision is deployed to specific prediction errors via introspective attention.** This is a form of mental action—broadcasting top-down predictions of precision to lower levels, making certain prediction errors salient.

To make a representation opaque, the system must:
1. Generate predictions about its own representational states
2. Estimate the precision of those predictions
3. Detect prediction errors in this meta-representational process
4. Weight those errors sufficiently to reach conscious awareness

### Why Self-Beliefs Remain Transparent

**Our key claim: beliefs about action cannot become opaque because they generate the very precision expectations that enable opacity elsewhere.**

Consider: to introspect (a mental action), you must have beliefs about what you're doing (introspecting). These action-beliefs carry precision expectations. But you cannot simultaneously:
1. Use these precision expectations to enable introspection
2. Make these same precision expectations the target of introspection

The beliefs that enable "seeing" cannot themselves be "seen" in the same moment. A minimal sense of agency must remain transparent because it provides the epistemic foundation for any opacity.

### The Wordplay Explained

"Seeing the dark" = holding beliefs about very low precision

When we become aware that our perceptions might be unreliable (low precision), we can experience opacity—the sense that experience is constructed. We "see" our uncertainty. But the seeing itself (the act of attention) must remain transparent.

---

## Implications for Selfhood

### Minimal Phenomenal Selfhood (MPS)

MPS—the basic, pre-reflective experience of being a self—is necessarily transparent. You don't experience yourself as a representation but as the subject having representations.

This follows from our analysis: the self-model that enables agency (and thus introspection) must remain transparent to perform its function.

### The Epistemic Agent Model (EAM)

Beyond MPS, humans develop a more sophisticated self-model: the **Epistemic Agent Model**. This is a transparent self-model equipped with:
- Attentional agency (ability to direct precision)
- Metacognitive capacity (beliefs about beliefs)
- Temporal thickness (planning horizons extending into past and future)

The EAM experiences itself as a "knowing self"—an entity that can direct attention, evaluate evidence, and form justified beliefs. Yet this self-model remains phenomenally transparent; we don't typically experience ourselves as representations.

### Temporal Thickness and Depth

**Temporal thickness** refers to how far into past and future the agent's planning horizons extend. This is associated with levels of consciousness—more temporally extended models support richer conscious experience.

**Temporal depth** refers to the hierarchical depth of inference—how many levels of abstraction the model employs. Deeper models can represent more abstract regularities.

These interact with precision: attending to temporally extended patterns requires estimating precision over longer time scales.

---

## Formal Concepts

| Concept | Definition | Implementation |
|---------|------------|----------------|
| **Belief** | Conditional expectation (probabilistic representation) | Neural activity encoding sufficient statistics |
| **Precision** | Inverse variance; confidence weighting | Synaptic gain modulation |
| **Prediction** | Top-down expectation about lower-level states | Descending neural signals |
| **Prediction Error** | Mismatch between prediction and input | Ascending neural signals |
| **Introspective Attention** | Precision deployed to internal states | Meta-level precision optimization |
| **Mental Action** | Changing precision expectations | Policy selection over attention |
| **Markov Blanket** | Statistical boundary separating system from environment | Sensory and active states |

### The Precision-Weighting Hierarchy

At each level of the hierarchy:

```
Level N:   μ_n ← μ_n + κ · Π_n · ε_n

Where:
  μ_n = beliefs at level n
  Π_n = precision at level n
  ε_n = prediction error at level n
  κ   = learning rate
```

Precision (Π) determines how much prediction errors update beliefs. Attention increases Π for selected signals.

For introspection, add a meta-level:

```
Meta-level: μ_meta ← μ_meta + κ · Π_meta · ε_meta

Where:
  ε_meta = (observed internal state) - (predicted internal state)
  Π_meta = precision of meta-level predictions
```

Opacity emerges when ε_meta is large and Π_meta is high—when surprising internal states receive attention.

---

## Phenomenological Examples

### Transparent States
- **Perceiving colors:** We experience red, not "my brain's encoding of 650nm light"
- **Body location:** We feel ourselves at a location, not "a model of body position"
- **Sense of agency:** Actions feel self-generated without representing the generative process
- **Saccadic suppression:** We cannot experience the optical flow during eye movements—transparency is "written into" action execution

### Opaque States
- **Lucid dreams:** Awareness that the dream is a construction
- **Meditation:** Attending to the constructed nature of experience
- **Pseudo-hallucinations:** Hallucinations recognized as such
- **Philosophical reflection:** Considering that perceptions are representations
- **Perceptual learning:** Becoming aware of previously invisible features

### Pathological States
- **Derealization:** The world feels unreal—aberrant opacity in world-model
- **Depersonalization:** The self feels unreal—aberrant opacity in self-model
- **Psychosis:** Loss of insight—aberrant transparency in hallucinations
- **Schizophrenia:** Disordered precision control across multiple domains

---

## Predictions and Implications

### For Consciousness Research

1. **Consciousness requires self-modeling:** Any conscious system must have a (transparent) self-model to enable attention and opacity

2. **Transparency is primary:** Opacity is achieved by adding meta-level processing; transparency is the default

3. **Agency is foundational:** The sense of agency provides the epistemic ground for all other self-representation

### For Psychopathology

Disorders of insight (psychosis) and disorders of presence (depersonalization/derealization) can be understood as opposite failures of precision control:

| Disorder | Precision Abnormality | Phenomenal Result |
|----------|----------------------|-------------------|
| Psychosis | Aberrantly high precision on false predictions | Transparency of delusions/hallucinations |
| Depersonalization | Aberrantly low precision on self-model | Opacity/unreality of self |
| Derealization | Aberrantly low precision on world-model | Opacity/unreality of world |

### For Meditation and Contemplative Practice

Meditation practices that cultivate "witnessing" or "observer" awareness may work by:
1. Increasing meta-level precision (attention to mental processes)
2. Decreasing object-level precision (deconstructing perceptual transparency)
3. Revealing the constructed nature of experience (cultivating strategic opacity)

Yet the witness itself remains transparent—a finding consistent with reports from experienced meditators.

---

## Conclusions

We have proposed that phenomenal transparency and opacity can be grounded in precision estimation within active inference:

1. **Transparency is the default** when predictive models successfully suppress prediction errors

2. **Opacity emerges through introspective attention**—deploying precision to prediction errors about internal states

3. **Self-beliefs about action remain necessarily transparent** because they generate the precision expectations enabling opacity elsewhere

4. **Consciousness and self-consciousness necessarily coexist**—any conscious world-model requires a (transparent) self-model

This framework reconciles the Self-model Theory of Subjectivity with predictive processing accounts, providing mechanistic grounding for phenomenological distinctions. The title's wordplay captures the core insight: we can "see the dark"—become aware of our uncertainty—but the seeing itself must remain light.

---

## Open Questions

1. Can phenomenal world-models exist without phenomenal self-models?
2. What is the relationship between non-conscious and conscious inference?
3. How do social contexts modulate transparency/opacity?
4. Can artificial systems achieve genuine phenomenal transparency?

---

## References

*For the complete reference list, see the original publication at [doi.org/10.3389/fpsyg.2018.00643](https://doi.org/10.3389/fpsyg.2018.00643)*

Key references include:

- Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience*, 11(2), 127-138.
- Hohwy, J. (2013). *The Predictive Mind*. Oxford University Press.
- Metzinger, T. (2003). *Being No One: The Self-Model Theory of Subjectivity*. MIT Press.
- Seth, A. K. (2013). Interoceptive inference, emotion, and the embodied self. *Trends in Cognitive Sciences*, 17(11), 565-573.
- Limanowski, J., & Blankenburg, F. (2013). Minimal self-models and the free energy principle. *Frontiers in Human Neuroscience*, 7, 547.

---

## Citation

Limanowski, J., & Friston, K. (2018). 'Seeing the Dark': Grounding Phenomenal Transparency and Opacity in Precision Estimation for Active Inference. *Frontiers in Psychology*, 9, 643. https://doi.org/10.3389/fpsyg.2018.00643
