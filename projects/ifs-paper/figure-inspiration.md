# Figure Design Inspiration
## Visual patterns from Chamberlin 2022, existing IFS figures, and reference papers

Date: 2026-03-26

---

## Most relevant precedents for the v2 simulation figures

### From Chamberlin 2022 (Coherence Therapy)

**ct_mechanism_comparison.png — Step-function vs gradual learning**
- Side-by-side: CBT (gradual slope over 100 trials) vs CT (sharp vertical drop at intervention)
- Identical axes and scale for direct comparison
- The step-function is the most visually compelling pattern in the whole set
- **For IFS:** The cascade in Condition 3 should have this "something shifts and everything follows" quality. Not a step-function exactly, but a visible phase transition.

**ct_schematic.png — Process flowchart comparing two modes**
- Parallel pathways: Modular Mode (pink) vs Integrated Mode (green)
- Color-coded properties flowing to outcome boxes with numerical results
- **For IFS:** Template for the mechanism inset in the iconic figure. Show capture regime (part dominates, channel 5 off) vs relational depth regime (Self-energy sufficient, channel 5 open, cascade).

**ct_before_after.png — Grouped bars, pre/post**
- Dramatic height differences show effect magnitude
- Most conditions near zero; one stands out
- **For IFS:** Could use for the free-choice probe — P(approach) across conditions after forced contact.

**discovery_mechanism.png — 2x2 small multiples**
- Behavioral avoidance, schema belief, annealing curve, schema accessibility — all sharing time axis
- Consistent y-axis scaling, color-coordinated
- **For IFS:** Template for decomposing the cascade into interpretable sub-figures. Each panel = one bundle element.

### From existing IFS simulation figures

**fig1_h1_belief_trajectories.png — 2x2 dashboard**
- Self-state, Threat Meaning, Avoidance Tendency, Capture Index across 5 conditions
- Consistent colors, shared x-axis
- **Note:** Good but dense. The v2 heatmap approach may be cleaner for showing cascade order.

**fig2_witnessing_vs_exposure.png — Direct comparison**
- Solid vs dashed lines distinguish mechanisms
- **Note:** The relational depth gap should be THIS clear in the v2 figure.

**formation_bundle_rigidity.png — Confidence bands**
- Mean trajectory + shaded ±1 SD
- **For IFS:** Use for ensemble results (N=50 runs) in the v2 simulation.

### From reference papers

**Ho 2021 figure1 — Active inference process diagram**
- Box-and-arrow: external state, sensory state, active state, internal state
- **For IFS:** Accessible template for explaining the model architecture to non-computational readers.

---

## Top 10 design patterns to adopt

1. **Step-function / phase transition** — make the cascade look like something SHIFTED, not gradual drift
2. **Identical axes across condition panels** — direct visual comparison without mental rescaling
3. **Color hierarchy** — consistent colors for conditions; muted for controls, saturated for key result
4. **Confidence bands over error bars** — mean + shaded region for stochastic runs
5. **Small multiples** — one panel per bundle element, shared time axis
6. **Annotated intervention points** — vertical dashed line at phase transitions, labeled
7. **Effect size prominence** — make the key result visually dominant; don't equalize conditions
8. **Mechanism inset** — small causal diagram accompanying the data figure
9. **First-passage markers** — dots/ticks showing when each element crosses threshold (from GPT 5.4 critique)
10. **Vertical divider between phases** — forced contact | free choice, clearly marked

---

## The iconic figure design (synthesized)

**Left inset:** Minimal mechanism diagram
- Causal chain: Self-state → Threat → Outcome → Policy
- Self-energy / capture as global gate above
- Three evidence streams below: external → threat, body → self+threat, witnessed self-state → self-state
- H1 vs H2 as tiny swap inset

**Right main panel:** Three stacked heatmaps
- Rows: Self-state, Threat, Expected Outcome, P(approach)
- Columns: time (with vertical divider at forced/free boundary)
- First-passage markers on each row
- Tiny strip above each heatmap: capture / witness precision over time

**Exposure panel:** Weak, diffuse. No diagonal.
**Informational panel:** Threat row changes. Self-state stays dark. Partial.
**Relational depth panel:** Change starts top-left, descends diagonally. Annotated once.

