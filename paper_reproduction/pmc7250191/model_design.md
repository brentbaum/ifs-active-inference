# Model Design (PMC7250191 / Concepts_model.m)

This document encodes the **exact generative model structure** from the supplementary
`Concepts_model.m` and how we will represent it in our Julia library.

## 1) Dimensions
- **Hidden state factors (Nf = 2)**
  - Factor 1: `animal` (Ns1 = 8)
  - Factor 2: `report` (Ns2 = 11) = {start + 10 reports}
- **Outcome modalities (Ng = 4)**
  - Modality 1: size (No1 = 3; row1 unused)
  - Modality 2: color (No2 = 3; row1 unused)
  - Modality 3: wings/gills (No3 = 3; row1 unused)
  - Modality 4: feedback (No4 = 4) = {start, correct‑specific, incorrect, correct‑basic}
- **Trial length**: `T = 2` (observe then report)

## 2) Labels / Ordering
### Animal identities (columns)
1. Parakeet
2. Parrot
3. Pigeon
4. Hawk
5. Clownfish
6. Manta ray
7. Minnow (report label uses “Sardine”)
8. Shark

### Report states (rows / actions)
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

## 3) A: Likelihoods
### Features (modality 1–3)
Features are independent of the report state, so A is repeated across report states.
For each modality, rows 2–3 encode the binary feature; row 1 is unused/zero.

- **Size** (A1 rows 2–3)
  - row2: [0 1 0 1 0 1 0 1]
  - row3: [1 0 1 0 1 0 1 0]

- **Color** (A2 rows 2–3)
  - row2: [1 1 0 0 1 1 0 0]
  - row3: [0 0 1 1 0 0 1 1]

- **Wings/Gills** (A3 rows 2–3)
  - row2: [1 1 1 1 0 0 0 0]
  - row3: [0 0 0 0 1 1 1 1]

### Feedback (modality 4)
Feedback depends on **animal identity** + **report choice**:
- Action 1 (start): always `start`.
- Actions 2–9 (specific): `correct‑specific` if report matches animal, else `incorrect`.
- Action 10 (bird): `correct‑basic` for animals 1–4, else `incorrect`.
- Action 11 (fish): `correct‑basic` for animals 5–8, else `incorrect`.

## 4) B: Transitions
- **Animal** factor: identity matrix (animal does not change within trial).
- **Report** factor: controllable; action `k` transitions to report state `k`.
  - Report states (2–11) are absorbing once selected.

## 5) C: Preferences
- Only feedback modality is non‑zero:
  - correct‑specific: +4
  - correct‑basic: 0
  - incorrect: −4
  - start: 0
- Other modalities: 0

## 6) D: Priors and Dirichlet beliefs
- D{1} = ones(8) (uniform over animals)
- D{2} = [1, 0, …, 0] (start state)
- d{1} = ones(8), d{2} = D{2}

## 7) Learning and Precision
- A learning enabled (`likelihood_A_learning = 1`).
- D learning enabled (`prior_D_learning = 1`).
- **alpha = 128** (action selection inverse temperature)
- **beta = 1** (policy precision; higher beta → more random). We map to our `gamma = 1/beta`.

## 8) Unknown concept initialization
For any “unknown” concept column, knowledge is flattened via:
```
spm_softmax(pa * log(A + exp(-4))) + 0.01 * randn
```
with `pa = 0`, applied to rows 2–3 for each feature modality.

## 9) Policy sets
- **Learning phase**: policy restriction to “stay” (only action=1).
- **Reporting phase**: actions 2–11 available as policies.

## 10) Implementation mapping to our library
- `AIFModel` with `T=2`, `Ns=(8,11)`, `No=(3,3,3,4)`
- `A` built directly from rules above
- `B` identity for animal; action‑controlled report transitions
- `C` only on feedback modality
- `D` uniform + start
- Learning script should allow toggling:
  - `remove_granularity`, `remove_{animal}_knowledge`
  - `prevent_reporting`
  - `BMR`

