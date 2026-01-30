# PMC7250191 Task Spec (Concept Learning via Active Inference)

Source paper: "An Active Inference Approach to Modeling Structure Learning: Concept Learning as an Example Case" (2020).

Note: Some task-specific details appear only in figures/appendix or SPM demo code.
These are captured here for planning, but should be verified against the PDF/supplements.

## 1) Task Overview
- Agent is shown animals across trials and must infer the animal's identity from observable features.
- Each trial has **two time points**: (1) observe features, (2) report category.
- Features are drawn from **three modalities**: size, color, and a species-specific feature.

## 2) Hidden State Factors
1) **Animal identity** (up to 8 concepts)
   - Paper code uses: Parakeet, Parrot, Pigeon, Hawk, Clownfish, Manta ray, Minnow/Sardine*, Shark
   - (*Report labels use “Sardine”; the internal list uses “Minnow.”)
2) **Report choice** (action/state factor)
   - Report one of the 8 specific animals, or report a basic category (bird or fish).
   - Only one report at a time; the agent chooses its level of specificity.

## 3) Outcome Modalities
- **Feature outcomes** (observations at timepoint 1):
  - Size: {big, small}
  - Color: {gray, colorful}
  - Species-specific: {wings, gills}
- **Feedback outcomes** (timepoint 2):
  - Indicates whether the report was correct at a **basic** or **specific** level, or incorrect.
  - Supplementary code uses 4 feedback outcomes: {start, correct-specific, incorrect, correct-basic}.

Note: The supplementary code uses **3 outcome levels** for each feature modality (size/color/species),
with the first row effectively unused/“null”; labels only expose the 2 meaningful outcomes.

## 4) Generative Model Components
### A (Likelihood)
- Maps animal identity to feature combinations.
- Each animal corresponds to a unique point in the 3D feature space (size, color, species-specific).
- Concept learning uses **spare "slots"**: one or more A columns start **flat/uniform** (with small noise), allowing novel concepts to be learned.

### B (Transitions)
- For animal identity: **identity matrix** (animal does not change within trial).
- For report factor: controlled by policy (agent selects a report at timepoint 2).

### C (Preferences)
- Agent prefers **correct specific** reports most.
- Correct **basic** (bird/fish) reports are preferred but less than specific.
- Incorrect reports are least preferred (aversive).

### D (Priors)
- Prior over animal identity is typically flat or learned (see model reduction section).
- D learning accumulates concentration parameters reflecting exposure frequencies.

## 5) Learning Protocols
- **Unsupervised learning phase**:
  - Reporting is disabled (policies restricted), so no feedback is provided.
  - Learning is driven only by repeated feature exposure (A matrix learning).
- **Reporting evaluation phase**:
  - Learning disabled; reporting enabled.
  - Accuracy assessed with **20 trials per animal**.

## 6) State-Space Expansion (Concept Acquisition)
- One or more concept slots in A are initialized as uniform distributions.
- Agent is exposed to **2,000 trials** with all 8 animals sampled with equal probability.
- Model learns to assign the novel feature patterns to an unused slot and refine its A column.
- Performance improves faster when fewer new concepts must be learned.

## 7) Avoiding Redundant Concepts
- Agent starts with knowledge of 7 animals and one unused slot.
- Exposed to known animals first (e.g., 80 trials), then a novel animal (20 trials).
- Unused slot should stay inactive until a truly novel animal is presented.

## 8) Bayesian Model Reduction (BMR)
- After learning, the model reduces redundant concepts by applying BMR to **D** (and optionally A).
- If a concept was never observed, its learned A/D parameters can be **reset to pre-learning** values.
- BMR performance is best with accurate A; if A learning is imperfect, reduction is less reliable.

## 9) Generalization Task
- A different question is asked instead of “what animal is this?”
- Example: “Could this be seen from a distance?”
  - Answer depends on **size + color**: "yes" for large + colorful; otherwise "no".
- Learning disabled; model must generalize from existing feature knowledge.
- Test uses an animal the model has not seen; model answers based on feature rules.

## 10) Evaluation Metrics
- Reporting accuracy (specific vs basic) after learning.
- Time/exposure count until high accuracy (e.g., ~50 exposures for a new concept in the simple case).
- Successful avoidance of unused-slot engagement during familiar-only exposure.
- Generalization accuracy in the distance question task.
- Sanity checks from the paper: with fully known A, specific report accuracy is 100% across 32 sims (4 trials per animal); with only wings/gills knowledge, basic category accuracy is 100%.
- Supplementary demo code plots **A before/after learning**; we also track similarity of learned A to the true A for concept acquisition curves.
- When multiple concepts are learned without feedback, feature columns can permute; reporting accuracy can be evaluated after aligning learned columns to true feature signatures.

## 11) Parameters Not Explicitly Specified in Paper Text
(Need confirmation from SPM demo code or supplements)
- Dirichlet prior strengths for A and D.
- Learning rates (eta) and any update schedules.
- Policy precision (gamma/beta).
- Noise magnitude used to break symmetry in flat A columns.
- Exact C numeric values for feedback preferences.

## 12) Parameters Extracted from Concepts_model.m (Supplementary)
### Core dimensions
- No (outcomes): [3, 3, 3, 4] for size, color, wings/gills, feedback
- Ns (states): animal identity = 8, report = 11 (start + 10 reports)

### Prior states (D, d)
- D{1} = ones(8) (uniform concept prior)
- D{2} = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]ᵀ (start)
- d{1} = ones(8), d{2} = D{2}

### Report/action labels (order)
1. start
2. choose Parakeet
3. choose Parrot
4. choose Pigeon
5. choose Hawk
6. choose Clownfish
7. choose Manta ray
8. choose Sardine (Minnow)
9. choose Shark
10. choose Bird
11. choose Fish

### Feature mappings (A)
- Size (A{1}, outcomes 2–3): row2 = [0 1 0 1 0 1 0 1], row3 = [1 0 1 0 1 0 1 0]
- Color (A{2}, outcomes 2–3): row2 = [1 1 0 0 1 1 0 0], row3 = [0 0 1 1 0 0 1 1]
- Wings/Gills (A{3}, outcomes 2–3): row2 = [1 1 1 1 0 0 0 0], row3 = [0 0 0 0 1 1 1 1]
- Feedback (A{4}):
  - action 1 (start): outcome = start for all animals
  - actions 2–9 (specific): correct-specific only if report matches animal, otherwise incorrect
  - action 10 (bird): correct-basic for animals 1–4, incorrect for animals 5–8
  - action 11 (fish): correct-basic for animals 5–8, incorrect for animals 1–4

### Preferences (C)
- C{4}(2,:) = +4 (correct-specific)
- C{4}(4,:) = 0 (correct-basic)
- C{4}(3,:) = -4 (incorrect)
- Others = 0 (including feedback “start”)

### Policy and precision
- T = 2 (observe, then report)
- Reporting disabled during learning via policy restriction (only “stay” action)
- alpha = 128 (action selection inverse temperature)
- beta = 1 (policy precision parameter; higher beta → more randomness)

### Unknown concepts / “slot” initialization
- pa = 0 (flattens distributions)
- Removed knowledge columns set to uniform via softmax(log(A + exp(-4)) * pa) + 0.01 * Gaussian noise

## 12) Implementation Notes for Our Library
- Requires 2 hidden state factors (animal identity + report choice).
- Requires 4 outcome modalities (size, color, species-specific, feedback).
- Requires policy restriction during learning (no report actions).
- Requires BMR routine for D (and optionally A) to reproduce reduction results.