The diagonal IS the argument.

---

## Source files analyzed

Chamberlin 2022: `projects/reproductions/chamberlin_2022/figures/ct_*.png`, `discovery_*.png`
IFS current: `projects/ifs-paper/figures/fig*.png`, `formation_*.png`, `polarization_*.png`
Reference: `resources/papers/ho_2021_compassion/figures/`, `resources/papers/limanowski_blankenburg_2013_minimal_self/figures/`

---

## System Architecture Diagrams (for simulation model figure)

Searched all figures in `projects/reproductions/chamberlin_2022/figures/`, `resources/papers/ho_2021_compassion/figures/`, and `archive/figures/`. The following show generative model structure, hidden-factor-to-observation mappings, or prior flow through a model. Simulation output plots (trajectories, bar charts, heatmaps) are excluded.

### 1. Ho 2021 Figure 1 -- Bayesian Active Inference Architecture
**File:** `resources/papers/ho_2021_compassion/figures/figure1_bayesian_active_inference.jpg`

Four-node box-and-arrow diagram inside a rounded rectangle labeled "(sample space)." Nodes: External State (Node E, dashed border -- hidden/unobservable), Sensory State (Node S, solid border), Active State (Node A, solid border), Internal State (Node I, large circle). Thick block arrows show causal flow: E -> S, S -> I, I -> A, A -> E. Bidirectional "Prediction Errors" arrows connect S and A through the center. Asterisks on S and A mark them as Markov Blanket nodes separating Internal from External states.

**Relevance for IFS v2 figure:** The clearest precedent for showing a generative model's high-level architecture in this literature. Clean, minimal, black-and-white. The four-node layout with directed arrows is the template. For the IFS figure, we replace this with: Hidden Factors (self-state, threat, outcome) as internal nodes, Observation Channels (1-5) as sensory nodes, Policy/EFE as the active node, and Environment as the external node. The Markov Blanket concept maps to the observation channels mediating between hidden states and the world.

### 2. Ho 2021 Figure 2 -- Bayesian Dysfunction (Ego-Preserving Bias)
**File:** `resources/papers/ho_2021_compassion/figures/figure2_bayesian_dysfunction.jpg`

Same four-node layout as Figure 1, now populated with clinical content. P1's Node E lists "events causing sensations to conform to identity-grasping beliefs: flashbacks, interoceptive triggers, conceptual thoughts (VIKALPA)" and "events caused by actions driven by ego-preserving bias: objects to be avoided, objects to seek, objects to destroy." P1's Node S feeds into P1's Node I which contains "mental images, identity-grasping beliefs & other conceptual thoughts (VIKALPA)." Between S and A: "Excessive Free-Energy" with a fire icon and "Irreconcilable prediction errors due to ego-preserving bias" plus "Chronic Stress." Two face icons (P1, P2) flank the diagram showing interpersonal context.

**Relevance for IFS v2 figure:** Demonstrates how to annotate a system architecture diagram with domain-specific content while keeping the structural skeleton intact. The "excessive free energy" annotation between sensory and active states maps directly to the IFS concept of capture -- where prediction errors are resolved by maintaining burdened priors rather than updating them. The P1/P2 relational framing maps to the IFS witnessed-self-state channel that requires relational context.

### 3. Ho 2021 Figure 4 -- Attuning to Another Agent
**File:** `resources/papers/ho_2021_compassion/figures/figure4_attuning_to_others.jpg`

Horizontal flow diagram. Left: P2's Bayesian Engine (brain icon) feeds into P1's sample space through "Mirror-Neuron Systems (automatic mirroring)", "Ventral Attention Network (data-driven attention, conflict detection)", and "Frontoparietal Network (reasoning, working memory, thought releasing, spatial frame regulation)." These converge on P1's Node S and Node A within the sample space. Right side shows a vertical column of processing stages: "P1-P2 attunement" -> "P1's Reality-Checking" -> "P1's Conflict-Alarming" -> "P1's Relation-Modeling", each annotated with brain regions (Salience Network: PAG, Amygdala, Caudate, pvMCC & Insula; DMN Affect-Object Generating Network: Limbic, vACC, OFC, vmPFC; etc.). Arrow flows show belief-violation signals feeding up to a "Relational Frames / Hippocampus" component.

