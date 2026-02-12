# Chamberlin 2022 Task Spec (Coherence Therapy via Active Inference)

Source paper: "The Active Inference Model of Coherence Therapy" (Frontiers in Human Neuroscience, 2022).

**Note:** Paper is theoretical - no simulation exists. This spec proposes a simulation that operationalizes the key claims.

## 1) Task Overview
- Agent has a protective schema formed under stress that generates avoidance behavior.
- Schema is initially **modular** (context-blind): fires regardless of current context.
- Therapy renders schema **integrated** (context-sensitive): agent recognizes context.
- Resolution occurs when agent realizes current context doesn't warrant protective behavior.

## 2) Core Claim to Test
From p3: "successful Discovery of the precise symptom necessitating schema results in immediate and enduring cessation of the symptom in more than half of clients"

**Simulation hypothesis:** Resolution can occur WITHOUT belief updating - just by enabling context-sensitivity in policy selection.

## 3) Hidden State Factors (Nf = 4)

| Factor | States | Description |
|--------|--------|-------------|
| f1: context | 3 | Current environmental context: {safe, ambiguous, dangerous} |
| f2: action | 4 | Agent behavior: {wait, approach, avoid, report} |
| f3: threat | 2 | Belief about threat: {threatening, non-threatening} |
| f4: schema_mode | 2 | Schema accessibility: {modular, integrated} |

**Dimensions:** Ns = (3, 4, 2, 2)

### Explicit Index Mapping (CANONICAL)

```julia
# Factor 1: context
const CONTEXT_SAFE = 1
const CONTEXT_AMBIGUOUS = 2
const CONTEXT_DANGEROUS = 3

# Factor 2: action
const ACTION_WAIT = 1
const ACTION_APPROACH = 2
const ACTION_AVOID = 3
const ACTION_REPORT = 4

# Factor 3: threat
const THREAT_THREATENING = 1
const THREAT_NON_THREATENING = 2

# Factor 4: schema_mode
const SCHEMA_MODULAR = 1
const SCHEMA_INTEGRATED = 2

# Observation 1: context_cues
const CUE_SAFE = 1
const CUE_AMBIGUOUS = 2
const CUE_DANGER = 3

# Observation 2: outcome
const OUTCOME_NEUTRAL = 1
const OUTCOME_HARM = 2

# Observation 3: proprioception (same as action indices)
const PROPRIO_WAIT = 1
const PROPRIO_APPROACH = 2
const PROPRIO_AVOID = 3
const PROPRIO_REPORT = 4

# Observation 4: metacognition
const META_INACCESSIBLE = 1
const META_ACCESSIBLE = 2

# Policy indices
const POLICY_WAIT = 1      # [1,1,1] wait-wait-wait
const POLICY_APPROACH = 2  # [1,2,2] wait-approach-approach
const POLICY_AVOID = 3     # [1,3,3] wait-avoid-avoid
const POLICY_REPORT = 4    # [1,4,4] wait-report-report

# B4 control indices
const B4_NO_INTERVENTION = 1
const B4_DISCOVERY = 2

# Condition IDs
const CONDITION_BASELINE = 1
const CONDITION_CBT = 2
const CONDITION_CT = 3
const CONDITION_CT_DANGEROUS = 4
```

### Factor Details

**f1: context** (exogenous, uncontrollable)
- Index 1: safe - No threat cues present
- Index 2: ambiguous - Mixed cues
- Index 3: dangerous - Clear threat cues present

**f2: action** (controllable)
- Index 1: wait - No action taken
- Index 2: approach - Move toward stimulus
- Index 3: avoid - Move away from stimulus
- Index 4: report - Verbal report of schema (only available when integrated)

**f3: threat** (inferred, learnable)
- Index 1: threatening - Stimulus poses danger
- Index 2: non-threatening - Stimulus is safe

**f4: schema_mode** (therapist-controlled)
- Index 1: modular - Schema operates context-blind; agent cannot report it
- Index 2: integrated - Schema is context-sensitive; agent can report and revise

## 4) Outcome Modalities (Ng = 4)

| Modality | Outcomes | Description |
|----------|----------|-------------|
| m1: context_cues | 3 | Environmental observations: {safe_cue, ambiguous_cue, danger_cue} |
| m2: outcome | 2 | Consequence of action: {neutral, harm} |
| m3: proprioception | 4 | Agent's own action: {wait, approach, avoid, report} |
| m4: metacognition | 2 | Schema awareness: {inaccessible, accessible} |

**Dimensions:** No = (3, 2, 4, 2)

## 5) Generative Model Components - Full Specification

### A (Likelihood) - P(o|s)

All A matrices have shape (No, Ns1, Ns2, Ns3, Ns4) where:
- Ns1 = 3 (context: safe=1, ambiguous=2, dangerous=3)
- Ns2 = 4 (action: wait=1, approach=2, avoid=3, report=4)
- Ns3 = 2 (threat: threatening=1, non-threatening=2)
- Ns4 = 2 (schema_mode: modular=1, integrated=2)

