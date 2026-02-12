# Model Design (Smith 2021 / Spider Phobia)

This document encodes the **exact generative model structure** from the paper and reference implementation.

## 1) Dimensions
- **Hidden state factors (Nf = 3)**
  - Factor 1: `behavior` (Ns1 = 5): start, approach, avoid, freeze, interact
  - Factor 2: `spider_present` (Ns2 = 2): absent, present
  - Factor 3: `danger` (Ns3 = 2): dangerous, safe
- **Outcome modalities (Ng = 3)**
  - Modality 1: proprioception (behavior observation)
  - Modality 2: exteroception (spider presence observation)
  - Modality 3: interoception (harm/neutral outcome)
- **Trial length**: `T` (configurable, typically multi-timestep)

## 2) Labels / Ordering

### Behavior states (Factor 1)
1. start
2. approach
3. avoid
4. freeze
5. interact

### Spider presence (Factor 2)
1. absent
2. present

### Danger states (Factor 3)
1. dangerous
2. safe

## 3) A: Likelihoods

### Proprioception (A[1])
- Shape: (5, 5, 2, 2) = (behavior_obs, behavior, spider_present, danger)
- Identity mapping for behavior observation (agent sees own state).
- Independent of spider_present and danger.

### Exteroception (A[2])
- Shape: (2, 5, 2, 2) = (spider_obs, behavior, spider_present, danger)
- Deterministic mapping to spider_present state.
- Independent of behavior and danger.

### Interoception (A[3])
- Shape: (2, 5, 2, 2) = (harm_obs, behavior, spider_present, danger)
- Outcomes: 1=harm, 2=neutral
- Key mapping:
  - approach/interact + spider_present + dangerous => P(harm) high
  - avoid/freeze + any => P(harm) ~ 0 (neutral)
  - approach/interact + spider_present + safe => P(harm) ~ 0 (neutral)
  - no spider present => always neutral

## 4) B: Transitions

### Behavior (B[1])
- Shape: (5, 5, Na) where Na = number of actions
- Controllable by policy/action selection.
- Action k transitions to behavior state k.

### Spider Present (B[2])
- Shape: (2, 2, 1) - single "action" (uncontrollable)
- Identity matrix: spider presence stays constant.

### Danger (B[3])
- Shape: (2, 2, 1) - single "action" (uncontrollable)
- Identity matrix: danger state is static within trial.
- The agent infers this hidden state but cannot change it.

## 5) C: Preferences
- **Proprioception**: neutral (zeros).
- **Exteroception**: neutral (zeros).
- **Interoception**:
  - harm (outcome 1): negative preference (aversive)
  - neutral (outcome 2): positive or zero preference

## 6) D: Priors and Dirichlet beliefs

### Paper-matching priors (use_paper_priors=true)
- D{1} = start state (behavior starts at 1)
- D{2} = spider present (state 2, spider is present during exposure)
- D{3} = [45, 5] / 50 => P(dangerous) = 0.9, P(safe) = 0.1

### Dirichlet parameters (d)
- d{1}, d{2}: match D (not learned)
- d{3} = [45, 5] for danger factor
  - This gives initial P(safe) = 5/50 = 10%
  - Learning updates: d{3}[2] += eta * P(safe | observations)

## 7) Policies

### Exposure mode (therapist-guided)
- Single policy: always approach (action 1 for behavior factor).
- Simulates therapist encouraging patient to face fear.
- No policy selection via EFE (action is forced).

### Free choice mode
- Multiple policies available.
- EFE-based selection typically leads to avoidance (prior belief is dangerous).
- Without exposure mode, agent rarely approaches and doesn't learn.

## 8) Learning Configuration

### What is learned
- D[3] (danger beliefs): updated after each trial based on final posterior.
- A matrix: **not learned** in our implementation (see learnings.md for why).

### Learning rule
- Update pD[3] += eta * qs_final[3]
- Where qs_final is the posterior belief about danger after observing trial outcome.
- Uses FINAL beliefs (end of trial) because danger is static.

## 9) Precision Parameters
- gamma: policy precision (from AIFSettings).
- alpha: action selection precision (from AIFSettings).
- eta: learning rate for D updates (from AIFSettings).

## 10) Implementation Notes
- Environment tracks true danger state (spider_dangerous bool).
- SpiderEnvironment.current_state = [behavior, spider_present, danger].
- Initial state: [1, 2, 1 if dangerous else 2].
- Exposure trial forces approach action throughout.
