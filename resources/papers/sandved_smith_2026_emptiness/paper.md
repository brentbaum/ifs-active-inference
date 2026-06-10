# There is no self-evidence: A physics of emptiness realisation

**Authors:** Lars Sandved-Smith<sup>1</sup>*, Chris Fields<sup>2</sup>, Thomas Doctor<sup>3,4,5</sup>, Ruben Laukkonen<sup>6,7,8</sup>, Jakob Hohwy<sup>1</sup>

**Affiliations:**
1. Monash Centre for Consciousness and Contemplative Studies, Monash University, Melbourne, Australia
2. Allen Discovery Center, Tufts University, Medford, MA, USA
3. Kathmandu University Centre for Buddhist Studies, Rangjung Yeshe Institute, Kathmandu, Nepal
4. 84000: Unlocking the Tibetan Buddhist Canon for All, Fremont, CA 94539, USA
5. Center for the Study of Apparent Selves, Kathmandu 44600, Nepal
6. Flourishing Intelligence Program, Centre for Eudaimonia and Human Flourishing, Linacre College, University of Oxford, Oxford, UK
7. Department of Psychiatry, University of Oxford, Oxford, UK
8. LIFE, London, UK

*Corresponding author: lars.sandvedsmith@gmail.com

**Published:** May 23, 2026

**Keywords:** free energy principle, active inference, quantum reference frames, emptiness, awakening, self-model, Buddhist philosophy, contextuality, Bayesian model reduction, criticality

---

## Abstract

Any system that persists must minimise surprisal, thereby gathering evidence for its own generative model, a process known as *self-evidencing*. However, one dimension of self-evidencing is provably impossible: evidencing the boundary that would constitute the agent as an entity *separate from* their environment. Recent results in quantum information theory demonstrate that no finite system can measure the entanglement entropy across its own boundary, rendering the separability of agent from environment permanently unevidenceable. Subjectively therefore, there can be no evidence for a self separate from the world. We propose that the Buddhist notion of awakening, in the sense of stable realisation of *emptiness*, can be understood as the embodied recognition of this impossibility. We formalise the belief in separation as a structural prior over an agent's quantum reference frame (QRF) deployments, constraining all measurement frames to respect a self/environment partition. We describe how contemplative practice progressively opacifies this constraint by developing a model of the agent's own QRF dynamics, revealing the partition as a contingent modelling choice rather than a given feature of reality. Once visible, the prior is eliminated via Bayesian model reduction resulting in a post-dual agent with unconstrained QRF deployments. We argue that such priors suppress the inherent contextuality of the boundary and that their removal constitutes a formal counterpart to the Buddhist notion of emptiness realisation. Self-evidencing may continue unimpeded after this transition, grounded in structural realism about causal regularities, while the ontological commitment to a bounded self is relinquished. We discuss empirical predictions, including altered dynamical regimes in neural systems, and the formal relationship between emptiness realisation and compassion.

---

## 1. Introduction

This paper outlines a proposed explanatory model of the Buddhist notion of awakening in the language of first-principles physics. Our model leverages recent developments in quantum information-theoretic formulations of the free energy principle (Fields et al., 2022) as well as results from quantum contextuality and the frame problem (Fields and Glazebrook, 2023). Awakening is understood as the *stable realisation of the empty nature of all phenomena*, most importantly the phenomenon of the subjective experience of a self as an entity separable from the environment. These terms will be unpacked further below.

The aim of this work is to contribute to the development of a model of awakening in a contemporary formal language. We draw on classical Buddhist formulations in an effort to identify and translate key principles into conceptual and formal formats, developed with the help of insights and frameworks from cognitive science and quantum information theory. We do not claim that the model presented here is fundamentally better than preceding articulations of awakening, of which there are many beautiful and rigorous examples across Buddhist traditions. If successful, this will simply be another "finger pointing at the moon," in a language that might provide a generative bridge between the contemplative and scientific domains of inquiry. We suggest that such bridging can empower research in areas such as well-being and artificial intelligence, by contributing to the emergence of interfaces between biology and technology that are both ethically grounded and conducive to human flourishing.

We argue that it is accurate to model emptiness realisation as the recognition of a fundamental feature of any agent's embodiment: that they can never make a measurement (receive a sensory observation) that provides evidence for their separation from the environment. Recent work in quantum information theory has demonstrated this from a context-transcendent theoretical perspective; indeed no such measurement can be made by any finite agent (Fields and Glazebrook, 2023). We therefore relate awakening to the embodied insight into this somewhat counter-intuitive aspect of agency, the impossibility of evidence for a separate agent.

In other words, an awakened agent is one that recognises that it can never know whether it is separable from, or fully entangled with, its environment. The agent may seek to gather evidence for the belief "I am doing *x*," yet it knows that it cannot have any evidence for the belief "'I' refers to this or that" or indeed for "'I' refers to everything." We argue that this formally captures an aspect of the insight into emptiness as well as true non-duality, which transcends the conventional dichotomy between duality (self–world separation) and its denial (oneness). The nature of self is seen to be necessarily indeterminable—that is, lacking any ontological status, or *empty* in Buddhist terminology.

We go on to demonstrate that this realisation applies equally to any belief in separation whatsoever, including boundaries that define objects or other agents in experience. This understanding is encoded by the agent's embodiment (in the *structure* of the generative model, as discussed in Section 4); hence our model casts awakening as an embodied understanding that all things, including the self, have no possible evidence, within subjective experience, for independent existence.

We point out that this does not imply a form of irrealism nor solipsism. The subjective unevidenceability of boundaries does not entail the absence of structure. The very possibility of self-evidencing presupposes mind-independent causal regularities. Without lawlike structure external to the agent, no generative model could accumulate evidence (von Helmholtz, 1977; Hohwy, 2025). What the agent can do is (approximately) infer this relational, causal structure, and some models of it are demonstrably better than others in terms of predictive accuracy. The agent may therefore continue to operate with beliefs about boundaries, e.g., a self-model, and these models can be more or less advantageous to the agent's adaptability and objectives, i.e., to its self-evidencing. What changes with awakening, therefore, is not the agent's capacity for structural modelling but the *status* of those models: boundary designations are recognised as pragmatic tools for navigating real structure, not as reflections of ontological divisions in nature. Information encoded upon the agent–world boundary is recognised by the agent, yet without overriding the acknowledgement that the boundary itself can never be ascertained as ontologically real. Thus, our model motivates a relational perspective on all things, demonstrating that any ontological leaps beyond belief in minimal structural realism in one's inferences are unfounded, and that this understanding is encoded by the agent's embodiment upon full awakening.

The upshot is that the agent is liberated from a class of rigid prior beliefs, which we may categorise as beliefs in the ontological truth or givenness of boundaries, and equally, metaphysical belief in boundarylessness (sometimes known as "attachment to emptiness"). We argue that this results in a combination of reduced prediction error and an open-ended cognitive and behavioural flexibility, as all boundary beliefs remain subject to revision. We relate this to Buddhist views of impermanence, which traditionally are seen to facilitate insight into emptiness. In short, this is a model reduction that results in improved free energy minimisation and greater synchrony between the agent and their environment.

The paper is structured as follows. In Section 2, we review the quantum-information-theoretic formulation of the free energy principle and introduce the boundary construct between agent and environment. In Section 3, we present the core result, that no finite system can measure the entanglement entropy across its own boundary, rendering the separability of agent from environment permanently unevidenceable, and show that this impossibility extends to all boundaries whatsoever. In Section 4, we model the contemplative path as progressive opacification of a separation prior, culminating in its elimination via Bayesian model reduction. In Section 5, we characterise the post-dual agent's unconstrained inference and show that self-evidencing continues unimpaired and improved, grounded in structural realism about causal regularities. Finally, in Section 6, we discuss the correspondence between emptiness and quantum contextuality, offer a formal account of the relationship between emptiness and compassion, present empirical predictions linking emptiness realisation to critical neural dynamics and outline directions for future computational work.

## 2. The quantum free energy principle

The free energy principle (FEP) states that any system that persists through time, i.e., that remains identifiable as a bounded entity, must behave so as to minimise an upper bound on surprisal, formalised as variational free energy (VFE) (Friston, 2010; Parr et al., 2022). In its classical formulation, the FEP considers a joint state decomposable into internal, external and blanket states, where the blanket states (further partitioned into sensory and active states) mediate all interactions and render internal and external states conditionally independent (Friston, 2019). The blanket is almost irresistibly read as a division in physical space rather than state space, but this spatial reading is not licensed by the FEP directly.

Fields et al. (2022) reformulate the FEP in the language of quantum information theory. We adopt this quantum formulation (qFEP) as the more appropriate expression of the FEP for modelling awakening. The contemplative path involves investigating the assumptions that structure experience and, with practice, finding them to be mental constructions rather than manifestations of some deeper objective truth. This includes the experience of space and time. A formalism that bakes in the assumptions one is trying to investigate is therefore the wrong tool for explaining that aspect of the path.

