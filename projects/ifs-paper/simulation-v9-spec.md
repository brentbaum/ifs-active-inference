# Simulation Specification: v9 — Hierarchical Relational Gating

**Date:** 2026-03-28
**Purpose:** One simulation testing the central v9 claim: witnessing works by relaxing protective predictions (gate) enough for burdened self-states to revise, and this revision generalizes across cues because it operates at identity level, not threat level.
**Language:** Julia (extends `projects/library/`)
**Target model file:** `projects/library/src/active_inference/ifs_model_v4.jl`
**Target runner:** `projects/library/scripts/ifs_simulation_v4.jl`

---

## Design Philosophy

The v9 simulation is leaner than v2. The witnessed-self-state channel (v2's channel 5) is gone. Self-energy is no longer a direct precision modulator. Instead, the key mechanism is **multi-cue gate inference**: the gate is a true hidden factor whose posterior is shaped by all four observation channels. Presence is one voice among several — it does not force the gate, but it tips the balance. When the gate opens, self-state can revise. When self-state revises, meaning follows.

The simulation tests one consequence of the theory: that relational contact (Presence cue) combined with corrective evidence produces an ordering — gate opens first, then self-state revises, then meaning updates, then adaptive policy emerges — and that this ordering transfers to novel cues because gate and self-state are shared across contexts while meaning is cue-specific.

### Simulation-Theory Gap (stated honestly)

The theory defines protectors as full parts with role-identities, feared consequences, target-part models, and cross-part appraisals. The simulation collapses all of this into one effective **gate state** — the net output of protector policies — represented as a single binary hidden factor. This is a deliberate simplification. Section 7 of the paper states it explicitly:

> "The simulation represents the effective gate state — the net output of protector policies — as a single hidden factor, while the theory allows for richer protector bundles."

---

## Architecture

### Hidden Factors (3 factors, 2 states each)

| Factor | Index | State 1 (burdened) | State 2 (revised) | Interpretation |
|---|---|---|---|---|
| **Gate state (G)** | 1 | `closed` | `permissive` | Net output of protector policies. When closed, the system blocks access to lower-layer states. When permissive, contact with exile self-state becomes possible. |
| **Exile self-state (S)** | 2 | `unmet_alone` | `held_capable` | The exile's identity-level prior, including developmental time-position ("I am six, alone with this"). Revision means the exile updates from frozen isolation to present-moment, relational possibility. |
| **Meaning / expected cost of contact (M)** | 3 | `contact_costly` | `contact_manageable` | The system's appraisal of what contact with the need will cost. Costly = flooding, shame, destabilization. Manageable = the need can be approached without catastrophe. |

**Constants:**
```julia
# Hidden factor 1: gate state
const V4_GATE_CLOSED = 1
const V4_GATE_PERMISSIVE = 2

# Hidden factor 2: exile self-state
const V4_SELF_UNMET_ALONE = 1
const V4_SELF_HELD_CAPABLE = 2

# Hidden factor 3: meaning / cost of contact
const V4_MEANING_CONTACT_COSTLY = 1
const V4_MEANING_CONTACT_MANAGEABLE = 2

const V4_NS = (2, 2, 2)  # num_states per factor
```

### Observation Channels (4 channels)

| Channel | Index | States | Depends primarily on | Role |
|---|---|---|---|---|
| **Need cue** | 1 | `dormant`, `activated` | Gate, Meaning | Whether the underlying need/longing/protest is currently activated. Dormant when gate is closed and meaning says contact is costly. Activated when need breaks through or meaning shifts. |
| **Interoceptive / impulse cue** | 2 | `calm`, `constricted`, `panic` | Gate, Self-state | Body signals. Calm when gate is permissive and self-state is held. Panic when gate is closed and self-state is unmet. Constricted = intermediate. |
| **External response cue** | 3 | `rejecting`, `neutral`, `supportive` | Meaning (+ environment) | Environmental response to the system's bids. This is the informational channel — it carries evidence about whether the world punishes contact. |
| **Presence cue** | 4 | `absent`, `present` | Self-state (+ control parameter) | Whether a broader self-anchor (Presence / Self-energy) is available. This is NOT a hidden factor — it is modulated by a control parameter (Self-energy level) that determines what the agent observes. Presence informs both gate and self-state. |

**Constants:**
```julia
# Observation 1: need cue
const V4_NEED_DORMANT = 1
const V4_NEED_ACTIVATED = 2

# Observation 2: interoceptive / impulse cue
const V4_INTERO_CALM = 1
const V4_INTERO_CONSTRICTED = 2
const V4_INTERO_PANIC = 3

# Observation 3: external response cue
const V4_EXT_REJECTING = 1
const V4_EXT_NEUTRAL = 2
const V4_EXT_SUPPORTIVE = 3

# Observation 4: presence cue
const V4_PRES_ABSENT = 1
const V4_PRES_PRESENT = 2

const V4_NO = (2, 3, 3, 2)  # num_observations per channel
```

### Policies (4 actions)

| Policy | Index | Interpretation | Relation to IFS |
|---|---|---|---|
| **Suppress / hide** | 1 | Shut down the activation, avoid contact with the need. | Protector-dominant: manager strategy. |
| **Protest / discharge** | 2 | Express distress reactively without relational contact. | Firefighter-like: reactive, not relational. |
| **Stay-with / witness** | 3 | Remain present to the activation without acting on it. | Self-led: the witnessing stance. |
| **Direct ask / reach** | 4 | Actively reach toward relational contact with the need. | Self-led: direct engagement with exile. |

**Constants:**
```julia
const V4_POLICY_SUPPRESS = 1
const V4_POLICY_PROTEST = 2
const V4_POLICY_STAYWITH = 3
const V4_POLICY_DIRECTASK = 4

const V4_NUM_POLICIES = 4
```

---

## Generative Model Specification

### A-Matrices (Likelihood Mappings)

Each A-matrix specifies P(observation | hidden states). The full tensor for each channel is `A[obs, gate, self, meaning]` with shape `(num_obs, 2, 2, 2)`.

#### Channel 1: Need Cue — A_need[obs, G, S, M]

The need cue activates when the gate allows access AND the meaning appraisal says contact is not prohibitively costly. If the gate is closed, the need stays dormant regardless. If contact is costly, the need is suppressed even when the gate is slightly open.

| G | S | M | P(dormant) | P(activated) |
|---|---|---|---|---|
| closed | unmet_alone | contact_costly | **0.95** | 0.05 |
| closed | unmet_alone | contact_manageable | **0.80** | 0.20 |
| closed | held_capable | contact_costly | **0.90** | 0.10 |
| closed | held_capable | contact_manageable | **0.75** | 0.25 |
| permissive | unmet_alone | contact_costly | 0.55 | **0.45** |
| permissive | unmet_alone | contact_manageable | 0.20 | **0.80** |
| permissive | held_capable | contact_costly | 0.50 | **0.50** |
| permissive | held_capable | contact_manageable | 0.15 | **0.85** |

**Logic:** Gate closed strongly suppresses need expression. When gate is permissive, need comes forward, especially when meaning says contact is manageable. Self-state has a minor modulating effect (held_capable slightly increases willingness to let the need show).

#### Channel 2: Interoceptive / Impulse Cue — A_intero[obs, G, S, M]

Body signals reflect the interaction of gate tension and self-state. When the gate is closed and self-state is unmet, the body is in panic or constriction. When the gate is permissive and self-state is held, the body calms.

| G | S | M | P(calm) | P(constricted) | P(panic) |
|---|---|---|---|---|---|
| closed | unmet_alone | contact_costly | 0.05 | 0.30 | **0.65** |
| closed | unmet_alone | contact_manageable | 0.10 | 0.35 | **0.55** |
| closed | held_capable | contact_costly | 0.15 | **0.50** | 0.35 |
| closed | held_capable | contact_manageable | 0.25 | **0.50** | 0.25 |
| permissive | unmet_alone | contact_costly | 0.15 | **0.45** | 0.40 |
| permissive | unmet_alone | contact_manageable | 0.30 | **0.45** | 0.25 |
| permissive | held_capable | contact_costly | **0.40** | 0.40 | 0.20 |
| permissive | held_capable | contact_manageable | **0.65** | 0.25 | 0.10 |

**Logic:** Primary drivers are gate and self-state. Gate closed + unmet_alone = panic. Gate permissive + held_capable = calm. Meaning has a secondary effect (manageable meaning allows more calm). The interoceptive channel is the body's readout of the system state.

#### Channel 3: External Response Cue — A_ext[obs, G, S, M]

The external response channel depends primarily on the meaning factor and is shaped by the actual observation the agent receives (the environment). In the generative model, meaning determines what the agent *expects* to see. The actual observation delivered to the agent is set by the experimental condition (see Conditions section).

| G | S | M | P(rejecting) | P(neutral) | P(supportive) |
|---|---|---|---|---|---|
| closed | unmet_alone | contact_costly | **0.60** | 0.30 | 0.10 |
| closed | unmet_alone | contact_manageable | 0.15 | 0.35 | **0.50** |
| closed | held_capable | contact_costly | **0.55** | 0.30 | 0.15 |
| closed | held_capable | contact_manageable | 0.15 | 0.35 | **0.50** |
| permissive | unmet_alone | contact_costly | **0.50** | 0.35 | 0.15 |
| permissive | unmet_alone | contact_manageable | 0.10 | 0.30 | **0.60** |
| permissive | held_capable | contact_costly | **0.45** | 0.35 | 0.20 |
| permissive | held_capable | contact_manageable | 0.10 | 0.25 | **0.65** |

**Logic:** Meaning is the dominant driver. Contact_costly predicts rejection. Contact_manageable predicts support. Gate and self-state have secondary effects (permissive gate + held self slightly increase expected supportiveness, reflecting that the system's own openness shapes how it perceives responses).

#### Channel 4: Presence Cue — A_pres[obs, G, S, M]

Presence depends primarily on self-state (held_capable self-states are more likely to detect Presence) and secondarily on gate state (permissive gate allows Presence to register). Meaning has minimal effect.

| G | S | M | P(absent) | P(present) |
|---|---|---|---|---|
| closed | unmet_alone | contact_costly | **0.85** | 0.15 |
| closed | unmet_alone | contact_manageable | **0.80** | 0.20 |
| closed | held_capable | contact_costly | 0.45 | **0.55** |
| closed | held_capable | contact_manageable | 0.40 | **0.60** |
| permissive | unmet_alone | contact_costly | **0.60** | 0.40 |
| permissive | unmet_alone | contact_manageable | **0.55** | 0.45 |
| permissive | held_capable | contact_costly | 0.20 | **0.80** |
| permissive | held_capable | contact_manageable | 0.15 | **0.85** |

**Logic:** Self-state is the primary driver — a held, capable self-state perceives Presence. Gate is secondary — a permissive gate makes Presence more detectable. Meaning has minimal influence. This channel is also the key entry point for Presence-as-control-parameter: the actual observation delivered depends on the Self-energy control parameter (see Conditions).

### Gate Coupling: Multi-Cue Inference (Option A)

The gate is a hidden factor inferred from ALL four observation channels via the A-matrices above. Each channel contributes evidence about the gate state:

1. **Need cue activated** → evidence that gate is permissive (need broke through)
2. **Interoceptive calm** → evidence that gate is permissive + self held; **panic** → gate closed
3. **External response supportive** → weak evidence for gate permissive; **rejecting** → weak evidence for gate closed
4. **Presence present** → evidence for gate permissive (Presence detected implies openness)

No single channel forces the gate. The posterior over gate state is the Bayesian combination of all four likelihood channels weighted by the current observations. This is the central design principle: **Presence is one voice among several.**

The coupling strength is visible in the A-matrix entries:
- Presence channel: P(present | permissive, held, manageable) = 0.85 vs P(present | closed, unmet, costly) = 0.15. This is strong but not deterministic.
- Interoceptive channel: P(calm | permissive, held, manageable) = 0.65 vs P(calm | closed, unmet, costly) = 0.05. Also strong.
- External and need channels provide corroborating evidence.

The gate posterior on any given trial reflects the joint evidence from all four channels.

---

### B-Matrices (Transition Dynamics)

B-matrices specify P(state_{t+1} | state_t, policy). They are 3D arrays of shape `(num_states, num_states, num_policies)` for each hidden factor. Entry `B[s', s, u]` = P(next_state = s' | current_state = s, action = u).

#### B_gate[s', s, u] — Gate transitions

The gate is policy-dependent. Stay-with and direct-ask favor opening. Suppress favors closing. Protest is neutral-to-closing.

**Columns = current state; rows = next state. One matrix per policy.**

**Suppress (u=1):**

|  | closed | permissive |
|---|---|---|
| closed | **0.95** | **0.70** |
| permissive | 0.05 | 0.30 |

**Protest (u=2):**

|  | closed | permissive |
|---|---|---|
| closed | **0.85** | **0.55** |
| permissive | 0.15 | 0.45 |

**Stay-with (u=3):**

|  | closed | permissive |
|---|---|---|
| closed | 0.40 | 0.10 |
| permissive | **0.60** | **0.90** |

**Direct ask (u=4):**

|  | closed | permissive |
|---|---|---|
| closed | 0.35 | 0.08 |
| permissive | **0.65** | **0.92** |

**Logic:** Suppress strongly maintains/reinstates gate closure. Protest is moderately closing (reactive discharge without relational engagement does not open gates). Stay-with and direct-ask strongly favor gate opening — these are the Self-led policies that build protector trust. Direct-ask is slightly stronger than stay-with because it represents active relational engagement.

#### B_self[s', s, u] — Exile self-state transitions

Self-state revision is **gate-dependent**, not directly policy-dependent. The key mechanism: self-state can only revise when the gate is permissive. We implement this through a **gate-conditioned B-matrix** — effectively `B_self[s', s, gate_state]` rather than `B_self[s', s, policy]`.

**Implementation note:** Since standard POMDP B-matrices are conditioned on actions, implement gate-conditioning by making B_self depend on the *inferred* gate state at each timestep. After computing the gate posterior, use it to interpolate between two transition matrices:

**B_self when gate = closed:**

|  | unmet_alone | held_capable |
|---|---|---|
| unmet_alone | **0.98** | **0.75** |
| held_capable | 0.02 | 0.25 |

**B_self when gate = permissive:**

|  | unmet_alone | held_capable |
|---|---|---|
| unmet_alone | 0.45 | 0.10 |
| held_capable | **0.55** | **0.90** |

**Logic:** When gate is closed, self-state is frozen — the exile cannot revise because access is blocked. P(stays unmet | unmet, closed) = 0.98. Even a held self-state drifts back toward unmet when the gate closes (0.75 reversion). When gate is permissive, self-state can revise — P(moves to held | unmet, permissive) = 0.55. Once held and gate remains permissive, it is stable (0.90 retention).

**Effective B_self at each timestep:**
```
B_self_eff = P(gate=closed) * B_self_closed + P(gate=permissive) * B_self_permissive
```

#### B_meaning[s', s, u] — Meaning transitions

Meaning is driven by external response observations, not directly by policy. Like self-state, implement this as observation-conditioned:

**B_meaning when external = rejecting:**

|  | contact_costly | contact_manageable |
|---|---|---|
| contact_costly | **0.95** | **0.70** |
| contact_manageable | 0.05 | 0.30 |

**B_meaning when external = neutral:**

|  | contact_costly | contact_manageable |
|---|---|---|
| contact_costly | **0.80** | 0.40 |
| contact_manageable | 0.20 | **0.60** |

**B_meaning when external = supportive:**

|  | contact_costly | contact_manageable |
|---|---|---|
| contact_costly | 0.35 | 0.08 |
| contact_manageable | **0.65** | **0.92** |

**Logic:** Meaning updates based on what the environment actually does. Rejecting responses confirm that contact is costly. Supportive responses disconfirm it. Neutral responses allow slow drift. This is the informational channel — it carries threat-level evidence.

**Effective B_meaning at each timestep:**
```
B_meaning_eff = P(ext=rejecting) * B_meaning_rej + P(ext=neutral) * B_meaning_neu + P(ext=supportive) * B_meaning_sup
```

Where P(ext=X) is the posterior probability over the external response observation.

**Implementation variant:** If observation-conditioned transitions prove complex, an alternative is to make B_meaning policy-dependent with stay-with and direct-ask favoring revision (since those policies lead to situations where corrective evidence is encountered). The observation-conditioned version is preferred because it separates the mechanism (external evidence) from the behavioral correlate (policy).

---

### C Matrix (Preference / Outcome Priors)

The C matrix encodes preferences over observations for Expected Free Energy (EFE) computation. These drive policy selection.

| Channel | Preferred | Dispreferred | Values |
|---|---|---|---|
| Need cue | Neither strongly | — | C_need = [0.0, 0.0] (neutral — the agent doesn't prefer the need to be dormant or active per se) |
| Interoceptive | calm | panic | C_intero = [1.0, -0.2, -1.5] |
| External response | supportive | rejecting | C_ext = [−1.5, 0.0, 1.0] |
| Presence | present | absent | C_pres = [−0.5, 0.8] |

**Logic:** The agent prefers calm body states, supportive responses, and Presence. It dislikes panic and rejection. Need cue preferences are neutral — the IFS claim is that the need itself is not the problem; the *predicted cost of contact* with the need is.

---

### D Priors (Initial Beliefs)

Strongly burdened starting point. These represent a consolidated part system.

| Factor | P(burdened) | P(revised) | Interpretation |
|---|---|---|---|
| Gate (G) | **0.90** (closed) | 0.10 (permissive) | The system starts with the protector gate firmly shut. This reflects a history of learned protection. |
| Self-state (S) | **0.90** (unmet_alone) | 0.10 (held_capable) | The exile starts frozen in the burdened self-state — developmentally young, isolated, unable to contact Presence. |
| Meaning (M) | **0.80** (contact_costly) | 0.20 (contact_manageable) | Slightly less extreme than gate and self-state — meaning is somewhat more responsive to environmental evidence. This asymmetry matters: it allows meaning to shift faster than identity, producing the temporal ordering the paper predicts. |

**Implementation:**
```julia
D_gate = [0.90, 0.10]
D_self = [0.90, 0.10]
D_meaning = [0.80, 0.20]
```

---

### E Prior (Policy Prior / Habit)

Initial policy preference reflecting the burdened system's habitual strategies:

```julia
E = [0.50, 0.25, 0.15, 0.10]  # suppress, protest, stay-with, direct-ask
```

**Logic:** The burdened system defaults to suppress (50%) and protest (25%). Stay-with (15%) and direct-ask (10%) are available but unlikely without sufficient gate opening and self-state revision. The E prior is softened by EFE during inference.

---

## Self-Energy as Control Parameter

Self-energy (E_t) is a **control parameter**, not a hidden factor. It is not inferred by the agent. It modulates **what the agent observes** on the Presence channel.

**Implementation:** Self-energy determines the probability that the delivered Presence observation is `present` vs `absent`:

```julia
function deliver_presence_observation(E_t::Float64)
    # E_t ∈ [0, 1]
    # At E_t = 0: always deliver absent
    # At E_t = 1: always deliver present
    # Sigmoid mapping with threshold around 0.4
    p_present = 1.0 / (1.0 + exp(-8.0 * (E_t - 0.4)))
    return rand() < p_present ? V4_PRES_PRESENT : V4_PRES_ABSENT
end
```

Self-energy does NOT directly modulate precision, gate state, or any A/B matrix. It only controls what the agent sees on the Presence channel. This is cleaner than v2's precision-modulation approach: Presence is an observation, and the agent infers what it implies about gate, self-state, and meaning through the same Bayesian inference as every other observation.

For the three conditions, Self-energy is fixed per condition (not a schedule):
- Informational-only: E_t = 0.0 (Presence absent)
- Relational-only: E_t = 0.9 (Presence reliably present)
- Full witnessing: E_t = 0.9 (Presence reliably present)

---

## Experimental Conditions

### Trial Structure

Each condition runs for **T = 25 trials** (training phase) followed by a **probe phase** of **5 trials** with learning frozen (behavioral assay).

During the training phase, the agent receives observations, updates beliefs, selects policies via EFE, and learns (updates D priors via Dirichlet accumulation). During the probe phase, beliefs are frozen — the agent acts on what it has learned.

### Delivered Observations by Condition

For each condition, the environment delivers specific observations on the external response and Presence channels. The need cue and interoceptive channels are generated from the A-matrices given the agent's current hidden state posteriors (i.e., the agent generates its own expected interoceptive and need cue observations based on its beliefs).

**Alternative:** Deliver all four observations from the generative process (sample from A-matrices given true hidden state). The conditions differ only in the true environmental state. Prefer this approach for cleanliness — it avoids splitting channels into "delivered" vs "generated."

**True environmental state by condition:**

#### Condition 1: Informational-Only (Exposure Analogue)

Corrective external evidence, no Presence.

| Channel | Delivered observation | Rationale |
|---|---|---|
| Need cue | Sampled from A given true state | Agent's own generative process |
| Interoceptive | Sampled from A given true state | Agent's own generative process |
| External response | **supportive** (fixed) | The environment provides corrective evidence: contact is met with support, not rejection |
| Presence | **absent** (E_t = 0.0) | No Self-energy. No broader self-anchor available. This is the "informational correction without relational holding" condition. |

**Expected result:** Meaning shifts toward contact_manageable (strong corrective external evidence). Gate and self-state barely move — there is no Presence signal to inform them. The agent learns that the environment is not rejecting, but the identity-level frozen-ness (unmet_alone, gate closed) persists. Policy may shift slightly away from suppress toward protest, but stay-with and direct-ask remain unlikely.

#### Condition 2: Relational-Only

Presence available, but only neutral external evidence.

| Channel | Delivered observation | Rationale |
|---|---|---|
| Need cue | Sampled from A given true state | |
| Interoceptive | Sampled from A given true state | |
| External response | **neutral** (fixed) | The environment is neither rejecting nor supportive — it just is. No corrective threat-level information. |
| Presence | **present** (E_t = 0.9) | Self-energy is available. The broader self-anchor can be perceived. |

**Expected result:** Gate opens (Presence signal informs gate via A-matrix). Self-state begins to shift (gate opening allows revision; Presence informs self-state via A-matrix). Meaning shifts minimally — neutral external evidence provides only weak correction. The agent may move toward stay-with but not strongly toward direct-ask (meaning still says contact is somewhat costly). This is "relational holding without corrective information."

#### Condition 3: Full Witnessing

Presence AND corrective external evidence. The IFS-canonical condition.

| Channel | Delivered observation | Rationale |
|---|---|---|
| Need cue | Sampled from A given true state | |
| Interoceptive | Sampled from A given true state | |
| External response | **supportive** (fixed) | Corrective evidence: contact is safe. |
| Presence | **present** (E_t = 0.9) | Self-energy available. Broader self-anchor perceived. |

**Expected result — the key prediction:**
1. **Gate opens first** (trials 1-8): Presence + calming interoceptive signals + supportive external → gate posterior shifts toward permissive.
2. **Self-state revises second** (trials 5-15): Once gate is permissive, B_self allows revision. Self-state shifts from unmet_alone toward held_capable.
3. **Meaning updates third** (trials 10-20): Supportive external response accumulates evidence. Meaning shifts from contact_costly toward contact_manageable.
4. **Policy shifts last** (trials 15-25): As gate opens, self-state revises, and meaning shifts, EFE increasingly favors stay-with and direct-ask over suppress and protest.

The temporal ordering — gate, self, meaning, policy — is the paper's central empirical prediction. It reflects the theory's claim that protector relaxation precedes exile revision, which precedes meaning revision, which precedes behavioral change.

---

## Gate Ablation

### Design

Block the Presence cue from informing gate state by setting the Presence-to-Gate likelihood to **uniform**. Presence still informs self-state and meaning through the A-matrices.

**Implementation:** Create a modified A_pres matrix for the ablation condition:

```julia
# Original: A_pres[obs, G, S, M] — gate matters
# Ablation: A_pres_ablated[obs, G, S, M] — gate dimension is uniform

# For each (S, M) pair, set:
# P(absent | closed, S, M) = P(absent | permissive, S, M) = average of original values
# P(present | closed, S, M) = P(present | permissive, S, M) = average of original values
```

This means the agent can still perceive Presence, and Presence still informs its beliefs about self-state and meaning, but observing Presence provides **zero evidence** about the gate state. The gate can still be informed by the other three channels (need cue, interoceptive, external response).

### Ablation Condition

Run under full-witnessing observations (external = supportive, Presence = present, E_t = 0.9) with the modified A_pres matrix.

**Expected result:** The witnessing advantage disappears. Without Presence informing the gate, the gate's opening depends only on interoceptive and external channels — which are the same as the informational-only condition plus a Presence observation that the gate cannot use. Self-state revision slows dramatically (gate stays more closed). The ordering collapses. The ablation condition should look similar to the informational-only condition, not the full-witnessing condition.

**What this proves:** The witnessing advantage is specifically mediated by Presence informing the gate. Remove that pathway, and relational contact loses its distinctive power.

---

## Transfer Probe

### Design

The transfer probe tests whether witnessing produces generalization across cues. The mechanism: gate state and self-state are shared across contexts (they are identity-level), while meaning is cue-specific (it is learned about a particular type of need/situation).

**Implementation: Shared Dirichlet Banks**

Use Dirichlet concentration parameters for learning, following v2/v3 patterns:

| Bank | Shared across cues? | What it represents |
|---|---|---|
| `d_gate` | **Yes (shared)** | Identity-level protector policy — learned once, applies everywhere |
| `d_self` | **Yes (shared)** | Identity-level self-state — learned once, applies everywhere |
| `d_meaning_A` | **No (cue A specific)** | Threat/cost appraisal for cue A context |
| `d_meaning_B` | **No (cue B specific)** | Threat/cost appraisal for cue B context |

**Cue definitions (abstract with concrete gloss):**
- **Cue A:** "comfort unavailable" — the need is for soothing/comfort, and the original wound is that comfort was absent or withdrawn. Training cue.
- **Cue B:** "request for help unanswered" — the need is for assistance/support, and the original wound is that asking for help was met with dismissal or shame. Novel probe cue.

Both cues activate the same gate and self-state systems (same protector stack, same exile identity), but they have different meaning priors (different specific fears about what contact will cost in each context).

### Transfer Protocol

1. **Training phase (cue A):** 20 trials under each condition (informational-only, relational-only, full witnessing). Gate and self-state Dirichlet banks accumulate. Meaning bank d_meaning_A accumulates.
2. **Probe phase (cue B):** 5 trials. First probe trial is the clean discriminant — no prior cue B learning. Gate and self-state carry over from cue A training. Meaning starts from d_meaning_B (fresh, burdened prior: [0.80, 0.20]).
3. **Probe observations:** Same condition as training (e.g., if trained under full witnessing, probe under full witnessing observations for cue B).

### Expected Results

**Full witnessing (trained on cue A, probed on cue B):**
- Gate starts already open (shared d_gate was updated during cue A training)
- Self-state starts already revised (shared d_self was updated)
- Meaning starts fresh and burdened (d_meaning_B untouched)
- Result: gate and self-state transfer immediately. Meaning for cue B must still be learned, but it updates faster because the gate is already open and self-state is already held. Policy shift is faster than starting from scratch.

**Informational-only (trained on cue A, probed on cue B):**
- Gate still mostly closed (informational-only didn't open it much)
- Self-state still mostly unmet (informational-only didn't revise it)
- Meaning for cue A was revised (d_meaning_A updated), but d_meaning_B is fresh
- Result: minimal transfer. The agent faces cue B with the same burdened gate and self-state. Any meaning revision from cue A does not help with cue B (cue-specific).

**The discriminant:** On the first cue B probe trial, compare P(gate=permissive) and P(self=held_capable) across conditions. In full witnessing, these should be high (transferred). In informational-only, they should be low (not transferred). This is the paper's generalization prediction: identity-level revision generalizes; threat-level revision does not.

---

## Success Criteria (Pre-Registered)

### 1. Hard Temporal Ordering (Full Witnessing)

In the full-witnessing condition, the four quantities must cross the 0.50 threshold in this order:

```
gate (P(permissive) > 0.50)  →  self (P(held) > 0.50)  →  meaning (P(manageable) > 0.50)  →  policy (P(stay-with + direct-ask) > P(suppress + protest))
```

**Metric:** First-passage time for each quantity. Gate first-passage < self first-passage < meaning first-passage < policy crossover.

**Tolerance:** Each lag must be at least 2 trials. If gate and self cross within 1 trial of each other, the ordering is ambiguous and the spec needs revision.

### 2. Unburdening Threshold

In the full-witnessing condition, after 25 training trials:
- P(gate = permissive) > 0.50 sustained across the final 5 training trials
- P(self = held_capable) > 0.50 sustained across the final 5 training trials
- Policy: P(suppress) is no longer the dominant policy (P(suppress) < max(P(stay-with), P(direct-ask)))

This represents unburdening: the burdened attractor basin has collapsed. The gate no longer defaults to closed. The exile is no longer frozen in unmet_alone. The habitual suppress policy is no longer dominant.

### 3. Transfer

On the **first** cue B probe trial (clean discriminant):
- Full witnessing: P(gate = permissive) > 0.50 AND P(self = held) > 0.50
- Informational-only: P(gate = permissive) < 0.30 AND P(self = held) < 0.30
- Difference between conditions on gate and self: at least 0.20

Meaning for cue B should start burdened (~0.80 costly) in all conditions on the first probe trial, confirming that meaning does NOT transfer.

### 4. Ablation

Under full-witnessing observations with Presence-to-Gate blocked:
- P(gate = permissive) at trial 25 is < 0.40 (gate did not fully open)
- P(self = held) at trial 25 is < 0.40 (self did not fully revise)
- The temporal ordering (criterion 1) is absent or degraded
- The ablation condition's final posteriors are closer to informational-only than to full witnessing

**Metric:** |posteriors_ablation - posteriors_informational| < |posteriors_ablation - posteriors_witnessing| for gate and self-state.

---

## Not Simulated (By Design)

The following are part of IFS theory but are deliberately excluded from this simulation. Each exclusion is justified.

| Omission | Reason |
|---|---|
| **Ceremonial release / imaginal unburdening** | The simulation models the window (witnessing) that makes this possible, not the process itself. Unburdening is represented as the durable posterior shift, not as a discrete ceremony. |
| **Developmental aging of all layers** | The theory describes layered protection with developmentally later strategies wrapping earlier ones. The simulation collapses this to one gate state. Multi-layer aging would require a recursive model. |
| **Multi-layer protector stacks** | Same as above. One effective gate represents the net output. The theory section (Section 4) describes stacking; the simulation tests one consequence of it. |
| **Polarization** | Other-parts-in-world-model is a theoretical contribution (Section 4). Simulating it would require multi-agent dynamics beyond the current scope. |
| **Therapist as second agent** | The therapist's contribution is collapsed into the Presence control parameter. A two-agent model is future work. |
| **8 C's of Self-leadership** | Cut from the paper entirely. Self-energy is the scalar proxy. |
| **Formation** | The simulation starts from a burdened state. How that state formed is not modeled. |
| **Self-like parts** | Acknowledged as unsolved in the theory. Not representable in this architecture. |
| **Retrieval / reintegration** | Downstream of witnessing. The simulation models the witnessing window, not the full IFS arc. |

---

## Parameter Sensitivity

### Requirement

All four success criteria must survive **plus/minus 20% variation** in every key parameter. If a criterion depends on a knife-edge parameter setting, the design is fragile and must be revised.

### Parameters to Sweep

| Parameter | Baseline | Range | Criterion most affected |
|---|---|---|---|
| D_gate prior (P(closed)) | 0.90 | 0.72 - 1.00 | Ordering (criterion 1) |
| D_self prior (P(unmet)) | 0.90 | 0.72 - 1.00 | Ordering (criterion 1) |
| D_meaning prior (P(costly)) | 0.80 | 0.64 - 0.96 | Ordering (criterion 1) |
| B_self revision rate (P(held \| unmet, permissive)) | 0.55 | 0.44 - 0.66 | Ordering + unburdening |
| B_gate opening rate (P(permissive \| closed, stay-with)) | 0.60 | 0.48 - 0.72 | Ordering + unburdening |
| B_meaning revision rate (P(manageable \| costly, supportive)) | 0.65 | 0.52 - 0.78 | Ordering + transfer |
| A_pres coupling (P(present \| permissive, held, manageable)) | 0.85 | 0.68 - 1.00 | Ablation (criterion 4) |
| E prior (suppress dominance) | 0.50 | 0.40 - 0.60 | Policy ordering |
| Self-energy sigmoid threshold | 0.4 | 0.32 - 0.48 | All conditions |
| Number of training trials | 25 | 20 - 30 | Unburdening (criterion 2) |

### Sweep Protocol

1. One-at-a-time (OAT) sweep: vary each parameter independently at ±20% while holding others at baseline.
2. For each setting, run 50 replications (stochastic observation sampling).
3. Report: fraction of replications where each success criterion passes.
4. Criterion: **>80% of replications** pass at every point in the ±20% range.
5. If a parameter fails: either widen the passing range in the A/B matrices or flag as a known fragility in the appendix.

---

## Figures to Generate

### Figure 1: Architecture Diagram

Schematic of the generative model:
- Three hidden factors (gate, self-state, meaning) with directed arrows showing causal dependencies
- Four observation channels with arrows from hidden factors showing which factors inform each channel
- Four policies with arrows to gate (B_gate is policy-dependent)
- Self-energy as external control parameter feeding into Presence channel
- Dashed arrows for gate-conditioned self-state transitions and observation-conditioned meaning transitions
- Ablation shown as a crossed-out arrow from Presence to Gate

### Figure 2: Training Trajectories + Transfer (5 panels)

**Panel A:** P(gate = permissive) across trials for all three conditions + ablation. Full witnessing rises first and fastest. Relational-only rises second. Informational-only and ablation stay low.

**Panel B:** P(self = held_capable) across trials. Same ordering but lagged behind gate. Full witnessing crosses 0.50 after gate does.

**Panel C:** P(meaning = contact_manageable) across trials. Informational-only and full witnessing both rise (both have supportive external). Relational-only rises slowly (neutral external). Ablation rises like informational-only.

**Panel D:** P(stay-with + direct-ask) across trials (policy shift). Full witnessing crosses over from suppress-dominant to Self-led-dominant last of the three hidden factors.

**Panel E:** Cue B transfer probe. Bar chart or line showing P(gate=permissive) and P(self=held) on first cue B trial across conditions. Full witnessing shows high transfer. Informational-only shows none.

**Annotations:** First-passage time markers (vertical dotted lines or ticks) on panels A-D showing when each quantity crosses 0.50 in the full-witnessing condition. The stagger between these markers IS the paper's argument.

### Figure 3 (Appendix): Sensitivity Analysis

Heatmap or strip chart showing pass rate for each success criterion across ±20% parameter variations.

---

## Implementation Notes

### Extending the Existing Codebase

Build as `ifs_model_v4.jl`. Follow v2 structural patterns:
- Index constants at top
- `@kwdef` parameter struct
- Condition config struct
- Environment struct
- Model struct holding A, B, D matrices
- Two-stage inference per timestep (not needed here — all channels update simultaneously; single-stage is fine since there is no witnessed-self-state gating)
- Aggregation structs for results

### Key Differences from v2

| Feature | v2 | v4 |
|---|---|---|
| Hidden factors | Self-state, Threat, Expected outcome | Gate, Self-state, Meaning |
| Observation channels | 5 (including witnessed self-state) | 4 (no witnessed self-state) |
| Self-energy mechanism | Precision modulation (beta/gamma exponents) | Control parameter for Presence observation |
| Gate | Not a hidden factor (derived from capture index) | True hidden factor inferred from all channels |
| Policies | Avoid, Inspect, Stay | Suppress, Protest, Stay-with, Direct-ask |
| Transfer probe | Not in v2 | Shared Dirichlet banks |
| A-matrix architecture | 5D tensor | 4D tensor per channel |
| B-matrix conditioning | All policy-conditioned | Gate: policy-conditioned; Self: gate-conditioned; Meaning: observation-conditioned |

### Dirichlet Learning

For the transfer probe, use Dirichlet concentration parameters that accumulate evidence across trials:

```julia
# After each trial, update Dirichlet parameters:
# d_gate += learning_rate * (posterior_gate - prior_gate)
# d_self += learning_rate * (posterior_self - prior_self)
# d_meaning_cue += learning_rate * (posterior_meaning - prior_meaning)  # cue-specific

# D prior for next trial = normalize(d)
```

Gate and self-state banks are shared across cues A and B. Meaning banks are cue-specific. This is the structural assumption that produces differential transfer.

### File Structure

```
projects/library/src/active_inference/ifs_model_v4.jl     # Model
projects/library/scripts/ifs_simulation_v4.jl              # Runner + figures
projects/ifs-paper/figures/v4/                              # Output
projects/ifs-paper/simulation-v9-spec.md                   # This file
projects/ifs-paper/simulation-v9-magic-numbers.md          # Parameter registry
```

### Run Parameters

- Training trials: T = 25
- Probe trials: T = 5
- Replications per condition: N = 50 (for error bars and sensitivity)
- Learning rate: 0.3 (Dirichlet accumulation)
- Policy precision (softmax inverse temperature): 4.0
- Self-energy: 0.0 (informational), 0.9 (relational / witnessing)

---

## Relation to Paper Sections

| Paper section | What simulation supports |
|---|---|
| §3 (Formalization) | Hidden factor definitions (gate, self-state, meaning) are the computational translation of exile bundles and protector policies |
| §4 (Layered Protection) | Gate as effective output of protector stack; multi-cue inference over gate state |
| §5 (Self-Energy) | Self-energy as control parameter modulating Presence observation delivery |
| §6 (Relational PE) | Full witnessing produces the ordering predicted by relational prediction error theory: protector (gate) relaxes before exile (self-state) revises |
| §7 (Simulation Evidence) | All results reported here |
| §8 (Discussion) | Transfer probe supports generalization prediction; ablation supports mechanism claim; "not simulated" list grounds limitations |

---

## Verification Checklist

Before declaring the simulation complete:

- [ ] All four success criteria pass at baseline parameters
- [ ] Temporal ordering is visible in Figure 2 panels A-D
- [ ] Transfer is visible in Figure 2 panel E
- [ ] Ablation eliminates witnessing advantage
- [ ] All criteria survive ±20% parameter variation (>80% of replications)
- [ ] Gate opening is NOT forced by Presence alone (test: Presence=present but external=rejecting and interoceptive=panic should leave gate mostly closed)
- [ ] Simulation-theory gap is documented in runner script comments
- [ ] Parameter registry (simulation-v9-magic-numbers.md) is up to date