**A1: context_cues** - Shape: (3, 3, 4, 2, 2)

Observation outcomes: safe_cue=1, ambiguous_cue=2, danger_cue=3

Depends on f1 (context) and f4 (schema_mode). Independent of f2, f3.

```julia
A1 = zeros(3, 3, 4, 2, 2)

# When modular (f4=1): uniform distribution - agent cannot process context cues
# P(any_cue | any_context, any_action, any_threat, modular) = 1/3
for s1 in 1:3, s2 in 1:4, s3 in 1:2
    A1[:, s1, s2, s3, 1] .= 1/3
end

# When integrated (f4=2): deterministic mapping from context
# P(cue=context | context, any_action, any_threat, integrated) = 1
for s1 in 1:3, s2 in 1:4, s3 in 1:2
    A1[s1, s1, s2, s3, 2] = 1.0  # Diagonal: observation matches context
end
```

**A2: outcome** - Shape: (2, 3, 4, 2, 2)

Observation outcomes: neutral=1, harm=2

**Complete probability table (all 48 state combinations):**

| context | action | threat | schema_mode | P(neutral) | P(harm) |
|---------|--------|--------|-------------|------------|---------|
| safe | wait | threatening | modular | 1.0 | 0.0 |
| safe | wait | threatening | integrated | 1.0 | 0.0 |
| safe | wait | non-threatening | modular | 1.0 | 0.0 |
| safe | wait | non-threatening | integrated | 1.0 | 0.0 |
| safe | approach | threatening | modular | 0.95 | 0.05 |
| safe | approach | threatening | integrated | 0.95 | 0.05 |
| safe | approach | non-threatening | modular | 0.95 | 0.05 |
| safe | approach | non-threatening | integrated | 0.95 | 0.05 |
| safe | avoid | threatening | modular | 1.0 | 0.0 |
| safe | avoid | threatening | integrated | 1.0 | 0.0 |
| safe | avoid | non-threatening | modular | 1.0 | 0.0 |
| safe | avoid | non-threatening | integrated | 1.0 | 0.0 |
| safe | report | threatening | modular | 1.0 | 0.0 |
| safe | report | threatening | integrated | 1.0 | 0.0 |
| safe | report | non-threatening | modular | 1.0 | 0.0 |
| safe | report | non-threatening | integrated | 1.0 | 0.0 |
| ambiguous | wait | threatening | modular | 1.0 | 0.0 |
| ambiguous | wait | threatening | integrated | 1.0 | 0.0 |
| ambiguous | wait | non-threatening | modular | 1.0 | 0.0 |
| ambiguous | wait | non-threatening | integrated | 1.0 | 0.0 |
| ambiguous | approach | threatening | modular | 0.7 | 0.3 |
| ambiguous | approach | threatening | integrated | 0.7 | 0.3 |
| ambiguous | approach | non-threatening | modular | 0.9 | 0.1 |
| ambiguous | approach | non-threatening | integrated | 0.9 | 0.1 |
| ambiguous | avoid | threatening | modular | 1.0 | 0.0 |
| ambiguous | avoid | threatening | integrated | 1.0 | 0.0 |
| ambiguous | avoid | non-threatening | modular | 1.0 | 0.0 |
| ambiguous | avoid | non-threatening | integrated | 1.0 | 0.0 |
| ambiguous | report | threatening | modular | 1.0 | 0.0 |
| ambiguous | report | threatening | integrated | 1.0 | 0.0 |
| ambiguous | report | non-threatening | modular | 1.0 | 0.0 |
| ambiguous | report | non-threatening | integrated | 1.0 | 0.0 |
| dangerous | wait | threatening | modular | 1.0 | 0.0 |
| dangerous | wait | threatening | integrated | 1.0 | 0.0 |
| dangerous | wait | non-threatening | modular | 1.0 | 0.0 |
| dangerous | wait | non-threatening | integrated | 1.0 | 0.0 |
| dangerous | approach | threatening | modular | 0.1 | 0.9 |
| dangerous | approach | threatening | integrated | 0.1 | 0.9 |
| dangerous | approach | non-threatening | modular | 0.5 | 0.5 |
| dangerous | approach | non-threatening | integrated | 0.5 | 0.5 |
| dangerous | avoid | threatening | modular | 1.0 | 0.0 |
| dangerous | avoid | threatening | integrated | 1.0 | 0.0 |
| dangerous | avoid | non-threatening | modular | 1.0 | 0.0 |
| dangerous | avoid | non-threatening | integrated | 1.0 | 0.0 |
| dangerous | report | threatening | modular | 1.0 | 0.0 |
| dangerous | report | threatening | integrated | 1.0 | 0.0 |
| dangerous | report | non-threatening | modular | 1.0 | 0.0 |
| dangerous | report | non-threatening | integrated | 1.0 | 0.0 |

