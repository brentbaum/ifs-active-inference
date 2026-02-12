# Learnings (Smith 2021 / Spider Phobia Reproduction)

## 1) Exposure mode is essential for learning
- Without forced approach, the agent avoids the spider due to high P(dangerous).
- Avoidance provides no differential evidence (both dangerous and safe spiders give same observations).
- Only approach/interaction provides evidence (harm vs neutral).
- This explains why CBT exposure therapy requires therapist guidance.

## 2) A matrix learning should be disabled
- Initial implementation attempted to learn A alongside D.
- Problem: updating pA for all state combinations (weighted by belief) degrades the observation model.
- When agent sees neutral outcomes and believes spider is probably safe, it still updates pA[dangerous, neutral], which increases P(neutral|dangerous).
- This slows down learning and prevents convergence to paper's expected ~90% P(safe).
- Solution: keep A fixed and only learn D.

## 3) Update pD based on FINAL beliefs, not initial
- Standard pD update uses initial beliefs (qs at t=1).
- For static hidden states like danger, we want to learn from ALL evidence in the trial.
- `update_pD_final!()` uses beliefs at end of trial after all observations.
- This is crucial for matching paper's learning dynamics.

## 4) The paper's priors are carefully calibrated
- d[3] = [45, 5] gives exactly P(safe) = 0.1 (10%).
- This creates a strong prior that requires many exposures to overcome.
- With weaker priors, learning is faster but less realistic.

## 5) Trial structure matters
- Paper uses multi-timestep trials where agent can observe, act, observe outcome.
- Single-timestep trials don't provide enough structure for meaningful inference.
- Our `run_exposure_trial!()` handles this correctly.

## 6) EFE-based policy selection leads to avoidance
- Without exposure mode, EFE computation favors avoidance.
- Agent expects harm from approach (due to high P(dangerous)).
- Expected free energy is lower for avoidance (no expected harm).
- This demonstrates the "safety trap" that exposure therapy breaks.

## 7) Practical lesson for the library
- For static hidden states that persist across trials, use final-belief updates.
- For dynamic states that change within trials, use standard timestep-by-timestep updates.
- The `learn_D` parameter should specify which factors to learn.

## 8) Convergence takes ~200 trials
- With paper parameters, P(safe) reaches ~81-90% after 200 exposure trials.
- This is consistent with real therapy requiring multiple sessions.
- Fewer trials with stronger learning rates also work but may be less realistic.
