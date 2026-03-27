# Simulation v3: Generalization Test
## Does identity-level revision transfer to novel stimuli?

**Date:** 2026-03-27
**Purpose:** Test Move 3's distinctive prediction: self-state revision (relational depth) generalizes across stimuli; threat revision (exposure) stays local.
**Designed by:** Claude + GPT 5.4 adversarial collaboration (2 rounds)

---

## Design philosophy

The v2 simulation proved Move 1 (H1 cascade) and Move 2 (depth-gated threshold). But adversarial Test 4 showed it does NOT prove Move 3: replacing Channel 5's self-state content with threat content produced similar dynamics. The model couldn't distinguish WHERE evidence enters the causal chain.

V3 shifts the burden of proof from "what opens late within one trial" to "what generalizes across trials after dog-only training." The discriminant is transfer to a novel stimulus (cat), not within-trial dynamics.

---

## Architecture

### Hidden factors (2, minimal)

| Factor | States | Scope |
|---|---|---|
| Self-state | helpless / resourced | SHARED across all stimuli |
| Threat | dangerous / safe | Current stimulus only |

Stimulus context (dog vs cat) is KNOWN, not inferred.

### Learned priors (Dirichlet banks)

Three separate Dirichlet prior banks, updated across trials:
- `pD_self` — shared identity prior
- `pD_threat_dog` — dog-specific threat prior
- `pD_threat_cat` — cat-specific threat prior (untouched during dog training)

At the start of each trial, the threat prior is loaded from the stimulus-appropriate bank.

### Observations (3 channels)

| Channel | Outcomes | Source | Notes |
|---|---|---|---|
| Cue | dog / cat | Deterministic from stimulus | Tells the agent what it's facing |
| Self evidence | helpless-like / resourced-like | Always truthful (adult in safe context) | Always available. Precision modulated by E_t. No gate. |
| Outcome | harm / neutral | Depends on threat + contact | Provides learning signal |

### Within-trial structure

1. Observe cue (dog or cat)
2. Observe self evidence
3. Choose or force action (avoid / contact)
4. Observe outcome

B matrices = identity. States are static within a trial. The "cascade" is sequential inference updating beliefs in order, not B-matrix propagation.

### Precision modulation

Standard Self-energy balance, no explicit gate:
```
π_part_eff = π_part * exp(-β * E_t)
λ_self_eff = λ_self * exp(+γ * E_t)
```

Under low E_t (capture): self prior is rigid, self evidence can't overcome it.
Under high E_t (relational depth): self prior softens, self evidence lands.

### Learning rule (cross-trial)

After each TRAINING trial, update Dirichlet priors from final posteriors:
```
pD_self ← pD_self + η_self * q_self(final)
pD_threat_s ← pD_threat_s + η_threat * q_threat(final)
```

- **H1:** Both updates active on dog trials
- **H2:** Only `pD_threat_dog` updates. `pD_self` is frozen.
- **Cat probes:** All learning frozen.

### Policies

- Dog training trials: forced contact (standard exposure/witnessing protocol)
- Cat probe trials: free choice between avoid and contact

---

## Experimental conditions

| Condition | Architecture | E_t | What updates during dog training | Expected cat transfer |
|---|---|---|---|---|
| H1-highE | H1 (self learns) | 0.85 | d_self + d_threat_dog | YES — self revised, cat benefits |
| H2-highE | H2 (self frozen) | 0.85 | d_threat_dog only | NO — only dog threat revised |
| H1-lowE | H1 (self learns) | 0.15 | d_threat_dog (self evidence too weak) | NO — self didn't revise |

---

## Protocol

### Phase 1: Dog training (20 trials)
- Stimulus: dog
- Action: forced contact
- Context: safe (dog is friendly, no harm)
- Learning: active (per condition)

### Phase 2: Cat probe (5 trials, learning frozen)
- Stimulus: cat
- Action: free choice
- Context: safe
- Learning: frozen
- The first cat probe is the clean discriminant. Trials 2-5 are repeated measures for CI.