The qFEP reformulation drops two assumptions that the classical FEP inherits from its statistical-mechanical origins: that the system is embedded in a pre-given spacetime and that randomness is observer-independent. The given-ness of background *time* is the assumption that matters most here. The classical FEP describes the agent's dynamics as trajectories unfolding over an assumed time parameter, which presupposes time to be a measurable quantity rather than an agent's construction.[^1] In any relativistically consistent theory, observable time and observable space are aspects of a single observable spacetime. Taking observable background time as given therefore commits the formalism, implicitly, to an observable background spacetime as well, which makes it very easy to mistakenly read the blanket as a spatial boundary. The qFEP requires no such observable backdrop. It still relies on a background time parameter, but that parameter is not itself observable. Observable time is instead constructed internally, from the correlations between a clock subsystem and the rest of the world (Page and Wootters, 1983). The qFEP is therefore developed in an explicitly "spacetime-background free" setting. Observable time, like observable space and the agent–environment separation, is not a feature of the formalism's setup but a structure that the agent can be described as constructing from its own sequence of measurements on the boundary.

This aligns the qFEP with a broad trend in modern theoretical physics, which increasingly treats spacetime as emergent from a deeper, non-spatiotemporal informational structure. For example, in the holographic and entanglement-geometric programme, spacetime connectivity is built from patterns of quantum entanglement (Van Raamsdonk, 2010; Maldacena and Susskind, 2013), while in the positive-geometry programme locality and unitarity are derived from a more primitive object rather than assumed (Arkani-Hamed and Trnka, 2014).

What remains is more general and, for our purposes, more apt and revealing modelling framework. The starting point is the principle of unitarity, the conservation of information, and the question becomes, what can any finite system know about its relationship to everything else?

To follow the argument, a few concepts from quantum information theory are needed. We introduce them here as to the depth we require rather than in their full technical rigour (for which the reader is referred to Fields et al. (2022) and Fields and Glazebrook (2023)).

[^1]: More precisely, classical Bayesian mechanics is written in generalised coordinates of *motion*, the state augmented with its temporal derivatives (Friston et al., 2023), so its formal commitment is to a background time parameter together with classical, observer-independent fluctuations. The Markov blanket is itself a partition of state space by conditional independence, not a boundary in physical space.

### 2.1 Physical interaction as information exchange

Consider an effectively isolated system *U* (which we can think of as "everything relevant") decomposed into two components, *A* and *B*. One might picture an organism and its environment, but the formalism applies to any two interacting systems at any scale.

The physics of such a system is governed by its *Hamiltonian*, the mathematical object that encodes how energy flows and how the system evolves over time. The total Hamiltonian decomposes naturally into three parts.

$$H_U = H_A + H_B + H_{AB} \tag{1}$$

Here $H_A$ and $H_B$ describe the internal dynamics of each component on its own, while $H_{AB}$, the interaction Hamiltonian, captures everything that happens between them. It is $H_{AB}$ that makes the boundary interesting, it is where *A* and *B* exchange information.

The space of all possible states that a quantum system can occupy is called its *Hilbert space*, denoted $\mathcal{H}$. When we say the total system factorises as $\mathcal{H}_U = \mathcal{H}_A \otimes \mathcal{H}_B$, we are asserting that there exists a way of carving the universe into "states of *A*'s degrees of freedom" and "states of *B*'s degrees of freedom." This factorisation defines a decompositional boundary $\mathscr{B}$ between them.

A key question is whether *A* and *B* are *separable*, i.e., whether they can be described independently of each other. In quantum theory, the joint state $|AB\rangle$ is separable when it can be written as a simple product $|A\rangle |B\rangle$, meaning that knowing everything about *A* tells you nothing new about *B* and vice versa. Separability is measured by the *entanglement entropy* $\mathcal{S}$, which is zero when the systems are fully independent and increases as they become more quantum correlated (entangled):

$$\mathcal{S}(|AB\rangle) = 0 \iff |AB\rangle = |A\rangle |B\rangle \quad \text{(separability)} \tag{2}$$

When *A* and *B* are separable, the boundary $\mathscr{B}$ between them can be treated as a *holographic screen*: an array of *N* binary quantum channels (quantum bits or "qubits") through which the two systems communicate. Under this condition, the interaction Hamiltonian takes an elegant form (Fields et al., 2022):

$$H_{AB} = \beta^k k_B T^k \sum_{i=1}^{N} M_i^k \tag{3}$$

where $k = A$ or $B$, each $M_i^k$ is an operator with eigenvalues $\pm 1$ (i.e., an operator implementing a yes/no question), and $\beta^k k_B T^k$ is a thermodynamic prefactor encoding the energetic cost of the exchange for the system *k*; see (Fields and Glazebrook, 2025, Ch. 2) for details and further discussion. The deep insight, following Wheeler's "it from bit" (Wheeler, 1990), is that all physical interaction between separable systems reduces to:

$$\text{Physical interaction} = \text{Thermodynamics} \times \text{Yes/No questions} \tag{4}$$

Every interaction across the boundary is an exchange of binary messages, paid for in energy. *A* and *B* interact by alternately preparing and measuring the states of the qubits comprising the channel, i.e., by alternately writing and reading *N*-bit strings on the shared screen $\mathscr{B}$. This communication is bidirectional and informationally symmetric by definition. It is, however, deeply non-classical. Each of the $M_i^k$ acts with respect to a local reference frame that depends only on the internal dynamics $H_k$ of the system that implements it; the reference frames and hence the *semantics* of the exchanged bits are chosen, on each cycle of interaction, completely independently by *A* and *B*. This perspective on the nature of communication thus reveals two of its general features: first, that there is no such thing as purely passive observation, rather all observation is interaction; and second, that the languages employed by the communicating systems can never be assumed to be exactly the same, and indeed may differ completely.

A point of fundamental importance for what follows is that the boundary $\mathscr{B}$ is not a physical object discovered in the world. It is a *modelling choice*, an ancillary construct that provides a convenient representation for the interaction (Fields and Levin, 2025). The total Hamiltonian $H_U$ does not specify where to draw the line between *A* and *B*; it is equally consistent with any factorisation of the Hilbert space (Zanardi, 2002). Nothing about the physics of *U* favours any one decomposition, any one placement of $\mathscr{B}$, over any other.

This means that the boundary between A (e.g., "you") and B (e.g., "the world") is not written into the fundamental physics. It is imposed by an external theorist, or equivalently, assumed by the agent itself as part of its generative model. Different observers may draw the boundary differently, and no observation can adjudicate between them. This does not mean that all boundary placements are equally good. Some decompositions will support generative models with far greater predictive accuracy than others, and it is precisely this that makes certain boundaries pragmatically indispensable. The point is that their value is *predictive*, not *ontological*. The boundary is, from the outset, a construct that earns its keep by being useful, not by being true. This observation will become central in Section 3, where we show that the boundary construct cannot even in principle be validated from within the bounded agent's perspective.

### 2.2 Variational free energy in the quantum setting

What does it mean for *A* to model *B* well? At each moment, *A* maintains a generative model, a set of expectations about what signals will arrive on the boundary $\mathscr{B}$. The quality of this model can be quantified in terms of *prediction error*, the distance between what *A* expects and what actually arrives.

$$\text{Er}_E(k) = d\big(\mathbb{M}_E^A(k), \mathbb{M}_E(k)\big) \tag{5}$$

where $\mathbb{M}_E^A(k)$ is *A*'s generative model at internal time *k* and $\mathbb{M}_E(k)$ is the actual pattern of observations. The FEP states that *A* will act so as to minimise this prediction error (Fields et al., 2022). Variational free energy (VFE) provides an upper bound on prediction error, and it decomposes into two sources:

$$\text{VFE} = \text{Noise} + \text{Insufficient learning} \tag{6}$$

"Noise" captures irreducible uncertainty, including aspects of *B* that *A* cannot observe, interference between incompatible measurement strategies, and any mismatch between how *A* and *B* carve up their shared boundary. "Insufficient learning" is simply the gap between the model *A* has and the best model it could have given its observations.

This decomposition leads to a remarkable asymptotic result. As prediction error approaches zero, the FEP drives *A* and *B* toward ever-closer alignment in how they structure their interaction across $\mathscr{B}$. Perfect alignment would require *A* and *B* to share identical measurement frameworks, and hence identical local reference frames for each operator $M_i^k$, which – by the no-cloning theorem of quantum mechanics – is only possible if they are entangled rather than separable. In other words, the FEP is asymptotically equivalent to the Principle of Unitarity (Fields et al., 2022). Free energy minimisation drives toward the dissolution of the very separability condition that defines a bounded agent. The better *A* gets at modelling *B*, the less meaningful the boundary between them becomes. Recall that this boundary was a modelling choice to begin with; the physics is now telling us that optimal modelling erodes the very distinction the modeller imposed.

## 3. There is no self-evidence

We now present the core argument of this paper: that no finite agent can obtain evidence for its own boundary.

### 3.1 The impossibility of measuring the boundary

Fields and Glazebrook (2023) prove the following:

**Corollary 1** (Fields & Glazebrook, 2023, Cor. 3.1). *No finite system A can measure the entanglement entropy $\mathcal{S}(|AB\rangle)$ across the boundary $\mathscr{B}$ that separates it from its environment B.*

To appreciate why this result holds, recall what entanglement entropy measures. $\mathcal{S}(|AB\rangle)$ quantifies the degree to which *A* and *B* are quantum correlated: zero when they are fully independent (separable), and increasing as they become more entangled. Determining this quantity requires probing all components of the joint state $|AB\rangle$. This is not something that can be done from one side of the boundary. The measurement operators $M_i^A$ available to *A* act exclusively on the qubits comprising the boundary $\mathscr{B}$; they have no access to the "bulk" state $|B\rangle$; the operators $M_i^B$ available to *B* face exactly the same restriction. The result is that the maximum information obtainable by *A* (or *B*) at any moment is the *N*-bit string written on its side of the holographic screen $\mathscr{B}$, which is not sufficient to even specify $|AB\rangle$, let alone compute $\mathcal{S}(|AB\rangle)$.[^2]

