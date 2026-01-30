# Library Mapping + Gaps (Smith 2021 / Spider Phobia)

This file maps paper requirements to current library capabilities and notes gaps.

## 1) Core Task Requirements (from paper)
- Agent with initial belief that spider is dangerous (~90%).
- Exposure therapy: forced approach to spider over multiple trials.
- Learning: D matrix updates for danger beliefs.
- Safe spider exposure => P(safe) increases to ~81-90%.
- Dangerous spider exposure => P(safe) decreases.

## 2) Mapping to Our Library

### Trial structure
- Supported via `AIFModel(...; trial_length=T)`.
- Multi-timestep trials with action selection at each step.

### Hidden factors
- Factor 1 (behavior): 5 states, controllable.
- Factor 2 (spider_present): 2 states, uncontrollable (identity B).
- Factor 3 (danger): 2 states, uncontrollable (identity B), **learned**.

### Outcomes
- Modality 1: proprioception (behavior observation).
- Modality 2: exteroception (spider presence).
- Modality 3: interoception (harm/neutral outcome).

### A matrices
- Built via `build_model()` from `model.jl`.
- Paper-specific feature mappings encoded.

### B matrices
- Behavior: action-controlled transitions.
- Spider present: identity matrix.
- Danger: identity matrix.

### C matrix
- Preferences over interoception (harm aversion).
- Other modalities neutral.

### D matrix
- Paper priors: d[3] = [45, 5] for 90% dangerous prior.
- Learned via `update_pD_final!()`.

### Learning
- `update_pD_final!()`: Updates pD based on **final** beliefs (critical for static states).
- This is different from standard update_pD which uses initial beliefs.

### Exposure mode
- `run_exposure_trial!()`: Forces approach policy.
- Bypasses EFE-based policy selection.
- Still performs state inference and learning.

## 3) Key Implementation Components

### SpiderEnvironment
- Tracks true danger state via `spider_dangerous` bool.
- Generates observations based on A matrices.
- Steps state based on B matrices.

### run_spider_aif_therapy()
- Main simulation function.
- Parameters: n_trials, spider_dangerous, params, settings.
- Returns: Vector of P(safe) after each trial.

### run_exposure_trial!()
- Single trial with forced approach.
- Performs state inference and D learning.
- Does NOT learn A matrix (see learnings for rationale).

## 4) Gaps / Missing Features
- None identified for core reproduction.
- A matrix learning disabled intentionally (degrades model).

## 5) Reference Implementation Mapping

| Paper/Reference | Our Library |
|-----------------|-------------|
| rssmith33/Simulating_Cognitive_Behavioral_Therapy | spider_model.jl |
| Initial danger prior 90% | d[3] = [45, 5] |
| Exposure therapy | run_exposure_trial!() |
| P(safe) tracking | agent.pD[3][2] / sum(agent.pD[3]) |
| Belief updating | update_pD_final!() |

## 6) Test Coverage
- Test that P(safe) increases for safe spider.
- Test that P(safe) decreases for dangerous spider.
- Test that initial P(safe) ~ 10%.
- Test that final P(safe) > 50% after exposure to safe spider.