---

## Pre-registered success criteria

1. **Matched dog fit:** Final 5 dog trials show strong approach in both H1-highE and H2-highE. |P(contact_dog)_H1 - P(contact_dog)_H2| < 0.10.

2. **Shared-self revision:** Across dog training, ΔP(resourced_self) > 0.25 in H1-highE.

3. **Threat-dog revision:** Across dog training, ΔP(safe_dog) > 0.25 in both H1-highE and H2-highE.

4. **Low-E blockade:** ΔP(resourced_self) < 0.10 in H1-lowE.

5. **Cat transfer discriminant:** First cat probe P(contact_cat) in H1-highE exceeds both H2-highE and H1-lowE by > 0.20.

6. **Stimulus specificity:** D_threat_cat change after dog training is negligible (L1 shift < 0.05). Transfer comes from revised d_self, not from secretly rewriting cat threat priors.

7. **Self-learning necessity:** Setting η_self = 0 in H1 collapses cat transfer to H2 levels.

---

## Pre-registered adversarial tests

1. **Fake-content test:** Replace self evidence with threat evidence. Dog learning may persist, cat transfer should collapse.
2. **Counterbalanced training:** Train on cat, probe dog. Transfer should reverse symmetrically.
3. **Real-danger probe:** After revision, present cat in actually-dangerous context. Agent should still avoid.
4. **Sensitivity sweep:** Vary η_self, π_part, λ_self, E_t thresholds. Qualitative transfer result must hold.
5. **Matched-fit verification:** H1 and H2 must produce similar dog-training trajectories.

---

## Figures

### Figure 1: "Identity Revision Transfers, Threat Revision Doesn't" (THE key figure)

Two panels:

**Left panel — Dog training (20 trials):**
- Three lines each for P(resourced_self) and P(safe_dog)
- H1-highE: both rise (self + threat revise)
- H2-highE: only threat rises (self frozen)
- H1-lowE: only threat rises slowly (self evidence too weak)
- All three conditions converge on similar dog approach by trial 20

**Right panel — First cat probe:**
- Bar chart: P(contact_cat) for each condition
- H1-highE: high (transfer from revised self)
- H2-highE: low (only dog threat revised, cat untouched)
- H1-lowE: low (self didn't revise)
- The GAP between H1-highE and the others IS Move 3

### Figure 2: "Within-Trial Cascade" (support figure)
- On a single dog trial under H1-highE, show sequential inference: self posterior updates before/alongside threat posterior
- Downgraded from headline to mechanism support

### Figure 3: "Self-Learning Necessity" (ablation)
- η_self = 0 in H1 → cat transfer collapses to H2 levels
- Confirms that self-state learning is necessary for transfer

### Figure 4: "Stimulus Specificity" (control)
- D_threat_cat before and after dog training → negligible change
- Transfer is through revised d_self, not through threat leakage

---

## Relation to paper

- **Move 1 (§3):** The bundle structure with self-state as organizing prior is why revision at the root generalizes
- **Move 2 (§6-8):** Self-energy determines whether self evidence lands (precision balance)
- **Move 3 (§8.3):** The generalization test IS the distinctive prediction. Self-state revision transfers because identity is shared across situations. Threat revision stays local because it's stimulus-specific.
- **§12.4:** This is the paper's cleanest empirical target made computational

---

## Implementation notes

- Build as `ifs_model_v3.jl`
- Extend the existing D-learning infrastructure from v2
- 2 hidden factors keeps matrices small (2×2)
- 50+ replications per condition
- Parameter sensitivity ±20%
- Save figures to `figures/v3/`

---

## What this proves that v2 couldn't

V2 showed: a gated channel produces a threshold effect and a cascade.
V3 shows: identity-level revision (shared self-state) transfers to novel stimuli; threat-level revision (stimulus-specific) does not. The content of what gets revised matters — not just the timing or gating of evidence delivery.

That is Move 3's distinctive claim.