```julia
A2 = zeros(2, 3, 4, 2, 2)

# Default: all actions except approach are safe
A2[1, :, :, :, :] .= 1.0  # P(neutral) = 1.0 default

# Override for approach action (s2=2) based on context and threat
# Safe context (s1=1): low harm regardless of threat
A2[1, 1, 2, :, :] .= 0.95; A2[2, 1, 2, :, :] .= 0.05

# Ambiguous context (s1=2): harm depends on threat
A2[1, 2, 2, 1, :] .= 0.7; A2[2, 2, 2, 1, :] .= 0.3   # threatening
A2[1, 2, 2, 2, :] .= 0.9; A2[2, 2, 2, 2, :] .= 0.1   # non-threatening

# Dangerous context (s1=3): harm depends on threat
A2[1, 3, 2, 1, :] .= 0.1; A2[2, 3, 2, 1, :] .= 0.9   # threatening
A2[1, 3, 2, 2, :] .= 0.5; A2[2, 3, 2, 2, :] .= 0.5   # non-threatening
```

**A3: proprioception** - Shape: (4, 3, 4, 2, 2)

Observation outcomes: wait=1, approach=2, avoid=3, report=4

Deterministic identity mapping from f2 (action). Independent of f1, f3, f4.

```julia
A3 = zeros(4, 3, 4, 2, 2)

# For each state combination, P(o=action | action) = 1
for s1 in 1:3, s2 in 1:4, s3 in 1:2, s4 in 1:2
    A3[s2, s1, s2, s3, s4] = 1.0  # Observation matches action state
end

# Verification: A3[:, s1, s2, s3, s4] should be one-hot at index s2
```

**A4: metacognition** - Shape: (2, 3, 4, 2, 2)

Observation outcomes: inaccessible=1, accessible=2

Deterministic mapping from f4 (schema_mode). Independent of f1, f2, f3.

```julia
A4 = zeros(2, 3, 4, 2, 2)

# For each state combination:
for s1 in 1:3, s2 in 1:4, s3 in 1:2
    # When modular (s4=1): always observe inaccessible
    A4[1, s1, s2, s3, 1] = 1.0  # P(inaccessible | modular) = 1
    A4[2, s1, s2, s3, 1] = 0.0  # P(accessible | modular) = 0

    # When integrated (s4=2): always observe accessible
    A4[1, s1, s2, s3, 2] = 0.0  # P(inaccessible | integrated) = 0
    A4[2, s1, s2, s3, 2] = 1.0  # P(accessible | integrated) = 1
end
```

### B (Transitions) - P(s'|s,a)

**B1: context** - Shape: (3, 3, 1)

Context is exogenous - set by environment, does not change within trial.
Single "null" control state (no agent control).

```julia
B1 = zeros(3, 3, 1)
B1[:, :, 1] = I(3)  # Identity: context persists
```

**B2: action** - Shape: (4, 4, 4)

Agent-controlled transitions. Control index = target action.

```julia
B2 = zeros(4, 4, 4)
for target_action in 1:4
    B2[target_action, :, target_action] .= 1.0  # Deterministic transition to target
end
```

**B3: threat** - Shape: (2, 2, 1)

Threat state is static within trial (reflects prior belief, not updated mid-trial).
Single "null" control state.

```julia
B3 = zeros(2, 2, 1)
B3[:, :, 1] = I(2)  # Identity: threat belief persists within trial
```

**B4: schema_mode** - Shape: (2, 2, 2)

Therapist-controlled. Two control states: no_intervention, discovery.
Transition is **deterministic** and **irreversible** (integrated → integrated).

```julia
B4 = zeros(2, 2, 2)

# Control 1: no_intervention - identity
B4[:, :, 1] = I(2)

# Control 2: discovery - forces integrated state
B4[2, :, 2] .= 1.0  # Both modular and integrated → integrated
# Note: B4[1, :, 2] = 0 (never transitions back to modular)
```

### C (Preferences) - log P(o)

Preferences are log-probabilities (higher = more preferred).

```julia
# C1: context_cues - neutral (no preference for observing any context)
C1 = zeros(3)

# C2: outcome - strong aversion to harm
C2 = [2.0, -4.0]  # [neutral=+2, harm=-4]

# C3: proprioception - slight preference for action over waiting
C3 = [0.0, 0.5, 0.5, 0.5]  # [wait=0, approach=+0.5, avoid=+0.5, report=+0.5]

# C4: metacognition - neutral (no preference for accessibility)
C4 = [0.0, 0.0]
```

### D (Priors) - P(s, t=1)

Initial state distributions at trial start. These are **Dirichlet concentration parameters** for learning.

```julia
# D1: context - set by experimental condition
# Represented as concentration parameters (sum = confidence)
D1_safe = [10.0, 0.1, 0.1]       # Strong prior: safe
D1_ambiguous = [0.1, 10.0, 0.1] # Strong prior: ambiguous
D1_dangerous = [0.1, 0.1, 10.0] # Strong prior: dangerous

# D2: action - start in wait state
D2 = [10.0, 0.1, 0.1, 0.1]  # Strong prior: wait

# D3: threat - THE SCHEMA (learnable)
# Initial: strong belief that stimulus is threatening
D3_initial = [9.0, 1.0]  # 90% threatening prior
# Concentration sum = 10 (moderate confidence, can be updated)

# D4: schema_mode - start modular
D4 = [10.0, 0.1]  # Strong prior: modular
```

