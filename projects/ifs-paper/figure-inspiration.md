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