The intuitive core of the result can be stated simply. The boundary $\mathscr{B}$ is the medium through which all of *A*'s evidence flows. To gather evidence that the boundary enforces separability, *A* would need to step outside of it, to inspect the *A*-*B* relationship from a vantage point that is neither *A*'s nor *B*'s. But *A* is, by definition, on one side. In short, it can read the messages that arrive on the boundary, but it cannot examine the boundary itself.

To make the implications of this result clear, it is useful to put it in 1st person. If *I* cannot measure the entanglement entropy across *my* boundary, then I cannot demonstrate that I am separable from my environment. I have, in this case, no evidence that I am distinguishable from my environment in any way.

It is worth noting that the impossibility is symmetric. Just as there is no evidence for a self separate from the environment, there is equally no evidence for being fully "one with" the environment. The entanglement entropy is screened off in both directions: observations cannot confirm separation, nor can they confirm unity. There is no *self*-evidence, and no *no-self*-evidence either. The question of the boundary's status is not answered in the negative; it is unanswerable. The notion of self-boundaries, and therefore 'selfhood', is groundless.[^3]

We propose that a central aspect of the Buddhist notion of awakening can be formalised in terms of an agent whose embodiment encodes the understanding that its separation from the environment is an unknowable concept. Again in 1st person, I realise I cannot know whether I have a boundary. We formally articulate this realisation in what follows.

[^2]: Entanglement entropies are routinely measured in laboratories. All such measurements, however, must assume *a priori* that at least two systems – conventionally, the observers making the measurements – are mutually separable; see (Fields and Glazebrook, 2025, Ch. 7) for a detailed discussion.

[^3]: Furthermore, because *A*'s measurement operators act only on $\mathscr{B}$, *A* is also incapable of measuring the entanglement entropy across any *internal* boundary. Hence *A* can have no evidence that it itself has "parts" in any meaningful sense.

### 3.2 Self-evidencing without self-evidence

The concept of *self-evidencing* (Hohwy, 2016) captures the constitutive relationship between an agent and its model evidence: any persisting system minimises surprisal and thereby maximises evidence for its own generative model, i.e., self-evidences. Self-evidencing is not an optional activity; it is what it means to persist as a bounded system. Our claim is that one specific dimension of self-evidencing is provably impossible: evidencing the boundary itself. The agent can gather evidence for causal regularities observed through $\mathscr{B}$ (patterns, predictions, structural models), but it cannot gather evidence for the proposition that $\mathscr{B}$ constitutes a real separation between self and world. The boundary is the medium through which all evidence flows, but it is not itself evidenceable.

What does it mean, therefore, to be a self-evidencing agent that knows the separate self is not evidenceable? To make this precise, we must first clarify what the belief in separation concretely amounts to within the quantum-information-theoretic framework.

#### The separation belief as a sectorisation of the boundary

Recall from Section 2.1 that an agent is defined as a system *A* that deploys one or more quantum reference frames (QRFs). A QRF is a subset of measurement operators $M_i^A$ that are selectively sensitive to some degrees of freedom encoded on $\mathscr{B}$, together with a combinatorial logic that assigns a semantics to the outcomes measured by the operators. Deploying multiple QRFs induces decoherent sectors on $\mathscr{B}$, partitioning the *N* boundary qubits into functionally distinct groups.

We propose that the separation belief can be understood as a specific mode of sectorisation, one in which the agent's QRFs partition the boundary into sectors attributed to two distinct causal origins, self and environment. Let $\mathcal{Q}$ denote a particular QRF deployment that induces a sectorisation:

$$\mathcal{Q} : \mathscr{B} \longrightarrow \mathscr{B}_{\text{self}} \cup \mathscr{B}_{\text{env}} \tag{7}$$

where $\mathscr{B}_{\text{self}}$ groups the sectors whose observed values are attributed to causes that depend on the agent's own internal dynamics, and $\mathscr{B}_{\text{env}}$ groups sectors attributed to causes independent of those dynamics. This casts the sense of self as a structural (embodied) assumption, enacted by the agent's choice of measurement frame that organises the boundary into causally distinct regions, not a propositional belief ("I am separate"). How this sectorisation comes to be established developmentally, the metacognitive architecture it presupposes and the adaptive pressures that reinforce it, is discussed in Section 4.1.

#### Pragmatic utility without ontological evidence

How can a separation belief (dual partitioning of $\mathscr{B}$) be pragmatically useful even in the absence of evidence for it? In short, a factorised model can result in better predictions, but that improvement does not necessarily entail evidence for the existence of that factorisation independent of the agent's model. Said differently, given a particular QRF deployment $\mathcal{Q}$ (and its induced sectorisation), the agent can construct a factored generative model $M_{\mathcal{Q}}$ that exploits the partition with separate predictive dynamics for observations on $\mathscr{B}_{\text{self}}$ (those expected to covary with action and internal state changes) and observations on $\mathscr{B}_{\text{env}}$ (those expected to vary independently). Such a factored model can outperform an unfactored alternative at, e.g., predicting the consequences of the agent's own actions, and the resulting prediction-error reduction manifests in the standard sense, i.e., the agent obtains lower VFE on action-contingent observations.

However, the evidence that accumulates does so *conditional on* $\mathcal{Q}$, not *for* $\mathcal{Q}$ itself. The model evidence for a generative model *M* that assumes sectorisation $\mathcal{Q}$ is conditional on that choice:

$$P(\bar{o} \mid M_{\mathcal{Q}}) = P(\bar{o} \mid \mathcal{Q}, M) \tag{8}$$

where $\bar{o}$ is observations with semantics assigned by $\mathcal{Q}$. Different sectorisations yield different predictive accuracy, which is what *may* make the separation belief pragmatically useful. But the data on the boundary, *o*, is equally compatible with any alternative QRF deployment $\mathcal{Q}'$ that induces a different partitioning of $\mathscr{B}$—this is what Corollary 3.1 of Fields and Glazebrook (2023) entails. As noted in Section 2.1, the total Hamiltonian $H_U$ is equally consistent with any factorisation of the Hilbert space (Zanardi, 2002), and nothing about the physics privileges any one placement of sectors over any other. Let $\mathcal{Q}_1, \mathcal{Q}_2, \ldots$ denote the space of all possible QRF-induced sectorisations of $\mathscr{B}$. Then no outcome *o* (i.e., bit stream on the boundary) can differentially support any sectorisation over any other as a feature of the underlying physics:

$$P(o \mid \mathcal{Q}_i) = P(o \mid \mathcal{Q}_j) \quad \forall \mathcal{Q}_i, \mathcal{Q}_j, \quad \forall o \tag{9}$$

Equations (8) and (9) are fully compatible; a sectorisation can improve the agent's predictions without thereby providing evidence that the sectorisation reflects a real division in nature.[^4] The choice of sectorisation is screened off from all possible outcomes by the structure of the boundary itself, even as some choices yield better models than others. It is in this sense that we claim there is no self-evidence.

An analogy may clarify. A coordinate system in general relativity is necessary for calculation, and some coordinate choices make the physics more tractable than others, but no observation can tell the physicist which coordinates are "real" because the physics is diffeomorphism-invariant. The QRF-induced sectorisation plays an analogous role. It is a structure-enabling assumption that may be pragmatically indispensable but is ontologically unconstrained. The agent can accumulate evidence for the accuracy of its model *given* the sectorisation, just as a physicist can verify predictions *given* a coordinate chart; neither can obtain evidence that the chosen frame reflects a real division in the underlying structure.

#### Ontological commitment as a structural prior

Having established that the separation belief amounts to a QRF-induced sectorisation, and that the data on the boundary cannot adjudicate between sectorisations, we can now ask what it means, formally, for an agent to reify the separation as an ontological fact.

It is not sufficient to equate reification with a fixed QRF, since in ordinary, non-contemplative cognition the agent's QRF changes constantly. Every shift of attention, every saccade, every reorientation of precision weighting constitutes a different deployment of measurement operators on $\mathscr{B}$. However, we propose that what is static, under typical conditions, is a *structural prior* on the space of admissible QRF deployments, i.e., the requirement that every deployment respect a self/environment partition.

Let $\mathcal{Q}$ denote the full space of QRF deployments available to the agent, and let $\sigma$ be understood as a *structural prior over* $\mathcal{Q}$, a constraint that restricts admissible deployments to those consistent with a fixed self/environment partition:

$$\sigma : \mathcal{Q} \longrightarrow \mathcal{Q}_\sigma \subset \mathcal{Q} \tag{10}$$

where $\mathcal{Q}_\sigma$ is the subspace of QRF deployments that preserve the sectorisation $\mathscr{B}_{\text{self}} \cup \mathscr{B}_{\text{env}}$. Since QRF deployments are themselves policies, $\sigma$ is a prior over a policy space, and can therefore be understood as a *habit* in the sense developed in the active inference literature (Friston et al., 2016). The agent that reifies separation infers states and selects actions within $\mathcal{Q}_\sigma$, but does not represent $\sigma$ itself as a variable over which inference is performed. Said differently, $\sigma$ is a structural feature of the inference process, part of the model's architecture rather than part of its state space.