**Relevance for IFS v2 figure:** Most complex architecture in the set. Shows how an external agent's influence enters the generative model through specific neural network pathways. For IFS v2, the "P2's Bayesian Engine" maps to the therapeutic relationship generating observations on Channels 4 and 5. The staged processing (attunement -> reality-checking -> conflict-alarming -> relation-modeling) parallels the IFS cascade (self-state -> threat -> outcome -> policy), though the Ho figure is neural rather than computational. The key lesson: show the external relational input as a distinct entry point, not just another observation.

### 4. Chamberlin 2022 ct_schematic.png -- Coherence Therapy Process Schematic
**File:** `projects/reproductions/chamberlin_2022/figures/ct_schematic.png`

Two-column process diagram. Left: "MODULAR MODE" (pink background) -- Context-blind. Lists: "A: uniform (can't process cues)", "D: fearful prior", "D: learning blocked." Right: "INTEGRATED MODE" (green background) -- Context-aware. Lists: "A: identity (processes cues)", "D: accurate prior", "D: learning enabled." Between them: "Therapist Intervention" arrow pointing right. Below each mode: OUTCOME boxes. Modular: "P(avoid) = 0.96, Pathological avoidance." Integrated: "P(approach) = 0.97, Context-appropriate engagement." Footer: "Key Insight: Resolution via structural change, not belief updating (D change = 0)."

**Relevance for IFS v2 figure:** This is the closest structural precedent to what the IFS v2 figure needs. It shows two regimes of the SAME generative model (not two different models) with different A-matrix and D-prior configurations, and the intervention that switches between them. For IFS v2, the two regimes are "capture" (part precision dominates, channel 5 off) and "relational depth" (context precision grows, channel 5 opens, cascade occurs). The Chamberlin figure uses color-coding (pink = pathological, green = resolved) and parameter annotations (A, D values) that could be adapted. Key difference: the IFS model has a CONTINUOUS transition governed by self-energy, not a discrete switch.

### 5. Chamberlin 2022 discovery_mechanism.png -- 2x2 Mechanism Dashboard
**File:** `projects/reproductions/chamberlin_2022/figures/discovery_mechanism.png`

Four-panel small-multiples figure. Top-left: "Behavioral Change" (avoidance probability over trials, showing regime shifts). Top-right: "Context Sensitivity" (binary modular/integrated state over trials, showing step transitions). Bottom-left: "Simulated Annealing" (precision/temperature curve stepping down over trials). Bottom-right: "Schema Belief (D3)" (belief parameter trajectory). All panels share the trial axis. Color-coded conditions overlay on each panel.

**Relevance for IFS v2 figure:** Not a system architecture diagram per se, but shows how to decompose a model's internal dynamics into parallel panels that together tell the mechanistic story. The "simulated annealing" panel is directly analogous to the self-energy / capture index trajectory in the IFS model. For the IFS figure, a companion version of this layout could show: (1) capture index, (2) channel 5 precision, (3) self-state posterior, (4) cascade readout -- all sharing the time axis.

### Summary: What to borrow for the IFS v2 system architecture figure

**From Ho 2021 Figure 1:** The basic template -- nodes for hidden factors, directed arrows for causal structure, observation channels as the interface between internal and external. Black-and-white, academic, minimal.

**From Ho 2021 Figure 2:** How to annotate nodes with domain content (IFS part states, observation meanings) without cluttering the structural logic. The "excessive free energy" placement between nodes is a good template for showing where capture operates.

**From Ho 2021 Figure 4:** The relational input as a distinct entry pathway. Channel 5 (witnessed self-state) should enter the architecture from a visually distinct direction or with distinct notation, not blended with the other four channels.

**From Chamberlin ct_schematic.png:** Regime comparison (capture vs. relational depth) with parameter annotations. Color-coded backgrounds for the two operating modes. Outcome annotations showing behavioral consequences.

**Key design principle across all:** The architecture diagram should be readable by someone who has never seen an active inference model. Nodes should be labeled with IFS language (not just "s1, s2"), arrows should indicate what causes what, and the self-energy modulation should be visually prominent as the mechanism that governs which regime the system operates in.