## 6) Policy Set and Temporal Structure

### Trial Structure
- **T = 3** timesteps per trial
- **N_trials = 100** per experimental condition

### Timestep Semantics
| Timestep | Agent Action | Observations Received |
|----------|--------------|----------------------|
| t=1 | None (observe) | context_cues, metacognition |
| t=2 | Select action | proprioception |
| t=3 | None (outcome) | outcome |

### Policy Definition

A **policy** π is a sequence of control states for each factor across timesteps.

**Controllable factors:** f2 (action), f4 (schema_mode - therapist only)

**Policy horizon:** τ = T = 3 (plan entire trial)

**Allowable action sequences for agent (f2):**

```julia
# Agent policies: (t=1, t=2, t=3) for f2
# t=1: must be wait (observe first)
# t=2: choose action
# t=3: maintain action (no mid-trial switching)

policies_f2 = [
    [1, 1, 1],  # wait-wait-wait (passive)
    [1, 2, 2],  # wait-approach-approach
    [1, 3, 3],  # wait-avoid-avoid
    [1, 4, 4],  # wait-report-report (only effective when integrated)
]

num_policies = 4
```

### Context-Blind Policy Evaluation (Key Mechanism)

**Implementation:** When f4 = modular, EFE calculation **marginalizes over f1** rather than conditioning on observed context.

```julia
function compute_EFE(policy, beliefs, schema_mode)
    if schema_mode == :modular
        # Marginalize over f1 (context) - context-blind
        # EFE = Σ_f1 P(f1) * EFE(policy | f1)
        # Since A1 is uniform, agent has no information about context
        # Result: policy selection ignores context, defaults to protective (avoid)
        return compute_EFE_marginalized(policy, beliefs, marginalize_over=[1])
    else
        # Condition on inferred f1 - context-sensitive
        return compute_EFE_conditioned(policy, beliefs)
    end
end
```

**Mathematical formulation:**

Modular mode EFE:
```
G(π) = Σ_τ Σ_{s1} P(s1) [ E_Q[ln Q(s|π) - ln P(o,s|π)] ]
```

Integrated mode EFE:
```
G(π) = Σ_τ [ E_Q[ln Q(s|π) - ln P(o,s|π)] | s1 = inferred_context ]
```

## 7) Learning Rules - Full Specification

### What is Learned

| Parameter | Learned? | When? | Rate |
|-----------|----------|-------|------|
| A matrices | No | Never | - |
| B matrices | No | Never | - |
| C preferences | No | Never | - |
| D1 (context) | No | Never | - |
| D2 (action) | No | Never | - |
| **D3 (threat)** | **Yes** | When integrated | η |
| D4 (schema_mode) | No | Never | - |

### Learning Rate Schedule

**Base learning rate:** η_base = 0.5

**State-conditional learning:**
```julia
function get_learning_rate(schema_mode)
    if schema_mode == :modular
        return 0.0  # No learning - schema protected
    else  # integrated
        return η_base  # Learning enabled
    end
end
```

### Dirichlet Update Rule

D3 is updated using Dirichlet-categorical conjugate learning:

```julia
function update_D3!(D3, posterior_s3, η)
    # posterior_s3: inferred threat state from trial [P(threatening), P(non-threatening)]
    # η: learning rate (0 when modular, η_base when integrated)

    if η > 0
        # Dirichlet update: add scaled posterior to concentration parameters
        D3 .+= η * posterior_s3
    end
    # When η = 0, D3 unchanged (schema protected)
end
```

### Initial Concentration Parameters

```julia
# D3 initial concentrations (the "schema")
D3_initial = [9.0, 1.0]  # Sum = 10, 90% threatening

# After many safe trials with learning (CBT):
# D3 ≈ [9.0, 1.0 + n*η*posterior_safe] → shifts toward non-threatening

# After CT discovery (no learning needed):
# D3 ≈ [9.0, 1.0] unchanged, but behavior changes via context-sensitivity
```

### Learning Disabled Enforcement

**Mechanism:** Set η = 0 when schema_mode = modular

**Verification:**
```julia
@test D3_after_modular_trials == D3_initial  # No change
@test D3_after_integrated_trials != D3_initial  # Change occurred
```

## 8) Therapist Intervention Protocol

### Intervention Type
**External state override** (not agent control input)

The therapist directly sets the schema_mode state, bypassing the agent's B4 transitions.

### Implementation

```julia
struct TherapistIntervention
    trial::Int           # Trial number to intervene
    target_state::Int    # 2 = integrated (Discovery)
end

function apply_intervention!(agent_state, intervention, current_trial)
    if current_trial == intervention.trial
        # Direct state override - deterministic, immediate
        agent_state[:schema_mode] = intervention.target_state
    end
end
```

### Intervention Timing by Condition (Explicit)