This is the formal counterpart of *transparency* in Metzinger's sense (Metzinger, 2003). The agent looks through $\sigma$ without seeing it because the model lacks the representational resources to bring it into view. The self/environment partition is not experienced as a belief that could be questioned (i.e. "opacified"); it is the unexamined scaffolding within which all beliefs are formed. Therefore, we equate taking separation to be an ontological fact, computationally, to having the dual sectorisation constraint as a rigid transparent prior rather than a revisable hypothesis.

We can now be more precise in the formalisation of awakening we expressed above. We put forward that "knowing that the self-world boundary cannot be known" can be formalised in terms of the opacification of $\sigma$ from a structural constraint on QRF space to an explicit variable within the generative model whose evidential support can be evaluated, and ultimately found wanting. The path that leads to this opacification and release of $\sigma$ is formalised in Section 4.

[^4]: Operationally, the language of the model *M*, which is determined by (or is) the selection of QRFs and hence sectors $\mathcal{Q}$, picks out the objects in the world that the agent is capable of recognizing. Equation (9) therefore says: the *data* that the agent gets on the boundary is independent of the language of the model, and hence independent of how the agent cuts the observed world up into objects. In the example of vision, the boundary corresponds to the photoreceptor layer (whereas the retina, which already does information processing, is part of the model).

### 3.3 Generalisation to all boundaries

The impossibility of self-evidence applies not only to the agent–environment boundary but to *any* boundary that the agent might posit. This generalisation is a formal consequence of the quantum-information-theoretic framework. Fields and Glazebrook (2023) establish that no finite system *A* can determine that any decomposition of its environment $B = B_1 B_2$ isolates all causal consequences of its actions in a single component $B_1$ (Corollary 3.2). The proof follows the same logic as the unevidenceability of the self–world boundary, since verifying the separability of $B_1$ and $B_2$ requires measuring the entanglement entropy $S(|B_1 B_2\rangle)$ across that internal boundary, which Corollary 3.1 of Fields and Glazebrook (2023) forbids for any finite observer. In plain terms, an agent can never verify that the part of the world it is attending to is genuinely independent of everything else.

This means that every act of perceptual segmentation, e.g., every identification of an "object" as distinct from its surroundings, every recognition of another agent as a bounded entity, rests on an assumption of separability that cannot be verified. The boundary between "this" and "not-this" is always a pragmatic designation, imposed by the observer's choice of quantum reference frame, not discovered as a feature of observer-independent reality (Fields and Glazebrook, 2023). Recall from Equation (9) that switching QRFs does not change the world, just what the world looks like.

Full emptiness realisation therefore extends to all such boundaries. The agent recognises that not only the self, but all objects, all agents, all phenomena are designations that are pragmatically useful but ontologically empty. We relate this to the Buddhist teaching that all *dharmas* (phenomena) are empty, not only the self.

In what follows, we develop the formal consequences of investigating the prior enforcing the self–environment boundary specifically, as this is the case of greatest contemplative and phenomenological significance. The reader should bear in mind that the argument generalises, every claim about $\sigma$ and its dissolution applies to any prior that enforces a fixed factorisation.

## 4. From separation to emptiness

We now model the contemplative path to emptiness realisation as a process of Bayesian model reduction (BMR), the mechanism by which a generative model prunes state factors that lack evidential support, which is in turn enabled by a preceding process of opacification. We begin by offering an account of why the separation prior emerges in the first place, which then motivates a proposed formalisation of the contemplative process that leads to its dissolution.

### 4.1 Why the separation prior emerges

It seems that under typical developmental conditions, humans construct generative models that include a structural prior $\sigma$ constraining the sectorisation of $\mathscr{B}$. But why does $\sigma$ arise?

We propose that $\sigma$ is a natural structural move when a sense of agency comes online. To see why, note that the sectorisation of $\mathscr{B}$ into $\mathscr{B}_{\text{self}}$ and $\mathscr{B}_{\text{env}}$ has a prerequisite: the agent must possess beliefs about its own internal dynamics in order to attribute a subset of boundary observations to self-generated causes. As shown by Friston et al. (2023) and Sandved-Smith and Da Costa (2024), this requires the architecture of a "metacognitive particle", a system that encodes beliefs about a subset of its own internal states. A purely cognitive particle, one that holds beliefs only about external states, has no representational basis on which to distinguish "observations that covary with my parameters" from "observations that do not." The developmental question is therefore what happens when this metacognitive capacity first emerges.

A metacognitive agent possesses a hierarchical model with *parametric depth*[^5]—the capacity to make higher-order inferences about the parameters of its own generative model (Sandved-Smith et al., 2021). This allows the agent to detect that some boundary observations covary with their own internal state changes, while others do not. This covariance pattern is the experiential signature of agency, or empowerment (Klyubin et al., 2005), namely that certain changes on $\mathscr{B}$ are systematically predictable from the agent's own dynamics. We suggest that the natural response is to partition the boundary accordingly, grouping action-contingent channels into $\mathscr{B}_{\text{self}}$ and action-independent channels into $\mathscr{B}_{\text{env}}$. This yields a factored generative model with separate predictive dynamics for each sector, and such a model naturally outperforms an unfactored alternative at predicting the consequences of the agent's own actions.

The dual sectorisation is, in this sense, the simplest architecture that exploits a sense of agency. The phenomenological character of the self-concept—the felt sense that "I" am the cause of certain experiences—reflects its attributional structure. Further developmental pressures then reinforce it. The self–world distinction enables efficient action planning (separating controllable from uncontrollable degrees of freedom), threat detection (localising danger relative to a bounded body), social coordination (modelling other agents as distinct from oneself), and the attribution of responsibility. Therefore, once established, model evidence accumulates conditioned on this structural separation belief and the sectorisation hardens into an architectural constraint.

We can be more precise about this hardening. In active inference, habits are formalised as prior beliefs over policies that accumulate evidence from the observation of one's own policy selections. Each time a policy is deployed, the prior over that policy is reinforced (Friston et al., 2016). When the prior becomes sufficiently precise, policy selection is dominated by the habit term and short-circuits the deliberative evaluation of expected free energy, producing the characteristic rigidity of habitual behaviour, i.e., its tendency to persist even when the outcomes it produces are no longer beneficial (Proietti et al., 2025). Because QRF deployments are policies, the separation prior $\sigma$ is subject to this same dynamic. Every dual QRF deployment, which is to say, every moment of ordinary perception, provides further evidence for deployment of a dual QRF, resulting in an increase in the precision of the prior. $\sigma$ is therefore a self-reinforcing prior, which gains precision simply by being used, decoupled from whether its use remains optimal in any given situation.

The result is a habitual prior over structural policies that may enable an accuracy gain at a complexity cost, since maintaining $\sigma$ adds an architectural constraint making the model more rigid. The separation prior persists so long as this trade-off is favourable, and as long as the agent cannot entertain a more flexible factorisation.

