# Smith 2021 Task Spec (Spider Phobia / CBT Exposure Therapy)

Source paper: "Simulating the computational mechanisms of cognitive and behavioral psychotherapeutic interventions: Insights from active inference" (Scientific Reports, 2021).

Reference implementation: https://github.com/rssmith33/Simulating_Cognitive_Behavioral_Therapy

## 1) Task Overview
- Agent with spider phobia undergoes exposure therapy.
- Each trial: agent observes spider, chooses behavior, receives outcome.
- Through repeated exposure to a safe spider, agent learns P(safe) increases.
- Simulates how CBT exposure therapy works computationally.

## 2) Hidden State Factors (3 factors)
1. **Behavior** (5 states):
   - `start`: initial state
   - `approach`: move toward spider
   - `avoid`: move away from spider
   - `freeze`: stay still
   - `interact`: touch/engage with spider

2. **Spider Present** (2 states):
   - `absent`: no spider in environment
   - `present`: spider is visible

3. **Danger** (2 states):
   - `dangerous`: spider can cause harm
   - `safe`: spider cannot cause harm
   - This is the key hidden state the agent must infer.

## 3) Outcome Modalities
- **Proprioception**: agent observes own behavior state (deterministic).
- **Exteroception**: agent observes spider presence (deterministic when present).
- **Interoception**: agent observes harm/neutral outcome.
  - Harm only possible when interacting with dangerous spider.
  - Otherwise neutral.

## 4) Generative Model Components

### A (Likelihood)
- Maps hidden states to observations.
- Proprioception: identity mapping to behavior.
- Exteroception: identity mapping to spider presence.
- Interoception:
  - Approach/interact + dangerous spider = high P(harm).
  - All other combinations = neutral.

### B (Transitions)
- **Behavior factor**: controllable by agent (policy determines action).
- **Spider present factor**: fixed (identity matrix, spider stays present).
- **Danger factor**: fixed (identity matrix, danger state is static).

### C (Preferences)
- Agent prefers neutral outcomes over harm.
- Agent may have slight preference for avoidance (safety-seeking).

### D (Priors)
- **Behavior**: starts in `start` state.
- **Spider present**: present (exposure therapy context).
- **Danger**: initially strongly biased toward `dangerous` (P(dangerous) ~ 90%).
  - Paper uses d[3] = [45, 5] giving P(safe) = 5/50 = 10%.

## 5) Learning Protocol
- **Exposure mode**: Agent is forced to approach/interact (therapist guidance).
- **Learning target**: D[3] (danger beliefs).
- After each trial, update pD based on observed outcomes.
- Safe spider + no harm => P(safe) increases over trials.

## 6) Key Results to Replicate
- Initial P(safe) ~ 10%.
- After ~200 trials of exposure to safe spider: P(safe) ~ 81-90%.
- If spider is actually dangerous: P(safe) should decrease.

## 7) Exposure Therapy Mechanism
The model demonstrates why exposure therapy works:
1. Patient believes spider is dangerous (90% prior).
2. Avoidance provides no evidence (can't distinguish dangerous from safe).
3. Approach/interaction provides evidence:
   - If dangerous: harm observed => belief confirmed.
   - If safe: no harm => evidence accumulates that spider is safe.
4. Therapist guidance (exposure mode) forces approach, enabling learning.

## 8) Parameters from Implementation
- Trial length T: configurable (default in model.jl).
- Number of exposure trials: typically 200.
- Learning rate eta: from AIFSettings (default 1.0).
- Dirichlet prior d[3] = [45, 5] for danger factor (90% dangerous prior).

## 9) Evaluation Metrics
- P(safe) trajectory over trials.
- Convergence rate to high P(safe) for safe spider.
- Correct decrease in P(safe) for dangerous spider.