| Condition ID | Name | Context (D1) | Initial f4 | Intervention Trial | Target f4 | Learning |
|--------------|------|--------------|------------|-------------------|-----------|----------|
| 1 | Baseline | safe | SCHEMA_MODULAR (1) | None | - | η=0 always |
| 2 | CBT | safe | SCHEMA_INTEGRATED (2) | None (start integrated) | - | η=0.5 always |
| 3 | CT | safe | SCHEMA_MODULAR (1) | 51 | SCHEMA_INTEGRATED (2) | η=0→0.5 at t=51 |
| 4 | CT-dangerous | dangerous | SCHEMA_MODULAR (1) | 51 | SCHEMA_INTEGRATED (2) | η=0→0.5 at t=51 |

**Intervention Timing Within Trial:**
- Intervention is applied **at the START of the intervention trial** (before t=1)
- This means the agent observes context_cues at t=1 already in integrated mode
- The intervention persists for all subsequent trials

**Intervention Implementation:**
```julia
function run_trial(agent, trial_num, interventions)
    # Apply any interventions BEFORE the trial starts
    for interv in interventions
        if trial_num == interv.trial
            agent.state[interv.factor] = interv.target
        end
    end

    # Now run the trial: t=1 observe, t=2 act, t=3 outcome
    # ...
end

function run_simulation(condition_id::Int)
    # Set initial states based on condition
    if condition_id == CONDITION_BASELINE
        D1 = D1_safe
        initial_f4 = SCHEMA_MODULAR
        interventions = []
    elseif condition_id == CONDITION_CBT
        D1 = D1_safe
        initial_f4 = SCHEMA_INTEGRATED
        interventions = []
    elseif condition_id == CONDITION_CT
        D1 = D1_safe
        initial_f4 = SCHEMA_MODULAR
        interventions = [TherapistIntervention(trial=51, factor=4, target=SCHEMA_INTEGRATED)]
    elseif condition_id == CONDITION_CT_DANGEROUS
        D1 = D1_dangerous
        initial_f4 = SCHEMA_MODULAR
        interventions = [TherapistIntervention(trial=51, factor=4, target=SCHEMA_INTEGRATED)]
    end
    # ... run trial loop
end
```

### Irreversibility
Once f4 = integrated, it **cannot** return to modular within the simulation.
This models the clinical observation that explicit awareness, once achieved, persists.

## 9) Simulation Protocol - Detailed

### Condition 1: Baseline (No Therapy)

```julia
baseline_config = SimulationConfig(
    n_trials = 100,
    context = :safe,           # D1 = D1_safe
    initial_schema_mode = :modular,
    interventions = [],        # No intervention
    learning_enabled = false,  # η = 0 throughout
)
```

**Expected outcomes:**
- P(avoid) ≈ 1.0 for all 100 trials
- D3 unchanged from [9.0, 1.0]
- Agent never processes context cues

### Condition 2: CBT Exposure (Smith 2021 style)

```julia
cbt_config = SimulationConfig(
    n_trials = 100,
    context = :safe,
    initial_schema_mode = :integrated,  # Start integrated
    interventions = [],
    learning_enabled = true,   # η = η_base throughout
)
```

**Expected outcomes:**
- P(avoid) starts high, gradually decreases
- P(avoid) crosses 0.5 around trial 30-50
- D3 shifts from [9.0, 1.0] toward [9.0, ~5.0] by trial 100
- Sigmoid-shaped learning curve

### Condition 3: Coherence Therapy (Discovery)

```julia
ct_config = SimulationConfig(
    n_trials = 100,
    context = :safe,
    initial_schema_mode = :modular,
    interventions = [
        TherapistIntervention(trial=51, target_state=:integrated)
    ],
    learning_enabled = true,  # η = 0 when modular, η_base when integrated
)
```

**Expected outcomes:**
- Trials 1-50: P(avoid) ≈ 1.0, D3 unchanged
- Trial 51: P(avoid) drops sharply (step function)
- Trials 51-100: P(avoid) ≈ 0.0 (context-appropriate approach)
- D3 may shift slightly but NOT required for resolution

### Condition 4: CT without Context Change

```julia
ct_dangerous_config = SimulationConfig(
    n_trials = 100,
    context = :dangerous,  # Changed from safe
    initial_schema_mode = :modular,
    interventions = [
        TherapistIntervention(trial=51, target_state=:integrated)
    ],
    learning_enabled = true,
)
```

**Expected outcomes:**
- Trials 1-50: P(avoid) ≈ 1.0 (context-blind avoidance)
- Trial 51: P(avoid) remains ≈ 1.0 (context-appropriate avoidance)
- Trials 51-100: P(avoid) ≈ 1.0 (no behavior change - correct response to danger)
- D3 may shift toward threatening (reinforced by dangerous context)

## 10) Simulation Parameters

### Replication and Randomization