This developmental account resonates with the Buddhist concept of *avidyā* (Pali: *avijjā*), conventionally translated as "ignorance" but more precisely understood as a fundamental misapprehension, taking what is constructed to be given, mistaking a model for reality. In some traditions, avidyā is characterised as *dualistic fixation* (*gnyis 'dzin*, Tib.), the deeply habitual tendency to reify the subject–object structure of experience as reflecting an ontological division rather than a modelling convenience (Garfield, 2015). Similarly, in our framework, avidyā is not an absence of knowledge that could be remedied by acquiring new information. It is a structural feature of the generative model, the presence of $\sigma$ as a transparent architectural constraint (Equation (10)) that the agent cannot recognise as a construct precisely because it is the scaffolding within which all experience is organised. The agent does not *believe* in separation as a propositional attitude; they *perceive through* separation as an unexamined architecture of their inference.

[^5]: Parametric depth is very similar to the notion of *epistemic depth* discussed in (Laukkonen et al., 2025).

### 4.2 Contemplative inquiry as progressive opacification

Contemplative practice, particularly in the Buddhist traditions of *vipassanā* (insight meditation), can be understood as a sustained program of active inference directed at the evidential basis of one's own priors (Laukkonen and Slagter, 2021). We propose that the contemplative path can therefore be described as a process of *progressive opacification*: the systematic development of metacognitive access to previously transparent structural features of the generative model (Metzinger, 2003; Limanowski and Friston, 2018; Sandved-Smith et al., 2021; Laukkonen et al., 2025). In terms of the QRF formalism developed in Section 3.2, each shift of attention constitutes a different deployment of the agent's QRFs, a different selection of measurement operators $M_i^A$ and a different pattern of sensitivity to degrees of freedom on $\mathscr{B}$. The contemplative practitioner, by attending with increasing precision to the process of perception itself, may progressively develop a model of this variation. First, gross aspects of attentional deployment may become visible as the practitioner notices that perception is conditioned by where attention is directed, by affective tone, by conceptual framing. With sustained practice, subtler aspects of the inferential process then become accessible. What emerges is a representation of the agent's own low-level QRF dynamics, a vantage point from which the variation of the measurement frame across deployments becomes visible. This dynamic has been articulated in the contemporary contemplative literature as the cultivation of multiple *ways of looking*, where the practitioner deliberately adopts different perceptual frames in order to observe how each shapes what arises and develops with practice a fluency in moving between them (Burbea, 2014).

Recall that $\sigma$ constrains all QRF deployments to respect a fixed self/environment partition (Equation (10)). Under ordinary conditions, this constraint is transparent, the agent has little or no representation of its QRF dynamics, and therefore no basis on which to notice that the sectorisation is invariant across deployments, let alone question whether it must be. But as the practitioner builds a model of QRF variation, the previously invisible constraint becomes conspicuous. While the content of perception varies across attentional deployments, the self/environment partition remains curiously fixed. The very tracking of QRF variation reveals $\sigma$ as a structural feature of one's own inference, a constraint that was always operating but never seen. Once visible, $\sigma$ ceases to be part of the model architecture and enters the state space as a representable, examinable variable. The agent can now evaluate whether $\sigma$ earns its place, and the answer, as we will see in Section 4.3, is that it does not. The constraint that once structured all experience is revealed to be a choice.

This process corresponds closely to the Buddhist notion of developing insight into *pratītyasamutpāda* (dependent origination), the recognition that all phenomena arise in dependence upon conditions rather than from their own side or from a substantial self (Siderits and Katsura, 2013). What was previously experienced as "my experience of *x*" is progressively resolved into a causal chain of conditioning factors, none of which require or imply an independent experiencer. The path from avidyā to *prajñā* (wisdom) might be described as the trajectory from transparency to opacity, e.g., from not seeing the QRF that structures experience, to seeing it as a contingent deployment and recognising that the constraint $\sigma$ is itself a modelling assumption.[^6]

[^6]: Note that this discussion assumes both that the cognitive system is hierarchical and that its connection architecture enables metacognition. These, in turn, assume that the cognitive system has (self-)identifiable components. We saw earlier that this assumption also cannot be evidenced; the agent cannot demonstrate separability of its own internal state. Hence the hierarchical structure of cognition is itself a modelling assumption to be opacified.

### 4.3 Model reduction and the elimination of the separation factor

Bayesian model reduction provides the formal mechanism for the release of $\sigma$. BMR is a process of "fact-free learning" (Friston et al., 2017), the rapid simplification of a generative model by pruning parameters or state factors that fail to contribute to model evidence, without requiring new sensory data. The key insight is that BMR operates on the model's own structure, evaluating the evidential support for each component. BMR and fact-free learning have provided promising computational accounts of insight experiences (both ordinary "aha!" moments, Friston et al., 2017; Laukkonen et al., 2023, and deeper insights yielded through long-term meditation, Laukkonen and Slagter, 2021).

The contemplative trajectory described in Section 4.2 accomplishes a specific precondition for BMR: it converts $\sigma$ from a transparent constraint on QRF space, part of the model architecture and invisible to inference, into an explicit state factor within the generative model (the transition from transparency to opacity). Once $\sigma$ is a representable hypothesis, the standard BMR calculus applies. The VFE decomposes into complexity (the KL divergence between posterior and prior) and accuracy (expected log-likelihood). For BMR, we write this decomposition for a generative model *m* (Parr et al., 2022):

$$\mathcal{F} = \underbrace{D_{\text{KL}}[Q(s)\|P(s \mid m)]}_{\text{Complexity}} - \underbrace{\langle \ln P(o \mid s, m)\rangle_Q}_{\text{Accuracy}} \tag{11}$$

Any component of the model must "pay its way", meaning its contribution to accuracy must justify its complexity cost. If a component adds a dimension to the state space but no longer improves predictions, BMR will prune it.

The structural prior $\sigma$ is precisely such a component. On the complexity side, $\sigma$ constrains the model's QRF space, adding an architectural commitment that contributes to the KL divergence between posterior and prior. On the accuracy side, as discussed in Section 4.1, $\sigma$'s contribution is indirect. It scaffolds a factored inference architecture with separate predictive dynamics for $\mathscr{B}_{\text{self}}$ and $\mathscr{B}_{\text{env}}$, yielding genuine prediction-error reduction on action-contingent observations.

However, the contemplative trajectory described in Section 4.2 systematically undermines this indirect accuracy contribution. As the practitioner develops an increasingly precise model of their own QRF dynamics, they acquire the representational resources to adopt factorisations flexibly when the situation demands, without the need to depend on a fixed prior. The factored architecture that $\sigma$ once scaffolded is now sustained by a detailed metacognitive model, which can infer context-appropriate sectorisations on the fly. The accuracy gain afforded by $\sigma$ therefore approaches zero because the basis for those predictions has shifted from a fixed architectural constraint to a flexible, context-dependent inference.

But the complexity cost remains. The structural prior $\sigma$ continues to constrain QRF space, contributing to the KL divergence term regardless of whether it carries information. BMR now compares the current model *m* (which includes $\sigma$) against a reduced model $\tilde{m}$ (which does not). The change in free energy is:

$$\Delta\mathcal{F} = \mathcal{F}_{\tilde{m}} - \mathcal{F}_m = \Delta\text{Complexity} - \Delta\text{Accuracy} \tag{12}$$

This is negative, because $\Delta\text{Complexity} < 0$ (removing $\sigma$ reduces model complexity)[^7] while $\Delta\text{Accuracy} \approx 0$ (the flexible metacognitive model already provides the factored predictions that $\sigma$ once scaffolded). The reduced model $\tilde{m}$ has lower free energy, and therefore higher model evidence, so BMR prunes $\sigma$. The agent's choice of QRF becomes unconstrained and can be selected freely as a result of free energy minimisation.

[^7]: Note that the complexity incurred by the metacognitive model of the QRF dynamics is not implicated in Equation (12), which is specifically a comparison of the model with and without $\sigma$, not a comparison between a model with $\sigma$ versus a metacognitive model of low-level QRF dynamics. In other words, the pruning occurs when the metacognitive model is already in place, having paid its way separately in terms of accuracy and complexity contributions.

## 5. The post-dual agent

A natural concern might arise. If any boundary is just a modelling choice, not a discoverable feature of reality, does this lead to irrealism or solipsism? Does emptiness realisation leave the agent with nothing to hold on to? The answer operates at two levels. First, what is pruned is the prior $\sigma$ that enforced one particular designation, not the capacity for boundary designation altogether. The agent loses a constraint, not a capability. But this only pushes the question back: if boundary designations remain useful yet never reflect real divisions, what grounds the agent's modelling at all? In what follows we address both points, first characterising how inference changes when $\sigma$ is removed (Section 5.1), then grounding the post-dual agent's continued efficacy in a structural realist account of what remains (Section 5.2).

### 5.1 Unconstrained inference

Under dualistic fixation, the agent minimises VFE over the state space of its generative model, but the *form* of that model — specifically, the requirement that $\mathscr{B}$ be sectorised into $\mathscr{B}_{\text{self}}$ and $\mathscr{B}_{\text{env}}$ — is fixed by $\sigma$ and not itself subject to inference. The agent may select among QRFs that respect this partition, but cannot question the partition itself.[^8]

$$\min_{\mathcal{Q} \in \mathcal{Q}_\sigma} \mathcal{F}(M_{\mathcal{Q}}) \tag{13}$$

After $\sigma$ is pruned, the full QRF space $\mathcal{Q}$ is available. The sectorisation is now optimised over the full space of possible deployments, unconstrained by $\sigma$:

$$\min_{\mathcal{Q} \in \mathcal{Q}} \mathcal{F}(M_{\mathcal{Q}}) \tag{14}$$

The difference is that in Equation (13), the partition is a fixed structural assumption whereas in Equation (14) it becomes a *policy variable*, maintained, revised, or dissolved as VFE minimisation demands. Different tasks or contexts may call for different sectorisations. For example, the agent might partition the boundary one way when planning a reach (attributing proprioceptive channels to "self") and another way when processing speech (attributing auditory channels to "environment"). No deployment is ontologically privileged as all are provisional and task-relative.

The joint optimisation in Equation (14) is strictly more flexible than the constrained optimisation in Equation (13). Any solution available to the constrained agent is also available to the unconstrained agent, but the converse does not hold. The post-dual agent can access QRF deployments, and therefore predictive strategies, that were structurally excluded under dualistic fixation. We note that the larger solution space may also introduce additional local minima, so the practical benefit depends on the agent's capacity to navigate the expanded landscape. The contemplative training described in Section 4.2 may itself develop this capacity, by building the metacognitive model of QRF dynamics that enables informed exploration of $\mathcal{Q}$. We return to this point in Section 6.2, where we suggest that Buddhist compassion teachings can be understood as practical strategies for orienting the agent within this expanded space.

[^8]: $\mathcal{F}(M_{\mathcal{Q}})$ denotes the variational free energy of the generative model indexed by QRF deployment $\mathcal{Q}$, optimised over the approximate posterior as in Equation (11). Since different $\mathcal{Q}$ induce different factorisations of the hidden state space, the choice of QRF and the optimisation of the posterior are not independent.

### 5.2 Structure without ontology

The absence of a fixed partition does not imply an absence of structure. We appeal here to structural realism, the position that there is mind-independent structure—causal regularities that make some models better than others—but that this structure does not come pre-carved into things (Hohwy, 2025). Without such regularities external to the perceiver, no model could accumulate evidence, and hence no perceiver could exist. The dynamics of the universe, encoded by the Hamiltonian $H_U$ in Equation (1), exemplifies such a structure: real and observer-independent, but decomposition-independent, i.e., it does not specify any particular partition of the world into objects or agents. The agent can therefore know the relational, causal structure of its world-as-experienced, "an image of the law of this thing which is happening" (von Helmholtz, 1977, p. 122), but not the intrinsic nature of things-in-themselves. In the language of Section 2.1, *A* can know the relational, causal structure of observed state changes on $\mathscr{B}$, but cannot know $|B\rangle$.

What is pruned in emptiness realisation is therefore not the agent's capacity to model the world, but the *ontological commitment* that any particular sectorisation of the boundary marks a genuine division. This formalises what the contemplative literature calls *dereification*—the disengagement from the automatic tendency to treat mental constructions, including the boundary between self and world, as ontologically real (Dahl et al., 2015; Lutz et al., 2015). The generative model retains its full predictive structure, tracking, e.g., causal regularities, temporal patterns and the pragmatic distinction between states whose dynamics depend on the agent's actions and states that are more distal. Boundary designations are recognised as tools for navigating structure, not as reflections of ontological divisions in nature. The sectorisation $\mathscr{B}_{\text{self}} \cup \mathscr{B}_{\text{env}}$ remains available as one possible QRF deployment among many, and it remains pragmatically useful for action planning, social coordination, and the other adaptive functions. What changes is its status: it is deployed when helpful and set aside when not, rather than being architecturally enforced.

Self-evidencing, the process by which a persisting system maximises evidence for its generative model, is therefore not only unimpaired but *improved*. As argued in Section 4.3, the contemplative trajectory renders $\sigma$'s indirect accuracy contribution dispensable, so that it contributes only complexity; its removal therefore reduces VFE. The transition from constrained to unconstrained optimisation over QRF space strictly enlarges the set of admissible predictive strategies, and the generative model becomes both more parsimonious and more flexible. This characterisation makes precise the relationship between emptiness and the traditional Buddhist emphasis on *skilful means* (*upāya*). The awakened agent does not lack a self-model; rather, the self-model, along with all other boundary designations, is deployed skilfully, selected on the basis of predictive utility rather than ontological commitment, and held subject to revision as conditions change.

The unconstrained optimisation also implies a direction. As shown by Fields et al. (2022), VFE minimisation asymptotically drives *A* and *B* toward alignment of their measurement frameworks. Once QRF choice is free, the FEP tells the agent which QRF to select: the one that matches how the environment writes on the boundary. The direction of optimal inference, for the post-dual agent, is to see the world as the world sees it.

### 5.3 Impermanence and ongoing revision

The Buddhist tradition emphasises that insight into emptiness is intimately connected with insight into *impermanence* (*anicca/anitya*): the recognition that all conditioned phenomena are transient. In our framework, this corresponds to the recognition that all boundary designations, all coarse-grainings of the holographic screen into "self" and "world" or into distinct objects and agents, are provisional and subject to revision.

After emptiness realisation, the agent's relationship to its own model changes. Boundary designations are no longer treated as fixed structural commitments but as *hypotheses* to be maintained, revised, or abandoned as predictive accuracy demands. All models are held lightly, because none are mistaken for reality.

We connect this to the phenomenological reports of a *zero-person perspective* documented in the literature on minimal phenomenal experience (MPE) (Metzinger, 2024; Sandved-Smith, 2025), a stable mode of experience in which the sense of being an experiencer, a subjective centre, is persistently absent as an enduring shift in the structure of perception. In our terms, the zero-person perspective is the phenomenology of a generative model from which $\sigma$ has been pruned. The agent continues to perceive, act, and plan, but without the abstract reference point of "separate self" that previously anchored the experiential field.

## 6. Discussion

### 6.1 Emptiness as contextuality

The model developed in this paper reveals a correspondence between the Buddhist understanding of emptiness and the quantum-information-theoretic concept of contextuality. We propose that these are articulations of the same structural feature of reality: the impossibility of assigning context-independent properties to a system whose structure is irreducibly context-dependent. What the Buddhist tradition calls the lack of *svabhāva* (intrinsic, context-independent self-nature) can be articulated, in the language of quantum information theory, as the context-dependence of any observed boundary.

Importantly, the contextuality is not a consequence of the model developed here; it is a feature of the boundary itself. As established in Section 3, different QRF deployments yield incompatible measurement bases on $\mathscr{B}$, i.e., no single frame captures the boundary across all possible measurements. The "properties" of the boundary depend on which measurement frame is deployed. This is the natural structure of the boundary prior to any modelling assumption. If present, the structural prior $\sigma$ suppresses this contextuality by requiring every QRF deployment to sort every channel into a binary partition (self-caused or environment-caused) and the agent operates as though a context-independent value assignment were possible, when in fact the boundary is contextual.

To say the boundary lacks context-independent properties is also to say that whatever properties it has are constituted by the contexts in which they appear. This latter positive formulation evokes a notion similar to *pratītyasamutpāda* (dependent origination, or interdependence) mentioned earlier, the idea that things exist only in dependence on conditions, conceptual schemes and the relations in which they stand. Contextuality says no QRF-independent value assignment is possible; interdependence says any value the agent attributes to the boundary is jointly constituted by the boundary and the QRF deployed to interrogate it. The structural realism of Section 5.2 already aligns with this view. It states that there is mind-independent structure but nothing can be said about it as it is in itself; what we can articulate however is that this structure is relational rather than residing in self-standing things—and even the relations are themselves defined by further relations, *ad infinitum*. The structure is therefore not a new ontological resting place but the further articulation of dependent origination at every layer (*śūnyatā-śūnyatā*, the emptiness of emptiness) (Westerhoff, 2020). For the realised agent, interdependence is recognised as the structural condition that enables inference.

This allows us to sharpen the formalisation of *avidyā* introduced in Section 4.1. There, we characterised avidyā as the transparent presence of $\sigma$—the agent perceiving through a fixed partition without recognising it as a construct. The contextuality framing reveals what is being suppressed: avidyā is the enforcement of non-contextuality on a boundary whose structure is inherently context-dependent. The "ignorant" agent actively constrains its own inference to a subspace $\mathcal{Q}_\sigma$ that preserves a fixed partition, and mistakes this constraint for a feature of reality.

The habitual character of $\sigma$ developed in Section 4.1 also resonates with the Buddhist account of how avidyā is perpetuated. In the canonical formulation of dependent origination, avidyā gives rise to *saṃskāra* (Pali: *saṅkhāra*), often translated to "conditioned formations"—world shaping activities that both arise from ignorance and, in arising, reinforce the very ignorance that conditioned them (84000, 2018). Avidyā can therefore be understood as the ongoing product of a self-reinforcing loop, in which each saṃskāric formation consolidates the tendency to reify a self-world partition. Our formalism echos this perspective. Every dually sectorised QRF deployment is a saṃskāric formation in the sense that it is an action that both expresses $\sigma$ and, by the habit dynamics of Section 4.1, reinforces it—regardless of whether the sectorisation was contextually apt. Avidyā, in these terms, is the operation of an unexamined habit that continuously produces the appearance of a non-contextual boundary designations.

The transition from avidyā to *prajñā* (wisdom) is therefore not confined to the acquisition of a new belief (e.g., "boundaries are contextual"). What changes is the operative structure of the agent's QRF deployments, which are allowed to range over the full space $\mathcal{Q}$, selecting context-appropriate factorisations as VFE minimisation demands. The metacognitive model developed through contemplative practice (Section 4.2) provides a tacit fluency with this contextual structure—a knowing *how* rather than a knowing *that*, in the sense articulated by Varela (1999). Each context-sensitive QRF selection enacts the insight into emptiness. This provides a lens on why the Buddhist traditions characterise prajñā as culminating in embodied wisdom rather than intellectual understanding. Realisation is not a belief about contextuality. The awakened agent's mode of *being* is contextual, their QRF deployments are unconstrained. And therefore, awakening can be understood as the agent's embodied recognition of, and fluent operation within, the contextual—and therefore interdependent—structure that was always the nature of their boundary.

### 6.2 Compassion as unbounded free energy minimisation

The Buddhist tradition often highlights that emptiness realisation and compassion (*karuṇā*) arise together, not as separate pursuits but as two aspects of a single insight (84000, 2021; Dharmachakra Translation Committee, 2014; Doctor et al., 2022). Our framework offers a formal account of their coincidence, and the importance of both aspects.

Before emptiness realisation, the agent's free energy minimisation is structured by the separation prior $\sigma$. The fixed sectorisation of $\mathscr{B}$ into $\mathscr{B}_{\text{self}}$ and $\mathscr{B}_{\text{env}}$ determines the scope of what the agent treats as its own prediction error. Because the partition is architectural, not subject to inference or revision, the agent preferentially minimises VFE within the domain it identifies as "self." The suffering of others is, computationally, prediction error on $\mathscr{B}_{\text{env}}$, not treated with the same priority as prediction error on $\mathscr{B}_{\text{self}}$.

After $\sigma$ is pruned and the sectorisation becomes a policy variable (Section 5.1), this preferential scoping dissolves. The distinction between "my prediction error about me" and "my prediction error about you" is no longer an architectural given but a pragmatic, task-relative choice that can be redrawn or removed depending on context. Free energy minimisation extends naturally to all states the agent can influence, without the former restriction to a privileged "self" domain.

However, although the removal of $\sigma$ lifts a structural limitation to the agent's field of concern, it is only a removal of *constraint*. It opens the full space of QRF deployments without specifying which deployment is appropriate in any given situation. The FEP itself supplies the answer. As discussed in Section 5.2, VFE minimisation asymptotically drives the agent toward alignment of its measurement framework with the environment's, i.e., toward the QRF that matches how the environment writes on the boundary (Fields et al., 2022). In other words, QRF alignment is implied by optimal inference, now possible once the constraint is lifted.

We propose that Buddhist compassion teachings can be understood as practical methods for fulfilling what the FEP identifies as optimal. Emptiness realisation removes the structural impediment and then compassion practices orient the agent toward the QRF alignment that unconstrained VFE minimisation demands. The two are inseparable for the same reason that clearing a path and walking it are inseparable if you want to arrive somewhere: without emptiness realisation, the constraint blocks alignment; without compassion training, the agent has no compass for navigating the expanded QRF space toward its optimum. Embodied wisdom and compassion therefore goes beyond a new belief that "I am you" or "we are one", it is a mode of engagement in which the agent's inference is both unbounded in scope and actively oriented toward seeing the world as the world sees it.

### 6.3 Criticality as an empirical prediction

The reduction of VFE associated with emptiness realisation (the removal of the unevidenced separation prior) generates a concrete empirical prediction. Lower free energy has been associated with internal state dynamics closer to a critical dynamical regime, the threshold between ordered and chaotic dynamics (Beggs and Plenz, 2003; Shew and Plenz, 2013; Cocchi et al., 2017). Indeed, Friston et al. (2012) show that Bayes-optimal perception inherently produces self-organized instability (local Lyapunov exponents that fluctuate around zero), so that free energy minimisation itself drives the system toward criticality. Criticality is characterised by maximal dynamic range, optimal information storage and transmission, and scale-free, self-similar fluctuations (Beggs, 2012).

We predict that agents who have undergone stable emptiness realisation will exhibit neural dynamics closer to criticality than matched controls. This prediction is amenable to empirical investigation using standard neuroimaging techniques (EEG, fMRI), measuring signatures such as long-range temporal correlations, power-law scaling of neural avalanches and fractal dimensionality of brain dynamics. In fact, recent empirical work is converging on this prediction. Mago et al. (2025) show that experienced meditators in states of deep absorption (jhāna/dhyāna) exhibit a shift toward a metastable, near-critical regime, characterised by increased neural signal diversity, reduced chaoticity and enhanced perturbational sensitivity. Complementary whole-brain modelling by Vohryzek et al. (2025) demonstrates that jhāna states are associated with dynamics approaching criticality, using neurophenomenological methods that combine first-person phenomenology with computational models of brain dynamics. Earlier work is also broadly consistent (Irrmischer et al., 2018; van Lutterveld et al., 2017), though direct tests in populations reporting stable selflessness (as distinct from transient meditative states) have not yet been conducted.

### 6.4 Future computational work

The model presented here opens several directions for future computational work:

1. **Adaptive value of the separation prior.** Under what conditions does developing a belief in separation confer short-term adaptive benefits? Simulations of active inference agents with and without a separation factorisation could formalise the developmental trajectory that gives rise to the belief in a bounded self.
2. **Contemplative inquiry as model interrogation.** Formalising meditation practice as active inference directed at the agent's own generative model structure, demonstrating the conditions under which BMR of the separation prior occurs.
3. **Post-awakening dynamics.** Characterising the free energy landscape and dynamical regime of an agent whose separation prior has been pruned, including the predicted shift toward criticality and compassion.

## 7. Conclusion

This paper has developed a formal account of the Buddhist notion of awakening as the embodied recognition that no finite agent can obtain evidence for its own separability from its environment. Drawing on the quantum-information-theoretic formulation of the free energy principle (Fields et al., 2022; Fields and Glazebrook, 2023), we showed that the entanglement entropy across any agent's boundary is unmeasurable from the agent's side (Section 3). This renders the belief in a separate self, which we formalised as the separation prior $\sigma$, permanently unevidenceable.

We then modelled the contemplative path as a trajectory through generative model space (Section 4). Contemplative practice progressively opacifies the agent's own QRF dynamics, revealing the structural prior $\sigma$ as a contingent constraint on the space of admissible measurement frames. Bayesian model reduction then prunes $\sigma$ from the model entirely. The post-dual agent's inference is characterised by unconstrained VFE minimisation over the full QRF space (Equations (13) and (14)), with the sectorisation itself becoming a policy variable rather than an architectural commitment.

Five consequences follow. First, the agent's self-evidencing is unimpaired and indeed improved: the pruned model is more parsimonious without loss of accuracy, yielding lower variational free energy (Section 4). What remains is a structural realism in which boundary designations may remain as pragmatic tools but are no longer reified as ontological commitments (Hohwy, 2025). Second, the formal result generalises: the same impossibility that renders the self–world boundary unevidenceable applies to any boundary the agent might posit, grounding the Buddhist teaching that all phenomena are empty (Section 3.3). Third, the model identifies emptiness with the contextuality of the boundary (Section 6.1): $\sigma$ suppresses the inherent context-dependence of QRF deployments, and its removal reveals the contextual structure that was always there. Awakening is not the acquisition of a new belief but the agent's fluent operation within this contextual structure. Fourth, the reduction in free energy predicts a shift toward critical dynamics (Friston et al., 2012), a prediction that converges with recent empirical findings in experienced meditators (Mago et al., 2025; Vohryzek et al., 2025). Fifth, the removal of $\sigma$ clears the way for compassion understood as selfless VFE minimisation and the acceleration of the asymptotic QRF alignment with the environment (Section 5.1), which implies that the post-dual agent's optimal choice of QRF is to become fully entangled with the world by seeing the world as the world sees it.

Finally, we note that the model presented here is itself a pragmatic designation. It does not claim to capture the "true nature" of awakening in some final or definitive sense, such a claim would contradict the very insight it seeks to formalise. This paper is a generative model of emptiness realisation, offered in the spirit of structural realism as a useful representation of relational structure that makes no metaphysical claims about the intrinsic nature of what it represents. It is, to use the traditional metaphor, a finger pointing at the moon.

## Acknowledgements

The initial conversations that later became this paper took place at the "Holistic Intelligence" unconference hosted by Softmax Inc. in San Francisco in December 2024. We thank the organisers and participants for the discussions that initiated this work.

## References

84000 (2018). The Rice Seedling (śālistamba, sa lu'i ljang pa, Toh 210). 84000: Translating the Words of the Buddha. Translated by the Dharmasāgara Translation Group.

84000 (2021). "The Ten Bhūmis" Chapter from the Mahāvaipulya Sūtra "A Multitude of Buddhas" (Buddhāvataṃsakanāmamahāvaipulyasūtrāt daśabhūmikaḥ paṭalaḥ, sa bcu, Toh 44-31). 84000: Translating the Words of the Buddha. Translated by Peter Alan Roberts.

Arkani-Hamed, N. and Trnka, J. (2014). The amplituhedron. *Journal of High Energy Physics*, 2014(10):30.

Beggs, J. M. (2012). The criticality hypothesis: How local cortical networks might optimize information processing. *Philosophical Transactions of the Royal Society A*, 366:329–343.

Beggs, J. M. and Plenz, D. (2003). Neuronal avalanches in neocortical circuits. *Journal of Neuroscience*, 23(35):11167–11177.

Burbea, R. (2014). *Seeing That Frees: Meditations on Emptiness and Dependent Arising*. Hermes Amāra Publications.

Cocchi, L., Gollo, L. L., Zalesky, A., and Breakspear, M. (2017). Criticality in the brain: A synthesis of neurobiology, models and cognition. *Progress in Neurobiology*, 158:132–152.

Dahl, C. J., Lutz, A., and Davidson, R. J. (2015). Reconstructing and deconstructing the self: Cognitive mechanisms in meditation practice. *Trends in Cognitive Sciences*, 19(9):515–523.

Dharmachakra Translation Committee (2014). *Ornament of the Great Vehicle Sutras*. Shambhala Publications, Boston, MA.

Doctor, T., Witkowski, O., Solomonova, E., Duane, B., and Levin, M. (2022). Biology, buddhism, and AI: Care as the driver of intelligence. *Entropy*, 24(5):710.

Fields, C., Friston, K., Glazebrook, J. F., and Levin, M. (2022). A free energy principle for generic quantum systems. *Progress in Biophysics and Molecular Biology*, 173:36–59.

Fields, C. and Glazebrook, J. F. (2023). Separability, contextuality, and the quantum frame problem. *International Journal of Theoretical Physics*, 62:159.

Fields, C. and Glazebrook, J. F. (2025). *Distributed Information and Computation in Generic Quantum Systems*. Springer, Cham.

Fields, C. and Levin, M. (2025). Thoughts and thinkers: On the complementarity between objects and processes. *Physics of Life Reviews*, 52:256–273.

Friston, K. (2010). The free-energy principle: A unified brain theory? *Nature Reviews Neuroscience*, 11(2):127–138.

Friston, K. (2019). A free energy principle for a particular physics. *arXiv preprint arXiv:1906.10184*.

Friston, K., Breakspear, M., and Deco, G. (2012). Perception and self-organized instability. *Frontiers in Computational Neuroscience*, 6:44.

Friston, K., Da Costa, L., Sakthivadivel, D. A. R., Heins, C., Pavliotis, G. A., Ramstead, M., and Parr, T. (2023). Path integrals, particular kinds, and strange things. *Physics of Life Reviews*, 47:257–289.

Friston, K., FitzGerald, T., Rigoli, F., Schwartenbeck, P., and Pezzulo, G. (2016). Active inference and learning. *Neuroscience & Biobehavioral Reviews*, 68:862–879.

Friston, K. J., Lin, M., Frith, C. D., Pezzulo, G., Hobson, J. A., and Ondobaka, S. (2017). Active inference, curiosity and insight. *Neural Computation*, 29(10):2633–2683.

Garfield, J. L. (2015). *Engaging Buddhism: Why It Matters to Philosophy*. Oxford University Press.

Hohwy, J. (2016). The self-evidencing brain. *Noûs*, 50(2):259–285.

Hohwy, J. (2025). A metaphysics for predictive processing. *Synthese*, 206:87.

Irrmischer, M., Houtman, S. J., Mansvelder, H. D., Tremmel, M., Ott, U., and Linkenkaer-Hansen, K. (2018). Controlling the temporal structure of brain oscillations by focused attention meditation. *Human Brain Mapping*, 39(4):1825–1838.

Klyubin, A., Polani, D., and Nehaniv, C. (2005). Empowerment: A Universal Agent-Centric Measure of Control. In *2005 IEEE Congress on Evolutionary Computation*, volume 1, pages 128–135, Edinburgh, Scotland, UK. IEEE.

Laukkonen, R. E., Friston, K., and Chandaria, S. (2025). A beautiful loop: An active inference theory of consciousness. *Neuroscience and Biobehavioral Reviews*, 176:106296.

Laukkonen, R. E. and Slagter, H. A. (2021). From many to (n)one: Meditation and the plasticity of the predictive mind. *Neuroscience and Biobehavioral Reviews*, 128:1–14.

Laukkonen, R. E., Webb, M., Salvi, C., Tangen, J. M., Slagter, H. A., and Schooler, J. W. (2023). Insight and the selection of ideas. *Neuroscience and Biobehavioral Reviews*, 153:105363.

Limanowski, J. and Friston, K. (2018). "Seeing the Dark": Grounding phenomenal transparency and opacity in precision estimation for active inference. *Frontiers in Psychology*, 9:643.

Lutz, A., Jha, A. P., Dunne, J. D., and Saron, C. D. (2015). Investigating the phenomenological matrix of mindfulness-related practices from a neurocognitive perspective. *American Psychologist*, 70(7):632–658.

Mago, J., Brahinsky, J., Miller, M., Maschke, C., Slagter, H. A., Catherine, S., Laukkonen, R. E., Cahn, B. R., Sacchet, M. D., Dixey, W., Dixey, R., Rej, S., and Lifshitz, M. (2025). Meditative absorption shifts brain dynamics toward criticality. *arXiv preprint*. arXiv:2511.20990.

Maldacena, J. and Susskind, L. (2013). Cool horizons for entangled black holes. *Fortschritte der Physik*, 61(9):781–811.

Metzinger, T. (2003). *Being No One: The Self-Model Theory of Subjectivity*. MIT Press.

Metzinger, T. (2024). *The Elephant and the Blind: The Experience of Pure Consciousness: Philosophy, Science, and 500+ Labs*. MIT Press.

Page, D. N. and Wootters, W. K. (1983). Evolution without evolution: Dynamics described by stationary observables. *Physical Review D*, 27(12):2885–2892.

Parr, T., Pezzulo, G., and Friston, K. J. (2022). *Active Inference: The Free Energy Principle in Mind, Brain, and Behavior*. MIT Press.

Proietti, R., Parr, T., Tessari, A., Friston, K., and Pezzulo, G. (2025). Active inference and cognitive control: Balancing deliberation and habits through precision optimization. *Physics of Life Reviews*.

Sandved-Smith, L. (2025). A computational model of minimal phenomenal experience (MPE). *Preprints*. Preprint.

Sandved-Smith, L. and Da Costa, L. (2024). Metacognitive particles, mental action, and the sense of agency. *arXiv preprint arXiv:2405.12941*.

Sandved-Smith, L., Hesp, C., Mattout, J., Friston, K. J., Lutz, A., and Ramstead, M. J. D. (2021). Towards a computational phenomenology of mental action: Modelling meta-awareness and attentional control with deep parametric active inference. *Neuroscience of Consciousness*, 2021(2):niab018.

Shew, W. L. and Plenz, D. (2013). The functional benefits of criticality in the cortex. *The Neuroscientist*, 19(1):88–100.

Siderits, M. and Katsura, S. (2013). *Nāgārjuna's Middle Way: Mūlamadhyamakakārikā*. Wisdom Publications, Boston, MA.

van Lutterveld, R., Houlihan, S. D., Pal, P., Sacchet, M. D., McFarlane-Blake, C., Patel, P. R., Sullivan, J. S., Ossadtchi, A., Druker, S., and Brewer, J. A. (2017). Source-space EEG neurofeedback links subjective experience with brain activity during effortless awareness meditation. *NeuroImage*, 151:117–127.

Van Raamsdonk, M. (2010). Building up spacetime with quantum entanglement. *General Relativity and Gravitation*, 42(10):2323–2329.

Varela, F. J. (1999). *Ethical Know-How: Action, Wisdom, and Cognition*. Stanford University Press.

Vohryzek, J., Lopez-Sola, E., Yang, W. F. Z., Sanz Perl, Y., Sparby, T., Laukkonen, R. E., and Deco, G. (2025). Whole-brain models of minimal phenomenal experience: Approaching criticality through Jhāna meditation. *bioRxiv*.

von Helmholtz, H. (1878/1977). The facts in perception. In Cohen, R. S. and Elkana, Y., editors, *Epistemological Writings*, pages 115–185. Springer Netherlands.

Westerhoff, J. (2020). *The Non-Existence of the Real World*. Oxford University Press.

Wheeler, J. A. (1990). Information, physics, quantum: The search for links. pages 3–28.

Zanardi, P. (2002). Quantum entanglement in fermionic lattices. *Physical Review A*, 65:042101.

---

## Figure Descriptions

This paper contains **no figures**. It is a theoretical/conceptual contribution whose formal content is carried entirely by numbered equations (Eq. 1–14). No images, diagrams, plots, or tables appear in the source PDF. The `figures/` directory is therefore intentionally empty.

Key equations (for reference):
- **Eq. 1** — Decomposition of the total Hamiltonian: $H_U = H_A + H_B + H_{AB}$
- **Eq. 2** — Separability via zero entanglement entropy
- **Eq. 3** — Interaction Hamiltonian as a holographic screen of yes/no operators
- **Eq. 4** — "Physical interaction = Thermodynamics × Yes/No questions" (it-from-bit)
- **Eq. 5–6** — Prediction error and the VFE = Noise + Insufficient learning decomposition
- **Eq. 7** — QRF-induced sectorisation of the boundary into $\mathscr{B}_{\text{self}} \cup \mathscr{B}_{\text{env}}$
- **Eq. 8–9** — Model evidence conditional on sectorisation vs. data invariance across sectorisations
- **Eq. 10** — The separation prior $\sigma$ as a structural constraint on QRF space
- **Eq. 11** — VFE complexity/accuracy decomposition for Bayesian model reduction
- **Eq. 12** — Free-energy change from pruning $\sigma$
- **Eq. 13–14** — Constrained (dualistic) vs. unconstrained (post-dual) VFE minimisation over QRF space

---

## Relevance to Active Inference / IFS Research

This paper is directly load-bearing for the IFS / active-inference project and is, in fact, co-authored by figures central to the surrounding literature (Sandved-Smith, Laukkonen, Hohwy; with Fields on the quantum-information side).

1. **Boundaries as priors, not ontology** — The core move (separation modelled as a structural prior $\sigma$ over QRF deployments, later pruned via Bayesian model reduction) is a clean formal template for how *any* self/part boundary can be held as a revisable hypothesis rather than a fixed division. This maps onto IFS's treatment of "parts" as functional structures rather than substantial selves.

2. **Self-evidencing without self-evidence** — Extends Hohwy's self-evidencing into a provable limit: an agent can evidence regularities *through* a boundary but never the boundary's reality. Useful framing for distinguishing what an internal-family system can know about its sub-agents vs. what is architecturally assumed.

3. **Opacification → model reduction as the mechanism of insight** — The "transparency → opacity → BMR pruning" pipeline (Sections 4.2–4.3) is a concrete computational story for how contemplative inquiry (and, by analogy, IFS unburdening/Self-leadership) dissolves a reified structural prior. This is the same Friston/Laukkonen BMR machinery the project already engages.

4. **Metacognitive particles and parametric depth** — Builds on Sandved-Smith et al. (2021) and Sandved-Smith & Da Costa (2024), the deep-parametric active inference architecture, which is plausibly the formal substrate for modelling IFS parts/Self relations (self-modelling subsystems with beliefs about their own internal states).

5. **Compassion as unbounded VFE minimisation** — Section 6.2 gives a formal account of why dissolving the self/env partition extends free-energy minimisation beyond a privileged "self" domain. A potential bridge to IFS notions of Self-energy (compassion, connectedness) emerging when protective boundaries relax.

6. **Empirical hook: criticality** — The prediction that emptiness/Self-led states shift neural dynamics toward criticality (Mago et al. 2025; Vohryzek et al. 2025) offers a testable physiological correlate that could be repurposed for IFS-state research.