```julia
using Random  # Julia stdlib

# Number of independent simulation runs per condition
N_REPLICATIONS = 50

# Random seed for reproducibility
BASE_SEED = 42

# RNG algorithm: Xoshiro256++ (Julia default as of 1.7+)
# Seeds for each replication - deterministic function
function get_seed(condition_id::Int, replication_id::Int)::Int
    return BASE_SEED + condition_id * 1000 + replication_id
end

# Initialize RNG for a replication
function init_rng(condition_id::Int, replication_id::Int)
    seed = get_seed(condition_id, replication_id)
    return Random.Xoshiro(seed)
end

# Condition IDs
CONDITION_BASELINE = 1
CONDITION_CBT = 2
CONDITION_CT = 3
CONDITION_CT_DANGEROUS = 4
```

### Trial Parameters

```julia
N_TRIALS = 100          # Trials per condition per replication
T = 3                   # Timesteps per trial
INTERVENTION_TRIAL = 51 # Trial when therapist intervenes (CT conditions)
```

### Agent Hyperparameters

```julia
GAMMA = 4.0      # Policy precision (inverse temperature for softmax)
ALPHA = 8.0      # Action precision
ETA_BASE = 0.5   # Learning rate when enabled
ETA_MODULAR = 0.0 # Learning rate when modular (disabled)
```

## 11) Verification Criteria - Quantitative Definitions

### Primary Metric: P(avoid) Trajectory

**Definition:** P(avoid) = probability of selecting avoid policy at each trial

```julia
function compute_p_avoid(policy_posterior)
    # policy_posterior: Vector of length 4 (probabilities for each policy)
    # Policy indices: 1=wait, 2=approach, 3=avoid, 4=report
    return policy_posterior[3]
end

# Aggregate across replications
function aggregate_p_avoid(results::Vector{SimulationResult})
    # results: one per replication
    # Returns: (mean_trajectory, std_trajectory, ci_lower, ci_upper)
    n_trials = length(results[1].p_avoid)
    n_reps = length(results)

    trajectories = hcat([r.p_avoid for r in results]...)  # 100 × 50 matrix

    mean_traj = vec(mean(trajectories, dims=2))
    std_traj = vec(std(trajectories, dims=2))
    ci_lower = mean_traj .- 1.96 * std_traj / sqrt(n_reps)
    ci_upper = mean_traj .+ 1.96 * std_traj / sqrt(n_reps)

    return (mean=mean_traj, std=std_traj, ci_lower=ci_lower, ci_upper=ci_upper)
end
```

### Change-Point Detection (Operational Definition)

**Algorithm:** PELT (Pruned Exact Linear Time) change-point detection

**Parameters:**
```julia
const PELT_PENALTY = 3.0 * log(N_TRIALS)  # BIC-like penalty
const PELT_COST = :normal_mean            # Normal mean change cost function
const CHANGE_POINT_WINDOW = 3             # Acceptable deviation from intervention trial
const MIN_CHANGE_MAGNITUDE = 0.7          # Minimum Δ for step function
const MAX_CHANGE_WIDTH = 5                # Maximum trials for transition
```

```julia
using Changepoints  # Julia package (v0.4+)

function detect_change_point(trajectory::Vector{Float64})
    # Detect single change-point using PELT algorithm
    # Returns: (change_trial, magnitude, width)

    # Run PELT with normal mean cost function
    cpts = pelt(trajectory, NormalMeanChange())

    if isempty(cpts)
        return (trial=nothing, magnitude=0.0, width=Inf)
    end

    # Find largest change
    best_cpt = cpts[1]
    pre_mean = mean(trajectory[1:best_cpt])
    post_mean = mean(trajectory[best_cpt+1:end])
    magnitude = abs(post_mean - pre_mean)

    # Calculate width: trials to go from 10% to 90% of change
    threshold_low = pre_mean + 0.1 * (post_mean - pre_mean)
    threshold_high = pre_mean + 0.9 * (post_mean - pre_mean)
    width = count(t -> threshold_low <= trajectory[t] <= threshold_high, 1:length(trajectory))

    return (trial=best_cpt, magnitude=magnitude, width=width)
end
```

**Step function criteria (CT):**
- Change-point detected within ±3 trials of intervention (trial 48-54)
- Magnitude Δ > 0.7 (change from ~1.0 to ~0.3 or less)
- Width < 5 trials (rapid transition)

**No change-point criteria (Baseline, CT-dangerous):**
- No change-point detected OR magnitude < 0.1

### Sigmoid Fit (Operational Definition)

**Algorithm:** Nonlinear least squares logistic regression

**Parameters:**
```julia
const SIGMOID_MIN_R2 = 0.9           # Minimum R² for CBT
const SIGMOID_MAX_R2_FOR_STEP = 0.5  # Maximum R² for CT (step doesn't fit sigmoid)
const SIGMOID_T_HALF_MIN = 20        # Minimum midpoint trial
const SIGMOID_T_HALF_MAX = 80        # Maximum midpoint trial

# Initial parameter bounds for fitting
const SIGMOID_P0 = [0.1, 0.9, -0.1, 50.0]  # [L, U, k, t_half]
const SIGMOID_LOWER = [0.0, 0.5, -1.0, 10.0]
const SIGMOID_UPPER = [0.5, 1.0, 0.0, 90.0]
```

```julia
using LsqFit  # Julia package (v0.13+)

function fit_sigmoid(trajectory::Vector{Float64}, trials::Vector{Int})
    # Fit logistic function: P(avoid) = L + (U-L) / (1 + exp(-k*(t - t_half)))
    # L = lower asymptote, U = upper asymptote, k = steepness, t_half = midpoint

    # Model function
    @. model(t, p) = p[1] + (p[2] - p[1]) / (1 + exp(-p[3] * (t - p[4])))

    # Initial parameters: [L=0.1, U=0.9, k=-0.1, t_half=50]
    p0 = [0.1, 0.9, -0.1, 50.0]

    # Fit
    fit = curve_fit(model, Float64.(trials), trajectory, p0)

    # Compute R²
    y_pred = model(Float64.(trials), fit.param)
    ss_res = sum((trajectory .- y_pred).^2)
    ss_tot = sum((trajectory .- mean(trajectory)).^2)
    r_squared = 1 - ss_res / ss_tot

    return (params=fit.param, r_squared=r_squared, predictions=y_pred)
end
```

**Sigmoid criteria (CBT):**
- R² > 0.9 for logistic fit
- Estimated k < 0 (decreasing function)
- t_half between trials 20-80

**Non-sigmoid criteria (CT):**
- R² < 0.5 (logistic does not fit step function well)

### D3 Belief Change Calculation

```julia
function compute_d3_change(d3_initial::Vector{Float64}, d3_final::Vector{Float64})
    # D3 = [threatening_concentration, non_threatening_concentration]
    # Compute normalized change in threatening belief

    p_threat_initial = d3_initial[1] / sum(d3_initial)
    p_threat_final = d3_final[1] / sum(d3_final)

    return abs(p_threat_final - p_threat_initial)
end
```

### Effect Size Calculations

**Cohen's d (within-condition pre/post comparison):**

```julia
function cohens_d(pre::Vector{Float64}, post::Vector{Float64})
    # pre: P(avoid) values for trials 1-50 across replications
    # post: P(avoid) values for trials 51-100 across replications

    mean_pre = mean(pre)
    mean_post = mean(post)
    pooled_std = sqrt((var(pre) + var(post)) / 2)

    return (mean_pre - mean_post) / pooled_std
end

# Usage for CT condition:
# pre = [mean(r.p_avoid[1:50]) for r in ct_results]
# post = [mean(r.p_avoid[51:100]) for r in ct_results]
# d = cohens_d(pre, post)
```

**Eta-squared (between-condition ANOVA):**

```julia
function eta_squared(group_means::Vector{Float64}, group_vars::Vector{Float64}, group_ns::Vector{Int})
    # One-way ANOVA effect size

    grand_mean = mean(group_means)
    ss_between = sum(group_ns .* (group_means .- grand_mean).^2)
    ss_within = sum((group_ns .- 1) .* group_vars)
    ss_total = ss_between + ss_within

    return ss_between / ss_total
end

# Groups: Baseline, CBT, CT, CT-dangerous
# Computed on mean P(avoid) trials 51-100 per replication
```

**Bayes Factor (CT vs CBT curve shape):**

**Parameters:**
```julia
const BF_THRESHOLD = 10.0  # Strong evidence threshold
# BIC formula: BIC = n * ln(SS_res/n) + k * ln(n)
# where n = number of observations, k = number of parameters
# Step model: k = 2 (pre-mean, post-mean)
# Sigmoid model: k = 4 (L, U, k, t_half)
```

```julia
function bayes_factor_curve_shape(ct_trajectories, cbt_trajectories)
    # Compare step-function model vs sigmoid model using BIC approximation

    # Fit both models to CT data
    ct_step_bic = fit_step_model_bic(ct_trajectories)
    ct_sigmoid_bic = fit_sigmoid_model_bic(ct_trajectories)

    # Fit both models to CBT data
    cbt_step_bic = fit_step_model_bic(cbt_trajectories)
    cbt_sigmoid_bic = fit_sigmoid_model_bic(cbt_trajectories)

    # BIC difference → approximate Bayes Factor
    # BF ≈ exp((BIC_sigmoid - BIC_step) / 2) for CT (should favor step)
    bf_ct_favors_step = exp((ct_sigmoid_bic - ct_step_bic) / 2)

    # BF ≈ exp((BIC_step - BIC_sigmoid) / 2) for CBT (should favor sigmoid)
    bf_cbt_favors_sigmoid = exp((cbt_step_bic - cbt_sigmoid_bic) / 2)

    return (ct_step_bf=bf_ct_favors_step, cbt_sigmoid_bf=bf_cbt_favors_sigmoid)
end
```

### Quantitative Acceptance Thresholds

**Aggregation Method:** All metrics computed on MEAN trajectory across 50 replications, unless noted.

| Metric | Aggregation | Baseline | CBT | CT | CT-dangerous |
|--------|-------------|----------|-----|-----|--------------|
| P(avoid) mean trials 1-50 | Mean of means | > 0.9 | > 0.7 | > 0.9 | > 0.9 |
| P(avoid) mean trials 51-100 | Mean of means | > 0.9 | < 0.3 | < 0.3 | > 0.9 |
| D3 belief change | Mean across reps | < 0.05 | > 0.3 | < 0.15 | - |
| Change-point magnitude | On mean traj | < 0.1 | < 0.3 | > 0.7 | < 0.1 |
| Change-point within ±3 of trial 51 | On mean traj | N/A | N/A | Yes | N/A |
| Sigmoid R² | On mean traj | N/A | > 0.9 | < 0.5 | N/A |
| Cohen's d (pre/post) | Per-rep means | < 0.2 | > 1.0 | > 2.0 | < 0.2 |

### Statistical Tests (Complete)

```julia
function run_all_tests(baseline, cbt, ct, ct_dangerous)
    results = Dict()

    # Aggregate trajectories
    base_agg = aggregate_p_avoid(baseline)
    cbt_agg = aggregate_p_avoid(cbt)
    ct_agg = aggregate_p_avoid(ct)
    ctd_agg = aggregate_p_avoid(ct_dangerous)

    # Test 1: Baseline maintains avoidance
    results[:baseline_maintains] = mean(base_agg.mean[51:100]) > 0.9

    # Test 2: CBT shows gradual resolution
    cbt_sigmoid = fit_sigmoid(cbt_agg.mean, 1:100)
    results[:cbt_sigmoid_r2] = cbt_sigmoid.r_squared > 0.9
    results[:cbt_resolves] = mean(cbt_agg.mean[51:100]) < 0.3

    # Test 3: CT shows step function at intervention
    ct_cpt = detect_change_point(ct_agg.mean)
    results[:ct_step_magnitude] = ct_cpt.magnitude > 0.7
    results[:ct_step_timing] = 48 <= ct_cpt.trial <= 54
    results[:ct_step_width] = ct_cpt.width < 5

    # Test 4: CT resolves without belief change
    ct_d3_changes = [compute_d3_change(r.d3_initial, r.d3_final) for r in ct]
    results[:ct_minimal_belief_change] = mean(ct_d3_changes) < 0.15

    # Test 5: CT-dangerous maintains avoidance
    results[:ctd_maintains] = mean(ctd_agg.mean[51:100]) > 0.9
    ctd_cpt = detect_change_point(ctd_agg.mean)
    results[:ctd_no_change] = ctd_cpt.magnitude < 0.1

    # Test 6: Modular blocks learning (baseline D3 unchanged)
    base_d3_changes = [compute_d3_change(r.d3_initial, r.d3_final) for r in baseline]
    results[:modular_blocks_learning] = mean(base_d3_changes) < 0.01

    # Test 7: Effect sizes
    ct_pre = [mean(r.p_avoid[1:50]) for r in ct]
    ct_post = [mean(r.p_avoid[51:100]) for r in ct]
    results[:ct_cohens_d] = cohens_d(ct_pre, ct_post) > 2.0

    # Test 8: Bayes factor for curve shape
    bf = bayes_factor_curve_shape(
        hcat([r.p_avoid for r in ct]...),
        hcat([r.p_avoid for r in cbt]...)
    )
    results[:ct_favors_step] = bf.ct_step_bf > 10
    results[:cbt_favors_sigmoid] = bf.cbt_sigmoid_bf > 10

    return results
end
```

### Pass/Fail Criteria

**PASS:** All tests return `true`
**FAIL:** Any test returns `false` - indicates model does not capture the predicted behavior

## 12) Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Implement state-conditional A matrix (A1 gated by f4)
- [ ] Implement state-conditional learning rate (η gated by f4)
- [ ] Implement therapist state override mechanism
- [ ] Implement context-blind EFE (marginalization over f1)

### Phase 2: Model Construction
- [ ] Build A matrices with exact values from spec
- [ ] Build B matrices with exact values from spec
- [ ] Build C preferences with exact values from spec
- [ ] Build D priors with exact values from spec
- [ ] Define policy set (4 policies)

### Phase 3: Simulation
- [ ] Implement trial loop with T=3 structure
- [ ] Implement intervention application
- [ ] Run 4 conditions × 100 trials
- [ ] Record P(avoid), D3 at each trial

### Phase 4: Verification
- [ ] Compute all metrics from Section 10
- [ ] Run statistical tests
- [ ] Generate comparison plots
- [ ] Document deviations from spec in learnings.md

## 13) Reference Files

| File | Purpose |
|------|---------|
| `paper.md` | Citation and theory summary |
| `model_design.md` | Alternative model candidates (historical) |
| `library_mapping.md` | Capability gaps in current library |
| `learnings.md` | Insights and deviations during implementation |
| `PLAN.md` | Progress tracking |
| `fnhum-16-955558.pdf` | Original paper |

### Existing Library References
- `src/models/AIFModel.jl` - Base active inference model
- `src/inference/policy_selection.jl` - EFE calculation
- `src/learning/dirichlet.jl` - Dirichlet parameter updates
- `paper_reproduction/smith_2021/` - CBT baseline comparison
